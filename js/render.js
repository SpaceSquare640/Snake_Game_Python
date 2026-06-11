/* All canvas drawing, as a mixin folded into Game.prototype.
 *
 * Mirrors the Python package's render.py RenderMixin: every method here uses
 * `this` (the Game instance) for state, and reads colors from the live `C`
 * palette so theme switches recolor instantly.
 */
import {
  WIDTH, HEIGHT, PLAY_WIDTH, PLAY_HEIGHT, PLAY_TOP, CONTROL_TOP, CONTROL_HEIGHT,
  HUD_HEIGHT, CELL, COLS, ROWS, UP, DOWN, LEFT, RIGHT, MODE_KEYS, MAIN_MENU_MODES,
  AI_MENU_MODES, FILL_MODES, TWO_SNAKE_MODES, LEVEL, MOVE_DIRS, REPLAY_LIMIT, TUT_GOAL,
  STATE_MENU, STATE_SETTINGS, STATE_AI_MENU, STATE_COLOR, STATE_LANG, STATE_NAME,
  STATE_THEME, STATE_AUDIO, STATE_CONTROLS, STATE_REBIND, STATE_LEADERBOARD,
  STATE_REPLAYS, STATE_TUTORIAL, STATE_READY, STATE_PLAY, STATE_OVER,
} from "./config.js";
import { C, THEMES, THEME_ORDER, SNAKE_COLORS, BTN_RADIUS } from "./theme.js";
import { keyLabel } from "./i18n.js";
import { xpForLevel } from "./profile.js";
import { APP_VERSION } from "./version.js";

