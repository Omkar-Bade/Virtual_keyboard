# main.py

import cv2
import time
import threading
from config import *
from hand_tracker import HandTracker
from smoother import PositionSmoother
from keyboard_ui import draw_keyboard, draw_text_display
from input_engine import InputEngine


# ================= THREADED CAMERA =================
class CameraStream:
    """
    Captures frames in a background daemon thread so cap.read() never
    blocks the main render loop.  The main loop always gets the latest
    available frame instantly.
    """
    def __init__(self, index=0, width=FRAME_WIDTH, height=FRAME_HEIGHT):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.ret, self.frame = self.cap.read()   # grab first frame
        self._lock = threading.Lock()
        self._stop = False

        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()

    def _update(self):
        while not self._stop:
            ret, frame = self.cap.read()
            with self._lock:
                self.ret, self.frame = ret, frame

    def read(self):
        with self._lock:
            return self.ret, self.frame.copy() if self.ret else (False, None)

    def release(self):
        self._stop = True
        self._thread.join(timeout=1)
        self.cap.release()


# ================= FULLSCREEN WINDOW =================
WINDOW_NAME = "Virtual Keyboard"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    WINDOW_NAME,
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

# ================= OBJECTS =================
cam     = CameraStream(0, FRAME_WIDTH, FRAME_HEIGHT)
tracker = HandTracker(MAX_HANDS, DETECTION_CONF, TRACKING_CONF)
smoother = PositionSmoother(ALPHA)
engine  = InputEngine()

prev_fps_time = time.time()

# ================= MAIN LOOP =================
while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    # NOTE: resize removed — camera is already configured to FRAME_WIDTH×FRAME_HEIGHT

    # ---------- HAND TRACKING ----------
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pos = tracker.get_index_tip(rgb, FRAME_WIDTH, FRAME_HEIGHT)

    cx, cy = None, None
    if pos:
        cx, cy = smoother.smooth(*pos)
    else:
        smoother.reset()

    # ---------- UI & KEYBOARD LOGIC ----------
    # 1. Render keyboard GUI & find hovered key
    hovered = draw_keyboard(frame, cx, cy, engine)

    # 2. Process keystroke via back-end logic
    typed_text, cursor, _ = engine.update(hovered)

    # 3. Render clean typing bar at top
    draw_text_display(frame, typed_text, cursor, engine)

    # 4. FPS counter
    curr_time = time.time()
    dt = curr_time - prev_fps_time
    fps = 1.0 / dt if dt > 0 else 0.0
    prev_fps_time = curr_time
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 110),
                cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)

    # 5. Render finger cursor ON TOP of everything
    if pos:
        cv2.circle(frame, (cx, cy), 8,  (255, 180, 50), -1)   # inner dot
        cv2.circle(frame, (cx, cy), 14, (200, 200, 255), 2)   # outer ring

    # ---------- SHOW ----------
    cv2.imshow(WINDOW_NAME, frame)

    # ESC to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# ================= CLEANUP =================
cam.release()
cv2.destroyAllWindows()
