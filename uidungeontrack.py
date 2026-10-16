#author: dracaryS

#dyanmic
import app, player, grp, net, chat, event, item, wndMgr, WikiRenderTarget

#static
import ui, _weakref, os, pickle as cPickle, operator, osfInfo, localeInfo, math
import nonplayer
import dungeonpresentation
import featureavailability

#second
LOG_UPDATE_TIME = 1

IMG_DIR = "d:/ymir work/ui/game/dungeon_info/"
DUNGEON_ATLAS_IMG_DIR = "d:/ymir work/ui/game/crimson_ember/dungeon_teleport/"

BG_IMG_DIR = IMG_DIR+"bg/"
ICON_IMG_DIR = IMG_DIR+"icons/"
NOTIFICATIONS_IMG_DIR = IMG_DIR+"notifications/"

DUNGEON_STATUS_AVAILABLE_COLOR = 0xff83d45b
DUNGEON_STATUS_UNAVAILABLE_COLOR = 0xffff4f5f

def _DungeonSignedColor(color):
	# wndMgr's Python 3 bridge accepts a C int, while packed ARGB is a DWORD.
	color = int(color)
	return color - 0x100000000 if color > 0x7fffffff else color

DUNGEON_COLOR_GOLD = _DungeonSignedColor(0xffffcf6c)
DUNGEON_COLOR_BLUE = _DungeonSignedColor(0xff69a7d7)
DUNGEON_COLOR_GREEN = _DungeonSignedColor(0xff72c66a)
DUNGEON_COLOR_AMBER = _DungeonSignedColor(0xffdea435)
DUNGEON_COLOR_DIM = _DungeonSignedColor(0xffa99f94)
DUNGEON_COLOR_NAME = _DungeonSignedColor(0xffeee6dc)

DUNGEON_TRACK_BODY_TOP = 31
DUNGEON_SETTINGS_VERSION = 8
DUNGEON_WIKI_COMMANDS = {
	2092 : "dungeon#20",
	2493 : "dungeon#21",
	6192 : "dungeon#24",
}

def _AtlasLocale(key, fallback):
	return getattr(localeInfo, key, fallback)

def _DungeonRejoinButtonText():
	fallback = "VRATIT SE" if app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz" else "RETURN"
	return _AtlasLocale("DUNGEON_REJOIN_BUTTON", fallback)

def _DungeonRejoinStatusText(leftTime):
	fallback = "NAVRAT %s" if app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz" else "RETURN %s"
	return _AtlasLocale("DUNGEON_REJOIN_STATUS", fallback) % FormatTime(leftTime)

def _AtlasSetWidgetAlpha(widget, alpha):
	setAlpha = getattr(widget, "SetAlpha", None)
	if setAlpha:
		setAlpha(alpha)

def _AtlasSetButtonVisuals(button, family, selected = False):
	basePath = DUNGEON_ATLAS_IMG_DIR + family
	if selected:
		button.SetUpVisual(basePath + "_selected.png")
		button.SetOverVisual(basePath + "_selected.png")
		button.SetDownVisual(basePath + "_selected.png")
	else:
		button.SetUpVisual(basePath + "_normal.png")
		button.SetOverVisual(basePath + "_hover.png")
		button.SetDownVisual(basePath + "_pressed.png")
	button.SetDisableVisual(basePath + "_disabled.png")

def GetDungeonRejoinOffer(mobIdx = None):
	offer = getattr(osfInfo, "dungeonRejoinOffer", None)
	if not isinstance(offer, dict):
		return None
	try:
		if int(offer["expiresAt"]) <= app.GetGlobalTimeStamp():
			osfInfo.dungeonRejoinOffer = None
			return None
		if mobIdx is not None and int(offer["bossVnum"]) != int(mobIdx):
			return None
	except (KeyError, TypeError, ValueError):
		osfInfo.dungeonRejoinOffer = None
		return None
	return offer

# Version 1 used the old Hydra/Jotun/Razador/Nemere ordering.  Only migrate
# that exact default layout; a player-created ordering remains authoritative.
DUNGEON_SETTINGS_V1_DEFAULT_ORDER = {
	1093: 0,
	2092: 1,
	2598: 2,
	2493: 3,
	6192: 4,
	6091: 5,
	6191: 6,
	3962: 7,
	6193: 8,
}

# Version 2 is the last nine-dungeon layout.  Existing player ordering is
# preserved behind the newly introduced Orc Sanctuary row.
DUNGEON_SETTINGS_V2_DEFAULT_ORDER = {
	1093: 0,
	2092: 1,
	2598: 2,
	2493: 3,
	3962: 4,
	6192: 5,
	6091: 6,
	6191: 7,
	6193: 8,
}

# Version 4 is the last layout before the seven Plechito dungeons.  It lets
# the migration distinguish the stock level order from a player's manual
# order: stock users receive the new level-sorted catalogue, while manual
# orders keep their existing rows and get the new entries appended.
DUNGEON_SETTINGS_V4_DEFAULT_ORDER = {
	5695: 0,
	1093: 1,
	2092: 2,
	4944: 3,
	2598: 4,
	2493: 5,
	3962: 6,
	6192: 7,
	6091: 8,
	6191: 9,
	6193: 10,
}

# Version 6 is the first compact 13-dungeon catalogue.  Stock ordering moves
# to the new minimum-level progression in version 7; manual ordering survives.
DUNGEON_SETTINGS_V6_DEFAULT_ORDER = {
	5695: 0,
	5672: 1,
	5710: 2,
	5731: 3,
	2092: 4,
	4944: 5,
	2493: 6,
	3962: 7,
	4815: 8,
	6192: 9,
	4685: 10,
	4701: 11,
	4760: 12,
}

# Version 7 is the last catalogue before Duratus and Andun Temple.  Preserve
# custom player ordering while giving stock users the new level-sorted order.
DUNGEON_SETTINGS_V7_DEFAULT_ORDER = {
	5695: 0,
	2092: 1,
	4944: 2,
	2493: 3,
	4685: 4,
	5731: 5,
	4815: 6,
	4701: 7,
	3962: 8,
	6192: 9,
	5672: 10,
	5710: 11,
	4760: 12,
}

def GetCloneDungeonData(infoDict):
	_dict = {
		"name" : "",
		"finalBossVnum" : 0,
		"image" : "sd3_new.png",
		"minLevel" : 0,
		"group" : False,
		"cooldown" : 0,
		"ticket": [],
		"ticketShop": True,
		"server_shop_idx" : 0,
		"listIndex" : 0,
		"static_listIndex" : 0,
		"showStatus" : True,
		"alarm" : False,
		"autoTicket" : False,
		"server_cooldown": 0,
		"server_completed":0,
		"server_fastest":0,
		"server_damage":0,
		"selected":True,
		"whisper_info":False,
		"directEntry":False,
	}
	for key, value in infoDict.items():
		_dict[key] = value
	# Level, cooldown, ticket, party mode and ticket-shop button are server
	# data: root/dungeoncatalog.py is generated from the althea/server catalog.
	import dungeoncatalog
	_dict.update(dungeoncatalog.DungeonInfo(_dict["finalBossVnum"]))
	return _dict

def IsDungeonLevelLocked(dungeonInfo, playerLevel):
	return playerLevel < dungeonInfo["minLevel"]


dungeonData = {
	5695 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[5695],
		"finalBossVnum" : 5695,
		"image" : "jotun_dungeon.png",
		"server_shop_idx" : 107,
		"listIndex" : 0,
		"static_listIndex" : 0,
		"directEntry" : True,
	}),
	2092 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[2092],
		"finalBossVnum" : 2092,
		"image" : "sd3_new.png",
		"server_shop_idx" : 107,
		"listIndex" : 1,
		"static_listIndex" : 1,
		"directEntry" : True,
	}),
	2493 : GetCloneDungeonData({
		"name" : "Beran Setaou",
		"finalBossVnum" : 2493,
		"image" : "dragon_lair.png",
		"server_shop_idx" : 107,
		"listIndex" : 4,
		"static_listIndex" : 4,
		"directEntry" : True,
	}),
	6192 : GetCloneDungeonData({
		"name" : "Jotun",
		"finalBossVnum" : 6192,
		"image" : "jotun_dungeon.png",
		"server_shop_idx" : 107,
		"listIndex" : 10,
		"static_listIndex" : 10,
		"directEntry" : True,
	}),
	3962 : GetCloneDungeonData({
		"name" : "Hydra",
		"finalBossVnum" : 3962,
		"image" : "ship_defense.png",
		"server_shop_idx" : 107,
		"listIndex" : 9,
		"static_listIndex" : 9,
		"directEntry" : True,
	}),
	4944 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[4944],
		"finalBossVnum" : 4944,
		"image" : "ship_defense.png",
		"server_shop_idx" : 107,
		"listIndex" : 2,
		"static_listIndex" : 2,
		"directEntry" : True,
	}),
	4856 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[4856],
		"finalBossVnum" : 4856,
		"image" : "flame_dungeon.png",
		"server_shop_idx" : 107,
		"listIndex" : 3,
		"static_listIndex" : 3,
		"directEntry" : True,
	}),
	5672 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[5672],
		"finalBossVnum" : 5672,
		"image" : "jotun_dungeon.png",
		"server_shop_idx" : 107,
		"listIndex" : 11,
		"static_listIndex" : 11,
		"directEntry" : True,
	}),
	4685 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[4685],
		"finalBossVnum" : 4685,
		"image" : "deviltower_new.png",
		"server_shop_idx" : 107,
		"listIndex" : 5,
		"static_listIndex" : 5,
		"directEntry" : True,
	}),
	4815 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[4815],
		"finalBossVnum" : 4815,
		"image" : "snow_dungeon.png",
		"server_shop_idx" : 107,
		"listIndex" : 7,
		"static_listIndex" : 7,
		"directEntry" : True,
	}),
	4701 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[4701],
		"finalBossVnum" : 4701,
		"image" : "devilcatacomb_new.png",
		"server_shop_idx" : 107,
		"listIndex" : 8,
		"static_listIndex" : 8,
		"directEntry" : True,
	}),
	4760 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[4760],
		"finalBossVnum" : 4760,
		"image" : "flame_dungeon.png",
		"server_shop_idx" : 107,
		"listIndex" : 14,
		"static_listIndex" : 14,
		"directEntry" : True,
	}),
	5710 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[5710],
		"finalBossVnum" : 5710,
		"image" : "jotun_dungeon.png",
		"server_shop_idx" : 107,
		"listIndex" : 12,
		"static_listIndex" : 12,
		"directEntry" : True,
	}),
	5731 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[5731],
		"finalBossVnum" : 5731,
		"image" : "ship_defense.png",
		"server_shop_idx" : 107,
		"listIndex" : 6,
		"static_listIndex" : 6,
		"directEntry" : True,
	}),
	4549 : GetCloneDungeonData({
		"name" : localeInfo.DUNGEON_DISPLAY_NAMES[4549],
		"finalBossVnum" : 4549,
		"image" : "deviltower_new.png",
		"server_shop_idx" : 107,
		"listIndex" : 13,
		"static_listIndex" : 13,
		"directEntry" : True,
	}),
}


def _RefreshCountdownSelection(reveal):
	interface = osfInfo.GetInterfaceInstance()
	if interface and hasattr(interface, "RefreshCountdownHUDSelection"):
		interface.RefreshCountdownHUDSelection(bool(reveal))


