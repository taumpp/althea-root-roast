import json
import os
import re
import time

try:
	import builtins
except ImportError:
	import __builtin__ as builtins


VERSION = 1
LAYOUT_VERSION = 1

LAYOUT_MODE_TASKBAR = "taskbar"
LAYOUT_MODE_FREE = "free"
LAYOUT_MODES = (LAYOUT_MODE_TASKBAR, LAYOUT_MODE_FREE)

EVENT_PICKUP = 1
EVENT_KILL = 2

SOURCE_UNKNOWN = 0
SOURCE_MONSTER = 1
SOURCE_METIN = 2
SOURCE_BOSS = 3
# Rewards of an opened chest; source_vnum is the chest item VNUM (ALTHEA-568).
SOURCE_CHEST = 4

FLAG_PARTY_RECIPIENT = 1

TIME_WINDOWS = (0, 5 * 60, 15 * 60, 30 * 60, 60 * 60)
TRACKED_SOURCES = (SOURCE_MONSTER, SOURCE_METIN, SOURCE_BOSS, SOURCE_CHEST)
SOURCE_FILTERS = (SOURCE_UNKNOWN,) + TRACKED_SOURCES

MAX_EVENTS = 2000
MAX_RECENT = 40
RECENT_LIFETIMES = (3, 5, 7, 10, 15, 0)
DEFAULT_RECENT_LIFETIME = 7
SAVE_INTERVAL = 5.0
LAYOUT_SAVE_INTERVAL = 0.5

_REAL_OPEN = getattr(builtins, "old_open", builtins.open)


def _safe_character_name(name):
	value = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name or "character"))
	value = value.strip("._")
	return value[:64] or "character"


def _to_int(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError, OverflowError):
		return default


def _to_float(value, default=0.0):
	try:
		return float(value)
	except (TypeError, ValueError, OverflowError):
		return default


class DropTrackerLayoutConfig(object):
	def __init__(self, storage_directory="UserData"):
		self.path = os.path.join(
			storage_directory, "drop_tracker_ui.json"
		)
		self.mode = LAYOUT_MODE_TASKBAR
		self.floating_anchor = None
		self._dirty = False
		self._last_save = 0.0
		self.Load()

	def Load(self):
		self.mode = LAYOUT_MODE_TASKBAR
		self.floating_anchor = None
		try:
			with _REAL_OPEN(self.path, "rb") as handle:
				payload = json.loads(handle.read().decode("utf-8"))
			if _to_int(payload.get("version")) != LAYOUT_VERSION:
				return False

			mode = str(payload.get("mode", LAYOUT_MODE_TASKBAR))
			if mode in LAYOUT_MODES:
				self.mode = mode

			anchor = payload.get("floating_anchor")
			if (
				isinstance(anchor, (list, tuple)) and
				len(anchor) == 2
			):
				self.floating_anchor = (
					max(0.0, min(1.0, _to_float(anchor[0]))),
					max(0.0, min(1.0, _to_float(anchor[1]))),
				)
			self._dirty = False
			return True
		except (OSError, ValueError, TypeError, UnicodeError):
			return False

	def SetMode(self, mode):
		mode = (
			LAYOUT_MODE_FREE
			if mode == LAYOUT_MODE_FREE
			else LAYOUT_MODE_TASKBAR
		)
		if self.mode == mode:
			return False
		self.mode = mode
		self._dirty = True
		return True

	def SetFloatingAnchor(self, normalized_x, normalized_y):
		anchor = (
			max(0.0, min(1.0, _to_float(normalized_x))),
			max(0.0, min(1.0, _to_float(normalized_y))),
		)
		if self.floating_anchor == anchor:
			return False
		self.floating_anchor = anchor
		self._dirty = True
		return True

	def ResetFloatingAnchor(self):
		if self.floating_anchor is None:
			return False
		self.floating_anchor = None
		self._dirty = True
		return True

	def Save(self, force=False, now=None):
		if not self._dirty and not force:
			return False
		now = time.time() if now is None else float(now)
		if (
			not force and
			now - self._last_save < LAYOUT_SAVE_INTERVAL
		):
			return False

		directory = os.path.dirname(self.path)
		try:
			if directory and not os.path.isdir(directory):
				os.makedirs(directory, exist_ok=True)
			payload = {
				"version": LAYOUT_VERSION,
				"mode": self.mode,
				"floating_anchor": self.floating_anchor,
			}
			temporary_path = self.path + ".tmp"
			body = json.dumps(
				payload, ensure_ascii=False, separators=(",", ":")
			).encode("utf-8")
			with _REAL_OPEN(temporary_path, "wb") as handle:
				handle.write(body)
				handle.flush()
				os.fsync(handle.fileno())
			os.replace(temporary_path, self.path)
			self._dirty = False
			self._last_save = now
			return True
		except (OSError, TypeError, ValueError):
			try:
				os.unlink(self.path + ".tmp")
			except OSError:
				pass
			return False


