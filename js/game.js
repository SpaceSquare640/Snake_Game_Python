/* The Game controller: state machine, input, round/replay/tutorial logic.
 *
 * Drawing lives in render.js (folded into the prototype below), mirroring the
 * Python package's SnakeGame(RenderMixin) split.
 */
import {
  WIDTH, HEIGHT, COLS, ROWS, UP, DOWN, LEFT, RIGHT,
  CLASSIC, SURVIVAL, BATTLE, LEVEL, AI_HUMAN, PLAYER_FILL, AI_AI, AI_FILL,
  AI_ASTAR, AI_ANNEAL, AI_GREEDY, AI_DRIFT, AI_MINIMAX, AI_MINIMAX_DUEL,
  AI_COOP_FILL, AI_FOOD_RUSH, MODE_KEYS, MAIN_MENU_MODES, AI_MENU_MODES,
  SOLO_AI_MODES, TWO_SNAKE_MODES, FILL_MODES, RUSH_TARGET,
  STATE_MENU, STATE_READY, STATE_PLAY, STATE_OVER, STATE_COLOR, STATE_LANG,
  STATE_NAME, STATE_SETTINGS, STATE_AI_MENU, STATE_THEME, STATE_CONTROLS,
  STATE_REBIND, STATE_LEADERBOARD, STATE_AUDIO, STATE_REPLAYS, STATE_TUTORIAL,
  REPLAY_LIMIT, TUT_GOAL, MOVE_DIRS, DIR_VECTORS, DEFAULT_KEYMAP, mulberry32,
} from "./config.js";
import { applyTheme, SNAKE_COLORS, OPPONENT_COLOR, THEME_ORDER } from "./theme.js";
import { T, LANG_ORDER } from "./i18n.js";
import { APP_VERSION, parseVersion, fetchLatestTag } from "./version.js";
import { loadProfile, saveProfile, addScore } from "./profile.js";
import { SoundManager } from "./audio.js";
import { Snake } from "./entities.js";
import {
  key, inBounds, buildHamiltonianCycle, bfsDirection, survivalDirection,
  greedyDirection, astarDirection, annealDirection, driftDirection, minimaxDirection,
} from "./ai.js";
import { RenderMixin } from "./render.js";

export class Game {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.profile = loadProfile();
    applyTheme(this.profile.theme);
    this.sound = new SoundManager(this.profile);
    this.state = STATE_MENU;
    this.mode = CLASSIC;
    this.subReturn = STATE_MENU;
    this.mouseDown = null;   // [action, arg] armed on mouse-down
    this.rebindDir = null;
    // Replay state.
    this.rng = Math.random;
    this.tickCount = 0;
    this.recording = null;
    this.replaying = false;
    this.replayByTick = {};
    this.lastReplay = null;
    this.currentReplay = null;
    // Tutorial state.
    this.tutStep = 0;
    this.tutEaten = 0;
    this.tutMoved = false;

    this.buttons = [];
    this.pointer = { x: -1, y: -1 };

    this.snakes = [];
    this.food = null;
    this.obstacles = new Set();
    this.stage = 1;
    this.tickMs = 120;
    this.moveAccum = 0;
    this.lastTs = 0;
    this.resultText = "";
    this.win = false;
    this.levelUpFlash = 0;
    this.nameBuffer = "";

    this.updateState = "checking";
    this.latestVersion = "";
    this.checkUpdate();

