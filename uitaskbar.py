import ui
import net
import item
import skill
import localeInfo
import wndMgr
import player
import constInfo
import osfInfo
import mouseModule
import uiScriptLocale
import app
import guild
import os
import quickslotpolicy
import slotwindowpolicy
import dbg

WindowDestroy = getattr(ui, "WindowDestroy", lambda method: method)

METIN_QUEUE_MOUSE_MODE_ENABLED = (
	getattr(app, "ENABLE_AUTO_FARM_METIN", 0)
	and hasattr(player, "MBF_METIN_QUEUE")
)

if app.ENABLE_POISON_GAUGE_EFFECT:
	import chr
	import chrmgr

if app.ENABLE_WINDOW_RESIZE:
	from resizeexpr import Expr

MOUSE_SETTINGS = [0, 0]

def _R1TextTipShow(owner):
	"""R1 look: the gauge / energy text as the one R1 hint above the mouse (uir1.TextTooltipShow); False = the
	original look draws the text line itself."""
	try:
		import uir1
		return uir1.TextTooltipShow(owner, owner.textLine.GetText())
	except Exception:
		return False


def _R1TextTipHide(owner):
	try:
		import uir1
		uir1.HideHint(owner)
	except Exception:
		pass


def InitMouseButtonSettings(left, right):
	global MOUSE_SETTINGS
	MOUSE_SETTINGS = [left, right]

def SetMouseButtonSetting(dir, event):
	global MOUSE_SETTINGS
	MOUSE_SETTINGS[dir] = event

def GetMouseButtonSettings():
	global MOUSE_SETTINGS
	return MOUSE_SETTINGS

def SaveMouseButtonSettings():
	global MOUSE_SETTINGS
	os.makedirs("UserData/mouse", exist_ok=True)
	with open("UserData/mouse/mouse.cfg", "w") as settingsFile:
		settingsFile.write("%s\t%s" % tuple(MOUSE_SETTINGS))

def LoadMouseButtonSettings():
	global MOUSE_SETTINGS
	with open("UserData/mouse/mouse.cfg", "r") as settingsFile:
		tokens = settingsFile.read().split()

	if len(tokens) != 2:
		raise RuntimeError("MOUSE_SETTINGS_FILE_ERROR")

	MOUSE_SETTINGS[0] = int(tokens[0])
	MOUSE_SETTINGS[1] = int(tokens[1])

def unsigned32(n):
	return n & 0xFFFFFFFF

#-------------------Giftbox Begin------------------------------

class GiftBox(ui.ScriptWindow):
	class TextToolTip(ui.Window):
		def __init__(self):
			ui.Window.__init__(self, "TOP_MOST")
			self.SetWindowName("GiftBox")
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetHorizontalAlignCenter()
			textLine.SetOutline()
			textLine.Show()
			self.textLine = textLine

		def __del__(self):
			ui.Window.__del__(self)

		def SetText(self, text):
			self.textLine.SetText(text)

		def OnRender(self):
			(mouseX, mouseY) = wndMgr.GetMousePosition()
			self.textLine.SetPosition(mouseX, mouseY - 15)

	def __init__(self):
		# print "NEW TASKBAR -----------------------------------------------------------------------------"
		ui.ScriptWindow.__init__(self)
		self.tooltipGift = self.TextToolTip()
		self.tooltipGift.Show()

	def __del__(self):
		# print "---------------------------------------------------------------------------- DELETE TASKBAR"
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "giftbox.py")
		except:
			import exception
			exception.Abort("GiftBox.LoadWindow.LoadObject")

		self.giftBoxIcon = self.GetChild("GiftBox_Icon")
		self.giftBoxIcon.SetEvent(ui.__mem_func__(self.OpenMall), "mouse_click")
		self.giftBoxToolTip = self.GetChild("GiftBox_ToolTip")

	def Destroy(self):
		self.giftBoxIcon = None
		self.giftBoxToolTip = None

	def OpenMall(self):
		#net.SendChatPacket("/click_mall")
		osfInfo.GetInterfaceInstance().OpenItemShopMallFromSpecInv()
		self.Hide()

#-------------------Giftbox End------------------------------

class EnergyBar(ui.ScriptWindow):
	class TextToolTip(ui.Window):
		def __init__(self):
			ui.Window.__init__(self, "TOP_MOST")
			self.SetWindowName("EnergyBar")
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetHorizontalAlignCenter()
			textLine.SetOutline()
			textLine.Show()
			self.textLine = textLine

		def __del__(self):
			ui.Window.__del__(self)

		def Show(self):
			if not _R1TextTipShow(self):
				ui.Window.Show(self)

		def Hide(self):
			_R1TextTipHide(self)
			ui.Window.Hide(self)

		def SetText(self, text):
			self.textLine.SetText(text)

		def OnRender(self):
			(mouseX, mouseY) = wndMgr.GetMousePosition()
			self.textLine.SetPosition(mouseX, mouseY - 15)

	def __init__(self):
		#print "NEW TASKBAR -----------------------------------------------------------------------------"
		ui.ScriptWindow.__init__(self)
		self.tooltipEnergy = self.TextToolTip()
		self.tooltipEnergy.Show()

	def __del__(self):
		#print "---------------------------------------------------------------------------- DELETE TASKBAR"
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "EnergyBar.py")
		except:
			import exception
			exception.Abort("EnergyBar.LoadWindow.LoadObject")

		self.energyEmpty = self.GetChild("EnergyGauge_Empty")
		self.energyHungry = self.GetChild("EnergyGauge_Hungry")
		self.energyFull = self.GetChild("EnergyGauge_Full")

		self.energyGaugeBoard = self.GetChild("EnergyGauge_Board")
		self.energyGaugeToolTip = self.GetChild("EnergyGauge_ToolTip")

	def Destroy(self):
		self.tooltipEnergy = None
		self.energyEmpty = None
		self.energyHungry = None
		self.energyFull = None

		self.energyGaugeBoard = None
		self.energyGaugeToolTip = None

	## Gauge
	def RefreshStatus(self):
		pointEnergy = player.GetStatus(player.ENERGY)
		if app.ENABLE_EXTENDED_BLEND_AFFECT:
			if pointEnergy != 0:
				leftTimeEnergy = 7200
			else:
				leftTimeEnergy = player.GetStatus(player.ENERGY_END_TIME) - app.GetGlobalTimeStamp()
		else:
			leftTimeEnergy = player.GetStatus(player.ENERGY_END_TIME) - app.GetGlobalTimeStamp()
		# 충기환 지속 시간 = 2시간.
		self.SetEnergy(pointEnergy, leftTimeEnergy, 7200)

	def SetEnergy(self, point, leftTime, maxTime):
		leftTime = max(leftTime, 0)
		maxTime = max(maxTime, 0)

		self.energyEmpty.Hide()
		self.energyHungry.Hide()
		self.energyFull.Hide()

		if leftTime == 0:
			self.energyEmpty.Show()
		elif ((leftTime * 100) // maxTime) < 15:
			self.energyHungry.Show()
		else:
			self.energyFull.Show()

		self.tooltipEnergy.SetText("%s" % (localeInfo.TOOLTIP_ENERGY(point)))

	def OnUpdate(self):
		if True == self.energyGaugeToolTip.IsIn():
			self.RefreshStatus()
			self.tooltipEnergy.Show()
		else:
			self.tooltipEnergy.Hide()

if app.ENABLE_GEM_SYSTEM:
	class ExpandedMoneyTaskBar(ui.ScriptWindow):
		def __init__(self):
			ui.Window.__init__(self)

			self.wndMoney = None
			self.wndMoneySlot = None
			self.wndMoneyIcon = None

			if app.ENABLE_GEM_SYSTEM:
				self.wndGem = None
				self.wndGemSlot = None
				self.wndGemIcon = None

		def __del__(self):
			ui.Window.__del__(self)

		def Destroy(self):
			self.wndMoney = None
			self.wndMoneySlot = None
			self.wndMoneyIcon = None
			if app.ENABLE_GEM_SYSTEM:
				self.wndGem = None
				self.wndGemSlot = None
				self.wndGemIcon = None

		def LoadWindow(self):
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "UIScript/ExpandedMoneyTaskbar.py")

				self.wndMoney = self.GetChild("Money")
				self.wndMoneyIcon = self.GetChild("Money_Icon")
				self.wndMoneySlot = self.GetChild("Money_Slot")

				if app.ENABLE_GEM_SYSTEM:
					self.wndGem = self.GetChild("Gem")
					self.wndGemIcon = self.GetChild("Gem_Icon")
					self.wndGemSlot = self.GetChild("Gem_Slot")

			except:
				import exception
				exception.Abort("ExpandedMoneyTaskBar.LoadWindow.LoadObject")

		def GetMoneySlot(self):
			if self.wndMoneySlot:
				return self.wndMoneySlot
			else:
				return None

		def GetMoney(self):
			if self.wndMoney:
				return self.wndMoney
			else:
				return None

		def GetMoneyIcon(self):
			if self.wndMoneyIcon:
				return self.wndMoneyIcon
			else:
				return None

		if app.ENABLE_GEM_SYSTEM:
			def GetGem(self):
				if self.wndGem:
					return self.wndGem
				else:
					return None

			def GetGemSlot(self):
				if self.wndGemSlot:
					return self.wndGemSlot
				else:
					return None

			def GetGemIcon(self):
				if self.wndGemIcon:
					return self.wndGemIcon
				else:
					return None

		def Show(self):
			self.SetTop()
			ui.ScriptWindow.Show(self)

		def Close(self):
			self.Hide()

		def OnPressEscapeKey(self):
			self.Close()
			return True

