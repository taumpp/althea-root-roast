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
import dropsort
import uiToolTip
import uimonsterindicators
import uitargetr1

ENABLE_DPS_METER = getattr(app, "ENABLE_DPS_METER", False)

if ENABLE_DPS_METER:
	import uiDpsMeter

if app.ENABLE_MESSENGER_BLOCK:
	import uiCommon

if app.ENABLE_POISON_GAUGE_EFFECT:
	import chrmgr


# races whose listed drops do not drop at the player's level (an ordinary monster more than the
# server's level_gap below him). The server sends TargetDropLevelGapV1 <race> <0|1> before every drop list; the
# list stays visible like a Metin's or a boss's and each item's tooltip says why it does not drop.
DROP_LEVEL_GAP_NOTE = "Kvůli levelu nepadá"
_dropLevelGapRaces = set()


def SetDropLevelGap(race, blocked):
	try:
		race = int(race)
		blocked = int(blocked) != 0
	except (TypeError, ValueError):
		return
	if blocked:
		_dropLevelGapRaces.add(race)
	else:
		_dropLevelGapRaces.discard(race)


def IsDropLevelGap(race):
	try:
		return int(race) in _dropLevelGapRaces
	except (TypeError, ValueError):
		return False


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
			# R1 frame over the original ThinBoard (None: Starý vzhled or a failure, the ThinBoard stays).
			self.r1look = uitargetr1.DressDropPanel(self)
			self.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)
			self.AddFlag("float")
			self.SetOnRunMouseWheelEvent(ui.__mem_func__(self.OnMouseWheel))
			self.parent = parent
			self.owner = parent         # the board (kept apart: SetParent of the form re-parents the window)
			self.race_vnum = 0
			self.opened = False
			# The unified target form (uitargetform, variant A): the panel is the "Kořist" section of the board's
			# frame. form = the form (None: the original floating panel), columns = the grid's columns at the
			# form's width (the engine grid stays GRID_COLUMNS wide: a packed cell maps onto it, see _Slot).
			self.form = None
			self.formWidth = 0
			self.columns = self.GRID_COLUMNS
			self.used_columns = 0
			self.used_rows = 0
			self.cascade = None         # (clock, columns revealed) while the icons cascade in
			self.slot_columns = {}      # engine slot -> its column in the packed grid (the cascade goes by column)
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
			if self.r1look is not None:
				self.r1look.Slots(slot_window)
			slot_window.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInSlot))
			slot_window.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutSlot))
			slot_window.SetOnRunMouseWheelEvent(ui.__mem_func__(self.OnMouseWheel))
			slot_window.Show()
			self.slot_window = slot_window

		def _Slot(self, position):
			"""The engine slot of a cell of the packed grid (packed at self.columns, the engine grid is
			GRID_COLUMNS wide, so a tall item still covers the slots under it)."""
			row, column = divmod(position, self.columns)
			return row * self.GRID_COLUMNS + column

		def SetForm(self, form, width):
			"""Into (form) or out of (None) the unified target form; ``width`` = the form's inner width."""
			self.form = form
			if form is None:
				self.formWidth = 0
				self.SetColumns(self.GRID_COLUMNS)
				return
			self.SetFormWidth(width)

		def SetFormWidth(self, width):
			self.formWidth = int(width)
			self.SetColumns(max(1, min(self.GRID_COLUMNS, (self.formWidth - 2 * self.form.SIDE) // self.SLOT_SIZE)))

		def SetColumns(self, columns):
			"""Re-packs the drops at ``columns`` (the form's width); nothing when the same."""
			columns = max(1, min(self.GRID_COLUMNS, int(columns)))
			if columns == self.columns:
				if self.form is not None:
					self.__PlaceGrid()
				return
			self.columns = columns
			if self.drop_heights:
				self.pages = PackDropGridPages(self.drop_heights, self.columns, self.GRID_ROWS)
				self.page_index = min(self.page_index, len(self.pages) - 1)
				self.__RefreshSlots()

		def ContentHeight(self):
			"""The grid's height in the form (the rows of the shown page)."""
			return self.used_rows * self.SLOT_SIZE

		def DropCount(self):
			return len(self.drop_items)

		def IsOpen(self):
			return self.opened

		def SetSize(self, width, height):
			ui.Window.SetSize(self, width, height)
			self.chrome.SetSize(width, height)
			r1look = getattr(self, "r1look", None)
			if r1look is not None:
				r1look.Layout(width, height)

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
			# Presentation order only (equipment, costumes, books, materials, consumables, rest); the grouped
			# spirit stone slot sorts by its first stone. PackDropGridPages then fills the grid row by row.
			return dropsort.SortDrops(display_drops, item, self.race_vnum,
				lambda entry: (entry["vnum"], entry["frames"][0][2]))

		def __LoadDrops(self):
			(_page_count, drop_list) = nonplayer.GetMonsterItemDrop(self.race_vnum)
			self.drop_items = self.__BuildDisplayDrops(drop_list)
			heights = []
			for entry in self.drop_items:
				item.SelectItem(entry["vnum"])
				heights.append(item.GetItemSize()[1])
			self.drop_heights = heights
			self.pages = PackDropGridPages(heights, self.columns, self.GRID_ROWS)
			self.ResetScroll()

		def __RefreshSlots(self):
			self.__OnOverOutSlot()
			for slot_number in range(self.GRID_SIZE):
				self.slot_window.ClearSlot(slot_number)
				self.slot_window.HideSlotBaseImage(slot_number)
			occupied, columns, rows = GetDropPageFootprint(
				self.pages[self.page_index], self.drop_heights, self.columns, self.GRID_ROWS
			)
			for position in occupied:
				self.slot_window.ShowSlotBaseImage(self._Slot(position))
			self.used_columns, self.used_rows = columns, rows
			self.slot_window.SetSize(columns * self.SLOT_SIZE, rows * self.SLOT_SIZE)
			if self.form is None:
				self.SetSize(self.GRID_X * 2 + columns * self.SLOT_SIZE,
					self.GRID_Y * 2 + rows * self.SLOT_SIZE)
			else:
				self.__PlaceGrid()
			self.visible_slot_items = {}
			self.stone_cycles = {}
			self.slot_columns = {}
			for position, index in self.pages[self.page_index]:
				slot_number = self._Slot(position)
				frames = self.drop_items[index]["frames"]
				vnum, _icon_path, count = frames[0]
				self.slot_columns[slot_number] = position % self.columns
				if self.cascade is None or self.slot_columns[slot_number] < self.cascade[1]:
					self.slot_window.SetItemSlot(slot_number, vnum, count)
				self.visible_slot_items[slot_number] = vnum
				if len(frames) > 1:
					self.stone_cycles[slot_number] = frames
			self.stone_frame_index = 0
			self.stone_next_time = app.GetTime() + self.STONE_FRAME_DURATION
			self.slot_window.RefreshSlot()
			if self.IsShow() and self.owner:
				self.owner.UpdatePosition()

		def __PlaceGrid(self):
			"""In the form: as wide as the form, as high as the grid, the grid in the middle (no margins: the
			section's heading and padding belong to the form)."""
			width = max(self.formWidth, self.used_columns * self.SLOT_SIZE)
			ui.Window.SetSize(self, width, self.used_rows * self.SLOT_SIZE)
			self.chrome.SetSize(width, self.used_rows * self.SLOT_SIZE)
			self.slot_window.SetPosition((width - self.used_columns * self.SLOT_SIZE) // 2, 0)

		# ------------------------------------------------------------------ the icon cascade (form only)
		def StartCascade(self, clock):
			"""The icons come in column after column (uir1motion: from 40 % of the unroll, 25 ms apart); the slot
			C cells are there from the start (the engine slot has no alpha for an icon, so a column appears whole)."""
			self.cascade = (clock, 0)
			for slot_number in self.visible_slot_items:
				self.slot_window.ClearSlot(slot_number)
			self.slot_window.RefreshSlot()
			self.StepCascade()

		def StepCascade(self):
			"""Shows the columns that are due; False when the cascade is over (or there is none)."""
			if self.cascade is None:
				return False
			import uir1motion
			clock, shown = self.cascade
			columns = self.used_columns
			due = uir1motion.CascadeDue(clock.elapsed, columns)
			if due != shown:
				for slot_number, vnum in self.visible_slot_items.items():
					column = self.slot_columns.get(slot_number, 0)
					if shown <= column < due:
						frames = self.stone_cycles.get(slot_number)
						count = frames[self.stone_frame_index % len(frames)][2] if frames else self.__CountOf(slot_number)
						self.slot_window.SetItemSlot(slot_number, vnum, count)
				self.slot_window.RefreshSlot()
				self.cascade = (clock, due)
			if due >= columns:
				self.cascade = None
				self.stone_next_time = app.GetTime() + self.STONE_FRAME_DURATION
				return False
			return True

		def FinishCascade(self):
			if self.cascade is not None:
				clock, shown = self.cascade
				clock.elapsed = 1e9
				self.StepCascade()

		def __CountOf(self, slot_number):
			for position, index in self.pages[self.page_index]:
				if self._Slot(position) == slot_number:
					return self.drop_items[index]["frames"][0][2]
			return 1

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
				if IsDropLevelGap(self.race_vnum):
					self.tooltip_item.AppendSpace(5)
					self.tooltip_item.AppendTextLineDontCheckColor(DROP_LEVEL_GAP_NOTE,
						self.tooltip_item.NEGATIVE_COLOR)

		def __OnOverOutSlot(self):
			self.hover_slot = None
			self.tooltip_item.HideToolTip()

		def OnUpdate(self):
			if self.cascade is not None:
				return                # the form reveals the columns; the stones cycle after the cascade
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
			if self.form is not None:
				return                # a section of the form: the form places it
			if self.owner:
				parent_x, parent_y = self.owner.GetGlobalPosition()
				panel_x = parent_x + (self.owner.GetWidth() - self.GetWidth()) // 2
				self.SetPosition(panel_x, parent_y + self.owner.GetHeight() + self.owner.DETAILS_PANEL_GAP)

		def Open(self, race_vnum):
			same = self.IsShow() and self.race_vnum == race_vnum and self.form is not None
			self.race_vnum = race_vnum
			self.opened = True
			if not same:              # a re-open while the section collapses keeps its icons (it turns back)
				self.cascade = None
				self.Refresh()
			self.UpdateAutoY()
			if self.form is None:
				self.SetTop()
			self.Show()

		def Toggle(self, race_vnum):
			if self.opened and self.race_vnum == race_vnum:
				self.Close()
				return False
			self.Open(race_vnum)
			return True

		def Close(self):
			self.__OnOverOutSlot()
			self.opened = False
			if self.form is not None:
				# the form collapses the section with the icons still in it and hides the panel at its end
				# (FormHide); the page goes back to the first one then
				if self.owner:
					self.owner.OnTargetDetailsPanelClosed()
				return
			self.ResetScroll()
			self.Hide()
			if self.owner:
				self.owner.OnTargetDetailsPanelClosed()

		def FormHide(self):
			"""The form collapsed the section: the panel hides, back on its first page."""
			self.cascade = None
			if self.opened:
				return
			self.Hide()               # first: the page reset below then does not re-place the board
			self.ResetScroll()

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
		# The base constructor calls Hide before child widgets are built.
		self.monsterIndicators = None
		self.form = None            # the unified target form (uitargetform, R1 variant A); None = separate boxes
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
		# R1 look (uitargetr1): its frame is made here, under everything else; None = the original look.
		self.r1look = uitargetr1.Begin(self)

		if ENABLE_DPS_METER:
			dpsMeter = uiDpsMeter.DpsMeterPanel()
			dpsMeter.SetParent(self)
			dpsMeter.SetExpireEvent(ui.__mem_func__(self.UpdatePosition))
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

		if self.r1look is not None:
			# Swaps in the R1 buttons (same event API) before the events below are bound; None = original look.
			self.r1look = self.r1look.Finish()
		if self.r1look is not None:
			# R1: the board, its drop panel ("Kořist") and the DPS table are ONE form in one frame (variant A of
			# 9. 10. 2026); None after a failure (traced): the three boxes as before
			self.form = uitargetr1.MakeForm(self)

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
		self.buttonDict[localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY].SAFE_SetEvent(self.__OnRequestParty)
		self.buttonDict[localeInfo.TARGET_BUTTON_BUILDING_DESTROY].SAFE_SetEvent(self.__OnDestroyBuilding)
		self.buttonDict[localeInfo.TARGET_BUTTON_EMOTION_ALLOW].SAFE_SetEvent(self.__OnEmotionAllow)
		if app.ENABLE_MESSENGER_BLOCK:
			self.buttonDict[localeInfo.TARGET_BUTTON_BLOCK].SAFE_SetEvent(self.__OnBlock)
			self.buttonDict[localeInfo.TARGET_BUTTON_BLOCK_REMOVE].SAFE_SetEvent(self.__OnBlockRemove)

		self.buttonDict["VOTE_BLOCK_CHAT"].SetEvent(ui.__mem_func__(self.__OnVoteBlockChat))

		self.monsterIndicators = uimonsterindicators.MonsterIndicators()
		self.__Initialize()
		self.ResetTargetBoard()

	def __del__(self):
		ui.Window.__del__(self)

		print("===================================================== DESTROYED TARGET BOARD")

	def SetSize(self, width, height):
		r1look = getattr(self, "r1look", None)
		if r1look is not None:
			width = r1look.FitWidth(width, height)
			height = r1look.FitHeight(height)
		form = getattr(self, "form", None)
		if form is not None:
			# a monster's form keeps one width in every state (closed, Kořist, DPS, both): at least the table's
			width = max(width, form.MinBoardWidth())
		elif ENABLE_DPS_METER and getattr(self, "dpsMeter", None):
			# the DPS table and the board are one block: the board is at least as wide as the shown table
			width = max(width, self.dpsMeter.BoardWidth(self.TARGET_CHROME_SIDE_INSET))
		ui.Window.SetSize(self, width, height)
		self.chrome.SetSize(width - self.TARGET_CHROME_SIDE_INSET * 2, height)
		r1look = getattr(self, "r1look", None)
		if r1look is not None:
			r1look.Layout(width, height)

	def __Initialize(self):
		if self.monsterIndicators:
			self.monsterIndicators.Hide()
			self.monsterIndicators.monsterVnum = None
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
		if self.monsterIndicators:
			self.monsterIndicators.Hide()
		self.__CloseTargetDetailsPanel()
		form = getattr(self, "form", None)
		if form is not None:
			form.Reset()
		ui.Window.Hide(self)

	def Show(self):
		ui.Window.Show(self)
		form = getattr(self, "form", None)
		if form is not None:
			form.Sync()

	def Destroy(self):
		self.__CloseTargetDetailsPanel()
		if self.form is not None:
			self.form.Destroy()
			self.form = None
		self.__Initialize()
		if self.monsterIndicators:
			self.monsterIndicators.Destroy()
			self.monsterIndicators = None

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
				self.target_details_thinboard.owner = None
			self.target_details_thinboard = None
			self.target_details_button = None

		self.closeButton = None
		self.buttonDict = None
		self.showingButtonList = None
		self.r1look = None

		if app.ENABLE_ELEMENT_ADD:
			self.elementImgList = None
			self.element_enchants_dict = {}

	if app.ENABLE_SEND_TARGET_INFO:
		def RefreshMonsterInfoBoard(self, raceNum):
			# RefreshMonsterDropInfo follows the TARGET_INFO drop rows and can
			# arrive after the panel opened. The attached panel is the only drop
			# preview; TargetBoard never builds the legacy MobItemDropWindow.
			if int(raceNum) != self.race_vnum:
				return
			panel = getattr(self, "target_details_thinboard", None)
			if panel and panel.IsShow():
				panel.Refresh()

		def OnTargetDetailsPanelClosed(self):
			self.__SetTargetDetailsButtonState(False)
			if app.ENABLE_ELEMENT_ADD:
				self.ShowElementImg(self.element_enchants_dict)
			self.UpdatePosition()

		def __SetTargetDetailsButtonState(self, active):
			visual = "local_target_board/toggle/active.png" if active else "local_target_board/toggle/inactive.png"
			r1look = getattr(self, "r1look", None)
			if r1look is not None:
				visual = r1look.DetailsVisual(active, visual)
			self.target_details_button.LoadImage(visual)
			self.target_details_button.SetScale(self.TARGET_DETAILS_ICON_SCALE, self.TARGET_DETAILS_ICON_SCALE)

		def __UpdateTargetDetailsButtonPosition(self):
			if not self.target_details_button:
				return
			r1look = getattr(self, "r1look", None)
			if r1look is not None and r1look.PlacePair():
				return                # R1: "?" and "DPS" centred between the name and the HP block

			name_x, name_y = self.name.GetGlobalPosition()
			board_x, board_y = self.GetGlobalPosition()
			text_width, text_height = self.name.GetTextSize()
			if not self.hpGauge.IsShow():
				name_x -= text_width // 2
			icon_height = self.TARGET_DETAILS_ICON_SIZE
			icon_x = name_x - board_x + text_width + self.TARGET_DETAILS_ICON_GAP
			r1look = getattr(self, "r1look", None)
			if r1look is not None:
				icon_x += r1look.InfoRoom()      # after the element and race icons
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

		if self.form is not None:
			self.form.Reset()
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
		r1look = getattr(self, "r1look", None)
		if r1look is not None:
			r1look.Refit()
		if self.form is None and ENABLE_DPS_METER and self.dpsMeter and \
				self.GetWidth() < self.dpsMeter.BoardWidth(self.TARGET_CHROME_SIDE_INSET):
			self.SetSize(self.GetWidth(), self.GetHeight())
		elif self.form is not None and self.GetWidth() < self.form.MinBoardWidth():
			self.SetSize(self.GetWidth(), self.GetHeight())
		self.SetPosition(wndMgr.GetScreenWidth() // 2 - self.GetWidth() // 2, 10)
		if app.ENABLE_SEND_TARGET_INFO:
			self.__UpdateTargetDetailsButtonPosition()
		if app.ENABLE_ELEMENT_ADD:
			self.AdjustPositionElementImage()

		if app.ENABLE_AUTO_FARM_METIN:
			if chr.GetInstanceType(self.vid) == chr.INSTANCE_TYPE_STONE and self.form is not None:
				# the unified form: the queue hint is a line of the Kořist section (shown with "?"), the header
				# stays 38 px like any monster's
				self.autoFarmText.Hide()
			elif chr.GetInstanceType(self.vid) == chr.INSTANCE_TYPE_STONE:
				self.SetSize(self.GetWidth(), self.METIN_TARGET_HEIGHT)

				self.__RefreshMetinQueueText()
				self.autoFarmText.SetPosition(self.GetWidth() // 2, self.METIN_QUEUE_ROW_Y)
				self.autoFarmText.Show()
			else:
				self.autoFarmText.Hide()

		self.__RefreshMonsterIndicators()

		if self.form is not None:
			# one form: the sections (Kořist, DPS) unroll under the header inside the board's frame
			self.form.Sync()
			return

		if app.ENABLE_SEND_TARGET_INFO and self.target_details_thinboard and self.target_details_thinboard.IsShow():
			self.target_details_thinboard.UpdateAutoY()

		if ENABLE_DPS_METER and self.dpsMeter:
			details_height = 0
			if app.ENABLE_SEND_TARGET_INFO and self.target_details_thinboard.IsShow():
				details_height = self.DETAILS_PANEL_GAP + self.target_details_thinboard.GetHeight()
			# as wide as the board's frame, DETAILS_PANEL_GAP under the board (or under the open drop panel)
			self.dpsMeter.SetBlockWidth(self.GetWidth() - 2 * self.TARGET_CHROME_SIDE_INSET)
			self.dpsMeter.SetPosition(
				self.TARGET_CHROME_SIDE_INSET,
				self.GetHeight() + max(details_height, self.monsterIndicators.GetHeight() if self.monsterIndicators.IsShow() else 0) + self.DETAILS_PANEL_GAP,
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

		if self.form is not None:
			self.form.Reset()          # another target: no animation, the new one starts closed
		self.SetSize(250, 40)

	if ENABLE_DPS_METER:
		def ApplyDpsMeterSnapshot(self, victimVid, encounterId, flags, totalDamage, rows):
			if not uiDpsMeter.IsEnabled():
				return                # Settings: "Ukazatel poškození (DPS)" off - the snapshot is dropped at once
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

		self.__RefreshMonsterIndicators()

	def GetTargetElements(self):
		if getattr(self, "element_enchants_vid", 0) == self.vid:
			return getattr(self, "element_enchants_dict", None)
		return None

	def __RefreshMonsterIndicators(self):
		if not self.monsterIndicators:
			return
		# R1: the element and race icons sit in the header after the name (uitargetr1, variant B of 9. 10. 2026)
		r1look = getattr(self, "r1look", None)
		monster = self.vid and chr.GetInstanceType(self.vid) in (chr.INSTANCE_TYPE_ENEMY, chr.INSTANCE_TYPE_STONE)
		if r1look is not None and r1look.ShowTargetInfo(nonplayer.GetRaceByVID(self.vid) if monster else 0):
			self.monsterIndicators.Hide()
			return
		if not self.vid or chr.GetInstanceType(self.vid) not in (chr.INSTANCE_TYPE_ENEMY, chr.INSTANCE_TYPE_STONE):
			self.monsterIndicators.Hide()
			return
		if app.ENABLE_SEND_TARGET_INFO and self.target_details_thinboard and self.target_details_thinboard.IsShow():
			self.monsterIndicators.Hide()
			return
		width = self.monsterIndicators.SetMonster(nonplayer.GetRaceByVID(self.vid), liveElements=self.GetTargetElements())
		if not width:
			self.monsterIndicators.Hide()
			return
		x, y = self.GetGlobalPosition()
		self.monsterIndicators.SetPosition(x, y + self.GetHeight() + 2)
		self.monsterIndicators.SetTop()
		self.monsterIndicators.Show()

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
				r1look = getattr(self, "r1look", None)
				if r1look is not None:
					r1look.PlaceHp()
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

		r1look = getattr(self, "r1look", None)
		if r1look is None or not r1look.ArrangeButtons():
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
		if self.form is not None:
			self.form.Update()         # the sections' unroll (nothing to do at rest)
			self.form.RefreshQueue()   # the meteor queue numbers of the hint line (only while it is shown)

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
			self.__RefreshMonsterIndicators()

		def ShowElementImg(self, element_enchants_dict):
			self.element_enchants_dict = dict(element_enchants_dict)
			self.element_enchants_vid = self.vid
			self.__RefreshMonsterIndicators()

		def __HideAllElementImg(self):
			self.monsterIndicators.Hide()
