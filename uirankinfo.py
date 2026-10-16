import ui
import app
import item
import net
import grp 
import wndMgr
import localeInfo
import uiScriptLocale
import player
import mouseModule
import chat
import ui
import item
from _weakref import proxy

RANK_BY_LEVEL = 0
RANK_BY_STONE = 1
RANK_BY_MAX_DMG_STONE = 2
RANK_BY_DUNGEON_COMPLETE = 3
RANK_BY_BOSS = 4
RANK_BY_MAX_DMG_BOSS = 5
RANK_BY_MONSTER = 6
RANK_BY_ITEM_IMPROVED = 7
RANK_BY_PLAYING_TIME = 8
RANK_BY_MISSION_BOOK_COMPLETE = 9
RANK_BY_BOX_OPENED = 10
RANK_BY_BONUS_CHANGED = 11
RANK_BY_FISH_CAUGHT = 12
RANK_BY_EXTRACTION = 13
RANK_BY_RESET_EXTRACTION = 14
RANK_BY_RESET_FISH_CAUGHT = 15
RANK_BY_RESET_MISSION_BOOK = 16

def IS_RESET_CATEGORY(category):
	resetCategories = [
		# EDIT_RANKING_CATEGORIES_HERE
		# these categories will be reset every x days:
		RANK_BY_RESET_EXTRACTION,
		RANK_BY_RESET_FISH_CAUGHT,
		RANK_BY_RESET_MISSION_BOOK,
	]
	
	if category in resetCategories:
		return True
		
	return False

Y_SPACER = 4

TEXT_CATEGORY = [uiScriptLocale.PLAYER_RANKING_LEVEL,  
				uiScriptLocale.PLAYER_RANKING_STONE,
				uiScriptLocale.PLAYER_RANKING_DMG_STONE,
				uiScriptLocale.PLAYER_RANKING_DUNGEON,	
				uiScriptLocale.PLAYER_RANKING_BOSS, 
				uiScriptLocale.PLAYER_RANKING_DMG_BOSS,
				uiScriptLocale.PLAYER_RANKING_MONSTER,
				uiScriptLocale.PLAYER_RANKING_REFINE,
				uiScriptLocale.PLAYER_RANKING_PLAYTIME,
				uiScriptLocale.PLAYER_RANKING_MISSION_BOOK,
				uiScriptLocale.PLAYER_RANKING_CHEST,
				uiScriptLocale.PLAYER_RANKING_ENCHANT,
				uiScriptLocale.PLAYER_RANKING_FISHING,
				uiScriptLocale.PLAYER_RANKING_MINING,
				uiScriptLocale.PLAYER_RANKING_MINING,
				uiScriptLocale.PLAYER_RANKING_FISHING,
				uiScriptLocale.PLAYER_RANKING_MISSION_BOOK,
]

RANKING_PATH = "d:/ymir work/ui/game/player_ranking/"

MAX_CATEGORY_NUM = len(TEXT_CATEGORY)

global_t = (0,24,60)
def CalculateTimeLeft(iTime):
	if iTime <= 0:
		return "00:00:00"
		
	A, B = divmod(iTime, global_t[2])
	C, A = divmod(A, global_t[2])
	return "%02d:%02d:%02d" % (C, A, B)	

