import math
import time

import item
import localeInfo
import nonplayer
import player
import ui
import uiScriptLocale
import uiToolTip
import wndMgr

import droptrackermodel


PUBLIC_PATH = "d:/ymir work/ui/public/"

COLOR_TEXT = 0xffe5e1d8
COLOR_MUTED = 0xff9b978f
COLOR_GOLD = 0xffffd36b
COLOR_GREEN = 0xff8ac28f
COLOR_RED = 0xffd69a72
COLOR_SOURCE = 0xffb7ad99

COMPACT_DROP_COUNT = 5
COMPACT_SOURCE_COUNT = 3
DETAIL_ROW_COUNT = 10
TASKBAR_ICON_SIZE = 32
TASKBAR_ICON_GAP = 2
TASKBAR_MAX_ICONS = 24
TASKBAR_FADE_SECONDS = 1.5
FLOATING_GRIP_WIDTH = 14
FLOATING_SCREEN_MARGIN = 4
FLOATING_TASKBAR_GAP = 4
FLOATING_PREVIEW_WIDTH = 132
FLOATING_EDIT_SECONDS = 15.0


def _Locale(key, fallback):
	return getattr(
		uiScriptLocale, key, getattr(localeInfo, key, fallback)
	)


def _SetButtonText(button, text):
	if button.GetText() != text:
		button.SetText(text)


def _FormatNumber(value):
	try:
		return localeInfo.MoneyFormat(int(value))
	except (TypeError, ValueError):
		return str(value)


def _FormatOverlayAmount(value):
	value = max(0, int(value))
	if value < 1000:
		return str(value)
	if value < 1000000:
		scaled = float(value) / 1000.0
		return (
			"%.1fK" % scaled if scaled < 10.0 else
			"%dK" % int(scaled)
		)
	if value < 1000000000:
		scaled = float(value) / 1000000.0
		return (
			"%.1fM" % scaled if scaled < 10.0 else
			"%dM" % int(scaled)
		)
	scaled = float(value) / 1000000000.0
	return (
		"%.1fB" % scaled if scaled < 10.0 else
		"%dB" % int(scaled)
	)