class DropTrackerModel(object):
	def __init__(self, storage_directory="UserData"):
		self.storage_directory = storage_directory
		self.character_name = ""
		self.path = ""
		self.events = []
		self.recent = []
		self.recent_updated_at = 0.0
		self.recent_lifetime = DEFAULT_RECENT_LIFETIME
		self.blacklist = set()
		self.paused = False
		self.mode = "summary"
		self.time_window = 0
		self.source_filter = SOURCE_UNKNOWN
		self.page = 0
		self.window_position = None
		self.session_started = time.time()
		self._dirty = False
		self._last_save = 0.0

	def SetIdentity(self, character_name):
		name = str(character_name or "character")
		path = os.path.join(
			self.storage_directory,
			"drop_tracker_%s.json" % _safe_character_name(name),
		)
		if path == self.path:
			return

		if self.path:
			self.Save(force=True)

		self.character_name = name
		self.path = path
		self.events = []
		self.recent = []
		self.recent_updated_at = 0.0
		self.recent_lifetime = DEFAULT_RECENT_LIFETIME
		self.blacklist = set()
		self.paused = False
		self.mode = "summary"
		self.time_window = 0
		self.source_filter = SOURCE_UNKNOWN
		self.page = 0
		self.window_position = None
		self.session_started = time.time()
		self._dirty = False
		self._last_save = 0.0
		self.Load()

	def Load(self):
		if not self.path:
			return False
		try:
			with _REAL_OPEN(self.path, "rb") as handle:
				payload = json.loads(handle.read().decode("utf-8"))
			if _to_int(payload.get("version")) != VERSION:
				return False

			loaded = []
			for row in payload.get("events", []):
				event = self._NormalizeStoredEvent(row)
				if event is not None:
					loaded.append(event)
			self.events = loaded[-MAX_EVENTS:]
			self.recent_lifetime = _to_int(
				payload.get(
					"recent_lifetime", DEFAULT_RECENT_LIFETIME
				)
			)
			if self.recent_lifetime not in RECENT_LIFETIMES:
				self.recent_lifetime = DEFAULT_RECENT_LIFETIME
			self.blacklist = set(
				value for value in (
					_to_int(vnum) for vnum in payload.get("blacklist", [])
				) if value > 0
			)
			self.paused = bool(payload.get("paused", False))
			self.mode = (
				"log" if payload.get("mode") == "log" else "summary"
			)
			self.time_window = _to_int(payload.get("time_window"))
			if self.time_window not in TIME_WINDOWS:
				self.time_window = 0
			self.source_filter = _to_int(payload.get("source_filter"))
			if self.source_filter not in SOURCE_FILTERS:
				self.source_filter = SOURCE_UNKNOWN
			position = payload.get("window_position")
			if (
				isinstance(position, (list, tuple)) and
				len(position) == 2
			):
				self.window_position = (
					_to_int(position[0]), _to_int(position[1])
				)
			self.session_started = float(
				payload.get("session_started", time.time())
			)
			self._dirty = False
			return True
		except (OSError, ValueError, TypeError, UnicodeError):
			return False

	def Save(self, force=False, now=None):
		if not self.path or (not self._dirty and not force):
			return False
		now = time.time() if now is None else float(now)
		if not force and now - self._last_save < SAVE_INTERVAL:
			return False

		directory = os.path.dirname(self.path)
		try:
			if directory and not os.path.isdir(directory):
				os.makedirs(directory, exist_ok=True)
			payload = {
				"version": VERSION,
				"character": self.character_name,
				"session_started": self.session_started,
				"events": self.events[-MAX_EVENTS:],
				"blacklist": sorted(self.blacklist),
				"paused": self.paused,
				"mode": self.mode,
				"time_window": self.time_window,
				"source_filter": self.source_filter,
				"recent_lifetime": self.recent_lifetime,
				"window_position": self.window_position,
			}
			temporary_path = self.path + ".tmp"
			body = json.dumps(
				payload, ensure_ascii=False, separators=(",", ":")
			).encode("utf-8")
			with _REAL_OPEN(temporary_path, "wb") as handle:
				handle.write(body)
				handle.flush()
				os.fsync(handle.fileno())
			os.replace(temporary_path, self.path)
			self._dirty = False
			self._last_save = now
			return True
		except (OSError, TypeError, ValueError):
			try:
				os.unlink(self.path + ".tmp")
			except OSError:
				pass
			return False

	def AddBatch(self, rows, now=None):
		if self.paused:
			return 0
		now = time.time() if now is None else float(now)
		batch = {}
		kills = []

		for row in rows or ():
			event = self._NormalizePacketRow(row, now)
			if event is None or (
				event["kind"] == EVENT_PICKUP and event["item_vnum"] == 1
			):
				continue
			if event["kind"] == EVENT_KILL:
				kills.append(event)
				continue

			key = (
				event["event_id"],
				event["item_vnum"],
				event["source_type"],
				event["source_vnum"],
				event["map_index"],
				event["flags"],
				event["recipient_vid"],
			)
			if key in batch:
				batch[key]["amount"] += event["amount"]
			else:
				batch[key] = event

		added = kills + list(batch.values())
		if not added:
			return 0

		self.events.extend(added)
		if len(self.events) > MAX_EVENTS:
			del self.events[:-MAX_EVENTS]

		if (
			self.recent and self.recent_lifetime > 0 and
			now - self.recent_updated_at >= self.recent_lifetime
		):
			self.recent = []

		for event in added:
			if event["kind"] != EVENT_PICKUP:
				continue
			recent = next((
				row for row in self.recent
				if row["item_vnum"] == event["item_vnum"]
			), None)
			if recent is None:
				recent = dict(event)
				recent["updated_at"] = now
				self.recent.insert(0, recent)
			else:
				recent["amount"] += event["amount"]
				recent["timestamp"] = now
				recent["updated_at"] = now
				recent["source_type"] = event["source_type"]
				recent["source_vnum"] = event["source_vnum"]
				recent["map_index"] = event["map_index"]
				recent["flags"] |= event["flags"]
				self.recent.remove(recent)
				self.recent.insert(0, recent)
		if len(self.recent) > MAX_RECENT:
			del self.recent[MAX_RECENT:]
		if any(
			event["kind"] == EVENT_PICKUP for event in added
		):
			self.recent_updated_at = now

		self._dirty = True
		return len(added)

	def GetRecent(self, now=None, limit=5):
		now = time.time() if now is None else float(now)
		if (
			self.recent_lifetime > 0 and self.recent_updated_at and
			now - self.recent_updated_at >= self.recent_lifetime
		):
			self.recent = []
			return []
		return [
			event for event in self.recent
			if event["item_vnum"] != 1 and event["item_vnum"] not in self.blacklist
		][:max(0, int(limit))]

	def GetRows(self, now=None):
		now = time.time() if now is None else float(now)
		if self.mode == "log":
			return self.GetLog(now)
		return self.GetSummary(now)

	def GetSummary(self, now=None):
		now = time.time() if now is None else float(now)
		summary = {}
		for event in self._FilteredEvents(now):
			if event["kind"] != EVENT_PICKUP:
				continue
			key = (
				event["item_vnum"],
				event["source_type"],
				event["source_vnum"],
			)
			if key not in summary:
				summary[key] = {
					"kind": EVENT_PICKUP,
					"item_vnum": event["item_vnum"],
					"source_type": event["source_type"],
					"source_vnum": event["source_vnum"],
					"amount": 0,
					"timestamp": event["timestamp"],
					"map_index": event["map_index"],
					"flags": event["flags"],
				}
			entry = summary[key]
			entry["amount"] += event["amount"]
			entry["timestamp"] = max(
				entry["timestamp"], event["timestamp"]
			)
			entry["flags"] |= event["flags"]

		return sorted(
			summary.values(),
			key=lambda event: (
				event["amount"],
				event["timestamp"],
			),
			reverse=True,
		)

	def GetItemSummary(self, now=None, include_blacklisted=False):
		"""Build presentation rows without discarding concrete source rows."""
		now = time.time() if now is None else float(now)
		items = {}
		for source in self._BuildConcreteSummary(
			now, include_blacklisted=include_blacklisted
		):
			item_vnum = source["item_vnum"]
			if item_vnum not in items:
				items[item_vnum] = {
					"kind": EVENT_PICKUP,
					"item_vnum": item_vnum,
					"source_type": source["source_type"],
					"source_vnum": source["source_vnum"],
					"source_count": 0,
					"sources": [],
					"amount": 0,
					"timestamp": source["timestamp"],
					"map_index": source["map_index"],
					"flags": 0,
				}
			entry = items[item_vnum]
			entry["sources"].append(source)
			entry["source_count"] += 1
			entry["amount"] += source["amount"]
			entry["flags"] |= source["flags"]
			if source["timestamp"] >= entry["timestamp"]:
				entry["timestamp"] = source["timestamp"]
				entry["map_index"] = source["map_index"]

		for entry in items.values():
			entry["sources"].sort(
				key=lambda source: (
					source["amount"], source["timestamp"]
				),
				reverse=True,
			)
			if entry["sources"]:
				dominant = entry["sources"][0]
				entry["source_type"] = dominant["source_type"]
				entry["source_vnum"] = dominant["source_vnum"]

		return sorted(
			items.values(),
			key=lambda event: (
				event["amount"],
				event["timestamp"],
			),
			reverse=True,
		)

	def GetSourceSummary(self, now=None):
		now = time.time() if now is None else float(now)
		sources = {}
		for event in self._FilteredEvents(
			now, include_blacklisted=True
		):
			key = (event["source_type"], event["source_vnum"])
			if key not in sources:
				sources[key] = {
					"source_type": event["source_type"],
					"source_vnum": event["source_vnum"],
					"kills": 0,
					"items": 0,
					"pickup_events": 0,
					"unique_items": set(),
					"timestamp": event["timestamp"],
				}
			entry = sources[key]
			entry["timestamp"] = max(
				entry["timestamp"], event["timestamp"]
			)
			if event["kind"] == EVENT_KILL:
				entry["kills"] += 1
			else:
				entry["pickup_events"] += 1
				entry["items"] += event["amount"]
				entry["unique_items"].add(event["item_vnum"])

		result = []
		for entry in sources.values():
			row = dict(entry)
			row["unique_items"] = len(entry["unique_items"])
			result.append(row)
		return sorted(
			result,
			key=lambda source: (
				source["items"],
				source["kills"],
				source["timestamp"],
			),
			reverse=True,
		)

	def GetBlacklistedSummary(self, now=None):
		now = time.time() if now is None else float(now)
		return [
			row for row in self._BuildConcreteSummary(
				now, include_blacklisted=True
			)
			if row["item_vnum"] in self.blacklist
		]

	def GetLog(self, now=None):
		now = time.time() if now is None else float(now)
		return list(reversed([
			event for event in self._FilteredEvents(now)
			if event["kind"] == EVENT_PICKUP
		]))

	def GetStats(self, now=None):
		now = time.time() if now is None else float(now)
		stats = {
			"kills": 0,
			"kills_monster": 0,
			"kills_metin": 0,
			"kills_boss": 0,
			"items": 0,
			"unique_items": set(),
			"sources": set(),
			"party_items": 0,
		}
		for event in self._FilteredEvents(now, include_blacklisted=True):
			stats["sources"].add((
				event["source_type"], event["source_vnum"]
			))
			if event["kind"] == EVENT_KILL:
				stats["kills"] += 1
				key = {
					SOURCE_MONSTER: "kills_monster",
					SOURCE_METIN: "kills_metin",
					SOURCE_BOSS: "kills_boss",
				}.get(event["source_type"])
				if key:
					stats[key] += 1
			else:
				stats["items"] += event["amount"]
				stats["unique_items"].add(event["item_vnum"])
				if event["flags"] & FLAG_PARTY_RECIPIENT:
					stats["party_items"] += event["amount"]
		stats["unique_items"] = len(stats["unique_items"])
		stats["sources"] = len(stats["sources"])
		return stats

	def GetSessionDuration(self, now=None):
		now = time.time() if now is None else float(now)
		return max(0, int(now - self.session_started))

	def Clear(self):
		self.events = []
		self.recent = []
		self.recent_updated_at = 0.0
		self.page = 0
		self.session_started = time.time()
		self._dirty = True

	def SetPaused(self, value):
		value = bool(value)
		if self.paused != value:
			self.paused = value
			self._dirty = True

	def SetMode(self, mode):
		mode = "log" if mode == "log" else "summary"
		if self.mode != mode:
			self.mode = mode
			self.page = 0
			self._dirty = True

	def CycleTimeWindow(self):
		index = TIME_WINDOWS.index(self.time_window)
		self.time_window = TIME_WINDOWS[(index + 1) % len(TIME_WINDOWS)]
		self.page = 0
		self._dirty = True
		return self.time_window

	def CycleSourceFilter(self):
		index = SOURCE_FILTERS.index(self.source_filter)
		self.source_filter = SOURCE_FILTERS[
			(index + 1) % len(SOURCE_FILTERS)
		]
		self.page = 0
		self._dirty = True
		return self.source_filter

	def SetRecentLifetime(self, seconds):
		if seconds not in RECENT_LIFETIMES:
			return False
		self.recent_lifetime = seconds
		self._dirty = True
		return True

	def CycleRecentLifetime(self):
		index = RECENT_LIFETIMES.index(self.recent_lifetime)
		self.SetRecentLifetime(RECENT_LIFETIMES[
			(index + 1) % len(RECENT_LIFETIMES)
		])
		return self.recent_lifetime

	def ToggleBlacklist(self, item_vnum):
		item_vnum = _to_int(item_vnum)
		if item_vnum <= 0:
			return False
		if item_vnum in self.blacklist:
			self.blacklist.remove(item_vnum)
			blacklisted = False
		else:
			self.blacklist.add(item_vnum)
			blacklisted = True
		self.page = 0
		self._dirty = True
		return blacklisted

	def SetWindowPosition(self, x, y):
		position = (_to_int(x), _to_int(y))
		if position != self.window_position:
			self.window_position = position
			self._dirty = True

	def _FilteredEvents(self, now, include_blacklisted=False):
		minimum = (
			0.0 if self.time_window == 0 else now - self.time_window
		)
		for event in self.events:
			# Keep old currency records on disk, outside every tracker view.
			if event["kind"] == EVENT_PICKUP and event["item_vnum"] == 1:
				continue
			if event["timestamp"] < minimum:
				continue
			if (
				self.source_filter != SOURCE_UNKNOWN and
				event["source_type"] != self.source_filter
			):
				continue
			if (
				not include_blacklisted and
				event["kind"] == EVENT_PICKUP and
				event["item_vnum"] in self.blacklist
			):
				continue
			yield event

	def _BuildConcreteSummary(self, now, include_blacklisted=False):
		summary = {}
		for event in self._FilteredEvents(
			now, include_blacklisted=include_blacklisted
		):
			if event["kind"] != EVENT_PICKUP:
				continue
			key = (
				event["item_vnum"],
				event["source_type"],
				event["source_vnum"],
			)
			if key not in summary:
				summary[key] = {
					"kind": EVENT_PICKUP,
					"item_vnum": event["item_vnum"],
					"source_type": event["source_type"],
					"source_vnum": event["source_vnum"],
					"amount": 0,
					"timestamp": event["timestamp"],
					"map_index": event["map_index"],
					"flags": event["flags"],
				}
			entry = summary[key]
			entry["amount"] += event["amount"]
			entry["timestamp"] = max(
				entry["timestamp"], event["timestamp"]
			)
			entry["flags"] |= event["flags"]
		return sorted(
			summary.values(),
			key=lambda event: (event["amount"], event["timestamp"]),
			reverse=True,
		)

	def _NormalizePacketRow(self, row, timestamp):
		if not isinstance(row, (list, tuple)) or len(row) != 9:
			return None
		kind = _to_int(row[0])
		source_type = _to_int(row[1])
		flags = _to_int(row[2])
		item_vnum = _to_int(row[3])
		source_vnum = _to_int(row[4])
		amount = _to_int(row[5])
		event_id = _to_int(row[6])
		map_index = _to_int(row[7])
		recipient_vid = _to_int(row[8])
		if kind not in (EVENT_PICKUP, EVENT_KILL):
			return None
		if source_type not in TRACKED_SOURCES:
			return None
		if source_type == SOURCE_CHEST and kind != EVENT_PICKUP:
			return None
		if event_id <= 0 or source_vnum <= 0:
			return None
		if kind == EVENT_PICKUP and (item_vnum <= 0 or amount <= 0):
			return None
		if kind == EVENT_KILL:
			item_vnum = 0
			amount = 1
		return {
			"kind": kind,
			"source_type": source_type,
			"flags": flags,
			"item_vnum": item_vnum,
			"source_vnum": source_vnum,
			"amount": amount,
			"event_id": event_id,
			"map_index": map_index,
			"recipient_vid": recipient_vid,
			"timestamp": float(timestamp),
		}

	def _NormalizeStoredEvent(self, row):
		if not isinstance(row, dict):
			return None
		return self._NormalizePacketRow((
			row.get("kind"),
			row.get("source_type"),
			row.get("flags"),
			row.get("item_vnum"),
			row.get("source_vnum"),
			row.get("amount"),
			row.get("event_id"),
			row.get("map_index"),
			row.get("recipient_vid"),
		), float(row.get("timestamp", 0.0)))
