"""Presentation of Seon-Pyeong's server-authoritative mixed stone recipes."""

DUST_VNUM = 79620
CHEST_VNUM = 79633
RESIST_ALL_APPLY = 172
OLD_BASE_VNUMS = (28000, 28004, 28008, 28012) + tuple(range(28030, 28048))

def MaterialVnums(reward, material):
    if reward == DUST_VNUM and material == 28030:
        return tuple(base + grade * 100 for grade in range(4) for base in OLD_BASE_VNUMS)
    if reward == CHEST_VNUM and material == 28430:
        return tuple(base + 400 for base in OLD_BASE_VNUMS)
    return (material,)

def MaterialCount(reward, material, count_by_vnum):
    return sum(count_by_vnum(vnum) for vnum in MaterialVnums(reward, material))

def MaterialGroupKey(reward, material):
    if reward == DUST_VNUM and material == 28030:
        return 'STONE_CRAFT_OLD_LOW'
    if reward == CHEST_VNUM and material == 28430:
        return 'STONE_CRAFT_OLD_FOUR'
    return None


def GroupChestPreview(chestVnum, pages):
    """Collapse only complete, single-reward classic families from the reply."""
    if chestVnum != 50124:
        return pages, {}
    families = {}
    order = []
    for page in sorted(pages):
        for slot in sorted(pages[page]):
            vnum, count = pages[page][slot]
            grade = (vnum - 28000) // 100
            base = vnum - grade * 100
            if base not in OLD_BASE_VNUMS or grade not in range(5) or count != 1:
                return pages, {}
            if base not in families:
                families[base] = set()
                order.append(base)
            if grade in families[base]:
                return pages, {}
            families[base].add(grade)
    if not families or any(grades != set(range(5)) for grades in families.values()):
        return pages, {}
    # All allowlisted prototypes occupy one cell; at most 22 families fit here.
    grouped = {1: {slot: [base, 1] for slot, base in enumerate(order)}}
    ranges = {(1, slot): (0, 4) for slot in range(len(order))}
    return grouped, ranges
