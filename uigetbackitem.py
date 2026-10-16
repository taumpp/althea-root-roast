import ui
import uiScriptLocale
import localeInfo
import player
import item
import net
import osfInfo
import app
import math
import uiCommon
import chat
from datetime import datetime

from _weakref import proxy

IMG_FOLDER = "d:/ymir work/ui/game/sell_history/"
IMG_FOLDER2 = "d:/ymir work/ui/save_item/"
IMG_DIR = "d:/ymir work/ui/game/exchange_log/"
MAX_1_PAGE_COUNT = 20

SPACER_X = 5
SPACER_Y = 4

saveItemDialog=None

def SortMySellLog(e):
	return e[4]

class ListBoxItem(ui.Window):
	class NewItem(ui.Window):
		def __init__(self, parent, time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refineElement=None):
			ui.Window.__init__(self)
			self.background = None
			
			self.item_id = item_id
			self.index = vnum
			self.count = count
			
			self.getBackQuestionDialog = None
			
			price = yang
			self.fragments = fragments

			when = time
			
			self.metinSlot = []
			self.metinSlot = metinSlot
			
			self.attrSlot = []
			self.attrSlot = attrSlot

			self.applyRandom = []
			self.applyRandom = applyRandom

			self.transmutation = transmutation
			self.soulbind = soulbind
			self.refineElement = refineElement
			
			self.saveID = vnum
			self.ResetInit()
			
			ItemVnum = vnum
			ItemCount = count
		
			if ItemVnum == 0:
				return

			item.SelectItem(ItemVnum)
			_, size = item.GetItemSize()

			self.background = ui.ExpandedImageBoxSaveItem()
			self.background.SetParent(self)
			if size == 1:
				self.background.LoadImage(IMG_FOLDER + "32.png")
			elif size == 2:
				self.background.LoadImage(IMG_FOLDER + "64.png")
			elif size == 3:
				self.background.LoadImage(IMG_FOLDER + "96.png")
				
			self.background.SetPosition(0+32, 0)
			self.background.Show()

			self.NameItem = ui.TextLine()
			self.NameItem.SetParent(self)
			if ItemCount > 1:
				self.NameItem.SetText("x%d " % (ItemCount) + item.GetItemName())
			else:
				self.NameItem.SetText(item.GetItemName())
				
#__ GET_BACK_BUTTON
			# self.getBackBtn = ui.Button()
			# self.getBackBtn.SetParent(self)
			# self.getBackBtn.SetUpVisual("d:/ymir work/ui/save_item/"+"get_back_01.png")
			# self.getBackBtn.SetOverVisual("d:/ymir work/ui/save_item/"+"get_back_02.png")
			# self.getBackBtn.SetDownVisual("d:/ymir work/ui/save_item/"+"get_back_03.png")
			# self.getBackBtn.SetPosition(4, 7)
			# self.getBackBtn.SetToolTipText(localeInfo.DESTROYED_ITEMS_GET_BACK)
			# self.getBackBtn.SetEvent(lambda arg=item_id: self.ClickGetBack(arg))
			# self.getBackBtn.Show()


			self.getBackBtn = ui.ExpandedImageBoxSaveItem()
			self.getBackBtn.SetParent(self)
			self.getBackBtn.LoadImage("d:/ymir work/ui/save_item/change_name_norm.tga")
			self.getBackBtn.SetPosition(-5, 2)
			self.getBackBtn.SetWindowHorizontalAlignLeft()
			self.getBackBtn.SetWindowVerticalAlignCenter()
			self.getBackBtn.SetEvent(ui.__mem_func__(self.ClickGetBack), "MOUSE_LEFT_BUTTON_DOWN", item_id, item.GetItemName(), yang, fragments)
			self.getBackBtn.SetEvent(ui.__mem_func__(self.OnOverInGetBack), "MOUSE_OVER_IN")
			self.getBackBtn.SetEvent(ui.__mem_func__(self.OnOverOutGetBack), "MOUSE_OVER_OUT")
			self.getBackBtn.Show()


#__ ITEM NAME
			self.NameItem.SetPosition(43+3+2+32, -5)
			self.NameItem.SetWindowHorizontalAlignLeft()
			self.NameItem.SetWindowVerticalAlignCenter()
			self.NameItem.SetPackedFontColor(0xffFFB96D)
			self.NameItem.Show()
