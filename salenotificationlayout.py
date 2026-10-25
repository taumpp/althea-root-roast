"""Owner-selected sale strip C: fixed native pixels, measured price reservation."""
WIDTH = 470
HEIGHT = 56
TEXT_X = 56
RIGHT = 16
SLOT = (12, 11, 32)
FONT_SIZES = (11, 14, 17)  # status, item name, price; same R1 family as the UI


def geometry(width, price_width):
    """Reserve the full amount first. Very narrow screens put it below the name.

    The ordinary strip stays 56 px high. The 80 px fallback preserves the full
    price and a useful item-name area instead of colliding or shrinking text.
    """
    price_x = int(width) - RIGHT
    separator = price_x - int(price_width) - 12
    text_width = separator - TEXT_X - 12
    stacked = text_width < 80
    height = 80 if stacked else HEIGHT
    return dict(height=height, text_width=max(1, width - TEXT_X - RIGHT if stacked else text_width),
                price=(price_x, 53 if stacked else 21),
                separator=None if stacked else (separator, 14, 1, 28),
                vein=(12, height - 3, width - 24))
