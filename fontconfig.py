ROLE_DENSE = "dense"
ROLE_BODY = "body"
ROLE_CONTROL = "control"
ROLE_SECTION = "section"
ROLE_WINDOW_TITLE = "window_title"
ROLE_LARGE_BOLD = "large_bold"

ROLE_NAMES = (
	ROLE_DENSE,
	ROLE_BODY,
	ROLE_CONTROL,
	ROLE_SECTION,
	ROLE_WINDOW_TITLE,
	ROLE_LARGE_BOLD,
)

FONT_PALETTES = (
	{
		ROLE_DENSE: "Tahoma:11",
		ROLE_BODY: "Tahoma:12",
		ROLE_CONTROL: "Tahoma:12b",
		ROLE_SECTION: "Tahoma:12b",
		ROLE_WINDOW_TITLE: "Tahoma:14",
		ROLE_LARGE_BOLD: "Tahoma:14b",
	},
	{
		ROLE_DENSE: "Tahoma:12",
		ROLE_BODY: "Tahoma:14",
		ROLE_CONTROL: "Tahoma:14b",
		ROLE_SECTION: "Tahoma:14b",
		ROLE_WINDOW_TITLE: "Tahoma:16",
		ROLE_LARGE_BOLD: "Tahoma:16b",
	},
)

FONT_LEVELS = tuple(palette[ROLE_BODY] for palette in FONT_PALETTES)
FONT_LARGE = "Tahoma:16"

_current_level = 0


def NormalizeFontLevel(level):
	try:
		level = int(level)
	except (TypeError, ValueError):
		return 0

	if level in (1, 3):
		return 1
	return 0


def ConfigureLevel(level):
	global _current_level
	_current_level = NormalizeFontLevel(level)
	return _current_level


def FontForRole(role, level=None):
	if role not in ROLE_NAMES:
		raise KeyError(role)
	if level is None:
		level = _current_level
	else:
		level = NormalizeFontLevel(level)
	return FONT_PALETTES[level][role]


def FontNameForLevel(level):
	return FontForRole(ROLE_BODY, level)
