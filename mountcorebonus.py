# -*- coding: utf-8 -*-
"""Scoped mount-core attributes. Deliberately separate from global character points.

The scoped apply range is the item/apply layout shared with the server
(APPLY_MOUNT_CORE_FIRST..LAST); the bonus values and their maxima come from the
server bonus catalog (bonuscatalog.py, ALTHEA-647). The labels below are client
presentation, indexed by apply.
"""
import bonuscatalog

CORE_VNUM = 79524
SEAL_VNUM = 79534
CORE_WEAR_CELL = 50
FIRST_APPLY = 135
LAST_APPLY = 170

BOSSES = (
	u"Pibos", u"Kryptian", u"Anu'Lim", u"Strážce Atlantidy", u"Elita Atlantidy",
	u"Quag Primus", u"Nekromant věže", u"Prastarý džunglový kolos",
	u"Sopečný džunglový titán", u"Sloní vojevůdce", u"Mladší sloní vojevůdce",
)
METINS = (
	u"Meteor strážce oázi", u"Meteor hlubinné perly", u"Meteor krabího strážce",
	u"Meteor ohnivého jaguára", u"Meteor přízraků", u"Meteor pralesního ducha",
	u"Meteor zlatého hrobu",
)
DUNGEONS = (
	u"Chrám Jiangshi", u"Chrám Utopeného Boha", u"Ledová Citadela", u"Hydra",
	u"Jotun", u"Andunův chrám", u"Doupě Prastarého Minotaura",
	u"Mystický Bambusový chrám", u"Ruiny Mazarifa",
)


def IsScopedApply(affectType):
	return FIRST_APPLY <= affectType <= LAST_APPLY


def CanUseSeal(sourceVnum, targetVnum):
	return sourceVnum == SEAL_VNUM and targetVnum == CORE_VNUM


def IsMaximum(affectType, value):
	if not IsScopedApply(affectType):
		return False
	catalog = bonuscatalog.Current()
	maximum = catalog.CoreMaximum(affectType) if catalog else None
	return maximum is not None and value == maximum


def FormatAffect(affectType, value, czech=True):
	if not IsScopedApply(affectType) or not value:
		return None
	if affectType < 146:
		label = (u"Síla proti %s" if czech else u"Strength against %s") % BOSSES[affectType - 135]
	elif affectType < 153:
		label = (u"Síla proti %s" if czech else u"Strength against %s") % METINS[affectType - 146]
	elif affectType < 162:
		label = (u"Síla v dungeonu: %s" if czech else u"Dungeon strength: %s") % DUNGEONS[affectType - 153]
	else:
		label = (u"Zkrácení čekání: %s" if czech else u"Cooldown reduction: %s") % DUNGEONS[affectType - 162]
	return u"%s %+d%%" % (label, value)
