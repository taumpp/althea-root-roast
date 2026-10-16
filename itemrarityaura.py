"""D1 item silhouette aura; presentation reads server-owned rarity metadata."""
import net
import player


COLORS = (
    (1.0, 1.0, 1.0, 0.0),
    (0.58, 0.58, 0.58, 1.0),
    (0.95, 0.95, 0.95, 1.0),
    (0.30, 0.82, 0.35, 1.0),
    (0.30, 0.55, 1.00, 1.0),
    (1.00, 0.55, 0.18, 1.0),
    (0.70, 0.35, 1.00, 1.0),
    (1.00, 0.82, 0.20, 1.0),
)


def ApplyGrade(slotWindow, visibleSlot, grade):
    """Apply a display grade, including a server-approved promotion target."""
    setter = getattr(slotWindow, "SetSlotRarityColor", None)
    if setter is None:
        return
    try:
        grade = int(grade)
    except (TypeError, ValueError, OverflowError):
        grade = 0
    if grade < 0 or grade >= len(COLORS):
        grade = 0
    setter(visibleSlot, COLORS[grade])


def InventoryGrade(sourceSlot):
    grade = 0
    getter = getattr(net, "GetRarityGrade", None)
    if getter is not None:
        window = player.EQUIPMENT if player.IsEquipmentSlot(sourceSlot) else player.INVENTORY
        try:
            grade = int(getter(getattr(net, "RARITY_CONTEXT_INVENTORY", 1),
                window, int(sourceSlot), 0, 0))
        except (TypeError, ValueError, OverflowError):
            grade = 0
    if grade < 0 or grade >= len(COLORS):
        grade = 0
    return grade


def ApplyInventory(slotWindow, visibleSlot, sourceSlot):
    if getattr(slotWindow, "SetSlotRarityColor", None) is not None:
        ApplyGrade(slotWindow, visibleSlot, InventoryGrade(sourceSlot))
