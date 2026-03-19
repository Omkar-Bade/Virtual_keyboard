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
        self.num_lock = True

        self.last_backspace_time = 0

    def update(self, hovered):
        now = time.time()

        if hovered is None:
            self.last_key = None
            self.key_locked = False
            return self.typed_text, self.cursor, self.special_mode

        if hovered != self.last_key:
            self.last_key = hovered
            self.hover_start = now
            self.key_locked = False
            return self.typed_text, self.cursor, self.special_mode

        hold_time = now - self.hover_start

        if hovered in ("BACK", "BACKSPACE") and hold_time > DWELL_TIME:
            if now - self.last_backspace_time > DELETE_INTERVAL and self.cursor > 0:
                winsound.Beep(600, 30)
                self.typed_text = (self.typed_text[:self.cursor - 1]
                                   + self.typed_text[self.cursor:])
                self.cursor -= 1
                self.last_backspace_time = now
            return self.typed_text, self.cursor, self.special_mode

        if self.key_locked or hold_time < DWELL_TIME:
            return self.typed_text, self.cursor, self.special_mode

        winsound.Beep(800, 50)

        if hovered == "SPACE":
            self._insert(" ")
        elif hovered == "TAB":
            self._insert("    ")
        elif hovered in ("ENTER", "NP_ENT"):
            self._insert("\n")
        elif hovered == "CAPS":
            self.caps = not self.caps
        elif hovered in ("SHIFT", "SHIFT "):
            self.shift = True
        elif hovered == "NUMLK":
            self.num_lock = not self.num_lock
        elif hovered in ("CTRL", "CTRL ", "WIN", "ALT", "ALT "):
            pass
        elif hovered == "?123":
            self.special_mode = True
        elif hovered == "ABC":
            self.special_mode = False
        elif hovered == "←":
            if self.cursor > 0:
                self.cursor -= 1
        elif hovered == "→":
            if self.cursor < len(self.typed_text):
                self.cursor += 1
        elif hovered in ("↑", "↓"):
            pass
        else:
            char = hovered
            if len(char) == 1 and char.isalpha():
                char = char.upper() if self.caps ^ self.shift else char.lower()
                self.shift = False
            self._insert(char)

        self.key_locked = True
        return self.typed_text, self.cursor, self.special_mode

    def _insert(self, char):
        self.typed_text = (self.typed_text[:self.cursor]
                           + char
                           + self.typed_text[self.cursor:])
        self.cursor += len(char)