/* Game AI brains — the browser-edition counterpart of the Python ai.py.
 *
 * BFS + survival fallback and a Hamiltonian fill cycle (the originals), plus the
 * v1.5.0 toolbox: greedy best-first, A* with an aggressiveness knob, simulated
 * annealing, a DFS/random-walk "drift", and an adversarial minimax.
 */
import { COLS, ROWS, UP, DOWN, LEFT, RIGHT } from "./config.js";

export const key = (x, y) => x + "," + y;
export const inBounds = (x, y) => x >= 0 && x < COLS && y >= 0 && y < ROWS;

export function neighbors(x, y) {
  return [
    [x + 1, y, RIGHT], [x - 1, y, LEFT], [x, y + 1, DOWN], [x, y - 1, UP],
  ];
}

export function manhattan(a, b) {
  return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
}

// Legal, non-reversing moves from (hx, hy): array of [nx, ny, dir].
function safeMoves(hx, hy, blocked, curDir) {
  const out = [];
  for (const [nx, ny, dir] of neighbors(hx, hy)) {
    if (dir[0] === -curDir[0] && dir[1] === -curDir[1]) continue;
    if (!inBounds(nx, ny) || blocked.has(key(nx, ny))) continue;
    out.push([nx, ny, dir]);
  }
  return out;
}

// -- BFS shortest path ------------------------------------------------------
export function bfsDirection(sx, sy, gx, gy, blocked) {
  if (sx === gx && sy === gy) return null;
  const startK = key(sx, sy);
  const cameFrom = new Map();
  cameFrom.set(startK, [null, null]);
  const queue = [[sx, sy]];
  let qi = 0;
  while (qi < queue.length) {
    const [cx, cy] = queue[qi++];
    for (const [nx, ny, dir] of neighbors(cx, cy)) {
      const nk = key(nx, ny);
      if (cameFrom.has(nk) || !inBounds(nx, ny) || blocked.has(nk)) continue;
      cameFrom.set(nk, [key(cx, cy), dir]);
      if (nx === gx && ny === gy) {
        let node = nk;
        while (cameFrom.get(node)[0] !== startK) node = cameFrom.get(node)[0];
        return cameFrom.get(node)[1];
      }
      queue.push([nx, ny]);
    }
  }
  return null;
}

export function floodFree(sx, sy, blocked) {
  if (!inBounds(sx, sy) || blocked.has(key(sx, sy))) return 0;
  const seen = new Set([key(sx, sy)]);
  const queue = [[sx, sy]];
  let qi = 0;
  while (qi < queue.length) {
    const [cx, cy] = queue[qi++];
    for (const [nx, ny] of neighbors(cx, cy)) {
      const nk = key(nx, ny);
      if (seen.has(nk) || !inBounds(nx, ny) || blocked.has(nk)) continue;
      seen.add(nk);
      queue.push([nx, ny]);
    }
  }
  return seen.size;
}

export function survivalDirection(hx, hy, blocked, curDir) {
  let bestDir = null, bestScore = -1;
  for (const [nx, ny, dir] of neighbors(hx, hy)) {
    if (dir[0] === -curDir[0] && dir[1] === -curDir[1]) continue;
    if (!inBounds(nx, ny) || blocked.has(key(nx, ny))) continue;
    const score = floodFree(nx, ny, blocked);
    if (score > bestScore) { bestScore = score; bestDir = dir; }
  }
  return bestDir;
}

// Hamiltonian cycle (requires even ROWS). Returns { seq, next: Map cell->cell }.
export function buildHamiltonianCycle(cols, rows) {
  const seq = [];
  for (let x = 0; x < cols; x++) seq.push([x, 0]);
  let goingDown = true;
  for (let x = cols - 1; x >= 1; x--) {
    if (goingDown) { for (let y = 1; y < rows; y++) seq.push([x, y]); }
    else { for (let y = rows - 1; y >= 1; y--) seq.push([x, y]); }
    goingDown = !goingDown;
  }
  for (let y = rows - 1; y >= 1; y--) seq.push([0, y]);

  const next = new Map();
  const n = seq.length;
  for (let i = 0; i < n; i++) {
    const a = seq[i], b = seq[(i + 1) % n];
    next.set(key(a[0], a[1]), b);
  }
  return { seq, next };
}

// -- Greedy best-first (Easy mode) -----------------------------------------
export function greedyDirection(hx, hy, food, blocked, curDir) {
  if (!food) return survivalDirection(hx, hy, blocked, curDir);
  let bestDir = null, bestD = Infinity;
  for (const [nx, ny, dir] of safeMoves(hx, hy, blocked, curDir)) {
    const d = manhattan([nx, ny], food);
    if (d < bestD) { bestD = d; bestDir = dir; }
  }
  return bestDir;
}

// -- A* with an aggressiveness knob ----------------------------------------
// Tiny binary min-heap of [f, g, x, y] entries (ordered by f).
class MinHeap {
  constructor() { this.a = []; }
  get size() { return this.a.length; }
  push(item) {
    const a = this.a; a.push(item); let i = a.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (a[p][0] <= a[i][0]) break; [a[p], a[i]] = [a[i], a[p]]; i = p; }
  }
  pop() {
    const a = this.a, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last; let i = 0; const n = a.length;
      for (;;) {
        let l = 2 * i + 1, r = 2 * i + 2, s = i;
        if (l < n && a[l][0] < a[s][0]) s = l;
        if (r < n && a[r][0] < a[s][0]) s = r;
        if (s === i) break; [a[s], a[i]] = [a[i], a[s]]; i = s;
      }
    }
    return top;
  }
}

