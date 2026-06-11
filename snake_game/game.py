"""The SnakeGame controller: state, input, round/replay/tutorial logic."""
import random
import threading
import time

import pygame

from .config import *  # geometry, mode/state enums, input constants
from .theme import apply_theme, THEME_ORDER, SNAKE_COLORS, OPPONENT_COLOR
from .i18n import TRANSLATIONS, LANG_ORDER
from .version import APP_VERSION, fetch_latest_version, parse_version
from .profile import load_profile, save_profile
from .audio import SoundManager
from .entities import Snake
from .ai import (
    build_hamiltonian_cycle, _in_bounds,
    bfs_direction, survival_direction,
    greedy_direction, astar_direction, anneal_direction,
    drift_direction, minimax_direction,
)
from .render import RenderMixin


class SnakeGame(RenderMixin):
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

        # Tutorial state.
        self.tut_step = 0
        self.tut_eaten = 0
        self.tut_moved = False

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
            elif self.mode == AI_MINIMAX:
                right.is_ai = True  # human on the left, Minimax hunter on the right
                right.brain = "minimax"
            elif self.mode == AI_MINIMAX_DUEL:
                left.is_ai = right.is_ai = True
                left.brain = "minimax"   # the hunter boxes the rival in
                right.brain = "survive"  # the runner just maximises its space
            elif self.mode == AI_FOOD_RUSH:
                left.is_ai = right.is_ai = True
                left.brain = right.brain = "astar"  # both race for the same apple
            self.snakes = [left, right]
        elif self.mode == AI_FILL:
            seq, nxt = build_hamiltonian_cycle(COLS, ROWS)
            snake = Snake([seq[0]], RIGHT, color, is_ai=True)
            snake.cycle = nxt
            self.snakes = [snake]
        elif self.mode == AI_COOP_FILL:
            # Two AI snakes split the board: each follows a perfect-fill cycle
            # over its own half, so together they paint every cell, collision-free.
            half = COLS // 2
            seq, nxt = build_hamiltonian_cycle(half, ROWS)
            left = Snake([seq[0]], RIGHT, color, is_ai=True)
            left.cycle = nxt
            right_cycle = {(x + half, y): (nx + half, ny)
                           for (x, y), (nx, ny) in nxt.items()}
            right = Snake([(seq[0][0] + half, seq[0][1])], RIGHT,
                          OPPONENT_COLOR, is_ai=True)
            right.cycle = right_cycle
            self.snakes = [left, right]
        elif self.mode == PLAYER_FILL:
            self.snakes = [Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)]
        elif self.mode in SOLO_AI_MODES:
            brain = {AI_ASTAR: "astar", AI_ANNEAL: "anneal",
                     AI_GREEDY: "greedy", AI_DRIFT: "drift"}[self.mode]
            snake = Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color, is_ai=True)
            snake.brain = brain
            self.snakes = [snake]
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
            AI_ASTAR: 75,
            AI_ANNEAL: 80,
            AI_GREEDY: 70,
            AI_DRIFT: 90,
            AI_MINIMAX: 100,
            AI_MINIMAX_DUEL: 85,
            AI_COOP_FILL: 32,
            AI_FOOD_RUSH: 75,
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

    # -- Tutorial -----------------------------------------------------------
    TUT_GOAL = 3  # apples to eat in the "eat" step

    def start_tutorial(self):
        self.mode = CLASSIC
        self.replaying = False
        self.recording = None
        self.rng = random.Random()
        self.obstacles = set()
        self.tut_step = 0
        self.tut_eaten = 0
        self.tut_moved = False
        mid_y = ROWS // 2
        color = SNAKE_COLORS[self.profile.color_index]
        self.snakes = [Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)]
        self.food = self._spawn_food()
        self.tick_ms = 140
        self.move_accum = 0.0
        self.state = STATE_TUTORIAL

    def _tutorial_respawn(self):
        mid_y = ROWS // 2
        color = SNAKE_COLORS[self.profile.color_index]
        self.snakes = [Snake([(4, mid_y), (3, mid_y), (2, mid_y)], RIGHT, color)]
        self.food = self._spawn_food()

    def _tutorial_advance(self):
        snake = self.snakes[0]
        snake.step()
        head = snake.head
        if not _in_bounds(head) or head in snake.body[1:]:
            self.sound.play("crash")
            self._tutorial_respawn()  # forgiving: beginners just restart
            return
        if self.food and head == self.food:
            snake.grow(1)
            self.tut_eaten += 1
            self.sound.play("eat")
            self.food = self._spawn_food()
        if self.tut_step == 1 and self.tut_eaten >= self.TUT_GOAL:
            self.tut_step = 2

    def _tutorial_input(self, direction):
        self.snakes[0].set_direction(direction)
        if self.tut_step == 0:
            self.tut_step = 1  # first move advances past the "move" step
            self.tut_moved = True

    # -- Update -------------------------------------------------------------
    def update(self, dt):
        if self.state == STATE_TUTORIAL:
            self.move_accum += dt
            if self.move_accum >= self.tick_ms:
                self.move_accum -= self.tick_ms
                self._tutorial_advance()
            return
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
                self._plan_ai_snake(snake)

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
        # In fill modes the snake grows every tick, so no tail tip frees up.
        own_recedes = self.mode not in FILL_MODES
        for other in self.snakes:
            if other is snake and own_recedes:
                blocked.update(other.body[:-1])  # own tail tip will move
            else:
                blocked.update(other.body)
        return blocked

    def _opponent_of(self, snake):
        """The other live snake (for adversarial planning), or None."""
        for other in self.snakes:
            if other is not snake and other.alive:
                return other
        return None

    def _plan_ai_snake(self, snake):
        """Steer one AI snake using whichever brain it was assigned."""
        if snake.cycle is not None:          # AI Fill: follow the perfect cycle
            snake.plan_cycle()
            return
        blocked = self._blocked_for(snake)
        head, cur, length = snake.head, snake.direction, len(snake.body)
        brain = snake.brain
        if brain == "greedy":
            direction = greedy_direction(head, self.food, blocked, cur)
        elif brain == "astar":
            direction = astar_direction(head, self.food, blocked, cur, length)
        elif brain == "anneal":
            direction = anneal_direction(head, self.food, blocked, cur, self.rng, length)
        elif brain == "drift":
            direction = drift_direction(head, blocked, cur, self.rng)
        elif brain == "survive":
            direction = survival_direction(head, blocked, cur)
        elif brain == "minimax":
            opp = self._opponent_of(snake)
            direction = minimax_direction(snake, opp, self.food, self.obstacles) if opp else None
            if direction is None:
                direction = survival_direction(head, blocked, cur)
        else:  # "bfs" — shortest path, anti-trap fallback
            direction = bfs_direction(head, self.food, blocked)
            if direction is None:
                direction = survival_direction(head, blocked, cur)
        if direction is not None:
            snake.set_direction(direction)

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
            # Single- or co-op fill: count every painted cell across all snakes.
            filled = sum(len(s.body) for s in self.snakes)
            if filled >= total:
                self.win = True
                self.result_text = self.t("board_filled", n=filled)
                self._end_round(filled)
            elif not any(s.alive for s in self.snakes):
                self._end_round(filled)
            return

        alive = [s for s in self.snakes if s.alive]
        if self.mode == AI_FOOD_RUSH:
            if any(s.score >= RUSH_TARGET for s in self.snakes) or len(alive) <= 1:
                self._finish_rush()
        elif self.mode in TWO_SNAKE_MODES:
            if len(alive) <= 1:
                self._finish_versus(alive)
        else:  # CLASSIC, SURVIVAL, LEVEL
            if not alive:
                self._end_round(self.snakes[0].score)

    def _finish_rush(self):
        """Food Rush ends when an AI hits the target or only one is left."""
        best = max(self.snakes, key=lambda s: (s.score, s.alive))
        name = self._snake_label(self.snakes.index(best))
        self.result_text = self.t("winner", name=name)
        self.win = False  # both racers are AI
        self._end_round(best.score)

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
        if self.mode in (AI_AI, AI_MINIMAX_DUEL, AI_FOOD_RUSH):
            return f"{self.t('ai')} {index + 1}"
        if self.mode in (AI_HUMAN, AI_MINIMAX):
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
            STATE_TUTORIAL: self._key_tutorial,
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
        if action == "start_tutorial":
            self.start_tutorial(); return
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
            if self.state == STATE_TUTORIAL:
                self._tutorial_input(arg)
                return
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
        elif key == pygame.K_t:
            self.start_tutorial()
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

    def _key_tutorial(self, event):
        key = event.key
        if key in (pygame.K_ESCAPE, pygame.K_m):
            self.state = STATE_MENU
            return
        if key == pygame.K_SPACE:
            # SPACE advances the two informational steps.
            if self.tut_step == 2:
                self.tut_step = 3
            elif self.tut_step == 3:
                self.state = STATE_MENU
            return
        # Movement: remappable keymap + arrows both work.
        direction = None
        for d in MOVE_DIRS:
            if key == self.profile.keymap[d]:
                direction = DIR_VECTORS[d]
                break
        if direction is None:
            arrows = {pygame.K_UP: UP, pygame.K_DOWN: DOWN,
                      pygame.K_LEFT: LEFT, pygame.K_RIGHT: RIGHT}
            direction = arrows.get(key)
        if direction is not None:
            self._tutorial_input(direction)

    def _key_ai_menu(self, event):
        key = event.key
        idx = None
        if pygame.K_1 <= key <= pygame.K_9:
            idx = key - pygame.K_1
        elif key == pygame.K_0:
            idx = 9  # the tenth entry
        if idx is not None and idx < len(AI_MENU_MODES):
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
