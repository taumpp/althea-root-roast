"""Maximum of a rolled item attribute per item family (tooltip "max bonus").

The server rolls the first five attributes from a different pool per item
family. Every maximum comes from the server's bonus catalog
(bonuscatalog.py, ALTHEA-647): the item_attr row values and the highest level
each attribute set rolls, the weapon addon caps, the belt, talisman heart,
Item Shop costume, mount speed and mount core pools, and the item family of
each prototype. A value is highlighted only when it equals the maximum of its
own family. Without a catalog (older server, reply pending) nothing is
highlighted; there is no built-in fallback table.

Dragon soul stones have none: their values follow grade/step/strength.
"""

import bonuscatalog
import mountcorebonus

FAMILY_NORMAL = "normal"            # attribute set of the prototype (or none)
FAMILY_BELT = "belt"
FAMILY_TALISMAN_HEART = "talisman_heart"
FAMILY_IS_COSTUME = "is_costume"
FAMILY_COSTUME_MOUNT = "costume_mount"
FAMILY_DRAGON_SOUL = "dragon_soul"

_MISSING = object()


def _Constant(itemModule, name):
	return getattr(itemModule, name, _MISSING)


def GetFamily(itemModule, itemType, subType, value5=0, vnum=0):
	"""(family, detail) of a prototype; detail is its attribute set or Value5.

	itemModule is the native item module (or a stand-in exposing its type
	constants). Unknown constants never match.
	"""
	if itemType == _Constant(itemModule, "ITEM_TYPE_DS"):
		return (FAMILY_DRAGON_SOUL, None)
	catalog = bonuscatalog.Current()
	kind = catalog.KindFor(vnum, itemType, subType) if catalog else None
	if kind == "belt" or itemType == _Constant(itemModule, "ITEM_TYPE_BELT"):
		return (FAMILY_BELT, None)
	if kind == "talisman_heart":
		return (FAMILY_TALISMAN_HEART, None)
	if kind == "mount_speed":
		return (FAMILY_COSTUME_MOUNT, None)
	if catalog and itemType == _Constant(itemModule, "ITEM_TYPE_COSTUME") and value5 in catalog.costumePools:
		return (FAMILY_IS_COSTUME, value5)
	return (FAMILY_NORMAL, catalog.SetFor(itemType, subType) if catalog else None)


def GetSelectedFamily(vnum=0):
	"""Family of the prototype currently selected in the native item module."""
	import item

	itemType = item.GetItemType()
	subType = item.GetItemSubType()
	value5 = 0
	if itemType == _Constant(item, "ITEM_TYPE_COSTUME"):
		value5 = item.GetValue(5)
	return GetFamily(item, itemType, subType, value5, vnum)


def _NormalMaximum(catalog, setIndex, affectType):
	if setIndex is None:
		# No attribute set (sashes absorbing equipment, legacy items): the
		# largest value any non-glove set rolls, as before the catalog.
		glove = catalog.GloveSet()
		values = [catalog.SetMaximum(index, affectType) for index in catalog.sets if index != glove]
		values = [value for value in values if value is not None]
		maximum = max(values) if values else None
	else:
		maximum = catalog.SetMaximum(setIndex, affectType)
	# Weapon addon bonuses roll up to the addon cap on every non-glove item.
	addon = catalog.AddonMaximum(affectType)
	if addon is not None and setIndex != catalog.GloveSet():
		return addon
	return maximum


def GetMaximum(family, affectType):
	"""Server maximum of affectType on the family, or None when it has none."""
	catalog = bonuscatalog.Current()
	if not catalog:
		return None
	affectType = int(affectType)
	if mountcorebonus.IsScopedApply(affectType):
		return None
	name, detail = family
	if name == FAMILY_DRAGON_SOUL:
		return None
	if name == FAMILY_BELT:
		entry = catalog.belt.get(affectType)
		return entry[0] if entry else None
	if name == FAMILY_TALISMAN_HEART:
		return catalog.heartMaximum if affectType in catalog.heartApplies else None
	if name == FAMILY_COSTUME_MOUNT:
		return catalog.mountSpeedMaximum if affectType == catalog.mountSpeedApply else None
	if name == FAMILY_IS_COSTUME:
		return catalog.costumePools[detail][2].get(affectType)
	return _NormalMaximum(catalog, detail, affectType)


def IsMaximum(family, affectType, value):
	try:
		affectType = int(affectType)
		value = int(value)
	except (TypeError, ValueError):
		return False
	if value <= 0:
		return False
	if mountcorebonus.IsScopedApply(affectType):
		return mountcorebonus.IsMaximum(affectType, value)
	return GetMaximum(family, affectType) == value
