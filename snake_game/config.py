"""Geometry, paths, directions, mode/state enums, and input constants."""
import sys
from pathlib import Path

import pygame

# Geometry -----------------------------------------------------------------
CELL = 28
COLS = 24
ROWS = 22  # even -> a grid Hamiltonian cycle always exists
HUD_HEIGHT = CELL * 2
CONTROL_HEIGHT = 112
PLAY_WIDTH = COLS * CELL
PLAY_HEIGHT = ROWS * CELL
PLAY_TOP = HUD_HEIGHT
CONTROL_TOP = HUD_HEIGHT + PLAY_HEIGHT
WIDTH = PLAY_WIDTH
HEIGHT = PLAY_HEIGHT + HUD_HEIGHT + CONTROL_HEIGHT
FPS = 60


def _app_dir() -> Path:
    """Writable directory for save data (handles the frozen exe case)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # Dev: the package lives in <repo>/snake_game, so the repo root is parent.parent.
    return Path(__file__).resolve().parent.parent


def resource_path(rel: str) -> Path:
    """Resolve a bundled read-only asset in both dev and PyInstaller builds."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).resolve().parent.parent / rel


SAVE_PATH = _app_dir() / "snake_save.json"
ICON_PATH = resource_path("assets/icon.png")

# Directions ---------------------------------------------------------------
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Game modes ---------------------------------------------------------------
(CLASSIC, SURVIVAL, BATTLE, LEVEL, AI_HUMAN, PLAYER_FILL, AI_AI, AI_FILL) = range(8)
MODE_KEYS = [
    "classic", "survival", "battle", "level",
    "ai_human", "player_fill", "ai_ai", "ai_fill",
]
MAIN_MENU_MODES = [CLASSIC, SURVIVAL, BATTLE, LEVEL, AI_HUMAN, PLAYER_FILL]
AI_MENU_MODES = [AI_AI, AI_FILL]
TWO_SNAKE_MODES = {BATTLE, AI_AI, AI_HUMAN}
FILL_MODES = {PLAYER_FILL, AI_FILL}

# Lightweight state machine.
STATE_MENU, STATE_READY, STATE_PLAY, STATE_OVER = range(4)
STATE_COLOR, STATE_LANG, STATE_NAME, STATE_SETTINGS, STATE_AI_MENU = range(4, 9)
(STATE_THEME, STATE_CONTROLS, STATE_REBIND, STATE_LEADERBOARD, STATE_AUDIO) = range(9, 14)
STATE_REPLAYS, STATE_TUTORIAL = range(14, 16)

# Leaderboard: how many top scores to keep per mode.
LEADERBOARD_SIZE = 5
# Replays: how many recorded runs to keep.
REPLAY_LIMIT = 8

# Remappable movement keys (Player 1 / single player). Stored in the profile
# as integer keycodes so they survive JSON round-trips.
MOVE_DIRS = ["up", "down", "left", "right"]
DIR_VECTORS = {"up": UP, "down": DOWN, "left": LEFT, "right": RIGHT}
DEFAULT_KEYMAP = {
    "up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d,
}
