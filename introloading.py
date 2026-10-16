import ui
import uiScriptLocale
import net
import app
import dbg
import player
import background
import wndMgr

import localeInfo
import chrmgr
import colorInfo
import constInfo
import osfInfo
import loadingprogress
import introbackground

import playerSettingModule
import stringCommander
import emotion

####################################
# 빠른 실행을 위한 모듈 로딩 분담
####################################
import uiRefine
import uiToolTip
import uiAttachMetin
import uiPickMoney
import uiChat
import uiMessenger
import uiHelp
import uiWhisper
import uiPointReset
import uiShop
import uiExchange
import uiSystem
import uiOption
import uiRestart
####################################

IsLoaded = False


def _CreateLoadingArtwork(parent, backgroundImage=None):
	image = backgroundImage or ui.ExpandedImageBox()
	if backgroundImage is None:
		image.SetParent(parent)
	image.AddFlag("not_pick")
	# This artwork owns its cover transform, including legacy UIScript images.
	resizeDic = getattr(image, "resizeDic", None)
	if resizeDic is not None:
		for key in ("scale", "position", "size", "rect"):
			resizeDic.pop(key, None)
	logo = ui.ExpandedImageBox()
	logo.SetParent(parent)
	logo.AddFlag("not_pick")
	width, height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
	parent.SetSize(width, height)
	introbackground.apply_background(image, width, height)
	introbackground.apply_spec(logo, introbackground.get_logo_spec(width, height))
	parent.artworkSize = (width, height)
	image.Show()
	logo.Show()
	return image, logo


def _RefreshLoadingArtwork(window):
	size = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
	if size == window.artworkSize or not window.loadingImage:
		return
	# A failed decorative texture must never block legacy loading steps or
	# retry every frame. A later resolution change allows one new attempt.
	window.artworkSize = size
	try:
		window.SetSize(*size)
		introbackground.apply_background(window.loadingImage, *size)
		if window.loadingLogo:
			introbackground.apply_spec(window.loadingLogo, introbackground.get_logo_spec(*size))
	except Exception:
		dbg.TraceError("LoadingWindow - artwork resize failed")

