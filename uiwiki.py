# author: dracaryS
# v3.2 Update Multifunctional Wiki

# static imports
import ui, localeInfo, osfInfo, WikiUI, os

# dynamics imports
import grp, app, wiki, WikiRenderTarget, item, nonplayer, skill, player, chat, dbg

# if false will be textline!
USE_ITEM_COUNT_NUMBER_LINE = False

# if this true item refine showing start index in +0 than +9 will be next item if have!
SHOW_NEXT_ITEM_REFINE = False

SHOW_ITEM_LOWER_TO_BIG = False
# category load speed
AUTOLOAD_SPEED = 0.010
AUTOLOAD_MONSTER_SPEED = 0.020

IMG_DIR = "d:/ymir work/ui/game/wiki/"

class EncyclopediaofGame(ui.BoardWithTitleBar):
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		if "listBoxCube" in self.children:
			self.children["listBoxCube"].ClearItem()
			self.children["listBoxCube"]=None
			del self.children["listBoxCube"]

		if "resultpageListbox" in self.children:
			self.children["resultpageListbox"].RemoveAllItems()
			self.children["resultpageListbox"]=None
			del self.children["resultpageListbox"]

		self.selectArg=""
		self.currentCharacterIdx=-1
		self.AIAppendAlgoritm = None

		if len(self.children) != 0:
			ui.BoardWithTitleBar.Destroy(self)

		self.children = {}

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.SetWindowName("EncyclopediaofGame")
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetCloseEvent(self.Close)
		self.children = {}

		self.Destroy()

		# Default variable
		self.children["characterIndex"]=0
		self.Initialize()

	def Initialize(self):
		self.SetSize(720, 480)
		self.SetTitleName(localeInfo.WIKI_TITLE)
		self.SetCenterPosition()

		self.LoadSearchInfos()
		self.LoadCategoryInfos()
		self.LoadBlock()
		self.LoadResultPage()

	def LoadResultPage(self):
		resultPageImage = WikiUI.CreateWindow(ui.ImageBoxWiki(), self, (150,104), IMG_DIR+"result_wall.tga")
		self.children["resultPageImage"] = resultPageImage

		for j in range(4):
			characterBtn =  WikiUI.CreateWindow(ui.RadioButton(), resultPageImage, (16+(132*j), 11))
			characterBtn.SetEvent(ui.__mem_func__(self.__SelectCharacters),j)
			characterBtn.SetUpVisual(IMG_DIR+"character/%d_0.png"%j)
			characterBtn.SetOverVisual(IMG_DIR+"character/%d_1.png"%j)
			characterBtn.SetDownVisual(IMG_DIR+"character/%d_2.png"%j)
			characterBtn.Hide()
			self.children["job_%d_characterBtn"%j] = characterBtn

		resultpageListbox = WikiUI.ListBoxSpecial()
		resultpageListbox.SetParent(self)
		self.children["resultpageListbox"] = resultpageListbox

		resultpageListboxScrollbar = WikiUI.ScrollBarSpecial()
		resultpageListboxScrollbar.SetParent(resultpageListbox)
		resultpageListbox.SetScrollBar(resultpageListboxScrollbar)

		resultpagebtn = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (150, 32))
		resultpagebtn.SetEvent(ui.__mem_func__(self.LoadGuidePage),"mouse_click")
		self.children["resultpagebtn"] = resultpagebtn

	def LoadGuidePage(self, emptyArg = ""):
		self.__SelectType("system#0", False, False)

	def LoadBlock(self):
		self.children["blockImage"] =  WikiUI.CreateWindow(ui.ImageBoxWiki(), self, (140,32), IMG_DIR+"block.tga")

	def LoadSearchInfos(self):
		self.children["selectedMob"] = 0
		self.children["selectedItem"] = 0

		wikiBg = WikiUI.CreateWindow(ui.ImageBoxWiki(), self, (9, 37), IMG_DIR+"background.png")
		self.children["wikiBg"] = wikiBg

		searchSlot = WikiUI.CreateWindow(ui.ImageBoxWiki(), self, (14, 40), IMG_DIR+"searchfield.png")
		self.children["searchSlot"] = searchSlot

		searchButton = WikiUI.CreateWindow(ui.Button(), self, (112,40))
		searchButton.SetUpVisual(IMG_DIR+"search_btn_s_0.png")
		searchButton.SetOverVisual(IMG_DIR+"search_btn_s_1.png")
		searchButton.SetDownVisual(IMG_DIR+"search_btn_s_2.png")
		searchButton.SAFE_SetEvent(self.StartSearchItem)
		self.children["searchButton"] = searchButton

		searchItemName = WikiUI.CreateWindow(ui.EditLine(), searchSlot, (3,3), "", "", (91,26))
		searchItemName.SetInfoMessage("|cFF727677"+localeInfo.WIKI_ITEM_NAME+"|r")
		searchItemName.SetMax(65)
		searchItemName.isNeedEmpty = False
		searchItemName.OnPressEscapeKey = ui.__mem_func__(self.Close)
		searchItemName.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateItem)
		searchItemName.SetReturnEvent(ui.__mem_func__(self.StartSearchItem))
		searchItemName.SetTabEvent(ui.__mem_func__(self.__ItemEditLineKeyUp))
		self.children["searchItemName"] = searchItemName

		searchClearBtn = WikiUI.CreateWindow(ui.Button(), searchSlot, (83,6))
		searchClearBtn.SetUpVisual(IMG_DIR+"search_btn_x_0.png")
		searchClearBtn.SetOverVisual(IMG_DIR+"search_btn_x_1.png")
		searchClearBtn.SetDownVisual(IMG_DIR+"search_btn_x_2.png")
		searchClearBtn.SAFE_SetEvent(self.ClearEditlineItem)
		searchClearBtn.Hide()
		self.children["searchClearBtn"] = searchClearBtn

		mobSlot = WikiUI.CreateWindow(ui.ImageBoxWiki(), self, (14,40), IMG_DIR+"searchfield.png")
		self.children["mobSlot"] = mobSlot
		mobSlot.Hide()

		searchButtonMob = WikiUI.CreateWindow(ui.Button(), self, (112,40))
		searchButtonMob.SetUpVisual(IMG_DIR+"search_btn_s_0.png")
		searchButtonMob.SetOverVisual(IMG_DIR+"search_btn_s_1.png")
		searchButtonMob.SetDownVisual(IMG_DIR+"search_btn_s_2.png")
		searchButtonMob.SAFE_SetEvent(self.StartSearchMob)
		searchButtonMob.Hide()
		self.children["searchButtonMob"] = searchButtonMob

		searchMobName = WikiUI.CreateWindow(ui.EditLine(), mobSlot, (3,3), "", "", (91,26))
		searchMobName.SetInfoMessage("|cFF727677"+localeInfo.WIKI_MOB_NAME+"|r")
		searchMobName.isNeedEmpty = False
		searchMobName.SetMax(65)
		searchMobName.OnPressEscapeKey = ui.__mem_func__(self.Close)
		searchMobName.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateMob)
		searchMobName.SetReturnEvent(ui.__mem_func__(self.StartSearchMob))
		searchMobName.SetTabEvent(ui.__mem_func__(self.__ItemEditLineKeyUpMob))
		searchMobName.Hide()
		self.children["searchMobName"] = searchMobName

		searchClearBtnMob = WikiUI.CreateWindow(ui.Button(), mobSlot, (83,6))
		searchClearBtnMob.SetUpVisual(IMG_DIR+"search_btn_x_0.png")
		searchClearBtnMob.SetOverVisual(IMG_DIR+"search_btn_x_1.png")
		searchClearBtnMob.SetDownVisual(IMG_DIR+"search_btn_x_2.png")
		searchClearBtnMob.SAFE_SetEvent(self.ClearEditlineMob)
		searchClearBtnMob.Hide()
		self.children["searchClearBtnMob"] = searchClearBtnMob

		searchSwitchButton = WikiUI.CreateWindow(ui.Button(), self, (13,65))
		searchSwitchButton.SetUpVisual(IMG_DIR+"btn_i_0.png")
		searchSwitchButton.SetOverVisual(IMG_DIR+"btn_i_1.png")
		searchSwitchButton.SetDownVisual(IMG_DIR+"btn_i_0.png")
		searchSwitchButton.SAFE_SetEvent(self.ChangeSearchBar)
		self.children["searchSwitchBtn"] = searchSwitchButton

		searchSwitchButton2 = WikiUI.CreateWindow(ui.Button(), self, (13,65))
		searchSwitchButton2.SetUpVisual(IMG_DIR+"btn_m_0.png")
		searchSwitchButton2.SetOverVisual(IMG_DIR+"btn_m_1.png")
		searchSwitchButton2.SetDownVisual(IMG_DIR+"btn_m_0.png")
		searchSwitchButton2.SAFE_SetEvent(self.ChangeSearchBar)

		self.children["searchSwitchBtn2"] = searchSwitchButton2
		self.children["searchSwitchBtn2"].Hide()

		self.children["searchItemNameText"] = WikiUI.CreateWindow(ui.TextLine(), searchSwitchButton, (62, 2), localeInfo.WIKI_MONSTER, "horizontal:center")
		self.children["searchMobNameText"] = WikiUI.CreateWindow(ui.TextLine(), searchSwitchButton2, (62, 2), localeInfo.WIKI_ITEMS, "horizontal:center")
		self.children["searchMobNameText"].Hide()

	def ChangeSearchBar(self):
		if self.children["searchSlot"].IsShow():
			self.children["searchSlot"].Hide()
			self.children["searchItemName"].Hide()
			self.children["mobSlot"].Show()
			self.children["searchButtonMob"].Show()
			self.children["searchMobName"].Show()
			self.children["searchMobNameText"].Show()
			self.children["searchItemNameText"].Hide()
			self.children["searchSwitchBtn"].Hide()
			self.children["searchSwitchBtn2"].Show()

		elif self.children["mobSlot"].IsShow():
			self.children["mobSlot"].Hide()
			self.children["searchButtonMob"].Hide()
			self.children["searchMobName"].Hide()
			self.children["searchSlot"].Show()
			self.children["searchItemName"].Show()
			self.children["searchItemNameText"].Show()
			self.children["searchMobNameText"].Hide()

			self.children["searchSwitchBtn"].Show()
			self.children["searchSwitchBtn2"].Hide()

	def FocusSearchItem(self):
		if self.children.get("mobSlot") and self.children["mobSlot"].IsShow():
			self.ChangeSearchBar()
		if self.children.get("searchItemName"):
			self.children["searchItemName"].SetFocus()

	def LoadCategoryInfos(self):
		self.children["categoryText"] = WikiUI.CreateWindow(ui.TextLine(), self, (13, 89), localeInfo.WIKI_CATEGORY, "horizontal:left")

		listBoxCube = WikiUI.CreateWindow(WikiUI.CategoryList(), self, (13, 105), "", "", (115, 339))
		self.children["listBoxCube"] = listBoxCube

		scrollBarListBoxCube = WikiUI.ScrollBarSpecial()
		scrollBarListBoxCube.SetParent(self)
		scrollBarListBoxCube.SetPosition(listBoxCube.GetLocalPosition()[0]+listBoxCube.GetWidth()+2,listBoxCube.GetLocalPosition()[1]-1)
		scrollBarListBoxCube.Show()
		self.children["scrollBarListBoxCube"] = scrollBarListBoxCube

		listBoxCube.SetScrollBar(scrollBarListBoxCube)
		scrollBarListBoxCube.SetSize(8, listBoxCube.GetHeight())

		self.children["historySearch"] = []
		self.children["currentIndex"] = 0

		historyBack = WikiUI.CreateWindow(ui.Button(), self, (13,105+343))
		historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.png")
		historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_hover.png")
		historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_down.png")
		historyBack.SAFE_SetEvent(self.ClickBackHistory)
		self.children["historyBack"] = historyBack

		historyNext = WikiUI.CreateWindow(ui.Button(), self, (15+historyBack.GetWidth(),105+343))
		historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.png")
		historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_hover.png")
		historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_down.png")
		historyNext.SAFE_SetEvent(self.ClickNextHistory)
		self.children["historyNext"] = historyNext

		categoryDict = WikiUI.GetCategoryDict()
		listBoxCubeItems = []
		for key, data in categoryDict.items():
			newDict = {}
			newDict["item"] = WikiUI.CreateCategoryItem(data["name"] if "name" in data else "Noname", None)
			newDict["children"] = []
			itemDict = data["items"] if "items" in data else {}
			for categoryIdx, categoryName in itemDict.items():
				categoryDict = {}
				categoryDict["item"] = WikiUI.CreateCategorySubItem(categoryName, lambda arg = ("{}#{}".format(data["type"] if "type" in data else "article", categoryIdx)) : self.__SelectType(arg))
				newDict["children"].append(categoryDict)
			listBoxCubeItems.append(newDict)
		self.children["listBoxCube"].AppendItemList(listBoxCubeItems)

	def SetHistoryButtons(self):
		historyBack = self.children["historyBack"]
		historyNext = self.children["historyNext"]

		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]

		if len(historySearch) == 0:
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.png")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_hover.png")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_down.png")
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.png")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_hover.png")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_down.png")
			return

		if currentIndex > 0:
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.png")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_hover.png")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_down.png")
		else:
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.png")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_hover.png")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_down.png")

		if currentIndex+1 >= len(historySearch):
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.png")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_hover.png")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_down.png")
		else:
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.png")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_hover.png")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_down.png")

	def RunHistoryArgument(self, argument):
		if argument.find("NEW") != -1:
			argumentList = argument.split("#")
			self.ShowItemInfo(int(argumentList[1]), int(argumentList[2]), False)
		else:
			self.__SelectType(argument, False, False)

	def ClickBackHistory(self):
		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]
		if currentIndex-1 < 0:
			return
		currentIndex-=1
		self.children["currentIndex"]=currentIndex
		self.RunHistoryArgument(historySearch[currentIndex])
		self.SetHistoryButtons()

	def ClickNextHistory(self):
		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]
		if currentIndex+1 >= len(historySearch):
			return
		currentIndex+=1
		self.children["currentIndex"]=currentIndex
		self.RunHistoryArgument(historySearch[currentIndex])
		self.SetHistoryButtons()

	def get_length(self, x):
		return len(x[0])

	def UpdateItemsList(self, putFullName = False):
		input_text_real = self.children["searchItemName"].GetText()
		input_len = len(input_text_real)

		if input_len == 0:
			self.ClearEditlineItem()
			return False

		if localeInfo.IsARABIC():
			input_text = input_text_real
		else:
			input_text = input_text_real.lower()

		self.children["searchClearBtn"].Show()
		items_list = item.GetItemsByName(str(input_text))
		itemList = []
		namesList = []
		for i, itemVnum in enumerate(items_list, start=1):
			(realVnum, isRefineItem) = WikiUI.getRealVnum(itemVnum)
			if isRefineItem:
				realVnum += wiki.GetRefineMaxLevel(realVnum)
				if itemVnum != realVnum:
					continue

			item.SelectItem(itemVnum)
			itemName = item.GetItemName() if localeInfo.IsARABIC() else item.GetItemName().lower()

			if itemName.find("+") != -1:
				itemName = itemName[:itemName.find("+")]

			tempName = list(itemName)
			for i in range(input_len):
				tempName[i]=list(input_text_real)[i]

			if not putFullName:
				itemName = ""
				for x in range(len(tempName)):
					if x >= input_len:
						continue
					itemName+= tempName[x]

				for x in range(len(tempName)):
					if x < input_len:
						continue
					itemName+= "{}{}{}".format("|cFF727677",tempName[x],"|r")

			if itemName in namesList:
				continue
			namesList.append(itemName)
			itemList.append([itemName, realVnum])
		if len(itemList) > 0:
			if len(itemList) > 1:
				itemList = sorted(itemList, key=self.get_length,reverse=False)
			self.children["selectedItem"] = itemList[0][1]
			self.children["searchItemName"].SetInfoMessage(itemList[0][0])
			if putFullName:
				self.ResetEditline2(self.children["searchItemName"], itemList[0][0])
		else:
			self.children["selectedItem"] = 0
			self.children["searchItemName"].SetInfoMessage("")
		return True

	def ResetEditline2(self, editLine, text):
		editLine.SetFocus()
		editLine.SetText(text)
		# editLine.SetInfoMessage("")
		editLine.OnIMEUpdate()
		editLine.KillFocus()
		editLine.SetFocus()

	def __OnValueUpdateItem(self):
		ui.EditLine.OnIMEUpdate(self.children["searchItemName"])
		if not self.UpdateItemsList():
			self.ClearEditlineItem()

		def OnKeyDown(self, key):
			if app.DIK_RETURN == key:
				self.StartSearchItem()
				return True
			return True

	def ClearEditlineItem(self):
		self.children["selectedItem"]=0
		self.children["searchItemName"].SetText("")
		self.children["searchItemName"].SetInfoMessage("|cFF727677"+localeInfo.WIKI_ITEM_NAME+"|r")
		self.children["searchClearBtn"].Hide()

	def StartSearchItem(self):
		if self.children["selectedItem"] != 0:
			self.ShowItemInfo(self.children["selectedItem"],0)

	def __ItemEditLineKeyUp(self):
		self.UpdateItemsList(True)

	def __ItemEditLineKeyUpMob(self):
		self.UpdateMobsList(True)

	def UpdateMobsList(self, putFullName = False):
		input_text_real = self.children["searchMobName"].GetText()
		input_len = len(input_text_real)

		if input_len == 0:
			self.ClearEditlineMob()
			return False

		input_text = input_text_real if localeInfo.IsARABIC() else input_text_real.lower()

		self.children["searchClearBtnMob"].Show()
		mobs_list = nonplayer.GetMobsByName(str(input_text))
		mobList = []
		namesList = []
		for i, mobVnum in enumerate(mobs_list, start=1):
			if localeInfo.IsARABIC():
				mob_name = nonplayer.GetMonsterName(mobVnum)
			else:
				mob_name = nonplayer.GetMonsterName(mobVnum).lower()

			tempName = list(mob_name)
			for i in range(input_len):
				tempName[i]=list(input_text_real)[i]

			if not putFullName:
				mob_name = ""
				for x in range(len(tempName)):
					if x >= input_len:
						continue
					mob_name+= tempName[x]

				for x in range(len(tempName)):
					if x < input_len:
						continue
					mob_name+= "{}{}{}".format("|cFF727677",tempName[x],"|r")

			if mob_name in namesList:
				continue

			namesList.append(mob_name)
			mobList.append([mob_name, mobVnum])
		if len(mobList) > 0:
			if len(mobList) > 1:
				mobList = sorted(mobList, key=self.get_length,reverse=False)
			if putFullName:
				self.ResetEditline2(self.children["searchMobName"], mobList[0][0])
			self.children["selectedMob"] = mobList[0][1]
			self.children["searchMobName"].SetInfoMessage(mobList[0][0])
		else:
			self.children["selectedMob"] = 0
			self.children["searchMobName"].SetInfoMessage("")
		return True

	def __OnValueUpdateMob(self):
		ui.EditLine.OnIMEUpdate(self.children["searchMobName"])
		if not self.UpdateMobsList():
			self.ClearEditlineMob()
		def OnKeyDown(self, key):
			if app.DIK_RETURN == key:
				self.StartSearchMob()
				return True
			return True

	def ClearEditlineMob(self):
		self.children["selectedMob"]=0
		self.children["searchMobName"].SetText("")
		self.children["searchMobName"].SetInfoMessage("|cFF727677"+localeInfo.WIKI_MOB_NAME+"|r")
		self.children["searchClearBtnMob"].Hide()

	def StartSearchMob(self):
		if self.children["selectedMob"] != 0:
			self.ShowItemInfo(self.children["selectedMob"],1)

	def LoadData(self, arg):
		self.__SelectType(arg)

	def __SelectCharacters(self, buttonIndex):
		WikiUI.ClickRadioButton([self.children["job_%d_characterBtn"%j] for j in range(4)], buttonIndex)
		self.children["characterIndex"]=buttonIndex
		self.__SelectType(self.selectArg, True)

	def SetCharacterImagesStatus(self, showStatus):
		btnList = [self.children["job_%d_characterBtn"%j] for j in range(4)]
		for btn in btnList:
			if showStatus:
				btn.Show()
			else:
				btn.Hide()
		if showStatus:
			WikiUI.ClickRadioButton(btnList, self.children["characterIndex"])

	def ClearResultListbox(self, argList, isSingleItem = False):
		self.AIAppendAlgoritm = None

		try:
			resultpageListbox = self.children["resultpageListbox"]
			resultpageListbox.RemoveAllItems()
			resultpageListbox.Render(0)
			resultpageListbox.Show()

			if len(argList) == 0:
				return

			imageFile = WikiUI.GetResultPageImage(argList)
			if imageFile:
				self.children["resultpagebtn"].LoadImage(imageFile)
				self.children["resultpagebtn"].Show()

			isEquipmentPage = True if WikiUI.IsCategory(argList[0], "equipment") and isSingleItem == False else False

			self.SetCharacterImagesStatus(isEquipmentPage)
			resultpageListbox.SetPosition(152, 162 if isEquipmentPage else 105)
			resultpageListbox.SetSize(555, 297 if isEquipmentPage else 375 if WikiUI.IsCategory(argList[0], "article") else 360)

			resultpageListboxScrollbar = self.children["resultpageListbox"].scrollBar
			if resultpageListboxScrollbar:
				resultpageListboxScrollbar.SetPosition(resultpageListbox.GetWidth()-9, 1)
				resultpageListboxScrollbar.SetSize(8, resultpageListbox.GetHeight())
		except:
			dbg.TraceError("Wiki-Debug: Something is wrong in clear result listbox method.")

	def __SelectType(self, arg, isCharacterBtn=False, isHistory=True):
		import traceback
		try:
			self.selectArg = arg
			self.currentCharacterIdx = self.children["characterIndex"]

			if isHistory:
				self.children["historySearch"].append(arg)
				self.children["currentIndex"] = len(self.children["historySearch"]) - 1
				self.SetHistoryButtons()

			argList = arg.split("#")
			self.ClearResultListbox(argList)

			if WikiUI.IsArticleCategory(argList):
				resultpageListbox = self.children["resultpageListbox"]
				event_item = ArticleGUI(argList[1] + "#" + argList[2] if len(argList) == 3 else int(argList[1]))
				resultpageListbox.AppendItem(event_item)
				event_item.LoadItemInfos()
				if resultpageListbox.scrollBar:
					resultpageListbox.scrollBar.Hide()
			else:
				AIAppendAlgoritm = WikiUI.AutoLoad()
				(loadSpeed, maxSize, itemType) = (AUTOLOAD_SPEED, -1, int(argList[1]))

				categoryType = argList[0].lower() if not localeInfo.IsARABIC() else argList[0]
				if categoryType == "equipment":
					maxSize = wiki.GetCategorySize(self.children["characterIndex"], int(argList[1]))
					AIAppendAlgoritm.SetFlag("characterIndex", self.children["characterIndex"])
				else:
					_methodFunc = {
						"costume": wiki.GetCostumeSize,
						"chests": wiki.GetChestSize,
						"bosses": wiki.GetBossSize,
						"monster": wiki.GetMonsterSize,
						"metinstone": wiki.GetStoneSize,
						"cube": wiki.GetCubeSize,
					}
					maxSize = _methodFunc[categoryType](int(argList[1]))
					if categoryType == "monster":
						loadSpeed = AUTOLOAD_MONSTER_SPEED

				if maxSize <= 0:
					return

				AIAppendAlgoritm.SetFlag("maxSize", maxSize - 1)
				AIAppendAlgoritm.SetFlag("loadTime", loadSpeed)
				AIAppendAlgoritm.SetFlag("loadType", argList[0])
				AIAppendAlgoritm.SetFlag("itemType", itemType)

				useWikiImprovements = getattr(app, "WIKI_IMPROVEMENTS", 1)
				lastListIndex = max(0, maxSize - 1)
				AIAppendAlgoritm.SetFlag("{}_renderLoadedCount".format(categoryType), min(4, lastListIndex))

				self.AIAppendAlgoritm = AIAppendAlgoritm

		except Exception as e:
			import sys
			import traceback
			exc_type, exc_value, exc_traceback = sys.exc_info()
			dbg.TraceError("Wiki-Debug: Exception occurred in __SelectType: %s" % str(e))
			traceback.print_exception(exc_type, exc_value, exc_traceback)

	def GetHyperlinkData(self):
		hyperlink = ""
		historyLen = len(self.children["historySearch"])
		if historyLen:
			currendCommand = self.children["historySearch"][ historyLen - 1]
			hyperlink = "|cffffc700|Hwiki:"+currendCommand+"|h<Wiki Link>|h|r"
			currendCommandList = currendCommand.split("#")
			return hyperlink

	def ShowItemInfo(self, selectedVnum, argumentIndex, isHistory=True):
		import traceback
		self.children["listBoxCube"].Reset()
		try:
			if isHistory:
				self.children["historySearch"].append("NEW#{}#{}".format(selectedVnum, argumentIndex))
				self.children["currentIndex"] = len(self.children["historySearch"]) - 1
				self.SetHistoryButtons()

			resultpageListbox = self.children["resultpageListbox"]

			if argumentIndex == 0:
				self.ClearResultListbox("equipment#0".split("#"), True)
				selectedVnum, isRefineItem = WikiUI.getRealVnum(selectedVnum)
				if isRefineItem:
					selectedVnum += wiki.GetRefineMaxLevel(selectedVnum)
					resultpageListbox.AppendItem(EquipmentItem(99, selectedVnum, True))

				item.SelectItem(selectedVnum)
				if item.GetItemType() == item.ITEM_TYPE_GIFTBOX:
					resultpageListbox.AppendItem(MonsterItemSpecial(selectedVnum, 3, True))
					resultpageListbox.AppendItem(MonsterStatics(selectedVnum, 3, True))
				else:
					resultpageListbox.AppendItem(MonsterItemSpecial(selectedVnum, 1, True))

			elif argumentIndex == 1:
				self.ClearResultListbox("monster#0".split("#"), True)
				resultpageListbox.AppendItem(MonsterItemSpecial(selectedVnum, 0, True))
				resultpageListbox.AppendItem(MonsterStatics(selectedVnum, 0, True))

			elif argumentIndex == 3:
				self.__SelectType(selectedVnum)

		except Exception as e:
			dbg.TraceError("Wiki-Debug: Exception in ShowItemInfo: %s" % str(e))
			for line in traceback.format_exc().splitlines():
				dbg.TraceError(line)

	def OnUpdate(self):
		self.CheckLoadProcess()

	def CheckLoadProcess(self):
		import traceback
		try:
			__ai = self.AIAppendAlgoritm
			if __ai != None:
				if __ai.GetFlag("nexTime") > app.GetTime():
					return
				__ai.SetFlag("nexTime", app.GetTime() + __ai.GetFlag("loadTime"))
				(loadType, listIndex) = (__ai.GetFlag("loadType"), __ai.GetFlag("maxSize"))
				useWikiImprovements = getattr(app, "WIKI_IMPROVEMENTS", 1)

				if WikiUI.IsCategory(loadType, "equipment"):
					equipItemPointer = EquipmentItem(
						listIndex,
						wiki.GetCategoryData(__ai.GetFlag("characterIndex"), __ai.GetFlag("itemType"), listIndex),
						True
					)
					equipItemPointer.sortIndex = listIndex
					self.children["resultpageListbox"].AppendItem(equipItemPointer, False)

				elif WikiUI.IsCategory(loadType, "costume"):
					createNewWindow = True
					ListBoxItems = self.children["resultpageListbox"].itemList
					if len(ListBoxItems) > 0:
						lastItem = ListBoxItems[-1]
						if lastItem.CanAddNewItem():
							lastItem.LoadItemInfos(wiki.GetCostumeData(__ai.GetFlag("itemType"), listIndex))
							createNewWindow = False
					if createNewWindow:
						equipItemPointer = SpecialClass(listIndex, 0)
						equipItemPointer.LoadItemInfos(wiki.GetCostumeData(__ai.GetFlag("itemType"), listIndex))
						equipItemPointer.sortIndex = listIndex
						self.children["resultpageListbox"].AppendItem(equipItemPointer, False)

				elif WikiUI.IsCategory(loadType, "chests"):
					itemVnum, bossVnum = wiki.GetChestData(__ai.GetFlag("itemType"), listIndex)
					if itemVnum == 0:
						return
					equipItemPointer = ListBoxItemSpecial(listIndex, itemVnum, bossVnum, 0, True)
					equipItemPointer.sortIndex = listIndex
					self.children["resultpageListbox"].AppendItem(equipItemPointer, False)

				elif WikiUI.IsCategory(loadType, "monster"):
					mobVnum = wiki.GetMonsterData(__ai.GetFlag("itemType"), listIndex)
					if mobVnum == 0:
						return
					if useWikiImprovements:
						renderLoadedCount = __ai.GetFlag("monster_renderLoadedCount")
						loadRender = True if listIndex == renderLoadedCount else False
						equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True, loadRender)
						if loadRender:
							__ai.SetFlag("monster_renderLoadedCount", renderLoadedCount - 1)
					else:
						equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True)
					equipItemPointer.sortIndex = listIndex
					self.children["resultpageListbox"].AppendItem(equipItemPointer, False)

				elif WikiUI.IsCategory(loadType, "bosses"):
					mobVnum = wiki.GetBossData(__ai.GetFlag("itemType"), listIndex)
					if mobVnum == 0:
						return
					if useWikiImprovements:
						renderLoadedCount = __ai.GetFlag("bosses_renderLoadedCount")
						loadRender = True if listIndex == renderLoadedCount else False
						equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True, loadRender)
						if loadRender:
							__ai.SetFlag("bosses_renderLoadedCount", renderLoadedCount - 1)
					else:
						equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True)
					equipItemPointer.sortIndex = listIndex
					self.children["resultpageListbox"].AppendItem(equipItemPointer, False)

				elif WikiUI.IsCategory(loadType, "metinstone"):
					mobVnum = wiki.GetStoneData(__ai.GetFlag("itemType"), listIndex)
					if mobVnum == 0:
						return
					if useWikiImprovements:
						renderLoadedCount = __ai.GetFlag("metinstone_renderLoadedCount")
						loadRender = True if listIndex == renderLoadedCount else False
						equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True, loadRender)
						if loadRender:
							__ai.SetFlag("metinstone_renderLoadedCount", renderLoadedCount - 1)
					else:
						equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True)
					equipItemPointer.sortIndex = listIndex
					self.children["resultpageListbox"].AppendItem(equipItemPointer, False)

				elif WikiUI.IsCategory(loadType, "cube"):
					cubeData = wiki.GetCubeData(__ai.GetFlag("itemType"), listIndex)
					if cubeData == 0:
						return
					equipItemPointer = ListBoxCubeItem(listIndex, *cubeData)
					equipItemPointer.sortIndex = listIndex
					self.children["resultpageListbox"].AppendItem(equipItemPointer, False)

				self.SetPositionToSort(self.children["resultpageListbox"], loadType)
				__ai.SetFlag("maxSize", listIndex - 1)
				if listIndex - 1 < 0:
					self.AIAppendAlgoritm = None
					self.children["resultpageListbox"].CalculateScroll()

		except Exception as e:
			dbg.TraceError("Wiki-Debug: Exception in CheckLoadProcess: %s" % str(e))
			for line in traceback.format_exc().splitlines():
				dbg.TraceError(line)

	def get_key(self, data):
		return data.sortIndex

	def SetPositionToSort(self, listBox, loadType):
		(itemList, _y) = (listBox.itemList, 0)
		reverseMethod = True if WikiUI.IsCategory(loadType, "costume") else SHOW_ITEM_LOWER_TO_BIG
		if len(itemList) > 1:
			itemList = sorted(itemList, key=self.get_key,reverse=reverseMethod)
		for child in itemList:
			child.SetPosition(0, _y, True)
			_y += child.GetHeight()

	def SetWindowStatus(self, bShowStatus):
		if "resultpageListbox" in self.children:
			resultpageListbox = self.children["resultpageListbox"].itemList
			for child in resultpageListbox:
				renderIndex = child._children["renderIndex"] if "renderIndex" in child._children else -1
				if renderIndex != -1:
					WikiRenderTarget.SetVisibility(renderIndex, bShowStatus)

		__ai = self.AIAppendAlgoritm
		if __ai != None:
			__ai.SetFlag("nexTime",app.GetTime()+(0.15 if bShowStatus else 999999))

	def Open(self):
		self.SetWindowStatus(True)
		self.Show()
		self.SetTop()

	def Close(self):
		if self.children["searchItemName"]:
			self.children["searchItemName"].KillFocus()
		if self.children["searchMobName"]:
			self.children["searchMobName"].KillFocus()

		self.SetWindowStatus(False)
		self.Hide()

	def OnPressExitKey(self):
		self.Close()
		return TRUE
	def OnPressEscapeKey(self):
		self.Close()
		return TRUE

