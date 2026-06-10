# Changelog

All notable changes to **Snake_Game_Python** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project adheres to [Semantic Versioning](https://semver.org/).

**Languages:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

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

[1.0.0]: https://github.com/<OWNER>/Snake_Game_Python/releases/tag/v1.0.0