if app.ENABLE_LOADING_PERFORMANCE:
	class NewLoadingWindow(ui.ScriptWindow):
		def __init__(self, stream, silent=False):
			ui.ScriptWindow.__init__(self)
			self.stream = stream
			self.silent = bool(silent)
			self.loadingImage = None
			self.loadingLogo = None
			self.artworkSize = None
			self.progressTrack = None
			self.progressFill = None
			self.progressModel = loadingprogress.LoadingProgressModel()
			net.SendSelectCharacterPacket(self.stream.GetCharacterSlot())

		def __del__(self):
			ui.ScriptWindow.__del__(self)

		def Open(self):

			# Reset all
			osfInfo.AUTOPICKUP_ENABLED = False
			osfInfo.DS_SET_ENABLED = False

			if app.ENABLE_OFFLINE_SHOP:
				osfInfo.SHOP_SKIN_VALUE = 0
				osfInfo.SHOP_BANNER_VALUE = 0
				osfInfo.SHOP_SKIN_UNLOCKED = {
					0 : False,
					1 : False,
					2 : False,
					3 : False,
					4 : False,
					5 : False,
					6 : False,
					7 : False,
				}
				osfInfo.SHOP_BANNER_UNLOCKED = {
					0 : False,
					1 : False,
					2 : False,
					3 : False,
					4 : False,
				}

				osfInfo.SHOP_SKIN_TIME = {
					0 : 0,
					1 : 0,
					2 : 0,
					3 : 0,
					4 : 0,
					5 : 0,
					6 : 0,
					7 : 0,
				}
				osfInfo.SHOP_BANNER_TIME = {
					0 : 0,
					1 : 0,
					2 : 0,
					3 : 0,
					4 : 0,
				}

				osfInfo.SHOP_VID = {}
				osfInfo.SHOPNAMES_RANGE = 4000
				osfInfo.IS_OFFLINE_SHOP_DECORATION = False
				osfInfo.OFFLINE_SHOP_DECORATION_UPDATE = False

			if app.ENABLE_HIDE_COSTUME_SYSTEM:
				osfInfo.HIDDEN_BODY_COSTUME = 0
				osfInfo.HIDDEN_HAIR_COSTUME = 0
				if app.ENABLE_ACCE_COSTUME_SYSTEM:
					osfInfo.HIDDEN_ACCE_COSTUME = 0
				if app.ENABLE_WEAPON_COSTUME_SYSTEM:
					osfInfo.HIDDEN_WEAPON_COSTUME = 0
				if app.ENABLE_AURA_SYSTEM:
					osfInfo.HIDDEN_AURA_COSTUME = 0
				if app.ENABLE_ACCE_SKIN_SYSTEM:
					osfInfo.HIDDEN_ACCE_SKIN = 0
				if app.ENABLE_SPECIAL_SHINING_SYSTEM:
					osfInfo.HIDDEN_SHINING_WEAPON = 0
					osfInfo.HIDDEN_SHINING_ARMOR = 0
			# Reset all

			if not self.silent:
				try:
					self.loadingImage, self.loadingLogo = _CreateLoadingArtwork(self)
					_RefreshLoadingArtwork(self)
				except:
					dbg.TraceError("NewLoadingWindow.Open - background asset load failed")

				self.__CreateProgressBar()

				self.Show()
			app.SetFrameSkip(0)

		def __CreateProgressBar(self):
			try:
				track = ui.ExpandedImageBox()
				track.SetParent(self)
				track.LoadImage(uiScriptLocale.LOCALE_UISCRIPT_PATH + "loading/progress_track_320x8.png")

				fill = ui.ExpandedImageBox()
				fill.SetParent(self)
				fill.LoadImage(uiScriptLocale.LOCALE_UISCRIPT_PATH + "loading/progress_fill_318x6.png")

				trackX = max(0, (wndMgr.GetScreenWidth() - 320) // 2)
				trackY = max(0, wndMgr.GetScreenHeight() - 69)
				track.SetPosition(trackX, trackY)
				fill.SetPosition(trackX + 1, trackY + 1)
				fill.SetPercentage(0, 100)
				track.Show()
				fill.Show()

				self.progressTrack = track
				self.progressFill = fill
			except:
				dbg.TraceError("NewLoadingWindow.__CreateProgressBar - asset load failed")
				self.progressTrack = None
				self.progressFill = None

		def OnUpdate(self):
			if self.silent or not self.progressModel:
				return

			previousSize = self.artworkSize
			_RefreshLoadingArtwork(self)
			if self.artworkSize != previousSize and self.progressTrack and self.progressFill:
				trackX = max(0, (wndMgr.GetScreenWidth() - 320) // 2)
				trackY = max(0, wndMgr.GetScreenHeight() - 69)
				self.progressTrack.SetPosition(trackX, trackY)
				self.progressFill.SetPosition(trackX + 1, trackY + 1)

			nativeValue = None
			getter = getattr(net, "GetLoadingProgress", None)
			if getter:
				try:
					nativeValue = getter()
				except:
					nativeValue = None

			value = self.progressModel.Step(nativeValue, app.GetTime())
			if self.progressFill:
				self.progressFill.SetPercentage(value, 100)

		def Close(self):
			app.SetFrameSkip(1)

			self.loadingImage = None
			self.loadingLogo = None
			self.artworkSize = None
			self.progressTrack = None
			self.progressFill = None
			self.progressModel = None

			self.ClearDictionary()
			self.Hide()

		def OnPressEscapeKey(self):
			if self.silent:
				return True
			self.stream.SetLoginPhase()
			return True

class LoadingWindow(ui.ScriptWindow):
	def __init__(self, stream):
		#print "NEW LOADING WINDOW -------------------------------------------------------------------------------"
		ui.Window.__init__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_LOAD, self)

		self.stream = stream
		self.loadingImage = 0
		self.loadingLogo = None
		self.artworkSize = None
		self.loadingGage = 0
		self.errMsg = 0
		self.update = 0
		self.playerX = 0
		self.playerY = 0
		self.loadStepList = []

	def __del__(self):
		#print "---------------------------------------------------------------------------- DELETE LOADING WINDOW"
		net.SetPhaseWindow(net.PHASE_WINDOW_LOAD, 0)
		ui.Window.__del__(self)

	def Open(self):
		#print "OPEN LOADING WINDOW -------------------------------------------------------------------------------"

		#app.HideCursor()

		if app.ENABLE_OFFLINE_SHOP:
			osfInfo.SHOP_SKIN_VALUE = 0
			osfInfo.SHOP_BANNER_VALUE = 0
			osfInfo.SHOP_SKIN_UNLOCKED = {
				0 : False,
				1 : False,
				2 : False,
				3 : False,
				4 : False,
				5 : False,
				6 : False,
				7 : False,
			}
			osfInfo.SHOP_BANNER_UNLOCKED = {
				0 : False,
				1 : False,
				2 : False,
				3 : False,
				4 : False,
			}

			osfInfo.SHOP_SKIN_TIME = {
				0 : 0,
				1 : 0,
				2 : 0,
				3 : 0,
				4 : 0,
				5 : 0,
				6 : 0,
				7 : 0,
			}
			osfInfo.SHOP_BANNER_TIME = {
				0 : 0,
				1 : 0,
				2 : 0,
				3 : 0,
				4 : 0,
			}

			osfInfo.SHOP_VID = {}
			osfInfo.SHOPNAMES_RANGE = 4000
			osfInfo.IS_OFFLINE_SHOP_DECORATION = False
			osfInfo.OFFLINE_SHOP_DECORATION_UPDATE = False

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/LoadingWindow.py")
		except:
			import exception
			exception.Abort("LodingWindow.Open - LoadScriptFile Error")

		try:
			self.loadingImage = self.GetChild("BackGround")
			self.errMsg = self.GetChild("ErrorMessage")
			self.loadingGage = self.GetChild("FullGage")
			if app.ENABLE_LOADING_TIP:
				self.loadingTipBackground = self.GetChild("TipBackground")
				self.loadingTip = self.GetChild("LoadingTip")

				if osfInfo.SHOW_LOADING_PROGRESS == True:
					loadingTipProgress = ui.TextLine()
					loadingTipProgress.SetParent(self.loadingTip)
					loadingTipProgress.SetPosition(0, 25)
					loadingTipProgress.Show()
					self.loadingTipProgress = loadingTipProgress

		except:
			import exception
			exception.Abort("LodingWindow.Open - LoadScriptFile Error")

		self.errMsg.Hide()

		try:
			self.loadingImage, self.loadingLogo = _CreateLoadingArtwork(self, self.loadingImage)
			_RefreshLoadingArtwork(self)
		except:
			dbg.TraceError("LoadingWindow.Open - background asset load failed")
			self.loadingImage.Hide()

		self.loadingGage.SetPercentage(2, 100)

		if app.ENABLE_LOADING_TIP:
			self.loadingTip.SetText(player.GetLoadingTip())

		self.Show()

		chrSlot = self.stream.GetCharacterSlot()
		net.SendSelectCharacterPacket(chrSlot)

		app.SetFrameSkip(0)

	def Close(self):
		#print "---------------------------------------------------------------------------- CLOSE LOADING WINDOW"

		app.SetFrameSkip(1)

		self.loadStepList = []
		self.loadingImage = 0
		self.loadingLogo = None
		self.artworkSize = None
		self.loadingGage = 0
		self.errMsg = 0
		self.ClearDictionary()
		self.Hide()

	def OnPressEscapeKey(self):
		app.SetFrameSkip(1)
		self.stream.SetLoginPhase()
		return True

	def __SetNext(self, next):
		if next:
			self.update = ui.__mem_func__(next)
		else:
			self.update=0

	def __SetProgress(self, p):
		if self.loadingGage:
			if osfInfo.EXTENDED_LOADING_GUAGE:
				self.loadingGage.SetPercentage(p, 160)
			else:
				self.loadingGage.SetPercentage(2+98*p//100, 100)

	def DEBUG_LoadData(self, playerX, playerY):
		self.playerX=playerX
		self.playerY=playerY

		self.__RegisterSkill() ## 로딩 중간에 실행 하면 문제 발생
		self.__RegisterTitleName()
		if app.ENABLE_GUILD_LEADER_GRADE_NAME:
			self.__RegisterGuildLeaderGradeName()
		self.__RegisterColor()
		self.__InitData()
		# self.__LoadMap()
		self.__LoadSound()
		self.__LoadEffect()
		self.__LoadWarrior()
		self.__LoadAssassin()
		self.__LoadSura()
		self.__LoadShaman()
		self.__LoadWolfman()
		self.__LoadSkill()
		self.__LoadEnemy()
		self.__LoadNPC()
		self.__LoadRaceHeight()
		self.__StartGame()

	def LoadData(self, playerX, playerY):
		self.playerX=playerX
		self.playerY=playerY

		self.__RegisterDungeonMapName()
		self.__RegisterSkill() ## 로딩 중간에 실행 하면 문제 발생
		self.__RegisterTitleName()
		if app.ENABLE_GUILD_LEADER_GRADE_NAME:
			self.__RegisterGuildLeaderGradeName()
		self.__RegisterColor()
		self.__RegisterEmotionIcon()

		self.loadStepList = [
			(0, ui.__mem_func__(self.__InitData)),
			# (10, ui.__mem_func__(self.__LoadMap)),
			(30, ui.__mem_func__(self.__LoadSound)),
			(40, ui.__mem_func__(self.__LoadEffect)),
			(50, ui.__mem_func__(self.__LoadWarrior)),
			(60, ui.__mem_func__(self.__LoadAssassin)),
			(70, ui.__mem_func__(self.__LoadSura)),
			(80, ui.__mem_func__(self.__LoadShaman)),
			(85, ui.__mem_func__(self.__LoadWolfman)),
			(90, ui.__mem_func__(self.__LoadSkill)),
			(93, ui.__mem_func__(self.__LoadEnemy)),
			(97, ui.__mem_func__(self.__LoadNPC)),

			# GUILD_BUILDING
			(98, ui.__mem_func__(self.__LoadGuildBuilding)),
			# END_OF_GUILD_BUILDING

			# RACE HEIGHT
			(99, ui.__mem_func__(self.__LoadRaceHeight)),
			# END_OF_RACE_HEIGHT

			(100, ui.__mem_func__(self.__StartGame)),
		]

		if osfInfo.EXTENDED_LOADING_GUAGE:
			global IsLoaded
			if not IsLoaded:
				tmpLoadStepList = tuple(zip(*self.loadStepList))[0]
				for progress in set(range(tmpLoadStepList[0], tmpLoadStepList[-1] + 1)).difference(tmpLoadStepList):
					self.loadStepList.append((progress, lambda: None))
				self.loadStepList.sort(key=lambda step: step[0])
				IsLoaded = True

		self.__SetProgress(0)
		# self.__SetNext(self.__LoadMap)

	def OnUpdate(self):
		_RefreshLoadingArtwork(self)
		if len(self.loadStepList) > 0:
			(progress, runFunc) = self.loadStepList[0]

			try:
				if app.ENABLE_LOADING_TIP and app.WJ_MULTI_TEXTLINE:
					if osfInfo.SHOW_LOADING_PROGRESS == True:
						self.loadingTipProgress.SetText("Loading %s%%" % progress)

				runFunc()
			except:
				self.errMsg.Show()
				self.loadStepList=[]

				## 이곳에서 syserr.txt 를 보낸다.

				import dbg
				dbg.TraceError(" !!! Failed to load game data : STEP [%d]" % (progress))

				#import shutil
				#import os
				#shutil.copyfile("syserr.txt", "errorlog.txt")
				#os.system("errorlog.exe")

				app.Exit()

				return

			self.loadStepList.pop(0)

			self.__SetProgress(progress)

	def __InitData(self):
		playerSettingModule.LoadGameData("INIT")

	def __RegisterDungeonMapName(self):
		background.RegisterDungeonMapName("metin2_map_spiderdungeon")
		background.RegisterDungeonMapName("metin2_map_monkeydungeon")
		background.RegisterDungeonMapName("metin2_map_monkeydungeon_02")
		background.RegisterDungeonMapName("metin2_map_monkeydungeon_03")
		background.RegisterDungeonMapName("metin2_map_deviltower1")

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
				# py3: the old hand-rolled izip (map(iter)+map(next) in a while loop)
				# would raise RuntimeError under PEP 479; zip() is the exact equivalent
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

	# def __LoadMap(self):
		# net.Warp(self.playerX, self.playerY)

	def __LoadSound(self):
		playerSettingModule.LoadGameData("SOUND")

	def __LoadEffect(self):
		playerSettingModule.LoadGameData("EFFECT")

	def __LoadWarrior(self):
		playerSettingModule.LoadGameData("WARRIOR")

	def __LoadAssassin(self):
		playerSettingModule.LoadGameData("ASSASSIN")

	def __LoadSura(self):
		playerSettingModule.LoadGameData("SURA")

	def __LoadShaman(self):
		playerSettingModule.LoadGameData("SHAMAN")

	def __LoadWolfman(self):
		playerSettingModule.LoadGameData("WOLFMAN")

	def __LoadSkill(self):
		playerSettingModule.LoadGameData("SKILL")

	def __LoadEnemy(self):
		playerSettingModule.LoadGameData("ENEMY")

	def __LoadNPC(self):
		playerSettingModule.LoadGameData("NPC")

	# GUILD_BUILDING
	def __LoadGuildBuilding(self):
		playerSettingModule.LoadGuildBuildingList(localeInfo.GUILD_BUILDING_LIST_TXT)
	# END_OF_GUILD_BUILDING

	def __LoadRaceHeight(self):
		playerSettingModule.LoadGameData("RACE_HEIGHT")

	def __StartGame(self):
		background.SetViewDistanceSet(background.DISTANCE0, 25600)
		"""
		background.SetViewDistanceSet(background.DISTANCE1, 19200)
		background.SetViewDistanceSet(background.DISTANCE2, 12800)
		background.SetViewDistanceSet(background.DISTANCE3, 9600)
		background.SetViewDistanceSet(background.DISTANCE4, 6400)
		"""
		background.SelectViewDistanceNum(background.DISTANCE0)

		app.SetGlobalCenterPosition(self.playerX, self.playerY)

		net.StartGame()
