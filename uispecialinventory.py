import ui
import player
import mouseModule
import net
import app
import snd
import item
import mountcorebonus
import player
import chat
import grp
import uiScriptLocale
import uiRefine
import uiAttachMetin
import uiPickMoney
import uiSplitItem
import uiCommon
import uiPrivateShopBuilder
import localeInfo
import constInfo
import osfInfo
import ime
import wndMgr
import uiToolTip
import itemsplitplanner
import inventoryshortcutpolicy
import exchangequickadd
import safebox
import storagepresentation
if app.ENABLE_ACCE_COSTUME_SYSTEM:
	import acce

from _weakref import proxy

SEARCH_FIELD_UI_PATH = "d:/ymir work/ui/game/inventory/"

ITEM_MALL_BUTTON_ENABLE = True
ITEM_FLAG_APPLICABLE = 1 << 14
RETIRED_COSTUME_BUTTON_NUM = 5
CONSUMABLE_BUTTON_NUM = 8
SAFEBOX_BUTTON_NUM = 6
MALL_BUTTON_NUM = 7
SPECIAL_INVENTORY_WINDOW_WIDTH = 272
SPECIAL_INVENTORY_STORAGE_WIDTH = 176
SPECIAL_INVENTORY_GRID_WIDTH = player.SPECIAL_INVENTORY_PAGE_WIDTH
SPECIAL_INVENTORY_GRID_HEIGHT = player.SPECIAL_INVENTORY_PAGE_HEIGHT


def IsExpandedSafeboxLayout():
	try:
		return storagepresentation.GetLayout(safebox) == storagepresentation.EXPANDED_LAYOUT
	except (TypeError, ValueError):
		return False