#__ PRICE
			self.PriceItem = ui.TextLine()
			self.PriceItem.SetParent(self)
			self.PriceItem.SetPosition(43+205, -5)
			self.PriceItem.SetWindowVerticalAlignCenter()
			
			if price > 0:
				self.PriceItem.SetText(localeInfo.NumberToMoneyString(price+25000000) + " Yang")
			elif fragments > 0:
				self.PriceItem.SetText(localeInfo.NumberToMoneyString(fragments+50) + " Fragments")
			else:
				self.PriceItem.SetText(localeInfo.NumberToMoneyString(25000000) + " Yang")
			self.PriceItem.Show()

#__ DATE

			dt_object = str(datetime.fromtimestamp(int(when)))
			timeText = "None"
			timeSplit = dt_object.split(" ")
			if len(timeSplit) == 2:
				splitDate1 = timeSplit[0].split("-")
				if len(splitDate1) == 3:
					timeText= splitDate1[2]+"/"+splitDate1[1]
					timeText+= " "
				splitDate2 = timeSplit[1].split(":")
				if len(splitDate2) == 3:
					timeText += splitDate2[0]+":"+splitDate2[1]

			self.DateItem = ui.TextLine()
			self.DateItem.SetParent(self)
			self.DateItem.SetPosition(424+8, -5)
			self.DateItem.SetWindowVerticalAlignCenter()
			self.DateItem.SetText(timeText)
			self.DateItem.Show()
