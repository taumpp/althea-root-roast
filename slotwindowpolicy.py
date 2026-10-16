"""Item window of a mouse-attached slot type.

Special-inventory tabs attach their global INVENTORY cell (295+) under their
own slot type, for example a split stack from the materials tab. The server
keeps those cells in the INVENTORY window. Published executables before
client-src !395 return RESERVED_WINDOW from player.SlotTypeToInvenType for
every special tab, so this module resolves them itself and stays correct with
both the old and the fixed executable. Every other slot type is delegated to
the executable unchanged.
"""

import player


SPECIAL_INVENTORY_SLOT_TYPE_NAMES = (
	"SLOT_TYPE_SKILL_BOOK_INVENTORY",
	"SLOT_TYPE_UPGRADE_ITEMS_INVENTORY",
	"SLOT_TYPE_STONE_INVENTORY",
	"SLOT_TYPE_GIFT_BOX_INVENTORY",
	"SLOT_TYPE_SWITCH_INVENTORY",
	"SLOT_TYPE_COSTUME_INVENTORY",
	"SLOT_TYPE_CONSUMABLE_INVENTORY",
)


def SpecialInventorySlotTypes():
	values = set()
	for name in SPECIAL_INVENTORY_SLOT_TYPE_NAMES:
		value = getattr(player, name, None)
		if value is not None:
			values.add(value)
	values.discard(player.SLOT_TYPE_INVENTORY)
	return frozenset(values)


def IsSpecialInventorySlotType(slotType):
	return slotType in SpecialInventorySlotTypes()


def IsInventorySlotType(slotType):
	"""SLOT_TYPE_INVENTORY or a special tab; the cell is a global INVENTORY cell."""
	return slotType == player.SLOT_TYPE_INVENTORY or IsSpecialInventorySlotType(slotType)


def IsOwnedItemSlotType(slotType):
	"""An item the player carries: inventory, special tabs or Dragon Soul."""
	return IsInventorySlotType(slotType) or slotType == player.SLOT_TYPE_DRAGON_SOUL_INVENTORY


def NormalizeSlotType(slotType):
	"""Treat a special-tab attachment exactly like SLOT_TYPE_INVENTORY."""
	if IsSpecialInventorySlotType(slotType):
		return player.SLOT_TYPE_INVENTORY
	return slotType


def ItemWindowForSlotType(slotType):
	if IsInventorySlotType(slotType):
		return player.INVENTORY
	return player.SlotTypeToInvenType(slotType)
