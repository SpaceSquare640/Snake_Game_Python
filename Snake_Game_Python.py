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

# ---------------------------------------------------------------------------
# Auto-setup bootstrap
# ---------------------------------------------------------------------------
# This block runs *before* Pygame is imported so the game can install its own
# dependencies on first launch. It is intentionally dependency-free.

import importlib.util
import subprocess
import sys


def _run(cmd: list[str]) -> bool:
    """Run a subprocess command, returning ``True`` on success."""
    try:
        subprocess.check_call(cmd)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        print(f"  ! command failed: {' '.join(cmd)}\n    {exc}")
        return False


def _pip(*args: str) -> bool:
    return _run([sys.executable, "-m", "pip", *args])


def _pygame_package_name() -> str:
    """Pick the right Pygame distribution for the running interpreter.

    Mainline ``pygame`` can lag behind brand-new Python releases (it may not
    publish wheels yet). ``pygame-ce`` is a drop-in replacement that imports as
    ``pygame`` and ships wheels faster, so prefer it on very new interpreters.
    """
    if sys.version_info >= (3, 13):
        return "pygame-ce"
    return "pygame>=2.1"


def bootstrap() -> None:
    """Ensure a supported Python and an importable, up-to-date Pygame."""
    # A frozen (PyInstaller) build already bundles Pygame; never run pip there.
    if getattr(sys, "frozen", False):
        return
    print("Snake bootstrap: checking environment ...")

    # 1) Python version check (and a best-effort winget update on Windows).
    if sys.version_info < (3, 8):
        print(f"  Python {sys.version.split()[0]} is too old; 3.8+ is required.")
        if sys.platform.startswith("win"):
            print("  Attempting to update Python via winget ...")
            _run(["winget", "install", "-e", "--id", "Python.Python.3.12"])
        print("  Please re-run the game with Python 3.8 or newer.")
        sys.exit(1)

    # 2) Is Pygame importable? If not, install it.
    pkg = _pygame_package_name()
    if importlib.util.find_spec("pygame") is None:
        print(f"  Pygame not found; installing '{pkg}' ...")
        if not _pip("install", pkg):
            print("  Could not install Pygame automatically. Install it with:")
            print(f"    {sys.executable} -m pip install {pkg}")
            sys.exit(1)

    # 3) Version check / auto-update of an already-installed Pygame.
    try:
        import pygame  # noqa: F401  (import to read the version)

        version = tuple(int(p) for p in pygame.ver.split(".")[:2])
        if version < (2, 1):
            print(f"  Pygame {pygame.ver} is outdated; updating ...")
            _pip("install", "--upgrade", pkg)
    except Exception:  # pragma: no cover - defensive
        # If anything about the version probe fails, a fresh install is safest.
        _pip("install", "--upgrade", pkg)

    print("Snake bootstrap: environment ready.\n")


bootstrap()

# ---------------------------------------------------------------------------
# Imports (safe now that the bootstrap has guaranteed Pygame)
# ---------------------------------------------------------------------------
import json
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import pygame

# ---------------------------------------------------------------------------
# Version / update check
# ---------------------------------------------------------------------------
APP_VERSION = "1.3.0"
GITHUB_REPO = "SpaceSquare640/Snake_Game_Python"


def parse_version(text: str) -> tuple:
    """Parse a version/tag string like 'v1.2.0' into a comparable tuple."""
    parts = []
    for chunk in text.strip().lstrip("vV").split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def fetch_latest_version() -> str:
    """Return the latest release tag from GitHub (raises on failure)."""
    import urllib.request

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Snake_Game_Python",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=6) as resp:
        data = json.load(resp)
    return data.get("tag_name", "")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
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
    """Writable directory next to the app (handles the frozen exe case)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def resource_path(rel: str) -> Path:
    """Resolve a bundled read-only asset in both dev and PyInstaller builds."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).resolve().parent / rel


SAVE_PATH = _app_dir() / "snake_save.json"
ICON_PATH = resource_path("assets/icon.png")

# Themes -------------------------------------------------------------------
# Each theme is a full color set. The named module globals below (BLACK,
# PANEL, ACCENT, ...) are the *current* theme and are reassigned by
# apply_theme(); all drawing code reads those names, so a theme switch
# recolors the whole UI with no other changes. Palette follows a 60-30-10
# split: base background (~60%), panel fills (~30%), accent (~10%).
THEMES = {
    "dark": {
        "black": (15, 15, 20), "dark": (24, 24, 32), "panel": (30, 31, 40),
        "panel_hover": (44, 46, 58), "grid": (34, 34, 44), "border": (58, 60, 74),
        "white": (236, 236, 241), "grey": (140, 140, 150), "dim": (78, 80, 92),
        "divider": (54, 56, 70), "red": (220, 70, 70), "gold": (240, 200, 90),
        "food": (235, 80, 90), "accent": (118, 196, 162),
        "accent_deep": (70, 150, 120), "obstacle": (70, 70, 86),
    },
    "neon": {
        "black": (8, 8, 16), "dark": (16, 16, 30), "panel": (24, 22, 44),
        "panel_hover": (44, 40, 78), "grid": (30, 30, 54), "border": (78, 66, 132),
        "white": (235, 240, 255), "grey": (150, 150, 185), "dim": (92, 90, 134),
        "divider": (60, 55, 104), "red": (255, 80, 120), "gold": (255, 220, 120),
        "food": (255, 90, 150), "accent": (90, 230, 235),
        "accent_deep": (60, 170, 180), "obstacle": (84, 72, 148),
    },
    "retro": {
        "black": (6, 14, 8), "dark": (9, 22, 12), "panel": (13, 30, 17),
        "panel_hover": (22, 48, 28), "grid": (16, 38, 21), "border": (44, 96, 54),
        "white": (180, 255, 190), "grey": (110, 175, 122), "dim": (74, 124, 84),
        "divider": (32, 72, 42), "red": (255, 120, 90), "gold": (210, 255, 120),
        "food": (160, 255, 140), "accent": (120, 255, 150),
        "accent_deep": (70, 185, 100), "obstacle": (44, 96, 54),
    },
    "minimal": {
        "black": (18, 18, 20), "dark": (26, 26, 28), "panel": (34, 34, 38),
        "panel_hover": (50, 50, 56), "grid": (40, 40, 44), "border": (72, 72, 80),
        "white": (230, 230, 234), "grey": (150, 150, 158), "dim": (104, 104, 112),
        "divider": (56, 56, 64), "red": (200, 96, 96), "gold": (210, 190, 120),
        "food": (210, 120, 120), "accent": (176, 182, 192),
        "accent_deep": (120, 126, 138), "obstacle": (70, 70, 80),
    },
}
THEME_ORDER = ["dark", "neon", "retro", "minimal"]

# Current-theme globals (initialised to "dark"; apply_theme() reassigns them).
BLACK = DARK = PANEL = PANEL_HOVER = GRID_LINE = BORDER = WHITE = GREY = DIM = (0, 0, 0)
DIVIDER = RED = GOLD = FOOD_COLOR = ACCENT = ACCENT_DEEP = OBSTACLE = (0, 0, 0)


def apply_theme(name):
    """Reassign the color globals from THEMES[name] (defaults to 'dark')."""
    global BLACK, DARK, PANEL, PANEL_HOVER, GRID_LINE, BORDER, WHITE, GREY, DIM
    global DIVIDER, RED, GOLD, FOOD_COLOR, ACCENT, ACCENT_DEEP, OBSTACLE
    t = THEMES.get(name, THEMES["dark"])
    BLACK, DARK, PANEL, PANEL_HOVER = t["black"], t["dark"], t["panel"], t["panel_hover"]
    GRID_LINE, BORDER, WHITE, GREY, DIM = t["grid"], t["border"], t["white"], t["grey"], t["dim"]
    DIVIDER, RED, GOLD, FOOD_COLOR = t["divider"], t["red"], t["gold"], t["food"]
    ACCENT, ACCENT_DEEP, OBSTACLE = t["accent"], t["accent_deep"], t["obstacle"]


apply_theme("dark")

# Default corner radius for GUI buttons (rounder = more modern).
BTN_RADIUS = 12

# Nine selectable snake colors.
SNAKE_COLORS = [
    (90, 200, 120),   # green
    (90, 170, 235),   # blue
    (235, 180, 80),   # amber
    (200, 110, 235),  # purple
    (235, 110, 150),  # pink
    (110, 220, 220),  # cyan
    (235, 130, 90),   # orange
    (180, 220, 90),   # lime
    (230, 230, 235),  # white
]

