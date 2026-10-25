import ui, app, net, osfInfo, player
import datetime
import chat
import wndMgr
import localeInfo
import fontconfig
import grp
import eventcalendarlogic
import json

DAY_VIEW_ART = "calendar_day_view/"
# Native pack.Get reads .py/.pyc/.txt only; this text file contains JSON.
with open(DAY_VIEW_ART + "layout.txt", "r") as _layoutFile:
	CALENDAR_LAYOUT = json.load(_layoutFile)
if app.ENABLE_WHEEL_OF_FORTUNE:
	import uiWheelofFortune
from uiToolTip import ItemToolTip, GET_AFFECT_STRING
IMG_DIR = "d:/ymir work/ui/game/event_calendar/"
IMG_ICON_DIR = "d:/ymir work/ui/game/event_calendar/icons/"
IMG_ICON_EX_DIR = "d:/ymir work/ui/game/event_calendar/icons/icons/"
CRIMSON_CALENDAR_DIR = "d:/ymir work/ui/game/crimson_ember/event_calendar/"
CALENDAR_ARROW_LEFT = DAY_VIEW_ART + "arrow_left.png"
CALENDAR_ARROW_RIGHT = DAY_VIEW_ART + "arrow_right.png"
DENSE_FONT_ROLE = fontconfig.ROLE_DENSE
SECTION_FONT_ROLE = fontconfig.ROLE_SECTION
# This fork has no WindowDestroy; retain its explicit cleanup convention.
WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)

WINDOW_WIDTH, WINDOW_HEIGHT = CALENDAR_LAYOUT["size"]
PAGER_GLYPH_SIZE = 16

def _Color(red, green, blue, alpha=255):
	# Python 3 rejects positive packed ARGB values above INT_MAX in wndMgr.
	return grp.GenerateColor(
		float(red) / 255.0,
		float(green) / 255.0,
		float(blue) / 255.0,
		float(alpha) / 255.0,
	)


PANEL_SURFACE_COLOR = _Color(21, 19, 21)
DAY_SURFACE_COLOR = _Color(21, 19, 21)
DAY_TODAY_TEXT_COLOR = _Color(145, 189, 123)
DAY_SELECTED_TEXT_COLOR = _Color(213, 184, 120)
ROW_SELECTED_COLOR = _Color(90, 20, 26, 170)
LIGHT_TEXT_COLOR = _Color(228, 218, 203)
METADATA_TEXT_COLOR = _Color(170, 162, 147)
TIME_TEXT_COLOR = _Color(213, 184, 120)
EVENT_ROW_HOVER_COLOR = _Color(81, 26, 30, 136)
EMPTY_TEXT_COLOR = _Color(118, 105, 93)

events_default_data = {
	# img , eventName
	player.BONUS_EVENT:["bonus_event",""],
	player.DOUBLE_BOSS_LOOT_EVENT:["double_boss_loot_event",localeInfo.EVENT_CALENDAR_NAME_BOSS],
	player.DOUBLE_METIN_LOOT_EVENT:["double_metin_loot_event", localeInfo.EVENT_CALENDAR_NAME_METIN],
	player.MOONLIGHT_EVENT:["moonlight_event",localeInfo.EVENT_CALENDAR_NAME_MOONLIGHT],
	player.DOUBLE_FISHING_EVENT:["double_fishing_event", localeInfo.EVENT_CALENDAR_NAME_FISHING],
	player.DOUBLE_MINING_EVENT:["double_mining_event", localeInfo.EVENT_CALENDAR_NAME_MINING],
	player.OKEY_CARD_EVENT:["okay_cards",localeInfo.EVENT_CALENDAR_NAME_OKEY],
	player.CATCH_KING_EVENT:["catch_king",localeInfo.EVENT_CALENDAR_NAME_KING],
	player.ITEM_DROP_EVENT:["item_drop_event",localeInfo.EVENT_CALENDAR_NAME_ITEM],
	player.YANG_DROP_EVENT:["money_drop_event",localeInfo.EVENT_CALENDAR_NAME_YANG],
	player.EXP_EVENT:["exp_event",localeInfo.EVENT_CALENDAR_NAME_EXP],
	player.WHEEL_FORTUNE_EVENT:["Wheel_of_fortune_event",localeInfo.EVENT_CALENDAR_NAME_WHEEL],
	player.KINGDOMS_WAR_EVENT:["kingdoms_war_event",localeInfo.EVENT_CALENDAR_NAME_WAR],
}


def _GetEventDefinition(eventIndex):
	return events_default_data.get(int(eventIndex), ["bonus_event", localeInfo.EVENT_CALENDAR_UNKNOWN])

#Dont touch!
def CalculateDayCount(month, year):
	if month == 2:
		if ((year%400==0) or (year%4==0 and year%100!=0)):
			return 29
		else:
			return 28
	elif month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month==12:
		return 31
	else:
		return 30
EVENT_DAY_INDEX = 0
EVENT_ID = 1
EVENT_INDEX = 2
EVENT_START_TEXT = 3
EVENT_END_TEXT = 4
EVENT_EMPIRE_FLAG = 5
EVENT_CHANNEL_FLAG = 6
EVENT_VALUE0 = 7
EVENT_VALUE1 = 8
EVENT_VALUE2 = 9
EVENT_VALUE3 = 10
EVENT_VALUE4 = 11
EVENT_VALUE5 = 12
EVENT_VALUE6 = 13
EVENT_VALUE7 = 14
EVENT_START_TIME = 15
EVENT_END_TIME = 16
EVENT_IS_ACTIVE = 17
server_event_data = {}
def SetEventStatus(eventID, eventStatus, endTime, endTimeText):
	for dateKey, eventList in server_event_data.items():
		if eventID in eventList:
			eventList[eventID][EVENT_IS_ACTIVE] = eventStatus
			eventList[eventID][EVENT_END_TIME] = endTime
			eventList[eventID][EVENT_END_TEXT] = endTimeText
def SetServerData(dayIndex, eventID, eventIndex, startTime, endTime, empireFlag, channelFlag, value0, value1, value2, value3, value4, value5, value6, value7, startRealTime, endRealTime, isAlreadyStart):
	row = [dayIndex, eventID, eventIndex, startTime, endTime, empireFlag, channelFlag, value0, value1, value2, value3, value4, value5, value6, value7, startRealTime, endRealTime, isAlreadyStart]
	dateKey = eventcalendarlogic.ResolveEventTimestamp(startRealTime, endRealTime)
	if dateKey is None:
		return
	if dateKey not in server_event_data:
		server_event_data[dateKey] = {}
	server_event_data[dateKey][eventID] = row
def IsEventIDActive(eventID):
	for dateKey, eventList in server_event_data.items():
		if eventID in eventList:
			return bool(eventList[eventID][EVENT_IS_ACTIVE])
	return False
def IsEventIndexActive(eventIndex):
	for dateKey, eventList in server_event_data.items():
		for eventID, eventData in eventList.items():
			if eventData[EVENT_IS_ACTIVE] and eventData[EVENT_INDEX] == eventIndex:
				return True
	return False
def GetEventIndexData(eventIndex):
	for dateKey, eventList in server_event_data.items():
		for eventID, eventData in eventList.items():
			if eventData[EVENT_INDEX] == eventIndex:
				return eventData
	return None
