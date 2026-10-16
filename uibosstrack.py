#static
import ui, localeInfo

#dynamic
import app, net, nonplayer, item
import servergamedata

IMG_DIR = "d:/ymir work/ui/game/boss_track/"

# Presentation only. Every tracker point (id, mob, map, position, channels,
# respawn) comes from the server catalogue (althea/server boss_track.txt via
# root/servergamedata.py, generated). A point is listed under the title of its
# map and drawn with its mob's portrait, so a new or re-aimed server point needs
# no edit here; only a new map or a new boss needs a title or portrait.
TRACK_MAP_TITLES = (
	(64, localeInfo.BOSS_TRACK_ORC),
	(63, localeInfo.BOSS_TRACK_DESERT),
	(61, localeInfo.BOSS_TRACK_SOHAN),
	(62, localeInfo.BOSS_TRACK_FLAME),
	(71, localeInfo.BOSS_TRACK_SPIDER2),
	(65, localeInfo.BOSS_TRACK_HWANG),
	(68, localeInfo.BOSS_TRACK_RED_WOOD),
	(72, localeInfo.BOSS_TRACK_EXIL1),
	(73, localeInfo.BOSS_TRACK_EXIL2),
)

# mob vnum -> (portrait in IMG_DIR, difficulty label)
TRACK_MOB_PRESENTATION = {
	691 : ("691.png", localeInfo.BOSS_TRACK_EASY),
	791 : ("791.png", localeInfo.BOSS_TRACK_NORMAL),
	1191 : ("1191.png", localeInfo.BOSS_TRACK_NORMAL),
	# Mighty Ice Witch has no own portrait; it shares the Ice Witch one.
	1192 : ("1191.png", localeInfo.BOSS_TRACK_DIFFICULT),
	1304 : ("1304.png", localeInfo.BOSS_TRACK_NORMAL),
	1901 : ("1901.png", localeInfo.BOSS_TRACK_NORMAL),
	2091 : ("2091.png", localeInfo.BOSS_TRACK_EASY),
	2191 : ("2191.png", localeInfo.BOSS_TRACK_NORMAL),
	2206 : ("2206.png", localeInfo.BOSS_TRACK_NORMAL),
	2291 : ("2291.png", localeInfo.BOSS_TRACK_DIFFICULT),
	# Giant Ghost Tree has no own portrait; it shares the Ghost Tree Lord one.
	2306 : ("2307.png", localeInfo.BOSS_TRACK_DIFFICULT),
	2307 : ("2307.png", localeInfo.BOSS_TRACK_DIFFICULT),
	2492 : ("2492.png", localeInfo.BOSS_TRACK_DIFFICULT),
}


def _TrackEntry(trackId):
	(mobIdx, mapIndex, x, y, channels, respawn, live) = servergamedata.BOSS_TRACK[trackId]
	(image, difficulty) = TRACK_MOB_PRESENTATION.get(mobIdx, ("%d.png" % mobIdx, localeInfo.BOSS_TRACK_NORMAL))
	return {
		"id" : trackId,
		"mobIdx" : mobIdx,
		"image" : image,
		"difficulty" : difficulty,
		"x" : x,
		"y" : y,
		# Every public channel the server lists for the point (CH1-CH7 in
		# production); the channel panel pages through them three at a time.
		"ch_data" : [[channel, 0] for channel in channels],
		"drop" : [list(entry) for entry in servergamedata.BOSS_DROPS.get(mobIdx, ())],
	}


def _BuildTrackData():
	# A point without a matching server spawn is never armed by the game, so it
	# is not listed. Points on a map without a title are grouped at the end.
	live = [trackId for (trackId, track) in sorted(servergamedata.BOSS_TRACK.items()) if track[6]]
	groups = []
	titled = set()
	for (mapIndex, name) in TRACK_MAP_TITLES:
		titled.add(mapIndex)
		bossList = [_TrackEntry(trackId) for trackId in live if servergamedata.BOSS_TRACK[trackId][1] == mapIndex]
		if bossList:
			groups.append({"name" : name, "boss_list" : bossList})
	extra = [_TrackEntry(trackId) for trackId in live if servergamedata.BOSS_TRACK[trackId][1] not in titled]
	if extra:
		groups.append({"name" : localeInfo.BOSS_TRACK_TITLE, "boss_list" : extra})
	return groups


