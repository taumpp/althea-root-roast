# -*- coding: utf-8 -*-
import ui
import uiScriptLocale
import app
import net
import dbg
import snd
import player
import mouseModule
import wndMgr
import skill
import localeInfo
import uiToolTip
import constInfo
import chr
import item
import chat
import uiCommon
import uiAffectShower
import functools
import event
import uipetcompact
import mountfeedmodel
import growthpetpresentation

SKILL_SLOT_ENABLE	= "d:/ymir work/ui/pet/album_c/skill-lock.png"
SKILL_SLOT_MAX		= player.PET_SKILL_COUNT_MAX

FEED_WINDOW_X_SIZE = 3
FEED_WINDOW_Y_SIZE = 3

VISIBLE_LINE_COUNT = 4
DEFAULT_DESC_Y = 7

def _LocalePetHeart(key, fallback):
	return getattr(uiScriptLocale, key, fallback)

def unsigned32(n):
	return n & 0xFFFFFFFF
	

"""
		PetHatchingWindow will appear when hatching an egg.
		It can be closed manually or after successful egg hatch.
"""
class PetHatchingWindow(ui.ScriptWindow):
	def __init__(self, wndPetInformation):
		import exception

		if not wndPetInformation:
			exception.Abort("wndPetInformation parameter must be set to PetInformationWindow")
			return						
			 	 
		ui.ScriptWindow.__init__(self)

		self.isLoaded = 0
		self.hatchingSlot = 0
		self.eggItemSlotIndex  = -1
		self.eggItemSlotWindow = player.INVENTORY
		self.wndPetInformation = wndPetInformation
		self.hatchingButton = 0
		self.petNameEdit = 0
		self.petName = 0
		self.questionDialog = 0
		self.popupDialog = 0
		self.hatchingMoneyText = None
			
		self.__LoadWindow()
	
	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
	def Show(self):
		self.__LoadWindow()
		ui.ScriptWindow.Show(self)		
		self.SetTop()
		
	def Close(self):
		self.ClearMouseEventEggItem()
		self.hatchingSlot.SetItemSlot(0, 0)
		self.hatchingSlot.RefreshSlot()
		self.petName = 0
			
		self.Hide()
		player.SetOpenPetHatchingWindow(False)
		net.SendPetHatchingWindowPacket(False)
		
		if self.questionDialog:
			self.questionDialog.Close()
			
		if self.popupDialog:
			self.popupDialog.Close()
			
		if self.petNameEdit:
			self.petNameEdit.KillFocus()
		
	def Destroy(self):
		self.isLoaded = 0
		self.hatchingSlot = 0
		self.wndPetInformation = 0
		self.hatchingButton = 0
		self.petName = 0
		self.hatchingMoneyText = None
		
		if self.popupDialog:
			self.popupDialog.Destroy()
		
	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			self.__LoadScript("UIScript/petHatchingWindow.py")
				
		except:
			import exception
			exception.Abort("petHatchingWindow.LoadWindow.LoadObject")
			
			
		try:
			self.GetChild("PetHatching_TitleBar").SetCloseEvent(ui.__mem_func__(self.Close))
			self.hatchingSlot = self.GetChild("HatchingItemSlot")
			self.hatchingSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			self.hatchingSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))			
			self.hatchingSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			
			# Hatch button
			self.hatchingButton = self.GetChild("HatchingButton")
			self.hatchingButton.SetEvent(ui.__mem_func__(self.ClickHatchingButton))
				
			# Hatch price text
			self.hatchingMoneyText = self.GetChild("HatchingMoney");
			self.hatchingMoneyText.SetText(localeInfo.PET_HATCHING_MONEY % localeInfo.NumberToMoneyString(0))
			
			# Pet name editline
			self.petNameEdit = self.GetChild("pet_name")
			self.petNameEdit.SetText("")
			self.petNameEdit.SetReturnEvent(ui.__mem_func__(self.ClickHatchingButton))
			self.petNameEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
			self.petNameEdit.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.OnMouseLeftButtonUpEvent))
			self.petNameEdit.SetFocus()
			self.petNameEdit.Show()
			
			# Initialize question and popup dialogs
			self.__MakeQuestionDialog()
			self.__MakePopupDialog()
			
			
		except:
			import exception
			exception.Abort("petHatchingWindow.LoadWindow.BindObject")
			
	def __LoadScript(self, fileName):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, fileName)
		
	def __MakeQuestionDialog(self):
		if not self.questionDialog:
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText("")
			
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__HatchingQuestionDialogAccept))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__HatchingQuestionDialogCancel))
		
		
	def __MakePopupDialog(self):
		self.popupDialog = uiCommon.PopupDialog()
		self.popupDialog.SetText("")
		
	def ClickHatchingButton(self):
		if self.popupDialog:
			if self.popupDialog.IsShow():
				return
				
		self.__OpenHatchingQuestionDialog()
		
	def OnMouseLeftButtonUpEvent(self):
		if self.petName == self.petNameEdit.GetText():
			self.petNameEdit.SetText("")
			self.petNameEdit.SetEndPosition()
			
		
	def OverInItem(self, slotIndex):
		return
		
	def OverOutItem(self):
		return
		
	def ClearMouseEventEggItem(self):
		if self.eggItemSlotIndex == -1:
			return
			
		# Unlock egg item
		inven_slot_pos = self.eggItemSlotIndex
			
		if inven_slot_pos >= player.INVENTORY_PAGE_SIZE:
			inven_page = self.wndPetInformation.inven.GetInventoryPageIndex()
			inven_slot_pos -= (inven_page * player.INVENTORY_PAGE_SIZE)
					
		self.wndPetInformation.inven.wndItem.SetCanMouseEventSlot(inven_slot_pos)
	
		# Reset egg item position
		self.eggItemSlotIndex  = -1
		self.eggItemSlotWindow = player.INVENTORY
		
	def OnUpdate(self):

		if not self.wndPetInformation.inven:
			return
			
		if self.eggItemSlotIndex == -1:
			return
			
		if not self.hatchingSlot:
			return		
		
		try:
			inven = self.wndPetInformation.inven
			invenPage = inven.GetInventoryPageIndex()
		
			min_range = invenPage * player.INVENTORY_PAGE_SIZE
			max_range = (invenPage + 1) * player.INVENTORY_PAGE_SIZE
			
			# Lock egg item
			inven_slot_pos = self.eggItemSlotIndex
			
			if min_range <= inven_slot_pos < max_range:
				inven_slot_pos = inven_slot_pos - min_range
				inven.wndItem.SetCantMouseEventSlot(inven_slot_pos)
			
		except:
			pass
				
		return
		
	def HatchingWindowOpen(self, slotWindow, slotIndex):
		# Check if player has no other trading windows opened
		checkMsg = net.CheckUsePetItem()
		
		if checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_TRADING:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		elif checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_SHOP_OPEN:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		elif checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_MALL_OPEN:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		elif checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_SAFEBOX_OPEN:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		if checkMsg != item.PET_EGG_USE_TRUE:
			return
			
		if not self.hatchingSlot:
			return
			
		ItemVNum = player.GetItemIndex(slotWindow, slotIndex)
		
		if ItemVNum == 0:
			return
			
		item.SelectItem(ItemVNum)
		
		growthPetVnum = item.GetValue(0)
			
		if growthPetVnum == 0:
			return

		hatching_money_value = item.GetValue(3)
		if self.hatchingMoneyText:
			self.hatchingMoneyText.SetText(localeInfo.PET_HATCHING_MONEY % localeInfo.NumberToMoneyString(hatching_money_value))
		
		self.Close()
		self.eggItemSlotIndex  = slotIndex
		self.eggItemSlotWindow = slotWindow
		self.hatchingSlot.SetItemSlot(0, growthPetVnum)
		self.hatchingSlot.RefreshSlot()
		item_string = item.GetItemName()
		self.petName = item_string[:item.PET_NAME_MAX_SIZE]
		self.petNameEdit.SetText(self.petName)
		self.petNameEdit.SetEndPosition()
		self.petNameEdit.SetFocus()
		self.petNameEdit.Show()
		self.Show()
		net.SendPetHatchingWindowPacket(True)
		player.SetOpenPetHatchingWindow(True)
		
	def __OpenHatchingQuestionDialog(self):
		interface = self.wndPetInformation.interface
		
		if interface.IsShowDlgQuestionWindow():
			interface.CloseDlgQuestionWindow()
			
		if not self.questionDialog:
			self.__MakeQuestionDialog()
			
		# Reset position if name has no characters inside editline
		if "" == self.petNameEdit.GetText():
			self.petNameEdit.SetText(self.petName)
			self.petNameEdit.SetEndPosition()
			
		self.questionDialog.SetText(localeInfo.PET_HATCHING_ACCEPT % (self.petNameEdit.GetText()))
		self.questionDialog.SetTop()
		self.questionDialog.Open()
		
		
	def __HatchingQuestionDialogAccept(self):
		self.questionDialog.Close()
		
		# Check if pet's name is smaller than defined minimal size (item.PET_NAME_MIN_SIZE)
		if len(self.petNameEdit.GetText()) < item.PET_NAME_MIN_SIZE:
			self.petNameEdit.SetText("")
			self.__OpenPopupDialog(localeInfo.PET_NAME_MIN)
			return

		itemVnum = player.GetItemIndex(self.eggItemSlotWindow, self.eggItemSlotIndex)
		if itemVnum == 0:
			return
			
		item.SelectItem(itemVnum)
		hatching_money = item.GetValue(3)
		
		# Check if player has enough money to hatch an egg
		if player.GetMoney() < hatching_money:
			self.__OpenPopupDialog(localeInfo.PET_MSG_NOT_ENOUGH_MONEY)
			return		
			
		net.SendPetHatchingPacket(self.petNameEdit.GetText(), self.eggItemSlotWindow, self.eggItemSlotIndex)
		
	def __HatchingQuestionDialogCancel(self):
		self.questionDialog.Close()
		
	def __OpenPopupDialog(self, str):
		interface = self.wndPetInformation.interface
		
		if interface.IsShowDlgQuestionWindow():
			interface.CloseDlgQuestionWindow()
		
		if not self.popupDialog:
			self.__MakePopupDialog()
			
		self.popupDialog.SetText(str)
		self.popupDialog.SetTop()
		self.popupDialog.Open()
	
	def PetHatchingWindowCommand(self, command):
		# Egg hatch succeeded, close the window
		if command == item.EGG_USE_SUCCESS:
			self.Close()
			
		# Egg hatch failed, clear the name
		elif command == item.EGG_USE_FAILED_BECAUSE_NAME:
			self.petNameEdit.SetText("")
			self.petNameEdit.SetEndPosition()
			
		# Egg hatch hit an error, close the window
		elif command == item.EGG_USE_FAILED_TIMEOVER:
				self.Close()
		
