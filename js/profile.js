/* Player profile persistence (localStorage). */
import {
  MODE_KEYS, MOVE_DIRS, DEFAULT_KEYMAP, LEADERBOARD_SIZE, REPLAY_LIMIT,
} from "./config.js";
import { SNAKE_COLORS, THEMES } from "./theme.js";
import { LANG_ORDER } from "./i18n.js";

const SAVE_KEY = "snake_game_python_save";

export function xpForLevel(level) { return 50 * level; }

export function defaultProfile() {
  const highscores = {}, leaderboards = {};
  for (const k of MODE_KEYS) { highscores[k] = 0; leaderboards[k] = []; }
  return {
    name: "Player", language: "en", colorIndex: 0, level: 1, xp: 0, highscores,
    theme: "dark", sound: true, music: false, showFps: false,
    keymap: Object.assign({}, DEFAULT_KEYMAP), leaderboards, replays: [],
  };
}

export function loadProfile() {
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
    p.theme = THEMES[data.theme] ? data.theme : "dark";
    p.sound = data.sound !== false;
    p.music = data.music === true;
    p.showFps = data.showFps === true;
    const km = data.keymap || {};
    for (const d of MOVE_DIRS) p.keymap[d] = km[d] || DEFAULT_KEYMAP[d];
    const boards = data.leaderboards || {};
    for (const k of MODE_KEYS) {
      const entries = Array.isArray(boards[k]) ? boards[k] : [];
      p.leaderboards[k] = entries.slice(0, LEADERBOARD_SIZE).map((e) => ({
        name: String(e.name || "?").slice(0, 14), score: e.score | 0,
      }));
    }
    p.replays = Array.isArray(data.replays) ? data.replays.slice(0, REPLAY_LIMIT) : [];
    return p;
  } catch (e) {
    return defaultProfile();
  }
}

export function saveProfile(p) {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(p)); } catch (e) { /* ignore */ }
}

export function addScore(p, modeKey, score) {
  if (score > (p.highscores[modeKey] || 0)) p.highscores[modeKey] = score;
  const board = p.leaderboards[modeKey] || (p.leaderboards[modeKey] = []);
  board.push({ name: p.name, score: score | 0 });
  board.sort((a, b) => b.score - a.score);
  board.length = Math.min(board.length, LEADERBOARD_SIZE);
  p.xp += score;
  let levelled = false;
  while (p.xp >= xpForLevel(p.level)) {
    p.xp -= xpForLevel(p.level);
    p.level += 1;
    levelled = true;
  }
  return levelled;
}