#__ ITEM ICON
			self.ImageItemVnum = ui.ExpandedImageBoxSaveItem()
			self.ImageItemVnum.SetParent(self)
			self.ImageItemVnum.LoadImage(item.GetIconImageFileName())
			self.ImageItemVnum.SetWindowVerticalAlignCenter()
			self.ImageItemVnum.SetPosition(5+32, 0)
			self.ImageItemVnum.SetEvent(ui.__mem_func__(self.OnMouseInIcon), "MOUSE_OVER_IN", ItemVnum)
			self.ImageItemVnum.SetEvent(ui.__mem_func__(self.OnMouseOutIcon), "MOUSE_OVER_OUT")
			self.ImageItemVnum.Show()

			self.SetSize(self.background.GetWidth(), self.background.GetHeight())

		def OnRender(self):
			xList, yList = self.parent.GetGlobalPosition()
			widthList, heightList = self.parent.GetWidth(), self.parent.GetHeight()	

			images = [self.background, self.ImageItemVnum, self.getBackBtn]
			for img in images:
				if img:
					img.SetClipRect(xList-5, yList, xList + widthList, yList + heightList)

			textList = [self.NameItem, self.DateItem, self.PriceItem]
			for text in textList:
				if text:
					xText, yText = text.GetGlobalPosition()

					if yText < yList or yText + text.GetTextSize()[1] > yList + heightList:
						text.Hide()
					else:
						text.Show()
						
			#buttons
			

		def __del__(self):
			ui.Window.__del__(self)
			self.ResetInit()

		def ResetInit(self):
			self.xBase = 0
			self.yBase = 0
			self.overInEventFunc = None
			self.overOutEventFunc = None
			self.clickEvent = None
			self.background = None

		def SetParent(self, parent):
			ui.Window.SetParent(self, parent)
			self.parent = proxy(parent)

		def SetBasePosition(self, x, y):
			self.xBase = x
			self.yBase = y
			
		def GetBasePosition(self):
			return (self.xBase, self.yBase)
			
		def SetOverInEvent(self, event):
			self.overInEventFunc = event
			
		def SetOverOutEvent(self, event):
			self.overOutEventFunc = event
			
		def SetClickEvent(self, event):
			self.clickEvent = event

		def OnMouseInIcon(self, type, vnum):
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				if interface.tooltipItem:
					interface.tooltipItem.ClearToolTip()
					refine_element = self.refineElement if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
					interface.tooltipItem.AddItemData(vnum, self.metinSlot, self.attrSlot, apply_random_list=self.applyRandom, refine_element=refine_element, rarity_key=(7, 0, 0, 0, self.item_id))
					interface.tooltipItem.ShowToolTip()

		def OnMouseOutIcon(self, type):
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				if interface.tooltipItem:
					interface.tooltipItem.HideToolTip()
					
		def AnswerGetBackItem(self, yes):
			
			if yes:
				net.SendChatPacket("/restore_saved_item %d" % self.getBackQuestionDialog.item_id)
		
			if self.getBackQuestionDialog:
				self.getBackQuestionDialog.Close()
				self.getBackQuestionDialog = None
			

				
					
		def ClickGetBack(self, empty, item_id, item_name, yang, fragments):
			self.getBackBtn.LoadImage("d:/ymir work/ui/save_item/change_name_down.tga")
			if self.getBackQuestionDialog:
				self.getBackQuestionDialog.Close()
				self.getBackQuestionDialog = None
			
			getBackQuestionDialog = uiCommon.QuestionDialog()
			
			if yang > 0:
				needPay = localeInfo.NumberToMoneyString(yang+25000000) + " Yang"
				question = localeInfo.DESTROYED_ITEMS_CONFIRM % needPay
			elif fragments > 0:
				needPay = localeInfo.NumberToMoneyString(fragments+50) + " Fragments"
				question = localeInfo.DESTROYED_ITEMS_CONFIRM % needPay
			else:
				needPay = localeInfo.NumberToMoneyString(yang+25000000) + " Yang"
				question = localeInfo.DESTROYED_ITEMS_CONFIRM % needPay
			
			getBackQuestionDialog.SetText(question)
			getBackQuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerGetBackItem(arg))
			getBackQuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerGetBackItem(arg))
			getBackQuestionDialog.Open()
			getBackQuestionDialog.item_id = item_id
				
			self.getBackQuestionDialog = getBackQuestionDialog
			
			
		def OnOverInGetBack(self):
			self.getBackBtn.LoadImage("d:/ymir work/ui/save_item/change_name_hover.tga")
			
		def OnOverOutGetBack(self):
			self.getBackBtn.LoadImage("d:/ymir work/ui/save_item/change_name_norm.tga")

	def __init__(self):
		ui.Window.__init__(self)
		self.ResetInit()

	def __del__(self):
		ui.Window.__del__(self)
		self.ResetInit()
		
	def Destroy(self):
		self.ResetInit()
		
	def ResetInit(self):
		self.SetFuncDown = None
		self.itemList = []
		self.scrollBar = None

		self.itemTooltip = None
		self.selectEvent = None

	def SetParent(self, parent):
		ui.Window.SetParent(self, parent)
		
		self.parent = proxy(parent)
		self.SetPosition(10, 10)
		self.SetSize(parent.GetWidth() - 10, parent.GetHeight() - 10)
		
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		scrollBar.SetScrollStep(0.01)
		self.scrollBar=scrollBar

	def SetEventSelect(self, event):
		self.selectEvent = event
		
	def __OnScroll(self):
		self.AdjustItemPositions(True)

	def GetTotalItemHeight(self):
		totalHeight = 0

		if self.itemList:
			for itemH in self.itemList:
				totalHeight += itemH.GetHeight() + 2
			
		return totalHeight
	
	def GetItemCount(self):
		return len(self.itemList)

	def AppendItem(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refineElement=None):
		item = self.NewItem(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refineElement)
		item.SetParent(self)

		if len(self.itemList) == 0:
			item.SetBasePosition(0, 0)
		else:
			x, y = self.itemList[-1].GetLocalPosition()
			y += 2
			item.SetBasePosition(0, y + self.itemList[-1].GetHeight())

		item.SetOverInEvent(ui.__mem_func__(self.OverInItem))
		item.SetOverOutEvent(ui.__mem_func__(self.OverOutItem))
		item.SetClickEvent(ui.__mem_func__(self.ClickSaveItem))
			
		item.Show()
		self.itemList.append(item)
		
		self.AdjustScrollBar()
		self.AdjustItemPositions()
		
		self.scrollBar.Show()
		
		step = float(1.0 / len(self.itemList))
		self.scrollBar.SetScrollStep(step)

	def ClickSaveItem(self, index):
		global saveItemDialog
		if saveItemDialog == None:
			saveItemDialog = uiCommon.QuestionDialog()
		(itemVnum, itemCount, itemDate) = player.GetSaveItem(index)
		
		if itemVnum == 0 or itemCount == 0:
			return
		item.SelectItem(itemVnum)
		text = localeInfo.SAVE_ITEM_QUESTION
		if itemCount > 1:
			text += " (%s %dx)"%(item.GetItemName(),itemCount)
		else:
			text +=" (%s)"%(item.GetItemName())
		saveItemDialog.SetText(text)
		saveItemDialog.SetAcceptText(localeInfo.UI_ACCEPT)
		saveItemDialog.SetCancelText(localeInfo.UI_DENY)
		saveItemDialog.SetAcceptEvent(lambda arg=1: self.__AnswerSaveItem(arg))
		saveItemDialog.SetCancelEvent(lambda arg=0: self.__AnswerSaveItem(arg))
		saveItemDialog.saveIndex = index
		saveItemDialog.Open()

	def __AnswerSaveItem(self, p):
		global saveItemDialog
		if saveItemDialog != None:
			saveItemDialog.Close()
			if p:
				net.SendChatPacket("/save_item remove %d" % saveItemDialog.saveIndex)
				# Simulation
				# self.RemoveItem(saveItemDialog.saveIndex)

	def RemoveItem(self, index):
		if len(self.itemList) == 0:
			return
		
		reList = []
		for item in self.itemList:
			if item.index == index:
				item.ResetInit()
				item.Hide()
				del item
				continue
			
			reList.append(item.index)
		
		self.Clear()
		
		for item in reList:
			self.AppendItem(item)
			
		reList = []

	def OverInItem(self, ItemVnum):
		if self.itemTooltip and ItemVnum != 0:
			self.itemTooltip.SetItemToolTip(ItemVnum)
			
	def OverOutItem(self):
		if self.itemTooltip:
			self.itemTooltip.HideToolTip()
			self.itemTooltip.ClearToolTip()

	def AdjustScrollBar(self):
		totalHeight = float(self.GetTotalItemHeight())
		if totalHeight:
			scrollBarHeight = min(float(self.GetHeight() - 10) / totalHeight, 1.0)
		else:
			scrollBarHeight = 1.0
			
		self.scrollBar.SetMiddleBarSize(scrollBarHeight)
		
	def ResetScrollbar(self):
		self.scrollBar.SetPos(0)

	def AdjustItemPositions(self, scrolling = False, startIndex = -1):		
		scrollPos = self.scrollBar.GetPos()
		totalHeight = max(0, self.GetTotalItemHeight() - self.GetHeight())

		idx = 0
		if startIndex >= 0:
			idx = startIndex
		
		for item in self.itemList[idx:]:
			xB, yB = item.GetBasePosition()
			
			if startIndex >= 0:
				yB -= ITEM_HEIGHT + 2
			
			if scrolling:
				setPos = yB - int(scrollPos * totalHeight)
				item.SetPosition(xB, setPos)
			else:
				item.SetPosition(xB, yB)
				
			item.SetBasePosition(xB, yB)

	def OnMouseWheel(self, nLen):
		if nLen > 0:
			self.scrollBar.OnUp()
			return True
			
		elif nLen < 0:
			self.scrollBar.OnDown()
			return True
			
		return False

	def Clear(self):
		if len(self.itemList) == 0:
			return

		for item in self.itemList:
			item.ResetInit()
			item.Hide()
			del item
		
		self.OverOutItem()
		self.itemList = []
	
	def RemoveAllItems(self):
		self.Clear()