class ListBoxCubeItem(WikiUI.DefaultWikiImage):
	def __init__(self, listIndex, *cubeData):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["listIndex"] = listIndex

		self._children["reward"] = int(cubeData[0])
		self._children["gold"] = int(cubeData[1])
		self._children["gem"] = int(cubeData[2])
		self._children["mobIdx"] = int(cubeData[3])

		materialList = []
		for j in range(10):
			materialList.append([int(cubeData[4 + (j * 2)]),  int(cubeData[5 + (j * 2)])])

		self._children["materials"] = materialList
		self.LoadImage(IMG_DIR+"slot/detail_craft.tga")
		self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True

			(itemVnum, gold, gem, mobIdx, materials) = (self._children["reward"], self._children["gold"], self._children["gem"], self._children["mobIdx"], self._children["materials"])

			item.SelectItem(itemVnum)

			setItemName = localeInfo.WIKI_CUBE_INFO % item.GetItemName()
			if WikiUI.IsGameMaster():
				setItemName += " - ItemIdx {}".format(itemVnum)

			self._children["itemName"] = WikiUI.CreateWindow(ui.TextLine(), self, (230, 5), setItemName, "horizontal:center")
			self._children["origin"] = WikiUI.CreateWindow(ui.TextLine(), self, (480, 5), localeInfo.WIKI_ORIGIN)
			self._children["cost"] = WikiUI.CreateWindow(ui.TextLine(), self, (410, 5), localeInfo.WIKI_COST)

			originName = nonplayer.GetMonsterName(mobIdx)
			bossVnum = WikiUI.CreateWindow(ui.TextLine(), self, (271, 40), "", "", (90, 66))
			# bossVnum.SetTextRange(13)
			bossVnum.SetAllAlign()

			bossVnum.SetText(originName[:15] + "..." if len(originName) > 18 else originName)

			self._children["bossVnum"] = bossVnum

			itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (10, (self.GetHeight()//2) - ((item.GetItemSize()[1]*32) // 2)), item.GetIconImageFileName())
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, itemVnum)
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
			itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
			self._children["itemIcon"] = itemIcon

			self._children["goldText"] = WikiUI.CreateWindow(ui.TextLine(), self, (420, 40), "|Ikey/mini_coin|i "+WikiUI.price_to_k(gold), "horizontal:center")
			self._children["gemText"] = WikiUI.CreateWindow(ui.TextLine(), self, (420, 57), "|Ikey/mini_gem|i "+WikiUI.price_to_k(gem), "horizontal:center")

			Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (48, 22), "", "", (344, 65))
			gridCalculate = WikiUI.Grid(width = 12, height = 50)
			for j in range(10):
				(vnum, count) = materials[j]
				if vnum == 0 or count == 0:
					continue
				item.SelectItem(vnum)
				(width, height) = item.GetItemSize()
				if width == 0 or height == 0:
					continue
				pos = gridCalculate.find_blank(width, height)
				gridCalculate.put(pos, width, height)
				(x, y) = WikiUI.calculatePos(pos, 11)

				item_new = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), Listbox, (x, y, True), item.GetIconImageFileName())
				item_new.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,vnum)
				item_new.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				item_new.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,vnum)
				Listbox.AppendItem(item_new)
				if count>1:
					Listbox.AppendItem(WikiUI.CreateWindow(ui.NumberLine() if USE_ITEM_COUNT_NUMBER_LINE else ui.TextLine(), Listbox, (x+15,y+item_new.GetHeight()-10,True) if USE_ITEM_COUNT_NUMBER_LINE else (x+5,y+item_new.GetHeight()-10,True), (localeInfo.MoneyFormat(str(count)).replace(".000","k")), "horizontal:left"))
			if Listbox.isNeedScrollBar():
				Listbox.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (385, 23), "", "", (8, 63)))
			self._children["Listbox"] = Listbox
			self.Show()


