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
 *   config · theme · i18n · version · profile · ai · audio · entities ·
 *   crazygames · render · game (controller) · main (this file).
 */
import { Game } from "./game.js";
import { CG } from "./crazygames.js";

// Give the font stack a chance to load so the first painted frame isn't a
// fallback-face flash. Everything else (canvas, audio, AI) is code, not assets,
// so once fonts are ready the game is ready.
function preloadFonts() {
  if (!document.fonts || !document.fonts.ready) return Promise.resolve();
  // Nudge the browser to actually fetch the faces we draw with.
  try {
    document.fonts.load('700 60px "Segoe UI"');
    document.fonts.load('400 22px "Microsoft YaHei"');
  } catch (e) { /* non-fatal */ }
  // Don't let a slow/unavailable font subsystem stall the boot forever.
  return Promise.race([
    document.fonts.ready,
    new Promise((r) => setTimeout(r, 2500)),
  ]);
}

function hideLoader() {
  const el = document.getElementById("loader");
  if (!el) return;
  el.classList.add("hidden");
  setTimeout(() => el.remove(), 600);
}

async function boot() {
  // Tell the portal we're loading (no-op off CrazyGames).
  await CG.init();
  CG.loadingStart();

  await preloadFonts();

  const canvas = document.getElementById("game");
  window.snakeGame = new Game(canvas);

  CG.loadingStop();
  hideLoader();
}

if (document.readyState === "loading") {
  window.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
