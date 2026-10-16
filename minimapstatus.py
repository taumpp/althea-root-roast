# -*- coding: utf-8 -*-
"""Native minimap status text; independent of OS date-language settings."""

import globalhub


def FormatDate(localTime):
	# A fixed-width numeric date leaves room for readable native glyphs.
	return "%02d.%02d.%04d" % (localTime.tm_mday, localTime.tm_mon, localTime.tm_year)


def FormatChannel(channelNumber, mapIndex):
	if globalhub.IsGlobalHub(channelNumber, mapIndex):
		# Footer-only presentation; never change the native HUB sentinel.
		return "CH1"
	try:
		channelNumber = int(channelNumber)
	except (TypeError, ValueError):
		return ""
	# Missing channel state and the physical HUB route are not player channels.
	if channelNumber <= 0 or channelNumber == 98:
		return ""
	return "CH%d" % channelNumber
