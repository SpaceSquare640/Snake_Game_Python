"""All drawing for SnakeGame, mixed in via RenderMixin.

This is the only module that reads the live theme palette; it does so via
``theme.<NAME>`` so a runtime theme switch (which reassigns those globals)
recolors the whole UI without rebinding.
"""
import pygame

from . import theme
from .config import *  # geometry, mode/state enums, input constants
from .theme import SNAKE_COLORS, BTN_RADIUS, THEME_ORDER, THEMES
from .i18n import key_label
from .profile import Profile
from .version import APP_VERSION


class RenderMixin:
    """Drawing methods for :class:`SnakeGame` (operate on ``self``)."""

    def draw(self):
        self.buttons = []
        self.screen.fill(theme.BLACK)
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
        elif self.state == STATE_TUTORIAL:
            self._draw_play_area()
            self._draw_tutorial_hud()
            self._draw_control_bar()
            self._draw_tutorial_banner()
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
        self._text(f"{fps} FPS", "tiny", theme.DIM, topleft=(12, HEIGHT - 24))

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
        self._text(str(text), "tiny", theme.ACCENT if active else theme.DIM,
                   topleft=(rect.x + 11, rect.y + 8))

    def _button(self, rect, label, action, arg=None, font="small",
                selected=False, swatch=None, radius=BTN_RADIUS, badge=None):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        pressed = self.mouse_down == (action, arg) and hover
        if hover and not selected and not pressed:
            self._glow(rect, theme.ACCENT, radius)
        if pressed:
            fill = theme.ACCENT_DEEP
        elif selected:
            fill = theme.ACCENT
        elif hover:
            fill = theme.PANEL_HOVER
        else:
            fill = theme.PANEL
        active = hover or selected or pressed
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        pygame.draw.rect(self.screen, theme.ACCENT if active else theme.BORDER, rect,
                         2 if active else 1, border_radius=radius)
        txt_color = theme.BLACK if selected else theme.WHITE
        cx = rect.centerx
        if swatch is not None:
            sw = pygame.Rect(rect.x + 16, rect.centery - 10, 20, 20)
            pygame.draw.rect(self.screen, swatch, sw, border_radius=6)
            pygame.draw.rect(self.screen, theme.BORDER, sw, 1, border_radius=6)
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
            self._glow(rect, theme.ACCENT, BTN_RADIUS)
        active = hover or pressed
        pygame.draw.rect(self.screen, theme.ACCENT_DEEP if pressed else (theme.PANEL_HOVER if hover else theme.PANEL),
                         rect, border_radius=BTN_RADIUS)
        pygame.draw.rect(self.screen, theme.ACCENT if active else theme.BORDER, rect,
                         2 if active else 1, border_radius=BTN_RADIUS)
        self._text(self.t(key), "small", theme.WHITE,
                   center=(rect.centerx, rect.centery - 9))
        best = self.profile.highscores.get(key, 0)
        self._text(f"{self.t('high')}: {best}", "tiny", theme.GREY,
                   center=(rect.centerx, rect.centery + 13))
        if badge is not None:
            self._draw_badge(rect, badge, active)
        self.buttons.append({"rect": rect, "action": "start_mode", "arg": mode})

    # -- Menus --------------------------------------------------------------
    def _draw_menu(self):
        # Bold title; credits dimmed to keep focus on the buttons below.
        self._text(self.t("title"), "title", theme.ACCENT, center=(WIDTH // 2, 102))
        self._text(self.t("credits"), "tiny", theme.DIM, center=(WIDTH // 2, 144))

        # Small version / update status pinned to the top-right corner.
        self._draw_status_corner()

        # Wider side margins so nothing hugs the edges.
        margin, gap = 50, 22
        bw = (WIDTH - 2 * margin - gap) // 2
        bh, srow_h, trow_h = 64, 54, 42
        block_h = 3 * bh + 2 * gap + 28 + srow_h + 16 + trow_h
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

        # Slim full-width tutorial row for newcomers.
        tut_y = row_y + srow_h + 16
        self._button(pygame.Rect(start_x, tut_y, WIDTH - 2 * margin, trow_h),
                     self.t("tutorial_btn"), "start_tutorial", font="tiny", badge="T")

        # A thin separator divides the menu from the profile card.
        card_top = HEIGHT - 100
        sep_y = card_top - 22
        pygame.draw.line(self.screen, theme.DIVIDER,
                         (margin + 40, sep_y), (WIDTH - margin - 40, sep_y))
        self._draw_profile_card(card_top)
        self._text(self.t("menu_hint"), "tiny", theme.DIM, center=(WIDTH // 2, HEIGHT - 28))

    def _draw_status_corner(self):
        """Compact version + colored status dot in the top-right corner."""
        dot_colors = {"checking": theme.GREY, "latest": theme.ACCENT, "outdated": theme.GOLD,
                      "unknown": theme.DIM}
        dot = dot_colors.get(self.update_state, theme.DIM)
        if self.update_state == "outdated" and self.latest_version:
            label = f"v{APP_VERSION} → {self.latest_version}"
            text_color = theme.GOLD
        else:
            label = f"v{APP_VERSION}"
            text_color = theme.GREY
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
        pygame.draw.rect(self.screen, theme.PANEL, card, border_radius=BTN_RADIUS)
        pygame.draw.rect(self.screen, theme.BORDER, card, 1, border_radius=BTN_RADIUS)

        # Unequal segments: the name needs the most room.
        d1 = card.x + 214          # name | level divider
        d2 = card.x + 332          # level | xp divider
        for x in (d1, d2):
            pygame.draw.line(self.screen, theme.DIVIDER, (x, card.y + 11), (x, card.bottom - 11))

        # Segment 1: color swatch + name.
        sw = pygame.Rect(card.x + 18, card.centery - 10, 20, 20)
        pygame.draw.rect(self.screen, SNAKE_COLORS[prof.color_index], sw, border_radius=6)
        pygame.draw.rect(self.screen, theme.BORDER, sw, 1, border_radius=6)
        self._text(prof.name, "small", theme.WHITE, topleft=(sw.right + 12, card.centery - 13))

        # Segment 2: level (accent).
        self._text(f"{self.t('level_label')} {prof.level}", "small", theme.ACCENT,
                   center=((d1 + d2) // 2, card.centery))

        # Segment 3: XP progress.
        self._text(f"{self.t('xp')} {prof.xp}/{Profile.xp_for_level(prof.level)}",
                   "small", theme.GREY, center=((d2 + card.right) // 2, card.centery))

    def _draw_settings(self):
        self._text(self.t("settings_title"), "big", theme.ACCENT, center=(WIDTH // 2, 78))
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
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_theme_menu(self):
        self._text(self.t("theme_menu"), "big", theme.ACCENT, center=(WIDTH // 2, 90))
        bw, bh = 380, 60
        x = (WIDTH - bw) // 2
        for i, name in enumerate(THEME_ORDER):
            sw = THEMES[name]["accent"]
            self._button(pygame.Rect(x, 180 + i * (bh + 18), bw, bh),
                         f"{self.t('theme_' + name)}", "set_theme", name,
                         selected=(self.profile.theme == name), swatch=sw, badge=i + 1)
        self._button(pygame.Rect(x, 180 + 4 * (bh + 18) + 8, bw, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_audio_menu(self):
        self._text(self.t("audio_menu"), "big", theme.ACCENT, center=(WIDTH // 2, 100))
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
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_controls_menu(self):
        self._text(self.t("controls_menu"), "big", theme.ACCENT, center=(WIDTH // 2, 90))
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
        self._text(self.t("rebind_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_rebind(self):
        # Keep the controls list visible, dimmed, with a capture prompt over it.
        self._draw_controls_menu()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        d = self.rebind_dir or "up"
        self._text(self.t("dir_" + d), "mid", theme.ACCENT, center=(WIDTH // 2, HEIGHT // 2 - 30))
        self._text(self.t("press_key"), "big", theme.WHITE, center=(WIDTH // 2, HEIGHT // 2 + 30))

    def _draw_leaderboard(self):
        self._text(self.t("leaderboard_title"), "big", theme.ACCENT, center=(WIDTH // 2, 64))
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
            pygame.draw.rect(self.screen, theme.PANEL, panel, border_radius=10)
            pygame.draw.rect(self.screen, theme.BORDER, panel, 1, border_radius=10)
            self._text(self.t(key), "small", theme.ACCENT, topleft=(bx + 12, by + 8))
            board = self.profile.leaderboards.get(key, [])
            if not board:
                self._text(self.t("empty_board"), "tiny", theme.DIM, topleft=(bx + 12, by + 38))
            for r, entry in enumerate(board):
                line = f"{r + 1}. {entry['name'][:9]:<9}  {entry['score']}"
                self._text(line, "tiny", theme.WHITE if r == 0 else theme.GREY,
                           topleft=(bx + 12, by + 36 + r * 14))
        self._button(pygame.Rect(WIDTH // 2 - 90, HEIGHT - 86, 180, 48),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 28))

    def _draw_ai_menu(self):
        self._text(self.t("ai_menu_title"), "big", theme.ACCENT, center=(WIDTH // 2, 90))
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
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 36))

    def _draw_color_menu(self):
        self._text(self.t("color_menu"), "mid", theme.ACCENT, center=(WIDTH // 2, 70))
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
                self._glow(rect, theme.ACCENT, 12)
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            if selected:
                pygame.draw.rect(self.screen, theme.ACCENT, rect.inflate(10, 10), 3, border_radius=14)
            self._text(str(i + 1), "small", theme.BLACK, center=rect.center)
            self.buttons.append({"rect": rect, "action": "set_color", "arg": i})
        self._button(pygame.Rect(WIDTH // 2 - 90, HEIGHT - 90, 180, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 28))

    def _draw_lang_menu(self):
        self._text(self.t("lang_menu"), "mid", theme.ACCENT, center=(WIDTH // 2, 90))
        options = [("english", "en"), ("tchinese", "zh_tw"), ("schinese", "zh_cn")]
        bw, bh = 360, 60
        x = (WIDTH - bw) // 2
        for i, (label_key, code) in enumerate(options):
            rect = pygame.Rect(x, 180 + i * (bh + 18), bw, bh)
            self._button(rect, f"{i + 1}.  {self.t(label_key)}", "set_lang", code,
                         selected=(self.profile.language == code))
        self._button(pygame.Rect(x, 180 + 3 * (bh + 18) + 10, bw, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_name_menu(self):
        self._text(self.t("name_menu"), "mid", theme.ACCENT, center=(WIDTH // 2, 110))
        box = pygame.Rect(WIDTH // 2 - 160, 190, 320, 56)
        pygame.draw.rect(self.screen, theme.DARK, box, border_radius=8)
        pygame.draw.rect(self.screen, theme.ACCENT, box, 2, border_radius=8)
        cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " "
        self._text(self.name_buffer + cursor, "mid", theme.WHITE, center=box.center)
        self._text(self.t("name_hint"), "small", theme.GREY, center=(WIDTH // 2, 290))
        self._button(pygame.Rect(WIDTH // 2 - 90, 340, 180, 50),
                     self.t("back"), "sub_back")
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 30))

    def _draw_replays(self):
        self._text(self.t("replays_title"), "big", theme.ACCENT, center=(WIDTH // 2, 70))
        replays = self.profile.replays
        if not replays:
            self._text(self.t("no_replays"), "small", theme.DIM, center=(WIDTH // 2, HEIGHT // 2))
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
        self._text(self.t("back_hint"), "tiny", theme.GREY, center=(WIDTH // 2, HEIGHT - 24))

    # -- Play area ----------------------------------------------------------
    def _draw_play_area(self):
        play_rect = pygame.Rect(0, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, theme.DARK, play_rect)
        for x in range(COLS + 1):
            px = x * CELL
            pygame.draw.line(self.screen, theme.GRID_LINE, (px, PLAY_TOP), (px, CONTROL_TOP))
        for y in range(ROWS + 1):
            py = PLAY_TOP + y * CELL
            pygame.draw.line(self.screen, theme.GRID_LINE, (0, py), (PLAY_WIDTH, py))

        for (ox, oy) in self.obstacles:
            self._cell_rect(ox, oy, fill=theme.OBSTACLE, inset=1, radius=4)

        if self.food is not None:
            fx, fy = self.food
            self._cell_rect(fx, fy, fill=theme.FOOD_COLOR, inset=5, radius=8)

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
        pygame.draw.rect(self.screen, theme.BLACK, bar)
        pygame.draw.line(self.screen, theme.GRID_LINE, (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT))
        self._text(self.t(MODE_KEYS[self.mode]), "small", theme.ACCENT, topleft=(16, 10))
        if self.replaying:  # REPLAY badge, top-right of the HUD
            self._text(self.t("replay_label"), "small", theme.GOLD, topleft=(WIDTH - 110, 10))

        if self.mode in FILL_MODES:
            filled = len(self.snakes[0].body)
            self._text(f"{self.t('filled')}: {filled} / {COLS * ROWS}", "small",
                       theme.WHITE, topleft=(16, 34))
            best = self.profile.highscores[MODE_KEYS[self.mode]]
            self._text(f"{self.t('high')}: {best}", "small", theme.GREY, topleft=(280, 34))
        elif self.mode in TWO_SNAKE_MODES:
            parts = [f"{self._snake_label(i)}: {s.score}" for i, s in enumerate(self.snakes)]
            self._text("   ".join(parts), "small", theme.WHITE, topleft=(16, 34))
        else:
            score = self.snakes[0].score
            self._text(f"{self.t('score')}: {score}", "small", theme.WHITE, topleft=(16, 34))
            best = self.profile.highscores[MODE_KEYS[self.mode]]
            self._text(f"{self.t('high')}: {best}", "small", theme.GREY, topleft=(180, 34))
            if self.mode == LEVEL:
                self._text(f"{self.t('stage')}: {self.stage}", "small", theme.WHITE,
                           topleft=(320, 34))

    def _draw_tutorial_hud(self):
        bar = pygame.Rect(0, 0, WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.screen, theme.BLACK, bar)
        pygame.draw.line(self.screen, theme.GRID_LINE, (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT))
        self._text(self.t("tut_title"), "small", theme.ACCENT, topleft=(16, 10))
        if self.tut_step == 1:
            remaining = max(0, self.TUT_GOAL - self.tut_eaten)
            self._text(self.t("tut_eat", n=remaining), "small", theme.WHITE, topleft=(16, 34))
        self._text(self.t("tut_skip"), "tiny", theme.DIM, topleft=(WIDTH - 180, 14))

    def _draw_tutorial_banner(self):
        """Step-driven instruction strip across the top of the play field."""
        if self.tut_step == 0:
            lines = [self.t("tut_move")]
        elif self.tut_step == 1:
            remaining = max(0, self.TUT_GOAL - self.tut_eaten)
            lines = [self.t("tut_eat", n=remaining)]
        elif self.tut_step == 2:
            lines = [self.t("tut_avoid"), self.t("tut_continue")]
        else:
            lines = [self.t("tut_done"), self.t("tut_continue")]
        strip_h = 46 + 28 * (len(lines) - 1)
        strip = pygame.Rect(20, PLAY_TOP + 14, WIDTH - 40, strip_h)
        overlay = pygame.Surface((strip.w, strip.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, strip.topleft)
        pygame.draw.rect(self.screen, theme.ACCENT, strip, 1, border_radius=10)
        for i, line in enumerate(lines):
            color = theme.WHITE if i == 0 else theme.GREY
            self._text(line, "small", color,
                       center=(strip.centerx, strip.y + 24 + i * 28))

    # -- On-screen control bar (D-pad + Menu) ------------------------------
    def _draw_control_bar(self):
        bar = pygame.Rect(0, CONTROL_TOP, WIDTH, CONTROL_HEIGHT)
        pygame.draw.rect(self.screen, theme.BLACK, bar)
        pygame.draw.line(self.screen, theme.GRID_LINE, (0, CONTROL_TOP), (WIDTH, CONTROL_TOP))

        # Menu button (left).
        self._button(pygame.Rect(20, CONTROL_TOP + 36, 130, 44),
                     self.t("menu_btn"), "to_menu")

        # D-pad (right) — only when a human is actively controlling (not replay).
        if (self.state in (STATE_READY, STATE_PLAY, STATE_TUTORIAL)
                and not self.replaying
                and self._human_snake() is not None):
            self._draw_dpad()
        else:
            note = self.t("replay_label") if self.replaying else self.t("watching")
            self._text(note, "small", theme.GOLD if self.replaying else theme.GREY,
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
                self._glow(rect, theme.ACCENT, 10)
            pygame.draw.rect(self.screen, theme.PANEL_HOVER if hover else theme.PANEL, rect,
                             border_radius=10)
            pygame.draw.rect(self.screen, theme.ACCENT if hover else theme.BORDER, rect,
                             2 if hover else 1, border_radius=10)
            self._draw_arrow(rect, direction, theme.ACCENT if hover else theme.WHITE)
            self.buttons.append({"rect": rect, "action": "dir", "arg": direction})

    def _draw_arrow(self, rect, direction, color=theme.WHITE):
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
        self._text(text, "mid", theme.WHITE, center=(WIDTH // 2, PLAY_TOP + PLAY_HEIGHT // 2))

    def _draw_game_over(self):
        overlay = pygame.Surface((WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, PLAY_TOP))
        cy = PLAY_TOP + PLAY_HEIGHT // 2
        if self.win:
            self._text(self.t("you_win"), "big", theme.GOLD, center=(WIDTH // 2, cy - 80))
        else:
            self._text(self.t("game_over"), "big", theme.RED, center=(WIDTH // 2, cy - 80))
        if self.result_text:
            self._text(self.result_text, "mid", theme.WHITE, center=(WIDTH // 2, cy - 18))
        if self.level_up_flash > 0:
            self._text(self.t("level_up", lvl=self.profile.level), "small", theme.ACCENT,
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