class EquipmentItem(WikiUI.DefaultWikiImage):

	class RefineItem(WikiUI.DefaultWikiWindow):
		def LoadData(self, refine, itemVnum, refineCount, refineData):
			tooltipImage = WikiUI.CreateWindow(ui.ImageBoxWiki(), self, (0, 0), "", "",(45, 19))
			tooltipImage.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, (itemVnum-wiki.GetRefineMaxLevel(itemVnum))+refine)
			tooltipImage.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
			tooltipImage.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
			self._children["tooltipImage"] = tooltipImage

			self._children["step_refine"] = WikiUI.CreateWindow(ui.TextLine(), self, (21, 5), "+{}".format(refine), "horizontal:center")
			self._children["step_refine"].AddFlag("not_pick")

			self._children["step_price"] = WikiUI.CreateWindow(ui.TextLine(), self, (21, [140, 140, 140, 180, 230, 275][refineCount]-21), (localeInfo.MoneyFormat(refineData["cost"]).replace(".000","k") if "cost" in refineData else "0") if SHOW_NEXT_ITEM_REFINE or refine else "-", "horizontal:center")

			for i in range(refineCount):
				materialItem = refineData["item"][i] if "item" in refineData else 0
				needInsertIcon = materialItem != 0
				if needInsertIcon == True and SHOW_NEXT_ITEM_REFINE == False and refine == 0:
					needInsertIcon = False
				if needInsertIcon:
					item.SelectItem(materialItem)
					refineItemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (5, 20+5+(i*(32+5+10))), item.GetIconImageFileName())
					refineItemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, materialItem)
					refineItemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					refineItemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click", 0, materialItem)
					self._children["refineItemIcon{}".format(i)] = refineItemIcon
					materialItemCount = refineData["count"][i] if "count" in refineData else 0
					if materialItemCount > 0:
						self._children["refineItemCount{}".format(i)] = WikiUI.CreateWindow(ui.NumberLine() if USE_ITEM_COUNT_NUMBER_LINE else ui.TextLine(), self, (5, 20+5+(i*(32+5+10))+(32 if USE_ITEM_COUNT_NUMBER_LINE else 20)), str(materialItemCount), "horizontal:left")
				else:
					self._children["emptyRefine{}".format(i)] = WikiUI.CreateWindow(ui.TextLine(), self, (self.GetWidth()//2, 21+18+(i*44)), "-")

	def __init__(self, listIndex, itemVnum, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["itemVnum"] = itemVnum
		self._children["refineItems"] = {}
		self._children["refineCount"] = 2
		self._children["refineLevel"] = wiki.GetRefineMaxLevel(itemVnum)
		self.overLine = False

		for j in range(self._children["refineLevel"]+1):
			if item.SelectItemWiki((itemVnum-self._children["refineLevel"])+j) == 1:
				argv = wiki.GetRefineItems(item.GetRefineSet())
				if argv != 0:
					self.InsertRefine(j, *argv)

		self.LoadImage(IMG_DIR+"slot/slot_{}.png".format(self._children["refineCount"]))

		if self._children["refineLevel"] >= 11:
			self.SetSize(self.GetWidth()+10, self.GetHeight()+10)

		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True
			(itemVnum, refineLevel, refineCount, listIndex, refineItems) = (self._children["itemVnum"], self._children["refineLevel"], self._children["refineCount"], self._children["listIndex"], self._children["refineItems"])
			(firstLevel, secondLevel) = WikiUI.FindItemLevelRange(itemVnum, refineLevel)

			itemName = item.GetItemName()
			self._children["itemName"] = WikiUI.CreateWindow(ui.TextLine(), self, (5, 5), itemName[:itemName.find("+")] if itemName.find("+") != -1 else itemName)
			self._children["itemLevel"] = WikiUI.CreateWindow(ui.TextLine(), self, (355, 5), (localeInfo.WIKI_LEVEL_TEXT2%(firstLevel, secondLevel, 0, refineLevel)) if secondLevel != firstLevel else (localeInfo.WIKI_LEVEL_TEXT%(firstLevel, 0, refineLevel)))

			itemLevelCoordinates = [ [0,0],[0,0],[10,55],[10,70],[10,80],[10,115]]
			itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (itemLevelCoordinates[refineCount][0], itemLevelCoordinates[refineCount][1]),  item.GetIconImageFileName() if item.GetIconImageFileName().find("gr2") == -1 else "icon/item/27995.tga")
			if listIndex == 99:
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, itemVnum-refineLevel)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0)
			else:
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, itemVnum)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0)
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
			self._children["itemIcon"] = itemIcon

			self._children["upgradeItem"] = WikiUI.CreateWindow(ui.TextLine(), self, (50, 24), localeInfo.WIKI_UPGRADE_COSTS)
			self._children["yangCost"] = WikiUI.CreateWindow(ui.TextLine(), self, (58,  [140, 140, 140, 180, 230, 275][refineCount]), localeInfo.WIKI_YANG_COSTS)

			refinedVnum = item.GetRefinedVnum()
			if refinedVnum != 0:
				item.SelectItem(refinedVnum)

				nextItemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (75, itemLevelCoordinates[refineCount][1]), item.GetIconImageFileName() if item.GetIconImageFileName().find("gr2") == -1 else "icon/item/27995.tga")
				nextItemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,refinedVnum)
				nextItemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				nextItemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",refinedVnum)
				self._children["upgradeItem"] = nextItemIcon

			listboxSizes = [ [0,0], [0,0], [411,136], [411,180], [411,228], [411,276] ]

			Listbox = WikiUI.CreateWindow(WikiUI.ListBoxEx(True), self, (130, 20), "", "", (listboxSizes[refineCount][0], listboxSizes[refineCount][1]))
			Listbox.SetItemStep(41)
			Listbox.SetItemSize(45, listboxSizes[refineCount][1])
			Listbox.SetViewItemCount(10)

			if refineLevel > 10:
				scrollbar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(True), self, (0, [156, 156, 156, 200, 255, 296][refineCount]), "", "", (540, 8))
				scrollbar.SetScale(540, 540+((refineLevel-10) * 45))
				Listbox.SetScrollBar(scrollbar)

			for i in range(refineLevel+1):
				refine_data = self.RefineItem()
				Listbox.AppendItem(refine_data)
				refine_data.LoadData(i, itemVnum, refineCount, refineItems[i if SHOW_NEXT_ITEM_REFINE or i == 0 else i-1] if (i if SHOW_NEXT_ITEM_REFINE or i == 0 else i-1) in refineItems else {})

			Listbox.SetBasePos(0)
			Listbox.Show()
			self._children["Listbox"] = Listbox
			self.Show()

	def OnClickItem(self, arg, itemVnum = 0):
		self.OverOutItem()

		parent = osfInfo.GetWikiInterface()
		if parent != None:
			parent.ShowItemInfo(itemVnum+wiki.GetRefineMaxLevel(itemVnum) if itemVnum != 0 else self._children["itemVnum"], 0)

	def InsertRefine(self, refineIndex, *refineData):
		refineMaterialCount = 5
		(refineItems, refineCount) = (self._children["refineItems"], self._children["refineCount"])
		refineItems[refineIndex] = {
			#"id" : int(refineData[0]), # unused
			"item" : [int(refineData[1+(j * 2)]) for j in range(refineMaterialCount)],
			"count" : [int(refineData[2+(j * 2)]) for j in range(refineMaterialCount)],
			"cost" : int(refineData[(refineMaterialCount * 2) + 1]),
			"prob" : int(refineData[(refineMaterialCount * 2) + 2]),
			#"refine_count" : int(refineData[(refineMaterialCount * 2) + 3]), #unused
		}
		if int(refineData[(refineMaterialCount * 2) + 3]) > refineCount:
			refineCount = int(refineData[(refineMaterialCount * 2) + 3])
		(self._children["refineItems"], self._children["refineCount"]) = (refineItems, refineCount)

