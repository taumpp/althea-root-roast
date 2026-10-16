# -*- coding: utf-8 -*-

import app
import fontconfig
import item
import localeInfo
import ui
import wndMgr


GENERIC_MAX_WIDTH = 448
GENERIC_HEIGHT = 94
SALE_MAX_WIDTH = 420
SALE_HEIGHT = 64
MIN_WIDTH = 300
TARGET_X = 16
BOTTOM_MARGIN = 124
SCREEN_MARGIN = 12
MOTION_SECONDS = 0.18
DISPLAY_SECONDS = 7.0
MAX_QUEUE = 20
SALE_IDENTITY_LRU_SIZE = 128

PANEL_COLOR = 0xf20b0a0a
SALE_PANEL_COLOR = 0xf509090a
HEADER_COLOR = 0xe01c1113
ACCENT_COLOR = 0xffc02643
GOLD_COLOR = 0xffcfb16d
SALE_GOLD_RULE_COLOR = 0xff846641
TEXT_COLOR = 0xffebe7e0
ICON_BACK_COLOR = 0xe0141111
SALE_ICON_BACK_COLOR = 0xee110d0e
PROGRESS_BACK_COLOR = 0xff241416
BORDER_COLOR = 0xff6b4038
SALE_BORDER_COLOR = 0xff533e35
SALE_PROGRESS_BACK_COLOR = 0xff281316


def _Bar(parent, x, y, width, height, color):
	bar = ui.Bar()
	bar.SetParent(parent)
	bar.SetPosition(x, y)
	bar.SetSize(width, height)
	bar.SetColor(color)
	bar.AddFlag("not_pick")
	bar.Show()
	return bar


def _Text(parent, x, y, color):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	line.SetPackedFontColor(color)
	line.SetOutline()
	line.AddFlag("not_pick")
	line.Show()
	return line


def _MoneyText(value):
	text = localeInfo.NumberToMoneyString(value)
	unit = getattr(localeInfo, "MONETARY_UNIT0", "Yang")
	if unit and unit not in text:
		return "%s %s" % (text, unit)
	return text


