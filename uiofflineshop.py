import ui
import net
import player
import mouseModule
import slotwindowpolicy
import uitooltip
import item
import chat
import localeInfo
import uiCommon
import chr
import background
import uimyshopdecoration as uiMyShopDecoration
import systemSetting
import chrmgr
import app
import osfInfo
import uiScriptLocale
import os

#TODO background.GlobalPositionToMapInfo(x, y)

OFFLINE_SHOP_CHR_VID = 1000000
OFFLINE_SHOP_CLOSED_RACE = 30001

OFFLINESHOP_TIME_LIMIT = 60*60*24*30

if app.WJ_ENABLE_TRADABLE_ICON:
	INVENTORY_PAGE_SIZE = player.INVENTORY_PAGE_SIZE
	if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
		SPECIAL_INVENTORY_PAGE_SIZE = player.SPECIAL_INVENTORY_PAGE_SIZE

def debug(msg):
	chat.AppendChat(chat.CHAT_TYPE_GUILD, "<DEBUG> {}".format(msg))
	
	import dbg
	dbg.TraceError("<DEBUG> {}".format(msg))

OfflineShopManagerInstance = None
def GetOfflineShopManager():
	global OfflineShopManagerInstance
	if not OfflineShopManagerInstance:
		OfflineShopManagerInstance = Manager()
	return OfflineShopManagerInstance

def ClearOfflineShopManager():
	global OfflineShopManagerInstance
	if OfflineShopManagerInstance:
		OfflineShopManagerInstance = None

class Manager(object):

	def __init__(self):
		net.SetOfflineShopManagerHandler(self)
		
		self.__managerWindow = ManagerWindow()
		self.__managerWindow.Hide()
		
		self.__shops = {}
		self.__advBoards = {}
		self.__avgPriceDialogs = {}
	
	def __del__(self):
		pass
		#net.SetOfflineShopManagerHandler(None)

	def SetGameWindowInstance(self, gameWindowInstance):
		self.__gameWindowInstance = gameWindowInstance
	
	def GetGameWindowInstance(self):
		return self.__gameWindowInstance
	
	def Destroy(self):
		self.Clear()
		self.ClearMyShops()
		
	
	def Clear(self):
		for _, board in self.__advBoards.items():
			board.Hide()
			del board
		
		self.__advBoards = {}
		
		for _, shop in self.__shops.items():
			shop.Hide()
			del shop
		
		self.__shops = {}
	
	def ToggleWindow(self):
		if self.__managerWindow.IsShow():
			self.__managerWindow.Hide()
		else:
			self.__managerWindow.Show()

	def TryOpenMyShop(self):
		return self.__managerWindow.TryOpenMyShop()

	def HideAllWindows(self):
		self.__managerWindow.Hide()
		
		for id, shop in self.__shops.items():
			shop.Hide()
		
		self.__shops = {}
	
	def ClearMyShops(self):
		self.__managerWindow.Clear()
	
	def UpdateMyShop(self, id, name):
		self.__managerWindow.UpdateShop(id, name)
	
	def DestroyMyShop(self, id):
		self.__managerWindow.DestroyShop(id)
	
	def OnUpdate(self):
		deleteList = []
		
		for vid, board in self.__advBoards.items():
			if not chr.HasInstance(vid):
				deleteList.append(vid)
				continue
				
			# chr.SelectInstance(vid)
			distance = player.GetCharacterDistance(vid)
			if not systemSetting.IsShowSalesText() or distance > osfInfo.SHOPNAMES_RANGE:
				board.Hide()
			elif not board.IsShow():
				board.Show()
					
		for vid in deleteList:
			self.__advBoards[vid].Hide()
			del self.__advBoards[vid]
	
	def OnSpawnShop(self, id, vid, type, shopName):
		osfInfo.SHOP_VID[id] = vid
	
		if vid in self.__advBoards:
			self.__advBoards[vid].Hide()
			del self.__advBoards[vid]
		
		advBoard = _AdvertismentWindow(id, vid, type, shopName)
		advBoard.Show()
		
		self.__advBoards[vid] = advBoard
		
		if id in self.__shops:
			self.__shops[id].SetShopName(shopName)
	
	def OnOpenShop(self, id, isMyShop, isClosed):
		isMyShop = isMyShop == 1
		isClosed = isClosed == 1
		
		if isMyShop:
			shop = EditorWindow(id, self.GetGameWindowInstance(), isClosed)
		else:
			shop = ViewerWindow(id, self.GetGameWindowInstance())
		
		shop.Show()
		
		self.__shops[id] = shop

	def RegisterAveragePriceDialog(self, shopId, vnum, count, dlg):
		try:
			key = (int(shopId), int(vnum), int(count))
		except:
			return
		self.__avgPriceDialogs[key] = dlg

	def OnAveragePrice(self, shopId, vnum, count, avgPrice, sampleCount):
		try:
			key = (int(shopId), int(vnum), int(count))
		except:
			return

		dlg = self.__avgPriceDialogs.get(key, None)
		if not dlg:
			return

		try:
			dlg.SetAveragePrice(int(avgPrice), int(sampleCount))
		except:
			try:
				dlg.SetAveragePrice(None)
			except:
				pass

	def GetEditorWindow(self):
		for key in self.__shops:
			if isinstance(self.__shops[key], EditorWindow) and self.__shops[key].IsShow():
				return self.__shops[key]
		return None
	
	def OnCloseShop(self, id):
		if id not in self.__shops:
			return
		
		self.__shops[id].Hide()
		del self.__shops[id]

	def IsShow(self):
		if self.__managerWindow.IsShow():
			return True
		for shop in self.__shops.values():
			if shop.IsShow():
				return True
		return False

class AdvertismentBoard(ui.Window):
	TYPES = ("default", "ice", "wing", "fire", "paper", "ribon")
	
	BASE_PATH = "d:/ymir work/ui/game/myshop_deco/"
	
	BOTTOM = BASE_PATH + "{}/p_{}_bottom.tga"
	LEFT_BOTTOM = BASE_PATH + "{}/p_{}_left_bottom.tga"
	LEFT_TOP = BASE_PATH + "{}/p_{}_left_top.tga"
	RIGHT_BOTTOM = BASE_PATH + "{}/p_{}_right_bottom.tga"
	RIGHT_TOP = BASE_PATH + "{}/p_{}_right_top.tga"
	TOP = BASE_PATH + "{}/p_{}_top.tga"
	
	HEIGHT = 32
	CORNER_WIDTH = 48
	LINE_WIDTH = 16
	
	def __init__(self, type = "default"):
		ui.Window.__init__(self, "UI_BOTTOM")
		
		self.__corners = {'LB': None, 'LT': None, 'RB': None, 'RT': None}
		for key in self.__corners:
			corner = ui.ImageBox()
			corner.SetParent(self)
			corner.AddFlag("attach")
			corner.AddFlag("not_pick")
			corner.Show()
			
			self.__corners[key] = corner
		
		self.__lines = {'B': None, 'T': None}
		for key in self.__lines:
			line = ui.ExpandedImageBox()
			line.SetParent(self)
			line.AddFlag("attach")
			line.AddFlag("not_pick")
			line.Show()
			
			self.__lines[key] = line
		
		# Always set images
		if isinstance(type, int):
			if type < 0 or type >= len(self.TYPES):
				type = self.TYPES[0]
			else:
				type = self.TYPES[type]
		elif not type in self.TYPES:
			type = self.TYPES[0]
		
		self.SetType(type)
	
	def __del__(self):
		ui.Window.__del__(self)
	
	def Destroy(self):
		ui.Window.Destroy(self)

		self.__corners = None
		self.__lines = None

	def SetType(self, type):
		if not type in self.TYPES:
			return
		
		corners = {'LB': self.LEFT_BOTTOM, 'LT': self.LEFT_TOP, 'RB': self.RIGHT_BOTTOM, 'RT': self.RIGHT_TOP}
		for key, corner in self.__corners.items():
			corner.LoadImage(corners[key].format(type, type))
		
		lines = {'B': self.BOTTOM, 'T': self.TOP}
		for key, line in self.__lines.items():
			line.LoadImage(lines[key].format(type, type))
		
		self.SetWidth(self.GetWidth())
	
	def SetSize(self, width, _):
		self.SetWidth(width)
	
	def SetWidth(self, width):
		width = max(self.CORNER_WIDTH * 2, width)
		height = self.HEIGHT * 2
		
		ui.Window.SetSize(self, width, height)
		
		self.__corners['LB'].SetPosition(0, height - self.HEIGHT)
		self.__corners['LT'].SetPosition(0, 0)
		self.__corners['RB'].SetPosition(width - self.CORNER_WIDTH, height - self.HEIGHT)
		self.__corners['RT'].SetPosition(width - self.CORNER_WIDTH, 0)
		self.__lines['B'].SetPosition(self.CORNER_WIDTH, height - self.HEIGHT)
		self.__lines['T'].SetPosition(self.CORNER_WIDTH, 0)
		
		horizontalPercentage = -1.0 + float(width - self.CORNER_WIDTH * 2) / float(self.LINE_WIDTH)
		for line in self.__lines.values():
			line.SetRenderingRect(0, 0, horizontalPercentage, 0)

