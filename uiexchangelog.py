import ui, _weakref, localeInfo, math, osfInfo, app, uiCommon, net, player

IMG_DIR = "d:/ymir work/ui/game/exchange_log/"

def calculateRect(curValue, maxValue):
	try:
		return -1.0 + float(curValue) / float(maxValue)
	except:
		return 0.0

class ExchangeLog(ui.ScriptWindow):
	class ExchangeWindow(ui.ScriptWindow):
		def __del__(self):
			ui.ScriptWindow.__del__(self)
		def Destroy(self):
			self.ClearDictionary()
			self.logData = {}
			self.isOpened = False
		def __init__(self):
			ui.ScriptWindow.__init__(self)
			self.Destroy()
			self.__LoadWindow()
		def __LoadWindow(self):
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "uiscript/exchange_log/fake_exchange.py")
				GetChild = self.GetChild

				GetChild("owner_slot").SetOverInItemEvent(ui.__mem_func__(self.OverInOwnerItem))
				GetChild("target_slot").SetOverInItemEvent(ui.__mem_func__(self.OverInTargetItem))
				GetChild("owner_slot").SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
				GetChild("target_slot").SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
				
				self.GetChild("board").SetCloseEvent(self.Hide)

			except:
				import exception
				exception.Abort("ExchangeLog.ExchangeWindow.Initialize.__LoadWindow")

		def OverInTargetItem(self, slotIndex):
			interface = osfInfo.GetInterfaceInstance()
			if interface != None:
				if interface.tooltipItem:
					ownerItems = self.logData["target_items"]
					if slotIndex in ownerItems:
						itemData = ownerItems[slotIndex]
						interface.tooltipItem.ClearToolTip()
						refine_element = itemData.get("refineElement") if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
						interface.tooltipItem.AddItemData(itemData["itemVnum"], itemData["metinSlot"], itemData["attrSlot"], apply_random_list=itemData["applyRandomSlot"], refine_element=refine_element)
		def OverInOwnerItem(self, slotIndex):
			interface = osfInfo.GetInterfaceInstance()
			if interface != None:
				if interface.tooltipItem:
					ownerItems = self.logData["owner_items"]
					if slotIndex in ownerItems:
						itemData = ownerItems[slotIndex]
						interface.tooltipItem.ClearToolTip()
						refine_element = itemData.get("refineElement") if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
						interface.tooltipItem.AddItemData(itemData["itemVnum"], itemData["metinSlot"], itemData["attrSlot"], apply_random_list=itemData["applyRandomSlot"], refine_element=refine_element)
		def OverOutItem(self):
			interface = osfInfo.GetInterfaceInstance()
			if interface != None:
				if interface.tooltipItem:
					interface.tooltipItem.HideToolTip()

		def Refresh(self):
			exchange_grid_size = [6, 4]
			(ownerSlot,targetSlot) = (self.GetChild("owner_slot"),self.GetChild("target_slot"))
			(ownerItems, targetItems) = (self.logData["owner_items"], self.logData["target_items"])

			for j in range(exchange_grid_size[0] * exchange_grid_size[1]):
				ownerSlot.ClearSlot(j)
				targetSlot.ClearSlot(j)

				itemData = ownerItems[j] if j in ownerItems else -1
				if itemData != -1:
					ownerSlot.SetItemSlot(j, itemData["itemVnum"], itemData["itemCount"] if itemData["itemCount"] > 1 else 0)
	
				itemData = targetItems[j] if j in targetItems else -1
				if itemData != -1:
					targetSlot.SetItemSlot(j, itemData["itemVnum"], itemData["itemCount"] if itemData["itemCount"] > 1 else 0)

			ownerSlot.RefreshSlot()
			targetSlot.RefreshSlot()

			self.GetChild("owner_gold").SetText(localeInfo.MoneyFormat(self.logData["owner_gold"]).replace(".000","k"))
			self.GetChild("target_gold").SetText(localeInfo.MoneyFormat(self.logData["target_gold"]).replace(".000","k"))

		def SetLoadingStatus(self, bStatus):
			__listofChilds = ["owner_slot","target_slot","direction"]
			GetChild = self.GetChild
			
			loadingText = GetChild("loadingText")
			loadingText.nextTime = 0
			loadingText.dotCount = 0
			loadingText.dotIncrease = 1
			if bStatus:
				loadingText.Show()
			else:
				loadingText.Hide()
			for childName in __listofChilds:
				if bStatus:
					GetChild(childName).Hide()
				else:
					GetChild(childName).Show()

		def SetLog(self, logData):
			self.logData = logData

			self.GetChild("board").SetTitleName(localeInfo.EXCHANGELOG_FAKETITLE % (logData["owner"], logData["target"]))
			if logData["itemsLoaded"]:
				self.SetLoadingStatus(False)
				self.Refresh()
			else:
				self.SetLoadingStatus(True)
				net.SendChatPacket("/ex_log load_item {}".format(logData["logID"]))
			self.Show()
			self.SetTop()

		def OnPressEscapeKey(self):
			self.Hide()
			return True

		def OnUpdate(self):
			loadingText = self.GetChild("loadingText") if self.IsChild("loadingText") else None
			if loadingText:
				if loadingText.IsShow() and app.GetTime() > loadingText.nextTime:
					dotCount = loadingText.dotCount
					dotIncrease = loadingText.dotIncrease
					
					loadingText.SetText(localeInfo.EXCHANGELOG_LOADING + (dotCount * "."))
					bg = self.GetChild("bg")
					loadingText.SetPosition((bg.GetWidth()//2) - (loadingText.GetTextSize()[0]//2), (bg.GetHeight()//2) - (loadingText.GetTextSize()[1]//2))
					dotCount+=1

					if dotIncrease == dotCount:
						dotIncrease+=1
						if dotIncrease == 10:
							dotIncrease = 1
						dotCount = 0

					loadingText.dotCount = dotCount
					loadingText.dotIncrease = dotIncrease
					loadingText.nextTime = app.GetTime() + 0.2

	class LogItem(ui.ScriptWindow):
		def __del__(self):
			ui.ScriptWindow.__del__(self)
		def Destroy(self):
			self.ClearDictionary()
			self.logData = {}
			self.guiWnd = None
		def __init__(self, parent, guiWnd, logData):
			ui.ScriptWindow.__init__(self)
			self.SetParent(parent)
			self.Destroy()
			self.guiWnd = guiWnd
			self.__LoadLog(logData)
		def __LoadLog(self, logData):
			self.logData = logData
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "uiscript/exchange_log/log.py")
				GetChild = self.GetChild
				GetChild("owner").SetText(logData["owner"])
				GetChild("target").SetText(logData["target"])
				GetChild("date").SetText(logData["date"])
				GetChild("ip").SetText(logData["ip"])
				GetChild("gold").SetText(localeInfo.MoneyFormat(logData["owner_gold"]+logData["target_gold"]).replace(".000","k"))

				selectedBtn = GetChild("select_btn")
				selectedBtn.LoadImage(IMG_DIR+"selected.tga" if logData["isSelected"] else IMG_DIR+"not_selected.tga")
				selectedBtn.SetPosition(16, 8)
				selectedBtn.SetEvent(ui.__mem_func__(self.SetSelected), "mouse_click")

				GetChild("board").SetEvent(ui.__mem_func__(self.SetSelected), "mouse_click")

				GetChild("content").SetEvent(ui.__mem_func__(self.__ClickContent))
			except:
				import exception
				exception.Abort("ExchangeLog.LogItem.Initialize.__LoadLog")
			self.Show()

		def __ClickContent(self):
			self.guiWnd.SetFakeExchangeData(self.logData)

		def SetSelected(self, emptyArg):
			newStatus = not self.logData["isSelected"]
			selectedBtn = self.GetChild("select_btn")
			selectedBtn.LoadImage(IMG_DIR+"selected.tga" if newStatus else IMG_DIR+"not_selected.tga")
			selectedBtn.SetPosition(16, 8)
			self.logData["isSelected"] = newStatus

		def GetListBox(self):
			return self.guiWnd.GetChild("listbox")

		def OnRender(self):
			parent = self.GetListBox()
			_wy = parent.GetGlobalPosition()[1]
			_height = parent.GetHeight()
			#HIDE_Y_DIFFERENCE = 250
			#renderList = [childItem for chilname, childItem in self.ElementDictionary.items()]

			for chilname, childItem in self.ElementDictionary.items():
				if isinstance(childItem, ui.TextLine):
					(_x,_y) = childItem.GetGlobalPosition()
					childHeight = childItem.GetHeight()
					if _y < _wy:
						if childItem.IsShow():
							childItem.Hide()
						continue
					if _y+childHeight > (_wy+_height-20):
						if childItem.IsShow():
							childItem.Hide()
						continue
					if not childItem.IsShow():
						childItem.Show()

				if isinstance(childItem, ui.ToggleButton) or isinstance(childItem, ui.Button) or isinstance(childItem, ui.ExpandedImageBox):
					topRender = 0
					bottomRender = 0
					itsRendered = False
					(_x,_y) = childItem.GetGlobalPosition()
					childHeight = childItem.GetHeight()

					if _y < _wy:
						topRender = _y-_wy
						itsRendered = True
					if _y+childHeight > (_wy+_height-2):
						bottomRender = (_wy+_height-2)-(_y+childHeight)
						itsRendered = True

					if itsRendered:
						childItem.SetRenderingRect(0,calculateRect(childHeight-abs(topRender), childHeight),0,calculateRect(childHeight-abs(bottomRender),childHeight))
					else:
						childItem.SetRenderingRect(0,0,0,0)
					if not childItem.IsShow():
						childItem.Show()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
	def Destroy(self):
		if self.IsChild("listbox"):
			listBox = self.GetChild("listbox")
			listBox.RemoveAllItems()
			listBox.Destroy()
		if self.IsChild("exchangeWindow"):
			self.GetChild("exchangeWindow").Destroy()
		self.ClearDictionary()
		self.logDataDict={}
		self.currentPage=0
		self.pageCount=0
		self.perPage=0
		self.privateCode="NONE"
		self.packetLoaded=False
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.Destroy()
		self.perPage = 20
		self.__LoadWindow()

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/exchange_log/window.py")

			GetChild = self.GetChild

			listBox = GetChild("listbox")
			scrollBar = ScrollBarNew()
			scrollBar.SetParent(listBox)
			scrollBar.SetPosition(listBox.GetWidth()-scrollBar.GetWidth(), 0)
			scrollBar.SetScrollBarSize(listBox.GetHeight())
			scrollBar.SetMiddleBarSize(1.0)
			scrollBar.Show()
			listBox.SetScrollBar(_weakref.proxy(scrollBar))
			listBox.SetExtraScrollLen(40)

			self.ElementDictionary["scrollBar"] = scrollBar

			GetChild("next_button").SetEvent(ui.__mem_func__(self.NextPage))
			GetChild("prev_button").SetEvent(ui.__mem_func__(self.PrevPage))
			GetChild("first_prev_button").SetEvent(ui.__mem_func__(self.FirstPage))
			GetChild("last_next_button").SetEvent(ui.__mem_func__(self.LastPage))

			GetChild("delete_selected").SAFE_SetEvent(self.__ClickDelete, False)
			GetChild("delete_all").SAFE_SetEvent(self.__ClickDelete, True)

			GetChild("board").SetCloseEvent(self.Close)

		except:
			import exception
			exception.Abort("ExchangeLogWindow.Initialize.__LoadWindow")

		self.ElementDictionary["questionDialog"] = uiCommon.QuestionDialog2()

		self.ElementDictionary["exchangeWindow"] = self.ExchangeWindow()

		self.SetCenterPosition()
		self.OnMoveWindow(*self.GetGlobalPosition())
		#self.Simulation()
		self.GotoPage(1)

	def GetInputBoard(self):
		InputBoard = self.GetChild("InputBoard") if self.IsChild("InputBoard") else None
		if not InputBoard:
			InputBoard = uiCommon.InputDialogWithDescription()
			InputBoard.SetTitle(localeInfo.EXCHANGELOG_INPUTTITLE)
			InputBoard.SetAcceptEvent(ui.__mem_func__(self.AcceptInputPrivateCode))
			InputBoard.SetCancelEvent(ui.__mem_func__(self.CancelInputPrivateCode))
			InputBoard.SetNumberMode()
			InputBoard.SetSecretMode()
			InputBoard.SetMaxLength(7)
			InputBoard.SetBoardWidth(150)
			InputBoard.SetDescription(localeInfo.EXCHANGELOG_INPUTDESC)
			self.ElementDictionary["InputBoard"] = InputBoard
		return InputBoard

	def __ClickDelete(self, deleteType):
		if deleteType:
			if len(self.logDataDict) == 0:
				self.PopupNotifyMessage(localeInfo.EXCHANGELOG_INPUT_NOT_HAS_LOG)
				return
		else:
			hasRemoveLogs = False
			for key, data in self.logDataDict.items():
				if data["isSelected"]:
					hasRemoveLogs = True
					break
			if not hasRemoveLogs:
				self.PopupNotifyMessage(localeInfo.EXCHANGELOG_INPUT_NOT_HAS_LOG)
				return

		InputBoard = self.GetInputBoard()
		InputBoard.deleteType = deleteType
		InputBoard.Open()

	def Open(self):
		self.GetChild("board").SetTitleName(localeInfo.EXCHANGELOG_TITLE+"("+player.GetName()+")")
		exchangeWindow = self.ElementDictionary["exchangeWindow"]
		if exchangeWindow.isOpened:
			exchangeWindow.Show()
			exchangeWindow.SetTop()
		self.Show()
		self.SetTop()

		if not self.packetLoaded:
			self.packetLoaded = True
			net.SendChatPacket("/ex_log load")

	def Close(self):
		self.ElementDictionary["InputBoard"] = None
		exchangeWindow = self.ElementDictionary["exchangeWindow"]
		exchangeWindow.isOpened = exchangeWindow.IsShow()
		exchangeWindow.Hide()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def CancelInputPrivateCode(self):
		self.ElementDictionary["InputBoard"] = None

	def EmptyFunc(self):
		pass

	def PopupNotifyMessage(self, msg, func = 0):
		if not func:
			func = self.EmptyFunc
		game = osfInfo.GetGameInstance()
		if game:
			game.stream.popupWindow.Close()
			game.stream.popupWindow.Open(msg, func, localeInfo.UI_OK)

	def AcceptInputPrivateCode(self):
		InputBoard = self.GetInputBoard()
		deleteType = InputBoard.deleteType
		text = InputBoard.GetText()
		self.ElementDictionary["InputBoard"] = None

		#import chat
		#chat.AppendChat(1, "[TEST]Private code {} input {}".format(self.privateCode, text))

		if not text.isdigit():
			self.PopupNotifyMessage(localeInfo.EXCHANGELOG_INPUT_NOT_NUMBER)
			return
		elif len(text) != 7:
			self.PopupNotifyMessage(localeInfo.EXCHANGELOG_INPUT_NOT_ENOUGHT_SIZE)
			return
		elif text != self.privateCode:
			self.PopupNotifyMessage(localeInfo.EXCHANGELOG_INPUT_NOT_SAME_CODE)
			return

		exchangeWindow = self.ElementDictionary["exchangeWindow"]
		if deleteType:
			if exchangeWindow.IsShow():
				exchangeWindow.Hide()

			net.SendChatPacket("/ex_log delete {} all".format(text))
			self.logDataDict={}
		else:
			cmd = "/ex_log delete {}".format(text)
			deletedList = []
			logDataDict = self.logDataDict
			for key, data in logDataDict.items():
				if data["isSelected"]:
					cmd+= " {}".format(key)
					deletedList.append(key)
					if len(cmd) > 120:
						break
					if exchangeWindow.IsShow() and exchangeWindow.logData["logID"] == key:
						exchangeWindow.Hide()
			for key in deletedList:
				del logDataDict[key]
			self.logDataDict = logDataDict
			net.SendChatPacket(cmd)
		self.Refresh()

	def SetFakeExchangeData(self, logData):
		exchangeWindow = self.GetChild("exchangeWindow")
		exchangeWindow.SetLog(logData)

	def OnMoveWindow(self, x, y):
		exchangeWindow = self.GetChild("exchangeWindow") if self.IsChild("exchangeWindow") else None
		if exchangeWindow:
			exchangeWindow.SetPosition(x+self.GetWidth()+5, y+11)

	def Refresh(self):
		listBox = self.GetChild("listbox")
		listBox.RemoveAllItems()

		logDataList = [ data for key, data in dict(sorted(self.logDataDict.items())).items()]
		logDataList = sorted(logDataList, key=lambda data: (data["date"], data["logID"]), reverse=True)
		self.pageCount = int(math.ceil(float(len(logDataList)) / float(self.perPage)))
		self.RefreshPaginationButtons()

		start = (self.currentPage - 1) * self.perPage
		end = ((self.currentPage - 1) * self.perPage) + self.perPage
		currentDatList = logDataList[start:end]

		NEXT_Y = 30
		proxyListBox = _weakref.proxy(listBox)
		selfProxy = _weakref.proxy(self)
		for logData in currentDatList:
			newLog = self.LogItem(proxyListBox, selfProxy, logData)
			newLog.SetPosition(0, len(listBox.itemList) * NEXT_Y, True)
			listBox.AppendItem(newLog)
		listBox.RefreshAll()

	def RefreshPaginationButtons(self):
		pageButtons=[self.GetChild("page_{}".format(x)) for x in range(5)]
		currentPaginationPage = int(math.ceil(float(self.currentPage) / 5.0 ))
		shownPages = min(self.pageCount - (5 * (currentPaginationPage - 1)), 5)
		for x in range(5):
			currentPage = (x + ((currentPaginationPage-1) * 5) + 1)
			pageButtons[x].SetUp()
			pageButtons[x].SetText(str(currentPage))
			pageButtons[x].SetEvent(lambda arg=currentPage: self.GotoPage(arg))
		for pageButton in pageButtons:
			ui.Button.Hide(pageButton)
		for pageButton in pageButtons:
			ui.Button.Enable(pageButton)
		for x in range(shownPages):
			pageButtons[x].Show()
		pageButtons[(self.currentPage - ((currentPaginationPage - 1) * 5)) - 1].Down()
		pageButtons[(self.currentPage - ((currentPaginationPage - 1) * 5)) - 1].Disable()
	def GotoPage(self, page):
		self.currentPage = page
		self.Refresh()
	def FirstPage(self):
		self.GotoPage(1)
	def LastPage(self):
		self.GotoPage(self.pageCount)
	def NextPage(self):
		if self.currentPage < self.pageCount:
			self.GotoPage(self.currentPage+1)
	def PrevPage(self):
		if self.currentPage > 1:
			self.GotoPage(self.currentPage-1)

	def RefreshItems(self, logID):
		if logID in self.logDataDict:
			self.logDataDict[logID]["itemsLoaded"] = True

			exchangeWindow = self.ElementDictionary["exchangeWindow"]
			if logID == exchangeWindow.logData["logID"]:
				exchangeWindow.SetLoadingStatus(False)
				exchangeWindow.Refresh()

	def Clear(self, playerCode):
		self.privateCode = str(playerCode)
		self.logDataDict={}
		self.Refresh()

	def ExchangeLogItemAppend(self, logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, refineElement, isOwnerItem):
		#import chat
		#chat.AppendChat(1,"[TEST]ExchangeLogItemAppend {} {} {} {} {} {} {} {}".format(logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, isOwnerItem))

		if logID in self.logDataDict:
			attrList = [[attrType[x], attrValue[x]] for x in range(len(attrType))]
			applyRandomList = [[applyRandomType[x], applyRandomValue[x]] for x in range(len(applyRandomType))]
			dataDict = self.logDataDict[logID]
			itemDict = dataDict["owner_items"] if isOwnerItem else dataDict["target_items"]
			newItem = {
				"itemVnum":itemVnum,
				"itemCount":itemCount,
				"metinSlot":metinSlot,
				"attrSlot":attrList,
				"applyRandomSlot":applyRandomList,
				"refineElement":refineElement,
			}
			itemDict[itemPos] = newItem

	def ExchangeLogAppend(self, logID, ownerName, ownerGold, ownerIP, targetName, targetGold, targetIP, date):
		#import chat
		#chat.AppendChat(1,"[TEST]ExchangeLogAppend {} {} {} {} {} {} {} {}".format(logID, ownerName, ownerGold, ownerIP, targetName, targetGold, targetIP, date))

		realIpAdress = ownerIP if player.GetName() == ownerName else targetIP
		newLog = {
			"owner": ownerName,
			"owner_gold": ownerGold,
			"owner_items": {},
			"target": targetName,
			"target_gold": targetGold,
			"target_items": {}, 
			"date": date,
			"ip": realIpAdress,
			"isSelected": False,
			"itemsLoaded": False,
			"logID": logID,
		}
		self.logDataDict[logID] = newLog

	def Simulation(self):
		self.logDataDict={}
		for i in range(25):
			new_dict = {
				"owner": "OwnerPlayer{}".format(i+1),
				"owner_gold": 1000,
				"owner_items": {},
				"target": "TargetPlayer{}".format(i+1),
				"target_gold": 1000,
				"target_items": {}, 
				"date": "2022-05-06 21:47:31",
				"ip": "127.0.0.1",
				"isSelected": False,
				"itemsLoaded": False,
				"logID": i,
			}
			self.logDataDict[i] = new_dict

class ScrollBarNew(ui.Window):
	SCROLLBAR_WIDTH = 10
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
			top.LoadImage(IMG_DIR+"scrollbar_ex/scrollbar_top.tga")
			top.AddFlag("not_pick")
			top.Show()
			topScale = ui.ExpandedImageBox()
			topScale.SetParent(self)
			topScale.SetPosition(0, top.GetHeight())
			topScale.LoadImage(IMG_DIR+"scrollbar_ex/scrollbar_scale.tga")
			topScale.AddFlag("not_pick")
			topScale.Show()
			bottom = ui.ExpandedImageBox()
			bottom.SetParent(self)
			bottom.LoadImage(IMG_DIR+"scrollbar_ex/scrollbar_bottom.tga")
			bottom.AddFlag("not_pick")
			bottom.Show()
			bottomScale = ui.ExpandedImageBox()
			bottomScale.SetParent(self)
			bottomScale.LoadImage(IMG_DIR+"scrollbar_ex/scrollbar_scale.tga")
			bottomScale.AddFlag("not_pick")
			bottomScale.Show()
			middle = ui.ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage(IMG_DIR+"scrollbar_ex/scrollbar_mid.tga")
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
		self.scrollStep = 0.2
		self.SetWindowName("NONAME_ScrollBar")
	def __del__(self):
		ui.Window.__del__(self)
	def CreateScrollBar(self):
		topImage = ui.ExpandedImageBox()
		topImage.SetParent(self)
		topImage.AddFlag("not_pick")
		topImage.LoadImage(IMG_DIR+"scrollbar_ex/scroll_top.tga")
		topImage.Show()
		bottomImage = ui.ExpandedImageBox()
		bottomImage.SetParent(self)
		bottomImage.AddFlag("not_pick")
		bottomImage.LoadImage(IMG_DIR+"scrollbar_ex/scroll_bottom.tga")
		bottomImage.Show()
		middleImage = ui.ExpandedImageBox()
		middleImage.SetParent(self)
		middleImage.AddFlag("not_pick")
		middleImage.SetPosition(0, topImage.GetHeight())
		middleImage.LoadImage(IMG_DIR+"scrollbar_ex/scroll_mid.tga")
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
