"""Native 3x3 mount-crystal basket; the mount controller owns all requests."""
import chat
import item
import mouseModule
import player
import ui
import uimountk1 as K1
import uicrimsoncontrols
from weakref import ProxyTypes, proxy
from mountfeedmodel import FeedBasket, CRYSTAL_VNUMS, SLOT_COUNT


def InventoryStack(cell):
	return (player.GetItemIndex(player.INVENTORY, cell),
		player.GetItemCount(player.INVENTORY, cell))


def IsInventorySource(slotType, cell):
	if not isinstance(cell, int) or cell < 0:
		return False
	if slotType == player.SLOT_TYPE_INVENTORY and cell < player.EQUIPMENT_SLOT_START:
		return True
	for name in ("SKILL_BOOK", "UPGRADE_ITEMS", "STONE", "GIFT_BOX", "SWITCH"):
		kind = getattr(player, "SLOT_TYPE_%s_INVENTORY" % name, None)
		start = getattr(item, "%s_INVENTORY_SLOT_START" % name, None)
		# Ordinary special-inventory clicks use the generic inventory drag type;
		# split/search paths may retain the category type. Both use global cells.
		if kind is not None and start is not None and slotType in (kind, player.SLOT_TYPE_INVENTORY):
			capacity = player.SPECIAL_INVENTORY_PAGE_SIZE * player.SPECIAL_INVENTORY_PAGE_COUNT
			if start <= cell < start + capacity:
				return True
	return False


class MountFeedWindow(ui.BoardWithTitleBar):
	WIDTH = 246
	HEIGHT = 210

	def __init__(self, owner):
		# Window.__init__ invokes Hide, including tooltip and basket cleanup.
		# Native button callbacks already pass a weak proxy as their self.
		self.owner = owner if type(owner) in ProxyTypes else proxy(owner)
		self.basket = FeedBasket()
		self.deadline = 0.0
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName(u"Nakrmit mounta")
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.body = ui.Bar()
		self.body.SetParent(self)
		self.body.SetPosition(7, 29)
		self.body.SetSize(232, 174)
		self.body.SetColor(0xff080809)
		self.body.AddFlag("not_pick")
		self.body.Show()
		K1.Text(self, 123, 40, u"Vlož krystaly duše mounta", color=K1.GOLD, align="center")
		K1.Text(self, 123, 54, u"Pravým klikem odebereš výběr", size=11, color=K1.MUTED, align="center")
		self.grid = ui.GridSlotWindow()
		self.grid.SetParent(self)
		self.grid.SetPosition(75, 65)
		self.grid.ArrangeSlot(0, 3, 3, 32, 32, 0, 0)
		self.grid.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1, 1, 1, 1)
		self.grid.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		self.grid.SetSelectItemSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.SetUnselectItemSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.SetUseSlotEvent(ui.__mem_func__(self.RemoveSlot))
		self.grid.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.grid.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.grid.Show()
		self.status = K1.Text(self, 123, 176, u"", size=11, color=K1.BLUE, align="center")
		self.accept = ui.Button()
		self.accept.SetParent(self)
		self.accept.SetPosition(83, 180)
		uicrimsoncontrols.ApplyVisuals(self.accept, "80x24")
		self.accept.SetText(u"OK")
		self.accept.SetEvent(ui.__mem_func__(self.Accept))
		self.accept.Show()
		ui.BoardWithTitleBar.Hide(self)

	def Open(self):
		if self.basket.busy:
			return
		if not self.IsShow():
			self.basket.clear()
			self.SetCenterPosition()
		self.Refresh()
		self.Show()
		self.SetTop()
		self.SetFocus()

	def Refresh(self):
		for index, row in enumerate(self.basket.slots):
			self.grid.ClearSlot(index)
			if row:
				self.grid.SetItemSlot(index, row[1], row[2])
		self.grid.RefreshSlot()
		self.RefreshControls()

	def RefreshControls(self):
		count = sum(row is not None for row in self.basket.slots)
		self.status.SetText(u"Probíhá krmení…" if self.basket.busy or self.basket.active
			else u"Vybráno: %d / 9" % count)
		K1.SetColor(self.status, K1.BLUE)
		if count and not self.basket.active and not self.basket.busy and self.owner.CanStartFeeding():
			self.accept.Enable()
		else:
			self.accept.Disable()

	def SelectEmptySlot(self, slot):
		mouse = mouseModule.mouseController
		if not self.owner.CanStartFeeding() or not mouse.isAttached():
			return
		cell = mouse.GetAttachedSlotNumber()
		if not IsInventorySource(mouse.GetAttachedType(), cell):
			return
		vnum, count = InventoryStack(cell)
		if mouse.GetAttachedItemIndex() != vnum:
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Předmět na kurzoru se změnil. Vyber ho znovu.")
			return
		if vnum not in CRYSTAL_VNUMS:
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Sem patří pouze krystaly duše mounta.")
			return
		if mouse.GetAttachedItemCount() != count:
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Vlož celý stack krystalů jako při krmení PETa.")
			return
		if self.basket.add(slot, cell, vnum, count):
			mouse.DeattachObject()
			self.Refresh()

	def RemoveSlot(self, slot):
		if not mouseModule.mouseController.isAttached() and self.basket.remove(slot):
			self.OverOutItem()
			self.Refresh()

	def Accept(self):
		self.owner.StartFeeding()

	def OverInItem(self, slot):
		if not 0 <= slot < SLOT_COUNT:
			return
		row = self.basket.slots[slot]
		tooltip = self.owner.tooltipItem
		if row and tooltip and InventoryStack(row[0])[0] == row[1]:
			tooltip.SetInventoryItem(row[0], player.INVENTORY, appendShortcuts=False)

	def OverOutItem(self):
		if self.owner.tooltipItem:
			self.owner.tooltipItem.HideToolTip()

	def Hide(self):
		self.OverOutItem()
		self.basket.clear()
		self.KillFocus()
		ui.BoardWithTitleBar.Hide(self)

	def Close(self):
		self.Hide()

	def Destroy(self):
		self.Hide()
		self.basket.stop()
		self.accept.SetEvent(None)

	def OnUpdate(self):
		if not self.owner.IsShow() or self.owner.activePage != "mount":
			self.Hide()
			return

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		return self.OnPressEscapeKey()

	def OnMouseWheel(self, unusedDelta):
		return True