class ExpandedTaskBar(ui.ScriptWindow):
	"""Inventory shortcut rail (configurable, owner-approved 2026-10-04).

	The twelve buttons of locale/common/ui/expandedtaskbar.py keep their keys,
	callbacks, tooltips and approved icons; other catalogue functions get
	runtime buttons on the same 37x37 carrier. Which functions are shown, in
	one or two columns of at most 13, comes from root/inventoryrail.py
	(UserData/button-panels.json, "inventory" section). Without a stored
	section the rail is exactly today's twelve buttons. Right click or
	Shift+click opens Change… / Remove / Move to More; the small cogwheel
	above the rail opens Settings -> Panely tlačítek -> Inventář.
	"""
	BUTTON_SPECIAL_INVENTORY = 0
	BUTTON_DRAGON_SOUL = 1
	BUTTON_TELEPORT = 2
	BUTTON_WIKI = 3
	BUTTON_DUNGEON_INFO = 4
	BUTTON_SWITCHBOT = 5
	BUTTON_SHOP_SEARCH = 6
	BUTTON_BIOLOG = 7
	BUTTON_QUICK_BUFF_ACTIVATE = 8
	BUTTON_TALISMAN = 9
	BUTTON_DEW = 10
	BUTTON_MISSION_BOOKS = 11
	BUTTON_QUICK_EQUIP = 12
	BUTTON_PET = 13
	BUTTON_MOUNT = 14

	# Panel action ID of each named rail button (root/inventoryrail.py DEFAULT_IDS).
	ACTION_BY_KEY = {
		BUTTON_SPECIAL_INVENTORY: "inventory.special",
		BUTTON_QUICK_EQUIP: "system.quick_equip",
		BUTTON_DRAGON_SOUL: "inventory.dragon_soul",
		BUTTON_BIOLOG: "system.biolog",
		BUTTON_TELEPORT: "system.teleport",
		BUTTON_PET: "system.pet",
		BUTTON_SHOP_SEARCH: "system.shop_search",
		BUTTON_SWITCHBOT: "system.switchbot",
		BUTTON_TALISMAN: "system.talisman",
		BUTTON_MISSION_BOOKS: "system.mission_books",
		BUTTON_MOUNT: "system.mount",
		BUTTON_DEW: "system.dew_craft",
	}

	RAIL_PATH = "d:/ymir work/ui/game/crimson_ember/inventory/"
	RAIL_COLUMN_WIDTH = 42
	RAIL_STEP = 41
	RAIL_BACKGROUND_HEIGHT = 334.0
	SETTINGS_SIZE = 18
	SETTINGS_TOP = 9
	# "⋯" half bar below column 1 (opens More; takes no slot). 13 buttons + bar
	# end at 33 + 4 + 13 * 41 + 12 + 2 = 584, inside the 585 px inventory body.
	MORE_BAR_HEIGHT = 12
	# Expand/collapse "ear" of column 2 (owner 2026-10-04, variant A): the
	# belt-inventory arrow cut to one rail button (10x37), level with the first
	# row - next to the first button of column 2, or of column 1 when pushed in.
	TAB_PATH = "d:/ymir work/ui/game/crimson_ember/inventory/rail_tab_"
	TAB_WIDTH = 10
	TAB_HEIGHT = 37
	# Style "beside the cogwheel": a 22 px arrow head left of the cogwheel above the rail.
	HEAD_PATH = "d:/ymir work/ui/game/crimson_ember/inventory/rail_head_"
	HEAD_SIZE = 22
	HEAD_TOP = 6
	# Page switcher of the pages mode (owner 2026-10-04): a 13x37 plate (up 14, page
	# number 9, down 14) left of the rail, or the same three parts in the 37x12 "⋯" bar.
	PAGE_WIDTH = 13
	PAGE_ARROW_HEIGHT = 14
	PAGE_NUM_HEIGHT = 9
	PAGE_HEIGHT = 37
	PAGEBAR_PARTS = (0, 13, 24)

	def __init__(self):
		ui.Window.__init__(self)
		self.SetWindowName("ExpandedTaskBar")

		self.exclusion_list = []
		self.hiddenButtonKeys = set()
		self.wndInventory = None
		self.interface = None
		self.petAlbumCaptureBadge = None
		self.toggleButtonDict = {}
		self.keyEvents = {}
		self.actionButtons = {}
		self.extraButtons = {}
		self.railEntries = {}
		self.railColumns = ((),)
		self.secondBackground = None
		self.settingsButton = None
		self.moreBar = None
		self.columnTab = None
		self.headButton = None
		self.railCollapsed = False
		self.pageWidgets = None
		self.railPicker = None
		self.railContext = None
		self.railToolTip = None
		self.railTexts = {}
		self.railBadges = None

	def __del__(self):
		ui.Window.__del__(self)

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "ExpandedTaskBar.py")
		except:
			import exception
			exception.Abort("ExpandedTaskBar.LoadWindow.LoadObject")

		self.expandedTaskBarBoard = self.GetChild("ExpanedTaskBar_Board")

		# Column 2 (outside the inventory body) has its own stretched background;
		# created before the buttons are re-parented so it renders beneath them.
		background = ui.ExpandedImageBox()
		background.SetParent(self)
		background.AddFlag("not_pick")
		background.LoadImage(ExpandedTaskBar.RAIL_PATH + "rail_background.png")
		background.Hide()
		self.secondBackground = background

		moreBar = ui.Button()
		moreBar.SetParent(self)
		for method, state in (("SetUpVisual", "normal"), ("SetOverVisual", "hover"), ("SetDownVisual", "pressed")):
			getattr(moreBar, method)(ExpandedTaskBar.RAIL_PATH + "rail_more_bar_%s.png" % state)
		from settingslocale import Text
		self.railTexts["rail.more"] = Text("Další", "More")
		self.__UseRailToolTip(moreBar, "rail.more")
		moreBar.SetEvent(ui.__mem_func__(self.ToggleRailMenu))
		moreBar.Show()
		self.moreBar = moreBar

		columnTab = ui.Button()
		columnTab.SetParent(self)
		columnTab.SetEvent(ui.__mem_func__(self.ToggleSecondColumn))
		columnTab.Hide()
		self.columnTab = columnTab
		self.__UseRailToolTip(columnTab, "rail.tab")

		self.toggleButtonDict = {}
		button_bindings = (
			(app.ENABLE_SPECIAL_INVENTORY_SYSTEM, ExpandedTaskBar.BUTTON_SPECIAL_INVENTORY, "SpecialInventoryButton"),
			(True, ExpandedTaskBar.BUTTON_QUICK_EQUIP, "QuickEquipButton"),
			(app.ENABLE_DRAGON_SOUL_SYSTEM, ExpandedTaskBar.BUTTON_DRAGON_SOUL, "DragonSoulButton"),
			(app.ENABLE_BIOLOG_SYSTEM, ExpandedTaskBar.BUTTON_BIOLOG, "BiologButton"),
			(app.ENABLE_TELEPORT_WINDOW, ExpandedTaskBar.BUTTON_TELEPORT, "TeleportButton"),
			(app.ENABLE_GROWTH_PET_SYSTEM, ExpandedTaskBar.BUTTON_PET, "PetButton"),
			(getattr(app, "ENABLE_VIRTUAL_MARKET", 0), ExpandedTaskBar.BUTTON_SHOP_SEARCH, "ShopSearchButton"),
			(app.ENABLE_SWITCHBOT_SYSTEM, ExpandedTaskBar.BUTTON_SWITCHBOT, "SwitchbotButton"),
			(True, ExpandedTaskBar.BUTTON_TALISMAN, "TalismanButton"),
			(True, ExpandedTaskBar.BUTTON_MISSION_BOOKS, "MissionBooksButton"),
			(True, ExpandedTaskBar.BUTTON_MOUNT, "MountButton"),
			(app.ENABLE_CUBE_RENEWAL, ExpandedTaskBar.BUTTON_DEW, "DewButton"),
		)
		for enabled, key, child_name in button_bindings:
			if not enabled:
				continue
			button = self.GetChild(child_name)
			button.SetParent(self)
			self.toggleButtonDict[key] = button
			actionId = ExpandedTaskBar.ACTION_BY_KEY[key]
			self.actionButtons[actionId] = button
			self.__UseRailToolTip(button, actionId)
			# The chosen game icon set replaces the item-art when packed (owner 2026-10-04).
			if self.IsChild(child_name + "Icon"):
				import inventoryrailicons
				(image, position, unused) = inventoryrailicons.Icon(actionId)
				icon = self.GetChild(child_name + "Icon")
				icon.LoadImage(image)
				icon.SetPosition(*position)
			button.SAFE_SetStringEvent("MOUSE_RIGHT_BUTTON_UP", self.OpenRailContext, actionId)
			if key in self.hiddenButtonKeys:
				button.Hide()

		self.RePositionButton()
		if ExpandedTaskBar.BUTTON_PET in self.toggleButtonDict:
			import uipetalbumcapturebadge
			self.petAlbumCaptureBadge = uipetalbumcapturebadge.AlbumCaptureBadge(
				self.toggleButtonDict[ExpandedTaskBar.BUTTON_PET], 22, 2)
			# Same size and place as the rail number badges (root/uibuttonpaneldecor.py).
			import uibuttonpaneldecor
			uibuttonpaneldecor.MatchAlbumRailBadge(self.petAlbumCaptureBadge)

	def BindInventoryWindow(self, wndInventory):
		from _weakref import proxy
		self.wndInventory = proxy(wndInventory)
		self.SetParent(wndInventory)
		self.SetPosition(0, 33)
		self.__CreateSettingsButton(wndInventory)
		self.RePositionButton()
		self.Show()
		# The R1 look of the inventory (root/uiinventoryr1.py) recolours the rail frames too.
		if hasattr(wndInventory, "BindR1Rail"):
			wndInventory.BindR1Rail(self)

	def SetR1Look(self, on):
		"""Rail frames of the R1 look (recoloured copies, root/uiinventoryr1.RAIL_ART) or the original ones; the
		function icons stay. Every rail texture is chosen through RAIL_PATH / TAB_PATH / HEAD_PATH of this rail."""
		if on:
			import uiinventoryr1
			self.RAIL_PATH = uiinventoryr1.RAIL_ART
			self.TAB_PATH = uiinventoryr1.RAIL_ART + "rail_tab_"
			self.HEAD_PATH = uiinventoryr1.RAIL_ART + "rail_head_"
		else:
			for name in ("RAIL_PATH", "TAB_PATH", "HEAD_PATH"):
				self.__dict__.pop(name, None)
		path = self.RAIL_PATH
		for background in (self.expandedTaskBarBoard, self.secondBackground):
			if background:
				background.LoadImage(path + "rail_background.png")
		if self.moreBar:
			for method, state in (("SetUpVisual", "normal"), ("SetOverVisual", "hover"), ("SetDownVisual", "pressed")):
				getattr(self.moreBar, method)(path + "rail_more_bar_%s.png" % state)
		buttons = list(self.toggleButtonDict.values()) + list(self.extraButtons.values())
		for button in buttons:
			button.SetUpVisual(path + "rail_button_normal.png")
			button.SetOverVisual(path + "rail_button_hover.png")
			button.SetDownVisual(path + "rail_button_pressed.png")
			button.SetDisableVisual(path + "rail_button_disabled.png")
		if self.settingsButton:
			for method, state in (("SetUpVisual", "normal"), ("SetOverVisual", "hover"), ("SetDownVisual", "pressed")):
				getattr(self.settingsButton, method)(path + "rail_settings_%s.png" % state)
		self.RePositionButton()

	def BindInterface(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface) if interface is not None else None
		self.RefreshRail()

	@WindowDestroy
	def Destroy(self):
		self.Hide()
		if self.petAlbumCaptureBadge:
			self.petAlbumCaptureBadge.Destroy()
		self.petAlbumCaptureBadge = None
		if self.railBadges:
			self.railBadges.Destroy()
		self.railBadges = None
		if self.railPicker:
			self.railPicker.Destroy()
		self.railPicker = None
		if self.railContext:
			self.railContext.Destroy()
		self.railContext = None
		if self.railToolTip:
			self.railToolTip.Destroy()
		self.railToolTip = None
		if self.settingsButton:
			self.settingsButton.Hide()
		self.settingsButton = None
		self.moreBar = None
		self.columnTab = None
		self.pageWidgets = None
		if self.headButton:
			self.headButton.Hide()
		self.headButton = None
		self.ClearDictionary()
		self.toggleButtonDict = {}
		self.keyEvents = {}
		self.actionButtons = {}
		self.extraButtons = {}
		self.secondBackground = None
		self.expandedTaskBarBoard = None
		self.wndInventory = None
		self.interface = None
		self.exclusion_list = []
		self.hiddenButtonKeys = set()

	# Configurable layout ------------------------------------------------------
	def __KnownIds(self):
		import inventoryrail
		named = tuple(actionId for key, actionId in sorted(ExpandedTaskBar.ACTION_BY_KEY.items())
			if key in self.toggleButtonDict)
		return inventoryrail.KnownIds(tuple(self.railEntries), named)

	def RailKnownIds(self):
		return self.__KnownIds()

	def RefreshRail(self):
		"""Re-read the catalogue and the stored layout, then rebuild the rail."""
		import inventoryrail
		import minimappanel
		minimappanel.MarkVip(self)
		try:
			# No VIP channel without VIP in game (root/minimappanel.py ShownInGame).
			self.railEntries = dict((entry.action_id, entry)
				for entry in minimappanel.ShownInGame(inventoryrail.Catalog(self.interface)))
		except Exception:
			self.railEntries = {}
		self.RePositionButton()
		if self.railPicker and self.railPicker.IsShow():
			self.railPicker.Refresh()

	def __Shown(self, actionId):
		button = self.__ButtonFor(actionId)
		if not button:
			return False
		for key, keyAction in ExpandedTaskBar.ACTION_BY_KEY.items():
			if keyAction == actionId and (key in self.exclusion_list or key in self.hiddenButtonKeys):
				return False
		return True

	def __ButtonFor(self, actionId):
		if actionId in self.actionButtons:
			return self.actionButtons[actionId]
		if actionId in self.extraButtons:
			return self.extraButtons[actionId]
		if actionId not in self.railEntries:
			return None
		import inventoryrailicons
		import uiinventoryrailmenu
		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual(self.RAIL_PATH + "rail_button_normal.png")
		button.SetOverVisual(self.RAIL_PATH + "rail_button_hover.png")
		button.SetDownVisual(self.RAIL_PATH + "rail_button_pressed.png")
		button.SetDisableVisual(self.RAIL_PATH + "rail_button_disabled.png")
		(image, position, mark) = inventoryrailicons.Icon(actionId)
		icon = ui.ImageBox()
		icon.SetParent(button)
		icon.AddFlag("not_pick")
		icon.SetPosition(*position)
		icon.LoadImage(image)
		icon.Show()
		button.railIcon = icon
		if mark:
			button.SetText(mark)
		self.railTexts[actionId] = uiinventoryrailmenu.Tooltip(self.railEntries, actionId)
		self.__UseRailToolTip(button, actionId)
		button.SetEvent(ui.__mem_func__(self.__OnClickAction), actionId)
		button.SAFE_SetStringEvent("MOUSE_RIGHT_BUTTON_UP", self.OpenRailContext, actionId)
		self.extraButtons[actionId] = button
		return button

	def RePositionButton(self):
		import inventoryrail
		known = self.__KnownIds()
		state = inventoryrail.LoadState(known)
		self.railCollapsed = state.collapsed
		# Column 2 keeps its buttons while pushed in; only the visible columns are laid out.
		visible = state.VisibleColumns()
		columns = []
		for column in visible:
			columns.append(tuple(actionId for actionId in column if self.__Shown(actionId)))
		# A column 2 of which the game shows nothing (functions this client does not offer) takes
		# no room: it would be an empty 42 px column beside column 1.
		if len(columns) > 1 and not columns[1]:
			columns = columns[:1]
		columnCount = len(columns)
		self.railColumns = tuple(columns)
		shown = set(actionId for column in columns for actionId in column)

		# Columns mode: the column-2 control exists while column 2 has buttons. Styles
		# "top" and "bottom" are an ear left of the rail (the columns move right by its
		# width); style "cog" is an arrow head beside the cogwheel above the rail.
		# Pages mode: the page switcher exists while more than one page has buttons;
		# "top"/"side" take 13 px left of the rail, "bottom" replaces the "⋯" bar.
		pages = state.IsPages()
		# The column-2 control follows what the game SHOWS of column 2 (a column of functions this
		# client does not offer, e.g. VIP channels without VIP, has no ear and no gap).
		secondShown = [actionId for actionId in (state.columns[1] if len(state.columns) > 1 else ())
			if actionId != inventoryrail.EMPTY and self.__Shown(actionId)]
		firstShown = [actionId for actionId in state.columns[0]
			if actionId != inventoryrail.EMPTY and self.__Shown(actionId)]
		style = state.tab_style if secondShown and not pages else None
		switch = state.switch_style if state.ShowsSwitch() else None
		if pages:
			tab = ExpandedTaskBar.PAGE_WIDTH if switch in (inventoryrail.SWITCH_TOP, inventoryrail.SWITCH_SIDE) else 0
		else:
			tab = ExpandedTaskBar.TAB_WIDTH if style in (inventoryrail.TAB_TOP, inventoryrail.TAB_BOTTOM) else 0
		# "side"/"bottom": the rail is as tall as its longest page, so the switcher
		# below never moves when the page changes.
		fixedRows = None
		if switch in (inventoryrail.SWITCH_SIDE, inventoryrail.SWITCH_BOTTOM):
			fixedRows = max(len([a for a in state.PageIds(page) if a != inventoryrail.EMPTY and self.__Shown(a)])
				for page in state.ContentPages())
		for actionId, button in list(self.actionButtons.items()) + list(self.extraButtons.items()):
			if actionId not in shown:
				button.Hide()
		columnWidth = ExpandedTaskBar.RAIL_COLUMN_WIDTH
		step = ExpandedTaskBar.RAIL_STEP
		railHeight = 4
		barY = 4
		for columnIndex, column in enumerate(columns):
			# Column 1 and its controls keep their distance to the inventory body when
			# column 2 is pushed in/out (2026-10-04); column 2 touches column 1 and
			# the ear hangs on the outer edge of the rail (2026-10-05).
			columnX = self.__ColumnX(columnIndex, columnCount, tab)
			pos_x = columnX + 2
			pos_y = 4
			for actionId in column:
				button = self.__ButtonFor(actionId)
				button.SetPosition(pos_x, pos_y)
				button.Show()
				pos_y += step
			if columnIndex == 0 and fixedRows is not None:
				pos_y = 4 + max(fixedRows, len(column)) * step
			columnHeight = pos_y
			if columnIndex == 0 and self.moreBar:
				barY = pos_y
				if switch == inventoryrail.SWITCH_BOTTOM:
					self.moreBar.Hide()  # "⋯" moves beside the cogwheel
				else:
					self.moreBar.SetPosition(pos_x, pos_y)
					self.moreBar.Show()
				columnHeight += ExpandedTaskBar.MORE_BAR_HEIGHT + 2
			railHeight = max(railHeight, columnHeight)
			background = self.expandedTaskBarBoard if columnIndex == 0 else self.secondBackground
			if background:
				background.SetPosition(columnX, 0)
				background.SetSize(columnWidth, columnHeight)
				background.SetScale(1.0, float(columnHeight) / ExpandedTaskBar.RAIL_BACKGROUND_HEIGHT)
				if column or columnIndex == 0:
					background.Show()
				else:
					background.Hide()
		if columnCount < 2 and self.secondBackground:
			self.secondBackground.Hide()
		self.__PlaceColumnTab(tab if not pages else 0, state.collapsed,
			inventoryrail.TabRowOf(state.tab_style, len(firstShown), len(secondShown)), columnCount)
		self.__PlacePageSwitch(state, switch, tab, barY)
		self.SetSize(tab + columnWidth * columnCount, railHeight)
		if self.wndInventory and hasattr(self.wndInventory, "SetRailColumns"):
			self.wndInventory.SetRailColumns(columnCount, tab)
		if switch == inventoryrail.SWITCH_BOTTOM:
			self.__PlaceSettingsButton(columnCount, tab, None, True)
		else:
			self.__PlaceSettingsButton(columnCount, tab, state.collapsed if style == inventoryrail.TAB_COG else None)
		self.__UseRailWheel(state.ShowsSwitch() and state.wheel)
		self.__SyncRailBadges(state, known, columns, switch == inventoryrail.SWITCH_BOTTOM)

	# Badges and states (root/uibuttonpanelbadges.py) ----------------------------
	def __SuppressRailBadge(self, actionId, button):
		"""The pet button already shows the album capture count at the same corner."""
		badge = getattr(self, "petAlbumCaptureBadge", None)
		return bool(actionId == "system.pet" and badge is not None and getattr(badge, "count", 0))

	def __SyncRailBadges(self, state, known, columns, headMore):
		import inventoryrail
		import uibuttonpanelbadges
		if getattr(self, "railBadges", None) is None:
			self.railBadges = uibuttonpanelbadges.PanelBadges("rail", ui.__mem_func__(self.__SuppressRailBadge))
		pairs = []
		more = []
		for column in columns:
			for actionId in column:
				pairs.append((self.__ButtonFor(actionId), actionId))
		self.railBadges.Sync(pairs)
		if self.moreBar and self.moreBar.IsShow():
			more.append((self.moreBar, (27, -4)))
		if headMore and self.headButton:
			more.append((self.headButton, (13, -3)))
		try:
			menu = inventoryrail.MenuIds(state, known)
		except Exception:
			menu = ()
		self.railBadges.SetMore(more, menu)

	def OnUpdate(self):
		import minimappanel
		if minimappanel.VipChanged(self):
			self.RefreshRail()   # VIP channels appear / disappear
		if getattr(self, "railBadges", None):
			self.railBadges.Update(self.interface)

	# Pages mode: page switcher and mouse wheel ---------------------------------
	def __PageButton(self, key, event, *args):
		button = ui.Button()
		button.SetParent(self)
		button.SetEvent(ui.__mem_func__(event), *args)
		self.__UseRailToolTip(button, key)
		button.Hide()
		return button

	def __PageNumberButton(self):
		"""The page number plate: left click = next page, right click = previous
		(round the end, empty pages skipped - ``inventoryrail.FlipPage``)."""
		button = self.__PageButton("rail.page", self.FlipRailPage, 1)
		# ui.Button.OnMouseRightButtonUp only dispatches its string-event table.
		button.SAFE_SetStringEvent("MOUSE_RIGHT_BUTTON_UP", self.FlipRailPage, -1)
		return button

	def __PageWidgets(self):
		"""Lazily created: (up, number, down) of the plate and of the bar."""
		if self.pageWidgets is None:
			plate = (self.__PageButton("rail.page_up", self.FlipRailPage, -1),
				self.__PageNumberButton(),
				self.__PageButton("rail.page_down", self.FlipRailPage, 1))
			bar = (self.__PageButton("rail.page_up", self.FlipRailPage, -1),
				self.__PageNumberButton(),
				self.__PageButton("rail.page_down", self.FlipRailPage, 1))
			self.pageWidgets = (plate, bar)
		return self.pageWidgets

	def __PlacePageSwitch(self, state, switch, tab, barY):
		import inventoryrail
		if switch is None:
			if self.pageWidgets is not None:
				for button in self.pageWidgets[0] + self.pageWidgets[1]:
					button.Hide()
			return
		plate, bar = self.__PageWidgets()
		pages = state.ContentPages()
		number = state.ActivePage() + 1
		from settingslocale import Text
		where = "%d/%d" % (pages.index(state.ActivePage()) + 1, len(pages))
		wheel = Text("  |  kolečko myši", "  ·  mouse wheel") if state.wheel else ""
		self.railTexts["rail.page_up"] = Text("Předchozí strana", "Previous page") + " (" + where + ")" + wheel
		# Number plate: "Strana 2/3 · levý/pravý klik nebo kolečko" (owner 2026-10-04).
		hint = (Text("levý/pravý klik nebo kolečko", "left/right click or wheel") if state.wheel
			else Text("levý/pravý klik", "left/right click"))
		self.railTexts["rail.page"] = Text("Strana %s", "Page %s") % where + " | " + hint
		self.railTexts["rail.page_down"] = Text("Další strana", "Next page") + " (" + where + ")" + wheel
		path = self.RAIL_PATH
		if switch == inventoryrail.SWITCH_BOTTOM:
			for button in plate:
				button.Hide()
			parts = (("rail_pagebar_up_%s.png", None), ("rail_pagebar_num_%d.png" % number, True),
				("rail_pagebar_down_%s.png", None))
			x0 = tab + 2
			for index, (button, (stem, fixed)) in enumerate(zip(bar, parts)):
				self.__PageVisuals(button, path + stem, fixed)
				button.SetPosition(x0 + ExpandedTaskBar.PAGEBAR_PARTS[index], barY)
				button.Show()
				button.SetTop()
			return
		for button in bar:
			button.Hide()
		if switch == inventoryrail.SWITCH_SIDE:
			# Bottom-aligned with the "⋯" bar: beside the last row and the bar.
			y = barY + ExpandedTaskBar.MORE_BAR_HEIGHT - ExpandedTaskBar.PAGE_HEIGHT
		else:
			y = 4  # level with the first row, where the column-2 ear sits
		parts = (("rail_page_up_%s.png", None, 0), ("rail_page_num_%d.png" % number, True,
			ExpandedTaskBar.PAGE_ARROW_HEIGHT), ("rail_page_down_%s.png", None,
			ExpandedTaskBar.PAGE_ARROW_HEIGHT + ExpandedTaskBar.PAGE_NUM_HEIGHT))
		for button, (stem, fixed, dy) in zip(plate, parts):
			self.__PageVisuals(button, path + stem, fixed)
			button.SetPosition(0, y + dy)
			button.Show()
			button.SetTop()

	def __PageVisuals(self, button, pattern, fixed):
		if fixed:
			for method in ("SetUpVisual", "SetOverVisual", "SetDownVisual"):
				getattr(button, method)(pattern)
			return
		for method, state in (("SetUpVisual", "normal"), ("SetOverVisual", "hover"), ("SetDownVisual", "pressed")):
			getattr(button, method)(pattern % state)

	def FlipRailPage(self, step):
		"""Previous/next page with buttons (empty pages are skipped), round the end."""
		import inventoryrail
		known = self.__KnownIds()
		state = inventoryrail.LoadState(known)
		if not state.ShowsSwitch():
			return False
		import uiinventoryrailmenu
		uiinventoryrailmenu.Commit(inventoryrail.FlipPage(state, step), known)
		self.RePositionButton()
		if self.railPicker and self.railPicker.IsShow():
			self.railPicker.Refresh()
		return True

	def __OnRailWheel(self, down):
		self.FlipRailPage(1 if down else -1)

	def __UseRailWheel(self, enabled):
		"""The mouse wheel over the rail flips pages (pages mode, option "Kolečko")."""
		handler = ui.__mem_func__(self.__OnRailWheel) if enabled else None
		# Anywhere over the rail (owner 2026-10-04): the rail window itself (its gaps and
		# background), every button, "⋯", the ear, the cogwheel and the switcher -
		# a pickable child would otherwise take the wheel event first.
		widgets = [self, self.moreBar, self.headButton, self.columnTab, self.settingsButton,
			self.expandedTaskBarBoard, self.secondBackground] + list(self.actionButtons.values()) + \
			list(self.extraButtons.values())
		if self.pageWidgets is not None:
			widgets += list(self.pageWidgets[0] + self.pageWidgets[1])
		for widget in widgets:
			setter = getattr(widget, "SetOnRunMouseWheelEvent", None) if widget is not None else None
			if setter:
				setter(handler)

	def __ColumnX(self, columnIndex, columnCount, tab):
		"""Local x of a rail column: column 1 is always the last ``RAIL_COLUMN_WIDTH`` px
		of the rail (next to the body), column 2 right left of it (the columns touch),
		the ear (``tab`` px) leftmost - on the outer edge of column 2, or of column 1
		while column 2 is pushed in."""
		columnWidth = ExpandedTaskBar.RAIL_COLUMN_WIDTH
		if columnIndex == 0:
			return tab + columnWidth * (columnCount - 1)
		return tab

	def __PlaceColumnTab(self, tab, collapsed, row=0, columnCount=1):
		button = self.columnTab
		if not button:
			return
		if not tab:
			button.Hide()
			return
		stem = "expand" if collapsed else "minimize"
		button.SetUpVisual(self.TAB_PATH + stem + "_normal.png")
		button.SetOverVisual(self.TAB_PATH + stem + "_over.png")
		button.SetDownVisual(self.TAB_PATH + stem + "_down.png")
		from settingslocale import Text
		self.railTexts["rail.tab"] = (Text("Vysunout 2. sloupec", "Show column 2") if collapsed
			else Text("Zasunout 2. sloupec", "Hide column 2"))
		# On the outer edge of the rail: attached to column 2 while it is out, to column 1
		# while it is pushed in (owner play test 2026-10-05: between the columns it stuck to
		# column 1 and left a 10 px gap). "top": level with the first row; "bottom": with the
		# last row of the shorter column, the same in both states.
		button.SetPosition(0, 4 + row * ExpandedTaskBar.RAIL_STEP)
		button.Show()

	def ToggleSecondColumn(self):
		"""The arrow tab: push column 2 out or in; nothing is deleted (owner 2026-10-04)."""
		import inventoryrail
		known = self.__KnownIds()
		state = inventoryrail.LoadState(known)
		if not state.HasSecond():
			return
		import uiinventoryrailmenu
		uiinventoryrailmenu.Commit(inventoryrail.SetCollapsed(state, not state.collapsed), known)
		self.RePositionButton()
		if self.railPicker and self.railPicker.IsShow():
			self.railPicker.Refresh()

	if app.ENABLE_WINDOW_RESIZE:
		def OnResize(self):
			try:
				self.RePositionButton()
			except:
				pass

	# Clicks, context menu and "More" -----------------------------------------
	def __ShiftPressed(self):
		keys = [getattr(app, name, None) for name in ("DIK_LSHIFT", "DIK_RSHIFT")]
		return any(key is not None and app.IsPressed(key) for key in keys)

	def __OnClickKey(self, key):
		actionId = ExpandedTaskBar.ACTION_BY_KEY.get(key)
		if actionId and self.__ShiftPressed():
			self.OpenRailContext(actionId)
			return
		event = self.keyEvents.get(key)
		if event:
			event()

	def __OnClickAction(self, actionId):
		if self.__ShiftPressed():
			self.OpenRailContext(actionId)
			return
		self.RunRailAction(actionId)

	def RunRailAction(self, actionId):
		for key, keyAction in ExpandedTaskBar.ACTION_BY_KEY.items():
			if keyAction == actionId and key in self.keyEvents:
				self.keyEvents[key]()
				return True
		import minimappanel
		return minimappanel.Invoke(actionId, self.interface)

	def __RailPicker(self):
		if self.railPicker is None:
			import uibuttonpanelpicker
			self.railPicker = uibuttonpanelpicker.FunctionPicker()
		return self.railPicker

	def __PickerPosition(self, anchor=None):
		"""Left of the rail, top-aligned with the anchor button. The picker itself clamps
		to the screen above the taskbar once its size is known and opens upwards from
		the anchor when it does not fit below."""
		import uibuttonpanelpicker
		(x, y) = self.GetGlobalPosition()
		if anchor is not None:
			y = anchor.GetGlobalPosition()[1]
		return (x - uibuttonpanelpicker.WIDTH - 4, y)

	def __AnchorHeight(self, anchor):
		return anchor.GetHeight() if anchor is not None else 0

	def ToggleRailMenu(self):
		"""The rail's "More" button: every function in the "More" state."""
		import inventoryrail
		import uiinventoryrailmenu
		picker = self.__RailPicker()
		if picker.IsShow():
			picker.Close()
			return
		anchor = self.moreBar
		if anchor is not None and not anchor.IsShow() and self.headButton is not None:
			anchor = self.headButton  # page switcher below the rail: "⋯" is above it
		picker.EnableBadges(self.interface)
		uiinventoryrailmenu.OpenMore(picker, self.railEntries, self.__KnownIds(),
			ui.__mem_func__(self.RunRailAction), self.__PickerPosition(anchor), self.__AnchorHeight(anchor))

	def OpenRailPicker(self, actionId):
		"""Choose the function of the slot that shows ``actionId`` (assign, swap or empty)."""
		import uiinventoryrailmenu
		where = self.__Where(actionId)
		if where is None:
			return
		button = self.__ButtonFor(actionId)
		uiinventoryrailmenu.OpenSlotPicker(self.__RailPicker(), self.railEntries, self.__KnownIds(),
			where[0], where[1], ui.__mem_func__(self.RefreshRail),
			self.__PickerPosition(button), anchor_height=self.__AnchorHeight(button))

	def __Where(self, actionId):
		import inventoryrail
		state = inventoryrail.LoadState(self.__KnownIds())
		return state.Where(actionId)

	def OpenRailContext(self, actionId):
		"""Right click (or Shift+click) on a rail button: Change… / Remove / Move to More."""
		if mouseModule.mouseController.isAttached():
			return
		if self.__Where(actionId) is None:
			return
		import uibuttonpanelcontext
		import uiinventoryrailmenu
		if self.railContext is None:
			self.railContext = uibuttonpanelcontext.ContextMenu()
		entries = uiinventoryrailmenu.SlotMenuEntries(
			lambda selected=actionId: self.OpenRailPicker(selected), self.__KnownIds(), actionId,
			ui.__mem_func__(self.RefreshRail), ui.__mem_func__(self.OpenRailSettings))
		import uibuttonpanelbadges
		entries = tuple(entries) + uibuttonpanelbadges.ContextEntries(actionId)
		button = self.__ButtonFor(actionId)
		(x, y) = button.GetGlobalPosition() if button else self.GetGlobalPosition()
		self.railContext.Open(entries, (self.GetGlobalPosition()[0] - uibuttonpanelcontext.WIDTH - 4, y))

	def OpenRailSettings(self):
		import uiinventoryrailmenu
		return uiinventoryrailmenu.OpenSettings(self.interface, "inventory")

	def ToggleRailSettings(self):
		"""The cogwheel above the rail: a second click closes Settings (the context menu only opens)."""
		import uiinventoryrailmenu
		return uiinventoryrailmenu.ToggleSettings(self.interface, "inventory")

	# Settings cogwheel above the rail ------------------------------------------
	def __CreateSettingsButton(self, wndInventory):
		if self.settingsButton is not None:
			return
		head = ui.Button()
		head.SetParent(wndInventory)
		head.SetEvent(ui.__mem_func__(self.ToggleSecondColumn))
		head.Hide()
		self.headButton = head
		self.__UseRailToolTip(head, "rail.head")
		import inventoryrailicons
		button = ui.Button()
		button.SetParent(wndInventory)
		button.SetUpVisual(inventoryrailicons.SettingsVisual("normal"))
		button.SetOverVisual(inventoryrailicons.SettingsVisual("hover"))
		button.SetDownVisual(inventoryrailicons.SettingsVisual("pressed"))
		from settingslocale import Text
		self.railTexts["rail.settings"] = Text("Nastavení lišty", "Rail settings")
		self.__UseRailToolTip(button, "rail.settings")
		button.SetEvent(ui.__mem_func__(self.ToggleRailSettings))
		button.Show()
		self.settingsButton = button

	def __PlaceSettingsButton(self, columnCount, tab=0, headCollapsed=None, headMore=False):
		"""Centered above the first button of column 1, clear of the titlebar search.

		With the "cog" style (``headCollapsed`` is not None) the arrow head and the
		cogwheel form one pair above column 1, fixed relative to the inventory body.
		With the page switcher below the rail (``headMore``) the same place holds "⋯".
		"""
		if not self.settingsButton:
			return
		columnWidth = ExpandedTaskBar.RAIL_COLUMN_WIDTH
		column1 = tab + columnWidth * (columnCount - 1)
		x = column1 + (columnWidth - ExpandedTaskBar.SETTINGS_SIZE) // 2
		head = self.headButton
		if head:
			if headMore:
				for method, state in (("SetUpVisual", "normal"), ("SetOverVisual", "hover"), ("SetDownVisual", "pressed")):
					getattr(head, method)(self.HEAD_PATH + "more_" + state + ".png")
				head.SetEvent(ui.__mem_func__(self.ToggleRailMenu))
				self.railTexts["rail.head"] = self.railTexts.get("rail.more", "")
				head.SetPosition(column1, ExpandedTaskBar.HEAD_TOP)
				head.Show()
				head.SetTop()
				x = column1 + ExpandedTaskBar.HEAD_SIZE + 2
			elif headCollapsed is None:
				head.Hide()
			else:
				head.SetEvent(ui.__mem_func__(self.ToggleSecondColumn))
				# Both sit above column 1 (head 22 + 2 + cogwheel 18 = 42 px), so neither
				# moves when column 2 is pushed in or out; the arrow only flips.
				x0 = column1
				stem = "expand" if headCollapsed else "minimize"
				head.SetUpVisual(self.HEAD_PATH + stem + "_normal.png")
				head.SetOverVisual(self.HEAD_PATH + stem + "_hover.png")
				head.SetDownVisual(self.HEAD_PATH + stem + "_pressed.png")
				from settingslocale import Text
				self.railTexts["rail.head"] = (Text("Vysunout 2. sloupec", "Show column 2") if headCollapsed
					else Text("Zasunout 2. sloupec", "Hide column 2"))
				head.SetPosition(x0, ExpandedTaskBar.HEAD_TOP)
				head.Show()
				head.SetTop()
				x = x0 + ExpandedTaskBar.HEAD_SIZE + 2
		self.settingsButton.SetPosition(x, ExpandedTaskBar.SETTINGS_TOP)
		self.settingsButton.SetTop()

	def SetTop(self):
		super(ExpandedTaskBar, self).SetTop()
		for button in self.toggleButtonDict.values():
			button.SetTop()

	def Show(self):
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()

	def SetToolTipText(self, eButton, text):
		actionId = ExpandedTaskBar.ACTION_BY_KEY.get(eButton)
		if actionId:
			self.railTexts[actionId] = text

	def __RailToolTip(self):
		if self.railToolTip is None:
			import uibuttonpaneltooltip
			self.railToolTip = uibuttonpaneltooltip.PanelToolTip()
		return self.railToolTip

	def __UseRailToolTip(self, button, textKey):
		"""Name tooltip left of the rail on the TOP_MOST tooltip board (owner bug
		2026-10-04: the per-button tooltip child was drawn under the next button)."""
		child = getattr(button, "ToolTipText", None)
		if child:
			if textKey not in self.railTexts:
				self.railTexts[textKey] = child.GetText()
			child.Hide()
			button.ToolTipText = None
		import uibuttonpaneltooltip
		from _weakref import proxy
		owner = proxy(self)
		uibuttonpaneltooltip.Attach(button, self.__RailToolTip(),
			lambda key=textKey: owner.railTexts.get(key, ""), "left",
			lambda: owner.GetGlobalPosition()[0])  # left of the whole rail, both columns

	def SetToggleButtonEvent(self, eButton, kEventFunc):
		self.keyEvents[eButton] = kEventFunc
		self.toggleButtonDict[eButton].SetEvent(ui.__mem_func__(self.__OnClickKey), eButton)

	def SetButtonVisible(self, eButton, visible):
		button = self.toggleButtonDict.get(eButton)
		if not button:
			return
		if visible:
			self.hiddenButtonKeys.discard(eButton)
		else:
			self.hiddenButtonKeys.add(eButton)
			button.Hide()
		self.RePositionButton()

	def SetButtonEnabled(self, eButton, enabled):
		button = self.toggleButtonDict.get(eButton)
		if not button:
			return
		if enabled:
			button.Enable()
		else:
			button.Disable()

	def SetButtonSelected(self, eButton, selected):
		button = self.toggleButtonDict.get(eButton)
		if not button:
			return
		if selected:
			button.Down()
		else:
			button.SetUp()

	def OnPressEscapeKey(self):
		if self.wndInventory:
			self.wndInventory.Close()
		else:
			self.Close()
		return True

