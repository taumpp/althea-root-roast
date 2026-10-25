"""Presentation of native boss elements; entry levels remain server data."""

# Native MOB_ELEMENT order, also used by the target-info element API.
ELEMENT_ASSETS = ("lightning", "fire", "ice", "wind", "earth", "dark")
ELEMENT_ROOT = "d:/ymir work/ui/game/crimson_ember/mount_system/"
ICON_SIZE = 24
ICON_GAP = 4
ICON_RIGHT = 548
ICON_Y = 206
NAME_X = 276
NAME_Y = 202
LEVEL_Y = 219
CAPTION_X = 269
CAPTION_Y = 198
CAPTION_WIDTH = 287
CAPTION_HEIGHT = 40
NAME_GAP = 8


def BossLevelText(bossVnum, mobData):
    level = mobData.GetMonsterLevel(bossVnum)
    return "Lv. %d" % level if level > 0 else ""


def ReadBossElements(bossVnum, enabled, mobData):
    if not enabled:
        return ()
    try:
        # SelectMob keeps the previous selection when a VNUM is missing.
        # Verify the table first so a missing boss cannot inherit its elements.
        if not mobData.GetMonsterLevel(bossVnum):
            return ()
        mobData.SelectMob(bossVnum)
        return tuple(index for index in range(len(ELEMENT_ASSETS))
                     if mobData.GetElement(index) > 0)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return ()


def ElementPositions(elements):
    width = len(elements) * (ICON_SIZE + ICON_GAP) - ICON_GAP
    left = ICON_RIGHT - max(0, width)
    return tuple((element, left + offset * (ICON_SIZE + ICON_GAP), ICON_Y)
                 for offset, element in enumerate(elements))


def BossNameWidth(elements):
    positions = ElementPositions(elements)
    right = positions[0][1] - NAME_GAP if positions else ICON_RIGHT
    return max(0, right - NAME_X)
