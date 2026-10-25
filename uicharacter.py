import ui
import uiScriptLocale
import app
import net
import dbg
import snd
import player
import mouseModule
import wndMgr
import skill
import playerSettingModule
import quest
import localeInfo
import uiToolTip
import constInfo
import osfInfo
import emotion
import chr
import chat
import item
import skillpresentation
import skillraise
import skillgradecount
import uicharacterbuff
import uiluckknot
import bonuscolor

SKILL_GRADE_SAGE_MASTER = getattr(player, "SKILL_GRADE_SAGE_MASTER", None)

if app.ENABLE_DETAILS_UI:
	import uiCharacterDetails

if app.ENABLE_SKILL_COLOR_SYSTEM:
	import uiSkillColor

if app.ENABLE_LOADING_PERFORMANCE:
	import loading

SHOW_ONLY_ACTIVE_SKILL = False
SHOW_LIMIT_SUPPORT_SKILL_LIST = [123, 124, 135]
HIDE_SUPPORT_SKILL_POINT = False

PERMANENT_TASK_ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/permanent_tasks/"
PERMANENT_TASK_SKILL_ENTRIES = (
	("bossologie", 92, 221, "passive_bossologie_32.png"),
	("kamenologie", 129, 221, "passive_kamenologie_32.png"),
)
# What the three permanent passives among the standard skills give (the skill tooltip shows it as the description
# of every other skill of the page): the locale key, the Czech text when the locale has none.
PERMANENT_PASSIVE_DESCRIPTIONS = {
	"bossologie": ("PERMANENT_TASKS_BOSS_DESC",
		u"Trvalý bonus proti bossům za dokončené stupně lovu bossů v Trvalých úkolech."),
	"kamenologie": ("PERMANENT_TASKS_STONE_DESC",
		u"Trvalý bonus proti meteorům za dokončené stupně lovu meteorů v Trvalých úkolech."),
	"luck_knot": ("LUCK_KNOT_DESC",
		u"Zvyšuje šanci na Althea meteor, na dvojitou kořist z meteorů a bossů a na vylepšení rarity. "
		u"Vylepšuje se pečetěmi a Yangy."),
}

QUEST_SCROLL_ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/quest/scroll/"
QUEST_SCROLL_NORMAL = QUEST_SCROLL_ASSET_ROOT + "quest_scroll_normal.png"
QUEST_SCROLL_HOVER = QUEST_SCROLL_ASSET_ROOT + "quest_scroll_hover.png"
QUEST_SCROLL_PRESSED = QUEST_SCROLL_ASSET_ROOT + "quest_scroll_pressed.png"
QUEST_NAME_COLOR = 0xffeadfc8
QUEST_META_COLOR = 0xffa99e8a


def _GetRenderableQuestData():
	questDataList = []
	for questDataIndex in range(quest.GetQuestCount()):
		questData = quest.GetQuestData(questDataIndex)
		if app.ENABLE_QUEST_RENEWAL:
			questName = questData[1]
		else:
			questName = questData[0]

		displayName = questName
		if displayName and displayName[0] in "*&~":
			displayName = displayName[1:]
		if not displayName or not displayName.strip():
			continue

		questDataList.append((questDataIndex, questData))

	return questDataList

if localeInfo.IsYMIR():
	if not localeInfo.IsCHEONMA():
		HIDE_SUPPORT_SKILL_POINT = True
elif localeInfo.IsJAPAN() or (localeInfo.IsEUROPE() and app.GetLocalePath() != "locale/ca") and (localeInfo.IsEUROPE() and app.GetLocalePath() != "locale/br"):
	HIDE_SUPPORT_SKILL_POINT = True
else:
	HIDE_SUPPORT_SKILL_POINT = True

FACE_IMAGE_DICT = {
	playerSettingModule.RACE_WARRIOR_M : "icon/face/warrior_m.tga",
	playerSettingModule.RACE_WARRIOR_W : "icon/face/warrior_w.tga",
	playerSettingModule.RACE_ASSASSIN_M : "icon/face/assassin_m.tga",
	playerSettingModule.RACE_ASSASSIN_W : "icon/face/assassin_w.tga",
	playerSettingModule.RACE_SURA_M : "icon/face/sura_m.tga",
	playerSettingModule.RACE_SURA_W : "icon/face/sura_w.tga",
	playerSettingModule.RACE_SHAMAN_M : "icon/face/shaman_m.tga",
	playerSettingModule.RACE_SHAMAN_W : "icon/face/shaman_w.tga",
	playerSettingModule.RACE_WOLFMAN_M : "icon/face/wolfman_m.tga",
}

def unsigned32(n):
	return n & 0xFFFFFFFF

