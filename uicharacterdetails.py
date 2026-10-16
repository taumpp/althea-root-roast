import ui, player, item, net, app, localeInfo
from uiToolTip import ItemToolTip, GET_AFFECT_STRING

import osfInfo

IMG_DIR = "d:/ymir work/ui/game/characterdetails/"
# only need setting here bro do u have question?
bonus_list = [
	[localeInfo.BONUS_TABLE_TITLE_1,
		[
			[item.APPLY_ATTBONUS_MONSTER,53],
			[item.APPLY_ATTBONUS_METIN,160],
			[item.APPLY_ATTBONUS_BOSS,161],
			[item.APPLY_ATTBONUS_UNDEAD,47],
			[item.APPLY_ATTBONUS_DEVIL,48],
			[item.APPLY_ATTBONUS_ORC,45],
			[item.APPLY_ATTBONUS_ANIMAL,44],
			[item.APPLY_ATTBONUS_MILGYO,46],
			[item.APPLY_STEAL_HP,63],
			[item.APPLY_HP_REGEN,32],
			[item.APPLY_EXP_DOUBLE_BONUS,83],
			[item.APPLY_GOLD_DOUBLE_BONUS,84],
			[item.APPLY_ITEM_DROP_BONUS,85],
			[item.APPLY_ENCHANT_ELECT, item.GetApplyPoint(item.APPLY_ENCHANT_ELECT)],
			[item.APPLY_ENCHANT_FIRE, item.GetApplyPoint(item.APPLY_ENCHANT_FIRE)],
			[item.APPLY_ENCHANT_ICE, item.GetApplyPoint(item.APPLY_ENCHANT_ICE)],
			[item.APPLY_ENCHANT_WIND, item.GetApplyPoint(item.APPLY_ENCHANT_WIND)],
			[item.APPLY_ENCHANT_EARTH, item.GetApplyPoint(item.APPLY_ENCHANT_EARTH)],
			[item.APPLY_ENCHANT_DARK, item.GetApplyPoint(item.APPLY_ENCHANT_DARK)],
		]
	],
	[localeInfo.BONUS_TABLE_TITLE_2,
		[
			[item.APPLY_ATTBONUS_HUMAN,43],
			[item.APPLY_ATTBONUS_WARRIOR,54],
			[item.APPLY_ATTBONUS_ASSASSIN,55],
			[item.APPLY_ATTBONUS_SURA,56],
			[item.APPLY_ATTBONUS_SHAMAN,57],
			[item.APPLY_RESIST_WARRIOR,59],
			[item.APPLY_RESIST_ASSASSIN,60],
			[item.APPLY_RESIST_SURA,61],
			[item.APPLY_RESIST_SHAMAN,62],
			[item.APPLY_RESIST_HUMAN,159],
			[item.APPLY_RESIST_SWORD,69],
			[item.APPLY_RESIST_TWOHAND,70],
			[item.APPLY_RESIST_DAGGER,71],
			[item.APPLY_RESIST_BELL,72],
			[item.APPLY_RESIST_FAN,73],
			[item.APPLY_RESIST_BOW,74],
			[item.APPLY_RESIST_MAGIC,77],
		]
	],
	[localeInfo.BONUS_TABLE_TITLE_3,
		[
			[item.APPLY_SKILL_DAMAGE_BONUS,121],
			[item.APPLY_NORMAL_HIT_DAMAGE_BONUS,122],
			[item.APPLY_CRITICAL_PCT,40],
			[item.APPLY_PENETRATE_PCT,41],
			[item.APPLY_POISON_PCT,37],
			[item.APPLY_SLOW_PCT,39],
			[item.APPLY_STUN_PCT,38],
			[item.APPLY_CAST_SPEED,21],
			[item.APPLY_ATT_GRADE_BONUS,95],
		]
	],
	[localeInfo.BONUS_TABLE_TITLE_4,
		[
			[item.APPLY_SKILL_DEFEND_BONUS,123],
			[item.APPLY_NORMAL_HIT_DEFEND_BONUS,124],
			[item.APPLY_ANTI_CRITICAL_PCT,136],
			[item.APPLY_ANTI_PENETRATE_PCT,137],
			[item.APPLY_BLOCK,67],
			[item.APPLY_REFLECT_MELEE,79],
			[item.APPLY_DODGE,68],
			[item.APPLY_POISON_REDUCE,81],
			[item.APPLY_RESIST_FIRE,75],
			[item.APPLY_RESIST_ELEC,76],
			[item.APPLY_RESIST_WIND,78],
		]
	],
]

