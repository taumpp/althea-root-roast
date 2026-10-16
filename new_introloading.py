import ui
import net
import app
import dbg
import background
import localeInfo
import chrmgr
import colorInfo
import playerSettingModule
import stringCommander
import emotion
import osfInfo
class LoadingWindow(ui.ScriptWindow):
	def __init__(self, stream):
		#print "NEW LOADING WINDOW -------------------------------------------------------------------------------"
		ui.Window.__init__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_LOAD, self)

		self.stream = stream
		self.update = 0
		self.playerX = 0
		self.playerY = 0
		self.loadStepList = []

	def __del__(self):
		#print "---------------------------------------------------------------------------- DELETE LOADING WINDOW"
		net.SetPhaseWindow(net.PHASE_WINDOW_LOAD, 0)
		ui.Window.__del__(self)

	def Open(self):
		self.Show()
		chrSlot = self.stream.GetCharacterSlot()
		net.SendSelectCharacterPacket(chrSlot)

		app.SetFrameSkip(0)

	def Close(self):
		#print "---------------------------------------------------------------------------- CLOSE LOADING WINDOW"

		app.SetFrameSkip(1)

		self.loadStepList = []
		self.ClearDictionary()
		self.Hide()

	def OnPressEscapeKey(self):
		app.SetFrameSkip(0)
		self.stream.SetLoginPhase()
		return True

	def __SetNext(self, next):
		if next:
			self.update = ui.__mem_func__(next)
		else:
			self.update=0

	def LoadData(self, playerX, playerY):
		self.playerX=playerX
		self.playerY=playerY

		self.__RegisterSkill()
		self.__RegisterTitleName()
		if app.ENABLE_GUILD_LEADER_GRADE_NAME:
			self.__RegisterGuildLeaderGradeName()
		self.__RegisterColor()
		self.__RegisterEmotionIcon()

		self.loadStepList = [
			(30, ui.__mem_func__(self.__LoadSkill)),
			(60, ui.__mem_func__(self.__LoadGuildBuilding)),
			(90, ui.__mem_func__(self.__LoadRaceHeight)),
			(100, ui.__mem_func__(self.__StartGame)),
		]

	def OnUpdate(self):
		if len(self.loadStepList) > 0:
			(progress, runFunc) = self.loadStepList[0]

			try:
				runFunc()
			except:
				self.errMsg.Show()
				self.loadStepList=[]

				dbg.TraceError(" !!! Failed to load game data : STEP [%d]" % (progress))
				app.Exit()

				return

			self.loadStepList.pop(0)

	def __RegisterSkill(self):
		race = net.GetMainActorRace()
		group = net.GetMainActorSkillGroup()
		empire = net.GetMainActorEmpire()

		playerSettingModule.RegisterSkill(race, group, empire)

	if app.ENABLE_GENDER_ALIGNMENT:
		def __RegisterTitleName(self):
			def GetTitleData(gender):
				return localeInfo.TITLE_NAME_DICT.get(gender, ('UNKNOWN_GENDER', ))

			def GetTitleNamesTuple(*title_data):
				# py3: the py2 map(iter)/StopIteration generator idiom is exactly zip semantics
				return zip(*title_data)

			for titleNameIndex, (titleNameFemale, titleNameMale) in enumerate(GetTitleNamesTuple(GetTitleData(localeInfo.GENDER_FEMALE), GetTitleData(localeInfo.GENDER_MALE))):
				chrmgr.RegisterTitleName(titleNameIndex, titleNameFemale, titleNameMale)
	else:
		def __RegisterTitleName(self):
			for i in range(len(localeInfo.TITLE_NAME_LIST)):
				chrmgr.RegisterTitleName(i, localeInfo.TITLE_NAME_LIST[i])

	if app.ENABLE_GUILD_LEADER_GRADE_NAME:
		def __RegisterGuildLeaderGradeName(self):
			for i in range(len(localeInfo.GUILD_LEADER_GRADE_NAME_LIST)):
				chrmgr.RegisterGuildLeaderGradeName(i, localeInfo.GUILD_LEADER_GRADE_NAME_LIST[i])

	def __RegisterColor(self):
		## Name
		NAME_COLOR_DICT = {
			chrmgr.NAMECOLOR_PC : colorInfo.CHR_NAME_RGB_PC,
			chrmgr.NAMECOLOR_NPC : colorInfo.CHR_NAME_RGB_NPC,
			chrmgr.NAMECOLOR_MOB : colorInfo.CHR_NAME_RGB_MOB,
			chrmgr.NAMECOLOR_PVP : colorInfo.CHR_NAME_RGB_PVP,
			chrmgr.NAMECOLOR_PK : colorInfo.CHR_NAME_RGB_PK,
			chrmgr.NAMECOLOR_PARTY : colorInfo.CHR_NAME_RGB_PARTY,
			chrmgr.NAMECOLOR_WARP : colorInfo.CHR_NAME_RGB_WARP,
			chrmgr.NAMECOLOR_WAYPOINT : colorInfo.CHR_NAME_RGB_WAYPOINT,
			#chrmgr.NAMECOLOR_TARGET_VICTIM : colorInfo.CHR_NAME_RGB_TARGET_VICTIM,

			chrmgr.NAMECOLOR_EMPIRE_MOB : colorInfo.CHR_NAME_RGB_EMPIRE_MOB,
			chrmgr.NAMECOLOR_EMPIRE_NPC : colorInfo.CHR_NAME_RGB_EMPIRE_NPC,
			chrmgr.NAMECOLOR_EMPIRE_PC+1 : colorInfo.CHR_NAME_RGB_EMPIRE_PC_A,
			chrmgr.NAMECOLOR_EMPIRE_PC+2 : colorInfo.CHR_NAME_RGB_EMPIRE_PC_B,
			chrmgr.NAMECOLOR_EMPIRE_PC+3 : colorInfo.CHR_NAME_RGB_EMPIRE_PC_C,
		}

		NAME_COLOR_DICT.update({chrmgr.NAMECOLOR_OFFLINE_SHOP : colorInfo.CHR_NAME_RGB_OFFLINE_SHOP,})

		if app.ENABLE_ATLAS_ICON_RENEWAL:
			NAME_COLOR_DICT[chrmgr.NAMECOLOR_METIN] = colorInfo.CHR_NAME_RGB_METIN
			NAME_COLOR_DICT[chrmgr.NAMECOLOR_BOSS] = colorInfo.CHR_NAME_RGB_BOSS

		for name, rgb in NAME_COLOR_DICT.items():
			chrmgr.RegisterNameColor(name, rgb[0], rgb[1], rgb[2])

		## Title
		TITLE_COLOR_DICT = (
			colorInfo.TITLE_RGB_GOOD_4,
			colorInfo.TITLE_RGB_GOOD_3,
			colorInfo.TITLE_RGB_GOOD_2,
			colorInfo.TITLE_RGB_GOOD_1,
			colorInfo.TITLE_RGB_NORMAL,
			colorInfo.TITLE_RGB_EVIL_1,
			colorInfo.TITLE_RGB_EVIL_2,
			colorInfo.TITLE_RGB_EVIL_3,
			colorInfo.TITLE_RGB_EVIL_4,
		)
		count = 0
		for rgb in TITLE_COLOR_DICT:
			chrmgr.RegisterTitleColor(count, rgb[0], rgb[1], rgb[2])
			count += 1

	def __RegisterEmotionIcon(self):
		emotion.RegisterEmotionIcons()

	def __LoadSkill(self):
		playerSettingModule.LoadGameData("SKILL")

	def __LoadGuildBuilding(self):
		playerSettingModule.LoadGuildBuildingList(localeInfo.GUILD_BUILDING_LIST_TXT)

	def __LoadRaceHeight(self):
		playerSettingModule.LoadGameData("RACE_HEIGHT")

	def __StartGame(self):
		background.SetViewDistanceSet(background.DISTANCE0, 25600)
		background.SelectViewDistanceNum(background.DISTANCE0)

		app.SetGlobalCenterPosition(self.playerX, self.playerY)

		net.StartGame()