class DungeonManager(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.Destroy()
	def Destroy(self):
		self.__children={}
	def AddDungeon(self, dungeonBossIdx):
		global dungeonData
		if dungeonBossIdx not in dungeonData:
			return
		image = CreateWindow(ui.ImageBox(), self, (0, 0), NOTIFICATIONS_IMG_DIR+dungeonData[dungeonBossIdx]["image"])
		image.Hide()
		image.SetEvent(ui.__mem_func__(self.__Click), "mouse_click", dungeonBossIdx)
		image.leftTime = app.GetTime() + 10.0
		self.__children[dungeonBossIdx] = image

		image.text = CreateWindow(MultiTextLine(), image, (45, 8), "")
		image.text.Hide()
		image.text.SetTextRange(13)
		image.text.SetText(localeInfo.DUNGEON_TRACK_NOTIFICATION % dungeonData[dungeonBossIdx]["name"])

		self.Show()

	def __Click(self, emptyArg, mobIdx):
		if mobIdx in self.__children:
			leftTime = self.__children[mobIdx].leftTime - app.GetTime()
			self.__children[mobIdx].leftTime = app.GetTime() + (leftTime if leftTime < 1.0 else 1.0)

	def SortWithIndex(self, child):
		return child[1]

	def OnUpdate(self):
		global dungeonData
		(needRemoveList, imageList, now) = ([], [], app.GetTime())
		for key, image in self.__children.items():
			if image.leftTime < now:
				needRemoveList.append(key)
			else:
				imageList.append([key, dungeonData[key]["static_listIndex"], image])

		for mobIdx in needRemoveList:
			self.__children[mobIdx].text = None
			self.__children[mobIdx].Hide()
			del self.__children[mobIdx]

		if len(imageList):
			imageList.sort(key=ui.__mem_func__(self.SortWithIndex))
			xPos, yPos = (wndMgr.GetScreenWidth() // 2) - (119 // 2), 0
			self.SetPosition(xPos, 100)

			for imageListInfo in imageList:
				image = imageListInfo[2]
				image.SetPosition(0, yPos)
				yPos += image.GetHeight() + 4
				leftTime = image.leftTime - now
				if leftTime < 1.0:
					image.SetAlpha(leftTime)
				image.text.Show()
				image.Show()
			self.SetSize(119, yPos)
			self.Show()
		else:
			self.Hide()

#DungeonManagerEx = DungeonManager()

class DungeonTrack(ui.ExpandedImageBox):
	__children = {}
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)
		self.__LoadWindow()
	def Destroy(self):
		self.__ClearTicketImages()
		logManager = self.__children["logManager"] if "logManager" in self.__children else None
		if logManager:
			logManager.Close()
			logManager.Destroy()
			self.__children["logManager"] = None

		self.__children = {}

	def __ClearTicketImages(self):
		for ticketImage in self.__children.get("ticketImageList", []):
			ticketImage.Hide()
		self.__children["ticketImageList"] = []

	def __LoadWindow(self):
		self.Destroy()
		self.LoadImage(IMG_DIR+"bg.png")
		self.AddFlag("float")
		self.AddFlag("movable")
		self.AddFlag("attach")

		bodyImage = CreateWindow(ui.ExpandedImageBox(), self, (0, 0), IMG_DIR+"bg_body_pre_v31.png")
		bodyImage.SetRenderingRect(0.0, -float(DUNGEON_TRACK_BODY_TOP) / float(bodyImage.GetHeight()), 0.0, 0.0)
		bodyImage.AddFlag("not_pick")
		self.__children["bodyImage"] = bodyImage

		titleBar = CreateWindow(ui.TitleBar(), self, (35, 5))
		titleBar.MakeTitleBar(self.GetWidth()-40, "red")
		titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__children["titleBar"] = titleBar

		titleName = CreateWindow(ui.TextLine(), titleBar, (0, 4), localeInfo.DUNGEON_TRACK_TITLE)
		titleName.SetWindowHorizontalAlignCenter()
		titleName.SetHorizontalAlignCenter()
		self.__children["titleName"] = titleName

		scrollBar = CreateWindow(ScrollBarSpecial(False), self, (324, 35), "", "", (7, 376))
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.__children["scrollBar"] = scrollBar

		listWindow = CreateWindow(ui.Window(), self, (18, 41), "", "", (300, 364))
		listWindow.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)
		listWindow.SetInsideRender(True)
		self.__children["listWindow"] = listWindow

		clearBtn = CreateWindow(ui.Button(), self, (5, 5))
		clearBtn.SetUpVisual("d:/ymir work/ui/game/windows/refresh_titlebar_up.sub")
		clearBtn.SetOverVisual("d:/ymir work/ui/game/windows/refresh_titlebar_over.sub")
		clearBtn.SetDownVisual("d:/ymir work/ui/game/windows/refresh_titlebar_down.sub")
		clearBtn.SetEvent(ui.__mem_func__(self.__ClearBtn))
		self.__children["clearBtn"] = clearBtn

		dungeonBtnDict = {}
		global dungeonData
		for mobIdx, dataDict in dungeonData.items():
			btn =  CreateWindow(Dungeon(mobIdx, self), listWindow, (0, 0))
			btn.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)
			btn.SetEvent(ui.__mem_func__(self.__ClickDungeon), "mouse_click", mobIdx)
			dungeonBtnDict[str(mobIdx)+"btn"] = btn
		self.__children["dungeonBtnDict"] = dungeonBtnDict

		# Right Table

		rightBG = CreateWindow(ui.ImageBox(), self, (340, 39), BG_IMG_DIR+"ape_dungeon.png")
		self.__children["rightBG"] = rightBG
		self.__children["clock"] = CreateWindow(ui.ImageBox(), rightBG, (10, 7), IMG_DIR+"clock.png")


		checkBox = CreateWindow(ui.Button(), rightBG, (34, 7))
		checkBox.SetUpVisual(IMG_DIR+"checkbox_new_unselected.tga")
		checkBox.SetOverVisual(IMG_DIR+"checkbox_new_unselected.tga")
		checkBox.SetDownVisual(IMG_DIR+"checkbox_new_unselected.tga")
		checkBox.SetEvent(ui.__mem_func__(self.__ClickCheckBox))
		checkBox.SetToolTipText(localeInfo.DUNGEON_TRACK_CHECKBOX)
		self.__children["checkBox"] = checkBox

		self.__children["title"] = CreateWindow(ui.TextLine(), rightBG, (125, 7), localeInfo.DUNGEON_TRACK_UNKNOWN, "horizontal:center")

		wikiBtn = CreateWindow(ui.Button(), rightBG, (222, 7))
		wikiBtn.SetUpVisual("d:/ymir work/ui/pattern/q_mark_01.tga")
		wikiBtn.SetOverVisual("d:/ymir work/ui/pattern/q_mark_02.tga")
		wikiBtn.SetDownVisual("d:/ymir work/ui/pattern/q_mark_01.tga")
		wikiBtn.SetEvent(ui.__mem_func__(self.__WikiBtn))
		wikiBtn.SetToolTipText(localeInfo.DUNGEON_TRACK_WIKI_TOOLTIP)
		self.__children["wikiBtn"] = wikiBtn

		self.__children["level_info"] = CreateWindow(ui.TextLine(), rightBG, (10, 32), localeInfo.DUNGEON_TRACK_LEVEL_INFO)
		self.__children["level_text"] = CreateWindow(ui.TextLine(), rightBG, (222+14, 32), "LV. 0+", "horizontal:right")

		self.__children["group_info"] = CreateWindow(ui.TextLine(), rightBG, (10, 32 + (17 * 1)), localeInfo.DUNGEON_TRACK_GROUP_INFO)
		self.__children["group_text"] = CreateWindow(ui.TextLine(), rightBG, (222+14, 32 + (17 * 1)), localeInfo.DUNGEON_TRACK_FALSE, "horizontal:right")

		self.__children["cooldown_info"] = CreateWindow(ui.TextLine(), rightBG, (10, 32 + (17 * 2)), localeInfo.DUNGEON_TRACK_COOLDOWN_INFO)
		self.__children["cooldown_text"] = CreateWindow(ui.TextLine(), rightBG, (222+14, 32 + (17 * 2)), "0s", "horizontal:right")

		self.__children["ticket_info"] = CreateWindow(ui.TextLine(), rightBG, (10, 32 + (17 * 4)), localeInfo.DUNGEON_TRACK_TICKET_INFO)

		shopBtn = CreateWindow(ui.Button(), rightBG, (209, 96))
		shopBtn.SetUpVisual(IMG_DIR+"shop_0.png")
		shopBtn.SetOverVisual(IMG_DIR+"shop_1.png")
		shopBtn.SetDownVisual(IMG_DIR+"shop_2.png")
		shopBtn.SetEvent(ui.__mem_func__(self.__ShopBtn))
		shopBtn.SetToolTipText(localeInfo.DUNGEON_TRACK_SHOP_INFO)
		self.__children["shopBtn"] = shopBtn

		enterBtn = CreateWindow(ui.Button(), rightBG, (10, 324))
		enterBtn.SetUpVisual(IMG_DIR+"teleport_into_0.png")
		enterBtn.SetOverVisual(IMG_DIR+"teleport_into_1.png")
		enterBtn.SetDownVisual(IMG_DIR+"teleport_into_2.png")
		enterBtn.SAFE_SetEvent(self.__ClickQuest, "ENTER")
		enterBtn.SetToolTipText(localeInfo.DUNGEON_TRACK_TELEPORT_ENTER)
		self.__children["enterBtn"] = enterBtn

		testBtn = CreateWindow(ui.Button(), rightBG, (10 + 80 + 80, 324))
		testBtn.SetUpVisual(IMG_DIR+"test_boss_0.png")
		testBtn.SetOverVisual(IMG_DIR+"test_boss_1.png")
		testBtn.SetDownVisual(IMG_DIR+"test_boss_2.png")
		testBtn.SAFE_SetEvent(self.__ClickQuest, "TEST")
		testBtn.SetToolTipText(localeInfo.DUNGEON_TRACK_TEST)
		self.__children["testBtn"] = testBtn
		self.__children["testBtn"].Hide()

		self.__children["personal_info"] = CreateWindow(ui.TextLine(), rightBG, (125, 150), localeInfo.DUNGEON_TRACK_PERSONAL_STATISTICS, "horizontal:center")

		completedRank = CreateWindow(ui.Button(), rightBG, (10, 183))
		completedRank.SetUpVisual(IMG_DIR+"completed_0.png")
		completedRank.SetOverVisual(IMG_DIR+"completed_1.png")
		completedRank.SetDownVisual(IMG_DIR+"completed_2.png")
		completedRank.SAFE_SetEvent(self.__ClickRank, 0)
		completedRank.SetToolTipText(localeInfo.DUNGEON_TRACK_RANK_COMPLETED)
		self.__children["completedRank"] = completedRank

		self.__children["completed_info"] = CreateWindow(ui.TextLine(), rightBG, (10+38, 183 + 2), localeInfo.DUNGEON_TRACK_COMPLETED)
		self.__children["completed_text"] = CreateWindow(ui.TextLine(), rightBG, (222+14, 183 + 2), "0", "horizontal:right")

		fastRank = CreateWindow(ui.Button(), rightBG, (10, 183 + 25))
		fastRank.SetUpVisual(IMG_DIR+"fastest_0.png")
		fastRank.SetOverVisual(IMG_DIR+"fastest_1.png")
		fastRank.SetDownVisual(IMG_DIR+"fastest_2.png")
		fastRank.SAFE_SetEvent(self.__ClickRank, 1)
		fastRank.SetToolTipText(localeInfo.DUNGEON_TRACK_RANK_FASTEST)
		self.__children["fastRank"] = fastRank

		self.__children["fast_info"] = CreateWindow(ui.TextLine(), rightBG, (10+38, 183 + 2 + 25), localeInfo.DUNGEON_TRACK_FASTEST)
		self.__children["fast_text"] = CreateWindow(ui.TextLine(), rightBG, (222+14, 183 + 2 + 25), "0s", "horizontal:right")

		damageRank = CreateWindow(ui.Button(), rightBG, (10, 183 + 25 + 25))
		damageRank.SetUpVisual(IMG_DIR+"damage_0.png")
		damageRank.SetOverVisual(IMG_DIR+"damage_1.png")
		damageRank.SetDownVisual(IMG_DIR+"damage_2.png")
		damageRank.SAFE_SetEvent(self.__ClickRank, 2)
		damageRank.SetToolTipText(localeInfo.DUNGEON_TRACK_RANK_DMG)
		self.__children["damageRank"] = damageRank

		self.__children["damage_info"] = CreateWindow(ui.TextLine(), rightBG, (10+38, 183 + 2 + 25 + 25), localeInfo.DUNGEON_TRACK_DMG)
		self.__children["damage_text"] = CreateWindow(ui.TextLine(), rightBG, (222+14, 183 + 2 + 25 + 25), "0", "horizontal:right")

		self.SetCenterPosition()
		LoadSettings()
		self.Refresh()

	def GetCurrentSelectedDungeon(self):
		global dungeonData
		for mobIdx, dungeonInfo in dungeonData.items():
			if dungeonInfo["selected"]:
				return mobIdx
		return -1

	def LoadServerData(self, mobIdx, rankIdx, cmd):
		logManager = self.__children["logManager"] if "logManager" in self.__children else None
		if logManager:
			logManager.LoadServerData(int(mobIdx), int(rankIdx), cmd)
	
	def __ClickRank(self, rankIdx):
		logManager = self.__children["logManager"] if "logManager" in self.__children else None
		if not logManager:
			logManager = LogWindow()
			self.__children["logManager"] = logManager
		logManager.Open(self.GetCurrentSelectedDungeon(), rankIdx)

	def __ClickQuest(self, questMode):
		currentDungeon = self.GetCurrentSelectedDungeon()
		if currentDungeon == -1:
			return
		if questMode == "ENTER":
			self.Close()
		osfInfo.dungeonInfoCMD = questMode + "#" + str(currentDungeon)
		event.QuestButtonClick(int(osfInfo.dungeonInfoQuestIdx))

	def __ShopBtn(self):
		currentDungeon = self.GetCurrentSelectedDungeon()
		if currentDungeon != -1:
			if not dungeonData[currentDungeon]["ticket"] or not dungeonData[currentDungeon]["ticketShop"]:
				return
			lastShopBtnClick = self.__children["lastShopBtnClick"] if "lastShopBtnClick" in self.__children else 0
			if lastShopBtnClick > app.GetGlobalTimeStamp():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DUNGEON_TRACK_SLOW_INFO)
				return
			self.__children["lastShopBtnClick"] = app.GetGlobalTimeStamp() + 2
			self.__ClickQuest("SHOP")

	def __WikiBtn(self):
		currentDungeon = self.GetCurrentSelectedDungeon()

		if currentDungeon in DUNGEON_WIKI_COMMANDS:
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				interface.OpenWikiWindow()
				interface.wndWiki.LoadData(DUNGEON_WIKI_COMMANDS[currentDungeon])
				interface.wndWiki.SetTop()

	def __ClickCheckBox(self):
		currentDungeon = self.GetCurrentSelectedDungeon()
		if currentDungeon != -1:
			global dungeonData
			dungeonData[currentDungeon]["alarm"] = not dungeonData[currentDungeon]["alarm"]
			self.Refresh(False, False, True)
			SaveSettings()
			_RefreshCountdownSelection(dungeonData[currentDungeon]["alarm"])

	def __ClickDungeon(self, emptyArg, mobIdx):
		global dungeonData
		for key, dungeonInfo in dungeonData.items():
			dungeonInfo["selected"] = False
		if mobIdx in dungeonData:
			dungeonData[mobIdx]["selected"] = True
		self.Refresh()
		SaveSettings()

	def __OnScroll(self):
		self.Refresh(False, False, False)

	def __ClearBtn(self):
		ClearSettings()
		self.Refresh(True)

	def SortWithIndex(self, child):
		return child.GetIndex()

	def OnMouseWheel(self, length):
		self.__children["scrollBar"].OnMouseWheel(length)
		return True

	def Refresh(self, resetPos = False, refreshItems = True, refreshRightTable = True):
		dungeonBtnDict = self.__children["dungeonBtnDict"]
		btnList = []
		for key, dungeonBtn in dungeonBtnDict.items():
			dungeonBtn.Refresh()
			if dungeonBtn.GetShowStatus():
				dungeonBtn.Show()
				btnList.append(dungeonBtn)
			else:
				dungeonBtn.Hide()
		btnList.sort(key=ui.__mem_func__(self.SortWithIndex))
		scrollBar = self.__children["scrollBar"]
		if resetPos:
			scrollBar.SetPos(0)
		if len(btnList):
			scrollLen = 0
			(screenSize, windowHeight) = (len(btnList) * (46 + 7), 364)
			if screenSize != 0:
				screenSize -= 7
			if screenSize > windowHeight:
				scrollLen = screenSize-windowHeight
				scrollBar.SetScale(windowHeight, screenSize)
				basePos = int(scrollBar.GetPos()*scrollLen)
			else:
				scrollBar.SetScale(376, 376)
				basePos = 0
			yPos = 0
			for child in btnList:
				child.SetPosition(0, yPos - basePos)
				yPos += child.GetHeight() + 7
		else:
			scrollBar.SetScale(376, 376)
		
		if refreshRightTable:
			self.__ClearTicketImages()
			currentDungeon = self.GetCurrentSelectedDungeon()
			if currentDungeon != -1:
				global dungeonData
				dungeonInfo = dungeonData[currentDungeon]
				self.__children["enterBtn"].Show()
				self.__children["title"].SetText(dungeonInfo["name"])
				self.__children["level_text"].SetText("LV. %d+" % dungeonInfo["minLevel"])
				self.__children["group_text"].SetText(localeInfo.DUNGEON_TRACK_TRUE if dungeonInfo["group"] else localeInfo.DUNGEON_TRACK_FALSE)
				self.__children["cooldown_text"].SetText(FormatTimeEx(dungeonInfo["cooldown"]))

				self.__children["completed_text"].SetText(NumberToDecimalString(dungeonInfo["server_completed"]))
				self.__children["fast_text"].SetText(FormatTimeEx(dungeonInfo["server_fastest"]))
				self.__children["damage_text"].SetText(NumberToDecimalString(dungeonInfo["server_damage"]))

				checkBox = self.__children["checkBox"]
				checkBox.SetUpVisual(IMG_DIR+"checkbox_new_unselected.tga" if not dungeonInfo["alarm"] else IMG_DIR+"checkbox_new_selected.tga")
				checkBox.SetOverVisual(IMG_DIR+"checkbox_new_unselected.tga" if not dungeonInfo["alarm"] else IMG_DIR+"checkbox_new_selected.tga")
				checkBox.SetDownVisual(IMG_DIR+"checkbox_new_unselected.tga" if not dungeonInfo["alarm"] else IMG_DIR+"checkbox_new_selected.tga")

				rightBG = self.__children["rightBG"]

				rightBG.LoadImage(BG_IMG_DIR+dungeonInfo["image"])

				if dungeonInfo["ticket"]:
					self.__children["ticket_info"].SetText(localeInfo.DUNGEON_TRACK_TICKET_INFO)
					if dungeonInfo["ticketShop"]:
						self.__children["shopBtn"].Show()
					else:
						self.__children["shopBtn"].Hide()
					ticketItem = dungeonInfo["ticket"][0]
					ticketImageList = []
					item.SelectItem(ticketItem[0])
					itemIcon = CreateWindow(ui.ExpandedImageBox(), rightBG, (163, 96), item.GetIconImageFileName())
					itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OverInItem, ticketItem[0])
					itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OverOutItem)
					ticketImageList.append(itemIcon)
					if ticketItem[1] > 1:
						itemCountText = CreateWindow(ui.TextLine(), rightBG, (185, 118), str(ticketItem[1]))
						itemCountText.SetOutline()
						ticketImageList.append(itemCountText)
					self.__children["ticketImageList"] = ticketImageList
				else:
					self.__children["ticket_info"].SetText(localeInfo.DUNGEON_TRACK_NO_TICKET)
					self.__children["shopBtn"].Hide()

	def __OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def __OverInItem(self, itemIdx):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.SetItemToolTip(itemIdx)
	def OnUpdate(self):
		dungeonBtnDict = self.__children["dungeonBtnDict"]
		for key, dungeonBtn in dungeonBtnDict.items():
			dungeonBtn.OnUpdate()
	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()
	def Close(self):
		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True

