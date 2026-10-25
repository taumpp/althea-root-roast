"""Presentation order of a monster's drop list in the target drop grid.

It only reorders what the client already shows; what drops comes from the server table and never changes here.
Groups, in this order:
  0 equipment (weapons, armour, helmets, shields, shoes, bracelets, necklaces, earrings, belts, ...)
  1 costumes, mounts and pets (with their eggs and seals)
  2 boss souls, skill books and souls
  3 upgrade materials (crystals and jewels, spirit stones, refine and enchant scrolls, other refine materials)
  4 consumables (potions, dews, food and sticks)
  5 everything else
Server-authored guaranteed drops precede all other drops. Within each tier, equipment goes by slot,
then by its level limit, lowest first. The other groups keep their
kinds together (in the order above) and put the higher level first, then the higher refine grade, then the vnum. The same vnum with different counts sits side by side, smaller count first.
Everything is derived from item.SelectItem + the item type/subtype the client knows; no vnum is listed here.
Ores share ITEM_TYPE_SPECIAL with gold bars, tickets and quest items and mount/pet boxes are plain gift boxes,
so the client cannot tell them apart; they stay in the last group.
"""

GROUP_EQUIPMENT = 0
GROUP_COSMETIC = 1
GROUP_BOOKS = 2
GROUP_UPGRADE = 3
GROUP_CONSUMABLE = 4
GROUP_OTHER = 5

_guaranteedRace = 0
_guaranteedDrops = set()


def ReceiveOrder(race, append, vnums):
	"""Optional server metadata; a reset also clears guarantees for the same race."""
	global _guaranteedRace, _guaranteedDrops
	try:
		race = int(race)
		append = int(append)
		values = set(int(value) for value in vnums.split(",")) if vnums != "-" else set()
	except (TypeError, ValueError):
		return
	if append not in (0, 1) or race <= 0 or any(value <= 0 for value in values):
		return
	if not append:
		_guaranteedRace, _guaranteedDrops = race, values
	elif race == _guaranteedRace:
		_guaranteedDrops.update(values)


def ResetOrder():
	global _guaranteedRace, _guaranteedDrops
	_guaranteedRace, _guaranteedDrops = 0, set()

# Native subtype values (GameLib/ItemData.h EUseSubTypes) for the ones the item module does not export.
_USE_FALLBACK = {
	"USE_POTION": 0, "USE_TALISMAN": 1, "USE_TUNING": 2, "USE_BAIT": 6, "USE_ABILITY_UP": 7, "USE_AFFECT": 8,
	"USE_SPECIAL": 10, "USE_POTION_NODELAY": 11, "USE_CLEAR": 12, "USE_INVISIBILITY": 13, "USE_DETACHMENT": 14,
	"USE_POTION_CONTINUE": 16, "USE_CLEAN_SOCKET": 17, "USE_CHANGE_ATTRIBUTE": 18, "USE_ADD_ATTRIBUTE": 19,
	"USE_ADD_ACCESSORY_SOCKET": 20, "USE_PUT_INTO_ACCESSORY_SOCKET": 21, "USE_ADD_ATTRIBUTE2": 22,
	"USE_CHANGE_ATTRIBUTE2": 24, "USE_TIME_CHARGE_PER": 27, "USE_TIME_CHARGE_FIX": 28,
	"USE_PUT_INTO_BELT_SOCKET": 29, "USE_PUT_INTO_RING_SOCKET": 30, "USE_CHANGE_COSTUME_ATTR": 31,
	"USE_RESET_COSTUME_ATTR": 32, "USE_SELECT_ATTRIBUTE": 35, "USE_ELEMENT_UPGRADE": 40,
	"USE_ELEMENT_DOWNGRADE": 41, "USE_ELEMENT_CHANGE": 42, "USE_POTION_TOWER": 43, "USE_POTION_NODELAY_TOWER": 44,
	"USE_PUT_INTO_AURA_SOCKET": 48, "USE_RESONANCE_SEAL": 50,
}

_EQUIPMENT_ARMOR = ("ARMOR_BODY", "ARMOR_HEAD", "ARMOR_SHIELD", "ARMOR_FOOTS", "ARMOR_WRIST", "ARMOR_NECK",
	"ARMOR_EAR", "ARMOR_GLOVE", "ARMOR_PENDANT", "ARMOR_TALISMAN_HEART")
_COSTUME_ORDER = ("COSTUME_TYPE_WEAPON", "COSTUME_TYPE_BODY", "COSTUME_TYPE_HAIR", "COSTUME_TYPE_ACCE",
	"COSTUME_TYPE_ACCE_SKIN", "COSTUME_TYPE_AURA", "COSTUME_TYPE_EFFECT_WEAPON", "COSTUME_TYPE_EFFECT_ARMOR")
