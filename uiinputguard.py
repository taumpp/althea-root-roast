# -*- coding: utf-8 -*-
"""InputGuard v1 windows: the temporary-restriction curtain and the owner
of the GM watch viewer.

Both are owned by interfacemodule.Interface through InputGuardSystem and are
driven only by the EXE's BINARY_InputGuard* hooks on the game window. Neither
is remembered by the client: a warp or relog destroys them and the server
sends the state again. State and validation live in inputguardmodel.

The restriction curtain is the only element a player can ever see, and its
texts speak only of a temporary restriction. The viewer (uiinputguardwatch,
inputguardwatchmodel) is imported and built only when the server starts a
watch for this (GM) client, which it announces with the viewer's legend;
this module must not import either at the top.
"""

import app
import dbg
import grp
import ui
import wndMgr

import inputguardmodel
import localeInfo


def _LocaleText(key, fallback):
	return getattr(localeInfo, key, None) or fallback


def _FormatLocale(template, value):
	try:
		return template % value
	except (TypeError, ValueError):
		return "%s %s" % (template, value)


class PenaltyWindow(ui.Bar):
	"""Full-screen dim curtain with a centred countdown panel.

	The window is pickable and covers the screen, so it swallows the mouse;
	it takes the keyboard focus and eats every key, and the game window asks
	InputGuardSystem.IsInputLocked() for its own handlers. One curtain at a
	time: while a warp or phase curtain is up this one stays transparent
	(still locking input) and appears when the other one is gone. A curtain
	that never goes away cannot hide the reason for the lock for long: after
	MAX_YIELD_SECONDS the restriction is shown regardless.
	"""

	CURTAIN_ALPHA = 0.53
	MAX_YIELD_SECONDS = 15.0
	PANEL_WIDTH = 480
	PANEL_HEIGHT = 150
	TITLE_COLOR = 0xfff2e6d0
	COUNTDOWN_COLOR = 0xffffd36b
	HINT_COLOR = 0xffb7ad99

	def __init__(self, model, otherCurtainProbe=None):
		ui.Bar.__init__(self, "CURTAIN")
		if getattr(wndMgr, "IME_RETURN_PRIORITY", 0) == 1:
			self.AddFlag("ime_return_priority")
		self.SetWindowName("TemporaryRestriction")
		self.AddFlag("float")
		self.model = model
		self.otherCurtainProbe = otherCurtainProbe
		self.presented = None
		self.yieldSince = None
		self.shownSeconds = None
		self.screenSize = None
		self.remainingTemplate = _LocaleText("TEMP_RESTRICTION_REMAINING", "Time remaining: %s")
		self.panel = None
		self.borders = []
		self.titleLine = None
		self.countdownLine = None
		self.hintLine = None
		self.__Build()
		self.Hide()

	def __del__(self):
		ui.Bar.__del__(self)

	def Destroy(self):
		self.Close()
		self.otherCurtainProbe = None
		self.titleLine = None
		self.countdownLine = None
		self.hintLine = None
		self.borders = []
		self.panel = None

	def __MakeLine(self, y, color, large):
		line = ui.TextLine()
		line.SetParent(self.panel)
		line.AddFlag("not_pick")
		if large:
			line.SetFontName(getattr(localeInfo, "UI_DEF_FONT_LARGE", localeInfo.UI_DEF_FONT))
		line.SetHorizontalAlignCenter()
		line.SetOutline()
		line.SetPackedFontColor(color)
		line.SetPosition(self.PANEL_WIDTH // 2, y)
		line.Show()
		return line

	def __Build(self):
		panel = ui.Bar()
		panel.SetParent(self)
		panel.AddFlag("not_pick")
		panel.SetSize(self.PANEL_WIDTH, self.PANEL_HEIGHT)
		panel.SetColor(grp.GenerateColor(0.05, 0.04, 0.04, 0.88))
		self.panel = panel
		for y in (0, self.PANEL_HEIGHT - 1):
			border = ui.Bar()
			border.SetParent(panel)
			border.AddFlag("not_pick")
			border.SetPosition(0, y)
			border.SetSize(self.PANEL_WIDTH, 1)
			border.SetColor(grp.GenerateColor(0.72, 0.58, 0.32, 0.9))
			border.Show()
			self.borders.append(border)
		self.titleLine = self.__MakeLine(30, self.TITLE_COLOR, True)
		self.titleLine.SetText(_LocaleText("TEMP_RESTRICTION_TITLE",
			"Your character is temporarily restricted."))
		self.countdownLine = self.__MakeLine(70, self.COUNTDOWN_COLOR, True)
		self.hintLine = self.__MakeLine(112, self.HINT_COLOR, False)
		self.hintLine.SetText(_LocaleText("TEMP_RESTRICTION_HINT",
			"You can continue playing when the time runs out."))
		self.__Layout()

	def __Layout(self):
		width, height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
		self.screenSize = (width, height)
		self.SetPosition(0, 0)
		self.SetSize(width, height)
		self.panel.SetPosition((width - self.PANEL_WIDTH) // 2,
			(height - self.PANEL_HEIGHT) // 2)

	def __IsYielding(self, now):
		probe = self.otherCurtainProbe
		try:
			yielding = bool(probe and probe())
		except Exception:
			yielding = False
		if not yielding:
			self.yieldSince = None
			return False
		if self.yieldSince is None:
			self.yieldSince = now
		return now - self.yieldSince < self.MAX_YIELD_SECONDS

	def __Present(self, presented):
		if presented == self.presented:
			return
		self.presented = presented
		self.SetColor(grp.GenerateColor(0.0, 0.0, 0.0,
			self.CURTAIN_ALPHA if presented else 0.0))
		if presented:
			self.panel.Show()
			self.SetTop()
			self.SetFocus()
		else:
			self.panel.Hide()

	def __RefreshCountdown(self, now):
		seconds = self.model.Remaining(now)
		if seconds == self.shownSeconds:
			return
		self.shownSeconds = seconds
		self.countdownLine.SetText(_FormatLocale(self.remainingTemplate,
			inputguardmodel.FormatCountdown(seconds)))

	def Open(self):
		"""Show or refresh from the model (the server packet set it)."""
		now = app.GetTime()
		if self.screenSize != (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()):
			self.__Layout()
		self.shownSeconds = None
		self.__RefreshCountdown(now)
		if not self.IsShow():
			self.presented = None
			self.yieldSince = None
			self.Show()
		self.__Present(not self.__IsYielding(now))

	def Close(self):
		wasShown = self.IsShow()
		self.presented = None
		self.shownSeconds = None
		if wasShown:
			if self.IsFocus():
				self.KillFocus()
			self.Hide()
		return wasShown

	def IsInputLocked(self):
		return bool(self.model.active and self.IsShow())

	def OnUpdate(self):
		now = app.GetTime()
		if not self.model.Update(now):
			self.Close()
			return
		if self.screenSize != (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()):
			self.__Layout()
		self.__Present(not self.__IsYielding(now))
		self.__RefreshCountdown(now)

	# Every key stays here while the restriction is shown.
	def OnKeyDown(self, key):
		return True

	def OnKeyUp(self, key):
		return True

	def OnPressEscapeKey(self):
		return True

	def OnPressExitKey(self):
		return True

	def OnIMEReturn(self):
		return True


class InputGuardSystem(object):
	"""Owner of both windows; every entry point is safe to call at any time.

	Windows are created on the first packet that needs them. A failure to
	build one is logged and leaves the game untouched (no lock without a
	visible window).
	"""

	def __init__(self):
		self.penaltyModel = inputguardmodel.PenaltyModel()
		# Built by the first legend row or OnWatchBegin; None until then.
		self.watchModel = None
		self.penaltyWindow = None
		self.watchWindow = None
		self.otherCurtainProbe = None
		self.lockListener = None
		self.locked = False

	def BindGameWindow(self, otherCurtainProbe, lockListener):
		"""otherCurtainProbe() -> a warp/phase curtain is up;
		lockListener(locked) -> the game window releases held input."""
		self.otherCurtainProbe = otherCurtainProbe
		self.lockListener = lockListener
		if self.penaltyWindow:
			self.penaltyWindow.otherCurtainProbe = otherCurtainProbe

	def Destroy(self):
		self.__SetLocked(False)
		self.otherCurtainProbe = None
		self.lockListener = None
		self.penaltyModel.Reset()
		if self.watchModel:
			if self.watchModel.logicalWatch:
				self.watchModel.KeepContinuation()
				self.watchModel = None
			else:
				self.watchModel.Reset()
				self.watchModel.ForgetLegend()
		if self.penaltyWindow:
			self.penaltyWindow.Destroy()
		self.penaltyWindow = None
		if self.watchWindow:
			self.watchWindow.Destroy()
		self.watchWindow = None

	def OnSessionEnd(self):
		"""Drop capture/UI state; retain only the bounded logical staff viewer."""
		self.penaltyModel.Reset()
		if self.penaltyWindow:
			self.penaltyWindow.Close()
		self.__SetLocked(False)
		if self.watchModel:
			if self.watchModel.logicalWatch:
				self.watchModel.KeepContinuation()
				self.watchModel = None
			else:
				self.watchModel.Reset()
				self.watchModel.ForgetLegend()
		if self.watchWindow:
			self.watchWindow.Close()

	def __SetLocked(self, locked):
		if locked == self.locked:
			return
		self.locked = locked
		listener = self.lockListener
		if listener:
			try:
				listener(locked)
			except Exception as error:
				dbg.TraceError("TemporaryRestriction lock listener failed: %s" % error)

	# Temporary restriction -------------------------------------------------
	def OnPenalty(self, remainingSec, reason):
		active = self.penaltyModel.Apply(app.GetTime(), remainingSec, reason)
		if not active:
			if self.penaltyWindow:
				self.penaltyWindow.Close()
			self.__SetLocked(False)
			return False
		try:
			if not self.penaltyWindow:
				self.penaltyWindow = PenaltyWindow(self.penaltyModel, self.otherCurtainProbe)
			self.penaltyWindow.Open()
		except Exception as error:
			dbg.TraceError("TemporaryRestriction window unavailable: %s" % error)
			self.penaltyModel.Reset()
			self.penaltyWindow = None
			self.__SetLocked(False)
			return False
		self.__SetLocked(True)
		return True

	def IsInputLocked(self):
		window = self.penaltyWindow
		locked = bool(window and window.IsInputLocked())
		if not locked and self.locked:
			# The local countdown ended and the window closed itself.
			self.__SetLocked(False)
		return locked

	# GM watch viewer -----------------------------------------------------------
	def __RefreshWatch(self):
		window = self.watchWindow
		if window and window.IsShow():
			window.Refresh()

	def __EnsureWatchModel(self):
		if not self.watchModel:
			# The only place the viewer's state module is imported.
			try:
				import inputguardwatchmodel
				self.watchModel = inputguardwatchmodel.TakeContinuation() or inputguardwatchmodel.WatchModel()
			except Exception as error:
				dbg.TraceError("InputGuard watch viewer unavailable: %s" % error)
				self.watchModel = None
		return self.watchModel

	def OnWatchLegend(self, row):
		"""One row of the viewer's legend as the server wrote it. The server
		sends it to a watcher alone, so it may build the watch model; it
		opens nothing."""
		model = self.__EnsureWatchModel()
		if not model:
			return False
		return model.LegendRow(row)

	def OnWatchState(self, pid, watchId, captureId, deadline, gap):
		model = self.__EnsureWatchModel()
		return model.LogicalState(pid, watchId, captureId, deadline, gap) if model else False

	def OnWatchBegin(self, pid, captureId, name):
		if not self.__EnsureWatchModel():
			return False
		if not self.watchModel.Begin(pid, captureId, name):
			return False
		try:
			if not self.watchWindow:
				import uiinputguardwatch
				self.watchWindow = uiinputguardwatch.WatchWindow(self.watchModel)
			self.watchWindow.Open()
		except Exception as error:
			dbg.TraceError("InputGuard watch viewer unavailable: %s" % error)
			self.watchModel.Reset()
			self.watchWindow = None
			return False
		return True

	# Without a watch model there is no Begin, and the model ignores every
	# callback without one: the values below are what it returns then.
	def OnWatchTrace(self, pid, clientWidth, clientHeight, samples):
		if not self.watchModel:
			return 0
		return self.watchModel.Trace(pid, clientWidth, clientHeight, samples)

	def OnWatchVerdict(self, pid, verdict):
		if not self.watchModel:
			return False
		return self.watchModel.Verdict(pid, verdict)

	def OnWatchAction(self, pid, tMs, kind, cover):
		if not self.watchModel:
			return False
		return self.watchModel.Action(pid, tMs, kind, cover)

	def OnWatchEnd(self, pid, reason):
		if not self.watchModel:
			return False
		ended = self.watchModel.End(pid, reason)
		if ended:
			self.__RefreshWatch()
		return ended

	def OnWatchStatus(self, pid, report, secondsSinceReport, missedHeartbeats, penaltyActive):
		if not self.watchModel:
			return False
		return self.watchModel.Status(pid, report, secondsSinceReport,
			missedHeartbeats, penaltyActive)
