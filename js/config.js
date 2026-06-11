/* Geometry, directions, mode/state enums, and input constants.
 *
 * The browser-edition counterpart of the Python package's config.py. Pure data
 * and tiny helpers — no DOM, no game state.
 */

// Geometry -----------------------------------------------------------------
export const CELL = 28;
export const COLS = 24;
export const ROWS = 22; // even -> a grid Hamiltonian cycle always exists
export const HUD_HEIGHT = CELL * 2;
export const CONTROL_HEIGHT = 112;
export const PLAY_WIDTH = COLS * CELL;
export const PLAY_HEIGHT = ROWS * CELL;
export const PLAY_TOP = HUD_HEIGHT;
export const CONTROL_TOP = HUD_HEIGHT + PLAY_HEIGHT;
export const WIDTH = PLAY_WIDTH;
export const HEIGHT = PLAY_HEIGHT + HUD_HEIGHT + CONTROL_HEIGHT;

// Directions ---------------------------------------------------------------
export const UP = [0, -1], DOWN = [0, 1], LEFT = [-1, 0], RIGHT = [1, 0];

// Game modes ---------------------------------------------------------------
// The first eight are the original modes; the rest are the v1.5.0 algorithm
// showcases that live in the All-AI menu.
export const CLASSIC = 0, SURVIVAL = 1, BATTLE = 2, LEVEL = 3,
  AI_HUMAN = 4, PLAYER_FILL = 5, AI_AI = 6, AI_FILL = 7,
  AI_ASTAR = 8, AI_ANNEAL = 9, AI_GREEDY = 10, AI_DRIFT = 11,
  AI_MINIMAX = 12, AI_MINIMAX_DUEL = 13, AI_COOP_FILL = 14, AI_FOOD_RUSH = 15;
export const MODE_KEYS = [
  "classic", "survival", "battle", "level",
  "ai_human", "player_fill", "ai_ai", "ai_fill",
  "ai_astar", "ai_anneal", "ai_greedy", "ai_drift",
  "ai_minimax", "ai_minimax_duel", "ai_coop_fill", "ai_food_rush",
];
export const MAIN_MENU_MODES = [CLASSIC, SURVIVAL, BATTLE, LEVEL, AI_HUMAN, PLAYER_FILL];
export const AI_MENU_MODES = [
  AI_AI, AI_FILL, AI_ASTAR, AI_ANNEAL, AI_GREEDY, AI_DRIFT,
  AI_MINIMAX, AI_MINIMAX_DUEL, AI_COOP_FILL, AI_FOOD_RUSH,
];
// A single AI snake playing an otherwise-classic round (watch-only showcases).
export const SOLO_AI_MODES = new Set([AI_ASTAR, AI_ANNEAL, AI_GREEDY, AI_DRIFT]);
// Two snakes share the board. AI_MINIMAX has a human on the left.
export const TWO_SNAKE_MODES = new Set([
  BATTLE, AI_AI, AI_HUMAN, AI_MINIMAX, AI_MINIMAX_DUEL, AI_FOOD_RUSH]);
// Snakes grow every tick to paint the board; win when it is full.
export const FILL_MODES = new Set([PLAYER_FILL, AI_FILL, AI_COOP_FILL]);
// Food Rush: the first AI to eat this many apples wins.
export const RUSH_TARGET = 12;

// Lightweight state machine.
export const STATE_MENU = 0, STATE_READY = 1, STATE_PLAY = 2, STATE_OVER = 3,
  STATE_COLOR = 4, STATE_LANG = 5, STATE_NAME = 6, STATE_SETTINGS = 7,
  STATE_AI_MENU = 8, STATE_THEME = 9, STATE_CONTROLS = 10, STATE_REBIND = 11,
  STATE_LEADERBOARD = 12, STATE_AUDIO = 13, STATE_REPLAYS = 14,
  STATE_TUTORIAL = 15;

// Leaderboard size + replay cap + tutorial goal + remappable movement keys.
export const LEADERBOARD_SIZE = 5;
export const REPLAY_LIMIT = 8;
export const TUT_GOAL = 3; // apples to eat in the tutorial's "eat" step
export const MOVE_DIRS = ["up", "down", "left", "right"];
export const DIR_VECTORS = { up: UP, down: DOWN, left: LEFT, right: RIGHT };
export const DEFAULT_KEYMAP = { up: "w", down: "s", left: "a", right: "d" };

// Seedable PRNG so runs are deterministic (and therefore replayable).
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
