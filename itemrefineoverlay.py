MAX_VISIBLE_REFINE_LEVEL = 99
SLOT_CELL_SIZE = 32
RIGHT_INSET = 3
BOTTOM_INSET = 15
STONE_TOP_INSET = 1


def ExtractRefineLevel(itemName):
	"""Return the explicit trailing +N grade, or None for an ungraded item."""
	if not isinstance(itemName, str):
		return None

	name, separator, suffix = itemName.rpartition("+")
	if not separator or not name or not suffix.isdigit():
		return None

	level = int(suffix)
	if level < 0 or level > MAX_VISIBLE_REFINE_LEVEL:
		return None
	return level


def GetOverlayPosition(slotX, slotY, itemWidth, itemHeight, stone=False):
	"""Keep stone grades above stack counts; equipment stays bottom-right."""
	width = max(1, int(itemWidth))
	height = max(1, int(itemHeight))
	return (
		int(slotX) + width * SLOT_CELL_SIZE - RIGHT_INSET,
		int(slotY) + (STONE_TOP_INSET if stone else height * SLOT_CELL_SIZE - BOTTOM_INSET),
	)


def HideGroup(overlays, group):
	for key, overlay in overlays.items():
		if key[0] == group:
			overlay.Hide()


def Clear(overlays):
	for overlay in overlays.values():
		overlay.Hide()
	overlays.clear()


def SetOverlay(overlays, key, slotWindow, itemVnum, itemTypes):
	"""Refresh one non-pickable grade without changing the native slot count."""
	import item
	import ui

	overlay = overlays.get(key)
	if overlay:
		overlay.Hide()
	if not itemVnum:
		return
	item.SelectItem(itemVnum)
	itemType = item.GetItemType()
	if itemType not in itemTypes:
		return
	refineLevel = ExtractRefineLevel(item.GetItemName())
	if refineLevel is None:
		return
	itemWidth, itemHeight = item.GetItemSize()
	slotPosition = slotWindow.GetSlotLocalPosition(key[1])
	if slotPosition is None:
		return
	if not overlay:
		overlay = ui.TextLine()
		overlay.SetParent(slotWindow)
		overlay.AddFlag("not_pick")
		overlay.SetHorizontalAlignRight()
		overlay.SetOutline()
		overlay.SetPackedFontColor(0xFFFFFFFF)
		overlays[key] = overlay
	slotX, slotY = slotPosition
	overlay.SetPosition(*GetOverlayPosition(
		slotX, slotY, itemWidth, itemHeight, itemType == item.ITEM_TYPE_METIN))
	overlay.SetText("+%d" % refineLevel)
	overlay.Show()
