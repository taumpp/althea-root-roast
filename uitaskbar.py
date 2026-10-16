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

	def __init__(self):
		ui.Window.__init__(self)
		self.SetWindowName("ExpandedTaskBar")

		self.exclusion_list = []
		self.hiddenButtonKeys = set()
		self.wndInventory = None
		self.petAlbumCaptureBadge = None

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
			if key in self.hiddenButtonKeys:
				button.Hide()

		self.RePositionButton()
		if ExpandedTaskBar.BUTTON_PET in self.toggleButtonDict:
			import uipetalbumcapturebadge
			self.petAlbumCaptureBadge = uipetalbumcapturebadge.AlbumCaptureBadge(
				self.toggleButtonDict[ExpandedTaskBar.BUTTON_PET], 22, 2)

	def BindInventoryWindow(self, wndInventory):
		from _weakref import proxy
		self.wndInventory = proxy(wndInventory)
		self.SetParent(wndInventory)
		self.SetPosition(0, 33)
		self.RePositionButton()
		self.Show()

	@WindowDestroy
	def Destroy(self):
		self.Hide()
		if self.petAlbumCaptureBadge:
			self.petAlbumCaptureBadge.Destroy()
		self.petAlbumCaptureBadge = None
		self.ClearDictionary()
		self.toggleButtonDict = {}
		self.expandedTaskBarBoard = None
		self.wndInventory = None
		self.exclusion_list = []
		self.hiddenButtonKeys = set()

	def RePositionButton(self):
		button_order = [key for key in (
			ExpandedTaskBar.BUTTON_SPECIAL_INVENTORY,
			ExpandedTaskBar.BUTTON_QUICK_EQUIP,
			ExpandedTaskBar.BUTTON_DRAGON_SOUL,
			ExpandedTaskBar.BUTTON_BIOLOG,
			ExpandedTaskBar.BUTTON_TELEPORT,
			ExpandedTaskBar.BUTTON_PET,
			ExpandedTaskBar.BUTTON_SHOP_SEARCH,
			ExpandedTaskBar.BUTTON_SWITCHBOT,
			ExpandedTaskBar.BUTTON_TALISMAN,
			ExpandedTaskBar.BUTTON_MISSION_BOOKS,
			ExpandedTaskBar.BUTTON_MOUNT,
			ExpandedTaskBar.BUTTON_DEW,
		) if (key in self.toggleButtonDict
			and key not in self.exclusion_list
			and key not in self.hiddenButtonKeys)]

		pos_x = 2
		pos_y = 4
		for key in button_order:
			button = self.toggleButtonDict.get(key)
			if not button:
				continue

			if key in self.exclusion_list:
				continue

			button.SetPosition(pos_x, pos_y)
			pos_y += 41
		railHeight = 4 + len(button_order) * 41
		self.SetSize(42, railHeight)
		self.expandedTaskBarBoard.SetSize(42, railHeight)
		self.expandedTaskBarBoard.SetScale(1.0, float(railHeight) / 334.0)

	if app.ENABLE_WINDOW_RESIZE:
		def OnResize(self):
			try:
				self.RePositionButton()
			except:
				pass

	def SetTop(self):
		super(ExpandedTaskBar, self).SetTop()
		for button in self.toggleButtonDict.values():
			button.SetTop()

	def Show(self):
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()

	def SetToolTipText(self, eButton, text):
		self.toggleButtonDict[eButton].SetToolTipText(text)

	def SetToggleButtonEvent(self, eButton, kEventFunc):
		self.toggleButtonDict[eButton].SetEvent(kEventFunc)

	def SetButtonVisible(self, eButton, visible):
		button = self.toggleButtonDict.get(eButton)
		if not button:
			return
		if visible:
			self.hiddenButtonKeys.discard(eButton)
			button.Show()
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
		AttachedSlotType = mouseModule.mouseController.GetAttachedType()
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
			self.curSkillButton.Deactivate()

		## Quick Slot
		for slotWindow in self.quickslot:
			for i in range(4):
				(Type, Position) = player.GetLocalQuickSlot(slotIndex)

				if Type == player.SLOT_TYPE_SKILL:
					if usedSlotIndex == Position:
						slotWindow.ActivateSlotOld(slotIndex)
						return

				slotIndex += 1

	def OnDeactivateSkill(self, usedSlotIndex):
		slotIndex = 0

		## Current Skill Button
		if usedSlotIndex == self.curSkillButton.GetSlotIndex():
			self.curSkillButton.Deactivate()

		## Quick Slot
		for slotWindow in self.quickslot:
			for i in range(4):
				(Type, Position) = player.GetLocalQuickSlot(slotIndex)

				if Type == player.SLOT_TYPE_SKILL:
					if usedSlotIndex == Position:
						slotWindow.DeactivateSlot(slotIndex)
						return

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
