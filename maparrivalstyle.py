# -*- coding: utf-8 -*-
"""One layout and animation contract for every map arrival title."""

ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/map_arrival/"
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 260
TITLE_CENTER_X = 316.8643533123028
TITLE_CENTER_Y = 143
TITLE_BASELINE = 158
TITLE_MAX_WIDTH = 460
FONT_SIZE = 43
TOP = 6
ART_STRIP_WIDTH = 16
ART_STRIPS = CANVAS_WIDTH // ART_STRIP_WIDTH
REVEAL_START = 0.15
REVEAL_END = 1.0
TITLE_START = 0.65
TITLE_END = 1.15
FADE_START = 3.25
DURATION = 3.90


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def animation(elapsed):
    fade = 1.0 - smooth((elapsed - FADE_START) / (DURATION - FADE_START))
    reveal = smooth((elapsed - REVEAL_START) / (REVEAL_END - REVEAL_START))
    title = smooth((elapsed - TITLE_START) / (TITLE_END - TITLE_START))
    return reveal, title * fade, fade


def viewport(screen_width, screen_height):
    # Reserve the minimap's corner at small resolutions. Keep approved 1:1 art
    # at 1024px and above; neither the painting nor font gets stretched.
    scale = max(0.1, min(1.0, (screen_width - 360.0) / CANVAS_WIDTH,
                         (screen_height - 80.0) / CANVAS_HEIGHT))
    return int(round((screen_width - CANVAS_WIDTH * scale) / 2.0)), TOP, scale


# The embedded client omits unicodedata. These font-supported canonical pairs
# are baked by tools/build_map_arrival_assets.py; runtime uses only built-ins.
# BEGIN GENERATED TITLE COMPOSITIONS
_TITLE_COMPOSITIONS = {
    '\u0300': ('AEIOUaeiou', '\xc0\xc8\xcc\xd2\xd9\xe0\xe8\xec\xf2\xf9'),
    '\u0301': ('AEIOUYaeiouyCcLlNnRrSsZz\xc5\xe5\xc6\xe6\xd8\xf8\xa8\u0391\u0395\u0397\u0399\u039f\u03a5\u03a9\u03ca\u03b1\u03b5\u03b7\u03b9\u03cb\u03bf\u03c5\u03c9\u0413\u041a\u0433\u043a', '\xc1\xc9\xcd\xd3\xda\xdd\xe1\xe9\xed\xf3\xfa\xfd\u0106\u0107\u0139\u013a\u0143\u0144\u0154\u0155\u015a\u015b\u0179\u017a\u01fa\u01fb\u01fc\u01fd\u01fe\u01ff\u0385\u0386\u0388\u0389\u038a\u038c\u038e\u038f\u0390\u03ac\u03ad\u03ae\u03af\u03b0\u03cc\u03cd\u03ce\u0403\u040c\u0453\u045c'),
    '\u0302': ('AEIOUaeiouCcGgHhJjSsWwYy', '\xc2\xca\xce\xd4\xdb\xe2\xea\xee\xf4\xfb\u0108\u0109\u011c\u011d\u0124\u0125\u0134\u0135\u015c\u015d\u0174\u0175\u0176\u0177'),
    '\u0303': ('ANOanoIiUu', '\xc3\xd1\xd5\xe3\xf1\xf5\u0128\u0129\u0168\u0169'),
    '\u0304': ('AaEeIiOoUu', '\u0100\u0101\u0112\u0113\u012a\u012b\u014c\u014d\u016a\u016b'),
    '\u0306': ('AaEeGgIiOoUu\u0423\u0418\u0438\u0443', '\u0102\u0103\u0114\u0115\u011e\u011f\u012c\u012d\u014e\u014f\u016c\u016d\u040e\u0419\u0439\u045e'),
    '\u0307': ('CcEeGgIZz', '\u010a\u010b\u0116\u0117\u0120\u0121\u0130\u017b\u017c'),
    '\u0308': ('AEIOUaeiouyY\u0399\u03a5\u03b9\u03c5\u0415\u0406\u0435\u0456', '\xc4\xcb\xcf\xd6\xdc\xe4\xeb\xef\xf6\xfc\xff\u0178\u03aa\u03ab\u03ca\u03cb\u0401\u0407\u0451\u0457'),
    '\u030a': ('AaUu', '\xc5\xe5\u016e\u016f'),
    '\u030b': ('OoUu', '\u0150\u0151\u0170\u0171'),
    '\u030c': ('CcDdEeLlNnRrSsTtZz', '\u010c\u010d\u010e\u010f\u011a\u011b\u013d\u013e\u0147\u0148\u0158\u0159\u0160\u0161\u0164\u0165\u017d\u017e'),
    '\u0326': ('SsTt', '\u0218\u0219\u021a\u021b'),
    '\u0327': ('CcGgKkLlNnRrSsTt', '\xc7\xe7\u0122\u0123\u0136\u0137\u013b\u013c\u0145\u0146\u0156\u0157\u015e\u015f\u0162\u0163'),
    '\u0328': ('AaEeIiUu', '\u0104\u0105\u0118\u0119\u012e\u012f\u0172\u0173'),
}
# END GENERATED TITLE COMPOSITIONS


def normalize_title(title):
    result = []
    for char in " ".join(title.split()):
        pair = _TITLE_COMPOSITIONS.get(char)
        if pair and result:
            index = pair[0].find(result[-1])
            if index >= 0:
                result[-1] = pair[1][index]
                continue
        result.append(char)
    return "".join(result)


def glyph_layout(title, glyphs, kerning):
    """Return glyph/codepoint positions using the shared font's ink bounds.

    Glyph metrics: advance, bearing-x, bearing-y, width, height. Positions and
    scale remain float until the final UI placement. Unknown glyphs use the
    same font's question mark, never a platform-dependent fallback font.
    """
    title = normalize_title(title)
    runs = []
    cursor = 0.0
    previous = None
    left = right = None
    for char in title:
        code = ord(char)
        if code not in glyphs:
            code = ord("?")
        advance, bearing_x, bearing_y, width, height = glyphs[code]
        if previous is not None:
            cursor += kerning.get((previous, code), 0.0)
        if width and height:
            x = cursor + bearing_x
            runs.append((code, x, bearing_y))
            left = x if left is None else min(left, x)
            right = x + width if right is None else max(right, x + width)
        cursor += advance
        previous = code
    if not runs:
        return [], 1.0
    scale = min(1.0, TITLE_MAX_WIDTH / max(1.0, right - left))
    offset_x = TITLE_CENTER_X - (left + right) * scale / 2.0
    baseline = TITLE_CENTER_Y + (TITLE_BASELINE - TITLE_CENTER_Y) * scale
    return [(code, offset_x + x * scale, baseline + y * scale)
            for code, x, y in runs], scale
