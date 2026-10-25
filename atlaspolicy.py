"""Maps where the large map (atlas: M key, minimap atlas button, panel launcher) stays closed.

No large map in dungeons; the minimap stays. The rules live in
``locale/common/atlas_policy.txt``, which ``tools/build_server_catalogs.py`` generates from the
althea/server dungeon catalog (``base_map`` of every dungeon). A private instance (index base * factor + n)
follows its base map, so a dungeon instance and a guild village instance differ by their base.
Each rule names its locale_game key; this module holds no map index and no player text.
The executable lets Python read only ``locale/`` text and a short fixed list of root text files,
so the data lives under ``locale/common`` (a root ``.txt`` would be refused at run time).
"""
import json

DATA = "locale/common/atlas_policy.txt"
SCHEMA = "althea-atlas-policy-v1"

_policy = None


def Parse(catalog):
	"""(private map factor, {base map: locale_game key}) of the decoded data file."""
	if catalog.get("schema") != SCHEMA:
		raise ValueError("unsupported atlas policy")
	factor = int(catalog["private_map_factor"])
	if factor < 2:
		raise ValueError("invalid private map factor")
	messages = {}
	for rule in catalog["rules"]:
		message = str(rule["message"])
		for baseMap in rule["base_maps"]:
			messages[int(baseMap)] = message
	return factor, messages


def _Policy():
	global _policy
	if _policy is None:
		try:
			with open(DATA, "r") as stream:
				_policy = Parse(json.load(stream))
		except Exception as error:
			# Without the data every map keeps its large map.
			_policy = (0, {})
			try:
				import dbg
				dbg.TraceError("atlaspolicy: %s unusable (%s)" % (DATA, error))
			except Exception:
				pass
	return _policy


def BaseMap(mapIndex, factor):
	if factor and mapIndex >= factor:
		return mapIndex // factor
	return mapIndex


def BlockedMessage(mapIndex):
	"""locale_game key of the notice when the large map stays closed on ``mapIndex``, otherwise None."""
	try:
		mapIndex = int(mapIndex)
	except (TypeError, ValueError):
		return None
	if mapIndex <= 0:
		return None
	factor, messages = _Policy()
	return messages.get(BaseMap(mapIndex, factor))