track_data = _BuildTrackData()

class Window(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.__LoadWindow()
	def Destroy(self):
		self.__children = {}
	def __LoadWindow(self):
		self.Destroy()

		self.AddFlag("movable")
		self.AddFlag("attach")
		self.AddFlag("float")
		self.SetTitleName(localeInfo.BOSS_TRACK_TITLE)
		self.SetCloseEvent(self.Close)

		bg = CreateWindow(ui.ImageBox(), self, (8, 30), IMG_DIR + "bg_system.png")
		self.__children["bg"] = bg

		self.SetSize(8 + bg.GetWidth() + 8, 30 + bg.GetHeight() + 8)
		self.SetCenterPosition()

		renderWnd = CreateWindow(ui.Window(), bg, (3, 3), "", "", (212, 333))
		renderWnd.SetInsideRender(True)
		renderWnd.OnMouseWheel = ui.__mem_func__(self.OnMouseWheelLeft)
		self.__children["renderWnd"] = renderWnd

		renderWndChildren = {}
		global track_data
		yPos = 0
		for bossData in track_data:
			idx = track_data.index(bossData)

			titleImg = CreateWindow(ui.ExpandedImageBox(), renderWnd, (0, yPos, True), IMG_DIR + "boss_bar.png")
			renderWndChildren["titleImg"+str(idx)] = titleImg

			titleText = CreateWindow(ui.TextLine(), titleImg, (7, 5), bossData["name"])
			titleText.SetPackedFontColor(0xFFFFB975)
			renderWndChildren["titleText"+str(idx)] = titleText

			yPos += titleImg.GetHeight() + 3

			for boss in bossData["boss_list"]:
				id = boss["id"]

				btnImg = CreateWindow(ui.RadioButton(), renderWnd, (0, yPos, True))
				btnImg.SetUpVisual(IMG_DIR + "btn_boss_0.png")
				btnImg.SetOverVisual(IMG_DIR + "btn_boss_1.png")
				btnImg.SetDownVisual(IMG_DIR + "btn_boss_2.png")
				btnImg.SAFE_SetEvent(self.__ClickBoss, id)
				renderWndChildren["btnImg"+str(id)] = btnImg

				bossImg = CreateWindow(ui.ExpandedImageBox(), btnImg, (1, 1), IMG_DIR + boss["image"])
				bossImg.AddFlag("not_pick")
				renderWndChildren["bossImg"+str(id)] = bossImg

				nameText = CreateWindow(ui.TextLine(), btnImg, (73, 8), nonplayer.GetMonsterName(boss["mobIdx"]))
				nameText.SetPackedFontColor(0xFFFFB975)
				renderWndChildren["nameText"+str(id)] = nameText

				posText = CreateWindow(ui.TextLine(), btnImg, (72, 22), localeInfo.BOSS_TRACK_CORD_TEXT % (boss["x"], boss["y"]))
				renderWndChildren["posText"+str(id)] = posText

				yPos += btnImg.GetHeight() + 2

			if len(bossData["boss_list"]):
				yPos += 1
		self.__children["renderWndChildren"] = renderWndChildren

		scrollBar = CreateWindow(ScrollBar(), bg, (219, 3))
		scrollBar.SetScrollBarSize(333)
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__ChangePos))
		self.__children["scrollBar"] = scrollBar

		windowHeight = renderWnd.GetHeight()

		if yPos > windowHeight:
			self.__children["scrollLen"] = yPos-windowHeight
			scrollBar.SetMiddleBarSize(float(windowHeight-5)/float(yPos))
		else:
			scrollBar.SetMiddleBarSize(1.0)

		# Right Table

		self.__children["rightTitleImg"] = CreateWindow(ui.ExpandedImageBox(), bg, (238, 2), IMG_DIR + "info_bar.png")

		self.__children["rightTitleText"] = CreateWindow(ui.TextLine(), self.__children["rightTitleImg"], (10, 5), localeInfo.BOSS_TRACK_MOB_INFO)
		self.__children["rightTitleText"].SetPackedFontColor(0xFFFFB975)


		self.__children["rightLevelImg"] = CreateWindow(ui.ExpandedImageBox(), bg, (238, 2 + 24), IMG_DIR + "info_line.png")

		self.__children["rightLevelInfo"] = CreateWindow(ui.TextLine(), self.__children["rightLevelImg"], (7, 2), localeInfo.BOSS_TRACK_LEVEL)
		self.__children["rightLevelInfo"].SetOutline()
		self.__children["rightLevelText"] = CreateWindow(ui.TextLine(), self.__children["rightLevelImg"], (140, 2), "0", "horizontal:center")
		self.__children["rightLevelText"].SetOutline()
		self.__children["rightLevelText"].Hide()


		self.__children["rightHpImg"] = CreateWindow(ui.ExpandedImageBox(), bg, (238, 2 + 24 + 17), IMG_DIR + "info_line.png")
		
		self.__children["rightHpInfo"] = CreateWindow(ui.TextLine(), self.__children["rightHpImg"], (7, 2), localeInfo.BOSS_TRACK_HP)
		self.__children["rightHpInfo"].SetOutline()
		self.__children["rightHpText"] = CreateWindow(ui.TextLine(), self.__children["rightHpImg"], (140, 2), "0", "horizontal:center")
		self.__children["rightHpText"].SetOutline()
		self.__children["rightHpText"].Hide()

		self.__children["rightDifficultyImg"] = CreateWindow(ui.ExpandedImageBox(), bg, (238, 2 + 24 + 17 + 17), IMG_DIR + "info_line.png")

		self.__children["rightDifficultyInfo"] = CreateWindow(ui.TextLine(), self.__children["rightDifficultyImg"], (7, 2), localeInfo.BOSS_TRACK_DIFF)
		self.__children["rightDifficultyInfo"].SetOutline()

		self.__children["rightDifficultyText"] = CreateWindow(ui.TextLine(), self.__children["rightDifficultyImg"], (140, 2), "0", "horizontal:center")
		self.__children["rightDifficultyText"].SetOutline()
		self.__children["rightDifficultyText"].Hide()


		self.__children["rightChTitleImg"] = CreateWindow(ui.ExpandedImageBox(), bg, (238, 78), IMG_DIR + "info_bar.png")

		self.__children["rightChTitleText"] = CreateWindow(ui.TextLine(), self.__children["rightChTitleImg"], (10, 5), localeInfo.BOSS_TRACK_CH)
		self.__children["rightChTitleText"].SetPackedFontColor(0xFFFFB975)

		rightBackBtn = CreateWindow(ui.Button(), bg, (243, 120))
		rightBackBtn.SetUpVisual(IMG_DIR + "back_0.png")
		rightBackBtn.SetOverVisual(IMG_DIR + "back_1.png")
		rightBackBtn.SetDownVisual(IMG_DIR + "back_2.png")
		rightBackBtn.SetDisableVisual(IMG_DIR + "back_2.png")
		rightBackBtn.SAFE_SetEvent(self.__ClickDirection, "back")
		self.__children["rightBackBtn"] = rightBackBtn

		rightNextBtn = CreateWindow(ui.Button(), bg, (418, 120))
		rightNextBtn.SetUpVisual(IMG_DIR + "front_0.png")
		rightNextBtn.SetOverVisual(IMG_DIR + "front_1.png")
		rightNextBtn.SetDownVisual(IMG_DIR + "front_2.png")
		rightNextBtn.SetDisableVisual(IMG_DIR + "front_2.png")
		rightNextBtn.SAFE_SetEvent(self.__ClickDirection, "next")
		self.__children["rightNextBtn"] = rightNextBtn

		for j in range(3):
			chImg = CreateWindow(ui.ExpandedImageBox(), bg, (264 + (j * 50), 103), IMG_DIR + "ch_slot.png")
			self.__children["chImg" + str(j)] = chImg

			chText = CreateWindow(ui.TextLine(), chImg, (chImg.GetWidth() // 2, 6), "", "horizontal:center")
			chText.SetOutline()
			chText.Hide()
			self.__children["chText" + str(j)] = chText

			chTestData = [["None", 0xFFFF5555], ["Alive", 0xFFB4FF00], ["Dead", 0xFFFF5555]]

			chStatusText = CreateWindow(ui.TextLine(), chImg, (chImg.GetWidth() // 2, 27), "", "horizontal:center")
			chStatusText.SetPackedFontColor(chTestData[j][1])
			chStatusText.SetOutline()
			chStatusText.Hide()
			self.__children["chStatusText" + str(j)] = chStatusText

			chTime = CreateWindow(ui.TextLine(), chImg, (chImg.GetWidth() // 2, 32), "", "horizontal:center")
			chTime.SetOutline()
			chTime.Hide()
			self.__children["chTime" + str(j)] = chTime

		self.__children["rightDropTitleImg"] = CreateWindow(ui.ExpandedImageBox(), bg, (238, 156), IMG_DIR + "info_bar.png")

		self.__children["rightDropTitleText"] = CreateWindow(ui.TextLine(), self.__children["rightDropTitleImg"], (10, 5), localeInfo.BOSS_TRACK_DROP)
		self.__children["rightDropTitleText"].SetPackedFontColor(0xFFFFB975)

		rightDropBg = CreateWindow(ui.ExpandedImageBox(), bg, (238, 180), IMG_DIR + "bg_drop_slot.png")
		self.__children["rightDropBg"] = rightDropBg

		rightDropWindow = CreateWindow(ui.Window(), rightDropBg, (15, 12), "", "", (5 * 32, 4 * 32))
		rightDropWindow.SetInsideRender(True)
		rightDropWindow.OnMouseWheel = ui.__mem_func__(self.OnMouseWheelRight)
		self.__children["rightDropWindow"] = rightDropWindow

		rightScrollBar = CreateWindow(ScrollBar(), rightDropBg, (189, 2))
		rightScrollBar.SetScrollBarSize(154)
		rightScrollBar.SetScrollEvent(ui.__mem_func__(self.__ChangeRightPos))
		rightScrollBar.SetMiddleBarSize(1.0)
		self.__children["rightScrollBar"] = rightScrollBar

		self.Clear()
		#self.SetServerData("0:1?-1.2?0!", True)
	
	def Clear(self):
		global track_data
		for bossData in track_data:
			for boss in bossData["boss_list"]:
				for j in range(len(boss["ch_data"])):
					boss["ch_data"][j][1] = 0

	def SetServerData(self, data, isClean):
		if isClean:
			self.Clear()
		if data.find(":") == -1:
			return

		currentID = self.__children["currentID"] if "currentID" in self.__children else -1

		#0:1?0.2?0!

		global track_data

		for bossSplit in data.split("!"):
			bossData = bossSplit.split(":")
			if len(bossData) != 2:
				continue
			id = int(bossData[0])
			for bossChData in bossData[1].split("."):
				ch = int(bossChData.split("?")[0])
				isOk = False
				for bossInfo in track_data:
					if isOk:
						break
					for boss in bossInfo["boss_list"]:
						if isOk:
							break
						if boss["id"] == id:
							for j in range(len(boss["ch_data"])):
								if boss["ch_data"][j][0] == ch:
									val = int(bossChData.split("?")[1])
									if val > 1:
										val += app.GetGlobalTimeStamp()
									boss["ch_data"][j][1] = val
									isOk = True
									break

			if currentID == int(bossData[0]):
				self.RefreshRightTable()

	def __ClickBoss(self, id):
		renderWndChildren = self.__children["renderWndChildren"]
		for key, data in renderWndChildren.items():
			if isinstance(data, ui.RadioButton):
				data.SetUp()
		renderWndChildren["btnImg"+str(id)].Down()
		self.__children["currentID"] = id
		self.__children["currentCHIdx"] = 0
		self.RefreshRightTable(True)

	def RefreshRightTable(self, reset_drop_scroll=False):
		id = self.__children["currentID"]
		bossData = self.GetBossData(id)
		if not bossData:
			return

		mobIdx = bossData["mobIdx"]

		self.__children["rightLevelText"].SetText(str(nonplayer.GetMonsterLevel(mobIdx)))
		self.__children["rightLevelText"].Show()

		self.__children["rightHpText"].SetText(NumberToDecimalString(nonplayer.GetMonsterMaxHP(mobIdx)))
		self.__children["rightHpText"].Show()

		self.__children["rightDifficultyText"].SetText(bossData["difficulty"])
		self.__children["rightDifficultyText"].Show()
		
		rightDropWindow = self.__children["rightDropWindow"]

		itemIconList = []
		dropList = bossData["drop"] if "drop" in bossData else []
		
		gridImg = CreateWindow(ui.ExpandedImageBox(), rightDropWindow, (0, 0, True), IMG_DIR + "grid.png")
		gridImg.AddFlag("not_pick")
		itemIconList.append(gridImg)
		
		yTotal = 0
		grid = Grid(5, 300)
		for itemData in dropList:
			item.SelectItem(itemData[0])
			pos = grid.find_blank(*item.GetItemSize())
			if pos == -1:
				continue
			grid.put(pos, *item.GetItemSize())
			(x, y) = calculatePos(pos, 4)

			if yTotal == 0 or yTotal < y + (32 * item.GetItemSize()[1]):
				yTotal = y + (32 * item.GetItemSize()[1])

			img = CreateWindow(ui.ExpandedImageBox(), rightDropWindow, (x, y, True), item.GetIconImageFileName())
			itemIconList.append(img)
			if itemData[1] > 1:
				countText = CreateWindow(ui.NumberLine(), img, (28, 22), str(itemData[1]), "horizontal:right")
				itemIconList.append(countText)
		self.__children["itemIconList"] = itemIconList

		scrollBar = self.__children["rightScrollBar"]
		windowHeight = rightDropWindow.GetHeight()
		if yTotal > windowHeight:
			self.__children["scrollLenRight"] = yTotal-windowHeight
			scrollBar.SetMiddleBarSize(float(windowHeight-5)/float(yTotal))
		else:
			self.__children["scrollLenRight"] = 0
			scrollBar.SetMiddleBarSize(1.0)
		if reset_drop_scroll:
			scrollBar.SetPos(0.0)
		self.__ChangeRightPos()
		self.RefreshChannels(bossData["ch_data"])

	def RefreshChannels(self, chData):
		scrollBar = self.__children["rightScrollBar"]
		currentCHIdx = self.__children["currentCHIdx"]

		for j in range(3):
			chImg = self.__children["chImg" + str(j)]
			idx = j + currentCHIdx

			if idx > len(chData):
				chImg.Hide()
				return
			else:
				chImg.Show()

			chText = self.__children["chText" + str(j)]
			chTime = self.__children["chTime" + str(j)]
			chStatusText = self.__children["chStatusText" + str(j)]

			chTestData = [[localeInfo.BOSS_TRACK_NONE, 0xFFFF5555], [localeInfo.BOSS_TRACK_VIVO, 0xFFB4FF00], [localeInfo.BOSS_TRACK_MUERTO, 0xFFFF5555]]

			try:
				data = chData[idx]
			except:
				chImg.Hide()
				continue

			chText.SetText("CH"+str(data[0]))
			chText.Show()

			chStatusText.Show()

			if data[1] == 0:
				chStatusText.SetText(chTestData[0][0])
				chStatusText.SetPackedFontColor(chTestData[0][1])
				chStatusText.SetPosition(chImg.GetWidth() // 2, 27)
			
				chTime.Hide()
				
			elif data[1] == -1:
				chStatusText.SetText(chTestData[1][0])
				chStatusText.SetPackedFontColor(chTestData[1][1])
				chStatusText.SetPosition(chImg.GetWidth() // 2, 27)
			
				chTime.Hide()
			else:
				chStatusText.SetText(chTestData[2][0])
				chStatusText.SetPackedFontColor(chTestData[2][1])
				chStatusText.SetPosition(chImg.GetWidth() // 2, 21)

				leftTime = data[1] - app.GetGlobalTimeStamp()
				if leftTime < 0:
					self.SetServerData("{}:{}?{}!".format(self.__children["currentID"], data[0], -1), 0)
					return

				chTime.SetText(FormatTime(leftTime))
				chTime.Show()

	def OnUpdate(self):
		bossData = self.GetBossData(self.__children["currentID"] if "currentID" in self.__children else -1)
		if not bossData:
			return
		lastRefresh = self.__children["lastRefresh"] if "lastRefresh" in self.__children else 0.0
		if lastRefresh > app.GetTime():
			return
		self.__children["lastRefresh"] = app.GetTime() + 1.0
		self.RefreshChannels(bossData["ch_data"])

	def __ClickDirection(self, direction):
		currentCHIdx = self.__children["currentCHIdx"]
		if direction == "back":
			if currentCHIdx - 1 < 0:
				return
			currentCHIdx -= 1
		else:
			bossData = self.GetBossData(self.__children["currentID"])
			if not bossData:
				return
			elif currentCHIdx + 1 > len(bossData["ch_data"]) - 3:
				return
			currentCHIdx+=1 
		self.__children["currentCHIdx"] = currentCHIdx
		self.RefreshRightTable()

	def __ChangeRightPos(self):
		itemIconList = self.__children["itemIconList"] if "itemIconList" in self.__children else []
		scrollBar = self.__children["rightScrollBar"] if "rightScrollBar" in self.__children else None
		basePos = scrollBar.GetPos() * (self.__children["scrollLenRight"] if "scrollLenRight" in self.__children else 0)
		for child in itemIconList:
			if isinstance(child, ui.ExpandedImageBox):
				(ex, ey) = child.exPos
				child.SetPosition(ex, ey - basePos)

	def __ChangePos(self):
		renderWndChildren = self.__children["renderWndChildren"] if "renderWndChildren" in self.__children else {}
		scrollBar = self.__children["scrollBar"] if "scrollBar" in self.__children else None
		basePos = scrollBar.GetPos() * (self.__children["scrollLen"] if "scrollLen" in self.__children else 0)
		for key, child in renderWndChildren.items():
			(ex, ey) = child.exPos
			if ey != 0 or key.find("titleImg") != -1:
				child.SetPosition(ex, ey - basePos)
	
	def OnMouseWheelRight(self, nLen):
		scrollBar = self.__children["rightScrollBar"] if "rightScrollBar" in self.__children else None
		if scrollBar:
			if nLen > 0:
				scrollBar.OnUp()
			else:
				scrollBar.OnDown()
			return True
		return False
	def OnMouseWheelLeft(self, nLen):
		scrollBar = self.__children["scrollBar"] if "scrollBar" in self.__children else None
		if scrollBar:
			if nLen > 0:
				scrollBar.OnUp()
			else:
				scrollBar.OnDown()
			return True
		return False
	def GetBossData(self, id):
		global track_data
		for bossData in track_data:
			for boss in bossData["boss_list"]:
				if boss["id"] == id:
					return boss
		return None
	def Open(self):
		import chat
		if not (self.__children["packetLoad"] if "packetLoad" in self.__children else 0):
			self.__children["packetLoad"] = 1
			net.SendChatPacket("/boss_track load")
		self.Show()
		self.SetTop()
	def Close(self):
		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True

def calculatePos(pos, maxWidth):
	(x , y) = (0, 0)
	while True:
		if pos <= maxWidth:
			if pos < 0:
				pos = 0
			x = 32*pos
			break
		else:
			pos -= maxWidth+1
			y+=32
	return (x, y)

def FormatTime(seconds):
	if seconds <= 0:
		return "0s"
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	text = ""
	if d > 0:
		text+="{}d".format(d)
	if h > 0:
		text+="{}h".format(h)
	if m > 0:
		text+="{}m".format(m)
	if s > 0:
		text+="{}s".format(s)
	return text if len(text) > 0 else "0s"

def NumberToDecimalString(n):
	return str('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))

def CreateWindow(window, parent, windowPos, windowArgument = "", windowPositionRule = "", windowSize = (-1, -1), windowFontName = -1):
	window.SetParent(parent)
	window.SetPosition(*windowPos)
	if windowSize != (-1, -1):
		window.SetSize(*windowSize)
	if windowPositionRule:
		splitList = windowPositionRule.split(":")
		if len(splitList) == 2:
			(type, mode) = (splitList[0], splitList[1])
			if type == "horizontal":
				if isinstance(window, ui.TextLine):
					if mode == "center":
						window.SetHorizontalAlignCenter()
					elif mode == "right":
						window.SetHorizontalAlignRight()
					elif mode == "left":
						window.SetHorizontalAlignLeft()
				else:
					if mode == "center":
						window.SetWindowHorizontalAlignCenter()
					elif mode == "right":
						window.SetWindowHorizontalAlignRight()
					elif mode == "left":
						window.SetWindowHorizontalAlignLeft()
			elif type == "vertical":
				if isinstance(window, ui.TextLine):
					if mode == "center":
						window.SetVerticalAlignCenter()
					elif mode == "top":
						window.SetVerticalAlignTop()
					elif mode == "bottom":
						window.SetVerticalAlignBottom()
				else:
					if mode == "top":
						window.SetWindowVerticalAlignTop()
					elif mode == "center":
						window.SetWindowVerticalAlignCenter()
					elif mode == "bottom":
						window.SetWindowVerticalAlignBottom()
	if windowArgument:
		if isinstance(window, ui.TextLine):
			if windowFontName != -1:
				window.SetFontName(windowFontName)
			window.SetText(windowArgument)
		elif isinstance(window, ui.NumberLine):
			window.SetNumber(windowArgument)
		elif isinstance(window, ui.ExpandedImageBox) or isinstance(window, ui.ImageBox):
			window.LoadImage(windowArgument if windowArgument.find("gr2") == -1 else "icon/item/27995.tga")
	window.Show()
	return window

class ScrollBar(ui.Window):
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
			top.LoadImage(IMG_DIR+"scrollbar/scroll_top.png")
			top.AddFlag("not_pick")
			top.Show()
			topScale = ui.ExpandedImageBox()
			topScale.SetParent(self)
			topScale.SetPosition(0, top.GetHeight())
			topScale.LoadImage(IMG_DIR+"scrollbar/scroll_scale.png")
			topScale.AddFlag("not_pick")
			topScale.Show()
			bottom = ui.ExpandedImageBox()
			bottom.SetParent(self)
			bottom.LoadImage(IMG_DIR+"scrollbar/scroll_bottom.png")
			bottom.AddFlag("not_pick")
			bottom.Show()
			bottomScale = ui.ExpandedImageBox()
			bottomScale.SetParent(self)
			bottomScale.LoadImage(IMG_DIR+"scrollbar/scroll_scale.png")
			bottomScale.AddFlag("not_pick")
			bottomScale.Show()
			middle = ui.ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage(IMG_DIR+"scrollbar/scrollbar_mid.png")
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
		topImage.LoadImage(IMG_DIR+"scrollbar/scrollbar_top.png")
		topImage.Show()
		bottomImage = ui.ExpandedImageBox()
		bottomImage.SetParent(self)
		bottomImage.AddFlag("not_pick")
		bottomImage.LoadImage(IMG_DIR+"scrollbar/scrollbar_bottom.png")
		bottomImage.Show()
		middleImage = ui.ExpandedImageBox()
		middleImage.SetParent(self)
		middleImage.AddFlag("not_pick")
		middleImage.SetPosition(0, topImage.GetHeight())
		middleImage.LoadImage(IMG_DIR+"scrollbar/scrollbar_mid.png")
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
class Grid:
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.reset()
	def find_blank(self, width, height):
		if width > self.width or height > self.height:
			return -1

		for row in range(self.height):
			for col in range(self.width):
				index = row * self.width + col
				if self.is_empty(index, width, height):
					return index
		return -1
	def put(self, pos, width, height):
		if not self.is_empty(pos, width, height):
			return False
		for row in range(height):
			start = pos + (row * self.width)
			self.grid[start] = True
			col = 1
			while col < width:
				self.grid[start + col] = True
				col += 1
		return True
	def clear(self, pos, width, height):
		if pos < 0 or pos >= (self.width * self.height):
			return
		for row in range(height):
			start = pos + (row * self.width)
			self.grid[start] = True
			col = 1
			while col < width:
				self.grid[start + col] = False
				col += 1
	def is_empty(self, pos, width, height):
		if pos < 0:
			return False
		row = pos // self.width
		if (row + height) > self.height:
			return False
		if (pos + width) > ((row * self.width) + self.width):
			return False
		for row in range(height):
			start = pos + (row * self.width)
			if self.grid[start]:
				return False
			col = 1
			while col < width:
				if self.grid[start + col]:
					return False
				col += 1
		return True
	def get_size(self):
		return self.width * self.height
	def reset(self):
		self.grid = [False] * (self.width * self.height)
