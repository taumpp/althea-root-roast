"""Pixel geometry for the world atlas and its shared outer frame."""

import math


TITLE_HEIGHT = 23
FRAME_WIDTH = 2
MAX_IMAGE_SIZE = 512
SCREEN_MARGIN = 16
TASKBAR_SPACE = 80
RESIZE_GRIP = 8


def fit(image_width, image_height, screen_width, screen_height, preferred_size=None):
    if image_width <= 0 or image_height <= 0:
        return None

    available_width = max(1, screen_width - 2 * SCREEN_MARGIN - 2 * FRAME_WIDTH)
    available_height = max(1, screen_height - 2 * SCREEN_MARGIN
                           - TITLE_HEIGHT - FRAME_WIDTH - TASKBAR_SPACE)
    limit = min(MAX_IMAGE_SIZE, max(image_width, image_height)) if preferred_size is None else preferred_size
    scale = min(float(limit) / max(image_width, image_height),
                float(available_width) / image_width,
                float(available_height) / image_height)
    # Floating-point multiplication can land just above an integer limit.
    width = min(available_width, math.ceil(image_width * scale))
    height = min(available_height, math.ceil(image_height * scale))
    return scale, int(width), int(height)


def clamp_position(x, y, width, height, screen_width, screen_height):
    max_x = max(SCREEN_MARGIN, screen_width - width - SCREEN_MARGIN)
    max_y = max(SCREEN_MARGIN, screen_height - height - TASKBAR_SPACE - SCREEN_MARGIN)
    return (int(max(SCREEN_MARGIN, min(x, max_x))),
            int(max(SCREEN_MARGIN, min(y, max_y))))


def grips(width, height):
    """An external hit ring: never cover the title, close button or map clicks."""
    size = RESIZE_GRIP
    return {(-1, -1): (-size, -size, size, size),
            (0, -1): (0, -size, width, size),
            (1, -1): (width, -size, size, size),
            (-1, 0): (-size, 0, size, height),
            (1, 0): (width, 0, size, height),
            (-1, 1): (-size, height, size, size),
            (0, 1): (0, height, width, size),
            (1, 1): (width, height, size, size)}


def resize(image_size, start_rect, edge, delta, screen_size, start_scale=None):
    """Uniformly scale from the press snapshot, keeping the opposite edge fixed."""
    iw, ih = image_size
    x, y, width, height = start_rect
    ex, ey = edge
    dx, dy = delta
    sw, sh = screen_size
    border_w, border_h = 2 * FRAME_WIDTH, TITLE_HEIGHT + FRAME_WIDTH
    scale = float(width - border_w) / iw if start_scale is None else start_scale
    # Project a corner drag onto the image diagonal; one-axis grips use that axis.
    scale += (ex * dx * iw + ey * dy * ih) / float(ex * ex * iw * iw + ey * ey * ih * ih)
    anchor_x = x + (width if ex < 0 else width / 2.0 if ex == 0 else 0)
    anchor_y = y + (height if ey < 0 else height / 2.0 if ey == 0 else 0)
    left, right = anchor_x - SCREEN_MARGIN, sw - SCREEN_MARGIN - anchor_x
    top, bottom = anchor_y - SCREEN_MARGIN, sh - TASKBAR_SPACE - SCREEN_MARGIN - anchor_y
    available_w = left if ex < 0 else right if ex > 0 else 2 * min(left, right)
    available_h = top if ey < 0 else bottom if ey > 0 else 2 * min(top, bottom)
    maximum = max(0.001, min((available_w - border_w) / iw, (available_h - border_h) / ih))
    minimum = min(maximum, max(160.0 / iw, 128.0 / ih))
    scale = max(minimum, min(scale, maximum))
    image_w, image_h = int(math.ceil(iw * scale)), int(math.ceil(ih * scale))
    width, height = image_w + border_w, image_h + border_h
    x = anchor_x - (width if ex < 0 else width / 2.0 if ex == 0 else 0)
    y = anchor_y - (height if ey < 0 else height / 2.0 if ey == 0 else 0)
    x, y = clamp_position(x, y, width, height, sw, sh)
    return scale, image_w, image_h, x, y
