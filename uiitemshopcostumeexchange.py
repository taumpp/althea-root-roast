# -*- coding: utf-8 -*-
"""Item Shop costume exchange (owner + team 18. 10. 2026).

Item Shop costumes of one category become one Item Shop chest of that category.
The server owns the rule: "/ishop costume_exchange" answers
ItemShopCostumeExchangeRules <costumes per chest> <costume sub type>:<chest>,...
The window only collects the costumes dragged from the inventory, shows the
chest and sends their cells; the server checks everything again and answers
ItemShopCostumeExchangeDone <chest> or a chat message with the reason.
Owner 19. 10. 2026: a costume with a time limit (the 7-day starter gifts) is
refused already on the drop; the server refuses it too and alone knows which
costumes the Item Shop sells.

Batch 6 (owner 19. 10. 2026): the window is an R1 window (docs/ALTHEA_R1_KIT.md, like Denní úkoly R1): the R1
frame and header (title, vein, plain X; Esc closes it, the header drags it), Noto Sans texts and the primary R1
button. Every costume slot and the "Dostaneš:" slot is a column of ITEM_ROWS item cells of the R1 inventory grid
(uir1.SlotGrid, the same slot C cell as the inventory); the item is drawn over as many cells as its item_proto size
(item.GetItemSize), a three-cell costume over the whole column. No old board.
"""
import weakref

import ui
import item
import net
import player
import mouseModule
import localeInfo
import uiCommon
import uiToolTip

import uir1
import uir1tokens as T

ITEM_ROWS = 3                   # the tallest item of the inventory grid (item_proto size 1-3): cells per column
SLOT_GAP = 10                   # px between the costume columns
HINT_Y = 6                      # below the header (ContentTop)
LINE_H = 22
SECTION_GAP = 12
BUTTON_W = 120
MIN_W = 300
TIME_LIMITS = ("LIMIT_REAL_TIME", "LIMIT_REAL_TIME_START_FIRST_USE", "LIMIT_TIMER_BASED_ON_WEAR")

costumesPerChest = 0
chests = {}
window = None


def SetRules(count, chestList):
	global costumesPerChest, chests
	costumesPerChest = int(count)
	chests = {}
	if chestList != "-":
		for entry in chestList.split(","):
			subType, chest = entry.split(":")
			chests[int(subType)] = int(chest)
	if window:
		window.Build()


def IsTimeLimited():
	"""The selected item (item.SelectItem) has a real-time or wear-time limit."""
	limits = [getattr(item, name) for name in TIME_LIMITS]
	for index in range(item.LIMIT_MAX_NUM):
		if item.GetLimit(index)[0] in limits:
			return True
	return False


def ItemRows(vnum):
	"""Cells the item covers in a column: its item_proto size, at most ITEM_ROWS."""
	item.SelectItem(vnum)
	height = item.GetItemSize()[1]
	return max(1, min(ITEM_ROWS, int(height)))


def OnDone(chest):
	if window:
		window.Clear()


