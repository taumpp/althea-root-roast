# -*- coding: utf-8 -*-

import item
import mouseModule
import player
import ui
import uicrimsoncontrols
import skilltreelocale
from weakref import proxy, ProxyTypes


SLOT_COUNT = 9
SLOT_IMAGE = "d:/ymir work/ui/public/Slot_Base.sub"
INFO_BUTTON_ICON = "d:/ymir work/ui/game/skill_tree_v2/info_book.png"
INFO_VISIBLE_ROWS = 15
INFO_ROW_HEIGHT = 20


def _IsInventorySource(slotType, cell):
	if not isinstance(cell, int) or cell < 0:
		return False
	if slotType == player.SLOT_TYPE_INVENTORY and cell < player.EQUIPMENT_SLOT_START:
		return True
	for name in ("SKILL_BOOK", "UPGRADE_ITEMS", "STONE", "GIFT_BOX", "SWITCH", "COSTUME", "CONSUMABLE"):
		kind = getattr(player, "SLOT_TYPE_%s_INVENTORY" % name, None)
		start = getattr(item, "%s_INVENTORY_SLOT_START" % name, None)
		if kind is not None and start is not None and slotType in (kind, player.SLOT_TYPE_INVENTORY):
			capacity = player.SPECIAL_INVENTORY_PAGE_SIZE * player.SPECIAL_INVENTORY_PAGE_COUNT
			if start <= cell < start + capacity:
				return True
	return False


def _OwnerProxy(owner):
	if isinstance(owner, ProxyTypes):
		return owner
	return proxy(owner)


def _Text(parent, x, y, value, centered=False):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	if centered:
		line.SetHorizontalAlignCenter()
	line.SetText(value)
	line.AddFlag("not_pick")
	line.Show()
	return line


def _Button(parent, x, y, size, value, callback):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	uicrimsoncontrols.ApplyVisuals(button, size)
	button.SetText(value)
	button.SetEvent(ui.__mem_func__(callback))
	button.Show()
	return button


