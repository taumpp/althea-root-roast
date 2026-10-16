MAX_VISIBLE_REFINE_LEVEL = 99
SLOT_CELL_SIZE = 32
RIGHT_INSET = 3
BOTTOM_INSET = 15


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


def GetOverlayPosition(slotX, slotY, itemWidth, itemHeight):
	"""Anchor the label to the bottom-right of a multi-cell item icon."""
	width = max(1, int(itemWidth))
	height = max(1, int(itemHeight))
	return (
		int(slotX) + width * SLOT_CELL_SIZE - RIGHT_INSET,
		int(slotY) + height * SLOT_CELL_SIZE - BOTTOM_INSET,
	)
