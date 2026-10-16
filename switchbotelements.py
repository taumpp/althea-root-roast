# -*- coding: utf-8 -*-
# Random elemental resistances in the switchbot attribute picker (ALTHEA-591).
#
# Which applies form the elemental group and how many one item may carry come
# from the server bonus catalog (bonuscatalog.py, ALTHEA-647). The server sends
# only the elements the item's attribute set can roll. The item tooltip labels
# are inflected ("Odolnost proti ohni"), so the search also matches the
# nominative element names below; they are presentation only.
from marketfilters import folded
import bonuscatalog

# Czech nominative names by apply id, in the owner's design-table order
# (APPLY_RESIST_FIRE, _ELEC, _WIND, _ICE, _EARTH, _DARK).
ELEMENTS = (
	(35, u'oheň'),
	(36, u'blesk'),
	(38, u'vítr'),
	(87, u'led'),
	(88, u'země'),
	(89, u'temnota'),
)
ELEMENT_NAMES = dict(ELEMENTS)
ELEMENT_ORDER = dict((apply, index) for index, (apply, name) in enumerate(ELEMENTS))
GROUP_KEYWORDS = u'živel živly'


def IsElement(applyType):
	return bonuscatalog.IsElement(applyType)


def SearchKeywords(applyType):
	name = ELEMENT_NAMES.get(applyType)
	return u'%s %s' % (name, GROUP_KEYWORDS) if name else u''


def Matches(query, label, keywords=u''):
	needle = folded(query).strip()
	if not needle:
		return True
	return needle in folded(label) or (bool(keywords) and needle in folded(keywords))


def Allowance(catalogTypes):
	# The server's per-item limit, never more than the elements the slot offers
	# (owner decision 2026-09-29: an item may carry every element of its slot).
	offered = len(set(kind for kind in catalogTypes if IsElement(kind)))
	return min(offered, bonuscatalog.ElementLimit())


def Blocked(applyType, otherSelectedTypes, catalogTypes):
	if not IsElement(applyType):
		return False
	chosen = set(kind for kind in otherSelectedTypes if IsElement(kind))
	return len(chosen) >= Allowance(catalogTypes)


def Ordered(entries):
	# Keep the server order of ordinary bonuses and list the elements together
	# at the end, in design-table order, instead of scattered by apply id.
	ordinary = [entry for entry in entries if not IsElement(entry[0])]
	elements = sorted((entry for entry in entries if IsElement(entry[0])),
		key=lambda entry: ELEMENT_ORDER.get(entry[0], len(ELEMENT_ORDER) + entry[0]))
	return ordinary + elements