class TaskBar(ui.ScriptWindow):
	BUTTON_CHARACTER = 0
	BUTTON_INVENTORY = 1
	BUTTON_MESSENGER = 2
	BUTTON_SYSTEM = 3
	BUTTON_CHAT = 4
	BUTTON_EXPAND = 4
	if app.ENABLE_GEM_SYSTEM:
		BUTTON_EXPAND_MONEY = 5

	IS_EXPANDED = False

	MOUSE_BUTTON_LEFT = 0
	MOUSE_BUTTON_RIGHT = 1
	NONE = 255

	EVENT_MOVE = 0
	EVENT_ATTACK = 1
	EVENT_MOVE_AND_ATTACK = 2
	EVENT_CAMERA = 3
	EVENT_SKILL = 4
	EVENT_AUTO = 5
	EVENT_METIN_QUEUE = 6

	GAUGE_WIDTH = 95
	GAUGE_HEIGHT = 13

	QUICKPAGE_NUMBER_FILENAME = [
		"d:/ymir work/ui/game/taskbar/crimson/taskbar_page_1.tga",
		"d:/ymir work/ui/game/taskbar/crimson/taskbar_page_2.tga",
		"d:/ymir work/ui/game/taskbar/crimson/taskbar_page_3.tga",
		"d:/ymir work/ui/game/taskbar/crimson/taskbar_page_4.tga",
	]

	# Gift icon show and hide
	def ShowGift(self):
		if not localeInfo.IsBRAZIL():
			self.wndGiftBox.Show()

	def HideGift(self):
		self.wndGiftBox.Hide()

	class TextToolTip(ui.Window):
		def __init__(self):
			ui.Window.__init__(self, "TOP_MOST")

			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetHorizontalAlignCenter()
			textLine.SetOutline()
			textLine.Show()
			self.textLine = textLine

		def __del__(self):
			ui.Window.__del__(self)
			self.textLine = None

		def Show(self):
			if not _R1TextTipShow(self):
				ui.Window.Show(self)

		def Hide(self):
			_R1TextTipHide(self)
			ui.Window.Hide(self)

		def SetText(self, text):
			self.textLine.SetText(text)

		def OnRender(self):
			(mouseX, mouseY) = wndMgr.GetMousePosition()
			self.textLine.SetPosition(mouseX, mouseY - 15)

	class SkillButton(ui.SlotWindow):
		def __init__(self):
			ui.SlotWindow.__init__(self)

			self.event = None
			self.arg = None

			self.slotIndex = 0
			self.skillIndex = 0

			slotIndex = 0
			wndMgr.SetSlotBaseImage(self.hWnd, "d:/ymir work/ui/public/slot_base.sub", 1.0, 1.0, 1.0, 1.0)
			wndMgr.AppendSlot(self.hWnd, slotIndex, 0, 0, 32, 32)
			self.SetCoverButton(slotIndex, "d:/ymir work/ui/public/slot_cover_button_01.sub",\
				"d:/ymir work/ui/public/slot_cover_button_02.sub",\
				"d:/ymir work/ui/public/slot_cover_button_03.sub",\
				"d:/ymir work/ui/public/slot_cover_button_04.sub", True, False)
			self.SetSize(32, 32)

		def __del__(self):
			ui.SlotWindow.__del__(self)

		def Destroy(self):
			if 0 != self.tooltipSkill:
				self.tooltipSkill.HideToolTip()

		def RefreshSkill(self):
			if 0 != self.slotIndex:
				self.SetSkill(self.slotIndex)

		def SetSkillToolTip(self, tooltip):
			self.tooltipSkill = tooltip

		def SetSkill(self, skillSlotNumber):
			slotNumber = 0
			skillIndex = player.GetSkillIndex(skillSlotNumber)
			skillGrade = player.GetSkillGrade(skillSlotNumber)
			skillLevel = player.GetSkillLevel(skillSlotNumber)
			skillType = skill.GetSkillType(skillIndex)

			self.skillIndex = skillIndex
			if 0 == self.skillIndex:
				self.ClearSlot(slotNumber)
				return

			self.slotIndex = skillSlotNumber

			self.SetSkillSlotNew(slotNumber, skillIndex, skillGrade, skillLevel)
			self.SetSlotCountNew(slotNumber, skillGrade, skillLevel)

			## NOTE : CoolTime 체크
			if player.IsSkillCoolTime(skillSlotNumber):
				(coolTime, elapsedTime) = player.GetSkillCoolTime(skillSlotNumber)
				self.SetSlotCoolTime(slotNumber, coolTime, elapsedTime)

			## NOTE : Activate 되어 있다면 아이콘도 업데이트
			if player.IsSkillActive(skillSlotNumber):
				self.ActivateSlotOld(slotNumber)
			else:
				self.DeactivateSlot(slotNumber)

		def SetSkillEvent(self, event, arg=0):
			self.event = event
			self.arg = arg

		def GetSkillIndex(self):
			return self.skillIndex

		def GetSlotIndex(self):
			return self.slotIndex

		def Activate(self, coolTime):
			self.SetSlotCoolTime(0, coolTime)

			if skill.IsToggleSkill(self.skillIndex):
				self.ActivateSlotOld(0)

		def Deactivate(self):
			if skill.IsToggleSkill(self.skillIndex):
				self.DeactivateSlot(0)

		def OnOverInItem(self, dummy):
			self.tooltipSkill.SetSkill(self.skillIndex)

		def OnOverOutItem(self):
			self.tooltipSkill.HideToolTip()

		def OnSelectItemSlot(self, dummy):
			if 0 != self.event:
				if 0 != self.arg:
					self.event(self.arg)
				else:
					self.event()

	def __init__(self):
		#print "NEW TASKBAR -----------------------------------------------------------------------------"

		ui.ScriptWindow.__init__(self, "TOP_MOST")

		self.quickPageNumImageBox = None
		self.tooltipItem = None
		self.tooltipSkill = None
		self.mouseModeButtonList = [ ui.ScriptWindow("TOP_MOST"), ui.ScriptWindow("TOP_MOST") ]

		if app.ENABLE_HEART_BEAT_MALL:
			self.heartBeat = False

		self.tooltipHP = self.TextToolTip()
		self.tooltipHP.Show()
		self.tooltipSP = self.TextToolTip()
		self.tooltipSP.Show()
		self.tooltipST = self.TextToolTip()
		self.tooltipST.Show()
		self.tooltipEXP = self.TextToolTip()
		self.tooltipEXP.Show()

		self.skillCategoryNameList = [ "ACTIVE_1", "ACTIVE_2", "ACTIVE_3" ]
		self.skillPageStartSlotIndexDict = {
			"ACTIVE_1" : 1,
			"ACTIVE_2" : 21,
			"ACTIVE_3" : 41,
		}

		self.selectSkillButtonList = []

		self.lastUpdateQuickSlot = 0
		self.pendingQuickSlotDeletes = set()
		self.primaryAuxButton = None
		self.brandFlourishActive = False
		self.brandFlourishNextAt = 0.0
		self.brandFlourishLogo = None
		self.orbHitArea = None
		self.orbLogoHovered = False
		self.r1Dress = None
		self.SetWindowName("TaskBar")

	def __del__(self):
		#print "---------------------------------------------------------------------------- DELETE TASKBAR"
		ui.ScriptWindow.__del__(self)

	def __LoadNewExperienceGauges(self):
		gauges = []
		for index in range(1, 5):
			try:
				gauge = self.GetChild("NewExpGauge_%02d" % index)
			except:
				if app.ENABLE_CONQUEROR_LEVEL:
					raise
				continue

			gauge.SetSize(0, 0)
			gauge.Hide()
			gauges.append(gauge)

		return gauges

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()

			pyScrLoader.LoadScriptFile(self, "UIScript/TaskBar_Dominant_Orb.py")

			pyScrLoader.LoadScriptFile(self.mouseModeButtonList[self.MOUSE_BUTTON_LEFT], "UIScript/MouseButtonWindow.py")
			pyScrLoader.LoadScriptFile(self.mouseModeButtonList[self.MOUSE_BUTTON_RIGHT], "UIScript/RightMouseButtonWindow.py")
		except:
			import exception
			exception.Abort("TaskBar.LoadWindow.LoadObject")

		self.quickslot = []
		self.quickslot.append(self.GetChild("quick_slot_1"))
		self.quickslot.append(self.GetChild("quick_slot_2"))
		for slot in self.quickslot:
			slot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			slot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptyQuickSlot))
			slot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemQuickSlot))
			slot.SetUnselectItemSlotEvent(ui.__mem_func__(self.UnselectItemQuickSlot))
			slot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		toggleButtonDict = {}
		toggleButtonDict[TaskBar.BUTTON_CHARACTER] = self.GetChild("CharacterButton")
		toggleButtonDict[TaskBar.BUTTON_INVENTORY] = self.GetChild("InventoryButton")
		toggleButtonDict[TaskBar.BUTTON_MESSENGER] = self.GetChild("MessengerButton")
		toggleButtonDict[TaskBar.BUTTON_SYSTEM] = self.GetChild("SystemButton")

		self.__RegisterPrimaryAuxButton(toggleButtonDict)

		if app.ENABLE_GEM_SYSTEM:
			toggleButtonDict[TaskBar.BUTTON_EXPAND_MONEY]=self.GetChild("ExpandMoneyButton")

		if localeInfo.IsARABIC():
			systemButton = toggleButtonDict[TaskBar.BUTTON_SYSTEM]
			if systemButton.ToolTipText:
				tx, ty = systemButton.ToolTipText.GetLocalPosition()
				tw = systemButton.ToolTipText.GetWidth() 
				systemButton.ToolTipText.SetPosition(-tw//2, ty)

		expGauge = []
		expGauge.append(self.GetChild("EXPGauge_01"))
		expGauge.append(self.GetChild("EXPGauge_02"))
		expGauge.append(self.GetChild("EXPGauge_03"))
		expGauge.append(self.GetChild("EXPGauge_04"))

		for exp in expGauge:
			exp.SetSize(0, 0)

		newExpGauge = self.__LoadNewExperienceGauges()

		self.quickPageNumImageBox=self.GetChild("QuickPageNumber")

		self.GetChild("QuickPageUpButton").SetEvent(ui.__mem_func__(self.__OnClickQuickPageUpButton))
		self.GetChild("QuickPageDownButton").SetEvent(ui.__mem_func__(self.__OnClickQuickPageDownButton))

		mouseLeftButtonModeButton = self.GetChild("LeftMouseButton")
		mouseRightButtonModeButton = self.GetChild("RightMouseButton")
		mouseLeftButtonModeButton.SetEvent(ui.__mem_func__(self.ToggleLeftMouseButtonModeWindow))
		mouseRightButtonModeButton.SetEvent(ui.__mem_func__(self.ToggleRightMouseButtonModeWindow))
		self.curMouseModeButton = [ mouseLeftButtonModeButton, mouseRightButtonModeButton ]

		(xLocalRight, yLocalRight) = mouseRightButtonModeButton.GetLocalPosition()
		self.curSkillButton = self.SkillButton()
		self.curSkillButton.SetParent(self)
		self.curSkillButton.SetPosition(xLocalRight, 3)
		self.curSkillButton.SetSkillEvent(ui.__mem_func__(self.ToggleRightMouseButtonModeWindow))
		self.curSkillButton.Hide()

		(xLeft, yLeft) = mouseLeftButtonModeButton.GetGlobalPosition()
		(xRight, yRight) = mouseRightButtonModeButton.GetGlobalPosition()
		leftModeButtonList = self.mouseModeButtonList[self.MOUSE_BUTTON_LEFT]
		leftModeButtonList.SetPosition(xLeft, yLeft - leftModeButtonList.GetHeight()-5)
		if app.ENABLE_WINDOW_RESIZE:
			leftModeButtonList.SetResizeDic({ "position": (Expr("SCREEN_WIDTH")/2 - 128, Expr("SCREEN_HEIGHT") - 34 - leftModeButtonList.GetHeight()-5) })
		rightModeButtonList = self.mouseModeButtonList[self.MOUSE_BUTTON_RIGHT]
		rightModeButtonList.SetPosition(xRight - rightModeButtonList.GetWidth() + 32, yRight - rightModeButtonList.GetHeight()-5)
		if app.ENABLE_WINDOW_RESIZE:
			rightModeButtonList.SetResizeDic({ "position": (Expr("SCREEN_WIDTH")/2 + 128 + 66 + 11 - rightModeButtonList.GetWidth() + 32, Expr("SCREEN_HEIGHT") - 34 - rightModeButtonList.GetHeight()-5) })
		rightModeButtonList.GetChild("button_skill").SetEvent(lambda adir=self.MOUSE_BUTTON_RIGHT, aevent=self.EVENT_SKILL: self.SelectMouseButtonEvent(adir, aevent))
		rightModeButtonList.GetChild("button_skill").Hide()

		mouseImage = ui.ImageBox("TOP_MOST")
		mouseImage.AddFlag("float")
		mouseImage.LoadImage("d:/ymir work/ui/game/taskbar/mouse_button_camera_01.sub")
		mouseImage.SetPosition(xRight, wndMgr.GetScreenHeight() - 34)
		if app.ENABLE_WINDOW_RESIZE:
			mouseImage.SetResizeDic({ "position": (Expr("SCREEN_WIDTH")/2 + 128 + 66 + 11, Expr("SCREEN_HEIGHT") - 34) })
		mouseImage.Hide()
		self.mouseImage = mouseImage

		dir = self.MOUSE_BUTTON_LEFT
		wnd = self.mouseModeButtonList[dir]
		wnd.GetChild("button_move_and_attack").SetEvent(lambda adir=dir, aevent=self.EVENT_MOVE_AND_ATTACK: self.SelectMouseButtonEvent(adir, aevent))
		wnd.GetChild("button_auto_attack").SetEvent(lambda adir=dir, aevent=self.EVENT_AUTO: self.SelectMouseButtonEvent(adir, aevent))
		wnd.GetChild("button_camera").SetEvent(lambda adir=dir, aevent=self.EVENT_CAMERA: self.SelectMouseButtonEvent(adir, aevent))
		if METIN_QUEUE_MOUSE_MODE_ENABLED:
			wnd.GetChild("button_metin_queue").SetEvent(lambda adir=dir, aevent=self.EVENT_METIN_QUEUE: self.SelectMouseButtonEvent(adir, aevent))

		dir = self.MOUSE_BUTTON_RIGHT
		wnd = self.mouseModeButtonList[dir]
		wnd.GetChild("button_move_and_attack").SetEvent(lambda adir=dir, aevent=self.EVENT_MOVE_AND_ATTACK: self.SelectMouseButtonEvent(adir, aevent))
		wnd.GetChild("button_camera").SetEvent(lambda adir=dir, aevent=self.EVENT_CAMERA: self.SelectMouseButtonEvent(adir, aevent))

		self.toggleButtonDict = toggleButtonDict
		self.expGauge = expGauge
		if app.ENABLE_CONQUEROR_LEVEL:
			self.newExpGauge = newExpGauge

		self.rampageGauge1 = self.GetChild("RampageGauge")
		self.rampageGauge2 = self.GetChild("RampageGauge2")
		self.rampageGauge3 = self.GetChild("RampageGauge3")
		self.rampageGauge4 = self.GetChild("RampageGauge4")
		self.rampageGauge3.SetDelay(4)
		self.rampageGauge4.SetDelay(4)

		self.brandFlourishLogo = self.GetChild("HotStrokeLogo")
		self.brandFlourishLogo.Hide()
		self.brandFlourishLogo.ResetFrame()
		self.brandFlourishLogo.SetEndFrameEvent(ui.__mem_func__(self.__FinishBrandFlourish))
		self.orbHitArea = self.GetChild("OrbHitArea")
		self.orbHitArea.OnMouseOverIn = ui.__mem_func__(self.__RampageGauge_OverIn)
		self.orbHitArea.OnMouseOverOut = ui.__mem_func__(self.__RampageGauge_OverOut)
		self.orbHitArea.OnMouseLeftButtonUp = ui.__mem_func__(self.__RampageGauge_Click)
		self.__RampageGauge_OverOut()
		self.__ScheduleNextBrandFlourish()

		self.hpGauge = self.GetChild("HPGauge")
		self.mpGauge = self.GetChild("SPGauge")
		self.stGauge = self.GetChild("STGauge")
		self.hpRecoveryGaugeBar = self.GetChild("HPRecoveryGaugeBar")
		self.spRecoveryGaugeBar = self.GetChild("SPRecoveryGaugeBar")

		if app.ENABLE_POISON_GAUGE_EFFECT:
			self.hpPoisonGauge = self.GetChild("HPPoisonGauge")
			self.hpPoisonRecoveryGaugeBar = self.GetChild("HPPoisonRecoveryGaugeBar")
			self.hpPoisonGauge.Hide()
			self.hpPoisonRecoveryGaugeBar.Hide()

		self.hpGaugeBoard = self.GetChild("HPGauge_Board")
		self.mpGaugeBoard = self.GetChild("SPGauge_Board")
		self.stGaugeBoard = self.GetChild("STGauge_Board")
		self.expGaugeBoard = self.GetChild("EXP_Gauge_Board")
		if app.ENABLE_ANTI_EXP:
			self.GetChild("AntiExp").SetEvent(ui.__mem_func__(self.__ClickAntiExp))

		# Giftbox object
		wndGiftBox = GiftBox()
		wndGiftBox.LoadWindow()
		self.wndGiftBox = wndGiftBox

		self.__LoadMouseSettings()
		self.RefreshStatus()
		self.RefreshQuickSlot()
		self.__ApplyR1Look()
		try:
			import uir1
			uir1.FollowLook(self)
		except Exception:
			pass

	def SyncR1Look(self):
		"""Settings switched the look (uir1.LookChanged): the R1 bottom bar dressed or today's bar restored in place,
		then the gauges and the quick slots drawn again in that look."""
		import uir1
		wanted = uir1.UseR1()
		dress = getattr(self, "r1Dress", None)
		if wanted and not dress:
			self.__ApplyR1Look()
		elif not wanted and dress:
			self.r1Dress = None
			dress.Restore()
		else:
			return
		for refresh in (self.RefreshStatus, self.RefreshQuickSlot):
			try:
				refresh()
			except Exception:
				uir1.TraceFailure("Spodni lista (look switch)")

	def __ApplyR1Look(self):
		# R1 bottom bar A2 (root/uitaskbarr1.py); the old look ("Stary vzhled") or a failure keeps today's bar
		# (traced there, today's art restored, not retried in this session).
		self.r1Dress = None
		try:
			import uitaskbarr1
			self.r1Dress = uitaskbarr1.Create(self)
		except Exception:
			import dbg
			dbg.TraceError("R1 look of Spodni lista could not be loaded, the original look is used.")
			self.r1Dress = None
		if self.r1Dress:
			self.RefreshQuickSlot()

	def __R1(self, method, *args):
		# True when the R1 bar took the update; a failing R1 update restores today's bar and returns False.
		dress = getattr(self, "r1Dress", None)
		return bool(dress) and dress.Call(method, *args)

	if app.ENABLE_ANTI_EXP:
		def __ClickAntiExp(self):
			net.SendChatPacket("/anti_exp")

	def __RegisterPrimaryAuxButton(self, toggleButtonDict):
		TaskBar.IS_EXPANDED = False
		self.primaryAuxButton = None
		for buttonKey, childName, isExpanded in (
			(TaskBar.BUTTON_CHAT, "ChatButton", False),
			(TaskBar.BUTTON_EXPAND, "ExpandButton", True),
		):
			try:
				button = self.GetChild(childName)
			except:
				continue
			toggleButtonDict[buttonKey] = button
			self.primaryAuxButton = button
			TaskBar.IS_EXPANDED = isExpanded
			break

	def __HideIdleLogos(self):
		self.rampageGauge1.Hide()
		self.rampageGauge2.Hide()
		self.rampageGauge3.Hide()
		self.rampageGauge4.Hide()

	def __RefreshIdleLogo(self):
		self.__HideIdleLogos()
		if self.brandFlourishActive:
			return
		if app.ENABLE_HEART_BEAT_MALL and self.heartBeat:
			if self.orbLogoHovered:
				self.rampageGauge4.Show()
			else:
				self.rampageGauge3.Show()
		else:
			if self.orbLogoHovered:
				self.rampageGauge2.Show()
			else:
				self.rampageGauge1.Show()

	def __RampageGauge_OverIn(self):
		self.orbLogoHovered = True
		self.__RefreshIdleLogo()

	def __RampageGauge_OverOut(self):
		self.orbLogoHovered = False
		self.__RefreshIdleLogo()

	def __ScheduleNextBrandFlourish(self):
		self.brandFlourishNextAt = app.GetTime() + 15.0

	def __FinishBrandFlourish(self):
		self.brandFlourishLogo.Hide()
		self.brandFlourishLogo.ResetFrame()
		self.brandFlourishActive = False
		self.__RefreshIdleLogo()
		self.__ScheduleNextBrandFlourish()

	def __StartBrandFlourish(self):
		self.brandFlourishActive = True
		self.__HideIdleLogos()
		self.brandFlourishLogo.ResetFrame()
		self.brandFlourishLogo.Show()

	def __UpdateBrandFlourish(self):
		if not self.brandFlourishActive and app.GetTime() >= self.brandFlourishNextAt:
			self.__StartBrandFlourish()

	def __RampageGauge_Click(self):
		if app.ENABLE_ITEMSHOP:
			osfInfo.GetInterfaceInstance().OpenItemShopWindow()

	def __LoadMouseSettings(self):
		try:
			LoadMouseButtonSettings()
			(mouseLeftButtonEvent, mouseRightButtonEvent) = GetMouseButtonSettings()
			if not self.__IsInSafeMouseButtonSettingRange(self.MOUSE_BUTTON_LEFT, mouseLeftButtonEvent) or not self.__IsInSafeMouseButtonSettingRange(self.MOUSE_BUTTON_RIGHT, mouseRightButtonEvent):
				raise RuntimeError("INVALID_MOUSE_BUTTON_SETTINGS")
		except:
			InitMouseButtonSettings(self.EVENT_AUTO, self.EVENT_CAMERA)
			(mouseLeftButtonEvent, mouseRightButtonEvent) = GetMouseButtonSettings()

		try:
			self.SelectMouseButtonEvent(self.MOUSE_BUTTON_LEFT, mouseLeftButtonEvent)
			self.SelectMouseButtonEvent(self.MOUSE_BUTTON_RIGHT, mouseRightButtonEvent)
		except:
			InitMouseButtonSettings(self.EVENT_AUTO, self.EVENT_CAMERA)
			(mouseLeftButtonEvent, mouseRightButtonEvent) = GetMouseButtonSettings()

			self.SelectMouseButtonEvent(self.MOUSE_BUTTON_LEFT, mouseLeftButtonEvent)
			self.SelectMouseButtonEvent(self.MOUSE_BUTTON_RIGHT, mouseRightButtonEvent)

	def __IsInSafeMouseButtonSettingRange(self, direction, event):
		if event < self.EVENT_MOVE or event > self.EVENT_METIN_QUEUE:
			return False
		if self.EVENT_METIN_QUEUE == event:
			return (
				METIN_QUEUE_MOUSE_MODE_ENABLED
				and self.MOUSE_BUTTON_LEFT == direction
			)
		return True

	def Destroy(self):
		SaveMouseButtonSettings()
		try:
			import uir1
			uir1.UnfollowLook(self)
		except Exception:
			pass
		if getattr(self, "r1Dress", None):
			self.r1Dress.taskbar = None
		self.r1Dress = None

		self.ClearDictionary()
		self.mouseModeButtonList[0].ClearDictionary()
		self.mouseModeButtonList[1].ClearDictionary()
		self.mouseModeButtonList = []
		self.curMouseModeButton = []
		self.curSkillButton = None
		self.selectSkillButtonList = []

		self.expGauge = None
		if app.ENABLE_CONQUEROR_LEVEL:
			self.newExpGauge = None
		self.hpGauge = None
		self.mpGauge = None
		self.stGauge = None
		self.hpRecoveryGaugeBar = None
		self.spRecoveryGaugeBar = None

		self.rampageGauge1 = None
		self.rampageGauge2 = None
		self.rampageGauge3 = None
		self.rampageGauge4 = None
		self.primaryAuxButton = None
		self.brandFlourishLogo = None
		self.orbHitArea = None
		self.orbLogoHovered = False
		self.brandFlourishActive = False
		if app.ENABLE_HEART_BEAT_MALL:
			self.heartBeat = False

		if app.ENABLE_POISON_GAUGE_EFFECT:
			self.hpPoisonGauge = None
			self.hpPoisonRecoveryGaugeBar = None	

		self.tooltipItem = None
		self.tooltipSkill = None
		self.quickslot = []
		self.toggleButtonDict = {}

		self.hpGaugeBoard = None
		self.mpGaugeBoard = None
		self.stGaugeBoard = None
		self.expGaugeBoard = None

		self.tooltipHP = None
		self.tooltipSP = None
		self.tooltipST = None
		self.tooltipEXP = None

		self.mouseImage = None

	def __OnClickQuickPageUpButton(self):
		player.SetQuickPage(player.GetQuickPage()-1)

	def __OnClickQuickPageDownButton(self):
		player.SetQuickPage(player.GetQuickPage()+1)

	def SetToggleButtonEvent(self, eButton, kEventFunc):
		self.toggleButtonDict[eButton].SetEvent(kEventFunc)

	def HasPrimaryAuxButton(self):
		return self.primaryAuxButton is not None

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetSkillToolTip(self, tooltipSkill):
		self.tooltipSkill = tooltipSkill
		self.curSkillButton.SetSkillToolTip(self.tooltipSkill)

	## Mouse Image
	def ShowMouseImage(self):
		self.mouseImage.SetTop()
		self.mouseImage.Show()

	def HideMouseImage(self):
		player.SetQuickCameraMode(False)
		self.mouseImage.Hide()

	## Gauge
	def RefreshStatus(self):
		curHP = player.GetStatus(player.HP)
		maxHP = player.GetStatus(player.MAX_HP)
		curSP = player.GetStatus(player.SP)
		maxSP = player.GetStatus(player.MAX_SP)
		if app.ENABLE_CONQUEROR_LEVEL:
			if player.GetStatus(player.POINT_CONQUEROR_LEVEL) > 0:
				curEXP = unsigned32(player.GetStatus(player.POINT_CONQUEROR_EXP))
				nextEXP = unsigned32(player.GetStatus(player.POINT_CONQUEROR_NEXT_EXP))
			else:
				curEXP = unsigned32(player.GetStatus(player.EXP))
				nextEXP = unsigned32(player.GetStatus(player.NEXT_EXP))
		else:
			curEXP = unsigned32(player.GetStatus(player.EXP))
			nextEXP = unsigned32(player.GetStatus(player.NEXT_EXP))
		recoveryHP = player.GetStatus(player.HP_RECOVERY)
		recoverySP = player.GetStatus(player.SP_RECOVERY)

		self.RefreshStamina()

		if app.ENABLE_POISON_GAUGE_EFFECT:
			if chrmgr.HasAffectByVID(player.GetMainCharacterIndex(), chr.AFFECT_POISON):
				self.hpGauge.Hide()
				self.hpPoisonGauge.Show()
			else:
				self.hpPoisonGauge.Hide()
				self.hpGauge.Show()

		self.SetHP(curHP, recoveryHP, maxHP)
		self.SetSP(curSP, recoverySP, maxSP)
		self.SetExperience(curEXP, nextEXP)

	def RefreshStamina(self):
		curST = player.GetStatus(player.STAMINA)
		maxST = player.GetStatus(player.MAX_STAMINA)

		try:
			curST = int(curST)
			maxST = int(maxST)
		except (TypeError, ValueError):
			curST = 0
			maxST = 1

		self.SetST(curST, maxST)

	def RefreshSkill(self):
		self.curSkillButton.RefreshSkill()
		for button in self.selectSkillButtonList:
			button.RefreshSkill()

	if app.ENABLE_SKILL_COOLTIME_UPDATE:
		def SkillClearCoolTime(self, usedSlotIndex):
			QUICK_SLOT_SLOT_COUNT = 4
			slotIndex = 0
			for slotWindow in self.quickslot:
				for i in range(QUICK_SLOT_SLOT_COUNT):
					(Type, Position) = player.GetLocalQuickSlot(slotIndex)
					if Type == player.SLOT_TYPE_SKILL:
						if usedSlotIndex == Position:
							slotWindow.SetSlotCoolTime(slotIndex, 0)
							return
					slotIndex += 1

	def SetHP(self, curPoint, recoveryPoint, maxPoint):
		curPoint = min(curPoint, maxPoint)
		if maxPoint > 0:
			if app.ENABLE_POISON_GAUGE_EFFECT:
				self.hpPoisonGauge.SetPercentage(curPoint, maxPoint)
			self.hpGauge.SetPercentage(curPoint, maxPoint)
			self.tooltipHP.SetText("%s : %d / %d" % (localeInfo.TASKBAR_HP, curPoint, maxPoint))

			if 0 == recoveryPoint:
				if app.ENABLE_POISON_GAUGE_EFFECT:
					self.hpPoisonRecoveryGaugeBar.Hide()
				self.hpRecoveryGaugeBar.Hide()
			else:
				destPoint = min(maxPoint, curPoint + recoveryPoint)
				newWidth = int(self.GAUGE_WIDTH * (float(destPoint) / float(maxPoint)))
				if app.ENABLE_POISON_GAUGE_EFFECT:
					if chrmgr.HasAffectByVID(player.GetMainCharacterIndex(), chr.AFFECT_POISON):
						if self.hpRecoveryGaugeBar.IsShow():
							self.hpRecoveryGaugeBar.Hide()
						self.hpPoisonRecoveryGaugeBar.SetSize(newWidth, self.GAUGE_HEIGHT)
						self.hpPoisonRecoveryGaugeBar.Show()
						return
					else:
						if self.hpPoisonRecoveryGaugeBar.IsShow():
							self.hpPoisonRecoveryGaugeBar.Hide()
						self.hpRecoveryGaugeBar.SetSize(newWidth, self.GAUGE_HEIGHT)
						self.hpRecoveryGaugeBar.Show()	
				self.hpRecoveryGaugeBar.SetSize(newWidth, self.GAUGE_HEIGHT)
				self.hpRecoveryGaugeBar.Show()

		if app.ENABLE_HEART_BEAT_MALL and maxPoint > 0:
			curPointPct = int(100 * float(curPoint) / float(maxPoint))
			self.heartBeat = curPointPct <= 50
			self.__RefreshIdleLogo()

	def SetSP(self, curPoint, recoveryPoint, maxPoint):
		curPoint = min(curPoint, maxPoint)
		if maxPoint > 0:
			self.mpGauge.SetPercentage(curPoint, maxPoint)
			self.tooltipSP.SetText("%s : %d / %d" % (localeInfo.TASKBAR_SP, curPoint, maxPoint))

			if 0 == recoveryPoint:
				self.spRecoveryGaugeBar.Hide()
			else:
				destPoint = min(maxPoint, curPoint + recoveryPoint)
				newWidth = int(self.GAUGE_WIDTH * (float(destPoint) / float(maxPoint)))
				self.spRecoveryGaugeBar.SetSize(newWidth, self.GAUGE_HEIGHT)
				self.spRecoveryGaugeBar.Show()

	def SetST(self, curPoint, maxPoint):
		curPoint = min(curPoint, maxPoint)
		if maxPoint > 0:
			self.stGauge.SetPercentage(curPoint, maxPoint)
			self.tooltipST.SetText("%s : %d / %d" % (localeInfo.TASKBAR_ST, curPoint, maxPoint))

	def SetExperience(self, curPoint, maxPoint):
		curPoint = min(curPoint, maxPoint)
		curPoint = max(curPoint, 0)
		maxPoint = max(maxPoint, 0)

		quarterPoint = maxPoint // 4
		FullCount = 0

		if 0 != quarterPoint:
			FullCount = min(4, curPoint // quarterPoint)

		if app.ENABLE_CONQUEROR_LEVEL:
			if player.GetStatus(player.POINT_CONQUEROR_LEVEL) > 0:
				for i in range(4):
					self.expGauge[i].Hide()
					self.newExpGauge[i].Hide()

				for i in range(FullCount):
					self.newExpGauge[i].SetRenderingRect(0.0, 0.0, 0.0, 0.0)
					self.newExpGauge[i].Show()

				if 0 != quarterPoint:
					if FullCount < 4:
						Percentage = float(curPoint % quarterPoint) / quarterPoint - 1.0
						self.newExpGauge[FullCount].SetRenderingRect(0.0, Percentage, 0.0, 0.0)
						self.newExpGauge[FullCount].Show()

				self.tooltipEXP.SetText("%s : %.2f%%" % (localeInfo.TASKBAR_EXP, float(curPoint) / max(1, float(maxPoint)) * 100))
				return
			else:
				for i in range(4):
					self.newExpGauge[i].Hide()

		for i in range(4):
			self.expGauge[i].Hide()

		for i in range(FullCount):
			self.expGauge[i].SetRenderingRect(0.0, 0.0, 0.0, 0.0)
			self.expGauge[i].Show()

		if 0 != quarterPoint:
			if FullCount < 4:
				Percentage = float(curPoint % quarterPoint) / quarterPoint - 1.0
				self.expGauge[FullCount].SetRenderingRect(0.0, Percentage, 0.0, 0.0)
				self.expGauge[FullCount].Show()

		#####
		self.tooltipEXP.SetText("%s : %.2f%%" % (localeInfo.TASKBAR_EXP, float(curPoint) / max(1, float(maxPoint)) * 100))

	## QuickSlot
	def RefreshQuickSlot(self):
		pageNum = player.GetQuickPage()

		try:
			dress = getattr(self, "r1Dress", None)
			if dress:
				self.quickPageNumImageBox.LoadImage(dress.PagePath(pageNum))
			else:
				self.quickPageNumImageBox.LoadImage(TaskBar.QUICKPAGE_NUMBER_FILENAME[pageNum])
		except:
			pass

		startNumber = 0
		for slot in self.quickslot:

			for i in range(4):
				slotNumber = i+startNumber

				(Type, Position) = player.GetLocalQuickSlot(slotNumber)

				globalSlotIndex = player.LocalQuickSlotIndexToGlobalQuickSlotIndex(
					slotNumber)
				if not quickslotpolicy.ReconcileStoredQuickSlot(
						Type,
						Position,
						globalSlotIndex,
						self.pendingQuickSlotDeletes):
					slot.ClearSlot(slotNumber)
					continue

				if player.SLOT_TYPE_INVENTORY == Type:
					itemIndex = player.GetItemIndex(Position)
					itemCount = player.GetItemCount(Position)
					if itemCount <= 1:
						itemCount = 0

					## 자동물약 (#72723, #72724) 특수처리 - 아이템인데도 슬롯에 활성화/비활성화 표시를 위한 작업임 - [hyo]
					if constInfo.IS_AUTO_POTION(itemIndex):
						# metinSocket - [0] : 활성화 여부, [1] : 사용한 양, [2] : 최대 용량
						metinSocket = [player.GetItemMetinSocket(Position, j) for j in range(player.METIN_SOCKET_MAX_NUM)]

						if 0 != int(metinSocket[0]):
							slot.ActivateSlotOld(slotNumber)
						else:
							slot.DeactivateSlot(slotNumber)

					if item.IsPetPay(itemIndex):
						metinSocket = [player.GetItemMetinSocket(Position, j) for j in range(player.METIN_SOCKET_MAX_NUM)]

						if 0 != int(metinSocket[1]):
							slot.ActivateSlotOld(slotNumber)
						else:
							slot.DeactivateSlot(slotNumber)

					if app.ENABLE_SOUL_SYSTEM:
						if item.IsSoulItem(itemIndex):
							metinSocket = [player.GetItemMetinSocket(window, Position, j) for j in range(player.METIN_SOCKET_MAX_NUM)]

							if 0 != int(metinSocket[1]):
								slot.ActivateSlotOld(slotNumber)
							else:
								slot.DeactivateSlot(slotNumber)

					if app.ENABLE_GROWTH_PET_SYSTEM:
						if constInfo.IS_PET_ITEM(itemIndex):
							self.__SetCoolTimePetItemSlot(slot, Position, slotNumber, itemIndex)
							
							slot.DeactivateSlot(slotNumber)
							
							active_id = player.GetActivePetItemId()
							if active_id and active_id == player.GetItemMetinSocket(Position, 2):
								slot.ActivateSlotOld(slotNumber)

					slot.SetItemSlot(slotNumber, itemIndex, itemCount)

				elif player.SLOT_TYPE_SKILL == Type:
					skillIndex = player.GetSkillIndex(Position)
					if 0 == skillIndex:
						slot.ClearSlot(slotNumber)
						continue

					skillType = skill.GetSkillType(skillIndex)
					if skill.SKILL_TYPE_GUILD == skillType:
						skillGrade = 0
						skillLevel = guild.GetSkillLevel(Position)
					else:
						skillGrade = player.GetSkillGrade(Position)
						skillLevel = player.GetSkillLevel(Position)

					slot.SetSkillSlotNew(slotNumber, skillIndex, skillGrade, skillLevel)
					slot.SetSlotCountNew(slotNumber, skillGrade, skillLevel)
					slot.SetCoverButton(slotNumber)

					## NOTE : CoolTime 체크
					if player.IsSkillCoolTime(Position):
						(coolTime, elapsedTime) = player.GetSkillCoolTime(Position)
						slot.SetSlotCoolTime(slotNumber, coolTime, elapsedTime)

					## NOTE : Activate 되어 있다면 아이콘도 업데이트
					if player.IsSkillActive(Position):
						slot.ActivateSlotOld(slotNumber)
					else:
						slot.DeactivateSlot(slotNumber)

				elif player.SLOT_TYPE_EMOTION == Type:

					emotionIndex = Position
					slot.SetEmotionSlot(slotNumber, emotionIndex)
					slot.SetCoverButton(slotNumber)
					slot.SetSlotCount(slotNumber, 0)

			slot.RefreshSlot()
			startNumber += 4

	if app.ENABLE_GROWTH_PET_SYSTEM:		
		def __SetCoolTimePetItemSlot(self, slot, Position, slotNumber, itemVnum):
		
			item.SelectItem(itemVnum)
			itemSubType = item.GetItemSubType()
		
			if itemSubType not in [item.PET_UPBRINGING, item.PET_BAG]:
				return
				
			if itemSubType == item.PET_BAG:
				id = player.GetItemMetinSocket(Position, 2)
				if id == 0:
					return
			
			(limitType, limitValue) = item.GetLimit(0)

			if itemSubType == item.PET_UPBRINGING:
				limitValue = player.GetItemMetinSocket(Position, 1)
					
			if limitType in [item.LIMIT_REAL_TIME, item.LIMIT_REAL_TIME_START_FIRST_USE]:
				sock_time   = player.GetItemMetinSocket(Position, 0)
				remain_time = max( 0, sock_time - app.GetGlobalTimeStamp() )
				
				slot.SetSlotCoolTimeInverse(slotNumber, limitValue, limitValue - remain_time)

	def canAddQuickSlot(self, Type, slotNumber):
		return quickslotpolicy.CanRegisterQuickSlot(Type, slotNumber)

	def AddQuickSlot(self, localSlotIndex):
		AttachedSlotType = slotwindowpolicy.NormalizeSlotType(
			mouseModule.mouseController.GetAttachedType())
		AttachedSlotNumber = mouseModule.mouseController.GetAttachedSlotNumber()

		if player.SLOT_TYPE_QUICK_SLOT == AttachedSlotType:
			(Type, Position) = player.GetGlobalQuickSlot(AttachedSlotNumber)
			if quickslotpolicy.CanRegisterQuickSlot(Type, Position):
				player.RequestMoveGlobalQuickSlotToLocalQuickSlot(
					AttachedSlotNumber,
					localSlotIndex)
		elif self.canAddQuickSlot(AttachedSlotType, AttachedSlotNumber):
			player.RequestAddLocalQuickSlot(
				localSlotIndex,
				AttachedSlotType,
				AttachedSlotNumber)
		else:
			dbg.TraceError("Quickslot registration refused: type=%d position=%d state=%d" % (
				AttachedSlotType, AttachedSlotNumber,
				quickslotpolicy.GetQuickSlotState(AttachedSlotType, AttachedSlotNumber)))

		mouseModule.mouseController.DeattachObject()
		self.RefreshQuickSlot()

	def SelectEmptyQuickSlot(self, slotIndex):
		if True == mouseModule.mouseController.isAttached():
			self.AddQuickSlot(slotIndex)

	def SelectItemQuickSlot(self, localQuickSlotIndex):
		if True == mouseModule.mouseController.isAttached():
			self.AddQuickSlot(localQuickSlotIndex)
		else:
			globalQuickSlotIndex=player.LocalQuickSlotIndexToGlobalQuickSlotIndex(localQuickSlotIndex)
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_QUICK_SLOT, globalQuickSlotIndex, globalQuickSlotIndex)

	def UnselectItemQuickSlot(self, localSlotIndex):
		if False == mouseModule.mouseController.isAttached():
			player.RequestUseLocalQuickSlot(localSlotIndex)
			return
		elif mouseModule.mouseController.isAttached():
			mouseModule.mouseController.DeattachObject()
			return

	def OnUseSkill(self, usedSlotIndex, coolTime):
		QUICK_SLOT_SLOT_COUNT = 4
		slotIndex = 0

		## Current Skill Button
		if usedSlotIndex == self.curSkillButton.GetSlotIndex():
			self.curSkillButton.Activate(coolTime)

		## Quick Slot
		for slotWindow in self.quickslot:
			for i in range(QUICK_SLOT_SLOT_COUNT):
				(Type, Position) = player.GetLocalQuickSlot(slotIndex)

				if Type == player.SLOT_TYPE_SKILL:
					if usedSlotIndex == Position:
						slotWindow.SetSlotCoolTime(slotIndex, coolTime)
						return

				slotIndex += 1

	def OnActivateSkill(self, usedSlotIndex):
		slotIndex = 0

		## Current Skill Button
		if usedSlotIndex == self.curSkillButton.GetSlotIndex():
			self.curSkillButton.ActivateSlotOld(0)

		## Quick Slot
		for slotWindow in self.quickslot:
			for i in range(4):
				(Type, Position) = player.GetLocalQuickSlot(slotIndex)

				if Type == player.SLOT_TYPE_SKILL:
					if usedSlotIndex == Position:
						slotWindow.ActivateSlotOld(slotIndex)

				slotIndex += 1

	def OnDeactivateSkill(self, usedSlotIndex):
		slotIndex = 0

		## Current Skill Button
		if usedSlotIndex == self.curSkillButton.GetSlotIndex():
			self.curSkillButton.DeactivateSlot(0)

		## Quick Slot
		for slotWindow in self.quickslot:
			for i in range(4):
				(Type, Position) = player.GetLocalQuickSlot(slotIndex)

				if Type == player.SLOT_TYPE_SKILL:
					if usedSlotIndex == Position:
						slotWindow.DeactivateSlot(slotIndex)

				slotIndex += 1

	## ToolTip
	def OverInItem(self, slotNumber):
		if mouseModule.mouseController.isAttached():
			return

		(Type, Position) = player.GetLocalQuickSlot(slotNumber)

		if player.SLOT_TYPE_INVENTORY == Type:
			self.tooltipItem.SetInventoryItem(Position)
			self.tooltipSkill.HideToolTip()

		elif player.SLOT_TYPE_SKILL == Type:
			skillIndex = player.GetSkillIndex(Position)
			skillType = skill.GetSkillType(skillIndex)

			if skill.SKILL_TYPE_GUILD == skillType:
				skillGrade = 0
				skillLevel = guild.GetSkillLevel(Position)

			else:
				skillGrade = player.GetSkillGrade(Position)
				skillLevel = player.GetSkillLevel(Position)

			self.tooltipSkill.SetSkillNew(Position, skillIndex, skillGrade, skillLevel)
			# rebuilt from the new level / grade on RefreshSkill while the mouse stays on the slot
			self.tooltipSkill.RememberRefresh(self.OverInItem, slotNumber)
			self.tooltipItem.HideToolTip()

	def OverOutItem(self):
		if 0 != self.tooltipItem:
			self.tooltipItem.HideToolTip()
		if 0 != self.tooltipSkill:
			self.tooltipSkill.HideToolTip()

	def OnUpdate(self):
		if app.GetGlobalTime() - self.lastUpdateQuickSlot > 500:
			self.lastUpdateQuickSlot = app.GetGlobalTime()
			self.RefreshQuickSlot()

		if True == self.hpGaugeBoard.IsIn():
			self.tooltipHP.Show()
		else:
			self.tooltipHP.Hide()

		if True == self.mpGaugeBoard.IsIn():
			self.tooltipSP.Show()
		else:
			self.tooltipSP.Hide()

		if True == self.stGaugeBoard.IsIn():
			self.tooltipST.Show()
		else:
			self.tooltipST.Hide()

		if True == self.expGaugeBoard.IsIn():
			self.tooltipEXP.Show()
		else:
			self.tooltipEXP.Hide()

		self.__UpdateBrandFlourish()
		self.__R1("Update")

	## Skill
	def ToggleLeftMouseButtonModeWindow(self):
		wndMouseButtonMode = self.mouseModeButtonList[self.MOUSE_BUTTON_LEFT]

		if True == wndMouseButtonMode.IsShow():
			wndMouseButtonMode.Hide()
		else:
			wndMouseButtonMode.Show()

	def ToggleRightMouseButtonModeWindow(self):
		wndMouseButtonMode = self.mouseModeButtonList[self.MOUSE_BUTTON_RIGHT]

		if True == wndMouseButtonMode.IsShow():
			wndMouseButtonMode.Hide()
			self.CloseSelectSkill()
		else:
			wndMouseButtonMode.Show()
			self.OpenSelectSkill()

	def OpenSelectSkill(self):
		PAGE_SLOT_COUNT = 6

		(xSkillButton, y) = self.curSkillButton.GetGlobalPosition()
		y -= (37 + 32 + 1)

		for key in self.skillCategoryNameList:
			appendCount = 0
			startNumber = self.skillPageStartSlotIndexDict[key]
			x = xSkillButton

			getSkillIndex=player.GetSkillIndex
			getSkillLevel=player.GetSkillLevel

			for i in range(PAGE_SLOT_COUNT):
				skillIndex = getSkillIndex(startNumber+i)
				skillLevel = getSkillLevel(startNumber+i)

				if 0 == skillIndex:
					continue
				if 0 == skillLevel:
					continue
				if skill.IsStandingSkill(skillIndex):
					continue

				## FIXME : 스킬 하나당 슬롯 하나씩 할당하는건 아무리 봐도 부하가 크다.
				##		 이 부분은 시간을 나면 고치도록. - [levites]
				skillButton = self.SkillButton()
				skillButton.SetSkill(startNumber+i)
				skillButton.SetPosition(x, y)
				skillButton.SetSkillEvent(ui.__mem_func__(self.CloseSelectSkill), startNumber+i+1)
				skillButton.SetSkillToolTip(self.tooltipSkill)
				skillButton.SetTop()
				skillButton.Show()
				self.selectSkillButtonList.append(skillButton)

				appendCount += 1
				x -= 32

			if appendCount > 0:
				y -= 32

	def CloseSelectSkill(self, slotIndex=-1):
		self.mouseModeButtonList[self.MOUSE_BUTTON_RIGHT].Hide()
		for button in self.selectSkillButtonList:
			button.Destroy()

		self.selectSkillButtonList = []

		if -1 != slotIndex:
			self.curSkillButton.Show()
			self.curMouseModeButton[self.MOUSE_BUTTON_RIGHT].Hide()
			player.SetMouseFunc(player.MBT_RIGHT, player.MBF_SKILL)
			player.ChangeCurrentSkillNumberOnly(slotIndex-1)
		else:
			self.curSkillButton.Hide()
			self.curMouseModeButton[self.MOUSE_BUTTON_RIGHT].Show()

	def SelectMouseButtonEvent(self, dir, event):
		if not self.__IsInSafeMouseButtonSettingRange(dir, event):
			return

		SetMouseButtonSetting(dir, event)

		self.CloseSelectSkill()
		self.mouseModeButtonList[dir].Hide()

		btn = 0
		type = self.NONE
		func = self.NONE
		tooltip_text = ""

		if self.MOUSE_BUTTON_LEFT == dir:
			type = player.MBT_LEFT

		elif self.MOUSE_BUTTON_RIGHT == dir:
			type = player.MBT_RIGHT

		if self.EVENT_MOVE == event:
			btn = self.mouseModeButtonList[dir].GetChild("button_move")
			func = player.MBF_MOVE
			tooltip_text = localeInfo.TASKBAR_MOVE
		elif self.EVENT_ATTACK == event:
			btn = self.mouseModeButtonList[dir].GetChild("button_attack")
			func = player.MBF_ATTACK
			tooltip_text = localeInfo.TASKBAR_ATTACK
		elif self.EVENT_AUTO == event:
			btn = self.mouseModeButtonList[dir].GetChild("button_auto_attack")
			func = player.MBF_AUTO
			tooltip_text = localeInfo.TASKBAR_AUTO
		elif self.EVENT_MOVE_AND_ATTACK == event:
			btn = self.mouseModeButtonList[dir].GetChild("button_move_and_attack")
			func = player.MBF_SMART
			tooltip_text = localeInfo.TASKBAR_ATTACK
		elif self.EVENT_CAMERA == event:
			btn = self.mouseModeButtonList[dir].GetChild("button_camera")
			func = player.MBF_CAMERA
			tooltip_text = localeInfo.TASKBAR_CAMERA
		elif self.EVENT_SKILL == event:
			btn = self.mouseModeButtonList[dir].GetChild("button_skill")
			func = player.MBF_SKILL
			tooltip_text = localeInfo.TASKBAR_SKILL
		elif self.EVENT_METIN_QUEUE == event:
			if not METIN_QUEUE_MOUSE_MODE_ENABLED or self.MOUSE_BUTTON_LEFT != dir:
				return
			btn = self.mouseModeButtonList[dir].GetChild("button_metin_queue")
			func = player.MBF_METIN_QUEUE
			tooltip_text = localeInfo.TASKBAR_METIN_QUEUE

		if 0 != btn:
			self.curMouseModeButton[dir].SetToolTipText(tooltip_text, 0, -18)
			self.curMouseModeButton[dir].SetUpVisual(btn.GetUpVisualFileName())
			self.curMouseModeButton[dir].SetOverVisual(btn.GetOverVisualFileName())
			self.curMouseModeButton[dir].SetDownVisual(btn.GetDownVisualFileName())
			self.curMouseModeButton[dir].Show()

		player.SetMouseFunc(type, func)

	def OnChangeCurrentSkill(self, skillSlotNumber):
		self.curSkillButton.SetSkill(skillSlotNumber)
		self.curSkillButton.Show()
		self.curMouseModeButton[self.MOUSE_BUTTON_RIGHT].Hide()
