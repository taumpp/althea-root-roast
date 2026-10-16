# -*- coding: utf-8 -*-
"""Bonus catalog received from the game server (ALTHEA-647).

The client keeps no copy of switchbot or bonus data. The server offers one
versioned catalog after every EnterGame (``BonusCatalogV1 offer <hash> 1``),
this module asks for it once per hash (``/bonus_catalog <hash>``) and installs
the rows only when their count and FNV-1a hash match. The row format is
documented in althea/server-src docs/BONUS_CATALOG.md;
ci/tests/fixtures/bonus_catalog_v1_rows.txt is a byte copy of its golden rows.

Until a catalog is installed (older server, or the reply has not arrived yet)
every accessor answers "unknown": no maximum is highlighted, no scroll is
offered and no switchbot slot can start. That is the safe state; never fall
back to built-in values.
"""

SCHEMA = 1
COMMAND = 'BonusCatalogV1'


def Hash(rows):
	"""FNV-1a 32 of the payload rows joined by newlines, as 8 hex digits."""
	value = 2166136261
	for byte in bytearray('\n'.join(rows).encode('utf-8')):
		value = ((value ^ byte) * 16777619) & 0xffffffff
	return '%08x' % value


def _Ints(text):
	return tuple(int(part) for part in text.split(',')) if text else ()


class Catalog(object):
	"""Parsed catalog rows; Parse raises ValueError on any malformed row."""

	def __init__(self):
		self.regularSlots = 0
		self.vipSlots = 0
		self.instantFee = 0
		self.instantMaxScrolls = 0
		self.scrolls = []          # [(vnum, kind)] in catalog order
		self.sets = {}             # set index -> name
		self.setMap = {}           # (item type, subtype) -> set index
		self.attributes = {}       # apply -> (values lv1..lv5, highest level per set)
		self.addon = {}            # apply -> menu values (last = cap)
		self.elements = ()
		self.elementLimit = 0
		self.beltLines = []        # [(first, last, slots)]
		self.belt = {}             # apply -> (maximum, legacy)
		self.heartCount = 0
		self.heartMinimum = 0
		self.heartMaximum = 0
		self.heartApplies = ()
		self.mountSpeedApply = 0
		self.mountSpeedMinimum = 0
		self.mountSpeedMaximum = 0
		self.mountSpeedMenu = ()
		self.core = {}             # apply -> (kind, values)
		self.costumePools = {}     # costume Value5 -> (count, (fixed apply, value), {apply: value})
		self.fits = []             # [(kind, item type, subtypes or None, first, last)]
		self.rarityMaximumGrade = 0
		self.rarity = {}           # apply -> values per grade

	@classmethod
	def Parse(cls, rows):
		catalog = cls()
		for row in rows:
			catalog._Row(row.split('/'))
		if not catalog.scrolls or not catalog.sets or not catalog.attributes:
			raise ValueError('incomplete catalog')
		for values, levels in catalog.attributes.values():
			if len(levels) != len(catalog.sets):
				raise ValueError('attribute row with a wrong set count')
		return catalog

	def _Row(self, fields):
		kind, args = fields[0], fields[1:]
		if kind == 'slots':
			self.regularSlots, self.vipSlots = int(args[0]), int(args[1])
		elif kind == 'instant':
			self.instantFee, self.instantMaxScrolls = int(args[0]), int(args[1])
		elif kind == 'scroll':
			self.scrolls.append((int(args[0]), args[1]))
		elif kind == 'set':
			self.sets[int(args[0])] = args[1]
		elif kind == 'setmap':
			itemType = int(args[0])
			for pair in args[1].split(','):
				subtype, setIndex = pair.split(':')
				self.setMap[(itemType, int(subtype))] = int(setIndex)
		elif kind == 'attr':
			values = _Ints(args[1])
			if len(values) != 5:
				raise ValueError('attribute row needs five values')
			self.attributes[int(args[0])] = (values, _Ints(args[2]))
		elif kind == 'addon':
			self.addon[int(args[0])] = _Ints(args[1])
		elif kind == 'elements':
			self.elements, self.elementLimit = _Ints(args[0]), int(args[1])
		elif kind == 'beltline':
			self.beltLines.append((int(args[0]), int(args[1]), int(args[2])))
		elif kind == 'belt':
			self.belt[int(args[0])] = (int(args[1]), args[2] == '1')
		elif kind == 'heart':
			self.heartCount, self.heartMinimum, self.heartMaximum = int(args[0]), int(args[1]), int(args[2])
			self.heartApplies = _Ints(args[3])
		elif kind == 'mountspeed':
			self.mountSpeedApply, self.mountSpeedMinimum, self.mountSpeedMaximum = (
				int(args[0]), int(args[1]), int(args[2]))
			self.mountSpeedMenu = _Ints(args[3])
		elif kind == 'core':
			values = _Ints(args[2])
			for apply in _Ints(args[3]):
				self.core[apply] = (args[0], values)
		elif kind == 'iscostume':
			fixedApply, fixedValue = args[2].split(':')
			bonuses = {}
			for pair in args[3].split(','):
				apply, value = pair.split(':')
				bonuses[int(apply)] = int(value)
			self.costumePools[int(args[0])] = (int(args[1]), (int(fixedApply), int(fixedValue)), bonuses)
		elif kind == 'fit':
			subtypes = _Ints(args[2])
			self.fits.append((args[0], int(args[1]), None if subtypes == (-1,) else frozenset(subtypes),
				int(args[3]), int(args[4])))
		elif kind == 'rarity':
			self.rarityMaximumGrade = int(args[0])
		elif kind == 'rarityapply':
			self.rarity[int(args[0])] = _Ints(args[1])
		# Unknown row kinds are ignored so the server may append rows within schema 1.

	# --- item families -------------------------------------------------

	def KindFor(self, vnum, itemType, subtype):
		"""Scroll kind whose item family holds this prototype (first fit wins)."""
		vnum = int(vnum or 0)
		for kind, fitType, subtypes, first, last in self.fits:
			if fitType >= 0 and fitType != itemType:
				continue
			if subtypes is not None and subtype not in subtypes:
				continue
			if (first or last) and not first <= vnum <= last:
				continue
			return kind
		return None

	def SetFor(self, itemType, subtype):
		return self.setMap.get((itemType, subtype))

	# --- maxima --------------------------------------------------------

	def SetMaximum(self, setIndex, apply):
		"""Largest value the set rolls for apply, or None."""
		row = self.attributes.get(apply)
		if not row or setIndex is None or not 0 <= setIndex < len(row[1]):
			return None
		level = row[1][setIndex]
		return max(row[0][:level]) if level else None

	def AddonMaximum(self, apply):
		menu = self.addon.get(apply)
		return max(menu) if menu else None

	def GloveSet(self):
		for index, name in self.sets.items():
			if name == 'glove':
				return index
		return None

	def CoreMaximum(self, apply):
		entry = self.core.get(apply)
		return max(entry[1]) if entry else None