def GetEventIDData(eventID):
	for dateKey, eventList in server_event_data.items():
		if eventID in eventList:
			return eventList[eventID]
	return None
#Dont touch!

class ImageBoxSpecial(ui.ImageBox):
	def __del__(self):
		ui.ImageBox.__del__(self)
	def Destroy(self):
		self.miniIcon = None
		self.eventList=[]
		self.imageIndex = 0
		self.isMiniIcon = False
		if app.ENABLE_WINDOW_RESIZE:
			self._miniRightMargin = None
			self._miniTop = None

		self.waitingTime = 0.0
		self.sleepTime = 0.0
		self.alphaValue = 0.0
		self.increaseValue = 0.0
		self.minAlpha = 0.0
		self.maxAlpha = 0.0
		self.alphaStatus = False

	def __init__(self, isMiniIcon = False):
		ui.ImageBox.__init__(self)
		self.Destroy()
		self.isMiniIcon = isMiniIcon

		self.waitingTime = 2.0
		self.alphaValue = 0.3
		self.increaseValue = 0.05
		self.minAlpha = 0.3
		self.maxAlpha = 1.0

		if isMiniIcon:
			self.AddFlag("attach")
			self.AddFlag("movable")
			#self.SetSize(57, 57)
			(x,y) = (wndMgr.GetScreenWidth()-285, 0)
			self.SetPosition(x, y)
			if app.ENABLE_WINDOW_RESIZE:
				self._miniRightMargin = wndMgr.GetScreenWidth() - (x + self.GetWidth())
				self._miniTop = y
			self.SetEvent(ui.__mem_func__(self.OnClickEventIcon),"mouse_click")
			self.SetMouseLeftButtonDoubleClickEvent(ui.__mem_func__(self.OnClickDouble))
			self.SetMouseRightButtonDownEvent(ui.__mem_func__(self.NextEventWithKey))

	def OnMoveWindow(self, x, y):
		(screenWidth, screenHeight) = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		maxX = screenWidth - self.GetWidth()
		maxY = screenHeight - self.GetHeight()
		if maxX < 0:
			maxX = 0
		if maxY < 0:
			maxY = 0

		if x < 0:
			x = 0
		elif x > maxX:
			x = maxX

		if y < 0:
			y = 0
		elif y > maxY:
			y = maxY

		self.SetPosition(x, y)
		if app.ENABLE_WINDOW_RESIZE:
			if self.isMiniIcon:
				self._miniRightMargin = screenWidth - (x + self.GetWidth())
				self._miniTop = y

	def NextEventWithKey(self):
		if len(self.eventList) > 1:
			self.sleepTime = 0
			self.alphaValue = self.maxAlpha
			self.alphaStatus = True

	def SetBackgroundImage(self, image):
		self.LoadImage(image)
		self.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem)
		self.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
		self.SetEvent(ui.__mem_func__(self.OnClickEventIcon),"mouse_click")

	def OnClickEventIcon(self):
		(_index, eventID) = self.GetNextImage(self.imageIndex)
		if GetEventIDData(eventID) != None:
			if GetEventIDData(eventID)[EVENT_IS_ACTIVE] == True:
				interface = osfInfo.GetInterfaceInstance()
				if interface:
					if interface.wndEventManager:
						interface.wndEventManager.OnClick(GetEventIDData(eventID)[EVENT_INDEX])

	def SetImage(self, folder):
		if self.miniIcon == None:
			miniIcon = ui.ImageBox()
			miniIcon.SetParent(self)
			miniIcon.AddFlag("not_pick")
			self.miniIcon = miniIcon

		if self.isMiniIcon == True:
			self.miniIcon.LoadImage(IMG_ICON_EX_DIR+folder+".tga")
		else:
			self.miniIcon.LoadImage(IMG_ICON_DIR+folder+".tga")
		self.miniIcon.SetPosition(6, 6)
		self.miniIcon.Show()

		if self.isMiniIcon:
			self.SetSize(85,70)
			if app.ENABLE_WINDOW_RESIZE:
				try:
					x, y = self.GetLocalPosition()
					self._miniRightMargin = wndMgr.GetScreenWidth() - (x + self.GetWidth())
					self._miniTop = y
				except:
					pass

		self.alphaValue = self.minAlpha
		self.alphaStatus = False

	def OnClickDouble(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			interface.OpenEventCalendar()
	def OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def OverInItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.wndEventManager:
				if self.isMiniIcon:
					(_index, eventID) = self.GetNextImage(self.imageIndex)
					eventData = GetEventIDData(eventID)
					if eventData:
						interface.wndEventManager.ShowEventTooltip(eventData)
				elif hasattr(self, "dayIndex"):
					interface.wndEventManager.OverInItem(self.dayIndex)
	def Clear(self):
		self.miniIcon = None
		self.eventList = []
		if self.isMiniIcon:
			self.SetSize(0,0)
			
	def DeleteImage(self, eventIndex):
		del self.eventList[eventIndex]
		if self.isMiniIcon and len(self.eventList) == 0:
			self.SetSize(0,0)

	def AppendImage(self, eventID):
		if eventID in self.eventList:
			return
		self.eventList.append(eventID)
		if len(self.eventList) == 1:
			self.imageIndex = 0
			if GetEventIDData(eventID) != None:
				self.SetImage(_GetEventDefinition(GetEventIDData(eventID)[EVENT_INDEX])[0])
		
		if self.isMiniIcon:
			self.SetSize(57,57)

	def GetNextImage(self, listIndex):
		if listIndex >= len(self.eventList):
			if len(self.eventList) > 0:
				return (0,self.eventList[0])
			return (0,0)
		return (listIndex, self.eventList[listIndex])
	
	def OnUpdate(self):
		if app.ENABLE_WINDOW_RESIZE:
			if self.isMiniIcon and self._miniRightMargin is not None:
				try:
					screenW = wndMgr.GetScreenWidth()
					x = screenW - self.GetWidth() - self._miniRightMargin
					y = self._miniTop if self._miniTop is not None else 0
					self.OnMoveWindow(x, y)
				except:
					pass
			elif self.isMiniIcon and self._miniRightMargin is None:
				try:
					x, y = self.GetLocalPosition()
					self._miniRightMargin = wndMgr.GetScreenWidth() - (x + self.GetWidth())
					self._miniTop = y
				except:
					pass

		if len(self.eventList) <= 1:
			self.imageIndex=0
			return
		elif self.sleepTime > app.GetTime():
			return
		if self.alphaStatus == True:
			self.alphaValue -= self.increaseValue
			if self.alphaValue < self.minAlpha:
				self.alphaValue = self.minAlpha
				self.alphaStatus = False
				(imageIndex, eventID) = self.GetNextImage(self.imageIndex+1)
				if GetEventIDData(eventID) != None:
					self.SetImage(_GetEventDefinition(GetEventIDData(eventID)[EVENT_INDEX])[0])
				self.imageIndex = imageIndex
		else:
			self.alphaValue += self.increaseValue
			if self.alphaValue > self.maxAlpha:
				self.alphaStatus = True
				self.sleepTime = app.GetTime()+self.waitingTime
		if self.miniIcon != None:
			self.miniIcon.SetAlpha(self.alphaValue)

class CalendarEventRow(ui.Window):
	WIDTH = 303
	HEIGHT = 52

	def __init__(self, parent, owner):
		ui.Window.__init__(self)
		from _weakref import proxy
		self.owner = proxy(owner)
		self.eventData = None
		self.selected = False
		self.SetParent(parent)
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.background = owner.CreateEventImage(self, 0, 0, DAY_VIEW_ART + "row.png")
		self.icon = owner.CreateEventImage(self, 8, 10, DAY_VIEW_ART + "icons/bonus_event_32.png")
		self.name = owner.CreateEventText(self, 50, 8, "", LIGHT_TEXT_COLOR, width=243, section=True)
		self.clock = owner.CreateEventText(self, 50, 28, "", METADATA_TEXT_COLOR, width=139)
		self.status = owner.CreateEventText(self, 293, 28, "", TIME_TEXT_COLOR, align="right", width=101)

	def SetEvent(self, eventData, selected):
		self.eventData = eventData
		self.selected = selected
		state = self.owner.GetEventState(eventData)
		self.icon.LoadImage(self.owner.GetIconPath(eventData, 32, state == "ended" and not selected))
		self.name.SetText(self.owner.GetEventName(eventData))
		self.clock.SetText(self.owner.GetEventTimeLabel(eventData))
		state = self.owner.GetEventState(eventData)
		self.status.SetText(self.owner.GetEventStatus(eventData))
		self.status.SetPackedFontColor(DAY_TODAY_TEXT_COLOR if state == "active" else
			_Color(82, 77, 72) if state == "ended" and not selected else _Color(117, 111, 101) if state == "ended" else TIME_TEXT_COLOR)
		color = _Color(154, 147, 138) if state == "ended" and not selected else LIGHT_TEXT_COLOR
		self.name.SetPackedFontColor(color)
		self.clock.SetPackedFontColor(_Color(116, 110, 102) if state == "ended" and not selected else METADATA_TEXT_COLOR)
		self.icon.SetAlpha(1.0)
		self.background.LoadImage(DAY_VIEW_ART + ("row_selected.png" if selected else "row_ended.png" if state == "ended" else "row.png"))
		self.Show()

	def OnMouseOverIn(self):
		self.background.LoadImage(DAY_VIEW_ART + "row_selected.png")
		if self.eventData:
			self.owner.ShowEventTooltip(self.eventData)

	def OnMouseOverOut(self):
		if self.eventData:
			self.SetEvent(self.eventData, self.selected)
		self.owner.HideEventTooltip()

	def OnMouseLeftButtonDown(self):
		if self.eventData:
			self.owner.SelectEvent(self.eventData[EVENT_ID])
		return True


class CalendarWeekDay(ui.Window):
	def __init__(self, parent, owner):
		ui.Window.__init__(self)
		from _weakref import proxy
		self.owner = proxy(owner)
		self.dateKey = None
		self.selected = False
		self.allowed = False
		self.SetParent(parent)
		self.SetSize(*CALENDAR_LAYOUT["week_size"])
		self.background = owner.CreateEventImage(self, 0, 0, DAY_VIEW_ART + "week_selected.png")
		self.accent = owner.CreateEventBar(self, 20, 0, 35, 2, DAY_SELECTED_TEXT_COLOR)
		self.label = owner.CreateEventText(self, 37, 6, "", align="center", width=74)
		self.count = owner.CreateEventText(self, 37, 24, "", METADATA_TEXT_COLOR, "center", 74, font="week_count")

	def SetDate(self, dateKey, count, selected, today, allowed):
		self.dateKey, self.selected, self.allowed = dateKey, selected, allowed
		self.background.LoadImage(DAY_VIEW_ART + "week_selected.png")
		self.background.Show() if selected else self.background.Hide()
		self.accent.Show() if today else self.accent.Hide()
		# Native SetValue ignores identical captions; clear cached glyphs before font changes.
		self.label.SetText("")
		self.label.SetFontName(CALENDAR_LAYOUT["fonts"]["dense"] + ("b" if selected else ""))
		self.label.SetPackedFontColor(DAY_SELECTED_TEXT_COLOR if selected or today else LIGHT_TEXT_COLOR if allowed else EMPTY_TEXT_COLOR)
		day = datetime.date(*dateKey)
		self.label.SetText(localeInfo.EVENT_CALENDAR_WEEK_DATE % (
			getattr(localeInfo, "EVENT_CALENDAR_WEEKDAY_%d" % day.weekday()), day.day, day.month))
		self.count.SetText(self.owner.GetEventCount(count) if count else localeInfo.EVENT_CALENDAR_WEEK_EMPTY)
		self.count.SetPackedFontColor(LIGHT_TEXT_COLOR if selected else METADATA_TEXT_COLOR if allowed else EMPTY_TEXT_COLOR)
		self.Show()

	def OnMouseOverIn(self):
		if self.allowed and not self.selected:
			self.background.LoadImage(DAY_VIEW_ART + "week_hover.png")
			self.background.Show()

	def OnMouseOverOut(self):
		self.background.LoadImage(DAY_VIEW_ART + "week_selected.png")
		self.background.Show() if self.selected else self.background.Hide()

	def OnMouseLeftButtonDown(self):
		if self.allowed and self.dateKey:
			self.owner.SelectDate(self.dateKey)
		return True


class EventCalendarWindow(ui.BoardWithTitleBar):
	PAGE_SIZE = CALENDAR_LAYOUT["page_size"]
	ROWS_PER_COLUMN = CALENDAR_LAYOUT["rows_per_column"]
	ROW_PITCH = CALENDAR_LAYOUT["row_pitch"]

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.__Initialize()
		self.AddFlag("movable")
		self.AddFlag("float")
		# Pin only this window to the exact approved chrome, independent of shared UI edits.
		self.LoadVisuals(DAY_VIEW_ART + "chrome/Board_Corner_", DAY_VIEW_ART + "chrome/Board_Line_", DAY_VIEW_ART + "chrome/Board_Base.tga")
		# Native LoadImage recreates image instances and clears their rendering rects.
		# Stretch the pinned board only after every replacement texture is loaded.
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.titleBar.SetVisuals(*[DAY_VIEW_ART + "chrome/" + name for name in (
			"titlebar_left.tga", "titlebar_center.tga", "titlebar_right.tga", "close_01.tga", "close_02.tga", "close_03.tga")])
		self.titleBar.Hide()
		self.titleArt = self.CreateEventImage(self, 0, 0, DAY_VIEW_ART + "titlebar.png")
		self.titleName.SetParent(self)
		self.titleName.SetWindowHorizontalAlignLeft()
		self.titleName.SetPosition(WINDOW_WIDTH // 2, 4)
		self.titleName.SetFontName(CALENDAR_LAYOUT["fonts"]["title"])
		self.titleName.Show()
		self.titleBar.btnClose.SetParent(self)
		self.titleBar.btnClose.SetPosition(WINDOW_WIDTH - 20, 3)
		self.titleBar.btnClose.Show()
		self.SetTitleColor(LIGHT_TEXT_COLOR)
		self.SetTitleName(localeInfo.EVENT_CALENDAR_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__BuildLook()
		self.SetCenterPosition()
		self.Refresh()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Initialize(self):
		self.children = []
		self.eventRows = []
		self.weekDays = []
		self.visibleEvents = []
		self.selectedEventID = None
		self.eventPage = 0
		self.lastUpdate = 0
		self.anchorDate = datetime.date.today()
		self.selectedDate = (self.anchorDate.year, self.anchorDate.month, self.anchorDate.day)
		self.currentYear, self.currentMonth = self.selectedDate[:2]
		for name in ("dateTitle", "dayCount", "previousButton", "nextButton", "todayButton",
				"previousPage", "nextPage", "pageLabel", "emptyDay", "detailIcon", "detailTitle",
				"detailDescription", "detailMetadata", "detailStart", "detailEnd", "detailStatus",
				"detailCountdown", "actionButton", "infoButton", "detailBonus",
				"detailDescription2", "detailClock", "detailMeasure", "previousWeek", "nextWeek"):
			setattr(self, name, None)

	@WindowDestroy
	def Destroy(self):
		self.Hide()
		self.HideEventTooltip()
		self.__Initialize()
		self.r1 = None

	def __Own(self, child):
		self.children.append(child)
		return child

	def CreateEventBar(self, parent, x, y, width, height, color):
		bar = ui.Bar()
		bar.SetParent(parent)
		bar.SetPosition(x, y)
		bar.SetSize(width, height)
		bar.SetColor(color)
		bar.AddFlag("not_pick")
		bar.Show()
		return self.__Own(bar)

	def CreateEventText(self, parent, x, y, text, color=LIGHT_TEXT_COLOR, align="left", width=0, section=False, role=None, font=None):
		label = ui.TextLine()
		label.SetParent(parent)
		label.SetPosition(x, y)
		label.SetFontName(CALENDAR_LAYOUT["fonts"][font or role or (SECTION_FONT_ROLE if section else DENSE_FONT_ROLE)])
		if align == "center":
			label.SetHorizontalAlignCenter()
		elif align == "right":
			label.SetHorizontalAlignRight()
		if width:
			label.SetLimitWidth(width)
		label.SetPackedFontColor(color)
		label.AddFlag("not_pick")
		label.SetOutline(False)
		label.SetText(text)
		label.Show()
		return self.__Own(label)

	def CreateEventImage(self, parent, x, y, path, size=None):
		image = ui.ExpandedImageBox()
		image.SetParent(parent)
		image.SetPosition(x, y)
		image.LoadImage(path)
		if size:
			image.SetScale(float(size) / image.GetWidth(), float(size) / image.GetHeight())
		image.AddFlag("not_pick")
		image.Show()
		return self.__Own(image)

	def __Button(self, x, y, width, text, callback, argument=None, glyph=None):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetSize(width, 24)
		if argument is None:
			button.SetEvent(ui.__mem_func__(callback))
		else:
			button.SetEvent(ui.__mem_func__(callback), argument)
		if glyph:
			button.calendarGlyph = self.CreateEventImage(button, (width - PAGER_GLYPH_SIZE) // 2, 4, glyph)
		else:
			button.calendarLabel = self.CreateEventText(button, width // 2, 5, text, METADATA_TEXT_COLOR, "center", width)
		button.Show()
		return self.__Own(button)

	def __BuildLook(self):
		"""The R1 look (root/uir1calendar.py) unless Settings -> "Starý vzhled" chose the original window or R1 failed;
		a failed R1 build is traced and leaves nothing behind, then the original window is built."""
		self.r1 = None
		try:
			import uir1calendar
			useR1 = uir1calendar.UseR1()
		except Exception:
			useR1 = False
		if useR1:
			kept = list(self.children)
			self.r1 = uir1calendar.Build(self, globals())
			if self.r1:
				return
			self.__Initialize()
			self.children = kept
		self.__BuildWindow()

	def __BuildWindow(self):
		# Preserve revision 5 content; only the outer Board chrome uses shipped art.
		self.CreateEventImage(self, 16, 37, DAY_VIEW_ART + "calendar_24.png")
		self.dateTitle = self.CreateEventText(self, 50, 41, "", DAY_SELECTED_TEXT_COLOR, width=350, font="date")
		self.dayCount = self.CreateEventText(self, WINDOW_WIDTH - 20, 44, "", METADATA_TEXT_COLOR, "right", 210)
		self.CreateEventBar(self, 16, 125, 619, 1, _Color(58, 48, 48))
		self.previousWeek = self.__Button(24, 78, 16, "", self.__ChangeWeek, -1, CALENDAR_ARROW_LEFT)
		self.nextWeek = self.__Button(610, 78, 16, "", self.__ChangeWeek, 1, CALENDAR_ARROW_RIGHT)
		for index in range(CALENDAR_LAYOUT["week_days"]):
			day = CalendarWeekDay(self, self)
			day.SetPosition(CALENDAR_LAYOUT["week_origin"][0] + index * CALENDAR_LAYOUT["week_pitch"], CALENDAR_LAYOUT["week_origin"][1])
			self.weekDays.append(day)
			self.__Own(day)
		for index in range(self.PAGE_SIZE):
			row = CalendarEventRow(self, self)
			row.SetPosition(CALENDAR_LAYOUT["row_origin"][0] + (index // self.ROWS_PER_COLUMN) * CALENDAR_LAYOUT["column_pitch"],
				CALENDAR_LAYOUT["row_origin"][1] + (index % self.ROWS_PER_COLUMN) * self.ROW_PITCH)
			row.Hide()
			self.eventRows.append(row)
			self.__Own(row)
		self.emptyDay = self.CreateEventText(self, 325, 263, localeInfo.EVENT_CALENDAR_EMPTY_DAY,
			EMPTY_TEXT_COLOR, "center", 590)
		self.CreateEventImage(self, CALENDAR_LAYOUT["detail_origin"][0], CALENDAR_LAYOUT["detail_origin"][1], DAY_VIEW_ART + "detail.png")
		self.detailIcon = self.CreateEventImage(self, 29, 446, DAY_VIEW_ART + "icons/bonus_event_45.png")
		self.detailTitle = self.CreateEventText(self, 90, 444, "", DAY_SELECTED_TEXT_COLOR, width=340, font="large_bold")
		self.detailDescription = self.CreateEventText(self, 90, 470, "", width=334, font="body")
		self.detailDescription2 = self.CreateEventText(self, 90, 488, "", width=334, font="body")
		self.detailMeasure = self.CreateEventText(self, 0, 0, "", font="body")
		self.detailMeasure.Hide()
		self.detailBonus = self.CreateEventText(self, 90, 519, "", DAY_SELECTED_TEXT_COLOR, width=334, section=True)
		self.CreateEventBar(self, 444, 444, 1, 92, _Color(61, 48, 52))
		self.detailStatus = self.CreateEventText(self, 459, 444, "", width=165, section=True)
		self.detailClock = self.CreateEventImage(self, 458, 469, DAY_VIEW_ART + "clock_20.png")
		self.detailStart = self.CreateEventText(self, 484, 472, "", width=140)
		self.detailCountdown = self.CreateEventText(self, 459, 497, "", METADATA_TEXT_COLOR, width=165, font="small")
		self.detailMetadata = self.CreateEventText(self, 459, 525, "", METADATA_TEXT_COLOR, width=165, font="small")
		# The description opens full conditions; the original event icon opens active games.
		self.infoButton = self.__Button(90, 470, 334, "", self.__ShowSelectedTooltip)
		self.infoButton.SetSize(334, 36)
		self.infoButton.SetToolTipText(localeInfo.EVENT_CALENDAR_DETAILS)
		self.actionButton = self.__Button(29, 446, 45, "", self.__ActivateSelected)
		self.actionButton.SetSize(45, 45)
		self.actionButton.SetToolTipText(localeInfo.EVENT_CALENDAR_OPEN_EVENT)
		self.previousButton = self.__Button(16, 560, 120, localeInfo.EVENT_CALENDAR_PREVIOUS_DAY, self.__ChangeDay, -1)
		self.nextButton = self.__Button(513, 560, 120, localeInfo.EVENT_CALENDAR_NEXT_DAY, self.__ChangeDay, 1)
		self.todayButton = self.__Button(250, 560, 150, "", self.__SelectToday)
		self.previousButton.calendarLabel.SetPosition(2, 5)
		self.previousButton.calendarLabel.SetHorizontalAlignLeft()
		self.nextButton.calendarLabel.SetPosition(118, 5)
		self.nextButton.calendarLabel.SetHorizontalAlignRight()
		self.todayButton.calendarLabel.SetPackedFontColor(DAY_SELECTED_TEXT_COLOR)
		self.previousPage = self.__Button(142, 560, 24, "", self.__ChangePage, -1, CALENDAR_ARROW_LEFT)
		self.nextPage = self.__Button(232, 560, 24, "", self.__ChangePage, 1, CALENDAR_ARROW_RIGHT)
		self.pageLabel = self.CreateEventText(self, 199, 565, "", METADATA_TEXT_COLOR, "center", 62)

	def Open(self):
		self.Show()
		self.Refresh()
		self.SetTop()

	def Close(self):
		self.Hide()
		self.HideEventTooltip()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnMouseWheel(self, delta):
		if len(self.visibleEvents) <= self.PAGE_SIZE or not delta:
			return False
		self.__ChangePage(-1 if delta > 0 else 1)
		return True

	def OnUpdate(self):
		now = app.GetGlobalTimeStamp()
		if now != self.lastUpdate:
			self.lastUpdate = now
			self.Refresh()

	def GetEventState(self, row):
		return eventcalendarlogic.EventState(row[EVENT_START_TIME], row[EVENT_END_TIME],
			row[EVENT_IS_ACTIVE], app.GetGlobalTimeStamp())

	def __Duration(self, seconds, short=False):
		seconds = max(0, int(seconds))
		minutes, seconds = divmod(seconds, 60)
		hours, minutes = divmod(minutes, 60)
		return ((localeInfo.EVENT_CALENDAR_DURATION_HOURS_SHORT if short else localeInfo.EVENT_CALENDAR_DURATION_HOURS) % (hours, minutes) if hours else
			localeInfo.EVENT_CALENDAR_DURATION_MINUTES % minutes)

	def EventOrder(self, row):
		# Sort key of the day's rows: running first, then upcoming / scheduled / ended, each by id (R1 by start).
		priority = {"active":0, "upcoming":1, "scheduled":2, "ended":3}
		return (priority[self.GetEventState(row)], int(row[EVENT_ID]))

	def GetEventStatus(self, row):
		state = self.GetEventState(row)
		if state == "upcoming":
			if self.selectedDate > (self.anchorDate.year, self.anchorDate.month, self.anchorDate.day):
				return localeInfo.EVENT_CALENDAR_STATE_SCHEDULED
			return localeInfo.EVENT_CALENDAR_STARTS_IN % self.__Duration(row[EVENT_START_TIME] - app.GetGlobalTimeStamp(), short=True)
		return getattr(localeInfo, "EVENT_CALENDAR_STATE_" + state.upper())

	def Refresh(self):
		oldAnchor = self.anchorDate
		self.anchorDate = datetime.date.today()
		if oldAnchor != self.anchorDate and self.selectedDate == (oldAnchor.year, oldAnchor.month, oldAnchor.day):
			self.selectedDate = (self.anchorDate.year, self.anchorDate.month, self.anchorDate.day)
		if not eventcalendarlogic.IsDateAllowed(self.selectedDate, self.anchorDate):
			self.selectedDate = (self.anchorDate.year, self.anchorDate.month, self.anchorDate.day)
		self.currentYear, self.currentMonth = self.selectedDate[:2]
		year, month, day = self.selectedDate
		self.dateTitle.SetText(localeInfo.EVENT_CALENDAR_DATE % (
			getattr(localeInfo, "EVENT_CALENDAR_WEEKDAY_FULL_%d" % datetime.date(year, month, day).weekday()),
			day, getattr(localeInfo, "EVENT_CALENDAR_MONTH_DATE_%d" % month)))
		isToday = self.selectedDate == (self.anchorDate.year, self.anchorDate.month, self.anchorDate.day)
		self.todayButton.calendarLabel.SetText(localeInfo.EVENT_CALENDAR_TODAY_CLOCK %
			datetime.datetime.fromtimestamp(app.GetGlobalTimeStamp()).strftime("%H:%M") if isToday else localeInfo.EVENT_CALENDAR_BACK_TODAY)
		for button, offset in ((self.previousButton, -1), (self.nextButton, 1)):
			target = datetime.date(*self.selectedDate) + datetime.timedelta(days=offset)
			allowed = eventcalendarlogic.IsDateAllowed((target.year, target.month, target.day), self.anchorDate)
			button.Enable() if allowed else button.Disable()
		rows = [row for dayRows in server_event_data.values() for row in dayRows.values()]
		self.visibleEvents = eventcalendarlogic.EventsForDay(rows, self.selectedDate, EVENT_START_TIME, EVENT_END_TIME)
		self.visibleEvents.sort(key=self.EventOrder)
		# A status transition may move the selected row into another page.
		for index, row in enumerate(self.visibleEvents):
			if row[EVENT_ID] == self.selectedEventID:
				self.eventPage = index // self.PAGE_SIZE
				break
		self.__RefreshWeek(rows)
		count = self.GetEventCount(len(self.visibleEvents))
		if self.selectedDate == (self.anchorDate.year, self.anchorDate.month, self.anchorDate.day):
			count = localeInfo.EVENT_CALENDAR_TODAY_COUNT % count
		self.dayCount.SetText(count)
		self.eventPage, first, last, pages = eventcalendarlogic.PageBounds(len(self.visibleEvents), self.eventPage, self.PAGE_SIZE)
		current = self.visibleEvents[first:last]
		if not any(row[EVENT_ID] == self.selectedEventID for row in current):
			self.selectedEventID = current[0][EVENT_ID] if current else None
		for index, widget in enumerate(self.eventRows):
			if index < len(current):
				row = current[index]
				widget.SetEvent(row, row[EVENT_ID] == self.selectedEventID)
			else:
				widget.eventData = None
				widget.Hide()
		self.emptyDay.Hide() if current else self.emptyDay.Show()
		self.pageLabel.SetText("%d / %d" % (self.eventPage + 1, pages))
		for widget in (self.previousPage, self.nextPage, self.pageLabel):
			widget.Show() if pages > 1 else widget.Hide()
		self.previousPage.Enable() if self.eventPage > 0 else self.previousPage.Disable()
		self.nextPage.Enable() if self.eventPage + 1 < pages else self.nextPage.Disable()
		self.__RefreshDetail()

	def SelectEvent(self, eventID):
		self.selectedEventID = eventID
		self.Refresh()

	def SelectDate(self, dateKey):
		if eventcalendarlogic.IsDateAllowed(dateKey, self.anchorDate):
			self.selectedDate = tuple(dateKey)
			self.eventPage = 0
			self.selectedEventID = None
			self.HideEventTooltip()
			self.Refresh()

	def GetEventCount(self, count):
		key = "SINGLE" if count == 1 else "FEW" if count in (2, 3, 4) else "MANY"
		return getattr(localeInfo, "EVENT_CALENDAR_COUNT_" + key) % count

	def __RefreshWeek(self, rows):
		for widget, date in zip(self.weekDays, eventcalendarlogic.WeekDates(self.selectedDate)):
			count = len(eventcalendarlogic.EventsForDay(rows, date, EVENT_START_TIME, EVENT_END_TIME))
			widget.SetDate(date, count, date == self.selectedDate,
				date == (self.anchorDate.year, self.anchorDate.month, self.anchorDate.day),
				eventcalendarlogic.IsDateAllowed(date, self.anchorDate))
		for button, offset in ((self.previousWeek, -1), (self.nextWeek, 1)):
			allowed = eventcalendarlogic.ShiftWeek(self.selectedDate, offset, self.anchorDate) is not None
			button.Enable() if allowed else button.Disable()
			button.calendarGlyph.SetAlpha(1.0 if allowed else 0.35)

	def __ChangeWeek(self, offset):
		target = eventcalendarlogic.ShiftWeek(self.selectedDate, offset, self.anchorDate)
		if target is not None:
			self.SelectDate(target)

	def __ChangeDay(self, offset):
		target = datetime.date(*self.selectedDate) + datetime.timedelta(days=int(offset))
		self.SelectDate((target.year, target.month, target.day))

	def __SelectToday(self):
		today = datetime.date.today()
		self.anchorDate = today
		self.SelectDate((today.year, today.month, today.day))

	def __ChangePage(self, offset):
		self.eventPage += int(offset)
		self.selectedEventID = None
		self.HideEventTooltip()
		self.Refresh()

	def __SelectedEvent(self):
		return GetEventIDData(self.selectedEventID) if self.selectedEventID is not None else None

	def __RefreshDetail(self):
		row = self.__SelectedEvent()
		widgets = (self.detailIcon, self.detailTitle, self.detailDescription, self.detailDescription2,
			self.detailBonus, self.detailMetadata, self.detailStatus, self.detailStart,
			self.detailClock, self.detailCountdown, self.infoButton)
		for widget in widgets:
			widget.Show() if row else widget.Hide()
		self.actionButton.Hide()
		if not row:
			return
		key = _GetEventDefinition(row[EVENT_INDEX])[0].upper()
		self.detailIcon.LoadImage(self.GetIconPath(row, 45))
		name = self.GetEventName(row)
		self.detailTitle.SetText(name)
		self.detailBonus.SetText(self.GetEventBonus(row))
		description = getattr(localeInfo, "EVENT_CALENDAR_DESC_" + key, localeInfo.EVENT_CALENDAR_DESC_DEFAULT)
		words = description.split("|", 1)[0].split()
		line = []
		while words:
			self.detailMeasure.SetText(" ".join(line + words[:1]))
			if line and self.detailMeasure.GetTextSize()[0] > 334:
				break
			line.append(words.pop(0))
		self.detailDescription.SetText(" ".join(line))
		self.detailDescription2.SetText(description.split("|", 1)[1] if "|" in description else " ".join(words))
		self.detailMetadata.SetText(self.GetEventMetadata(row))
		state = self.GetEventState(row)
		self.detailStatus.SetText(self.GetEventStatus(row))
		self.detailStatus.SetPackedFontColor(DAY_TODAY_TEXT_COLOR if state == "active" else
			METADATA_TEXT_COLOR if state == "ended" else TIME_TEXT_COLOR)
		self.detailStart.SetText(self.GetEventTimeLabel(row))
		now = app.GetGlobalTimeStamp()
		countdown = ""
		if state == "active" and int(row[EVENT_END_TIME]) > int(row[EVENT_START_TIME]):
			countdown = localeInfo.EVENT_CALENDAR_ENDS_IN % self.__Duration(row[EVENT_END_TIME] - now)
		elif state == "upcoming":
			countdown = localeInfo.EVENT_CALENDAR_STARTS_IN % self.__Duration(row[EVENT_START_TIME] - now)
		elif state == "ended":
			countdown = localeInfo.EVENT_CALENDAR_ENDED_AGO % self.__Duration(now - row[EVENT_END_TIME])
		self.detailCountdown.SetText(countdown)
		if self.__CanActivate(row):
			self.actionButton.Show()

	def __CanActivate(self, row):
		if self.GetEventState(row) != "active":
			return False
		eventIndex = row[EVENT_INDEX]
		return (eventIndex in (player.OKEY_CARD_EVENT, player.CATCH_KING_EVENT) or
			(app.ENABLE_KINGDOMS_WAR and eventIndex == player.KINGDOMS_WAR_EVENT) or
			(app.ENABLE_WHEEL_OF_FORTUNE and eventIndex == player.WHEEL_FORTUNE_EVENT))

	def __ShowSelectedTooltip(self):
		row = self.__SelectedEvent()
		if row:
			self.ShowEventTooltip(row)

	def __ActivateSelected(self):
		row = self.__SelectedEvent()
		if row and self.__CanActivate(row):
			self.ActivateEvent(row[EVENT_INDEX])

	def __FilteredEvents(self, values):
		return sorted(values, key=lambda row: (int(row[EVENT_START_TIME]), int(row[EVENT_ID])))

	def ActivateEvent(self, eventIndex):
		self.OnClick(eventIndex)


	def OnClick(self, eventIndex):
		interface = osfInfo.GetInterfaceInstance()
		if app.ENABLE_WHEEL_OF_FORTUNE and player.WHEEL_FORTUNE_EVENT == eventIndex:
			if interface:
				interface.OpenWheelofFortune()
		elif player.KINGDOMS_WAR_EVENT == eventIndex:
			import event
			event.QuestButtonClick(int(osfInfo.KINGDOMS_TP))
		elif player.CATCH_KING_EVENT == eventIndex:
			if interface:
				interface.ClickCatchKingEventButton()
		elif player.OKEY_CARD_EVENT == eventIndex:
			if interface and interface.wndCardsInfo.IsShow():
				interface.wndCardsInfo.Close()
			elif interface:
				interface.wndCardsInfo.Open()

	def GetIconPath(self, eventData, size, ended=False):
		name = _GetEventDefinition(eventData[EVENT_INDEX])[0]
		if name not in CALENDAR_LAYOUT["icons"]:
			name = "bonus_event"
		return DAY_VIEW_ART + "icons/%s%s_%d.png" % (name, "_ended" if ended else "", size)

	def GetEventName(self, eventData):
		definition = _GetEventDefinition(eventData[EVENT_INDEX])
		return definition[1] or localeInfo.EVENT_CALENDAR_NAME_BONUS

	def GetEventBonus(self, eventData):
		key = _GetEventDefinition(eventData[EVENT_INDEX])[0].upper()
		if eventData[EVENT_INDEX] == player.BONUS_EVENT:
			if eventData[EVENT_VALUE0] <= 0 or eventData[EVENT_VALUE1] <= 0:
				return ""
			return self.__GetBonusName(eventData[EVENT_VALUE0], eventData[EVENT_VALUE1])
		template = getattr(localeInfo, "EVENT_CALENDAR_BONUS_" + key, "")
		return template % eventData[EVENT_VALUE0] if "%d" in template else template

	def GetEventMetadata(self, eventData):
		empireTexts = (
			localeInfo.ALL_KINGDOMS, localeInfo.RED_KINGDOM,
			localeInfo.YELLOW_KINGDOM, localeInfo.BLUE_KINGDOM)
		empireIndex = int(eventData[EVENT_EMPIRE_FLAG])
		if empireIndex < 0 or empireIndex >= len(empireTexts):
			empireIndex = 0
		if int(eventData[EVENT_CHANNEL_FLAG]) == 0:
			channel = localeInfo.ALL_CHANNEL
		else:
			channel = localeInfo.ONLY_CHANNEL % eventData[EVENT_CHANNEL_FLAG]
		return localeInfo.EVENT_CALENDAR_METADATA % (empireTexts[empireIndex], channel.lower())

	def GetEventTimeLabel(self, eventData):
		startText = str(eventData[EVENT_START_TEXT] or "")
		endText = str(eventData[EVENT_END_TEXT] or "")
		startClock = startText.split(" ")[-1][:5] if startText else "--:--"
		invalidEnd = not endText or endText.startswith("1970-01-01")
		if invalidEnd:
			return startClock
		endClock = endText.split(" ")[-1][:5]
		return localeInfo.EVENT_CALENDAR_TIME_RANGE % (startClock, endClock)

	def ShowDateTooltip(self, dateKey):
		interface = osfInfo.GetInterfaceInstance()
		if not interface or not interface.tooltipItem:
			return
		tooltip = interface.tooltipItem
		tooltip.ClearToolTip()
		tooltip.AppendTextLine(localeInfo.EVENT_TOOLTIP_TITLE % self.__textToColorFull(
			"%04d-%02d-%02d" % dateKey))
		tooltip.AppendSpace(5)
		rows = [row for dayRows in server_event_data.values() for row in dayRows.values()]
		events = self.__FilteredEvents(eventcalendarlogic.EventsForDay(rows, dateKey, EVENT_START_TIME, EVENT_END_TIME))
		if not events:
			tooltip.AppendTextLine(
				getattr(localeInfo, "EVENT_CALENDAR_EMPTY_DAY", localeInfo.EVENT_TOOLTIP_DOESNT_HAVE_EVENT),
				tooltip.NEGATIVE_COLOR)
		for eventData in events:
			self.__AppendEventTooltip(tooltip, eventData)
		tooltip.ShowToolTip()

	def ShowEventTooltip(self, eventData):
		interface = osfInfo.GetInterfaceInstance()
		if not interface or not interface.tooltipItem:
			return
		tooltip = interface.tooltipItem
		tooltip.ClearToolTip()
		self.__AppendEventTooltip(tooltip, eventData)
		tooltip.ShowToolTip()

	def HideEventTooltip(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.tooltipItem:
			interface.tooltipItem.HideToolTip()

	def OverInItem(self, dayIndex):
		if isinstance(dayIndex, tuple):
			dateKey = dayIndex
		else:
			dateKey = (self.currentYear, self.currentMonth, int(dayIndex))
		self.ShowDateTooltip(dateKey)

	def __AppendEventTooltip(self, tooltip, eventData):
		tooltip.AppendTextLine(self.__textToColorFull(self.GetEventName(eventData)))
		bonus = self.GetEventBonus(eventData)
		if bonus:
			tooltip.AppendTextLine(bonus)
		if app.ENABLE_KINGDOMS_WAR and eventData[EVENT_INDEX] == player.KINGDOMS_WAR_EVENT:
			tooltip.AppendTextLine(self.__textToColorFull(
				self.__GetKingdomsWarLevelDescription(
					eventData[EVENT_VALUE0], eventData[EVENT_VALUE1])))
			self.__AppendKingdomsWarRewardToolTipLines(
				tooltip, eventData[EVENT_VALUE2], eventData[EVENT_VALUE3])
			self.__AppendKingdomsWarWinnerPrivTooltipLines(
				tooltip, eventData[EVENT_VALUE4], eventData[EVENT_VALUE5],
				eventData[EVENT_VALUE6], eventData[EVENT_VALUE7])
		tooltip.AppendTextLine(self.GetEventMetadata(eventData))
		tooltip.AppendTextLine(self.__CalculateTime(
			eventData[EVENT_INDEX], eventData[EVENT_START_TEXT],
			eventData[EVENT_END_TEXT], eventData[EVENT_END_TIME]))
		tooltip.AppendSpace(8)

	def __textToColorFull(self, text):
		return localeInfo.EVENT_COLORFULL_TEXT % text

	def __GetBonusName(self, affect, value):
		return GET_AFFECT_STRING(affect, value)

	def __CalculateTime(self, eventIndex, startTimeText, endTimeText, endTime):
		invalidEndValues = (
			"1970-01-01 03:00:00", "1970-01-01 02:00:00",
			"1970-01-01 01:00:00", "1970-01-01 00:00:00", "")
		if endTimeText in invalidEndValues:
			parts = startTimeText.split(" ")
			startClock = parts[1] if len(parts) > 1 else startTimeText
			return localeInfo.PVP_EVENT_TIME % self.__textToColorFull(startClock)
		startParts = startTimeText.split(" ")
		endParts = endTimeText.split(" ")
		if len(startParts) < 2 or len(endParts) < 2:
			return self.__textToColorFull(self.GetEventTimeLabel([
				0, 0, eventIndex, startTimeText, endTimeText, 0, 0,
				0, 0, 0, 0, 0, 0, 0, 0, 0, endTime, False]))
		startDate, startClock = startParts[0], startParts[1]
		endDate, endClock = endParts[0], endParts[1]
		if startDate != endDate:
			startClock = "/".join(reversed(startDate.split("-")[1:])) + " " + startClock
			endClock = "/".join(reversed(endDate.split("-")[1:])) + " " + endClock
		return localeInfo.NORMAL_EVENT_TIME % (
			self.__textToColorFull(startClock), self.__textToColorFull(endClock))

	def __GetMonthName(self, monthIndex):
		return {
			1: localeInfo.EVENT_MONTH_1, 2: localeInfo.EVENT_MONTH_2,
			3: localeInfo.EVENT_MONTH_3, 4: localeInfo.EVENT_MONTH_4,
			5: localeInfo.EVENT_MONTH_5, 6: localeInfo.EVENT_MONTH_6,
			7: localeInfo.EVENT_MONTH_7, 8: localeInfo.EVENT_MONTH_8,
			9: localeInfo.EVENT_MONTH_9, 10: localeInfo.EVENT_MONTH_10,
			11: localeInfo.EVENT_MONTH_11, 12: localeInfo.EVENT_MONTH_12,
		}.get(monthIndex, "Unknown Month")

	def __GetKingdomsWarLevelDescription(self, value0, value1):
		minLevel, maxLevel = int(value0), int(value1)
		if minLevel > 0 and maxLevel > 0:
			return getattr(localeInfo, "KINGDOMS_WAR_EVENT_LEVELS_MINMAX", "Levels %d - %d") % (minLevel, maxLevel)
		if minLevel > 0:
			return getattr(localeInfo, "KINGDOMS_WAR_EVENT_LEVEL_MIN", "Min. level %d") % minLevel
		if maxLevel > 0:
			return getattr(localeInfo, "KINGDOMS_WAR_EVENT_LEVEL_MAX", "Max. level %d") % maxLevel
		return getattr(localeInfo, "KINGDOMS_WAR_EVENT_LEVEL_ANY", "All levels")

	def __FormatKingdomsWarYangValue(self, amount):
		try:
			return localeInfo.NumberToMoneyString(int(amount))
		except BaseException:
			return str(int(amount))

	def __AppendKingdomsWarRewardToolTipLines(self, tooltip, value2, value3):
		if int(value2) > 0:
			fmt = getattr(localeInfo, "KINGDOMS_WAR_EVENT_REWARD_PARTICIPANTS", "Participation reward: %s Yang")
			tooltip.AppendTextLine(self.__textToColorFull(fmt % self.__FormatKingdomsWarYangValue(value2)))
		if int(value3) > 0:
			fmt = getattr(localeInfo, "KINGDOMS_WAR_EVENT_REWARD_WINNER", "Reward winner kingdoms: %s Yang")
			tooltip.AppendTextLine(self.__textToColorFull(fmt % self.__FormatKingdomsWarYangValue(value3)))

	def __AppendKingdomsWarWinnerPrivTooltipLines(self, tooltip, value4, value5, value6, value7):
		hours = int(value7)
		definitions = (
			(int(value4), "KINGDOMS_WAR_EVENT_WINNER_EXP_ONLY", "Winner kingdom: +%d%% EXP"),
			(int(value5), "KINGDOMS_WAR_EVENT_WINNER_ITEM", "Winner kingdom: +%d%% item drop"),
			(int(value6), "KINGDOMS_WAR_EVENT_WINNER_GOLD", "Winner kingdom: +%d%% gold drop"),
		)
		for value, localeKey, fallback in definitions:
			if value <= 0:
				continue
			line = getattr(localeInfo, localeKey, fallback) % value
			if hours > 0:
				line += getattr(localeInfo, "KINGDOMS_WAR_EVENT_WINNER_HOURS_SUFFIX", " (%dh)") % hours
			tooltip.AppendTextLine(self.__textToColorFull(line))


class MovableImage(ImageBoxSpecial):
	def __del__(self):
		ImageBoxSpecial.__del__(self)

	def Destroy(self):
		self.window = None
		self.eventCache = []
		self.timeList = []
		self.timeText = None
		ImageBoxSpecial.Destroy(self)

	def __init__(self):
		self.Destroy()
		ImageBoxSpecial.__init__(self, True)

		window = ui.Window()
		window.SetParent(self)
		window.AddFlag("not_pick")
		window.OnUpdate = ui.__mem_func__(self.OnUpdate)
		window.Show()
		self.window = window

		timeText = ui.TextLine()
		timeText.SetParent(self)
		timeText.AddFlag("not_pick")
		timeText.SetHorizontalAlignCenter()
		timeText.SetPosition(43, 70)
		timeText.SetOutline()
		timeText.Show()
		self.timeText = timeText

		timeTextEx = ui.TextLine()
		timeTextEx.SetParent(self)
		timeTextEx.AddFlag("not_pick")
		timeTextEx.SetHorizontalAlignCenter()
		timeTextEx.SetPosition(43, 90)
		#timeTextEx.SetText(localeInfo.BONUS_NEXT_EVENT)
		timeTextEx.SetOutline()
		timeTextEx.Show()
		self.timeTextEx = timeTextEx

	def Clear(self):
		self.eventCache = []
		self.timeList = []
		self.timeText.SetText("")
		self.timeTextEx.Hide()
		ImageBoxSpecial.Clear(self)
		self.Hide()

	def Refresh(self):
		self.Clear()
		for dayIndex, eventList in server_event_data.items():
			for eventID, eventData in eventList.items():
				self.AppendEvent(eventData[EVENT_ID], eventData[EVENT_START_TIME], eventData[EVENT_END_TIME], eventData[EVENT_IS_ACTIVE])

	def LoadTime(self, eventID, startTime, endTime, isAlreadyStart):
		self.AppendImage(eventID)
		self.timeList.append([startTime, endTime, isAlreadyStart])

		if len(self.timeList) > 1:
			self.timeTextEx.Show()
		else:
			self.timeTextEx.Hide()
		self.Show()

	def CheckCacheEvent(self):
		if len(self.eventCache) == 0:
			return
		clientGlobalTime = app.GetGlobalTimeStamp()
		for j in range(len(self.eventCache)):
			startTime = self.eventCache[j][1] - clientGlobalTime
			endTime = self.eventCache[j][2] - clientGlobalTime
			if startTime >= 0 and startTime <= (60*30):
				self.Refresh()
				return

	def AppendEvent(self, eventID, startTime, endTime, isAlreadyStart):
		clientGlobalTime = app.GetGlobalTimeStamp()

		newStartTime = startTime
		newEndTime = endTime
		if newStartTime != 0:
			newStartTime -= clientGlobalTime
		if newEndTime != 0:
			newEndTime -= clientGlobalTime

		if (startTime != 0 and newStartTime <= 0 and endTime == startTime and isAlreadyStart == True) or (startTime != 0 and newStartTime <= 0 and endTime == 0 and isAlreadyStart == True):
			self.LoadTime(eventID, startTime, endTime, 2)
		elif newStartTime <= 0 and newEndTime <= 0:
			return
		elif newStartTime > 0 and newStartTime <= (60*30):#start-in
			self.LoadTime(eventID, startTime, endTime, 0)
		elif newEndTime > 0 and isAlreadyStart == True:#end-in
			self.LoadTime(eventID, startTime, endTime, 1)
		else:
			self.eventCache.append([eventID, startTime, endTime, isAlreadyStart])

		if len(self.timeList) > 1:
			self.timeTextEx.Show()
		else:
			self.timeTextEx.Hide()

	def DeleteEvent(self, index):
		self.DeleteImage(index)
		del self.timeList[index]

		if len(self.timeList) <= 1:
			self.timeTextEx.Hide()

	def FormatTime(self, seconds):
		if seconds == 0:
			return ""
		m, s = divmod(seconds, 60)
		h, m = divmod(m, 60)
		return "%02dh %02dm %02ds" % (h, m, s)

	def OnUpdate(self):
		ImageBoxSpecial.OnUpdate(self)
		self.CheckCacheEvent()

		if self.imageIndex < len(self.timeList):
			timeData = self.timeList[self.imageIndex]

			if timeData[2] == 0:
				leftTime = timeData[0] - app.GetGlobalTimeStamp()
				if leftTime > 0:
					self.timeText.SetText(localeInfo.BONUS_START_IN%self.FormatTime(leftTime))

					if not self.timeText.IsShow():
						self.timeText.Show()

			elif timeData[2] == 1:
				leftTime = timeData[1] - app.GetGlobalTimeStamp()
				if leftTime > 0:
					self.timeText.SetText(localeInfo.BONUS_END_IN%self.FormatTime(leftTime))
					if not self.timeText.IsShow():
						self.timeText.Show()

			elif timeData[2] == 2:
				if self.timeText.IsShow():
					self.timeText.Hide()