# Opponent color for two-snake modes (distinct from player choices visually).
OPPONENT_COLOR = (235, 90, 90)

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


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    "en": {
        "title": "SNAKE",
        "subtitle": "Choose a mode",
        "classic": "Classic",
        "survival": "Survival",
        "battle": "Battle",
        "level": "Level",
        "ai_ai": "AI vs AI",
        "ai_human": "AI vs Human",
        "player_fill": "Player Fill",
        "ai_fill": "AI Fill",
        "press_space": "Press SPACE / a button to start",
        "game_over": "GAME OVER",
        "you_win": "YOU WIN!",
        "board_filled": "Board filled — {n} cells!",
        "press_space_restart": "Press SPACE to play again",
        "score": "Score",
        "filled": "Filled",
        "high": "Best",
        "level_label": "Lv",
        "stage": "Stage",
        "player": "Player",
        "p1": "P1",
        "p2": "P2",
        "ai": "AI",
        "you": "You",
        "winner": "{name} wins!",
        "draw": "Draw!",
        "watching": "Watching AI…",
        "menu_hint": "Click a mode or press 1-6  ·  ESC quit",
        "ai_modes": "All-AI Modes",
        "settings": "Settings",
        "settings_title": "Settings",
        "ai_menu_title": "All-AI Modes",
        "color_btn": "Snake Color",
        "lang_btn": "Language",
        "name_btn": "Player Name",
        "menu_btn": "Menu",
        "back": "Back",
        "color_menu": "Choose snake color",
        "lang_menu": "Choose language",
        "name_menu": "Enter your name",
        "name_hint": "Type a name, ENTER to confirm",
        "back_hint": "ESC / Back",
        "level_up": "Level up!  Lv {lvl}",
        "xp": "XP",
        "english": "English",
        "tchinese": "Traditional Chinese",
        "schinese": "Simplified Chinese",
        "credits": "Creators: SpaceSquare, Claude Code   ·   Owner: SpaceSquare",
        "theme_btn": "Theme", "theme_menu": "Choose a theme",
        "theme_dark": "Dark", "theme_neon": "Neon", "theme_retro": "Retro CRT",
        "theme_minimal": "Minimal",
        "audio_btn": "Audio", "audio_menu": "Audio", "sound_label": "Sound effects",
        "music_label": "Music", "on": "On", "off": "Off",
        "controls_btn": "Controls", "controls_menu": "Controls",
        "rebind_hint": "Click a key to rebind  ·  R reset",
        "press_key": "Press any key…", "reset_default": "Reset to default",
        "dir_up": "Up", "dir_down": "Down", "dir_left": "Left", "dir_right": "Right",
        "leaderboard_btn": "Leaderboard", "leaderboard_title": "Leaderboard",
        "empty_board": "No scores yet", "fps_label": "FPS counter",
        "replays_btn": "Replays", "replays_title": "Replays",
        "watch_replay": "Watch replay", "replay_again": "Replay again",
        "replay_label": "REPLAY", "no_replays": "No replays yet",
        "tutorial_btn": "▶  How to play (Tutorial)", "tut_title": "Tutorial",
        "tut_move": "Use WASD / Arrows / the D-pad to move",
        "tut_eat": "Now eat the apples —  {n}  to go",
        "tut_avoid": "Avoid walls, obstacles, and yourself!",
        "tut_done": "You're ready!  Pick a mode from the menu.",
        "tut_continue": "Press SPACE to continue", "tut_skip": "ESC / M to skip",
        "ver_checking": "v{ver} · checking for updates…",
        "ver_latest": "v{ver} · up to date",
        "ver_outdated": "v{ver} · update available: {latest}",
        "ver_unknown": "v{ver}",
    },
    "zh_tw": {
        "title": "貪食蛇",
        "subtitle": "選擇模式",
        "classic": "經典模式",
        "survival": "生存模式",
        "battle": "對戰模式",
        "level": "關卡模式",
        "ai_ai": "AI 對 AI",
        "ai_human": "AI 對 玩家",
        "player_fill": "玩家填滿",
        "ai_fill": "AI 填滿",
        "press_space": "按空白鍵／按鈕開始",
        "game_over": "遊戲結束",
        "you_win": "你贏了！",
        "board_filled": "場地已填滿 — {n} 格！",
        "press_space_restart": "按空白鍵再玩一次",
        "score": "分數",
        "filled": "已填滿",
        "high": "最高",
        "level_label": "等級",
        "stage": "關卡",
        "player": "玩家",
        "p1": "玩家1",
        "p2": "玩家2",
        "ai": "AI",
        "you": "你",
        "winner": "{name} 獲勝！",
        "draw": "平手！",
        "watching": "觀看 AI…",
        "menu_hint": "點選模式或按 1-6  ·  ESC 離開",
        "ai_modes": "全 AI 模式",
        "settings": "設定",
        "settings_title": "設定",
        "ai_menu_title": "全 AI 模式",
        "color_btn": "蛇身顏色",
        "lang_btn": "語言",
        "name_btn": "玩家名稱",
        "menu_btn": "選單",
        "back": "返回",
        "color_menu": "選擇蛇身顏色",
        "lang_menu": "選擇語言",
        "name_menu": "輸入你的名稱",
        "name_hint": "輸入名稱，按 ENTER 確認",
        "back_hint": "ESC／返回",
        "level_up": "升級！等級 {lvl}",
        "xp": "經驗",
        "english": "英文 English",
        "tchinese": "繁體中文",
        "schinese": "簡體中文",
        "credits": "創作者：SpaceSquare、Claude Code   ·   擁有者：SpaceSquare",
        "theme_btn": "佈景主題", "theme_menu": "選擇佈景主題",
        "theme_dark": "深色", "theme_neon": "霓虹", "theme_retro": "復古 CRT",
        "theme_minimal": "極簡",
        "audio_btn": "音效", "audio_menu": "音效設定", "sound_label": "音效",
        "music_label": "背景音樂", "on": "開", "off": "關",
        "controls_btn": "按鍵設定", "controls_menu": "按鍵設定",
        "rebind_hint": "點選按鍵以重新設定  ·  R 還原",
        "press_key": "請按任意鍵…", "reset_default": "還原預設",
        "dir_up": "上", "dir_down": "下", "dir_left": "左", "dir_right": "右",
        "leaderboard_btn": "排行榜", "leaderboard_title": "排行榜",
        "empty_board": "尚無紀錄", "fps_label": "FPS 顯示",
        "replays_btn": "重播", "replays_title": "重播紀錄",
        "watch_replay": "觀看重播", "replay_again": "再看一次",
        "replay_label": "重播中", "no_replays": "尚無重播",
        "tutorial_btn": "▶  新手教學", "tut_title": "新手教學",
        "tut_move": "用 WASD／方向鍵／畫面方向鍵移動",
        "tut_eat": "現在吃掉蘋果 —  還剩 {n}  顆",
        "tut_avoid": "避開牆壁、障礙物與自己！",
        "tut_done": "你準備好了！從選單選擇一個模式吧。",
        "tut_continue": "按空白鍵繼續", "tut_skip": "ESC／M 跳過",
        "ver_checking": "v{ver} · 檢查更新中…",
        "ver_latest": "v{ver} · 已是最新版",
        "ver_outdated": "v{ver} · 有可用更新：{latest}",
        "ver_unknown": "v{ver}",
    },
    "zh_cn": {
        "title": "贪食蛇",
        "subtitle": "选择模式",
        "classic": "经典模式",
        "survival": "生存模式",
        "battle": "对战模式",
        "level": "关卡模式",
        "ai_ai": "AI 对 AI",
        "ai_human": "AI 对 玩家",
        "player_fill": "玩家填满",
        "ai_fill": "AI 填满",
        "press_space": "按空格键／按钮开始",
        "game_over": "游戏结束",
        "you_win": "你赢了！",
        "board_filled": "场地已填满 — {n} 格！",
        "press_space_restart": "按空格键再玩一次",
        "score": "分数",
        "filled": "已填满",
        "high": "最高",
        "level_label": "等级",
        "stage": "关卡",
        "player": "玩家",
        "p1": "玩家1",
        "p2": "玩家2",
        "ai": "AI",
        "you": "你",
        "winner": "{name} 获胜！",
        "draw": "平局！",
        "watching": "观看 AI…",
        "menu_hint": "点选模式或按 1-6  ·  ESC 退出",
        "ai_modes": "全 AI 模式",
        "settings": "设置",
        "settings_title": "设置",
        "ai_menu_title": "全 AI 模式",
        "color_btn": "蛇身颜色",
        "lang_btn": "语言",
        "name_btn": "玩家名称",
        "menu_btn": "菜单",
        "back": "返回",
        "color_menu": "选择蛇身颜色",
        "lang_menu": "选择语言",
        "name_menu": "输入你的名称",
        "name_hint": "输入名称，按 ENTER 确认",
        "back_hint": "ESC／返回",
        "level_up": "升级！等级 {lvl}",
        "xp": "经验",
        "english": "英文 English",
        "tchinese": "繁体中文",
        "schinese": "简体中文",
        "credits": "创作者：SpaceSquare、Claude Code   ·   拥有者：SpaceSquare",
        "theme_btn": "界面主题", "theme_menu": "选择界面主题",
        "theme_dark": "深色", "theme_neon": "霓虹", "theme_retro": "复古 CRT",
        "theme_minimal": "极简",
        "audio_btn": "音效", "audio_menu": "音效设置", "sound_label": "音效",
        "music_label": "背景音乐", "on": "开", "off": "关",
        "controls_btn": "按键设置", "controls_menu": "按键设置",
        "rebind_hint": "点选按键以重新设置  ·  R 还原",
        "press_key": "请按任意键…", "reset_default": "还原默认",
        "dir_up": "上", "dir_down": "下", "dir_left": "左", "dir_right": "右",
        "leaderboard_btn": "排行榜", "leaderboard_title": "排行榜",
        "empty_board": "暂无记录", "fps_label": "FPS 显示",
        "replays_btn": "重播", "replays_title": "重播记录",
        "watch_replay": "观看重播", "replay_again": "再看一次",
        "replay_label": "重播中", "no_replays": "暂无重播",
        "tutorial_btn": "▶  新手教学", "tut_title": "新手教学",
        "tut_move": "用 WASD／方向键／画面方向键移动",
        "tut_eat": "现在吃掉苹果 —  还剩 {n}  颗",
        "tut_avoid": "避开墙壁、障碍物与自己！",
        "tut_done": "你准备好了！从菜单选择一个模式吧。",
        "tut_continue": "按空格键继续", "tut_skip": "ESC／M 跳过",
        "ver_checking": "v{ver} · 检查更新中…",
        "ver_latest": "v{ver} · 已是最新版",
        "ver_outdated": "v{ver} · 有可用更新：{latest}",
        "ver_unknown": "v{ver}",
    },
}

LANG_ORDER = ["en", "zh_tw", "zh_cn"]

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


def key_label(code):
    """Human-readable name for a pygame keycode (e.g. 'W', 'Up')."""
    try:
        name = pygame.key.name(int(code))
    except Exception:
        name = "?"
    return name.upper() if len(name) == 1 else name.title()