## LISTBOX_ITEM

class SaveWindow(ui.DragonBoardWithTitleBar):
	def __del__(self):
		ui.DragonBoardWithTitleBar.__del__(self)

	def Destroy(self):
		self.children = []
		self.saveIDList = []
		self.perPage = 0
		self.currentPage = 1
		self.lastAction = 0
		self.loadingImageRotation = 0
		self.isLoad = False
		self.listboxSaveItem=None
		self.loadingImage = None
		if self.listboxSaveItem != None:
			self.listboxSaveItem.RemoveAllItems()
			self.listboxSaveItem=None
		ui.DragonBoardWithTitleBar.Destroy(self)

	def __init__(self):
		ui.DragonBoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("attach")
		self.AddFlag("float")
		
		if app.ENABLE_ANIMATED_WINDOW:
			self.AddFlag("animate")
	
		self.SetTitleName(localeInfo.DESTROYED_ITEMS_TITLE)
		self.children = []
		self.saveIDList = []
		self.perPage = MAX_1_PAGE_COUNT
		self.currentPage = 1
		self.lastAction = 0
		self.pageCount=1
		self.isLoad = False
		self.loadingImage = None
		self.loadingImageRotation = 0
		self.listboxSaveItem=None
		
		self.curPage = 0
		self.maxPage = 0
		self.firstPageBtn = None
		self.lastPageBtn = None
		self.nextPageBtn = None
		self.backPageBtn = None
		
		self.canSendRequest = True
		
		self._LoadWindow()

	def Simulation(self):
		timestamp = 1545730073
		dt_object = datetime.fromtimestamp(timestamp)
	
		import random
		for j in range(5):
			
			n = random.randint(10,89)
			self.AddSaveItem(n)

	def Open(self):
		if self.isLoad == False:
			net.SendChatPacket("/load_saved_items 0")
			self.isLoad = True
			# return
	
		self.SetCenterPosition()
		self.SetTop()
		# self.RefreshList()
		self.Show()

	def AddSaveItem(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refineElement=None):
		if self.listboxSaveItem != None:

			self.saveIDList.append([time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refineElement])
			
			self.loadingImage.Hide()
			self.RefreshList()

	def OnPressEscapeKey(self):
		self.Hide()
		return True
		
	def Close(self):
		self.Hide()

	def ClearItems(self):
		if self.isLoad==False:
			self.isLoad=True
		self.saveIDList = []
		

	def RefreshList(self):
		self.listboxSaveItem.RemoveAllItems()
		# self.saveIDList.sort(reverse=True, key=SortMySellLog)
		
		self.loadingImage.Hide()

		for x in self.saveIDList:
			time = x[0]
			item_id = x[1]
			vnum = x[2]
			count = x[3]
			yang = x[4]
			fragments = x[5]
			metinSlot = x[6]
			attrSlot = x[7]
			applyRandom = x[8]
			transmutation = x[9]
			soulbind = x[10]
			refineElement = x[11] if len(x) > 11 else None

			self.listboxSaveItem.AppendItem(time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refineElement)

	def CalculatePageCount(self):
		pass
		
	def SetPage(self, curPage, maxPage):
		disableAll = False
		if curPage == -1:
			disableAll = True
			curPage = 0
			
		self.curPage = curPage
		self.maxPage = maxPage
		
		self.pageText.SetText(str(curPage+1))
		
		self.SetUpPageButtons()
		
		if self.lastPageBtn:
			self.lastPageBtn.SetText(str(maxPage))
		
		for x in range(200):
			self.CategoryScrollBar.OnUp()
			
		self.canSendRequest = True
		
		if disableAll:
			self.firstPageBtn.Disable()
			self.lastPageBtn.Disable()
			self.nextPageBtn.Disable()
			self.backPageBtn.Disable()
		
	def SetUpPageButtons(self):
		if self.nextPageBtn and self.backPageBtn:
			
			if self.curPage == 0:
				self.backPageBtn.Disable()
				self.firstPageBtn.Down()
				self.firstPageBtn.Disable()
			else:
				self.backPageBtn.Enable()
				self.firstPageBtn.Enable()
				self.firstPageBtn.SetUp()
				
			if self.curPage >= self.maxPage-1:
				self.nextPageBtn.Disable()
				self.lastPageBtn.Down()
				self.lastPageBtn.Disable()
			else:
				self.nextPageBtn.Enable()
				self.lastPageBtn.Enable()
				self.lastPageBtn.SetUp()

