"""What the server lets this session's panel show: the names, grouping and
inputs of the actions in its capability mask.

The rows are sent as server commands ahead of the capability result. They are
untrusted input: every row is bounded and checked, and a set replaces the
current catalogue only when all of it was valid. An action the catalogue does
not describe is still offered, by number and with every input, because the
server alone decides what a request does.
"""

SEPARATOR = "|"
MAX_ROW_LENGTH = 255
MAX_ROWS = 512
MAX_ACTION = 63
# The left panel holds two rows of three tabs, one of them for actions
# without a description.
MAX_CATEGORIES = 5
MAX_ROLES = 16
MAX_LEVEL = 255
MAX_LABEL = 48
MAX_TEXT = 160

FIELD_NAMES = {
	"t": "target",
	"a": "argument",
	"v": "value",
	"s": "secondary",
	"r": "reason",
	"m": "map",
}
FIELD_ORDER = "tavsrm"
FIELD_LETTERS = dict((name, letter) for letter, name in FIELD_NAMES.items())
PICKERS = ("item", "mob")
NONE = "-"

CONFIRM_NONE = 0
CONFIRM_ASK = 1
# The confirmed request carries 1 as its secondary value.
CONFIRM_ASK_AND_MARK = 2

# Category of the actions the catalogue does not describe.
PLAIN_CATEGORY = 0
PLAIN_CATEGORY_LABEL = "-"
PLAIN_FIELDS = ("target", "argument", "value", "secondary", "reason")

# Parts of a row after its kind.
ROW_PARTS = {
	"begin": 0,
	"total": 1,
	"role": 2,
	"category": 2,
	"label": 2,
	"action": 6,
	"field": 3,
	"about": 2,
	"end": 0,
}


def _Number(text, minimum, maximum):
	"""A plain decimal within bounds, or None."""
	if not 1 <= len(text) <= 3 or text.strip("0123456789"):
		return None
	value = int(text)
	if value < minimum or value > maximum:
		return None
	return value


def _Text(text, maximum):
	"""A text sent with '_' for a space, or None when it cannot be shown."""
	text = text.replace("_", " ")
	if not 1 <= len(text) <= maximum or not text.strip():
		return None
	for character in text:
		if ord(character) < 32 or ord(character) == 127:
			return None
	return text


def _PlainInfo(action):
	return {
		"label": "#%d" % action,
		"category": PLAIN_CATEGORY,
		"fields": PLAIN_FIELDS,
		"labels": dict((name, name) for name in PLAIN_FIELDS),
		"reason": False,
		"confirm": True,
		"mark": False,
		"picker": None,
		"description": "",
		"plain": True,
	}


class Catalog(object):
	"""A complete catalogue, or the empty one every session starts with."""

	def __init__(self):
		self.total = 0
		self.roles = {}
		self.categories = []
		self.categoryLabels = {}
		self.fieldLabels = {}
		self.order = []
		self.actions = {}

	def IsEmpty(self):
		return not self.total

	def Actions(self, mask):
		"""The actions of a capability mask in the order they are listed:
		described ones as the server ordered them, then the others by number."""
		listed = [action for action in self.order if mask & (1 << action)]
		for action in range(1, MAX_ACTION + 1):
			if mask & (1 << action) and action not in self.actions:
				listed.append(action)
		return listed

	def Info(self, action):
		info = self.actions.get(action)
		if info is None:
			info = _PlainInfo(action)
		return info

	def Categories(self, mask):
		"""The categories with at least one action of the mask, in tab order."""
		used = set(self.Info(action)["category"] for action in self.Actions(mask))
		listed = [category for category in self.categories if category in used]
		if PLAIN_CATEGORY in used:
			listed.append(PLAIN_CATEGORY)
		return listed

	def CategoryLabel(self, category):
		return self.categoryLabels.get(category, PLAIN_CATEGORY_LABEL)

	def RoleName(self, level):
		return self.roles.get(level, "Role %d" % level)

	def Total(self, mask):
		"""How many actions exist, as far as this session was told."""
		return max(self.total, len(self.Actions(mask)))


