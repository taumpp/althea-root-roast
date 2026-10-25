# -*- coding: utf-8 -*-
"""Complete active totals from the server; catalog labels come from existing UI data."""
import bonuslabels
import itembonuspresentation
import mountcorebonus

# Shared authoritative totals for character details and owned inventory equipment.
totals = itembonuspresentation.EquipmentTotals("/character_bonuses", 65535)
SCALE = 1000000
# Presentation selection; numeric fallbacks are immutable APPLY identities.
COMBAT_APPLIES = (
    ('APPLY_MAX_HP', 1),
    ('APPLY_MAX_SP', 2),
    ('APPLY_ATT_SPEED', 7),
    ('APPLY_MOV_SPEED', 8),
    ('APPLY_CAST_SPEED', 9),
    ('APPLY_HP_REGEN', 10),
    ('APPLY_SP_REGEN', 11),
    ('APPLY_POISON_PCT', 12),
    ('APPLY_STUN_PCT', 13),
    ('APPLY_SLOW_PCT', 14),
    ('APPLY_CRITICAL_PCT', 15),
    ('APPLY_PENETRATE_PCT', 16),
    ('APPLY_ATTBONUS_HUMAN', 17),
    ('APPLY_ATTBONUS_ANIMAL', 18),
    ('APPLY_ATTBONUS_ORC', 19),
    ('APPLY_ATTBONUS_MILGYO', 20),
    ('APPLY_ATTBONUS_UNDEAD', 21),
    ('APPLY_ATTBONUS_DEVIL', 22),
    ('APPLY_STEAL_HP', 23),
    ('APPLY_STEAL_SP', 24),
    ('APPLY_MANA_BURN_PCT', 25),
    ('APPLY_DAMAGE_SP_RECOVER', 26),
    ('APPLY_BLOCK', 27),
    ('APPLY_DODGE', 28),
    ('APPLY_RESIST_SWORD', 29),
    ('APPLY_RESIST_TWOHAND', 30),
    ('APPLY_RESIST_DAGGER', 31),
    ('APPLY_RESIST_BELL', 32),
    ('APPLY_RESIST_FAN', 33),
    ('APPLY_RESIST_BOW', 34),
    ('APPLY_RESIST_FIRE', 35),
    ('APPLY_RESIST_ELEC', 36),
    ('APPLY_RESIST_MAGIC', 37),
    ('APPLY_RESIST_WIND', 38),
    ('APPLY_REFLECT_MELEE', 39),
    ('APPLY_REFLECT_CURSE', 40),
    ('APPLY_POISON_REDUCE', 41),
    ('APPLY_KILL_SP_RECOVER', 42),
    ('APPLY_EXP_DOUBLE_BONUS', 43),
    ('APPLY_GOLD_DOUBLE_BONUS', 44),
    ('APPLY_ITEM_DROP_BONUS', 45),
    ('APPLY_POTION_BONUS', 46),
    ('APPLY_KILL_HP_RECOVER', 47),
    ('APPLY_IMMUNE_STUN', 48),
    ('APPLY_IMMUNE_SLOW', 49),
    ('APPLY_IMMUNE_FALL', 50),
    ('APPLY_ATT_GRADE_BONUS', 53),
    ('APPLY_DEF_GRADE_BONUS', 54),
    ('APPLY_MAGIC_ATT_GRADE', 55),
    ('APPLY_MAGIC_DEF_GRADE', 56),
    ('APPLY_ATTBONUS_WARRIOR', 59),
    ('APPLY_ATTBONUS_ASSASSIN', 60),
    ('APPLY_ATTBONUS_SURA', 61),
    ('APPLY_ATTBONUS_SHAMAN', 62),
    ('APPLY_ATTBONUS_MONSTER', 63),
    ('APPLY_MALL_ATTBONUS', 64),
    ('APPLY_MALL_DEFBONUS', 65),
    ('APPLY_MALL_EXPBONUS', 66),
    ('APPLY_MALL_ITEMBONUS', 67),
    ('APPLY_MALL_GOLDBONUS', 68),
    ('APPLY_MAX_HP_PCT', 69),
    ('APPLY_MAX_SP_PCT', 70),
    ('APPLY_SKILL_DAMAGE_BONUS', 71),
    ('APPLY_NORMAL_HIT_DAMAGE_BONUS', 72),
    ('APPLY_SKILL_DEFEND_BONUS', 73),
    ('APPLY_NORMAL_HIT_DEFEND_BONUS', 74),
    ('APPLY_RESIST_WARRIOR', 78),
    ('APPLY_RESIST_ASSASSIN', 79),
    ('APPLY_RESIST_SURA', 80),
    ('APPLY_RESIST_SHAMAN', 81),
    ('APPLY_DEF_GRADE', 83),
    ('APPLY_MAGIC_ATTBONUS_PER', 85),
    ('APPLY_MELEE_MAGIC_ATTBONUS_PER', 86),
    ('APPLY_RESIST_ICE', 87),
    ('APPLY_RESIST_EARTH', 88),
    ('APPLY_RESIST_DARK', 89),
    ('APPLY_ANTI_CRITICAL_PCT', 90),
    ('APPLY_ANTI_PENETRATE_PCT', 91),
    ('APPLY_BLEEDING_REDUCE', 92),
    ('APPLY_BLEEDING_PCT', 93),
    ('APPLY_ATTBONUS_WOLFMAN', 94),
    ('APPLY_RESIST_WOLFMAN', 95),
    ('APPLY_RESIST_CLAW', 96),
    ('APPLY_RESIST_MAGIC_REDUCTION', 99),
    ('APPLY_ENCHANT_ELEC', 100),
    ('APPLY_ENCHANT_FIRE', 101),
    ('APPLY_ENCHANT_ICE', 102),
    ('APPLY_ENCHANT_WIND', 103),
    ('APPLY_ENCHANT_EARTH', 104),
    ('APPLY_ENCHANT_DARK', 105),
    ('APPLY_RESIST_SWORD_REDUCTION', 109),
    ('APPLY_RESIST_TWOHAND_REDUCTION', 110),
    ('APPLY_RESIST_DAGGER_REDUCTION', 111),
    ('APPLY_RESIST_BELL_REDUCTION', 112),
    ('APPLY_RESIST_FAN_REDUCTION', 113),
    ('APPLY_RESIST_BOW_REDUCTION', 114),
    ('APPLY_RESIST_CLAW_REDUCTION', 115),
    ('APPLY_RESIST_HUMAN', 116),
    ('APPLY_ATTBONUS_METIN', 117),
    ('APPLY_ATTBONUS_BOSS', 118),
    ('APPLY_RESIST_NORMAL_DAMAGE', 124),
    ('APPLY_RESIST_MONSTER', 126),
    ('APPLY_RESIST_BOSS', 127),
    ('APPLY_PVM_ATTBONUS', 128),
    ('APPLY_ATTBONUS_ORDINARY_MONSTER', 129),
    ('APPLY_DEFENSE_BREAKTHROUGH', 130),
    ('APPLY_BLOCK_PENETRATION', 131),
    ('APPLY_CRITICAL_DAMAGE_PVM', 171),
    ('APPLY_WEAPON_BASE_PERCENT', 173),
)
POINT_ROW_BASE = 62000
BONUS_ROW_BASE = 63000

