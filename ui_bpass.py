import ui
import app
import grp
import net
import chat
import item
from _weakref import proxy
import nonplayer
import wndMgr
import localeInfo
import player
import mouseModule
from datetime import datetime
import osfInfo

PATH_ROOT = "d:/ymir work/ui/game/battle_pass_reworked/"
PATH_ICONS = "d:/ymir work/ui/game/battle_pass_reworked/slice/quest/icons/"
IMG_DIR = "d:/ymir work/ui/game/gameoption/"
OPEN_SHOP_ID = 12

ITEM_VNUM_SKIP_MISSION = 31091

TITLE_TYPES = {
	0 : localeInfo.BP_KILL_PLAYERS,
	1 : localeInfo.BP_KILL_MONSTERS,
	2 : localeInfo.BP_KILL_METINS,
	3 : localeInfo.BP_KILL_BOSSES,
	4 : localeInfo.BP_USE_ITEMS,
	5 : localeInfo.BP_COMPLETE_DUNGEONS,
	6 : localeInfo.BP_WRITE_CHAT,
	7 : localeInfo.BP_REFINE_ALCHEMY,
	8 : localeInfo.BP_COMB_ACCE,
	9 : localeInfo.BP_CATCH_FISH,
	10 : localeInfo.BP_DESTROY_ITEM,
	11 : localeInfo.BP_REWARD_YANG,
	12 : localeInfo.BP_CRAFT_ITEM,
	13 : localeInfo.BP_USE_EMOTICON,
	14 : localeInfo.BP_REFINE_ITEM,
	15 : localeInfo.BP_MINING,
	16 : localeInfo.BP_OPEN_CHEST,
	17 : localeInfo.BP_SPEND_MONEY,
	18 : localeInfo.BP_LEVEL_UP,
	19 : localeInfo.BP_FRY_FISH,
}

def MakeTextLineRightAlign(parent):
	textLine = ui.TextLine()
	textLine.SetParent(parent)
	textLine.SetWindowHorizontalAlignRight()
	textLine.SetWindowVerticalAlignCenter()
	textLine.SetHorizontalAlignRight()
	textLine.SetVerticalAlignCenter()
	textLine.SetPosition(3, 0)
	textLine.Show()
	return textLine

def GetNameByTypeVnum(type, vnum):
	if vnum == 0:
		return localeInfo.BP_ALL

	if type == 1 or type == 2 or type == 3:
		monster_name = localeInfo.BP_MONSTERS
		if vnum:
			monster_name = nonplayer.GetMonsterName(vnum)
		
		return monster_name
	elif type == 4 or type == 10:
		item_name = localeInfo.BP_ITEMS
		if vnum:
			item.SelectItem(vnum)
			item_name = item.GetItemName()
		
		return item_name
		
	return localeInfo.BP_ALL

CURRENT_LEVEL = 0
MAX_BP_LEVEL = 20

