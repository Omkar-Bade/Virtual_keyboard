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
    if engine.caps:  badges.append("CAPS")
    if engine.shift: badges.append("SHIFT")
    if engine.num_lock: badges.append("NUM")
    if badges:
        cv2.putText(frame, "  ".join(badges), (bx2-140, by1+54),
                    cv2.FONT_HERSHEY_PLAIN, 1.1, STATE_COL, 1, cv2.LINE_AA)


def draw_keyboard(frame, cx, cy, engine):
    hovered_key = None
    now         = time.time()

    _fill(frame, 0, 100, FRAME_WIDTH, FRAME_HEIGHT, BG_PANEL)
    cv2.line(frame, (0, 100), (FRAME_WIDTH, 100), (52, 46, 40), 1)

    main_layout = SPECIAL_LAYOUT if engine.special_mode else KEYBOARD_LAYOUT

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

    def put_key(key, kx1, ky1, kx2, ky2,
                override_bg=None, override_text=None):
        nonlocal hovered_key
        is_hov = (cx is not None and cy is not None
                  and kx1 < cx < kx2 and ky1 < cy < ky2)
        if is_hov:
            hovered_key = key
        is_act  = (engine.last_key == key and not engine.key_locked)
        is_pres = (engine.last_key == key and engine.key_locked)
        prog    = 0.0
        if is_act and engine.hover_start > 0:
            prog = min(1.0, (now - engine.hover_start) / DWELL_TIME)
        _draw_key(frame, kx1, ky1, kx2, ky2, key,
                  is_hov, prog, is_pres, override_bg, override_text)

    def grid(layout, sx, sy):
        y = sy
        for row in layout:
            x = sx
            for key, w_mul in row:
                w = int(KU * w_mul)
                put_key(key, x, y, x + w, y + KH)
                x += w + GAP
            y += KH + GAP
        return y

    # ── rows 1–4 (number row to shift row) ──
    rows_1_to_4 = main_layout[:4]
    y_after_r4  = grid(rows_1_to_4, main_x, start_y)

    # ── bottom row ──────────────────────────────────────────
    row5_y  = y_after_r4 + GAP
    ctrl_w  = int(KU * 1.5)
    win_w   = int(KU * 1.2)
    alt_w   = int(KU * 1.2)
    arrow_w = KU

    arrow_cluster_w = 3 * arrow_w + 2 * GAP
    fixed_left      = ctrl_w + win_w + alt_w + 3 * GAP
    fixed_right     = alt_w + ctrl_w + 2 * GAP + arrow_cluster_w + GAP
    space_w         = main_w - fixed_left - fixed_right

    bx = main_x
    by = row5_y

    put_key("CTRL",  bx, by, bx + ctrl_w,  by + KH); bx += ctrl_w  + GAP
    put_key("WIN",   bx, by, bx + win_w,   by + KH); bx += win_w   + GAP
    put_key("ALT",   bx, by, bx + alt_w,   by + KH); bx += alt_w   + GAP
    put_key("SPACE", bx, by, bx + space_w, by + KH); bx += space_w + GAP
    put_key("ALT ",  bx, by, bx + alt_w,   by + KH); bx += alt_w   + GAP
    put_key("CTRL ", bx, by, bx + ctrl_w,  by + KH); bx += ctrl_w  + GAP

    # arrow inverted-T
    half_h  = (KH - GAP) // 2
    up_y1   = row5_y
    up_y2   = row5_y + half_h
    down_y1 = up_y2 + GAP
    down_y2 = row5_y + KH

    up_x1 = bx + arrow_w + GAP
    put_key("↑", up_x1, up_y1, up_x1 + arrow_w, up_y2)

    ax = bx
    for sym in ["←", "↓", "→"]:
        put_key(sym, ax, down_y1, ax + arrow_w, down_y2)
        ax += arrow_w + GAP

    # ── numpad ──────────────────────────────────────────────
    cv2.putText(frame, "NUM", (np_x + 2, start_y - 6),
                cv2.FONT_HERSHEY_PLAIN, 0.8, TEXT_DIM, 1, cv2.LINE_AA)

    ny = start_y
    top_row = [("NUMLK", KEY_NUMLK, TEXT_NUMLK),
               ("/",     KEY_NUMOP, TEXT_NUMOP),
               ("*",     KEY_NUMOP, TEXT_NUMOP),
               ("-",     KEY_NUMOP, TEXT_NUMOP)]
    for i, (key, bg, tc) in enumerate(top_row):
        nx1 = np_x + i * (KU + GAP)
        put_key(key, nx1, ny, nx1 + KU, ny + KH, bg, tc)
    ny += KH + GAP

    digits = [["NP_7","NP_8","NP_9"], ["NP_4","NP_5","NP_6"], ["NP_1","NP_2","NP_3"]]
    for row_keys in digits:
        for ci, key in enumerate(row_keys):
            nx1 = np_x + ci * (KU + GAP)
            put_key(key, nx1, ny, nx1 + KU, ny + KH)
        ny += KH + GAP

    put_key("NP_0", np_x, ny, np_x + 2*KU + GAP, ny + KH)
    put_key("NP_.", np_x + 2*KU + 2*GAP, ny, np_x + 3*KU + 2*GAP, ny + KH)

    tall_x1 = np_x + 3*KU + 3*GAP
    tall_y1 = start_y + KH + GAP
    put_key("+",      tall_x1, tall_y1, tall_x1+KU, tall_y1+KH2, KEY_NUMOP, TEXT_NUMOP)
    ent_y1  = tall_y1 + KH2 + GAP
    put_key("NP_ENT", tall_x1, ent_y1,  tall_x1+KU, ent_y1+KH2,  KEY_NUMOP, TEXT_NUMOP)

    return hovered_key