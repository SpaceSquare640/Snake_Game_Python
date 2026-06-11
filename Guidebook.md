# Guidebook — Snake_Game_Python

A friendly visitor's guide: how to get the game running and how to play each
mode well. For the feature list see the [README](README.md); for the release
history see the [CHANGELOG](CHANGELOG.md).

**Languages:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

### 1. Getting started

**The easiest way (Windows):** download `Snake_Game_Python.exe` from the latest
[GitHub Release](../../releases) and double-click it. No installation needed.

**From source (any OS):**

```bash
python Snake_Game_Python.py
```

On the very first launch the game prints a few "bootstrap" lines while it makes
sure Pygame is installed. This only happens once.

### 2. The main menu

- **Click** a mode button (each shows a `1`–`6` shortcut badge), or press the key.
- New to Snake? Hit **How to play** (or press `T`) for a short interactive tutorial.
- Utility buttons: **All-AI Modes**, **Leaderboard** (top-5 per mode), **Replays**
  (rewatch your last 8 runs), and **Settings** — language, snake color, **theme**
  (Dark / Neon / Retro CRT / Minimal), **audio** (sound, music, FPS counter),
  **controls** (rebind your movement keys), and player name.
- Your **name**, **level**, and **XP** are shown at the bottom, next to your
  current snake-color swatch. The version line tells you if an update is out.
- Press **`ESC`** to quit.

### 3. Starting a round

Every mode opens on a **"Press SPACE / a button to start"** screen so you can
get ready. Press **SPACE** or tap a D-pad button to begin. During play, press
**`M`** (or the **Menu** button) to jump back to the menu at any time.

The bottom **control bar** has an on-screen **D-pad** — four up/down/left/right
buttons you can click instead of using the keyboard.

### 4. The modes

**Main menu:**

| Mode | Goal | Controls |
|------|------|----------|
| **Classic** | Eat, grow, don't crash. | WASD / Arrows / D-pad |
| **Survival** | Same, but you speed up with every bite. | WASD / Arrows / D-pad |
| **Battle** | Outlast a second human player. | P1 = WASD, P2 = Arrows |
| **Level** | Eat through obstacle stages; every 5 points advances a stage. | WASD / Arrows / D-pad |
| **AI vs Human** | Beat the AI to the food. You are the left snake. | WASD / D-pad |
| **Player Fill** | Every step grows you — fill the whole board without crashing. | WASD / Arrows / D-pad |

**All-AI menu:**

| Mode | Goal | Controls |
|------|------|----------|
| **AI vs AI** | Sit back and watch two BFS snakes duel. | — (just watch) |
| **AI Fill** | Watch a perfect Hamiltonian-cycle AI fill every cell. | — (just watch) |

Two-snake modes end when only one snake (or none) is left; the survivor wins.
Fill modes end when the board is full (**You Win!**) or you crash.

### 5. Levelling up

Your score becomes XP. Fill the XP bar and your **player level** rises — it is
saved permanently in `snake_save.json`, along with your best score in each mode.

### 6. Tips

- In **Survival**, plan your turns early — the later game is *fast*.
- In **Level**, the safe lane on your starting row is always kept clear.
- **Player Fill** is the ultimate challenge — every step counts, so think ahead.
- Watching **AI Fill** is a great way to see a "perfect" snake solve the board.

---

## 繁體中文

### 1. 開始遊玩

**最簡單的方式（Windows）：** 從最新的 [GitHub Release](../../releases) 下載
`Snake_Game_Python.exe` 並雙擊執行，無需安裝。

**從原始碼執行（任何系統）：**

```bash
python Snake_Game_Python.py
```

首次啟動時，遊戲會顯示幾行「啟動程序」訊息，以確認 Pygame 已安裝。此步驟只會發生一次。

### 2. 主選單

- **點選** 模式按鈕（每顆都有 `1`–`6` 快捷鍵標示），或按對應按鍵。
- 第一次玩？點 **新手教學**（或按 `T`）體驗簡短的互動教學。
- 工具按鈕：**全 AI 模式**、**排行榜**（各模式前 5 名）、**重播**（回顧最近 8 局），
  以及 **設定** — 語言、蛇身顏色、**佈景主題**（深色／霓虹／復古 CRT／極簡）、
  **音效**（音效、音樂、FPS 顯示）、**按鍵設定**（重新對應移動鍵）與玩家名稱。
- 畫面下方會顯示你的 **名稱**、**等級** 與 **經驗值**，旁邊是目前的蛇身顏色方塊；
  版本列會提示是否有可用更新。
- 按 **`ESC`** 離開。

### 3. 開始一局

每種模式都會以 **「按空白鍵／按鈕開始」** 畫面開場，讓你做好準備。按 **空白鍵**
或點一下方向鍵按鈕即可開始。遊戲進行中，隨時可按 **`M`**（或 **選單** 按鈕）返回主選單。

底部 **控制列** 內建畫面 **方向鍵（D-pad）** —— 上下左右四顆按鈕，可用點選取代鍵盤。

### 4. 各種模式

**主選單：**

