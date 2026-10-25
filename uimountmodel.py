GEAR_NAMES = (
	u"Sedlo",
	u"Podkovy",
	u"Uzda",
	u"Zbroj mounta",
	u"Prizmatické jádro",
)
GEAR_UNLOCK_LEVELS = (5, 10, 15, 20, 25)
GEAR_BONUSES = (
	(u"Silný proti meteorům +10%",),
	(u"Silný proti bossům +10%",),
	(u"Obrana +100",),
	(u"Hodnota útoku +100",),
	(u"Síla všech živlů +10%", u"Útok zbraní +5%", u"Silný proti příšerám +10%"),
)
ELEMENT_NAMES = (
	u"Oheň",
	u"Led",
	u"Blesk",
	u"Vítr",
	u"Země",
	u"Temnota",
)
ELEMENT_ASSETS = (
	"element_fire_24.png",
	"element_ice_24.png",
	"element_lightning_24.png",
	"element_wind_24.png",
	"element_earth_24.png",
	"element_dark_24.png",
)
ELEMENT_STATES = {
	0: "normal",
	1: "active",
	2: "completed",
	3: "locked",
}
ELEMENT_CARRIER_STATES = {
	"normal": "normal",
	"active": "normal",
	"completed": "completed",
	"locked": "locked",
}
PRISMATIC_STATES = {
	0: ("locked", u"Odemkne se na úrovni Duše 25"),
	1: ("ready", u"Recept odemčen u Pacholka"),
	2: ("crafted", u"Prizmatické jádro v inventáři"),
}


def _group_integer(value):
	return format(int(value), ",d").replace(",", " ")


def _require_int(value, name, minimum=0):
	try:
		result = int(value)
	except (TypeError, ValueError):
		raise ValueError("invalid %s" % name)
	if result < minimum:
		raise ValueError("invalid %s" % name)
	return result