_PET_FOOD = ("PET_FEEDSTUFF", "PET_EXPFOOD", "PET_EXPFOOD_PER", "PET_PRIMIUM_FEEDSTUFF")
_PET_BOOKS = ("PET_SKILL", "PET_SKILL_DEL_BOOK", "PET_SKILL_ALL_DEL_BOOK")
_PET_CORE = ("PET_EGG", "PET_UPBRINGING", "PET_BAG", "PET_PAY")
_USE_JEWELS = ("USE_ADD_ACCESSORY_SOCKET", "USE_PUT_INTO_ACCESSORY_SOCKET", "USE_PUT_INTO_BELT_SOCKET",
	"USE_PUT_INTO_RING_SOCKET", "USE_PUT_INTO_AURA_SOCKET")
_USE_SCROLLS = ("USE_TUNING", "USE_DETACHMENT", "USE_CLEAN_SOCKET", "USE_CHANGE_ATTRIBUTE", "USE_ADD_ATTRIBUTE",
	"USE_ADD_ATTRIBUTE2", "USE_CHANGE_ATTRIBUTE2", "USE_SELECT_ATTRIBUTE", "USE_CHANGE_COSTUME_ATTR",
	"USE_RESET_COSTUME_ATTR", "USE_ELEMENT_UPGRADE", "USE_ELEMENT_DOWNGRADE", "USE_ELEMENT_CHANGE",
	"USE_RESONANCE_SEAL")
_USE_POTIONS = ("USE_POTION", "USE_POTION_NODELAY", "USE_POTION_CONTINUE", "USE_POTION_TOWER",
	"USE_POTION_NODELAY_TOWER", "USE_ABILITY_UP", "USE_AFFECT", "USE_CLEAR", "USE_INVISIBILITY",
	"USE_TIME_CHARGE_PER", "USE_TIME_CHARGE_FIX", "USE_TALISMAN", "USE_BAIT")


def _Constant(itemModule, name):
	value = getattr(itemModule, name, None)
	if value is None:
		value = _USE_FALLBACK.get(name)
	return value


def _In(itemModule, value, names):
	for name in names:
		constant = _Constant(itemModule, name)
		if constant is not None and value == constant:
			return True
	return False


def _Is(itemModule, value, name):
	constant = _Constant(itemModule, name)
	return constant is not None and value == constant


def _Rank(itemModule, value, names):
	for index, name in enumerate(names):
		if _Is(itemModule, value, name):
			return index
	return len(names)


def _LevelLimit(itemModule):
	limitLevel = getattr(itemModule, "LIMIT_LEVEL", None)
	if limitLevel is None:
		return 0
	for index in range(int(getattr(itemModule, "LIMIT_MAX_NUM", 2))):
		try:
			(limitType, limitValue) = itemModule.GetLimit(index)
		except Exception:
			return 0
		if limitType == limitLevel:
			return int(limitValue)
	return 0


def _RefineLevel(itemModule):
	try:
		return int(itemModule.GetRefineLevel())
	except Exception:
		return 0


