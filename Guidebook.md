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

- Press a number key **`1`–`6`** to pick a mode.
- Your **name**, **level**, and **XP** are shown at the bottom, next to your
  current snake-color swatch.
- Press **`C`** to change color, **`L`** for language, **`N`** to set your name.
- Press **`ESC`** to quit.

### 3. Starting a round

Every mode opens on a **"Press SPACE to start"** screen so you can get your
fingers ready. Press **SPACE** to begin. During play, press **`M`** to jump
back to the menu at any time.

### 4. The modes

| Mode | Goal | Controls |
|------|------|----------|
| **Classic** | Eat, grow, don't crash. | WASD or Arrows |
| **Survival** | Same, but you speed up with every bite. | WASD or Arrows |
| **Battle** | Outlast a second human player. | P1 = WASD, P2 = Arrows |
| **Level** | Eat through obstacle stages; every 5 points advances a stage. | WASD or Arrows |
| **AI vs AI** | Sit back and watch two BFS snakes duel. | — (just watch) |
| **AI vs Human** | Beat the AI to the food. You are the left snake. | WASD |

Two-snake modes end when only one snake (or none) is left; the survivor wins.

### 5. Levelling up

Your score becomes XP. Fill the XP bar and your **player level** rises — it is
saved permanently in `snake_save.json`, along with your best score in each mode.

### 6. Tips

- In **Survival**, plan your turns early — the later game is *fast*.
- In **Level**, the safe lane on your starting row is always kept clear.
- Watching **AI vs AI** is a great way to learn efficient pathing.

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

- 按數字鍵 **`1`–`6`** 選擇模式。
- 畫面下方會顯示你的 **名稱**、**等級** 與 **經驗值**，旁邊是目前的蛇身顏色方塊。
- 按 **`C`** 變更顏色、**`L`** 切換語言、**`N`** 設定名稱。
- 按 **`ESC`** 離開。

### 3. 開始一局

每種模式都會以 **「按空白鍵開始」** 畫面開場，讓你做好準備。按 **空白鍵** 開始遊戲。
遊戲進行中，隨時可按 **`M`** 返回主選單。

### 4. 各種模式

| 模式 | 目標 | 操作 |
|------|------|------|
| **經典模式** | 吃食物、成長、別撞上。 | WASD 或 方向鍵 |
| **生存模式** | 相同，但每吃一次就會加速。 | WASD 或 方向鍵 |
| **對戰模式** | 比第二位玩家活得更久。 | 玩家1＝WASD，玩家2＝方向鍵 |
| **關卡模式** | 通過障礙關卡；每 5 分前進一關。 | WASD 或 方向鍵 |
| **AI 對 AI** | 輕鬆觀看兩條 BFS 蛇對決。 | —（純觀賞） |
| **AI 對 玩家** | 比 AI 更快搶到食物。你是左邊那條蛇。 | WASD |

雙蛇模式會在只剩一條（或全滅）時結束，存活者獲勝。

### 5. 升級

你的分數會轉換成經驗值。填滿經驗條，**玩家等級** 就會提升 —— 等級會永久儲存於
`snake_save.json`，連同你在各模式的最高分。

### 6. 小技巧

- 在 **生存模式**，提早規劃轉向 —— 後期速度*非常*快。
- 在 **關卡模式**，你起始列上的安全通道永遠會保持淨空。
- 觀看 **AI 對 AI** 是學習高效率路徑規劃的好方法。

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

- 按数字键 **`1`–`6`** 选择模式。
- 画面下方会显示你的 **名称**、**等级** 与 **经验值**，旁边是当前的蛇身颜色方块。
- 按 **`C`** 更改颜色、**`L`** 切换语言、**`N`** 设置名称。
- 按 **`ESC`** 退出。

### 3. 开始一局

每种模式都会以 **“按空格键开始”** 画面开场，让你做好准备。按 **空格键** 开始游戏。
游戏进行中，随时可按 **`M`** 返回主菜单。

### 4. 各种模式

| 模式 | 目标 | 操作 |
|------|------|------|
| **经典模式** | 吃食物、成长、别撞上。 | WASD 或 方向键 |
| **生存模式** | 相同，但每吃一次就会加速。 | WASD 或 方向键 |
| **对战模式** | 比第二位玩家活得更久。 | 玩家1＝WASD，玩家2＝方向键 |
| **关卡模式** | 通过障碍关卡；每 5 分前进一关。 | WASD 或 方向键 |
| **AI 对 AI** | 轻松观看两条 BFS 蛇对决。 | —（纯观赏） |
| **AI 对 玩家** | 比 AI 更快抢到食物。你是左边那条蛇。 | WASD |

双蛇模式会在只剩一条（或全灭）时结束，存活者获胜。

### 5. 升级

你的分数会转换成经验值。填满经验条，**玩家等级** 就会提升 —— 等级会永久保存于
`snake_save.json`，连同你在各模式的最高分。

### 6. 小技巧

- 在 **生存模式**，提早规划转向 —— 后期速度*非常*快。
- 在 **关卡模式**，你起始行上的安全通道永远会保持净空。
- 观看 **AI 对 AI** 是学习高效率路径规划的好方法。