class ListBox(ui.Window):
	class NewItem(ui.Window):
		def __init__(self, category, index, title, type, vnum, count, maxCount, expRecieve, func, IsPremium, coolTime, parent):
			ui.Window.__init__(self)
			self.category = category
			self.isPremium = IsPremium
			self.index = index
			self.select = False
			self.expRecieve = expRecieve
			self.QuestionDialog = None
			self.coolTime = coolTime
	
			title = TITLE_TYPES[type]
			self.title = title
			self.type = type
			self.vnum = vnum
			self.count = count
			self.maxCount = maxCount
	
			self.Reinitialize()

			if func:
				self.OnSelectitemIndex = ui.__mem_func__(func)

			self.bg = ui.ExpandedImageBox()
			self.bg.SetParent(self)
			self.bg.AddFlag("not_pick")
			self.bg.SetPosition(0, 0)
			if not self.isPremium:
				self.bg.image = PATH_ROOT + "slice/quest/" + "quest_blue.png"
			else:
				self.bg.image = PATH_ROOT + "slice/quest/" + "quest_gold.png"
				
			self.bg.LoadImage(self.bg.image)
			self.bg.Show()
			
			self.SetSize(self.bg.GetWidth(), self.bg.GetHeight())		

			self.wndIcon = ui.ExpandedImageBox()
			self.wndIcon.SetParent(self)
			self.wndIcon.AddFlag("not_pick")
			self.wndIcon.SetPosition(6, 2)
			self.wndIcon.LoadImage(PATH_ICONS + "%d.png" % (type))
			self.wndIcon.Show()
		
			self.wndTextLine = ui.TextLine()
			self.wndTextLine.SetParent(self.bg)
			self.wndTextLine.SetPosition(55, 5)
			self.wndTextLine.SetText(title + " (%d)" % (self.maxCount - self.count))
			self.wndTextLine.SetPackedFontColor(0xFFC6B38D)
			self.wndTextLine.Show()
	
			self.wndTextLine2 = ui.TextLine()
			self.wndTextLine2.SetParent(self.bg)
			self.wndTextLine2.SetPosition(55, 24)
			self.wndTextLine2.SetText(localeInfo.BP_TARGET % (GetNameByTypeVnum(type, vnum)))
			self.wndTextLine2.Show()

			self.wndTextLine3 = ui.TextLine()
			self.wndTextLine3.SetParent(self.bg)
			self.wndTextLine3.SetPosition(250, 5)
			self.wndTextLine3.SetText("EXP %d" % (expRecieve))
			self.wndTextLine3.SetPackedFontColor(0xFF9F8C76)
			self.wndTextLine3.Show()

			self.wndTextLine4 = ui.TextLine()
			self.wndTextLine4.SetParent(self.bg)
			self.wndTextLine4.SetPosition(250, 5 + 17)
			if self.isPremium:
				self.wndTextLine4.SetText(localeInfo.BATTLE_PASS_PREMIUM)
			else:
				self.wndTextLine4.SetText(localeInfo.BATTLE_PASS_FREE)
			self.wndTextLine4.SetPackedFontColor(0xFF9F8C76)
			self.wndTextLine4.Show()

			self.bgGauge = ui.Window()
			self.bgGauge.SetParent(self)
			self.bgGauge.SetPosition(1, 41)
			
			if self.isPremium:
				self.bgGaugeFull = ui.MakeExpandedImageBox(self.bgGauge, PATH_ROOT+"slice/quest/" + "gauge_gold.png", 0, 2, "not_pick")
			else:
				self.bgGaugeFull = ui.MakeExpandedImageBox(self.bgGauge, PATH_ROOT+"slice/quest/" + "gauge_blue.png", 0, 2, "not_pick")

			self.bgGauge.SetSize(self.bgGaugeFull.GetWidth(), self.bgGaugeFull.GetHeight())
			self.bgGauge.Show()
			
			self.wndSkipMission = ui.ExpandedImageBoxButton()
			self.wndSkipMission.SetParent(self)
			self.wndSkipMission.SetPosition(350, 7)
			self.wndSkipMission.SetUpVisual(PATH_ROOT+"slice/quest/btn_0.png")
			self.wndSkipMission.SetOverVisual(PATH_ROOT+"slice/quest/btn_1.png")
			self.wndSkipMission.SetDownVisual(PATH_ROOT+"slice/quest/btn_2.png")
			self.wndSkipMission.SetEvent(ui.__mem_func__(self.OnSkipMission), "MOUSE_CLICK")
			self.wndSkipMission.SetText(localeInfo.BATTLE_PASS_SKIP)
			self.wndSkipMission.Show()

			self.wndTextLine5 = ui.TextLine()
			self.wndTextLine5.SetParent(self.bg)
			self.wndTextLine5.SetPosition(310, 14)
			self.wndTextLine5.SetText("")
			self.wndTextLine5.SetPackedFontColor(0xFF9F8C76)
			self.wndTextLine5.Show()

			self.UpdateGauge(count, maxCount, self.coolTime)
		
		def OnSkipMission(self):
			if self.count == self.maxCount or self.QuestionDialog:
				return
			
			item.SelectItem(ITEM_VNUM_SKIP_MISSION)
				
			import uiCommon
			QuestionDialog = uiCommon.QuestionDialog()
			QuestionDialog.SetText(localeInfo.BATTLE_PASS_SKIP_QUESTION % item.GetItemName())
			QuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerQuestionSkipMission(arg))
			QuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerQuestionSkipMission(arg))
			QuestionDialog.Open()
			self.QuestionDialog = QuestionDialog
		
		def AnswerQuestionSkipMission(self, answer):
			if not self.QuestionDialog:
				return
			
			if answer:
				net.SendChatPacket("/battle_pass skip %d" % (self.index))
		
			self.QuestionDialog.Close()
			self.QuestionDialog = None

		def GetInfoItem(self):
			return (self.title, self.type, self.vnum, self.count, self.maxCount)
		
		def SetItemToolTip(self, tooltipItem):
			self.tooltipItem = tooltipItem
			
		def AppendReward(self, vnum, count):
			if vnum == 0:
				return

			item.SelectItem(vnum)
			
			length = len(self.dictRewards)
			
			newReward = ui.ExpandedImageBoxWiki()
			newReward.SetParent(self)
			newReward.LoadImage(item.GetIconImageFileName())
			newReward.SetPosition(360 + (32 * (length // 2)), 6)
			newReward.Show()
			
			newReward.SAFE_SetStringEvent("MOUSE_OVER_IN",ui.__mem_func__(self.OverInReward), vnum)
			newReward.SAFE_SetStringEvent("MOUSE_OVER_OUT",ui.__mem_func__(self.OverOutReward))
			
			newCount = MakeTextLineRightAlign(newReward)
			newCount.SetPosition(1, 7)
			newCount.SetText(str(count))
			newCount.SetOutline()
			newCount.SetWindowName("text")
			
			self.dictRewards.append(newReward)
			self.dictRewards.append(newCount)
		
		def OnRender(self):
			xList, yList = self.parent.GetGlobalPosition()
			width, height = self.parent.GetWidth(), self.parent.GetHeight()	
		
			listImage = [self.bg, self.wndIcon, self.wndSkipMission]
			for image in listImage:
				if image:
					self.SetClipRect(image, xList, yList, xList + width, yList + height)
			
			self.bgGaugeFull.SetClipRect(0.0, yList, -1.0 + float(self.percentActual) / float(self.percentTotal), yList + self.parent.GetHeight(), True)
			
			listText = [self.wndTextLine, self.wndTextLine2, self.wndTextLine3, self.wndTextLine4, self.wndTextLine5, self.wndSkipMission.ButtonText]
			for text in listText:
				if text:
					xText, yText = text.GetGlobalPosition()
					text.Hide() if yText < yList or yText + text.GetTextSize()[1] > yList + height else text.Show()
			
			if len(self.dictRewards):
				for image in self.dictRewards:
					if image.GetWindowName() == "text":
						xText, yText = image.GetGlobalPosition()
						image.Hide() if yText < yList or yText + image.GetTextSize()[1] > yList + height else image.Show()
					else:
						self.SetClipRect(image, xList, yList, xList + width, yList + height)
						
			if self.coolTime > 0 and self.coolTime > app.GetGlobalTimeStamp():
				leftSec = self.coolTime - app.GetGlobalTimeStamp()
				self.wndTextLine5.SetText(localeInfo.LEFT_TIME + " : " + localeInfo.SecondToDHM(leftSec))
			elif self.coolTime > 0:
				self.wndTextLine5.SetText("")
				self.coolTime = 0

		def UpdateGauge(self, actual, total, coolTime):
			if total == 0:
				total = self.maxCount

			self.wndSkipMission.Show()
			
			self.coolTime = coolTime
			
			if coolTime > 0 and coolTime > app.GetGlobalTimeStamp():
				self.wndSkipMission.Hide()
			else:
				self.wndTextLine5.SetText("")

			self.count = actual
			self.percentActual = actual
			self.percentTotal = total
			
			self.wndTextLine.SetText(self.title + " (%d)" % (self.maxCount - self.count))
		
			if self.percentActual == self.percentTotal:
				self.bgGaugeFull.LoadImage(PATH_ROOT+"slice/quest/" + "gauge_red.png")
			# elif self.percentActual >= 0.5 * self.percentTotal:
				# self.bgGaugeFull.LoadImage(PATH_ROOT+"slice/quest/" + "gauge_blue.png")
			else:
				if self.isPremium:
					self.bgGaugeFull.LoadImage(PATH_ROOT+"slice/quest/" + "gauge_gold.png")
				else:
					self.bgGaugeFull.LoadImage(PATH_ROOT+"slice/quest/" + "gauge_blue.png")
			
		def SetClipRect(self, image, fLeft, fTop, fRight, fBottom):
			if image.GetWidth() == 0 and image.GetHeight() == 0:
				return
		
			(left, top, right, bottom) = image.GetRect()
			right = right + left
			bottom = bottom + top
			
			#calculate
			fDifLeft = -(float(fLeft - left) / float(image.GetWidth())) if (left < fLeft) else 0.0
			fDifTop = -(float(fTop - top) / float(image.GetHeight())) if (top < fTop) else 0.0
			fDifRight = -(float(right - fRight) / float(image.GetWidth())) if (right > fRight) else 0.0
			fDifBottom = -(float(bottom - fBottom) / float(image.GetHeight())) if (bottom > fBottom) else  0.0
			
			image.SetRenderingRect(fDifLeft, fDifTop, fDifRight, fDifBottom)

		def SelectImage(self):
			# self.bg.LoadImage(PATH_ROOT + "slice/quest/"+ "quest_gold.png")
			# self.OnSelectitemIndex([self.index])
			self.select = True

		def OverInImage(self):
			if self.select:
				return
		
			# self.bg.LoadImage(PATH_ROOT + "slice/quest/"+ "quest_gold.png")

		def OverOutImage(self):
			pass
			# if self.select == False:
				# self.bg.LoadImage(PATH_ROOT + "slice/quest/"+ "quest_gold.png")
	
		def SetSelect(self):
			self.select = True
			# self.bg.LoadImage(PATH_ROOT + "slice/quest/"+ "quest_gold.png")
	
		def OverOutForce(self):
			self.select = False
			# self.bg.LoadImage(PATH_ROOT + "slice/quest/"+ "quest_gold.png")
		
		def __del__(self):
			ui.Window.__del__(self)
			self.Reinitialize()
			
		def Reinitialize(self):
			self.xBase = 0
			self.yBase = 0

			self.bg = None
			self.dictRewards = []
			self.tooltipItem = None
			self.QuestionDialog = None
		
		def SetParent(self, parent):
			ui.Window.SetParent(self, parent)
			self.parent = proxy(parent)

		def SetBasePosition(self, x, y):
			self.xBase = x
			self.yBase = y
			
		def GetBasePosition(self):
			return (self.xBase, self.yBase)
			
		def OverInReward(self, vnum):
			if self.tooltipItem:
				self.tooltipItem.SetItemToolTip(vnum)
		
		def OverOutReward(self):
			if self.tooltipItem:
				self.tooltipItem.HideToolTip()
				
		def OnMouseLeftButtonDown(self):	
			self.SelectImage()

	def __init__(self):
		ui.Window.__init__(self)
		self.currentCategory = 0
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
				if itemH.IsShow() == FALSE:
					continue
				totalHeight += itemH.GetHeight() + 2
			
		return totalHeight

	def GetItemCount(self):
		return len(self.itemList)
			
	def SelectItemIndex(self, index):
		for x in range(len(self.itemList)):
			itemCurrent = self.itemList[x]
			itemCurrent.OverOutForce()
			
			if itemCurrent.index == index:	
				itemCurrent.SetSelect()
	
	def GetInfoItem(self, index):
		mission = self.GetMission(index)
		return mission.GetInfoItem()
	
	def GetFinishedMissions(self):
		count_finished = 0
		count_need_done = 0

		if self.itemList:
			for itemH in self.itemList:
				if itemH.percentActual >= itemH.percentTotal:
					count_finished += 1
				
				count_need_done += 1

		return (count_finished, count_need_done)
	
	def UpdateMissionCount(self, index, count, coolTime):
		mission = self.GetMission(index)
		
		if mission:
			mission.UpdateGauge(count, 0, coolTime)
	
	def GetMission(self, index):
		if self.itemList:
			for itemH in self.itemList:
				if itemH.index == index:
					return itemH

		return None
	
	def AppendItemReward(self, index, vnum, count):
		mission = self.GetMission(index)
		
		if mission:
			mission.AppendReward(vnum, count)
	
	def AppendItem(self, category, index, title, type, vnum, count, maxCount, expRecieve, func, isPremium, coolTime):
		item = self.NewItem(category, index, title, type, vnum, count, maxCount, expRecieve, func, isPremium, coolTime, self)
		item.SetParent(self)
		item.SetItemToolTip(self.tooltipItem)
		
		if len(self.itemList) == 0:
			item.SetBasePosition(0, 0)
		else:
			x, y = self.itemList[-1].GetLocalPosition()
			y += 2
			item.SetBasePosition(0, y + self.itemList[-1].GetHeight())
			
		if item.category == self.currentCategory:
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
		
		if totalHeight < self.GetHeight(): # fixme scroll
			self.scrollBar.Hide()
		else:
			self.scrollBar.Show()
	
	def ResetScrollbar(self):
		self.scrollBar.SetPos(0)
	
	def RefreshList(self, category):
		self.currentCategory = category
	
		for item in self.itemList:
			if item.category != self.currentCategory:
				item.Hide()
			else:
				item.Show()
	
	def AdjustItemPositions(self, scrolling = False, startIndex = -1):		
		scrollPos = self.scrollBar.GetPos()
		totalHeight = self.GetTotalItemHeight() - self.GetHeight()

		idx = 0
		if startIndex >= 0:
			idx = startIndex

		yAccumulate = 0
		for item in self.itemList[idx:]:
			if item.IsShow() == FALSE:
				continue
			
			if startIndex >= 0:
				yAccumulate -= item.GetHeight()
			
			if scrolling:
				setPos = yAccumulate - int(scrollPos * totalHeight)
				item.SetPosition(0, setPos)
			else:
				item.SetPosition(0, yAccumulate)
				
			item.SetBasePosition(0, yAccumulate)

			yAccumulate += item.GetHeight() + 2

	def SelectItem(self):
		if self.selectEvent:
			self.selectEvent()

	def Clear(self, bIsRefresh = False):
		if len(self.itemList) == 0:
			return
	
		for item in self.itemList:
			item.Reinitialize()
			item.Hide()
			del item
		
		if bIsRefresh == False:
			self.tooltipItem = None
		self.itemList = []

class ListBoxHorizontal(ui.Window):
	class NewItem(ui.Window):
		def __init__(self, index, vnum, count, iNecessaryLevel, status):
			ui.Window.__init__(self)
			self.index = index
			self.vnum = vnum
			self.status = status
			self.iNecessaryLevel = iNecessaryLevel
	
			self.Reinitialize()

			self.bg = ui.ExpandedImageBox()
			self.bg.SetParent(self)
			self.bg.AddFlag("not_pick")
			self.bg.SetPosition(0, 0)
			self.bg.LoadImage(PATH_ROOT + "slice/board_base.png")
			self.bg.Show()

			item.SelectItem(vnum)

			self.wndIcon = ui.ExpandedImageBox()
			self.wndIcon.SetParent(self)
			self.wndIcon.AddFlag("not_pick")
			self.wndIcon.LoadImage(item.GetIconImageFileName())
			self.wndIcon.SetWindowHorizontalAlignCenter()
			self.wndIcon.SetWindowVerticalAlignCenter()
			self.wndIcon.Show()

			self.wndCount = MakeTextLineRightAlign(self.wndIcon)
			self.wndCount.SetPosition(1, 7)
			self.wndCount.SetText(str(count))
			self.wndCount.SetOutline()
			self.wndCount.Show()
			
			self.wndStatus = ui.ExpandedImageBox()
			self.wndStatus.SetParent(self)
			self.wndStatus.AddFlag("not_pick")
			if status == 0: # is currently locked
				self.wndStatus.LoadImage(PATH_ROOT + "slice/items/item_lock.png")
			elif status == 1: # is currently ongoing
				pass
			elif status == 2: # is currently done
				self.wndStatus.LoadImage(PATH_ROOT + "slice/items/item_done.png")
			self.wndStatus.SetWindowHorizontalAlignCenter()
			self.wndStatus.SetWindowVerticalAlignCenter()
			self.wndStatus.Show()

			self.wndDesignLevel = None
			self.wndDesignLevelCount = None

			self.SetSize(self.bg.GetWidth() - 1, self.bg.GetHeight())		
	
		def SetItemToolTip(self, tooltipItem):
			self.tooltipItem = tooltipItem
		
		def SetDesignLevel(self):
			self.wndDesignLevel = ui.ExpandedImageBox()
			self.wndDesignLevel.SetParent(self)
			self.wndDesignLevel.AddFlag("not_pick")
			self.wndDesignLevel.LoadImage(PATH_ROOT + "slice/items/level_bar/bg_level_0.png")
			self.wndDesignLevel.SetPosition(30, -25)
			self.wndDesignLevel.Show()

			self.wndDesignLevelCount = ui.ExpandedImageBox()
			self.wndDesignLevelCount.SetParent(self.wndDesignLevel)
			self.wndDesignLevelCount.AddFlag("not_pick")
			self.wndDesignLevelCount.LoadImage(PATH_ROOT + "slice/items/level_bar/%d.png" % (self.iNecessaryLevel))
			self.wndDesignLevelCount.SetWindowHorizontalAlignCenter()
			self.wndDesignLevelCount.SetWindowVerticalAlignCenter()
			self.wndDesignLevelCount.Show()
	
		def OnRender(self):
			if self.status != 2:
				global CURRENT_LEVEL
				if CURRENT_LEVEL >= self.iNecessaryLevel:
					self.wndStatus.Hide()
			else:
				self.wndStatus.Show()

			xList, yList = self.parent.GetGlobalPosition()
			width, height = self.parent.GetWidth(), self.parent.GetHeight()	
			
			listImage = [self.bg, self.wndIcon, self.wndStatus]
			for image in listImage:
				if image:
					self.SetClipRect(image, xList, yList, xList + width, yList + height)
	
			listText = [self.wndCount]
			for text in listText:
				if text:
					xText, yText = text.GetGlobalPosition()
					text.Hide() if yText < yList or yText + text.GetTextSize()[1] > yList + height else text.Show()
					
					if xText < xList+10 or xText + text.GetTextSize()[0]-10 > xList + width:
						text.Hide()
			
			if self.wndDesignLevel:
				self.SetClipRect(self.wndDesignLevel, xList, yList - 55, xList + width, yList - 55 + height)
				self.SetClipRect(self.wndDesignLevelCount, xList, yList - 55, xList + width, yList - 55 + height)

		def SetClipRect(self, image, fLeft, fTop, fRight, fBottom):
			if image.GetWidth() == 0 and image.GetHeight() == 0:
				return
		
			(left, top, right, bottom) = image.GetRect()
			right = right + left
			bottom = bottom + top
			
			#calculate
			fDifLeft = -(float(fLeft - left) / float(image.GetWidth())) if (left < fLeft) else 0.0
			fDifTop = -(float(fTop - top) / float(image.GetHeight())) if (top < fTop) else 0.0
			fDifRight = -(float(right - fRight) / float(image.GetWidth())) if (right > fRight) else 0.0
			fDifBottom = -(float(bottom - fBottom) / float(image.GetHeight())) if (bottom > fBottom) else  0.0
			
			image.SetRenderingRect(fDifLeft, fDifTop, fDifRight, fDifBottom)
		
		def __del__(self):
			ui.Window.__del__(self)
			self.Reinitialize()
			
		def Reinitialize(self):
			self.xBase = 0
			self.yBase = 0

			self.bg = None
			self.tooltipItem = None
		
		def SetParent(self, parent):
			ui.Window.SetParent(self, parent)
			self.parent = proxy(parent)

		def SetBasePosition(self, x, y):
			self.xBase = x
			self.yBase = y
			
		def GetBasePosition(self):
			return (self.xBase, self.yBase)
			
		def OnMouseOverIn(self):
			if self.parent and getattr(self.parent, "IsPremiumTrack", None) and getattr(self.parent, "IsPremiumUnlocked", None):
				isPreview = False
				if getattr(self.parent, "IsPremiumPreview", None):
					isPreview = self.parent.IsPremiumPreview()

				if self.parent.IsPremiumTrack() and (not self.parent.IsPremiumUnlocked()) and (not isPreview):
					return

			wnd = osfInfo.GetInterfaceInstance()
			if wnd == None:
				return
			
			if wnd.tooltipItem:
				wnd.tooltipItem.SetItemToolTip(self.vnum)
		
		def OnMouseOverOut(self):
			wnd = osfInfo.GetInterfaceInstance()
			if wnd == None:
				return
			
			if wnd.tooltipItem:
				wnd.tooltipItem.HideToolTip()

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
		self.__isPremiumTrack = False
		self.__premiumUnlocked = True
		self.__premiumPreview = False

	def SetPremiumTrack(self, isPremiumTrack):
		self.__isPremiumTrack = bool(isPremiumTrack)

	def IsPremiumTrack(self):
		return self.__isPremiumTrack

	def SetPremiumUnlocked(self, premiumUnlocked):
		self.__premiumUnlocked = bool(premiumUnlocked)

	def IsPremiumUnlocked(self):
		return self.__premiumUnlocked

	def SetPremiumPreview(self, premiumPreview):
		self.__premiumPreview = bool(premiumPreview)

	def IsPremiumPreview(self):
		return self.__premiumPreview

	def SetParent(self, parent):
		ui.Window.SetParent(self, parent)
		
		self.SetPosition(5, 5)
		self.SetSize(parent.GetWidth() - 10, parent.GetHeight() - 10)

	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollSpeed(50)
		self.scrollBar = scrollBar

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem
		
	def SetSelectEvent(self, event):
		self.selectEvent = event
			
	def GetTotalItemWidth(self):
		totalHeight = 0
		
		if self.itemList:
			for itemH in self.itemList:
				totalHeight += itemH.GetWidth() + 2
			
		return totalHeight

	def AppendItem(self, index, vnum, count, iNecessaryLevel, state, setDesignlevel = False):
		item = self.NewItem(index, vnum, count, iNecessaryLevel, state)
		item.SetParent(self)
		item.SetItemToolTip(self.tooltipItem)
		
		if setDesignlevel:
			item.SetDesignLevel()
		
		if len(self.itemList) == 0:
			item.SetBasePosition(0, 0)
		else:
			x, y = self.itemList[-1].GetLocalPosition()

			item.SetBasePosition(x + self.itemList[-1].GetWidth(), 0)
			
		item.Show()
		self.itemList.append(item)
		
		# self.AdjustScrollBar()
		self.AdjustItemPositions()
	
	def AdjustScrollBar(self):
		totalHeight = float(self.GetTotalItemHeight())
		if totalHeight:
			scrollBarHeight = min(float(self.GetHeight() - 10) / totalHeight, 1.0)
		else:
			scrollBarHeight = 1.0
	
		self.scrollBar.SetMiddleBarSize(scrollBarHeight)
		
		if totalHeight < self.GetHeight(): # fixme scroll
			self.scrollBar.Hide()
		else:
			self.scrollBar.Show()
	
	def ResetScrollbar(self):
		self.scrollBar.SetPos(0)

	def AdjustItemPositions(self, scrolling = False, startIndex = -1):		
		scrollPos = self.scrollBar.middleBar.GetLocalPosition()[0] * 0.0032
		totalHeight = self.GetTotalItemWidth() - self.GetWidth()

		idx = 0
		if startIndex >= 0:
			idx = startIndex

		for item in self.itemList[idx:]:
			xB, yB = item.GetBasePosition()
			
			if startIndex >= 0:
				yB -= 2
			
			if scrolling:
				setPos = xB - int(scrollPos * totalHeight)
				item.SetPosition(setPos, yB)
			else:
				item.SetPosition(xB, yB)
				
			item.SetBasePosition(xB, yB)

	def Clear(self, bIsRefresh = False):
		if len(self.itemList) == 0:
			return
	
		for item in self.itemList:
			item.Reinitialize()
			item.Hide()
			del item
		
		if bIsRefresh == False:
			self.tooltipItem = None
		self.itemList = []

class BattlePassWindow(ui.ScriptWindow):
	def __init__(self):
		self.bLoaded = False
		self.tooltipItem = None
		self.ListBoxItem = None
		self.ListBoxItems = None
		self.__premiumUnlocked = False
		self.seasonEndTime = 0
		self.__lastSeasonRemainUpdate = 0
		
		ui.ScriptWindow.__init__(self)
		self.LoadWindow()
		self.SetCenterPosition()
		
	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		
		self.categories = []
		
		if self.ListBoxItem:
			self.ListBoxItem.Clear()
		self.ListBoxItem = None
		
		if self.ListBoxItems:
			self.ListBoxItems.Clear()
		self.ListBoxItems = None
		
		self.bLoadedInfo = False
		self.tooltipItem = None

	def SetItemToolTip(self, itemTooltip):
		self.tooltipItem = itemTooltip
		self.ListBoxItem.SetItemToolTip(self.tooltipItem)

	def Show(self):
		self.LoadWindow()
		self.SetTop()
		ui.ScriptWindow.Show(self)
		
		self.ListBoxItem.Clear()
		self.ListBoxItems.Clear()
		self.ListBoxItemsPremium.Clear()

		if self.ListBoxItemsPremium:
			self.ListBoxItemsPremium.SetPremiumPreview(False)

		if self.__premiumUnlocked:
			self.premium_board.Hide()
		else:
			self.premium_board.Show()
		
		net.SendChatPacket("/battle_pass request")

	def LoadWindow(self):
		if self.bLoaded == True:
			return
			
		self.bLoaded = True

		self.AddFlag("movable")
		self.AddFlag("float")

		# self.BoardEx = ui.Board()
		# self.BoardEx.SetParent(self)
		# self.BoardEx.SetSize(180, 45)
		# self.BoardEx.SetPosition(320, 290)
		# self.BoardEx.Show()
	
		self.Board = ui.BoardWithTitleBar()
		self.Board.SetParent(self)
		self.Board.SetSize(499, 285 + 35 + 25)
		self.Board.SetTitleName("Battle Pass")
		self.Board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.Board.Show()
		
		self.SetSize(self.Board.GetWidth(), self.Board.GetHeight() + 32)
			
		self.LoadTopBoard()
		self.LoadBottomBoard()
		
		self.LoadItemsByExpBoard()
		self.LoadMiddleBoard()
		
		self.ClickCategory(0)
		self.RefreshCategory()

		self.wndSeasonRemain = ui.MakeTextLineNew(self, 242, 53, "")
		self.wndSeasonRemain.SetFontName(localeInfo.UI_BOLD_FONT)
		self.wndSeasonRemain.SetPackedFontColor(0xFFC6B38D)
		self.wndSeasonRemain.SetTop()
	
	def LoadTopBoard(self):
		self.boardExpInfo = ui.MakeExpandedImageBox(self, PATH_ROOT+"slice/" + "top_bg.png", 8, 30, "not_pick")
		self.bannerMonth = ui.MakeExpandedImageBox(self, PATH_ROOT+"slice/banners/" + "banner_06.png", 239, 32, "not_pick")
		
		self.wndLevel = ui.MakeTextLineNew(self.boardExpInfo, 30, 10, "Lv. 0")
		self.wndEXP = ui.MakeTextLineNew(self.boardExpInfo, 150, 10, "0/100 EXP")
		self.boardGaugeEXP = ui.MakeExpandedImageBox(self, PATH_ROOT+"slice/" + "gauge.png", 34, 57, "not_pick")
		self.GaugeEXP = ui.MakeExpandedImageBox(self.boardGaugeEXP, PATH_ROOT+"slice/" + "gauge_inner.png", 3, 3, "not_pick")
		
		# Gauge Lines
		self.LinegaugeEXP1 = ui.MakeExpandedImageBox(self.boardGaugeEXP, PATH_ROOT+"slice/" + "gauge_line.png", 37, 1, "not_pick")
		self.LinegaugeEXP2 = ui.MakeExpandedImageBox(self.boardGaugeEXP, PATH_ROOT+"slice/" + "gauge_line.png", 33*2, 1, "not_pick")
		self.LinegaugeEXP3 = ui.MakeExpandedImageBox(self.boardGaugeEXP, PATH_ROOT+"slice/" + "gauge_line.png", 33*3, 1, "not_pick")
		self.LinegaugeEXP4 = ui.MakeExpandedImageBox(self.boardGaugeEXP, PATH_ROOT+"slice/" + "gauge_line.png", 33*4, 1, "not_pick")
		
		# GaugeEXP Effect
		self.wndAnimEXP = ui.AniImageBox()
		self.wndAnimEXP.SetParent(self.boardGaugeEXP)
		self.wndAnimEXP.SetPosition(0, 0)
		self.wndAnimEXP.SetDelay(3)
		self.wndAnimEXP.Show()
		
		self.dictImagesEXPEffect = []
		for x in range(53):
			self.wndAnimEXP.AppendImage(PATH_ROOT+"gauge effect gif/gauge_effect_%02d.png" % (x))
		
	def LoadMiddleBoard(self):
		self.board_Base = ui.BoxedBoard()
		self.board_Base.SetParent(self.Board)
		self.board_Base.SetPosition(8, 90 + 25)
		self.board_Base.SetSize(482, 218)
		self.board_Base.Show()	
		
		self.categories = []
		
		btnCategory1 = ui.MakeRadioButton(self, 8, 91, PATH_ROOT+"slice/quest/" , "btn_l_0.png", "btn_l_1.png", "btn_l_1.png")
		btnCategory1.SetText(localeInfo.BATTLE_PASS_DAILY)
		btnCategory1.Down()
		
		self.categories.append(btnCategory1)
		
		btnCategory2 = ui.MakeRadioButton(self, 8 + 84, 91, PATH_ROOT+"slice/quest/" , "btn_m_0.png", "btn_m_1.png", "btn_m_1.png")
		btnCategory2.SetText(localeInfo.BATTLE_PASS_WEEKLY)
		self.categories.append(btnCategory2)
		
		btnCategory3 = ui.MakeRadioButton(self, 8 + 84 + 82, 91, PATH_ROOT+"slice/quest/" , "btn_r_0.png", "btn_r_1.png", "btn_r_1.png")
		btnCategory3.SetText(localeInfo.BATTLE_PASS_MONTHLY)
		self.categories.append(btnCategory3)
	
		for i, btnCat in enumerate(self.categories):
			btnCat.SetEvent(ui.__mem_func__(self.ClickCategoryMission), i)
		
		# Mission List Code
		self.ScrollBarItem = ScrollBarNew()
		self.ScrollBarItem.SetParent(self.board_Base)
		self.ScrollBarItem.SetScrollBarSize(self.board_Base.GetHeight() - 6)
		self.ScrollBarItem.SetPosition(self.board_Base.GetWidth() - 12, 3)
		self.ScrollBarItem.Show()

		self.ListBoxItem = ListBox()
		self.ListBoxItem.SetParent(self.board_Base)
		self.ListBoxItem.SetScrollBar(self.ScrollBarItem)
		self.ListBoxItem.SetSize(self.board_Base.GetWidth() - self.ScrollBarItem.GetWidth() - 2, self.board_Base.GetHeight() - 4)
		self.ListBoxItem.SetPosition(2, 2)
		self.ListBoxItem.Show()

	def LoadBottomBoard(self):
		self.currentCategory = 1
	
		self.btnCategoryBG = ui.MakeImageBox(self, PATH_ROOT + "slice/btns_quests.tga", 2, 275 + 35 + 25)

		self.btnCategory1 = ui.MakeButton(self.btnCategoryBG, 0, 0, "", PATH_ROOT+"slice/" , "btn.tga", "btn.tga", "btn.tga")
		self.btnCategory1.SetEvent(ui.__mem_func__(self.ClickCategory), 0)

		self.btnCategory2 = ui.MakeButton(self.btnCategoryBG, 59, 0, "", PATH_ROOT+"slice/" , "btn.tga", "btn.tga", "btn.tga")
		self.btnCategory2.SetEvent(ui.__mem_func__(self.ClickCategory), 1)
		
		# Collect Button
		self.btnCollect = ui.MakeButton(self, 423, 275+ 35 + 25, "", PATH_ROOT+"slice/" , "btn_collect_0.png", "btn_collect_1.png", "btn_collect_2.png")
		self.btnCollect.SetEvent(ui.__mem_func__(self.ClickCollect))	
		
		# Shop Button
		# self.btnShop = ui.MakeButton(self, 330, 275+ 42, "", PATH_ROOT+"slice/quest/" , "btn_0.png", "btn_1.png", "btn_2.png")
		# self.btnShop.SetText("Shop")
		# self.btnShop.SetEvent(ui.__mem_func__(self.ClickShop))	

	def LoadItemsByExpBoard(self):
		self.board_Base_items = ui.MakeExpandedImageBox(self, PATH_ROOT+"slice/items/" + "bg_fram_norm.png", 8, 90, "not_pick")

		self.board_BaseItems = ui.BorderA()
		self.board_BaseItems.SetParent(self.board_Base_items)
		self.board_BaseItems.SetPosition(71, 17)
		self.board_BaseItems.SetSize(409, 193)
		self.board_BaseItems.Show()

		self.ScrollBarItems = ui.WikiScrollBar(True)
		self.ScrollBarItems.SetParent(self)
		self.ScrollBarItems.SetSize(481, 12)
		self.ScrollBarItems.SetPosition(8, 300)
		self.ScrollBarItems.SetStaticScale(90)
		self.ScrollBarItems.Show()
		
		self.ListBoxItems = ListBoxHorizontal()
		self.ListBoxItems.SetParent(self.board_BaseItems)
		self.ListBoxItems.SetScrollBar(self.ScrollBarItems)
		self.ListBoxItems.SetSize(self.board_BaseItems.GetWidth() - 5, 100)
		self.ListBoxItems.SetPosition(3, 3)
		self.ListBoxItems.SetPremiumTrack(False)
		self.ListBoxItems.SetPremiumUnlocked(True)
		self.ListBoxItems.Show()

		self.ListBoxItemsPremium = ListBoxHorizontal()
		self.ListBoxItemsPremium.SetParent(self.board_BaseItems)
		self.ListBoxItemsPremium.SetScrollBar(self.ScrollBarItems)
		self.ListBoxItemsPremium.SetSize(self.board_BaseItems.GetWidth() - 5, 100)
		self.ListBoxItemsPremium.SetPosition(3, 98)
		self.ListBoxItemsPremium.SetPremiumTrack(True)
		self.ListBoxItemsPremium.SetPremiumUnlocked(self.__premiumUnlocked)
		self.ListBoxItemsPremium.SetPremiumPreview(False)
		self.ListBoxItemsPremium.Show()

		self.ScrollBarItems.SetScrollEvent(self.OnScrollPageItems)
		
		# Premium Lock
		self.premium_board = ui.MakeExpandedImageBox(self.board_BaseItems, PATH_ROOT+"slice/items/" + "big_lock.png", 1, 100, "not_pick")

		self.btnPreviewPremium = ui.MakeButton(self.premium_board , 245, 33, "", PATH_ROOT+"slice/quest/" , "btn_0.png", "btn_1.png", "btn_2.png")
		self.btnPreviewPremium.SetEvent(ui.__mem_func__(self.ClickPreviewPremium))
		self.btnPreviewPremium.SetText(localeInfo.BP_PREVIEW_REWARD)

		# test
		# for x in range(20):
			# self.ListBoxItems.AppendItem(x, 71084, 15 + x, 2, True)
			# self.ListBoxItemsPremium.AppendItem(x, 71085, 15 + x, False)
			
		# self.SetExperience(150, 300)
	
	def OnScrollPageItems(self):
		self.ListBoxItems.AdjustItemPositions(True)
		self.ListBoxItemsPremium.AdjustItemPositions(True)
	
	def ClickPreviewPremium(self):
		self.premium_board.Hide()
		if self.ListBoxItemsPremium:
			self.ListBoxItemsPremium.SetPremiumPreview(True)
	
	def ClickCollect(self):
		net.SendChatPacket("/battle_pass collect")
	
	def ClickShop(self):
		net.SendChatPacket("/open_shop %d" % (OPEN_SHOP_ID))
	
	def ClickCategory(self, nextCategory):
		if self.currentCategory == nextCategory:
			return

		self.currentCategory = not self.currentCategory

		if self.currentCategory == 0:
			self.btnCategoryBG.LoadImage(PATH_ROOT + "slice/btns_items.tga")
			
			self.Board.SetSize(499, 285 + 35)
			self.btnCategoryBG.SetPosition(2, 275+ 35)
			self.btnCollect.SetPosition(423, 275+ 35)
			
			for btnCat in self.categories:
				btnCat.Hide()
		else:
			self.btnCategoryBG.LoadImage(PATH_ROOT + "slice/btns_quests.tga")
			
			self.Board.SetSize(499, 285 + 35 + 25)
			self.btnCategoryBG.SetPosition(2, 275+ 35 + 25)
			self.btnCollect.SetPosition(423, 275+ 35 + 25)
			
			for btnCat in self.categories:
				btnCat.Show()
			
		self.RefreshCategory()

	def Close(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True
	
	def RefreshCategory(self):
		if self.currentCategory == 1:
			self.board_Base.Show()
			self.board_Base_items.Hide()
			self.ScrollBarItems.Hide()
			self.btnCollect.Hide()
		else:
			self.board_Base_items.Show()
			self.board_Base.Hide()
			self.ScrollBarItems.Show()
			self.btnCollect.Show()
	
	# Recv Packets
	def AppendMission(self, category, index, title, type, vnum, count, maxCount, expRecv, isPremium, coolTime):
		self.ListBoxItem.AppendItem(category, index, title, type, vnum, count, maxCount, expRecv, None, isPremium, coolTime)

	def AppendMissionReward(self, category, index, vnum, count):
		self.ListBoxItem.AppendItemReward(category, index, vnum, count)
		
	def UpdateMission(self, index, count, coolTime):
		self.ListBoxItem.UpdateMissionCount(index, count, coolTime)
		
	def AppendRewardItem(self, index, vnum, count, status, isPremium, iNecessaryLevel):
		if isPremium:
			self.ListBoxItemsPremium.AppendItem(index, vnum, count, iNecessaryLevel, status)
		else:
			self.ListBoxItems.AppendItem(index, vnum, count, iNecessaryLevel, status, True)

	def SetExperience(self, exp, maxExp):
		global CURRENT_LEVEL
		if CURRENT_LEVEL >= MAX_BP_LEVEL:
			self.GaugeEXP.SetPercentage(1, 1)
			return

		if maxExp == 0:
			maxExp = 1
		exp = min(exp, maxExp)
		self.wndEXP.SetText("%d/%d EXP" % (exp, maxExp))
		self.GaugeEXP.SetPercentage(exp, maxExp)

	def SetLevel(self, currentLevel):
		global CURRENT_LEVEL
		CURRENT_LEVEL = min(currentLevel, MAX_BP_LEVEL)

		if CURRENT_LEVEL >= MAX_BP_LEVEL:
			self.wndLevel.SetText("Lv. %d (MAX)" % MAX_BP_LEVEL)
			self.wndEXP.SetText(localeInfo.BATTLE_PASS_MAX_LEVEL)
			self.GaugeEXP.SetPercentage(1, 1)
		else:
			self.wndLevel.SetText("Lv. %d" % CURRENT_LEVEL)

	def UnlockPremium(self):
		self.__premiumUnlocked = True
		self.premium_board.Hide()
		if self.ListBoxItemsPremium:
			self.ListBoxItemsPremium.SetPremiumUnlocked(True)

	def SetSeasonEndTime(self, seasonEndUnix):
		self.seasonEndTime = int(seasonEndUnix)
		self.__lastSeasonRemainUpdate = 0
		self.__RefreshSeasonRemainText()

	def __RefreshSeasonRemainText(self):
		if not self.wndSeasonRemain:
			return
		fmt = getattr(localeInfo, "BATTLE_PASS_REMAINING_TIME", "Time remaining : %s")
		if self.seasonEndTime <= 0:
			self.wndSeasonRemain.SetText("")
			return
		now = app.GetGlobalTimeStamp()
		left = max(0, self.seasonEndTime - now)
		self.wndSeasonRemain.SetText(fmt % localeInfo.SecondToDHM(left))

	def OnUpdate(self):
		if self.seasonEndTime <= 0 or not self.wndSeasonRemain:
			return
		t = app.GetTime()
		if t - self.__lastSeasonRemainUpdate < 1.0:
			return
		self.__lastSeasonRemainUpdate = t
		self.__RefreshSeasonRemainText()
	
	def ClearBattlePass(self):
		self.ListBoxItem.Clear()
		self.ListBoxItems.Clear()
		self.ListBoxItemsPremium.Clear()
		self.seasonEndTime = 0
		self.__lastSeasonRemainUpdate = 0
		if self.wndSeasonRemain:
			self.wndSeasonRemain.SetText("")

	def OnMouseWheel(self, nLen):
		if nLen > 0:
			self.ScrollBarItem.OnUp()
			return True
			
		elif nLen < 0:
			self.ScrollBarItem.OnDown()
			return True
			
		return False

	def ClickCategoryMission(self, index):
		self.selectedCategoryMission = index
		
		for i, btnCat in enumerate(self.categories):
			if index == i:
				btnCat.Down()
			else:
				btnCat.SetUp()		
		
		self.ListBoxItem.RefreshList(self.selectedCategoryMission)
		
		self.ListBoxItem.ResetScrollbar()
		self.ListBoxItem.AdjustScrollBar()
		self.ListBoxItem.AdjustItemPositions()

class ScrollBarNew(ui.Window):
	SCROLLBAR_WIDTH = 7
	SCROLL_BTN_XDIST = 0
	SCROLL_BTN_YDIST = 0
	class MiddleBar(ui.DragButton):
		def __init__(self):
			ui.DragButton.__init__(self)
			self.AddFlag("movable")
			self.SetWindowName("scrollbar_middlebar")
		def MakeImage(self):
			top = ui.ExpandedImageBox()
			top.SetParent(self)
			top.LoadImage(IMG_DIR+"scrollbar/scrollbar_top.tga")
			top.AddFlag("not_pick")
			top.Show()
			topScale = ui.ExpandedImageBox()
			topScale.SetParent(self)
			topScale.SetPosition(0, top.GetHeight())
			topScale.LoadImage(IMG_DIR+"scrollbar/scrollbar_scale.tga")
			topScale.AddFlag("not_pick")
			topScale.Show()
			bottom = ui.ExpandedImageBox()
			bottom.SetParent(self)
			bottom.LoadImage(IMG_DIR+"scrollbar/scrollbar_bottom.tga")
			bottom.AddFlag("not_pick")
			bottom.Show()
			bottomScale = ui.ExpandedImageBox()
			bottomScale.SetParent(self)
			bottomScale.LoadImage(IMG_DIR+"scrollbar/scrollbar_scale.tga")
			bottomScale.AddFlag("not_pick")
			bottomScale.Show()
			middle = ui.ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage(IMG_DIR+"scrollbar/scrollbar_mid.tga")
			middle.AddFlag("not_pick")
			middle.Show()
			self.top = top
			self.topScale = topScale
			self.bottom = bottom
			self.bottomScale = bottomScale
			self.middle = middle
		def SetSize(self, height):
			minHeight = self.top.GetHeight() + self.bottom.GetHeight() + self.middle.GetHeight()
			height = max(minHeight, height)
			ui.DragButton.SetSize(self, 10, height)
			scale = (height - minHeight) // 2
			extraScale = 0
			if (height - minHeight) % 2 == 1:
				extraScale = 1
			self.topScale.SetRenderingRect(0, 0, 0, scale - 1)
			self.middle.SetPosition(0, self.top.GetHeight() + scale)
			self.bottomScale.SetPosition(0, self.middle.GetBottom())
			self.bottomScale.SetRenderingRect(0, 0, 0, scale - 1 + extraScale)
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
		self.scrollStep = 0.4
		self.SetWindowName("NONAME_ScrollBar")
	def __del__(self):
		ui.Window.__del__(self)
	def CreateScrollBar(self):
		topImage = ui.ExpandedImageBox()
		topImage.SetParent(self)
		topImage.AddFlag("not_pick")
		topImage.LoadImage(IMG_DIR+"scrollbar/scroll_top.tga")
		topImage.Show()
		bottomImage = ui.ExpandedImageBox()
		bottomImage.SetParent(self)
		bottomImage.AddFlag("not_pick")
		bottomImage.LoadImage(IMG_DIR+"scrollbar/scroll_bottom.tga")
		bottomImage.Show()
		middleImage = ui.ExpandedImageBox()
		middleImage.SetParent(self)
		middleImage.AddFlag("not_pick")
		middleImage.SetPosition(0, topImage.GetHeight())
		middleImage.LoadImage(IMG_DIR+"scrollbar/scroll_mid.tga")
		middleImage.Show()
		self.topImage = topImage
		self.bottomImage = bottomImage
		self.middleImage = middleImage
		middleBar = self.MiddleBar()
		middleBar.SetParent(self)
		middleBar.SetMoveEvent(ui.__mem_func__(self.OnMove))
		middleBar.Show()
		middleBar.MakeImage()
		middleBar.SetSize(12)
		self.middleBar = middleBar
	def Destroy(self):
		self.eventScroll = None
		self.eventArgs = None
	def SetScrollEvent(self, event, *args):
		self.eventScroll = event
		self.eventArgs = args
	def SetMiddleBarSize(self, pageScale):
		self.middleBar.SetSize(int(pageScale * float(self.GetHeight() - (self.SCROLL_BTN_YDIST*2))))
		realHeight = self.GetHeight() - (self.SCROLL_BTN_YDIST*2) - self.middleBar.GetHeight()
		self.pageSize = realHeight

	def SetScrollBarSize(self, height):
		self.SetSize(self.SCROLLBAR_WIDTH, height)
		self.pageSize = height - self.SCROLL_BTN_YDIST*2 - self.middleBar.GetHeight()
		middleImageScale = float((height - self.SCROLL_BTN_YDIST*2) - self.middleImage.GetHeight()) / float(self.middleImage.GetHeight())
		self.middleImage.SetRenderingRect(0, 0, 0, middleImageScale)
		self.bottomImage.SetPosition(0, height - self.bottomImage.GetHeight())
		self.middleBar.SetRestrictMovementArea(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST, \
			self.middleBar.GetWidth(), height - self.SCROLL_BTN_YDIST * 2)
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST)
	def SetScrollStep(self, step):
		self.scrollStep = step
	def OnUp(self):
		self.SetPos(self.curPos-self.scrollStep)
	def OnDown(self):
		self.SetPos(self.curPos+self.scrollStep)
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
