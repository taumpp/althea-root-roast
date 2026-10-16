import time


MAX_DURATION_SECONDS = 30 * 24 * 60 * 60
REQUEST_INTERVAL = 0.25
AUTO_SCAN_INTERVAL = 0.50
CONFIRM_TIMEOUT = 1.0
MISSING_RETRY = 10.0
REJECTED_RETRY = 30.0
DURATION_GRACE = 3.0
MANUAL_ONLY_VNUMS = frozenset((71018, 71019, 71020))

# Every special tab the server can store items in; the server routes cooked
# fish and elixirs to Consumable (server-src special_inventory_destination_policy.h).
SPECIAL_INVENTORY_STARTS = (
	"SKILL_BOOK_INVENTORY_SLOT_START",
	"UPGRADE_ITEMS_INVENTORY_SLOT_START",
	"STONE_INVENTORY_SLOT_START",
	"GIFT_BOX_INVENTORY_SLOT_START",
	"SWITCH_INVENTORY_SLOT_START",
	"COSTUME_INVENTORY_SLOT_START",
	"CONSUMABLE_INVENTORY_SLOT_START",
)


def _merge_unique(current, additions):
	seen = set(current)
	merged = list(current)
	for value in additions:
		if value and value not in seen:
			seen.add(value)
			merged.append(value)
	return merged


class QuickBuffItemPolicy(object):
	def __init__(self, item_module, player_module, allowed_vnums=None):
		self.item = item_module
		self.player = player_module
		self.allowed_vnums = None if allowed_vnums is None else frozenset(allowed_vnums)

	def Describe(self, vnum, slot=None):
		try:
			vnum = int(vnum)
			if vnum <= 0 or (self.allowed_vnums is not None and vnum not in self.allowed_vnums):
				return None
			self.item.SelectItem(vnum)
			if self.item.IsEquipmentVID(vnum):
				return None
			if vnum in MANUAL_ONLY_VNUMS:
				return {
					"vnum": vnum,
					"kind": "instant",
					"duration": 0,
					"automatic": False,
				}
			item_type = self.item.GetItemType()
			subtype = self.item.GetItemSubType()
			if item_type == self.item.ITEM_TYPE_BLEND:
				duration = 0
				if slot is not None:
					duration = int(self.player.GetItemMetinSocket(slot, 2))
				if duration <= 0:
					duration = int(self.item.GetValue(2))
				kind = "blend"
			elif (
				item_type in (
					self.item.ITEM_TYPE_USE,
					getattr(self.item, "ITEM_TYPE_UNIQUE", -1),
				)
				and subtype == self.item.USE_ABILITY_UP
			):
				kind = "ability"
				duration = int(self.item.GetValue(1))
			elif (
				item_type == self.item.ITEM_TYPE_USE
				and subtype == getattr(self.item, "USE_AFFECT", -1)
			):
				kind = "affect"
				duration = int(self.item.GetValue(3))
			else:
				return None
			if not 0 < duration <= MAX_DURATION_SECONDS:
				return None
			return {
				"vnum": vnum,
				"kind": kind,
				"duration": duration,
				"automatic": True,
			}
		except (
			AttributeError,
			IndexError,
			KeyError,
			TypeError,
			ValueError,
			OverflowError,
		):
			return None

	def RuntimeDuration(self, slot, descriptor):
		if descriptor["kind"] != "blend":
			return descriptor["duration"]
		try:
			remaining = int(self.player.GetItemMetinSocket(slot, 2))
		except (AttributeError, TypeError, ValueError, OverflowError):
			remaining = 0
		return remaining if remaining > 0 else descriptor["duration"]

	def IsActiveBlend(self, slot, descriptor):
		if descriptor["kind"] != "blend":
			return False
		try:
			return bool(self.player.GetItemMetinSocket(slot, 3))
		except (AttributeError, TypeError, ValueError, OverflowError):
			return False


