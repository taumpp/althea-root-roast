"""Only a weapon can be absorbed into a sash.

The absorb window (uiacce.AbsorbWindow) takes the sash in slot 0 and the material in slot 1; the native acce.Add
with slot 255 picks the slot by itself. Body armour was accepted as material before. The client refuses it with a
message before anything is sent, the server refuses the same (CHARACTER::AddAcceMaterial and
the absorption in RefineAcceMaterials), so a modified client cannot bypass it.
"""

WEAPON_ONLY = "Do šerpy lze absorbovat jen zbraň."
SASH_SLOT, MATERIAL_SLOT, ANY_SLOT = 0, 1, 255


def Refusal(item, slot):
	"""The chat text when the item selected with item.SelectItem may not go to ``slot`` of the absorb window, else
	None. ``item`` is the native item module (or its stand-in)."""
	itemType = item.GetItemType()
	if itemType == item.ITEM_TYPE_WEAPON:
		return None if slot in (MATERIAL_SLOT, ANY_SLOT) else WEAPON_ONLY
	isSash = itemType == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == item.COSTUME_TYPE_ACCE
	if isSash and slot in (SASH_SLOT, ANY_SLOT):
		return None
	return WEAPON_ONLY


def IsAbsorbable(item):
	"""Whether the selected item may take part in an absorption at all (the inventory keeps the others dimmed)."""
	return Refusal(item, ANY_SLOT) is None