class MonsterItemSpecial(WikiUI.DefaultWikiImage):

	def Destroy(self):
		if "renderIndex" in self._children:
			WikiRenderTarget.SetVisibility(self._children["renderIndex"], False)
			WikiRenderTarget.ResetModel(self._children["renderIndex"])
		WikiUI.DefaultWikiImage.Destroy(self)

	def __init__(self, selectedVnum, isType, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["selectedVnum"] = selectedVnum
		self._children["isType"] = isType
		self.LoadImage(IMG_DIR+"slot/header.png")
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded = True

			renderIndex = WikiRenderTarget.GetFreeIndex(86, 1000000)
			self._children["renderIndex"] = renderIndex
			(isType, selectedVnum) = (self._children["isType"],self._children["selectedVnum"])

			Listbox = None

			if isType == 0 or isType == 3:
				if isType == 0:
					renterTarget = WikiUI.CreateWindow(ui.WikiRenderTargetUi(), self, (1, 1), "", "", (187, 163))
					renterTarget.SetRenderTarget(renderIndex)
					WikiRenderTarget.SetRotation(renderIndex, False)
					self._children["renterTarget"] = renterTarget

					WikiRenderTarget.SelectModel(renderIndex, selectedVnum)
					WikiRenderTarget.SetVisibility(renderIndex, True)

				elif isType == 3:
					item.SelectItem(selectedVnum)

					itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (70, 45), item.GetIconImageFileName())
					itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, selectedVnum)
					itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0, selectedVnum)
					self._children["itemIcon"] = itemIcon

				Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (190, 25), "", "", (350, 138))
				self._children["Listbox"] = Listbox

				self._children["dropList"] = WikiUI.CreateWindow(ui.TextLine(), self, (300, 6), localeInfo.WIKI_DROPLIST_INFO % nonplayer.GetMonsterName(selectedVnum) if isType == 0 else localeInfo.WIKI_CONTENT_INFO % item.GetItemName())
				self._children["monsterInfo"] = WikiUI.CreateWindow(ui.TextLine(), self, (245, 170), localeInfo.WIKI_STATICS_INFO % nonplayer.GetMonsterName(selectedVnum) if isType == 0 else localeInfo.WIKI_AVAIBLE_AT, "horizontal:center")

				grid = WikiUI.Grid(width = 10, height = 50)

				itemLen = (wiki.GetMobInfoSize if isType == 0 else wiki.GetSpecialInfoSize)(selectedVnum)
				getFunc = wiki.GetMobInfoData if isType == 0 else wiki.GetSpecialInfoData


				for j in range(itemLen):
					(vnum, count) = getFunc(selectedVnum, j)
					if vnum == 0:
						continue

					item.SelectItem(vnum)

					pos = grid.find_blank(*item.GetItemSize())
					if not len(item.GetItemName()) or pos == -1:
						continue

					grid.put(pos, *item.GetItemSize())

					(x, y) = WikiUI.calculatePos(pos, 9)

					item_new = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), Listbox, (x, y, True), item.GetIconImageFileName())
					item_new.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, vnum)
					item_new.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					item_new.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0, vnum)
					Listbox.AppendItem(item_new)

					if count>1:
						itemNumberline = WikiUI.CreateWindow(ui.TextLine(), Listbox, (x+item_new.GetWidth()-5,y+item_new.GetHeight()-10, True), (localeInfo.MoneyFormat(str(count)).replace(".000","k")), "horizontal:right")
						Listbox.AppendItem(itemNumberline)

				if Listbox.isNeedScrollBar():
					scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), Listbox, (Listbox.GetWidth()-13, -1), "", "", (8, 137))
					Listbox.SetScrollBar(scrollBar)
			else:

				item.SelectItem(selectedVnum)

				if WikiUI.IsCanModelPreview(selectedVnum):
					renterTarget = WikiUI.CreateWindow(ui.WikiRenderTargetUi(), self, (1, 1), "", "", (187, 163))
					renterTarget.SetRenderTarget(renderIndex)
					WikiRenderTarget.SetRotation(renderIndex, False)
					self._children["renterTarget"] = renterTarget
					WikiUI.SetItemToModelPreview(renderIndex, selectedVnum)

				itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (renterTarget.GetWidth()-33-3,3) if WikiUI.IsCanModelPreview(selectedVnum) else (70, 45), item.GetIconImageFileName())
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, selectedVnum)
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0, selectedVnum)
				self._children["itemIcon"] = itemIcon

				self._children["avaible"] = WikiUI.CreateWindow(ui.TextLine(), self, (350, 6), localeInfo.WIKI_AVAIBLE_AT)

				Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (190, 25), "", "", (350, 138))
				self._children["Listbox"] = Listbox

				WikiUI.PrintDrop(selectedVnum, self, Listbox)

				if Listbox.isNeedScrollBar():
					scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), Listbox, (Listbox.GetWidth()-13, -1), "", "", (8, 137))
					Listbox.SetScrollBar(scrollBar)

			if Listbox != None:
				if len(Listbox.itemList) > 0:
					Listbox.SetBasePos(0, False)
			self.Show()

