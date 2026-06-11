/* The Snake entity: movement, growth, and AI hooks. */
import { key, bfsDirection, survivalDirection } from "./ai.js";

export class Snake {
  constructor(body, dir, color, isAi = false) {
    this.body = body.map((c) => [c[0], c[1]]); // head at index 0
    this.dir = dir;
    this.pending = dir;
    this.color = color;
    this.isAi = isAi;
    this.alive = true;
    this.growPending = 0;
    this.score = 0;
    this.cycle = null;        // set for Hamiltonian fill AI
    this.brain = "bfs";       // AI planner: bfs/astar/greedy/anneal/drift/minimax/survive
  }
  get head() { return this.body[0]; }
  setDirection(dir) {
    if (dir[0] === -this.dir[0] && dir[1] === -this.dir[1]) return;
    this.pending = dir;
  }
  planAi(food, blocked) {
    let dir = food ? bfsDirection(this.head[0], this.head[1], food[0], food[1], blocked) : null;
    if (!dir) dir = survivalDirection(this.head[0], this.head[1], blocked, this.dir);
    if (dir) this.setDirection(dir);
  }
  planCycle() {
    const [hx, hy] = this.head;
    const nxt = this.cycle.get(key(hx, hy));
    this.pending = [nxt[0] - hx, nxt[1] - hy];
  }
  step() {
    this.dir = this.pending;
    const [hx, hy] = this.head;
    this.body.unshift([hx + this.dir[0], hy + this.dir[1]]);
    if (this.growPending > 0) this.growPending -= 1;
    else this.body.pop();
  }
  grow(n = 1) { this.growPending += n; }
  has(x, y, fromIndex = 0) {
    for (let i = fromIndex; i < this.body.length; i++) {
      if (this.body[i][0] === x && this.body[i][1] === y) return true;
    }
    return false;
  }
}
