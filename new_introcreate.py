import chr
import math
import createcharacterlayout
import introbackground
import grp
import app
import wndMgr
import net
import snd
import musicInfo
import systemSetting
import localeInfo
import namepolicy

import ui
import uiScriptLocale
import networkModule
import playerSettingModule

MAN = 0
WOMAN = 1

class CreateCharacterWindow(ui.Window):
	HAIR_DATA = (
		[ 0, 21, 22, 23, 24, 31, 32, 33, 34, 41, 42, 43, 44, 61, 51, 71, 81, 91, 101, ], ## Warrior
		[ 0, 21, 22, 23, 24, 31, 32, 33, 34, 41, 42, 43, 44, 61, 51, 71, 81, 91, 101, ], ## Assassin
		[ 0, 21, 22, 23, 24, 31, 32, 33, 34, 41, 42, 43, 44, 61, 51, 71, 81, 91, 101, ], ## Sura
		[ 0, 21, 22, 23, 24, 31, 32, 33, 34, 41, 42, 43, 44, 61, 51, 71, 81, 91, 101, ], ## Shaman
		[ 0, 21, 22, 23, 24, 31, 32, 33, 34, 41, 42, 43, 44, 61, 51, 71, 81, 91, 101, ], ## Wolfman
	)
	if not app.DISABLE_WOLFMAN_CREATION:
		M2STATPOINT = ( ## CON INT STR DEX ##
			( 4, 3, 6, 3 ), ## WARRIOR ##
			( 3, 3, 4, 6 ), ## ASSASSIN ##
			( 3, 5, 5, 3 ), ## SURA ##
			( 4, 6, 3, 3 ), ## SHAMAN ##
			( 6, 2, 2, 6 ), ## WOLFMAN ##
		)

		##M2_CONST_ID[JOB][SEX]##
		M2_CONST_ID = (
			(playerSettingModule.RACE_WARRIOR_M, playerSettingModule.RACE_WARRIOR_W),
			(playerSettingModule.RACE_ASSASSIN_M, playerSettingModule.RACE_ASSASSIN_W),
			(playerSettingModule.RACE_SURA_M, playerSettingModule.RACE_SURA_W),
			(playerSettingModule.RACE_SHAMAN_M, playerSettingModule.RACE_SHAMAN_W),
			(playerSettingModule.RACE_WOLFMAN_M, -1),
		)

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
		M2STATPOINT = ( ## CON INT STR DEX ##
			( 4, 3, 6, 3 ), ## WARRIOR ##
			( 3, 3, 4, 6 ), ## ASSASSIN ##
			( 3, 5, 5, 3 ), ## SURA ##
			( 4, 6, 3, 3 ), ## SHAMAN ##
		)

		##M2_CONST_ID[JOB][SEX]##
		M2_CONST_ID = (
			(playerSettingModule.RACE_WARRIOR_M, playerSettingModule.RACE_WARRIOR_W),
			(playerSettingModule.RACE_ASSASSIN_M, playerSettingModule.RACE_ASSASSIN_W),
			(playerSettingModule.RACE_SURA_M, playerSettingModule.RACE_SURA_W),
			(playerSettingModule.RACE_SHAMAN_M, playerSettingModule.RACE_SHAMAN_W),
		)

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
			playerSettingModule.RACE_WARRIOR_M :"icon/face/warrior_m.tga",
			playerSettingModule.RACE_ASSASSIN_W :"icon/face/assassin_w.tga",
			playerSettingModule.RACE_SURA_M :"icon/face/sura_m.tga",
			playerSettingModule.RACE_SHAMAN_W :"icon/face/shaman_w.tga",
			playerSettingModule.RACE_WARRIOR_W :"icon/face/warrior_w.tga",
			playerSettingModule.RACE_ASSASSIN_M :"icon/face/assassin_m.tga",
			playerSettingModule.RACE_SURA_W :"icon/face/sura_w.tga",
			playerSettingModule.RACE_SHAMAN_M :"icon/face/shaman_m.tga",
		}

	LEN_STATPOINT = len(M2STATPOINT[0])
	M2_INIT_VALUE = -1

	class CharacterRenderer(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.viewportX = self.viewportY = 0
			self.viewportWidth = self.viewportHeight = 1

		def Configure(self, x, y, width, height):
			self.viewportX, self.viewportY = max(0, int(x)), max(0, int(y))
			self.viewportWidth, self.viewportHeight = max(1, int(width)), max(1, int(height))
			self.SetSize(self.viewportWidth, self.viewportHeight)

		def OnRender(self):
			grp.ClearDepthBuffer()
			grp.SetGameRenderState()
			grp.PushState()
			grp.SetOmniLight()
			screenWidth, screenHeight = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
			width, height = float(self.viewportWidth), float(self.viewportHeight)
			grp.SetViewport(float(self.viewportX) / screenWidth, float(self.viewportY) / screenHeight, width / screenWidth, height / screenHeight)
			try:
				app.SetCenterPosition(0.0, 0.0, 0.0)
				app.SetCamera(1550.0, 15.0, 180.0, 95.0)
				aspect = width / height
				# Same two-axis framing as selection, for an unequipped live actor.
				fov = math.degrees(2.0 * math.atan(max(math.tan(math.radians(5.0)), math.tan(math.radians(3.0)) / aspect)))
				grp.SetPerspective(fov, aspect, 1000.0, 3000.0)
				grp.SetCursorPosition(*app.GetCursorPosition())
				chr.Deform()
				chr.Render()
			finally:
				grp.RestoreViewport()
				grp.PopState()
				grp.SetInterfaceRenderState()

	## class CreateCharacterWindow Function ##
	def __init__(self, stream):
		if not app.DISABLE_WOLFMAN_CREATION:
			self.M2JOBLIST = {
				0 : localeInfo.JOB_WARRIOR,
				1 : localeInfo.JOB_ASSASSIN,
				2 : localeInfo.JOB_SURA,
				3 : localeInfo.JOB_SHAMAN,
				4 : localeInfo.JOB_WOLFMAN,
			}

		else:
			self.M2JOBLIST = {
				0 : localeInfo.JOB_WARRIOR,
				1 : localeInfo.JOB_ASSASSIN,
				2 : localeInfo.JOB_SURA,
				3 : localeInfo.JOB_SHAMAN,
			}

		self.LEN_JOBLIST = len(self.M2JOBLIST)

		ui.Window.__init__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_CREATE, self)
		self.stream = stream

		## Init Value ##
		self.createSuccess = False
		self.MotionStart = False
		self.MotionTime = 0.0
		self.gender = self.M2_INIT_VALUE
		self.job_id = self.M2_INIT_VALUE
		self.shape = self.M2_INIT_VALUE
		self.controlsLocked = False
		self.layoutSize = None
		self.statpoint = [0, 0, 0, 0]
		self.curGauge = [0.0, 0.0, 0.0, 0.0]

	def __del__(self):
		net.SetPhaseWindow(net.PHASE_WINDOW_CREATE, 0)
		ui.Window.__del__(self)

	def Open(self):
		playerSettingModule.LoadGameData("INIT")
		self.dlgBoard = ui.ScriptWindow()
		ui.PythonScriptLoader().LoadScriptFile(self.dlgBoard, uiScriptLocale.LOCALE_UISCRIPT_PATH + "New_CreateCharacterWindow.py")
		getChild = self.dlgBoard.GetChild
		jobKeys = ("WARRIOR", "ASSASSIN", "SURA", "SHAMAN", "WOLFMAN")[:self.LEN_JOBLIST]
		self.JobList = [getChild(key) for key in jobKeys]
		self.SelectBtnFaceList = [getChild("CharacterFace_%d" % index) for index in range(self.LEN_JOBLIST)]
		self.SelectBtnNameList = [getChild("class_name_%d" % index) for index in range(self.LEN_JOBLIST)]
		self.genderButtonList = [getChild("gender_button_01"), getChild("gender_button_02")]
		self.shapeButtonList = [getChild("shape_button_01"), getChild("shape_button_02")]
		self.statValue = [getChild(key + "_value") for key in ("hth", "int", "str", "dex")]
		self.GaugeList = [getChild(key + "_gauge") for key in ("hth", "int", "str", "dex")]
		self.btnCreate, self.btnCancel = getChild("create_button"), getChild("cancel_button")
		self.raceNameText, self.actorNameText = getChild("raceName_Text"), getChild("actor_class_name")
		self.editCharacterName, self.nameField = getChild("character_name_value"), getChild("name_field")
		self.backGround, self.brandMark = getChild("BackGround"), getChild("giant_brand_mark")
		self.renderArea = getChild("character_render_area")
		self.layoutSize = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		layout = createcharacterlayout.get_layout(*self.layoutSize)
		self.layoutProfile, self.portraitLayout = layout["profile"], layout["portrait"]
		self.RefreshActionTypography()
		introbackground.apply_background(self.backGround, *self.layoutSize)
		self.brandMark.SetAlpha(0.60)
		self.JobSex = {index: app.GetRandom(MAN, WOMAN) for index in range(4)}
		if not app.DISABLE_WOLFMAN_CREATION:
			self.JobSex[4] = MAN
		self.editCharacterName.SetText("")
		for index, button in enumerate(self.JobList):
			button.SetEvent(ui.__mem_func__(self.SelectJob), index)
		for index in (0, 1):
			self.genderButtonList[index].SetEvent(ui.__mem_func__(self.SelectGender), index)
			self.shapeButtonList[index].SetEvent(ui.__mem_func__(self.SelectShape), index)
		self.btnCreate.SetEvent(ui.__mem_func__(self.CreateCharacterButton))
		self.btnCancel.SetEvent(ui.__mem_func__(self.CancelButton))
		self.editCharacterName.SetReturnEvent(ui.__mem_func__(self.CreateCharacterButton))
		self.editCharacterName.SetEscapeEvent(ui.__mem_func__(self.CancelButton))
		self.chrRenderer = self.CharacterRenderer()
		self.chrRenderer.SetParent(self.renderArea)
		self.chrRenderer.AddFlag("not_pick")
		self.chrRenderer.Show()
		for race in self.__GetAllCreatedRaces():
			self.MakeCharacter(race)
		self.EnableWindow()
		self.SelectJob(app.GetRandom(0, self.LEN_JOBLIST - 1))
		self.RefreshResponsiveLayout()
		self.dlgBoard.Show()
		self.SetSize(*self.layoutSize)
		self.Show()
		app.ShowCursor()
		if musicInfo.createMusic != "":
			snd.SetMusicVolume(systemSetting.GetMusicVolume())
			snd.FadeInMusic("BGM/" + musicInfo.createMusic)

	def Close(self):
		self.controlsLocked = True
		self.editCharacterName.KillFocus()
		self.chrRenderer.Hide()
		for race in self.__GetAllCreatedRaces():
			chr.DeleteInstance(race)
		if musicInfo.createMusic != "":
			snd.FadeOutMusic("BGM/" + musicInfo.createMusic)
		self.dlgBoard.Hide()
		self.dlgBoard.ClearDictionary()
		self.Hide()
		app.HideCursor()
		for name in ("JobList", "SelectBtnFaceList", "SelectBtnNameList", "genderButtonList", "shapeButtonList", "statValue", "GaugeList"):
			setattr(self, name, [])
		for name in ("btnCreate", "btnCancel", "raceNameText", "actorNameText", "editCharacterName", "nameField", "backGround", "brandMark", "renderArea", "chrRenderer", "dlgBoard", "stream"):
			setattr(self, name, None)

	## [Event]Create Success - Phase Change ##
	def OnCreateSuccess(self):
		self.createSuccess = True

	## [Event]Create Fail - ## EnableWindow
	def OnCreateFailure(self, type):
		self.MotionStart = False
		self.createSuccess = False
		chr.BlendLoopMotion(chr.MOTION_INTRO_WAIT, 0.1)

		if 1 == type:
			self.PopupMessage(localeInfo.CREATE_EXIST_SAME_NAME, self.EnableWindow)
		elif 2 == type:
			self.PopupMessage(localeInfo.CREATE_ERROR_LIMIT_LEVEL, self.EnableWindow)
		elif 3 == type:
			self.PopupMessage(localeInfo.CREATE_ERROR_TIME_LIMIT, self.EnableWindow)
		elif 4 == type:
			self.PopupMessage(localeInfo.CREATE_ERROR_WRONG_STRING, self.EnableWindow)
		else:
			self.PopupMessage(localeInfo.CREATE_FAILURE, self.EnableWindow)

	def EnableWindow(self):
		self.controlsLocked = False
		for button in self.JobList + self.genderButtonList + self.shapeButtonList + [self.btnCreate, self.btnCancel]:
			button.Enable()
		self.editCharacterName.Enable()
		self.editCharacterName.SetFocus()
		if self.job_id >= 0:
			self.JobList[self.job_id].Down()
			self.genderButtonList[self.gender].Down()
			self.shapeButtonList[self.shape].Down()

	def DisableWindow(self):
		self.controlsLocked = True
		for button in self.JobList + self.genderButtonList + self.shapeButtonList + [self.btnCreate, self.btnCancel]:
			button.Disable()
		self.editCharacterName.KillFocus()
		self.editCharacterName.Disable()

	def RefreshActionTypography(self):
		primary, choice, back = {"full": (27, 18, 15), "medium": (23, 15, 12), "compact": (18, 12, 10)}[self.layoutProfile]
		for button, size in [(self.btnCreate, primary), (self.btnCancel, back)] + [(button, choice) for button in self.genderButtonList + self.shapeButtonList]:
			# Native SetTextPointer does not invalidate the previous glyph run,
			# and assigning the same text is a no-op. Clear before changing font
			# so initial setup and every profile change rebuild visible glyphs.
			label = button.GetText()
			if not label:
				continue  # Czech captions are part of the Bloodglass state images.
			button.SetText("")
			button.SetFontName("Tahoma:%d" % size)
			button.SetText(label)
			if button.ButtonText:
				button.ButtonText.SetFontColor(0.89, 0.84, 0.75)

	def MakeCharacter(self, race):
		chr_id = race;

		chr.CreateInstance(chr_id)
		chr.SelectInstance(chr_id)
		chr.SetVirtualID(chr_id)
		chr.SetNameString(str(race))

		chr.SetRace(race)
		chr.SetArmor(0)
		chr.SetHair(0)

		chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
		chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)

		chr.SetRotation(-7.0) # Degree value
		chr.Hide()

	def __GetAllCreatedRaces(self):
		races = []
		try:
			for job in range(self.LEN_JOBLIST):
				for sex in (MAN, WOMAN):
					try:
						r = self.M2_CONST_ID[job][sex]
					except Exception:
						r = -1
					if r != -1:
						races.append(r)
		except Exception:
			pass
		return races

	def __HideOtherRaces(self, current_race):
		for r in self.__GetAllCreatedRaces():
			if r == current_race:
				continue
			if chr.HasInstance(r):
				chr.SelectInstance(r)
				chr.Hide()

	def SelectJob(self, job_id):
		if self.controlsLocked or self.MotionStart:
			return
		if job_id < 0 or job_id >= self.LEN_JOBLIST:
			return
		for index, button in enumerate(self.JobList):
			button.SetUp()
			self.SelectBtnNameList[index].SetFontColor(*((0.66, 0.62, 0.58) if index != job_id else (0.89, 0.84, 0.75)))
		self.job_id = job_id
		self.JobList[job_id].Down()
		self.SelectGender(self.JobSex[job_id])
		self.raceNameText.SetText(self.M2JOBLIST[job_id])
		self.actorNameText.SetText(self.M2JOBLIST[job_id])
		self.ResetStat()
		if self.M2_CONST_ID[job_id][WOMAN] == -1:
			self.genderButtonList[WOMAN].Hide()
		else:
			self.genderButtonList[WOMAN].Show()

	def SelectGender(self, gender):
		if self.controlsLocked or self.MotionStart:
			return
		if gender not in (MAN, WOMAN) or self.job_id < 0 or self.M2_CONST_ID[self.job_id][gender] == -1:
			return
		for button in self.genderButtonList:
			button.SetUp()

		self.gender = gender
		self.genderButtonList[self.gender].Down()

		if self.M2_INIT_VALUE == self.job_id:
			return

		self.JobSex[self.job_id] = self.gender
		self.race = self.M2_CONST_ID[self.job_id][self.gender]
		self.__HideOtherRaces(self.race)

		self.RefreshPortraits()

		if self.M2_INIT_VALUE == self.shape:
			self.shape = 0

		self.SelectShape(self.shape)

	def RefreshPortraits(self):
		portrait = self.portraitLayout
		loader = ui.PythonScriptLoader()
		for i in range(self.LEN_JOBLIST):
			face = self.SelectBtnFaceList[i]
			if self.job_id == i:
				face.LoadImage(self.RACE_FACE_PATH[self.race] + "1.sub")
			else:
				face.LoadImage(self.RACE_FACE_PATH[self.M2_CONST_ID[i][self.JobSex[i]]] + "2.sub")
			face.SetScale(portrait["scale"], portrait["scale"])
			# With ENABLE_TELEPORT_WINDOW native SetScale applies the scale
			# twice to widget bounds. Match them to the once-scaled artwork,
			# then compute the LTR/RTL anchor on initial load and every refresh.
			face.SetSize(portrait["size"], portrait["size"])
			loader.LoadDefaultData(face, portrait, self.JobList[i])

	def SelectShape(self, shape):
		if self.controlsLocked or self.MotionStart:
			return
		if shape not in (0, 1):
			return
		for button in self.shapeButtonList:
			button.SetUp()

		self.shape = shape
		self.shapeButtonList[self.shape].Down()

		# print "job = %s, race = %s, shape = %s" %(self.job_id, self.race, self.shape)

		if self.M2_INIT_VALUE == self.job_id:
			return

		self.__HideOtherRaces(self.race)
		chr.SelectInstance(self.race)
		chr.Hide()
		chr.ChangeShape(self.shape)
		chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
		chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)
		chr.Show()

	# def GetSlotIndex(self):
	def RefreshStat(self):
		for index in range(self.LEN_STATPOINT):
			self.statValue[index].SetText(str(self.statpoint[index]))
			ratio = max(0.0, min(1.0, float(self.statpoint[index]) / 8.0))
			self.GaugeList[index].SetRenderingRect(0.0, 0.0, ratio - 1.0, 0.0)
			if ratio > 0.0:
				self.GaugeList[index].Show()
			else:
				self.GaugeList[index].Hide()

	def ResetStat(self):
		for i in range(self.LEN_STATPOINT):
			self.statpoint[i] = self.M2STATPOINT[self.job_id][i]
		self.RefreshStat()

	## Create Character Button ##
	def CreateCharacterButton(self):
		if self.controlsLocked or self.job_id == self.M2_INIT_VALUE or self.MotionStart:
			return

		textName = self.editCharacterName.GetText()

		if False == self.CheckCreateCharacterName(textName):
			return

		self.DisableWindow()

		chrSlot = self.stream.GetCharacterSlot()
		raceIndex = self.M2_CONST_ID[self.job_id][self.gender]
		shapeIndex = self.shape
		statCon = self.M2STATPOINT[self.job_id][0]
		statInt = self.M2STATPOINT[self.job_id][1]
		statStr = self.M2STATPOINT[self.job_id][2]
		statDex = self.M2STATPOINT[self.job_id][3]

		chr.PushOnceMotion(chr.MOTION_INTRO_SELECTED)
		if app.ENABLE_PET_MOUNT_COSTUME_CREATE:
			net.SendCreateCharacterPacket(
				chrSlot, textName, raceIndex, shapeIndex,
				statCon, statInt, statStr, statDex, "",
				0, 0, 0, 0, 0
			)
		else:
			net.SendCreateCharacterPacket(chrSlot, textName, raceIndex, shapeIndex, statCon, statInt, statStr, statDex, "")

		self.MotionStart = True
		self.MotionTime = app.GetTime()

	## Cancel Button ##
	def CancelButton(self):
		if self.controlsLocked or self.MotionStart:
			return
		self.stream.SetSelectCharacterPhase()
		self.Hide()

	def EmptyFunc(self):
		pass

	def PopupMessage(self, msg, func = 0):
		if not func:
			func = self.EmptyFunc

		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg, func, localeInfo.UI_OK)

	def OnPressExitKey(self):
		self.CancelButton()
		return True

	def OnPressEscapeKey(self):
		return self.OnPressExitKey()

	def CheckCreateCharacterName(self, name):
		if len(name) == 0:
			self.PopupMessage(localeInfo.CREATE_INPUT_NAME, self.EnableWindow)
			return False

		# The shared policy also covers the legacy "GM" check.
		error = namepolicy.character_error(name)
		if error is not namepolicy.CHARACTER_OK:
			self.PopupMessage(namepolicy.character_message(localeInfo, error, localeInfo.CREATE_ERROR_INSULT_NAME), self.EnableWindow)
			return False

		return True

	def RefreshResponsiveLayout(self):
		size = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		if size != self.layoutSize:
			path = uiScriptLocale.LOCALE_UISCRIPT_PATH + "New_CreateCharacterWindow.py"
			namespace = {"SCREEN_WIDTH": size[0], "SCREEN_HEIGHT": size[1]}
			execfile(path, namespace)
			self.dlgBoard.SetSize(*size)
			self.SetSize(*size)
			layout = createcharacterlayout.get_layout(*size)
			self.layoutProfile, self.portraitLayout = layout["profile"], layout["portrait"]
			# RTL positioning uses each child's width. Restore the portrait's
			# new dimensions before the loader computes its mirrored anchor.
			self.RefreshPortraits()
			loader = ui.PythonScriptLoader()
			pending = [(entry, self.dlgBoard) for entry in namespace["window"]["children"]]
			while pending:
				entry, parentWidget = pending.pop()
				widget = self.dlgBoard.GetChild(entry["name"])
				kind = entry["type"]
				wasVisible = widget.IsShow()
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
					if self.controlsLocked:
						widget.Disable()
					elif wasDown:
						widget.Down()
				elif kind in ("image", "expanded_image"):
					if not entry["name"].startswith("CharacterFace_"):
						widget.LoadImage(entry["image"])
						if "x_scale" in entry:
							widget.SetScale(entry["x_scale"], entry["y_scale"])
				elif kind == "text":
					value = dict(entry)
					value["text"] = widget.GetText()
					widget.SetText("")
					loader.LoadElementText(widget, value, parentWidget)
				if kind != "text":
					# Match initial load after applying the new native dimensions.
					# In RTL the loader transforms X and window alignment together;
					# raw SetPosition would retain the previous RIGHT alignment.
					loader.LoadDefaultData(widget, entry, parentWidget)
				# Both loader paths call Show; preserve conditional visibility.
				if not wasVisible:
					widget.Hide()
				pending.extend((child, widget) for child in entry.get("children", ()))
			self.layoutSize = size
			self.RefreshActionTypography()
			self.nameFieldImage = None
			self.brandMark.SetAlpha(0.60)
			introbackground.apply_background(self.backGround, *size)
			self.RefreshStat()
			for index, label in enumerate(self.SelectBtnNameList):
				label.SetFontColor(*((0.66, 0.62, 0.58) if index != self.job_id else (0.89, 0.84, 0.75)))
			if not self.controlsLocked:
				self.JobList[self.job_id].Down()
				self.genderButtonList[self.gender].Down()
				self.shapeButtonList[self.shape].Down()
		renderX, renderY = self.renderArea.GetGlobalPosition()
		self.chrRenderer.Configure(renderX, renderY, self.renderArea.GetWidth(), self.renderArea.GetHeight())

	def OnUpdate(self):
		self.RefreshResponsiveLayout()
		chr.Update()
		state = "disabled" if self.controlsLocked else ("pressed" if self.editCharacterName.IsFocus() else "normal")
		fieldImage = "locale/common/ui/living_sigil_create/input_%s_%s.png" % (self.layoutProfile, state)
		if getattr(self, "nameFieldImage", None) != fieldImage:
			self.nameField.LoadImage(fieldImage)
			self.nameFieldImage = fieldImage
		if self.MotionStart and self.createSuccess and app.GetTime() - self.MotionTime >= 2.0:
			self.MotionStart = False
			self.stream.SetSelectCharacterPhase()
			self.Hide()
