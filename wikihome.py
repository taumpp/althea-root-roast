# -*- coding: utf-8 -*-
"""Native homepage geometry; all gameplay stays in wikicatalog."""
ART = 'd:/ymir work/ui/wiki/home/'
SIDE = 208
ARTICLE_X = 220
ARTICLE_Y = 40
NAV_Y = 105
NAV_WIDTH = 188
NAV_HEIGHT = 38
NAV_GAP = 3
GROUP_Y = 149
GROUPS = (
    ('equipment', 'equipment', 'equipment'),
    ('chests', 'chests', 'chest'),
    ('dungeons', 'dungeons', 'dungeon'),
    ('maps', 'maps', 'boss'),
    ('progression', 'progression', 'progression'),
    ('companions', 'companions', 'pet'),
    ('crafting', 'crafting', 'crafting'),
)
CARDS = (
    ('equipment', 'start_equipment', 'equipment_short'),
    ('dungeons', 'start_dungeon', 'dungeon_short'),
    ('systems', 'start_system', 'system_short'),
)


def Measure(screen_width, screen_height):
    # Fixed native rasters: choose the profile that fits both axes instead of
    # stretching approved backgrounds or letting a tall profile leave the screen.
    compact = screen_width-48 < 880 or screen_height-128 < 540
    width = min(752 if compact else 880, screen_width-48)
    height = min(472 if compact else 540, screen_height-128)
    return compact, width, height


def HeaderSize(compact):
    return (520, 72) if compact else (648, 84)


def CardSize(compact):
    return (520, 88) if compact else (648, 112)


def CardY(compact, index):
    return (130 if compact else 150) + index*(CardSize(compact)[1]+14)
