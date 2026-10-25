"""Shared, proto-driven race and element presentation for monster UI."""

RACE_ASSETS = (
    ("ANIMAL", "animal", "TARGET_INFO_RACE_ANIMAL"),
    ("UNDEAD", "undead", "TARGET_INFO_RACE_UNDEAD"),
    ("DEVIL", "devil", "TARGET_INFO_RACE_DEVIL"),
    ("HUMAN", "human", "TARGET_INFO_RACE_HUMAN"),
    ("ORC", "orc", "TARGET_INFO_RACE_ORC"),
    ("MILGYO", "mystic", "TARGET_INFO_RACE_MILGYO"),
    ("INSECT", "insect", "TARGET_INFO_RACE_INSECT"),
    ("DESERT", "desert", "TARGET_INFO_RACE_DESERT"),
    ("TREE", "tree", "TARGET_INFO_RACE_TREE"),
    ("ZODIAC", "zodiac", "TARGET_INFO_RACE_ZODIAC"),
)
ELEMENT_NAMES = ("ELEC", "FIRE", "ICE", "WIND", "EARTH", "DARK")
ELEMENT_ASSETS = ("lightning", "fire", "ice", "wind", "earth", "dark")
RACE_ROOT = "monster_indicators/"
ELEMENT_ROOT = "d:/ymir work/ui/game/12zi/element/"
SMALL_ELEMENT_ROOT = "d:/ymir work/ui/game/crimson_ember/mount_system/"
ELEMENT_FILES = ("elect.sub", "fire.sub", "ice.sub", "wind.sub", "earth.sub", "dark.sub")


def ReadMonster(vnum, elementsEnabled, mobData):
    """Never inherit native selection when SelectMob receives an absent VNUM."""
    try:
        if not vnum or not mobData.GetMonsterLevel(vnum):
            return (), (), False
        mobData.SelectMob(vnum)
        flags = mobData.GetRaceFlag()
        races = tuple(index for index, entry in enumerate(RACE_ASSETS)
                      if flags & getattr(mobData, "RACE_FLAG_" + entry[0], 0))
        elements = tuple(index for index in range(len(ELEMENT_NAMES))
                         if elementsEnabled and mobData.GetElement(index) > 0)
        return races, elements, bool(mobData.IsStone())
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return (), (), False


def TooltipLines(races, elements, isStone, locale):
    raceNames = [getattr(locale, RACE_ASSETS[index][2]) for index in races]
    if not raceNames:
        raceNames = [locale.TARGET_INFO_RACE_METIN if isStone else locale.TARGET_INFO_RACE_UNKNOWN]
    elementNames = [getattr(locale, "TARGET_INFO_RACE_" + ELEMENT_NAMES[index]) for index in elements]
    lines = (locale.TARGET_INFO_RACE % ", ".join(raceNames),)
    if elementNames:
        lines += (locale.MONSTER_INFO_ELEMENT % ", ".join(elementNames),)
    return lines


def IndicatorAssets(races, elements, size=39):
    # One race-group symbol keeps multi-flag protos bounded; its tooltip names
    # every matching race, never just the representative silhouette.
    result = []
    if races:
        result.append(RACE_ROOT + RACE_ASSETS[races[0]][1] + "_%d.png" % size)
    if size == 24:
        result.extend(SMALL_ELEMENT_ROOT + "element_%s_24.png" % ELEMENT_ASSETS[index] for index in elements)
    else:
        result.extend(ELEMENT_ROOT + ELEMENT_FILES[index] for index in elements)
    return tuple(result)


def RowWidth(count, size, gap):
    return max(0, count * (size + gap) - gap)
