# keyboard_ui.py — Minimal / Clean / Flat (Blue-Cyan palette)
#
# Bottom row layout:
#   [CTRL][WIN][ALT][        SPACE        ][ALT][CTRL]  [ ↑ ]
#                                                      [←][↓][→]
#
# Numpad (right block):
#   [NUMLK][/][*][-]
#   [7][8][9] [+] (tall)
#   [4][5][6]
#   [1][2][3] [ENT] (tall)
#   [  0  ][.]

import cv2
import numpy as np
import time

from config import (
    KEYBOARD_LAYOUT,
    NUMPAD_LAYOUT,
    SPECIAL_LAYOUT,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    DWELL_TIME,
)

KU  = 46
KH  = 48
KH2 = KH * 2 + 5
GAP = 5

BG_PANEL    = ( 28,  22,  18)
KEY_NORMAL  = ( 42,  38,  34)
KEY_SPECIAL = ( 55,  48,  42)
KEY_NUMOP   = ( 30,  42,  48)
KEY_NUMLK   = ( 30,  42,  22)
KEY_HOVER   = (120, 100,  40)
KEY_PRESSED = (210, 195,  65)
TEXT_ON     = (235, 225, 215)
TEXT_NUMOP  = (205, 185,  50)
TEXT_NUMLK  = (  0, 165, 232)
TEXT_DIM    = (110, 100,  90)
ACCENT      = (205, 185,  50)
DISPLAY_BG  = ( 20,  16,  13)
STATE_COL   = (175, 155,  38)

SPECIAL_KEYS = {
    "ENTER","SPACE","TAB","CAPS",
    "SHIFT","SHIFT ","CTRL","CTRL ",
    "WIN","ALT","ALT ","BACK","BACKSPACE",
    "?123","ABC",
}

ARROW_MAP = {"↑": "UP", "↓": "DOWN", "←": "LEFT", "→": "RIGHT"}


# ---------------------------------------------------------------------------
# Low-level drawing helpers
# ---------------------------------------------------------------------------

def _fill(img, x1, y1, x2, y2, col):
    cv2.rectangle(img, (x1, y1), (x2, y2), col, -1)

def _stroke(img, x1, y1, x2, y2, col, t=1):
    cv2.rectangle(img, (x1, y1), (x2, y2), col, t)

def _text_centred(img, txt, x1, y1, x2, y2, col, scale=0.60, thick=1):
    font = cv2.FONT_HERSHEY_DUPLEX
    if len(txt) > 4:
        scale = 0.42
    (tw, th), _ = cv2.getTextSize(txt, font, scale, thick)
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 + th) // 2
    cv2.putText(img, txt, (tx, ty), font, scale, col, thick, cv2.LINE_AA)

def _arrow(img, x1, y1, x2, y2, direction, col):
    mx = (x1 + x2) // 2
    my = (y1 + y2) // 2
    s  = min(x2 - x1, y2 - y1) // 3
    if   direction == "UP":    pts = [[mx, my-s],[mx-s, my+s],[mx+s, my+s]]
    elif direction == "DOWN":  pts = [[mx, my+s],[mx-s, my-s],[mx+s, my-s]]
    elif direction == "LEFT":  pts = [[mx-s, my],[mx+s, my-s],[mx+s, my+s]]
    elif direction == "RIGHT": pts = [[mx+s, my],[mx-s, my-s],[mx-s, my+s]]
    else: return
    cv2.fillPoly(img, [np.array(pts, np.int32)], col)


# ---------------------------------------------------------------------------
# Per-key renderer (only called for hover/pressed keys or first paint)
# ---------------------------------------------------------------------------

def _draw_key(frame, x1, y1, x2, y2, key,
              is_hov, progress, is_pressed,
              override_bg=None, override_text=None):
    arrow_dir = ARROW_MAP.get(key)
    is_spec   = (key in SPECIAL_KEYS or arrow_dir is not None)

    if override_bg:
        bg = override_bg
    elif is_pressed:
        bg = KEY_PRESSED
    elif is_hov:
        bg = KEY_HOVER
    elif is_spec:
        bg = KEY_SPECIAL
    else:
        bg = KEY_NORMAL

    _fill(frame, x1, y1, x2, y2, bg)

    border = ACCENT if is_hov else (52, 46, 40)
    _stroke(frame, x1, y1, x2, y2, border, 1)

    if is_hov and progress > 0 and not is_pressed:
        bw = int((x2 - x1 - 4) * progress)
        if bw > 2:
            cv2.line(frame, (x1+2, y2-3), (x1+2+bw, y2-3), ACCENT, 3)

    if is_pressed:
        cv2.line(frame, (x1, y1), (x2, y1), ACCENT, 2)

    lc = (DISPLAY_BG if is_pressed else (override_text or TEXT_ON))
    if arrow_dir:
        _arrow(frame, x1, y1, x2, y2, arrow_dir, lc)
    else:
        disp_key = key
        if key.startswith("NP_") and key != "NP_ENT":
            disp_key = key[3:]
        elif key == "NP_ENT":
            disp_key = "ENT"
        _text_centred(frame, disp_key, x1, y1, x2, y2, lc)


