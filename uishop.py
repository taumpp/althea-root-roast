import net
import player
import item
import snd
import shop
import net
import wndMgr
import app
import chat

import ui
import uiCommon
import mouseModule
import slotwindowpolicy
import localeInfo
import constInfo
import osfInfo
import shopgrid
import uicrimsoncontrols


SHOP_WINDOW_WIDTH = 344
SHOP_GRID_Y = 34
SHOP_SLOT_SIZE = 32
SHOP_FOOTER_GAP = 8
SHOP_FOOTER_HEIGHT = 24
SHOP_BOTTOM_MARGIN = 11
SHOP_BUY_X = 94
SHOP_SELL_X = 178
SHOP_CLOSE_X = 98

"""
Note:
	class ShopDialog 가 개인상점, NPC 상점을 유동적으로 사용 하였는데,
	개인상점 꾸미기 적용 후( #define ENABLE_MYSHOP_DECO ) 부터
	class ShopDialog ( NPC 상점 ) class PrivateShopDialog ( 개인 상점 ) 분리 됨
"""

## NPC 상점 ##
class ShopDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = 0
		self.xShopStart = 0
		self.yShopStart = 0
		self.questionDialog = None
		self.popup = None
		self.itemBuyQuestionDialog = None
		self.interface = None
		self.board = None
		self.visibleAnchorToRealIndex = {}
		self.visibleSlotToRealIndex = {}
		self.visibleSlotCount = 0
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = False

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __ItemHeight(self, itemVnum):
		try:
			item.SelectItem(int(itemVnum))
			return max(1, min(3, int(item.GetItemSize()[1])))
		except:
			return 1

	def __ResizeForRows(self, rowCount):
		footerY = SHOP_GRID_Y + int(rowCount) * SHOP_SLOT_SIZE + SHOP_FOOTER_GAP
		windowHeight = footerY + SHOP_FOOTER_HEIGHT + SHOP_BOTTOM_MARGIN

		self.SetSize(SHOP_WINDOW_WIDTH, windowHeight)
		self.board.SetSize(SHOP_WINDOW_WIDTH, windowHeight)
		self.titleBar.SetWidth(self.board.GetWidth() + 8)
		self.btnBuy.SetPosition(SHOP_BUY_X, footerY)
		self.btnSell.SetPosition(SHOP_SELL_X, footerY)
		self.btnClose.SetPosition(SHOP_CLOSE_X, footerY)

	def __RebuildGrid(self):
		records = []
		tabCount = max(1, int(shop.GetTabCount()))
		for realIndex in range(tabCount * shop.SHOP_SLOT_COUNT):
			itemVnum = int(shop.GetItemID(realIndex))
			if itemVnum:
				records.append((realIndex, self.__ItemHeight(itemVnum)))

		layout = shopgrid.PackShopItems(records)
		for visibleSlot in range(self.visibleSlotCount):
			self.itemSlotWindow.ClearSlot(visibleSlot)
			self.itemSlotWindow.EnableSlotCoverImage(visibleSlot, False)

		rowCount = layout["rows"]
		self.itemSlotWindow.ArrangeSlot(
			0, shopgrid.GRID_COLUMNS, rowCount,
			SHOP_SLOT_SIZE, SHOP_SLOT_SIZE, 0, 0)
		self.itemSlotWindow.SetSlotBaseImage(
			"d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		self.itemSlotWindow.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)

		self.visibleAnchorToRealIndex = layout["anchors"]
		self.visibleSlotToRealIndex = layout["footprint"]
		self.visibleSlotCount = shopgrid.GRID_COLUMNS * rowCount
		for visibleSlot in range(self.visibleSlotCount):
			self.itemSlotWindow.ClearSlot(visibleSlot)
			self.itemSlotWindow.EnableSlotCoverImage(visibleSlot, False)
		self.__ResizeForRows(rowCount)

	def __ResolveRealIndex(self, visibleSlot):
		return shopgrid.ResolveRealIndex(self.visibleSlotToRealIndex, visibleSlot)

	def __GetSourceTab(self, realIndex):
		return shopgrid.SourceTab(realIndex, shop.SHOP_SLOT_COUNT)

	def __IsCombatZoneIndex(self, realIndex):
		if not app.ENABLE_COMBAT_ZONE:
			return False
		sourceTab = self.__GetSourceTab(realIndex)
		return sourceTab is not None and shop.SHOP_COIN_TYPE_COMBAT_ZONE == \
			shop.GetTabCoinType(sourceTab)

	def __HasCombatZoneItems(self):
		for realIndex in self.visibleAnchorToRealIndex.values():
			if self.__IsCombatZoneIndex(realIndex):
				return True
		return False

	def Refresh(self):
		self.__RebuildGrid()
		getItemID = shop.GetItemID
		getItemCount = shop.GetItemCount
		setItemID = self.itemSlotWindow.SetItemSlot

		for visibleSlot in sorted(self.visibleAnchorToRealIndex):
			realIndex = self.visibleAnchorToRealIndex[visibleSlot]
			itemVnum = getItemID(realIndex)
			itemCount = getItemCount(realIndex)
			if itemCount <= 1:
				itemCount = 0
			setItemID(visibleSlot, itemVnum, itemCount)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				changelookvnum = shop.GetItemChangeLookVnum(realIndex)
				if not changelookvnum == 0:
					self.itemSlotWindow.SetSlotCoverImage(visibleSlot, "icon/item/ingame_convert_Mark.tga")
				else:
					self.itemSlotWindow.EnableSlotCoverImage(visibleSlot, False)

			if app.ENABLE_EXTENDED_BLEND_AFFECT:
				if osfInfo.IS_EXTENDED_BLEND_POTION(itemVnum):
					self.itemSlotWindow.SetSlotCoverImage(visibleSlot, "d:/ymir work/ui/acce/ingame_convert_mark_02.tga")
				elif osfInfo.IS_BLEND_POTION(itemVnum):
					self.itemSlotWindow.SetSlotCoverImage(visibleSlot, "icon/item/trade.tga")
				else:
					self.itemSlotWindow.EnableSlotCoverImage(visibleSlot, False)

		wndMgr.RefreshSlot(self.itemSlotWindow.GetWindowHandle())

	def SetItemData(self, pos, itemID, itemCount, itemPrice):
		shop.SetItemData(pos, itemID, itemCount, itemPrice)

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/shopdialog.py")
		except:
			import exception
			exception.Abort("ShopDialog.LoadDialog.LoadObject")

		try:
			GetObject = self.GetChild
			self.board = GetObject("Board")
			self.itemSlotWindow = GetObject("ItemSlot")
			self.btnBuy = GetObject("BuyButton")
			self.btnSell = GetObject("SellButton")
			self.btnClose = GetObject("CloseButton")
			self.titleBar = GetObject("TitleBar")

		except:
			import exception
			exception.Abort("ShopDialog.LoadDialog.BindObject")

		uicrimsoncontrols.ApplyVisuals(self.btnBuy, "72x24")
		uicrimsoncontrols.ApplyVisuals(self.btnSell, "72x24")
		uicrimsoncontrols.ApplyVisuals(self.btnClose, "148x23")

		self.itemSlotWindow.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
		self.itemSlotWindow.SAFE_SetButtonEvent("LEFT", "EMPTY", self.SelectEmptySlot)
		self.itemSlotWindow.SAFE_SetButtonEvent("LEFT", "EXIST", self.SelectItemSlot)
		self.itemSlotWindow.SAFE_SetButtonEvent("RIGHT", "EXIST", self.UnselectItemSlot)

		self.itemSlotWindow.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.itemSlotWindow.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		self.btnBuy.SetToggleUpEvent(ui.__mem_func__(self.CancelShopping))
		self.btnBuy.SetToggleDownEvent(ui.__mem_func__(self.OnBuy))

		self.btnSell.SetToggleUpEvent(ui.__mem_func__(self.CancelShopping))
		self.btnSell.SetToggleDownEvent(ui.__mem_func__(self.OnSell))

		self.btnClose.SetEvent(ui.__mem_func__(self.AskClosePrivateShop))

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

		self.Refresh()

	def Destroy(self):
		self.Close()
		self.ClearDictionary()

		self.tooltipItem = 0
		self.itemSlotWindow = 0
		self.btnBuy = 0
		self.btnSell = 0
		self.btnClose = 0
		self.titleBar = 0
		self.board = 0
		self.visibleAnchorToRealIndex = {}
		self.visibleSlotToRealIndex = {}
		self.visibleSlotCount = 0
		self.questionDialog = None
		self.popup = None

	# Combat Zone is retired on Althea. Keep these no-op entry points so a
	# legacy packet/client combination cannot break an otherwise normal shop.
	def SetCombatZoneBoard(self, flag):
		pass

	def SetCombatZonePoints(self, points):
		pass

	def SetLimitCombatZonePoints(self, curLimit, maxLimit):
		pass

	def Open(self, vid, points=0, curLimit=0, maxLimit=0):
		isPrivateShop = False
		isMainPlayerPrivateShop = False

		import chr
		if vid == 0 or chr.IsNPC(vid):
			isPrivateShop = False
		else:
			isPrivateShop = True

		if player.IsMainCharacterIndex(vid):
			isMainPlayerPrivateShop = True

			self.btnBuy.Hide()
			self.btnSell.Hide()
			self.btnClose.Show()
		else:
			isMainPlayerPrivateShop = False

			self.btnBuy.Show()
			self.btnSell.Show()
			self.btnClose.Hide()

		shop.Open(isPrivateShop, isMainPlayerPrivateShop)

		self.Refresh()
		windowX = max(0, wndMgr.GetScreenWidth() - 400)
		windowY = max(0, min(10, wndMgr.GetScreenHeight() - self.GetHeight()))
		self.SetPosition(windowX, windowY)
		self.SetTop()

		if app.ENABLE_COMBAT_ZONE:
			if self.__HasCombatZoneItems():
				self.SetCombatZonePoints(points)
				self.SetLimitCombatZonePoints(curLimit, maxLimit)
				self.SetCombatZoneBoard(True)
			else:
				self.SetCombatZoneBoard(False)

		self.Show()

		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = False

		(self.xShopStart, self.yShopStart, z) = player.GetMainCharacterPosition()

	def Close(self):
		print("uiShop.py Close")
		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()

		if self.itemBuyQuestionDialog:
			self.itemBuyQuestionDialog.Close()
			self.itemBuyQuestionDialog = None
			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

		if self.questionDialog:
			self.OnCloseQuestionDialog()

		shop.Close()
		net.SendShopEndPacket()
		self.CancelShopping()
		self.tooltipItem.HideToolTip()
		if app.ENABLE_ANIMATED_WINDOW:
			if self.bClosed == False:
				self.Hide()
		else:
			self.Hide()

		self.visibleAnchorToRealIndex = {}
		self.visibleSlotToRealIndex = {}

		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = True

	def GetIndexFromSlotPos(self, slotPos):
		return self.__ResolveRealIndex(slotPos)

	def AskClosePrivateShop(self):
		questionDialog = uiCommon.QuestionDialog()
		questionDialog.SetText(localeInfo.PRIVATE_SHOP_CLOSE_QUESTION)
		questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnClosePrivateShop))
		questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
		questionDialog.Open()
		self.questionDialog = questionDialog

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

		return True

	def OnClosePrivateShop(self):
		net.SendChatPacket("/close_shop")
		self.OnCloseQuestionDialog()
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		self.Close()
		return True

	def OnBuy(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_BUY_INFO)
		app.SetCursor(app.BUY)
		self.btnSell.SetUp()

	def OnSell(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_SELL_INFO)
		app.SetCursor(app.SELL)
		self.btnBuy.SetUp()

	def CancelShopping(self):
		self.btnBuy.SetUp()
		self.btnSell.SetUp()
		app.SetCursor(app.NORMAL)

	def __OnClosePopupDialog(self):
		self.pop = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	## 용혼석 팔리는 기능 추가.
	def SellAttachedItem(self):
		if shop.IsPrivateShop():
			mouseModule.mouseController.DeattachObject()
			return

		if self.__HasCombatZoneItems():
			mouseModule.mouseController.DeattachObject()
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedCount = mouseModule.mouseController.GetAttachedItemCount()
		if localeInfo.IsBRAZIL() == 0:
			attachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()

		if player.IsEquipmentSlot(attachedSlotPos):
			return

		if app.ENABLE_SOUL_BIND_SYSTEM:
			if player.GetItemSealDate(attachedSlotType, attachedSlotPos) == -1 or player.GetItemSealDate(attachedSlotType, attachedSlotPos) > 0: #봉인아이템 걸러냄.
				mouseModule.mouseController.DeattachObject()
				return

		if slotwindowpolicy.IsOwnedItemSlotType(attachedSlotType):

			if localeInfo.IsBRAZIL():
				itemIndex = player.GetItemIndex(attachedSlotPos)
				item.SelectItem(itemIndex)
			else:
				item.SelectItem(attachedItemIndex)

			if item.IsAntiFlag(item.ANTIFLAG_SELL):
				popup = uiCommon.PopupDialog()
				popup.SetText(localeInfo.SHOP_CANNOT_SELL_ITEM)
				popup.SetAcceptEvent(self.__OnClosePopupDialog)
				popup.Open()
				self.popup = popup
				return

			itemtype = player.INVENTORY

			if localeInfo.IsBRAZIL() == 0:
				if player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == attachedSlotType:
					itemtype = player.DRAGON_SOUL_INVENTORY

			if player.IsValuableItem(itemtype, attachedSlotPos):
				itemPrice = item.GetISellItemPrice()

				if item.Is1GoldItem():
					itemPrice = attachedCount // itemPrice // 5
				else:
					itemPrice = itemPrice * max(1, attachedCount) // 5

				itemName = item.GetItemName()

				questionDialog = uiCommon.QuestionDialog()
				questionDialog.SetText(localeInfo.DO_YOU_SELL_ITEM(itemName, attachedCount, itemPrice))

				questionDialog.SetAcceptEvent(lambda arg1=attachedSlotPos, arg2=attachedCount, arg3 = itemtype: self.OnSellItem(arg1, arg2, arg3))
				questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
				questionDialog.Open()
				self.questionDialog = questionDialog

				constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)
			else:
				self.OnSellItem(attachedSlotPos, attachedCount, itemtype)
		else:
			snd.PlaySound("sound/ui/loginfail.wav")

		mouseModule.mouseController.DeattachObject()

	def OnSellItem(self, slotPos, count, itemtype):
		net.SendShopSellPacketNew(slotPos, count, itemtype)
		snd.PlaySound("sound/ui/money.wav")
		self.OnCloseQuestionDialog()

	def OnCloseQuestionDialog(self):
		if not self.questionDialog:
			return

		self.questionDialog.Close()
		self.questionDialog = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def SelectEmptySlot(self, selectedSlotPos):
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			self.SellAttachedItem()

	def UnselectItemSlot(self, selectedSlotPos):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		realIndex = self.__ResolveRealIndex(selectedSlotPos)
		if realIndex is None:
			return

		if shop.IsPrivateShop():
			self.AskBuyItem(realIndex)
		else:
			if self.__IsCombatZoneIndex(realIndex):
				self.AskBuyItem(realIndex)
			elif app.ENABLE_MULTIPLE_BUY:
				canBuyMultiple = False

				itemIndex = shop.GetItemID(realIndex)
				item.SelectItem(itemIndex)
				if item.IsFlag(item.ITEM_FLAG_STACKABLE) and itemIndex != 51002 and itemIndex != 55031:
					canBuyMultiple = True

				if app.IsPressed(app.DIK_LCONTROL) and canBuyMultiple:
					self.AskSelectQuantity(realIndex)
				else:
					net.SendShopBuyPacket(realIndex)
			else:
				net.SendShopBuyPacket(realIndex)

	if app.ENABLE_MULTIPLE_BUY:
		def AskSelectQuantity(self, realIndex, canChangeQuantity = True):
			itemIndex = shop.GetItemID(realIndex)
			itemPrice = shop.GetItemPrice(realIndex)
			itemCount = shop.GetItemCount(realIndex)

			itemBuyQuestionDialog = uiCommon.BuyMultipleDialog()
			itemBuyQuestionDialog.SetCanEditQuantity(canChangeQuantity)
			itemBuyQuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerBuyItem(arg))
			itemBuyQuestionDialog.SetConfirmQuantityEvent(lambda arg=True: self.AnswerBuyItem(arg))
			itemBuyQuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerBuyItem(arg))
			itemBuyQuestionDialog.SetItemSlot(realIndex)
			itemBuyQuestionDialog.SetQuantityEscapeEvent(lambda arg=False: self.AnswerBuyItem(arg))
			itemBuyQuestionDialog.Open()
			itemBuyQuestionDialog.pos = realIndex
			if app.ENABLE_MULTIPLE_BUY:
				itemBuyQuestionDialog.checkQuantity = True

			self.itemBuyQuestionDialog = itemBuyQuestionDialog

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

	def SelectItemSlot(self, selectedSlotPos):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		realIndex = self.__ResolveRealIndex(selectedSlotPos)
		if realIndex is None:
			return

		isAttached = mouseModule.mouseController.isAttached()

		if isAttached:
			self.SellAttachedItem()
		else:
			if True == shop.IsMainPlayerPrivateShop():
				return

			curCursorNum = app.GetCursor()
			if app.BUY == curCursorNum:
				self.AskBuyItem(realIndex)
			elif app.SELL == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_SELL_INFO)
			else:
				selectedItemID = shop.GetItemID(realIndex)
				itemCount = shop.GetItemCount(realIndex)

				type = player.SLOT_TYPE_SHOP
				if shop.IsPrivateShop():
					type = player.SLOT_TYPE_PRIVATE_SHOP

				mouseModule.mouseController.AttachObject(self, type, realIndex, selectedItemID, itemCount)
				mouseModule.mouseController.SetCallBack("INVENTORY", ui.__mem_func__(self.DropToInventory))
				snd.PlaySound("sound/ui/pick.wav")

	def DropToInventory(self):
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		self.AskBuyItem(attachedSlotPos)

	def AskBuyItem(self, realIndex):
		if app.ENABLE_MULTIPLE_BUY and not self.__IsCombatZoneIndex(realIndex):
			self.AskSelectQuantity(realIndex, False)
			return

		itemIndex = shop.GetItemID(realIndex)
		itemPrice = shop.GetItemPrice(realIndex)
		itemCount = shop.GetItemCount(realIndex)

		item.SelectItem(itemIndex)
		itemName = item.GetItemName()

		itemBuyQuestionDialog = uiCommon.QuestionDialog()
		if self.__IsCombatZoneIndex(realIndex):
			itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM(itemName, itemCount, localeInfo.NumberToCombatZoneCoinString(itemPrice)))
		else:
			itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM(itemName, itemCount, localeInfo.NumberToMoneyString(itemPrice)))

		itemBuyQuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerBuyItem(arg))
		itemBuyQuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerBuyItem(arg))
		itemBuyQuestionDialog.Open()
		itemBuyQuestionDialog.pos = realIndex
		if app.ENABLE_MULTIPLE_BUY:
			itemBuyQuestionDialog.checkQuantity = False
		self.itemBuyQuestionDialog = itemBuyQuestionDialog

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

	def AnswerBuyItem(self, flag):
		if flag:
			pos = self.itemBuyQuestionDialog.pos
			if app.ENABLE_MULTIPLE_BUY and self.itemBuyQuestionDialog.checkQuantity:
				quantity = self.itemBuyQuestionDialog.GetQuantity()
				net.SendShopBuyPacket(pos, quantity)
			else:
				net.SendShopBuyPacket(pos)

		self.itemBuyQuestionDialog.Close()
		self.itemBuyQuestionDialog = None

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def OverInItem(self, slotIndex):
		realIndex = self.__ResolveRealIndex(slotIndex)
		if realIndex is None:
			return
		if mouseModule.mouseController.isAttached():
			return

		if 0 != self.tooltipItem:
			if app.ENABLE_SHOPEX_RENEWAL:
				PriceType = shop.GetItemPriceType(realIndex)
				if PriceType == 1:
					self.tooltipItem.SetShopItem(realIndex)
				elif PriceType == 2:
					self.tooltipItem.SetShopItemBySecondaryCoin(realIndex)
				else:
					self.tooltipItem.SetShopItemByShopEx(realIndex, PriceType)
			else:
				sourceTab = self.__GetSourceTab(realIndex)
				if shop.SHOP_COIN_TYPE_GOLD == shop.GetTabCoinType(sourceTab):
					self.tooltipItem.SetShopItem(realIndex)
				elif self.__IsCombatZoneIndex(realIndex):
					self.tooltipItem.SetShopItemByCombatZoneCoin(realIndex)
				else:
					self.tooltipItem.SetShopItemBySecondaryCoin(realIndex)

	def OverOutItem(self):
		if 0 != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnUpdate(self):
		USE_SHOP_LIMIT_RANGE = 1000

		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xShopStart) > USE_SHOP_LIMIT_RANGE or abs(y - self.yShopStart) > USE_SHOP_LIMIT_RANGE:
			self.Close()

	if app.WJ_ENABLE_TRADABLE_ICON:
		def CantSellInvenItem(self, slotIndex):
			itemIndex = player.GetItemIndex(slotIndex)

			if itemIndex:
				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0: #봉인아이템 걸러냄.
						return True

				return player.IsAntiFlagBySlot(slotIndex, item.ANTIFLAG_SELL)
			return False

		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

		def OnTop(self):
			if not self.interface:
				return

			if shop.IsPrivateShop():
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()
			else:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_SHOP)
				self.interface.RefreshMarkInventoryBag()

class MallPageDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()

	def Open(self):
		scriptLoader = ui.PythonScriptLoader()
		scriptLoader.LoadScriptFile(self, "uiscript/mallpagedialog.py")

		self.GetChild("titlebar").SetCloseEvent(ui.__mem_func__(self.Close))

		(x, y) = self.GetGlobalPosition()
		x += 10
		y += 30

		MALL_PAGE_WIDTH = 600
		MALL_PAGE_HEIGHT = 480

		app.ShowWebPage(
			"http://metin2.co.kr/08_mall/game_mall/login_fail.htm", 
			(x, y, x + MALL_PAGE_WIDTH, y + MALL_PAGE_HEIGHT))

		self.Lock()
		self.Show()

	def Close(self):
		#app.HideWebPage()
		self.Unlock()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True