class Column(object):
	"""One item column: ITEM_ROWS cells of the R1 inventory grid (a picture, uir1.SlotGrid) under a slot window
	without a base image. The pickable slot covers the whole column while it is empty and the cells of the item
	(its item_proto size, from the top cell like the inventory) while it holds one; ``middle`` centres a shorter
	item in the column (the chest, which takes no drop). The window's handlers get the column index."""

	def __init__(self, parent, x, y, index=0, middle=False, owner=None):
		self.parent = parent
		self.x, self.y = x, y
		self.index = index
		self.middle = middle
		self.owner = weakref.proxy(owner) if owner is not None else None
		self.cells = uir1.SlotGrid(parent, x, y, 1, ITEM_ROWS)
		self.slots = None
		self.rows = 0
		self.vnum = None
		self.__Slots(ITEM_ROWS, 0)

	def __Slots(self, rows, top):
		if self.slots is not None and self.rows == rows:
			self.slots.SetPosition(self.x, self.y + top)
			return
		if self.slots is not None:
			self.slots.Hide()
		slots = ui.SlotWindow()
		slots.SetParent(self.parent)
		slots.SetPosition(self.x, self.y + top)
		slots.SetSize(T.SLOT, rows * T.SLOT)
		slots.AppendSlot(0, 0, 0, T.SLOT, rows * T.SLOT)
		slots.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmpty))
		slots.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItem))
		slots.SetOverInItemEvent(ui.__mem_func__(self.OnOverIn))
		slots.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOut))
		slots.Show()
		self.slots, self.rows = slots, rows

	def Show(self, vnum):
		if vnum == self.vnum:
			return
		self.vnum = vnum
		if not vnum:
			self.__Slots(ITEM_ROWS, 0)
			self.slots.ClearSlot(0)
		else:
			rows = ItemRows(vnum)
			self.__Slots(rows, (ITEM_ROWS - rows) * T.SLOT // 2 if self.middle else 0)
			self.slots.SetItemSlot(0, vnum, 0)
		self.slots.RefreshSlot()

	def OnSelectEmpty(self, slot):
		if self.owner is not None and not self.middle:
			self.owner.Drop(self.index)

	def OnSelectItem(self, slot):
		if self.owner is not None and not self.middle:
			self.owner.Remove(self.index)

	def OnOverIn(self, slot):
		if self.owner is not None:
			self.owner.OverColumn(self)

	def OnOverOut(self):
		if self.owner is not None:
			self.owner.OverOut()

	def Destroy(self):
		if self.slots is not None:
			self.slots.Hide()
		self.cells.Hide()
		self.slots = self.owner = None


class CostumeExchangeWindow(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		global window
		window = self
		self.AddFlag("movable")
		self.AddFlag("float")
		self.kit = uir1.Kit()
		self.cells = []
		self.vnums = []
		self.widgets = []
		self.columns = []
		self.result = None
		self.button = None
		self.tooltip = uiToolTip.ItemToolTip()
		self.tooltip.HideToolTip()
		self.question = uiCommon.QuestionDialog()
		self.question.Close()
		self.Build()

	def Destroy(self):
		global window
		if window is self:
			window = None
		self.question.Close()
		self.tooltip.HideToolTip()
		self.__DestroyWidgets()
		self.Hide()

	def __DestroyWidgets(self):
		for widget in self.widgets:
			widget.Destroy() if isinstance(widget, (Column, uir1.Chrome)) else widget.Hide()
		self.widgets, self.columns, self.result, self.button = [], [], None, None

	def Build(self):
		"""The R1 window for the rules the server sent: one column per costume, the chest column, Vyměnit."""
		self.__DestroyWidgets()
		count = max(costumesPerChest, 1)
		text_s = self.kit.font("text_s")
		hint = (localeInfo.ITEMSHOP_COSTUME_EXCHANGE_HINT % costumesPerChest if costumesPerChest
			else localeInfo.ITEMSHOP_COSTUME_EXCHANGE_OFF)
		probe = ui.TextLine()
		probe.SetFontName(text_s)
		probe.SetText(hint)
		columnsWidth = count * T.SLOT + (count - 1) * SLOT_GAP
		width = max(MIN_W, columnsWidth + 2 * T.PAD, uir1.TextWidth(probe) + 2 * T.PAD)
		top = T.HEAD_H + T.CONTENT_GAP
		hintY = top + HINT_Y
		costumesY = hintY + LINE_H + SECTION_GAP // 2
		resultTextY = costumesY + ITEM_ROWS * T.SLOT + SECTION_GAP
		resultY = resultTextY + LINE_H
		buttonY = resultY + ITEM_ROWS * T.SLOT + SECTION_GAP
		height = buttonY + T.BTN_H + T.PAD
		self.SetSize(width, height)

		chrome = uir1.Chrome(self, self.kit, width, height, localeInfo.ITEMSHOP_COSTUME_EXCHANGE, self.Close)
		self.widgets.append(chrome)
		self.hint = uir1.Text(self, hint, width // 2, hintY + uir1.CellTop(LINE_H, text_s), text_s, T.INK_DIM,
			align="center", valign="top")
		self.widgets.append(self.hint)
		left = (width - columnsWidth) // 2
		for index in range(count):
			column = Column(self, left + index * (T.SLOT + SLOT_GAP), costumesY, index, owner=self)
			self.columns.append(column)
			self.widgets.append(column)
		self.resultText = uir1.Text(self, localeInfo.ITEMSHOP_COSTUME_EXCHANGE_RESULT, width // 2,
			resultTextY + uir1.CellTop(LINE_H, text_s), text_s, T.INK, align="center", valign="top")
		self.widgets.append(self.resultText)
		self.result = Column(self, (width - T.SLOT) // 2, resultY, middle=True, owner=self)
		self.widgets.append(self.result)
		self.button = uir1.Button(self, self.kit, (width - BUTTON_W) // 2, buttonY, BUTTON_W,
			localeInfo.ITEMSHOP_COSTUME_EXCHANGE_BUTTON, primary=True, event=ui.__mem_func__(self.Ask))
		self.widgets.append(self.button)
		self.Clear()

	def Open(self):
		net.SendChatPacket("/ishop costume_exchange")
		self.Clear()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		self.question.Close()
		self.tooltip.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Clear(self):
		self.cells = [-1] * costumesPerChest
		self.vnums = [0] * costumesPerChest
		self.Refresh()

	def Chest(self):
		"""The chest of the category in the slots, or 0."""
		for cell in self.cells:
			if cell >= 0:
				item.SelectItem(player.GetItemIndex(cell))
				return chests.get(item.GetItemSubType(), 0)
		return 0

	def Refresh(self):
		for index, cell in enumerate(self.cells):
			if index < len(self.columns):
				self.columns[index].Show(player.GetItemIndex(cell) if cell >= 0 else 0)
		if self.result:
			self.result.Show(self.Chest())
		if self.button:
			if self.cells and min(self.cells) >= 0:
				self.button.Enable()
			else:
				self.button.Disable()

	def Drop(self, index):
		if not mouseModule.mouseController.isAttached():
			return
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			return
		cell = mouseModule.mouseController.GetAttachedSlotNumber()
		if cell >= player.ITEM_SLOT_COUNT or index >= len(self.cells):
			return
		mouseModule.mouseController.DeattachObject()
		if cell in self.cells:
			return
		item.SelectItem(player.GetItemIndex(cell))
		subType = item.GetItemSubType()
		if item.GetItemType() != item.ITEM_TYPE_COSTUME or subType not in chests:
			self.Notify(localeInfo.ITEMSHOP_COSTUME_EXCHANGE_WRONG)
			return
		if IsTimeLimited():
			self.Notify(localeInfo.ITEMSHOP_COSTUME_EXCHANGE_TIMED)
			return
		chest = self.Chest()
		if chest and chests[subType] != chest:
			self.Notify(localeInfo.ITEMSHOP_COSTUME_EXCHANGE_MIXED)
			return
		self.cells[index] = cell
		self.vnums[index] = player.GetItemIndex(cell)
		self.Refresh()

	def Remove(self, index):
		if mouseModule.mouseController.isAttached():
			self.Drop(index)
			return
		self.cells[index] = -1
		self.vnums[index] = 0
		self.Refresh()

	def Notify(self, text):
		import chat
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	def Ask(self):
		chest = self.Chest()
		if not chest or min(self.cells) < 0:
			return
		item.SelectItem(chest)
		self.question.SetText(localeInfo.ITEMSHOP_COSTUME_EXCHANGE_QUESTION % (costumesPerChest, item.GetItemName()))
		self.question.SetAcceptEvent(ui.__mem_func__(self.Send))
		self.question.SetCancelEvent(ui.__mem_func__(self.question.Close))
		self.question.Open()

	def Send(self):
		self.question.Close()
		net.SendChatPacket("/ishop costume_exchange " + " ".join(str(cell) for cell in self.cells))

	def OnUpdate(self):
		# A costume moved or left the inventory (the exchange took it): its slot empties.
		moved = [index for index, cell in enumerate(self.cells)
			if cell >= 0 and player.GetItemIndex(cell) != self.vnums[index]]
		for index in moved:
			self.cells[index] = -1
			self.vnums[index] = 0
		if moved:
			self.Refresh()

	def OverColumn(self, column):
		if column is self.result:
			self.OverChest(0)
		else:
			self.OverCostume(column.index)

	def OverCostume(self, index):
		if index < len(self.cells) and self.cells[index] >= 0:
			self.tooltip.SetInventoryItem(self.cells[index])

	def OverChest(self, index):
		chest = self.Chest()
		if chest:
			self.tooltip.SetItemToolTip(chest)

	def OverOut(self):
		self.tooltip.HideToolTip()
