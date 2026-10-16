import app
import ui
import player
import net
import wndMgr
import messenger
import guild
import chr
import nonplayer
import localeInfo
import constInfo
import osfInfo
import item
import uiToolTip

ENABLE_DPS_METER = getattr(app, "ENABLE_DPS_METER", False)

if ENABLE_DPS_METER:
	import uiDpsMeter

if app.ENABLE_MESSENGER_BLOCK:
	import uiCommon

if app.ENABLE_POISON_GAUGE_EFFECT:
	import chrmgr


def GetCenteredImageY(text_y, text_height, image_height):
	return int(text_y) + (int(text_height) - int(image_height)) // 2


def PackDropGridPages(heights, columns=12, rows=4):
	pages = []
	page = []
	occupied = set()
	for index, raw_height in enumerate(heights):
		height = max(1, min(rows, int(raw_height)))
		position = None
		for candidate in range(columns * rows):
			if candidate // columns + height > rows:
				continue
			if all(candidate + offset * columns not in occupied for offset in range(height)):
				position = candidate
				break
		if position is None:
			pages.append(page)
			page = []
			occupied = set()
			position = 0
		page.append((position, index))
		for offset in range(height):
			occupied.add(position + offset * columns)
	pages.append(page)
	return pages


def GetDropPageFootprint(page, heights, columns=12, rows=4):
	occupied = set()
	for position, index in page:
		height = max(1, min(rows, int(heights[index])))
		for offset in range(height):
			occupied.add(position + offset * columns)
	if not occupied:
		return occupied, 0, 0
	return occupied, max(position % columns for position in occupied) + 1, max(position // columns for position in occupied) + 1


class TargetAnimatedHpGauge(ui.Window):
	HP_ANIMATION_DELAY = 6
	GAUGE_CONTENT_WIDTH = 95
	GAUGE_CONTENT_X = 4
	GAUGE_FRAME_WIDTH = 103
	GAUGE_WIDTH = GAUGE_FRAME_WIDTH
	GAUGE_HEIGHT = 11
	HUD_FRAME = "local_target_board/hp_gauge_frame.sub"
	NORMAL_FRAMES = (
		"D:/Ymir Work/UI/Pattern/HPGauge/01.tga",
		"D:/Ymir Work/UI/Pattern/HPGauge/02.tga",
		"D:/Ymir Work/UI/Pattern/HPGauge/03.tga",
		"D:/Ymir Work/UI/Pattern/HPGauge/04.tga",
		"D:/Ymir Work/UI/Pattern/HPGauge/05.tga",
		"D:/Ymir Work/UI/Pattern/HPGauge/06.tga",
		"D:/Ymir Work/UI/Pattern/HPGauge/07.tga",
	)
	POISON_FRAMES = (
		"D:/Ymir Work/UI/Pattern/HPPoisonGauge/01.tga",
		"D:/Ymir Work/UI/Pattern/HPPoisonGauge/02.tga",
		"D:/Ymir Work/UI/Pattern/HPPoisonGauge/03.tga",
		"D:/Ymir Work/UI/Pattern/HPPoisonGauge/04.tga",
		"D:/Ymir Work/UI/Pattern/HPPoisonGauge/05.tga",
		"D:/Ymir Work/UI/Pattern/HPPoisonGauge/06.tga",
		"D:/Ymir Work/UI/Pattern/HPPoisonGauge/07.tga",
	)

	def __init__(self):
		ui.Window.__init__(self)
		self.SetSize(self.GAUGE_WIDTH, self.GAUGE_HEIGHT)
		self.preValue = 0.0
		self.currentValue = 0.0
		self.targetID = 0
		self.isPoisoned = False

		self.background = self.__CreateBackground()
		self.normalGauge = self.__CreateAnimation(self.NORMAL_FRAMES)
		self.poisonGauge = self.__CreateAnimation(self.POISON_FRAMES)
		self.poisonGauge.Hide()

	def __CreateBackground(self):
		background = ui.ImageBox()
		background.SetParent(self)
		background.SetPosition(0, 0)
		background.AddFlag("not_pick")
		background.LoadImage(self.HUD_FRAME)
		background.Show()
		return background

	def __CreateAnimation(self, frames):
		animation = ui.AniImageBox()
		animation.SetParent(self)
		animation.SetPosition(self.GAUGE_CONTENT_X, 0)
		animation.SetDelay(self.HP_ANIMATION_DELAY)
		for frame in frames:
			animation.AppendImage(frame)
		animation.Show()
		return animation

	def SetGaugeColor(self, color):
		self.isPoisoned = color == "lime"
		if self.isPoisoned:
			self.normalGauge.Hide()
			self.poisonGauge.Show()
		else:
			self.poisonGauge.Hide()
			self.normalGauge.Show()

	def SetPercentage(self, curValue, maxValue):
		value = 0.0
		if maxValue > 0:
			value = max(0.0, min(100.0, float(curValue) * 100.0 / float(maxValue)))
		self.preValue = self.currentValue
		self.currentValue = value
		self.normalGauge.SetPercentage(value, 100)
		self.poisonGauge.SetPercentage(value, 100)

	def SetPercentageBack(self, curValue, maxValue):
		return

	def SetDMGPercentage(self, targetID, minValue, curValue, maxValue, color=0x55ff0000):
		self.targetID = targetID

	def GetPrevalue(self):
		return self.preValue


if app.ENABLE_SEND_TARGET_INFO:
	import item
	import uiToolTip

	def IS_SET(flag, bit):
		return (flag & bit) != 0

	class TargetDetailsThinBoard(ui.ThinBoard):
		BOARD_WIDTH = 280
		BOARD_HEIGHT = 0

		RACE_FLAG_NAME_DICT = {
			nonplayer.RACE_FLAG_ANIMAL : localeInfo.TARGET_INFO_RACE_ANIMAL,
			nonplayer.RACE_FLAG_UNDEAD : localeInfo.TARGET_INFO_RACE_UNDEAD,
			nonplayer.RACE_FLAG_DEVIL : localeInfo.TARGET_INFO_RACE_DEVIL,
			nonplayer.RACE_FLAG_HUMAN : localeInfo.TARGET_INFO_RACE_HUMAN,
			nonplayer.RACE_FLAG_ORC : localeInfo.TARGET_INFO_RACE_ORC,
			nonplayer.RACE_FLAG_MILGYO : localeInfo.TARGET_INFO_RACE_MILGYO,
			nonplayer.RACE_FLAG_INSECT : localeInfo.TARGET_INFO_RACE_INSECT,
			nonplayer.RACE_FLAG_DESERT : localeInfo.TARGET_INFO_RACE_DESERT,
			nonplayer.RACE_FLAG_TREE : localeInfo.TARGET_INFO_RACE_TREE,
			nonplayer.RACE_FLAG_ZODIAC : localeInfo.TARGET_INFO_RACE_ATT_CZ,
		}

		if app.ENABLE_ELEMENT_ADD:
			ELEMENT_ENCHANT_NAME_DICT = {
				0 : [ "d:/ymir work/ui/game/12zi/element/elect.sub", localeInfo.TARGET_INFO_ELEMENT_ELECT ],
				1 : [ "d:/ymir work/ui/game/12zi/element/fire.sub", localeInfo.TARGET_INFO_ELEMENT_FIRE ],
				2 : [ "d:/ymir work/ui/game/12zi/element/ice.sub", localeInfo.TARGET_INFO_ELEMENT_ICE ],
				3 : [ "d:/ymir work/ui/game/12zi/element/wind.sub", localeInfo.TARGET_INFO_ELEMENT_WIND ],
				4 : [ "d:/ymir work/ui/game/12zi/element/earth.sub", localeInfo.TARGET_INFO_ELEMENT_EARTH ],
				5 : [ "d:/ymir work/ui/game/12zi/element/dark.sub", localeInfo.TARGET_INFO_ELEMENT_DARK ],
			}

		PERCENT_BY_DELTA_LEVEL = [
			1, 5, 10, 20, 30, 50, 70, 80, 85, 90,
			92, 94, 96, 98, 100, 100, 105, 110, 115, 120,
			125, 130, 135, 140, 145, 150, 155, 160, 165, 170,
			180
		]

		QUESTION_BUTTON_ELEMENT = 0
		QUESTION_BUTTON_ATTR = 1
		QUESTION_BUTTON_REWARD = 2

		ELEMENT_TOOLTIP_LIST = [
			localeInfo.TARGET_INFO_ELEMENT_TOOLTIP_LIST1,
			localeInfo.TARGET_INFO_ELEMENT_TOOLTIP_LIST2
		]

		ATTR_TOOLTIP_LIST = [
			localeInfo.TARGET_INFO_ATTR_TOOLTIP_LIST1,
			localeInfo.TARGET_INFO_ATTR_TOOLTIP_LIST2
		]

		REWARD_TOOLTIP_LIST = [
			localeInfo.TARGET_INFO_REWARD_TOOLTIP_LIST1,
			localeInfo.TARGET_INFO_REWARD_TOOLTIP_LIST2,
			localeInfo.TARGET_INFO_REWARD_TOOLTIP_LIST3
		]

		THINBOARD_BAR_GAP = 3
		THINBOARD_BAR_COLOR = 0x66111111
		THINBOARD_BAR_TITLE_COLOR = 0xfffff571
		THINBOARD_BAR_TEXT_COLOR = 0xffFFFFE0

		def __init__(self, parent):
			ui.ThinBoard.__init__(self)

			self.SetSize(self.BOARD_WIDTH, 0)
			self.HideCorners(self.LT)
			self.HideCorners(self.RT)
			self.HideLine(self.T)

			self.parent = parent
			self.race_vnum = 0
			self.attr_page = 0
			self.attr_page_dict = {}
			self.attr_show_null_value = False
			self.attr_show_color = True

			self.children_list = []
			self.height = 0
			self.tooltip = uiToolTip.ToolTip()
			self.help_tooltip_height_dict = {}
			self.item_drop_window = MobItemDropWindow()

			self.has_attr = False
			if app.ENABLE_ELEMENT_ADD:
				self.has_element = False
			self.has_reward = True

			self.__LoadWindow()

		def __del__(self):
			ui.ThinBoard.__del__(self)
			self.attr_page_dict = {}
			self.children_list = []
			self.help_tooltip_height_dict = {}
			del self.tooltip
			del self.item_drop_window

		def __LoadWindow(self):
			self.SetWindowName("TargetDetailsThinBoard")
			self.AddFlag("float")
			#self.SetPosition(0, 34)
			self.SetWindowHorizontalAlignCenter()
			self.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)

			self.__AppendSeperator()

		def UpdateAutoY(self):
			if not self.parent:
				return
			margin = 1
			self.SetPosition(0, self.parent.GetHeight() + margin)

		def __AppendHeight(self, height):
			self.height += height
			self.SetSize(self.BOARD_WIDTH, self.height)

		def __AppendSpace(self, height = 0):
			self.__AppendHeight(height if height else 5)

		def __AppendChild(self, child, height):
			self.children_list.append(child)
			self.__AppendHeight(height)

		def __AppendSeperator(self, space = 25):
			image = ui.ImageBox()
			image.SetParent(self)
			image.AddFlag("not_pick")
			image.LoadImage("d:/ymir work/ui/pattern/seperator.tga")
			image.SetPosition(0, self.height + image.GetTop() - 10)
			image.SetWindowHorizontalAlignCenter()
			image.Show()
			self.__AppendChild(image, space)

		def __AutoAppendTitleLine(self, text):
			text_line = self.__AutoAppendTextLine(text)
			text_line.SetPackedFontColor(0xfffff2cc)

		def __AutoAppendTextLine(self, text, font_color = 0, outline_color = 0):
			text_line = ui.TextLine()
			text_line.SetParent(self)
			text_line.SetPosition(0, self.height)
			text_line.SetWindowHorizontalAlignCenter()
			text_line.SetHorizontalAlignCenter()
			text_line.SetText(text)
			if font_color != 0:
				text_line.SetPackedFontColor(font_color)
			text_line.SetOutline(True)
			if outline_color != 0:
				text_line.SetOutline(outline_color)
			text_line.Show()
			self.__AppendChild(text_line, 17)
			return text_line

		def __AutoAppendTextValueLine(self, text, value, font_color = 0, outline_color = 0):
			if value != 0 or self.attr_show_null_value:
				if self.attr_show_color:
					if value > 0:
						self.__AutoAppendTextLine(text % value, 0xFFFF6F61, outline_color)
					elif value < 0:
						self.__AutoAppendTextLine(text % value, 0xFF98FB98, outline_color)
					else:
						self.__AutoAppendTextLine(text % value, font_color, outline_color)
				else:
					self.__AutoAppendTextLine(text % value, font_color, outline_color)

			return value

		def __AppendHorizontalLine(self, line_size = 0):
			draw_line = True
			if draw_line != True:
				line = ui.ImageBox()
				line.SetParent(self)
				line.LoadImage("d:/ymir work/ui/quest_re/quest_list_line_01.tga")
				line.SetDiffuseColor(3.0, 0.3, 0.3, 1.0)
				line.SetPosition(0, self.height)
				line.SetWindowHorizontalAlignCenter()
				line.Show()
				self.__AppendChild(line, 0)
			else:
				if line_size == 0:
					line_size = self.GetWidth() - 50

				for i in range(2):
					line = ui.Line()
					line.SetParent(self)
					line.SetSize(line_size, 0)
					line.SetColor(0x66c7c7c7 if 0 == i else 0xff000000)
					line.SetPosition((self.GetWidth() // 2) - (line_size // 2), self.height + 2 + i)
					line.Show()

					self.__AppendChild(line, 0)

			self.__AppendHeight(7)

		def __AppendCheckBox(self, text, check_func, uncheck_func, check):
			checkbox = ui.CheckBoxTarget()
			checkbox.SetParent(self)
			checkbox.SetCheckBox(check)
			checkbox.SetText(text, 0xfffffff1)
			checkbox.SetPosition(0, self.height + 5)
			checkbox.SetWindowHorizontalAlignCenter()
			if check_func and uncheck_func:
				checkbox.SetEvent(ui.__mem_func__(check_func), "check")
				checkbox.SetEvent(ui.__mem_func__(uncheck_func), "uncheck")
			checkbox.Show()
			self.__AppendChild(checkbox, 13)
			self.__AppendHeight(5)

		def __AppendArrows(self, prev_func, next_func):
			prev_button = ui.Button()
			prev_button.SetParent(self)
			prev_button.SetPosition(25, self.height + 5)
			prev_button.SetUpVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub")
			prev_button.SetOverVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_02.sub")
			prev_button.SetDownVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub")
			if prev_func:
				prev_button.SetEvent(ui.__mem_func__(prev_func))
			prev_button.Show()

			next_button = ui.Button()
			next_button.SetParent(self)
			next_button.SetPosition(self.GetWidth() - 45, self.height + 5)
			next_button.SetUpVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub")
			next_button.SetOverVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_02.sub")
			next_button.SetDownVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub")
			if next_func:
				next_button.SetEvent(ui.__mem_func__(next_func))
			next_button.Show()

			self.__AppendChild(prev_button, 0)
			self.__AppendChild(next_button, 0)
			self.__AppendHeight(5)

		def __OnImageMouseEvent(self, event_type, arg = None):
			self.tooltip.ClearToolTip()

			if "mouse_over_in" == event_type and arg:
				self.tooltip.SetThinBoardSize(app.GetTextLength(str(arg)))

				self.tooltip.color = ui.Bar()
				self.tooltip.color.SetParent(self.tooltip)
				self.tooltip.color.SetColor(self.THINBOARD_BAR_COLOR)
				self.tooltip.color.SetPosition(0, 0)
				self.tooltip.color.SetWindowHorizontalAlignCenter()
				self.tooltip.color.SetWindowVerticalAlignCenter()
				self.tooltip.color.Show()

				self.tooltip.AutoAppendTextLine(arg, self.THINBOARD_BAR_TEXT_COLOR)
				self.tooltip.AlignHorizonalCenter()
				self.tooltip.ShowToolTip()

				self.tooltip.color.SetSize(self.tooltip.GetWidth() - self.THINBOARD_BAR_GAP, self.tooltip.GetHeight() - self.THINBOARD_BAR_GAP)

			elif "mouse_over_out" == event_type:
				self.tooltip.Hide()

		def __AutoAppendInlineImage(self, element_dict):
			image_scale = 0.5
			image_gap = 5

			inline_window = ui.Window()
			inline_window.SetParent(self)

			for i, (key, dict) in enumerate(element_dict.items()):
				image = ui.ImageBox()
				image.SetParent(inline_window)
				image.LoadImage(dict["image_path"])

				inline_window.SetSize((image.GetWidth() * image_scale + image_gap) * len(element_dict), (image.GetHeight() * image_scale + image_gap))

				image.SetScale(image_scale, image_scale)
				image.SetPosition((image_gap // 2) + (image.GetWidth() * image_scale + image_gap) * i, (image_gap // 2))
				image.SetEvent(ui.__mem_func__(self.__OnImageMouseEvent), "mouse_over_in", dict["locale_text"] % dict["value"])
				image.SetEvent(ui.__mem_func__(self.__OnImageMouseEvent), "mouse_over_out")
				image.Show()

				self.__AppendChild(image, 0)

			inline_window.SetPosition(0, self.height)
			inline_window.SetWindowHorizontalAlignCenter()
			inline_window.Show()

			self.__AppendChild(inline_window, 0)
			self.__AppendHeight(28)

		def __CalculateValueLvDelta(self, player_level, victim_level, exp):
			percent_lv_delta = self.PERCENT_BY_DELTA_LEVEL[min(max(0, (victim_level + 15) - player_level), len(self.PERCENT_BY_DELTA_LEVEL) - 1)]
			return (exp * percent_lv_delta) // 100

		def __AppendDefaultDetails(self):
			## Race
			race_name_list = [value for key, value in self.RACE_FLAG_NAME_DICT.items() if IS_SET(nonplayer.GetRaceFlag(), key)]
			race_name = ", ".join(race_name_list)
			if race_name_list:
				self.__AutoAppendTextLine(localeInfo.TARGET_INFO_RACE % race_name)
			else:
				if nonplayer.IsStone():
					self.__AutoAppendTextLine(localeInfo.TARGET_INFO_RACE % localeInfo.TARGET_INFO_RACE_METIN)
				else:
					self.__AutoAppendTextLine(localeInfo.TARGET_INFO_RACE % localeInfo.TARGET_INFO_RACE_UNKNOWN)

			max_hp = nonplayer.GetMaxHP()
			regen_pct = nonplayer.GetRegenPercent()
			regen_cycle = nonplayer.GetRegenCycle()
			regen_hp_value = max(1, max_hp * regen_pct // 100)

			## Health
			self.__AutoAppendTextLine(localeInfo.TARGET_INFO_MAX_HP % localeInfo.NumberToDecimal(max_hp))

			## Health Regeneration
			self.__AutoAppendTextLine(localeInfo.TARGET_INFO_HP_REGEN % (regen_pct, regen_hp_value, regen_cycle))
			self.__AppendSpace()

		if app.ENABLE_ELEMENT_ADD:
			def __AppendElementDetails(self):
				element_dict = {}
				for key, list in self.ELEMENT_ENCHANT_NAME_DICT.items():
					value = nonplayer.GetElement(key)
					if value != 0:
						element_dict.update({ key : { "value" : value, "image_path" : list[0], "locale_text" : list[1] }})

				if not element_dict:
					self.has_element = False
					return

				self.__AppendHorizontalLine()
				self.__AppendQuestion(self.QUESTION_BUTTON_ELEMENT)
				self.__AutoAppendTitleLine(localeInfo.TARGET_INFO_ELEMENT_TITLE)

				self.__AutoAppendInlineImage(element_dict)

				self.has_element = True

		def __OnCheckShowAttrNullValue(self):
			self.attr_show_null_value = True
			self.Refresh()

		def __OnUnCheckShowAttrNullValue(self):
			self.attr_show_null_value = False
			self.Refresh()

		def __OnCheckShowAttrColor(self):
			self.attr_show_color = True
			self.Refresh()

		def __OnUnCheckShowAttrColor(self):
			self.attr_show_color = False
			self.Refresh()

		def __AppendAttrDetails(self):
			if nonplayer.IsStone():
				return

			attr_dict = {
				0 : [ ## Weapon Resistances
					(localeInfo.TARGET_INFO_RESIST_SWORD, nonplayer.GetResist(nonplayer.MOB_RESIST_SWORD)),
					(localeInfo.TARGET_INFO_RESIST_TWOHAND, nonplayer.GetResist(nonplayer.MOB_RESIST_TWOHAND)),
					(localeInfo.TARGET_INFO_RESIST_DAGGER, nonplayer.GetResist(nonplayer.MOB_RESIST_DAGGER)),
					(localeInfo.TARGET_INFO_RESIST_BOW, nonplayer.GetResist(nonplayer.MOB_RESIST_BOW)),
					(localeInfo.TARGET_INFO_RESIST_BELL, nonplayer.GetResist(nonplayer.MOB_RESIST_BELL)),
					(localeInfo.TARGET_INFO_RESIST_FAN, nonplayer.GetResist(nonplayer.MOB_RESIST_FAN)),
				],
				1 : [ ## Elemental Resistances
					(localeInfo.TARGET_INFO_RESIST_FIRE, nonplayer.GetResist(nonplayer.MOB_RESIST_FIRE)),
				],
				2 : [ ## Resistances (Others)
					(localeInfo.TARGET_INFO_RESIST_POISON, nonplayer.GetResist(nonplayer.MOB_RESIST_POISON)),
					(localeInfo.TARGET_INFO_RESIST_BLEEDING, nonplayer.GetResist(nonplayer.MOB_RESIST_BLEEDING)),
				],
				3 : [ ## Enchantments
					(localeInfo.TARGET_INFO_ENCHANT_SLOW, nonplayer.GetEnchant(nonplayer.MOB_ENCHANT_SLOW)),
					(localeInfo.TARGET_INFO_ENCHANT_STUN, nonplayer.GetEnchant(nonplayer.MOB_ENCHANT_STUN)),
					(localeInfo.TARGET_INFO_ENCHANT_POISON, nonplayer.GetEnchant(nonplayer.MOB_ENCHANT_POISON)),
					(localeInfo.TARGET_INFO_ENCHANT_CRITICAL, nonplayer.GetEnchant(nonplayer.MOB_ENCHANT_CRITICAL)),
					(localeInfo.TARGET_INFO_ENCHANT_PENETRATE, nonplayer.GetEnchant(nonplayer.MOB_ENCHANT_PENETRATE)),
				],
			}
			if not app.DISABLE_WOLFMAN_CREATION:
				attr_dict[0].append((localeInfo.TARGET_INFO_RESIST_CLAW, nonplayer.GetResist(nonplayer.MOB_RESIST_CLAW)))
			attr_dict[1].append((localeInfo.TARGET_INFO_RESIST_WIND, nonplayer.GetResist(nonplayer.MOB_RESIST_WIND)))
			attr_dict[1].append((localeInfo.TARGET_INFO_RESIST_ELECT, nonplayer.GetResist(nonplayer.MOB_RESIST_ELECT)))
			attr_dict[1].append((localeInfo.TARGET_INFO_RESIST_MAGIC, nonplayer.GetResist(nonplayer.MOB_RESIST_MAGIC)))
			self.attr_page_dict = {}
			i = 0
			for key, list in attr_dict.items():
				for tuple in list:
					if tuple[1] != 0:
						self.attr_page_dict[i] = key
						i += 1
						break

			if i == 0:
				self.has_attr = False
				return

			self.__AppendHorizontalLine()
			self.__AppendQuestion(self.QUESTION_BUTTON_ATTR)

			self.__AppendCheckBox(localeInfo.TARGET_INFO_CHECKBOX_SHOW_ATTR_NULL_VALUE, self.__OnCheckShowAttrNullValue, self.__OnUnCheckShowAttrNullValue, self.attr_show_null_value)
			self.__AppendCheckBox(localeInfo.TARGET_INFO_CHECKBOX_SHOW_ATTR_COLOR, self.__OnCheckShowAttrColor, self.__OnUnCheckShowAttrColor, self.attr_show_color)

			self.__AppendSeperator(20)
			self.__AppendArrows(self.__OnClickPrevResistDetails, self.__OnClickNextResistDetails)

			if self.attr_page in self.attr_page_dict:
				page = self.attr_page_dict[self.attr_page]
				if page in attr_dict:
					if page == 0:
						self.__AutoAppendTitleLine(localeInfo.TARGET_INFO_RESIST_WEAPON_TITLE)
					elif page == 1:
						self.__AutoAppendTitleLine(localeInfo.TARGET_INFO_RESIST_ELEMENT_TITLE)
					elif page == 2:
						self.__AutoAppendTitleLine(localeInfo.TARGET_INFO_RESIST_TITLE)
					elif page == 3:
						self.__AutoAppendTitleLine(localeInfo.TARGET_INFO_RESIST_ELEMENT_TITLE)

					for tuple in attr_dict[page]:
						self.__AutoAppendTextValueLine(tuple[0], tuple[1])

			self.has_attr = True

		def __CreateGameTypeToolTip(self, title, desc_list):
			tooltip = uiToolTip.ToolTip()
			tooltip.ClearToolTip()
			tooltip.AppendSpace(5)

			tooltip.color = ui.Bar()
			tooltip.color.SetParent(tooltip)
			tooltip.color.SetColor(self.THINBOARD_BAR_COLOR)
			tooltip.color.SetPosition(0, 0)
			tooltip.color.SetWindowHorizontalAlignCenter()
			tooltip.color.SetWindowVerticalAlignCenter()
			tooltip.color.Show()

			tooltip.AutoAppendTextLine(title, self.THINBOARD_BAR_TITLE_COLOR)
			for desc in desc_list:
				tooltip.AutoAppendTextLine(desc, self.THINBOARD_BAR_TEXT_COLOR)
			tooltip.AlignHorizonalCenter()

			tooltip.color.SetSize(tooltip.GetWidth() - self.THINBOARD_BAR_GAP, tooltip.GetHeight() - self.THINBOARD_BAR_GAP)

			return tooltip

		def __AppendQuestion(self, key):
			self.help_tooltip_height_dict[key] = self.height

		def __AutoAppendQuestion(self, key, title, desc_list):
			if key not in self.help_tooltip_height_dict:
				return

			button = ui.Button()
			button.SetParent(self)
			button.SetUpVisual("d:/ymir work/ui/pattern/q_mark_01.tga")
			button.SetOverVisual("d:/ymir work/ui/pattern/q_mark_02.tga")
			button.SetDownVisual("d:/ymir work/ui/pattern/q_mark_01.tga")
			if localeInfo.IsARABIC():
				button.SetPosition(self.GetWidth() - button.GetWidth() - 24 , self.help_tooltip_height_dict[key] - 13)
			else:
				button.SetPosition(24 , self.help_tooltip_height_dict[key] - 13)

			tooltip = self.__CreateGameTypeToolTip(title, desc_list)
			button.SetToolTipWindow(tooltip)
			button.Show()

			self.__AppendChild(button, 0)
			self.__AppendChild(tooltip, 0)

		def __AppendRewardDetails(self):
			self.__AppendHorizontalLine()
			self.__AppendQuestion(self.QUESTION_BUTTON_REWARD)

			my_level = player.GetStatus(player.LEVEL)
			level = nonplayer.GetLevel()

			## Experience
			self.__AutoAppendTextLine(localeInfo.TARGET_INFO_EXP % localeInfo.NumberToDecimal(self.__CalculateValueLvDelta(my_level, level, nonplayer.GetExp())))
			## Gold
			self.__AutoAppendTextLine(localeInfo.TARGET_INFO_GOLD_MIN_MAX % (localeInfo.NumberToMoneyString(nonplayer.GetMinGold()), localeInfo.NumberToMoneyString(nonplayer.GetMaxGold())))

			self.__AppendSpace()

			## Metin Stone Drop
			if nonplayer.GetDropMetinStone():
				self.__AutoAppendTextLine(localeInfo.TARGET_INFO_METIN_STONE_DROP)
				self.__AppendSpace()

			## Mob Item Drop Button
			button = ui.Button()
			button.SetParent(self)
			button.SetDisableVisual("d:/ymir work/ui/game/treasure_hunt/event/reward_list/reward_off_btn_default.sub")
			button.SetUpVisual("d:/ymir work/ui/game/treasure_hunt/event/reward_list/reward_on_btn_default.sub")
			button.SetOverVisual("d:/ymir work/ui/game/treasure_hunt/event/reward_list/reward_on_btn_over.sub")
			button.SetDownVisual("d:/ymir work/ui/game/treasure_hunt/event/reward_list/reward_on_btn_down.sub")
			button.SetPosition(0, self.height)
			button.SetWindowHorizontalAlignCenter()
			button.SetEvent(ui.__mem_func__(self.__OnClickMobItemDropButton), -1)
			if nonplayer.HasMonsterItemDrop(self.race_vnum):
				button.SetOverEvent(ui.__mem_func__(self.__OnImageMouseEvent), "mouse_over_in", localeInfo.TARGET_INFO_ITEM_DROP)
				button.Enable()
			else:
				button.Disable()
				button.SetOverEvent(ui.__mem_func__(self.__OnImageMouseEvent), "mouse_over_in", localeInfo.TARGET_INFO_NO_ITEM_DROP)
			button.SetOverOutEvent(ui.__mem_func__(self.__OnImageMouseEvent), "mouse_over_out")
			button.Show()

			self.__AppendChild(button, button.GetHeight() + 5)

		def __OnClickMobItemDropButton(self):
			if not self.item_drop_window:
				return
			if self.item_drop_window.IsShow():
				if getattr(self.item_drop_window, "race_vnum", None) == self.race_vnum:
					self.item_drop_window.Close()
				else:
					self.item_drop_window.Open(self.race_vnum)
			else:
				self.item_drop_window.Open(self.race_vnum)

		def __OnClickPrevResistDetails(self):
			self.attr_page -= 1
			if self.attr_page < 0:
				self.attr_page = len(self.attr_page_dict) - 1

			self.Refresh()

		def __OnClickNextResistDetails(self):
			self.attr_page += 1
			if self.attr_page > len(self.attr_page_dict) - 1:
				self.attr_page = 0

			self.Refresh()

		def __ShowDetails(self):
			if self.race_vnum == 0:
				return False

			nonplayer.SelectMob(self.race_vnum)

			self.__AppendDefaultDetails()
			if not nonplayer.IsStone():
				if app.ENABLE_ELEMENT_ADD:
					self.__AppendElementDetails()
				self.__AppendAttrDetails()
			self.__AppendRewardDetails()

			return True

		def __ClearChildren(self):
			self.children_list = []
			self.height = 0

		def Refresh(self):
			self.__ClearChildren()

			self.has_attr = False
			if app.ENABLE_ELEMENT_ADD:
				self.has_element = False
			self.has_reward = True

			self.__AppendSeperator()
			if self.__ShowDetails():
				self.__AppendSeperator(16)

			if self.has_reward:
				self.__AutoAppendQuestion(self.QUESTION_BUTTON_REWARD, localeInfo.TARGET_INFO_REWARD_TOOLTIP_TITLE, self.REWARD_TOOLTIP_LIST)

			if self.has_attr:
				self.__AutoAppendQuestion(self.QUESTION_BUTTON_ATTR, localeInfo.TARGET_INFO_ATTR_TOOLTIP_TITLE, self.ATTR_TOOLTIP_LIST)

			if app.ENABLE_ELEMENT_ADD:
				if self.has_element:
					self.__AutoAppendQuestion(self.QUESTION_BUTTON_ELEMENT, localeInfo.TARGET_INFO_ELEMENT_TOOLTIP_TITLE, self.ELEMENT_TOOLTIP_LIST)

		def Open(self, race_vnum):
			self.race_vnum = race_vnum

			self.SetTop()
			self.Show()

			self.Refresh()

		def Close(self):
			if self.tooltip:
				self.tooltip.Hide()

			self.Hide()

		def OnPressEscapeKey(self):
			self.Close()
			return True

	class MobItemDropWindow(ui.BoardWithTitleBar):
		BOARD_WIDTH = 200
		BOARD_HEIGHT = 355
		ALTHEA_METEOR_VNUMS = (8890, 8891, 8892, 8893)
		STONE_FRAME_DURATION = 0.7

		def __init__(self):
			ui.BoardWithTitleBar.__init__(self)
			self.isLoaded = False

			self.race_vnum = 0
			self.page_count = 0
			self.page = 0
			self.drop_dict = {}
			self.stone_frames = []
			self.stone_slot = None
			self.stone_frame_index = 0
			self.stone_next_time = 0.0
			self.hovered_stone = False
			self.tooltip_item = uiToolTip.ItemToolTip()

			self.__LoadWindow()

		def __del__(self):
			ui.BoardWithTitleBar.__del__(self)
			self.drop_dict = {}
			del self.tooltip_item
			self.slot_window = None
			self.prev_button = None
			self.next_button = None

		def __LoadWindow(self):
			self.SetWindowName("MobItemDropWindow")
			self.AddFlag("movable")
			self.AddFlag("float")

			self.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)
			self.SetCenterPosition()
			self.SetCloseEvent(ui.__mem_func__(self.Close))
			self.SetTitleName(localeInfo.TARGET_INFO_ITEM_DROP)

			window = ui.OutlineWindow()
			window.SetParent(self)
			window.SetPosition(0, 32)
			window.SetWindowHorizontalAlignCenter()
			window.MakeOutlineWindow(self.GetWidth() - 20, self.GetHeight() - 45)
			window.Show()
			self.window = window

			slot_window = ui.GridSlotWindow()
			slot_window.SetParent(self.window)
			slot_window.SetWindowHorizontalAlignCenter()
			slot_window.SetPosition(0, 10)
			slot_window.ArrangeSlot(0, nonplayer.MAX_MOB_ITEM_DROP_GRID_SLOT_X, nonplayer.MAX_MOB_ITEM_DROP_GRID_SLOT_Y, 32, 32, 0, 0)
			slot_window.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
			slot_window.RefreshSlot()
			slot_window.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInSlot))
			slot_window.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutSlot))
			slot_window.Show()
			self.slot_window = slot_window

			prev_button = ui.Button()
			prev_button.SetParent(self.window)
			prev_button.SetPosition(-40, 30)
			prev_button.SetWindowHorizontalAlignCenter()
			prev_button.SetWindowVerticalAlignBottom()
			prev_button.SetUpVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub")
			prev_button.SetOverVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_02.sub")
			prev_button.SetDownVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub")
			prev_button.SetEvent(ui.__mem_func__(self.__SetPage), -1)
			prev_button.Show()
			self.prev_button = prev_button

			next_button = ui.Button()
			next_button.SetParent(self.window)
			next_button.SetPosition(40, 30)
			next_button.SetWindowHorizontalAlignCenter()
			next_button.SetWindowVerticalAlignBottom()
			next_button.SetUpVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub")
			next_button.SetOverVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_02.sub")
			next_button.SetDownVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub")
			next_button.SetEvent(ui.__mem_func__(self.__SetPage), +1)
			next_button.Show()
			self.next_button = next_button

			page_window = ui.ThinBoardCircle()
			page_window.SetParent(self.window)
			page_window.SetSize(30, 20)
			page_window.SetPosition(0, 32)
			page_window.SetWindowHorizontalAlignCenter()
			page_window.SetWindowVerticalAlignBottom()
			page_window.Show()
			self.page_window = page_window

			page_text = ui.TextLine()
			page_text.SetParent(self.page_window)
			page_text.SetPosition(0, 3)
			page_text.SetWindowHorizontalAlignCenter()
			page_text.SetHorizontalAlignCenter()
			page_text.SetText("1")
			page_text.Show()
			self.page_text = page_text

		def __OnOverInSlot(self, slot_num):
			if self.tooltip_item and self.page in self.drop_dict:
				if slot_num in self.drop_dict[self.page]:
					if self.stone_slot == (self.page, slot_num) and self.stone_frames:
						self.hovered_stone = True
						self.tooltip_item.ClearToolTip()
						self.tooltip_item.SetTitle("Kámen ducha +4")
						self.tooltip_item.AppendTextLine("Náhodný druh kamene")
						self.tooltip_item.ShowToolTip()
						return
					data = self.drop_dict[self.page][slot_num]
					self.tooltip_item.SetItemToolTip(data[0])

		def __OnOverOutSlot(self):
			self.hovered_stone = False
			if self.tooltip_item:
				self.tooltip_item.HideToolTip()

		def OnUpdate(self):
			if not self.stone_frames or self.hovered_stone or app.GetTime() < self.stone_next_time:
				return
			self.stone_frame_index += 1
			if self.stone_slot and self.page == self.stone_slot[0]:
				vnum = self.stone_frames[self.stone_frame_index % len(self.stone_frames)]
				self.slot_window.SetItemSlot(self.stone_slot[1], vnum, 1)
				self.slot_window.RefreshSlot()
			self.stone_next_time = app.GetTime() + self.STONE_FRAME_DURATION

		def __RefreshItems(self):
			for i in range(nonplayer.MAX_MOB_ITEM_DROP_GRID_SIZE):
				self.slot_window.ClearSlot(i)

			if self.page in self.drop_dict:
				for pos in self.drop_dict[self.page]:
					data = self.drop_dict[self.page][pos]
					self.slot_window.SetItemSlot(pos, data[0], data[1])

			self.slot_window.RefreshSlot()

		def __SetPage(self, page):
			next_page = page + self.page
			if 0 <= next_page <= self.page_count:
				self.page = next_page
				self.page_text.SetText(str(self.page + 1))
				self.__RefreshItems()

		def Refresh(self):
			self.page = 0
			(self.page_count, drop_list) = nonplayer.GetMonsterItemDrop(self.race_vnum)
			self.stone_frames = []
			self.stone_slot = None
			self.stone_frame_index = 0
			self.stone_next_time = app.GetTime() + self.STONE_FRAME_DURATION

			self.drop_dict.clear()
			for i in range(self.page_count + 1):
				self.drop_dict[i] = dict()

			for page, pos, vnum, count in drop_list:
				if self.race_vnum in self.ALTHEA_METEOR_VNUMS and 28430 <= vnum <= 28443:
					if vnum not in self.stone_frames:
						self.stone_frames.append(vnum)
					if self.stone_slot is None:
						self.stone_slot = (page, pos)
					else:
						continue
				self.drop_dict[page][pos] = (vnum, count)

			self.__SetPage(0)

		def Open(self, race_vnum):
			if self.isLoaded == False:
				self.isLoaded = True
				self.__LoadWindow()

			self.race_vnum = race_vnum

			self.SetTitleName(nonplayer.GetMonsterName(self.race_vnum))
			self.SetCenterPosition()
			self.SetTop()
			self.Show()

			self.Refresh()

		def Close(self):
			self.__OnOverOutSlot()
			self.Hide()

		def OnPressEscapeKey(self):
			self.Close()
			return True

	class CrimsonTargetDetailsPanel(ui.Window):
		ALTHEA_METEOR_VNUMS = (8890, 8891, 8892, 8893)
		GRID_COLUMNS = 12
		GRID_ROWS = 4
		SLOT_SIZE = 32
		GRID_X = 18
		GRID_Y = 18
		GRID_SIZE = GRID_COLUMNS * GRID_ROWS
		BOARD_WIDTH = GRID_COLUMNS * SLOT_SIZE + GRID_X * 2
		BOARD_HEIGHT = GRID_ROWS * SLOT_SIZE + GRID_Y * 2
		STONE_FRAME_DURATION = 0.7

		def __init__(self, parent):
			ui.Window.__init__(self)
			self.SetWindowName("CrimsonTargetDetailsPanel")
			self.chrome = ui.ThinBoard(
				cornerPrefix=ui.TOOLTIP_CORNER_PREFIX,
				linePrefix=ui.TOOLTIP_LINE_PREFIX,
				baseColor=ui.TOOLTIP_BASE_COLOR,
			)
			self.chrome.SetParent(self)
			self.chrome.AddFlag("not_pick")
			self.chrome.Show()
			self.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)
			self.AddFlag("float")
			self.SetOnRunMouseWheelEvent(ui.__mem_func__(self.OnMouseWheel))
			self.parent = parent
			self.race_vnum = 0
			self.drop_items = []
			self.drop_heights = []
			self.pages = [[]]
			self.page_index = 0
			self.visible_slot_items = {}
			self.stone_cycles = {}
			self.stone_frame_index = 0
			self.stone_next_time = 0.0
			self.hover_slot = None
			self.tooltip_item = uiToolTip.ItemToolTip()

			slot_window = ui.GridSlotWindow()
			slot_window.SetParent(self)
			slot_window.SetPosition(self.GRID_X, self.GRID_Y)
			slot_window.SetSize(self.GRID_COLUMNS * self.SLOT_SIZE, self.GRID_ROWS * self.SLOT_SIZE)
			slot_window.ArrangeSlot(0, self.GRID_COLUMNS, self.GRID_ROWS, self.SLOT_SIZE, self.SLOT_SIZE, 0, 0)
			slot_window.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 1.0, 1.0, 1.0, 1.0)
			slot_window.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInSlot))
			slot_window.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutSlot))
			slot_window.SetOnRunMouseWheelEvent(ui.__mem_func__(self.OnMouseWheel))
			slot_window.Show()
			self.slot_window = slot_window

		def SetSize(self, width, height):
			ui.Window.SetSize(self, width, height)
			self.chrome.SetSize(width, height)

		def __BuildDisplayDrops(self, drop_list):
			display_drops = []
			stone_frames = []
			stone_insert_index = None
			seen_stones = set()
			for page, position, vnum, count in sorted(drop_list, key=lambda drop: (drop[0], drop[1], drop[2])):
				item.SelectItem(vnum)
				if item.GetItemType() == item.ITEM_TYPE_METIN and (self.race_vnum not in self.ALTHEA_METEOR_VNUMS or 28430 <= vnum <= 28443):
					if stone_insert_index is None:
						stone_insert_index = len(display_drops)
					if vnum not in seen_stones:
						seen_stones.add(vnum)
						stone_frames.append((vnum, item.GetIconImageFileName(), count))
					continue
				display_drops.append({"vnum": vnum, "frames": [(vnum, item.GetIconImageFileName(), count)]})
			if stone_frames:
				display_drops.insert(stone_insert_index, {"vnum": stone_frames[0][0], "frames": stone_frames})
			return display_drops

		def __LoadDrops(self):
			(_page_count, drop_list) = nonplayer.GetMonsterItemDrop(self.race_vnum)
			self.drop_items = self.__BuildDisplayDrops(drop_list)
			heights = []
			for entry in self.drop_items:
				item.SelectItem(entry["vnum"])
				heights.append(item.GetItemSize()[1])
			self.drop_heights = heights
			self.pages = PackDropGridPages(heights, self.GRID_COLUMNS, self.GRID_ROWS)
			self.ResetScroll()

		def __RefreshSlots(self):
			self.__OnOverOutSlot()
			for slot_number in range(self.GRID_SIZE):
				self.slot_window.ClearSlot(slot_number)
				self.slot_window.HideSlotBaseImage(slot_number)
			occupied, columns, rows = GetDropPageFootprint(
				self.pages[self.page_index], self.drop_heights, self.GRID_COLUMNS, self.GRID_ROWS
			)
			for slot_number in occupied:
				self.slot_window.ShowSlotBaseImage(slot_number)
			self.slot_window.SetSize(columns * self.SLOT_SIZE, rows * self.SLOT_SIZE)
			self.SetSize(self.GRID_X * 2 + columns * self.SLOT_SIZE,
				self.GRID_Y * 2 + rows * self.SLOT_SIZE)
			self.visible_slot_items = {}
			self.stone_cycles = {}
			for slot_number, index in self.pages[self.page_index]:
				frames = self.drop_items[index]["frames"]
				vnum, _icon_path, count = frames[0]
				self.slot_window.SetItemSlot(slot_number, vnum, count)
				self.visible_slot_items[slot_number] = vnum
				if len(frames) > 1:
					self.stone_cycles[slot_number] = frames
			self.stone_frame_index = 0
			self.stone_next_time = app.GetTime() + self.STONE_FRAME_DURATION
			self.slot_window.RefreshSlot()
			if self.IsShow() and self.parent:
				self.parent.UpdatePosition()

		def __OnOverInSlot(self, slot_number):
			vnum = self.visible_slot_items.get(slot_number)
			self.hover_slot = slot_number if vnum else None
			if vnum:
				if self.race_vnum in self.ALTHEA_METEOR_VNUMS and slot_number in self.stone_cycles:
					self.tooltip_item.ClearToolTip()
					self.tooltip_item.SetTitle("Kámen ducha +4")
					self.tooltip_item.AppendTextLine("Náhodný druh kamene")
					self.tooltip_item.ShowToolTip()
				else:
					self.tooltip_item.SetItemToolTip(vnum)

		def __OnOverOutSlot(self):
			self.hover_slot = None
			self.tooltip_item.HideToolTip()

		def OnUpdate(self):
			if not self.stone_cycles or app.GetTime() < self.stone_next_time:
				return
			self.stone_frame_index += 1
			for slot_number, frames in self.stone_cycles.items():
				if slot_number == self.hover_slot:
					continue
				vnum, _icon_path, count = frames[self.stone_frame_index % len(frames)]
				self.slot_window.SetItemSlot(slot_number, vnum, count)
				self.visible_slot_items[slot_number] = vnum
			self.slot_window.RefreshSlot()
			self.stone_next_time = app.GetTime() + self.STONE_FRAME_DURATION

		def ResetScroll(self):
			self.page_index = 0
			self.__RefreshSlots()

		def OnMouseWheel(self, scroll_down):
			page_index = self.page_index + (1 if scroll_down else -1)
			page_index = max(0, min(len(self.pages) - 1, page_index))
			if page_index != self.page_index:
				self.page_index = page_index
				self.__RefreshSlots()
			return True

		def Refresh(self):
			if not self.race_vnum:
				return
			nonplayer.SelectMob(self.race_vnum)
			self.__LoadDrops()

		def UpdateAutoY(self):
			if self.parent:
				parent_x, parent_y = self.parent.GetGlobalPosition()
				panel_x = parent_x + (self.parent.GetWidth() - self.GetWidth()) // 2
				self.SetPosition(panel_x, parent_y + self.parent.GetHeight() + self.parent.DETAILS_PANEL_GAP)

		def Open(self, race_vnum):
			self.race_vnum = race_vnum
			self.Refresh()
			self.UpdateAutoY()
			self.SetTop()
			self.Show()

		def Toggle(self, race_vnum):
			if self.IsShow() and self.race_vnum == race_vnum:
				self.Close()
				return False
			self.Open(race_vnum)
			return True

		def Close(self):
			self.__OnOverOutSlot()
			self.ResetScroll()
			self.Hide()
			if self.parent:
				self.parent.OnTargetDetailsPanelClosed()

		def OnPressEscapeKey(self):
			self.Close()
			return True

