# -*- coding: utf-8 -*-
"""How many of a price item the player has: one count and one look for every cost paid in items ("Sigil II  12 / 25",
the number green when it is enough, red when it is not - the look of the R1 crafting window).

    import ownedcount
    owned = ownedcount.Owned(91201)                       # 12: client-visible count
    line.SetText(ownedcount.Text(owned, 25))              # "12 / 25"
    line.SetPackedFontColor(ownedcount.Color(owned, 25))  # SHORT (red); GREEN when owned >= need
    ownedcount.Paint(line, owned, 25)                     # the two lines above in one call
    ownedcount.Tagged(owned, 25)                          # "|cffdc443c12 / 25|r" for a line with more text in it

The displayed count covers the server's inventory ranges: normal pages, all
special inventories including consumables, and the separate Dragon Soul window.
Equipped items, belt and storage are excluded. Client-visible counts are an
estimate: server reservations, exchange and shop locks remain authoritative.

Crafting (uicrafting) keeps the counts its server quote sends; it only shares the text and the colours.
Yang prices keep the R1 price (uir1price): red when short, no "owned" number.

player and item are looked up when they are used (_Native): in the game they are the one native module; the test
harnesses swap their fakes per test, and a window loaded with its fakes keeps the ones it was loaded with.
"""
import sys

try:
	import player as _player
except ImportError:
	_player = None
try:
	import item as _item
except ImportError:
	_item = None

GREEN = 0xFF5FC45A          # enough (uicraftingr1.GREEN)
SHORT = 0xFFDC443C          # not enough (uicraftingr1.SHORT, uir1price.SHORT)

# special inventories the server counts, by the item module constant of their first cell;
# Keep these ranges aligned with CountSpecifyItem, including consumables.
COUNTED_SPECIAL = (
	"SKILL_BOOK_INVENTORY_SLOT_START",
	"UPGRADE_ITEMS_INVENTORY_SLOT_START",
	"STONE_INVENTORY_SLOT_START",
	"GIFT_BOX_INVENTORY_SLOT_START",
	"SWITCH_INVENTORY_SLOT_START",
	"COSTUME_INVENTORY_SLOT_START",
	"CONSUMABLE_INVENTORY_SLOT_START",
)


def _Signed(color):
	"""A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
	color = int(color) & 0xFFFFFFFF
	return color - 0x100000000 if color > 0x7FFFFFFF else color


def _Native(name, loaded):
	"""The native module ``name``: the current one, else the one this module was loaded with."""
	module = sys.modules.get(name)
	return module if module is not None else loaded


def _Constant(module, name):
	"""An integer constant of a native module, None when the executable has none."""
	value = getattr(module, name, None)
	if isinstance(value, bool) or not isinstance(value, (int, type(2 ** 64))):
		return None
	return int(value)


def CountedCells():
	"""The global INVENTORY cells the server counts: the inventory pages, then each counted special inventory;
	empty when the executable does not tell the layout (Owned then falls back to player.GetItemCountByVnum)."""
	item = _Native("item", _item)
	player = _Native("player", _player)
	pages = _Constant(player, "ITEM_SLOT_COUNT")
	if not pages:
		return []
	cells = list(range(pages))
	size = _Constant(player, "SPECIAL_ITEM_SLOT_COUNT") or 0
	if size > 0:
		for name in COUNTED_SPECIAL:
			start = _Constant(item, name)
			if start is not None:
				cells.extend(range(start, start + size))
	return cells


def Owned(vnum):
	"""Client-visible count in the server's counted ranges; 0 when unknown."""
	try:
		player = _Native("player", _player)
		vnum = int(vnum)
		if vnum <= 0:
			return 0
		cells = CountedCells()
		if not cells:
			return max(0, int(player.GetItemCountByVnum(vnum)))
		count = 0
		for cell in cells:
			if int(player.GetItemIndex(cell)) == vnum:
				count += int(player.GetItemCount(cell))
		window = _Constant(player, "DRAGON_SOUL_INVENTORY")
		size = _Constant(player, "DRAGON_SOUL_SLOT_COUNT") or 0
		if window is not None:
			for cell in range(size):
				if int(player.GetItemIndex(window, cell)) == vnum:
					count += int(player.GetItemCount(window, cell))
		return max(0, count)
	except Exception:
		return 0


def Short(count):
	"""A count as the crafting window writes it: 999, 9999, 12,5k, 1,2M."""
	try:
		count = max(0, int(count))
	except Exception:
		count = 0
	if count >= 1000000:
		return ("%.1fM" % (count / 1000000.0)).replace(".", ",")
	if count >= 10000:
		return ("%.1fk" % (count / 1000.0)).replace(".", ",")
	return str(count)


def IsEnough(owned, need):
	try:
		return int(owned) >= int(need)
	except Exception:
		return False


def Text(owned, need, compact=False):
	"""'12 / 25' (owned / needed); ``compact`` '12/25' for a count on a 32 px item icon."""
	return ("%s/%s" if compact else "%s / %s") % (Short(owned), Short(need))


def Color(owned, need):
	"""GREEN when ``owned`` covers ``need``, SHORT (red) otherwise; packed signed for SetPackedFontColor."""
	return _Signed(GREEN if IsEnough(owned, need) else SHORT)


def Tagged(owned, need):
	"""Text() in its colour as an engine colour tag, for a line that has more text in it."""
	return "|c%08x%s|r" % ((GREEN if IsEnough(owned, need) else SHORT) & 0xFFFFFFFF, Text(owned, need))


def Paint(line, owned, need, compact=False):
	"""Writes Text() into ``line`` in Color()."""
	line.SetPackedFontColor(Color(owned, need))
	line.SetText(Text(owned, need, compact))
	return line
