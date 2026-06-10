/* Snake_Game_Python — browser edition.
 *
 * A faithful HTML5 Canvas port of the Python/Pygame game: eight modes across
 * two menus, a clickable GUI with an on-screen D-pad, three languages, a BFS
 * AI with a survival fallback, a perfect Hamiltonian-cycle fill AI, an
 * automatic update check against GitHub Releases, and localStorage saves.
 *
 * Credits — Creators: SpaceSquare, Claude Code · Owner: SpaceSquare
 * Released under a custom license (see the repository LICENSE). Any derivative
 * work, modification, or re-upload must clearly credit the creators and owner.
 */
"use strict";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const APP_VERSION = "1.1.1";
const GITHUB_REPO = "SpaceSquare640/Snake_Game_Python";

const CELL = 28;
const COLS = 24;
const ROWS = 22; // even -> a grid Hamiltonian cycle always exists
const HUD_HEIGHT = CELL * 2;
const CONTROL_HEIGHT = 112;
const PLAY_WIDTH = COLS * CELL;
const PLAY_HEIGHT = ROWS * CELL;
const PLAY_TOP = HUD_HEIGHT;
const CONTROL_TOP = HUD_HEIGHT + PLAY_HEIGHT;
const WIDTH = PLAY_WIDTH;
const HEIGHT = PLAY_HEIGHT + HUD_HEIGHT + CONTROL_HEIGHT;

// Colors — 60-30-10 split (black base / panel fills / accent highlights).
const C = {
  black: "#0f0f14", dark: "#181820", panel: "#1e1f28", panelHover: "#2c2e3a",
  grid: "#22222c", border: "#3a3c4a", white: "#ececf1", grey: "#8c8c96",
  dim: "#565862", divider: "#363846", red: "#dc4646", gold: "#f0c85a",
  food: "#eb505a", accent: "#76c4a2", accentDeep: "#469678",
  obstacle: "#464656",
};
const SNAKE_COLORS = [
  "#5ac878", "#5aaaeb", "#ebb450", "#c86eeb", "#eb6e96",
  "#6edcdc", "#eb825a", "#b4dc5a", "#e6e6eb",
];
const OPPONENT_COLOR = "#eb5a5a";
const BTN_RADIUS = 12;

const UP = [0, -1], DOWN = [0, 1], LEFT = [-1, 0], RIGHT = [1, 0];

// Modes
const CLASSIC = 0, SURVIVAL = 1, BATTLE = 2, LEVEL = 3,
      AI_HUMAN = 4, PLAYER_FILL = 5, AI_AI = 6, AI_FILL = 7;
const MODE_KEYS = [
  "classic", "survival", "battle", "level",
  "ai_human", "player_fill", "ai_ai", "ai_fill",
];
const MAIN_MENU_MODES = [CLASSIC, SURVIVAL, BATTLE, LEVEL, AI_HUMAN, PLAYER_FILL];
const AI_MENU_MODES = [AI_AI, AI_FILL];
const TWO_SNAKE_MODES = new Set([BATTLE, AI_AI, AI_HUMAN]);
const FILL_MODES = new Set([PLAYER_FILL, AI_FILL]);

// States
const STATE_MENU = 0, STATE_READY = 1, STATE_PLAY = 2, STATE_OVER = 3,
      STATE_COLOR = 4, STATE_LANG = 5, STATE_NAME = 6, STATE_SETTINGS = 7,
      STATE_AI_MENU = 8;

const LANG_ORDER = ["en", "zh_tw", "zh_cn"];

