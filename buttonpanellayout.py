"""Pure slot operations shared by the configurable button panels.

A panel layout is a tuple of function IDs: slot index ``i`` shows ``slots[i]``.
``EMPTY`` ('') is an empty slot added with "+" in Settings (owner 2026-10-04):
it is kept in the stored layout so the player can fill it later. In game the
minimap keeps its slot empty (so ring 2 shows what the Settings preview
shows) and the inventory rail packs its column. Every operation returns a new tuple and never exceeds
``limit``. Used by the minimap panel (the inventory rail has its own
two-column variant in ``inventoryrail``).
"""

EMPTY = ''


def _clean(slots):
    return [action for action in slots if action or action == EMPTY]


def AddEmpty(slots, limit):
    """Settings "+": append an empty slot (unchanged when the panel is full)."""
    slots = _clean(slots)
    if len(slots) < limit:
        slots.append(EMPTY)
    return tuple(slots)


def AssignSlot(slots, index, action, limit):
    """Put ``action`` into slot ``index``.

    ``None`` ("Empty slot") turns a function slot into an empty slot and removes
    an empty slot. A function already shown elsewhere swaps places with the
    slot's content (or moves last when the target is past the end). An index
    beyond the end appends.
    """
    slots = _clean(slots)
    if index < 0:
        return tuple(slots)
    if action is None:
        if index < len(slots):
            if slots[index] == EMPTY:
                del slots[index]
            else:
                slots[index] = EMPTY
        return tuple(slots)
    if action in slots:
        source = slots.index(action)
        if index >= len(slots):
            # Moving to a free place after the end: the function goes last.
            del slots[source]
            slots.append(action)
        else:
            slots[source], slots[index] = slots[index], slots[source]
        return tuple(slots[:limit])
    if index >= len(slots):
        if len(slots) >= limit:
            return tuple(slots)
        slots.append(action)
    else:
        slots[index] = action
    return tuple(slots[:limit])


def FillFirstEmpty(slots, action, limit):
    """Put ``action`` into the first empty slot, else append (when there is room)."""
    slots = _clean(slots)
    if action in slots:
        return tuple(slots)
    if EMPTY in slots:
        slots[slots.index(EMPTY)] = action
    elif len(slots) < limit:
        slots.append(action)
    return tuple(slots)


def SwapSlots(slots, first, second):
    """Swap two slots; an index beyond the end moves the other slot's content last."""
    slots = _clean(slots)
    count = len(slots)
    if first == second or (first >= count and second >= count) or min(first, second) < 0:
        return tuple(slots)
    if first >= count or second >= count:
        source = first if first < count else second
        action = slots.pop(source)
        slots.append(action)
        return tuple(slots)
    slots[first], slots[second] = slots[second], slots[first]
    return tuple(slots)


def RemoveAction(slots, action):
    return tuple(item for item in _clean(slots) if item != action)


def Assigned(slots):
    """The functions of a layout without its empty slots (what the game shows)."""
    return tuple(action for action in slots if action != EMPTY)
