MODIFIER_ORDER = ("CTRL", "SHIFT", "ALT")
MODIFIER_TOKENS = frozenset(MODIFIER_ORDER)
VALID_BASE_KEYS = frozenset(
	tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
	+ tuple(str(value) for value in range(10))
	+ tuple("F%d" % value for value in range(1, 13))
	+ tuple("NUMPAD%d" % value for value in range(10))
	+ (
		"UP", "DOWN", "LEFT", "RIGHT", "HOME", "END", "PGUP", "PGDN",
		"INSERT", "DELETE", "MINUS", "EQUALS", "LBRACKET", "RBRACKET",
		"SEMICOLON", "APOSTROPHE", "GRAVE", "BACKSLASH", "COMMA",
		"PERIOD", "SLASH", "SPACE", "ENTER", "ESC", "SYSRQ", "TAB",
		"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "DECIMAL", "NUMPADENTER",
		"MOUSE4", "MOUSE5",
	)
)


class Shortcut(object):
	__slots__ = ("key", "modifiers")

	def __init__(self, key, modifiers=()):
		normalized_key = str(key).strip().upper()
		normalized_values = tuple(
			str(value).strip().upper() for value in modifiers
		)
		normalized_modifiers = frozenset(normalized_values)

		if not normalized_key or normalized_key in MODIFIER_TOKENS:
			raise ValueError("shortcut needs a base key")
		if normalized_key not in VALID_BASE_KEYS:
			raise ValueError("unknown base key")
		if len(normalized_values) != len(normalized_modifiers):
			raise ValueError("duplicate modifier")
		if not normalized_modifiers.issubset(MODIFIER_TOKENS):
			raise ValueError("unknown modifier")

		self.key = normalized_key
		self.modifiers = tuple(
			value for value in MODIFIER_ORDER if value in normalized_modifiers
		)

	@classmethod
	def parse(cls, text):
		normalized = str(text).strip()
		if not normalized:
			return None

		parts = [part.strip() for part in normalized.split("+")]
		if any(not part for part in parts):
			raise ValueError("malformed shortcut")
		return cls(parts[-1], parts[:-1])

	def serialize(self):
		return "+".join(self.modifiers + (self.key,))

	def display(self):
		labels = {"CTRL": "Ctrl", "SHIFT": "Shift", "ALT": "Alt"}
		key_label = {"MOUSE4": "Mouse4", "MOUSE5": "Mouse5"}.get(self.key, self.key)
		return "+".join(
			tuple(labels[value] for value in self.modifiers) + (key_label,)
		)

	def __eq__(self, other):
		return (
			isinstance(other, Shortcut)
			and self.key == other.key
			and self.modifiers == other.modifiers
		)

	def __hash__(self):
		return hash((self.key, self.modifiers))

	def __repr__(self):
		return "Shortcut(%r)" % self.serialize()


class AssignmentConflict(object):
	def __init__(self, action_id):
		self.action_id = action_id


class ReservedShortcutError(ValueError):
	def __init__(self, owner_id):
		ValueError.__init__(self, owner_id)
		self.owner_id = owner_id


class BindingState(object):
	def __init__(self, defaults, reserved):
		self._defaults = dict(defaults)
		self._reserved = dict(reserved)
		self._bindings = dict(defaults)

	def clone(self):
		result = BindingState(self._defaults, self._reserved)
		result._bindings = dict(self._bindings)
		return result

	def get(self, action_id):
		return self._bindings[action_id]

	def as_dict(self):
		return dict(self._bindings)

	def owner_of(self, shortcut):
		for action_id, assigned in self._bindings.items():
			if assigned == shortcut:
				return action_id
		return None

	def assign(self, action_id, shortcut, replace=False):
		if action_id not in self._bindings:
			raise KeyError(action_id)
		if shortcut is None:
			self.unbind(action_id)
			return None
		if shortcut in self._reserved:
			raise ReservedShortcutError(self._reserved[shortcut])

		owner = self.owner_of(shortcut)
		if owner is not None and owner != action_id:
			if not replace:
				return AssignmentConflict(owner)
			self._bindings[owner] = None

		self._bindings[action_id] = shortcut
		return None

	def unbind(self, action_id):
		if action_id not in self._bindings:
			raise KeyError(action_id)
		self._bindings[action_id] = None

	def reset_defaults(self):
		self._bindings = dict(self._defaults)

	def replace_all(self, bindings):
		if set(bindings) != set(self._defaults):
			raise ValueError("binding IDs do not match registry")

		candidate = BindingState(self._defaults, self._reserved)
		for action_id in bindings:
			candidate.unbind(action_id)
		for action_id, shortcut in bindings.items():
			if shortcut is not None:
				conflict = candidate.assign(action_id, shortcut)
				if conflict is not None:
					raise ValueError("duplicate shortcut")
		self._bindings = candidate.as_dict()
