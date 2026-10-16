#static
import ui, app, background, constInfo, uiPhaseCurtain, uiPrivateShopBuilder, uiSelectMusic, musicInfo, localeInfo, uiScriptLocale

# dynamic
import player
import net
import dbg, chat, wndMgr, systemSetting, snd, pack
import osfInfo
import interfaceModule
import cfg
import uikeybindings
import uimetinqueueappearance
from systemnotificationlocale import Text as NotificationText
from uicrimsonember import SettingsScrollBar

if app.ENABLE_FONT_OPTION:
	import os
	import fontconfig

MUSIC_FILENAME_MAX_LEN = 25
FPS_LIMITS = (60, 120, 180, 240)
WORLD_GRAPHICS_PROFILES = (0, 1, 2, 3)
WORLD_ANTIALIAS_MODES = (0, 1, 2, 3)
WORLD_RAIN_LEVELS = (0, 1, 2, 3)
GRAPHICS_CATEGORY_POSITIONS = (252, 277, 302, 327, 352)

if app.ENABLE_GRAPHIC_ON_OFF:
	GRAPHIC_LEVEL_MAX_NUM = 5
if app.ENABLE_FONT_OPTION:
	FONT_LEVEL_MAX_NUM = len(fontconfig.FONT_LEVELS)

blockMode = 0
IMG_DIR = "d:/ymir work/ui/game/crimson_ember/gameoption/"
_SKY_BASE = "d:/ymir work/environment/jtx_skybox/"
SKYBOX_PRESETS = [
	(0,  None),
	(20, _SKY_BASE + "env_01.msenv"),
	(21, _SKY_BASE + "env_02.msenv"),
	(22, _SKY_BASE + "env_03.msenv"),
	(23, _SKY_BASE + "env_04.msenv"),
	(24, _SKY_BASE + "env_05.msenv"),
	(25, _SKY_BASE + "env_06.msenv"),
	(26, _SKY_BASE + "env_07.msenv"),
	(27, _SKY_BASE + "env_08.msenv"),
	(28, _SKY_BASE + "env_09.msenv"),
	(29, _SKY_BASE + "env_10.msenv"),
	(30, _SKY_BASE + "env_11.msenv"),
]


def _GetOptionLocale(name, fallback):
	return getattr(uiScriptLocale, name, fallback)


def _CreateKeybindingsPage(scriptWindow):
	page = None
	try:
		page = uikeybindings.KeybindingsPage()
		page.Bind(scriptWindow)
		return page
	except Exception as error:
		dbg.TraceError("[GameOption] Keybindings page unavailable: %s" % error)
		if page:
			try:
				page.Destroy()
			except Exception:
				pass
		return None


def _GetSkyboxLabel(slotIndex):
	if slotIndex <= 0:
		return uiScriptLocale.OPTION_GAMEOPTION_SKYBOX_DEFAULT_MAP
	try:
		return uiScriptLocale.OPTION_GAMEOPTION_SKYBOX_ENV_NAME % slotIndex
	except TypeError:
		return uiScriptLocale.OPTION_GAMEOPTION_SKYBOX_ENV_NAME


def ApplyGraphicsConfig():
	try:
		slot = int(systemSetting.GetSkyboxPreset())
	except (AttributeError, RuntimeError):
		return
	if slot < 0 or slot >= len(SKYBOX_PRESETS):
		slot = 0
	engineSlot, msenvPath = SKYBOX_PRESETS[slot]
	if not msenvPath:
		try:
			background.ClearUserEnvironmentSlot()
		except (AttributeError, RuntimeError):
			pass
		return
	if not app.IsExistFile(msenvPath):
		return
	try:
		background.RegisterEnvironmentData(engineSlot, msenvPath)
		# Native code recomposes the selected sky over the active map/event
		# environment. A legacy SetEnvironmentData(0) refresh here would replace
		# that authoritative base and make the original look unrecoverable.
		background.SetUserEnvironmentSlot(engineSlot)
	except (AttributeError, RuntimeError):
		pass

