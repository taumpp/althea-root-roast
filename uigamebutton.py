import app
import ui
import player
import net
import skill
import skillraise

class GameButtonWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadWindow("UIScript/GameWindow_Dominant_Orb.py")

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self, filename):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, filename)

		except Exception as msg:
			import dbg
			dbg.TraceError("GameButtonWindow.LoadScript - %s" % (msg))
			app.Abort()
			return False

		try:
			self.gameButtonDict = {
				"STATUS" : self.GetChild("StatusPlusButton"),
				"SKILL" : self.GetChild("SkillPlusButton"),
				"QUEST" : self.GetChild("QuestButton"),
				"HELP" : self.GetChild("HelpButton"),
				"BUILD" : self.GetChild("BuildGuildBuilding"),
				"EXIT_OBSERVER" : self.GetChild("ExitObserver"),
			}

			self.gameButtonDict["EXIT_OBSERVER"].SetEvent(ui.__mem_func__(self.__OnClickExitObserver))

			if app.ENABLE_GEM_SYSTEM:
				posx, posy = self.gameButtonDict["SKILL"].GetGlobalPosition()
				self.gameButtonDict["SKILL"].SetPosition(posx, posy - 25 )

				posx, posy = self.gameButtonDict["BUILD"].GetGlobalPosition()
				self.gameButtonDict["BUILD"].SetPosition(posx, posy - 25 )

				posx, posy = self.gameButtonDict["EXIT_OBSERVER"].GetGlobalPosition()
				self.gameButtonDict["EXIT_OBSERVER"].SetPosition(posx, posy - 25 )

		except Exception as msg:
			import dbg
			dbg.TraceError("GameButtonWindow.LoadScript - %s" % (msg))
			app.Abort()
			return False

		self.__HideAllGameButton()
		self.SetObserverMode(player.IsObserverMode())
		self.r1Dress = None
		self.__ApplyR1Look()
		try:
			import uir1
			uir1.FollowLook(self)
		except Exception:
			pass
		return True

	def __ApplyR1Look(self):
		self.r1Dress = None
		try:
			import uitaskbarr1
			self.r1Dress = uitaskbarr1.CreateGameButtons(self)
		except Exception:
			import dbg
			dbg.TraceError("R1 look of Zvysit status / schopnost could not be loaded, the original look is used.")
			self.r1Dress = None

	def SyncR1Look(self):
		"""Settings switched the look (uir1.LookChanged): the R1 plus buttons dressed or the original ones restored,
		the point counts shown again."""
		import uir1
		wanted = uir1.UseR1()
		dress = getattr(self, "r1Dress", None)
		if wanted and not dress:
			self.__ApplyR1Look()
		elif not wanted and dress:
			self.r1Dress = None
			dress.Restore()
		else:
			return
		try:
			self.CheckGameButton()
		except Exception:
			uir1.TraceFailure("Zvysit status / schopnost (look switch)")

	def Destroy(self):
		try:
			import uir1
			uir1.UnfollowLook(self)
		except Exception:
			pass
		self.r1Dress = None
		for key in self.gameButtonDict:
			self.gameButtonDict[key].SetEvent(0)

		self.gameButtonDict={}

	def SetButtonEvent(self, name, event):
		try:
			self.gameButtonDict[name].SetEvent(event)

		except Exception as msg:
			print("GameButtonWindow.LoadScript - %s" % (msg))
			app.Abort()
			return

	def ShowBuildButton(self):
		self.gameButtonDict["BUILD"].Show()

	def HideBuildButton(self):
		self.gameButtonDict["BUILD"].Hide()

	def CheckGameButton(self):
		if not self.IsShow():
			return

		statusPlusButton=self.gameButtonDict["STATUS"]
		skillPlusButton=self.gameButtonDict["SKILL"]
		helpButton=self.gameButtonDict["HELP"]

		if player.GetStatus(player.STAT) > 0:
			statusPlusButton.Show()
		else:
			statusPlusButton.Hide()

		skillPoints = self.__SpendableSkillPoints()
		if skillPoints > 0:
			skillPlusButton.Show()
		else:
			skillPlusButton.Hide()

		dress = getattr(self, "r1Dress", None)
		if dress:
			dress.Call("SetCounts", player.GetStatus(player.STAT), skillPoints)

		helpButton.Hide()

	def __SpendableSkillPoints(self):
		# Owner 8. 10.: points raise only skills below M; M/G/P need books. Hidden while no skill can take a point.
		try:
			return skillraise.SpendablePoints(player, skill, net)
		except Exception:
			import dbg
			dbg.TraceError("Zvysit schopnost: skill check failed, the free points decide.")
			return max(0, player.GetStatus(player.SKILL_ACTIVE))

	def __OnClickExitObserver(self):
		net.SendChatPacket("/observer_exit")

	def __HideAllGameButton(self):
		for btn in self.gameButtonDict.values():
			btn.Hide()

	def SetObserverMode(self, isEnable):
		if isEnable:
			self.gameButtonDict["EXIT_OBSERVER"].Show()
		else:
			self.gameButtonDict["EXIT_OBSERVER"].Hide()