function toRGB(color) {
  if (color[0] === "#") {
    const n = parseInt(color.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  const m = color.match(/\d+/g);
  return [parseInt(m[0], 10), parseInt(m[1], 10), parseInt(m[2], 10)];
}

export const RenderMixin = {
  // -- Frame dispatch ---------------------------------------------------
  draw() {
    this.buttons = [];
    const ctx = this.ctx;
    ctx.fillStyle = C.black;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    switch (this.state) {
      case STATE_MENU: this.drawMenu(); break;
      case STATE_SETTINGS: this.drawSettings(); break;
      case STATE_AI_MENU: this.drawAiMenu(); break;
      case STATE_COLOR: this.drawColorMenu(); break;
      case STATE_LANG: this.drawLangMenu(); break;
      case STATE_NAME: this.drawNameMenu(); break;
      case STATE_THEME: this.drawThemeMenu(); break;
      case STATE_AUDIO: this.drawAudioMenu(); break;
      case STATE_CONTROLS: this.drawControlsMenu(); break;
      case STATE_REBIND: this.drawRebind(); break;
      case STATE_LEADERBOARD: this.drawLeaderboard(); break;
      case STATE_REPLAYS: this.drawReplays(); break;
      case STATE_TUTORIAL:
        this.drawPlayArea();
        this.drawTutorialHud();
        this.drawControlBar();
        this.drawTutorialBanner();
        break;
      default:
        this.drawPlayArea();
        this.drawHud();
        this.drawControlBar();
        if (this.state === STATE_READY) this.drawCenterBanner(this.t("press_space"));
        else if (this.state === STATE_OVER) this.drawGameOver();
    }
    if (this.profile.showFps) {
      this.text(Math.round(this.fps || 0) + " FPS", 15, C.dim, 12, HEIGHT - 14, "left");
    }
  },

  // -- Primitives -------------------------------------------------------
  font(size, bold) { return (bold ? "bold " : "") + size + 'px "Segoe UI","Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif'; },

  text(str, size, color, x, y, align = "center", bold = false) {
    const ctx = this.ctx;
    ctx.font = this.font(size, bold);
    ctx.fillStyle = color;
    ctx.textAlign = align;
    ctx.textBaseline = "middle";
    ctx.fillText(str, x, y);
  },

  roundRect(x, y, w, h, r) {
    const ctx = this.ctx;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, w, h, r);
    else {
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }
  },

  hovered(b) {
    return this.pointer.x >= b.x && this.pointer.x <= b.x + b.w &&
           this.pointer.y >= b.y && this.pointer.y <= b.y + b.h;
  },

  button(b) {
    const ctx = this.ctx;
    const hover = this.hovered(b);
    const pressed = this.mouseDown && this.mouseDown[0] === b.action &&
                    this.mouseDown[1] === b.arg && hover;
    const active = hover || b.selected || pressed;
    const r = b.radius || BTN_RADIUS;
    ctx.save();
    if (hover && !b.selected && !pressed) { ctx.shadowColor = C.accent; ctx.shadowBlur = 18; }
    ctx.fillStyle = pressed ? C.accentDeep : (b.selected ? C.accent : (hover ? C.panelHover : C.panel));
    this.roundRect(b.x, b.y, b.w, b.h, r); ctx.fill();
    ctx.restore();
    ctx.lineWidth = active ? 2 : 1;
    ctx.strokeStyle = active ? C.accent : C.border;
    this.roundRect(b.x, b.y, b.w, b.h, r); ctx.stroke();

    let cx = b.x + b.w / 2;
    if (b.swatch) {
      const s = 20;
      ctx.fillStyle = b.swatch;
      this.roundRect(b.x + 16, b.y + b.h / 2 - s / 2, s, s, 6); ctx.fill();
      ctx.strokeStyle = C.border; ctx.lineWidth = 1;
      this.roundRect(b.x + 16, b.y + b.h / 2 - s / 2, s, s, 6); ctx.stroke();
      cx += 16;
    }
    const txtColor = b.selected ? C.black : C.white;
    if (b.sub) {
      this.text(b.label, b.font || 22, txtColor, cx, b.y + b.h / 2 - 9);
      this.text(b.sub, 15, C.grey, cx, b.y + b.h / 2 + 13);
    } else {
      this.text(b.label, b.font || 22, txtColor, cx, b.y + b.h / 2);
    }
    if (b.badge != null) {
      this.text(String(b.badge), 15, active ? C.accent : C.dim, b.x + 11, b.y + 16, "left");
    }
    this.buttons.push(b);
  },

  // -- Menus ------------------------------------------------------------
  drawMenu() {
    this.text(this.t("title"), 60, C.accent, WIDTH / 2, 102, "center", true);
    this.text(this.t("credits"), 15, C.dim, WIDTH / 2, 144);
    this.drawStatusCorner();

    const margin = 50, gap = 22;
    const bw = (WIDTH - 2 * margin - gap) / 2;
    const bh = 64, srowH = 54, trowH = 42;
    const blockH = 3 * bh + 2 * gap + 28 + srowH + 16 + trowH;
    const bandTop = 178, bandBottom = HEIGHT - 134;
    const startX = margin;
    const startY = bandTop + Math.max(0, (bandBottom - bandTop - blockH) / 2);

    MAIN_MENU_MODES.forEach((mode, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = startX + col * (bw + gap), y = startY + row * (bh + gap);
      const k = MODE_KEYS[mode];
      this.button({ x, y, w: bw, h: bh, label: this.t(k),
        sub: this.t("high") + ": " + this.profile.highscores[k],
        action: "start_mode", arg: mode, badge: i + 1 });
    });

    const rowY = startY + 3 * (bh + gap) + 28;
    const ug = 14;
    const tw = (WIDTH - 2 * margin - 3 * ug) / 4;
    const util = [
      [this.t("ai_modes"), "open_ai_menu", "A"],
      [this.t("leaderboard_btn"), "open_leaderboard", null],
      [this.t("replays_btn"), "open_replays", null],
      [this.t("settings"), "open_settings", "S"],
    ];
    util.forEach((u, i) => {
      this.button({ x: startX + i * (tw + ug), y: rowY, w: tw, h: srowH,
        label: u[0], action: u[1], font: 16, badge: u[2] });
    });

    const tutY = rowY + srowH + 16;
    this.button({ x: startX, y: tutY, w: WIDTH - 2 * margin, h: trowH,
      label: this.t("tutorial_btn"), action: "start_tutorial", font: 16, badge: "T" });

    const cardTop = HEIGHT - 100, sepY = cardTop - 22;
    const ctx = this.ctx;
    ctx.strokeStyle = C.divider; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(margin + 40, sepY); ctx.lineTo(WIDTH - margin - 40, sepY); ctx.stroke();
    this.drawProfileCard(cardTop);
    this.text(this.t("menu_hint"), 15, C.dim, WIDTH / 2, HEIGHT - 28);
  },

  drawStatusCorner() {
    const dotColors = { checking: C.grey, latest: C.accent, outdated: C.gold, unknown: C.dim };
    const dot = dotColors[this.updateState] || C.dim;
    let label, color;
    if (this.updateState === "outdated" && this.latestVersion) {
      label = "v" + APP_VERSION + " → " + this.latestVersion; color = C.gold;
    } else { label = "v" + APP_VERSION; color = C.grey; }
    const ctx = this.ctx;
    ctx.font = this.font(15, false);
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    ctx.fillStyle = color;
    ctx.fillText(label, WIDTH - 16, 18);
    const w = ctx.measureText(label).width;
    ctx.beginPath();
    ctx.fillStyle = dot;
    ctx.arc(WIDTH - 16 - w - 10, 19, 4, 0, Math.PI * 2);
    ctx.fill();
  },

  drawProfileCard(top) {
    const ctx = this.ctx;
    const p = this.profile;
    const cardW = 478, cardH = 52;
    const x = (WIDTH - cardW) / 2;
    ctx.fillStyle = C.panel;
    this.roundRect(x, top, cardW, cardH, BTN_RADIUS); ctx.fill();
    ctx.strokeStyle = C.border; ctx.lineWidth = 1;
    this.roundRect(x, top, cardW, cardH, BTN_RADIUS); ctx.stroke();

    const cy = top + cardH / 2;
    const d1 = x + 214, d2 = x + 332;
    ctx.strokeStyle = C.divider; ctx.lineWidth = 1;
    for (const dx of [d1, d2]) {
      ctx.beginPath(); ctx.moveTo(dx, top + 11); ctx.lineTo(dx, top + cardH - 11); ctx.stroke();
    }
    const sw = 20;
    ctx.fillStyle = SNAKE_COLORS[p.colorIndex];
    this.roundRect(x + 18, cy - sw / 2, sw, sw, 6); ctx.fill();
    ctx.strokeStyle = C.border;
    this.roundRect(x + 18, cy - sw / 2, sw, sw, 6); ctx.stroke();
    this.text(p.name, 22, C.white, x + 18 + sw + 12, cy, "left");
    this.text(this.t("level_label") + " " + p.level, 22, C.accent, (d1 + d2) / 2, cy);
    this.text(this.t("xp") + " " + p.xp + "/" + xpForLevel(p.level), 22, C.grey, (d2 + x + cardW) / 2, cy);
  },

  drawSettings() {
    this.text(this.t("settings_title"), 60, C.accent, WIDTH / 2, 78, "center", true);
    const bw = 380, bh = 58, vg = 14, x = (WIDTH - bw) / 2, y0 = 150;
    const langLabel = { en: "English", zh_tw: "繁體中文", zh_cn: "简体中文" }[this.profile.language];
    const themeLabel = this.t("theme_" + this.profile.theme);
    const rows = [
      [this.t("lang_btn") + ":  " + langLabel, "open_lang", null],
      [this.t("color_btn"), "open_color", SNAKE_COLORS[this.profile.colorIndex]],
      [this.t("theme_btn") + ":  " + themeLabel, "open_theme", null],
      [this.t("audio_btn"), "open_audio", null],
      [this.t("controls_btn"), "open_controls", null],
      [this.t("name_btn") + ":  " + this.profile.name, "open_name", null],
    ];
    rows.forEach((r, i) => {
      this.button({ x, y: y0 + i * (bh + vg), w: bw, h: bh, label: r[0],
        action: r[1], swatch: r[2], badge: i + 1 });
    });
    this.button({ x, y: y0 + 6 * (bh + vg) + 6, w: bw, h: 50, label: this.t("back"), action: "back_menu" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  },

  drawThemeMenu() {
    this.text(this.t("theme_menu"), 60, C.accent, WIDTH / 2, 90, "center", true);
    const bw = 380, bh = 60, x = (WIDTH - bw) / 2;
    THEME_ORDER.forEach((name, i) => {
      this.button({ x, y: 180 + i * (bh + 18), w: bw, h: bh, label: this.t("theme_" + name),
        action: "set_theme", arg: name, selected: this.profile.theme === name,
        swatch: THEMES[name].accent, badge: i + 1 });
    });
    this.button({ x, y: 180 + 4 * (bh + 18) + 8, w: bw, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  },

  drawAudioMenu() {
    this.text(this.t("audio_menu"), 60, C.accent, WIDTH / 2, 100, "center", true);
    const bw = 400, bh = 62, x = (WIDTH - bw) / 2;
    const toggles = [
      [this.t("sound_label"), this.profile.sound, "toggle_sound"],
      [this.t("music_label"), this.profile.music, "toggle_music"],
      [this.t("fps_label"), this.profile.showFps, "toggle_fps"],
    ];
    toggles.forEach((tg, i) => {
      const state = tg[1] ? this.t("on") : this.t("off");
      this.button({ x, y: 190 + i * (bh + 18), w: bw, h: bh, label: tg[0] + ":  " + state, action: tg[2], badge: i + 1 });
    });
    this.button({ x, y: 190 + 3 * (bh + 18) + 10, w: bw, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  },

  drawControlsMenu() {
    this.text(this.t("controls_menu"), 60, C.accent, WIDTH / 2, 90, "center", true);
    const bw = 400, bh = 60, x = (WIDTH - bw) / 2;
    MOVE_DIRS.forEach((d, i) => {
      const label = this.t("dir_" + d) + ":  [ " + keyLabel(this.profile.keymap[d]) + " ]";
      this.button({ x, y: 170 + i * (bh + 16), w: bw, h: bh, label, action: "rebind", arg: d, badge: i + 1 });
    });
    const by = 170 + 4 * (bh + 16) + 6;
    this.button({ x, y: by, w: bw / 2 - 6, h: 50, label: this.t("reset_default"), action: "reset_keys", font: 17 });
    this.button({ x: x + bw / 2 + 6, y: by, w: bw / 2 - 6, h: 50, label: this.t("back"), action: "sub_back", font: 17 });
    this.text(this.t("rebind_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  },

  drawRebind() {
    this.drawControlsMenu();
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.72)";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const d = this.rebindDir || "up";
    this.text(this.t("dir_" + d), 32, C.accent, WIDTH / 2, HEIGHT / 2 - 30);
    this.text(this.t("press_key"), 60, C.white, WIDTH / 2, HEIGHT / 2 + 30, "center", true);
  },

  drawLeaderboard() {
    this.text(this.t("leaderboard_title"), 60, C.accent, WIDTH / 2, 50, "center", true);
    // Three compact columns so all 16 modes fit on one screen.
    const margin = 18, gap = 10, cols = 3;
    const colW = (WIDTH - 2 * margin - (cols - 1) * gap) / cols;
    const x0 = margin, y0 = 88, rowH = 104, shown = 3;
    const ctx = this.ctx;
    MODE_KEYS.forEach((k, i) => {
      const col = i % cols, row = Math.floor(i / cols);
      const bx = x0 + col * (colW + gap), by = y0 + row * rowH;
      ctx.fillStyle = C.panel;
      this.roundRect(bx, by, colW, rowH - 12, 10); ctx.fill();
      ctx.strokeStyle = C.border; ctx.lineWidth = 1;
      this.roundRect(bx, by, colW, rowH - 12, 10); ctx.stroke();
      this.text(this.t(k), 15, C.accent, bx + 10, by + 13, "left");
      const board = this.profile.leaderboards[k] || [];
      if (!board.length) this.text(this.t("empty_board"), 15, C.dim, bx + 10, by + 34, "left");
      board.slice(0, shown).forEach((e, r) => {
        const nm = (e.name || "?").slice(0, 7);
        this.text((r + 1) + ". " + nm + " " + e.score, 15, r === 0 ? C.white : C.grey,
          bx + 10, by + 34 + r * 16, "left");
      });
    });
    this.button({ x: WIDTH / 2 - 90, y: HEIGHT - 64, w: 180, h: 44, label: this.t("back"), action: "sub_back", font: 20 });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 14);
  },

  drawReplays() {
    this.text(this.t("replays_title"), 60, C.accent, WIDTH / 2, 70, "center", true);
    const replays = this.profile.replays;
    if (!replays.length) this.text(this.t("no_replays"), 22, C.dim, WIDTH / 2, HEIGHT / 2);
    const bw = 472, bh = 52, x = (WIDTH - bw) / 2;
    replays.slice(0, REPLAY_LIMIT).forEach((rec, i) => {
      const modeName = this.t(MODE_KEYS[rec.mode || 0]);
      const tag = rec.win ? this.t("you_win") : "";
      const label = modeName + "   ·   " + this.t("score") + " " + (rec.score || 0) + "   " + tag;
      this.button({ x, y: 128 + i * (bh + 10), w: bw, h: bh, label, action: "play_replay", arg: i, font: 22 });
    });
    this.button({ x: WIDTH / 2 - 90, y: HEIGHT - 70, w: 180, h: 46, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 24);
  },

  drawAiMenu() {
    this.text(this.t("ai_menu_title"), 60, C.accent, WIDTH / 2, 64, "center", true);
    // Two-column grid with a one-line description under each mode button.
    const margin = 40, gap = 18, cols = 2;
    const bw = (WIDTH - 2 * margin - gap) / cols;
    const bh = 50, descH = 16, vgap = 12, cellH = bh + descH + vgap, y0 = 116;
    const badges = "1234567890";
    AI_MENU_MODES.forEach((mode, i) => {
      const col = i % cols, row = Math.floor(i / cols);
      const x = margin + col * (bw + gap), y = y0 + row * cellH;
      const k = MODE_KEYS[mode];
      this.button({ x, y, w: bw, h: bh, font: 20,
        label: this.t(k) + "   (" + this.t("high") + ": " + this.profile.highscores[k] + ")",
        action: "start_mode", arg: mode, badge: i < badges.length ? badges[i] : null });
      this.text(this.t("desc_" + k), 15, C.dim, x + bw / 2, y + bh + descH / 2 - 1);
    });
    const nrows = Math.ceil(AI_MENU_MODES.length / cols);
    const backY = y0 + nrows * cellH + 6;
    this.button({ x: (WIDTH - 240) / 2, y: backY, w: 240, h: 46, label: this.t("back"), action: "back_menu", font: 20 });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 22);
  },

  drawColorMenu() {
    this.text(this.t("color_menu"), 32, C.accent, WIDTH / 2, 70);
    const ctx = this.ctx;
    const cols = 3, size = 80, gap = 30;
    const totalW = cols * size + (cols - 1) * gap;
    const startX = (WIDTH - totalW) / 2, startY = 130;
    SNAKE_COLORS.forEach((color, i) => {
      const x = startX + (i % cols) * (size + gap);
      const y = startY + Math.floor(i / cols) * (size + gap);
      const b = { x, y, w: size, h: size };
      const hover = this.hovered(b);
      const selected = i === this.profile.colorIndex;
      ctx.save();
      if (hover || selected) { ctx.shadowColor = C.accent; ctx.shadowBlur = 18; }
      ctx.fillStyle = color;
      this.roundRect(x, y, size, size, 12); ctx.fill();
      ctx.restore();
      if (selected) {
        ctx.strokeStyle = C.accent; ctx.lineWidth = 3;
        this.roundRect(x - 5, y - 5, size + 10, size + 10, 14); ctx.stroke();
      }
      this.text(String(i + 1), 22, C.black, x + size / 2, y + size / 2);
      this.buttons.push({ x, y, w: size, h: size, action: "set_color", arg: i });
    });
    this.button({ x: WIDTH / 2 - 90, y: HEIGHT - 90, w: 180, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 28);
  },

  drawLangMenu() {
    this.text(this.t("lang_menu"), 32, C.accent, WIDTH / 2, 90);
    const options = [["english", "en"], ["tchinese", "zh_tw"], ["schinese", "zh_cn"]];
    const bw = 360, bh = 60, x = (WIDTH - bw) / 2;
    options.forEach((opt, i) => {
      this.button({ x, y: 180 + i * (bh + 18), w: bw, h: bh,
        label: (i + 1) + ".  " + this.t(opt[0]), action: "set_lang", arg: opt[1],
        selected: this.profile.language === opt[1] });
    });
    this.button({ x, y: 180 + 3 * (bh + 18) + 10, w: bw, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  },

  drawNameMenu() {
    const ctx = this.ctx;
    this.text(this.t("name_menu"), 32, C.accent, WIDTH / 2, 110);
    const bx = WIDTH / 2 - 160, by = 190, bw = 320, bh = 56;
    ctx.fillStyle = C.dark;
    this.roundRect(bx, by, bw, bh, 8); ctx.fill();
    ctx.strokeStyle = C.accent; ctx.lineWidth = 2;
    this.roundRect(bx, by, bw, bh, 8); ctx.stroke();
    const cursor = (Math.floor(performance.now() / 400) % 2 === 0) ? "_" : " ";
    this.text(this.nameBuffer + cursor, 32, C.white, WIDTH / 2, by + bh / 2);
    this.text(this.t("name_hint"), 22, C.grey, WIDTH / 2, 290);
    this.button({ x: WIDTH / 2 - 90, y: 340, w: 180, h: 50, label: this.t("back"), action: "sub_back" });
    this.text(this.t("back_hint"), 15, C.grey, WIDTH / 2, HEIGHT - 30);
  },

  // -- Play area --------------------------------------------------------
  cellRect(x, y, color, inset, radius) {
    const ctx = this.ctx;
    ctx.fillStyle = color;
    this.roundRect(x * CELL + inset, PLAY_TOP + y * CELL + inset, CELL - inset * 2, CELL - inset * 2, radius);
    ctx.fill();
  },

  drawPlayArea() {
    const ctx = this.ctx;
    ctx.fillStyle = C.dark;
    ctx.fillRect(0, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT);
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x <= COLS; x++) { ctx.moveTo(x * CELL, PLAY_TOP); ctx.lineTo(x * CELL, CONTROL_TOP); }
    for (let y = 0; y <= ROWS; y++) { ctx.moveTo(0, PLAY_TOP + y * CELL); ctx.lineTo(PLAY_WIDTH, PLAY_TOP + y * CELL); }
    ctx.stroke();

    for (const o of this.obstacles) {
      const [ox, oy] = o.split(",").map(Number);
      this.cellRect(ox, oy, C.obstacle, 1, 4);
    }
    if (this.food) this.cellRect(this.food[0], this.food[1], C.food, 5, 8);
    for (const s of this.snakes) this.drawSnake(s);
  },

  drawSnake(s) {
    const n = s.body.length;
    let base = toRGB(s.color);
    if (!s.alive) base = base.map((c) => Math.max(0, c - 80)); // dimmed when dead
    for (let i = 0; i < n; i++) {
      const f = 1 - (i / Math.max(1, n)) * 0.45; // head brightest, tail darker
      const color = "rgb(" + base.map((c) => Math.round(c * f)).join(",") + ")";
      this.cellRect(s.body[i][0], s.body[i][1], color, i ? 2 : 1, i ? 6 : 8);
    }
  },

  drawHud() {
    const ctx = this.ctx;
    ctx.fillStyle = C.black;
    ctx.fillRect(0, 0, WIDTH, HUD_HEIGHT);
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, HUD_HEIGHT); ctx.lineTo(WIDTH, HUD_HEIGHT); ctx.stroke();
    this.text(this.t(MODE_KEYS[this.mode]), 22, C.accent, 16, 22, "left");
    if (this.replaying) this.text(this.t("replay_label"), 22, C.gold, WIDTH - 110, 22, "left");

    if (FILL_MODES.has(this.mode)) {
      const filled = this.snakes.reduce((a, s) => a + s.body.length, 0);
      this.text(this.t("filled") + ": " + filled + " / " + (COLS * ROWS), 22, C.white, 16, 44, "left");
      this.text(this.t("high") + ": " + this.profile.highscores[MODE_KEYS[this.mode]], 22, C.grey, 280, 44, "left");
    } else if (TWO_SNAKE_MODES.has(this.mode)) {
      const parts = this.snakes.map((s, i) => this.snakeLabel(i) + ": " + s.score);
      this.text(parts.join("   "), 22, C.white, 16, 44, "left");
    } else {
      this.text(this.t("score") + ": " + this.snakes[0].score, 22, C.white, 16, 44, "left");
      this.text(this.t("high") + ": " + this.profile.highscores[MODE_KEYS[this.mode]], 22, C.grey, 180, 44, "left");
      if (this.mode === LEVEL) this.text(this.t("stage") + ": " + this.stage, 22, C.white, 320, 44, "left");
    }
  },

  drawTutorialHud() {
    const ctx = this.ctx;
    ctx.fillStyle = C.black;
    ctx.fillRect(0, 0, WIDTH, HUD_HEIGHT);
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, HUD_HEIGHT); ctx.lineTo(WIDTH, HUD_HEIGHT); ctx.stroke();
    this.text(this.t("tut_title"), 22, C.accent, 16, 22, "left");
    if (this.tutStep === 1) {
      const remaining = Math.max(0, TUT_GOAL - this.tutEaten);
      this.text(this.t("tut_eat", { n: remaining }), 22, C.white, 16, 44, "left");
    }
    this.text(this.t("tut_skip"), 15, C.dim, WIDTH - 180, 18, "left");
  },

  drawTutorialBanner() {
    let lines;
    if (this.tutStep === 0) lines = [this.t("tut_move")];
    else if (this.tutStep === 1) lines = [this.t("tut_eat", { n: Math.max(0, TUT_GOAL - this.tutEaten) })];
    else if (this.tutStep === 2) lines = [this.t("tut_avoid"), this.t("tut_continue")];
    else lines = [this.t("tut_done"), this.t("tut_continue")];
    const ctx = this.ctx;
    const stripH = 46 + 28 * (lines.length - 1);
    const x = 20, y = PLAY_TOP + 14, w = WIDTH - 40;
    ctx.fillStyle = "rgba(0,0,0,0.7)";
    this.roundRect(x, y, w, stripH, 10); ctx.fill();
    ctx.strokeStyle = C.accent; ctx.lineWidth = 1;
    this.roundRect(x, y, w, stripH, 10); ctx.stroke();
    lines.forEach((line, i) => {
      this.text(line, 22, i === 0 ? C.white : C.grey, WIDTH / 2, y + 24 + i * 28);
    });
  },

  drawControlBar() {
    const ctx = this.ctx;
    ctx.fillStyle = C.black;
    ctx.fillRect(0, CONTROL_TOP, WIDTH, CONTROL_HEIGHT);
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, CONTROL_TOP); ctx.lineTo(WIDTH, CONTROL_TOP); ctx.stroke();

    this.button({ x: 20, y: CONTROL_TOP + 36, w: 130, h: 44, label: this.t("menu_btn"), action: "to_menu" });

    const dpadStates = [STATE_READY, STATE_PLAY, STATE_TUTORIAL];
    if (dpadStates.includes(this.state) && !this.replaying && this.humanSnake()) {
      this.drawDpad();
    } else {
      const note = this.replaying ? this.t("replay_label") : this.t("watching");
      this.text(note, 22, this.replaying ? C.gold : C.grey, WIDTH - 150, CONTROL_TOP + CONTROL_HEIGHT / 2);
    }
  },

  drawDpad() {
    const cx = WIDTH - 110, cy = CONTROL_TOP + CONTROL_HEIGHT / 2, b = 40;
    const layout = [
      [UP, cx, cy - (b + 4)], [DOWN, cx, cy + (b + 4)],
      [LEFT, cx - (b + 4), cy], [RIGHT, cx + (b + 4), cy],
    ];
    const ctx = this.ctx;
    for (const [dir, bxc, byc] of layout) {
      const x = bxc - b / 2, y = byc - b / 2;
      const btn = { x, y, w: b, h: b };
      const hover = this.hovered(btn);
      ctx.save();
      if (hover) { ctx.shadowColor = C.accent; ctx.shadowBlur = 16; }
      ctx.fillStyle = hover ? C.panelHover : C.panel;
      this.roundRect(x, y, b, b, 10); ctx.fill();
      ctx.restore();
      ctx.strokeStyle = hover ? C.accent : C.border; ctx.lineWidth = hover ? 2 : 1;
      this.roundRect(x, y, b, b, 10); ctx.stroke();
      this.drawArrow(bxc, byc, dir, hover ? C.accent : C.white);
      this.buttons.push({ x, y, w: b, h: b, action: "dir", arg: dir });
    }
  },

  drawArrow(cx, cy, dir, color) {
    const ctx = this.ctx;
    const s = 9;
    ctx.fillStyle = color;
    ctx.beginPath();
    if (dir === UP) { ctx.moveTo(cx, cy - s); ctx.lineTo(cx - s, cy + s); ctx.lineTo(cx + s, cy + s); }
    else if (dir === DOWN) { ctx.moveTo(cx, cy + s); ctx.lineTo(cx - s, cy - s); ctx.lineTo(cx + s, cy - s); }
    else if (dir === LEFT) { ctx.moveTo(cx - s, cy); ctx.lineTo(cx + s, cy - s); ctx.lineTo(cx + s, cy + s); }
    else { ctx.moveTo(cx + s, cy); ctx.lineTo(cx - s, cy - s); ctx.lineTo(cx - s, cy + s); }
    ctx.closePath(); ctx.fill();
  },

  drawCenterBanner(str) {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.fillRect(0, PLAY_TOP, WIDTH, PLAY_HEIGHT);
    this.text(str, 32, C.white, WIDTH / 2, PLAY_TOP + PLAY_HEIGHT / 2);
  },

  drawGameOver() {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.72)";
    ctx.fillRect(0, PLAY_TOP, WIDTH, PLAY_HEIGHT);
    const cy = PLAY_TOP + PLAY_HEIGHT / 2;
    if (this.win) this.text(this.t("you_win"), 60, C.gold, WIDTH / 2, cy - 80, "center", true);
    else this.text(this.t("game_over"), 60, C.red, WIDTH / 2, cy - 80, "center", true);
    if (this.resultText) this.text(this.resultText, 32, C.white, WIDTH / 2, cy - 18);
    if (this.levelUpFlash > 0) this.text(this.t("level_up", { lvl: this.profile.level }), 22, C.accent, WIDTH / 2, cy + 18);
    const primary = this.replaying
      ? [this.t("replay_again"), "replay_current"]
      : [this.t("press_space_restart"), "restart"];
    this.button({ x: WIDTH / 2 - 200, y: cy + 50, w: 190, h: 50, label: primary[0], action: primary[1], font: 17 });
    this.button({ x: WIDTH / 2 + 10, y: cy + 50, w: 190, h: 50, label: this.t("menu_btn"), action: "to_menu" });
    if (!this.replaying && this.lastReplay) {
      this.button({ x: WIDTH / 2 - 95, y: cy + 112, w: 190, h: 46, label: this.t("watch_replay"), action: "watch_replay", font: 17 });
    }
  },
};
