import dbg
import ui
import snd
import systemSetting
import net
import chat
import app
import localeInfo
import constInfo
import chrmgr
import player
import musicInfo

import uiSelectMusic
import background
import uiPhaseCurtain

import uiCommon

import sys
import uiScriptLocale
import wndMgr

def ReloadModule(name):
	if name in sys.modules:
		del sys.modules[name]

		if name in locals():
			del locals()[name]

		if name in globals():
			del globals()[name]

		module = __import__(name)

		if not module in locals():
			locals()[name] = module

		if not module in globals():
			globals()[name] = module

MIN_LOCALE_SCROLL = 5
LOCALE_LANG_DICT = {
	app.LOCALE_EN : { "name" : uiScriptLocale.LANGUAGE_EN, "locale" : "en", "code_page" : 1252 },
	app.LOCALE_PT : { "name" : uiScriptLocale.LANGUAGE_PT, "locale" : "pt", "code_page" : 1252 },
	app.LOCALE_ES : { "name" : uiScriptLocale.LANGUAGE_ES, "locale" : "es", "code_page" : 1252 },
	app.LOCALE_FR : { "name" : uiScriptLocale.LANGUAGE_FR, "locale" : "fr", "code_page" : 1252 },
	app.LOCALE_GR : { "name" : uiScriptLocale.LANGUAGE_GR, "locale" : "gr", "code_page" : 1253 },
	app.LOCALE_DE : { "name" : uiScriptLocale.LANGUAGE_DE, "locale" : "de", "code_page" : 1252 },
	app.LOCALE_RO : { "name" : uiScriptLocale.LANGUAGE_RO, "locale" : "ro", "code_page" : 1250 },
	app.LOCALE_PL : { "name" : uiScriptLocale.LANGUAGE_PL, "locale" : "pl", "code_page" : 1250 },
	app.LOCALE_IT : { "name" : uiScriptLocale.LANGUAGE_IT, "locale" : "it", "code_page" : 1252 },
	app.LOCALE_CZ : { "name" : uiScriptLocale.LANGUAGE_CZ, "locale" : "cz", "code_page" : 1250 },
	app.LOCALE_HU : { "name" : uiScriptLocale.LANGUAGE_HU, "locale" : "hu", "code_page" : 1250 },
	app.LOCALE_TR : { "name" : uiScriptLocale.LANGUAGE_TR, "locale" : "tr", "code_page" : 1254 },
}

MUSIC_FILENAME_MAX_LEN = 25
if app.ENABLE_GRAPHIC_ON_OFF:
	GRAPHIC_LEVEL_MAX_NUM = 5

blockMode = 0

class OptionDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__Load()

		if app.ENABLE_GRAPHIC_ON_OFF:
			self.RefreshPetStatus()
			self.RefreshNpcNameStatus()

		self.questionDialog = None

		self.__CreateLanguageSelectWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		#print " -------------------------------------- DELETE SYSTEM OPTION DIALOG"

	def __Initialize(self):
		if not app.ENABLE_DISABLE_SOFTWARE_TILING:
			self.tilingMode = 0
		self.titleBar = 0
		self.changeMusicButton = 0
		self.selectMusicFile = 0
		self.ctrlMusicVolume = 0
		self.ctrlSoundVolume = 0
		self.musicListDlg = 0
		if not app.ENABLE_DISABLE_SOFTWARE_TILING:
			self.tilingApplyButton = 0
		self.cameraModeButtonList = []
		self.fogModeButtonList = []
		if not app.ENABLE_DISABLE_SOFTWARE_TILING:
			self.tilingModeButtonList = []
		self.ctrlShadowQuality = 0

		if app.ENABLE_FOG_FIX:
			self.fogButtonList = []

		if app.ENABLE_SHADOW_RENDER_QUALITY_OPTION:
			self.shadowQualityButtonList = []
			self.shadowTargetButtonList = []

		if app.ENABLE_GRAPHIC_ON_OFF:
			self.effectLevel = 0
			self.effectLevelApplyButton = 0
			self.effectLevelButtonList = []

			self.privateShopLevel = 0
			self.privateShopLevelApplyButton = 0
			self.privateShopLevelButtonList = []

			self.dropItemLevel = 0
			self.dropItemLevelApplyButton = 0
			self.dropItemLevelButtonList = []

			self.petStatusButtonList = []
			self.npcNameStatusButtonList = []

		if app.ENABLE_FOV_OPTION:
			self.fovController = None
			self.fovResetButton = None
			self.fovValueText = None

		if app.ENABLE_HIDE_SKILL_EFFECT:
			self.BLEffectGroupList = []

		self.language_change_window = None
		self.language_select_button = None
		self.language_change_button = None

		self.cur_language_text = None
		self.cur_language_text_window = None

		self.language_button_dict = {}
		self.language_select_list_open = False
		self.language_select_window_height = 0

		self.language_select_window_bar = None

		self.language_scrollbar = None
		self.language_scrollbar_pos = 0
		self.language_scrollbar_diff = 0

		self.mouse_over_image = None

		self.selected_language = 0

		self.IsShow = False

	def Destroy(self):
		self.ClearDictionary()

		self.__Initialize()
		#print " -------------------------------------- DESTROY SYSTEM OPTION DIALOG"

	def __Load_LoadScript(self, fileName):
		try:
			pyScriptLoader = ui.PythonScriptLoader()
			pyScriptLoader.LoadScriptFile(self, fileName)
		except:
			import exception
			exception.Abort("System.OptionDialog.__Load_LoadScript")

	def __Load_BindObject(self):
		try:
			GetObject = self.GetChild
			self.titleBar = GetObject("titlebar")
			self.selectMusicFile = GetObject("bgm_file")
			self.changeMusicButton = GetObject("bgm_button")
			self.ctrlMusicVolume = GetObject("music_volume_controller")
			self.ctrlSoundVolume = GetObject("sound_volume_controller")
			self.cameraModeButtonList.append(GetObject("camera_short"))
			self.cameraModeButtonList.append(GetObject("camera_long"))

			if app.ENABLE_FOG_FIX:
				self.fogButtonList.append(GetObject("fog_off"))
				self.fogButtonList.append(GetObject("fog_on"))
			else:
				self.fogModeButtonList.append(GetObject("fog_level0"))
				self.fogModeButtonList.append(GetObject("fog_level1"))
				self.fogModeButtonList.append(GetObject("fog_level2"))

			if app.ENABLE_HIDE_SKILL_EFFECT:
				for BLEffectNames in ('BuffEffect', 'SkillEffect'):
					self.BLEffectGroupList.append(GetObject('BL_EFFECT_{}'.format(BLEffectNames)))
				for (Index, Button) in enumerate(self.BLEffectGroupList):
					Button.SetToggleDownEvent(lambda arg=Index: self.__OnClickBLEffectButton(arg))
					Button.SetToggleUpEvent(lambda arg=Index: self.__OnClickBLEffectButton(arg))
				self.__RefreshBLEffectButton()

			if not app.ENABLE_DISABLE_SOFTWARE_TILING:
				self.tilingModeButtonList.append(GetObject("tiling_cpu"))
				self.tilingModeButtonList.append(GetObject("tiling_gpu"))
				self.tilingApplyButton = GetObject("tiling_apply")

			if app.ENABLE_GRAPHIC_ON_OFF:
				for i in range(1, GRAPHIC_LEVEL_MAX_NUM + 1):
					self.effectLevelButtonList.append(GetObject("effect_level%d" % i))
					self.privateShopLevelButtonList.append(GetObject("privateShop_level%d" % i))
					self.dropItemLevelButtonList.append(GetObject("dropItem_level%d" % i))

				self.effectLevelApplyButton = GetObject("effect_apply")
				self.privateShopLevelApplyButton = GetObject("privateShop_apply")
				self.dropItemLevelApplyButton = GetObject("dropItem_apply")

				self.petStatusButtonList.append(GetObject("pet_on"))
				self.petStatusButtonList.append(GetObject("pet_off"))

				self.npcNameStatusButtonList.append(GetObject("npcName_on"))
				self.npcNameStatusButtonList.append(GetObject("npcName_off"))

			if app.ENABLE_FOV_OPTION:
				self.fovController = GetObject("fov_controller")
				self.fovController.SetButtonVisual("d:/ymir work/ui/public/crimson/controls/slider/",\
					"small_thumb_01.tga",\
					"small_thumb_02.tga",\
					"small_thumb_03.tga")
				self.fovController.SetBackgroundVisual("d:/ymir work/ui/public/crimson/controls/slider/small_track.tga")
				self.fovResetButton = GetObject("fov_reset_button")
				self.fovValueText = GetObject("fov_value_text")

			self.language_select_button = self.GetChild("language_select_button")
			self.language_change_window = self.GetChild("language_change_window")
			self.cur_language_text = self.GetChild("cur_language_text")
			self.cur_language_text_window = self.GetChild("cur_language_text_window")
			self.language_change_button = self.GetChild("language_change_button")

			if app.ENABLE_SHADOW_RENDER_QUALITY_OPTION:
				self.shadowQualityButtonList.append(GetObject("shadow_quality_bad"))
				self.shadowQualityButtonList.append(GetObject("shadow_quality_average"))
				self.shadowQualityButtonList.append(GetObject("shadow_quality_good"))

				self.shadowTargetButtonList.append(GetObject("shadow_target_none"))
				self.shadowTargetButtonList.append(GetObject("shadow_target_ground"))
				self.shadowTargetButtonList.append(GetObject("shadow_target_ground_and_solo"))
				self.shadowTargetButtonList.append(GetObject("shadow_target_all"))

			#self.ctrlShadowQuality = GetObject("shadow_bar")
		except:
			import exception
			exception.Abort("OptionDialog.__Load_BindObject")

	def __Load(self):
		self.__Load_LoadScript("uiscript/systemoptiondialog.py")
		self.__Load_BindObject()

		self.SetCenterPosition()

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

		self.ctrlMusicVolume.SetSliderPos(float(systemSetting.GetMusicVolume()))
		self.ctrlMusicVolume.SetEvent(ui.__mem_func__(self.OnChangeMusicVolume))

		self.ctrlSoundVolume.SetSliderPos(float(systemSetting.GetSoundVolume()) / 5.0)
		self.ctrlSoundVolume.SetEvent(ui.__mem_func__(self.OnChangeSoundVolume))

		#self.ctrlShadowQuality.SetSliderPos(float(systemSetting.GetShadowLevel()) / 5.0)
		#self.ctrlShadowQuality.SetEvent(ui.__mem_func__(self.OnChangeShadowQuality))

		self.changeMusicButton.SAFE_SetEvent(self.__OnClickChangeMusicButton)

		self.cameraModeButtonList[0].SAFE_SetEvent(self.__OnClickCameraModeShortButton)
		self.cameraModeButtonList[1].SAFE_SetEvent(self.__OnClickCameraModeLongButton)

		if app.ENABLE_FOG_FIX:
			self.fogButtonList[0].SAFE_SetEvent(self.__OnClickFogModeOffButton)
			self.fogButtonList[1].SAFE_SetEvent(self.__OnClickFogModeOnButton)
		else:
			self.fogModeButtonList[0].SAFE_SetEvent(self.__OnClickFogModeLevel0Button)
			self.fogModeButtonList[1].SAFE_SetEvent(self.__OnClickFogModeLevel1Button)
			self.fogModeButtonList[2].SAFE_SetEvent(self.__OnClickFogModeLevel2Button)

		if not app.ENABLE_DISABLE_SOFTWARE_TILING:
			self.tilingModeButtonList[0].SAFE_SetEvent(self.__OnClickTilingModeCPUButton)
			self.tilingModeButtonList[1].SAFE_SetEvent(self.__OnClickTilingModeGPUButton)

			self.tilingApplyButton.SAFE_SetEvent(self.__OnClickTilingApplyButton)

			self.__SetCurTilingMode()

		self.__ClickRadioButton(self.fogModeButtonList, constInfo.GET_FOG_LEVEL_INDEX())
		self.__ClickRadioButton(self.cameraModeButtonList, constInfo.GET_CAMERA_MAX_DISTANCE_INDEX())

		if app.ENABLE_FOG_FIX:
			self.__ClickRadioButton(self.fogButtonList, background.GetFogMode())

		if app.ENABLE_SHADOW_RENDER_QUALITY_OPTION:
			self.shadowQualityButtonList[background.SHADOW_QUALITY_BAD].SAFE_SetEvent(self.__OnClickChangeShadowQuality, background.SHADOW_QUALITY_BAD)
			self.shadowQualityButtonList[background.SHADOW_QUALITY_AVERAGE].SAFE_SetEvent(self.__OnClickChangeShadowQuality, background.SHADOW_QUALITY_AVERAGE)
			self.shadowQualityButtonList[background.SHADOW_QUALITY_GOOD].SAFE_SetEvent(self.__OnClickChangeShadowQuality, background.SHADOW_QUALITY_GOOD)
			self.__ClickRadioButton(self.shadowQualityButtonList, systemSetting.GetShadowQualityLevel())

			self.shadowTargetButtonList[background.SHADOW_TARGET_NONE].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_NONE)
			self.shadowTargetButtonList[background.SHADOW_TARGET_GROUND].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_GROUND)
			self.shadowTargetButtonList[background.SHADOW_TARGET_GROUND_AND_SOLO].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_GROUND_AND_SOLO)
			self.shadowTargetButtonList[background.SHADOW_TARGET_ALL].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_ALL)
			self.__ClickRadioButton(self.shadowTargetButtonList, systemSetting.GetShadowTargetLevel())

		if app.ENABLE_GRAPHIC_ON_OFF:
			self.__ClickRadioButton(self.effectLevelButtonList, systemSetting.GetEffectLevel())
			self.__ClickRadioButton(self.privateShopLevelButtonList, systemSetting.GetPrivateShopLevel())
			self.__ClickRadioButton(self.dropItemLevelButtonList, systemSetting.GetDropItemLevel())

			self.__ClickRadioButton(self.petStatusButtonList, systemSetting.IsPetStatus())
			self.__ClickRadioButton(self.npcNameStatusButtonList, systemSetting.IsNpcNameStatus())

		if app.ENABLE_FOV_OPTION:
			if self.fovController:
				self.fovController.SetSliderPos(float(systemSetting.GetFOV()) / float(app.MAX_CAMERA_PERSPECTIVE))
				self.fovController.SetEvent(ui.__mem_func__(self.__OnChangeFOV))

			if self.fovValueText:
				self.fovValueText.SetText(str(int(systemSetting.GetFOV())))

			if self.fovResetButton:
				self.fovResetButton.SetEvent(ui.__mem_func__(self.__OnClickFOVResetButton))

		if self.language_select_button:
			self.language_select_button.SetEvent(ui.__mem_func__(self.__OnClickLanguageSelectButton))
			self.cur_language_text_window.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.__OnClickLanguageSelectButton))

		if self.language_change_button:
			self.language_change_button.SetEvent(ui.__mem_func__(self.__OnClickLanguageChangeButton))

		self.mouse_over_image = self.GetChild("mouse_over_image")
		self.mouse_over_image.Hide()

		if musicInfo.fieldMusic == musicInfo.METIN2THEMA:
			self.selectMusicFile.SetText(uiSelectMusic.DEFAULT_THEMA)
		else:
			self.selectMusicFile.SetText(musicInfo.fieldMusic[:MUSIC_FILENAME_MAX_LEN])

		if app.ENABLE_GRAPHIC_ON_OFF:
			for i in range(GRAPHIC_LEVEL_MAX_NUM):
				self.effectLevelButtonList[i].SAFE_SetEvent(self.__OnClickEffectLevelButton, i)
				self.privateShopLevelButtonList[i].SAFE_SetEvent(self.__OnClickPrivateShopLevelButton, i)
				self.dropItemLevelButtonList[i].SAFE_SetEvent(self.__OnClickDropItemLevelButton, i)

			self.petStatusButtonList[0].SAFE_SetEvent(self.__OnClickPetStatusButton, 0)
			self.petStatusButtonList[1].SAFE_SetEvent(self.__OnClickPetStatusButton, 1)

			self.npcNameStatusButtonList[0].SAFE_SetEvent(self.__OnClickNpcNameStatusButton, 0)
			self.npcNameStatusButtonList[1].SAFE_SetEvent(self.__OnClickNpcNameStatusButton, 1)

			self.effectLevelApplyButton.SAFE_SetEvent(self.__OnClickEffectApplyButton)
			self.privateShopLevelApplyButton.SAFE_SetEvent(self.__OnClickPrivateShopApplyButton)
			self.dropItemLevelApplyButton.SAFE_SetEvent(self.__OnClickDropItemApplyButton)

	if not app.ENABLE_DISABLE_SOFTWARE_TILING:
		def __OnClickTilingModeCPUButton(self):
			self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_CPU_TILING_1)
			self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_CPU_TILING_2)
			self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_CPU_TILING_3)
			self.__SetTilingMode(0)

		def __OnClickTilingModeGPUButton(self):
			self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_GPU_TILING_1)
			self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_GPU_TILING_2)
			self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_GPU_TILING_3)
			self.__SetTilingMode(1)

		def __OnClickTilingApplyButton(self):
			self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_TILING_EXIT)
			if 0 == self.tilingMode:
				background.EnableSoftwareTiling(1)
			else:
				background.EnableSoftwareTiling(0)

			net.ExitGame()

	def __OnClickChangeMusicButton(self):
		if not self.musicListDlg:
			self.musicListDlg = uiSelectMusic.FileListDialog()
			self.musicListDlg.SAFE_SetSelectEvent(self.__OnChangeMusic)

		self.musicListDlg.Open()

	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			selButton = buttonList[buttonIndex]
		except IndexError:
			return

		for eachButton in buttonList:
			eachButton.SetUp()

		selButton.Down()

	if not app.ENABLE_DISABLE_SOFTWARE_TILING:
		def __SetTilingMode(self, index):
			self.__ClickRadioButton(self.tilingModeButtonList, index)
			self.tilingMode = index

	def __SetCameraMode(self, index):
		constInfo.SET_CAMERA_MAX_DISTANCE_INDEX(index)
		self.__ClickRadioButton(self.cameraModeButtonList, index)

	def __SetFogLevel(self, index):
		constInfo.SET_FOG_LEVEL_INDEX(index)
		self.__ClickRadioButton(self.fogModeButtonList, index)

	def __OnClickCameraModeShortButton(self):
		self.__SetCameraMode(0)

	def __OnClickCameraModeLongButton(self):
		self.__SetCameraMode(1)

	def __OnClickFogModeLevel0Button(self):
		self.__SetFogLevel(0)

	def __OnClickFogModeLevel1Button(self):
		self.__SetFogLevel(1)

	def __OnClickFogModeLevel2Button(self):
		self.__SetFogLevel(2)

	if app.ENABLE_FOG_FIX:
		def __OnClickFogModeOnButton(self):
			systemSetting.SetFogMode(True)
			background.SetFogMode(True)
			self.__ClickRadioButton(self.fogButtonList, 1)

		def __OnClickFogModeOffButton(self):
			systemSetting.SetFogMode(False)
			background.SetFogMode(False)
			self.__ClickRadioButton(self.fogButtonList, 0)

	def __OnChangeMusic(self, fileName):
		self.selectMusicFile.SetText(fileName[:MUSIC_FILENAME_MAX_LEN])

		if musicInfo.fieldMusic != "":
			snd.FadeOutMusic("BGM/"+ musicInfo.fieldMusic)

		if fileName == uiSelectMusic.DEFAULT_THEMA:
			musicInfo.fieldMusic = musicInfo.METIN2THEMA
		else:
			musicInfo.fieldMusic = fileName

		musicInfo.SaveLastPlayFieldMusic()

		if musicInfo.fieldMusic != "":
			snd.FadeInMusic("BGM/" + musicInfo.fieldMusic)

		def __OnClickSnowTextureModeOffButton(self):
			self.__ClickRadioButton(self.snowTextureModeButtonList, 0)
			self.__SetSnowTextureMode(0)

		def __OnClickSnowTextureModeOnButton(self):
			self.__ClickRadioButton(self.snowTextureModeButtonList, 1)
			self.__SetSnowTextureMode(1)

		#def __SetSnowMode(self, index):
		#	systemSetting.SetSnowModeOption(index)

		def __SetSnowTextureMode(self, index):
			systemSetting.SetSnowTextureModeOption(index)

		def __SetNightMode(self, index):
			systemSetting.SetNightModeOption(index)

			if not background.GetDayMode():
				return

			if not background.IsBoomMap():
				return

			if 1 == index:
				self.curtain.SAFE_FadeOut(self.__DayMode_OnCompleteChangeToDark)
			else:
				self.curtain.SAFE_FadeOut(self.__DayMode_OnCompleteChangeToLight)

		def __DayMode_OnCompleteChangeToLight(self):
			background.ChangeEnvironmentData(background.DAY_MODE_LIGHT)
			self.curtain.FadeIn()

		def __DayMode_OnCompleteChangeToDark(self):
			background.RegisterEnvironmentData(background.DAY_MODE_DARK, constInfo.ENVIRONMENT_NIGHT)
			background.ChangeEnvironmentData(background.DAY_MODE_DARK)
			self.curtain.FadeIn()

	if app.ENABLE_SHADOW_RENDER_QUALITY_OPTION:
		def __OnClickChangeShadowQuality(self, shadow_quality):
			self.__ClickRadioButton(self.shadowQualityButtonList, shadow_quality)
			self.__SetShadowQualityLevel(shadow_quality)

		def __SetShadowQualityLevel(self, index):
			systemSetting.SetShadowQualityLevel(index)
			background.SetShadowQualityLevel(index)

		def __OnClickChangeShadowTarget(self, shadow_target):
			self.__ClickRadioButton(self.shadowTargetButtonList, shadow_target)
			self.__SetShadowTargetLevel(shadow_target)

		def __SetShadowTargetLevel(self, index):
			systemSetting.SetShadowTargetLevel(index)
			background.SetShadowTargetLevel(index)

	if app.ENABLE_GRAPHIC_ON_OFF:
		# Effect
		def __OnClickEffectLevelButton(self, index):
			self.__ClickRadioButton(self.effectLevelButtonList, index)
			self.effectLevel = index

		def __OnClickEffectApplyButton(self):
			systemSetting.SetEffectLevel(self.effectLevel)

		# PrivateShop
		def __OnClickPrivateShopLevelButton(self, privateShopLevelIdx):
			self.__ClickRadioButton(self.privateShopLevelButtonList, privateShopLevelIdx)
			self.privateShopLevel = privateShopLevelIdx

		def __OnClickPrivateShopApplyButton(self):
			systemSetting.SetPrivateShopLevel(self.privateShopLevel)

		# DropItem
		def __OnClickDropItemLevelButton(self, index):
			self.__ClickRadioButton(self.dropItemLevelButtonList, index)
			self.dropItemLevel = index

		def __OnClickDropItemApplyButton(self):
			systemSetting.SetDropItemLevel(self.dropItemLevel)

		def __OnClickPetStatusButton(self, flag):
			self.__ClickRadioButton(self.petStatusButtonList, flag)
			systemSetting.SetPetStatusFlag(flag)
			self.RefreshPetStatus()
		
		def RefreshPetStatus(self):
			if systemSetting.IsPetStatus():
				self.petStatusButtonList[0].SetUp()
				self.petStatusButtonList[1].Down()
			else:
				self.petStatusButtonList[0].Down()
				self.petStatusButtonList[1].SetUp()

		def __OnClickNpcNameStatusButton(self, flag):
			self.__ClickRadioButton(self.npcNameStatusButtonList, flag)
			systemSetting.SetNpcNameStatusFlag(flag)
			self.RefreshNpcNameStatus()

		def RefreshNpcNameStatus(self):
			if systemSetting.IsNpcNameStatus():
				self.npcNameStatusButtonList[0].SetUp()
				self.npcNameStatusButtonList[1].Down()
			else:
				self.npcNameStatusButtonList[0].Down()
				self.npcNameStatusButtonList[1].SetUp()

	if app.ENABLE_HIDE_SKILL_EFFECT:
		def __OnClickBLEffectButton(self, Index):
			systemSetting.SetBLEffectOption(Index, not systemSetting.GetBLEffectOption(Index))
			self.__RefreshBLEffectButton()
		
		def __RefreshBLEffectButton(self):
			for (Index, Button) in enumerate(self.BLEffectGroupList):
				if systemSetting.GetBLEffectOption(Index):
					Button.SetUp()
				else:
					Button.Down()

	if app.ENABLE_FOV_OPTION:
		def __OnChangeFOV(self):
			pos = self.fovController.GetSliderPos()
			systemSetting.SetFOV(pos * float(app.MAX_CAMERA_PERSPECTIVE))

			if self.fovValueText:
				self.fovValueText.SetText(str(int(systemSetting.GetFOV())))

		def __OnClickFOVResetButton(self):
			self.fovController.SetSliderPos(float(app.DEFAULT_CAMERA_PERSPECTIVE) / float(app.MAX_CAMERA_PERSPECTIVE))
			systemSetting.SetFOV(float(app.DEFAULT_CAMERA_PERSPECTIVE))

			if self.fovValueText:
				self.fovValueText.SetText(str(int(systemSetting.GetFOV())))

	def OnChangeMusicVolume(self):
		pos = self.ctrlMusicVolume.GetSliderPos()
		snd.SetMusicVolume(pos * net.GetFieldMusicVolume())
		systemSetting.SetMusicVolume(pos)

	def OnChangeSoundVolume(self):
		pos = self.ctrlSoundVolume.GetSliderPos()
		snd.SetSoundVolumef(pos)
		systemSetting.SetSoundVolumef(pos)

	def OnChangeShadowQuality(self):
		pos = self.ctrlShadowQuality.GetSliderPos()
		systemSetting.SetShadowLevel(int(pos / 0.2))

	def OnCloseInputDialog(self):
		self.inputDialog.Close()
		self.inputDialog = None
		return True

	def OnCloseQuestionDialog(self):
		self.questionDialog.Close()
		self.questionDialog = None
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Show(self):
		ui.ScriptWindow.Show(self)
		self.IsShow = True

	def IsShowWindow(self):
		return self.IsShow

	def Close(self):
		if not app.ENABLE_DISABLE_SOFTWARE_TILING:
			self.__SetCurTilingMode()
		self.Hide()
		self.IsShow = False

		if self.questionDialog:
			self.OnCloseQuestionDialog()

		self.__LanguageSelectShowHide(False)

	if not app.ENABLE_DISABLE_SOFTWARE_TILING:
		def __SetCurTilingMode(self):
			if background.IsSoftwareTiling():
				self.__SetTilingMode(0)
			else:
				self.__SetTilingMode(1)

	def __NotifyChatLine(self, text):
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	""" Based on dumped meta data"""
	# YMD.2019.12.32.Owsap - Multi Language
	def __AdjustLanguageSelectWindowPosition(self):
		x, y = self.GetGlobalPosition()

		(lx, ly) = self.language_change_window.GetLocalPosition()
		if self.language_select_window_bar:
			self.language_select_window_bar.SetPosition(x + lx + 30, y + ly + 36)

	def __CreateLanguageSelectWindow(self):
		if self.language_button_dict:
			return

		languageList = LOCALE_LANG_DICT
		if not LOCALE_LANG_DICT:
			return

		self.cur_language_text.SetText(LOCALE_LANG_DICT[self.__GetCurLanguageKey()]["name"])

		button_height = 16
		dict_len = MIN_LOCALE_SCROLL + 1
		self.language_select_window_height = dict_len * button_height - 15

		self.language_select_window_bar = ui.Bar("TOP_MOST")
		self.language_select_window_bar.SetSize(210, self.language_select_window_height)
		self.language_select_window_bar.Hide()

		for index, key in enumerate(LOCALE_LANG_DICT):
			if key > MIN_LOCALE_SCROLL:
				continue

			button = ui.Button()
			button.SetParent(self.language_select_window_bar)
			button.SetPosition(0, button_height * index)

			if 1 == dict_len:
				button.SetUpVisual("d:/ymir work/ui/quest_re/button_middle.sub")
				button.SetDownVisual("d:/ymir work/ui/quest_re/button_middle.sub")
				button.SetOverVisual("d:/ymir work/ui/quest_re/button_middle.sub")
			elif index == 0:
				button.SetUpVisual("d:/ymir work/ui/quest_re/button_middle.sub")
				button.SetDownVisual("d:/ymir work/ui/quest_re/button_middle.sub")
				button.SetOverVisual("d:/ymir work/ui/quest_re/button_middle.sub")
			elif index == MIN_LOCALE_SCROLL - 1:
				button.SetUpVisual("d:/ymir work/ui/quest_re/button_bottom.sub")
				button.SetDownVisual("d:/ymir work/ui/quest_re/button_bottom.sub")
				button.SetOverVisual("d:/ymir work/ui/quest_re/button_bottom.sub")
			else:
				button.SetUpVisual("d:/ymir work/ui/quest_re/button_middle.sub")
				button.SetDownVisual("d:/ymir work/ui/quest_re/button_middle.sub")
				button.SetOverVisual("d:/ymir work/ui/quest_re/button_middle.sub")

			button.SetEvent(ui.__mem_func__(self.__OnClickLanguageSelect), key)
			button.SetOverEvent(ui.__mem_func__(self.__OnClickLanguageButtonOver), key)
			button.SetOverOutEvent(ui.__mem_func__(self.__OnClickLanguageButtonOverOut), key)
			button.SetText(LOCALE_LANG_DICT[key]["name"])
			button.Hide()

			self.language_button_dict[key] = button

		self.mouse_over_image.SetParent(self.language_select_window_bar)

		## ScrollBar
		self.language_scrollbar = ui.ScrollBar()
		self.language_scrollbar.SetParent(self.language_select_window_bar)

		self.language_scrollbar.SetUpButtonUpVisual("d:/ymir work/ui/game/mailbox/scroll_up_arrow_button_default.sub")
		self.language_scrollbar.SetUpButtonOverVisual("d:/ymir work/ui/game/mailbox/scroll_up_arrow_button_over.sub")
		self.language_scrollbar.SetUpButtonDownVisual("d:/ymir work/ui/game/mailbox/scroll_up_arrow_button_down.sub")
		self.language_scrollbar.SetDownButtonUpVisual("d:/ymir work/ui/game/mailbox/scroll_down_arrow_button_default.sub")
		self.language_scrollbar.SetDownButtonOverVisual("d:/ymir work/ui/game/mailbox/scroll_down_arrow_button_over.sub")
		self.language_scrollbar.SetDownButtonDownVisual("d:/ymir work/ui/game/mailbox/scroll_down_arrow_button_down.sub")

		self.language_scrollbar.SetPosition(210 - 16, 0)
		self.language_scrollbar.SetScrollBarSize(self.language_select_window_height)

		self.language_scrollbar_diff = len(LOCALE_LANG_DICT) - MIN_LOCALE_SCROLL
		if self.language_scrollbar_diff > 0:
			stepSize = 1.0 / self.language_scrollbar_diff
			self.language_scrollbar.SetScrollStep(stepSize)
		self.language_scrollbar.SetScrollEvent(ui.__mem_func__(self.__OnLanguageSelectScroll))
		if dict_len > MIN_LOCALE_SCROLL:
			self.language_scrollbar.Show()
		else:
			self.language_scrollbar.Hide()

		self.__AdjustLanguageSelectWindowPosition()

	def __GetCurLanguageKey(self):
		for key in LOCALE_LANG_DICT.keys():
			localeName = LOCALE_LANG_DICT[key]["locale"]
			if app.GetLocaleName() == localeName:
				return key

	def __GetStringCurLanguage(self):
		for key in LOCALE_LANG_DICT.keys():
			localeName = LOCALE_LANG_DICT[key]["locale"]
			if app.GetLocaleName() == localeName:
				return localeName

	def __LanguageSelectShowHide(self, is_show):
		if True == is_show:
			self.language_select_list_open = True

			if self.language_select_window_bar:
				self.language_select_window_bar.SetSize(210, self.language_select_window_height)
				self.language_select_window_bar.Show()

			for button in self.language_button_dict.values():
				button.Show()

			if self.language_scrollbar:
				self.language_scrollbar.Show()
		else:
			self.language_select_list_open = False

			if self.language_select_window_bar:
				self.language_select_window_bar.SetSize(210, 0)

			for button in self.language_button_dict.values():
				button.Hide()

			if self.language_scrollbar:
				self.language_scrollbar.Hide()

	def __OnClickLanguageButtonOver(self, index):
		if not self.mouse_over_image:
			return

		button = self.language_button_dict.get(index, 0)
		if 0 == button:
			return

		(button_x, button_y) = button.GetLocalPosition()
		self.mouse_over_image.SetPosition(button_x, button_y)
		self.mouse_over_image.Show()

	def __OnClickLanguageButtonOverOut(self, index):
		if not self.mouse_over_image:
			return

		self.mouse_over_image.Hide()

	def __OnClickLanguageChangeButton(self):
		if self.__GetCurLanguageKey() == self.selected_language:
			return

		if self.selected_language != 0:
			self.ConfirmLanguageChange()

	def __OnClickLanguageSelect(self, index):
		for button in self.language_button_dict.values():
			button.Hide()

		self.__LanguageSelectShowHide(False)

		self.selected_language = index + self.language_scrollbar_pos

		if self.cur_language_text:
			self.cur_language_text.SetText(LOCALE_LANG_DICT[self.selected_language]["name"])

	def __OnClickLanguageSelectButton(self):
		self.__CreateLanguageSelectWindow()

		if self.language_select_list_open:
			self.__LanguageSelectShowHide(False)
		else:
			self.__LanguageSelectShowHide(True)

	def __OnLanguageSelectScroll(self):
		self.language_scrollbar_pos = int(self.language_scrollbar.GetPos() * self.language_scrollbar_diff)
		try:
			for key in LOCALE_LANG_DICT.keys():
				pos = key + self.language_scrollbar_pos
				localeName = LOCALE_LANG_DICT[min(pos, len(LOCALE_LANG_DICT))]["name"]
				self.language_button_dict[key].SetText(localeName)
		except KeyError:
			pass

	def __SaveLoca(self, code_page, locale):
		if app.SetLoca(code_page, locale):
			return True

		return False

	def OnTop(self):
		if self.language_select_window_bar:
			self.language_select_window_bar.SetTop()

	def OnMoveWindow(self, x, y):
		self.__AdjustLanguageSelectWindowPosition()

	def ConfirmLanguageChange(self):
		questionDialog = uiCommon.QuestionDialog2()
		questionDialog.SetText1(localeInfo.RESTART_CLIENT_DO_YOU_ACCEPT_1)
		questionDialog.SetText2(localeInfo.RESTART_CLIENT_DO_YOU_ACCEPT_2)
		questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnAcceptLanguageChange))
		questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
		questionDialog.SetWidth(450)
		questionDialog.Open()
		self.questionDialog = questionDialog

	def OnEndCountDown(self):
		net.Disconnect()
		app.ShellExecute(app.GetName())
		app.Exit()

	def OnPressExitKey(self):
		pass

	def OnAcceptLanguageChange(self):
		self.OnCloseQuestionDialog()

		if self.selected_language != 0:
			locale = LOCALE_LANG_DICT[self.selected_language]["locale"]
			code_page = LOCALE_LANG_DICT[self.selected_language]["code_page"]

			if self.__SaveLoca(code_page, locale):
				net.SendChangeLanguagePacket(self.selected_language)

				import introLogin
				self.popUpTimer = introLogin.ConnectingDialog()
				self.popUpTimer.Open(3.0)
				self.popUpTimer.SetText(localeInfo.LEFT_TIME)
				self.popUpTimer.SAFE_SetTimeOverEvent(self.OnEndCountDown)
				self.popUpTimer.SAFE_SetExitEvent(self.OnPressExitKey)
		else:
			pass # No language selected
