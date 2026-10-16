"""Colors for active-effect tooltips, separate from equipment attributes."""
import item


def Packed(rgb):
    return (0xff000000 | rgb) - 0x100000000


TITLE_COLOR = Packed(0xE9E1CE)
STAT_COLOR = Packed(0xDDD9C9)
COMBAT_COLOR = Packed(0xE6AF84)
DEFENSE_COLOR = Packed(0x9DCDEC)
UTILITY_COLOR = Packed(0xA7DDBA)
CHANCE_COLOR = Packed(0xD8AFE9)
TIME_COLOR = Packed(0xBFC5BF)

ROLE_COLORS = {
    "stat": STAT_COLOR,
    "combat": COMBAT_COLOR,
    "defense": DEFENSE_COLOR,
    "utility": UTILITY_COLOR,
    "chance": CHANCE_COLOR,
}

GROUP_COLORS = {
    "gods": Packed(0xD8C390),
    "buffs": Packed(0x9FD2BD),
    "skills": Packed(0xB6B8E0),
    "dews": Packed(0xD5A5BE),
    "tree": Packed(0xC4DDAE),
}


def ColorForRole(role):
    return ROLE_COLORS.get(role, STAT_COLOR)


def RoleForApplyName(name):
    name = name[6:]
    if name in ("STR", "DEX", "INT", "CON", "ALL_ATTRIBUTES"):
        return "stat"
    if "DEFENSE_BREAKTHROUGH" in name or "CRITICAL_DAMAGE" in name:
        return "combat"
    if name.startswith("ANTI_") or name == "BLOCK_PENETRATION":
        return "defense"
    if ("CRITICAL" in name or "PENETRATE" in name or "CHANCE" in name
            or name in ("BLOCK", "DODGE", "POISON_PCT", "STUN_PCT", "SLOW_PCT")):
        return "chance"
    if ("RESIST" in name or "DEF" in name or "IMMUNE" in name
            or "REFLECT" in name):
        return "defense"
    if ("ATTBONUS" in name or "ATT_GRADE" in name or "MAGIC_ATT" in name
            or "DAMAGE" in name or "ATT_SPEED" in name or "ENCHANT" in name
            or "WEAPON_BASE" in name):
        return "combat"
    return "utility"


def BuildPointRoles():
    roles = {}
    for name in dir(item):
        if not name.startswith("APPLY_"):
            continue
        apply_type = getattr(item, name)
        if not isinstance(apply_type, int):
            continue
        try:
            point = item.GetApplyPoint(apply_type)
        except (TypeError, ValueError):
            continue
        if point > 0:
            roles[point] = RoleForApplyName(name)
    return roles


POINT_ROLES = BuildPointRoles()


def RoleForPoint(point):
    return POINT_ROLES.get(point, "stat")


TREE_DEFENSE = frozenset((2114, 2116, 2131, 2134, 2136, 2138, 2140))
TREE_UTILITY = frozenset((2115, 2117, 2118, 2119, 2120, 2121, 2124, 2141))
TREE_CHANCE = frozenset((2122, 2123, 2126, 2127, 2128, 2129))


def RoleForTreeNode(node_id):
    if node_id == 2101:
        return "stat"
    if node_id in TREE_DEFENSE:
        return "defense"
    if node_id in TREE_UTILITY:
        return "utility"
    if node_id in TREE_CHANCE:
        return "chance"
    return "combat"