class MonsterStatics(WikiUI.DefaultWikiImage):
	def __init__(self, mobVnum, isType, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["mobVnum"] = mobVnum
		self._children["isType"] = isType
		self.LoadImage(IMG_DIR+"slot/subheader.png")
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True
			ListBox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (0, 0), "", "", (self.GetWidth(), self.GetHeight()-3))
			self._children["ListBox"] = ListBox
			(mobVnum, isType) = (self._children["mobVnum"], self._children["isType"])
			if isType == 3:
				WikiUI.PrintDrop(mobVnum, self, ListBox)
			elif isType == 0:
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3, True), "|Ikey/plus|i "+localeInfo.WIKI_LEVEL_MOB_TEXT%nonplayer.GetMonsterLevel(mobVnum)))
				RACE_FLAG_TO_NAME = {
					1 << 0  : localeInfo.TARGET_INFO_RACE_ANIMAL,
					1 << 1 	: localeInfo.TARGET_INFO_RACE_UNDEAD,
					1 << 2  : localeInfo.TARGET_INFO_RACE_DEVIL,
					1 << 3  : localeInfo.TARGET_INFO_RACE_HUMAN,
					1 << 4  : localeInfo.TARGET_INFO_RACE_ORC,
					1 << 5  : localeInfo.TARGET_INFO_RACE_MILGYO,
				}
				SUB_RACE_FLAG_TO_NAME = {
					1 << 11 : localeInfo.TARGET_INFO_RACE_ELEC,
					1 << 12 : localeInfo.TARGET_INFO_RACE_FIRE,
					1 << 13 : localeInfo.TARGET_INFO_RACE_ICE,
					1 << 14 : localeInfo.TARGET_INFO_RACE_WIND,
					1 << 15 : localeInfo.TARGET_INFO_RACE_EARTH,
					1 << 16 : localeInfo.TARGET_INFO_RACE_DARK,
					1 << 17 : localeInfo.TARGET_INFO_RACE_ZODIAC,
				}
				(mainrace, subrace, dwRaceFlag) = ("", "", nonplayer.GetMonsterRaceFlag(mobVnum))

				for i in range(18):
					curFlag = 1 << i
					if WikiUI.IS_SET(dwRaceFlag, curFlag):
						if curFlag in RACE_FLAG_TO_NAME:
							mainrace += RACE_FLAG_TO_NAME[curFlag] + ", "
						elif curFlag in SUB_RACE_FLAG_TO_NAME:
							subrace += SUB_RACE_FLAG_TO_NAME[curFlag] + ", "

				if nonplayer.IsMonsterStone(mobVnum):
					mainrace += localeInfo.TARGET_INFO_RACE_METIN + ", "

				mainrace = localeInfo.TARGET_INFO_NO_RACE if mainrace == "" else mainrace[:-2]
				subrace = localeInfo.TARGET_INFO_NO_RACE if subrace == "" else subrace[:-2]

				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*1), True), "|Ikey/plus|i "+localeInfo.WIKI_STATICS_INFO_TYPE%(mainrace, subrace)))

				(mindmg, maxdmg) = nonplayer.GetMonsterDamage(mobVnum)
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*2), True), "|Ikey/plus|i "+localeInfo.WIKI_STATICS_INFO_DMG%(mindmg,maxdmg,nonplayer.GetMonsterMaxHP(mobVnum))))

				(minyang, maxyang) = nonplayer.GetMonsterPrice(mobVnum)
				exp = nonplayer.GetMonsterExp(mobVnum)
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*3), True), "|Ikey/plus|i "+localeInfo.WIKI_STATICS_INFO_YNG%(minyang, maxyang, exp)))

				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*4), True), "|Ikey/plus|i "+localeInfo.WIKI_STATICS_INFO_DEFENSES))
				resists = {
					nonplayer.MOB_RESIST_SWORD : localeInfo.TARGET_INFO_RESIST_SWORD,
					nonplayer.MOB_RESIST_TWOHAND : localeInfo.TARGET_INFO_RESIST_TWOHAND,
					nonplayer.MOB_RESIST_DAGGER : localeInfo.TARGET_INFO_RESIST_DAGGER,
					nonplayer.MOB_RESIST_BELL : localeInfo.TARGET_INFO_RESIST_BELL,
					nonplayer.MOB_RESIST_FAN : localeInfo.TARGET_INFO_RESIST_FAN,
					nonplayer.MOB_RESIST_BOW : localeInfo.TARGET_INFO_RESIST_BOW,
					nonplayer.MOB_RESIST_MAGIC : localeInfo.TARGET_INFO_RESIST_MAGIC,
				}
				c = 0
				for resist, label in resists.items():
					ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (20, 3*(7*(5+c)), True), label % nonplayer.GetMonsterResist(mobVnum, resist)))
					c+=1

			if ListBox.isNeedScrollBar():
				ListBox.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), ListBox, (ListBox.GetWidth()-13, -1, True), "", "", (8, ListBox.GetHeight()+5)))
			ListBox.Show()
			self._children["ListBox"] = ListBox
			self.Show()

