# hand_tracker.py

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import cv2
import urllib.request
import os


# Path to the hand landmarker model
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


def _ensure_model():
    """Download the hand landmarker model if it isn't already present."""
    if not os.path.exists(_MODEL_PATH):
        print("[HandTracker] Downloading hand_landmarker.task model …")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("[HandTracker] Model downloaded.")


# Landmark index for the index-finger tip
_INDEX_TIP = 8


class HandTracker:
    def __init__(self, max_hands=1, det_conf=0.6, track_conf=0.6):
        _ensure_model()

        base_options = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,   # stateless, thread-safe
            num_hands=max_hands,
            min_hand_detection_confidence=det_conf,
            min_hand_presence_confidence=det_conf,
            min_tracking_confidence=track_conf,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def get_index_tip(self, rgb_frame, w, h, draw=False, frame=None):
        """
        Returns (x, y) pixel coordinates of the index-finger tip.
        If no hand is detected, returns None.

        Parameters
        ----------
        rgb_frame : np.ndarray  – BGR-converted-to-RGB frame (uint8, HxWx3)
        w, h      : int         – frame width and height
        draw      : bool        – whether to draw landmarks on *frame*
        frame     : np.ndarray  – BGR frame used for drawing (optional)
        """
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.detector.detect(mp_image)

        if not result.hand_landmarks:
            return None

        # First detected hand
        landmarks = result.hand_landmarks[0]
        tip = landmarks[_INDEX_TIP]

        x = int(tip.x * w)
        y = int(tip.y * h)

        if draw and frame is not None:
            # Draw all landmarks manually
            for lm in landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)
            # Highlight index tip
            cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)

        return x, y
