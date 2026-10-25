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

import time

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
		self.rarityTargets = []    # fit tuples of the families the rarity scrolls take
		self.rarityExceptions = [] # fit tuples of prototypes refused inside those families

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
		elif kind in ('raritytarget', 'rarityexcept'):
			subtypes = _Ints(args[1])
			rows = self.rarityTargets if kind == 'raritytarget' else self.rarityExceptions
			rows.append((RARITY_KIND, int(args[0]), None if subtypes == (-1,) else frozenset(subtypes),
				int(args[2]), int(args[3])))
		# Unknown row kinds are ignored so the server may append rows within schema 1.

	# --- item families -------------------------------------------------

	def _Holds(self, fit, vnum, itemType, subtype):
		kind, fitType, subtypes, first, last = fit
		if fitType >= 0 and fitType != itemType:
			return False
		if subtypes is not None and subtype not in subtypes:
			return False
		if (first or last) and not first <= vnum <= last:
			return False
		return True

	def KindFor(self, vnum, itemType, subtype):
		"""Scroll kind whose item family holds this prototype (first fit wins)."""
		vnum = int(vnum or 0)
		for fit in self.fits:
			if self._Holds(fit, vnum, itemType, subtype):
				return fit[0]
		return None

	def Accepts(self, kind, vnum, itemType, subtype):
		"""Whether any family of this kind holds the prototype.

		The rarity families repeat the equipment and glove families, so the
		first fit never names them; ask for the kind instead.
		"""
		vnum = int(vnum or 0)
		for fit in self.fits:
			if fit[0] == kind and self._Holds(fit, vnum, itemType, subtype):
				return True
		return False

	def AcceptsRarity(self, vnum, itemType, subtype):
		"""Whether the rarity scrolls take this prototype in the inventory.

		The server names its own targets and the prototypes it refuses among
		them. A server that sends no target rows leaves the switchbot
		families of the rarity kind, which is all an older catalog knows.
		"""
		vnum = int(vnum or 0)
		for row in self.rarityExceptions:
			if self._Holds(row, vnum, itemType, subtype):
				return False
		if not self.rarityTargets:
			return self.Accepts(RARITY_KIND, vnum, itemType, subtype)
		for row in self.rarityTargets:
			if self._Holds(row, vnum, itemType, subtype):
				return True
		return False

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

	# The server accepts a stream at most once per character every five seconds.
	RETRY_SECONDS = 6.0
	ATTEMPT_LIMIT = 4
	MAX_ROWS = 4096

	def __init__(self, send=None):
		self.send = send
		self.catalog = None
		self.hash = None
		self.pending = None
		self.listeners = []
		self.clock = time.monotonic
		self.offeredHash = None
		self.attempts = 0
		self.nextAttempt = 0
		self.state = 'waiting'

	def _Request(self):
		self.pending = {'hash': self.offeredHash, 'rows': None, 'payloads': []}
		self.attempts += 1
		self.nextAttempt = self.clock() + self.RETRY_SECONDS
		self.state = 'loading'
		self._Send('/bonus_catalog %s' % self.offeredHash)

	def Tick(self):
		# One bounded stream attempt per deadline, independent of window visibility.
		if self.catalog or not self.offeredHash or self.state == 'error' or self.clock() < self.nextAttempt:
			return
		self.pending = None
		if self.attempts >= self.ATTEMPT_LIMIT:
			self.state = 'error'
		else:
			self._Request()

	def Retry(self):
		# A player can reopen/click after exhaustion; repeated clicks cannot flood.
		if self.catalog or not self.offeredHash or self.pending or self.clock() < self.nextAttempt:
			return False
		if self.state == 'error':
			self.attempts = 0
		self._Request()
		return True

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
			if payload != str(SCHEMA) or len(hashText) != 8 or any(c not in '0123456789abcdef' for c in hashText):
				return
			if hashText == self.hash or (self.pending and self.pending['hash'] == hashText):
				return
			if hashText != self.offeredHash:
				self.offeredHash = hashText
				self.catalog, self.hash = None, None
				self.attempts = 0
			if self.attempts < self.ATTEMPT_LIMIT:
				self._Request()
			return
		pending = self.pending
		if not pending or pending['hash'] != hashText:
			return
		if action == 'begin':
			try:
				count = int(payload)
			except (ValueError, TypeError):
				self.pending = None
				return
			if not 0 <= count <= self.MAX_ROWS:
				self.pending = None
				return
			pending['rows'] = count
			pending['payloads'] = []
		elif action == 'row' and pending['rows'] is not None:
			if len(pending['payloads']) >= pending['rows']:
				self.pending = None
				return
			pending['payloads'].append(payload)
		elif action == 'end':
			self.pending = None
			rows = pending['payloads']
			try:
				if pending['rows'] != len(rows) or int(payload) != len(rows) or Hash(rows) != hashText:
					return
				catalog = Catalog.Parse(rows)
			except (ValueError, TypeError, IndexError):
				return
			self.catalog, self.hash = catalog, hashText
			self.state = 'ready'
			for callback in list(self.listeners):
				callback()

	def Reset(self):
		self.catalog = None
		self.hash = None
		self.pending = None
		self.offeredHash = None
		self.attempts = 0
		self.nextAttempt = 0
		self.state = 'waiting'

	def ClearPending(self):
		# A warp can cut a stream; the destination re-offers the same hash,
		# which Receive would otherwise ignore while it is still pending.
		self.pending = None
		self.offeredHash = None
		self.attempts = 0
		self.nextAttempt = 0
		self.state = 'ready' if self.catalog else 'waiting'


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


# --- use on an inventory item --------------------------------------------

# How the server uses a bonus changer: one the catalog does not list takes
# the generic equipment path, a worn target is refused except for the mount
# speed and mount core rerolls, and the generic reroll (equipment, gloves)
# needs an existing bonus to change.
UNLISTED_CHANGER_KIND = 'equipment'
WORN_TARGET_KINDS = ('mount_speed', 'mount_core')
ROLLED_TARGET_KINDS = ('equipment', 'glove')
RARITY_KIND = 'rarity'


def TargetKind(vnum):
	"""Scroll kind of the item family holding this prototype, or None."""
	catalog = receiver.catalog
	vnum = int(vnum or 0)
	if not catalog or not vnum:
		return None
	import item
	item.SelectItem(vnum)
	return catalog.KindFor(vnum, item.GetItemType(), item.GetItemSubType())


def CanUseChanger(scrollVnum, targetVnum, worn, hasBonus):
	"""Whether the server uses this bonus changer on the target item.

	False while no catalog is installed: nothing is highlighted then.
	"""
	target = TargetKind(targetVnum)
	if target is None:
		return False
	kind = ScrollKind(scrollVnum) or UNLISTED_CHANGER_KIND
	if kind != target:
		return False
	if worn and kind not in WORN_TARGET_KINDS:
		return False
	return bool(hasBonus) or kind not in ROLLED_TARGET_KINDS


def AcceptsRarity(targetVnum):
	"""Whether the server takes this prototype as a rarity scroll target."""
	catalog = receiver.catalog
	targetVnum = int(targetVnum or 0)
	if not catalog or not targetVnum:
		return False
	import item
	item.SelectItem(targetVnum)
	return catalog.AcceptsRarity(targetVnum, item.GetItemType(), item.GetItemSubType())


# --- elements ------------------------------------------------------------

def IsElement(apply):
	catalog = receiver.catalog
	return bool(catalog) and int(apply) in catalog.elements


def ElementLimit():
	catalog = receiver.catalog
	return catalog.elementLimit if catalog else 0
