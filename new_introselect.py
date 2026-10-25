import chr
import grp
import app
import wndMgr
import net
import snd
import musicInfo
import event
import systemSetting
import localeInfo
import namepolicy
import math
import re

import ui
import introbackground
import uiToolTip
import uiScriptLocale
import networkModule
import playerSettingModule

####################################
# 빠른 실행을 위한 모듈 로딩 분담
####################################
import uiCommon
import uiMapNameShower
import uiAffectShower
import uiPlayerGauge
import uiCharacter
import uiTarget
import consoleModule
import interfaceModule
import uiTaskBar
import uiInventory

import osfInfo
###################################

ENABLE_ENGNUM_DELETE_CODE = False

if app.ENABLE_PET_MOUNT_COSTUME_CREATE:
	import player

if localeInfo.IsNEWCIBN() or localeInfo.IsCIBN10():
	ENABLE_ENGNUM_DELETE_CODE = True
elif localeInfo.IsEUROPE():
	ENABLE_ENGNUM_DELETE_CODE = True

M2_INIT_VALUE = -1

if app.ENABLE_PLAYER_PER_ACCOUNT5:
	CHARACTER_SLOT_COUNT_MAX = 5
else:
	CHARACTER_SLOT_COUNT_MAX = 4

JOB_WARRIOR = 0
JOB_ASSASSIN = 1
JOB_SURA = 2
JOB_SHAMAN = 3
JOB_WOLFMAN = 4

if app.ENABLE_CONQUEROR_LEVEL:
	ORIGEN_STAT = 0
	SUNGMA_STAT = 1

class MyCharacters:
	class MyUnit:
		def __init__(self, const_id, name, level, race, playtime, guildname, form, hair, acce, stat_str, stat_dex, stat_hth, stat_int, change_name):
			self.UnitDataDic = {
				"ID" : const_id,
				"NAME" : name,
				"LEVEL" : level,
				"RACE" : race,
				"PLAYTIME" : playtime,
				"GUILDNAME" : guildname,
				"FORM" : form,
				"HAIR" : hair,
				"ACCE" : acce,
				"STR" : stat_str,
				"DEX" : stat_dex,
				"HTH" : stat_hth,
				"INT" : stat_int,
				"CHANGENAME" : change_name,
			}

		def __del__(self):
			#print self.UnitDataDic["NAME"]
			self.UnitDataDic = None

		def GetUnitData(self):
			return self.UnitDataDic

		if app.ENABLE_CONQUEROR_LEVEL:
			def SetStatSungmaPoints(self, level, str, hp, move, immune):
				self.UnitDataDic.update({
					"CONQUEROR_LEVEL" : level,
					"SUNGMA_STR" : str,
					"SUNGMA_HP" : hp,
					"SUNGMA_MOVE" : move,
					"SUNGMA_IMMUNE" : immune
				})

	def __init__(self, stream):
		self.MainStream = stream
		self.PriorityData = []
		self.myUnitDic = {}
		self.HowManyChar = 0
		self.EmptySlot = []
		self.Race = [None, None, None, None, None]
		self.Job = [None, None, None, None, None]
		self.Guild_Name = [None, None, None, None, None]
		self.Hair = [0, 0, 0, 0, 0]
		self.Play_Time = [None, None, None, None, None]
		self.Change_Name= [None, None, None, None, None]
		self.Display_Data = {}
		self.Stat_Point = { 0 : None, 1 : None, 2 : None, 3 : None, 4 : None }
		if app.ENABLE_CONQUEROR_LEVEL:
			self.Sungma_Stat_Point = { 0 : None, 1 : None, 2 : None, 3 : None, 4 : None }

	def __del__(self):
		self.MainStream = None

		for i in range(self.HowManyChar):
			chr.DeleteInstance(i)

		self.PriorityData = None
		self.myUnitDic = None
		self.HowManyChar = None
		self.EmptySlot = None
		self.Race = None
		self.Job = None
		self.Guild_Name = None
		self.Hair = None
		self.Play_Time = None
		self.Change_Name = None
		self.Display_Data = None
		self.Stat_Point = None
		if app.ENABLE_CONQUEROR_LEVEL:
			self.Sungma_Stat_Point = None

	def LoadCharacterData(self):
		self.RefreshData()
		self.MainStream.All_ButtonInfoHide()
		for i in range(CHARACTER_SLOT_COUNT_MAX):
			pid = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_ID) 

			if not pid :
				self.EmptySlot.append(i)
				continue

			name = net.GetAccountCharacterSlotDataString(i, net.ACCOUNT_CHARACTER_SLOT_NAME)
			level = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_LEVEL)
			race = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_RACE)
			playtime = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_PLAYTIME)
			guildname = net.GetAccountCharacterSlotDataString(i, net.ACCOUNT_CHARACTER_SLOT_GUILD_NAME)
			form = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_FORM)
			hair = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_HAIR)
			stat_str = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_STR)
			stat_dex = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_DEX)
			stat_hth = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_HTH)
			stat_int = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_INT)
			last_playtime = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_LAST_PLAYTIME)
			change_name = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_CHANGE_NAME_FLAG)
			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				acce = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_ACCE)
			else:
				acce = 0

			if app.ENABLE_CONQUEROR_LEVEL:
				conqueror_level = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_CONQUEROR_LEVEL)
				sungma_stat_str = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_SUNGMA_STR)
				sungma_stat_hp = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_SUNGMA_HP)
				sungma_stat_move = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_SUNGMA_MOVE)
				sungma_stat_immune = net.GetAccountCharacterSlotDataInteger(i, net.ACCOUNT_CHARACTER_SLOT_SUNGMA_IMMUNE)

			self.SetPriorityData(last_playtime, i)

			self.myUnitDic[i] = self.MyUnit(i, name, level, race, playtime, guildname, form, hair, acce, stat_str, stat_dex, stat_hth, stat_int, change_name)
			if app.ENABLE_CONQUEROR_LEVEL:
				self.myUnitDic[i].SetStatSungmaPoints(conqueror_level, sungma_stat_str, sungma_stat_hp, sungma_stat_move, sungma_stat_immune)

		self.PriorityData.sort(reverse = True)

		for i in range(len(self.PriorityData)):
			time, index = self.PriorityData[i]
			DestDataDic = self.myUnitDic[index].GetUnitData()

			self.SetSortingData(i, DestDataDic)
			self.MakeCharacter(i, DestDataDic["NAME"], DestDataDic["RACE"], DestDataDic["FORM"], DestDataDic["HAIR"], DestDataDic["ACCE"])

			if app.ENABLE_CONQUEROR_LEVEL:
				self.MainStream.InitDataSet(i, DestDataDic["NAME"], DestDataDic["LEVEL"], DestDataDic["CONQUEROR_LEVEL"], DestDataDic["ID"])
			else:
				self.MainStream.InitDataSet(i, DestDataDic["NAME"], DestDataDic["LEVEL"], DestDataDic["ID"])

		## Default Setting ##
		if self.HowManyChar:
			self.MainStream.SelectButton(0)

		return self.HowManyChar;

	def SetPriorityData(self, last_playtime, index):
		self.PriorityData.append([last_playtime, index])

	def MakeCharacter(self, slot, name, race, form, hair, acce):
		chr.CreateInstance(slot)
		chr.SelectInstance(slot)
		chr.SetVirtualID(slot)
		chr.SetNameString(name)

		chr.SetRace(race)
		chr.SetArmor(form)
		chr.SetHair(hair)
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			chr.SetAcce(acce)

		chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
		chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)

		## 수인족만, 스케일 조금 축소.
		if not app.DISABLE_WOLFMAN_CREATION:
			if chr.RaceToJob(race) == JOB_WOLFMAN:
				chr.SetScale(0.95,0.95,0.95)

		chr.SetRotation(0.0)
		chr.Hide()

	def SetSortingData(self, slot, pDataDic):
		self.HowManyChar += 1

		self.Race[slot] = pDataDic["RACE"]
		self.Job[slot] = chr.RaceToJob(pDataDic["RACE"])
		self.Guild_Name[slot] = pDataDic["GUILDNAME"]
		self.Hair[slot] = pDataDic["HAIR"]
		self.Play_Time[slot] = pDataDic["PLAYTIME"]
		self.Change_Name[slot] = pDataDic["CHANGENAME"]
		if not hasattr(self, "Display_Data") or self.Display_Data is None:
			self.Display_Data = {}
		self.Display_Data[slot] = dict(pDataDic)
		self.Stat_Point[slot] = [pDataDic["HTH"], pDataDic["INT"], pDataDic["STR"], pDataDic["DEX"]]
		if app.ENABLE_CONQUEROR_LEVEL:
			self.Sungma_Stat_Point[slot] = [pDataDic["SUNGMA_STR"], pDataDic["SUNGMA_HP"], pDataDic["SUNGMA_MOVE"], pDataDic["SUNGMA_IMMUNE"]]

	def GetRace(self, slot):
		return self.Race[slot]

	def GetHair(self, slot):
		return self.Hair[slot]

	def GetJob(self, slot):
		return self.Job[slot]

	def GetMyCharacterCount(self):
		return self.HowManyChar

	def GetEmptySlot(self, index=0):
		if index < 0 or index >= len(self.EmptySlot):
			return M2_INIT_VALUE

		return self.EmptySlot[index]

	def GetStatPoint(self, slot):
		return self.Stat_Point[slot]

	def GetDisplayData(self, slot):
		if slot < 0 or slot >= CHARACTER_SLOT_COUNT_MAX:
			return None
		return self.Display_Data.get(slot)

	if app.ENABLE_CONQUEROR_LEVEL:
		def GetStatSungmaPoint(self, slot):
			return self.Sungma_Stat_Point[slot]

	def GetGuildNamePlayTime(self, slot):
		return self.Guild_Name[slot], self.Play_Time[slot]

	def GetChangeName(self, slot):
		return self.Change_Name[slot]

	def SetChangeNameSuccess(self, slot, name=None):
		self.Change_Name[slot] = 0
		if name is not None and slot in self.Display_Data:
			self.Display_Data[slot]["NAME"] = name

	def RefreshData(self):
		self.HowManyChar = 0
		self.EmptySlot = []
		self.PriorityData = []
		self.Race = [None, None, None, None, None]
		self.Guild_Name = [None, None, None, None, None]
		self.Hair = [0, 0, 0, 0, 0]
		self.Play_Time = [None, None, None, None, None]
		self.Change_Name= [None, None, None, None, None]
		self.Display_Data = {}
		self.Stat_Point = { 0 : None, 1 : None, 2 : None, 3 : None, 4 : None }
		if app.ENABLE_CONQUEROR_LEVEL:
			self.Sungma_Stat_Point = { 0 : None, 1 : None, 2 : None, 3 : None, 4 : None }