class InventoryScanner(object):
	def __init__(
		self,
		item_module,
		player_module,
		default_vnums=(),
		excluded_vnums=(),
	):
		self.item = item_module
		self.player = player_module
		self.default_vnums = tuple(default_vnums)
		self.excluded_vnums = frozenset(excluded_vnums)

	def Positions(self):
		seen = set()
		for slot in range(max(0, int(self.player.ITEM_SLOT_COUNT))):
			seen.add(slot)
			yield slot
		special_count = max(
			0, int(getattr(self.player, "SPECIAL_ITEM_SLOT_COUNT", 0))
		)
		for constant in SPECIAL_INVENTORY_STARTS:
			start = getattr(self.item, constant, None)
			if start is None:
				continue
			try:
				start = int(start)
			except (TypeError, ValueError, OverflowError):
				continue
			for slot in range(start, start + special_count):
				if slot not in seen:
					seen.add(slot)
					yield slot

	def Find(self, vnum):
		try:
			vnum = int(vnum)
		except (TypeError, ValueError, OverflowError):
			return None
		for slot in self.Positions():
			if (
				self.player.GetItemIndex(slot) == vnum
				and self.player.GetItemCount(slot) > 0
			):
				return slot
		return None

	def MatchingPositions(self, vnum):
		try:
			vnum = int(vnum)
		except (TypeError, ValueError, OverflowError):
			return ()
		return tuple(
			slot for slot in self.Positions()
			if self.player.GetItemIndex(slot) == vnum
			and self.player.GetItemCount(slot) > 0
		)

	def TotalCount(self, vnum):
		return sum(
			max(0, int(self.player.GetItemCount(slot)))
			for slot in self.MatchingPositions(vnum)
		)

	def Catalog(self, policy):
		ordered = []
		entries = {}
		for raw_vnum in self.default_vnums:
			try:
				vnum = int(raw_vnum)
			except (TypeError, ValueError, OverflowError):
				continue
			if (
				vnum <= 0
				or vnum in entries
				or vnum in self.excluded_vnums
			):
				continue
			entries[vnum] = {
				"vnum": vnum,
				"slot": None,
				"count": 0,
				"descriptor": None,
			}
			ordered.append(vnum)

		for slot in self.Positions():
			try:
				vnum = int(self.player.GetItemIndex(slot))
				count = max(0, int(self.player.GetItemCount(slot)))
			except (AttributeError, TypeError, ValueError, OverflowError):
				continue
			if (
				vnum <= 0
				or count <= 0
				or vnum in self.excluded_vnums
			):
				continue
			descriptor = policy.Describe(vnum, slot)
			if vnum not in entries:
				if descriptor is None:
					continue
				entries[vnum] = {
					"vnum": vnum,
					"slot": slot,
					"count": 0,
					"descriptor": descriptor,
				}
				ordered.append(vnum)
			entry = entries[vnum]
			if entry["slot"] is None:
				entry["slot"] = slot
			if descriptor is not None and entry["descriptor"] is None:
				entry["descriptor"] = descriptor
			entry["count"] += count

		return [entries[vnum] for vnum in ordered]


