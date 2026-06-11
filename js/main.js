/* Snake_Game_Python — browser edition entry point.
 *
 * A faithful HTML5 Canvas port of the Python/Pygame game: sixteen modes across
 * two menus (ten of them AI-algorithm showcases), a clickable GUI with an
 * on-screen D-pad, three languages, a toolbox of snake AIs (BFS, A*, greedy,
 * simulated annealing, drift, minimax, Hamiltonian fill), deterministic
 * replays, an update check against GitHub Releases, and localStorage saves.
 *
 * Credits — Creators: SpaceSquare, Claude Code · Owner: SpaceSquare
 * Released under a custom license (see the repository LICENSE). Any derivative
 * work, modification, or re-upload must clearly credit the creators and owner.
 *
 * The code is split into ES modules under js/ that mirror the Python package:
 *   config · theme · i18n · version · profile · ai · entities · audio ·
 *   render · game (controller) · main (this file).
 */
import { Game } from "./game.js";

window.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("game");
  window.snakeGame = new Game(canvas);
});
