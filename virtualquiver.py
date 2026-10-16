import chat
import item
import localeInfo
import player

# ALTHEA-641 virtual quiver (owner decision 2026-10-02).
#
# An equipped bow is always loaded: archers no longer equip arrows or a
# quiver and the server no longer consumes or accepts them. The arrow
# equipment cell keeps its index (player.EQUIPMENT_SLOT_START + 9, server
# WEAR_ARROW) reserved, but the inventory no longer presents it. It is shown
# again only while an item from before the change still occupies it, so the
# player can take that item out. The server stays authoritative; this module
# only explains the refusal before a packet is sent.

ARROW_EQUIPMENT_SLOT = player.EQUIPMENT_SLOT_START + 9

FALLBACK_TEXT = "Arrows are no longer needed, the bow shoots on its own."


def IsRetiredAmmo(itemType, itemSubType):
	if itemType != item.ITEM_TYPE_WEAPON:
		return False
	return itemSubType in (item.WEAPON_ARROW, getattr(item, "WEAPON_QUIVER", -1))


def IsRetiredAmmoInSlot(slotPos, window=player.INVENTORY):
	if not player.GetItemIndex(window, slotPos):
		return False
	return IsRetiredAmmo(
		player.GetItemTypeBySlot(window, slotPos),
		player.GetItemSubTypeBySlot(window, slotPos))


def IsArrowSlotOccupied():
	return player.GetItemIndex(ARROW_EQUIPMENT_SLOT) != 0


def RefusesEquip(srcSlotPos, dstSlotPos=None):
	# Only an equip attempt is refused: a move without an equipment target is
	# ordinary inventory handling, and taking an old arrow or quiver out of
	# the equipment stays allowed.
	if dstSlotPos is not None and not player.IsEquipmentSlot(dstSlotPos):
		return False
	if player.IsEquipmentSlot(srcSlotPos):
		return False
	return IsRetiredAmmoInSlot(srcSlotPos)


def NoLongerNeededText():
	return getattr(localeInfo, "ARROWS_NO_LONGER_NEEDED", FALLBACK_TEXT)


def NotifyNoLongerNeeded():
	chat.AppendChat(chat.CHAT_TYPE_INFO, NoLongerNeededText())
