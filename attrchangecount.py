import player

# Bonus-change scrolls used on each owned item, by cell. The server
# sends "AttrChangeCountV1 window cell count" whenever a counted item appears,
# changes or leaves a cell; a game session starts empty.
_counts = {}


def _Key(window, cell):
	# Equipped items use the inventory cell numbering.
	if window == player.EQUIPMENT:
		window = player.INVENTORY
	return (window, cell)


def Reset():
	_counts.clear()


def Set(window, cell, count):
	key = _Key(window, cell)
	if count > 0:
		_counts[key] = count
	else:
		_counts.pop(key, None)


def Get(window, cell):
	return _counts.get(_Key(window, cell), 0)
