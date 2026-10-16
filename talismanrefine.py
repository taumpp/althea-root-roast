# -*- coding: utf-8 -*-
"""Presentation mirror of the server talisman refine contract.

The server (server-src common/talisman_contract.h and
talisman_refine_policy.h) stays the authority. The client only uses these
rules to explain a refusal the server would otherwise make silently and to
avoid a misleading downgrade warning.
"""

FAMILY_RANGES = (
	(9600, 9650),
	(9830, 9880),
	(10060, 10110),
	(10290, 10340),
	(10520, 10570),
)
MAXIMUM_REFINE = 25
# Blessing Scroll 25040 and the Magic Stones 25041/39001.
REFINE_SCROLLS = (25040, 25041, 39001)


def RefineLevel(vnum):
	vnum = int(vnum)
	for first, last in FAMILY_RANGES:
		if first <= vnum <= last:
			return vnum - first
	return -1


def IsTalisman(vnum):
	return RefineLevel(vnum) >= 0


def RefineRejectionKey(scrollVnum, targetVnum):
	"""Locale key explaining why the server refuses this scroll, or None."""
	level = RefineLevel(targetVnum)
	if level < 0:
		return None
	if int(scrollVnum) not in REFINE_SCROLLS:
		return "TALISMAN_REFINE_SCROLL_REQUIRED"
	if level == 0:
		return "TALISMAN_REFINE_CRAFT_FIRST"
	if level >= MAXIMUM_REFINE:
		return "REFINE_FAILURE_UPGRADE_DISABLE_ITEM"
	return None


def KeepsGradeOnFailure(targetVnum):
	# The server forces keep-grade for every fixed talisman refine.
	return IsTalisman(targetVnum)
