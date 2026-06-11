"""Game AI brains.

A toolbox of snake planners, from the simple to the master-level:

* :func:`bfs_direction` / :func:`survival_direction` — shortest path + anti-trap
  fallback (the original "AI vs AI" brain).
* :func:`build_hamiltonian_cycle` — the perfect-fill cycle used by AI Fill.
* :func:`greedy_direction` — greedy best-first; fast and reckless (Easy mode).
* :func:`astar_direction` — A* with a Manhattan heuristic and an aggressiveness
  knob trading food-chasing against self-preservation.
* :func:`anneal_direction` — simulated-annealing flavoured; escapes dead ends by
  occasionally taking a worse-looking move.
* :func:`drift_direction` — DFS-ish / random walk ("drunk / drift" mode).
* :func:`minimax_direction` — adversarial look-ahead that boxes a rival in.
"""
import heapq
from collections import deque

from .config import COLS, ROWS, UP, DOWN, LEFT, RIGHT


def _neighbors(cell):
    x, y = cell
    yield (x + 1, y), RIGHT
    yield (x - 1, y), LEFT
    yield (x, y + 1), DOWN
    yield (x, y - 1), UP


def _in_bounds(cell) -> bool:
    x, y = cell
    return 0 <= x < COLS and 0 <= y < ROWS


def bfs_direction(start, goal, blocked):
    """Return the first step direction of the shortest path start -> goal."""
    if start == goal:
        return None
    queue = deque([start])
    came_from = {start: (None, None)}
    while queue:
        current = queue.popleft()
        for nxt, direction in _neighbors(current):
            if nxt in came_from or not _in_bounds(nxt) or nxt in blocked:
                continue
            came_from[nxt] = (current, direction)
            if nxt == goal:
                node = nxt
                while came_from[node][0] != start:
                    node = came_from[node][0]
                return came_from[node][1]
            queue.append(nxt)
    return None


def _flood_free(start, blocked):
    """Count cells reachable from ``start`` (open space around a move)."""
    if not _in_bounds(start) or start in blocked:
        return 0
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt, _ in _neighbors(current):
            if nxt in seen or not _in_bounds(nxt) or nxt in blocked:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return len(seen)


def survival_direction(head, blocked, current_dir):
    """Pick the safe move that keeps the most open space (anti-trap)."""
    best_dir, best_score = None, -1
    for nxt, direction in _neighbors(head):
        if direction[0] == -current_dir[0] and direction[1] == -current_dir[1]:
            continue
        if not _in_bounds(nxt) or nxt in blocked:
            continue
        score = _flood_free(nxt, blocked)
        if score > best_score:
            best_dir, best_score = direction, score
    return best_dir


def build_hamiltonian_cycle(cols, rows):
    """Build a Hamiltonian cycle over every grid cell (requires even rows).

    Returns ``(sequence, next_map)`` where ``sequence`` is the cell visit order
    and ``next_map[cell]`` gives the following cell in the cycle. A snake that
    starts on the cycle and always follows ``next_map`` covers the entire board
    without ever colliding — the classic "perfect" fill.
    """
    seq = []
    # Top row, left to right.
    for x in range(cols):
        seq.append((x, 0))
    # Vertical serpentine through columns cols-1..1 for rows 1..rows-1,
    # leaving column 0 as the return spine.
    going_down = True
    for x in range(cols - 1, 0, -1):
        ys = range(1, rows) if going_down else range(rows - 1, 0, -1)
        for y in ys:
            seq.append((x, y))
        going_down = not going_down
    # Return spine: column 0 from the bottom back up to row 1.
    for y in range(rows - 1, 0, -1):
        seq.append((0, y))

    nxt = {}
    n = len(seq)
    for i in range(n):
        nxt[seq[i]] = seq[(i + 1) % n]
    return seq, nxt


