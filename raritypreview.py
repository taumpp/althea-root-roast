"""Read-only promotion display for the fixed, server-validated rarity v2 catalog.

Source: althea/server 2928d79a54ca5f4e25273992ee579fa82180dfe8 share/conf/rarity_system_v1.json.
The server enforces these values against common/rarity_v2_policy.h.
A preview never selects a random bonus or changes inventory metadata.
"""

MAXIMUM_GRADE = 6
BONUS_VALUES = {
    1: (200, 200, 200, 400, 600, 800),
    2: (50, 50, 50, 100, 150, 200),
    3: (1, 1, 1, 2, 3, 4),
    4: (1, 1, 1, 2, 3, 4),
    5: (1, 1, 1, 2, 3, 4),
    6: (1, 1, 1, 2, 3, 4),
    7: (1, 1, 1, 2, 3, 4),
    9: (1, 1, 1, 2, 3, 4),
    10: (2, 2, 2, 4, 6, 8),
    11: (2, 2, 2, 4, 6, 8),
    13: (1, 1, 1, 2, 3, 4),
    14: (1, 1, 1, 2, 3, 4),
    15: (2, 2, 2, 4, 6, 8),
    16: (2, 2, 2, 4, 6, 8),
    18: (2, 2, 2, 3, 4, 5),
    19: (2, 2, 2, 3, 4, 5),
    20: (2, 2, 2, 3, 4, 5),
    21: (2, 2, 2, 3, 4, 5),
    22: (2, 2, 2, 3, 4, 5),
    58: (10, 10, 10, 20, 30, 40),
    71: (1, 1, 1, 2, 3, 4),
    72: (1, 1, 1, 2, 3, 4),
    117: (2, 2, 2, 3, 4, 5),
    118: (2, 2, 2, 3, 4, 5),
}


def ProjectAttributes(attributes, extra, targetGrade, isV2):
    """Return copied post-promotion attributes and indexes awaiting a random roll."""
    projected = list(attributes or ())[:7]
    projected += [(0, 0)] * (7 - len(projected))
    projected.append(tuple(extra or (0, 0)))
    grade = int(targetGrade)
    count = min(grade, 3 if isV2 else 2) if 1 <= grade <= MAXIMUM_GRADE else 0
    pending = []
    for offset in range(3):
        index = 5 + offset
        affect, value = projected[index]
        if offset >= count:
            projected[index] = (0, 0)
        elif not isV2 or not affect:
            projected[index] = (0, 0)
            pending.append(index)
        elif affect in BONUS_VALUES:
            projected[index] = (affect, BONUS_VALUES[affect][grade - 1])
        # Retired legacy types keep their exact value, as on the server.
    return projected, tuple(pending)
