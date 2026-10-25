import ui, app, item, os, osfInfo, localeInfo, uiScriptLocale, wndMgr
import uiwheel
import itemshopcategories as categoryData
import net
import player
import iscostumevoucher
import itempreview
from marketfilters import folded
from _weakref import proxy
try:
	import threading		# OpenLinkInBrowser: the browser starts off the main thread
except ImportError:
	threading = None

itemshopData = {}
playerLog = []
itemshopReactions = {}
itemShopWndInstance = None

UPDATE_TIME = -1
# Most pieces of one purchase: the server's stack limit (CONFIG MAX_ITEM_COUNT),
# sent as ItemShopMaxCount before the offers.
MAX_BUY_COUNT = 1

def ItemShopLogClear():
	global playerLog
	playerLog=[]

def ItemShopAppendLog(dateText, dateTime, playerName, ipAdress, itemVnum, itemCount, itemPrice):
	dateTimeReal = "None"
	dateSplit = dateText.split(" ")
	if len(dateSplit) > 1:
		dateFirst = dateSplit[0].split("-")
		if len(dateFirst) == 3:
			dateTimeReal = dateFirst[2]+"/"+dateFirst[1]+"/"+dateFirst[0]
			dateTimeReal+=" "
			dateSecond = dateSplit[1].split(":")
			if len(dateSecond) == 3:
				dateTimeReal += dateSecond[0]+":"+dateSecond[1]

	global playerLog
	playerLog.append([dateTimeReal,dateTime,playerName,ipAdress,itemVnum,itemCount,itemPrice])

def ItemShopClear(time):
	global itemshopData
	global UPDATE_TIME
	if time != UPDATE_TIME:
		itemshopData.clear()
		UPDATE_TIME = time

def ItemShopAppendItem(categoryIndex, categorySubIndex, itemID, itemVnum, itemPrice, itemDiscount, itemOffertime, itemTopSelling, itemAddedTime, itemSellingCount, itemCount=1):
	if categoryIndex not in itemshopData:
		subCategoryList=[]
		for x in range(10):
			subCategoryList.append([])
		itemshopData[categoryIndex] = subCategoryList
	itemshopData[categoryIndex][categorySubIndex].append([itemID, itemVnum, itemPrice, itemDiscount, itemOffertime, itemTopSelling, itemAddedTime, itemSellingCount, itemCount])

def ItemShopSetMaxCount(maxCount):
	global MAX_BUY_COUNT
	MAX_BUY_COUNT = max(1, maxCount)

def ItemShopSetReaction(itemID, likes, dislikes, myVote):
	global itemshopReactions
	itemshopReactions[int(itemID)] = {"likes": int(likes), "dislikes": int(dislikes), "myVote": int(myVote)}
	global itemShopWndInstance
	if itemShopWndInstance:
		itemShopWndInstance.UpdateReactionForItem(int(itemID))


def OfferSearchNames(itemVnum):
	"""Names an offer is found by: its own and, for a costume voucher, the costume's."""
	names = []
	for vnum in (itemVnum, iscostumevoucher.DisplayVnum(itemVnum)):
		item.SelectItem(vnum)
		name = item.GetItemName()
		if name and name not in names:
			names.append(name)
	return names

def CurrentPlayerRace():
	try:
		return player.GetRace()
	except (AttributeError, RuntimeError, TypeError, ValueError):
		return None


buyQuestionDialog = None

# The R1 look (uiitemshopr1.Theme) while the shop is drawn in it, else None (the original look).
_r1 = None


def Img(name, r1name=None):
	"""An Item Shop texture: its R1 copy while the R1 look is on, else the original file."""
	if _r1 is not None:
		path = _r1.Path(r1name or name)
		if path:
			return path
	return IMG_DIR + name


def R1(method, *args):
	"""Runs a hook of the R1 look; a failure is traced to syserr and the shop goes back to the original look."""
	global _r1
	theme = _r1
	if theme is None:
		return None
	try:
		return getattr(theme, method)(*args)
	except Exception:
		import uir1
		uir1.TraceFailure("Item Shop")
		_r1 = None
		try:
			theme.Fail()
		except Exception:
			pass
		return None

LIST_ITEM_COUNT=8
LIST_ITEM_ID=0
LIST_ITEM_VNUM=1
LIST_ITEM_PRICE=2
LIST_ITEM_DISCOUNT=3
LIST_ITEM_TIME=4
LIST_ITEM_TOP_SELLING_INDEX=5
LIST_ITEM_ADDED_TIME=6
LIST_ITEM_SELLING_COUNT=7

LOG_DATE_TEXT = 0
LOG_DATE = 1
LOG_ACCOUNT = 2
LOG_IP = 3
LOG_ITEM = 4
LOG_COUNT = 5
LOG_PRICE = 6


HOT_ITEM=1
NEW_ITEM=2
OFFER_ITEM=3
WARDROBE_CATEGORY_INDEX=-100

#Config

# The web addresses the shop opens are data: one "KEY<TAB>address" row per link in this file; the code only reads them.
LINKS_FILE = "locale/common/itemshop_links.txt"


def ItemShopLink(key):
	"""The address of one Item Shop link from LINKS_FILE, or "" when the file or the row is missing."""
	try:
		with open(LINKS_FILE, "r") as stream:
			lines = stream.readlines()
	except IOError:
		return ""
	for line in lines:
		line = line.strip()
		if not line or line.startswith("#"):
			continue
		name, separator, address = line.partition("\t")
		if separator and name.strip() == key:
			return address.strip()
	return ""


def OpenLinkInBrowser(url):
	"""Open a web page in the default browser without stopping the game (owner 15. 10.: "Koupit mince" froze the
	game for a few seconds). The old os.system("start ...") started cmd.exe with its own console and waited for it
	and for the browser hand-off on the main thread (about 1 s for the console alone, measured). os.startfile is the
	same ShellExecute "open" without cmd.exe; it runs in a daemon thread and releases the GIL while Windows starts
	the browser. Without threads the native app.ShellExecute (no console) is the fallback. True when started."""
	if not url:
		return False

	def _Open():
		try:
			os.startfile(url)
		except Exception:
			pass

	try:
		worker = threading.Thread(target=_Open, name="itemshop-link")
		worker.daemon = True
		worker.start()
		return True
	except Exception:
		pass
	shell = getattr(app, "ShellExecute", None)
	if shell:
		shell(url)
		return True
	return False

eventCategory = [
	# [[FILENAMES],[CATEGORY, SUB_CATEGORY]]
	[["costume_banner_0.tga","costume_banner_1.tga"],[0,0]],
]

IMG_DIR ="d:/ymir work/ui/game/ishop/"
# The toolbar of this look (RefreshAfkRewards): five 98 px buttons from TOOLBAR_X, then the costume exchange
# (owner 18. 10. 2026) as a narrow icon button, then the search up to SEARCH_RIGHT. A sixth 98 px button would
# cover the search, so the exchange shows an icon and its name as the tooltip.
TOOLBAR_X, TOOLBAR_PITCH, SEARCH_RIGHT, ICON_BUTTON_W = 270, 102, 957, 40
SEARCH_X = TOOLBAR_X + 5 * TOOLBAR_PITCH + ICON_BUTTON_W + 6
COSTUME_EXCHANGE_ICON = "icon/key/cosmetics.tga"

itemShopCategoryData = dict((key, {
	"name": "|cfffffed " + getattr(localeInfo, name),
	"subCategory": [getattr(localeInfo, sub) for sub in subs],
}) for key, name, subs in categoryData.CATEGORIES)