class Dungeon(ui.ExpandedImageBox):
	def Destroy(self):
		self.__children={}
	def __init__(self, mobIdx, parent):
		ui.ExpandedImageBox.__init__(self)
		self.__Load(mobIdx, parent)
	
	def GetShowStatus(self):
		global dungeonData
		return dungeonData[self.__children["mobIdx"]]["showStatus"]

	def GetIndex(self):
		global dungeonData
		return dungeonData[self.__children["mobIdx"]]["listIndex"]

	def __Load(self, mobIdx, parent):
		self.Destroy()
		self.__children["mobIdx"] = mobIdx
		self.__children["parent"] = _weakref.proxy(parent)

		global dungeonData
		data = dungeonData[mobIdx]

		self.__children["name"] = CreateWindow(ui.TextLine(), self, (66, 17), data["name"])
		self.__children["image"] = CreateWindow(ui.ExpandedImageBox(), self, (1, 0), ICON_IMG_DIR+data["image"])
		self.__children["image"].AddFlag("not_pick")
		self.__children["status"] = CreateWindow(ui.TextLine(), self, (255, 12), "", "horizontal:right")
		self.__children["time"] = CreateWindow(ui.TextLine(), self, (245, 25), "", "horizontal:right")

		backBtn = CreateWindow(ui.Button(), self, (280, 5))
		backBtn.SetWindowName("not_render")
		backBtn.SetUpVisual(IMG_DIR+"up_0.png")
		backBtn.SetOverVisual(IMG_DIR+"up_1.png")
		backBtn.SetDownVisual(IMG_DIR+"up_2.png")
		backBtn.SetEvent(ui.__mem_func__(self.__BackBtn))
		backBtn.SetToolTipText(localeInfo.DUNGEON_TRACK_MOVE_UP)
		self.__children["backBtn"] = backBtn

		nextBtn = CreateWindow(ui.Button(), self, (280, 25))
		nextBtn.SetWindowName("not_render")
		nextBtn.SetUpVisual(IMG_DIR+"down_0.png")
		nextBtn.SetOverVisual(IMG_DIR+"down_1.png")
		nextBtn.SetDownVisual(IMG_DIR+"down_2.png")
		nextBtn.SetEvent(ui.__mem_func__(self.__NextBtn))
		nextBtn.SetToolTipText(localeInfo.DUNGEON_TRACK_MOVE_DOWN)
		self.__children["nextBtn"] = nextBtn

		eyeBtn = CreateWindow(ui.Button(), self, (0, 33))
		eyeBtn.SetUpVisual(IMG_DIR+"btn_hide_1.png")
		eyeBtn.SetOverVisual(IMG_DIR+"btn_hide_2.png")
		eyeBtn.SetDownVisual(IMG_DIR+"btn_hide_3.png")
		eyeBtn.SetEvent(ui.__mem_func__(self.__ShowBtn))
		eyeBtn.SetToolTipText(localeInfo.DUNGEON_TRACK_HIDE)
		self.__children["eyeBtn"] = eyeBtn

	def SortWithIndex(self, child):
		return child[1]
	def FindIndexInList(self, idx, goingType):
		global dungeonData
		btnList = []
		for mobIdx, dungeonDict in dungeonData.items():
			if not dungeonDict["showStatus"]:
				continue
			btnList.append([mobIdx, dungeonDict["listIndex"]])
		btnList.sort(key=ui.__mem_func__(self.SortWithIndex), reverse=not goingType)
		for child in btnList:
			if goingType:
				if child[1] >= idx:
					return child
			else:
				if child[1] <= idx:
					return child
		return -1

	def __BackBtn(self):
		global dungeonData
		listIdx = dungeonData[self.__children["mobIdx"]]["listIndex"]
		if listIdx <= 0:
			return
		destIndex = self.FindIndexInList(listIdx-1, False)
		if destIndex != -1:
			dungeonData[destIndex[0]]["listIndex"] = listIdx
			dungeonData[self.__children["mobIdx"]]["listIndex"] = destIndex[1]
		else:
			dungeonData[self.__children["mobIdx"]]["listIndex"] -= 1
		self.__children["parent"].Refresh(False, True, False)
		SaveSettings()

	def __NextBtn(self):
		global dungeonData
		listIdx = dungeonData[self.__children["mobIdx"]]["listIndex"]
		if listIdx >= len(dungeonData)-1:
			return
		destIndex = self.FindIndexInList(listIdx+1, True)
		if destIndex != -1:
			dungeonData[destIndex[0]]["listIndex"] = listIdx
			dungeonData[self.__children["mobIdx"]]["listIndex"] = destIndex[1]
		else:
			dungeonData[self.__children["mobIdx"]]["listIndex"] += 1

		self.__children["parent"].Refresh(False, True, False)
		SaveSettings()

	def __ShowBtn(self):
		global dungeonData
		dungeonData[self.__children["mobIdx"]]["showStatus"] = False
		self.__children["parent"].Refresh(True, True, False)
		SaveSettings()

	def Refresh(self):
		global dungeonData
		data = dungeonData[self.__children["mobIdx"]]

		isDeactive = True if data["server_cooldown"] > app.GetGlobalTimeStamp() or IsDungeonLevelLocked(data, player.GetStatus(player.LEVEL)) else False
		#isDeactive = True if data["server_cooldown"] > app.GetGlobalTimeStamp() else False

		self.__children["status"].SetText(localeInfo.DUNGEON_TRACK_DEACTIVE if isDeactive else localeInfo.DUNGEON_TRACK_ACTIVE)
		self.__children["status"].SetPackedFontColor(
			_DungeonSignedColor(DUNGEON_STATUS_UNAVAILABLE_COLOR if isDeactive else DUNGEON_STATUS_AVAILABLE_COLOR))
		self.__children["time"].SetPackedFontColor(_DungeonSignedColor(DUNGEON_STATUS_UNAVAILABLE_COLOR))
		
		if isDeactive:
			self.__children["time"].Show()
		else:
			self.__children["time"].Hide()

			# CountdownWindow owns the single silent readiness edge.

		if IsDungeonLevelLocked(data, player.GetStatus(player.LEVEL)):
			self.__children["time"].SetText(localeInfo.DUNGEON_TRACK_LOW_LEVEL)
			self.__children["time"].Show()

		currentImage = IMG_DIR+"quest_red.png" if isDeactive else IMG_DIR+"quest_blue.png"
		if currentImage != (self.__children["currentImage"] if "currentImage" in self.__children else ""):
			self.__children["currentImage"] = currentImage
			self.LoadImage(currentImage)
		self.SetAlpha(1.0 if data["selected"] else 0.6)

	def OnUpdate(self):
		global dungeonData

		lastUpdate = self.__children["lastUpdate"] if "lastUpdate" in self.__children else 0
		if lastUpdate < app.GetTime():
			self.__children["lastUpdate"] = app.GetTime() + 0.3
			leftTime = dungeonData[self.__children["mobIdx"]]["server_cooldown"] - app.GetGlobalTimeStamp()
			if leftTime <= 0:
				self.Refresh()
			else:
				self.__children["time"].SetText(FormatTime(leftTime))

		if self.__children["eyeBtn"].IsIn() or self.__children["backBtn"].IsIn() or self.__children["nextBtn"].IsIn():
			return
		if self.IsIn():
			listIdx = dungeonData[self.__children["mobIdx"]]["listIndex"]
			if listIdx > 0:
				self.__children["backBtn"].Show()
			else:
				self.__children["backBtn"].Hide()
			if listIdx < len(dungeonData)-1:
				self.__children["nextBtn"].Show()
			else:
				self.__children["nextBtn"].Hide()
			self.__children["eyeBtn"].Show()
		else:
			self.__children["backBtn"].Hide()
			self.__children["nextBtn"].Hide()
			self.__children["eyeBtn"].Hide()