# the hall's tuning keys (DIK codes -> uipregamehall.Hall methods), active only with devkeys=1 in pregame-hall.cfg
HALL_DEV_KEYS = {35: "ToggleUI", 68: "ToggleUI", 62: "CycleOther", 63: "Rebuild", 64: "CycleRig", 65: "CycleLayout",
	67: "CycleDetail", 87: "StrikeNow"}
HALL_MUSIC_KEY = 66  # F8 (owner 11. 10., temporary): the next music track, for everyone (not only devkeys)

class SelectCharacterWindow(ui.Window):
	if not app.DISABLE_WOLFMAN_CREATION:
		RACE_FACE_PATH = {
			playerSettingModule.RACE_WARRIOR_M : "D:/ymir work/ui/intro/public_intro/face/face_warrior_m_0",
			playerSettingModule.RACE_ASSASSIN_W : "D:/ymir work/ui/intro/public_intro/face/face_assassin_w_0",
			playerSettingModule.RACE_SURA_M : "D:/ymir work/ui/intro/public_intro/face/face_sura_m_0",
			playerSettingModule.RACE_SHAMAN_W : "D:/ymir work/ui/intro/public_intro/face/face_shaman_w_0",
			playerSettingModule.RACE_WARRIOR_W : "D:/ymir work/ui/intro/public_intro/face/face_warrior_w_0",
			playerSettingModule.RACE_ASSASSIN_M : "D:/ymir work/ui/intro/public_intro/face/face_assassin_m_0",
			playerSettingModule.RACE_SURA_W : "D:/ymir work/ui/intro/public_intro/face/face_sura_w_0",
			playerSettingModule.RACE_SHAMAN_M : "D:/ymir work/ui/intro/public_intro/face/face_shaman_m_0",
			playerSettingModule.RACE_WOLFMAN_M : "D:/ymir work/ui/intro/public_intro/face/face_wolfman_m_0",
		}
		DISC_FACE_PATH = {
			playerSettingModule.RACE_WARRIOR_M :"icon/face/warrior_m.tga",
			playerSettingModule.RACE_ASSASSIN_W :"icon/face/assassin_w.tga",
			playerSettingModule.RACE_SURA_M :"icon/face/sura_m.tga",
			playerSettingModule.RACE_SHAMAN_W :"icon/face/shaman_w.tga",
			playerSettingModule.RACE_WARRIOR_W :"icon/face/warrior_w.tga",
			playerSettingModule.RACE_ASSASSIN_M :"icon/face/assassin_m.tga",
			playerSettingModule.RACE_SURA_W :"icon/face/sura_w.tga",
			playerSettingModule.RACE_SHAMAN_M :"icon/face/shaman_m.tga",
			playerSettingModule.RACE_WOLFMAN_M :"icon/face/wolfman_m.tga",
		}
	else:
		RACE_FACE_PATH = {
			playerSettingModule.RACE_WARRIOR_M : "D:/ymir work/ui/intro/public_intro/face/face_warrior_m_0",
			playerSettingModule.RACE_ASSASSIN_W : "D:/ymir work/ui/intro/public_intro/face/face_assassin_w_0",
			playerSettingModule.RACE_SURA_M : "D:/ymir work/ui/intro/public_intro/face/face_sura_m_0",
			playerSettingModule.RACE_SHAMAN_W : "D:/ymir work/ui/intro/public_intro/face/face_shaman_w_0",
			playerSettingModule.RACE_WARRIOR_W : "D:/ymir work/ui/intro/public_intro/face/face_warrior_w_0",
			playerSettingModule.RACE_ASSASSIN_M : "D:/ymir work/ui/intro/public_intro/face/face_assassin_m_0",
			playerSettingModule.RACE_SURA_W : "D:/ymir work/ui/intro/public_intro/face/face_sura_w_0",
			playerSettingModule.RACE_SHAMAN_M : "D:/ymir work/ui/intro/public_intro/face/face_shaman_m_0",
		}
		DISC_FACE_PATH = {
			playerSettingModule.RACE_WARRIOR_M : "icon/face/warrior_m.tga",
			playerSettingModule.RACE_ASSASSIN_W : "icon/face/assassin_w.tga",
			playerSettingModule.RACE_SURA_M : "icon/face/sura_m.tga",
			playerSettingModule.RACE_SHAMAN_W : "icon/face/shaman_w.tga",
			playerSettingModule.RACE_WARRIOR_W : "icon/face/warrior_w.tga",
			playerSettingModule.RACE_ASSASSIN_M : "icon/face/assassin_m.tga",
			playerSettingModule.RACE_SURA_W : "icon/face/sura_w.tga",
			playerSettingModule.RACE_SHAMAN_M : "icon/face/shaman_m.tga",
		}

	class DescriptionBox(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.descIndex = 0

		def __del__(self):
			ui.Window.__del__(self)

		def SetIndex(self, index):
			self.descIndex = index

		def OnRender(self):
			event.RenderEventSet(self.descIndex)

	class CharacterRenderer(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.viewportX = 0
			self.viewportY = 0
			self.viewportWidth = 1
			self.viewportHeight = 1
			self.hasAccessory = True

		def Configure(self, x, y, width, height):
			self.viewportX = max(0, int(x))
			self.viewportY = max(0, int(y))
			self.viewportWidth = max(1, int(width))
			self.viewportHeight = max(1, int(height))
			self.SetSize(self.viewportWidth, self.viewportHeight)

		def OnRender(self):
			grp.ClearDepthBuffer()

			grp.SetGameRenderState()
			grp.PushState()
			grp.SetOmniLight()

			screenWidth = wndMgr.GetScreenWidth()
			screenHeight = wndMgr.GetScreenHeight()
			viewportWidth = float(self.viewportWidth)
			viewportHeight = float(self.viewportHeight)

			grp.SetViewport(
				float(self.viewportX) / float(screenWidth),
				float(self.viewportY) / float(screenHeight),
				viewportWidth / float(screenWidth),
				viewportHeight / float(screenHeight),
			)

			app.SetCenterPosition(0.0, 0.0, 0.0) # X, Z, Y (X + RIGHT, Z + ??, Y + DOWN) 좀 더 분석해 볼 것 
			app.SetCamera(1550.0, 15.0, 180.0, 95.0)
			aspect = viewportWidth / viewportHeight
			# Ordinary characters need a narrower horizontal field than wings.
			# Keep their 10-degree vertical framing in normal windows, reserving
			# the wider two-axis field only for equipped/unknown accessories.
			verticalHalf = math.tan(math.radians(5.0))
			horizontalHalf = math.tan(math.radians(5.0 if self.hasAccessory else 3.0))
			fov = math.degrees(2.0 * math.atan(max(verticalHalf, horizontalHalf / aspect)))
			grp.SetPerspective(fov, aspect, 1000.0, 3000.0)

			(x, y) = app.GetCursorPosition()
			grp.SetCursorPosition(x, y)

			chr.Deform()
			chr.Render()

			grp.RestoreViewport()
			grp.PopState()
			grp.SetInterfaceRenderState()

	def __init__(self, stream):
		if not app.DISABLE_WOLFMAN_CREATION:
			## Job Description ##
			self.DESCRIPTION_FILE_NAME = (
				uiScriptLocale.JOBDESC_WARRIOR_PATH,
				uiScriptLocale.JOBDESC_ASSASSIN_PATH,
				uiScriptLocale.JOBDESC_SURA_PATH,
				uiScriptLocale.JOBDESC_SHAMAN_PATH,
				uiScriptLocale.JOBDESC_WOLFMAN_PATH,
			)

			## Job List ##
			self.JOB_LIST = {
				0 : localeInfo.JOB_WARRIOR,
				1 : localeInfo.JOB_ASSASSIN,
				2 : localeInfo.JOB_SURA,
				3 : localeInfo.JOB_SHAMAN,
				4 : localeInfo.JOB_WOLFMAN,
			}
		else:
			## Job Description ##
			self.DESCRIPTION_FILE_NAME = (
				uiScriptLocale.JOBDESC_WARRIOR_PATH,
				uiScriptLocale.JOBDESC_ASSASSIN_PATH,
				uiScriptLocale.JOBDESC_SURA_PATH,
				uiScriptLocale.JOBDESC_SHAMAN_PATH,
			)

			## Job List ##
			self.JOB_LIST = {
				0 : localeInfo.JOB_WARRIOR,
				1 : localeInfo.JOB_ASSASSIN,
				2 : localeInfo.JOB_SURA,
				3 : localeInfo.JOB_SHAMAN,
			}
		ui.Window.__init__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_SELECT, self)
		self.stream = stream
		self.mycharacters = None
		self.familyNameStatus = getattr(stream, "familyNameStatus", -1)
		self.familyName = getattr(stream, "familyName", "") if self.familyNameStatus == 2 else ""
		self.familyNameDialog = None
		self.familyNameAutoSelectPending = False
		self.r1 = None  # R1 column (root/uir1pregame.py); None = Living Sigil

		## Init Value ##
		self.SelectSlot = M2_INIT_VALUE
		self.OpenCreate = False
		self.ShowToolTip = False
		self.select_job = M2_INIT_VALUE
		self.select_race = M2_INIT_VALUE
		self.LEN_STATPOINT = 4
		self.descIndex = 0
		self.statpoint = [0, 0, 0, 0]
		self.curGauge = [0.0, 0.0, 0.0, 0.0]
		self.Name_FontColor_Def = grp.GenerateColor(0.7215, 0.7215, 0.7215, 1.0)
		self.Name_FontColor = grp.GenerateColor(197.0/255.0, 134.0/255.0, 101.0/255.0, 1.0)
		self.Level_FontColor = grp.GenerateColor(250.0/255.0, 211.0/255.0, 136.0/255.0, 1.0)
		if app.ENABLE_CONQUEROR_LEVEL:
			self.Conqueror_Level_FontColor = grp.GenerateColor(140.0 / 255.0, 200.0 / 255.0, 255.0 / 255.0, 1.0)
		self.Not_SelectMotion = False
		self.MotionStart = False
		self.MotionTime = 0.0
		self.RealSlot = []
		self.Disable = False
		if app.ENABLE_CONQUEROR_LEVEL:
			self.StatPage = ORIGEN_STAT

		if app.ENABLE_PET_MOUNT_COSTUME_CREATE:
			self.OFFSETS = [100, 200]

	def __del__(self):
		ui.Window.__del__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_SELECT, 0)

	@staticmethod
	def FormatPlayTime(minutes):
		try:
			minutes = max(0, int(minutes))
		except (TypeError, ValueError):
			minutes = 0
		return "%d h %02d min" % (minutes // 60, minutes % 60)

	@staticmethod
	def StatRatio(value):
		try:
			return max(0.0, min(1.0, float(value) / 90.0))
		except (TypeError, ValueError):
			return 0.0

	@staticmethod
	def ShortStatLabel(text, fallback):
		try:
			left = text.rfind("(")
			right = text.find(")", left + 1)
			if left >= 0 and right > left + 1:
				return text[left + 1:right]
		except (AttributeError, TypeError):
			pass
		return fallback

	def Open(self):
		# print "##---------------------------------------- NEW INTRO SELECT OPEN"
		autoSelectRealSlot = self.stream.GetCharacterSlot() if self.stream.isAutoSelect else None
		if osfInfo.SELECT_CHARACTER_ROTATION == True:
			self.Rotation = 0
		playerSettingModule.LoadGameData("INIT")

		dlgBoard = ui.ScriptWindow()
		self.dlgBoard = dlgBoard
		pythonScriptLoader = ui.PythonScriptLoader() # uiScriptLocale.LOCALE_UISCRIPT_PATH = locale/ymir_ui/
		pythonScriptLoader.LoadScriptFile( self.dlgBoard, uiScriptLocale.LOCALE_UISCRIPT_PATH + "New_SelectCharacterWindow.py")
		self.layoutSize = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())

		getChild = self.dlgBoard.GetChild

		## Background ##
		self.backGround = getChild("BackGround")
		introbackground.apply_background(self.backGround, *self.layoutSize)
		self.brandMark = getChild("giant_brand_mark")
		self.brandMark.SetAlpha(0.34)
		self.renderArea = getChild("character_render_area")
		self.NameList = []

		## Button List ##
		self.btnStart = getChild("start_button")
		self.btnCreate = getChild("create_button")
		self.btnDelete = getChild("delete_button")
		self.btnExit = getChild("exit_button")

		## Face Image ##
		self.FaceImage = []
		self.FaceImage.append(getChild("CharacterFace_0"))
		self.FaceImage.append(getChild("CharacterFace_1"))
		self.FaceImage.append(getChild("CharacterFace_2"))
		self.FaceImage.append(getChild("CharacterFace_3"))
		self.FaceImage.append(getChild("CharacterFace_4"))
		if not app.ENABLE_PLAYER_PER_ACCOUNT5:
			self.FaceImage[4].Hide()

		self.EmptyRowList = []
		self.RowNameList = []
		self.RowMetaList = []
		for i in range(5):
			self.EmptyRowList.append(getChild("NoneButton_%d" % i))
			self.RowNameList.append(getChild("row_name_%d" % i))
			self.RowMetaList.append(getChild("row_meta_%d" % i))
			self.EmptyRowList[i].SetEvent(ui.__mem_func__(self.CreateCharacterInRow), i)
		if not app.ENABLE_PLAYER_PER_ACCOUNT5:
			self.EmptyRowList[4].Hide()

		## Select Character List ##
		self.CharacterButtonList = []
		self.CharacterButtonList.append(getChild("CharacterSlot_0"))
		self.CharacterButtonList.append(getChild("CharacterSlot_1"))
		self.CharacterButtonList.append(getChild("CharacterSlot_2"))
		self.CharacterButtonList.append(getChild("CharacterSlot_3"))
		self.CharacterButtonList.append(getChild("CharacterSlot_4"))
		if not app.ENABLE_PLAYER_PER_ACCOUNT5:
			self.CharacterButtonList[4].Hide()

		## ToolTip : GuildName, PlayTime ##
		getChild("CharacterSlot_0").ShowToolTip = lambda arg = 0 : self.OverInToolTip(arg)
		getChild("CharacterSlot_0").HideToolTip = lambda : self.OverOutToolTip()
		getChild("CharacterSlot_1").ShowToolTip = lambda arg = 1 : self.OverInToolTip(arg)
		getChild("CharacterSlot_1").HideToolTip = lambda : self.OverOutToolTip()
		getChild("CharacterSlot_2").ShowToolTip = lambda arg = 2 : self.OverInToolTip(arg)
		getChild("CharacterSlot_2").HideToolTip = lambda : self.OverOutToolTip()
		getChild("CharacterSlot_3").ShowToolTip = lambda arg = 3 : self.OverInToolTip(arg)
		getChild("CharacterSlot_3").HideToolTip = lambda : self.OverOutToolTip()
		if app.ENABLE_PLAYER_PER_ACCOUNT5:
			getChild("CharacterSlot_4").ShowToolTip = lambda arg = 4 : self.OverInToolTip(arg)
			getChild("CharacterSlot_4").HideToolTip = lambda : self.OverOutToolTip()

		## ToolTip etc : Create, Delete, Start, Exit, Prev, Next ##
		getChild("create_button").ShowToolTip = lambda arg = uiScriptLocale.SELECT_CREATE : self.OverInToolTipETC(arg)
		getChild("create_button").HideToolTip = lambda : self.OverOutToolTip()
		getChild("delete_button").ShowToolTip = lambda arg = uiScriptLocale.SELECT_DELETE : self.OverInToolTipETC(arg)
		getChild("delete_button").HideToolTip = lambda : self.OverOutToolTip()
		getChild("start_button").ShowToolTip = lambda arg = uiScriptLocale.SELECT_SELECT : self.OverInToolTipETC(arg)
		getChild("start_button").HideToolTip = lambda : self.OverOutToolTip()
		getChild("exit_button").ShowToolTip = lambda arg = uiScriptLocale.SELECT_EXIT : self.OverInToolTipETC(arg)
		getChild("exit_button").HideToolTip = lambda : self.OverOutToolTip()

		self.selectThinboardPage = None

		if app.ENABLE_CONQUEROR_LEVEL:
			self.originStatButton = getChild("origin_stat_button")
			self.originStatButton.SetEvent(ui.__mem_func__(self.SetStatPage), ORIGEN_STAT)
			self.originStatButton.SetShowToolTipEvent(ui.__mem_func__(self.OverInToolTipETC), uiScriptLocale.SELECT_ORIGIN_STAT)
			self.originStatButton.SetHideToolTipEvent(ui.__mem_func__(self.OverOutToolTip))

			self.sungmaStatButton = getChild("sungma_stat_button")
			self.sungmaStatButton.SetEvent(ui.__mem_func__(self.SetStatPage), SUNGMA_STAT)
			self.sungmaStatButton.SetShowToolTipEvent(ui.__mem_func__(self.OverInToolTipETC), uiScriptLocale.SELECT_SUNGMA_STAT)
			self.sungmaStatButton.SetHideToolTipEvent(ui.__mem_func__(self.OverOutToolTip))
		else:
			self.originStatButton = None
			self.sungmaStatButton = None

		self.statLabel = []
		for i in range(4):
			self.statLabel.append(getChild("stat_label_%d" % i))

		## StatPoint Value ##
		self.statValue = []
		self.statValue.append(getChild("hth_value"))
		self.statValue.append(getChild("int_value"))
		self.statValue.append(getChild("str_value"))
		self.statValue.append(getChild("dex_value"))

		## Gauge UI ##
		self.GaugeList = []
		self.GaugeList.append(getChild("hth_gauge"))
		self.GaugeList.append(getChild("int_gauge"))
		self.GaugeList.append(getChild("str_gauge"))
		self.GaugeList.append(getChild("dex_gauge"))

		self.selectedName = getChild("selected_name")
		self.selectedLevel = getChild("selected_level")
		self.selectedGuild = getChild("selected_guild")
		self.selectedPlaytime = getChild("selected_playtime")
		self.textBoard = None
		self.btnPrev = None
		self.btnNext = None
		self.discFace = None
		self.raceNameText = None
		self.myID = None

		## Button Event ##
		self.btnStart.SetEvent(ui.__mem_func__(self.StartGameButton))
		self.btnCreate.SetEvent(ui.__mem_func__(self.CreateCharacterButton))
		self.btnExit.SetEvent(ui.__mem_func__(self.ExitButton))
		self.btnDelete.SetEvent(ui.__mem_func__(self.InputPrivateCode))

		## Select MyCharacter ##
		self.CharacterButtonList[0].SetEvent(ui.__mem_func__(self.SelectButton), 0)
		self.CharacterButtonList[1].SetEvent(ui.__mem_func__(self.SelectButton), 1)
		self.CharacterButtonList[2].SetEvent(ui.__mem_func__(self.SelectButton), 2)
		self.CharacterButtonList[3].SetEvent(ui.__mem_func__(self.SelectButton), 3)
		if app.ENABLE_PLAYER_PER_ACCOUNT5:
			self.CharacterButtonList[4].SetEvent(ui.__mem_func__(self.SelectButton), 4)

		# Account loading selects a character synchronously, so its renderer
		# must exist before the selection callback updates accessory framing.
		self.chrRenderer = self.CharacterRenderer()
		self.chrRenderer.SetParent(self.renderArea)
		self.chrRenderer.SetPosition(0, 0)
		renderX, renderY = self.renderArea.GetGlobalPosition()
		self.chrRenderer.Configure(renderX, renderY, self.renderArea.GetWidth(), self.renderArea.GetHeight())
		self.chrRenderer.Show()

		## MyCharacter CLASS ##
		self.mycharacters = MyCharacters(self);
		self.mycharacters.LoadCharacterData()

		if not self.mycharacters.GetMyCharacterCount():
			self.stream.SetCharacterSlot(self.mycharacters.GetEmptySlot())
			self.OpenCreate = self.AutoCreateOnOpen()

		self.descriptionBox = None

		## Tool Tip(Guild Name, PlayTime) ##
		self.toolTip = uiToolTip.ToolTip()
		self.toolTip.ClearToolTip()

		self.dlgBoard.Show()
		self.Show()
		import uir1pregame
		self.r1 = uir1pregame.AttachSelect(self)
		if self.familyNameStatus not in (-1, 0, 2):
			self.OpenFamilyNameDialog()

		if self.stream.isAutoSelect:
			displaySlot = 0
			try:
				displaySlot = self.RealSlot.index(autoSelectRealSlot)
			except ValueError:
				pass
			self.SelectButton(displaySlot)
			self.familyNameAutoSelectPending = self.familyNameStatus == -1
			self.StartGameButton()

		app.ShowCursor()

		# the hall's track alone (root/pregamemusic.py: the engine does not fade before the game - a FadeOutMusic
		# left the login music playing on); the same file in the creation plays on
		played = None
		try:
			import uipregamehall
			played = uipregamehall.ApplyMusic(self._Hall() is not None)
		except Exception:
			played = None
		if played is None and musicInfo.selectMusic != "":
			try:
				import pregamemusic
				pregamemusic.Only("BGM/" + musicInfo.selectMusic)
			except Exception:
				snd.SetMusicVolume(systemSetting.GetMusicVolume())
				snd.FadeInMusic("BGM/"+musicInfo.selectMusic)

		## Default Setting ##
	def EventProgress(self, event_type, slot):
		if self.Disable:
			return

		if "mouse_click" == event_type:
			if slot == self.SelectSlot:
				return

			snd.PlaySound("sound/ui/click.wav")
			self.SelectButton(slot)

		elif "mouse_over_in" == event_type:
			for button in self.CharacterButtonList:
				button.SetUp()

			# self.CharacterButtonList[slot].Over()
			self.CharacterButtonList[self.SelectSlot].Down()
			self.OverInToolTip(slot)

		elif "mouse_over_out" == event_type:
			for button in self.CharacterButtonList:
				button.SetUp()

			self.CharacterButtonList[self.SelectSlot].Down()
			self.OverOutToolTip()

		else:
			print(" New_introSelect.py ::EventProgress : FALSE")

	def SelectButton(self, slot):
		# print "self.RealSlot = %s" % self.RealSlot
		# slot 0 ~ 4
		if slot >= self.mycharacters.GetMyCharacterCount() or slot == self.SelectSlot:
			return

		if self.Not_SelectMotion or self.MotionTime != 0.0:
			self.CharacterButtonList[slot].SetUp()
			# self.CharacterButtonList[slot].Over()
			return

		for button in self.CharacterButtonList:
			button.SetUp()

		prev_slot = self.SelectSlot
		self.SelectSlot = slot
		self.CharacterButtonList[self.SelectSlot].Down()
		self.stream.SetCharacterSlot(self.RealSlot[self.SelectSlot])

		self.select_job = self.mycharacters.GetJob(self.SelectSlot)

		osfInfo.currentHairIndex=self.mycharacters.GetHair(self.SelectSlot)
		if app.ENABLE_CONQUEROR_LEVEL:
			self.SetStatPage(ORIGEN_STAT)
		else:
			self.ResetStat()
		self.RefreshLivingSigilDetail(self.SelectSlot)

		## Face Setting & Font Color Setting ##
		self.select_race = self.mycharacters.GetRace(self.SelectSlot)
		# print "self.mycharacters.GetMyCharacterCount() = %s" % self.mycharacters.GetMyCharacterCount()
		for i in range(self.mycharacters.GetMyCharacterCount()):
			if slot == i:
				self.FaceImage[slot].LoadImage(self.RACE_FACE_PATH[self.select_race] + "1.sub")
			else:
				self.FaceImage[i].LoadImage(self.RACE_FACE_PATH[self.mycharacters.GetRace(i)] + "2.sub")

		try:
			cnt = self.mycharacters.GetMyCharacterCount()
		except Exception:
			cnt = 5

		hall = self._Hall()
		if hall is not None:
			# the hall (uipregamehall): every character stays in its place, only the light follows the selection
			self._RefreshR1("Select", prev_slot, self.SelectSlot)
		else:
			if prev_slot is not None and prev_slot != self.SelectSlot and chr.HasInstance(prev_slot):
				chr.SelectInstance(prev_slot)
				try:
					chr.PushOnceMotion(chr.MOTION_INTRO_NOT_SELECTED, 0.1)
				except Exception:
					pass
				chr.Hide()

			for i in range(cnt):
				if i == self.SelectSlot:
					continue
				if chr.HasInstance(i):
					chr.SelectInstance(i)
					chr.Hide()

			if chr.HasInstance(self.SelectSlot):
				chr.SelectInstance(self.SelectSlot)
				chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)
				chr.Show()

		if app.ENABLE_PET_MOUNT_COSTUME_CREATE:
			self.ClearPetAndMountInstances()
		self._RefreshR1()

	def _Hall(self):
		r1 = getattr(self, "r1", None)
		if r1 is not None and getattr(r1, "is_hall", False) and not getattr(r1, "failed", False):
			return r1
		return None

	def _HallDev(self):
		hall = self._Hall()
		if hall is not None and getattr(hall, "cfg", {}).get("devkeys", 0):
			return hall
		return None

	def _RefreshR1(self, method="Refresh", *args):
		if getattr(self, "r1", None) is not None:
			import uir1pregame
			return uir1pregame.Safe(self.r1, method, *args)
		return None

	def Close(self):
		if self.familyNameDialog:
			self.familyNameDialog.Close()
			self.familyNameDialog = None
		if getattr(self, "r1", None) is not None:
			self._RefreshR1("Destroy")
			self.r1 = None
		#print "##---------------------------------------- NEW INTRO SELECT CLOSE"
		# A queued phase can be closed before Open(), or again during shutdown.
		self.mycharacters = None
		self.RACE_FACE_PATH = None
		self.DISC_FACE_PATH = None
		self.DESCRIPTION_FILE_NAME = None
		self.JOB_LIST = None

		## Default Value ##
		self.SelectSlot = None
		self.OpenCreate = None
		self.ShowToolTip = None
		self.LEN_STATPOINT = None
		self.descIndex = None
		self.statpoint = None #[]
		self.curGauge = None #[]
		self.Name_FontColor_Def = None
		self.Name_FontColor = None
		self.Level_FontColor = None
		if app.ENABLE_CONQUEROR_LEVEL:
			self.Conqueror_Level_FontColor = None
		self.Not_SelectMotion = None
		self.MotionStart = None
		self.MotionTime = None
		self.RealSlot = None
		if app.ENABLE_CONQUEROR_LEVEL:
			self.StatPage = None

		self.select_job = None
		self.select_race = None

		## Open Func ##
		self.dlgBoard = None
		self.backGround = None
		self.brandMark = None
		self.renderArea = None
		self.chrRenderer = None
		self.NameList = None #[]
		self.btnStart = None
		self.btnCreate = None
		self.btnDelete = None
		self.btnExit = None
		self.FaceImage = None #[]
		self.CharacterButtonList = None #[]
		self.EmptyRowList = None #[]
		self.RowNameList = None #[]
		self.RowMetaList = None #[]
		self.statLabel = None #[]
		self.statValue = None #[]
		self.GaugeList = None #[]
		self.selectedName = None
		self.selectedLevel = None
		self.selectedGuild = None
		self.selectedPlaytime = None
		self.originStatButton = None
		self.sungmaStatButton = None
		self.textBoard = None
		self.btnPrev = None
		self.btnNext = None
		self.raceNameText = None
		# self.descPhaseText = None
		self.myID = None

		self.descriptionBox = None
		self.toolTip = None
		self.Disable = None

		if musicInfo.selectMusic != "":
			snd.FadeOutMusic("BGM/"+musicInfo.selectMusic)

		if app.ENABLE_PET_MOUNT_COSTUME_CREATE:
			for i in range(CHARACTER_SLOT_COUNT_MAX):
				for offset in self.OFFSETS:
					if chr.HasInstance(i + offset):
						chr.DeleteInstance(i + offset)

		self.Hide()
		self.KillFocus()
		app.HideCursor()
		event.Destroy()

	def CreateCharacterButton(self):
		self.OpenCreateCharacterSlot(self.mycharacters.GetEmptySlot())

	def CreateCharacterInRow(self, displaySlot):
		emptyIndex = displaySlot - self.mycharacters.GetMyCharacterCount()
		slotNumber = self.mycharacters.GetEmptySlot(emptyIndex)
		self.OpenCreateCharacterSlot(slotNumber)

	def OpenCreateCharacterSlot(self, slotNumber):
		if self.familyNameStatus not in (0, 2):
			if self.familyNameStatus != -1:
				self.OpenFamilyNameDialog()
			return


		if slotNumber == M2_INIT_VALUE:
			self.stream.popupWindow.Close()
			self.stream.popupWindow.Open(localeInfo.CREATE_FULL, 0, localeInfo.UI_OK)
			return

		pid = self.GetCharacterSlotPID(slotNumber)

		if not pid:
			self.stream.SetCharacterSlot(slotNumber)
			self.stream.SetCreateCharacterPhase()
			self.Hide()

	def ExitButton(self):
		app.Exit()
		self.Hide()

	def StartGameButton(self):
		if self.familyNameStatus not in (0, 2):
			if self.familyNameStatus != -1:
				self.OpenFamilyNameDialog()
			return

		if not self.mycharacters.GetMyCharacterCount() or self.MotionTime != 0.0:
			return

		self.DisableWindow()

		IsChangeName = self.mycharacters.GetChangeName(self.SelectSlot)
		if IsChangeName:
			self.OpenChangeNameDialog()
			return

		if chr.HasInstance(self.SelectSlot):
			chr.SelectInstance(self.SelectSlot)
			chr.Show()
			chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)

		chr.PushOnceMotion(chr.MOTION_INTRO_SELECTED)
		self.MotionStart = True
		self.MotionTime = app.GetTime()

	def RefreshResponsiveLayout(self):
		size = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		if size != self.layoutSize:
			# Re-evaluate profile and min/max branches after a live resize. Expr
			# alone keeps the branch chosen when the script was first loaded.
			path = uiScriptLocale.LOCALE_UISCRIPT_PATH + "New_SelectCharacterWindow.py"
			namespace = {"SCREEN_WIDTH": size[0], "SCREEN_HEIGHT": size[1]}
			execfile(path, namespace)
			body = namespace["window"]
			self.dlgBoard.SetSize(*size)
			loader = ui.PythonScriptLoader()
			pending = list(body["children"])
			while pending:
				entry = pending.pop()
				widget = self.dlgBoard.GetChild(entry["name"])
				kind = entry["type"]
				widget.SetPosition(entry["x"], entry["y"])
				if "width" in entry and "height" in entry:
					widget.SetSize(entry["width"], entry["height"])
				if kind in ("button", "radio_button"):
					wasDown = widget.IsDown()
					widget.SetUpVisual(entry["default_image"])
					widget.SetOverVisual(entry["over_image"])
					widget.SetDownVisual(entry["down_image"])
					widget.SetDisableVisual(entry["disable_image"])
					if widget.ButtonText:
						widget.ButtonText.SetPosition(widget.GetWidth() // 2, widget.GetHeight() // 2)
					if self.Disable:
						widget.Disable()
					elif wasDown:
						widget.Down()
				elif kind in ("image", "expanded_image"):
					# Portraits belong to the selected account race, not the
					# placeholder in the UIScript. Preserve their current image.
					if not entry["name"].startswith("CharacterFace_"):
						widget.LoadImage(entry["image"])
					if "x_scale" in entry:
						widget.SetScale(entry["x_scale"], entry["y_scale"])
				elif kind == "text":
					value = dict(entry)
					value["text"] = widget.GetText()
					loader.LoadElementText(widget, value, self.dlgBoard)
				pending.extend(entry.get("children", ()))
			introbackground.apply_background(self.backGround, *size)
			self.brandMark.SetAlpha(0.34)
			self.RefreshLivingSigilDetail(self.SelectSlot)
			self.RefreshStat()
			if self.SelectSlot >= 0 and not self.Disable:
				self.CharacterButtonList[self.SelectSlot].Down()
			self.layoutSize = size
			if getattr(self, "r1", None) is not None:
				import uir1pregame
				self._RefreshR1("Destroy")
				self.r1 = uir1pregame.AttachSelect(self)
		# The renderer must follow the actual widget, not its opening rectangle.
		renderX, renderY = self.renderArea.GetGlobalPosition()
		self.chrRenderer.Configure(renderX, renderY, self.renderArea.GetWidth(), self.renderArea.GetHeight())

	def AutoCreateOnOpen(self):
		# An account without characters opens creation by itself only on the way in. Coming back from
		# creation (Zpět / Esc) it stays here - with the empty rows and Vytvořit - instead of bouncing
		# straight back into creation (in-game 9. 10.: "z tvorby nejde odejít").
		back = getattr(self.stream, "backFromCreate", False)
		self.stream.backFromCreate = False
		return not back

	def OnUpdate(self):
		try:
			import pregamemusic
			pregamemusic.UpdatePhase(self)
		except Exception:
			pass
		# An account without characters goes straight to creation, but only
		# once its family name is settled: the server refuses creation without
		# one. While the status is unknown or the name is being chosen, stay
		# on this screen with the family-name dialog; status 2 resumes here.
		if self.OpenCreate and self.familyNameStatus in (0, 2):
			self.OpenCreate = False
			self.stream.SetCreateCharacterPhase()
			self.Hide()
			return

		self.RefreshResponsiveLayout()
		chr.Update()
		if osfInfo.SELECT_CHARACTER_ROTATION == True:
			self.Rotation = self.Rotation - 0.5
			chr.SetRotation(self.Rotation)

		self.ToolTipProgress()

		if self.MotionStart and app.GetTime() - self.MotionTime >= 2.0:
			self.MotionStart = False
			## 기존 사용 그대로 들구옴 ##
			#print " Start Game "
			chrSlot = self.stream.GetCharacterSlot()

			#print "chrSlot = %s" % chrSlot
			if musicInfo.selectMusic != "":
				snd.FadeLimitOutMusic("BGM/" + musicInfo.selectMusic, systemSetting.GetMusicVolume() * 0.05)
			try:
				import pregamemusic
				pregamemusic.Leave()  # the game's music code (with working engine fades) takes over
			except Exception:
				pass

			net.DirectEnter(chrSlot)
			playTime = net.GetAccountCharacterSlotDataInteger(chrSlot, net.ACCOUNT_CHARACTER_SLOT_PLAYTIME)

			import player
			player.SetPlayTime(playTime)
			import chat
			chat.Clear()

	# def Refresh(self):
	def GetCharacterSlotPID(self, slotIndex):
		return net.GetAccountCharacterSlotDataInteger(slotIndex, net.ACCOUNT_CHARACTER_SLOT_ID)

	def All_ButtonInfoHide(self):
		for i in range(CHARACTER_SLOT_COUNT_MAX):
			self.CharacterButtonList[i].Hide()
			self.FaceImage[i].Hide()
			self.RowNameList[i].SetText("")
			self.RowMetaList[i].SetText("")
			self.EmptyRowList[i].Show()
		for gauge in self.GaugeList:
			gauge.Hide()
		for detail in (self.selectedName, self.selectedLevel, self.selectedGuild, self.selectedPlaytime):
			detail.SetText("")

	if app.ENABLE_CONQUEROR_LEVEL:
		def SetStatPage(self, page):
			self.StatPage = page
			if self.StatPage == SUNGMA_STAT:
				labels = (
					self.ShortStatLabel(localeInfo.STAT_TOOLTIP_SUNGMA_STR, "STR"),
					self.ShortStatLabel(localeInfo.STAT_TOOLTIP_SUNGMA_HP, "HP"),
					self.ShortStatLabel(localeInfo.STAT_TOOLTIP_SUNGMA_MOVE, "MOV"),
					self.ShortStatLabel(localeInfo.STAT_TOOLTIP_SUNGMA_IMMUNE, "IMM"),
				)
				self.originStatButton.SetUp()
				self.sungmaStatButton.Down()
			else:
				labels = (
					uiScriptLocale.CREATE_HP,
					uiScriptLocale.CREATE_SP,
					uiScriptLocale.CREATE_ATT_GRADE,
					uiScriptLocale.CREATE_DEX_GRADE,
				)
				self.originStatButton.Down()
				self.sungmaStatButton.SetUp()

			for index, label in enumerate(labels):
				self.statLabel[index].SetText(label)

			self.ResetStat()
			self.RefreshLivingSigilDetail(self.SelectSlot)

	def _InitLivingSigilRow(self, slot, name, level, conqueror_level, real_slot):
		data = self.mycharacters.GetDisplayData(slot) or {}
		displayLevel = conqueror_level if conqueror_level > 0 else level
		playtime = self.FormatPlayTime(data.get("PLAYTIME", 0))
		self.RowNameList[slot].SetText(name)
		self.RowMetaList[slot].SetText(
			"Lv. %d   •   %s" % (displayLevel, playtime)
		)
		if localeInfo.IsARABIC():
			self.CharacterButtonList[slot].LeftRightReverse()
		self.EmptyRowList[slot].Hide()
		self.CharacterButtonList[slot].Show()
		self.FaceImage[slot].LoadImage(self.RACE_FACE_PATH[self.mycharacters.GetRace(slot)] + "2.sub")
		self.FaceImage[slot].Show()
		self.RealSlot.append(real_slot)

	if app.ENABLE_CONQUEROR_LEVEL:
		def InitDataSet(self, slot, name, level, conqueror_level, real_slot):
			self._InitLivingSigilRow(slot, name, level, conqueror_level, real_slot)
	else:
		def InitDataSet(self, slot, name, level, real_slot):
			self._InitLivingSigilRow(slot, name, level, 0, real_slot)

	def InputPrivateCode(self):
		if not self.mycharacters.GetMyCharacterCount():
			return

		r1 = getattr(self, "r1", None)
		if r1 is not None and not getattr(r1, "failed", False):
			board = self._RefreshR1("OpenDelete", not ENABLE_ENGNUM_DELETE_CODE, 7,
				ui.__mem_func__(self.AcceptInputPrivateCode), ui.__mem_func__(self.CancelInputPrivateCode))
			if board is not None:
				self.privateInputBoard = board
				self.DisableWindow()
				if not self.Not_SelectMotion:
					self.Not_SelectMotion = True
					chr.PushOnceMotion(chr.MOTION_INTRO_NOT_SELECTED, 0.1)
				return

		import uiCommon
		privateInputBoard = uiCommon.InputDialogWithDescription()
		privateInputBoard.SetTitle(localeInfo.INPUT_PRIVATE_CODE_DIALOG_TITLE)
		privateInputBoard.SetAcceptEvent(ui.__mem_func__(self.AcceptInputPrivateCode))
		privateInputBoard.SetCancelEvent(ui.__mem_func__(self.CancelInputPrivateCode))

		if ENABLE_ENGNUM_DELETE_CODE:
			pass
		else:
			privateInputBoard.SetNumberMode()

		privateInputBoard.SetSecretMode()
		privateInputBoard.SetMaxLength(7)

		privateInputBoard.SetBoardWidth(250)
		privateInputBoard.SetDescription(localeInfo.INPUT_PRIVATE_CODE_DIALOG_DESCRIPTION)
		privateInputBoard.Open()
		self.privateInputBoard = privateInputBoard

		self.DisableWindow()

		if not self.Not_SelectMotion:
			self.Not_SelectMotion = True
			chr.PushOnceMotion(chr.MOTION_INTRO_NOT_SELECTED, 0.1)

	def AcceptInputPrivateCode(self):
		privateCode = self.privateInputBoard.GetText()
		if not privateCode:
			return

		pid = net.GetAccountCharacterSlotDataInteger(self.RealSlot[self.SelectSlot], net.ACCOUNT_CHARACTER_SLOT_ID)

		if not pid:
			self.PopupMessage(localeInfo.SELECT_EMPTY_SLOT)
			return

		net.SendDestroyCharacterPacket(self.RealSlot[self.SelectSlot], privateCode)
		self.PopupMessage(localeInfo.SELECT_DELEING)

		self.CancelInputPrivateCode()
		return True

	def CancelInputPrivateCode(self):
		self._RefreshR1("CloseDelete")
		self.privateInputBoard = None
		self.Not_SelectMotion = False
		chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)
		self.EnableWindow()
		return True

	def OnDeleteSuccess(self, slot):
		self.PopupMessage(localeInfo.SELECT_DELETED)
		for i in range(len(self.RealSlot)):
			chr.DeleteInstance(i)

		self.RealSlot = []
		self.SelectSlot = M2_INIT_VALUE

		for button in self.CharacterButtonList:
			button.AppendTextLineAllClear()

		if not self.mycharacters.LoadCharacterData():
			self.stream.popupWindow.Close()
			self.stream.SetCharacterSlot(self.mycharacters.GetEmptySlot())
			self.OpenCreate = True
		self._RefreshR1()

	def OnDeleteFailure(self):
		self.PopupMessage(localeInfo.SELECT_CAN_NOT_DELETE)

	def EmptyFunc(self):
		pass

	def PopupMessage(self, msg, func = 0):
		if not func:
			func = self.EmptyFunc

		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg, func, localeInfo.UI_OK)

	def RefreshStat(self):
		for index, value in enumerate(self.statpoint):
			self.statValue[index].SetText(str(value))
			ratio = self.StatRatio(value)
			self.curGauge[index] = ratio
			if ratio <= 0.0:
				self.GaugeList[index].Hide()
			else:
				self.GaugeList[index].SetRenderingRect(0.0, 0.0, -1.0 + ratio, 0.0)
				self.GaugeList[index].Show()

	def RefreshLivingSigilDetail(self, slot):
		data = self.mycharacters.GetDisplayData(slot)
		# Use the same sorted account data as MakeCharacter; unknown data
		# keeps the conservative field and cannot inherit another slot's zoom.
		self.chrRenderer.hasAccessory = not data or data.get("ACCE") != 0
		if not data:
			return
		conquerorLevel = int(data.get("CONQUEROR_LEVEL", 0) or 0)
		level = conquerorLevel if conquerorLevel > 0 else int(data.get("LEVEL", 0) or 0)
		noGuild = getattr(uiScriptLocale, "SELECT_NO_GUILD", localeInfo.SELECT_NOT_JOIN_GUILD)
		guild = data.get("GUILDNAME") or noGuild
		guildLabel = getattr(uiScriptLocale, "GUILD_NAME", localeInfo.GUILD_NAME)
		played = self.FormatPlayTime(data.get("PLAYTIME", 0))
		characterName = data.get("NAME", "")
		familyName = getattr(self, "familyName", "")
		self.selectedName.SetText("%s  (%s)" % (characterName, familyName) if familyName else characterName)
		self.selectedLevel.SetText("Lv. %d" % level)
		self.selectedGuild.SetText("%s  %s" % (guildLabel, guild))
		self.selectedPlaytime.SetText(uiScriptLocale.SELECT_PLAYTIME + "  " + played)

	def ResetStat(self):
		if app.ENABLE_CONQUEROR_LEVEL:
			if self.StatPage == SUNGMA_STAT:
				myStatPoint = self.mycharacters.GetStatSungmaPoint(self.SelectSlot)
			else:
				myStatPoint = self.mycharacters.GetStatPoint(self.SelectSlot)
		else:
			myStatPoint = self.mycharacters.GetStatPoint(self.SelectSlot)

		if not myStatPoint:
			return

		for i in range(self.LEN_STATPOINT):
			self.statpoint[i] = myStatPoint[i]

		self.RefreshStat()

	## Job Description Prev & Next Button ##
	def PrevDescriptionPage(self):
		if True == event.IsWait(self.descIndex):
			if event.GetVisibleStartLine(self.descIndex) - event.BOX_VISIBLE_LINE_COUNT >= 0:
				event.SetVisibleStartLine(self.descIndex, event.GetVisibleStartLine(self.descIndex) - event.BOX_VISIBLE_LINE_COUNT)
				event.Skip(self.descIndex)
		else:
			event.Skip(self.descIndex)

	def NextDescriptionPage(self):
		if True == event.IsWait(self.descIndex):
			event.SetVisibleStartLine(self.descIndex, event.GetVisibleStartLine(self.descIndex) + event.BOX_VISIBLE_LINE_COUNT)
			event.Skip(self.descIndex)
		else:
			event.Skip(self.descIndex)

	## ToolTip : GuildName, PlayTime ##
	def OverInToolTip(self, slot):
		GuildName = localeInfo.GUILD_NAME
		myGuildName, myPlayTime = self.mycharacters.GetGuildNamePlayTime(slot)
		pos_x, pos_y = self.CharacterButtonList[slot].GetGlobalPosition()

		if not myGuildName:
			myGuildName = localeInfo.SELECT_NOT_JOIN_GUILD

		guild_name = GuildName + " : " + myGuildName
		play_time = uiScriptLocale.SELECT_PLAYTIME + " : " + self.FormatPlayTime(myPlayTime)

		textlen = max(len(guild_name), len(play_time))
		tooltip_width = 6 * textlen + 22

		self.toolTip.ClearToolTip()
		self.toolTip.SetThinBoardSize(tooltip_width)

		if localeInfo.IsARABIC():
			self.toolTip.SetToolTipPosition(pos_x - 23 - tooltip_width // 2, pos_y + 34)
			self.toolTip.AppendTextLine(guild_name, 0xffe4cb1b) ## YELLOW ##
			self.toolTip.AppendTextLine(play_time, 0xffffff00) ## YELLOW ##
		else:
			self.toolTip.SetToolTipPosition(pos_x + 173 + tooltip_width // 2, pos_y + 34)
			self.toolTip.AppendTextLine(guild_name, 0xffe4cb1b, False) ## YELLOW ##
			self.toolTip.AppendTextLine(play_time, 0xffffff00, False) ## YELLOW ##

		self.toolTip.Show()

	def OverInToolTipETC(self, arg):
		arglen = len(str(arg))
		pos_x, pos_y = wndMgr.GetMousePosition()

		self.toolTip.ClearToolTip()
		self.toolTip.SetThinBoardSize(11 * arglen)
		self.toolTip.SetToolTipPosition(pos_x + 50, pos_y + 50)
		self.toolTip.AppendTextLine(arg, 0xffffff00)
		self.toolTip.Show()
		self.ShowToolTip = True

	def OverOutToolTip(self):
		self.toolTip.Hide()
		self.ShowToolTip = False

	def ToolTipProgress(self):
		if self.ShowToolTip:
			pos_x, pos_y = wndMgr.GetMousePosition()
			self.toolTip.SetToolTipPosition(pos_x + 50, pos_y + 50)

	def SameLoginDisconnect(self):
		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(localeInfo.LOGIN_FAILURE_SAMELOGIN, self.ExitButton, localeInfo.UI_OK)

	def OnIMEReturn(self):
		self.StartGameButton()
		return True

	def OnPressEscapeKey(self):
		if self.Disable:
			return True
		self.ExitButton()
		return True

	def OnKeyDown(self, key):
		if self.MotionTime != 0.0:
			return

		if 2 == key: # 1
			self.SelectButton(0)
		elif 3 == key:
			self.SelectButton(1)
		elif 4 == key:
			self.SelectButton(2)
		elif 5 == key:
			self.SelectButton(3)
		elif 6 == key:
			self.SelectButton(4)
		elif 200 == key or 208 == key:
			self.KeyInputUpDown(key)
		elif (203 == key or 205 == key) and self._Hall() is not None:
			# the hall (uipregamehall): left / right walk the arc
			self._RefreshR1("Step", -1 if 203 == key else 1)
		elif 211 == key and self._Hall() is not None and not self.Disable:
			self.InputPrivateCode()
		elif HALL_MUSIC_KEY == key and self._Hall() is not None:
			self._RefreshR1("CycleMusic")
		elif key in HALL_DEV_KEYS and self._HallDev() is not None:
			# the hall's tuning keys - only with devkeys=1 in pregame-hall.cfg (off in the distributed client):
			# H / F10 the scene alone, F4 the unselected light, F5 rebuild from the cfg, F6 the row under the rig,
			# F7 the button layout, F9 the character detail, F11 a lightning now (F8 = the music, above)
			method = HALL_DEV_KEYS[key]
			if method == "Rebuild":
				import uir1pregame
				self._RefreshR1("Destroy")
				self.r1 = uir1pregame.AttachSelect(self)
			else:
				self._RefreshR1(method)
		else:
			return True

		return True

	def KeyInputUpDown(self, key):
		idx = self.SelectSlot
		maxValue = self.mycharacters.GetMyCharacterCount()
		if 200 == key: # UP
			idx = idx - 1
			if idx < 0:
				idx = maxValue - 1

		elif 208 == key: # DOWN
			idx = idx + 1
			if idx >= maxValue:
				idx = 0

		else: # 이런 경우 없겠지만, 혹시 몰라 예외 처리
			self.SelectButton(0)

		self.SelectButton(idx)

	def OnPressExitKey(self):
		if self.Disable:
			return True
		self.ExitButton()
		return True

	def DisableWindow(self):
		if self.btnStart:
			self.btnStart.Disable()
		if self.btnCreate:
			self.btnCreate.Disable()
		if self.btnExit:
			self.btnExit.Disable()
		if self.btnDelete:
			self.btnDelete.Disable()
		if self.btnPrev:
			self.btnPrev.Disable()
		if self.btnNext:
			self.btnNext.Disable()
		if self.originStatButton:
			self.originStatButton.Disable()
		if self.sungmaStatButton:
			self.sungmaStatButton.Disable()
		if self.toolTip:
			self.toolTip.Hide()
		self.ShowToolTip = False
		self.Disable = True
		if self.CharacterButtonList:
			for button in self.CharacterButtonList:
				button.Disable()
		if self.EmptyRowList:
			for button in self.EmptyRowList:
				button.Disable()
		self._RefreshR1("SetEnabled", False)

	def EnableWindow(self):
		if self.btnStart:
			self.btnStart.Enable()
		if self.btnCreate:
			self.btnCreate.Enable()
		if self.btnExit:
			self.btnExit.Enable()
		if self.btnDelete:
			self.btnDelete.Enable()
		if self.btnPrev:
			self.btnPrev.Enable()
		if self.btnNext:
			self.btnNext.Enable()
		if self.originStatButton:
			self.originStatButton.Enable()
		if self.sungmaStatButton:
			self.sungmaStatButton.Enable()
		if self.EmptyRowList:
			for button in self.EmptyRowList:
				button.Enable()
		self.Disable = False
		if self.CharacterButtonList:
			for button in self.CharacterButtonList:
				button.Enable()
		self._RefreshR1("SetEnabled", True)

	def OnFamilyNameStatus(self, status, name):
		self.familyNameStatus = status
		if status in (0, 1, 2):
			self.stream.familyNameStatus = status
			self.stream.familyName = name if status == 2 else ""
		if status == 2:
			self.familyName = name
			if self.familyNameDialog:
				self.familyNameDialog.Close()
				self.familyNameDialog = None
			if self.mycharacters and self.selectedName and self.SelectSlot is not None and self.SelectSlot != M2_INIT_VALUE:
				self.RefreshLivingSigilDetail(self.SelectSlot)
		elif status == 1:
			self.OpenFamilyNameDialog()
		elif status == 3:
			self.PopupMessage("Toto rodové jméno už někdo používá.")
		elif status == 4:
			self.PopupMessage("Jméno musí mít 3 až 16 znaků: písmena bez diakritiky, číslice a podtržítko.")
		elif status == 5:
			self.PopupMessage("Jméno se nepodařilo uložit. Zkus to prosím znovu.")
		if status in (0, 2) and self.familyNameAutoSelectPending:
			self.familyNameAutoSelectPending = False
			self.StartGameButton()

	def OpenFamilyNameDialog(self):
		if self.familyNameDialog or not getattr(self, "dlgBoard", None):
			return
		dialog = uiCommon.InputDialogWithDescription()
		dialog.SetTitle("Zvol rodové jméno")
		dialog.SetDescription("Společné jméno pro všechny postavy na tomto účtu")
		dialog.SetMaxLength(16)
		dialog.SetBoardWidth(320)
		dialog.SetAcceptEvent(ui.__mem_func__(self.AcceptFamilyName))
		dialog.SetCancelEvent(ui.__mem_func__(self.CancelFamilyName))
		dialog.Open()
		self.familyNameDialog = dialog

	def AcceptFamilyName(self):
		if not self.familyNameDialog:
			return
		name = self.familyNameDialog.GetText()
		if not re.match(r"^[A-Za-z][A-Za-z0-9_]{2,15}$", name):
			self.PopupMessage("Jméno musí mít 3 až 16 znaků: písmena bez diakritiky, číslice a podtržítko.")
			return
		net.SendFamilyNamePacket(name)

	def CancelFamilyName(self):
		if self.familyNameDialog:
			self.familyNameDialog.Close()
			self.familyNameDialog = None
		return True

	def OpenChangeNameDialog(self):
		import uiCommon
		nameInputBoard = uiCommon.InputDialogWithDescription()
		nameInputBoard.SetTitle(localeInfo.SELECT_CHANGE_NAME_TITLE)
		nameInputBoard.SetAcceptEvent(ui.__mem_func__(self.AcceptInputName))
		nameInputBoard.SetCancelEvent(ui.__mem_func__(self.CancelInputName))
		nameInputBoard.SetMaxLength(namepolicy.CHARACTER_MAX_BYTES)
		nameInputBoard.SetBoardWidth(200)
		nameInputBoard.SetDescription(localeInfo.SELECT_INPUT_CHANGING_NAME)
		nameInputBoard.Open()
		nameInputBoard.slot = self.RealSlot[self.SelectSlot]
		self.nameInputBoard = nameInputBoard

	def AcceptInputName(self):
		changeName = self.nameInputBoard.GetText()
		error = namepolicy.character_error(changeName)
		if error is not namepolicy.CHARACTER_OK:
			self.PopupMessage(namepolicy.character_message(localeInfo, error, localeInfo.SELECT_CHANGE_FAILURE_STRANGE_NAME))
			return False

		net.SendChangeNamePacket(self.nameInputBoard.slot, changeName)
		return self.CancelInputName()

	def CancelInputName(self):
		self.nameInputBoard.Close()
		self.nameInputBoard = None
		self.EnableWindow()
		return True

	def OnCreateFailure(self, type):
		if 0 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_STRANGE_NAME)
		elif 1 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_ALREADY_EXIST_NAME)
		elif 100 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_STRANGE_INDEX)

	def OnChangeName(self, slot, name):
		for i in range(len(self.RealSlot)):
			if self.RealSlot[i] == slot:
				self.ChangeNameButton(i, name)
				self.SelectButton(i)
				self.PopupMessage(localeInfo.SELECT_CHANGED_NAME)
				break

	def ChangeNameButton(self, slot, name):
		self.RowNameList[slot].SetText(name)
		self.mycharacters.SetChangeNameSuccess(slot, name)
		if slot == self.SelectSlot:
			self.selectedName.SetText(name)

	if app.ENABLE_PET_MOUNT_COSTUME_CREATE:
		def ClearPetAndMountInstances(self):
			try:
				count = max(5, self.mycharacters.GetMyCharacterCount())
			except Exception:
				count = 5

			for i in range(count):
				for base_id in (100, 200):
					instance_id = i + base_id
					if chr.HasInstance(instance_id):
						chr.DeleteInstance(instance_id)