class ListBox(ui.Window):
	class NewItem(ui.Window):
		def __init__(self, index, func):
			ui.Window.__init__(self)
			self.Index = index
			self.select = False
			self.Reinitialize()

			self.DoChange = ui.__mem_func__(func)

			self.background = ui.ExpandedImageBox()
			self.background.SetParent(self)
			self.background.AddFlag("not_pick")
			self.background.SetPosition(0, -1)
			
			if IS_RESET_CATEGORY(self.Index):
				self.background.LoadImage(RANKING_PATH + "challenge_btn_1.png")
			else:
				self.background.LoadImage(RANKING_PATH + "ranking_btn_1.png")
			
			self.background.Show()
			
			self.SetSize(self.background.GetWidth(), self.background.GetHeight())		

			self.Icon = ui.ExpandedImageBox()
			self.Icon.SetParent(self)
			self.Icon.AddFlag("not_pick")
			self.Icon.SetPosition(1, 0)
			self.Icon.LoadImage(RANKING_PATH + "category/rank_%d.png" % (index))
			self.Icon.Show()
		
			self.textCat = ui.TextLine()
			self.textCat.SetParent(self.background)
			self.textCat.SetPosition(56, 9)
			text = TEXT_CATEGORY[index]
			text1 = text.find(' ')
			if text1 != -1:
				self.textCat.SetText(text[:text1 + 1])
			else:
				self.textCat.SetText(text)
			self.textCat.Show()
			
			self.text2Cat = None
			if text1 != -1:
				self.text2Cat = ui.TextLine()
				self.text2Cat.SetParent(self.background)
				self.text2Cat.SetPosition(56, 19)
				self.text2Cat.SetText(text[text1 + 1:])
				self.text2Cat.Show()

		def SelectImage(self):
			if IS_RESET_CATEGORY(self.Index):
				self.background.LoadImage(RANKING_PATH + "challenge_btn_2.png")
			else:
				self.background.LoadImage(RANKING_PATH + "ranking_btn_2.png")
			self.DoChange(self.Index)
			self.select = True

		def OverInImage(self):
			if IS_RESET_CATEGORY(self.Index):
				self.background.LoadImage(RANKING_PATH + "challenge_btn_2.png")
			else:
				self.background.LoadImage(RANKING_PATH + "ranking_btn_2.png")

		def OverOutImage(self):
			if self.select == False:
				if IS_RESET_CATEGORY(self.Index):
					self.background.LoadImage(RANKING_PATH + "challenge_btn_1.png")
				else:
					self.background.LoadImage(RANKING_PATH + "ranking_btn_1.png")
	
		def SetSelect(self):
			self.select = True
			if IS_RESET_CATEGORY(self.Index):
				self.background.LoadImage(RANKING_PATH + "challenge_btn_2.png")
			else:
				self.background.LoadImage(RANKING_PATH + "ranking_btn_2.png")
	
		def OverOutForce(self):
			self.select = False
			if IS_RESET_CATEGORY(self.Index):
				self.background.LoadImage(RANKING_PATH + "challenge_btn_1.png")
			else:
				self.background.LoadImage(RANKING_PATH + "ranking_btn_1.png")
		
		def __del__(self):
			ui.Window.__del__(self)
			self.Reinitialize()
			
		def Reinitialize(self):
			self.selected = False
			self.xBase = 0
			self.yBase = 0

			self.overInEvent = None
			self.overOutEvent = None
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
			self.overInEvent = event
			
		def SetOverOutEvent(self, event):
			self.overOutEvent = event
			
		def SetClickEvent(self, event):
			self.clickEvent = event
			
		def OnMouseOverIn(self):
			if self.overInEvent:
				self.overInEvent()
			
		def OnMouseOverOut(self):
			if self.overOutEvent:
				self.overOutEvent()
				
		def OnMouseLeftButtonDown(self):	
			if self.clickEvent:
				self.clickEvent()

		def OnRender(self):		
			xList, yList = self.parent.GetGlobalPosition()
			widthList, heightList = self.parent.GetWidth() + 50, self.parent.GetHeight() + 8
			
			if self.background:
				self.background.SetClipRect(xList, yList, xList + widthList, yList + heightList)

			if self.Icon:
				self.Icon.SetClipRect(xList, yList, xList + widthList, yList + heightList)

			textList = [self.textCat, self.text2Cat]		
			for text in textList:
				if text:
					xText, yText = text.GetGlobalPosition()

					if yText < yList or yText + text.GetTextSize()[1] > yList + heightList:
						text.Hide()
					else:
						text.Show()

	def __init__(self):
		ui.Window.__init__(self)
		self.Reinitialize()

	def __del__(self):
		ui.Window.__del__(self)
		self.Reinitialize()
		
	def Destroy(self):
		self.Reinitialize()
		
	def Reinitialize(self):
		self.itemList = []
		self.scrollBar = None
		self.tooltipItem = None
		
		self.selectEvent = None

	def SetParent(self, parent):
		ui.Window.SetParent(self, parent)
		
		self.SetPosition(5, 5)
		self.SetSize(parent.GetWidth() - 10, parent.GetHeight() - 10)
		
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		scrollBar.SetScrollStep(0.2)
		self.scrollBar = scrollBar

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem
		
	def SetSelectEvent(self, event):
		self.selectEvent = event
		
	def __OnScroll(self):
		self.AdjustItemPositions(True)
			
	def GetTotalItemHeight(self):
		totalHeight = 0
		
		if self.itemList:
			for itemH in self.itemList:
				totalHeight += itemH.GetHeight() + 2
			
		return totalHeight
			
	def OnMouseWheel(self, nLen):
		if self.scrollBar:
			self.scrollBar.OnMouseWheel(nLen)
			return True
			
		return False
			
	def GetItemCount(self):
		return len(self.itemList)
			
	def OverOutAll(self, y):
		for x in range(len(self.itemList)):
			self.itemList[x].OverOutForce()
			
		self.itemList[y].SetSelect()
			
	def AppendItem(self, ItemVnum, func):
		item = self.NewItem(ItemVnum, func)
		item.SetParent(self)
		
		if len(self.itemList) == 0:
			item.SetBasePosition(0, 0)
		else:
			x, y = self.itemList[-1].GetLocalPosition()
			y += 2
			item.SetBasePosition(0, y + self.itemList[-1].GetHeight())

		item.SetOverInEvent(ui.__mem_func__(item.OverInImage))
		item.SetOverOutEvent(ui.__mem_func__(item.OverOutImage))
		item.SetClickEvent(ui.__mem_func__(item.SelectImage))
			
		item.Show()
		self.itemList.append(item)
		
		self.AdjustScrollBar()
		self.AdjustItemPositions()

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

	def SelectItem(self):
		if self.selectEvent:
			self.selectEvent()

	def Clear(self):
		if len(self.itemList) == 0:
			return
	
		for item in self.itemList:
			item.Reinitialize()
			item.Hide()
			del item

		self.itemList = []