class MountSystemViewModel(object):
	"""Atomic, UI-only normalization of an authoritative server snapshot."""

	def __init__(self, core_unlock_text=None):
		self.core_unlock_text = core_unlock_text
		self.clear()

	def clear(self):
		self.revision = -1
		self.session_nonce = 0
		self.flags = 0
		self.skin_vnum = 0
		self.mount_race = None
		self.mount_empty_text = u"Není nasazen žádný mount"
		self.forge_available = False
		self.bonuses = ()
		self.gear = ()
		self.elements = ()
		self.soul = self._build_soul(0, 0, 0)
		self.soul_level_up = 0
		self.prismatic = self._build_prismatic(0)
		self.open_element_id = None

	def apply_snapshot(self, snapshot):
		"""Validate first, then replace every server-owned visible value."""
		if not isinstance(snapshot, dict):
			raise ValueError("snapshot must be a dictionary")
		revision = _require_int(snapshot.get("revision"), "revision")
		if revision < self.revision:
			return False

		nonce = _require_int(snapshot.get("session_nonce"), "session_nonce", 1)
		flags = _require_int(snapshot.get("flags", 0), "flags")
		skin_vnum = _require_int(snapshot.get("skin_vnum", 0), "skin_vnum")
		mount_race_value = _require_int(snapshot.get("mount_race", 0), "mount_race")
		soul = self._build_soul(
			snapshot.get("soul_level", 0),
			snapshot.get("soul_exp", 0),
			snapshot.get("next_soul_exp", 0),
		)
		gear = self._build_gear(
			snapshot.get("gear"),
			snapshot.get("next_unlock_subtype", 255),
			snapshot.get("next_unlock_level", 0),
		)
		elements = self._build_elements(
			snapshot.get("elements"), snapshot.get("tasks")
		)
		prismatic = self._build_prismatic(
			snapshot.get("prismatic_state", 0)
		)
		bonuses = self._build_bonuses(snapshot.get("bonuses", ()))

		# owner 21. 10. 2026: a soul level-up empties the bar and the fed EXP looked lost; the new level of the same
		# mount in the same session (not the first snapshot, a relog or another mount) for the window to announce
		same = self.revision >= 0 and nonce == self.session_nonce and (mount_race_value or None) == self.mount_race
		self.soul_level_up = soul["level"] if same and soul["level"] > self.soul["level"] else 0
		self.revision = revision
		self.session_nonce = nonce
		self.flags = flags
		self.skin_vnum = skin_vnum
		self.mount_race = mount_race_value or None
		self.forge_available = bool(snapshot.get("forge_available", False))
		self.soul = soul
		self.gear = gear
		self.elements = elements
		self.prismatic = prismatic
		self.bonuses = bonuses
		valid_ids = set(row["element_id"] for row in elements)
		if self.open_element_id not in valid_ids:
			self.open_element_id = None
		self._apply_open_state()
		return True

	def open_element(self, element_id):
		element_id = _require_int(element_id, "element_id")
		if element_id not in set(row["element_id"] for row in self.elements):
			return False
		self.open_element_id = (
			None if self.open_element_id == element_id else element_id
		)
		self._apply_open_state()
		return True

	def mark_prismatic_opened(self):
		if self.prismatic["state"] not in ("ready", "opened"):
			return False
		self.prismatic = {
			"state": "opened",
			"text": u"Otevřena nabídka Pacholka",
		}
		return True

	def set_prismatic_equipped(self, equipped):
		if self.prismatic["state"] != "crafted":
			return False
		self.prismatic = dict(self.prismatic)
		self.prismatic["text"] = (
			u"Prizmatické jádro nasazeno"
			if equipped else u"Prizmatické jádro v inventáři"
		)
		return True

	def _build_soul(self, level, current, target):
		level = _require_int(level, "soul_level")
		current = _require_int(current, "soul_exp")
		target = _require_int(target, "next_soul_exp")
		if target and current > target:
			current = target
		percent = min(100, (current * 100 // target) if target else 0)
		filled = min(4, ((current * 4 + target - 1) // target) if target and current else 0)
		segment_fill = tuple(
			max(0.0, min(1.0, float(current * 4 - index * target) / float(target)))
			for index in range(4)
		) if target else (0.0, 0.0, 0.0, 0.0)
		maximum = level >= 25
		if maximum:
			percent, filled, segment_fill = 100, 4, (1.0,) * 4
		return {
			"maximum": maximum,
			"speed_bonus_percent": min(level, 25) * 2,
			"level": level,
			"current_exp": current,
			"next_exp": target,
			"percent": percent,
			"segments": tuple(index < filled for index in range(4)),
			"segment_fill": segment_fill,
			"exp_text": u"Maximální úroveň" if maximum else u"%s / %s EXP" % (
				_group_integer(current), _group_integer(target)
			),
		}

	def _build_gear(self, rows, next_subtype, next_level):
		if not isinstance(rows, (list, tuple)) or len(rows) != 5:
			raise ValueError("gear must contain exactly five rows")
		next_subtype = _require_int(next_subtype, "next_unlock_subtype")
		next_level = _require_int(next_level, "next_unlock_level")
		result = [None] * 5
		for raw in rows:
			if not isinstance(raw, (list, tuple)) or len(raw) != 5:
				raise ValueError("invalid gear row")
			subtype, wear_cell, item_vnum, item_id, locked = raw
			subtype = _require_int(subtype, "gear subtype")
			wear_cell = _require_int(wear_cell, "gear wear cell")
			item_vnum = _require_int(item_vnum, "gear item vnum")
			item_id = _require_int(item_id, "gear item id")
			if subtype >= 5 or result[subtype] is not None or wear_cell != 46 + subtype:
				raise ValueError("invalid or duplicate gear subtype")
			is_locked = bool(locked)
			if is_locked:
				level = GEAR_UNLOCK_LEVELS[subtype]
				if next_subtype == subtype and next_level:
					level = next_level
				unlock_text = u"Odemkne se na úrovni Duše %d" % level
				if subtype == 4 and self.core_unlock_text:
					unlock_text = self.core_unlock_text
			else:
				unlock_text = u"Odemčeno"
			result[subtype] = {
				"subtype": subtype,
				"name": GEAR_NAMES[subtype],
				"wear_cell": wear_cell,
				"item_vnum": item_vnum,
				"item_id": item_id,
				"empty": item_vnum == 0,
				"locked": is_locked,
				"icon": item_vnum or None,
				"unlock_text": unlock_text,
			}
		if any(row is None for row in result):
			raise ValueError("missing gear subtype")
		return tuple(result)

	def _build_elements(self, rows, tasks):
		if not isinstance(rows, (list, tuple)) or len(rows) != 6:
			raise ValueError("elements must contain exactly six rows")
		if not isinstance(tasks, (list, tuple)) or len(tasks) > 64:
			raise ValueError("tasks must contain zero to sixty-four rows")
		by_element = dict((index, []) for index in range(6))
		task_ids = set()
		for raw in tasks:
			if not isinstance(raw, (list, tuple)) or len(raw) != 8:
				raise ValueError("invalid task row")
			element_id, task_id, event_kind, target_vnum, progress, target, reward, complete = raw
			element_id = _require_int(element_id, "task element id")
			task_id = _require_int(task_id, "task id", 1)
			event_kind = _require_int(event_kind, "event kind", 1)
			target_vnum = _require_int(target_vnum, "task target vnum")
			progress = _require_int(progress, "task progress")
			target = _require_int(target, "task target", 1)
			reward = _require_int(reward, "task reward", 1)
			key = (element_id, task_id)
			if element_id >= 6 or event_kind > 3 or key in task_ids or progress > target:
				raise ValueError("invalid or duplicate task")
			task_ids.add(key)
			is_complete = bool(complete)
			by_element[element_id].append({
				"element_id": element_id,
				"task_id": task_id,
				"event_kind": event_kind,
				"target_vnum": target_vnum,
				"progress": progress,
				"target": target,
				"progress_text": u"%s / %s" % (
					_group_integer(progress), _group_integer(target)
				),
				"reward_basis_points": reward,
				"reward_text": u"+%g %%" % (reward / 100.0),
				"complete": is_complete,
				})

		result = [None] * 6
		for raw in rows:
			if not isinstance(raw, (list, tuple)) or len(raw) != 3:
				raise ValueError("invalid element row")
			element_id, bonus, state_value = raw
			element_id = _require_int(element_id, "element id")
			bonus = _require_int(bonus, "element bonus")
			state_value = _require_int(state_value, "element state")
			if element_id >= 6 or result[element_id] is not None or bonus > 2000 or state_value not in ELEMENT_STATES:
				raise ValueError("invalid or duplicate element")
			state = ELEMENT_STATES[state_value]
			result[element_id] = {
				"element_id": element_id,
				"name": ELEMENT_NAMES[element_id],
				"icon": ELEMENT_ASSETS[element_id],
				"bonus_basis_points": bonus,
				"bonus_text": u"+%g / 20 %%" % (bonus / 100.0),
				"state": state,
				"carrier": "element_parent_350x34_%s.png" % (
					ELEMENT_CARRIER_STATES[state]
				),
				"tasks": tuple(by_element[element_id]),
				"opened": False,
			}
		if any(row is None for row in result):
			raise ValueError("missing element")
		return tuple(result)

	def _build_prismatic(self, state_value):
		state_value = _require_int(state_value, "prismatic state")
		if state_value not in PRISMATIC_STATES:
			raise ValueError("invalid prismatic state")
		state, text = PRISMATIC_STATES[state_value]
		return {
			"state": state,
			"text": text,
		}

	def _build_bonuses(self, rows):
		if not isinstance(rows, (list, tuple)) or len(rows) > 16:
			raise ValueError("bonuses must contain zero to sixteen rows")
		result = []
		seen = set()
		for raw in rows:
			if not isinstance(raw, (list, tuple)) or len(raw) != 2:
				raise ValueError("invalid bonus row")
			apply_type = _require_int(raw[0], "bonus apply type", 1)
			value = int(raw[1])
			if apply_type in seen or value == 0:
				raise ValueError("invalid or duplicate bonus")
			seen.add(apply_type)
			result.append({"apply_type": apply_type, "value": value})
		return tuple(result)

	def _apply_open_state(self):
		result = []
		for row in self.elements:
			copy = dict(row)
			copy["opened"] = row["element_id"] == self.open_element_id
			copy["carrier"] = "element_parent_350x34_%s.png" % (
				ELEMENT_CARRIER_STATES[row["state"]]
			)
			if copy["opened"] and row["state"] not in ("completed", "locked"):
				copy["carrier"] = "element_parent_350x34_opened.png"
			result.append(copy)
		self.elements = tuple(result)