class Receiver(object):
	"""Command handler and holder of the installed catalog."""

	def __init__(self, send=None):
		self.send = send
		self.catalog = None
		self.hash = None
		self.pending = None
		self.listeners = []

	def _Send(self, line):
		if self.send:
			self.send(line)
			return
		import net
		net.SendChatPacket(line)

	def AddListener(self, callback):
		if callback not in self.listeners:
			self.listeners.append(callback)

	def RemoveListener(self, callback):
		if callback in self.listeners:
			self.listeners.remove(callback)

	def Receive(self, action, hashText, payload):
		if action == 'offer':
			if payload != str(SCHEMA) or len(hashText) != 8:
				return
			if hashText == self.hash or (self.pending and self.pending['hash'] == hashText):
				return
			self.pending = {'hash': hashText, 'rows': None, 'payloads': []}
			self._Send('/bonus_catalog %s' % hashText)
			return
		pending = self.pending
		if not pending or pending['hash'] != hashText:
			return
		if action == 'begin':
			pending['rows'] = int(payload)
			pending['payloads'] = []
		elif action == 'row' and pending['rows'] is not None:
			pending['payloads'].append(payload)
		elif action == 'end':
			self.pending = None
			rows = pending['payloads']
			if pending['rows'] != len(rows) or int(payload) != len(rows) or Hash(rows) != hashText:
				return
			try:
				catalog = Catalog.Parse(rows)
			except (ValueError, IndexError):
				return
			self.catalog, self.hash = catalog, hashText
			for callback in list(self.listeners):
				callback()

	def Reset(self):
		self.catalog = None
		self.hash = None
		self.pending = None


receiver = Receiver()


def Current():
	return receiver.catalog


def IsReady():
	return receiver.catalog is not None


# --- switchbot -----------------------------------------------------------

def SlotCount(vip):
	catalog = receiver.catalog
	if not catalog:
		return 0
	return catalog.vipSlots if vip else catalog.regularSlots


def IsSlotAllowed(slot):
	import player
	vip = bool(getattr(player, 'IsVipActive', lambda: False)())
	return 0 <= int(slot) < SlotCount(vip)


def InstantFee():
	catalog = receiver.catalog
	return catalog.instantFee if catalog else 0


def InstantMaxScrolls():
	catalog = receiver.catalog
	return catalog.instantMaxScrolls if catalog else 0


def IsOfferedScroll(vnum):
	catalog = receiver.catalog
	return bool(catalog) and any(scroll == int(vnum) for scroll, kind in catalog.scrolls)


def ScrollKind(vnum):
	catalog = receiver.catalog
	for scroll, kind in (catalog.scrolls if catalog else ()):
		if scroll == int(vnum):
			return kind
	return None


def MenuScrolls(count=None):
	"""One scroll per offered kind, in catalog order of the kinds.

	Several scrolls of one kind behave identically in the switchbot; the menu
	shows the one the player holds most of (catalog order breaks ties).
	"""
	catalog = receiver.catalog
	if not catalog:
		return []
	if count is None:
		import player
		count = player.GetItemCountByVnum
	order, best = [], {}
	for vnum, kind in catalog.scrolls:
		if kind not in best:
			order.append(kind)
			best[kind] = (vnum, count(vnum))
		else:
			owned = count(vnum)
			if owned > best[kind][1]:
				best[kind] = (vnum, owned)
	return [best[kind][0] for kind in order]


def RecommendedScroll(vnum, count=None):
	"""Menu scroll of the item's family; the first offered kind for no item.

	0 while no catalog is installed (the switchbot then cannot start).
	"""
	catalog = receiver.catalog
	if not catalog:
		return 0
	menu = MenuScrolls(count)
	if not menu:
		return 0
	kind = None
	vnum = int(vnum or 0)
	if vnum:
		import item
		item.SelectItem(vnum)
		kind = catalog.KindFor(vnum, item.GetItemType(), item.GetItemSubType())
	for scroll in menu:
		if kind is None or ScrollKind(scroll) == kind:
			return scroll
	return menu[0]


# --- elements ------------------------------------------------------------

def IsElement(apply):
	catalog = receiver.catalog
	return bool(catalog) and int(apply) in catalog.elements


def ElementLimit():
	catalog = receiver.catalog
	return catalog.elementLimit if catalog else 0
