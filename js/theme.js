/* Visual themes + the live palette object.
 *
 * applyTheme() copies one theme into C *in place*, so every module that imported
 * C sees the new colors immediately and all drawing recolors at once.
 */

export const THEMES = {
  dark: {
    black: "#0f0f14", dark: "#181820", panel: "#1e1f28", panelHover: "#2c2e3a",
    grid: "#22222c", border: "#3a3c4a", white: "#ececf1", grey: "#8c8c96",
    dim: "#4e505c", divider: "#363846", red: "#dc4646", gold: "#f0c85a",
    food: "#eb505a", accent: "#76c4a2", accentDeep: "#469678", obstacle: "#464656",
  },
  neon: {
    black: "#080810", dark: "#10101e", panel: "#18162c", panelHover: "#2c284e",
    grid: "#1e1e36", border: "#4e4284", white: "#ebf0ff", grey: "#9696b9",
    dim: "#5c5a86", divider: "#3c3768", red: "#ff5078", gold: "#ffdc78",
    food: "#ff5a96", accent: "#5ae6eb", accentDeep: "#3caab4", obstacle: "#544894",
  },
  retro: {
    black: "#060e08", dark: "#09160c", panel: "#0d1e11", panelHover: "#16301c",
    grid: "#102615", border: "#2c6036", white: "#b4ffbe", grey: "#6eaf7a",
    dim: "#4a7c54", divider: "#20482a", red: "#ff785a", gold: "#d2ff78",
    food: "#a0ff8c", accent: "#78ff96", accentDeep: "#46b964", obstacle: "#2c6036",
  },
  minimal: {
    black: "#121214", dark: "#1a1a1c", panel: "#222226", panelHover: "#323238",
    grid: "#28282c", border: "#484850", white: "#e6e6ea", grey: "#96969e",
    dim: "#686870", divider: "#383840", red: "#c86060", gold: "#d2be78",
    food: "#d27878", accent: "#b0b6c0", accentDeep: "#787e8a", obstacle: "#464650",
  },
};
export const THEME_ORDER = ["dark", "neon", "retro", "minimal"];

// The live palette: one shared object, mutated in place by applyTheme().
export const C = Object.assign({}, THEMES.dark);
export function applyTheme(name) { Object.assign(C, THEMES[name] || THEMES.dark); }

export const SNAKE_COLORS = [
  "#5ac878", "#5aaaeb", "#ebb450", "#c86eeb", "#eb6e96",
  "#6edcdc", "#eb825a", "#b4dc5a", "#e6e6eb",
];
export const OPPONENT_COLOR = "#eb5a5a";
export const BTN_RADIUS = 12;