class SkillTreePointInfo(ui.BoardWithTitleBar):
	def __init__(self, owner):
		self.owner = _OwnerProxy(owner)
		self.sources = []
		self.firstRow = 0
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(320, 400)
		self.SetTitleName(skilltreelocale.GetDismantleText("info_title"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.body = ui.Bar()
		self.body.SetParent(self)
		self.body.SetPosition(7, 29)
		self.body.SetSize(306, 364)
		self.body.SetColor(0xff080809)
		self.body.AddFlag("not_pick")
		self.body.Show()
		self.itemHeader = _Text(self, 18, 42,
			skilltreelocale.GetDismantleText("info_items"))
		self.pointHeader = _Text(self, 282, 42,
			skilltreelocale.GetDismantleText("info_points"))
		for header in (self.itemHeader, self.pointHeader):
			header.SetPackedFontColor(0xffd4ae6b)
		divider = ui.Bar()
		divider.SetParent(self)
		divider.SetPosition(17, 57)
		divider.SetSize(269, 1)
		divider.SetColor(0xff594632)
		divider.AddFlag("not_pick")
		divider.Show()
		self.divider = divider
		self.rows = []
		for index in range(INFO_VISIBLE_ROWS):
			y = 64 + index * INFO_ROW_HEIGHT
			icon = ui.ExpandedImageBox()
			icon.SetParent(self)
			icon.SetPosition(18, y)
			icon.AddFlag("not_pick")
			icon.Hide()
			name = _Text(self, 41, y + 1, u"")
			points = _Text(self, 281, y + 1, u"")
			points.SetHorizontalAlignRight()
			points.SetPackedFontColor(0xffd4ae6b)
			line = ui.Bar()
			line.SetParent(self)
			line.SetPosition(18, y + 18)
			line.SetSize(268, 1)
			line.SetColor(0xff302b29)
			line.AddFlag("not_pick")
			line.Show()
			self.rows.append((icon, name, points, line))
		self.footer = _Text(self, 18, 370, u"")
		self.footer.SetPackedFontColor(0xff9a9187)
		self.scroll = ui.ScrollBarFlat()
		self.scroll.SetParent(self)
		self.scroll.SetPosition(296, 64)
		self.scroll.SetScrollBarSize(302)
		self.scroll.SetScrollEvent(ui.__mem_func__(self._OnScroll))
		self.scroll.SetMiddleBarSize(float(INFO_VISIBLE_ROWS) / 23.0)
		self.scroll.Show()
		ui.BoardWithTitleBar.Hide(self)

	def Open(self, sources):
		# The catalog groups four sigils, fourteen dungeon/boss drops, then five
		# low-value materials. The approved list puts those materials first.
		catalogOrder = self.owner.GetPointSourceOrder()
		visibleOrder = catalogOrder[:4] + catalogOrder[18:] + catalogOrder[4:18]
		self.sources = [(vnum, sources[vnum]) for vnum in visibleOrder if vnum in sources]
		self.firstRow = 0
		self.scroll.SetMiddleBarSize(min(0.25,
			float(INFO_VISIBLE_ROWS) / max(1, len(self.sources))))
		self.scroll.SetPos(0.0)
		if len(self.sources) > INFO_VISIBLE_ROWS:
			self.scroll.Show()
		else:
			self.scroll.Hide()
		self._RefreshRows()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def _RefreshRows(self):
		for index, (icon, nameText, pointText, line) in enumerate(self.rows):
			sourceIndex = self.firstRow + index
			if sourceIndex >= len(self.sources):
				icon.Hide()
				nameText.Hide()
				pointText.Hide()
				line.Hide()
				continue
			vnum, points = self.sources[sourceIndex]
			item.SelectItem(vnum)
			icon.LoadImage(item.GetIconImageFileName())
			icon.SetScale(0.5, 0.5)
			icon.Show()
			nameText.SetText(item.GetItemName())
			nameText.Show()
			pointText.SetText(skilltreelocale.FormatPointAmount(points))
			pointText.Show()
			line.Show()
		self.footer.SetText(skilltreelocale.GetDismantleText("info_footer") % (
			self.firstRow + 1,
			min(self.firstRow + INFO_VISIBLE_ROWS, len(self.sources)),
			len(self.sources)))

	def _OnScroll(self):
		maximum = max(0, len(self.sources) - INFO_VISIBLE_ROWS)
		first = int(self.scroll.GetPos() * maximum + 0.5)
		if first != self.firstRow:
			self.firstRow = first
			self._RefreshRows()

	def OnMouseWheel(self, delta):
		maximum = max(0, len(self.sources) - INFO_VISIBLE_ROWS)
		if maximum:
			self.scroll.SetPos(float(max(0, min(maximum,
				self.firstRow + (-1 if delta > 0 else 1)))) / maximum)
		return True

	def Close(self):
		self.Hide()

	def Destroy(self):
		self.Close()
		self.owner = None

	def OnPressEscapeKey(self):
		self.Close()
		return True


class SkillTreeDismantleWindow(ui.BoardWithTitleBar):
	def __init__(self, owner):
		self.owner = _OwnerProxy(owner)
		self.slots = [None] * SLOT_COUNT
		self.busy = False
		self.canAccept = False
		self.lastRejected = False
		self.info = None
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(150, 195)
		self.SetTitleName(skilltreelocale.GetDismantleText("title"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.body = ui.Bar()
		self.body.SetParent(self)
		self.body.SetPosition(7, 29)
		self.body.SetSize(136, 159)
		self.body.SetColor(0xff080809)
		self.body.AddFlag("not_pick")
		self.body.Show()
		self.grid = ui.GridSlotWindow()
		self.grid.SetParent(self)
		self.grid.SetPosition(27, 45)
		self.grid.ArrangeSlot(0, 3, 3, 32, 32, 0, 0)
		self.grid.SetSlotBaseImage(SLOT_IMAGE, 1, 1, 1, 1)
		self.grid.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		self.grid.SetSelectItemSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.SetUnselectItemSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.SetUseSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.Show()
		self.sumText = _Text(self, 75, 143, u"0", True)
		self.sumText.SetPackedFontColor(0xffd4ae6b)
		self.infoButton = _Button(self, 8, 166, "43x21", u"", self.OpenInfo)
		self.infoIcon = ui.ImageBox()
		self.infoIcon.SetParent(self.infoButton)
		self.infoIcon.SetPosition(12, 1)
		self.infoIcon.LoadImage(INFO_BUTTON_ICON)
		self.infoIcon.AddFlag("not_pick")
		self.infoIcon.Show()
		self.acceptButton = _Button(self, 54, 166, "88x21",
			skilltreelocale.GetDismantleText("action"), self.Accept)
		ui.BoardWithTitleBar.Hide(self)

	def Open(self):
		if not self.IsShow():
			self.slots = [None] * SLOT_COUNT
			self.lastRejected = False
			self.SetCenterPosition()
		self.Refresh()
		self.Show()
		self.SetTop()
		self.SetFocus()

	def Refresh(self):
		sources = self.owner.GetPointSources()
		points = 0
		for index, row in enumerate(self.slots):
			self.grid.ClearSlot(index)
			if row is None:
				continue
			cell, vnum, count = row
			if (vnum not in sources or player.GetItemIndex(player.INVENTORY, cell) != vnum
				or player.GetItemCount(player.INVENTORY, cell) != count):
				self.slots[index] = None
				continue
			self.grid.SetItemSlot(index, vnum, count)
			points += sources[vnum] * count
		self.grid.RefreshSlot()
		self.canAccept = bool(points and not self.busy and self.owner.CanDismantle(points))
		if self.lastRejected:
			self.sumText.SetText(skilltreelocale.GetDismantleText("rejected_short"))
		elif self.busy:
			self.sumText.SetText(skilltreelocale.GetDismantleText("pending_short"))
		elif points and not self.canAccept:
			self.sumText.SetText(skilltreelocale.GetDismantleText("unavailable_short"))
		else:
			self.sumText.SetText(skilltreelocale.GetDismantleText("summary") %
				skilltreelocale.FormatPointAmount(points))
		if self.canAccept:
			self.acceptButton.Enable()
		else:
			self.acceptButton.Disable()

	def SelectEmptySlot(self, slot):
		mouse = mouseModule.mouseController
		if self.busy or not self.owner.GetPointSources() or not mouse.isAttached():
			return
		cell = mouse.GetAttachedSlotNumber()
		if (not _IsInventorySource(mouse.GetAttachedType(), cell)
			or any(row and row[0] == cell for row in self.slots)):
			return
		vnum = player.GetItemIndex(player.INVENTORY, cell)
		count = player.GetItemCount(player.INVENTORY, cell)
		if (vnum not in self.owner.GetPointSources() or count <= 0
			or mouse.GetAttachedItemIndex() != vnum
			or mouse.GetAttachedItemCount() != count):
			return
		self.slots[slot] = (cell, vnum, count)
		self.lastRejected = False
		mouse.DeattachObject()
		self.Refresh()

	def RemoveSlot(self, slot):
		if not self.busy and not mouseModule.mouseController.isAttached():
			self.slots[slot] = None
			self.lastRejected = False
			self.Refresh()

	def OpenInfo(self):
		if self.info is None:
			self.info = SkillTreePointInfo(self.owner)
		self.info.Open(self.owner.GetPointSources())

	def Accept(self):
		self.lastRejected = False
		self.Refresh()
		if not self.canAccept:
			self.lastRejected = True
			self.Refresh()
			return
		slots = tuple((player.INVENTORY, row[0]) for row in self.slots if row)
		if self.owner.RequestDismantle(slots):
			self.busy = True
			self.Refresh()
		else:
			self.lastRejected = True
			self.Refresh()

	def OnResult(self, success):
		self.busy = False
		self.lastRejected = not success
		if success:
			self.slots = [None] * SLOT_COUNT
		self.Refresh()

	def Close(self):
		if self.info:
			self.info.Close()
		self.Hide()
		self.KillFocus()

	def Destroy(self):
		self.Close()
		if self.info:
			self.info.Destroy()
		self.info = None
		self.owner = None

	def OnPressEscapeKey(self):
		self.Close()
		return True