class Row(list):
    def __init__(self, values, active_only=False):
        list.__init__(self, values)
        self.members = None
        self.active_only = active_only

def Members(row):
    return getattr(row, "members", None) or [row]

def Key(row):
    return POINT_ROW_BASE + row[1] if row[1] else row[0]

def Value(row):
    return " / ".join(Format(totals.GetExact(Key(part)), part[3]) for part in Members(row))

def Visible(row):
    return not getattr(row, "active_only", False) or any(
        totals.GetExact(Key(part)) not in (None, 0) for part in Members(row))

def Format(value, percent):
    if value is None:
        return "--"
    sign = "-" if value < 0 else ""
    whole, fraction = divmod(abs(value), SCALE)
    text = sign + str(whole)
    if fraction:
        text += "." + ("%06d" % fraction).rstrip("0")
    return text + ("%" if percent else "")

def IsInventoryEquipment(player, item, itemVnum, windowType, slotIndex, previewGrade=None):
    if previewGrade is not None or slotIndex is None or slotIndex < 0:
        return False
    windows = tuple(getattr(player, name, None) for name in
                    ("INVENTORY", "EQUIPMENT", "DRAGON_SOUL_INVENTORY"))
    if windowType is None or windowType not in windows or player.GetItemIndex(windowType, slotIndex) != itemVnum:
        return False
    item.SelectItem(itemVnum)
    types = tuple(getattr(item, name, None) for name in
                  ("ITEM_TYPE_WEAPON", "ITEM_TYPE_ARMOR", "ITEM_TYPE_COSTUME",
                   "ITEM_TYPE_DS", "ITEM_TYPE_SPECIAL_DS", "ITEM_TYPE_UNIQUE",
                   "ITEM_TYPE_BELT", "ITEM_TYPE_RING", "ITEM_TYPE_MOUNT_EQUIPMENT"))
    return item.GetItemType() in types


