# -*- coding: utf-8 -*-
"""Item Shop navigation data. IDs are the server ishop_data.categoryType values.

Order is presentation only: never renumber existing server categories.
"""
# Category 0 "Balicek" (package) was removed on 2026-10-16 (Dalton): it never had an
# offer; server SQL162 moves any offer still in category 0 to 6 "Ostatni".
CATEGORIES = (
    (1, "CATEGORY_1_NAME", ()),
    (2, "CATEGORY_2_NAME", ()),
    (3, "CATEGORY_3_NAME", ()),
    (8, "CATEGORY_8_NAME", ()),
    (4, "CATEGORY_4_NAME", ("SHINING_ARMOR_CATEGORY", "SHINING_WEAPON_CATEGORY")),
    (5, "CATEGORY_5_NAME", ()),
    (6, "CATEGORY_6_NAME", ()),
    (7, "CATEGORY_7_NAME", ()),
    (9, "CATEGORY_9_NAME", ()),
)

# Approved sidebar A: same row pitch, a bounded viewport, proportional thumb.
LIST_POSITION = (10, 76)
LIST_WIDTH = 150
VIEWPORT_HEIGHT = 450
ROW_PITCH = 50
SCROLL_POSITION = (161, 76)
SCROLL_HEIGHT = VIEWPORT_HEIGHT
