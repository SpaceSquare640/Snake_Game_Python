# Snake_Game_Python — HTML Version (browser edition)

A faithful, install-free **browser port** of Snake_Game_Python, built with the
HTML5 Canvas and vanilla JavaScript — no build step, no dependencies.

**Languages:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

### Play online

▶ **Live:** https://spacesquare640.github.io/Snake_Game_Python/

(Served by GitHub Pages from the `HTML_Version` branch.)

### Play locally

Just open `index.html` in any modern browser. Because the update check uses a
network request, serving it over HTTP avoids browser restrictions:

```bash
# from this folder
python -m http.server 8099
# then open http://localhost:8099
```

### What's included

The same game as the desktop edition:

- **8 modes** — Classic, Survival, Battle, Level, AI vs Human, Player Fill
  (main menu) and AI vs AI, AI Fill (All-AI menu).
- **Clickable GUI** with a Settings menu, an All-AI menu, and an on-screen
  **D-pad** for mouse/touch play.
- **Themes** (Dark / Neon / Retro CRT / Minimal), **sound effects + music**
  (WebAudio), a **leaderboard** (top-5 per mode), **key remapping**, an
  optional FPS counter, and a **replay system** (deterministic, seeded).
- **3 languages** — English, Traditional Chinese, Simplified Chinese.
- **BFS AI** with a survival fallback, plus a perfect **Hamiltonian-cycle**
  fill AI.
- **Saved progress** (name, level, XP, colors, high scores) via `localStorage`.
- **Update check** against GitHub Releases, shown in the top-right corner.

### Controls

- **Mouse / touch:** click menu items, buttons, or the on-screen D-pad.
- **`1`–`6`** select a mode; **`A`/`S`** open the All-AI / Settings menus.
- **WASD** or **Arrow keys** (and the D-pad) to move; **Arrows** for Player 2 in Battle.
- **SPACE** start / restart · **M** menu · **ESC** back.

---

## 繁體中文

### 線上遊玩

▶ **線上版：** https://spacesquare640.github.io/Snake_Game_Python/

（由 GitHub Pages 從 `HTML_Version` 分支提供。）

### 本機遊玩

用任何現代瀏覽器開啟 `index.html` 即可。由於更新檢查會發出網路請求，建議以 HTTP
方式提供以避免瀏覽器限制：

```bash
# 在此資料夾下
python -m http.server 8099
# 然後開啟 http://localhost:8099
```

### 內容

與桌面版相同的遊戲：

- **8 種模式** — 經典、生存、對戰、關卡、AI 對 玩家、玩家填滿（主選單），
  以及 AI 對 AI、AI 填滿（全 AI 選單）。
- **可點選的 GUI**，含設定選單、全 AI 選單，以及畫面上的 **方向鍵（D-pad）**，
  支援滑鼠／觸控。
- **佈景主題**（深色／霓虹／復古 CRT／極簡）、**音效＋音樂**（WebAudio）、**排行榜**
  （各模式前 5 名）、**按鍵重新對應**，以及可選的 FPS 顯示。
- **3 種語言** — 英文、繁體中文、簡體中文。
- **BFS 人工智慧** 與生存後備策略，以及完美的 **漢米頓迴圈** 填滿 AI。
- **進度儲存**（名稱、等級、經驗、顏色、最高分）使用 `localStorage`。
- **更新檢查**：向 GitHub Releases 查詢，顯示於右上角。

### 操作

- **滑鼠／觸控：** 點選選單項目、按鈕或畫面方向鍵。
- **`1`–`6`** 選擇模式；**`A`／`S`** 開啟全 AI／設定選單。
- **WASD** 或 **方向鍵**（及 D-pad）移動；對戰模式玩家2 用 **方向鍵**。
- **空白鍵** 開始／重新開始 · **M** 選單 · **ESC** 返回。

---

## 简体中文

### 在线游玩

▶ **在线版：** https://spacesquare640.github.io/Snake_Game_Python/

（由 GitHub Pages 从 `HTML_Version` 分支提供。）

### 本地游玩

用任何现代浏览器打开 `index.html` 即可。由于更新检查会发出网络请求，建议以 HTTP
方式提供以避免浏览器限制：

```bash
# 在此文件夹下
python -m http.server 8099
# 然后打开 http://localhost:8099
```

### 内容

与桌面版相同的游戏：

- **8 种模式** — 经典、生存、对战、关卡、AI 对 玩家、玩家填满（主菜单），
  以及 AI 对 AI、AI 填满（全 AI 菜单）。
- **可点选的 GUI**，含设置菜单、全 AI 菜单，以及画面上的 **方向键（D-pad）**，
  支持鼠标／触控。
- **界面主题**（深色／霓虹／复古 CRT／极简）、**音效＋音乐**（WebAudio）、**排行榜**
  （各模式前 5 名）、**按键重新映射**，以及可选的 FPS 显示。
- **3 种语言** — 英文、繁体中文、简体中文。
- **BFS 人工智能** 与生存后备策略，以及完美的 **哈密顿回路** 填满 AI。
- **进度保存**（名称、等级、经验、颜色、最高分）使用 `localStorage`。
- **更新检查**：向 GitHub Releases 查询，显示于右上角。

### 操作

- **鼠标／触控：** 点选菜单项目、按钮或画面方向键。
- **`1`–`6`** 选择模式；**`A`／`S`** 打开全 AI／设置菜单。
- **WASD** 或 **方向键**（及 D-pad）移动；对战模式玩家2 用 **方向键**。
- **空格键** 开始／重新开始 · **M** 菜单 · **ESC** 返回。

---

## License / 授權 / 许可

Released under the project's custom license. Any derivative work, modification,
or re-upload must clearly credit **Creators: SpaceSquare, Claude Code** and
**Owner: SpaceSquare**. Provided "As-Is" with no warranty. See the repository
`LICENSE` for full terms.