class SpecialInventoryWindow(ui.ScriptWindow):
	USE_TYPE_TUPLE = (
		"USE_CLEAN_SOCKET",
		"USE_CHANGE_ATTRIBUTE",
		"USE_ADD_ATTRIBUTE",
		"USE_ADD_ATTRIBUTE2",
		"USE_ADD_ACCESSORY_SOCKET",
		"USE_PUT_INTO_ACCESSORY_SOCKET",
		"USE_PUT_INTO_BELT_SOCKET",
		"USE_PUT_INTO_RING_SOCKET",
		"USE_CHANGE_COSTUME_ATTR",
		"USE_RESET_COSTUME_ATTR"
	)

	questionDialog = None
	tooltipItem = None
	dlgPickMoney = None
	dlgSplitItem = None

	sellingSlotNumber = -1
	isLoaded = 0

	interface = None
	safebox = None
	mall = None
	toolTip = None
	inventoryPageIndex = 0
	inventoryType = 0

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		listAttachedAcceSlot = []

	if app.ENABLE_AURA_SYSTEM:
		listAttachedAuraSlot = []

	def __init__(self, wndInventory):
		ui.ScriptWindow.__init__(self)
		self.wndInventory = wndInventory
		self.__LoadWindow()
		self.wndInventory.SetSpecialWnd(self)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Show(self, category = 0):
		self.__LoadWindow()

		ui.ScriptWindow.Show(self)

		self.RefreshItemSlot()

	def BindInterfaceClass(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)

	def BindSafeboxAndMallClass(self, safebox, mall):
		self.safebox = proxy(safebox)
		self.mall = proxy(mall)

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "SpecialInventoryWindow.py")
		except:
			import exception
			exception.Abort("SpecialInventoryWindow.LoadWindow.LoadObject")

		try:
			wndItem = self.GetChild("ItemSlot")
			self.board = self.GetChild("board")
			self.titleBar = self.GetChild("TitleBar")
			self.categoryBackground = self.GetChild("backGroundPic")
			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			self.titleName = self.GetChild("TitleName")
			if app.ENABLE_SORT_INVENTORY:
				self.sortInventoryButton = self.GetChild2("SortInventoryButton")

			self.SkillBookButton = self.GetChild("SkillBookButton")
			self.UpgradeItemsButton = self.GetChild("UpgradeItemsButton")
			self.stoneButton = self.GetChild("StoneButton")
			self.GiftBoxButton = self.GetChild("GiftBoxButton")
			self.SwitchButton = self.GetChild("SwitchButton")
			self.ConsumableButton = self.GetChild("ConsumableButton")
			self.SafeboxButton = self.GetChild("SafeboxButton")
			self.MallButton = self.GetChild("MallButton")

			self.inventoryTab = [
				self.GetChild("Inventory_Tab_%02d" % page)
				for page in range(1, player.SPECIAL_INVENTORY_PAGE_COUNT + 1)
			]

			self.dlgQuestion = uiCommon.QuestionDialog2()
			self.dlgQuestion.Close()

			if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
				self.listHighlightedSlot = []

			self.loading_image = self.GetChild("loading_image")
			self.loading_image.Hide()
		except:
			import exception
			exception.Abort("SpecialInventoryWindow.LoadWindow.BindObject")

		## Item
		wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		wndItem.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndItem.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		self.SkillBookButton.SetEvent(lambda arg=0: self.SetInventoryType(arg))
		self.UpgradeItemsButton.SetEvent(lambda arg=1: self.SetInventoryType(arg))
		self.stoneButton.SetEvent(lambda arg=2: self.SetInventoryType(arg))
		self.GiftBoxButton.SetEvent(lambda arg=3: self.SetInventoryType(arg))
		self.SwitchButton.SetEvent(lambda arg=4: self.SetInventoryType(arg))
		self.ConsumableButton.SetEvent(lambda arg=CONSUMABLE_BUTTON_NUM: self.SetInventoryType(arg))
		self.SafeboxButton.SetEvent(lambda arg=6: self.SetInventoryType(arg))
		self.MallButton.SetEvent(lambda arg=7: self.SetInventoryType(arg))
		self.SkillBookButton.Down()

		## PickMoneyDialog
		dlgPickMoney = uiPickMoney.PickMoneyDialog()
		dlgPickMoney.LoadDialog()
		dlgPickMoney.Hide()

		dlgSplitItem = uiSplitItem.SplitItemDialog()
		dlgSplitItem.LoadDialog()
		dlgSplitItem.Hide()

		## AttachMetinDialog
		self.attachMetinDialog = uiAttachMetin.AttachMetinDialog()
		self.attachMetinDialog.Hide()

		for inven_index in range(player.SPECIAL_INVENTORY_PAGE_COUNT):
			self.inventoryTab[inven_index].SetEvent(lambda arg=inven_index: self.SetInventoryPage(arg))
		self.inventoryTab[0].Down()

		self.wndItem = wndItem
		self.dlgPickMoney = dlgPickMoney
		self.dlgSplitItem = dlgSplitItem

		if app.ENABLE_SEARCH_FIELD:
			import skill
			self._skillModuleSearch = skill
			_sx, _sy = wndItem.GetLocalPosition()
			board = self.board
			self.wndSearchBarBase = ui.ImageBox()
			self.wndSearchBarBase.SetParent(board)
			self.wndSearchBarBase.SetPosition((SPECIAL_INVENTORY_WINDOW_WIDTH - 160) // 2, 33)
			self.wndSearchBarBase.LoadImage(SEARCH_FIELD_UI_PATH + "btn-base_storage.png")
			self.wndSearchBarBase.Show()
			self.wndNameSlot = ui.ImageBox()
			self.wndNameSlot.SetParent(self.wndSearchBarBase)
			self.wndNameSlot.SetPosition(52, 4)
			self.wndNameSlot.LoadImage(SEARCH_FIELD_UI_PATH + "input.png")
			self.wndNameSlot.Show()
			self.btnSearchStack = ui.Button()
			self.btnSearchStack.SetParent(self.wndSearchBarBase)
			self.btnSearchStack.SetPosition(3, 4)
			self.btnSearchStack.SetUpVisual(SEARCH_FIELD_UI_PATH + "btn-stack-1.png")
			self.btnSearchStack.SetOverVisual(SEARCH_FIELD_UI_PATH + "btn-stack-2.png")
			self.btnSearchStack.SetDownVisual(SEARCH_FIELD_UI_PATH + "btn-stack-3.png")
			self.btnSearchStack.SetToolTipText(getattr(localeInfo, "INVENTORY_STACK_TOOLTIP", "Stack"), 0, -23)
			if app.ENABLE_SORT_INVENTORY:
				self.btnSearchStack.SetEvent(ui.__mem_func__(self.__OnSearchBarStackClick))
				self.btnSearchStack.Show()
			else:
				self.btnSearchStack.Hide()
			self.btnSearchSort = ui.Button()
			self.btnSearchSort.SetParent(self.wndSearchBarBase)
			self.btnSearchSort.SetPosition(27, 4)
			self.btnSearchSort.SetUpVisual(SEARCH_FIELD_UI_PATH + "btn-sort-1.png")
			self.btnSearchSort.SetOverVisual(SEARCH_FIELD_UI_PATH + "btn-sort-2.png")
			self.btnSearchSort.SetDownVisual(SEARCH_FIELD_UI_PATH + "btn-sort-3.png")
			self.btnSearchSort.SetToolTipText(uiScriptLocale.INVENTORY_ITEM_SORT_TOOLTIP, 0, -23)
			if app.ENABLE_SORT_INVENTORY:
				self.btnSearchSort.SetEvent(ui.__mem_func__(self.__OnSearchBarSortClick))
				self.btnSearchSort.Show()
			else:
				self.btnSearchSort.Hide()
			self.wndItemSRC = ui.GridSlotWindow()
			self.wndItemSRC.SetParent(board)
			self.wndItemSRC.SetPosition(_sx, _sy)
			self.wndItemSRC.ArrangeSlot(0, player.SPECIAL_INVENTORY_PAGE_WIDTH, player.SPECIAL_INVENTORY_PAGE_HEIGHT, 32, 32, 0, 0)
			self.wndItemSRC.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
			self.wndItemSRC.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
			self.wndItemSRC.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
			self.wndItemSRC.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
			self.wndItemSRC.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
			self.wndItemSRC.SetOverInItemEvent(ui.__mem_func__(self.__OverInItemSpecialSearchResult))
			self.wndItemSRC.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			self.wndItemSRC.dictItems = {}
			self.wndItemSRC.Hide()
			self._invSearchGridAnchor = {}
			self.wndSearchEdit = ui.EditLine()
			self.wndSearchEdit.SetParent(self.wndNameSlot)
			self.wndSearchEdit.SetPosition(6, 4)
			self.wndSearchEdit.SetSize(self.wndNameSlot.GetWidth() - 2, self.wndNameSlot.GetHeight() - 2)
			self.wndSearchEdit.SetMax(55)
			self.wndSearchEdit.SetInfoMessage(localeInfo.ITEMSHOP_ITEMSEARCH_DEFAULT_TEXT)
			self.wndSearchEdit.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateSpecialSearchField)
			self.wndSearchEdit.SetEscapeEvent(ui.__mem_func__(self.__OnSearchEditEscapeSpecial))
			self.wndSearchEdit.KillFocus()
			self.wndSearchEdit.Show()
		else:
			self.wndItemSRC = None
			self.wndSearchEdit = None
			self.wndSearchBarBase = None
			self.wndNameSlot = None
			self.btnSearchStack = None
			self.btnSearchSort = None
			self._skillModuleSearch = None
			self._invSearchGridAnchor = None

		if app.ENABLE_SORT_INVENTORY:
			if self.sortInventoryButton:
				self.sortInventoryButton.SetEvent(ui.__mem_func__(self.SortInventoryButton))

		## Refresh
		self.SetInventoryType(0)
		self.SetInventoryPage(0)

		self.RefreshItemSlot()

	def Destroy(self):
		self.ClearDictionary()

		self.dlgPickMoney.Destroy()
		self.dlgPickMoney = 0
		self.dlgSplitItem.Destroy()
		self.dlgSplitItem = 0

		self.attachMetinDialog.Destroy()
		self.attachMetinDialog = 0

		self.tooltipItem = None
		self.wndItem = 0
		self.board = None
		self.titleBar = None
		self.titleName = None
		self.categoryBackground = None
		self.dlgPickMoney = 0
		self.dlgSplitItem = 0
		self.questionDialog = None
		self.interface = None

		self.safebox = None
		self.mall = None
		self.toolTip = None

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			self.listAttachedAcceSlot = []

		if app.ENABLE_AURA_SYSTEM:
			self.listAttachedAuraSlot = []

		self.inventoryTab = []
		self.inventoryPageIndex = 0

		if app.ENABLE_SEARCH_FIELD:
			self.wndItemSRC = None
			self.wndSearchEdit = None
			self.wndNameSlot = None
			self.wndSearchBarBase = None
			self.btnSearchStack = None
			self.btnSearchSort = None
			self._skillModuleSearch = None
			self._invSearchGridAnchor = None

	def Hide(self):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS():
			self.OnCloseQuestionDialog()
			return

		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()

		if self.dlgPickMoney:
			self.dlgPickMoney.Close()
		if self.dlgSplitItem:
			self.dlgSplitItem.Close()

		wndMgr.Hide(self.hWnd)

	def Close(self):
		if app.ENABLE_SEARCH_FIELD:
			if self.wndSearchEdit and self.wndSearchEdit.IsFocus():
				self.wndSearchEdit.KillFocus()
		if self.GetInventoryType() == SAFEBOX_BUTTON_NUM:
			self.__CloseSafebox()
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()
			self.SetInventoryType(0)
		elif self.GetInventoryType() == MALL_BUTTON_NUM:
			self.__CloseMall()
			self.SetInventoryType(0)
		self.Hide()

	def GetMallButtonIDX(self):
		return MALL_BUTTON_NUM

	def SetInventoryPage(self, page):
		if page < 0 or page >= len(self.inventoryTab):
			return
		self.inventoryPageIndex = page

		for index in range(len(self.inventoryTab)):
			if index == page:
				self.inventoryTab[index].Down()
				continue
			self.inventoryTab[index].SetUp()

		provider = self.__GetActiveStorageProvider()
		if self.IsExpandedStorageProvider() and provider:
			provider.SelectPage(page)
		else:
			self.RefreshBagSlotWindow()

	def __ApplyInventoryLayout(self, inventory_type):
		target_width = SPECIAL_INVENTORY_WINDOW_WIDTH
		if inventory_type in (SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM) and not IsExpandedSafeboxLayout():
			target_width = SPECIAL_INVENTORY_STORAGE_WIDTH

		current_width = self.GetWidth()
		if current_width == target_width:
			return

		current_x, current_y = self.GetLocalPosition()
		window_height = self.GetHeight()
		board_height = self.board.GetHeight()

		# Keep the window docked by its right edge while switching between the
		# 8x8 special inventory and the legacy 5x9 storage grids.
		self.SetPosition(current_x + current_width - target_width, current_y)
		self.SetSize(target_width, window_height)
		self.board.SetSize(target_width, board_height)

		title_x, _ = self.titleBar.GetLocalPosition()
		title_width = target_width - title_x - 7
		self.titleBar.SetWidth(title_width)
		_, title_y = self.titleName.GetLocalPosition()
		self.titleName.SetPosition(0, title_y)

		category_x = (target_width - self.categoryBackground.GetWidth()) // 2
		_, category_y = self.categoryBackground.GetLocalPosition()
		self.categoryBackground.SetPosition(category_x, category_y)

		if app.ENABLE_SEARCH_FIELD and self.wndSearchBarBase:
			search_x = (target_width - self.wndSearchBarBase.GetWidth()) // 2
			_, search_y = self.wndSearchBarBase.GetLocalPosition()
			self.wndSearchBarBase.SetPosition(search_x, search_y)

		self.UpdateRect()

	def SetInventoryType(self, type, canPassSafeBoxAndMallEvent = False):
		type = int(type)
		if type == RETIRED_COSTUME_BUTTON_NUM:
			type = 0
		if type not in (0, 1, 2, 3, 4, 8, SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM):
			type = 0

		if self.dlgSplitItem:
			self.dlgSplitItem.Close()

		if self.GetInventoryType() == SAFEBOX_BUTTON_NUM:
			self.__CloseSafebox()
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()
		elif self.GetInventoryType() == MALL_BUTTON_NUM:
			self.__CloseMall()

		self.__ApplyInventoryLayout(type)
		
		self.inventoryType = type
		
		m_buttons = {
			0: (self.SkillBookButton, localeInfo.SPECIAL_INVENTORY_SKILL_BOOK),
			1: (self.UpgradeItemsButton, localeInfo.SPECIAL_INVENTORY_MATERIAL),
			2: (self.stoneButton, localeInfo.SPECIAL_INVENTORY_STONE),
			3: (self.GiftBoxButton, localeInfo.SPECIAL_INVENTORY_CHEST),
			4: (self.SwitchButton, uiScriptLocale.SPECIAL_INVENTORY_SWITCH),
			CONSUMABLE_BUTTON_NUM: (self.ConsumableButton, uiScriptLocale.SPECIAL_INVENTORY_CONSUMABLE),
			SAFEBOX_BUTTON_NUM: (
				self.SafeboxButton, uiScriptLocale.SPECIAL_INVENTORY_SAFEBOX),
			MALL_BUTTON_NUM: (
				self.MallButton, uiScriptLocale.SPECIAL_INVENTORY_MALL),
		}
		
		for obj, _ in m_buttons.values():
			obj.SetUp()
		obj, title = m_buttons[type]
		obj.Down()
		self.titleName.SetText(title)
	
		if not canPassSafeBoxAndMallEvent:
			if type == SAFEBOX_BUTTON_NUM:
				#self.sortInventoryButton.Disable()
				self.__OpenSafebox()
			elif type == MALL_BUTTON_NUM:
				#self.sortInventoryButton.Disable()
				self.__OpenMall()
			else:
				#self.sortInventoryButton.Enable()
				pass
		
		if self.CanRefreshSpecialInventoryPage() or self.IsExpandedStorageProvider():
			self.SetInventoryPage(0)

		if app.ENABLE_SEARCH_FIELD:
			self.__ApplySpecialInventorySearchVisibility()

	if app.ENABLE_SORT_INVENTORY:
		def StackInventoryButton(self):
			if self.inventoryType not in (
				0, 1, 2, 3, 4, 8, SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM
			):
				return
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(getattr(localeInfo, "SPECIAL_INVENTORY_DO_YOU_STACK", "Do you really want to stack matching special inventory items?"))
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnStackInventoryItems))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
			self.questionDialog.Open()

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

		def OnStackInventoryItems(self):
			if None == self.questionDialog:
				return

			net.SendChatPacket("/stack_special_inventory %d" % self.inventoryType)
			snd.PlaySound("sound/ui/pickup_item_in_inventory.wav")

			self.OnCloseQuestionDialog()

		def SortInventoryButton(self):
			if self.inventoryType not in (
				0, 1, 2, 3, 4, 8, SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM
			):
				return
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(localeInfo.SPECIAL_INVENTORY_DO_YOU_SORT)
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnSortInventoryItems))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
			self.questionDialog.Open()

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

		def OnSortInventoryItems(self):
			if None == self.questionDialog:
				return

			net.SendChatPacket("/sort_special_inventory %d" % self.inventoryType)
			snd.PlaySound("sound/ui/pickup_item_in_inventory.wav")

			self.OnCloseQuestionDialog()

		def __OnSearchBarSortClick(self):
			self.SortInventoryButton()

		def __OnSearchBarStackClick(self):
			self.StackInventoryButton()

	def OnPickItem(self, count):
		itemSlotIndex = self.dlgSplitItem.itemGlobalSlotIndex
		if self.dlgSplitItem.IsSplitAllChecked():
			self.__SplitAllItems(itemSlotIndex, count)
			return

		selectedItemVNum = player.GetItemIndex(itemSlotIndex)

		if self.inventoryType == 0:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_SKILL_BOOK_INVENTORY, itemSlotIndex, selectedItemVNum, count)
		elif self.inventoryType == 1:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY, itemSlotIndex, selectedItemVNum, count)
		elif self.inventoryType == 2:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_STONE_INVENTORY, itemSlotIndex, selectedItemVNum, count)
		elif self.inventoryType == 3:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_GIFT_BOX_INVENTORY, itemSlotIndex, selectedItemVNum, count)
		elif self.inventoryType == 4:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_SWITCH_INVENTORY, itemSlotIndex, selectedItemVNum, count)
		elif self.inventoryType == CONSUMABLE_BUTTON_NUM:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_CONSUMABLE_INVENTORY, itemSlotIndex, selectedItemVNum, count)
		elif self.inventoryType == 5:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_COSTUME_INVENTORY, itemSlotIndex, selectedItemVNum, count)

	def __SpecialSplitItemDimensionsAt(self, cell):
		itemVnum = player.GetItemIndex(cell)
		if not itemVnum:
			return None

		item.SelectItem(itemVnum)
		return item.GetItemSize()

	def __SplitAllItems(self, itemSlotIndex, splitCount):
		if self.inventoryType > 5:
			return

		sourceCount = player.GetItemCount(itemSlotIndex)
		itemVnum = player.GetItemIndex(itemSlotIndex)
		if not itemVnum:
			return

		item.SelectItem(itemVnum)
		itemWidth, itemHeight = item.GetItemSize()
		categoryStart = (
			self.__InventoryLocalSlotPosToGlobalSlotPos(0)
			- self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE
		)
		pageStarts = tuple(
			categoryStart + page * player.SPECIAL_INVENTORY_PAGE_SIZE
			for page in range(player.SPECIAL_INVENTORY_PAGE_COUNT)
		)
		occupied = itemsplitplanner.mark_occupied_cells(
			pageStarts,
			player.SPECIAL_INVENTORY_PAGE_WIDTH,
			player.SPECIAL_INVENTORY_PAGE_HEIGHT,
			self.__SpecialSplitItemDimensionsAt
		)
		moves, requiredMoves = itemsplitplanner.plan_split_moves(
			sourceCount, splitCount, itemSlotIndex, pageStarts,
			player.SPECIAL_INVENTORY_PAGE_WIDTH,
			player.SPECIAL_INVENTORY_PAGE_HEIGHT,
			itemWidth, itemHeight, occupied
		)

		for destination, count in moves:
			net.SendItemMovePacket(
				player.INVENTORY, itemSlotIndex,
				player.INVENTORY, destination, count
			)

		if requiredMoves and not moves:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.INVENTORY_SPLIT_NO_SPACE)
		elif len(moves) < requiredMoves:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.INVENTORY_SPLIT_PARTIAL)

	def __InventoryLocalSlotPosToGlobalSlotPos(self, local):
		if self.inventoryType == 0:
			return self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.SKILL_BOOK_INVENTORY_SLOT_START
		elif self.inventoryType == 1:
			return self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.UPGRADE_ITEMS_INVENTORY_SLOT_START
		elif self.inventoryType == 2:
			return self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.STONE_INVENTORY_SLOT_START
		elif self.inventoryType == 3:
			return self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.GIFT_BOX_INVENTORY_SLOT_START
		elif self.inventoryType == 4:
			return self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.SWITCH_INVENTORY_SLOT_START
		elif self.inventoryType == CONSUMABLE_BUTTON_NUM:
			return self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.CONSUMABLE_INVENTORY_SLOT_START
		elif self.inventoryType == 5:
			return self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.COSTUME_INVENTORY_SLOT_START

	def __SpecialInventoryGlobalSlot(self, page, local):
		if self.inventoryType == 0:
			return page * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.SKILL_BOOK_INVENTORY_SLOT_START
		elif self.inventoryType == 1:
			return page * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.UPGRADE_ITEMS_INVENTORY_SLOT_START
		elif self.inventoryType == 2:
			return page * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.STONE_INVENTORY_SLOT_START
		elif self.inventoryType == 3:
			return page * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.GIFT_BOX_INVENTORY_SLOT_START
		elif self.inventoryType == 4:
			return page * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.SWITCH_INVENTORY_SLOT_START
		elif self.inventoryType == CONSUMABLE_BUTTON_NUM:
			return page * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.CONSUMABLE_INVENTORY_SLOT_START
		elif self.inventoryType == 5:
			return page * player.SPECIAL_INVENTORY_PAGE_SIZE + local + item.COSTUME_INVENTORY_SLOT_START
		return -1

	def __ApplySpecialInventorySearchVisibility(self):
		if not app.ENABLE_SEARCH_FIELD or not self.wndSearchBarBase:
			return
		if not self.CanRefreshSpecialInventoryPage() and not self.IsExpandedStorageProvider():
			self.wndSearchBarBase.Hide()
			if self.wndItemSRC:
				self.wndItemSRC.Hide()
			if self.wndSearchEdit:
				self.wndSearchEdit.KillFocus()
				self.wndSearchEdit.SetText("")
			return
		self.wndSearchBarBase.Show()
		self.__RefreshSpecialInventorySearchGrid()

	def __ClearSpecialInventorySearchGrid(self):
		if not self.wndItemSRC:
			return
		for x in range(player.SPECIAL_INVENTORY_PAGE_SIZE):
			self.wndItemSRC.ClearSlot(x)
		self.wndItemSRC.RefreshSlot()
		self._invSearchGridAnchor = {}

	def __SpecialInvSearchCanPlace(self, top_left, width, height, used_cells):
		col = top_left % SPECIAL_INVENTORY_GRID_WIDTH
		row = top_left // SPECIAL_INVENTORY_GRID_WIDTH
		if col + width > SPECIAL_INVENTORY_GRID_WIDTH or row + height > SPECIAL_INVENTORY_GRID_HEIGHT:
			return False
		for dy in range(height):
			for dx in range(width):
				idx = (row + dy) * SPECIAL_INVENTORY_GRID_WIDTH + (col + dx)
				if idx in used_cells:
					return False
		return True

	def __SpecialInvSearchMarkArea(self, top_left, width, height, used_cells, anchor_key):
		col = top_left % SPECIAL_INVENTORY_GRID_WIDTH
		row = top_left // SPECIAL_INVENTORY_GRID_WIDTH
		for dy in range(height):
			for dx in range(width):
				idx = (row + dy) * SPECIAL_INVENTORY_GRID_WIDTH + (col + dx)
				used_cells.add(idx)
				self._invSearchGridAnchor[idx] = anchor_key

	def __SpecialInvSearchFindEmpty(self, width, height, used_cells):
		for pos in range(player.SPECIAL_INVENTORY_PAGE_SIZE):
			if self.__SpecialInvSearchCanPlace(pos, width, height, used_cells):
				return pos
		return -1

	def __SpecialInventorySearchResolveAnchor(self, grid_slot_index):
		if self._invSearchGridAnchor == None:
			return grid_slot_index
		return self._invSearchGridAnchor.get(grid_slot_index, grid_slot_index)

	def __RefreshSpecialInventorySearchGrid(self):
		if not app.ENABLE_SEARCH_FIELD or not self.wndItemSRC or not self.wndSearchEdit or not self._skillModuleSearch:
			return
		if not self.CanRefreshSpecialInventoryPage() and not self.IsExpandedStorageProvider():
			return
		text = self.wndSearchEdit.GetText().strip()
		self.wndItemSRC.dictItems = {}
		self.__ClearSpecialInventorySearchGrid()
		if not text:
			self.wndItemSRC.Hide()
			provider = self.__GetActiveStorageProvider()
			if self.IsExpandedStorageProvider() and provider:
				self.wndItem.Hide()
				provider.Show()
			elif self.wndItem:
				self.wndItem.Show()
			return
		self.wndItemSRC.Show()
		if self.wndItem:
			self.wndItem.Hide()
		skill = self._skillModuleSearch
		query_lower = text.lower()
		used_cells = set()
		provider = self.__GetActiveStorageProvider()
		if self.IsExpandedStorageProvider() and provider:
			provider.Hide()
		if self.IsExpandedStorageProvider() and provider:
			slotWinType = self.inventoryType
		else:
			slotWinType = self.PageToInventoryType()
		grid_full = False
		if self.IsExpandedStorageProvider() and provider:
			searchItems = provider.IterSearchItems()
		else:
			searchItems = []
			for page in range(player.SPECIAL_INVENTORY_PAGE_COUNT):
				for local in range(player.SPECIAL_INVENTORY_PAGE_SIZE):
					slotNumber = self.__SpecialInventoryGlobalSlot(page, local)
					if slotNumber >= 0:
						searchItems.append((
							slotNumber,
							player.GetItemIndex(slotNumber),
							player.GetItemCount(slotNumber)
						))

		for slotNumber, itemVNum, itemCount in searchItems:
			if itemCount == 0:
				continue
			elif 1 == itemCount:
				itemCount = 0
			item.SelectItem(itemVNum)
			stName = item.GetItemName()
			if itemVNum == 50300:
				if self.IsExpandedStorageProvider() and provider:
					skillVnum = provider.GetSearchItemSocket(slotNumber, 0)
				else:
					skillVnum = player.GetItemMetinSocket(slotNumber, 0)
				stName = skill.GetSkillName(skillVnum)
			w, h = item.GetItemSize()
			if w <= 0 or h <= 0:
				continue
			if query_lower not in stName.lower():
				continue
			dest = self.__SpecialInvSearchFindEmpty(w, h, used_cells)
			if dest == -1:
				grid_full = True
				break
			self.__SpecialInvSearchMarkArea(dest, w, h, used_cells, dest)
			self.wndItemSRC.SetItemSlot(dest, itemVNum, itemCount)
			if not self.IsExpandedStorageProvider() and app.ENABLE_EXTENDED_BLEND_AFFECT and osfInfo.IS_DEW_POTION(itemVNum):
				if player.GetItemMetinSocket(slotNumber, 3):
					self.wndItemSRC.ActivateSlotOld(dest)
			self.wndItemSRC.dictItems[dest] = (slotWinType, slotNumber)
			if grid_full:
				break
		self.wndItemSRC.RefreshSlot()

	def __OverInItemSpecialSearchResult(self, slotIndex):
		if self.wndItemSRC:
			anchor = self.__SpecialInventorySearchResolveAnchor(slotIndex)
			if anchor in self.wndItemSRC.dictItems:
				resultType, globalSlot = self.wndItemSRC.dictItems[anchor]
				provider = self.__GetActiveStorageProvider()
				if resultType in (SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM):
					if (
						resultType == self.inventoryType and
						self.IsExpandedStorageProvider() and provider
					):
						provider.OverInGlobalItem(globalSlot)
					else:
						self.OverOutItem()
				else:
					self.ShowToolTip(globalSlot)
				return
		self.OverOutItem()

	def __OnValueUpdateSpecialSearchField(self):
		if not self.wndSearchEdit:
			return
		if not self.IsShow():
			return
		if self.wndSearchEdit.IsFocus():
			ui.EditLine.OnIMEUpdate(self.wndSearchEdit)
		self.__RefreshSpecialInventorySearchGrid()

	def __OnSearchEditEscapeSpecial(self):
		self.Close()
		return True

	if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
		def DisableMultipleEffect(self):
			if not self.wndItem:
				return
	
			getItemVNum = player.GetItemIndex
			getItemCount = player.GetItemCount
			setItemVNum = self.wndItem.SetItemSlot
	
			for i in range(self.wndItem.GetSlotCount()):
				self.wndItem.DeactivateSlot(i)
	
			if app.WJ_ENABLE_TRADABLE_ICON:
				if self.interface:
					onTopWindow = self.interface.GetOnTopWindow()
	
			for i in range(player.SPECIAL_INVENTORY_PAGE_SIZE):
				slotNumber = self.__InventoryLocalSlotPosToGlobalSlotPos(i)
	
				itemCount = getItemCount(slotNumber)
				if 0 == itemCount:
					self.wndItem.ClearSlot(i)
					continue
				elif 1 == itemCount:
					itemCount = 0
	
				itemVnum = getItemVNum(slotNumber)
				setItemVNum(i, itemVnum, itemCount)
				
				if slotNumber in osfInfo.MULTIPLE_LIST:
					self.wndItem.DeactivateSlot(i)
					continue

	def RefreshBagSlotWindow(self):
		if not self.wndItem:
			return

		if self.CanRefreshSpecialInventoryPage() is False:
			return

		getItemVNum = player.GetItemIndex
		getItemCount = player.GetItemCount
		setItemVNum = self.wndItem.SetItemSlot

		for i in range(self.wndItem.GetSlotCount()):
			self.wndItem.DeactivateSlot(i)

			if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
				self.wndItem.DeactivateSlot(i)

		onTopWindow = None
		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				onTopWindow = self.interface.GetOnTopWindow()

		for i in range(player.SPECIAL_INVENTORY_PAGE_SIZE):
			slotNumber = self.__InventoryLocalSlotPosToGlobalSlotPos(i)

			itemCount = getItemCount(slotNumber)
			if 0 == itemCount:
				if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
					if slotNumber in osfInfo.MULTIPLE_LIST:
						osfInfo.MULTIPLE_LIST.remove(int(slotNumber))
						if self.wndInventory and self.wndInventory.wndMultiple:
							self.wndInventory.wndMultiple.UpdateItemCount(int(slotNumber), 2)
							self.wndInventory.wndMultiple.UpdatePrice(int(slotNumber), 2)
				self.wndItem.ClearSlot(i)
				continue
			elif 1 == itemCount:
				itemCount = 0

			itemVnum = getItemVNum(slotNumber)
			setItemVNum(i, itemVnum, itemCount)

			if app.ENABLE_EXTENDED_BLEND_AFFECT and osfInfo.IS_DEW_POTION(itemVnum):
				if player.GetItemMetinSocket(slotNumber, 3):
					self.wndItem.ActivateSlotOld(i)

			if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
				if slotNumber in osfInfo.MULTIPLE_LIST:
					r, g, b = (255.00 / 255.0), (255.00 / 255.0), (0.00 / 255.0)
					self.wndItem.ActivateSlot(i)
					continue

					self.OwnerSlot.EnableSlotCoverImage(i, False)

			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				AcceSlotNumberChecked = 0
				for j in range(acce.WINDOW_MAX_MATERIALS):
					(isHere, iCell) = acce.GetAttachedItem(j)

					if isHere:
						if iCell == slotNumber:
							self.wndItem.ActivateSlot(i)
							if not slotNumber in self.listAttachedAcceSlot:
								self.listAttachedAcceSlot.append(slotNumber)

							AcceSlotNumberChecked = 1
					else:
						if slotNumber in self.listAttachedAcceSlot and not AcceSlotNumberChecked:
							self.wndItem.DeactivateSlot(i)
							self.listAttachedAcceSlot.remove(slotNumber)

			if app.ENABLE_AURA_SYSTEM:
				AuraSlotNumberChecked = 0
				for j in range(2):
					if j in osfInfo.AURA_ATTACHED_LIST_SLOT and osfInfo.AURA_ATTACHED_LIST_SLOT[j] == slotNumber:
						self.wndItem.ActivateSlot(i)
						if not slotNumber in self.listAttachedAuraSlot:
							self.listAttachedAuraSlot.append(slotNumber)

						AuraSlotNumberChecked = 1
					else:
						if slotNumber in self.listAttachedAuraSlot and not AuraSlotNumberChecked:
							self.wndItem.DeactivateSlot(i)
							self.listAttachedAuraSlot.remove(slotNumber)

			if app.WJ_ENABLE_TRADABLE_ICON:
				if itemVnum and self.interface and onTopWindow:
					if self.interface.MarkUnusableInvenSlotOnTopWnd(onTopWindow, slotNumber):
						self.wndItem.SetUnusableSlotOnTopWnd(i)
					else:
						self.wndItem.SetUsableSlotOnTopWnd(i)
				else:
					self.wndItem.SetUsableSlotOnTopWnd(i)

		if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
			self.__HighlightSlot_Refresh()

		self.wndItem.RefreshSlot()

		if app.ENABLE_SEARCH_FIELD:
			if self.wndSearchEdit and self.wndSearchEdit.GetText():
				self.__RefreshSpecialInventorySearchGrid()

	def RefreshItemSlot(self):
		if self.CanRefreshSpecialInventoryPage() is False:
			return
		self.RefreshBagSlotWindow()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SellItem(self):
		if self.sellingSlotitemIndex == player.GetItemIndex(self.sellingSlotNumber):
			if self.sellingSlotitemCount == player.GetItemCount(self.sellingSlotNumber):
				net.SendShopSellPacketNew(self.sellingSlotNumber, self.questionDialog.count, player.INVENTORY)
				snd.PlaySound("sound/ui/money.wav")

		self.OnCloseQuestionDialog()

	def OnDetachMetinFromItem(self):
		if None == self.questionDialog:
			return

		self.__SendUseItemToItemPacket(self.questionDialog.sourcePos, self.questionDialog.targetPos)
		self.OnCloseQuestionDialog()

	def OnCloseQuestionDialog(self):
		if not self.questionDialog:
			return

		self.questionDialog.Close()
		self.questionDialog = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def SelectEmptySlot(self, selectedSlotPos):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		if app.ENABLE_SEARCH_FIELD:
			if self.wndItemSRC and self.wndItemSRC.IsShow() and self.wndSearchEdit and self.wndSearchEdit.GetText():
				return

		selectedSlotPos = self.__InventoryLocalSlotPosToGlobalSlotPos(selectedSlotPos)

		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedItemCount = mouseModule.mouseController.GetAttachedItemCount()
			attachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()

			if player.SLOT_TYPE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_STONE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SWITCH_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_COSTUME_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_CONSUMABLE_INVENTORY == attachedSlotType:

				itemCount = player.GetItemCount(attachedSlotPos)
				attachedCount = mouseModule.mouseController.GetAttachedItemCount()

				self.__SendMoveItemPacket(attachedSlotPos, selectedSlotPos, attachedCount)

				if item.IsRefineScroll(attachedItemIndex):
					self.interface.SetUseItemMode(False)

			elif player.SLOT_TYPE_PRIVATE_SHOP == attachedSlotType:
				mouseModule.mouseController.RunCallBack("INVENTORY")

			elif player.SLOT_TYPE_SHOP == attachedSlotType:
				net.SendShopBuyPacket(attachedSlotPos)

			elif player.SLOT_TYPE_SAFEBOX == attachedSlotType:
				if player.ITEM_MONEY == attachedItemIndex:
					net.SendSafeboxWithdrawMoneyPacket(mouseModule.mouseController.GetAttachedItemCount())
					snd.PlaySound("sound/ui/money.wav")
				else:
					net.SendSafeboxCheckoutPacket(attachedSlotPos, selectedSlotPos)

			elif player.SLOT_TYPE_MALL == attachedSlotType:
				net.SendMallCheckoutPacket(attachedSlotPos, selectedSlotPos)

			mouseModule.mouseController.DeattachObject()

	def SelectItemSlot(self, itemSlotIndex):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		if app.ENABLE_SEARCH_FIELD:
			if self.wndItemSRC and self.wndItemSRC.IsShow() and self.wndSearchEdit and self.wndSearchEdit.GetText():
				anchor = self.__SpecialInventorySearchResolveAnchor(itemSlotIndex)
				if anchor in self.wndItemSRC.dictItems:
					resultType, itemSlotIndex = self.wndItemSRC.dictItems[anchor]
					provider = self.__GetActiveStorageProvider()
					if resultType in (SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM):
						if (
							resultType == self.inventoryType and
							self.IsExpandedStorageProvider() and provider
						):
							provider.SelectGlobalItemSlot(itemSlotIndex)
						return
				else:
					itemSlotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(itemSlotIndex)
			else:
				itemSlotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(itemSlotIndex)
		else:
			itemSlotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(itemSlotIndex)

		isAltPressed = app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT)
		isShiftPressed = app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT)
		isCtrlPressed = app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)
		leftClickAction = inventoryshortcutpolicy.ResolveLeftClick(
			isAltPressed, isShiftPressed, isCtrlPressed
		)

		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedItemVID = mouseModule.mouseController.GetAttachedItemIndex()

			if player.SLOT_TYPE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_STONE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SWITCH_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_COSTUME_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_CONSUMABLE_INVENTORY == attachedSlotType:

				self.__DropSrcItemToDestItemInInventory(attachedItemVID, attachedSlotPos, itemSlotIndex)

			mouseModule.mouseController.DeattachObject()
		else:
			curCursorNum = app.GetCursor()

			if app.SELL == curCursorNum:
				self.__SellItem(itemSlotIndex)

			elif app.BUY == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_BUY_INFO)

			elif leftClickAction == inventoryshortcutpolicy.ACTION_STACK:
				if 0 <= self.inventoryType <= 4 or self.inventoryType == 8:
					net.SendChatPacket("/stack_special_inventory %d %d" % (self.inventoryType, itemSlotIndex))
				return

			elif leftClickAction == inventoryshortcutpolicy.ACTION_LINK:
				if app.ENABLE_REFINE_ELEMENT_SYSTEM:
					link = constInfo.GetItemLinkEx(itemSlotIndex)
				else:
					link = player.GetItemLink(itemSlotIndex)
				ime.PasteString(link)

			elif leftClickAction == inventoryshortcutpolicy.ACTION_SPLIT:
				itemCount = player.GetItemCount(itemSlotIndex)

				if itemCount > 1 and self.inventoryType <= 5:
					self.dlgSplitItem.SetTitleName(localeInfo.PICK_ITEM_TITLE)
					self.dlgSplitItem.SetAcceptEvent(ui.__mem_func__(self.OnPickItem))
					self.dlgSplitItem.Open(itemCount)
					self.dlgSplitItem.itemGlobalSlotIndex = itemSlotIndex

			elif leftClickAction == inventoryshortcutpolicy.ACTION_MARKET:
				if 0 <= self.inventoryType <= 5:
					itemVnum = player.GetItemIndex(itemSlotIndex)
					if itemVnum > 0 and getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
						self.interface.SearchVirtualMarketInventoryItem(itemVnum)
				return

			else:
				selectedItemVNum = player.GetItemIndex(itemSlotIndex)
				itemCount = player.GetItemCount(itemSlotIndex)

				mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, itemSlotIndex, selectedItemVNum, itemCount)

				if self.__IsUsableItemToItem(selectedItemVNum, itemSlotIndex):
					self.interface.SetUseItemMode(True)
				else:
					self.interface.SetUseItemMode(False)

				snd.PlaySound("sound/ui/pick.wav")

	def __DropSrcItemToDestItemInInventory(self, srcItemVID, srcItemSlotPos, dstItemSlotPos):
		if srcItemSlotPos == dstItemSlotPos:
			return

		## 악세서리 창이 열려있으면
		## 아이템 이동 금지.
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if player.GetAcceRefineWindowOpen() == 1:
				return

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if player.GetChangeLookWindowOpen() == 1:
				return

		## [MT-462]
		player.GetItemIndex(srcItemSlotPos)
		if player.GetItemIndex(srcItemSlotPos) == player.GetItemIndex(dstItemSlotPos) \
			and (player.GetItemFlags(srcItemSlotPos) & item.ITEM_FLAG_STACKABLE) \
			and player.IsEquipmentSlot(dstItemSlotPos) == False:
			self.__SendMoveItemPacket(srcItemSlotPos, dstItemSlotPos, 0)
			return

		if app.ENABLE_SOUL_BIND_SYSTEM:
			# cyh itemseal 2013 11 08
			if item.IsSealScroll(srcItemVID):
				if player.CanSealItem(srcItemVID, player.INVENTORY, dstItemSlotPos):
					self.__OpenQuestionDialog(srcItemSlotPos, dstItemSlotPos)

		if item.IsRefineScroll(srcItemVID):
			self.RefineItem(srcItemSlotPos, dstItemSlotPos)
			self.interface.SetUseItemMode(False)

		#elif item.IsMetin(srcItemVID):
			#self.AttachMetinToItem(srcItemSlotPos, dstItemSlotPos)
		#Fix: Spirit stones - stacking.
		elif item.IsMetin(srcItemVID) and not item.IsMetin(player.GetItemIndex(dstItemSlotPos)):
			self.AttachMetinToItem(srcItemSlotPos, dstItemSlotPos)

		elif item.IsDetachScroll(srcItemVID):
			self.DetachMetinFromItem(srcItemSlotPos, dstItemSlotPos)

		elif item.IsKey(srcItemVID):
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		elif (player.GetItemFlags(srcItemSlotPos) & ITEM_FLAG_APPLICABLE) == ITEM_FLAG_APPLICABLE:
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		elif item.GetUseType(srcItemVID) in self.USE_TYPE_TUPLE:
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		else:
			self.__SendMoveItemPacket(srcItemSlotPos, dstItemSlotPos, 0)

	def __SellItem(self, itemSlotPos):
		self.sellingSlotNumber = itemSlotPos
		itemIndex = player.GetItemIndex(itemSlotPos)
		itemCount = player.GetItemCount(itemSlotPos)

		self.sellingSlotitemIndex = itemIndex
		self.sellingSlotitemCount = itemCount

		item.SelectItem(itemIndex)
		## 안티 플레그 검사 빠져서 추가
		## 20140220
		if item.IsAntiFlag(item.ANTIFLAG_SELL):
			popup = uiCommon.PopupDialog()
			popup.SetText(localeInfo.SHOP_CANNOT_SELL_ITEM)
			popup.SetAcceptEvent(self.__OnClosePopupDialog)
			popup.Open()
			self.popup = popup
			return

		itemPrice = item.GetISellItemPrice()

		if item.Is1GoldItem():
			itemPrice = itemCount // itemPrice // 5
		else:
			itemPrice = itemPrice * itemCount // 5

		item.GetItemName(itemIndex)
		itemName = item.GetItemName()

		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetText(localeInfo.DO_YOU_SELL_ITEM(itemName, itemCount, itemPrice))
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.SellItem))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
		self.questionDialog.Open()
		self.questionDialog.count = itemCount

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

	def __OnClosePopupDialog(self):
		self.pop = None

	def DetachMetinFromItem(self, scrollSlotPos, targetSlotPos):
		scrollIndex = player.GetItemIndex(scrollSlotPos)
		targetIndex = player.GetItemIndex(targetSlotPos)

		if not player.CanDetach(scrollIndex, targetSlotPos):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_METIN_INSEPARABLE_ITEM)
			return

		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetText(localeInfo.REFINE_DO_YOU_SEPARATE_METIN)
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnDetachMetinFromItem))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
		self.questionDialog.Open()
		self.questionDialog.sourcePos = scrollSlotPos
		self.questionDialog.targetPos = targetSlotPos

	def AttachMetinToItem(self, metinSlotPos, targetSlotPos):
		metinIndex = player.GetItemIndex(metinSlotPos)
		targetIndex = player.GetItemIndex(targetSlotPos)

		item.SelectItem(metinIndex)
		itemName = item.GetItemName()

		result = player.CanAttachMetin(metinIndex, targetSlotPos)

		if player.ATTACH_METIN_NOT_MATCHABLE_ITEM == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_CAN_NOT_ATTACH % (itemName))

		if player.ATTACH_METIN_NO_MATCHABLE_SOCKET == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_NO_SOCKET(itemName))

		elif player.ATTACH_METIN_NOT_EXIST_GOLD_SOCKET == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_NO_GOLD_SOCKET(itemName))

		elif player.ATTACH_METIN_CANT_ATTACH_TO_EQUIPMENT == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_EQUIP_ITEM)

		if player.ATTACH_METIN_OK != result:
			return

		self.attachMetinDialog.Open(metinSlotPos, targetSlotPos)

	def OverOutItem(self):
		self.wndItem.SetUsableItem(False)
		if app.ENABLE_SEARCH_FIELD and self.wndItemSRC:
			self.wndItemSRC.SetUsableItem(False)
		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OverInItem(self, overSlotPos):
		if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
			overInvenSlotPos = self.__InventoryLocalSlotPosToGlobalSlotPos(overSlotPos)
			self.wndItem.SetUsableItem(False)

			getItemVNum = player.GetItemIndex
			itemVnum = getItemVNum(overInvenSlotPos)
			self.DelHighlightSlot(overInvenSlotPos)

			if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
				if self.wndInventory.wndMultiple.IsShow() and app.IsPressed(app.DIK_LCONTROL) and self.wndItem and self.wndItem.IsLeftMouseClicked():
					if not player.IsEquipmentSlot(overInvenSlotPos):
						if osfInfo.MULTIPLE_MODE_SPECIAL_INV == osfInfo.MULTIPLE_MODE_ADD:
							self.AddToMultipleList(overInvenSlotPos, False, False)
						elif osfInfo.MULTIPLE_MODE_SPECIAL_INV == osfInfo.MULTIPLE_MODE_DELETE:
							self.RemoveFromMultipleList(overInvenSlotPos)

			if mouseModule.mouseController.isAttached():
				attachedItemType = mouseModule.mouseController.GetAttachedType()

				if player.SLOT_TYPE_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_STONE_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_SWITCH_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_COSTUME_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_CONSUMABLE_INVENTORY == attachedItemType:

					attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
					attachedItemVNum = mouseModule.mouseController.GetAttachedItemIndex()

					if self.__CanUseSrcItemToDstItem(attachedItemVNum, attachedSlotPos, overInvenSlotPos):
						self.wndItem.SetUsableItem(True)
						self.ShowToolTip(overInvenSlotPos)
						return

			self.ShowToolTip(overInvenSlotPos)
		else:
			overSlotPos = self.__InventoryLocalSlotPosToGlobalSlotPos(overSlotPos)
			self.wndItem.SetUsableItem(False)

			if mouseModule.mouseController.isAttached():
				attachedItemType = mouseModule.mouseController.GetAttachedType()

				if player.SLOT_TYPE_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_STONE_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_SWITCH_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_COSTUME_INVENTORY == attachedItemType or\
					player.SLOT_TYPE_CONSUMABLE_INVENTORY == attachedItemType:

					attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
					attachedItemVNum = mouseModule.mouseController.GetAttachedItemIndex()

					if self.__CanUseSrcItemToDstItem(attachedItemVNum, attachedSlotPos, overSlotPos):
						self.wndItem.SetUsableItem(True)
						self.ShowToolTip(overSlotPos)
						return

			self.ShowToolTip(overSlotPos)

	def __IsUsableItemToItem(self, srcItemVNum, srcSlotPos):
		if item.IsRefineScroll(srcItemVNum):
			return True
		elif item.IsMetin(srcItemVNum):
			return True
		elif item.IsDetachScroll(srcItemVNum):
			return True
		elif item.IsKey(srcItemVNum):
			return True
		elif (player.GetItemFlags(srcSlotPos) & ITEM_FLAG_APPLICABLE) == ITEM_FLAG_APPLICABLE:
			return True
		else:
			if item.GetUseType(srcItemVNum) in self.USE_TYPE_TUPLE:
				return True

		return False

	def __CanUseSrcItemToDstItem(self, srcItemVNum, srcSlotPos, dstSlotPos):
		if srcItemVNum == 79850:
			return (not player.IsEquipmentSlot(dstSlotPos)
				and 10750 <= player.GetItemIndex(dstSlotPos) <= 10754)
		if 10750 <= player.GetItemIndex(dstSlotPos) <= 10754 and item.GetUseType(srcItemVNum) in (
			"USE_CHANGE_ATTRIBUTE", "USE_CHANGE_ATTRIBUTE2", "USE_ADD_ATTRIBUTE", "USE_ADD_ATTRIBUTE2"):
			return False
		if srcItemVNum == mountcorebonus.SEAL_VNUM:
			return mountcorebonus.CanUseSeal(srcItemVNum, player.GetItemIndex(dstSlotPos))
		if srcSlotPos == dstSlotPos:
			return False

		if item.IsRefineScroll(srcItemVNum):
			if player.REFINE_OK == player.CanRefine(srcItemVNum, dstSlotPos):
				return True
		#elif item.IsMetin(srcItemVNum):
			#if player.ATTACH_METIN_OK == player.CanAttachMetin(srcItemVNum, dstSlotPos):
				#return True
		#Fix: Spirit stones - stacking.
		elif item.IsMetin(srcItemVNum):
			if player.ATTACH_METIN_OK == player.CanAttachMetin(srcItemVNum, dstSlotPos) or (item.IsMetin(player.GetItemIndex(dstSlotPos)) and player.GetItemIndex(dstSlotPos) == srcItemVNum):
				return True
		elif item.IsDetachScroll(srcItemVNum):
			if player.DETACH_METIN_OK == player.CanDetach(srcItemVNum, dstSlotPos):
				return True
		elif item.IsKey(srcItemVNum):
			if player.CanUnlock(srcItemVNum, dstSlotPos):
				return True
		elif (player.GetItemFlags(srcSlotPos) & ITEM_FLAG_APPLICABLE) == ITEM_FLAG_APPLICABLE:
			return True
		else:
			useType=item.GetUseType(srcItemVNum)

			if "USE_CLEAN_SOCKET" == useType:
				if self.__CanCleanBrokenMetinStone(dstSlotPos):
					return True
			elif "USE_CHANGE_ATTRIBUTE" == useType:
				if self.__CanChangeItemAttrList(dstSlotPos):
					return True
			elif "USE_ADD_ATTRIBUTE" == useType:
				if self.__CanAddItemAttr(dstSlotPos):
					return True
			elif "USE_ADD_ATTRIBUTE2" == useType:
				if self.__CanAddItemAttr(dstSlotPos):
					return True
			elif "USE_ADD_ACCESSORY_SOCKET" == useType:
				if self.__CanAddAccessorySocket(dstSlotPos):
					return True
			elif "USE_PUT_INTO_ACCESSORY_SOCKET" == useType:
				if self.__CanPutAccessorySocket(dstSlotPos, srcItemVNum):
					return True;
			elif "USE_PUT_INTO_BELT_SOCKET" == useType:
				dstItemVNum = player.GetItemIndex(dstSlotPos)

				item.SelectItem(dstItemVNum)

				if item.ITEM_TYPE_BELT == item.GetItemType():
					return True
			elif "USE_CHANGE_COSTUME_ATTR" == useType:
				if self.__CanChangeCostumeAttrList(dstSlotPos):
					return True
			elif "USE_RESET_COSTUME_ATTR" == useType:
				if self.__CanResetCostumeAttr(dstSlotPos):
					return True
			else:
				pass

		return False

	def __CanChangeItemAttrList(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
			return False

		attrCount = 0
		for i in range(player.METIN_SOCKET_MAX_NUM):
			if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
				attrCount += 1

		if attrCount > 0:
			return True

		return False

	def __CanChangeCostumeAttrList(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)
		if item.GetItemType() != item.ITEM_TYPE_COSTUME:
			return False
		if app.ENABLE_ACCE_COSTUME_SYSTEM and item.GetItemSubType() == item.COSTUME_TYPE_ACCE:
			return False
		if app.ENABLE_MOUNT_COSTUME_SYSTEM and item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
			return False

		for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
				return True
		return False

	def __CanResetCostumeAttr(self, dstSlotPos):
		return self.__CanChangeCostumeAttrList(dstSlotPos)
		
	def __CanAddItemAttr(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
			return False

		attrCount = 0
		for i in range(player.METIN_SOCKET_MAX_NUM):
			# 2020.02.13.Owsap - Fix Attribute Count
			if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
				attrCount += 1

		if attrCount < 4:
			return True

		return False

	def ShowToolTip(self, slotIndex):
		if None != self.tooltipItem:
			self.tooltipItem.SetInventoryItem(
				slotIndex, specialInventoryType=self.inventoryType
			)

	def OnTop(self):
		if None != self.tooltipItem:
			self.tooltipItem.SetTop()

		if self.GetInventoryType() == SAFEBOX_BUTTON_NUM:
			self.safebox.OnTop()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def UseItemSlot(self, slotIndex):
		curCursorNum = app.GetCursor()
		if app.SELL == curCursorNum:
			return

		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS():
			return

		if app.ENABLE_SEARCH_FIELD:
			if self.wndItemSRC and self.wndItemSRC.IsShow() and self.wndSearchEdit and self.wndSearchEdit.GetText():
				anchor = self.__SpecialInventorySearchResolveAnchor(slotIndex)
				if anchor in self.wndItemSRC.dictItems:
					resultType, slotIndex = self.wndItemSRC.dictItems[anchor]
					provider = self.__GetActiveStorageProvider()
					if resultType in (SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM):
						if (
							resultType == self.inventoryType and
							self.IsExpandedStorageProvider() and provider
						):
							provider.UseGlobalItemSlot(slotIndex)
							self.OverOutItem()
						return
				else:
					slotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(slotIndex)
			else:
				slotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(slotIndex)
		else:
			slotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(slotIndex)

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if slotIndex in osfInfo.MULTIPLE_LIST:
				return

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if self.isShowAcceWindow():
				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_NOT_SEALITEM)
						return

				acce.Add(player.INVENTORY, slotIndex, 255)
				return

		if app.ENABLE_AURA_SYSTEM:
			if self.isShowAuraWindow():
				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHANGE_LOOK_DO_NOT_SEAL_ITEM)
						return

				self.wndAura.AddFastItem(slotIndex)
				return

		self.__UseItem(slotIndex)
		mouseModule.mouseController.DeattachObject()
		self.OverOutItem()

	def PageToInventoryType(self):
		if self.inventoryType == 0:
			return player.SLOT_TYPE_SKILL_BOOK_INVENTORY
		elif self.inventoryType == 1:
			return player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY
		elif self.inventoryType == 2:
			return player.SLOT_TYPE_STONE_INVENTORY
		elif self.inventoryType == 3:
			return player.SLOT_TYPE_GIFT_BOX_INVENTORY
		elif self.inventoryType == 4:
			return player.SLOT_TYPE_SWITCH_INVENTORY
		elif self.inventoryType == CONSUMABLE_BUTTON_NUM:
			return player.SLOT_TYPE_CONSUMABLE_INVENTORY
		elif self.inventoryType == 5:
			return player.SLOT_TYPE_COSTUME_INVENTORY
		return player.SLOT_TYPE_INVENTORY

	def __UseItem(self, slotIndex):
		ItemVNum = player.GetItemIndex(slotIndex)
		item.SelectItem(ItemVNum)

		isCtrlPressed = app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)
		isAltPressed = app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT)

		if isCtrlPressed and isAltPressed:
			return

		if app.ENABLE_WIKI:
			if isCtrlPressed:
				if self.interface:
					if not self.interface.wndWiki or not self.interface.wndWiki.IsShow():
						self.interface.OpenWikiWindow()

					if self.interface.wndWiki and self.interface.wndWiki.IsShow():
						self.interface.wndWiki.ShowItemInfo(ItemVNum, 0, isHistory=False)
						if hasattr(self.interface.wndWiki, "FocusSearchItem"):
							self.interface.wndWiki.FocusSearchItem()
				return

		# Ctrl keeps the wiki lookup above; any other right-click while an
		# exchange is open offers the item instead of using it (ALTHEA-601).
		if exchangequickadd.TryAddInventoryItem(self.interface, slotIndex):
			return

		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				if self.interface.AttachInvenItemToOtherWindowSlot(slotIndex):
					return

		if app.ENABLE_GROWTH_PET_SYSTEM:
			itemType = item.GetItemType()
			slotType = self.PageToInventoryType()
			if itemType == item.ITEM_TYPE_PET and item.GetItemSubType() == item.PET_SKILL:
				if self.interface and self.interface.wndPetInfoWindow:
					self.interface.wndPetInfoWindow.RequestLearnSkillBook(slotIndex)
				return
			if self.interface.wndPetInfoWindow.AttachItemToPetWindow(player.INVENTORY, slotType, slotIndex):
				return

		if app.ENABLE_SHOW_CHEST_DROP:
			if player.GetItemTypeBySlot(slotIndex) in (
					item.ITEM_TYPE_GIFTBOX, item.ITEM_TYPE_GACHA,
					item.ITEM_TYPE_TREASURE_BOX):
				if self.interface and self.interface.dlgChestDrop:
					self.interface.dlgChestDrop.RequestPreview(slotIndex)
				return

		if item.IsFlag(item.ITEM_FLAG_CONFIRM_WHEN_USE):
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(localeInfo.INVENTORY_REALLY_USE_ITEM2)

			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__UseItemQuestionDialog_OnAccept))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__UseItemQuestionDialog_OnCancel))
			self.questionDialog.Open()
			self.questionDialog.slotIndex = slotIndex

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)
		else:
			self.__SendUseItemPacket(slotIndex)

	def __UseItemQuestionDialog_OnCancel(self):
		self.OnCloseQuestionDialog()

	def __UseItemQuestionDialog_OnAccept(self):
		self.__SendUseItemPacket(self.questionDialog.slotIndex)
		self.OnCloseQuestionDialog()

	def __SendUseItemToItemPacket(self, srcSlotPos, dstSlotPos):
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.USE_ITEM_FAILURE_PRIVATE_SHOP)
			return

		if self.interface.IsShowDlgQuestionWindow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DONT_USE_ITEM_WHEN_SHOW_CONFIRM)
			return

		net.SendItemUseToItemPacket(srcSlotPos, dstSlotPos)

	def __SendUseItemPacket(self, slotPos):
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.USE_ITEM_FAILURE_PRIVATE_SHOP)
			return

		if self.interface.IsShowDlgQuestionWindow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DONT_USE_ITEM_WHEN_SHOW_CONFIRM)
			return

		net.SendItemUsePacket(slotPos)

	def __SendMoveItemPacket(self, srcSlotPos, dstSlotPos, srcItemCount):
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MOVE_ITEM_FAILURE_PRIVATE_SHOP)
			return

		if self.interface.IsShowDlgQuestionWindow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DONT_USE_ITEM_WHEN_SHOW_CONFIRM)
			return

		net.SendItemMovePacket(srcSlotPos, dstSlotPos, srcItemCount)

	if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
		def HighlightSlot(self, slot):
			if not slot in self.listHighlightedSlot:
				self.listHighlightedSlot.append(slot)

		def DelHighlightSlot(self, inventorylocalslot):
			if inventorylocalslot in self.listHighlightedSlot:
				if inventorylocalslot >= player.SPECIAL_INVENTORY_PAGE_SIZE:
					self.wndItem.DeactivateSlot(inventorylocalslot - (self.inventoryPageIndex * player.SPECIAL_INVENTORY_PAGE_SIZE))
				else:
					self.wndItem.DeactivateSlot(inventorylocalslot)

				self.listHighlightedSlot.remove(inventorylocalslot)

				self.RefreshBagSlotWindow() # hot fix

	# 악세서리 슬롯 테두리 추가, 제거.
	## HilightSlot Change
	def DeactivateSlot(self, slotindex, type):
		if type == wndMgr.HILIGHTSLOT_MAX:
			return

	## HilightSlot Change
	def ActivateSlot(self, slotindex, type):
		if type == wndMgr.HILIGHTSLOT_MAX:
			return

	def __HighlightSlot_Refresh(self):
		for i in range(self.wndItem.GetSlotCount()):
			slotNumber = self.__InventoryLocalSlotPosToGlobalSlotPos(i)
			if slotNumber in self.listHighlightedSlot:
				# An active dew keeps the Sun Elixir effect over the pickup marker.
				if (app.ENABLE_EXTENDED_BLEND_AFFECT and
						osfInfo.IS_DEW_POTION(player.GetItemIndex(slotNumber)) and
						player.GetItemMetinSocket(slotNumber, 3)):
					self.wndItem.ActivateSlotOld(i)
				else:
					self.wndItem.ActivateSlot(i)

	def __HighlightSlot_Clear(self):
		for i in range(self.wndItem.GetSlotCount()):
			slotNumber = self.__InventoryLocalSlotPosToGlobalSlotPos(i)
			if slotNumber in self.listHighlightedSlot:
				self.wndItem.DeactivateSlot(i)
				self.listHighlightedSlot.remove(slotNumber)

	def IsDlgQuestionShow(self):
		if self.dlgQuestion.IsShow():
			return True
		else:
			return False

	def SetUseItemMode(self, bUse):
		self.wndItem.SetUseMode(bUse)

	def CancelDlgQuestion(self):
		self.__Cancel()

	def GetInventoryPageIndex(self):
		return self.inventoryPageIndex

	def GetInventoryType(self):
		return self.inventoryType

	if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
		def OnUpdate(self):
			if osfInfo.MULTIPLE_MODE_SPECIAL_INV != -1:
				if self.wndItem:
					if not self.wndItem.IsLeftMouseClicked():
						osfInfo.MULTIPLE_MODE_SPECIAL_INV = -1
					 
		def AddToMultipleList(self, slot, bSetMode = False, bPrintInfo = True):
			if slot in osfInfo.MULTIPLE_LIST:
				return
				
			if len(osfInfo.MULTIPLE_LIST) == 0:
				if self.wndInventory.wndMultiple.IsTypeSell() and not osfInfo.CanSellItem(slot):
					if osfInfo.CanDestroyItem(slot):
						self.wndInventory.wndMultiple.OnPressFragmentBtn()
					else:
						if bPrintInfo:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL_OR_DESTROY)
						return
				elif self.wndInventory.wndMultiple.IsTypeDestroy() and not osfInfo.CanDestroyItem(slot):
					if osfInfo.CanSellItem(slot):
						self.wndInventory.wndMultiple.OnPressSellBtn()
					else:
						if bPrintInfo:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL_OR_DESTROY)
						return
			else:
				if self.wndInventory.wndMultiple.IsTypeSell() and not osfInfo.CanSellItem(slot):
					if bPrintInfo:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL)
					return
					
				if self.wndInventory.wndMultiple.IsTypeDestroy() and not osfInfo.CanDestroyItem(slot):
					if bPrintInfo:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_DESTROY)
					return
				
			if bSetMode:
				osfInfo.MULTIPLE_MODE_SPECIAL_INV = osfInfo.MULTIPLE_MODE_ADD
				
			if self.wndInventory.wndMultiple.IsOpeningInventory() == False:
				self.wndInventory.wndMultiple.Show(True)

			osfInfo.MULTIPLE_LIST.append(int(slot))
			self.wndInventory.wndMultiple.UpdateItemCount(int(slot), 1)
			self.wndInventory.wndMultiple.UpdatePrice(int(slot), 1)

			self.wndInventory.interface.RefreshMarkInventoryBag()
			
		def RemoveFromMultipleList(self, slot):
			if slot in osfInfo.MULTIPLE_LIST:
				osfInfo.MULTIPLE_LIST.remove(int(slot))
				self.wndInventory.wndMultiple.UpdateItemCount(int(slot), 2)
				self.wndInventory.wndMultiple.UpdatePrice(int(slot), 2)
				self.RefreshBagSlotWindow()
				
				if len(osfInfo.MULTIPLE_LIST) < 1:
					self.wndInventory.wndMultiple.CloseInventory()

	def CanManageSafeboxWindow(self):
		return bool(self.safebox)

	def CanManageMallWindow(self):
		return bool(self.mall)

	def IsExpandedStorageProvider(self):
		return (
			IsExpandedSafeboxLayout() and
			self.GetInventoryType() in (
				SAFEBOX_BUTTON_NUM, MALL_BUTTON_NUM
			)
		)

	def __GetActiveStorageProvider(self):
		if self.GetInventoryType() == SAFEBOX_BUTTON_NUM:
			return self.safebox
		if self.GetInventoryType() == MALL_BUTTON_NUM:
			return self.mall
		return None

	def __ApplyStorageTabVisibility(self):
		for button in self.inventoryTab:
			if self.IsExpandedStorageProvider():
				button.Show()
			else:
				button.Hide()

	def RefreshActiveProviderSearch(self, provider):
		if (
			provider == self.__GetActiveStorageProvider() and
			self.IsExpandedStorageProvider() and
			app.ENABLE_SEARCH_FIELD
		):
			self.__RefreshSpecialInventorySearchGrid()

	def CanRefreshSpecialInventoryPage(self):
		if self.GetInventoryType() == SAFEBOX_BUTTON_NUM or\
			self.GetInventoryType() == MALL_BUTTON_NUM:
			return False
		return True

		##############################

	def __OpenSafebox(self):
		self.wndItem.Hide()
		if self.CanManageSafeboxWindow():
			self.safebox.PrepareWindow()
		self.__ApplyStorageTabVisibility()
		self.loading_image.Hide()
		net.SendChatPacket("/new_safebox_open")

	def __CloseSafebox(self):
		net.SendChatPacket("/safebox_close")
		self.wndItem.Show()
		for button in self.inventoryTab: button.Show()
		if self.CanManageSafeboxWindow(): self.safebox.Hide()
		self.loading_image.Hide()

	def ShowSafeboxWindow(self, size):
		if self.GetInventoryType() != SAFEBOX_BUTTON_NUM or not self.IsShow():
			net.SendChatPacket("/safebox_close")
			return

		if self.CanManageSafeboxWindow() is False: return
		self.__ApplyInventoryLayout(SAFEBOX_BUTTON_NUM)
		self.safebox.ShowWindow(size)
		self.__ApplyStorageTabVisibility()
		self.__ApplySpecialInventorySearchVisibility()
		self.safebox.OnTop()
		self.loading_image.Hide()

	def CommandCloseSafebox(self):
		if self.CanManageSafeboxWindow() is False: return
		self.safebox.CommandCloseSafebox()

		#################################################

	def __OpenMall(self):
		self.wndItem.Hide()
		if self.CanManageMallWindow():
			self.mall.PrepareWindow()
		self.__ApplyStorageTabVisibility()
		self.loading_image.Hide()
		net.SendChatPacket("/new_mall_open")

	def __CloseMall(self):
		net.SendChatPacket("/mall_close")
		self.wndItem.Show()
		for button in self.inventoryTab: button.Show()
		if self.CanManageMallWindow(): self.mall.Hide()
		self.loading_image.Hide()

	def ShowMallWindow(self, size):
		if self.GetInventoryType() != MALL_BUTTON_NUM or not self.IsShow():
			net.SendChatPacket("/mall_close")
			return

		if self.CanManageMallWindow() is False: return
		self.__ApplyInventoryLayout(MALL_BUTTON_NUM)
		self.mall.ShowWindow(size)
		self.__ApplyStorageTabVisibility()
		self.__ApplySpecialInventorySearchVisibility()
		self.loading_image.Hide()

	def CommandCloseMall(self):
		if self.CanManageMallWindow() is False: return
		self.mall.CommandCloseMall()

	def CloseLoadSafeboxEvent(self):
		self.__CloseSafebox()
		self.SetInventoryType(0)

	def CloseLoadMallEvent(self):
		self.__CloseMall()
		self.SetInventoryType(0)

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def SetAcceWindow(self, wndAcceCombine, wndAcceAbsorption):
			self.wndAcceCombine = wndAcceCombine
			self.wndAcceAbsorption = wndAcceAbsorption

		def isShowAcceWindow(self):
			if self.wndAcceCombine:
				if self.wndAcceCombine.IsShow():
					return 1

			if self.wndAcceAbsorption:
				if self.wndAcceAbsorption.IsShow():
					return 1

			return 0

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def SetChangeLookWindow(self, wndChangeLook):
			self.wndChangeLook = wndChangeLook

		def isShowChangeLookWindow(self):
			if self.wndChangeLook:
				if self.wndChangeLook.IsShow():
					return 1
			return 0

	if app.ENABLE_AURA_SYSTEM:
		def SetAuraWindow(self, wndAura):
			self.wndAura = wndAura
			
		def isShowAuraWindow(self):
			if self.wndAura:
				if self.wndAura.IsShow():
					return 1
			return 0