# ---------------------------------------------------------------------------
# Save data
# ---------------------------------------------------------------------------
@dataclass
class Profile:
    """Persistent player profile and settings."""

    name: str = "Player"
    language: str = "en"
    color_index: int = 0
    level: int = 1
    xp: int = 0
    highscores: dict = field(default_factory=lambda: {k: 0 for k in MODE_KEYS})
    # v1.2.0 additions
    theme: str = "dark"
    sound: bool = True
    music: bool = False
    show_fps: bool = False
    keymap: dict = field(default_factory=lambda: dict(DEFAULT_KEYMAP))
    # leaderboards[mode] = list of {"name", "score"} sorted high -> low
    leaderboards: dict = field(default_factory=lambda: {k: [] for k in MODE_KEYS})
    # replays = list of recorded runs (newest first), each a dict (see Game)
    replays: list = field(default_factory=list)

    # XP required to reach the *next* level grows linearly.
    @staticmethod
    def xp_for_level(level: int) -> int:
        return 50 * level

    def add_score(self, mode_key: str, score: int) -> bool:
        """Record a score; return ``True`` if the player levelled up."""
        if score > self.highscores.get(mode_key, 0):
            self.highscores[mode_key] = score
        self._record_leaderboard(mode_key, score)
        self.xp += score
        levelled = False
        while self.xp >= self.xp_for_level(self.level):
            self.xp -= self.xp_for_level(self.level)
            self.level += 1
            levelled = True
        return levelled

    def _record_leaderboard(self, mode_key: str, score: int) -> None:
        board = self.leaderboards.setdefault(mode_key, [])
        board.append({"name": self.name, "score": int(score)})
        board.sort(key=lambda e: e["score"], reverse=True)
        del board[LEADERBOARD_SIZE:]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "language": self.language,
            "color_index": self.color_index,
            "level": self.level,
            "xp": self.xp,
            "highscores": self.highscores,
            "theme": self.theme,
            "sound": self.sound,
            "music": self.music,
            "show_fps": self.show_fps,
            "keymap": self.keymap,
            "leaderboards": self.leaderboards,
            "replays": self.replays,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        prof = cls()
        prof.name = str(data.get("name", prof.name))[:14] or "Player"
        prof.language = data.get("language", "en")
        if prof.language not in TRANSLATIONS:
            prof.language = "en"
        prof.color_index = int(data.get("color_index", 0)) % len(SNAKE_COLORS)
        prof.level = max(1, int(data.get("level", 1)))
        prof.xp = max(0, int(data.get("xp", 0)))
        scores = data.get("highscores", {})
        # New modes default to 0 for older save files (backward compatible).
        prof.highscores = {k: int(scores.get(k, 0)) for k in MODE_KEYS}
        prof.theme = data.get("theme", "dark")
        if prof.theme not in THEMES:
            prof.theme = "dark"
        prof.sound = bool(data.get("sound", True))
        prof.music = bool(data.get("music", False))
        prof.show_fps = bool(data.get("show_fps", False))
        km = data.get("keymap", {})
        prof.keymap = {d: int(km.get(d, DEFAULT_KEYMAP[d])) for d in MOVE_DIRS}
        boards = data.get("leaderboards", {})
        prof.leaderboards = {}
        for k in MODE_KEYS:
            entries = boards.get(k, [])
            clean = []
            for e in entries[:LEADERBOARD_SIZE]:
                try:
                    clean.append({"name": str(e["name"])[:14], "score": int(e["score"])})
                except (KeyError, TypeError, ValueError):
                    continue
            prof.leaderboards[k] = clean
        replays = data.get("replays", [])
        prof.replays = replays[:REPLAY_LIMIT] if isinstance(replays, list) else []
        return prof


def load_profile() -> Profile:
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as fh:
            return Profile.from_dict(json.load(fh))
    except (OSError, ValueError):
        return Profile()


def save_profile(profile: Profile) -> None:
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as fh:
            json.dump(profile.to_dict(), fh, ensure_ascii=False, indent=2)
    except OSError as exc:  # pragma: no cover - defensive
        print(f"Could not save profile: {exc}")


# ---------------------------------------------------------------------------
# AI helpers: BFS, survival fallback, and a Hamiltonian cycle for filling
# ---------------------------------------------------------------------------
def _neighbors(cell):
    x, y = cell
    yield (x + 1, y), RIGHT
    yield (x - 1, y), LEFT
    yield (x, y + 1), DOWN
    yield (x, y - 1), UP


def _in_bounds(cell) -> bool:
    x, y = cell
    return 0 <= x < COLS and 0 <= y < ROWS


def bfs_direction(start, goal, blocked):
    """Return the first step direction of the shortest path start -> goal."""
    if start == goal:
        return None
    queue = deque([start])
    came_from = {start: (None, None)}
    while queue:
        current = queue.popleft()
        for nxt, direction in _neighbors(current):
            if nxt in came_from or not _in_bounds(nxt) or nxt in blocked:
                continue
            came_from[nxt] = (current, direction)
            if nxt == goal:
                node = nxt
                while came_from[node][0] != start:
                    node = came_from[node][0]
                return came_from[node][1]
            queue.append(nxt)
    return None


def _flood_free(start, blocked):
    """Count cells reachable from ``start`` (open space around a move)."""
    if not _in_bounds(start) or start in blocked:
        return 0
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt, _ in _neighbors(current):
            if nxt in seen or not _in_bounds(nxt) or nxt in blocked:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return len(seen)


def survival_direction(head, blocked, current_dir):
    """Pick the safe move that keeps the most open space (anti-trap)."""
    best_dir, best_score = None, -1
    for nxt, direction in _neighbors(head):
        if direction[0] == -current_dir[0] and direction[1] == -current_dir[1]:
            continue
        if not _in_bounds(nxt) or nxt in blocked:
            continue
        score = _flood_free(nxt, blocked)
        if score > best_score:
            best_dir, best_score = direction, score
    return best_dir


def build_hamiltonian_cycle(cols, rows):
    """Build a Hamiltonian cycle over every grid cell (requires even rows).

    Returns ``(sequence, next_map)`` where ``sequence`` is the cell visit order
    and ``next_map[cell]`` gives the following cell in the cycle. A snake that
    starts on the cycle and always follows ``next_map`` covers the entire board
    without ever colliding — the classic "perfect" fill.
    """
    seq = []
    # Top row, left to right.
    for x in range(cols):
        seq.append((x, 0))
    # Vertical serpentine through columns cols-1..1 for rows 1..rows-1,
    # leaving column 0 as the return spine.
    going_down = True
    for x in range(cols - 1, 0, -1):
        ys = range(1, rows) if going_down else range(rows - 1, 0, -1)
        for y in ys:
            seq.append((x, y))
        going_down = not going_down
    # Return spine: column 0 from the bottom back up to row 1.
    for y in range(rows - 1, 0, -1):
        seq.append((0, y))

    nxt = {}
    n = len(seq)
    for i in range(n):
        nxt[seq[i]] = seq[(i + 1) % n]
    return seq, nxt


# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------
class Snake:
    """A single snake body with movement and self/obstacle awareness."""

    def __init__(self, body, direction, color, is_ai=False):
        self.body = list(body)          # head is body[0]
        self.direction = direction
        self.pending = direction
        self.color = color
        self.is_ai = is_ai
        self.alive = True
        self.grow_pending = 0
        self.score = 0
        self.cycle = None               # set for Hamiltonian fill AI

    @property
    def head(self):
        return self.body[0]

    def set_direction(self, direction):
        # Disallow reversing directly onto the neck.
        if (direction[0] == -self.direction[0]
                and direction[1] == -self.direction[1]):
            return
        self.pending = direction

    def plan_ai(self, food, blocked):
        """Choose a direction using BFS, falling back to survival."""
        direction = bfs_direction(self.head, food, blocked)
        if direction is None:
            direction = survival_direction(self.head, blocked, self.direction)
        if direction is not None:
            self.set_direction(direction)

    def plan_cycle(self):
        """Follow the Hamiltonian cycle (authoritative; bypasses the guard)."""
        hx, hy = self.head
        nx, ny = self.cycle[self.head]
        self.pending = (nx - hx, ny - hy)

    def step(self):
        self.direction = self.pending
        x, y = self.head
        new_head = (x + self.direction[0], y + self.direction[1])
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self, amount=1):
        self.grow_pending += amount


# ---------------------------------------------------------------------------
# Sound — small procedural synth (no audio files, no numpy required)
# ---------------------------------------------------------------------------
import array
import math


def _tone(freq, ms, vol=0.35, sr=22050, shape="square"):
    """Build a 16-bit mono sample buffer for a single enveloped tone."""
    n = max(1, int(sr * ms / 1000))
    buf = array.array("h")
    attack = sr * 0.005
    release = sr * 0.03
    for i in range(n):
        t = i / sr
        if shape == "square":
            s = vol if math.sin(2 * math.pi * freq * t) >= 0 else -vol
        else:
            s = vol * math.sin(2 * math.pi * freq * t)
        env = min(1.0, i / attack) * min(1.0, (n - i) / release)
        buf.append(int(max(-1.0, min(1.0, s * env)) * 32767))
    return buf


def _sequence(notes, sr=22050, vol=0.22, shape="sine"):
    """Concatenate (freq, ms) notes into one buffer (freq 0 = rest)."""
    out = array.array("h")
    for freq, ms in notes:
        if freq <= 0:
            out.extend(array.array("h", [0]) * int(sr * ms / 1000))
        else:
            out.extend(_tone(freq, ms, vol=vol, sr=sr, shape=shape))
    return out


class SoundManager:
    """Synthesizes effect and music buffers at startup; respects settings."""

    SR = 22050

    def __init__(self, profile):
        self.profile = profile
        self.ok = False
        self.sounds = {}
        self.music = None
        self.music_channel = None
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=self.SR, size=-16, channels=1, buffer=512)
            self._build()
            self.ok = True
        except Exception:
            self.ok = False
        if self.ok and self.profile.music:
            self.start_music()

    def _snd(self, buf):
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build(self):
        self.sounds = {
            "eat": self._snd(_tone(880, 70, vol=0.4)),
            "select": self._snd(_tone(520, 45, vol=0.3)),
            "crash": self._snd(_tone(150, 240, vol=0.45, shape="square")),
            "win": self._snd(_sequence([(523, 90), (659, 90), (784, 90), (1046, 160)],
                                       vol=0.35, shape="square")),
        }
        # A gentle looping melody for background music.
        loop = [
            (392, 220), (523, 220), (659, 220), (523, 220),
            (440, 220), (587, 220), (440, 220), (0, 120),
            (349, 220), (523, 220), (659, 220), (784, 220),
            (659, 220), (523, 220), (440, 220), (0, 260),
        ]
        self.music = self._snd(_sequence(loop, vol=0.12, shape="sine"))

    def play(self, name):
        if self.ok and self.profile.sound and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

    def start_music(self):
        if not self.ok or not self.music:
            return
        try:
            self.music_channel = self.music.play(loops=-1)
        except Exception:
            self.music_channel = None

    def stop_music(self):
        if self.music_channel:
            try:
                self.music_channel.stop()
            except Exception:
                pass
            self.music_channel = None

    def set_music(self, on):
        if on:
            self.start_music()
        else:
            self.stop_music()


