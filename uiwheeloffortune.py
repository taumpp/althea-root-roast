import ui, app, item, osfInfo, localeInfo
import net
import uiToolTip

IMG_DIR = "d:/ymir work/ui/game/whell_of_fortune/"

INFO_MODE = 0

item_list = [\
	[71228,1],[71243,1],[83028,1],[83030,1],[78001,1],[78002,1],[71072,1],[71025,1],[70508,1]\
	,[50923,1],[50921,1],[50310,1],[50124,1],[50036,1],[50269,1],[50270,1],[50527,10],[50617,10],[50619,10],[50616,10],[50638,10],[50615,10],[50618,10]
]

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
	def SetTextType(self, textType):
		self.textType = textType
		for text in self.children:
			self.AddTextType(self.textType.split("#"),text)
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
			if self.textType != "":
				self.AddTextType(self.textType.split("#"),childText)
			childText.SetText(str(text))
			childText.Show()
			self.children.append(childText)
			yPosition+=self.rangeText

class MessageWindow(ui.BoardWithTitleBar):
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'okButton')
		self.Destroy()
	def Destroy(self):
		self.children = {}
		self.okButton = None
	def LoadMessage(self, itemVnum, itemCount):
		self.SetTitleName(localeInfo.WHEEL_REWARD_TITLE)
		self.SetCloseEvent(self.Close)
		self.SetSize(210,180)
		self.AddFlag("attach")
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetCenterPosition()

		item.SelectItem(itemVnum)

		multiText = MultiTextLine()
		multiText.SetParent(self)
		multiText.SetTextType("horizontal#center")
		multiText.SetPosition(95,45)
		if itemCount > 1:
			text = "%s\nx%d%s\n%s"%(localeInfo.WHEEL_REWARD_TEXT, itemCount,item.GetItemName(), localeInfo.WHEEL_REWARD_TEXT_1)
		else:
			text = "%s\n%s\n%s"%(localeInfo.WHEEL_REWARD_TEXT,item.GetItemName(), localeInfo.WHEEL_REWARD_TEXT_1)
		multiText.SetText(text)
		multiText.Show()
		self.children["multiText"] = multiText

		itemIcon = ui.ImageBox()
		itemIcon.SetParent(self)
		itemIcon.LoadImage(item.GetIconImageFileName())
		itemIcon.SetPosition(105-16,95)
		itemIcon.Show()
		self.children["itemIcon"] = itemIcon

		itemCountNumber = ui.NumberLine()
		itemCountNumber.SetParent(itemIcon)
		itemCountNumber.SetNumber(str(itemCount))
		itemCountNumber.SetPosition(20,20)
		itemCountNumber.Show()
		self.children["itemCount"] = itemCountNumber

		okBtn = ui.Button()
		okBtn.SetParent(self)
		okBtn.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		okBtn.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		okBtn.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		okBtn.SetText(localeInfo.UI_OK)
		okBtn.SetEvent(ui.__mem_func__(self.Close))
		okBtn.SetPosition(105-(okBtn.GetWidth()//2),135)
		okBtn.Show()
		self.children["okBtn"] = okBtn
		self.okButton = okBtn

		self.Show()

	def Close(self):
		self.Destroy()
		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True

class ImageBoxSpecial(ui.Window):
	def __del__(self):
		ui.Window.__del__(self)
	def Destroy(self):
		self.imageList=[]
		self.waitingTime = 0.0
		self.sleepTime = 0.0
		self.alphaValue = 0.0
		self.increaseValue = 0.0
		self.minAlpha = 0.0
		self.maxAlpha = 0.0
		self.alphaStatus = False
		self.imageIndex = 0
		self.img = None
		self.numberText = None

	def __init__(self):
		ui.Window.__init__(self)
		self.Destroy()
		self.waitingTime = 2.0
		self.alphaValue = 0.3
		self.increaseValue = 0.05
		self.minAlpha = 0.3
		self.maxAlpha = 1.0
	def SetImage(self, folder, itemVnum, itemCount):
		(x, y) = (0,0)
		if self.img != None:
			(x, y) = self.img.GetLocalPosition()
		if self.img == None:
			img = ui.ImageBox()
			img.SetParent(self)
			img.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
			img.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem)
			self.img = img
		if self.numberText == None:
			numberText = ui.NumberLine()
			numberText.SetParent(self.img)
			numberText.SetPosition(20,20)
			self.numberText = numberText

		self.numberText.SetNumber(str(itemCount))
		self.numberText.Show()

		self.img.LoadImage(folder)
		self.img.SetPosition(x, y)
		self.img.Show()

	def OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def OverInItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.SetItemToolTip(self.imageList[self.imageIndex][1])
	def Clear(self):
		self.img = None
		self.numberText = None
		self.imageList = []
	def LoadImage(self, imageFolder, itemVnum, itemCount):
		item_list = [imageFolder, itemVnum, itemCount]
		if item_list in self.imageList:
			return
		self.imageList.append(item_list)
		if self.img == None:
			self.SetImage(imageFolder, itemVnum, itemCount)
	def GetNextImage(self, listIndex):
		if listIndex >= len(self.imageList):
			if len(self.imageList) > 0:
				return (0,self.imageList[0][0],self.imageList[0][1],self.imageList[0][2])
			return (0,"",0,0)
		return (listIndex, self.imageList[listIndex][0],self.imageList[listIndex][0], self.imageList[listIndex][2])
	def OnUpdate(self):
		if len(self.imageList) <= 1:
			self.imageIndex=0
			return
		elif self.sleepTime > app.GetTime():
			return
		if self.alphaStatus == True:
			self.alphaValue -= self.increaseValue
			if self.alphaValue < self.minAlpha:
				self.alphaValue = self.minAlpha
				self.alphaStatus = False
				(imageIndex, imageFolder, itemVnum, itemCount) = self.GetNextImage(self.imageIndex+1)
				if imageFolder != "":
					self.SetImage(imageFolder, itemVnum, itemCount)
				self.imageIndex = imageIndex
		else:
			self.alphaValue += self.increaseValue
			if self.alphaValue > self.maxAlpha:
				self.alphaStatus = True
				self.sleepTime = app.GetTime()+self.waitingTime
		if self.img != None:
			self.img.SetAlpha(self.alphaValue)

class WheelofFortune(ui.BoardWithTitleBar):
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.Destroy()
		self.CreateGame()
	def Destroy(self):
		self.children = {}
		self.circleRotation = 0
		self.wheelStep = 0
		self.giftIndex = 0
		self.showAnimation = True
	def Open(self):
		self.Show()
	def Close(self):
		self.CloseMessageWindow()

		if self.wheelStep > 0:
			self.wheelStep = 0
			self.circleRotation = self.wheelRotation
			self.children["wheelCircle"].SetRotation(self.circleRotation)
			self.UpdateSingleFortune()
			self.SendServerDone()

		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True
		
	def __CreateGameTypeToolTip(self, title, descList):
		toolTip = uiToolTip.ToolTip()
		toolTip.SetTitle(title)
		toolTip.AppendSpace(7)

		for desc in descList:
			toolTip.AutoAppendTextLine(desc)

		toolTip.AlignHorizonalCenter()
		toolTip.SetTop()
		return toolTip
		
	def CreateGame(self):
		self.SetSize(437+12,33+421)
		self.SetCenterPosition()
		self.SetTitleName(localeInfo.WHEEL_GAME_TITLE)
		self.SetCloseEvent(self.Close)
		self.AddFlag("movable")
		self.AddFlag("attach")
		self.AddFlag("float")

		board = ui.ImageBox()
		board.SetParent(self)
		#board.AddFlag("not_pick")
		board.LoadImage(IMG_DIR+"wallpaper.tga")
		board.SetPosition(5,28)
		board.Show()
		self.children["board"] = board

		fortuneImg = ui.ImageBox()
		fortuneImg.SetParent(board)
		fortuneImg.AddFlag("not_pick")
		fortuneImg.LoadImage(IMG_DIR+"fortune.tga")
		fortuneImg.SetPosition(28,23)
		fortuneImg.Show()
		self.children["fortuneImg"] = fortuneImg

		fortuneSingle = ui.ExpandedImageBox()
		fortuneSingle.SetParent(board)
		fortuneSingle.AddFlag("not_pick")
		fortuneSingle.LoadImage(IMG_DIR+"single.tga")
		fortuneSingle.SetPosition(164,38)
		fortuneSingle.Show()
		self.children["fortuneSingle"] = fortuneSingle

		wheelCircle = ui.ExpandedImageBox()
		wheelCircle.SetParent(board)
		wheelCircle.LoadImage(IMG_DIR+"circle.tga")
		wheelCircle.AddFlag("not_pick")
		wheelCircle.SetPosition(155,136)
		wheelCircle.Show()
		self.children["wheelCircle"] = wheelCircle

		wheelBtn = ui.Button()
		wheelBtn.SetParent(board)
		wheelBtn.SetUpVisual(IMG_DIR+"wheel_0.tga")
		wheelBtn.SetOverVisual(IMG_DIR+"wheel_1.tga")
		wheelBtn.SetDownVisual(IMG_DIR+"wheel_2.tga")
		wheelBtn.SetPosition(160,155)
		wheelBtn.SetEvent(ui.__mem_func__(self.StartWheel))
		wheelBtn.Show()
		self.children["wheelBtn"] = wheelBtn

		if INFO_MODE:
			debugText = ui.MultiTextLine()
			debugText.SetParent(board)
			debugText.SetPosition(180,140+wheelCircle.GetHeight())
			debugText.Show()
			self.children["debugText"] = debugText

		event = lambda index = 0 : ui.__mem_func__(self.SetAnimationStatus)(index)
		self.children["animationCheckBox"] = ui.CheckBoxNew(board, 10, 10, event)

		animationText = ui.TextLine()
		animationText.SetParent(board)
		animationText.SetText(localeInfo.WHEEL_GAME_SKIP_ANIMATION)
		animationText.SetOutline()
		animationText.SetPosition(10+self.children["animationCheckBox"].GetWidth()+10,10)
		animationText.Show()
		self.children["animationText"] = animationText

		itemPosition = [[205,65], [275,90], [320,160], [320,235], [275,290], [205,320], [130,295], [90,235], [85,160], [130,90]]
		for j in range(len(itemPosition)):
			wheelItem = ImageBoxSpecial()
			wheelItem.SetParent(board)
			wheelItem.SetPosition(itemPosition[j][0],itemPosition[j][1])
			wheelItem.SetSize(32,32)
			wheelItem.Show()
			self.children["wheelItem%d"%j] = wheelItem
			
		infoBtn = ui.Button()
		infoBtn.SetParent(board)
		infoBtn.SetUpVisual(IMG_DIR+"info_0.tga")
		infoBtn.SetOverVisual(IMG_DIR+"info_1.tga")
		infoBtn.SetDownVisual(IMG_DIR+"info_2.tga")
		infoBtn.SetPosition(402,5)
		infoBtn.Show()
		self.children["infoBtn"] = infoBtn
		
		infoText = [
			"Using a special seal you have the possibility to use the Wheel of Fortune.",
			"Special seal will allow you to turn the wheel only once. Can only be purchased in the Itemshop.",
			"Compete for interesting prizes, such as completely unique costumes that you can't get anywhere else."
		]
		self.infoTooltip = self.__CreateGameTypeToolTip("Wheel of fortune", infoText)
		self.children["infoBtn"].SetToolTipWindow(self.infoTooltip)
			
		self.SetTrailerMode()

	def SetAnimationStatus(self, key):
		value = 0
		if not self.children["animationCheckBox"].GetCheck():
			value = 1
		self.children["animationCheckBox"].SetCheck(value)
		if value == 1:
			self.showAnimation = False
		else:
			self.showAnimation = True

	def GetGiftRotation(self, giftIndex):
		if giftIndex == 0:
			if app.GetRandom(0,1) == 0:
				return 341+app.GetRandom(4,18)
			else:
				return app.GetRandom(4,19)
		else:
			listofIndex = [0,20,58,94,126,160,196,232,268,304,341]
			return listofIndex[giftIndex]+app.GetRandom(4,28)

	def CloseMessageWindow(self):
		if "message_window" in self.children:
			msgWindow = self.children["message_window"]
			if msgWindow != None:
				msgWindow.Hide()
				msgWindow = None

	def GetGiftData(self, itemVnum, itemCount):
		self.CloseMessageWindow()
		self.children["message_window"] = MessageWindow()
		self.children["message_window"].LoadMessage(itemVnum, itemCount)

	def GetRotationToIndex(self, rotation):
		if rotation >= 341 and rotation <= 360 or rotation <= 20:
			return 0
		elif rotation >= 305 and rotation <= 305+38:
			return 9
		elif rotation >= 269 and rotation <= 269+38:
			return 8
		elif rotation >= 233 and rotation <= 233+38:
			return 7
		elif rotation >= 197 and rotation <= 197+38:
			return 6
		elif rotation >= 161 and rotation <= 161+38:
			return 5
		elif rotation >= 127 and rotation <= 127+38:
			return 4
		elif rotation >= 95 and rotation <= 95+38:
			return 3
		elif rotation >= 59 and rotation <= 59+38:
			return 2
		elif rotation >= 21 and rotation <= 21+38:
			return 1
		return 0

	def SetTrailerMode(self):
		for j in range(10):
			self.children["wheelItem%d"%j].Clear()
			for x in range(10):
				itemData = item_list[app.GetRandom(0,len(item_list)-1)]
				item.SelectItem(itemData[0])
				self.children["wheelItem%d"%j].LoadImage(item.GetIconImageFileName(), itemData[0], itemData[1])

	def SendServerDone(self):
		net.SendChatPacket("/wheel_of_fortune done")

	def Simulation(self):
		itemList = []
		while True:
			itemData = item_list[app.GetRandom(0,len(item_list)-1)]
			if not itemData in itemList:
				itemList.append(itemData)
			if len(itemList) == 10:
				break
		text = ""
		for j in range(len(itemList)):
			text+=str(itemList[j][0])
			text+= "|"
			text+=str(itemList[j][1])
			text+="#"
		self.SetItemData(str(text))
		self.OnSetWheel(app.GetRandom(0,9))

	def StartWheel(self):
		net.SendChatPacket("/wheel_of_fortune start")
		#self.Simulation()

	def SetItemData(self, data):
		for j in range(10):
			self.children["wheelItem%d"%j].Clear()

		index = 0
		splitData = data.split("#")
		for splitText in splitData:
			splitItem = splitText.split("|")
			if len(splitItem) == 2:
				item.SelectItem(int(splitItem[0]))
				self.children["wheelItem%d"%index].LoadImage(item.GetIconImageFileName(), int(splitItem[0]), int(splitItem[1]))
				index += 1

	def UpdateSingleFortune(self):
		single_pos = [[164,38,0], [230,63,35], [270,120,70], [266,188,110], [226,241,142], [160,262,180], [98,243,215], [56,189,250], [53,119,285], [96,61,324]]
		index = self.GetRotationToIndex(self.circleRotation)
		self.children["fortuneSingle"].SetRotation(single_pos[index][2])
		self.children["fortuneSingle"].SetPosition(single_pos[index][0],single_pos[index][1])

	def OnSetWheel(self, giftIndex):
		self.giftIndex = giftIndex
		self.wheelRotation = self.GetGiftRotation(giftIndex)

		if self.showAnimation:
			self.wheelStep = app.GetRandom(10, 15)
		else:
			self.wheelStep = 0
			self.circleRotation = self.wheelRotation
			self.children["wheelCircle"].SetRotation(self.circleRotation)
			self.UpdateSingleFortune()
			self.SendServerDone()

		if INFO_MODE:
			self.children["debugText"].SetText("giftIndex: %d\n giftRotation: %d\nWheel Step: %d\nRotation %d\nIncrease Rotation: %.2f"%(self.giftIndex,self.wheelRotation,self.wheelStep,self.circleRotation, 0))

	def OnUpdate(self):
		if self.wheelStep > 0:
			increaseValue = 0.5 * float((self.wheelStep*2))
			self.circleRotation += increaseValue
			self.children["wheelCircle"].SetRotation(self.circleRotation)
			self.UpdateSingleFortune()

			if INFO_MODE:
				self.children["debugText"].SetText("giftIndex: %d\n giftRotation: %d\nWheel Step: %d\nRotation %d\nIncrease Rotation: %.2f"%(self.giftIndex,self.wheelRotation,self.wheelStep,self.circleRotation, increaseValue))

			if self.circleRotation >= 360:
				if self.wheelStep > 1:
					self.wheelStep-= 1
				self.circleRotation= 0

			if self.wheelStep == 1 and self.wheelRotation == self.circleRotation:
				self.wheelStep -= 1
				self.SendServerDone()
				return

	def OnPressEscapeKey(self):
		self.Close()
		return True