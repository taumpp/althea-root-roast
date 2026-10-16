import player
import exchange
import net
import localeInfo
import chat
import item
import uiCommon
import ui
import mouseModule
import slotwindowpolicy
import uiPickMoney
import wndMgr
import app
import time
import playerSettingModule
import exchangequickadd
###################################################################################################
## Exchange
if app.WJ_ENABLE_TRADABLE_ICON:
	INVENTORY_PAGE_SIZE = player.INVENTORY_PAGE_SIZE
	if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
		SPECIAL_INVENTORY_PAGE_SIZE = player.SPECIAL_INVENTORY_PAGE_SIZE

class ExchangeDialog(ui.ScriptWindow):
	FACE_IMAGE_DICT = {
						playerSettingModule.RACE_WARRIOR_M : "icon/face/warrior_m.tga",
						playerSettingModule.RACE_WARRIOR_W : "icon/face/warrior_w.tga",
						playerSettingModule.RACE_ASSASSIN_M : "icon/face/assassin_m.tga",
						playerSettingModule.RACE_ASSASSIN_W : "icon/face/assassin_w.tga",
						playerSettingModule.RACE_SURA_M : "icon/face/sura_m.tga",
						playerSettingModule.RACE_SURA_W : "icon/face/sura_w.tga",
						playerSettingModule.RACE_SHAMAN_M : "icon/face/shaman_m.tga",
						playerSettingModule.RACE_SHAMAN_W : "icon/face/shaman_w.tga",
	}
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.TitleName = 0
		self.tooltipItem = 0
		self.xStart = 0
		self.yStart = 0
		self.interface = None
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None

	class Item(ui.ListBoxEx.Item):
		def __init__(self,parent, text, value=0):
			ui.ListBoxEx.Item.__init__(self)
			self.textBox=ui.TextLine()
			self.textBox.SetParent(self)
			self.textBox.SetText(text)
			self.textBox.Show()
			self.value = value

		def GetValue(self):
			return self.value

		def __del__(self):
			ui.ListBoxEx.Item.__del__(self)

	def LoadDialog(self):
		PythonScriptLoader = ui.PythonScriptLoader()
		if app.ENABLE_NEW_EXCHANGE_WINDOW:
			PythonScriptLoader.LoadScriptFile(self, "UIScript/exchangedialog_new.py")
		else:
			PythonScriptLoader.LoadScriptFile(self, "UIScript/exchangedialog.py")


		## Owner
		self.OwnerSlot = self.GetChild("Owner_Slot")
		self.OwnerSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectOwnerEmptySlot))
		self.OwnerSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectOwnerItemSlot))
		self.OwnerSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInOwnerItem))
		self.OwnerSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.OwnerMoney = self.GetChild("Owner_Money_Value")
		if not app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.OwnerAcceptLight = self.GetChild("Owner_Accept_Light")
			self.OwnerAcceptLight.Disable()
		self.OwnerMoneyButton = self.GetChild("Owner_Money")
		self.OwnerMoneyButton.SetEvent(ui.__mem_func__(self.OpenPickMoneyDialog))

		## Target
		self.TargetSlot = self.GetChild("Target_Slot")
		self.TargetSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInTargetItem))
		self.TargetSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.TargetMoney = self.GetChild("Target_Money_Value")
		if not app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.TargetAcceptLight = self.GetChild("Target_Accept_Light")
			self.TargetAcceptLight.Disable()

		## PickMoneyDialog
		dlgPickMoney = uiPickMoney.PickMoneyDialog()
		dlgPickMoney.LoadDialog()
		dlgPickMoney.SetAcceptEvent(ui.__mem_func__(self.OnPickMoney))
		dlgPickMoney.SetTitleName(localeInfo.EXCHANGE_MONEY)
		dlgPickMoney.SetMax(13)
		dlgPickMoney.Hide()
		self.dlgPickMoney = dlgPickMoney

		## Button
		self.AcceptButton = self.GetChild("Owner_Accept_Button")
		self.AcceptButton.SetToggleDownEvent(ui.__mem_func__(self.AcceptExchange))
		if app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.TargetAcceptButton = self.GetChild("Target_Accept_Button")

		self.TitleName = self.GetChild("TitleName")
		self.GetChild("TitleBar").SetCloseEvent(net.SendExchangeExitPacket)

		if app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.FaceOwnerImage = self.GetChild("FaceOwner_Image")
			self.FaceTargetImage = self.GetChild("FaceTarget_Image")
			self.TargetName = self.GetChild("target_NameText")
			self.TargetLevel = self.GetChild("target_LvText")
			self.ExchangeLogs = self.GetChild("ExchangeLogs")
			self.LogsScrollBar = ui.ThinScrollBar()
			self.LogsScrollBar.SetParent(self.ExchangeLogs)
			self.LogsScrollBar.SetPosition(442 - 75, 17)
			self.LogsScrollBar.SetScrollBarSize(50)
			self.LogsScrollBar.Show()
			self.LogsDropList = ui.ListBoxEx()
			self.LogsDropList.SetParent(self.ExchangeLogs)
			self.LogsDropList.itemHeight = 12
			self.LogsDropList.itemStep = 13
			self.LogsDropList.SetPosition(35, 27)
			self.LogsDropList.SetSize(0, 45)
			self.LogsDropList.SetScrollBar(self.LogsScrollBar)
			self.LogsDropList.SetViewItemCount(2)
			self.LogsDropList.Show()
			self.LogsScrollBar.Show()
			self.listOwnerSlot = []
			self.listTargetSlot = []

	def Destroy(self):
		#print "---------------------------------------------------------------------------- DESTROY EXCHANGE"
		self.ClearDictionary()
		self.dlgPickMoney.Destroy()
		self.dlgPickMoney = 0
		self.OwnerSlot = 0
		self.OwnerMoney = 0
		if not app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.OwnerAcceptLight = 0
		self.OwnerMoneyButton = 0
		self.TargetSlot = 0
		self.TargetMoney = 0
		if not app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.TargetAcceptLight = 0
		self.TitleName = 0
		self.AcceptButton = 0
		if app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.TargetAcceptButton = 0
			self.FaceOwnerImage = None
			self.FaceTargetImage = None
			self.TargetName = None
			self.TargetLevel = None
			self.ExchangesLogsWindow = None
			self.LogsDropList.RemoveAllItems()
			self.LogsScrollBar = None
			self.LogsDropList = None
		self.tooltipItem = 0

	def OpenDialog(self):
		if app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.TitleName.SetText(localeInfo.EXCHANGE_TITLE_LEVEL % (exchange.GetNameFromTarget(), exchange.GetLevelFromTarget()))
		else:
			self.TitleName.SetText(localeInfo.EXCHANGE_TITLE % (exchange.GetNameFromTarget()))

		self.AcceptButton.Enable()
		self.AcceptButton.SetUp()
		if app.ENABLE_NEW_EXCHANGE_WINDOW:
			self.TargetAcceptButton.Disable()
			self.TargetAcceptButton.SetUp()
			self.FaceOwnerImage.LoadImage(self.FACE_IMAGE_DICT[exchange.GetRaceFromSelf()])
			self.FaceTargetImage.LoadImage(self.FACE_IMAGE_DICT[exchange.GetRaceFromTarget()])
			self.TargetName.SetText(exchange.GetNameFromTarget())
			self.TargetLevel.SetText(localeInfo.NEW_EXCHANGE_LEVEL % (exchange.GetLevelFromTarget()))
			self.LogsDropList.RemoveAllItems()
			self.LogsDropList.AppendItem(self.Item(self, localeInfo.NEW_EXCHANGE_YOU_READY % (str(time.strftime("[%H:%M:%S]"))), 0))
		exchangequickadd.Reset()
		self.SetTop()
		self.Show()

		(self.xStart, self.yStart, z) = player.GetMainCharacterPosition()

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = None ## Fix OnUpdate syserr
			self.ItemListIdx = []

	def CloseDialog(self):
		wndMgr.OnceIgnoreMouseLeftButtonUpEvent()

		if 0 != self.tooltipItem:
			self.tooltipItem.HideToolTip()

		self.dlgPickMoney.Close()
		self.Hide()
		exchangequickadd.Reset()
		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()

			self.ItemListIdx = None

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def OpenPickMoneyDialog(self):
		if exchange.GetElkFromSelf() > 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.EXCHANGE_CANT_EDIT_MONEY)
			return

		self.dlgPickMoney.Open(player.GetElk())

	def OnPickMoney(self, money):
		net.SendExchangeElkAddPacket(money)

	def AcceptExchange(self):
		if app.ENABLE_NEW_EXCHANGE_WINDOW:
			atLeastOneItem = 0
			atLeastOneYang = 0
			for i in range(exchange.EXCHANGE_ITEM_MAX_NUM):
				itemCount = exchange.GetItemCountFromTarget(i)
				if itemCount >= 1:
					atLeastOneYang = 1
					break
			
			if exchange.GetElkFromTarget() >= 1:
				atLeastOneYang = 1
			
			if atLeastOneItem or atLeastOneYang:
				net.SendExchangeAcceptPacket()
				self.AcceptButton.Disable()
			else:
				atLeastOneItem = 0
				atLeastOneYang = 0
				for i in range(exchange.EXCHANGE_ITEM_MAX_NUM):
					itemCount = exchange.GetItemCountFromSelf(i)
					if itemCount >= 1:
						atLeastOneYang = 1
						break
				
				if exchange.GetElkFromSelf() >= 1:
					atLeastOneYang = 1
				
				if atLeastOneItem or atLeastOneYang:
					self.questionDialog = uiCommon.QuestionDialog2()
					self.questionDialog.SetText1(localeInfo.NEW_EXCHANGE_ALERT1)
					self.questionDialog.SetText2(localeInfo.NEW_EXCHANGE_ALERT2)
					self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.AcceptQuestion))
					self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
					self.questionDialog.Open()
				else:
					net.SendExchangeAcceptPacket()
					self.AcceptButton.Disable()
		else:
			net.SendExchangeAcceptPacket()
			self.AcceptButton.Disable()

	if app.ENABLE_NEW_EXCHANGE_WINDOW:
		def AcceptQuestion(self):
			net.SendExchangeAcceptPacket()
			self.AcceptButton.Disable()
			if self.questionDialog:
				self.questionDialog.Close()
			
			self.questionDialog = None

		def OnCloseQuestionDialog(self):
			if self.questionDialog:
				self.questionDialog.Close()
			
			self.questionDialog = None
			self.AcceptButton.Enable()
			self.AcceptButton.SetUp()

	def SelectOwnerEmptySlot(self, SlotIndex):
		if False == mouseModule.mouseController.isAttached():
			return

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if player.GetAcceRefineWindowOpen() == 1:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_NOT_WINDOWOPEN)
				return

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if player.GetChangeLookWindowOpen() == 1:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHANGE_LOOK_OPEN_OTHER_WINDOW)
				return

		if mouseModule.mouseController.IsAttachedMoney():
			net.SendExchangeElkAddPacket(mouseModule.mouseController.GetAttachedMoneyAmount())
		else:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()

			if slotwindowpolicy.IsOwnedItemSlotType(attachedSlotType):

				attachedInvenType = slotwindowpolicy.ItemWindowForSlotType(attachedSlotType)
				if player.RESERVED_WINDOW == attachedInvenType:
					mouseModule.mouseController.DeattachObject()
					return
				SrcSlotNumber = mouseModule.mouseController.GetAttachedSlotNumber()
				DstSlotNumber = SlotIndex

				itemID = player.GetItemIndex(attachedInvenType, SrcSlotNumber)
				item.SelectItem(itemID)

				#if player.IsAntiFlagBySlot(SrcSlotNumber, item.ANTIFLAG_GIVE):
				if item.IsAntiFlag(item.ANTIFLAG_GIVE):
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.EXCHANGE_CANNOT_GIVE)
					mouseModule.mouseController.DeattachObject()
					return

				net.SendExchangeItemAddPacket(attachedInvenType, SrcSlotNumber, DstSlotNumber)
				if app.WJ_ENABLE_TRADABLE_ICON:
					self.ItemListIdx.append(SrcSlotNumber)

		mouseModule.mouseController.DeattachObject()

	def SelectOwnerItemSlot(self, SlotIndex):
		if player.ITEM_MONEY == mouseModule.mouseController.GetAttachedItemIndex():
			money = mouseModule.mouseController.GetAttachedItemCount()
			net.SendExchangeElkAddPacket(money)

	def RefreshOwnerSlot(self):
		for i in range(exchange.EXCHANGE_ITEM_MAX_NUM):
			itemIndex = exchange.GetItemVnumFromSelf(i)
			itemCount = exchange.GetItemCountFromSelf(i)
			if 1 == itemCount:
				itemCount = 0
			self.OwnerSlot.SetItemSlot(i, itemIndex, itemCount)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				changelookvnum = exchange.GetChangeLookVnumFromSelf(i)
				if not changelookvnum == 0 and itemIndex != osfInfo.SUPPORT_ITEM_VNUM:
					self.OwnerSlot.SetSlotCoverImage(i, "icon/item/ingame_convert_Mark.tga")
				else:
					self.OwnerSlot.EnableSlotCoverImage(i, False)

		self.OwnerSlot.RefreshSlot()

	def RefreshTargetSlot(self):
		for i in range(exchange.EXCHANGE_ITEM_MAX_NUM):
			itemIndex = exchange.GetItemVnumFromTarget(i)
			itemCount = exchange.GetItemCountFromTarget(i)
			if 1 == itemCount:
				itemCount = 0
			self.TargetSlot.SetItemSlot(i, itemIndex, itemCount)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				changelookvnum = exchange.GetChangeLookVnumFromTarget(i)
				if not changelookvnum == 0 and itemIndex != osfInfo.SUPPORT_ITEM_VNUM:
					self.TargetSlot.SetSlotCoverImage(i, "icon/item/ingame_convert_Mark.tga")
				else:
					self.TargetSlot.EnableSlotCoverImage(i, False)

		self.TargetSlot.RefreshSlot()

	def Refresh(self):
		self.RefreshOwnerSlot()
		self.RefreshTargetSlot()

		self.OwnerMoney.SetText(str(localeInfo.AddPointToNumberString(exchange.GetElkFromSelf())))
		self.TargetMoney.SetText(str(localeInfo.AddPointToNumberString(exchange.GetElkFromTarget())))

		if True == exchange.GetAcceptFromSelf():
			if not app.ENABLE_NEW_EXCHANGE_WINDOW:
				self.OwnerAcceptLight.Down()
			else:
				self.OwnerSlot.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 0.3500, 0.8500, 0.3500, 1.0)
				self.LogsDropList.AppendItem(self.Item(self, localeInfo.NEW_EXCHANGE_YOU_ACCEPT % (str((time.strftime("[%H:%M:%S]")))), 0))
		else:
			self.AcceptButton.Enable()
			self.AcceptButton.SetUp()
			if not app.ENABLE_NEW_EXCHANGE_WINDOW:
				self.OwnerAcceptLight.SetUp()
			else:
				self.OwnerSlot.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 1.0, 1.0, 1.0, 1.0)

		if True == exchange.GetAcceptFromTarget():
			if not app.ENABLE_NEW_EXCHANGE_WINDOW:
				self.TargetAcceptLight.Down()
			else:
				self.TargetAcceptButton.Down()
				self.TargetSlot.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 0.3500, 0.8500, 0.3500, 1.0)
				self.LogsDropList.AppendItem(self.Item(self, localeInfo.NEW_EXCHANGE_ACCEPT % (str((time.strftime("[%H:%M:%S]"))), exchange.GetNameFromTarget()), 0))
		else:
			if not app.ENABLE_NEW_EXCHANGE_WINDOW:
				self.TargetAcceptLight.SetUp()
			else:
				if self.TargetAcceptButton.IsDown() == True:
					self.LogsDropList.AppendItem(self.Item(self, localeInfo.NEW_EXCHANGE_ABORT % (str((time.strftime("[%H:%M:%S]"))), exchange.GetNameFromTarget()), 0))
				
				self.TargetAcceptButton.SetUp()
				self.TargetSlot.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 1.0, 1.0, 1.0, 1.0)

	def OverInOwnerItem(self, slotIndex):
		if 0 != self.tooltipItem:
			self.tooltipItem.SetExchangeOwnerItem(slotIndex)

	def OverInTargetItem(self, slotIndex):
		if 0 != self.tooltipItem:
			self.tooltipItem.SetExchangeTargetItem(slotIndex)

	def OverOutItem(self):
		if 0 != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	if not app.WJ_ENABLE_TRADABLE_ICON:
		def OnTop(self):
			self.tooltipItem.SetTop()

	def OnUpdate(self):
		USE_EXCHANGE_LIMIT_RANGE = 1000

		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xStart) > USE_EXCHANGE_LIMIT_RANGE or abs(y - self.yStart) > USE_EXCHANGE_LIMIT_RANGE:
			(self.xStart, self.yStart, z) = player.GetMainCharacterPosition()
			net.SendExchangeExitPacket()

		if app.WJ_ENABLE_TRADABLE_ICON:
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if not self.inven or not self.invenSpecial:
					return
			else:
				if not self.inven:
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

	def OnPressEscapeKey(self):
		net.SendExchangeExitPacket()
		return True

	if app.WJ_ENABLE_TRADABLE_ICON:
		def CantTradableItem(self, slotIndex):
			itemIndex = player.GetItemIndex(slotIndex)

			if itemIndex:
				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0: #봉인아이템 걸러냄.
						return True

				return player.IsAntiFlagBySlot(slotIndex, item.ANTIFLAG_GIVE)

			return False

		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

		def OnTop(self):
			self.tooltipItem.SetTop()
			if not self.interface:
				return

			self.interface.SetOnTopWindow(player.ON_TOP_WND_EXCHANGE)
			self.interface.RefreshMarkInventoryBag()

		def SetInven(self, inven):
			self.inven = inven

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			def SetSpecialInven(self, invenSpecial):
				self.invenSpecial = invenSpecial

		def AddExchangeItemSlotIndex(self, idx):
			self.ItemListIdx.append(idx)