def _FormatDuration(seconds):
	seconds = max(0, int(seconds))
	if seconds < 60:
		return "%d s" % seconds
	if seconds < 3600:
		return "%d min" % (seconds // 60)
	hours = seconds // 3600
	minutes = (seconds % 3600) // 60
	if hours < 24:
		return "%d h %02d min" % (hours, minutes)
	days = hours // 24
	return "%d d %02d h" % (days, hours % 24)


def _ItemName(vnum):
	try:
		item.SelectItem(int(vnum))
		return item.GetItemName()
	except:
		return _Locale("DROP_TRACKER_UNKNOWN_ITEM", "Item #%d") % int(vnum)


def _SourceLabels():
	return {
		droptrackermodel.SOURCE_MONSTER: _Locale(
			"DROP_TRACKER_MONSTER", "Monster"
		),
		droptrackermodel.SOURCE_METIN: _Locale(
			"DROP_TRACKER_METIN", "Meteor"
		),
		droptrackermodel.SOURCE_BOSS: _Locale(
			"DROP_TRACKER_BOSS", "Boss"
		),
		droptrackermodel.SOURCE_CHEST: _Locale(
			"DROP_TRACKER_CHEST", "Chest"
		),
	}


def _SourceName(sourceType, sourceVnum):
	if sourceType == droptrackermodel.SOURCE_CHEST:
		# A chest source is the chest item itself.
		return _ItemName(sourceVnum)
	try:
		name = nonplayer.GetMonsterName(int(sourceVnum))
		if name:
			return name
	except:
		pass
	return "%s #%d" % (
		_SourceLabels().get(
			sourceType, _Locale("DROP_TRACKER_UNKNOWN_SOURCE", "Unknown")
		),
		int(sourceVnum),
	)


def _ElapsedText(timestamp, now):
	seconds = max(0, int(now - float(timestamp)))
	if seconds < 60:
		return _Locale("DROP_TRACKER_SECONDS_AGO", "%d s") % seconds
	if seconds < 3600:
		return _Locale("DROP_TRACKER_MINUTES_AGO", "%d min") % (
			seconds // 60
		)
	if seconds < 86400:
		return _Locale("DROP_TRACKER_HOURS_AGO", "%d h") % (
			seconds // 3600
		)
	return _Locale("DROP_TRACKER_DAYS_AGO", "%d d") % (
		seconds // 86400
	)


def _ColorWithAlpha(color, alpha):
	alphaByte = max(0, min(255, int(float(alpha) * 255.0)))
	return (alphaByte << 24) | (int(color) & 0x00ffffff)


def _MakeText(
	parent, x, y, text="", centered=False, right=False,
	color=COLOR_TEXT,
):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	if centered:
		line.SetHorizontalAlignCenter()
	elif right:
		line.SetHorizontalAlignRight()
	line.SetPackedFontColor(color)
	line.SetText(text)
	line.Show()
	return line


def _MakeButton(parent, x, y, text, event, *args):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual(PUBLIC_PATH + "small_thin_button_01.sub")
	button.SetOverVisual(PUBLIC_PATH + "small_thin_button_02.sub")
	button.SetDownVisual(PUBLIC_PATH + "small_thin_button_03.sub")
	button.SetText(text)
	button.SetEvent(event, *args)
	button.Show()
	return button


def _MakeMiddleButton(parent, x, y, text, event, *args):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual(PUBLIC_PATH + "middle_button_01.sub")
	button.SetOverVisual(PUBLIC_PATH + "middle_button_02.sub")
	button.SetDownVisual(PUBLIC_PATH + "middle_button_03.sub")
	button.SetText(text)
	button.SetEvent(event, *args)
	button.Show()
	return button


def _MakePanel(parent, x, y, width, height):
	panel = ui.ThinBoard()
	panel.SetParent(parent)
	panel.SetPosition(x, y)
	panel.SetSize(width, height)
	panel.Show()
	return panel


def _LoadItemIcon(image, vnum, maxSize=30):
	"""Load an item into a normalized square footprint."""
	try:
		vnum = int(vnum)
		item.SelectItem(vnum)
		path = item.GetIconImageFileName()
		image.LoadImage(path)
		width = max(1, int(image.GetWidth()))
		height = max(1, int(image.GetHeight()))
		scale = min(
			1.0,
			float(maxSize) / float(width),
			float(maxSize) / float(height),
		)
		image.SetScale(scale, scale)
		image.SetAlpha(1.0)
		image.Show()
		return (
			max(1, int(width * scale)),
			max(1, int(height * scale)),
		)
	except:
		image.Hide()
		return (0, 0)


class KpiCard(object):
	def __init__(self, parent, x, title):
		self.panel = _MakePanel(parent, x, 58, 198, 57)
		self.title = _MakeText(
			self.panel, 99, 9, title, centered=True, color=COLOR_MUTED
		)
		self.value = _MakeText(
			self.panel, 99, 29, "0", centered=True, color=COLOR_GOLD
		)

	def SetValue(self, value):
		self.value.SetText(value)

	def Show(self):
		self.panel.Show()

	def Hide(self):
		self.panel.Hide()


class CompactDropRow(object):
	def __init__(self, owner, parent, rowIndex):
		self.owner = owner
		self.data = None
		self.panel = _MakePanel(
			parent, 12, 143 + rowIndex * 37, 406, 34
		)
		self.panel.OnMouseLeftButtonUp = ui.__mem_func__(
			self._OnLeftClick
		)
		self.panel.OnMouseRightButtonUp = ui.__mem_func__(
			self._OnRightClick
		)

		self.icon = ui.ImageBox()
		self.icon.SetParent(self.panel)
		self.icon.SetPosition(10, 2)
		self.icon.OnMouseOverIn = ui.__mem_func__(self._ShowToolTip)
		self.icon.OnMouseOverOut = ui.__mem_func__(self._HideToolTip)
		self.icon.Show()

		self.name = _MakeText(self.panel, 52, 5)
		self.name.SetLimitWidth(225)
		self.source = _MakeText(
			self.panel, 52, 19, color=COLOR_SOURCE
		)
		self.source.SetLimitWidth(265)
		self.amount = _MakeText(
			self.panel, 390, 10, right=True, color=COLOR_GOLD
		)
		self.panel.Hide()

	def SetData(self, data):
		self.data = data
		vnum = int(data["item_vnum"])
		_, iconHeight = _LoadItemIcon(self.icon, vnum, 28)
		self.icon.SetPosition(10, max(2, (34 - iconHeight) // 2))
		self.name.SetText(_ItemName(vnum))
		if data.get("source_count", 1) > 1:
			sourceText = _Locale(
				"DROP_TRACKER_SOURCE_COUNT", "%d sources"
			) % data["source_count"]
		else:
			sourceText = _SourceName(
				data["source_type"], data["source_vnum"]
			)
		self.source.SetText(sourceText)
		self.amount.SetText("+%s" % _FormatNumber(data["amount"]))
		self.panel.Show()

	def Clear(self):
		self.data = None
		self.panel.Hide()

	def _OnLeftClick(self):
		if self.data:
			self.owner.OpenDetailsForItem(self.data["item_vnum"])

	def _OnRightClick(self):
		if self.data:
			self.owner.ToggleBlacklist(self.data["item_vnum"])

	def _ShowToolTip(self):
		if self.data:
			self.owner.ShowItemToolTip(self.data["item_vnum"])

	def _HideToolTip(self):
		self.owner.HideItemToolTip()


class CompactSourceRow(object):
	def __init__(self, parent, rowIndex):
		y = 356 + rowIndex * 23
		self.rank = _MakeText(
			parent, 18, y, "#%d" % (rowIndex + 1), color=COLOR_MUTED
		)
		self.name = _MakeText(parent, 48, y)
		self.name.SetLimitWidth(220)
		self.meta = _MakeText(
			parent, 414, y, right=True, color=COLOR_SOURCE
		)
		self.Hide()

	def SetData(self, data):
		self.name.SetText(_SourceName(
			data["source_type"], data["source_vnum"]
		))
		self.meta.SetText(
			_Locale(
				"DROP_TRACKER_SOURCE_META",
				"%s items | %s kills",
			) % (
				_FormatNumber(data["items"]),
				_FormatNumber(data["kills"]),
			)
		)
		self.Show()

	def Show(self):
		self.rank.Show()
		self.name.Show()
		self.meta.Show()

	def Hide(self):
		self.rank.Hide()
		self.name.Hide()
		self.meta.Hide()


class DetailDropRow(object):
	def __init__(self, owner, parent, rowIndex):
		self.owner = owner
		self.data = None
		self.panel = _MakePanel(
			parent, 10, 125 + rowIndex * 32, 740, 30
		)
		self.panel.OnMouseLeftButtonUp = ui.__mem_func__(
			self._OnLeftClick
		)
		self.panel.OnMouseRightButtonUp = ui.__mem_func__(
			self._OnRightClick
		)

		self.icon = ui.ImageBox()
		self.icon.SetParent(self.panel)
		self.icon.SetPosition(8, 1)
		self.icon.OnMouseOverIn = ui.__mem_func__(self._ShowToolTip)
		self.icon.OnMouseOverOut = ui.__mem_func__(self._HideToolTip)
		self.icon.Show()

		self.name = _MakeText(self.panel, 43, 8)
		self.name.SetLimitWidth(295)
		self.source = _MakeText(
			self.panel, 400, 8, centered=True, color=COLOR_SOURCE
		)
		self.source.SetLimitWidth(245)
		self.amount = _MakeText(
			self.panel, 615, 8, centered=True, color=COLOR_GOLD
		)
		self.age = _MakeText(
			self.panel, 705, 8, centered=True, color=COLOR_MUTED
		)
		self.panel.Hide()

	def SetData(self, data, now):
		self.data = data
		vnum = int(data["item_vnum"])
		isChild = bool(data.get("is_source_child"))
		if isChild:
			self.icon.Hide()
			self.name.SetPosition(25, 8)
			self.name.SetPackedFontColor(COLOR_SOURCE)
			self.name.SetText("> %s" % _SourceName(
				data["source_type"], data["source_vnum"]
			))
			self.source.SetText(
				_Locale("DROP_TRACKER_SOURCE_DETAIL", "Source detail")
			)
		else:
			_, iconHeight = _LoadItemIcon(self.icon, vnum, 27)
			self.icon.SetPosition(8, max(1, (30 - iconHeight) // 2))
			self.name.SetPosition(43, 8)
			self.name.SetPackedFontColor(COLOR_TEXT)
			prefix = ""
			if (
				self.owner.model.mode == "summary" and
				data.get("source_count", 1) > 1
			):
				prefix = (
					"- " if self.owner.expandedItemVnum == vnum else "+ "
				)
			self.name.SetText(prefix + _ItemName(vnum))
			if data.get("source_count", 1) > 1:
				self.source.SetText(
					_Locale(
						"DROP_TRACKER_SOURCE_COUNT", "%d sources"
					) % data["source_count"]
				)
			else:
				self.source.SetText(_SourceName(
					data["source_type"], data["source_vnum"]
				))
		self.amount.SetText(_FormatNumber(data["amount"]))
		self.age.SetText(_ElapsedText(data["timestamp"], now))
		self.panel.Show()

	def Clear(self):
		self.data = None
		self.panel.Hide()

	def _OnLeftClick(self):
		if (
			self.data and
			not self.data.get("is_source_child") and
			self.owner.model.mode == "summary"
		):
			self.owner.ToggleItemSources(self.data)

	def _OnRightClick(self):
		if self.data:
			self.owner.ToggleBlacklist(self.data["item_vnum"])

	def _ShowToolTip(self):
		if self.data:
			self.owner.ShowItemToolTip(self.data["item_vnum"])

	def _HideToolTip(self):
		self.owner.HideItemToolTip()


class DropTrackerWindow(ui.BoardWithTitleBar):
	COMPACT_WIDTH = 430
	COMPACT_HEIGHT = 480
	DETAIL_WIDTH = 760
	DETAIL_HEIGHT = 500

	def __init__(self, system):
		ui.BoardWithTitleBar.__init__(self)
		self.system = system
		self.model = system.model
		self.compactWidgets = []
		self.detailWidgets = []
		self.advancedWidgets = []
		self.compactRows = []
		self.sourceRows = []
		self.detailRows = []
		self.lastPosition = None
		self.detailed = False
		self.showAdvanced = False
		self.showHidden = False
		self.expandedItemVnum = 0

		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.COMPACT_WIDTH, self.COMPACT_HEIGHT)
		self.SetTitleName(_Locale("DROP_TRACKER_TITLE", "Drop tracker"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()
		self._BuildCompact()
		self._BuildDetails()
		self.SetDetailed(False)
		self.Hide()

	def _BuildCompact(self):
		self.compactStatus = _MakeText(
			self, 14, 36, color=COLOR_GREEN
		)
		self.compactDuration = _MakeText(
			self, 416, 36, right=True, color=COLOR_MUTED
		)
		self.compactWidgets.extend((
			self.compactStatus, self.compactDuration,
		))

		self.kpiKills = KpiCard(
			self, 12, _Locale("DROP_TRACKER_KILLS", "Kills")
		)
		self.kpiItems = KpiCard(
			self, 220, _Locale("DROP_TRACKER_ITEMS", "Items")
		)

		self.topDropsTitle = _MakeText(
			self, 14, 124,
			_Locale("DROP_TRACKER_TOP_DROPS", "Top drops"),
			color=COLOR_GOLD,
		)
		self.compactEmpty = _MakeText(
			self, 215, 236,
			_Locale(
				"DROP_TRACKER_EMPTY",
				"No drops in the selected scope yet",
			),
			centered=True,
			color=COLOR_MUTED,
		)
		self.compactWidgets.extend((
			self.topDropsTitle, self.compactEmpty,
		))
		for rowIndex in range(COMPACT_DROP_COUNT):
			self.compactRows.append(
				CompactDropRow(self, self, rowIndex)
			)

		self.topSourcesTitle = _MakeText(
			self, 14, 337,
			_Locale("DROP_TRACKER_TOP_SOURCES", "Top sources"),
			color=COLOR_GOLD,
		)
		self.compactWidgets.append(self.topSourcesTitle)
		for rowIndex in range(COMPACT_SOURCE_COUNT):
			self.sourceRows.append(
				CompactSourceRow(self, rowIndex)
			)

		self.compactPauseButton = _MakeMiddleButton(
			self, 12, 445, "", self.TogglePause
		)
		self.resetButton = _MakeMiddleButton(
			self, 170, 445,
			_Locale("DROP_TRACKER_RESET", "Reset"),
			self.Reset,
		)
		self.detailsButton = _MakeMiddleButton(
			self, 327, 445,
			_Locale("DROP_TRACKER_OPEN_DETAILS", "Details >"),
			self.SetDetailed, True,
		)
		self.compactWidgets.extend((
			self.compactPauseButton,
			self.resetButton,
			self.detailsButton,
		))

	def _BuildDetails(self):
		self.backButton = _MakeMiddleButton(
			self, 12, 35,
			_Locale("DROP_TRACKER_BACK", "< Back"),
			self.SetDetailed, False,
		)
		self.modeSummary = _MakeMiddleButton(
			self, 103, 35,
			_Locale("DROP_TRACKER_SUMMARY", "Items"),
			self.SetMode, "summary",
		)
		self.modeLog = _MakeMiddleButton(
			self, 194, 35,
			_Locale("DROP_TRACKER_LOG", "History"),
			self.SetMode, "log",
		)
		self.filtersButton = _MakeMiddleButton(
			self, 285, 35,
			_Locale("DROP_TRACKER_FILTERS", "Filters"),
			self.ToggleAdvanced,
		)
		self.detailPauseButton = _MakeMiddleButton(
			self, 649, 35, "", self.TogglePause
		)
		self.detailWidgets.extend((
			self.backButton, self.modeSummary, self.modeLog,
			self.filtersButton, self.detailPauseButton,
		))

		self.timeButton = _MakeMiddleButton(
			self, 376, 35, "", self.CycleTimeWindow
		)
		self.sourceButton = _MakeMiddleButton(
			self, 467, 35, "", self.CycleSourceFilter
		)
		self.hiddenButton = _MakeMiddleButton(
			self, 649, 63, "", self.ToggleHidden
		)
		self.recentLifetimeButton = _MakeMiddleButton(
			self, 558, 63, "", self.CycleRecentLifetime
		)
		self.advancedWidgets.extend((
			self.timeButton, self.sourceButton,
			self.recentLifetimeButton,
			self.hiddenButton,
		))

		self.detailStatus = _MakeText(
			self, 14, 67, color=COLOR_MUTED
		)
		self.detailHint = _MakeText(
			self, 746, 67,
			_Locale(
				"DROP_TRACKER_DETAIL_HINT",
				"Left click expands sources | Right click hides",
			),
			right=True,
			color=COLOR_MUTED,
		)
		self.detailEmpty = _MakeText(
			self, 380, 269,
			_Locale(
				"DROP_TRACKER_EMPTY",
				"No drops in the selected scope yet",
			),
			centered=True,
			color=COLOR_MUTED,
		)
		self.detailWidgets.extend((
			self.detailStatus, self.detailHint, self.detailEmpty,
		))

		headers = (
			(52, _Locale("DROP_TRACKER_ITEM", "Item"), False),
			(410, _Locale("DROP_TRACKER_SOURCE", "Source"), True),
			(625, _Locale("DROP_TRACKER_AMOUNT", "Amount"), True),
			(715, _Locale("DROP_TRACKER_AGE", "Age"), True),
		)
		for x, text, centered in headers:
			header = _MakeText(
				self, x, 106, text, centered=centered,
				color=COLOR_SOURCE,
			)
			self.detailWidgets.append(header)

		for rowIndex in range(DETAIL_ROW_COUNT):
			self.detailRows.append(
				DetailDropRow(self, self, rowIndex)
			)

		self.previousButton = _MakeButton(
			self, 285, 462, "<", self.PreviousPage
		)
		self.pageText = _MakeText(
			self, 380, 467, "", centered=True, color=COLOR_MUTED
		)
		self.nextButton = _MakeButton(
			self, 412, 462, ">", self.NextPage
		)
		self.detailWidgets.extend((
			self.previousButton, self.pageText, self.nextButton,
		))

	def Open(self):
		self.SetDetailed(False)
		if self.model.window_position is not None:
			self.SetPosition(*self.model.window_position)
			self._ClampToScreen()
		else:
			self.SetCenterPosition()
		self.Show()
		self.SetTop()
		self.Refresh()

	def Close(self):
		self._RememberPosition()
		self.HideItemToolTip()
		self.Hide()
		self.model.Save()

	def Destroy(self):
		self._RememberPosition()
		self.HideItemToolTip()
		self.compactRows = []
		self.sourceRows = []
		self.detailRows = []
		self.compactWidgets = []
		self.detailWidgets = []
		self.advancedWidgets = []
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		self.system.Tick()
		self._RememberPosition()

	def SetDetailed(self, value):
		self.detailed = bool(value)
		self.showAdvanced = False
		width = (
			self.DETAIL_WIDTH if self.detailed else self.COMPACT_WIDTH
		)
		height = (
			self.DETAIL_HEIGHT if self.detailed else self.COMPACT_HEIGHT
		)
		self.SetSize(width, height)
		for widget in self.compactWidgets:
			widget.Hide()
		for card in (self.kpiKills, self.kpiItems):
			card.Hide()
		for row in self.compactRows:
			row.panel.Hide()
		for row in self.sourceRows:
			row.Hide()
		for widget in self.detailWidgets:
			widget.Hide()
		for widget in self.advancedWidgets:
			widget.Hide()
		for row in self.detailRows:
			row.panel.Hide()

		if self.detailed:
			for widget in self.detailWidgets:
				widget.Show()
		else:
			for widget in self.compactWidgets:
				widget.Show()
			for card in (self.kpiKills, self.kpiItems):
				card.Show()
		self._ClampToScreen()
		if self.IsShow():
			self.Refresh()

	def OpenDetailsForItem(self, itemVnum):
		self.expandedItemVnum = int(itemVnum)
		self.model.SetMode("summary")
		self.model.page = 0
		self.SetDetailed(True)

	def ToggleAdvanced(self):
		self.showAdvanced = not self.showAdvanced
		self.Refresh()

	def Refresh(self):
		now = time.time()
		if self.detailed:
			self._RefreshDetails(now)
		else:
			self._RefreshCompact(now)
		self._RefreshControls()

	def _RefreshCompact(self, now):
		stats = self.model.GetStats(now)
		self.compactStatus.SetText(self._RecordingState())
		self.compactStatus.SetPackedFontColor(
			COLOR_RED if self.model.paused else COLOR_GREEN
		)
		self.compactDuration.SetText(
			_Locale("DROP_TRACKER_SESSION", "Session %s") %
			_FormatDuration(self.model.GetSessionDuration(now))
		)
		self.kpiKills.SetValue(_FormatNumber(stats["kills"]))
		self.kpiItems.SetValue(_FormatNumber(stats["items"]))

		drops = self.model.GetItemSummary(now)
		if drops:
			self.compactEmpty.Hide()
		else:
			self.compactEmpty.Show()
		for index, row in enumerate(self.compactRows):
			if index < len(drops):
				row.SetData(drops[index])
			else:
				row.Clear()

		sources = self.model.GetSourceSummary(now)
		for index, row in enumerate(self.sourceRows):
			if index < len(sources):
				row.SetData(sources[index])
			else:
				row.Hide()

	def _RefreshDetails(self, now):
		rows = self._CurrentDetailRows(now)
		if rows:
			self.detailEmpty.Hide()
		else:
			self.detailEmpty.Show()
		pageCount = max(1, int(math.ceil(
			float(len(rows)) / float(DETAIL_ROW_COUNT)
		)))
		self.model.page = max(0, min(self.model.page, pageCount - 1))
		start = self.model.page * DETAIL_ROW_COUNT
		pageRows = rows[start:start + DETAIL_ROW_COUNT]
		for index, row in enumerate(self.detailRows):
			if index < len(pageRows):
				row.SetData(pageRows[index], now)
			else:
				row.Clear()

		self.pageText.SetText(
			_Locale("DROP_TRACKER_PAGE", "Page %d / %d") % (
				self.model.page + 1, pageCount
			)
		)
		stats = self.model.GetStats(now)
		self.detailStatus.SetText(
			_Locale(
				"DROP_TRACKER_DETAIL_ITEMS_STATUS",
				"%s | %s kills | %s items",
			) % (
				self._RecordingState(),
				_FormatNumber(stats["kills"]),
				_FormatNumber(stats["items"]),
			)
		)
		if self.showAdvanced:
			self.detailHint.Hide()
		else:
			self.detailHint.Show()
		for widget in self.advancedWidgets:
			if self.showAdvanced:
				widget.Show()
			else:
				widget.Hide()

	def _RecordingState(self):
		if not self.system.available:
			return _Locale("DROP_TRACKER_UNAVAILABLE", "Unavailable")
		if self.model.paused:
			state = _Locale("DROP_TRACKER_PAUSED", "Paused")
		else:
			state = _Locale("DROP_TRACKER_RECORDING", "Recording")
		scope = self._ScopeText()
		return state if not scope else "%s | %s" % (state, scope)

	def _ScopeText(self):
		parts = []
		if self.model.time_window:
			parts.append("%d min" % (self.model.time_window // 60))
		sourceLabels = _SourceLabels()
		if self.model.source_filter in sourceLabels:
			parts.append(sourceLabels[self.model.source_filter])
		return " | ".join(parts)

	def _RefreshControls(self):
		_SetButtonText(self.compactPauseButton,
			_Locale("DROP_TRACKER_RESUME", "Resume")
			if self.model.paused else
			_Locale("DROP_TRACKER_PAUSE", "Pause")
		)
		_SetButtonText(self.detailPauseButton,
			_Locale("DROP_TRACKER_RESUME", "Resume")
			if self.model.paused else
			_Locale("DROP_TRACKER_PAUSE", "Pause")
		)
		_SetButtonText(self.modeSummary,
			("* " if self.model.mode == "summary" else "") +
			_Locale("DROP_TRACKER_SUMMARY", "Items")
		)
		_SetButtonText(self.modeLog,
			("* " if self.model.mode == "log" else "") +
			_Locale("DROP_TRACKER_LOG", "History")
		)
		_SetButtonText(self.filtersButton,
			_Locale("DROP_TRACKER_FILTERS_CLOSE", "Close filters")
			if self.showAdvanced else
			_Locale("DROP_TRACKER_FILTERS", "Filters")
		)
		timeLabels = {
			0: _Locale("DROP_TRACKER_TIME_ALL", "All time"),
			300: "5 min",
			900: "15 min",
			1800: "30 min",
			3600: "60 min",
		}
		sourceLabels = _SourceLabels()
		sourceLabels[droptrackermodel.SOURCE_UNKNOWN] = _Locale(
			"DROP_TRACKER_SOURCE_ALL", "All sources"
		)
		_SetButtonText(
			self.timeButton, timeLabels[self.model.time_window]
		)
		_SetButtonText(
			self.sourceButton, sourceLabels[self.model.source_filter]
		)
		_SetButtonText(self.hiddenButton,
			_Locale("DROP_TRACKER_BACK", "Visible items")
			if self.showHidden else
			_Locale("DROP_TRACKER_HIDDEN", "Hidden (%d)") %
			len(self.model.blacklist - {1})
		)
		if self.model.recent_lifetime:
			recentLifetimeText = _Locale(
				"DROP_TRACKER_ICON_LIFETIME", "Icons: %d s"
			) % self.model.recent_lifetime
		else:
			recentLifetimeText = _Locale(
				"DROP_TRACKER_ICON_LIFETIME_ALWAYS", "Icons: always"
			)
		_SetButtonText(self.recentLifetimeButton, recentLifetimeText)

	def SetMode(self, mode):
		self.expandedItemVnum = 0
		self.model.SetMode(mode)
		self.Refresh()

	def CycleTimeWindow(self):
		self.expandedItemVnum = 0
		self.model.CycleTimeWindow()
		self.Refresh()

	def CycleSourceFilter(self):
		self.expandedItemVnum = 0
		self.model.CycleSourceFilter()
		self.Refresh()

	def CycleRecentLifetime(self):
		self.model.CycleRecentLifetime()
		self.Refresh()
		self.system.RefreshRecent()

	def TogglePause(self):
		self.model.SetPaused(not self.model.paused)
		self.Refresh()

	def Reset(self):
		self.expandedItemVnum = 0
		self.model.Clear()
		self.Refresh()
		self.system.RefreshRecent()

	def ToggleHidden(self):
		self.showHidden = not self.showHidden
		self.expandedItemVnum = 0
		self.model.page = 0
		self.Refresh()

	def ToggleItemSources(self, data):
		if data.get("source_count", 1) <= 1:
			return
		vnum = int(data["item_vnum"])
		self.expandedItemVnum = (
			0 if self.expandedItemVnum == vnum else vnum
		)
		self.model.page = 0
		self.Refresh()

	def PreviousPage(self):
		self.model.page = max(0, self.model.page - 1)
		self.Refresh()

	def NextPage(self):
		pageCount = max(1, int(math.ceil(
			float(len(self._CurrentDetailRows(time.time()))) /
			float(DETAIL_ROW_COUNT)
		)))
		self.model.page = min(pageCount - 1, self.model.page + 1)
		self.Refresh()

	def ToggleBlacklist(self, itemVnum):
		self.model.ToggleBlacklist(itemVnum)
		self.expandedItemVnum = 0
		self.Refresh()
		self.system.RefreshRecent()

	def ShowItemToolTip(self, itemVnum):
		self.system.ShowItemToolTip(itemVnum)

	def HideItemToolTip(self):
		self.system.HideItemToolTip()

	def _RememberPosition(self):
		if not self.IsShow():
			return
		position = self.GetLocalPosition()
		if position != self.lastPosition:
			self.lastPosition = position
			self.model.SetWindowPosition(*position)

	def _ClampToScreen(self):
		x, y = self.GetLocalPosition()
		maxX = max(0, wndMgr.GetScreenWidth() - self.GetWidth())
		maxY = max(0, wndMgr.GetScreenHeight() - self.GetHeight())
		self.SetPosition(
			max(0, min(x, maxX)), max(0, min(y, maxY))
		)

	def _CurrentDetailRows(self, now):
		if self.showHidden:
			return self.model.GetBlacklistedSummary(now)
		if self.model.mode == "log":
			return self.model.GetLog(now)

		result = []
		for entry in self.model.GetItemSummary(now):
			result.append(entry)
			if self.expandedItemVnum != entry["item_vnum"]:
				continue
			for source in entry.get("sources", []):
				child = dict(source)
				child["is_source_child"] = True
				result.append(child)
		return result


class TaskBarDropIcon(ui.Window):
	def __init__(self, owner, parent, index):
		ui.Window.__init__(self)
		self.owner = owner
		self.data = None
		self.itemVnum = 0
		self.lastUpdatedAt = 0.0
		self.pulseUntil = 0.0
		self.SetParent(parent)
		self.SetPosition(
			index * (TASKBAR_ICON_SIZE + TASKBAR_ICON_GAP), 0
		)
		self.SetSize(TASKBAR_ICON_SIZE, TASKBAR_ICON_SIZE)
		self.AddFlag("float")
		self.SetPickAlways()

		self.hover = ui.Bar()
		self.hover.SetParent(self)
		self.hover.SetPosition(0, 0)
		self.hover.SetSize(TASKBAR_ICON_SIZE, TASKBAR_ICON_SIZE)
		self.hover.SetColor(0x553f3527)
		self.hover.AddFlag("not_pick")
		self.hover.Hide()

		self.icon = ui.ImageBox()
		self.icon.SetParent(self)
		self.icon.AddFlag("not_pick")
		self.icon.Hide()

		self.amount = ui.TextLine()
		self.amount.SetParent(self)
		self.amount.SetPosition(TASKBAR_ICON_SIZE - 2, 17)
		self.amount.SetHorizontalAlignRight()
		self.amount.SetPackedFontColor(COLOR_GOLD)
		self.amount.SetOutline()
		self.amount.SetFeather(False)
		self.amount.AddFlag("not_pick")
		self.amount.Hide()
		self.Hide()

	def SetData(self, data, now, alpha):
		updatedAt = float(data.get("updated_at", data["timestamp"]))
		if (
			self.data is None or
			int(self.data["item_vnum"]) != int(data["item_vnum"]) or
			updatedAt != self.lastUpdatedAt
		):
			self.pulseUntil = now + 0.45
		self.lastUpdatedAt = updatedAt

		self.data = data
		vnum = int(data["item_vnum"])
		if self.itemVnum != vnum:
			self.itemVnum = vnum
			iconWidth, iconHeight = _LoadItemIcon(
				self.icon, vnum, TASKBAR_ICON_SIZE - 2
			)
			self.icon.SetPosition(
				max(0, (TASKBAR_ICON_SIZE - iconWidth) // 2),
				max(0, (TASKBAR_ICON_SIZE - iconHeight) // 2),
			)
		self.amount.SetText(_FormatOverlayAmount(data["amount"]))
		self.icon.Show()
		self.amount.Show()
		self._ApplyAlpha(now, alpha)
		self.Show()

	def Clear(self):
		if self.data:
			self.owner.system.HideItemToolTip()
		self.data = None
		self.itemVnum = 0
		self.lastUpdatedAt = 0.0
		self.pulseUntil = 0.0
		self.hover.Hide()
		self.icon.Hide()
		self.amount.Hide()
		self.Hide()

	def _ApplyAlpha(self, now, alpha):
		pulseAlpha = 1.0
		if now < self.pulseUntil:
			pulseAlpha = 0.72 + 0.28 * abs(math.sin(
				(self.pulseUntil - now) * 18.0
			))
		iconAlpha = max(0.0, min(1.0, alpha * pulseAlpha))
		self.icon.SetAlpha(iconAlpha)
		self.amount.SetPackedFontColor(
			_ColorWithAlpha(COLOR_GOLD, alpha)
		)

	def UpdateAnimation(self, now, alpha):
		if self.data:
			self._ApplyAlpha(now, alpha)

	def OnMouseOverIn(self):
		if not self.data:
			return
		self.hover.Show()
		self.owner.system.ShowItemToolTip(
			self.data["item_vnum"], self.data["amount"]
		)

	def OnMouseOverOut(self):
		self.hover.Hide()
		self.owner.system.HideItemToolTip()

	def OnMouseLeftButtonUp(self):
		if self.data:
			self.owner.system.OpenItemDetails(
				self.data["item_vnum"]
			)


class TaskBarDropStrip(ui.Window):
	def __init__(self, system):
		ui.Window.__init__(self)
		self.system = system
		self.taskBar = None
		self.icons = []
		self.AddFlag("float")
		self.SetSize(1, TASKBAR_ICON_SIZE)
		for index in range(TASKBAR_MAX_ICONS):
			self.icons.append(TaskBarDropIcon(self, self, index))
		self.Hide()

	def BindTaskBar(self, taskBar):
		self.taskBar = taskBar
		if taskBar:
			self.SetParent(taskBar)
		self.Refresh()

	def Refresh(self):
		now = time.time()
		left, capacity = self._Measure()
		recent = self.system.model.GetRecent(now, capacity)
		if (
			self.system.GetPlacementMode() !=
				droptrackermodel.LAYOUT_MODE_TASKBAR or
			not self.system.available or not self.taskBar or
			capacity <= 0 or not recent
		):
			self._Clear()
			return

		alpha = self._GroupAlpha(now)
		for index, icon in enumerate(self.icons):
			if index < len(recent):
				icon.SetPosition(
					index * (
						TASKBAR_ICON_SIZE + TASKBAR_ICON_GAP
					), 0
				)
				icon.SetData(recent[index], now, alpha)
			else:
				icon.Clear()

		width = (
			len(recent) * TASKBAR_ICON_SIZE +
			max(0, len(recent) - 1) * TASKBAR_ICON_GAP
		)
		self.SetPosition(left, 2)
		self.SetSize(max(1, width), TASKBAR_ICON_SIZE)
		self.Show()
		self.SetTop()

	def OnUpdate(self):
		self.system.Tick()
		self._UpdateAnimation(time.time())

	def Destroy(self):
		self._Clear()
		self.icons = []
		self.taskBar = None
		self.Hide()

	def _Measure(self):
		if not self.taskBar:
			return (0, 0)

		left = 264
		right = max(left, wndMgr.GetScreenWidth() // 2 - 128)
		try:
			antiExp = self.taskBar.GetChild2("AntiExp")
			if antiExp:
				antiX, _ = antiExp.GetLocalPosition()
				left = (
					antiX + max(32, antiExp.GetWidth()) + 4
				)
		except:
			pass
		try:
			leftMouse = self.taskBar.GetChild2("LeftMouseButton")
			if leftMouse:
				mouseX, _ = leftMouse.GetLocalPosition()
				right = mouseX - 4
		except:
			pass

		available = max(0, right - left)
		capacity = min(
			TASKBAR_MAX_ICONS,
			(available + TASKBAR_ICON_GAP) //
			(TASKBAR_ICON_SIZE + TASKBAR_ICON_GAP),
		)
		return (left, max(0, capacity))

	def _GroupAlpha(self, now):
		lifetime = self.system.model.recent_lifetime
		if lifetime <= 0:
			return 1.0
		remaining = (
			float(lifetime) -
			(now - self.system.model.recent_updated_at)
		)
		if remaining >= TASKBAR_FADE_SECONDS:
			return 1.0
		progress = max(
			0.0, min(1.0, remaining / TASKBAR_FADE_SECONDS)
		)
		return progress * progress * (3.0 - 2.0 * progress)

	def _UpdateAnimation(self, now):
		if not self.IsShow():
			return
		alpha = self._GroupAlpha(now)
		for icon in self.icons:
			icon.UpdateAnimation(now, alpha)

	def _Clear(self):
		for icon in self.icons:
			icon.Clear()
		self.Hide()


class FloatingDropStripGrip(ui.Bar):
	def __init__(self, owner):
		ui.Bar.__init__(self)
		self.owner = owner
		self.editing = False
		self.hovered = False
		self.SetParent(owner)
		self.SetSize(FLOATING_GRIP_WIDTH, TASKBAR_ICON_SIZE)
		self.AddFlag("dragable")
		self.SetPickAlways()

		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.SetPosition(FLOATING_GRIP_WIDTH // 2, 8)
		self.label.SetHorizontalAlignCenter()
		self.label.SetPackedFontColor(COLOR_MUTED)
		self.label.SetText("::")
		self.label.AddFlag("not_pick")
		self.label.Show()
		self._RefreshColor()
		self.Show()

	def SetEditing(self, editing):
		self.editing = bool(editing)
		self._RefreshColor()

	def OnMouseOverIn(self):
		self.hovered = True
		self._RefreshColor()

	def OnMouseOverOut(self):
		self.hovered = False
		self._RefreshColor()

	def OnMouseLeftButtonDown(self):
		self.owner.BeginGripDrag()
		return True

	def OnMouseDrag(self, x, y):
		self.owner.DragGrip(x, y)

	def OnMouseLeftButtonUp(self):
		self.owner.EndGripDrag()

	def _RefreshColor(self):
		if self.editing:
			self.SetColor(0xaa755627)
			self.label.SetPackedFontColor(COLOR_GOLD)
		elif self.hovered:
			self.SetColor(0x99483b2b)
			self.label.SetPackedFontColor(COLOR_TEXT)
		else:
			self.SetColor(0x66302720)
			self.label.SetPackedFontColor(COLOR_MUTED)


class FloatingDropStrip(TaskBarDropStrip):
	def __init__(self, system):
		ui.Window.__init__(self, "TOP_MOST")
		self.system = system
		self.taskBar = None
		self.icons = []
		self.visibleCount = 0
		self.editUntil = 0.0
		self.growLeft = False
		self.dragging = False
		self.AddFlag("float")
		self.SetSize(FLOATING_GRIP_WIDTH, TASKBAR_ICON_SIZE)

		self.editBackdrop = ui.Bar()
		self.editBackdrop.SetParent(self)
		self.editBackdrop.SetPosition(0, 0)
		self.editBackdrop.SetColor(0x88302a22)
		self.editBackdrop.AddFlag("not_pick")
		self.editBackdrop.Hide()

		for index in range(TASKBAR_MAX_ICONS):
			self.icons.append(TaskBarDropIcon(self, self, index))

		self.grip = FloatingDropStripGrip(self)

		self.editHint = ui.TextLine()
		self.editHint.SetParent(self)
		self.editHint.SetPosition(0, 8)
		self.editHint.SetHorizontalAlignCenter()
		self.editHint.SetPackedFontColor(COLOR_TEXT)
		self.editHint.SetOutline()
		self.editHint.SetText(_Locale(
			"DROP_TRACKER_PLACEMENT_EDIT_HINT",
			"Drag the handle",
		))
		self.editHint.AddFlag("not_pick")
		self.editHint.Hide()
		self.Hide()

	def BindTaskBar(self, taskBar):
		self.taskBar = taskBar
		self.Refresh()

	def BeginEdit(self):
		self.editUntil = time.time() + FLOATING_EDIT_SECONDS
		self.Refresh()

	def Refresh(self):
		now = time.time()
		editing = now < self.editUntil
		if (
			self.system.GetPlacementMode() !=
				droptrackermodel.LAYOUT_MODE_FREE
		):
			self._Clear()
			return
		if not self.system.available:
			self._Clear()
			return

		anchorX, anchorY = self._GetAnchor()
		if not self.dragging:
			self.growLeft = (
				anchorX > wndMgr.GetScreenWidth() // 2
			)
		capacity = self._MeasureCapacity(anchorX, self.growLeft)
		recent = (
			self.system.model.GetRecent(now, capacity)
			if capacity > 0 else []
		)
		if not recent and not editing:
			self._Clear()
			return

		alpha = self._GroupAlpha(now)
		for index, icon in enumerate(self.icons):
			if index < len(recent):
				icon.SetData(recent[index], now, alpha)
			else:
				icon.Clear()

		self.visibleCount = len(recent)
		self._ApplyLayout(anchorX, anchorY, editing)
		self.Show()
		self.SetTop()

	def OnUpdate(self):
		self.system.Tick()
		now = time.time()
		if self.editUntil and now >= self.editUntil:
			self.editUntil = 0.0
			self.Refresh()
			return
		self._UpdateAnimation(now)

	def BeginGripDrag(self):
		self.dragging = True
		self.editUntil = time.time() + FLOATING_EDIT_SECONDS

	def DragGrip(self, x, y):
		anchorX, anchorY = self._ClampAnchor(
			int(x), int(y)
		)
		self._StoreAnchor(anchorX, anchorY)
		self.editUntil = time.time() + FLOATING_EDIT_SECONDS
		self.growLeft = anchorX > wndMgr.GetScreenWidth() // 2
		self._ApplyLayout(
			anchorX, anchorY, self.editUntil > time.time()
		)

	def EndGripDrag(self):
		self.dragging = False
		self.system.layout.Save(force=True)
		self.Refresh()

	def Destroy(self):
		self.system.HideItemToolTip()
		TaskBarDropStrip.Destroy(self)
		self.grip = None
		self.editBackdrop = None
		self.editHint = None

	def _TaskBarTop(self):
		if self.taskBar:
			try:
				_unusedX, taskBarY = self.taskBar.GetGlobalPosition()
				return int(taskBarY)
			except:
				pass
		return max(0, wndMgr.GetScreenHeight() - 37)

	def _AnchorBounds(self):
		minX = FLOATING_SCREEN_MARGIN
		maxX = max(
			minX,
			wndMgr.GetScreenWidth() -
				FLOATING_SCREEN_MARGIN - FLOATING_GRIP_WIDTH,
		)
		minY = FLOATING_SCREEN_MARGIN
		maxY = max(
			minY,
			self._TaskBarTop() - TASKBAR_ICON_SIZE -
				FLOATING_TASKBAR_GAP,
		)
		return minX, maxX, minY, maxY

	def _ClampAnchor(self, anchorX, anchorY):
		minX, maxX, minY, maxY = self._AnchorBounds()
		return (
			max(minX, min(int(anchorX), maxX)),
			max(minY, min(int(anchorY), maxY)),
		)

	def _DefaultAnchor(self):
		anchorX = wndMgr.GetScreenWidth() // 4
		try:
			antiExp = self.taskBar.GetChild2("AntiExp")
			if antiExp:
				antiX, _antiY = antiExp.GetGlobalPosition()
				anchorX = antiX + max(32, antiExp.GetWidth()) + 4
		except:
			pass
		anchorY = (
			self._TaskBarTop() - TASKBAR_ICON_SIZE -
			FLOATING_TASKBAR_GAP
		)
		return self._ClampAnchor(anchorX, anchorY)

	def _GetAnchor(self):
		minX, maxX, minY, maxY = self._AnchorBounds()
		normalized = self.system.layout.floating_anchor
		if normalized is None:
			return self._DefaultAnchor()
		return self._ClampAnchor(
			minX + int(round((maxX - minX) * normalized[0])),
			minY + int(round((maxY - minY) * normalized[1])),
		)

	def _StoreAnchor(self, anchorX, anchorY):
		minX, maxX, minY, maxY = self._AnchorBounds()
		normalizedX = (
			float(anchorX - minX) / float(max(1, maxX - minX))
		)
		normalizedY = (
			float(anchorY - minY) / float(max(1, maxY - minY))
		)
		self.system.layout.SetFloatingAnchor(
			round(normalizedX, 6), round(normalizedY, 6)
		)

	def _MeasureCapacity(self, anchorX, growLeft):
		if growLeft:
			available = anchorX - FLOATING_SCREEN_MARGIN
		else:
			available = (
				wndMgr.GetScreenWidth() - FLOATING_SCREEN_MARGIN -
				anchorX - FLOATING_GRIP_WIDTH
			)
		return max(0, min(
			TASKBAR_MAX_ICONS,
			(available + TASKBAR_ICON_GAP) //
				(TASKBAR_ICON_SIZE + TASKBAR_ICON_GAP),
		))

	def _ApplyLayout(self, anchorX, anchorY, editing):
		iconAreaWidth = (
			self.visibleCount * TASKBAR_ICON_SIZE +
			max(0, self.visibleCount - 1) * TASKBAR_ICON_GAP
		)
		if editing and self.visibleCount == 0:
			if self.growLeft:
				available = anchorX - FLOATING_SCREEN_MARGIN
			else:
				available = (
					wndMgr.GetScreenWidth() -
					FLOATING_SCREEN_MARGIN - anchorX -
					FLOATING_GRIP_WIDTH
				)
			iconAreaWidth = min(
				FLOATING_PREVIEW_WIDTH, max(1, available)
			)
		totalWidth = FLOATING_GRIP_WIDTH + iconAreaWidth

		if self.growLeft:
			rootX = anchorX - iconAreaWidth
			gripX = iconAreaWidth
			for index, icon in enumerate(self.icons):
				icon.SetPosition(
					iconAreaWidth - TASKBAR_ICON_SIZE -
						index * (
							TASKBAR_ICON_SIZE +
							TASKBAR_ICON_GAP
						),
					0,
				)
			hintX = iconAreaWidth // 2
		else:
			rootX = anchorX
			gripX = 0
			for index, icon in enumerate(self.icons):
				icon.SetPosition(
					FLOATING_GRIP_WIDTH +
						index * (
							TASKBAR_ICON_SIZE +
							TASKBAR_ICON_GAP
						),
					0,
				)
			hintX = FLOATING_GRIP_WIDTH + iconAreaWidth // 2

		self.SetPosition(int(rootX), int(anchorY))
		self.SetSize(max(FLOATING_GRIP_WIDTH, totalWidth), TASKBAR_ICON_SIZE)
		self.editBackdrop.SetSize(
			max(FLOATING_GRIP_WIDTH, totalWidth),
			TASKBAR_ICON_SIZE,
		)
		self.grip.SetPosition(gripX, 0)
		self.grip.SetEditing(editing)

		if editing:
			self.editBackdrop.Show()
			if self.visibleCount == 0:
				self.editHint.SetPosition(hintX, 8)
				self.editHint.Show()
			else:
				self.editHint.Hide()
		else:
			self.editBackdrop.Hide()
			self.editHint.Hide()
		self.grip.SetTop()


class DropTrackerSystem(object):
	def __init__(self):
		self.model = droptrackermodel.DropTrackerModel()
		self.layout = droptrackermodel.DropTrackerLayoutConfig()
		self.available = False
		self.lastRefresh = 0.0
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.Hide()
		self.window = DropTrackerWindow(self)
		self.recentStrip = TaskBarDropStrip(self)
		self.floatingStrip = FloatingDropStrip(self)
		self._LoadPlayerIdentity()

	def BindTaskBar(self, taskBar):
		self.recentStrip.BindTaskBar(taskBar)
		self.floatingStrip.BindTaskBar(taskBar)

	def _LoadPlayerIdentity(self):
		try:
			name = player.GetName()
		except:
			name = "character"
		self.model.SetIdentity(name)

	def SetCapability(self, available):
		self.available = bool(available)
		if self.available:
			self._LoadPlayerIdentity()
		else:
			self.recentStrip.Hide()
			self.floatingStrip.Hide()
		if self.window.IsShow():
			self.window.Refresh()
		self.RefreshRecent()

	def AddBatch(self, rows):
		if not self.available:
			return
		self._LoadPlayerIdentity()
		if self.model.AddBatch(rows):
			self.RefreshRecent()
			if self.window.IsShow():
				self.window.Refresh()
			self.model.Save()

	def ToggleWindow(self):
		if self.window.IsShow():
			self.window.Close()
		else:
			self.window.Open()

	def CloseWindow(self):
		if self.window.IsShow():
			self.window.Close()

	def OpenItemDetails(self, itemVnum):
		if not self.window.IsShow():
			self.window.Open()
		self.window.OpenDetailsForItem(itemVnum)
		self.window.SetTop()

	def RefreshRecent(self):
		self.recentStrip.Refresh()
		self.floatingStrip.Refresh()

	def SetRecentLifetime(self, seconds):
		if not self.model.SetRecentLifetime(seconds):
			return False
		saved = self.model.Save(force=True)
		self.RefreshRecent()
		if self.window.IsShow():
			self.window.Refresh()
		return saved

	def GetPlacementMode(self):
		return self.layout.mode

	def SetPlacementMode(self, mode):
		changed = self.layout.SetMode(mode)
		if changed:
			self.layout.Save(force=True)
		if self.layout.mode == droptrackermodel.LAYOUT_MODE_FREE:
			self.floatingStrip.BeginEdit()
		self.RefreshRecent()

	def BeginPlacementEdit(self):
		if self.layout.mode != droptrackermodel.LAYOUT_MODE_FREE:
			return False
		self.floatingStrip.BeginEdit()
		return True

	def ResetFloatingPlacement(self):
		self.layout.ResetFloatingAnchor()
		self.layout.Save(force=True)
		if self.layout.mode == droptrackermodel.LAYOUT_MODE_FREE:
			self.floatingStrip.BeginEdit()
		self.RefreshRecent()

	def Tick(self):
		now = time.time()
		if now - self.lastRefresh < 0.25:
			return
		self.lastRefresh = now
		self.RefreshRecent()
		if self.window.IsShow():
			self.window.Refresh()
		self.model.Save(now=now)
		self.layout.Save(now=now)

	def ShowItemToolTip(self, itemVnum, amount=None):
		try:
			itemVnum = int(itemVnum)
			self.tooltipItem.SetItemToolTip(itemVnum)
			if amount is not None:
				self.tooltipItem.AppendTextLine(
					_Locale(
						"DROP_TRACKER_OBTAINED",
						"Obtained: %s",
					) % _FormatNumber(amount),
					COLOR_GOLD,
				)
			self.tooltipItem.ShowToolTip()
		except:
			self.tooltipItem.HideToolTip()

	def HideItemToolTip(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def Destroy(self):
		self.model.Save(force=True)
		self.layout.Save(force=True)
		self.HideItemToolTip()
		self.window.Destroy()
		self.recentStrip.Destroy()
		self.floatingStrip.Destroy()
		self.window = None
		self.recentStrip = None
		self.floatingStrip = None
		self.tooltipItem = None
		self.layout = None
