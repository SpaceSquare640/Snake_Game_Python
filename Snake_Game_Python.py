#!/usr/bin/env python3
"""Snake — a multi-mode, multi-language Snake game built with Pygame.

Features
--------
* Self-contained auto-setup bootstrap (checks Python, installs/updates Pygame).
* Eight game modes across two menus:
  - Main: Classic, Survival, Battle, Level, AI vs Human, Player Fill.
  - All-AI menu: AI vs AI, AI Fill.
* On-launch update check against the project's GitHub Releases.
* Full on-screen GUI: clickable menus with shortcut badges, a Settings menu, an
  All-AI menu, a Leaderboard, and a four-button D-pad for up/down/left/right.
* Four visual themes (Dark, Neon, Retro CRT, Minimal).
* Procedural sound effects and a background-music toggle (no audio files).
* Per-mode leaderboard (top 5) and remappable movement keys.
* Deterministic replay system (seeded RNG + input log) with a Replays page.
* Interactive step-by-step tutorial for new players.
* Three languages: English (default), Traditional Chinese, Simplified Chinese.
* Player profiles with a persistent, XP-based level.
* Nine selectable snake colors.
* Persistent save data (``snake_save.json``).
* A Breadth-First-Search (BFS) AI with a survival fallback, plus a perfect
  Hamiltonian-cycle "fill the board" AI.

Run with::

    python Snake_Game_Python.py

The bootstrap installs Pygame automatically on first run.

Credits
-------
Creators: SpaceSquare, Claude Code
Owner:    SpaceSquare

Released under a custom license (see LICENSE). Any derivative work,
modification, or re-upload must clearly credit the creators and owner above.
"""

from __future__ import annotations

# The bootstrap must run before any part of the game package is imported,
# because those modules import pygame at module load time.
from snake_game.bootstrap import bootstrap

bootstrap()

from snake_game.app import main  # noqa: E402  (intentionally after bootstrap)

if __name__ == "__main__":
    main()
