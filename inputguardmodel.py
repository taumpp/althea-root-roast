# -*- coding: utf-8 -*-
"""InputGuard v1: headless content state every client loads.

Everything that crosses a repository boundary (command name, capability
bits, callback argument orders, automation masks) is fixed by the
cross-repository contract; see docs/FEATURE_INVARIANTS.md ("InputGuard v1").
This module only keeps state and formats it: the temporary-restriction
countdown and the ids the hover probe reports. It imports no client module,
so it runs under plain Python in tests. Every value the server hands over is
validated here and never raised to the caller. The GM watch viewer's state
lives in inputguardwatchmodel, which may import this module; this module
never imports it.
"""

OFFER_VERSION = "1"

CAP_PENALTY_UI = 64
CAP_WATCH_UI = 128
CONTENT_CAPS = CAP_PENALTY_UI | CAP_WATCH_UI

AUTOMATION_METIN_QUEUE = 1
AUTOMATION_AUTO_PICKUP = 2
AUTOMATION_QUICK_BUFF = 4
AUTOMATION_SWITCHBOT = 8
AUTOMATION_AUTO_ATTACK = 16
AUTOMATION_OTHER = 32
AUTOMATION_ALL = 63

SLOT_NONE = 0xFFFF

# Stable ids content reports through inputguard.SetHoverUi. Append only.
HOVER_UI_WINDOWS = (
	(1, "wndInventory", "inventory"),
	(2, "wndCharacter", "character"),
	(3, "wndSafebox", "safebox"),
	(4, "dlgShop", "shop"),
	(5, "dlgExchange", "exchange"),
	(6, "wndMiniMap", "minimap"),
	(7, "wndTaskBar", "taskbar"),
	(8, "wndChat", "chat"),
	(9, "wndSwitchbot", "switchbot"),
	(10, "wndVirtualMarket", "market"),
	(11, "wndDragonSoul", "alchemy"),
	(12, "wndMall", "item mall"),
	(13, "wndCubeRenewal", "crafting"),
	(14, "dlgRefineNew", "refine"),
	(15, "wndMessenger", "messenger"),
	(16, "wndGuild", "guild"),
	(17, "dlgSystem", "system menu"),
)

_U8 = 0xFF
_U32 = 0xFFFFFFFF

try:
	_INTEGER_TYPES = (int, long)
except NameError:
	_INTEGER_TYPES = (int,)


def _Integer(value, maximum, minimum=0):
	"""Exact integer within [minimum, maximum], or None."""
	if isinstance(value, bool) or not isinstance(value, _INTEGER_TYPES):
		return None
	if value < minimum or value > maximum:
		return None
	return int(value)


def FormatCountdown(seconds):
	"""Whole seconds as M:SS, H:MM:SS or Dd HH:MM:SS."""
	seconds = max(0, int(seconds))
	minutes, second = divmod(seconds, 60)
	hours, minute = divmod(minutes, 60)
	days, hour = divmod(hours, 24)
	if days:
		return "%dd %02d:%02d:%02d" % (days, hour, minute, second)
	if hours:
		return "%d:%02d:%02d" % (hour, minute, second)
	return "%d:%02d" % (minute, second)


class PenaltyModel(object):
	"""Temporary restriction: server-supplied duration, local countdown.

	The server alone opens, updates and closes it. The countdown runs on the
	local clock; when it reaches zero the client keeps its lock for a short
	grace and then lets go, so a lost close packet cannot strand the player
	behind the curtain. The server keeps dropping gameplay packets until its
	own timer ends, and re-sends the remaining time on every game entry.
	"""

	MAX_SECONDS = 10 * 365 * 24 * 60 * 60
	EXPIRY_GRACE_SECONDS = 3.0

	def __init__(self):
		self.active = False
		self.endTime = 0.0
		self.reason = 0

	def Reset(self):
		self.active = False
		self.endTime = 0.0
		self.reason = 0

	def Apply(self, now, remainingSec, reason=0):
		"""Server packet; returns whether a restriction is active afterwards."""
		seconds = _Integer(remainingSec, _U32)
		if not seconds:
			self.Reset()
			return False
		self.active = True
		self.endTime = float(now) + min(seconds, self.MAX_SECONDS)
		self.reason = _Integer(reason, _U8) or 0
		return True

	def Remaining(self, now):
		"""Whole seconds left on the local clock (rounded up, never negative)."""
		if not self.active:
			return 0
		left = self.endTime - float(now)
		if left <= 0.0:
			return 0
		whole = int(left)
		return whole if whole == left else whole + 1

	def Update(self, now):
		"""Advance the local clock; returns whether the lock still holds."""
		if self.active and float(now) >= self.endTime + self.EXPIRY_GRACE_SECONDS:
			self.Reset()
		return self.active