// ---------------------------------------------------------------------------
// Translations
// ---------------------------------------------------------------------------
const T = {
  en: {
    title: "SNAKE", classic: "Classic", survival: "Survival", battle: "Battle",
    level: "Level", ai_ai: "AI vs AI", ai_human: "AI vs Human",
    player_fill: "Player Fill", ai_fill: "AI Fill",
    press_space: "Press SPACE / a button to start", game_over: "GAME OVER",
    you_win: "YOU WIN!", board_filled: "Board filled — {n} cells!",
    press_space_restart: "Play again", score: "Score", filled: "Filled",
    high: "Best", level_label: "Lv", stage: "Stage", p1: "P1", p2: "P2",
    ai: "AI", you: "You", winner: "{name} wins!", draw: "Draw!",
    watching: "Watching AI…", menu_hint: "Click a mode or press 1-6  ·  ESC back",
    ai_modes: "All-AI Modes", settings: "Settings", settings_title: "Settings",
    ai_menu_title: "All-AI Modes", color_btn: "Snake Color", lang_btn: "Language",
    name_btn: "Player Name", menu_btn: "Menu", back: "Back",
    color_menu: "Choose snake color", lang_menu: "Choose language",
    name_menu: "Enter your name", name_hint: "Type a name, ENTER to confirm",
    back_hint: "ESC / Back", level_up: "Level up!  Lv {lvl}", xp: "XP",
    english: "English", tchinese: "Traditional Chinese", schinese: "Simplified Chinese",
    credits: "Creators: SpaceSquare, Claude Code   ·   Owner: SpaceSquare",
  },
  zh_tw: {
    title: "貪食蛇", classic: "經典模式", survival: "生存模式", battle: "對戰模式",
    level: "關卡模式", ai_ai: "AI 對 AI", ai_human: "AI 對 玩家",
    player_fill: "玩家填滿", ai_fill: "AI 填滿",
    press_space: "按空白鍵／按鈕開始", game_over: "遊戲結束",
    you_win: "你贏了！", board_filled: "場地已填滿 — {n} 格！",
    press_space_restart: "再玩一次", score: "分數", filled: "已填滿",
    high: "最高", level_label: "等級", stage: "關卡", p1: "玩家1", p2: "玩家2",
    ai: "AI", you: "你", winner: "{name} 獲勝！", draw: "平手！",
    watching: "觀看 AI…", menu_hint: "點選模式或按 1-6  ·  ESC 返回",
    ai_modes: "全 AI 模式", settings: "設定", settings_title: "設定",
    ai_menu_title: "全 AI 模式", color_btn: "蛇身顏色", lang_btn: "語言",
    name_btn: "玩家名稱", menu_btn: "選單", back: "返回",
    color_menu: "選擇蛇身顏色", lang_menu: "選擇語言",
    name_menu: "輸入你的名稱", name_hint: "輸入名稱，按 ENTER 確認",
    back_hint: "ESC／返回", level_up: "升級！等級 {lvl}", xp: "經驗",
    english: "英文 English", tchinese: "繁體中文", schinese: "簡體中文",
    credits: "創作者：SpaceSquare、Claude Code   ·   擁有者：SpaceSquare",
  },
  zh_cn: {
    title: "贪食蛇", classic: "经典模式", survival: "生存模式", battle: "对战模式",
    level: "关卡模式", ai_ai: "AI 对 AI", ai_human: "AI 对 玩家",
    player_fill: "玩家填满", ai_fill: "AI 填满",
    press_space: "按空格键／按钮开始", game_over: "游戏结束",
    you_win: "你赢了！", board_filled: "场地已填满 — {n} 格！",
    press_space_restart: "再玩一次", score: "分数", filled: "已填满",
    high: "最高", level_label: "等级", stage: "关卡", p1: "玩家1", p2: "玩家2",
    ai: "AI", you: "你", winner: "{name} 获胜！", draw: "平局！",
    watching: "观看 AI…", menu_hint: "点选模式或按 1-6  ·  ESC 返回",
    ai_modes: "全 AI 模式", settings: "设置", settings_title: "设置",
    ai_menu_title: "全 AI 模式", color_btn: "蛇身颜色", lang_btn: "语言",
    name_btn: "玩家名称", menu_btn: "菜单", back: "返回",
    color_menu: "选择蛇身颜色", lang_menu: "选择语言",
    name_menu: "输入你的名称", name_hint: "输入名称，按 ENTER 确认",
    back_hint: "ESC／返回", level_up: "升级！等级 {lvl}", xp: "经验",
    english: "英文 English", tchinese: "繁体中文", schinese: "简体中文",
    credits: "创作者：SpaceSquare、Claude Code   ·   拥有者：SpaceSquare",
  },
};

// ---------------------------------------------------------------------------
// Save data (localStorage)
// ---------------------------------------------------------------------------
const SAVE_KEY = "snake_game_python_save";

function defaultProfile() {
  const highscores = {};
  for (const k of MODE_KEYS) highscores[k] = 0;
  return { name: "Player", language: "en", colorIndex: 0, level: 1, xp: 0, highscores };
}

function xpForLevel(level) { return 50 * level; }

function loadProfile() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return defaultProfile();
    const data = JSON.parse(raw);
    const p = defaultProfile();
    p.name = (String(data.name || "Player").slice(0, 14)) || "Player";
    p.language = LANG_ORDER.includes(data.language) ? data.language : "en";
    p.colorIndex = ((data.colorIndex | 0) % SNAKE_COLORS.length + SNAKE_COLORS.length) % SNAKE_COLORS.length;
    p.level = Math.max(1, data.level | 0 || 1);
    p.xp = Math.max(0, data.xp | 0);
    const hs = data.highscores || {};
    for (const k of MODE_KEYS) p.highscores[k] = hs[k] | 0;
    return p;
  } catch (e) {
    return defaultProfile();
  }
}

function saveProfile(p) {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(p)); } catch (e) { /* ignore */ }
}

function addScore(p, modeKey, score) {
  if (score > (p.highscores[modeKey] || 0)) p.highscores[modeKey] = score;
  p.xp += score;
  let levelled = false;
  while (p.xp >= xpForLevel(p.level)) {
    p.xp -= xpForLevel(p.level);
    p.level += 1;
    levelled = true;
  }
  return levelled;
}

// ---------------------------------------------------------------------------
// Grid / AI helpers
// ---------------------------------------------------------------------------
const key = (x, y) => x + "," + y;
const inBounds = (x, y) => x >= 0 && x < COLS && y >= 0 && y < ROWS;

function neighbors(x, y) {
  return [
    [x + 1, y, RIGHT], [x - 1, y, LEFT], [x, y + 1, DOWN], [x, y - 1, UP],
  ];
}