    this.bindInput();
    requestAnimationFrame((ts) => this.loop(ts));
  }

  t(k, vars) {
    let s = (T[this.profile.language] && T[this.profile.language][k]) || k;
    if (vars) for (const vk in vars) s = s.replace("{" + vk + "}", vars[vk]);
    return s;
  }

  // -- Update check -----------------------------------------------------
  checkUpdate() {
    fetchLatestTag().then((tag) => {
      if (!tag) { this.updateState = "unknown"; return; }
      this.latestVersion = tag;
      this.updateState = parseVersion(tag) > parseVersion(APP_VERSION) ? "outdated" : "latest";
    }).catch(() => { this.updateState = "unknown"; });
  }

  // -- Round setup ------------------------------------------------------
  startRound(seed) {
    if (seed === undefined) seed = (Math.random() * 0x40000000) >>> 0;
    this.rng = mulberry32(seed);
    this.replaying = false;
    this.replayByTick = {};
    this.tickCount = 0;
    this.recording = { mode: this.mode, seed: seed,
      colorIndex: this.profile.colorIndex, inputs: [] };
    this._setupRound(SNAKE_COLORS[this.profile.colorIndex]);
    this.state = STATE_READY;
  }

  startReplay(rec) {
    this.mode = rec.mode;
    this.currentReplay = rec;
    this.rng = mulberry32(rec.seed >>> 0);
    this.replaying = true;
    this.recording = null;
    this.tickCount = 0;
    this.replayByTick = {};
    for (const inp of (rec.inputs || [])) {
      (this.replayByTick[inp.t] = this.replayByTick[inp.t] || []).push([inp.s, inp.d]);
    }
    this._setupRound(SNAKE_COLORS[(rec.colorIndex || 0) % SNAKE_COLORS.length]);
    this.state = STATE_PLAY; // replays auto-play
  }

  _setupRound(color) {
    this.obstacles = new Set();
    this.stage = 1;
    this.resultText = "";
    this.win = false;
    this.food = null;
    const midY = Math.floor(ROWS / 2);

    if (TWO_SNAKE_MODES.has(this.mode)) {
      const left = new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color);
      const right = new Snake(
        [[COLS - 5, midY], [COLS - 4, midY], [COLS - 3, midY]], LEFT, OPPONENT_COLOR);
      if (this.mode === AI_AI) { left.isAi = true; right.isAi = true; }
      else if (this.mode === AI_HUMAN) { right.isAi = true; }
      else if (this.mode === AI_MINIMAX) { right.isAi = true; right.brain = "minimax"; }
      else if (this.mode === AI_MINIMAX_DUEL) {
        left.isAi = true; right.isAi = true; left.brain = "minimax"; right.brain = "survive";
      } else if (this.mode === AI_FOOD_RUSH) {
        left.isAi = true; right.isAi = true; left.brain = "astar"; right.brain = "astar";
      }
      this.snakes = [left, right];
    } else if (this.mode === AI_FILL) {
      const { seq, next } = buildHamiltonianCycle(COLS, ROWS);
      const s = new Snake([[seq[0][0], seq[0][1]]], RIGHT, color, true);
      s.cycle = next;
      this.snakes = [s];
    } else if (this.mode === AI_COOP_FILL) {
      // Two AI snakes split the board: each follows a perfect-fill cycle over
      // its own half, so together they paint every cell, collision-free.
      const half = Math.floor(COLS / 2);
      const { seq, next } = buildHamiltonianCycle(half, ROWS);
      const left = new Snake([[seq[0][0], seq[0][1]]], RIGHT, color, true);
      left.cycle = next;
      const rightCycle = new Map();
      for (const [k, v] of next) {
        const [x, y] = k.split(",").map(Number);
        rightCycle.set(key(x + half, y), [v[0] + half, v[1]]);
      }
      const right = new Snake([[seq[0][0] + half, seq[0][1]]], RIGHT, OPPONENT_COLOR, true);
      right.cycle = rightCycle;
      this.snakes = [left, right];
    } else if (this.mode === PLAYER_FILL) {
      this.snakes = [new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color)];
    } else if (SOLO_AI_MODES.has(this.mode)) {
      const brain = { [AI_ASTAR]: "astar", [AI_ANNEAL]: "anneal",
        [AI_GREEDY]: "greedy", [AI_DRIFT]: "drift" }[this.mode];
      const s = new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color, true);
      s.brain = brain;
      this.snakes = [s];
    } else {
      this.snakes = [new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color)];
      if (this.mode === LEVEL) this.buildStage(this.stage);
    }

    if (!FILL_MODES.has(this.mode)) this.food = this.spawnFood();
    this.tickMs = this.baseTick();
    this.moveAccum = 0;
  }

  baseTick() {
    return {
      [CLASSIC]: 120, [SURVIVAL]: 140, [BATTLE]: 110, [LEVEL]: 120,
      [AI_HUMAN]: 90, [PLAYER_FILL]: 100, [AI_AI]: 70, [AI_FILL]: 26,
      [AI_ASTAR]: 75, [AI_ANNEAL]: 80, [AI_GREEDY]: 70, [AI_DRIFT]: 90,
      [AI_MINIMAX]: 100, [AI_MINIMAX_DUEL]: 85, [AI_COOP_FILL]: 32, [AI_FOOD_RUSH]: 75,
    }[this.mode];
  }

  occupied() {
    const cells = new Set(this.obstacles);
    for (const s of this.snakes) for (const c of s.body) cells.add(key(c[0], c[1]));
    return cells;
  }

  spawnFood() {
    const occ = this.occupied();
    const free = [];
    for (let x = 0; x < COLS; x++)
      for (let y = 0; y < ROWS; y++)
        if (!occ.has(key(x, y))) free.push([x, y]);
    return free.length ? free[(this.rng() * free.length) | 0] : null;
  }

  buildStage(stage) {
    this.obstacles = new Set();
    let seed = stage * 7919;
    const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
    const wallCount = Math.min(3 + stage, 9);
    for (let i = 0; i < wallCount; i++) {
      const horizontal = rnd() < 0.5;
      const len = 3 + ((rnd() * 4) | 0);
      const x = 2 + ((rnd() * (COLS - 8)) | 0);
      const y = 2 + ((rnd() * (ROWS - 4)) | 0);
      for (let j = 0; j < len; j++) {
        const cx = horizontal ? x + j : x;
        const cy = horizontal ? y : y + j;
        if (inBounds(cx, cy)) this.obstacles.add(key(cx, cy));
      }
    }
    const midY = Math.floor(ROWS / 2);
    for (let x = 0; x < 6; x++) this.obstacles.delete(key(x, midY));
  }

  // -- Tutorial ---------------------------------------------------------
  startTutorial() {
    this.mode = CLASSIC;
    this.replaying = false;
    this.recording = null;
    this.rng = Math.random;
    this.obstacles = new Set();
    this.tutStep = 0;
    this.tutEaten = 0;
    this.tutMoved = false;
    const midY = Math.floor(ROWS / 2);
    const color = SNAKE_COLORS[this.profile.colorIndex];
    this.snakes = [new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color)];
    this.food = this.spawnFood();
    this.tickMs = 140;
    this.moveAccum = 0;
    this.state = STATE_TUTORIAL;
  }
  tutorialRespawn() {
    const midY = Math.floor(ROWS / 2);
    const color = SNAKE_COLORS[this.profile.colorIndex];
    this.snakes = [new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color)];
    this.food = this.spawnFood();
  }
  tutorialAdvance() {
    const snake = this.snakes[0];
    snake.step();
    const [hx, hy] = snake.head;
    if (!inBounds(hx, hy) || snake.has(hx, hy, 1)) {
      this.sound.play("crash");
      this.tutorialRespawn();
      return;
    }
    if (this.food && hx === this.food[0] && hy === this.food[1]) {
      snake.grow(1); this.tutEaten += 1; this.sound.play("eat");
      this.food = this.spawnFood();
    }
    if (this.tutStep === 1 && this.tutEaten >= TUT_GOAL) this.tutStep = 2;
  }
  tutorialInput(dir) {
    this.snakes[0].setDirection(dir);
    if (this.tutStep === 0) { this.tutStep = 1; this.tutMoved = true; }
  }

  // -- Update -----------------------------------------------------------
  update(dt) {
    if (this.state === STATE_TUTORIAL) {
      this.moveAccum += dt;
      if (this.moveAccum >= this.tickMs) { this.moveAccum -= this.tickMs; this.tutorialAdvance(); }
      return;
    }
    if (this.state !== STATE_PLAY) return;
    this.moveAccum += dt;
    if (this.moveAccum < this.tickMs) return;
    this.moveAccum -= this.tickMs;
    this.advance();
  }

  advance() {
    if (this.replaying) {
      for (const [idx, dir] of (this.replayByTick[this.tickCount] || [])) {
        if (idx < this.snakes.length) this.snakes[idx].setDirection(dir);
      }
    }
    for (const s of this.snakes) if (s.isAi && s.alive) this.planAiSnake(s);
    if (FILL_MODES.has(this.mode)) {
      for (const s of this.snakes) if (s.alive) s.grow(1);
    }
    for (const s of this.snakes) if (s.alive) s.step();
    const aliveBefore = this.snakes.filter((s) => s.alive).length;
    this.resolveCollisions();
    if (this.snakes.filter((s) => s.alive).length < aliveBefore) this.sound.play("crash");
    if (!FILL_MODES.has(this.mode)) this.resolveFood();
    this.tickCount += 1;
    this.checkRoundEnd();
  }

  opponentOf(snake) {
    for (const other of this.snakes) if (other !== snake && other.alive) return other;
    return null;
  }

  planAiSnake(s) {
    if (s.cycle) { s.planCycle(); return; }
    const blocked = this.blockedFor(s);
    const [hx, hy] = s.head, cur = s.dir, length = s.body.length;
    let dir;
    switch (s.brain) {
      case "greedy": dir = greedyDirection(hx, hy, this.food, blocked, cur); break;
      case "astar": dir = astarDirection(hx, hy, this.food, blocked, cur, length); break;
      case "anneal": dir = annealDirection(hx, hy, this.food, blocked, cur, this.rng, length); break;
      case "drift": dir = driftDirection(hx, hy, blocked, cur, this.rng); break;
      case "survive": dir = survivalDirection(hx, hy, blocked, cur); break;
      case "minimax": {
        const opp = this.opponentOf(s);
        dir = opp ? minimaxDirection(s, opp, this.food, this.obstacles) : null;
        if (!dir) dir = survivalDirection(hx, hy, blocked, cur);
        break;
      }
      default: // "bfs" — shortest path, anti-trap fallback
        dir = this.food ? bfsDirection(hx, hy, this.food[0], this.food[1], blocked) : null;
        if (!dir) dir = survivalDirection(hx, hy, blocked, cur);
    }
    if (dir) s.setDirection(dir);
  }

  recordInput(idx, dir) {
    if (idx < this.snakes.length) this.snakes[idx].setDirection(dir);
    if (this.recording && !this.replaying) {
      this.recording.inputs.push({ t: this.tickCount, s: idx, d: dir });
    }
  }

  blockedFor(snake) {
    const blocked = new Set(this.obstacles);
    // In fill modes the snake grows every tick, so no tail tip frees up.
    const ownRecedes = !FILL_MODES.has(this.mode);
    for (const other of this.snakes) {
      if (other === snake && ownRecedes) {
        for (let i = 0; i < other.body.length - 1; i++) blocked.add(key(other.body[i][0], other.body[i][1]));
      } else {
        for (const c of other.body) blocked.add(key(c[0], c[1]));
      }
    }
    return blocked;
  }

  resolveCollisions() {
    const heads = new Map();
    for (const s of this.snakes) {
      if (!s.alive) continue;
      const [hx, hy] = s.head;
      if (!inBounds(hx, hy) || this.obstacles.has(key(hx, hy))) { s.alive = false; continue; }
      if (s.has(hx, hy, 1)) { s.alive = false; continue; }
      let hit = false;
      for (const other of this.snakes) {
        if (other === s) continue;
        if (other.has(hx, hy, 0)) { hit = true; break; }
      }
      if (hit) { s.alive = false; continue; }
      const hk = key(hx, hy);
      if (!heads.has(hk)) heads.set(hk, []);
      heads.get(hk).push(s);
    }
    for (const group of heads.values()) {
      if (group.length > 1) for (const s of group) s.alive = false;
    }
  }

  resolveFood() {
    if (!this.food) return;
    for (const s of this.snakes) {
      if (s.alive && s.head[0] === this.food[0] && s.head[1] === this.food[1]) {
        s.grow(1);
        s.score += 1;
        this.sound.play("eat");
        if (this.mode === SURVIVAL) this.tickMs = Math.max(45, this.tickMs - 4);
        if (this.mode === LEVEL && s.score % 5 === 0) { this.stage += 1; this.buildStage(this.stage); }
        this.food = this.spawnFood();
        break;
      }
    }
  }

  checkRoundEnd() {
    const total = COLS * ROWS;
    if (FILL_MODES.has(this.mode)) {
      const filled = this.snakes.reduce((a, s) => a + s.body.length, 0);
      if (filled >= total) {
        this.win = true;
        this.resultText = this.t("board_filled", { n: filled });
        this.endRound(filled);
      } else if (!this.snakes.some((s) => s.alive)) {
        this.endRound(filled);
      }
      return;
    }
    const alive = this.snakes.filter((s) => s.alive);
    if (this.mode === AI_FOOD_RUSH) {
      if (this.snakes.some((s) => s.score >= RUSH_TARGET) || alive.length <= 1) this.finishRush();
    } else if (TWO_SNAKE_MODES.has(this.mode)) {
      if (alive.length <= 1) this.finishVersus(alive);
    } else {
      if (alive.length === 0) this.endRound(this.snakes[0].score);
    }
  }

  finishRush() {
    let best = this.snakes[0];
    for (const s of this.snakes) {
      if (s.score > best.score || (s.score === best.score && s.alive && !best.alive)) best = s;
    }
    this.resultText = this.t("winner", { name: this.snakeLabel(this.snakes.indexOf(best)) });
    this.win = false; // both racers are AI
    this.endRound(best.score);
  }

  finishVersus(alive) {
    let score;
    if (alive.length === 1) {
      const winner = alive[0];
      const idx = this.snakes.indexOf(winner);
      this.resultText = this.t("winner", { name: this.snakeLabel(idx) });
      this.win = !this.snakes[0].isAi && winner === this.snakes[0];
      score = winner.score;
    } else {
      this.resultText = this.t("draw");
      score = Math.max(0, ...this.snakes.map((s) => s.score));
    }
    this.endRound(score);
  }

  snakeLabel(index) {
    if (this.mode === BATTLE) return index === 0 ? this.t("p1") : this.t("p2");
    if (this.mode === AI_AI || this.mode === AI_MINIMAX_DUEL || this.mode === AI_FOOD_RUSH)
      return this.t("ai") + " " + (index + 1);
    if (this.mode === AI_HUMAN || this.mode === AI_MINIMAX)
      return index === 0 ? this.t("you") : this.t("ai");
    return this.t("player");
  }

  endRound(score) {
    if (this.win) this.sound.play("win");
    if (this.replaying) { this.state = STATE_OVER; return; }
    const levelled = addScore(this.profile, MODE_KEYS[this.mode], score);
    if (levelled) this.levelUpFlash = 1800;
    this._saveRecording(score);
    saveProfile(this.profile);
    this.state = STATE_OVER;
  }

  _saveRecording(score) {
    if (!this.recording) return;
    const rec = this.recording;
    rec.score = score | 0;
    rec.win = !!this.win;
    rec.ticks = this.tickCount;
    rec.name = this.profile.name;
    rec.ts = Date.now();
    this.lastReplay = rec;
    this.profile.replays.unshift(rec);
    this.profile.replays.length = Math.min(this.profile.replays.length, REPLAY_LIMIT);
  }

  humanSnake() {
    if (!this.snakes.length) return null;
    const first = this.snakes[0];
    return first.isAi ? null : first;
  }

  // -- Input ------------------------------------------------------------
  bindInput() {
    window.addEventListener("keydown", (e) => { this.sound.resume(); this.onKey(e); });
    const toLocal = (clientX, clientY) => {
      const r = this.canvas.getBoundingClientRect();
      return {
        x: (clientX - r.left) * (WIDTH / r.width),
        y: (clientY - r.top) * (HEIGHT / r.height),
      };
    };
    this.canvas.addEventListener("mousemove", (e) => {
      this.pointer = toLocal(e.clientX, e.clientY);
    });
    this.canvas.addEventListener("mouseleave", () => { this.pointer = { x: -1, y: -1 }; });
    this.canvas.addEventListener("mousedown", (e) => {
      this.sound.resume();
      const p = toLocal(e.clientX, e.clientY);
      const b = this.buttonAt(p.x, p.y);
      this.mouseDown = b ? [b.action, b.arg] : null;
    });
    this.canvas.addEventListener("mouseup", (e) => {
      const p = toLocal(e.clientX, e.clientY);
      const b = this.buttonAt(p.x, p.y);
      if (b && this.mouseDown && this.mouseDown[0] === b.action && this.mouseDown[1] === b.arg) {
        this.dispatch(b.action, b.arg);
      }
      this.mouseDown = null;
    });
    this.canvas.addEventListener("touchstart", (e) => {
      e.preventDefault();
      this.sound.resume();
      const tp = e.changedTouches[0];
      const p = toLocal(tp.clientX, tp.clientY);
      this.pointer = p;
      const b = this.buttonAt(p.x, p.y);
      if (b) this.dispatch(b.action, b.arg);
    }, { passive: false });
  }

  buttonAt(x, y) {
    for (let i = this.buttons.length - 1; i >= 0; i--) {
      const b = this.buttons[i];
      if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) return b;
    }
    return null;
  }

  dispatch(action, arg) {
    if (action !== "dir") this.sound.play("select");
    switch (action) {
      case "start_mode": this.mode = arg; this.startRound(); break;
      case "open_ai_menu": this.state = STATE_AI_MENU; break;
      case "open_settings": this.state = STATE_SETTINGS; break;
      case "open_color": this.openSub(STATE_COLOR); break;
      case "open_lang": this.openSub(STATE_LANG); break;
      case "open_name": this.nameBuffer = this.profile.name; this.openSub(STATE_NAME); break;
      case "open_theme": this.openSub(STATE_THEME); break;
      case "open_audio": this.openSub(STATE_AUDIO); break;
      case "open_controls": this.openSub(STATE_CONTROLS); break;
      case "open_leaderboard": this.openSub(STATE_LEADERBOARD); break;
      case "set_lang": this.profile.language = arg; saveProfile(this.profile); break;
      case "set_color": this.profile.colorIndex = arg; saveProfile(this.profile); break;
      case "set_theme": this.profile.theme = arg; applyTheme(arg); saveProfile(this.profile); break;
      case "toggle_sound": this.profile.sound = !this.profile.sound; saveProfile(this.profile); break;
      case "toggle_music":
        this.profile.music = !this.profile.music;
        this.sound.setMusic(this.profile.music); saveProfile(this.profile); break;
      case "toggle_fps": this.profile.showFps = !this.profile.showFps; saveProfile(this.profile); break;
      case "rebind": this.rebindDir = arg; this.state = STATE_REBIND; break;
      case "reset_keys": this.profile.keymap = Object.assign({}, DEFAULT_KEYMAP); saveProfile(this.profile); break;
      case "open_replays": this.openSub(STATE_REPLAYS); break;
      case "watch_replay": if (this.lastReplay) this.startReplay(this.lastReplay); break;
      case "replay_current": if (this.currentReplay) this.startReplay(this.currentReplay); break;
      case "play_replay":
        if (arg >= 0 && arg < this.profile.replays.length) this.startReplay(this.profile.replays[arg]);
        break;
      case "start_tutorial": this.startTutorial(); break;
      case "back_menu": this.state = STATE_MENU; break;
      case "sub_back": this.state = this.subReturn; break;
      case "to_menu": this.state = STATE_MENU; break;
      case "restart": this.startRound(); break;
      case "dir":
        if (this.state === STATE_TUTORIAL) { this.tutorialInput(arg); break; }
        if (this.replaying) break;
        if (this.state === STATE_READY) this.state = STATE_PLAY;
        if (this.humanSnake()) this.recordInput(0, arg);
        break;
    }
  }

  openSub(state) {
    this.subReturn = (this.state === STATE_MENU || this.state === STATE_SETTINGS)
      ? this.state : STATE_MENU;
    this.state = state;
  }

  onKey(e) {
    const k = e.key;
    if (this.state === STATE_NAME) {
      if (k === "Enter") { this.profile.name = this.nameBuffer.trim() || "Player"; saveProfile(this.profile); this.state = this.subReturn; }
      else if (k === "Escape") this.state = this.subReturn;
      else if (k === "Backspace") this.nameBuffer = this.nameBuffer.slice(0, -1);
      else if (k.length === 1 && this.nameBuffer.length < 14) this.nameBuffer += k;
      e.preventDefault();
      return;
    }
    if (this.state === STATE_REBIND) { this.keyRebind(k); e.preventDefault(); return; }
    if ([" ", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(k)) e.preventDefault();

    const h = {
      [STATE_MENU]: () => this.keyMenu(k),
      [STATE_SETTINGS]: () => this.keySettings(k),
      [STATE_AI_MENU]: () => this.keyAiMenu(k),
      [STATE_THEME]: () => this.keyTheme(k),
      [STATE_AUDIO]: () => this.keyAudio(k),
      [STATE_CONTROLS]: () => this.keyControls(k),
      [STATE_LEADERBOARD]: () => { if (k === "Escape" || k === "m") this.state = this.subReturn; },
      [STATE_REPLAYS]: () => { if (k === "Escape" || k === "m") this.state = this.subReturn; },
      [STATE_TUTORIAL]: () => this.keyTutorial(k),
      [STATE_READY]: () => this.keyReady(k),
      [STATE_PLAY]: () => this.keyPlay(k),
      [STATE_OVER]: () => this.keyOver(k),
      [STATE_COLOR]: () => this.keyColor(k),
      [STATE_LANG]: () => this.keyLang(k),
    };
    if (h[this.state]) h[this.state]();
  }

  keyMenu(k) {
    if (k >= "1" && k <= "6") {
      const idx = k.charCodeAt(0) - 49;
      if (idx < MAIN_MENU_MODES.length) { this.mode = MAIN_MENU_MODES[idx]; this.startRound(); }
    } else if (k === "a" || k === "A") this.state = STATE_AI_MENU;
    else if (k === "s" || k === "S") this.state = STATE_SETTINGS;
    else if (k === "c" || k === "C") this.openSub(STATE_COLOR);
    else if (k === "l" || k === "L") this.openSub(STATE_LANG);
    else if (k === "n" || k === "N") { this.nameBuffer = this.profile.name; this.openSub(STATE_NAME); }
    else if (k === "t" || k === "T") this.startTutorial();
  }

  keyTutorial(k) {
    if (k === "Escape" || k === "m" || k === "M") { this.state = STATE_MENU; return; }
    if (k === " ") {
      if (this.tutStep === 2) this.tutStep = 3;
      else if (this.tutStep === 3) this.state = STATE_MENU;
      return;
    }
    let dir = null;
    const lk = k.length === 1 ? k.toLowerCase() : k;
    for (const d of MOVE_DIRS) if (lk === this.profile.keymap[d]) { dir = DIR_VECTORS[d]; break; }
    if (!dir) {
      const arrows = { ArrowUp: UP, ArrowDown: DOWN, ArrowLeft: LEFT, ArrowRight: RIGHT };
      dir = arrows[k];
    }
    if (dir) this.tutorialInput(dir);
  }

  keySettings(k) {
    if (k === "1") this.openSub(STATE_LANG);
    else if (k === "2") this.openSub(STATE_COLOR);
    else if (k === "3") this.openSub(STATE_THEME);
    else if (k === "4") this.openSub(STATE_AUDIO);
    else if (k === "5") this.openSub(STATE_CONTROLS);
    else if (k === "6") { this.nameBuffer = this.profile.name; this.openSub(STATE_NAME); }
    else if (k === "Escape") this.state = STATE_MENU;
  }

  keyTheme(k) {
    if (k === "Escape") this.state = this.subReturn;
    else if (k >= "1" && k <= "4") {
      const idx = k.charCodeAt(0) - 49;
      if (idx < THEME_ORDER.length) { this.profile.theme = THEME_ORDER[idx]; applyTheme(this.profile.theme); saveProfile(this.profile); }
    }
  }

  keyAudio(k) {
    if (k === "Escape") this.state = this.subReturn;
    else if (k === "1") this.dispatch("toggle_sound");
    else if (k === "2") this.dispatch("toggle_music");
    else if (k === "3") this.dispatch("toggle_fps");
  }

  keyControls(k) {
    if (k === "Escape") this.state = this.subReturn;
    else if (k === "r" || k === "R") this.dispatch("reset_keys");
    else if (k >= "1" && k <= "4") { this.rebindDir = MOVE_DIRS[k.charCodeAt(0) - 49]; this.state = STATE_REBIND; }
  }

  keyRebind(k) {
    if (k === "Escape") { this.rebindDir = null; this.state = STATE_CONTROLS; return; }
    if (this.rebindDir) {
      this.profile.keymap[this.rebindDir] = k.length === 1 ? k.toLowerCase() : k;
      saveProfile(this.profile);
      this.sound.play("select");
    }
    this.rebindDir = null;
    this.state = STATE_CONTROLS;
  }

  keyAiMenu(k) {
    let idx = null;
    if (k >= "1" && k <= "9") idx = k.charCodeAt(0) - 49;
    else if (k === "0") idx = 9; // the tenth entry
    if (idx !== null && idx < AI_MENU_MODES.length) { this.mode = AI_MENU_MODES[idx]; this.startRound(); }
    else if (k === "Escape") this.state = STATE_MENU;
  }

  keyReady(k) {
    if (k === " ") this.state = STATE_PLAY;
    else if (k === "Escape" || k === "m" || k === "M") this.state = STATE_MENU;
  }

  keyPlay(k) {
    if (this.replaying) {
      if (k === "m" || k === "M" || k === "Escape") this.state = STATE_MENU;
      return; // no live control during playback
    }
    if (k === "m" || k === "M" || k === "Escape") { this.state = STATE_MENU; return; }
    if (!this.snakes.length) return;
    const p1 = this.snakes[0];
    const arrows = { ArrowUp: UP, ArrowDown: DOWN, ArrowLeft: LEFT, ArrowRight: RIGHT };
    if (!p1.isAi) {
      const lk = k.length === 1 ? k.toLowerCase() : k;
      for (const d of MOVE_DIRS) {
        if (lk === this.profile.keymap[d]) { this.recordInput(0, DIR_VECTORS[d]); break; }
      }
      if (this.snakes.length === 1 && arrows[k]) this.recordInput(0, arrows[k]);
    }
    if (this.mode === BATTLE && this.snakes.length > 1 && arrows[k]) {
      this.recordInput(1, arrows[k]);
    }
  }

  keyOver(k) {
    if (k === " ") {
      if (this.replaying && this.currentReplay) this.startReplay(this.currentReplay);
      else this.startRound();
    } else if (k === "m" || k === "M" || k === "Escape") this.state = STATE_MENU;
  }

  keyColor(k) {
    if (k === "Escape") this.state = this.subReturn;
    else if (k >= "1" && k <= "9") { this.profile.colorIndex = k.charCodeAt(0) - 49; saveProfile(this.profile); }
    else if (k === "ArrowLeft") { this.profile.colorIndex = (this.profile.colorIndex - 1 + SNAKE_COLORS.length) % SNAKE_COLORS.length; saveProfile(this.profile); }
    else if (k === "ArrowRight") { this.profile.colorIndex = (this.profile.colorIndex + 1) % SNAKE_COLORS.length; saveProfile(this.profile); }
  }

  keyLang(k) {
    if (k === "Escape") this.state = this.subReturn;
    else if (k >= "1" && k <= "3") { this.profile.language = LANG_ORDER[k.charCodeAt(0) - 49]; saveProfile(this.profile); }
  }

  // -- Main loop --------------------------------------------------------
  loop(ts) {
    const dt = this.lastTs ? ts - this.lastTs : 0;
    this.lastTs = ts;
    if (dt > 0) this.fps = this.fps ? this.fps * 0.9 + (1000 / dt) * 0.1 : 1000 / dt;
    if (this.levelUpFlash > 0) this.levelUpFlash -= dt;
    this.update(dt);
    this.draw();
    requestAnimationFrame((t) => this.loop(t));
  }
}

// Fold the drawing methods into the prototype (mirrors SnakeGame(RenderMixin)).
Object.assign(Game.prototype, RenderMixin);
