# the "return to dungeon" window survives temporary refusals.
# It stays open while an ACCEPT is in flight, shows the reason and a countdown
# after a DungeonRejoinRetry, and closes only when the offer itself expires
# (or the server sends a final DungeonRejoinResult, handled in game.py).

import app
import localeInfo
import uiCommon

import dungeonrejoinretry


class DungeonRejoinDialog(uiCommon.QuestionDialog2):
	def __init__(self):
		uiCommon.QuestionDialog2.__init__(self)
		self.retry = dungeonrejoinretry.RetryState()
		self.expiresAt = 0
		self.expireEvent = None
		self.shownText = None
		self.acceptEnabled = True

	def __del__(self):
		uiCommon.QuestionDialog2.__del__(self)

	def SetExpiresAt(self, expiresAt):
		self.expiresAt = expiresAt

	def SetExpireEvent(self, event):
		self.expireEvent = event

	def CanAccept(self):
		return self.retry.CanAccept(app.GetTime())

	def BeginAccept(self):
		self.retry.Begin(app.GetTime())
		self.Refresh()

	def Refuse(self, reason, seconds):
		self.retry.Refuse(reason, seconds, app.GetTime())
		self.Refresh()

	def Close(self):
		self.expireEvent = None
		uiCommon.QuestionDialog2.Close(self)

	def __LineText(self, kind, value):
		if kind == dungeonrejoinretry.LINE_WAITING:
			return localeInfo.DUNGEON_REJOIN_WAITING
		if kind == dungeonrejoinretry.LINE_RETRY_COOLDOWN:
			return localeInfo.DUNGEON_REJOIN_RETRY_COOLDOWN % value
		if kind == dungeonrejoinretry.LINE_RETRY_BUSY:
			return localeInfo.DUNGEON_REJOIN_RETRY_BUSY % value
		return localeInfo.DUNGEON_REJOIN_REMAINING % localeInfo.SecondToDHM(value)

	def Refresh(self):
		offerLeft = self.expiresAt - app.GetGlobalTimeStamp()
		if offerLeft <= 0:
			event = self.expireEvent
			if event:
				self.expireEvent = None
				event()
			return

		kind, value = self.retry.StatusLine(app.GetTime(), offerLeft)
		text = self.__LineText(kind, value)
		if text != self.shownText:
			self.shownText = text
			self.SetText2(text)

		canAccept = self.CanAccept()
		if canAccept != self.acceptEnabled:
			self.acceptEnabled = canAccept
			if canAccept:
				self.acceptButton.Enable()
			else:
				self.acceptButton.Disable()

	def OnUpdate(self):
		self.Refresh()
