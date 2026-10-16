import ui
import mouseModule
import slotwindowpolicy
import player
import net
import snd
import safebox
import chat
import app
import localeInfo
import uiScriptLocale
import item
import osfInfo
import item
import storagepresentation

LEGACY_PAGE_START_POS = (8, 32)
EXPANDED_PAGE_START_POS = (8, 63)
MAX_EXPANDED_PAGE_COUNT = 3


def GetSafeboxLayout():
	return storagepresentation.GetLayout(safebox)


def UseParentPageTabs():
	return GetSafeboxLayout()[0] == 2


class PasswordDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadDialog()

		self.sendMessage = "/safebox_password "

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadDialog(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			# if localeInfo.IsEUROPE()and app.GetLocalePath() != "locale/ca"and app.GetLocalePath() != "locale/sg" :
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "passworddialog.py")
			# else:
				# pyScrLoader.LoadScriptFile(self, "uiscript/passworddialog.py")
		except:
			import exception
			exception.Abort("PasswordDialog.__LoadDialog.LoadObject")

		try:
			self.passwordValue = self.GetChild("password_value")
			self.acceptButton = self.GetChild("accept_button")
			self.cancelButton = self.GetChild("cancel_button")
			self.titleName = self.GetChild("TitleName")
			self.GetChild("titlebar").SetCloseEvent(ui.__mem_func__(self.CloseDialog))
		except:
			import exception
			exception.Abort("PasswordDialog.__LoadDialog.BindObject")

		self.passwordValue.OnIMEReturn = ui.__mem_func__(self.OnAccept)
		self.passwordValue.OnPressEscapeKey = ui.__mem_func__(self.OnCancel)
		self.acceptButton.SetEvent(ui.__mem_func__(self.OnAccept))
		self.cancelButton.SetEvent(ui.__mem_func__(self.OnCancel))

	def Destroy(self):
		self.ClearDictionary()
		self.passwordValue = None
		self.acceptButton = None
		self.cancelButton = None
		self.titleName = None

	def SetTitle(self, title):
		self.titleName.SetText(title)

	def SetSendMessage(self, msg):
		self.sendMessage = msg

	def ShowDialog(self):
		if app.ENABLE_GROWTH_PET_SYSTEM:
			if player.IsOpenPetHatchingWindow():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_HATCHING_WINDOW_OPEN_CAN_NOT_USE)
				return False
		self.passwordValue.SetText("")
		self.passwordValue.SetFocus()
		self.SetCenterPosition()
		self.Show()

	def CloseDialog(self):
		self.passwordValue.KillFocus()
		self.Hide()

	def OnAccept(self):
		net.SendChatPacket(self.sendMessage + self.passwordValue.GetText())
		self.CloseDialog()
		return True

	def OnCancel(self):
		self.CloseDialog()
		return True

class ChangePasswordDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadDialog(self):
		self.dlgMessage = ui.ScriptWindow()
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self.dlgMessage, "uiscript/popupdialog.py")
			self.dlgMessage.GetChild("message").SetText(localeInfo.SAFEBOX_WRONG_PASSWORD)
			self.dlgMessage.GetChild("accept").SetEvent(ui.__mem_func__(self.OnCloseMessageDialog))
		except:
			import exception
			exception.Abort("SafeboxWindow.__LoadDialog.LoadObject")

	def LoadDialog(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/changepassworddialog.py")

		except:
			import exception
			exception.Abort("ChangePasswordDialog.LoadDialog.LoadObject")

		try:
			self.GetChild("accept_button").SetEvent(ui.__mem_func__(self.OnAccept))
			self.GetChild("cancel_button").SetEvent(ui.__mem_func__(self.OnCancel))
			self.GetChild("titlebar").SetCloseEvent(ui.__mem_func__(self.OnCancel))
			oldPassword = self.GetChild("old_password_value")
			newPassword = self.GetChild("new_password_value")
			newPasswordCheck = self.GetChild("new_password_check_value")
		except:
			import exception
			exception.Abort("ChangePasswordDialog.LoadDialog.BindObject")

		oldPassword.SetTabEvent(lambda arg=1: self.OnNextFocus(arg))
		newPassword.SetTabEvent(lambda arg=2: self.OnNextFocus(arg))
		newPasswordCheck.SetTabEvent(lambda arg=3: self.OnNextFocus(arg))
		oldPassword.SetReturnEvent(lambda arg=1: self.OnNextFocus(arg))
		newPassword.SetReturnEvent(lambda arg=2: self.OnNextFocus(arg))
		newPasswordCheck.SetReturnEvent(ui.__mem_func__(self.OnAccept))
		oldPassword.OnPressEscapeKey = self.OnCancel
		newPassword.OnPressEscapeKey = self.OnCancel
		newPasswordCheck.OnPressEscapeKey = self.OnCancel

		self.oldPassword = oldPassword
		self.newPassword = newPassword
		self.newPasswordCheck = newPasswordCheck

	def OnNextFocus(self, arg):
		if 1 == arg:
			self.oldPassword.KillFocus()
			self.newPassword.SetFocus()
		elif 2 == arg:
			self.newPassword.KillFocus()
			self.newPasswordCheck.SetFocus()
		elif 3 == arg:
			self.newPasswordCheck.KillFocus()
			self.oldPassword.SetFocus()

	def Destroy(self):
		self.ClearDictionary()
		self.dlgMessage.ClearDictionary()
		self.oldPassword = None
		self.newPassword = None
		self.newPasswordCheck = None

	def Open(self):
		self.oldPassword.SetText("")
		self.newPassword.SetText("")
		self.newPasswordCheck.SetText("")
		self.oldPassword.SetFocus()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.oldPassword.SetText("")
		self.newPassword.SetText("")
		self.newPasswordCheck.SetText("")
		self.oldPassword.KillFocus()
		self.newPassword.KillFocus()
		self.newPasswordCheck.KillFocus()
		self.Hide()

	def OnAccept(self):
		oldPasswordText = self.oldPassword.GetText()
		newPasswordText = self.newPassword.GetText()
		newPasswordCheckText = self.newPasswordCheck.GetText()
		if newPasswordText != newPasswordCheckText:
			self.dlgMessage.SetCenterPosition()
			self.dlgMessage.SetTop()
			self.dlgMessage.Show()
			return True
		net.SendChatPacket("/safebox_change_password %s %s" % (oldPasswordText, newPasswordText))
		self.Close()
		return True

	def OnCancel(self):
		self.Close()
		return True

	def OnCloseMessageDialog(self):
		self.newPassword.SetText("")
		self.newPasswordCheck.SetText("")
		self.newPassword.SetFocus()
		self.dlgMessage.Hide()


class SafeboxWindow(ui.ScriptWindow):
	if app.ENABLE_SAFEBOX_5PAGES:
		PAGE_TEXT = ( "I", "II", "III", "IV", "V")

	def __init__(self, wndSpecialInv = None):
		if not wndSpecialInv:
			print("cant load wndSpecialInv (safeboxwindow)")
			return

		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.sellingSlotNumber = -1
		self.pageButtonList = []
		self.pageCount = 1
		self.curPageIndex = 0
		self.dataReady = False
		self.isLoaded = 0
		self.interface = None
		self.wndSpecialInv = wndSpecialInv
		self.SetParent(self.wndSpecialInv)
		self.__ApplyRuntimeLayout()
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __ApplyRuntimeLayout(self):
		(self.layoutVersion, self.slotXCount, self.slotYCount,
		 self.pageSize) = GetSafeboxLayout()
		self.pageWidth = self.slotXCount * 32
		self.pageButtonY = self.slotYCount * 32 + 5
		if self.layoutVersion == 2:
			pageStartPos = EXPANDED_PAGE_START_POS
			# Layout v2 pages through the parent SpecialInventoryWindow tabs
			# just below the grid. This pickable child must end at the grid,
			# otherwise its transparent strip swallows clicks on tabs II/III.
			self.pageHeight = self.slotYCount * 32
		else:
			pageStartPos = LEGACY_PAGE_START_POS
			# Legacy layout keeps its own page buttons inside this window.
			self.pageHeight = self.slotYCount * 32 + 30
		self.SetPosition(*pageStartPos)
		self.SetSize(self.pageWidth, self.pageHeight)

	def Show(self):
		self.__LoadWindow()

		ui.ScriptWindow.Show(self)

	def Destroy(self):
		self.ClearDictionary()

		self.tooltipItem = None
		self.wndItem = None

		self.pageButtonList = []

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		from _weakref import proxy

		## Item
		wndItem = ui.GridSlotWindow()
		wndItem.SetParent(self)
		wndItem.SetPosition(0, 0)
		wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		wndItem.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndItem.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		wndItem.Show()

		self.wndItem = wndItem

		## Initialize
		self.SetTableSize(3)
		self.RefreshSafeboxMoney()

	def OpenPickMoneyDialog(self):
		if mouseModule.mouseController.isAttached():
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()

			if player.SLOT_TYPE_INVENTORY == mouseModule.mouseController.GetAttachedType():
				if player.ITEM_MONEY == mouseModule.mouseController.GetAttachedItemIndex():
					net.SendSafeboxSaveMoneyPacket(mouseModule.mouseController.GetAttachedItemCount())
					snd.PlaySound("sound/ui/money.wav")

			mouseModule.mouseController.DeattachObject()
		else:
			curMoney = safebox.GetMoney()

			if curMoney <= 0:
				return

			self.dlgPickMoney.Open(curMoney)

	def ShowWindow(self, size):
		self.SetTableSize(size)
		self.dataReady = True
		self.SetTop()
		self.Show()
		self.RefreshSafebox()

		if app.ENABLE_GROWTH_PET_SYSTEM:
			player.SetOpenSafeBox(True)

	def __ClearVisibleItems(self):
		for localSlot in range(self.pageSize):
			self.wndItem.ClearSlot(localSlot)
			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				self.wndItem.EnableSlotCoverImage(localSlot, False)
		self.wndItem.RefreshSlot()

	def PrepareWindow(self):
		self.dataReady = False
		self.SetTableSize(self.slotYCount * MAX_EXPANDED_PAGE_COUNT)
		self.curPageIndex = 0
		self.__ClearVisibleItems()
		self.Show()

	if app.ENABLE_SAFEBOX_5PAGES:
		def __MakePageButton(self, pageCount):
			for button in self.pageButtonList:
				button.Hide()
			self.curPageIndex = 0
			self.pageButtonList = []

			m_tooltip = [uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_1, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_2, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_3, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_4, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_5]
			pos = -int(float(pageCount-1)/2 * 32)
			for i in range(pageCount):
				text = self.PAGE_TEXT[i]
				button = ui.RadioButton()
				button.SetParent(self)
				button.SetUpVisual("d:/ymir work/ui/game/windows/tab_button_small_01.sub")
				button.SetOverVisual("d:/ymir work/ui/game/windows/tab_button_small_02.sub")
				button.SetDownVisual("d:/ymir work/ui/game/windows/tab_button_small_03.sub")
				button.SetWindowHorizontalAlignCenter()
				button.SetToolTipText(m_tooltip[i])
				button.SetPosition(pos, self.pageButtonY)
				button.SetText(text)
				button.SetEvent(lambda arg=i: self.SelectPage(arg))
				button.Show()
				self.pageButtonList.append(button)
				pos += 32
			self.pageButtonList[0].Down()
	else:
		def __MakePageButton(self, pageCount):
			for button in self.pageButtonList:
				button.Hide()
			self.curPageIndex = 0
			self.pageButtonList = []

			text = "I"
			m_tooltip = [uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_1, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_2, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_3]
			pos = -int(float(pageCount-1)/2 * 52)
			for i in range(pageCount):
				button = ui.RadioButton()
				button.SetParent(self)
				button.SetUpVisual("d:/ymir work/ui/game/windows/tab_button_middle_01.sub")
				button.SetOverVisual("d:/ymir work/ui/game/windows/tab_button_middle_02.sub")
				button.SetDownVisual("d:/ymir work/ui/game/windows/tab_button_middle_03.sub")
				button.SetWindowHorizontalAlignCenter()
				button.SetToolTipText(m_tooltip[i])
				button.SetPosition(pos, self.pageButtonY)
				button.SetText(text)
				button.SetEvent(lambda arg=i: self.SelectPage(arg))
				button.Show()
				self.pageButtonList.append(button)
				pos += 52
				text += "I"
			self.pageButtonList[0].Down()

	def SelectPage(self, index):
		if index < 0 or index >= self.pageCount:
			return
		self.curPageIndex = index

		if not UseParentPageTabs():
			for btn in self.pageButtonList:
				btn.SetUp()

			self.pageButtonList[index].Down()
		if self.dataReady:
			self.RefreshSafebox()
		else:
			self.__ClearVisibleItems()

	def __LocalToGlobalSlot(self, localSlot):
		return self.curPageIndex * self.pageSize + localSlot

	def SetTableSize(self, size):
		self.__ApplyRuntimeLayout()
		pageCount = max(1, size // self.slotYCount)
		if UseParentPageTabs():
			pageCount = min(MAX_EXPANDED_PAGE_COUNT, pageCount)
			for button in self.pageButtonList:
				button.Hide()
			self.pageButtonList = []
		elif app.ENABLE_SAFEBOX_5PAGES:
			pageCount = min(5, pageCount)
		else:
			pageCount = min(3, pageCount)

		self.pageCount = pageCount
		if self.curPageIndex >= self.pageCount:
			self.curPageIndex = 0
		if not UseParentPageTabs():
			self.__MakePageButton(pageCount)
		self.wndItem.ArrangeSlot(0, self.slotXCount, self.slotYCount, 32, 32, 0, 0)
		self.wndItem.RefreshSlot()
		self.wndItem.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)

		self.SetSize(self.pageWidth, self.pageHeight)
		self.UpdateRect()

	def RefreshSafebox(self):
		if not self.dataReady:
			self.__ClearVisibleItems()
			return

		getItemID=safebox.GetItemID
		getItemCount=safebox.GetItemCount
		setItemID=self.wndItem.SetItemSlot

		for localSlot in range(self.pageSize):
			slotIndex = self.__LocalToGlobalSlot(localSlot)
			itemCount = getItemCount(slotIndex)
			if itemCount <= 1:
				itemCount = 0
			setItemID(localSlot, getItemID(slotIndex), itemCount)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				changelookitemvnum = safebox.GetItemChangeLookVnum(slotIndex)
				if not changelookitemvnum == 0:
					self.wndItem.SetSlotCoverImage(localSlot, "icon/item/ingame_convert_Mark.tga")
				else:
					self.wndItem.EnableSlotCoverImage(localSlot, False)

			if app.ENABLE_GROWTH_PET_SYSTEM:
				self.__SetCoolTimePetItemSlot( slotIndex, getItemID(slotIndex))

		self.wndItem.RefreshSlot()
		self.wndSpecialInv.RefreshActiveProviderSearch(self)

	def RefreshSafeboxMoney(self):
		pass
		#self.wndMoney.SetText(str(safebox.GetMoney()))

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def CommandCloseSafebox(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()

		if app.ENABLE_GROWTH_PET_SYSTEM:
			player.SetOpenSafeBox(False)

		self.curPageIndex = 0
		self.dataReady = False
		self.Hide()

	def IterSearchItems(self):
		if not self.dataReady:
			return
		slotCount = min(
			safebox.GetCurrentSafeboxSize(),
			self.pageCount * self.pageSize
		)
		for globalSlot in range(slotCount):
			itemVnum = safebox.GetItemID(globalSlot)
			if itemVnum:
				yield (
					globalSlot,
					itemVnum,
					safebox.GetItemCount(globalSlot)
				)

	def GetSearchItemSocket(self, globalSlot, socketIndex):
		return safebox.GetItemMetinSocket(globalSlot, socketIndex)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def __SetCoolTimePetItemSlot(self, slotNumber, itemVnum):
			if 0 == itemVnum:
				return
				
			item.SelectItem(itemVnum)
			itemSubType = item.GetItemSubType()
				
			if itemSubType not in [item.PET_UPBRINGING, item.PET_BAG]:
				return
						
			if itemSubType == item.PET_BAG:
				id = safebox.GetItemMetinSocket(slotNumber, 2)
				if id == 0:
					return
					
			(limitType, limitValue) = item.GetLimit(0)

			if itemSubType == item.PET_UPBRINGING:
				limitValue = safebox.GetItemMetinSocket(slotNumber, 1)
							
			if limitType in [item.LIMIT_REAL_TIME, item.LIMIT_REAL_TIME_START_FIRST_USE]:
										
				sock_time   = safebox.GetItemMetinSocket(slotNumber, 0)
				remain_time = max( 0, sock_time - app.GetGlobalTimeStamp() )

				if slotNumber >= self.pageSize:
					slotNumber -= (self.curPageIndex * self.pageSize)

				self.wndItem.SetSlotCoolTimeInverse(slotNumber, limitValue, limitValue - remain_time)

	## Slot Event
	def SelectEmptySlot(self, selectedSlotPos):
		selectedSlotPos = self.__LocalToGlobalSlot(selectedSlotPos)

		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()

			if player.SLOT_TYPE_SAFEBOX == attachedSlotType:
				net.SendSafeboxItemMovePacket(attachedSlotPos, selectedSlotPos, 0)
				#snd.PlaySound("sound/ui/drop.wav")
			else:
				attachedInvenType = slotwindowpolicy.ItemWindowForSlotType(attachedSlotType)
				if player.RESERVED_WINDOW == attachedInvenType:
					return

				if player.ITEM_MONEY == mouseModule.mouseController.GetAttachedItemIndex():
					net.SendSafeboxSaveMoneyPacket(mouseModule.mouseController.GetAttachedItemCount())
					snd.PlaySound("sound/ui/money.wav")
				else:
					net.SendSafeboxCheckinPacket(attachedInvenType, attachedSlotPos, selectedSlotPos)
					#snd.PlaySound("sound/ui/drop.wav")

			mouseModule.mouseController.DeattachObject()

	def SelectItemSlot(self, selectedSlotPos):
		selectedSlotPos = self.__LocalToGlobalSlot(selectedSlotPos)
		self.SelectGlobalItemSlot(selectedSlotPos)

	def SelectGlobalItemSlot(self, selectedSlotPos):
		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()

			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if slotwindowpolicy.IsInventorySlotType(attachedSlotType):

					if player.ITEM_MONEY == mouseModule.mouseController.GetAttachedItemIndex():
						net.SendSafeboxSaveMoneyPacket(mouseModule.mouseController.GetAttachedItemCount())
						snd.PlaySound("sound/ui/money.wav")
					else:
						attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
						#net.SendSafeboxCheckinPacket(attachedSlotPos, selectedSlotPos)
						#snd.PlaySound("sound/ui/drop.wav")
			else:
				if player.SLOT_TYPE_INVENTORY == attachedSlotType:
					if player.ITEM_MONEY == mouseModule.mouseController.GetAttachedItemIndex():
						net.SendSafeboxSaveMoneyPacket(mouseModule.mouseController.GetAttachedItemCount())
						snd.PlaySound("sound/ui/money.wav")
					else:
						attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
						#net.SendSafeboxCheckinPacket(attachedSlotPos, selectedSlotPos)
						#snd.PlaySound("sound/ui/drop.wav")

			mouseModule.mouseController.DeattachObject()
		else:
			curCursorNum = app.GetCursor()
			if app.SELL == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SAFEBOX_SELL_DISABLE_SAFEITEM)

			elif app.BUY == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_BUY_INFO)

			else:
				selectedItemID = safebox.GetItemID(selectedSlotPos)
				mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_SAFEBOX, selectedSlotPos, selectedItemID)
				snd.PlaySound("sound/ui/pick.wav")

	def UseItemSlot(self, slotIndex):
		self.UseGlobalItemSlot(self.__LocalToGlobalSlot(slotIndex))

	def UseGlobalItemSlot(self, slotIndex):
		mouseModule.mouseController.DeattachObject()

	def __ShowToolTip(self, slotIndex):
		if self.tooltipItem:
			self.tooltipItem.SetSafeBoxItem(slotIndex)

	def OverInItem(self, slotIndex):
		slotIndex = self.__LocalToGlobalSlot(slotIndex)
		self.OverInGlobalItem(slotIndex)

	def OverInGlobalItem(self, slotIndex):
		self.wndItem.SetUsableItem(False)
		self.__ShowToolTip(slotIndex)

	def OverOutItem(self):
		self.wndItem.SetUsableItem(False)
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	if app.WJ_ENABLE_TRADABLE_ICON:
		def CantCheckInItem(self, slotIndex):
			itemIndex = player.GetItemIndex(slotIndex)

			if itemIndex:
				return player.IsAntiFlagBySlot(slotIndex, item.ANTIFLAG_SAFEBOX)

			return False

		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

		def OnTop(self):
			if not self.interface:
				return

			self.interface.SetOnTopWindow(player.ON_TOP_WND_SAFEBOX)
			self.interface.RefreshMarkInventoryBag()

