# -*- coding: utf-8 -*-
"""The hand-in window of a craft contract (owner 14. 10., REM-ODEVZDAT-CO: "ať si tam dá kdo chce co chce").

The player drags the pieces to hand in from the inventory into the slots; only the kinds the contract takes
(CraftContractKindsV1, server data contract.vnums) are accepted; nothing is put in for the player (owner 14. 10.:
no "cheapest" helper). Odevzdat sends "/craft_mastery hand_in <craft> <cell>..." - the same
server function as the NPC (ContractHandIn), which checks everything again. Texts: locale_game CRAFT_CONTRACT_HANDIN_*.
"""

import app
import item
import mouseModule
import player
import slotwindowpolicy
import ui
import uicrimsoncontrols
from weakref import proxy, ProxyTypes

import craftcontractmodel

# Stacks the window holds; the pieces needed come from the server (hand_in). 16 = the server's cap of
# "/craft_mastery hand_in <craft> <cell>..." (ContractHandIn, HandInCellsCommand): the fishing contract takes 8 fish
# and caught fish never stack (each its own length), ore and wood come in several part stacks - 4 slots left such a
# player unable to hand in (dávka 7, doplněk 2).
SLOT_COUNT = 16
SLOT_COLUMNS = 8
SLOT_ROWS = SLOT_COUNT // SLOT_COLUMNS
SLOT_IMAGE = "d:/ymir work/ui/public/Slot_Base.sub"


def _Text(key, default=u''):
	return craftcontractmodel.Text(key, default)


def _IsHandInCell(slotType, cell):
	"""A cell the player may put into the window: the main inventory or a special-inventory tab (caught fish land in
	the Spotřební tab, cells 1645+, and the tab attaches them under its own slot type), never equipment."""
	if not slotwindowpolicy.IsInventorySlotType(slotType) or not isinstance(cell, int) or cell < 0:
		return False
	if cell < player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT:
		return True
	if not getattr(app, "ENABLE_SPECIAL_INVENTORY_SYSTEM", 0):
		return False
	capacity = player.SPECIAL_INVENTORY_PAGE_SIZE * player.SPECIAL_INVENTORY_PAGE_COUNT
	for name in ("SKILL_BOOK", "UPGRADE_ITEMS", "STONE", "GIFT_BOX", "SWITCH", "COSTUME", "CONSUMABLE"):
		start = getattr(item, name + "_INVENTORY_SLOT_START", None)
		if start is not None and start <= cell < start + capacity:
			return True
	return False


def _OwnerProxy(owner):
	if isinstance(owner, ProxyTypes):
		return owner
	return proxy(owner)


def _Line(parent, x, y, value=u"", color=None):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	line.SetHorizontalAlignCenter()
	line.SetText(value)
	if color:
		line.SetPackedFontColor(color)
	line.AddFlag("not_pick")
	line.Show()
	return line


def _Button(parent, x, y, value, callback):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	uicrimsoncontrols.ApplyVisuals(button, "88x21")
	button.SetText(value)
	button.SetEvent(ui.__mem_func__(callback))
	button.Show()
	return button