class _AdvertismentWindow(AdvertismentBoard):
	def __init__(self, id, vid, type, shopName):
		AdvertismentBoard.__init__(self, type)
		
		self.__vid = vid
		
		self.__shopName = ui.TextLine()
		self.__shopName.SetParent(self)
		self.__shopName.SetWindowHorizontalAlignCenter()
		self.__shopName.SetWindowVerticalAlignCenter()
		self.__shopName.SetHorizontalAlignCenter()
		self.__shopName.SetVerticalAlignCenter()
		self.__shopName.SetPackedFontColor(0xFFCACACA)
		self.__shopName.UpdateRect()
		self.__shopName.Show()
		
		self.SetShopName(shopName)
	
	def __del__(self):
		AdvertismentBoard.__del__(self)
		del self.__shopName
	
	def Destroy(self):
		AdvertismentBoard.Destroy(self)

		self.__shopName = None
	def Show(self):
		self.Reposition()
		
		AdvertismentBoard.Show(self)
	
	def Reposition(self):
		(x, y) = chr.GetProjectPosition(self.__GetVID(), 220)
		self.SetPosition(x - self.GetWidth() // 2, y - self.GetHeight() // 2)
	
	def SetShopName(self, shopName):
		self.__shopName.SetText(shopName)
		self.SetWidth(len(shopName) * 6 + 48 * 2)
	
	def __GetVID(self):
		return self.__vid
	
	def OnMouseLeftButtonUp(self):
		if player.GetCharacterDistance(self.__GetVID()) > 8000:
			return
		
		net.SendOnClickPacket(self.__GetVID())
	
	def OnMouseRightButtonUp(self):
		# chr.SelectInstance(self.__GetVID())
		# if chr.HasEffect(chrmgr.EFFECT_SHOP_MARK):
			# chr.DetachEffect(chrmgr.EFFECT_SHOP_MARK)
		# else:
			# chr.AttachEffect(chrmgr.EFFECT_SHOP_MARK)
		
		# chr.SelectInstance(player.GetMainCharacterIndex())
		
		return True
	
	def OnUpdate(self):
		self.Reposition()

class Item:
	VNUM = 0
	COUNT = 0
	SOCKETS = [0 for i in range(player.METIN_SOCKET_MAX_NUM)]
	ATTRIBUTES = [(0, 1) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
	APPLY_RANDOM = [(0, 1) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)]
	PRICE = 0
	SOULBIND = 0
	TRANSMUTATION = 0
	REFINE_ELEMENT = None

class ItemToolTip(uitooltip.ItemToolTip):
	def __init__(self):
		uitooltip.ItemToolTip.__init__(self)
	
	def __del__(self):
		uitooltip.ItemToolTip.__del__(self)
	
	def SetOfflineShopItem(self, item):
		self.ClearToolTip()
		self.SetRefreshFunc(self.SetOfflineShopItem, item)
		refine_element = item.REFINE_ELEMENT if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
		apply_random_list = item.APPLY_RANDOM if app.ENABLE_APPLY_RANDOM else None
		self.AddItemData(item.VNUM, item.SOCKETS, item.ATTRIBUTES, 0, 0, item.SOULBIND, player.INVENTORY, -1, refine_element, apply_random_list, 0)
		self.AppendChangeLookInfoItemVnum(item.TRANSMUTATION)
		self.AppendPrice(item.PRICE)
		self.ClearAddRefreshFunc()
	
	def AppendBuyerName(self, buyerName):
		self.AppendTextLine("Buyer: {}".format(buyerName))

class ManagerWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		
		self.__shops = {}
		self.__myshop = -1
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/offline_shop_manager.py")
		
		self.__shopList = self.GetChild("shops")
		
		self.GetChild("edit").SetEvent(self.__Edit)
		self.GetChild("close").SetEvent(self.__Close)
		self.GetChild("closeAll").SetEvent(self.__CloseAll)

		self.GetChild("board").SetCloseEvent(self.Hide)
	
	def __del__(self):
		ui.ScriptWindow.__del__(self)
	
	def Destroy(self):
		ui.ScriptWindow.Destroy(self)

		self.__shopList = None
	def Clear(self):
		self.__shops = {}
		self.__UpdateList()
	
	def UpdateShop(self, id, name):
		self.__shops[id] = name
		self.__myshop = id
		self.__UpdateList()

	def HasShop(self):
		return self.__myshop != -1

	def DestroyShop(self, id):
		if id not in self.__shops:
			return

		if self.__myshop == id:
			self.__myshop = -1

		del self.__shops[id]
		self.__UpdateList()
	
	def __UpdateList(self):
		self.__shopList.ClearItem()
		for id, name in self.__shops.items():
			self.__shopList.InsertItem(id, name)
	
	def __Edit(self):
		id = self.__shopList.GetSelectedItem()
		if id == 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OFFLINE_SHOP_SELECT_SHOP)
			return
		
		net.SendChatPacket("/open_offline_shop {}".format(id))
	
	def __Close(self):
		id = self.__shopList.GetSelectedItem()
		if id == 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OFFLINE_SHOP_SELECT_SHOP)
			return
		
		net.SendChatPacket("/close_offline_shop {}".format(id))

	def __CloseAll(self):
		for id, _ in self.__shops.items():
			net.SendChatPacket("/close_offline_shop {}".format(id))

	def TryOpenMyShop(self):
		if not self.__myshop in self.__shops:
			# chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OFFLINE_SHOP_NO_SHOP)
			return False

		net.SendChatPacket("/open_offline_shop {}".format(self.__myshop))
		return True

