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
MAX_1_PAGE_COUNT = 8

SPACER_X = 5
SPACER_Y = 4

saveItemDialog=None

def SortMySellLog(e):
	return e[4]

class ListBoxItem(ui.Window):
	class NewItem(ui.Window):
		def __init__(self, parent, vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement=None):
			ui.Window.__init__(self)
			self.background = None
			self.index = vnum
			self.count = count
			self.price = price
			self.buyer = buyer
			self.when = when
			
			self.metinSlot = []
			self.metinSlot = metinSlot

			self.applyRandom = []
			self.applyRandom = applyRandom

			self.attrSlot = []
			self.attrSlot = attrSlot
			
			self.transmutation = transmutation
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
				
			self.background.SetPosition(0, 0)
			self.background.Show()

			self.NameItem = ui.TextLine()
			self.NameItem.SetParent(self)
			if ItemCount > 1:
				self.NameItem.SetText("x%d " % (ItemCount) + item.GetItemName())
			else:
				self.NameItem.SetText(item.GetItemName())
#__ ITEM NAME
			self.NameItem.SetPosition(43+3+2, -5)
			self.NameItem.SetWindowHorizontalAlignLeft()
			self.NameItem.SetWindowVerticalAlignCenter()
			self.NameItem.SetPackedFontColor(0xffFFB96D)
			self.NameItem.Show()
#__ PRICE
			self.PriceItem = ui.TextLine()
			self.PriceItem.SetParent(self)
			self.PriceItem.SetPosition(43+205, -5)
			self.PriceItem.SetWindowVerticalAlignCenter()
			self.PriceItem.SetText(localeInfo.NumberToMoneyString(price) + " Yang")
			self.PriceItem.Show()
#__ BUYER
			self.BuyerItem = ui.TextLine()
			self.BuyerItem.SetParent(self)
			self.BuyerItem.SetPosition(335+14, -5)
			self.BuyerItem.SetWindowVerticalAlignCenter()
			self.BuyerItem.SetText(buyer)
			self.BuyerItem.Show()

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
			self.ImageItemVnum.SetPosition(5, 0)
			self.ImageItemVnum.SetEvent(ui.__mem_func__(self.OnMouseInIcon), "MOUSE_OVER_IN", ItemVnum)
			self.ImageItemVnum.SetEvent(ui.__mem_func__(self.OnMouseOutIcon), "MOUSE_OVER_OUT")
			self.ImageItemVnum.Show()

			self.SetSize(self.background.GetWidth(), self.background.GetHeight())

		def OnRender(self):
			xList, yList = self.parent.GetGlobalPosition()
			widthList, heightList = self.parent.GetWidth(), self.parent.GetHeight()	

			images = [self.background, self.ImageItemVnum]
			for img in images:
				if img:
					img.SetClipRect(xList, yList, xList + widthList, yList + heightList)

			textList = [self.NameItem, self.DateItem, self.PriceItem, self.BuyerItem]
			for text in textList:
				if text:
					xText, yText = text.GetGlobalPosition()

					if yText < yList or yText + text.GetTextSize()[1] > yList + heightList:
						text.Hide()
					else:
						text.Show()

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
					interface.tooltipItem.AddItemData(vnum,self.metinSlot,self.attrSlot, apply_random_list = self.applyRandom, refine_element=refine_element)
					interface.tooltipItem.ShowToolTip()

		def OnMouseOutIcon(self, type):
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				if interface.tooltipItem:
					interface.tooltipItem.HideToolTip()

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
		scrollBar.SetScrollStep(0.2)
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

	def AppendItem(self, vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement=None):
		item = self.NewItem(self, vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement)
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
		totalHeight = self.GetTotalItemHeight() - self.GetHeight()

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

class SellLogWindow(ui.DragonBoardWithTitleBar):
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
	
		self.SetTitleName(uiScriptLocale.OFFLINE_SHOP_HISTORY)
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
			net.SendChatPacket("/sell_history 1")
			self.isLoad = True

		self.SetCenterPosition()
		self.SetTop()
		# self.RefreshList()
		self.Show()

	def AddSaveItem(self, vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement=None):
		if self.listboxSaveItem != None:

			self.saveIDList.append([vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement])
			
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
		self.saveIDList.sort(reverse=True, key=SortMySellLog)
		
		self.loadingImage.Hide()

		for x in self.saveIDList:
			vnum = x[0]
			count = x[1]
			price = x[2]
			buyer = x[3]
			when = x[4]
			metinSlot = x[5]
			attrSlot = x[6]
			applyRandom = x[7]
			transmutation = x[8]
			refineElement = x[9] if len(x) > 9 else None

			self.listboxSaveItem.AppendItem(vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement)

	def CalculatePageCount(self):
		pass