class GameNotificationManager(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag("float")
		self.queue = []
		self.active = None
		self.state = "idle"
		self.motionStarted = 0.0
		self.motionFromX = 0
		self.motionToX = TARGET_X
		self.endTime = 0.0
		self.currentKind = "generic"
		self.currentHeight = GENERIC_HEIGHT
		self.currentWidth = self._ResponsiveWidth()
		self.lastScreenWidth = wndMgr.GetScreenWidth()
		self.seenSaleIdentities = []
		self.seenSaleIdentitySet = set()
		self.SetSize(self.currentWidth, self.currentHeight)
		self._Build()
		self._Layout("generic")
		self.SetPosition(-self.currentWidth, self._TargetY())
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def _MaxWidth(self):
		return SALE_MAX_WIDTH if self.currentKind == "sale" else GENERIC_MAX_WIDTH

	def _ResponsiveWidth(self):
		available = max(MIN_WIDTH, wndMgr.GetScreenWidth() - TARGET_X - SCREEN_MARGIN)
		return min(self._MaxWidth(), available)

	def _TargetY(self):
		return max(110, wndMgr.GetScreenHeight() - BOTTOM_MARGIN - self.currentHeight)

	def _ProgressGeometry(self):
		if self.currentKind == "sale":
			return 5, self.currentHeight - 3, self.currentWidth - 8
		return 4, self.currentHeight - 4, self.currentWidth - 8

	def _Build(self):
		self.panel = _Bar(self, 1, 1, 1, 1, PANEL_COLOR)
		self.borderTop = _Bar(self, 0, 0, 1, 1, BORDER_COLOR)
		self.borderBottom = _Bar(self, 0, 0, 1, 1, BORDER_COLOR)
		self.borderLeft = _Bar(self, 0, 0, 1, 1, BORDER_COLOR)
		self.borderRight = _Bar(self, 0, 0, 1, 1, BORDER_COLOR)
		self.header = _Bar(self, 3, 3, 1, 24, HEADER_COLOR)
		self.topLine = _Bar(self, 7, 6, 1, 1, GOLD_COLOR)
		self.accent = _Bar(self, 0, 0, 3, 1, ACCENT_COLOR)
		self.divider = _Bar(self, 14, 28, 1, 1, 0xff3b1719)
		self.iconFrame = _Bar(self, 10, 10, 44, 44, SALE_GOLD_RULE_COLOR)
		self.iconBack = _Bar(self, 18, 35, 42, 42, ICON_BACK_COLOR)
		self.progressBack = _Bar(self, 4, 1, 1, 2, PROGRESS_BACK_COLOR)
		self.progress = _Bar(self, 4, 1, 1, 2, ACCENT_COLOR)

		self.iconImage = ui.ExpandedImageBox()
		self.iconImage.SetParent(self)
		self.iconImage.AddFlag("not_pick")
		self.iconImage.Hide()

		self.titleLine = _Text(self, 74, 10, GOLD_COLOR)
		self.messageLine = _Text(self, 74, 50, TEXT_COLOR)
		self.priceLine = _Text(self, 0, 31, GOLD_COLOR)
		self.priceLine.SetHorizontalAlignRight()
		self.priceLine.Hide()

	def _Layout(self, kind=None):
		if kind is not None:
			self.currentKind = kind
		self.currentHeight = SALE_HEIGHT if self.currentKind == "sale" else GENERIC_HEIGHT
		self.currentWidth = self._ResponsiveWidth()
		self.SetSize(self.currentWidth, self.currentHeight)
		self.panel.SetPosition(1, 1)
		self.panel.SetSize(self.currentWidth - 2, self.currentHeight - 2)
		self.panel.SetColor(PANEL_COLOR)
		self.borderTop.SetPosition(0, 0)
		self.borderTop.SetSize(self.currentWidth, 1)
		self.borderBottom.SetPosition(0, self.currentHeight - 1)
		self.borderBottom.SetSize(self.currentWidth, 1)
		self.borderLeft.SetPosition(0, 0)
		self.borderLeft.SetSize(1, self.currentHeight)
		self.borderRight.SetPosition(self.currentWidth - 1, 0)
		self.borderRight.SetSize(1, self.currentHeight)
		for border in (self.borderTop, self.borderBottom,
				self.borderLeft, self.borderRight):
			border.SetColor(BORDER_COLOR)
		self.accent.SetPosition(0, 0)
		self.accent.SetSize(3, self.currentHeight)
		self.progressBack.SetColor(PROGRESS_BACK_COLOR)

		progressX, progressY, progressWidth = self._ProgressGeometry()
		self.progressBack.SetPosition(progressX, progressY)
		self.progressBack.SetSize(progressWidth, 2)
		self.progress.SetPosition(progressX, progressY)
		self.progress.SetSize(progressWidth, 2)

		if self.currentKind == "sale":
			self.header.Hide()
			self.divider.Hide()
			self.panel.SetPosition(4, 1)
			self.panel.SetSize(self.currentWidth - 5, self.currentHeight - 2)
			self.panel.SetColor(SALE_PANEL_COLOR)
			self.borderTop.SetPosition(4, 1)
			self.borderTop.SetSize(self.currentWidth - 5, 1)
			self.borderBottom.SetPosition(4, self.currentHeight - 2)
			self.borderBottom.SetSize(self.currentWidth - 5, 1)
			self.borderLeft.SetPosition(4, 1)
			self.borderLeft.SetSize(1, self.currentHeight - 2)
			self.borderRight.SetPosition(self.currentWidth - 2, 1)
			self.borderRight.SetSize(1, self.currentHeight - 2)
			for border in (self.borderTop, self.borderBottom,
					self.borderLeft, self.borderRight):
				border.SetColor(SALE_BORDER_COLOR)
			self.accent.SetSize(4, self.currentHeight)
			self.topLine.SetPosition(5, 4)
			self.topLine.SetSize(self.currentWidth - 8, 1)
			self.topLine.SetColor(SALE_GOLD_RULE_COLOR)
			self.topLine.Show()
			self.iconFrame.SetPosition(10, 10)
			self.iconFrame.SetSize(44, 44)
			self.iconFrame.SetColor(SALE_GOLD_RULE_COLOR)
			self.iconFrame.Show()
			self.iconBack.SetPosition(11, 11)
			self.iconBack.SetSize(42, 42)
			self.iconBack.SetColor(SALE_ICON_BACK_COLOR)
			self.progressBack.SetColor(SALE_PROGRESS_BACK_COLOR)
			self.titleLine.SetPosition(66, 10)
			# Palette roles follow the player's font size; the former fixed
			# Tahoma 10 bold merged capital diacritics under the outline.
			self.titleLine.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_SECTION))
			self.titleLine.SetPackedFontColor(GOLD_COLOR)
			self.titleLine.SetLimitWidth(self.currentWidth - 92)
			self.messageLine.SetPosition(66, 31)
			self.messageLine.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL))
			self.messageLine.SetPackedFontColor(TEXT_COLOR)
			self.messageLine.SetLimitWidth(max(80, self.currentWidth - 217))
			self.priceLine.SetPosition(self.currentWidth - 12, 31)
			self.priceLine.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL))
			self.priceLine.SetPackedFontColor(GOLD_COLOR)
			self.priceLine.SetLimitWidth(min(139, max(90, self.currentWidth - 281)))
			self.priceLine.Show()
			return

		self.header.SetPosition(3, 3)
		self.header.SetSize(self.currentWidth - 6, 24)
		self.header.Show()
		self.topLine.SetPosition(7, 6)
		self.topLine.SetSize(self.currentWidth - 14, 1)
		self.topLine.SetColor(GOLD_COLOR)
		self.topLine.Show()
		self.divider.SetPosition(14, 28)
		self.divider.SetSize(self.currentWidth - 28, 1)
		self.divider.Show()
		self.iconFrame.Hide()
		self.iconBack.SetPosition(18, 35)
		self.iconBack.SetSize(42, 42)
		self.iconBack.SetColor(ICON_BACK_COLOR)
		self.titleLine.SetPosition(74, 10)
		self.titleLine.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL))
		self.titleLine.SetPackedFontColor(GOLD_COLOR)
		self.titleLine.SetLimitWidth(self.currentWidth - 92)
		self.messageLine.SetPosition(74, 50)
		self.messageLine.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
		self.messageLine.SetPackedFontColor(TEXT_COLOR)
		self.messageLine.SetLimitWidth(self.currentWidth - 92)
		self.priceLine.Hide()

	def _LoadItemIcon(self, iconVnum):
		if self.currentKind == "sale":
			slotX, slotY, slotSize = 10, 10, 44
		else:
			slotX, slotY, slotSize = 18, 35, 42
		try:
			item.SelectItem(int(iconVnum))
			filename = item.GetIconImageFileName()
			if not filename:
				raise RuntimeError("empty icon")
			self.iconImage.SetScale(1.0, 1.0)
			self.iconImage.LoadImage(filename)
			width = max(1, self.iconImage.GetWidth())
			height = max(1, self.iconImage.GetHeight())
			scale = min(1.0, 32.0 / float(max(width, height)))
			self.iconImage.SetScale(scale, scale)
			renderWidth = max(1, int(width * scale))
			renderHeight = max(1, int(height * scale))
			self.iconImage.SetPosition(
				slotX + (slotSize - renderWidth) // 2,
				slotY + (slotSize - renderHeight) // 2,
			)
			self.iconImage.Show()
			return True
		except:
			self.iconImage.Hide()
			return False

	def _Append(self, notification):
		if self.state == "idle":
			self._Show(notification)
			return True
		self.queue.append(notification)
		if len(self.queue) > MAX_QUEUE:
			del self.queue[:len(self.queue) - MAX_QUEUE]
		return True

	def Add(self, title, message, iconVnum=0):
		return self._Append({
			"kind": "generic",
			"title": title,
			"message": message,
			"iconVnum": int(iconVnum),
		})

	def AddDungeon(self, title, message, bossVnum):
		return self._Append({
			"kind": "generic", "title": title, "message": message,
			"iconVnum": 0, "bossVnum": int(bossVnum),
		})

	def _LoadDungeonPortrait(self, bossVnum):
		try:
			self.iconImage.SetScale(1.0, 1.0)
			self.iconImage.LoadImage(
				"d:/ymir work/ui/game/crimson_ember/dungeon_teleport/portrait/%d_67x52.png" % bossVnum)
			width = max(1, self.iconImage.GetWidth())
			height = max(1, self.iconImage.GetHeight())
			scale = min(42.0 / width, 42.0 / height, 1.0)
			self.iconImage.SetScale(scale, scale)
			self.iconImage.SetPosition(18 + int((42 - width * scale) / 2),
				35 + int((42 - height * scale) / 2))
			self.iconImage.Show()
		except (RuntimeError, OSError):
			self.iconImage.Hide()

	def AddSale(self, transactionHigh, transactionLow, listingId, iconVnum,
			count, totalPrice):
		try:
			transactionHigh = int(transactionHigh)
			transactionLow = int(transactionLow)
			listingId = int(listingId)
			iconVnum = int(iconVnum)
			count = int(count)
			totalPrice = int(totalPrice)
			if transactionHigh < 0 or transactionHigh > 0xffffffffffffffff:
				return False
			if transactionLow < 0 or transactionLow > 0xffffffffffffffff:
				return False
			if transactionHigh == 0 and transactionLow == 0:
				return False
			if listingId <= 0 or listingId > 0xffffffffffffffff:
				return False
			if iconVnum <= 0 or iconVnum > 0xffffffff:
				return False
			if count <= 0 or count > 0xffff:
				return False
			if totalPrice < 0 or totalPrice > 0x7fffffffffffffff:
				return False

			identity = (transactionHigh, transactionLow, listingId)
			if identity in self.seenSaleIdentitySet:
				self.seenSaleIdentities.remove(identity)
				self.seenSaleIdentities.append(identity)
				return False

			itemName = item.GetItemNameByVnum(iconVnum)
			item.SelectItem(iconVnum)
			iconFilename = item.GetIconImageFileName()
			if not itemName or not iconFilename:
				return False
		except:
			return False

		self.seenSaleIdentities.append(identity)
		self.seenSaleIdentitySet.add(identity)
		if len(self.seenSaleIdentities) > SALE_IDENTITY_LRU_SIZE:
			evicted = self.seenSaleIdentities.pop(0)
			self.seenSaleIdentitySet.discard(evicted)

		return self._Append({
			"kind": "sale",
			"transactionHigh": transactionHigh,
			"transactionLow": transactionLow,
			"listingId": listingId,
			"iconVnum": iconVnum,
			"title": getattr(localeInfo,
				"VIRTUAL_MARKET_SALE_NOTIFICATION_TITLE",
				u"VIRTUAL MARKET • SOLD"),
			"message": u"%s  ×%d" % (itemName, count),
			"price": _MoneyText(totalPrice),
		})

	def _Show(self, notification):
		self._Layout(notification["kind"])
		self.active = notification
		self.titleLine.SetText(notification["title"])
		self.messageLine.SetText(notification["message"])
		self.priceLine.SetText(notification.get("price", ""))
		if notification.get("bossVnum"):
			self._LoadDungeonPortrait(notification["bossVnum"])
		else:
			self._LoadItemIcon(notification["iconVnum"])
		unusedX, unusedY, progressWidth = self._ProgressGeometry()
		self.progress.SetSize(progressWidth, 2)
		self.progress.Show()
		self.SetPosition(-self.currentWidth, self._TargetY())
		self._BeginMotion("enter", TARGET_X)
		self.Show()
		self.SetTop()

	def _BeginMotion(self, state, targetX):
		x, unusedY = self.GetLocalPosition()
		self.state = state
		self.motionStarted = app.GetTime()
		self.motionFromX = x
		self.motionToX = targetX

	def _UpdateMotion(self):
		progress = min(1.0, max(0.0, app.GetTime() - self.motionStarted) / MOTION_SECONDS)
		eased = 1.0 - pow(1.0 - progress, 3)
		x = int(self.motionFromX + (self.motionToX - self.motionFromX) * eased)
		self.SetPosition(x, self._TargetY())
		return progress >= 1.0

	def _ShowNext(self):
		if not self.queue:
			self.state = "idle"
			self.active = None
			self.Hide()
			return
		self._Show(self.queue.pop(0))

	def OnUpdate(self):
		if self.state == "idle":
			return
		screenWidth = wndMgr.GetScreenWidth()
		if screenWidth != self.lastScreenWidth:
			self.lastScreenWidth = screenWidth
			self._Layout()
			if self.state == "leave":
				self.motionToX = -self.currentWidth
		if self.state == "enter":
			if self._UpdateMotion():
				self.state = "visible"
				self.endTime = app.GetTime() + DISPLAY_SECONDS
			return
		if self.state == "visible":
			self.SetPosition(TARGET_X, self._TargetY())
			remaining = max(0.0, self.endTime - app.GetTime())
			unusedX, unusedY, progressWidth = self._ProgressGeometry()
			width = int(progressWidth * remaining / DISPLAY_SECONDS)
			if width:
				self.progress.SetSize(width, 2)
			else:
				self.progress.Hide()
			if remaining <= 0.0:
				self._BeginMotion("leave", -self.currentWidth)
			return
		if self.state == "leave" and self._UpdateMotion():
			self._ShowNext()

	def OnMouseLeftButtonUp(self):
		if self.state in ("enter", "visible"):
			self._BeginMotion("leave", -self.currentWidth)

	def Destroy(self):
		self.queue = []
		self.active = None
		self.seenSaleIdentities = []
		self.seenSaleIdentitySet = set()
		self.state = "idle"
		self.Hide()
