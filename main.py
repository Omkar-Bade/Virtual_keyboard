# main.py

import cv2
from config import *
from hand_tracker import HandTracker
from smoother import PositionSmoother
from keyboard_ui import draw_keyboard, draw_text_display
from input_engine import InputEngine

# ================= CAMERA =================
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# ================= FULLSCREEN WINDOW =================
WINDOW_NAME = "Virtual Keyboard"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    WINDOW_NAME,
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

# ================= OBJECTS =================
tracker = HandTracker(MAX_HANDS, DETECTION_CONF, TRACKING_CONF)
smoother = PositionSmoother(ALPHA)
engine = InputEngine()

# ================= MAIN LOOP =================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    # ---------- HAND TRACKING ----------
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pos = tracker.get_index_tip(rgb, FRAME_WIDTH, FRAME_HEIGHT)

    cx, cy = None, None
    if pos:
        cx, cy = smoother.smooth(*pos)
    else:
        smoother.reset()

    # ---------- UI & KEYBOARD LOGIC ----------
    # 1. Render keyboard GUI & find hovered point purely using cx, cy
    hovered = draw_keyboard(frame, cx, cy, engine)

    # 2. Process keystroke via back-end logic
    typed_text, cursor, _ = engine.update(hovered)

    # 3. Render clean typing bar at top
    draw_text_display(frame, typed_text, cursor, engine)

    # 3.5 Calculate and display FPS
    import time
    if not hasattr(engine, 'prev_fps_time'):
        engine.prev_fps_time = time.time()
    curr_time = time.time()
    fps = 1 / (curr_time - engine.prev_fps_time) if (curr_time - engine.prev_fps_time) > 0 else 0
    engine.prev_fps_time = curr_time
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 110), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)

    # 4. Render finger cursor ON TOP of everything
    if pos:
        cv2.circle(frame, (cx, cy), 8, (255, 180, 50), -1)   # inner dot
        cv2.circle(frame, (cx, cy), 14, (200, 200, 255), 2)  # outer ring

    # ---------- SHOW ----------
    cv2.imshow(WINDOW_NAME, frame)

    # ESC to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# ================= CLEANUP =================
cap.release()
cv2.destroyAllWindows()