class MallWindow(ui.ScriptWindow):
	PAGE_TEXT = ("I", "II", "III", "IV", "V")
	
	def __init__(self, wndSpecialInv = None):
		if not wndSpecialInv:
			print("cant load wndSpecialInv (safeboxwindow)")
			return
		
		ui.ScriptWindow.__init__(self)
		
		self.tooltipItem = None
		self.sellingSlotNumber = -1
		self.pageButtonList = []
		self.pageCount = 1
		self.curPageIndex = 0
		self.dataReady = False
		self.isLoaded = 0
		self.interface = None
		self.wndSpecialInv = wndSpecialInv
		
		self.SetParent(self.wndSpecialInv)
		self.__ApplyRuntimeLayout()
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __ApplyRuntimeLayout(self):
		(self.layoutVersion, self.slotXCount, self.slotYCount,
		 self.pageSize) = GetSafeboxLayout()
		self.pageWidth = self.slotXCount * 32
		self.pageButtonY = self.slotYCount * 32 + 5
		if self.layoutVersion == 2:
			pageStartPos = EXPANDED_PAGE_START_POS
			# Layout v2 pages through the parent SpecialInventoryWindow tabs
			# just below the grid. This pickable child must end at the grid,
			# otherwise its transparent strip swallows clicks on tabs II/III.
			self.pageHeight = self.slotYCount * 32
		else:
			pageStartPos = LEGACY_PAGE_START_POS
			# Legacy layout keeps its own page buttons inside this window.
			self.pageHeight = self.slotYCount * 32 + 30
		self.SetPosition(*pageStartPos)
		self.SetSize(self.pageWidth, self.pageHeight)

	def Show(self):
		self.__LoadWindow()

		ui.ScriptWindow.Show(self)

	def Destroy(self):
		self.ClearDictionary()

		self.tooltipItem = None
		self.wndItem = None

		self.pageButtonList = []

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		## Item
		wndItem = ui.GridSlotWindow()
		wndItem.SetParent(self)
		wndItem.SetPosition(0, 0)
		wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		wndItem.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndItem.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		wndItem.Show()

		self.wndItem = wndItem

		## Initialize
		self.SetTableSize(3)

	def ShowWindow(self, size):
		self.SetTableSize(size)
		self.dataReady = True
		self.Show()
		self.RefreshMall()

		if app.ENABLE_GROWTH_PET_SYSTEM:
			player.SetOpenMall(True)

	def __ClearVisibleItems(self):
		for localSlot in range(self.pageSize):
			self.wndItem.ClearSlot(localSlot)
			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				self.wndItem.EnableSlotCoverImage(localSlot, False)
		self.wndItem.RefreshSlot()

	def PrepareWindow(self):
		self.dataReady = False
		self.SetTableSize(self.slotYCount * MAX_EXPANDED_PAGE_COUNT)
		self.curPageIndex = 0
		self.__ClearVisibleItems()
		self.Show()

	def __MakePageButton(self, pageCount):
		for button in self.pageButtonList:
			button.Hide()
		self.curPageIndex = 0
		self.pageButtonList = []

		m_tooltip = [uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_1, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_2, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_3, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_4, uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_5]
		pos = -int(float(pageCount-1)/2 * 32)
		for i in range(pageCount):
			button = ui.RadioButton()
			button.SetParent(self)
			button.SetUpVisual("d:/ymir work/ui/game/windows/tab_button_small_01.sub")
			button.SetOverVisual("d:/ymir work/ui/game/windows/tab_button_small_02.sub")
			button.SetDownVisual("d:/ymir work/ui/game/windows/tab_button_small_03.sub")
			button.SetWindowHorizontalAlignCenter()
			button.SetToolTipText(m_tooltip[i])
			button.SetPosition(pos, self.pageButtonY)
			button.SetText(self.PAGE_TEXT[i])
			button.SetEvent(lambda arg=i: self.SelectPage(arg))
			button.Show()
			self.pageButtonList.append(button)

			pos += 32

		self.pageButtonList[0].Down()

	def SelectPage(self, index):
		if index < 0 or index >= self.pageCount:
			return
		self.curPageIndex = index
		if not UseParentPageTabs():
			for button in self.pageButtonList:
				button.SetUp()
			self.pageButtonList[index].Down()
		if self.dataReady:
			self.RefreshMall()
		else:
			self.__ClearVisibleItems()

	def __LocalToGlobalSlot(self, localSlot):
		return self.curPageIndex * self.pageSize + localSlot

	def SetTableSize(self, size):
		self.__ApplyRuntimeLayout()
		pageCount = max(1, size // self.slotYCount)
		if UseParentPageTabs():
			pageCount = min(MAX_EXPANDED_PAGE_COUNT, pageCount)
			for button in self.pageButtonList:
				button.Hide()
			self.pageButtonList = []
		else:
			pageCount = min(5, pageCount)

		self.pageCount = pageCount
		if self.curPageIndex >= self.pageCount:
			self.curPageIndex = 0
		if not UseParentPageTabs():
			self.__MakePageButton(pageCount)
		self.wndItem.ArrangeSlot(0, self.slotXCount, self.slotYCount, 32, 32, 0, 0)
		self.wndItem.RefreshSlot()
		self.wndItem.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		self.SetSize(self.pageWidth, self.pageHeight)
		self.UpdateRect()

	def RefreshMall(self):
		if not self.dataReady:
			self.__ClearVisibleItems()
			return

		getItemID=safebox.GetMallItemID
		getItemCount=safebox.GetMallItemCount
		setItemID=self.wndItem.SetItemSlot

		for localSlot in range(self.pageSize):
			globalSlot = self.__LocalToGlobalSlot(localSlot)
			if globalSlot >= safebox.GetMallSize():
				self.wndItem.ClearSlot(localSlot)
				if app.ENABLE_CHANGE_LOOK_SYSTEM:
					self.wndItem.EnableSlotCoverImage(localSlot, False)
				continue
			itemID = getItemID(globalSlot)
			itemCount = getItemCount(globalSlot)
			if itemCount <= 1:
				itemCount = 0
			setItemID(localSlot, itemID, itemCount)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				changelookitemvnum = safebox.GetMallItemChangeLookVnum(globalSlot)
				if not changelookitemvnum == 0:
					self.wndItem.SetSlotCoverImage(localSlot, "icon/item/ingame_convert_Mark.tga")
				else:
					self.wndItem.EnableSlotCoverImage(localSlot, False)

		self.wndItem.RefreshSlot()
		self.wndSpecialInv.RefreshActiveProviderSearch(self)

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def Close(self):
		net.SendChatPacket("/mall_close")

	def CommandCloseMall(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
		if app.ENABLE_GROWTH_PET_SYSTEM:
			player.SetOpenMall(False)
		self.curPageIndex = 0
		self.dataReady = False
		self.Hide()

	def IterSearchItems(self):
		if not self.dataReady:
			return
		slotCount = min(
			safebox.GetMallSize(),
			self.pageCount * self.pageSize
		)
		for globalSlot in range(slotCount):
			itemVnum = safebox.GetMallItemID(globalSlot)
			if itemVnum:
				yield (
					globalSlot,
					itemVnum,
					safebox.GetMallItemCount(globalSlot)
				)

	def GetSearchItemSocket(self, globalSlot, socketIndex):
		return safebox.GetMallItemMetinSocket(globalSlot, socketIndex)

	## Slot Event
	def SelectEmptySlot(self, selectedSlotPos):
		if mouseModule.mouseController.isAttached():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MALL_CANNOT_INSERT)
			mouseModule.mouseController.DeattachObject()

	def SelectItemSlot(self, selectedSlotPos):
		selectedSlotPos = self.__LocalToGlobalSlot(selectedSlotPos)
		self.SelectGlobalItemSlot(selectedSlotPos)

	def SelectGlobalItemSlot(self, selectedSlotPos):
		if mouseModule.mouseController.isAttached():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MALL_CANNOT_INSERT)
			mouseModule.mouseController.DeattachObject()
		else:
			curCursorNum = app.GetCursor()
			selectedItemID = safebox.GetMallItemID(selectedSlotPos)
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_MALL, selectedSlotPos, selectedItemID)
			snd.PlaySound("sound/ui/pick.wav")

	def UseItemSlot(self, slotIndex):
		self.UseGlobalItemSlot(self.__LocalToGlobalSlot(slotIndex))

	def UseGlobalItemSlot(self, slotIndex):
		mouseModule.mouseController.DeattachObject()

	def __ShowToolTip(self, slotIndex):
		if self.tooltipItem:
			self.tooltipItem.SetMallItem(slotIndex)

	def OverInItem(self, slotIndex):
		slotIndex = self.__LocalToGlobalSlot(slotIndex)
		self.OverInGlobalItem(slotIndex)

	def OverInGlobalItem(self, slotIndex):
		self.__ShowToolTip(slotIndex)

	def OverOutItem(self):
		self.wndItem.SetUsableItem(False)
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	if app.WJ_ENABLE_TRADABLE_ICON:
		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

if __name__ == "__main__":
	import app
	import wndMgr
	import systemSetting
	import mouseModule
	import grp
	import ui
	import chr
	import background
	import player

	#wndMgr.SetOutlineFlag(True)

	app.SetMouseHandler(mouseModule.mouseController)
	app.SetHairColorEnable(True)
	wndMgr.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetScreenSize(systemSetting.GetWidth(), systemSetting.GetHeight())
	app.Create("METIN2 CLOSED BETA", systemSetting.GetWidth(), systemSetting.GetHeight(), 1)
	mouseModule.mouseController.Create()

	wnd = SafeboxWindow()
	wnd.ShowWindow(1)

	app.Loop()
