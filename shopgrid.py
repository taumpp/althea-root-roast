GRID_COLUMNS = 10
MIN_ROWS = 4
MAX_ITEM_HEIGHT = 3


def PackShopItems(records, columns=GRID_COLUMNS, minimumRows=MIN_ROWS):
	columns = max(1, int(columns))
	columnHeights = [0] * columns
	anchors = {}
	footprint = {}

	for realIndex, rawHeight in records:
		height = max(1, min(MAX_ITEM_HEIGHT, int(rawHeight)))
		row = min(columnHeights)
		column = columnHeights.index(row)
		visible = row * columns + column

		anchors[visible] = int(realIndex)
		for offset in range(height):
			footprint[visible + offset * columns] = int(realIndex)
		columnHeights[column] += height

	rows = max(int(minimumRows), max(columnHeights) if columnHeights else 0)
	return {
		"columns": columns,
		"rows": rows,
		"anchors": anchors,
		"footprint": footprint,
	}


def ResolveRealIndex(footprint, visibleSlot):
	try:
		return footprint.get(int(visibleSlot))
	except (TypeError, ValueError):
		return None


def SourceTab(realIndex, slotsPerTab):
	try:
		realIndex = int(realIndex)
		slotsPerTab = int(slotsPerTab)
	except (TypeError, ValueError):
		return None

	if realIndex < 0 or slotsPerTab <= 0:
		return None
	return realIndex // slotsPerTab