# ---------------------------------------------------------------------------
# Geometry cache — computed once at import time, never again
# ---------------------------------------------------------------------------
# Each entry in _KEY_RECTS_* is a tuple:
#   (key, x1, y1, x2, y2, override_bg, override_text)
# _STATIC_BG_* is a pre-rendered numpy image of the keyboard with no
#   hover/press state.  Each frame we memcopy it into the live frame then
#   only overdraw the single hovered/pressed key.

def _build_geometry(main_layout):
    """Return (key_rects, static_bg) for the given main layout."""
    key_rects = []

    def row_w(row):
        return sum(int(KU * w) for _, w in row) + GAP * (len(row) - 1)

    main_w = max(row_w(r) for r in main_layout)
    np_w   = 3 * KU + 2 * GAP + GAP + KU

    SECTION_GAP = 20
    total_w     = main_w + SECTION_GAP + np_w
    ox          = (FRAME_WIDTH - total_w) // 2
    start_y     = 108

    main_x = ox
    np_x   = ox + main_w + SECTION_GAP

    def record(key, kx1, ky1, kx2, ky2, obg=None, otxt=None):
        key_rects.append((key, kx1, ky1, kx2, ky2, obg, otxt))

    # rows 1–4
    y = start_y
    for row in main_layout[:4]:
        x = main_x
        for key, w_mul in row:
            w = int(KU * w_mul)
            record(key, x, y, x + w, y + KH)
            x += w + GAP
        y += KH + GAP

    # bottom row
    row5_y = y + GAP
    ctrl_w = int(KU * 1.5)
    win_w  = int(KU * 1.2)
    alt_w  = int(KU * 1.2)
    arrow_w = KU

    arrow_cluster_w = 3 * arrow_w + 2 * GAP
    fixed_left      = ctrl_w + win_w + alt_w + 3 * GAP
    fixed_right     = alt_w + ctrl_w + 2 * GAP + arrow_cluster_w + GAP
    space_w         = main_w - fixed_left - fixed_right

    bx = main_x
    by = row5_y
    for key, kw in [("CTRL", ctrl_w), ("WIN", win_w), ("ALT", alt_w),
                    ("SPACE", space_w), ("ALT ", alt_w), ("CTRL ", ctrl_w)]:
        record(key, bx, by, bx + kw, by + KH)
        bx += kw + GAP

    # arrow cluster
    half_h  = (KH - GAP) // 2
    up_y1   = row5_y
    up_y2   = row5_y + half_h
    down_y1 = up_y2 + GAP
    down_y2 = row5_y + KH
    up_x1   = bx + arrow_w + GAP
    record("↑", up_x1, up_y1, up_x1 + arrow_w, up_y2)
    ax = bx
    for sym in ["←", "↓", "→"]:
        record(sym, ax, down_y1, ax + arrow_w, down_y2)
        ax += arrow_w + GAP

    # numpad top row
    ny = start_y
    numpad_top = [("NUMLK", KEY_NUMLK, TEXT_NUMLK),
                  ("/",     KEY_NUMOP, TEXT_NUMOP),
                  ("*",     KEY_NUMOP, TEXT_NUMOP),
                  ("-",     KEY_NUMOP, TEXT_NUMOP)]
    for i, (key, bg, tc) in enumerate(numpad_top):
        nx1 = np_x + i * (KU + GAP)
        record(key, nx1, ny, nx1 + KU, ny + KH, bg, tc)
    ny += KH + GAP

    # numpad digit rows
    digits = [["NP_7","NP_8","NP_9"],
              ["NP_4","NP_5","NP_6"],
              ["NP_1","NP_2","NP_3"]]
    for row_keys in digits:
        for ci, key in enumerate(row_keys):
            nx1 = np_x + ci * (KU + GAP)
            record(key, nx1, ny, nx1 + KU, ny + KH)
        ny += KH + GAP

    record("NP_0", np_x,            ny, np_x + 2*KU + GAP,    ny + KH)
    record("NP_.", np_x + 2*KU + 2*GAP, ny, np_x + 3*KU + 2*GAP, ny + KH)

    tall_x1 = np_x + 3*KU + 3*GAP
    tall_y1 = start_y + KH + GAP
    record("+",      tall_x1, tall_y1, tall_x1+KU, tall_y1+KH2, KEY_NUMOP, TEXT_NUMOP)
    ent_y1 = tall_y1 + KH2 + GAP
    record("NP_ENT", tall_x1, ent_y1,  tall_x1+KU, ent_y1+KH2,  KEY_NUMOP, TEXT_NUMOP)

    # ---- build static background image ----
    static_bg = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), BG_PANEL, dtype=np.uint8)
    cv2.line(static_bg, (0, 100), (FRAME_WIDTH, 100), (52, 46, 40), 1)
    cv2.putText(static_bg, "NUM", (np_x + 2, start_y - 6),
                cv2.FONT_HERSHEY_PLAIN, 0.8, TEXT_DIM, 1, cv2.LINE_AA)
    for (key, x1, y1, x2, y2, obg, otxt) in key_rects:
        _draw_key(static_bg, x1, y1, x2, y2, key,
                  False, 0.0, False, obg, otxt)

    return key_rects, static_bg, np_x, start_y


