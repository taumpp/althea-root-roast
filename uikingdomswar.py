import ui
import grp
import time
import wndMgr
import uiscriptlocale
import osfInfo
import app

class Window(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = 0
		self.timeRemained = 0
		self.LoadObject()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		self.wndBoard = None

	def Show(self):
		self.LoadObject()
		ui.ScriptWindow.Show(self)

	def LoadObject(self):
		if self.isLoaded == 1:
			return

		try:
			self.isLoaded = 1
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/kingdomswar_window.py")
		except:
			import exception
			exception.Abort("Window.LoadObject.LoadObject")

		try:
			self.wndBoard = self.GetChild("board")
			self.ShinsooKills = self.GetChild("ShinsooKills")
			self.ChunjoKills = self.GetChild("ChunjoKills")
			self.JinnoKills = self.GetChild("JinnoKills")
			self.Deaths = self.GetChild("DeathsT")
			self.Clock = self.GetChild("ClockT")
		except:
			import exception
			exception.Abort("Window.LoadObject.BindObject")

	def ShowWindow(self, score1, score2, score3, limitKills, deads, limiDeads, timeRemained):
		self.timeRemained = timeRemained
		if limitKills > 0:
			self.ShinsooKills.SetText(str(score1) + "/" + str(limitKills))
			self.ChunjoKills.SetText(str(score2) + "/" + str(limitKills))
			self.JinnoKills.SetText(str(score3) + "/" + str(limitKills))
		else:
			self.ShinsooKills.SetText(str(score1))
			self.ChunjoKills.SetText(str(score2))
			self.JinnoKills.SetText(str(score3))

		self.Deaths.SetText(str(deads))
		self.SetPosition(10, wndMgr.GetScreenHeight()//2)
		self.SetTop()
		self.Show()

	def RefreshScore(self, score1, score2, score3, limitKills):
		if limitKills > 0:
			self.ShinsooKills.SetText(str(score1) + "/" + str(limitKills))
			self.ChunjoKills.SetText(str(score2) + "/" + str(limitKills))
			self.JinnoKills.SetText(str(score3) + "/" + str(limitKills))
		else:
			self.ShinsooKills.SetText(str(score1))
			self.ChunjoKills.SetText(str(score2))
			self.JinnoKills.SetText(str(score3))

	def RefreshDeads(self, deads, limiDeads):
		self.Deaths.SetText(str(deads))

	def OnUpdate(self):
		if self.timeRemained >= app.GetGlobalTimeStamp():
			self.Clock.SetText(osfInfo.CalculateTime(self.timeRemained-app.GetGlobalTimeStamp()))
