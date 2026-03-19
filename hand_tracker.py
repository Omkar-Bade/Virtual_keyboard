# hand_tracker.py

import mediapipe as mp
import cv2


class HandTracker:
    def __init__(self, max_hands=1, det_conf=0.6, track_conf=0.6):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=det_conf,
            min_tracking_confidence=track_conf
        )
        self.mp_draw = mp.solutions.drawing_utils

    def get_index_tip(self, rgb_frame, w, h, draw=False, frame=None):
        """
        Returns (x, y) coordinates of index finger tip.
        If no hand detected, returns None.
        """

        result = self.hands.process(rgb_frame)

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]
            tip = hand_landmarks.landmark[8]

            x = int(tip.x * w)
            y = int(tip.y * h)

            # Optional drawing
            if draw and frame is not None:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )
                cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)

            return x, y

        return None