class CharacterWindow(ui.ScriptWindow):
	if app.ENABLE_CONQUEROR_LEVEL:
		ACTIVE_PAGE_SLOT_COUNT = 10
		SUPPORT_PAGE_SLOT_COUNT = 18
	else:
		ACTIVE_PAGE_SLOT_COUNT = 8
		SUPPORT_PAGE_SLOT_COUNT = 12

	PAGE_SLOT_COUNT = 12

	SKILL_GROUP_NAME_DICT = {
		playerSettingModule.JOB_WARRIOR : { 1 : localeInfo.SKILL_GROUP_WARRIOR_1, 2 : localeInfo.SKILL_GROUP_WARRIOR_2, },
		playerSettingModule.JOB_ASSASSIN : { 1 : localeInfo.SKILL_GROUP_ASSASSIN_1, 2 : localeInfo.SKILL_GROUP_ASSASSIN_2, },
		playerSettingModule.JOB_SURA : { 1 : localeInfo.SKILL_GROUP_SURA_1, 2 : localeInfo.SKILL_GROUP_SURA_2, },
		playerSettingModule.JOB_SHAMAN : { 1 : localeInfo.SKILL_GROUP_SHAMAN_1, 2 : localeInfo.SKILL_GROUP_SHAMAN_2, },
		playerSettingModule.JOB_WOLFMAN : { 1 : localeInfo.JOB_WOLFMAN1, 2 : localeInfo.JOB_WOLFMAN2, },
	}

	STAT_DESCRIPTION = {
		"HTH" : localeInfo.STAT_TOOLTIP_CON,
		"INT" : localeInfo.STAT_TOOLTIP_INT,
		"STR" : localeInfo.STAT_TOOLTIP_STR,
		"DEX" : localeInfo.STAT_TOOLTIP_DEX,
	}
	if app.ENABLE_CONQUEROR_LEVEL:
		STAT_DESCRIPTION.update({
			"SSTR" : localeInfo.STAT_TOOLTIP_SUNGMA_STR,
			"SHP" : localeInfo.STAT_TOOLTIP_SUNGMA_HP,
			"SMOVE" : localeInfo.STAT_TOOLTIP_SUNGMA_MOVE,
			"SIMMUNE" : localeInfo.STAT_TOOLTIP_SUNGMA_IMMUNE,
		})

	STAT_MINUS_DESCRIPTION = localeInfo.STAT_MINUS_DESCRIPTION

	def __init__(self):
		if app.ENABLE_DETAILS_UI:
			self.chDetailsWnd = None
			self.isOpenedDetailsWnd = False

		if app.ENABLE_SKILL_COLOR_SYSTEM:
			self.skillColorWnd = None
			self.skillColorButton = []

		ui.ScriptWindow.__init__(self)
		self.state = "STATUS"
		self.isLoaded = 0
		self.r1Skin = None

		self.toolTipSkill = 0

		self.__Initialize()
		self.__LoadWindow()
		try:
			import uir1
			uir1.FollowLook(self)
		except Exception:
			pass

		self.statusPlusCommandDict = {
			"HTH" : "/stat ht",
			"INT" : "/stat iq",
			"STR" : "/stat st",
			"DEX" : "/stat dx",
		}

		self.statusMinusCommandDict = {
			"HTH-" : "/stat- ht",
			"INT-" : "/stat- iq",
			"STR-" : "/stat- st",
			"DEX-" : "/stat- dx",
		}

		if app.ENABLE_CONQUEROR_LEVEL:
			self.statusConquerorPlusCommandDict = {
				"SSTR" : "/conqueror_point sstr",
				"SHP" : "/conqueror_point shp",
				"SMOVE" : "/conqueror_point smove",
				"SIMMUNE" : "/conqueror_point simmune",
			}

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.refreshToolTip = 0
		self.selectedSkillTab = 0
		self.buffPage = None
		self.skillGradeCounts = {}
		self.skillHeaderRow = None
		self.skillPointArea = None

		self.toolTip = None
		self.toolTipJob = None
		self.toolTipAlignment = None
		self.toolTipSkill = None
		self.permanentTaskButtons = {}
		self.permanentTaskLevels = {}
		self.permanentTaskProgress = {}
		self.permanentTaskTooltipCategory = None
		self.luckKnotButton = None
		self.luckKnotLevel = None
		self.luckKnotPlus = None
		self.luckKnotSnapshot = None
		self.luckKnotAvailable = False
		self.luckKnotUpgradeDialog = None
		self.luckKnotUpgradeQuote = None
		self.luckKnotUpgradePending = False
		self.faceImage = None
		self.statusPlusLabel = None
		self.statusPlusValue = None
		self.activeSlot = None
		self.tabDict = None
		self.tabButtonDict = None
		self.pageDict = None
		self.titleBarDict = None
		self.statusPlusButtonDict = None
		self.statusMinusButtonDict = None

		self.skillPageDict = None
		self.questShowingStartIndex = 0
		self.questScrollBar = None
		self.questSlot = None
		self.questNameList = None
		self.questLastTimeList = None
		self.questLastCountList = None
		self.questRowButtonList = []
		self.questShortcutIconList = []
		self.questShortcutList = []
		self.questActionMap = {}
		self.questDataIndexMap = {}
		self.questIndexMap = {}
		self.questClicked = []
		self.skillGroupButton = ()

		self.activeSlot = None
		self.activeSkillPointValue = None
		self.supportSkillPointValue = None
		self.skillGroupButton1 = None
		self.skillGroupButton2 = None
		self.activeSkillGroupName = None

		self.guildNameSlot = None
		self.guildNameValue = None
		self.characterNameSlot = None
		self.characterNameValue = None

		self.emotionToolTip = None
		self.soloEmotionSlot = None
		self.dualEmotionSlot = None
		if app.ENABLE_EXPRESSING_EMOTION:
			self.specialEmotionSlot = None

		if app.ENABLE_SKILL_COLOR_SYSTEM:
			self.skillColorWnd = None
			self.skillColorButton = []

		if app.ENABLE_DETAILS_UI:
			self.chDetailsWnd = None
			self.isOpenedDetailsWnd = False

		if app.ENABLE_CONQUEROR_LEVEL:
			self.levelType = 0

			self.tabLevelInfoButtonDict = None
			self.tabLevelInfoPageDict = None
			self.statusConquerorPlusButtonDict = None

			self.passive_expanded_btn = None

	if app.ENABLE_DETAILS_UI:
		def OnTop(self):
			if self.chDetailsWnd:
				self.chDetailsWnd.SetTop()

			if app.ENABLE_SKILL_COLOR_SYSTEM:
				if self.skillColorWnd:
					self.skillColorWnd.SetTop()

	def Hide(self):
		self.__CloseLuckKnotUpgrade()
		self.__HideStatToolTip()
		self.OverOutItem()
		if app.ENABLE_DETAILS_UI:
			if self.chDetailsWnd:
				self.isOpenedDetailsWnd = self.chDetailsWnd.IsShow()
				self.chDetailsWnd.Close()

		if app.ENABLE_SKILL_COLOR_SYSTEM:
			if self.skillColorWnd and self.skillColorWnd.IsShow():
				self.skillColorWnd.Close()

		wndMgr.Hide(self.hWnd)

	def Show(self):
		self.__LoadWindow()

		if app.ENABLE_DETAILS_UI:
			self.__InitCharacterDetailsUIButton()
			if self.chDetailsWnd and self.isOpenedDetailsWnd:
				self.chDetailsWnd.Show()

		ui.ScriptWindow.Show(self)

	def __LoadScript(self, fileName):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, fileName)

	def __BindObject(self):
		self.toolTip = uiToolTip.ToolTip()
		self.toolTipJob = uiToolTip.ToolTip()
		self.toolTipAlignment = uiToolTip.ToolTip(130)
		self.faceImage = self.GetChild("Face_Image")

		faceSlot=self.GetChild("Face_Slot")
		if 949 == app.GetDefaultCodePage():
			faceSlot.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__ShowJobToolTip)
			faceSlot.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__HideJobToolTip)

		self.statusPlusLabel = self.GetChild("Status_Plus_Label")
		self.statusPlusValue = self.GetChild("Status_Plus_Value")

		self.characterNameSlot = self.GetChild("Character_Name_Slot")
		self.characterNameValue = self.GetChild("Character_Name")
		self.guildNameSlot = self.GetChild("Guild_Name_Slot")
		self.guildNameValue = self.GetChild("Guild_Name")
		self.characterNameSlot.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__ShowAlignmentToolTip)
		self.characterNameSlot.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__HideAlignmentToolTip)

		self.activeSlot = self.GetChild("Skill_Active_Slot")
		self.activeSkillPointValue = self.GetChild("Active_Skill_Point_Value")
		self.supportSkillPointValue = self.GetChild("Support_Skill_Point_Value")
		self.skillGroupButton1 = self.GetChild("Skill_Group_Button_1")
		self.skillGroupButton2 = self.GetChild("Skill_Group_Button_2")
		self.activeSkillGroupName = self.GetChild("Active_Skill_Group_Name")

		self.questScrollBar = self.GetChild("Quest_ScrollBar")
		self.questSlot = self.GetChild("Quest_Slot")
		self.questSlot.AddFlag("not_pick")
		self.questNameList = []
		self.questLastTimeList = []
		self.questLastCountList = []
		self.questRowButtonList = []
		for i in range(quest.QUEST_MAX_NUM):
			rowButton = self.GetChild("Quest_Row_0" + str(i))
			rowButton.SetEvent(ui.__mem_func__(self.__SelectQuest), i)
			rowButton.Hide()
			self.questRowButtonList.append(rowButton)
			self.questNameList.append(self.GetChild("Quest_Name_0" + str(i)))
			self.questLastTimeList.append(self.GetChild("Quest_LastTime_0" + str(i)))
			self.questLastCountList.append(self.GetChild("Quest_LastCount_0" + str(i)))
			self.questNameList[i].SetPackedFontColor(QUEST_NAME_COLOR)
			self.questLastTimeList[i].SetPackedFontColor(QUEST_META_COLOR)
			self.questLastCountList[i].SetPackedFontColor(QUEST_META_COLOR)
		self.__CreateQuestShortcutIcons()

		self.tabDict = {
			"STATUS" : self.GetChild("Tab_01"),
			"SKILL" : self.GetChild("Tab_02"),
			"EMOTICON" : self.GetChild("Tab_03"),
			"QUEST" : self.GetChild("Tab_04"),
		}

		self.tabButtonDict = {
			"STATUS" : self.GetChild("Tab_Button_01"),
			"SKILL" : self.GetChild("Tab_Button_02"),
			"EMOTICON" : self.GetChild("Tab_Button_03"),
			"QUEST" : self.GetChild("Tab_Button_04")
		}

		self.pageDict = {
			"STATUS" : self.GetChild("Character_Page"),
			"SKILL" : self.GetChild("Skill_Page"),
			"EMOTICON" : self.GetChild("Emoticon_Page"),
			"QUEST" : self.GetChild("Quest_Page")
		}

		self.titleBarDict = {
			"STATUS" : self.GetChild("Character_TitleBar"),
			"SKILL" : self.GetChild("Skill_TitleBar"),
			"EMOTICON" : self.GetChild("Emoticon_TitleBar"),
			"QUEST" : self.GetChild("Quest_TitleBar")
		}

		self.statusPlusButtonDict = {
			"HTH" : self.GetChild("HTH_Plus"),
			"INT" : self.GetChild("INT_Plus"),
			"STR" : self.GetChild("STR_Plus"),
			"DEX" : self.GetChild("DEX_Plus"),
		}

		self.statusMinusButtonDict = {
			"HTH-" : self.GetChild("HTH_Minus"),
			"INT-" : self.GetChild("INT_Minus"),
			"STR-" : self.GetChild("STR_Minus"),
			"DEX-" : self.GetChild("DEX_Minus"),
		}

		self.skillPageDict = {
			"ACTIVE" : self.GetChild("Skill_Active_Slot"),
			"SUPPORT" : self.GetChild("Skill_ETC_Slot"),
		}

		self.skillPageStatDict = {
			"SUPPORT" : player.SKILL_SUPPORT,
			"ACTIVE" : player.SKILL_ACTIVE,
		}

		self.skillGroupButton = (
			self.GetChild("Skill_Group_Button_1"),
			self.GetChild("Skill_Group_Button_2"),
		)

		if app.ENABLE_CONQUEROR_LEVEL:
			self.tabLevelInfoButtonDict = {
				player.LEVEL_TYPE_BASE : self.GetChild("change_base_button"),
				player.LEVEL_TYPE_CONQUEROR : self.GetChild("change_conqueror_button")
			}

			self.tabLevelInfoPageDict = {
				player.LEVEL_TYPE_BASE : self.GetChild("base_info"),
				player.LEVEL_TYPE_CONQUEROR : self.GetChild("sungma_info"),
			}

			self.statusConquerorPlusButtonDict = {
				"SSTR" : self.GetChild("sungma_str_plus"),
				"SHP" : self.GetChild("sungma_hp_plus"),
				"SMOVE" : self.GetChild("sungma_move_plus"),
				"SIMMUNE" : self.GetChild("sungma_immune_plus"),
			}

			## TabButton1 (Character)
			self.GetChild("Tab_Button_01").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_TAB_CHARACTER)
			self.GetChild("Tab_Button_01").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))
			## TabButton2 (Skill)
			self.GetChild("Tab_Button_02").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_TAB_SKILL)
			self.GetChild("Tab_Button_02").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))
			## TabButton3 (Emoticon)
			self.GetChild("Tab_Button_03").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_TAB_EMOTICON)
			self.GetChild("Tab_Button_03").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))
			## TabButton4 (Quest)
			self.GetChild("Tab_Button_04").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_TAB_QUEST)
			self.GetChild("Tab_Button_04").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))

			## Level
			self.GetChild("Lv_ToolTip").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_LEVEL)
			self.GetChild("Lv_ToolTip").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))
			## EXP
			self.GetChild("Exp_ToolTip").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_EXP)
			self.GetChild("Exp_ToolTip").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))

			## Base Level
			self.GetChild("change_base_button").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_BASE_LEVEL)
			self.GetChild("change_base_button").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))
			## Conqueror Level
			self.GetChild("change_conqueror_button").SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_CONQUEROR_LEVEL)
			self.GetChild("change_conqueror_button").SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))
			## Passive Relic
			self.passive_expanded_btn = self.GetChild("passive_expanded_btn")
			self.passive_expanded_btn.SetShowToolTipEvent(ui.__mem_func__(self.__ShowToolTipButton), localeInfo.STAT_TOOLTIP_PASSIVE)
			self.passive_expanded_btn.SetHideToolTipEvent(ui.__mem_func__(self.__HideToolTip))
			self.passive_expanded_btn.Hide()

			## Char Status Info
			self.GetChild("Char_Info_Status_img").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_STAT : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("Char_Info_Status_img").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## Status Plus Points
			self.GetChild("Status_Plus_Label").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_POINT : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("Status_Plus_Label").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

			## CON (Constitution)
			self.GetChild("HTH_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_IMG_CON : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("HTH_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## INT (Intelligence)
			self.GetChild("INT_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_IMG_INT : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("INT_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## STR (Strength)
			self.GetChild("STR_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_IMG_STR : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("STR_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## DEX (Dexterity)
			self.GetChild("DEX_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_IMG_DEX : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("DEX_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

			## HP (Health)
			self.GetChild("HEL_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_HP : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("HEL_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## SP (Stamina)
			self.GetChild("SP_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_SP : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("SP_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## ATT (Attack)
			self.GetChild("ATT_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_ATT : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("ATT_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## DEF (Defense)
			self.GetChild("DEF_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_DEF : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("DEF_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

			## MSPD (Move Speed)
			self.GetChild("MSPD_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_MOVE_SPEED : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("MSPD_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## ASPD (Attack Speed)
			self.GetChild("ASPD_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_ATT_SPEED : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("ASPD_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## CSPD (Cast Speed)
			self.GetChild("CSPD_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_CAST_SPEED : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("CSPD_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## MATT (Magic Attack)
			self.GetChild("MATT_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_MAG_ATT : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("MATT_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## MDEF (Magic Defense)
			self.GetChild("MDEF_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_MAG_DEF : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("MDEF_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## EF (Evasion Resistance)
			self.GetChild("ER_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_DODGE_PER : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("ER_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

			## SUNGMA_STR
			self.GetChild("SUNGMA_STR_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_SUNGMA_STR : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("SUNGMA_STR_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## SUNGMA_HP
			self.GetChild("SUNGMA_HP_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_SUNGMA_HP : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("SUNGMA_HP_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## SUNGMA_MOVE
			self.GetChild("SUNGMA_MOVE_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_SUNGMA_MOVE : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("SUNGMA_MOVE_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## SUNGMA_IMMUNE
			self.GetChild("SUNGMA_IMMUNE_IMG").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_SUNGMA_IMMUNE : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("SUNGMA_IMMUNE_IMG").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

			## Active Skill Point Label
			self.GetChild("Active_Skill_Point_Label").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_POINT : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("Active_Skill_Point_Label").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			## Support Skill Point Label
			self.GetChild("Support_Skill_ToolTip").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_SUPPORT_SKILL : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("Support_Skill_ToolTip").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

			self.GetChild("Action_Bar_Img").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_ACTION : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("Action_Bar_Img").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			self.GetChild("Reaction_Bar_Img").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_REACTION : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("Reaction_Bar_Img").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()
			self.GetChild("Special_Action_Bar_Img").OnMouseOverIn = lambda arg = localeInfo.STAT_TOOLTIP_SPECIAL_ACTION : ui.__mem_func__(self.__ShowToolTip)(arg)
			self.GetChild("Special_Action_Bar_Img").OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

		global SHOW_ONLY_ACTIVE_SKILL
		global HIDE_SUPPORT_SKILL_POINT
		if SHOW_ONLY_ACTIVE_SKILL or HIDE_SUPPORT_SKILL_POINT:
			self.GetChild("Support_Skill_Point_Label").Hide()

		self.soloEmotionSlot = self.GetChild("SoloEmotionSlot")
		self.dualEmotionSlot = self.GetChild("DualEmotionSlot")
		if app.ENABLE_EXPRESSING_EMOTION:
			self.specialEmotionSlot = self.GetChild("SpecialEmotionSlot")
		self.__SetEmotionSlot()

		self.questShowingStartIndex = 0
		self.questScrollBar.SetScrollEvent(ui.__mem_func__(self.OnQuestScroll))
		for i in range(quest.QUEST_MAX_NUM):
			self.questSlot.HideSlotBaseImage(i)
			self.questSlot.SetCoverButton(i,\
				QUEST_SCROLL_NORMAL,\
				QUEST_SCROLL_HOVER,\
				QUEST_SCROLL_PRESSED,\
				QUEST_SCROLL_NORMAL, True)

		if app.ENABLE_DETAILS_UI:
			"""
				Note : Belt 이미지가 반대라서, 버튼 이미지는 반대로 사용
			"""
			self.MainBoard = self.GetChild("board")
			self.ExpandBtn = ui.MakeButton(self.MainBoard, 240, 120, "", "d:/ymir work/ui/game/belt_inventory/", "btn_minimize_normal.tga", "btn_minimize_over.tga", "btn_minimize_down.tga")
			self.ExpandBtn.SetEvent(ui.__mem_func__(self.__ClickExpandButton))
			self.MinimizeBtn = ui.MakeButton(self.MainBoard, 240, 120, "", "d:/ymir work/ui/game/belt_inventory/", "btn_expand_normal.tga", "btn_expand_over.tga", "btn_expand_down.tga")
			self.MinimizeBtn.SetEvent(ui.__mem_func__(self.__ClickMinimizeButton))
			if app.ENABLE_CONQUEROR_LEVEL:
				self.ExpandBtn.OnMouseOverIn = lambda arg = localeInfo.DETAILS_TITLE : ui.__mem_func__(self.__ShowToolTip)(arg)
				self.ExpandBtn.OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

				self.MinimizeBtn.OnMouseOverIn = lambda arg = localeInfo.DETAILS_TITLE : ui.__mem_func__(self.__ShowToolTip)(arg)
				self.MinimizeBtn.OnMouseOverOut = lambda : ui.__mem_func__(self.__HideToolTip)()

	if app.ENABLE_DETAILS_UI:
		def __InitCharacterDetailsUIButton(self):
			self.ExpandBtn.Show()
			self.MinimizeBtn.Hide()

		def __ClickExpandButton(self):
			if not self.chDetailsWnd:
				(x, y) = self.GetLocalPosition()
				self.chDetailsWnd = uiCharacterDetails.CharacterDetailsUI()
				self.chDetailsWnd.AdjustPosition(x, y)
				self.chDetailsWnd.Show()
			else:
				self.chDetailsWnd.Show()

			self.ExpandBtn.Hide()
			self.MinimizeBtn.Show()

			if app.ENABLE_SKILL_COLOR_SYSTEM:
				if self.skillColorWnd and self.skillColorWnd.IsShow():
					self.skillColorWnd.Hide()

		def __ClickMinimizeButton(self):
			self.chDetailsWnd.Hide()
			self.MinimizeBtn.Hide()
			self.ExpandBtn.Show()

		def OnMoveWindow(self, x, y):
			if self.chDetailsWnd:
				self.chDetailsWnd.AdjustPosition(x, y)

	def __SetSkillSlotEvent(self):
		for skillPageValue in self.skillPageDict.values():
			skillPageValue.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			skillPageValue.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectSkill))
			skillPageValue.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
			skillPageValue.SetUnselectItemSlotEvent(ui.__mem_func__(self.ClickSkillSlot))
			skillPageValue.SetUseSlotEvent(ui.__mem_func__(self.ClickSkillSlot))
			skillPageValue.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
			skillPageValue.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			skillPageValue.SetPressedSlotButtonEvent(ui.__mem_func__(self.OnPressedSlotButton))
			skillPageValue.AppendSlotButton("d:/ymir work/ui/game/windows/btn_plus_up.sub",\
				"d:/ymir work/ui/game/windows/btn_plus_over.sub",\
				"d:/ymir work/ui/game/windows/btn_plus_down.sub")

	def __SetEmotionSlot(self):
		self.emotionToolTip = uiToolTip.ToolTip()

		if app.ENABLE_EXPRESSING_EMOTION:
			for slot in (self.soloEmotionSlot, self.dualEmotionSlot, self.specialEmotionSlot):
				slot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
				slot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectEmotion))
				slot.SetUnselectItemSlotEvent(ui.__mem_func__(self.__ClickEmotionSlot))
				slot.SetUseSlotEvent(ui.__mem_func__(self.__ClickEmotionSlot))
				slot.SetOverInItemEvent(ui.__mem_func__(self.__OverInEmotion))
				slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutEmotion))
				slot.AppendSlotButton("d:/ymir work/ui/game/windows/btn_plus_up.sub",\
					"d:/ymir work/ui/game/windows/btn_plus_over.sub",\
					"d:/ymir work/ui/game/windows/btn_plus_down.sub")
		else:
			for slot in (self.soloEmotionSlot, self.dualEmotionSlot):
				slot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
				slot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectEmotion))
				slot.SetUnselectItemSlotEvent(ui.__mem_func__(self.__ClickEmotionSlot))
				slot.SetUseSlotEvent(ui.__mem_func__(self.__ClickEmotionSlot))
				slot.SetOverInItemEvent(ui.__mem_func__(self.__OverInEmotion))
				slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutEmotion))
				slot.AppendSlotButton("d:/ymir work/ui/game/windows/btn_plus_up.sub",\
					"d:/ymir work/ui/game/windows/btn_plus_over.sub",\
					"d:/ymir work/ui/game/windows/btn_plus_down.sub")

		for slotIdx, datadict in emotion.EMOTION_DICT.items():
			emotionIdx = slotIdx

			slot = self.soloEmotionSlot
			if app.ENABLE_EXPRESSING_EMOTION:
				if slotIdx > 50 and slotIdx < app.SPECIAL_ACTION_START_INDEX:
					slot = self.dualEmotionSlot

				if slotIdx >= app.SPECIAL_ACTION_START_INDEX:
					slot = self.specialEmotionSlot
			else:
				if slotIdx > 50:
					slot = self.dualEmotionSlot

			slot.SetEmotionSlot(slotIdx, emotionIdx)
			slot.SetCoverButton(slotIdx)

	def __SelectEmotion(self, slotIndex):
		if not slotIndex in emotion.EMOTION_DICT:
			return

		if app.IsPressed(app.DIK_LCONTROL):
			player.RequestAddToEmptyLocalQuickSlot(player.SLOT_TYPE_EMOTION, slotIndex)
			return

		mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_EMOTION, slotIndex, slotIndex)

	def __ClickEmotionSlot(self, slotIndex):
		print("click emotion")
		if not slotIndex in emotion.EMOTION_DICT:
			return

		print("check target acting")
		if player.IsActingTargetEmotion():
			return

		command = emotion.EMOTION_DICT[slotIndex]["command"]
		print("command", command)

		if app.ENABLE_EXPRESSING_EMOTION:
			if slotIndex > 50 and slotIndex < app.SPECIAL_ACTION_START_INDEX:
				vid = player.GetTargetVID()

				if 0 == vid or vid == player.GetMainCharacterIndex() or chr.IsNPC(vid) or chr.IsEnemy(vid):
					import chat
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.EMOTION_CHOOSE_ONE)
					return

				command += " " + chr.GetNameByVID(vid)
		else:
			if slotIndex > 50:
				vid = player.GetTargetVID()

				if 0 == vid or vid == player.GetMainCharacterIndex() or chr.IsNPC(vid) or chr.IsEnemy(vid):
					import chat
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.EMOTION_CHOOSE_ONE)
					return

				command += " " + chr.GetNameByVID(vid)

		print("send_command", command)
		net.SendChatPacket(command)

	def ActEmotion(self, emotionIndex):
		self.__ClickEmotionSlot(emotionIndex)

	def __OverInEmotion(self, slotIndex):
		if self.emotionToolTip:

			if not slotIndex in emotion.EMOTION_DICT:
				return

			name = emotion.EMOTION_DICT[slotIndex]["name"]
			body = None
			if app.ENABLE_EXPRESSING_EMOTION and slotIndex >= app.SPECIAL_ACTION_START_INDEX:
				leftSec = max(0, emotion.EMOTION_DICT[slotIndex]["time"] - app.GetGlobalTimeStamp())
				if leftSec > 0:
					body = localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftSec)
			if self.__R1Hint(name, body):
				self.emotionToolTip.HideToolTip()
				return
			self.emotionToolTip.ClearToolTip()
			self.emotionToolTip.SetTitle(name)
			if app.ENABLE_EXPRESSING_EMOTION:
				if slotIndex >= app.SPECIAL_ACTION_START_INDEX:
					self.emotionToolTip.AppendLastTime(emotion.EMOTION_DICT[slotIndex]["time"])
			self.emotionToolTip.AlignHorizonalCenter()
			self.emotionToolTip.ShowToolTip()

	def __OverOutEmotion(self):
		self.__R1HideHint()
		if self.emotionToolTip:
			self.emotionToolTip.HideToolTip()

	def __BindEvent(self):
		for i in range(len(self.skillGroupButton)):
			self.skillGroupButton[i].SetEvent(ui.__mem_func__(self.__SelectSkillGroup),i)

		self.RefreshQuest()
		self.__HideJobToolTip()

		for (tabKey, tabButton) in self.tabButtonDict.items():
			tabButton.SetEvent(ui.__mem_func__(self.__OnClickTabButton), tabKey)

		if app.ENABLE_CONQUEROR_LEVEL:
			for (tabKey, tabButton) in self.tabLevelInfoButtonDict.items():
				tabButton.SetEvent(ui.__mem_func__(self.__ChangeLevelInfoButton), tabKey)

			for (statusPlusKey, statusPlusButton) in self.statusConquerorPlusButtonDict.items():
				statusPlusButton.SAFE_SetEvent(self.__OnClickConquerorStatusPlusButton, statusPlusKey)
				statusPlusButton.ShowToolTip = lambda arg = statusPlusKey: self.__OverInStatButton(arg)
				statusPlusButton.HideToolTip = lambda arg = statusPlusKey: self.__OverOutStatButton()

		for (statusPlusKey, statusPlusButton) in self.statusPlusButtonDict.items():
			statusPlusButton.SAFE_SetEvent(self.__OnClickStatusPlusButton, statusPlusKey)
			statusPlusButton.SetShowToolTipEvent(ui.__mem_func__(self.__OverInStatButton), statusPlusKey)
			statusPlusButton.SetHideToolTipEvent(ui.__mem_func__(self.__OverOutStatButton), statusPlusKey)

		for (statusMinusKey, statusMinusButton) in self.statusMinusButtonDict.items():
			statusMinusButton.SAFE_SetEvent(self.__OnClickStatusMinusButton, statusMinusKey)
			statusMinusButton.SetShowToolTipEvent(ui.__mem_func__(self.__OverInStatMinusButton), statusMinusKey)
			statusMinusButton.SetHideToolTipEvent(ui.__mem_func__(self.__OverOutStatMinusButton), statusMinusKey)

		for titleBarValue in self.titleBarDict.values():
			if app.ENABLE_DETAILS_UI:
				titleBarValue.SetCloseEvent(ui.__mem_func__(self.Close))
			else:
				titleBarValue.SetCloseEvent(ui.__mem_func__(self.Hide))

		self.questSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectQuest))

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			if localeInfo.IsARABIC() or localeInfo.IsVIETNAM() or localeInfo.IsJAPAN():
				self.__LoadScript(uiScriptLocale.LOCALE_UISCRIPT_PATH + "CharacterWindow.py")
			else:
				self.__LoadScript("UIScript/CharacterWindow.py")

			self.__BindObject()
			self.__BindEvent()
			self.SetLuckKnotCapability(self.luckKnotAvailable)
			uicharacterbuff.ConfigureHeader(self)
			self.buffPage = uicharacterbuff.CharacterBuffPage(self.pageDict["SKILL"])
			self.buffPage.SetPosition(*self.activeSlot.GetLocalPosition())
			# After the slot windows (and the Buffi page): the grade counts above the cells' cover buttons.
			self.skillGradeCounts = dict((name, skillgradecount.GradeCounts(self.pageDict["SKILL"], page))
				for name, page in self.skillPageDict.items())
			self.skillPointArea.OnMouseOverIn = ui.__mem_func__(self.__ShowSkillPointToolTip)
			self.skillPointArea.OnMouseOverOut = ui.__mem_func__(self.__HideStatToolTip)
			self.activeSkillPointValue.AddFlag("not_pick")
			self.__SelectSkillGroup(0)
		except:
			import exception
			exception.Abort("CharacterWindow.__LoadWindow")

		#self.tabButtonDict["EMOTICON"].Disable()
		self.SetState("STATUS")
		if app.ENABLE_CONQUEROR_LEVEL:
			self.__ChangeLevelInfoButton(player.LEVEL_TYPE_BASE)
		self.__ApplyR1Look()

	def __ApplyR1Look(self):
		"""R1 look (root/uicharacterr1.py) unless Settings -> "Starý vzhled" chose the original one; a build
		failure undoes every change and keeps the original look (traced to syserr)."""
		self.r1Skin = None
		try:
			import uir1
			if not uir1.UseR1():
				return
			import uicharacterr1
			self.r1Skin = uicharacterr1.CharacterSkin(self)
		except Exception:
			self.r1Skin = None
			try:
				import uir1
				uir1.TraceFailure("the character window")
			except Exception:
				pass

	def SyncR1Look(self):
		"""Settings switched the look (uir1.LookChanged): the R1 look dressed into the live window or undone, then the
		page, its tabs and the skill group laid out again by the window's own code (an undo restores what was shown
		when the look was dressed). A failure keeps the original look (traced)."""
		import uir1
		if self.isLoaded == 0:
			return
		wanted = uir1.UseR1()
		skin = getattr(self, "r1Skin", None)
		if wanted and not skin:
			self.__ApplyR1Look()
		elif not wanted and skin:
			self.r1Skin = None
			try:
				skin.Undo()
			finally:
				skin.Destroy()
		else:
			return
		for refresh in (lambda: self.SetState(self.state),
						lambda: self.__SelectSkillGroup(getattr(self, "selectedSkillTab", 0))):
			try:
				refresh()
			except Exception:
				uir1.TraceFailure("the character window (look switch)")

	def Destroy(self):
		try:
			import uir1
			uir1.UnfollowLook(self)
		except Exception:
			pass
		if getattr(self, "r1Skin", None):
			self.r1Skin.Destroy()
		self.r1Skin = None
		self.__CloseLuckKnotUpgrade()
		self.__HideStatToolTip()
		if app.ENABLE_SKILL_COLOR_SYSTEM and self.skillColorWnd:
			self.skillColorWnd.Close()
		for counts in (getattr(self, "skillGradeCounts", None) or {}).values():
			counts.Destroy()
		self.skillGradeCounts = {}
		self.ClearDictionary()

		self.__Initialize()

	def Close(self):
		if 0 != self.toolTipSkill:
			self.toolTipSkill.Hide()

		if app.ENABLE_DETAILS_UI:
			if self.chDetailsWnd and self.chDetailsWnd.IsShow():
				self.chDetailsWnd.Hide()

		if app.ENABLE_SKILL_COLOR_SYSTEM:
			if self.skillColorWnd and self.skillColorWnd.IsShow():
				self.skillColorWnd.Hide()

		self.Hide()

	def SetSkillToolTip(self, toolTipSkill):
		self.toolTipSkill = toolTipSkill
		self.buffPage.SetToolTip(toolTipSkill)

	def SetBuffSkillLevels(self, levels):
		self.buffPage.SetLevels(levels)

	def SetBuffHealingUnlocked(self, unlocked):
		self.buffPage.SetHealingUnlocked(unlocked)

	def ResetBuffSkills(self):
		self.buffPage.Reset()

	def __R1Hint(self, title, body=None, widget=None):
		"""R1 look: a short hover text of this window (the tabs, level / EXP, free skill points, the emotions, the
		champion level switch) is the one R1 hint (uir1, like "Nastavení lišty") - at ``widget``, else above the
		mouse cursor; False in "Starý vzhled", where the window's tooltip board shows it."""
		if not getattr(self, "r1Skin", None) or not title:
			return False
		try:
			import uir1
			if widget is not None:
				x, y = widget.GetGlobalPosition()
				rect, follow = (x, y, widget.GetWidth(), widget.GetHeight()), False
			else:
				mx, my = wndMgr.GetMousePosition()
				rect, follow = (mx, my, 1, 1), True
			uir1.ShowHintAt(rect, title, body, owner=self, follow=follow)
		except Exception:
			return False
		if getattr(self, "toolTip", None):
			self.toolTip.Hide()
		return True

	def __R1HideHint(self):
		if getattr(self, "r1Skin", None):
			try:
				import uir1
				uir1.HideHint(self)
			except Exception:
				pass

	def __ShowSkillPointToolTip(self):
		if self.__R1Hint(localeInfo.STAT_TOOLTIP_POINT, widget=self.skillPointArea):
			return
		self.toolTip.ClearToolTip()
		self.toolTip.SetThinBoardSize(200)
		self.toolTip.AutoAppendTextLine(localeInfo.STAT_TOOLTIP_POINT)
		self.toolTip.AlignHorizonalCenter()
		self.toolTip.ShowToolTip()

	def SetQuestShortcuts(self, questShortcuts):
		self.questShortcutList = list(questShortcuts or ())
		self.questShowingStartIndex = 0
		if self.isLoaded:
			self.RefreshQuest()

	def SetPermanentTaskBonuses(self, bossPercent=0, metinPercent=0,
			bossLevel=None, metinLevel=None):
		self.__CreatePermanentTaskButtons()
		for category, level, bonus in (("bossologie", bossLevel, bossPercent),
				("kamenologie", metinLevel, metinPercent)):
			self.permanentTaskProgress[category] = (level, bonus)
			counter = self.permanentTaskLevels[category]
			if level is not None and level > 0:
				counter.SetNumber(str(level))
				# Native SetNumber creates glyphs without laying them out.
				counter.SetPosition(28, 22)
				counter.Show()
			else:
				counter.Hide()
		if self.permanentTaskTooltipCategory:
			self.__ShowPermanentTaskToolTip(self.permanentTaskTooltipCategory)
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncSafe()

	def __ShowPermanentTaskToolTip(self, category):
		self.permanentTaskTooltipCategory = category
		boss = category == "bossologie"
		label = (localeInfo.PERMANENT_TASKS_BOSS_LABEL if boss
			else localeInfo.PERMANENT_TASKS_STONE_LABEL)
		level, bonus = self.permanentTaskProgress.get(category, (None, 0))
		lines = []
		if level is None:
			lines.append((localeInfo.LUCK_KNOT_LOADING, None))
		else:
			lines.append((localeInfo.TOOLTIP_SKILL_LEVEL % level, None))
			reward = (localeInfo.PERMANENT_TASKS_BOSS_PASSIVE_BONUS if boss
				else localeInfo.PERMANENT_TASKS_STONE_PASSIVE_BONUS)
			lines.append((reward % bonuscolor.Number(bonus), bonuscolor.Value(bonus)))
		self.__ShowPassiveToolTip(label, category, lines, 240)

	def __ShowPassiveToolTip(self, title, descriptionKey, lines, legacyWidth):
		"""Lov bossů, Lov meteorů and Uzel štěstí among the standard skills: the skill tooltip of every other skill
		of the page (title, what it gives, then its level and bonuses). These three showed the
		window's small centred stat tooltip with no description. Without the skill tooltip (not handed over yet)
		the stat tooltip shows the same lines."""
		key, default = PERMANENT_PASSIVE_DESCRIPTIONS[descriptionKey]
		description = getattr(localeInfo, key, None) or default
		skillToolTip = getattr(self, "toolTipSkill", None)
		if skillToolTip:
			if self.toolTip:
				self.toolTip.Hide()
			skillToolTip.ClearToolTip()
			skillToolTip.SetTitle(title)
			skillToolTip.AppendDescription(description, 25)
			skillToolTip.AppendSpace(5)
			for text, color in lines:
				skillToolTip.AppendTextLine(text, skillToolTip.NORMAL_COLOR if color is None else color)
			skillToolTip.ShowToolTip()
			self.passiveToolTipShown = True
			return
		if not self.toolTip:
			return
		self.toolTip.ClearToolTip()
		self.toolTip.SetThinBoardSize(legacyWidth)
		self.toolTip.AutoAppendTextLine(title, 0xffffd36b - 0x100000000)
		for text, color in lines:
			if color is None:
				self.toolTip.AutoAppendTextLine(text)
			else:
				self.toolTip.AutoAppendTextLine(text, color)
		self.toolTip.AlignHorizonalCenter()
		self.toolTip.ShowToolTip()

	def __CreatePermanentTaskButtons(self):
		if self.permanentTaskButtons:
			return
		parent = self.pageDict["SKILL"]
		for category, x, y, iconName in PERMANENT_TASK_SKILL_ENTRIES:
			button = ui.Button()
			button.SetParent(parent)
			icon = PERMANENT_TASK_ASSET_ROOT + iconName
			button.SetUpVisual(icon)
			button.SetOverVisual(icon)
			button.SetDownVisual(icon)
			button.SetPosition(
				x + (32 - button.GetWidth()) // 2,
				y + (32 - button.GetHeight()) // 2,
			)
			button.Show()
			self.permanentTaskButtons[category] = button
			button.SetShowToolTipEvent(ui.__mem_func__(self.__ShowPermanentTaskToolTip), category)
			button.SetHideToolTipEvent(ui.__mem_func__(self.__HideStatToolTip))
			# Same native NumberLine and lower-right anchor as skill slot counts.
			counter = ui.NumberLine()
			counter.SetParent(button)
			counter.SetHorizontalAlignRight()
			counter.SetPosition(28, 22)
			counter.AddFlag("not_pick")
			counter.Hide()
			self.permanentTaskLevels[category] = counter


	def SetLuckKnotCapability(self, available):
		if bool(available) != self.luckKnotAvailable:
			self.__CloseLuckKnotUpgrade()
			self.__HideStatToolTip()
			self.luckKnotSnapshot = None
		self.luckKnotAvailable = bool(available)
		if not self.isLoaded:
			return
		self.__CreateLuckKnotButton()
		if self.luckKnotAvailable:
			self.luckKnotButton.Show()
		else:
			self.luckKnotButton.Hide()
		self.SetLuckKnotSnapshot(self.luckKnotSnapshot)
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncSafe()

	def __CreateLuckKnotButton(self):
		if self.luckKnotButton:
			return
		parent = self.pageDict["SKILL"]
		self.luckKnotButton = ui.Button()
		self.luckKnotButton.SetParent(parent)
		icon = PERMANENT_TASK_ASSET_ROOT + "passive_uzel_stesti_32.png"
		self.luckKnotButton.SetUpVisual(icon)
		self.luckKnotButton.SetOverVisual(icon)
		self.luckKnotButton.SetDownVisual(icon)
		self.luckKnotButton.SetPosition(166, 221)
		self.luckKnotButton.SetShowToolTipEvent(ui.__mem_func__(self.__ShowLuckKnotToolTip))
		self.luckKnotButton.SetHideToolTipEvent(ui.__mem_func__(self.__HideStatToolTip))
		self.luckKnotLevel = ui.NumberLine()
		self.luckKnotLevel.SetParent(self.luckKnotButton)
		self.luckKnotLevel.SetHorizontalAlignRight()
		self.luckKnotLevel.SetPosition(28, 22)
		self.luckKnotLevel.AddFlag("not_pick")
		self.luckKnotLevel.Hide()
		self.luckKnotPlus = ui.Button()
		self.luckKnotPlus.SetParent(parent)
		for setter, state in ((self.luckKnotPlus.SetUpVisual, "up"),
				(self.luckKnotPlus.SetOverVisual, "over"), (self.luckKnotPlus.SetDownVisual, "down")):
			setter("d:/ymir work/ui/game/windows/btn_plus_%s.sub" % state)
		self.luckKnotPlus.SetPosition(186, 221)
		self.luckKnotPlus.SetEvent(ui.__mem_func__(self.__UpgradeLuckKnot))
		self.luckKnotPlus.SetShowToolTipEvent(ui.__mem_func__(self.__ShowLuckKnotToolTip))
		self.luckKnotPlus.SetHideToolTipEvent(ui.__mem_func__(self.__HideStatToolTip))
		self.luckKnotPlus.Hide()

	def SetLuckKnotSnapshot(self, snapshot):
		changed = snapshot != self.luckKnotSnapshot
		if changed:
			# The server's answer to a confirmed upgrade keeps the dialog open (new stage and
			# price, or "Max"); any other change of the quote closes it as before (a stale quote never charges).
			if not self.__KeepLuckKnotUpgrade(snapshot):
				self.__CloseLuckKnotUpgrade()
			self.__HideStatToolTip()
		self.luckKnotSnapshot = snapshot
		if changed:
			self.__RefreshLuckKnotUpgrade(snapshot)
		if not self.isLoaded:
			return
		self.__CreateLuckKnotButton()
		self.luckKnotPlus.Hide()
		self.luckKnotLevel.Hide()
		if self.luckKnotAvailable and snapshot and snapshot["code"] == 0:
			if snapshot["level"] > 0:
				self.luckKnotLevel.SetNumber(str(snapshot["level"]))
				# Native SetNumber creates glyphs without laying them out.
				self.luckKnotLevel.SetPosition(28, 22)
				self.luckKnotLevel.Show()
			if snapshot["costs"]:
				self.luckKnotPlus.Show()

	def __UpgradeLuckKnot(self):
		state = self.luckKnotSnapshot
		if not self.luckKnotAvailable or not state or state["code"] != 0 or not state["costs"]:
			return
		self.__CloseLuckKnotUpgrade()
		self.__HideStatToolTip()
		self.luckKnotUpgradeQuote = state
		self.luckKnotUpgradeDialog = uiluckknot.UpgradeDialog(state)
		self.luckKnotUpgradeDialog.SetAcceptEvent(ui.__mem_func__(self.__ConfirmLuckKnotUpgrade))
		self.luckKnotUpgradeDialog.SetCancelEvent(ui.__mem_func__(self.__CloseLuckKnotUpgrade))
		self.luckKnotUpgradeDialog.Open()

	def __ConfirmLuckKnotUpgrade(self):
		quote = self.luckKnotUpgradeQuote
		if self.luckKnotUpgradePending:
			return
		if not self.luckKnotAvailable or not quote or quote != self.luckKnotSnapshot or not quote["costs"]:
			self.__CloseLuckKnotUpgrade()
			return
		if net.UpgradeLuckKnot():
			self.luckKnotPlus.Hide()
			# The dialog stays open; the next snapshot refreshes it so the player can upgrade again
			self.luckKnotUpgradePending = True
			if self.luckKnotUpgradeDialog:
				self.luckKnotUpgradeDialog.SetPending(True)
		else:
			self.__CloseLuckKnotUpgrade()

	def __KeepLuckKnotUpgrade(self, snapshot):
		"""The open dialog survives the server's answer to its own confirmed upgrade: a new quote (code 0), or a
		refusal / busy answer after which the client asks for the quote again (codes 1-5)."""
		return bool(self.luckKnotUpgradeDialog and self.luckKnotUpgradePending and self.luckKnotAvailable
			and isinstance(snapshot, dict) and snapshot.get("code") in (0, 1, 2, 3, 4, 5))

	def __RefreshLuckKnotUpgrade(self, snapshot):
		"""The same dialog again on the same spot with the server's new quote (stage, price, or "Max")."""
		old = self.luckKnotUpgradeDialog
		if not old or not self.luckKnotUpgradePending or not snapshot or snapshot.get("code") != 0:
			return
		try:
			x, y = old.GetGlobalPosition()
			centre = x + old.GetWidth() // 2
		except Exception:
			x = y = centre = None
		old.Close()
		self.luckKnotUpgradePending = False
		self.luckKnotUpgradeQuote = snapshot
		self.luckKnotUpgradeDialog = uiluckknot.UpgradeDialog(snapshot)
		self.luckKnotUpgradeDialog.SetAcceptEvent(ui.__mem_func__(self.__ConfirmLuckKnotUpgrade))
		self.luckKnotUpgradeDialog.SetCancelEvent(ui.__mem_func__(self.__CloseLuckKnotUpgrade))
		self.luckKnotUpgradeDialog.Open()
		if centre is not None:
			try:
				self.luckKnotUpgradeDialog.SetPosition(centre - self.luckKnotUpgradeDialog.GetWidth() // 2, y)
			except Exception:
				pass

	def __CloseLuckKnotUpgrade(self):
		# Hide() already runs inside ui.ScriptWindow.__init__, before __Initialize.
		dialog = getattr(self, "luckKnotUpgradeDialog", None)
		if dialog:
			dialog.Close()
		self.luckKnotUpgradeDialog = None
		self.luckKnotUpgradeQuote = None
		self.luckKnotUpgradePending = False

	def __ShowLuckKnotToolTip(self):
		state = self.luckKnotSnapshot
		lines = []
		if not state or state["code"] != 0:
			lines.append((localeInfo.LUCK_KNOT_LOADING, None))
		else:
			lines.append((localeInfo.LUCK_KNOT_LEVEL % state["level"], None))
			labels = (localeInfo.LUCK_KNOT_METEOR, localeInfo.LUCK_KNOT_DOUBLE_METEOR,
				localeInfo.LUCK_KNOT_DOUBLE_BOSS, localeInfo.LUCK_KNOT_RARITY)
			for label, value in zip(labels, state["effects_bp"]):
				lines.append((label % bonuscolor.Number(value / 100.0), bonuscolor.Value(value)))
		self.__ShowPassiveToolTip(localeInfo.LUCK_KNOT_NAME, "luck_knot", lines, 260)

	def __OnClickStatusPlusButton(self, statusKey):
		try:
			status_inc = osfInfo.INCREASE_POINTS_CTRL\
			if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL) else 1

			statusPlusCommand=self.statusPlusCommandDict[statusKey]
			net.SendChatPacket("%s %d" % (statusPlusCommand, status_inc))
		except KeyError as msg:
			dbg.TraceError("CharacterWindow.__OnClickStatusPlusButton KeyError: %s", msg)

	def __OnClickStatusMinusButton(self, statusKey):
		try:
			statusMinusCommand = self.statusMinusCommandDict[statusKey]
			net.SendChatPacket(statusMinusCommand)
		except KeyError as msg:
			dbg.TraceError("CharacterWindow.__OnClickStatusMinusButton KeyError: %s", msg)

	if app.ENABLE_CONQUEROR_LEVEL:
		def __OnClickConquerorStatusPlusButton(self, statusKey):
			try:
				status_inc = osfInfo.INCREASE_POINTS_CTRL\
				if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL) else 1
				statusConquerorPlusCommand = self.statusConquerorPlusCommandDict[statusKey]
				net.SendChatPacket("%s %d" % (statusConquerorPlusCommand, status_inc))
			except KeyError as msg:
				dbg.TraceError("CharacterWindow.__OnClickConquerorStatusPlusButton KeyError: %s", msg)

	def __OnClickTabButton(self, stateKey):
		self.SetState(stateKey)

	if app.ENABLE_CONQUEROR_LEVEL:
		def __ChangeLevelInfoButton(self, key):
			self.levelType = key

			for (tabKey, tabButton) in self.tabLevelInfoButtonDict.items():
				if key != tabKey:
					tabButton.SetUp()

			self.tabLevelInfoButtonDict[key].Down()

			for tabPage in self.tabLevelInfoPageDict.values():
				tabPage.Hide()

			self.tabLevelInfoPageDict[key].Show()

			self.RefreshStatus()

	def SetState(self, stateKey):
		self.OverOutItem()
		self.state = stateKey

		for (tabKey, tabButton) in self.tabButtonDict.items():
			if stateKey != tabKey:
				tabButton.SetUp()
		self.tabButtonDict[stateKey].Down()

		for tabValue in self.tabDict.values():
			tabValue.Hide()

		for pageValue in self.pageDict.values():
			pageValue.Hide()

		for titleBarValue in self.titleBarDict.values():
			titleBarValue.Hide()

		self.titleBarDict[stateKey].Show()
		self.tabDict[stateKey].Show()
		self.pageDict[stateKey].Show()

		if stateKey == "QUEST":
			self.RefreshQuest()
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncSafe()

	def GetState(self):
		return self.state

	def __GetTotalAtkText(self):
		minAtk=player.GetStatus(player.ATT_MIN)
		maxAtk=player.GetStatus(player.ATT_MAX)
		atkBonus=player.GetStatus(player.ATT_BONUS)
		attackerBonus=player.GetStatus(player.ATTACKER_BONUS)

		# [MT-360] 호각귀걸이 이슈
		# 클라와 서버간 표기 차이로 변신 중일때는 ATT_BONUS 값을 제외한다.
		#if player.IsPoly():
		#	atkBonus = 0

		if minAtk==maxAtk:
			return "%d" % (minAtk+atkBonus+attackerBonus)
		else:
			return "%d-%d" % (minAtk+atkBonus+attackerBonus, maxAtk+atkBonus+attackerBonus)

	def __GetTotalMagAtkText(self):
		minMagAtk=player.GetStatus(player.MAG_ATT)+player.GetStatus(player.MIN_MAGIC_WEP)
		maxMagAtk=player.GetStatus(player.MAG_ATT)+player.GetStatus(player.MAX_MAGIC_WEP)

		if minMagAtk==maxMagAtk:
			return "%d" % (minMagAtk)
		else:
			return "%d-%d" % (minMagAtk, maxMagAtk)

	def __GetTotalDefText(self):
		defValue=player.GetStatus(player.DEF_GRADE)
		if constInfo.ADD_DEF_BONUS_ENABLE:
			defValue+=player.GetStatus(player.DEF_BONUS)
		return "%d" % (defValue)

	if app.ENABLE_CONQUEROR_LEVEL:
		def __GetSungMaPointValuePer(self, point_type, percent_point_type):
			pass

	def RefreshStatus(self):
		if self.isLoaded == 0:
			return

		try:
			if app.ENABLE_CONQUEROR_LEVEL:
				if self.levelType == player.LEVEL_TYPE_CONQUEROR:
					self.GetChild("Level_Value").SetText(str(player.GetStatus(player.POINT_CONQUEROR_LEVEL)))
					self.GetChild("Exp_Value").SetText(str(unsigned32(player.GetStatus(player.POINT_CONQUEROR_EXP))))
					self.GetChild("RestExp_Value").SetText(str(unsigned32(player.GetStatus(player.POINT_CONQUEROR_NEXT_EXP)) - unsigned32(player.GetStatus(player.POINT_CONQUEROR_EXP))))
				else:
					self.GetChild("Level_Value").SetText(str(player.GetStatus(player.LEVEL)))
					self.GetChild("Exp_Value").SetText(str(unsigned32(player.GetEXP())))
					self.GetChild("RestExp_Value").SetText(str(unsigned32(player.GetStatus(player.NEXT_EXP)) - unsigned32(player.GetStatus(player.EXP))))
			else:
				self.GetChild("Level_Value").SetText(str(player.GetStatus(player.LEVEL)))
				self.GetChild("Exp_Value").SetText(str(unsigned32(player.GetEXP())))
				self.GetChild("RestExp_Value").SetText(str(unsigned32(player.GetStatus(player.NEXT_EXP)) - unsigned32(player.GetStatus(player.EXP))))
			self.GetChild("HP_Value").SetText(str(player.GetStatus(player.HP)) + "/" + str(player.GetStatus(player.MAX_HP)))
			self.GetChild("SP_Value").SetText(str(player.GetStatus(player.SP)) + "/" + str(player.GetStatus(player.MAX_SP)))

			self.GetChild("STR_Value").SetText(str(player.GetStatus(player.ST)))
			self.GetChild("DEX_Value").SetText(str(player.GetStatus(player.DX)))
			self.GetChild("HTH_Value").SetText(str(player.GetStatus(player.HT)))
			self.GetChild("INT_Value").SetText(str(player.GetStatus(player.IQ)))

			self.GetChild("ATT_Value").SetText(self.__GetTotalAtkText())
			self.GetChild("DEF_Value").SetText(self.__GetTotalDefText())

			self.GetChild("MATT_Value").SetText(self.__GetTotalMagAtkText())
			# self.GetChild("MATT_Value").SetText(str(player.GetStatus(player.MAG_ATT)))

			self.GetChild("MDEF_Value").SetText(str(player.GetStatus(player.MAG_DEF)))
			self.GetChild("ASPD_Value").SetText(str(player.GetStatus(player.ATT_SPEED)))
			self.GetChild("MSPD_Value").SetText(str(player.GetStatus(player.MOVING_SPEED)))
			self.GetChild("CSPD_Value").SetText(str(player.GetStatus(player.CASTING_SPEED)))
			self.GetChild("ER_Value").SetText(str(player.GetStatus(player.EVADE_RATE)))

			if app.ENABLE_CONQUEROR_LEVEL:
				self.GetChild("sungma_str_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_STR)))
				self.GetChild("sungma_hp_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_HP)))
				self.GetChild("sungma_move_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_MOVE)))
				self.GetChild("sungma_immune_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_IMMUNE)))
				self.GetChild("sungma_str_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_STR)))
				self.GetChild("sungma_hp_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_HP)))
				self.GetChild("sungma_move_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_MOVE)))
				self.GetChild("sungma_immune_value").SetText(str(player.GetStatus(player.POINT_SUNGMA_IMMUNE)))
		except:
			# import exception
			# exception.Abort("CharacterWindow.RefreshStatus.BindObject")
			## 게임이 튕겨 버림
			pass

		self.__RefreshStatusPlusButtonList()
		self.__RefreshStatusMinusButtonList()
		self.RefreshAlignment()

		if self.refreshToolTip:
			self.refreshToolTip()

		if app.ENABLE_DETAILS_UI:
			if self.chDetailsWnd and self.chDetailsWnd.IsShow():
				self.chDetailsWnd.Refresh()
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncSafe()

	def __RefreshStatusPlusButtonList(self):
		if self.isLoaded == 0:
			return

		if app.ENABLE_CONQUEROR_LEVEL:
			if self.levelType == player.LEVEL_TYPE_CONQUEROR:
				statusPlusPoint = player.GetStatus(player.POINT_CONQUEROR_POINT)
			else:
				statusPlusPoint = player.GetStatus(player.STAT)
		else:
			statusPlusPoint = player.GetStatus(player.STAT)

		if statusPlusPoint > 0:
			self.statusPlusValue.SetText(str(statusPlusPoint))
			if not app.ENABLE_CONQUEROR_LEVEL:
				self.statusPlusLabel.Show()
			self.ShowStatusPlusButtonList()
			if app.ENABLE_CONQUEROR_LEVEL:
				self.ShowConquerorStatusPlusButtonList()
		else:
			self.statusPlusValue.SetText(str(0))
			if not app.ENABLE_CONQUEROR_LEVEL:
				self.statusPlusLabel.Hide()
			self.HideStatusPlusButtonList()
			if app.ENABLE_CONQUEROR_LEVEL:
				self.HideConquerorStatusPlusButtonList()

		if app.ENABLE_CONQUEROR_LEVEL:
			self.statusPlusLabel.Show()

	def __RefreshStatusMinusButtonList(self):
		if self.isLoaded == 0:
			return

		statusMinusPoint = self.__GetStatMinusPoint()

		if statusMinusPoint>0:
			self.__ShowStatusMinusButtonList()
		else:
			self.__HideStatusMinusButtonList()

	def RefreshAlignment(self):
		point, grade = player.GetAlignmentData()

		import colorInfo
		COLOR_DICT = {
			0 : colorInfo.TITLE_RGB_GOOD_4,
			1 : colorInfo.TITLE_RGB_GOOD_3,
			2 : colorInfo.TITLE_RGB_GOOD_2,
			3 : colorInfo.TITLE_RGB_GOOD_1,
			4 : colorInfo.TITLE_RGB_NORMAL,
			5 : colorInfo.TITLE_RGB_EVIL_1,
			6 : colorInfo.TITLE_RGB_EVIL_2,
			7 : colorInfo.TITLE_RGB_EVIL_3,
			8 : colorInfo.TITLE_RGB_EVIL_4,
		}
		colorList = COLOR_DICT.get(grade, colorInfo.TITLE_RGB_NORMAL)
		gradeColor = ui.GenerateColor(colorList[0], colorList[1], colorList[2])

		self.toolTipAlignment.ClearToolTip()
		if app.ENABLE_GENDER_ALIGNMENT:
			self.toolTipAlignment.AutoAppendTextLine(localeInfo.GetAlignmentTitleName(point), gradeColor)
		else:
			self.toolTipAlignment.AutoAppendTextLine(localeInfo.TITLE_NAME_LIST[grade], gradeColor)
		self.toolTipAlignment.AutoAppendTextLine(localeInfo.ALIGNMENT_NAME + str(point))
		self.toolTipAlignment.AlignHorizonalCenter()

	def __ShowStatusMinusButtonList(self):
		for (stateMinusKey, statusMinusButton) in self.statusMinusButtonDict.items():
			statusMinusButton.Show()

	def __HideStatusMinusButtonList(self):
		for (stateMinusKey, statusMinusButton) in self.statusMinusButtonDict.items():
			statusMinusButton.Hide()

	def ShowStatusPlusButtonList(self):
		for (statePlusKey, statusPlusButton) in self.statusPlusButtonDict.items():
			statusPlusButton.Show()

	def HideStatusPlusButtonList(self):
		for (statePlusKey, statusPlusButton) in self.statusPlusButtonDict.items():
			statusPlusButton.Hide()

	if app.ENABLE_CONQUEROR_LEVEL:
		def ShowConquerorStatusPlusButtonList(self):
			for (statePlusKey, statusPlusButton) in self.statusConquerorPlusButtonDict.items():
				statusPlusButton.Show()

		def HideConquerorStatusPlusButtonList(self):
			for (statePlusKey, statusPlusButton) in self.statusConquerorPlusButtonDict.items():
				statusPlusButton.Hide()

	def SelectSkill(self, skillSlotIndex):
		mouseController = mouseModule.mouseController

		if False == mouseController.isAttached():
			srcSlotIndex = self.__RealSkillSlotToSourceSlot(skillSlotIndex)
			selectedSkillIndex = player.GetSkillIndex(srcSlotIndex)

			if skill.CanUseSkill(selectedSkillIndex):
				if app.IsPressed(app.DIK_LCONTROL):
					player.RequestAddToEmptyLocalQuickSlot(player.SLOT_TYPE_SKILL, srcSlotIndex)
					return

				mouseController.AttachObject(self, player.SLOT_TYPE_SKILL, srcSlotIndex, selectedSkillIndex)
		else:
			mouseController.DeattachObject()

	def SelectEmptySlot(self, SlotIndex):
		mouseModule.mouseController.DeattachObject()

	if app.ENABLE_CONQUEROR_LEVEL:
		def __ShowToolTip(self, desc):
			if not self.toolTip:
				return

			if self.__R1Hint(desc):
				return
			descLen = len(desc)
			self.toolTip.ClearToolTip()
			width = max(100, min(11 * descLen, 200))
			self.toolTip.SetThinBoardSize(width)
			self.toolTip.AutoAppendTextLine(desc)
			self.toolTip.AlignHorizonalCenter()
			self.toolTip.Show()

		def __HideToolTip(self):
			self.__HideStatToolTip()

		def __ShowToolTipButton(self, desc):
			self.__ShowToolTip(desc)

		def __ShowToolTipImg(self, event_type, text):
			if "mouse_over_in" == event_type :
				if self.__R1Hint(text):
					return
				textLen = len(text)

				self.toolTip.ClearToolTip()
				self.toolTip.SetThinBoardSize(11 * arglen)
				#self.toolTip.SetToolTipPosition(pos_x + 50, pos_y + 50)
				self.toolTip.AppendTextLine(text, 0xffffffff)
				self.toolTip.Show()
			elif "mouse_over_out" == event_type:
				self.__HideToolTip()

		def __TogglePassiveAttrWindow(self, event_type): pass
		def __ToolTipProgress(self): pass

	## ToolTip
	def OverInItem(self, slotNumber):
		if mouseModule.mouseController.isAttached():
			return

		if 0 == self.toolTipSkill:
			return

		srcSlotIndex = self.__RealSkillSlotToSourceSlot(slotNumber)
		skillIndex = player.GetSkillIndex(srcSlotIndex)
		skillLevel = player.GetSkillLevel(srcSlotIndex)
		skillGrade = player.GetSkillGrade(srcSlotIndex)
		skillType = skill.GetSkillType(skillIndex)

		## ACTIVE
		if skill.SKILL_TYPE_ACTIVE == skillType:
			overInSkillGrade = self.__GetSkillGradeFromSlot(slotNumber)

			if slotNumber == self.__GetRealSkillSlot(skillGrade, srcSlotIndex):
				self.toolTipSkill.SetSkillNew(srcSlotIndex, skillIndex, skillGrade, skillLevel)
			else:
				self.toolTipSkill.SetSkillOnlyName(srcSlotIndex, skillIndex, overInSkillGrade)
		else:
			self.toolTipSkill.SetSkillNew(srcSlotIndex, skillIndex, skillGrade, skillLevel)
		# rebuilt from the new level / grade on RefreshSkill while the mouse stays on the slot
		self.toolTipSkill.RememberRefresh(self.OverInItem, slotNumber)

	def OverOutItem(self):
		# Window construction invokes Hide before __Initialize creates children.
		if getattr(self, "buffPage", None):
			self.buffPage.HideToolTip()
		if getattr(self, "toolTipSkill", None):
			self.toolTipSkill.HideToolTip()
		if getattr(self, "toolTip", None):
			self.toolTip.Hide()

	## Quest
	def __CreateQuestShortcutIcons(self):
		self.questShortcutIconList = []
		for i in range(quest.QUEST_MAX_NUM):
			image = ui.ImageBox()
			image.SetParent(self.questSlot)
			image.SetPosition(0, i * 60)
			image.AddFlag("not_pick")
			image.Hide()
			self.questShortcutIconList.append(image)

	def __SelectQuest(self, slotIndex):
		action = self.questActionMap.get(slotIndex)
		if not action:
			return

		actionType, actionValue = action
		if actionType == "shortcut":
			actionValue()
			return

		questIndex = actionValue
		if app.ENABLE_QUEST_RENEWAL and questIndex not in self.questClicked:
			self.questClicked.append(questIndex)

		import event
		event.QuestButtonClick(-2147483648 + questIndex)

	if app.ENABLE_EXPRESSING_EMOTION:
		def ClearSpecialEmotions(self):
			emotion.ClearSpecialEmotionIcons()
			self.__SetEmotionSlot()

		def RegisterSpecialEmotions(self, emotionIdx, leftTime):
			emotion.RegisterSpecialEmotionIcons(emotionIdx, leftTime)
			self.__SetEmotionSlot()

	def RefreshQuest(self):
		if self.isLoaded == 0:
			return

		self.OnQuestScroll()

		questShortcuts = getattr(self, "questShortcutList", ())
		nativeQuestData = _GetRenderableQuestData()
		questCount = len(questShortcuts) + len(nativeQuestData)
		self.questTotalCount = questCount
		visibleQuestCount = min(questCount, quest.QUEST_MAX_NUM)
		questRange = range(quest.QUEST_MAX_NUM)
		self.questIndexMap = {}
		self.questActionMap = {}
		self.questDataIndexMap = {}

		if questCount > quest.QUEST_MAX_NUM:
			self.questScrollBar.Show()
		else:
			self.questScrollBar.Hide()

		for i in questRange[:visibleQuestCount]:
			rowIndex = self.questShowingStartIndex + i
			isShortcut = rowIndex < len(questShortcuts)
			self.questRowButtonList[i].Show()
			shortcutIcon = self.questShortcutIconList[i]
			shortcutIcon.Hide()

			if isShortcut:
				(_, questName, questIcon, questAction) = questShortcuts[rowIndex]
				questCounterName = ""
				questCounterValue = 0
				self.questActionMap[i] = ("shortcut", questAction)
				self.questDataIndexMap[i] = None
			else:
				(questDataIndex, questData) = nativeQuestData[rowIndex - len(questShortcuts)]
				if app.ENABLE_QUEST_RENEWAL:
					(questIndex, questName, questCategory, questIcon, questCounterName, questCounterValue) = questData
				else:
					(questName, questIcon, questCounterName, questCounterValue) = questData
					questIndex = quest.GetQuestIndex(questDataIndex)

				self.questIndexMap[i] = questIndex
				self.questActionMap[i] = ("quest", questIndex)
				self.questDataIndexMap[i] = questDataIndex

			if questName and questName[0] in "*&~":
				questName = questName[1:]

			rowY = i * 60
			self.questNameList[i].SetText(questName)
			self.questNameList[i].Show()
			if isShortcut:
				self.questNameList[i].SetPosition(72, rowY + 22)
				self.questLastTimeList[i].Hide()
				self.questLastCountList[i].Hide()
			else:
				self.questNameList[i].SetPosition(72, rowY + 10)
				self.questLastTimeList[i].SetPosition(72, rowY + 24)
				self.questLastCountList[i].SetPosition(72, rowY + 38)
				self.questLastTimeList[i].Show()
				self.questLastCountList[i].Show()

			if len(questCounterName) > 0:
				self.questLastCountList[i].SetText("%s : %d" % (questCounterName, questCounterValue))
			else:
				self.questLastCountList[i].SetText("")
			self.questLastTimeList[i].SetText("")

			self.questSlot.ClearSlot(i)
			if isShortcut:
				self.questSlot.SetSlot(i, i, 1, 1, 0)
				if app.IsExistFile(questIcon):
					shortcutIcon.LoadImage(questIcon)
					shortcutIcon.Show()
				else:
					dbg.TraceError(
						"CharacterWindow.RefreshQuest: missing shortcut icon %s",
						questIcon,
					)
			else:
				self.questSlot.SetSlot(i, i, 1, 1, questIcon)

		for i in questRange[visibleQuestCount:]:
			self.questRowButtonList[i].Hide()
			self.questNameList[i].Hide()
			self.questLastTimeList[i].Hide()
			self.questLastCountList[i].Hide()
			self.questShortcutIconList[i].Hide()
			self.questSlot.ClearSlot(i)
			self.questSlot.HideSlotBaseImage(i)

		self.__UpdateQuestClock()
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncQuestSafe()

	def OnRunMouseWheel(self, nLen):
		# The top window gets every notch over it first: only the quest page scrolls the quest list (it used to be
		# scrolled, hidden, from every page and nothing else under the mouse got the wheel).
		if "QUEST" != self.state or not self.questScrollBar.IsShow():
			return False
		if nLen > 0:
			self.questScrollBar.OnUp()
		else:
			self.questScrollBar.OnDown()
		return True

	def __UpdateQuestClock(self):
		if "QUEST" == self.state:
			for i in range(quest.QUEST_MAX_NUM):
				questDataIndex = self.questDataIndexMap.get(i)
				if questDataIndex is None:
					continue

				(lastName, lastTime) = quest.GetQuestLastTime(questDataIndex)

				clockText = localeInfo.QUEST_UNLIMITED_TIME
				if len(lastName) > 0:
					if lastTime <= 0:
						clockText = localeInfo.QUEST_TIMEOVER
					else:
						questLastMinute = lastTime // 60
						questLastSecond = lastTime % 60
						clockText = lastName + " : "

						if questLastMinute > 0:
							clockText += str(questLastMinute) + localeInfo.QUEST_MIN
							if questLastSecond > 0:
								clockText += " "

						if questLastSecond > 0:
							clockText += str(questLastSecond) + localeInfo.QUEST_SEC

				self.questLastTimeList[i].SetText(clockText)

	def __GetStatMinusPoint(self):
		POINT_STAT_RESET_COUNT = 112
		return player.GetStatus(POINT_STAT_RESET_COUNT)

	def __OverInStatMinusButton(self, stat):
		try:
			self.__ShowStatToolTip(self.STAT_MINUS_DESCRIPTION[stat] % self.__GetStatMinusPoint())
		except KeyError:
			pass

		self.refreshToolTip = lambda arg = stat : ui.__mem_func__(self.__OverInStatMinusButton)(arg)

	def __OverOutStatMinusButton(self):
		self.__HideStatToolTip()
		self.refreshToolTip = 0

	def __OverInStatButton(self, stat):
		try:
			self.__ShowStatToolTip(self.STAT_DESCRIPTION[stat])
		except KeyError:
			pass

	def __OverOutStatButton(self):
		self.__HideStatToolTip()

	def __ShowStatToolTip(self, statDesc):
		if not self.toolTip:
			return

		if app.ENABLE_CONQUEROR_LEVEL:
			statDescLen = len(statDesc)
			width = max(100, min(11 * statDescLen, 450))
			self.toolTip.SetThinBoardSize(width)
			self.toolTip.AlignHorizonalCenter()

		self.toolTip.ClearToolTip()
		self.toolTip.AppendTextLine(statDesc)
		self.toolTip.AppendSpace(5)
		self.toolTip.AppendTextLine("|Ikey/ctrl|i + |Ikey/mouse_left|i - " +\
								localeInfo.MULTIPLY_STATE_POINT_ADD_TEXT.format(osfInfo.INCREASE_POINTS_CTRL),\
								osfInfo.TOOLTIP_KEYS_COLOR_HEX)
		self.toolTip.Show()

	def __HideStatToolTip(self):
		self.__R1HideHint()
		self.permanentTaskTooltipCategory = None
		# Also reached from Hide() inside ui.ScriptWindow.__init__.
		toolTip = getattr(self, "toolTip", None)
		if toolTip:
			toolTip.Hide()
		if getattr(self, "passiveToolTipShown", False):
			self.passiveToolTipShown = False
			skillToolTip = getattr(self, "toolTipSkill", None)
			if skillToolTip:
				skillToolTip.HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		self.__UpdateQuestClock()

		if app.ENABLE_SKILL_COLOR_SYSTEM:
			if self.skillColorWnd:
				self.__UpdateSkillColorPosition()

	## Skill Process
	def __RefreshSkillPage(self, name, slotCount):
		global SHOW_LIMIT_SUPPORT_SKILL_LIST

		skillPage = self.skillPageDict[name]
		# The engine count of a cell lies under its cover button; the same digits again above it (skillgradecount).
		counts = (getattr(self, "skillGradeCounts", None) or {}).get(name)

		startSlotIndex = skillPage.GetStartIndex()

		getSkillType = skill.GetSkillType
		getSkillIndex = player.GetSkillIndex
		getSkillGrade = player.GetSkillGrade
		getSkillLevel = player.GetSkillLevel
		getSkillLevelUpPoint = skill.GetSkillLevelUpPoint
		getSkillMaxLevel = skill.GetSkillMaxLevel
		skillActivated = False

		for i in range(slotCount + 1):
			slotIndex = i + startSlotIndex
			skillIndex = getSkillIndex(slotIndex)
			activeList = {}
			cooltmList = {}

			realSlots = set(self.__GetRealSkillSlot(j, i)
				for j in range(skill.SKILL_GRADE_COUNT + 1))
			for realSlotIndex in realSlots:
				activeList[realSlotIndex] = skillPage.IsActivatedSlot(realSlotIndex)
				cooltmList[realSlotIndex] = skillPage.GetSlotCoolTime(realSlotIndex)
				skillPage.ClearSlot(realSlotIndex)
				if counts:
					counts.Clear(realSlotIndex)

			if 0 == skillIndex:
				continue

			skillGrade = getSkillGrade(slotIndex)
			skillLevel = getSkillLevel(slotIndex)
			skillType = getSkillType(skillIndex)

			if "SUPPORT" == name and skillIndex not in SHOW_LIMIT_SUPPORT_SKILL_LIST:
				continue

			## 승마 스킬 예외 처리
			if player.SKILL_INDEX_RIDING == skillIndex:
				if skillGrade == 1:
					skillLevel += 19
				elif skillGrade == 2:
					skillLevel += 29
				elif skillGrade == 3:
					skillLevel = 40

				skillPage.SetSkillSlotNew(slotIndex, skillIndex, max(skillLevel - 1, 0), skillLevel)
				skillPage.SetSlotCount(slotIndex, skillLevel)
				if counts:
					counts.SetCount(slotIndex, skillLevel)

			## ACTIVE
			elif skill.SKILL_TYPE_ACTIVE == skillType:
				for j in skillpresentation.ColumnGrades(skillGrade):
					realSlotIndex = self.__GetRealSkillSlot(j, slotIndex)
					skillPage.SetSkillSlotNew(realSlotIndex, skillIndex, j, skillLevel)
					skillPage.SetCoverButton(realSlotIndex)

					if (not self.__CanUseSkillNow()) or (skillGrade != j):
						skillPage.SetSlotCount(realSlotIndex, 0)
						skillPage.DisableCoverButton(realSlotIndex)
						skillPage.DeactivateSlot(realSlotIndex) # hotfix
						if counts:
							counts.Clear(realSlotIndex)
					else:
						skillPage.SetSlotCountNew(realSlotIndex, skillGrade, skillLevel)
						if counts:
							counts.Set(realSlotIndex, skillGrade, skillLevel)

					isActive = activeList.get(realSlotIndex, False)
					coolTime,elapsedTime = cooltmList.get(realSlotIndex, (0,0))
					if isActive:
						skillPage.ActivateSlotOld(realSlotIndex)
					if coolTime:
						skillPage.SetSlotCoolTime(realSlotIndex, coolTime, elapsedTime)

				if player.IsSkillActive(slotIndex):
					skillPage.ActivateSlotOld(self.__GetRealSkillSlot(skillGrade, slotIndex))
					skillActivated = True
			## 그외
			else:
				if not SHOW_LIMIT_SUPPORT_SKILL_LIST or skillIndex in SHOW_LIMIT_SUPPORT_SKILL_LIST:
					realSlotIndex = self.__GetETCSkillRealSlotIndex(slotIndex)
					skillPage.SetSkillSlot(realSlotIndex, skillIndex, skillLevel)
					skillPage.SetSlotCountNew(realSlotIndex, skillGrade, skillLevel)
					if counts:
						counts.Set(realSlotIndex, skillGrade, skillLevel)

					if skill.CanUseSkill(skillIndex):
						skillPage.SetCoverButton(realSlotIndex)

					if player.IsSkillActive(slotIndex):  # hotfix
						skillPage.ActivateSlotOld(realSlotIndex)
						skillActivated = True
					else:
						skillPage.DeactivateSlot(realSlotIndex)

			skillPage.RefreshSlot()

		if counts:
			counts.Sync()

		## 쿨 타임 복원
		self.__RestoreSlotCoolTime(skillPage)

		if app.ENABLE_SKILL_COLOR_SYSTEM:
			if "ACTIVE" == name:
				self.__CreateSkillColorButton(skillPage)

	def __RestoreSlotCoolTime(self, skillPage):
		skillPage.RestoreSlotCoolTime(skill.SKILL_TYPE_ACTIVE)

	def RefreshSkill(self):
		if self.isLoaded==0:
			return

		global SHOW_ONLY_ACTIVE_SKILL
		if SHOW_ONLY_ACTIVE_SKILL:
			self.__RefreshSkillPage("ACTIVE", self.ACTIVE_PAGE_SLOT_COUNT)
		else:
			self.__RefreshSkillPage("ACTIVE", self.ACTIVE_PAGE_SLOT_COUNT)
			self.__RefreshSkillPage("SUPPORT", self.SUPPORT_PAGE_SLOT_COUNT)

		self.RefreshSkillPlusButtonList()

	def __RefreshSkillPlusButton(self, name):
		global HIDE_SUPPORT_SKILL_POINT
		if HIDE_SUPPORT_SKILL_POINT and "SUPPORT" == name:
			return

		slotWindow = self.skillPageDict[name]
		slotWindow.HideAllSlotButton()

		slotStatType = self.skillPageStatDict[name]
		if 0 == slotStatType:
			return

		statPoint = player.GetStatus(slotStatType)
		startSlotIndex = slotWindow.GetStartIndex()
		if "HORSE" == name:
			startSlotIndex += self.ACTIVE_PAGE_SLOT_COUNT

		if statPoint > 0:
			for i in range(self.PAGE_SLOT_COUNT):
				slotIndex = i + startSlotIndex
				skillIndex = player.GetSkillIndex(slotIndex)
				skillGrade = player.GetSkillGrade(slotIndex)
				skillLevel = player.GetSkillLevel(slotIndex)

				if skillIndex == 0:
					continue
				if skillGrade != 0:
					continue

				if name == "HORSE":
					if player.GetStatus(player.LEVEL) >= skill.GetSkillLevelLimit(skillIndex):
						if skillLevel < 20:
							slotWindow.ShowSlotButton(self.__GetETCSkillRealSlotIndex(slotIndex))
				else:
					# One rule with "Zvýšit schopnost" (skillraise): the right point pool, grade 0, CanLevelUpSkill.
					if "SUPPORT" == name:
						if not SHOW_LIMIT_SUPPORT_SKILL_LIST or skillIndex in SHOW_LIMIT_SUPPORT_SKILL_LIST:
							if skillraise.CanTakePoint(player, skill, slotIndex, skillraise.PAGE_SUPPORT):
								slotWindow.ShowSlotButton(slotIndex)
					else:
						if skillraise.CanTakePoint(player, skill, slotIndex, skillraise.PAGE_ACTIVE):
							slotWindow.ShowSlotButton(slotIndex)

	if app.ENABLE_SKILL_COLOR_SYSTEM:
		def __IsColorableSkill(self, skillIndex):
			if not osfInfo.SKILL_COLOR_BUFF_ONLY:
				return True

			WARRIOR_SG = [
				[3, 4], # WARRIOR SG1
				[19] # WARRIOR SG2
			]
			NINJA_SG = [
				[34], # NINJA SG1
				[49] # NINJA SG2
			]
			SURA_SG = [
				[63, 64, 65], # SURA SG1
				[78, 79] # SURA SG2
			]
			SHAMAN_SG = [
				[94, 95, 96], # SHAMAN SG1
				[109, 110, 111] # SHAMAN SG1
			]

			if skillIndex in WARRIOR_SG[0] or skillIndex in WARRIOR_SG[1] or\
				skillIndex in NINJA_SG[0] or skillIndex in NINJA_SG[1] or\
				skillIndex in SURA_SG[0] or skillIndex in SURA_SG[1] or\
				skillIndex in SHAMAN_SG[0] or skillIndex in SHAMAN_SG[1]:
				return True
			return False

		def __CreateSkillColorButton(self, parent):
			for button in self.skillColorButton:
				button.Hide()
			self.skillColorButton = []
			if self.selectedSkillTab != 0:
				return
			# SlotWindow paints its own icons after its children. A sibling on
			# Skill_Page keeps the full 16x17 rainbow above the completed slot.
			page = self.GetChild("Skill_Page")
			pageX, pageY = parent.GetLocalPosition()
			for skillSlot in range(6):
				skillSlotIndex = skillSlot + 1
				skillIndex = player.GetSkillIndex(skillSlotIndex)
				grade = player.GetSkillGrade(skillSlotIndex)
				if SKILL_GRADE_SAGE_MASTER is None or grade != SKILL_GRADE_SAGE_MASTER:
					continue
				if not skillIndex or not self.__IsColorableSkill(skillIndex):
					continue
				position = parent.GetSlotLocalPosition(self.__GetRealSkillSlot(grade, skillSlotIndex))
				if position is None:
					continue
				button = ui.Button()
				button.SetParent(page)
				button.SetUpVisual("d:/ymir work/ui/skillcolor/skill_color_button_default.tga")
				button.SetOverVisual("d:/ymir work/ui/skillcolor/skill_color_button_over.tga")
				button.SetDownVisual("d:/ymir work/ui/skillcolor/skill_color_button_down.tga")
				button.SetPosition(pageX + position[0], pageY + position[1])
				button.SetToolTipText("Barva schopnosti")
				button.SetEvent(lambda arg=skillSlot, arg2=skillIndex: ui.__mem_func__(self.__OnPressSkillColorButton)(arg, arg2))
				button.Show()
				self.skillColorButton.append(button)

		def __UpdateSkillColorPosition(self):
			x,y = self.GetGlobalPosition()
			self.skillColorWnd.SetPosition(x + 250,y)

		def __OnPressSkillColorButton(self, skillSlot, skillIndex):
			if self.skillColorWnd:
				self.skillColorWnd.Close()
			self.skillColorWnd = uiSkillColor.SkillColorWindow(skillSlot, skillIndex)
			if self.skillColorWnd and not self.skillColorWnd.IsShow():
				self.skillColorWnd.Show()

				if app.ENABLE_DETAILS_UI:
					if self.chDetailsWnd and self.chDetailsWnd.IsShow():
						self.chDetailsWnd.Hide()
						self.__InitCharacterDetailsUIButton()

	def RefreshSkillPlusButtonList(self):
		if self.isLoaded==0:
			return

		self.RefreshSkillPlusPointLabel()

		if not self.__CanUseSkillNow():
			return

		try:
			self.__RefreshSkillPlusButton("ACTIVE")

			self.__RefreshSkillPlusButton("SUPPORT")

		except:
			import exception
			exception.Abort("CharacterWindow.RefreshSkillPlusButtonList.BindObject")

	def RefreshSkillPlusPointLabel(self):
		if self.isLoaded==0:
			return

		activeStatPoint = player.GetStatus(player.SKILL_ACTIVE)
		self.activeSkillPointValue.SetText("%s: %d" % (uiScriptLocale.CREATE_LAST_POINT, activeStatPoint))
		if self.activeSkillPointValue.GetTextSize()[0] > self.skillPointArea.GetWidth():
			self.activeSkillPointValue.SetText(str(activeStatPoint))

		supportStatPoint = max(0, player.GetStatus(player.SKILL_SUPPORT))
		self.supportSkillPointValue.SetText(str(supportStatPoint))
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncSafe()

	## Skill Level Up Button
	def OnPressedSlotButton(self, slotNumber):
		srcSlotIndex = self.__RealSkillSlotToSourceSlot(slotNumber)

		skillIndex = player.GetSkillIndex(srcSlotIndex)
		curLevel = player.GetSkillLevel(srcSlotIndex)
		maxLevel = skill.GetSkillMaxLevel(skillIndex)

		net.SendChatPacket("/skillup " + str(skillIndex))

	## Use Skill
	def ClickSkillSlot(self, slotIndex):
		srcSlotIndex = self.__RealSkillSlotToSourceSlot(slotIndex)
		skillIndex = player.GetSkillIndex(srcSlotIndex)
		skillType = skill.GetSkillType(skillIndex)

		if not self.__CanUseSkillNow():
			if skill.SKILL_TYPE_ACTIVE == skillType:
				return

		for slotWindow in self.skillPageDict.values():
			if slotWindow.HasSlot(slotIndex):
				if skill.CanUseSkill(skillIndex):
					player.ClickSkillSlot(srcSlotIndex)
					return

		mouseModule.mouseController.DeattachObject()

	## FIXME : 스킬을 사용했을때 슬롯 번호를 가지고 해당 슬롯을 찾아서 업데이트 한다.
	## 매우 불합리. 구조 자체를 개선해야 할듯.
	def OnUseSkill(self, slotIndex, coolTime):
		skillIndex = player.GetSkillIndex(slotIndex)
		skillType = skill.GetSkillType(skillIndex)

		## ACTIVE
		if skill.SKILL_TYPE_ACTIVE == skillType:
			skillGrade = player.GetSkillGrade(slotIndex)
			slotIndex = self.__GetRealSkillSlot(skillGrade, slotIndex)
		## ETC
		else:
			slotIndex = self.__GetETCSkillRealSlotIndex(slotIndex)

		for slotWindow in self.skillPageDict.values():
			if slotWindow.HasSlot(slotIndex):
				slotWindow.StoreSlotCoolTime(skillType, slotIndex, coolTime)
				self.__RestoreSlotCoolTime(slotWindow)
				#slotWindow.SetSlotCoolTime(slotIndex, coolTime)
				return

	def OnActivateSkill(self, slotIndex):
		skillGrade = player.GetSkillGrade(slotIndex)
		slotIndex = self.__GetRealSkillSlot(skillGrade, slotIndex)

		for slotWindow in self.skillPageDict.values():
			if slotWindow.HasSlot(slotIndex):
				slotWindow.ActivateSlotOld(slotIndex)
				return

		self.RefreshSkill()

	def OnDeactivateSkill(self, slotIndex):
		skillGrade = player.GetSkillGrade(slotIndex)
		slotIndex = self.__GetRealSkillSlot(skillGrade, slotIndex)

		for slotWindow in self.skillPageDict.values():
			if slotWindow.HasSlot(slotIndex):
				slotWindow.DeactivateSlot(slotIndex)
				return

		self.RefreshSkill()

	def __ShowJobToolTip(self):
		self.toolTipJob.ShowToolTip()

	if app.ENABLE_SKILL_COOLTIME_UPDATE:
		def SkillClearCoolTime(self, slotIndex):
			slotIndex = self.__GetRealSkillSlot(player.GetSkillGrade(slotIndex), slotIndex)
			for slotWindow in self.skillPageDict.values():
				if slotWindow.HasSlot(slotIndex):
					slotWindow.SetSlotCoolTime(slotIndex, 0)

	def __HideJobToolTip(self):
		self.toolTipJob.HideToolTip()

	def __SetJobText(self, mainJob, subJob):
		if player.GetStatus(player.LEVEL)<5:
			subJob=0

		if 949 == app.GetDefaultCodePage():
			self.toolTipJob.ClearToolTip()

			try:
				jobInfoTitle=localeInfo.JOBINFO_TITLE[mainJob][subJob]
				jobInfoData=localeInfo.JOBINFO_DATA_LIST[mainJob][subJob]
			except IndexError:
				print("uiCharacter.CharacterWindow.__SetJobText(mainJob=%d, subJob=%d)" % (mainJob, subJob))
				return

			self.toolTipJob.AutoAppendTextLine(jobInfoTitle)
			self.toolTipJob.AppendSpace(5)

			for jobInfoDataLine in jobInfoData:
				self.toolTipJob.AutoAppendTextLine(jobInfoDataLine)

			self.toolTipJob.AlignHorizonalCenter()

	def __ShowAlignmentToolTip(self):
		self.toolTipAlignment.ShowToolTip()

	def __HideAlignmentToolTip(self):
		self.toolTipAlignment.HideToolTip()

	def RefreshCharacter(self):
		if self.isLoaded == 0:
			return

		## Name
		try:
			characterName = player.GetName()
			guildName = player.GetGuildName()
			self.characterNameValue.SetText(characterName)
			self.guildNameValue.SetText(guildName)
			if not guildName:
				if localeInfo.IsARABIC():
					self.characterNameSlot.SetPosition(190, 34)
				else:
					self.characterNameSlot.SetPosition(109, 34)

				self.guildNameSlot.Hide()
			else:
				if localeInfo.IsJAPAN():
					self.characterNameSlot.SetPosition(143, 34)
				else:
					self.characterNameSlot.SetPosition(153, 34)
				self.guildNameSlot.Show()

		except:
			import exception
			exception.Abort("CharacterWindow.RefreshCharacter.BindObject")

		race = net.GetMainActorRace()
		group = net.GetMainActorSkillGroup()
		empire = net.GetMainActorEmpire()

		## Job Text
		job = chr.RaceToJob(race)
		self.__SetJobText(job, group)

		## FaceImage
		try:
			faceImageName = FACE_IMAGE_DICT[race]

			try:
				self.faceImage.LoadImage(faceImageName)
			except:
				print("CharacterWindow.RefreshCharacter(race=%d, faceImageName=%s)" % (race, faceImageName))
				self.faceImage.Hide()

		except KeyError:
			self.faceImage.Hide()

		# Retain the unassigned character's read-only first-discipline preview.
		# Only the level-5 quest changes the server's actual specialization.
		self.__SetSkillSlotData(race, group or 1, empire)
		self.__SelectSkillGroup(self.selectedSkillTab)
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncSafe()

	def __SetSkillSlotData(self, race, group, empire=0):
		## SkillIndex
		if app.ENABLE_LOADING_PERFORMANCE:
			loading.RegisterSkill(race, group, empire)
		else:
			playerSettingModule.RegisterSkill(race, group, empire)

		## Event
		self.__SetSkillSlotEvent()

		## Refresh
		self.RefreshSkill()

	def __SelectSkillGroup(self, index):
		if index not in (0, 1):
			return
		self.OverOutItem()
		for btn in self.skillGroupButton:
			btn.SetUp()
			btn.ButtonText.SetPackedFontColor(0xffb8aa93)
		self.skillGroupButton[index].Down()
		self.skillGroupButton[index].ButtonText.SetPackedFontColor(0xfff8d878)
		self.selectedSkillTab = index
		for widget in (self.activeSlot, self.skillPointArea):
			if index == 0:
				widget.Show()
			else:
				widget.Hide()
		for name in ("Skill_Board", "Skill_Board_expanded"):
			if self.IsChild(name):
				if index == 0:
					self.GetChild(name).Show()
				else:
					self.GetChild(name).Hide()
		if index == 1:
			if getattr(self, "skillColorWnd", None):
				self.skillColorWnd.Close()
			self.buffPage.Show()
		else:
			self.buffPage.Hide()
		self.RefreshSkill()
		if getattr(self, "r1Skin", None):
			self.r1Skin.SyncSafe()

	def __CanUseSkillNow(self):
		if 0 == net.GetMainActorSkillGroup():
			return False

		return True

	def __GetRealSkillSlot(self, skillGrade, skillSlot):
		return skillSlot + skillpresentation.CompactGrade(skillGrade) * skill.SKILL_GRADE_STEP_COUNT

	def __GetETCSkillRealSlotIndex(self, skillSlot):
		if skillSlot > 100:
			return skillSlot
		return skillSlot % self.ACTIVE_PAGE_SLOT_COUNT

	def __RealSkillSlotToSourceSlot(self, realSkillSlot):
		if realSkillSlot > 100:
			return realSkillSlot
		return realSkillSlot % skill.SKILL_GRADE_STEP_COUNT

	def __GetSkillGradeFromSlot(self, skillSlot):
		column = int(skillSlot // skill.SKILL_GRADE_STEP_COUNT)
		actualGrade = player.GetSkillGrade(self.__RealSkillSlotToSourceSlot(skillSlot))
		return skillpresentation.ColumnGrades(actualGrade)[min(2, column)]

	def SelectSkillGroup(self, index):
		self.__SelectSkillGroup(index)

	def OnQuestScroll(self):
		questCount = len(getattr(self, "questShortcutList", ())) + len(_GetRenderableQuestData())
		scrollLineCount = max(0, questCount - quest.QUEST_MAX_NUM)
		startIndex = int(scrollLineCount * self.questScrollBar.GetPos())

		if startIndex != self.questShowingStartIndex:
			self.questShowingStartIndex = startIndex
			self.RefreshQuest()