class GameOptionWindow(ui.BoardWithTitleBar):
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)
	def Destroy(self):
		metin_queue_controller = getattr(self, "metinQueueAppearanceController", None)
		if metin_queue_controller:
			metin_queue_controller.Destroy()
		self.metinQueueAppearanceController = None
		keybindings_page = getattr(self, "keybindingsPage", None)
		if keybindings_page:
			keybindings_page.Destroy()
		self.keybindingsPage = None
		self.pvpModeButtonDict={}
		self.blockButtonList=[]
		self.viewChatButtonList = []
		self.countryFlagButtonList = []
		self.nameColorModeButtonList = []
		self.viewTargetBoardButtonList=[]
		self.alwaysShowNameButtonList=[]
		self.familyNameButtonList = []
		self.showDamageButtonList=[]
		self.showsalesTextButtonList=[]
		self.cameraModeButtonList=[]
		self.fpsLimitButtonList=[]
		self.showFPSButtonList=[]
		self.vsyncButtonList=[]
		self.dogModeButtonList=[]
		self.worldGraphicsProfileButtonList=[]
		self.worldAntialiasButtonList=[]
		self.worldRainButtonList=[]
		self.worldRainFxButtonList=[]
		self.worldGrassButtonList=[]
		self.worldGrassRadiusSlider=None
		self.worldGrassRadiusValueText=None
		self.worldLightsButtonList=[]
		self.worldReflectionsButtonList=[]
		self.worldPostProcessingButtonList=[]
		self.worldGraphicsStatusText=None
		self.worldGraphicsFallbackText=None
		self.worldGraphicsCapabilityText=None
		self.worldGraphicsResourceWarningText=None
		self.worldGraphicsRecommendedButton=None
		self.worldGraphicsNextStatusRefresh=0.0
		if app.ENABLE_FOG_FIX:
			self.fogButtonList = []

		self.fullMapRenderButtonList = []

		if app.ENABLE_FOV_OPTION:
			self.fovController = None
			self.fovResetButton = None
			self.fovValueText = None

		if app.ENABLE_SHARPNESS:
			self.sharpnessSlider = None
			self.sharpnessResetButton = None
			self.sharpnessValueText = None

		self.skyboxButtonList = []
		self.skyboxCurrentText = None

		self._skyboxLoadedEngineSlots = set()
		if app.ENABLE_QUEST_OPTION:
			self.questModeButtonList = []

		if app.ENABLE_OUTLINE_NAME_SHADOW:
			self.showOutlinedNamesList = []

		if app.ENABLE_HIDE_AFFECT_ICONS:
			self.showAffectIconsList = []

		if app.ENABLE_FONT_OPTION:
			self.fontLevel = 0
			self.fontLevelButtonList = []

		if app.ENABLE_GRAPHIC_ON_OFF:
			self.effectLevel = 0
			self.effectLevelButtonList = []

			self.dropItemLevel = 0
			self.dropItemLevelButtonList = []

			self.npcNameStatusButtonList = []

		if app.WJ_SHOW_MOB_INFO:
			self.showMobInfoButtonList = []

		if app.ENABLE_GRAPHIC_ON_OFF:
			self.petStatusButtonList = 0
			self.MountStatusButtonList = 0
			self.SupportStatusButtonList = 0
			self.ShopStatusButtonList = 0

		if app.ENABLE_HIDE_SKILL_EFFECT:
			self.BLEffectGroupList = []

		self.ctrlSoundVolume = None
		self.ctrlMusicVolume = None
		self.selectMusicFile = None
		self.musicListDlg = None
		if app.ENABLE_SHADOW_RENDER_QUALITY_OPTION:
			self.shadowQualityButtonList = []
			self.shadowTargetButtonList = []

		if app.ENABLE_SCALE_OPTION:
			self.stoneScaling = None

		if app.ENABLE_SCALE_DAMAGE_TEXT:
			self.damageScaling = None

		if app.ENABLE_AREA_OPTIMISATION:
			self.objectScaling=[]

		if app.ENABLE_DROP_INFO_WINDOW:
			self.dropButtonList = {}
		self.dropTrackerPlacementButtonList = []
		self.dropTrackerPlacementEditButton = None
		self.dropTrackerPlacementResetButton = None
		self.costumeInventoryModeButtonList = []

		#PICKUP
		self.cfgPickupLoaded = False
		self.cfgPickupMode = 1
		self.cfgPickupBlockClass = []
		self.cfgPickupMinLvl = 1
		self.cfgPickupMaxLvl = 150
		self.cfgPickupBlockWeapon = []
		self.cfgPickupBlockArmor = []
		
		self.pickupModeButton = []
		self.pickupBlockClassBtn = []
		self.pickupBlockWeaponBtn = []
		self.pickupBlockArmorBtn = []
		self.pickupMinLvl = None
		self.pickupMaxLvl = None
		#PICKUP

		for j in range(10):
			for x in range(10):
				if "optionWindow%d%d"%(j,x) in self.children:
					window = self.children["optionWindow%d%d"%(j,x)]
					if window:
						window.Hide()
						window.scrollBar = None
						window.ClearDictionary()
						window.Destroy()
		self.children = {}
		self.Hide()
		self.searchEdit = None

	def __init__(self):
		self.keybindingsPage = None
		self.metinQueueAppearanceController = None
		self.searchEdit = None
		ui.BoardWithTitleBar.__init__(self)
		self.children = {}
		self.Destroy()
		self.__LoadWindow()
		self.SetTitleName(uiScriptLocale.OPTION_TITLE)

	def __LoadWindow(self):
		self.AddFlag("movable")
		self.AddFlag("attach")
		self.AddFlag("animate")
		# Native SetTop() only reorders windows carrying FLAG_FLOAT.  Game
		# options are opened from an older, persistent system-dialog object,
		# so without this flag another root UI window can consume Escape first.
		self.AddFlag("float")
		self.SetSize(615, 450)
		self.searchEntries = []
		self.searchEntries.append((1, 1, NotificationText("NAVIGATION")))

		option_data = [
			(uiScriptLocale.OPTION_NEW_GAME, 0, [
				(uiScriptLocale.OPTION_NEW_GENERAL, 0),
				(uiScriptLocale.OPTION_NEW_PICKUP, 1),
				(_GetOptionLocale("OPTION_NEW_KEYBINDINGS", "Keybindings"), 2),
				(_GetOptionLocale("OPTION_METIN_QUEUE_CATEGORY", u"Fronta meteorů"), 3),
			]),
			(uiScriptLocale.OPTION_NEW_GRAPHICS, 1, [
				(uiScriptLocale.OPTION_NEW_GENERAL, 0),
				(uiScriptLocale.OPTION_NEW_INTERFACE, 1),
				(uiScriptLocale.OPTION_NEW_PERFORMANCE, 2),
			]),
			(uiScriptLocale.OPTION_NEW_SOUND, 2, [
				(uiScriptLocale.OPTION_NEW_GENERAL, 0),
			]),
		]
		if app.ENABLE_POSTPROCESSING:
			option_data[1][2].append((uiScriptLocale.OPTION_NEW_VISUAL_EFFECTS, 3))
		if getattr(app, "ENABLE_GRAPHICS_ENHANCEMENT", 0):
			option_data[1][2].append((
				_GetOptionLocale("OPTION_WORLD_GRAPHICS_CATEGORY", "World renderer"),
				4))

		bg = ui.ImageBox()
		bg.SetParent(self)
		bg.AddFlag("attach")
		bg.SetPosition(7, 34)
		bg.LoadImage(IMG_DIR + "bg.tga")
		bg.Show()
		self.children["bg"] = bg

		searchBG = ui.ImageBox()
		searchBG.SetParent(self)
		searchBG.SetPosition(14, 41)
		searchBG.LoadImage(IMG_DIR + "search_bg.tga")
		searchBG.Show()
		self.children["searchBG"] = searchBG

		searchEdit = ui.EditLine()
		searchEdit.SetParent(self)
		searchEdit.SetPosition(22, 46)
		searchEdit.SetSize(154, 16)
		searchEdit.SetMax(40)
		searchEdit.SetInfoMessage(getattr(localeInfo, "ITEMSHOP_ITEMSEARCH_DEFAULT_TEXT", "Search..."))
		searchEdit.SAFE_SetReturnEvent(self.__SearchOptions)
		searchEdit.SetEscapeEvent(self.OnPressEscapeKey)
		searchEdit.Show()
		self.searchEdit = searchEdit
		self.children["searchEdit"] = searchEdit

		searchButton = ui.Button()
		searchButton.SetParent(self)
		searchButton.SetPosition(183, 43)
		searchButton.SetUpVisual(IMG_DIR + "search_btn_0.tga")
		searchButton.SetOverVisual(IMG_DIR + "search_btn_1.tga")
		searchButton.SetDownVisual(IMG_DIR + "search_btn_2.tga")
		searchButton.SAFE_SetEvent(self.__SearchOptions)
		searchButton.Show()
		self.children["searchButton"] = searchButton

		extraGraphicsRows = max(0, len(option_data[1][2]) - 4)
		soundOffset = extraGraphicsRows * 25
		title_positions = {0: 74, 1: 214, 2: 354 + soundOffset}
		category_positions = {
			0: (112, 137, 162, 187),
			1: GRAPHICS_CATEGORY_POSITIONS,
			2: (393 + soundOffset,),
		}
		visual_prefix = {0: "first", 1: "middle", 2: "end"}

		for key, optionIndex, optionTitles in option_data:
			titleButton = ui.RadioButton()
			titleButton.SetParent(self)
			prefix = visual_prefix[optionIndex]
			titleButton.SetUpVisual(IMG_DIR + prefix + "_title_0.tga")
			titleButton.SetOverVisual(IMG_DIR + prefix + "_title_1.tga")
			titleButton.SetDownVisual(IMG_DIR + prefix + "_title_2.tga")
			titleButton.SetPosition(14, title_positions[optionIndex])
			titleButton.SetListText(key, 58)
			titleButton.SAFE_SetEvent(self.SetOptionType, optionIndex)
			titleButton.Show()
			self.children["titleBtn%d" % optionIndex] = titleButton

			for categoryRow, (keyEx, categoryIndex) in enumerate(optionTitles):
				if categoryRow >= len(category_positions[optionIndex]):
					dbg.TraceError(
						"[GameOption] Missing sidebar position for optionIndex: %d row: %d categoryIndex: %d"
						% (optionIndex, categoryRow, categoryIndex))
					continue
				optionCategory = ui.RadioButton()
				optionCategory.SetParent(self)
				optionCategory.SetUpVisual(IMG_DIR + "category_0.tga")
				optionCategory.SetOverVisual(IMG_DIR + "category_1.tga")
				optionCategory.SetDownVisual(IMG_DIR + "category_2.tga")
				optionCategory.SetPosition(14, category_positions[optionIndex][categoryRow])
				optionCategory.SetListText(keyEx, 38)
				optionCategory.SAFE_SetEvent(self.SetCategoryTypeForOption, optionIndex, categoryIndex)
				optionCategory.Show()
				self.children["optionCategory%d%d" % (optionIndex, categoryIndex)] = optionCategory
				self.searchEntries.append((optionIndex, categoryIndex, keyEx))

				optionWindow = self.CreateOptionWindow(bg, optionIndex, categoryIndex)
				self.children["optionWindow%d%d" % (optionIndex, categoryIndex)] = optionWindow

		self.SetOptionType(0)
		self.SetCenterPosition()
		if app.ENABLE_FONT_OPTION:
			self.popupDialog = PopupDialog(self)
		self.UpdateScrollBar()
	def Open(self):
		self.RefreshBlock()
		self.__RefreshWorldGraphicsOptions()
		self.RefreshDropTrackerPlacement()
		self.RefreshCostumeInventoryMode()
		if self.keybindingsPage:
			self.keybindingsPage.BeginSession()
		if (self.metinQueueAppearanceController and
				self._IsMetinQueueAppearanceCategory()):
			self.metinQueueAppearanceController.BeginSession()
		self.Show()
		self.SetTop()
		self.SetFocus()
	def Hide(self):
		if self.keybindingsPage:
			self.keybindingsPage.Discard()
		if self.metinQueueAppearanceController:
			self.metinQueueAppearanceController.Discard()
		if self.searchEdit:
			self.searchEdit.KillFocus()
		if getattr(self, "hWnd", None):
			self.KillFocus()
		ui.BoardWithTitleBar.Hide(self)
	def OnPressEscapeKey(self):
		self.Hide()
		return True
	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			btn=buttonList[buttonIndex]
		except IndexError:
			return
		for eachButton in buttonList:
			eachButton.SetUp()
		btn.Down()

	def IsCanContinue(self, dictKey):
		if dictKey == "index":
			return True
		return False

	def SetOptionType(self, optionType, selectFirst = True):
		self.children["optionType"] = optionType
		for j in range(10):
			if "titleBtn%d" % j in self.children:
				titleBtn = self.children["titleBtn%d" % j]
				if j == optionType:
					titleBtn.Down()
				else:
					titleBtn.SetUp()
		if selectFirst:
			self.SetCategoryType(0)

	def SetCategoryTypeForOption(self, optionType, categoryType):
		self.SetOptionType(optionType, False)
		self.SetCategoryType(categoryType)

	def SetCategoryType(self, categoryType):
		for j in range(3):
			for x in range(5):
				if "optionWindow%d%d" % (j, x) in self.children:
					self.children["optionWindow%d%d" % (j, x)].Hide()

		self.children["categoryType"] = categoryType
		currentCategoryType = self.children["optionType"]
		for j in range(3):
			for x in range(5):
				name = "optionCategory%d%d" % (j, x)
				if name in self.children:
					categoryBtn = self.children[name]
					if j == currentCategoryType and x == categoryType:
						categoryBtn.Down()
					else:
						categoryBtn.SetUp()

		name = "optionWindow%d%d" % (currentCategoryType, categoryType)
		if name in self.children:
			self.children[name].Show()
		if self.metinQueueAppearanceController:
			if self._IsMetinQueueAppearanceCategory():
				self.metinQueueAppearanceController.BeginSession()
			else:
				self.metinQueueAppearanceController.Discard()
		self.UpdateScrollBar()

	def _IsMetinQueueAppearanceCategory(self):
		return (self.children.get("optionType", -1) == 0 and
			self.children.get("categoryType", -1) == 3)

	def __SearchOptions(self):
		if not self.searchEdit:
			return
		query = self.searchEdit.GetText().strip().lower()
		if not query:
			return
		for optionIndex, categoryIndex, label in self.searchEntries:
			if query in label.lower():
				self.SetCategoryTypeForOption(optionIndex, categoryIndex)
				self.searchEdit.KillFocus()
				return

	def CreateOptionWindow(self, windowBG, optionIndex, categoryIndex):
		scriptWindow = ui.ScriptWindow()
		scriptWindow.SetParent(windowBG)
		fileName = "UIScript/game_option_%d_%d.py" % (optionIndex, categoryIndex)
		pyScrLoader = ui.PythonScriptLoader()
		if pack.Exist(fileName):
			pyScrLoader.LoadScriptFile(scriptWindow, fileName)
		else:
			dbg.TraceError("[GameOption]Can't find script window for optionIndex: %d categoryIndex: %d" % (optionIndex, categoryIndex))

		if scriptWindow.GetWidth() > 0:
			scrollBar = ScrollBarNew()
			scrollBar.SetParent(scriptWindow)
			if optionIndex == 0 and categoryIndex == 2:
				legacyScrollBar = scriptWindow.GetChild2("BindingScrollBar")
				if legacyScrollBar:
					(_scrollX, scrollY) = legacyScrollBar.GetLocalPosition()
					scrollBar.SetPosition(scriptWindow.GetWidth() - scrollBar.GetWidth(), scrollY)
					scrollBar.SetScrollBarSize(legacyScrollBar.GetHeight())
					legacyScrollBar.Hide()
				scriptWindow.InsertChild("BindingScrollBar", scrollBar)
				scriptWindow.keybindingsScrollBar = scrollBar
				scriptWindow.scrollBar = None
			else:
				scrollBar.SetPosition(scriptWindow.GetWidth() - scrollBar.GetWidth(), 0)
				scrollBar.SetScrollBarSize(scriptWindow.GetHeight() - 5)
				scrollBar.Hide()
				scrollBar.SetScrollEvent(ui.__mem_func__(self.UpdateScrollBar))
				scriptWindow.scrollBar = scrollBar
				scriptWindow.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)

			self.LoadCatetoryOptions(scriptWindow, optionIndex, categoryIndex)

			for child in scriptWindow.Children:
				(_x, _y) = child.GetLocalPosition()
				child.SetPosition(_x, _y, True)
			scriptWindow.Show()
		else:
			scriptWindow.scrollBar = None
		return scriptWindow

	def LoadCatetoryOptions(self, scriptWindow, optionIndex, categoryIndex):
		# try:
		GetObject = scriptWindow.GetChild			
		if optionIndex == 0:#Game-Options

			if categoryIndex == 0:#General
				self.pvpModeButtonDict[player.PK_MODE_PEACE] = GetObject("pvp_peace")
				self.pvpModeButtonDict[player.PK_MODE_PEACE].SAFE_SetEvent(self.__OnClickPvPModePeaceButton)
				self.pvpModeButtonDict[player.PK_MODE_REVENGE] = GetObject("pvp_revenge")
				self.pvpModeButtonDict[player.PK_MODE_REVENGE].SAFE_SetEvent(self.__OnClickPvPModeRevengeButton)
				self.pvpModeButtonDict[player.PK_MODE_GUILD] = GetObject("pvp_guild")
				self.pvpModeButtonDict[player.PK_MODE_GUILD].SAFE_SetEvent(self.__OnClickPvPModeGuildButton)
				self.pvpModeButtonDict[player.PK_MODE_FREE] = GetObject("pvp_free")
				self.pvpModeButtonDict[player.PK_MODE_FREE].SAFE_SetEvent(self.__OnClickPvPModeFreeButton)
				self.__SetPeacePKMode()

				block_exchange_button = GetObject("block_exchange_button")
				block_exchange_button.SetToggleUpEvent(self.__OnClickBlockExchangeButton)
				block_exchange_button.SetToggleDownEvent(self.__OnClickBlockExchangeButton)
				self.blockButtonList.append(block_exchange_button)

				block_party_button = GetObject("block_party_button")
				block_party_button.SetToggleUpEvent(self.__OnClickBlockPartyButton)
				block_party_button.SetToggleDownEvent(self.__OnClickBlockPartyButton)
				self.blockButtonList.append(block_party_button)

				block_guild_button = GetObject("block_guild_button")
				block_guild_button.SetToggleUpEvent(self.__OnClickBlockGuildButton)
				block_guild_button.SetToggleDownEvent(self.__OnClickBlockGuildButton)
				self.blockButtonList.append(block_guild_button)

				block_whisper_button = GetObject("block_whisper_button")
				block_whisper_button.SetToggleUpEvent(self.__OnClickBlockWhisperButton)
				block_whisper_button.SetToggleDownEvent(self.__OnClickBlockWhisperButton)
				self.blockButtonList.append(block_whisper_button)

				block_friend_button = GetObject("block_friend_button")
				block_friend_button.SetToggleUpEvent(self.__OnClickBlockFriendButton)
				block_friend_button.SetToggleDownEvent(self.__OnClickBlockFriendButton)
				self.blockButtonList.append(block_friend_button)

				block_party_request_button = GetObject("block_party_request_button")
				block_party_request_button.SetToggleUpEvent(self.__OnClickBlockPartyRequest)
				block_party_request_button.SetToggleDownEvent(self.__OnClickBlockPartyRequest)
				self.blockButtonList.append(block_party_request_button)

				if app.ENABLE_VIEW_EQUIPMENT_SYSTEM:
					block_equipment_request = GetObject("block_equipment_request")
					block_equipment_request.SetToggleUpEvent(self.__OnClickBlockViewEquipmentButton)
					block_equipment_request.SetToggleDownEvent(self.__OnClickBlockViewEquipmentButton)
					self.blockButtonList.append(block_equipment_request)

				self.viewChatButtonList.append(GetObject("view_chat_on_button"))
				self.viewChatButtonList[0].SAFE_SetEvent(self.__OnClickViewChat)
				self.viewChatButtonList.append(GetObject("view_chat_off_button"))
				self.viewChatButtonList[1].SAFE_SetEvent(self.__OnClickViewChat)
				self.RefreshViewChat()

				#self.countryFlagButtonList.append(GetObject("country_flag_on"))
				#self.countryFlagButtonList[0].SAFE_SetEvent(self.__OnClickCountryFlag)
				#self.countryFlagButtonList.append(GetObject("country_flag_off"))
				#self.countryFlagButtonList[1].SAFE_SetEvent(self.__OnClickCountryFlag)
				#self.RefreshCountryFlag()

				self.nameColorModeButtonList.append(GetObject("name_color_normal"))
				self.nameColorModeButtonList[0].SAFE_SetEvent(self.__OnClickNameColorMode)
				self.nameColorModeButtonList.append(GetObject("name_color_empire"))
				self.nameColorModeButtonList[1].SAFE_SetEvent(self.__OnClickNameColorMode)
				self.RefreshNameColor()

				self.viewTargetBoardButtonList.append(GetObject("target_board_view"))
				self.viewTargetBoardButtonList[0].SAFE_SetEvent(self.__SetTargetBoardViewMode)
				self.viewTargetBoardButtonList.append(GetObject("target_board_no_view"))
				self.viewTargetBoardButtonList[1].SAFE_SetEvent(self.__SetTargetBoardViewMode)
				self.RefreshTargetBoard()
			elif categoryIndex == 1:#Pickup Options

				self.pickupModeButton.append(GetObject("pickup_all"))
				self.pickupModeButton.append(GetObject("pickup_single"))
				self.pickupModeButton[0].SAFE_SetEvent(self.__OnClickPickupAll)
				self.pickupModeButton[1].SAFE_SetEvent(self.__OnClickPickupSingle)
				
				# Block class sector
				block_warrior_button = GetObject("block_item_warrior")
				block_warrior_button.SetToggleUpEvent(lambda arg=0: self.__OnClickBlockClass(arg))
				block_warrior_button.SetToggleDownEvent(lambda arg=0: self.__OnClickBlockClass(arg))
				self.pickupBlockClassBtn.append(block_warrior_button)
				
				block_sura_button = GetObject("block_item_sura")
				block_sura_button.SetToggleUpEvent(lambda arg=1: self.__OnClickBlockClass(arg))
				block_sura_button.SetToggleDownEvent(lambda arg=1: self.__OnClickBlockClass(arg))
				self.pickupBlockClassBtn.append(block_sura_button)
				
				block_shaman_button = GetObject("block_item_shaman")
				block_shaman_button.SetToggleUpEvent(lambda arg=2: self.__OnClickBlockClass(arg))
				block_shaman_button.SetToggleDownEvent(lambda arg=2: self.__OnClickBlockClass(arg))
				self.pickupBlockClassBtn.append(block_shaman_button)
				
				block_ninja_button = GetObject("block_item_ninja")
				block_ninja_button.SetToggleUpEvent(lambda arg=3: self.__OnClickBlockClass(arg))
				block_ninja_button.SetToggleDownEvent(lambda arg=3: self.__OnClickBlockClass(arg))
				self.pickupBlockClassBtn.append(block_ninja_button)
				# Block class sector
				
				self.pickupMinLvl = GetObject("min_lvl_editline")
				self.pickupMaxLvl = GetObject("max_lvl_editline")
				self.pickupMinLvl.SetUpdateEvent(ui.__mem_func__(self.OnChangePickupMinLvl))
				self.pickupMaxLvl.SetUpdateEvent(ui.__mem_func__(self.OnChangePickupMaxLvl))
				self.pickupMinLvl.SetEscapeEvent(self.OnPressEscapeKey)
				self.pickupMaxLvl.SetEscapeEvent(self.OnPressEscapeKey)
				
				# Block weapon sector
				block_sword_button = GetObject("block_weapon_onesword")
				block_sword_button.SetToggleUpEvent(lambda arg=0: self.__OnClickBlockWeapon(arg))
				block_sword_button.SetToggleDownEvent(lambda arg=0: self.__OnClickBlockWeapon(arg))
				self.pickupBlockWeaponBtn.append(block_sword_button)
				
				block_twosword_button = GetObject("block_weapon_twosword")
				block_twosword_button.SetToggleUpEvent(lambda arg=1: self.__OnClickBlockWeapon(arg))
				block_twosword_button.SetToggleDownEvent(lambda arg=1: self.__OnClickBlockWeapon(arg))
				self.pickupBlockWeaponBtn.append(block_twosword_button)
				
				block_dagger_button = GetObject("block_weapon_dagger")
				block_dagger_button.SetToggleUpEvent(lambda arg=2: self.__OnClickBlockWeapon(arg))
				block_dagger_button.SetToggleDownEvent(lambda arg=2: self.__OnClickBlockWeapon(arg))
				self.pickupBlockWeaponBtn.append(block_dagger_button)
				
				block_arrow_button = GetObject("block_weapon_arrow")
				block_arrow_button.SetToggleUpEvent(lambda arg=3: self.__OnClickBlockWeapon(arg))
				block_arrow_button.SetToggleDownEvent(lambda arg=3: self.__OnClickBlockWeapon(arg))
				self.pickupBlockWeaponBtn.append(block_arrow_button)
				
				block_bow_button = GetObject("block_weapon_bow")
				block_bow_button.SetToggleUpEvent(lambda arg=4: self.__OnClickBlockWeapon(arg))
				block_bow_button.SetToggleDownEvent(lambda arg=4: self.__OnClickBlockWeapon(arg))
				self.pickupBlockWeaponBtn.append(block_bow_button)
				
				block_bell_button = GetObject("block_weapon_bell")
				block_bell_button.SetToggleUpEvent(lambda arg=5: self.__OnClickBlockWeapon(arg))
				block_bell_button.SetToggleDownEvent(lambda arg=5: self.__OnClickBlockWeapon(arg))
				self.pickupBlockWeaponBtn.append(block_bell_button)
				
				block_fan_button = GetObject("block_weapon_fan")
				block_fan_button.SetToggleUpEvent(lambda arg=6: self.__OnClickBlockWeapon(arg))
				block_fan_button.SetToggleDownEvent(lambda arg=6: self.__OnClickBlockWeapon(arg))
				self.pickupBlockWeaponBtn.append(block_fan_button)
				# Block weapon sector
				
				# Block armor sector
				block_armor_button = GetObject("block_armor_button")
				block_armor_button.SetToggleUpEvent(lambda arg=0: self.__OnClickBlockArmor(arg))
				block_armor_button.SetToggleDownEvent(lambda arg=0: self.__OnClickBlockArmor(arg))
				self.pickupBlockArmorBtn.append(block_armor_button)
				
				block_helmet_button = GetObject("block_head_button")
				block_helmet_button.SetToggleUpEvent(lambda arg=1: self.__OnClickBlockArmor(arg))
				block_helmet_button.SetToggleDownEvent(lambda arg=1: self.__OnClickBlockArmor(arg))
				self.pickupBlockArmorBtn.append(block_helmet_button)
				
				block_shield_button = GetObject("block_shield_button")
				block_shield_button.SetToggleUpEvent(lambda arg=2: self.__OnClickBlockArmor(arg))
				block_shield_button.SetToggleDownEvent(lambda arg=2: self.__OnClickBlockArmor(arg))
				self.pickupBlockArmorBtn.append(block_shield_button)
				
				block_earring_button = GetObject("block_ear_button")
				block_earring_button.SetToggleUpEvent(lambda arg=3: self.__OnClickBlockArmor(arg))
				block_earring_button.SetToggleDownEvent(lambda arg=3: self.__OnClickBlockArmor(arg))
				self.pickupBlockArmorBtn.append(block_earring_button)
				
				block_wrist_button = GetObject("block_wrist_button")
				block_wrist_button.SetToggleUpEvent(lambda arg=4: self.__OnClickBlockArmor(arg))
				block_wrist_button.SetToggleDownEvent(lambda arg=4: self.__OnClickBlockArmor(arg))
				self.pickupBlockArmorBtn.append(block_wrist_button)
				
				block_foots_button = GetObject("block_foots_button")
				block_foots_button.SetToggleUpEvent(lambda arg=5: self.__OnClickBlockArmor(arg))
				block_foots_button.SetToggleDownEvent(lambda arg=5: self.__OnClickBlockArmor(arg))
				self.pickupBlockArmorBtn.append(block_foots_button)
				
				block_neck_button = GetObject("block_neck_button")
				block_neck_button.SetToggleUpEvent(lambda arg=6: self.__OnClickBlockArmor(arg))
				block_neck_button.SetToggleDownEvent(lambda arg=6: self.__OnClickBlockArmor(arg))
				self.pickupBlockArmorBtn.append(block_neck_button)
				# Block armor sector
				
				self.LoadPickupConfig()
			elif categoryIndex == 2:#Keybindings
				self.keybindingsPage = _CreateKeybindingsPage(scriptWindow)
			elif categoryIndex == 3:#Meteor Queue Appearance
				controller = uimetinqueueappearance.MetinQueueAppearanceController()
				if controller.Bind(scriptWindow, self.Hide):
					self.metinQueueAppearanceController = controller
				else:
					controller.Destroy()
					self.metinQueueAppearanceController = None
				
		elif optionIndex == 1:#Graphic-Options
			if categoryIndex == 0:#General
				if app.ENABLE_FOV_OPTION:
					self.fovController = GetObject("fov_controller")
					self.fovController.SetButtonVisual(IMG_DIR + "slider/",\
						"small_thumb_01.tga",\
						"small_thumb_02.tga",\
						"small_thumb_03.tga")
					self.fovController.SetBackgroundVisual(IMG_DIR + "slider/small_track.tga")
					self.fovResetButton = GetObject("fov_reset_button")
					self.fovValueText = GetObject("fov_value_text")

					if self.fovController:
						self.fovController.SetSliderPos(float(systemSetting.GetFOV()) / float(app.MAX_CAMERA_PERSPECTIVE))
						self.fovController.SetEvent(ui.__mem_func__(self.__OnChangeFOV))

					if self.fovValueText:
						self.fovValueText.SetText(str(int(systemSetting.GetFOV())))

					if self.fovResetButton:
						self.fovResetButton.SetEvent(ui.__mem_func__(self.__OnClickFOVResetButton))

				if app.ENABLE_SCALE_OPTION:
					stoneScaling = GetObject("stone_scale")
					stoneScaling.SetButtonVisual(IMG_DIR + "slider/",\
						"small_thumb_01.tga",\
						"small_thumb_02.tga",\
						"small_thumb_03.tga")
					stoneScaling.SetBackgroundVisual(IMG_DIR + "slider/small_track.tga")
					stoneScaling.SetSliderPos(float(systemSetting.GetMetinstoneScale()))
					stoneScaling.SetEvent(ui.__mem_func__(self.OnStoneScaling))
					self.stoneScaling = stoneScaling

				self.showDamageButtonList.append(GetObject("show_damage_on_button"))
				self.showDamageButtonList[0].SAFE_SetEvent(self.__OnClickShowDamage)
				self.showDamageButtonList.append(GetObject("show_damage_off_button"))
				self.showDamageButtonList[1].SAFE_SetEvent(self.__OnClickShowDamage)
				self.RefreshShowDamage()

				self.cameraModeButtonList.append(GetObject("camera_short"))
				self.cameraModeButtonList[0].SAFE_SetEvent(self.__OnClickCameraMode)
				self.cameraModeButtonList.append(GetObject("camera_long"))
				self.cameraModeButtonList[1].SAFE_SetEvent(self.__OnClickCameraMode)
				self.RefreshCameraMode()

				if app.ENABLE_SHADOW_RENDER_QUALITY_OPTION:
					self.shadowQualityButtonList.append(GetObject("shadow_quality_bad"))
					self.shadowQualityButtonList.append(GetObject("shadow_quality_average"))
					self.shadowQualityButtonList.append(GetObject("shadow_quality_good"))

					self.shadowTargetButtonList.append(GetObject("shadow_target_none"))
					self.shadowTargetButtonList.append(GetObject("shadow_target_ground"))
					self.shadowTargetButtonList.append(GetObject("shadow_target_ground_and_solo"))
					self.shadowTargetButtonList.append(GetObject("shadow_target_all"))

					self.shadowQualityButtonList[background.SHADOW_QUALITY_BAD].SAFE_SetEvent(self.__OnClickChangeShadowQuality, background.SHADOW_QUALITY_BAD)
					self.shadowQualityButtonList[background.SHADOW_QUALITY_AVERAGE].SAFE_SetEvent(self.__OnClickChangeShadowQuality, background.SHADOW_QUALITY_AVERAGE)
					self.shadowQualityButtonList[background.SHADOW_QUALITY_GOOD].SAFE_SetEvent(self.__OnClickChangeShadowQuality, background.SHADOW_QUALITY_GOOD)
					self.__ClickRadioButton(self.shadowQualityButtonList, systemSetting.GetShadowQualityLevel())

					self.shadowTargetButtonList[background.SHADOW_TARGET_NONE].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_NONE)
					self.shadowTargetButtonList[background.SHADOW_TARGET_GROUND].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_GROUND)
					self.shadowTargetButtonList[background.SHADOW_TARGET_GROUND_AND_SOLO].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_GROUND_AND_SOLO)
					self.shadowTargetButtonList[background.SHADOW_TARGET_ALL].SAFE_SetEvent(self.__OnClickChangeShadowTarget, background.SHADOW_TARGET_ALL)
					self.__ClickRadioButton(self.shadowTargetButtonList, systemSetting.GetShadowTargetLevel())


			elif categoryIndex == 1:#Interface
				if app.WJ_SHOW_MOB_INFO:
					self.showMobInfoButtonList.append(GetObject("show_mob_level_button"))
					self.showMobInfoButtonList.append(GetObject("show_mob_AI_flag_button"))
					self.showMobInfoButtonList[0].SetToggleUpEvent(self.__OnClickShowMobLevelButton)
					self.showMobInfoButtonList[1].SetToggleUpEvent(self.__OnClickShowMobAIFlagButton)
					self.showMobInfoButtonList[0].SetToggleDownEvent(self.__OnClickShowMobLevelButton)
					self.showMobInfoButtonList[1].SetToggleDownEvent(self.__OnClickShowMobAIFlagButton)
					self.RefreshShowMobInfo()

				if app.ENABLE_FONT_OPTION:
					for i in range(1, FONT_LEVEL_MAX_NUM + 1):
						self.fontLevelButtonList.append(GetObject("font_level%d" % i))
					for i in range(FONT_LEVEL_MAX_NUM):
						self.fontLevelButtonList[i].SAFE_SetEvent(self.__OnClickFontLevelButton, i)
					fontLevel = fontconfig.NormalizeFontLevel(systemSetting.GetFontLevel())
					self.__ClickRadioButton(self.fontLevelButtonList, fontLevel)
					self.fontLevel = fontLevel
					systemSetting.SetFontLevel(fontLevel)

				if app.ENABLE_QUEST_OPTION:
					self.questModeButtonList.append(GetObject("quest_mode_off"))
					self.questModeButtonList.append(GetObject("quest_mode_on"))
					self.questModeButtonList[0].SAFE_SetEvent(self.__OnClickQuestMode)
					self.questModeButtonList[1].SAFE_SetEvent(self.__OnClickQuestMode)
					self.RefreshQuestMode()

				if app.ENABLE_HIDE_AFFECT_ICONS:
					self.showAffectIconsList.append(GetObject("show_affect_icons"))
					self.showAffectIconsList[0].SAFE_SetEvent(self.__OnClickAffectIcons)
					self.showAffectIconsList.append(GetObject("hide_affect_icons"))
					self.showAffectIconsList[1].SAFE_SetEvent(self.__OnClickAffectIcons)
					self.RefreshAffectIcons()

				if app.ENABLE_SCALE_DAMAGE_TEXT:
					damageScaling = GetObject("damage_scale")
					damageScaling.SetButtonVisual(IMG_DIR + "slider/",\
						"small_thumb_01.tga",\
						"small_thumb_02.tga",\
						"small_thumb_03.tga")
					damageScaling.SetBackgroundVisual(IMG_DIR + "slider/small_track.tga")
					damageScaling.SetSliderPos(float(systemSetting.GetDamageTextureScale()))
					damageScaling.SetEvent(ui.__mem_func__(self.OnDamageScaling))
					self.damageScaling = damageScaling

				if app.ENABLE_DROP_INFO_WINDOW:
					self.dropConfig = [
						("drop_option_window", self.__OnClickDropWindowButton, False),
						("drop_option_chat", self.__OnClickDropChatButton, False),
						("drop_option_all", self.__OnClickDropAllOffButton, False),
						("drop_option_gold", self.__OnClickDropYangToggleButton, True),
					]

					for name, callback, isToggle in self.dropConfig:
						btn = GetObject(name)
						if isToggle:
							btn.SetToggleUpEvent(callback)
							btn.SetToggleDownEvent(callback)
						else:
							btn.SAFE_SetEvent(callback)
						self.dropButtonList[name] = btn

					self.RefreshDropMode()

				self.dropTrackerPlacementButtonList.append(
					GetObject("drop_tracker_placement_taskbar")
				)
				self.dropTrackerPlacementButtonList.append(
					GetObject("drop_tracker_placement_free")
				)
				self.dropTrackerPlacementButtonList[0].SAFE_SetEvent(
					self.__OnClickDropTrackerPlacement, "taskbar"
				)
				self.dropTrackerPlacementButtonList[1].SAFE_SetEvent(
					self.__OnClickDropTrackerPlacement, "free"
				)
				self.dropTrackerPlacementEditButton = GetObject(
					"drop_tracker_placement_edit"
				)
				self.dropTrackerPlacementEditButton.SAFE_SetEvent(
					self.__OnClickDropTrackerPlacementEdit
				)
				self.dropTrackerPlacementResetButton = GetObject(
					"drop_tracker_placement_reset"
				)
				self.dropTrackerPlacementResetButton.SAFE_SetEvent(
					self.__OnClickDropTrackerPlacementReset
				)
				self.RefreshDropTrackerPlacement()
				GetObject("system_notification_settings").SAFE_SetEvent(
					self.OpenSystemNotificationSettings)

				self.costumeInventoryModeButtonList.append(
					GetObject("costume_inventory_mode_integrated")
				)
				self.costumeInventoryModeButtonList.append(
					GetObject("costume_inventory_mode_separate")
				)
				self.costumeInventoryModeButtonList[0].SAFE_SetEvent(
					self.__OnClickCostumeInventoryMode, False
				)
				self.costumeInventoryModeButtonList[1].SAFE_SetEvent(
					self.__OnClickCostumeInventoryMode, True
				)
				self.RefreshCostumeInventoryMode()

			elif categoryIndex == 2:#Performance
				for fpsLimit in FPS_LIMITS:
					button = GetObject("fps_limit_%d" % fpsLimit)
					button.SAFE_SetEvent(self.__OnClickFPSLimit, fpsLimit)
					self.fpsLimitButtonList.append(button)

				self.showFPSButtonList.append(GetObject("show_fps_on"))
				self.showFPSButtonList.append(GetObject("show_fps_off"))
				self.showFPSButtonList[0].SAFE_SetEvent(self.__OnClickShowFPS, 1)
				self.showFPSButtonList[1].SAFE_SetEvent(self.__OnClickShowFPS, 0)

				self.vsyncButtonList.append(GetObject("vsync_on"))
				self.vsyncButtonList.append(GetObject("vsync_off"))
				self.vsyncButtonList[0].SAFE_SetEvent(self.__OnClickVSync, 1)
				self.vsyncButtonList[1].SAFE_SetEvent(self.__OnClickVSync, 0)

				self.__RefreshFrameRateOptions()

				self.alwaysShowNameButtonList.append(GetObject("always_show_name_on_button"))
				self.alwaysShowNameButtonList.append(GetObject("always_show_name_off_button"))
				self.alwaysShowNameButtonList[0].SAFE_SetEvent(self.__OnClickAlwaysShowName)
				self.alwaysShowNameButtonList[1].SAFE_SetEvent(self.__OnClickAlwaysShowName)
				self.RefreshAlwaysShowName()

				self.familyNameButtonList.append(GetObject("family_name_on"))
				self.familyNameButtonList.append(GetObject("family_name_off"))
				if hasattr(systemSetting, "CanChangeOwnFamilyNameVisibility"):
					self.familyNameButtonList[0].SAFE_SetEvent(self.__OnClickFamilyName, 1)
					self.familyNameButtonList[1].SAFE_SetEvent(self.__OnClickFamilyName, 0)
					self.RefreshFamilyName()
				else:
					for button in self.familyNameButtonList:
						button.Disable()

				if getattr(app, "ENABLE_DOG_MODE", 0):
					self.dogModeButtonList.append(GetObject("dog_mode_on"))
					self.dogModeButtonList.append(GetObject("dog_mode_off"))
					self.dogModeButtonList[0].SAFE_SetEvent(self.__OnClickDogMode, True)
					self.dogModeButtonList[1].SAFE_SetEvent(self.__OnClickDogMode, False)
					self.RefreshDogMode()

				if app.ENABLE_GRAPHIC_ON_OFF:
					for i in range(1, GRAPHIC_LEVEL_MAX_NUM + 1):
						self.effectLevelButtonList.append(GetObject("effect_level%d" % i))
						self.dropItemLevelButtonList.append(GetObject("dropItem_level%d" % i))

					for i in range(GRAPHIC_LEVEL_MAX_NUM):
						self.effectLevelButtonList[i].SAFE_SetEvent(self.__OnClickEffectLevelButton, i)
						self.dropItemLevelButtonList[i].SAFE_SetEvent(self.__OnClickDropItemLevelButton, i)
					self.__ClickRadioButton(self.effectLevelButtonList, systemSetting.GetEffectLevel())
					self.__ClickRadioButton(self.dropItemLevelButtonList, systemSetting.GetDropItemLevel())

					self.npcNameStatusButtonList.append(GetObject("npcName_on"))
					self.npcNameStatusButtonList.append(GetObject("npcName_off"))
					self.npcNameStatusButtonList[0].SAFE_SetEvent(self.__OnClickNpcNameStatusButton, 0)
					self.npcNameStatusButtonList[1].SAFE_SetEvent(self.__OnClickNpcNameStatusButton, 1)				
					self.__ClickRadioButton(self.npcNameStatusButtonList, systemSetting.IsNpcNameStatus())

				if app.ENABLE_OUTLINE_NAME_SHADOW:
					self.showOutlinedNamesList.append(GetObject("outline_on_button"))
					self.showOutlinedNamesList[0].SAFE_SetEvent(self.__OnClickOulineName)
					self.showOutlinedNamesList.append(GetObject("outline_off_button"))
					self.showOutlinedNamesList[1].SAFE_SetEvent(self.__OnClickOulineName)
					self.RefreshOulineName()

					self.petStatusButtonList = GetObject("show_pet")
					self.SupportStatusButtonList = GetObject("show_support")
					self.MountStatusButtonList = GetObject("show_mount")
					self.ShopStatusButtonList = GetObject("show_shop")

					self.petStatusButtonList.SetToggleUpEvent(self.__OnClickPetButton, 0)
					self.petStatusButtonList.SetToggleDownEvent(self.__OnClickPetButton, 1)
					self.SupportStatusButtonList.SetToggleUpEvent(self.__OnClickSupportButton, 0)
					self.SupportStatusButtonList.SetToggleDownEvent(self.__OnClickSupportButton, 1)
					self.MountStatusButtonList.SetToggleUpEvent(self.__OnClickMountButton, 0)
					self.MountStatusButtonList.SetToggleDownEvent(self.__OnClickMountButton, 1)
					self.RefreshCompanions()

					self.ShopStatusButtonList.SetToggleUpEvent(self.__OnClickShopButton, 0)
					self.ShopStatusButtonList.SetToggleDownEvent(self.__OnClickShopButton, 1)
					self.RefreshHideShop()

				if app.ENABLE_HIDE_SKILL_EFFECT:
					for BLEffectNames in ('BuffEffect', 'SkillEffect'):
						self.BLEffectGroupList.append(GetObject('BL_EFFECT_{}'.format(BLEffectNames)))
					for (Index, Button) in enumerate(self.BLEffectGroupList):
						Button.SetToggleDownEvent(lambda arg=Index: self.__OnClickBLEffectButton(arg))
						Button.SetToggleUpEvent(lambda arg=Index: self.__OnClickBLEffectButton(arg))
					self.__RefreshBLEffectButton()

				if app.ENABLE_AREA_OPTIMISATION:
					objectScaling = GetObject("object_distance_scale")
					objectScaling.SetButtonVisual(IMG_DIR + "slider/",\
						"small_thumb_01.tga",\
						"small_thumb_02.tga",\
						"small_thumb_03.tga")
					objectScaling.SetBackgroundVisual(IMG_DIR + "slider/small_track.tga")
					objectScaling.SetSliderPos(float(systemSetting.GetLoadingDistance()))
					objectScaling.SetEvent(ui.__mem_func__(self.OnObjectScaling))
					self.objectScaling = objectScaling

			elif categoryIndex == 3:#Visual Effects
				if app.ENABLE_SHARPNESS:
					self.sharpnessSlider = GetObject("sharpness_slider")
					self.sharpnessSlider.SetButtonVisual(IMG_DIR + "slider/",\
						"small_thumb_01.tga",\
						"small_thumb_02.tga",\
						"small_thumb_03.tga")
					self.sharpnessSlider.SetBackgroundVisual(IMG_DIR + "slider/small_track.tga")
					self.sharpnessResetButton = GetObject("sharpness_reset_button")
					self.sharpnessValueText = GetObject("sharpness_value_text")

					if self.sharpnessSlider:
						# Slider 0.0..1.0 maps to SharpnessPower 0.0..2.0
						self.sharpnessSlider.SetSliderPos(float(systemSetting.GetSharpnessPower()) / 2.0)
						self.sharpnessSlider.SetEvent(ui.__mem_func__(self.OnSharpnessChange))

					if self.sharpnessValueText:
						self.sharpnessValueText.SetText("%.2f" % systemSetting.GetSharpnessPower())

					if self.sharpnessResetButton:
						self.sharpnessResetButton.SetEvent(ui.__mem_func__(self.__OnClickSharpnessResetButton))

				if app.ENABLE_FOG_FIX:
					try:
						self.fogButtonList.append(GetObject("fog_off"))
						self.fogButtonList.append(GetObject("fog_on"))
						self.fogButtonList[0].SAFE_SetEvent(self.__OnClickFogModeOffButton)
						self.fogButtonList[1].SAFE_SetEvent(self.__OnClickFogModeOnButton)
						self.__ClickRadioButton(self.fogButtonList, background.GetFogMode())
					except:
						dbg.TraceError("[GameOption] Cannot wire fog buttons")

				try:
					self.fullMapRenderButtonList = []
					self.fullMapRenderButtonList.append(GetObject("full_map_render_on"))
					self.fullMapRenderButtonList.append(GetObject("full_map_render_off"))
					self.fullMapRenderButtonList[0].SAFE_SetEvent(self.__OnClickFullMapRenderOn)
					self.fullMapRenderButtonList[1].SAFE_SetEvent(self.__OnClickFullMapRenderOff)
					currentWant = int(systemSetting.GetFullMapRender())
					self.__ClickRadioButton(self.fullMapRenderButtonList, 0 if currentWant else 1)
				except:
					dbg.TraceError("[GameOption] Cannot wire full_map_render buttons (binding C++ manquant ?)")

				try:
					self.skyboxButtonList = []
					for i in range(len(self.__JTX_GetSkyboxPresets())):
						btn = GetObject("skybox_thumb_%d" % i)
						self.skyboxButtonList.append(btn)
						btn.SAFE_SetEvent(self.__OnClickSkyboxSlot, i)

					self.skyboxCurrentText = GetObject("skybox_current_text")

					savedSlot = int(systemSetting.GetSkyboxPreset())
					if savedSlot < 0 or savedSlot >= len(self.skyboxButtonList):
						savedSlot = 0
					self.__ClickRadioButton(self.skyboxButtonList, savedSlot)
					self.__JTX_RefreshSkyboxLabel(savedSlot)
				except:
					dbg.TraceError("[GameOption] Cannot wire skybox grid (UI script absent ?)")

			elif categoryIndex == 4 and getattr(app, "ENABLE_GRAPHICS_ENHANCEMENT", 0):#World renderer
				for profile in WORLD_GRAPHICS_PROFILES:
					button = GetObject("world_graphics_profile_%d" % profile)
					button.SAFE_SetEvent(self.__OnClickWorldGraphicsProfile, profile)
					self.worldGraphicsProfileButtonList.append(button)

				profileTooltips = (
					_GetOptionLocale("OPTION_WORLD_GRAPHICS_STOCK_TOOLTIP", "Original renderer; maximum compatibility."),
					_GetOptionLocale("OPTION_WORLD_GRAPHICS_LOW_TOOLTIP", "Modern renderer with conservative GPU load."),
					_GetOptionLocale("OPTION_WORLD_GRAPHICS_HIGH_TOOLTIP", "Recommended modern rendering quality."),
					_GetOptionLocale("OPTION_WORLD_GRAPHICS_ULTRA_TOOLTIP", "Maximum quality with significantly higher GPU and VRAM load."),
				)
				for profile, button in enumerate(self.worldGraphicsProfileButtonList):
					button.SetToolTipText(profileTooltips[profile])

				antialiasTooltips = (
					_GetOptionLocale("OPTION_WORLD_ANTIALIAS_OFF_TOOLTIP", "Disables edge anti-aliasing."),
					_GetOptionLocale("OPTION_WORLD_ANTIALIAS_FXAA_TOOLTIP", "Fast post-process anti-aliasing for enhanced profiles; the interface stays sharp."),
					_GetOptionLocale("OPTION_WORLD_ANTIALIAS_MSAA_TOOLTIP", "2x MSAA resets the graphics device; depth-based god rays use a compatibility path."),
					_GetOptionLocale("OPTION_WORLD_ANTIALIAS_MSAA4_TOOLTIP", "4x MSAA resets the graphics device and falls back to 2x when unsupported."),
				)
				for antialiasMode in WORLD_ANTIALIAS_MODES:
					button = GetObject("world_antialias_%d" % antialiasMode)
					button.SAFE_SetEvent(self.__OnClickWorldAntialias, antialiasMode)
					button.SetToolTipText(antialiasTooltips[antialiasMode])
					self.worldAntialiasButtonList.append(button)

				for rainLevel in WORLD_RAIN_LEVELS:
					button = GetObject("world_rain_level_%d" % rainLevel)
					button.SAFE_SetEvent(self.__OnClickWorldRainLevel, rainLevel)
					self.worldRainButtonList.append(button)

				self.worldRainFxButtonList = [
					GetObject("world_rain_fx_classic"),
					GetObject("world_rain_fx_enhanced"),
				]
				self.worldRainFxButtonList[0].SAFE_SetEvent(
					self.__OnClickWorldRainFx, 0)
				self.worldRainFxButtonList[1].SAFE_SetEvent(
					self.__OnClickWorldRainFx, 1)

				self.worldGrassButtonList = [
					GetObject("world_grass_on"),
					GetObject("world_grass_off"),
				]
				self.worldLightsButtonList = [
					GetObject("world_lights_on"),
					GetObject("world_lights_off"),
				]
				self.worldReflectionsButtonList = [
					GetObject("world_reflections_on"),
					GetObject("world_reflections_off"),
				]
				self.worldPostProcessingButtonList = [
					GetObject("world_postprocess_on"),
					GetObject("world_postprocess_off"),
				]

				self.worldGrassButtonList[0].SAFE_SetEvent(self.__OnClickWorldGrass, 1)
				self.worldGrassButtonList[1].SAFE_SetEvent(self.__OnClickWorldGrass, 0)
				self.worldGrassRadiusSlider = GetObject(
					"world_grass_radius_slider")
				self.worldGrassRadiusSlider.SetButtonVisual(
					IMG_DIR + "slider/",
					"thumb_01.tga",
					"thumb_02.tga",
					"thumb_03.tga")
				self.worldGrassRadiusSlider.SetBackgroundVisual(
					IMG_DIR + "slider/small_track.tga")
				self.worldGrassRadiusSlider.SetEvent(
					ui.__mem_func__(self.__OnChangeWorldGrassRadius))
				self.worldGrassRadiusValueText = GetObject(
					"world_grass_radius_value")
				self.worldLightsButtonList[0].SAFE_SetEvent(self.__OnClickWorldLights, 1)
				self.worldLightsButtonList[1].SAFE_SetEvent(self.__OnClickWorldLights, 0)
				self.worldReflectionsButtonList[0].SAFE_SetEvent(self.__OnClickWorldReflections, 1)
				self.worldReflectionsButtonList[1].SAFE_SetEvent(self.__OnClickWorldReflections, 0)
				self.worldPostProcessingButtonList[0].SAFE_SetEvent(self.__OnClickWorldPostProcessing, 1)
				self.worldPostProcessingButtonList[1].SAFE_SetEvent(self.__OnClickWorldPostProcessing, 0)

				self.worldGraphicsStatusText = GetObject("world_graphics_status")
				self.worldGraphicsFallbackText = GetObject("world_graphics_fallback")
				self.worldGraphicsCapabilityText = GetObject("world_graphics_capabilities")
				self.worldGraphicsResourceWarningText = GetObject("world_graphics_resource_warning")
				self.worldGraphicsRecommendedButton = GetObject("world_graphics_recommended")
				self.worldGraphicsRecommendedButton.SAFE_SetEvent(self.__OnClickWorldGraphicsRecommended)
				self.worldGraphicsRecommendedButton.SetToolTipText(
					_GetOptionLocale(
						"OPTION_WORLD_GRAPHICS_RECOMMENDED_TOOLTIP",
						"Selects a safe profile from the detected GPU capabilities."))

				featureTooltips = (
					(
						self.worldRainFxButtonList,
						_GetOptionLocale("OPTION_WORLD_RAIN_FX_TOOLTIP", "Adds surface-aware rain, splashes and distant rainfall."),
					),
					(
						self.worldGrassButtonList,
						_GetOptionLocale("OPTION_WORLD_GRASS_TOOLTIP", "Animated grass with wind and character interaction."),
					),
					(
						self.worldLightsButtonList,
						_GetOptionLocale("OPTION_WORLD_LIGHTS_TOOLTIP", "Dynamic light from nearby torches, lamps and effects."),
					),
					(
						self.worldReflectionsButtonList,
						_GetOptionLocale("OPTION_WORLD_REFLECTIONS_TOOLTIP", "Real-time reflections on water and wet surfaces."),
					),
					(
						self.worldPostProcessingButtonList,
						_GetOptionLocale("OPTION_WORLD_POSTPROCESS_TOOLTIP", "World colour grade, god rays, underwater effects and sharpness; the interface stays untouched."),
					),
				)
				for buttonList, tooltip in featureTooltips:
					for button in buttonList:
						button.SetToolTipText(tooltip)
				self.__RefreshWorldGraphicsOptions()

		elif optionIndex == 2:#Sound-Options
			if categoryIndex == 0:#General

				ctrlSoundVolume = GetObject("sound_volume_controller")
				ctrlSoundVolume.SetButtonVisual(IMG_DIR + "slider/", "thumb_01.tga", "thumb_02.tga", "thumb_03.tga")
				ctrlSoundVolume.SetBackgroundVisual(IMG_DIR + "slider/track.tga")
				ctrlSoundVolume.SetSliderPos(float(systemSetting.GetSoundVolume()) / 5.0)
				ctrlSoundVolume.SetEvent(ui.__mem_func__(self.OnChangeSoundVolume))
				self.ctrlSoundVolume = ctrlSoundVolume

				ctrlMusicVolume = GetObject("music_volume_controller")
				ctrlMusicVolume.SetButtonVisual(IMG_DIR + "slider/", "thumb_01.tga", "thumb_02.tga", "thumb_03.tga")
				ctrlMusicVolume.SetBackgroundVisual(IMG_DIR + "slider/track.tga")
				ctrlMusicVolume.SetSliderPos(float(systemSetting.GetMusicVolume()))
				ctrlMusicVolume.SetEvent(ui.__mem_func__(self.OnChangeMusicVolume))
				self.ctrlMusicVolume = ctrlMusicVolume
				GetObject("bgm_button").SAFE_SetEvent(self.__OnClickChangeMusicButton)
				self.selectMusicFile = GetObject("bgm_file")

		# except:
			# dbg.TraceError("[GameOption]LoadCatetoryOptions optionIndex: %d categoryIndex: %d"%(optionIndex, categoryIndex))

	# Dont Touch #
	def __GetOptionInteger(self, key, defaultValue):
		try:
			return int(cfg.Get(cfg.SAVE_OPTION, key, str(defaultValue)))
		except (TypeError, ValueError):
			return defaultValue

	def __RefreshFrameRateOptions(self):
		fpsLimit = max(30, min(360, self.__GetOptionInteger("fps_limit", 60)))
		for button in self.fpsLimitButtonList:
			button.SetUp()
		if fpsLimit in FPS_LIMITS:
			self.fpsLimitButtonList[FPS_LIMITS.index(fpsLimit)].Down()
		app.SetFPS(fpsLimit)

		showFPS = 1 if self.__GetOptionInteger("show_fps", 0) else 0
		self.__ClickRadioButton(self.showFPSButtonList, 0 if showFPS else 1)

		vsync = 1 if self.__GetOptionInteger("vsync", 1) else 0
		self.__ClickRadioButton(self.vsyncButtonList, 0 if vsync else 1)

		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.wndMiniMap:
			interface.wndMiniMap.SetFPSCounterVisible(bool(showFPS))

	def __OnClickFPSLimit(self, fpsLimit):
		cfg.Set(cfg.SAVE_OPTION, "fps_limit", str(fpsLimit))
		app.SetFPS(fpsLimit)
		self.__RefreshFrameRateOptions()

	def __OnClickShowFPS(self, showFPS):
		cfg.Set(cfg.SAVE_OPTION, "show_fps", str(showFPS))
		self.__RefreshFrameRateOptions()

	def __OnClickVSync(self, vsync):
		cfg.Set(cfg.SAVE_OPTION, "vsync", str(vsync))
		self.__RefreshFrameRateOptions()
		chat.AppendChat(chat.CHAT_TYPE_INFO, uiScriptLocale.OPTION_VSYNC_RESTART)

	if getattr(app, "ENABLE_DOG_MODE", 0):
		def RefreshDogMode(self):
			enabled = bool(systemSetting.GetDogMode())
			self.__ClickRadioButton(self.dogModeButtonList, 0 if enabled else 1)

		def __OnClickDogMode(self, enabled):
			enabled = bool(enabled)
			if bool(systemSetting.GetDogMode()) != enabled:
				systemSetting.SetDogMode(enabled)
				chat.AppendChat(
					chat.CHAT_TYPE_INFO,
					localeInfo.RESTART_CLIENT_DO_YOU_ACCEPT_1,
				)
			self.RefreshDogMode()

	def __GetWorldGraphicsValue(self, getterName, defaultValue):
		try:
			return int(getattr(systemSetting, getterName)())
		except (AttributeError, RuntimeError, TypeError, ValueError):
			return defaultValue

	def __GetWorldGraphicsCapability(self, getterName, defaultValue):
		try:
			return int(getattr(background, getterName)())
		except (AttributeError, RuntimeError, TypeError, ValueError):
			return defaultValue

	def __RefreshWorldGraphicsOptions(self):
		if not self.worldGraphicsProfileButtonList:
			return

		requested = self.__GetWorldGraphicsValue("GetWorldGraphicsLevel", 0)
		requestedAntialias = self.__GetWorldGraphicsValue(
			"GetWorldAntialiasMode",
			1)
		rainLevel = self.__GetWorldGraphicsValue("GetWorldRainLevel", 0)
		rainFx = 1 if self.__GetWorldGraphicsValue("GetWorldRainFx", 1) else 0
		grass = 1 if self.__GetWorldGraphicsValue("GetWorldGrass", 1) else 0
		grassRadius = self.__GetWorldGraphicsValue(
			"GetWorldGrassRadius",
			100)
		lights = 1 if self.__GetWorldGraphicsValue("GetWorldLights", 1) else 0
		reflections = 1 if self.__GetWorldGraphicsValue("GetWorldReflections", 1) else 0
		postProcessing = 1 if self.__GetWorldGraphicsValue("GetWorldPostProcessing", 1) else 0

		requested = max(0, min(3, requested))
		requestedAntialias = max(0, min(3, requestedAntialias))
		rainLevel = max(0, min(3, rainLevel))
		grassRadius = max(100, min(300, grassRadius))
		self.__ClickRadioButton(self.worldGraphicsProfileButtonList, requested)
		self.__ClickRadioButton(
			self.worldAntialiasButtonList,
			requestedAntialias)
		self.__ClickRadioButton(self.worldRainButtonList, rainLevel)
		self.__ClickRadioButton(self.worldRainFxButtonList, rainFx)
		self.__ClickRadioButton(self.worldGrassButtonList, 0 if grass else 1)
		if self.worldGrassRadiusSlider:
			self.worldGrassRadiusSlider.SetSliderPos(
				float(grassRadius - 100) / 200.0)
		self.__ClickRadioButton(self.worldLightsButtonList, 0 if lights else 1)
		self.__ClickRadioButton(self.worldReflectionsButtonList, 0 if reflections else 1)
		self.__ClickRadioButton(self.worldPostProcessingButtonList, 0 if postProcessing else 1)

		effective = 0
		reason = "disabled"
		maximum = self.__GetWorldGraphicsCapability("GetWorldGraphicsMaximumLevel", 0)
		effectiveAntialias = self.__GetWorldGraphicsCapability(
			"GetWorldAntialiasEffectiveMode",
			0)
		sampleableDepth = self.__GetWorldGraphicsCapability(
			"IsWorldSampleableDepthActive",
			0)
		textureMemoryMB = self.__GetWorldGraphicsCapability(
			"GetWorldGraphicsAvailableTextureMemoryMB",
			0)
		effectiveRainFx = self.__GetWorldGraphicsCapability(
			"GetWorldRainFxEffective",
			0)
		effectiveGrassRadius = self.__GetWorldGraphicsCapability(
			"GetWorldGrassRadiusEffective",
			100)
		if self.worldGrassRadiusSlider:
			if grass:
				self.worldGrassRadiusSlider.Enable()
			else:
				self.worldGrassRadiusSlider.Disable()
		if self.worldGrassRadiusValueText:
			grassRadiusText = _GetOptionLocale(
				"OPTION_WORLD_GRASS_RADIUS_VALUE",
				"%.1fx (active %.1fx)") % (
					float(grassRadius) / 100.0,
					float(effectiveGrassRadius) / 100.0)
			if effectiveGrassRadius < grassRadius:
				grassRadiusText += _GetOptionLocale(
					"OPTION_WORLD_GRASS_RADIUS_LIMITED_SUFFIX",
					" | limited by the active profile")
			self.worldGrassRadiusValueText.SetText(grassRadiusText)
		if self.worldRainFxButtonList:
			rainFxTooltip = "%s | %s" % (
				_GetOptionLocale(
					"OPTION_WORLD_RAIN_FX_TOOLTIP",
					"Adds surface-aware rain, splashes and distant rainfall."),
				_GetOptionLocale(
					"OPTION_WORLD_RAIN_FX_EFFECTIVE_TOOLTIP",
					"Enhanced rain active: %s") % (
						_GetOptionLocale("OPTION_WORLD_STATUS_ON", "on")
							if effectiveRainFx else
						_GetOptionLocale("OPTION_WORLD_STATUS_OFF", "off")))
			for button in self.worldRainFxButtonList:
				button.SetToolTipText(rainFxTooltip)
		try:
			effective = max(0, min(3, int(background.GetWorldGraphicsEffectiveLevel())))
			reason = str(background.GetWorldGraphicsFallbackReason())
		except (AttributeError, RuntimeError, TypeError, ValueError):
			pass

		profileNames = (
			_GetOptionLocale("OPTION_WORLD_GRAPHICS_STOCK", "Stock"),
			_GetOptionLocale("OPTION_WORLD_GRAPHICS_LOW", "Low"),
			_GetOptionLocale("OPTION_WORLD_GRAPHICS_HIGH", "High"),
			_GetOptionLocale("OPTION_WORLD_GRAPHICS_ULTRA", "Ultra"),
		)
		antialiasNames = (
			_GetOptionLocale("OPTION_WORLD_ANTIALIAS_OFF", "Off"),
			"FXAA",
			"MSAA 2x",
			"MSAA 4x",
		)
		effectiveAntialias = max(0, min(3, effectiveAntialias))
		if self.worldGraphicsStatusText:
			self.worldGraphicsStatusText.SetText(
				_GetOptionLocale("OPTION_WORLD_GRAPHICS_STATUS", "Selected: %s | Active: %s")
				% (profileNames[requested], profileNames[effective]))

		fallbackLabels = {
			"none": "",
			"disabled": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_DISABLED", "Stock renderer is active."),
			"device_not_ready": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_DEVICE", "Graphics device is not ready."),
			"renderer_not_ready": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_RENDERER", "Enhanced renderer resources are not ready."),
			"vertex_shader_3_required": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_SM3", "Shader Model 3.0 is required."),
			"pixel_shader_3_required": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_SM3", "Shader Model 3.0 is required."),
			"pixel_shader_instruction_limit": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_LIMIT", "GPU shader instruction limit is too low."),
			"reflection_target_unsupported": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_REFLECTION", "Reflections were disabled by GPU compatibility."),
			"reflection_clip_plane_unsupported": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_REFLECTION_CLIP", "This GPU cannot clip the reflection pass safely."),
			"reflection_profile_required": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_REFLECTION_PROFILE", "Real-time reflections require the Ultra profile."),
			"depth_surface_unsupported": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_DEPTH", "Required depth format is unsupported."),
			"depth_match_unsupported": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_DEPTH", "Required depth format is unsupported."),
			"shadow_target_unsupported": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_DEPTH", "Required R32F shadow format is unsupported."),
			"shadow_depth_match_unsupported": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_DEPTH", "Required R32F/D16 shadow pairing is unsupported."),
			"profile_clamped_by_gpu": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_CLAMPED", "The active profile was reduced for this GPU."),
			"shader_pack_missing": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_SHADER_PACK", "Enhanced shader files are missing."),
			"shader_bytecode_invalid": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_SHADER_INVALID", "Enhanced shader data is invalid."),
			"shader_contract_mismatch": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_SHADER_INVALID", "Enhanced shader data is invalid."),
			"shader_create_failed": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_SHADER_CREATE", "The GPU rejected an enhanced shader."),
			"render_target_create_failed": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_TARGET", "An enhanced render target could not be created."),
			"device_reset_pending": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_RESET", "Enhanced graphics are recovering after a device reset."),
			"light_texture_unsupported": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_LIGHT_TEXTURE", "This GPU does not support the point-light texture format."),
			"light_subsystem_not_ready": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_LIGHT_RUNTIME", "Enhanced point lights are temporarily unavailable."),
			"neutral_texture_create_failed": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_NEUTRAL_TEXTURE", "Enhanced fallback textures could not be created."),
			"grass_subsystem_not_ready": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_GRASS_RUNTIME", "Enhanced grass is temporarily unavailable."),
			"postprocess_subsystem_not_ready": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_POSTPROCESS", "World post-processing is temporarily unavailable."),
			"weather_subsystem_not_ready": _GetOptionLocale("OPTION_WORLD_GRAPHICS_REASON_WEATHER_RUNTIME", "Enhanced rain is temporarily unavailable; classic rain is active."),
		}
		if self.worldGraphicsFallbackText:
			self.worldGraphicsFallbackText.SetText(fallbackLabels.get(reason, reason))

		maximum = max(0, min(3, maximum))
		if self.worldGraphicsCapabilityText:
			self.worldGraphicsCapabilityText.SetText(
				_GetOptionLocale(
					"OPTION_WORLD_GRAPHICS_CAPABILITIES",
					"AA: %s -> %s | INTZ: %s | GPU: %s")
				% (
					antialiasNames[requestedAntialias],
					antialiasNames[effectiveAntialias],
					_GetOptionLocale("OPTION_WORLD_STATUS_ON", "on")
						if sampleableDepth else
						_GetOptionLocale("OPTION_WORLD_STATUS_OFF", "off"),
					profileNames[maximum]))

		if self.worldGraphicsResourceWarningText:
			if requested == 3:
				if textureMemoryMB > 0:
					self.worldGraphicsResourceWarningText.SetText(
						_GetOptionLocale(
							"OPTION_WORLD_GRAPHICS_ULTRA_WARNING_MEMORY",
							"Ultra has high GPU load | available ~%d MB")
						% textureMemoryMB)
				else:
					self.worldGraphicsResourceWarningText.SetText(
						_GetOptionLocale(
							"OPTION_WORLD_GRAPHICS_ULTRA_WARNING",
							"Ultra has significantly higher GPU and VRAM load."))
			else:
				self.worldGraphicsResourceWarningText.SetText("")

	def __OnClickWorldGraphicsProfile(self, profile):
		if profile not in WORLD_GRAPHICS_PROFILES:
			return
		systemSetting.SetWorldGraphicsLevel(profile)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldAntialias(self, antialiasMode):
		if antialiasMode not in WORLD_ANTIALIAS_MODES:
			return
		systemSetting.SetWorldAntialiasMode(antialiasMode)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldGraphicsRecommended(self):
		recommended = self.__GetWorldGraphicsCapability(
			"GetWorldGraphicsRecommendedLevel",
			0)
		recommended = max(0, min(3, recommended))
		systemSetting.SetWorldGraphicsLevel(recommended)
		if recommended > 0:
			systemSetting.SetWorldGrass(1)
			systemSetting.SetWorldLights(1)
			systemSetting.SetWorldReflections(1)
			systemSetting.SetWorldPostProcessing(1)
			background.SetWorldRainFx(1)
			background.SetWorldGrassRadius(100)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldRainLevel(self, rainLevel):
		if rainLevel not in WORLD_RAIN_LEVELS:
			return
		# The system-setting bridge persists the value, but it does not update
		# the live weather emitter.  Route interactive changes through the
		# background bridge so rain density changes immediately in-game.
		background.SetWorldRainLevel(rainLevel)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldGrass(self, enabled):
		systemSetting.SetWorldGrass(1 if enabled else 0)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldRainFx(self, enabled):
		background.SetWorldRainFx(1 if enabled else 0)
		self.__RefreshWorldGraphicsOptions()

	def __OnChangeWorldGrassRadius(self):
		if not self.worldGrassRadiusSlider:
			return
		position = max(
			0.0,
			min(1.0, float(self.worldGrassRadiusSlider.GetSliderPos())))
		radius = 100 + int(round(position * 20.0)) * 10
		background.SetWorldGrassRadius(radius)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldLights(self, enabled):
		systemSetting.SetWorldLights(1 if enabled else 0)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldReflections(self, enabled):
		systemSetting.SetWorldReflections(1 if enabled else 0)
		self.__RefreshWorldGraphicsOptions()

	def __OnClickWorldPostProcessing(self, enabled):
		systemSetting.SetWorldPostProcessing(1 if enabled else 0)
		self.__RefreshWorldGraphicsOptions()

	def OnUpdate(self):
		if getattr(self, "familyNameButtonList", None) and hasattr(systemSetting, "CanChangeOwnFamilyNameVisibility"):
			self.RefreshFamilyName()
		if not getattr(app, "ENABLE_GRAPHICS_ENHANCEMENT", 0):
			return
		if not self.IsShow() or not self.worldGraphicsProfileButtonList:
			return
		now = app.GetTime()
		if now < self.worldGraphicsNextStatusRefresh:
			return
		self.worldGraphicsNextStatusRefresh = now + 0.5
		if self.children.get("optionType", -1) == 1 and \
				self.children.get("categoryType", -1) == 4:
			self.__RefreshWorldGraphicsOptions()

	def GetCurrentWindow(self):
		if "optionType" in self.children and "categoryType" in self.children:
			(optionType,categoryType) = (self.children["optionType"],self.children["categoryType"])
			if "optionWindow%d%d"%(optionType,categoryType) in self.children:
				return self.children["optionWindow%d%d"%(optionType,categoryType)]
		return None
	def GetCurrentScrollBar(self):
		window = self.GetCurrentWindow()
		if window != None:
			return window.scrollBar
		return None
	def OnMouseWheel(self, nLen):
		scrollBar = self.GetCurrentScrollBar()
		if scrollBar:
			if scrollBar.IsShow():
				if nLen > 0:
					scrollBar.OnUp()
				else:
					scrollBar.OnDown()
				return True
		return False

	def UpdateScrollBar(self):
		window = self.GetCurrentWindow()
		if window == None:
			return
		scrollBar = window.scrollBar
		if scrollBar == None:
			return
		scriptChildrens = window.Children
		if len(scriptChildrens) == 0:
			return

		windowHeight = window.GetHeight()

		# OLD SHIT
		#lastChildren = scriptChildrens[len(scriptChildrens)-1]
		#screenSize = lastChildren.exPos[1]+lastChildren.GetHeight()

		screenSize = 0
		for child in scriptChildrens:
			childHeight = child.exPos[1] + child.GetHeight()
			if childHeight > screenSize:
				screenSize=childHeight

		if screenSize > windowHeight:
			scrollLen = screenSize-windowHeight
			basePos = int(scrollBar.GetPos()*scrollLen)
			for child in scriptChildrens:
				(_x,_y) = child.exPos
				child.SetPosition(_x,_y-basePos)

			scrollBar.SetMiddleBarSize(float(windowHeight-5)/float(screenSize))
			scrollBar.Show()
		else:
			scrollBar.Hide()

		_wy = window.GetGlobalPosition()[1]
		elementDictionary = window.ElementDictionary
		for childName, child in elementDictionary.items():
			(_x,_y) = child.GetGlobalPosition()
			childHeight = child.GetHeight()
			textLines = []
			images = []
			if isinstance(child, ui.ExpandedImageBox):
				images.append(child)
			elif isinstance(child, ui.TextLine):
				textLines.append(child)
			elif isinstance(child, ui.ToggleButton) or isinstance(child, ui.RadioButton) or isinstance(child, ui.Button):
				if child.ButtonText != None:
					textLines.append(child.ButtonText)
				images.append(child)
			elif isinstance(child, ui.SliderBar):
				if child.backGroundImage != None:
					images.append(child.backGroundImage)
				if child.cursor != None:
					images.append(child.cursor)

			for childItem in textLines:
				if _y < _wy:
					if childItem.IsShow():
						childItem.Hide()
				elif _y > (_wy+windowHeight-20):
					if childItem.IsShow():
						childItem.Hide()
				else:
					if not childItem.IsShow():
						childItem.Show()

			for childItem in images:
				if _y < _wy:
					if childItem.IsShow():
						childItem.Hide()
				elif _y > (_wy + windowHeight -25):
					if childItem.IsShow():
						childItem.Hide()
				else:
					if not childItem.IsShow():
						childItem.Show()
	# Dont Touch #
	
	######################
	### PICKUP OPTIONS ###
	def SavePickupConfig(self):
		PICKUP_FOLDER = "UserData/pickup"
		osfInfo.CheckDirectory(PICKUP_FOLDER)
		
		PICKUP_CFG_FILE = PICKUP_FOLDER + "/" + player.GetName() + ".cfg"
		try:
			f = open(PICKUP_CFG_FILE, "w+")
			f.write("pick_mode:" + str(self.cfgPickupMode) + "\n")
			
			txtBlockClass = ""
			i=0
			for blockClass in self.cfgPickupBlockClass:
				if i == 0:
					txtBlockClass += str(blockClass)
				else:
					txtBlockClass += "," + str(blockClass)
				i=i+1
				
			f.write("block_class:" + txtBlockClass + "\n")
			f.write("min_lvl:" + str(self.cfgPickupMinLvl) + "\n")
			f.write("max_lvl:" + str(self.cfgPickupMaxLvl) + "\n")
			
			txtBlockWeapon = ""
			i=0
			for blockWeapon in self.cfgPickupBlockWeapon:
				if i == 0:
					txtBlockWeapon += str(blockWeapon)
				else:
					txtBlockWeapon += "," + str(blockWeapon)
				i=i+1
			
			f.write("block_weapon:" + txtBlockWeapon +"\n")
			
			txtBlockArmor = ""
			i=0
			for blockArmor in self.cfgPickupBlockArmor:
				if i == 0:
					txtBlockArmor += str(blockArmor)
				else:
					txtBlockArmor += "," + str(blockArmor)
				i=i+1
			
			f.write("block_armor:" + txtBlockArmor +"\n")
			f.close()
		except:
			pass
	
	def LoadPickupConfig(self):
		if self.cfgPickupLoaded:
			return

		## IF YOU EDIT THIS FUNCTION
		## DONT FORGET TO EDIT 'LoadPickupConfig' also in osfInfo.py
			
		PICKUP_FOLDER = "UserData/pickup"
		osfInfo.CheckDirectory(PICKUP_FOLDER)
		
		PICKUP_CFG_FILE = PICKUP_FOLDER + "/" + player.GetName() + ".cfg"
		if osfInfo.CheckFile(PICKUP_CFG_FILE):	

			for xx in range(4):
				player.PickupBlockClassType(False, xx)
				
			for xx in range(6):
				player.PickupBlockWeaponType(False, xx)
				
			for xx in range(6):
				player.PickupBlockArmorType(False, xx)
		
			lines = open(PICKUP_CFG_FILE, "r").readlines()
			if len(lines) > 0:
				for line in lines:
					if len(line) <= 2:
						continue
						
					line = line.replace("\n", "")
					lineSplit = line.split(":")
					
					if lineSplit[0] == "pick_mode":
						self.cfgPickupMode = int(lineSplit[1])
						
					elif lineSplit[0] == "block_class":
						if len(lineSplit[1]) >= 1:
							splitClass = lineSplit[1].split(",")
							for blockClass in splitClass:
								self.cfgPickupBlockClass.append(int(blockClass))
								player.PickupBlockClassType(True, int(blockClass))
								
					elif lineSplit[0] == "min_lvl":
						self.cfgPickupMinLvl = int(lineSplit[1])
						player.PickupBlockMinLvl(int(lineSplit[1]))
						
					elif lineSplit[0] == "max_lvl":
						self.cfgPickupMaxLvl = int(lineSplit[1])
						player.PickupBlockMaxLvl(int(lineSplit[1]))
						
					elif lineSplit[0] == "block_weapon":
						if len(lineSplit[1]) >= 1:
							splitClass = lineSplit[1].split(",")
							for blockClass in splitClass:
								self.cfgPickupBlockWeapon.append(int(blockClass))
								player.PickupBlockWeaponType(True, int(blockClass))
								
					elif lineSplit[0] == "block_armor":
						if len(lineSplit[1]) >= 1:
							splitClass = lineSplit[1].split(",")
							for blockClass in splitClass:
								self.cfgPickupBlockArmor.append(int(blockClass))
								player.PickupBlockArmorType(True, int(blockClass))
		else:
			self.SavePickupConfig()
			self.LoadPickupConfig()
			return
		
		self.cfgPickupLoaded = True
		##
		self.RefreshPickupConfig()

	def RefreshPickupConfig(self):
		if self.cfgPickupMode == 1:
			self.__OnClickPickupAll(False)
		else:
			self.__OnClickPickupSingle(False)
			
		self.RefreshPickupBlockClass(False)
		
		self.pickupMinLvl.SetText(str(self.cfgPickupMinLvl))
		self.pickupMaxLvl.SetText(str(self.cfgPickupMaxLvl))
		
		self.RefreshPickupBlockWeapon(False)
		self.RefreshPickupBlockArmor(False)
	
	def __PickupModeSelected(self, mode):
		self.pickupModeButton[mode].Down()
		self.pickupModeButton[not mode].SetUp()
		osfInfo.PICKUP_MODE = mode+1
	
	def __OnClickPickupAll(self, bSave = True):
		self.cfgPickupMode = 1
		self.__PickupModeSelected(0)
		
		if bSave:
			self.SavePickupConfig()
		
	def __OnClickPickupSingle(self, bSave = True):
		self.cfgPickupMode = 2
		self.__PickupModeSelected(1)
		
		if bSave:
			self.SavePickupConfig()
			
	def RefreshPickupBlockClass(self, bSave = True):
		if bSave:
			self.SavePickupConfig()
		for i in range(len(self.pickupBlockClassBtn)):
			if i in self.cfgPickupBlockClass:
				self.pickupBlockClassBtn[i].Down()
				player.PickupBlockClassType(True, i)
			else:
				self.pickupBlockClassBtn[i].SetUp()
				player.PickupBlockClassType(False, i)
				
	def __OnClickBlockClass(self, i):
		if i in self.cfgPickupBlockClass:
			self.cfgPickupBlockClass.remove(i)
		else:
			self.cfgPickupBlockClass.append(i)
			
		self.RefreshPickupBlockClass()
		
	def OnChangePickupMinLvl(self):
		text = self.pickupMinLvl.GetText()

		if len(text) <= 0:
			self.cfgPickupMinLvl = 1
			player.PickupBlockMinLvl(self.cfgPickupMinLvl)
			self.SavePickupConfig()
			return
		else:
			if int(text) <= 0:
				self.pickupMinLvl.SetText("1")	
			elif int(text) >= 150:
				self.pickupMinLvl.SetText("150")
				
		self.cfgPickupMinLvl = int(self.pickupMinLvl.GetText())
		player.PickupBlockMinLvl(self.cfgPickupMinLvl)
		self.SavePickupConfig()
		
	def OnChangePickupMaxLvl(self):
		text = self.pickupMaxLvl.GetText()

		if len(text) <= 0:
			self.cfgPickupMaxLvl = 150
			player.PickupBlockMaxLvl(self.cfgPickupMaxLvl)
			self.SavePickupConfig()
			return
		else:
			if int(text) <= 0:
				self.pickupMaxLvl.SetText("1")	
			elif int(text) >= 150:
				self.pickupMaxLvl.SetText("150")
				
		self.cfgPickupMaxLvl = int(self.pickupMaxLvl.GetText())
		player.PickupBlockMaxLvl(self.cfgPickupMaxLvl)
		self.SavePickupConfig()
		
	def RefreshPickupBlockWeapon(self, bSave = True):
		if bSave:
			self.SavePickupConfig()
		for i in range(len(self.pickupBlockWeaponBtn)):
			if i in self.cfgPickupBlockWeapon:
				self.pickupBlockWeaponBtn[i].Down()
				player.PickupBlockWeaponType(True, i)
			else:
				self.pickupBlockWeaponBtn[i].SetUp()
				player.PickupBlockWeaponType(False, i)
				
	def __OnClickBlockWeapon(self, i):
		if i in self.cfgPickupBlockWeapon:
			self.cfgPickupBlockWeapon.remove(i)
		else:
			self.cfgPickupBlockWeapon.append(i)
			
		self.RefreshPickupBlockWeapon()
		
	def RefreshPickupBlockArmor(self, bSave = True):
		if bSave:
			self.SavePickupConfig()
		for i in range(len(self.pickupBlockArmorBtn)):
			if i in self.cfgPickupBlockArmor:
				self.pickupBlockArmorBtn[i].Down()
				player.PickupBlockArmorType(True, i)
			else:
				self.pickupBlockArmorBtn[i].SetUp()
				player.PickupBlockArmorType(False, i)
				
	def __OnClickBlockArmor(self, i):
		if i in self.cfgPickupBlockArmor:
			self.cfgPickupBlockArmor.remove(i)
		else:
			self.cfgPickupBlockArmor.append(i)
			
		self.RefreshPickupBlockArmor()
	####PICKUP OPTIONS ###
	######################

	# PvP - Mode
	def __SetPeacePKMode(self):
		self.__SetPKMode(player.PK_MODE_PEACE)
	def __SetPKMode(self, mode):
		for btn in self.pvpModeButtonDict.values():
			btn.SetUp()
		if mode in self.pvpModeButtonDict:
			self.pvpModeButtonDict[mode].Down()
	def __CheckPvPProtectedLevelPlayer(self):
		if player.GetStatus(player.LEVEL)<constInfo.PVPMODE_PROTECTED_LEVEL:
			self.__SetPeacePKMode()
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPTION_PVPMODE_PROTECT % (constInfo.PVPMODE_PROTECTED_LEVEL))
			return True
		return False
	def __RefreshPVPButtonList(self):
		self.__SetPKMode(player.GetPKMode())
	def __OnClickPvPModePeaceButton(self):
		if self.__CheckPvPProtectedLevelPlayer():
			return
		self.__RefreshPVPButtonList()
		if constInfo.PVPMODE_ENABLE:
			net.SendChatPacket("/pkmode 0", chat.CHAT_TYPE_TALKING)
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPTION_PVPMODE_NOT_SUPPORT)
	def __OnClickPvPModeRevengeButton(self):
		if self.__CheckPvPProtectedLevelPlayer():
			return
		self.__RefreshPVPButtonList()
		if constInfo.PVPMODE_ENABLE:
			net.SendChatPacket("/pkmode 1", chat.CHAT_TYPE_TALKING)
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPTION_PVPMODE_NOT_SUPPORT)
	def __OnClickPvPModeFreeButton(self):
		if self.__CheckPvPProtectedLevelPlayer():
			return
		self.__RefreshPVPButtonList()
		if constInfo.PVPMODE_ENABLE:
			net.SendChatPacket("/pkmode 2", chat.CHAT_TYPE_TALKING)
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPTION_PVPMODE_NOT_SUPPORT)
	def __OnClickPvPModeGuildButton(self):
		if self.__CheckPvPProtectedLevelPlayer():
			return
		self.__RefreshPVPButtonList()
		if 0 == player.GetGuildID():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPTION_PVPMODE_CANNOT_SET_GUILD_MODE)
			return
		if constInfo.PVPMODE_ENABLE:
			net.SendChatPacket("/pkmode 4", chat.CHAT_TYPE_TALKING)
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPTION_PVPMODE_NOT_SUPPORT)
	def OnChangePKMode(self):
		self.__RefreshPVPButtonList()
	# PvP - Mode

	# Block - Mode
	def RefreshBlock(self):
		global blockMode
		for i in range(len(self.blockButtonList)):
			if 0 != (blockMode & (1 << i)):
				self.blockButtonList[i].Down()
			else:
				self.blockButtonList[i].SetUp()
	def OnBlockMode(self, mode):
		global blockMode
		blockMode = mode
		self.RefreshBlock()
	def __OnClickBlockExchangeButton(self):
		self.RefreshBlock()
		global blockMode
		net.SendChatPacket("/setblockmode " + str(blockMode ^ player.BLOCK_EXCHANGE))
	def __OnClickBlockPartyButton(self):
		self.RefreshBlock()
		global blockMode
		net.SendChatPacket("/setblockmode " + str(blockMode ^ player.BLOCK_PARTY))
	def __OnClickBlockGuildButton(self):
		self.RefreshBlock()
		global blockMode
		net.SendChatPacket("/setblockmode " + str(blockMode ^ player.BLOCK_GUILD))
	def __OnClickBlockWhisperButton(self):
		self.RefreshBlock()
		global blockMode
		net.SendChatPacket("/setblockmode " + str(blockMode ^ player.BLOCK_WHISPER))
	def __OnClickBlockFriendButton(self):
		self.RefreshBlock()
		global blockMode
		net.SendChatPacket("/setblockmode " + str(blockMode ^ player.BLOCK_FRIEND))
	def __OnClickBlockPartyRequest(self):
		self.RefreshBlock()
		global blockMode
		net.SendChatPacket("/setblockmode " + str(blockMode ^ player.BLOCK_PARTY_REQUEST))
		
	if app.ENABLE_VIEW_EQUIPMENT_SYSTEM:
		def __OnClickBlockViewEquipmentButton(self):
			self.RefreshBlock()
			global blockMode
			net.SendChatPacket("/setblockmode " + str(blockMode ^ player.BLOCK_EQUIPMENT_REQUEST))
		
	# Block - Mode

	# Chat - Mode
	def RefreshViewChat(self):
		if systemSetting.IsViewChat():
			self.viewChatButtonList[0].Down()
			self.viewChatButtonList[1].SetUp()
		else:
			self.viewChatButtonList[0].SetUp()
			self.viewChatButtonList[1].Down()
	def __OnClickViewChat(self):
		systemSetting.SetViewChatFlag(not systemSetting.IsViewChat())
		self.RefreshViewChat()
	# Chat - Mode

	# Name Color - Mode
	def __OnClickNameColorMode(self):
		systemSetting.SetNameColorModeOption(not systemSetting.GetNameColorModeOption())
		self.RefreshNameColor()
	def RefreshNameColor(self):
		index = systemSetting.GetNameColorModeOption()
		import chrmgr
		if index == 1:
			chrmgr.SetEmpireNameMode(1)
		else:
			chrmgr.SetEmpireNameMode(0)
		self.nameColorModeButtonList[index].Down()
		self.nameColorModeButtonList[not index].SetUp()
	# Name Color - Mode

	# Target Board - Mode
	def RefreshTargetBoard(self):
		index = systemSetting.GetTargetModeOption()
		if index == 1:
			constInfo.SET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD(1)
		else:
			constInfo.SET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD(0)
		self.viewTargetBoardButtonList[index].Down()
		self.viewTargetBoardButtonList[not index].SetUp()
	def __SetTargetBoardViewMode(self):
		systemSetting.SetTargetModeOption(not systemSetting.GetTargetModeOption())
		self.RefreshTargetBoard()
	# Target Board - Mode

	# Show Always Name - Mode
	def RefreshAlwaysShowName(self):
		index = systemSetting.IsAlwaysShowName()
		self.alwaysShowNameButtonList[index].SetUp()
		self.alwaysShowNameButtonList[not index].Down()
	def __OnClickAlwaysShowName(self):
		systemSetting.SetAlwaysShowNameFlag(not systemSetting.IsAlwaysShowName())
		self.RefreshAlwaysShowName()
	# Show Always Name - Mode

	def RefreshFamilyName(self):
		for button in self.familyNameButtonList:
			button.Enable() if systemSetting.CanChangeOwnFamilyNameVisibility() else button.Disable()
		index = 0 if systemSetting.IsOwnFamilyNameVisible() else 1
		self.__ClickRadioButton(self.familyNameButtonList, index)

	def __OnClickFamilyName(self, flag):
		if not systemSetting.CanChangeOwnFamilyNameVisibility():
			return
		systemSetting.SetOwnFamilyNameVisible(flag)
		self.RefreshFamilyName()

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

	if app.ENABLE_SCALE_OPTION:
		def OnStoneScaling(self):
			if not self.stoneScaling:
				return
			pos = float(self.stoneScaling.GetSliderPos())
			systemSetting.SetMetinstoneScale(pos)

	if app.ENABLE_SCALE_DAMAGE_TEXT:
		def OnDamageScaling(self):
			if not self.damageScaling:
				return
			pos = float(self.damageScaling.GetSliderPos())
			systemSetting.SetDamageTextureScale(pos)

	if app.ENABLE_QUEST_OPTION:
		def __OnClickQuestMode(self):
			systemSetting.SetQuestModeOption(not systemSetting.GetQuestModeOption())
			self.RefreshQuestMode()
		def RefreshQuestMode(self):
			index = systemSetting.GetQuestModeOption()
			self.questModeButtonList[index].Down()
			self.questModeButtonList[not index].SetUp()
	
			interface = osfInfo.GetInterfaceInstance()
			if interface != None:
				interfaceModule.IsQBHide = not index
				interface.DynamicArrangeQuestBtn()

	if app.ENABLE_FONT_OPTION:
		def __OnClickFontLevelButton(self, index):
			index = fontconfig.NormalizeFontLevel(index)
			self.__ClickRadioButton(self.fontLevelButtonList, index)
			osfInfo.CheckDirectory("UserData/font")
			if os.path.exists("UserData/font/fontoption.cfg"):
				os.remove("UserData/font/fontoption.cfg")
			f = open( "UserData/font/fontoption.cfg", "w")
			f.write("%d" % (index))
			f.close()
			self.popupDialog.Open(localeInfo.RESTART_CLIENT_DO_YOU_ACCEPT_1)
			self.fontLevel = index
			systemSetting.SetFontLevel(self.fontLevel)

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
			systemSetting.SetEffectLevel(self.effectLevel)

		# DropItem
		def __OnClickDropItemLevelButton(self, index):
			self.__ClickRadioButton(self.dropItemLevelButtonList, index)
			self.dropItemLevel = index
			systemSetting.SetDropItemLevel(self.dropItemLevel)
			
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

	if app.WJ_SHOW_MOB_INFO:
		def __OnClickShowMobLevelButton(self):
			if systemSetting.IsShowMobLevel():
				systemSetting.SetShowMobLevel(False)
			else:
				systemSetting.SetShowMobLevel(True)
			self.RefreshShowMobInfo()

		def __OnClickShowMobAIFlagButton(self):
			if systemSetting.IsShowMobAIFlag():
				systemSetting.SetShowMobAIFlag(False)
			else:
				systemSetting.SetShowMobAIFlag(True)
			self.RefreshShowMobInfo()

		def RefreshShowMobInfo(self):
			if systemSetting.IsShowMobLevel():
				self.showMobInfoButtonList[0].Down()
			else:
				self.showMobInfoButtonList[0].SetUp()

			if systemSetting.IsShowMobAIFlag():
				self.showMobInfoButtonList[1].Down()
			else:
				self.showMobInfoButtonList[1].SetUp()

	if app.ENABLE_GRAPHIC_ON_OFF:
		def RefreshCompanions(self):
			if systemSetting.IsShowPet():
				self.petStatusButtonList.Down()
				net.SendChatPacket("/show_hide_pet 1")
			else:
				self.petStatusButtonList.SetUp()
				net.SendChatPacket("/show_hide_pet 0")

			if systemSetting.IsShowMount():
				self.MountStatusButtonList.Down()
				net.SendChatPacket("/show_hide_mount 1")
			else:
				self.MountStatusButtonList.SetUp()
				net.SendChatPacket("/show_hide_mount 0")

			if systemSetting.IsShowSupport():
				self.SupportStatusButtonList.Down()
				net.SendChatPacket("/show_hide_support 1")	
			else:
				self.SupportStatusButtonList.SetUp()
				net.SendChatPacket("/show_hide_support 0")	

		def RefreshHideShop(self):
			if systemSetting.IsShowShop():
				self.ShopStatusButtonList.Down()
				net.SendChatPacket("/show_hide_shop 1")
			else:
				self.ShopStatusButtonList.SetUp()
				net.SendChatPacket("/show_hide_shop 0")

		def __OnClickPetButton(self, flag):
			systemSetting.SetShowPet(flag)	
			self.RefreshCompanions()

		def __OnClickShopButton(self, flag):
			systemSetting.SetShowShop(flag)	
			self.RefreshHideShop()

		def __OnClickMountButton(self, flag):
			systemSetting.SetShowMount(flag)
			self.RefreshCompanions()

		def __OnClickSupportButton(self, flag):
			systemSetting.SetShowSupport(flag)
			self.RefreshCompanions()

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

	# Show Damage - Mode
	def RefreshShowDamage(self):
		index = systemSetting.IsShowDamage()
		self.showDamageButtonList[index].SetUp()
		self.showDamageButtonList[not index].Down()
	def __OnClickShowDamage(self):
		systemSetting.SetShowDamageFlag(not systemSetting.IsShowDamage())
		self.RefreshShowDamage()
	# Show Damage - Mode

	# Sales Text - Mode
	def RefreshShowSalesText(self):
		if systemSetting.IsShowSalesText():
			self.showsalesTextButtonList[0].Down()
			self.showsalesTextButtonList[1].SetUp()
		else:
			self.showsalesTextButtonList[0].SetUp()
			self.showsalesTextButtonList[1].Down()
			
	def __OnClickSalesTextOnButton(self):
		systemSetting.SetShowSalesTextFlag(True)
		self.RefreshShowSalesText()
		uiPrivateShopBuilder.UpdateADBoard()

	def __OnClickSalesTextOffButton(self):
		systemSetting.SetShowSalesTextFlag(False)
		self.RefreshShowSalesText()
	# Sales Text - Mode

	# Sound - Mode
	def OnChangeSoundVolume(self):
		pos = self.ctrlSoundVolume.GetSliderPos()
		snd.SetSoundVolumef(pos)
		systemSetting.SetSoundVolumef(pos)
	# Sound - Mode

	def OnChangeShadowQuality(self):
		pos = self.ctrlShadowQuality.GetSliderPos()
		systemSetting.SetShadowLevel(int(pos / 0.2))

	# Music - Mode
	def OnChangeMusicVolume(self):
		pos = self.ctrlMusicVolume.GetSliderPos()
		snd.SetMusicVolume(pos * net.GetFieldMusicVolume())
		systemSetting.SetMusicVolume(pos)
	def __OnChangeMusic(self, fileName):
		self.selectMusicFile.SetText(fileName[:MUSIC_FILENAME_MAX_LEN])
		if musicInfo.fieldMusic != "":
			snd.FadeOutMusic("BGM/"+ musicInfo.fieldMusic)
		if fileName==uiSelectMusic.DEFAULT_THEMA:
			musicInfo.fieldMusic=musicInfo.METIN2THEMA
		else:
			musicInfo.fieldMusic=fileName
		musicInfo.SaveLastPlayFieldMusic()
		if musicInfo.fieldMusic != "":
			snd.FadeInMusic("BGM/" + musicInfo.fieldMusic)
	def __OnClickChangeMusicButton(self):
		if not self.musicListDlg:
			self.musicListDlg=uiSelectMusic.FileListDialog()
			self.musicListDlg.SAFE_SetSelectEvent(self.__OnChangeMusic)
		self.musicListDlg.Open()
	# Music - Mode

	# Camera - Mode
	def __OnClickCameraMode(self):
		systemSetting.SetCameraModeOption(not systemSetting.GetCameraModeOption())
		self.RefreshCameraMode()

	def RefreshCameraMode(self):
		index = systemSetting.GetCameraModeOption()
		if index == 1:
			app.SetCameraMaxDistance(3500.0 * 2)
		else:
			app.SetCameraMaxDistance(2500.0)

		self.cameraModeButtonList[index].Down()
		self.cameraModeButtonList[not index].SetUp()
	# Camera - Mode

	if app.ENABLE_FOG_FIX:
		def __OnClickFogModeOnButton(self):
			systemSetting.SetFogMode(True)
			background.SetFogMode(True)
			self.__ClickRadioButton(self.fogButtonList, 1)

		def __OnClickFogModeOffButton(self):
			systemSetting.SetFogMode(False)
			background.SetFogMode(False)
			self.__ClickRadioButton(self.fogButtonList, 0)

	def __JTX_FullMapStatusMsg(self, want):
		try:
			active = int(background.IsFullMapRenderActive())
		except:
			active = -1

		wantTxt = "ON" if want else "OFF"
		if active < 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO,
				uiScriptLocale.OPTION_GAMEOPTION_FULL_MAP_STATUS_WANT % wantTxt)
		elif want and not active:
			chat.AppendChat(chat.CHAT_TYPE_INFO,
				uiScriptLocale.OPTION_GAMEOPTION_FULL_MAP_STATUS_BLOCKED)
		elif want and active:
			chat.AppendChat(chat.CHAT_TYPE_INFO,
				uiScriptLocale.OPTION_GAMEOPTION_FULL_MAP_STATUS_ACTIVE)
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO,
				uiScriptLocale.OPTION_GAMEOPTION_FULL_MAP_STATUS_OFF)

	def __OnClickFullMapRenderOn(self):
		systemSetting.SetFullMapRender(1)
		self.__ClickRadioButton(self.fullMapRenderButtonList, 0)
		self.__JTX_FullMapStatusMsg(1)

	def __OnClickFullMapRenderOff(self):
		systemSetting.SetFullMapRender(0)
		self.__ClickRadioButton(self.fullMapRenderButtonList, 1)
		self.__JTX_FullMapStatusMsg(0)

	def __JTX_GetSkyboxPresets(self):
		return SKYBOX_PRESETS

	def __JTX_RefreshSkyboxLabel(self, slotIndex):
		if self.skyboxCurrentText is None:
			return
		presets = self.__JTX_GetSkyboxPresets()
		if slotIndex < 0 or slotIndex >= len(presets):
			slotIndex = 0
		label = _GetSkyboxLabel(slotIndex)
		self.skyboxCurrentText.SetText(uiScriptLocale.OPTION_GAMEOPTION_SKYBOX_CURRENT % label)

	def __OnClickSkyboxSlot(self, slotIndex):
		presets = self.__JTX_GetSkyboxPresets()
		if slotIndex < 0 or slotIndex >= len(presets):
			return

		engineSlot, msenvPath = presets[slotIndex]

		if not msenvPath:
			try:
				background.ClearUserEnvironmentSlot()
			except:
				dbg.TraceError("[Skybox] Echec ClearUserEnvironmentSlot()")
				return
		else:
			if not app.IsExistFile(msenvPath):
				dbg.TraceError("[Skybox] Fichier introuvable : %s" % str(msenvPath))
				chat.AppendChat(chat.CHAT_TYPE_INFO,
					uiScriptLocale.OPTION_GAMEOPTION_SKYBOX_FILE_NOT_FOUND % str(msenvPath))
				return
			try:
				if engineSlot not in self._skyboxLoadedEngineSlots:
					background.RegisterEnvironmentData(engineSlot, msenvPath)
					self._skyboxLoadedEngineSlots.add(engineSlot)
			except:
				dbg.TraceError("[Skybox] Echec RegisterEnvironmentData(%d)" % engineSlot)
				return
			try:
				background.SetUserEnvironmentSlot(engineSlot)
			except (AttributeError, RuntimeError):
				dbg.TraceError("[Skybox] Echec sky-only overlay (%d)" % engineSlot)
				return

		systemSetting.SetSkyboxPreset(slotIndex)
		self.__ClickRadioButton(self.skyboxButtonList, slotIndex)
		self.__JTX_RefreshSkyboxLabel(slotIndex)

	if app.ENABLE_OUTLINE_NAME_SHADOW:
		def RefreshOulineName(self):
			index = systemSetting.GetNamesType()
			self.showOutlinedNamesList[index].SetUp()
			self.showOutlinedNamesList[not index].Down()
		def __OnClickOulineName(self):
			systemSetting.SetNamesType(not systemSetting.GetNamesType())
			self.RefreshOulineName()

	if app.ENABLE_HIDE_AFFECT_ICONS:
		def RefreshAffectIcons(self):
			index = systemSetting.IsAffectIconShow()
			self.showAffectIconsList[index].SetUp()
			self.showAffectIconsList[not index].Down()
		def __OnClickAffectIcons(self):
			osfInfo.AffectIconState = 1
			systemSetting.SetEffectIconShow(not systemSetting.IsAffectIconShow())
			self.RefreshAffectIcons()

	if app.ENABLE_AREA_OPTIMISATION:
		def OnObjectScaling(self):
			if not self.objectScaling:
				return
			pos = float(self.objectScaling.GetSliderPos())
			systemSetting.SetLoadingDistance(pos)

	if app.ENABLE_SHARPNESS:
		DEFAULT_SHARPNESS_POWER = 1.0
		MAX_SHARPNESS_POWER = 2.0

		def OnSharpnessChange(self):
			if not self.sharpnessSlider:
				return
			pos = float(self.sharpnessSlider.GetSliderPos())
			systemSetting.SetSharpnessPower(pos * self.MAX_SHARPNESS_POWER)

			if self.sharpnessValueText:
				self.sharpnessValueText.SetText("%.2f" % systemSetting.GetSharpnessPower())

		def __OnClickSharpnessResetButton(self):
			if self.sharpnessSlider:
				self.sharpnessSlider.SetSliderPos(self.DEFAULT_SHARPNESS_POWER / self.MAX_SHARPNESS_POWER)
			systemSetting.SetSharpnessPower(self.DEFAULT_SHARPNESS_POWER)

			if self.sharpnessValueText:
				self.sharpnessValueText.SetText("%.2f" % systemSetting.GetSharpnessPower())

	if app.ENABLE_DROP_INFO_WINDOW:
		def SetDropMode(self, index):
			if index == 3: 
				newYangState = not systemSetting.IsShowYang()
				systemSetting.SetShowYang(newYangState)
			else:
				systemSetting.SetDropInfomation(index)

				for key in ["drop_option_window", "drop_option_chat", "drop_option_all"]:
					self.dropButtonList[key].SetUp()

				if index == 0:
					self.dropButtonList["drop_option_window"].Down()
				elif index == 1:
					self.dropButtonList["drop_option_chat"].Down()
				elif index == 2:
					self.dropButtonList["drop_option_all"].Down()

		def RefreshDropMode(self):
			index = systemSetting.GetDropInfomation()
			showYang = systemSetting.IsShowYang()

			for key in ["drop_option_window", "drop_option_chat", "drop_option_all", "drop_option_gold"]:
				self.dropButtonList[key].SetUp()

			if index == 0:
				self.dropButtonList["drop_option_window"].Down()
			elif index == 1:
				self.dropButtonList["drop_option_chat"].Down()
			elif index == 2:
				self.dropButtonList["drop_option_all"].Down()

			if showYang:
				self.dropButtonList["drop_option_gold"].Down()

		def __OnClickDropWindowButton(self):
			self.SetDropMode(0)

		def __OnClickDropChatButton(self):
			self.SetDropMode(1)

		def __OnClickDropAllOffButton(self):
			self.SetDropMode(2)

		def __OnClickDropYangToggleButton(self):
			self.SetDropMode(3)

	def __GetDropTrackerInterface(self):
		try:
			interface = osfInfo.GetInterfaceInstance()
			if interface and getattr(
				interface, "dropTrackerSystem", None
			):
				return interface
		except:
			pass
		return None

	def OpenSystemNotificationSettings(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface and getattr(interface, "systemNotifications", None):
			self.Hide()
			interface.OpenSystemNotificationSettings()

	def RefreshDropTrackerPlacement(self):
		if len(self.dropTrackerPlacementButtonList) != 2:
			return
		interface = self.__GetDropTrackerInterface()
		mode = (
			interface.GetDropTrackerPlacementMode()
			if interface else "taskbar"
		)
		for button in self.dropTrackerPlacementButtonList:
			if interface:
				button.Enable()
			else:
				button.SetUp()
				button.Disable()
		if interface:
			# CButton::Enable() calls SetUp(), so select only after both
			# controls have been enabled or the visible radio state is lost.
			self.__ClickRadioButton(
				self.dropTrackerPlacementButtonList,
				1 if mode == "free" else 0,
			)
		canEdit = bool(interface and mode == "free")
		for button in (
			self.dropTrackerPlacementEditButton,
			self.dropTrackerPlacementResetButton,
		):
			if not button:
				continue
			if canEdit:
				button.Enable()
			else:
				button.Disable()

	def __OnClickDropTrackerPlacement(self, mode):
		interface = self.__GetDropTrackerInterface()
		if interface:
			interface.SetDropTrackerPlacementMode(mode)
		self.RefreshDropTrackerPlacement()

	def __OnClickDropTrackerPlacementEdit(self):
		interface = self.__GetDropTrackerInterface()
		if interface and interface.BeginDropTrackerPlacementEdit():
			self.Hide()

	def __OnClickDropTrackerPlacementReset(self):
		interface = self.__GetDropTrackerInterface()
		if interface:
			interface.ResetDropTrackerFloatingPlacement()
		self.RefreshDropTrackerPlacement()

	def __GetCostumeInventoryInterface(self):
		try:
			interface = osfInfo.GetInterfaceInstance()
			if interface and getattr(
					interface, "wndCostumeInventory", None):
				return interface
		except:
			pass
		return None

	def RefreshCostumeInventoryMode(self):
		if len(self.costumeInventoryModeButtonList) != 2:
			return
		interface = self.__GetCostumeInventoryInterface()
		for button in self.costumeInventoryModeButtonList:
			if interface:
				button.Enable()
			else:
				button.SetUp()
				button.Disable()
		if interface:
			self.__ClickRadioButton(
				self.costumeInventoryModeButtonList,
				1 if interface.IsSeparateCostumeInventory() else 0,
			)

	def __OnClickCostumeInventoryMode(self, separate):
		interface = self.__GetCostumeInventoryInterface()
		if interface:
			interface.SetSeparateCostumeInventory(bool(separate))
		self.RefreshCostumeInventoryMode()

ScrollBarNew = SettingsScrollBar

if app.ENABLE_FONT_OPTION:
	class PopupDialog(ui.ScriptWindow):
		def __init__(self, parent):
			print("PopupDialog::PopupDialog()")
			ui.ScriptWindow.__init__(self)

			self.__Load()
			self.__Bind()

		def __del__(self):
			ui.ScriptWindow.__del__(self)
			print("PopupDialog::~PopupDialog()")

		def __Load(self):
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "UIScript/PopupDialog.py")
			except:
				import exception
				exception.Abort("PopupDialog.__Load")

		def __Bind(self):
			try:
				self.textLine=self.GetChild("message")
				self.okButton=self.GetChild("accept")
			except:
				import exception
				exception.Abort("PopupDialog.__Bind")

			self.okButton.SAFE_SetEvent(self.__OnOK)

		def Open(self, msg):
			self.textLine.SetText(msg)
			self.SetCenterPosition()
			self.Show()
			self.SetTop()

		def __OnOK(self):
			self.Hide()
