# keyboard_ui.py

import cv2
import time
from config import (
    KEYBOARD_LAYOUT,
    NUMPAD_LAYOUT,
    SPECIAL_LAYOUT,
    ARROW_LAYOUT,
    KEY_UNIT,
    KEY_HEIGHT,
    KEY_GAP,
    FRAME_WIDTH,
    DWELL_TIME
)

# Dark Mode UI Colors (BGR Format)
BG_COLOR = (55, 55, 55)            # Base key color (dark grey)
SPECIAL_BG = (40, 40, 40)          # Special key color (darker grey)
SHADOW_COLOR = (15, 15, 15)        # Drop shadow color
TEXT_COLOR = (245, 245, 245)       # Text color (off-white)
HOVER_COLOR = (120, 120, 120)      # Lighter background on hover
PRESS_COLOR = (80, 210, 80)        # Green highlight on press
PROGRESS_COLOR = (250, 180, 80)    # Light blue fill for dwell progress
BORDER_COLOR = (80, 80, 80)        # Key outline color

SPECIAL_KEYS = ["ENTER", "SPACE", "TAB", "CAPS", "SHIFT", "SHIFT ", "CTRL", "CTRL ", "WIN", "WIN ", "ALT", "ALT ", "?123", "ABC", "BACK", "BACKSPACE"]


def draw_rounded_rect(img, pt1, pt2, color, thickness=-1, r=8):
    """Draws a rounded rectangle using cv2 primitives."""
    x1, y1 = pt1
    x2, y2 = pt2
    
    # Ensure radius doesn't exceed dimensions
    r = int(min(r, abs(x2 - x1) / 2, abs(y2 - y1) / 2))
    
    if thickness < 0:
        # Fill inner rectangles and 4 corner circles
        cv2.circle(img, (x1 + r, y1 + r), r, color, -1)
        cv2.circle(img, (x2 - r, y1 + r), r, color, -1)
        cv2.circle(img, (x1 + r, y2 - r), r, color, -1)
        cv2.circle(img, (x2 - r, y2 - r), r, color, -1)
        
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
    else:
        # Draw 4 corner curves and lines
        cv2.circle(img, (x1 + r, y1 + r), r, color, thickness)
        cv2.circle(img, (x2 - r, y1 + r), r, color, thickness)
        cv2.circle(img, (x1 + r, y2 - r), r, color, thickness)
        cv2.circle(img, (x2 - r, y2 - r), r, color, thickness)
        
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
        cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
        cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)