def NumberToDecimalString(n):
	return str('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))

def FormatTimeEx(seconds):
	if seconds <= 0:
		return localeInfo.GUILDLAND_NOT
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	text = ""
	if d > 0:
		text+="{} {} ".format(d, localeInfo.DAY)
	if h > 0:
		text+="{} {} ".format(h, localeInfo.HOUR)
	if m > 0:
		text+="{} {} ".format(m, localeInfo.MINUTE)
	if s > 0:
		text+="{} {} ".format(s, localeInfo.SECOND)
	return text[:len(text)-1] if len(text) > 0 else localeInfo.GUILDLAND_NOT

def FormatTime(seconds):
	if seconds <= 0:
		return "00:00:00"
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	return "%02d:%02d:%02d"% (h, m, s)


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
def ClearSettings():
	global dungeonData
	for mobIdx, dungeonInfo in dungeonData.items():
		dungeonInfo["listIndex"] = dungeonInfo["static_listIndex"]
		dungeonInfo["showStatus"] = True
		#dungeonInfo["alarm"] = False
	SaveSettings()

def __GetSettingsDirectory():
	return "UserData/dungeon_info"

def __GetSettingsPath():
	return "{}/{}_track".format(__GetSettingsDirectory(), player.GetName())

def __EnsureSettingsDirectory():
	settingsDirectory = __GetSettingsDirectory()
	if not os.path.exists(settingsDirectory):
		os.makedirs(settingsDirectory)

def __NormalizeDungeonListIndexes():
	global dungeonData
	orderedDungeons = sorted(
		dungeonData.items(),
		key=lambda dungeonEntry: (
			dungeonEntry[1]["listIndex"],
			dungeonEntry[1]["static_listIndex"],
		),
	)
	for listIndex, dungeonEntry in enumerate(orderedDungeons):
		dungeonEntry[1]["listIndex"] = listIndex

def LoadSettings():
	global dungeonData, _settingsCharacter
	character = str(player.GetName())
	previousCharacter = globals().get("_settingsCharacter")
	if previousCharacter is not None and previousCharacter != character:
		first = min(dungeonData, key=lambda vnum: dungeonData[vnum]["static_listIndex"])
		for vnum, entry in dungeonData.items():
			entry.update(listIndex=entry["static_listIndex"], showStatus=True, alarm=False, autoTicket=False, selected=vnum == first)
	_settingsCharacter = character
	try:
		f = old_open(__GetSettingsPath(), "rb")
		currentSettings = cPickle.load(f)
		f.close()
		if not isinstance(currentSettings, dict):
			return

		settingsVersion = currentSettings.get("version", 0)
		if settingsVersion == DUNGEON_SETTINGS_VERSION:
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = True
			listIndexOffset = 0
			saveMigratedSettings = False
		elif settingsVersion == 7:
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = not all(
				mobIdx in storedDungeons
					and isinstance(storedDungeons[mobIdx], dict)
					and storedDungeons[mobIdx].get("listIndex") == oldListIndex
				for mobIdx, oldListIndex in DUNGEON_SETTINGS_V7_DEFAULT_ORDER.items()
			)
			listIndexOffset = 0
			saveMigratedSettings = True
		elif settingsVersion == 6:
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = not all(
				mobIdx in storedDungeons
					and isinstance(storedDungeons[mobIdx], dict)
					and storedDungeons[mobIdx].get("listIndex") == oldListIndex
				for mobIdx, oldListIndex in DUNGEON_SETTINGS_V6_DEFAULT_ORDER.items()
			)
			listIndexOffset = 0
			saveMigratedSettings = True
		elif settingsVersion == 5:
			# Version 5 still contained the five retired stock dungeons.
			# Preserve the player's order and preferences for every remaining
			# row, then rewrite the compact version-6 catalogue.
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = True
			listIndexOffset = 0
			saveMigratedSettings = True
		elif settingsVersion == 4:
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = not all(
				mobIdx in storedDungeons
				and isinstance(storedDungeons[mobIdx], dict)
				and storedDungeons[mobIdx].get("listIndex") == oldListIndex
				for mobIdx, oldListIndex in DUNGEON_SETTINGS_V4_DEFAULT_ORDER.items()
			)
			listIndexOffset = 0
			saveMigratedSettings = True
		elif settingsVersion == 3:
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = True
			listIndexOffset = 0
			saveMigratedSettings = True
		elif settingsVersion == 2:
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = True
			listIndexOffset = 1
			saveMigratedSettings = True
		elif settingsVersion == 1:
			storedDungeons = currentSettings.get("dungeons", {})
			if not isinstance(storedDungeons, dict):
				return
			restoreListIndex = not all(
				mobIdx in storedDungeons
				and isinstance(storedDungeons[mobIdx], dict)
				and storedDungeons[mobIdx].get("listIndex") == oldListIndex
				for mobIdx, oldListIndex in DUNGEON_SETTINGS_V1_DEFAULT_ORDER.items()
			)
			listIndexOffset = 1 if restoreListIndex else 0
			saveMigratedSettings = True
		else:
			# Legacy files stored the complete dungeonData dictionary. Keep the
			# player's visibility/alarm choices, but migrate the stale order to
			# the current level-based default.
			storedDungeons = currentSettings
			restoreListIndex = False
			listIndexOffset = 0
			saveMigratedSettings = True

		if settingsVersion in (1, 2) and any(
			isinstance(settingData, dict) and settingData.get("selected", False)
			for settingData in storedDungeons.values()
		):
			dungeonData[5695]["selected"] = False
		if settingsVersion == 3:
			dungeonData[4944]["selected"] = False
		if settingsVersion in (1, 2, 3) and restoreListIndex:
			lastStoredIndex = max(
				(settingData.get("listIndex", -1) + listIndexOffset
				 for settingData in storedDungeons.values()
				 if isinstance(settingData, dict)),
				default=-1,
			)
			newMobIndexes = [4944]
			newMobIndexes.extend(sorted(
				(5672, 4685, 4815, 4701, 4760, 5710, 5731, 4856, 4549),
				key=lambda mobIdx: dungeonData[mobIdx]["static_listIndex"],
			))
			for offset, mobIdx in enumerate(newMobIndexes, 1):
				dungeonData[mobIdx]["listIndex"] = lastStoredIndex + offset
		if settingsVersion == 4:
			for mobIdx in (5672, 4685, 4815, 4701, 4760, 5710, 5731, 4856, 4549):
				dungeonData[mobIdx]["selected"] = False
			if restoreListIndex:
				lastStoredIndex = max(
					(settingData.get("listIndex", -1)
					 for settingData in storedDungeons.values()
					 if isinstance(settingData, dict)),
					default=-1,
				)
				newMobIndexes = sorted(
					(5672, 4685, 4815, 4701, 4760, 5710, 5731, 4856, 4549),
					key=lambda mobIdx: dungeonData[mobIdx]["static_listIndex"],
				)
				for offset, mobIdx in enumerate(newMobIndexes, 1):
					dungeonData[mobIdx]["listIndex"] = lastStoredIndex + offset
		if settingsVersion in (6, 7):
			for mobIdx in (4856, 4549):
				dungeonData[mobIdx]["selected"] = False
			if restoreListIndex:
				lastStoredIndex = max(
					(settingData.get("listIndex", -1)
					 for settingData in storedDungeons.values()
					 if isinstance(settingData, dict)),
					default=-1,
				)
				for offset, mobIdx in enumerate((4856, 4549), 1):
					dungeonData[mobIdx]["listIndex"] = lastStoredIndex + offset

		for mobIdx, settingData in storedDungeons.items():
			if mobIdx in dungeonData and isinstance(settingData, dict):
				dungeonInfo = dungeonData[mobIdx]
				if restoreListIndex:
					dungeonInfo["listIndex"] = settingData.get("listIndex", dungeonInfo["listIndex"]) + listIndexOffset
				dungeonInfo["showStatus"] = settingData.get("showStatus", dungeonInfo["showStatus"])
				dungeonInfo["alarm"] = settingData.get("alarm", dungeonInfo["alarm"])
				dungeonInfo["autoTicket"] = bool(settingData.get("autoTicket", False))
				dungeonInfo["selected"] = settingData.get("selected", dungeonInfo["selected"])
		__NormalizeDungeonListIndexes()
		if not any(dungeonInfo["selected"] for dungeonInfo in dungeonData.values()):
			firstDungeon = min(dungeonData.values(), key=lambda dungeonInfo: dungeonInfo["listIndex"])
			firstDungeon["selected"] = True
			saveMigratedSettings = True
		if saveMigratedSettings:
			SaveSettings()
	except (IOError, EOFError, cPickle.UnpicklingError, ValueError, TypeError):
		pass
def SaveSettings():
	global dungeonData
	try:
		__EnsureSettingsDirectory()
		dungeonSettings = {}
		for mobIdx, dungeonInfo in dungeonData.items():
			dungeonSettings[mobIdx] = {
				"listIndex" : dungeonInfo["listIndex"],
				"showStatus" : dungeonInfo["showStatus"],
				"alarm" : dungeonInfo["alarm"],
				"autoTicket" : dungeonInfo["autoTicket"],
				"selected" : dungeonInfo["selected"],
			}
		settings = {
			"version" : DUNGEON_SETTINGS_VERSION,
			"dungeons" : dungeonSettings,
		}
		with old_open(__GetSettingsPath(), 'wb') as f:
			cPickle.dump(settings, f)
	except IOError:
		pass

class ScrollBarSpecial(ui.Window):
	BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)
	CORNERS_AND_LINES_COLOR = grp.GenerateColor(0.3411, 0.3411, 0.3411, 1.0)
	BAR_NUMB = 9 #This is static value! Please dont touch in him.
	SCROLL_WIDTH= 8
	class MiddleBar(ui.DragButton):
		MIDDLE_BAR_COLOR = grp.GenerateColor(0.6470, 0.6470, 0.6470, 1.0)
		def __init__(self, horizontal_scroll):
			ui.DragButton.__init__(self)
			self.AddFlag("movable")
			self.horizontal_scroll = horizontal_scroll
			self.middle = ui.Bar()
			self.middle.SetParent(self)
			self.middle.AddFlag("attach")
			self.middle.AddFlag("not_pick")
			self.middle.SetColor(self.MIDDLE_BAR_COLOR)
			self.middle.SetSize(1, 1)
			self.middle.Show()
		def SetStaticScale(self, size):
			(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, base_width, size)
				self.middle.SetSize(base_width, size)
			else:
				ui.DragButton.SetSize(self, size, base_height)
				self.middle.SetSize(size, base_height)
		def SetSize(self, selfSize, fullSize):
			(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())
			
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, base_width, operator.truediv(int(selfSize), int(fullSize)) * selfSize)
				self.middle.SetSize(base_width, operator.truediv(int(selfSize), int(fullSize)) * selfSize)
			else:
				ui.DragButton.SetSize(self, operator.truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
				self.middle.SetSize(operator.truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
		def SetStaticSize(self, size):
			size = max(2, size)
			
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, size, self.middle.GetHeight())
				self.middle.SetSize(size, self.middle.GetHeight())
			else:
				ui.DragButton.SetSize(self, self.middle.GetWidth(), size)
				self.middle.SetSize(self.middle.GetWidth(), size)
	def __init__(self, horizontal_scroll = False):
		ui.Window.__init__(self)
		self.horizontal_scroll = horizontal_scroll
		self.scrollEvent = None
		self.scrollSpeed = 50
		self.sizeScale = 1.0
		self.bars = []
		for i in range(self.BAR_NUMB):
			br = ui.Bar()
			br.SetParent(self)
			br.AddFlag("attach")
			br.AddFlag("not_pick")
			br.SetColor([self.CORNERS_AND_LINES_COLOR, self.BASE_COLOR][i == (self.BAR_NUMB-1)])
			if not (i % 2 == 0): br.SetSize(1, 1)
			br.Show()
			self.bars.append(br)
		self.middleBar = self.MiddleBar(self.horizontal_scroll)
		self.middleBar.SetParent(self)
		self.middleBar.SetMoveEvent(ui.__mem_func__(self.OnScrollMove))
		self.middleBar.Show()
	def OnScrollMove(self):
		if not self.scrollEvent:
			return
		arg = float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else\
				float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())
		self.scrollEvent(arg)
	def SetScrollEvent(self, func):
		self.scrollEvent = func
	def SetScrollSpeed(self, speed):
		self.scrollSpeed = speed
	def OnMouseWheel(self, length):
		if not self.IsShow():
			return False
		length = int((length * 0.01) * self.scrollSpeed)
		if not self.horizontal_scroll:
			val = min(max(1, self.middleBar.GetLocalPosition()[1] - (length * 0.01) * self.scrollSpeed * self.sizeScale), self.GetHeight() - self.middleBar.GetHeight() - 1)
			self.middleBar.SetPosition(1, val)
		else:
			val = min(max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) *  self.scrollSpeed * self.sizeScale), self.GetWidth() - self.middleBar.GetWidth() - 1)
			self.middleBar.SetPosition(val, 1)
		self.OnScrollMove()
		return True
	def GetPos(self):
		return float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())
	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
		if not self.horizontal_scroll:
			if xMouseLocalPosition == 0 or xMouseLocalPosition == self.GetWidth():
				return
			y_pos = (yMouseLocalPosition - self.middleBar.GetHeight() // 2)
			self.middleBar.SetPosition(1, y_pos)
		else:
			if yMouseLocalPosition == 0 or yMouseLocalPosition == self.GetHeight():
				return
			x_pos = (xMouseLocalPosition - self.middleBar.GetWidth() // 2)
			self.middleBar.SetPosition(x_pos, 1)
		self.OnScrollMove()
	def SetSize(self, w, h):
		(width, height) = (max(3, w), max(3, h))
		ui.Window.SetSize(self, width, height)
		self.bars[0].SetSize(1, (height - 2))
		self.bars[0].SetPosition(0, 1)
		self.bars[2].SetSize((width - 2), 1)
		self.bars[2].SetPosition(1, 0)
		self.bars[4].SetSize(1, (height - 2))
		self.bars[4].SetPosition((width - 1), 1)
		self.bars[6].SetSize((width - 2), 1)
		self.bars[6].SetPosition(1, (height - 1))
		self.bars[8].SetSize((width - 2), (height - 2))
		self.bars[8].SetPosition(1, 1)
		self.bars[1].SetPosition(0, 0)
		self.bars[3].SetPosition((width - 1), 0)
		self.bars[5].SetPosition((width - 1), (height - 1))
		self.bars[7].SetPosition(0, (height - 1))
		if not self.horizontal_scroll:
			self.middleBar.SetStaticSize(width - 2)
			self.middleBar.SetSize(12, self.GetHeight())
		else:
			self.middleBar.SetStaticSize(height - 2)
			self.middleBar.SetSize(12, self.GetWidth())
		self.middleBar.SetRestrictMovementArea(1, 1, width - 2, height - 2)
	def SetScale(self, selfSize, fullSize):
		self.sizeScale = float(selfSize)/float(fullSize)
		if self.sizeScale <= 0.0305:
			self.sizeScale = 0.05
		self.middleBar.SetSize(selfSize, fullSize)
	def SetStaticScale(self, r_size):
		self.middleBar.SetStaticScale(r_size)
	def SetPosScale(self, fScale):
		pos = (math.ceil((self.GetHeight() - 2 - self.middleBar.GetHeight()) * fScale) + 1) if not self.horizontal_scroll else (math.ceil((self.GetWidth() - 2 - self.middleBar.GetWidth()) * fScale) + 1)
		self.SetPos(pos)
	def SetPos(self, pos):
		wPos = (1, pos) if not self.horizontal_scroll else (pos, 1)
		self.middleBar.SetPosition(*wPos)

class MultiTextLine(ui.Window):
	def Destroy(self):
		self.textRules = {}
	def __init__(self):
		ui.Window.__init__(self)
		self.Destroy()
		self.AddFlag("not_pick")
		self.textRules["textRange"] = 15
		self.textRules["text"] = ""
		self.textRules["textType"] = ""
		self.textRules["fontName"] = ""
		self.textRules["hexColor"] = 0
		self.textRules["fontColor"] = 0
		self.textRules["outline"] = 0
	def SetTextType(self, textType):
		self.textRules["textType"] = textType
		self.Refresh()
	def SetTextRange(self, textRange):
		self.textRules["textRange"] = textRange
		self.Refresh()
	def SetOutline(self, outline):
		self.textRules["outline"] = outline
		self.Refresh()
	def SetPackedFontColor(self, hexColor):
		self.textRules["hexColor"] = hexColor
		self.Refresh()
	def SetFontColor(self, r, g, b):
		self.textRules["fontColor"] =[r, g, b]
		self.Refresh()
	def SetFontName(self, fontName):
		self.textRules["fontName"] = fontName
		self.Refresh()
	def SetText(self, newText):
		self.textRules["text"] = newText
		self.Refresh()
	def Refresh(self):
		textRules = self.textRules
		if textRules["text"] == "":
			return
		self.children=[]
		outline = textRules["outline"]
		fontColor = textRules["fontColor"]
		hexColor = textRules["hexColor"]
		yRange = textRules["textRange"]
		fontName = textRules["fontName"]
		textType = textRules["textType"].split("#")
		totalTextList = textRules["text"].split("#")

		(xPosition, yPosition) = (0, 0)
		width = 0
		for text in totalTextList:
			childText = ui.TextLine()
			childText.SetParent(self)
			childText.AddFlag("not_pick")
			childText.SetPosition(xPosition, yPosition)
			if fontName != "":
				childText.SetFontName(fontName)
			if hexColor != 0:
				childText.SetPackedFontColor(hexColor)
			if fontColor != 0:
				childText.SetFontColor(*fontColor)
			if outline:
				childText.SetOutline()
			self.AddTextType(childText, textType)
			childText.SetText(str(text))
			if childText.GetTextSize()[0] > width:
				width = childText.GetTextSize()[0]
			childText.Show()
			self.children.append(childText)
			yPosition+=yRange

	def AddTextType(self, text,  typeArg):
		if len(typeArg) != 2:
			return
		_typeDict = {
			"vertical": {
				"top":text.SetVerticalAlignTop,
				"bottom":text.SetVerticalAlignBottom,
				"center":text.SetVerticalAlignCenter,
			},
			"horizontal": {
				"left":text.SetHorizontalAlignLeft,
				"right":text.SetHorizontalAlignRight,
				"center":text.SetHorizontalAlignCenter,
			},
			"all_align": {
				"1" : [text.SetHorizontalAlignCenter,text.SetVerticalAlignCenter,text.SetWindowHorizontalAlignCenter,text.SetWindowVerticalAlignCenter],
			},
		}
		(firstToken, secondToken) = tuple(typeArg)
		if firstToken in _typeDict:
			textType = _typeDict[firstToken][secondToken] if secondToken in _typeDict[firstToken] else None
			if textType != None:
				if isinstance(textType, list):
					for rule in textType:
						rule()
				else:
					textType()

class DungeonTeleportRow(ui.Window):
	WIDTH = 231
	HEIGHT = 54
	NAME_WIDTH = 153

	def __init__(self, owner, mobIdx, scale = 1.0):
		ui.Window.__init__(self)
		self.owner = _weakref.proxy(owner)
		self.mobIdx = mobIdx
		self.scale = float(scale)
		self.SetSize(self._Scaled(self.WIDTH), self._Scaled(self.HEIGHT))

		data = dungeonData[mobIdx]
		statusFontName = "Tahoma:11" if self.scale >= 0.9 else "Tahoma:9"
		self.body = ui.Button()
		self.body.SetParent(self)
		self.body.SetPosition(0, 0)
		self.body.SetSize(self._Scaled(self.WIDTH), self._Scaled(self.HEIGHT))
		wndMgr.SetScale(self.body.hWnd, self.scale, self.scale)
		self.body.SAFE_SetEvent(self.owner._SelectDungeon, mobIdx)
		self.body.Show()

		self.portrait = ui.ExpandedImageBox()
		self.portrait.SetParent(self)
		self.portrait.SetPosition(self._Scaled(1), self._Scaled(1))
		self.portrait.LoadImage(DUNGEON_ATLAS_IMG_DIR + ("portrait/%d_67x52.png" % data["finalBossVnum"]))
		self.portrait.SetScale(self.scale, self.scale)
		self.portrait.AddFlag("not_pick")
		self.portrait.Show()

		self.levelBackdrop = ui.Bar()
		self.levelBackdrop.SetParent(self)
		self.levelBackdrop.SetPosition(self._Scaled(8), self._Scaled(34))
		self.levelBackdrop.SetSize(self._Scaled(54), self._Scaled(17))
		self.levelBackdrop.SetColor(_DungeonSignedColor(0xff090807))
		self.levelBackdrop.AddFlag("not_pick")
		self.levelBackdrop.Show()
		self.levelText = ui.TextLine()
		self.levelText.SetParent(self)
		self.levelText.SetPosition(self._Scaled(35), self._Scaled(35))
		self.levelText.SetHorizontalAlignCenter()
		self.levelText.SetFontName("Tahoma:12" if self.scale >= 0.9 else "Tahoma:11")
		self.levelText.SetPackedFontColor(DUNGEON_COLOR_NAME)
		self.levelText.AddFlag("not_pick")
		self.levelText.Show()

		self.nameText = ui.TextLine()
		self.nameText.SetParent(self)
		self.nameText.SetPosition(self._Scaled(73), self._Scaled(4))
		self.nameText.SetPackedFontColor(DUNGEON_COLOR_NAME)
		self.nameText.AddFlag("not_pick")
		self.nameText.Show()

		self._SetName(data["name"])

		self.statusText = ui.TextLine()
		self.statusText.SetParent(self)
		self.statusText.SetPosition(self._Scaled(73), self._Scaled(36))
		self.statusText.SetFontName(statusFontName)
		self.statusText.SetPackedFontColor(_DungeonSignedColor(DUNGEON_STATUS_AVAILABLE_COLOR))
		self.statusText.AddFlag("not_pick")
		self.statusText.Show()

		self.upButton = ui.Button()
		self.upButton.SetParent(self)
		self.upButton.SetPosition(self._Scaled(162), self._Scaled(32))
		self.upButton.SetSize(self._Scaled(21), self._Scaled(21))
		_AtlasSetButtonVisuals(self.upButton, "control_v2/up_21")
		wndMgr.SetScale(self.upButton.hWnd, self.scale, self.scale)
		self.upButton.SAFE_SetEvent(self.owner._MoveDungeon, mobIdx, -1)
		self.upButton.SetToolTipText(_AtlasLocale("DUNGEON_TRACK_MOVE_UP", "Move up"))

		self.downButton = ui.Button()
		self.downButton.SetParent(self)
		self.downButton.SetPosition(self._Scaled(185), self._Scaled(32))
		self.downButton.SetSize(self._Scaled(21), self._Scaled(21))
		_AtlasSetButtonVisuals(self.downButton, "control_v2/down_21")
		wndMgr.SetScale(self.downButton.hWnd, self.scale, self.scale)
		self.downButton.SAFE_SetEvent(self.owner._MoveDungeon, mobIdx, 1)
		self.downButton.SetToolTipText(_AtlasLocale("DUNGEON_TRACK_MOVE_DOWN", "Move down"))

		self.hideButton = ui.Button()
		self.hideButton.SetParent(self)
		self.hideButton.SetPosition(self._Scaled(208), self._Scaled(32))
		self.hideButton.SetSize(self._Scaled(21), self._Scaled(21))
		_AtlasSetButtonVisuals(self.hideButton, "control_v2/eye_21")
		wndMgr.SetScale(self.hideButton.hWnd, self.scale, self.scale)
		self.hideButton.SAFE_SetEvent(self.owner._HideDungeon, mobIdx)
		self.hideButton.SetToolTipText(_AtlasLocale("DUNGEON_TRACK_HIDE", "Hide dungeon"))

		self.Refresh()

	def _Scaled(self, value):
		return int(round(float(value) * self.scale))

	def _SetName(self, name):
		fullName = " ".join(str(name).split())
		limit = self._Scaled(self.NAME_WIDTH)
		largestSize = 12 if self.scale >= 0.9 else 10
		for fontSize in range(largestSize, 7, -1):
			self.nameText.SetFontName("Tahoma:%db" % fontSize)
			# Native font changes alone do not invalidate cached text metrics.
			self.nameText.SetText("")
			self.nameText.SetText(fullName)
			if self.nameText.GetTextSize()[0] <= limit:
				return
		# Guard future names longer than the current roster; full name stays in the tooltip.
		self.nameText.SetText(self._Ellipsize(fullName, self.nameText, limit))

	def _Ellipsize(self, text, widget, limit):
		widget.SetText(text)
		if widget.GetTextSize()[0] <= limit:
			return text
		ellipsis = u"…"
		bounded = ""
		for character in text:
			widget.SetText(bounded + character + ellipsis)
			if widget.GetTextSize()[0] > limit:
				break
			bounded += character
		return bounded.rstrip() + ellipsis

	def _SetStatusText(self, text, countdownText = None):
		fullText = str(text)
		limit = self._Scaled(85)
		self.statusText.SetText(fullText)
		if self.statusText.GetTextSize()[0] <= limit:
			return fullText
		if countdownText is not None:
			fallback = "NAVRAT %s" if app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz" else "RETURN %s"
			compactText = _AtlasLocale("DUNGEON_REJOIN_STATUS", fallback) % countdownText
			self.statusText.SetText(compactText)
			if self.statusText.GetTextSize()[0] <= limit:
				return fullText
			compactText = u"… " + countdownText
			self.statusText.SetText(compactText)
			if self.statusText.GetTextSize()[0] > limit:
				self.statusText.SetText(countdownText)
			return fullText
		self.statusText.SetText(self._Ellipsize(fullText, self.statusText, limit))
		return fullText

	def Refresh(self):
		data = dungeonData[self.mobIdx]
		rejoinOffer = GetDungeonRejoinOffer(self.mobIdx)
		visibleAlpha = 1.0 if data["showStatus"] else 0.52
		self.levelText.SetText("Lv. %d+" % data["minLevel"])
		for widget in (self.body, self.portrait, self.nameText, self.statusText, self.levelText):
			_AtlasSetWidgetAlpha(widget, visibleAlpha)
		if data["showStatus"]:
			self.hideButton.SAFE_SetEvent(self.owner._HideDungeon, self.mobIdx)
		else:
			self.hideButton.SAFE_SetEvent(self.owner._RestoreDungeon, self.mobIdx)
		_AtlasSetButtonVisuals(self.body, "row/dungeon_231x54", data["selected"])
		lockedByLevel = IsDungeonLevelLocked(data, player.GetStatus(player.LEVEL))
		leftTime = data["server_cooldown"] - app.GetGlobalTimeStamp()
		if rejoinOffer:
			leftTime = max(0, int(rejoinOffer["expiresAt"]) - app.GetGlobalTimeStamp())
			fullStatusText = self._SetStatusText(
				_DungeonRejoinStatusText(leftTime), "%d:%02d" % (leftTime // 60, leftTime % 60))
			statusColor = DUNGEON_STATUS_AVAILABLE_COLOR
		elif leftTime > 0:
			fullStatusText = self._SetStatusText(FormatTime(leftTime))
			statusColor = DUNGEON_STATUS_UNAVAILABLE_COLOR
		elif lockedByLevel:
			fullStatusText = self._SetStatusText("LV. %d+" % data["minLevel"])
			statusColor = DUNGEON_STATUS_UNAVAILABLE_COLOR
		else:
			fullStatusText = self._SetStatusText(_AtlasLocale("DUNGEON_TRACK_ACTIVE", "AVAILABLE"))
			statusColor = DUNGEON_STATUS_AVAILABLE_COLOR
		packedStatusColor = _DungeonSignedColor(statusColor)
		self.statusText.SetPackedFontColor(packedStatusColor)
		self.body.SetToolTipText("%s | %s" % (data["name"], fullStatusText))

	def SetControlVisibility(self, visible):
		if not dungeonData[self.mobIdx]["showStatus"]:
			self.upButton.Hide()
			self.downButton.Hide()
			self.hideButton.SetToolTipText(_AtlasLocale("DUNGEON_ATLAS_RESTORE", "Restore dungeon"))
			self.hideButton.Show()
			return
		self.hideButton.SetToolTipText(_AtlasLocale("DUNGEON_TRACK_HIDE", "Hide dungeon"))
		for control in (self.upButton, self.downButton, self.hideButton):
			if visible:
				control.Show()
			else:
				control.Hide()

	def OnMouseWheel(self, length):
		return self.owner.OnMouseWheel(length)


class DungeonTeleportPage(ui.Window):
	WIDTH = 821
	HEIGHT = 491
	CATALOG_RECT = (6, 18, 247, 455)
	DETAIL_RECT = (259, 18, 307, 455)
	STATS_RECT = (572, 18, 239, 455)
	ROW_STEP = 57
	VISIBLE_ROWS = 6
	SCROLL_THUMB_Y = 62
	SCROLL_TRAVEL = 276
	BOSS_PREVIEW_FIRST_TIMEOUT = 1.0
	BOSS_PREVIEW_RETRY_INTERVAL = 2.0

	def __init__(self, owner, scale = 1.0):
		ui.Window.__init__(self)
		self.owner = _weakref.proxy(owner)
		self.scale = float(scale)
		self.SetSize(self._Scaled(self.WIDTH), self._Scaled(self.HEIGHT))
		self.rows = {}
		self.visibleMobIndexes = []
		self.scrollOffset = 0
		self.showLocked = True
		self.showHidden = False
		self.ticketVnum = 0
		self.lastRefresh = 0.0
		self.dropWindow = None
		self.lastShopClick = 0
		self.activeRank = 0
		self.rankCache = {}
		self.renderTargetIndex = -1
		self.renderRequestedBossVnum = 0
		self.renderBossVnum = 0
		self.renderBossRequestTime = 0.0
		self.renderBossNextRetryTime = 0.0
		self.renderBossAttemptCount = 0
		self.renderBossSelectionSucceeded = False
		self.renderTarget = None
		self.elementIcons = []
		self.elementBossVnum = None
		self.staticWidgets = []
		self.__BuildWindow()
		LoadSettings()
		self.Refresh()

	def _Scaled(self, value):
		return int(round(float(value) * self.scale))

	def _Image(self, parent, position, path):
		image = ui.ExpandedImageBox()
		image.SetParent(parent)
		image.SetPosition(self._Scaled(position[0]), self._Scaled(position[1]))
		image.LoadImage(DUNGEON_ATLAS_IMG_DIR + path)
		if self.scale != 1.0:
			image.SetScale(self.scale, self.scale)
		image.AddFlag("not_pick")
		image.Show()
		self.staticWidgets.append(image)
		return image

	def _Text(self, parent, position, text, color = 0xffd9d2c8, align = "left"):
		label = ui.TextLine()
		label.SetParent(parent)
		label.SetPosition(self._Scaled(position[0]), self._Scaled(position[1]))
		label.SetText(text)
		label.SetPackedFontColor(_DungeonSignedColor(color))
		if align == "center":
			label.SetHorizontalAlignCenter()
		elif align == "right":
			label.SetHorizontalAlignRight()
		label.AddFlag("not_pick")
		label.Show()
		self.staticWidgets.append(label)
		return label

	def _Button(self, parent, position, size, family, text, event, *eventArgs):
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(self._Scaled(position[0]), self._Scaled(position[1]))
		button.SetSize(self._Scaled(size[0]), self._Scaled(size[1]))
		_AtlasSetButtonVisuals(button, family)
		wndMgr.SetScale(button.hWnd, self.scale, self.scale)
		button.SetText(text)
		button.SAFE_SetEvent(event, *eventArgs)
		button.Show()
		self.staticWidgets.append(button)
		return button

	def __BuildWindow(self):
		self.surface = self._Image(self, (0, 0), "surface/content_821x491.png")
		self.catalogPanel = self._Image(self, self.CATALOG_RECT[:2], "panel/catalog_247x455.png")
		self.detailPanel = self._Image(self, self.DETAIL_RECT[:2], "panel/detail_307x455.png")
		self.statsPanel = self._Image(self, self.STATS_RECT[:2], "panel/stats_239x455.png")

		self._Image(self, (12, 24), "header/header_235x28.png")
		self._Image(self, (265, 24), "header/header_295x28.png")
		self._Image(self, (578, 24), "header/header_227x28.png")
		self._Text(self, (21, 31), _AtlasLocale("DUNGEON_ATLAS_LIST", "DUNGEON LIST"), DUNGEON_COLOR_GOLD)
		self._Text(self, (274, 31), _AtlasLocale("DUNGEON_ATLAS_DETAILS", "DUNGEON DETAILS"), DUNGEON_COLOR_GOLD)
		self._Text(self, (587, 31), _AtlasLocale("DUNGEON_ATLAS_PERFORMANCE", "PERFORMANCE & RANKS"), DUNGEON_COLOR_GOLD)

		self.catalogList = ui.Window()
		self.catalogList.SetParent(self)
		self.catalogList.SetPosition(self._Scaled(14), self._Scaled(60))
		self.catalogList.SetSize(self._Scaled(231), self._Scaled(361))
		self.catalogList.Show()

		for mobIdx in dungeonData:
			row = DungeonTeleportRow(self, mobIdx, self.scale)
			row.SetParent(self.catalogList)
			row.Hide()
			self.rows[mobIdx] = row

		self.scrollTrack = self._Image(self, (241, 60), "scrollbar/track_12x373.png")
		self.scrollThumb = ui.DragButton()
		self.scrollThumb.SetParent(self)
		self.scrollThumb.SetPosition(self._Scaled(243), self._Scaled(self.SCROLL_THUMB_Y))
		self.scrollThumb.SetSize(self._Scaled(8), self._Scaled(93))
		_AtlasSetButtonVisuals(self.scrollThumb, "scrollbar/thumb_8x93")
		wndMgr.SetScale(self.scrollThumb.hWnd, self.scale, self.scale)
		self.scrollThumb.SetRestrictMovementArea(
			self._Scaled(243), self._Scaled(self.SCROLL_THUMB_Y),
			self._Scaled(8), self._Scaled(369),
		)
		self.scrollThumb.SetMoveEvent(ui.__mem_func__(self._OnScrollThumbMove))
		self.scrollThumb.Show()

		self.showLockedButton = self._Button(self, (16, 438), (18, 18), "choice/checkbox", "", self._ToggleShowLocked)
		self.showLockedText = self._Text(self, (40, 441), _AtlasLocale("DUNGEON_ATLAS_SHOW_LOCKED", "Show locked"), 0xffb9afa4)
		self.showHiddenButton = self._Button(self, (137, 438), (18, 18), "choice/checkbox", "", self._ToggleShowHidden)
		self.hiddenCountText = self._Text(self, (161, 441), "", 0xffb9afa4)

		self.bossFallback = self._Image(self, (268, 60), "boss/render_target_fallback_289x179.png")
		self.renderTarget = ui.WikiRenderTargetUi()
		self.renderTarget.SetParent(self)
		self.renderTarget.SetPosition(self._Scaled(268), self._Scaled(60))
		self.renderTarget.SetSize(self._Scaled(289), self._Scaled(179))
		self.renderTarget.Hide()
		self.bossFrame = self._Image(self, (268, 60), "boss/render_target_frame_289x179.png")
		for position, size, color in (
			((dungeonpresentation.CAPTION_X, dungeonpresentation.CAPTION_Y + 1),
			 (dungeonpresentation.CAPTION_WIDTH, dungeonpresentation.CAPTION_HEIGHT - 1), 0xff090807),
			((dungeonpresentation.CAPTION_X, dungeonpresentation.CAPTION_Y),
			 (dungeonpresentation.CAPTION_WIDTH, 1), 0xff5f4024)):
			caption = ui.Bar()
			caption.SetParent(self)
			caption.SetPosition(self._Scaled(position[0]), self._Scaled(position[1]))
			caption.SetSize(self._Scaled(size[0]), self._Scaled(size[1]))
			caption.SetColor(_DungeonSignedColor(color))
			caption.AddFlag("not_pick")
			caption.Show()
			self.staticWidgets.append(caption)
		self.bossName = self._Text(self, (dungeonpresentation.NAME_X, dungeonpresentation.NAME_Y), "", DUNGEON_COLOR_GOLD)
		self.bossName.SetFontName("Tahoma:14" if self.scale >= 0.9 else "Tahoma:12")

		for element in dungeonpresentation.ELEMENT_ASSETS:
			icon = ui.ExpandedImageBox()
			icon.SetParent(self)
			icon.LoadImage(dungeonpresentation.ELEMENT_ROOT + "element_%s_24.png" % element)
			factor = float(self._Scaled(dungeonpresentation.ICON_SIZE)) / icon.GetWidth()
			if factor != 1.0:
				icon.SetScale(factor, factor)
			icon.AddFlag("not_pick")
			icon.Hide()
			self.elementIcons.append(icon)
			self.staticWidgets.append(icon)

		self.levelValue = self.__BuildInfoRow(246, "level_20.png", _AtlasLocale("DUNGEON_TRACK_LEVEL_INFO", "Required level"))
		self.groupValue = self.__BuildInfoRow(277, "group_20.png", _AtlasLocale("DUNGEON_TRACK_GROUP_INFO", "Group required"))
		self.cooldownValue = self.__BuildInfoRow(308, "cooldown_20.png", _AtlasLocale("DUNGEON_TRACK_COOLDOWN_INFO", "Cooldown"))

		self._Image(self, (268, 340), "info/ticket_289x48.png")
		self._Image(self, (274, 354), "icon/ticket_20.png")
		self.ticketIcon = ui.ExpandedImageBox()
		self.ticketIcon.SetParent(self)
		self.ticketIcon.SetPosition(self._Scaled(299), self._Scaled(348))
		self.ticketIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self._OverInTicket)
		self.ticketIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self._OverOutTicket)
		self.ticketName = self._Text(self, (334, 348), "", DUNGEON_COLOR_GOLD)
		self.ticketCount = self._Text(self, (329, 368), "", DUNGEON_COLOR_GOLD, "right")
		self.ticketCount.SetOutline()
		self.shopButton = self._Button(self, (465, 350), (86, 28), "button/shop_86x28", _AtlasLocale("DUNGEON_ATLAS_SHOP", "SHOP"), self._OpenTicketShop)
		self.autoTicketCheck = self._Button(self, (334, 366), (15, 14), "choice/checkbox", "", self._ToggleAutoTicket)
		self.autoTicketCheck.SetToolTipText(_AtlasLocale("DUNGEON_TRACK_AUTO_TICKET", "Auto ticket") + " (VIP)")
		self.autoTicketText = self._Text(self, (353, 367), "", 0xffd9d2c8)
		self.autoTicketText.SetFontName("Tahoma:12")
		self.autoTicketText.SetText(_AtlasLocale("DUNGEON_TRACK_AUTO_TICKET_SHORT", "Auto ticket") + " (VIP)")

		self.alarmButton = self._Button(self, (320, 392), (28, 28), "button/icon_28x28", "", self._ToggleAlarm)
		self.alarmButton.SetToolTipText(_AtlasLocale("DUNGEON_TRACK_ALARM", "Notify when cooldown ends"))
		self._Image(self, (324, 396), "icon/alarm_20.png")
		self.guideButton = self._Button(self, (358, 392), (110, 28), "button/guide_110x28", _AtlasLocale("DUNGEON_ATLAS_GUIDE", "GUIDE"), self._OpenGuide)
		self.dropButton = self._Button(self, (478, 392), (28, 28), "button/icon_28x28", "", self._ToggleDrop)
		self.dropButton.SetToolTipText(localeInfo.DUNGEON_DROP_BUTTON)
		self._Image(self, (482, 396), "icon/shop_20.png")
		self.enterButton = self._Button(self, (315, 425), (196, 36), "button/enter_196x36", _AtlasLocale("DUNGEON_ATLAS_ENTER", "ENTER"), self._EnterDungeon)

		self._Text(self, (584, 65), _AtlasLocale("DUNGEON_TRACK_PERSONAL_STATISTICS", "PERSONAL STATISTICS"), DUNGEON_COLOR_GOLD)
		self.completedValue = self.__BuildStatRow(86, "completed_20.png", _AtlasLocale("DUNGEON_TRACK_COMPLETED", "Completed"), False, DUNGEON_COLOR_GREEN)
		self.fastestValue = self.__BuildStatRow(117, "fastest_20.png", _AtlasLocale("DUNGEON_TRACK_FASTEST", "Fastest"), True, DUNGEON_COLOR_BLUE)
		self.damageValue = self.__BuildStatRow(148, "damage_20.png", _AtlasLocale("DUNGEON_TRACK_DMG", "Max. boss damage"), False, DUNGEON_COLOR_AMBER)
		self._Text(self, (584, 190), _AtlasLocale("DUNGEON_ATLAS_SERVER_RANK", "SERVER RANK"), DUNGEON_COLOR_GOLD)
		self.__BuildRankPlaceholders()

	def __BuildInfoRow(self, y, iconName, labelText):
		self._Image(self, (268, y), "info/info_row_289x28.png")
		self._Image(self, (274, y + 4), "icon/" + iconName)
		self._Text(self, (299, y + 7), labelText, DUNGEON_COLOR_DIM)
		return self._Text(self, (548, y + 7), "", DUNGEON_COLOR_DIM, "right")

	def __BuildStatRow(self, y, iconName, labelText, alternate, valueColor):
		asset = "info/stat_row_221x28_alternate.png" if alternate else "info/stat_row_221x28_normal.png"
		self._Image(self, (581, y), asset)
		self._Image(self, (587, y + 4), "icon/" + iconName)
		self._Text(self, (612, y + 7), labelText, DUNGEON_COLOR_DIM)
		return self._Text(self, (795, y + 7), "", valueColor, "right")

	def __BuildRankPlaceholders(self):
		isCzech = app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz"
		labels = ("POČET", "ČAS", "DMG") if isCzech else ("COUNT", "TIME", "DMG")
		self.rankValueTitles = (
			_AtlasLocale("DUNGEON_TRACK_RANK_COMPLETED_TITLE", "COUNT"),
			_AtlasLocale("DUNGEON_TRACK_RANK_FASTEST_TITLE", "TIME"),
			_AtlasLocale("DUNGEON_TRACK_RANK_DMG_TITLE", "DMG"),
		)
		self.rankButtons = []
		for rankIdx in range(3):
			button = self._Button(self, (581 + rankIdx * 73, 211), (68, 28), "button/rank_68x28", labels[rankIdx], self._SelectRank, rankIdx)
			self.rankButtons.append(button)
		self.rankLines = []
		self._Text(self, (588, 249), "#", 0xff8f8478)
		self._Text(self, (609, 249), _AtlasLocale("DUNGEON_TRACK_RANK_NAME", "Player"), 0xffb9afa4)
		self.rankValueHeader = self._Text(self, (795, 249), self.rankValueTitles[0], 0xffb9afa4, "right")
		for lineIdx in range(4):
			y = 274 + lineIdx * 27
			position = self._Text(self, (588, y), "%d." % (lineIdx + 1), 0xffffcb67)
			name = self._Text(self, (609, y), "-", 0xffd7cfc5)
			value = self._Text(self, (795, y), "-", 0xffeee6dc, "right")
			self.rankLines.append((position, name, value))

	def GetCurrentSelectedDungeon(self):
		for mobIdx, dungeonInfo in dungeonData.items():
			if dungeonInfo["selected"]:
				return mobIdx
		return -1

	def OpenTrackedDungeon(self, mobIdx):
		if mobIdx not in dungeonData:
			return
		self.showHidden = self.showHidden or not dungeonData[mobIdx]["showStatus"]
		self.showLocked = True
		self._SelectDungeon(mobIdx, True)
		if mobIdx in self.visibleMobIndexes:
			self.scrollOffset = self.visibleMobIndexes.index(mobIdx)
			self._RefreshCatalogue()

	def _SelectDungeon(self, mobIdx, includeHidden=False):
		if mobIdx not in dungeonData or (not includeHidden and not dungeonData[mobIdx]["showStatus"]):
			return
		self._ResetRenderTarget()
		for dungeonInfo in dungeonData.values():
			dungeonInfo["selected"] = False
		dungeonData[mobIdx]["selected"] = True
		SaveSettings()
		self.Refresh()

	def _MoveDungeon(self, mobIdx, direction):
		indexes = list(self.visibleMobIndexes)
		if mobIdx not in indexes:
			return
		current = indexes.index(mobIdx)
		target = current + direction
		if target < 0 or target >= len(indexes):
			return
		otherMobIdx = indexes[target]
		dungeonData[mobIdx]["listIndex"], dungeonData[otherMobIdx]["listIndex"] = dungeonData[otherMobIdx]["listIndex"], dungeonData[mobIdx]["listIndex"]
		SaveSettings()
		self._RefreshCatalogue()

	def _HideDungeon(self, mobIdx):
		if mobIdx not in dungeonData:
			return
		dungeonData[mobIdx]["showStatus"] = False
		if dungeonData[mobIdx]["selected"]:
			dungeonData[mobIdx]["selected"] = False
			for candidateMobIdx, candidate in sorted(dungeonData.items(), key=lambda entry: entry[1]["listIndex"]):
				if candidate["showStatus"]:
					candidate["selected"] = True
					break
		SaveSettings()
		self.Refresh()

	def _RestoreDungeon(self, mobIdx):
		if mobIdx not in dungeonData or dungeonData[mobIdx]["showStatus"]:
			return
		dungeonData[mobIdx]["showStatus"] = True
		SaveSettings()
		self.Refresh()

	def _ToggleShowLocked(self):
		self.showLocked = not self.showLocked
		self.scrollOffset = 0
		self._RefreshCatalogue()

	def _ToggleShowHidden(self):
		self.showHidden = not self.showHidden
		self.scrollOffset = 0
		self._RefreshCatalogue()

	def _ToggleAlarm(self):
		mobIdx = self.GetCurrentSelectedDungeon()
		if mobIdx == -1:
			return
		dungeonInfo = dungeonData[mobIdx]
		dungeonInfo["alarm"] = not dungeonInfo["alarm"]
		SaveSettings()
		self._RefreshDetails()
		_RefreshCountdownSelection(dungeonInfo["alarm"])

	def _ToggleAutoTicket(self):
		mobIdx = self.GetCurrentSelectedDungeon()
		if mobIdx not in dungeonData:
			return
		dungeonInfo = dungeonData[mobIdx]
		if not player.IsVipActive():
			dungeonInfo["autoTicket"] = False
			_AtlasSetButtonVisuals(self.autoTicketCheck, "choice/checkbox")
			chat.AppendChat(chat.CHAT_TYPE_INFO, _AtlasLocale("DUNGEON_TRACK_AUTO_TICKET_VIP", "Active VIP is required."))
			return
		dungeonInfo["autoTicket"] = not dungeonInfo["autoTicket"]
		SaveSettings()
		self._RefreshDetails()

	def _RefreshCatalogue(self):
		visible = []
		hiddenCount = 0
		level = player.GetStatus(player.LEVEL)
		now = app.GetGlobalTimeStamp()
		for mobIdx, dungeonInfo in dungeonData.items():
			hasRejoin = GetDungeonRejoinOffer(mobIdx) is not None
			if not dungeonInfo["showStatus"]:
				hiddenCount += 1
			if not dungeonInfo["showStatus"] and not self.showHidden and not hasRejoin:
				continue
			locked = IsDungeonLevelLocked(dungeonInfo, level) or dungeonInfo["server_cooldown"] > now
			if locked and not self.showLocked and not hasRejoin:
				continue
			visible.append((mobIdx, dungeonInfo))
		visible.sort(key=lambda entry: entry[1]["listIndex"])
		self.visibleMobIndexes = [entry[0] for entry in visible]
		maximumOffset = max(0, len(visible) - self.VISIBLE_ROWS)
		self.scrollOffset = min(maximumOffset, max(0, self.scrollOffset))
		for row in self.rows.values():
			row.Hide()
		for displayIndex, mobIdx in enumerate(self.visibleMobIndexes[self.scrollOffset:self.scrollOffset + self.VISIBLE_ROWS]):
			row = self.rows[mobIdx]
			row.SetPosition(0, self._Scaled(displayIndex * self.ROW_STEP))
			row.Refresh()
			row.SetControlVisibility(dungeonData[mobIdx]["selected"])
			row.Show()
		_AtlasSetButtonVisuals(self.showLockedButton, "choice/checkbox", self.showLocked)
		_AtlasSetButtonVisuals(self.showHiddenButton, "choice/checkbox", self.showHidden)
		self.hiddenCountText.SetText(_AtlasLocale("DUNGEON_ATLAS_SHOW_HIDDEN", "Hidden (%d)") % hiddenCount)
		if maximumOffset:
			self.scrollThumb.SetPosition(self._Scaled(243), self._Scaled(self.SCROLL_THUMB_Y + int(float(self.scrollOffset) / maximumOffset * self.SCROLL_TRAVEL)))
			self.scrollThumb.Show()
		else:
			self.scrollThumb.SetPosition(self._Scaled(243), self._Scaled(self.SCROLL_THUMB_Y))
			self.scrollThumb.Hide()

	def _OnScrollThumbMove(self):
		maximumOffset = max(0, len(self.visibleMobIndexes) - self.VISIBLE_ROWS)
		if not maximumOffset:
			return
		unusedX, localY = self.scrollThumb.GetLocalPosition()
		travel = max(1, self._Scaled(self.SCROLL_TRAVEL))
		relativeY = min(travel, max(0, localY - self._Scaled(self.SCROLL_THUMB_Y)))
		newOffset = int(round(float(relativeY) / float(travel) * maximumOffset))
		if newOffset != self.scrollOffset:
			self.scrollOffset = newOffset
			self._RefreshCatalogue()

	def _RefreshTicket(self, dungeonInfo):
		self.ticketVnum = 0
		self.ticketIcon.Hide()
		self.ticketName.SetText(_AtlasLocale("DUNGEON_TRACK_NO_TICKET", "No ticket required"))
		self.ticketCount.SetText("")
		self.shopButton.Hide()
		if not dungeonInfo["ticket"]:
			return
		ticketVnum, ticketCount = dungeonInfo["ticket"][0]
		try:
			item.SelectItem(ticketVnum)
			iconFileName = item.GetIconImageFileName()
			itemName = item.GetItemName()
			self.ticketIcon.LoadImage(iconFileName)
			self.ticketIcon.SetScale(self.scale, self.scale)
			self.ticketIcon.Show()
			self.ticketVnum = ticketVnum
			self.ticketName.SetText(itemName)
			self.ticketCount.SetText("x%d" % ticketCount if ticketCount > 1 else "")
		except (RuntimeError, TypeError):
			self.ticketIcon.Hide()
			self.ticketName.SetText(_AtlasLocale("DUNGEON_TRACK_NO_TICKET", "No ticket required"))
			self.ticketCount.SetText("")
			return
		if dungeonInfo["ticketShop"]:
			self.shopButton.Show()

	def _RefreshBossElements(self, bossVnum):
		if self.elementBossVnum == bossVnum:
			return
		self.elementBossVnum = bossVnum
		elements = dungeonpresentation.ReadBossElements(
			bossVnum, getattr(app, "ENABLE_ELEMENT_ADD", False), nonplayer)
		for icon in self.elementIcons:
			icon.Hide()
		for element, x, y in dungeonpresentation.ElementPositions(elements):
			icon = self.elementIcons[element]
			icon.SetPosition(self._Scaled(x), self._Scaled(y))
			icon.Show()
		self.bossName.SetLimitWidth(self._Scaled(dungeonpresentation.BossNameWidth(elements)))

	def _RefreshDetails(self):
		mobIdx = self.GetCurrentSelectedDungeon()
		if mobIdx == -1 or mobIdx not in dungeonData:
			return
		dungeonInfo = dungeonData[mobIdx]
		rejoinOffer = GetDungeonRejoinOffer(mobIdx)
		if getattr(self, "dropWindow", None) and self.dropWindow.IsShow():
			self.dropWindow.SetDungeon(dungeonInfo["finalBossVnum"], dungeonInfo["name"])
		self.bossName.SetText(nonplayer.GetMonsterName(dungeonInfo["finalBossVnum"]))
		self._RefreshBossElements(dungeonInfo["finalBossVnum"])
		self.levelValue.SetText("LV. %d+" % dungeonInfo["minLevel"])
		lockedByLevel = IsDungeonLevelLocked(dungeonInfo, player.GetStatus(player.LEVEL))
		self.levelValue.SetPackedFontColor(_DungeonSignedColor(
			DUNGEON_STATUS_UNAVAILABLE_COLOR if lockedByLevel else DUNGEON_COLOR_GOLD))
		self.groupValue.SetText(_AtlasLocale("DUNGEON_TRACK_TRUE", "Yes") if dungeonInfo["group"] else _AtlasLocale("DUNGEON_TRACK_FALSE", "No"))
		self.groupValue.SetPackedFontColor(_DungeonSignedColor(DUNGEON_COLOR_DIM))
		cooldown = max(0, dungeonInfo["server_cooldown"] - app.GetGlobalTimeStamp())
		if rejoinOffer:
			rejoinLeft = max(0, int(rejoinOffer["expiresAt"]) - app.GetGlobalTimeStamp())
			self.cooldownValue.SetText(_DungeonRejoinStatusText(rejoinLeft))
			self.cooldownValue.SetPackedFontColor(_DungeonSignedColor(DUNGEON_STATUS_AVAILABLE_COLOR))
		else:
			self.cooldownValue.SetText(FormatTime(cooldown) if cooldown else FormatTimeEx(dungeonInfo["cooldown"]))
			self.cooldownValue.SetPackedFontColor(_DungeonSignedColor(
				DUNGEON_STATUS_UNAVAILABLE_COLOR if cooldown else DUNGEON_COLOR_DIM))
		self.completedValue.SetText(NumberToDecimalString(dungeonInfo["server_completed"]))
		self.fastestValue.SetText(FormatTimeEx(dungeonInfo["server_fastest"]))
		self.damageValue.SetText(NumberToDecimalString(dungeonInfo["server_damage"]))
		_AtlasSetButtonVisuals(self.alarmButton, "button/icon_28x28", dungeonInfo["alarm"])
		_AtlasSetButtonVisuals(self.autoTicketCheck, "choice/checkbox", bool(dungeonInfo["autoTicket"]) and player.IsVipActive())
		if player.IsVipActive():
			self.autoTicketCheck.Enable()
		else:
			self.autoTicketCheck.Disable()
		self._RefreshTicket(dungeonInfo)
		if rejoinOffer:
			self.enterButton.SetText(_DungeonRejoinButtonText())
			self.enterButton.Show()
		elif dungeonInfo["directEntry"]:
			self.enterButton.SetText(_AtlasLocale("DUNGEON_ATLAS_ENTER", "ENTER"))
			self.enterButton.Show()
		else:
			self.enterButton.SetText(_AtlasLocale("DUNGEON_ATLAS_ENTER", "ENTER"))
			self.enterButton.Hide()
		if mobIdx in DUNGEON_WIKI_COMMANDS:
			self.guideButton.Enable()
		else:
			self.guideButton.Disable()
		if self.IsShow() and self.renderRequestedBossVnum != dungeonInfo["finalBossVnum"]:
			self._SelectBossModel(dungeonInfo["finalBossVnum"])
		self._RefreshRank()

	def _OverInTicket(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.tooltipItem and self.ticketVnum:
			interface.tooltipItem.SetItemToolTip(self.ticketVnum)

	def _OverOutTicket(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.tooltipItem:
			interface.tooltipItem.HideToolTip()

	def _OpenTicketShop(self):
		currentDungeon = self.GetCurrentSelectedDungeon()
		if currentDungeon == -1:
			return
		dungeonInfo = dungeonData[currentDungeon]
		if not dungeonInfo["ticket"] or not dungeonInfo["ticketShop"]:
			return
		if self.lastShopClick > app.GetGlobalTimeStamp():
			chat.AppendChat(chat.CHAT_TYPE_INFO, _AtlasLocale("DUNGEON_TRACK_SLOW_INFO", "Please wait."))
			return
		self.lastShopClick = app.GetGlobalTimeStamp() + 2
		self._SendQuestAction("SHOP")

	def _OpenGuide(self):
		currentDungeon = self.GetCurrentSelectedDungeon()
		if currentDungeon not in DUNGEON_WIKI_COMMANDS:
			return
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			interface.OpenWikiWindow()
			interface.wndWiki.LoadData(DUNGEON_WIKI_COMMANDS[currentDungeon])
			interface.wndWiki.SetTop()

	def _ToggleDrop(self):
		mobIdx = self.GetCurrentSelectedDungeon()
		if mobIdx not in dungeonData:
			return
		if self.dropWindow is None:
			import uiDungeonDrop
			self.dropWindow = uiDungeonDrop.DungeonDropWindow()
		if self.dropWindow.IsShow():
			self.dropWindow.Close()
		else:
			info = dungeonData[mobIdx]
			self.dropWindow.Open(info["finalBossVnum"], info["name"], self)

	def _EnterDungeon(self):
		currentDungeon = self.GetCurrentSelectedDungeon()
		if currentDungeon == -1:
			return
		rejoinOffer = GetDungeonRejoinOffer(currentDungeon)
		if rejoinOffer:
			self.owner.Close()
			osfInfo.dungeonRejoinCMD = "ACCEPT#{}".format(rejoinOffer["token"])
			event.QuestButtonClick(int(rejoinOffer["questIdx"]))
			return
		if not dungeonData[currentDungeon]["directEntry"]:
			return
		self.owner.Close()
		if dungeonData[currentDungeon]["autoTicket"] and player.IsVipActive():
			self._SendQuestAction("AUTO_ENTER")
		else:
			self._SendQuestAction("ENTER")

	def _SendQuestAction(self, questMode):
		currentDungeon = self.GetCurrentSelectedDungeon()
		if currentDungeon == -1:
			return
		osfInfo.dungeonInfoCMD = questMode + "#" + str(currentDungeon)
		event.QuestButtonClick(int(osfInfo.dungeonInfoQuestIdx))

	def _SelectBossModel(self, finalBossVnum):
		self._ResetRenderTarget()
		self.renderRequestedBossVnum = int(finalBossVnum)
		self.bossFallback.Show()
		self.renderTarget.Hide()
		self._RequestBossModel()
		self._RefreshBossPreview()

	def _RequestBossModel(self):
		if not self.renderRequestedBossVnum:
			return
		now = app.GetTime()
		self.renderBossRequestTime = now
		self.renderBossAttemptCount += 1
		if self.renderBossAttemptCount == 1:
			self.renderBossNextRetryTime = now + self.BOSS_PREVIEW_FIRST_TIMEOUT
		else:
			self.renderBossNextRetryTime = now + self.BOSS_PREVIEW_RETRY_INTERVAL
		self.renderBossVnum = 0
		self.renderBossSelectionSucceeded = False
		self.renderTarget.Hide()
		self.bossFallback.Show()
		try:
			if self.renderTargetIndex < 0:
				self.renderTargetIndex = int(WikiRenderTarget.GetFreeIndex(86, 1000000))
				if self.renderTargetIndex < 1:
					raise RuntimeError("no free dungeon render target")
			else:
				WikiRenderTarget.SetVisibility(self.renderTargetIndex, False)
				WikiRenderTarget.ResetModel(self.renderTargetIndex)
			self.renderTarget.SetRenderTarget(self.renderTargetIndex)
			WikiRenderTarget.SetBackground(self.renderTargetIndex, "d:/ymir work/ui/render_target/render_target_bg.dds")
			selected = WikiRenderTarget.SelectModel(self.renderTargetIndex, self.renderRequestedBossVnum)
			if selected == 0:
				raise RuntimeError("dungeon boss model unavailable")
			WikiRenderTarget.SetEffectStatus(self.renderTargetIndex, False)
			WikiRenderTarget.SetRotation(self.renderTargetIndex, False)
			WikiRenderTarget.SetVisibility(self.renderTargetIndex, True)
			self.renderBossSelectionSucceeded = True
		except (AttributeError, RuntimeError, TypeError, ValueError):
			self.renderBossSelectionSucceeded = False

	def _RefreshBossPreview(self):
		if not self.renderRequestedBossVnum:
			return
		if self.renderBossVnum == self.renderRequestedBossVnum:
			return

		if self.renderBossSelectionSucceeded:
			isReady = False
			if self.renderTargetIndex >= 0:
				try:
					isReady = bool(WikiRenderTarget.IsModelReady(self.renderTargetIndex))
				except AttributeError:
					# Older clients do not expose native readiness. Keep their legacy
					# successful-selection behavior during a coordinated rollout.
					isReady = True
				except (RuntimeError, TypeError, ValueError):
					isReady = False

			if isReady or app.GetTime() >= self.renderBossNextRetryTime:
				self.renderBossVnum = self.renderRequestedBossVnum
				self.renderTarget.Show()
				self.bossFallback.Hide()
			return

		if app.GetTime() >= self.renderBossNextRetryTime:
			self._RequestBossModel()

	def _ResetRenderTarget(self):
		self.renderRequestedBossVnum = 0
		self.renderBossVnum = 0
		self.renderBossRequestTime = 0.0
		self.renderBossNextRetryTime = 0.0
		self.renderBossAttemptCount = 0
		self.renderBossSelectionSucceeded = False
		if self.renderTarget:
			self.renderTarget.Hide()
		if self.renderTargetIndex >= 0:
			try:
				WikiRenderTarget.SetVisibility(self.renderTargetIndex, False)
				WikiRenderTarget.ResetModel(self.renderTargetIndex)
			except (AttributeError, RuntimeError, TypeError, ValueError):
				pass
		if hasattr(self, "bossFallback"):
			self.bossFallback.Show()

	def _RemoveRenderTarget(self):
		if self.renderTargetIndex < 0:
			return
		try:
			WikiRenderTarget.Remove(self.renderTargetIndex)
		except (AttributeError, RuntimeError, TypeError, ValueError):
			return
		self.renderTargetIndex = -1

	def _SelectRank(self, rankIdx):
		if rankIdx not in (0, 1, 2):
			return
		if not featureavailability.IsAvailable(featureavailability.RANKINGS):
			featureavailability.NotifyRefused(featureavailability.RANKINGS)
			self._RefreshRank()
			return
		self.activeRank = rankIdx
		self._RefreshRank()

	def _RequestRank(self, mobIdx, rankIdx):
		cacheKey = (int(mobIdx), int(rankIdx))
		cached = self.rankCache.get(cacheKey)
		if cached and cached["leftTime"] > app.GetGlobalTimeStamp():
			return
		net.SendChatPacket("/dungeon_info rank {} {}".format(mobIdx, rankIdx))
		self.rankCache[cacheKey] = {
			"leftTime" : app.GetGlobalTimeStamp() + LOG_UPDATE_TIME,
			"data" : cached["data"] if cached else [],
		}

	def _RefreshRank(self):
		mobIdx = self.GetCurrentSelectedDungeon()
		self.rankValueHeader.SetText(self.rankValueTitles[self.activeRank])
		valueColor = (DUNGEON_COLOR_GREEN, DUNGEON_COLOR_BLUE, DUNGEON_COLOR_AMBER)[self.activeRank]
		self.rankValueHeader.SetPackedFontColor(_DungeonSignedColor(valueColor))
		for rankIdx, button in enumerate(self.rankButtons):
			_AtlasSetButtonVisuals(button, "button/rank_68x28", rankIdx == self.activeRank)
		for unusedPosition, name, value in self.rankLines:
			name.SetText("-")
			value.SetText("-")
			value.SetPackedFontColor(_DungeonSignedColor(valueColor))
		if not featureavailability.IsAvailable(featureavailability.RANKINGS):
			# Paused by the server: no request, the panel says it is coming.
			self.rankLines[0][1].SetText(getattr(localeInfo, "FEATURE_COMING_SOON_SHORT", "Coming soon"))
			return
		if mobIdx == -1:
			return
		cacheKey = (int(mobIdx), int(self.activeRank))
		if self.IsShow():
			self._RequestRank(mobIdx, self.activeRank)
		cached = self.rankCache.get(cacheKey)
		if not cached:
			return
		for lineIdx, rankInfo in enumerate(cached["data"][:len(self.rankLines)]):
			unusedPosition, name, value = self.rankLines[lineIdx]
			name.SetText("%s (Lv. %d)" % (rankInfo["name"], rankInfo["level"]))
			if self.activeRank == 1:
				value.SetText(FormatTimeEx(rankInfo["val"]))
			else:
				value.SetText(NumberToDecimalString(rankInfo["val"]))

	def Refresh(self):
		self._RefreshCatalogue()
		self._RefreshDetails()

	def OpenPage(self):
		net.SendChatPacket("/dungeon_info update")
		self.Show()
		self.Refresh()

	def ClosePage(self):
		if self.dropWindow:
			self.dropWindow.Close()
		self._ResetRenderTarget()
		self._RemoveRenderTarget()
		self.Hide()

	def LoadServerData(self, mobIdx, rankIdx, cmd):
		cacheKey = (int(mobIdx), int(rankIdx))
		rankList = []
		if cmd != "-":
			for rankEntry in cmd.split("#"):
				parts = rankEntry.split("|")
				if len(parts) != 3:
					continue
				try:
					rankList.append({"name" : parts[0], "val" : int(parts[1]), "level" : int(parts[2])})
				except ValueError:
					continue
		self.rankCache[cacheKey] = {
			"leftTime" : app.GetGlobalTimeStamp() + LOG_UPDATE_TIME,
			"data" : rankList,
		}
		if cacheKey == (self.GetCurrentSelectedDungeon(), self.activeRank):
			self._RefreshRank()

	def Destroy(self):
		self._ResetRenderTarget()
		self._RemoveRenderTarget()
		if self.dropWindow:
			self.dropWindow.Destroy()
			self.dropWindow = None
		self.renderTargetIndex = -1
		self.renderTarget = None
		self.rows = {}
		self.rankCache = {}
		self.staticWidgets = []
		self.elementIcons = []
		self.elementBossVnum = None

	def OnMouseWheel(self, length):
		if length > 0:
			self.scrollOffset -= 1
		elif length < 0:
			self.scrollOffset += 1
		self._RefreshCatalogue()
		# The catalogue owns the wheel even at its first/last row.
		return True

	def OnUpdate(self):
		self._RefreshBossPreview()
		if self.lastRefresh + 0.5 < app.GetTime():
			self.lastRefresh = app.GetTime()
			self._RefreshCatalogue()
			self._RefreshDetails()


class LogWindow(ui.BoardWithTitleBar):
	__children = {}
	class LogItem(ui.ExpandedImageBox):
		def Destroy(self):
			self.__children = {}
		def __init__(self, idx, name, val, level, rankIdx):
			ui.ExpandedImageBox.__init__(self)
			self.__LoadWindow(idx, name, val, level, rankIdx)

		def __LoadWindow(self, idx, name, val, level, rankIdx):
			self.Destroy()
			self.LoadImage(IMG_DIR+"log_item.tga")

			indexText = CreateWindow(ui.TextLine(), self, (20, 3), str(idx+1), "horizontal:center")
			self.__children["indexText"] = indexText

			nameText = CreateWindow(ui.TextLine(), self, (110, 3), name, "horizontal:center")
			self.__children["nameText"] = nameText

			levelText = CreateWindow(ui.TextLine(), self, (203, 3), str(level), "horizontal:center")
			self.__children["levelText"] =levelText

			valueComparedTest = FormatTimeEx(val) if rankIdx == 1 else NumberToDecimalString(val)
			valueText = CreateWindow(ui.TextLine(), self, (268, 3), valueComparedTest, "horizontal:center")
			self.__children["valueText"] = valueText

			if name == player.GetName():
				indexText.SetPackedFontColor(0xFFffcc00)
				nameText.SetPackedFontColor(0xFFffcc00)
				levelText.SetPackedFontColor(0xFFffcc00)
				valueText.SetPackedFontColor(0xFFffcc00)

	def Destroy(self):
		listBox = self.__children["listBox"] if "listBox" in self.__children else None
		if listBox:
			listBox.RemoveAllItems()
		self.__children = {}
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.Destroy()
		self.__LoadWindow()

	def __LoadWindow(self):
		self.SetSize(362,200)
		self.SetCenterPosition()
		self.AddFlag("float")
		self.AddFlag("movable")
		self.AddFlag("attach")
		self.AddFlag("animate")

		logTitle = CreateWindow(ui.ImageBox(), self, (19, 39), IMG_DIR+"log_title.tga")
		self.__children["logTitle"] = logTitle

		self.__children["rankText"] = CreateWindow(ui.TextLine(), logTitle, (20, 3), localeInfo.DUNGEON_TRACK_RANK_INDEX, "horizontal:center")
		self.__children["nameText"] = CreateWindow(ui.TextLine(), logTitle, (110, 3), localeInfo.DUNGEON_TRACK_RANK_NAME, "horizontal:center")
		self.__children["levelText"] = CreateWindow(ui.TextLine(), logTitle, (203, 3), localeInfo.DUNGEON_TRACK_RANK_LEVEL, "horizontal:center")
		self.__children["valueText"] = CreateWindow(ui.TextLine(), logTitle, (268, 3), "", "horizontal:center")

		listBox = CreateWindow(ui.ListBoxEx(), self, (19,39+logTitle.GetHeight()+5), "", "", (308, 23*5))
		listBox.AddFlag("attach")
		listBox.SetItemSize(308, 21)
		listBox.SetItemStep(23)
		listBox.SetViewItemCount(5)
		self.__children["listBox"] = listBox

		self.__children["loadingImage"] = CreateWindow(ui.ExpandedImageBox(), listBox, ((listBox.GetWidth()//2)-16, (listBox.GetHeight()//2)-16), IMG_DIR+"load_.tga")
		self.__children["loadingImage"].Hide()
		self.__children["loadingImageRotation"] = 0

		scrollBar = CreateWindow(ui.ScrollBar(), self, (19+logTitle.GetWidth()+5,39+logTitle.GetHeight()))
		scrollBar.SetScrollBarSize(21 * 5 + 15)
		listBox.SetScrollBar(scrollBar)
		self.__children["scrollBar"] = scrollBar
	
		self.__children["rankData"] = {}

	def LoadServerData(self, mobIdx, rankIdx, cmd):
		rankData = self.__children["rankData"][mobIdx] if mobIdx in self.__children["rankData"] else {}
		data = rankData[rankIdx] if rankIdx in rankData else {}
		rankList = []
		if cmd != "-":
			cmdSplit = cmd.split("#")
			for cmdInfo in cmdSplit:
				cmdInfoSplit = cmdInfo.split("|")
				if len(cmdInfoSplit) != 3:
					continue
				rankList.append({"name":cmdInfoSplit[0],"val":int(cmdInfoSplit[1]),"level":int(cmdInfoSplit[2])})

		data["leftTime"] = app.GetGlobalTimeStamp() + LOG_UPDATE_TIME
		data["data"] = rankList

		rankData[rankIdx] = data
		self.__children["rankData"][mobIdx] = rankData
		self.__LoadData(mobIdx, rankIdx)
		
	def __LoadData(self, mobIdx, rankIdx):
		self.__children["listBox"].RemoveAllItems()
		global dungeonData
		if mobIdx not in dungeonData:
			return
		__titleNames = [localeInfo.DUNGEON_TRACK_RANK_COMPLETED_TITLE, localeInfo.DUNGEON_TRACK_RANK_FASTEST_TITLE, localeInfo.DUNGEON_TRACK_RANK_DMG_TITLE]
		self.__children["valueText"].SetText(__titleNames[rankIdx])
		self.SetTitleName(dungeonData[mobIdx]["name"] + " - " + __titleNames[rankIdx])

		(self.__children["mobIdx"], self.__children["rankIdx"]) = (mobIdx, rankIdx)

		if self.__CheckRankNeedUpdate(mobIdx, rankIdx):
			self.__children["loadingImage"].Show()
			net.SendChatPacket("/dungeon_info rank {} {}".format(mobIdx, rankIdx))
		else:
			self.__children["loadingImage"].Hide()

			rankData = self.__GetData(mobIdx, rankIdx)
			if rankData != None:
				rankList = rankData["data"]
				for j in range(len(rankList)):
					self.__children["listBox"].AppendItem(self.LogItem(j, rankList[j]["name"], rankList[j]["val"], rankList[j]["level"], rankIdx))
		self.Show()
		self.SetTop()

	def __GetData(self, mobIdx, rankIdx):
		rankData = self.__children["rankData"]
		if mobIdx in rankData:
			if rankIdx in rankData[mobIdx]:
				return rankData[mobIdx][rankIdx]
		return None
	def __GetLeftTime(self, mobIdx, rankIdx):
		rankData = self.__children["rankData"]
		if mobIdx in rankData:
			if rankIdx in rankData[mobIdx]:
				return rankData[mobIdx][rankIdx]["leftTime"]
		return -1
	def __CheckRankNeedUpdate(self, mobIdx, rankIdx):
		return False if self.__GetLeftTime(mobIdx, rankIdx) > app.GetGlobalTimeStamp() else True
	def OnUpdate(self):
		loadingImage = self.__children["loadingImage"] if "loadingImage" in self.__children else None
		if loadingImage:
			if loadingImage.IsShow():
				newRotation = self.__children["loadingImageRotation"] = self.__children["loadingImageRotation"] + 10
				self.__children["loadingImage"].SetRotation(newRotation)
	def Open(self, mobIdx, rankIdx):
		self.__LoadData(mobIdx, rankIdx)
	def OnMouseWheel(self, nLen):
		if self.__children["scrollBar"]:
			self.__children["scrollBar"].OnMouseWheel2(nLen)
			return True
		return False
	def Close(self):
		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True
