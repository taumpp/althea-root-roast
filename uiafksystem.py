import app
import chat
import localeInfo
import net
import ui
import uiCommon


STATE_DISABLED = 0
STATE_LOADING = 1
STATE_INELIGIBLE = 2
STATE_QUALIFYING = 3
STATE_ACTIVE = 4
STATE_PAUSED_STORAGE = 5


def _Locale(key, fallback):
	return getattr(localeInfo, key, fallback)


def _FormatDuration(seconds):
	try:
		seconds = max(0, int(seconds))
	except (TypeError, ValueError):
		seconds = 0
	days, seconds = divmod(seconds, 86400)
	hours, seconds = divmod(seconds, 3600)
	minutes, seconds = divmod(seconds, 60)
	parts = []
	if days:
		parts.append("%dd" % days)
	if hours or days:
		parts.append("%dh" % hours)
	if minutes or hours or days:
		parts.append("%dm" % minutes)
	parts.append("%ds" % seconds)
	return " ".join(parts)


class AfkSystem(object):
	def __init__(self):
		self.affectShower = None
		self.tipBoard = None
		self.snapshot = (
			STATE_LOADING, 0, 0, 0, 0, 0
		)
		self.snapshotAt = app.GetTime()
		self.teleportOffer = (0, 0, 0)
		self.teleportQuestion = None
		self.teleportPromptSuppressed = False
		self.lastTeleportOfferAt = 0.0
		self.lastIndicatorSecond = -1

	def Destroy(self):
		self._CloseTeleportQuestion()
		if self.affectShower:
			self.affectShower.SetAfkIndicator(False, "", None)
		self.affectShower = None
		self.tipBoard = None

	def BindAffectShower(self, shower):
		self.affectShower = shower
		self._RefreshPresentation()

	def BindTipBoard(self, tipBoard):
		self.tipBoard = tipBoard

	def IsAvailable(self):
		function = getattr(net, "IsAfkSystemAvailable", None)
		return bool(callable(function) and function())

	def HasTeleportOffer(self):
		offerId, expiresAt, unusedMap = self.teleportOffer
		return bool(
			offerId and expiresAt > app.GetGlobalTimeStamp()
		)

	def _QualificationSeconds(self):
		getOffer = getattr(net, "GetAfkSystemOffer", None)
		if callable(getOffer):
			value = getOffer()
			if isinstance(value, tuple) and len(value) == 2:
				try:
					seconds = int(value[1])
				except (TypeError, ValueError):
					seconds = 0
				if 60 <= seconds <= 3600:
					return seconds
		return 600

	def _CloseTeleportQuestion(self, suppress=False):
		if self.teleportQuestion:
			self.teleportQuestion.Close()
		self.teleportQuestion = None
		if suppress:
			self.teleportPromptSuppressed = True

	def _OpenTeleportQuestion(self):
		if (not self.HasTeleportOffer() or self.teleportPromptSuppressed or
				self.teleportQuestion):
			return

		dialog = uiCommon.QuestionDialog2()
		dialog.SetWidth(430)
		dialog.SetText1(_Locale(
			"AFK_TELEPORT_CONFIRM_CONTEXT",
			"You were detected as AFK outside the AFK zone.",
		))
		dialog.SetText2(_Locale(
			"AFK_TELEPORT_CONFIRM_QUESTION",
			"Do you want to teleport to the AFK zone?",
		))
		dialog.SetAcceptEvent(ui.__mem_func__(self._AcceptTeleportQuestion))
		dialog.SetCancelEvent(ui.__mem_func__(self._DeclineTeleportQuestion))
		dialog.OnPressEscapeKey = ui.__mem_func__(
			self._DeclineTeleportQuestion)
		dialog.Open()
		self.teleportQuestion = dialog

	def _AcceptTeleportQuestion(self):
		self._CloseTeleportQuestion(True)
		self.RequestTeleport()
		return True

	def _DeclineTeleportQuestion(self):
		self._CloseTeleportQuestion(True)
		return True

	def _ReadNativeState(self):
		if not self.IsAvailable():
			self.snapshot = (
				STATE_DISABLED, 1, 0, 0, 0, 0
			)
			self.teleportOffer = (0, 0, 0)
			self._CloseTeleportQuestion()
			self.teleportPromptSuppressed = False
			self.lastTeleportOfferAt = 0.0
			self.snapshotAt = app.GetTime()
			return
		getSnapshot = getattr(net, "GetAfkSnapshot", None)
		getTeleport = getattr(net, "GetAfkTeleportOffer", None)
		if callable(getSnapshot):
			value = getSnapshot()
			if isinstance(value, tuple) and len(value) == 6:
				self.snapshot = value
				self.snapshotAt = app.GetTime()
		if callable(getTeleport):
			value = getTeleport()
			if isinstance(value, tuple) and len(value) == 3:
				self.teleportOffer = value

	def _Interpolated(self):
		state, reason, flags, remaining, sessionSeconds, totalSeconds = self.snapshot
		elapsed = max(0, int(app.GetTime() - self.snapshotAt))
		if state == STATE_QUALIFYING:
			remaining = max(0, remaining - elapsed)
		elif state == STATE_ACTIVE:
			sessionSeconds += elapsed
			totalSeconds += elapsed
		return state, reason, flags, remaining, sessionSeconds, totalSeconds

	def _IndicatorDescription(self, view):
		state, unusedReason, unusedFlags, remaining, sessionSeconds, unusedTotal = view
		if state == STATE_ACTIVE:
			return "%s\n%s: %s" % (
				_Locale("AFK_STATE_ACTIVE", "AFK active"),
				_Locale("AFK_SYSTEM_SESSION", "Session"),
				_FormatDuration(sessionSeconds),
			)
		if state == STATE_QUALIFYING:
			return "%s\n%s: %s" % (
				_Locale("AFK_STATE_QUALIFYING", "AFK waiting"),
				_Locale("AFK_SYSTEM_COUNTDOWN", "Starts in"),
				_FormatDuration(remaining),
			)
		return _Locale("AFK_STATE_PAUSED", "AFK storage paused")

	def _RefreshPresentation(self):
		view = self._Interpolated()
		state = view[0]
		showIndicator = self.IsAvailable() and state in (
			STATE_QUALIFYING, STATE_ACTIVE, STATE_PAUSED_STORAGE
		)
		if self.affectShower:
			self.affectShower.SetAfkIndicator(
				showIndicator,
				self._IndicatorDescription(view),
				None,
			)

	def Refresh(self):
		self._ReadNativeState()
		self._RefreshPresentation()

	def OnChanged(self):
		previousState = self.snapshot[0]
		self.Refresh()
		if previousState != STATE_ACTIVE and self.snapshot[0] == STATE_ACTIVE:
			text = "%s: %s" % (
				_Locale("AFK_SYSTEM_TITLE", "AFK system"),
				_Locale("AFK_STATE_ACTIVE", "Active"),
			)
			if self.tipBoard:
				self.tipBoard.SetTip(text)
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	def OnTeleportOffer(self, offerId, expiresAt, mapIndex):
		now = app.GetTime()
		newCycleGap = max(60.0, self._QualificationSeconds() * 0.5)
		if (self.teleportPromptSuppressed and self.lastTeleportOfferAt and
				now - self.lastTeleportOfferAt >= newCycleGap):
			self.teleportPromptSuppressed = False
		self.lastTeleportOfferAt = now
		self.teleportOffer = (offerId, expiresAt, mapIndex)
		self._OpenTeleportQuestion()
		self._RefreshPresentation()

	def OnTeleportResult(self, unusedOfferId, status):
		self._CloseTeleportQuestion(True)
		self.teleportOffer = (0, 0, 0)
		key = {
			1: ("AFK_TELEPORT_ACCEPTED", "Transfer accepted."),
			2: ("AFK_TELEPORT_EXPIRED", "The AFK transfer offer expired."),
			3: ("AFK_TELEPORT_INVALID", "The AFK transfer is no longer valid."),
			4: ("AFK_TELEPORT_UNAVAILABLE", "The AFK transfer is unavailable."),
		}.get(status, ("AFK_TELEPORT_UNAVAILABLE", "The AFK transfer is unavailable."))
		chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(*key))
		self.Refresh()

	def OnError(self, unusedRequestId, reason):
		messages = {
			1: ("AFK_ERROR_DISABLED", "The AFK system is disabled."),
			2: ("AFK_ERROR_UNAVAILABLE", "The AFK system is temporarily unavailable."),
			3: ("AFK_ERROR_INVALID_REQUEST", "The AFK request was invalid."),
			4: ("AFK_ERROR_INVALID_STATE", "This action is not available now."),
			5: ("AFK_ERROR_RATE_LIMIT", "Please wait before trying again."),
			6: ("AFK_ERROR_INTERNAL", "The AFK request could not be completed."),
		}
		chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(*messages.get(
			reason, messages[6])))

	def RequestTeleport(self):
		if not self.HasTeleportOffer():
			self.Refresh()
			return
		offerId = self.teleportOffer[0]
		function = getattr(net, "SendAfkTeleport", None)
		if not callable(function) or not function(offerId):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"AFK_ERROR_UNAVAILABLE",
				"The AFK system is temporarily unavailable.",
			))

	def OnUpdate(self):
		if not self.IsAvailable():
			return
		second = int(app.GetTime())
		if second == self.lastIndicatorSecond:
			return
		self.lastIndicatorSecond = second
		if self.HasTeleportOffer() is False and self.teleportOffer[0]:
			self._CloseTeleportQuestion(True)
			self.teleportOffer = (0, 0, 0)
		self._RefreshPresentation()