class QuickBuffController(object):
	def __init__(
		self,
		model,
		policy,
		scanner,
		net_module,
		player_module,
		now_fn=None,
		active_effect_remaining_fn=None,
	):
		self.model = model
		self.policy = policy
		self.scanner = scanner
		self.net = net_module
		self.player = player_module
		self.now_fn = now_fn or time.time
		self.active_effect_remaining_fn = active_effect_remaining_fn or (lambda vnum: 0)
		self.manual_queue = []
		self.automatic_queue = []
		self.pending_requests = []
		self.vip_active = self._NativeVipActive()
		self.last_auto_scan_at = float("-inf")
		self.last_request_at = float("-inf")

	def _NativeVipActive(self):
		try:
			return bool(self.player.IsVipActive())
		except (AttributeError, TypeError, ValueError):
			return False

	def QueueManual(self):
		configured = self.model.ExecutionVnums()
		pending = self._PendingVnums()
		candidates = [
			vnum for vnum in configured
			if vnum not in pending and not self.active_effect_remaining_fn(vnum)
			and self.scanner.Find(vnum) is not None
			and self.policy.Describe(vnum, self.scanner.Find(vnum)) is not None
		]
		self.manual_queue = _merge_unique(self.manual_queue, candidates)
		if candidates:
			manual = set(candidates)
			self.automatic_queue = [
				vnum for vnum in self.automatic_queue if vnum not in manual
			]
		return bool(candidates)

	def OnProfileChanged(self):
		self.manual_queue = []
		self.automatic_queue = []

	def OnVipStatus(self, active):
		self.vip_active = bool(active)
		if not self.vip_active:
			self.automatic_queue = []

	def _PendingVnums(self):
		return set(request["vnum"] for request in self.pending_requests)

	def Tick(self, now=None):
		now = self.now_fn() if now is None else float(now)
		self._ConfirmPending(now)

		native_vip = self._NativeVipActive()
		if native_vip != self.vip_active:
			self.OnVipStatus(native_vip)

		if (
			self.model.path
			and self.model.auto_enabled
			and self.vip_active
			and now - self.last_auto_scan_at >= AUTO_SCAN_INTERVAL
		):
			self.last_auto_scan_at = now
			pending = self._PendingVnums()
			manual = set(self.manual_queue)
			self.automatic_queue = _merge_unique(
				self.automatic_queue,
				[
					vnum for vnum in self.model.DueVnums(now)
					if vnum not in pending and vnum not in manual
					and self._CanUseAutomatically(vnum)
				],
			)

		if now - self.last_request_at < REQUEST_INTERVAL:
			self.model.Save(now=now)
			return

		if self.manual_queue:
			queue = self.manual_queue
			automatic = False
		elif self.model.auto_enabled and self.vip_active and self.automatic_queue:
			queue = self.automatic_queue
			automatic = True
		else:
			self.model.Save(now=now)
			return

		vnum = queue.pop(0)
		self._UseOrSchedule(vnum, now, automatic)
		self.model.Save(now=now)

	def _CanUseAutomatically(self, vnum):
		slot = self.scanner.Find(vnum)
		if slot is None:
			descriptor = self.policy.Describe(vnum)
		else:
			descriptor = self.policy.Describe(vnum, slot)
		return bool(descriptor and descriptor.get("automatic"))

	def _UseOrSchedule(self, vnum, now, automatic):
		slot = self.scanner.Find(vnum)
		if slot is None:
			if automatic:
				self.model.SetNextDue(vnum, now + MISSING_RETRY)
			return False

		descriptor = self.policy.Describe(vnum, slot)
		if descriptor is None:
			if automatic:
				self.model.SetNextDue(vnum, now + REJECTED_RETRY)
			return False
		if automatic and not descriptor.get("automatic"):
			return False

		duration = self.policy.RuntimeDuration(slot, descriptor)
		remaining = self.active_effect_remaining_fn(vnum)
		if remaining > 0:
			self.model.SetNextDue(vnum, now + remaining + DURATION_GRACE)
			return False
		if self.policy.IsActiveBlend(slot, descriptor):
			self.model.SetNextDue(vnum, now + duration + DURATION_GRACE)
			return False

		request = {
			"vnum": vnum,
			"kind": descriptor["kind"],
			"request_at": now,
			"deadline": now + CONFIRM_TIMEOUT,
			"duration": duration,
			"automatic": bool(descriptor.get("automatic")),
			"count": self.scanner.TotalCount(vnum),
			"positions": self.scanner.MatchingPositions(vnum),
			"active_socket": bool(
				self.player.GetItemMetinSocket(slot, 3)
				if descriptor["kind"] == "blend" else False
			),
		}
		self.net.SendItemUsePacket(slot)
		self.last_request_at = now
		self.pending_requests.append(request)
		return True

	def _AnyActiveBlend(self, vnum):
		for slot in self.scanner.MatchingPositions(vnum):
			try:
				if self.player.GetItemMetinSocket(slot, 3):
					return True
			except (AttributeError, TypeError, ValueError, OverflowError):
				pass
		return False

	def _ConfirmPending(self, now):
		remaining = []
		for request in self.pending_requests:
			vnum = request["vnum"]
			confirmed = (
				self.scanner.TotalCount(vnum) < request["count"]
				or self.scanner.MatchingPositions(vnum) != request["positions"]
				or (
					request["kind"] == "blend"
					and not request["active_socket"]
					and self._AnyActiveBlend(vnum)
				)
			)
			if confirmed:
				if request["automatic"]:
					self.model.SetNextDue(
						vnum,
						request["request_at"]
						+ request["duration"]
						+ DURATION_GRACE,
					)
			elif now >= request["deadline"]:
				if request["automatic"]:
					self.model.SetNextDue(vnum, now + REJECTED_RETRY)
			else:
				remaining.append(request)
		self.pending_requests = remaining

	def Destroy(self):
		self.manual_queue = []
		self.automatic_queue = []
		self.pending_requests = []
		self.model.Save(force=True)
