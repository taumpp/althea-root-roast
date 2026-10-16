# Dedicated random base applies retired by the Snake/Jotun equipment revision.
# Stored snapshots remain intact; ordinary attributes and rarity are separate.
SNAKE_WEAPON_BASES = (360, 380, 1210, 2230, 3250, 5200, 6150, 7330)
JOTUN_WEAPON_BASES = (35100, 35120, 35140, 35160, 35180, 35200, 35220, 35240)
SNAKE_BASES = SNAKE_WEAPON_BASES + (21310, 21330, 21350, 21370, 21390)
JOTUN_BASES = JOTUN_WEAPON_BASES + (21600, 21620, 21640, 21660)


def HasRetiredRandomApplies(itemVnum):
    return (any(base <= itemVnum <= base + 12 for base in SNAKE_BASES) or
            any(base <= itemVnum <= base + 15 for base in JOTUN_BASES))


def HasClassicWeaponAddon(itemVnum):
    return (any(base <= itemVnum <= base + 12 for base in SNAKE_WEAPON_BASES) or
            any(base <= itemVnum <= base + 15 for base in JOTUN_WEAPON_BASES))