class BuilderWindow(ui.ScriptWindow):

	interface = None
	
	def __init__(self):
		ui.ScriptWindow.__init__(self)
			
		self.interface = None
		
		self.__items = {}
	
		self.__isPositioningMode = False
		self.__npcPosition = player.GetMainCharacterPosition()
		self.__npcRace = 30000
		self.__advertismentBoard = 0
			
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/offline_shop_builder.py")
		
		self.__shopName = self.GetChild("shopName")
		self.__shopName.SetEscapeEvent(self.Close)
		self.__itemGrid = self.GetChild("items")
		# self.__openingTime = self.GetChild("openingTime")
			
		self.__itemGrid.SetSelectEmptySlotEvent(self.__OnSelectEmptySlot)
		self.__itemGrid.SetSelectItemSlotEvent(self.__OnSelectItemSlot)
		self.__itemGrid.SetOverInItemEvent(self.__OnOverInItem)
		self.__itemGrid.SetOverOutItemEvent(self.__OnOverOutItem)
		
		# MULTIPLE_PAGE_UPDATE
		self.__currentPage = 0
		self.__pagesTab = []

		for page in range(4): ## 0, 1, 2, 3
			self.__pagesTab.append(self.GetChild("slot_page_" + str(page+1)))
			self.__pagesTab[page].SetEvent(lambda arg=page: self.__OnClickPage(arg))

		self.__OnClickPage(0, True)
		# MULTIPLE_PAGE_UPDATE

		self.__shopDecoration = uiMyShopDecoration.MyShopDecorationWindow()
		self.__shopDecoration.SetCompleteEvent(self.__OnSelectDecoration)
		self.__shopDecoration.Hide()
			
		self.__priceInput = uiCommon.MoneyInputDialog()
		self.__priceInput.SetTitle(localeInfo.PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE)
		self.__priceInput.SetValue(0)
		self.__priceInput.SetAcceptEvent(self.__OnAcceptInputPrice)
		self.__priceInput.SetCancelEvent(self.__OnCancelInputPrice)
		self.__priceInput.ITEM_INFO = {
			'VNUM' : 0,
			'SLOT_OWNER' : None,
			'SLOT_TYPE' : 0,
			'SLOT_INDEX' : 0,
			'TARGET_SLOT_INDEX' : 0
		}
		self.__priceInput.Hide()
		
		self.__itemToolTip = uitooltip.GetItemToolTipInstance()
		
		self.GetChild("board").SetCloseEvent(self.Close)
		# self.GetChild("position").SetEvent(self.__SelectPosition)
		self.GetChild("decoration").SetEvent(self.__SelectDecoration)
		self.GetChild("submit").SetEvent(self.__Submit)
		# self.GetChild("cancel").SetEvent(self.Close)
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None
		
	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
		self.__shopDecoration.Hide()
		self.__priceInput.Hide()
		self.__itemToolTip.HideToolTip()
		
		del self.__shopDecoration
		del self.__priceInput
		del self.__itemToolTip
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None
	
	def Destroy(self):
		if self.__shopDecoration:
			self.__shopDecoration.Hide()
			
		self.__Reset()
		self.Hide()
		
		ui.ScriptWindow.Destroy(self)
		
		# self.Close()

	def Open(self, openingTime, openGold):
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = []
			if self.inven == None:
				self.inven = self.interface.GetInventoryWnd()
			if self.invenSpecial == None:
				self.invenSpecial = self.interface.GetSpecialInventoryWnd()
				
			self.interface.SetOnTopWindow(player.ON_TOP_WND_PRIVATE_SHOP)
			self.interface.RefreshMarkInventoryBag()
	
		self.__Reset()
				
		self.SetCenterPosition()
		self.Show()
		self.__SpawnPseudoShopKeeper()
		
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = False
	
	def Close(self):
		if self.__shopDecoration:
			self.__shopDecoration.Hide()
		
		self.__Reset()
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()

			self.ItemListIdx = None
		
		if self.IsShow():
			net.SendChatPacket("/cancel_opening_offline_shop")
			
		if app.ENABLE_ANIMATED_WINDOW:
			if self.bClosed == False:
				self.Hide()
		else:
			self.Hide()
			
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = True
		
		self.__PurgePseudoShopKeeper()
		
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
	
	# def __SelectPosition(self):
		# self.__SetPositioningMode(True)
		
	def BindInterfaceClass(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)
		
	if app.WJ_ENABLE_TRADABLE_ICON:
		def OnTop(self):
			if not self.interface:
				return

			self.interface.SetOnTopWindow(player.ON_TOP_WND_PRIVATE_SHOP)
			self.interface.RefreshMarkInventoryBag()
			
	# MULTIPLE_PAGE_UPDATE
	def __OnClickPage(self, page, bIsFirst = False):
		self.__currentPage = page

		for index in range(len(self.__pagesTab)):
			if index == page:
				self.__pagesTab[index].Down()
				continue
			self.__pagesTab[index].SetUp()

		if not bIsFirst:
			self.__RefreshItemGrid()
	# MULTIPLE_PAGE_UPDATE

	def __SelectDecoration(self):
		# pass
		self.__shopDecoration.Show()
		self.__shopDecoration.SetTop()
		self.__shopDecoration.SetFocus()
	
	def __OnSelectDecoration(self):
		skinID = self.__shopDecoration.GetSelectedSkinID()
		bannerID = self.__shopDecoration.GetSelectedBannerID()
		
		if skinID != -1 and osfInfo.SHOP_SKIN_UNLOCKED[skinID] == False:
			chat.AppendChat(1, localeInfo.SHOP_SKIN_NOT_UNLOCKED)
			return
			
		if bannerID != -1 and osfInfo.SHOP_BANNER_UNLOCKED[bannerID] == False:
			chat.AppendChat(1, localeInfo.SHOP_BANNER_NOT_UNLOCKED)
			return
	
		self.__npcRace = self.__shopDecoration.GetSelectedNpcRace()
		
		self.__advertismentBoard = self.__shopDecoration.GetSelectedAdvertismentBoard()
		
		self.__shopDecoration.Hide()
		
		if self.__IsPseudoShopKeeperSpawned():
			self.__PurgePseudoShopKeeper()
			self.__SpawnPseudoShopKeeper()
	
	def __GetNpcRace(self):
		return self.__npcRace
	
	def __Submit(self):
		if len(self.__items) < 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OFFLINE_SHOP_NEED_ITEMS)
			return
		
		shopName = self.__shopName.GetText()
		if len(shopName) < 3 or len(shopName) > 32:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OFFLINE_SHOP_MAX_NAME_LENGTH)
			return
		
		net.SendOfflineShopCreatePacket(shopName,
			self.__npcPosition[0], self.__npcPosition[1],
			self.__npcRace, self.__advertismentBoard,
			self.__items)
		
		self.Close()
	
	def __RefreshItemGrid(self):
		i = self.__itemGrid.GetStartIndex()
		while self.__itemGrid.HasSlot(i):
			checkItemKey = i

			# MULTIPLE_PAGE_UPDATE
			checkItemKey += self.__currentPage*80
			# MULTIPLE_PAGE_UPDATE
			if checkItemKey in self.__items:
				itemInfo = self.__items[checkItemKey]

				itemCount = player.GetItemCount(itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX'])
				self.__itemGrid.SetItemSlot(i, player.GetItemIndex(itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX']), itemCount > 1 and itemCount or 0)
			else:
				self.__itemGrid.ClearSlot(i)
			
			i += 1
		
		self.__itemGrid.RefreshSlot()

	def __Reset(self):
		for k, itemInfo in self.__items.items():
			if itemInfo['SLOT_OWNER']:
				try:
					itemInfo['SLOT_OWNER'].DeactivateSlot(itemInfo['SLOT_INDEX'])
				except:
					pass
		
		self.__items = {}
		self.__shopName.SetText("")
		self.__RefreshItemGrid()
		self.__npcPosition = player.GetMainCharacterPosition()
		self.SetCenterPosition()
		self.__shopDecoration.SetCenterPosition()
		# MULTIPLE_PAGE_UPDATE
		self.__OnClickPage(0)
		# MULTIPLE_PAGE_UPDATE
	
	def __RemoveItem(self, slotIndex):
		if slotIndex not in self.__items:
			return
			
		if app.WJ_ENABLE_TRADABLE_ICON:
			pos = self.__items[slotIndex]['SLOT_INDEX']
			for i in range(len(self.ItemListIdx)):
				if self.ItemListIdx[i] == pos:
					del self.ItemListIdx[i]
					break
		
		if self.__items[slotIndex]['SLOT_OWNER']:
			try:
				self.__items[slotIndex]['SLOT_OWNER'].DeactivateSlot(self.__items[slotIndex]['SLOT_INDEX'])
			except:
				pass
		
		del self.__items[slotIndex]
		self.__RefreshItemGrid()
	
	def __OnAcceptInputPrice(self):
		price = self.__priceInput.GetValue()
		if price < 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OFFLINE_SHOP_INPUT_PRICE)
			return
		
		newItemInfo = self.__priceInput.ITEM_INFO
		
		for slotIndex, itemInfo in list(self.__items.items()):
			if itemInfo['SLOT_TYPE'] == newItemInfo['SLOT_TYPE'] and itemInfo['SLOT_INDEX'] == newItemInfo['SLOT_INDEX']:
				self.__RemoveItem(slotIndex)
				break
		
		self.__items[newItemInfo['TARGET_SLOT_INDEX']] = {
			'SLOT_OWNER' : newItemInfo['SLOT_OWNER'],
			'SLOT_TYPE' : newItemInfo['SLOT_TYPE'],
			'SLOT_INDEX' : newItemInfo['SLOT_INDEX'],
			'PRICE' : price
		}
		
		if newItemInfo['SLOT_OWNER']:
			try:
				newItemInfo['SLOT_OWNER'].ActivateSlot(newItemInfo['SLOT_INDEX'])
			except:
				pass
		
		osfInfo.SaveItemPrice(player.GetItemIndex(newItemInfo['SLOT_TYPE'], newItemInfo['SLOT_INDEX']), player.GetItemCount(newItemInfo['SLOT_TYPE'], newItemInfo['SLOT_INDEX']), int(price))
		
		self.__priceInput.SetValue(0)
		self.__priceInput.Hide()
		
		self.__RefreshItemGrid()
		
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
		
		return True
	
	def __OnCancelInputPrice(self):
		if app.WJ_ENABLE_TRADABLE_ICON:
			try:
				pos = self.__priceInput.ITEM_INFO['SLOT_INDEX']
			except:
				pos = None

			itemList = getattr(self, "ItemListIdx", None)
			if pos is not None and isinstance(itemList, list):
				for i in range(len(itemList)):
					if itemList[i] == pos:
						del itemList[i]
						break

			if pos is None:
				pos = -1

			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if self.inven or self.invenSpecial:
					page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
					special_page = self.invenSpecial.GetInventoryPageIndex()

					if (page * INVENTORY_PAGE_SIZE) <= pos < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						idx = pos - (page * INVENTORY_PAGE_SIZE)
						wnd = getattr(getattr(self, "inven", None), "wndItem", None)
						if hasattr(wnd, "SetCanMouseEventSlot"):
							wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 0:
						if (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.SKILL_BOOK_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 1:
						if (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 2:
						if (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.STONE_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 3:
						if (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.GIFT_BOX_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 4:
						if (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.SWITCH_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 5:
						if (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.COSTUME_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

			else:
				if self.inven:
					page = self.inven.GetInventoryPageIndex() # range 0 ~ 1

					if (page * INVENTORY_PAGE_SIZE) <= pos < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						idx = pos - (page * INVENTORY_PAGE_SIZE)
						wnd = getattr(getattr(self, "inven", None), "wndItem", None)
						if hasattr(wnd, "SetCanMouseEventSlot"):
							wnd.SetCanMouseEventSlot(idx)
					
		self.__priceInput.ITEM_INFO = {
			'VNUM' : 0,
			'SLOT_OWNER' : None,
			'SLOT_TYPE' : 0,
			'SLOT_INDEX' : 0,
			'TARGET_SLOT_INDEX' : 0
		}
		self.__priceInput.SetValue(0)
		self.__priceInput.Hide()
		
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
			
	#if ENABLE_ADD_FAST_ITEM:
	def AddFastItem(self):
		self.__OnSelectEmptySlot(-1)
	#endif ENABLE_ADD_FAST_ITEM
	
	def __OnSelectEmptySlot(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			attachedOwner = mouseModule.mouseController.GetAttachedOwner()
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotIndex = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()
			
			self.__itemToolTip.HideToolTip()

			attachedInventoryType = slotwindowpolicy.ItemWindowForSlotType(attachedSlotType)
			if attachedInventoryType == player.RESERVED_WINDOW:
				return
			if attachedInventoryType == player.INVENTORY and player.IsEquipmentSlot(attachedSlotIndex):
				return

			self.RequestAddItem(attachedInventoryType, attachedSlotIndex, slotIndex, attachedOwner)

	#if ENABLE_ADD_FAST_ITEM:
	def GetEmptySlot(self, newItemSize):
		# offline shop window = 9x10
		offlineShopWidth = 10
		offlineShopHeight = 8
		OFFLINESHOP_SLOT_COUNT = offlineShopWidth * offlineShopHeight
		
		tempItemGrid = {}
		
		for i in range(OFFLINESHOP_SLOT_COUNT*4):
			if i in self.__items:
				itemInfo = self.__items[i]
				itemVnum = player.GetItemIndex(itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX'])

				item.SelectItem(itemVnum)
				itemWidth, itemHeight = item.GetItemSize()
				
				row = 0
				while row < itemHeight:
					p = i + (row * 10)
					tempItemGrid[p] = 1
					row = row + 1

		for i in range(OFFLINESHOP_SLOT_COUNT):
			if i not in tempItemGrid:
				if newItemSize == 1:
					return i
				elif newItemSize == 2:
					if i+9 < OFFLINESHOP_SLOT_COUNT and i+9 not in tempItemGrid:
						return i
				elif newItemSize == 3:
					if i+9 < OFFLINESHOP_SLOT_COUNT and i+9+9 < OFFLINESHOP_SLOT_COUNT and i+9 not in tempItemGrid and i+9+9 not in tempItemGrid:
						return i

		return -1
	#endif ENABLE_ADD_FAST_ITEM
	
	def RequestAddItem(self, slotType, slotIndex, targetSlotIndex = -1, owner = None):
			itemVnum = player.GetItemIndex(slotType, slotIndex)
			itemCount = player.GetItemCount(slotType, slotIndex)
			
			item.SelectItem(itemVnum)
			if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP): #or player.HasItemSpecialFlag(item.SPECIAL_FLAG_ANTI_SHOP, slotType, slotIndex):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PRIVATE_SHOP_CANNOT_SELL_ITEM)
				return

			if targetSlotIndex < 0:
				itemWidth, itemHeight = item.GetItemSize()
				targetSlotIndex = self.GetEmptySlot(itemHeight)
				if targetSlotIndex < 0:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_ADD_MORE_ITEMS)
					return
			
			self.__priceInput.ITEM_INFO = {
				'VNUM' : itemVnum,
				'SLOT_OWNER' : owner,
				'SLOT_TYPE' : slotType,
				'SLOT_INDEX' : slotIndex,
				'TARGET_SLOT_INDEX' : targetSlotIndex + 80*self.__currentPage,
			}
			GetOfflineShopManager().RegisterAveragePriceDialog(0, itemVnum, itemCount, self.__priceInput)
			self.__priceInput.SetAveragePriceText("~ …")
			net.SendOfflineShopRequestAveragePrice(0, itemVnum, itemCount)

			self.__priceInput.Open()
			
			savedPrice = osfInfo.ReadItemPrice(itemVnum, itemCount)
			if savedPrice > 0:
				self.__priceInput.SetValue(savedPrice)
				
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.ItemListIdx.append(slotIndex)
	
	def __OnSelectItemSlot(self, slotIndex):
		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		self.__RemoveItem(slotIndex)
	
	def __OnOverInItem(self, slotIndex):
		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		
		if slotIndex not in self.__items:
			return
		
		itemInfo = self.__items[slotIndex]
		
		self.__itemToolTip.SetInventoryItem(itemInfo['SLOT_INDEX'], itemInfo['SLOT_TYPE'])
		
		if app.ENABLE_SOUL_BIND_SYSTEM:
			self.__itemToolTip.AppendSealInformation(itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX'])
			
		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.__itemToolTip.AppendChangeLookInformation(itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX'])
			
		self.__itemToolTip.AppendPrice(itemInfo['PRICE'])
		self.__itemToolTip.ShowToolTip()
	
	def __OnOverOutItem(self):
		self.__itemToolTip.HideToolTip()
		
	def __SetPositioningMode(self, positioningMode):
		self.__isPositioningMode = positioningMode
	
	def IsPositioningMode(self):
		return self.__isPositioningMode
	
	def __SpawnPseudoShopKeeper(self):
		chr.CreateInstance(OFFLINE_SHOP_CHR_VID)
		chr.SelectInstance(OFFLINE_SHOP_CHR_VID)
		chr.SetVirtualID(OFFLINE_SHOP_CHR_VID)
		chr.SetInstanceType(chr.INSTANCE_TYPE_NPC)
		
		chr.SetRace(self.__GetNpcRace())
		# chr.SetArmor(0)
		chr.Refresh()
		chr.SetLoopMotion(chr.MOTION_WAIT)
		
		chr.SetPixelPosition(*self.__npcPosition)
	
	def __IsPseudoShopKeeperSpawned(self):
		return chr.HasInstance(OFFLINE_SHOP_CHR_VID)
	
	def __PurgePseudoShopKeeper(self):
		if self.__IsPseudoShopKeeperSpawned():
			chr.DeleteInstanceByFade(OFFLINE_SHOP_CHR_VID)
	
	def POSITIONING_OnMouseLeftButtonUp(self):
		if self.IsPositioningMode():
			self.__SetPositioningMode(False)
			return True
		
		return False
	
	def OnUpdate(self):
		if self.IsPositioningMode():
			if not self.__IsPseudoShopKeeperSpawned():
				self.__SpawnPseudoShopKeeper()
			
			self.__npcPosition = background.GetPickingPoint()
			chr.SelectInstance(OFFLINE_SHOP_CHR_VID)
			chr.SetPixelPosition(*self.__npcPosition)
			
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
		self.Close()

class EditorWindow(ui.ScriptWindow):
	__openingTime = None
	interface = None
	
	if app.ENABLE_ANIMATED_WINDOW:
		bClosed = False
	
	def __init__(self, id, gameWnd, isClosed):
		ui.ScriptWindow.__init__(self)
		
		self.__id = id
		self.__itemStock = {}
		#self.__previewFunc = gameWnd.interface.OpenPreviewWindow
		
		(self.__startX, self.__startY, z) = player.GetMainCharacterPosition()
		self.__closingTime = 0
		self.interface = gameWnd.interface

		net.RegisterOfflineShopHandler(self.__GetId(), self)
		
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/offline_shop_editor.py")
		
		self.__confirmation = uiCommon.QuestionDialog()
		self.__confirmation.SetCancelEvent(self.__confirmation.Hide)
		self.__confirmation.Hide()
		
		self.__priceInput = uiCommon.MoneyInputDialog()
		self.__priceInput.SetTitle(localeInfo.PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE)
		self.__priceInput.SetValue(0)
		self.__priceInput.SetAcceptEvent(self.__OnAcceptInputPrice)
		self.__priceInput.SetCancelEvent(self.__OnCancelInputPrice)
		self.__priceInput.ITEM_INFO = {
			'VNUM' : 0,
			'SLOT_TYPE' : 0,
			'SLOT_INDEX' : 0,
			'TARGET_SLOT_INDEX' : 0
		}
		self.__priceInput.Hide()
		
		self.__withdrawInput = uiCommon.MoneyInputDialog()
		self.__withdrawInput.SetTitle(uiScriptLocale.OFFLINE_SHOP_SHOP_WITHDRAW)
		self.__withdrawInput.SetValue(0)
		self.__withdrawInput.SetAcceptEvent(self.__OnWithdraw)
		self.__withdrawInput.SetCancelEvent(self.__OnCancelWithdraw)
		self.__withdrawInput.Hide()

		self.__itemToolTip = uitooltip.GetItemToolTipInstance()
		self.__itemToolTip.BindInterfaceClass(gameWnd.interface)
		
		self.__board = self.GetChild("board")
		self.__board.SetCloseEvent(self.Hide)
		
		self.__items = self.GetChild("items")
		self.__items.SAFE_SetButtonEvent("LEFT", "EMPTY", self.__OnSelectEmptySlot)
		self.__items.SAFE_SetButtonEvent("LEFT", "EXIST", self.OnClickItemSlot)
		self.__items.SAFE_SetButtonEvent("RIGHT", "EXIST", self.OnClickItemSlot)
		self.__items.SetOverInItemEvent(self.__OnOverInItem)
		self.__items.SetOverOutItemEvent(self.__OnOverOutItem)
		
		# MULTIPLE_PAGE_UPDATE
		self.__currentPage = 0
		self.__pagesTab = []

		for page in range(4): ## 0, 1, 2, 3
			self.__pagesTab.append(self.GetChild("slot_page_" + str(page+1)))
			self.__pagesTab[page].SetEvent(lambda arg=page: self.__OnClickPage(arg))

		self.__OnClickPage(0, True)
		# MULTIPLE_PAGE_UPDATE

		self.__openingTime = self.GetChild("openingTime")
		self.__gold = self.GetChild("gold")
		
		self.__nameEdit = self.GetChild("NameEdit")
		self.__nameEdit.SetEscapeEvent(self.Hide)
		self.__nameAccept = self.GetChild("NameAccept")
		#self.__search = self.GetChild("search")
		self.__close = self.GetChild("close")
		self.__reopen = self.GetChild("reopen")
		self.__getAllItems = self.GetChild("GetAllItemsButton")
		self.__historyItems = self.GetChild("HistoryItemsButton")

		self.__helpbtn = self.GetChild("ShopFAQButton")
		self.__warpbtn = self.GetChild("WarpButton")
		self.__warpbtn.SetEvent(self.__AskWarp)
		self.__warpbtn.Hide()
		self.__nameAccept.SetEvent(self.__OnChangeName)
		#self.__search.SetEvent(gameWnd.interface.OpenShopSearchWindow)
		self.__close.SetEvent(self.__AskClose)
		self.__reopen.SetEvent(self.__AskReopen)
		self.__getAllItems.SetEvent(self.__AskGetAllItems)
		self.__historyItems.SetEvent(gameWnd.interface.OpenSellHistoryWindow)

		self.GetChild("goldBackground").SetMouseLeftButtonDownEvent(ui.__mem_func__(self.__OpenWithdraw))
		self.__SetClosed(isClosed)
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None
	
	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
		self.__confirmation.Hide()
		self.__priceInput.Hide()
		self.__withdrawInput.Hide()
		self.__itemToolTip.HideToolTip()
		del self.__confirmation
		del self.__priceInput
		del self.__withdrawInput
		del self.__itemToolTip	
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None
	
	def Destroy(self):
		if self.__confirmation:
			self.__confirmation = None
		ui.ScriptWindow.Destroy(self)

	def __GetId(self):
		return self.__id

	def __OnAcceptInputPrice(self):
		price = self.__priceInput.GetValue()
		if price < 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OFFLINE_SHOP_INPUT_PRICE)
			return
		
		itemInfo = self.__priceInput.ITEM_INFO
		net.SendOfflineShopAddItemPacket(self.__GetId(), itemInfo['TARGET_SLOT_INDEX'], itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX'], price)

		osfInfo.SaveItemPrice(player.GetItemIndex(itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX']), player.GetItemCount(itemInfo['SLOT_TYPE'], itemInfo['SLOT_INDEX']), int(price))

		self.__priceInput.SetValue(0)
		self.__priceInput.Hide()
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			itemList = getattr(self, "ItemListIdx", None)
			if isinstance(itemList, list):
				pos = itemInfo['SLOT_INDEX']
				for i in range(len(itemList)):
					if itemList[i] == pos:
						del itemList[i]
						break
		
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
		
		return True
	
	def __OnCancelInputPrice(self):
		if app.WJ_ENABLE_TRADABLE_ICON:
			try:
				pos = self.__priceInput.ITEM_INFO['SLOT_INDEX']
			except:
				pos = None

			itemList = getattr(self, "ItemListIdx", None)
			if pos is not None and isinstance(itemList, list):
				for i in range(len(itemList)):
					if itemList[i] == pos:
						del itemList[i]
						break

			if pos is None:
				pos = -1

			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if self.inven or self.invenSpecial:
					page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
					special_page = self.invenSpecial.GetInventoryPageIndex()

					if (page * INVENTORY_PAGE_SIZE) <= pos < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						idx = pos - (page * INVENTORY_PAGE_SIZE)
						wnd = getattr(getattr(self, "inven", None), "wndItem", None)
						if hasattr(wnd, "SetCanMouseEventSlot"):
							wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 0:
						if (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.SKILL_BOOK_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 1:
						if (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 2:
						if (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.STONE_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 3:
						if (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.GIFT_BOX_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 4:
						if (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.SWITCH_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

					if self.invenSpecial.GetInventoryType() == 5:
						if (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= pos < (item.COSTUME_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = pos - (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							wnd = getattr(getattr(self, "invenSpecial", None), "wndItem", None)
							if hasattr(wnd, "SetCanMouseEventSlot"):
								wnd.SetCanMouseEventSlot(idx)

			else:
				if self.inven:
					page = self.inven.GetInventoryPageIndex() # range 0 ~ 1

					if (page * INVENTORY_PAGE_SIZE) <= pos < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						idx = pos - (page * INVENTORY_PAGE_SIZE)
						wnd = getattr(getattr(self, "inven", None), "wndItem", None)
						if hasattr(wnd, "SetCanMouseEventSlot"):
							wnd.SetCanMouseEventSlot(idx)
	
		self.__priceInput.ITEM_INFO = {
			'VNUM' : 0,
			'SLOT_TYPE' : 0,
			'SLOT_INDEX' : 0,
			'TARGET_SLOT_INDEX' : 0
		}
		self.__priceInput.SetValue(0)
		self.__priceInput.Hide()
		
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
			
	#if ENABLE_ADD_FAST_ITEM:
	def AddFastItem(self):
		self.__OnSelectEmptySlot(-1)
		
	def GetEmptySlot(self, newItemSize):
		# offline shop window = 9x10
		offlineShopWidth = 10
		offlineShopHeight = 8
		OFFLINESHOP_SLOT_COUNT = offlineShopWidth * offlineShopHeight
		
		tempItemGrid = {}
		
		for i in range(OFFLINESHOP_SLOT_COUNT*4):
			if i in self.__itemStock:
				itemInfo = self.__itemStock[i]
				itemVnum = itemInfo.VNUM

				item.SelectItem(itemVnum)
				itemWidth, itemHeight = item.GetItemSize()
				
				row = 0
				while row < itemHeight:
					p = i + (row * 10)
					tempItemGrid[p] = 1
					row = row + 1

		for i in range(OFFLINESHOP_SLOT_COUNT):
			if i not in tempItemGrid:
				if newItemSize == 1:
					return i
				elif newItemSize == 2:
					if i+9 < OFFLINESHOP_SLOT_COUNT and i+9 not in tempItemGrid:
						return i
				elif newItemSize == 3:
					if i+9 < OFFLINESHOP_SLOT_COUNT and i+9+9 < OFFLINESHOP_SLOT_COUNT and i+9 not in tempItemGrid and i+9+9 not in tempItemGrid:
						return i
		return -1
	#endif ENABLE_ADD_FAST_ITEM
	
	def __OnSelectEmptySlot(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotIndex = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			self.__itemToolTip.HideToolTip()

			if attachedSlotType == player.SLOT_TYPE_OFFLINE_SHOP:
				net.SendOfflineShopMoveItemPacket(self.__GetId(), attachedSlotIndex, slotIndex)
			elif slotwindowpolicy.IsOwnedItemSlotType(attachedSlotType):
				attachedInventoryType = slotwindowpolicy.ItemWindowForSlotType(attachedSlotType)
				if attachedInventoryType == player.RESERVED_WINDOW:
					return
				if attachedInventoryType == player.INVENTORY and player.IsEquipmentSlot(attachedSlotIndex):
					return

				self.RequestAddItem(attachedInventoryType, attachedSlotIndex, slotIndex)

	def __GetAvailItemPrice(self, vnum, count):
		singlePrice = 0

		i = self.__items.GetStartIndex()
		while self.__items.HasSlot(i):
			if i in self.__itemStock:
				itemInfo = self.__itemStock[i]
				if itemInfo.VNUM == vnum:
					if itemInfo.COUNT == count:
						return itemInfo.PRICE
					elif singlePrice == 0:
						singlePrice = itemInfo.PRICE // itemInfo.COUNT

			i += 1

		return singlePrice * count

	def RequestAddItem(self, slotType, slotIndex, targetSlotIndex = -1, owner = None):
			itemVnum = player.GetItemIndex(slotType, slotIndex)
			itemCount = player.GetItemCount(slotType, slotIndex)
			
			item.SelectItem(itemVnum)
			if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):# or player.HasItemSpecialFlag(item.SPECIAL_FLAG_ANTI_SHOP, slotType, slotIndex):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PRIVATE_SHOP_CANNOT_SELL_ITEM)
				return

			if targetSlotIndex < 0:
				itemWidth, itemHeight = item.GetItemSize()
				targetSlotIndex = self.GetEmptySlot(itemHeight)
				if targetSlotIndex < 0:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_ADD_MORE_ITEMS)
					return
			
			self.__priceInput.ITEM_INFO = {
				'VNUM' : itemVnum,
				'SLOT_TYPE' : slotType,
				'SLOT_INDEX' : slotIndex,
				'TARGET_SLOT_INDEX' : targetSlotIndex + 80*self.__currentPage
			}

			GetOfflineShopManager().RegisterAveragePriceDialog(self.__GetId(), itemVnum, itemCount, self.__priceInput)
			self.__priceInput.SetAveragePriceText("~ …")
			net.SendOfflineShopRequestAveragePrice(self.__GetId(), itemVnum, itemCount)

			self.__priceInput.Open()
			
			savedPrice = osfInfo.ReadItemPrice(itemVnum, itemCount)
			if savedPrice > 0:
				self.__priceInput.SetValue(savedPrice)
				
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.ItemListIdx.append(slotIndex)
	
	def __OnSelectItemSlot(self, slotIndex):
		return
		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		itemInfo = self.__itemStock[slotIndex]
		mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_OFFLINE_SHOP, slotIndex, itemInfo.VNUM, itemInfo.COUNT)
	
	def OnClickItemSlot(self, slotIndex, destinationSlot = -1):
		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		self.__AskRemove(slotIndex, destinationSlot)
	
	def __OnOverInItem(self, slotIndex):
		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		if slotIndex not in self.__itemStock:
			return

		self.__itemToolTip.SetOfflineShopItem(self.__itemStock[slotIndex])
		self.__itemToolTip.ShowToolTip()

	def __OnOverOutItem(self):
		self.__itemToolTip.HideToolTip()
	
	def __AskRemove(self, slotIndex, destinationSlot = -1):
		if slotIndex not in self.__itemStock:
			return

		itemInfo = self.__itemStock[slotIndex]

		item.SelectItem(itemInfo.VNUM)

		self.__confirmation.SetText(localeInfo.OFFLINE_SHOP_REMOVE_ITEM_QUESTION.format(item.GetItemName()))
		self.__confirmation.SetAcceptEvent(lambda : self.__OnRemove(slotIndex, destinationSlot))
		self.__confirmation.Open()

	def __OnRemove(self, slotIndex, destinationSlot):
		if destinationSlot != -1:
			net.SendOfflineShopRemoveItemPacket(self.__GetId(), slotIndex, player.SLOT_TYPE_INVENTORY, destinationSlot)
		else:
			net.SendOfflineShopRemoveItemPacket(self.__GetId(), slotIndex, player.SLOT_TYPE_NONE, 0xffff)
		self.__confirmation.Hide()

	def __OpenWithdraw(self):
		self.__withdrawInput.Open()

	def __OnWithdraw(self):
		gold = self.__withdrawInput.GetText()
		if len(gold) < 1:
			return
		if osfInfo.MONEY_K_FORMAT:
			if 'k' in gold:
				gold = str(osfInfo.FormatMoneyToK(gold))
			elif 'K' in gold:
				gold = str(osfInfo.FormatMoneyToK(gold))
				
		try:
			intGold = int(gold)
		except ValueError:
			intGold = 0

		net.SendOfflineShopWithdrawPacket(self.__GetId(), intGold)
		
		self.__withdrawInput.SetValue(0)
		self.__withdrawInput.Hide()
		
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
		
	def __OnCancelWithdraw(self):
		self.__withdrawInput.Hide()
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
	
	def __OnChangeName(self):
		shopName = self.__nameEdit.GetText()
		if len(shopName) < 3 or len(shopName) > 32:
			return
		
		net.SendOfflineShopChangeNamePacket(self.__GetId(), shopName)
		
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
		
		return True
		
	def __OnCancelChangeName(self):
		game = GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
		
	def __AskGetAllItems(self):
		self.__confirmation.SetText(localeInfo.OFFLINE_SHOP_GET_ALL_ITEMS_CONFIRM)
		self.__confirmation.SetAcceptEvent(self.__OnGetAllItems)
		self.__confirmation.Open()
		
	def __AskHistoryButton(self):
		self.Hide()
		self.interface.OpenSellHistoryWindow()
	
	def __OnGetAllItems(self):
		net.SendOfflineShopGetAllItems(self.__GetId())
		self.__confirmation.Hide()
		
	def __AskWarp(self):
		self.__confirmation.SetText(localeInfo.PRIVATE_SHOP_WARP_QUESTION)
		self.__confirmation.SetAcceptEvent(self.__OnWarp)
		self.__confirmation.Open()
	
	def __OnWarp(self):
		self.__confirmation.Hide()
		net.SendOfflineShopWarpPacket(self.__GetId())
	
	def __AskClose(self):
		self.__confirmation.SetText(localeInfo.PRIVATE_SHOP_CLOSE_QUESTION)
		self.__confirmation.SetAcceptEvent(self.__OnClose)
		self.__confirmation.Open()
	
	def __OnClose(self):
		net.SendOfflineShopClosePacket(self.__GetId())
		self.__confirmation.Hide()

	def __AskReopen(self):
		self.__confirmation.SetText(localeInfo.OFFLINE_SHOP_REOPEN_QUESTION)
		self.__confirmation.SetAcceptEvent(self.__OnReopen)
		self.__confirmation.Open()

	def __OnReopen(self):
		net.SendOfflineShopReopenPacket(self.__GetId())
		self.__confirmation.Hide()

	def __SetClosed(self, closed = True):
		if closed:
			self.__close.Hide()
			self.__reopen.Show()
		else:
			self.__close.Show()
			self.__reopen.Hide()

	def __SetOpen(self):
		self.__close.Show()
		self.__reopen.Hide()

	def Hide(self): #EditorClass
		if self.IsShow():
			net.SendOfflineShopRemoveViewerPacket(self.__GetId())

			if self.__confirmation:
				self.__confirmation.Hide()
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()

			self.ItemListIdx = None
		
		if app.ENABLE_ANIMATED_WINDOW:
			if not self.bClosed:
				ui.Window.Hide(self)
			self.bClosed = True
		else:
			ui.Window.Hide(self)
	
	def Show(self):
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = []
			if self.inven == None:
				self.inven = self.interface.GetInventoryWnd()
			if self.invenSpecial == None:
				self.invenSpecial = self.interface.GetSpecialInventoryWnd()
				
			self.interface.SetOnTopWindow(player.ON_TOP_WND_PRIVATE_SHOP)
			self.interface.RefreshMarkInventoryBag()
				
		self.SetCenterPosition()
		ui.Window.Show(self)
		
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = False
			
	if app.WJ_ENABLE_TRADABLE_ICON:
		def OnTop(self):
			if not self.interface:
				return

			self.interface.SetOnTopWindow(player.ON_TOP_WND_PRIVATE_SHOP)
			self.interface.RefreshMarkInventoryBag()
	
	def RefreshItemGrid(self):
		# for i in range(self.__items.GetStartIndex(), self.__items.GetStartIndex() + self.__items.GetSlotCount()):
		
		# MULTIPLE_PAGE_UPDATE
		for i in range(80):
			self.__items.ClearSlot(i)
	
		for i in range(80*4):
			if i in self.__itemStock:
			
				gridSlot = i
				if self.__currentPage == 0:
					if i >= 80:
						break
					gridSlot = i
				elif self.__currentPage == 1:
					if i < 80:
						continue
					if i >= 160:
						break
					gridSlot -= 80
				elif self.__currentPage == 2:
					if i < 160:
						continue
					if i >= 240:
						break
					gridSlot -= 160
				elif self.__currentPage == 3:
					if i < 240:
						continue
					if i >= 320:
						break
					gridSlot -= 240

				self.__items.SetItemSlot(gridSlot, self.__itemStock[i].VNUM, self.__itemStock[i].COUNT > 1 and self.__itemStock[i].COUNT or 0)
				
				if app.ENABLE_CHANGE_LOOK_SYSTEM:
					itemTransmutedVnum = self.__itemStock[i].TRANSMUTATION
					if itemTransmutedVnum:
						self.__items.DisableCoverButton(gridSlot)
					else:
						self.__items.EnableCoverButton(gridSlot)
			# else:
				# self.__items.ClearSlot(i)
		
		self.__items.RefreshSlot()

	# MULTIPLE_PAGE_UPDATE
	def __OnClickPage(self, page, bIsFirst = False):
		self.__currentPage = page

		for index in range(len(self.__pagesTab)):
			if index == page:
				self.__pagesTab[index].Down()
				continue
			self.__pagesTab[index].SetUp()

		if not bIsFirst:
			self.RefreshItemGrid()
	# MULTIPLE_PAGE_UPDATE

	def SetShopName(self, shopName):
		if len(shopName) > 16:
			shopName = ("%s..." % shopName[:16])
		
		self.__nameEdit.SetText(shopName)
	
	def AddItem(self, shopPosition, price, vnum, count, soulbind, transmutation, sockets, attributes, ApplyRandom=None, refineElement=None):
		item = Item()
		item.VNUM = vnum
		item.COUNT = count
		item.SOULBIND = soulbind
		item.TRANSMUTATION = transmutation
		item.SOCKETS = sockets
		item.ATTRIBUTES = attributes
		item.APPLY_RANDOM = ApplyRandom
		item.PRICE = price
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			item.REFINE_ELEMENT = refineElement

		self.__itemStock[shopPosition] = item
		self.RefreshItemGrid()
	
	def MoveItem(self, oldShopPosition, newShopPosition):
		self.__itemStock[newShopPosition] = self.__itemStock.pop(oldShopPosition)
		self.RefreshItemGrid()
	
	def RemoveItem(self, shopPosition):
		del self.__itemStock[shopPosition]
		self.RefreshItemGrid()
	
	def SetOpeningTime(self, openingTime):
		self.__closingTime = openingTime
		self.__SetClosed(openingTime == 0)

	def SetShopPosition(self, channel, local_x, local_y, global_x, global_y):
		realMapName = "Unknown"
		(mapName, xBase, yBase) = background.GlobalPositionToMapInfo(global_x, global_y)

		localeMapName=localeInfo.MINIMAP_ZONE_NAME_DICT.get(mapName, "")
		if localeMapName!="":
			realMapName = localeMapName

		showPosX = int(round(local_x // 100))
		showPosY = int(round(local_y // 100))
		# self.__location.SetText("{}, {} | {} | |cff74cbff|H|h CH{} |h|r".format(showPosX, showPosY, realMapName, channel))
		#self.__location.SetText("|cff74cbff|H|h CH{}|h|r | {} | {}, {}".format(channel, realMapName, showPosX, showPosY))


	def IsClosed(self):
		return self.__closingTime == 0

	def SetGold(self, gold):
		self.__gold.SetText("{} {}".format(localeInfo.GetFormattedNumberString(gold), uiScriptLocale.OFFLINE_SHOP_EARNED_GOLD))

	def OnUpdate(self):
		USE_SHOP_LIMIT_RANGE = 2500

		leftTime = self.__closingTime - app.GetGlobalTimeStamp()
		if leftTime > 0 and self.__openingTime:
			formattedTime = localeInfo.FormatDays(max(0, leftTime))
			self.__openingTime.SetText(" {} |h|r".format(formattedTime))
		else:
			self.__SetClosed(True)

		# (x, y, z) = player.GetMainCharacterPosition()
		# if abs(x - self.__startX) > USE_SHOP_LIMIT_RANGE or abs(y - self.__startY) > USE_SHOP_LIMIT_RANGE:
			# if (self.bClosed != True):
				# self.Hide()
				
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

				
	def BindInterfaceClass(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)

	def OnPressEscapeKey(self):
		self.Hide()
		return True

class ViewerWindow(ui.ScriptWindow):
	if app.ENABLE_ANIMATED_WINDOW:
		bClosed = False
		
	def __init__(self, id, gameWnd):
		ui.ScriptWindow.__init__(self)
		
		self.__id = id
		self.__itemStock = {}
		self.__buyState = False
		#self.__previewFunc = gameWnd.interface.OpenPreviewWindow
		
		(self.__startX, self.__startY, z) = player.GetMainCharacterPosition()

		net.RegisterOfflineShopHandler(self.__GetId(), self)
		
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/offline_shop_viewer.py")
		
		self.__buyConfirmation = uiCommon.QuestionDialog()
		self.__buyConfirmation.SetCancelEvent(self.__buyConfirmation.Hide)
		self.__buyConfirmation.Hide()
		
		self.__itemToolTip = uitooltip.GetItemToolTipInstance()
		self.__itemToolTip.BindInterfaceClass(gameWnd.interface)
		
		self.__board = self.GetChild("board")
		self.__board.SetCloseEvent(self.Hide)
		
		self.__items = self.GetChild("items")
		self.__items.SAFE_SetButtonEvent("LEFT", "EXIST", self.OnClickItemSlot)
		self.__items.SAFE_SetButtonEvent("RIGHT", "EXIST", self.OnClickItemSlot)
		self.__items.SetOverInItemEvent(self.__OnOverInItem)
		self.__items.SetOverOutItemEvent(self.__OnOverOutItem)
		
		# MULTIPLE_PAGE_UPDATE
		self.__currentPage = 0
		self.__pagesTab = []

		for page in range(4): ## 0, 1, 2, 3
			self.__pagesTab.append(self.GetChild("slot_page_" + str(page+1)))
			self.__pagesTab[page].SetEvent(lambda arg=page: self.__OnClickPage(arg))

		self.__OnClickPage(0, True)
		# MULTIPLE_PAGE_UPDATE
		
		# buyButton = self.GetChild("buy")
		# buyButton.SetToggleUpEvent(lambda : self.__SetBuyState(False))
		# buyButton.SetToggleDownEvent(lambda : self.__SetBuyState(True))
		
		vid = osfInfo.SHOP_VID[id]
		playerName = chr.GetNameByVID(vid)
		if "'" in playerName:
			playerName = playerName.split("'")[-1].strip()
		
		self.userInfo = self.GetChild("user_informations")
		self.userInfo.SetText(uiScriptLocale.OFFLINE_SHOP_SHOP_OWNER % (playerName))
		
		self.sellerPM = self.GetChild("user_message")
		self.sellerPM.SetEvent(lambda arg=playerName: self.__OnClickPM(arg))
		
		self.wndInterface = gameWnd.interface

		self.GetChild("gm_delete_button").Hide()
		self.GetChild("gm_delete_button").SetEvent(ui.__mem_func__(self.OnClickDeleteGM))
		
		if chr.IsGameMaster(player.GetMainCharacterIndex()):
			self.GetChild("gm_delete_button").Show()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
				
		self.__buyConfirmation.Hide()
		self.__itemToolTip.HideToolTip()
		
		del self.__buyConfirmation
		del self.__itemToolTip

	def Destroy(self):
		ui.ScriptWindow.Destroy(self)

	def __GetId(self):
		return self.__id
		
	def __OnClickPM(self, playerName):
		self.wndInterface.OpenWhisperDialog(playerName)
		
	# MULTIPLE_PAGE_UPDATE
	def __OnClickPage(self, page, bIsFirst = False):
		self.__currentPage = page

		for index in range(len(self.__pagesTab)):
			if index == page:
				self.__pagesTab[index].Down()
				continue
			self.__pagesTab[index].SetUp()

		if not bIsFirst:
			self.RefreshItemGrid()
	# MULTIPLE_PAGE_UPDATE
	
	def __OnSelectItemSlot(self, slotIndex):
		#if app.IsPressed(app.DIK_LCONTROL):
		#	self.__previewFunc(self.__itemStock[slotIndex].VNUM)

		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		
		if self.__buyState:
			self.__AskBuy(slotIndex)

		else:
			itemInfo = self.__itemStock[slotIndex]
			
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_OFFLINE_SHOP, slotIndex, itemInfo.VNUM, itemInfo.COUNT)
	
	def OnClickItemSlot(self, slotIndex, destinationSlot = -1):
		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		self.__AskBuy(slotIndex, destinationSlot)
	
	def __OnOverInItem(self, slotIndex):
		# MULTIPLE_PAGE_UPDATE
		slotIndex += self.__currentPage*80
		# MULTIPLE_PAGE_UPDATE
		if slotIndex not in self.__itemStock:
			return
		
		self.__itemToolTip.SetOfflineShopItem(self.__itemStock[slotIndex])
		self.__itemToolTip.ShowToolTip()
	
	def __OnOverOutItem(self):
		self.__itemToolTip.HideToolTip()
	
	def __SetBuyState(self, buyState):
		self.__buyState = buyState
	
	def __AskBuy(self, slotIndex, destinationSlot = -1):
		if slotIndex not in self.__itemStock:
			return
		
		itemInfo = self.__itemStock[slotIndex]
		
		item.SelectItem(itemInfo.VNUM)
		
		self.__buyConfirmation.SetText(localeInfo.DO_YOU_BUY_ITEM(item.GetItemName(), itemInfo.COUNT, itemInfo.PRICE))
		self.__buyConfirmation.SetAcceptEvent(lambda : self.__OnBuy(slotIndex, destinationSlot))
		self.__buyConfirmation.Open()
	
	def __OnBuy(self, slotIndex, destinationSlot):
		if destinationSlot != -1:
			net.SendOfflineShopBuyItemPacket(self.__GetId(), slotIndex, player.SLOT_TYPE_INVENTORY, destinationSlot)
		else:
			net.SendOfflineShopBuyItemPacket(self.__GetId(), slotIndex, player.SLOT_TYPE_NONE, 0xffff)
		
		self.__buyConfirmation.Hide()
	
	def Hide(self): #ViewerClass
		if self.IsShow():
			net.SendOfflineShopRemoveViewerPacket(self.__GetId())
		
		if app.ENABLE_ANIMATED_WINDOW:
			if self.bClosed == False:
				ui.Window.Hide(self)
		else:
			ui.Window.Hide(self)
		
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = True		
	
	def Show(self):
		self.SetCenterPosition()
		ui.Window.Show(self)
		
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = False
	
	def RefreshItemGrid(self):
		# for i in range(self.__items.GetStartIndex(), self.__items.GetStartIndex() + self.__items.GetSlotCount()):
		
		# MULTIPLE_PAGE_UPDATE
		for i in range(80):
			self.__items.ClearSlot(i)
			
		for i in range(80*4):
			if i in self.__itemStock:
			
				gridSlot = i
				if self.__currentPage == 0:
					if i >= 80:
						break
					gridSlot = i
				elif self.__currentPage == 1:
					if i < 80:
						continue
					if i >= 160:
						break
					gridSlot -= 80
				elif self.__currentPage == 2:
					if i < 160:
						continue
					if i >= 240:
						break
					gridSlot -= 160
				elif self.__currentPage == 3:
					if i < 240:
						continue
					if i >= 320:
						break
					gridSlot -= 240

				self.__items.SetItemSlot(gridSlot, self.__itemStock[i].VNUM, self.__itemStock[i].COUNT > 1 and self.__itemStock[i].COUNT or 0)
		
				if app.ENABLE_CHANGE_LOOK_SYSTEM:
					itemTransmutedVnum = self.__itemStock[i].TRANSMUTATION
					if itemTransmutedVnum:
						self.__items.DisableCoverButton(gridSlot)
					else:
						self.__items.EnableCoverButton(gridSlot)
			
			# else:
				# self.__items.ClearSlot(i)
		# MULTIPLE_PAGE_UPDATE
		
		self.__items.RefreshSlot()

	def SetShopName(self, shopName):
		if len(shopName) > 16:
			shopName = ("%s..." % shopName[:16])
		
		self.__board.SetTitleName(shopName)
	
	def AddItem(self, shopPosition, price, vnum, count, soulbind, transmutation, sockets, attributes, ApplyRandom=None, refineElement=None):
		item = Item()
		item.VNUM = vnum
		item.COUNT = count
		item.SOULBIND = soulbind
		item.TRANSMUTATION = transmutation
		item.SOCKETS = sockets
		item.ATTRIBUTES = attributes
		item.APPLY_RANDOM = ApplyRandom
		item.PRICE = price
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			item.REFINE_ELEMENT = refineElement

		self.__itemStock[shopPosition] = item
		self.RefreshItemGrid()
	
	def MoveItem(self, oldShopPosition, newShopPosition):
		self.__itemStock[newShopPosition] = self.__itemStock.pop(oldShopPosition)
		self.RefreshItemGrid()
	
	def RemoveItem(self, shopPosition):
		del self.__itemStock[shopPosition]
		self.RefreshItemGrid()
	
	def SetOpeningTime(self, openingTime):
		pass
	
	def SetGold(self, gold):
		pass

	def OnUpdate(self):
		USE_SHOP_LIMIT_RANGE = 2500

		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.__startX) > USE_SHOP_LIMIT_RANGE or abs(y - self.__startY) > USE_SHOP_LIMIT_RANGE:
			if app.ENABLE_ANIMATED_WINDOW:
				if (self.bClosed != True):
					self.Hide()
			else:
				self.Hide()

	def OnPressEscapeKey(self):
		self.Hide()
		return True

	def OnClickDeleteGM(self):
		net.SendChatPacket("/delete_shop " + str(self.__GetId()))
