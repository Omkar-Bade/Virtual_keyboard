# 🖐️ Virtual Keyboard — Hand-Tracking Input System

A **touchless virtual keyboard** powered by real-time hand tracking using **MediaPipe** and **OpenCV**. Move your index finger in front of your webcam to hover over keys — dwell (hold) for 0.6 seconds to type them. No physical contact required.

---

## ✨ Features

- 🖐️ **Real-time hand tracking** — detects your index fingertip via webcam using MediaPipe
- ⌨️ **Full QWERTY keyboard layout** — matches a standard physical keyboard (number row, letter rows, spacebar, modifiers)
- 🔢 **Integrated numpad** — with NUMLK, `+`, `*`, `/`, `−`, `ENT`, and digit keys
- 🔤 **Special characters panel** — toggle between ABC and symbols (`!@#$%^&*()_+{}[]|;:"'<>`)
- 🏹 **Arrow key cluster** — inverted-T layout (`↑`, `←`, `↓`, `→`) for cursor navigation
- 💡 **Dwell-to-type** — keys trigger after hovering 0.6 s (no click needed)
- 🖱️ **Smooth finger cursor** — exponential smoothing removes hand jitter
- 🔒 **CAPS LOCK & SHIFT** — full case toggling with on-screen status badge
- ⌫ **Long-hold Backspace** — hold back to continuously delete characters
- 🔔 **Audible feedback** — beep sound on key press via `winsound`
- 📺 **Fullscreen UI** — renders at 1280×720 in a maximised OpenCV window

---

## 🗂️ Project Structure

```
Virtual_keyboard_modular.py/
│
├── main.py            # Entry point: camera loop, orchestrates all modules
├── config.py          # All constants (layout, timing, resolution, flags)
├── hand_tracker.py    # MediaPipe hand detection → index fingertip (x, y)
├── smoother.py        # Exponential moving average to stabilise finger position
├── input_engine.py    # State machine: dwell timer, key logic, text buffer
├── keyboard_ui.py     # OpenCV rendering: keys, numpad, text display
│
├── requirements.txt   # Python dependencies
├── .gitignore         # Git exclusions (venv, pycache, .env, etc.)
└── virtual_keyboard_report.docx  # Project report document
```

---

## 🧱 Architecture

```
Webcam Frame
     │
     ▼
┌─────────────────┐
│  hand_tracker   │  ─── MediaPipe detects index fingertip → (x, y)
└─────────────────┘
     │
     ▼
┌─────────────────┐
│    smoother     │  ─── Exponential MA removes jitter → smooth (cx, cy)
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  keyboard_ui    │  ─── Renders keys, highlights hovered key, returns it
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  input_engine   │  ─── Dwell timer → fires keystroke → updates text buffer
└─────────────────┘
     │
     ▼
  Typed Text displayed in on-screen INPUT bar
```

---

## ⚙️ Module Details

### `main.py`
The application entry point. Opens the webcam, creates a fullscreen window, and runs the main loop that chains all modules together.

### `config.py`
Central configuration file. Modify this to tune behaviour:

| Constant | Default | Description |
|---|---|---|
| `FRAME_WIDTH / HEIGHT` | `1280 × 720` | Webcam & render resolution |
| `MAX_HANDS` | `1` | Number of hands to track |
| `DETECTION_CONF` | `0.6` | MediaPipe detection threshold |
| `TRACKING_CONF` | `0.6` | MediaPipe tracking threshold |
| `ALPHA` | `0.2` | Smoothing factor (lower = smoother) |
| `DWELL_TIME` | `0.6 s` | How long to hover before key fires |
| `DELETE_INTERVAL` | `0.35 s` | Repeat-delete speed when holding Backspace |
| `KEY_HEIGHT / KEY_UNIT / KEY_GAP` | `60 / 55 / 8` | Key dimensions in pixels |

### `hand_tracker.py`
Wraps MediaPipe Hands. Exposes `get_index_tip(rgb_frame, w, h)` which returns `(x, y)` pixel coordinates of landmark **#8** (index fingertip), or `None` if no hand is detected.

### `smoother.py`
`PositionSmoother` applies **Exponential Moving Average**:

```
smoothed = prev + alpha × (new − prev)
```

Keeps the on-screen cursor steady even when the camera or hand trembles. Resets automatically when the hand leaves the frame.

### `input_engine.py`
The core state machine:
- Tracks which key is currently hovered and for how long
- Fires the key action once `DWELL_TIME` is exceeded
- Handles modifier keys: `CAPS`, `SHIFT` (case toggle), `NUMLK`
- Handles navigation: `←` `→` cursor movement inside the text buffer
- Handles long-hold Backspace with repeat-delete
- Plays a `winsound.Beep` on every successful keypress

### `keyboard_ui.py`
Renders everything onto the OpenCV frame using a dark flat theme (`#1C1612` background, golden accent `#CDB941`):
- **Main keyboard** — QWERTY rows or Special Characters panel (toggled by state)
- **Numpad block** — right-side panel with tall `+` and `ENT` tall keys
- **Arrow cluster** — inverted-T below the spacebar row
- **INPUT bar** — blinking cursor, displays CAPS/SHIFT badges
- Dwell progress shown as a gold underline that fills as you hover

---

## 🔧 Requirements

- **Python** ≥ 3.8
- **Windows** (uses `winsound` for audio feedback)
- A working **webcam**

### Python Dependencies

```
opencv-python>=4.8.0
mediapipe>=0.10.0
numpy>=1.24.0
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Omkar-Bade/Virtual_keyboard.git
cd Virtual_keyboard
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python main.py
```
---

## 🎮 How to Use

| Action | Result |
|---|---|
| Move index finger in front of webcam | Finger cursor appears on screen |
| Hover over a key for **0.6 seconds** | Key is typed (gold progress bar fills) |
| Hover over **BACK** and hold | Continuously deletes characters |
| Hover **CAPS** | Toggles CAPS LOCK (badge appears) |
| Hover **SHIFT** | Next letter types as uppercase |
| Hover **NUMLK** | Toggles Num Lock on numpad |
| Press **ESC** | Exits the application |
---

## 📸 Key Layout Preview

```
 ` 1 2 3 4 5 6 7 8 9 0 - = [BACK]     [NUMLK] [/] [*] [-]
 [TAB] Q W E R T Y U I O P [ ] \       [7] [8] [9]   [+]
 [CAPS] A S D F G H J K L ; '  [ENTER] [4] [5] [6]
 [SHIFT] Z X C V B N M , . /  [SHIFT]  [1] [2] [3]  [ENT]
 [CTRL][WIN][ALT][   SPACE   ][ALT][CTRL] [↑]  [ 0 ][.]
                                        [←][↓][→]
```

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Omkar Bade**  
GitHub: [@Omkar-Bade](https://github.com/Omkar-Bade)
