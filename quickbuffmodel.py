import json
import math
import os
import re
import time

try:
	import builtins
except ImportError:
	import __builtin__ as builtins


VERSION = 3
LEGACY_VERSION = 1
PROFILE_NAMES = ("pvm", "pvp")
MAX_SELECTED_COUNT = 40
MAX_VNUM = 2147483647
MAX_FUTURE_SECONDS = 30 * 24 * 60 * 60
SAVE_INTERVAL = 1.0

_REAL_OPEN = getattr(builtins, "old_open", builtins.open)


def _safe_character_name(name):
	value = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name or "character"))
	value = value.strip("._")
	return value[:64] or "character"


def _coerce_vnum(value):
	if isinstance(value, bool):
		return 0
	try:
		value = int(value)
	except (TypeError, ValueError, OverflowError):
		return 0
	return value if 0 < value <= MAX_VNUM else 0


def _stored_vnum(value, allow_zero=False):
	if isinstance(value, bool) or not isinstance(value, int):
		return None
	minimum = 0 if allow_zero else 1
	if minimum <= value <= MAX_VNUM:
		return value
	return None


def _stored_number(value):
	if isinstance(value, bool) or not isinstance(value, (int, float)):
		return None
	value = float(value)
	return value if math.isfinite(value) else None


def _stable_unique(values):
	seen = set()
	ordered = []
	for value in values:
		if value and value not in seen:
			seen.add(value)
			ordered.append(value)
	return ordered