class RankInfo(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.dicInfoRank = {}
		for x in range(MAX_CATEGORY_NUM):
			self.dicInfoRank[x] = {}
		self.Size = {}
		self.bLoaded = False
		self.bCurPage = 0
		self.MyPos = 0
		self.LoadWindow()
		self.bInfoMyPos = None
		self.bInfoMyName = None
		self.bInfoMyValue = None
		self.iNextRequest = 0
		self.iResetTime = 0
		self.iInterval = 0
		self.toolTipItem = None
		self.iRewardVnum = {}
		self.iRewardCount = {}
		
	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		self.bTab = {}
		self.bInfoPos = {}
		self.bInfoName = {}
		self.bInfoValue = {}
		self.dicInfoRank = {}
		for x in range(MAX_CATEGORY_NUM):
			self.dicInfoRank[x] = {}

		self.bInfoMyPos = None
		self.bInfoMyName = None
		self.bInfoMyValue = None
		self.iNextRequest = 0
		self.iResetTime = 0
		self.iInterval = 0
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
		self.toolTipItem = None
		self.iRewardVnum = {}
		self.iRewardCount = {}
	
		self.ListBoxItem.Clear()
	
	def Show(self):
		self.LoadWindow()
		self.SetCenterPosition()
		self.DoChange(self.bCurPage)
		ui.ScriptWindow.Show(self)
		
	def SetItemToolTip(self, itemTooltip):
		self.toolTipItem = itemTooltip

	def __ShowToolTip(self, slotIndex):
		if self.toolTipItem:
			vnum = self.iRewardVnum[slotIndex]
			self.toolTipItem.SetRankingRewardItem(vnum)
		 
	def OverInItem(self, slotIndex):
		self.__ShowToolTip(slotIndex)

	def OverOutItem(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def LoadWindow(self):
		if self.bLoaded == True:
			return
			
		self.bLoaded = True
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "uiscript/rank_info.py")
		except:
			import exception
			exception.Abort("rank_info.LoadWindow.LoadObject")

		try:
			self.titleBar = self.GetChild("TitleBar")
			self.board = self.GetChild("board")
			self.wndTextCount = self.GetChild("wndTextCount")
			self.txtResetTime = self.GetChild("RemainingTime")
			self.resetInfoBoard = self.GetChild("ResetInfoBoard")
			# import dbg
			# dbg.TraceError("resetInfoBoard loaded")
			
			self.rewardItem = self.GetChild("RewardSlot")
			self.rewardItem.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
			self.rewardItem.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		except:
			import exception
			exception.Abort("rank_info.__LoadWindow.BindObject")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))	

		scrollPath = RANKING_PATH + "scrollbar/"
		self.ScrollBar = ui.ScrollBarTemplate()
		self.ScrollBar.SetParent(self)
		self.ScrollBar.SetPosition(195, 48)
		self.ScrollBar.SetBarImage(scrollPath + "scrollbar_bg_big.png")
		self.ScrollBar.SetMiddleImage(scrollPath + "middle_big.png")	
		self.ScrollBar.SetScrollBarSize(341)
		self.ScrollBar.Show()

		self.ListBoxItem = ListBox()
		self.ListBoxItem.SetParent(self)
		self.ListBoxItem.SetScrollBar(self.ScrollBar)
		self.ListBoxItem.SetSize(150, 330)
		self.ListBoxItem.SetPosition(25, 50)
		self.ListBoxItem.Show()		
		
		self.CreateButtonCategory()
		
		self.wndAnimMask = ui.ThinBoardCircle()
		self.wndAnimMask.SetParent(self)
		self.wndAnimMask.SetPosition(235, 94)
		self.wndAnimMask.SetSize(350, 259)
		self.wndAnimMask.Hide()
		
		self.wndAnim = ui.AniImageBox()
		self.wndAnim.SetDelay(2)
		self.wndAnim.SetParent(self)
		self.wndAnim.SetEndFrameEvent(ui.__mem_func__(self.SearchRank))
		self.wndAnim.Hide()

		for i in range(30):
			self.wndAnim.AppendImage("d:/ymir work/ui/game/search_shop/loading_circle/%d.png" % (i))	

	def OnPressEscapeKey(self):
		self.Close()
		return True
		
	def SetRewardItem(self, iPos, vnum, count):
		self.rewardItem.SetItemSlot(iPos, vnum, count)
		self.iRewardVnum[iPos] = vnum
		self.iRewardCount[iPos] = count
		
	def SetResetTime(self, iTime, iInterval):	
		self.iResetTime = iTime
		self.iInterval = iInterval
		
	def OnUpdate(self):
		if self.iResetTime <= 0:
			return

		remainingSeconds = self.iResetTime - app.GetGlobalTimeStamp()
			
		if remainingSeconds < 0:
			self.txtResetTime.SetText(CalculateTimeLeft(0))
			return
			
		if self.IsShow():
			if remainingSeconds > 60*60*24:
				self.txtResetTime.SetText(localeInfo.SecondToDHM(remainingSeconds))
			else:
				self.txtResetTime.SetText(CalculateTimeLeft(remainingSeconds))


	def CreateButtonCategory(self):
		for x in range(MAX_CATEGORY_NUM):
			self.ListBoxItem.AppendItem(x, self.DoChange)

	def DoChange(self, arg):
		self.ListBoxItem.OverOutAll(arg)
		self.bCurPage = arg
	
		self.bTab = {}
		self.bInfoPos = {}
		self.bInfoName = {}
		self.bInfoValue = {}
		
		if IS_RESET_CATEGORY(self.bCurPage):
			self.resetInfoBoard.Show()
		else:
			self.resetInfoBoard.Hide()
		
		if self.iNextRequest < app.GetTime():
			myEmpire = net.GetMainActorEmpire() #im not sure
			self.AppendMyInformation("-", player.GetMainCharacterName(), 0, myEmpire)
			self.SearchRank()
		else:
			self.wndAnim.SetPosition(400, 197)
			self.wndAnim.ResetFrame()
			self.wndAnimMask.Show()
			self.wndAnim.Show()
			myEmpire = net.GetMainActorEmpire() #im not sure
			self.AppendMyInformation("-", player.GetMainCharacterName(), 0, myEmpire)
			
	def SearchRank(self):
		self.wndAnimMask.Hide()
		self.wndAnim.Hide()
		self.dicInfoRank[self.bCurPage] = {}
		net.SendChatPacket("/req_info_rank %d" % (self.bCurPage))
		self.ListBoxItem.OverOutAll(self.bCurPage)

		if self.bCurPage == 0:
			self.wndTextCount.SetText(uiScriptLocale.PLAYER_RANKING_LEVEL_TITLE)
		# elif self.bCurPage == 1:
			# self.wndTextCount.SetText(uiScriptLocale.PLAYER_RANKING_LEVEL_YANG)
		else:
			self.wndTextCount.SetText(uiScriptLocale.PLAYER_RANKING_COUNT)
			
		self.iNextRequest = app.GetTime() + 1.0
	
	def AppendMyInformation(self, pos, name, value, empire): 
		if pos:
			if not self.bInfoMyPos: 
				self.bInfoMyPos = ui.TextLine()
				self.bInfoMyPos.SetParent(self)
				self.bInfoMyPos.SetPosition(245, 360-Y_SPACER)
				self.bInfoMyPos.SetPackedFontColor(0xff99907e)
				self.bInfoMyPos.Show()
			
			self.bInfoMyPos.SetText(str(pos))
			
			if not self.bInfoMyName:
				self.bInfoMyName = ui.TextLine()
				self.bInfoMyName.SetParent(self)
				self.bInfoMyName.SetPosition(15, 360-Y_SPACER)
				self.bInfoMyName.SetWindowHorizontalAlignCenter()	
				self.bInfoMyName.SetHorizontalAlignCenter()
				self.bInfoMyName.SetPackedFontColor(0xff99907e)
				self.bInfoMyName.Show()

			self.bInfoMyName.SetText(name)
		
			if not self.bInfoMyValue:
				self.bInfoMyValue = ui.TextLine()
				self.bInfoMyValue.SetParent(self)
				self.bInfoMyValue.SetPosition(230, 360-Y_SPACER)
				self.bInfoMyValue.SetWindowHorizontalAlignCenter()	
				self.bInfoMyValue.SetHorizontalAlignCenter()
				self.bInfoMyValue.SetPackedFontColor(0xff99907e)
				self.bInfoMyValue.Show()
				
			price = localeInfo.NumberToString(int(value))
			self.bInfoMyValue.SetText(str(price))

	def AppendInfo(self, my_pos, mode, pos, name, value, empire):
		if mode < 0 or mode >= MAX_CATEGORY_NUM:
			return

		if mode != self.bCurPage:
			return

		if my_pos:
			self.AppendMyInformation(pos, name, value, empire)
		else:
			self.dicInfoRank[mode][pos] = {"Name": name, "Value": value}
			self.Refresh(pos)

	def Refresh(self, size):
		self.bTab = {}
		self.bInfoPos = {}
		self.bInfoName = {}
		self.bInfoValue = {}

		y_pos = [101-Y_SPACER, 127-Y_SPACER, 152-Y_SPACER, 178-Y_SPACER, 204-Y_SPACER, 230-Y_SPACER, 255-Y_SPACER, 282-Y_SPACER, 307-Y_SPACER, 335-Y_SPACER]
		colors = ["|cff969265", "|cff7c7a85", "|cFF6f5b54"]

		rankData = self.dicInfoRank.get(self.bCurPage, {})

		for x in range(1, size):
			if x not in rankData:
				continue

			self.bInfoPos[x] = ui.TextLine()
			self.bInfoPos[x].SetParent(self)
			self.bInfoPos[x].SetPosition(245, y_pos[x-1])
			self.bInfoPos[x].SetText(str(x))
			self.bInfoPos[x].SetPackedFontColor(0xff99907e)
			self.bInfoPos[x].Show()
			
			self.bInfoName[x] = ui.TextLine()
			self.bInfoName[x].SetParent(self)
			self.bInfoName[x].SetPosition(15, y_pos[x-1])
			self.bInfoName[x].SetWindowHorizontalAlignCenter()
			self.bInfoName[x].SetHorizontalAlignCenter()
			self.bInfoName[x].SetPackedFontColor(0xff99907e)
			
			if x <= 3:
				self.bInfoName[x].SetText(colors[x-1] + rankData[x]["Name"])
			else:
				self.bInfoName[x].SetText(rankData[x]["Name"])
			
			self.bInfoName[x].Show()
			
			self.bInfoValue[x] = ui.TextLine()
			self.bInfoValue[x].SetParent(self)
			self.bInfoValue[x].SetPosition(230, y_pos[x-1])
			self.bInfoValue[x].SetWindowHorizontalAlignCenter()	
			self.bInfoValue[x].SetHorizontalAlignCenter()
			self.bInfoValue[x].SetPackedFontColor(0xff99907e)
			price = localeInfo.NumberToString(int(rankData[x]["Value"]))
			if x <= 3:
				self.bInfoValue[x].SetText(colors[x-1] + str(price))
			else:
				self.bInfoValue[x].SetText(str(price))
			self.bInfoValue[x].Show()

	def Close(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
		self.Hide()
