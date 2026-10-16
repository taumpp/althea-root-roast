#
# File: uiCaptcha.py
# Date: 2019.11.17
# Author: Owsap
#

import ui
import app
import uiToolTip
import grp
import chat
import net
import uiCommon
import introLogin
import time
import localeInfo
import constInfo

class CaptchaDialog(ui.ScriptWindow):
	CAPTCHA_TIME = 10.0
	TOOLTIP_COLOR = grp.GenerateColor((255.00 / 255), (255.00 / 255), (77.00 / 255), 1.0)
	RANDOM_CAPTCHA = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = False
		self.captchaTime = None
		self.toolTip = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		self.isLoaded = False
		self.captchaTime = None
		self.toolTip = None

	def LoadDialog(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/CaptchaDialog.py")
		except:
			import exception
			exception.Abort("CaptchaDialog.LoadDialog.LoadScript")

		try:
			self.thinboard = self.GetChild("thin_board")
			self.board = self.GetChild("board")
			self.titleBar = self.GetChild("title_bar")
			self.titleName = self.GetChild("title_name")

			self.randomCaptchaName = self.GetChild("random_captcha_name")
			self.randomCaptchaInfo = self.GetChild("random_captcha_info")

			self.captchaTimeImage = self.GetChild("captcha_time_image")
			self.captchaTimeName = self.GetChild("captcha_time_name")
			self.captchaValue = self.GetChild("captcha_value")

			self.acceptButton = self.GetChild("accept_button")
			self.cancelButton = self.GetChild("cancel_button")

		except:
			import exception
			exception.Abort("CaptchaDialog.LoadDialog.BindObject")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.__OnCancelButton))
		self.acceptButton.SetEvent(ui.__mem_func__(self.__OnAcceptButton))
		self.cancelButton.SetEvent(ui.__mem_func__(self.__OnCancelButton))

		self.toolTip = uiToolTip.ToolTip()
		self.popUp = uiCommon.PopupDialog()
		self.popUpTimer = introLogin.ConnectingDialog()

		self.startTime = float(app.GetTime())
		if self.captchaTime is None:
			self.captchaTime = app.GetGlobalTimeStamp() + int(self.CAPTCHA_TIME)

		self.captchaTimeImage.SetCoolTime(self.CAPTCHA_TIME)
		self.captchaTimeImage.SetStartCoolTime(self.startTime)

		self.RandomCaptcha(4)
		self.captchaValue.SetFocus()

		self.isLoaded = True

	def Destroy(self):
		self.ClearDictionary()
		self.Close()

	def Open(self, timeLeft = CAPTCHA_TIME):
		if timeLeft:
			self.CAPTCHA_TIME = timeLeft

		if not self.isLoaded:
			self.LoadDialog()

		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def BindInterface(self, interface):
		self.interface = interface

	def RandomCaptcha(self, max_len):
		captcha = ""

		try:
			for repeat in range(max_len):
				captcha = captcha + self.RANDOM_CAPTCHA[app.GetRandom(-len(self.RANDOM_CAPTCHA), len(self.RANDOM_CAPTCHA))]
		except:
			captcha = "0000"

		self.titleName.SetText("%s : %s" % (localeInfo.CAPTCHA, str(captcha)))
		self.randomCaptchaName.SetText(str(captcha))
		self.randomCaptchaName.SetFontColor((255.00 / 255), (255.00 / 255), (77.00 / 255))

	def Close(self):
		if self.toolTip:
			self.toolTip = None

		self.captchaTime = None
		self.isLoaded = False
		self.Hide()

	def __OnAcceptButton(self):
		self.CheckCaptcha()

	def __OnCancelButton(self):
		if len(self.captchaValue.GetText()) > 0:
			self.captchaValue.SetText("")
		else:
			self.CheckCaptcha()

	def CheckCaptcha(self, timedout = False):
		if self.toolTip:
			self.toolTip.HideToolTip()

		if self.popUp:
			self.popUp.Close()

		if self.popUpTimer:
			self.popUpTimer.Close()

		if timedout == True:
			self.popUpTimer.Open(3.0)
			self.popUpTimer.SetText(localeInfo.CAPTCHA_TIMEOUT)
			self.popUpTimer.SAFE_SetTimeOverEvent(self.ExitGame)
			self.popUpTimer.SAFE_SetExitEvent(self.ExitGame)
		else:
			if len(self.captchaValue.GetText()) <= 0:
				self.popUp.Open()
				self.popUp.SetText(localeInfo.CAPTCHA_EMPTY)
				return

			elif self.captchaValue.GetText() != self.randomCaptchaName.GetText():
				self.popUpTimer.Open(3.0)
				self.popUpTimer.SetText(localeInfo.CAPTCHA_WRONG)
				self.popUpTimer.SAFE_SetTimeOverEvent(self.ExitGame)
				self.popUpTimer.SAFE_SetExitEvent(self.ExitGame)

		if self.interface:
			self.interface.ShowDefaultWindows()

		self.captchaValue.KillFocus()
		self.Close()

	def ExitGame(self):
		self.Destroy()
		net.Disconnect()
		app.Exit()

	def OnUpdate(self):
		if self.captchaTime is None:
			self.captchaTime = app.GetGlobalTimeStamp() + int(self.CAPTCHA_TIME)

		leftTime = max(0, self.captchaTime - app.GetGlobalTimeStamp())
		leftMin, leftSec = divmod(leftTime, 60)

		if leftTime > 0:
			if leftSec <= 5:
				self.captchaTimeName.SetFontColor((255.00 / 255), (0.00 / 255), (0.00 / 255))

			self.captchaTimeName.SetText("%02d:%02d" % (leftMin, leftSec))

			# prevent interface use
			if self.interface:
				self.interface.HideAllWindows()
		else:
			leftTime = None
			self.CheckCaptcha(True)
			self.captchaTimeName.SetText("00:00")

		if self.toolTip:
			if self.randomCaptchaInfo.IsIn():
				self.toolTip.ClearToolTip()
				self.toolTip.AutoAppendTextLine(localeInfo.CAPTCHA_TOOLTIP % (str(leftSec), self.randomCaptchaName.GetText()), self.TOOLTIP_COLOR)
				self.toolTip.AlignHorizonalCenter()
				self.toolTip.ShowToolTip()
			else:
				self.toolTip.HideToolTip()