# ---------------------------------------------------------------------------
# The game
# ---------------------------------------------------------------------------
# Lightweight state machine.
STATE_MENU, STATE_READY, STATE_PLAY, STATE_OVER = range(4)
STATE_COLOR, STATE_LANG, STATE_NAME, STATE_SETTINGS, STATE_AI_MENU = range(4, 9)
(STATE_THEME, STATE_CONTROLS, STATE_REBIND, STATE_LEADERBOARD, STATE_AUDIO) = range(9, 14)
STATE_REPLAYS, STATE_TUTORIAL = range(14, 16)


class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake")
        self._set_window_icon()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.profile = load_profile()
        apply_theme(self.profile.theme)
        self.fonts = self._load_fonts()
        self.sound = SoundManager(self.profile)
        self.state = STATE_MENU
        self.mode = CLASSIC
        self.running = True

        # Clickable buttons rebuilt every frame: list of (rect, action, arg).
        self.buttons = []
        self.sub_return = STATE_MENU
        self.mouse_down = None       # (action, arg) armed on mouse-down for press feedback
        self.rebind_dir = None       # which movement key is being rebound

        # Per-round state (initialised in start_round).
        self.snakes = []
        self.food = None
        self.obstacles = set()
        self.stage = 1
        self.tick_ms = 120
        self.move_accum = 0.0
        self.result_text = ""
        self.win = False
        self.level_up_flash = 0
        self.name_buffer = ""

        # Replay state.
        self.rng = random.Random()       # per-round seeded RNG (deterministic)
        self.tick_count = 0
        self.recording = None            # inputs being recorded this round
        self.replaying = False
        self.replay_by_tick = {}         # tick -> [(snake_idx, dir), ...]
        self.last_replay = None          # the most recent finished recording
        self.current_replay = None       # the recording currently being watched

        # Background update check.
        self.update_state = "checking"   # checking | latest | outdated | unknown
        self.latest_version = ""
        threading.Thread(target=self._check_update, daemon=True).start()

    # -- Update check -------------------------------------------------------
    def _check_update(self):
        try:
            tag = fetch_latest_version()
            if not tag:
                self.update_state = "unknown"
                return
            self.latest_version = tag
            if parse_version(tag) > parse_version(APP_VERSION):
                self.update_state = "outdated"
            else:
                self.update_state = "latest"
        except Exception:
            self.update_state = "unknown"

    # -- Window icon --------------------------------------------------------
    def _set_window_icon(self):
        try:
            icon = pygame.image.load(str(ICON_PATH))
            pygame.display.set_icon(icon)
        except (pygame.error, FileNotFoundError):
            pass

    # -- Fonts --------------------------------------------------------------
    def _load_fonts(self):
        """Load CJK-capable fonts so all three languages render."""
        cjk = ("microsoftyaheui,microsoftyahei,microsoftjhenghei,simhei,"
               "simsun,notosanscjktc,notosanscjksc,arialunicodems")
        try:
            return {
                "title": pygame.font.SysFont(cjk, 66, bold=True),
                "big": pygame.font.SysFont(cjk, 60),
                "mid": pygame.font.SysFont(cjk, 32),
                "small": pygame.font.SysFont(cjk, 22),
                "tiny": pygame.font.SysFont(cjk, 17),
            }
        except Exception:  # pragma: no cover - defensive
            return {
                "title": pygame.font.Font(None, 66),
                "big": pygame.font.Font(None, 60),
                "mid": pygame.font.Font(None, 32),
                "small": pygame.font.Font(None, 22),
                "tiny": pygame.font.Font(None, 17),
            }

    # -- Translation helper -------------------------------------------------
    def t(self, key, **kwargs):
        text = TRANSLATIONS[self.profile.language].get(key, key)
        return text.format(**kwargs) if kwargs else text

    # -- Round setup --------------------------------------------------------
    def start_round(self, seed=None):
        """Begin a fresh, recorded round (deterministic from a random seed)."""
        seed = random.randrange(1 << 30) if seed is None else seed
        self.rng = random.Random(seed)
        self.replaying = False
        self.replay_by_tick = {}
        self.tick_count = 0
        self.recording = {
            "mode": self.mode, "seed": seed,
            "color_index": self.profile.color_index, "inputs": [],
        }
        self._setup_round(SNAKE_COLORS[self.profile.color_index])
        self.state = STATE_READY

    def start_replay(self, rec):
        """Replay a recorded run deterministically (no live input)."""
        self.mode = rec["mode"]
        self.current_replay = rec
        self.rng = random.Random(rec["seed"])
        self.replaying = True
        self.recording = None
        self.tick_count = 0
        self.replay_by_tick = {}
        for inp in rec.get("inputs", []):
            self.replay_by_tick.setdefault(inp["t"], []).append((inp["s"], tuple(inp["d"])))
        color = SNAKE_COLORS[rec.get("color_index", 0) % len(SNAKE_COLORS)]
        self._setup_round(color)
        self.state = STATE_PLAY  # replays auto-play

    def _setup_round(self, color):
        self.obstacles = set()
        self.stage = 1
        self.result_text = ""
        self.win = False
        self.food = None
        mid_y = ROWS // 2

        if self.mode in TWO_SNAKE_MODES:
            left = Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)
            right = Snake(
                [(COLS - 5, mid_y), (COLS - 4, mid_y), (COLS - 3, mid_y)],
                LEFT, OPPONENT_COLOR,
            )
            if self.mode == AI_AI:
                left.is_ai = right.is_ai = True
            elif self.mode == AI_HUMAN:
                right.is_ai = True  # right snake is the AI; left is the human
            self.snakes = [left, right]
        elif self.mode == AI_FILL:
            seq, nxt = build_hamiltonian_cycle(COLS, ROWS)
            snake = Snake([seq[0]], RIGHT, color, is_ai=True)
            snake.cycle = nxt
            self.snakes = [snake]
        elif self.mode == PLAYER_FILL:
            self.snakes = [Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)]
        else:  # CLASSIC, SURVIVAL, LEVEL
            self.snakes = [Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)]
            if self.mode == LEVEL:
                self._build_stage(self.stage)

        if self.mode not in FILL_MODES:
            self.food = self._spawn_food()
        self.tick_ms = self._base_tick()
        self.move_accum = 0.0

    def _base_tick(self):
        return {
            CLASSIC: 120,
            SURVIVAL: 140,
            BATTLE: 110,
            LEVEL: 120,
            AI_HUMAN: 90,
            PLAYER_FILL: 100,
            AI_AI: 70,
            AI_FILL: 26,
        }[self.mode]

    def _occupied(self, extra=()):
        cells = set(self.obstacles)
        for snake in self.snakes:
            cells.update(snake.body)
        cells.update(extra)
        return cells

    def _spawn_food(self):
        occupied = self._occupied()
        free = [
            (x, y)
            for x in range(COLS)
            for y in range(ROWS)
            if (x, y) not in occupied
        ]
        return self.rng.choice(free) if free else None

    def _build_stage(self, stage):
        """Place obstacle walls for Level mode (deterministic per stage)."""
        self.obstacles = set()
        rng = random.Random(stage * 7919)  # local: reproducible, no global state
        wall_count = min(3 + stage, 9)
        for _ in range(wall_count):
            horizontal = rng.random() < 0.5
            length = rng.randint(3, 6)
            x = rng.randint(2, COLS - 7)
            y = rng.randint(2, ROWS - 3)
            for i in range(length):
                cell = (x + i, y) if horizontal else (x, y + i)
                if _in_bounds(cell):
                    self.obstacles.add(cell)
        mid_y = ROWS // 2
        for x in range(0, 6):
            self.obstacles.discard((x, mid_y))

    # -- Update -------------------------------------------------------------
    def update(self, dt):
        if self.state != STATE_PLAY:
            return
        self.move_accum += dt
        if self.move_accum < self.tick_ms:
            return
        self.move_accum -= self.tick_ms
        self._advance()

    def _advance(self):
        # Replay: feed the inputs recorded for this tick before anything moves.
        if self.replaying:
            for snake_idx, direction in self.replay_by_tick.get(self.tick_count, ()):
                if snake_idx < len(self.snakes):
                    self.snakes[snake_idx].set_direction(direction)

        # AI planning.
        for snake in self.snakes:
            if snake.is_ai and snake.alive:
                if snake.cycle is not None:
                    snake.plan_cycle()
                else:
                    snake.plan_ai(self.food, self._blocked_for(snake))

        # Fill modes grow every tick — the snake keeps painting the board.
        if self.mode in FILL_MODES:
            for snake in self.snakes:
                if snake.alive:
                    snake.grow(1)

        for snake in self.snakes:
            if snake.alive:
                snake.step()

        alive_before = sum(1 for s in self.snakes if s.alive)
        self._resolve_collisions()
        if sum(1 for s in self.snakes if s.alive) < alive_before:
            self.sound.play("crash")
        if self.mode not in FILL_MODES:
            self._resolve_food()
        self.tick_count += 1
        self._check_round_end()

    def _record_input(self, snake_idx, direction):
        """Apply a human direction change and record it for replays."""
        if snake_idx < len(self.snakes):
            self.snakes[snake_idx].set_direction(direction)
        if self.recording is not None and not self.replaying:
            self.recording["inputs"].append(
                {"t": self.tick_count, "s": snake_idx, "d": list(direction)})

    def _blocked_for(self, snake):
        blocked = set(self.obstacles)
        for other in self.snakes:
            if other is snake:
                blocked.update(other.body[:-1])  # own tail tip will move
            else:
                blocked.update(other.body)
        return blocked

    def _resolve_collisions(self):
        heads = {}
        for snake in self.snakes:
            if not snake.alive:
                continue
            head = snake.head
            if not _in_bounds(head) or head in self.obstacles:
                snake.alive = False
                continue
            if head in snake.body[1:]:
                snake.alive = False
                continue
            for other in self.snakes:
                if other is snake:
                    continue
                if head in other.body:
                    snake.alive = False
                    break
            heads.setdefault(head, []).append(snake)
        for head, group in heads.items():
            if len(group) > 1:
                for snake in group:
                    snake.alive = False

    def _resolve_food(self):
        if self.food is None:
            return
        for snake in self.snakes:
            if snake.alive and snake.head == self.food:
                snake.grow(1)
                snake.score += 1
                self.sound.play("eat")
                if self.mode == SURVIVAL:
                    self.tick_ms = max(45, self.tick_ms - 4)
                if self.mode == LEVEL and snake.score % 5 == 0:
                    self.stage += 1
                    self._build_stage(self.stage)
                self.food = self._spawn_food()
                break

    def _check_round_end(self):
        total = COLS * ROWS
        if self.mode in FILL_MODES:
            snake = self.snakes[0]
            if len(snake.body) >= total:
                self.win = True
                self.result_text = self.t("board_filled", n=len(snake.body))
                self._end_round(len(snake.body))
            elif not snake.alive:
                self._end_round(len(snake.body))
            return

        alive = [s for s in self.snakes if s.alive]
        if self.mode in TWO_SNAKE_MODES:
            if len(alive) <= 1:
                self._finish_versus(alive)
        else:  # CLASSIC, SURVIVAL, LEVEL
            if not alive:
                self._end_round(self.snakes[0].score)

    def _finish_versus(self, alive):
        if len(alive) == 1:
            winner = alive[0]
            name = self._snake_label(self.snakes.index(winner))
            self.result_text = self.t("winner", name=name)
            self.win = not self.snakes[0].is_ai and winner is self.snakes[0]
            score = winner.score
        else:
            self.result_text = self.t("draw")
            score = max((s.score for s in self.snakes), default=0)
        self._end_round(score)

    def _snake_label(self, index):
        if self.mode == BATTLE:
            return self.t("p1") if index == 0 else self.t("p2")
        if self.mode == AI_AI:
            return f"{self.t('ai')} {index + 1}"
        if self.mode == AI_HUMAN:
            return self.t("you") if index == 0 else self.t("ai")
        return self.t("player")

    def _end_round(self, score):
        if self.win:
            self.sound.play("win")
        # Replays don't affect scores/leaderboards/saved replays.
        if self.replaying:
            self.state = STATE_OVER
            return
        mode_key = MODE_KEYS[self.mode]
        levelled = self.profile.add_score(mode_key, score)
        if levelled:
            self.level_up_flash = 1800  # ms
        self._save_recording(score)
        save_profile(self.profile)
        self.state = STATE_OVER

    def _save_recording(self, score):
        """Finalize the round's recording and keep it for replay."""
        if not self.recording:
            return
        rec = self.recording
        rec["score"] = int(score)
        rec["win"] = bool(self.win)
        rec["ticks"] = self.tick_count
        rec["name"] = self.profile.name
        rec["ts"] = int(time.time())
        self.last_replay = rec
        self.profile.replays.insert(0, rec)
        del self.profile.replays[REPLAY_LIMIT:]

    def _human_snake(self):
        """The snake a human controls in the current round, or None."""
        if not self.snakes:
            return None
        first = self.snakes[0]
        return first if not first.is_ai else None

    # -- Input --------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        # Press feedback: arm on mouse-down, fire on mouse-up over the same button.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            btn = self._button_at(event.pos)
            self.mouse_down = (btn["action"], btn.get("arg")) if btn else None
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            btn = self._button_at(event.pos)
            if btn and self.mouse_down == (btn["action"], btn.get("arg")):
                self._dispatch(btn["action"], btn.get("arg"))
            self.mouse_down = None
            return
        if event.type != pygame.KEYDOWN:
            return

        # Key-capture screen intercepts everything.
        if self.state == STATE_REBIND:
            self._key_rebind(event)
            return

        dispatch = {
            STATE_MENU: self._key_menu,
            STATE_SETTINGS: self._key_settings,
            STATE_AI_MENU: self._key_ai_menu,
            STATE_THEME: self._key_theme,
            STATE_AUDIO: self._key_audio,
            STATE_CONTROLS: self._key_controls,
            STATE_LEADERBOARD: self._key_simple_back,
            STATE_REPLAYS: self._key_simple_back,
            STATE_READY: self._key_ready,
            STATE_PLAY: self._key_play,
            STATE_OVER: self._key_over,
            STATE_COLOR: self._key_color,
            STATE_LANG: self._key_lang,
            STATE_NAME: self._key_name,
        }
        if self.state in dispatch:
            dispatch[self.state](event)

    def _button_at(self, pos):
        for button in reversed(self.buttons):
            if button["rect"].collidepoint(pos):
                return button
        return None

    def _dispatch(self, action, arg=None):
        if action != "dir":
            self.sound.play("select")
        if action == "open_theme":
            self._open_sub(STATE_THEME); return
        if action == "open_audio":
            self._open_sub(STATE_AUDIO); return
        if action == "open_controls":
            self._open_sub(STATE_CONTROLS); return
        if action == "open_leaderboard":
            self._open_sub(STATE_LEADERBOARD); return
        if action == "set_theme":
            self.profile.theme = arg
            apply_theme(arg)
            save_profile(self.profile); return
        if action == "toggle_sound":
            self.profile.sound = not self.profile.sound
            save_profile(self.profile); return
        if action == "toggle_music":
            self.profile.music = not self.profile.music
            self.sound.set_music(self.profile.music)
            save_profile(self.profile); return
        if action == "toggle_fps":
            self.profile.show_fps = not self.profile.show_fps
            save_profile(self.profile); return
        if action == "rebind":
            self.rebind_dir = arg
            self.state = STATE_REBIND; return
        if action == "reset_keys":
            self.profile.keymap = dict(DEFAULT_KEYMAP)
            save_profile(self.profile); return
        if action == "open_replays":
            self._open_sub(STATE_REPLAYS); return
        if action == "watch_replay":  # the run just played
            if self.last_replay:
                self.start_replay(self.last_replay)
            return
        if action == "replay_current":  # re-run the replay being watched
            if self.current_replay:
                self.start_replay(self.current_replay)
            return
        if action == "play_replay":   # by index in profile.replays
            if 0 <= arg < len(self.profile.replays):
                self.start_replay(self.profile.replays[arg])
            return
        if action == "start_mode":
            self.mode = arg
            self.start_round()
        elif action == "open_ai_menu":
            self.state = STATE_AI_MENU
        elif action == "open_settings":
            self.state = STATE_SETTINGS
        elif action == "open_color":
            self._open_sub(STATE_COLOR)
        elif action == "open_lang":
            self._open_sub(STATE_LANG)
        elif action == "open_name":
            self.name_buffer = self.profile.name
            self._open_sub(STATE_NAME)
        elif action == "set_lang":
            self.profile.language = arg
            save_profile(self.profile)
        elif action == "set_color":
            self.profile.color_index = arg
            save_profile(self.profile)
        elif action == "back_menu":
            self.state = STATE_MENU
        elif action == "sub_back":
            self.state = self.sub_return
        elif action == "to_menu":
            self.state = STATE_MENU
        elif action == "restart":
            self.start_round()
        elif action == "quit":
            self.running = False
        elif action == "dir":
            if self.replaying:
                return
            if self.state == STATE_READY:
                self.state = STATE_PLAY
            if self._human_snake():
                self._record_input(0, arg)

    def _open_sub(self, state):
        self.sub_return = self.state if self.state in (STATE_MENU, STATE_SETTINGS) else STATE_MENU
        self.state = state

    def _key_menu(self, event):
        key = event.key
        if pygame.K_1 <= key <= pygame.K_6:
            idx = key - pygame.K_1
            if idx < len(MAIN_MENU_MODES):
                self.mode = MAIN_MENU_MODES[idx]
                self.start_round()
        elif key == pygame.K_a:
            self.state = STATE_AI_MENU
        elif key == pygame.K_s:
            self.state = STATE_SETTINGS
        elif key == pygame.K_c:
            self._open_sub(STATE_COLOR)
        elif key == pygame.K_l:
            self._open_sub(STATE_LANG)
        elif key == pygame.K_n:
            self.name_buffer = self.profile.name
            self._open_sub(STATE_NAME)
        elif key == pygame.K_ESCAPE:
            self.running = False

    def _key_settings(self, event):
        actions = {
            pygame.K_1: lambda: self._open_sub(STATE_LANG),
            pygame.K_2: lambda: self._open_sub(STATE_COLOR),
            pygame.K_3: lambda: self._open_sub(STATE_THEME),
            pygame.K_4: lambda: self._open_sub(STATE_AUDIO),
            pygame.K_5: lambda: self._open_sub(STATE_CONTROLS),
            pygame.K_6: self._open_name_screen,
        }
        if event.key in actions:
            actions[event.key]()
        elif event.key == pygame.K_ESCAPE:
            self.state = STATE_MENU

    def _open_name_screen(self):
        self.name_buffer = self.profile.name
        self._open_sub(STATE_NAME)

    def _key_theme(self, event):
        if event.key == pygame.K_ESCAPE:
            self.state = self.sub_return
        elif pygame.K_1 <= event.key <= pygame.K_4:
            idx = event.key - pygame.K_1
            if idx < len(THEME_ORDER):
                self.profile.theme = THEME_ORDER[idx]
                apply_theme(self.profile.theme)
                save_profile(self.profile)

    def _key_audio(self, event):
        if event.key == pygame.K_ESCAPE:
            self.state = self.sub_return
        elif event.key == pygame.K_1:
            self._dispatch("toggle_sound")
        elif event.key == pygame.K_2:
            self._dispatch("toggle_music")
        elif event.key == pygame.K_3:
            self._dispatch("toggle_fps")

    def _key_controls(self, event):
        if event.key == pygame.K_ESCAPE:
            self.state = self.sub_return
        elif event.key == pygame.K_r:
            self._dispatch("reset_keys")
        elif pygame.K_1 <= event.key <= pygame.K_4:
            self.rebind_dir = MOVE_DIRS[event.key - pygame.K_1]
            self.state = STATE_REBIND

    def _key_rebind(self, event):
        if event.key == pygame.K_ESCAPE:
            self.rebind_dir = None
            self.state = STATE_CONTROLS
            return
        if self.rebind_dir is not None:
            self.profile.keymap[self.rebind_dir] = event.key
            save_profile(self.profile)
            self.sound.play("select")
        self.rebind_dir = None
        self.state = STATE_CONTROLS

    def _key_simple_back(self, event):
        if event.key in (pygame.K_ESCAPE, pygame.K_m):
            self.state = self.sub_return

    def _key_ai_menu(self, event):
        key = event.key
        if pygame.K_1 <= key <= pygame.K_2:
            idx = key - pygame.K_1
            if idx < len(AI_MENU_MODES):
                self.mode = AI_MENU_MODES[idx]
                self.start_round()
        elif key == pygame.K_ESCAPE:
            self.state = STATE_MENU

    def _key_ready(self, event):
        if event.key == pygame.K_SPACE:
            self.state = STATE_PLAY
        elif event.key in (pygame.K_ESCAPE, pygame.K_m):
            self.state = STATE_MENU

    def _key_play(self, event):
        key = event.key
        if self.replaying:
            if key in (pygame.K_m, pygame.K_ESCAPE):
                self.state = STATE_MENU
            return  # no live control during playback
        if key == pygame.K_m:
            self.state = STATE_MENU
            return
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if not self.snakes:
            return
        p1 = self.snakes[0]
        if not p1.is_ai:
            # Player 1 / single player: the remappable keymap.
            for d in MOVE_DIRS:
                if key == self.profile.keymap[d]:
                    self._record_input(0, DIR_VECTORS[d])
                    break
            # Arrow keys remain a fixed convenience in single-player.
            if len(self.snakes) == 1:
                arrows = {pygame.K_UP: UP, pygame.K_DOWN: DOWN,
                          pygame.K_LEFT: LEFT, pygame.K_RIGHT: RIGHT}
                if key in arrows:
                    self._record_input(0, arrows[key])
        if self.mode == BATTLE and len(self.snakes) > 1:
            arrows = {pygame.K_UP: UP, pygame.K_DOWN: DOWN,
                      pygame.K_LEFT: LEFT, pygame.K_RIGHT: RIGHT}
            if key in arrows:
                self._record_input(1, arrows[key])

    def _key_over(self, event):
        if event.key == pygame.K_SPACE:
            if self.replaying and self.current_replay:
                self.start_replay(self.current_replay)
            else:
                self.start_round()
        elif event.key in (pygame.K_m, pygame.K_ESCAPE):
            self.state = STATE_MENU

    def _key_color(self, event):
        if event.key == pygame.K_ESCAPE:
            self.state = self.sub_return
        elif pygame.K_1 <= event.key <= pygame.K_9:
            self.profile.color_index = event.key - pygame.K_1
            save_profile(self.profile)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.profile.color_index = (self.profile.color_index - 1) % len(SNAKE_COLORS)
            save_profile(self.profile)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.profile.color_index = (self.profile.color_index + 1) % len(SNAKE_COLORS)
            save_profile(self.profile)

    def _key_lang(self, event):
        if event.key == pygame.K_ESCAPE:
            self.state = self.sub_return
        elif pygame.K_1 <= event.key <= pygame.K_3:
            self.profile.language = LANG_ORDER[event.key - pygame.K_1]
            save_profile(self.profile)

    def _key_name(self, event):
        if event.key == pygame.K_RETURN:
            self.profile.name = self.name_buffer.strip() or "Player"
            save_profile(self.profile)
            self.state = self.sub_return
        elif event.key == pygame.K_ESCAPE:
            self.state = self.sub_return
        elif event.key == pygame.K_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]
        else:
            char = event.unicode
            if char and char.isprintable() and len(self.name_buffer) < 14:
                self.name_buffer += char

    # -- Rendering ----------------------------------------------------------
    def draw(self):
        self.buttons = []
        self.screen.fill(BLACK)
        screens = {
            STATE_MENU: self._draw_menu,
            STATE_SETTINGS: self._draw_settings,
            STATE_AI_MENU: self._draw_ai_menu,
            STATE_COLOR: self._draw_color_menu,
            STATE_LANG: self._draw_lang_menu,
            STATE_NAME: self._draw_name_menu,
            STATE_THEME: self._draw_theme_menu,
            STATE_AUDIO: self._draw_audio_menu,
            STATE_CONTROLS: self._draw_controls_menu,
            STATE_REBIND: self._draw_rebind,
            STATE_LEADERBOARD: self._draw_leaderboard,
            STATE_REPLAYS: self._draw_replays,
        }
        if self.state in screens:
            screens[self.state]()
        else:
            self._draw_play_area()
            self._draw_hud()
            self._draw_control_bar()
            if self.state == STATE_READY:
                self._draw_center_banner(self.t("press_space"))
            elif self.state == STATE_OVER:
                self._draw_game_over()
        if self.profile.show_fps:
            self._draw_fps()
        pygame.display.flip()

    def _draw_fps(self):
        fps = int(self.clock.get_fps())
        self._text(f"{fps} FPS", "tiny", DIM, topleft=(12, HEIGHT - 24))

    def _text(self, text, font, color, center=None, topleft=None):
        surf = self.fonts[font].render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = center
        elif topleft:
            rect.topleft = topleft
        self.screen.blit(surf, rect)
        return rect

    # -- Reusable button widgets -------------------------------------------
    def _glow(self, rect, color, radius):
        """Soft outer glow behind a rounded rect, used for hover feedback."""
        pad = 14
        glow = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)
        cx, cy = glow.get_width() // 2, glow.get_height() // 2
        for grow, alpha in ((12, 16), (8, 30), (4, 50)):
            r = pygame.Rect(0, 0, rect.w + grow * 2, rect.h + grow * 2)
            r.center = (cx, cy)
            pygame.draw.rect(glow, (*color, alpha), r, border_radius=radius + grow)
        self.screen.blit(glow, (rect.x - pad, rect.y - pad))

    def _draw_badge(self, rect, text, active):
        """A tiny shortcut-key hint in the button's top-left corner."""
        self._text(str(text), "tiny", ACCENT if active else DIM,
                   topleft=(rect.x + 11, rect.y + 8))

    def _button(self, rect, label, action, arg=None, font="small",
                selected=False, swatch=None, radius=BTN_RADIUS, badge=None):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        pressed = self.mouse_down == (action, arg) and hover
        if hover and not selected and not pressed:
            self._glow(rect, ACCENT, radius)
        if pressed:
            fill = ACCENT_DEEP
        elif selected:
            fill = ACCENT
        elif hover:
            fill = PANEL_HOVER
        else:
            fill = PANEL
        active = hover or selected or pressed
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        pygame.draw.rect(self.screen, ACCENT if active else BORDER, rect,
                         2 if active else 1, border_radius=radius)
        txt_color = BLACK if selected else WHITE
        cx = rect.centerx
        if swatch is not None:
            sw = pygame.Rect(rect.x + 16, rect.centery - 10, 20, 20)
            pygame.draw.rect(self.screen, swatch, sw, border_radius=6)
            pygame.draw.rect(self.screen, BORDER, sw, 1, border_radius=6)
            cx += 16
        self._text(label, font, txt_color, center=(cx, rect.centery))
        if badge is not None:
            self._draw_badge(rect, badge, active)
        self.buttons.append({"rect": rect, "action": action, "arg": arg})

    def _mode_button(self, rect, mode, badge=None):
        key = MODE_KEYS[mode]
        hover = rect.collidepoint(pygame.mouse.get_pos())
        pressed = self.mouse_down == ("start_mode", mode) and hover
        if hover and not pressed:
            self._glow(rect, ACCENT, BTN_RADIUS)
        active = hover or pressed
        pygame.draw.rect(self.screen, ACCENT_DEEP if pressed else (PANEL_HOVER if hover else PANEL),
                         rect, border_radius=BTN_RADIUS)
        pygame.draw.rect(self.screen, ACCENT if active else BORDER, rect,
                         2 if active else 1, border_radius=BTN_RADIUS)
        self._text(self.t(key), "small", WHITE,
                   center=(rect.centerx, rect.centery - 9))
        best = self.profile.highscores.get(key, 0)
        self._text(f"{self.t('high')}: {best}", "tiny", GREY,
                   center=(rect.centerx, rect.centery + 13))
        if badge is not None:
            self._draw_badge(rect, badge, active)
        self.buttons.append({"rect": rect, "action": "start_mode", "arg": mode})

    # -- Menus --------------------------------------------------------------
    def _draw_menu(self):
        # Bold title; credits dimmed to keep focus on the buttons below.
        self._text(self.t("title"), "title", ACCENT, center=(WIDTH // 2, 102))
        self._text(self.t("credits"), "tiny", DIM, center=(WIDTH // 2, 144))

        # Small version / update status pinned to the top-right corner.
        self._draw_status_corner()

        # Wider side margins so nothing hugs the edges.
        margin, gap = 50, 22
        bw = (WIDTH - 2 * margin - gap) // 2
        bh, srow_h = 64, 54
        block_h = 3 * bh + 2 * gap + 28 + srow_h
        band_top, band_bottom = 178, HEIGHT - 134
        start_x = margin
        start_y = band_top + max(0, (band_bottom - band_top - block_h) // 2)
        for i, mode in enumerate(MAIN_MENU_MODES):
            col, row = i % 2, i // 2
            rect = pygame.Rect(start_x + col * (bw + gap),
                               start_y + row * (bh + gap), bw, bh)
            self._mode_button(rect, mode, badge=i + 1)

        # Four-wide utility row: All-AI · Leaderboard · Replays · Settings.
        row_y = start_y + 3 * (bh + gap) + 28
        ug = 14
        tw = (WIDTH - 2 * margin - 3 * ug) // 4
        util = [
            (self.t("ai_modes"), "open_ai_menu", "A"),
            (self.t("leaderboard_btn"), "open_leaderboard", None),
            (self.t("replays_btn"), "open_replays", None),
            (self.t("settings"), "open_settings", "S"),
        ]
        for i, (label, action, badge) in enumerate(util):
            self._button(pygame.Rect(start_x + i * (tw + ug), row_y, tw, srow_h),
                         label, action, font="tiny", badge=badge)

        # A thin separator divides the menu from the profile card.
        card_top = HEIGHT - 100
        sep_y = card_top - 22
        pygame.draw.line(self.screen, DIVIDER,
                         (margin + 40, sep_y), (WIDTH - margin - 40, sep_y))
        self._draw_profile_card(card_top)
        self._text(self.t("menu_hint"), "tiny", DIM, center=(WIDTH // 2, HEIGHT - 28))

    def _draw_status_corner(self):
        """Compact version + colored status dot in the top-right corner."""
        dot_colors = {"checking": GREY, "latest": ACCENT, "outdated": GOLD,
                      "unknown": DIM}
        dot = dot_colors.get(self.update_state, DIM)
        if self.update_state == "outdated" and self.latest_version:
            label = f"v{APP_VERSION} → {self.latest_version}"
            text_color = GOLD
        else:
            label = f"v{APP_VERSION}"
            text_color = GREY
        surf = self.fonts["tiny"].render(label, True, text_color)
        rect = surf.get_rect()
        rect.topright = (WIDTH - 16, 14)
        self.screen.blit(surf, rect)
        pygame.draw.circle(self.screen, dot, (rect.left - 11, rect.centery + 1), 4)

    def _draw_profile_card(self, top):
        """A small card grouping name | level | XP with thin dividers."""
        prof = self.profile
        card_w, card_h = 478, 52
        card = pygame.Rect((WIDTH - card_w) // 2, top, card_w, card_h)
        pygame.draw.rect(self.screen, PANEL, card, border_radius=BTN_RADIUS)
        pygame.draw.rect(self.screen, BORDER, card, 1, border_radius=BTN_RADIUS)

        # Unequal segments: the name needs the most room.
        d1 = card.x + 214          # name | level divider
        d2 = card.x + 332          # level | xp divider
        for x in (d1, d2):
            pygame.draw.line(self.screen, DIVIDER, (x, card.y + 11), (x, card.bottom - 11))

        # Segment 1: color swatch + name.
        sw = pygame.Rect(card.x + 18, card.centery - 10, 20, 20)
        pygame.draw.rect(self.screen, SNAKE_COLORS[prof.color_index], sw, border_radius=6)
        pygame.draw.rect(self.screen, BORDER, sw, 1, border_radius=6)
        self._text(prof.name, "small", WHITE, topleft=(sw.right + 12, card.centery - 13))

        # Segment 2: level (accent).
        self._text(f"{self.t('level_label')} {prof.level}", "small", ACCENT,
                   center=((d1 + d2) // 2, card.centery))

        # Segment 3: XP progress.
        self._text(f"{self.t('xp')} {prof.xp}/{Profile.xp_for_level(prof.level)}",
                   "small", GREY, center=((d2 + card.right) // 2, card.centery))

    def _draw_settings(self):
        self._text(self.t("settings_title"), "big", ACCENT, center=(WIDTH // 2, 78))
        bw, bh, vg = 380, 58, 14
        x = (WIDTH - bw) // 2
        y0 = 150
        lang_label = {"en": "English", "zh_tw": "繁體中文", "zh_cn": "简体中文"}[self.profile.language]
        theme_label = self.t("theme_" + self.profile.theme)
        rows = [
            (f"{self.t('lang_btn')}:  {lang_label}", "open_lang", None),
            (f"{self.t('color_btn')}", "open_color", SNAKE_COLORS[self.profile.color_index]),
            (f"{self.t('theme_btn')}:  {theme_label}", "open_theme", None),
            (f"{self.t('audio_btn')}", "open_audio", None),
            (f"{self.t('controls_btn')}", "open_controls", None),
            (f"{self.t('name_btn')}:  {self.profile.name}", "open_name", None),
        ]
        for i, (label, action, swatch) in enumerate(rows):
            self._button(pygame.Rect(x, y0 + i * (bh + vg), bw, bh),
                         f"{label}", action, swatch=swatch, badge=i + 1)
        self._button(pygame.Rect(x, y0 + 6 * (bh + vg) + 6, bw, 50),
                     self.t("back"), "back_menu")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_theme_menu(self):
        self._text(self.t("theme_menu"), "big", ACCENT, center=(WIDTH // 2, 90))
        bw, bh = 380, 60
        x = (WIDTH - bw) // 2
        for i, name in enumerate(THEME_ORDER):
            sw = THEMES[name]["accent"]
            self._button(pygame.Rect(x, 180 + i * (bh + 18), bw, bh),
                         f"{self.t('theme_' + name)}", "set_theme", name,
                         selected=(self.profile.theme == name), swatch=sw, badge=i + 1)
        self._button(pygame.Rect(x, 180 + 4 * (bh + 18) + 8, bw, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_audio_menu(self):
        self._text(self.t("audio_menu"), "big", ACCENT, center=(WIDTH // 2, 100))
        bw, bh = 400, 62
        x = (WIDTH - bw) // 2
        toggles = [
            (self.t("sound_label"), self.profile.sound, "toggle_sound"),
            (self.t("music_label"), self.profile.music, "toggle_music"),
            (self.t("fps_label"), self.profile.show_fps, "toggle_fps"),
        ]
        for i, (label, on, action) in enumerate(toggles):
            state = self.t("on") if on else self.t("off")
            self._button(pygame.Rect(x, 190 + i * (bh + 18), bw, bh),
                         f"{label}:  {state}", action, badge=i + 1)
        self._button(pygame.Rect(x, 190 + 3 * (bh + 18) + 10, bw, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_controls_menu(self):
        self._text(self.t("controls_menu"), "big", ACCENT, center=(WIDTH // 2, 90))
        bw, bh = 400, 60
        x = (WIDTH - bw) // 2
        for i, d in enumerate(MOVE_DIRS):
            label = f"{self.t('dir_' + d)}:  [ {key_label(self.profile.keymap[d])} ]"
            self._button(pygame.Rect(x, 170 + i * (bh + 16), bw, bh),
                         label, "rebind", d, badge=i + 1)
        self._button(pygame.Rect(x, 170 + 4 * (bh + 16) + 6, bw // 2 - 6, 50),
                     self.t("reset_default"), "reset_keys", font="tiny")
        self._button(pygame.Rect(x + bw // 2 + 6, 170 + 4 * (bh + 16) + 6, bw // 2 - 6, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("rebind_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_rebind(self):
        # Keep the controls list visible, dimmed, with a capture prompt over it.
        self._draw_controls_menu()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        d = self.rebind_dir or "up"
        self._text(self.t("dir_" + d), "mid", ACCENT, center=(WIDTH // 2, HEIGHT // 2 - 30))
        self._text(self.t("press_key"), "big", WHITE, center=(WIDTH // 2, HEIGHT // 2 + 30))

    def _draw_leaderboard(self):
        self._text(self.t("leaderboard_title"), "big", ACCENT, center=(WIDTH // 2, 64))
        margin = 40
        col_w = (WIDTH - 2 * margin - 20) // 2
        x0 = margin
        y0 = 120
        row_h = 118
        for i, key in enumerate(MODE_KEYS):
            col, row = i % 2, i // 2
            bx = x0 + col * (col_w + 20)
            by = y0 + row * row_h
            panel = pygame.Rect(bx, by, col_w, row_h - 14)
            pygame.draw.rect(self.screen, PANEL, panel, border_radius=10)
            pygame.draw.rect(self.screen, BORDER, panel, 1, border_radius=10)
            self._text(self.t(key), "small", ACCENT, topleft=(bx + 12, by + 8))
            board = self.profile.leaderboards.get(key, [])
            if not board:
                self._text(self.t("empty_board"), "tiny", DIM, topleft=(bx + 12, by + 38))
            for r, entry in enumerate(board):
                line = f"{r + 1}. {entry['name'][:9]:<9}  {entry['score']}"
                self._text(line, "tiny", WHITE if r == 0 else GREY,
                           topleft=(bx + 12, by + 36 + r * 14))
        self._button(pygame.Rect(WIDTH // 2 - 90, HEIGHT - 86, 180, 48),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 28))

    def _draw_ai_menu(self):
        self._text(self.t("ai_menu_title"), "big", ACCENT, center=(WIDTH // 2, 90))
        bw, bh = 360, 64
        x = (WIDTH - bw) // 2
        for i, mode in enumerate(AI_MENU_MODES):
            key = MODE_KEYS[mode]
            best = self.profile.highscores.get(key, 0)
            rect = pygame.Rect(x, 190 + i * (bh + 20), bw, bh)
            self._button(rect, f"{i + 1}.  {self.t(key)}   ({self.t('high')}: {best})",
                         "start_mode", mode)
        self._button(pygame.Rect(x, 190 + len(AI_MENU_MODES) * (bh + 20) + 10, bw, 50),
                     self.t("back"), "back_menu")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 36))

    def _draw_color_menu(self):
        self._text(self.t("color_menu"), "mid", ACCENT, center=(WIDTH // 2, 70))
        cols, size, gap = 3, 80, 30
        total_w = cols * size + (cols - 1) * gap
        start_x = (WIDTH - total_w) // 2
        start_y = 130
        for i, color in enumerate(SNAKE_COLORS):
            cx = start_x + (i % cols) * (size + gap)
            cy = start_y + (i // cols) * (size + gap)
            rect = pygame.Rect(cx, cy, size, size)
            hover = rect.collidepoint(pygame.mouse.get_pos())
            selected = i == self.profile.color_index
            if hover or selected:
                self._glow(rect, ACCENT, 12)
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            if selected:
                pygame.draw.rect(self.screen, ACCENT, rect.inflate(10, 10), 3, border_radius=14)
            self._text(str(i + 1), "small", BLACK, center=rect.center)
            self.buttons.append({"rect": rect, "action": "set_color", "arg": i})
        self._button(pygame.Rect(WIDTH // 2 - 90, HEIGHT - 90, 180, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 28))

    def _draw_lang_menu(self):
        self._text(self.t("lang_menu"), "mid", ACCENT, center=(WIDTH // 2, 90))
        options = [("english", "en"), ("tchinese", "zh_tw"), ("schinese", "zh_cn")]
        bw, bh = 360, 60
        x = (WIDTH - bw) // 2
        for i, (label_key, code) in enumerate(options):
            rect = pygame.Rect(x, 180 + i * (bh + 18), bw, bh)
            self._button(rect, f"{i + 1}.  {self.t(label_key)}", "set_lang", code,
                         selected=(self.profile.language == code))
        self._button(pygame.Rect(x, 180 + 3 * (bh + 18) + 10, bw, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_name_menu(self):
        self._text(self.t("name_menu"), "mid", ACCENT, center=(WIDTH // 2, 110))
        box = pygame.Rect(WIDTH // 2 - 160, 190, 320, 56)
        pygame.draw.rect(self.screen, DARK, box, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT, box, 2, border_radius=8)
        cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " "
        self._text(self.name_buffer + cursor, "mid", WHITE, center=box.center)
        self._text(self.t("name_hint"), "small", GREY, center=(WIDTH // 2, 290))
        self._button(pygame.Rect(WIDTH // 2 - 90, 340, 180, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_replays(self):
        self._text(self.t("replays_title"), "big", ACCENT, center=(WIDTH // 2, 70))
        replays = self.profile.replays
        if not replays:
            self._text(self.t("no_replays"), "small", DIM, center=(WIDTH // 2, HEIGHT // 2))
        bw, bh = 472, 52
        x = (WIDTH - bw) // 2
        for i, rec in enumerate(replays[:REPLAY_LIMIT]):
            mode_name = self.t(MODE_KEYS[rec.get("mode", 0)])
            tag = self.t("you_win") if rec.get("win") else ""
            label = f"{mode_name}   ·   {self.t('score')} {rec.get('score', 0)}   {tag}"
            self._button(pygame.Rect(x, 128 + i * (bh + 10), bw, bh),
                         label, "play_replay", i, font="small")
        self._button(pygame.Rect(WIDTH // 2 - 90, HEIGHT - 70, 180, 46),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 24))

    # -- Play area ----------------------------------------------------------
    def _draw_play_area(self):
        play_rect = pygame.Rect(0, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, DARK, play_rect)
        for x in range(COLS + 1):
            px = x * CELL
            pygame.draw.line(self.screen, GRID_LINE, (px, PLAY_TOP), (px, CONTROL_TOP))
        for y in range(ROWS + 1):
            py = PLAY_TOP + y * CELL
            pygame.draw.line(self.screen, GRID_LINE, (0, py), (PLAY_WIDTH, py))

        for (ox, oy) in self.obstacles:
            self._cell_rect(ox, oy, fill=OBSTACLE, inset=1, radius=4)

        if self.food is not None:
            fx, fy = self.food
            self._cell_rect(fx, fy, fill=FOOD_COLOR, inset=5, radius=8)

        for snake in self.snakes:
            self._draw_snake(snake)

    def _draw_snake(self, snake):
        n = len(snake.body)
        base = snake.color if snake.alive else tuple(max(0, c - 80) for c in snake.color)
        for i, (x, y) in enumerate(snake.body):
            shade = 1.0 - (i / max(1, n)) * 0.45
            color = tuple(int(c * shade) for c in base)
            inset = 2 if i else 1
            radius = 6 if i else 8
            self._cell_rect(x, y, fill=color, inset=inset, radius=radius)

    def _cell_rect(self, x, y, fill, inset=0, radius=0):
        rect = pygame.Rect(
            x * CELL + inset,
            PLAY_TOP + y * CELL + inset,
            CELL - inset * 2,
            CELL - inset * 2,
        )
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)

    def _draw_hud(self):
        bar = pygame.Rect(0, 0, WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.screen, BLACK, bar)
        pygame.draw.line(self.screen, GRID_LINE, (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT))
        self._text(self.t(MODE_KEYS[self.mode]), "small", ACCENT, topleft=(16, 10))
        if self.replaying:  # REPLAY badge, top-right of the HUD
            self._text(self.t("replay_label"), "small", GOLD, topleft=(WIDTH - 110, 10))

        if self.mode in FILL_MODES:
            filled = len(self.snakes[0].body)
            self._text(f"{self.t('filled')}: {filled} / {COLS * ROWS}", "small",
                       WHITE, topleft=(16, 34))
            best = self.profile.highscores[MODE_KEYS[self.mode]]
            self._text(f"{self.t('high')}: {best}", "small", GREY, topleft=(280, 34))
        elif self.mode in TWO_SNAKE_MODES:
            parts = [f"{self._snake_label(i)}: {s.score}" for i, s in enumerate(self.snakes)]
            self._text("   ".join(parts), "small", WHITE, topleft=(16, 34))
        else:
            score = self.snakes[0].score
            self._text(f"{self.t('score')}: {score}", "small", WHITE, topleft=(16, 34))
            best = self.profile.highscores[MODE_KEYS[self.mode]]
            self._text(f"{self.t('high')}: {best}", "small", GREY, topleft=(180, 34))
            if self.mode == LEVEL:
                self._text(f"{self.t('stage')}: {self.stage}", "small", WHITE,
                           topleft=(320, 34))

    # -- On-screen control bar (D-pad + Menu) ------------------------------
    def _draw_control_bar(self):
        bar = pygame.Rect(0, CONTROL_TOP, WIDTH, CONTROL_HEIGHT)
        pygame.draw.rect(self.screen, BLACK, bar)
        pygame.draw.line(self.screen, GRID_LINE, (0, CONTROL_TOP), (WIDTH, CONTROL_TOP))

        # Menu button (left).
        self._button(pygame.Rect(20, CONTROL_TOP + 36, 130, 44),
                     self.t("menu_btn"), "to_menu")

        # D-pad (right) — only when a human is actively controlling (not replay).
        if (self.state in (STATE_READY, STATE_PLAY) and not self.replaying
                and self._human_snake() is not None):
            self._draw_dpad()
        else:
            note = self.t("replay_label") if self.replaying else self.t("watching")
            self._text(note, "small", GOLD if self.replaying else GREY,
                       center=(WIDTH - 150, CONTROL_TOP + CONTROL_HEIGHT // 2))

    def _draw_dpad(self):
        cx = WIDTH - 110
        cy = CONTROL_TOP + CONTROL_HEIGHT // 2
        b = 40
        layout = {
            UP: (cx, cy - (b + 4)),
            DOWN: (cx, cy + (b + 4)),
            LEFT: (cx - (b + 4), cy),
            RIGHT: (cx + (b + 4), cy),
        }
        for direction, (bx, by) in layout.items():
            rect = pygame.Rect(0, 0, b, b)
            rect.center = (bx, by)
            hover = rect.collidepoint(pygame.mouse.get_pos())
            if hover:
                self._glow(rect, ACCENT, 10)
            pygame.draw.rect(self.screen, PANEL_HOVER if hover else PANEL, rect,
                             border_radius=10)
            pygame.draw.rect(self.screen, ACCENT if hover else BORDER, rect,
                             2 if hover else 1, border_radius=10)
            self._draw_arrow(rect, direction, ACCENT if hover else WHITE)
            self.buttons.append({"rect": rect, "action": "dir", "arg": direction})

    def _draw_arrow(self, rect, direction, color=WHITE):
        cx, cy = rect.center
        s = 9
        if direction == UP:
            pts = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)]
        elif direction == DOWN:
            pts = [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)]
        elif direction == LEFT:
            pts = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
        else:  # RIGHT
            pts = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
        pygame.draw.polygon(self.screen, color, pts)

    # -- Overlays -----------------------------------------------------------
    def _draw_center_banner(self, text):
        overlay = pygame.Surface((WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, PLAY_TOP))
        self._text(text, "mid", WHITE, center=(WIDTH // 2, PLAY_TOP + PLAY_HEIGHT // 2))

    def _draw_game_over(self):
        overlay = pygame.Surface((WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, PLAY_TOP))
        cy = PLAY_TOP + PLAY_HEIGHT // 2
        if self.win:
            self._text(self.t("you_win"), "big", GOLD, center=(WIDTH // 2, cy - 80))
        else:
            self._text(self.t("game_over"), "big", RED, center=(WIDTH // 2, cy - 80))
        if self.result_text:
            self._text(self.result_text, "mid", WHITE, center=(WIDTH // 2, cy - 18))
        if self.level_up_flash > 0:
            self._text(self.t("level_up", lvl=self.profile.level), "small", ACCENT,
                       center=(WIDTH // 2, cy + 18))
        # Primary buttons (also bound to SPACE / M).
        if self.replaying:
            primary = (self.t("replay_again"), "replay_current")
        else:
            primary = (self.t("press_space_restart"), "restart")
        self._button(pygame.Rect(WIDTH // 2 - 200, cy + 50, 190, 50),
                     primary[0], primary[1], font="tiny")
        self._button(pygame.Rect(WIDTH // 2 + 10, cy + 50, 190, 50),
                     self.t("menu_btn"), "to_menu", font="small")
        # A "Watch replay" button for the run just played (live runs only).
        if not self.replaying and self.last_replay is not None:
            self._button(pygame.Rect(WIDTH // 2 - 95, cy + 112, 190, 46),
                         self.t("watch_replay"), "watch_replay", font="tiny")

    # -- Main loop ----------------------------------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            if self.level_up_flash > 0:
                self.level_up_flash -= dt
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    SnakeGame().run()


if __name__ == "__main__":
    main()
