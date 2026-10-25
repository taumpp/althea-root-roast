"""Presentation-only countdown helpers; server snapshots never reach disk."""

import builtins
import hashlib
import json
import math
import os
import tempfile


DEFAULT_WIDTH = 222
DEFAULT_HEIGHT = 272
MIN_WIDTH = 222
MIN_HEIGHT = 216
ROW_HEIGHT = 36
LIST_TOP = 108
FOOTER_RESERVE = 24

SCREEN_MARGIN = 8
SETTINGS_VERSION = 1
MAX_SETTINGS_BYTES = 64 * 1024
MAX_GEOMETRY = 32768
MAX_SCROLL = 65535
_REAL_OPEN = getattr(builtins, "old_open", builtins.open)


def _whole_number(value, fallback=0):
	if type(value) is int:
		return value
	try:
		number = float(value)
		if math.isfinite(number):
			return int(math.floor(number))
	except (TypeError, ValueError, OverflowError):
		pass
	return fallback


def format_time(seconds):
	seconds = max(0, _whole_number(seconds))
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	if hours:
		return "%02d:%02d:%02d" % (hours, minutes, seconds)
	return "%02d:%02d" % (minutes, seconds)


BIO_TOP = 49
BAND_HEIGHT = 21


def dungeon_band_top(bio_rows):
	"""The Dungeony band sits under the Biolog rows (or in the Biolog band's place when Biolog is not tracked)."""
	bio_rows = max(0, _whole_number(bio_rows))
	return BIO_TOP + bio_rows * ROW_HEIGHT + 2 if bio_rows else BIO_TOP - BAND_HEIGHT


def dungeon_list_top(bio_rows):
	return dungeon_band_top(bio_rows) + BAND_HEIGHT


def biolog_row_count(height, bio_total, dungeon_total):
	"""Biolog rows that fit: one per tracked research, like the dungeon rows; with dungeons tracked, room for the
	Dungeony band and one dungeon row stays. At least one row while anything is tracked (it then shows "(+N)")."""
	bio_total = max(0, _whole_number(bio_total))
	if not bio_total:
		return 0
	reserve = BAND_HEIGHT + 2 + ROW_HEIGHT if _whole_number(dungeon_total) > 0 else 0
	available = (_whole_number(height) - BIO_TOP - FOOTER_RESERVE - reserve) // ROW_HEIGHT
	return max(1, min(bio_total, available))


def visible_count(height, total, list_top=LIST_TOP):
	available = (_whole_number(height) - _whole_number(list_top) - FOOTER_RESERVE) // ROW_HEIGHT
	return max(0, min(_whole_number(total), available))


def _clamp_axis(position, size, minimum, viewport):
	viewport = max(0, _whole_number(viewport))
	margin = min(SCREEN_MARGIN, max(0, (viewport - 1) // 2))
	available = max(0, viewport - 2 * margin)
	size = min(available, max(minimum, _whole_number(size, minimum)))
	position = min(max(margin, _whole_number(position, margin)), viewport - margin - size)
	return position, size


def clamp_geometry(x, y, width, height, screen_width, usable_height):
	x, width = _clamp_axis(x, width, MIN_WIDTH, screen_width)
	y, height = _clamp_axis(y, height, MIN_HEIGHT, usable_height)
	return x, y, width, height


def fit_text(text, width, measure):
	text = str(text)
	width = max(0, _whole_number(width))
	if not text or width <= 0:
		return ""
	if measure(text) <= width:
		return text
	ellipsis = "..."
	if measure(ellipsis) > width:
		return ""
	# Measure the entire candidate so proportional glyphs and kerning use the
	# same font metrics as the final native TextLine.
	for length in range(len(text) - 1, -1, -1):
		candidate = text[:length].rstrip() + ellipsis
		if measure(candidate) <= width:
			return candidate
	return ""


def watched_dungeons(catalog):
	if not isinstance(catalog, dict):
		return []
	rows = [
		(vnum, data) for vnum, data in catalog.items()
		if type(vnum) is int and isinstance(data, dict)
		and data.get("alarm") is True
	]
	return sorted(rows, key=lambda row: (_whole_number(row[1].get("listIndex")), row[0]))


def dungeon_status(data, now, player_level, known):
	if _whole_number(player_level) < _whole_number(data.get("minLevel")):
		return {"state": "locked", "remaining": 0, "progress": 0.0}
	if not known:
		return {"state": "unknown", "remaining": 0, "progress": 0.0}
	remaining = max(0, _whole_number(data.get("server_cooldown")) - _whole_number(now))
	if not remaining:
		return {"state": "ready", "remaining": 0, "progress": 1.0}
	interval = max(0, _whole_number(data.get("cooldown")))
	progress = max(0.0, min(1.0, 1.0 - float(remaining) / interval)) if interval else 0.0
	return {"state": "cooldown", "remaining": remaining, "progress": progress}


def default_settings():
	return {
		"version": SETTINGS_VERSION,
		"width": DEFAULT_WIDTH,
		"height": DEFAULT_HEIGHT,
		"x": None,
		"y": None,
		"visible": True,
		"collapsed": False,
		"locked": False,
		"scroll": 0,
	}


def normalize_settings(raw):
	settings = default_settings()
	if not isinstance(raw, dict):
		return settings
	version = raw.get("version")
	if type(version) is not int or version != SETTINGS_VERSION:
		return settings
	for key in ("visible", "collapsed", "locked"):
		if type(raw.get(key)) is bool:
			settings[key] = raw[key]
	for key, minimum, maximum in (
		("width", MIN_WIDTH, MAX_GEOMETRY),
		("height", MIN_HEIGHT, MAX_GEOMETRY),
		("x", -MAX_GEOMETRY, MAX_GEOMETRY),
		("y", -MAX_GEOMETRY, MAX_GEOMETRY),
		("scroll", 0, MAX_SCROLL),
	):
		value = raw.get(key)
		# In particular bool, float, NaN and numeric strings are not geometry.
		if type(value) is int:
			settings[key] = min(maximum, max(minimum, value))
	return settings


def _settings_path(character, base_path):
	if not isinstance(character, str) or not character:
		return None
	identity = hashlib.sha256(character.encode("utf-8")).hexdigest()
	return os.path.join(base_path, identity + ".json")


def load_settings(character, base_path="UserData/countdown_hud"):
	try:
		path = _settings_path(character, base_path)
		if not path:
			return default_settings()
		with _REAL_OPEN(path, "rb") as settings_file:
			raw = settings_file.read(MAX_SETTINGS_BYTES + 1)
		if len(raw) > MAX_SETTINGS_BYTES:
			return default_settings()
		return normalize_settings(json.loads(raw.decode("utf-8")))
	except (OSError, ValueError, TypeError, RecursionError):
		return default_settings()


def save_settings(character, settings, base_path="UserData/countdown_hud"):
	temporary_path = None
	try:
		path = _settings_path(character, base_path)
		if not path:
			return False
		data = json.dumps(normalize_settings(settings), sort_keys=True).encode("utf-8")
		os.makedirs(base_path, exist_ok=True)
		descriptor, temporary_path = tempfile.mkstemp(prefix=".countdown-", suffix=".tmp", dir=base_path)
		with os.fdopen(descriptor, "wb") as settings_file:
			settings_file.write(data)
			settings_file.flush()
			os.fsync(settings_file.fileno())
		os.replace(temporary_path, path)
		temporary_path = None
		return True
	except (OSError, ValueError, TypeError):
		return False
	finally:
		if temporary_path:
			try:
				os.unlink(temporary_path)
			except OSError:
				pass