class ItemShopWindow(ui.BoardWithTitleBar):
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)
	def Destroy(self):
		if getattr(self, "afkShop", None):
			self.afkShop.Destroy()
			self.afkShop = None
		self._afkNextPoll = 0
		self._afkNextRequest = 0
		self._afkRequestAttempts = 0
		self._afkPresentation = None
		if getattr(self, "wardrobeWindow", None):
			self.wardrobeWindow.Destroy()
			self.wardrobeWindow = None
		if getattr(self, "costumeExchangeWindow", None):
			self.costumeExchangeWindow.Destroy()
			self.costumeExchangeWindow = None
		ItemShopLogClear()
		skin = getattr(self, "r1skin", None)
		if skin:
			skin.Destroy()
			skin.window = None
			self.r1skin = None
		if "categoryListBox" in self.children:
			self.children["categoryListBox"].RemoveAllItems()
		if "itemListBox" in self.children:
			self.children["itemListBox"].RemoveAllItems()
		if "PurchasesListBox" in self.children:
			self.children["PurchasesListBox"].RemoveAllItems()
		self.CloseWeb()
	
		global buyQuestionDialog
		if buyQuestionDialog != None:
			buyQuestionDialog.Hide()
			buyQuestionDialog.Destroy()
			buyQuestionDialog=None

		self.RealMoney = 0
		self.NewMoney = 0
		self.MoneyRange = 0
		self.MoneyFlag = False
		self.moneySize = 0

		self.lastReactionRefreshTime = 0
		self.reactionRefreshInterval = 5

		self.children = {}
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.children = {}
		self.wardrobeWindow = None
		self.costumeExchangeWindow = None
		self.afkShop = None
		self.r1skin = None
		self.Destroy()
		global itemShopWndInstance
		itemShopWndInstance = self
		self.LoadWindow()
		self.BuildR1()

	def BuildR1(self):
		"""The R1 look drawn into the window (uiitemshopr1) unless Settings -> "Stary vzhled" chose the original
		one; a failure is traced and the original look stays."""
		global _r1
		try:
			import uir1
			if not uir1.UseR1():
				return
			import uiitemshopr1
			self.r1skin = uiitemshopr1.ShopSkin(self, self.ForgetR1)
			_r1 = self.r1skin.theme
		except Exception:
			import uir1
			uir1.TraceFailure("Item Shop")
			self.r1skin = None
			_r1 = None

	def ForgetR1(self, theme):
		global _r1
		if _r1 is theme:
			_r1 = None
		self.r1skin = None

	def RefreshSearch(self):
		self.__OnValueUpdate()

	def LoadWindow(self):
		self.AddFlag("movable")
		self.AddFlag("attach")
		self.AddFlag("float")

		boardImage = ui.ImageBox()
		boardImage.SetParent(self)
		boardImage.AddFlag("attach")
		boardImage.LoadImage(IMG_DIR+"bg.tga")
		boardImage.SetPosition(10,32)
		boardImage.Show()
		self.children["boardImage"] = boardImage

		self.SetTitleName(uiScriptLocale.ITEMSHOP_TITLE)

		self.SetSize(boardImage.GetWidth()+20,boardImage.GetHeight()+32+10)

		closeBtn = ui.Button()
		closeBtn.SetParent(boardImage)
		closeBtn.SetUpVisual(IMG_DIR+"close_0.tga")
		closeBtn.SetOverVisual(IMG_DIR+"close_1.tga")
		closeBtn.SetDownVisual(IMG_DIR+"close_2.tga")
		closeBtn.SetEvent(self.Close)
		closeBtn.SetPosition(boardImage.GetWidth()-closeBtn.GetWidth()-5,5)
		closeBtn.Hide()
		self.children["closeBtn"] = closeBtn

		leftDragonCoinImage = ui.ImageBox()
		leftDragonCoinImage.SetParent(boardImage)
		leftDragonCoinImage.LoadImage(IMG_DIR+"coin.tga")
		leftDragonCoinImage.SetPosition(35,20)
		leftDragonCoinImage.Show()
		self.children["leftDragonCoinImage"] = leftDragonCoinImage

		dragonCoinText = MultiTextLine()
		dragonCoinText.SetParent(boardImage)
		dragonCoinText.SetPosition(35+leftDragonCoinImage.GetWidth()+10,17)
		dragonCoinText.SetTextRange(17)
		dragonCoinText.SetTextType("horizontal#left")
		dragonCoinText.SetFontName("Tahoma:14")
		dragonCoinText.SetOutline(True)
		dragonCoinText.Show()
		self.children["dragonCoinText"] = dragonCoinText

		buyCoinBtn = ui.Button()
		buyCoinBtn.SetParent(boardImage)
		buyCoinBtn.SetUpVisual(IMG_DIR+"button1_0.tga")
		buyCoinBtn.SetOverVisual(IMG_DIR+"button1_1.tga")
		buyCoinBtn.SetDownVisual(IMG_DIR+"button1_2.tga")
		buyCoinBtn.SetEvent(self.BuyDragonCoin)
		buyCoinBtn.SetPosition(180,12)
		buyCoinBtn.Show()
		self.children["buyCoinBtn"] = buyCoinBtn

		buyCoinBtnText = MultiTextLine()
		buyCoinBtnText.SetParent(buyCoinBtn)
		buyCoinBtnText.SetTextRange(17)
		buyCoinBtnText.SetPosition(buyCoinBtn.GetWidth()//2,10)
		buyCoinBtnText.SetTextType("horizontal#center")
		buyCoinBtnText.SetFontName("Tahoma:16")
		buyCoinBtnText.SetText(localeInfo.ITEMSHOP_BUY_COIN)
		buyCoinBtnText.SetOutline(True)
		buyCoinBtnText.Show()
		buyCoinBtn.multiText = buyCoinBtnText

		purchasesBtn = ui.Button()
		purchasesBtn.SetParent(boardImage)
		purchasesBtn.SetUpVisual(IMG_DIR+"button2_0.tga")
		purchasesBtn.SetOverVisual(IMG_DIR+"button2_1.tga")
		purchasesBtn.SetDownVisual(IMG_DIR+"button2_2.tga")
		purchasesBtn.SetEvent(self.PurchaseBtn)
		purchasesBtn.SetPosition(180+buyCoinBtn.GetWidth()+7,12)
		purchasesBtn.Show()
		self.children["purchasesBtn"] = purchasesBtn
		
		

		purchasesBtnText = MultiTextLine()
		purchasesBtnText.SetParent(purchasesBtn)
		purchasesBtnText.SetTextRange(17)
		purchasesBtnText.SetPosition(purchasesBtn.GetWidth()//2,10)
		purchasesBtnText.SetTextType("horizontal#center")
		purchasesBtnText.SetFontName("Tahoma:14")
		purchasesBtnText.SetOutline(True)
		purchasesBtnText.SetText(localeInfo.ITEMSHOP_PURCHASES)
		purchasesBtnText.Show()
		purchasesBtn.multiText = purchasesBtnText

		hotItemsBtn = ui.Button()
		hotItemsBtn.SetParent(boardImage)
		hotItemsBtn.SetUpVisual(IMG_DIR+"button2_0.tga")
		hotItemsBtn.SetOverVisual(IMG_DIR+"button2_1.tga")
		hotItemsBtn.SetDownVisual(IMG_DIR+"button2_2.tga")
		hotItemsBtn.SetEvent(self.HotItems)
		hotItemsBtn.SetPosition(180+((buyCoinBtn.GetWidth()+7)*2),12)
		hotItemsBtn.Show()
		self.children["hotItemsBtn"] = hotItemsBtn

		hotItemsBtnText = MultiTextLine()
		hotItemsBtnText.SetParent(hotItemsBtn)
		hotItemsBtnText.SetTextRange(17)
		hotItemsBtnText.SetPosition(hotItemsBtn.GetWidth()//2,11)
		hotItemsBtnText.SetTextType("horizontal#center")
		hotItemsBtnText.SetFontName("Tahoma:14")
		hotItemsBtnText.SetOutline(True)
		hotItemsBtnText.SetText(localeInfo.ITEMSHOP_HOTITEMS)
		hotItemsBtnText.Show()
		hotItemsBtn.multiText = hotItemsBtnText

		offersBtn = ui.Button()
		offersBtn.SetParent(boardImage)
		offersBtn.SetUpVisual(IMG_DIR+"button2_0.tga")
		offersBtn.SetOverVisual(IMG_DIR+"button2_1.tga")
		offersBtn.SetDownVisual(IMG_DIR+"button2_2.tga")
		offersBtn.SetEvent(self.OfferItems)
		offersBtn.SetPosition(180+((buyCoinBtn.GetWidth()+7)*3),12)
		offersBtn.Show()
		self.children["offersBtn"] = offersBtn

		offersBtnText = MultiTextLine()
		offersBtnText.SetParent(offersBtn)
		offersBtnText.SetTextRange(17)
		offersBtnText.SetPosition(offersBtn.GetWidth()//2,11)
		offersBtnText.SetTextType("horizontal#center")
		offersBtnText.SetFontName("Tahoma:14")
		offersBtnText.SetOutline(True)
		offersBtnText.SetText(localeInfo.ITEMSHOP_OFFERS)
		offersBtnText.Show()
		offersBtn.multiText = offersBtnText

		costumeExchangeBtn = ui.Button()
		costumeExchangeBtn.SetParent(boardImage)
		costumeExchangeBtn.SetUpVisual(IMG_DIR+"button2_0.tga")
		costumeExchangeBtn.SetOverVisual(IMG_DIR+"button2_1.tga")
		costumeExchangeBtn.SetDownVisual(IMG_DIR+"button2_2.tga")
		wndMgr.SetScale(costumeExchangeBtn.hWnd, float(ICON_BUTTON_W) / costumeExchangeBtn.GetWidth(), 1.0)
		costumeExchangeBtn.SetToolTipText(localeInfo.ITEMSHOP_COSTUME_EXCHANGE)
		costumeExchangeBtn.SetEvent(self.OpenCostumeExchange)
		costumeExchangeBtn.SetPosition(180+((buyCoinBtn.GetWidth()+7)*4),12)
		costumeExchangeBtn.Show()
		self.children["costumeExchangeBtn"] = costumeExchangeBtn

		costumeExchangeIcon = ui.ImageBox()
		costumeExchangeIcon.SetParent(costumeExchangeBtn)
		costumeExchangeIcon.AddFlag("not_pick")
		costumeExchangeIcon.LoadImage(COSTUME_EXCHANGE_ICON)
		costumeExchangeIcon.SetPosition((ICON_BUTTON_W - costumeExchangeIcon.GetWidth())//2,
			(costumeExchangeBtn.GetHeight() - costumeExchangeIcon.GetHeight())//2)
		costumeExchangeIcon.Show()
		costumeExchangeBtn.icon = costumeExchangeIcon

		itemSearchBg = ui.ExpandedImageBox()
		itemSearchBg.SetParent(boardImage)
		itemSearchBg.LoadImage(IMG_DIR+"search_box.tga")
		# Preserve the right edge while making room for the AFK and costume exchange header actions.
		searchWidth = SEARCH_RIGHT - SEARCH_X
		itemSearchBg.SetScale(float(searchWidth) / itemSearchBg.GetWidth(), 1.0)
		itemSearchBg.SetSize(searchWidth, 36)
		itemSearchBg.SetPosition(869-searchWidth,13)
		itemSearchBg.Show()
		self.children["itemSearchBg"] = itemSearchBg

		itemSearch = ui.EditLine()
		itemSearch.SetParent(itemSearchBg)
		itemSearch.SetMax(25)
		itemSearch.SetPosition(14,15)
		itemSearch.SetFontColor(128,128,128)
		itemSearch.SetFontName("Tahoma:14")
		itemSearch.SetSize(searchWidth-28, itemSearchBg.GetHeight()-10)
		itemSearch.SetLimitWidth(searchWidth-28)
		itemSearch.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdate)
		itemSearch.SetEscapeEvent(self.Close)
		itemSearch.Show()
		self.children["itemSearch"] = itemSearch

		itemSearchText = MultiTextLine()
		itemSearchText.SetParent(itemSearch)
		itemSearchText.SetTextRange(15)
		itemSearchText.SetPosition(0,-2)
		itemSearchText.SetFontColor(128,128,128)
		itemSearchText.SetTextType("horizontal#left")
		itemSearchText.SetFontName("Tahoma:14")
		itemSearchText.SetText(localeInfo.ITEMSHOP_ITEMSEARCH_DEFAULT_TEXT)
		itemSearchText.Show()
		itemSearch.overLay = itemSearchText

		categoryScrollBar = ScrollBar()
		categoryScrollBar.SetParent(boardImage)
		categoryScrollBar.SetPosition(*categoryData.SCROLL_POSITION)
		categoryScrollBar.SetScrollBarSize(categoryData.SCROLL_HEIGHT)
		categoryScrollBar.Hide()
		self.children["categoryScrollBar"] = categoryScrollBar

		categoryListBox = CategoryListBox()
		categoryListBox.SetParent(boardImage)
		categoryListBox.SetPosition(*categoryData.LIST_POSITION)
		categoryListBox.SetSize(categoryData.LIST_WIDTH, categoryData.VIEWPORT_HEIGHT)
		categoryListBox.SetItemStep(2)
		categoryListBox.SetItemSize(categoryData.LIST_WIDTH, categoryData.ROW_PITCH)
		categoryListBox.SetScrollBar(categoryScrollBar)
		categoryListBox.Show()
		self.children["categoryListBox"] = categoryListBox

		itemScrollBar = ScrollBar()
		itemScrollBar.SetParent(boardImage)
		itemScrollBar.SetPosition(200+750+10,76)
		itemScrollBar.SetScrollBarSize(435)
		itemScrollBar.SetScrollStep(0.07)
		itemScrollBar.Show()
		self.children["itemScrollBar"] = itemScrollBar

		itemListBox = ListBox()
		itemListBox.SetParent(boardImage)
		itemListBox.SetPosition(200,76)
		itemListBox.SetSize(750,445)
		itemListBox.SetItemStep(8)
		itemListBox.SetItemSize(750,122)
		itemListBox.SetScrollBar(itemScrollBar)
		itemListBox.OnUpdate = self.OnUpdate()
		itemListBox.Show()
		self.children["itemListBox"] = itemListBox

		PurchasesScrollBar = ScrollBar()
		PurchasesScrollBar.SetParent(boardImage)
		PurchasesScrollBar.SetPosition(200+750+10,76)
		PurchasesScrollBar.SetScrollBarSize(435)
		PurchasesScrollBar.SetScrollStep(0.07)
		self.children["PurchasesScrollBar"] = PurchasesScrollBar

		PurchasesListBox = ListBox()
		PurchasesListBox.SetParent(boardImage)
		PurchasesListBox.SetPosition(16,75)
		PurchasesListBox.SetSize(927,440)
		PurchasesListBox.SetItemStep(8)
		PurchasesListBox.SetItemSize(927,28)
		PurchasesListBox.SetScrollBar(PurchasesScrollBar)
		self.children["PurchasesListBox"] = PurchasesListBox

		LoadingImage = ui.ExpandedImageBox()
		LoadingImage.SetParent(boardImage)
		LoadingImage.SetPosition(boardImage.GetWidth()//2,boardImage.GetHeight()//2)
		LoadingImage.LoadImage(IMG_DIR+"load_.tga")
		self.children["LoadingImage"] = LoadingImage

		self.children["LoadingImageRotation"] = 0

		self.SetDragonCoin(0)
		self.SetCenterPosition()
		self.LoadShopCategory()
		self.RefreshAfkRewards()

	def __OnValueUpdate(self):
		itemSearch = self.children["itemSearch"]
		ui.EditLine.OnIMEUpdate(itemSearch)

		self.ClearItemList()
		searchItemList = []
		searchText = folded(itemSearch.GetText())
		if len(searchText) > 0:
			for key, data in itemshopData.items():
				for itemList in data:
					for itemData in itemList:
						if any(searchText in folded(name) for name in OfferSearchNames(itemData[LIST_ITEM_VNUM])):
							searchItemList.append(itemData)
			self.RefreshItemList(searchItemList)
		else:
			self.LoadFirstOpening()

		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			itemSearch.KillFocus()

	def OnUpdate(self):
		self.PollAfkRewards()
		if "itemListBox" in self.children:
			listboxData = self.children["itemListBox"].GetItems()
			for itemPointer in listboxData:
				itemPointer.OnUpdate()
		if "LoadingImage" in self.children:
			LoadingImage = self.children["LoadingImage"]
			if LoadingImage.IsShow():
				self.children["LoadingImageRotation"] += 15
				LoadingImage.SetRotation(self.children["LoadingImageRotation"])

		if self.MoneyFlag == True:
			if self.moneySize>=0 and self.moneySize<=15:
				if self.NewMoney > self.RealMoney:
					self.RealMoney += ((self.MoneyRange)//15)
					self.SetDragonCoinReal(self.RealMoney)
				else:
					self.RealMoney -= ((self.MoneyRange)//15)
					self.SetDragonCoinReal(self.RealMoney)
				self.moneySize+=1
				if self.moneySize ==15:
					self.RealMoney = self.NewMoney
					self.SetDragonCoinReal(self.RealMoney)
					self.MoneyFlag = False

		if self.IsShow():
			now = app.GetGlobalTimeStamp()
			if self.lastReactionRefreshTime == 0:
				self.lastReactionRefreshTime = now
			elif now - self.lastReactionRefreshTime >= self.reactionRefreshInterval:
				self.lastReactionRefreshTime = now
				net.SendChatPacket("/ishop reacts")

	def LoadShopCategory(self):
		self.categoryIndex = -1
		self.categorySubIndex = -1
		categoryListBox = self.children["categoryListBox"]
		if getattr(app, "ENABLE_ITEMSHOP_WARDROBE", False):
			categoryItem = CategoryItem()
			categoryItem.SetParent(categoryListBox)
			categoryItem.SetPosition(0, len(categoryListBox.GetItems()) * categoryData.ROW_PITCH, True)
			categoryItem.SetData(WARDROBE_CATEGORY_INDEX, "|cfffffed " + getattr(localeInfo, "WARDROBE_TITLE", "\u0160atn\u00edk"), categoryListBox)
			categoryItem.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInCategory, WARDROBE_CATEGORY_INDEX, proxy(categoryItem))
			categoryItem.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutCategory, WARDROBE_CATEGORY_INDEX, proxy(categoryItem))
			categoryItem.SetEvent(self.ClickCategory, "mouse_click", WARDROBE_CATEGORY_INDEX, -1)
			categoryItem.Show()
			categoryListBox.AppendItem(categoryItem)
		for key, name, subs in categoryData.CATEGORIES:
			data = itemShopCategoryData[key]
			categoryItem = CategoryItem()
			categoryItem.SetParent(categoryListBox)
			categoryItem.SetPosition(0,len(categoryListBox.GetItems()) * categoryData.ROW_PITCH,True)
			categoryItem.SetData(key, data["name"],categoryListBox)
			categoryItem.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInCategory,key, proxy(categoryItem))
			categoryItem.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutCategory, key, proxy(categoryItem))
			categoryItem.SetEvent(self.ClickCategory, "mouse_click", key, -1)
			categoryItem.Show()
			categoryListBox.AppendItem(categoryItem)
		categoryListBox.RefreshScroll()


	def RequestAfkRewards(self):
		import uiafkrewardshop
		now = app.GetTime()
		if not uiafkrewardshop.IsSupported() or now < self._afkNextRequest or self._afkRequestAttempts >= 3:
			return
		self._afkNextRequest = now + 5.0
		self._afkRequestAttempts += 1
		getattr(net, "SendAfkRewardsSnapshot", lambda: False)()

	def PollAfkRewards(self):
		if not self.IsShow():
			return
		now = app.GetTime()
		if now < self._afkNextPoll:
			return
		self._afkNextPoll = now + 0.5
		import uiafkrewardshop
		state = (uiafkrewardshop.IsSupported(), uiafkrewardshop.Snapshot())
		if state != self._afkPresentation:
			self.RefreshAfkRewards()
		if state[0] and state[1] is None:
			self.RequestAfkRewards()

	def RefreshAfkRewards(self):
		import uiafkrewardshop
		if "afkBalanceText" not in self.children:
			label = MultiTextLine()
			label.SetParent(self.children["boardImage"])
			label.SetPosition(162, 17)
			label.SetTextRange(17)
			label.SetTextType("horizontal#left")
			label.SetFontName("Tahoma:14")
			label.SetOutline(True)
			self.children["afkBalanceText"] = label
			button = ui.Button()
			button.SetParent(self.children["boardImage"])
			button.SetUpVisual(IMG_DIR+"button2_0.tga")
			button.SetOverVisual(IMG_DIR+"button2_1.tga")
			button.SetDownVisual(IMG_DIR+"button2_2.tga")
			caption = MultiTextLine()
			caption.SetParent(button)
			caption.SetTextRange(17)
			caption.SetPosition(button.GetWidth()//2, 11)
			caption.SetTextType("horizontal#center")
			caption.SetFontName("Tahoma:14")
			caption.SetOutline(True)
			caption.SetText(uiafkrewardshop.Text("AFK_SHOP_TITLE", "AFK shop"))
			caption.Show()
			button.multiText = caption
			button.SetEvent(self.OpenAfkShop)
			self.children["afkShopButton"] = button
		data = uiafkrewardshop.Snapshot()
		offered = uiafkrewardshop.IsSupported()
		self._afkPresentation = (offered, data)
		# The AFK shop and the AFK balance are always in the toolbar. Until the server offers the rewards the balance
		# reads "-" (unknown, never a false 0) and the AFK page says the points are unavailable (balances, prices and
		# purchases stay the server's).
		for key in ("afkBalanceText", "afkShopButton"):
			self.children[key].Show()
		self.children["leftDragonCoinImage"].SetPosition(15, 20)
		self.children["dragonCoinText"].SetPosition(44, 17)
		for index, key in enumerate(("buyCoinBtn", "purchasesBtn", "hotItemsBtn", "offersBtn", "afkShopButton",
				"costumeExchangeBtn")):
			self.children[key].SetPosition(TOOLBAR_X + index * TOOLBAR_PITCH, 12)
		self.children["itemSearchBg"].SetPosition(SEARCH_X, 13)
		self.children["afkShopButton"].Enable()
		if data is not None:
			balance = NumberToMoneyFormat(data[0])
		elif offered:
			balance = uiafkrewardshop.Text("AFK_STATE_LOADING", "Loading...")
		else:
			balance = "-"
		self.children["afkBalanceText"].SetText(uiafkrewardshop.Text("AFK_SHOP_BALANCE", "AFK points") + "\n|cffF8BE47" + balance)
		if self.afkShop:
			self.afkShop.Refresh()
		skin = getattr(self, "r1skin", None)
		if skin:
			skin.LayoutHeader()

	def OpenAfkShop(self):
		import uiafkrewardshop
		self.ClosePurchasesWindow()
		self.ClearSubCategoryWindow()
		self.children["itemSearch"].KillFocus()
		self.categoryIndex = -101
		self.categorySubIndex = -1
		if self.afkShop is None:
			self.afkShop = uiafkrewardshop.AfkRewardShop(self.children["boardImage"])
			skin = getattr(self, "r1skin", None)
			if skin:
				skin.StyleAfk(self.afkShop)
		for key in ("itemListBox", "itemScrollBar", "LoadingImage"):
			self.children[key].Hide()
		self.afkShop.Refresh()
		self.afkShop.Show()
		if uiafkrewardshop.IsSupported():
			getattr(net, "SendAfkRewardsSnapshot", lambda: False)()

	def CloseAfkShop(self):
		if self.afkShop:
			self.afkShop.Close()

	def OnAfkRewardPurchaseResult(self, result, balance):
		self.RefreshAfkRewards()
		if self.afkShop:
			self.afkShop.OnPurchaseResult(result, balance)

	def OpenWardrobe(self, emptyArg=None):
		if not getattr(app, "ENABLE_ITEMSHOP_WARDROBE", False):
			return
		import uiwardrobe
		if self.wardrobeWindow is not None and uiwardrobe.IsR1(self.wardrobeWindow) != uiwardrobe.WantR1():
			self.wardrobeWindow.Destroy()		# the look was switched in Settings since the last open
			self.wardrobeWindow = None
		if self.wardrobeWindow is None:
			self.wardrobeWindow = uiwardrobe.CreateWindow(self)
		self.wardrobeWindow.Open(itemshopData)

	def OpenCostumeExchange(self):
		import uiitemshopcostumeexchange
		if self.costumeExchangeWindow is None:
			self.costumeExchangeWindow = uiitemshopcostumeexchange.CostumeExchangeWindow()
		self.costumeExchangeWindow.Open()

	def BuyWardrobeItem(self, itemVnum):
		offer = None
		wardrobe = getattr(self, "wardrobeWindow", None)
		if wardrobe:
			mapped = wardrobe.itemshopOffers.get(int(itemVnum))
			if mapped and (not mapped[LIST_ITEM_TIME] or app.GetGlobalTimeStamp() <= mapped[LIST_ITEM_TIME]):
				offer = (wardrobe._OfferPrice(mapped), mapped)
		for subcategories in itemshopData.values():
			for offerList in subcategories:
				for itemData in offerList:
					if int(itemData[LIST_ITEM_VNUM]) != int(itemVnum):
						continue
					if itemData[LIST_ITEM_TIME] and app.GetGlobalTimeStamp() > itemData[LIST_ITEM_TIME]:
						continue
					price = itemData[LIST_ITEM_PRICE]
					if itemData[LIST_ITEM_DISCOUNT] > 0:
						price = (price * (100 - itemData[LIST_ITEM_DISCOUNT])) // 100
					if offer is None or price < offer[0]:
						offer = (price, itemData)
		if offer is None:
			return

		global buyQuestionDialog
		if buyQuestionDialog is not None:
			buyQuestionDialog.Hide()
			buyQuestionDialog.Destroy()

		price, itemData = offer
		item.SelectItem(itemData[LIST_ITEM_VNUM])
		buyQuestionDialog = BuyWindow()
		buyQuestionDialog.SetText(localeInfo.ITEMSHOP_BUY_TEXT % item.GetItemName() + "\n" + localeInfo.ITEMSHOP_PRICE % price)
		buyQuestionDialog.SetAcceptEvent(lambda itemID=itemData[LIST_ITEM_ID]: self.__AcceptWardrobeBuy(itemID))
		buyQuestionDialog.SetCancelEvent(self.__CloseWardrobeBuy)
		buyQuestionDialog.SetCenterPosition()
		buyQuestionDialog.SetTop()
		buyQuestionDialog.Show()

	def __AcceptWardrobeBuy(self, itemID):
		if getattr(app, "ENABLE_ITEMSHOP_BUNDLES", False):
			net.SendChatPacket("/ishop buy_v2 %d 1" % itemID)
		else:
			net.SendChatPacket("/ishop buy %d 1" % itemID)
		self.__CloseWardrobeBuy()

	def __CloseWardrobeBuy(self):
		global buyQuestionDialog
		if buyQuestionDialog is not None:
			buyQuestionDialog.Hide()
			buyQuestionDialog.Destroy()
			buyQuestionDialog = None

	def ClickCategory(self, emptyArg, categoryIndex, categorySubIndex = -1):
		if categoryIndex == WARDROBE_CATEGORY_INDEX:
			self.OpenWardrobe()
			return

		itemSearch = self.children["itemSearch"]
		itemSearch.KillFocus()
		if self.categoryIndex == categoryIndex:
			if categorySubIndex == self.categorySubIndex:
				return

		oldIndex = self.categoryIndex
		self.categoryIndex = categoryIndex
		self.categorySubIndex = categorySubIndex

		categoryItems = self.children["categoryListBox"].GetItems()
		for category in categoryItems:
			if category.categoryIndex == oldIndex:
				self.OverOutCategory(oldIndex, category)
			elif category.categoryIndex == categoryIndex:
				self.OverInCategory(categoryIndex, category)

		self.UpdateSubCategoryWindow()
		self.RefreshItem()

	def OverOutCategory(self, categoryIndex, categoryItem):
		self.ClearSubCategoryWindow()
		if categoryIndex==self.categoryIndex:
			return
		categoryItem.LoadImage(Img("category_no_selected.tga"))
		R1("CategoryState", categoryItem, "normal")
		categoryItem.OnRender()

	def OverInCategory(self, categoryIndex, categoryItem):
		self.ClearSubCategoryWindow()
		subCategoryBtns = self.CreateSubCategoryWindow(categoryIndex)
		if subCategoryBtns != None:
			subCategoryBtns.Show()
			(px,py) = categoryItem.parent.GetLocalPosition()
			maxYPos = py+categoryItem.parent.GetHeight()
			(x, y) = categoryItem.GetLocalPosition()

			if y <= 0:
				subCategoryBtns.SetPosition(px+categoryItem.GetWidth()+2,py)
			elif (py+y+(len(subCategoryBtns.children)*39)) <= maxYPos:
				subCategoryBtns.SetPosition(px+categoryItem.GetWidth()+2,py+y)
			else:
				subCategoryBtns.SetPosition(px+categoryItem.GetWidth()+2,maxYPos-(len(subCategoryBtns.children)*39)-1)
			R1("SubMenuPlace", subCategoryBtns, categoryItem)
			self.children["subCategoryBtns"]=subCategoryBtns

		# R1: the row under the mouse is lighter, the chosen one the dark well with the red line
		hover = _r1 is not None and categoryIndex != self.categoryIndex
		categoryItem.LoadImage(Img("category_hover" if hover else "category_selected.tga"))
		R1("CategoryState", categoryItem, "hover" if hover else "selected")
		categoryItem.OnRender()

	def UpdateSubCategoryWindow(self):
		if "subCategoryBtns" in self.children:
			subCategoryBtns = self.children["subCategoryBtns"]
			if subCategoryBtns != None:
				if subCategoryBtns.categoryIndex == self.categoryIndex:
					if self.categorySubIndex != -1:
						self.__ClickRadioButton(subCategoryBtns.children, self.categorySubIndex)

	def ClearSubCategoryWindow(self):
		if "subCategoryBtns" in self.children:
			subCategoryBtns = self.children["subCategoryBtns"]
			if subCategoryBtns != None:
				(x, y) = app.GetCursorPosition()
				(sx,sy) = subCategoryBtns.GetGlobalPosition()
				if x >= sx and x <= sx+115:
					if y >= sy and y <= sy+(len(subCategoryBtns.children)*39):
						return

				if subCategoryBtns:
					for children in subCategoryBtns.children:
						children.backText = None
					subCategoryBtns.children = None
					subCategoryBtns.Hide()

				self.children["subCategoryBtns"] = None

	def CreateSubCategoryWindow(self, categoryIndex):
		if categoryIndex not in itemShopCategoryData:
			return None
		categoryData = itemShopCategoryData[categoryIndex]["subCategory"]
		if len(categoryData) == 0:
			return None

		subCategoryBtns = ui.ImageBox()
		subCategoryBtns.SetParent(self)
		R1("SubMenu", subCategoryBtns, len(categoryData))
		children = []

		for j in range(len(categoryData)):
			categoryBtn = ui.RadioButton()
			categoryBtn.SetParent(subCategoryBtns)
			categoryBtn.SetUpVisual(Img("submenu_selected.tga"))
			categoryBtn.SetOverVisual(Img("submenu_selected2.tga"))
			categoryBtn.SetDownVisual(Img("submenu_selected2.tga", "submenu_down"))
			categoryBtn.SetHideToolTipEvent(ui.__mem_func__(self.ClearSubCategoryWindow))
			categoryBtn.SetEvent(self.ClickCategory, "", categoryIndex, j)
			categoryBtn.SetPosition(0,39*j)
			categoryBtn.Show()

			categoryBtnText = MultiTextLine()
			categoryBtnText.SetParent(categoryBtn)
			categoryBtnText.SetTextRange(15)
			categoryBtnText.SetPosition(categoryBtn.GetWidth()//2,8)
			categoryBtnText.SetTextType("horizontal#center")
			categoryBtnText.SetFontName("Tahoma:16")
			R1("SubMenuText", categoryBtnText)
			categoryBtnText.SetText(categoryData[j])
			categoryBtnText.Show()
			categoryBtn.backText = categoryBtnText
			children.append(categoryBtn)
		subCategoryBtns.categoryIndex = categoryIndex
		subCategoryBtns.children = children
		if self.categoryIndex == categoryIndex:
			if self.categorySubIndex != -1:
				self.__ClickRadioButton(subCategoryBtns.children, self.categorySubIndex)
		subCategoryBtns.SetSize(150, len(children)*39)
		return subCategoryBtns

	def RefreshItem(self):
		self.ClearItemList()
		itemListBox = self.children["itemListBox"]
		if self.categoryIndex in itemshopData:
			itemData = itemshopData[self.categoryIndex]
			if self.categorySubIndex == -1:
				allList = []
				for itemList in itemData:
					for shopItem in itemList:
						allList.append(shopItem)
				self.RefreshItemList(allList)
			else:
				if self.categorySubIndex >= len(itemData):
					return
				itemList = itemData[self.categorySubIndex]
				self.RefreshItemList(itemList)

	def SortList(self, itemDataList):
		# A body-part chest leads its tab; the rest keeps the server order.
		import ischests
		return ischests.ChestsFirst(itemDataList)
		sortData = []
		for itemData in itemDataList:
			sortItem = SortClass(itemData)
			sortData.append(sortItem)
		sortData.sort()
		itemDataListEx = []
		for shortItem in sortData:
			itemDataListEx.append(shortItem.arg)
		return itemDataListEx

	def ClearItemList(self):
		self.CloseAfkShop()
		itemListBox = self.children["itemListBox"]
		itemListBox.RemoveAllItems()

	def RefreshItemList(self, itemDataList):
		self.ClosePurchasesWindow()
		if len(itemDataList) == 0:
			return
		itemListBox = self.children["itemListBox"]

		itemDataList = self.SortList(itemDataList)
		itemWindowPtr = ItemWindow(itemListBox)
		itemWindowPtr.SetParent(itemListBox)
		itemWindowPtr.SetPosition(0,len(itemListBox.GetItems())*132, True)
		itemWindowPtr.Show()
		for shopItem in itemDataList:
			xItem = ItemShopItem()
			xItem.SetParent(itemWindowPtr)
			xItem.SetPosition(len(itemWindowPtr.children)*250,0)
			xItem.LoadData(shopItem)
			xItem.Show()
			itemWindowPtr.AppendWindow(xItem)
			if len(itemWindowPtr.children) == 3:
				itemListBox.AppendItem(itemWindowPtr)
				itemWindowPtr = ItemWindow(itemListBox)
				itemWindowPtr.SetParent(itemListBox)
				itemWindowPtr.SetPosition(0,len(itemListBox.GetItems())*132, True)
				itemWindowPtr.Show()
		if itemWindowPtr != None:
			if len(itemWindowPtr.children) > 0:
				itemListBox.AppendItem(itemWindowPtr)

	def InsertItemWithType(self, itemDataList, insertType):
		currentTime = app.GetGlobalTimeStamp()
		for key, data in itemshopData.items():
			for categoryItems in data:
				for itemData in categoryItems:
					if insertType == LIST_ITEM_DISCOUNT:
						if itemData[LIST_ITEM_DISCOUNT] > 0 or itemData[LIST_ITEM_TIME] > 0:
							if not itemData in itemDataList:
								itemDataList.append(itemData)
					elif insertType == LIST_ITEM_TOP_SELLING_INDEX:
						if itemData[LIST_ITEM_TOP_SELLING_INDEX] >= 0 and itemData[LIST_ITEM_TOP_SELLING_INDEX] <= 10:
							if not itemData in itemDataList:
								itemDataList.append(itemData)
					elif insertType == LIST_ITEM_ADDED_TIME:
						if itemData[LIST_ITEM_ADDED_TIME] > currentTime-(60*60*24*3):
							if not itemData in itemDataList:
								itemDataList.append(itemData)
					else:
						itemDataList.append(itemData)

		return itemDataList

	def OfferItems(self):
		self.ClearItemList()
		itemDataList = []
		itemDataList = self.InsertItemWithType(itemDataList, LIST_ITEM_DISCOUNT)
		self.RefreshItemList(itemDataList)

	def HotItems(self):
		self.ClearItemList()

		itemDataList = []
		itemDataList = self.InsertItemWithType(itemDataList, LIST_ITEM_TOP_SELLING_INDEX)
		self.RefreshItemList(itemDataList)

	def LoadFirstOpening(self):
		self.categoryIndex = -1
		self.categorySubIndex = -1
		self.ClearItemList()
		itemListBox = self.children["itemListBox"]

		if len(eventCategory) <= 3:
			itemWindowPtr = ItemWindow(itemListBox)
			itemWindowPtr.SetParent(itemListBox)
			itemWindowPtr.SetPosition(0,len(itemListBox.GetItems())*132, True)
			itemWindowPtr.Show()
			for banner in range(len(eventCategory)):
				xBanner = ItemShopBanner()
				xBanner.SetParent(itemWindowPtr)
				xBanner.SetPosition(len(itemWindowPtr.children)*250,0)
				xBanner.LoadData(banner)
				xBanner.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInBanner,banner, proxy(xBanner))
				xBanner.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutBanner, banner, proxy(xBanner))
				#xBanner.SetEvent(self.ClickBanner, "mouse_click", eventCategory[banner][1][0],eventCategory[banner][1][1])
				xBanner.Show()
				itemWindowPtr.AppendWindow(xBanner)
			if itemWindowPtr != None:
				if len(itemWindowPtr.children) > 0:
					itemListBox.AppendItem(itemWindowPtr)

		itemDataList = []
		itemDataList = self.InsertItemWithType(itemDataList, LIST_ITEM_TOP_SELLING_INDEX)
		itemDataList = self.InsertItemWithType(itemDataList, LIST_ITEM_DISCOUNT)
		itemDataList = self.InsertItemWithType(itemDataList, LIST_ITEM_ADDED_TIME)
		if len(itemDataList) == 0:
			itemDataList = self.InsertItemWithType(itemDataList, 99)
		itemDataList = self.SortList(itemDataList)
		self.RefreshItemList(itemDataList)

	def ClickBanner(self, emptyArg, categoryIndex, categorySubIndex):
		self.categoryIndex = categoryIndex
		self.categorySubIndex = categorySubIndex
		self.RefreshItem()

	def BuyDragonCoin(self):
		# "Koupit mince": the coin top-up page from the data file (no row = the button opens nothing).
		OpenLinkInBrowser(ItemShopLink("ITEMSHOP_BUY_COIN_URL"))

	def OpenWeb(self, url):
		self.CloseWeb()
		webWnd = WebWindow(self)
		webWnd.Open(url)
		self.children["WebWindow"] = webWnd

	def CloseWeb(self):
		if "WebWindow" in self.children:
			webWnd = self.children["WebWindow"]
			webWnd.Close()
			webWnd.Destroy()
			del self.children["WebWindow"]

	def OverOutBanner(self, index, bannerItem):
		bannerItem.LoadImage(IMG_DIR+eventCategory[index][0][0])
		bannerItem.OnRender(self.children["itemListBox"])

	def OverInBanner(self, index, bannerItem):
		bannerItem.LoadImage(IMG_DIR+eventCategory[index][0][1])
		bannerItem.OnRender(self.children["itemListBox"])

	def PurchaseBtn(self):
		self.OpenPurchasesWindow()

	def SetDragonCoinReal(self, dragonCoinValue):
		text = localeInfo.ITEMSHOP_DRAGONCOINT + "\n|cffF8BE47" + NumberToMoneyFormat(dragonCoinValue)
		self.children["dragonCoinText"].SetText(text)
	
	def SetDragonCoin(self, dragonCoinValue):
		if self.RealMoney==0:
			self.RealMoney = dragonCoinValue
			self.SetDragonCoinReal(self.RealMoney)
		else:
			self.NewMoney = dragonCoinValue
			if self.NewMoney == self.RealMoney:
				self.MoneyFlag = False
			else:
				self.MoneyFlag = True
				self.MoneyRange = self.NewMoney - self.RealMoney
				self.moneySize = 0

	def Open(self):
		# Catalog reply callbacks also call Open (once per category). Only a
		# hidden-to-visible open should refresh balances or restart AFK polling.
		wasVisible = self.IsShow()
		if not wasVisible:
			self._afkRequestAttempts = 0
			self.RefreshAfkRewards()
			self.RequestAfkRewards()
		if "sendPacketData" not in self.children:
			self.children["sendPacketData"] = 1
			self.children["LoadingImage"].Show()
			self.LoadFirstOpening()
			global UPDATE_TIME
			if getattr(app, "ENABLE_ITEMSHOP_BUNDLES", False):
				net.SendChatPacket("/ishop data_v2 %d" % UPDATE_TIME)
			else:
				net.SendChatPacket("/ishop data %d" % UPDATE_TIME)
			net.SendChatPacket("/ishop reacts")
		elif not wasVisible:
			# The offers and the balance came with the first open. Coins bought on
			# the website since then exist only on the server: ask for the balance.
			net.SendChatPacket("/ishop coins")

		self.Show()
		self.SetTop()

	def UpdateReactionForItem(self, itemID):
		if "itemListBox" not in self.children:
			return
		itemListBox = self.children["itemListBox"]
		for rowWindow in itemListBox.GetItems():
			if not hasattr(rowWindow, "children"):
				continue
			for child in rowWindow.children:
				try:
					if child and child.data and child.data[LIST_ITEM_ID] == itemID:
						child.RefreshReactionUI()
				except:
					pass

	def CloseLoading(self):
		self.children["LoadingImage"].Hide()

	def OnItemShopClosed(self):
		# The server answered ItemShopClosed (gate item_shop_open is off): no
		# offers arrive. Ask again on the next open, so the shop works as soon
		# as a GM opens the gate. The AFK shop shares this window and stays
		# reachable; without it there is nothing to show.
		self.children.pop("sendPacketData", None)
		self.children.pop("sendPacketDataLog", None)
		self.CloseLoading()
		import uiafkrewardshop
		if not uiafkrewardshop.IsSupported():
			self.Close()

	def OpenPurchasesWindow(self):
		self.CloseAfkShop()
		skin = getattr(self, "r1skin", None)
		if skin:
			skin.Page("log")
		self.children["itemListBox"].Hide()
		self.children["itemScrollBar"].Hide()
		self.children["categoryListBox"].Hide()
		self.children["categoryScrollBar"].Hide()

		self.children["PurchasesScrollBar"].Show()
		self.children["PurchasesListBox"].Show()

		if "sendPacketDataLog" not in self.children:
			self.children["sendPacketDataLog"] = 1
			self.children["LoadingImage"].Show()
			net.SendChatPacket("/ishop log")
		else:
			self.RefreshPurchasesWindow()

	def SortPurchasesWindow(self):
		global playerLog
		sortData = []
		for logData in playerLog:
			sortLog = SortClass(logData,True)
			sortData.append(sortLog)
		sortData.sort()
		logDataList = []
		for sortLog in sortData:
			logDataList.append(sortLog.arg)
		return logDataList

	def RefreshPurchasesWindow(self):

		PurchasesListBox = self.children["PurchasesListBox"]
		PurchasesListBox.Show()
		PurchasesListBox.RemoveAllItems()

		global playerLog
		playerLog = self.SortPurchasesWindow()

		logTitle = PurchasesLog(PurchasesListBox)
		logTitle.SetParent(PurchasesListBox)
		logTitle.LoadData(-1)
		logTitle.SetPosition(0,0, True)
		logTitle.Show()
		PurchasesListBox.AppendItem(logTitle)

		for j in range(len(playerLog)):
			logItem = PurchasesLog(PurchasesListBox)
			logItem.SetParent(PurchasesListBox)
			logItem.LoadData(j)
			logItem.SetPosition(0,len(PurchasesListBox.GetItems())*35, True)
			logItem.Show()
			PurchasesListBox.AppendItem(logItem)
		PurchasesListBox.Render(0)

	def ClosePurchasesWindow(self):
		skin = getattr(self, "r1skin", None)
		if skin:
			skin.Page("shop")
		self.children["PurchasesScrollBar"].Hide()
		self.children["PurchasesListBox"].Hide()

		self.children["itemListBox"].Show()
		self.children["itemScrollBar"].Show()
		self.children["categoryListBox"].Show()
		self.children["categoryListBox"].RefreshScroll()

	def Close(self):
		if self.afkShop and self.afkShop.IsShow():
			self.LoadFirstOpening()
		self.CloseAfkShop()
		self.CloseWeb()
		if self.wardrobeWindow:
			self.wardrobeWindow.Close()
		if self.costumeExchangeWindow:
			self.costumeExchangeWindow.Close()

		global buyQuestionDialog
		if buyQuestionDialog != None:
			buyQuestionDialog.Hide()
			buyQuestionDialog.Destroy()
			buyQuestionDialog=None

		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True
	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			btn=buttonList[buttonIndex]
		except IndexError:
			return
		for eachButton in buttonList:
			eachButton.SetUp()
		btn.Down()

class PurchasesLog(ui.ExpandedImageBox):
	def __del__(self):
		ui.ExpandedImageBox.__del__(self)
	def Destroy(self):
		self.childrenImages = {}
		self.childrenTextLine = {}
		self.parent = None
	def __init__(self, parent):
		ui.ExpandedImageBox.__init__(self)
		self.Destroy()
		self.parent = proxy(parent)
	def LoadData(self, index):
		if index >= 0:
			self.childrenImages["self"] = self
			self.LoadImage(Img("purch_img.tga"))

		try:
			logData = playerLog[index]
		except:
			return

		if index >= 0:
			dateText = logData[LOG_DATE_TEXT]
			accountText = logData[LOG_ACCOUNT]
			ipText = logData[LOG_IP]
			item.SelectItem(logData[LOG_ITEM])
			if logData[LOG_COUNT] > 1:
				itemText = "|cffF7BD48%sx%d|r" % (item.GetItemName(),logData[LOG_COUNT])
			else:
				itemText = "|cffF7BD48%s|r" % item.GetItemName()
			priceText = localeInfo.PURCHASES_PRICE_TEXT % NumberToMoneyFormat(logData[LOG_PRICE])
		else:
			dateText = localeInfo.PURCHASES_DATE
			accountText = localeInfo.PURCHASES_ACCOUNTID
			ipText = localeInfo.PURCHASES_IP
			itemText = localeInfo.PURCHASES_ITEMBOUGHT
			priceText = localeInfo.PURCHASES_PRICE

		textList = [
			[75,5,dateText],
			[260,5,accountText],
			[400,5,ipText],
			[600,5,itemText],
			[800,5,priceText],
		]
		for j in range(len(textList)):
			text = textList[j]
			logText = ui.TextLine()
			logText.SetParent(self)
			logText.SetFontName("Tahoma:13")
			logText.SetText(text[2])
			logText.SetHorizontalAlignCenter()
			if index >= 0:
				logText.SetPosition(text[0],text[1])
			else:
				logText.SetPosition(text[0],0)
			R1("LogText", logText, index < 0)
			logText.Show()
			self.childrenTextLine["text%d"%j] = logText

	def OnRender(self):
		listboxHeight = self.parent.GetHeight()
		(pgx,pgy) = self.parent.GetGlobalPosition()
		for key, textline in self.childrenTextLine.items():
			(igx,igy) = textline.GetGlobalPosition()
			if igy < pgy:
				textline.Hide()
			elif igy > (pgy+listboxHeight-25):
				textline.Hide()
			else:
				textline.Show()
		for key, image in self.childrenImages.items():
			(jgx,jgy) = image.GetGlobalPosition()
			imageHeight = image.GetHeight()
			if jgy < pgy:
				image.SetRenderingRect(0,ui.calculateRect(imageHeight-abs(jgy-pgy),imageHeight),0,0)
			elif jgy+imageHeight > (pgy+listboxHeight-8):
				calculate = (pgy+listboxHeight-8) - (jgy+imageHeight)
				if calculate == 0:
					return
				image.SetRenderingRect(0.0,0.0,0.0,ui.calculateRect(imageHeight-abs(calculate),imageHeight))
			else:
				image.SetRenderingRect(0,0,0,0)

class ItemShopBoard(ui.Window):
	CORNER_WIDTH = 7
	CORNER_HEIGHT = 7
	LINE_WIDTH = 7
	LINE_HEIGHT = 7
	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3
	def __init__(self):
		ui.Window.__init__(self)
		self.MakeBoard()
		self.MakeBase()
	def MakeBoard(self):
		cornerPath = IMG_DIR+"board/corner_"
		linePath = IMG_DIR+"board/"
		CornerFileNames = [ cornerPath+dir+".tga" for dir in ("left_top", "left_bottom", "right_top", "right_bottom") ]
		LineFileNames = [ linePath+dir+".tga" for dir in ("left", "right", "top", "bottom") ]
		self.Corners = []
		for fileName in CornerFileNames:
			Corner = ui.ExpandedImageBox()
			Corner.AddFlag("not_pick")
			Corner.LoadImage(fileName)
			Corner.SetParent(self)
			Corner.SetPosition(0, 0)
			Corner.Show()
			self.Corners.append(Corner)
		self.Lines = []
		for fileName in LineFileNames:
			Line = ui.ExpandedImageBox()
			Line.AddFlag("not_pick")
			Line.LoadImage(fileName)
			Line.SetParent(self)
			Line.SetPosition(0, 0)
			Line.Show()
			self.Lines.append(Line)
		self.Lines[self.L].SetPosition(0, self.CORNER_HEIGHT)
		self.Lines[self.T].SetPosition(self.CORNER_WIDTH, 0)
	def MakeBase(self):
		self.Base = ui.ExpandedImageBox()
		self.Base.AddFlag("not_pick")
		self.Base.LoadImage(IMG_DIR+"board/base.tga")
		self.Base.SetParent(self)
		self.Base.SetPosition(self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Base.Show()
	def __del__(self):
		ui.Window.__del__(self)
	def Destroy(self):
		self.Base=0
		self.Corners=0
		self.Lines=0
		self.CORNER_WIDTH = 0
		self.CORNER_HEIGHT = 0
		self.LINE_WIDTH = 0
		self.LINE_HEIGHT = 0
		self.LT = 0
		self.LB = 0
		self.RT = 0
		self.RB = 0
		self.L = 0
		self.R = 0
		self.T = 0
		self.B = 0
	def SetSize(self, width, height):
		width = max(self.CORNER_WIDTH*2, width)
		height = max(self.CORNER_HEIGHT*2, height)
		ui.Window.SetSize(self, width, height)
		self.Corners[self.LB].SetPosition(0, height - self.CORNER_HEIGHT)
		self.Corners[self.RT].SetPosition(width - self.CORNER_WIDTH, 0)
		self.Corners[self.RB].SetPosition(width - self.CORNER_WIDTH, height - self.CORNER_HEIGHT)
		self.Lines[self.R].SetPosition(width - self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Lines[self.B].SetPosition(self.CORNER_HEIGHT, height - self.CORNER_HEIGHT)
		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.LINE_HEIGHT) / self.LINE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.LINE_WIDTH) / self.LINE_WIDTH
		self.Lines[self.L].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.T].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		if self.Base:
			self.Base.SetRenderingRect(0, 0, horizontalShowingPercentage, verticalShowingPercentage)

class WebWindow(ItemShopBoard):
	def __del__(self):
		ItemShopBoard.__del__(self)
	def Destroy(self):
		self.oldPos=(0,0)
		self.closeBtn=None
		self.parent = None
	def __init__(self, parent):
		ItemShopBoard.__init__(self)
		self.Destroy()
		self.parent = proxy(parent)
		self.LoadWindow()
	def LoadWindow(self):
		self.AddFlag("attach")
		self.AddFlag("float")
		#self.AddFlag("movable")
		self.SetSize(450*2,450)
		closeBtn = ui.Button()
		closeBtn.SetParent(self)
		closeBtn.SetUpVisual(IMG_DIR+"close_0.tga")
		closeBtn.SetOverVisual(IMG_DIR+"close_1.tga")
		closeBtn.SetDownVisual(IMG_DIR+"close_2.tga")
		closeBtn.SetPosition(self.GetWidth()-closeBtn.GetWidth(),0)
		closeBtn.SetEvent(self.parent.CloseWeb)
		closeBtn.Show()
		self.closeBtn=closeBtn

	def Close(self):
		#app.HideWebPage()
		self.Hide()

	def Open(self, url):
		self.SetSize(450*2,450)
		self.Show()
		self.SetTop()
		self.SetCenterPosition()

		x, y = self.GetGlobalPosition()
		sx, sy = x + 10, y + 30
		ex, ey = sx + self.GetWidth() - 20, sy + self.GetHeight() - 40
		app.ShowWebPage(url, (sx, sy, ex, ey))

	def OnUpdate(self):
		newPos = self.GetGlobalPosition()
		if newPos == self.oldPos:
			return
		self.oldPos = newPos
		x, y = newPos
		sx, sy = x + 10, y + 30
		ex, ey = sx + self.GetWidth() - 20, sy + self.GetHeight() - 40
		app.MoveWebPage((sx, sy, ex, ey))

class BuyWindow(ItemShopBoard):
	def __del__(self):
		ItemShopBoard.__del__(self)
	def __init__(self):
		ItemShopBoard.__init__(self)
		self.AddFlag("attach")
		self.AddFlag("float")
		self.Destroy()
		self.r1 = R1("BuyDialog", self)
		buyText = MultiTextLine()
		buyText.SetParent(self)
		buyText.SetTextRange(25)
		buyText.SetPosition(self.GetWidth()//2,28)
		buyText.SetTextType("horizontal#center")
		buyText.SetFontName("Tahoma:16")
		buyText.Show()
		self.children["buyText"] = buyText
		yesBtn = ui.Button()
		yesBtn.SetParent(self)
		yesBtn.SetUpVisual(IMG_DIR+"buy_0.tga")
		yesBtn.SetOverVisual(IMG_DIR+"buy_1.tga")
		yesBtn.SetDownVisual(IMG_DIR+"buy_2.tga")
		yesBtn.SetText(localeInfo.YES)
		yesBtn.Show()
		self.children["yesBtn"] = yesBtn
		cancelBtn = ui.Button()
		cancelBtn.SetParent(self)
		cancelBtn.SetUpVisual(IMG_DIR+"cancel_0.tga")
		cancelBtn.SetOverVisual(IMG_DIR+"cancel_1.tga")
		cancelBtn.SetDownVisual(IMG_DIR+"cancel_2.tga")
		cancelBtn.SetText(localeInfo.UI_CANCEL)
		cancelBtn.Show()
		self.children["cancelBtn"] = cancelBtn
		if self.r1:
			self.__DressR1()
	def __DressR1(self):
		try:
			self.r1.Dress()
		except Exception:
			import uir1
			uir1.TraceFailure("Item Shop dialog")
			self.r1.Undo()
			self.r1 = None
	def Destroy(self):
		self.children={}
	def SetText(self, text):
		buyText = self.children["buyText"]
		buyText.SetText(text)
		(x, y) = buyText.GetTextSize()
		(minWidth,minHeight) = (256,142)
		if x+40 > minWidth:
			minWidth = x+40
		if not ((minWidth%2) == 0):
			minWidth+=1
		self.SetSize(minWidth,minHeight)
		buyText.SetPosition(self.GetWidth()//2,28)
		self.children["yesBtn"].SetPosition((self.GetWidth()//2)-self.children["yesBtn"].GetWidth()-15,94)
		self.children["cancelBtn"].SetPosition((self.GetWidth()//2)+15,94)
		if getattr(self, "r1", None):
			self.r1.Layout()
	def SetCancelEvent(self, func):
		self.children["cancelBtn"].SetEvent(func)
	def SetAcceptEvent(self, func):
		self.children["yesBtn"].SetEvent(func)
	def OnPressEscapeKey(self):
		self.children["cancelBtn"].CallEvent()
		return True

class SortClass:
	def __init__(self, arg, isLog = False):
		self.arg = arg
		self.isLog = isLog
	def __del__(self):
		self.arg = []
	def __lt__(self, other):
		if self.isLog:
			return self.arg[LOG_DATE] >= other.arg[LOG_DATE]
		else:
			currentTime = app.GetGlobalTimeStamp()
			# hot item
			if self.arg[LIST_ITEM_TOP_SELLING_INDEX] <= 10 or other.arg[LIST_ITEM_TOP_SELLING_INDEX] <= 10:
				return self.arg[LIST_ITEM_TOP_SELLING_INDEX] <= other.arg[LIST_ITEM_TOP_SELLING_INDEX]
			# time offer
			if self.arg[LIST_ITEM_TIME] != 0 or other.arg[LIST_ITEM_TIME] != 0:
				if self.arg[LIST_ITEM_TIME] > 0 and other.arg[LIST_ITEM_TIME] > 0:
					return ((self.arg[LIST_ITEM_TIME]-currentTime) <= (other.arg[LIST_ITEM_TIME]-currentTime))
				else:
					return self.arg[LIST_ITEM_TIME] >= other.arg[LIST_ITEM_TIME]
			# discount
			if self.arg[LIST_ITEM_DISCOUNT] != 0 or other.arg[LIST_ITEM_DISCOUNT] != 0:
				return self.arg[LIST_ITEM_DISCOUNT] >= other.arg[LIST_ITEM_DISCOUNT]
			# added time
			if self.arg[LIST_ITEM_ADDED_TIME] > currentTime-(60*60*24*3) or other.arg[LIST_ITEM_ADDED_TIME] > currentTime-(60*60*24*3):
				return self.arg[LIST_ITEM_ADDED_TIME] >= other.arg[LIST_ITEM_ADDED_TIME]
			return self.arg[LIST_ITEM_ID] >= other.arg[LIST_ITEM_ID]

class ItemShopBanner(ui.ExpandedImageBox):
	def __del__(self):
		ui.ExpandedImageBox.__del__(self)
	def Destroy(self):
		self.bannerIndex = -1
		self.childrenImages = {}
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)
		self.Destroy()
	def LoadData(self, bannerIndex):
		self.bannerIndex=bannerIndex
		if bannerIndex >= len(eventCategory):
			return
		self.LoadImage(IMG_DIR+eventCategory[bannerIndex][0][0])
		self.childrenImages["self"] = self
	def OnUpdate(self):
		pass
	def OnRender(self, parent):
		listboxHeight = parent.GetHeight()
		(pgx,pgy) = parent.GetGlobalPosition()
		for key, image in self.childrenImages.items():
			(jgx,jgy) = image.GetGlobalPosition()
			imageHeight = image.GetHeight()
			if jgy < pgy:
				image.SetRenderingRect(0,ui.calculateRect(imageHeight-abs(jgy-pgy),imageHeight),0,0)
			elif jgy+imageHeight > (pgy+listboxHeight-8):
				calculate = (pgy+listboxHeight-8) - (jgy+imageHeight)
				if calculate == 0:
					return
				image.SetRenderingRect(0.0,0.0,0.0,ui.calculateRect(imageHeight-abs(calculate),imageHeight))
			else:
				image.SetRenderingRect(0,0,0,0)

class ItemShopItem(ui.ExpandedImageBox):
	def __del__(self):
		ui.ExpandedImageBox.__del__(self)
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)
		self.Destroy()
		self.buyCount=1
		self.LoadImage(Img("item_box.tga"))
		self.childrenImages["self"] = self
	def Destroy(self):
		self.data = []
		self.buyCount=0
		self.butButtonSet = False
		self.childrenImages = {}
		self.childrenTextLine = {}

	def LoadData(self, itemData):
		self.data = itemData
		self.SetItem(itemData[LIST_ITEM_VNUM])
		self.SetCount()
		self.SetItemName()
		self.SetVoucherBadge()
		self.SetBuyButton(itemData[LIST_ITEM_TIME])
		self.SetPrice(itemData[LIST_ITEM_PRICE],itemData[LIST_ITEM_DISCOUNT])
		self.SetTime(itemData[LIST_ITEM_TIME])
		self.SetReactions()

		if itemData[LIST_ITEM_TOP_SELLING_INDEX] >= 0 and itemData[LIST_ITEM_TOP_SELLING_INDEX] <= 10:
			self.SetItemType(1)
		elif itemData[LIST_ITEM_TIME] > 0 or itemData[LIST_ITEM_DISCOUNT] > 0:
			self.SetItemType(3)
		elif itemData[LIST_ITEM_ADDED_TIME] > app.GetGlobalTimeStamp()-(60*60*24*3):
			self.SetItemType(2)

	def SetReactions(self):
		self.ClearChildren("likeBtn")
		self.ClearChildren("dislikeBtn")
		self.ClearChildren("likeCountText")
		self.ClearChildren("dislikeCountText")

		likeBtn = ui.ExpandedImageBox()
		likeBtn.SetParent(self)
		likeBtn.LoadImage(self.ReactionImage("like"))
		likeBtn.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OverInLikeBtn)
		likeBtn.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OverOutLikeBtn)
		likeBtn.SetEvent(ui.__mem_func__(self.ClickLike), "mouse_click")
		likeBtn.SetPosition(180,35)
		likeBtn.Show()
		self.childrenImages["likeBtn"] = likeBtn

		dislikeBtn = ui.ExpandedImageBox()
		dislikeBtn.SetParent(self)
		dislikeBtn.LoadImage(self.ReactionImage("dislike"))
		dislikeBtn.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OverInDislikeBtn)
		dislikeBtn.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OverOutDislikeBtn)
		dislikeBtn.SetEvent(ui.__mem_func__(self.ClickDislike), "mouse_click")
		dislikeBtn.SetPosition(220,35)
		dislikeBtn.Show()
		self.childrenImages["dislikeBtn"] = dislikeBtn

		likeCountText = ui.TextLine()
		likeCountText.SetParent(self)
		likeCountText.SetFontName("Tahoma:12")
		likeCountText.SetHorizontalAlignCenter()
		likeCountText.SetPosition(180 + (likeBtn.GetWidth() // 2), 35 + likeBtn.GetHeight() + 2)
		likeCountText.Show()
		self.childrenTextLine["likeCountText"] = likeCountText

		dislikeCountText = ui.TextLine()
		dislikeCountText.SetParent(self)
		dislikeCountText.SetFontName("Tahoma:12")
		dislikeCountText.SetHorizontalAlignCenter()
		dislikeCountText.SetPosition(220 + (dislikeBtn.GetWidth() // 2), 35 + dislikeBtn.GetHeight() + 2)
		dislikeCountText.Show()
		self.childrenTextLine["dislikeCountText"] = dislikeCountText
		R1("CardReactions", self)

		self.RefreshReactionUI()

	def MyVote(self):
		if not self.data:
			return 0
		return int(itemshopReactions.get(int(self.data[LIST_ITEM_ID]), {}).get("myVote", 0))

	def ReactionImage(self, kind, hover=False):
		"""like / dislike: the hover picture under the mouse; in the R1 look the player's own vote shows the filled
		thumb (like_active / dislike_active), the original look keeps its two pictures."""
		original = kind + ("_hover.tga" if hover else ".tga")
		if self.MyVote() == (1 if kind == "like" else -1):
			return Img(original, kind + "_active")
		return Img(original)

	def ShowReaction(self, kind, hover=None):
		key = kind + "Btn"
		if key not in self.childrenImages:
			return
		if hover is None:
			hover = getattr(self, "reactionHover", None) == kind
		else:
			self.reactionHover = kind if hover else None
		self.childrenImages[key].LoadImage(self.ReactionImage(kind, hover))

	def __OverInLikeBtn(self):
		self.ShowReaction("like", True)

	def __OverOutLikeBtn(self):
		self.ShowReaction("like", False)

	def __OverInDislikeBtn(self):
		self.ShowReaction("dislike", True)

	def __OverOutDislikeBtn(self):
		self.ShowReaction("dislike", False)

	def RefreshReactionUI(self):
		if not self.data:
			return
		if "likeCountText" not in self.childrenTextLine or "dislikeCountText" not in self.childrenTextLine:
			return
		itemID = int(self.data[LIST_ITEM_ID])
		global itemshopReactions
		if itemID in itemshopReactions:
			info = itemshopReactions[itemID]
			likes = info.get("likes", 0)
			dislikes = info.get("dislikes", 0)
		else:
			likes = 0
			dislikes = 0

		self.childrenTextLine["likeCountText"].SetText(self.__FormatCompactNumber(likes))
		self.childrenTextLine["dislikeCountText"].SetText(self.__FormatCompactNumber(dislikes))
		self.ShowReaction("like")
		self.ShowReaction("dislike")

	def __FormatCompactNumber(self, n):
		try:
			n = int(n)
		except:
			return "0"
		if n < 1000:
			return str(n)
		k = n // 1000
		h = (n % 1000) // 100
		if h <= 0:
			return "%dk" % k
		return "%dk%d" % (k, h)

	def ClickLike(self):
		if not self.data:
			return
		itemID = int(self.data[LIST_ITEM_ID])
		global itemshopReactions
		current = 0
		if itemID in itemshopReactions:
			current = int(itemshopReactions[itemID].get("myVote", 0))
		newVote = 0
		if current != 1:
			newVote = 1
		net.SendChatPacket("/ishop vote %d %d" % (itemID, newVote))

	def ClickDislike(self):
		if not self.data:
			return
		itemID = int(self.data[LIST_ITEM_ID])
		global itemshopReactions
		current = 0
		if itemID in itemshopReactions:
			current = int(itemshopReactions[itemID].get("myVote", 0))
		newVote = 0
		if current != -1:
			newVote = -1
		net.SendChatPacket("/ishop vote %d %d" % (itemID, newVote))

	def ClearChildren(self, childrenName):
		if childrenName in self.childrenTextLine:
			self.childrenTextLine[childrenName].Hide()
			self.childrenTextLine[childrenName].Destroy()
			del self.childrenTextLine[childrenName]
		if childrenName in self.childrenImages:
			self.childrenImages[childrenName].Hide()
			self.childrenImages[childrenName].Destroy()
			del self.childrenImages[childrenName]

	def FormatTime(self, seconds):
		if seconds <= 0:
			if self.butButtonSet == False:
				self.SetBuyButton(self.data[LIST_ITEM_TIME])
			return "|cffFF7B7B0h 0m 0s"
		m, s = divmod(seconds, 60)
		h, m = divmod(m, 60)
		d, h = divmod(h, 24)
		if d > 0:
			return "|cffFF7B7B%dd %dh %dm %ds"%(d,h,m,s)
		return "|cffFF7B7B%dh %dm %ds" % (h,m,s)

	def OnUpdate(self):
		if "timeText" in self.childrenTextLine:
			self.childrenTextLine["timeText"].SetText(self.FormatTime(self.data[LIST_ITEM_TIME]-app.GetGlobalTimeStamp()))

	def SetTime(self, time):
		self.ClearChildren("timeText")
		if time != 0:
			self.butButtonSet = False
			
			timeText = ui.TextLine()
			timeText.SetParent(self)
			timeText.SetPosition(168,65)
			timeText.SetWindowHorizontalAlignLeft()
			timeText.SetFontName("Tahoma:13")
			R1("CardTime", timeText)
			timeText.Show()
			self.childrenTextLine["timeText"] = timeText

	def SetBuyButton(self, time):
		self.ClearChildren("buyButton")
		self.butButtonSet = False
		buyButton = ui.ExpandedImageBox()
		buyButton.SetParent(self)

		if time != 0 and app.GetGlobalTimeStamp() > time:
			buyButton.LoadImage(Img("button_buy_disabled.tga"))
			self.butButtonSet = True
		else:
			buyButton.LoadImage(Img("buy_0.tga"))
			buyButton.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInBuyBtn)
			buyButton.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutBuyBtn)
			buyButton.SetEvent(ui.__mem_func__(self.ClickBuyBtn),"mouse_click")
		buyButton.SetPosition(168,82)
		buyButton.Show()
		self.childrenImages["buyButton"] = buyButton

		buyBtnText = ui.TextLine()
		buyBtnText.SetParent(buyButton)
		buyBtnText.SetHorizontalAlignCenter()
		buyBtnText.SetVerticalAlignCenter()
		buyBtnText.SetWindowHorizontalAlignCenter()
		buyBtnText.SetWindowVerticalAlignCenter()
		buyBtnText.SetText(localeInfo.ITEMSHOP_BUY)
		buyBtnText.SetOutline(True)
		buyBtnText.Show()
		self.childrenTextLine["buyBtnText"] = buyBtnText
		R1("CardBuy", self, buyButton, buyBtnText)

	def ClickBuyBtn(self, emptyArg):
		time = self.data[LIST_ITEM_TIME]
		if time != 0 and app.GetGlobalTimeStamp() > time:
			return
		
		global buyQuestionDialog
		if buyQuestionDialog == None:
			buyQuestionDialog = BuyWindow()

		text = ""
		
		price = self.data[LIST_ITEM_PRICE]*self.buyCount
		discount = self.data[LIST_ITEM_DISCOUNT]
		if discount > 0:
			price = (price * (100 - discount)) // 100

		item.SelectItem(self.data[LIST_ITEM_VNUM])
		if self.DeliveredCount() > 1:
			text+=localeInfo.ITEMSHOP_BUY_TEXT_COUNT % (item.GetItemName(),self.DeliveredCount())
		else:
			text+=localeInfo.ITEMSHOP_BUY_TEXT % item.GetItemName()

		text+="\n"
		text+=localeInfo.ITEMSHOP_PRICE % price

		buyQuestionDialog.SetText(text)
		buyQuestionDialog.SetAcceptEvent(lambda count=self.buyCount: self.AcceptBuy(count))
		buyQuestionDialog.SetCancelEvent(self.CloseQuestionDialog)
		buyQuestionDialog.SetCenterPosition()
		buyQuestionDialog.SetTop()
		buyQuestionDialog.Show()

	def CloseQuestionDialog(self):
		global buyQuestionDialog
		if buyQuestionDialog!= None:
			buyQuestionDialog.Hide()
			buyQuestionDialog.Destroy()
			buyQuestionDialog=None

	def AcceptBuy(self, count=None):
		if count is None:
			count = self.buyCount
		command = "/ishop buy_v2" if getattr(app, "ENABLE_ITEMSHOP_BUNDLES", False) else "/ishop buy"
		net.SendChatPacket("%s %d %d"%(command,self.data[LIST_ITEM_ID],count))
		self.CloseQuestionDialog()

	def EmptyFunction(self):
		pass

	def OverOutBuyBtn(self):
		if "buyButton" in self.childrenImages:
			self.childrenImages["buyButton"].LoadImage(Img("buy_0.tga"))

	def OverInBuyBtn(self):
		if "buyButton" in self.childrenImages:
			self.childrenImages["buyButton"].LoadImage(Img("buy_1.tga"))

	def SetPrice(self, price, discount):
		self.ClearChildren("lineImage")
		self.ClearChildren("itemPrice")

		itemPrice = MultiTextLine()
		itemPrice.SetParent(self)
		itemPrice.SetTextRange(20)
		itemPrice.SetPosition(60, 35)
		itemPrice.SetTextType("horizontal#left")
		itemPrice.SetFontName("Tahoma:13")
		R1("CardPrice", itemPrice)

		price = price*self.buyCount

		text= ""
		if discount > 0:
			newPrice = (price * (100 - discount)) // 100

			text = localeInfo.ITEMSHOP_PRICE_ONLY_TEXT % NumberToMoneyFormat(price)
			itemPriceEx = ui.TextLine()
			itemPriceEx.SetParent(self)
			itemPriceEx.SetText(text)
			(xSize,ySize) = itemPriceEx.GetTextSize()

			text = localeInfo.ITEMSHOP_PRICE_WITH_DISCOUNT % (NumberToMoneyFormat(price),discount)
			text+="\n"
			text+="     "
			text+=localeInfo.ITEMSHOP_PRICE_ONLY_TEXT % NumberToMoneyFormat(newPrice)

			lineImage = ui.ExpandedImageBox()
			lineImage.SetParent(itemPrice)
			lineImage.LoadImage(IMG_DIR+"line.tga")
			lineImage.SetDiffuseColor(1.0,0.0,0.0,0.9)
			scaleCalc = float(xSize)*(1.0/10.0)
			lineImage.SetScale(scaleCalc, 1.0)
			lineImage.SetPosition(17,(ySize//2)+1)
			R1("CardStrike", itemPrice, lineImage, localeInfo.ITEMSHOP_PRICE_ONLY_TEXT % NumberToMoneyFormat(price))
			lineImage.Show()
			self.childrenImages["lineImage"] = lineImage

			self.SetItemType(3)
		else:
			text = localeInfo.ITEMSHOP_PRICE % NumberToMoneyFormat(price)

		itemPrice.SetText(text)
		itemPrice.Show()
		self.childrenTextLine["itemPrice"] = itemPrice

	def SetItemName(self):
		self.ClearChildren("itemName")
		offerVnum = self.data[LIST_ITEM_VNUM]
		# A costume voucher offer is shown as the costume; the badge and the
		# purchase dialog keep the delivered voucher explicit (ALTHEA-595).
		item.SelectItem(iscostumevoucher.DisplayVnum(offerVnum))
		name = item.GetItemName()
		item.SelectItem(offerVnum)
		itemName = ui.TextLine()
		itemName.SetParent(self)
		itemName.SetWindowHorizontalAlignLeft()
		itemName.SetFontName("Tahoma:13")
		itemName.SetPosition(60,15)
		itemName.SetText("|cffF7BD48"+name)
		#itemName.SetFontColor(247,189,72)
		itemName.Show()
		self.childrenTextLine["itemName"] = itemName
		R1("CardName", itemName, name)

	def SetVoucherBadge(self):
		self.ClearChildren("voucherBadge")
		if not iscostumevoucher.IsVoucher(self.data[LIST_ITEM_VNUM]):
			return
		badge = ui.TextLine()
		badge.SetParent(self)
		badge.SetWindowHorizontalAlignLeft()
		badge.SetFontName("Tahoma:12")
		badge.SetPosition(60, 88)
		badge.SetPackedFontColor(0xff8BBDFF)
		badge.SetOutline(True)
		badge.SetText("[ %s ]" % getattr(localeInfo, "COSTUME_VOUCHER_BADGE", "Voucher"))
		R1("CardBadge", badge)
		badge.Show()
		self.childrenTextLine["voucherBadge"] = badge

	def OfferUnits(self):
		return max(1, self.data[LIST_ITEM_COUNT] if len(self.data) > LIST_ITEM_COUNT else 1)

	def DeliveredCount(self):
		return self.buyCount * self.OfferUnits()

	def MaxOffers(self):
		# Like the server's IsValidPurchaseCount: a stackable item at most one stack
		# (MAX_BUY_COUNT pieces) in whole offers, any other item one offer.
		item.SelectItem(self.data[LIST_ITEM_VNUM])
		if not item.IsFlag(item.ITEM_FLAG_STACKABLE):
			return 1
		return max(1, MAX_BUY_COUNT // self.OfferUnits())

	def SetCountUnits(self):
		# A bundle offer says how many pieces the typed offers deliver ("= 30 ks").
		units = self.childrenTextLine.get("CountUnits")
		if units:
			units.SetText(localeInfo.ITEMSHOP_BUNDLE_PIECES % self.DeliveredCount())

	def SetCount(self):
		self.ClearChildren("CountBg")
		self.ClearChildren("CountText")
		self.ClearChildren("CountLeft")
		self.ClearChildren("CountRight")
		self.ClearChildren("CountUnits")
		if not item.IsFlag(item.ITEM_FLAG_STACKABLE):
			return

		CountLeft = ui.ExpandedImageBox()
		CountLeft.SetParent(self)
		CountLeft.LoadImage(Img("count_left.tga"))
		CountLeft.SetPosition(60,85)
		CountLeft.SetEvent(ui.__mem_func__(self.ClickCount),"mouse_click",0)
		CountLeft.Show()
		self.childrenImages["CountLeft"] = CountLeft

		CountBg = ui.ExpandedImageBox()
		CountBg.SetParent(self)
		CountBg.LoadImage(Img("count_back.tga"))
		# Wide enough for the digits of the largest count.
		countWidth = max(CountBg.GetWidth(), 8*len(str(self.MaxOffers()))+6)
		CountBg.SetScale(float(countWidth)/CountBg.GetWidth(), 1.0)
		CountBg.SetSize(countWidth, CountBg.GetHeight())
		CountBg.SetPosition(60+CountLeft.GetWidth(),85)
		CountBg.Show()
		self.childrenImages["CountBg"] = CountBg

		CountText = ui.EditLine()
		CountText.SetParent(CountBg)
		CountText.SetPosition(3,2)
		CountText.SetSize(CountBg.GetWidth()-6,CountBg.GetHeight()-2)
		CountText.SetNumberMode()
		CountText.SetMax(len(str(self.MaxOffers())))
		CountText.SetText(str(self.buyCount))
		CountText.OnIMEUpdate = ui.__mem_func__(self.OnCountUpdate)
		CountText.SetOnFocusEvent(ui.__mem_func__(self.OnCountFocus))
		CountText.SetKillFocusEvent(ui.__mem_func__(self.OnCountKillFocus))
		CountText.SetReturnEvent(ui.__mem_func__(CountText.KillFocus))
		CountText.SetEscapeEvent(ui.__mem_func__(CountText.KillFocus))
		CountText.Show()
		self.childrenTextLine["CountText"] = CountText

		CountRight = ui.ExpandedImageBox()
		CountRight.SetParent(self)
		CountRight.LoadImage(Img("count_right.tga"))
		CountRight.SetPosition(60+CountLeft.GetWidth()+CountBg.GetWidth(),85)
		CountRight.SetEvent(ui.__mem_func__(self.ClickCount),"mouse_click",1)
		CountRight.Show()
		self.childrenImages["CountRight"] = CountRight

		if self.OfferUnits() > 1:
			CountUnits = ui.TextLine()
			CountUnits.SetParent(self)
			CountUnits.SetPosition(60+CountLeft.GetWidth()+CountBg.GetWidth()+CountRight.GetWidth()+4,87)
			CountUnits.Show()
			self.childrenTextLine["CountUnits"] = CountUnits
			self.SetCountUnits()
		R1("CardCount", self)

	def ClickCount(self,emptyArg, btnType):
		value = 1
		if app.IsPressed(app.DIK_LCONTROL):
			value += 4
		if btnType == 0:
			value = -value
		self.SetBuyCount(self.buyCount + value)

	def OnCountFocus(self):
		# Typing replaces the count; an empty field keeps it (OnCountKillFocus).
		self.childrenTextLine["CountText"].SetText("")

	def OnCountUpdate(self):
		countText = self.childrenTextLine["CountText"]
		ui.EditLine.OnIMEUpdate(countText)
		if countText.GetText():
			self.SetBuyCount(int(countText.GetText()))

	def OnCountKillFocus(self):
		self.childrenTextLine["CountText"].SetText(str(self.buyCount))

	def SetBuyCount(self, buyCount):
		# The field counts offers; one offer delivers OfferUnits() pieces (Quote on the server).
		self.buyCount = min(max(1, buyCount), self.MaxOffers())
		countText = self.childrenTextLine.get("CountText")
		if countText and countText.GetText() != str(self.buyCount):
			countText.SetText(str(self.buyCount))
		self.SetCountUnits()

		itemData = self.data
		self.SetPrice(itemData[LIST_ITEM_PRICE],itemData[LIST_ITEM_DISCOUNT])

	def SetItem(self, itemVnum):
		self.ClearChildren("itemImage")
		self.ClearChildren("itemCount")
		# Costume vouchers show the costume icon (female drawing for a female
		# character where one exists); layout follows the costume's size.
		item.SelectItem(iscostumevoucher.IconVnum(itemVnum, CurrentPlayerRace()))
		iconFileName = item.GetIconImageFileName()
		item.SelectItem(iscostumevoucher.DisplayVnum(itemVnum))
		(width,height) = item.GetItemSize()
		centerIcon = _r1 is not None and item.GetItemType() != item.ITEM_TYPE_COSTUME
		item.SelectItem(itemVnum)
		(xPos, yPos) = (1,46)
		if height == 1:
			xPos = 14
		elif height == 2:
			yPos -= 20
			xPos = 14
		elif height == 3:
			yPos -= 30
			xPos = 14
		itemImage = ui.ExpandedImageBox()
		itemImage.SetParent(self)
		itemImage.LoadImage(iconFileName)
		itemImage.SetPosition(xPos,yPos)
		if centerIcon:
			R1("CardIcon", itemImage)
		itemImage.SetEvent(ui.__mem_func__(self.PreviewItem), "mouse_click")
		itemImage.SetMouseRightButtonDownEvent(ui.__mem_func__(self.OnMouseRightButtonDown))
		if app.ENABLE_SHOW_CHEST_DROP:
			itemImage.SAFE_SetStringEvent("MOUSE_RIGHT_BUTTON_UP", self.RightClickItem, itemVnum)
			itemImage.SAFE_SetStringEvent("MOUSE_RIGHT_DOWN", self.RightClickItem, itemVnum)
		itemImage.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,itemVnum)
		itemImage.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
		itemImage.Show()
		self.childrenImages["itemImage"] = itemImage
		
	def PreviewItem(self):
		if not self.data:
			return False
		return self.OpenItemPreview(self.data[LIST_ITEM_VNUM])

	def OpenItemPreview(self, itemVnum):
		"""A click on the offer image previews it: the costume, mount, pet or
		elf on the model, a chest its contents (Shift no longer needed)."""
		if self.OpenCostumePreview(itemVnum):
			return True
		return self.OpenChestPreview(itemVnum)

	def OnMouseRightButtonDown(self):
		if not self.data:
			return False

		self.RightClickItem(self.data[LIST_ITEM_VNUM])
		return True

	def RightClickItem(self, itemVnum):
		# Right click (with or without Shift) stays an alias of the left click.
		self.OpenItemPreview(itemVnum)

	def OpenChestPreview(self, itemVnum):
		if not app.ENABLE_SHOW_CHEST_DROP:
			return False

		item.SelectItem(itemVnum)
		itemType = item.GetItemType()
		if not (item.ITEM_TYPE_GIFTBOX == itemType or item.ITEM_TYPE_TREASURE_BOX == itemType or item.ITEM_TYPE_GACHA == itemType):
			return False

		interface = osfInfo.GetInterfaceInstance()
		if not interface:
			return False

		if not hasattr(interface, "dlgChestDrop") or not interface.dlgChestDrop:
			return False

		return bool(interface.dlgChestDrop.RequestPreviewByVnum(itemVnum))

	def OpenCostumePreview(self, itemVnum):
		"""Shared click preview for equipment, companions and costume vouchers."""
		if not getattr(app, "ENABLE_RENDER_TARGET_PREVIEW", False):
			return False
		costumeVnum = iscostumevoucher.DisplayVnum(itemVnum)
		previewType, previewVnum = itempreview.Resolve(item, costumeVnum)
		item.SelectItem(itemVnum)
		if not previewType:
			return False
		interface = osfInfo.GetInterfaceInstance()
		if not interface or not hasattr(interface, "OpenRenderTargetWindow"):
			return False
		# A VIP elf outfit is worn by the elf-form Buffi, not by the viewer:
		# the preview opens the elf race the outfit is drawn as.
		import vipelfvisual
		elf = vipelfvisual.PreviewModel(costumeVnum)
		if elf:
			import uirendertargetview
			previewVnum, previewType = elf[0], uirendertargetview.TYPE_MONTER
		# uirendertargetview opens on the viewer's own class and sex.
		osfInfo.RENDER_TARGET_ITEM_VNUM = previewVnum
		osfInfo.RENDER_TARGET_ITEM_TYPE = previewType
		interface.OpenRenderTargetWindow()
		return True

	def OverInItem(self, itemVnum):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				tooltip = interface.tooltipItem
				if iscostumevoucher.IsVoucher(itemVnum) and hasattr(tooltip, "SetCostumeVoucherOfferToolTip"):
					tooltip.SetCostumeVoucherOfferToolTip(itemVnum)
				else:
					tooltip.SetItemToolTip(itemVnum, itemShopOffer=True)
	def OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def SetItemType(self, itemType):
		self.ClearChildren("itemType")
		typeImages = ["hot.tga","new.tga","offer.tga"]
		if itemType == 0:
			return
		itemType-=1
		if itemType >= len(typeImages):
			return
		typeImage = ui.ExpandedImageBox()
		typeImage.SetParent(self)
		typeImage.LoadImage(IMG_DIR+typeImages[itemType])
		typeImage.SetPosition(0,0)
		typeImage.Show()
		self.childrenImages["typeImage"] = typeImage

	def OnRender(self, parent):
		listboxHeight = parent.GetHeight()
		(pgx,pgy) = parent.GetGlobalPosition()
		for key, textline in self.childrenTextLine.items():
			(igx,igy) = textline.GetGlobalPosition()
			if igy < pgy:
				textline.Hide()
			elif igy > (pgy+listboxHeight-25):
				textline.Hide()
			else:
				textline.Show()
		for key, image in self.childrenImages.items():
			(jgx,jgy) = image.GetGlobalPosition()
			imageHeight = image.GetHeight()
			if jgy < pgy:
				image.SetRenderingRect(0,ui.calculateRect(imageHeight-abs(jgy-pgy),imageHeight),0,0)
			elif jgy+imageHeight > (pgy+listboxHeight-8):
				calculate = (pgy+listboxHeight-8) - (jgy+imageHeight)
				if calculate == 0:
					return
				image.SetRenderingRect(0.0,0.0,0.0,ui.calculateRect(imageHeight-abs(calculate),imageHeight))
			else:
				image.SetRenderingRect(0,0,0,0)

class ItemWindow(ui.Window):
	def __del__(self):
		ui.Window.__del__(self)
	def __init__(self, parent):
		ui.Window.__init__(self)
		self.children=[]
		self.Destroy()
		self.parent=proxy(parent)
		self.SetSize(750,122)
	def OnUpdate(self):
		for children in self.children:
			children.OnUpdate()
	def Destroy(self):
		for children in self.children:
			children.Destroy()
			children=None
		self.children=[]
		self.parent = None
	def AppendWindow(self, window):
		self.children.append(window)
		self.OnRender()
	def OnRender(self):
		for children in self.children:
			children.OnRender(self.parent)
class CategoryItem(ui.ExpandedImageBox):
	def __del__(self):
		ui.ExpandedImageBox.__del__(self)
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)
		self.Destroy()
		self.categoryIndex=-1
		self.LoadImage(Img("category_no_selected.tga"))
	def Destroy(self):
		self.parent=None
		self.categoryIndex=0
		self.categoryText=None
	def SetData(self, categoryIndex, categoryName, categoryListBox):
		self.categoryIndex=categoryIndex
		self.parent=proxy(categoryListBox)
		categoryText = MultiTextLine()
		categoryText.SetParent(self)
		categoryText.SetPosition(self.GetWidth()//2,11)
		categoryText.SetTextRange(15)
		categoryText.SetTextType("horizontal#center")
		categoryText.SetFontName("Tahoma:16")
		categoryText.SetText(categoryName)
		categoryText.AddFlag("not_pick")
		for line in categoryText.children:
			line.AddFlag("not_pick")
		categoryText.Show()
		self.categoryText = categoryText
	def OnRender(self):
		parent = self.parent
		if parent == None:
			return
		listboxHeight = parent.GetHeight()
		(pgx,pgy) = parent.GetGlobalPosition()
		(igx,igy) = self.categoryText.GetGlobalPosition()
		if igy < pgy:
			self.categoryText.Hide()
		elif igy > (pgy+listboxHeight-25):
			self.categoryText.Hide()
		else:
			self.categoryText.Show()
		(jgx,jgy) = self.GetGlobalPosition()
		imageHeight = self.GetHeight()
		if jgy < pgy:
			self.SetRenderingRect(0,ui.calculateRect(imageHeight-abs(jgy-pgy),imageHeight),0,0)
		elif jgy+imageHeight > (pgy+listboxHeight-4):
			calculate = (pgy+listboxHeight-4) - (jgy+imageHeight)
			if calculate == 0:
				return
			self.SetRenderingRect(0.0,0.0,0.0,ui.calculateRect(imageHeight-abs(calculate),imageHeight))
		else:
			self.SetRenderingRect(0,0,0,0)
class ScrollBar(ui.Window):
	SCROLLBAR_WIDTH = 13
	SCROLLBAR_MIDDLE_HEIGHT = 1
	SCROLLBAR_BUTTON_WIDTH = 17
	SCROLLBAR_BUTTON_HEIGHT = 17
	SCROLL_BTN_XDIST = 2
	SCROLL_BTN_YDIST = 2
	class MiddleBar(ui.DragButton):
		def __init__(self):
			ui.DragButton.__init__(self)
			self.AddFlag("movable")
			self.SetWindowName("scrollbar_middlebar")
		def MakeImage(self):
			top = ui.ExpandedImageBox()
			top.SetParent(self)
			top.LoadImage(IMG_DIR+"scroll_top.tga")
			top.AddFlag("not_pick")
			top.Show()
			bottom = ui.ExpandedImageBox()
			bottom.SetParent(self)
			bottom.LoadImage(IMG_DIR+"scroll_bottom.tga")
			bottom.AddFlag("not_pick")
			bottom.Show()
			middle = ui.ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage(IMG_DIR+"scroll_mid.tga")
			middle.AddFlag("not_pick")
			middle.Show()
			self.top = top
			self.bottom = bottom
			self.middle = middle
		def SetSize(self, height):
			minHeight = self.top.GetHeight() + self.bottom.GetHeight() + self.middle.GetHeight()
			height = max(minHeight, height)
			ui.DragButton.SetSize(self, 10, height)
			scale = (height - minHeight) // 2 
			extraScale = 0
			if (height - minHeight) % 2 == 1:
				extraScale = 1
			self.middle.SetPosition(0, self.top.GetHeight() + scale)
			self.bottom.SetPosition(0, height - self.bottom.GetHeight())

	def __init__(self):
		ui.Window.__init__(self)

		self.pageSize = 1
		self.curPos = 0.0
		self.eventScroll = None
		self.eventArgs = None
		self.lockFlag = False

		self.CreateScrollBar()
		self.SetScrollBarSize(0)

		self.scrollStep = 0.03
		self.SetWindowName("NONAME_ScrollBar")

	def __del__(self):
		ui.Window.__del__(self)

	def CreateScrollBar(self):
		topImage = ui.ExpandedImageBox()
		topImage.SetParent(self)
		topImage.AddFlag("not_pick")
		topImage.LoadImage(IMG_DIR+"scrollbar_top.tga")
		topImage.Show()
		bottomImage = ui.ExpandedImageBox()
		bottomImage.SetParent(self)
		bottomImage.AddFlag("not_pick")
		bottomImage.LoadImage(IMG_DIR+"scrollbar_bottom.tga")
		bottomImage.Show()
		middleImage = ui.ExpandedImageBox()
		middleImage.SetParent(self)
		middleImage.AddFlag("not_pick")
		middleImage.SetPosition(0, topImage.GetHeight())
		middleImage.LoadImage(IMG_DIR+"scrollbar_mid.tga")
		middleImage.Show()
		self.topImage = topImage
		self.bottomImage = bottomImage
		self.middleImage = middleImage

		middleBar = self.MiddleBar()
		middleBar.SetParent(self)
		middleBar.SetMoveEvent(ui.__mem_func__(self.OnMove))
		middleBar.Show()
		middleBar.MakeImage()
		middleBar.SetSize(0) # set min height
		self.middleBar = middleBar
	def Destroy(self):
		self.eventScroll = None
		self.eventArgs = None
	def SetScrollEvent(self, event, *args):
		self.eventScroll = event
		self.eventArgs = args
	def SetMiddleBarSize(self, pageScale):
		self.middleBar.SetSize(int(pageScale * float(self.GetHeight() - self.SCROLL_BTN_YDIST*2)))
		realHeight = self.GetHeight() - self.SCROLL_BTN_YDIST*2 - self.middleBar.GetHeight()
		self.pageSize = realHeight
	def SetScrollBarSize(self, height):
		self.SetSize(self.SCROLLBAR_WIDTH, height)
		self.pageSize = height - self.SCROLL_BTN_YDIST*2 - self.middleBar.GetHeight()
		middleImageScale = float((height - self.SCROLL_BTN_YDIST*2) - self.middleImage.GetHeight()) / float(self.middleImage.GetHeight())
		self.middleImage.SetRenderingRect(0, 0, 0, middleImageScale)
		self.bottomImage.SetPosition(0, height - self.bottomImage.GetHeight())
		self.middleBar.SetRestrictMovementArea(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST, self.middleBar.GetWidth(), height - self.SCROLL_BTN_YDIST * 2)
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST)
	def SetScrollStep(self, step):
		self.scrollStep = step
	def GetScrollStep(self):
		return self.scrollStep
	def GetPos(self):
		return self.curPos
	def OnUp(self):
		self.SetPos(self.curPos-self.scrollStep)
	def OnDown(self):
		self.SetPos(self.curPos+self.scrollStep)
	def SetPos(self, pos, moveEvent = True):
		pos = max(0.0, pos)
		pos = min(1.0, pos)
		newPos = float(self.pageSize) * pos
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, int(newPos) + self.SCROLL_BTN_YDIST)
		if moveEvent == True:
			self.OnMove()
	def OnMove(self):
		if self.lockFlag:
			return
		if 0 == self.pageSize:
			return
		(xLocal, yLocal) = self.middleBar.GetLocalPosition()
		self.curPos = float(yLocal - self.SCROLL_BTN_YDIST) / float(self.pageSize)
		if self.eventScroll:
			self.eventScroll(*self.eventArgs)
	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
		newPos = float(yMouseLocalPosition) / float(self.GetHeight())
		self.SetPos(newPos)
	def LockScroll(self):
		self.lockFlag = True
	def UnlockScroll(self):
		self.lockFlag = False
#class ScrollBar(ui.Window):
#	SCROLLBAR_WIDTH = 12
#	MIDDLE_BAR_POS = 5
#	MIDDLE_BAR_UPPER_PLACE = 4
#	MIDDLE_BAR_DOWNER_PLACE = 4
#	MIDDLE_BAR_PER_HEIGHT = 27
#	TEMP_SPACE = MIDDLE_BAR_UPPER_PLACE + MIDDLE_BAR_DOWNER_PLACE
#	class MiddleBar(ui.DragButton):
#		MIDDLE_BAR_PER_HEIGHT = 27
#		MIDDLE_BAR_WIDTH = 6
#		def __init__(self):
#			ui.DragButton.__init__(self)
#			self.AddFlag("movable")
#		def MakeImage(self):
#			top = ui.ImageBox()
#			top.SetParent(self)
#			top.LoadImage(IMG_DIR+"scroll_top.tga")
#			top.SetPosition(0, 0)
#			top.AddFlag("not_pick")
#			top.Show()
#			bottom = ui.ImageBox()
#			bottom.SetParent(self)
#			bottom.LoadImage(IMG_DIR+"scroll_bottom.tga")
#			bottom.AddFlag("not_pick")
#			bottom.Show()
#			middle = ui.ExpandedImageBox()
#			middle.SetParent(self)
#			middle.LoadImage(IMG_DIR+"scroll_mid.tga")
#			middle.SetPosition(0, self.MIDDLE_BAR_PER_HEIGHT)
#			middle.AddFlag("not_pick")
#			middle.Show()
#			self.top = top
#			self.bottom = bottom
#			self.middle = middle
#		def SetSize(self, height):
#			height = max(self.MIDDLE_BAR_PER_HEIGHT * 3, height)
#			ui.DragButton.SetSize(self, 10, height)
#			self.bottom.SetPosition(0, height-self.MIDDLE_BAR_PER_HEIGHT)
#			height -= self.MIDDLE_BAR_PER_HEIGHT*3
#			self.middle.SetRenderingRect(0, 0, 0, float(height)/float(self.MIDDLE_BAR_PER_HEIGHT))
#	def __init__(self):
#		ui.Window.__init__(self)
#		self.pageSize = 1
#		self.curPos = 0.0
#		self.eventScroll = lambda *arg: None
#		self.lockFlag = FALSE
#		self.scrollStep = 0.20
#		self.CreateScrollBar()
#	def __del__(self):
#		ui.Window.__del__(self)
#	def CreateScrollBar(self):
#		barSlot = ui.Bar3D()
#		barSlot.SetParent(self)
#		barSlot.AddFlag("not_pick")
#		barSlot.Show()
#		middleBar = self.MiddleBar()
#		middleBar.SetParent(self)
#		middleBar.SetMoveEvent(ui.__mem_func__(self.OnMove))
#		middleBar.Show()
#		middleBar.MakeImage()
#		middleBar.SetSize(60)
#		self.middleBar = middleBar
#		self.barSlot = barSlot
#		self.SCROLLBAR_MIDDLE_HEIGHT = self.middleBar.GetHeight()
#	def Destroy(self):
#		self.middleBar = None
#		self.eventScroll = lambda *arg: None
#	def SetScrollEvent(self, event):
#		self.eventScroll = event
#	def SetMiddleBarSize(self, pageScale):
#		realHeight = self.GetHeight()
#		self.SCROLLBAR_MIDDLE_HEIGHT = int(pageScale * float(realHeight))
#		self.middleBar.SetSize(self.SCROLLBAR_MIDDLE_HEIGHT)
#		self.pageSize = self.GetHeight() - self.SCROLLBAR_MIDDLE_HEIGHT - (self.TEMP_SPACE)
#	def SetScrollBarSize(self, height):
#		self.pageSize = height - self.SCROLLBAR_MIDDLE_HEIGHT - (self.TEMP_SPACE)
#		self.SetSize(self.SCROLLBAR_WIDTH, height)
#		self.middleBar.SetRestrictMovementArea(self.MIDDLE_BAR_POS, self.MIDDLE_BAR_UPPER_PLACE, self.MIDDLE_BAR_POS+2, height - self.TEMP_SPACE)
#		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, 0)
#		self.UpdateBarSlot()
#	def UpdateBarSlot(self):
#		self.barSlot.SetPosition(0, 2)
#		self.barSlot.SetSize(self.GetWidth() - 2, self.GetHeight() - 2)
#	def GetPos(self):
#		return self.curPos
#	def SetPos(self, pos):
#		pos = max(0.0, pos)
#		pos = min(1.0, pos)
#		newPos = float(self.pageSize) * pos
#		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, int(newPos) + self.MIDDLE_BAR_UPPER_PLACE)
#		self.OnMove()
#	def SetScrollStep(self, step):
#		self.scrollStep = step
#	def GetScrollStep(self):
#		return self.scrollStep
#	def OnUp(self):
#		self.SetPos(self.curPos-self.scrollStep)
#	def OnDown(self):
#		self.SetPos(self.curPos+self.scrollStep)
#	def OnMove(self):
#		if self.lockFlag:
#			return
#		if 0 == self.pageSize:
#			return
#		(xLocal, yLocal) = self.middleBar.GetLocalPosition()
#		self.curPos = float(yLocal - self.MIDDLE_BAR_UPPER_PLACE) / float(self.pageSize)
#		self.eventScroll()
#	def OnMouseLeftButtonDown(self):
#		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
#		pickedPos = yMouseLocalPosition - self.SCROLLBAR_MIDDLE_HEIGHT/2
#		newPos = float(pickedPos) / float(self.pageSize)
#		self.SetPos(newPos)
#	def LockScroll(self):
#		self.lockFlag = TRUE
#	def UnlockScroll(self):
#		self.lockFlag = FALSE
def NumberToMoneyFormat(n):
	if n <= 0 :
		return "0"
	return "%s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))
class MultiTextLine(ui.Window):
	def __del__(self):
		ui.Window.__del__(self)
	def Destroy(self):
		self.children = []
		self.rangeText = 0
	def __init__(self):
		ui.Window.__init__(self)
		self.children = []
		self.rangeText = 15
		self.textType = ""
		self.fontName = ""
		self.outline = False
		self.rgb = (0,0,0)
	def SetFontColor(self, r, g, b):
		self.rgb = (r, g, b)
		for text in self.children:
			if self.rgb[0] != 0:
				text.SetFontColor(self.rgb[0],self.rgb[1],self.rgb[2])
	def SetOutline(self, flag):
		self.outline = flag
		for text in self.children:
			if self.outline:
				text.SetOutline()
	def SetTextType(self, textType):
		self.textType = textType
		for text in self.children:
			self.AddTextType(self.textType.split("#"),text)
	def SetFontName(self, fontName):
		self.fontName = fontName
		for text in self.children:
			text.SetFontName(fontName)
	def GetTextSize(self, index = 0):
		if len(self.children) == 0:
			return (0,0)
		elif index >= len(self.children):
			return (0,0)
		return self.children[index].GetTextSize()

	def SetTextRange(self, range):
		self.rangeText = range
		yPosition = 0
		for text in self.children:
			text.SetPosition(0,yPosition)
			yPosition+=self.rangeText
	def AddTextType(self, typeArg, text):
		if len(typeArg) > 1:
			if typeArg[0] == "vertical":
				if typeArg[1] == "top":
					text.SetVerticalAlignTop()
				elif typeArg[1] == "bottom":
					text.SetVerticalAlignBottom()
				elif typeArg[1] == "center":
					text.SetVerticalAlignCenter()
			elif typeArg[0] == "horizontal":
				if typeArg[1] == "left":
					text.SetHorizontalAlignLeft()
				elif typeArg[1] == "right":
					text.SetHorizontalAlignRight()
				elif typeArg[1] == "center":
					text.SetHorizontalAlignCenter()
	def SetText(self, cmd):
		if len(self.children) > 1:
			self.children=[]
		multi_arg = cmd.split("\n")
		yPosition = 0
		for text in multi_arg:
			childText = ui.TextLine()
			childText.SetParent(self)
			childText.SetPosition(0,yPosition)
			if self.rgb[0] != 0:
				childText.SetFontColor(self.rgb[0],self.rgb[1],self.rgb[2])
			if self.textType != "":
				self.AddTextType(self.textType.split("#"),childText)
			if self.fontName != "":
				childText.SetFontName(self.fontName)
			if self.outline:
				childText.SetOutline()
			childText.SetText(str(text))
			childText.Show()
			self.children.append(childText)
			yPosition+=self.rangeText
class ListBox(ui.Window):
	def __init__(self, isHorizontal = False):
		ui.Window.__init__(self)
		self.viewItemCount=10
		self.basePos=0
		self.itemHeight=16
		self.itemStep=20
		self.itemList=[]
		self.itemWidth=100
		self.scrollBar=None
		self.isHorizontal= isHorizontal
	def __del__(self):
		ui.Window.__del__(self)
	def __GetItemCount(self):
		return len(self.itemList)
	def SetItemStep(self, itemStep):
		self.itemStep=itemStep
	def SetItemSize(self, itemWidth, itemHeight):
		self.itemWidth=itemWidth
		self.itemHeight=itemHeight
	def SetViewItemCount(self, viewItemCount):
		self.viewItemCount=viewItemCount
	def RemoveAllItems(self):
		for item in self.itemList:
			item.Destroy()
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
	def GetItems(self):
		return self.itemList
	def RemoveItem(self, delItem):
		self.itemList.remove(delItem)
	def AppendItem(self, newItem):
		self.itemList.append(newItem)
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar=scrollBar
		uiwheel.Attach(scrollBar, scrollBar)	# the wheel over the bar itself scrolls the offers too
	def OnMouseWheel(self, nLen):
		if self.scrollBar:
			if self.scrollBar.IsShow():
				if nLen > 0:
					self.scrollBar.OnUp()
				else:
					self.scrollBar.OnDown()
				return True
		return False
	def __OnScroll(self):
		self.SetBasePos(int(self.scrollBar.GetPos()*self.__GetScrollLen()))
	def __GetScrollLen(self):
		if self.__GetItemCount() == 0:
			return 0
		(lx,ly) = self.itemList[len(self.itemList)-1].exPos
		return ly
	def Render(self,basePos):
		for item in self.itemList:
			(ex,ey) = item.exPos
			if self.isHorizontal:
				item.SetPosition(ex-(basePos),ey)
			else:
				item.SetPosition(ex,ey-(basePos))
			item.OnRender()
	def SetBasePos(self, basePos):
		if self.basePos == basePos:
			return
		self.Render(basePos)
		self.basePos=basePos

class CategoryListBox(ListBox):
	"""Sidebar scrolls only its overflow; wheel events never escape to products."""
	def Render(self, basePos):
		# Reposition/visibility only on a scroll or layout event, never in OnUpdate.
		for item in self.itemList:
			x, y = item.exPos
			y -= basePos
			item.SetPosition(x, y)
			if y >= self.GetHeight() or y + item.GetHeight() <= 0:
				item.Hide()
			else:
				item.Show()
				item.OnRender()

	def GetScrollRange(self):
		return max(0, len(self.itemList) * self.itemHeight - self.GetHeight())

	def SetScrollBar(self, scrollBar):
		self.scrollBar = scrollBar
		scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		uiwheel.Bind(scrollBar, self)
		self.RefreshScroll()

	def RefreshScroll(self):
		bar = self.scrollBar
		if bar is None:
			return
		overflow = self.GetScrollRange()
		content = max(self.GetHeight(), len(self.itemList) * self.itemHeight)
		bar.SetMiddleBarSize(float(self.GetHeight()) / max(1, content))
		bar.SetScrollStep(min(1.0, float(self.itemHeight) / max(1, overflow)))
		bar.Show() if overflow else bar.Hide()
		self.SetBasePos(min(self.basePos, overflow))
		bar.SetPos(float(min(self.basePos, overflow)) / max(1, overflow))
		self.Render(self.basePos)

	def OnScroll(self):
		self.SetBasePos(int(round(self.scrollBar.GetPos() * self.GetScrollRange())))

	def SetBasePos(self, basePos):
		ListBox.SetBasePos(self, max(0, min(int(basePos), self.GetScrollRange())))

	def OnMouseWheel(self, delta):
		if not delta:
			return False
		uiwheel.Scroll(self.scrollBar, delta)
		return True


def Simulation():
	itemList = []
	randomItems = [149,50300,51501,51502,11299,469,70048,70005,70043,30197]
	itemID = 0
	topSellingIndex = 0

	for categoryIndex in range(5):
		for x in range(3):
			forList = []
			for j in range(app.GetRandom(1,6)):
				discount = 0
				if app.GetRandom(0,15) == 3:
					discount = app.GetRandom(0,99)
				time = 0
				if app.GetRandom(0,15) == 0:
					time = app.GetGlobalTimeStamp()+app.GetRandom(1,60*60*24*7)
				addedTime = 0
				if app.GetRandom(0,2) == 0:
					addedTime = app.GetGlobalTimeStamp()-app.GetRandom(1,60*60*24*7)
				forList.append([itemID,randomItems[app.GetRandom(0,len(randomItems)-1)],app.GetRandom(10,100),discount,time,app.GetRandom(0,100),addedTime])
				itemID+=1
			itemList.append(forList)
		itemshopData[categoryIndex] = itemList
		itemList=[]
		for j in range(50):
			playerLog.append(["06/12/2021 21:59",app.GetGlobalTimeStamp()-app.GetRandom(1,200),"testaccount","127.0.0.1",randomItems[app.GetRandom(0,len(randomItems)-1)],app.GetRandom(1,200),app.GetRandom(1,200)])
#Simulation()
