# input_engine.py

import time
import winsound
from config import DWELL_TIME, DELETE_INTERVAL


class InputEngine:
    def __init__(self):
        self.typed_text = ""
        self.cursor = 0

        self.last_key = None
        self.hover_start = 0
        self.key_locked = False

        self.caps = False
        self.shift = False
        self.special_mode = False

        self.last_backspace_time = 0

    def update(self, hovered):
        now = time.time()

        # ===============================
        # NO KEY HOVERED
        # ===============================
        if hovered is None:
            self.last_key = None
            self.key_locked = False
            return self.typed_text, self.cursor, self.special_mode

        # ===============================
        # NEW KEY HOVER
        # ===============================
        if hovered != self.last_key:
            self.last_key = hovered
            self.hover_start = now
            self.key_locked = False
            return self.typed_text, self.cursor, self.special_mode

        hold_time = now - self.hover_start

        # ===============================
        # BACKSPACE (LONG HOLD)
        # ===============================
        if hovered in ["BACK", "BACKSPACE"] and hold_time > DWELL_TIME:
            if now - self.last_backspace_time > DELETE_INTERVAL and self.cursor > 0:
                winsound.Beep(600, 30)
                self.typed_text = (
                    self.typed_text[:self.cursor - 1]
                    + self.typed_text[self.cursor:]
                )
                self.cursor -= 1
                self.last_backspace_time = now
            return self.typed_text, self.cursor, self.special_mode

        # ===============================
        # PREVENT MULTIPLE FIRE
        # ===============================
        if self.key_locked or hold_time < DWELL_TIME:
            return self.typed_text, self.cursor, self.special_mode

        # ===============================
        # KEY ACTIVATION (ONCE)
        # ===============================
        winsound.Beep(800, 50)

        # --------- CONTROL KEYS ----------
        if hovered == "SPACE":
            self._insert(" ")

        elif hovered == "TAB":
            self._insert("    ")

        elif hovered == "ENTER":
            self._insert("\n")

        elif hovered == "CAPS":
            self.caps = not self.caps

        elif hovered in ["SHIFT", "SHIFT "]:
            self.shift = True

        elif hovered in ["CTRL", "WIN", "ALT", "CTRL ", "WIN ", "ALT "]:
            pass

        elif hovered == "?123":
            self.special_mode = True

        elif hovered == "ABC":
            self.special_mode = False

        # --------- ARROW KEYS ----------
        elif hovered == "←":
            if self.cursor > 0:
                self.cursor -= 1

        elif hovered == "→":
            if self.cursor < len(self.typed_text):
                self.cursor += 1

        elif hovered in ["↑", "↓"]:
            pass  # future: line navigation

        # --------- CHARACTER / NUMPAD ----------
        else:
            char = hovered
            if len(char) == 1 and char.isalpha():
                char = char.upper() if self.caps ^ self.shift else char.lower()
                self.shift = False

            self._insert(char)

        # ===============================
        # LOCK KEY UNTIL FINGER LEAVES
        # ===============================
        self.key_locked = True
        return self.typed_text, self.cursor, self.special_mode

    # ===============================
    # INTERNAL INSERT HELPER
    # ===============================
    def _insert(self, char):
        self.typed_text = (
            self.typed_text[:self.cursor]
            + char
            + self.typed_text[self.cursor:]
        )
        self.cursor += len(char)