class QuickBuffModel(object):
	def __init__(self, storage_directory="UserData", now_fn=None):
		self.storage_directory = storage_directory
		self.now_fn = now_fn or time.time
		self.character_name = ""
		self.path = ""
		self._ResetState()

	def _ResetState(self):
		self.profiles = {name: [0] * MAX_SELECTED_COUNT for name in PROFILE_NAMES}
		self.profile_enabled = {name: [False] * MAX_SELECTED_COUNT for name in PROFILE_NAMES}
		self.active_profile = "pvm"
		self.auto_enabled = False
		self.window_position = None
		self.next_due = {}
		self.needs_migration = False
		self._dirty = False
		self._last_save = 0.0

	def SetIdentity(self, character_name):
		name = str(character_name or "character")
		next_path = os.path.join(
			self.storage_directory,
			"quick_buffs_%s.json" % _safe_character_name(name),
		)
		if next_path == self.path:
			return False
		if self.path and self._dirty:
			self.Save(force=True)
		self.character_name = name
		self.path = next_path
		self._ResetState()
		self.Load()
		return True

	def IsSelected(self, vnum):
		vnum = _coerce_vnum(vnum)
		slots = self.profiles[self.active_profile]
		return bool(vnum in slots and self.profile_enabled[self.active_profile][slots.index(vnum)])

	@property
	def items(self):
		return self.ExecutionVnums()

	def Slots(self):
		return list(self.profiles[self.active_profile])

	def EnabledSlots(self):
		return list(self.profile_enabled[self.active_profile])

	def SetSlotEnabled(self, index, enabled):
		if not isinstance(index, int) or not 0 <= index < MAX_SELECTED_COUNT:
			return False
		if not self.profiles[self.active_profile][index]:
			return False
		enabled = bool(enabled)
		flags = self.profile_enabled[self.active_profile]
		if flags[index] == enabled:
			return False
		flags[index] = enabled
		self._dirty = True
		return True

	def SetProfile(self, profile):
		if profile not in PROFILE_NAMES or profile == self.active_profile:
			return False
		self.active_profile = profile
		self._dirty = True
		return True

	def SetSlot(self, index, vnum):
		if not isinstance(index, int) or not 0 <= index < MAX_SELECTED_COUNT:
			return False
		vnum = _coerce_vnum(vnum)
		if not vnum:
			return False
		slots = self.profiles[self.active_profile]
		if slots[index] == vnum:
			return False
		if vnum in slots:
			previous = slots.index(vnum)
			slots[previous] = 0
			self.profile_enabled[self.active_profile][previous] = False
		slots[index] = vnum
		self.profile_enabled[self.active_profile][index] = True
		self._dirty = True
		return True

	def RemoveSlot(self, index):
		if not isinstance(index, int) or not 0 <= index < MAX_SELECTED_COUNT:
			return False
		slots = self.profiles[self.active_profile]
		if not slots[index]:
			return False
		slots[index] = 0
		self.profile_enabled[self.active_profile][index] = False
		self._dirty = True
		return True

	def ClearProfile(self):
		if not any(self.profiles[self.active_profile]):
			return False
		self.profiles[self.active_profile] = [0] * MAX_SELECTED_COUNT
		self.profile_enabled[self.active_profile] = [False] * MAX_SELECTED_COUNT
		self._dirty = True
		return True

	def RetainVnums(self, allowed_vnums):
		allowed = frozenset(allowed_vnums)
		changed = False
		for name in PROFILE_NAMES:
			for index, vnum in enumerate(self.profiles[name]):
				if vnum and vnum not in allowed:
					self.profiles[name][index] = 0
					self.profile_enabled[name][index] = False
					changed = True
		if changed:
			self._dirty = True
		return changed

	def SetSelected(self, vnum, selected):
		vnum = _coerce_vnum(vnum)
		if not vnum:
			return False
		selected = bool(selected)
		slots = self.profiles[self.active_profile]
		if selected:
			if vnum in slots:
				return self.SetSlotEnabled(slots.index(vnum), True)
			if 0 not in slots:
				return False
			index = slots.index(0)
			slots[index] = vnum
			self.profile_enabled[self.active_profile][index] = True
		else:
			if vnum not in slots:
				return False
			return self.SetSlotEnabled(slots.index(vnum), False)
		self._dirty = True
		return True

	def SetAutoEnabled(self, enabled):
		enabled = bool(enabled)
		if self.auto_enabled == enabled:
			return False
		self.auto_enabled = enabled
		self._dirty = True
		return True

	def SetWindowPosition(self, position):
		if position is None:
			next_position = None
		elif isinstance(position, (list, tuple)) and len(position) == 2:
			try:
				next_position = (int(position[0]), int(position[1]))
			except (TypeError, ValueError, OverflowError):
				return False
		else:
			return False
		if self.window_position == next_position:
			return False
		self.window_position = next_position
		self._dirty = True
		return True

	def SetNextDue(self, vnum, due_at):
		vnum = _coerce_vnum(vnum)
		due_at = _stored_number(due_at)
		if not vnum or due_at is None:
			return False
		now = float(self.now_fn())
		due_at = max(0.0, min(due_at, now + MAX_FUTURE_SECONDS))
		if self.next_due.get(vnum) == due_at:
			return False
		self.next_due[vnum] = due_at
		self._dirty = True
		return True

	def GetNextDue(self, vnum):
		return float(self.next_due.get(_coerce_vnum(vnum), 0.0))

	def ExecutionVnums(self):
		return [vnum for vnum, enabled in zip(self.profiles[self.active_profile], self.profile_enabled[self.active_profile]) if vnum and enabled]

	def DueVnums(self, now=None):
		now = self.now_fn() if now is None else float(now)
		return [
			vnum for vnum in self.ExecutionVnums()
			if self.GetNextDue(vnum) <= now
		]

	def _LoadProfiles(self, payload):
		version = payload.get("version")
		if version == VERSION:
			stored = payload.get("profiles")
			if not isinstance(stored, dict):
				return None
			profiles = {}
			for name in PROFILE_NAMES:
				values = stored.get(name)
				if not isinstance(values, list) or len(values) != MAX_SELECTED_COUNT:
					return None
				if any(_stored_vnum(value, allow_zero=True) is None for value in values):
					return None
				if len(set(value for value in values if value)) != len([value for value in values if value]):
					return None
				profiles[name] = list(values)
			stored_enabled = payload.get("enabled")
			if not isinstance(stored_enabled, dict):
				return None
			enabled = {}
			for name in PROFILE_NAMES:
				flags = stored_enabled.get(name)
				if not isinstance(flags, list) or len(flags) != MAX_SELECTED_COUNT or any(not isinstance(flag, bool) for flag in flags):
					return None
				enabled[name] = [flag and bool(vnum) for flag, vnum in zip(flags, profiles[name])]
			return profiles, enabled

		if version == 2:
			values = payload.get("items")
			if not isinstance(values, list) or len(values) > MAX_SELECTED_COUNT:
				return None
			items = []
			for value in values:
				vnum = _stored_vnum(value)
				if vnum is None:
					return None
				items.append(vnum)
			items = _stable_unique(items)
			return self._LegacyProfiles(items)

		if version != LEGACY_VERSION:
			return None
		profiles = payload.get("profiles")
		if not isinstance(profiles, dict):
			return None
		legacy_items = []
		for profile in PROFILE_NAMES:
			values = profiles.get(profile)
			if not isinstance(values, list) or len(values) > MAX_SELECTED_COUNT:
				return None
			for value in values:
				vnum = _stored_vnum(value, allow_zero=True)
				if vnum is None:
					return None
				legacy_items.append(vnum)
		items = _stable_unique(legacy_items)[:MAX_SELECTED_COUNT]
		return self._LegacyProfiles(items)

	def _LegacyProfiles(self, items):
		profiles = {name: list(items) + [0] * (MAX_SELECTED_COUNT - len(items)) for name in PROFILE_NAMES}
		enabled = {name: [bool(value) for value in profiles[name]] for name in PROFILE_NAMES}
		return profiles, enabled

	def Load(self):
		if not self.path:
			return False
		self._ResetState()
		try:
			with _REAL_OPEN(self.path, "rb") as handle:
				payload = json.loads(handle.read().decode("utf-8"))
			if not isinstance(payload, dict):
				return False

			profile_state = self._LoadProfiles(payload)
			if profile_state is None:
				return False
			profiles, enabled = profile_state
			active_profile = payload.get("active_profile", "pvm")
			if active_profile not in PROFILE_NAMES:
				return False

			auto_enabled = payload.get("auto_enabled", False)
			if not isinstance(auto_enabled, bool):
				return False

			position = payload.get("window_position")
			window_position = None
			if isinstance(position, (list, tuple)) and len(position) == 2:
				if all(
					isinstance(value, int) and not isinstance(value, bool)
					for value in position
				):
					window_position = (position[0], position[1])

			now = float(self.now_fn())
			next_due = {}
			stored_due = payload.get("next_due", {})
			if isinstance(stored_due, dict):
				for key, value in stored_due.items():
					vnum = _coerce_vnum(key)
					due_at = _stored_number(value)
					if not vnum or due_at is None:
						continue
					next_due[vnum] = max(
						0.0, min(due_at, now + MAX_FUTURE_SECONDS)
					)

			self.profiles = profiles
			self.profile_enabled = enabled
			self.active_profile = active_profile if payload.get("version") == VERSION else "pvm"
			self.auto_enabled = auto_enabled
			self.window_position = window_position
			self.next_due = next_due
			self.needs_migration = payload.get("version") != VERSION
			self._dirty = self.needs_migration
			return True
		except (OSError, ValueError, TypeError, UnicodeError, OverflowError):
			self._ResetState()
			return False

	def Save(self, force=False, now=None):
		if not self.path or (not self._dirty and not force):
			return False
		now = self.now_fn() if now is None else float(now)
		if not force and now - self._last_save < SAVE_INTERVAL:
			return False

		directory = os.path.dirname(self.path)
		temporary_path = self.path + ".tmp"
		try:
			if directory and not os.path.isdir(directory):
				os.makedirs(directory, exist_ok=True)
			payload = {
				"version": VERSION,
				"character": self.character_name,
				"profiles": self.profiles,
				"enabled": self.profile_enabled,
				"active_profile": self.active_profile,
				"auto_enabled": self.auto_enabled,
				"window_position": self.window_position,
				"next_due": {
					str(vnum): due_at
					for vnum, due_at in self.next_due.items()
				},
			}
			body = json.dumps(
				payload, ensure_ascii=False, separators=(",", ":")
			).encode("utf-8")
			with _REAL_OPEN(temporary_path, "wb") as handle:
				handle.write(body)
				handle.flush()
				os.fsync(handle.fileno())
			os.replace(temporary_path, self.path)
			self.needs_migration = False
			self._dirty = False
			self._last_save = now
			return True
		except (OSError, TypeError, ValueError, OverflowError):
			try:
				os.unlink(temporary_path)
			except OSError:
				pass
			return False