class ContractHandInWindow(ui.BoardWithTitleBar):
	def __init__(self, owner):
		self.owner = _OwnerProxy(owner)
		self.taskId = ""
		self.slots = [None] * SLOT_COUNT          # (cell, vnum, count)
		self.busy = False
		self.checking = False
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(282, 228)
		self.SetTitleName(_Text("CRAFT_CONTRACT_HANDIN_TITLE", u""))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.body = ui.Bar()
		self.body.SetParent(self)
		self.body.SetPosition(7, 29)
		self.body.SetSize(268, 192)
		self.body.SetColor(0xff080809)
		self.body.AddFlag("not_pick")
		self.body.Show()
		self.nameText = _Line(self, 141, 38, u"", 0xffeadfc8)
		self.hintText = _Line(self, 141, 56, _Text("CRAFT_CONTRACT_HANDIN_HINT", u""), 0xff9f968c)
		self.grid = ui.GridSlotWindow()
		self.grid.SetParent(self)
		self.grid.SetPosition(141 - SLOT_COLUMNS * 16, 76)
		self.grid.ArrangeSlot(0, SLOT_COLUMNS, SLOT_ROWS, 32, 32, 0, 0)
		self.grid.SetSlotBaseImage(SLOT_IMAGE, 1, 1, 1, 1)
		self.grid.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		self.grid.SetSelectItemSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.SetUnselectItemSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.SetUseSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.Show()
		self.piecesText = _Line(self, 141, 150, u"", 0xffd4ae6b)
		self.statusText = _Line(self, 141, 168, u"", 0xffef7070)
		self.acceptButton = _Button(self, 97, 194, _Text("CRAFT_CONTRACT_HANDIN_SUBMIT", u""), self.Accept)
		ui.BoardWithTitleBar.Hide(self)
		try:
			import uir1frame
			uir1frame.Dress(self)
		except Exception:
			pass

	# ------------------------------------------------------------------ data
	def _Model(self):
		return self.owner.CraftContractModel()

	def _Kinds(self):
		return self._Model().HandInKinds(self.taskId)

	def _Need(self):
		return self._Model().HandInPieces(self.taskId)

	def Pieces(self):
		return sum(row[2] for row in self.slots if row)

	# ------------------------------------------------------------------ window
	def Open(self, taskId, name=u""):
		if taskId != self.taskId or not self.IsShow():
			self.slots = [None] * SLOT_COUNT
			self.SetCenterPosition()
		self.taskId = taskId
		self.busy = False
		self.checking = False
		self.statusText.SetText(u"")
		self.nameText.SetText(name)
		self.Refresh()
		self.Show()
		self.SetTop()
		self.SetFocus()

	def Refresh(self):
		kinds = self._Kinds()
		for index, row in enumerate(self.slots):
			self.grid.ClearSlot(index)
			if row is None:
				continue
			cell, vnum, count = row
			# the inventory changed under the window: the slot goes
			if (vnum not in kinds or player.GetItemIndex(player.INVENTORY, cell) != vnum
				or player.GetItemCount(player.INVENTORY, cell) != count):
				self.slots[index] = None
				continue
			self.grid.SetItemSlot(index, vnum, count)
		self.grid.RefreshSlot()
		need = self._Need()
		self.piecesText.SetText(craftcontractmodel._Fill(_Text("CRAFT_CONTRACT_HANDIN_PIECES", u"%d / %d"),
			min(self.Pieces(), need), need))
		if not self.busy and not self.checking and need and self.Pieces() >= need:
			self.acceptButton.Enable()
		else:
			self.acceptButton.Disable()

	def SelectEmptySlot(self, slot):
		mouse = mouseModule.mouseController
		if self.busy or self.checking or not mouse.isAttached():
			return
		cell = mouse.GetAttachedSlotNumber()
		if not _IsHandInCell(mouse.GetAttachedType(), cell) or any(row and row[0] == cell for row in self.slots):
			return
		vnum = player.GetItemIndex(player.INVENTORY, cell)
		count = player.GetItemCount(player.INVENTORY, cell)
		if vnum not in self._Kinds() or count <= 0:
			self.statusText.SetText(_Text("CRAFT_CONTRACT_HANDIN_WRONG", u""))
			mouse.DeattachObject()
			return
		self.slots[slot] = (cell, vnum, count)
		self.statusText.SetText(u"")
		mouse.DeattachObject()
		self.Refresh()

	def RemoveSlot(self, slot):
		if not self.busy and not self.checking and not mouseModule.mouseController.isAttached():
			self.slots[slot] = None
			self.Refresh()

	def Accept(self):
		self.Refresh()
		if self.busy or self.checking or not self._Need() or self.Pieces() < self._Need():
			return
		# Refresh from the server before consuming a selection kept open across midnight.
		self.checking = True
		self.owner.SendCraftContractCommand(craftcontractmodel.REQUEST)
		self.Refresh()

	def OnServerState(self, craft):
		if craftcontractmodel._CraftOf(self.taskId) != craft or not self.IsShow():
			return
		if not self._Need():
			self.slots = [None] * SLOT_COUNT
			self.checking = False
			self.Refresh()
			return
		if self.checking:
			self.checking = False
			self.Refresh()
			if self.Pieces() >= self._Need():
				command = craftcontractmodel.HandInCellsCommand(self.taskId, [row[0] for row in self.slots if row])
				if command and self.owner.SendCraftContractCommand(command):
					self.busy = True
		self.Refresh()

	def OnReply(self, handedIn):
		"""The server's answer (CraftContractReply): handed in closes the window, else it stays for another try."""
		self.busy = False
		self.checking = False
		if handedIn:
			self.slots = [None] * SLOT_COUNT
			self.Close()
		else:
			self.Refresh()

	def OnUpdate(self):
		# a stack moved or used up while the window is open (cheap: at most SLOT_COUNT slots)
		if self.IsShow() and not self.busy:
			for row in self.slots:
				if row and (player.GetItemIndex(player.INVENTORY, row[0]) != row[1]
				or player.GetItemCount(player.INVENTORY, row[0]) != row[2]):
					self.Refresh()
					break

	def Close(self):
		self.checking = False
		self.Hide()
		self.KillFocus()

	def Destroy(self):
		self.Close()
		self.owner = None

	def OnPressEscapeKey(self):
		self.Close()
		return True