| 模式 | 目標 | 操作 |
|------|------|------|
| **經典模式** | 吃食物、成長、別撞上。 | WASD／方向鍵／D-pad |
| **生存模式** | 相同，但每吃一次就會加速。 | WASD／方向鍵／D-pad |
| **對戰模式** | 比第二位玩家活得更久。 | 玩家1＝WASD，玩家2＝方向鍵 |
| **關卡模式** | 通過障礙關卡；每 5 分前進一關。 | WASD／方向鍵／D-pad |
| **AI 對 玩家** | 比 AI 更快搶到食物。你是左邊那條蛇。 | WASD／D-pad |
| **玩家填滿** | 每走一步就變長 —— 在不撞死的前提下填滿整個場地。 | WASD／方向鍵／D-pad |

**全 AI 選單：**

| 模式 | 目標 | 操作 |
|------|------|------|
| **AI 對 AI** | 輕鬆觀看兩條 BFS 蛇對決。 | —（純觀賞） |
| **AI 填滿** | 觀看採用完美漢米頓迴圈的 AI 填滿每一格。 | —（純觀賞） |

雙蛇模式會在只剩一條（或全滅）時結束，存活者獲勝。
填滿模式在場地填滿時結束（**你贏了！**），或在撞死時結束。

### 5. 升級

你的分數會轉換成經驗值。填滿經驗條，**玩家等級** 就會提升 —— 等級會永久儲存於
`snake_save.json`，連同你在各模式的最高分。

### 6. 小技巧

- 在 **生存模式**，提早規劃轉向 —— 後期速度*非常*快。
- 在 **關卡模式**，你起始列上的安全通道永遠會保持淨空。
- **玩家填滿** 是終極挑戰 —— 每一步都重要，務必提前思考。
- 觀看 **AI 填滿** 是欣賞「完美蛇」如何解開棋盤的好方法。

---

## 简体中文

### 1. 开始游玩

**最简单的方式（Windows）：** 从最新的 [GitHub Release](../../releases) 下载
`Snake_Game_Python.exe` 并双击运行，无需安装。

**从源码运行（任何系统）：**

```bash
python Snake_Game_Python.py
```

首次启动时，游戏会显示几行“启动程序”信息，以确认 Pygame 已安装。此步骤只会发生一次。

### 2. 主菜单

- **点选** 模式按钮（每个都有 `1`–`6` 快捷键标示），或按对应按键。
- 第一次玩？点 **新手教学**（或按 `T`）体验简短的交互式教学。
- 工具按钮：**全 AI 模式**、**排行榜**（各模式前 5 名）、**重播**（回顾最近 8 局），
  以及 **设置** — 语言、蛇身颜色、**界面主题**（深色／霓虹／复古 CRT／极简）、
  **音效**（音效、音乐、FPS 显示）、**按键设置**（重新映射移动键）与玩家名称。
- 画面下方会显示你的 **名称**、**等级** 与 **经验值**，旁边是当前的蛇身颜色方块；
  版本行会提示是否有可用更新。
- 按 **`ESC`** 退出。

### 3. 开始一局

每种模式都会以 **“按空格键／按钮开始”** 画面开场，让你做好准备。按 **空格键**
或点一下方向键按钮即可开始。游戏进行中，随时可按 **`M`**（或 **菜单** 按钮）返回主菜单。

底部 **控制栏** 内置画面 **方向键（D-pad）** —— 上下左右四个按钮，可用点选取代键盘。

### 4. 各种模式

**主菜单：**

| 模式 | 目标 | 操作 |
|------|------|------|
| **经典模式** | 吃食物、成长、别撞上。 | WASD／方向键／D-pad |
| **生存模式** | 相同，但每吃一次就会加速。 | WASD／方向键／D-pad |
| **对战模式** | 比第二位玩家活得更久。 | 玩家1＝WASD，玩家2＝方向键 |
| **关卡模式** | 通过障碍关卡；每 5 分前进一关。 | WASD／方向键／D-pad |
| **AI 对 玩家** | 比 AI 更快抢到食物。你是左边那条蛇。 | WASD／D-pad |
| **玩家填满** | 每走一步就变长 —— 在不撞死的前提下填满整个场地。 | WASD／方向键／D-pad |

**全 AI 菜单：**

| 模式 | 目标 | 操作 |
|------|------|------|
| **AI 对 AI** | 轻松观看两条 BFS 蛇对决。 | —（纯观赏） |
| **AI 填满** | 观看采用完美哈密顿回路的 AI 填满每一格。 | —（纯观赏） |

双蛇模式会在只剩一条（或全灭）时结束，存活者获胜。
填满模式在场地填满时结束（**你赢了！**），或在撞死时结束。

### 5. 升级

你的分数会转换成经验值。填满经验条，**玩家等级** 就会提升 —— 等级会永久保存于
`snake_save.json`，连同你在各模式的最高分。

### 6. 小技巧

- 在 **生存模式**，提早规划转向 —— 后期速度*非常*快。
- 在 **关卡模式**，你起始行上的安全通道永远会保持净空。
- **玩家填满** 是终极挑战 —— 每一步都重要，务必提前思考。
- 观看 **AI 填满** 是欣赏“完美蛇”如何解开棋盘的好方法。