def FormatItemTotal(text, kind):
    value = totals.GetExact(BONUS_ROW_BASE + kind)
    if value is None:
        return text
    return text + " (" + Format(value, "%" in text) + ")"


def TotalsLegend(czech):
    return (u"V závorce: získané bonusy bez základu postavy." if czech
            else "In brackets: acquired bonuses without character base.")


def Catalog(item, affects, formatter, categories, language):
    czech = language == "cz"
    allowed = set(getattr(item, name, fallback) for name, fallback in COMBAT_APPLIES)
    conditional = set(getattr(item, name, fallback) for name, fallback in COMBAT_APPLIES
                      if fallback in (92, 93, 94, 95, 96, 109, 110, 111, 112, 113, 114, 115))
    rows, seenPoints = {}, set()
    for kind in sorted(set(affects) & allowed):
        point = item.GetApplyPoint(kind)
        if point and point in seenPoints:
            continue
        description = bonuslabels.Describe(formatter, kind)
        if description is None:
            continue
        label, unit = description
        rows[kind] = Row([kind, point, label, unit == "%"], kind in conditional)
        if point:
            seenPoints.add(point)

    # Same name, different units: keep independent values/sources in one row.
    # Defense grade includes the additive defense bonus; never add them again.
    defenseBonus = getattr(item, "APPLY_DEF_GRADE_BONUS", 54)
    defenseGrade = getattr(item, "APPLY_DEF_GRADE", 83)
    representatives, grouped = {}, {}
    for kind, row in sorted(rows.items()):
        previous = representatives.get(row[2])
        if previous is None:
            representatives[row[2]] = row
            grouped[kind] = kind
            continue
        if previous.members is None:
            previous.members = [Row(previous, previous.active_only)]
        previous.members.append(row)
        previous.active_only = previous.active_only and row.active_only
        grouped[kind] = previous[0]
    for row in representatives.values():
        if row.members and any(part[0] == defenseGrade for part in row.members):
            row.members = [part for part in row.members if part[0] != defenseBonus]
        if row.members:
            row.members.sort(key=lambda part: part[3])
    result, used = [], set()
    for title, original in categories:
        current = []
        for kind in original:
            representative = grouped.get(kind)
            if representative is not None and representative not in used:
                current.append(rows[representative]); used.add(representative)
        if current:
            result.append([title, current])
    other = [row for kind, row in sorted(rows.items())
             if grouped[kind] == kind and kind not in used]
    if other:
        result.append([u"Ostatní atributy" if czech else "Other attributes", other])
    cores = []
    for kind in range(mountcorebonus.FIRST_APPLY, mountcorebonus.LAST_APPLY + 1):
        text = mountcorebonus.FormatAffect(kind, 1, czech)
        cores.append(Row([kind, 0, text.rsplit(" ", 1)[0], True], True))
    result.append([u"Jádro mounta a dungeony" if czech else "Mount core and dungeons", cores])
    return result
