# -*- coding: utf-8 -*-

import skilltreecatalog
from skilltreetexts import NODE_TEXT_BY_LANGUAGE, NODE_VALUE_FORMAT_BY_ID

EXPECTED_NODE_IDS = frozenset(skilltreecatalog.NODE_IDS)
ERROR_TEXT_BY_LANGUAGE = {
	u'cz': u"Strom schopnost\u00ed se nepoda\u0159ilo na\u010d\u00edst. Vylep\u0161ov\u00e1n\u00ed je te\u010f vypnut\u00e9.",
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
YANG_COST_TEXT_BY_LANGUAGE = {
	u'cz': u'%s Yang',
	u'en': u'%s Yang',
}
UPGRADE_ACTION_TEXT_BY_LANGUAGE = {
	u'cz': (u'Vylep\u0161it', u'Zru\u0161it'),
	u'en': (u'Upgrade', u'Cancel'),
}
MAX_RANK_TEXT_BY_LANGUAGE = {
	u'cz': u'Max (%d/%d)',
	u'en': u'Max (%d/%d)',
}
CLOSE_TEXT_BY_LANGUAGE = {
	u'cz': u'Zav\u0159\u00edt',
	u'en': u'Close',
}
DISMANTLE_TEXT_BY_LANGUAGE = {
	u'cz': {'title': u'Rozklad', 'info_title': u'Hodnoty rozkladu',
		'action': u'Rozlo\u017eit', 'open': u'Rozklad',
		'info_items': u'P\u0158IJ\u00cdMAN\u00c9 P\u0158EDM\u011aTY', 'info_points': u'BODY',
		'info_footer': u'%d-%d z %d  |  posu\u0148 seznam',
		'info_range': u'%d-%d z %d',
		'summary': u'Z\u00edsk\u00e1\u0161 %s bod\u016f',
		'balance': u'Body: %s / %s',
		'capacity': u'M\u00edsto pro %s bod\u016f',
		'cap_exceeded': u'Zisk p\u0159ekra\u010duje bodov\u00fd limit',
		'rejected_short': u'Rozklad odm\u00edtnut',
		'pending_short': u'Prob\u00edh\u00e1 rozklad...',
		'unavailable_short': u'Zat\u00edm nelze rozlo\u017eit'},
	u'en': {'title': u'Dismantle', 'info_title': u'Dismantle values',
		'action': u'Dismantle', 'open': u'Dismantle',
		'info_items': u'ACCEPTED ITEMS', 'info_points': u'POINTS',
		'info_footer': u'%d\u2013%d of %d  \u00b7  scroll list',
		'info_range': u'%d\u2013%d of %d',
		'summary': u'Gain %s points',
		'balance': u'Points: %s / %s',
		'capacity': u'Room for %s points',
		'cap_exceeded': u'Gain exceeds the point limit',
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
	text = texts.get(nodeId)
	if text is None:
		return None
	# Ordinary attributes use the item/switchbot name; custom effects keep their title.
	kind = skilltreecatalog.APPLY_BY_ID.get(nodeId, 0)
	if kind and kind < 60000:
		try:
			import app
			import bonuslabels
			from uiToolTip import ItemToolTip, GET_AFFECT_STRING
			if app.GetLocalePath().split("/")[-1] == language and kind in ItemToolTip.AFFECT_DICT:
				label = bonuslabels.Describe(GET_AFFECT_STRING, kind)
				if label:
					name = label[0]
					if isinstance(name, bytes):
						name = name.decode('cp%d' % app.GetDefaultCodePage())
					return (name, text[1])
		except (ImportError, AttributeError, KeyError, TypeError, ValueError, LookupError):
			pass
	return text


def GetErrorText(language):
	return ERROR_TEXT_BY_LANGUAGE.get(language, ERROR_TEXT_BY_LANGUAGE[u'en'])


def GetGateText(language, level):
	return GATE_TEXT_BY_LANGUAGE.get(language, GATE_TEXT_BY_LANGUAGE[u'en']) % level


def GetPointCostText(language, points):
	amount = FormatPointAmount(points)
	return POINT_COST_TEXT_BY_LANGUAGE.get(language, POINT_COST_TEXT_BY_LANGUAGE[u'en']) % amount


def GetYangCostText(language, yang):
	amount = FormatPointAmount(yang)
	return YANG_COST_TEXT_BY_LANGUAGE.get(language, YANG_COST_TEXT_BY_LANGUAGE[u'en']) % amount


def FormatPointAmount(points):
	return format(points, ',d').replace(',', ' ')


def GetUpgradeActionText(language):
	return UPGRADE_ACTION_TEXT_BY_LANGUAGE.get(language, UPGRADE_ACTION_TEXT_BY_LANGUAGE[u'en'])


def GetMaxRankText(language, rank, maxRank):
	return MAX_RANK_TEXT_BY_LANGUAGE.get(language, MAX_RANK_TEXT_BY_LANGUAGE[u'en']) % (rank, maxRank)


def GetCloseText(language):
	return CLOSE_TEXT_BY_LANGUAGE.get(language, CLOSE_TEXT_BY_LANGUAGE[u'en'])


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