function astarFirstStep(sx, sy, gx, gy, blocked) {
  if (gx == null || (sx === gx && sy === gy)) return null;
  const startK = key(sx, sy);
  const heap = new MinHeap();
  heap.push([manhattan([sx, sy], [gx, gy]), 0, sx, sy]);
  const cameFrom = new Map(); cameFrom.set(startK, [null, null]);
  const bestG = new Map(); bestG.set(startK, 0);
  while (heap.size) {
    const [, g, cx, cy] = heap.pop();
    if (cx === gx && cy === gy) {
      let node = key(cx, cy);
      while (cameFrom.get(node)[0] !== startK) node = cameFrom.get(node)[0];
      return cameFrom.get(node)[1];
    }
    for (const [nx, ny, dir] of neighbors(cx, cy)) {
      if (!inBounds(nx, ny) || blocked.has(key(nx, ny))) continue;
      const ng = g + 1, nk = key(nx, ny);
      if (!bestG.has(nk) || ng < bestG.get(nk)) {
        bestG.set(nk, ng);
        cameFrom.set(nk, [key(cx, cy), dir]);
        heap.push([ng + manhattan([nx, ny], [gx, gy]), ng, nx, ny]);
      }
    }
  }
  return null;
}

export function astarDirection(hx, hy, food, blocked, curDir, length, aggression = 0.65) {
  const step = food ? astarFirstStep(hx, hy, food[0], food[1], blocked) : null;
  if (step) {
    const nx = hx + step[0], ny = hy + step[1];
    const room = floodFree(nx, ny, blocked);
    if (room >= length || room >= length * (1 - aggression)) return step;
  }
  return survivalDirection(hx, hy, blocked, curDir);
}

// -- Simulated annealing (master-level escape) ------------------------------
export function annealDirection(hx, hy, food, blocked, curDir, rng, length) {
  const moves = safeMoves(hx, hy, blocked, curDir);
  if (!moves.length) return null;
  const cand = moves.map(([nx, ny, dir]) => ({
    room: floodFree(nx, ny, blocked),
    dist: food ? manhattan([nx, ny], food) : 0,
    dir,
  }));
  let greedy = cand[0], safe = cand[0];
  for (const c of cand) {
    if (c.dist < greedy.dist || (c.dist === greedy.dist && c.room > greedy.room)) greedy = c;
    if (c.room > safe.room || (c.room === safe.room && c.dist < safe.dist)) safe = c;
  }
  if (greedy === safe || cand.length === 1) return greedy.dir;
  const temperature = Math.max(0, 1 - greedy.room / Math.max(1, length * 2));
  return rng() < temperature ? safe.dir : greedy.dir;
}

// -- DFS / random walk ("drift / drunk" mode) -------------------------------
export function driftDirection(hx, hy, blocked, curDir, rng, straightBias = 0.55) {
  const moves = safeMoves(hx, hy, blocked, curDir);
  if (!moves.length) return null;
  let straight = null;
  for (const [, , dir] of moves) {
    if (dir[0] === curDir[0] && dir[1] === curDir[1]) { straight = dir; break; }
  }
  if (straight && rng() < straightBias) return straight;
  return moves[(rng() * moves.length) | 0][2];
}

// -- Minimax (adversarial; blocks a rival's living space) -------------------
export function minimaxDirection(me, opp, food, obstacles, depth = 4) {
  const base = new Set(obstacles);
  for (const c of me.body) base.add(key(c[0], c[1]));
  for (const c of opp.body) base.add(key(c[0], c[1]));

  function options(hx, hy, lastDir, blocked) {
    const opts = [];
    for (const [nx, ny, dir] of neighbors(hx, hy)) {
      if (lastDir && dir[0] === -lastDir[0] && dir[1] === -lastDir[1]) continue;
      if (!inBounds(nx, ny) || blocked.has(key(nx, ny))) continue;
      opts.push([nx, ny, dir]);
    }
    return opts;
  }
  function evaluate(mh, oh, blocked) {
    let score = floodFree(mh[0], mh[1], blocked) - floodFree(oh[0], oh[1], blocked);
    if (food) score -= 0.3 * manhattan(mh, food);
    return score;
  }
  function search(mh, mdir, oh, odir, blocked, d, maximizing) {
    if (d === 0) return [evaluate(mh, oh, blocked), null];
    if (maximizing) {
      const opts = options(mh[0], mh[1], mdir, new Set(blocked).add(key(oh[0], oh[1])));
      if (!opts.length) return [-1e6 - d, null];
      let bestVal = -1e9, bestDir = null;
      for (const [nx, ny, dir] of opts) {
        const nb = new Set(blocked).add(key(mh[0], mh[1]));
        const [val] = search([nx, ny], dir, oh, odir, nb, d - 1, false);
        if (val > bestVal) { bestVal = val; bestDir = dir; }
      }
      return [bestVal, bestDir];
    }
    const opts = options(oh[0], oh[1], odir, new Set(blocked).add(key(mh[0], mh[1])));
    if (!opts.length) return [1e6 + d, null];
    let worstVal = 1e9, worstDir = null;
    for (const [nx, ny, dir] of opts) {
      const nb = new Set(blocked).add(key(oh[0], oh[1]));
      const [val] = search(mh, mdir, [nx, ny], dir, nb, d - 1, true);
      if (val < worstVal) { worstVal = val; worstDir = dir; }
    }
    return [worstVal, worstDir];
  }
  const [, best] = search(me.head, me.dir, opp.head, opp.dir, base, depth, true);
  return best;
}