class _Draft(object):
	"""The rows between begin and end; None from a row means the set is void."""

	def __init__(self):
		self.catalog = Catalog()
		self.rowCount = 0
		self.described = set()

	def Row(self, kind, parts):
		self.rowCount += 1
		if self.rowCount > MAX_ROWS:
			return None
		return getattr(self, "_" + kind)(*parts)

	def _total(self, total):
		total = _Number(total, 1, MAX_ACTION)
		if total is None or self.catalog.total:
			return None
		self.catalog.total = total
		return True

	def _role(self, level, label):
		level = _Number(level, 0, MAX_LEVEL)
		label = _Text(label, MAX_LABEL)
		roles = self.catalog.roles
		if level is None or label is None or level in roles or len(roles) >= MAX_ROLES:
			return None
		roles[level] = label
		return True

	def _category(self, category, label):
		category = _Number(category, 1, MAX_LEVEL)
		label = _Text(label, MAX_LABEL)
		catalog = self.catalog
		if (category is None or label is None or category in catalog.categoryLabels
			or len(catalog.categories) >= MAX_CATEGORIES):
			return None
		catalog.categories.append(category)
		catalog.categoryLabels[category] = label
		return True

	def _label(self, field, label):
		label = _Text(label, MAX_LABEL)
		labels = self.catalog.fieldLabels
		if field not in FIELD_NAMES or label is None or field in labels:
			return None
		labels[field] = label
		return True

	def _action(self, action, category, confirm, fields, picker, label):
		action = _Number(action, 1, MAX_ACTION)
		category = _Number(category, 1, MAX_LEVEL)
		confirm = _Number(confirm, CONFIRM_NONE, CONFIRM_ASK_AND_MARK)
		label = _Text(label, MAX_LABEL)
		catalog = self.catalog
		if None in (action, category, confirm, label):
			return None
		if action in catalog.actions or category not in catalog.categoryLabels:
			return None
		if fields == NONE:
			fields = ""
		elif not fields or len(fields) > len(FIELD_ORDER):
			return None
		if len(set(fields)) != len(fields) or not set(fields) <= set(FIELD_ORDER):
			return None
		# The map picker and a search both fill the value.
		if "m" in fields and ("v" in fields or picker != NONE):
			return None
		if picker != NONE and (picker not in PICKERS or "v" not in fields):
			return None
		names = tuple(FIELD_NAMES[field] for field in fields)
		catalog.order.append(action)
		catalog.actions[action] = {
			"label": label,
			"category": category,
			"fields": names,
			"labels": {},
			"reason": "reason" in names,
			"confirm": confirm != CONFIRM_NONE,
			"mark": confirm == CONFIRM_ASK_AND_MARK,
			"picker": picker if picker != NONE else None,
			"description": "",
			"plain": False,
		}
		return True

	def _field(self, action, field, label):
		info = self.catalog.actions.get(_Number(action, 1, MAX_ACTION))
		label = _Text(label, MAX_LABEL)
		name = FIELD_NAMES.get(field)
		if info is None or label is None or name not in info["fields"] or name in info["labels"]:
			return None
		info["labels"][name] = label
		return True

	def _about(self, action, text):
		action = _Number(action, 1, MAX_ACTION)
		text = _Text(text, MAX_TEXT)
		if action not in self.catalog.actions or text is None or action in self.described:
			return None
		self.described.add(action)
		self.catalog.actions[action]["description"] = text
		return True

	def Finish(self):
		"""The catalogue when the set is consistent, else None."""
		catalog = self.catalog
		if not catalog.total or len(catalog.actions) > catalog.total:
			return None
		for info in catalog.actions.values():
			for name in info["fields"]:
				if name not in info["labels"]:
					info["labels"][name] = catalog.fieldLabels.get(FIELD_LETTERS[name], name)
		return catalog


class Collector(object):
	"""Takes the rows one by one and keeps the last complete catalogue."""

	def __init__(self):
		self.catalog = Catalog()
		self.draft = None

	def Row(self, row):
		"""True when this row completed a set and the catalogue was replaced."""
		try:
			if len(row) > MAX_ROW_LENGTH:
				raise ValueError
			parts = row.split(SEPARATOR)
			kind = parts.pop(0)
			if ROW_PARTS.get(kind) != len(parts):
				raise ValueError
		except Exception:
			self.draft = None
			return False

		if kind == "begin":
			self.draft = _Draft()
			return False
		draft = self.draft
		if draft is None:
			return False
		if kind == "end":
			self.draft = None
			catalog = draft.Finish()
			if catalog is None:
				return False
			self.catalog = catalog
			return True
		if draft.Row(kind, parts) is None:
			self.draft = None
		return False