def _Classify(itemModule, raceVnum):
	"""(group, subgroup) of the selected item."""
	itemType = itemModule.GetItemType()
	subType = itemModule.GetItemSubType()

	if _Is(itemModule, itemType, "ITEM_TYPE_WEAPON"):
		if _Is(itemModule, subType, "WEAPON_ARROW"):
			return GROUP_CONSUMABLE, 3
		return GROUP_EQUIPMENT, 0
	if _Is(itemModule, itemType, "ITEM_TYPE_ARMOR"):
		return GROUP_EQUIPMENT, 1 + _Rank(itemModule, subType, _EQUIPMENT_ARMOR)
	if _Is(itemModule, itemType, "ITEM_TYPE_BELT"):
		return GROUP_EQUIPMENT, 2 + len(_EQUIPMENT_ARMOR)
	if _Is(itemModule, itemType, "ITEM_TYPE_RING"):
		return GROUP_EQUIPMENT, 3 + len(_EQUIPMENT_ARMOR)

	if _Is(itemModule, itemType, "ITEM_TYPE_COSTUME"):
		if _Is(itemModule, subType, "COSTUME_TYPE_MOUNT"):
			return GROUP_COSMETIC, 10
		if _Is(itemModule, subType, "COSTUME_TYPE_PET"):
			return GROUP_COSMETIC, 20
		return GROUP_COSMETIC, _Rank(itemModule, subType, _COSTUME_ORDER)
	if _Is(itemModule, itemType, "ITEM_TYPE_MOUNT_EQUIPMENT"):
		return GROUP_COSMETIC, 11
	if _Is(itemModule, itemType, "ITEM_TYPE_PET"):
		if _In(itemModule, subType, _PET_FOOD):
			return GROUP_CONSUMABLE, 2
		if _In(itemModule, subType, _PET_BOOKS):
			return GROUP_BOOKS, 2
		if _In(itemModule, subType, _PET_CORE):
			return GROUP_COSMETIC, 21
		return GROUP_COSMETIC, 22

	if _Is(itemModule, itemType, "ITEM_TYPE_USE") and _Is(itemModule, subType, "USE_SPECIAL"):
		# A boss soul names the boss in value 0; it is told apart from other USE_SPECIAL items by that boss
		# being the monster whose drop is shown.
		try:
			if raceVnum and int(itemModule.GetValue(0)) == int(raceVnum):
				return GROUP_BOOKS, 0
		except Exception:
			pass
		return GROUP_OTHER, 4
	if _Is(itemModule, itemType, "ITEM_TYPE_SKILLBOOK"):
		return GROUP_BOOKS, 1
	if _Is(itemModule, itemType, "ITEM_TYPE_SKILLFORGET"):
		return GROUP_BOOKS, 3
	if _Is(itemModule, itemType, "ITEM_TYPE_SOUL"):
		return GROUP_BOOKS, 4

	if _Is(itemModule, itemType, "ITEM_TYPE_RESOURCE"):
		return GROUP_UPGRADE, 0
	if _Is(itemModule, itemType, "ITEM_TYPE_MATERIAL"):
		if _In(itemModule, subType, ("MATERIAL_DS_REFINE_NORMAL", "MATERIAL_DS_REFINE_BLESSED",
				"MATERIAL_DS_REFINE_HOLLY")):
			return GROUP_UPGRADE, 0
		return GROUP_UPGRADE, 3
	if _Is(itemModule, itemType, "ITEM_TYPE_METIN"):
		return GROUP_UPGRADE, 1
	if _Is(itemModule, itemType, "ITEM_TYPE_USE"):
		if _In(itemModule, subType, _USE_JEWELS):
			return GROUP_UPGRADE, 0
		if _In(itemModule, subType, _USE_SCROLLS):
			return GROUP_UPGRADE, 2
		if _In(itemModule, subType, _USE_POTIONS):
			return GROUP_CONSUMABLE, 0
		return GROUP_OTHER, 4

	if _Is(itemModule, itemType, "ITEM_TYPE_BLEND"):
		return GROUP_CONSUMABLE, 1
	if _Is(itemModule, itemType, "ITEM_TYPE_FISH") or _Is(itemModule, itemType, "ITEM_TYPE_AUTOUSE"):
		return GROUP_CONSUMABLE, 2
	if _In(itemModule, itemType, ("ITEM_TYPE_GIFTBOX", "ITEM_TYPE_GACHA")):
		return GROUP_OTHER, 1
	if _Is(itemModule, itemType, "ITEM_TYPE_SPECIAL"):
		return GROUP_OTHER, 2
	if _Is(itemModule, itemType, "ITEM_TYPE_QUEST"):
		return GROUP_OTHER, 3
	return GROUP_OTHER, 99


def DropSortKey(itemModule, vnum, count=1, raceVnum=0):
	"""Sort key of one drop entry; smaller sorts first."""
	vnum = int(vnum)
	count = int(count)
	try:
		itemModule.SelectItem(vnum)
		(group, subgroup) = _Classify(itemModule, raceVnum)
		level = _LevelLimit(itemModule)
		refine = _RefineLevel(itemModule)
	except Exception:
		return (GROUP_OTHER, 99, 0, 0, vnum, count)
	if group == GROUP_EQUIPMENT:
		return (group, subgroup, level, refine, vnum, count)
	return (group, subgroup, -level, -refine, vnum, count)


def SortDrops(entries, itemModule, raceVnum=0, getVnumCount=None):
	"""A new list of the entries in presentation order (stable: equal keys keep their order).

	The entries are (vnum, count) pairs unless getVnumCount(entry) returns that pair for each."""
	if getVnumCount is None:
		getVnumCount = lambda entry: (entry[0], entry[1])
	keyed = []
	for index, entry in enumerate(entries):
		(vnum, count) = getVnumCount(entry)
		guaranteed = int(raceVnum) == _guaranteedRace and int(vnum) in _guaranteedDrops
		keyed.append(((0 if guaranteed else 1,) + DropSortKey(itemModule, vnum, count, raceVnum), index, entry))
	keyed.sort(key=lambda row: (row[0], row[1]))
	return [row[2] for row in keyed]


def RelayDrops(dropList, itemModule, packPages, raceVnum=0):
	"""nonplayer.GetMonsterItemDrop rows [(page, pos, vnum, count)] re-laid in presentation order.

	packPages(heights) lays the item heights out row by row ([[(position, index)] per page], e.g.
	uitarget.PackDropGridPages for the grid size). Returns (last page index, rows) in the shape
	GetMonsterItemDrop returns."""
	ordered = SortDrops(list(dropList), itemModule, raceVnum, lambda row: (row[2], row[3]))
	heights = []
	for row in ordered:
		try:
			itemModule.SelectItem(int(row[2]))
			heights.append(itemModule.GetItemSize()[1])
		except Exception:
			heights.append(1)
	result = []
	pages = packPages(heights) or [[]]
	for pageIndex, page in enumerate(pages):
		for position, index in page:
			result.append((pageIndex, position, ordered[index][2], ordered[index][3]))
	return len(pages) - 1, result