def draw_text_display(frame, typed_text, cursor, engine):
    """Draws the futuristic text display bar at the top."""
    # Text container background and border
    draw_rounded_rect(frame, (20, 20), (FRAME_WIDTH - 20, 100), (20, 20, 20), -1, r=12)
    draw_rounded_rect(frame, (20, 20), (FRAME_WIDTH - 20, 100), (100, 100, 100), 2, r=12)
    
    # Blinking cursor effect (every 0.5 sec)
    blink = "|" if int(time.time() * 2) % 2 == 0 else " "
    display_text = typed_text[:cursor] + blink + typed_text[cursor:]
    
    # Display the text inside the bounds
    cv2.putText(
        frame,
        display_text[-50:],  # Show last 50 chars to avoid overflow
        (40, 72),
        cv2.FONT_HERSHEY_DUPLEX,
        1.1,
        (255, 255, 255),
        2
    )

    # Show Active States (CAPS, SHIFT) in top right corner of text area
    state_str = []
    if engine.caps: state_str.append("CAPS")
    if engine.shift: state_str.append("SHIFT")
    if state_str:
        cv2.putText(frame, " / ".join(state_str), (FRAME_WIDTH - 180, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)


def draw_key(frame, x1, y1, x2, y2, key, is_hovered, progress, is_pressed):
    """Draws a single key with modern 3D styling, shadows, and hover progress."""
    # 1. Shadow effect (shifted bottom-right)
    draw_rounded_rect(frame, (x1 + 4, y1 + 5), (x2 + 4, y2 + 5), SHADOW_COLOR, -1, r=8)
    
    # 2. Determine base background colors
    if is_pressed:
        bg = PRESS_COLOR
    elif is_hovered:
        bg = HOVER_COLOR
    elif key in SPECIAL_KEYS or key in ["↑", "↓", "←", "→"]:
        bg = SPECIAL_BG
    else:
        bg = BG_COLOR
        
    # 3. Dynamic popup/shrink animation
    # Press visually pushes the key down
    base_x1, base_y1, base_x2, base_y2 = x1, y1, x2, y2
    if is_pressed:
        base_x1 += 2; base_y1 += 2; base_x2 -= 2; base_y2 -= 2
    elif is_hovered:
        base_x1 -= 2; base_y1 -= 2; base_x2 += 2; base_y2 += 2

    # Draw Main Key Box
    draw_rounded_rect(frame, (base_x1, base_y1), (base_x2, base_y2), bg, -1, r=8)
    # Draw Inner Outline (adds 3D separation effect)
    draw_rounded_rect(frame, (base_x1, base_y1), (base_x2, base_y2), BORDER_COLOR, 1, r=8)
    
    # 4. Progress bar (fill animation while lingering)
    if is_hovered and progress > 0 and not is_pressed:
        fill_x = int((base_x2 - base_x1) * progress)
        # We cap the visual width to avoid jumping outside corners
        capped_x2 = min(base_x1 + fill_x, base_x2 - 1)
        # Simple progress bar line at the bottom
        if capped_x2 > base_x1 + 10:
             cv2.line(frame, (base_x1 + 8, base_y2 - 6), (capped_x2 - 8, base_y2 - 6), PROGRESS_COLOR, 4)

    # 5. Draw text centered
    font = cv2.FONT_HERSHEY_DUPLEX
    scale = 0.55 if len(key) > 4 else 0.75
    thickness = 1 if len(key) > 4 else 2
    
    ts = cv2.getTextSize(key, font, scale, thickness)[0]
    tx = base_x1 + (base_x2 - base_x1 - ts[0]) // 2
    ty = base_y1 + (base_y2 - base_y1 + ts[1]) // 2
    
    cv2.putText(frame, key, (tx, ty), font, scale, TEXT_COLOR, thickness)


def row_width(row):
    return sum(int(KEY_UNIT * w) for _, w in row) + KEY_GAP * (len(row) - 1)


def draw_keyboard(frame, cx, cy, engine):
    """Calculates layout bounding boxes and routes them to `draw_key`."""
    hovered_key = None
    special_mode = engine.special_mode
    now = time.time()

    # Apply a subtle semi-transparent overlay to the entire screen for better visibility
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 110), (FRAME_WIDTH, 720), (10, 10, 10), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    # -------- SELECT MAIN LAYOUT --------
    main_layout = SPECIAL_LAYOUT if special_mode else KEYBOARD_LAYOUT

    # -------- CALCULATE CENTER X --------
    max_row_w = max(row_width(row) for row in main_layout)
    start_x = (FRAME_WIDTH - max_row_w) // 2
    start_y = 150

    # We store the final 'hovered_key' based on coordinates.
    # We also check the engine's current state to calculate the progress visually.
    
    def process_key_grid(layout, start_x, start_y):
        nonlocal hovered_key
        y = start_y
        for row in layout:
            x = start_x
            for key, w_mul in row:
                w = int(KEY_UNIT * w_mul)
                x1, y1 = x, y
                x2, y2 = x + w, y + KEY_HEIGHT
                
                # Check collision safely
                is_hovered = False
                if cx is not None and cy is not None:
                    if x1 < cx < x2 and y1 < cy < y2:
                        is_hovered = True
                        hovered_key = key

                # Check Engine state for correct animations
                is_active = (engine.last_key == key and not engine.key_locked)
                is_pressed = (engine.last_key == key and engine.key_locked)
                
                progress = 0.0
                if is_active and engine.hover_start > 0:
                    progress = min(1.0, (now - engine.hover_start) / DWELL_TIME)

                draw_key(frame, x1, y1, x2, y2, key, is_hovered, progress, is_pressed)

                x += w + KEY_GAP
            y += KEY_HEIGHT + KEY_GAP
        return y

    # -------- DRAW MAIN KEYBOARD --------
    process_key_grid(main_layout, start_x, start_y)

    # -------- NUMPAD (RIGHT SIDE) --------
    np_x = start_x + max_row_w + 50
    np_y = start_y
    y_after_numpad = process_key_grid(NUMPAD_LAYOUT, np_x, np_y)

    # -------- ARROW KEYS (BOTTOM CENTER) --------
    arrow_w = max(row_width(row) for row in ARROW_LAYOUT)
    arrow_x = (FRAME_WIDTH - arrow_w) // 2
    arrow_y = y_after_numpad + 20
    process_key_grid(ARROW_LAYOUT, arrow_x, arrow_y)

    return hovered_key