class ListBoxItemSpecial(WikiUI.DefaultWikiImage):

	def __init__(self, listIndex, itemVnum, mobVnum, isType, directlyLoad = False, loadRender = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["isType"] = isType
		self._children["itemVnum"] = itemVnum
		self._children["mobVnum"] = mobVnum
		self.LoadImage(IMG_DIR+"slot/detail_chest.png")
		if directlyLoad:
			self.LoadItemInfos(loadRender)

	def LoadItemInfos(self, loadRender = False):
		if self.IsLoaded == False:
			self.IsLoaded=True

			(listIndex, isType, itemVnum, mobVnum) = (self._children["listIndex"], self._children["isType"], self._children["itemVnum"], self._children["mobVnum"])

			name = nonplayer.GetMonsterName(mobVnum if isType == 0 else itemVnum)

			if isType == 0:
				item.SelectItem(itemVnum)

			setItemName = localeInfo.WIKI_CONTENT_INFO%item.GetItemName()
			if isType != 0:
				setItemName = localeInfo.WIKI_DROPLIST_INFO%name
				setItemName += " - Level {}".format(nonplayer.GetMonsterLevel(itemVnum))
				if WikiUI.IsGameMaster():
					setItemName += " - Mob Vnum {}".format(itemVnum)

			self._children["itemName"] = WikiUI.CreateWindow(ui.TextLine(), self, (230, 5), setItemName, "horizontal:center")
			self._children["origin"] = WikiUI.CreateWindow(ui.TextLine(), self, (480, 5), localeInfo.WIKI_ORIGIN)

			needOriginListBox = True if not (isType == 0 and mobVnum != 0) and isinstance(WikiUI.GetOriginMapName(itemVnum), list) and len(WikiUI.GetOriginMapName(itemVnum)) > 0 else False

			if needOriginListBox:
				yPos = 0
				ListboxOrigin = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (450, 25), "", "", (90, 66))
				nameList = WikiUI.GetOriginMapName(itemVnum)
				for originName in nameList:
					ListboxOrigin.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListboxOrigin, (5, yPos, True), originName[:15] + "..." if len(originName) > 18 else originName, "horizontal:left", (-1, -1), "Tahoma:11"))
					ListboxOrigin.SetNameList(nameList)
					yPos+=13
				if ListboxOrigin.isNeedScrollBar():
					ListboxOrigin.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (450+83, 22), "", "", (8, ListboxOrigin.GetHeight())))
				self._children["ListboxOrigin"] = ListboxOrigin
			else:
				yPos = 0
				ListboxOrigin = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (450, 25), "", "", (90, 66))
				name = WikiUI.GetOriginMapName(itemVnum)

				ListboxOrigin.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListboxOrigin, (5, yPos, True), name[:15] + "..." if len(name) > 18 else name, "horizontal:left", (-1, -1), "Tahoma:11"))
				ListboxOrigin.SetNameList(name)
				self._children["ListboxOrigin"] = ListboxOrigin

				# bossVnum = WikiUI.CreateWindow(ui.TextLine(), self, (450, 36), "", "", (90, 66))
				# # bossVnum.SetTextRange(13)
				# bossVnum.SetHorizontalAlignLeft()
				# bossVnum.SetVerticalAlignCenter()
				# bossVnum.SetFontName("Tahoma:11")
				# if isType == 0 and mobVnum != 0:
				# 	bossVnum.SetText(name[:12] + "..." if len(name) > 15 else name)
				# else:
				# 	name = WikiUI.GetOriginMapName(itemVnum)
				# 	newName = name[:12] + "..." if len(name) > 15 else name
				# 	if isinstance(newName, list):
				# 		newText = ""
				# 		for tr in newName:
				# 			newText+=tr+"\\n"
				# 		bossVnum.SetText(newText if newText != "" else "-")
				# 		bossVnum.SetPosition(450, 22-(len(newName)*4))
				# 	else:
				# 		bossVnum.SetText(newName if newName != "" else "-")
				# 	bossVnum.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInToolTip,name)
				# 	bossVnum.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutToolTip)

				# self._children["bossVnum"] = bossVnum

			if isType == 0:
				itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (10, 25), item.GetIconImageFileName())
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,itemVnum)
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
				self._children["itemIcon"] = itemIcon

			else:
				renderIndex = 20 + listIndex
				renterTarget = WikiUI.CreateWindow(ui.WikiRenderTargetUi(), self, (1, 1), "", "", (47,87))
				renterTarget.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 1, itemVnum)
				self._children["renterTarget"] = renterTarget
				self._children["renderIndex"] = renderIndex

				useWikiImprovements = getattr(app, "WIKI_IMPROVEMENTS", 1)
				if not useWikiImprovements:
					self.renderLoaded = True
					renterTarget.SetRenderTarget(renderIndex)
					WikiRenderTarget.SelectModel(renderIndex, itemVnum)
					WikiRenderTarget.SetMotionStatus(renderIndex, 0)
					WikiRenderTarget.SetEffectStatus(renderIndex, 0)
					WikiRenderTarget.SetVisibility(renderIndex, True)
				else:
					self.renderLoaded = bool(loadRender)
					if loadRender:
						renterTarget.SetRenderTarget(renderIndex)
						WikiRenderTarget.SelectModel(renderIndex, itemVnum)
						WikiRenderTarget.SetMotionStatus(renderIndex, 0)
						WikiRenderTarget.SetEffectStatus(renderIndex, 0)
						WikiRenderTarget.SetVisibility(renderIndex, True)
			whileSize = wiki.GetSpecialInfoSize(itemVnum) if isType == 0 else wiki.GetMobInfoSize(itemVnum)

			if whileSize != 0:
				Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (48, 22), "", "", (403, 65))

				gridCalculate = WikiUI.Grid(width = 12, height = 50)

				for j in range(whileSize):
					(vnum, count) = wiki.GetSpecialInfoData(itemVnum, j) if isType == 0 else wiki.GetMobInfoData(itemVnum, j)
					if vnum == 0 or count == 0:
						continue
					item.SelectItem(vnum)
					(width, height) = item.GetItemSize()
					if width == 0 or height == 0:
						continue
					pos = gridCalculate.find_blank(width, height)
					gridCalculate.put(pos, width, height)
					(x, y) = WikiUI.calculatePos(pos, 11)

					item_new = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), Listbox, (x, y, True), item.GetIconImageFileName())
					item_new.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,vnum)
					item_new.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					item_new.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,vnum)
					Listbox.AppendItem(item_new)

					if count>1:
						Listbox.AppendItem(WikiUI.CreateWindow(ui.NumberLine() if USE_ITEM_COUNT_NUMBER_LINE else ui.TextLine(), Listbox, (x+5,y+item_new.GetHeight()-10,True) if USE_ITEM_COUNT_NUMBER_LINE else (x+5,y+item_new.GetHeight()-10,True), (localeInfo.MoneyFormat(str(count)).replace(".000","k")), "horizontal:left"))
				if Listbox.isNeedScrollBar():
					Listbox.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (443, 23), "", "", (8, 63)))
				self._children["Listbox"] = Listbox
			self.Show()

	def RenderLoad(self):
		if getattr(self, "renderLoaded", True):
			return

		renderIndex = self._children["renderIndex"] if "renderIndex" in self._children else -1
		if renderIndex == -1:
			return

		self.renderLoaded = True
		self._children["renterTarget"].SetRenderTarget(renderIndex)
		WikiRenderTarget.SelectModel(renderIndex, self._children["itemVnum"])
		WikiRenderTarget.SetMotionStatus(renderIndex, 0)
		WikiRenderTarget.SetEffectStatus(renderIndex, 0)
		WikiRenderTarget.SetVisibility(renderIndex, True)