function bfsDirection(sx, sy, gx, gy, blocked) {
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

function floodFree(sx, sy, blocked) {
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

function survivalDirection(hx, hy, blocked, curDir) {
  let bestDir = null, bestScore = -1;
  for (const [nx, ny, dir] of neighbors(hx, hy)) {
    if (dir[0] === -curDir[0] && dir[1] === -curDir[1]) continue;
    if (!inBounds(nx, ny) || blocked.has(key(nx, ny))) continue;
    const score = floodFree(nx, ny, blocked);
    if (score > bestScore) { bestScore = score; bestDir = dir; }
  }
  return bestDir;
}

// Hamiltonian cycle (requires even ROWS). Returns a Map cell -> next cell.
function buildHamiltonianCycle(cols, rows) {
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

// ---------------------------------------------------------------------------
// Snake
// ---------------------------------------------------------------------------
class Snake {
  constructor(body, dir, color, isAi = false) {
    this.body = body.map((c) => [c[0], c[1]]); // head at index 0
    this.dir = dir;
    this.pending = dir;
    this.color = color;
    this.isAi = isAi;
    this.alive = true;
    this.growPending = 0;
    this.score = 0;
    this.cycle = null;
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

// ---------------------------------------------------------------------------
// Game
// ---------------------------------------------------------------------------
class Game {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.profile = loadProfile();
    this.state = STATE_MENU;
    this.mode = CLASSIC;
    this.subReturn = STATE_MENU;

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
    fetch("https://api.github.com/repos/" + GITHUB_REPO + "/releases/latest", {
      headers: { "Accept": "application/vnd.github+json" },
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        const tag = (data && data.tag_name) || "";
        if (!tag) { this.updateState = "unknown"; return; }
        this.latestVersion = tag;
        this.updateState = parseVersion(tag) > parseVersion(APP_VERSION) ? "outdated" : "latest";
      })
      .catch(() => { this.updateState = "unknown"; });
  }

  // -- Round setup ------------------------------------------------------
  startRound() {
    this.obstacles = new Set();
    this.stage = 1;
    this.resultText = "";
    this.win = false;
    this.food = null;
    const color = SNAKE_COLORS[this.profile.colorIndex];
    const midY = Math.floor(ROWS / 2);

    if (TWO_SNAKE_MODES.has(this.mode)) {
      const left = new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color);
      const right = new Snake(
        [[COLS - 5, midY], [COLS - 4, midY], [COLS - 3, midY]], LEFT, OPPONENT_COLOR);
      if (this.mode === AI_AI) { left.isAi = true; right.isAi = true; }
      else if (this.mode === AI_HUMAN) { right.isAi = true; }
      this.snakes = [left, right];
    } else if (this.mode === AI_FILL) {
      const { seq, next } = buildHamiltonianCycle(COLS, ROWS);
      const s = new Snake([[seq[0][0], seq[0][1]]], RIGHT, color, true);
      s.cycle = next;
      this.snakes = [s];
    } else if (this.mode === PLAYER_FILL) {
      this.snakes = [new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color)];
    } else {
      this.snakes = [new Snake([[4, midY], [3, midY], [2, midY]], RIGHT, color)];
      if (this.mode === LEVEL) this.buildStage(this.stage);
    }

    if (!FILL_MODES.has(this.mode)) this.food = this.spawnFood();
    this.tickMs = this.baseTick();
    this.moveAccum = 0;
    this.state = STATE_READY;
  }

  baseTick() {
    return {
      [CLASSIC]: 120, [SURVIVAL]: 140, [BATTLE]: 110, [LEVEL]: 120,
      [AI_HUMAN]: 90, [PLAYER_FILL]: 100, [AI_AI]: 70, [AI_FILL]: 26,
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
    return free.length ? free[(Math.random() * free.length) | 0] : null;
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

  // -- Update -----------------------------------------------------------
  update(dt) {
    if (this.state !== STATE_PLAY) return;
    this.moveAccum += dt;
    if (this.moveAccum < this.tickMs) return;
    this.moveAccum -= this.tickMs;
    this.advance();
  }

  advance() {
    for (const s of this.snakes) {
      if (s.isAi && s.alive) {
        if (s.cycle) s.planCycle();
        else s.planAi(this.food, this.blockedFor(s));
      }
    }
    if (FILL_MODES.has(this.mode)) {
      for (const s of this.snakes) if (s.alive) s.grow(1);
    }
    for (const s of this.snakes) if (s.alive) s.step();
    this.resolveCollisions();
    if (!FILL_MODES.has(this.mode)) this.resolveFood();
    this.checkRoundEnd();
  }

  blockedFor(snake) {
    const blocked = new Set(this.obstacles);
    for (const other of this.snakes) {
      if (other === snake) {
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
      const s = this.snakes[0];
      if (s.body.length >= total) {
        this.win = true;
        this.resultText = this.t("board_filled", { n: s.body.length });
        this.endRound(s.body.length);
      } else if (!s.alive) {
        this.endRound(s.body.length);
      }
      return;
    }
    const alive = this.snakes.filter((s) => s.alive);
    if (TWO_SNAKE_MODES.has(this.mode)) {
      if (alive.length <= 1) this.finishVersus(alive);
    } else {
      if (alive.length === 0) this.endRound(this.snakes[0].score);
    }
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
    if (this.mode === AI_AI) return this.t("ai") + " " + (index + 1);
    if (this.mode === AI_HUMAN) return index === 0 ? this.t("you") : this.t("ai");
    return this.t("player");
  }

  endRound(score) {
    const levelled = addScore(this.profile, MODE_KEYS[this.mode], score);
    if (levelled) this.levelUpFlash = 1800;
    saveProfile(this.profile);
    this.state = STATE_OVER;
  }

  humanSnake() {
    if (!this.snakes.length) return null;
    const first = this.snakes[0];
    return first.isAi ? null : first;
  }

  // -- Input ------------------------------------------------------------
  bindInput() {
    window.addEventListener("keydown", (e) => this.onKey(e));
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
    this.canvas.addEventListener("click", (e) => {
      const p = toLocal(e.clientX, e.clientY);
      this.handleClick(p.x, p.y);
    });
    // Touch: treat as pointer + click.
    this.canvas.addEventListener("touchstart", (e) => {
      e.preventDefault();
      const tp = e.changedTouches[0];
      const p = toLocal(tp.clientX, tp.clientY);
      this.pointer = p;
      this.handleClick(p.x, p.y);
    }, { passive: false });
  }

  handleClick(x, y) {
    for (let i = this.buttons.length - 1; i >= 0; i--) {
      const b = this.buttons[i];
      if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
        this.dispatch(b.action, b.arg);
        return;
      }
    }
  }

  dispatch(action, arg) {
    switch (action) {
      case "start_mode": this.mode = arg; this.startRound(); break;
      case "open_ai_menu": this.state = STATE_AI_MENU; break;
      case "open_settings": this.state = STATE_SETTINGS; break;
      case "open_color": this.openSub(STATE_COLOR); break;
      case "open_lang": this.openSub(STATE_LANG); break;
      case "open_name": this.nameBuffer = this.profile.name; this.openSub(STATE_NAME); break;
      case "set_lang": this.profile.language = arg; saveProfile(this.profile); break;
      case "set_color": this.profile.colorIndex = arg; saveProfile(this.profile); break;
      case "back_menu": this.state = STATE_MENU; break;
      case "sub_back": this.state = this.subReturn; break;
      case "to_menu": this.state = STATE_MENU; break;
      case "restart": this.startRound(); break;
      case "dir":
        if (this.state === STATE_READY) this.state = STATE_PLAY;
        { const h = this.humanSnake(); if (h) h.setDirection(arg); }
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
    // Prevent the page from scrolling on arrows/space.
    if ([" ", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(k)) e.preventDefault();

    if (this.state === STATE_MENU) this.keyMenu(k);
    else if (this.state === STATE_SETTINGS) this.keySettings(k);
    else if (this.state === STATE_AI_MENU) this.keyAiMenu(k);
    else if (this.state === STATE_READY) this.keyReady(k);
    else if (this.state === STATE_PLAY) this.keyPlay(k);
    else if (this.state === STATE_OVER) this.keyOver(k);
    else if (this.state === STATE_COLOR) this.keyColor(k);
    else if (this.state === STATE_LANG) this.keyLang(k);
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
  }

  keySettings(k) {
    if (k === "1") this.openSub(STATE_LANG);
    else if (k === "2") this.openSub(STATE_COLOR);
    else if (k === "3") { this.nameBuffer = this.profile.name; this.openSub(STATE_NAME); }
    else if (k === "Escape") this.state = STATE_MENU;
  }

  keyAiMenu(k) {
    if (k >= "1" && k <= "2") {
      const idx = k.charCodeAt(0) - 49;
      if (idx < AI_MENU_MODES.length) { this.mode = AI_MENU_MODES[idx]; this.startRound(); }
    } else if (k === "Escape") this.state = STATE_MENU;
  }

  keyReady(k) {
    if (k === " ") this.state = STATE_PLAY;
    else if (k === "Escape" || k === "m" || k === "M") this.state = STATE_MENU;
  }

  keyPlay(k) {
    if (k === "m" || k === "M") { this.state = STATE_MENU; return; }
    if (k === "Escape") { this.state = STATE_MENU; return; }
    if (!this.snakes.length) return;
    const p1 = this.snakes[0];
    if (!p1.isAi) {
      if (k === "w" || k === "W") p1.setDirection(UP);
      else if (k === "s" || k === "S") p1.setDirection(DOWN);
      else if (k === "a" || k === "A") p1.setDirection(LEFT);
      else if (k === "d" || k === "D") p1.setDirection(RIGHT);
      if (this.snakes.length === 1) {
        if (k === "ArrowUp") p1.setDirection(UP);
        else if (k === "ArrowDown") p1.setDirection(DOWN);
        else if (k === "ArrowLeft") p1.setDirection(LEFT);
        else if (k === "ArrowRight") p1.setDirection(RIGHT);
      }
    }
    if (this.mode === BATTLE && this.snakes.length > 1) {
      const p2 = this.snakes[1];
      if (k === "ArrowUp") p2.setDirection(UP);
      else if (k === "ArrowDown") p2.setDirection(DOWN);
      else if (k === "ArrowLeft") p2.setDirection(LEFT);
      else if (k === "ArrowRight") p2.setDirection(RIGHT);
    }
  }

  keyOver(k) {
    if (k === " ") this.startRound();
    else if (k === "m" || k === "M" || k === "Escape") this.state = STATE_MENU;
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

  // -- Rendering --------------------------------------------------------
  loop(ts) {
    const dt = this.lastTs ? ts - this.lastTs : 0;
    this.lastTs = ts;
    if (this.levelUpFlash > 0) this.levelUpFlash -= dt;
    this.update(dt);
    this.draw();
    requestAnimationFrame((t) => this.loop(t));
  }

  draw() {
    this.buttons = [];
    const ctx = this.ctx;
    ctx.fillStyle = C.black;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    switch (this.state) {
      case STATE_MENU: this.drawMenu(); break;
      case STATE_SETTINGS: this.drawSettings(); break;
      case STATE_AI_MENU: this.drawAiMenu(); break;
      case STATE_COLOR: this.drawColorMenu(); break;
      case STATE_LANG: this.drawLangMenu(); break;
      case STATE_NAME: this.drawNameMenu(); break;
      default:
        this.drawPlayArea();
        this.drawHud();
        this.drawControlBar();
        if (this.state === STATE_READY) this.drawCenterBanner(this.t("press_space"));
        else if (this.state === STATE_OVER) this.drawGameOver();
    }
  }

  font(size, bold) { return (bold ? "bold " : "") + size + 'px "Segoe UI","Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif'; }

  text(str, size, color, x, y, align = "center", bold = false) {
    const ctx = this.ctx;
    ctx.font = this.font(size, bold);
    ctx.fillStyle = color;
    ctx.textAlign = align;
    ctx.textBaseline = "middle";
    ctx.fillText(str, x, y);
  }

  roundRect(x, y, w, h, r) {
    const ctx = this.ctx;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, w, h, r);
    else {
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }
  }

  hovered(b) {
    return this.pointer.x >= b.x && this.pointer.x <= b.x + b.w &&
           this.pointer.y >= b.y && this.pointer.y <= b.y + b.h;
  }

  button(b) {
    const ctx = this.ctx;
    const hover = this.hovered(b);
    ctx.save();
    if (hover && !b.selected) { ctx.shadowColor = C.accent; ctx.shadowBlur = 18; }
    ctx.fillStyle = b.selected ? C.accent : (hover ? C.panelHover : C.panel);
    this.roundRect(b.x, b.y, b.w, b.h, b.radius || BTN_RADIUS);
    ctx.fill();
    ctx.restore();
    ctx.lineWidth = (hover || b.selected) ? 2 : 1;
    ctx.strokeStyle = (hover || b.selected) ? C.accent : C.border;
    this.roundRect(b.x, b.y, b.w, b.h, b.radius || BTN_RADIUS);
    ctx.stroke();

    let cx = b.x + b.w / 2;
    if (b.swatch) {
      const s = 20;
      ctx.fillStyle = b.swatch;
      this.roundRect(b.x + 16, b.y + b.h / 2 - s / 2, s, s, 6); ctx.fill();
      ctx.strokeStyle = C.border; ctx.lineWidth = 1;
      this.roundRect(b.x + 16, b.y + b.h / 2 - s / 2, s, s, 6); ctx.stroke();
      cx += 16;
    }
    if (b.sub) {
      this.text(b.label, b.font || 22, b.selected ? C.black : C.white, cx, b.y + b.h / 2 - 9);
      this.text(b.sub, 15, C.grey, cx, b.y + b.h / 2 + 13);
    } else {
      this.text(b.label, b.font || 22, b.selected ? C.black : C.white, cx, b.y + b.h / 2);
    }
    this.buttons.push(b);
  }

  // -- Menus ------------------------------------------------------------
  drawMenu() {
    this.text(this.t("title"), 60, C.accent, WIDTH / 2, 104, "center", true);
    this.text(this.t("credits"), 15, C.dim, WIDTH / 2, 144);
    this.drawStatusCorner();

    const bw = 290, bh = 64, gap = 20, srowH = 56;
    const blockH = 3 * bh + 2 * gap + 22 + srowH;
    const bandTop = 176, bandBottom = HEIGHT - 120;
    const startX = (WIDTH - (2 * bw + gap)) / 2;
    const startY = bandTop + Math.max(0, (bandBottom - bandTop - blockH) / 2);

    MAIN_MENU_MODES.forEach((mode, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = startX + col * (bw + gap), y = startY + row * (bh + gap);
      const k = MODE_KEYS[mode];
      this.button({ x, y, w: bw, h: bh, label: this.t(k),
        sub: this.t("high") + ": " + this.profile.highscores[k],
        action: "start_mode", arg: mode });
    });

    const rowY = startY + 3 * (bh + gap) + 22;
    this.button({ x: startX, y: rowY, w: bw, h: srowH, label: this.t("ai_modes"), action: "open_ai_menu" });
    this.button({ x: startX + bw + gap, y: rowY, w: bw, h: srowH, label: this.t("settings"), action: "open_settings" });

    this.drawProfileCard(HEIGHT - 98);
    this.text(this.t("menu_hint"), 15, C.dim, WIDTH / 2, HEIGHT - 32);
  }

  drawStatusCorner() {
    const dotColors = { checking: C.grey, latest: C.accent, outdated: C.gold, unknown: C.dim };
    const dot = dotColors[this.updateState] || C.dim;
    let label, color;
    if (this.updateState === "outdated" && this.latestVersion) {
      label = "v" + APP_VERSION + " → " + this.latestVersion; color = C.gold;
    } else { label = "v" + APP_VERSION; color = C.grey; }
    const ctx = this.ctx;
    ctx.font = this.font(15, false);
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    ctx.fillStyle = color;
    ctx.fillText(label, WIDTH - 16, 18);
    const w = ctx.measureText(label).width;
    ctx.beginPath();
    ctx.fillStyle = dot;
    ctx.arc(WIDTH - 16 - w - 10, 19, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  drawProfileCard(top) {
    const ctx = this.ctx;
    const p = this.profile;
    const cardW = 478, cardH = 52;
    const x = (WIDTH - cardW) / 2;
    ctx.fillStyle = C.panel;
    this.roundRect(x, top, cardW, cardH, BTN_RADIUS); ctx.fill();
    ctx.strokeStyle = C.border; ctx.lineWidth = 1;
    this.roundRect(x, top, cardW, cardH, BTN_RADIUS); ctx.stroke();

    const cy = top + cardH / 2;
    const d1 = x + 214, d2 = x + 332;
    ctx.strokeStyle = C.divider; ctx.lineWidth = 1;
    for (const dx of [d1, d2]) {
      ctx.beginPath(); ctx.moveTo(dx, top + 11); ctx.lineTo(dx, top + cardH - 11); ctx.stroke();
    }
    const sw = 20;
    ctx.fillStyle = SNAKE_COLORS[p.colorIndex];
    this.roundRect(x + 18, cy - sw / 2, sw, sw, 6); ctx.fill();
    ctx.strokeStyle = C.border;
    this.roundRect(x + 18, cy - sw / 2, sw, sw, 6); ctx.stroke();
    this.text(p.name, 22, C.white, x + 18 + sw + 12, cy, "left");
    this.text(this.t("level_label") + " " + p.level, 22, C.accent, (d1 + d2) / 2, cy);
    this.text(this.t("xp") + " " + p.xp + "/" + xpForLevel(p.level), 22, C.grey, (d2 + x + cardW) / 2, cy);
  }

  drawSettings() {
    this.text(this.t("settings_title"), 60, C.accent, WIDTH / 2, 90, "center", true);
    const bw = 360, bh = 60, x = (WIDTH - bw) / 2;
    const langLabel = { en: "English", zh_tw: "繁體中文", zh_cn: "简体中文" }[this.profile.language];
    this.button({ x, y: 180, w: bw, h: bh, label: "1.  " + this.t("lang_btn") + ":  " + langLabel, action: "open_lang" });
    this.button({ x, y: 180 + bh + 18, w: bw, h: bh, label: "2.  " + this.t("color_btn"), action: "open_color", swatch: SNAKE_COLORS[this.profile.colorIndex] });
    this.button({ x, y: 180 + 2 * (bh + 18), w: bw, h: bh, label: "3.  " + this.t("name_btn") + ":  " + this.profile.name, action: "open_name" });
    this.button({ x, y: 180 + 3 * (bh + 18) + 12, w: bw, h: 50, label: this.t("back"), action: "back_menu" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 36);
  }

  drawAiMenu() {
    this.text(this.t("ai_menu_title"), 60, C.accent, WIDTH / 2, 90, "center", true);
    const bw = 360, bh = 64, x = (WIDTH - bw) / 2;
    AI_MENU_MODES.forEach((mode, i) => {
      const k = MODE_KEYS[mode];
      this.button({ x, y: 190 + i * (bh + 20), w: bw, h: bh,
        label: (i + 1) + ".  " + this.t(k) + "   (" + this.t("high") + ": " + this.profile.highscores[k] + ")",
        action: "start_mode", arg: mode });
    });
    this.button({ x, y: 190 + AI_MENU_MODES.length * (bh + 20) + 10, w: bw, h: 50, label: this.t("back"), action: "back_menu" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 36);
  }

  drawColorMenu() {
    this.text(this.t("color_menu"), 32, C.accent, WIDTH / 2, 70);
    const ctx = this.ctx;
    const cols = 3, size = 80, gap = 30;
    const totalW = cols * size + (cols - 1) * gap;
    const startX = (WIDTH - totalW) / 2, startY = 130;
    SNAKE_COLORS.forEach((color, i) => {
      const x = startX + (i % cols) * (size + gap);
      const y = startY + Math.floor(i / cols) * (size + gap);
      const b = { x, y, w: size, h: size };
      const hover = this.hovered(b);
      const selected = i === this.profile.colorIndex;
      ctx.save();
      if (hover || selected) { ctx.shadowColor = C.accent; ctx.shadowBlur = 18; }
      ctx.fillStyle = color;
      this.roundRect(x, y, size, size, 12); ctx.fill();
      ctx.restore();
      if (selected) {
        ctx.strokeStyle = C.accent; ctx.lineWidth = 3;
        this.roundRect(x - 5, y - 5, size + 10, size + 10, 14); ctx.stroke();
      }
      this.text(String(i + 1), 22, C.black, x + size / 2, y + size / 2);
      this.buttons.push({ x, y, w: size, h: size, action: "set_color", arg: i });
    });
    this.button({ x: WIDTH / 2 - 90, y: HEIGHT - 90, w: 180, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 28);
  }

  drawLangMenu() {
    this.text(this.t("lang_menu"), 32, C.accent, WIDTH / 2, 90);
    const options = [["english", "en"], ["tchinese", "zh_tw"], ["schinese", "zh_cn"]];
    const bw = 360, bh = 60, x = (WIDTH - bw) / 2;
    options.forEach((opt, i) => {
      this.button({ x, y: 180 + i * (bh + 18), w: bw, h: bh,
        label: (i + 1) + ".  " + this.t(opt[0]), action: "set_lang", arg: opt[1],
        selected: this.profile.language === opt[1] });
    });
    this.button({ x, y: 180 + 3 * (bh + 18) + 10, w: bw, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  }

  drawNameMenu() {
    const ctx = this.ctx;
    this.text(this.t("name_menu"), 32, C.accent, WIDTH / 2, 110);
    const bx = WIDTH / 2 - 160, by = 190, bw = 320, bh = 56;
    ctx.fillStyle = C.dark;
    this.roundRect(bx, by, bw, bh, 8); ctx.fill();
    ctx.strokeStyle = C.accent; ctx.lineWidth = 2;
    this.roundRect(bx, by, bw, bh, 8); ctx.stroke();
    const cursor = (Math.floor(performance.now() / 400) % 2 === 0) ? "_" : " ";
    this.text(this.nameBuffer + cursor, 32, C.white, WIDTH / 2, by + bh / 2);
    this.text(this.t("name_hint"), 22, C.grey, WIDTH / 2, 290);
    this.button({ x: WIDTH / 2 - 90, y: 340, w: 180, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  }

  // -- Play area --------------------------------------------------------
  cellRect(x, y, color, inset, radius) {
    const ctx = this.ctx;
    ctx.fillStyle = color;
    this.roundRect(x * CELL + inset, PLAY_TOP + y * CELL + inset, CELL - inset * 2, CELL - inset * 2, radius);
    ctx.fill();
  }

  drawPlayArea() {
    const ctx = this.ctx;
    ctx.fillStyle = C.dark;
    ctx.fillRect(0, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT);
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x <= COLS; x++) { ctx.moveTo(x * CELL, PLAY_TOP); ctx.lineTo(x * CELL, CONTROL_TOP); }
    for (let y = 0; y <= ROWS; y++) { ctx.moveTo(0, PLAY_TOP + y * CELL); ctx.lineTo(PLAY_WIDTH, PLAY_TOP + y * CELL); }
    ctx.stroke();

    for (const o of this.obstacles) {
      const [ox, oy] = o.split(",").map(Number);
      this.cellRect(ox, oy, C.obstacle, 1, 4);
    }
    if (this.food) this.cellRect(this.food[0], this.food[1], C.food, 5, 8);
    for (const s of this.snakes) this.drawSnake(s);
  }

  drawSnake(s) {
    const n = s.body.length;
    let base = toRGB(s.color);
    if (!s.alive) base = base.map((c) => Math.max(0, c - 80)); // dimmed when dead
    for (let i = 0; i < n; i++) {
      const f = 1 - (i / Math.max(1, n)) * 0.45; // head brightest, tail darker
      const color = "rgb(" + base.map((c) => Math.round(c * f)).join(",") + ")";
      this.cellRect(s.body[i][0], s.body[i][1], color, i ? 2 : 1, i ? 6 : 8);
    }
  }

  drawHud() {
    const ctx = this.ctx;
    ctx.fillStyle = C.black;
    ctx.fillRect(0, 0, WIDTH, HUD_HEIGHT);
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, HUD_HEIGHT); ctx.lineTo(WIDTH, HUD_HEIGHT); ctx.stroke();
    this.text(this.t(MODE_KEYS[this.mode]), 22, C.accent, 16, 22, "left");

    if (FILL_MODES.has(this.mode)) {
      this.text(this.t("filled") + ": " + this.snakes[0].body.length + " / " + (COLS * ROWS), 22, C.white, 16, 44, "left");
      this.text(this.t("high") + ": " + this.profile.highscores[MODE_KEYS[this.mode]], 22, C.grey, 280, 44, "left");
    } else if (TWO_SNAKE_MODES.has(this.mode)) {
      const parts = this.snakes.map((s, i) => this.snakeLabel(i) + ": " + s.score);
      this.text(parts.join("   "), 22, C.white, 16, 44, "left");
    } else {
      this.text(this.t("score") + ": " + this.snakes[0].score, 22, C.white, 16, 44, "left");
      this.text(this.t("high") + ": " + this.profile.highscores[MODE_KEYS[this.mode]], 22, C.grey, 180, 44, "left");
      if (this.mode === LEVEL) this.text(this.t("stage") + ": " + this.stage, 22, C.white, 320, 44, "left");
    }
  }

  drawControlBar() {
    const ctx = this.ctx;
    ctx.fillStyle = C.black;
    ctx.fillRect(0, CONTROL_TOP, WIDTH, CONTROL_HEIGHT);
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, CONTROL_TOP); ctx.lineTo(WIDTH, CONTROL_TOP); ctx.stroke();

    this.button({ x: 20, y: CONTROL_TOP + 36, w: 130, h: 44, label: this.t("menu_btn"), action: "to_menu" });

    if ((this.state === STATE_READY || this.state === STATE_PLAY) && this.humanSnake()) {
      this.drawDpad();
    } else {
      this.text(this.t("watching"), 22, C.grey, WIDTH - 150, CONTROL_TOP + CONTROL_HEIGHT / 2);
    }
  }

  drawDpad() {
    const cx = WIDTH - 110, cy = CONTROL_TOP + CONTROL_HEIGHT / 2, b = 40;
    const layout = [
      [UP, cx, cy - (b + 4)], [DOWN, cx, cy + (b + 4)],
      [LEFT, cx - (b + 4), cy], [RIGHT, cx + (b + 4), cy],
    ];
    const ctx = this.ctx;
    for (const [dir, bxc, byc] of layout) {
      const x = bxc - b / 2, y = byc - b / 2;
      const btn = { x, y, w: b, h: b };
      const hover = this.hovered(btn);
      ctx.save();
      if (hover) { ctx.shadowColor = C.accent; ctx.shadowBlur = 16; }
      ctx.fillStyle = hover ? C.panelHover : C.panel;
      this.roundRect(x, y, b, b, 10); ctx.fill();
      ctx.restore();
      ctx.strokeStyle = hover ? C.accent : C.border; ctx.lineWidth = hover ? 2 : 1;
      this.roundRect(x, y, b, b, 10); ctx.stroke();
      this.drawArrow(bxc, byc, dir, hover ? C.accent : C.white);
      this.buttons.push({ x, y, w: b, h: b, action: "dir", arg: dir });
    }
  }

  drawArrow(cx, cy, dir, color) {
    const ctx = this.ctx;
    const s = 9;
    ctx.fillStyle = color;
    ctx.beginPath();
    if (dir === UP) { ctx.moveTo(cx, cy - s); ctx.lineTo(cx - s, cy + s); ctx.lineTo(cx + s, cy + s); }
    else if (dir === DOWN) { ctx.moveTo(cx, cy + s); ctx.lineTo(cx - s, cy - s); ctx.lineTo(cx + s, cy - s); }
    else if (dir === LEFT) { ctx.moveTo(cx - s, cy); ctx.lineTo(cx + s, cy - s); ctx.lineTo(cx + s, cy + s); }
    else { ctx.moveTo(cx + s, cy); ctx.lineTo(cx - s, cy - s); ctx.lineTo(cx - s, cy + s); }
    ctx.closePath(); ctx.fill();
  }

  drawCenterBanner(str) {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.fillRect(0, PLAY_TOP, WIDTH, PLAY_HEIGHT);
    this.text(str, 32, C.white, WIDTH / 2, PLAY_TOP + PLAY_HEIGHT / 2);
  }

  drawGameOver() {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.72)";
    ctx.fillRect(0, PLAY_TOP, WIDTH, PLAY_HEIGHT);
    const cy = PLAY_TOP + PLAY_HEIGHT / 2;
    if (this.win) this.text(this.t("you_win"), 60, C.gold, WIDTH / 2, cy - 80, "center", true);
    else this.text(this.t("game_over"), 60, C.red, WIDTH / 2, cy - 80, "center", true);
    if (this.resultText) this.text(this.resultText, 32, C.white, WIDTH / 2, cy - 18);
    if (this.levelUpFlash > 0) this.text(this.t("level_up", { lvl: this.profile.level }), 22, C.accent, WIDTH / 2, cy + 18);
    this.button({ x: WIDTH / 2 - 200, y: cy + 50, w: 190, h: 50, label: this.t("press_space_restart"), action: "restart" });
    this.button({ x: WIDTH / 2 + 10, y: cy + 50, w: 190, h: 50, label: this.t("menu_btn"), action: "to_menu" });
  }
}

// ---------------------------------------------------------------------------
// Small utilities
// ---------------------------------------------------------------------------
function parseVersion(text) {
  const parts = String(text).trim().replace(/^v/i, "").split(".").map((c) => {
    const m = c.match(/^\d+/);
    return m ? parseInt(m[0], 10) : 0;
  });
  // Compare as a zero-padded number string.
  return parts.map((n) => String(n).padStart(5, "0")).join(".");
}

function toRGB(color) {
  // Parse "#rrggbb" or "rgb(r,g,b)" into [r, g, b].
  if (color[0] === "#") {
    const n = parseInt(color.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  const m = color.match(/\d+/g);
  return [parseInt(m[0], 10), parseInt(m[1], 10), parseInt(m[2], 10)];
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("game");
  window.snakeGame = new Game(canvas);
});
