###################################################################################################
# Network

import app
import chr
import dbg
import net
import snd

import chr
import chrmgr
import background
import player
import playerSettingModule

import ui
import uiPhaseCurtain
import osfInfo

import localeInfo
import introLoading

import uiOfflineShop
import uiwarpstate
import noticestyle


def _IsCustomPortsInstantWarp():
	function = getattr(net, "IsCustomPortsInstantWarpInProgress", None)
	return bool(function and function())


class PopupDialog(ui.ScriptWindow):
	def __init__(self):
		#print "NEW POPUP DIALOG ----------------------------------------------------------------------------"
		ui.ScriptWindow.__init__(self)
		self.CloseEvent = 0
		self.messageLines = []

	def __del__(self):
		#print "---------------------------------------------------------------------------- DELETE POPUP DIALOG "
		ui.ScriptWindow.__del__(self)

	def LoadDialog(self):
		PythonScriptLoader = ui.PythonScriptLoader()
		PythonScriptLoader.LoadScriptFile(self, "UIScript/PopupDialog.py")

	def Open(self, Message, event = 0, ButtonName = localeInfo.UI_CANCEL):
		if True == self.IsShow():
			self.Close()

		self.Lock()
		self.SetTop()
		self.CloseEvent = event

		AcceptButton = self.GetChild("accept")
		AcceptButton.SetText(ButtonName)
		AcceptButton.SetEvent(ui.__mem_func__(self.Close))

		self._LayoutMessage(Message)
		self.SetCenterPosition()
		self.Show()

	def _ClearMessageLines(self):
		for line in self.messageLines:
			line.Hide()
		self.messageLines = []

	def _LayoutMessage(self, message):
		# Native multiline centers the whole text before wrapping. Center each
		# measured physical line instead; the hidden UIScript label only measures.
		# SetText updates native glyph metrics immediately, before GetTextSize.
		self._ClearMessageLines()
		measure = self.GetChild("message")
		measure.Hide()
		measure.SetText("")
		measure.SetFontName(localeInfo.UI_DEF_FONT)

		def width(text):
			measure.SetText(text)
			return measure.GetTextSize()[0]

		board = self.GetChild("board")
		rows = noticestyle.wrap(message.replace("[ENTER]", "\n"), 250, width)
		y = 28
		for text in rows:
			line = ui.TextLine()
			line.SetParent(board)
			line.SetFontName(localeInfo.UI_DEF_FONT)
			line.SetWindowHorizontalAlignCenter()
			line.SetHorizontalAlignCenter()
			line.SetVerticalAlignTop()
			line.AddFlag("not_pick")
			line.SetPosition(0, y)
			line.SetText(text)
			line.Show()
			self.messageLines.append(line)
			y += max(14, line.GetTextSize()[1]) + 4
		measure.SetText("")
		button = self.GetChild("accept")
		buttonY = max(63, y - 4 + 16)
		button.SetPosition(0, buttonY)
		height = max(105, buttonY + button.GetHeight() + 21)
		board.SetSize(280, height)
		self.SetSize(280, height)

	def Close(self):
		if False == self.IsShow():
			self.CloseEvent = 0
			return

		self.Unlock()
		self.Hide()
		self._ClearMessageLines()

		if 0 != self.CloseEvent:
			self.CloseEvent()
			self.CloseEvent = 0

	def Destroy(self):
		self.Close()
		self._ClearMessageLines()
		self.ClearDictionary()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnIMEReturn(self):
		self.Close()
		return True

