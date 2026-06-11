"""Color themes and the live palette.

``apply_theme`` reassigns the module-level color globals below; rendering
code reads them as ``theme.<NAME>`` so a theme switch recolors everything.
"""
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
