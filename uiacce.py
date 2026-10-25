import app
import ui
import net
import grp
import snd
import item
import chat
import acce
import player
import uiToolTip
import localeInfo
import acceabsorbpolicy
import uiInventory
import mouseModule
import uiScriptLocale
import uiresonance

if app.WJ_ENABLE_TRADABLE_ICON:
	INVENTORY_PAGE_SIZE = player.INVENTORY_PAGE_SIZE
	if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
		SPECIAL_INVENTORY_PAGE_SIZE = player.SPECIAL_INVENTORY_PAGE_SIZE

def _DressR1(window, kind):
	"""R1 look of the window (root/uir1theowahdan.py, inside the shared R1 frame of root/uir1frame.py); "Starý vzhled"
	or a failure keeps the original window."""
	try:
		import uir1theowahdan
		uir1theowahdan.Dress(window, kind)
	except Exception:
		pass

def _SetR1Cost(window, amount=None, text=None):
	try:
		import uir1theowahdan
		uir1theowahdan.SetCost(window, amount, text)
	except Exception:
		pass

class CombineWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'btnAccept')
		self.isLoaded = 0
		self.PositionOut = 0
		self.PositionStartX = 0
		self.PositionStartY = 0

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.interface = None
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None

			self.ItemListIdx = []

	def __del__(self):
		ui.ScriptWindow.__del__(self)

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.interface = None
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None

			self.ItemListIdx = []

	def Destroy(self):
		self.ClearDictionary()
		self.titleBar = None
		self.btnAccept = None
		self.btnCancel = None
		self.acceSlot = None
		self.cost = None
		self.Result = None
		self.PositionOut = 0
		self.PositionStartX = 0
		self.PositionStartY = 0
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = []

	def LoadWindow(self):
		if self.isLoaded:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/acce_combinewindow.py")

		except:
			import exception
			exception.Abort("Acce_CombineWindow.LoadDialog.LoadScript")

		try:
			self.titleBar = self.GetChild("TitleBar")
			self.btnAccept = self.GetChild("AcceptButton")
			self.btnCancel = self.GetChild("CancelButton")
			self.cost = self.GetChild("Cost")
			self.Result = self.GetChild("Result")
			self.acceSlot = self.GetChild("AcceSlot")
		except:
			import exception
			exception.Abort("Acce_CombineWindow.LoadDialog.BindObject")

		self.acceSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		self.acceSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.acceSlot.SetUseSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.acceSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		self.acceSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
		self.titleBar.SetCloseEvent(ui.__mem_func__(self.OnClose))
		self.btnCancel.SetEvent(ui.__mem_func__(self.OnClose))
		self.btnAccept.SetEvent(ui.__mem_func__(self.OnAccept))
		self.tooltipItem = None
		_DressR1(self, "combine")

	def SetItemToolTip(self, itemTooltip):
		self.tooltipItem = itemTooltip

	def __SetCombineInfo(self):
		(resultVnum, chance, unusedMax) = acce.GetResultItem()
		if resultVnum and uiresonance.IsSealVnum(resultVnum):
			self.cost.SetText(localeInfo.RARITY_CHANCE % str(chance))
			_SetR1Cost(self, text=self.cost.GetText())
		else:
			self.cost.SetText(localeInfo.ACCE_ABSORB_COST % acce.GetPrice())
			_SetR1Cost(self, amount=acce.GetPrice())

	def IsOpened(self):
		if self.IsShow() and self.isLoaded:
			return True

		return False

	def Open(self):
		self.PositionOut = 0
		(self.PositionStartX, self.PositionStartY, z) = player.GetMainCharacterPosition()
		self.__SetCombineInfo()
		for i in range(acce.WINDOW_MAX_MATERIALS + 1):
			self.acceSlot.ClearSlot(i)

		player.SetAcceRefineWindowOpen(2)
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_ACCE_COMBINE)
				self.interface.RefreshMarkInventoryBag()

		if app.ENABLE_ANIMATED_WINDOW: 	
			self.bClosed = False

	def Close(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

		if app.ENABLE_ANIMATED_WINDOW: 	
			if self.bClosed == False:
				self.Hide()
		else:
			self.Hide()

		if app.ENABLE_ANIMATED_WINDOW: 
			self.bClosed = True

	def OnClose(self):
		self.Close()
		player.SetAcceRefineWindowOpen(0)
		acce.SendCloseRequest()

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.__ClearTradableIconState()

	def OnPressEscapeKey(self):
		self.OnClose()
		return True

	def OnAccept(self):
		acce.SendRefineRequest()

	if app.WJ_ENABLE_TRADABLE_ICON:
		def __ClearTradableIconState(self):
			if self.interface:
				try:
					self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
					self.interface.RefreshMarkInventoryBag()
				except AttributeError:
					pass

			self.ItemListIdx = None

		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

		def SetInven(self, inven):
			self.inven = inven

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			def SetSpecialInven(self, invenSpecial):
				self.invenSpecial = invenSpecial

		def CantTradableItem(self, slotIndex):
			itemIndex = player.GetItemIndex(slotIndex)

			if itemIndex:
				item.SelectItem(itemIndex)

				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0: #봉인아이템 걸러냄.
						return True

				if not ((item.GetItemType() == item.ITEM_TYPE_COSTUME and
					item.GetItemSubType() == item.COSTUME_TYPE_ACCE) or
					uiresonance.IsSealVnum(itemIndex)):
					return True

			return False

		def OnTop(self):
			self.tooltipItem.SetTop()
			if not self.interface:
				return

			self.interface.SetOnTopWindow(player.ON_TOP_WND_ACCE_COMBINE)
			self.interface.RefreshMarkInventoryBag()

		def AcceItemMouseEvent(self):
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if not self.inven or not self.invenSpecial:
					return
			else:
				if not self.inven:
					return

			if not self.ItemListIdx:
				return

			page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				special_page = self.invenSpecial.GetInventoryPageIndex()

			if self.ItemListIdx:
				for i in self.ItemListIdx:
					if (page * INVENTORY_PAGE_SIZE) <= i < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						lock_idx = i - (page * INVENTORY_PAGE_SIZE)
						self.inven.wndItem.SetCantMouseEventSlot(lock_idx)

					if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
						if self.invenSpecial.GetInventoryType() == 0:
							if (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.SKILL_BOOK_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 1:
							if (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 2:
							if (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.STONE_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 3:
							if (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.GIFT_BOX_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 4:
							if (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.SWITCH_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 5:
							if (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.COSTUME_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

	def OnUpdate(self):
		LIMIT_RANGE = acce.LIMIT_RANGE
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.PositionStartX) >= LIMIT_RANGE or abs(y - self.PositionStartY) >= LIMIT_RANGE:
			if not self.PositionOut:
				self.PositionOut += 1
				self.OnClose()
				return

		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.IsShow():
				self.AcceItemMouseEvent()

	def OnSelectEmptySlot(self, selectedSlotPos):
		isAttached = mouseModule.mouseController.isAttached()
		if not isAttached or selectedSlotPos == acce.WINDOW_MAX_MATERIALS:
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)

		if player.GetItemSealDate(player.INVENTORY, attachedSlotPos) == -1 or player.GetItemSealDate(player.INVENTORY, attachedSlotPos) > 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_NOT_SEALITEM)
			return

		mouseModule.mouseController.DeattachObject()
		#if attachedSlotType == player.SLOT_TYPE_INVENTORY and attachedInvenType == player.INVENTORY:
		if attachedSlotType == player.SLOT_TYPE_INVENTORY or attachedSlotType == player.SLOT_TYPE_COSTUME_INVENTORY:
			acce.Add(attachedInvenType, attachedSlotPos, selectedSlotPos)

	def OnSelectItemSlot(self, selectedSlotPos):
		if selectedSlotPos == acce.WINDOW_MAX_MATERIALS:
			return

		mouseModule.mouseController.DeattachObject()
		acce.Remove(selectedSlotPos)

	def OnOverInItem(self, selectedSlotPos):
		if self.tooltipItem:
			if selectedSlotPos == acce.WINDOW_MAX_MATERIALS:
				(isHere, iCell) = acce.GetAttachedItem(0)
				if isHere:
					(resultVnum, unusedMin, unusedMax) = acce.GetResultItem()
					if resultVnum and uiresonance.IsSealVnum(resultVnum):
						self.tooltipItem.SetItemToolTip(resultVnum)
					else:
						self.tooltipItem.SetAcceResultItem(iCell)
			else:
				(isHere, iCell) = acce.GetAttachedItem(selectedSlotPos)
				if isHere:
					self.tooltipItem.SetInventoryItem(iCell)

	def OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def Refresh(self, iAct):
		self.__SetCombineInfo()
		self.acceSlot.ClearSlot(acce.WINDOW_MAX_MATERIALS)

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = []

		for i in range(acce.WINDOW_MAX_MATERIALS):
			self.acceSlot.ClearSlot(i)

			(isHere, iCell) = acce.GetAttachedItem(i)
			if isHere:
				self.acceSlot.SetItemSlot(i, player.GetItemIndex(iCell), 0)

				if app.WJ_ENABLE_TRADABLE_ICON:
					self.ItemListIdx.append(iCell)

				if i == int(acce.WINDOW_MAX_MATERIALS - 1):
					(itemVnum, MinAbs, MaxAbs) = acce.GetResultItem()
					if not itemVnum:
						break

					self.acceSlot.SetItemSlot(i + 1, itemVnum, 0)
					break

class AbsorbWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'btnAccept')
		self.isLoaded = 0
		self.PositionOut = 0
		self.PositionStartX = 0
		self.PositionStartY = 0

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.interface = None
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None

			self.ItemListIdx = []

	def __del__(self):
		ui.ScriptWindow.__del__(self)

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.interface = None
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None

			self.ItemListIdx = []

	def Destroy(self):
		self.ClearDictionary()
		self.titleBar = None
		self.btnAccept = None
		self.btnCancel = None
		self.acceSlot = None
		self.PositionOut = 0
		self.PositionStartX = 0
		self.PositionStartY = 0
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = []

	def LoadWindow(self):
		if self.isLoaded:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/acce_absorbwindow.py")
		except:
			import exception
			exception.Abort("Acce_AbsorbtionWindow.LoadDialog.LoadScript")

		try:
			self.titleBar = self.GetChild("TitleBar")
			self.btnAccept = self.GetChild("AcceptButton")
			self.btnCancel = self.GetChild("CancelButton")
			self.acceSlot = self.GetChild("AcceSlot")
		except:
			import exception
			exception.Abort("Acce_AbsorbtionWindow.LoadDialog.BindObject")

		self.acceSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		self.acceSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.acceSlot.SetUseSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.acceSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		self.acceSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
		self.titleBar.SetCloseEvent(ui.__mem_func__(self.OnClose))
		self.btnCancel.SetEvent(ui.__mem_func__(self.OnClose))
		self.btnAccept.SetEvent(ui.__mem_func__(self.OnAccept))

		self.tooltipItem = None
		_DressR1(self, "absorb")

	def SetItemToolTip(self, itemTooltip):
		self.tooltipItem = itemTooltip

	def IsOpened(self):
		if self.IsShow() and self.isLoaded:
			return True

		return False

	def Open(self):
		self.PositionOut = 0
		(self.PositionStartX, self.PositionStartY, z) = player.GetMainCharacterPosition()
		for i in range(acce.WINDOW_MAX_MATERIALS + 1):
			self.acceSlot.ClearSlot(i)

		player.SetAcceRefineWindowOpen(1)
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_ACCE_ABSORB)
				self.interface.RefreshMarkInventoryBag()

		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = False

	def Close(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

		if app.ENABLE_ANIMATED_WINDOW: 	
			if self.bClosed == False:
				self.Hide()
		else:
			self.Hide()

		if app.ENABLE_ANIMATED_WINDOW: 
			self.bClosed = True

	def OnClose(self):
		self.Close()
		player.SetAcceRefineWindowOpen(0)
		acce.SendCloseRequest()

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.__ClearTradableIconState()

	def OnPressEscapeKey(self):
		self.OnClose()
		return True

	def OnAccept(self):
		acce.SendRefineRequest()

	def RefuseMaterial(self, invenType, slotPos, targetSlot):
		"""only a weapon is absorbed (acceabsorbpolicy); anything else stays in the inventory with a
		message instead of being sent. Returns True when the item was refused."""
		itemIndex = player.GetItemIndex(invenType, slotPos)
		if not itemIndex:
			return False
		item.SelectItem(itemIndex)
		refusal = acceabsorbpolicy.Refusal(item, targetSlot)
		if refusal:
			chat.AppendChat(chat.CHAT_TYPE_INFO, refusal)
			return True
		return False

	if app.WJ_ENABLE_TRADABLE_ICON:
		def __ClearTradableIconState(self):
			if self.interface:
				try:
					self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
					self.interface.RefreshMarkInventoryBag()
				except AttributeError:
					pass

			self.ItemListIdx = None

		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

		def SetInven(self, inven):
			self.inven = inven

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			def SetSpecialInven(self, invenSpecial):
				self.invenSpecial = invenSpecial

		def CantTradableItem(self, slotIndex):
			itemIndex = player.GetItemIndex(slotIndex)

			if itemIndex:
				item.SelectItem(itemIndex)

				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0: #봉인아이템 걸러냄.
						return True

				if not acceabsorbpolicy.IsAbsorbable(item): # a sash or a weapon, never armour
					return True
					
				#check limit 120lv
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_LEVEL == limitType:
						if limitValue == 120:
							return True
				#check limit 120lv

			return False

		def OnTop(self):
			self.tooltipItem.SetTop()
			if not self.interface:
				return

			self.interface.SetOnTopWindow(player.ON_TOP_WND_ACCE_ABSORB)
			self.interface.RefreshMarkInventoryBag()

		def AcceItemMouseEvent(self):
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if not self.inven or not self.invenSpecial:
					return
			else:
				if not self.inven:
					return

			if not self.ItemListIdx:
				return

			page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				special_page = self.invenSpecial.GetInventoryPageIndex()

			if self.ItemListIdx:
				for i in self.ItemListIdx:
					if (page * INVENTORY_PAGE_SIZE) <= i < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						lock_idx = i - (page * INVENTORY_PAGE_SIZE)
						self.inven.wndItem.SetCantMouseEventSlot(lock_idx)

					if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
						if self.invenSpecial.GetInventoryType() == 0:
							if (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.SKILL_BOOK_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 1:
							if (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 2:
							if (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.STONE_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 3:
							if (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.GIFT_BOX_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 4:
							if (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.SWITCH_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 5:
							if (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.COSTUME_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

	def OnUpdate(self):
		LIMIT_RANGE = acce.LIMIT_RANGE
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.PositionStartX) >= LIMIT_RANGE or abs(y - self.PositionStartY) >= LIMIT_RANGE:
			if not self.PositionOut:
				self.PositionOut += 1
				self.OnClose()
				return

		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.IsShow():
				self.AcceItemMouseEvent()

	def OnSelectEmptySlot(self, selectedSlotPos):
		isAttached = mouseModule.mouseController.isAttached()
		if not isAttached or selectedSlotPos == acce.WINDOW_MAX_MATERIALS:
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)

		if player.GetItemSealDate(player.INVENTORY, attachedSlotPos) == -1 or player.GetItemSealDate(player.INVENTORY, attachedSlotPos) > 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_NOT_SEALITEM)
			return

		mouseModule.mouseController.DeattachObject()
		#if attachedSlotType == player.SLOT_TYPE_INVENTORY and attachedInvenType == player.INVENTORY:
		if attachedSlotType == player.SLOT_TYPE_INVENTORY or attachedSlotType == player.SLOT_TYPE_COSTUME_INVENTORY:
			if self.RefuseMaterial(attachedInvenType, attachedSlotPos, selectedSlotPos):
				return
			acce.Add(attachedInvenType, attachedSlotPos, selectedSlotPos)

	def OnSelectItemSlot(self, selectedSlotPos):
		if selectedSlotPos == acce.WINDOW_MAX_MATERIALS:
			return

		mouseModule.mouseController.DeattachObject()
		acce.Remove(selectedSlotPos)

	def OnOverInItem(self, selectedSlotPos):
		if self.tooltipItem:
			if selectedSlotPos == acce.WINDOW_MAX_MATERIALS:
				(isHere1, iCell1) = acce.GetAttachedItem(0)
				(isHere2, iCell2) = acce.GetAttachedItem(1)
				if isHere1 and isHere2:
					self.tooltipItem.SetAcceResultAbsItem(iCell1, iCell2)
			else:
				(isHere, iCell) = acce.GetAttachedItem(selectedSlotPos)
				if isHere:
					self.tooltipItem.SetInventoryItem(iCell)

	def OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def Refresh(self, iAct):
		self.acceSlot.ClearSlot(acce.WINDOW_MAX_MATERIALS)

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = []

		for i in range(acce.WINDOW_MAX_MATERIALS):
			self.acceSlot.ClearSlot(i)

			(isHere, iCell) = acce.GetAttachedItem(i)
			if isHere:
				self.acceSlot.SetItemSlot(i, player.GetItemIndex(iCell), 0)

				if app.WJ_ENABLE_TRADABLE_ICON:
					self.ItemListIdx.append(iCell)

				if i == int(acce.WINDOW_MAX_MATERIALS - 1):
					(itemVnum, MinAbs, MaxAbs) = acce.GetResultItem()
					if not itemVnum:
						break

					self.acceSlot.SetItemSlot(i + 1, itemVnum, 0)
					break