"""
		PetNameChangeWindow will appear when change name item is
		dragged to upbringing item. It can be closed manually or 
		after successful name change.
"""
class PetNameChangeWindow(ui.ScriptWindow):
	def __init__(self, wndPetInformation):
		import exception

		if not wndPetInformation:
			exception.Abort("wndPetInformation parameter must be set to PetInformationWindow")
			return						
			 	 
		ui.ScriptWindow.__init__(self)

		self.isLoaded					= 0
		self.wndPetInformation			= wndPetInformation
		
		self.nameChangeItemSlotIndex	= -1
		self.petItemSlotIndex			= -1
		
		self.petItemSlot		= None
		self.nameChangeButton	= None
		self.petNameEdit		= None
		self.petName			= None
		self.questionDialog		= None
		self.popupDialog		= None
		
		self.__LoadWindow()
	
	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
	def Show(self):
		self.__LoadWindow()
		ui.ScriptWindow.Show(self)		
		self.SetTop()
		
	def Close(self):
		self.ClearMouseEventItem()
		
		if self.petItemSlot:
			self.petItemSlot.SetItemSlot(0, 0)
			self.petItemSlot.RefreshSlot()
			
		self.petName = None
		self.Hide()
		
		player.SetOpenPetNameChangeWindow(False)
		net.SendPetNameChangeWindowPacket(False)
		
		if self.questionDialog:
			self.questionDialog.Close()
			
		if self.popupDialog:
			self.popupDialog.Close()
			
		if self.petNameEdit:
			self.petNameEdit.KillFocus()
			
		
	def Destroy(self):
		self.isLoaded			= 0
		self.wndPetInformation	= None
		self.petItemSlot		= None
		self.nameChangeButton	= None
		self.petName			= None
		
		if self.popupDialog:
			self.popupDialog.Destroy()
		
	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			self.__LoadScript("UIScript/petNameChangeWindow.py")
				
		except:
			import exception
			exception.Abort("petNameChangeWindow.LoadWindow.LoadObject")
			
			
		try:
			self.GetChild("PetNameChangeTitleBar").SetCloseEvent(ui.__mem_func__(self.Close))
			self.petItemSlot = self.GetChild("PetItemSlot")
			self.petItemSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			
			# Name change button
			self.nameChangeButton = self.GetChild("NameChangeButton")
			self.nameChangeButton.SetEvent(ui.__mem_func__(self.ClickNameChangeButton))
				
			# Pet change name price
			MoneyText = self.GetChild("NameChangeMoney");
			MoneyText.SetText(localeInfo.PET_HATCHING_MONEY % (localeInfo.NumberToMoneyString(item.PET_HATCHING_MONEY)))
			
			# Pet name editline
			self.petNameEdit = self.GetChild("pet_name")
			self.petNameEdit.SetText("")
			self.petNameEdit.SetReturnEvent(ui.__mem_func__(self.ClickNameChangeButton))
			self.petNameEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
			self.petNameEdit.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.OnMouseLeftButtonUpEvent))
			self.petNameEdit.SetFocus()
			self.petNameEdit.Show()
			
			# Initialize question and popup dialogs
			self.__MakeQuestionDialog()
			self.__MakePopupDialog()
			
			
		except:
			import exception
			exception.Abort("petNameChangeWindow.LoadWindow.BindObject")
			
	def __LoadScript(self, fileName):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, fileName)
		
	def __MakeQuestionDialog(self):
		if not self.questionDialog:
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText("")
			
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__NameChangeQuestionDialogAccept))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__NameChangeQuestionDialogCancel))
		
		
	def __MakePopupDialog(self):
		self.popupDialog = uiCommon.PopupDialog()
		self.popupDialog.SetText("")
		
	def ClickNameChangeButton(self):
		if self.popupDialog:
			if self.popupDialog.IsShow():
				return
				
		self.__OpenNameChangeQuestionDialog()
		
	def OnMouseLeftButtonUpEvent(self):
		if self.petName == self.petNameEdit.GetText():
			self.petNameEdit.SetText("")
			self.petNameEdit.SetEndPosition()

	def ClearMouseEventItem(self):
		if self.nameChangeItemSlotIndex == -1:
			return
			
		if self.petItemSlotIndex == -1:
			return
		
		# Unlock name change item
		if self.nameChangeItemSlotIndex >= player.INVENTORY_PAGE_SIZE:
			inven_page = self.wndPetInformation.inven.GetInventoryPageIndex()
			self.nameChangeItemSlotIndex -= (inven_page * player.INVENTORY_PAGE_SIZE)
					
		self.wndPetInformation.inven.wndItem.SetCanMouseEventSlot(self.nameChangeItemSlotIndex)
		
		# Unlock pet upbringing item
		if self.petItemSlotIndex >= player.INVENTORY_PAGE_SIZE:
			inven_page = self.wndPetInformation.inven.GetInventoryPageIndex()
			self.petItemSlotIndex -= (inven_page * player.INVENTORY_PAGE_SIZE)
					
		self.wndPetInformation.inven.wndItem.SetCanMouseEventSlot(self.petItemSlotIndex)
	
		# Reset item positions
		self.nameChangeItemSlotIndex	= -1
		self.petItemSlotIndex			= -1
		
	def OnUpdate(self):
		if not self.wndPetInformation.inven:
			return
			
		if self.nameChangeItemSlotIndex == -1:
			return
			
		if self.petItemSlotIndex == -1:
			return
			
		if not self.petItemSlot:
			return
		
		try:
			inven		= self.wndPetInformation.inven
			invenPage	= inven.GetInventoryPageIndex()
		
			min_range = invenPage * player.INVENTORY_PAGE_SIZE
			max_range = (invenPage + 1) * player.INVENTORY_PAGE_SIZE
			
			# Lock name change item
			inven_slot_pos = self.nameChangeItemSlotIndex
			if min_range <= inven_slot_pos < max_range:
				inven_slot_pos = inven_slot_pos - min_range
				inven.wndItem.SetCantMouseEventSlot(inven_slot_pos)
				
			# Lock pet upbringing item
			inven_slot_pos = self.petItemSlotIndex
			if min_range <= inven_slot_pos < max_range:
				inven_slot_pos = inven_slot_pos - min_range
				inven.wndItem.SetCantMouseEventSlot(inven_slot_pos)
		except:
			pass
				
		return
		
	def NameChangeWindowOpen(self, srcSlotIndex, dstSlotIndex):
		# Check if player has no other trading windows opened
		checkMsg = net.CheckUsePetItem()
		
		if checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_TRADING:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		elif checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_SHOP_OPEN:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		elif checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_MALL_OPEN:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		elif checkMsg == item.PET_EGG_USE_FAILED_BECAUSE_SAFEBOX_OPEN:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_EGG_ITEM_USE)
			
		if checkMsg != item.PET_EGG_USE_TRUE:
			return
			
		if not self.petItemSlot:
			return
		
		petItemVnum = player.GetItemIndex(dstSlotIndex)
		if 0 == petItemVnum:
			return
		
		metinSlot = [player.GetItemMetinSocket(dstSlotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		pet_id = metinSlot[2]
		if 0 == pet_id:
			return
			
		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
					
		self.Close()
		self.nameChangeItemSlotIndex	= srcSlotIndex
		self.petItemSlotIndex			= dstSlotIndex

		self.petItemSlot.SetItemSlot(0, petItemVnum)
		self.petItemSlot.RefreshSlot()
		self.petName = pet_nick
		self.petNameEdit.SetText(self.petName)
		self.petNameEdit.SetEndPosition()
		self.petNameEdit.SetFocus()
		self.petNameEdit.Show()
		self.Show()
		
		net.SendPetNameChangeWindowPacket(True)
		player.SetOpenPetNameChangeWindow(True)
		
	def __OpenNameChangeQuestionDialog(self):
		interface = self.wndPetInformation.interface
		
		if interface.IsShowDlgQuestionWindow():
			interface.CloseDlgQuestionWindow()
			
		if not self.questionDialog:
			self.__MakeQuestionDialog()
			
		# Reset position if name has no characters inside editline
		if "" == self.petNameEdit.GetText():
			self.petNameEdit.SetText(self.petName)
			self.petNameEdit.SetEndPosition()
			
		self.questionDialog.SetText(localeInfo.PET_NAME_CHANGE_ACCEPT % (self.petNameEdit.GetText()))
		self.questionDialog.SetTop()
		self.questionDialog.Open()
		
		
	def __NameChangeQuestionDialogAccept(self):
		self.questionDialog.Close()
		
		# Check if pet's name is smaller than defined minimal size (item.PET_NAME_MIN_SIZE)
		if len(self.petNameEdit.GetText()) < item.PET_NAME_MIN_SIZE:
			self.petNameEdit.SetText("")
			self.__OpenPopupDialog(localeInfo.PET_NAME_MIN)
			return
		
		# Check if player has enough money to change the name
		if player.GetMoney() < item.PET_HATCHING_MONEY:
			self.__OpenPopupDialog(localeInfo.PET_MSG_NOT_ENOUGH_MONEY)
			return			
			
		net.SendPetNameChangePacket(self.petNameEdit.GetText(), self.nameChangeItemSlotIndex, self.petItemSlotIndex)
		
	def __NameChangeQuestionDialogCancel(self):
		self.questionDialog.Close()
		
	def __OpenPopupDialog(self, str):
		interface = self.wndPetInformation.interface
		
		if interface.IsShowDlgQuestionWindow():
			interface.CloseDlgQuestionWindow()
		
		if not self.popupDialog:
			self.__MakePopupDialog()
			
		self.popupDialog.SetText(str)
		self.popupDialog.SetTop()
		self.popupDialog.Open()
			
	def PetNameChangeWindowCommand(self, command):
		# Name change succeeded, close the window
		if command == item.NAME_CHANGE_USE_SUCCESS:
			self.Close()
			
		# Name change has failed, clear the name
		elif command == item.NAME_CHANGE_USE_FAILED_BECAUSE_NAME:
			self.petNameEdit.SetText("")
			self.petNameEdit.SetEndPosition()
						
"""
		PetFeedWindow is opened through main pet interface.
		It consists of item slot grid on which player can
		drag items. Used for pet lifetime, evolve & item exp.
"""
class PetFeedWindow(ui.ScriptWindow):
	def __init__(self, wndPetInformation):
		import exception

		if not wndPetInformation:
			exception.Abort("wndPetInformation parameter must be set to PetInformationWindow")
			return						
			 	 
		ui.ScriptWindow.__init__(self)

		self.isLoaded = 0
		self.feedButtonClickTime = 0
		self.backupFeedItems = []
		self.feedDraft = {}
		self.wndPetInformation = wndPetInformation
		self.feedHint = None
		self.board = None
		
		self.questionDialogEmptyPos = -1
		self.questionDialogItemPos = -1
		
		self.__LoadWindow()
	
	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
	def Show(self):
		self.__LoadWindow()
		ui.ScriptWindow.Show(self)
		player.SetOpenPetFeedWindow(True)
		
		if self.wndPetInformation and self.wndPetInformation.inven:
			self.wndPetInformation.inven.Show()
				
	def ClearFeedItems(self):
		self.ClearMouseEventFeedItems()
		
		if self.FeedItemSlot:
			for slotPos in range(self.FeedItemSlot.GetSlotCount()):
				self.FeedItemSlot.ClearSlot(slotPos)
				
			self.FeedItemSlot.RefreshSlot()
		
	def SetOnTopWindowNone(self):
	
		if not self.wndPetInformation:
			return
			
		if not self.wndPetInformation.interface:
			return
			
		interface = self.wndPetInformation.interface
		interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
		interface.RefreshMarkInventoryBag()
		
	def Close(self):
		self.SetOnTopWindowNone()
		self.wndPetInformation.PetFeedToggleButtonUpAll()
		self.wndPetInformation.feedIndex = player.FEED_BUTTON_MAX
		self.ClearFeedItems()
		self.__ClearItemMoveQuestionDialog()
		
		self.Hide()
		
		player.SetOpenPetFeedWindow(False)
		
	def Destroy(self):
		del self.FeedItems[:]
		del	self.FeedItemsCount[:]
		del self.FeedItemDummy[:]
		self.FeedItems		= None
		self.FeedItemsCount	= None
		self.FeedItemSlot	= None
		self.FeedItemDummy  = None
		self.questionDialog = None
		self.feedHint = None
		self.board = None
		
		self.questionDialogEmptyPos = -1
		self.questionDialogItemPos = -1
	
	
	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			self.__LoadScript("UIScript/petFeedWindow.py")
				
		except:
			import exception
			exception.Abort("petFeedWindow.LoadWindow.LoadObject")
			
		try:
			self.board = self.GetChild("board")
			self.board.SetCloseEvent(ui.__mem_func__(self.Close))
			self.feedHint = self.GetChild("FeedHint")
			
			# Item slot grid
			FeedItemSlot = self.GetChild("FeedItemSlot")
			FeedItemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))			
			FeedItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			FeedItemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.UnselectItemSlot))
			FeedItemSlot.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
			FeedItemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
			FeedItemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
			self.FeedItemSlot = FeedItemSlot
			
			self.FeedItems		= []
			self.FeedItemsCount = []
			
			# Used as a sub-container for items to check their positions
			self.FeedItemDummy	= []
						
			self.ClearMouseEventFeedItems()
			
			self.feedButton = self.GetChild("FeedButton")
			if self.feedButton:
				self.feedButton.SetEvent(ui.__mem_func__(self.ClickPetFeedButton))
				
			self.questionDialog = uiCommon.QuestionDialog2()
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__ItemMoveQuestionDialogAccept))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__ItemMoveQuestionDialogCancel))
			self.questionDialog.Close()
			
		except:
			import exception
			exception.Abort("petFeedWindow.LoadWindow.BindObject")

	def SetFeedMode(self, index):
		isEvolution = index == player.FEED_EVOL_EVENT
		if self.board:
			if isEvolution:
				self.board.SetTitleName(
					_LocalePetHeart("PET_FEED_EVOLUTION_TITLE", u"Evoluce peta"))
			else:
				self.board.SetTitleName(
					_LocalePetHeart("PET_FEED_TITLE", u"Nakrmít mazlíčka"))
		if self.feedHint:
			if isEvolution:
				self.feedHint.SetText(_LocalePetHeart(
					"PET_FEED_INSERT_HINT", u"Vlož příslušnou knihu"))
			else:
				self.feedHint.SetText(_LocalePetHeart(
					"PET_FEED_MIXED_HINT", u"Krystaly nebo tyčinka"))
			
	def __LoadScript(self, fileName):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, fileName)
		
	def OverInItem(self, slotIndex):
		if None != self.wndPetInformation.tooltipItem:
			invenPos = self.FeedItems[slotIndex]
			if invenPos != -1:
				self.wndPetInformation.tooltipItem.SetInventoryItem(invenPos, player.INVENTORY)
				
		return
		
	def OverOutItem(self):
		if None != self.wndPetInformation.tooltipItem:
			self.wndPetInformation.tooltipItem.HideToolTip()
		return
		
	def UseItemSlot(self, slotIndex):
		self.RemoveItemSlot(slotIndex)
		return
	
	def UnselectItemSlot(self, slotIndex):
		self.RemoveItemSlot(slotIndex)
		return
		
	def SelectItemSlot(self, slotIndex):
	
		self.RemoveItemSlot(slotIndex)
		return
		
	def RemoveItemSlot(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			return
		
		# Unlock item that was inside feed window
		inven_slot_pos = self.FeedItems[slotIndex]
		if inven_slot_pos != -1:
			if inven_slot_pos >= player.INVENTORY_PAGE_SIZE:
				inven_page = self.wndPetInformation.inven.GetInventoryPageIndex()
				inven_slot_pos -= (inven_page * player.INVENTORY_PAGE_SIZE)
				
			self.wndPetInformation.inven.wndItem.SetCanMouseEventSlot(inven_slot_pos)
		
		self.DeleteDataDummySlot(slotIndex, self.FeedItems[slotIndex])
		self.FeedItems[slotIndex] = -1
		self.FeedItemsCount[slotIndex] = 0
		self.feedDraft.pop(slotIndex, None)
		self.FeedItemSlot.ClearSlot(slotIndex)		
		self.FeedItemSlot.RefreshSlot()

	# Search for empty slot space for item
	# If not found, return -1
	def SearchEmptySlot(self, size):
		
		for value in range(player.PET_FEED_SLOT_MAX):
			
			if 0 == self.FeedItemDummy[value]:	# Check if value inside this slot is empty
			
				if 1 == size:
					return value
					
				emptySlotIndex	= value
				searchSucceed	= True
				
				for i in range(size - 1):
					emptySlotIndex = emptySlotIndex + FEED_WINDOW_X_SIZE
				
					if emptySlotIndex >= player.PET_FEED_SLOT_MAX:
						searchSucceed = False
						continue
					
					if 1 == self.FeedItemDummy[emptySlotIndex]:
						searchSucceed = False
			
				if True == searchSucceed:
					return value
				
		return -1
	
	# Move items inside the feed window (item slot grid)
	def ItemMoveFeedWindow(self, slotWindow, attachSlotType, slotIndex):
		#if player.INVENTORY == slotWindow:
		#	attachSlotType = player.SLOT_TYPE_INVENTORY
		#else:
		#	return False
		checkTime = app.GetGlobalTimeStamp() - self.feedButtonClickTime
		if checkTime < 2:
			if slotIndex in self.backupFeedItems:
				return False
		else:
			self.backupFeedItems = []
	
		mouseModule.mouseController.DeattachObject()
		
		selectedItemVNum = player.GetItemIndex(slotWindow, slotIndex)
		count			 = player.GetItemCount(slotWindow, slotIndex)
		
		mouseModule.mouseController.AttachObject(self, attachSlotType, slotIndex, selectedItemVNum, count)
		
		item.SelectItem(selectedItemVNum)
		itemSize = item.GetItemSize()
		
		emptySlotPos = self.SearchEmptySlot(itemSize[1])

		if -1 != emptySlotPos:
			self.ProcessItemMove(slotIndex, emptySlotPos)
			return True
			
		return False
		
	def ProcessItemMove(self, slotIndex, emptySlotIndex):
		if self.wndPetInformation.CantFeedItem(slotIndex):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_FEED_TYPE)
			return
		itemVnum = player.GetItemIndex(player.INVENTORY, slotIndex)
		item.SelectItem(itemVnum)
		
		# If item has one or more attributes, display a question dialog to continue
		if item.GetItemType() in [item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR]:
			metinSlot = [player.GetItemMetinSocket(player.INVENTORY, slotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = [player.GetItemAttribute(player.INVENTORY, slotIndex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			
			attributeCount = 0
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				type = attrSlot[i][0]
				value = attrSlot[i][1]
				
				if value:
					attributeCount += 1
					
			if attributeCount:
				self.questionDialogEmptyPos = emptySlotIndex
				self.questionDialogItemPos = slotIndex
				
				self.questionDialog.SetText1(localeInfo.SECOND_CONFIRM_PET_FEED_QUESTION_1 % attributeCount)
				self.questionDialog.SetText2(localeInfo.SECOND_CONFIRM_PET_FEED_QUESTION_2)
				self.questionDialog.SetTop()
				self.questionDialog.Open()
				
				if mouseModule.mouseController.isAttached():
					mouseModule.mouseController.DeattachObject()
				return

		# Item did not have any attributes, move it to the feed window
		self.InsertItemToSlot(emptySlotIndex)

				
	def __ItemMoveQuestionDialogAccept(self):
		attachSlotType = player.SLOT_TYPE_INVENTORY
		selectedItemVNum = player.GetItemIndex(player.INVENTORY, self.questionDialogItemPos)
		count			 = player.GetItemCount(player.INVENTORY, self.questionDialogItemPos)
		
		mouseModule.mouseController.AttachObject(self, attachSlotType, self.questionDialogItemPos, selectedItemVNum, count)
		
		self.InsertItemToSlot(self.questionDialogEmptyPos)
		
		# Clear question dialog data for further use
		self.__ClearItemMoveQuestionDialog()
		
	def __ItemMoveQuestionDialogCancel(self):
		self.__ClearItemMoveQuestionDialog()
		
	def __ClearItemMoveQuestionDialog(self):
		if self.questionDialog:
			self.questionDialog.Close()
			
		# Clear the locked item (it will stay locked if it was put into the feed window)
		inven_slot_pos = self.questionDialogItemPos
		if inven_slot_pos != -1:
			if inven_slot_pos >= player.INVENTORY_PAGE_SIZE:
				inven_page = self.wndPetInformation.inven.GetInventoryPageIndex()
				inven_slot_pos -= (inven_page * player.INVENTORY_PAGE_SIZE)
				
			self.wndPetInformation.inven.wndItem.SetCanMouseEventSlot(inven_slot_pos)
			
		self.questionDialogEmptyPos = -1
		self.questionDialogItemPos = -1
		
	def SelectEmptySlot(self, slotIndex):
		attachedSlotType	= mouseModule.mouseController.GetAttachedType()			
		attachedSlotPos		= mouseModule.mouseController.GetAttachedSlotNumber()
		
		#if player.SLOT_TYPE_INVENTORY != attachedSlotType:
		#	return False
		
		if player.SLOT_TYPE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_STONE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SWITCH_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_COSTUME_INVENTORY == attachedSlotType:
		
			self.ItemMoveFeedWindow(player.INVENTORY, attachedSlotType, attachedSlotPos)
		
	def InsertItemToSlot(self, slotIndex):
		checkTime = app.GetGlobalTimeStamp() - self.feedButtonClickTime
		if checkTime < 2:
			if slotIndex in self.backupFeedItems:
				return False
		else:
			self.backupFeedItems = []
				
		if not mouseModule.mouseController.isAttached():
			return False
		
		attachedSlotType	= mouseModule.mouseController.GetAttachedType()			
		attachedSlotPos		= mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemCount	= mouseModule.mouseController.GetAttachedItemCount()
		attachedItemVNum	= player.GetItemIndex(attachedSlotPos)
		item.SelectItem(attachedItemVNum)		
		
		itemType	= item.GetItemType()
		itemSubType = item.GetItemSubType()			
		
		# Return if item is beging attached from not inventory window
		if player.SLOT_TYPE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SKILL_BOOK_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_GIFT_BOX_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SWITCH_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_COSTUME_INVENTORY != attachedSlotType:
			return False

		# Match the shared crystal basket: normal inventory and live categories 0-4.
		from uimountfeed import IsInventorySource
		if not IsInventorySource(attachedSlotType, attachedSlotPos):
			return False
		
		# Return if there is no pet summoned
		petVNum = player.GetActivePetItemVNum()
		if 0 == petVNum:
			return False

		# Return if active pet is being dragged to the window
		if item.ITEM_TYPE_PET == itemType and itemSubType == item.PET_UPBRINGING:
			activePetId = player.GetActivePetItemId()
			petId = player.GetItemMetinSocket(attachedSlotPos, 2)
			if petId == activePetId:
				return False
		
		# Display a msg if item type does not correspond to condtions
		if self.wndPetInformation.CantFeedItem(attachedSlotPos):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_FEED_TYPE)
			return False
		
		if -1 != self.FeedItems[slotIndex]:
			return False
		
		if attachedSlotPos not in self.FeedItems:
			mouseModule.mouseController.DeattachObject()
			
			invenItemCount = player.GetItemCount(attachedSlotPos)
			if attachedItemCount != invenItemCount:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_FEED_SPLIT_ITEM)
				return False
			
			self.FeedItems[slotIndex] = attachedSlotPos			
			self.FeedItemsCount[slotIndex] = attachedItemCount
			self.feedDraft[slotIndex] = (attachedItemVNum, attachedItemCount)
			self.InsertDataDummySlot(slotIndex, attachedItemVNum)
			self.FeedItemSlot.SetItemSlot(slotIndex, attachedItemVNum, attachedItemCount)
			self.FeedItemSlot.RefreshSlot()
			
		return True
		
		
	def InsertDataDummySlot(self, slotIndex, vnum):
	
		self.FeedItemDummy[slotIndex] = 1
	
		item.SelectItem(vnum)
		itemSize = item.GetItemSize(vnum)
		
		if 1 == itemSize[1]:
			return
		
		addSlotIndex = slotIndex
		
		for value in range(itemSize[1] - 1):
			addSlotIndex = addSlotIndex + FEED_WINDOW_X_SIZE
		
			if addSlotIndex >= player.PET_FEED_SLOT_MAX:
				return
				
			self.FeedItemDummy[addSlotIndex] = 1
			
		
	def DeleteDataDummySlot(self, slotIndex, InvenPos):
	
		vnum = player.GetItemIndex(InvenPos)
		item.SelectItem(vnum)
		itemSize = item.GetItemSize(vnum)
		
		self.FeedItemDummy[slotIndex] = 0
		
		if 1 == itemSize[1]:
			return
			
		delSlotIndex = slotIndex
		
		for value in range(itemSize[1] - 1):
			delSlotIndex = delSlotIndex + FEED_WINDOW_X_SIZE
		
			if delSlotIndex >= player.PET_FEED_SLOT_MAX:
				return
				
			self.FeedItemDummy[delSlotIndex] = 0
		
		
	# Send feed packet if there are items inside the window
	def ClickPetFeedButton(self):
		# Basket entries are references, not copies; reject a changed source stack.
		for slot, cell in enumerate(self.FeedItems):
			if cell == -1:
				continue
			if self.feedDraft.get(slot) != (player.GetItemIndex(cell), player.GetItemCount(cell)):
				self.ClearFeedItems()
				return
		resultFeedItems = [value for value in self.FeedItems if value != -1]
		resultFeedItemCounts = [value for value in self.FeedItemsCount if value != 0]

		if resultFeedItems:
			if net.SendPetFeedPacket(self.wndPetInformation.feedIndex, resultFeedItems, resultFeedItemCounts):
				self.feedButtonClickTime = app.GetGlobalTimeStamp()

	def ClearMouseEventFeedItems(self):
		self.feedDraft.clear()
		# Unlock items that are inside the feed window
		for inven_slot_pos in self.FeedItems:
			if inven_slot_pos != -1:
				if inven_slot_pos >= player.INVENTORY_PAGE_SIZE:
					inven_page = self.wndPetInformation.inven.GetInventoryPageIndex()
					inven_slot_pos -= (inven_page * player.INVENTORY_PAGE_SIZE)
					
				self.wndPetInformation.inven.wndItem.SetCanMouseEventSlot(inven_slot_pos)
	
		del self.FeedItems[:]
		del self.FeedItemsCount[:]
		del self.FeedItemDummy[:]
		
		for value in range(0, player.PET_FEED_SLOT_MAX):			
			self.FeedItems.append(-1)
			self.FeedItemsCount.append(0)
			self.FeedItemDummy.append(0)
	
	def BackUpSucceedFeedItems(self):
		self.backupFeedItems = self.FeedItems[:]
		
	def OnUpdate(self):
		if self.wndPetInformation.inven == 0:
			return
		
		inven = self.wndPetInformation.inven
		invenPage = inven.GetInventoryPageIndex()
		
		min_range = invenPage * player.INVENTORY_PAGE_SIZE
		max_range = (invenPage + 1) * player.INVENTORY_PAGE_SIZE
		
		# Lock items that are inside the feed window
		for inven_slot_pos in self.FeedItems:
			if inven_slot_pos == -1:
				continue
				
			if min_range <= inven_slot_pos < max_range:
				inven_slot_pos = inven_slot_pos - min_range
				inven.wndItem.SetCantMouseEventSlot(inven_slot_pos)
				
		if self.questionDialogItemPos != -1:
			inven_slot_pos = self.questionDialogItemPos
			if min_range <= inven_slot_pos < max_range:
				inven_slot_pos = inven_slot_pos - min_range
				inven.wndItem.SetCantMouseEventSlot(inven_slot_pos)
				
		return
	
	def OnTop(self):
		if not self.wndPetInformation:
			return
			
		if not self.wndPetInformation.interface:
			return
			
		interface = self.wndPetInformation.interface
		interface.SetOnTopWindow(player.ON_TOP_WND_PET_FEED)
		interface.RefreshMarkInventoryBag()

	
"""
		PetInformationWindow is opened through taskbar or 'P' key.
		Shows pet statistics and windows for attr change/pet revive.
"""
class PetInformationWindow(ui.ScriptWindow):
	wndPetFeed		= None
	tooltipItem		= None
	inven			= None
	wndPetHatching	= None
	wndPetNameChange= None
	feedIndex		= player.FEED_BUTTON_MAX
	skillSlot		= []
	feedButton		= []
	
	SkillBookSlotIndex	= -1
	SkillBookInvenIndex = -1
	
	SkillBookDelSlotIndex	= -1
	SkillBookDelInvenIndex	= -1
	
	typeInfo = {
		1	:	localeInfo.PET_ATTR_DETERMINE_TYPE1,
		2	:	localeInfo.PET_ATTR_DETERMINE_TYPE2,
		3	:	localeInfo.PET_ATTR_DETERMINE_TYPE3,
		4	:	localeInfo.PET_ATTR_DETERMINE_TYPE4,
		5	:	localeInfo.PET_ATTR_DETERMINE_TYPE5,
		6	:	localeInfo.PET_ATTR_DETERMINE_TYPE6,
		7	:	localeInfo.PET_ATTR_DETERMINE_TYPE7,
		8	:	localeInfo.PET_ATTR_DETERMINE_TYPE8,
	}
	
	class DescriptionBox(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.descIndex = 0
		def __del__(self):
			ui.Window.__del__(self)
		def SetIndex(self, index):
			self.descIndex = index
		def OnRender(self):
			event.RenderEventSet(self.descIndex)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.interface = None
		self.isLoaded = 0
		self.state = player.PET_WINDOW_INFO
		self.pageDict		= None
		self.activeView		= "pet"
		self.compact = None
		self.skillSlot = []
		self.heartPage		= None
		self.petSwitch		= None
		self.heartSwitch	= None
		self.windowTitle	= None
		self.petInfoBackground = None
		self.feedButton = [None for unused in range(player.FEED_BUTTON_MAX)]
		self.AffectShower	= None
		self.popupDialog	= None
		self.questionDialog	= None
		self.tooptipPetSkill	= None
		self.attrChangeIndex	= [-1, -1, -1]
		self.petReviveIndex		= -1
		self.inspectedPetSlot	= -1
		self.inspectedPetID		= 0
		self.inspectedPetVnum	= 0
		self.displayedPetID		= 0
		self.displayedPetSlot	= -1
		self.petReviveItems	= [-1 for i in range(player.PET_REVIVE_MATERIAL_SLOT_MAX)]
		self.petReviveItemsCount	= [0 for i in range(player.PET_REVIVE_MATERIAL_SLOT_MAX)]
		self.isPetReviveResultTooltip = False
		self.descIndex = 0
		self.desc_Y = DEFAULT_DESC_Y
		self.SetWindowName("PetInformationWindow")
		self.__LoadWindow()
		self.wndPetHatching		= PetHatchingWindow(self)
		self.wndPetNameChange	= PetNameChangeWindow(self)
		self.wndPetFeed			= PetFeedWindow(self)
		self.compact = uipetcompact.PetCompactPresentation(self)
		
	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
	def Show(self):		
		self.__LoadWindow()
		ui.ScriptWindow.Show(self)
		self.SetTop()
		if self.activeView == "heart" and self.heartPage:
			self.heartPage.Refresh()
			
	def Hide(self):
		if getattr(self, "compact", None):
			self.compact.Hide()
		if self.wndPetFeed:
			self.wndPetFeed.Close()
	
		wndMgr.Hide(self.hWnd)
		
	def BindInterfaceClass(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)
		
	def __LoadWindow(self):
		if self.isLoaded == 1:
			return
		self.isLoaded = 1
		
		try:
			self.__LoadScript("UIScript/petInformationWindow.py")
				
		except:
			import exception
			exception.Abort("petInformationWindow.LoadWindow.__LoadScript")
		
		
		
		
		try:
			self.AddFlag("ignore_size")
			self.AddFlag("not_pick")
			titleBar = self.GetChild("TitleBar")
			titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			titleBar.SetTop()
			self.petInfoBackground = self.GetChild("PetInfoUIBG")
			
			self.pageDict = {
				player.PET_WINDOW_INFO					: self.GetChild("PetInfo_Page"),
				player.PET_WINDOW_ATTR_CHANGE			: self.GetChild("PetAttrChange_Page"),
				player.PET_WINDOW_PRIMIUM_FEEDSTUFF		: self.GetChild("PetPremiumFeefstuff_Page"),
			}
			
			# UpBringing Pet Slot
			wndUpBringingPetSlot = self.GetChild("UpBringing_Pet_Slot")
			wndUpBringingPetSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			
			if localeInfo.IsARABIC():
				wndUpBringingPetSlot.SetPosition(295,55)
				
			self.wndUpBringingPetSlot	= wndUpBringingPetSlot
			
			self.feedMainButton = self.GetChild("FeedMainButton")
			self.evolutionMainButton = self.GetChild("EvolutionMainButton")
			self.feedMainButton.SetText(
				_LocalePetHeart("PET_FEED_MAIN_ACTION", u"Nakrmít"))
			self.evolutionMainButton.SetText(
				_LocalePetHeart("PET_EVOLUTION_MAIN_ACTION", u"Evoluce"))
			self.feedMainButton.SetEvent(ui.__mem_func__(self.OpenFeedMenu))
			self.evolutionMainButton.SetEvent(ui.__mem_func__(self.OpenEvolutionFeed))
			self.feedButton[player.FEED_LIFE_TIME_EVENT] = self.feedMainButton
			self.feedButton[player.FEED_EVOL_EVENT] = self.evolutionMainButton
			self.feedButton[player.FEED_EXP_EVENT] = self.feedMainButton
			self.feedMainButton.DisableFlash()
			self.evolutionMainButton.DisableFlash()
				
			# Life Time Gauge
			self.lifeTimeGauge = self.GetChild("LifeGauge")
			self.lifeTimeGauge.SetWindowHorizontalAlignLeft()
			
			if localeInfo.IsARABIC():
				self.lifeTimeGauge.SetPosition(26,0)
						
			# EXP Gauges
			expGauge = []
			self.expGaugeBoard = self.GetChild("UpBringing_Pet_EXP_Gauge_Board")
			expGauge.append(self.GetChild("UpBringing_Pet_EXPGauge_01"))
			expGauge.append(self.GetChild("UpBringing_Pet_EXPGauge_02"))
			expGauge.append(self.GetChild("UpBringing_Pet_EXPGauge_03"))
			expGauge.append(self.GetChild("UpBringing_Pet_EXPGauge_04"))
			expGauge.append(self.GetChild("UpBringing_Pet_EXPGauge_05"))
			
			for exp in expGauge:
				exp.SetSize(0, 0)
			
			self.expGauge	= expGauge
			self.tooltipEXP = ui.TextLine()
			self.tooltipEXP.SetParent(self)
			self.tooltipEXP.SetPosition(100, 50)
			self.tooltipEXP.Hide()
			
			# Skill slot
			arabic_start_pos_x = 36
			
			for value in range(SKILL_SLOT_MAX):
				self.skillSlot.append(self.GetChild("PetSkillSlot"+str(value)))
				self.skillSlot[value].SetCoverButton(0, SKILL_SLOT_ENABLE, SKILL_SLOT_ENABLE, SKILL_SLOT_ENABLE, SKILL_SLOT_ENABLE, False, False)
				self.skillSlot[value].SetAlwaysRenderCoverButton(0)
				if localeInfo.IsARABIC():
					# 36, 100, 164
					self.skillSlot[value].SetPosition(arabic_start_pos_x, 365)
					arabic_start_pos_x = arabic_start_pos_x + 32

				self.skillSlot[value].SetSelectEmptySlotEvent(
					functools.partial(self.SelectEmptySkillSlot, value))
				self.skillSlot[value].SetSelectItemSlotEvent(
					functools.partial(self.SetSelectItemSlotEvent, value))
				self.skillSlot[value].SetOverInItemEvent(
					functools.partial(self.OverInPetSkillSlot, value))
				self.skillSlot[value].SetOverOutItemEvent(
					ui.__mem_func__(self.OverOutPetSkillSlot))
			
			# Initialize skill delete question dialog
			self.questionSkillDelDlg = uiCommon.QuestionDialog2()
			self.questionSkillDelDlg.SetAcceptEvent(ui.__mem_func__(self.__SkillDeleteQuestionDialogAccept))
			self.questionSkillDelDlg.SetCancelEvent(ui.__mem_func__(self.__SkillDeleteQuestionDialogCancel))
			self.questionSkillDelDlg.Close()
			
			# Initialize skill learn question dialog
			self.questionDialog1 = uiCommon.QuestionDialog()
			self.questionDialog1.SetAcceptEvent(ui.__mem_func__(self.__SkillLearnQuestionDialogAccept))
			self.questionDialog1.SetCancelEvent(ui.__mem_func__(self.__SkillLearnQuestionDialogCancel))
			self.questionDialog1.Close()
			
				
			# Determine Button
			self.GetChild("DetermineButton").SetEvent(ui.__mem_func__(self.ClickDetermineButton))
			# Shop Button

			# Attr Change Slot
			attrChangeSlot = self.GetChild("Change_Pet_Slot")
			attrChangeSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptyAttrChangeSlot))
			attrChangeSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectAttrChangeItemSlot))
			attrChangeSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInAttrChangeItem))
			attrChangeSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutAttrChangeItem))
			self.attrChangeSlot = attrChangeSlot
		
			# Attr Change Button
			self.attrChangeButton = self.GetChild("Pet_Change_Button")
			self.attrChangeButton.SetEvent(ui.__mem_func__(self.ClickAttrChangeButton))
			self.attrChangeButton.Hide()
			
			# Attr Change Close Button
			self.attrCloseButton = self.GetChild("Pet_OK_Button")		
			self.attrCloseButton.SetEvent(ui.__mem_func__(self.ClickAttrClearButton))
			
			# Attr Change Type Text
			self.attrChangeText = self.GetChild("PetDetermineInfoText")

			# Revive description window
			self.reviveDescWindow = self.GetChild("desc_window")
			
			# Revive description box
			self.descriptionBox = self.DescriptionBox()
			self.descriptionBox.Show()
			self.descriptionBox.SetParent(self.reviveDescWindow)

			# Revive description prev/next buttons
			self.petReviveDescPrevButton = self.GetChild("PetReviveDescPrevButton")
			self.petReviveDescNextButton = self.GetChild("PetReviveDescNextButton")
			self.petReviveDescPrevButton.SetEvent(ui.__mem_func__(self.PetPremiumFeedStuffPrevDescriptionPage))
			self.petReviveDescNextButton.SetEvent(ui.__mem_func__(self.PetPremiumFeedStuffNextDescriptionPage))
			
			# Revive UpBringing Pet Slot
			petReviveSlot = self.GetChild("PetReviveSlot")
			petReviveSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectPetReviveEmptySlot))
			petReviveSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectPetReviveItemSlot))
			petReviveSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInPetReviveSlot))
			petReviveSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutPetReviveSlot))
			self.petReviveSlot = petReviveSlot
			
			# Revived UpBringing Pet Slot
			petReviveResultSlot = self.GetChild("PetReviveResultSlot")
			petReviveResultSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInPetReviveResultSlot))
			petReviveResultSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutPetReviveResultSlot))
			self.petReviveResultSlot = petReviveResultSlot
			
			# Revive Material Slot Grid
			petReviveMaterialSlot = self.GetChild("PetReviveMaterialSlot")
			petReviveMaterialSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectPetReviveMaterialEmptySlot))
			petReviveMaterialSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectPetReviveMaterialItemSlot))
			self.petReviveMaterialSlot = petReviveMaterialSlot
			
			# Revive Age/Material Count Texts 
			self.petReviveAgeText = self.GetChild("PetReviveAgeNumberText")
			self.petReviveResultAgeText = self.GetChild("PetReviveResultAgeNumerText")
			self.petReviveItemsCountText = self.GetChild("PetReviveMaterialCountText")
			
			# Revive Button
			self.petReviveButton = self.GetChild("PetReviveButton")
			self.petReviveButton.SetEvent(ui.__mem_func__(self.ClickPetReviveButton))
			
			# Revive Cancel Button
			self.petReviveCancelButton = self.GetChild("PetReviveCancelButton")
			self.petReviveCancelButton.SetEvent(ui.__mem_func__(self.ClickPetReviveCancelButton))
			self.petReviveCancelButton.SetText(_LocalePetHeart("PET_HEART_BACK", u"Zpět"))

			# Heart is retired. The compact page owns one ordinary album action.
			self.windowTitle = self.GetChild("TitleName")
			
			# Initialize question dialog
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.Close()
			
			# Initialize info page and revive description
			self.SetState(player.PET_WINDOW_INFO)
			self.__DescPetPremiumFeedstuff()
		except:
			import exception
			exception.Abort("petInformationWindow.LoadWindow.BindObject")
			
	def OnPressEscapeKey(self):
		self.Close()
		return True
		
	def __LoadScript(self, fileName):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, fileName)
		
	def Destroy(self):
		if self.compact:
			self.compact.Destroy()
			self.compact = None
		self.isLoaded = 0
		
		if self.wndPetFeed:
			self.wndPetFeed.Destroy()
			self.wndPetFeed = None
		
		self.interface		= None	
		self.inven			= None
		self.tooltipItem	= None
		
		self.ClearDictionary()
		self.wndUpBringingPetSlot = None	
		
		self.lifeTimeGauge	= None
		self.expGauge		= None
		self.expGaugeBoard	= None
		self.tooltipEXP		= None
			
		if self.wndPetHatching:
			self.wndPetHatching.Destroy()
			self.wndPetHatching = None
			
		if self.wndPetNameChange:
			self.wndPetNameChange.Destroy()
			self.wndPetNameChange = None
			
		if self.skillSlot:
			del self.skillSlot[:]
			
		self.feedButton = [None for unused in range(player.FEED_BUTTON_MAX)]
			
		self.feedIndex				= player.FEED_BUTTON_MAX		
		self.SkillBookSlotIndex  = -1
		self.SkillBookInvenIndex = -1
		
		SkillBookDelSlotIndex	= -1
		SkillBookDelInvenIndex	= -1

		self.attrChangeIndex	 = None
		self.petReviveIndex		 = -1
		self.petReviveItems	= None
		self.petReviveItemsCount = None
		self.isPetReviveResultTooltip	= False

		if self.heartPage:
			self.heartPage.Destroy()
		self.heartPage = None
		self.petSwitch = None
		self.heartSwitch = None
		self.petInfoBackground = None
		self.feedMainButton = None
		self.evolutionMainButton = None
		
		self.AffectShower		= None
		self.tooptipPetSkill	= None
		
		if self.questionDialog1:
			self.questionDialog1.Destroy()
		
			
		if self.questionSkillDelDlg:
			self.questionSkillDelDlg.Destroy()
			
		if self.popupDialog:
			self.popupDialog.Destroy()
			
		if self.questionDialog:
			self.questionDialog.Destroy()
			
		self.questionDialog1		= None
		self.questionSkillDelDlg	= None
		self.popupDialog			= None
		self.questionDialog		= None
		
		self.pageDict		= None
		
		self.descIndex = 0
		self.desc_Y = DEFAULT_DESC_Y
		
	def Close(self):
		if self.tooltipEXP:
			self.tooltipEXP.Hide()
	
		if self.wndPetFeed:
			self.wndPetFeed.Close()
				
		self.PetFeedToggleButtonUpAll()
			
		self.__ClearPetSkillSlot()
		
		self.__ClearSkillBookLearnEvent()
		self.__ClearSkillDeleteBookEvent()
		
		self.__ClearAttrChangeWindow()
		self.__ClearPetReviveWindow()
		
		if self.popupDialog:
			self.popupDialog.Close()
		
		if self.questionDialog:
			self.questionDialog.Close()
		self.inspectedPetSlot, self.inspectedPetID, self.inspectedPetVnum = -1, 0, 0
		self.Hide()
		self.activeView = "pet"
		self.__SetPetBodyVisible(True)
		if self.heartPage:
			self.heartPage.Hide()
		self.__SetSideNavigation("pet")
		
		net.SendPetWindowType(player.PET_WINDOW_INFO)
		
	def __SetSideNavigation(self, view):
		if self.petSwitch:
			self.petSwitch.SetSelected(view == "pet")
		if self.heartSwitch:
			self.heartSwitch.SetSelected(view == "heart")

	def __SetPetBodyVisible(self, visible):
		if not self.petInfoBackground:
			return
		if visible:
			self.petInfoBackground.Show()
		else:
			self.petInfoBackground.Hide()

	def __ShowPetView(self):
		self.activeView = "pet"
		self.__SetPetBodyVisible(True)
		self.__SetSideNavigation("pet")
		if self.heartPage:
			self.heartPage.Hide()
		if self.state == player.PET_WINDOW_INFO:
			self.SetState(player.PET_WINDOW_INFO)
		else:
			net.SendPetWindowType(player.PET_WINDOW_INFO)

	def __ShowHeartView(self):
		# Compatibility entry is intentionally inert, including old callbacks.
		return

	def OpenPetReviveFromFeed(self):
		if self.wndPetFeed:
			self.wndPetFeed.Close()
		if not self.__IsInspectedPetValid(True):
			return
		net.SendPetRevive(self.inspectedPetSlot, [], [])

	def OpenInspectedPet(self, slotIndex, petID):
		itemVnum = player.GetItemIndex(slotIndex)
		if not itemVnum or player.GetItemMetinSocket(player.INVENTORY, slotIndex, 2) != petID:
			return
		self.inspectedPetSlot = slotIndex
		self.inspectedPetID = petID
		self.inspectedPetVnum = itemVnum
		self.displayedPetID = petID
		self.displayedPetSlot = slotIndex
		self.Show()
		self.SetState(player.PET_WINDOW_INFO)
		net.SendPetWindowType(player.PET_WINDOW_INFO)
		self.RefreshStatus()

	def __IsInspectedPetValid(self, requireExpired=False):
		if self.inspectedPetSlot < 0 or not self.inspectedPetID:
			return False
		if player.GetItemIndex(self.inspectedPetSlot) != self.inspectedPetVnum:
			return False
		if player.GetItemMetinSocket(player.INVENTORY, self.inspectedPetSlot, 2) != self.inspectedPetID:
			return False
		endTime = player.GetItemMetinSocket(player.INVENTORY, self.inspectedPetSlot, 0)
		return not requireExpired or app.GetGlobalTimeStamp() >= endTime

	def __FindPetSlot(self, petID):
		if self.displayedPetID == petID and self.displayedPetSlot >= 0:
			if player.GetItemMetinSocket(player.INVENTORY, self.displayedPetSlot, 2) == petID:
				return self.displayedPetSlot
		for slotIndex in range(player.INVENTORY_SLOT_COUNT):
			if player.GetItemMetinSocket(player.INVENTORY, slotIndex, 2) == petID:
				self.displayedPetID, self.displayedPetSlot = petID, slotIndex
				return slotIndex
		return -1

	def PetHeartUpdate(self):
		# Preserve the receive callback while retiring the gameplay surface.
		return

	def PetWindowTypeResult(self, result):
		if result in (player.PET_WINDOW_INFO, player.PET_WINDOW_ATTR_CHANGE,
				player.PET_WINDOW_PRIMIUM_FEEDSTUFF):
			self.SetState(player.PET_WINDOW_INFO)
		
	def SetState(self, stateKey):
		# The legacy attribute-reroll page is deliberately retired.
		if stateKey in (player.PET_WINDOW_ATTR_CHANGE, player.PET_WINDOW_PRIMIUM_FEEDSTUFF):
			stateKey = player.PET_WINDOW_INFO
		self.state = stateKey
		if self.compact:
			self.compact.SetState(stateKey)

		for pageValue in self.pageDict.values():
			pageValue.Hide()
		if self.heartPage:
			self.heartPage.Hide()

		self.activeView = "pet"
		self.__SetPetBodyVisible(True)
		self.pageDict[stateKey].Show()
		if self.windowTitle:
			if stateKey == player.PET_WINDOW_PRIMIUM_FEEDSTUFF:
				self.windowTitle.SetText(_LocalePetHeart("PET_HEART_REVIVE_TITLE", u"Oživení peta"))
			else:
				self.windowTitle.SetText(uiScriptLocale.PET_INFORMATION_TITLE)
		
		if self.interface and self.IsShow():
			if stateKey == player.PET_WINDOW_INFO:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()
				
			elif stateKey == player.PET_WINDOW_ATTR_CHANGE:
				if self.wndPetFeed.IsShow():
					self.wndPetFeed.Close()
					
				self.interface.SetOnTopWindow(player.ON_TOP_WND_PET_ATTR_CHANGE)
				self.interface.RefreshMarkInventoryBag()
				
			elif stateKey == player.PET_WINDOW_PRIMIUM_FEEDSTUFF:
				if self.wndPetFeed.IsShow():
					self.wndPetFeed.Close()
					
				self.interface.SetOnTopWindow(player.ON_TOP_WND_PET_PRIMIUM_FEEDSTUFF)
				self.interface.RefreshMarkInventoryBag()
		
			# Clear attr change/revive windows
			self.__ClearAttrChangeWindow()
			self.__ClearPetReviveWindow()
		
	def OnTop(self):
		if not self.interface:
			return
		if self.state == player.PET_WINDOW_INFO:
			self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
			self.interface.RefreshMarkInventoryBag()
			
		elif self.state == player.PET_WINDOW_ATTR_CHANGE:
			self.interface.SetOnTopWindow(player.ON_TOP_WND_PET_ATTR_CHANGE)
			self.interface.RefreshMarkInventoryBag()
			
		elif self.state == player.PET_WINDOW_PRIMIUM_FEEDSTUFF:
			self.interface.SetOnTopWindow(player.ON_TOP_WND_PET_PRIMIUM_FEEDSTUFF)
			self.interface.RefreshMarkInventoryBag()
			
	def GetState(self):
		return self.state
		
	def __ClearPetSkillSlot(self):
		for value in range(SKILL_SLOT_MAX):
			self.skillSlot[value].ClearSlot(0)
			self.skillSlot[value].SetCoverButton(0, SKILL_SLOT_ENABLE, SKILL_SLOT_ENABLE, SKILL_SLOT_ENABLE, SKILL_SLOT_ENABLE, False, False)
			self.skillSlot[value].SetAlwaysRenderCoverButton(0)
			self.skillSlot[value].HideAllSlotButton()

	def __GetPetSkillState(self, pet_id, slot):
		(skillLocked, skillVnum, skillLevel, cooltime) = player.GetPetSkillSlotState(pet_id, slot)
		skillDetails = player.GetPetSkillByIndex(pet_id, slot)
		return (skillLocked, skillVnum, skillLevel, cooltime, skillDetails)

	def __MakePopupDialog(self):
		self.popupDialog = uiCommon.PopupDialog()
		self.popupDialog.SetText("")
		
	def __OpenPopupDialog(self, str):
		if self.interface.IsShowDlgQuestionWindow():
			self.interface.CloseDlgQuestionWindow()
		
		if not self.popupDialog:
			self.__MakePopupDialog()
			
		self.popupDialog.SetText(str)
		self.popupDialog.SetWidth(max(280, self.popupDialog.GetTextSize()[0] + 40))
		self.popupDialog.SetTop()
		self.popupDialog.Open()
		
		
	# Delete skill dialog
	def SetSelectItemSlotEvent(self, skillSlotIndex, slotIndex=0):
		# Return if there is no pet summoned	
		pet_id = player.GetActivePetItemId()
		if 0 == pet_id:
			return
			
		if not mouseModule.mouseController.isAttached():
			return
			
		# Return if skill slot index is not between 0~2
		if skillSlotIndex < 0 or skillSlotIndex >= SKILL_SLOT_MAX:
			return
		
		(skillLocked, skillVnum, skillLevel, cooltime, skillDetails) = self.__GetPetSkillState(pet_id, skillSlotIndex)
		if skillLocked:
			return
		if not skillVnum:
			return

		attachedSlotType	= mouseModule.mouseController.GetAttachedType()			
		attachedSlotPos		= mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemCount	= mouseModule.mouseController.GetAttachedItemCount()
		attachedItemVNum	= player.GetItemIndex(attachedSlotPos)
		item.SelectItem(attachedItemVNum)		
		
		itemType	= item.GetItemType()
		itemSubType = item.GetItemSubType()			
		
		# Return if item is not from inventory
		if player.SLOT_TYPE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SKILL_BOOK_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_GIFT_BOX_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SWITCH_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_COSTUME_INVENTORY != attachedSlotType:
			return
			
		# Return if item position is bigger than player.INVENTORY_SLOT_COUNT
		if attachedSlotPos >= player.INVENTORY_SLOT_COUNT: 
			return
		
		# Return if it is not a skill delete item
		if item.ITEM_TYPE_PET != itemType or item.PET_SKILL_DEL_BOOK != itemSubType:
			return			

		# Initialize skill delete question dialog if it hasn't been yet
		if not self.questionSkillDelDlg:
			self.questionSkillDelDlg = uiCommon.QuestionDialog2()
			self.questionSkillDelDlg.SetAcceptEvent(ui.__mem_func__(self.__SkillDeleteQuestionDialogAccept))
			self.questionSkillDelDlg.SetCancelEvent(ui.__mem_func__(self.__SkillDeleteQuestionDialogCancel))
			
			
		self.questionSkillDelDlg.SetText1(localeInfo.PET_SKILL_DELETE_QUESTION_DLG_MSG1)
		self.questionSkillDelDlg.SetText2(localeInfo.PET_SKILL_DELETE_QUESTION_DLG_MSG2)
		(w,h) = self.questionSkillDelDlg.GetTextSize1()
		self.questionSkillDelDlg.SetWidth(w+100)
		
		mouseModule.mouseController.DeattachObject()
		self.SkillBookDelSlotIndex  = skillSlotIndex
		self.SkillBookDelInvenIndex = attachedSlotPos
		self.questionSkillDelDlg.SetTop()
		self.questionSkillDelDlg.Open()
			
	def __SkillDeleteQuestionDialogAccept(self):
		pet_id = player.GetActivePetItemId()
		if pet_id:
			net.SendPetDeleteSkill(self.SkillBookDelSlotIndex, self.SkillBookDelInvenIndex)	
		
		self.__ClearSkillDeleteBookEvent()
		return
		
	def __SkillDeleteQuestionDialogCancel(self):
		self.__ClearSkillDeleteBookEvent()
		return
		
	def __ClearSkillDeleteBookEvent(self):
		# Lock skill delete item
		self.CanInvenSlot(self.SkillBookDelInvenIndex)
		
		self.SkillBookDelSlotIndex  = -1
		self.SkillBookDelInvenIndex = -1
		
		if self.questionSkillDelDlg:
			self.questionSkillDelDlg.Close()
		
	# Show pet tooltip
	def OverInPetSkillSlot(self, slot, index):
		pet_id = player.GetActivePetItemId()
		if 0 == pet_id:
			return
		
		(skillLocked, skillVnum, skillLevel, cooltime, skillDetails) = self.__GetPetSkillState(pet_id, slot)
		if skillLocked or not skillVnum:
			return

		if self.tooptipPetSkill:
			self.tooptipPetSkill.SetPetSkill(pet_id, slot, index)

	def OverOutPetSkillSlot(self):
		if self.tooptipPetSkill:
			self.tooptipPetSkill.HideToolTip()

	def RequestLearnSkillBook(self, itemCell):
		pet_id = player.GetActivePetItemId()
		if not pet_id:
			self.__OpenPopupDialog(localeInfo.PET_SKILL_BOOK_NEEDS_PET)
			return

		item.SelectItem(player.GetItemIndex(itemCell))
		if item.GetItemType() != item.ITEM_TYPE_PET or item.GetItemSubType() != item.PET_SKILL:
			return
		bookSkill = item.GetValue(0)
		if not bookSkill:
			return

		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		if evol_level < player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL:
			self.__OpenPopupDialog(localeInfo.PET_SKILL_LEARN_FAIL_CONDITIONS)
			return

		emptySlot = -1
		for slot in range(SKILL_SLOT_MAX):
			(skillLocked, skillVnum, skillLevel, cooltime, skillDetails) = self.__GetPetSkillState(pet_id, slot)
			if skillLocked:
				continue
			if skillVnum == bookSkill:
				if skillLevel >= player.PET_GROWTH_SKILL_LEVEL_MAX:
					self.__OpenPopupDialog(localeInfo.PET_SKILL_BOOK_MAX_LEVEL)
					return
				net.SendPetLearnSkill(slot, itemCell)
				return
			if not skillVnum and emptySlot < 0:
				emptySlot = slot

		if emptySlot < 0:
			self.__OpenPopupDialog(localeInfo.PET_SKILL_BOOK_NO_SLOT)
			return
		net.SendPetLearnSkill(emptySlot, itemCell)

	# Triggered from SelectEmptySkillSlotX, opens learn skill dialog
	def SelectEmptySkillSlot(self, skillSlotIndex, slotIndex=0):
		# Return if there is no summoned pet		
		pet_id = player.GetActivePetItemId()
		if 0 == pet_id:
			return
			
		if not mouseModule.mouseController.isAttached():
			return
			
		if skillSlotIndex < 0 or skillSlotIndex >= SKILL_SLOT_MAX:
			return
		
		# Pet data
		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		
		(skillLocked, skillVnum, skillLevel, cooltime, skillDetails) = self.__GetPetSkillState(pet_id, skillSlotIndex)
		if skillLocked:
			return
		if skillVnum:
			return
		attachedSlotType	= mouseModule.mouseController.GetAttachedType()			
		attachedSlotPos		= mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemCount	= mouseModule.mouseController.GetAttachedItemCount()
		attachedItemVNum	= player.GetItemIndex(attachedSlotPos)
		item.SelectItem(attachedItemVNum)		
		
		itemType	= item.GetItemType()
		itemSubType = item.GetItemSubType()			
		
		# Return if item is not from inventory
		if player.SLOT_TYPE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SKILL_BOOK_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_GIFT_BOX_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SWITCH_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_COSTUME_INVENTORY != attachedSlotType:
			return
			
		# Skill books use global cells beyond the normal inventory range.
		if attachedSlotType == player.SLOT_TYPE_SKILL_BOOK_INVENTORY:
			bookSlotStart = item.SKILL_BOOK_INVENTORY_SLOT_START
			if not bookSlotStart <= attachedSlotPos < bookSlotStart + player.SPECIAL_ITEM_SLOT_COUNT:
				return
		elif attachedSlotPos >= player.INVENTORY_SLOT_COUNT:
			return
		
		# Check if item is item.ITEM_TYPE_PET
		if item.ITEM_TYPE_PET != itemType:
			return
		
		# Return if skill delete item is dragged to an empty slot
		if item.PET_SKILL_DEL_BOOK == itemSubType:
			self.__OpenPopupDialog(localeInfo.PET_EMPTY_SKILL_SLOT_USE_ITEM)
			return
				
		# Return if it is not item.PET_SKILL subtype
		if item.PET_SKILL != itemSubType:
			return
			
		# Return if pet's evolution is not player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL
		if evol_level < player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL:
			return
		
		if not self.questionDialog1:
			self.questionDialog1 = uiCommon.QuestionDialog()
			self.questionDialog1.SetAcceptEvent(ui.__mem_func__(self.__SkillLearnQuestionDialogAccept))
			self.questionDialog1.SetCancelEvent(ui.__mem_func__(self.__SkillLearnQuestionDialogCancel))
			
			
		self.questionDialog1.SetText(localeInfo.PET_SKILL_LEARN_QUESTION_DLG_MSG % (item.GetItemName()))
		mouseModule.mouseController.DeattachObject()
		self.SkillBookSlotIndex  = skillSlotIndex
		self.SkillBookInvenIndex = attachedSlotPos
		self.questionDialog1.SetTop()
		self.questionDialog1.Open()
		
	def __SkillLearnQuestionDialogAccept(self):
		pet_id = player.GetActivePetItemId()
		if pet_id:
			net.SendPetLearnSkill(self.SkillBookSlotIndex, self.SkillBookInvenIndex)	
		
		self.__ClearSkillBookLearnEvent()
		return
		
	def __SkillLearnQuestionDialogCancel(self):
		self.__ClearSkillBookLearnEvent()
		return
		
	def __ClearSkillBookLearnEvent(self):
	
		self.CanInvenSlot(self.SkillBookInvenIndex)
		
		self.SkillBookSlotIndex  = -1
		self.SkillBookInvenIndex = -1
		
		if self.questionDialog1:
			self.questionDialog1.Close()
		
	def PetFeedToggleButtonUpAll(self, exclusion_index = player.FEED_BUTTON_MAX):
		return

	def OpenFeedMenu(self):
		self.ClickPetFeedButton(player.FEED_EXP_EVENT)

	def OpenEvolutionFeed(self):
		self.ClickPetFeedButton(player.FEED_EVOL_EVENT)

	def IsActivateEvolButton(self, pet_id):
		# Return if there is no summoned pet
		if 0 == pet_id:
			return False
			
		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		
		if evol_level == player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_OPEN_EVOL_BUTTON_LEVEL_MAX)
			return False
			
		evol_require = self.GetEvolInfo(evol_level)
		if 0 == evol_require:
			return False
		
		# Check level and experience limit for the first two evolutions
		if evol_level < player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL-1:
			# Level Check
			if pet_level < evol_require:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_OPEN_EVOL_BUTTON % evol_require)
				return False
			else:
				# EXP Check
				(curEXP, nextEXP, itemEXP, itemMaxEXP) = player.GetPetExpPoints(pet_id)
				
				if curEXP != nextEXP or itemEXP != itemMaxEXP:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_OPEN_EVOL_BUTTON_EXP_LACK)
					return False
					
		# The heroic evolution requires only the level. Althea has no pet
		# age gate; the server decides the remaining book requirement.
		elif evol_level == player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL - 1:
			if pet_level < evol_require:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_OPEN_EVOL_BUTTON % evol_require)
				return False
			
		return True
			
	def ClickPetFeedButton(self, index):
		pet_id = player.GetActivePetItemId()
		if 0 == pet_id:
			self.PetFeedToggleButtonUpAll()
			return			
			
		if player.FEED_EVOL_EVENT == index:
			if False == self.IsActivateEvolButton(pet_id):
				self.PetFeedToggleButtonUpAll(self.feedIndex)
				return
			
		if not self.wndPetFeed:
			self.wndPetFeed = PetFeedWindow(self)
		
		self.feedIndex = index
		self.wndPetFeed.ClearFeedItems()
		self.wndPetFeed.SetFeedMode(index)
		self.wndPetFeed.Show()
		self.wndPetFeed.SetTop()
		
		self.PetFeedToggleButtonUpAll(self.feedIndex)
	
		
	def OnUpdate(self):
		self.RefreshStatus()
		
		# Lock used items 
		self.CantInvenSlot(self.SkillBookInvenIndex)
		self.CantInvenSlot(self.SkillBookDelInvenIndex	)	
		self.CantInvenSlot(self.petReviveIndex	)	
		
		for i in range(player.PET_WND_SLOT_ATTR_CHANGE_MAX):
			self.CantInvenSlot(self.attrChangeIndex[i])
			
		for i in range(player.PET_REVIVE_MATERIAL_SLOT_MAX):
			self.CantInvenSlot(self.petReviveItems[i])
		
		if self.expGaugeBoard.IsIn():
			self.tooltipEXP.Show()
		else:
			self.tooltipEXP.Hide()
					
		(xposEventSet, yposEventSet) = self.reviveDescWindow.GetGlobalPosition()
		event.UpdateEventSet(self.descIndex, xposEventSet+7, -(yposEventSet+self.desc_Y))
		self.descriptionBox.SetIndex(self.descIndex)
		self.descriptionBox.SetTop()
			
				
	def RefreshStatus(self):
		if self.isLoaded==0:
			return

		activePetID = player.GetActivePetItemId()
		isActive = activePetID != 0
		if isActive:
			pet_id = activePetID
			petSlot = self.__FindPetSlot(pet_id)
			CurPetItemVNum = player.GetActivePetItemVNum()
			self.inspectedPetSlot, self.inspectedPetID, self.inspectedPetVnum = -1, 0, 0
		elif self.__IsInspectedPetValid():
			pet_id = self.inspectedPetID
			petSlot = self.inspectedPetSlot
			CurPetItemVNum = self.inspectedPetVnum
		else:
			self.ClearStatus()
			return
			
		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		curTime = app.GetGlobalTimeStamp()
		
		# UpBringing Pet Slot Image
		self.wndUpBringingPetSlot.SetItemSlot(0, CurPetItemVNum)
		
		# Pet Name
		self.GetChild("PetName").SetText(pet_nick);
		
		# Evolution Name
		self.GetChild("EvolName").SetText(self.__GetEvolName(evol_level))
		
		# Level
		self.GetChild("LevelValue").SetText(str(pet_level))
		
		# Age
		birthSec = max(0, curTime - birthday)
		self.GetChild("AgeValue").SetText(localeInfo.SecondToDay(birthSec))
		
		# Life Time Text
		(endTime, maxTime) = player.GetPetLifeTime(pet_id)			
		lifeTime = max(0, endTime - curTime)			
		lifeText = "0 min" if lifeTime <= 0 else localeInfo.SecondToH(lifeTime) + " " + uiScriptLocale.PET_INFORMATION_LIFE_TIME
		self.GetChild("LifeTextValue").SetText(lifeText)
		
		# Life Time Gauge
		self.SetLifeTime(lifeTime, maxTime)
		
		# HP, Def, SP Bonus Text
		self.GetChild("HpValue").SetText("+" + str("%0.1f" % pet_hp) + "%")
		self.GetChild("DefValue").SetText("+" + str("%0.1f" % pet_def) + "%")
		petType = player.GetItemMetinSocket(player.INVENTORY, petSlot, 3) if petSlot >= 0 else 1
		self.GetChild("SpTitle").SetText(growthpetpresentation.ThirdBonusLabel(petType))
		self.GetChild("SpValue").SetText("+" + str("%0.1f" % growthpetpresentation.ThirdAppliedPercent(pet_sp)) + "%")
		
		# EXP
		(curEXP, nextEXP, itemEXP, itemMaxEXP) = player.GetPetExpPoints(pet_id)

		curEXP		= unsigned32(curEXP)
		nextEXP		= unsigned32(nextEXP)
		itemEXP		= unsigned32(itemEXP)
		itemMaxEXP	= unsigned32(itemMaxEXP)
		self.SetExperience(curEXP, nextEXP, itemEXP, itemMaxEXP)
		
		# Clear skill slots
		self.__ClearPetSkillSlot()
			
		# Check for evolution conditions and enable flash effect
		# Enable feed button flash effect if pet is hungry
		# Enable item exp button flash effect if battle exp is full
		
		if isActive:
			self.PetEvolFlashEventCheck(pet_level, evol_level,
				curEXP, nextEXP, itemEXP, itemMaxEXP)
			self.PetFeedFlashEventCheck(lifeTime, curEXP, nextEXP,
				itemEXP, itemMaxEXP)
		
		# Skill data
		for slot in range(SKILL_SLOT_MAX):
			if not isActive:
				continue
			(skillLocked, skillVnum, skillLevel, cooltime, skillDetails) = self.__GetPetSkillState(pet_id, slot)
			self.skillSlot[slot].HideAllSlotButton()
			if skillLocked:
				continue

			self.skillSlot[slot].SetAlwaysRenderCoverButton(0, False)
			if not skillVnum:
				continue

			self.skillSlot[slot].SetPetSkillSlotNew(0, skillVnum)
			self.skillSlot[slot].SetSlotCount(0, skillLevel)
			self.skillSlot[slot].SetCoverButton(0)


			(skillName, skillDesc, skillUseType, skillCoolTime) = skill.GetPetSkillInfo(skillVnum)
			if skill.PET_SKILL_USE_TYPE_AUTO == skillUseType:
				if curTime <= cooltime:
					curCoolTime = skillCoolTime - (cooltime - curTime)
					self.skillSlot[slot].SetSlotCoolTime(0, skillCoolTime, curCoolTime)
					
		if self.compact:
			petType = player.GetItemMetinSocket(player.INVENTORY, petSlot, 3) if petSlot >= 0 else 1
			self.compact.Refresh(pet_id, evol_level, CurPetItemVNum, isActive,
				lifeTime <= 0, petType, (pet_hp, pet_def, pet_sp))
		
	def ClearStatus(self):
		self.inspectedPetSlot, self.inspectedPetID, self.inspectedPetVnum = -1, 0, 0
		self.displayedPetID, self.displayedPetSlot = 0, -1
		self.wndUpBringingPetSlot.SetItemSlot(0, 0)
		self.GetChild("PetName").SetText("")
		self.GetChild("EvolName").SetText("")
		self.GetChild("LevelValue").SetText("")
		self.GetChild("AgeValue").SetText("")
		self.GetChild("LifeTextValue").SetText("")
		self.GetChild("DefValue").SetText("")
		self.GetChild("SpValue").SetText("")
		self.GetChild("SpTitle").SetText(uiScriptLocale.PET_INFORMATION_SP)
		self.GetChild("HpValue").SetText("")
		self.SetExperience(0, 0, 0, 0)
		self.SetLifeTime(0, 1)
		self.__ClearPetSkillSlot()	#˝şĹł clear
		if self.compact:
			self.compact.Refresh(0, 0)
		
		if self.wndPetFeed:
			if self.wndPetFeed.IsShow():
				self.wndPetFeed.Close()
			
		self.__ClearSkillBookLearnEvent()
		self.__ClearSkillDeleteBookEvent()
			
		if self.AffectShower:
			self.AffectShower.ClearPetSkillAffect()
			
		self.AllOffPetInfoFlashEvent()	

	# Lock item at position invenIndex
	def CantInvenSlot(self, invenIndex):
		if invenIndex == -1:
			return
		
		inven = self.inven
		invenPage = inven.GetInventoryPageIndex()
		
		min_range = invenPage * player.INVENTORY_PAGE_SIZE
		max_range = (invenPage + 1) * player.INVENTORY_PAGE_SIZE
			
		inven_slot_pos = invenIndex
			
		if min_range <= inven_slot_pos < max_range:
			inven_slot_pos = inven_slot_pos - min_range
			inven.wndItem.SetCantMouseEventSlot(inven_slot_pos)
			
	# Unlock item at position invenIndex
	def CanInvenSlot(self, invenIndex):
		if invenIndex == -1:
			return
			
		inven = self.inven
		invenPage = inven.GetInventoryPageIndex()
		
		min_range = invenPage * player.INVENTORY_PAGE_SIZE
		max_range = (invenPage + 1) * player.INVENTORY_PAGE_SIZE
			
		inven_slot_pos = invenIndex
			
		if min_range <= inven_slot_pos < max_range:
			inven_slot_pos = inven_slot_pos - min_range
			inven.wndItem.SetCanMouseEventSlot(inven_slot_pos)		
	
	def __GetEvolName(self, evol_level):
		if 1 == evol_level:
			return localeInfo.PET_INFORMATION_STAGE1
		elif 2 == evol_level:
			return localeInfo.PET_INFORMATION_STAGE2
		elif 3 == evol_level:
			return localeInfo.PET_INFORMATION_STAGE3
		elif 4 == evol_level:
			return localeInfo.PET_INFORMATION_STAGE4
			
		return localeInfo.PET_INFORMATION_STAGE1
		
	def PetAffectShowerRefresh(self):
		if self.AffectShower:
			self.AffectShower.ClearPetSkillAffect()
	
	def PetEvolFlashEventCheck(self, pet_level, evol_level, curEXP, nextEXP, itemEXP, itemMaxEXP):
		# Return if pet has reached peak evolution
		if evol_level == player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL:
			self.DisableFlashButtonEvent(player.FEED_EVOL_EVENT)
			return False
			
		# Return if there is no level conditions for evolution
		evol_require = self.GetEvolInfo(evol_level)
		if 0 == evol_require:
			self.DisableFlashButtonEvent(player.FEED_EVOL_EVENT)
			return False
		
		# Check level and experience limit for the first two evolutions
		if evol_level < player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL-1:
			# Level Check
			if pet_level == evol_require:
				if curEXP == nextEXP and itemEXP == itemMaxEXP:
					self.EnableFlashButtonEvent(player.FEED_EVOL_EVENT)
					
					return True
					
		# The heroic evolution is ready at its level, regardless of pet age
		elif evol_level == player.PET_GROWTH_SKILL_OPEN_EVOL_LEVEL - 1:
			if pet_level >= evol_require:
				self.EnableFlashButtonEvent(player.FEED_EVOL_EVENT)
				return True
				
		self.DisableFlashButtonEvent(player.FEED_EVOL_EVENT)
		return False
				
	def PetFeedFlashEventCheck(self, lifeTime, curEXP, nextEXP, itemEXP, itemMaxEXP):
		needsLifeTime = lifeTime < player.LIFE_TIME_FLASH_MIN_TIME
		# No artificial 90% item-EXP barrier: combat and crystals both complete XP.
		if needsLifeTime:
			self.EnableFlashButtonEvent(player.FEED_EXP_EVENT)
			return True

		self.DisableFlashButtonEvent(player.FEED_EXP_EVENT)
		return False
		
	def AllOffPetInfoFlashEvent(self):
		for i in range(player.FEED_BUTTON_MAX):
			self.DisableFlashButtonEvent(i)
			
	def EnableFlashButtonEvent(self, index):
		if index < 0 or index >= player.FEED_BUTTON_MAX:
			return
		
		if self.feedButton[index]:
			self.feedButton[index].EnableFlash()
			
	def DisableFlashButtonEvent(self, index):
		if index < 0 or index >= player.FEED_BUTTON_MAX:
			return
		
		if self.feedButton[index]:
			self.feedButton[index].DisableFlash()
	
	def SetExperience(self, curPoint, maxPoint, itemExp, itemExpMax):
		if self.compact:
			self.compact.SetExperience(curPoint, maxPoint, itemExp, itemExpMax)
			return
		# Legacy packet fields are summed into one pool, never a separate item bar.
		total = max(0, maxPoint) + max(0, itemExpMax)
		value = min(max(0, curPoint), max(0, maxPoint)) + min(max(0, itemExp), max(0, itemExpMax))
		ratio = float(value) / total if total else 0.0
		for index, gauge in enumerate(self.expGauge):
			fill = max(0.0, min(1.0, ratio * 4 - index)) if index < 4 else 0.0
			if fill:
				gauge.SetRenderingRect(0.0, fill - 1.0, 0.0, 0.0)
				gauge.Show()
			else:
				gauge.Hide()
		self.tooltipEXP.SetText("%s: %d / %d" % (localeInfo.PET_INFO_EXP, value, total))

	def SetLifeTime(self, curPoint, maxPoint):
		curPoint = min(curPoint, maxPoint)
		if maxPoint > 0:
			self.lifeTimeGauge.SetPercentage(curPoint, maxPoint)
			
	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem
		
	def SetInven(self, inven):
		self.inven = inven
		
	def IsFeedWindowOpen(self):
		if self.wndPetFeed:
			if self.wndPetFeed.IsShow():
				return True
			
		return False
		
	def GetPetHatchingWindow(self):
		return self.wndPetHatching

	def GetPetNameChangeWindow(self):
		return self.wndPetNameChange
		
	def GetPetFeedWindow(self):
		return self.wndPetFeed
	
	def CantFeedItem(self, InvenSlot):
		if self.feedIndex == player.FEED_LIFE_TIME_EVENT:
			return self.__CantLifeTimeFeedItem(InvenSlot)
			
		elif self.feedIndex == player.FEED_EVOL_EVENT:
			return self.__CantEvolFeedItem(InvenSlot)
			
		elif self.feedIndex == player.FEED_EXP_EVENT:
			return self.__CantExpFeedItem(InvenSlot)
		
		return False
		
		
	def __CantLifeTimeFeedItem(self, InvenSlot):
		ItemVNum = player.GetItemIndex(InvenSlot)
		
		if ItemVNum == 0:
			return True

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_PETFEED):
			return True
			
		item.SelectItem(ItemVNum)
		if item.GetItemType() == item.ITEM_TYPE_PET:
			if item.GetItemSubType() in [item.PET_UPBRINGING, item.PET_EGG]:
				return False
		
		return True
		
	def __CantEvolFeedItem(self, InvenSlot):
		ItemVNum = player.GetItemIndex(InvenSlot)
	
		if ItemVNum == 0:
			return True
			
		item.SelectItem(ItemVNum)
		
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_PETFEED):
			return True
		
	def __CantExpFeedItem(self, InvenSlot):
		return player.GetItemIndex(InvenSlot) not in mountfeedmodel.REGULAR_FEED_VNUMS

	def CantAttrChangeItem(self, InvenSlot):
		ItemVNum = player.GetItemIndex(InvenSlot)
		
		if ItemVNum == 0:
			return True
			
		item.SelectItem(ItemVNum)
		
		if item.GetItemType() == item.ITEM_TYPE_PET:
			if item.GetItemSubType() in [item.PET_UPBRINGING, item.PET_ATTR_CHANGE]:
				return False
			
		return True
		
	def CantPremiumFeedItem(self, InvenSlot):
		ItemVNum = player.GetItemIndex(InvenSlot)
		
		if ItemVNum == 0:
			return True
			
		item.SelectItem(ItemVNum)
		
		if item.GetItemType() == item.ITEM_TYPE_PET:
			if item.GetItemSubType() in [item.PET_UPBRINGING, item.PET_PRIMIUM_FEEDSTUFF]:
				return False
			
		return True
	
	def PetInfoBindAffectShower(self, affect_shower):
		self.AffectShower = affect_shower
		
	def SetPetSkillToolTip(self, tooltipPetSkill):
		self.tooptipPetSkill = tooltipPetSkill
		
	def GetEvolInfo(self, evol_level):
		# Return if evolution level in invalid
		if evol_level < 1 or evol_level >= player.PET_GROWTH_EVOL_MAX:
			return 0

		if 1 == evol_level:
			return 40
		elif 2 == evol_level:
			return 80
		elif 3 == evol_level:
			return 81
			
		return 0
		
	def PetFeedReuslt(self, result):
		if not self.wndPetFeed:
			return
		
		if True == result:
			self.wndPetFeed.BackUpSucceedFeedItems()
			
			if self.feedIndex == player.FEED_EVOL_EVENT:
				self.wndPetFeed.Close()
			
		self.wndPetFeed.ClearFeedItems()
		
	def OverInAttrChangeItem(self, slotIndex):
		if None != self.tooltipItem:
			invenPos = self.attrChangeIndex[slotIndex]
			if invenPos != -1:
				self.tooltipItem.SetInventoryItem(invenPos, player.INVENTORY)
				
		return
		
	def OverOutAttrChangeItem(self):
		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()
		return
		
	def SelectAttrChangeItemSlot(self, slotIndex):
		self.__ClearAttrChangeWindow()
		
	def __ClearAttrChangeSlot(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			return

		#Unlock item in slotIndex slot
		self.CanInvenSlot(self.attrChangeIndex[slotIndex])
		self.attrChangeIndex[slotIndex] = -1
		self.attrChangeSlot.ClearSlot(slotIndex)
		self.attrChangeSlot.RefreshSlot()
		
		if self.attrChangeButton.IsShow():
			self.attrChangeButton.Hide()
		
	def SelectEmptyAttrChangeSlot(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return False
		
		attachedSlotType	= mouseModule.mouseController.GetAttachedType()			
		attachedSlotPos		= mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemVNum	= player.GetItemIndex(attachedSlotPos)
		item.SelectItem(attachedItemVNum)		
		
		itemType	= item.GetItemType()
		itemSubType = item.GetItemSubType()			

		# Return if item is beging attached from not inventory window
		if player.SLOT_TYPE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SKILL_BOOK_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_GIFT_BOX_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SWITCH_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_COSTUME_INVENTORY != attachedSlotType:
			return False
			
		# Return if item position is bigger than player.INVENTORY_SLOT_COUNT
		if attachedSlotPos >= player.INVENTORY_SLOT_COUNT: 
			return False

		if slotIndex == player.PET_WND_SLOT_ATTR_CHANGE:
		
			# Return if upbringing item is already in place
			if -1 != self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE]:
				return False
			

			if item.ITEM_TYPE_PET != itemType or itemSubType != item.PET_UPBRINGING:
				return False
				
			# Return if there is an active pet
			activePetId = player.GetActivePetItemId()
			if activePetId != 0:
				return False
					
			# Select attr change item if it wasn't selected yet
			if -1 == self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE_ITEM]:

				attrChangePos = player.GetItemSlotIndex(player.PET_ATTR_CHANGE_ITEM)
				if attrChangePos != -1:
					self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE_ITEM] = attrChangePos
					self.attrChangeSlot.SetItemSlot(player.PET_WND_SLOT_ATTR_CHANGE_ITEM, player.PET_ATTR_CHANGE_ITEM)
				
		elif slotIndex == player.PET_WND_SLOT_ATTR_CHANGE_ITEM:
		
			# Return if attr change item is already in place
			if -1 != self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE_ITEM]:
				return False
				
			if item.ITEM_TYPE_PET != itemType or itemSubType != item.PET_ATTR_CHANGE:
				return False
				
		elif slotIndex == player.PET_WND_SLOT_ATTR_CHANGE_RESULT:
			return False
			
		self.attrChangeIndex[slotIndex] = attachedSlotPos
		self.attrChangeSlot.SetItemSlot(slotIndex, attachedItemVNum)
		self.attrChangeSlot.RefreshSlot()
		
		if self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE_ITEM] != -1 and self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE] != -1:
			self.attrChangeButton.Show()
		
		mouseModule.mouseController.DeattachObject()
		return True
		
	def ClickAttrChangeButton(self):
		if self.questionDialog.IsShow():
			return
			
		self.questionDialog.SetText(localeInfo.PET_ATTR_CHANGE_DIALOG_TEXT)
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__PetAttrChangeAccept))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__PetAttrChangeCancel))
		self.questionDialog.Open()
		
	def ClickAttrClearButton(self):
		self.__ClearAttrChangeWindow()
			
	def __ClearAttrChangeWindow(self):
		if self.questionDialog.IsShow():
			self.questionDialog.Close()
		
		self.attrChangeText.SetText("")
		for i in range(player.PET_WND_SLOT_ATTR_CHANGE_MAX):
			self.__ClearAttrChangeSlot(i)
	
	def __PetAttrChangeAccept(self):
		upBringingPos = self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE]
		attrChangePos = self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE_ITEM]
		
		# Send packet if positions are valid and close the question dialog
		if upBringingPos != -1 and attrChangePos != -1:
			net.SendPetAttrChange(upBringingPos, attrChangePos)
			
		self.questionDialog.Close()
		
	def __PetAttrChangeCancel(self):
		self.questionDialog.Close()
		
	def PetAttrChangeResult(self, slotIndex, byType):
		self.attrChangeButton.Hide()

		text = self.typeInfo[byType]
		self.attrChangeText.SetText(text)

		# Clear slots 
		for i in range(player.PET_WND_SLOT_ATTR_CHANGE_MAX):
			self.__ClearAttrChangeSlot(i)
			
		# Append new upbringing pet item in result slot
		itemVnum = player.GetItemIndex(slotIndex)
		self.attrChangeIndex[player.PET_WND_SLOT_ATTR_CHANGE_RESULT] = slotIndex
		self.attrChangeSlot.SetItemSlot(player.PET_WND_SLOT_ATTR_CHANGE_RESULT, itemVnum)
		self.attrChangeSlot.RefreshSlot()
		
	def ItemMoveAttrChangeWindow(self, slotWindow, slotIndex):
		if player.INVENTORY == slotWindow:
			attachSlotType = player.SLOT_TYPE_INVENTORY
		else:
			return False
	
		mouseModule.mouseController.DeattachObject()
		
		selectedItemVNum = player.GetItemIndex(slotWindow, slotIndex)
		count			 = player.GetItemCount(slotWindow, slotIndex)
		
		mouseModule.mouseController.AttachObject(self, attachSlotType, slotIndex, selectedItemVNum, count)
		
		item.SelectItem(selectedItemVNum)
		
		if item.GetItemType() == item.ITEM_TYPE_PET:
			if item.GetItemSubType() == item.PET_UPBRINGING:
				slotPos = player.PET_WND_SLOT_ATTR_CHANGE
				
			elif item.GetItemSubType() == item.PET_ATTR_CHANGE:
				slotPos = player.PET_WND_SLOT_ATTR_CHANGE_ITEM
				
			else:
				return False
		
			self.SelectEmptyAttrChangeSlot(slotPos)
		
			mouseModule.mouseController.DeattachObject()
			return True
		
		return False
		
	def ClickDetermineButton(self):
		# If there is an active pet and player has player.PET_ATTR_DETERMINE_ITEM 
		# item, send the packet
		activePetId = player.GetActivePetItemId()
		if activePetId != 0:
					
			sourcePos = player.GetItemSlotIndex(player.PET_ATTR_DETERMINE_ITEM)
			if sourcePos != -1:
				net.SendPetAttrDetermine(sourcePos)

	def PetAttrDetermineResult(self, byType):
		# Display determine result in a popup dialog
		text = self.typeInfo[byType]
		self.__OpenPopupDialog(text)
		
	def __DescPetPremiumFeedstuff(self):
		# Initialize pet premium feedstuff description
		event.ClearEventSet(self.descIndex)

		self.descIndex = event.RegisterEventSet(uiScriptLocale.PET_PRIMIUM_FEEDSTUFF_DESC)
		event.SetVisibleLineCount(self.descIndex, VISIBLE_LINE_COUNT)

		if localeInfo.IsARABIC():
			event.SetEventSetWidth(self.descIndex, 50)
			
		event.SetVisibleLineCount(self.descIndex, VISIBLE_LINE_COUNT)
		event.SetRestrictedCount(self.descIndex, 70)

	def PetPremiumFeedStuffPrevDescriptionPage(self):
		line_height	= event.GetLineHeight(self.descIndex) + 4
		if localeInfo.IsARABIC():
			line_height -= 4
			
		cur_start_line	= event.GetVisibleStartLine(self.descIndex)
		
		decrease_count = VISIBLE_LINE_COUNT
		
		if cur_start_line - decrease_count < 0:
			return;

		event.SetVisibleStartLine(self.descIndex, cur_start_line - decrease_count)
		self.desc_Y += (line_height * decrease_count)

	def PetPremiumFeedStuffNextDescriptionPage(self):
		line_height	= event.GetLineHeight(self.descIndex) + 4
		if localeInfo.IsARABIC():
			line_height -= 4
			
		total_line_count = event.GetProcessedLineCount(self.descIndex)
		cur_start_line = event.GetVisibleStartLine(self.descIndex)
		
		increase_count = VISIBLE_LINE_COUNT
		
		if cur_start_line + increase_count >= total_line_count:
			increase_count = total_line_count - cur_start_line

		if increase_count < 0 or cur_start_line + increase_count >= total_line_count:
			return
		
		event.SetVisibleStartLine(self.descIndex, cur_start_line + increase_count)
		self.desc_Y -= (line_height * increase_count)
		
		
	def OverInPetReviveResultSlot(self):
		if None != self.tooltipItem:
			invenPos = self.petReviveIndex
			if invenPos != -1:
				if self.isPetReviveResultTooltip:	# Real pet tooltip after being revived
					self.tooltipItem.SetInventoryItem(invenPos, player.INVENTORY)
				else:	# To be revived pet dummy tooltip
					metinSlot = [player.GetItemMetinSocket(invenPos, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
					pet_id = metinSlot[2]

					if pet_id:
						self.tooltipItem.ClearToolTip()
						
						itemVnum = player.GetItemIndex(invenPos)
						item.SelectItem(itemVnum)
						
						skillStates = [self.__GetPetSkillState(pet_id, slot) for slot in range(SKILL_SLOT_MAX)]
						skill_count = len([state for state in skillStates if not state[0]])
						(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
						
						# Item Title
						self.tooltipItem.AppendTextLine(pet_nick, self.tooltipItem.TITLE_COLOR)
						
						# Item Description
						itemDesc = item.GetItemDescription()
						self.tooltipItem.AppendDescription(itemDesc, 26)
						
						## Pet Type
						PET_TYPES = [
							0,
							localeInfo.PET_ATTR_DETERMINE_TYPE1_TOOLTIP,
							localeInfo.PET_ATTR_DETERMINE_TYPE2_TOOLTIP,
							localeInfo.PET_ATTR_DETERMINE_TYPE3_TOOLTIP,
							localeInfo.PET_ATTR_DETERMINE_TYPE4_TOOLTIP,
							localeInfo.PET_ATTR_DETERMINE_TYPE5_TOOLTIP,
							localeInfo.PET_ATTR_DETERMINE_TYPE6_TOOLTIP,
							localeInfo.PET_ATTR_DETERMINE_TYPE7_TOOLTIP,
							localeInfo.PET_ATTR_DETERMINE_TYPE8_TOOLTIP,
						]
						
						pet_type = metinSlot[3]
						self.tooltipItem.AppendSpace(5)
						self.tooltipItem.AppendTextLine(PET_TYPES[pet_type], self.tooltipItem.SPECIAL_POSITIVE_COLOR2)
						
						# Pet Level/Age
						self.tooltipItem.AppendSpace(5)
						birthSec = max(0, metinSlot[0] - birthday)
						self.tooltipItem.AppendTextLine(localeInfo.PET_TOOLTIP_LEVEL + " " + str(pet_level) + " (" + localeInfo.SecondToDay(birthSec * 0.8) + ")")

						# Pet Evolution / Skill Count
						self.tooltipItem.AppendSpace(5)
						if skill_count:
							self.tooltipItem.AppendTextLine(self.tooltipItem.GetEvolName(evol_level) + "(" + str(skill_count) + ")")
						else:
							self.tooltipItem.AppendTextLine(self.tooltipItem.GetEvolName(evol_level))

						# Pet HP/SP/DEF
						self.tooltipItem.AppendSpace(5)
						self.tooltipItem.AppendTextLine(localeInfo.PET_TOOLTIP_HP + " +" + str("%0.1f" % pet_hp) + "%", self.tooltipItem.SPECIAL_POSITIVE_COLOR)
						self.tooltipItem.AppendTextLine(localeInfo.PET_TOOLTIP_DEF + " +" + str("%0.1f" % pet_def) + "%", self.tooltipItem.SPECIAL_POSITIVE_COLOR)
						self.tooltipItem.AppendTextLine(growthpetpresentation.ThirdBonusLabel(pet_type) + " +" + str("%0.1f" % growthpetpresentation.ThirdAppliedPercent(pet_sp)) + "%", self.tooltipItem.SPECIAL_POSITIVE_COLOR)
						# Pet Skills
						for (skillLocked, skillVnum, skillLevel, cooltime, skillDetails) in skillStates:
							if skillLocked or not skillVnum:
								continue
							self.tooltipItem.AppendSpace(5)
							(skillName, skillDesc, skillUseType, skillCoolTime) = skill.GetPetSkillInfo(skillVnum)
							self.tooltipItem.AppendTextLine(localeInfo.PET_TOOLTUP_SKILL % (skillName, skillLevel), self.tooltipItem.SPECIAL_POSITIVE_COLOR)
						# Pet Lifetime
						for i in range(item.LIMIT_MAX_NUM):
							(limitType, limitValue) = item.GetLimit(i)
							if item.LIMIT_REAL_TIME == limitType:
								(endTime, maxTime) = player.GetPetLifeTime(pet_id)
								self.tooltipItem.AppendPetItemLastTime(app.GetGlobalTimeStamp() + maxTime)
								
						self.tooltipItem.Show()
				
		return
		
	def OverOutPetReviveResultSlot(self):
		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()
		return
		
	def OverInPetReviveSlot(self):
		if None != self.tooltipItem:
			invenPos = self.petReviveIndex
			if invenPos != -1:
				self.tooltipItem.SetInventoryItem(invenPos, player.INVENTORY)
				
		return
		
	def OverOutPetReviveSlot(self):
		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()
		return
		
	def __ClearPetReviveWindow(self):
		self.CanInvenSlot(self.petReviveIndex)
			
		self.isPetReviveResultTooltip = False
		self.petReviveIndex = -1
		
		self.petReviveSlot.SetItemSlot(0, 0)
		self.petReviveSlot.RefreshSlot()
		
		self.petReviveResultSlot.SetItemSlot(0, 0)
		self.petReviveResultSlot.RefreshSlot()

		for i in range(player.PET_REVIVE_MATERIAL_SLOT_MAX):
			self.petReviveMaterialSlot.SetItemSlot(i, 0)
			self.petReviveMaterialSlot.RefreshSlot()
			
			if self.petReviveItems[i]:
				self.CanInvenSlot(self.petReviveItems[i])
			self.petReviveItems[i] = -1
			self.petReviveItemsCount[i] = 0
			
		self.petReviveAgeText.SetText("")
		self.petReviveResultAgeText.SetText("")
		self.petReviveItemsCountText.SetText(localeInfo.PET_REVIVE_UI_MATERIAL_COUNT % (0, 0))
		
	def SelectPetReviveEmptySlot(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return False
		
		attachedSlotType	= mouseModule.mouseController.GetAttachedType()			
		attachedSlotPos		= mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemVNum	= player.GetItemIndex(attachedSlotPos)
		item.SelectItem(attachedItemVNum)		
		
		itemType	= item.GetItemType()
		itemSubType = item.GetItemSubType()			

		# Return if item is beging attached from not inventory window
		if player.SLOT_TYPE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SKILL_BOOK_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_GIFT_BOX_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SWITCH_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_COSTUME_INVENTORY != attachedSlotType:
			return False
			
		# Return if item position is bigger than player.INVENTORY_SLOT_COUNT
		if attachedSlotPos >= player.INVENTORY_SLOT_COUNT: 
			return False
			
		curTime = app.GetGlobalTimeStamp()
		metinSlot = [player.GetItemMetinSocket(attachedSlotPos, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		
		# Return if there is an active pet or target pet is still alive
		if item.ITEM_TYPE_PET == itemType and itemSubType == item.PET_UPBRINGING:
			activePetId = player.GetActivePetItemId()
			if activePetId != 0:
				return False
				
			if metinSlot[0] > curTime:
				return False
		else:
			return False

		# Return if there is already pet in place
		if self.petReviveIndex != -1:
			return False

		# Return if no pet_id in the socket
		pet_id = metinSlot[2]
		if 0 == pet_id:
			return False
			
		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		birthSec = max(0, metinSlot[0] - birthday)
		
		# Upbringing Slot
		self.petReviveIndex = attachedSlotPos
		self.petReviveSlot.SetItemSlot(slotIndex, attachedItemVNum)
		self.petReviveSlot.RefreshSlot()
		
		# Revived Upbringing Slot
		self.petReviveResultSlot.SetItemSlot(slotIndex, attachedItemVNum)
		self.petReviveResultSlot.RefreshSlot()
		
		# Age Texts
		self.petReviveAgeText.SetText("%s" % localeInfo.SecondToDay(birthSec))
		self.petReviveResultAgeText.SetText("%s" % localeInfo.SecondToDay(birthSec * 0.8))
		self.__RefreshPetReviveMaterialCount()		
		
		mouseModule.mouseController.DeattachObject()
		return True
		
	def SelectPetReviveItemSlot(self):
		self.__ClearPetReviveWindow()
		
	def SelectPetReviveMaterialEmptySlot(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return False
		
		attachedSlotType	= mouseModule.mouseController.GetAttachedType()			
		attachedSlotPos		= mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemCount	= mouseModule.mouseController.GetAttachedItemCount()
		attachedItemVNum	= player.GetItemIndex(attachedSlotPos)
		item.SelectItem(attachedItemVNum)		
		
		itemType	= item.GetItemType()
		itemSubType = item.GetItemSubType()	
		
		# Return if item is beging attached from not inventory window
		if player.SLOT_TYPE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SKILL_BOOK_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_GIFT_BOX_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_SWITCH_INVENTORY != attachedSlotType and\
			player.SLOT_TYPE_COSTUME_INVENTORY != attachedSlotType:
			return False
			
		# Return if item position is bigger than player.INVENTORY_SLOT_COUNT
		if attachedSlotPos >= player.INVENTORY_SLOT_COUNT: 
			return False
		
		# Return if there is no to-be-revived pet in slot
		if self.petReviveIndex == -1:
			return False
			
		# Return if material is not item.PET_PRIMIUM_FEEDSTUFF
		if itemType != item.ITEM_TYPE_PET or itemSubType != item.PET_PRIMIUM_FEEDSTUFF:
			return False
			
		# Return if the slot is already occupied or item is in another slot
		if self.petReviveItems[slotIndex] != -1:
			return False
			
		if attachedSlotPos in self.petReviveItems:
			return False
			
		# Return if enough material has been appended
		if self.HasEnoughPetReviveMaterial():
			return False
	
		self.petReviveItems[slotIndex] = attachedSlotPos
		self.petReviveItemsCount[slotIndex] = attachedItemCount
		self.petReviveMaterialSlot.SetItemSlot(slotIndex, attachedItemVNum, attachedItemCount)
		self.petReviveMaterialSlot.RefreshSlot()
		
		# Refresh required material text
		self.__RefreshPetReviveMaterialCount()
		
		mouseModule.mouseController.DeattachObject()
		return True
		
	def SelectPetReviveMaterialItemSlot(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			return

		self.CanInvenSlot(self.petReviveItems[slotIndex])
		self.petReviveItems[slotIndex] = -1
		self.petReviveItemsCount[slotIndex] = 0
		self.petReviveMaterialSlot.ClearSlot(slotIndex)
		self.petReviveMaterialSlot.RefreshSlot()
		
		self.__RefreshPetReviveMaterialCount()
		
	def __RefreshPetReviveMaterialCount(self):
		if -1 == self.petReviveIndex:
			self.petReviveItemsCountText.SetText(localeInfo.PET_REVIVE_UI_MATERIAL_COUNT % (0, 0))
			return
			
		metinSlot = [player.GetItemMetinSocket(self.petReviveIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		pet_id = metinSlot[2]

		# Pet data
		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		birthSec = max(0, metinSlot[0] - birthday)
		
		# Material Count
		petMaxReviveMaterialCount = localeInfo.SecondToDayNumber(birthSec) // 10
		if petMaxReviveMaterialCount < 1:
			petMaxReviveMaterialCount = 1
			
		petReviveMaterialCount = 0
		for i in range(player.PET_REVIVE_MATERIAL_SLOT_MAX):
			if self.petReviveItems[i] != -1:
				petReviveMaterialCount += self.petReviveItemsCount[i]
			
		# Set added mateiral count to required material count if higher
		if petReviveMaterialCount > petMaxReviveMaterialCount:
			petReviveMaterialCount = petMaxReviveMaterialCount
			
		self.petReviveItemsCountText.SetText(localeInfo.PET_REVIVE_UI_MATERIAL_COUNT % (petReviveMaterialCount, petMaxReviveMaterialCount))
		
	def HasEnoughPetReviveMaterial(self):
		if -1 == self.petReviveIndex:
			return False
			
		metinSlot = [player.GetItemMetinSocket(self.petReviveIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		pet_id = metinSlot[2]

		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		birthSec = max(0, metinSlot[0] - birthday)
		
		# Material Count
		petMaxReviveMaterialCount = localeInfo.SecondToDayNumber(birthSec) // 10
		if petMaxReviveMaterialCount < 1:
			petMaxReviveMaterialCount = 1
			
		itemCount = 0
		for i in range(player.PET_REVIVE_MATERIAL_SLOT_MAX):
			if self.petReviveItems[i] != -1:
				itemCount += self.petReviveItemsCount[i]
			
			if itemCount >= petMaxReviveMaterialCount:
				return True
				
		return False
		
	def ClickPetReviveButton(self):
		# Return if there is no pet upbringing item in slot
		if self.petReviveIndex == -1:
			self.__OpenPopupDialog(localeInfo.PET_REVIVE_FAIL_EMPTY_PET_SLOT)
			return
			
		# Return if question dialog is already opened
		if self.questionDialog.IsShow():
			return
			
		# Return if there is not enough material
		if not self.HasEnoughPetReviveMaterial():
			self.__OpenPopupDialog(localeInfo.PET_REVIVE_FAIL_NOT_ENOUGHT_MATERIAL)
			return
			
		metinSlot = [player.GetItemMetinSocket(self.petReviveIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		pet_id = metinSlot[2]

		(pet_level, evol_level, birthday, pet_nick, pet_hp, pet_def, pet_sp) = player.GetPetItem(pet_id)
		birthSec = max(0, metinSlot[0] - birthday)
		
		petMaxReviveMaterialCount = localeInfo.SecondToDayNumber(birthSec) // 10
		if petMaxReviveMaterialCount < 1:
			petMaxReviveMaterialCount = 1
			
		self.questionDialog.SetText(localeInfo.REVIVE_QUESTION % (pet_nick, petMaxReviveMaterialCount)) 
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__PetReviveAccept))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__PetReviveCancel))
		self.questionDialog.Open()
			
	def __PetReviveAccept(self):
		resultReviveItems = [value for value in self.petReviveItems if value != -1]
		resultReviveItemsCount = [value for value in self.petReviveItemsCount if value != 0]
		
		# Send revive packet if there are items in list and close the question dialog
		if resultReviveItems:
			net.SendPetRevive(self.petReviveIndex, resultReviveItems, resultReviveItemsCount)
			
		self.questionDialog.Close()
		
	def __PetReviveCancel(self):
		self.questionDialog.Close()
		
	def ClickPetReviveCancelButton(self):
		self.__ClearPetReviveWindow()
		self.__ShowPetView()
		
	def PetReviveResult(self, result):
		if not result:
			message = getattr(localeInfo, "PET_REVIVE_NEEDS_PROTEIN_BAR",
				u"K oživení potřebuješ Proteinovou tyčinku.")
			chat.AppendChat(chat.CHAT_TYPE_INFO, message)
		self.RefreshStatus()
			
			
	def ItemMovePremiumFeedWindow(self, slotWindow, attachSlotType, slotIndex):
		#if player.INVENTORY == slotWindow:
		#	attachSlotType = player.SLOT_TYPE_INVENTORY
		#else:
		#	return False
	
		mouseModule.mouseController.DeattachObject()
		
		selectedItemVNum = player.GetItemIndex(slotWindow, slotIndex)
		count			 = player.GetItemCount(slotWindow, slotIndex)
		
		mouseModule.mouseController.AttachObject(self, attachSlotType, slotIndex, selectedItemVNum, count)
		
		item.SelectItem(selectedItemVNum)
		
		if item.GetItemType() == item.ITEM_TYPE_PET:
			if item.GetItemSubType() == item.PET_UPBRINGING:
				return self.SelectPetReviveEmptySlot(0)
				
			elif item.GetItemSubType() == item.PET_PRIMIUM_FEEDSTUFF:
				# Return the first available slot
				for i in range(player.PET_REVIVE_MATERIAL_SLOT_MAX):
					if self.petReviveItems[i] == -1:
						return self.SelectPetReviveMaterialEmptySlot(i)
		
		return False
	
	def AttachItemToPetWindow(self, windowType, slotType, slotIndex):
		if self.IsShow():
			if self.GetState() == player.PET_WINDOW_INFO and self.feedIndex != player.FEED_BUTTON_MAX:
				if not self.CantFeedItem(slotIndex):
					if self.wndPetFeed.ItemMoveFeedWindow(windowType, slotType, slotIndex):
						return True
					
			elif self.GetState() == player.PET_WINDOW_ATTR_CHANGE:
				if self.ItemMoveAttrChangeWindow(windowType, slotIndex):
					return True
				
			elif  self.GetState() == player.PET_WINDOW_PRIMIUM_FEEDSTUFF:
				if self.ItemMovePremiumFeedWindow(windowType, slotType, slotIndex):
					return True

		return False
		