#__ TITLE BAR

	def _LoadWindow(self):
	
		self.historyBackground = ui.ImageBox()
		self.historyBackground.SetParent(self)
		self.historyBackground.LoadImage(IMG_FOLDER + "sell_history_bg.png")
		self.historyBackground.SetPosition(10, 27+5-2)
		self.historyBackground.Show()
	
		titleImage = ui.ImageBox()
		titleImage.SetParent(self)
		titleImage.LoadImage(IMG_FOLDER + "title_bar.png")
		titleImage.SetPosition(15-1-2+SPACER_X,30+3-3+SPACER_Y)
		titleImage.Show()
		self.children.append(titleImage)

		# titleImage = ui.BoxedBoard()
		# titleImage.SetParent(self)
		# titleImage.SetPosition(15,30+3)
		# titleImage.SetSize(492,18)
		# titleImage.Show()
		# self.children.append(titleImage)

		
		itemText = ui.TextLine()
		itemText.SetParent(titleImage)
		itemText.SetPosition(41-38+4,5)
		itemText.SetText(localeInfo.OFFLINE_SHOP_HISTORY_ITEM)
		itemText.Show()
		self.children.append(itemText)
		
		priceText = ui.TextLine()
		priceText.SetParent(titleImage)
		priceText.SetPosition(160+86,5)
		priceText.SetText(localeInfo.OFFLINE_SHOP_HISTORY_PRICE)
		priceText.SetTextColor(0xfff4ead5)
		priceText.Show()
		self.children.append(priceText)
		
		buyerText = ui.TextLine()
		buyerText.SetParent(titleImage)
		buyerText.SetPosition(240+107,5)
		buyerText.SetText(localeInfo.OFFLINE_SHOP_HISTORY_BUYER)
		buyerText.SetTextColor(0xfff4ead5)
		buyerText.Show()
		self.children.append(buyerText)
		
		
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
		self.listboxSaveItem.SetPosition(13+SPACER_X,30+5+titleImage.GetHeight()+SPACER_Y)
		self.listboxSaveItem.SetSize(492,(8*30) + 40)
		self.listboxSaveItem.AddFlag("attach")
		self.listboxSaveItem.SetScrollBar(self.CategoryScrollBar)
		self.listboxSaveItem.Show()
		
		(x, y) = self.listboxSaveItem.GetLocalPosition()
		
		backBtn = ui.Button()
		backBtn.SetParent(self)
		backBtn.SetUpVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub")
		backBtn.SetOverVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_02.sub")
		backBtn.SetDownVisual("d:/ymir work/ui/public/public_intro_btn/prev_btn_03.sub")
		backBtn.SetPosition(x+self.listboxSaveItem.GetWidth()//2-20-10-7+SPACER_X,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5)
		backBtn.SAFE_SetEvent(self.PrevPage)
		backBtn.Show()
		self.children.append(backBtn)
		
		pageBar = ui.SlotBar()
		pageBar.SetParent(self)
		pageBar.SetPosition(-20+x+self.listboxSaveItem.GetWidth()//2+20-7+SPACER_X,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5)
		pageBar.SetSize(backBtn.GetWidth(),backBtn.GetHeight())
		pageBar.Show()
		self.children.append(pageBar)
		#
		self.pageText = ui.TextLine()
		self.pageText.SetParent(pageBar)
		self.pageText.SetPosition(5,0)
		self.pageText.SetText("1")
		self.pageText.Show()
		
		nextBtn = ui.Button()
		nextBtn.SetParent(self)
		nextBtn.SetUpVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub")
		nextBtn.SetOverVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_02.sub")
		nextBtn.SetDownVisual("d:/ymir work/ui/public/public_intro_btn/next_btn_03.sub")
		nextBtn.SetPosition(x+self.listboxSaveItem.GetWidth()//2+20+10-7+SPACER_X,y+self.listboxSaveItem.GetHeight()+SPACER_Y+8.5)
		nextBtn.SAFE_SetEvent(self.NextPage)
		nextBtn.Show()
		self.children.append(nextBtn)

		
		self.loadingImage = ui.ExpandedImageBox()
		self.loadingImage.SetParent(self.listboxSaveItem)
		self.loadingImage.LoadImage(IMG_FOLDER+"load_.tga")
		self.loadingImage.SetPosition(self.listboxSaveItem.GetWidth()//2-15+SPACER_X,self.listboxSaveItem.GetHeight()//2-65+SPACER_Y)
		self.loadingImage.Show()
		
		(x, y) = self.listboxSaveItem.GetLocalPosition()

#__ WINDOW SIZE
		self.SetSize(535+9,389+6)

	def NextPage(self):
		if self.currentPage < 10:
			self.ClearItems()
			self.lastAction = 1
			self.currentPage += 1
			self.pageText.SetText(str(self.currentPage))
			net.SendChatPacket("/sell_history " + str(self.currentPage))

	def PrevPage(self):
		if self.currentPage > 1:
			self.ClearItems()
			self.lastAction = -1
			self.currentPage -= 1
			self.pageText.SetText(str(self.currentPage))
			net.SendChatPacket("/sell_history " + str(self.currentPage))
			
	def FirstPage(self):
		self.ClearItems()
		self.currentPage = 1
		self.pageText.SetText(str(self.currentPage))
		net.SendChatPacket("/sell_history " + str(self.currentPage))
			
	def RevertPage(self):
		self.FirstPage()
		
	def UpdateNewItems(self):
		if self.listboxSaveItem and len(self.saveIDList) > 0:
			self.RefreshList()
		if self.IsShow():
			#self.FirstPage()
			chat.AppendChat(1, uiScriptLocale.OOFFLINE_SHOP_HISTORY_REFRESH)
		else:
			#self.FirstPage()
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
		if self.isLoad==False:
			if self.loadingImage != None:
				self.loadingImage.SetRotation(self.loadingImageRotation)
				self.loadingImageRotation+=5

