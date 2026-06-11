"""Pathfinding AI: BFS, a survival fallback, and a Hamiltonian fill cycle."""
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
