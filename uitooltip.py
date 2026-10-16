import bonuscolor
import dbg
import player
import item
import grp
import wndMgr
import skill
import shop
import exchange
import grpText
import safebox
import localeInfo
import sagebuff
import pvmpersonal
import pvmpersonaltext
import skilltooltiptext
import app
import net
import background
import nonplayer
import chr
import uiScriptLocale
import ui
import mouseModule
import constInfo
import osfInfo
import keybindings
import fontconfig
import inventoryshortcutpolicy
import mountspeedtooltip
import itemattributemaxima
import servergamedata
import mountcorebonus
import growthpetskillcatalog
import iscostumevoucher
import growthpetpresentation
import raritypreview
import equipmentbonuspolicy
import itembonuspresentation
import resonanceuihelpers
import auraprogression
import virtualquiver

SKILL_GRADE_SAGE_MASTER = getattr(player, "SKILL_GRADE_SAGE_MASTER", None)

if app.ENABLE_PERMA_ACCESSORY:
	import math

if app.ENABLE_ACCE_COSTUME_SYSTEM:
	import acce

if app.ENABLE_DS_SET:
	import uiDragonSoul

if app.ENABLE_RENDER_TARGET_PREVIEW:
	import renderTarget
	import WikiRenderTarget

if app.ENABLE_SHOP_SEARCH:
	import shopsearch

if app.ENABLE_REFINE_ELEMENT_SYSTEM:
	import uiRefine

WARP_SCROLLS = [22011, 22000, 22010]

RARITY_GRADE_NAMES = (
	localeInfo.RARITY_GRADE_NONE,
	localeInfo.RARITY_GRADE_MATNA,
	localeInfo.RARITY_GRADE_POZEHNANA,
	localeInfo.RARITY_GRADE_PRASTARA,
	localeInfo.RARITY_GRADE_ANTICKA,
	localeInfo.RARITY_GRADE_DRACI,
	localeInfo.RARITY_GRADE_ASTRALNI,
	localeInfo.RARITY_GRADE_BOZSKA,
)
RARITY_GRADE_COLORS = (
	grp.GenerateColor(0.65, 0.65, 0.65, 1.0),
	grp.GenerateColor(0.58, 0.58, 0.58, 1.0),
	grp.GenerateColor(0.95, 0.95, 0.95, 1.0),
	grp.GenerateColor(0.30, 0.82, 0.35, 1.0),
	grp.GenerateColor(0.30, 0.55, 1.00, 1.0),
	grp.GenerateColor(1.00, 0.55, 0.18, 1.0),
	grp.GenerateColor(0.70, 0.35, 1.00, 1.0),
	grp.GenerateColor(1.00, 0.82, 0.20, 1.0),
)

def ResolveRarityInventoryWindow(windowType, slotIndex):
	if windowType == player.INVENTORY and player.IsEquipmentSlot(slotIndex):
		return player.EQUIPMENT
	return windowType

def GetRarityExtraSafe(*key):
	# Native GetRarityExtra raises for an unknown context (e.g. vid or public id 0).
	getter = getattr(net, "GetRarityExtra", None)
	if not getter:
		return None
	try:
		return getter(*[int(value) for value in key])
	except (TypeError, ValueError, RuntimeError, SystemError):
		return None

ICON_SKILLBOOK_VNUM_MIN = 50401
ICON_SKILLBOOK_VNUM_MAX = 50511

DESC_DEFAULT_MAX_COLS = 26 
DESC_WESTERN_MAX_COLS = 35
DESC_WESTERN_MAX_WIDTH = 220

LEADERSHIP_ATTACKER_BASE_VALUE = 10
LEADERSHIP_ATTACKER_ADJUSTMENT_VALUE = 50
LEADERSHIP_TANKER_BASE_VALUE = 50
LEADERSHIP_TANKER_ADJUSTMENT_VALUE = 1120
LEADERSHIP_BUFFER_BASE_VALUE = 5
LEADERSHIP_BUFFER_ADJUSTMENT_VALUE = 8
LEADERSHIP_SKILL_MASTER_BASE_VALUE = 1
LEADERSHIP_SKILL_MASTER_ADJUSTMENT_VALUE = 2
LEADERSHIP_BERSERKER_BASE_VALUE = 1
LEADERSHIP_BERSERKER_ADJUSTMENT_VALUE = 3
LEADERSHIP_DEFENDER_BASE_VALUE = 1
LEADERSHIP_DEFENDER_ADJUSTMENT_VALUE = 3

if app.ENABLE_PARTY_INSIGHT:
	INSIGHT_ATTACKER_BASE_VALUE = 2
	INSIGHT_ATTACKER_ADJUSTMENT_VALUE = 9
	INSIGHT_TANKER_BASE_VALUE = 10
	INSIGHT_TANKER_ADJUSTMENT_VALUE = 520
	INSIGHT_BUFFER_BASE_VALUE = 1
	INSIGHT_BUFFER_ADJUSTMENT_VALUE = 4
	INSIGHT_SKILL_MASTER_BASE_VALUE = 1
	INSIGHT_SKILL_MASTER_ADJUSTMENT_VALUE = 5
	INSIGHT_BERSERKER_BASE_VALUE = 1
	INSIGHT_BERSERKER_ADJUSTMENT_VALUE = 1
	INSIGHT_DEFENDER_BASE_VALUE = 1
	INSIGHT_DEFENDER_ADJUSTMENT_VALUE = 2

def chop(n):
	return round(n - 0.5, 1)

def GET_AFFECT_STRING(affType, affValue):
	if 0 == affType:
		return None
	
	try:
		affectString = ItemToolTip.AFFECT_DICT[affType]
		if type(affectString) != str:
			return affectString(affValue)

		if affectString.find("%d") != -1:
			return affectString % affValue
		else:
			return affectString
	except KeyError:
		return "UNKNOWN_TYPE[%s] %s" % (affType, affValue)

def SplitDescription(desc, limit):
	total_tokens = desc.split()
	line_tokens = []
	line_len = 0
	lines = []

	for token in total_tokens:
		if "|" in token:
			sep_pos = token.find("|")
			line_tokens.append(token[:sep_pos])
			lines.append(" ".join(line_tokens))
			line_len = len(token) - (sep_pos + 1)
			line_tokens = [token[sep_pos+1:]]
		elif app.WJ_MULTI_TEXTLINE and "\\n" in token:
			sep_pos = token.find("\\n")
			line_tokens.append(token[:sep_pos])

			lines.append(" ".join(line_tokens))
			line_len = len(token) - (sep_pos + 2)
			line_tokens = [token[sep_pos+2:]]
		else:
			line_len += len(token)
			if len(line_tokens) + line_len > limit:
				lines.append(" ".join(line_tokens))
				line_len = len(token)
				line_tokens = [token]
			else:
				line_tokens.append(token)

	if line_tokens:
		lines.append(" ".join(line_tokens))

	return lines

###################################################################################################
## ToolTip
##
##	NOTE : 현재는 Item과 Skill을 상속으로 특화 시켜두었음
##			하지만 그다지 의미가 없어 보임
##
class ToolTip(ui.ThinBoard):
	TOOL_TIP_WIDTH = 190
	TOOL_TIP_HEIGHT = 10

	TEXT_LINE_HEIGHT = 17

	TITLE_COLOR = grp.GenerateColor(0.9490, 0.9058, 0.7568, 1.0)
	SPECIAL_TITLE_COLOR = grp.GenerateColor(1.0, 0.7843, 0.0, 1.0)
	NORMAL_COLOR = grp.GenerateColor(0.7607, 0.7607, 0.7607, 1.0)
	FONT_COLOR = grp.GenerateColor(0.7607, 0.7607, 0.7607, 1.0)
	PRICE_COLOR = 0xffFFB96D

	HIGH_PRICE_COLOR = SPECIAL_TITLE_COLOR
	MIDDLE_PRICE_COLOR = grp.GenerateColor(0.85, 0.85, 0.85, 1.0)
	LOW_PRICE_COLOR = grp.GenerateColor(0.7, 0.7, 0.7, 1.0)

	ENABLE_COLOR = grp.GenerateColor(0.7607, 0.7607, 0.7607, 1.0)
	DISABLE_COLOR = grp.GenerateColor(0.9, 0.4745, 0.4627, 1.0)

	NEGATIVE_COLOR = grp.GenerateColor(0.9, 0.4745, 0.4627, 1.0)
	POSITIVE_COLOR = grp.GenerateColor(0.5411, 0.7254, 0.5568, 1.0)
	SPECIAL_POSITIVE_COLOR = grp.GenerateColor(0.6911, 0.8754, 0.7068, 1.0)
	SPECIAL_POSITIVE_COLOR2 = grp.GenerateColor(0.8824, 0.9804, 0.8824, 1.0)

	if app.ENABLE_CUBE_RENEWAL:
		PRICE_INFO_COLOR = grp.GenerateColor((255.0/255.0), (255.0/255.0), (102.0/255.0), 1.0)
		GEM_PRICE_COLOR = grp.GenerateColor((156.0/255.0), (255.0/255.0), (255.0/255.0), 1.0)

	if app.ENABLE_DS_SET:
		TEXTLINE_2ND_COLOR_DEFAULT = grp.GenerateColor(1.0, 1.0, 0.6078, 1.0)

	if app.ENABLE_ATTR_6TH_7TH:
		ATTR_6TH_7TH_COLOR = grp.GenerateColor(1.0, 1.0, 0.6078, 1.0)

	CONDITION_COLOR = 0xffBEB47D
	CAN_LEVEL_UP_COLOR = 0xff8EC292
	CANNOT_LEVEL_UP_COLOR = DISABLE_COLOR
	NEED_SKILL_POINT_COLOR = 0xff9A9CDB

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		CHANGELOOK_TITLE_COLOR = 0xff8BBDFF
		CHANGELOOK_ITEMNAME_COLOR = 0xffBCE55C

	if app.ENABLE_APPLY_RANDOM:
		APPLY_RANDOM_TEXT_COLOR = 0xff7AF6D4

	def __init__(self, width = TOOL_TIP_WIDTH, isPickable=False):
		ui.ThinBoard.__init__(
			self,
			"TOP_MOST",
			cornerPrefix=ui.TOOLTIP_CORNER_PREFIX,
			linePrefix=ui.TOOLTIP_LINE_PREFIX,
			baseColor=ui.TOOLTIP_BASE_COLOR,
		)

		if isPickable:
			pass
		else:
			self.AddFlag("not_pick")

		self.AddFlag("float")

		self.followFlag = True
		self.toolTipWidth = width

		self.xPos = -1
		self.yPos = -1

		if app.ENABLE_DS_SET:
			self.window_type = player.INVENTORY

		self.defFontName = fontconfig.FontForRole(fontconfig.ROLE_BODY)
		self.ClearToolTip()

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def ClearToolTip(self):
		self.toolTipHeight = 12
		self.childrenList = []

	def SetFollow(self, flag):
		self.followFlag = flag

	def SetDefaultFontName(self, fontName):
		self.defFontName = fontName

	def AppendSpace(self, size):
		self.toolTipHeight += size
		self.ResizeToolTip()

	def SetThinBoardSize(self, width, height = 12):
		self.toolTipWidth = width 
		self.toolTipHeight = height

	def AppendHorizontalLine(self):
		for i in range(2):
			horizontalLine = ui.Line()
			horizontalLine.SetParent(self)
			horizontalLine.SetPosition(0, self.toolTipHeight + 3 + i)
			horizontalLine.SetWindowHorizontalAlignCenter()
			horizontalLine.SetSize(150, 0)
			horizontalLine.Show()

			if 0 == i:
				horizontalLine.SetColor(0xff555555)
			else:
				horizontalLine.SetColor(0xff000000)

			self.childrenList.append(horizontalLine)

		self.toolTipHeight += 11
		self.ResizeToolTip()

	def AlignHorizonalCenter(self):
		for child in self.childrenList:
			(x, y) = child.GetLocalPosition()
			child.SetPosition(self.toolTipWidth//2, y)

		self.ResizeToolTip()

	def AlignTextLineHorizonalCenter(self):
		for child in self.childrenList:
			if type(child).__name__ == "TextLine":
				(x, y) = child.GetLocalPosition()
				child.SetPosition(self.toolTipWidth // 2, y)

		self.ResizeToolTip()

	def AutoAppendNewTextLineResize(self, text, color = FONT_COLOR, centerAlign = True):
		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetFontName(self.defFontName)
		textLine.SetPackedFontColor(color)
		textLine.SetText(text)
		textLine.SetOutline()
		textLine.SetFeather(False)
		textLine.Show()
 
		(textWidth, textHeight) = textLine.GetTextSize()
		textWidth += 30
		textHeight += 10
		if self.toolTipWidth < textWidth:
			self.toolTipWidth = textWidth
 
		if centerAlign:
			textLine.SetPosition(self.toolTipWidth//2, self.toolTipHeight)
			textLine.SetHorizontalAlignCenter()
		else:
			textLine.SetPosition(10, self.toolTipHeight)
 
		self.childrenList.append(textLine)
 
		self.toolTipHeight += self.TEXT_LINE_HEIGHT
		self.AlignHorizonalCenter()
		return textLine

	def AutoAppendTextLine(self, text, color = FONT_COLOR, centerAlign = True):
		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetFontName(self.defFontName)
		textLine.SetPackedFontColor(color)
		textLine.SetText(text)
		textLine.SetOutline()
		textLine.SetFeather(False)
		textLine.Show()

		if centerAlign:
			textLine.SetPosition(self.toolTipWidth//2, self.toolTipHeight)
			textLine.SetHorizontalAlignCenter()
		else:
			textLine.SetPosition(10, self.toolTipHeight)

		self.childrenList.append(textLine)

		(textWidth, textHeight)=textLine.GetTextSize()

		textWidth += 40
		textHeight += 5

		if self.toolTipWidth < textWidth:
			self.toolTipWidth = textWidth

		self.toolTipHeight += textHeight

		return textLine

	def SetThinBoardSize(self, width, height = 12):
		self.toolTipWidth = width 
		self.toolTipHeight = height

	def AppendTextLine(self, text, color = FONT_COLOR, centerAlign = True):
		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetFontName(self.defFontName)
		textLine.SetPackedFontColor(color)
		textLine.SetText(text)
		textLine.SetOutline()
		textLine.SetFeather(False)
		if app.WJ_MULTI_TEXTLINE:
			textLine.SetLineHeight(self.TEXT_LINE_HEIGHT)
		textLine.Show()

		if centerAlign:
			textLine.SetPosition(self.toolTipWidth//2, self.toolTipHeight)
			textLine.SetHorizontalAlignCenter()

		else:
			textLine.SetPosition(10, self.toolTipHeight)

		self.childrenList.append(textLine)

		if app.WJ_MULTI_TEXTLINE:
			lineCount = textLine.GetTextLineCount()
			self.toolTipHeight += self.TEXT_LINE_HEIGHT * lineCount
		else:
			self.toolTipHeight += self.TEXT_LINE_HEIGHT

		self.ResizeToolTip()

		return textLine

	if app.ENABLE_DS_SET:
		def AppendTwoColorTextLine(self, text, color, text2, color2 = TEXTLINE_2ND_COLOR_DEFAULT, centerAlign = True):
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetFontName(self.defFontName)
			textLine.SetPackedFontColor(color)
			textLine.SetText(text)
			textLine.SetOutline()
			textLine.SetFeather(False)
			w, h = textLine.GetTextSize()

			textLine2 = ui.TextLine()
			textLine2.SetParent(textLine)
			textLine2.SetFontName(self.defFontName)
			textLine2.SetPackedFontColor(color2)
			textLine2.SetText(text2)
			textLine2.SetOutline()
			textLine2.SetFeather(False)
			textLine2.Show()

			w2, h2 = textLine2.GetTextSize()

			textLine.SetLineHeight(self.TEXT_LINE_HEIGHT)
			textLine.Show()

			if centerAlign:
				if localeInfo.IsARABIC():
					textLine.SetPosition(self.toolTipWidth // 2 + w2 // 2, self.toolTipHeight)
					textLine.SetHorizontalAlignCenter()
					textLine2.SetPosition(-w // 2, 0)
				else:
					textLine.SetPosition(self.toolTipWidth // 2 -w2 // 2, self.toolTipHeight)
					textLine.SetHorizontalAlignCenter()
					textLine2.SetPosition(w // 2, 0)
			else:
				textLine.SetPosition(10, self.toolTipHeight)

			self.childrenList.append(textLine)
			self.childrenList.append(textLine2)

			lineCount = textLine.GetTextLineCount()
			self.toolTipHeight += self.TEXT_LINE_HEIGHT * lineCount

			self.ResizeToolTip()

			return textLine

	def AppendDescription(self, desc, limit, color = FONT_COLOR):
		if localeInfo.IsEUROPE():
			self.__AppendDescription_WesternLanguage(desc, color)
		else:
			self.__AppendDescription_EasternLanguage(desc, limit, color)

	def __AppendDescription_EasternLanguage(self, description, characterLimitation, color=FONT_COLOR):
		length = len(description)
		if 0 == length:
			return

		lineCount = grpText.GetSplitingTextLineCount(description, characterLimitation)
		for i in range(lineCount):
			if 0 == i:
				self.AppendSpace(5)
			self.AppendTextLine(grpText.GetSplitingTextLine(description, characterLimitation, i), color)

	def __AppendDescription_WesternLanguage(self, desc, color=FONT_COLOR):
		lines = SplitDescription(desc, DESC_WESTERN_MAX_COLS)
		if not lines:
			return

		self.AppendSpace(5)
		for line in lines:
			self.AppendTextLine(line, color)

	def ResizeToolTip(self):
		self.SetSize(self.toolTipWidth, self.TOOL_TIP_HEIGHT + self.toolTipHeight)

	def SetTitle(self, name):
		self.AppendTextLine(name, self.TITLE_COLOR)

	def GetLimitTextLineColor(self, curValue, limitValue):
		if curValue < limitValue:
			return self.DISABLE_COLOR

		return self.ENABLE_COLOR

	def GetChangeTextLineColor(self, value, isSpecial=False):
		if value > 0:
			if isSpecial:
				return self.SPECIAL_POSITIVE_COLOR
			else:
				return self.POSITIVE_COLOR

		if 0 == value:
			return self.NORMAL_COLOR

		return self.NEGATIVE_COLOR

	def SetToolTipPosition(self, x = -1, y = -1):
		self.xPos = x
		self.yPos = y

	def ShowToolTip(self):
		self.SetTop()
		self.Show()

		self.OnUpdate()

	def HideToolTip(self):
		self.Hide()

	if app.ENABLE_EXPRESSING_EMOTION:
		def AppendLastTime(self, endTime):
			leftSec = max(0, endTime - app.GetGlobalTimeStamp())
			if leftSec > 0:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftSec), self.NORMAL_COLOR)

	def OnUpdate(self):
		if not self.followFlag:
			return

		x = 0
		y = 0
		width = self.GetWidth()
		height = self.toolTipHeight

		if -1 == self.xPos and -1 == self.yPos:
			(mouseX, mouseY) = wndMgr.GetMousePosition()

			if mouseY < wndMgr.GetScreenHeight() - 300:
				y = mouseY + 40
			else:
				y = mouseY - height - 30

			x = mouseX - width//2

		else:
			x = self.xPos - width//2
			y = self.yPos - height

		x = max(x, 0)
		y = max(y, 0)
		x = min(x + width//2, wndMgr.GetScreenWidth() - width//2) - width//2
		y = min(y + self.GetHeight(), wndMgr.GetScreenHeight()) - self.GetHeight()

		parentWindow = self.GetParentProxy()
		if parentWindow:
			(gx, gy) = parentWindow.GetGlobalPosition()
			x -= gx
			y -= gy

		self.SetPosition(x, y)

class ItemToolTip(ToolTip):
	MAXIMUM_ATTRIBUTE_COLOR = grp.GenerateColor(64 / 255.0, 224 / 255.0, 117 / 255.0, 1.0)
	RESONANCE_TOOLTIP_SLOT_IMAGE = "d:/ymir work/ui/game/windows/metin_slot_silver.sub"
	RESONANCE_TOOLTIP_TEXT_X = 44
	RESONANCE_TOOLTIP_RIGHT_PADDING = 9
	MOUNT_PREVIEW_WIDTH = 220
	MOUNT_PREVIEW_HEIGHT = 150
	MOUNT_PREVIEW_MARGIN = 10
	MOUNT_PREVIEW_TOOLTIP_WIDTH = MOUNT_PREVIEW_WIDTH + MOUNT_PREVIEW_MARGIN * 2
	COSTUME_PREVIEW_WIDTH = 170
	COSTUME_PREVIEW_HEIGHT = 220
	COSTUME_PREVIEW_MARGIN = 10
	COSTUME_PREVIEW_TOOLTIP_WIDTH = COSTUME_PREVIEW_WIDTH + COSTUME_PREVIEW_MARGIN * 2
	# Player-type render targets expose no readiness; show the actor after a
	# short settle time so fast hovering never flashes a half-built model.
	COSTUME_PREVIEW_SETTLE_TIME = 0.25
	COSTUME_PREVIEW_DEGREES_PER_SECOND = 60.0
	COSTUME_VOUCHER_COLOR = 0xff8BBDFF

	if not app.DISABLE_WOLFMAN_CREATION:
		CHARACTER_NAMES = (
			localeInfo.TOOLTIP_WARRIOR,
			localeInfo.TOOLTIP_ASSASSIN,
			localeInfo.TOOLTIP_SURA,
			localeInfo.TOOLTIP_SHAMAN,
			localeInfo.TOOLTIP_WOLFMAN
		)
	else:
		CHARACTER_NAMES = (
			localeInfo.TOOLTIP_WARRIOR,
			localeInfo.TOOLTIP_ASSASSIN,
			localeInfo.TOOLTIP_SURA,
			localeInfo.TOOLTIP_SHAMAN,
		)

	CHARACTER_COUNT = len(CHARACTER_NAMES)
	WEAR_NAMES = ( 
		localeInfo.TOOLTIP_ARMOR, 
		localeInfo.TOOLTIP_HELMET, 
		localeInfo.TOOLTIP_SHOES, 
		localeInfo.TOOLTIP_WRISTLET, 
		localeInfo.TOOLTIP_WEAPON, 
		localeInfo.TOOLTIP_NECK,
		localeInfo.TOOLTIP_EAR,
		localeInfo.TOOLTIP_UNIQUE,
		localeInfo.TOOLTIP_SHIELD,
		localeInfo.TOOLTIP_ARROW,
	)
	WEAR_COUNT = len(WEAR_NAMES)

	if not app.DISABLE_WOLFMAN_CREATION:
		AFFECT_DICT = {
			item.APPLY_MAX_HP : localeInfo.TOOLTIP_MAX_HP,
			item.APPLY_MAX_SP : localeInfo.TOOLTIP_MAX_SP,
			item.APPLY_CON : localeInfo.TOOLTIP_CON,
			item.APPLY_INT : localeInfo.TOOLTIP_INT,
			item.APPLY_STR : localeInfo.TOOLTIP_STR,
			item.APPLY_DEX : localeInfo.TOOLTIP_DEX,
			item.APPLY_ATT_SPEED : localeInfo.TOOLTIP_ATT_SPEED,
			item.APPLY_MOV_SPEED : localeInfo.TOOLTIP_MOV_SPEED,
			item.APPLY_CAST_SPEED : localeInfo.TOOLTIP_CAST_SPEED,
			item.APPLY_HP_REGEN : localeInfo.TOOLTIP_HP_REGEN,
			item.APPLY_SP_REGEN : localeInfo.TOOLTIP_SP_REGEN,
			item.APPLY_POISON_PCT : localeInfo.TOOLTIP_APPLY_POISON_PCT,
			item.APPLY_BLEEDING_PCT : localeInfo.TOOLTIP_APPLY_BLEEDING_PCT,
			item.APPLY_STUN_PCT : localeInfo.TOOLTIP_APPLY_STUN_PCT,
			item.APPLY_SLOW_PCT : localeInfo.TOOLTIP_APPLY_SLOW_PCT,
			item.APPLY_CRITICAL_PCT : localeInfo.TOOLTIP_APPLY_CRITICAL_PCT,
			item.APPLY_PENETRATE_PCT : localeInfo.TOOLTIP_APPLY_PENETRATE_PCT,

			item.APPLY_ATTBONUS_WARRIOR : localeInfo.TOOLTIP_APPLY_ATTBONUS_WARRIOR,
			item.APPLY_ATTBONUS_ASSASSIN : localeInfo.TOOLTIP_APPLY_ATTBONUS_ASSASSIN,
			item.APPLY_ATTBONUS_SURA : localeInfo.TOOLTIP_APPLY_ATTBONUS_SURA,
			item.APPLY_ATTBONUS_SHAMAN : localeInfo.TOOLTIP_APPLY_ATTBONUS_SHAMAN,
			item.APPLY_ATTBONUS_MONSTER : localeInfo.TOOLTIP_APPLY_ATTBONUS_MONSTER,

			item.APPLY_ATTBONUS_HUMAN : localeInfo.TOOLTIP_APPLY_ATTBONUS_HUMAN,
			item.APPLY_ATTBONUS_ANIMAL : localeInfo.TOOLTIP_APPLY_ATTBONUS_ANIMAL,
			item.APPLY_ATTBONUS_ORC : localeInfo.TOOLTIP_APPLY_ATTBONUS_ORC,
			item.APPLY_ATTBONUS_MILGYO : localeInfo.TOOLTIP_APPLY_ATTBONUS_MILGYO,
			item.APPLY_ATTBONUS_UNDEAD : localeInfo.TOOLTIP_APPLY_ATTBONUS_UNDEAD,
			item.APPLY_ATTBONUS_DEVIL : localeInfo.TOOLTIP_APPLY_ATTBONUS_DEVIL,
			item.APPLY_STEAL_HP : localeInfo.TOOLTIP_APPLY_STEAL_HP,
			item.APPLY_STEAL_SP : localeInfo.TOOLTIP_APPLY_STEAL_SP,
			item.APPLY_MANA_BURN_PCT : localeInfo.TOOLTIP_APPLY_MANA_BURN_PCT,
			item.APPLY_DAMAGE_SP_RECOVER : localeInfo.TOOLTIP_APPLY_DAMAGE_SP_RECOVER,
			item.APPLY_BLOCK : localeInfo.TOOLTIP_APPLY_BLOCK,
			item.APPLY_DODGE : localeInfo.TOOLTIP_APPLY_DODGE,
			item.APPLY_RESIST_SWORD : localeInfo.TOOLTIP_APPLY_RESIST_SWORD,
			item.APPLY_RESIST_TWOHAND : localeInfo.TOOLTIP_APPLY_RESIST_TWOHAND,
			item.APPLY_RESIST_DAGGER : localeInfo.TOOLTIP_APPLY_RESIST_DAGGER,
			item.APPLY_RESIST_BELL : localeInfo.TOOLTIP_APPLY_RESIST_BELL,
			item.APPLY_RESIST_FAN : localeInfo.TOOLTIP_APPLY_RESIST_FAN,
			item.APPLY_RESIST_BOW : localeInfo.TOOLTIP_RESIST_BOW,
			item.APPLY_RESIST_FIRE : localeInfo.TOOLTIP_RESIST_FIRE,
			item.APPLY_RESIST_ELEC : localeInfo.TOOLTIP_RESIST_ELEC,
			item.APPLY_RESIST_MAGIC : localeInfo.TOOLTIP_RESIST_MAGIC,
			item.APPLY_RESIST_WIND : localeInfo.TOOLTIP_APPLY_RESIST_WIND,
			item.APPLY_REFLECT_MELEE : localeInfo.TOOLTIP_APPLY_REFLECT_MELEE,
			item.APPLY_REFLECT_CURSE : localeInfo.TOOLTIP_APPLY_REFLECT_CURSE,
			item.APPLY_POISON_REDUCE : localeInfo.TOOLTIP_APPLY_POISON_REDUCE,
			item.APPLY_BLEEDING_REDUCE : localeInfo.TOOLTIP_APPLY_BLEEDING_REDUCE,
			item.APPLY_KILL_SP_RECOVER : localeInfo.TOOLTIP_APPLY_KILL_SP_RECOVER,
			item.APPLY_EXP_DOUBLE_BONUS : localeInfo.TOOLTIP_APPLY_EXP_DOUBLE_BONUS,
			item.APPLY_GOLD_DOUBLE_BONUS : localeInfo.TOOLTIP_APPLY_GOLD_DOUBLE_BONUS,
			item.APPLY_ITEM_DROP_BONUS : localeInfo.TOOLTIP_APPLY_ITEM_DROP_BONUS,
			item.APPLY_POTION_BONUS : localeInfo.TOOLTIP_APPLY_POTION_BONUS,
			item.APPLY_KILL_HP_RECOVER : localeInfo.TOOLTIP_APPLY_KILL_HP_RECOVER,
			item.APPLY_IMMUNE_STUN : localeInfo.TOOLTIP_APPLY_IMMUNE_STUN,
			item.APPLY_IMMUNE_SLOW : localeInfo.TOOLTIP_APPLY_IMMUNE_SLOW,
			item.APPLY_IMMUNE_FALL : localeInfo.TOOLTIP_APPLY_IMMUNE_FALL,
			item.APPLY_BOW_DISTANCE : localeInfo.TOOLTIP_BOW_DISTANCE,
			item.APPLY_DEF_GRADE_BONUS : localeInfo.TOOLTIP_DEF_GRADE,
			# Belt pool rolls APPLY_DEF_GRADE (83), a different apply from bonus 54.
			83 : localeInfo.TOOLTIP_DEF_GRADE,
			item.APPLY_ATT_GRADE_BONUS : localeInfo.TOOLTIP_ATT_GRADE,
			item.APPLY_MAGIC_ATT_GRADE : localeInfo.TOOLTIP_MAGIC_ATT_GRADE,
			item.APPLY_MAGIC_DEF_GRADE : localeInfo.TOOLTIP_MAGIC_DEF_GRADE,
			item.APPLY_MAX_STAMINA : localeInfo.TOOLTIP_MAX_STAMINA,
			item.APPLY_MALL_ATTBONUS : localeInfo.TOOLTIP_MALL_ATTBONUS,
			item.APPLY_MALL_DEFBONUS : localeInfo.TOOLTIP_MALL_DEFBONUS,
			item.APPLY_MALL_EXPBONUS : localeInfo.TOOLTIP_MALL_EXPBONUS,
			item.APPLY_MALL_ITEMBONUS : localeInfo.TOOLTIP_MALL_ITEMBONUS,
			item.APPLY_MALL_GOLDBONUS : localeInfo.TOOLTIP_MALL_GOLDBONUS,
			item.APPLY_SKILL_DAMAGE_BONUS : localeInfo.TOOLTIP_SKILL_DAMAGE_BONUS,
			item.APPLY_NORMAL_HIT_DAMAGE_BONUS : localeInfo.TOOLTIP_NORMAL_HIT_DAMAGE_BONUS,
			item.APPLY_SKILL_DEFEND_BONUS : localeInfo.TOOLTIP_SKILL_DEFEND_BONUS,
			item.APPLY_NORMAL_HIT_DEFEND_BONUS : localeInfo.TOOLTIP_NORMAL_HIT_DEFEND_BONUS,
			item.APPLY_PC_BANG_EXP_BONUS : localeInfo.TOOLTIP_MALL_EXPBONUS_P_STATIC,
			item.APPLY_PC_BANG_DROP_BONUS : localeInfo.TOOLTIP_MALL_ITEMBONUS_P_STATIC,
			item.APPLY_RESIST_WARRIOR : localeInfo.TOOLTIP_APPLY_RESIST_WARRIOR,
			item.APPLY_RESIST_ASSASSIN : localeInfo.TOOLTIP_APPLY_RESIST_ASSASSIN,
			item.APPLY_RESIST_SURA : localeInfo.TOOLTIP_APPLY_RESIST_SURA,
			item.APPLY_RESIST_SHAMAN : localeInfo.TOOLTIP_APPLY_RESIST_SHAMAN,
			item.APPLY_MAX_HP_PCT : localeInfo.TOOLTIP_APPLY_MAX_HP_PCT,
			item.APPLY_MAX_SP_PCT : localeInfo.TOOLTIP_APPLY_MAX_SP_PCT,
			item.APPLY_ENERGY : localeInfo.TOOLTIP_ENERGY,
			item.APPLY_COSTUME_ATTR_BONUS : localeInfo.TOOLTIP_COSTUME_ATTR_BONUS,

			item.APPLY_MAGIC_ATTBONUS_PER : localeInfo.TOOLTIP_MAGIC_ATTBONUS_PER,
			item.APPLY_MELEE_MAGIC_ATTBONUS_PER : localeInfo.TOOLTIP_MELEE_MAGIC_ATTBONUS_PER,
			item.APPLY_RESIST_ICE : localeInfo.TOOLTIP_RESIST_ICE,
			item.APPLY_RESIST_EARTH : localeInfo.TOOLTIP_RESIST_EARTH,
			item.APPLY_RESIST_DARK : localeInfo.TOOLTIP_RESIST_DARK,
			item.APPLY_ANTI_CRITICAL_PCT : localeInfo.TOOLTIP_ANTI_CRITICAL_PCT,
			item.APPLY_ANTI_PENETRATE_PCT : localeInfo.TOOLTIP_ANTI_PENETRATE_PCT,

			item.APPLY_ATTBONUS_WOLFMAN : localeInfo.TOOLTIP_APPLY_ATTBONUS_WOLFMAN,
			item.APPLY_RESIST_WOLFMAN : localeInfo.TOOLTIP_APPLY_RESIST_WOLFMAN,
			item.APPLY_RESIST_CLAW : localeInfo.TOOLTIP_APPLY_RESIST_CLAW,
			#item.APPLY_ACCEDRAIN_RATE : localeInfo.TOOLTIP_APPLY_ACCEDRAIN_RATE,
		}
	else:
		AFFECT_DICT = {
			item.APPLY_MAX_HP : localeInfo.TOOLTIP_MAX_HP,
			item.APPLY_MAX_SP : localeInfo.TOOLTIP_MAX_SP,
			item.APPLY_CON : localeInfo.TOOLTIP_CON,
			item.APPLY_INT : localeInfo.TOOLTIP_INT,
			item.APPLY_STR : localeInfo.TOOLTIP_STR,
			item.APPLY_DEX : localeInfo.TOOLTIP_DEX,
			item.APPLY_ATT_SPEED : localeInfo.TOOLTIP_ATT_SPEED,
			item.APPLY_MOV_SPEED : localeInfo.TOOLTIP_MOV_SPEED,
			item.APPLY_CAST_SPEED : localeInfo.TOOLTIP_CAST_SPEED,
			item.APPLY_HP_REGEN : localeInfo.TOOLTIP_HP_REGEN,
			item.APPLY_SP_REGEN : localeInfo.TOOLTIP_SP_REGEN,
			item.APPLY_POISON_PCT : localeInfo.TOOLTIP_APPLY_POISON_PCT,
			item.APPLY_STUN_PCT : localeInfo.TOOLTIP_APPLY_STUN_PCT,
			item.APPLY_SLOW_PCT : localeInfo.TOOLTIP_APPLY_SLOW_PCT,
			item.APPLY_CRITICAL_PCT : localeInfo.TOOLTIP_APPLY_CRITICAL_PCT,
			item.APPLY_PENETRATE_PCT : localeInfo.TOOLTIP_APPLY_PENETRATE_PCT,

			item.APPLY_ATTBONUS_WARRIOR : localeInfo.TOOLTIP_APPLY_ATTBONUS_WARRIOR,
			item.APPLY_ATTBONUS_ASSASSIN : localeInfo.TOOLTIP_APPLY_ATTBONUS_ASSASSIN,
			item.APPLY_ATTBONUS_SURA : localeInfo.TOOLTIP_APPLY_ATTBONUS_SURA,
			item.APPLY_ATTBONUS_SHAMAN : localeInfo.TOOLTIP_APPLY_ATTBONUS_SHAMAN,
			item.APPLY_ATTBONUS_MONSTER : localeInfo.TOOLTIP_APPLY_ATTBONUS_MONSTER,

			item.APPLY_ATTBONUS_HUMAN : localeInfo.TOOLTIP_APPLY_ATTBONUS_HUMAN,
			item.APPLY_ATTBONUS_ANIMAL : localeInfo.TOOLTIP_APPLY_ATTBONUS_ANIMAL,
			item.APPLY_ATTBONUS_ORC : localeInfo.TOOLTIP_APPLY_ATTBONUS_ORC,
			item.APPLY_ATTBONUS_MILGYO : localeInfo.TOOLTIP_APPLY_ATTBONUS_MILGYO,
			item.APPLY_ATTBONUS_UNDEAD : localeInfo.TOOLTIP_APPLY_ATTBONUS_UNDEAD,
			item.APPLY_ATTBONUS_DEVIL : localeInfo.TOOLTIP_APPLY_ATTBONUS_DEVIL,
			item.APPLY_STEAL_HP : localeInfo.TOOLTIP_APPLY_STEAL_HP,
			item.APPLY_STEAL_SP : localeInfo.TOOLTIP_APPLY_STEAL_SP,
			item.APPLY_MANA_BURN_PCT : localeInfo.TOOLTIP_APPLY_MANA_BURN_PCT,
			item.APPLY_DAMAGE_SP_RECOVER : localeInfo.TOOLTIP_APPLY_DAMAGE_SP_RECOVER,
			item.APPLY_BLOCK : localeInfo.TOOLTIP_APPLY_BLOCK,
			item.APPLY_DODGE : localeInfo.TOOLTIP_APPLY_DODGE,
			item.APPLY_RESIST_SWORD : localeInfo.TOOLTIP_APPLY_RESIST_SWORD,
			item.APPLY_RESIST_TWOHAND : localeInfo.TOOLTIP_APPLY_RESIST_TWOHAND,
			item.APPLY_RESIST_DAGGER : localeInfo.TOOLTIP_APPLY_RESIST_DAGGER,
			item.APPLY_RESIST_BELL : localeInfo.TOOLTIP_APPLY_RESIST_BELL,
			item.APPLY_RESIST_FAN : localeInfo.TOOLTIP_APPLY_RESIST_FAN,
			item.APPLY_RESIST_BOW : localeInfo.TOOLTIP_RESIST_BOW,
			item.APPLY_RESIST_FIRE : localeInfo.TOOLTIP_RESIST_FIRE,
			item.APPLY_RESIST_ELEC : localeInfo.TOOLTIP_RESIST_ELEC,
			item.APPLY_RESIST_MAGIC : localeInfo.TOOLTIP_RESIST_MAGIC,
			item.APPLY_RESIST_WIND : localeInfo.TOOLTIP_APPLY_RESIST_WIND,
			item.APPLY_REFLECT_MELEE : localeInfo.TOOLTIP_APPLY_REFLECT_MELEE,
			item.APPLY_REFLECT_CURSE : localeInfo.TOOLTIP_APPLY_REFLECT_CURSE,
			item.APPLY_POISON_REDUCE : localeInfo.TOOLTIP_APPLY_POISON_REDUCE,
			item.APPLY_KILL_SP_RECOVER : localeInfo.TOOLTIP_APPLY_KILL_SP_RECOVER,
			item.APPLY_EXP_DOUBLE_BONUS : localeInfo.TOOLTIP_APPLY_EXP_DOUBLE_BONUS,
			item.APPLY_GOLD_DOUBLE_BONUS : localeInfo.TOOLTIP_APPLY_GOLD_DOUBLE_BONUS,
			item.APPLY_ITEM_DROP_BONUS : localeInfo.TOOLTIP_APPLY_ITEM_DROP_BONUS,
			item.APPLY_POTION_BONUS : localeInfo.TOOLTIP_APPLY_POTION_BONUS,
			item.APPLY_KILL_HP_RECOVER : localeInfo.TOOLTIP_APPLY_KILL_HP_RECOVER,
			item.APPLY_IMMUNE_STUN : localeInfo.TOOLTIP_APPLY_IMMUNE_STUN,
			item.APPLY_IMMUNE_SLOW : localeInfo.TOOLTIP_APPLY_IMMUNE_SLOW,
			item.APPLY_IMMUNE_FALL : localeInfo.TOOLTIP_APPLY_IMMUNE_FALL,
			item.APPLY_BOW_DISTANCE : localeInfo.TOOLTIP_BOW_DISTANCE,
			item.APPLY_DEF_GRADE_BONUS : localeInfo.TOOLTIP_DEF_GRADE,
			# Belt pool rolls APPLY_DEF_GRADE (83), a different apply from bonus 54.
			83 : localeInfo.TOOLTIP_DEF_GRADE,
			item.APPLY_ATT_GRADE_BONUS : localeInfo.TOOLTIP_ATT_GRADE,
			item.APPLY_MAGIC_ATT_GRADE : localeInfo.TOOLTIP_MAGIC_ATT_GRADE,
			item.APPLY_MAGIC_DEF_GRADE : localeInfo.TOOLTIP_MAGIC_DEF_GRADE,
			item.APPLY_MAX_STAMINA : localeInfo.TOOLTIP_MAX_STAMINA,
			item.APPLY_MALL_ATTBONUS : localeInfo.TOOLTIP_MALL_ATTBONUS,
			item.APPLY_MALL_DEFBONUS : localeInfo.TOOLTIP_MALL_DEFBONUS,
			item.APPLY_MALL_EXPBONUS : localeInfo.TOOLTIP_MALL_EXPBONUS,
			item.APPLY_MALL_ITEMBONUS : localeInfo.TOOLTIP_MALL_ITEMBONUS,
			item.APPLY_MALL_GOLDBONUS : localeInfo.TOOLTIP_MALL_GOLDBONUS,
			item.APPLY_SKILL_DAMAGE_BONUS : localeInfo.TOOLTIP_SKILL_DAMAGE_BONUS,
			item.APPLY_NORMAL_HIT_DAMAGE_BONUS : localeInfo.TOOLTIP_NORMAL_HIT_DAMAGE_BONUS,
			item.APPLY_SKILL_DEFEND_BONUS : localeInfo.TOOLTIP_SKILL_DEFEND_BONUS,
			item.APPLY_NORMAL_HIT_DEFEND_BONUS : localeInfo.TOOLTIP_NORMAL_HIT_DEFEND_BONUS,
			item.APPLY_PC_BANG_EXP_BONUS : localeInfo.TOOLTIP_MALL_EXPBONUS_P_STATIC,
			item.APPLY_PC_BANG_DROP_BONUS : localeInfo.TOOLTIP_MALL_ITEMBONUS_P_STATIC,
			item.APPLY_RESIST_WARRIOR : localeInfo.TOOLTIP_APPLY_RESIST_WARRIOR,
			item.APPLY_RESIST_ASSASSIN : localeInfo.TOOLTIP_APPLY_RESIST_ASSASSIN,
			item.APPLY_RESIST_SURA : localeInfo.TOOLTIP_APPLY_RESIST_SURA,
			item.APPLY_RESIST_SHAMAN : localeInfo.TOOLTIP_APPLY_RESIST_SHAMAN,
			item.APPLY_MAX_HP_PCT : localeInfo.TOOLTIP_APPLY_MAX_HP_PCT,
			item.APPLY_MAX_SP_PCT : localeInfo.TOOLTIP_APPLY_MAX_SP_PCT,
			item.APPLY_ENERGY : localeInfo.TOOLTIP_ENERGY,
			item.APPLY_COSTUME_ATTR_BONUS : localeInfo.TOOLTIP_COSTUME_ATTR_BONUS,

			item.APPLY_MAGIC_ATTBONUS_PER : localeInfo.TOOLTIP_MAGIC_ATTBONUS_PER,
			item.APPLY_MELEE_MAGIC_ATTBONUS_PER : localeInfo.TOOLTIP_MELEE_MAGIC_ATTBONUS_PER,
			item.APPLY_RESIST_ICE : localeInfo.TOOLTIP_RESIST_ICE,
			item.APPLY_RESIST_EARTH : localeInfo.TOOLTIP_RESIST_EARTH,
			item.APPLY_RESIST_DARK : localeInfo.TOOLTIP_RESIST_DARK,
			item.APPLY_ANTI_CRITICAL_PCT : localeInfo.TOOLTIP_ANTI_CRITICAL_PCT,
			item.APPLY_ANTI_PENETRATE_PCT : localeInfo.TOOLTIP_ANTI_PENETRATE_PCT,
		}

	guardianChanceApply = getattr(item, "APPLY_RARITY_GUARDIAN_CHANCE", None)
	if guardianChanceApply is not None:
		AFFECT_DICT[guardianChanceApply] = localeInfo.TOOLTIP_APPLY_RARITY_GUARDIAN_CHANCE
	AFFECT_DICT[172] = localeInfo.TOOLTIP_APPLY_RESIST_ALL
	AFFECT_DICT[item.APPLY_RESIST_MONSTER] = localeInfo.TOOLTIP_APPLY_RESIST_MONSTER
	AFFECT_DICT[item.APPLY_RESIST_BOSS] = localeInfo.TOOLTIP_APPLY_RESIST_BOSS
	AFFECT_DICT[item.APPLY_PVM_ATTBONUS] = localeInfo.TOOLTIP_APPLY_PVM_ATTBONUS
	AFFECT_DICT[item.APPLY_ATTBONUS_ORDINARY_MONSTER] = localeInfo.TOOLTIP_APPLY_ATTBONUS_ORDINARY_MONSTER
	AFFECT_DICT[item.APPLY_DEFENSE_BREAKTHROUGH] = localeInfo.TOOLTIP_APPLY_DEFENSE_BREAKTHROUGH
	AFFECT_DICT[item.APPLY_BLOCK_PENETRATION] = localeInfo.TOOLTIP_APPLY_BLOCK_PENETRATION
	AFFECT_DICT[item.APPLY_ALL_ATTRIBUTES] = localeInfo.TOOLTIP_APPLY_ALL_ATTRIBUTES
	AFFECT_DICT[getattr(item, "APPLY_ENCHANT_ALL", 134)] = localeInfo.TOOLTIP_APPLY_ENCHANT_ALL
	AFFECT_DICT[getattr(item, "APPLY_CRITICAL_DAMAGE_PVM", 171)] = localeInfo.TOOLTIP_APPLY_CRITICAL_DAMAGE_PVM
	AFFECT_DICT[getattr(item, "APPLY_WEAPON_BASE_PERCENT", 173)] = localeInfo.TOOLTIP_APPLY_WEAPON_BASE_PERCENT
	# Legacy items must stay readable even though new Lycan characters and rolls
	# are disabled server-side.
	AFFECT_DICT[item.APPLY_BLEEDING_REDUCE] = localeInfo.TOOLTIP_APPLY_BLEEDING_REDUCE
	AFFECT_DICT[item.APPLY_BLEEDING_PCT] = localeInfo.TOOLTIP_APPLY_BLEEDING_PCT
	AFFECT_DICT[item.APPLY_ATTBONUS_WOLFMAN] = localeInfo.TOOLTIP_APPLY_ATTBONUS_WOLFMAN
	AFFECT_DICT[item.APPLY_RESIST_WOLFMAN] = localeInfo.TOOLTIP_APPLY_RESIST_WOLFMAN
	AFFECT_DICT[item.APPLY_RESIST_CLAW] = localeInfo.TOOLTIP_APPLY_RESIST_CLAW
	# Compatibility for the historic SQL enum ordinal that was persisted as 133.
	AFFECT_DICT[133] = localeInfo.TOOLTIP_APPLY_BLOCK_PENETRATION

	if app.ENABLE_MAGIC_REDUCTION:
		AFFECT_DICT[item.APPLY_RESIST_MAGIC_REDUCTION] = localeInfo.TOOLTIP_RESIST_MAGIC_REDUCTION

	# AFFECT_DICT[item.APPLY_ACCEDRAIN_RATE] = localeInfo.TOOLTIP_APPLY_ACCEDRAIN_RATE

	if app.ENABLE_ELEMENT_ADD:
		AFFECT_DICT[item.APPLY_ENCHANT_ELEC] = localeInfo.TOOLTIP_APPLY_ENCHANT_ELECT
		AFFECT_DICT[item.APPLY_ENCHANT_FIRE] = localeInfo.TOOLTIP_APPLY_ENCHANT_FIRE
		AFFECT_DICT[item.APPLY_ENCHANT_ICE] = localeInfo.TOOLTIP_APPLY_ENCHANT_ICE
		AFFECT_DICT[item.APPLY_ENCHANT_WIND] = localeInfo.TOOLTIP_APPLY_ENCHANT_WIND
		AFFECT_DICT[item.APPLY_ENCHANT_EARTH] = localeInfo.TOOLTIP_APPLY_ENCHANT_EARTH
		AFFECT_DICT[item.APPLY_ENCHANT_DARK] = localeInfo.TOOLTIP_APPLY_ENCHANT_DARK
		AFFECT_DICT[item.APPLY_ATTBONUS_CZ] = localeInfo.TOOLTIP_APPLY_ATTBONUS_CZ
		AFFECT_DICT[item.APPLY_ATTBONUS_INSECT] = localeInfo.TOOLTIP_APPLY_ATTBONUS_INSECT
		AFFECT_DICT[item.APPLY_ATTBONUS_DESERT] = localeInfo.TOOLTIP_APPLY_ATTBONUS_DESERT

		AFFECT_DICT[item.APPLY_RESIST_SWORD_REDUCTION] = localeInfo.TOOLTIP_APPLY_ATTBONUS_SWORD
		AFFECT_DICT[item.APPLY_RESIST_TWOHAND_REDUCTION]= localeInfo.TOOLTIP_APPLY_ATTBONUS_TWOHAND
		AFFECT_DICT[item.APPLY_RESIST_DAGGER_REDUCTION] = localeInfo.TOOLTIP_APPLY_ATTBONUS_DAGGER
		AFFECT_DICT[item.APPLY_RESIST_BELL_REDUCTION] = localeInfo.TOOLTIP_APPLY_ATTBONUS_BELL
		AFFECT_DICT[item.APPLY_RESIST_FAN_REDUCTION] = localeInfo.TOOLTIP_APPLY_ATTBONUS_FAN
		AFFECT_DICT[item.APPLY_RESIST_BOW_REDUCTION] = localeInfo.TOOLTIP_APPLY_ATTBONUS_BOW
		AFFECT_DICT[item.APPLY_RESIST_CLAW_REDUCTION] = localeInfo.TOOLTIP_APPLY_ATTBONUS_CLAW
		AFFECT_DICT[item.APPLY_RESIST_HUMAN] = localeInfo.TOOLTIP_APPLY_RESIST_HUMAN

	if app.ENABLE_BOSS_AND_METIN_BONUS:
		AFFECT_DICT[item.APPLY_ATTBONUS_METIN] = localeInfo.TOOLTIP_APPLY_ATTBONUS_METIN
		AFFECT_DICT[item.APPLY_ATTBONUS_BOSS] = localeInfo.TOOLTIP_APPLY_ATTBONUS_BOSS

	if app.ENABLE_CONQUEROR_LEVEL:
		AFFECT_DICT[item.APPLY_SUNGMA_STR] = localeInfo.TOOLTIP_SUNGMA_STR
		AFFECT_DICT[item.APPLY_SUNGMA_HP] = localeInfo.TOOLTIP_SUNGMA_HP
		AFFECT_DICT[item.APPLY_SUNGMA_MOVE] = localeInfo.TOOLTIP_SUNGMA_MOVE
		AFFECT_DICT[item.APPLY_SUNGMA_IMMUNE] = localeInfo.TOOLTIP_SUNGMA_IMMUNE

	AFFECT_DICT[item.APPLY_RESIST_NORMAL_DAMAGE] = lambda value: u"%s +%d%%" % (localeInfo.TOOLTIP_SKILL_AFFECT_RESIST_NORMAL.rstrip(":"), value)

	POINT_DICT = {item.GetApplyPoint(affect): name for affect, name in AFFECT_DICT.items()}
	# Unsupported APPLY aliases map to POINT_NONE, which carries no stat bonus.
	POINT_DICT.pop(0, None)

	ATTRIBUTE_NEED_WIDTH = {
		23 : 230,
		24 : 230,
		25 : 230,
		26 : 220,
		27 : 210,

		35 : 210,
		36 : 210,
		37 : 210,
		38 : 210,
		39 : 210,
		40 : 210,
		41 : 210,

		42 : 220,
		43 : 230,
		45 : 230,
	}

	if not app.DISABLE_WOLFMAN_CREATION:
		ANTI_FLAG_DICT = {
			0 : item.ITEM_ANTIFLAG_WARRIOR,
			1 : item.ITEM_ANTIFLAG_ASSASSIN,
			2 : item.ITEM_ANTIFLAG_SURA,
			3 : item.ITEM_ANTIFLAG_SHAMAN,
			4 : item.ITEM_ANTIFLAG_WOLFMAN,
		}
	else:
		ANTI_FLAG_DICT = {
			0 : item.ITEM_ANTIFLAG_WARRIOR,
			1 : item.ITEM_ANTIFLAG_ASSASSIN,
			2 : item.ITEM_ANTIFLAG_SURA,
			3 : item.ITEM_ANTIFLAG_SHAMAN,
		}
	FONT_COLOR = grp.GenerateColor(0.7607, 0.7607, 0.7607, 1.0)

	if app.ENABLE_REFINE_ELEMENT_SYSTEM:
		REFINE_ELEMENT_BONUS_COLOR = -7751539

		REFINE_ELEMENT_COLOR_DICT = {
			item.APPLY_ENCHANT_ELEC : 4280530920,
			item.APPLY_ENCHANT_FIRE : 4292692027,
			item.APPLY_ENCHANT_ICE : 4282215647,
			item.APPLY_ENCHANT_WIND : 4281847585,
			item.APPLY_ENCHANT_EARTH : 4294232596,
			item.APPLY_ENCHANT_DARK : 4290195180
		}

		REFINE_ELEMENT_INDEX_APPLY_TYPE = 0
		REFINE_ELEMENT_INDEX_GRADE = 1
		REFINE_ELEMENT_INDEX_VALUE = 2
		REFINE_ELEMENT_INDEX_BONUS = 3
		REFINE_ELEMENT_INDEX_MAX = item.REFINE_ELEMENT_MAX

		REFINE_ELEMENT_TITLE_TEXT_GAP = 10

	def __init__(self, *args, **kwargs):
		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.mountPreviewIndex = None
			self.mountPreviewView = None
			self.mountPreviewRace = 0
			self.costumePreviewIndex = None
			self.costumePreviewView = None
			self.costumePreviewPlaceholder = None
			self.costumePreviewDeadline = 0.0
			self.costumePreviewClock = 0.0
		self.costumePreviewVnum = 0
		self.costumeVoucherOffer = 0
		ToolTip.__init__(self, *args, **kwargs)
		self.itemVnum = 0
		self.metinSlot = []
		self.isShopItem = False

		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			self.isRefineElementItem = False

		if app.ENABLE_DS_SET:
			self.interface = None

		self.attrSlot = []
		self.rarityGrade = 0
		self.weaponBasePercent = 0
		self.bonusLabels = {}
		self.bonusRows = []
		self.bonusLegend = None
		self.bonusVersion = None

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.savedItemVnum = 0

		# 아이템 툴팁을 표시할 때 현재 캐릭터가 착용할 수 없는 아이템이라면 강제로 Disable Color로 설정 (이미 그렇게 작동하고 있으나 꺼야 할 필요가 있어서)
		self.bCannotUseItemForceSetDisableColor = True 

	def BindInterfaceClass(self, interface):
		self.interface = interface	

	def __del__(self):
		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.__RemoveMountPreview()
			self.__RemoveCostumePreview()
		ToolTip.__del__(self)
		self.metinSlot = None
		self.attrSlot = None

	if app.ENABLE_DS_SET or app.ENABLE_RENDER_TARGET_PREVIEW:
		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

	def SetCannotUseItemForceSetDisableColor(self, enable):
		self.bCannotUseItemForceSetDisableColor = enable

	def CanEquip(self):
		if not item.IsEquipmentVID(self.itemVnum):
			return True

		race = player.GetRace()
		job = chr.RaceToJob(race)
		if job not in self.ANTI_FLAG_DICT:
			return False

		if item.IsAntiFlag(self.ANTI_FLAG_DICT[job]):
			return False

		sex = chr.RaceToSex(race)

		MALE = 1
		FEMALE = 0

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE) and sex == MALE:
			return False

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE) and sex == FEMALE:
			return False

		for i in range(item.LIMIT_MAX_NUM):
			(limitType, limitValue) = item.GetLimit(i)

			if item.LIMIT_LEVEL == limitType:
				if player.GetStatus(player.LEVEL) < limitValue:
					return False
			"""
			elif item.LIMIT_STR == limitType:
				if player.GetStatus(player.ST) < limitValue:
					return False
			elif item.LIMIT_DEX == limitType:
				if player.GetStatus(player.DX) < limitValue:
					return False
			elif item.LIMIT_INT == limitType:
				if player.GetStatus(player.IQ) < limitValue:
					return False
			elif item.LIMIT_CON == limitType:
				if player.GetStatus(player.HT) < limitValue:
					return False
			"""

		return True

	def __AlignBonusPair(self, line):
		suffix = getattr(line, "bonusSuffixLine", None)
		if suffix is None:
			return
		w = line.GetTextSize()[0]
		w2 = suffix.GetTextSize()[0]
		x, y = line.GetLocalPosition()
		if line.bonusCenterAlign:
			direction = -1 if localeInfo.IsARABIC() else 1
			line.SetPosition(self.toolTipWidth // 2 - direction * (w2 // 2), y)
			suffix.SetPosition(direction * (w // 2), 0)
		else:
			suffix.SetPosition(w, 0)

	def __GrowBonusWidth(self, textLine):
		suffix = getattr(textLine, "bonusSuffixLine", None)
		textWidth = textLine.GetTextSize()[0] + (suffix.GetTextSize()[0] if suffix else 0)
		width = max(self.toolTipWidth, textWidth + 24)
		self.__AlignBonusPair(textLine)
		if width == self.toolTipWidth:
			return
		oldCenter = self.toolTipWidth // 2
		self.toolTipWidth = width
		for child in self.childrenList:
			if getattr(child, "bonusSuffixLine", None) is not None:
				self.__AlignBonusPair(child)
			elif isinstance(child, ui.TextLine):
				x, y = child.GetLocalPosition()
				if x == oldCenter:
					child.SetPosition(width // 2, y)
		self.ResizeToolTip()

	def __AppendBonusLine(self, text, color, centerAlign):
		line = ToolTip.AppendTextLine(self, text, color, centerAlign)
		bonus = getattr(self, "bonusLabels", {}).get(text)
		if bonus is not None:
			self.bonusRows.append((line, bonus[0], bonus[1]))
			self.__GrowBonusWidth(line)
		return line

	if app.ENABLE_DS_SET:
		def AppendTwoColorTextLine(self, text, color, text2, color2 = ToolTip.TEXTLINE_2ND_COLOR_DEFAULT, centerAlign = True):
			line = ToolTip.AppendTwoColorTextLine(self, text, color, text2, color2, centerAlign)
			bonus = self.bonusLabels.get(text)
			if bonus is not None:
				line.bonusSuffixLine = self.childrenList[-1]
				line.bonusCenterAlign = centerAlign
				self.bonusRows.append((line, bonus[0], bonus[1]))
				self.__GrowBonusWidth(line)
			return line

	def ShowToolTip(self):
		if self.bonusRows and self.bonusLegend is None:
			self.bonusLegend = ToolTip.AppendTextLine(self,
				itembonuspresentation.TotalsLegend(app.GetLocalePath().endswith("/cz")),
				self.NORMAL_COLOR)
			self.__GrowBonusWidth(self.bonusLegend)
		ToolTip.ShowToolTip(self)

	def __RefreshBonusTotals(self):
		if not self.IsShow() or not self.bonusRows:
			return
		itembonuspresentation.totals.Request()
		version = itembonuspresentation.totals.Version()
		if self.bonusVersion == version:
			return
		self.bonusVersion = version
		for line, text, kind in self.bonusRows:
			if line not in self.childrenList:
				continue
			line.SetText(itembonuspresentation.totals.Format(text, kind))
			self.__GrowBonusWidth(line)

	def AppendTextLineAcce(self, text, color = FONT_COLOR, centerAlign = True):
		return self.__AppendBonusLine(text, color, centerAlign)

	def AppendTextLine(self, text, color = FONT_COLOR, centerAlign = True):
		if osfInfo.ENABLE_ITEM_HIGHLIGHT_RENEWAL == False:
			if not self.CanEquip() and self.bCannotUseItemForceSetDisableColor:
				color = self.DISABLE_COLOR

		return self.__AppendBonusLine(text, color, centerAlign)

	def AppendTextLineDontCheckColor(self, text, color = FONT_COLOR, centerAlign = True):
		return self.__AppendBonusLine(text, color, centerAlign)

	def ClearToolTip(self):
		self.inventoryRefreshSnapshot = None
		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.__RemoveMountPreview()
			self.mountPreviewRace = 0
			self.__RemoveCostumePreview()
		self.costumePreviewVnum = 0
		self.costumeVoucherOffer = 0
		self.isShopItem = False
		self.rarityGrade = 0
		self.weaponBasePercent = 0
		self.bonusLabels = {}
		self.bonusRows = []
		self.bonusLegend = None
		self.bonusVersion = None
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			self.isRefineElementItem = False
		self.toolTipWidth = self.TOOL_TIP_WIDTH
		ToolTip.ClearToolTip(self)

	def HideToolTip(self):
		self.inventoryRefreshSnapshot = None
		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.__RemoveMountPreview()
			self.__RemoveCostumePreview()
		ToolTip.HideToolTip(self)

	if app.ENABLE_RENDER_TARGET_PREVIEW:
		def __RemoveMountPreview(self):
			index = self.mountPreviewIndex
			view = self.mountPreviewView
			self.mountPreviewIndex = None
			self.mountPreviewView = None
			if view:
				try:
					view.Hide()
				except (AttributeError, RuntimeError, TypeError, ValueError):
					pass
				try:
					self.childrenList.remove(view)
				except (AttributeError, ValueError):
					pass
			if index is None:
				return
			try:
				WikiRenderTarget.SetVisibility(index, False)
			except (AttributeError, RuntimeError, TypeError, ValueError):
				pass
			try:
				WikiRenderTarget.ResetModel(index)
			except (AttributeError, RuntimeError, TypeError, ValueError):
				pass
			try:
				WikiRenderTarget.Remove(index)
			except (AttributeError, RuntimeError, TypeError, ValueError):
				pass

		def __AppendMountPreview(self):
			if self.mountPreviewRace <= 0:
				return False
			try:
				index = int(WikiRenderTarget.GetFreeIndex(86, 1000000))
				if index < 1:
					raise RuntimeError("no free mount tooltip render target")
				self.mountPreviewIndex = index
				view = ui.WikiRenderTargetUi()
				view.SetParent(self)
				self.mountPreviewView = view
				view.AddFlag("not_pick")
				view.SetPosition(
					(self.toolTipWidth - self.MOUNT_PREVIEW_WIDTH) // 2,
					self.toolTipHeight + self.MOUNT_PREVIEW_MARGIN // 2,
				)
				view.SetSize(self.MOUNT_PREVIEW_WIDTH, self.MOUNT_PREVIEW_HEIGHT)
				view.SetRenderTarget(index)
				WikiRenderTarget.SetBackground(
					index, "d:/ymir work/ui/render_target/render_target_bg.dds"
				)
				WikiRenderTarget.SetRotation(index, True)
				WikiRenderTarget.SelectModel(index, self.mountPreviewRace)
				WikiRenderTarget.SetVisibility(index, True)
				view.Show()
				self.childrenList.append(view)
				self.toolTipHeight += (
					self.MOUNT_PREVIEW_HEIGHT + self.MOUNT_PREVIEW_MARGIN
				)
				self.ResizeToolTip()
				return True
			except (AttributeError, RuntimeError, TypeError, ValueError):
				self.__RemoveMountPreview()
				return False

		def __RemoveCostumePreview(self):
			index = self.costumePreviewIndex
			self.costumePreviewIndex = None
			self.costumePreviewDeadline = 0.0
			self.costumePreviewClock = 0.0
			# Hide and drop the view before its target disappears: a visible
			# render-target window without a target logs on every frame.
			for attribute in ("costumePreviewView", "costumePreviewPlaceholder"):
				child = getattr(self, attribute, None)
				setattr(self, attribute, None)
				if child is None:
					continue
				try:
					child.Hide()
				except (AttributeError, RuntimeError, TypeError, ValueError):
					pass
				try:
					self.childrenList.remove(child)
				except (AttributeError, ValueError):
					pass
			if index is None:
				return
			try:
				renderTarget.SetVisibility(index, False)
			except (AttributeError, RuntimeError, TypeError, ValueError):
				pass
			try:
				# Generic removal from the shared render-target manager; it
				# releases player-type targets as well as wiki ones.
				WikiRenderTarget.Remove(index)
			except (AttributeError, RuntimeError, TypeError, ValueError):
				pass

		def __CostumePreviewPlan(self, costumeVnum):
			"""(race, part, hairIndex) for the embedded preview, or None.

			The preview uses a player-type render target (as uirendertargetview
			does): Wiki render targets create NPC actors and the released
			executable ignores SetHair for them, which left the head without hair.
			A hairstyle costume replaces the hair; other costumes keep the hair
			costume the character wears, or the race's default hair (index 0).
			"""
			try:
				playerRace = player.GetRace()
			except (AttributeError, RuntimeError, TypeError, ValueError):
				playerRace = None
			wornHair = iscostumevoucher.WornHairIndex(player, item)
			item.SelectItem(costumeVnum)
			if item.GetItemType() != item.ITEM_TYPE_COSTUME:
				return None
			subType = item.GetItemSubType()
			if subType == item.COSTUME_TYPE_BODY:
				part = "armor"
			elif subType == item.COSTUME_TYPE_HAIR:
				part = "hair"
			elif subType == getattr(item, "COSTUME_TYPE_WEAPON", -1):
				part = "weapon"
			else:
				return None
			jobFlags = (item.ITEM_ANTIFLAG_WARRIOR, item.ITEM_ANTIFLAG_ASSASSIN,
				item.ITEM_ANTIFLAG_SURA, item.ITEM_ANTIFLAG_SHAMAN)
			jobs = [job for job, flag in enumerate(jobFlags) if not item.IsAntiFlag(flag)]
			allowMale = not item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE)
			allowFemale = not item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE)
			race = iscostumevoucher.PreviewRace(playerRace, jobs, allowMale, allowFemale)
			if race is None:
				# No usable character race (e.g. before login): default model.
				race = iscostumevoucher.JOB_SEX_RACE[(jobs[0] if jobs else 0, not allowMale)]
			if part == "hair":
				hairIndex = max(0, int(item.GetValue(3)))
			else:
				hairIndex = iscostumevoucher.PreviewHairIndex(race, playerRace, wornHair)
			return race, part, hairIndex

		def __AppendCostumePreview(self):
			costumeVnum = self.costumePreviewVnum
			if costumeVnum <= 0 or self.costumePreviewIndex is not None:
				return False
			plan = self.__CostumePreviewPlan(costumeVnum)
			item.SelectItem(self.itemVnum)
			if plan is None:
				return False
			race, part, hairIndex = plan
			try:
				# The window API stores the index as one byte.
				index = int(WikiRenderTarget.GetFreeIndex(86, 256))
				if index < 1:
					raise RuntimeError("no free costume tooltip render target")
				self.costumePreviewIndex = index
				left = (self.toolTipWidth - self.COSTUME_PREVIEW_WIDTH) // 2
				top = self.toolTipHeight + self.COSTUME_PREVIEW_MARGIN // 2
				view = ui.RenderTarget()
				view.SetParent(self)
				self.costumePreviewView = view
				view.AddFlag("not_pick")
				view.SetPosition(left, top)
				view.SetSize(self.COSTUME_PREVIEW_WIDTH, self.COSTUME_PREVIEW_HEIGHT)
				view.SetRenderTarget(index)
				renderTarget.SetBackground(
					index, "d:/ymir work/ui/render_target/render_target_bg.dds"
				)
				renderTarget.SelectModel(index, race)
				# Parts attach only while the target is visible.
				renderTarget.SetVisibility(index, True)
				if part == "armor":
					renderTarget.ChangeArmor(index, costumeVnum)
				elif part == "weapon":
					renderTarget.ChangeWeapon(index, costumeVnum)
				if hairIndex > 0:
					renderTarget.ChangeHair(index, hairIndex)
				# Keep the view hidden briefly so a quick hover never flashes a
				# half-loaded actor; player-type targets report no readiness.
				view.Hide()
				self.childrenList.append(view)
				placeholder = ui.TextLine()
				placeholder.SetParent(self)
				placeholder.SetFontName(self.defFontName)
				placeholder.SetHorizontalAlignCenter()
				placeholder.SetPosition(self.toolTipWidth // 2, top + self.COSTUME_PREVIEW_HEIGHT // 2 - 6)
				placeholder.SetText(getattr(localeInfo, "COSTUME_PREVIEW_LOADING", "..."))
				placeholder.SetPackedFontColor(self.NORMAL_COLOR)
				placeholder.Show()
				self.costumePreviewPlaceholder = placeholder
				self.childrenList.append(placeholder)
				now = app.GetTime()
				self.costumePreviewDeadline = now + self.COSTUME_PREVIEW_SETTLE_TIME
				self.costumePreviewClock = now
				self.toolTipHeight += (
					self.COSTUME_PREVIEW_HEIGHT + self.COSTUME_PREVIEW_MARGIN
				)
				self.ResizeToolTip()
				return True
			except (AttributeError, RuntimeError, TypeError, ValueError):
				self.__RemoveCostumePreview()
				return False

		def __RefreshCostumePreview(self):
			view = self.costumePreviewView
			index = self.costumePreviewIndex
			if not view or index is None:
				return
			now = app.GetTime()
			elapsed = max(0.0, min(0.1, now - self.costumePreviewClock))
			self.costumePreviewClock = now
			try:
				renderTarget.Rotate(index, self.COSTUME_PREVIEW_DEGREES_PER_SECOND * elapsed)
			except (AttributeError, RuntimeError, TypeError, ValueError):
				pass
			placeholder = self.costumePreviewPlaceholder
			if placeholder is None or now < self.costumePreviewDeadline:
				return
			view.Show()
			self.costumePreviewPlaceholder = None
			placeholder.Hide()
			try:
				self.childrenList.remove(placeholder)
			except ValueError:
				pass

	def __AppendInventoryShortcutHints(
		self, itemVnum, slotIndex, window_type, specialInventoryType
	):
		if window_type != player.INVENTORY:
			return
		if player.IsEquipmentSlot(slotIndex):
			return
		if specialInventoryType is not None and not (
			0 <= specialInventoryType <= 5 or specialInventoryType == 8
		):
			return

		item.SelectItem(itemVnum)
		itemType = item.GetItemType()
		itemSubType = item.GetItemSubType()
		itemCount = player.GetItemCount(window_type, slotIndex)
		isSpecial = specialInventoryType is not None
		rows = []

		if itemVnum in (80003, 80004, 80005, 80006, 80007):
			rows.append((
				None,
				"|Ikey/mouse_right|i - %s" % localeInfo.GOLD_BAR_REDEEM_KEEP_ONE,
			))

		canStack = item.IsFlag(item.ITEM_FLAG_STACKABLE) or 79700 <= itemVnum <= 79729
		if isSpecial:
			canStack = canStack and (0 <= specialInventoryType <= 4 or specialInventoryType == 8)
		if canStack:
			rows.append((
				inventoryshortcutpolicy.ACTION_STACK,
				"|Ikey/alt|i + |Ikey/shift|i + |Ikey/mouse_left|i - %s"
				% localeInfo.INVENTORY_SHORTCUT_STACK,
			))

		rows.append((
			inventoryshortcutpolicy.ACTION_LINK,
			"|Ikey/alt|i + |Ikey/mouse_left|i - %s"
			% localeInfo.INVENTORY_SHORTCUT_LINK,
		))

		splitText = None
		if not isSpecial and app.ENABLE_BUFF_SYSTEM:
			if itemType == item.ITEM_SHAMAN:
				splitText = localeInfo.SUPPORT_OPEN_GUI
		if not splitText and not isSpecial and app.ENABLE_GROWTH_PET_SYSTEM:
			if itemType == item.ITEM_TYPE_PET and itemSubType == item.PET_UPBRINGING:
				splitText = localeInfo.INVENTORY_SHORTCUT_OPEN_PET
		if not splitText and itemCount > 1 and specialInventoryType != 8:
			splitText = localeInfo.INVENTORY_SHORTCUT_SPLIT
		if splitText:
			rows.append((
				inventoryshortcutpolicy.ACTION_SPLIT,
				"|Ikey/shift|i + |Ikey/mouse_left|i - %s" % splitText,
			))

		if getattr(app, "ENABLE_VIRTUAL_MARKET", 0) and specialInventoryType != 8:
			rows.append((
				inventoryshortcutpolicy.ACTION_MARKET,
				"|Ikey/ctrl|i + |Ikey/mouse_left|i - %s"
				% localeInfo.INVENTORY_SHORTCUT_MARKET,
			))

		if app.ENABLE_WIKI:
			rows.append((
				None,
				"|Ikey/ctrl|i + |Ikey/mouse_right|i - %s"
				% localeInfo.WIKI_SEARCH_WINDOWS_KEY,
			))
		if app.ENABLE_SHOW_CHEST_DROP:
			if itemType in (item.ITEM_TYPE_GIFTBOX, item.ITEM_TYPE_GACHA,
					item.ITEM_TYPE_TREASURE_BOX):
				rows.append((
					None,
					"|Ikey/mouse_right|i - %s"
					% localeInfo.CHEST_DROP_PREVIEW,
				))

		if not rows:
			return
		self.AppendSpace(5)
		maxTextWidth = 0
		for rowIndex, (_action, text) in enumerate(rows):
			textLine = self.AppendTextLine(text, self.TITLE_COLOR)
			textWidth, _textHeight = textLine.GetTextSize()
			maxTextWidth = max(maxTextWidth, textWidth)
			if rowIndex + 1 < len(rows):
				self.AppendSpace(3)

		requiredWidth = maxTextWidth + 30
		if self.toolTipWidth < requiredWidth:
			self.toolTipWidth = requiredWidth
			self.AlignTextLineHorizonalCenter()

	if app.ENABLE_SLOT_TOOLTIP_INFO:
		def ResizeToolTipText(self, x, y):
			self.SetSize(x, y)

		def AutoAppendNewTextLine(self, text, color = FONT_COLOR, centerAlign = True):
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetFontName(self.defFontName)
			textLine.SetPackedFontColor(color)
			textLine.SetText(text)
			textLine.SetOutline()
			textLine.SetFeather(FALSE)
			textLine.Show()
			textLine.SetPosition(15, self.toolTipHeight)
			
			self.childrenList.append(textLine)
			(textWidth, textHeight) = textLine.GetTextSize()
			textWidth += 30
			textHeight += 10
			if self.toolTipWidth < textWidth:
				self.toolTipWidth = textWidth
			
			self.toolTipHeight += textHeight
			self.ResizeToolTipText(textWidth, self.toolTipHeight)
			return textLine

	def __InventoryRefreshSnapshot(self, slotIndex):
		window = player.INVENTORY
		vnum = player.GetItemIndex(window, slotIndex)
		if not vnum:
			return (0,)
		sockets = tuple(player.GetItemMetinSocket(window, slotIndex, i)
			for i in range(player.METIN_SOCKET_MAX_NUM))
		attrs = tuple(player.GetItemAttribute(window, slotIndex, i)
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM))
		metadataWindow = ResolveRarityInventoryWindow(window, slotIndex)
		key = (getattr(net, "RARITY_CONTEXT_INVENTORY", 1), metadataWindow, slotIndex, 0, 0)
		extra = GetRarityExtraSafe(*key)
		state = [vnum, player.GetItemCount(window, slotIndex), sockets, attrs,
			self.__GetRarityGrade(window, slotIndex, key), extra,
			self.__GetResonanceMetadata(window, slotIndex),
			player.GetRace(), tuple(player.GetStatus(stat) for stat in
				(player.LEVEL, player.ST, player.DX, player.IQ, player.HT)),
			shop.IsOpen(), self.__EquippedWeaponPercent(window, slotIndex)]
		if shop.IsOpen():
			state.extend((shop.IsPrivateShop(), player.GetISellItemPrice(window, slotIndex)))
		if app.ENABLE_APPLY_RANDOM:
			state.append(tuple(player.GetItemApplyRandom(window, slotIndex, i)
				for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)))
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			state.append(player.GetItemRefineElement(window, slotIndex))
		if app.ENABLE_SOUL_BIND_SYSTEM:
			state.append(player.GetItemSealDate(window, slotIndex))
		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			state.append(player.GetChangeLookVnum(window, slotIndex))
		if app.ENABLE_GROWTH_PET_SYSTEM:
			item.SelectItem(vnum)
			if (item.GetItemType() == item.ITEM_TYPE_PET
					and item.GetItemSubType() in (item.PET_UPBRINGING, item.PET_BAG)
					and sockets[2]):
				petId = sockets[2]
				state.extend((player.GetPetItem(petId), tuple(growthpetpresentation.SkillSlots(petId)),
					player.GetPetItemVNumInBag(petId)))
		return tuple(state)

	def RefreshInventoryItem(self, slotIndex):
		previous = getattr(self, "inventoryRefreshSnapshot", None)
		if not self.IsShow() or previous is None or previous[0] != slotIndex:
			return
		if previous[1] != self.__InventoryRefreshSnapshot(slotIndex):
			self.SetInventoryItem(slotIndex)

	def SetInventoryItem(
		self, slotIndex, window_type=player.INVENTORY, specialInventoryType=None,
		appendShortcuts=True, rarityPreviewGrade=None
	):
		if app.ENABLE_DS_SET:
			self.window_type = window_type

		if app.ENABLE_SLOT_TOOLTIP_INFO:
			self.HideToolTip()
			self.ClearToolTip()

		itemVnum = player.GetItemIndex(window_type, slotIndex)

		if 0 == itemVnum:
			if app.ENABLE_SLOT_TOOLTIP_INFO:
				if player.IsEquipmentSlot(slotIndex):
					if app.ENABLE_EXTEND_INVEN_SYSTEM:
						EQUIPMENT_START_INDEX = 180
					else:
						EQUIPMENT_START_INDEX = 90
					COSTUME_START_INDEX = item.COSTUME_SLOT_START

					slotNames = {
						EQUIPMENT_START_INDEX+0 : [localeInfo.TOOLTIP_ARMOR,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						EQUIPMENT_START_INDEX+1 : [localeInfo.TOOLTIP_HELMET,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						EQUIPMENT_START_INDEX+2 : [localeInfo.TOOLTIP_SHOES,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						EQUIPMENT_START_INDEX+3 : [localeInfo.TOOLTIP_WRIST,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						EQUIPMENT_START_INDEX+4 : [localeInfo.TOOLTIP_WEAPON,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						EQUIPMENT_START_INDEX+5 : [localeInfo.TOOLTIP_NECK,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						EQUIPMENT_START_INDEX+6 : [localeInfo.TOOLTIP_EARRING,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						#EQUIPMENT_START_INDEX+7 : ["Unique1",grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						#EQUIPMENT_START_INDEX+8 : ["Unique2",grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						# ALTHEA-641: the empty arrow cell is reserved and hidden (virtual quiver).
						#EQUIPMENT_START_INDEX+9 : [localeInfo.TOOLTIP_ARROW,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						EQUIPMENT_START_INDEX+10 : [localeInfo.TOOLTIP_SHIELD,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],

						item.EQUIPMENT_BELT : [localeInfo.TOOLTIP_BELT,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.EQUIPMENT_PENDANT : [localeInfo.TOOLTIP_TALISMAN,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.EQUIPMENT_GLOVE : [localeInfo.TOOLTIP_GLOVES,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.EQUIPMENT_TALISMAN_HEART : [localeInfo.TOOLTIP_TALISMAN_HEART,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],

						COSTUME_START_INDEX+0 : [localeInfo.TOOLTIP_COSTUME,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						COSTUME_START_INDEX+1 : [localeInfo.TOOLTIP_COSTUME_HAIR,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						COSTUME_START_INDEX+2 : [localeInfo.TOOLTIP_MOUNT,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						COSTUME_START_INDEX+3 : [localeInfo.TOOLTIP_COSTUME_ACCE,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						COSTUME_START_INDEX+4 : [localeInfo.TOOLTIP_COSTUME_WEAPON,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],

						item.ACCE_SKIN_SLOT : [localeInfo.TOOLTIP_SKIN_ACCE,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						#item.PET_SKIN_SLOT : [localeInfo.TOOLTIP_SKIN_PET,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.EQUIPMENT_RING1 : [localeInfo.TOOLTIP_RINGS,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.EQUIPMENT_RING2 : [localeInfo.TOOLTIP_RINGS,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.COSTUME_TYPE_SLOT_EFFECT_WEAPON : [localeInfo.TOOLTIP_WEAPON_EFFECT,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.COSTUME_TYPE_SLOT_EFFECT_ARMOR : [localeInfo.TOOLTIP_ARMOR_EFFECT,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],

						item.COSTUME_SLOT_AURA : [uiScriptLocale.AURA_MAIN,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
						item.COSTUME_SLOT_PET : [localeInfo.WIKI_SUBCATEGORY_PET,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],

					}
					for talismanCellName, talismanTooltipName in (
						("EQUIPMENT_TALISMAN_HUNTER", "TOOLTIP_TALISMAN_HUNTER"),
						("EQUIPMENT_TALISMAN_GUARDIAN", "TOOLTIP_TALISMAN_GUARDIAN"),
						("EQUIPMENT_TALISMAN_BREAKER", "TOOLTIP_TALISMAN_BREAKER"),
						("EQUIPMENT_TALISMAN_PROTECTOR", "TOOLTIP_TALISMAN_PROTECTOR"),
						("EQUIPMENT_TALISMAN_CONQUEROR", "TOOLTIP_TALISMAN_CONQUEROR"),
						("EQUIPMENT_TALISMAN_HEART", "TOOLTIP_TALISMAN_HEART"),
					):
						talismanCell = getattr(item, talismanCellName, -1)
						if talismanCell >= 0:
							slotNames[talismanCell] = [
								getattr(localeInfo, talismanTooltipName),
								grp.GenerateColor(1.0, 1.0, 0.0, 1.0),
							]
					if slotIndex in slotNames:
						self.AlignHorizonalCenter()
						self.AutoAppendNewTextLine(slotNames[slotIndex][0],slotNames[slotIndex][1])
						self.ShowToolTip()
			return

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if window_type == player.PET_FEED:
				itemVnum = player.GetItemIndex(player.INVENTORY, slotIndex)

		if not app.ENABLE_SLOT_TOOLTIP_INFO:
			self.ClearToolTip()

		if shop.IsOpen():
			if not shop.IsPrivateShop():
				item.SelectItem(itemVnum)
				self.AppendSellingPrice(player.GetISellItemPrice(window_type, slotIndex))

		metinSlot = [player.GetItemMetinSocket(window_type, slotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [player.GetItemAttribute(window_type, slotIndex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if window_type == player.PET_FEED:
				metinSlot = [player.GetItemMetinSocket(player.INVENTORY, slotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]

		apply_random_list = []
		if app.ENABLE_APPLY_RANDOM:
			apply_random_list = [player.GetItemApplyRandom(window_type, slotIndex, i) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)]

		refine_element = player.GetItemRefineElement(window_type, slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

		pendingRaritySlots = ()
		rarityV2 = False
		if rarityPreviewGrade is not None:
			rarityV2 = bool(getattr(net, "IsRarityV2Available", lambda: False)())
			extra = (0, 0)
			if rarityV2:
				extra = GetRarityExtraSafe(
					getattr(net, "RARITY_CONTEXT_INVENTORY", 1),
					ResolveRarityInventoryWindow(window_type, slotIndex), slotIndex, 0, 0) or (0, 0)
			attrSlot, pendingRaritySlots = raritypreview.ProjectAttributes(
				attrSlot, extra, rarityPreviewGrade, rarityV2)

		self.AddItemData(
			itemVnum, metinSlot, attrSlot, None, 0, 0, window_type, slotIndex,
			refine_element, apply_random_list, 0,
			rarity_key=(
				getattr(net, "RARITY_CONTEXT_INVENTORY", 1),
				ResolveRarityInventoryWindow(window_type, slotIndex),
				slotIndex, 0, 0,
			),
			deferMountPreview=True,
			rarity_preview_grade=rarityPreviewGrade,
		)
		if pendingRaritySlots:
			color = RARITY_GRADE_COLORS[int(rarityPreviewGrade)]
			if rarityV2:
				for index in pendingRaritySlots:
					self.AppendTextLine(localeInfo.RARITY_PREVIEW_RANDOM_BONUS % (index + 1), color)
			else:
				self.AppendTextLine(localeInfo.RARITY_PREVIEW_UNAVAILABLE, color)
			self.ResizeToolTip()
			self.ShowToolTip()
		if appendShortcuts:
			self.__AppendInventoryShortcutHints(
				itemVnum, slotIndex, window_type, specialInventoryType
			)
		if app.ENABLE_RENDER_TARGET_PREVIEW and self.mountPreviewRace > 0:
			self.__AppendMountPreview()
		if app.ENABLE_RENDER_TARGET_PREVIEW and self.costumePreviewVnum > 0:
			self.__AppendCostumePreview()

		if (appendShortcuts and window_type == player.INVENTORY
				and specialInventoryType is None and rarityPreviewGrade is None):
			self.inventoryRefreshSnapshot = (slotIndex, self.__InventoryRefreshSnapshot(slotIndex))

	def SetResulItemAttrMove(self, baseSlotIndex, materialSlotIndex, window_type = player.INVENTORY):
		baseItemVnum = player.GetItemIndex(window_type, baseSlotIndex)

		if 0 == baseItemVnum:
			return

		materialItemVnum = player.GetItemIndex(window_type, materialSlotIndex)

		if 0 == materialItemVnum:
			return

		self.ClearToolTip()

		metinSlot = [player.GetItemMetinSocket(window_type, baseSlotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [player.GetItemAttribute(window_type, materialSlotIndex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
		refine_element = player.GetItemRefineElement(window_type, materialSlotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
		apply_random_list = [player.GetItemApplyRandom(window_type, materialSlotIndex, i) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)] if app.ENABLE_APPLY_RANDOM else []
		set_value = 0

		self.AddItemData(baseItemVnum, metinSlot, attrSlot, None, 0, 0, window_type, -1, refine_element, apply_random_list, set_value)

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def AppendChangeLookInfoShopWindow(self, slotIndex):
			changelookvnum = shop.GetItemChangeLookVnum(slotIndex)
			if not changelookvnum == 0:
				self.AppendSpace(5)
				self.AppendTextLine("[ " + localeInfo.CHANGE_LOOK_TITLE + " ]", self.CHANGELOOK_TITLE_COLOR)
				itemName = item.GetItemNameByVnum(changelookvnum)

				if item.GetItemType() == item.ITEM_TYPE_COSTUME:
					if item.GetItemSubType() == item.COSTUME_TYPE_BODY:
						malefemale = ""
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
							malefemale = localeInfo.FOR_FEMALE

						if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
							malefemale = localeInfo.FOR_MALE
						itemName += " ( " + malefemale + " )"

				textLine = self.AppendTextLine(itemName, self.CHANGELOOK_ITEMNAME_COLOR, True)
				textLine.SetFeather()

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def AppendChangeLookInfoItemVnum(self, changelookvnum):
			if not changelookvnum == 0:
				self.AppendSpace(5)
				self.AppendTextLine("[ " + localeInfo.CHANGE_LOOK_TITLE + " ]", self.CHANGELOOK_TITLE_COLOR)
				itemName = item.GetItemNameByVnum(changelookvnum)

				if item.GetItemType() == item.ITEM_TYPE_COSTUME:
					if item.GetItemSubType() == item.COSTUME_TYPE_BODY:
						malefemale = ""
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
							malefemale = localeInfo.FOR_FEMALE

						if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
							malefemale = localeInfo.FOR_MALE
						itemName += " ( " + malefemale + " )"

				textLine = self.AppendTextLine(itemName, self.CHANGELOOK_ITEMNAME_COLOR, True)
				textLine.SetFeather()

	if app.ENABLE_PLAYER_RANKING:
		def SetRankingRewardItem(self, itemVnum):
			self.ClearToolTip()
			
			metinSlot = []
			for i in range(player.METIN_SOCKET_MAX_NUM):
				metinSlot.append(0)
			attrSlot = []
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				attrSlot.append((0,0))
			
			self.AddItemData(itemVnum, metinSlot, attrSlot)

	def SetShopItem(self, slotIndex):
		itemVnum = shop.GetItemID(slotIndex)
		if 0 == itemVnum:
			return

		price = shop.GetItemPrice(slotIndex)
		self.ClearToolTip()
		self.isShopItem = True

		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(shop.GetItemMetinSocket(slotIndex, i))
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(shop.GetItemAttribute(slotIndex, i))
		apply_random_list = []
		if app.ENABLE_APPLY_RANDOM:
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
				apply_random_list.append(shop.GetItemApplyRandom(slotIndex, i))

		refine_element = shop.GetItemRefineElement(slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

		self.AddItemData(itemVnum, metinSlot, attrSlot, None, 0, 0, player.INVENTORY, slotIndex, refine_element, apply_random_list, 0,
			rarity_key=(getattr(net, "RARITY_CONTEXT_SHOP", 5), 0, 0, 0, slotIndex + 1))

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.AppendChangeLookInfoShopWindow(slotIndex)

		self.AppendPrice(price)

		if app.ENABLE_MULTIPLE_BUY and not shop.IsPrivateShop():
			item.SelectItem(itemVnum)
			if item.IsFlag(item.ITEM_FLAG_STACKABLE) and itemVnum != 51002 and itemVnum != 55031:
				self.AppendSpace(5)
				self.AppendTextLine("|Ikey/ctrl|i + |Ikey/mouse_right|i - %s" % localeInfo.SELECT_QUANTITY, self.TITLE_COLOR)

	if app.ENABLE_COMBAT_ZONE:
		def SetShopItemByCombatZoneCoin(self, slotIndex):
			itemVnum = shop.GetItemID(slotIndex)
			if 0 == itemVnum:
				return

			price = shop.GetItemPrice(slotIndex)
			self.ClearToolTip()
			self.isShopItem = True

			metinSlot = []
			for i in range(player.METIN_SOCKET_MAX_NUM):
				metinSlot.append(shop.GetItemMetinSocket(slotIndex, i))
			attrSlot = []
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				attrSlot.append(shop.GetItemAttribute(slotIndex, i))

			self.AddItemData(itemVnum, metinSlot, attrSlot)
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_BUYPRICE % (localeInfo.NumberToCombatZoneCoinString(price)), self.HIGH_PRICE_COLOR)

	def SetShopItemBySecondaryCoin(self, slotIndex):
		itemVnum = shop.GetItemID(slotIndex)
		if 0 == itemVnum:
			return

		price = shop.GetItemPrice(slotIndex)
		self.ClearToolTip()
		self.isShopItem = True

		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(shop.GetItemMetinSocket(slotIndex, i))
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(shop.GetItemAttribute(slotIndex, i))

		self.AddItemData(itemVnum, metinSlot, attrSlot)
		self.AppendPriceBySecondaryCoin(price)

		if app.ENABLE_MULTIPLE_BUY:
			item.SelectItem(itemVnum)
			if item.IsFlag(item.ITEM_FLAG_STACKABLE) and itemVnum != 51002 and itemVnum != 55031:
				self.AppendSpace(5)
				self.AppendTextLine("|Ikey/ctrl|i + |Ikey/mouse_right|i - %s" % localeInfo.SELECT_QUANTITY, self.TITLE_COLOR)

	if app.ENABLE_SHOPEX_RENEWAL:
		def SetShopItemByShopEx(self, slotIndex, type):
			itemVnum = shop.GetItemID(slotIndex)
			PriceVnum, PriceVnumCount = shop.ExGetItemPrice(slotIndex, 0)

			if 0 == itemVnum:
				return

			if PriceVnum == 0 and type == 3:
				return

			price = shop.GetItemPrice(slotIndex)
			self.ClearToolTip()
			self.isShopItem = True

			metinSlot = []
			for i in range(player.METIN_SOCKET_MAX_NUM):
				metinSlot.append(shop.GetItemMetinSocket(slotIndex, i))
			attrSlot = []
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				attrSlot.append(shop.GetItemAttribute(slotIndex, i))

			self.AddItemData(itemVnum, metinSlot, attrSlot)
			self.AppendSpace(5)

			if type == 3:
				self.AppendTextLine(localeInfo.MONEY_INPUT_DIALOG_SELLPRICE)
				self.AppendSpace(5)
				for i in range(shop.SHOPEX_VNUM_COUNT):
					PriceVnum, PriceVnumCount = shop.ExGetItemPrice(slotIndex, i)
					if PriceVnum != 0 and PriceVnumCount != 0:
						self.AddShopEXItem(PriceVnum, PriceVnumCount)
			else:
				self.AppendTextLineDontCheckColor(localeInfo.TOOLTIP_BUYPRICE % (localeInfo.NumberToShopEXP(price)), self.GetPriceColor(price))

			if app.ENABLE_MULTIPLE_BUY:
				item.SelectItem(itemVnum)
				if item.IsFlag(item.ITEM_FLAG_STACKABLE) and itemVnum != 51002 and itemVnum != 55031:
					self.AppendSpace(5)
					self.AppendTextLine("|Ikey/ctrl|i + |Ikey/mouse_right|i - %s" % localeInfo.SELECT_QUANTITY, self.TITLE_COLOR)

		def AddShopEXItem(self, itemVnum, price):
			item.SelectItem(itemVnum)
			if 91200 <= itemVnum <= 91203:
				iconPath = item.GetIconImageFileName()
				rowY = self.toolTipHeight
				priceLine = self.AppendTextLineDontCheckColor(
					"%dx %s" % (price, item.GetItemName()), self.SPECIAL_TITLE_COLOR, False)
				icon = ui.ImageBox()
				icon.SetParent(self)
				icon.LoadImage(iconPath)
				icon.Show()
				iconWidth = icon.GetWidth()
				iconHeight = icon.GetHeight()
				textWidth, textHeight = priceLine.GetTextSize()
				rowWidth = iconWidth + 6 + textWidth
				self.toolTipWidth = max(self.toolTipWidth, rowWidth + 20)
				rowX = (self.toolTipWidth - rowWidth) // 2
				icon.SetPosition(rowX, rowY)
				priceLine.SetPosition(rowX + iconWidth + 6, rowY + max(0, (iconHeight - textHeight) // 2))
				self.childrenList.append(icon)
				self.toolTipHeight += max(0, iconHeight - self.TEXT_LINE_HEIGHT) + 3
				self.ResizeToolTip()
				return
			
			priceItem = item.GetIconImageFileName()
			priceItem = priceItem.replace("\\", "/")
			priceItem = priceItem.replace("icon/", "")
			priceItem = priceItem.replace(".tga", "")
			iconPriceItem = "|I" + priceItem + "|i"
			
			name = "%dx %s %s" % (price, iconPriceItem, item.GetItemName())
			self.AutoAppendTextLine(name, self.SPECIAL_TITLE_COLOR)
			self.AppendSpace(18)
			self.ResizeToolTip()

	def SetExchangeOwnerItem(self, slotIndex):
		itemVnum = exchange.GetItemVnumFromSelf(slotIndex)

		if 0 == itemVnum:
			return

		self.ClearToolTip()

		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(exchange.GetItemMetinSocketFromSelf(slotIndex, i))
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(exchange.GetItemAttributeFromSelf(slotIndex, i))
		apply_random_list = []
		if app.ENABLE_APPLY_RANDOM:
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
				apply_random_list.append(exchange.GetItemApplyRandomFromSelf(slotIndex, i))

		refine_element = exchange.GetItemRefineElementFromSelf(slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

		self.AddItemData(itemVnum, metinSlot, attrSlot, None, 0, 0, player.INVENTORY, -1, refine_element, apply_random_list, 0,
			rarity_key=(getattr(net, "RARITY_CONTEXT_EXCHANGE", 3), 0, slotIndex, 0, 0))

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.AppendChangeLookInfoExchangeWIndow(0, slotIndex)

	if app.ENABLE_SEND_TARGET_INFO:
		def SetItemToolTipBook(self, itemVnum):
			item.SelectItem(itemVnum)

			self.ClearToolTip()

			self.SetTitle(item.GetItemName())
			self.AppendDescription(item.GetItemDescription(), 26)
			self.AppendDescription(item.GetItemSummary(), 26, self.CONDITION_COLOR)
			self.__AppendTradeabilityInformation()
			self.ShowToolTip()


	def SetExchangeTargetItem(self, slotIndex):
		itemVnum = exchange.GetItemVnumFromTarget(slotIndex)
		if 0 == itemVnum:
			return

		self.ClearToolTip()

		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(exchange.GetItemMetinSocketFromTarget(slotIndex, i))
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(exchange.GetItemAttributeFromTarget(slotIndex, i))
		apply_random_list = []
		if app.ENABLE_APPLY_RANDOM:
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
				apply_random_list.append(exchange.GetItemApplyRandomFromTarget(slotIndex, i))

		refine_element = exchange.GetItemRefineElementFromTarget(slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

		self.AddItemData(itemVnum, metinSlot, attrSlot, None, 0, 0, player.INVENTORY, -1, refine_element, apply_random_list, 0,
			rarity_key=(getattr(net, "RARITY_CONTEXT_EXCHANGE", 3), 1, slotIndex, 0, 0))

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.AppendChangeLookInfoExchangeWIndow(1, slotIndex)

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def AppendChangeLookInfoExchangeWIndow(self, type, slotIndex):
			if type == 0:
				changelookvnum = exchange.GetChangeLookVnumFromSelf(slotIndex)
			elif type == 1:
				changelookvnum = exchange.GetChangeLookVnumFromTarget(slotIndex)
			if not changelookvnum == 0:
				self.AppendSpace(5)
				self.AppendTextLine("[ " + localeInfo.CHANGE_LOOK_TITLE + " ]", self.CHANGELOOK_TITLE_COLOR)
				itemName = item.GetItemNameByVnum(changelookvnum)

				if item.GetItemType() == item.ITEM_TYPE_COSTUME:
					if item.GetItemSubType() == item.COSTUME_TYPE_BODY:
						malefemale = ""
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
							malefemale = localeInfo.FOR_FEMALE

						if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
							malefemale = localeInfo.FOR_MALE
						itemName += " ( " + malefemale + " )"

				textLine = self.AppendTextLine(itemName, self.CHANGELOOK_ITEMNAME_COLOR, True)
				textLine.SetFeather()

	def SetPrivateShopBuilderItem(self, invenType, invenPos, privateShopSlotIndex):
		itemVnum = player.GetItemIndex(invenType, invenPos)
		if 0 == itemVnum:
			return

		item.SelectItem(itemVnum)
		self.ClearToolTip()

		self.AppendSellingPrice(shop.GetPrivateShopItemPrice(invenType, invenPos))

		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(player.GetItemMetinSocket(invenPos, i))
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(player.GetItemAttribute(invenPos, i))
		apply_random_list = []
		if app.ENABLE_APPLY_RANDOM:
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
				apply_random_list.append(player.GetItemApplyRandom(invenPos, i))

		refine_element = player.GetItemRefineElement(invenType, invenPos) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

		self.AddItemData(itemVnum, metinSlot, attrSlot, None, 0, 0, invenType, invenPos, refine_element, apply_random_list, 0)

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def SetChangeLookWindowItem(self, slotIndex):
			inventoryslotindex = player.GetChangeLookItemInvenSlot(slotIndex)
			if inventoryslotindex == player.ITEM_SLOT_COUNT:
				return

			itemVnum = player.GetItemIndex(player.INVENTORY, inventoryslotindex)
			if 0 == itemVnum:
				return

			self.ClearToolTip()

			metinSlot = [player.GetItemMetinSocket(player.INVENTORY, inventoryslotindex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = [player.GetItemAttribute(player.INVENTORY, inventoryslotindex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			apply_random_list = []
			if app.ENABLE_APPLY_RANDOM:
				for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
					apply_random_list.append(player.GetItemApplyRandom(player.INVENTORY, inventoryslotindex, i))

			refine_element = player.GetItemRefineElement(player.INVENTORY, inventoryslotindex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

			self.AddItemData(itemVnum, metinSlot, attrSlot, None, 0, 0, player.INVENTORY, inventoryslotindex, refine_element, apply_random_list, 0)

	def SetSafeBoxItem(self, slotIndex):
		itemVnum = safebox.GetItemID(slotIndex)
		if 0 == itemVnum:
			return

		self.ClearToolTip()
		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(safebox.GetItemMetinSocket(slotIndex, i))
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(safebox.GetItemAttribute(slotIndex, i))
		apply_random_list = []
		if app.ENABLE_APPLY_RANDOM:
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
				apply_random_list.append(safebox.GetItemApplyRandom(slotIndex, i))

		refine_element = safebox.GetItemRefineElement(slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

		self.AddItemData(itemVnum, metinSlot, attrSlot, None, safebox.GetItemFlags(slotIndex), 0, player.SAFEBOX, slotIndex, refine_element, apply_random_list, 0,
			rarity_key=(getattr(net, "RARITY_CONTEXT_SAFEBOX", 2), player.SAFEBOX, slotIndex, 0, 0))

	def SetMallItem(self, slotIndex):
		itemVnum = safebox.GetMallItemID(slotIndex)
		if 0 == itemVnum:
			return

		self.ClearToolTip()
		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(safebox.GetMallItemMetinSocket(slotIndex, i))
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(safebox.GetMallItemAttribute(slotIndex, i))
		apply_random_list = []
		if app.ENABLE_APPLY_RANDOM:
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
				apply_random_list.append(safebox.GetMallItemApplyRandom(slotIndex, i))

		refine_element = safebox.GetMallItemRefineElement(slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

		self.AddItemData(itemVnum, metinSlot, attrSlot, None, 0, 0, player.MALL, slotIndex, refine_element, apply_random_list, 0,
			rarity_key=(getattr(net, "RARITY_CONTEXT_SAFEBOX", 2), player.MALL, slotIndex, 0, 0))

	if app.ENABLE_WIKI:
		def SetItemToolTipWiki(self, itemVnum):
			self.itemVnum = itemVnum
			item.SelectItem(itemVnum)
			metinSlot = [0 for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = [(0,0) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)
				if item.LIMIT_TIMER_BASED_ON_WEAR == limitType:
					metinSlot[0] = limitValue
				elif item.LIMIT_REAL_TIME == limitType or item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
					metinSlot[0] = app.GetGlobalTimeStamp()+limitValue
			self.SetTitle(item.GetItemName())
			self.AppendDescription(item.GetItemDescription(), 26)
			self.AppendDescription(item.GetItemSummary(), 26, self.CONDITION_COLOR)
			self.__AppendSageReadingTerms(itemVnum)
			self.__AppendAffectInformation()
			self.__AppendAttributeInformation(attrSlot, itemVnum)
			self.AppendWearableInformation()
			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)
				if item.LIMIT_REAL_TIME == limitType:
					if metinSlot[0] > 0:
						self.AppendMallItemLastTime(metinSlot[0])
					break
			self.ShowToolTip()

	def SetCostumeVoucherOfferToolTip(self, voucherVnum):
		"""Item Shop offer of an ALTHEA-522 voucher: describe the costume it redeems to.

		The purchase still buys (and the server still delivers) the voucher;
		only the presentation changes (ALTHEA-595).
		"""
		entry = iscostumevoucher.Get(voucherVnum)
		if not entry:
			self.SetItemToolTip(voucherVnum)
			return
		self.ClearToolTip()
		metinSlot = [0 for i in range(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [(0, 0) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
		self.costumeVoucherOffer = int(voucherVnum)
		try:
			self.AddItemData(entry[0], metinSlot, attrSlot)
		finally:
			self.costumeVoucherOffer = 0

	def __CostumeRenderTargetType(self, costumeVnum):
		item.SelectItem(costumeVnum)
		if item.GetItemType() != item.ITEM_TYPE_COSTUME:
			return 0
		subType = item.GetItemSubType()
		if subType == item.COSTUME_TYPE_BODY:
			return 2
		if subType == item.COSTUME_TYPE_HAIR:
			return 3
		if subType == getattr(item, "COSTUME_TYPE_WEAPON", -1):
			return 1
		return 0

	def __ResolveCostumeVoucher(self, itemVnum, isCostumeItem):
		"""Return the voucher entry this tooltip presents and arm its previews."""
		if self.costumeVoucherOffer:
			entry = iscostumevoucher.Get(self.costumeVoucherOffer)
			if not entry or not isCostumeItem:
				return None
			self.costumePreviewVnum = itemVnum
			return entry
		entry = iscostumevoucher.Get(itemVnum)
		if not entry:
			return None
		self.costumePreviewVnum = entry[0]
		if app.ENABLE_RENDER_TARGET_PREVIEW:
			previewType = self.__CostumeRenderTargetType(entry[0])
			if previewType:
				# Ctrl+X on an owned voucher previews the costume it redeems to.
				self.savedItemVnum = entry[0]
				osfInfo.RENDER_TARGET_ITEM_TYPE = previewType
		item.SelectItem(itemVnum)
		return entry

	def __AppendCostumeVoucherInformation(self, itemVnum, entry):
		# Voucher facts apply whatever class the viewer plays; keep them readable.
		forceDisable = self.bCannotUseItemForceSetDisableColor
		self.bCannotUseItemForceSetDisableColor = False
		try:
			self.__AppendCostumeVoucherLines(itemVnum, entry)
		finally:
			self.bCannotUseItemForceSetDisableColor = forceDisable
			item.SelectItem(itemVnum)

	def __AppendCostumeVoucherLines(self, itemVnum, entry):
		self.AppendSpace(5)
		if self.costumeVoucherOffer:
			self.AppendTextLineDontCheckColor(
				"[ %s ]" % getattr(localeInfo, "COSTUME_VOUCHER_BADGE", "Voucher"),
				self.COSTUME_VOUCHER_COLOR)
			self.AppendDescription(getattr(localeInfo, "COSTUME_VOUCHER_OFFER_INFO", ""), 26)
		else:
			item.SelectItem(entry[0])
			costumeName = item.GetItemName()
			if costumeName:
				self.AppendTextLineDontCheckColor(
					getattr(localeInfo, "COSTUME_VOUCHER_COSTUME", "%s") % costumeName,
					self.COSTUME_VOUCHER_COLOR)
		for label, variantVnum in (("PvM", entry[0]), ("PvP", entry[1])):
			item.SelectItem(variantVnum)
			self.AppendSpace(3)
			self.AppendTextLineDontCheckColor(label, self.TITLE_COLOR)
			description = item.GetItemDescription()
			if description:
				self.AppendDescription(description, 26, self.POSITIVE_COLOR)
				continue
			for index in range(item.ITEM_APPLY_MAX_NUM):
				(affectType, affectValue) = item.GetAffect(index)
				affectString = self.__GetAffectString(affectType, affectValue)
				if affectString:
					self.AppendTextLineDontCheckColor(affectString, self.POSITIVE_COLOR)
		item.SelectItem(itemVnum)
		if self.costumeVoucherOffer and app.ENABLE_RENDER_TARGET_PREVIEW:
			self.AppendSpace(5)
			self.AppendTextLineDontCheckColor(
				"|Ikey/mouse_right|i - %s" % localeInfo.IKEY_SYSTEM_PREVIEW, self.TITLE_COLOR)

	def SetItemToolTip(self, itemVnum):
		self.ClearToolTip()
		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(0)
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append((0, 0))

		self.AddItemData(itemVnum, metinSlot, attrSlot)

		if app.ENABLE_SHOW_CHEST_DROP:
			item.SelectItem(itemVnum)
			itemType = item.GetItemType()
			if itemType in (item.ITEM_TYPE_GIFTBOX, item.ITEM_TYPE_GACHA,
					item.ITEM_TYPE_TREASURE_BOX):
				self.AppendSpace(5)
				self.AppendTextLine("|Ikey/shift|i + |Ikey/mouse_right|i - %s" % localeInfo.CHEST_DROP_PREVIEW, self.TITLE_COLOR)

	if app.ENABLE_OFFLINE_SHOP:
		def SetOfflineShopItem(self, offlineShopItem):
			self.ClearToolTip()
			self.isShopItem = True
			refine_element = getattr(offlineShopItem, "REFINE_ELEMENT", None) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
			apply_random_list = offlineShopItem.APPLY_RANDOM if app.ENABLE_APPLY_RANDOM else None
			self.AddItemData(
				offlineShopItem.VNUM,
				offlineShopItem.SOCKETS,
				offlineShopItem.ATTRIBUTES,
				0, 0, 0,
				player.INVENTORY, -1,
				refine_element,
				apply_random_list,
				0,
			)
			self.AppendChangeLookInfoItemVnum(offlineShopItem.TRANSMUTATION)
			self.AppendPrice(offlineShopItem.PRICE)

	if app.ENABLE_SHOP_SEARCH:
		def SetShopSearchItem(self, resultIndex, priceColor):
			itemVnum = shopsearch.GetResultItemVnum(resultIndex)
			if itemVnum == 0:
				return
	
			self.ClearToolTip()
			self.isShopItem = True
			metinSlot = [shopsearch.GetResultItemSocket(resultIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = [shopsearch.GetResultItemAttribute(resultIndex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			price = shopsearch.GetResultItemPrice(resultIndex)
	
			refine_element = shopsearch.GetResultItemRefineElement(resultIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
			self.AddItemData(itemVnum, metinSlot, attrSlot, apply_random_list = [shopsearch.GetResultItemApplyRandom(resultIndex, i) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)], refine_element=refine_element)
			self.AppendPriceOfflineShop(price, priceColor)
			# if app.ENABLE_PREVIEW_MAX_STATS:
				# self.savedPrice = price

	def __AppendWeaponPowerLine(self, text, percent):
		text += itembonuspresentation.WeaponSuffix(percent)
		color = self.SPECIAL_POSITIVE_COLOR2 if percent > 0 else self.POSITIVE_COLOR
		line = self.AppendTextLine(text, color)
		self.__GrowBonusWidth(line)
		return line

	def __EquippedWeaponPercent(self, windowType, slotIndex, rarityKey=None, previewGrade=None):
		if (self.isShopItem or previewGrade is not None
				or windowType not in (player.INVENTORY, player.EQUIPMENT)
				or slotIndex != item.EQUIPMENT_WEAPON
				or (rarityKey is not None and int(rarityKey[0]) != 1)):
			return 0
		if player.GetItemIndex(player.INVENTORY, item.EQUIPMENT_WEAPON) != self.itemVnum:
			return 0
		return itembonuspresentation.WeaponPercent(player, item)

	def __AppendAttackSpeedInfo(self, item):
		atkSpd = item.GetValue(0)

		if atkSpd < 80:
			stSpd = localeInfo.TOOLTIP_ITEM_VERY_FAST
		elif atkSpd <= 95:
			stSpd = localeInfo.TOOLTIP_ITEM_FAST
		elif atkSpd <= 105:
			stSpd = localeInfo.TOOLTIP_ITEM_NORMAL
		elif atkSpd <= 120:
			stSpd = localeInfo.TOOLTIP_ITEM_SLOW
		else:
			stSpd = localeInfo.TOOLTIP_ITEM_VERY_SLOW

		self.AppendTextLine(localeInfo.TOOLTIP_ITEM_ATT_SPEED % stSpd, self.NORMAL_COLOR)

	def __AppendAttackGradeInfo(self):
		atkGrade = item.GetValue(1)
		self.AppendTextLine(localeInfo.TOOLTIP_ITEM_ATT_GRADE % atkGrade, self.GetChangeTextLineColor(atkGrade))

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def CalcAcceValue(self, value, abs):
			if not value:
				return 0

			valueCalc = int((round(value * abs) / 100) - .5) + int(int((round(value * abs) / 100) - .5) > 0)
			if valueCalc <= 0 and value > 0:
				value = 1
			else:
				value = valueCalc

			return value

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def __AppendAttackPowerInfo(self, itemAbsChance = 0, refine_element = None):
			percent = 0 if itemAbsChance else self.weaponBasePercent
			minPower = itembonuspresentation.WeaponBase(item.GetValue(3), percent)
			maxPower = itembonuspresentation.WeaponBase(item.GetValue(4), percent)
			addPower = item.GetValue(5)
			if itemAbsChance and item.GetItemSubType() == item.WEAPON_BOW and item.GetValue(0) > 0:
				# Value0 preserves the original donor maximum after narrowing the bow range.
				minPower = maxPower = item.GetValue(0)
				addPower = 0

			if itemAbsChance:
				minPower = self.CalcAcceValue(minPower, itemAbsChance)
				maxPower = self.CalcAcceValue(maxPower, itemAbsChance)
				addPower = self.CalcAcceValue(addPower, itemAbsChance)

			if maxPower > minPower:
				if app.ENABLE_REFINE_ELEMENT_SYSTEM and self.GetRefineElement(refine_element):
					grade = refine_element[self.REFINE_ELEMENT_INDEX_GRADE]
					bonus_value = 0
					for i in range(min(self.REFINE_ELEMENT_INDEX_MAX, grade)):
						bonus_value += refine_element[self.REFINE_ELEMENT_INDEX_BONUS][i]

					if itemAbsChance:
						bonus_value = self.CalcAcceValue(bonus_value, itemAbsChance)

					if self.isRefineElementItem:
						min_value = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_BONUS_VALUE_MIN
						max_value = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_BONUS_VALUE_MAX

						affect_string = localeInfo.TOOLTIP_ITEM_ATT_POWER % (minPower + addPower, maxPower + addPower)
						affect_string += self.__GetRefineElementValueText(0, min_value, max_value, bonus_value)
						if affect_string:
							self.__AppendWeaponPowerLine(affect_string, percent)
					else:
						self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_ATT_POWER_REFINE % (minPower + addPower, maxPower + addPower, bonus_value), percent)
				else:
					self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_ATT_POWER % (minPower+addPower, maxPower+addPower), percent)
			else:
				self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_ATT_POWER_ONE_ARG % (minPower+addPower), percent)
	else:
		def __AppendAttackPowerInfo(self, refine_element = None):
			percent = self.weaponBasePercent
			minPower = itembonuspresentation.WeaponBase(item.GetValue(3), percent)
			maxPower = itembonuspresentation.WeaponBase(item.GetValue(4), percent)
			addPower = item.GetValue(5)
			if maxPower > minPower:
				if app.ENABLE_REFINE_ELEMENT_SYSTEM and self.GetRefineElement(refine_element):
					grade = refine_element[self.REFINE_ELEMENT_INDEX_GRADE]
					bonus_value = 0
					for i in range(min(self.REFINE_ELEMENT_INDEX_MAX, grade)):
						bonus_value += refine_element[self.REFINE_ELEMENT_INDEX_BONUS][i]

					if self.isRefineElementItem:
						min_value = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_BONUS_VALUE_MIN
						max_value = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_BONUS_VALUE_MAX

						affect_string = localeInfo.TOOLTIP_ITEM_ATT_POWER % (minPower + addPower, maxPower + addPower)
						affect_string += self.__GetRefineElementValueText(0, min_value, max_value, bonus_value)
						if affect_string:
							self.__AppendWeaponPowerLine(affect_string, percent)
					else:
						self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_ATT_POWER_REFINE % (minPower + addPower, maxPower + addPower, bonus_value), percent)
				else:
					self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_ATT_POWER % (minPower+addPower, maxPower+addPower), percent)
			else:
				self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_ATT_POWER_ONE_ARG % (minPower+addPower), percent)

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def __AppendMagicAttackInfo(self, itemAbsChance = 0):
			percent = 0 if itemAbsChance else self.weaponBasePercent
			minMagicAttackPower = itembonuspresentation.WeaponBase(item.GetValue(1), percent)
			maxMagicAttackPower = itembonuspresentation.WeaponBase(item.GetValue(2), percent)
			addPower = item.GetValue(5)

			if itemAbsChance:
				minMagicAttackPower = self.CalcAcceValue(minMagicAttackPower, itemAbsChance)
				maxMagicAttackPower = self.CalcAcceValue(maxMagicAttackPower, itemAbsChance)
				addPower = self.CalcAcceValue(addPower, itemAbsChance)

			if minMagicAttackPower > 0 or maxMagicAttackPower > 0:
				if maxMagicAttackPower > minMagicAttackPower:
					self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_MAGIC_ATT_POWER % (minMagicAttackPower + addPower, maxMagicAttackPower + addPower), percent)
				else:
					self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_MAGIC_ATT_POWER_ONE_ARG % (minMagicAttackPower + addPower), percent)
	else:
		def __AppendMagicAttackInfo(self):
			percent = self.weaponBasePercent
			minMagicAttackPower = itembonuspresentation.WeaponBase(item.GetValue(1), percent)
			maxMagicAttackPower = itembonuspresentation.WeaponBase(item.GetValue(2), percent)
			addPower = item.GetValue(5)

			if minMagicAttackPower > 0 or maxMagicAttackPower > 0:
				if maxMagicAttackPower > minMagicAttackPower:
					self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_MAGIC_ATT_POWER % (minMagicAttackPower+addPower, maxMagicAttackPower+addPower), percent)
				else:
					self.__AppendWeaponPowerLine(localeInfo.TOOLTIP_ITEM_MAGIC_ATT_POWER_ONE_ARG % (minMagicAttackPower+addPower), percent)

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def __AppendMagicDefenceInfo(self, itemAbsChance = 0):
			magicDefencePower = item.GetValue(0)

			if itemAbsChance:
				magicDefencePower = self.CalcAcceValue(magicDefencePower, itemAbsChance)

			if magicDefencePower > 0:
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_MAGIC_DEF_POWER % magicDefencePower, self.GetChangeTextLineColor(magicDefencePower))
	else:
		def __AppendMagicDefenceInfo(self):
			magicDefencePower = item.GetValue(0)

			if magicDefencePower > 0:
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_MAGIC_DEF_POWER % magicDefencePower, self.GetChangeTextLineColor(magicDefencePower))

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def __AppendAttributeInformation(self, attrSlot, itemAbsChance = 0):
			if 0 != attrSlot:
				for i in range(min(8, len(attrSlot))):
					type = attrSlot[i][0]
					value = attrSlot[i][1]
					rawValue = value

					if 0 == value:
						continue

					affectString = self.__GetAffectString(type, value)

					if item.GetItemType() == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == item.COSTUME_TYPE_ACCE and itemAbsChance:
						value = self.CalcAcceValue(value, itemAbsChance)
						affectString = self.__GetAffectString(type, value)

					if affectString:
						affectColor = self.__GetAttributeColor(i, type, rawValue)
						self.AppendTextLine(affectString, affectColor)
	else:
		def __AppendAttributeInformation(self, attrSlot):
			if 0 != attrSlot:
				for i in range(min(8, len(attrSlot))):
					type = attrSlot[i][0]
					value = attrSlot[i][1]

					if 0 == value:
						continue

					affectString = self.__GetAffectString(type, value)
					if affectString:
						affectColor = self.__GetAttributeColor(i, type, value)
						self.AppendTextLine(affectString, affectColor)

	if app.ENABLE_67TH_BONUS:
		def __AppendRareAttributeInformation(self, attrSlot):
			if 0 != attrSlot:
				attrCount = 0
				for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
					if 0 == attrSlot[i][1]:
						continue

					attrCount += 1

				if attrCount < player.ATTRIBUTE_SLOT_MAX_NUM and attrCount >= (player.ATTRIBUTE_SLOT_MAX_NUM - 2):
					self.AppendTextLine(localeInfo.ATTR_6TH_7TH_POSSIBILITY, self.TEXTLINE_2ND_COLOR_DEFAULT)

	if app.ENABLE_APPLY_RANDOM:
		def __AppendDefaultItemApplyInformation(self, apply_random_list):
			if equipmentbonuspolicy.HasRetiredRandomApplies(self.itemVnum):
				return
			if apply_random_list != None:
				for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
					type = apply_random_list[i][0]
					value = apply_random_list[i][1]

					if 0 == value:
						continue

					affectString = self.__GetAffectString(type, value)
					if affectString:
						self.AppendTextLine(affectString, self.APPLY_RANDOM_TEXT_COLOR)

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			def __AppendAcceDefaultItemApplyInformation(self, apply_random_list, socketPercentage, sourceVnum):
				if equipmentbonuspolicy.HasRetiredRandomApplies(sourceVnum):
					return
				if apply_random_list != None:
					for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
						type = apply_random_list[i][0]
						value = apply_random_list[i][1]

						if 0 == value:
							continue

						affectValue = self.CalcAcceValue(value, socketPercentage)
						affectString = self.__GetAffectString(type, affectValue)
						if affectString:
							self.AppendTextLine(affectString, self.APPLY_RANDOM_TEXT_COLOR)

	if app.ENABLE_REFINE_ELEMENT_SYSTEM:
		def __AppendRefineElementInformation(self, refine_element):
			if not self.GetRefineElement(refine_element):
				return

			apply_type = refine_element[self.REFINE_ELEMENT_INDEX_APPLY_TYPE]
			grade = refine_element[self.REFINE_ELEMENT_INDEX_GRADE]
			value = 0
			for i in range(min(self.REFINE_ELEMENT_INDEX_MAX, grade)):
				value += refine_element[self.REFINE_ELEMENT_INDEX_VALUE][i]

			if self.isRefineElementItem:
				min_value = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_VALUE_MIN
				max_value = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_VALUE_MAX

				affect_string = self.__GetRefineElementValueText(apply_type, min_value, max_value, value)
				if affect_string:
					self.AppendTextLine(affect_string, self.REFINE_ELEMENT_COLOR_DICT[apply_type])
			else:
				affect_string = self.__GetAffectString(apply_type, value)
				if affect_string:
					self.AppendTextLine(affect_string, self.REFINE_ELEMENT_COLOR_DICT[apply_type])

		def __AppendRefineElementText(self, refine_element):
			if not self.GetRefineElement(refine_element):
				return

			apply_type = refine_element[self.REFINE_ELEMENT_INDEX_APPLY_TYPE]
			grade = refine_element[self.REFINE_ELEMENT_INDEX_GRADE]

			affect_string = self.__GetRefineElementText(apply_type, grade)
			if affect_string:
				self.AppendSpace(self.REFINE_ELEMENT_TITLE_TEXT_GAP)
				self.AppendTextLine(affect_string, self.REFINE_ELEMENT_COLOR_DICT[apply_type])

		def __GetRefineElementText(self, apply_type, grade):
			if apply_type == item.APPLY_ENCHANT_ELECT:
				return localeInfo.REFINE_ELEMENT_TEXT_ELECT % grade
			elif apply_type == item.APPLY_ENCHANT_FIRE:
				return localeInfo.REFINE_ELEMENT_TEXT_FIRE % grade
			elif apply_type == item.APPLY_ENCHANT_ICE:
				return localeInfo.REFINE_ELEMENT_TEXT_ICE % grade
			elif apply_type == item.APPLY_ENCHANT_WIND:
				return localeInfo.REFINE_ELEMENT_TEXT_WIND % grade
			elif apply_type == item.APPLY_ENCHANT_EARTH:
				return localeInfo.REFINE_ELEMENT_TEXT_EARTH % grade
			elif apply_type == item.APPLY_ENCHANT_DARK:
				return localeInfo.REFINE_ELEMENT_TEXT_DARK % grade
			else:
				return None

		def __GetRefineElementValueText(self, apply_type, min_value, max_value, value):
			min_value += value
			max_value += value

			if apply_type == item.APPLY_ENCHANT_ELECT:
				return localeInfo.TOOLTIP_APPLY_ENCHANT_ELECT2 % (min_value, max_value)
			elif apply_type == item.APPLY_ENCHANT_FIRE:
				return localeInfo.TOOLTIP_APPLY_ENCHANT_FIRE2 % (min_value, max_value)
			elif apply_type == item.APPLY_ENCHANT_ICE:
				return localeInfo.TOOLTIP_APPLY_ENCHANT_ICE2 % (min_value, max_value)
			elif apply_type == item.APPLY_ENCHANT_WIND:
				return localeInfo.TOOLTIP_APPLY_ENCHANT_WIND2 % (min_value, max_value)
			elif apply_type == item.APPLY_ENCHANT_EARTH:
				return localeInfo.TOOLTIP_APPLY_ENCHANT_EARTH2 % (min_value, max_value)
			elif apply_type == item.APPLY_ENCHANT_DARK:
				return localeInfo.TOOLTIP_APPLY_ENCHANT_DARK2 % (min_value, max_value)
			else:
				return " (+%d~+%d)" % (min_value, max_value)

		def GetRefineElement(self, real_refine_element):
			if not real_refine_element:
				return None

			if not isinstance(real_refine_element, (tuple, list)) or len(real_refine_element) < 4:
				return None

			try:
				apply_type = int(real_refine_element[self.REFINE_ELEMENT_INDEX_APPLY_TYPE])
				grade = int(real_refine_element[self.REFINE_ELEMENT_INDEX_GRADE])
			except (TypeError, ValueError, IndexError):
				return None

			if grade <= 0 or grade > self.REFINE_ELEMENT_INDEX_MAX:
				return None

			if apply_type not in uiRefine.REFINE_ELEMENT_KIND_TUPLE:
				return None

			values = real_refine_element[self.REFINE_ELEMENT_INDEX_VALUE]
			bonus = real_refine_element[self.REFINE_ELEMENT_INDEX_BONUS]
			if not isinstance(values, tuple) or not isinstance(bonus, tuple):
				return None

			max_value = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_VALUE_MAX
			max_bonus = uiRefine.RefineElementDialog.REFINE_ELEMENT_RANDOM_BONUS_VALUE_MAX

			for i in range(min(grade, self.REFINE_ELEMENT_INDEX_MAX)):
				if int(values[i]) < 0 or int(values[i]) > max_value:
					return None
				if int(bonus[i]) < 0 or int(bonus[i]) > max_bonus:
					return None

			return True

		def GetRefineElementCell(self, window_type, slot_index):
			if window_type == player.INVENTORY or window_type == player.EQUIPMENT:
				return player.GetItemRefineElement(window_type, slot_index)

	if app.ENABLE_ACCE_COSTUME_SYSTEM and app.ENABLE_REFINE_ELEMENT_SYSTEM:
		def __AppendRefineElementInformationAcce(self, metinSlot, refine_element):
			if refine_element == None:
				return

			absChance = int(metinSlot[acce.ABSORPTION_SOCKET])
			if absChance == 0:
				return

			apply_type = refine_element[self.REFINE_ELEMENT_INDEX_APPLY_TYPE]
			grade = refine_element[self.REFINE_ELEMENT_INDEX_GRADE]
			value = 0
			for i in range(min(self.REFINE_ELEMENT_INDEX_MAX, grade)):
				value += refine_element[self.REFINE_ELEMENT_INDEX_VALUE][i]

			value = self.CalcAcceValue(value, absChance)
			if value <= 0:
				return

			affect_string = self.__GetAffectString(apply_type, value)
			if affect_string:
				self.AppendTextLine(affect_string, self.REFINE_ELEMENT_COLOR_DICT[apply_type])

	if app.ENABLE_DS_SET:
		def __AppendDragonSoulAttributeInformation(self, attrSlot, dsType = 0, grade = 0):
			if 0 != attrSlot:
				if grade != 0:
					setWeightValue = item.GetDSSetWeight(dsType, grade)
					basicApplyCount = item.GetDSBasicApplyCount(dsType, grade)

					for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
						type = attrSlot[i][0]
						value = attrSlot[i][1]

						if 0 == value:
							continue

						affectString = self.__GetAffectString(type, value)
						if affectString:
							affectColor = self.__GetAttributeColor(i, type, value)

							setValue = 0
							if i < basicApplyCount:
								setValue = item.GetDSBasicApplyValue(dsType, type)
							else:
								setValue = item.GetDSAdditionalApplyValue(dsType, type)

							if setValue != 0:
								setValue = (setValue * setWeightValue - 1) // 100 + 1
								if affectString.find('%') == -1:
									self.AppendTwoColorTextLine(affectString, affectColor, " (+%d)" % (setValue))
								else:
									self.AppendTwoColorTextLine(affectString, affectColor, " (+%d%%)" % (setValue))
							else:
								self.AppendTextLine(affectString, affectColor)
				else:
					for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
						type = attrSlot[i][0]
						value = attrSlot[i][1]

						if 0 == value:
							continue

						affectString = self.__GetAffectString(type, value)
						if affectString:
							affectColor = self.__GetAttributeColor(i, type, value)
							self.AppendTextLine(affectString, affectColor)

	RESONANCE_CONTEXT_INVENTORY = 1
	RESONANCE_CONTEXT_SAFEBOX = 2
	RESONANCE_CONTEXT_EXCHANGE = 3
	RESONANCE_CONTEXT_EQUIPMENT = 4
	RESONANCE_CONTEXT_SHOP = 5
	RESONANCE_CONTEXT_MARKET = 6
	RESONANCE_BONUS_KEYS = (
		"RESONANCE_BONUS_DOMINANCE", "RESONANCE_BONUS_FURY",
		"RESONANCE_BONUS_ELEMENTS", "RESONANCE_BONUS_WAR",
		"RESONANCE_BONUS_DEFIANCE", "RESONANCE_BONUS_MYSTERY",
		"RESONANCE_BONUS_WIND", "RESONANCE_BONUS_KNOWLEDGE",
	)

	def __GetRarityGrade(self, windowType, slotIndex, rarityKey=None):
		if windowType == getattr(player, "SWITCHBOT", -100):
			from switchbotoptions import options
			return options.Rarity(slotIndex)[0]

		if rarityKey is None and (slotIndex is None or int(slotIndex) < 0):
			return 0
		getter = getattr(net, "GetRarityGrade", None)
		if not getter:
			return 0
		try:
			if rarityKey is None:
				rarityKey = (getattr(net, "RARITY_CONTEXT_INVENTORY", 1), windowType, slotIndex, 0, 0)
			return int(getter(*[int(value) for value in rarityKey]))
		except (TypeError, ValueError, RuntimeError):
			return 0

	def __GetResonanceMetadata(self, windowType, slotIndex, resonanceKey=None):
		empty = resonanceuihelpers.EMPTY_METADATA
		if not getattr(net, "IsResonanceAvailable", lambda: False)():
			return empty
		getter = getattr(net, "GetResonanceMetadata", None)
		if not getter:
			return empty
		if resonanceKey is None:
			if slotIndex is None or int(slotIndex) < 0:
				return empty
			resonanceKey = (self.RESONANCE_CONTEXT_INVENTORY, windowType, slotIndex, 0, 0)
		try:
			return resonanceuihelpers.NormalizeMetadata(
				getter(*[int(value) for value in resonanceKey])
			)
		except (AttributeError, TypeError, ValueError, RuntimeError):
			return empty

	def __AppendLooseResonanceSeal(self, sealVnum):
		bonus = resonanceuihelpers.GetSealBonus(sealVnum)
		if not bonus:
			return
		family, value = bonus
		if family >= len(self.RESONANCE_BONUS_KEYS):
			return
		pattern = getattr(localeInfo, self.RESONANCE_BONUS_KEYS[family], None)
		if pattern:
			self.AppendSpace(5)
			self.AppendTextLine(pattern % value, self.SPECIAL_POSITIVE_COLOR)

	def __AppendResonanceInformation(self, hostVnum, itemSubType, windowType,
			slotIndex, resonanceKey=None):
		if itemSubType not in (item.ARMOR_HEAD, item.ARMOR_SHIELD, item.ARMOR_FOOTS):
			return
		if not getattr(net, "IsResonanceAvailable", lambda: False)():
			return
		if resonanceKey is None and (slotIndex is None or int(slotIndex) < 0):
			return
		unusedInstanceId, unlockedMask, slots = self.__GetResonanceMetadata(windowType, slotIndex, resonanceKey)
		for slotIndex in range(3):
			if not (unlockedMask & (1 << slotIndex)):
				continue
			sealVnum, unusedBaseValue, effectiveValue = slots[slotIndex]
			self.__AppendResonanceSlot(sealVnum, effectiveValue)
		item.SelectItem(hostVnum)

	def __AppendResonanceSlot(self, sealVnum, effectiveValue):
		self.AppendSpace(5)
		sealName = localeInfo.TOOLTIP_SOCKET_EMPTY
		valueString = ""
		if sealVnum:
			item.SelectItem(int(sealVnum))
			sealName = item.GetItemName()
			family = max(0, min(7, (int(sealVnum) - 79640) // 6))
			pattern = getattr(localeInfo, self.RESONANCE_BONUS_KEYS[family], "+%d%%")
			valueString = pattern % int(effectiveValue)

		requiredWidth = self.RESONANCE_TOOLTIP_TEXT_X + max(
			app.GetTextWidth(sealName), app.GetTextWidth(valueString)
		) + self.RESONANCE_TOOLTIP_RIGHT_PADDING
		if requiredWidth > self.toolTipWidth:
			self.toolTipWidth = requiredWidth
			self.AlignTextLineHorizonalCenter()

		rowY = self.toolTipHeight
		slotImage = ui.ImageBox()
		slotImage.SetParent(self)
		slotImage.LoadImage(self.RESONANCE_TOOLTIP_SLOT_IMAGE)
		if localeInfo.IsARABIC():
			slotImage.SetPosition(self.toolTipWidth - slotImage.GetWidth() - 9, rowY - 1)
		else:
			slotImage.SetPosition(9, rowY - 1)
		slotImage.Show()
		self.childrenList.append(slotImage)

		nameText = ui.TextLine()
		nameText.SetParent(self)
		nameText.SetFontName(self.defFontName)
		nameText.SetPackedFontColor(self.NORMAL_COLOR)
		if localeInfo.IsARABIC():
			nameText.SetPosition(self.toolTipWidth - self.RESONANCE_TOOLTIP_TEXT_X, rowY + 2)
			nameText.SetHorizontalAlignRight()
		else:
			nameText.SetPosition(self.RESONANCE_TOOLTIP_TEXT_X, rowY + 2)
			nameText.SetHorizontalAlignLeft()
		nameText.SetOutline()
		nameText.SetFeather()
		nameText.Show()
		self.childrenList.append(nameText)

		sealIcon = ui.ImageBox()
		sealIcon.SetParent(self)
		sealIcon.Show()
		self.childrenList.append(sealIcon)

		if sealVnum:
			nameText.SetText(sealName)

			try:
				sealIcon.LoadImage(item.GetIconImageFileName())
			except:
				dbg.TraceError("ItemToolTip: missing resonance seal icon %d" % int(sealVnum))
			if localeInfo.IsARABIC():
				sealIcon.SetPosition(self.toolTipWidth - sealIcon.GetWidth() - 10, rowY)
			else:
				sealIcon.SetPosition(10, rowY)

			valueText = ui.TextLine()
			valueText.SetParent(self)
			valueText.SetFontName(self.defFontName)
			if localeInfo.IsARABIC():
				valueText.SetPosition(self.toolTipWidth - self.RESONANCE_TOOLTIP_TEXT_X, rowY + 18)
				valueText.SetHorizontalAlignRight()
			else:
				valueText.SetPosition(self.RESONANCE_TOOLTIP_TEXT_X, rowY + 18)
				valueText.SetHorizontalAlignLeft()
			valueText.SetPackedFontColor(self.POSITIVE_COLOR)
			valueText.SetOutline()
			valueText.SetFeather()
			valueText.SetText(valueString)
			valueText.Show()
			self.childrenList.append(valueText)
		else:
			nameText.SetText(localeInfo.TOOLTIP_SOCKET_EMPTY)

		self.toolTipHeight += 35
		self.ResizeToolTip()

	def __GetAttributeColor(self, index, affectType, value):
		# Maxima follow the family of the selected prototype (belt, glove,
		# talisman heart, Item Shop costume, mount, dragon soul ...).
		if index < 5 and itemattributemaxima.IsMaximum(
				itemattributemaxima.GetSelectedFamily(self.itemVnum), affectType, value):
			return self.MAXIMUM_ATTRIBUTE_COLOR
		if value > 0:
			if index >= 5 and self.rarityGrade > 0:
				gradeIndex = min(self.rarityGrade, len(RARITY_GRADE_COLORS) - 1)
				return RARITY_GRADE_COLORS[gradeIndex]
			if index >= 5:
				if app.ENABLE_ATTR_6TH_7TH and item.GetItemType() in [item.ITEM_TYPE_ARMOR, item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_COSTUME]:
					return self.ATTR_6TH_7TH_COLOR

				return self.SPECIAL_POSITIVE_COLOR2
			else:
				return self.SPECIAL_POSITIVE_COLOR
		elif value == 0:
			return self.NORMAL_COLOR
		else:
			return self.NEGATIVE_COLOR

	def __IsPolymorphItem(self, itemVnum):
		item.SelectItem(itemVnum)
		if item.GetItemType() == item.ITEM_TYPE_POLYMORPH:
			return 1
		return 0

	def __SetPolymorphItemTitle(self, monsterVnum):
		if localeInfo.IsVIETNAM():
			itemName =item.GetItemName()
			itemName+=" "
			itemName+=nonplayer.GetMonsterName(monsterVnum)
		else:
			itemName =nonplayer.GetMonsterName(monsterVnum)
			itemName+=" "
			itemName+=item.GetItemName()
		self.SetTitle(itemName)

	if osfInfo.ENABLE_ITEM_HIGHLIGHT_RENEWAL == True:
		def __CheckAntiFlag(self):
			race = player.GetRace()
			job = chr.RaceToJob(race)

			if item.IsAntiFlag(self.ANTI_FLAG_DICT[job]):
				return True
			else:
				return False

		def __CheckSex(self):
			sex = chr.RaceToSex(player.GetRace())
			MALE = 1
			FEMALE = 0
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE) and sex == MALE:
				return True
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE) and sex == FEMALE:
				return True

			return False

	def __SetNormalItemTitle(self):
		if osfInfo.ENABLE_ITEM_HIGHLIGHT_RENEWAL == True:
			if self.__CheckAntiFlag() == True:
				self.AppendTextLine(item.GetItemName(), self.DISABLE_COLOR)
			else:
				if self.__CheckSex() == True:
					self.AppendTextLine(item.GetItemName(), self.DISABLE_COLOR)
				else:
					self.AppendTextLine(item.GetItemName(), self.TITLE_COLOR)
		else:
			self.SetTitle(item.GetItemName())

	def __SetSpecialItemTitle(self):
		if osfInfo.ENABLE_ITEM_HIGHLIGHT_RENEWAL == True:
			if self.__CheckAntiFlag() == True:
				self.AppendTextLine(item.GetItemName(), self.DISABLE_COLOR)
			else:
				if self.__CheckSex() == True:
					self.AppendTextLine(item.GetItemName(), self.DISABLE_COLOR)
				else:
					self.AppendTextLine(item.GetItemName(), self.SPECIAL_TITLE_COLOR)
		else:
			self.AppendTextLine(item.GetItemName(), self.SPECIAL_TITLE_COLOR)

	def __SetItemTitle(self, itemVnum, metinSlot, attrSlot):
		if localeInfo.IsCANADA():
			if 72726 == itemVnum or 72730 == itemVnum:
				self.AppendTextLine(item.GetItemName(), grp.GenerateColor(1.0, 0.7843, 0.0, 1.0))
				return

		if self.__IsPolymorphItem(itemVnum):
			self.__SetPolymorphItemTitle(metinSlot[0])
		else:
			if self.__IsAttr(attrSlot):
				self.__SetSpecialItemTitle()
				return

			self.__SetNormalItemTitle()

	if app.ENABLE_ATTR_6TH_7TH:
		def __AppendAttribute6th7thPossibility(self, attrSlot):
			if 0 != attrSlot:
				attrCount = 0
				for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
					if 0 == attrSlot[i][1]:
						continue
					attrCount += 1

				if attrCount >= player.ATTRIBUTE_SLOT_MAX_NUM - 2 and attrCount < player.ATTRIBUTE_SLOT_MAX_NUM:
					self.AppendTextLine(localeInfo.ATTR_6TH_7TH_POSSIBILITY, self.ATTR_6TH_7TH_COLOR)

	def __IsAttr(self, attrSlot):
		if not attrSlot:
			return False

		## Item_name color is random. It needs to depend on bonuses
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			iType = attrSlot[i][0]
			val = attrSlot[i][1]
			if 0 != iType and val != 0:
				return True

		return False

	if app.ENABLE_BUFF_SYSTEM:
		def SetSupportEquipmentItem(self, itemVnum):
			self.ClearToolTip()
			
			metinSlot = []
			for i in range(player.METIN_SOCKET_MAX_NUM):
				metinSlot.append(0)
			attrSlot = []
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				attrSlot.append((0,0))
			
			self.AddItemData_Without_Bonus(itemVnum, True)

	if app.ENABLE_AURA_SYSTEM:
		def __GetAuraSocketValue(self, windowType, slotIndex, metinSlot, socketIndex):
			socketValue = metinSlot[socketIndex]
			if windowType == player.INVENTORY:
				liveValue = player.GetItemMetinSocket(windowType, slotIndex, socketIndex)
				if liveValue != 0:
					socketValue = liveValue
			elif windowType == player.AURA_REFINE:
				socketValue = player.GetAuraItemMetinSocket(slotIndex, socketIndex)
			elif windowType == player.SAFEBOX:
				socketValue = safebox.GetItemMetinSocket(slotIndex, socketIndex)
			return socketValue

		def __AppendAuraGameplayProgress(self, itemVnum, windowType, slotIndex, metinSlot):
			progressSocket = self.__GetAuraSocketValue(
				windowType, slotIndex, metinSlot, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
			absorption = self.__GetAuraAbsorptionPercent(itemVnum, windowType, slotIndex, metinSlot)

			self.AppendTextLine(
				localeInfo.AURA_GAMEPLAY_ABSORPTION % absorption,
				self.CONDITION_COLOR)
			(current, required) = auraprogression.Progress(itemVnum, progressSocket)
			if required == 0:
				self.AppendTextLine(
					localeInfo.AURA_GAMEPLAY_POINTS_MAX,
					self.CONDITION_COLOR)
			else:
				self.AppendTextLine(
					localeInfo.AURA_GAMEPLAY_POINTS % (current, required),
					self.CONDITION_COLOR)

		def __GetAuraAbsorptionPercent(self, itemVnum, windowType, slotIndex, metinSlot):
			boostSocket = self.__GetAuraSocketValue(
				windowType, slotIndex, metinSlot, player.ITEM_SOCKET_AURA_BOOST)
			absorption = auraprogression.AbsorptionPercent(itemVnum)
			if boostSocket != 0:
				boostIndex = boostSocket // 100000000
				boostItemVnum = boostIndex + item.AURA_BOOST_ITEM_VNUM_BASE
				item.SelectItem(boostItemVnum)
				absorption += item.GetValue(player.ITEM_VALUE_AURA_BOOST_PERCENT)
				item.SelectItem(itemVnum)
			return absorption

		def __AppendAuraAbsorbedBonuses(self, itemVnum, windowType, slotIndex, metinSlot, attrSlot):
			absorbedVnum = self.__GetAuraSocketValue(
				windowType, slotIndex, metinSlot, player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM)
			if not absorbedVnum:
				return

			absorption = self.__GetAuraAbsorptionPercent(itemVnum, windowType, slotIndex, metinSlot)
			item.SelectItem(absorbedVnum)
			absorbedAffects = []
			if item.GetItemType() == item.ITEM_TYPE_ARMOR and item.GetItemSubType() in (
				item.ARMOR_SHIELD, item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR):
				for index in range(item.ITEM_APPLY_MAX_NUM):
					(affectType, affectValue) = item.GetAffect(index)
					if affectType and affectType != item.APPLY_MOV_SPEED and affectValue > 0:
						absorbedAffects.append((affectType, max(1, int(affectValue * absorption / 100.0))))
			item.SelectItem(itemVnum)

			absorbedAttributes = []
			if attrSlot:
				for index, (affectType, affectValue) in enumerate(attrSlot):
					if affectType and affectValue > 0:
						absorbedAttributes.append((index, affectType, affectValue,
							max(1, int(affectValue * absorption / 100.0))))

			self.__AdjustMaxWidthFromAffectList(absorbedAffects + [
				(affectType, value) for _, affectType, _, value in absorbedAttributes])
			for affectType, value in absorbedAffects:
				affectString = self.__GetAffectString(affectType, value)
				if affectString:
					self.AppendTextLineAbsorb(affectString, self.GetChangeTextLineColor(value))
			for index, affectType, rawValue, value in absorbedAttributes:
				affectString = self.__GetAffectString(affectType, value)
				if affectString:
					self.AppendTextLineAbsorb(affectString, self.__GetAttributeColor(index, affectType, rawValue))

		def SetAuraWindowItem(self, slotIndex):
			itemVnum = player.GetAuraItemID(slotIndex)
			if 0 == itemVnum: return

			self.ClearToolTip()
			if shop.IsOpen() and not shop.IsPrivateShop():
				self.AppendSellingPrice(item.GetISellItemPrice(item.SelectItem(itemVnum)))

			metinSlot = [player.GetAuraItemMetinSocket(slotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = [player.GetAuraItemAttribute(slotIndex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]

			self.AddItemData(itemVnum, metinSlot, attrSlot, player.AURA_REFINE, slotIndex)

		def __AppendAffectInformationAura(self, windowType, slotIndex, metinSlot):
			socketLevelValue = 0
			socketBoostValue = 0
			if windowType == player.INVENTORY:
				socketLevelValue = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
				if metinSlot[player.ITEM_SOCKET_AURA_CURRENT_LEVEL] != 0 and socketLevelValue == 0:
					socketLevelValue = metinSlot[player.ITEM_SOCKET_AURA_CURRENT_LEVEL]
				socketBoostValue = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_BOOST)
				if metinSlot[player.ITEM_SOCKET_AURA_BOOST] != 0 and socketBoostValue == 0:
					socketBoostValue = metinSlot[player.ITEM_SOCKET_AURA_BOOST]
			elif windowType == player.AURA_REFINE:
				socketLevelValue = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
				socketBoostValue = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)
			elif windowType == player.SAFEBOX:
				socketLevelValue = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
				socketBoostValue = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)

			if socketLevelValue == 0:
				return

			curLevel = (socketLevelValue // 100000) - 1000
			curStep = player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_STEP)
			if curStep < item.AURA_GRADE_RADIANT:
				curExpPer = 100.0 * (socketLevelValue % 100000) / player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_NEED_EXP)

			self.AppendTextLine(localeInfo.AURA_LEVEL_STEP % (curLevel, curStep), self.CONDITION_COLOR)
			if curStep < item.AURA_GRADE_RADIANT:
				self.AppendTextLine(localeInfo.AURA_TOOLTIP_EXP % (curExpPer), self.CONDITION_COLOR)

			boostPercent = 0
			if socketBoostValue != 0:
				curBoostIndex = socketBoostValue // 100000000
				boostItemVnum = curBoostIndex + item.AURA_BOOST_ITEM_VNUM_BASE
				if boostItemVnum:
					item.SelectItem(boostItemVnum)
					boostPercent = item.GetValue(player.ITEM_VALUE_AURA_BOOST_PERCENT)

			if boostPercent > 0:
				self.AppendTextLine(localeInfo.AURA_DRAIN_BOOST_PER % (1.0 * curLevel / 10, boostPercent), self.CONDITION_COLOR)
			else:
				self.AppendTextLine(localeInfo.AURA_DRAIN_PER % (1.0 * curLevel / 10), self.CONDITION_COLOR)

		def __AppendAuraItemAffectInformation(self, oriItemVnum, windowType, slotIndex, metinSlot):
			socketLevelValue = 0
			socketBoostValue = 0
			if windowType == player.INVENTORY:
				socketLevelValue = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
				if metinSlot[player.ITEM_SOCKET_AURA_CURRENT_LEVEL] != 0 and socketLevelValue == 0:
					socketLevelValue = metinSlot[player.ITEM_SOCKET_AURA_CURRENT_LEVEL]
				socketBoostValue = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_BOOST)
				if metinSlot[player.ITEM_SOCKET_AURA_BOOST] != 0 and socketBoostValue == 0:
					socketBoostValue = metinSlot[player.ITEM_SOCKET_AURA_BOOST]
			elif windowType == player.AURA_REFINE:
				socketLevelValue = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
				socketBoostValue = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)
			elif windowType == player.SAFEBOX:
				socketLevelValue = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
				socketBoostValue = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)

			if socketLevelValue == 0:
				return

			curLevel = (socketLevelValue // 100000) - 1000
			boostPercent = 0.0
			if socketBoostValue != 0:
				curBoostIndex = socketBoostValue // 100000000
				boostItemVnum = curBoostIndex + item.AURA_BOOST_ITEM_VNUM_BASE
				if boostItemVnum:
					item.SelectItem(boostItemVnum)
					boostPercent = item.GetValue(player.ITEM_VALUE_AURA_BOOST_PERCENT) / 100.0

			drainlate = curLevel / 10. / 100. + boostPercent

			socketInDrainItemVnum = 0
			if windowType == player.INVENTORY:
				socketInDrainItemVnum = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM)
				if not metinSlot[player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM] == 0 and socketInDrainItemVnum == 0:
					socketInDrainItemVnum = metinSlot[player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM]
			elif windowType == player.AURA_REFINE:
				socketInDrainItemVnum = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM)
			elif windowType == player.SAFEBOX:
				socketInDrainItemVnum = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM)

			if socketInDrainItemVnum == 0:
				return

			item.SelectItem(socketInDrainItemVnum)
			itemType = item.GetItemType()
			if itemType == item.ITEM_TYPE_ARMOR:
				defBonus = item.GetValue(5)*2
				if item.GetValue(1) >= 1:
					defGrade = max(((item.GetValue(1) + defBonus) * drainlate) , 1)
					if defGrade > 0:
						self.AppendSpace(5)
						self.AppendTextLineAbsorb(localeInfo.TOOLTIP_ITEM_DEF_GRADE % (defGrade), self.GetChangeTextLineColor(defGrade))

			for i in range(item.ITEM_APPLY_MAX_NUM):
				(affectType, affectValue) = item.GetAffect(i)
				if affectValue > 0:
					affectValue = max((affectValue * drainlate), 1)
					affectString = self.__GetAffectString(affectType, affectValue)
					if affectString:
						self.AppendTextLineAbsorb(affectString, self.GetChangeTextLineColor(affectValue))

			item.SelectItem(oriItemVnum)

		def __AppendAttributeInformationAura(self, windowType, slotIndex, attrSlot, metinSlot):
			if 0 != attrSlot:
				socketLevelValue = 0
				socketBoostValue = 0
				if windowType == player.INVENTORY:
					socketLevelValue = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
					socketBoostValue = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_BOOST)
					if metinSlot[player.ITEM_SOCKET_AURA_CURRENT_LEVEL] != 0 and socketLevelValue == 0:
						socketLevelValue = metinSlot[player.ITEM_SOCKET_AURA_CURRENT_LEVEL]
					if metinSlot[player.ITEM_SOCKET_AURA_BOOST] != 0 and socketBoostValue == 0:
						socketBoostValue = metinSlot[player.ITEM_SOCKET_AURA_BOOST]
				elif windowType == player.AURA_REFINE:
					socketLevelValue = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
					socketBoostValue = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)
				elif windowType == player.SAFEBOX:
					socketLevelValue = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
					socketBoostValue = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)

				if socketLevelValue == 0:
					return

				curLevel = (socketLevelValue // 100000) - 1000
				boostPercent = 0.0
				if socketBoostValue != 0:
					curBoostIndex = socketBoostValue // 100000000
					boostItemVnum = curBoostIndex + item.AURA_BOOST_ITEM_VNUM_BASE
					if boostItemVnum:
						item.SelectItem(boostItemVnum)
						boostPercent = item.GetValue(player.ITEM_VALUE_AURA_BOOST_PERCENT) / 100.0

				drainlate = curLevel / 10. / 100. + boostPercent

				for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
					type = attrSlot[i][0]
					value = attrSlot[i][1]
					rawValue = value
					if 0 >= value:
						continue

					value = max(((value) * drainlate) , 1)
					affectString = self.__GetAffectString(type, value)

					if affectString:
						affectColor = self.__GetAttributeColor(i, type, rawValue)
						self.AppendTextLine(affectString, affectColor)

		def __AppendAuraBoostMetinSlotInfo(self, oriItemVnum, windowType, slotIndex, metinSlot):
			socketBoostValue = 0
			if windowType == player.INVENTORY:
				socketBoostValue = player.GetItemMetinSocket(windowType, slotIndex, player.ITEM_SOCKET_AURA_BOOST)
				if metinSlot[player.ITEM_SOCKET_AURA_BOOST] != 0 and socketBoostValue == 0:
					socketBoostValue = metinSlot[player.ITEM_SOCKET_AURA_BOOST]
			elif windowType == player.AURA_REFINE:
				socketBoostValue = player.GetAuraItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)
			elif windowType == player.SAFEBOX:
				socketBoostValue = safebox.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_BOOST)

			if socketBoostValue == 0:
				return

			curBoostIndex = socketBoostValue // 100000000

			socketImageDict = {
				player.METIN_SOCKET_TYPE_SILVER : "d:/ymir work/ui/game/windows/metin_slot_silver.sub",
				player.METIN_SOCKET_TYPE_GOLD : "d:/ymir work/ui/game/windows/metin_slot_gold.sub",
			}
			socketType = player.METIN_SOCKET_TYPE_NONE
			if item.ITEM_AURA_BOOST_ERASER < curBoostIndex < item.ITEM_AURA_BOOST_ULTIMATE:
				socketType = player.METIN_SOCKET_TYPE_SILVER
			elif curBoostIndex == item.ITEM_AURA_BOOST_ULTIMATE:
				socketType = player.METIN_SOCKET_TYPE_GOLD

			if player.METIN_SOCKET_TYPE_NONE == socketType:
				return

			boostRemainTime = socketBoostValue % 100000000
			boostItemVnum = curBoostIndex + item.AURA_BOOST_ITEM_VNUM_BASE

			self.AppendSpace(5)

			slotImage = ui.ImageBox()
			slotImage.SetParent(self)
			slotImage.LoadImage(socketImageDict[socketType])
			slotImage.Show()
			self.childrenList.append(slotImage)

			## Name
			nameTextLine = ui.TextLine()
			nameTextLine.SetParent(self)
			nameTextLine.SetFontName(self.defFontName)
			nameTextLine.SetPackedFontColor(self.NORMAL_COLOR)
			nameTextLine.SetOutline()
			nameTextLine.SetFeather()
			nameTextLine.Show()
			self.childrenList.append(nameTextLine)

			if localeInfo.IsARABIC():
				slotImage.SetPosition(self.toolTipWidth - slotImage.GetWidth() - 9, self.toolTipHeight-1)
				nameTextLine.SetPosition(self.toolTipWidth - 50, self.toolTipHeight + 2)
			else:
				slotImage.SetPosition(9, self.toolTipHeight-1)
				nameTextLine.SetPosition(50, self.toolTipHeight + 2)

			boostItemImage = ui.ImageBox()
			boostItemImage.SetParent(self)
			boostItemImage.Show()
			self.childrenList.append(boostItemImage)

			if boostItemVnum:
				item.SelectItem(boostItemVnum)
				try:
					boostItemImage.LoadImage(item.GetIconImageFileName())
				except:
					dbg.TraceError("ItemToolTip.__AppendAuraBoostMetinSlotInfo() - Failed to find image file %d:%s" % (boostItemVnum, item.GetIconImageFileName()))

				nameTextLine.SetText(item.GetItemName())

				boostDrainTextLine = ui.TextLine()
				boostDrainTextLine.SetParent(self)
				boostDrainTextLine.SetFontName(self.defFontName)
				boostDrainTextLine.SetPackedFontColor(self.POSITIVE_COLOR)
				boostDrainTextLine.SetOutline()
				boostDrainTextLine.SetFeather()
				boostDrainTextLine.SetText(localeInfo.AURA_BOOST_DRAIN_PER % (item.GetValue(player.ITEM_VALUE_AURA_BOOST_PERCENT)))
				boostDrainTextLine.Show()
				self.childrenList.append(boostDrainTextLine)

				if localeInfo.IsARABIC():
					boostItemImage.SetPosition(self.toolTipWidth - boostItemImage.GetWidth() - 10, self.toolTipHeight)
					boostDrainTextLine.SetPosition(self.toolTipWidth - 50, self.toolTipHeight + 16 + 2)
				else:
					boostItemImage.SetPosition(10, self.toolTipHeight)
					boostDrainTextLine.SetPosition(50, self.toolTipHeight + 16 + 2)

				if 1 == item.GetValue(player.ITEM_VALUE_AURA_BOOST_UNLIMITED):
					boostRemainTime = 0

				if 0 != boostRemainTime:
					timeText = (localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(boostRemainTime))

					timeTextLine = ui.TextLine()
					timeTextLine.SetParent(self)
					timeTextLine.SetFontName(self.defFontName)
					timeTextLine.SetPackedFontColor(self.POSITIVE_COLOR)
					timeTextLine.SetPosition(50, self.toolTipHeight + 16 + 2 + 16 + 2)
					timeTextLine.SetOutline()
					timeTextLine.SetFeather()
					timeTextLine.Show()
					timeTextLine.SetText(timeText)
					self.childrenList.append(timeTextLine)
					self.toolTipHeight += 16 + 2

			self.toolTipHeight += 35
			self.ResizeToolTip()

	def __AppendTradeabilityInformation(self):
		try:
			blocked = item.IsAntiFlag(item.ITEM_ANTIFLAG_GIVE) or \
				item.IsAntiFlag(item.ITEM_ANTIFLAG_MYSHOP)
		except:
			return
		self.AppendSpace(5)
		if blocked:
			self.AppendTextLine(
				getattr(localeInfo, "TOOLTIP_ITEM_NOT_TRADEABLE", "Not tradeable"),
				self.NEGATIVE_COLOR)
		else:
			self.AppendTextLine(
				getattr(localeInfo, "TOOLTIP_ITEM_TRADEABLE", "Tradeable"),
				self.POSITIVE_COLOR)

	def AddRefineItemData(self, item_vnum, sockets, attributes, rare_attr_slot = None, flags = 0, refine_element = None, apply_random_list = None, set_value = 0):
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlotData = sockets[i]
			if self.GetMetinItemIndex(metinSlotData) == constInfo.ERROR_METIN_STONE:
				sockets[i] = player.METIN_SOCKET_TYPE_SILVER

		self.AddItemData(item_vnum, sockets, attributes, rare_attr_slot, 0, 0, player.INVENTORY, -1, refine_element, apply_random_list, set_value)

	def AddItemData_Offline(self, itemVnum, itemDesc, itemSummary, metinSlot, attrSlot):
		self.__AdjustMaxWidth(attrSlot, itemDesc)
		self.__SetItemTitle(itemVnum, metinSlot, attrSlot)

		if self.__IsHair(itemVnum):
			self.__AppendHairIcon(itemVnum)

		### Description ###
		self.AppendDescription(itemDesc, 26)
		self.AppendDescription(itemSummary, 26, self.CONDITION_COLOR)

	if app.ENABLE_SOUL_SYSTEM:
		def __SoulItemToolTip(self, itemVnum, metinSlot, flags):
			self.itemVnum = itemVnum
			item.SelectItem(itemVnum)
			itemType = item.GetItemType()
			itemSubType = item.GetItemSubType()

			(limit_Type, limit_Value) = item.GetLimit(1)
			max_time = limit_Value

			if 0 != flags:
				metinSlot[2] = item.GetValue(2)

			data = metinSlot[2]
			keep_time = data // 10000
			remain_count = data % 10000

			## value3,4,5
			value_index = 2 + keep_time // 60
			if value_index < 3:
				value_index = 3
			if value_index > 5:
				value_index = 5
			damage_value = float(item.GetValue(value_index) / 10.0)

			self.ClearToolTip()
			## board size
			soul_desc = ""
			if item.RED_SOUL == itemSubType:
				soul_desc = localeInfo.SOUL_ITEM_TOOLTIP_RED1 % (keep_time, max_time)
				soul_desc += localeInfo.SOUL_ITEM_TOOLTIP_RED2 % (damage_value)
			elif item.BLUE_SOUL == itemSubType:
				soul_desc = localeInfo.SOUL_ITEM_TOOLTIP_BLUE1 % (keep_time, max_time)
				soul_desc += localeInfo.SOUL_ITEM_TOOLTIP_BLUE2 % (damage_value)

			self.__AdjustMaxWidth(0, soul_desc)

			## 아이템 이름
			self.__SetNormalItemTitle()

			## desc
			board_width = self.__AdjustDescMaxWidth(soul_desc)
			if keep_time < 60:
				desc_color = 0xfff15f5f # RGB(241,95,95)
			else:
				desc_color = 0xff86e57f # RGB(134,229,127)

			self.AppendDescription(soul_desc, 26, desc_color)

			## PVP,변신,마운트 미적용
			self.AppendDescription(localeInfo.SOUL_ITEM_TOOLTIP_COMMON, 26, 0xfff15f5f) # RGB(241,95,95)
			self.AppendSpace(10)

			## 효과 적용/미적용
			if metinSlot[1] and keep_time >= 60 and remain_count > 0:
				self.AppendTextLine(localeInfo.SOUL_ITEM_TOOLTIP_APPLY, 0xff86e57f ) # RGB(134,229,127)
			else:
				self.AppendTextLine(localeInfo.SOUL_ITEM_TOOLTIP_UNAPPLIED, 0xfff15f5f ) # RGB(241,95,95)
			self.AppendSpace(5)

			## 남은 횟수 
			self.AppendTextLine(localeInfo.SOUL_ITEM_TOOLTIP_REMAIN_COUNT % remain_count)
			self.AppendSpace(5)

			## 남은 시간
			if 0 == flags:
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)
					if item.LIMIT_REAL_TIME == limitType:
						self.AppendSoulItemLastTime(metinSlot[0])
			else:
				(limitType, limitValue) = item.GetLimit(0)
				self.AppendSoulItemLastTime(limitValue + app.GetGlobalTimeStamp())

			self.__AppendTradeabilityInformation()
			self.ShowToolTip()

		def AppendSoulItemLastTime(self, endTime):
			leftSec = max(0, endTime - app.GetGlobalTimeStamp())
			if leftSec > 0:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.SOUL_ITEM_TOOLTIP_REMOVE_TIME + " : " + localeInfo.SecondToDHM(leftSec), self.NORMAL_COLOR)

	def SetItemOnlyVnum(self, itemVnum):
		self.ClearToolTip()
		
		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(0)
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append((0,0))
		
		self.AddItemData_Without_Bonus(itemVnum, False)

	def AddItemData_Without_Bonus(self, itemVnum, isShamanEquipment = False):
		self.itemVnum = itemVnum
		item.SelectItem(itemVnum)
		itemType = item.GetItemType()
		itemSubType = item.GetItemSubType()
		itemDesc = item.GetItemDescription()
		itemSummary = item.GetItemSummary()

		if app.ENABLE_AURA_SYSTEM and item.ITEM_TYPE_COSTUME == itemType and item.COSTUME_TYPE_AURA == itemSubType:
			itemDesc = ""
			itemSummary = ""
		
		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.savedItemVnum = 0
			osfInfo.RENDER_TARGET_ITEM_TYPE = 0
			
		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(0)
		attrSlot = []
		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append((0,0))
			
		self.__AdjustMaxWidth(attrSlot, itemDesc)
		self.__SetItemTitle(itemVnum, metinSlot, attrSlot)
		
		### Description ###
		self.AppendDescription(itemDesc, 26)
		self.AppendDescription(itemSummary, 26, self.CONDITION_COLOR)
		
		if isShamanEquipment and itemVnum not in (49101, 49102, 49104, 49106, 49109):
			self.AppendTextLine(localeInfo.SKILL_TOOLTIP_INT + " +10", self.SPECIAL_POSITIVE_COLOR)
		
		if osfInfo.SHOW_ITEM_VNUM_TOOTIP == True:
			if chr.IsGameMaster(player.GetMainCharacterIndex()):
				self.AppendSpace(5)		
				self.AppendTextLine("Vnum: %d" % itemVnum, grp.GenerateColor(0.6705, 0.9490, 0.0, 1.0))
				self.AppendTextLine("ItemType: %s" % itemType, grp.GenerateColor(0.6705, 0.9490, 0.0, 1.0))
				self.AppendTextLine("ItemSubType: %s" % itemSubType, grp.GenerateColor(0.6705, 0.9490, 0.0, 1.0))
		
		self.ShowToolTip()

	def __AppendSageReadingTerms(self, itemVnum):
		if itemVnum != sagebuff.STONE_VNUM:
			return
		from settingslocale import Text as T
		material, required, cap = sagebuff.ReadingTerms(item)
		if material <= 0 or required <= 0 or cap <= 0:
			return
		name = item.GetItemNameByVnum(material)
		item.SelectItem(itemVnum)
		self.AppendDescription(T("Každý pokus spotřebuje i %dx %s.",
			"Each attempt also consumes %dx %s.") % (required, name), 26, self.CONDITION_COLOR)
		self.AppendDescription(T("P1 až S: nejvýše %d kamenů duše (S).",
			"P1 to S: at most %d Sage Soul Stones.") % cap, 26, self.CONDITION_COLOR)

	def AddItemData(self, itemVnum, metinSlot, attrSlot = 0, rare_attr_slot = None, flags = 0, unbindTime = 0, window_type = player.INVENTORY, slotIndex = -1, refine_element = None, apply_random_list = None, set_value = 0, rarity_key = None, resonance_key = None, deferMountPreview = False, rarity_preview_grade = None):
		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.__RemoveMountPreview()
			self.mountPreviewRace = 0
			self.__RemoveCostumePreview()
		self.costumePreviewVnum = 0
		self.itemVnum = itemVnum
		self.weaponBasePercent = self.__EquippedWeaponPercent(window_type, slotIndex, rarity_key, rarity_preview_grade)
		self.metinSlot = metinSlot
		self.attrSlot = attrSlot
		self.rarityGrade = (int(rarity_preview_grade) if rarity_preview_grade is not None
			else self.__GetRarityGrade(window_type, slotIndex, rarity_key))
		if rarity_preview_grade is None and self.rarityGrade >= 3 and getattr(net, "GetRarityExtra", None):
			key = rarity_key
			if key is None and slotIndex is not None and int(slotIndex) >= 0:
				key = (1, window_type, slotIndex, 0, 0)
			if key is not None:
				extra = GetRarityExtraSafe(*key)
				if window_type == getattr(player, "SWITCHBOT", -100):
					from switchbotoptions import options
					extra = options.Rarity(slotIndex)[1]

				if extra is not None:
					attrSlot = list(attrSlot) if attrSlot else [(0, 0)] * 7
					attrSlot = attrSlot[:7] + [extra]
					self.attrSlot = attrSlot
		if resonance_key is None and rarity_key is not None and int(rarity_key[0]) <= 6:
			resonance_key = rarity_key

		item.SelectItem(itemVnum)
		itemType = item.GetItemType()
		itemSubType = item.GetItemSubType()
		if self.__IsCostumeMount():
			attrSlot = mountspeedtooltip.FilterMountAttributes(attrSlot, item.APPLY_MOV_SPEED)
			self.attrSlot = attrSlot
			rare_attr_slot = None
			apply_random_list = None


		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.savedItemVnum = itemVnum
			osfInfo.RENDER_TARGET_ITEM_TYPE = 0

		self.__CalculateToolTipWidth()

		if 50026 == itemVnum:
			if 0 != metinSlot:
				name = item.GetItemName()
				if metinSlot[0] > 0:
					name += " "
					name += localeInfo.NumberToMoneyString(metinSlot[0])
				self.SetTitle(name)
				if app.ENABLE_SOUL_BIND_SYSTEM:
					self.AppendSealInformation(window_type, slotIndex) ## cyh itemseal 2013 11 11
				self.__AppendTradeabilityInformation()
				self.ShowToolTip()
			return

		if itemType == item.ITEM_TYPE_SKILLBOOK and ICON_SKILLBOOK_VNUM_MIN <= itemVnum <= ICON_SKILLBOOK_VNUM_MAX:
			skillBookSkillIndex = item.GetValue(0)
			if skillBookSkillIndex > 0:
				self.__SetSkillBookToolTip(skillBookSkillIndex, localeInfo.TOOLTIP_SKILLBOOK_NAME, 1)
				self.AppendDescription(item.GetItemDescription(), 26)
				self.AppendDescription(item.GetItemSummary(), 26, self.CONDITION_COLOR)
				if app.ENABLE_SOUL_BIND_SYSTEM:
					self.AppendSealInformation(window_type, slotIndex)
				self.__AppendTradeabilityInformation()
				self.ShowToolTip()
				return

		if app.ENABLE_SEND_TARGET_INFO:
			if itemType == item.ITEM_TYPE_SKILLBOOK or itemType == item.ITEM_TYPE_SKILLFORGET:
				if metinSlot != 0 and metinSlot[0] == 0:
					self.SetItemToolTipBook(itemVnum)
					return

		### Skill Book ###
		if 50300 == itemVnum:
			if 0 != metinSlot:
				self.__SetSkillBookToolTip(metinSlot[0], localeInfo.TOOLTIP_SKILLBOOK_NAME, 1)
				if app.ENABLE_SOUL_BIND_SYSTEM:
					self.AppendSealInformation(window_type, slotIndex) ## cyh itemseal 2013 11 11
				self.__AppendTradeabilityInformation()
				self.ShowToolTip()
			return
		elif 70037 == itemVnum:
			if 0 != metinSlot:
				self.__SetSkillBookToolTip(metinSlot[0], localeInfo.TOOLTIP_SKILL_FORGET_BOOK_NAME, 0)
				self.AppendDescription(item.GetItemDescription(), 26)
				self.AppendDescription(item.GetItemSummary(), 26, self.CONDITION_COLOR)
				if app.ENABLE_SOUL_BIND_SYSTEM:
					self.AppendSealInformation(window_type, slotIndex) ## cyh itemseal 2013 11 11
				self.__AppendTradeabilityInformation()
				self.ShowToolTip()
			return
		elif 70055 == itemVnum:
			if 0 != metinSlot:
				self.__SetSkillBookToolTip(metinSlot[0], localeInfo.TOOLTIP_SKILL_FORGET_BOOK_NAME, 0)
				self.AppendDescription(item.GetItemDescription(), 26)
				self.AppendDescription(item.GetItemSummary(), 26, self.CONDITION_COLOR)
				if app.ENABLE_SOUL_BIND_SYSTEM:
					self.AppendSealInformation(window_type, slotIndex) ## cyh itemseal 2013 11 11
				self.__AppendTradeabilityInformation()
				self.ShowToolTip()
			return
		###########################################################################################

		if app.ENABLE_SOUL_SYSTEM:
			if item.ITEM_TYPE_SOUL == itemType:
				self.__SoulItemToolTip(itemVnum, metinSlot, flags)
				return

		if slotIndex == -1:
			itemDesc = item.GetItemDescription()
		else:
			itemDesc = item.GetItemDescription(slotIndex, window_type)

		itemSummary = item.GetItemSummary()

		isCostumeItem = 0
		isCostumeHair = 0
		isCostumeBody = 0
		isCostumeMount = 0
		isCostumePet = 0
		isCostumeAcce = 0
		isCostumeWeapon = 0
		if app.ENABLE_AURA_SYSTEM:
			isCostumeAura = 0

		if item.ITEM_TYPE_COSTUME == itemType:
			isCostumeItem = 1
			isCostumeHair = item.COSTUME_TYPE_HAIR == itemSubType
			isCostumeBody = item.COSTUME_TYPE_BODY == itemSubType
			if app.ENABLE_MOUNT_COSTUME_SYSTEM:
				isCostumeMount = item.COSTUME_TYPE_MOUNT == itemSubType
			if item.COSTUME_TYPE_PET == itemSubType:
				isCostumePet = 1
			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				isCostumeAcce = item.COSTUME_TYPE_ACCE == itemSubType
			if app.ENABLE_WEAPON_COSTUME_SYSTEM:
				isCostumeWeapon = item.COSTUME_TYPE_WEAPON == itemSubType
			if app.ENABLE_ACCE_SKIN_SYSTEM:
				isCostumeSkinAcce = item.COSTUME_TYPE_ACCE_SKIN == itemSubType
			if app.ENABLE_SPECIAL_SHINING_SYSTEM:
				isWeaponEffect = item.COSTUME_TYPE_EFFECT_WEAPON == itemSubType
				isArmorEffect = item.COSTUME_TYPE_EFFECT_ARMOR == itemSubType
			if app.ENABLE_AURA_SYSTEM:
				isCostumeAura = item.COSTUME_TYPE_AURA == itemSubType

			if app.ENABLE_RENDER_TARGET_PREVIEW:
				if isCostumeHair:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 3
				elif isCostumeBody:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 2
				elif isCostumeWeapon:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 1
				elif isCostumeAcce:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 4
				elif isCostumeSkinAcce:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 4
				elif isWeaponEffect:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 5
				elif isArmorEffect:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 6
				elif isCostumePet:
					osfInfo.RENDER_TARGET_ITEM_TYPE = 20
					self.savedItemVnum = item.GetValue(0)
				elif isCostumeMount:
					self.mountPreviewRace = item.GetValue(1)
					self.savedItemVnum = self.mountPreviewRace
					osfInfo.RENDER_TARGET_ITEM_TYPE = 20

		if app.ENABLE_AURA_SYSTEM and isCostumeAura:
			itemDesc = ""
			itemSummary = ""

		costumeVoucher = self.__ResolveCostumeVoucher(itemVnum, isCostumeItem)
		if costumeVoucher and self.costumeVoucherOffer:
			# The offer's own costume description names only the PvM bonus;
			# the voucher block below describes both choices instead.
			itemDesc = ""
			itemSummary = ""

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			if self.mountPreviewRace > 0:
				self.toolTipWidth = max(
					self.toolTipWidth, self.MOUNT_PREVIEW_TOOLTIP_WIDTH
				)
			elif self.costumePreviewVnum > 0:
				self.toolTipWidth = max(
					self.toolTipWidth, self.COSTUME_PREVIEW_TOOLTIP_WIDTH
				)

		self.__AdjustMaxWidth(attrSlot, itemDesc)
		self.__SetItemTitle(itemVnum, metinSlot, attrSlot)
		if self.rarityGrade > 0 and not (app.ENABLE_AURA_SYSTEM and isCostumeAura):
			gradeIndex = min(self.rarityGrade, len(RARITY_GRADE_NAMES) - 1)
			self.AppendTextLine(localeInfo.RARITY_TOOLTIP_GRADE % RARITY_GRADE_NAMES[gradeIndex],
				RARITY_GRADE_COLORS[gradeIndex])

		if app.ENABLE_GROWTH_PET_SYSTEM and item.ITEM_TYPE_PET == itemType:
			if item.PET_UPBRINGING == itemSubType:
			
				pet_id = metinSlot[2]
				if pet_id:
					(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
					
					self.ClearToolTip()
					self.AppendTextLine(pet_nick, self.TITLE_COLOR)

		### Hair Preview Image ###
		if self.__IsHair(itemVnum):
			self.__AppendHairIcon(itemVnum)
			if app.ENABLE_RENDER_TARGET_PREVIEW:
				osfInfo.RENDER_TARGET_ITEM_TYPE = 3

		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			self.__AppendRefineElementText(refine_element)

		### Description ###
		if not app.ENABLE_AURA_SYSTEM or not isCostumeAura:
			self.AppendDescription(itemDesc, 26)
			self.AppendDescription(itemSummary, 26, self.CONDITION_COLOR)
			self.__AppendSageReadingTerms(itemVnum)

		if costumeVoucher:
			self.__AppendCostumeVoucherInformation(itemVnum, costumeVoucher)

		# Server-owned pickup deadlines; the runestone's old UNIQUE timer is unrelated.
		if itemVnum in (33046, 30139, 33102, 33050, 33092, 30998):
			deadline = metinSlot[0] if metinSlot else 0
			self.AppendMallItemLastTime(deadline if deadline > 0 else 300, deadline <= 0)

		### Weapon ###
		elif item.ITEM_TYPE_WEAPON == itemType:
			self.__AppendLimitInformation()

			self.AppendSpace(5)

			## 부채일 경우 마공을 먼저 표시한다.
			if item.WEAPON_FAN == itemSubType:
				self.__AppendMagicAttackInfo()
				if app.ENABLE_ACCE_COSTUME_SYSTEM:
					self.__AppendAttackPowerInfo(0, refine_element)
				else:
					self.__AppendAttackPowerInfo(refine_element)
			else:
				if app.ENABLE_ACCE_COSTUME_SYSTEM:
					self.__AppendAttackPowerInfo(0, refine_element)
				else:
					self.__AppendAttackPowerInfo(refine_element)
				self.__AppendMagicAttackInfo()

			self.__AppendAffectInformation()
			if app.ENABLE_APPLY_RANDOM:
				self.__AppendDefaultItemApplyInformation(apply_random_list)
			if app.ENABLE_REFINE_ELEMENT_SYSTEM:
				self.__AppendRefineElementInformation(refine_element)
			self.__AppendAttributeInformation(attrSlot)
			if app.ENABLE_ATTR_6TH_7TH:
				self.__AppendAttribute6th7thPossibility(attrSlot)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				self.AppendChangeLookInformation(window_type, slotIndex)

			self.AppendWearableInformation()

			# ALTHEA-641: arrows and quivers are retired; a bow is always loaded.
			if virtualquiver.IsRetiredAmmo(itemType, itemSubType):
				self.AppendSpace(5)
				self.AppendTextLine(virtualquiver.NoLongerNeededText(), self.NEGATIVE_COLOR)

			bHasRealtimeFlag = 0
			originalTimeLimit = 0
			if app.ENABLE_QUIVER_SYSTEM:
				if item.WEAPON_QUIVER == itemSubType:
					if not self.isShopItem:
						## 사용가능 시간 제한이 있는지 찾아보고
						if 1 == bHasRealtimeFlag:
							if metinSlot[0] == 0:
								self.AppendMallItemLastTime(originalTimeLimit, True)
							else:
								self.AppendMallItemLastTime(metinSlot[0])
				else:
					for i in range(item.LIMIT_MAX_NUM):
						(limitType, limitValue) = item.GetLimit(i)

						if item.LIMIT_REAL_TIME == limitType:
							bHasRealtimeFlag = 1

					if 1 != bHasRealtimeFlag:
						self.__AppendMetinSlotInfo(metinSlot)
			else:
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_REAL_TIME == limitType:
						bHasRealtimeFlag = 1

				if 1 != bHasRealtimeFlag:
					self.__AppendMetinSlotInfo(metinSlot)

			if app.WJ_NEW_USER_CARE:
				if item.WEAPON_QUIVER != itemSubType:
					self.__AppendRealTimeToolTip(itemVnum, metinSlot[0])

			if app.ENABLE_RENDER_TARGET_PREVIEW and item.WEAPON_QUIVER != itemSubType:
				osfInfo.RENDER_TARGET_ITEM_TYPE = 1

		### Armor ###
		elif item.ITEM_TYPE_ARMOR == itemType:
			self.__AppendLimitInformation()

			## 방어력
			defGrade = item.GetValue(1)
			defBonus = item.GetValue(5)*2 ## 방어력 표시 잘못 되는 문제를 수정
			if defGrade > 0:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_DEF_GRADE % (defGrade+defBonus), self.GetChangeTextLineColor(defGrade))

			self.__AppendMagicDefenceInfo()

			self.__AppendAffectInformation()

			if app.ENABLE_APPLY_RANDOM:
				self.__AppendDefaultItemApplyInformation(apply_random_list)

			self.__AppendAttributeInformation(attrSlot)
			self.__AppendResonanceInformation(
				itemVnum, itemSubType, window_type, slotIndex, resonance_key
			)
			if app.ENABLE_ATTR_6TH_7TH:
				if itemSubType != item.ARMOR_GLOVE:
					self.__AppendAttribute6th7thPossibility(attrSlot)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				self.AppendChangeLookInformation(window_type, slotIndex)

			self.AppendWearableInformation()

			if itemSubType in (item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR):
				self.__AppendAccessoryMetinSlotInfo(metinSlot, constInfo.GET_ACCESSORY_MATERIAL_VNUM(itemVnum, itemSubType))
			else:
				self.__AppendMetinSlotInfo(metinSlot)

			if app.ENABLE_RENDER_TARGET_PREVIEW and itemSubType == item.ARMOR_BODY:
				osfInfo.RENDER_TARGET_ITEM_TYPE = 2

		### Ring Slot Item (Not UNIQUE) ###
		elif item.ITEM_TYPE_RING == itemType:
			self.__AppendLimitInformation()
			self.__AppendAffectInformation()
			if app.ENABLE_APPLY_RANDOM:
				self.__AppendDefaultItemApplyInformation(apply_random_list)
			self.__AppendAttributeInformation(attrSlot)

			bHasRealtimeFlag = 0
			originalTimeLimit = 0
			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)
				if item.LIMIT_REAL_TIME == limitType:
					bHasRealtimeFlag = 1
					originalTimeLimit = limitValue
			
			if 1 == bHasRealtimeFlag:
				if metinSlot[0] == 0:
					self.AppendMallItemLastTime(originalTimeLimit, True)
				else:
					self.AppendMallItemLastTime(metinSlot[0])

			#반지 소켓 시스템 관련해선 아직 기획 미정
			#self.__AppendAccessoryMetinSlotInfo(metinSlot, 99001)

		### Belt Item ###
		elif item.ITEM_TYPE_BELT == itemType:
			self.__AppendLimitInformation()
			self.__AppendAffectInformation()
			if app.ENABLE_APPLY_RANDOM:
				self.__AppendDefaultItemApplyInformation(apply_random_list)
			self.__AppendAttributeInformation(attrSlot)
			if app.ENABLE_67TH_BONUS:
				self.__AppendRareAttributeInformation(attrSlot)

			# Belt cells are retired: Value0 is never shown as an inventory size.
			self.__AppendAccessoryMetinSlotInfo(metinSlot, constInfo.GET_BELT_MATERIAL_VNUM(itemVnum))

		## 코스츔 아이템 ##
		elif 0 != isCostumeItem:
			self.__AppendLimitInformation()

			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				if item.GetItemSubType() == item.COSTUME_TYPE_ACCE:
					## ABSORPTION RATE
					absChance = int(metinSlot[acce.ABSORPTION_SOCKET])
					self.AppendTextLine(localeInfo.TOOLTIP_APPLY_ACCEDRAIN_RATE(absChance), self.CONDITION_COLOR)
					## END ABSOPRTION RATE

					itemAbsorbedVnum = int(metinSlot[acce.ABSORBED_SOCKET])
					if itemAbsorbedVnum:
						## ATTACK / DEFENCE
						item.SelectItem(itemAbsorbedVnum)
						if item.GetItemType() == item.ITEM_TYPE_WEAPON:
							if item.GetItemSubType() == item.WEAPON_FAN:
								self.__AppendMagicAttackInfo(metinSlot[acce.ABSORPTION_SOCKET])
								item.SelectItem(itemAbsorbedVnum)
								self.__AppendAttackPowerInfo(metinSlot[acce.ABSORPTION_SOCKET], refine_element)
							else:
								self.__AppendAttackPowerInfo(metinSlot[acce.ABSORPTION_SOCKET], refine_element)
								item.SelectItem(itemAbsorbedVnum)
								self.__AppendMagicAttackInfo(metinSlot[acce.ABSORPTION_SOCKET])
						elif item.GetItemType() == item.ITEM_TYPE_ARMOR:
							defGrade = item.GetValue(1)
							defBonus = item.GetValue(5) * 2
							defGrade = self.CalcAcceValue(defGrade, metinSlot[acce.ABSORPTION_SOCKET])
							defBonus = self.CalcAcceValue(defBonus, metinSlot[acce.ABSORPTION_SOCKET])

							if defGrade > 0:
								self.AppendSpace(5)
								self.AppendTextLine(localeInfo.TOOLTIP_ITEM_DEF_GRADE % (defGrade + defBonus), self.GetChangeTextLineColor(defGrade))

							item.SelectItem(itemAbsorbedVnum)
							self.__AppendMagicDefenceInfo(metinSlot[acce.ABSORPTION_SOCKET])
						## END ATTACK / DEFENCE

						## EFFECT
						item.SelectItem(itemAbsorbedVnum)
						for i in range(item.ITEM_APPLY_MAX_NUM):
							(affectType, affectValue) = item.GetAffect(i)
							affectValue = self.CalcAcceValue(affectValue, metinSlot[acce.ABSORPTION_SOCKET])
							affectString = self.__GetAffectString(affectType, affectValue)
							if affectString and affectValue > 0:
								self.AppendTextLine(affectString, self.GetChangeTextLineColor(affectValue))

							item.SelectItem(itemAbsorbedVnum)
						# END EFFECT

						item.SelectItem(itemVnum)
						if app.ENABLE_APPLY_RANDOM:
							self.__AppendAcceDefaultItemApplyInformation(apply_random_list, metinSlot[acce.ABSORPTION_SOCKET], itemAbsorbedVnum)
						self.__AppendAttributeInformation(attrSlot, metinSlot[acce.ABSORPTION_SOCKET])
						if app.ENABLE_REFINE_ELEMENT_SYSTEM:
							self.__AppendRefineElementInformationAcce(metinSlot, refine_element)
					else:
						self.__AppendAttributeInformation(attrSlot)
				elif isCostumeAura:
					self.__AppendAffectInformation()
					self.__AppendAuraGameplayProgress(itemVnum, window_type, slotIndex, metinSlot)
					self.__AppendAuraAbsorbedBonuses(itemVnum, window_type, slotIndex, metinSlot, attrSlot)
				else:
					self.__AppendAffectInformation()
					self.__AppendAttributeInformation(attrSlot)
			else:
				self.__AppendAffectInformation()
				self.__AppendAttributeInformation(attrSlot)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if item.GetItemSubType() == item.COSTUME_TYPE_WEAPON or item.GetItemSubType() == item.COSTUME_TYPE_BODY:
					self.AppendChangeLookInformation(window_type, slotIndex)

				if item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
					self.AppendChangeLookInformation(window_type, slotIndex)

			self.AppendWearableInformation()

			bHasRealtimeFlag = 0
			bHasRealtimeFirstFlag = 0
			originalTimeLimit = 0

			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				if item.GetItemSubType() != item.COSTUME_TYPE_ACCE:
					## 사용가능 시간 제한이 있는지 찾아보고
					for i in range(item.LIMIT_MAX_NUM):
						(limitType, limitValue) = item.GetLimit(i)

						if item.LIMIT_REAL_TIME == limitType:
							bHasRealtimeFlag = 1
							originalTimeLimit = limitValue

						if item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
							bHasRealtimeFirstFlag = 1
							originalTimeLimit = limitValue

					if app.ENABLE_MOUNT_COSTUME_SYSTEM:
						if item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
							if not bHasRealtimeFirstFlag:
								self.__AppendMountCostumeLastTime(metinSlot, bHasRealtimeFlag, originalTimeLimit)
						else:
							if 1 == bHasRealtimeFlag:
								if metinSlot[0] == 0:
									self.AppendMallItemLastTime(originalTimeLimit, True)
								else:
									self.AppendMallItemLastTime(metinSlot[0])
					else:
						if 1 == bHasRealtimeFlag:
							if metinSlot[0] == 0:
								self.AppendMallItemLastTime(originalTimeLimit, True)
							else:
								self.AppendMallItemLastTime(metinSlot[0])
			else:
				## 사용가능 시간 제한이 있는지 찾아보고
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_REAL_TIME == limitType:
						bHasRealtimeFlag = 1
						originalTimeLimit = limitValue

					if item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
						bHasRealtimeFirstFlag = 1
						originalTimeLimit = limitValue

				if app.ENABLE_MOUNT_COSTUME_SYSTEM:
					if item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
						if not bHasRealtimeFirstFlag:
							self.__AppendMountCostumeLastTime(metinSlot, bHasRealtimeFlag, originalTimeLimit)
					else:
						if 1 == bHasRealtimeFlag:
							if metinSlot[0] == 0:
								self.AppendMallItemLastTime(originalTimeLimit, True)
							else:
								self.AppendMallItemLastTime(metinSlot[0])
				else:
					if 1 == bHasRealtimeFlag:
						if metinSlot[0] == 0:
							self.AppendMallItemLastTime(originalTimeLimit, True)
						else:
							self.AppendMallItemLastTime(metinSlot[0])

			if app.ENABLE_MOUNT_COSTUME_SYSTEM:
				if item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
					if osfInfo.SHOW_USE_IMAGE_TEXT_LINE == True:
						self.AppendSpace(5)
						self.AppendTextLine("|Ikey/mouse_right|i - %s" % localeInfo.TOOLTIP_ITEM_MOUNT)

		## Rod ##
		elif item.ITEM_TYPE_ROD == itemType:
			if 0 != metinSlot:
				if app.ENABLE_FISHING_GAME and 27591 == itemVnum:
					self.__AppendLimitInformation()

					curLevel = item.GetValue(0) // 10

					self.AppendSpace(5)
					self.AppendTextLine(localeInfo.TOOLTIP_FISHINGROD_LEVEL % (curLevel), self.NORMAL_COLOR)

					bHasRealtimeFlag = 0

					for i in range(item.LIMIT_MAX_NUM):
						(limitType, limitValue) = item.GetLimit(i)

						if item.LIMIT_REAL_TIME == limitType:
							bHasRealtimeFlag = 1

					if 1 == bHasRealtimeFlag:
						self.AppendMallItemLastTime(metinSlot[0])
					else:
						time = metinSlot[player.ITEM_METIN_SOCKET_MAX - 1] # METIN_SOCKET_MAX_NUM

						if 1 == item.GetValue(2):
							self.AppendMallItemLastTime(time)
						else:
							self.AppendUniqueItemLastTime(time)
				else:
					curLevel = item.GetValue(0) // 10
					curEXP = metinSlot[0]
					maxEXP = item.GetValue(2)

					self.__AppendLimitInformation()
					self.__AppendRodInformation(curLevel, curEXP, maxEXP)

		## Pick ##
		elif item.ITEM_TYPE_PICK == itemType:
			if 0 != metinSlot:
				curLevel = item.GetValue(0) // 10
				curEXP = metinSlot[0]
				maxEXP = item.GetValue(2)
				self.__AppendLimitInformation()
				self.__AppendPickInformation(curLevel, curEXP, maxEXP)

		## Lottery ##
		elif item.ITEM_TYPE_LOTTERY == itemType:
			if 0 != metinSlot:
				ticketNumber = int(metinSlot[0])
				stepNumber = int(metinSlot[1])

				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_LOTTERY_STEP_NUMBER % (stepNumber), self.NORMAL_COLOR)
				self.AppendTextLine(localeInfo.TOOLTIP_LOTTO_NUMBER % (ticketNumber), self.NORMAL_COLOR);

		### Metin ###
		elif item.ITEM_TYPE_METIN == itemType:
			self.AppendMetinInformation()
			self.AppendMetinWearInformation()

		### Fish ###
		elif item.ITEM_TYPE_FISH == itemType:
			self.__AppendFishBonusInformation(itemVnum)

		## item.ITEM_TYPE_BLEND
		elif item.ITEM_TYPE_BLEND == itemType:
			self.__AppendLimitInformation()

			import dewcatalog
			if not metinSlot or not metinSlot[0]:
				metinSlot = dewcatalog.preview_sockets(itemVnum) or metinSlot

			if metinSlot:
				affectType = metinSlot[0]
				affectValue = metinSlot[1]
				dew = dewcatalog.get(itemVnum)
				if dew:
					affectValue = dewcatalog.effective_value(dew[0]['values'][dew[1]], dewcatalog.player_rank())
				time = metinSlot[2]
				self.AppendSpace(5)
				affectText = self.__GetAffectString(affectType, affectValue)

				self.AppendTextLine(affectText, self.NORMAL_COLOR)

				if app.ENABLE_EXTENDED_BLEND_AFFECT:
					status = metinSlot[3]

					self.AppendSpace(10)
					if status != 0:
						self.AppendTextLine(localeInfo.BLEND_ITEM_TOOLTIP_APPLY, 0xff86e57f) # RGB(134, 229, 127)
					else:
						self.AppendTextLine(localeInfo.BLEND_ITEM_TOOLTIP_UNAPPLIED, 0xfff15f5f) # RGB(241, 95, 95)

					self.AppendSpace(5)
					if time > item.MIN_INFINITE_DURATION:
						self.AppendTextLine(localeInfo.INFINITE_USE, self.CONDITION_COLOR)
					else:
						if time > 0:
							endTime = app.GetGlobalTimeStamp() + time
							leftSec = max(0, endTime - app.GetGlobalTimeStamp())
							self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHMS(leftSec), self.NORMAL_COLOR)
						else:
							self.AppendTextLine(localeInfo.BLEND_ITEM_TOOLTIP_NO_TIME)
				else:
					if time > 0:
						minute = (time // 60)
						second = (time % 60)
						timeString = localeInfo.TOOLTIP_POTION_TIME

						if minute > 0:
							timeString += str(minute) + localeInfo.TOOLTIP_POTION_MIN
						if second > 0:
							timeString += " " + str(second) + localeInfo.TOOLTIP_POTION_SEC

						self.AppendTextLine(timeString)
					# [MT-489] 제조창에 알수 없는 툴팁
					#else:
					#	self.AppendTextLine(localeInfo.BLEND_POTION_NO_TIME)
			else:
				self.AppendTextLine("BLEND_POTION_NO_INFO")

		elif item.ITEM_TYPE_UNIQUE == itemType:
			if app.ENABLE_MULTI_FARM_BLOCK:
				if itemVnum == 55610:
					self.AppendTextLine("Adding Time: %s"% localeInfo.SecondToDHM(item.GetValue(0)),self.SPECIAL_TITLE_COLOR)
					self.AppendTextLine("Increase Count: +%d" % item.GetValue(1), self.SPECIAL_TITLE_COLOR)

			# The permanent Orc ticket must ignore timestamps on older instances.
			permanentOrcTicket = (itemVnum == 30312 and item.GetValue(0) == 0
				and item.GetValue(2) == 0
				and all(item.GetLimit(i) == (0, 0) for i in range(item.LIMIT_MAX_NUM)))
			if 0 != metinSlot and not permanentOrcTicket:
				bHasRealtimeFlag = 0
				originalTimeLimit = 0

				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_REAL_TIME == limitType:
						bHasRealtimeFlag = 1
						originalTimeLimit = limitValue

				if 1 == bHasRealtimeFlag:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(originalTimeLimit, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])
				else:
					time = metinSlot[player.METIN_SOCKET_MAX_NUM-1]
	
					timeLimit = 0
					if time <= 0:
						timeLimit = item.GetValue(0)
						
					if timeLimit >= 60:
						self.AppendUniqueItemLastTime(timeLimit)
					elif 1 == item.GetValue(2):
						self.AppendMallItemLastTime(time)
					else:
						self.AppendUniqueItemLastTime(time)

		### Use ###
		elif item.ITEM_TYPE_USE == itemType:
			self.__AppendLimitInformation()
			if item.USE_RESONANCE_SEAL == itemSubType:
				self.__AppendLooseResonanceSeal(itemVnum)

			if item.USE_POTION == itemSubType or item.USE_POTION_NODELAY == itemSubType:
				self.__AppendPotionInformation()

			elif item.USE_ABILITY_UP == itemSubType:
				self.__AppendAbilityPotionInformation()

			## 영석 감지기
			if 27989 == itemVnum or 76006 == itemVnum:
				if 0 != metinSlot:
					useCount = int(metinSlot[0])

					self.AppendSpace(5)
					self.AppendTextLine(localeInfo.TOOLTIP_REST_USABLE_COUNT % (6 - useCount), self.NORMAL_COLOR)

			## 이벤트 감지기
			elif 50004 == itemVnum:
				if 0 != metinSlot:
					useCount = int(metinSlot[0])

					self.AppendSpace(5)
					self.AppendTextLine(localeInfo.TOOLTIP_REST_USABLE_COUNT % (10 - useCount), self.NORMAL_COLOR)

			## 자동물약
			elif constInfo.IS_AUTO_POTION(itemVnum):
				if 0 != metinSlot:
					## 0: 활성화
					isActivated = int(metinSlot[0])

					if 0 != isActivated:
						self.AppendSpace(5)
						self.AppendTextLine("(%s)" % (localeInfo.TOOLTIP_AUTO_POTION_USING), self.SPECIAL_POSITIVE_COLOR)

			## 귀환 기억부
			elif itemVnum in WARP_SCROLLS:
				if 0 != metinSlot:
					xPos = int(metinSlot[0])
					yPos = int(metinSlot[1])

					if xPos != 0 and yPos != 0:
						(mapName, xBase, yBase) = background.GlobalPositionToMapInfo(xPos, yPos)

						localeMapName = localeInfo.MINIMAP_ZONE_NAME_DICT.get(mapName, "")

						self.AppendSpace(5)

						if localeMapName != "":
							self.AppendTextLine(localeInfo.TOOLTIP_MEMORIZED_POSITION % (localeMapName, int(xPos-xBase)//100, int(yPos-yBase)//100), self.NORMAL_COLOR)
						else:
							self.AppendTextLine(localeInfo.TOOLTIP_MEMORIZED_POSITION_ERROR % (int(xPos)//100, int(yPos)//100), self.NORMAL_COLOR)
							dbg.TraceError("NOT_EXIST_IN_MINIMAP_ZONE_NAME_DICT: %s" % mapName)

			#####
			if item.USE_SPECIAL == itemSubType:
				bHasRealtimeFlag = 0
				originalTimeLimit = 0
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_REAL_TIME == limitType:
						bHasRealtimeFlag = 1
						originalTimeLimit = limitValue

				## 있다면 관련 정보를 표시함. ex) 남은 시간 : 6일 6시간 58분 
				if 1 == bHasRealtimeFlag:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(originalTimeLimit, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])
				else:
					# ... 이거... 서버에는 이런 시간 체크 안되어 있는데...
					# 왜 이런게 있는지 알지는 못하나 그냥 두자...
					if 0 != metinSlot:
						time = metinSlot[player.METIN_SOCKET_MAX_NUM-1]

						## 실시간 이용 Flag
						if 1 == item.GetValue(2):
							self.AppendMallItemLastTime(time)

			elif item.USE_TIME_CHARGE_PER == itemSubType:
				bHasRealtimeFlag = 0
				originalTimeLimit = 0
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_REAL_TIME == limitType:
						bHasRealtimeFlag = 1
						originalTimeLimit = limitValue

				if metinSlot[2]:
					self.AppendTextLine(localeInfo.TOOLTIP_TIME_CHARGER_PER(metinSlot[2]))
				else:
					self.AppendTextLine(localeInfo.TOOLTIP_TIME_CHARGER_PER(item.GetValue(0)))

				## 있다면 관련 정보를 표시함. ex) 남은 시간 : 6일 6시간 58분 
				if 1 == bHasRealtimeFlag:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(originalTimeLimit, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])

			elif item.USE_TIME_CHARGE_FIX == itemSubType:
				bHasRealtimeFlag = 0
				originalTimeLimit = 0
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_REAL_TIME == limitType:
						bHasRealtimeFlag = 1
						originalTimeLimit = limitValue

				if metinSlot[2]:
					self.AppendTextLine(localeInfo.TOOLTIP_TIME_CHARGER_FIX(metinSlot[2]))
				else:
					self.AppendTextLine(localeInfo.TOOLTIP_TIME_CHARGER_FIX(item.GetValue(0)))

				## 있다면 관련 정보를 표시함. ex) 남은 시간 : 6일 6시간 58분 
				if 1 == bHasRealtimeFlag:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(originalTimeLimit, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])

		elif app.ENABLE_BUFF_SYSTEM and itemType == item.ITEM_SHAMAN:
			self.__AppendLimitInformation()
			suppWeapon = 0
			suppWeapon = player.GetItemSealDate(window_type, slotIndex)

			suppArmor = 0
			if metinSlot[1]:
				suppArmor = metinSlot[1]

			suppEffectWeapon = 0
			if metinSlot[3]:
				suppEffectWeapon = metinSlot[3]

			suppEffectArmor = 0
			if metinSlot[4]:
				suppEffectArmor = metinSlot[4]

			suppSash = 0
			if 0 != attrSlot:
				suppSash = attrSlot[0][1]

			suppHair = player.GetChangeLookVnum(window_type, slotIndex)
			if suppWeapon > 0:
				self.AppendTextLine(localeInfo.SUPPORT_WEAPON_EQUIPPED, self.POSITIVE_COLOR)
				
			if suppArmor > 0:
				self.AppendTextLine(localeInfo.SUPPORT_ARMOR_EQUIPPED, self.POSITIVE_COLOR)
				
			if suppHair > 0:
				self.AppendTextLine(localeInfo.SUPPORT_HAIR_EQUIPPED, self.POSITIVE_COLOR)
				
			if suppSash > 0:
				self.AppendTextLine(localeInfo.SUPPORT_SASH_EQUIPPED, self.POSITIVE_COLOR)
				
			if suppEffectWeapon > 0:
				self.AppendTextLine(localeInfo.SUPPORT_EFF_WEAPON_EQUIPPED, self.POSITIVE_COLOR)
				
			if suppEffectArmor > 0:
				self.AppendTextLine(localeInfo.SUPPORT_EFF_ARMOR_EQUIPPED, self.POSITIVE_COLOR)

			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)

				if item.LIMIT_REAL_TIME == limitType:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(limitValue, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])
						
			if 0 != attrSlot:
				soulBind = attrSlot[1][1]
				if soulBind == -1 or soulBind == -2:
					self.AppendSpace(5)
					self.AppendTextLine(localeInfo.TOOLTIP_SEALED, self.NEGATIVE_COLOR)

		elif item.ITEM_TYPE_QUEST == itemType:
			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)

				if item.LIMIT_REAL_TIME == limitType:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(limitValue, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])

			if 70058 == itemVnum:
				if 0 != metinSlot:
					using = int(metinSlot[0])
					maximum = 50
					self.AppendTextLine(localeInfo.TOOLTIP_REMAINING_COUNT % (maximum - using), grp.GenerateColor(1.0, 0.843, 0.0, 1.0))

		# app.ENABLE_PET_SYSTEM
		elif item.ITEM_TYPE_PET == itemType and item.PET_PAY == itemSubType:
			if osfInfo.PET_ITEM_ATTR_TOOLTIP == True:
				if item.IsPetPay(itemVnum):
					self.__AppendAffectInformation()
					if app.ENABLE_APPLY_RANDOM:
						self.__AppendDefaultItemApplyInformation(apply_random_list)
					self.__AppendAttributeInformation(attrSlot)

			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)

				if item.LIMIT_REAL_TIME == limitType:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(limitValue, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])


			if osfInfo.SHOW_USE_IMAGE_TEXT_LINE == True:
				if item.IsPetPay(itemVnum):
					self.AppendSpace(5)
					self.AppendTextLine("|Ikey/mouse_right|i - %s" % localeInfo.TOOLTIP_ITEM_SUMMON)
				else:
					pass

		elif 79520 <= itemVnum <= 79523:
			self.__AppendLimitInformation()
			self.__AppendAffectInformation()

		elif itemVnum == mountcorebonus.CORE_VNUM:
			self.__AppendLimitInformation()
			self.__AppendAffectInformation()
			if attrSlot and any(value for affectType, value in attrSlot[:5]):
				self.AppendSpace(5)
				self.__AppendAttributeInformation(attrSlot)

		elif item.ITEM_TYPE_DS == itemType:
			self.AppendTextLine(self.__DragonSoulInfoString(itemVnum))

			if app.ENABLE_DS_SET:
				if window_type == player.EQUIPMENT and self.interface and self.interface.wndDragonSoul:
					self.__AppendDragonSoulAttributeInformation(attrSlot, itemVnum // 10000, self.interface.wndDragonSoul.GetDSSetGrade())
				else:
					self.__AppendDragonSoulAttributeInformation(attrSlot)
			else:
				self.__AppendAttributeInformation(attrSlot)

		elif app.ENABLE_GROWTH_PET_SYSTEM and item.ITEM_TYPE_PET == itemType:		
			if item.PET_EGG == itemSubType:
				if window_type == player.INVENTORY:
					self.__AppendPetEggItemInformation(metinSlot)
				else:
					self.__AppendPetEggItemInformation(metinSlot, True)
						
			elif item.PET_UPBRINGING == itemSubType:
				self.__AppendUpBringingPetItemInfomation(metinSlot)
				
			elif item.PET_BAG == itemSubType:
				self.__AppendPetBagItemInfomation(metinSlot)

		else:
			self.__AppendLimitInformation()

		# if item.ITEM_TYPE_GIFTBOX == itemType:
			# for i in range(item.LIMIT_MAX_NUM):
				# (limitType, limitValue) = item.GetLimit(i)

				# if item.LIMIT_REAL_TIME == limitType:
					# self.AppendMallItemLastTime(metinSlot[0])

		if item.ITEM_TYPE_DS == itemType:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.INFINITE_USE, self.CONDITION_COLOR)
		else:
			if app.ENABLE_GROWTH_PET_SYSTEM:
				if not (item.ITEM_TYPE_PET == itemType and item.PET_BAG == itemSubType):
					for i in range(item.LIMIT_MAX_NUM):
						(limitType, limitValue) = item.GetLimit(i)

						if item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
							self.AppendRealTimeStartFirstUseLastTime(item, metinSlot, i)

						elif item.LIMIT_TIMER_BASED_ON_WEAR == limitType:
							if not (app.ENABLE_MOUNT_COSTUME_SYSTEM and item.ITEM_TYPE_COSTUME == itemType and item.COSTUME_TYPE_MOUNT == itemSubType):
								self.AppendTimerBasedOnWearLastTime(metinSlot)

			else:
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
						self.AppendRealTimeStartFirstUseLastTime(item, metinSlot, i)

					elif item.LIMIT_TIMER_BASED_ON_WEAR == limitType:
						if not (app.ENABLE_MOUNT_COSTUME_SYSTEM and item.ITEM_TYPE_COSTUME == itemType and item.COSTUME_TYPE_MOUNT == itemSubType):
							self.AppendTimerBasedOnWearLastTime(metinSlot)

		## 2015 크리스마스 이벤트 아이템으로 2개의 아이템은 REAL_TIME 이 아님에도 기간제 아이템이다
		if self.itemVnum in [79505, 79506]:
			if 0 != metinSlot[0]:
				self.AppendMallItemLastTime(metinSlot[0])

		# if app.ENABLE_10TH_EVENT:
		if self.itemVnum in [25101, 25103]:
			if 0 != metinSlot[0]:
				self.AppendMallItemLastTime(metinSlot[0])

		# if app.ENABLE_2017_RAMADAN:
		if self.itemVnum in [30315, 30317, 30318, 50183]:
			if 0 != metinSlot[0]:
				self.AppendMallItemLastTime(metinSlot[0])

		# if app.ENABLE_MINI_GAME_YUTNORI:
		if self.itemVnum in [79507, 79508]:
			if 0 != metinSlot[0]:
				self.AppendMallItemLastTime(metinSlot[0])

		if app.ENABLE_SOUL_BIND_SYSTEM:
			self.AppendSealInformation(window_type, slotIndex) ## cyh itemseal 2013 11 11

		if osfInfo.SHOW_SELL_IMAGE_TEXT_LINE == True:
			if slotIndex < player.EQUIPMENT_SLOT_START:
				if not player.IsAntiFlagBySlot(slotIndex, item.ANTIFLAG_SELL):
					self.AppendSpace(5)
					self.AppendTextLine("|Ikey/ctrl|i + |Ikey/x|i + |Ikey/mouse_left|i - Remover")

		if osfInfo.SHOW_ITEM_VNUM_TOOTIP == True:
			if chr.IsGameMaster(player.GetMainCharacterIndex()):
				self.AppendSpace(5)
				self.AppendTextLine("Vnum: %d" % itemVnum, grp.GenerateColor(0.6705, 0.9490, 0.0, 1.0))
				self.AppendTextLine("ItemType: %s" % itemType, grp.GenerateColor(0.6705, 0.9490, 0.0, 1.0))
				self.AppendTextLine("ItemSubType: %s" % itemSubType, grp.GenerateColor(0.6705, 0.9490, 0.0, 1.0))

		self.__AppendTradeabilityInformation()

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			if self.mountPreviewRace > 0:
				if not deferMountPreview:
					self.__AppendMountPreview()
			elif osfInfo.RENDER_TARGET_ITEM_TYPE:
				self.AppendSpace(5)
				self.AppendTextLine("|Ikey/ctrl|i + |Ikey/x|i - %s" % localeInfo.IKEY_SYSTEM_PREVIEW, self.TITLE_COLOR)
			if self.costumePreviewVnum > 0 and not deferMountPreview:
				self.__AppendCostumePreview()

		self.ShowToolTip()

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def AddHyperLinkPetItemData(self, itemVnum, metinSlot, attrSlot, pet_info):
			
			pet_level			= int(pet_info[0], 16)
			pet_birthday		= int(pet_info[1], 16)
			pet_evol_level		= int(pet_info[2], 16)
			pet_hp				= int(pet_info[3], 16) / 10.0
			pet_def				= int(pet_info[4], 16) / 10.0
			pet_sp				= int(pet_info[5], 16) / 10.0
			pet_life_time		= int(pet_info[6], 16)
			pet_life_time_max	= int(pet_info[7], 16)
			pet_skill_count		= int(pet_info[8], 16)
			pet_item_vnum		= int(pet_info[9], 16)
			pet_nick_name		= pet_info[10]
						
			pet_skill_vnum		= [0] * player.PET_SKILL_COUNT_MAX
			pet_skill_level		= [0] * player.PET_SKILL_COUNT_MAX
			
			skill_index = 11
			for index in range(player.PET_SKILL_COUNT_MAX):
				pet_skill_vnum[index]	= int(pet_info[skill_index], 16)
				skill_index = skill_index + 1
				pet_skill_level[index]	= int(pet_info[skill_index], 16)
				skill_index = skill_index + 1
				
			self.itemVnum = itemVnum
			item.SelectItem(itemVnum)
			itemType = item.GetItemType()
			itemSubType = item.GetItemSubType()
			itemDesc = item.GetItemDescription()
			itemSummary = item.GetItemSummary()

			if item.ITEM_TYPE_PET != itemType:
				return
			
			if itemSubType not in [item.PET_UPBRINGING, item.PET_BAG]:
				return
			
			if item.PET_BAG == itemSubType:
				self.itemVnum = pet_item_vnum
				item.SelectItem(pet_item_vnum)
				pet_bag_desc = localeInfo.PET_BAG_DESC % item.GetItemName()
				self.__AdjustMaxWidth(0, pet_bag_desc)
				self.itemVnum = itemVnum
				item.SelectItem(itemVnum)

			if item.PET_BAG == itemSubType:
				self.AppendTextLine( pet_nick_name + "(" + localeInfo.PET_TOOLTIP_TRADABLE + ")", self.TITLE_COLOR )
			elif item.PET_UPBRINGING == itemSubType:
				self.AppendTextLine( pet_nick_name, self.TITLE_COLOR)
				
			## Pet Type
			PET_TYPES = [
				0,
				localeInfo.PET_ATTR_DETERMINE_TYPE1_TOOLTIP,
				localeInfo.PET_ATTR_DETERMINE_TYPE2_TOOLTIP,
				localeInfo.PET_ATTR_DETERMINE_TYPE3_TOOLTIP,
				localeInfo.PET_ATTR_DETERMINE_TYPE4_TOOLTIP,
				localeInfo.PET_ATTR_DETERMINE_TYPE5_TOOLTIP,
				localeInfo.PET_ATTR_DETERMINE_TYPE6_TOOLTIP,
				localeInfo.PET_ATTR_DETERMINE_TYPE7_TOOLTIP,
				localeInfo.PET_ATTR_DETERMINE_TYPE8_TOOLTIP,
			]
			
			pet_type = metinSlot[3]
			self.AppendSpace(5)
			self.AppendTextLine(PET_TYPES[pet_type], self.SPECIAL_POSITIVE_COLOR2)
			
			## ??
			if item.PET_UPBRINGING == itemSubType:
				self.AppendDescription(itemDesc, 26)
				self.AppendDescription(itemSummary, 26, self.CONDITION_COLOR)
			elif item.PET_BAG == itemSubType:
				self.AppendDescription(pet_bag_desc, 26)
				self.itemVnum = itemVnum
				item.SelectItem(itemVnum)

			self.AppendSpace(5)
			if item.PET_UPBRINGING == itemSubType:
				cur_time = app.GetGlobalTimeStamp()
				
				# Pet's age stops at their death
				if metinSlot[0] < cur_time:
					pet_birthday = max(0, metinSlot[0] - pet_birthday)
				else:
					pet_birthday = max(0, cur_time - pet_birthday)
					
			elif item.PET_BAG == itemSubType:
				cur_time	 = app.GetGlobalTimeStamp()
				pet_birthday = max(0, cur_time - pet_birthday + (cur_time - metinSlot[1]))
				
			self.AppendTextLine(localeInfo.PET_TOOLTIP_LEVEL + " " + str(pet_level) + " (" + localeInfo.SecondToDay(pet_birthday) + ")")				

			self.AppendSpace(5)
			if pet_skill_count:
				self.AppendTextLine( self.GetEvolName(pet_evol_level) + "(" + str(pet_skill_count) + ")")
			else:
				self.AppendTextLine( self.GetEvolName(pet_evol_level) )

			self.AppendSpace(5)
			self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_HP, pet_hp, pet_type), self.SPECIAL_POSITIVE_COLOR)
			self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_SP, pet_sp, pet_type), self.SPECIAL_POSITIVE_COLOR)
			self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_DEF, pet_def, pet_type), self.SPECIAL_POSITIVE_COLOR)

			for index in range(player.PET_SKILL_COUNT_MAX):
				if pet_skill_vnum[index]:
					self.AppendSpace(5)
					( pet_skill_name, pet_skill_desc, pet_skill_use_type , pet_skill_cool_time ) = skill.GetPetSkillInfo(pet_skill_vnum[index])
					self.AppendTextLine( localeInfo.PET_TOOLTUP_SKILL % (pet_skill_name, pet_skill_level[index]) , self.SPECIAL_POSITIVE_COLOR)
						
			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)
				if item.LIMIT_REAL_TIME == limitType:
					self.AppendPetItemLastTime(metinSlot[0])
				if item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
					self.AppendPetItemLastTime(metinSlot[0])

			
			self.ShowToolTip()
			
		def GetEvolName(self, evol_level):
		
			if 1 == evol_level:
				return localeInfo.PET_INFORMATION_STAGE1
			elif 2 == evol_level:
				return localeInfo.PET_INFORMATION_STAGE2
			elif 3 == evol_level:
				return localeInfo.PET_INFORMATION_STAGE3
			elif 4 == evol_level:
				return localeInfo.PET_INFORMATION_STAGE4
				
			return localeInfo.PET_INFORMATION_STAGE1
		
		def __PetStatText(self, label, value, pet_type):
			if label == localeInfo.PET_TOOLTIP_SP:
				label = growthpetpresentation.ThirdBonusLabel(pet_type)
				value = growthpetpresentation.ThirdAppliedPercent(value)
			low = min(max(int(pet_type), 1), 5)
			high = 6
			current = ("%.1f" % float(value)).replace(".", ",")
			growth = ("%.1f-%.1f" % (low / 10.0, high / 10.0)).replace(".", ",")
			pattern = getattr(localeInfo, "PET_ALBUM_STAT_VALUE", u"+%s %% (%s %%)")
			return label + " " + (pattern % (current, growth))

		def __AppendPetBagItemInfomation(self, metinSlot):
			pet_id = metinSlot[2]
			if pet_id:
				self.ClearToolTip()
				growhPetVNum = player.GetPetItemVNumInBag(pet_id)
				if 0 == growhPetVNum:
					return

				item.SelectItem(growhPetVNum)
				pet_bag_desc = localeInfo.PET_BAG_DESC % item.GetItemName()
				self.__AdjustMaxWidth(0, pet_bag_desc)

				(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
				self.AppendTextLine( pet_nick + "(" + localeInfo.PET_TOOLTIP_TRADABLE + ")", self.TITLE_COLOR )
				
				## Pet Type
				PET_TYPES = [
					0,
					localeInfo.PET_ATTR_DETERMINE_TYPE1_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE2_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE3_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE4_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE5_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE6_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE7_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE8_TOOLTIP,
				]
				
				pet_type = metinSlot[3]
				self.AppendSpace(5)
				self.AppendTextLine(PET_TYPES[pet_type], self.SPECIAL_POSITIVE_COLOR2)

				## DESC
				self.AppendDescription(pet_bag_desc, 26)
				
				item.SelectItem(self.itemVnum)

				skillStates = growthpetpresentation.SkillSlots(pet_id)
				skill_count = len([state for state in skillStates if not state[0]])

				self.AppendSpace(5)

				cur_time = app.GetGlobalTimeStamp()
				birthSec = max(0, cur_time - birthday - (cur_time - metinSlot[1]))
				
				self.AppendTextLine(localeInfo.PET_TOOLTIP_LEVEL + " " + str(pet_level) + " (" + localeInfo.SecondToDay(birthSec) + ")")

				## Pet Evolution/Skill Count
				self.AppendSpace(5)
				if skill_count:
					self.AppendTextLine( self.GetEvolName(evol_level) + "(" + str(skill_count) + ")")
				else:
					self.AppendTextLine( self.GetEvolName(evol_level) )
					
				## Pet Stats
				self.AppendSpace(5)
				self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_HP, pet_hp, pet_type), self.SPECIAL_POSITIVE_COLOR)
				self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_SP, pet_sp, pet_type), self.SPECIAL_POSITIVE_COLOR)
				self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_DEF, pet_def, pet_type), self.SPECIAL_POSITIVE_COLOR)

				## Pet Skills
				for skillLocked, skillVnum, skillLevel, cooltime in skillStates:
					if skillLocked or not skillVnum:
						continue
					self.AppendSpace(5)
					(skillName, skillDesc, skillUseType, skillCoolTime) = skill.GetPetSkillInfo(skillVnum)
					self.AppendTextLine(localeInfo.PET_TOOLTUP_SKILL % (skillName, skillLevel), self.SPECIAL_POSITIVE_COLOR)

				## Bag Duration
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)
					if item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
						self.AppendPetItemLastTime(metinSlot[0])

		def __AppendPetEggItemInformation(self, metinSlot, isFeedWindow = False):
			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)
				if item.LIMIT_REAL_TIME == limitType:
					if metinSlot[0] == 0:
						self.AppendMallItemLastTime(limitValue, True)
					else:
						self.AppendMallItemLastTime(metinSlot[0])

		def __AppendUpBringingPetItemInfomation(self, metinSlot):
			pet_id = metinSlot[2]
			if pet_id:
				## Pet Type
				PET_TYPES = [
					0,
					localeInfo.PET_ATTR_DETERMINE_TYPE1_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE2_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE3_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE4_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE5_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE6_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE7_TOOLTIP,
					localeInfo.PET_ATTR_DETERMINE_TYPE8_TOOLTIP,
				]
				
				pet_type = metinSlot[3]
				self.AppendSpace(5)
				self.AppendTextLine(PET_TYPES[pet_type], self.SPECIAL_POSITIVE_COLOR2)
			
				## Skills
				skillStates = growthpetpresentation.SkillSlots(pet_id)
				skill_count = len([state for state in skillStates if not state[0]])
				
				## Pet Level/Age
				(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
				self.AppendSpace(5)
				
				curTime = app.GetGlobalTimeStamp()
				birthSec = 0
				
				# Pet's age stops at their death
				if metinSlot[0] < curTime:
					birthSec = max(0, metinSlot[0] - birthday)
				else:
					birthSec = max(0, curTime - birthday)
				self.AppendTextLine(localeInfo.PET_TOOLTIP_LEVEL + " " + str(pet_level) + " (" + localeInfo.SecondToDay(birthSec) + ")")
			
				## Pet Evolution/Skill Count
				self.AppendSpace(5)
				if skill_count:
					self.AppendTextLine( self.GetEvolName(evol_level) + "(" + str(skill_count) + ")")
				else:
					self.AppendTextLine( self.GetEvolName(evol_level) )
					
				## Pet Stats
				self.AppendSpace(5)
				self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_HP, pet_hp, pet_type), self.SPECIAL_POSITIVE_COLOR)
				self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_SP, pet_sp, pet_type), self.SPECIAL_POSITIVE_COLOR)
				self.AppendTextLine(self.__PetStatText(localeInfo.PET_TOOLTIP_DEF, pet_def, pet_type), self.SPECIAL_POSITIVE_COLOR)
				
				## Pet Skills
				for skillLocked, skillVnum, skillLevel, cooltime in skillStates:
					if skillLocked or not skillVnum:
						continue
					self.AppendSpace(5)
					(skillName, skillDesc, skillUseType, skillCoolTime) = skill.GetPetSkillInfo(skillVnum)
					self.AppendTextLine(localeInfo.PET_TOOLTUP_SKILL % (skillName, skillLevel), self.SPECIAL_POSITIVE_COLOR)
					
				## Pet Duration
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)
					if item.LIMIT_REAL_TIME == limitType:
						self.AppendPetItemLastTime(metinSlot[0])
			
		def AppendPetItemLastTime(self, endTime):
			self.AppendSpace(5)
			
			leftSec = endTime - app.GetGlobalTimeStamp()
			if leftSec >= 0:
				self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftSec), self.NORMAL_COLOR)
			else:
				self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.PET_TOOLTIP_LIFETIME_OVER, self.DISABLE_COLOR)

	def __DragonSoulInfoString (self, dwVnum):
		step = (dwVnum // 100) % 10
		refine = (dwVnum // 10) % 10
		if 0 == step:
			return localeInfo.DRAGON_SOUL_STEP_LEVEL1 + " " + localeInfo.DRAGON_SOUL_STRENGTH(refine)
		elif 1 == step:
			return localeInfo.DRAGON_SOUL_STEP_LEVEL2 + " " + localeInfo.DRAGON_SOUL_STRENGTH(refine)
		elif 2 == step:
			return localeInfo.DRAGON_SOUL_STEP_LEVEL3 + " " + localeInfo.DRAGON_SOUL_STRENGTH(refine)
		elif 3 == step:
			return localeInfo.DRAGON_SOUL_STEP_LEVEL4 + " " + localeInfo.DRAGON_SOUL_STRENGTH(refine)
		elif 4 == step:
			return localeInfo.DRAGON_SOUL_STEP_LEVEL5 + " " + localeInfo.DRAGON_SOUL_STRENGTH(refine)
		else:
			return ""

	## 헤어인가?
	def __IsHair(self, itemVnum):
		item.SelectItem(itemVnum)
		itemType = item.GetItemType()
		if itemType != item.ITEM_TYPE_COSTUME:
			return 0 # hot fix

		return (
			self.__IsOldHair(itemVnum) or 
			self.__IsNewHair(itemVnum) or
			self.__IsNewHair2(itemVnum) or
			self.__IsNewHair3(itemVnum) or
			self.__IsCostumeHair(itemVnum)
		)

	def __IsOldHair(self, itemVnum):
		return itemVnum > 73000 and itemVnum < 74000

	def __IsNewHair(self, itemVnum):
		return itemVnum > 74000 and itemVnum < 75000

	def __IsNewHair2(self, itemVnum):
		return itemVnum > 75000 and itemVnum < 76000

	def __IsNewHair3(self, itemVnum):
		return ((74012 < itemVnum and itemVnum < 74022) or
			(74262 < itemVnum and itemVnum < 74272) or
			(74512 < itemVnum and itemVnum < 74522) or
			(74762 < itemVnum and itemVnum < 74772) or
			(45000 < itemVnum and itemVnum < 47000))

	def __IsCostumeHair(self, itemVnum):
		return self.__IsNewHair3(itemVnum - 100000)

	def __AppendHairIcon(self, itemVnum):
		itemImage = ui.ImageBox()
		itemImage.SetParent(self)
		itemImage.Show()

		if self.__IsOldHair(itemVnum):
			itemImage.LoadImage("d:/ymir work/item/quest/" + str(itemVnum) + ".tga")
		elif self.__IsNewHair3(itemVnum):
			itemImage.LoadImage("icon/hair/%d.sub" % (itemVnum))
		elif self.__IsNewHair(itemVnum): # 기존 헤어 번호를 연결시켜서 사용한다. 새로운 아이템은 1000만큼 번호가 늘었다.
			if itemVnum > 74520 and itemVnum < 74751:
				itemImage.LoadImage("icon/hair/%d.sub" % (itemVnum))
			else:
				itemImage.LoadImage("d:/ymir work/item/quest/" + str(itemVnum-1000) + ".tga")
		elif self.__IsNewHair2(itemVnum):
			itemImage.LoadImage("icon/hair/%d.sub" % (itemVnum))
		elif self.__IsCostumeHair(itemVnum):
			itemImage.LoadImage("icon/hair/%d.sub" % (itemVnum - 100000))

		itemImage.SetPosition(itemImage.GetWidth() // 2, self.toolTipHeight)

		self.toolTipHeight += itemImage.GetHeight()
		#self.toolTipWidth += itemImage.GetWidth() / 2
		self.childrenList.append(itemImage)
		self.ResizeToolTip()

	def ResizeToolTipWidth(self, width):
		self.toolTipWidth = width

	def __IsCostumeMount(self):
		return (
			app.ENABLE_MOUNT_COSTUME_SYSTEM
			and item.GetItemType() == item.ITEM_TYPE_COSTUME
			and item.GetItemSubType() == item.COSTUME_TYPE_MOUNT
		)

	def __GetVisiblePrototypeAffects(self):
		if self.costumeVoucherOffer:
			# The fixed apply belongs to the PvM variant only; the buyer picks
			# PvM or PvP when using the voucher (see the voucher block).
			return []
		affects = [
			item.GetAffect(index)
			for index in range(item.ITEM_APPLY_MAX_NUM)
		]
		return mountspeedtooltip.FilterPrototypeAffects(
			self.__IsCostumeMount(),
			affects,
			self.attrSlot,
			item.APPLY_MOV_SPEED,
		)

	def __CalculateToolTipWidth(self):
		desc_string_list = []
		affect_string_list = []
		metin_affect_string_list = []

		for desc_type in range(2):
			if desc_type == 0:
				desc = item.GetItemDescription()
			else:
				desc = item.GetItemSummary()

			if not desc:
				continue

			if localeInfo.IsEUROPE():
				lines = SplitDescription(desc, DESC_WESTERN_MAX_COLS)
				desc_string_list.extend(lines)
			else:
				line_count = grpText.GetSplitingTextLineCount(desc, DESC_DEFAULT_MAX_COLS)
				for i in range(line_count):
					line = grpText.GetSplitingTextLine(desc, DESC_DEFAULT_MAX_COLS, i)
					desc_string_list.append(line)

		for affect_type, affect_value in self.__GetVisiblePrototypeAffects():
			if affect_value == 0:
				continue

			affect_string = self.__GetAffectString(affect_type, affect_value)
			if affect_string:
				affect_string_list.append(affect_string)

		if self.attrSlot:
			count = 0
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				affect_type, affect_value = self.attrSlot[i]
				if affect_type != 0 and affect_value != 0:
					count += 1
				if affect_value == 0:
					continue
				affect_string = self.__GetAffectString(affect_type, affect_value)
				if affect_string:
					affect_string_list.append(affect_string)
					if app.ENABLE_ATTR_6TH_7TH and 5 <= count <= 6:
						affect_string_list.append(localeInfo.ATTR_6TH_7TH_POSSIBILITY)

		has_slot = False
		has_realtime_flag = False

		for i in range(item.LIMIT_MAX_NUM):
			(limit_type, limit_value) = item.GetLimit(i)
			if item.LIMIT_REAL_TIME == limit_type:
				has_realtime_flag = True
				break

		if self.metinSlot and not has_realtime_flag:
			item_type = item.GetItemType()
			sub_type = item.GetItemSubType()

			if sub_type in (item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR) or item_type == item.ITEM_TYPE_BELT:
				if self.metinSlot[0] > 0:
					has_slot = True
			elif item.IsEquipmentVID(self.itemVnum) and item_type != item.ITEM_TYPE_COSTUME:
				for data in self.metinSlot:
					item_index = self.GetMetinItemIndex(data)
					if item_index == 0:
						continue

					item.SelectItem(item_index)
					for i in range(item.ITEM_APPLY_MAX_NUM):
						affect_type, affect_value = item.GetAffect(i)
						if affect_value == 0:
							continue

						affect_string = self.__GetAffectString(affect_type, affect_value)
						if affect_string:
							metin_affect_string_list.append(affect_string)
							has_slot = True

				item.SelectItem(self.itemVnum)

		total_strings = desc_string_list + affect_string_list + metin_affect_string_list
		if not total_strings:
			return

		max_text = max(total_strings, key = len) if total_strings else ""
		width = app.GetTextWidth(max_text) + 14

		if has_slot:
			max_metin_attr_text = max(metin_affect_string_list, key = len) if metin_affect_string_list else ""
			max_attr_text = max(affect_string_list, key = len) if affect_string_list else ""

			metin_attr_text_width = app.GetTextWidth(max_metin_attr_text)
			attr_text_width = app.GetTextWidth(max_attr_text)

			slot_gap = 43
			if metin_attr_text_width + slot_gap > attr_text_width:
				width = max(self.toolTipWidth, metin_attr_text_width + 14 + slot_gap)
			else:
				width += slot_gap

		if width > self.toolTipWidth:
			self.toolTipWidth = width
			self.AlignTextLineHorizonalCenter()

	## 사이즈가 큰 Description 일 경우 툴팁 사이즈를 조정한다
	def __AdjustMaxWidth(self, attrSlot, desc):
		newToolTipWidth = self.toolTipWidth
		newToolTipWidth = max(self.__AdjustAttrMaxWidth(attrSlot), newToolTipWidth)
		newToolTipWidth = max(self.__AdjustDescMaxWidth(desc), newToolTipWidth)
		if newToolTipWidth > self.toolTipWidth:
			self.toolTipWidth = newToolTipWidth
			self.ResizeToolTip()

	def __MeasureTextWidth(self, text):
		# Width probes must never enter childrenList or the live bonus registry.
		# SetText updates native glyph metrics even on hidden, unparented lines.
		textLine = ui.TextLine()
		textLine.SetFontName(self.defFontName)
		textLine.SetText(text)
		return textLine.GetTextSize()[0]

	def __AdjustAttrMaxWidth(self, attrSlot):
		if 0 == attrSlot:
			return self.toolTipWidth

		if not attrSlot:
			return self.toolTipWidth

		maxWidth = self.toolTipWidth
		for i in range(min(8, len(attrSlot))):
			type = attrSlot[i][0]
			value = attrSlot[i][1]
			if type in self.ATTRIBUTE_NEED_WIDTH:
				if value > 0:
					maxWidth = max(self.ATTRIBUTE_NEED_WIDTH[type], maxWidth)

			tW = self.__MeasureTextWidth(self.__GetAffectString(type, value))

			maxWidth = max(tW + 12, maxWidth)

					# ATTR_CHANGE_TOOLTIP_WIDTH
					#self.toolTipWidth = max(self.ATTRIBUTE_NEED_WIDTH[type], self.toolTipWidth)
					#self.ResizeToolTip()
					# END_OF_ATTR_CHANGE_TOOLTIP_WIDTH

		return maxWidth

	def __AdjustDescMaxWidth(self, desc):
		if len(desc) < DESC_DEFAULT_MAX_COLS:
			return self.toolTipWidth

		return DESC_WESTERN_MAX_WIDTH

	def __SetSkillBookToolTip(self, skillIndex, bookName, skillGrade):
		skillName = skill.GetSkillName(skillIndex)

		if not skillName:
			return

		if localeInfo.IsVIETNAM():
			itemName = bookName + " " + skillName
		else:
			itemName = skillName + " " + bookName
		self.SetTitle(itemName)

		if skillGrade != 0:
			self.__AppendSkillBookGradeIcons(skillIndex)

	def __AppendSkillBookGradeIcons(self, skillIndex):
		try:
			self.AppendSpace(5)

			skillSlot = ui.GridSlotWindow()
			skillSlot.SetParent(self)
			skillSlot.SetWindowHorizontalAlignCenter()
			skillSlot.SetPosition(0, self.toolTipHeight)
			skillSlot.ArrangeSlot(0, 3, 1, 32, 32, 0, 0)
			skillSlot.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)

			grades = [0]
			if hasattr(player, "SKILL_GRADE_MASTER"):
				grades.append(player.SKILL_GRADE_MASTER)
			else:
				grades.append(1)
			if hasattr(player, "SKILL_GRADE_GRAND_MASTER"):
				grades.append(player.SKILL_GRADE_GRAND_MASTER)
			else:
				grades.append(2)

			for i in range(3):
				skillSlot.SetSkillSlotNew(i, skillIndex, grades[i], 0)

			skillSlot.RefreshSlot()
			skillSlot.Show()
			self.childrenList.append(skillSlot)

			self.toolTipHeight += 32
			self.ResizeToolTip()
		except:
			pass

	def __AppendPickInformation(self, curLevel, curEXP, maxEXP):
		self.AppendSpace(5)
		self.AppendTextLine(localeInfo.TOOLTIP_PICK_LEVEL % (curLevel), self.NORMAL_COLOR)

		self.AppendTextLine(localeInfo.TOOLTIP_PICK_EXP % (curEXP, maxEXP), self.NORMAL_COLOR)

		if curEXP == maxEXP:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_PICK_UPGRADE1, self.NORMAL_COLOR)
			self.AppendTextLine(localeInfo.TOOLTIP_PICK_UPGRADE2, self.NORMAL_COLOR)
			self.AppendTextLine(localeInfo.TOOLTIP_PICK_UPGRADE3, self.NORMAL_COLOR)

	def __AppendRodInformation(self, curLevel, curEXP, maxEXP):
		self.AppendSpace(5)
		self.AppendTextLine(localeInfo.TOOLTIP_FISHINGROD_LEVEL % (curLevel), self.NORMAL_COLOR)

		self.AppendTextLine(localeInfo.TOOLTIP_FISHINGROD_EXP % (curEXP, maxEXP), self.NORMAL_COLOR)

		if curEXP == maxEXP:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_FISHINGROD_UPGRADE1, self.NORMAL_COLOR)
			self.AppendTextLine(localeInfo.TOOLTIP_FISHINGROD_UPGRADE2, self.NORMAL_COLOR)
			self.AppendTextLine(localeInfo.TOOLTIP_FISHINGROD_UPGRADE3, self.NORMAL_COLOR)

	def __AppendLimitInformation(self):
		appendSpace = False

		for i in range(item.LIMIT_MAX_NUM):
			(limitType, limitValue) = item.GetLimit(i)

			if limitValue > 0:
				if False == appendSpace:
					self.AppendSpace(5)
					appendSpace = True
			else:
				continue

			if item.LIMIT_LEVEL == limitType:
				color = self.GetLimitTextLineColor(player.GetStatus(player.LEVEL), limitValue)
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_LEVEL % (limitValue), color)
			"""
			elif item.LIMIT_STR == limitType:
				color = self.GetLimitTextLineColor(player.GetStatus(player.ST), limitValue)
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_STR % (limitValue), color)
			elif item.LIMIT_DEX == limitType:
				color = self.GetLimitTextLineColor(player.GetStatus(player.DX), limitValue)
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_DEX % (limitValue), color)
			elif item.LIMIT_INT == limitType:
				color = self.GetLimitTextLineColor(player.GetStatus(player.IQ), limitValue)
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_INT % (limitValue), color)
			elif item.LIMIT_CON == limitType:
				color = self.GetLimitTextLineColor(player.GetStatus(player.HT), limitValue)
				self.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_CON % (limitValue), color)
			"""

	if app.ENABLE_SOUL_BIND_SYSTEM:
		## cyh itemseal 2013 11 11
		def AppendSealInformation(self, window_type, slotIndex):
			itemSealDate = player.GetItemSealDate(window_type, slotIndex)
			if item.GetItemType() == item.ITEM_SHAMAN:
				return
			if itemSealDate == item.GetUnlimitedSealDate():
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_SEALED, self.NEGATIVE_COLOR)
			elif itemSealDate > 0:
				self.AppendSpace(5)
				hours, minutes = player.GetItemUnSealLeftTime(window_type, slotIndex)
				self.AppendTextLine(localeInfo.TOOLTIP_UNSEAL_LEFT_TIME % (hours, minutes), self.NEGATIVE_COLOR )

	def __GetAffectString(self, affectType, affectValue):
		text = self.__FormatAffectString(affectType, affectValue)
		if not text or text.startswith("UNKNOWN_"):
			return text
		formatted = itembonuspresentation.totals.Format(text, affectType)
		self.bonusLabels[formatted] = (text, affectType)
		return formatted

	def __FormatAffectString(self, affectType, affectValue):
		if mountcorebonus.IsScopedApply(affectType):
			return mountcorebonus.FormatAffect(affectType, affectValue, app.GetLocalePath().endswith("/cz"))
		if 0 == affectType:
			return None

		if 0 == affectValue:
			return None

		if app.ENABLE_APPLY_RANDOM:
			if affectType == item.APPLY_RANDOM:
				return None

		try:
			return mountspeedtooltip.FormatAffect(
				self.__IsCostumeMount(),
				affectType,
				affectValue,
				item.APPLY_MOV_SPEED,
				localeInfo.TOOLTIP_MOUNT_SPEED,
				self.AFFECT_DICT[affectType],
			)
		except TypeError:
			return "UNKNOWN_VALUE[%s] %s" % (affectType, affectValue)
		except KeyError:
			return "UNKNOWN_TYPE[%s] %s" % (affectType, affectValue)

	def __AdjustMaxWidthFromAffectList(self, affectList):
		maxWidth = self.toolTipWidth

		for affectType, affectValue in affectList:
			affectString = self.__GetAffectString(affectType, affectValue)

			if affectString:
				tW = self.__MeasureTextWidth(affectString)
				maxWidth = max(tW + 12, maxWidth)

		self.toolTipWidth = maxWidth


	def __AppendAffectInformation(self):
		affectList = self.__GetVisiblePrototypeAffects()

		self.__AdjustMaxWidthFromAffectList(affectList)

		for affectType, affectValue in affectList:
			affectString = self.__GetAffectString(affectType, affectValue)
			if affectString:
				self.AppendTextLine(affectString, self.GetChangeTextLineColor(affectValue))

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def AppendChangeLookInformation(self, window_type, slotIndex):
			if window_type == player.SAFEBOX:
				changelookvnum = safebox.GetItemChangeLookVnum(slotIndex)
			elif window_type == player.MALL:
				changelookvnum = safebox.GetMallItemChangeLookVnum(slotIndex)
			#elif window_type == player.ACCEREFINE:
			#	changelookvnum = player.GetAcceWindowChangeLookVnum(slotIndex)
			else:
				changelookvnum = player.GetChangeLookVnum(window_type, slotIndex)

			if not changelookvnum == 0:
				self.AppendSpace(5)
				self.AppendTextLine("[ " + localeInfo.CHANGE_LOOK_TITLE + " ]", self.CHANGELOOK_TITLE_COLOR)
				itemName = item.GetItemNameByVnum(changelookvnum)

				if item.GetItemType() == item.ITEM_TYPE_COSTUME:
					if item.GetItemSubType() == item.COSTUME_TYPE_BODY:
						malefemale = ""
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
							malefemale = localeInfo.FOR_FEMALE

						if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
							malefemale = localeInfo.FOR_MALE
						itemName += " ( " + malefemale + " )"

				textLine = self.AppendTextLine(itemName, self.CHANGELOOK_ITEMNAME_COLOR, True)
				textLine.SetFeather()

	def AppendWearableInformation(self):
		self.AppendSpace(5)
		self.AppendTextLine(localeInfo.TOOLTIP_ITEM_WEARABLE_JOB, self.NORMAL_COLOR)

		if not app.DISABLE_WOLFMAN_CREATION:
			flagList = (
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_WARRIOR),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_ASSASSIN),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_SURA),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_SHAMAN),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_WOLFMAN),
				)
		else:
			flagList = (
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_WARRIOR),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_ASSASSIN),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_SURA),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_SHAMAN),
				)

		characterNames = ""
		for i in range(self.CHARACTER_COUNT):
			name = self.CHARACTER_NAMES[i]
			flag = flagList[i]

			if flag:
				characterNames += " "
				characterNames += name

		textLine = self.AppendTextLine(characterNames, self.NORMAL_COLOR, True)
		textLine.SetFeather()

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
			textLine = self.AppendTextLine(localeInfo.FOR_FEMALE, self.NORMAL_COLOR, True)
			textLine.SetFeather()

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
			textLine = self.AppendTextLine(localeInfo.FOR_MALE, self.NORMAL_COLOR, True)
			textLine.SetFeather()

	def __AppendPotionInformation(self):
		self.AppendSpace(5)

		healHP = item.GetValue(0)
		healSP = item.GetValue(1)
		healStatus = item.GetValue(2)
		healPercentageHP = item.GetValue(3)
		healPercentageSP = item.GetValue(4)

		if healHP > 0:
			self.AppendTextLine(localeInfo.TOOLTIP_POTION_PLUS_HP_POINT % healHP, self.GetChangeTextLineColor(healHP))
		if healSP > 0:
			self.AppendTextLine(localeInfo.TOOLTIP_POTION_PLUS_SP_POINT % healSP, self.GetChangeTextLineColor(healSP))
		if healStatus != 0:
			self.AppendTextLine(localeInfo.TOOLTIP_POTION_CURE)
		if healPercentageHP > 0:
			self.AppendTextLine(localeInfo.TOOLTIP_POTION_PLUS_HP_PERCENT % healPercentageHP, self.GetChangeTextLineColor(healPercentageHP))
		if healPercentageSP > 0:
			self.AppendTextLine(localeInfo.TOOLTIP_POTION_PLUS_SP_PERCENT % healPercentageSP, self.GetChangeTextLineColor(healPercentageSP))

	def __AppendAbilityPotionInformation(self):
		self.AppendSpace(5)

		abilityType = item.GetValue(0)
		time = item.GetValue(1)
		point = item.GetValue(2)

		if abilityType == item.APPLY_ATT_SPEED:
			self.AppendTextLine(localeInfo.TOOLTIP_POTION_PLUS_ATTACK_SPEED % point, self.GetChangeTextLineColor(point))
		elif abilityType == item.APPLY_MOV_SPEED:
			self.AppendTextLine(localeInfo.TOOLTIP_POTION_PLUS_MOVING_SPEED % point, self.GetChangeTextLineColor(point))

		if time > 0:
			minute = (time // 60)
			second = (time % 60)
			timeString = localeInfo.TOOLTIP_POTION_TIME

			if minute > 0:
				timeString += str(minute) + localeInfo.TOOLTIP_POTION_MIN
			if second > 0:
				timeString += " " + str(second) + localeInfo.TOOLTIP_POTION_SEC

			self.AppendTextLine(timeString)

	def GetPriceColor(self, price):
		if price >= constInfo.HIGH_PRICE:
			return self.HIGH_PRICE_COLOR
		if price >= constInfo.MIDDLE_PRICE:
			return self.MIDDLE_PRICE_COLOR
		else:
			return self.LOW_PRICE_COLOR

	def AppendPrice(self, price):
		self.AppendSpace(5)
		self.AppendTextLineDontCheckColor(localeInfo.TOOLTIP_BUYPRICE % (localeInfo.NumberToMoneyString(price)), self.GetPriceColor(price))

	if app.ENABLE_SHOP_SEARCH:
		def AppendPriceOfflineShop(self, price, priceColor):
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_BUYPRICE % (localeInfo.NumberToMoneyString(price)), self.GetPriceColor(price))

	def AppendPriceBySecondaryCoin(self, price):
		self.AppendSpace(5)
		self.AppendTextLineDontCheckColor(localeInfo.TOOLTIP_BUYPRICE % (localeInfo.NumberToSecondaryCoinString(price)), self.GetPriceColor(price))

	def AppendSellingPrice(self, price):
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_SELL):
			self.AppendTextLineDontCheckColor(localeInfo.TOOLTIP_ANTI_SELL, self.DISABLE_COLOR)
			self.AppendSpace(5)
		else:
			self.AppendTextLineDontCheckColor(localeInfo.TOOLTIP_SELLPRICE % (localeInfo.NumberToMoneyString(price)), self.GetPriceColor(price))
			self.AppendSpace(5)

	def AppendMetinInformation(self):
		affectType, affectValue = item.GetAffect(0)
		#affectType = item.GetValue(0)
		#affectValue = item.GetValue(1)

		affectString = self.__GetAffectString(affectType, affectValue)

		if affectString:
			self.AppendSpace(5)
			self.AppendTextLine(affectString, self.GetChangeTextLineColor(affectValue))

	def AppendMetinWearInformation(self):
		self.AppendSpace(5)
		self.AppendTextLine(localeInfo.TOOLTIP_SOCKET_REFINABLE_ITEM, self.NORMAL_COLOR)

		flagList = (
			item.IsWearableFlag(item.WEARABLE_BODY),
			item.IsWearableFlag(item.WEARABLE_HEAD),
			item.IsWearableFlag(item.WEARABLE_FOOTS),
			item.IsWearableFlag(item.WEARABLE_WRIST),
			item.IsWearableFlag(item.WEARABLE_WEAPON),
			item.IsWearableFlag(item.WEARABLE_NECK),
			item.IsWearableFlag(item.WEARABLE_EAR),
			item.IsWearableFlag(item.WEARABLE_UNIQUE),
			item.IsWearableFlag(item.WEARABLE_SHIELD),
			item.IsWearableFlag(item.WEARABLE_ARROW)
		)

		wearNames = ""
		for i in range(self.WEAR_COUNT):
			name = self.WEAR_NAMES[i]
			flag = flagList[i]

			if flag:
				wearNames += " "
				wearNames += name

		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetFontName(self.defFontName)
		textLine.SetPosition(self.toolTipWidth//2, self.toolTipHeight)
		textLine.SetHorizontalAlignCenter()
		textLine.SetPackedFontColor(self.NORMAL_COLOR)
		textLine.SetText(wearNames)
		textLine.Show()
		self.childrenList.append(textLine)

		self.toolTipHeight += self.TEXT_LINE_HEIGHT
		self.ResizeToolTip()

	def GetMetinSocketType(self, number):
		if player.METIN_SOCKET_TYPE_NONE == number:
			return player.METIN_SOCKET_TYPE_NONE
		elif player.METIN_SOCKET_TYPE_SILVER == number:
			return player.METIN_SOCKET_TYPE_SILVER
		elif player.METIN_SOCKET_TYPE_GOLD == number:
			return player.METIN_SOCKET_TYPE_GOLD
		else:
			if app.WJ_NEW_USER_CARE:
				if item.SelectItem(number) == False:
					return player.METIN_SOCKET_TYPE_NONE
				else:
					if item.METIN_NORMAL == item.GetItemSubType():
						return player.METIN_SOCKET_TYPE_SILVER
					elif item.METIN_GOLD == item.GetItemSubType():
						return player.METIN_SOCKET_TYPE_GOLD
					elif "USE_PUT_INTO_ACCESSORY_SOCKET" == item.GetUseType(number):
						return player.METIN_SOCKET_TYPE_SILVER
					elif "USE_PUT_INTO_RING_SOCKET" == item.GetUseType(number):
						return player.METIN_SOCKET_TYPE_SILVER
					elif "USE_PUT_INTO_BELT_SOCKET" == item.GetUseType(number):
						return player.METIN_SOCKET_TYPE_SILVER
			else:
				item.SelectItem(number)
				if item.METIN_NORMAL == item.GetItemSubType():
					return player.METIN_SOCKET_TYPE_SILVER
				elif item.METIN_GOLD == item.GetItemSubType():
					return player.METIN_SOCKET_TYPE_GOLD
				elif "USE_PUT_INTO_ACCESSORY_SOCKET" == item.GetUseType(number):
					return player.METIN_SOCKET_TYPE_SILVER
				elif "USE_PUT_INTO_RING_SOCKET" == item.GetUseType(number):
					return player.METIN_SOCKET_TYPE_SILVER
				elif "USE_PUT_INTO_BELT_SOCKET" == item.GetUseType(number):
					return player.METIN_SOCKET_TYPE_SILVER

		return player.METIN_SOCKET_TYPE_NONE

	def GetMetinItemIndex(self, number):
		if player.METIN_SOCKET_TYPE_SILVER == number:
			return 0
		if player.METIN_SOCKET_TYPE_GOLD == number:
			return 0

		return number

	def __AppendAccessoryMetinSlotInfo(self, metinSlot, mtrlVnum):
		ACCESSORY_SOCKET_MAX_SIZE = 3

		if app.ENABLE_PERMA_ACCESSORY:
			realSocketGrade = int(math.ceil( (metinSlot[0] / 10.0)))
			
			if metinSlot[0] < 10:
				realSocketGrade = metinSlot[0]
			elif metinSlot[0] < 20 and metinSlot[0] != 10:
				realSocketGrade = (metinSlot[0] - 10) + 1
				
			PermanentJewlery = 0
			if metinSlot[0] >= 10:
				PermanentJewlery+=1
			if metinSlot[0] >= 20:
				PermanentJewlery+=1
			if metinSlot[0] >= 30:
				PermanentJewlery+=1

			cur=min(realSocketGrade, ACCESSORY_SOCKET_MAX_SIZE)
		else:
			cur=min(metinSlot[0], ACCESSORY_SOCKET_MAX_SIZE)
			
		end = min(metinSlot[1], ACCESSORY_SOCKET_MAX_SIZE)

		affectType1, affectValue1 = item.GetAffect(0)
		affectList1 = [0, max(1, affectValue1 * 10 // 100), max(2, affectValue1 * 20 // 100), max(3, affectValue1 * 40 // 100)]

		affectType2, affectValue2 = item.GetAffect(1)
		affectList2 = [0, max(1, affectValue2 * 10 // 100), max(2, affectValue2 * 20 // 100), max(3, affectValue2 * 40 // 100)]

		if app.ENABLE_PERMA_ACCESSORY:
			affectType3, affectValue3 = item.GetAffect(2)
			affectList3=[0, max(1, affectValue3*10//100), max(2, affectValue3*20//100), max(3, affectValue3*40//100)]
			
			affectType4, affectValue4 = item.GetAffect(3)
			affectList4=[0, max(1, affectValue4*10//100), max(2, affectValue4*20//100), max(3, affectValue4*40//100)]			

		mtrlPos = 0
		mtrlList = [mtrlVnum] * cur + [player.METIN_SOCKET_TYPE_SILVER] * (end - cur)
		for mtrl in mtrlList:
			affectString1 = self.__GetAffectString(affectType1, affectList1[mtrlPos + 1] - affectList1[mtrlPos])
			affectString2 = self.__GetAffectString(affectType2, affectList2[mtrlPos + 1] - affectList2[mtrlPos])
			if app.ENABLE_PERMA_ACCESSORY:
				affectString3 = self.__GetAffectString(affectType3, affectList3[mtrlPos+1]-affectList3[mtrlPos])
				affectString4 = self.__GetAffectString(affectType4, affectList4[mtrlPos+1]-affectList4[mtrlPos])

			leftTime = 0
			
			if app.ENABLE_PERMA_ACCESSORY:
				if mtrlPos == 0 and PermanentJewlery >= 1:
					leftTime=-1
				elif mtrlPos == 1 and PermanentJewlery >= 2:
					leftTime=-1
				elif mtrlPos == 2 and PermanentJewlery >= 3:
					leftTime=-1
				elif cur == mtrlPos+1:
					leftTime=metinSlot[2]

				if leftTime == -1:
					isPermanent = True
				else:
					isPermanent = False
					
				self.__AppendMetinSlotInfo_AppendMetinSocketData(mtrlPos, mtrl, affectString1, affectString2, affectString3, affectString4, leftTime, isPermanent)
			else:
				if cur == mtrlPos+1:
					leftTime=metinSlot[2]
					
				self.__AppendMetinSlotInfo_AppendMetinSocketData(mtrlPos, mtrl, affectString1, affectString2, affectString3, affectString4, leftTime)
				
			mtrlPos += 1

	def __AppendMetinSlotInfo(self, metinSlot):
		if self.__AppendMetinSlotInfo_IsEmptySlotList(metinSlot):
			return

		for i in range(player.METIN_SOCKET_MAX_NUM):
			if app.ENABLE_ITEM_SOCKET5:
				if metinSlot[i] == -1:
					continue

			self.__AppendMetinSlotInfo_AppendMetinSocketData(i, metinSlot[i])

	def __AppendMetinSlotInfo_IsEmptySlotList(self, metinSlot):
		if 0 == metinSlot:
			return 1

		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlotData = metinSlot[i]
			if app.ENABLE_ITEM_SOCKET5:
				if metinSlotData == -1:
					continue

			if 0 != self.GetMetinSocketType(metinSlotData):
				if 0 != self.GetMetinItemIndex(metinSlotData):
					return 0

		return 1

	def __AppendMetinSlotInfo_AppendMetinSocketData(self, index, metinSlotData, custumAffectString="", custumAffectString2="", custumAffectString3="", custumAffectString4="", leftTime=0, isPermanent=False):
		slotType = self.GetMetinSocketType(metinSlotData)
		itemIndex = self.GetMetinItemIndex(metinSlotData)

		# 2019.12.17.owsap.Only show socket items
		# if app.ENABLE_ITEM_SOCKET5:
			# if itemIndex:
				# item.SelectItem(itemIndex)
				# if item.GetItemType() != item.ITEM_TYPE_METIN and\
					# item.GetUseType(itemIndex) != "USE_PUT_INTO_ACCESSORY_SOCKET" and\
					# item.GetUseType(itemIndex) != "USE_PUT_INTO_RING_SOCKET" and\
					# item.GetUseType(itemIndex) != "USE_PUT_INTO_BELT_SOCKET":
					# return

		if 0 == slotType:
			return

		self.AppendSpace(5)

		slotImage = ui.ImageBox()
		slotImage.SetParent(self)
		slotImage.Show()

		## Name
		nameTextLine = ui.TextLine()
		nameTextLine.SetParent(self)
		nameTextLine.SetFontName(self.defFontName)
		nameTextLine.SetPackedFontColor(self.NORMAL_COLOR)
		nameTextLine.SetOutline()
		nameTextLine.SetFeather()
		nameTextLine.Show()

		self.childrenList.append(nameTextLine)

		if player.METIN_SOCKET_TYPE_SILVER == slotType:
			slotImage.LoadImage("d:/ymir work/ui/game/windows/metin_slot_silver.sub")
		elif player.METIN_SOCKET_TYPE_GOLD == slotType:
			slotImage.LoadImage("d:/ymir work/ui/game/windows/metin_slot_gold.sub")

		self.childrenList.append(slotImage)

		if localeInfo.IsARABIC():
			slotImage.SetPosition(self.toolTipWidth - slotImage.GetWidth() - 9, self.toolTipHeight - 1)
			nameTextLine.SetPosition(self.toolTipWidth - 50, self.toolTipHeight + 2)
		else:
			slotImage.SetPosition(9, self.toolTipHeight - 1)
			nameTextLine.SetPosition(50, self.toolTipHeight + 2)

		metinImage = ui.ImageBox()
		metinImage.SetParent(self)
		metinImage.Show()
		self.childrenList.append(metinImage)

		if itemIndex:
			item.SelectItem(itemIndex)

			## Image
			try:
				if app.ENABLE_PERMA_ACCESSORY:
					if isPermanent:
						PermanentIcon = "icon/item/permanent_accessory/" + str(itemIndex) + ".tga"
						metinImage.LoadImage(PermanentIcon)
					else:
						metinImage.LoadImage(item.GetIconImageFileName())
				else:
					metinImage.LoadImage(item.GetIconImageFileName())
			except:
				dbg.TraceError("ItemToolTip.__AppendMetinSocketData() - Failed to find image file %d:%s" % 
					(itemIndex, item.GetIconImageFileName())
				)

			nameTextLine.SetText(item.GetItemName())

			## Affect
			affectTextLine = ui.TextLine()
			affectTextLine.SetParent(self)
			affectTextLine.SetFontName(self.defFontName)
			affectTextLine.SetPackedFontColor(self.POSITIVE_COLOR)
			affectTextLine.SetOutline()
			affectTextLine.SetFeather()
			affectTextLine.Show()

			if localeInfo.IsARABIC():
				metinImage.SetPosition(self.toolTipWidth - metinImage.GetWidth() - 10, self.toolTipHeight)
				affectTextLine.SetPosition(self.toolTipWidth - 50, self.toolTipHeight + 16 + 2)
			else:
				metinImage.SetPosition(10, self.toolTipHeight)
				affectTextLine.SetPosition(50, self.toolTipHeight + 16 + 2)

			if custumAffectString:
				affectTextLine.SetText(custumAffectString)
			elif itemIndex != constInfo.ERROR_METIN_STONE:
				affectType, affectValue = item.GetAffect(0)
				affectString = self.__GetAffectString(affectType, affectValue)
				if affectString:
					affectTextLine.SetText(affectString)
			else:
				affectTextLine.SetText(localeInfo.TOOLTIP_APPLY_NOAFFECT)

			self.childrenList.append(affectTextLine)

			if custumAffectString2:
				affectTextLine = ui.TextLine()
				affectTextLine.SetParent(self)
				affectTextLine.SetFontName(self.defFontName)
				affectTextLine.SetPackedFontColor(self.POSITIVE_COLOR)
				affectTextLine.SetPosition(50, self.toolTipHeight + 16 + 2 + 16 + 2)
				affectTextLine.SetOutline()
				affectTextLine.SetFeather()
				affectTextLine.Show()
				affectTextLine.SetText(custumAffectString2)
				self.childrenList.append(affectTextLine)
				self.toolTipHeight += 16 + 2

			if app.ENABLE_PERMA_ACCESSORY:
				if (not custumAffectString3) and (itemIndex!=constInfo.ERROR_METIN_STONE):
					custumAffectString3 = self.__GetAffectString(*item.GetAffect(2))
					
				if custumAffectString3:
					affectTextLine = ui.TextLine()
					affectTextLine.SetParent(self)
					affectTextLine.SetFontName(self.defFontName)
					affectTextLine.SetPackedFontColor(self.POSITIVE_COLOR)
					affectTextLine.SetPosition(50, self.toolTipHeight + 16 + 2 + 16 + 2)
					affectTextLine.SetOutline()
					affectTextLine.SetFeather()
					affectTextLine.Show()
					affectTextLine.SetText(custumAffectString3)
					self.childrenList.append(affectTextLine)
					self.toolTipHeight += 16 + 2
					
				if (not custumAffectString4) and (itemIndex!=constInfo.ERROR_METIN_STONE):
					custumAffectString4 = self.__GetAffectString(*item.GetAffect(3))
					
				if custumAffectString4:
					affectTextLine = ui.TextLine()
					affectTextLine.SetParent(self)
					affectTextLine.SetFontName(self.defFontName)
					affectTextLine.SetPackedFontColor(self.POSITIVE_COLOR)
					affectTextLine.SetPosition(50, self.toolTipHeight + 16 + 2 + 16 + 2)
					affectTextLine.SetOutline()
					affectTextLine.SetFeather()
					affectTextLine.Show()
					affectTextLine.SetText(custumAffectString4)
					self.childrenList.append(affectTextLine)
					self.toolTipHeight += 16 + 2					
					
			if 0 != leftTime:
				if app.ENABLE_PERMA_ACCESSORY:
					if leftTime == -1:
						timeText = (localeInfo.LEFT_TIME + ": "+ localeInfo.PERNAMENT_ACCESSORY)
					else:
						timeText = (localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftTime))
				else:
					timeText = (localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftTime))
				timeTextLine = ui.TextLine()
				timeTextLine.SetParent(self)
				timeTextLine.SetFontName(self.defFontName)
				timeTextLine.SetPackedFontColor(self.POSITIVE_COLOR)
				timeTextLine.SetPosition(50, self.toolTipHeight + 16 + 2 + 16 + 2)
				timeTextLine.SetOutline()
				timeTextLine.SetFeather()
				timeTextLine.Show()
				timeTextLine.SetText(timeText)
				self.childrenList.append(timeTextLine)
				self.toolTipHeight += 16 + 2

		else:
			nameTextLine.SetText(localeInfo.TOOLTIP_SOCKET_EMPTY)

		self.toolTipHeight += 35
		self.ResizeToolTip()

	def __AppendFishBonusInformation(self, fishVnum):
		# Live or dead fish -> grilled form, from the server's fishing.txt rows.
		grilledVnum = servergamedata.FISH_GRILL.get(fishVnum)
		if not grilledVnum:
			return

		item.SelectItem(grilledVnum)
		cookedName = item.GetItemName()
		applyType = item.GetValue(0)
		duration = item.GetValue(1)
		applyValue = item.GetValue(2)
		item.SelectItem(fishVnum)

		if duration <= 0 or applyValue <= 0:
			return
		affectText = self.__GetAffectString(applyType, applyValue)
		if not affectText or affectText.startswith("UNKNOWN_"):
			return

		self.AppendSpace(5)
		self.AppendTextLine(cookedName, self.CONDITION_COLOR)
		self.AppendTextLine(affectText, self.POSITIVE_COLOR)
		minute = duration // 60
		second = duration % 60
		timeParts = []
		if minute:
			timeParts.append("%d %s" % (minute, localeInfo.TOOLTIP_POTION_MIN))
		if second:
			timeParts.append("%d %s" % (second, localeInfo.TOOLTIP_POTION_SEC))
		self.AppendTextLine(localeInfo.TOOLTIP_POTION_TIME + " " + " ".join(timeParts), self.NORMAL_COLOR)

	def AppendUniqueItemLastTime(self, restMin):
		restSecond = restMin * 60
		self.AppendSpace(5)
		self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(restSecond), self.NORMAL_COLOR)

	def AppendMallItemLastTime(self, endTime, isOriginalLimit = False):
		if isOriginalLimit:
			leftSec = endTime
		else:
			leftSec = max(0, endTime - app.GetGlobalTimeStamp())
			
		if leftSec > item.MIN_INFINITE_DURATION:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.INFINITE_USE, self.CONDITION_COLOR)
			return
			
		if leftSec > 0:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftSec), self.NORMAL_COLOR)

	if app.ENABLE_COSTUME_EXTENDED_RECHARGE:
		def AppendMallItemLastTimeEx(self, endTime):
			leftSec = max(0, endTime - app.GetGlobalTimeStamp())

			if leftSec > item.MIN_INFINITE_DURATION:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.INFINITE_USE, self.CONDITION_COLOR)
				return

			if leftSec > 0:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftSec), self.NORMAL_COLOR)

	if app.ENABLE_MOUNT_COSTUME_SYSTEM:
		def __AppendMountCostumeLastTime(self, metinSlot, bHasRealtimeFlag, originalTimeLimit):
			if 1 == bHasRealtimeFlag:
				if metinSlot[0] == 0:
					self.AppendMallItemLastTime(originalTimeLimit, True)
				else:
					self.AppendMallItemLastTime(metinSlot[0])
				return

			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)
				if item.LIMIT_TIMER_BASED_ON_WEAR == limitType:
					if 0 == metinSlot[0]:
						if limitValue > 0:
							self.AppendMallItemLastTime(app.GetGlobalTimeStamp() + limitValue)
						else:
							self.AppendTimerBasedOnWearLastTime(metinSlot)
					else:
						self.AppendTimerBasedOnWearLastTime(metinSlot)
					return

			# ALTHEA-634: a seal without a real-time or wear-timer limit rides without a time limit
			# (server game/src/mount_seal_policy.h); the unique-item remaining time the server still
			# stamps from Value0 when it creates a ride item never counts down for a costume mount,
			# so it is not shown.
			return

	def AppendTimerBasedOnWearLastTime(self, metinSlot):
		if 0 == metinSlot[0]:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.CANNOT_USE, self.DISABLE_COLOR)
		elif app.ENABLE_DSS_EXTENDED_RECHARGE and metinSlot[0] > item.MIN_INFINITE_DURATION:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.INFINITE_USE, self.CONDITION_COLOR)
		else:
			endTime = app.GetGlobalTimeStamp() + metinSlot[0]
			self.AppendMallItemLastTime(endTime)

	def AppendRealTimeStartFirstUseLastTime(self, item, metinSlot, limitIndex):
		useCount = metinSlot[1]
		endTime = metinSlot[0]

		# 한 번이라도 사용했다면 Socket0에 종료 시간(2012년 3월 1일 13시 01분 같은..) 이 박혀있음.
		# 사용하지 않았다면 Socket0에 이용가능시간(이를테면 600 같은 값. 초단위)이 들어있을 수 있고, 0이라면 Limit Value에 있는 이용가능시간을 사용한다.
		if 0 == useCount:
			if 0 == endTime:
				(limitType, limitValue) = item.GetLimit(limitIndex)
				endTime = limitValue

			endTime += app.GetGlobalTimeStamp()

		self.AppendMallItemLastTime(endTime)

	if app.WJ_NEW_USER_CARE:
		def __AppendRealTimeToolTip(self, itemVnum, endTime):
			item.SelectItem(itemVnum)

			for i in range(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)

				if item.LIMIT_REAL_TIME == limitType and limitValue > 0:
					self.AppendSpace(5)
					leftSec = max(0, endTime - app.GetGlobalTimeStamp())
					if leftSec > 0:
						self.AppendTextLine(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftSec), self.NORMAL_COLOR)
					return
				else:
					continue

	if app.ENABLE_AURA_SYSTEM:
		def AppendTextLineAbsorb(self, text, color = FONT_COLOR, centerAlign = True):
			return self.__AppendBonusLine(text, color, centerAlign)

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def __GetAccePreviewAttributes(self, windowType, slotIndex):
			attrs = [player.GetItemAttribute(windowType, slotIndex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			metadataWindow = ResolveRarityInventoryWindow(windowType, slotIndex)
			self.rarityGrade = self.__GetRarityGrade(metadataWindow, slotIndex)
			if self.rarityGrade >= 3:
				context = getattr(net, "RARITY_CONTEXT_INVENTORY", 1)
				extra = GetRarityExtraSafe(context, metadataWindow, slotIndex, 0, 0)
				if extra is not None:
					attrs.append(extra)
			return attrs

		def SetAcceResultItem(self, slotIndex, window_type = player.INVENTORY):
			(itemVnum, MinAbs, MaxAbs) = acce.GetResultItem()
			if not itemVnum:
				return

			self.ClearToolTip()

			metinSlot = [player.GetItemMetinSocket(window_type, slotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = self.__GetAccePreviewAttributes(window_type, slotIndex)
			apply_random_list = []
			if app.ENABLE_APPLY_RANDOM:
				apply_random_list = [player.GetItemApplyRandom(window_type, slotIndex, i) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)]
			refine_element = player.GetItemRefineElement(window_type, slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

			item.SelectItem(itemVnum)
			itemType = item.GetItemType()
			itemSubType = item.GetItemSubType()
			if itemType != item.ITEM_TYPE_COSTUME and itemSubType != item.COSTUME_TYPE_ACCE:
				return

			absChance = MaxAbs
			itemDesc = item.GetItemDescription()
			self.__AdjustMaxWidth(attrSlot, itemDesc)
			self.__SetItemTitle(itemVnum, metinSlot, attrSlot)
			self.AppendDescription(itemDesc, 26)
			self.AppendDescription(item.GetItemSummary(), 26, self.CONDITION_COLOR)
			self.__AppendLimitInformation()

			## ABSORPTION RATE
			if MinAbs == MaxAbs:
				self.AppendTextLine(localeInfo.TOOLTIP_APPLY_ACCEDRAIN_RATE(MinAbs), self.CONDITION_COLOR)
			else:
				self.AppendTextLine(localeInfo.TOOLTIP_APPLY_ACCEDRAIN_RATE(MinAbs) + " ~ %d%%" % (MaxAbs), self.CONDITION_COLOR)
			## END ABSOPRTION RATE

			itemAbsorbedVnum = int(metinSlot[acce.ABSORBED_SOCKET])
			if itemAbsorbedVnum:
				## ATTACK / DEFENCE
				item.SelectItem(itemAbsorbedVnum)
				if item.GetItemType() == item.ITEM_TYPE_WEAPON:
					if item.GetItemSubType() == item.WEAPON_FAN:
						self.__AppendMagicAttackInfo(absChance)
						item.SelectItem(itemAbsorbedVnum)
						self.__AppendAttackPowerInfo(absChance, refine_element)
					else:
						self.__AppendAttackPowerInfo(absChance, refine_element)
						item.SelectItem(itemAbsorbedVnum)
						self.__AppendMagicAttackInfo(absChance)
				elif item.GetItemType() == item.ITEM_TYPE_ARMOR:
					defGrade = item.GetValue(1)
					defBonus = item.GetValue(5) * 2
					defGrade = self.CalcAcceValue(defGrade, absChance)
					defBonus = self.CalcAcceValue(defBonus, absChance)

					if defGrade > 0:
						self.AppendSpace(5)
						self.AppendTextLine(localeInfo.TOOLTIP_ITEM_DEF_GRADE % (defGrade + defBonus), self.GetChangeTextLineColor(defGrade))

					item.SelectItem(itemAbsorbedVnum)
					self.__AppendMagicDefenceInfo(absChance)
				## END ATTACK / DEFENCE

				## EFFECT
				item.SelectItem(itemAbsorbedVnum)
				for i in range(item.ITEM_APPLY_MAX_NUM):
					(affectType, affectValue) = item.GetAffect(i)
					affectValue = self.CalcAcceValue(affectValue, absChance)
					affectString = self.__GetAffectString(affectType, affectValue)
					if affectString and affectValue > 0:
						self.AppendTextLine(affectString, self.GetChangeTextLineColor(affectValue))

					item.SelectItem(itemAbsorbedVnum)
				# END EFFECT

				if app.ENABLE_APPLY_RANDOM:
					self.__AppendAcceDefaultItemApplyInformation(apply_random_list, metinSlot[acce.ABSORPTION_SOCKET], itemAbsorbedVnum)

			item.SelectItem(itemVnum)
			## ATTR
			self.__AppendAttributeInformation(attrSlot, MaxAbs)
			# END ATTR
			if app.ENABLE_REFINE_ELEMENT_SYSTEM:
				self.__AppendRefineElementInformationAcce(metinSlot, refine_element)

			self.AppendWearableInformation()
			self.ShowToolTip()

		def SetAcceResultAbsItem(self, slotIndex1, slotIndex2, window_type = player.INVENTORY):
			itemVnumAcce = player.GetItemIndex(window_type, slotIndex1)
			itemVnumTarget = player.GetItemIndex(window_type, slotIndex2)
			if not itemVnumAcce or not itemVnumTarget:
				return

			self.ClearToolTip()

			item.SelectItem(itemVnumAcce)
			itemType = item.GetItemType()
			itemSubType = item.GetItemSubType()
			if itemType != item.ITEM_TYPE_COSTUME and itemSubType != item.COSTUME_TYPE_ACCE:
				return

			metinSlot = [player.GetItemMetinSocket(window_type, slotIndex1, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = self.__GetAccePreviewAttributes(window_type, slotIndex2)
			apply_random_list = []
			if app.ENABLE_APPLY_RANDOM:
				apply_random_list = [player.GetItemApplyRandom(window_type, slotIndex2, i) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)]
			refine_element = player.GetItemRefineElement(window_type, slotIndex1) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None

			itemDesc = item.GetItemDescription()
			self.__AdjustMaxWidth(attrSlot, itemDesc)
			self.__SetItemTitle(itemVnumAcce, metinSlot, attrSlot)
			self.AppendDescription(itemDesc, 26)
			self.AppendDescription(item.GetItemSummary(), 26, self.CONDITION_COLOR)
			item.SelectItem(itemVnumAcce)
			self.__AppendLimitInformation()

			## ABSORPTION RATE
			self.AppendTextLine(localeInfo.TOOLTIP_APPLY_ACCEDRAIN_RATE(metinSlot[acce.ABSORPTION_SOCKET]), self.CONDITION_COLOR)
			## END ABSOPRTION RATE

			## ATTACK / DEFENCE
			itemAbsorbedVnum = itemVnumTarget
			item.SelectItem(itemAbsorbedVnum)
			if item.GetItemType() == item.ITEM_TYPE_WEAPON:
				if item.GetItemSubType() == item.WEAPON_FAN:
					self.__AppendMagicAttackInfo(metinSlot[acce.ABSORPTION_SOCKET])
					item.SelectItem(itemAbsorbedVnum)
					self.__AppendAttackPowerInfo(metinSlot[acce.ABSORPTION_SOCKET], refine_element)
				else:
					self.__AppendAttackPowerInfo(metinSlot[acce.ABSORPTION_SOCKET], refine_element)
					item.SelectItem(itemAbsorbedVnum)
					self.__AppendMagicAttackInfo(metinSlot[acce.ABSORPTION_SOCKET])
			elif item.GetItemType() == item.ITEM_TYPE_ARMOR:
				defGrade = item.GetValue(1)
				defBonus = item.GetValue(5) * 2
				defGrade = self.CalcAcceValue(defGrade, metinSlot[acce.ABSORPTION_SOCKET])
				defBonus = self.CalcAcceValue(defBonus, metinSlot[acce.ABSORPTION_SOCKET])

				if defGrade > 0:
					self.AppendSpace(5)
					self.AppendTextLine(localeInfo.TOOLTIP_ITEM_DEF_GRADE % (defGrade + defBonus), self.GetChangeTextLineColor(defGrade))

				item.SelectItem(itemAbsorbedVnum)
				self.__AppendMagicDefenceInfo(metinSlot[acce.ABSORPTION_SOCKET])
			## END ATTACK / DEFENCE

			## EFFECT
			item.SelectItem(itemAbsorbedVnum)
			for i in range(item.ITEM_APPLY_MAX_NUM):
				(affectType, affectValue) = item.GetAffect(i)
				affectValue = self.CalcAcceValue(affectValue, metinSlot[acce.ABSORPTION_SOCKET])
				affectString = self.__GetAffectString(affectType, affectValue)
				if affectString and affectValue > 0:
					self.AppendTextLine(affectString, self.GetChangeTextLineColor(affectValue))
			## END EFFECT

			if app.ENABLE_APPLY_RANDOM:
				self.__AppendAcceDefaultItemApplyInformation(apply_random_list, metinSlot[acce.ABSORPTION_SOCKET], itemAbsorbedVnum)

			if app.ENABLE_REFINE_ELEMENT_SYSTEM:
				self.__AppendRefineElementInformationAcce(metinSlot, refine_element)

			## ATTR
			item.SelectItem(itemAbsorbedVnum)
			for i in range(min(8, len(attrSlot))):
				type = attrSlot[i][0]
				value = attrSlot[i][1]
				rawValue = value
				if not value:
					continue

				value = self.CalcAcceValue(value, metinSlot[acce.ABSORPTION_SOCKET])
				affectString = self.__GetAffectString(type, value)
				if affectString and value > 0:
					affectColor = self.__GetAttributeColor(i, type, rawValue)
					self.AppendTextLine(affectString, affectColor)
				item.SelectItem(itemAbsorbedVnum)
			## END ATTR

			## WEARABLE
			item.SelectItem(itemVnumAcce)
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_ITEM_WEARABLE_JOB, self.NORMAL_COLOR)

			item.SelectItem(itemVnumAcce)
			flagList = (
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_WARRIOR),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_ASSASSIN),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_SURA),
				not item.IsAntiFlag(item.ITEM_ANTIFLAG_SHAMAN)
			)

			if not app.DISABLE_WOLFMAN_CREATION:
				flagList += (not item.IsAntiFlag(item.ITEM_ANTIFLAG_WOLFMAN),)

			characterNames = ""
			for i in range(self.CHARACTER_COUNT):
				name = self.CHARACTER_NAMES[i]
				flag = flagList[i]
				if flag:
					characterNames += " "
					characterNames += name

			textLine = self.AppendTextLine(characterNames, self.NORMAL_COLOR, True)
			textLine.SetFeather()

			item.SelectItem(itemVnumAcce)
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
				textLine = self.AppendTextLine(localeInfo.FOR_FEMALE, self.NORMAL_COLOR, True)
				textLine.SetFeather()

			if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
				textLine = self.AppendTextLine(localeInfo.FOR_MALE, self.NORMAL_COLOR, True)
				textLine.SetFeather()
			## END WEARABLE

			self.ShowToolTip()

	def __RefreshLiveWeaponBonus(self):
		previous = getattr(self, "inventoryRefreshSnapshot", None)
		if (previous is not None and previous[0] == item.EQUIPMENT_WEAPON
				and self.weaponBasePercent != itembonuspresentation.WeaponPercent(player, item)):
			self.RefreshInventoryItem(previous[0])

	if app.ENABLE_RENDER_TARGET_PREVIEW:
		def OnUpdate(self):
			self.__RefreshBonusTotals()
			self.__RefreshLiveWeaponBonus()
			ToolTip.OnUpdate(self)
			self.__RefreshCostumePreview()
			if self.mountPreviewRace > 0:
				return
			
			if self.savedItemVnum > 0:
				ctrlXOwned = keybindings.ShortcutOwner("CTRL+X")
				if not ctrlXOwned and app.IsPressed(app.DIK_LCONTROL) and app.IsPressed(app.DIK_X):
					osfInfo.RENDER_TARGET_OPEN = True
				if osfInfo.RENDER_TARGET_OPEN and self.interface:
					osfInfo.RENDER_TARGET_OPEN = False
					if osfInfo.RENDER_TARGET_ITEM_TYPE != 0:
						osfInfo.RENDER_TARGET_ITEM_VNUM = self.savedItemVnum
						self.interface.OpenRenderTargetWindow()

	else:
		def OnUpdate(self):
			self.__RefreshBonusTotals()
			self.__RefreshLiveWeaponBonus()
			ToolTip.OnUpdate(self)

class HyperlinkItemToolTip(ItemToolTip):
	def __init__(self):
		ItemToolTip.__init__(self, isPickable=True)

	def __del__(self):
		ItemToolTip.__del__(self)

	def __HyperlinkGetPostSocketIndex(self):
		import chat

		idx = chat.HYPER_LINK_ITEM_SOCKET2 + 1
		if app.ENABLE_ITEM_SOCKET5:
			idx = chat.HYPER_LINK_ITEM_SOCKET4 + 1
		return idx

	def __HyperlinkGetRefineElementStartIndex(self):
		idx = 3
		if app.ENABLE_ITEM_SOCKET5:
			idx += 5
		else:
			idx += 3
		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			idx += 1
		if app.ENABLE_APPLY_RANDOM:
			idx += 8
		return idx

	def __HyperlinkGetRefineElementTokens(self, tokens):
		import chat

		if not tokens or tokens[0] != "item":
			return None

		refineStart = self.__HyperlinkGetRefineElementStartIndex()
		if hasattr(chat, "HYPER_LINK_ITEM_REFINE_ELEMENT_APPLY_TYPE"):
			refineStart = chat.HYPER_LINK_ITEM_REFINE_ELEMENT_APPLY_TYPE

		if len(tokens) < refineStart + 8:
			return None

		return tokens[refineStart:refineStart + 8]

	def __HyperlinkIsRefineElementTokenBlock(self, refineTokens):
		if not refineTokens or len(refineTokens) < 8:
			return False

		if all(int(token, 16) == 0 for token in refineTokens):
			return True

		return self.__HyperlinkBuildRefineElement(refineTokens) != None

	def __HyperlinkParseApplyRandomList(self, applyTokens):
		apply_random_list = [(0, 0)] * player.APPLY_RANDOM_SLOT_MAX_NUM
		if not applyTokens:
			return apply_random_list

		workTokens = list(applyTokens)
		parsedList = []
		workTokens.reverse()
		while workTokens:
			key = int(workTokens.pop(), 16)
			if workTokens:
				val = int(workTokens.pop())
				parsedList.append((key, val))

		if parsedList:
			apply_random_list = parsedList + [(0, 0)] * (player.APPLY_RANDOM_SLOT_MAX_NUM - len(parsedList))

		return apply_random_list

	def __HyperlinkParseAttrSlot(self, attrTokens):
		attrSlot = [(0, 0)] * player.ATTRIBUTE_SLOT_MAX_NUM
		if not attrTokens:
			return attrSlot

		workTokens = list(attrTokens)
		parsedList = []
		workTokens.reverse()
		while workTokens:
			key = int(workTokens.pop(), 16)
			if workTokens:
				val = int(workTokens.pop())
				parsedList.append((key, val))

		if parsedList:
			attrSlot = parsedList + [(0, 0)] * (player.ATTRIBUTE_SLOT_MAX_NUM - len(parsedList))

		return attrSlot

	def __HyperlinkBuildRefineElement(self, refineTokens):
		if not refineTokens or len(refineTokens) < 8:
			return None

		values = [int(token, 16) for token in refineTokens]
		if all(value == 0 for value in values):
			return None

		apply_type = values[0]
		grade = values[1]
		if grade <= 0 or grade > self.REFINE_ELEMENT_INDEX_MAX:
			return None

		if apply_type not in uiRefine.REFINE_ELEMENT_KIND_TUPLE:
			return None

		return (
			apply_type,
			grade,
			(values[2], values[3], values[4]),
			(values[5], values[6], values[7]),
		)

	def __HyperlinkTryConsumeRefineElement(self, tokens):
		refineStart = self.__HyperlinkGetRefineElementStartIndex()

		if not app.ENABLE_REFINE_ELEMENT_SYSTEM:
			return None, refineStart

		refineTokens = self.__HyperlinkGetRefineElementTokens(tokens)
		if refineTokens == None:
			return None, refineStart

		if self.__HyperlinkIsRefineElementTokenBlock(refineTokens):
			return self.__HyperlinkBuildRefineElement(refineTokens), refineStart + 8

		return None, refineStart

	def SetHyperlinkItem(self, tokens):
		import chat

		if app.ENABLE_ITEM_SOCKET5:
			minTokenCount = chat.HYPER_LINK_ITEM_SOCKET4 + 1
		else:
			minTokenCount = chat.HYPER_LINK_ITEM_SOCKET2 + 1

		if not tokens or len(tokens) < minTokenCount:
			return

		head, vnum, flag = tokens[:chat.HYPER_LINK_ITEM_FLAGS + 1]
		itemVnum = int(vnum, 16)

		if app.ENABLE_ITEM_SOCKET5:
			socketEndIndex = chat.HYPER_LINK_ITEM_SOCKET4
		else:
			socketEndIndex = chat.HYPER_LINK_ITEM_SOCKET2

		metinSlot = [int(metin, 16) for metin in tokens[chat.HYPER_LINK_ITEM_SOCKET0:socketEndIndex + 1]]

		changelookvnum = 0
		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if hasattr(chat, "HYPER_LINK_ITEM_CHANGE_ITEM_VNUM"):
				changelookvnum = int(tokens[chat.HYPER_LINK_ITEM_CHANGE_ITEM_VNUM], 16)
			else:
				changelookvnum = int(tokens[self.__HyperlinkGetPostSocketIndex()], 16)

		apply_random_list = [(0, 0)] * player.APPLY_RANDOM_SLOT_MAX_NUM
		if app.ENABLE_APPLY_RANDOM:
			if hasattr(chat, "HYPER_LINK_ITEM_APPLY_RANDOM_TYPE0"):
				applyTokens = tokens[
					chat.HYPER_LINK_ITEM_APPLY_RANDOM_TYPE0:chat.HYPER_LINK_ITEM_APPLY_RANDOM_VALUE3 + 1
				]
			else:
				tokenIdx = self.__HyperlinkGetPostSocketIndex()
				if app.ENABLE_CHANGE_LOOK_SYSTEM:
					tokenIdx += 1
				applyTokens = tokens[tokenIdx:tokenIdx + 8]
			apply_random_list = self.__HyperlinkParseApplyRandomList(applyTokens)

		refine_element = None
		attrStartIndex = self.__HyperlinkGetRefineElementStartIndex()
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			refine_element, attrStartIndex = self.__HyperlinkTryConsumeRefineElement(tokens)

		attrTokens = tokens[attrStartIndex:]

		attrSlot = self.__HyperlinkParseAttrSlot(attrTokens)

		self.ClearToolTip()
		self.AddItemData(itemVnum, metinSlot, attrSlot, None, 0, 0, player.INVENTORY, -1, refine_element, apply_random_list, 0)

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.AppendChangeLookInfoItemVnum(changelookvnum)

		ItemToolTip.OnUpdate(self)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def SetHyperlinkPetItem(self, tokens):
		
			defaultTokenCount = 3 + 4 #player.METIN_SOCKET_MAX_NUM			
			petTokenCount = defaultTokenCount + 11 + (player.PET_SKILL_COUNT_MAX * 2)
			
			if tokens and len(tokens) == petTokenCount:
			
				head, vnum, flag = tokens[:3]
				itemVnum = int(vnum, 16)
				metinSlot = [int(metin, 16) for metin in tokens[3:7]]
				
				attrSlot = [(0, 0)] * player.ATTRIBUTE_SLOT_MAX_NUM
				
				print(itemVnum)
				print(metinSlot)
				print(tokens[7:])

				self.ClearToolTip()
				self.AddHyperLinkPetItemData(itemVnum, metinSlot, attrSlot, tokens[7:])
				ItemToolTip.OnUpdate(self)

	def OnUpdate(self):
		pass

	def OnMouseLeftButtonDown(self):
		self.Hide()

class SkillToolTip(ToolTip):
	TEXT_LINE_HEIGHT = 15

	POINT_NAME_DICT = {
		player.LEVEL : localeInfo.SKILL_TOOLTIP_LEVEL,
		player.IQ : localeInfo.SKILL_TOOLTIP_INT,
	}

	SKILL_TOOL_TIP_WIDTH = 236
	PARTY_SKILL_TOOL_TIP_WIDTH = 340

	PARTY_SKILL_EXPERIENCE_AFFECT_LIST = (
		( 2, 2, 10,),
		( 8, 3, 20,),
		(14, 4, 30,),
		(22, 5, 45,),
		(28, 6, 60,),
		(34, 7, 80,),
		(38, 8, 100,),
	)

	PARTY_SKILL_PLUS_GRADE_AFFECT_LIST = (
		( 4, 2, 1, 0,),
		(10, 3, 2, 0,),
		(16, 4, 2, 1,),
		(24, 5, 2, 2,),
	)

	PARTY_SKILL_ATTACKER_AFFECT_LIST = (
		( 36, 3, ),
		( 26, 1, ),
		( 32, 2, ),
	)

	SKILL_GRADE_NAME = {
		player.SKILL_GRADE_MASTER : localeInfo.SKILL_GRADE_NAME_MASTER,
		player.SKILL_GRADE_GRAND_MASTER : localeInfo.SKILL_GRADE_NAME_GRAND_MASTER,
		player.SKILL_GRADE_PERFECT_MASTER : localeInfo.SKILL_GRADE_NAME_PERFECT_MASTER,
	}
	if SKILL_GRADE_SAGE_MASTER is not None:
		SKILL_GRADE_NAME[SKILL_GRADE_SAGE_MASTER] = localeInfo.SKILL_GRADE_NAME_SAGE_MASTER

	AFFECT_NAME_DICT = {
		"HP" : localeInfo.TOOLTIP_SKILL_AFFECT_ATT_POWER,
		"ATT_GRADE" : localeInfo.TOOLTIP_SKILL_AFFECT_ATT_GRADE,
		"DEF_GRADE" : localeInfo.TOOLTIP_SKILL_AFFECT_DEF_GRADE,
		"ATT_SPEED" : localeInfo.TOOLTIP_SKILL_AFFECT_ATT_SPEED,
		"MOV_SPEED" : localeInfo.TOOLTIP_SKILL_AFFECT_MOV_SPEED,
		"DODGE" : localeInfo.TOOLTIP_SKILL_AFFECT_DODGE,
		"RESIST_NORMAL" : localeInfo.TOOLTIP_SKILL_AFFECT_RESIST_NORMAL,
		"REFLECT_MELEE" : localeInfo.TOOLTIP_SKILL_AFFECT_REFLECT_MELEE,
	}

	AFFECT_APPEND_TEXT_DICT = {
		"DODGE" : "%",
		"RESIST_NORMAL" : "%",
		"REFLECT_MELEE" : "%",
	}

	def __init__(self):
		ToolTip.__init__(self, self.SKILL_TOOL_TIP_WIDTH)
		self.SetPersonalStyle()

	def ClearToolTip(self):
		ToolTip.ClearToolTip(self)
		self.SetPersonalStyle()

	def SetPersonalStyle(self):
		self.personalStyle = True
		self.toolTipWidth = self.SKILL_TOOL_TIP_WIDTH
		self.defFontName = fontconfig.FontForRole(fontconfig.ROLE_DENSE, 0)

	def SetTitle(self, name):
		if not getattr(self, 'personalStyle', False):
			return ToolTip.SetTitle(self, name)
		font, height = self.defFontName, self.TEXT_LINE_HEIGHT
		try:
			self.defFontName = fontconfig.FontForRole(fontconfig.ROLE_WINDOW_TITLE, 0)
			self.TEXT_LINE_HEIGHT = 19
			self.AppendTextLine(name, pvmpersonaltext.LEVEL_COLOR)
		finally:
			self.defFontName, self.TEXT_LINE_HEIGHT = font, height
		self.AppendSpace(3)

	def AppendPersonalSeparator(self):
		line = ui.Line()
		line.SetParent(self)
		line.AddFlag('not_pick')
		line.SetPosition(14, self.toolTipHeight + 5)
		line.SetSize(self.toolTipWidth - 28, 0)
		line.SetColor(grp.GenerateColor(0.32, 0.28, 0.21, 1.0))
		line.Show()
		self.childrenList.append(line)
		ToolTip.AppendSpace(self, 14)

	def AppendTextLine(self, text, color=ToolTip.FONT_COLOR, centerAlign=True):
		personal = getattr(self, 'personalStyle', False)
		if personal:
			centerAlign = False
		measureLine = ui.TextLine()
		measureLine.SetFontName(self.defFontName)
		def measure(value):
			measureLine.SetText(value)
			return measureLine.GetTextSize()[0]

		# Native packed colors cross a signed-int Python binding.
		if color > 0x7fffffff:
			color -= 0x100000000
		lines = skilltooltiptext.Wrap(text, self.toolTipWidth - (28 if personal else 24), measure)
		for line in lines or ['']:
			textLine = ToolTip.AppendTextLine(self, line, color, centerAlign)
			if personal:
				textLine.SetPosition(14, textLine.GetLocalPosition()[1])
		return textLine

	def AutoAppendTextLine(self, text, color=ToolTip.FONT_COLOR, centerAlign=True):
		return self.AppendTextLine(text, color, centerAlign)

	def AutoAppendNewTextLineResize(self, text, color=ToolTip.FONT_COLOR, centerAlign=True):
		return self.AppendTextLine(text, color, centerAlign)

	def AppendSpace(self, size):
		ToolTip.AppendSpace(self, min(size, 3))

	def AppendDescription(self, desc, limit, color=ToolTip.FONT_COLOR):
		if desc:
			self.AppendSpace(3)
			self.AppendTextLine(desc.replace('|', '\n'), color)

	def __del__(self):
		ToolTip.__del__(self)

	if app.ENABLE_RENEWAL_AFFECT_SHOWER:
		def SetSkillEx(self, skillIndex, skillLevel = -1, color = None):
			if 0 == skillIndex:
				return
			slotIndex = player.GetSkillSlotIndex(skillIndex)
			skillCurrentPercentage = player.GetSkillCurrentEfficientPercentage(slotIndex)
			for i in range(skill.GetSkillAffectDescriptionCount(skillIndex)):
				affectText = skill.GetSkillAffectDescription(skillIndex, i, skillCurrentPercentage)
				self.AppendTextLine(affectText, color if color is not None else bonuscolor.Text(affectText))
			self.ResizeToolTip()

	def SetSkill(self, skillIndex, skillLevel = -1):
		if 0 == skillIndex:
			return

		if skill.SKILL_TYPE_GUILD == skill.GetSkillType(skillIndex):
			if self.SKILL_TOOL_TIP_WIDTH != self.toolTipWidth:
				self.toolTipWidth = self.SKILL_TOOL_TIP_WIDTH
				self.ResizeToolTip()

			self.AppendDefaultData(skillIndex)
			self.AppendSkillConditionData(skillIndex)
			self.AppendGuildSkillData(skillIndex, skillLevel)

		else:
			if self.SKILL_TOOL_TIP_WIDTH != self.toolTipWidth:
				self.toolTipWidth = self.SKILL_TOOL_TIP_WIDTH
				self.ResizeToolTip()

			slotIndex = player.GetSkillSlotIndex(skillIndex)
			skillGrade = player.GetSkillGrade(slotIndex)
			skillLevel = player.GetSkillLevel(slotIndex)
			skillCurrentPercentage = player.GetSkillCurrentEfficientPercentage(slotIndex)
			skillNextPercentage = player.GetSkillNextEfficientPercentage(slotIndex)

			self.AppendDefaultData(skillIndex)
			self.AppendSkillConditionData(skillIndex)
			self.AppendSkillDataNew(slotIndex, skillIndex, skillGrade, skillLevel, skillCurrentPercentage, skillNextPercentage)
			self.AppendSkillRequirement(skillIndex, skillLevel)

		self.ShowToolTip()

	def SetSkillNew(self, slotIndex, skillIndex, skillGrade, skillLevel):
		import dewcatalog
		if skillIndex == dewcatalog.MASTERY_SKILL:
			rank = dewcatalog.mastery_rank(skillGrade, skillLevel)
			self.ClearToolTip()
			self.__SetSkillTitle(skillIndex, skillGrade)
			self.AppendDescription(skill.GetSkillDescription(skillIndex), 25)
			self.AppendSpace(5)
			tenths = dewcatalog.mastery_tenths(rank)
			self.AppendTextLine("Stupeň: %d / %d" % (rank, dewcatalog.MAX_RANK), self.NORMAL_COLOR)
			self.AppendTextLine("Síla ros: +%d,%d %%" % (tenths // 10, tenths % 10), bonuscolor.Value(tenths))
			durationBonus = dewcatalog.mastery_duration_bonus(rank)
			if durationBonus > 0:
				self.AppendTextLine("Doba ros: +%d min" % (durationBonus // 60), self.POSITIVE_COLOR)
			if rank < dewcatalog.MAX_RANK:
				nextTenths = dewcatalog.mastery_tenths(rank + 1)
				self.AppendTextLine("Po další knize: +%d,%d %%" % (nextTenths // 10, nextTenths % 10), self.POSITIVE_COLOR)
			self.ShowToolTip()
			return
		if 0 == skillIndex:
			return

		if player.SKILL_INDEX_TONGSOL == skillIndex:
			slotIndex = player.GetSkillSlotIndex(skillIndex)
			skillLevel = player.GetSkillLevel(slotIndex)

			self.AppendDefaultData(skillIndex)
			self.__AppendLeaderShipSkillData(skillGrade, skillLevel)

		elif app.ENABLE_PARTY_PROFICY and player.SKILL_INDEX_ROLE_PROFICIENCY == skillIndex:
			slotIndex = player.GetSkillSlotIndex(skillIndex)
			skillLevel = player.GetSkillLevel(slotIndex)

			self.AppendDefaultData(skillIndex)
			self.__AppendRoleProficiencySkillData(skillGrade, skillLevel)

		elif app.ENABLE_SKILL_DURATION and player.SKILL_INDEX_TIME_MASTER == skillIndex:
			skillTextList = {
				player.SKILL_INDEX_TIME_MASTER:[localeInfo.SKILL_INDEX_TIME_MASTER, 45],
			}
			maxLevel = 40
			realSkillLevel = skillLevel
			if 1 == skillGrade:
				realSkillLevel += 19
			elif 2 == skillGrade:
				realSkillLevel += 29
			elif 3 == skillGrade:
				realSkillLevel = 40

			self.ClearToolTip()
			self.__SetSkillTitle(skillIndex, skillGrade)
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL_MASTER % (realSkillLevel), self.NORMAL_COLOR)
			if skillIndex not in skillTextList:
				return
			skillData = skillTextList[skillIndex]
			if maxLevel == realSkillLevel:
				value = skillData[1]
			else:
				value = int(realSkillLevel * float(float(skillData[1]) / float(maxLevel)))
			self.AppendTextLine(skillData[0] % (value, skillData[1]), bonuscolor.Value(value))
			self.ShowToolTip()
			return

		elif app.ENABLE_PARTY_INSIGHT and player.SKILL_INDEX_INSIGHT == skillIndex:
			slotIndex = player.GetSkillSlotIndex(skillIndex)
			skillLevel = player.GetSkillLevel(slotIndex)

			self.AppendDefaultData(skillIndex)
			self.__AppendInSightSkillData(skillGrade, skillLevel)

		elif player.SKILL_INDEX_RIDING == skillIndex:
			slotIndex = player.GetSkillSlotIndex(skillIndex)
			self.AppendSupportSkillDefaultData(skillIndex, skillGrade, skillLevel, 30)

		elif player.SKILL_INDEX_SUMMON == skillIndex:
			maxLevel = 10

			self.ClearToolTip()
			self.__SetSkillTitle(skillIndex, skillGrade)

			## Description
			description = skill.GetSkillDescription(skillIndex)
			self.AppendDescription(description, 25)

			if skillLevel == 10:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL_MASTER % (skillLevel), self.NORMAL_COLOR)
				self.AppendTextLine(localeInfo.SKILL_SUMMON_DESCRIPTION % (skillLevel * 10), self.NORMAL_COLOR)

			else:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL % (skillLevel), self.NORMAL_COLOR)
				self.__AppendSummonDescription(skillLevel, self.NORMAL_COLOR)

				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL % (skillLevel + 1), self.NEGATIVE_COLOR)
				self.__AppendSummonDescription(skillLevel + 1, self.NEGATIVE_COLOR)

		elif skill.SKILL_TYPE_GUILD == skill.GetSkillType(skillIndex):
			if self.SKILL_TOOL_TIP_WIDTH != self.toolTipWidth:
				self.toolTipWidth = self.SKILL_TOOL_TIP_WIDTH
				self.ResizeToolTip()

			self.AppendDefaultData(skillIndex)
			self.AppendSkillConditionData(skillIndex)
			self.AppendGuildSkillData(skillIndex, skillLevel)

		else:
			if self.SKILL_TOOL_TIP_WIDTH != self.toolTipWidth:
				self.toolTipWidth = self.SKILL_TOOL_TIP_WIDTH
				self.ResizeToolTip()

			slotIndex = player.GetSkillSlotIndex(skillIndex)

			skillCurrentPercentage = player.GetSkillCurrentEfficientPercentage(slotIndex)
			skillNextPercentage = player.GetSkillNextEfficientPercentage(slotIndex)

			self.AppendDefaultData(skillIndex, skillGrade)
			self.AppendSkillConditionData(skillIndex)
			self.AppendSkillDataNew(slotIndex, skillIndex, skillGrade, skillLevel, skillCurrentPercentage, skillNextPercentage)
			self.AppendSkillRequirement(skillIndex, skillLevel)

		self.ShowToolTip()

	if app.ENABLE_BUFF_SYSTEM:
		def AppendSupportSkillDescription(self, skillIndex, skillPercentage, color):
			affectDataCount = skill.GetNewAffectDataCount(skillIndex)
			if affectDataCount > 0:
				for i in range(affectDataCount):
					type, minValue, maxValue = skill.GetNewAffectData(skillIndex, i, skillPercentage, 1)

					if type not in self.AFFECT_NAME_DICT:
						continue

					minValue = int(minValue)
					maxValue = int(maxValue)
					affectText = self.AFFECT_NAME_DICT[type]

					if "HP" == type:
						if minValue < 0 and maxValue < 0:
							minValue *= -1
							maxValue *= -1

						else:
							affectText = localeInfo.TOOLTIP_SKILL_AFFECT_HEAL

					affectText += str(minValue)
					if minValue != maxValue:
						affectText += " - " + str(maxValue)
					affectText += self.AFFECT_APPEND_TEXT_DICT.get(type, "")

					self.AppendTextLine(affectText, bonuscolor.Text(affectText))

			else:
				for i in range(skill.GetSkillAffectDescriptionCount(skillIndex)):
					affectText = skill.GetSkillAffectDescription(skillIndex, i, skillPercentage, 1)
					self.AppendTextLine(affectText, bonuscolor.Text(affectText))
	
		def AppendSupportSkillData(self, skillIndex, skillGrade, skillLevel, skillCurrentPercentage, skillNextPercentage):
			self.skillMaxLevelStartDict = { 0 : 17, 1 : 7, 2 : 10, }
			self.skillMaxLevelEndDict = { 0 : 20, 1 : 10, 2 : 10, }

			skillLevelUpPoint = 1
			realSkillGrade = skillGrade - 1
			skillMaxLevelStart = self.skillMaxLevelStartDict.get(realSkillGrade, 15)
			skillMaxLevelEnd = self.skillMaxLevelEndDict.get(realSkillGrade, 20)

			## Current Level
			if skillLevel > 0:
				if self.HasSkillLevelDescription(skillIndex, skillLevel):
					self.AppendSpace(5)
					if skillGrade == skill.SKILL_GRADE_COUNT:
						pass
					elif skillLevel == skillMaxLevelEnd:
						self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL_MASTER % (skillLevel), self.NORMAL_COLOR)
					else:
						self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL % (skillLevel), self.NORMAL_COLOR)
					self.AppendSupportSkillDescription(skillIndex, skillCurrentPercentage, self.ENABLE_COLOR)

			## Next Level
			if skillGrade != skill.SKILL_GRADE_COUNT:
				if skillLevel < skillMaxLevelEnd:
					if self.HasSkillLevelDescription(skillIndex, skillLevel+skillLevelUpPoint):
						self.AppendSpace(5)
						self.AppendTextLine(localeInfo.TOOLTIP_NEXT_SKILL_LEVEL_1 % (skillLevel+1, skillMaxLevelEnd), self.DISABLE_COLOR)
						self.AppendSupportSkillDescription(skillIndex, skillNextPercentage, self.DISABLE_COLOR)
		
		def SetSupportSkill(self, skillIndex, skillLevel, skillGrade, skillRealLvl):
			self.ClearToolTip()

			skillCurrentPercentage = player.GetSupportSkillCurrentEfficientPercentage(skillRealLvl)
			skillNextPercentage = player.GetSupportSkillNextEfficientPercentage(skillRealLvl)

			self.AppendDefaultData(skillIndex, skillGrade)
			self.AppendSkillConditionData(skillIndex)
			self.AppendSupportSkillData(skillIndex, skillGrade, skillLevel, skillCurrentPercentage, skillNextPercentage)

			self.ShowToolTip()

	def __SetSkillTitle(self, skillIndex, skillGrade):
		personal = pvmpersonal.current()
		if personal and skillIndex in personal.rows:
			self.SetTitle(pvmpersonaltext.title(skillIndex, skill.GetSkillName(skillIndex), app.GetTime()))
			return
		# Older descriptors populate only grade-name slots 0-2. The native
		# getter accepts P (3) too, so fall back when that name is empty.
		name = skill.GetSkillName(skillIndex, skillGrade) or skill.GetSkillName(skillIndex)
		self.SetTitle(name)
		self.__AppendSkillGradeName(skillIndex, skillGrade)

	def __AppendSkillGradeName(self, skillIndex, skillGrade):
		if skillGrade in self.SKILL_GRADE_NAME:
			self.AppendSpace(5)
			self.AppendTextLine(self.SKILL_GRADE_NAME[skillGrade] % (skill.GetSkillName(skillIndex, 0)), self.CAN_LEVEL_UP_COLOR)

	def SetSkillOnlyName(self, slotIndex, skillIndex, skillGrade):
		if 0 == skillIndex:
			return

		slotIndex = player.GetSkillSlotIndex(skillIndex)

		self.toolTipWidth = self.SKILL_TOOL_TIP_WIDTH
		self.ResizeToolTip()

		self.ClearToolTip()
		self.__SetSkillTitle(skillIndex, skillGrade)
		self.AppendDefaultData(skillIndex, skillGrade)
		self.AppendSkillConditionData(skillIndex)
		self.ShowToolTip()

	def AppendDefaultData(self, skillIndex, skillGrade = 0):
		self.ClearToolTip()
		personal = pvmpersonal.current()
		row = personal.rows.get(skillIndex) if personal else None
		if row is not None:
			self.SetPersonalStyle()
		self.__SetSkillTitle(skillIndex, skillGrade)

		## Level Limit
		levelLimit = skill.GetSkillLevelLimit(skillIndex)
		if levelLimit > 0:
			color = self.NORMAL_COLOR
			if player.GetStatus(player.LEVEL) < levelLimit:
				color = self.NEGATIVE_COLOR

			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_LEVEL % (levelLimit), color)

		if row is not None and not row['hud']:
			# Replaced buff descriptions must describe the actual current bonus.
			self.AppendDescription(pvmpersonaltext.cast_description(row), 25)
		else:
			self.AppendDescription(skill.GetSkillDescription(skillIndex), 25)

	def AppendSupportSkillDefaultData(self, skillIndex, skillGrade, skillLevel, maxLevel):
		self.ClearToolTip()
		self.__SetSkillTitle(skillIndex, skillGrade)

		if 1 == skillGrade:
			skillLevel += 19
		elif 2 == skillGrade:
			skillLevel += 29
		elif 3 == skillGrade:
			skillLevel = 40

		## Description
		description = skill.GetSkillDescription(skillIndex)
		self.AppendDescription(description, 25)
		self.AppendSpace(5)
		self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL_WITH_MAX % (skillLevel, maxLevel), self.NORMAL_COLOR)

	def AppendSkillConditionData(self, skillIndex):
		if pvmpersonal.current() and skillIndex in pvmpersonal.CAST_SKILLS:
			return
		conditionDataCount = skill.GetSkillConditionDescriptionCount(skillIndex)
		if conditionDataCount > 0:
			self.AppendSpace(5)
			for i in range(conditionDataCount):
				self.AppendTextLine(skill.GetSkillConditionDescription(skillIndex, i), self.CONDITION_COLOR)

	def AppendGuildSkillData(self, skillIndex, skillLevel):
		skillMaxLevel = 7
		skillCurrentPercentage = float(skillLevel) / float(skillMaxLevel)
		skillNextPercentage = float(skillLevel+1) / float(skillMaxLevel)
		## Current Level
		if skillLevel > 0:
			if self.HasSkillLevelDescription(skillIndex, skillLevel):
				self.AppendSpace(5)
				if skillLevel == skillMaxLevel:
					self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL_MASTER % (skillLevel), self.NORMAL_COLOR)
				else:
					self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL % (skillLevel), self.NORMAL_COLOR)

				#####

				for i in range(skill.GetSkillAffectDescriptionCount(skillIndex)):
					affectText = skill.GetSkillAffectDescription(skillIndex, i, skillCurrentPercentage)
					self.AppendTextLine(affectText, bonuscolor.Text(affectText))

				## Cooltime
				coolTime = skill.GetSkillCoolTime(skillIndex, skillCurrentPercentage)
				if coolTime > 0:
					self.AppendTextLine(localeInfo.TOOLTIP_SKILL_COOL_TIME + str(coolTime), self.ENABLE_COLOR)

				## SP
				needGSP = skill.GetSkillNeedSP(skillIndex, skillCurrentPercentage)
				if needGSP > 0:
					self.AppendTextLine(localeInfo.TOOLTIP_NEED_GSP % (needGSP), self.ENABLE_COLOR)

		## Next Level
		if skillLevel < skillMaxLevel:
			if self.HasSkillLevelDescription(skillIndex, skillLevel+1):
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_NEXT_SKILL_LEVEL_1 % (skillLevel+1, skillMaxLevel), self.DISABLE_COLOR)

				#####

				for i in range(skill.GetSkillAffectDescriptionCount(skillIndex)):
					affectText = skill.GetSkillAffectDescription(skillIndex, i, skillNextPercentage)
					self.AppendTextLine(affectText, bonuscolor.Text(affectText))

				## Cooltime
				coolTime = skill.GetSkillCoolTime(skillIndex, skillNextPercentage)
				if coolTime > 0:
					self.AppendTextLine(localeInfo.TOOLTIP_SKILL_COOL_TIME + str(coolTime), self.DISABLE_COLOR)

				## SP
				needGSP = skill.GetSkillNeedSP(skillIndex, skillNextPercentage)
				if needGSP > 0:
					self.AppendTextLine(localeInfo.TOOLTIP_NEED_GSP % (needGSP), self.DISABLE_COLOR)

	def AppendSkillDataNew(self, slotIndex, skillIndex, skillGrade, skillLevel, skillCurrentPercentage, skillNextPercentage):
		personal = pvmpersonal.current()
		if personal and skillIndex in personal.rows:
			if personal.rows[skillIndex]['hud']:
				if personal.rows[skillIndex]['learned']:
					self.AppendSkillLevelDescriptionNew(skillIndex, skillCurrentPercentage, self.ENABLE_COLOR)
				pvmpersonaltext.append_bonus(self, skillIndex, app.GetTime(), passive_section=True)
				return
			pvmpersonaltext.append_bonus(self, skillIndex, app.GetTime(), passive_controls=False, show_scope=True)
			if personal.rows[skillIndex]['learned']:
				if skillIndex in pvmpersonal.SUPPORT_SKILLS:
					self.AppendSkillCastCost(skillIndex, skillCurrentPercentage, self.ENABLE_COLOR)
				else:
					self.AppendSkillLevelDescriptionNew(skillIndex, skillCurrentPercentage, self.ENABLE_COLOR)
			return
		realGrade = player.GetSkillGrade(slotIndex)
		label = sagebuff.GradeLabel(realGrade, skillLevel)
		if skillIndex in sagebuff.SAGE_SKILLS and label is not None:
			self.AppendSpace(5)
			self.AppendTextLine(localeInfo.TOOLTIP_SAGE_BUFF_LEVEL % label, self.NORMAL_COLOR)
			self.AppendSkillLevelDescriptionNew(skillIndex, skillCurrentPercentage, self.ENABLE_COLOR)
			nextLabel = sagebuff.NextGradeLabel(realGrade, skillLevel)
			if nextLabel is not None:
				self.AppendSpace(5)
				self.AppendTextLine(localeInfo.TOOLTIP_SAGE_BUFF_NEXT % nextLabel, self.NORMAL_COLOR)
				self.AppendSkillLevelDescriptionNew(skillIndex, skillNextPercentage, self.DISABLE_COLOR)
			return

		self.skillMaxLevelStartDict = { 0 : 17, 1 : 7, 2 : 10, }
		self.skillMaxLevelEndDict = { 0 : 20, 1 : 10, 2 : 10, }

		skillLevelUpPoint = 1
		realSkillGrade = player.GetSkillGrade(slotIndex)
		skillMaxLevelStart = self.skillMaxLevelStartDict.get(realSkillGrade, 15)
		skillMaxLevelEnd = self.skillMaxLevelEndDict.get(realSkillGrade, 20)

		## Current Level
		if skillLevel > 0:
			if self.HasSkillLevelDescription(skillIndex, skillLevel):
				self.AppendSpace(5)
				if skillGrade == skill.SKILL_GRADE_COUNT:
					pass
				elif skillLevel == skillMaxLevelEnd:
					self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL_MASTER % (skillLevel), self.NORMAL_COLOR)
				else:
					self.AppendTextLine(localeInfo.TOOLTIP_SKILL_LEVEL % (skillLevel), self.NORMAL_COLOR)
				self.AppendSkillLevelDescriptionNew(skillIndex, skillCurrentPercentage, self.ENABLE_COLOR)

		## Next Level
		if skillGrade != skill.SKILL_GRADE_COUNT:
			if skillLevel < skillMaxLevelEnd:
				if self.HasSkillLevelDescription(skillIndex, skillLevel+skillLevelUpPoint):
					self.AppendSpace(5)
					## HP보강, 관통회피 보조스킬의 경우
					if skillIndex == 141 or skillIndex == 142:
						self.AppendTextLine(localeInfo.TOOLTIP_NEXT_SKILL_LEVEL_3 % (skillLevel+1), self.NORMAL_COLOR)
					else:
						self.AppendTextLine(localeInfo.TOOLTIP_NEXT_SKILL_LEVEL_1 % (skillLevel+1, skillMaxLevelEnd), self.NORMAL_COLOR)
					self.AppendSkillLevelDescriptionNew(skillIndex, skillNextPercentage, self.DISABLE_COLOR)

	def AppendSkillLevelDescriptionNew(self, skillIndex, skillPercentage, color):
		affectDataCount = skill.GetNewAffectDataCount(skillIndex)
		if affectDataCount > 0:
			for i in range(affectDataCount):
				type, minValue, maxValue = skill.GetNewAffectData(skillIndex, i, skillPercentage)
				pvpSuffix = pvmpersonaltext.legacy_affect_suffix(skillIndex, i, type)
				if pvpSuffix is None:
					continue

				if type not in self.AFFECT_NAME_DICT:
					continue

				minValue = int(minValue)
				maxValue = int(maxValue)
				affectText = self.AFFECT_NAME_DICT[type]

				if "HP" == type:
					if minValue < 0 and maxValue < 0:
						minValue *= -1
						maxValue *= -1

					else:
						affectText = localeInfo.TOOLTIP_SKILL_AFFECT_HEAL

				affectText += str(minValue)
				if minValue != maxValue:
					affectText += " - " + str(maxValue)
				affectText += self.AFFECT_APPEND_TEXT_DICT.get(type, "")

				#import debugInfo
				#if debugInfo.IsDebugMode():
				#	affectText = "!!" + affectText

				self.AppendTextLine(affectText + pvpSuffix, bonuscolor.Text(affectText))

		else:
			for i in range(skill.GetSkillAffectDescriptionCount(skillIndex)):
				pvpSuffix = pvmpersonaltext.legacy_affect_suffix(skillIndex, i)
				if pvpSuffix is None:
					continue
				affectText = skill.GetSkillAffectDescription(skillIndex, i, skillPercentage) + pvpSuffix
				self.AppendTextLine(affectText, bonuscolor.Text(affectText))

		## Duration
		duration = skill.GetDuration(skillIndex, skillPercentage)
		if pvmpersonal.current() and skillIndex in pvmpersonal.CAST_SKILLS and skillIndex != 34:
			duration = 0  # Shared two-hour duration is displayed with the personal bonus.
		if duration > 0:
			try:
				if app.ENABLE_SKILL_DURATION and hasattr(player, "SKILL_INDEX_TIME_MASTER"):
					timeMasterSlot = player.GetSkillSlotIndex(player.SKILL_INDEX_TIME_MASTER)
					if timeMasterSlot:
						timeMasterLevel = player.GetSkillLevel(timeMasterSlot)
						timeMasterGrade = player.GetSkillGrade(timeMasterSlot)
						if 1 == timeMasterGrade:
							timeMasterLevel += 19
						elif 2 == timeMasterGrade:
							timeMasterLevel += 29
						elif 3 == timeMasterGrade:
							timeMasterLevel = 40
						if timeMasterLevel > 0:
							durationSkillSet = (
								4,   # SKILL_GEOMKYUNG
								63,  # SKILL_GWIGEOM
								94,  # SKILL_HOSIN
								95,  # SKILL_REFLECT
								96,  # SKILL_GICHEON
								110, # SKILL_KWAESOK
								111, # SKILL_JEUNGRYEOK
								19,  # SKILL_CHUNKEON
								3,   # SKILL_JEONGWI
								78,  # SKILL_MUYEONG
								79,  # SKILL_MANASHILED
								64,  # SKILL_TERROR
								65,  # SKILL_JUMAGAP
								34,  # SKILL_EUNHYUNG
								49,  # SKILL_GYEONGGONG
							)

							if skillIndex in durationSkillSet:
								maxBonusSeconds = 2700.0
								if timeMasterLevel >= 40:
									bonusSeconds = int(maxBonusSeconds)
								else:
									bonusSeconds = int(timeMasterLevel * (maxBonusSeconds / 40.0))

								if bonusSeconds > 0:
									bonusMinutes = bonusSeconds // 60
									if bonusMinutes > 0:
										self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration) + (" (+ %d min)" % bonusMinutes), color)
									else:
										self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration) + (" (+ %d sec)" % bonusSeconds), color)
								else:
									self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration), color)
							else:
								self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration), color)
						else:
							self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration), color)
					else:
						self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration), color)
				else:
					self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration), color)
			except:
				self.AppendTextLine(localeInfo.TOOLTIP_SKILL_DURATION % (duration), color)

		self.AppendSkillCastCost(skillIndex, skillPercentage, color)

	def AppendSkillCastCost(self, skillIndex, skillPercentage, color):
		if getattr(self, 'personalStyle', False):
			color = pvmpersonaltext.MUTED_COLOR
		## Cooltime
		coolTime = skill.GetSkillCoolTime(skillIndex, skillPercentage)
		if coolTime > 0:
			self.AppendTextLine(localeInfo.TOOLTIP_SKILL_COOL_TIME + str(coolTime), color)

		## SP
		needSP = skill.GetSkillNeedSP(skillIndex, skillPercentage)
		if needSP != 0:
			continuationSP = skill.GetSkillContinuationSP(skillIndex, skillPercentage)
			if pvmpersonal.current() and skillIndex in pvmpersonal.CAST_SKILLS and skillIndex != 34:
				continuationSP = 0

			if skill.IsUseHPSkill(skillIndex):
				self.AppendNeedHP(needSP, continuationSP, color)
			else:
				self.AppendNeedSP(needSP, continuationSP, color)

	def AppendSkillRequirement(self, skillIndex, skillLevel):
		skillMaxLevel = skill.GetSkillMaxLevel(skillIndex)

		if skillLevel >= skillMaxLevel:
			return

		isAppendHorizontalLine = False

		## Requirement
		if skill.IsSkillRequirement(skillIndex):
			if not isAppendHorizontalLine:
				isAppendHorizontalLine = True
				self.AppendHorizontalLine()

			requireSkillName, requireSkillLevel = skill.GetSkillRequirementData(skillIndex)

			color = self.CANNOT_LEVEL_UP_COLOR
			if skill.CheckRequirementSueccess(skillIndex):
				color = self.CAN_LEVEL_UP_COLOR
			self.AppendTextLine(localeInfo.TOOLTIP_REQUIREMENT_SKILL_LEVEL % (requireSkillName, requireSkillLevel), color)

		## Require Stat
		requireStatCount = skill.GetSkillRequireStatCount(skillIndex)
		if requireStatCount > 0:
			for i in range(requireStatCount):
				type, level = skill.GetSkillRequireStatData(skillIndex, i)
				if type in self.POINT_NAME_DICT:
					if not isAppendHorizontalLine:
						isAppendHorizontalLine = True
						self.AppendHorizontalLine()

					name = self.POINT_NAME_DICT[type]
					color = self.CANNOT_LEVEL_UP_COLOR
					if player.GetStatus(type) >= level:
						color = self.CAN_LEVEL_UP_COLOR
					self.AppendTextLine(localeInfo.TOOLTIP_REQUIREMENT_STAT_LEVEL % (name, level), color)

	def HasSkillLevelDescription(self, skillIndex, skillLevel):
		if skill.GetSkillAffectDescriptionCount(skillIndex) > 0:
			return True
		if skill.GetSkillCoolTime(skillIndex, skillLevel) > 0:
			return True
		if skill.GetSkillNeedSP(skillIndex, skillLevel) > 0:
			return True

		return False

	def AppendMasterAffectDescription(self, index, desc, color):
		self.AppendTextLine(desc, bonuscolor.Text(desc))

	def AppendNextAffectDescription(self, index, desc):
		self.AppendTextLine(desc, bonuscolor.Text(desc))

	def AppendNeedHP(self, needSP, continuationSP, color):
		self.AppendTextLine(localeInfo.TOOLTIP_NEED_HP % (needSP), color)

		if continuationSP > 0:
			self.AppendTextLine(localeInfo.TOOLTIP_NEED_HP_PER_SEC % (continuationSP), color)

	def AppendNeedSP(self, needSP, continuationSP, color):
		if -1 == needSP:
			self.AppendTextLine(localeInfo.TOOLTIP_NEED_ALL_SP, color)
		else:
			self.AppendTextLine(localeInfo.TOOLTIP_NEED_SP % (needSP), color)

		if continuationSP > 0:
			self.AppendTextLine(localeInfo.TOOLTIP_NEED_SP_PER_SEC % (continuationSP), color)

	if app.ENABLE_PARTY_PROFICY:
		def __AppendRoleProficiencySkillData(self, skill_grade, skill_level):
			if 1 == skill_grade:
				skill_level += 19
			elif 2 == skill_grade:
				skill_level += 29
			elif 3 == skill_grade:
				skill_level = 40

			if skill_level <= 0:
				return

			self.AppendSpace(5)
			self.AutoAppendTextLine(localeInfo.TOOLTIP_ROLE_PROFICIENCY_SKILL_LEVEL % skill_level, self.NORMAL_COLOR)
			self.AutoAppendTextLine(localeInfo.TOOLTIP_ROLE_PROFICIENCY_LEADER_EFFECT % skill.GetRoleProficiencyLeaderBonusByLevel(skill_level), bonuscolor.POSITIVE)

			self.AlignHorizonalCenter()

	if app.ENABLE_PARTY_INSIGHT:
		def __AppendInSightSkillData(self, skill_grade, skill_level):
			if 1 == skill_grade:
				skill_level += 19
			elif 2 == skill_grade:
				skill_level += 29
			elif 3 == skill_grade:
				skill_level = 40

			if skill_level <= 0:
				return

			skillIndex = player.SKILL_INDEX_INSIGHT
			slotIndex = player.GetSkillSlotIndex(skillIndex)
			skillPower = player.GetSkillCurrentEfficientPercentage(slotIndex)

			if localeInfo.IsBRAZIL() or localeInfo.IsNEWCIBN():
				k = skillPower
			else:
				k = float(skill.GetSkillPowerByLevel(skill_level)) / 100

			self.AppendSpace(5)
			self.AutoAppendTextLine(localeInfo.TOOLTIP_INSIGHT_SKILL_LEVEL % skill_level, self.NORMAL_COLOR)

			if skill_level >= 10:
				self.AutoAppendTextLine(localeInfo.PARTY_SKILL_ATTACKER % int(INSIGHT_ATTACKER_BASE_VALUE + INSIGHT_ATTACKER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

			if skill_level >= 20:
				self.AutoAppendTextLine(localeInfo.PARTY_SKILL_BERSERKER % int(INSIGHT_BERSERKER_BASE_VALUE + INSIGHT_BERSERKER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)
				self.AutoAppendTextLine(localeInfo.PARTY_SKILL_TANKER % int(INSIGHT_TANKER_BASE_VALUE + INSIGHT_TANKER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

			if skill_level >= 25:
				self.AutoAppendTextLine(localeInfo.PARTY_SKILL_BUFFER % int(INSIGHT_BUFFER_BASE_VALUE + INSIGHT_BUFFER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

			if skill_level >= 35:
				self.AutoAppendTextLine(localeInfo.PARTY_SKILL_SKILL_MASTER % int(INSIGHT_SKILL_MASTER_BASE_VALUE + INSIGHT_SKILL_MASTER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

			if skill_level >= 40:
				self.AutoAppendTextLine(localeInfo.PARTY_SKILL_DEFENDER % int(INSIGHT_DEFENDER_BASE_VALUE + INSIGHT_DEFENDER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

			self.AlignHorizonalCenter()

	def __AppendLeaderShipSkillData(self, skill_grade, skill_level):
		if 1 == skill_grade:
			skill_level += 19
		elif 2 == skill_grade:
			skill_level += 29
		elif 3 == skill_grade:
			skill_level = 40

		if skill_level <= 0:
			return

		skillIndex = player.SKILL_INDEX_TONGSOL
		slotIndex = player.GetSkillSlotIndex(skillIndex)
		skillPower = player.GetSkillCurrentEfficientPercentage(slotIndex)

		if localeInfo.IsBRAZIL() or localeInfo.IsNEWCIBN():
			k = skillPower
		else:
			k = float(skill.GetSkillPowerByLevel(skill_level)) / 100

		self.AppendSpace(5)
		self.AutoAppendTextLine(localeInfo.TOOLTIP_PARTY_SKILL_LEVEL % skill_level, self.NORMAL_COLOR)

		if skill_level >= 10:
			self.AutoAppendTextLine(localeInfo.PARTY_SKILL_ATTACKER % int(LEADERSHIP_ATTACKER_BASE_VALUE + LEADERSHIP_ATTACKER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

		if skill_level >= 20:
			self.AutoAppendTextLine(localeInfo.PARTY_SKILL_BERSERKER % int(LEADERSHIP_BERSERKER_BASE_VALUE + LEADERSHIP_BERSERKER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)
			self.AutoAppendTextLine(localeInfo.PARTY_SKILL_TANKER % int(LEADERSHIP_TANKER_BASE_VALUE + LEADERSHIP_TANKER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

		if skill_level >= 25:
			self.AutoAppendTextLine(localeInfo.PARTY_SKILL_BUFFER % int(LEADERSHIP_BUFFER_BASE_VALUE + LEADERSHIP_BUFFER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

		if skill_level >= 35:
			self.AutoAppendTextLine(localeInfo.PARTY_SKILL_SKILL_MASTER % int(LEADERSHIP_SKILL_MASTER_BASE_VALUE + LEADERSHIP_SKILL_MASTER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

		if skill_level >= 40:
			self.AutoAppendTextLine(localeInfo.PARTY_SKILL_DEFENDER % int(LEADERSHIP_DEFENDER_BASE_VALUE + LEADERSHIP_DEFENDER_ADJUSTMENT_VALUE * k), bonuscolor.POSITIVE)

		self.AlignHorizonalCenter()

	def __AppendSummonDescription(self, skillLevel, color):
		if skillLevel > 1:
			self.AppendTextLine(localeInfo.SKILL_SUMMON_DESCRIPTION % (skillLevel * 10), color)
		elif 1 == skillLevel:
			self.AppendTextLine(localeInfo.SKILL_SUMMON_DESCRIPTION % (15), color)
		elif 0 == skillLevel:
			self.AppendTextLine(localeInfo.SKILL_SUMMON_DESCRIPTION % (10), color)

if app.ENABLE_OFFLINE_SHOP:
	_instanceItemToolTip = None
	
	def GetItemToolTipInstance():
		global _instanceItemToolTip
	
		if not _instanceItemToolTip:
			SetItemToolTipInstance(ItemToolTip())
	
		return _instanceItemToolTip
	
	def SetItemToolTipInstance(instance):
		global _instanceItemToolTip
	
		if _instanceItemToolTip:
			del _instanceItemToolTip
	
		_instanceItemToolTip = instance

if app.ENABLE_GROWTH_PET_SYSTEM:
	class PetSkillToolTip(ToolTip):

		PET_SKILL_TOOL_TIP_WIDTH = 255

		PET_SKILL_APPLY_DATA_DICT =	{
				chr.PET_SKILL_AFFECT_JIJOONG_WARRIOR	: localeInfo.TOOLTIP_APPLY_RESIST_WARRIOR,		# %d%%
				chr.PET_SKILL_AFFECT_JIJOONG_SURA		: localeInfo.TOOLTIP_APPLY_RESIST_SURA,			# %d%%
				chr.PET_SKILL_AFFECT_JIJOONG_ASSASSIN	: localeInfo.TOOLTIP_APPLY_RESIST_ASSASSIN,		# %d%%
				chr.PET_SKILL_AFFECT_JIJOONG_SHAMAN		: localeInfo.TOOLTIP_APPLY_RESIST_SHAMAN,		# %d%%
				chr.PET_SKILL_AFFECT_JIJOONG_WOLFMAN	: localeInfo.TOOLTIP_APPLY_RESIST_WOLFMAN,		# %d%%
				chr.PET_SKILL_AFFECT_PACHEON			: localeInfo.TOOLTIP_MELEE_MAGIC_ATTBONUS_PER,	# %d%%
				chr.PET_SKILL_AFFECT_CHEONRYEONG		: localeInfo.TOOLTIP_RESIST_MAGIC_REDUCTION,	# %d%%
				chr.PET_SKILL_AFFECT_BANYA				: localeInfo.TOOLTIP_CAST_SPEED,				# %d%%
				chr.PET_SKILL_AFFECT_CHOEHOENBIMU		: localeInfo.TOOLTIP_APPLY_PENETRATE_PCT,		# %d%%
				chr.PET_SKILL_AFFECT_HEAL				: localeInfo.PET_SKILL_TOOLTIP_HEAL,			# %d%%, %d
				chr.PET_SKILL_AFFECT_STEALHP			: localeInfo.TOOLTIP_APPLY_STEAL_HP,			# %d%%
				chr.PET_SKILL_AFFECT_STEALMP			: localeInfo.TOOLTIP_APPLY_STEAL_SP,			# %d%%
				chr.PET_SKILL_AFFECT_BLOCK				: localeInfo.TOOLTIP_APPLY_BLOCK,				# %d%%
				chr.PET_SKILL_AFFECT_REFLECT_MELEE		: localeInfo.TOOLTIP_APPLY_REFLECT_MELEE,		# %d%%
				chr.PET_SKILL_AFFECT_GOLD_DROP			: localeInfo.TOOLTIP_MALL_GOLDBONUS,			# %.1f%%
				chr.PET_SKILL_AFFECT_BOW_DISTANCE		: localeInfo.TOOLTIP_BOW_DISTANCE,				# %dm
				chr.PET_SKILL_AFFECT_INVINCIBILITY		: localeInfo.PET_SKILL_TOOLTIP_INVINVIBILITY,	# %d%%, %.1f
				chr.PET_SKILL_AFFECT_REMOVAL			: localeInfo.PET_SKILL_TOOLTIP_REMOVAL,			# %d%%
				chr.PET_SKILL_AFFECT_POTION				: localeInfo.TOOLTIP_APPLY_POTION_BONUS,		# %d%%
				chr.PET_SKILL_AFFECT_MOB_BONUS			: localeInfo.TOOLTIP_APPLY_ATTBONUS_MONSTER,	# %d%%
				# Skills 21/22 follow player.growth_pet_skill_proto and pet_skill.txt:
				# 21 grants EXP_DOUBLE_BONUS, 22 KILL_HP_RECOVERY. The EXE enum names
				# them the other way round (PET_SKILL_HP_RECOVER=21, _AFFECT_EXP=22).
				21										: localeInfo.TOOLTIP_MALL_EXPBONUS,				# %d%%
				22										: localeInfo.TOOLTIP_APPLY_KILL_HP_RECOVER,		# %d%%
				chr.PET_SKILL_FEATHER					: localeInfo.PET_SKILL_TOOLTIP_FEATHER,			# %d%%, %.1f, %d - %d
				# The released EXE does not export the chr constants for the
				# meteor/boss books (server skills 24/25, items 55042/55044).
				getattr(chr, "PET_SKILL_AFFECT_STONE", 24)	: localeInfo.TOOLTIP_APPLY_ATTBONUS_METIN,	# %d%%
				getattr(chr, "PET_SKILL_AFFECT_BOSS", 25)	: localeInfo.TOOLTIP_APPLY_ATTBONUS_BOSS,	# %d%%
		}

		# Skill ids already reported as missing from PET_SKILL_APPLY_DATA_DICT.
		# ci/tests/test_pet_skill_tooltip.py keeps the dictionary complete; this
		# only keeps a future skill from spamming syserr on every hover.
		__reportedMissingSkills = set()

		def __init__(self):
			ToolTip.__init__(self, self.PET_SKILL_TOOL_TIP_WIDTH)
		def __del__(self):
			ToolTip.__del__(self)

		def SetPetSkill(self, pet_id, slot, index):

			if 0 == pet_id:
				return
			
			self.ClearToolTip()
				
			( pet_skill_vnum, pet_skill_level, formula1, formula2, formula3, next_formula1, next_formula2, next_formula3, bonus_value ) = player.GetPetSkillByIndex( pet_id, slot )
			
			if 0 == pet_skill_vnum:
				return
			
			( pet_skill_name, pet_skill_desc, pet_skill_use_type , pet_skill_cool_time ) = skill.GetPetSkillInfo(pet_skill_vnum)			
			
			self.SetTitle(pet_skill_name)

			self.AppendDescription(pet_skill_desc, 30)

			self.AppendSpace(5)
			if bonus_value:
				self.AppendTextLine( (localeInfo.PET_TOOLTIP_SKILL_CUR_LEVEL % pet_skill_level) + " "+ localeInfo.PET_TOOLTIP_SKILL_BONUS_VALUE, self.NORMAL_COLOR)
			else:
				self.AppendTextLine( localeInfo.PET_TOOLTIP_SKILL_CUR_LEVEL % pet_skill_level, self.NORMAL_COLOR)

			pet_skill_cool_time = self.__ServerCoolTime(pet_id, pet_skill_vnum)

			if skill.PET_SKILL_USE_TYPE_PASSIVE == pet_skill_use_type:
				self.__AppendPassiveSkill(pet_skill_vnum, pet_skill_name, int(formula2), self.NORMAL_COLOR)
				
			elif skill.PET_SKILL_USE_TYPE_AUTO == pet_skill_use_type:
				self.__AppendAutoSkill(pet_skill_vnum, pet_skill_name, formula1, formula2, formula3, self.NORMAL_COLOR)
				self.__AppendCoolTime(pet_skill_cool_time, self.NORMAL_COLOR)
				
			nextSkillLevel	= pet_skill_level + 1
			maxSkillLevel	= player.PET_GROWTH_SKILL_LEVEL_MAX
			
			if nextSkillLevel <= maxSkillLevel:
				self.AppendHorizontalLine()
				self.__AppendNextLevel( nextSkillLevel, maxSkillLevel )

				if skill.PET_SKILL_USE_TYPE_PASSIVE == pet_skill_use_type:
					self.__AppendPassiveSkill(pet_skill_vnum, pet_skill_name, int(next_formula2), self.NEGATIVE_COLOR)
					
				elif skill.PET_SKILL_USE_TYPE_AUTO == pet_skill_use_type:
					self.__AppendAutoSkill(pet_skill_vnum, pet_skill_name, next_formula1, next_formula2, next_formula3, self.NEGATIVE_COLOR)
					self.__AppendCoolTime(pet_skill_cool_time, self.NEGATIVE_COLOR)
				
			self.ResizeToolTip()
			self.ShowToolTip()

		def __ServerCoolTime(self, pet_id, pet_skill_vnum):
			# The cooldown differs per pet (player.growth_pet_skill_proto) and the
			# server does not send it; the single value in locale pet_skill.txt is
			# wrong for most pets. Only the active pet's VNUM is known here, and an
			# unknown pet/skill pair shows no cooldown rather than a guessed one.
			try:
				if pet_id != player.GetActivePetItemId():
					return None
				pet_vnum = player.GetActivePetItemVNum()
			except AttributeError:
				return None

			return growthpetskillcatalog.SkillCooldown(pet_vnum, pet_skill_vnum)

		def __ApplyText(self, pet_skill_vnum):
			try:
				return self.PET_SKILL_APPLY_DATA_DICT[pet_skill_vnum]
			except KeyError:
				if pet_skill_vnum not in self.__reportedMissingSkills:
					self.__reportedMissingSkills.add(pet_skill_vnum)
					dbg.TraceError("PetSkillToolTip: no bonus text for pet skill %d; showing the generic line" % pet_skill_vnum)
				return None

		def __PassiveSkillExceptionDecsriptionValueChange(self, pet_skill_vnum, value):
			return value

		def __AppendPassiveSkill(self, pet_skill_vnum, pet_skill_name, value, color ):
			
			if 0 == pet_skill_vnum:
				return
				
			text = self.__ApplyText(pet_skill_vnum)
			if text is None:
				self.AppendSpace(5)
				self.AppendTextLine("%s %+d" % (pet_skill_name, value), bonuscolor.Value(value))
				return
				
			value = self.__PassiveSkillExceptionDecsriptionValueChange(pet_skill_vnum, value)
				
			self.AppendSpace(5)
			self.AppendTextLine(text(value), bonuscolor.Value(value))

		def __AppendAutoSkill(self, pet_skill_vnum, pet_skill_name, value1, value2, value3, color ):
			
			if 0 == pet_skill_vnum:
				return
				
			text = self.__ApplyText(pet_skill_vnum)
			if text is None:
				# value1 is the activation chance in percent, value2 the effect.
				self.AppendSpace(5)
				self.AppendTextLine("%s %+d (%d%%)" % (pet_skill_name, value2, value1), bonuscolor.Value(value2))
				return
				
			self.AppendSpace(5)
						
			if chr.PET_SKILL_AFFECT_INVINCIBILITY == pet_skill_vnum:
				value2 = value2 / 10.0
				
			if chr.PET_SKILL_FEATHER == pet_skill_vnum:
				value3 = value3 / 10.0
				textLine = self.AppendTextLine(text(value1, value3, value2, value2 * 2), bonuscolor.Value(value2))
			else:
				textLine = self.AppendTextLine(text(value1, value2), bonuscolor.Value(value2))
			
			(x, y) = textLine.GetLocalPosition()
			textLine.SetPosition(x, y - (textLine.GetTextLineCount() - 1)*8)
			self.AppendSpace(textLine.GetTextLineCount() * 5)

		def __AppendCoolTime(self, pet_skill_cool_time, color):
			if pet_skill_cool_time is None:
				return
			self.AppendSpace(5)
			self.AutoAppendTextLine( localeInfo.PET_SKILL_TOOLTIP_COOLTIME % (pet_skill_cool_time), color)
			return
			
		def __AppendNextLevel(self, curLevel, maxLevel):
			self.AppendSpace(5)
			self.AutoAppendTextLine(localeInfo.PET_TOOLTIP_SKILL_NEXT_LEVEL % (curLevel, maxLevel) , self.NEGATIVE_COLOR)

if __name__ == "__main__":
	import app
	import wndMgr
	import systemSetting
	import mouseModule
	import grp
	import ui

	# wndMgr.SetOutlineFlag(True)

	app.SetMouseHandler(mouseModule.mouseController)
	app.SetHairColorEnable(True)
	wndMgr.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetScreenSize(systemSetting.GetWidth(), systemSetting.GetHeight())
	app.Create("METIN2 CLOSED BETA", systemSetting.GetWidth(), systemSetting.GetHeight(), 1)
	mouseModule.mouseController.Create()

	toolTip = ItemToolTip()
	toolTip.ClearToolTip()
	# toolTip.AppendTextLine("Test")
	desc = "Item descriptions:|increase of width of display to 35 digits per row AND installation of function that the displayed words are not broken up in two parts, but instead if one word is too long to be displayed in this row, this word will start in the next row."
	summ = ""

	toolTip.AddItemData_Offline(10, desc, summ, 0, 0) 
	toolTip.Show()

	app.Loop()