# -- Shared helpers ---------------------------------------------------------
def manhattan(a, b):
    """Grid (L1) distance between two cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _safe_moves(head, blocked, current_dir):
    """Yield ``(cell, direction)`` for legal non-reversing moves from ``head``."""
    for nxt, direction in _neighbors(head):
        if direction[0] == -current_dir[0] and direction[1] == -current_dir[1]:
            continue
        if not _in_bounds(nxt) or nxt in blocked:
            continue
        yield nxt, direction


# -- Greedy best-first (Easy mode) ------------------------------------------
def greedy_direction(head, goal, blocked, current_dir):
    """Step that shrinks the straight-line distance to the food the most.

    Pure greed: it never checks whether the move walls itself in, so it is fast
    but dies easily — exactly what an "Easy" AI wants.
    """
    if goal is None:
        return survival_direction(head, blocked, current_dir)
    best_dir, best_d = None, None
    for nxt, direction in _safe_moves(head, blocked, current_dir):
        d = manhattan(nxt, goal)
        if best_d is None or d < best_d:
            best_dir, best_d = direction, d
    return best_dir


# -- A* with an aggressiveness knob -----------------------------------------
def _astar_first_step(start, goal, blocked):
    """First step of the A* shortest path ``start -> goal`` (Manhattan h)."""
    if goal is None or start == goal:
        return None
    open_heap = [(manhattan(start, goal), 0, start)]
    came_from = {start: (None, None)}
    best_g = {start: 0}
    while open_heap:
        _, cost, current = heapq.heappop(open_heap)
        if current == goal:
            node = current
            while came_from[node][0] != start:
                node = came_from[node][0]
            return came_from[node][1]
        for nxt, direction in _neighbors(current):
            if not _in_bounds(nxt) or nxt in blocked:
                continue
            ng = cost + 1
            if nxt not in best_g or ng < best_g[nxt]:
                best_g[nxt] = ng
                came_from[nxt] = (current, direction)
                heapq.heappush(open_heap, (ng + manhattan(nxt, goal), ng, nxt))
    return None


def astar_direction(head, goal, blocked, current_dir, length, aggression=0.65):
    """A* toward the food, tempered by a self-preservation check.

    ``aggression`` in ``[0, 1]`` controls how much open space the snake insists
    on keeping after a move: 1.0 charges the food regardless, lower values back
    off to the survival planner when the A* step looks like a trap.
    """
    step = _astar_first_step(head, goal, blocked)
    if step is not None:
        nxt = (head[0] + step[0], head[1] + step[1])
        room = _flood_free(nxt, blocked)
        if room >= length or room >= length * (1.0 - aggression):
            return step
    return survival_direction(head, blocked, current_dir)


# -- Simulated annealing (master-level escape) ------------------------------
def anneal_direction(head, goal, blocked, current_dir, rng, length):
    """Mostly optimal, but escapes dead ends like simulated annealing.

    Each safe move is scored by open space minus distance-to-food. When the best
    move still leaves little room the "temperature" rises and a worse-looking
    move may be accepted (probability ``exp(delta / T)``) — the long-term thinking
    that lets a master snake wriggle out of a near-trap.
    """
    moves = list(_safe_moves(head, blocked, current_dir))
    if not moves:
        return None
    cand = []
    for nxt, direction in moves:
        room = _flood_free(nxt, blocked)
        dist = manhattan(nxt, goal) if goal else 0
        cand.append((room, dist, direction))
    # The greedy move chases the food; the safe move keeps the most open space.
    greedy = min(cand, key=lambda c: (c[1], -c[0]))
    safe = max(cand, key=lambda c: (c[0], -c[1]))
    if greedy is safe or len(cand) == 1:
        return greedy[2]
    # Temperature rises as the greedy move's room shrinks toward the body size,
    # making the snake more willing to abandon greed and escape a looming trap.
    temperature = max(0.0, 1.0 - greedy[0] / float(max(1, length * 2)))
    if rng.random() < temperature:
        return safe[2]
    return greedy[2]


# -- DFS / random walk ("drift / drunk" mode) -------------------------------
def drift_direction(head, blocked, current_dir, rng, straight_bias=0.55):
    """A wandering planner: keep going straight when possible, else veer at
    random. Only ever picks *safe* moves, so it drifts around erratically
    without instantly dying — a human-ish but dim opponent.
    """
    moves = list(_safe_moves(head, blocked, current_dir))
    if not moves:
        return None
    straight = next((d for _c, d in moves if d == current_dir), None)
    if straight is not None and rng.random() < straight_bias:
        return straight
    return moves[rng.randrange(len(moves))][1]


# -- Minimax (adversarial; blocks a rival's living space) -------------------
def minimax_direction(me, opp, goal, obstacles, depth=4):
    """Look ``depth`` plies ahead to maximise my room while minimising the
    opponent's, actively sealing off the rival's escape routes.

    Bodies are treated as static walls over the short horizon (a deliberate,
    cheap approximation); leaves are scored by the flood-fill space differential
    plus a mild pull toward the food.
    """
    base_blocked = set(obstacles)
    base_blocked.update(me.body)
    base_blocked.update(opp.body)

    def options(head, last_dir, blocked):
        opts = []
        for nxt, direction in _neighbors(head):
            if last_dir and direction[0] == -last_dir[0] and direction[1] == -last_dir[1]:
                continue
            if not _in_bounds(nxt) or nxt in blocked:
                continue
            opts.append((nxt, direction))
        return opts

    def evaluate(my_head, opp_head, blocked):
        score = _flood_free(my_head, blocked) - _flood_free(opp_head, blocked)
        if goal is not None:
            score -= 0.3 * manhattan(my_head, goal)
        return score

    def search(my_head, my_dir, opp_head, opp_dir, blocked, d, maximizing):
        if d == 0:
            return evaluate(my_head, opp_head, blocked), None
        if maximizing:
            opts = options(my_head, my_dir, blocked | {opp_head})
            if not opts:
                return -1e6 - d, None  # trapped: prefer a death further away
            best_val, best_dir = -1e9, None
            for nxt, direction in opts:
                val, _ = search(nxt, direction, opp_head, opp_dir,
                                blocked | {my_head}, d - 1, False)
                if val > best_val:
                    best_val, best_dir = val, direction
            return best_val, best_dir
        opts = options(opp_head, opp_dir, blocked | {my_head})
        if not opts:
            return 1e6 + d, None  # opponent trapped: great for me
        worst_val, worst_dir = 1e9, None
        for nxt, direction in opts:
            val, _ = search(my_head, my_dir, nxt, direction,
                            blocked | {opp_head}, d - 1, True)
            if val < worst_val:
                worst_val, worst_dir = val, direction
        return worst_val, worst_dir

    _, best = search(me.head, me.direction, opp.head, opp.direction,
                     base_blocked, depth, True)
    return best
