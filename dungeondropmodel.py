"""Pure presentation rules for the compact boss-drop browser."""

COLUMNS = 6
VISIBLE_ROWS = 4
CELL_SIZE = 32
CELL_STEP = 36


def max_offset(count):
    return max(0, (max(0, count) + COLUMNS - 1) // COLUMNS - VISIBLE_ROWS)


def clamp_offset(offset, count):
    return min(max_offset(count), max(0, int(offset)))


def visible_entries(entries, offset):
    start = clamp_offset(offset, len(entries)) * COLUMNS
    return entries[start:start + COLUMNS * VISIBLE_ROWS]


def icon_layout(width, height, optical_offset=(0, 0)):
    scale = min(1.0, float(CELL_SIZE) / max(1, width), float(CELL_SIZE) / max(1, height))
    offset_x, offset_y = optical_offset
    return (scale,
            (CELL_SIZE - int(width * scale)) // 2 - int(round(offset_x * scale)),
            (CELL_SIZE - int(height * scale)) // 2 - int(round(offset_y * scale)))