#__ TITLE BAR

	def _LoadWindow(self):
	
		self.historyBackground = ui.ImageBox()
		self.historyBackground.SetParent(self)
		self.historyBackground.LoadImage(IMG_FOLDER2 + "bg.png")
		self.historyBackground.SetPosition(10, 27+5-2)
		self.historyBackground.Show()
	
		titleImage = ui.ImageBox()
		titleImage.SetParent(self)
		titleImage.SetPosition(15-1-2+SPACER_X,30+3-3+SPACER_Y)
		titleImage.Show()
		self.children.append(titleImage)
		
		itemText = ui.TextLine()
		itemText.SetParent(titleImage)
		itemText.SetPosition(41-38+4,5)
		itemText.SetText(localeInfo.DESTROYED_ITEMS_TITLE)
		itemText.Show()
		self.children.append(itemText)
		
		priceText = ui.TextLine()
		priceText.SetParent(titleImage)
		priceText.SetPosition(160+86,5)
		priceText.SetText(localeInfo.OFFLINE_SHOP_HISTORY_PRICE)
		priceText.SetTextColor(0xfff4ead5)
		priceText.Show()
		self.children.append(priceText)
		
		
		dateText = ui.TextLine()
		dateText.SetParent(titleImage)
		dateText.SetPosition(340+90,5)
		dateText.SetText(localeInfo.OFFLINE_SHOP_HISTORY_DATE)
		dateText.Show()
		self.children.append(dateText)

		wallThinBoard = ui.ThinBoard()
		wallThinBoard.SetParent(self)
		wallThinBoard.SetPosition(13+SPACER_X,30+5+titleImage.GetHeight()+SPACER_Y)
		wallThinBoard.SetSize(titleImage.GetWidth(),8*30)
		wallThinBoard.AddFlag("not_pick")
		wallThinBoard.Hide()
		self.children.append(wallThinBoard)
		
