# -*- coding: utf-8 -*-
"""Presentation mirror of the server rule for a failed glove refine.

The server keeps these gloves and their grade when a refine at the
blacksmith fails; every other item is destroyed there. The client uses the
ranges only to word the warning before the attempt.
"""

KEPT_ON_FAILURE_RANGES = (
	(23000, 23049),
	(23100, 23139),
)


def KeepsItemOnFailure(vnum):
	vnum = int(vnum)
	for first, last in KEPT_ON_FAILURE_RANGES:
		if first <= vnum <= last:
			return True
	return False