class TargetBoard(ui.Window):
	TARGET_CHROME_SIDE_INSET = 2
	DETAILS_PANEL_GAP = 4
	TARGET_DETAILS_ICON_SCALE = 20.0 / 28.0
	TARGET_DETAILS_ICON_SIZE = 20
	TARGET_DETAILS_ICON_GAP = 4
	TARGET_DETAILS_ICON_VISUAL_Y_OFFSET = 2
	TARGET_NAME_ROW_Y = 13
	METIN_TARGET_HEIGHT = 60
	METIN_QUEUE_ROW_Y = 40
	METIN_QUEUE_ROW_HEIGHT = 16
	if app.ENABLE_MESSENGER_BLOCK:
		BUTTON_NAME_LIST = [
			localeInfo.TARGET_BUTTON_WHISPER,
			localeInfo.TARGET_BUTTON_EXCHANGE,
			localeInfo.TARGET_BUTTON_FIGHT,
			localeInfo.TARGET_BUTTON_ACCEPT_FIGHT,
			localeInfo.TARGET_BUTTON_AVENGE,
			localeInfo.TARGET_BUTTON_FRIEND,
			localeInfo.TARGET_BUTTON_INVITE_PARTY,
			localeInfo.TARGET_BUTTON_LEAVE_PARTY,
			localeInfo.TARGET_BUTTON_EXCLUDE,
			localeInfo.TARGET_BUTTON_INVITE_GUILD,
			localeInfo.TARGET_BUTTON_DISMOUNT,
			localeInfo.TARGET_BUTTON_EXIT_OBSERVER,
			localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT,
			localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY,
			localeInfo.TARGET_BUTTON_BUILDING_DESTROY,
			localeInfo.TARGET_BUTTON_EMOTION_ALLOW,
			localeInfo.TARGET_BUTTON_BLOCK,
			localeInfo.TARGET_BUTTON_BLOCK_REMOVE,
			"VOTE_BLOCK_CHAT",
		]
	else:
		BUTTON_NAME_LIST = [
			localeInfo.TARGET_BUTTON_WHISPER,
			localeInfo.TARGET_BUTTON_EXCHANGE,
			localeInfo.TARGET_BUTTON_FIGHT,
			localeInfo.TARGET_BUTTON_ACCEPT_FIGHT,
			localeInfo.TARGET_BUTTON_AVENGE,
			localeInfo.TARGET_BUTTON_FRIEND,
			localeInfo.TARGET_BUTTON_INVITE_PARTY,
			localeInfo.TARGET_BUTTON_LEAVE_PARTY,
			localeInfo.TARGET_BUTTON_EXCLUDE,
			localeInfo.TARGET_BUTTON_INVITE_GUILD,
			localeInfo.TARGET_BUTTON_DISMOUNT,
			localeInfo.TARGET_BUTTON_EXIT_OBSERVER,
			localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT,
			localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY,
			localeInfo.TARGET_BUTTON_BUILDING_DESTROY,
			localeInfo.TARGET_BUTTON_EMOTION_ALLOW,
			"VOTE_BLOCK_CHAT",
		]

	GRADE_NAME = {
		nonplayer.PAWN : localeInfo.TARGET_LEVEL_PAWN,
		nonplayer.S_PAWN : localeInfo.TARGET_LEVEL_S_PAWN,
		nonplayer.KNIGHT : localeInfo.TARGET_LEVEL_KNIGHT,
		nonplayer.S_KNIGHT : localeInfo.TARGET_LEVEL_S_KNIGHT,
		nonplayer.BOSS : localeInfo.TARGET_LEVEL_BOSS,
		nonplayer.KING : localeInfo.TARGET_LEVEL_KING,
	}

	EXCHANGE_LIMIT_RANGE = 3000

	if app.ENABLE_ELEMENT_ADD:
		ELEMENT_IMG_PATH = {
			0: 'd:/ymir work/ui/game/12zi/element/elect.sub',
			1: 'd:/ymir work/ui/game/12zi/element/fire.sub',
			2: 'd:/ymir work/ui/game/12zi/element/ice.sub',
			3: 'd:/ymir work/ui/game/12zi/element/wind.sub',
			4: 'd:/ymir work/ui/game/12zi/element/earth.sub',
			5: 'd:/ymir work/ui/game/12zi/element/dark.sub'
		}
		ELEMENT_ENCHANT_ICON_SCALE = 0.8

	def __init__(self):
		ui.Window.__init__(self)

		self.chrome = ui.ThinBoard(
			cornerPrefix=ui.TOOLTIP_CORNER_PREFIX,
			linePrefix=ui.TOOLTIP_LINE_PREFIX,
			baseColor=ui.TOOLTIP_BASE_COLOR,
		)
		self.chrome.SetParent(self)
		self.chrome.SetPosition(self.TARGET_CHROME_SIDE_INSET, 0)
		self.chrome.AddFlag("not_pick")
		self.chrome.Show()

		if ENABLE_DPS_METER:
			dpsMeter = uiDpsMeter.DpsMeterPanel()
			dpsMeter.SetParent(self)
			dpsMeter.Hide()
			self.dpsMeter = dpsMeter

		if app.ENABLE_MESSENGER_BLOCK:
			self.AddFlag("float")

		name = ui.TextLine()
		name.SetParent(self)
		name.SetDefaultFontName()
		name.SetOutline()
		name.Show()
		self.name = name

		if app.ENABLE_AUTO_FARM_METIN:
			autoFarmText = ui.TextLine()
			autoFarmText.SetParent(self)
			autoFarmText.SetOutline()
			autoFarmText.SetHorizontalAlignCenter()
			autoFarmText.SetText("|Ikey/shift|i + |Ikey/mouse_right|i Fronta meteorů (0/0)")
			autoFarmText.Hide()
			self.autoFarmText = autoFarmText

		hpGauge = TargetAnimatedHpGauge()
		hpGauge.SetParent(self)
		hpGauge.Hide()
		self.hpGauge = hpGauge

		if app.ENABLE_VIEW_TARGET_DECIMAL_HP:
			hpDecimal = ui.TextLine()
			hpDecimal.SetParent(hpGauge)
			hpDecimal.SetDefaultFontName()
			hpDecimal.SetPosition(5, 5)
			hpDecimal.SetOutline()
			hpDecimal.Hide()
			self.hpDecimal = hpDecimal

		if app.ENABLE_SEND_TARGET_INFO:
			target_details_button = ui.ExpandedImageBox()
			target_details_button.SetParent(self)
			target_details_button.LoadImage("local_target_board/toggle/inactive.png")
			target_details_button.SetScale(self.TARGET_DETAILS_ICON_SCALE, self.TARGET_DETAILS_ICON_SCALE)
			target_details_button.SetEvent(ui.__mem_func__(self.__OnClickTargetDetailsButton), "mouse_click")
			target_details_button.Hide()
			self.target_details_button = target_details_button

			target_details_thinboard = CrimsonTargetDetailsPanel(self)
			target_details_thinboard.Hide()
			self.target_details_thinboard = target_details_thinboard

		closeButton = ui.Button()
		closeButton.SetParent(self)
		closeButton.SetUpVisual("d:/ymir work/ui/public/crimson_close_01.tga")
		closeButton.SetOverVisual("d:/ymir work/ui/public/crimson_close_02.tga")
		closeButton.SetDownVisual("d:/ymir work/ui/public/crimson_close_03.tga")
		closeButton.SetPosition(30, 13)

		if localeInfo.IsARABIC():
			hpGauge.SetPosition(51, 17)
			hpGauge.SetWindowHorizontalAlignLeft()
			closeButton.SetWindowHorizontalAlignLeft()
		else:
			hpGauge.SetPosition(144, 17)
			hpGauge.SetWindowHorizontalAlignRight()
			closeButton.SetWindowHorizontalAlignRight()

		closeButton.SetEvent(ui.__mem_func__(self.OnPressedCloseButton))
		closeButton.Show()
		self.closeButton = closeButton

		self.buttonDict = {}
		self.showingButtonList = []
		for buttonName in self.BUTTON_NAME_LIST:
			button = ui.Button()
			button.SetParent(self)

			if localeInfo.IsARABIC():
				button.SetUpVisual("d:/ymir work/ui/public/Small_Button_01.sub")
				button.SetOverVisual("d:/ymir work/ui/public/Small_Button_02.sub")
				button.SetDownVisual("d:/ymir work/ui/public/Small_Button_03.sub")
			else:
				button.SetUpVisual("d:/ymir work/ui/public/small_thin_button_01.sub")
				button.SetOverVisual("d:/ymir work/ui/public/small_thin_button_02.sub")
				button.SetDownVisual("d:/ymir work/ui/public/small_thin_button_03.sub")

			button.SetWindowHorizontalAlignCenter()
			button.SetText(buttonName)
			button.Hide()
			self.buttonDict[buttonName] = button
			self.showingButtonList.append(button)

		self.buttonDict[localeInfo.TARGET_BUTTON_WHISPER].SetEvent(ui.__mem_func__(self.OnWhisper))
		self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE].SetEvent(ui.__mem_func__(self.OnExchange))
		self.buttonDict[localeInfo.TARGET_BUTTON_FIGHT].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_ACCEPT_FIGHT].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_AVENGE].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_FRIEND].SetEvent(ui.__mem_func__(self.OnAppendToMessenger))
		self.buttonDict[localeInfo.TARGET_BUTTON_FRIEND].SetEvent(ui.__mem_func__(self.OnAppendToMessenger))
		self.buttonDict[localeInfo.TARGET_BUTTON_INVITE_PARTY].SetEvent(ui.__mem_func__(self.OnPartyInvite))
		self.buttonDict[localeInfo.TARGET_BUTTON_LEAVE_PARTY].SetEvent(ui.__mem_func__(self.OnPartyExit))
		self.buttonDict[localeInfo.TARGET_BUTTON_EXCLUDE].SetEvent(ui.__mem_func__(self.OnPartyRemove))

		self.buttonDict[localeInfo.TARGET_BUTTON_INVITE_GUILD].SAFE_SetEvent(self.__OnGuildAddMember)
		self.buttonDict[localeInfo.TARGET_BUTTON_DISMOUNT].SAFE_SetEvent(self.__OnDismount)
		self.buttonDict[localeInfo.TARGET_BUTTON_EXIT_OBSERVER].SAFE_SetEvent(self.__OnExitObserver)
		self.buttonDict[localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT].SAFE_SetEvent(self.__OnViewEquipment)
		self.buttonDict[localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY].SAFE_SetEvent(self.__OnRequestParty)
		self.buttonDict[localeInfo.TARGET_BUTTON_BUILDING_DESTROY].SAFE_SetEvent(self.__OnDestroyBuilding)
		self.buttonDict[localeInfo.TARGET_BUTTON_EMOTION_ALLOW].SAFE_SetEvent(self.__OnEmotionAllow)
		if app.ENABLE_MESSENGER_BLOCK:
			self.buttonDict[localeInfo.TARGET_BUTTON_BLOCK].SAFE_SetEvent(self.__OnBlock)
			self.buttonDict[localeInfo.TARGET_BUTTON_BLOCK_REMOVE].SAFE_SetEvent(self.__OnBlockRemove)

		self.buttonDict["VOTE_BLOCK_CHAT"].SetEvent(ui.__mem_func__(self.__OnVoteBlockChat))

		self.__Initialize()
		self.ResetTargetBoard()

	def __del__(self):
		ui.Window.__del__(self)

		print("===================================================== DESTROYED TARGET BOARD")

	def SetSize(self, width, height):
		ui.Window.SetSize(self, width, height)
		self.chrome.SetSize(width - self.TARGET_CHROME_SIDE_INSET * 2, height)

	def __Initialize(self):
		self.nameString = ""
		self.nameLength = 0
		self.vid = 0
		self.isShowButton = False
		if app.ENABLE_AUTO_FARM_METIN:
			self.metinQueueState = None

		if app.ENABLE_SEND_TARGET_INFO:
			self.race_vnum = 0

		if app.ENABLE_ELEMENT_ADD:
			self.element_enchants_dict = {}
			self.elementImgList = []

		if osfInfo.PAST_HEALTH_ON_TARGET:
			self.oldPercentage = 100
			self.newPercentage = 100

	def __CloseTargetDetailsPanel(self):
		if not app.ENABLE_SEND_TARGET_INFO:
			return
		panel = getattr(self, "target_details_thinboard", None)
		if panel and panel.IsShow():
			panel.Close()

	def Hide(self):
		self.__CloseTargetDetailsPanel()
		ui.Window.Hide(self)

	def Destroy(self):
		self.__CloseTargetDetailsPanel()
		self.__Initialize()

		if ENABLE_DPS_METER:
			self.dpsMeter.Reset()
			self.dpsMeter = None

		self.name = None
		self.hpGauge = None
		self.chrome = None
		if app.ENABLE_VIEW_TARGET_DECIMAL_HP:
			self.hpDecimal = None

		if app.ENABLE_SEND_TARGET_INFO:
			if self.target_details_thinboard:
				self.target_details_thinboard.parent = None
			self.target_details_thinboard = None
			self.target_details_button = None

		self.closeButton = None
		self.buttonDict = None
		self.showingButtonList = None

		if app.ENABLE_ELEMENT_ADD:
			self.elementImgList = None
			self.element_enchants_dict = {}

	if app.ENABLE_SEND_TARGET_INFO:
		def RefreshMonsterInfoBoard(self, raceNum):
			if int(raceNum) != self.race_vnum:
				return
			if self.target_details_thinboard.IsShow():
				self.target_details_thinboard.Refresh()
			dropWindow = self.target_details_thinboard.item_drop_window
			if dropWindow and dropWindow.IsShow() and dropWindow.race_vnum == self.race_vnum:
				dropWindow.Refresh()

		def OnTargetDetailsPanelClosed(self):
			self.__SetTargetDetailsButtonState(False)
			if app.ENABLE_ELEMENT_ADD:
				self.ShowElementImg(self.element_enchants_dict)
			self.UpdatePosition()

		def __SetTargetDetailsButtonState(self, active):
			visual = "local_target_board/toggle/active.png" if active else "local_target_board/toggle/inactive.png"
			self.target_details_button.LoadImage(visual)
			self.target_details_button.SetScale(self.TARGET_DETAILS_ICON_SCALE, self.TARGET_DETAILS_ICON_SCALE)

		def __UpdateTargetDetailsButtonPosition(self):
			if not self.target_details_button:
				return

			name_x, name_y = self.name.GetGlobalPosition()
			board_x, board_y = self.GetGlobalPosition()
			text_width, text_height = self.name.GetTextSize()
			if not self.hpGauge.IsShow():
				name_x -= text_width // 2
			icon_height = self.TARGET_DETAILS_ICON_SIZE
			icon_x = name_x - board_x + text_width + self.TARGET_DETAILS_ICON_GAP
			icon_y = GetCenteredImageY(name_y - board_y, text_height, icon_height) + self.TARGET_DETAILS_ICON_VISUAL_Y_OFFSET
			self.target_details_button.SetPosition(icon_x, icon_y)
			self.target_details_button.SetWindowHorizontalAlignLeft()

		def __OnClickTargetDetailsButton(self, event_type=None):
			if not self.target_details_thinboard:
				return
			if chr.GetInstanceType(self.vid) not in (chr.INSTANCE_TYPE_ENEMY, chr.INSTANCE_TYPE_STONE):
				return
			if not self.race_vnum:
				return

			net.RequestTargetInfo(player.GetTargetVID())
			is_open = self.target_details_thinboard.Toggle(self.race_vnum)
			self.__SetTargetDetailsButtonState(is_open)
			if app.ENABLE_ELEMENT_ADD:
				if is_open:
					self.__HideAllElementImg()
				else:
					self.ShowElementImg(self.element_enchants_dict)
			self.UpdatePosition()

	def OnPressedCloseButton(self):
		player.ClearTarget()
		self.Close()

	def Close(self):
		self.__Initialize()

		if ENABLE_DPS_METER:
			self.dpsMeter.Reset()

		if app.ENABLE_SEND_TARGET_INFO:
			if self.target_details_thinboard:
				self.target_details_thinboard.Close()
				self.__SetTargetDetailsButtonState(False)

		self.Hide()

	def Open(self, vid, name):
		if vid:
			if not constInfo.GET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD():
				if not player.IsSameEmpire(vid):
					self.Hide()
					return

			if vid != self.GetTargetVID():
				self.ResetTargetBoard()
				self.SetTargetVID(vid)
				self.SetTargetName(name)

			if player.IsMainCharacterIndex(vid):
				self.__ShowMainCharacterMenu()
			elif chr.INSTANCE_TYPE_BUILDING == chr.GetInstanceType(self.vid):
				self.Hide()
			else:
				self.RefreshButton()
				self.Show()
		else:
			self.HideAllButton()
			self.__ShowButton(localeInfo.TARGET_BUTTON_WHISPER)
			self.__ShowButton("VOTE_BLOCK_CHAT")
			self.__ArrangeButtonPosition()
			self.SetTargetName(name)
			self.Show()

	def Refresh(self):
		if self.IsShow():
			if self.IsShowButton():
				self.RefreshButton()

	def RefreshByVID(self, vid):
		if vid == self.GetTargetVID():
			self.Refresh()

	def RefreshByName(self, name):
		if name == self.GetTargetName():
			self.Refresh()

	def __ShowMainCharacterMenu(self):
		canShow = 0

		self.HideAllButton()

		if player.IsMountingHorse():
			self.__ShowButton(localeInfo.TARGET_BUTTON_DISMOUNT)
			canShow = 1

		if player.IsObserverMode():
			self.__ShowButton(localeInfo.TARGET_BUTTON_EXIT_OBSERVER)
			canShow = 1

		if canShow:
			self.__ArrangeButtonPosition()
			self.Show()
		else:
			self.Hide()

	def __ShowNameOnlyMenu(self):
		self.HideAllButton()

	def SetWhisperEvent(self, event):
		self.eventWhisper = event

	def UpdatePosition(self):
		self.SetPosition(wndMgr.GetScreenWidth() // 2 - self.GetWidth() // 2, 10)
		if app.ENABLE_SEND_TARGET_INFO:
			self.__UpdateTargetDetailsButtonPosition()
		if app.ENABLE_ELEMENT_ADD:
			self.AdjustPositionElementImage()

		if app.ENABLE_AUTO_FARM_METIN:
			if chr.GetInstanceType(self.vid) == chr.INSTANCE_TYPE_STONE:
				self.SetSize(self.GetWidth(), self.METIN_TARGET_HEIGHT)

				self.__RefreshMetinQueueText()
				self.autoFarmText.SetPosition(self.GetWidth() // 2, self.METIN_QUEUE_ROW_Y)
				self.autoFarmText.Show()
			else:
				self.autoFarmText.Hide()

		if app.ENABLE_SEND_TARGET_INFO and self.target_details_thinboard and self.target_details_thinboard.IsShow():
			self.target_details_thinboard.UpdateAutoY()

		if ENABLE_DPS_METER and self.dpsMeter:
			details_height = 0
			if app.ENABLE_SEND_TARGET_INFO and self.target_details_thinboard.IsShow():
				details_height = self.DETAILS_PANEL_GAP + self.target_details_thinboard.GetHeight()
			self.dpsMeter.SetPosition(
				(self.GetWidth() - self.dpsMeter.WIDTH) // 2,
				self.GetHeight() + details_height + 2,
			)

	if app.ENABLE_AUTO_FARM_METIN:
		def __RefreshMetinQueueText(self):
			queue_state = (
				int(player.GetMetinQueueCount()),
				int(player.GetMetinQueueCapacity()),
			)
			if queue_state == self.metinQueueState:
				return
			self.metinQueueState = queue_state
			self.autoFarmText.SetText(
				"|Ikey/shift|i + |Ikey/mouse_right|i Fronta meteorů (%d/%d)" % queue_state
			)

	if app.ENABLE_WINDOW_RESIZE:
		def OnResize(self):
			try:
				if self.IsShow():
					self.UpdatePosition()
			except:
				pass

	def ResetTargetBoard(self):
		for btn in self.buttonDict.values():
			btn.Hide()

		self.__Initialize()

		if ENABLE_DPS_METER:
			self.dpsMeter.Reset()

		self.name.SetPosition(0, self.TARGET_NAME_ROW_Y)
		self.name.SetHorizontalAlignCenter()
		self.name.SetWindowHorizontalAlignCenter()

		self.hpGauge.Hide()
		if app.ENABLE_VIEW_TARGET_DECIMAL_HP:
			self.hpDecimal.Hide()

		if app.ENABLE_SEND_TARGET_INFO:
			self.target_details_button.Hide()
			if self.target_details_thinboard:
				self.target_details_thinboard.Close()
				self.target_details_thinboard.ResetScroll()
				self.__SetTargetDetailsButtonState(False)

		self.SetSize(250, 40)

	if ENABLE_DPS_METER:
		def ApplyDpsMeterSnapshot(self, victimVid, encounterId, flags, totalDamage, rows):
			if victimVid != self.GetTargetVID():
				return
			if chr.GetInstanceType(victimVid) not in (chr.INSTANCE_TYPE_ENEMY, chr.INSTANCE_TYPE_STONE):
				return
			self.dpsMeter.ApplySnapshot(victimVid, encounterId, flags, totalDamage, rows)
			self.UpdatePosition()

	def SetTargetVID(self, vid):
		self.vid = vid
		if app.ENABLE_SEND_TARGET_INFO:
			self.race_vnum = 0
			if self.target_details_thinboard:
				self.target_details_thinboard.ResetScroll()

	def SetEnemyVID(self, vid):
		self.SetTargetVID(vid)

		if app.ENABLE_SEND_TARGET_INFO:
			race_vnum = nonplayer.GetRaceByVID(vid)
		name = chr.GetNameByVID(vid)
		level = nonplayer.GetLevelByVID(vid)
		grade = nonplayer.GetGradeByVID(vid)

		nameFront = ""
		if -1 != level:
			nameFront += "Lv." + str(level) + " "
		if chr.GetInstanceType(vid) == chr.INSTANCE_TYPE_STONE:
			nameFront += "(" + localeInfo.TARGET_INFO_RACE_METIN + ") "
		elif grade in self.GRADE_NAME:
			nameFront += "(" + self.GRADE_NAME[grade] + ") "

		if chr.IsGameMaster(player.GetMainCharacterIndex()):
			self.SetTargetName(nameFront + name + " ({})".format(race_vnum))
		else:
			self.SetTargetName(nameFront + name)

		if app.ENABLE_SEND_TARGET_INFO:
			if race_vnum >= 101:
				self.race_vnum = race_vnum

				if chr.GetInstanceType(self.vid) in (chr.INSTANCE_TYPE_ENEMY, chr.INSTANCE_TYPE_STONE):
					self.__SetTargetDetailsButtonState(False)
					self.__UpdateTargetDetailsButtonPosition()
					self.target_details_button.Show()

	def GetTargetVID(self):
		return self.vid

	def GetTargetName(self):
		return self.nameString

	def SetTargetName(self, name):
		self.nameString = name
		self.nameLength = len(name)
		self.name.SetText(name)

	if app.ENABLE_VIEW_TARGET_DECIMAL_HP:
		def SetHP(self, hpPercentage, iMinHP, iMaxHP):
			if not self.hpGauge.IsShow():
				if app.ENABLE_VIEW_TARGET_PLAYER_HP:
					showingButtonCount = len(self.showingButtonList)
					if showingButtonCount < len(self.BUTTON_NAME_LIST):
						if chr.GetInstanceType(self.vid) == chr.INSTANCE_TYPE_PLAYER:
							self.SetSize(max(150 + 75 * 3, showingButtonCount * 75), self.GetHeight())
						else:
							self.SetSize(200 + 7 * self.nameLength, self.GetHeight())
					else:
						self.SetSize(200 + 7 * self.nameLength, self.GetHeight())
				else:
					self.SetSize(200 + 7 * self.nameLength, self.GetHeight())

				if localeInfo.IsARABIC():
					self.name.SetPosition(self.GetWidth() - 23, self.TARGET_NAME_ROW_Y)
				else:
					self.name.SetPosition(23, self.TARGET_NAME_ROW_Y)

				self.name.SetWindowHorizontalAlignLeft()
				self.name.SetHorizontalAlignLeft()
				self.hpGauge.Show()
				self.UpdatePosition()

			if app.ENABLE_POISON_GAUGE_EFFECT:
				prevHp = self.hpGauge.GetPrevalue()
				if not prevHp:
					prevHp = hpPercentage
				if chrmgr.HasAffectByVID(self.GetTargetVID(), chr.AFFECT_POISON):
					self.hpGauge.SetGaugeColor("lime")
					self.hpGauge.SetDMGPercentage(self.GetTargetVID(), hpPercentage, prevHp, self.hpGauge.GAUGE_WIDTH, 0x55008000)
				else:
					self.hpGauge.SetGaugeColor("red")
					self.hpGauge.SetDMGPercentage(self.GetTargetVID(), hpPercentage, prevHp, self.hpGauge.GAUGE_WIDTH, 0x55ff0000)

			self.hpGauge.SetPercentage(hpPercentage, 100)

			if osfInfo.PAST_HEALTH_ON_TARGET:
				self.oldPercentage = float(self.newPercentage)
				self.newPercentage = float(hpPercentage)

				self.hpGauge.SetPercentageBack(self.oldPercentage, 100)

			if app.ENABLE_VIEW_TARGET_DECIMAL_HP:
				iMinHPText = '.'.join([i - 3 < 0 and str(iMinHP)[:i] or str(iMinHP)[i-3:i] for i in range(len(str(iMinHP)) % 3, len(str(iMinHP))+1, 3) if i])
				iMaxHPText = '.'.join([i - 3 < 0 and str(iMaxHP)[:i] or str(iMaxHP)[i-3:i] for i in range(len(str(iMaxHP)) % 3, len(str(iMaxHP))+1, 3) if i])
				self.hpDecimal.SetText(str(iMinHPText) + "/" + str(iMaxHPText) + " |cffFFA07A(%d%%)" % (hpPercentage))
				(textWidth, textHeight) = self.hpDecimal.GetTextSize()
				if localeInfo.IsARABIC():
					self.hpDecimal.SetPosition(self.hpGauge.GAUGE_WIDTH // 2 + textWidth // 2, -15)
				else:
					self.hpDecimal.SetPosition(self.hpGauge.GAUGE_WIDTH // 2 - textWidth // 2, -15)

				self.hpDecimal.Show()
	else:
		def SetHP(self, hpPercentage):
			if not self.hpGauge.IsShow():
				if app.ENABLE_VIEW_TARGET_PLAYER_HP:
					showingButtonCount = len(self.showingButtonList)
					if showingButtonCount > 0:
						if chr.GetInstanceType(self.GetTargetVID) != chr.INSTANCE_TYPE_PLAYER:
							if showingButtonCount != 1:
								self.SetSize(max(150, showingButtonCount * 75), self.GetHeight())
							else:
								self.SetSize(max(150, 2 * 75), self.GetHeight())
						else:
							self.SetSize(200 + 7 * self.nameLength, self.GetHeight())
					else:
						self.SetSize(200 + 7 * self.nameLength, self.GetHeight())
				else:
					self.SetSize(200 + 7 * self.nameLength, self.GetHeight())

				if localeInfo.IsARABIC():
					self.name.SetPosition(self.GetWidth() - 23, self.TARGET_NAME_ROW_Y)
				else:
					self.name.SetPosition(23, self.TARGET_NAME_ROW_Y)

				self.name.SetWindowHorizontalAlignLeft()
				self.name.SetHorizontalAlignLeft()
				self.hpGauge.Show()
				self.UpdatePosition()

			if app.ENABLE_POISON_GAUGE_EFFECT:
				prevHp = self.hpGauge.GetPrevalue()
				if not prevHp:
					prevHp = hpPercentage
				if chrmgr.HasAffectByVID(self.GetTargetVID(), chr.AFFECT_POISON):
					self.hpGauge.SetGaugeColor("lime")
					self.hpGauge.SetDMGPercentage(self.GetTargetVID(), hpPercentage, prevHp, self.hpGauge.GAUGE_WIDTH, 0x55008000)
				else:
					self.hpGauge.SetGaugeColor("red")
					self.hpGauge.SetDMGPercentage(self.GetTargetVID(), hpPercentage, prevHp, self.hpGauge.GAUGE_WIDTH, 0x55ff0000)

			if osfInfo.PAST_HEALTH_ON_TARGET:
				if self.oldPercentage > self.newPercentage:
					self.oldPercentage = self.oldPercentage - 0.5
					self.hpGauge.SetPercentageBack(self.oldPercentage, 100)
				else:
					self.hpGauge.SetPercentage(hpPercentage, 100)
			else:
				self.hpGauge.SetPercentage(hpPercentage, 100)

	def ShowDefaultButton(self):
		self.isShowButton = True
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_WHISPER])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_FIGHT])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_EMOTION_ALLOW])
		if app.ENABLE_VIEW_EQUIPMENT_SYSTEM:
			self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT])
		for button in self.showingButtonList:
			button.Show()

	def HideAllButton(self):
		self.isShowButton = False
		for button in self.showingButtonList:
			button.Hide()
		self.showingButtonList = []

	def __ShowButton(self, name):
		if name not in self.buttonDict:
			return

		self.buttonDict[name].Show()
		self.showingButtonList.append(self.buttonDict[name])

	def __HideButton(self, name):
		if name not in self.buttonDict:
			return

		button = self.buttonDict[name]
		button.Hide()

		for btnInList in self.showingButtonList:
			if btnInList == button:
				self.showingButtonList.remove(button)
				break

	def OnWhisper(self):
		if None != self.eventWhisper:
			self.eventWhisper(self.nameString)

	def OnExchange(self):
		net.SendExchangeStartPacket(self.vid)

	def OnPVP(self):
		net.SendChatPacket("/pvp %d" % (self.vid))

	def OnAppendToMessenger(self):
		net.SendMessengerAddByVIDPacket(self.vid)

	def OnPartyInvite(self):
		net.SendPartyInvitePacket(self.vid)

	def OnPartyExit(self):
		net.SendPartyExitPacket()

	def OnPartyRemove(self):
		pid = player.PartyMemberVIDToPID(self.vid)
		if pid:
			net.SendPartyRemovePacket(pid)

	def __OnGuildAddMember(self):
		if callable(getattr(net, "IsGuildV2Available", None)):
			interface = osfInfo.GetInterfaceInstance()
			if interface and interface.wndGuild:
				interface.wndGuild.OpenInvite(chr.GetNameByVID(self.vid))
			return
		net.SendGuildAddMemberPacket(self.vid)

	def __OnDismount(self):
		net.SendChatPacket("/unmount")

	def __OnExitObserver(self):
		net.SendChatPacket("/observer_exit")

	def __OnViewEquipment(self):
		net.SendChatPacket("/view_equip " + str(self.vid))

	def __OnRequestParty(self):
		net.SendChatPacket("/party_request " + str(self.vid))

	def __OnDestroyBuilding(self):
		net.SendChatPacket("/build d %d" % (self.vid))

	def __OnEmotionAllow(self):
		net.SendChatPacket("/emotion_allow %d" % (self.vid))

	def __OnVoteBlockChat(self):
		cmd = "/vote_block_chat %s" % (self.nameString)
		net.SendChatPacket(cmd)

	def OnPressEscapeKey(self):
		self.OnPressedCloseButton()
		return True

	def IsShowButton(self):
		return self.isShowButton

	def RefreshButton(self):
		self.HideAllButton()

		if chr.INSTANCE_TYPE_BUILDING == chr.GetInstanceType(self.vid):
			#self.__ShowButton(localeInfo.TARGET_BUTTON_BUILDING_DESTROY)
			#self.__ArrangeButtonPosition()
			return

		if player.IsPVPInstance(self.vid) or player.IsObserverMode():
			# PVP_INFO_SIZE_BUG_FIX
			self.SetSize(200 + 7 * self.nameLength, 40)
			self.UpdatePosition()
			# END_OF_PVP_INFO_SIZE_BUG_FIX
			return

		self.ShowDefaultButton()

		interface = osfInfo.GetInterfaceInstance()
		canInvite = (bool(interface and interface.wndGuild and interface.wndGuild.CanInviteMember())
			if callable(getattr(net, "IsGuildV2Available", None)) else guild.MainPlayerHasAuthority(guild.AUTH_ADD_MEMBER))
		if canInvite:
			if not guild.IsMemberByName(self.nameString):
				if 0 == chr.GetGuildID(self.vid):
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_GUILD)

		if not messenger.IsFriendByName(self.nameString):
			self.__ShowButton(localeInfo.TARGET_BUTTON_FRIEND)

		if app.ENABLE_MESSENGER_BLOCK:
			if not messenger.IsBlockFriendByName(self.nameString):
				self.__ShowButton(localeInfo.TARGET_BUTTON_BLOCK)
			else:
				self.__ShowButton(localeInfo.TARGET_BUTTON_BLOCK_REMOVE)

		if player.IsPartyMember(self.vid):
			self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

			if player.IsPartyLeader(self.vid):
				self.__ShowButton(localeInfo.TARGET_BUTTON_LEAVE_PARTY)
			elif player.IsPartyLeader(player.GetMainCharacterIndex()):
				self.__ShowButton(localeInfo.TARGET_BUTTON_EXCLUDE)
		else:
			if player.IsPartyMember(player.GetMainCharacterIndex()):
				if player.IsPartyLeader(player.GetMainCharacterIndex()):
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)
			else:
				if chr.IsPartyMember(self.vid):
					self.__ShowButton(localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY)
				else:
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)

			if player.IsRevengeInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)
				self.__ShowButton(localeInfo.TARGET_BUTTON_AVENGE)
			elif player.IsChallengeInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)
				self.__ShowButton(localeInfo.TARGET_BUTTON_ACCEPT_FIGHT)
			elif player.IsCantFightInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

			if not player.IsSameEmpire(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)
				self.__HideButton(localeInfo.TARGET_BUTTON_FRIEND)
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

		distance = player.GetCharacterDistance(self.vid)
		if distance > self.EXCHANGE_LIMIT_RANGE:
			self.__HideButton(localeInfo.TARGET_BUTTON_EXCHANGE)
			self.__ArrangeButtonPosition()

		self.__ArrangeButtonPosition()

	def __ArrangeButtonPosition(self):
		showingButtonCount = len(self.showingButtonList)

		pos = -(showingButtonCount // 2) * 68
		if 0 == showingButtonCount % 2:
			pos += 34

		for button in self.showingButtonList:
			button.SetPosition(pos, 33)
			pos += 68

		if app.ENABLE_VIEW_TARGET_PLAYER_HP:
			if showingButtonCount <= 2:
				self.SetSize(max(150 + 125, showingButtonCount * 75), 65)
			else:
				self.SetSize(max(150, showingButtonCount * 75), 65)
		else:
			self.SetSize(max(150, showingButtonCount * 75), 65)

		self.UpdatePosition()

	def OnUpdate(self):
		if app.ENABLE_AUTO_FARM_METIN and self.autoFarmText.IsShow():
			self.__RefreshMetinQueueText()

		if self.isShowButton:
			exchangeButton = self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE]
			distance = player.GetCharacterDistance(self.vid)

			if distance < 0:
				if app.WJ_NEW_USER_CARE:
					player.ClearTarget()
					self.Close()
				return

			if exchangeButton.IsShow():
				if distance > self.EXCHANGE_LIMIT_RANGE:
					self.RefreshButton()
			else:
				if distance < self.EXCHANGE_LIMIT_RANGE:
					self.RefreshButton()

	if app.ENABLE_MESSENGER_BLOCK:
		def __OnBlock(self):
			net.SendMessengerBlockAddByVIDPacket(self.vid)

		def __OnBlockRemove(self):
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(localeInfo.MESSENGER_DO_YOU_DELETE)
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnBlockRemove))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnBlockRemoveClose))
			self.questionDialog.Open()

		def OnBlockRemove(self):
			messenger.RemoveBlock(self.vid)
			net.SendMessengerBlockRemoveByVIDPacket(self.vid, chr.GetNameByVID(self.vid))
			self.OnBlockRemoveClose()

		def OnBlockRemoveClose(self):
			self.questionDialog.Close()
			self.questionDialog = None
			return True

	if app.ENABLE_ELEMENT_ADD:
		def AdjustPositionElementImage(self):

			if app.ENABLE_SEND_TARGET_INFO:
				if self.target_details_thinboard and self.target_details_thinboard.IsShow():
					self.__HideAllElementImg()
					return

			if not self.elementImgList:
				return

			isShowButton = False
			if self.IsShowButton():
				isShowButton = True

			for button in self.showingButtonList:
				if button.IsShow():
					isShowButton = True
					break

			for element, elementImg in enumerate(self.elementImgList):
				elementImg.SetPosition((32 * element - 1), 65 if isShowButton else 40)
				elementImg.SetScale(self.ELEMENT_ENCHANT_ICON_SCALE, self.ELEMENT_ENCHANT_ICON_SCALE)
				elementImg.Show()

		def ShowElementImg(self, element_enchants_dict):
			if not element_enchants_dict:
				return

			self.element_enchants_dict = element_enchants_dict

			if all(value == 0 for value in element_enchants_dict.values()) or not element_enchants_dict:
				self.__HideAllElementImg()
				return

			elementDict = sorted(element_enchants_dict.items(), key = lambda item : item[1])
			elementDict.reverse()

			self.elementImgList = []
			for key, value in elementDict:
				if value <= 0:
					continue

				elementImg = ui.ExpandedImageBox()
				elementImg.SetParent(self)
				elementImg.LoadImage(self.ELEMENT_IMG_PATH[key])
				elementImg.Hide()

				self.elementImgList.append(elementImg)

			self.AdjustPositionElementImage()

		def __HideAllElementImg(self):
			if self.elementImgList:
				for elementImg in self.elementImgList:
					elementImg.Hide()
				self.elementImgList = []