#__ SCROLLBAR
		
		scrollPath = "d:/ymir work/ui/public/scrollbar/"
		self.CategoryScrollBar = ui.ScrollBarTemplate()
		self.CategoryScrollBar.SetParent(self)
		self.CategoryScrollBar.SetPosition(428+81-2+SPACER_X, 55+7+SPACER_Y)
		self.CategoryScrollBar.SetBarImage(scrollPath + "scrollbar_bg_big.png")
		self.CategoryScrollBar.SetMiddleImage(scrollPath + "middle_big.png")	
		self.CategoryScrollBar.SetScrollBarSize(277)
		self.CategoryScrollBar.Show()		

		self.listboxSaveItem = ListBoxItem()
		self.listboxSaveItem.SetParent(self)
		self.listboxSaveItem.SetPosition(13+SPACER_X,30+5+titleImage.GetHeight()+SPACER_Y+27)
		self.listboxSaveItem.SetSize(492,(8*30) + 40)
		self.listboxSaveItem.AddFlag("attach")
		self.listboxSaveItem.SetScrollBar(self.CategoryScrollBar)
		self.listboxSaveItem.Show()
		
		(x, y) = self.listboxSaveItem.GetLocalPosition()
		
		backBtn = ui.Button()
		backBtn.SetParent(self)
		backBtn.SetUpVisual(IMG_DIR + "back_page_0.tga")
		backBtn.SetOverVisual(IMG_DIR + "back_page_1.tga")
		backBtn.SetDownVisual(IMG_DIR + "back_page_1.tga")
		backBtn.SetPosition(x+self.listboxSaveItem.GetWidth()//2-20-10-7+SPACER_X,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5+5)
		backBtn.SAFE_SetEvent(self.PrevPage)
		backBtn.Show()
		self.children.append(backBtn)
		
		self.backPageBtn = backBtn
		
		# self.firstPageBtn = None
		# self.lastPageBtn = None
		# self.nextPageBtn = None
		# self.backPageBtn = None
		
		firstBtn = ui.Button()
		firstBtn.SetParent(self)
		firstBtn.SetUpVisual(IMG_DIR + "first_page_0.tga")
		firstBtn.SetOverVisual(IMG_DIR + "first_page_1.tga")
		firstBtn.SetDownVisual(IMG_DIR + "first_page_1.tga")
		firstBtn.SetText("1")
		firstBtn.SetPosition((x+self.listboxSaveItem.GetWidth()//2-20-10-7+SPACER_X) - 40,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5 - 4+5)
		firstBtn.SAFE_SetEvent(self.FirstPage)
		firstBtn.Show()
		self.children.append(firstBtn)
		self.firstPageBtn = firstBtn
		
		pageBar = ui.ImageBox()
		pageBar.SetParent(self)
		pageBar.LoadImage(IMG_DIR + "page_box.tga")
		pageBar.SetPosition(-20+x+self.listboxSaveItem.GetWidth()//2+20-7+SPACER_X-6,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5-4.5)
		pageBar.Show()
		self.children.append(pageBar)
		#
		self.pageText = ui.TextLine()
		self.pageText.SetParent(pageBar)
		self.pageText.SetPosition(10,5)
		self.pageText.SetText("1")
		self.pageText.Show()
		
		nextBtn = ui.Button()
		nextBtn.SetParent(self)
		nextBtn.SetUpVisual(IMG_DIR + "next_page_0.tga")
		nextBtn.SetOverVisual(IMG_DIR + "next_page_1.tga")
		nextBtn.SetDownVisual(IMG_DIR + "next_page_1.tga")
		nextBtn.SetPosition(x+self.listboxSaveItem.GetWidth()//2+20+10-7+SPACER_X,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5+5)
		nextBtn.SAFE_SetEvent(self.NextPage)
		nextBtn.Show()
		self.children.append(nextBtn)
		
		self.nextPageBtn = nextBtn
		
		
		lastBtn = ui.Button()
		lastBtn.SetParent(self)
		lastBtn.SetUpVisual(IMG_DIR + "last_page_0.tga")
		lastBtn.SetOverVisual(IMG_DIR + "last_page_0.tga")
		lastBtn.SetDownVisual(IMG_DIR + "last_page_0.tga")
		lastBtn.SetPosition((x+self.listboxSaveItem.GetWidth()//2+20+10-7+SPACER_X) + 40,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5 - 4+5)
		lastBtn.SetText("-")
		lastBtn.SAFE_SetEvent(self.LastPage)
		lastBtn.Show()
		self.children.append(lastBtn)
		self.lastPageBtn = lastBtn

		
		self.loadingImage = ui.ExpandedImageBox()
		self.loadingImage.SetParent(self.listboxSaveItem)
		self.loadingImage.LoadImage(IMG_FOLDER+"load_.tga")
		self.loadingImage.SetPosition(self.listboxSaveItem.GetWidth()//2-15+SPACER_X,self.listboxSaveItem.GetHeight()//2-65+SPACER_Y)
		self.loadingImage.Show()
		
		(x, y) = self.listboxSaveItem.GetLocalPosition()

#__ WINDOW SIZE
		self.SetSize(535+9,389+6)

	def NextPage(self):
		if self.canSendRequest == False:
			return
			
		if self.nextPageBtn:
			self.nextPageBtn.Disable()
	
		self.loadingImage.Show()
		self.ClearItems()
		self.lastAction = 1
		# self.currentPage += 1
		# self.pageText.SetText(str(self.currentPage))
		net.SendChatPacket("/load_saved_items " + str(self.curPage+1))
		self.canSendRequest = False

	def PrevPage(self):
		if self.canSendRequest == False:
			return
	
		if self.backPageBtn:
			self.backPageBtn.Disable()
	
		self.loadingImage.Show()
		self.ClearItems()
		self.lastAction = -1
		# self.currentPage -= 1
		# self.pageText.SetText(str(self.currentPage))
		net.SendChatPacket("/load_saved_items " + str(self.curPage-1))
		self.canSendRequest = False
			
	def FirstPage(self):	
		if self.canSendRequest == False:
			return
			
		if self.firstPageBtn:
			self.firstPageBtn.Disable()
			
		self.loadingImage.Show()
		self.ClearItems()

		net.SendChatPacket("/load_saved_items 0")
		self.canSendRequest = False
		
	def LastPage(self):	
		if self.canSendRequest == False:
			return
			
		if self.lastPageBtn:
			self.lastPageBtn.Disable()
			
		self.loadingImage.Show()
		self.ClearItems()

		net.SendChatPacket("/load_saved_items " + str(self.maxPage-1))
		self.canSendRequest = False
		
	# def ClickGetBack(self, item_id):
		# import chat
		# chat.AppendChat(chat.CHAT_TYPE_INFO, "get back %d" % (item_id))
		
	# def OnOverInGetBack(self):
		# self.getBackBtn.LoadImage("d:/ymir work/ui/save_item/get_back_02.png")
		
	# def OnOverOutGetBack(self):
		# self.getBackBtn.LoadImage("d:/ymir work/ui/save_item/get_back_01.png")
			
	def RevertPage(self):
		self.FirstPage()
		
	def UpdateNewItems(self):
		if self.IsShow():
			self.FirstPage()
			chat.AppendChat(1, uiScriptLocale.OOFFLINE_SHOP_HISTORY_REFRESH)
		else:
			self.FirstPage()
			chat.AppendChat(1, uiScriptLocale.OFFLINE_SHOP_HISTORY_SOLD_ITEM)

	def OnMouseWheel(self, nLen):
		if nLen > 0:
			self.CategoryScrollBar.OnUp()
			return True
			
		elif nLen < 0:
			self.CategoryScrollBar.OnDown()
			return True
			
		return False

	def OnUpdate(self):
		# if self.isLoad==False:
		if self.loadingImage != None and self.loadingImage.IsShow():
			self.loadingImage.SetRotation(self.loadingImageRotation)
			self.loadingImageRotation+=5

