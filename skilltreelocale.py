# -*- coding: utf-8 -*-

import skilltreecatalog
from skilltreetexts import NODE_TEXT_BY_LANGUAGE, NODE_VALUE_FORMAT_BY_ID

EXPECTED_NODE_IDS = frozenset(skilltreecatalog.NODE_IDS)
ERROR_TEXT_BY_LANGUAGE = {
	u'cz': u"Strom dovednost\u00ed se nepoda\u0159ilo bezpe\u010dn\u011b na\u010d\u00edst. Vylep\u0161ov\u00e1n\u00ed je do\u010dasn\u011b vypnut\u00e9.",
	u'en': u"The skill tree could not be loaded safely. Upgrades are temporarily disabled.",
}
GATE_TEXT_BY_LANGUAGE = {
	u'cz': u'Od \u00farovn\u011b %d',
	u'en': u'From level %d',
}
POINT_COST_TEXT_BY_LANGUAGE = {
	u'cz': u'%s bod\u016f',
	u'en': u'%s points',
}
UPGRADE_ACTION_TEXT_BY_LANGUAGE = {
	u'cz': (u'Vylep\u0161it', u'Zru\u0161it'),
	u'en': (u'Upgrade', u'Cancel'),
}
DISMANTLE_TEXT_BY_LANGUAGE = {
	u'cz': {'title': u'Rozklad', 'info_title': u'Hodnoty rozkladu',
		'action': u'Rozlo\u017eit', 'open': u'Rozklad',
		'info_items': u'P\u0158IJ\u00cdMAN\u00c9 P\u0158EDM\u011aTY', 'info_points': u'BODY',
		'info_footer': u'%d\u2013%d z %d  \u00b7  posu\u0148 seznam',
		'summary': u'Z\u00edsk\u00e1\u0161 %s bod\u016f',
		'rejected_short': u'Rozklad odm\u00edtnut',
		'pending_short': u'Zpracov\u00e1v\u00e1m rozklad...',
		'unavailable_short': u'Zat\u00edm nelze rozlo\u017eit'},
	u'en': {'title': u'Dismantle', 'info_title': u'Dismantle values',
		'action': u'Dismantle', 'open': u'Dismantle',
		'info_items': u'ACCEPTED ITEMS', 'info_points': u'POINTS',
		'info_footer': u'%d\u2013%d of %d  \u00b7  scroll list',
		'summary': u'Gain %s points',
		'rejected_short': u'Dismantle rejected',
		'pending_short': u'Dismantling...',
		'unavailable_short': u'Cannot dismantle yet'},
}

try:
	_INTEGER_TYPES = (int, long)
except NameError:
	_INTEGER_TYPES = (int,)


def GetNodeText(language, nodeId):
	texts = NODE_TEXT_BY_LANGUAGE.get(language)
	if texts is None:
		return None
	return texts.get(nodeId)


def GetErrorText(language):
	return ERROR_TEXT_BY_LANGUAGE.get(language, ERROR_TEXT_BY_LANGUAGE[u'en'])


def GetGateText(language, level):
	return GATE_TEXT_BY_LANGUAGE.get(language, GATE_TEXT_BY_LANGUAGE[u'en']) % level


def GetPointCostText(language, points):
	amount = FormatPointAmount(points)
	return POINT_COST_TEXT_BY_LANGUAGE.get(language, POINT_COST_TEXT_BY_LANGUAGE[u'en']) % amount


def FormatPointAmount(points):
	return format(points, ',d').replace(',', ' ')


def GetUpgradeActionText(language):
	return UPGRADE_ACTION_TEXT_BY_LANGUAGE.get(language, UPGRADE_ACTION_TEXT_BY_LANGUAGE[u'en'])


def GetDismantleText(key, language=u'cz'):
	return DISMANTLE_TEXT_BY_LANGUAGE.get(language, DISMANTLE_TEXT_BY_LANGUAGE[u'en'])[key]


def HasCompleteLocale(language, nodeIds):
	texts = NODE_TEXT_BY_LANGUAGE.get(language)
	if texts is None:
		return False
	try:
		nodeIds = tuple(nodeIds)
	except TypeError:
		return False
	return len(nodeIds) == len(EXPECTED_NODE_IDS) and frozenset(nodeIds) == EXPECTED_NODE_IDS and frozenset(texts) == EXPECTED_NODE_IDS


def FormatNodeValue(nodeId, value):
	if isinstance(value, bool) or not isinstance(value, _INTEGER_TYPES):
		return None
	valueFormat = NODE_VALUE_FORMAT_BY_ID.get(nodeId)
	if valueFormat is None:
		return None
	formatted = u'%+d' % value
	if valueFormat == 'percent':
		return formatted + u' %'
	if valueFormat == 'distance':
		return formatted + u' m'
	return formatted
