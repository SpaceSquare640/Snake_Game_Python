"""Persistent player profile and settings (snake_save.json)."""
import json
from dataclasses import dataclass, field

from .config import (
    MODE_KEYS, SAVE_PATH, LEADERBOARD_SIZE, REPLAY_LIMIT, MOVE_DIRS,
    DEFAULT_KEYMAP,
)
from .theme import SNAKE_COLORS, THEMES
from .i18n import TRANSLATIONS


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
