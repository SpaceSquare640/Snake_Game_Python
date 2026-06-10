#!/usr/bin/env python3
"""Snake — a multi-mode, multi-language Snake game built with Pygame.

Features
--------
* Self-contained auto-setup bootstrap (checks Python, installs/updates Pygame).
* Six game modes: Classic, Survival, Battle, Level, AI vs AI, AI vs Human.
* Three languages: English (default), Traditional Chinese, Simplified Chinese.
* Player profiles with a persistent, XP-based level.
* Nine selectable snake colors.
* Persistent save data (``snake_save.json``).
* A Breadth-First-Search (BFS) AI with a survival fallback heuristic.

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
import os
import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import pygame

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CELL = 28
COLS = 24
ROWS = 22
HUD_HEIGHT = CELL * 2
PLAY_WIDTH = COLS * CELL
PLAY_HEIGHT = ROWS * CELL
WIDTH = PLAY_WIDTH
HEIGHT = PLAY_HEIGHT + HUD_HEIGHT
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
BLACK = (15, 15, 20)
DARK = (26, 26, 34)
GRID_LINE = (34, 34, 44)
WHITE = (235, 235, 240)
GREY = (140, 140, 150)
RED = (220, 70, 70)
FOOD_COLOR = (235, 80, 90)
ACCENT = (90, 200, 160)

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
CLASSIC, SURVIVAL, BATTLE, LEVEL, AI_AI, AI_HUMAN = range(6)
MODE_KEYS = ["classic", "survival", "battle", "level", "ai_ai", "ai_human"]


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
        "press_space": "Press SPACE to start",
        "game_over": "GAME OVER",
        "press_space_restart": "Press SPACE to play again",
        "score": "Score",
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
        "menu_hint": "1-6 select  |  C color  |  L language  |  N name  |  ESC quit",
        "in_game_hint": "M menu  |  ESC quit",
        "color_menu": "Choose snake color",
        "lang_menu": "Choose language",
        "name_menu": "Enter your name",
        "name_hint": "Type a name, ENTER to confirm",
        "back_hint": "ESC back",
        "level_up": "Level up!  Lv {lvl}",
        "xp": "XP",
        "english": "English",
        "tchinese": "Traditional Chinese",
        "schinese": "Simplified Chinese",
        "credits": "Creators: SpaceSquare, Claude Code   ·   Owner: SpaceSquare",
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
        "press_space": "按空白鍵開始",
        "game_over": "遊戲結束",
        "press_space_restart": "按空白鍵再玩一次",
        "score": "分數",
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
        "menu_hint": "1-6 選擇  |  C 顏色  |  L 語言  |  N 名稱  |  ESC 離開",
        "in_game_hint": "M 選單  |  ESC 離開",
        "color_menu": "選擇蛇身顏色",
        "lang_menu": "選擇語言",
        "name_menu": "輸入你的名稱",
        "name_hint": "輸入名稱，按 ENTER 確認",
        "back_hint": "ESC 返回",
        "level_up": "升級！等級 {lvl}",
        "xp": "經驗",
        "english": "英文 English",
        "tchinese": "繁體中文",
        "schinese": "簡體中文",
        "credits": "創作者：SpaceSquare、Claude Code   ·   擁有者：SpaceSquare",
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
        "press_space": "按空格键开始",
        "game_over": "游戏结束",
        "press_space_restart": "按空格键再玩一次",
        "score": "分数",
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
        "menu_hint": "1-6 选择  |  C 颜色  |  L 语言  |  N 名称  |  ESC 退出",
        "in_game_hint": "M 菜单  |  ESC 退出",
        "color_menu": "选择蛇身颜色",
        "lang_menu": "选择语言",
        "name_menu": "输入你的名称",
        "name_hint": "输入名称，按 ENTER 确认",
        "back_hint": "ESC 返回",
        "level_up": "升级！等级 {lvl}",
        "xp": "经验",
        "english": "英文 English",
        "tchinese": "繁体中文",
        "schinese": "简体中文",
        "credits": "创作者：SpaceSquare、Claude Code   ·   拥有者：SpaceSquare",
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
# AI: Breadth-First Search with a survival fallback
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
    """Return the first step direction of the shortest path start -> goal.

    ``blocked`` is a set of impassable cells. Returns ``None`` if no path
    exists.
    """
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
                # Walk the path back to the cell adjacent to start.
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
        # Never allow a direct reversal.
        if (direction[0] == -current_dir[0] and direction[1] == -current_dir[1]):
            continue
        if not _in_bounds(nxt) or nxt in blocked:
            continue
        score = _flood_free(nxt, blocked)
        if score > best_score:
            best_dir, best_score = direction, score
    return best_dir


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
STATE_COLOR, STATE_LANG, STATE_NAME = range(4, 7)


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

        # Per-round state (initialised in start_round).
        self.snakes = []
        self.food = (0, 0)
        self.obstacles = set()
        self.stage = 1
        self.tick_ms = 120
        self.move_accum = 0.0
        self.result_text = ""
        self.level_up_flash = 0
        self.name_buffer = ""

    # -- Window icon --------------------------------------------------------
    def _set_window_icon(self):
        """Set the window/taskbar icon; ignore if the asset is missing."""
        try:
            icon = pygame.image.load(str(ICON_PATH))
            pygame.display.set_icon(icon)
        except (pygame.error, FileNotFoundError):
            pass

    # -- Fonts --------------------------------------------------------------
    def _load_fonts(self):
        """Load CJK-capable fonts so all three languages render."""
        cjk = "microsoftyaheui,microsoftyahei,microsoftjhenghei,simhei,simsun,notosanscjktc,notosanscjksc,arialunicodems"
        try:
            return {
                "big": pygame.font.SysFont(cjk, 64),
                "mid": pygame.font.SysFont(cjk, 34),
                "small": pygame.font.SysFont(cjk, 22),
                "tiny": pygame.font.SysFont(cjk, 18),
            }
        except Exception:  # pragma: no cover - defensive
            return {
                "big": pygame.font.Font(None, 64),
                "mid": pygame.font.Font(None, 34),
                "small": pygame.font.Font(None, 22),
                "tiny": pygame.font.Font(None, 18),
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
        color = SNAKE_COLORS[self.profile.color_index]
        mid_y = ROWS // 2

        if self.mode in (BATTLE, AI_AI, AI_HUMAN):
            left = Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)
            right = Snake(
                [(COLS - 5, mid_y), (COLS - 4, mid_y), (COLS - 3, mid_y)],
                LEFT, OPPONENT_COLOR,
            )
            if self.mode == BATTLE:
                pass  # both human
            elif self.mode == AI_AI:
                left.is_ai = right.is_ai = True
            elif self.mode == AI_HUMAN:
                right.is_ai = True  # right snake is the AI
            self.snakes = [left, right]
        else:
            self.snakes = [
                Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)
            ]
            if self.mode == LEVEL:
                self._build_stage(self.stage)

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
            AI_AI: 70,
            AI_HUMAN: 90,
        }[self.mode]

    def _occupied(self, extra=()):
        cells = set(self.obstacles)
        for snake in self.snakes:
            cells.update(snake.body)
        cells.update(extra)
        return cells

    def _spawn_food(self):
        free = [
            (x, y)
            for x in range(COLS)
            for y in range(ROWS)
            if (x, y) not in self._occupied()
        ]
        return random.choice(free) if free else (0, 0)

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
        # Never bury the snake's start lane.
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
                blocked = self._blocked_for(snake)
                snake.plan_ai(self.food, blocked)

        for snake in self.snakes:
            if snake.alive:
                snake.step()

        self._resolve_collisions()
        self._resolve_food()
        self._check_round_end()

    def _blocked_for(self, snake):
        """Cells the given AI snake must avoid (walls handled by bounds)."""
        blocked = set(self.obstacles)
        for other in self.snakes:
            if other is snake:
                # Avoid own body except the tail tip (it will move).
                blocked.update(other.body[:-1])
            else:
                blocked.update(other.body)
        return blocked

    def _resolve_collisions(self):
        heads = {}
        for snake in self.snakes:
            if not snake.alive:
                continue
            head = snake.head
            # Wall.
            if not _in_bounds(head) or head in self.obstacles:
                snake.alive = False
                continue
            # Self.
            if head in snake.body[1:]:
                snake.alive = False
                continue
            # Other snakes' bodies.
            for other in self.snakes:
                if other is snake:
                    continue
                if head in other.body:
                    snake.alive = False
                    break
            heads.setdefault(head, []).append(snake)
        # Head-to-head collisions.
        for head, group in heads.items():
            if len(group) > 1:
                for snake in group:
                    snake.alive = False

    def _resolve_food(self):
        for snake in self.snakes:
            if snake.alive and snake.head == self.food:
                snake.grow(1)
                snake.score += 1
                if self.mode == SURVIVAL:
                    # Speed ramps up the longer (and longer) you live.
                    self.tick_ms = max(45, self.tick_ms - 4)
                if self.mode == LEVEL and snake.score % 5 == 0:
                    self.stage += 1
                    self._build_stage(self.stage)
                self.food = self._spawn_food()
                break

    def _check_round_end(self):
        alive = [s for s in self.snakes if s.alive]
        if self.mode in (CLASSIC, SURVIVAL, LEVEL):
            if not alive:
                self._end_round(self.snakes[0].score)
        else:
            # Two-snake modes end when fewer than two remain.
            if len(alive) <= 1:
                self._finish_versus(alive)

    def _finish_versus(self, alive):
        if len(alive) == 1:
            winner = alive[0]
            name = self._snake_label(self.snakes.index(winner))
            self.result_text = self.t("winner", name=name)
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

    # -- Input --------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type != pygame.KEYDOWN:
            return

        dispatch = {
            STATE_MENU: self._key_menu,
            STATE_READY: self._key_ready,
            STATE_PLAY: self._key_play,
            STATE_OVER: self._key_over,
            STATE_COLOR: self._key_color,
            STATE_LANG: self._key_lang,
            STATE_NAME: self._key_name,
        }
        dispatch[self.state](event)

    def _key_menu(self, event):
        key = event.key
        if pygame.K_1 <= key <= pygame.K_6:
            self.mode = key - pygame.K_1
            self.start_round()
        elif key == pygame.K_c:
            self.state = STATE_COLOR
        elif key == pygame.K_l:
            self.state = STATE_LANG
        elif key == pygame.K_n:
            self.name_buffer = self.profile.name
            self.state = STATE_NAME
        elif key == pygame.K_ESCAPE:
            self.running = False

    def _key_ready(self, event):
        if event.key == pygame.K_SPACE:
            self.state = STATE_PLAY
        elif event.key == pygame.K_ESCAPE:
            self.state = STATE_MENU
        elif event.key == pygame.K_m:
            self.state = STATE_MENU

    def _key_play(self, event):
        key = event.key
        if key == pygame.K_m:
            self.state = STATE_MENU
            return
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        # Player 1 / single-player: WASD. Player 2 / single: arrows.
        p1 = self.snakes[0] if self.snakes else None
        # In AI vs Human, the human is the *left* snake (index 0) on WASD.
        if p1 and not p1.is_ai:
            if key in (pygame.K_w,):
                p1.set_direction(UP)
            elif key == pygame.K_s:
                p1.set_direction(DOWN)
            elif key == pygame.K_a:
                p1.set_direction(LEFT)
            elif key == pygame.K_d:
                p1.set_direction(RIGHT)

        # Single-player snakes may also use arrow keys.
        if len(self.snakes) == 1:
            if key == pygame.K_UP:
                p1.set_direction(UP)
            elif key == pygame.K_DOWN:
                p1.set_direction(DOWN)
            elif key == pygame.K_LEFT:
                p1.set_direction(LEFT)
            elif key == pygame.K_RIGHT:
                p1.set_direction(RIGHT)
        elif self.mode == BATTLE and len(self.snakes) > 1:
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
            self.state = STATE_MENU
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
            self.state = STATE_MENU
        elif pygame.K_1 <= event.key <= pygame.K_3:
            self.profile.language = LANG_ORDER[event.key - pygame.K_1]
            save_profile(self.profile)

    def _key_name(self, event):
        if event.key == pygame.K_RETURN:
            self.profile.name = self.name_buffer.strip() or "Player"
            save_profile(self.profile)
            self.state = STATE_MENU
        elif event.key == pygame.K_ESCAPE:
            self.state = STATE_MENU
        elif event.key == pygame.K_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]
        else:
            char = event.unicode
            if char and char.isprintable() and len(self.name_buffer) < 14:
                self.name_buffer += char

    # -- Rendering ----------------------------------------------------------
    def draw(self):
        self.screen.fill(BLACK)
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_COLOR:
            self._draw_color_menu()
        elif self.state == STATE_LANG:
            self._draw_lang_menu()
        elif self.state == STATE_NAME:
            self._draw_name_menu()
        else:
            self._draw_play_area()
            self._draw_hud()
            if self.state == STATE_READY:
                self._draw_center_banner(self.t("press_space"))
            elif self.state == STATE_OVER:
                self._draw_game_over()
        pygame.display.flip()

    def _text(self, key_or_str, font, color, center=None, topleft=None, **kw):
        text = self.t(key_or_str, **kw) if key_or_str in TRANSLATIONS["en"] else key_or_str
        surf = self.fonts[font].render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = center
        elif topleft:
            rect.topleft = topleft
        self.screen.blit(surf, rect)
        return rect

    def _draw_menu(self):
        self._text("title", "big", ACCENT, center=(WIDTH // 2, 84))
        self._text("subtitle", "small", GREY, center=(WIDTH // 2, 132))
        self._text("credits", "tiny", (110, 110, 122), center=(WIDTH // 2, 162))

        start_y = 200
        for i, key in enumerate(MODE_KEYS):
            label = f"{i + 1}.  {self.t(key)}"
            best = self.profile.highscores.get(key, 0)
            row = self._text(label, "mid", WHITE, topleft=(WIDTH // 2 - 200, start_y + i * 50))
            self._text(
                f"{self.t('high')}: {best}", "small", GREY,
                topleft=(WIDTH // 2 + 110, start_y + i * 50 + 8),
            )

        # Profile strip.
        prof = self.profile
        info = f"{prof.name}   {self.t('level_label')} {prof.level}   {self.t('xp')} {prof.xp}/{Profile.xp_for_level(prof.level)}"
        self._text(info, "small", ACCENT, center=(WIDTH // 2, HEIGHT - 70))
        # Color swatch.
        swatch = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 58, 18, 18)
        pygame.draw.rect(self.screen, SNAKE_COLORS[prof.color_index], swatch, border_radius=4)
        self._text("menu_hint", "tiny", GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_color_menu(self):
        self._text("color_menu", "mid", ACCENT, center=(WIDTH // 2, 90))
        cols = 3
        size = 80
        gap = 30
        total_w = cols * size + (cols - 1) * gap
        start_x = (WIDTH - total_w) // 2
        start_y = 170
        for i, color in enumerate(SNAKE_COLORS):
            cx = start_x + (i % cols) * (size + gap)
            cy = start_y + (i // cols) * (size + gap)
            rect = pygame.Rect(cx, cy, size, size)
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            if i == self.profile.color_index:
                pygame.draw.rect(self.screen, WHITE, rect.inflate(10, 10), 3, border_radius=12)
            self._text(str(i + 1), "small", BLACK, center=rect.center)
        self._text("back_hint", "tiny", GREY, center=(WIDTH // 2, HEIGHT - 40))

    def _draw_lang_menu(self):
        self._text("lang_menu", "mid", ACCENT, center=(WIDTH // 2, 110))
        options = [("english", "en"), ("tchinese", "zh_tw"), ("schinese", "zh_cn")]
        for i, (label_key, code) in enumerate(options):
            selected = self.profile.language == code
            color = ACCENT if selected else WHITE
            marker = "> " if selected else "  "
            self._text(f"{i + 1}.  {marker}{self.t(label_key)}", "mid", color,
                       center=(WIDTH // 2, 200 + i * 60))
        self._text("back_hint", "tiny", GREY, center=(WIDTH // 2, HEIGHT - 40))

    def _draw_name_menu(self):
        self._text("name_menu", "mid", ACCENT, center=(WIDTH // 2, 130))
        box = pygame.Rect(WIDTH // 2 - 160, 200, 320, 56)
        pygame.draw.rect(self.screen, DARK, box, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT, box, 2, border_radius=8)
        cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " "
        self._text(self.name_buffer + cursor, "mid", WHITE, center=box.center)
        self._text("name_hint", "small", GREY, center=(WIDTH // 2, 300))
        self._text("back_hint", "tiny", GREY, center=(WIDTH // 2, HEIGHT - 40))

    def _draw_play_area(self):
        # Grid background.
        play_rect = pygame.Rect(0, HUD_HEIGHT, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, DARK, play_rect)
        for x in range(COLS + 1):
            px = x * CELL
            pygame.draw.line(self.screen, GRID_LINE, (px, HUD_HEIGHT), (px, HEIGHT))
        for y in range(ROWS + 1):
            py = HUD_HEIGHT + y * CELL
            pygame.draw.line(self.screen, GRID_LINE, (0, py), (PLAY_WIDTH, py))

        # Obstacles.
        for (ox, oy) in self.obstacles:
            self._cell_rect(ox, oy, fill=(70, 70, 86), inset=1, radius=4)

        # Food.
        fx, fy = self.food
        self._cell_rect(fx, fy, fill=FOOD_COLOR, inset=5, radius=8)

        # Snakes.
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
            HUD_HEIGHT + y * CELL + inset,
            CELL - inset * 2,
            CELL - inset * 2,
        )
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)

    def _draw_hud(self):
        bar = pygame.Rect(0, 0, WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.screen, BLACK, bar)
        pygame.draw.line(self.screen, GRID_LINE, (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT))

        self._text(self.t(MODE_KEYS[self.mode]), "small", ACCENT, topleft=(16, 10))

        if self.mode in (CLASSIC, SURVIVAL, LEVEL):
            score = self.snakes[0].score
            self._text(f"{self.t('score')}: {score}", "small", WHITE, topleft=(16, 34))
            best = self.profile.highscores[MODE_KEYS[self.mode]]
            self._text(f"{self.t('high')}: {best}", "small", GREY, topleft=(180, 34))
            if self.mode == LEVEL:
                self._text(f"{self.t('stage')}: {self.stage}", "small", WHITE,
                           topleft=(320, 34))
        else:
            parts = []
            for i, snake in enumerate(self.snakes):
                parts.append(f"{self._snake_label(i)}: {snake.score}")
            self._text("   ".join(parts), "small", WHITE, topleft=(16, 34))

        self._text("in_game_hint", "tiny", GREY, topleft=(WIDTH - 220, 14))

    def _draw_center_banner(self, text):
        overlay = pygame.Surface((WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, HUD_HEIGHT))
        self._text(text, "mid", WHITE, center=(WIDTH // 2, HEIGHT // 2))

    def _draw_game_over(self):
        overlay = pygame.Surface((WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, HUD_HEIGHT))
        cy = HUD_HEIGHT + PLAY_HEIGHT // 2
        self._text("game_over", "big", RED, center=(WIDTH // 2, cy - 70))
        if self.result_text:
            self._text(self.result_text, "mid", WHITE, center=(WIDTH // 2, cy - 10))
        self._text("press_space_restart", "small", GREY, center=(WIDTH // 2, cy + 50))
        if self.level_up_flash > 0:
            self._text(self.t("level_up", lvl=self.profile.level), "small", ACCENT,
                       center=(WIDTH // 2, cy + 90))

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
