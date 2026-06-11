# Snake_Game_Python

A multi-mode, multi-language Snake game built with Python and Pygame.
It features a smart **BFS AI**, six game modes, three languages, player
profiles, and an auto-setup bootstrap that installs everything it needs.

**Languages:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

> **Version 1.5.0** — see the full [CHANGELOG](CHANGELOG.md) · new here? read the [Guidebook](Guidebook.md).

> ▶ **Play in your browser (no install):** **https://spacesquare640.github.io/Snake_Game_Python/**
> — a full HTML5 port lives on the [`HTML_Version`](https://github.com/SpaceSquare640/Snake_Game_Python/tree/HTML_Version) branch.

---

## Project structure

The **`main` branch** holds the source and documentation. The packaged
executable is distributed via **[GitHub Releases](../../releases)**, not the
branch.

```
Snake_Game_Python/            (main branch — repo root)
├── Snake_Game_Python.py      # thin launcher (run this)
├── snake_game/               # the game package (modular, since v1.4.1)
│   ├── bootstrap.py          #   self-installs Pygame on first run
│   ├── config.py             #   geometry, paths, mode/state enums
│   ├── theme.py              #   color themes + live palette
│   ├── i18n.py               #   translations (en / zh_tw / zh_cn)
│   ├── profile.py            #   save data & settings
│   ├── ai.py                 #   BFS / survival / Hamiltonian AI
│   ├── entities.py           #   the Snake
│   ├── audio.py              #   procedural sound
│   ├── render.py             #   all drawing (RenderMixin)
│   ├── game.py               #   SnakeGame controller (logic)
│   ├── version.py · app.py   #   version/update check · entry point
│   └── __init__.py
├── requirements.txt
├── assets/                   # icon.png, icon.ico
├── README.md
├── CHANGELOG.md
├── Guidebook.md
├── LICENSE
└── .gitignore

Released separately  ──►  attached to each GitHub Release:
├── Snake_Game_Python.exe     # standalone Windows executable
├── build.py                  # one-command rebuild
└── snake.spec                # PyInstaller config
```

> **Local layout:** in development the source lives in a `Source_Code/` folder
> and the build tools in a sibling `Packaged_Program/` folder. The repository
> root corresponds to the contents of `Source_Code/`.

---

## English

### Features

- **Auto-setup bootstrap** — on launch the game automatically:
  - checks your Python version (and tries to update it via `winget` on Windows)
  - checks whether required pip packages are installed
  - auto-downloads any missing package
  - checks the installed package version
  - auto-updates outdated packages
- **16 game modes** across two menus (each starts with a "Press SPACE / button to start" screen):
  - **Main menu:**
    - **Classic** — the timeless single-player Snake
    - **Survival** — speed ramps up the longer you live
    - **Battle** — two human players go head-to-head (P1: WASD, P2: Arrows)
    - **Level** — clear obstacle-filled stages; advance as your score climbs
    - **AI vs Human** — race the AI for the food
    - **Player Fill** — every step grows you; fill the whole board without crashing
  - **All-AI menu** — ten AI-algorithm showcases:
    - **AI vs AI** (two BFS snakes compete) · **AI Fill** (a perfect Hamiltonian-cycle fill)
    - **A\* Pathfinder**, **Annealing Master**, **Greedy (Easy)**, **Drift / Drunk** — one AI snake plays Classic with that algorithm
    - **Minimax vs You** (play a blocking AI) · **Minimax Duel** (hunter vs fleeing runner)
    - **Co-op Fill** (two snakes fill the board together) · **Food Rush** (race to eat 12 apples)
- **Full on-screen GUI** — clickable menus, a **Settings** menu, an **All-AI** menu, and an on-screen **D-pad** (up/down/left/right buttons) for mouse/touch play
- **Themes, sound & more** — four **visual themes** (Dark, Neon, Retro CRT, Minimal), **sound effects + music** toggle, a **leaderboard** (top-5 per mode), **key remapping**, and an optional FPS counter — all in Settings
- **Replays** — every run is recorded with a seeded RNG + input log and can be replayed exactly; revisit the last 8 runs from the **Replays** page
- **Interactive tutorial** — a forgiving, step-by-step lesson for new players, from the **How to play** button (or press `T`)
- **Automatic update check** — on launch the game checks GitHub Releases and tells you if a newer version exists
- **3 Languages** with an in-game language menu: English (default), Traditional Chinese, Simplified Chinese
- **Player profiles** — username, persistent player level (earned via XP/score)
- **Customisation** — 9 selectable snake colors
- **Data save** — language, name, color, level, and per-mode high scores are saved to `snake_save.json`

### Requirements

- Python 3.8+
- Pygame 2.1+ (installed automatically on first run)
- On the newest Python releases (e.g. **Python 3.13+**) the game automatically
  installs **`pygame-ce`** instead — a drop-in replacement that imports as
  `pygame` — because mainline `pygame` may not have wheels for that version yet.

### Installation & Run

**Option A — run from source:**

```bash
git clone https://github.com/SpaceSquare640/Snake_Game_Python.git
cd Snake_Game_Python
python Snake_Game_Python.py
```

That's it — the bootstrap installs Pygame for you if it is missing.

**Option B — run the packaged executable (Windows):**

Download `Snake_Game_Python.exe` from the latest
[GitHub Release](../../releases) and double-click it. No Python required.

### Controls

| Key | Action |
|-----|--------|
| **Mouse** | Click any menu item, button, or the on-screen D-pad |
| `1` – `6` | Select a game mode / option |
| `A` / `S` | Open the All-AI menu / Settings (from the main menu) |
| `SPACE` | Start the game / restart after Game Over |
| `W A S D` | Move (Player 1 / single player) |
| `Arrow Keys` | Move (Player 2 / single player) |
| D-pad buttons | Move (mouse / touch) |
| `C` `L` `N` | Color / Language / Name |
| `M` | Return to main menu |
| `ESC` | Back / Exit |

### How the AI Works

For most modes the AI uses **Breadth-First Search (BFS)** to compute the
shortest safe path to the food every tick. If no safe path exists, it falls back
to a survival heuristic that flood-fills open space and steps toward the
roomiest direction — avoiding walls, obstacles, and other snakes.

**AI Fill** mode uses a different strategy: a precomputed **Hamiltonian cycle**
that visits every cell of the board exactly once. By always following the cycle,
the snake can never trap itself and steadily fills the entire field.

The **All-AI menu** adds a whole toolbox of brains beyond BFS: **A\*** (heuristic
search with an aggressiveness dial), **simulated annealing** (escapes dead ends
by occasionally taking a worse-looking move), **greedy best-first** (fast but
reckless), a **DFS / random-walk** drift, and an adversarial **minimax** that
predicts the opponent and seals off its living space.

---

## 繁體中文

### 功能特色

- **自動安裝啟動程序** — 啟動遊戲時會自動：
  - 檢查 Python 版本（Windows 會嘗試透過 `winget` 更新）
  - 檢查所需的 pip 套件是否已安裝
  - 自動下載缺少的套件
  - 檢查已安裝套件的版本
  - 自動更新過舊的套件
- **16 種遊戲模式**，分屬兩個選單（每種都會先顯示「按空白鍵／按鈕開始」畫面）：
  - **主選單：**
    - **經典模式** — 永恆的單人貪食蛇
    - **生存模式** — 活得越久，速度越快
    - **對戰模式** — 雙人對決（玩家1：WASD，玩家2：方向鍵）
    - **關卡模式** — 通過充滿障礙的關卡，分數越高關卡越進階
    - **AI 對 玩家** — 與 AI 搶食物
    - **玩家填滿** — 每走一步就變長，在不撞死的前提下填滿整個場地
  - **全 AI 選單** — 十種 AI 演算法展示：
    - **AI 對 AI**（兩條 BFS 蛇對決）· **AI 填滿**（完美漢米頓迴圈填滿）
    - **A\* 尋路**、**退火大師**、**貪婪（簡單）**、**漂移／醉酒** — 由單條 AI 蛇以該演算法玩經典模式
    - **Minimax 對你**（對戰會封鎖你的 AI）· **Minimax 對決**（獵手追逐逃跑者）
    - **協作填滿**（兩蛇共同填滿場地）· **搶食競賽**（搶先吃滿 12 顆蘋果）
- **完整畫面 GUI** — 可點選的選單、**設定**選單、**全 AI** 選單，以及畫面上的
  **方向鍵（D-pad）**（上下左右按鈕），支援滑鼠／觸控操作
- **主題、音效與更多** — 四種 **佈景主題**（深色、霓虹、復古 CRT、極簡）、**音效＋音樂**
  開關、**排行榜**（各模式前 5 名）、**按鍵重新對應**，以及可選的 FPS 顯示，皆於設定中
- **重播** — 每一局都以固定種子亂數＋輸入紀錄錄製，可完整重播；於 **重播** 頁面回顧最近 8 局
- **互動教學** — 為新手設計、寬容的逐步引導，可從 **新手教學** 按鈕進入（或按 `T`）
- **自動檢查更新** — 啟動時向 GitHub Releases 檢查，並提示是否有新版本
- **3 種語言**，內建語言選單：英文（預設）、繁體中文、簡體中文
- **玩家檔案** — 玩家名稱、可累積的玩家等級（依分數/經驗值成長）
- **自訂** — 9 種可選蛇身顏色
- **資料儲存** — 語言、名稱、顏色、等級與各模式最高分皆儲存於 `snake_save.json`

### 系統需求

- Python 3.8 以上
- Pygame 2.1 以上（首次執行時自動安裝）
- 在最新的 Python 版本（例如 **Python 3.13 以上**）上，遊戲會自動改裝 **`pygame-ce`**
  （可直接以 `pygame` 匯入的替代套件），因為主線 `pygame` 可能尚未提供該版本的 wheel。

### 安裝與執行

**方式 A — 從原始碼執行：**

```bash
git clone https://github.com/SpaceSquare640/Snake_Game_Python.git
cd Snake_Game_Python
python Snake_Game_Python.py
```

就這麼簡單 — 若缺少 Pygame，啟動程序會自動為你安裝。

**方式 B — 執行封裝好的執行檔（Windows）：**

從最新的 [GitHub Release](../../releases) 下載 `Snake_Game_Python.exe`
並雙擊執行，無需安裝 Python。

### 操作說明

| 按鍵 | 動作 |
|-----|--------|
| **滑鼠** | 點選任何選單項目、按鈕或畫面方向鍵 |
| `1` – `6` | 選擇遊戲模式 / 選項 |
| `A` / `S` | 開啟全 AI 選單 / 設定（於主選單） |
| `空白鍵` | 開始遊戲 / 結束後重新開始 |
| `W A S D` | 移動（玩家1 / 單人） |
| `方向鍵` | 移動（玩家2 / 單人） |
| 方向鍵按鈕 | 移動（滑鼠／觸控） |
| `C` `L` `N` | 顏色 / 語言 / 名稱 |
| `M` | 返回主選單 |
| `ESC` | 返回 / 離開 |

### AI 運作原理

多數模式中，AI 使用 **廣度優先搜尋（BFS）** 在每一幀計算通往食物的最短安全路徑。
若沒有安全路徑，則改用生存策略：以洪水填充計算各方向的開放空間，
並朝最寬敞的方向前進，藉此避開牆壁、障礙物與其他蛇。

**AI 填滿** 模式採用不同策略：預先計算一條 **漢米頓迴圈（Hamiltonian cycle）**，
恰好經過棋盤上每一格各一次。只要永遠沿著迴圈前進，蛇就絕不會困住自己，
並穩定地填滿整個場地。

**全 AI 選單** 在 BFS 之外提供一整套大腦：**A\***（可調侵略性的啟發式搜尋）、
**模擬退火**（偶爾選擇看似較差的走法以逃出死胡同）、**貪婪最佳優先**（快但魯莽）、
**DFS／隨機遊走** 漂移，以及會預測對手並封鎖其生存空間的對抗式 **Minimax**。

---

## 简体中文

### 功能特色

- **自动安装启动程序** — 启动游戏时会自动：
  - 检查 Python 版本（Windows 会尝试通过 `winget` 更新）
  - 检查所需的 pip 包是否已安装
  - 自动下载缺少的包
  - 检查已安装包的版本
  - 自动更新过旧的包
- **16 种游戏模式**，分属两个菜单（每种都会先显示“按空格键／按钮开始”画面）：
  - **主菜单：**
    - **经典模式** — 永恒的单人贪食蛇
    - **生存模式** — 活得越久，速度越快
    - **对战模式** — 双人对决（玩家1：WASD，玩家2：方向键）
    - **关卡模式** — 通过充满障碍的关卡，分数越高关卡越进阶
    - **AI 对 玩家** — 与 AI 抢食物
    - **玩家填满** — 每走一步就变长，在不撞死的前提下填满整个场地
  - **全 AI 菜单** — 十种 AI 算法展示：
    - **AI 对 AI**（两条 BFS 蛇对决）· **AI 填满**（完美哈密顿回路填满）
    - **A\* 寻路**、**退火大师**、**贪婪（简单）**、**漂移／醉酒** — 由单条 AI 蛇以该算法玩经典模式
    - **Minimax 对你**（对战会封锁你的 AI）· **Minimax 对决**（猎手追逐逃跑者）
    - **协作填满**（两蛇共同填满场地）· **抢食竞赛**（抢先吃满 12 颗苹果）
- **完整画面 GUI** — 可点选的菜单、**设置**菜单、**全 AI** 菜单，以及画面上的
  **方向键（D-pad）**（上下左右按钮），支持鼠标／触控操作
- **主题、音效与更多** — 四种 **界面主题**（深色、霓虹、复古 CRT、极简）、**音效＋音乐**
  开关、**排行榜**（各模式前 5 名）、**按键重新映射**，以及可选的 FPS 显示，均在设置中
- **重播** — 每一局都以固定种子随机数＋输入记录录制，可完整重播；在 **重播** 页面回顾最近 8 局
- **交互式教学** — 为新手设计、宽容的逐步引导，可从 **新手教学** 按钮进入（或按 `T`）
- **自动检查更新** — 启动时向 GitHub Releases 检查，并提示是否有新版本
- **3 种语言**，内置语言菜单：英文（默认）、繁体中文、简体中文
- **玩家档案** — 玩家名称、可累积的玩家等级（依分数/经验值成长）
- **自定义** — 9 种可选蛇身颜色
- **数据保存** — 语言、名称、颜色、等级与各模式最高分均保存于 `snake_save.json`

### 系统需求

- Python 3.8 以上
- Pygame 2.1 以上（首次运行时自动安装）
- 在最新的 Python 版本（例如 **Python 3.13 以上**）上，游戏会自动改装 **`pygame-ce`**
  （可直接以 `pygame` 导入的替代包），因为主线 `pygame` 可能尚未提供该版本的 wheel。

### 安装与运行

**方式 A — 从源码运行：**

```bash
git clone https://github.com/SpaceSquare640/Snake_Game_Python.git
cd Snake_Game_Python
python Snake_Game_Python.py
```

就这么简单 — 若缺少 Pygame，启动程序会自动为你安装。

**方式 B — 运行打包好的可执行文件（Windows）：**

从最新的 [GitHub Release](../../releases) 下载 `Snake_Game_Python.exe`
并双击运行，无需安装 Python。

### 操作说明

| 按键 | 动作 |
|-----|--------|
| **鼠标** | 点选任何菜单项目、按钮或画面方向键 |
| `1` – `6` | 选择游戏模式 / 选项 |
| `A` / `S` | 打开全 AI 菜单 / 设置（于主菜单） |
| `空格键` | 开始游戏 / 结束后重新开始 |
| `W A S D` | 移动（玩家1 / 单人） |
| `方向键` | 移动（玩家2 / 单人） |
| 方向键按钮 | 移动（鼠标／触控） |
| `C` `L` `N` | 颜色 / 语言 / 名称 |
| `M` | 返回主菜单 |
| `ESC` | 返回 / 退出 |

### AI 运作原理

多数模式中，AI 使用 **广度优先搜索（BFS）** 在每一帧计算通往食物的最短安全路径。
若没有安全路径，则改用生存策略：以洪水填充计算各方向的开放空间，
并朝最宽敞的方向前进，从而避开墙壁、障碍物与其他蛇。

**AI 填满** 模式采用不同策略：预先计算一条 **哈密顿回路（Hamiltonian cycle）**，
恰好经过棋盘上每一格各一次。只要永远沿着回路前进，蛇就绝不会困住自己，
并稳定地填满整个场地。

**全 AI 菜单** 在 BFS 之外提供一整套大脑：**A\***（可调侵略性的启发式搜索）、
**模拟退火**（偶尔选择看似较差的走法以逃出死胡同）、**贪婪最佳优先**（快但鲁莽）、
**DFS／随机游走** 漂移，以及会预测对手并封锁其生存空间的对抗式 **Minimax**。

---

## License

This project is released under a custom [LICENSE](LICENSE) (available in English,
繁體中文, and 简体中文). In short: you may freely download, use, and share the
source code and the packaged build, but any derivative work, modification, or
re-upload **must clearly credit** the contributors and owner:

- **Creators:** SpaceSquare, Claude Code
- **Owner:** SpaceSquare

The software is provided "As-Is" with no warranty or liability — see the
[LICENSE](LICENSE) for the full terms.
