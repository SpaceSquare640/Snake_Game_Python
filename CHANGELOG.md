# Changelog

All notable changes to **Snake_Game_Python** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project adheres to [Semantic Versioning](https://semver.org/).

**Languages:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

### [1.2.0] — 2026-06-10

#### Added
- **Visual themes** — Dark, Neon, Retro CRT, and Minimal, switchable in Settings.
- **Sound effects** (eat / select / crash / win) plus a **background-music**
  toggle, synthesized at runtime (no audio files).
- **Leaderboard** — top-5 scores per mode, reachable from the main menu.
- **Key remapping** — rebind the movement keys under Settings → Controls.
- **Optional FPS counter** (Settings → Audio).

#### Changed (UI)
- **Shortcut badges** (`1`–`6`, `A`, `S`) on the menu buttons.
- Wider margins, a thin **separator** above the profile card, smoother hover,
  and **press/click feedback** on every button.

### [1.1.1] — 2026-06-10

#### Changed (UI polish)
- **Button hover feedback** — buttons now show a soft outer glow and an
  accent-colored border on hover (instead of a flat grey outline).
- **Bolder title** and **lower-contrast credits** so focus lands on the menu.
- **Rounder corners** on all buttons and cards for a more modern look.
- **Profile card** — name, level, and XP are grouped into a single card with
  thin dividers, balancing the information density.
- **Corner status** — the version/update indicator (with a colored status dot)
  moved to the top-right corner so it never blocks the view.
- Slightly **desaturated accent green** for more comfortable long sessions.

### [1.1.0] — 2026-06-10

#### Added
- **Two new modes:**
  - **Player Fill** — every step grows the snake; fill the whole board without
    crashing (a true endgame puzzle).
  - **AI Fill** *(All-AI menu)* — a perfect **Hamiltonian-cycle** AI traces and
    fills every cell of the board.
- **All-AI menu** — `AI vs AI` moves here and is joined by `AI Fill`.
- **Settings menu** — Language, Snake Color, and Player Name in one place.
- **Full on-screen GUI** — clickable menus and buttons throughout.
- **On-screen D-pad** — four up/down/left/right buttons for mouse/touch play.
- **Automatic update check** — on launch the game checks GitHub Releases and
  shows whether you are on the latest version.

#### Changed
- Reorganised modes into a **Main menu** (Classic, Survival, Battle, Level,
  AI vs Human, Player Fill) and an **All-AI menu** (AI vs AI, AI Fill).
- Taller window with a dedicated bottom control bar.

#### Fixed
- Save file now writes next to the executable in packaged builds.

### [1.0.0] — 2026-06-10

First public release.

#### Added
- Self-contained **auto-setup bootstrap**: checks the Python version (and
  attempts a `winget` update on Windows), installs Pygame if missing, and
  auto-updates an outdated Pygame. Picks `pygame-ce` automatically on Python
  3.13+.
- **Six game modes**: Classic, Survival, Battle (2-player), Level (obstacle
  stages), AI vs AI, and AI vs Human. Each opens with a "Press SPACE to start"
  screen.
- **BFS AI** with a flood-fill **survival fallback** for when no safe path to
  the food exists.
- **Three languages** — English (default), Traditional Chinese, Simplified
  Chinese — switchable from an in-game menu.
- **Player profiles**: editable username and a persistent, XP-based player
  level.
- **Nine selectable snake colors.**
- **Persistent save** (`snake_save.json`) for language, name, color, level/XP,
  and per-mode high scores.
- **Custom app icon** shown on the game window/taskbar and embedded in the
  Windows executable.
- **Packaged build**: standalone `Snake_Game_Python.exe` (icon included),
  distributed via GitHub Releases, plus a reproducible `build.py` / `snake.spec`
  PyInstaller setup.
- Trilingual documentation: `README.md`, `CHANGELOG.md`, and `Guidebook.md`.
- **Custom license** with an attribution requirement (Creators: SpaceSquare,
  Claude Code; Owner: SpaceSquare), provided in all three languages.

---

## 繁體中文

### [1.2.0] — 2026-06-10

#### 新增
- **佈景主題** — 深色、霓虹、復古 CRT、極簡，可於設定中切換。
- **音效**（吃食物／選擇／碰撞／勝利）以及 **背景音樂** 開關，皆於執行時合成（無音檔）。
- **排行榜** — 各模式前 5 名，從主選單進入。
- **按鍵重新對應** — 於 設定 → 按鍵設定 重新綁定移動鍵。
- **可選 FPS 顯示**（設定 → 音效）。

#### 變更（介面）
- 選單按鈕加上 **快捷鍵標示**（`1`–`6`、`A`、`S`）。
- 加寬邊距、玩家資訊卡上方加入細 **分隔線**、更平滑的懸停效果，並為每顆按鈕加入
  **點擊回饋**。

### [1.1.1] — 2026-06-10

#### 變更（介面優化）
- **按鈕懸停回饋** — 滑鼠懸停時按鈕會出現柔和的外發光與主色邊框（取代原本的灰色外框）。
- **標題加粗**、**創作者資訊降低對比**，讓焦點集中在選單按鈕。
- 所有按鈕與卡片採用**更大的圓角**，看起來更現代圓潤。
- **玩家資訊卡片** — 將名稱、等級、經驗值整合為一張附細分隔線的卡片，使資訊密度更平衡。
- **角落狀態** — 版本／更新指示（含彩色狀態點）移至右上角，不再遮擋畫面。
- **主色綠稍微降低飽和度**，長時間遊玩更舒適。

### [1.1.0] — 2026-06-10

#### 新增
- **兩種新模式：**
  - **玩家填滿** — 每走一步蛇就變長；在不撞死的前提下填滿整個場地（真正的終局謎題）。
  - **AI 填滿**（全 AI 選單）— 採用完美的 **漢米頓迴圈（Hamiltonian cycle）** AI，
    巡遍並填滿場地的每一格。
- **全 AI 選單** — `AI 對 AI` 移至此處，並新增 `AI 填滿`。
- **設定選單** — 將語言、蛇身顏色、玩家名稱集中於一處。
- **完整的畫面 GUI** — 全程可用滑鼠點選的選單與按鈕。
- **畫面方向鍵（D-pad）** — 上下左右四顆按鈕，支援滑鼠／觸控操作。
- **自動檢查更新** — 啟動時會向 GitHub Releases 檢查，並顯示是否為最新版本。

#### 變更
- 將模式重新整理為 **主選單**（經典、生存、對戰、關卡、AI 對 玩家、玩家填滿）
  與 **全 AI 選單**（AI 對 AI、AI 填滿）。
- 視窗加高，並新增專屬的底部控制列。

#### 修正
- 封裝版本的存檔現在會寫入執行檔旁的目錄。

### [1.0.0] — 2026-06-10

首次公開發行。

#### 新增
- 內建 **自動安裝啟動程序**：檢查 Python 版本（Windows 會嘗試以 `winget` 更新）、
  缺少時自動安裝 Pygame、過舊時自動更新；在 Python 3.13 以上會自動改用 `pygame-ce`。
- **六種遊戲模式**：經典、生存、對戰（雙人）、關卡（障礙關卡）、AI 對 AI、AI 對 玩家。
  每種模式皆以「按空白鍵開始」畫面開場。
- **BFS 人工智慧**，並具備以洪水填充為基礎的 **生存後備策略**，當找不到通往食物的
  安全路徑時啟用。
- **三種語言** — 英文（預設）、繁體中文、簡體中文 — 可於遊戲內選單切換。
- **玩家檔案**：可編輯的玩家名稱，以及可持續累積、以經驗值計算的玩家等級。
- **九種可選蛇身顏色。**
- **資料持久化儲存**（`snake_save.json`）：語言、名稱、顏色、等級／經驗值與各模式最高分。
- **自訂應用程式圖示**，顯示於遊戲視窗／工作列，並內嵌於 Windows 執行檔。
- **封裝版本**：獨立的 `Snake_Game_Python.exe`（含圖示），透過 GitHub Releases
  發佈，並附可重現的 `build.py` / `snake.spec` PyInstaller 設定。
- 三語文件：`README.md`、`CHANGELOG.md`、`Guidebook.md`。
- **自訂授權條款**，附帶署名要求（創作者：SpaceSquare、Claude Code；擁有者：
  SpaceSquare），並提供三種語言版本。

---

## 简体中文

### [1.2.0] — 2026-06-10

#### 新增
- **界面主题** — 深色、霓虹、复古 CRT、极简，可在设置中切换。
- **音效**（吃食物／选择／碰撞／胜利）以及 **背景音乐** 开关，均在运行时合成（无音频文件）。
- **排行榜** — 各模式前 5 名，从主菜单进入。
- **按键重新映射** — 在 设置 → 按键设置 重新绑定移动键。
- **可选 FPS 显示**（设置 → 音效）。

#### 变更（界面）
- 菜单按钮加上 **快捷键标示**（`1`–`6`、`A`、`S`）。
- 加宽边距、玩家信息卡上方加入细 **分隔线**、更平滑的悬停效果，并为每个按钮加入
  **点击反馈**。

### [1.1.1] — 2026-06-10

#### 变更（界面优化）
- **按钮悬停反馈** — 鼠标悬停时按钮会出现柔和的外发光与主色边框（取代原本的灰色外框）。
- **标题加粗**、**创作者信息降低对比**，让焦点集中在菜单按钮。
- 所有按钮与卡片采用**更大的圆角**，看起来更现代圆润。
- **玩家信息卡片** — 将名称、等级、经验值整合为一张附细分隔线的卡片，使信息密度更平衡。
- **角落状态** — 版本／更新指示（含彩色状态点）移至右上角，不再遮挡画面。
- **主色绿稍微降低饱和度**，长时间游玩更舒适。

### [1.1.0] — 2026-06-10

#### 新增
- **两种新模式：**
  - **玩家填满** — 每走一步蛇就变长；在不撞死的前提下填满整个场地（真正的终局谜题）。
  - **AI 填满**（全 AI 菜单）— 采用完美的 **哈密顿回路（Hamiltonian cycle）** AI，
    遍历并填满场地的每一格。
- **全 AI 菜单** — `AI 对 AI` 移至此处，并新增 `AI 填满`。
- **设置菜单** — 将语言、蛇身颜色、玩家名称集中于一处。
- **完整的画面 GUI** — 全程可用鼠标点选的菜单与按钮。
- **画面方向键（D-pad）** — 上下左右四个按钮，支持鼠标／触控操作。
- **自动检查更新** — 启动时会向 GitHub Releases 检查，并显示是否为最新版本。

#### 变更
- 将模式重新整理为 **主菜单**（经典、生存、对战、关卡、AI 对 玩家、玩家填满）
  与 **全 AI 菜单**（AI 对 AI、AI 填满）。
- 窗口加高，并新增专属的底部控制栏。

#### 修复
- 打包版本的存档现在会写入可执行文件旁的目录。

### [1.0.0] — 2026-06-10

首次公开发行。

#### 新增
- 内置 **自动安装启动程序**：检查 Python 版本（Windows 会尝试以 `winget` 更新）、
  缺少时自动安装 Pygame、过旧时自动更新；在 Python 3.13 以上会自动改用 `pygame-ce`。
- **六种游戏模式**：经典、生存、对战（双人）、关卡（障碍关卡）、AI 对 AI、AI 对 玩家。
  每种模式均以“按空格键开始”画面开场。
- **BFS 人工智能**，并具备以洪水填充为基础的 **生存后备策略**，当找不到通往食物的
  安全路径时启用。
- **三种语言** — 英文（默认）、繁体中文、简体中文 — 可在游戏内菜单切换。
- **玩家档案**：可编辑的玩家名称，以及可持续累积、以经验值计算的玩家等级。
- **九种可选蛇身颜色。**
- **数据持久化保存**（`snake_save.json`）：语言、名称、颜色、等级／经验值与各模式最高分。
- **自定义应用程序图标**，显示于游戏窗口／任务栏，并内嵌于 Windows 可执行文件。
- **打包版本**：独立的 `Snake_Game_Python.exe`（含图标），通过 GitHub Releases
  发布，并附可复现的 `build.py` / `snake.spec` PyInstaller 配置。
- 三语文档：`README.md`、`CHANGELOG.md`、`Guidebook.md`。
- **自定义许可协议**，附带署名要求（创作者：SpaceSquare、Claude Code；拥有者：
  SpaceSquare），并提供三种语言版本。

[1.2.0]: https://github.com/SpaceSquare640/Snake_Game_Python/releases/tag/v1.2.0
[1.1.1]: https://github.com/SpaceSquare640/Snake_Game_Python/releases/tag/v1.1.1
[1.1.0]: https://github.com/SpaceSquare640/Snake_Game_Python/releases/tag/v1.1.0
[1.0.0]: https://github.com/SpaceSquare640/Snake_Game_Python/releases/tag/v1.0.0