stat_list = [
 [localeInfo.BONUS_TABLE_4, player.KILL_ALLPLAYER],
 [localeInfo.BONUS_TABLE_5, player.KILL_DUELWON],
 [localeInfo.BONUS_TABLE_6, player.KILL_DUELLOST],
 [localeInfo.BONUS_TABLE_7, player.KILL_MONSTER],
 [localeInfo.BONUS_TABLE_8, player.KILL_BOSSES ],
 [localeInfo.BONUS_TABLE_9, player.KILL_METINSTONE]
]

class CharacterDetailsUI(ui.ScriptWindow):
	def __del__(self):
		ui.ScriptWindow.__del__(self)
	def Destroy(self):
		self.ClearDictionary()
		self.btnIndex = 0
		self.isPacketLoaded = False
	def Show(self):
		ui.ScriptWindow.Show(self)
		self.SetTop()
		self.Refresh()
	def Close(self):
		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True
	def AdjustPosition(self, x, y):
		self.SetPosition(x + self.GetWidth(), y)
	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			radioBtn = buttonList[buttonIndex]
		except IndexError:
			return
		for eachButton in buttonList:
			eachButton.SetUp()
		radioBtn.Down()
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.Destroy()
		self.__LoadScript()
	def __LoadScript(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/CharacterDetailsWindow.py")

			self.GetChild("bonus_button").SAFE_SetEvent(self.SetCategory,0)
			self.GetChild("stat_button").SAFE_SetEvent(self.SetCategory,1)
			
		except:
			import exception
			exception.Abort("CharacterDetailsUI.__LoadScript")

		#self.ScrollBar = self.GetChild("ScrollBar")
		#self.ScrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))

		elementList = self.ElementDictionary
		statWindow = self.GetChild("stat_window")
		for i in range(len(stat_list)):
			statName = ui.TextLine()
			statName.SetParent(statWindow)
			statName.AddFlag("not_pick")
			statName.SetPosition(70,15+(i*40))
			statName.SetFontName("Tahoma:13")
			statName.SetHorizontalAlignCenter()
			statName.SetText(stat_list[i][0])
			statName.Show()
			elementList["%d_stat_name"%i] = statName

			statValue = ui.TextLine()
			statValue.AddFlag("not_pick")
			statValue.SetParent(statWindow)
			statValue.SetPosition(180,15+(i*40))
			statValue.SetFontName("Tahoma:13")
			statValue.SetHorizontalAlignCenter()
			statValue.Show()
			elementList["%d_stat"%i] = statValue

		bonusWindow = self.GetChild("bonus_window")

		searchBoard = SearchSlotBoard()
		searchBoard.SetParent(bonusWindow)
		searchBoard.SetPosition((bonusWindow.GetWidth()//2)-(129//2),11)
		searchBoard.SetSize(129,23)
		searchBoard.Show()
		elementList["searchBoard"] = searchBoard

		itemSearch = ui.EditLine()
		itemSearch.SetParent(searchBoard)
		itemSearch.SetMax(40)
		itemSearch.SetPosition(5,5)
		itemSearch.SetSize(searchBoard.GetWidth(), searchBoard.GetHeight())
		itemSearch.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdate)
		itemSearch.SetEscapeEvent(ui.__mem_func__(self.Close))
		itemSearch.Show()
		elementList["itemSearch"] = itemSearch

		searchBtn = ui.Button()
		searchBtn.SetParent(searchBoard)
		searchBtn.SetUpVisual(IMG_DIR+"search_btn_0.tga")
		searchBtn.SetOverVisual(IMG_DIR+"search_btn_1.tga")
		searchBtn.SetDownVisual(IMG_DIR+"search_btn_2.tga")
		searchBtn.SetEvent(self.__OnValueUpdate)
		searchBtn.SetPosition(itemSearch.GetWidth()-searchBtn.GetWidth(),2)
		searchBtn.Show()
		elementList["searchBtn"] = searchBtn

		#bonusWindow.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)

		scrollBar = ScrollBarNew()
		scrollBar.SetParent(bonusWindow)
		scrollBar.SetPosition((bonusWindow.GetWidth()-scrollBar.GetWidth())-3,43)
		scrollBar.SetScrollBarSize((bonusWindow.GetHeight()-46)-5)
		scrollBar.SetScrollEvent(ui.__mem_func__(self.Refresh))
		scrollBar.Show()
		elementList["scrollBar"] = scrollBar

		for i in range(len(bonus_list)):
			bonus_data = bonus_list[i][1]

			category = ui.ExpandedImageBox()
			category.SetParent(bonusWindow)
			category.LoadImage(IMG_DIR+"category_item.tga")
			category.buttonStatus = 0
			category.SetEvent(ui.__mem_func__(self.SetBonusCategory),"mouse_click", i)
			category.Show()
			elementList["%d_category"%i] = category

			categoryText = ui.TextLine()
			categoryText.SetParent(category)
			categoryText.SetHorizontalAlignLeft()
			categoryText.SetPosition(8,3)
			categoryText.SetText("|Ikey/plus|i "+bonus_list[i][0])
			categoryText.Show()
			elementList["%d_categoryText"%i] = categoryText

			for j in range(len(bonus_data)):
				bonusImage = ui.ExpandedImageBox()
				#bonusImage.AddFlag("not_pick")
				bonusImage.SetParent(bonusWindow)
				bonusImage.LoadImage(IMG_DIR+"bonus_item.tga")
				bonusImage.Show()
				elementList["%d_%d_image"%(i,j)] = bonusImage

				bonusText = GET_AFFECT_STRING(bonus_data[j][0], 0)
				
				disabledStr = ["%","+"]
				newText = ""
				for x in bonusText:
					if x in disabledStr:
						continue
					if x.isdigit():
						continue
					newText+=x
				bonusText=newText
				bonusImage.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInBonus, bonusText)
				bonusImage.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutBonus)
				
				#bonusText = bonusText.replace(":","")
				#index = bonusText.find("+")
				#if index == -1:
				#	index = bonusText.find("%")
				#	if index == -1:
				#		index =0
				#if not index  <= 0:
				#	bonusText = bonusText[:index]

				bonusName = ui.TextLine()
				bonusName.AddFlag("not_pick")
				bonusName.SetParent(bonusImage)
				bonusName.SetHorizontalAlignCenter()
				bonusName.SetPosition(72,3)
				bonusName.SetFontName("Tahoma:13")
				bonusName.SetText(bonusText)

				newText = ""
				if bonusName.GetTextSize()[0] > 134:
					for o in range(100):
						if bonusName.GetTextSize()[0] > 134:
							newText = bonusName.GetText()[:len(bonusName.GetText())-2]+"..."
							bonusName.SetText(bonusName.GetText()[:len(bonusName.GetText())-2])
						else:
							break
				
				if newText != "":
					bonusName.SetText(newText)

				bonusName.Show()
				elementList["%d_%d_name"%(i,j)] = bonusName

				bonusValue = ui.TextLine()
				bonusValue.AddFlag("not_pick")
				bonusValue.SetParent(bonusImage)
				bonusValue.SetHorizontalAlignCenter()
				bonusValue.SetPosition(170,3)
				bonusValue.SetFontName("Tahoma:13")
				bonusValue.SetText("0")
				bonusValue.Show()
				elementList["%d_%d_value"%(i,j)] = bonusValue

		self.SetCategory(0)
	
	def OverOutBonus(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def OverInBonus(self, bonusName):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.AppendTextLine(bonusName)
				interface.tooltipItem.ShowToolTip()

	def OnMouseWheel(self, nLen):
		if self.btnIndex == 0:
			if "scrollBar" in self.ElementDictionary:
				scrollBar = self.ElementDictionary["scrollBar"]
				if scrollBar.IsShow():
					if nLen > 0:
						scrollBar.OnUp()
					else:
						scrollBar.OnDown()
					return True
		return False

	def __OnValueUpdate(self):
		elementList = self.ElementDictionary
		itemSearch = elementList["itemSearch"]
		ui.EditLine.OnIMEUpdate(itemSearch)
		bonusWindow = self.GetChild("bonus_window")
		searchText = itemSearch.GetText()
		board = elementList["searchBoard"]
		totalWidth = 129
		if len(searchText) > 0:
			self.ElementDictionary["scrollBar"].SetPos(0, True)
			totalWidth-=25
			windowHeight = bonusWindow.GetWidth()-15
			textSize = itemSearch.GetTextSize()[0]
			if textSize >= totalWidth:
				if textSize >= windowHeight:
					totalWidth = windowHeight
				else:
					totalWidth = textSize
			totalWidth+=25
			if totalWidth >= windowHeight:
				totalWidth = windowHeight
		board.SetSize(totalWidth,23)
		itemSearch.SetSize(totalWidth,23)
		board.SetPosition((bonusWindow.GetWidth()//2)-(board.GetWidth()//2),11)
		searchBtn = elementList["searchBtn"]
		searchBtn.SetPosition(itemSearch.GetWidth()-searchBtn.GetWidth(),2)
		self.Refresh()

	def SetBonusCategory(self, emptyArg, categoryIndex):
		category = self.ElementDictionary["%d_category"%categoryIndex]
		category.buttonStatus = not category.buttonStatus
		if category.buttonStatus == 0:
			self.ElementDictionary["%d_categoryText"%categoryIndex].SetText("|Ikey/plus|i "+bonus_list[categoryIndex][0])
		else:
			self.ElementDictionary["%d_categoryText"%categoryIndex].SetText("|Ikey/negative|i "+bonus_list[categoryIndex][0])
		self.Refresh()

	def Refresh(self):
		elementList = self.ElementDictionary
		(X_POS,Y_POS) = (3,43)
		CATEGORY_Y_RANGE = 25
		CATEGORY_Y_FIRST_BONUS_RANGE = 29
		BONUS_X = 13

		if self.btnIndex == 0:
			bonusWindow = self.GetChild("bonus_window")
			scrollBar = self.GetChild("scrollBar")
			(basePos,windowHeight) = (0,bonusWindow.GetHeight()-46)

			searchText = elementList["itemSearch"].GetText().lower()

			maxHeight = 0
			if len(searchText) > 0:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					for j in range(len(bonus_data)):
						text = elementList["%d_%d_name"%(i,j)].GetText().lower()
						if text.find(searchText) != -1:
						#if len(text) >= len(searchText):
						#	if text[:len(searchText)] == searchText:
							maxHeight += CATEGORY_Y_FIRST_BONUS_RANGE
			else:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					if ("%d_category"%i) in elementList:
						categoryBtn = elementList["%d_category"%i]
						if categoryBtn.buttonStatus == 0:
							maxHeight += CATEGORY_Y_RANGE
						else:
							maxHeight += CATEGORY_Y_FIRST_BONUS_RANGE
							for j in range(len(bonus_data)):
								maxHeight += CATEGORY_Y_FIRST_BONUS_RANGE

			if maxHeight > windowHeight:
				scrollLen = maxHeight-windowHeight
				basePos = int(scrollBar.GetPos()*scrollLen)
				stepSize = 1.0 / (scrollLen/100.0)
				scrollBar.SetScrollStep(stepSize)
				scrollBar.SetMiddleBarSize(float(windowHeight-5)/float(maxHeight))
				scrollBar.Show()
			else:
				scrollBar.Hide()

			textLines = []
			images = []
			_wy = bonusWindow.GetGlobalPosition()[1]+43

			if len(searchText) > 0:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					if ("%d_category"%i) in elementList:
						elementList["%d_category"%i].Hide()
						for j in range(len(bonus_data)):
							text = elementList["%d_%d_name"%(i,j)].GetText().lower()
							if text.find(searchText) != -1:
								elementList["%d_%d_image"%(i,j)].Show()
								elementList["%d_%d_image"%(i,j)].SetPosition(BONUS_X, Y_POS - basePos, True)
								elementList["%d_%d_value"%(i,j)].SetText(str(player.GetStatus(bonus_data[j][1])))
								Y_POS += CATEGORY_Y_FIRST_BONUS_RANGE
								images.append(elementList["%d_%d_image"%(i,j)])
								textLines.append(elementList["%d_%d_name"%(i,j)])
								textLines.append(elementList["%d_%d_value"%(i,j)])
							else:
								elementList["%d_%d_image"%(i,j)].Hide()
			else:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					if ("%d_category"%i) in elementList:
						categoryBtn = elementList["%d_category"%i]
						categoryBtn.SetPosition(X_POS, Y_POS - basePos, True)
						categoryBtn.Show()

						images.append(categoryBtn)
						textLines.append(elementList["%d_categoryText"%i])

						if categoryBtn.buttonStatus == 0:
							Y_POS += CATEGORY_Y_RANGE
							for j in range(len(bonus_data)):
								elementList["%d_%d_image"%(i,j)].Hide()
						else:
							Y_POS += CATEGORY_Y_FIRST_BONUS_RANGE
							for j in range(len(bonus_data)):
								elementList["%d_%d_image"%(i,j)].Show()
								elementList["%d_%d_image"%(i,j)].SetPosition(BONUS_X, Y_POS - basePos, True)
								elementList["%d_%d_value"%(i,j)].SetText(str(player.GetStatus(bonus_data[j][1])))
								Y_POS += CATEGORY_Y_FIRST_BONUS_RANGE

								images.append(elementList["%d_%d_image"%(i,j)])
								textLines.append(elementList["%d_%d_name"%(i,j)])
								textLines.append(elementList["%d_%d_value"%(i,j)])

			for childItem in textLines:
				(_x,_y) = childItem.GetGlobalPosition()
				if _y < _wy:
					if childItem.IsShow():
						childItem.Hide()
				elif _y > (_wy+windowHeight-20):
					if childItem.IsShow():
						childItem.Hide()
				else:
					if not childItem.IsShow():
						childItem.Show()

			for childItem in images:
				childHeight = childItem.GetHeight()
				(_x,_y) = childItem.GetGlobalPosition()
				if _y < _wy:
					childItem.SetRenderingRect(0,ui.calculateRect(childHeight-abs(_y-_wy),childHeight),0,0)
					childItem.Hide()
				elif _y+childHeight > (_wy+windowHeight-4):
					calculate = (_wy+windowHeight-4) - (_y+childHeight)
					if calculate == 0:
						return
					f = ui.calculateRect(childHeight-abs(calculate),childHeight)
					childItem.SetRenderingRect(0,0,0,f)
					childItem.Hide()
				else:
					childItem.SetRenderingRect(0,0,0,0)
					childItem.Show()

		elif self.btnIndex == 1:
			for i in range(len(stat_list)):
				if ("%d_stat"%i) in elementList:
					elementList["%d_stat"%i].SetText(localeInfo.DottedNumber(player.GetKillLOG(stat_list[i][1])))

	#def OnUpdate(self):
	#	self.Refresh()

	def SetCategory(self, categoryIndex):
		self.btnIndex = categoryIndex
		self.__ClickRadioButton([self.GetChild("bonus_button"),self.GetChild("stat_button")],categoryIndex)
		self.ElementDictionary["itemSearch"].KillFocus()
		if self.btnIndex == 0:
			self.GetChild("bonus_window").Show()
			self.GetChild("stat_window").Hide()
		elif self.btnIndex == 1:
			self.GetChild("bonus_window").Hide()
			self.GetChild("stat_window").Show()

		self.Refresh()

	def OnScroll(self):
		pass


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

class SearchSlotBoard(ui.Window):
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
