#!/usr/bin/env python3
"""Snake — a multi-mode, multi-language Snake game built with Pygame.

Features
--------
* Self-contained auto-setup bootstrap (checks Python, installs/updates Pygame).
* Eight game modes across two menus:
  - Main: Classic, Survival, Battle, Level, AI vs Human, Player Fill.
  - All-AI menu: AI vs AI, AI Fill.
* On-launch update check against the project's GitHub Releases.
* Full on-screen GUI: clickable menus, a Settings menu, an All-AI menu, and a
  four-button D-pad for up/down/left/right.
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
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import pygame

# ---------------------------------------------------------------------------
# Version / update check
# ---------------------------------------------------------------------------
APP_VERSION = "1.1.1"
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

# Colors -------------------------------------------------------------------
# Palette follows a 60-30-10 split: BLACK base (~60%), PANEL button fills
# (~30%), and ACCENT for borders/highlights/text accents (~10%).
BLACK = (15, 15, 20)           # 60% — background base
DARK = (24, 24, 32)            # play-field / input wells
PANEL = (30, 31, 40)           # 30% — default button fill
PANEL_HOVER = (44, 46, 58)     # button fill on hover
GRID_LINE = (34, 34, 44)
BORDER = (58, 60, 74)          # subtle default button border
WHITE = (236, 236, 241)
GREY = (140, 140, 150)
DIM = (86, 88, 100)            # low-contrast text (credits / hints)
DIVIDER = (54, 56, 70)
RED = (220, 70, 70)
GOLD = (240, 200, 90)
FOOD_COLOR = (235, 80, 90)
# Slightly desaturated, softer green — easier on the eyes over long sessions.
ACCENT = (118, 196, 162)       # 10% — accent / hover border / highlights
ACCENT_DEEP = (70, 150, 120)   # darker accent for glows and pressed states

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
        "ver_checking": "v{ver} · 检查更新中…",
        "ver_latest": "v{ver} · 已是最新版",
        "ver_outdated": "v{ver} · 有可用更新：{latest}",
        "ver_unknown": "v{ver}",
    },
}

LANG_ORDER = ["en", "zh_tw", "zh_cn"]


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

    # XP required to reach the *next* level grows linearly.
    @staticmethod
    def xp_for_level(level: int) -> int:
        return 50 * level

    def add_score(self, mode_key: str, score: int) -> bool:
        """Record a score; return ``True`` if the player levelled up."""
        if score > self.highscores.get(mode_key, 0):
            self.highscores[mode_key] = score
        self.xp += score
        levelled = False
        while self.xp >= self.xp_for_level(self.level):
            self.xp -= self.xp_for_level(self.level)
            self.level += 1
            levelled = True
        return levelled

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "language": self.language,
            "color_index": self.color_index,
            "level": self.level,
            "xp": self.xp,
            "highscores": self.highscores,
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
# The game
# ---------------------------------------------------------------------------
# Lightweight state machine.
STATE_MENU, STATE_READY, STATE_PLAY, STATE_OVER = range(4)
STATE_COLOR, STATE_LANG, STATE_NAME, STATE_SETTINGS, STATE_AI_MENU = range(4, 9)


class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake")
        self._set_window_icon()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.profile = load_profile()
        self.fonts = self._load_fonts()
        self.state = STATE_MENU
        self.mode = CLASSIC
        self.running = True

        # Clickable buttons rebuilt every frame: list of (rect, action, arg).
        self.buttons = []
        self.sub_return = STATE_MENU

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
    def start_round(self):
        self.obstacles = set()
        self.stage = 1
        self.result_text = ""
        self.win = False
        self.food = None
        color = SNAKE_COLORS[self.profile.color_index]
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
        self.state = STATE_READY

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
        return random.choice(free) if free else None

    def _build_stage(self, stage):
        """Place obstacle walls for Level mode, scaling with the stage."""
        self.obstacles = set()
        random.seed(stage * 7919)
        wall_count = min(3 + stage, 9)
        for _ in range(wall_count):
            horizontal = random.random() < 0.5
            length = random.randint(3, 6)
            x = random.randint(2, COLS - 7)
            y = random.randint(2, ROWS - 3)
            for i in range(length):
                cell = (x + i, y) if horizontal else (x, y + i)
                if _in_bounds(cell):
                    self.obstacles.add(cell)
        random.seed()
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

        self._resolve_collisions()
        if self.mode not in FILL_MODES:
            self._resolve_food()
        self._check_round_end()

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
        mode_key = MODE_KEYS[self.mode]
        levelled = self.profile.add_score(mode_key, score)
        if levelled:
            self.level_up_flash = 1800  # ms
        save_profile(self.profile)
        self.state = STATE_OVER

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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
            return
        if event.type != pygame.KEYDOWN:
            return

        dispatch = {
            STATE_MENU: self._key_menu,
            STATE_SETTINGS: self._key_settings,
            STATE_AI_MENU: self._key_ai_menu,
            STATE_READY: self._key_ready,
            STATE_PLAY: self._key_play,
            STATE_OVER: self._key_over,
            STATE_COLOR: self._key_color,
            STATE_LANG: self._key_lang,
            STATE_NAME: self._key_name,
        }
        dispatch[self.state](event)

    def _handle_click(self, pos):
        for button in reversed(self.buttons):
            if button["rect"].collidepoint(pos):
                self._dispatch(button["action"], button.get("arg"))
                return

    def _dispatch(self, action, arg=None):
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
            if self.state == STATE_READY:
                self.state = STATE_PLAY
            human = self._human_snake()
            if human:
                human.set_direction(arg)

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
        if event.key == pygame.K_1:
            self._open_sub(STATE_LANG)
        elif event.key == pygame.K_2:
            self._open_sub(STATE_COLOR)
        elif event.key == pygame.K_3:
            self.name_buffer = self.profile.name
            self._open_sub(STATE_NAME)
        elif event.key == pygame.K_ESCAPE:
            self.state = STATE_MENU

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
            if key == pygame.K_w:
                p1.set_direction(UP)
            elif key == pygame.K_s:
                p1.set_direction(DOWN)
            elif key == pygame.K_a:
                p1.set_direction(LEFT)
            elif key == pygame.K_d:
                p1.set_direction(RIGHT)
            if len(self.snakes) == 1:
                if key == pygame.K_UP:
                    p1.set_direction(UP)
                elif key == pygame.K_DOWN:
                    p1.set_direction(DOWN)
                elif key == pygame.K_LEFT:
                    p1.set_direction(LEFT)
                elif key == pygame.K_RIGHT:
                    p1.set_direction(RIGHT)
        if self.mode == BATTLE and len(self.snakes) > 1:
            p2 = self.snakes[1]
            if key == pygame.K_UP:
                p2.set_direction(UP)
            elif key == pygame.K_DOWN:
                p2.set_direction(DOWN)
            elif key == pygame.K_LEFT:
                p2.set_direction(LEFT)
            elif key == pygame.K_RIGHT:
                p2.set_direction(RIGHT)

    def _key_over(self, event):
        if event.key == pygame.K_SPACE:
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
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_SETTINGS:
            self._draw_settings()
        elif self.state == STATE_AI_MENU:
            self._draw_ai_menu()
        elif self.state == STATE_COLOR:
            self._draw_color_menu()
        elif self.state == STATE_LANG:
            self._draw_lang_menu()
        elif self.state == STATE_NAME:
            self._draw_name_menu()
        else:
            self._draw_play_area()
            self._draw_hud()
            self._draw_control_bar()
            if self.state == STATE_READY:
                self._draw_center_banner(self.t("press_space"))
            elif self.state == STATE_OVER:
                self._draw_game_over()
        pygame.display.flip()

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

    def _button(self, rect, label, action, arg=None, font="small",
                selected=False, swatch=None, radius=BTN_RADIUS):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if hover and not selected:
            self._glow(rect, ACCENT, radius)
        fill = ACCENT if selected else (PANEL_HOVER if hover else PANEL)
        border = ACCENT if (hover or selected) else BORDER
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        pygame.draw.rect(self.screen, border, rect, 2 if (hover or selected) else 1,
                         border_radius=radius)
        txt_color = BLACK if selected else WHITE
        cx = rect.centerx
        if swatch is not None:
            sw = pygame.Rect(rect.x + 16, rect.centery - 10, 20, 20)
            pygame.draw.rect(self.screen, swatch, sw, border_radius=6)
            pygame.draw.rect(self.screen, BORDER, sw, 1, border_radius=6)
            cx += 16
        self._text(label, font, txt_color, center=(cx, rect.centery))
        self.buttons.append({"rect": rect, "action": action, "arg": arg})

    def _mode_button(self, rect, mode):
        key = MODE_KEYS[mode]
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if hover:
            self._glow(rect, ACCENT, BTN_RADIUS)
        pygame.draw.rect(self.screen, PANEL_HOVER if hover else PANEL, rect,
                         border_radius=BTN_RADIUS)
        pygame.draw.rect(self.screen, ACCENT if hover else BORDER, rect,
                         2 if hover else 1, border_radius=BTN_RADIUS)
        self._text(self.t(key), "small", WHITE,
                   center=(rect.centerx, rect.centery - 9))
        best = self.profile.highscores.get(key, 0)
        self._text(f"{self.t('high')}: {best}", "tiny", GREY,
                   center=(rect.centerx, rect.centery + 13))
        self.buttons.append({"rect": rect, "action": "start_mode", "arg": mode})

    # -- Menus --------------------------------------------------------------
    def _draw_menu(self):
        # Bold title; credits dimmed to keep focus on the buttons below.
        self._text(self.t("title"), "title", ACCENT, center=(WIDTH // 2, 104))
        self._text(self.t("credits"), "tiny", DIM, center=(WIDTH // 2, 144))

        # Small version / update status pinned to the top-right corner.
        self._draw_status_corner()

        # Mode grid (2 cols x 3 rows) + an All-AI / Settings row, vertically
        # centered in the band between the credits and the bottom card.
        bw, bh, gap = 290, 64, 20
        srow_h = 56
        block_h = 3 * bh + 2 * gap + 22 + srow_h
        band_top, band_bottom = 176, HEIGHT - 120
        start_x = (WIDTH - (2 * bw + gap)) // 2
        start_y = band_top + max(0, (band_bottom - band_top - block_h) // 2)
        for i, mode in enumerate(MAIN_MENU_MODES):
            col, row = i % 2, i // 2
            rect = pygame.Rect(start_x + col * (bw + gap),
                               start_y + row * (bh + gap), bw, bh)
            self._mode_button(rect, mode)

        row_y = start_y + 3 * (bh + gap) + 22
        self._button(pygame.Rect(start_x, row_y, bw, srow_h),
                     self.t("ai_modes"), "open_ai_menu")
        self._button(pygame.Rect(start_x + bw + gap, row_y, bw, srow_h),
                     self.t("settings"), "open_settings")

        # Profile card (name | level | xp) pinned near the bottom.
        self._draw_profile_card(HEIGHT - 98)
        self._text(self.t("menu_hint"), "tiny", DIM, center=(WIDTH // 2, HEIGHT - 32))

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
        self._text(self.t("settings_title"), "big", ACCENT, center=(WIDTH // 2, 90))
        bw, bh = 360, 60
        x = (WIDTH - bw) // 2
        lang_label = {"en": "English", "zh_tw": "繁體中文", "zh_cn": "简体中文"}[self.profile.language]
        self._button(pygame.Rect(x, 180, bw, bh),
                     f"1.  {self.t('lang_btn')}:  {lang_label}", "open_lang")
        self._button(pygame.Rect(x, 180 + bh + 18, bw, bh),
                     f"2.  {self.t('color_btn')}", "open_color",
                     swatch=SNAKE_COLORS[self.profile.color_index])
        self._button(pygame.Rect(x, 180 + 2 * (bh + 18), bw, bh),
                     f"3.  {self.t('name_btn')}:  {self.profile.name}", "open_name")
        self._button(pygame.Rect(x, 180 + 3 * (bh + 18) + 12, bw, 50),
                     self.t("back"), "back_menu")
        self._text(self.t("back_hint"), "tiny", GREY, center=(WIDTH // 2, HEIGHT - 36))

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
            self._cell_rect(ox, oy, fill=(70, 70, 86), inset=1, radius=4)

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

        # D-pad (right) — only when a human is (or will be) controlling.
        if self.state in (STATE_READY, STATE_PLAY) and self._human_snake() is not None:
            self._draw_dpad()
        else:
            self._text(self.t("watching"), "small", GREY,
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
        # Buttons (also bound to SPACE / M).
        self._button(pygame.Rect(WIDTH // 2 - 200, cy + 50, 190, 50),
                     self.t("press_space_restart"), "restart", font="tiny")
        self._button(pygame.Rect(WIDTH // 2 + 10, cy + 50, 190, 50),
                     self.t("menu_btn"), "to_menu", font="small")

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
