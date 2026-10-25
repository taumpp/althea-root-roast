# -*- coding: utf-8 -*-
"""InputGuard v1: guarded bridge to the EXE.

The root pack must run unchanged on an EXE without the `inputguard` module
or `net.SendInputGuardDeclare`, and on a server that never offers. Every
native call therefore goes through this module: a missing function is a
no-op, a failing one is swallowed and never reaches the game loop.

Automation flags are cached, so the per-frame callers cost one integer
comparison and reach the EXE only when a flag really changes.
"""

import inputguardmodel

try:
	import inputguard as _native
except ImportError:
	_native = None

CONTENT_CAPS = inputguardmodel.CONTENT_CAPS
AUTOMATION_METIN_QUEUE = inputguardmodel.AUTOMATION_METIN_QUEUE
AUTOMATION_AUTO_PICKUP = inputguardmodel.AUTOMATION_AUTO_PICKUP
AUTOMATION_QUICK_BUFF = inputguardmodel.AUTOMATION_QUICK_BUFF
AUTOMATION_SWITCHBOT = inputguardmodel.AUTOMATION_SWITCHBOT
AUTOMATION_AUTO_ATTACK = inputguardmodel.AUTOMATION_AUTO_ATTACK

CONTENT_AUTOMATIONS = (
	AUTOMATION_METIN_QUEUE,
	AUTOMATION_AUTO_PICKUP,
	AUTOMATION_QUICK_BUFF,
	AUTOMATION_SWITCHBOT,
	AUTOMATION_AUTO_ATTACK,
)

HOVER_NONE = (0, inputguardmodel.SLOT_NONE)
HOVER_PROBE_INTERVAL = 0.2
SWITCHBOT_PROBE_INTERVAL = 0.5

# [automation mask, hover id, hover slot]
_state = [0, HOVER_NONE[0], HOVER_NONE[1]]


def _NativeFunction(name):
	if _native is None:
		return None
	return getattr(_native, name, None)


def HasAutomationApi():
	return _NativeFunction("SetAutomation") is not None


def HasHoverApi():
	return _NativeFunction("SetHoverUi") is not None


def Declare(netModule, version):
	"""Answer the server's InputGuardV1 offer; False when nothing was sent."""
	if str(version) != inputguardmodel.OFFER_VERSION:
		return False
	send = getattr(netModule, "SendInputGuardDeclare", None)
	if send is None:
		return False
	send(CONTENT_CAPS)
	return True


def GetAutomationMask():
	return _state[0]


def SetAutomation(mask, active):
	"""Mark a sanctioned automation; returns whether the flag changed."""
	current = _state[0]
	updated = (current | mask) if active else (current & ~mask)
	if updated == current:
		return False
	_state[0] = updated
	function = _NativeFunction("SetAutomation")
	if function is not None:
		try:
			function(mask, 1 if active else 0)
		except Exception:
			pass
	return True


def ResendAutomation():
	"""Push every flag again: the EXE may have dropped its state with the
	connection, and the server offers on every game entry."""
	function = _NativeFunction("SetAutomation")
	if function is None:
		return False
	current = _state[0]
	try:
		for mask in CONTENT_AUTOMATIONS:
			function(mask, 1 if current & mask else 0)
	except Exception:
		return False
	return True


def ClearAutomation():
	for mask in CONTENT_AUTOMATIONS:
		SetAutomation(mask, False)


def SetHoverUi(uiId, slot=inputguardmodel.SLOT_NONE):
	if _state[1] == uiId and _state[2] == slot:
		return False
	_state[1] = uiId
	_state[2] = slot
	function = _NativeFunction("SetHoverUi")
	if function is not None:
		try:
			function(uiId, slot)
		except Exception:
			pass
	return True


def ClearHoverUi():
	return SetHoverUi(HOVER_NONE[0], HOVER_NONE[1])


def _Contains(window, mouseX, mouseY):
	if not window or not window.IsShow():
		return False
	x, y = window.GetGlobalPosition()
	return x <= mouseX < x + window.GetWidth() and y <= mouseY < y + window.GetHeight()


class HoverProbe(object):
	"""Reports which major window the cursor is over, a few times a second.

	Idle unless the EXE exposes SetHoverUi and the server offered InputGuard
	in this session. Any failure disables the probe for the rest of the run.
	"""

	def __init__(self, mousePositionFn, interval=HOVER_PROBE_INTERVAL):
		self.mousePositionFn = mousePositionFn
		self.interval = float(interval)
		self.nextTime = 0.0
		self.enabled = False
		self.failed = False

	def Enable(self):
		"""The server offered: report from scratch on this connection."""
		self.enabled = not self.failed and HasHoverApi()
		if self.enabled:
			_state[1] = None
		return self.enabled

	def Disable(self):
		self.enabled = False
		ClearHoverUi()

	def Update(self, now, interface):
		if not self.enabled or now < self.nextTime:
			return
		self.nextTime = now + self.interval
		try:
			mouseX, mouseY = self.mousePositionFn()
			found = HOVER_NONE[0]
			if interface:
				for uiId, attribute, _label in inputguardmodel.HOVER_UI_WINDOWS:
					if _Contains(getattr(interface, attribute, None), mouseX, mouseY):
						found = uiId
						break
			SetHoverUi(found)
		except Exception:
			self.failed = True
			self.Disable()


class SwitchbotProbe(object):
	"""Whether any switchbot slot is running, sampled twice a second."""

	def __init__(self, isActiveFn, slotCount, instantRunningFn=None,
			interval=SWITCHBOT_PROBE_INTERVAL):
		self.isActiveFn = isActiveFn
		self.slotCount = int(slotCount)
		self.instantRunningFn = instantRunningFn
		self.interval = float(interval)
		self.nextTime = 0.0
		self.active = False
		self.failed = False

	def Update(self, now):
		if self.failed or now < self.nextTime:
			return self.active
		self.nextTime = now + self.interval
		try:
			active = bool(self.instantRunningFn and self.instantRunningFn())
			if not active:
				for slot in range(self.slotCount):
					if self.isActiveFn(slot):
						active = True
						break
			self.active = active
		except Exception:
			self.failed = True
			self.active = False
		return self.active
