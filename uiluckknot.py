import ui
import localeInfo
import item
import player
import app
import uiToolTip
import uicrimsoncontrols

# This client predates the optional community cleanup decorator.
WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)


class UpgradeDialog(ui.BoardWithTitleBar):
	"""Compact confirmation of the server-authoritative guaranteed upgrade."""

	AVAILABLE_COLOR = 0xff75d98c
	MISSING_COLOR = 0xffe86e6e
	TEXT_COLOR = 0xffede1d3

	def __init__(self, state):
		self.Initialize()
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("float")
		self.state = state
		self.SetTitleName(localeInfo.LUCK_KNOT_NAME)
		self.SetCloseEvent(ui.__mem_func__(self.__Cancel))
		self.toolTip = uiToolTip.ItemToolTip()
		self.toolTip.Hide()
		self.surface = ui.Bar()
		self.surface.SetParent(self)
		self.surface.AddFlag("not_pick")
		self.surface.SetPosition(6, 31)
		self.surface.SetColor(0xff090807)
		self.surface.Show()

		self.materialRows = []
		width = 224
		for index, cost in enumerate(state["costs"]):
			item.SelectItem(cost["vnum"])
			name = "%s x%d" % (item.GetItemName(), cost["amount"])
			slot = ui.SlotWindow()
			slot.SetParent(self)
			slot.SetPosition(16, 52 + index * 38)
			slot.SetSize(32, 32)
			slot.AppendSlot(index, 0, 0, 32, 32)
			slot.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 1.0, 1.0, 1.0, 1.0)
			slot.SetItemSlot(index, cost["vnum"], cost["amount"])
			slot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
			slot.RefreshSlot()
			slot.Show()
			label = self.__Text(name, 58, 68 + index * 38)
			count = self.__Text("", 0, 68 + index * 38, "right")
			width = max(width, 58 + label.GetTextSize()[0] + 64)
			self.materialRows.append((slot, label, count))

		footerY = 56 + len(self.materialRows) * 38
		levelHeight = 20 if state["minimum_level"] else 0
		self.SetSize(width, footerY + 80 + levelHeight)
		self.surface.SetSize(width - 12, self.GetHeight() - 37)
		transition = localeInfo.LUCK_KNOT_LEVEL_TRANSITION % (state["level"], state["level"] + 1)
		self.stageText = self.__Text(transition, width // 2, 38, "center", 0xffb9b0a4)
		for slot, label, count in self.materialRows:
			count.SetPosition(width - 17, slot.GetLocalPosition()[1] + 16)

		self.yangIcon = ui.ImageBox()
		self.yangIcon.SetParent(self)
		self.yangIcon.AddFlag("not_pick")
		self.yangIcon.LoadImage("d:/ymir work/ui/game/crimson_ember/inventory/icon_yang.png")
		self.yangIcon.SetPosition(17, footerY)
		self.yangIcon.Show()
		price = "%s %s" % (localeInfo.NumberToString(state["yang"]), localeInfo.CHEQUE_SYSTEM_UNIT_YANG)
		self.priceText = self.__Text(price, 42, footerY + 8, color=0xfff1d7a4)
		self.chanceText = self.__Text(localeInfo.LUCK_KNOT_CHANCE, 17, footerY + 35)
		# The server transaction has no RNG/failure branch; this is its guarantee,
		# not a configurable probability copied out of the gameplay catalog.
		self.chanceValue = self.__Text("100 %", width - 17, footerY + 35, "right", self.AVAILABLE_COLOR, "Tahoma:13b")
		if levelHeight:
			self.minimumLevelText = self.__Text(localeInfo.LUCK_KNOT_REQUIRE_LEVEL % state["minimum_level"],
				17, footerY + 55)

		buttonY = footerY + 48 + levelHeight
		self.acceptButton = self.__Button(localeInfo.LUCK_KNOT_IMPROVE, width // 2 - 88, buttonY, self.__Accept)
		self.cancelButton = self.__Button(localeInfo.UI_CANCEL, width // 2 + 8, buttonY, self.__Cancel)
		self.RefreshAvailability()

	def Initialize(self):
		self.state = None
		self.materialRows = []
		self.surface = None
		self.stageText = None
		self.yangIcon = None
		self.priceText = None
		self.chanceText = None
		self.chanceValue = None
		self.minimumLevelText = None
		self.acceptButton = None
		self.cancelButton = None
		self.acceptEvent = None
		self.cancelEvent = None
		self.toolTip = None
		self.canUpgrade = False
		self.nextRefresh = 0.0

	def __Text(self, text, x, y, align="left", color=TEXT_COLOR, font="Tahoma:12"):
		line = ui.TextLine()
		line.SetParent(self)
		line.AddFlag("not_pick")
		line.SetFontName(font)
		line.SetPosition(x, y)
		line.SetVerticalAlignCenter()
		if align == "right":
			line.SetHorizontalAlignRight()
		elif align == "center":
			line.SetHorizontalAlignCenter()
		line.SetPackedFontColor(color)
		line.SetOutline()
		line.SetText(text)
		line.Show()
		return line

	def __Button(self, text, x, y, event):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		uicrimsoncontrols.ApplyVisuals(button, "80x24")
		button.SetText(text)
		button.SetEvent(ui.__mem_func__(event))
		button.Show()
		return button

	def RefreshAvailability(self):
		if not self.state or not self.acceptButton:
			return
		canUpgrade = True
		for cost, row in zip(self.state["costs"], self.materialRows):
			owned = player.GetItemCountByVnum(cost["vnum"])
			enough = owned >= cost["amount"]
			color = self.AVAILABLE_COLOR if enough else self.MISSING_COLOR
			row[1].SetPackedFontColor(color)
			row[2].SetPackedFontColor(color)
			row[2].SetText("[%d]" % owned)
			canUpgrade = canUpgrade and enough
		enoughYang = player.GetMoney() >= self.state["yang"]
		self.priceText.SetPackedFontColor(0xfff1d7a4 if enoughYang else self.MISSING_COLOR)
		canUpgrade = canUpgrade and enoughYang
		if self.minimumLevelText:
			enoughLevel = player.GetStatus(player.LEVEL) >= self.state["minimum_level"]
			self.minimumLevelText.SetPackedFontColor(self.TEXT_COLOR if enoughLevel else self.MISSING_COLOR)
			canUpgrade = canUpgrade and enoughLevel
		self.canUpgrade = canUpgrade
		self.acceptButton.SetTextColor(self.TEXT_COLOR if canUpgrade else 0xff8f8580)
		if canUpgrade:
			self.acceptButton.Enable()
		else:
			self.acceptButton.Disable()

	def OnUpdate(self):
		now = app.GetTime()
		if now >= self.nextRefresh:
			self.nextRefresh = now + 0.2
			self.RefreshAvailability()

	def __Accept(self):
		self.RefreshAvailability()
		if self.canUpgrade and self.acceptEvent:
			self.acceptEvent()

	def __Cancel(self):
		if self.cancelEvent:
			self.cancelEvent()
		else:
			self.Close()

	def SetAcceptEvent(self, event):
		self.acceptEvent = event

	def SetCancelEvent(self, event):
		self.cancelEvent = event

	def __OverInItem(self, index):
		if self.toolTip:
			self.toolTip.SetItemToolTip(self.state["costs"][index]["vnum"])

	def __OverOutItem(self):
		if self.toolTip:
			self.toolTip.HideToolTip()

	def Open(self):
		self.RefreshAvailability()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.__OverOutItem()
		self.Hide()

	@WindowDestroy
	def Destroy(self):
		self.__OverOutItem()
		self.Initialize()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def OnPressEscapeKey(self):
		self.__Cancel()
		return True