##
## Main Stream
##
class MainStream(object):
	isChrData = 0

	def __init__(self):
		#print "NEWMAIN STREAM ----------------------------------------------------------------------------"
		net.SetHandler(self)
		net.SetTCPRecvBufferSize(128 * 1024)
		net.SetTCPSendBufferSize(4096)
		net.SetUDPRecvBufferSize(4096)

		# Launcher credentials are one-use; returning here is not a fresh launch.
		self.launcherConnectionAttempted = False
		self.connectionFailureMessage = None

		self.id = ""
		self.pwd = ""
		self.addr = ""
		self.port = 0
		self.account_addr = 0
		self.account_port = 0
		self.slot = 0
		self.isAutoSelect = 0
		self.isAutoLogin = 0
		# The server sends this once per login, not on return from game to select.
		self.familyNameStatus = -1
		self.familyName = ""

		self.curtain = 0
		self.curPhaseWindow = 0
		self.newPhaseWindow = 0

	def __del__(self):
		# Runtime cleanup belongs in Destroy(). Python may call __del__ after
		# sys.meta_path and module globals have already been torn down.
		pass

	def Destroy(self):
		import uiQuest
		if uiQuest.QuestDialog:
			if "QuestCurtain" in uiQuest.QuestDialog.__dict__:
				del uiQuest.QuestDialog.QuestCurtain

		uiOfflineShop.ClearOfflineShopManager()

		if self.curPhaseWindow:
			self.curPhaseWindow.Close()
			self.curPhaseWindow = 0

		if self.newPhaseWindow:
			self.newPhaseWindow.Close()
			self.newPhaseWindow = 0

		self.popupWindow.Destroy()
		self.popupWindow = 0

		self.curtain = 0

	def Create(self):
		self.CreatePopupDialog()

		self.curtain = uiPhaseCurtain.PhaseCurtain()

	def SetPhaseWindow(self, newPhaseWindow):
		if self.newPhaseWindow:
			#print "이미 새로운 윈도우로 바꾼상태에서 또 바꿈", newPhaseWindow
			self.__ChangePhaseWindow()

		self.newPhaseWindow=newPhaseWindow

		if self.curPhaseWindow:
			if _IsCustomPortsInstantWarp():
				self.curtain.HideInstantly()
				self.__ChangePhaseWindow()
			else:
				#print "페이드 아웃되면 바꿈"
				self.curtain.FadeOut(self.__ChangePhaseWindow)
		else:
			#print "현재 윈도우가 없는 상태라 바로 바꿈"
			self.__ChangePhaseWindow()

	def __ChangePhaseWindow(self):
		oldPhaseWindow = self.curPhaseWindow
		newPhaseWindow = self.newPhaseWindow
		self.curPhaseWindow = 0
		self.newPhaseWindow = 0

		if oldPhaseWindow:
			oldPhaseWindow.Close()

		if newPhaseWindow:
			newPhaseWindow.Open()

		self.curPhaseWindow = newPhaseWindow

		if self.curPhaseWindow:
			if _IsCustomPortsInstantWarp():
				self.curtain.HideInstantly()
			else:
				self.curtain.FadeIn()
		else:
			app.Exit()

	def CreatePopupDialog(self):
		self.popupWindow = PopupDialog()
		self.popupWindow.LoadDialog()
		self.popupWindow.SetCenterPosition()
		self.popupWindow.Hide()

	## SelectPhase
	##########################################################################################
	def SetLogoPhase(self):
		uiwarpstate.Clear()
		net.Disconnect()
		self.familyNameStatus = -1
		self.familyName = ""

		import introLogo
		self.SetPhaseWindow(introLogo.LogoWindow(self))

	def SetLoginPhase(self):
		uiwarpstate.Clear()
		net.Disconnect()
		self.familyNameStatus = -1
		self.familyName = ""

		import introconnect
		self.SetPhaseWindow(introconnect.ConnectionWindow(self))

		if app.ENABLE_DISCORD_STUFF:
			app.SetTitle(localeInfo.APP_TITLE, localeInfo.APP_MINI_TITLE)

	def SameLogin_SetLoginPhase(self):
		uiwarpstate.Clear()
		net.Disconnect()
		self.familyNameStatus = -1
		self.familyName = ""

		import introconnect
		self.SetPhaseWindow(introconnect.ConnectionWindow(self, localeInfo.LOGIN_FAILURE_SAMELOGIN))

	def SetSelectEmpirePhase(self):
		self.SetSelectCharacterPhase()

	def SetReselectEmpirePhase(self):
		self.SetCreateCharacterPhase()

	def SetSelectCharacterPhase(self):
		try:
			uiwarpstate.Clear()
			localeInfo.LoadLocaleData()
			# Successful login dismisses the status; it is not a user cancel.
			self.popupWindow.CloseEvent = 0
			self.popupWindow.Close()

			if app.ENABLE_SELECT_RENEWAL:
				import New_introSelect
				self.SetPhaseWindow(New_introSelect.SelectCharacterWindow(self))
			else:
				import introSelect
				self.SetPhaseWindow(introSelect.SelectCharacterWindow(self))
				if app.ENABLE_DISCORD_STUFF:
					app.SetTitle(localeInfo.APP_TITLE, localeInfo.APP_MINI_TITLE)
		except:
			import exception
			exception.Abort("networkModule.SetSelectCharacterPhase")

	def SetCreateCharacterPhase(self):
		try:
			uiwarpstate.Clear()
			if app.ENABLE_CREATE_RENEWAL:
				import New_introCreate
				self.SetPhaseWindow(New_introCreate.CreateCharacterWindow(self))
			else:
				import introCreate
				self.SetPhaseWindow(introCreate.CreateCharacterWindow(self))
		except:
			import exception
			exception.Abort("networkModule.SetCreateCharacterPhase")

	def SetTestGamePhase(self, x, y):
		try:
			uiwarpstate.Clear()
			loadingPhaseWindow = introLoading.LoadingWindow(self)
			loadingPhaseWindow.LoadData(x, y)
			self.SetPhaseWindow(loadingPhaseWindow)
		except:
			import exception
			exception.Abort("networkModule.SetLoadingPhase")

	def SetLoadingPhase(self):
		try:
			import introLoading
			instantCustomPortsWarp = _IsCustomPortsInstantWarp()
			if app.ENABLE_LOADING_PERFORMANCE:
				self.SetPhaseWindow(introLoading.NewLoadingWindow(self, silent=instantCustomPortsWarp))
			else:
				self.SetPhaseWindow(introLoading.LoadingWindow(self))
		except:
			import exception
			exception.Abort("networkModule.SetLoadingPhase")

	def SetGamePhase(self):
		try:
			import game
			self.popupWindow.Close()
			instantCustomPortsWarp = _IsCustomPortsInstantWarp()
			self.SetPhaseWindow(game.GameWindow(self))
			if instantCustomPortsWarp:
				complete = getattr(net, "CompleteCustomPortsInstantWarp", None)
				if complete:
					complete()
		except:
			raise
			import exception
			exception.Abort("networkModule.SetGamePhase")

	################################
	# Functions used in python

	## Login
	def Connect(self):
		import constInfo
		if app.LOGIN_COUNT_DOWN_UI_MODIFY:
			result = False
			if constInfo.KEEP_ACCOUNT_CONNETION_ENABLE:
				result = net.ConnectToAccountServer(self.addr, self.port, self.account_addr, self.account_port)
			else:
				result = net.ConnectTCP(self.addr, self.port)

			return result
		else:
			if constInfo.KEEP_ACCOUNT_CONNETION_ENABLE:
				net.ConnectToAccountServer(self.addr, self.port, self.account_addr, self.account_port)
			else:
				net.ConnectTCP(self.addr, self.port)

		#net.ConnectUDP(IP, Port)

	def SetConnectInfo(self, addr, port, account_addr = 0, account_port = 0):
		self.addr = addr
		self.port = port
		self.account_addr = account_addr
		self.account_port = account_port

	def GetConnectAddr(self):
		return self.addr

	def SetLoginInfo(self, id, pwd):
		self.id = id
		self.pwd = pwd
		net.SetLoginInfo(id, pwd)

	def CancelEnterGame(self):
		pass

	## Select
	def SetCharacterSlot(self, slot):
		self.slot = slot

	def GetCharacterSlot(self):
		return self.slot

	## Empty
	def EmptyFunction(self):
		pass

	def Close(self):
		if self.curPhaseWindow:
			self.curPhaseWindow.Close()
			self.curPhaseWindow = 0

		if self.newPhaseWindow:
			self.newPhaseWindow.Close()
			self.newPhaseWindow = 0

	def SetWarpPhase(self):
		try:
			newPhaseWindow = self

			self.Close()

			if newPhaseWindow:
				chrSlot = self.GetCharacterSlot()
				net.SendSelectCharacterPacket(chrSlot)

			self.curPhaseWindow = newPhaseWindow

			if self.curPhaseWindow:
				if _IsCustomPortsInstantWarp():
					self.curtain.HideInstantly()
				else:
					self.curtain.FadeIn()
			else:
				app.Exit()
		except:
			import exception
			exception.Abort("networkModule.SetWarpPhase")
