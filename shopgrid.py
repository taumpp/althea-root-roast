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


def PackShopHalves(recordsByTab, columns=GRID_COLUMNS, minimumRows=MIN_ROWS):
	"""Two pages side by side in one grid of ``columns``: page 1 packed into the left half, page 2 into the right
	half (the R1 private shop with "Strana 1 / Strana 2" under the halves). Same result keys as PackShopItems."""
	half = max(1, int(columns) // 2)
	anchors = {}
	footprint = {}
	rows = int(minimumRows)
	for tab, records in enumerate(list(recordsByTab)[:2]):
		layout = PackShopItems(records, half, minimumRows)
		rows = max(rows, layout["rows"])
		for mapping, target in ((layout["anchors"], anchors), (layout["footprint"], footprint)):
			for visible, realIndex in mapping.items():
				row, column = divmod(visible, half)
				target[row * columns + column + tab * half] = realIndex
	return {
		"columns": int(columns),
		"rows": rows,
		"anchors": anchors,
		"footprint": footprint,
	}
