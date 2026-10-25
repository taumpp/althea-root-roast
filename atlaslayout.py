"""Pixel geometry for the world atlas and its shared outer frame."""

import math


TITLE_HEIGHT = 23
FRAME_WIDTH = 2
MAX_IMAGE_SIZE = 512
SCREEN_MARGIN = 16
TASKBAR_SPACE = 80
RESIZE_GRIP = 8
# The window is at least this wide (the R1 title in Cinzel must fit beside the X); a narrower map is centred in it.
MIN_WINDOW_WIDTH = 260
# A long narrow atlas (over 2:1) is shown at native size when the screen allows: its short side would otherwise
# shrink below this (the 256x768 pirate cave was 171x512).
MIN_SHORT_SIDE = 256

# Maps with several separate floors show only the floor the player stands on (owner 11. 10. 2026):
# {map name: (atlas image size, metres per atlas pixel, ((floor label, (x0, y0, x1, y1)), ...))} in atlas pixels.
# The engine always maps the whole MapSize onto the image (markers stay exact); the renderer is moved by the crop
# origin and its scissor rectangle cuts the rest. Every floor is shown in one box (the largest floor) centred on
# it, so a teleport between floors swaps the picture without resizing the window. A different image size (an old
# pack) shows the whole image.
ATLAS_FLOORS = {
    # tools/import_ghost_pirate_cave.py ATLAS_FLOORS: entry floor, second floor, third floor (d.jump_all)
    "plechito_pirate_cave_ghost": ((256, 768), 2.0, (
        ("I", (34, 8, 148, 204)), ("II", (28, 334, 160, 456)), ("III", (38, 594, 158, 718)))),
}


def floor_index(map_name, local_position):
    """Index of the floor at the player's local position ((x, y) in game units, 100 per metre), or None."""
    entry = ATLAS_FLOORS.get(map_name)
    if not entry or local_position is None:
        return None
    _, metres_per_pixel, floors = entry
    # the engine's pixel y may come signed: the atlas works with the distance from the map origin
    px = abs(float(local_position[0])) / 100.0 / metres_per_pixel
    py = abs(float(local_position[1])) / 100.0 / metres_per_pixel

    def distance(rect):
        x0, y0, x1, y1 = rect
        return max(x0 - px, 0, px - x1) ** 2 + max(y0 - py, 0, py - y1) ** 2
    return min(range(len(floors)), key=lambda index: (distance(floors[index][1]), index))


def crop(map_name, image_width, image_height, local_position=None):
    """(x0, y0, width, height, floor label) of the atlas part to show, at scale 1.0. x0 / y0 may be negative:
    the box of the largest floor centred on the current one (nothing is drawn outside the image)."""
    entry = ATLAS_FLOORS.get(map_name)
    if not entry or entry[0] != (image_width, image_height):
        return 0, 0, image_width, image_height, ""
    floors = entry[2]
    index = floor_index(map_name, local_position)
    label, (x0, y0, x1, y1) = floors[index or 0]
    width = max(r[2] - r[0] for _, r in floors)
    height = max(r[3] - r[1] for _, r in floors)
    return (x0 + x1 - width) // 2, (y0 + y1 - height) // 2, width, height, label


def view(image_width, crop_origin, scale):
    """The renderer width (at least MIN_WINDOW_WIDTH with the frame) and the offset of the atlas inside it, so the
    crop of width image_width (already scaled) is centred: (view_width, (dx, dy))."""
    view_width = max(int(image_width), MIN_WINDOW_WIDTH - 2 * FRAME_WIDTH)
    x0, y0 = crop_origin
    dx = int(round((view_width - image_width) / 2.0 - x0 * scale))
    return view_width, (dx, -int(round(y0 * scale)))


def fit(image_width, image_height, screen_width, screen_height, preferred_size=None, title_height=TITLE_HEIGHT):
    """title_height: the header of the frame (TITLE_HEIGHT for the original board, more for the R1 header)."""
    if image_width <= 0 or image_height <= 0:
        return None

    available_width = max(1, screen_width - 2 * SCREEN_MARGIN - 2 * FRAME_WIDTH)
    available_height = max(1, screen_height - 2 * SCREEN_MARGIN
                           - title_height - FRAME_WIDTH - TASKBAR_SPACE)
    if preferred_size is None:
        longest, shortest = max(image_width, image_height), min(image_width, image_height)
        # ordinary maps: the long side up to MAX_IMAGE_SIZE; over 2:1 the short side keeps MIN_SHORT_SIDE (max 1:1)
        cap = max(min(MAX_IMAGE_SIZE, longest) / float(longest), min(1.0, MIN_SHORT_SIDE / float(shortest)))
    else:
        cap = float(preferred_size) / max(image_width, image_height)
    scale = min(cap,
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


def resize(image_size, start_rect, edge, delta, screen_size, start_scale=None, title_height=TITLE_HEIGHT):
    """Uniformly scale from the press snapshot, keeping the opposite edge fixed."""
    iw, ih = image_size
    x, y, width, height = start_rect
    ex, ey = edge
    dx, dy = delta
    sw, sh = screen_size
    border_w, border_h = 2 * FRAME_WIDTH, title_height + FRAME_WIDTH
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