class ArticleGUI(WikiUI.DefaultWikiWindow):
	def __init__(self, index):
		WikiUI.DefaultWikiWindow.__init__(self)
		if isinstance(index, str):
			if index.find("#") != -1:
				indexList = index.split("#")
				if len(indexList) == 2:
					self._children["index"] = int(indexList[0])
					self._children["scrollPos"] = float(indexList[1])
		else:
			self._children["index"] = index
			self._children["scrollPos"] =  0.0
		mainParent = osfInfo.GetWikiInterface()
		if mainParent != None:
			self.SetSize(mainParent.children["resultpageListbox"].GetWidth(),mainParent.children["resultpageListbox"].GetHeight())
	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded = True
			Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (0,0), "", "", (self.GetWidth()-15, self.GetHeight()-15))
			self.ReadArticle(Listbox, self._children["index"])
			self.CheckScrollBarNeed(Listbox)
			self._children["Listbox"] = Listbox
			self.Show()
	def ParseToken(self, data):
		data = data.replace(chr(10), "").replace(chr(13), "")
		if not (len(data) and data[0] == "["):
			return (False, {}, data)
		fnd = data.find("]")
		if fnd <= 0:
			return (False, {}, data)
		content = data[1:fnd]
		data = data[fnd+1:]
		content = content.split(";")
		container = {}
		for i in content:
			i = i.strip()
			splt = i.split("=")
			if len(splt) == 1:
				container[splt[0].lower().strip()] = True
			else:
				#container[splt[0].lower().strip()] = splt[1].lower().strip()
				container[splt[0].lower().strip()] = splt[1].lower().strip() if splt[0].lower() != "linktext" else splt[1]
		return (True, container, data)
	def GetColorFromString(self, strCol):
		retData = []
		dNum = 4
		hCol = int(strCol, 16)
		if hCol <= 0xFFFFFF:
			retData.append(1.0)
			dNum = 3
		for i in range(dNum):
			retData.append(float((hCol >> (8 * i)) & 0xFF) / 255.0)
		retData.reverse()
		return retData
	def DirectionEvent(self, emptyArg, type, index, pos):
		parent = osfInfo.GetWikiInterface()
		if parent != None:
			if "item" == type:
				parent.ShowItemInfo(int(index), 0)
			elif "mob" == type:
				parent.ShowItemInfo(int(index), 1)
			elif "article" == type:
				parent.ShowItemInfo("System#"+str(index)+"#"+str(pos),3)
			elif "events" == type:
				parent.ShowItemInfo("events#"+str(index)+"#"+str(pos),3)
			elif "article" == type:
				parent.ShowItemInfo("System#"+str(index)+"#"+str(pos),3)
			elif "warp" == type:
				net.SendChatPacket("/wiki_server warp {} {}".format(index, pos))
				mainParent = osfInfo.GetWikiInterface()
				if mainParent:
					mainParent.Close()
			elif "website" == type:
				os.system("start \"\" {}".format(index))

	def ReadArticle(self, Listbox, index):
		fileName = WikiUI.GetArticleFileName(index)
		if fileName == "":
			return
		try:
			lines = open(fileName, "r").readlines()
		except:
			pass
		_y = 15
		for i in lines:
			(ret, tokenMap, i) = self.ParseToken(i)
			if ret:
				if "banner_img" in tokenMap:
					mainParent = osfInfo.GetWikiInterface()
					if mainParent != None:
						resultpagebtn = mainParent.children["resultpagebtn"]
						resultpagebtn.LoadImage(tokenMap["banner_img"])
						resultpagebtn.Show()
						tokenMap.pop("banner_img")

				if "img" in tokenMap:
					cimg = ui.ExpandedImageBoxWiki()
					cimg.SetParent(Listbox)
					cimg.AddFlag("attach")
					cimg.AddFlag("not_pick")
					cimg.LoadImage(tokenMap["img"])
					cimg.Show()
					tokenMap.pop("img")
					x = 0
					if "x" in tokenMap:
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					y = 0
					if "y" in tokenMap:
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if "center_align" in tokenMap:
						cimg.SetPosition(Listbox.GetWidth() // 2 - cimg.GetWidth() // 2, y, True)
						tokenMap.pop("center_align")
					elif "right_align" in tokenMap:
						cimg.SetPosition(Listbox.GetWidth() - cimg.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						cimg.SetPosition(x, y, True)
					Listbox.AppendItem(cimg)

				if "item" in tokenMap:
					itemVnum = int(tokenMap["item"])
					tokenMap.pop("item")

					metinSlot = [0 for j in range(player.METIN_SOCKET_MAX_NUM)]
					attrSlot = [[0,0] for j in range(player.ATTRIBUTE_SLOT_MAX_NUM)]

					if "socket" in tokenMap:
						metinSlotData = tokenMap["socket"].split("#")  if tokenMap["socket"].find("#") else tokenMap["socket"]
						tokenMap.pop("socket")
						for metin in metinSlotData:
							metinSplit = metin.split(":")
							if len(metinSplit) != 2:
								continue
							metinSlot[int(metinSplit[0])] = int(metinSplit[1])

					if "attr" in tokenMap:
						attrSlotData = tokenMap["attr"].split("#") if tokenMap["attr"].find("#") else tokenMap["attr"]
						tokenMap.pop("attr")

						for attr in attrSlotData:
							attrSplit = attr.split(":")
							if len(attrSplit) != 2:
								continue
							attrDataSplit = attrSplit[1].split("?")
							if len(attrDataSplit) != 2:
								continue
							attrSlot[int(attrSplit[0])] = [int(attrDataSplit[0]), int(attrDataSplit[1])]

					for k in range(player.ATTRIBUTE_SLOT_MAX_NUM):
						attrSlot[k] = tuple(attrSlot[k])

					item.SelectItem(itemVnum)
					cimg = ui.ExpandedImageBoxWiki()
					cimg.SetParent(Listbox)
					if item.GetIconImageFileName().find("gr2") == -1:
						cimg.LoadImage(item.GetIconImageFileName())
					else:
						cimg.LoadImage("icon/item/27995.tga")
					cimg.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, itemVnum, metinSlot, attrSlot)
					cimg.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					cimg.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
					cimg.Show()
					x = 0
					if "x" in tokenMap:
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					y = 0
					if "y" in tokenMap:
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if "center_align" in tokenMap:
						cimg.SetPosition(Listbox.GetWidth() // 2 - cimg.GetWidth() // 2, y, True)
						tokenMap.pop("center_align")
					elif "right_align" in tokenMap:
						cimg.SetPosition(Listbox.GetWidth() - cimg.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						cimg.SetPosition(x, y, True)

					Listbox.AppendItem(cimg)

				if "link" in tokenMap:
					link = tokenMap["link"].split("#")
					tokenMap.pop("link")
					if len(link) != 3:
						continue

					if "text" in tokenMap:
						#linkText = WikiUI.GetArgToString(tokenMap["text"])
						linkText =tokenMap["text"]
						tokenMap.pop("text")
					else:
						linkText = ""

					tmp = WikiUI.TextlineLink()
					tmp.SetParent(Listbox)
					if "font_size" in tokenMap:
						splt = localeInfo.UI_DEF_FONT.split(":")
						tmp.SetFontName(splt[0]+":"+tokenMap["font_size"])
						tokenMap.pop("font_size")
					else:
						tmp.SetFontName(localeInfo.UI_DEF_FONT)

					linkText = linkText.replace("*", "|Ikey/plus")

					#tmp.SetText(WikiUI.GetArgToString(linkText), 1.2)
					tmp.SetText(linkText, 1.2)
					tmp.Show()
					if "color" in tokenMap:
						fontColor = self.GetColorFromString(tokenMap["color"])
						tmp.SetColor(grp.GenerateColor(fontColor[0], fontColor[1], fontColor[2], fontColor[3]), fontColor[0], fontColor[1], fontColor[2])
						tokenMap.pop("color")
					tmp.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.DirectionEvent), "", link[0], link[1],link[2])
					tmp.linkIcon.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.DirectionEvent),"", link[0], link[1], link[2])
					if "y" in tokenMap:
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if "x" in tokenMap:
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					if "center_align" in tokenMap:
						tmp.SetPosition(Listbox.GetWidth() // 2 - tmp.GetWidth() // 2, y, True)
						tokenMap.pop("center_align")
					elif "right_align" in tokenMap:
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)

				if "rendertarget" in tokenMap:
					mobVnum = int(tokenMap["rendertarget"])
					tokenMap.pop("rendertarget")

					(width, height) = (47, 87)

					if "width" in tokenMap:
						width = int(tokenMap["width"])
						tokenMap.pop("width")

					if "height" in tokenMap:
						height = int(tokenMap["height"])
						tokenMap.pop("height")

					targetIndex = WikiRenderTarget.GetFreeIndex(86, 1000000)
					tmp = ui.WikiRenderTargetUi()
					tmp.SetParent(Listbox)
					tmp.SetSize(width, height)
					tmp.SetRenderTarget(targetIndex)

					WikiRenderTarget.SelectModel(targetIndex, mobVnum)
					WikiRenderTarget.SetRotation(targetIndex, False)
					WikiRenderTarget.SetVisibility(targetIndex, True)

					tmp.SetEvent(ui.__mem_func__(self.DirectionEvent),"mouse_click", "mob", mobVnum, 0)
					tmp.Show()

					if "movable" in tokenMap:
						if int(tokenMap["movable"]):
							tmp.AddFlag("movable")
						tokenMap.pop("movable")


					if "y" in tokenMap:
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if "x" in tokenMap:
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					if "center_align" in tokenMap:
						tmp.SetPosition(Listbox.GetWidth() // 2 - tmp.GetWidth() // 2, y, True)
						tokenMap.pop("center_align")
					elif "right_align" in tokenMap:
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)

				if "button" in tokenMap:
					button = tokenMap["button"].split("#")
					tokenMap.pop("button")
					if len(button) != 3:
						continue

					tmp = ui.Button()
					tmp.SetParent(Listbox)
					tmp.SetUpVisual(button[0])
					tmp.SetOverVisual(button[1])
					tmp.SetDownVisual(button[2])
					tmp.Show()
					if "linkindex" in tokenMap:
						try:
							linkindex = tokenMap["linkindex"].split("#")
							if len(linkindex) == 3:
								tmp.SAFE_SetEvent(self.DirectionEvent, "", linkindex[0], linkindex[1], linkindex[2])
						except:
							pass
						tokenMap.pop("linkindex")
					if "text" in tokenMap:
						tmp.SetText(tokenMap["text"])
						tokenMap.pop("text")
					if "y" in tokenMap:
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if "x" in tokenMap:
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					if "center_align" in tokenMap:
						tmp.SetPosition(Listbox.GetWidth() // 2 - tmp.GetWidth() // 2, y, True)
						tokenMap.pop("center_align")
					elif "right_align" in tokenMap:
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)

			if ret and not len(i):
				continue

			i = i.replace("*", "|Ikey/plus|i")
			tmp = ui.TextLine()
			tmp.SetParent(Listbox)
			if "font_size" in tokenMap:
				splt = localeInfo.UI_DEF_FONT.split(":")
				tmp.SetFontName(splt[0]+":"+tokenMap["font_size"])
				tokenMap.pop("font_size")
			else:
				tmp.SetFontName(localeInfo.UI_DEF_FONT)
			tmp.SetText(WikiUI.GetArgToString(i))
			tmp.Show()
			tmp.SetSize(*tmp.GetTextSize())

			if "color" in tokenMap:
				fontColor = self.GetColorFromString(tokenMap["color"])
				tmp.SetPackedFontColor(grp.GenerateColor(fontColor[0], fontColor[1], fontColor[2], fontColor[3]))
				tokenMap.pop("color")

			if "y" in tokenMap:
				y = int(tokenMap["y"])
				tokenMap.pop("y")
			if "x" in tokenMap:
				x = int(tokenMap["x"])
				tokenMap.pop("x")

			tmp.SetPosition(5, _y, True)
			_y+=tmp.GetHeight()

			if "center_align" in tokenMap:
				tmp.SetPosition(Listbox.GetWidth() // 2 - tmp.GetWidth() // 2, tmp.GetLocalPosition()[1], True)
				tokenMap.pop("center_align")
			elif "right_align" in tokenMap:
				tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), tmp.GetLocalPosition()[1], True)
				tokenMap.pop("right_align")
			elif "x_padding" in tokenMap:
				tmp.SetPosition(int(tokenMap["x_padding"]), tmp.GetLocalPosition()[1], True)
				tokenMap.pop("x_padding")
			tmp.Show()
			Listbox.AppendItem(tmp)

	def CheckScrollBarNeed(self, Listbox):
		if Listbox.isNeedScrollBar():
			scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (self.GetWidth()-8, 2), "", "", (8, self.GetHeight() - 15))
			scrollBar.SetPos(self._children["scrollPos"])
			Listbox.SetScrollBar(scrollBar)
			Listbox.OnScroll()