# Pre-build geometry for both keyboard modes at import time
_RECTS_MAIN,    _BG_MAIN,    _NP_X_MAIN,    _START_Y_MAIN    = _build_geometry(KEYBOARD_LAYOUT)
_RECTS_SPECIAL, _BG_SPECIAL, _NP_X_SPECIAL, _START_Y_SPECIAL = _build_geometry(SPECIAL_LAYOUT)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def draw_text_display(frame, typed_text, cursor, engine):
    PAD = 20
    bx1, by1, bx2, by2 = PAD, 12, FRAME_WIDTH - PAD, 88
    _fill(frame, bx1, by1, bx2, by2, DISPLAY_BG)
    cv2.line(frame, (bx1, by2), (bx2, by2), ACCENT, 2)
    cv2.putText(frame, "INPUT", (bx1+8, by1+14),
                cv2.FONT_HERSHEY_PLAIN, 0.85, ACCENT, 1)

    blink   = "|" if int(time.time() * 2) % 2 == 0 else " "
    display = (typed_text[:cursor] + blink + typed_text[cursor:])[-52:]
    cv2.putText(frame, display, (bx1+10, by1+52),
                cv2.FONT_HERSHEY_DUPLEX, 0.92, TEXT_ON, 1, cv2.LINE_AA)

    badges = []
    if engine.caps:     badges.append("CAPS")
    if engine.shift:    badges.append("SHIFT")
    if engine.num_lock: badges.append("NUM")
    if badges:
        cv2.putText(frame, "  ".join(badges), (bx2-140, by1+54),
                    cv2.FONT_HERSHEY_PLAIN, 1.1, STATE_COL, 1, cv2.LINE_AA)


def draw_keyboard(frame, cx, cy, engine):
    """
    Blits the cached static keyboard background, then only redraws the
    single hovered/pressed key.  All key bounding-box geometry is pre-
    computed — no per-frame layout arithmetic.
    """
    # Pick the correct cached set
    if engine.special_mode:
        key_rects, static_bg = _RECTS_SPECIAL, _BG_SPECIAL
    else:
        key_rects, static_bg = _RECTS_MAIN, _BG_MAIN

    # Fast blit: copy static background into the keyboard region of frame
    frame[100:, :] = static_bg[100:]

    now         = time.time()
    hovered_key = None

    for (key, x1, y1, x2, y2, obg, otxt) in key_rects:
        is_hov = (cx is not None and cy is not None
                  and x1 < cx < x2 and y1 < cy < y2)
        if is_hov:
            hovered_key = key

        is_act  = (engine.last_key == key and not engine.key_locked)
        is_pres = (engine.last_key == key and engine.key_locked)

        # Only redraw this key if its visual state differs from idle
        if is_hov or is_act or is_pres:
            prog = 0.0
            if is_act and engine.hover_start > 0:
                prog = min(1.0, (now - engine.hover_start) / DWELL_TIME)
            _draw_key(frame, x1, y1, x2, y2, key,
                      is_hov, prog, is_pres, obg, otxt)

    return hovered_key