class SpecialClass(WikiUI.DefaultWikiWindow):
	def __init__(self, listIndex, isMonster):
		WikiUI.DefaultWikiWindow.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["vnumList"] = []
		self._children["renderIndex"] = -1
		self.SetSize(700, 147)

	def CanAddNewItem(self):
		return len(self._children["vnumList"]) < 4

	def LoadItemInfos(self, data = -1):
		if data == -1:
			return
		xPos = len(self._children["vnumList"]) * (127+9)

		bg = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), self, (xPos, 0), IMG_DIR+"slot/detail_item_small.png")
		self._children["bg{}".format(data)] = bg

		item.SelectItem(data)
		itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBoxWiki(), bg, (-1, -1), item.GetIconImageFileName())
		itemIcon.SetPosition((bg.GetWidth()//2)-(itemIcon.GetWidth()//2), ((bg.GetHeight()-20)//2)-(itemIcon.GetHeight()//2))
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItemSpecial, data)
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
		itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click", 0, data)
		self._children["itemIcon{}".format(data)] = itemIcon
		self._children["itemName{}".format(data)] = WikiUI.CreateWindow(ui.TextLine(), self, (len(self._children["vnumList"]) * (127+9)+(bg.GetWidth()//2), bg.GetHeight()-18), item.GetItemName(), "horizontal:center")
		self._children["vnumList"].append(data)
		self.Show()

	def OverOutItem(self):
		renderIndex = self._children["renderIndex"]
		if renderIndex != -1:
			WikiRenderTarget.SetVisibility(renderIndex, False)
			WikiRenderTarget.ResetModel(renderIndex)
		WikiUI.DefaultWikiWindow.OverOutItem(self)

	def OverInItemSpecial(self, itemVnum):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			tooltipItem = interface.tooltipItem
			if tooltipItem:
				tooltipItem.ClearToolTip()

				renderIndex = WikiRenderTarget.GetFreeIndex(86, 1000000)
				self._children["renderIndex"] = renderIndex

				tooltipItem.toolTipWidth -= 35

				renterTarget = WikiUI.CreateWindow(ui.WikiRenderTargetUi(), tooltipItem, (10, 5), "", "", (tooltipItem.toolTipWidth-20, 150))
				renterTarget.SetRenderTarget(renderIndex)
				tooltipItem.childrenList.append(renterTarget)

				tooltipItem.toolTipHeight += 150
				tooltipItem.ResizeToolTip()
				tooltipItem.SetItemToolTipWiki(itemVnum)
				WikiUI.SetItemToModelPreview(renderIndex, itemVnum)
