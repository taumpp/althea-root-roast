import ui
import player
import mouseModule
import net
import app
import snd
import item
import mountcorebonus
import player
import chat
import grp
import uiScriptLocale
import uiRefine
import uiAttachMetin
import uiPickMoney
import uiSplitItem
import uiCommon
import uiPrivateShopBuilder # 개인상점 열동안 ItemMove 방지
import localeInfo
import constInfo
import osfInfo
import ime
import wndMgr
import uiToolTip
import itemrefineoverlay
import itemrarityaura
import itemsplitplanner
import inventoryshortcutpolicy
import talismanrefine
import exchangequickadd
import virtualquiver
import uiresonance
import auraprogression
import growthpetpresentation

SEARCH_FIELD_UI_PATH = "d:/ymir work/ui/game/crimson_ember/inventory/"

if app.ENABLE_PICK_GEM_SYSTEM:
	import uiPickGem

if app.ENABLE_PERMA_ACCESSORY:
	import math

if app.ENABLE_GEM_SYSTEM:
	import uiPickETC

if app.ENABLE_ACCE_COSTUME_SYSTEM:
	import acce

if app.ENABLE_PERMA_ACCESSORY:
	import math

ITEM_MALL_BUTTON_ENABLE = True
ITEM_FLAG_APPLICABLE = 1 << 14
RARITY_SCROLL_VNUM = 79628
RARITY_REROLL_VNUM = 79630
RARITY_TARGETED_VNUM = 79632
WEAPON_ENHANCEMENT_TARGETS = {
	79634: {299: 35009, 1179: 35019, 2159: 35029, 3219: 35039, 5119: 35049, 7169: 35059},
	79635: {3169: 51360, 189: 51361, 199: 51362, 2179: 51363, 1139: 51364, 5129: 51365},
}
EQUIPMENT_UNIQUE3_INDEX = player.EQUIPMENT_SLOT_START + 11
EQUIPMENT_UNIQUE4_INDEX = player.EQUIPMENT_SLOT_START + 12
REFINE_OVERLAY_ITEM_TYPES = (
	item.ITEM_TYPE_WEAPON,
	item.ITEM_TYPE_ARMOR,
	item.ITEM_TYPE_ROD,
	item.ITEM_TYPE_UNIQUE,
	item.ITEM_TYPE_PICK,
	item.ITEM_TYPE_RING,
	item.ITEM_TYPE_BELT,
)

def ReprGetItemIndex(window):
	return lambda pos : player.GetItemIndex(window, pos)

if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
	TYPE_SELL = 1
	TYPE_FRAG = 2
	
	class MultipleInventoryWindow(ui.ScriptWindow):	
		def __init__(self, wndInventory):
			if not wndInventory:
				return
			
			ui.ScriptWindow.__init__(self)
			self.isLoaded = 0
			
			self.wndInventory = wndInventory;
			self.wndMultipleInventoryLayer = None
			self.priceText = None
			self.FragText = None
			self.multipleChoiceBtn = []
			self.curType = TYPE_SELL
			self.__LoadWindow()
	
		def __del__(self):
			ui.ScriptWindow.__del__(self)
	
		def Show(self, openWindowSlot = False):
			self.__LoadWindow()
			ui.ScriptWindow.Show(self)
	
			if openWindowSlot:
				self.OpenInventory()
			else:
				self.CloseInventory()
	
			self.SetTop()
	
		def Close(self):
			osfInfo.MULTIPLE_LIST = []
			self.Hide()
			
		def IsTypeDestroy(self):
			return (self.curType == TYPE_FRAG)
			
		def IsTypeSell(self):
			return (self.curType == TYPE_SELL)
	
		def IsOpeningInventory(self):
			return self.wndMultipleInventoryLayer.IsShow()
	
		def OpenInventory(self):
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.wndInventory.interface.SetOnTopWindow(player.ON_TOP_WND_MULTIPLE_SELECT)
			self.priceText.SetText("0")
			self.FragText.SetText("0 - 0 Fragments")
			osfInfo.MULTIPLE_LIST = []
			self.wndMultipleInventoryLayer.Show()
			self.AdjustPositionAndSize()
	
		def CloseInventory(self):
			if app.WJ_ENABLE_TRADABLE_ICON:
				if self.wndInventory.interface.GetOnTopWindow() == player.ON_TOP_WND_MULTIPLE_SELECT:
					self.wndInventory.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
			osfInfo.MULTIPLE_LIST = []
			self.wndInventory.interface.RefreshMarkInventoryBag()
			self.wndMultipleInventoryLayer.Hide()
			self.AdjustPositionAndSize()

		def GetBasePosition(self):
			x, y = self.wndInventory.GetInventoryBodyGlobalPosition()
			return x - 200, y + 5
	
		def AdjustPositionAndSize(self):
			bx, by = self.GetBasePosition()
			if self.IsOpeningInventory():
				self.SetPosition(bx - 36, by)
				self.SetSize(self.ORIGINAL_WIDTH, self.GetHeight())
			else:
				self.SetPosition(bx + 138, by);
				self.SetSize(10, self.GetHeight())			
	
		def __LoadWindow(self):
			if self.isLoaded == 1:
				return					
			
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "UIScript/MultipleInventoryWindow.py")
			except:
				import exception
				exception.Abort("MultipleWindow.LoadWindow.LoadObject")
			
			try:			
				self.ORIGINAL_WIDTH = self.GetWidth()
				GetObject = self.GetChild				
				
				self.wndMultipleInventoryLayer = self.GetChild("MultipleInventoryLayer")
				self.wndMultipleInventoryLayer.SetCloseEvent(ui.__mem_func__(self.CloseInventory))
				self.GetChild("CloseBtn").SetEvent(ui.__mem_func__(self.CloseInventory))			
				
				self.multipleChoiceBtn = []
				self.multipleChoiceBtn.append(self.GetChild("sellBtn"))
				self.multipleChoiceBtn.append(self.GetChild("FragBtn"))				
				
				self.AcceptButton = self.GetChild("AcceptButton")
				
				self.priceText = self.GetChild("Money")
				self.wndSelectText = self.GetChild("ItemSelectedText")
				
				self.FragText = self.GetChild("Fragments")
				
				self.multipleChoiceBtn[0].SetToggleUpEvent(lambda arg= 1: self.Sell(arg))
				self.multipleChoiceBtn[0].SetToggleDownEvent(lambda arg= 1: self.Sell(arg))
				self.multipleChoiceBtn[1].SetToggleUpEvent(lambda arg= 2: self.Sell(arg))		
				self.multipleChoiceBtn[1].SetToggleDownEvent(lambda arg= 2: self.Sell(arg))		

				self.AcceptButton.SetEvent(ui.__mem_func__(self.Accept))		

				self.historyButton = self.GetChild("HistoryButton")
				self.historyButton.SetEvent(ui.__mem_func__(self.OnClickHistory))
				
				self.multipleChoiceBtn[0].Down()
				self.FragText.Hide()
				self.wndMultipleInventoryLayer.Hide()
			except:
				import exception
				exception.Abort("MultipleWindow.LoadWindow.BindObject")
			
			self.isLoaded = 1			

		def OnClickHistory(self):
			self.wndInventory.interface.OpenItemSaveWindow()
		
		def Sell(self, a):
			for i in osfInfo.MULTIPLE_LIST:
				itemIndex = player.GetItemIndex(i)
				if a == 1:
					if itemIndex:
						self.OnPressSellBtn()
				elif a == 2:
					if itemIndex:
						self.OnPressFragmentBtn()
		
		def Accept(self):
			for i in osfInfo.MULTIPLE_LIST:
				itemIndex = player.GetItemIndex(i)
				if itemIndex:
					itemCount = player.GetItemCount(i)
					net.SendMultipleItem(self.curType, i, itemCount)
					snd.PlaySound("sound/ui/money.wav")
					
			self.CloseInventory()				
			net.SendChatPacket("/load_saved_items 0")
			
		def OnPressSellBtn(self):
			self.curType = TYPE_SELL
			self.multipleChoiceBtn[0].Down()
			self.multipleChoiceBtn[1].SetUp()
			self.priceText.Show()
			self.FragText.Hide()
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.wndInventory.interface.SetOnTopWindow(player.ON_TOP_WND_MULTIPLE_SELECT)
				self.wndInventory.interface.RefreshMarkInventoryBag()
						
		def OnPressFragmentBtn(self):
			self.curType = TYPE_FRAG
			self.multipleChoiceBtn[0].SetUp()
			self.multipleChoiceBtn[1].Down()
			self.priceText.Hide()
			self.FragText.Show()
			self.UpdateFragmentCount()
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.wndInventory.interface.SetOnTopWindow(player.ON_TOP_WND_MULTIPLE_SELECT)
				self.wndInventory.interface.RefreshMarkInventoryBag()
						
		def OnTop(self):
			if self.wndInventory:
				self.wndInventory.SetTop()	
				if app.WJ_ENABLE_TRADABLE_ICON:
					self.wndInventory.interface.SetOnTopWindow(player.ON_TOP_WND_MULTIPLE_SELECT)
					self.wndInventory.interface.RefreshMarkInventoryBag()
				
		def OnPressEscapeKey(self):
			self.CloseInventory()
			return True
	
		def UpdateItemCount(self, slotNumber, i):
			str_len = str(len(osfInfo.MULTIPLE_LIST))
			self.wndSelectText.SetText(uiScriptLocale.MULTIPLE_WND_SELECTED_COUNT + "("+str_len+")")
			self.UpdateFragmentCount()
			
		def UpdateFragmentCount(self):
			gotItems = 0
			for i in osfInfo.MULTIPLE_LIST:
				itemIndex = player.GetItemIndex(i)
				if itemIndex:
					item.SelectItem(itemIndex)
					
					itemType = item.GetItemType()
					subType = item.GetItemSubType()
					canContinue = False
					if itemType == item.ITEM_TYPE_ARMOR:
						if subType in [item.WEAPON_SWORD, item.WEAPON_DAGGER, item.WEAPON_BOW, item.WEAPON_TWO_HANDED, item.WEAPON_BELL, item.WEAPON_FAN]:
							canContinue = True
					elif itemType == item.ITEM_TYPE_WEAPON:
						if subType in [item.ARMOR_BODY, item.ARMOR_HEAD, item.ARMOR_SHIELD, item.ARMOR_WRIST, item.ARMOR_FOOTS, item.ARMOR_NECK, item.ARMOR_EAR]:
							canContinue = True
							
					if canContinue:
						for i in range(item.LIMIT_MAX_NUM):
							(limitType, limitValue) = item.GetLimit(i)

							if item.LIMIT_LEVEL == limitType:
								if limitValue > 35:
									gotItems = gotItems + 1
									break
			
			possibleFragments = gotItems * 8
			self.FragText.SetText("0 - " + str(possibleFragments) + " Fragments")

		def UpdatePrice(self, slotNumber, i):
			itemIndex = player.GetItemIndex(slotNumber)
			if itemIndex:
				item.SelectItem(itemIndex)
				old = self.priceText.GetText()
				old = old.replace(" ", "")
				old = old.replace("Yang", "")
				old = old.replace(".", "")
				add = item.GetISellItemPrice()
				itemCount = player.GetItemCount(slotNumber)
				if item.Is1GoldItem():
					add = itemCount // add // 5
				else:
					add = add * itemCount // 5
				
				if i == 1:
					new = int(old) + add
				else:
					new = int(old) - add
					
				self.priceText.SetText(localeInfo.NumberToMoneyString(new))


MONEY_TEXT_LIMIT_WIDTH = 130

class InventoryWindow(ui.ScriptWindow):
	USE_TYPE_TUPLE = (
		"USE_CLEAN_SOCKET",
		"USE_CHANGE_ATTRIBUTE",
		"USE_ADD_ATTRIBUTE",
		"USE_ADD_ATTRIBUTE2",
		"USE_ADD_ACCESSORY_SOCKET",
		"USE_PUT_INTO_ACCESSORY_SOCKET",
		"USE_PUT_INTO_BELT_SOCKET",
		"USE_PUT_INTO_RING_SOCKET",
		"USE_CHANGE_COSTUME_ATTR",
		"USE_RESET_COSTUME_ATTR"
	)
	if app.ENABLE_COSTUME_EXTENDED_RECHARGE:
		USE_TYPE_LIST = list(USE_TYPE_TUPLE)
		USE_TYPE_LIST.append("USE_TIME_CHARGE_PER")
		USE_TYPE_LIST.append("USE_TIME_CHARGE_FIX")
		USE_TYPE_TUPLE = tuple(USE_TYPE_LIST)

	if app.ENABLE_AURA_SYSTEM:
		USE_TYPE_TUPLE += ("USE_PUT_INTO_AURA_SOCKET",)

	if app.ENABLE_ATTR_6TH_7TH:
		USE_TYPE_TUPLE += ("USE_CHANGE_ATTRIBUTE2",)

	if app.ENABLE_PERMA_ACCESSORY:
		USE_TYPE_TUPLE += ("USE_REMOVE_PERMANENT_ORE",)

	if app.ENABLE_REFINE_ELEMENT_SYSTEM:
		USE_TYPE_TUPLE += ("USE_ELEMENT_UPGRADE", "USE_ELEMENT_DOWNGRADE", "USE_ELEMENT_CHANGE",)

	questionDialog = None
	tooltipItem = None
	if app.ENABLE_BRAVE_CAPE_RENEWAL:
		wndBraveCape = None

	dlgPickMoney = None
	dlgSplitItem = None
	if app.ENABLE_PICK_GEM_SYSTEM:
		dlgPickGem = None
	wndSpecial = None
	if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
		wndMultiple = None
	sellingSlotNumber = -1
	isLoaded = 0
	if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
		isOpenedMultipleWindowWhenClosingInventory = 0

	if app.ENABLE_GROWTH_PET_SYSTEM:
		petHatchingWindow	= None
		petFeedWindow		= None
		petNameChangeWindow = None

	interface = None

	INVENTORY_TAB_STRIP_HEIGHT_PY = 20
	INVENTORY_SEARCH_FIELD_HEIGHT_PY = 0

	def SetSpecialWnd(self, wndSpecial):
		self.wndSpecial = wndSpecial

	def __init__(self):
		if app.ENABLE_GEM_SYSTEM:
			self.wndExpandedMoneyBar = None
			self.wndGem = None

		ui.ScriptWindow.__init__(self)
		self.refineLevelOverlays = {}
		self.virtualMarketDraftSlots = set()
		self.virtualMarketDraftMouseSlots = set()
		self.dragonCoin = 0
		self.quickBuffButton = None
		self.quickBuffSettingsButton = None
		self.retiredArrowSlotCover = None

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			self.isOpenedMultipleWindowWhenClosingInventory = 0
			self.IsClickMultipleInventory = False
		self.wndInventoryBody = None
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		if app.ENABLE_GEM_SYSTEM:
			self.wndExpandedMoneyBar = None
			self.wndGem = None

	if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
		def SetClickMultipleInventory(self, isclick):
			self.IsClickMultipleInventory = isclick

	def GetInventoryBodyGlobalPosition(self):
		return self.wndInventoryBody.GetGlobalPosition()

	def Show(self):
		self.__LoadWindow()

		ui.ScriptWindow.Show(self)

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			osfInfo.MULTIPLE_LIST = []

		if app.ENABLE_BRAVE_CAPE_RENEWAL:
			if self.wndBraveCape:
				self.wndBraveCape.AdjustPosition(*self.GetInventoryBodyGlobalPosition())

		self.RefreshItemSlot()
		self.RefreshStatus()

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if self.wndMultiple:
				self.wndMultiple.Show(self.isOpenedMultipleWindowWhenClosingInventory)

		# 인벤토리를 닫을 때 코스츔이 열려있었다면 인벤토리를 열 때 코스츔도 같이 열도록 함.

		if app.ENABLE_GEM_SYSTEM:
			if self.wndExpandedMoneyBar:
				self.wndExpandedMoneyBar.Show()

	def BindInterfaceClass(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)
		self.SetDragonCoin(getattr(interface, "itemShopDragonCoin", 0))

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()

			if ITEM_MALL_BUTTON_ENABLE:
				pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "InventoryWindow.py")
			else:
				pyScrLoader.LoadScriptFile(self, "UIScript/InventoryWindow.py")
		except:
			import exception
			exception.Abort("InventoryWindow.LoadWindow.LoadObject")

		try:
			self.wndInventoryBody = self.GetChild("board")
			wndItem = self.GetChild("ItemSlot")
			wndEquip = self.GetChild("EquipmentSlot")
			wndCostume = self.GetChild("CostumeSlot")
			titleBar = self.GetChild("TitleBar")
			titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			self.wndMoney = self.GetChild("Money")
			self.wndMoney.SetLimitWidth(MONEY_TEXT_LIMIT_WIDTH)
			self.wndMoneySlot = self.GetChild("Money_Slot")
			if app.ENABLE_SORT_INVENTORY:
				self.sortInventoryButton = self.GetChild2("SortInventoryButton")
			self.quickBuffButton = self.GetChild2("QuickBuffButton")
			self.quickBuffSettingsButton = self.GetChild2("QuickBuffSettingsButton")

			mask1 = self.GetChild("Equipment_Base")
			# ALTHEA-641: hides the retired arrow cell unless an old item is in it.
			self.retiredArrowSlotCover = self.GetChild2("RetiredArrowSlotCover")
			mask2 = self.GetChild("Costume_Base")

			self.imageTab = []
			for i in range(2):
				self.imageTab.append(self.GetChild("Costume_Tab_%02d" % (i + 1)))

			if app.ENABLE_SEARCH_FIELD:
				self.wndEquipmentTabStrip = self.GetChild("EquipmentTabControl")

			if app.ENABLE_GEM_SYSTEM:
				self.wndMoneyIcon = self.GetChild("Money_Icon")
				self.wndMoneyIcon.Hide()
				self.wndMoneySlot.Hide()
			else:
				self.wndMoneyIcon = self.GetChild("Money_Icon")
				self.wndMoneyIcon.SetEvent(ui.__mem_func__(self.EventProgress), "mouse_over_in", 0)
				self.wndMoneyIcon.SetEvent(ui.__mem_func__(self.EventProgress), "mouse_over_out", 0)

				self.toolTip = uiToolTip.ToolTip()
				self.toolTip.ClearToolTip()

			self.inventoryTab = []
			self.inventoryTab.append(self.GetChild("Inventory_Tab_01"))
			self.inventoryTab.append(self.GetChild("Inventory_Tab_02"))
			if app.ENABLE_EXTEND_INVEN_SYSTEM:
				self.inventoryTab.append(self.GetChild("Inventory_Tab_03"))
				self.inventoryTab.append(self.GetChild("Inventory_Tab_04"))

			self.equipmentTab = []
			self.equipmentTab.append(self.GetChild("Equipment_Tab_01"))
			self.equipmentTab.append(self.GetChild("Equipment_Tab_02"))

			if app.ENABLE_HIDE_COSTUME_SYSTEM:
				self.visibleBtnList = []
				self.visibleBtnList.append(self.GetChild("BodyToolTipButton")) ## 0
				self.visibleBtnList.append(self.GetChild("HairToolTipButton")) ## 1
				self.visibleBtnList.append(self.GetChild("WeaponToolTipButton")) ## 2
				self.visibleBtnList.append(self.GetChild("AcceSkinToolTipButton")) ## 3
				self.visibleBtnList.append(self.GetChild("AcceToolTipButton")) ## 4
				self.visibleBtnList.append(self.GetChild("AuraToolTipButton")) ## 5
				if app.ENABLE_SPECIAL_SHINING_SYSTEM:
					self.visibleBtnList.append(self.GetChild("ShiningWeaponToolTipButton")) ## 6
					self.visibleBtnList.append(self.GetChild("ShiningArmorToolTipButton")) ## 7
				if app.ENABLE_MOUNT_COSTUME_SYSTEM:
					self.mountVisibilityButtonIndex = len(self.visibleBtnList)
					self.visibleBtnList.append(self.GetChild("MountToolTipButton"))

			if app.ENABLE_BRAVE_CAPE_RENEWAL:
				self.wndBraveCape = None
			self.dlgQuestion = uiCommon.QuestionDialog2()
			self.dlgQuestion.Close()

			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				self.listHighlightedAcceSlot = []

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				self.listHighlightedChangeLookSlot = []

			if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
				self.listHighlightedSlot = []

			if app.ENABLE_GROWTH_PET_SYSTEM:
				self.PetItemQuestionDlg = uiCommon.QuestionDialog()
				self.PetItemQuestionDlg.Close()

				self.PetSkillDelDlg = uiCommon.QuestionDialog2()
				self.PetSkillDelDlg.Close()
				self.PetSkillAllDelBookIndex = -1

			if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
				self.wndMultiple = None
				self.wndMultiple = MultipleInventoryWindow(self)

		except:
			import exception
			exception.Abort("InventoryWindow.LoadWindow.BindObject")

		## Item
		wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		wndItem.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndItem.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		## Equipment
		wndEquip.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		wndEquip.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		wndEquip.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndEquip.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndEquip.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndEquip.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		wndCostume.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		wndCostume.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		wndCostume.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndCostume.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndCostume.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndCostume.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		if app.ENABLE_SLOT_TOOLTIP_INFO:
			wndEquip.SetOverInEvent(ui.__mem_func__(self.OverInItem))
			wndEquip.SetOverOutEvent(ui.__mem_func__(self.OverOutItem))

			wndCostume.SetOverInEvent(ui.__mem_func__(self.OverInItem))
			wndCostume.SetOverOutEvent(ui.__mem_func__(self.OverOutItem))

		## PickMoneyDialog
		dlgPickMoney = uiPickMoney.PickMoneyDialog()
		dlgPickMoney.LoadDialog()
		dlgPickMoney.Hide()

		dlgSplitItem = uiSplitItem.SplitItemDialog()
		dlgSplitItem.LoadDialog()
		dlgSplitItem.Hide()

		if app.ENABLE_PICK_GEM_SYSTEM:
			dlgPickGem = uiPickGem.PickGemDialog()
			dlgPickGem.LoadDialog()
			dlgPickGem.Hide()
			self.dlgPickGem = dlgPickGem

		if app.ENABLE_BRAVE_CAPE_RENEWAL:
			self.disbandBtn = ui.Button()
			self.disbandBtn.SetParent(self.wndInventoryBody)
			self.disbandBtn.SetPosition(-5, 180)
			self.disbandBtn.SetUpVisual("d:/ymir work/ui/game/belt_inventory/btn_expand_normal.tga")
			self.disbandBtn.SetOverVisual("d:/ymir work/ui/game/belt_inventory/btn_expand_over.tga")
			self.disbandBtn.SetDownVisual("d:/ymir work/ui/game/belt_inventory/btn_expand_down.tga")
			self.disbandBtn.SAFE_SetEvent(self.ClickBraveCape)
			self.disbandBtn.Show()

			self.wndBraveCape = BraveCapeWindow()
			self.OnMoveWindow(*self.GetInventoryBodyGlobalPosition())

		## RefineDialog
		self.refineDialog = uiRefine.RefineDialog()
		self.refineDialog.Hide()

		## AttachMetinDialog
		self.attachMetinDialog = uiAttachMetin.AttachMetinDialog()
		self.attachMetinDialog.Hide()

		if app.ENABLE_HIDE_COSTUME_SYSTEM:
			self.visibleBtnList[0].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 1, 0)
			self.visibleBtnList[0].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 1, 1)

			self.visibleBtnList[1].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 2, 0)
			self.visibleBtnList[1].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 2, 1)

			self.visibleBtnList[2].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 3, 0)
			self.visibleBtnList[2].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 3, 1)

			self.visibleBtnList[3].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 4, 0)
			self.visibleBtnList[3].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 4, 1)

			self.visibleBtnList[4].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 5, 0)
			self.visibleBtnList[4].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 5, 1)

			self.visibleBtnList[5].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 6, 0)
			self.visibleBtnList[5].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 6, 1)

			if app.ENABLE_SPECIAL_SHINING_SYSTEM:
				self.visibleBtnList[6].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 7, 0)
				self.visibleBtnList[6].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 7, 1)

				self.visibleBtnList[7].SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 8, 0)
				self.visibleBtnList[7].SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 8, 1)

			if app.ENABLE_MOUNT_COSTUME_SYSTEM:
				mountButton = self.visibleBtnList[self.mountVisibilityButtonIndex]
				mountButton.SetToggleUpEvent(ui.__mem_func__(self.VisibleCostume), 9, 0)
				mountButton.SetToggleDownEvent(ui.__mem_func__(self.VisibleCostume), 9, 1)

		## MoneySlot
		self.wndMoneySlot.SetEvent(ui.__mem_func__(self.OpenPickMoneyDialog))

		if app.ENABLE_EXTEND_INVEN_SYSTEM:
			for inven_index in range(player.INVENTORY_PAGE_COUNT): ## 0, 1, 2, 3
				self.inventoryTab[inven_index].SetEvent(lambda arg=inven_index: self.SetInventoryPage(arg))
		else:
			self.inventoryTab[0].SetEvent(lambda arg = 0: self.SetInventoryPage(arg))
			self.inventoryTab[1].SetEvent(lambda arg = 1: self.SetInventoryPage(arg))
		self.inventoryTab[0].Down()

		self.equipmentTab[0].SetEvent(lambda arg = 0: self.SetEquipmentPage(arg))
		self.equipmentTab[1].SetEvent(lambda arg = 1: self.SetEquipmentPage(arg))
		self.equipmentTab[0].Down()
		self.equipmentTab[0].Hide()
		self.equipmentTab[1].Hide()

		for idx in range(2):
			btn = self.imageTab[idx]
			if btn:
				btn.SetEvent(ui.__mem_func__(self.__OnClickEquipmentTabButton), idx)

		if app.ENABLE_SEARCH_FIELD:
			import skill
			self._skillModuleSearch = skill

			self.wndSearchBarBase = ui.ImageBox()
			self.wndSearchBarBase.SetParent(self.GetChild("board"))
			self.wndSearchBarBase.SetPosition(10, 33)
			self.wndSearchBarBase.LoadImage(SEARCH_FIELD_UI_PATH + "search_carrier.png")
			self.wndSearchBarBase.Hide()

			self.wndNameSlot = ui.ImageBox()
			self.wndNameSlot.SetParent(self.wndSearchBarBase)
			self.wndNameSlot.SetPosition(52, 4)
			self.wndNameSlot.LoadImage(SEARCH_FIELD_UI_PATH + "search_input_normal.png")
			self.wndNameSlot.Show()

			self.btnSearchStack = ui.Button()
			self.btnSearchStack.SetParent(self.wndSearchBarBase)
			self.btnSearchStack.SetPosition(3, 4)
			self.btnSearchStack.SetUpVisual(SEARCH_FIELD_UI_PATH + "search_utility_normal.png")
			self.btnSearchStack.SetOverVisual(SEARCH_FIELD_UI_PATH + "search_utility_hover.png")
			self.btnSearchStack.SetDownVisual(SEARCH_FIELD_UI_PATH + "search_utility_pressed.png")
			self.btnSearchStack.SetDisableVisual(SEARCH_FIELD_UI_PATH + "search_utility_disabled.png")
			self.searchStackIcon = ui.ImageBox()
			self.searchStackIcon.SetParent(self.btnSearchStack)
			self.searchStackIcon.AddFlag("not_pick")
			self.searchStackIcon.SetPosition(4, 3)
			self.searchStackIcon.LoadImage(SEARCH_FIELD_UI_PATH + "icon_stack.png")
			self.searchStackIcon.Show()
			self.btnSearchStack.SetToolTipText(getattr(localeInfo, "INVENTORY_STACK_TOOLTIP", "Stack"), 0, -23)
			if app.ENABLE_SORT_INVENTORY:
				self.btnSearchStack.SetEvent(ui.__mem_func__(self.__OnSearchBarStackClick))
				self.btnSearchStack.Show()
			else:
				self.btnSearchStack.Hide()

			self.btnSearchSort = ui.Button()
			self.btnSearchSort.SetParent(self.wndSearchBarBase)
			self.btnSearchSort.SetPosition(27, 4)
			self.btnSearchSort.SetUpVisual(SEARCH_FIELD_UI_PATH + "search_utility_normal.png")
			self.btnSearchSort.SetOverVisual(SEARCH_FIELD_UI_PATH + "search_utility_hover.png")
			self.btnSearchSort.SetDownVisual(SEARCH_FIELD_UI_PATH + "search_utility_pressed.png")
			self.btnSearchSort.SetDisableVisual(SEARCH_FIELD_UI_PATH + "search_utility_disabled.png")
			self.searchSortIcon = ui.ImageBox()
			self.searchSortIcon.SetParent(self.btnSearchSort)
			self.searchSortIcon.AddFlag("not_pick")
			self.searchSortIcon.SetPosition(4, 3)
			self.searchSortIcon.LoadImage(SEARCH_FIELD_UI_PATH + "icon_sort.png")
			self.searchSortIcon.Show()
			self.btnSearchSort.SetToolTipText(uiScriptLocale.INVENTORY_ITEM_SORT_TOOLTIP, 0, -23)
			if app.ENABLE_SORT_INVENTORY:
				self.btnSearchSort.SetEvent(ui.__mem_func__(self.__OnSearchBarSortClick))
				self.btnSearchSort.Show()
			else:
				self.btnSearchSort.Hide()

			self.wndItemSRC = ui.GridSlotWindow()
			self.wndItemSRC.SetParent(self.GetChild("board"))
			_grid_y = 246 + self.INVENTORY_TAB_STRIP_HEIGHT_PY + self.INVENTORY_SEARCH_FIELD_HEIGHT_PY
			self.wndItemSRC.SetPosition(8, _grid_y)
			self.wndItemSRC.ArrangeSlot(0, 5, 9, 32, 32, 0, 0)
			self.wndItemSRC.SetSlotBaseImage(SEARCH_FIELD_UI_PATH + "item_slot.sub", 1.0, 1.0, 1.0, 1.0)
			self.wndItemSRC.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
			self.wndItemSRC.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
			self.wndItemSRC.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
			self.wndItemSRC.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
			self.wndItemSRC.SetOverInItemEvent(ui.__mem_func__(self.__OverInItemSearchResult))
			self.wndItemSRC.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			self.wndItemSRC.dictItems = {}
			self.wndItemSRC.Hide()
			self._invSearchGridAnchor = {}

			self.wndSearchEdit = ui.EditLine()
			self.wndSearchEdit.SetParent(self.wndNameSlot)
			self.wndSearchEdit.SetPosition(6, 4)
			self.wndSearchEdit.SetSize(self.wndNameSlot.GetWidth() - 2, self.wndNameSlot.GetHeight() - 2)
			self.wndSearchEdit.SetMax(55)
			self.wndSearchEdit.SetInfoMessage(localeInfo.ITEMSHOP_ITEMSEARCH_DEFAULT_TEXT)
			self.wndSearchEdit.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateSearchField)
			self.wndSearchEdit.SetEscapeEvent(ui.__mem_func__(self.__OnSearchEditEscape))
			self.wndSearchEdit.SetOnFocusEvent(ui.__mem_func__(self.__OnSearchEditFocus))
			self.wndSearchEdit.SetKillFocusEvent(ui.__mem_func__(self.__OnSearchEditBlur))
			self.wndSearchEdit.KillFocus()
			self.wndSearchEdit.Show()
			self._searchFieldBarVisible = False
		else:
			self.wndItemSRC = None
			self.wndSearchEdit = None
			self.wndSearchBarBase = None
			self.wndNameSlot = None
			self.btnSearchStack = None
			self.btnSearchSort = None
			self.searchStackIcon = None
			self.searchSortIcon = None
			self._skillModuleSearch = None
			self._invSearchGridAnchor = None
			self._searchFieldBarVisible = False

		self.wndItem = wndItem
		self.wndEquip = wndEquip
		self.wndCostume = wndCostume
		self.mask1 = mask1
		self.mask2 = mask2

		self.ExtraPageIndex = 0
		self.dlgPickMoney = dlgPickMoney
		self.dlgSplitItem = dlgSplitItem

		if app.ENABLE_SORT_INVENTORY:
			if self.sortInventoryButton:
				if app.ENABLE_SEARCH_FIELD:
					self.sortInventoryButton.SetEvent(ui.__mem_func__(self.__OnClickTitleBarSearchToggle))
					self.__UpdateTitleBarSearchToggleToolTip()
				else:
					self.sortInventoryButton.SetEvent(ui.__mem_func__(self.SortInventoryButton))
		if self.quickBuffButton:
			self.quickBuffButton.SetEvent(ui.__mem_func__(self.__ActivateQuickBuffs))
		if self.quickBuffSettingsButton:
			self.quickBuffSettingsButton.SetEvent(ui.__mem_func__(self.__OpenQuickBuffSettings))

		## Refresh
		self.SetInventoryPage(0)
		self.SetEquipmentPage(0)
		self.RefreshItemSlot()
		self.RefreshStatus()

	def Destroy(self):
		self.__ClearRefineLevelOverlays()
		self.virtualMarketDraftSlots.clear()
		self.virtualMarketDraftMouseSlots.clear()
		self.quickBuffButton = None
		self.quickBuffSettingsButton = None
		self.ClearDictionary()
		self.wndInventoryBody = None

		self.dlgPickMoney.Destroy()
		self.dlgPickMoney = 0
		self.dlgSplitItem.Destroy()
		self.dlgSplitItem = 0

		if app.ENABLE_PICK_GEM_SYSTEM:
			self.dlgPickGem.Destroy()
			self.dlgPickGem = 0

		self.refineDialog.Destroy()
		self.refineDialog = 0

		self.attachMetinDialog.Destroy()
		self.attachMetinDialog = 0

		self.tooltipItem = None
		self.wndItem = 0
		self.wndEquip = 0
		self.retiredArrowSlotCover = None
		self.wndCostume = 0
		self.dlgPickMoney = 0
		self.dlgSplitItem = 0
		if app.ENABLE_PICK_GEM_SYSTEM:
			self.dlgPickGem = 0
		self.wndMoney = 0
		self.wndMoneySlot = 0
		self.questionDialog = None
		self.wikiButton = None
		self.shopButton = None
		self.switchButton = None
		self.interface = None

		if app.ENABLE_BRAVE_CAPE_RENEWAL:
			if self.wndBraveCape:
				self.wndBraveCape.Destroy()
				self.wndBraveCape = None

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if self.wndMultiple:
				self.wndMultiple.Destroy()
				self.wndMultiple = None

		self.inventoryTab = []
		self.equipmentTab = []
		self.windowTabs = []
		self.imageTab = []

		if app.ENABLE_SEARCH_FIELD:
			self.wndItemSRC = None
			self.wndSearchEdit = None
			self.wndNameSlot = None
			self.wndSearchBarBase = None
			self.btnSearchStack = None
			self.btnSearchSort = None
			self.searchStackIcon = None
			self.searchSortIcon = None
			self._skillModuleSearch = None
			self._invSearchGridAnchor = None

		if app.ENABLE_GEM_SYSTEM:
			self.wndExpandedMoneyBar = None

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			self.listHighlightedAcceSlot = []

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if self.petHatchingWindow:
				self.petHatchingWindow = None
				
			if self.petFeedWindow:
				self.petFeedWindow = None
				
			if self.petNameChangeWindow:
				self.petNameChangeWindow = None 

	def Hide(self):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS():
			self.OnCloseQuestionDialog()
			return

		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if self.wndMultiple:
				self.isOpenedMultipleWindowWhenClosingInventory = 0
				self.wndMultiple.Close()
				
				if self.wndSpecial:
					self.wndMultiple.CloseInventory()

		if app.ENABLE_BRAVE_CAPE_RENEWAL:
			if self.wndBraveCape:
				self.wndBraveCape.Close()

		if self.dlgPickMoney:
			self.dlgPickMoney.Close()
		if self.dlgSplitItem:
			self.dlgSplitItem.Close()

		if app.ENABLE_PICK_GEM_SYSTEM:
			if self.dlgPickGem:
				self.dlgPickGem.Close()

		if app.ENABLE_GEM_SYSTEM:
			if self.wndExpandedMoneyBar:
				self.wndExpandedMoneyBar.Close()

		wndMgr.Hide(self.hWnd)

	def Close(self):
		if app.ENABLE_SEARCH_FIELD:
			if self.wndSearchEdit and self.wndSearchEdit.IsFocus():
				self.wndSearchEdit.KillFocus()
		if self.interface:
			self.interface.CloseTalismanWindow()
		self.Hide()

	def __OpenQuickBuffSettings(self):
		if self.interface:
			self.interface.OpenQuickBuffSettings()

	def __ActivateQuickBuffs(self):
		if self.interface:
			self.interface.ActivateQuickBuffs()

	def OnMouseWheel(self, nLen):
		############
		isIn = False
		if self.wndItem.IsInPosition():
			isIn = True
		elif self.inventoryTab[0].IsInPosition():
			isIn = True
		elif self.inventoryTab[1].IsInPosition():
			isIn = True
		elif self.inventoryTab[2].IsInPosition():
			isIn = True
		elif self.inventoryTab[3].IsInPosition():
			isIn = True

		#############
		isInEquip = False
		if self.mask1.IsInPosition():
			isInEquip = True
		elif self.mask2.IsInPosition():
			isInEquip = True
		else:
			for btn in self.imageTab:
				if btn and btn.IsInPosition():
					isInEquip = True
					break

		#############
		
		if isIn:
			if nLen > 0:
				# 0 | 1 | 2 | 3
				if self.inventoryPageIndex >= 3:
					self.SetInventoryPage(0)
				else:
					self.SetInventoryPage(self.inventoryPageIndex + 1)
			else:
				if self.inventoryPageIndex <= 0:
					self.SetInventoryPage(3)
				else:
					self.SetInventoryPage(self.inventoryPageIndex - 1)
			return True
		elif isInEquip:
			currentPage = self.ExtraPageIndex
			if currentPage not in (0, 1):
				currentPage = 0
			pageDelta = 1 if nLen > 0 else -1
			nextPage = (currentPage + pageDelta) % 2
			self.__OnClickEquipmentTabButton(nextPage)
			return True
			
		return False

	if app.ENABLE_GEM_SYSTEM:
		def SetExpandedMoneyBar(self, wndBar):
			self.wndExpandedMoneyBar = wndBar
			if self.wndExpandedMoneyBar:
				self.wndMoneySlot = self.wndExpandedMoneyBar.GetMoneySlot()
				self.wndGemSlot = self.wndExpandedMoneyBar.GetGemSlot()
				self.wndMoney = self.wndExpandedMoneyBar.GetMoney()
				self.wndMoneyIcon = self.wndExpandedMoneyBar.GetMoneyIcon()
				if self.wndMoneyIcon:
					self.wndMoneyIcon.SetEvent(ui.__mem_func__(self.EventProgress), "mouse_over_in", 0)
					self.wndMoneyIcon.SetEvent(ui.__mem_func__(self.EventProgress), "mouse_over_out", 0)
				self.wndGemIcon = self.wndExpandedMoneyBar.GetGemIcon()
				if self.wndGemIcon:
					self.wndGemIcon.SetEvent(ui.__mem_func__(self.EventProgress), "mouse_over_in", 1)
					self.wndGemIcon.SetEvent(ui.__mem_func__(self.EventProgress), "mouse_over_out", 1)
				self.wndGem = self.wndExpandedMoneyBar.GetGem()

				self.toolTip = uiToolTip.ToolTip()
				self.toolTip.ClearToolTip()
				if self.wndMoneySlot:
					self.wndMoneySlot.SetEvent(ui.__mem_func__(self.OpenPickMoneyDialog), 0)
				if self.wndGemSlot:
					self.wndGemSlot.SetEvent(ui.__mem_func__(self.OpenPickGemDialog), 1)

	if app.ENABLE_EXTEND_INVEN_SYSTEM:
		def SetInventoryPage(self, page):
			self.inventoryPageIndex = page

			for index in range(len(self.inventoryTab)):
				if index == page:
					self.inventoryTab[index].Down()
				else:
					# continue
					self.inventoryTab[index].SetUp()

			if app.ENABLE_SEARCH_FIELD:
				if self.wndSearchEdit and page != 0 and self.wndSearchEdit.GetText():
					self.wndSearchEdit.SetText("")
					if self.wndItemSRC:
						self.wndItemSRC.Hide()
					self.wndItem.Show()

			self.RefreshBagSlotWindow()
	else:
		def SetInventoryPage(self, page):
			self.inventoryPageIndex = page
			self.inventoryTab[1-page].SetUp()

			if app.ENABLE_SEARCH_FIELD:
				if self.wndSearchEdit and page != 0 and self.wndSearchEdit.GetText():
					self.wndSearchEdit.SetText("")
					if self.wndItemSRC:
						self.wndItemSRC.Hide()
					self.wndItem.Show()

			self.RefreshBagSlotWindow()

	if app.ENABLE_HIDE_COSTUME_SYSTEM:
		def RefreshVisibleCostume(self):
			body = osfInfo.HIDDEN_BODY_COSTUME
			self.SetHideEvent(0, body)

			hair = osfInfo.HIDDEN_HAIR_COSTUME
			self.SetHideEvent(1, hair)

			weapon = osfInfo.HIDDEN_WEAPON_COSTUME
			self.SetHideEvent(2, weapon)

			skinAcce = osfInfo.HIDDEN_ACCE_SKIN
			self.SetHideEvent(3, skinAcce)

			acce = osfInfo.HIDDEN_ACCE_COSTUME
			self.SetHideEvent(4, acce)

			aura = osfInfo.HIDDEN_AURA_COSTUME
			self.SetHideEvent(5, aura)

			if app.ENABLE_SPECIAL_SHINING_SYSTEM:
				shiningWeapon = osfInfo.HIDDEN_SHINING_WEAPON
				self.SetHideEvent(6, shiningWeapon)

				shiningArmor = osfInfo.HIDDEN_SHINING_ARMOR
				self.SetHideEvent(7, shiningArmor)

			if app.ENABLE_MOUNT_COSTUME_SYSTEM:
				self.SetHideEvent(self.mountVisibilityButtonIndex, osfInfo.HIDDEN_MOUNT)

		def SetHideEvent(self, slot, hide = False):
			if hide:
				self.visibleBtnList[slot].SetToolTipText(localeInfo.SHOW_COSTUME)
				self.visibleBtnList[slot].SetUpVisual(SEARCH_FIELD_UI_PATH + "visibility_selected.png")
				self.visibleBtnList[slot].SetOverVisual(SEARCH_FIELD_UI_PATH + "visibility_selected.png")
				self.visibleBtnList[slot].SetDownVisual(SEARCH_FIELD_UI_PATH + "visibility_selected.png")
			else:
				self.visibleBtnList[slot].SetToolTipText(localeInfo.HIDE_COSTUME)
				self.visibleBtnList[slot].SetUpVisual(SEARCH_FIELD_UI_PATH + "visibility_normal.png")
				self.visibleBtnList[slot].SetOverVisual(SEARCH_FIELD_UI_PATH + "visibility_hover.png")
				self.visibleBtnList[slot].SetDownVisual(SEARCH_FIELD_UI_PATH + "visibility_pressed.png")

		def VisibleCostume(self, part, hidden):
			net.SendChatPacket("/hide_costume %d %d" % (part, hidden))

	def __OnClickEquipmentTabButton(self, page):
		if page == 1 and self.interface and \
				self.interface.IsSeparateCostumeInventory():
			self.SetEquipmentPage(0)
			self.interface.ShowCostumeInventoryWindow()
			return
		self.SetEquipmentPage(page)

	def SetEquipmentPage(self, page):
		if page not in (0, 1):
			page = 0
		if page == 1 and self.interface and \
				self.interface.IsSeparateCostumeInventory():
			page = 0
		self.ExtraPageIndex = page
		self.mask1.Hide()
		self.mask2.Hide()
		for i in range(2):
			self.imageTab[i].SetUp()
		if page == 0:
			self.mask1.Show()
			self.imageTab[0].Down()
		else:
			self.mask2.Show()
			self.imageTab[1].Down()
		self.RefreshEquipSlotWindow()

	def ShowInventory(self):
		if self.mask1:
			if not self.mask1.IsShow():
				self.mask1.Show()
				self.SetEquipmentPage(0)
		else:
			self.mask1.Show()

	def ShowCostumeInventory(self):
		if self.mask2:
			if not self.mask2.IsShow():
				self.mask2.Show()
				self.SetEquipmentPage(1)
		else:
			self.mask2.Show()

	def ClickMallButton(self):
		if self.interface.dlgPassword.IsShow():
			self.interface.dlgPassword.CloseDialog()
		else:
			net.SendChatPacket("/click_mall")

	if app.ENABLE_SORT_INVENTORY:
		def StackInventoryButton(self):
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(getattr(localeInfo, "INVENTORY_DO_YOU_STACK", "Do you really want to stack matching inventory items?"))
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnStackInventoryItems))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
			self.questionDialog.Open()

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

		def OnStackInventoryItems(self):
			if None == self.questionDialog:
				return
			if self.virtualMarketDraftSlots:
				self.__ShowVirtualMarketDraftLocked()
				self.OnCloseQuestionDialog()
				return

			net.SendChatPacket("/stack_inventory")
			snd.PlaySound("sound/ui/pickup_item_in_inventory.wav")

			self.OnCloseQuestionDialog()

		def SortInventoryButton(self):
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(localeInfo.INVENTORY_DO_YOU_SORT)
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnSortInventoryItems))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
			self.questionDialog.Open()

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

		def OnSortInventoryItems(self):
			if None == self.questionDialog:
				return
			if self.virtualMarketDraftSlots:
				self.__ShowVirtualMarketDraftLocked()
				self.OnCloseQuestionDialog()
				return

			net.SendChatPacket("/sort_inventory")
			snd.PlaySound("sound/ui/pickup_item_in_inventory.wav")

			self.OnCloseQuestionDialog()

		def __OnSearchBarSortClick(self):
			self.SortInventoryButton()

		def __OnSearchBarStackClick(self):
			self.StackInventoryButton()

	def OpenPickMoneyDialog(self):
		if osfInfo.ENABLE_PICK_MONEY_DIALOG == False:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MONEY_PICK_DIALOG_STATE)
			return

		if mouseModule.mouseController.isAttached():

			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			if player.SLOT_TYPE_SAFEBOX == mouseModule.mouseController.GetAttachedType():
				if player.ITEM_MONEY == mouseModule.mouseController.GetAttachedItemIndex():
					net.SendSafeboxWithdrawMoneyPacket(mouseModule.mouseController.GetAttachedItemCount())
					snd.PlaySound("sound/ui/money.wav")

			mouseModule.mouseController.DeattachObject()
		else:
			curMoney = player.GetElk()

			if curMoney <= 0:
				return

			self.dlgPickMoney.SetTitleName(localeInfo.PICK_MONEY_TITLE)
			self.dlgPickMoney.SetAcceptEvent(ui.__mem_func__(self.OnPickMoney))
			self.dlgPickMoney.Open(curMoney)
			self.dlgPickMoney.SetMax(7) # 인벤토리 990000 제한 버그 수정

	def OnPickMoney(self, money):
		mouseModule.mouseController.AttachMoney(self, player.SLOT_TYPE_INVENTORY, money)

	if app.ENABLE_PICK_GEM_SYSTEM:
		def OpenPickGemDialog(self):
			if mouseModule.mouseController.isAttached():
				mouseModule.mouseController.DeattachObject()
			else:
				curGem = player.GetGem()

				if curGem <= 0:
					return

				self.dlgPickGem.SetTitleName("Gayas")
				self.dlgPickGem.SetAcceptEvent(ui.__mem_func__(self.OnPickGem))
				self.dlgPickGem.Open(curGem)
				self.dlgPickGem.SetMax(7)

		def OnPickGem(self, gem):
			mouseModule.mouseController.AttachGem(self, player.SLOT_TYPE_INVENTORY, gem)

	def OnPickItem(self, count):
		itemSlotIndex = self.dlgSplitItem.itemGlobalSlotIndex
		if self.dlgSplitItem.IsSplitAllChecked():
			self.__SplitAllItems(itemSlotIndex, count)
			return

		selectedItemVNum = player.GetItemIndex(itemSlotIndex)
		mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, itemSlotIndex, selectedItemVNum, count)

	def __SplitItemDimensionsAt(self, cell):
		itemVnum = player.GetItemIndex(cell)
		if not itemVnum:
			return None

		item.SelectItem(itemVnum)
		return item.GetItemSize()

	def __SplitAllItems(self, itemSlotIndex, splitCount):
		if self.IsVirtualMarketDraftSlot(itemSlotIndex):
			self.__ShowVirtualMarketDraftLocked()
			return
		sourceCount = player.GetItemCount(itemSlotIndex)
		itemVnum = player.GetItemIndex(itemSlotIndex)
		if not itemVnum:
			return

		item.SelectItem(itemVnum)
		itemWidth, itemHeight = item.GetItemSize()
		pageStarts = tuple(
			page * player.INVENTORY_PAGE_SIZE
			for page in range(player.INVENTORY_PAGE_COUNT)
		)
		occupied = itemsplitplanner.mark_occupied_cells(
			pageStarts, 5, player.INVENTORY_PAGE_SIZE // 5,
			self.__SplitItemDimensionsAt
		)
		moves, requiredMoves = itemsplitplanner.plan_split_moves(
			sourceCount, splitCount, itemSlotIndex, pageStarts,
			5, player.INVENTORY_PAGE_SIZE // 5,
			itemWidth, itemHeight, occupied
		)

		for destination, count in moves:
			net.SendItemMovePacket(
				player.INVENTORY, itemSlotIndex,
				player.INVENTORY, destination, count
			)

		if requiredMoves and not moves:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.INVENTORY_SPLIT_NO_SPACE)
		elif len(moves) < requiredMoves:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.INVENTORY_SPLIT_PARTIAL)

	def __InventoryLocalSlotPosToGlobalSlotPos(self, local):
		if player.IsEquipmentSlot(local) or player.IsCostumeSlot(local) or (player.IsBeltInventorySlot(local)):
			return local

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			if player.IsSkillBookInventorySlot(local) or player.IsUpgradeItemsInventorySlot(local) or player.IsStoneInventorySlot(local) or player.IsGiftBoxInventorySlot(local) or player.IsSwitchInventorySlot(local) or player.IsCostumeInventorySlot(local):
				return local

		return self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE + local

	def __HideRefineLevelOverlayGroup(self, group):
		for key, overlay in self.refineLevelOverlays.items():
			if key[0] == group:
				overlay.Hide()

	def __ClearRefineLevelOverlays(self):
		for overlay in self.refineLevelOverlays.values():
			overlay.Hide()
		self.refineLevelOverlays = {}

	def __SetRefineLevelOverlay(self, group, slotWindow, renderingSlot, itemVnum):
		key = (group, renderingSlot)
		overlay = self.refineLevelOverlays.get(key)

		if not itemVnum:
			if overlay:
				overlay.Hide()
			return

		item.SelectItem(itemVnum)
		if item.GetItemType() not in REFINE_OVERLAY_ITEM_TYPES:
			if overlay:
				overlay.Hide()
			return

		refineLevel = itemrefineoverlay.ExtractRefineLevel(item.GetItemName())
		if refineLevel is None:
			if overlay:
				overlay.Hide()
			return

		itemWidth, itemHeight = item.GetItemSize()
		slotPosition = slotWindow.GetSlotLocalPosition(renderingSlot)
		if slotPosition is None:
			if overlay:
				overlay.Hide()
			return
		slotX, slotY = slotPosition

		if not overlay:
			overlay = ui.TextLine()
			overlay.SetParent(slotWindow)
			overlay.AddFlag("not_pick")
			overlay.SetHorizontalAlignRight()
			overlay.SetOutline()
			overlay.SetPackedFontColor(0xFFFFFFFF)
			self.refineLevelOverlays[key] = overlay

		overlay.SetPosition(*itemrefineoverlay.GetOverlayPosition(
			slotX, slotY, itemWidth, itemHeight))
		overlay.SetText("+%d" % refineLevel)
		overlay.Show()

	def RefreshBagSlotWindow(self):
		if not self.wndItem:
			return
		self.__HideRefineLevelOverlayGroup("bag")

		getItemVNum = player.GetItemIndex
		getItemCount = player.GetItemCount
		setItemVNum = self.wndItem.SetItemSlot

		## 리프레쉬 하기전에 하이라이트 모두 끈다.
		for i in range(self.wndItem.GetSlotCount()):
			self.wndItem.DeactivateSlot(i)

		onTopWindow = None
		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				onTopWindow = self.interface.GetOnTopWindow()

		for i in range(player.INVENTORY_PAGE_SIZE):
			slotNumber = self.__InventoryLocalSlotPosToGlobalSlotPos(i)

			itemCount = getItemCount(slotNumber)
			# itemCount == 0이면 소켓을 비운다.
			if 0 == itemCount:
				if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
					if slotNumber in osfInfo.MULTIPLE_LIST:
						osfInfo.MULTIPLE_LIST.remove(int(slotNumber))
						if self.wndMultiple:
							self.wndMultiple.UpdateItemCount(int(slotNumber), 2)
							self.wndMultiple.UpdatePrice(int(slotNumber), 2)
				self.wndItem.ClearSlot(i)
				continue
			elif 1 == itemCount:
				itemCount = 0

			itemVnum = getItemVNum(slotNumber)
			setItemVNum(i, itemVnum, itemCount)
			itemrarityaura.ApplyInventory(self.wndItem, i, slotNumber)
			self.__SetRefineLevelOverlay("bag", self.wndItem, i, itemVnum)

			if app.ENABLE_BUFF_SYSTEM and itemVnum == osfInfo.SUPPORT_ITEM_VNUM:
				if player.GetItemMetinSocket(slotNumber, osfInfo.SUPPORT_ACTIVE_SOCKET):
					self.wndItem.ActivateSlotOld(i)

			if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
				if slotNumber in osfInfo.MULTIPLE_LIST:
					self.wndItem.ActivateSlotOld(i)
					continue

			## 자동물약 (HP: #72723 ~ #72726, SP: #72727 ~ #72730) 특수처리 - 아이템인데도 슬롯에 활성화/비활성화 표시를 위한 작업임 - [hyo]
			if constInfo.IS_AUTO_POTION(itemVnum):
				# metinSocket - [0] : 활성화 여부, [1] : 사용한 양, [2] : 최대 용량
				metinSocket = [player.GetItemMetinSocket(slotNumber, j) for j in range(player.METIN_SOCKET_MAX_NUM)]	
				tempSlotNum = slotNumber
				if tempSlotNum >= player.INVENTORY_PAGE_SIZE:
					tempSlotNum -= (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE)

				isActivated = 0 != metinSocket[0]

				if isActivated:
					self.wndItem.ActivateSlotOld(tempSlotNum)
					potionType = 0
					if constInfo.IS_AUTO_POTION_HP(itemVnum):
						potionType = player.AUTO_POTION_TYPE_HP
					elif constInfo.IS_AUTO_POTION_SP(itemVnum):
						potionType = player.AUTO_POTION_TYPE_SP

					player.SetAutoPotionInfo(potionType, player.INVENTORY, slotNumber)
				else:
					self.wndItem.DeactivateSlot(tempSlotNum)

			if app.ENABLE_GROWTH_PET_SYSTEM:
				if constInfo.IS_PET_ITEM(itemVnum):
					self.__ActivePetHighlightSlot(slotNumber)
					self.__SetCoolTimePetItemSlot(slotNumber, itemVnum)

			if app.WJ_ENABLE_TRADABLE_ICON:
				if itemVnum and self.interface and onTopWindow:
					if self.interface.MarkUnusableInvenSlotOnTopWnd(onTopWindow,slotNumber):
						self.wndItem.SetUnusableSlotOnTopWnd(i)
					else:
						self.wndItem.SetUsableSlotOnTopWnd(i)
				else:
					self.wndItem.SetUsableSlotOnTopWnd(i)

			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				AcceSlotNumberChecked = 0
				for j in range(acce.WINDOW_MAX_MATERIALS):
					(isHere, iCell) = acce.GetAttachedItem(j)

					if isHere:
						if iCell == slotNumber:
							self.wndItem.ActivateSlotOld(i)
							if not slotNumber in self.listHighlightedAcceSlot:
								self.listHighlightedAcceSlot.append(slotNumber)

							AcceSlotNumberChecked = 1
					else:
						if slotNumber in self.listHighlightedAcceSlot and not AcceSlotNumberChecked:
							self.wndItem.DeactivateSlot(i)
							self.listHighlightedAcceSlot.remove(slotNumber)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if not player.GetChangeLookVnum(player.INVENTORY, slotNumber) == 0 and itemVnum != osfInfo.SUPPORT_ITEM_VNUM:
					self.wndItem.SetSlotCoverImage(i, "icon/item/ingame_convert_Mark.tga")
				else:
					self.wndItem.EnableSlotCoverImage(i, False)

			if app.ENABLE_SOUL_SYSTEM:
				if item.IsSoulItem(itemVnum):
					metinSocket = [player.GetItemMetinSocket(slotNumber, j) for j in range(player.METIN_SOCKET_MAX_NUM)]
					tempSlotNum = slotNumber
					if tempSlotNum >= player.INVENTORY_PAGE_SIZE:
						tempSlotNum -= (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE)

					if 0 != metinSocket[1]:
						self.wndItem.ActivateSlotOld(tempSlotNum)
					else:
						self.wndItem.DeactivateSlot(tempSlotNum)

			## [MT-662] 일반펫 소환표시 마크
			if item.ITEM_TYPE_PET == item.GetItemType() and item.PET_PAY == item.GetItemSubType():
				metinSocket = [player.GetItemMetinSocket(slotNumber, j) for j in range(player.METIN_SOCKET_MAX_NUM)]
				tempSlotNum = slotNumber
				if tempSlotNum >= player.INVENTORY_PAGE_SIZE:
					tempSlotNum -= (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE)
				if 0 != metinSocket[1]:
					self.wndItem.ActivateSlotOld(tempSlotNum)
				else:
					self.wndItem.DeactivateSlot(tempSlotNum)

			if app.ENABLE_EXTENDED_BLEND_AFFECT:
				if osfInfo.IS_DEW_POTION(itemVnum) or osfInfo.IS_BLEND_POTION(itemVnum) or osfInfo.IS_EXTENDED_BLEND_POTION(itemVnum):
					metinSocket = [player.GetItemMetinSocket(slotNumber, j) for j in range(player.METIN_SOCKET_MAX_NUM)]
					tempSlotNum = slotNumber
					if tempSlotNum >= player.INVENTORY_PAGE_SIZE:
						tempSlotNum -= (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE)

					isActivated = 0 != metinSocket[3]
					if isActivated:
						self.wndItem.ActivateSlotOld(tempSlotNum)
						# Dews use the same untinted active effect as auto potions.
						if not osfInfo.IS_DEW_POTION(itemVnum):
							if osfInfo.IS_EXTENDED_BLEND_POTION(itemVnum):
								self.wndItem.SetSlotDiffuseColor(tempSlotNum, wndMgr.COLOR_TYPE_PURPLE)
							else:
								self.wndItem.SetSlotDiffuseColor(tempSlotNum, wndMgr.COLOR_TYPE_DARK_BLUE)
					else:
						self.wndItem.DeactivateSlot(tempSlotNum)

				if osfInfo.IS_EXTENDED_BLEND_POTION(itemVnum):
					self.wndItem.SetSlotCoverImage(i, "d:/ymir work/ui/acce/ingame_convert_mark_02.tga")
				elif osfInfo.IS_BLEND_POTION(itemVnum):
					self.wndItem.SetSlotCoverImage(i, "icon/item/trade.tga")
				else:
					if app.ENABLE_CHANGE_LOOK_SYSTEM:
						if not player.GetChangeLookVnum(player.INVENTORY, slotNumber):
							self.wndItem.EnableSlotCoverImage(i, False)
					else:
						self.wndItem.EnableSlotCoverImage(i, False)

		self.__RefreshVirtualMarketDraftSlots()
		self.__HighlightSlot_Refresh()
		self.wndItem.RefreshSlot()

		if app.ENABLE_SEARCH_FIELD:
			if self.wndSearchEdit and self.wndSearchEdit.GetText():
				self.__RefreshInventorySearchGrid()

	def SetVirtualMarketDraftSlot(self, slotIndex, locked):
		slotIndex = int(slotIndex)
		if locked:
			self.virtualMarketDraftSlots.add(slotIndex)
		else:
			self.virtualMarketDraftSlots.discard(slotIndex)
		self.RefreshBagSlotWindow()

	def IsVirtualMarketDraftSlot(self, slotIndex):
		try:
			return int(slotIndex) in self.virtualMarketDraftSlots
		except (TypeError, ValueError, OverflowError):
			return False

	def __ShowVirtualMarketDraftLocked(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, getattr(
			localeInfo, "VIRTUAL_MARKET_DRAFT_LOCKED",
			"This item is prepared in the virtual market."))

	def __RefreshVirtualMarketDraftSlots(self):
		visible = set()
		pageStart = self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE
		pageEnd = pageStart + player.INVENTORY_PAGE_SIZE
		for globalSlot in self.virtualMarketDraftSlots:
			if pageStart <= globalSlot < pageEnd:
				visible.add(globalSlot - pageStart)
		for localSlot in self.virtualMarketDraftMouseSlots - visible:
			self.wndItem.SetCanMouseEventSlot(localSlot)
		for localSlot in visible:
			self.wndItem.ActivateSlotOld(localSlot)
			self.wndItem.SetCantMouseEventSlot(localSlot)
		self.virtualMarketDraftMouseSlots = visible

	def RefreshCostumeSlotWindow(self, slotWindow):
		if not slotWindow:
			return

		getItemVNum = player.GetItemIndex
		getItemCount = player.GetItemCount
		for i in range(item.COSTUME_SLOT_COUNT):
			slotNumber = item.COSTUME_SLOT_START + i
			itemVnum = getItemVNum(slotNumber)
			slotWindow.SetItemSlot(slotNumber, itemVnum, 0)
			itemrarityaura.ApplyInventory(slotWindow, slotNumber, slotNumber)
			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if player.GetChangeLookVnum(
						player.EQUIPMENT, slotNumber
					) != 0 and itemVnum != osfInfo.SUPPORT_ITEM_VNUM:
					slotWindow.SetSlotCoverImage(
						slotNumber, "icon/item/ingame_convert_Mark.tga")
				else:
					slotWindow.EnableSlotCoverImage(slotNumber, False)

		if app.ENABLE_NEW_EQUIPMENT_SYSTEM:
			for i in range(player.NEW_EQUIPMENT_SLOT_COUNT):
				slotNumber = player.NEW_EQUIPMENT_SLOT_START + i
				itemCount = getItemCount(slotNumber)
				if itemCount <= 1:
					itemCount = 0
				itemVnum = getItemVNum(slotNumber)
				slotWindow.SetItemSlot(slotNumber, itemVnum, itemCount)
				itemrarityaura.ApplyInventory(slotWindow, slotNumber, slotNumber)
				if app.ENABLE_CHANGE_LOOK_SYSTEM:
					if player.GetChangeLookVnum(
							player.EQUIPMENT, slotNumber
						) != 0 and itemVnum != osfInfo.SUPPORT_ITEM_VNUM:
						slotWindow.SetSlotCoverImage(
							slotNumber,
							"icon/item/ingame_convert_Mark.tga")
					else:
						slotWindow.EnableSlotCoverImage(slotNumber, False)

		slotWindow.RefreshSlot()

	def __RefreshRetiredArrowSlot(self):
		# ALTHEA-641 virtual quiver: the arrow cell stays reserved but hidden.
		# An arrow or quiver equipped before the change keeps the cell visible
		# until the player takes it out.
		if not self.retiredArrowSlotCover:
			return
		if virtualquiver.IsArrowSlotOccupied():
			self.retiredArrowSlotCover.Hide()
		else:
			self.retiredArrowSlotCover.Show()

	def RefreshEquipSlotWindow(self):
		self.__HideRefineLevelOverlayGroup("equip")
		getItemVNum=player.GetItemIndex
		getItemCount=player.GetItemCount
		setItemVNum=self.wndEquip.SetItemSlot

		for i in range(player.EQUIPMENT_PAGE_COUNT):
			slotNumber = player.EQUIPMENT_SLOT_START + i
			itemCount = getItemCount(slotNumber)
			if itemCount <= 1:
				itemCount = 0
			itemVnum = getItemVNum(slotNumber)
			setItemVNum(slotNumber, itemVnum, itemCount)
			itemrarityaura.ApplyInventory(self.wndEquip, slotNumber, slotNumber)
			self.__SetRefineLevelOverlay("equip", self.wndEquip, slotNumber, itemVnum)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if not player.GetChangeLookVnum(player.EQUIPMENT, slotNumber) == 0 and getItemVNum(slotNumber) != osfInfo.SUPPORT_ITEM_VNUM:
					self.wndEquip.SetSlotCoverImage(slotNumber, "icon/item/ingame_convert_Mark.tga")
				else:
					self.wndEquip.EnableSlotCoverImage(slotNumber, False)

		for slotNumber in (item.EQUIPMENT_RING1, EQUIPMENT_UNIQUE3_INDEX, EQUIPMENT_UNIQUE4_INDEX):
			itemCount = getItemCount(slotNumber)
			if itemCount <= 1:
				itemCount = 0
			itemVnum = getItemVNum(slotNumber)
			setItemVNum(slotNumber, itemVnum, itemCount)
			itemrarityaura.ApplyInventory(self.wndEquip, slotNumber, slotNumber)
			self.__SetRefineLevelOverlay("equip", self.wndEquip, slotNumber, itemVnum)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if not player.GetChangeLookVnum(player.EQUIPMENT, slotNumber) == 0 and getItemVNum(slotNumber) != osfInfo.SUPPORT_ITEM_VNUM:
					self.wndEquip.SetSlotCoverImage(slotNumber, "icon/item/ingame_convert_Mark.tga")
				else:
					self.wndEquip.EnableSlotCoverImage(slotNumber, False)

		for i in range(item.COSTUME_SLOT_COUNT):
			slotNumber = item.COSTUME_SLOT_START + i
			setItemVNum(slotNumber, getItemVNum(slotNumber), 0)
			itemrarityaura.ApplyInventory(self.wndEquip, slotNumber, slotNumber)

		if app.ENABLE_NEW_EQUIPMENT_SYSTEM:
			for i in range(player.NEW_EQUIPMENT_SLOT_COUNT):
				slotNumber = player.NEW_EQUIPMENT_SLOT_START + i
				itemCount = getItemCount(slotNumber)
				if itemCount <= 1:
					itemCount = 0
				itemVnum = getItemVNum(slotNumber)
				setItemVNum(slotNumber,getItemVNum(slotNumber),itemCount)
				itemrarityaura.ApplyInventory(self.wndEquip, slotNumber, slotNumber)
				self.__SetRefineLevelOverlay("equip", self.wndEquip, slotNumber, itemVnum)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if not player.GetChangeLookVnum(player.EQUIPMENT, slotNumber) == 0 and getItemVNum(slotNumber) != osfInfo.SUPPORT_ITEM_VNUM:
					self.wndEquip.SetSlotCoverImage(slotNumber, "icon/item/ingame_convert_Mark.tga")
				else:
					self.wndEquip.EnableSlotCoverImage(slotNumber, False)

		self.__RefreshRetiredArrowSlot()
		self.wndEquip.RefreshSlot()
		self.RefreshCostumeSlotWindow(self.wndCostume)

	def RefreshItemSlot(self):
		# Native RefreshSlot emits hover-out/in even for an unrelated update.
		# Keep the hovered tooltip alive, then refresh its actual item once.
		self.refreshingItemSlots = True
		try:
			self.RefreshBagSlotWindow()
			self.RefreshEquipSlotWindow()
		finally:
			self.refreshingItemSlots = False
		slot = getattr(self, "hoveredItemSlot", None)
		if self.tooltipItem and slot is not None:
			self.tooltipItem.RefreshInventoryItem(slot)

	def SetDragonCoin(self, dragonCoin):
		try:
			self.dragonCoin = max(0, int(dragonCoin))
		except (TypeError, ValueError):
			self.dragonCoin = 0

	def RefreshStatus(self):
		money = player.GetElk()
		self.wndMoney.SetText(localeInfo.NumberToMoneyString(money))

		if app.ENABLE_GEM_SYSTEM:
			if self.wndGem:
				gem = player.GetGem()
				self.wndGem.SetText(localeInfo.NumberToMoneyString(gem))

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def RefreshCostumeSlot(self):
		for i in range(item.COSTUME_SLOT_COUNT):
			slotNumber = item.COSTUME_SLOT_START + i
			self.wndEquip.SetItemSlot(slotNumber, player.GetItemIndex(slotNumber), 0)
			itemrarityaura.ApplyInventory(self.wndEquip, slotNumber, slotNumber)

	def SellItem(self):
		if self.sellingSlotitemIndex == player.GetItemIndex(self.sellingSlotNumber):
			if self.sellingSlotitemCount == player.GetItemCount(self.sellingSlotNumber):
				## 용혼석도 팔리게 하는 기능 추가하면서 인자 type 추가
				net.SendShopSellPacketNew(self.sellingSlotNumber, self.questionDialog.count, player.INVENTORY)
				snd.PlaySound("sound/ui/money.wav")

		self.OnCloseQuestionDialog()

	def OnDetachMetinFromItem(self):
		if None == self.questionDialog:
			return

		#net.SendItemUseToItemPacket(self.questionDialog.sourcePos, self.questionDialog.targetPos)
		self.__SendUseItemToItemPacket(self.questionDialog.sourcePos, self.questionDialog.targetPos)
		self.OnCloseQuestionDialog()

	def OnCloseQuestionDialog(self):
		if not self.questionDialog:
			return

		self.questionDialog.Close()
		self.questionDialog = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def OverInItem2(self, slotIndex):
		tooltipItem = self.tooltipItem
		if tooltipItem:
			tooltipItem.ClearToolTip()
			slotNames = {
				0: [localeInfo.TOOLTIP_COSTUME_WEAPON,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
				1: [localeInfo.TOOLTIP_COSTUME_HAIR,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
				2: [localeInfo.TOOLTIP_COSTUME,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
				3: [localeInfo.TOOLTIP_COSTUME_ACCE,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
				4: [localeInfo.TOOLTIP_ARMOR_EFFECT,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
				5: [localeInfo.TOOLTIP_WEAPON_EFFECT,grp.GenerateColor(1.0, 1.0, 0.0, 1.0)],
			}
			
			if slotIndex in slotNames:
				tooltipItem.AlignHorizonalCenter()
				tooltipItem.AutoAppendNewTextLine(slotNames[slotIndex][0],slotNames[slotIndex][1])
				tooltipItem.ShowToolTip()

	## Slot Event
	def SelectEmptySlot(self, selectedSlotPos):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		if app.ENABLE_SEARCH_FIELD:
			if self.wndItemSRC and self.wndItemSRC.IsShow() and self.wndSearchEdit and self.wndSearchEdit.GetText():
				return

		if app.ENABLE_AURA_SYSTEM:
			if player.IsAuraRefineWindowOpen():
				return

		if app.ENABLE_ATTR_6TH_7TH:
			if self.interface.wndAttr67Add.IsShow():
				return

		## 악세서리 창이 열려있으면
		## 아이템 이동 금지.
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if player.GetAcceRefineWindowOpen() == 1:
				return

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if player.GetChangeLookWindowOpen() == 1:
				return

		selectedSlotPos = self.__InventoryLocalSlotPosToGlobalSlotPos(selectedSlotPos)

		if mouseModule.mouseController.isAttached():

			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedItemCount = mouseModule.mouseController.GetAttachedItemCount()
			attachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()

			if player.SLOT_TYPE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_STONE_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_SWITCH_INVENTORY == attachedSlotType or\
				player.SLOT_TYPE_COSTUME_INVENTORY == attachedSlotType:

				if attachedSlotPos >= player.DRAGON_SOUL_EQUIPMENT_SLOT_START and attachedSlotPos < player.DRAGON_SOUL_EQUIPMENT_SLOT_END:
					mouseModule.mouseController.DeattachObject()
					return

				if app.ENABLE_PICK_GEM_SYSTEM:
					if -2 == attachedItemIndex:
						if attachedItemCount <= 2000:
							self.__SendMoveItemPacket(65535-1, selectedSlotPos, attachedItemCount)
						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GEM_SPLIT_COUNT)
							mouseModule.mouseController.DeattachObject()
							return
					else:
						self.__SendMoveItemPacket(attachedSlotPos, selectedSlotPos, attachedItemCount)
				else:
						self.__SendMoveItemPacket(attachedSlotPos, selectedSlotPos, attachedItemCount)

				if item.IsRefineScroll(attachedItemIndex):
					self.interface.SetUseItemMode(False)

			elif app.ENABLE_SWITCHBOT_SYSTEM and player.SLOT_TYPE_SWITCHBOT == attachedSlotType:
				attachedCount = mouseModule.mouseController.GetAttachedItemCount()
				net.SendItemMovePacket(player.SWITCHBOT, attachedSlotPos, player.INVENTORY, selectedSlotPos, attachedCount)

			elif player.SLOT_TYPE_QUICK_EQUIP == attachedSlotType:
				net.SendItemMovePacket(player.QUICK_EQUIP, attachedSlotPos,
					player.INVENTORY, selectedSlotPos, attachedItemCount)

			elif player.SLOT_TYPE_PRIVATE_SHOP == attachedSlotType:
				mouseModule.mouseController.RunCallBack("INVENTORY")

			elif player.SLOT_TYPE_SHOP == attachedSlotType:
				net.SendShopBuyPacket(attachedSlotPos)

			elif player.SLOT_TYPE_SAFEBOX == attachedSlotType:
				if player.ITEM_MONEY == attachedItemIndex:
					net.SendSafeboxWithdrawMoneyPacket(mouseModule.mouseController.GetAttachedItemCount())
					snd.PlaySound("sound/ui/money.wav")
				else:
					net.SendSafeboxCheckoutPacket(attachedSlotPos, selectedSlotPos)

			elif player.SLOT_TYPE_MALL == attachedSlotType:
				net.SendMallCheckoutPacket(attachedSlotPos, selectedSlotPos)

			elif app.ENABLE_AURA_SYSTEM and player.SLOT_TYPE_AURA == attachedSlotType:
				net.SendAuraRefineCheckOut(attachedSlotPos, player.GetAuraRefineWindowType())

			elif player.SLOT_TYPE_OFFLINE_SHOP == attachedSlotType and app.ENABLE_OFFLINE_SHOP:
				mouseModule.mouseController.GetAttachedOwner().OnClickItemSlot(attachedSlotPos, selectedSlotPos)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if player.SLOT_TYPE_CHANGE_LOOK == attachedSlotType:
					pass

			mouseModule.mouseController.DeattachObject()

	def __OnSearchEditEscape(self):
		self.Close()
		return True

	def __OnSearchEditFocus(self):
		if self.wndNameSlot:
			self.wndNameSlot.LoadImage(SEARCH_FIELD_UI_PATH + "search_input_focused.png")

	def __OnSearchEditBlur(self):
		if self.wndNameSlot:
			self.wndNameSlot.LoadImage(SEARCH_FIELD_UI_PATH + "search_input_normal.png")

	def __OnClickTitleBarSearchToggle(self):
		self.__ToggleSearchFieldBar()

	def __ToggleSearchFieldBar(self):
		if not self.wndSearchBarBase:
			return
		tabStrip = self.wndEquipmentTabStrip
		self._searchFieldBarVisible = not self._searchFieldBarVisible
		if self._searchFieldBarVisible:
			if tabStrip:
				tabStrip.Hide()
			self.wndSearchBarBase.Show()
		else:
			self.wndSearchBarBase.Hide()
			if self.wndSearchEdit:
				self.wndSearchEdit.KillFocus()
				self.wndSearchEdit.SetText("")
			self.__RefreshInventorySearchGrid()
			if tabStrip:
				tabStrip.Show()
				self.SetEquipmentPage(self.ExtraPageIndex)
		self.__UpdateTitleBarSearchToggleToolTip()

	def __UpdateTitleBarSearchToggleToolTip(self):
		if not self.sortInventoryButton:
			return
		if self._searchFieldBarVisible:
			self.sortInventoryButton.SetToolTipText(localeInfo.INVENTORY_SEARCH_BAR_HIDE_TOOLTIP, 0, -23)
		else:
			self.sortInventoryButton.SetToolTipText(localeInfo.INVENTORY_SEARCH_BAR_SHOW_TOOLTIP, 0, -23)

	def __OnValueUpdateSearchField(self):
		if not self.wndSearchEdit:
			return
		if not self.IsShow():
			return
		if self.wndSearchEdit.IsFocus():
			ui.EditLine.OnIMEUpdate(self.wndSearchEdit)
		self.__RefreshInventorySearchGrid()

	def __ClearInventorySearchGrid(self):
		if not self.wndItemSRC:
			return
		self.__HideRefineLevelOverlayGroup("search")
		for x in range(5 * 9):
			self.wndItemSRC.ClearSlot(x)
		self.wndItemSRC.RefreshSlot()
		self._invSearchGridAnchor = {}

	def __InventorySearchCanPlace(self, top_left, width, height, used_cells):
		col = top_left % 5
		row = top_left // 5
		if col + width > 5 or row + height > 9:
			return False
		for dy in range(height):
			for dx in range(width):
				idx = (row + dy) * 5 + (col + dx)
				if idx in used_cells:
					return False
		return True

	def __InventorySearchMarkArea(self, top_left, width, height, used_cells, anchor_key):
		col = top_left % 5
		row = top_left // 5
		for dy in range(height):
			for dx in range(width):
				idx = (row + dy) * 5 + (col + dx)
				used_cells.add(idx)
				self._invSearchGridAnchor[idx] = anchor_key

	def __InventorySearchFindEmpty(self, width, height, used_cells):
		for pos in range(5 * 9):
			if self.__InventorySearchCanPlace(pos, width, height, used_cells):
				return pos
		return -1

	def __InventorySearchResolveAnchor(self, grid_slot_index):
		m = self._invSearchGridAnchor
		if m == None:
			return grid_slot_index
		return m.get(grid_slot_index, grid_slot_index)

	def __RefreshInventorySearchGrid(self):
		if not self.wndItemSRC or not self.wndSearchEdit or not self._skillModuleSearch:
			return
		text = self.wndSearchEdit.GetText().strip()
		self.wndItemSRC.dictItems = {}
		self.__ClearInventorySearchGrid()
		if not text:
			self.wndItemSRC.Hide()
			self.wndItem.Show()
			return
		if self.inventoryPageIndex != 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.INVENTORY_SEARCH_USE_FIRST_PAGE)
			self.wndSearchEdit.SetText("")
			self.wndItemSRC.Hide()
			self.wndItem.Show()
			return
		self.wndItemSRC.Show()
		self.wndItem.Hide()
		skill = self._skillModuleSearch
		query_lower = text.lower()
		used_cells = set()
		for i in range(player.INVENTORY_PAGE_COUNT * player.INVENTORY_PAGE_SIZE):
			itemCount = player.GetItemCount(i)
			if itemCount == 0:
				continue
			elif 1 == itemCount:
				itemCount = 0
			itemVNum = player.GetItemIndex(i)
			item.SelectItem(itemVNum)
			stName = item.GetItemName()
			if itemVNum == 50300:
				stName = skill.GetSkillName(player.GetItemMetinSocket(i, 0))
			w, h = item.GetItemSize()
			if w <= 0 or h <= 0:
				continue
			if query_lower not in stName.lower():
				continue
			dest = self.__InventorySearchFindEmpty(w, h, used_cells)
			if dest == -1:
				break
			self.__InventorySearchMarkArea(dest, w, h, used_cells, dest)
			self.wndItemSRC.SetItemSlot(dest, itemVNum, itemCount)
			itemrarityaura.ApplyInventory(self.wndItemSRC, dest, i)
			self.__SetRefineLevelOverlay("search", self.wndItemSRC, dest, itemVNum)
			if app.ENABLE_BUFF_SYSTEM and itemVNum == osfInfo.SUPPORT_ITEM_VNUM:
				if player.GetItemMetinSocket(i, osfInfo.SUPPORT_ACTIVE_SOCKET):
					self.wndItemSRC.ActivateSlotOld(dest)
			if app.ENABLE_EXTENDED_BLEND_AFFECT and osfInfo.IS_DEW_POTION(itemVNum):
				if player.GetItemMetinSocket(i, 3):
					self.wndItemSRC.ActivateSlotOld(dest)
			self.wndItemSRC.dictItems[dest] = (player.INVENTORY, i)
		self.wndItemSRC.RefreshSlot()

	def __OverInItemSearchResult(self, slotIndex):
		if self.wndItemSRC:
			anchor = self.__InventorySearchResolveAnchor(slotIndex)
			if anchor in self.wndItemSRC.dictItems:
				self.ShowToolTip(self.wndItemSRC.dictItems[anchor][1])
				return
		self.OverOutItem()

	def SelectItemSlot(self, itemSlotIndex):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		if app.ENABLE_SEARCH_FIELD:
			if self.wndItemSRC and self.wndItemSRC.IsShow() and self.wndSearchEdit and self.wndSearchEdit.GetText():
				anchor = self.__InventorySearchResolveAnchor(itemSlotIndex)
				if anchor in self.wndItemSRC.dictItems:
					itemSlotIndex = self.wndItemSRC.dictItems[anchor][1]
				else:
					itemSlotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(itemSlotIndex)
			else:
				itemSlotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(itemSlotIndex)
		else:
			itemSlotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(itemSlotIndex)

		if self.IsVirtualMarketDraftSlot(itemSlotIndex):
			self.__ShowVirtualMarketDraftLocked()
			return

		isAltPressed = app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT)
		isShiftPressed = app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT)
		isCtrlPressed = app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)
		leftClickAction = inventoryshortcutpolicy.ResolveLeftClick(
			isAltPressed, isShiftPressed, isCtrlPressed
		)

		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedItemVID = mouseModule.mouseController.GetAttachedItemIndex()

			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if player.SLOT_TYPE_INVENTORY == attachedSlotType or\
					player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedSlotType or\
					player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedSlotType or\
					player.SLOT_TYPE_STONE_INVENTORY == attachedSlotType or\
					player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedSlotType or\
					player.SLOT_TYPE_SWITCH_INVENTORY == attachedSlotType or\
					player.SLOT_TYPE_COSTUME_INVENTORY == attachedSlotType:

					self.__DropSrcItemToDestItemInInventory(attachedItemVID, attachedSlotPos, itemSlotIndex)
			else:
				if player.SLOT_TYPE_INVENTORY == attachedSlotType:
					self.__DropSrcItemToDestItemInInventory(attachedItemVID, attachedSlotPos, itemSlotIndex)

			mouseModule.mouseController.DeattachObject()
		else:
			curCursorNum = app.GetCursor()

			if app.SELL == curCursorNum:
				self.__SellItem(itemSlotIndex)

			elif app.BUY == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_BUY_INFO)

			elif leftClickAction == inventoryshortcutpolicy.ACTION_STACK:
				if self.IsVirtualMarketDraftSlot(itemSlotIndex):
					self.__ShowVirtualMarketDraftLocked()
				else:
					net.SendChatPacket("/stack_inventory %d" % itemSlotIndex)
				return

			elif leftClickAction == inventoryshortcutpolicy.ACTION_LINK:
				if app.ENABLE_REFINE_ELEMENT_SYSTEM:
					link = constInfo.GetItemLinkEx(itemSlotIndex)
				else:
					link = player.GetItemLink(itemSlotIndex)
				ime.PasteString(link)

			elif leftClickAction == inventoryshortcutpolicy.ACTION_SPLIT:
				selectedVnum = player.GetItemIndex(itemSlotIndex)
				item.SelectItem(selectedVnum)
				if app.ENABLE_BUFF_SYSTEM:
					if item.GetItemType() == item.ITEM_SHAMAN:
						self.interface.OpenSupportGui(True)
						return
				if app.ENABLE_GROWTH_PET_SYSTEM:
					if item.GetItemType() == item.ITEM_TYPE_PET and item.GetItemSubType() == item.PET_UPBRINGING:
						self.interface.TogglePetInformationWindow()
						return

				itemCount = player.GetItemCount(itemSlotIndex)

				if itemCount > 1:
					self.dlgSplitItem.SetTitleName(localeInfo.PICK_ITEM_TITLE)
					self.dlgSplitItem.SetAcceptEvent(ui.__mem_func__(self.OnPickItem))
					self.dlgSplitItem.Open(itemCount)
					self.dlgSplitItem.itemGlobalSlotIndex = itemSlotIndex

			elif leftClickAction == inventoryshortcutpolicy.ACTION_MARKET:
				itemVnum = player.GetItemIndex(itemSlotIndex)
				if itemVnum > 0 and getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
					self.interface.SearchVirtualMarketInventoryItem(itemVnum)
				return

			else:
				selectedItemVNum = player.GetItemIndex(itemSlotIndex)
				itemCount = player.GetItemCount(itemSlotIndex)

				if app.ENABLE_GROWTH_PET_SYSTEM:
					if self.__CanAttachGrowthPetItem(selectedItemVNum, itemSlotIndex):
						mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, itemSlotIndex, selectedItemVNum, itemCount)
				else:
					mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, itemSlotIndex, selectedItemVNum, itemCount)

				if self.__IsUsableItemToItem(selectedItemVNum, itemSlotIndex):
					self.interface.SetUseItemMode(True)
				else:
					self.interface.SetUseItemMode(False)

				snd.PlaySound("sound/ui/pick.wav")

	def __DropSrcItemToDestItemInInventory(self, srcItemVID, srcItemSlotPos, dstItemSlotPos):
		if srcItemSlotPos == dstItemSlotPos:
			return

		if app.ENABLE_AURA_SYSTEM and player.IsAuraRefineWindowOpen():
			return

		if app.ENABLE_ATTR_6TH_7TH:
			if self.interface.wndAttr67Add.IsShow():
				return

		## 악세서리 창이 열려있으면
		## 아이템 이동 금지.
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if player.GetAcceRefineWindowOpen() == 1:
				return

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if player.GetChangeLookWindowOpen() == 1:
				return

		if srcItemVID in (61021, 61022):
			if not player.IsEquipmentSlot(dstItemSlotPos) and player.GetItemIndex(dstItemSlotPos) == 61020:
				self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)
			return

		if (getattr(net, "IsResonanceAvailable", lambda: False)()
				and uiresonance.IsResonanceKey(srcItemVID)
				and uiresonance.IsSupportedHostVnum(player.GetItemIndex(dstItemSlotPos))):
			if self.interface:
				self.interface.OpenResonanceUnlockDialog(
					dstItemSlotPos, srcItemSlotPos
				)
				self.interface.SetUseItemMode(False)
			return

		if (getattr(net, "IsResonanceAvailable", lambda: False)()
				and uiresonance.IsSealVnum(srcItemVID)
				and uiresonance.IsSupportedHostVnum(player.GetItemIndex(dstItemSlotPos))):
			if self.interface:
				self.interface.InsertResonanceSealDirect(
					dstItemSlotPos, srcItemSlotPos
				)
			return

		## [MT-462]
		player.GetItemIndex(srcItemSlotPos)
		if player.GetItemIndex(srcItemSlotPos) == player.GetItemIndex(dstItemSlotPos) \
			and (player.GetItemFlags(srcItemSlotPos) & item.ITEM_FLAG_STACKABLE) \
			and player.IsEquipmentSlot(dstItemSlotPos) == False:
			self.__SendMoveItemPacket(srcItemSlotPos, dstItemSlotPos, 0)
			return

		if srcItemVID in WEAPON_ENHANCEMENT_TARGETS:
			resultVnum = WEAPON_ENHANCEMENT_TARGETS[srcItemVID].get(player.GetItemIndex(dstItemSlotPos), 0)
			if resultVnum:
				self.refineDialog.OpenWeaponEnhancement(srcItemSlotPos, dstItemSlotPos, resultVnum)
				if self.interface:
					self.interface.SetUseItemMode(False)
			return

		if srcItemVID in (RARITY_SCROLL_VNUM, RARITY_REROLL_VNUM, RARITY_TARGETED_VNUM):
			self.interface.OpenRarityDialog(srcItemVID, dstItemSlotPos)
			self.interface.SetUseItemMode(False)
			return

		if app.ENABLE_SOUL_BIND_SYSTEM:
			# cyh itemseal 2013 11 08
			if item.IsSealScroll(srcItemVID):
				if player.CanSealItem(srcItemVID, player.INVENTORY, dstItemSlotPos):
					self.__OpenQuestionDialog(srcItemSlotPos, dstItemSlotPos)

		if item.IsRefineScroll(srcItemVID):
			self.RefineItem(srcItemSlotPos, dstItemSlotPos)
			self.interface.SetUseItemMode(False)

		#elif item.IsMetin(srcItemVID):
			#self.AttachMetinToItem(srcItemSlotPos, dstItemSlotPos)
		#Fix: Spirit stones - stacking.
		elif item.IsMetin(srcItemVID) and not item.IsMetin(player.GetItemIndex(dstItemSlotPos)):
			self.AttachMetinToItem(srcItemSlotPos, dstItemSlotPos)

		elif item.IsDetachScroll(srcItemVID):
			self.DetachMetinFromItem(srcItemSlotPos, dstItemSlotPos)

		elif item.IsKey(srcItemVID):
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		elif (player.GetItemFlags(srcItemSlotPos) & ITEM_FLAG_APPLICABLE) == ITEM_FLAG_APPLICABLE:
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		elif item.GetUseType(srcItemVID) in self.USE_TYPE_TUPLE:
			if app.ENABLE_REFINE_ELEMENT_SYSTEM:
				useType = item.GetUseType(srcItemVID)
				if "USE_ELEMENT_UPGRADE" == useType:
					if not uiRefine.RefineElementDialog.CanRefineElementUpgrade(player.INVENTORY, srcItemSlotPos, player.INVENTORY, dstItemSlotPos, True, False):
						return
				elif "USE_ELEMENT_DOWNGRADE" == useType:
					if not uiRefine.RefineElementDialog.CanRefineElementDowngrade(player.INVENTORY, srcItemSlotPos, player.INVENTORY, dstItemSlotPos, True, False):
						return
				elif "USE_ELEMENT_CHANGE" == useType:
					if not uiRefine.RefineElementChangeDialog.CanRefineElementChange(player.INVENTORY, srcItemSlotPos, player.INVENTORY, dstItemSlotPos, True, False):
						return
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		elif app.ENABLE_PERMA_ACCESSORY and item.GetUseType(srcItemVID) == "USE_REMOVE_PERMANENT_ORE":
			if not self.__CanRemovePermanentOre(dstItemSlotPos):
				return
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)


		elif app.ENABLE_67TH_BONUS and (srcItemVID == item.ADD_RARE_ATTRIBUTE_VNUM or srcItemVID == item.CHANGE_RARE_ATTRIBUTE_VNUM):
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		elif app.ENABLE_AURA_SYSTEM and (srcItemVID == 49980 or srcItemVID == 49970):
			self.__SendUseItemToItemPacket(srcItemSlotPos, dstItemSlotPos)

		else:
			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if item.IsChangeLookClearScroll(srcItemVID):
					if dstItemSlotPos > player.EQUIPMENT_SLOT_START - 1:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHANGE_LOOK_DO_NOT_EQUIP_ITEM)
						return

					if player.CanChangeLookClearItem(srcItemVID, player.INVENTORY, dstItemSlotPos):
						self.__OpenQuestionDialog(srcItemSlotPos, dstItemSlotPos)
						return

			if app.ENABLE_GROWTH_PET_SYSTEM:
				if self.__IsPetItem(srcItemVID):
					if self.__SendUsePetItemToItemPacket(srcItemVID, srcItemSlotPos, dstItemSlotPos):
						return

			## 이동시킨 곳이 장착 슬롯일 경우 아이템을 사용해서 장착 시킨다 - [levites]
			if player.IsEquipmentSlot(dstItemSlotPos):

				## 들고 있는 아이템이 장비일때만
				if item.IsEquipmentVID(srcItemVID):
					self.__UseItem(srcItemSlotPos)
			else:
				self.__SendMoveItemPacket(srcItemSlotPos, dstItemSlotPos, 0)
				# net.SendItemMovePacket(srcItemSlotPos, dstItemSlotPos, 0)

	def __OpenQuestionDialog(self, srcItemPos, dstItemPos):
		if self.interface.IsShowDlgQuestionWindow():
			self.interface.CloseDlgQuestionWindow()

		getItemVNum = player.GetItemIndex(dstItemPos)

		self.srcItemPos = srcItemPos
		self.dstItemPos = dstItemPos

		self.dlgQuestion.SetAcceptEvent(ui.__mem_func__(self.__Accept))
		self.dlgQuestion.SetCancelEvent(ui.__mem_func__(self.__Cancel))

		self.dlgQuestion.SetText1("%s" % item.GetItemNameByVnum(getItemVNum))
		self.dlgQuestion.SetText2(localeInfo.INVENTORY_REALLY_USE_ITEM)

		self.dlgQuestion.Open()

	def __Accept(self):
		self.dlgQuestion.Close()
		self.__SendUseItemToItemPacket(self.srcItemPos, self.dstItemPos)
		self.srcItemPos = (0, 0)
		self.dstItemPos = (0, 0)

	def __Cancel(self):
		self.srcItemPos = (0, 0)
		self.dstItemPos = (0, 0)
		self.dlgQuestion.Close()

	def __SellItem(self, itemSlotPos):
		if not player.IsEquipmentSlot(itemSlotPos):
			self.sellingSlotNumber = itemSlotPos
			itemIndex = player.GetItemIndex(itemSlotPos)
			itemCount = player.GetItemCount(itemSlotPos)

			self.sellingSlotitemIndex = itemIndex
			self.sellingSlotitemCount = itemCount

			item.SelectItem(itemIndex)
			## 안티 플레그 검사 빠져서 추가
			## 20140220
			if item.IsAntiFlag(item.ANTIFLAG_SELL):
				popup = uiCommon.PopupDialog()
				popup.SetText(localeInfo.SHOP_CANNOT_SELL_ITEM)
				popup.SetAcceptEvent(self.__OnClosePopupDialog)
				popup.Open()
				self.popup = popup
				return

			itemPrice = item.GetISellItemPrice()

			if item.Is1GoldItem():
				itemPrice = itemCount // itemPrice // 5
			else:
				itemPrice = itemPrice * itemCount // 5

			item.GetItemName(itemIndex)
			itemName = item.GetItemName()

			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(localeInfo.DO_YOU_SELL_ITEM(itemName, itemCount, itemPrice))
			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.SellItem))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
			self.questionDialog.Open()
			self.questionDialog.count = itemCount

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

	def __OnClosePopupDialog(self):
		self.pop = None

	def RefineItem(self, scrollSlotPos, targetSlotPos):
		scrollIndex = player.GetItemIndex(scrollSlotPos)
		targetIndex = player.GetItemIndex(targetSlotPos)

		# The server refuses these talisman refines without a message.
		talismanRejection = talismanrefine.RefineRejectionKey(scrollIndex, targetIndex)
		if talismanRejection:
			chat.AppendChat(chat.CHAT_TYPE_INFO, getattr(localeInfo, talismanRejection, ""))
			return

		if player.REFINE_OK != player.CanRefine(scrollIndex, targetSlotPos):
			return

		if app.ENABLE_AUTO_REFINE:
			osfInfo.AUTO_REFINE_TYPE = 1
			osfInfo.AUTO_REFINE_DATA["ITEM"][0] = scrollSlotPos
			osfInfo.AUTO_REFINE_DATA["ITEM"][1] = targetSlotPos

		###########################################################
		self.__SendUseItemToItemPacket(scrollSlotPos, targetSlotPos)
		#net.SendItemUseToItemPacket(scrollSlotPos, targetSlotPos)
		return
		###########################################################

		###########################################################
		#net.SendRequestRefineInfoPacket(targetSlotPos)
		#return
		###########################################################

		result = player.CanRefine(scrollIndex, targetSlotPos)

		if player.REFINE_ALREADY_MAX_SOCKET_COUNT == result:
			#snd.PlaySound("sound/ui/jaeryun_fail.wav")
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_NO_MORE_SOCKET)

		elif player.REFINE_NEED_MORE_GOOD_SCROLL == result:
			#snd.PlaySound("sound/ui/jaeryun_fail.wav")
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_NEED_BETTER_SCROLL)

		elif player.REFINE_CANT_MAKE_SOCKET_ITEM == result:
			#snd.PlaySound("sound/ui/jaeryun_fail.wav")
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_SOCKET_DISABLE_ITEM)

		elif player.REFINE_NOT_NEXT_GRADE_ITEM == result:
			#snd.PlaySound("sound/ui/jaeryun_fail.wav")
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_UPGRADE_DISABLE_ITEM)

		elif player.REFINE_CANT_REFINE_METIN_TO_EQUIPMENT == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_EQUIP_ITEM)

		if player.REFINE_OK != result:
			return

		self.refineDialog.Open(scrollSlotPos, targetSlotPos)

	def DetachMetinFromItem(self, scrollSlotPos, targetSlotPos):
		scrollIndex = player.GetItemIndex(scrollSlotPos)
		targetIndex = player.GetItemIndex(targetSlotPos)

		if scrollIndex == 71109:
			if player.CanDetach(scrollIndex, targetSlotPos):
				self.__OpenQuestionDialog(scrollSlotPos, targetSlotPos)
			return

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if not player.CanDetach(scrollIndex, targetSlotPos):
				item.SelectItem(scrollIndex)
				if acce.IsCleanScroll(scrollIndex):
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_FAILURE_CLEAN)
				else:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_METIN_INSEPARABLE_ITEM)

				return
		else:
			if not player.CanDetach(scrollIndex, targetSlotPos):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_METIN_INSEPARABLE_ITEM)
				return

		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetText(localeInfo.REFINE_DO_YOU_SEPARATE_METIN)
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			item.SelectItem(targetIndex)
			if item.GetItemType() == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == item.COSTUME_TYPE_ACCE:
				item.SelectItem(scrollIndex)
				if acce.IsCleanScroll(scrollIndex):
					self.questionDialog.SetText(localeInfo.ACCE_DO_YOU_CLEAN)

		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnDetachMetinFromItem))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
		self.questionDialog.Open()
		self.questionDialog.sourcePos = scrollSlotPos
		self.questionDialog.targetPos = targetSlotPos

	def AttachMetinToItem(self, metinSlotPos, targetSlotPos):
		metinIndex = player.GetItemIndex(metinSlotPos)
		targetIndex = player.GetItemIndex(targetSlotPos)

		item.SelectItem(metinIndex)
		itemName = item.GetItemName()

		result = player.CanAttachMetin(metinIndex, targetSlotPos)

		if player.ATTACH_METIN_NOT_MATCHABLE_ITEM == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_CAN_NOT_ATTACH % (itemName))

		if player.ATTACH_METIN_NO_MATCHABLE_SOCKET == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_NO_SOCKET(itemName))

		elif player.ATTACH_METIN_NOT_EXIST_GOLD_SOCKET == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_NO_GOLD_SOCKET(itemName))

		elif player.ATTACH_METIN_CANT_ATTACH_TO_EQUIPMENT == result:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_FAILURE_EQUIP_ITEM)

		if player.ATTACH_METIN_OK != result:
			return

		self.attachMetinDialog.Open(metinSlotPos, targetSlotPos)

	def OverOutItem(self):
		if getattr(self, "refreshingItemSlots", False):
			return
		self.hoveredItemSlot = None
		self.wndItem.SetUsableItem(False)
		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OverInItem(self, overSlotPos):
		overInvenSlotPos = self.__InventoryLocalSlotPosToGlobalSlotPos(overSlotPos)
		self.wndItem.SetUsableItem(False)

		getItemVNum = player.GetItemIndex
		itemVnum = getItemVNum(overInvenSlotPos)
		if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
			self.DelHighlightSlot(overInvenSlotPos)

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if self.wndMultiple.IsShow() and app.IsPressed(app.DIK_LCONTROL) and self.wndItem and self.wndItem.IsLeftMouseClicked():
				if not player.IsEquipmentSlot(overInvenSlotPos):
					if osfInfo.MULTIPLE_MODE == osfInfo.MULTIPLE_MODE_ADD:
						self.AddToMultipleList(overInvenSlotPos, False, False)
					elif osfInfo.MULTIPLE_MODE == osfInfo.MULTIPLE_MODE_DELETE:
						self.RemoveFromMultipleList(overInvenSlotPos)

		if mouseModule.mouseController.isAttached():
			attachedItemType = mouseModule.mouseController.GetAttachedType()
			if player.SLOT_TYPE_INVENTORY == attachedItemType or\
				player.SLOT_TYPE_SKILL_BOOK_INVENTORY == attachedItemType or\
				player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY == attachedItemType or\
				player.SLOT_TYPE_STONE_INVENTORY == attachedItemType or\
				player.SLOT_TYPE_GIFT_BOX_INVENTORY == attachedItemType or\
				player.SLOT_TYPE_SWITCH_INVENTORY == attachedItemType or\
				player.SLOT_TYPE_COSTUME_INVENTORY == attachedItemType and app.ENABLE_SPECIAL_INVENTORY_SYSTEM:

				attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
				attachedItemVNum = mouseModule.mouseController.GetAttachedItemIndex()

				if self.__CanUseSrcItemToDstItem(attachedItemVNum, attachedSlotPos, overInvenSlotPos):
					self.wndItem.SetUsableItem(True)
					self.ShowToolTip(overInvenSlotPos)
					return

		self.ShowToolTip(overInvenSlotPos)

	def __IsUsableItemToItem(self, srcItemVNum, srcSlotPos):
		if srcItemVNum in (61021, 61022):
			return True
		# 다른 아이템에 사용할 수 있는 아이템인가?

		if (getattr(net, "IsResonanceAvailable", lambda: False)()
				and uiresonance.IsResonanceKey(srcItemVNum)):
			return True
		elif srcItemVNum in (RARITY_SCROLL_VNUM, RARITY_REROLL_VNUM, RARITY_TARGETED_VNUM):
			return True
		elif item.IsRefineScroll(srcItemVNum):
			return True
		elif app.ENABLE_SOUL_BIND_SYSTEM and item.IsSealScroll(srcItemVNum):
			return True
		elif app.ENABLE_67TH_BONUS and (srcItemVNum == item.ADD_RARE_ATTRIBUTE_VNUM or srcItemVNum == item.CHANGE_RARE_ATTRIBUTE_VNUM):
			return True
		elif app.ENABLE_AURA_SYSTEM and (srcItemVNum == 49980 or srcItemVNum == 49970):
			return True
		elif item.IsMetin(srcItemVNum):
			return True
		elif item.IsDetachScroll(srcItemVNum):
			return True
		elif item.IsKey(srcItemVNum):
			return True
		elif item.IsItemUsedForDragonSoul(srcItemVNum):
			return True
		elif (player.GetItemFlags(srcSlotPos) & ITEM_FLAG_APPLICABLE) == ITEM_FLAG_APPLICABLE:
			return True
		elif app.ENABLE_CHANGE_LOOK_SYSTEM and item.IsChangeLookClearScroll(srcItemVNum):
			return True
		elif app.ENABLE_GROWTH_PET_SYSTEM and self.__IsUsablePetItem(srcItemVNum):
			return True
		else:
			if item.GetUseType(srcItemVNum) in self.USE_TYPE_TUPLE:
				return True

		return False

	def __CanUseSrcItemToDstItem(self, srcItemVNum, srcSlotPos, dstSlotPos):
		if srcItemVNum in (61021, 61022):
			return (srcSlotPos != dstSlotPos and not player.IsEquipmentSlot(dstSlotPos)
				and player.GetItemIndex(dstSlotPos) == 61020)
		if srcItemVNum == 79850:
			return (not player.IsEquipmentSlot(dstSlotPos)
				and 10750 <= player.GetItemIndex(dstSlotPos) <= 10754)
		if 10750 <= player.GetItemIndex(dstSlotPos) <= 10754 and item.GetUseType(srcItemVNum) in (
			"USE_CHANGE_ATTRIBUTE", "USE_CHANGE_ATTRIBUTE2", "USE_ADD_ATTRIBUTE", "USE_ADD_ATTRIBUTE2"):
			return False
		if srcItemVNum == mountcorebonus.SEAL_VNUM:
			return mountcorebonus.CanUseSeal(srcItemVNum, player.GetItemIndex(dstSlotPos))
		# 대상 아이템에 사용할 수 있는가?
		if srcSlotPos == dstSlotPos:
			return False

		if srcItemVNum in WEAPON_ENHANCEMENT_TARGETS:
			return player.GetItemIndex(dstSlotPos) in WEAPON_ENHANCEMENT_TARGETS[srcItemVNum]

		if (getattr(net, "IsResonanceAvailable", lambda: False)()
				and uiresonance.IsResonanceKey(srcItemVNum)):
			return uiresonance.IsSupportedHostVnum(player.GetItemIndex(dstSlotPos))
		elif srcItemVNum in (RARITY_SCROLL_VNUM, RARITY_REROLL_VNUM, RARITY_TARGETED_VNUM):
			return not player.IsEquipmentSlot(dstSlotPos)
		elif item.IsRefineScroll(srcItemVNum):
			if talismanrefine.RefineRejectionKey(srcItemVNum, player.GetItemIndex(dstSlotPos)):
				return False
			if player.REFINE_OK == player.CanRefine(srcItemVNum, dstSlotPos):
				return True
		elif app.ENABLE_SOUL_BIND_SYSTEM and item.IsSealScroll(srcItemVNum):
			if player.CanSealItem(srcItemVNum, player.INVENTORY, dstSlotPos):
				return True
		#elif item.IsMetin(srcItemVNum):
			#if player.ATTACH_METIN_OK == player.CanAttachMetin(srcItemVNum, dstSlotPos):
				#return True
		#Fix: Spirit stones - stacking.
		elif item.IsMetin(srcItemVNum):
			if player.ATTACH_METIN_OK == player.CanAttachMetin(srcItemVNum, dstSlotPos) or (item.IsMetin(player.GetItemIndex(dstSlotPos)) and player.GetItemIndex(dstSlotPos) == srcItemVNum):
				return True
		elif app.ENABLE_PERMA_ACCESSORY and self.__CanRemovePermanentOre(dstSlotPos):
				return True
		elif item.IsDetachScroll(srcItemVNum):
			if player.DETACH_METIN_OK == player.CanDetach(srcItemVNum, dstSlotPos):
				return True
		elif item.IsKey(srcItemVNum):
			if player.CanUnlock(srcItemVNum, dstSlotPos):
				return True
		elif (player.GetItemFlags(srcSlotPos) & ITEM_FLAG_APPLICABLE) == ITEM_FLAG_APPLICABLE:
			return True
		elif app.ENABLE_67TH_BONUS and srcItemVNum == item.ADD_RARE_ATTRIBUTE_VNUM:
			if self.__CanAddRareItemAttr(dstSlotPos):
				return True
		elif app.ENABLE_67TH_BONUS and srcItemVNum == item.CHANGE_RARE_ATTRIBUTE_VNUM:
			if self.__CanChangeRareItemAttrList(dstSlotPos):
				return True
		elif app.ENABLE_AURA_SYSTEM and (srcItemVNum == 49980 or srcItemVNum == 49970):
			if self.CanUseToAura(dstSlotPos):
				return True
		elif app.ENABLE_CHANGE_LOOK_SYSTEM and player.CanChangeLookClearItem(srcItemVNum, player.INVENTORY, dstSlotPos):
			return True
		elif app.ENABLE_GROWTH_PET_SYSTEM and self.__CanUseSrcPetItemToDstPetItem(srcItemVNum, srcSlotPos, dstSlotPos):
			return True
		else:
			useType = item.GetUseType(srcItemVNum)

			if "USE_CLEAN_SOCKET" == useType:
				if self.__CanCleanBrokenMetinStone(dstSlotPos):
					return True
			elif "USE_CHANGE_ATTRIBUTE" == useType:
				if self.__CanChangeItemAttrList(dstSlotPos):
					return True
			elif "USE_ADD_ATTRIBUTE" == useType:
				if self.__CanAddItemAttr(dstSlotPos):
					return True
			elif "USE_ADD_ATTRIBUTE2" == useType:
				if self.__CanAddItemAttr2(dstSlotPos):
					return True
			elif "USE_ADD_ACCESSORY_SOCKET" == useType:
				if self.__CanAddAccessorySocket(dstSlotPos):
					return True
			elif "USE_PUT_INTO_ACCESSORY_SOCKET" == useType:
				if self.__CanPutAccessorySocket(dstSlotPos, srcItemVNum):
					return True
			elif "USE_PUT_INTO_BELT_SOCKET" == useType:
				dstItemVNum = player.GetItemIndex(dstSlotPos)

				item.SelectItem(dstItemVNum)

				if item.ITEM_TYPE_BELT == item.GetItemType():
					return True
			elif "USE_CHANGE_COSTUME_ATTR" == useType:
				if self.__CanChangeCostumeAttrList(dstSlotPos):
					return True
			elif "USE_RESET_COSTUME_ATTR" == useType:
				if self.__CanResetCostumeAttr(dstSlotPos):
					return True
			elif "USE_TIME_CHARGE_PER" == useType:
				if self.__CanExtendTime(dstSlotPos):
					return True
			elif "USE_TIME_CHARGE_FIX" == useType:
				if self.__CanExtendTime(dstSlotPos):
					return True

			elif app.ENABLE_AURA_SYSTEM and "USE_PUT_INTO_AURA_SOCKET" == useType:
				dstItemVnum = player.GetItemIndex(dstSlotPos)
				item.SelectItem(dstItemVnum)
				if (item.ITEM_TYPE_COSTUME == item.GetItemType() and 
					item.COSTUME_TYPE_AURA == item.GetItemSubType() and 
					player.GetItemMetinSocket(dstSlotPos, player.ITEM_SOCKET_AURA_BOOST) == 0):
					return True

				else:
					dstItemVnum = player.GetItemIndex(dstSlotPos)
					item.SelectItem(dstItemVnum)
					if item.ITEM_TYPE_COSTUME == item.GetItemType() and item.COSTUME_TYPE_AURA == item.GetItemSubType():
						if player.GetItemMetinSocket(dstSlotPos, player.ITEM_SOCKET_AURA_BOOST) == 0:
							return True

			elif app.ENABLE_PERMA_ACCESSORY and useType == "USE_REMOVE_PERMANENT_ORE":
				if self.__CanRemovePermanentOre(dstSlotPos):
					return True

			elif app.ENABLE_ATTR_6TH_7TH and "USE_CHANGE_ATTRIBUTE2" == useType:
				if self.__CanChangeItemAttr67List(player.INVENTORY, dstSlotPos):
					return True

			elif app.ENABLE_REFINE_ELEMENT_SYSTEM:
				if "USE_ELEMENT_UPGRADE" == useType:
					if uiRefine.RefineElementDialog.CanRefineElementUpgrade(player.INVENTORY, srcSlotPos, player.INVENTORY, dstSlotPos, False, False):
						return True
				elif "USE_ELEMENT_DOWNGRADE" == useType:
					if uiRefine.RefineElementDialog.CanRefineElementDowngrade(player.INVENTORY, srcSlotPos, player.INVENTORY, dstSlotPos, False, False):
						return True
				elif "USE_ELEMENT_CHANGE" == useType:
					if uiRefine.RefineElementChangeDialog.CanRefineElementChange(player.INVENTORY, srcSlotPos, player.INVENTORY, dstSlotPos, False, False):
						return True

		return False

	if app.ENABLE_67TH_BONUS:
		def __CanAddRareItemAttr(self, dstSlotPos):
			dstItemVNum = player.GetItemIndex(dstSlotPos)
			if dstItemVNum == 0:
				return False

			item.SelectItem(dstItemVNum)

			if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
				return False

			attrCount = 0
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
					attrCount += 1

			if attrCount > player.ATTRIBUTE_SLOT_MAX_NUM - 2 and attrCount <= player.ATTRIBUTE_SLOT_MAX_NUM:
				return True

			return False

	if app.ENABLE_AURA_SYSTEM:
		def CanUseToAura(self, dstSlotPos):
			dstItemVNum = player.GetItemIndex(dstSlotPos)
			if dstItemVNum == 0:
				return False

			item.SelectItem(dstItemVNum)

			if item.ITEM_TYPE_COSTUME == item.GetItemType() and item.COSTUME_TYPE_AURA == item.GetItemSubType():
				return True

			return False

		def __CanChangeRareItemAttrList(self, dstSlotPos):
			dstItemVNum = player.GetItemIndex(dstSlotPos)
			if dstItemVNum == 0:
				return False

			item.SelectItem(dstItemVNum)

			if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
				return False

			attrCount = 0
			for i in range(player.METIN_SOCKET_MAX_NUM):
				if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
					attrCount += 1

			if attrCount < player.ATTRIBUTE_SLOT_MAX_NUM and attrCount >= (player.ATTRIBUTE_SLOT_MAX_NUM - 2):
				return True

			return False

	def __CanCleanBrokenMetinStone(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		# if item.ITEM_TYPE_WEAPON != item.GetItemType():
		if item.ITEM_TYPE_WEAPON != item.GetItemType() and item.ITEM_TYPE_ARMOR != item.GetItemType():
			return False

		for i in range(player.METIN_SOCKET_MAX_NUM):
			if player.GetItemMetinSocket(dstSlotPos, i) == constInfo.ERROR_METIN_STONE:
				return True

		return False

	def __CanChangeItemAttrList(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
			return False

		attrCount = 0
		for i in range(player.METIN_SOCKET_MAX_NUM):
			if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
				attrCount += 1

		if attrCount > 0:
			return True

		return False

	def __CanPutAccessorySocket(self, dstSlotPos, mtrlVnum):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if item.GetItemType() != item.ITEM_TYPE_ARMOR:
			return False

		if not item.GetItemSubType() in (item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR):
			return False

		curCount = player.GetItemMetinSocket(dstSlotPos, 0)
		maxCount = player.GetItemMetinSocket(dstSlotPos, 1)

		if app.ENABLE_PERMA_ACCESSORY:
			realCurCount = int(math.ceil( (curCount / 10.0)))
			
			if curCount < 10:
				realCurCount = curCount
			elif curCount < 20 and curCount != 10:
				realCurCount = (curCount - 10) + 1

			if mtrlVnum != constInfo.GET_ACCESSORY_MATERIAL_VNUM(dstItemVNum, item.GetItemSubType()) and mtrlVnum != constInfo.GET_Permanent_ACCESSORY_MATERIAL_VNUM(dstItemVNum, item.GetItemSubType()):
				return False
				
			if realCurCount>=maxCount:
				return False
		else:
			if mtrlVnum != constInfo.GET_ACCESSORY_MATERIAL_VNUM(dstItemVNum, item.GetItemSubType()):
				return False

			if curCount >= maxCount:
				return False

		return True

	def __CanAddAccessorySocket(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		#if item.GetItemType() != item.ITEM_TYPE_ARMOR:
		if not item.GetItemType() in (item.ITEM_TYPE_ARMOR, item.ITEM_TYPE_BELT):
			return False

		#if not item.GetItemSubType() in (item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR):
		if not item.GetItemType() == item.ITEM_TYPE_BELT:
			if not item.GetItemSubType() in (item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR):
				return False

		curCount = player.GetItemMetinSocket(dstSlotPos, 0)
		maxCount = player.GetItemMetinSocket(dstSlotPos, 1)

		ACCESSORY_SOCKET_MAX_SIZE = 3
		if maxCount >= ACCESSORY_SOCKET_MAX_SIZE:
			return False

		return True

	if app.ENABLE_ATTR_6TH_7TH:
		def __CanChangeItemAttr67List(self, dstSlotWindow, dstSlotPos):
			dstItemVNum = player.GetItemIndex(dstSlotWindow, dstSlotPos)
			if dstItemVNum == 0:
				return False

			item.SelectItem(dstItemVNum)

			if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
				return False

			if app.ENABLE_QUIVER_SYSTEM:
				if (item.GetItemType() == item.ITEM_TYPE_WEAPON and item.GetItemSubType() in (item.WEAPON_ARROW, item.WEAPON_QUIVER)):
					return False
			else:
				if (item.GetItemType() == item.ITEM_TYPE_WEAPON and item.GetItemSubType() == item.WEAPON_ARROW):
					return False

			# 재경비서
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_ENCHANT):
				return False

			if app.ENABLE_SOUL_BIND_SYSTEM:
				if player.GetItemSealDate(dstSlotWindow, dstSlotPos) == -1 or player.GetItemSealDate(dstSlotWindow, dstSlotPos) > 0:
					return False

			attrCount = 0
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				type, value = player.GetItemAttribute(dstSlotWindow, dstSlotPos, i)
				if type != 0:
					attrCount += 1

			if attrCount > player.ATTRIBUTE_SLOT_MAX_NUM - 2 and attrCount <= player.ATTRIBUTE_SLOT_MAX_NUM:
				return True

			return False

	def __CanAddItemAttr(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
			return False

		attrCount = 0
		for i in range(player.METIN_SOCKET_MAX_NUM):
			# 2020.02.13.Owsap - Fix Attribute Count
			if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
				attrCount += 1

		if attrCount < 4:
			return True

		return False

	# 2020.02.13.Owsap - Fix Attribute Count
	def __CanAddItemAttr2(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
			return False

		attrCount = 0
		for i in range(player.METIN_SOCKET_MAX_NUM):
			if player.GetItemAttribute(dstSlotPos, i)[0] != 0:
				attrCount += 1

		if attrCount == 4:
			return True

		return False

	def __CanChangeCostumeAttrList(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if item.GetItemType() != item.ITEM_TYPE_COSTUME:
			return False

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if item.GetItemSubType() == item.COSTUME_TYPE_ACCE:
				return False

		if app.ENABLE_MOUNT_COSTUME_SYSTEM:
			if item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
				return False

		for i in range(player.METIN_SOCKET_MAX_NUM):
			type, value = player.GetItemAttribute(dstSlotPos, i)
			if type != 0:
				return True

		return False

	def __CanResetCostumeAttr(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		if item.GetItemType() != item.ITEM_TYPE_COSTUME:
			return False

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if item.GetItemSubType() == item.COSTUME_TYPE_ACCE:
				return False

		if app.ENABLE_MOUNT_COSTUME_SYSTEM:
			if item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
				return False

		for i in range(player.METIN_SOCKET_MAX_NUM):
			type, value = player.GetItemAttribute(dstSlotPos, i)
			if type != 0:
				return True

		return False

	def __CanExtendTime(self, dstSlotPos):
		dstItemVNum = player.GetItemIndex(dstSlotPos)
		if dstItemVNum == 0:
			return False

		item.SelectItem(dstItemVNum)

		# Dragon Stones are permanent; the server refuses every time recharge.
		if item.GetItemType() == item.ITEM_TYPE_DS:
			return False

		if app.ENABLE_COSTUME_EXTENDED_RECHARGE:
			if item.GetItemType() != item.ITEM_TYPE_COSTUME:
				return False

			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				if item.GetItemSubType() == item.COSTUME_TYPE_ACCE:
					return False

			metinSlot = [player.GetItemMetinSocket(dstSlotPos, j) for j in range(player.METIN_SOCKET_MAX_NUM)]
			leftSec = max(0, metinSlot[0] - app.GetGlobalTimeStamp())

			if leftSec >= item.MIN_INFINITE_DURATION:
				return False
		else:
			return False

		return True

	if app.ENABLE_PERMA_ACCESSORY:
		def __CanRemovePermanentOre(self, dstSlotPos):
			dstItemVNum = player.GetItemIndex(dstSlotPos)
			if dstItemVNum == 0:
				return False
				
			item.SelectItem(dstItemVNum)
			
			dstItemType		= item.GetItemType()
			dstItemSubType	= item.GetItemSubType()
			
			isOK = False
			
			if dstItemType == item.ITEM_TYPE_BELT:
				isOK = True
				
			if dstItemType == item.ITEM_TYPE_ARMOR and dstItemSubType in [item.ARMOR_EAR, item.ARMOR_NECK, item.ARMOR_WRIST]:
				isOK = True
				
			if isOK == False:
				return False
		
			metinSlot = []
			for i in range(player.METIN_SOCKET_MAX_NUM):
				metinSlot.append(player.GetItemMetinSocket(dstSlotPos, i))
				
			if metinSlot[0] >= 10:
				return True
				
			return False

	def ShowToolTip(self, slotIndex):
		if getattr(self, "refreshingItemSlots", False):
			return
		self.hoveredItemSlot = slotIndex
		if None != self.tooltipItem:
			self.tooltipItem.SetInventoryItem(slotIndex)

	def OnTop(self):
		if None != self.tooltipItem:
			self.tooltipItem.SetTop()

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if self.wndMultiple:
				if self.IsClickMultipleInventory == False:
					self.wndMultiple.SetTop()
				else:
					self.IsClickMultipleInventory = False

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def UseItemSlot(self, slotIndex):
		curCursorNum = app.GetCursor()
		if app.SELL == curCursorNum:
			return

		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS():
			return

		## 2021.02.01.Owsap - Prevent unequipping an item while acting emotion.
		if player.IsActingEmotion():
			return

		if app.ENABLE_SEARCH_FIELD:
			if self.wndItemSRC and self.wndItemSRC.IsShow() and self.wndSearchEdit and self.wndSearchEdit.GetText():
				anchor = self.__InventorySearchResolveAnchor(slotIndex)
				if anchor in self.wndItemSRC.dictItems:
					slotIndex = self.wndItemSRC.dictItems[anchor][1]
				else:
					slotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(slotIndex)
			else:
				slotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(slotIndex)
		else:
			slotIndex = self.__InventoryLocalSlotPosToGlobalSlotPos(slotIndex)

		if self.IsVirtualMarketDraftSlot(slotIndex):
			self.__ShowVirtualMarketDraftLocked()
			return

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if slotIndex in osfInfo.MULTIPLE_LIST:
				return

		if self.wndDragonSoulRefine.IsShow():
			if self.wndDragonSoulRefine.AutoSetItem(
					(player.INVENTORY, slotIndex), 1):
				return

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if self.isShowAcceWindow():
				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_NOT_SEALITEM)
						return

				acce.Add(player.INVENTORY, slotIndex, 255)
				return

		if app.ENABLE_AURA_SYSTEM:
			if self.isShowAuraWindow():
				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHANGE_LOOK_DO_NOT_SEAL_ITEM)
						return

				self.wndAura.AddFastItem(slotIndex)
				return

		self.__UseItem(slotIndex)
		mouseModule.mouseController.DeattachObject()
		self.OverOutItem()

	def __UseItem(self, slotIndex):
		ItemVNum = player.GetItemIndex(slotIndex)
		item.SelectItem(ItemVNum)

		isCtrlPressed = app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)
		isAltPressed = app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT)

		if isCtrlPressed and isAltPressed:
			return

		if app.ENABLE_WIKI:
			if isCtrlPressed:
				if self.interface:
					if not self.interface.wndWiki or not self.interface.wndWiki.IsShow():
						self.interface.OpenWikiWindow()

					if self.interface.wndWiki and self.interface.wndWiki.IsShow():
						self.interface.wndWiki.ShowItemInfo(ItemVNum, 0, isHistory=False)
						if hasattr(self.interface.wndWiki, "FocusSearchItem"):
							self.interface.wndWiki.FocusSearchItem()
				return

		# Ctrl keeps the wiki lookup above; any other right-click while an
		# exchange is open offers the item instead of using it (ALTHEA-601).
		if exchangequickadd.TryAddInventoryItem(self.interface, slotIndex):
			return

		if app.ENABLE_AURA_SYSTEM:
			if player.IsAuraRefineWindowOpen():
				self.__UseItemAura(slotIndex)
				return

		if app.ENABLE_GROWTH_PET_SYSTEM:
			itemType = item.GetItemType()
			if itemType == item.ITEM_TYPE_PET and item.GetItemSubType() == item.PET_SKILL:
				self.__UseItemPet(slotIndex)
				return
			
			if self.interface.wndPetInfoWindow.AttachItemToPetWindow(player.INVENTORY, player.SLOT_TYPE_INVENTORY, slotIndex):
				return
				
			if self.PetSkillDelDlg and self.PetSkillDelDlg.IsShow():
				self.__PetSkillDeleteQuestionDialogCancel()

			if item.ITEM_TYPE_PET == itemType:
				self.__UseItemPet(slotIndex)
				return

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if player.GetChangeLookWindowOpen() == 1:
				return

		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface.AttachInvenItemToOtherWindowSlot(slotIndex):
				return

		if app.ENABLE_BUFF_SYSTEM:
			# A VIP elf outfit is worn only by the elf-form Buffi: right click runs
			# the same checks, confirmation and /support_system request as dragging
			# it onto the Buffi outfit slot. ITEM_USE would be refused by EquipItem.
			import uiBuff
			if uiBuff.IsVipElfOutfit(ItemVNum):
				supportWindow = getattr(self.interface, "wndSupportPG", None) if self.interface else None
				if supportWindow:
					supportWindow.EquipFromInventory(slotIndex, osfInfo.SUPPORT_SLOT_ARMOR)
				return

		if app.ENABLE_MOUNT_COSTUME_SYSTEM:
			if item.GetItemType() == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == item.COSTUME_TYPE_MOUNT:
				self.__SendUseItemPacket(slotIndex)
				return

		if app.ENABLE_SHOW_CHEST_DROP:
			if player.GetItemTypeBySlot(slotIndex) in (
					item.ITEM_TYPE_GIFTBOX, item.ITEM_TYPE_GACHA,
					item.ITEM_TYPE_TREASURE_BOX):
				if self.interface and self.interface.dlgChestDrop:
					self.interface.dlgChestDrop.RequestPreview(slotIndex)
				return

		# ALTHEA-641: a bow no longer needs arrows or a quiver to shoot.
		if virtualquiver.RefusesEquip(slotIndex):
			virtualquiver.NotifyNoLongerNeeded()
			return

		if item.IsFlag(item.ITEM_FLAG_CONFIRM_WHEN_USE):
			self.questionDialog = uiCommon.QuestionDialog()
			self.questionDialog.SetText(localeInfo.INVENTORY_REALLY_USE_ITEM2)

			self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__UseItemQuestionDialog_OnAccept))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__UseItemQuestionDialog_OnCancel))
			self.questionDialog.Open()
			self.questionDialog.slotIndex = slotIndex

			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

		else:
			self.__SendUseItemPacket(slotIndex)

	def __UseItemQuestionDialog_OnCancel(self):
		self.OnCloseQuestionDialog()

	def __UseItemQuestionDialog_OnAccept(self):
		self.__SendUseItemPacket(self.questionDialog.slotIndex)
		self.OnCloseQuestionDialog()

	def __SendUseItemToItemPacket(self, srcSlotPos, dstSlotPos):
		if self.IsVirtualMarketDraftSlot(srcSlotPos) or self.IsVirtualMarketDraftSlot(dstSlotPos):
			self.__ShowVirtualMarketDraftLocked()
			return
		# 개인상점 열고 있는 동안 아이템 사용 방지
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.USE_ITEM_FAILURE_PRIVATE_SHOP)
			return

		if self.interface.IsShowDlgQuestionWindow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DONT_USE_ITEM_WHEN_SHOW_CONFIRM)
			return

		net.SendItemUseToItemPacket(srcSlotPos, dstSlotPos)

	def __SendUseItemPacket(self, slotPos):
		if self.IsVirtualMarketDraftSlot(slotPos):
			self.__ShowVirtualMarketDraftLocked()
			return
		# 개인상점 열고 있는 동안 아이템 사용 방지
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.USE_ITEM_FAILURE_PRIVATE_SHOP)
			return

		if self.interface.IsShowDlgQuestionWindow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DONT_USE_ITEM_WHEN_SHOW_CONFIRM)
			return

		if app.ENABLE_SCROLL_ATLAS:
			WARP_SCROLLS = [22011, 22000, 22010]
			itemIndex = player.GetItemIndex(slotPos)
			if itemIndex in WARP_SCROLLS:
				x = player.GetItemMetinSocket(slotPos, 0)
				y = player.GetItemMetinSocket(slotPos, 1)
				if x > 0 and  y > 0:
					self.interface.wndScrollWarp.initMap(x,y,slotPos)
					return

		net.SendItemUsePacket(slotPos)

	def __SendMoveItemPacket(self, srcSlotPos, dstSlotPos, srcItemCount):
		if self.IsVirtualMarketDraftSlot(srcSlotPos) or self.IsVirtualMarketDraftSlot(dstSlotPos):
			self.__ShowVirtualMarketDraftLocked()
			return
		# ALTHEA-641: arrows and quivers can no longer be equipped.
		if virtualquiver.RefusesEquip(srcSlotPos, dstSlotPos):
			virtualquiver.NotifyNoLongerNeeded()
			return
		# 개인상점 열고 있는 동안 아이템 사용 방지
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MOVE_ITEM_FAILURE_PRIVATE_SHOP)
			return

		if self.interface.IsShowDlgQuestionWindow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DONT_USE_ITEM_WHEN_SHOW_CONFIRM)
			return

		net.SendItemMovePacket(srcSlotPos, dstSlotPos, srcItemCount)

	def SetDragonSoulRefineWindow(self, DragonSoulRefine):
		from _weakref import proxy
		self.wndDragonSoulRefine = proxy(DragonSoulRefine)

	def OnMoveWindow(self, x, y):
		body_x, body_y = self.GetInventoryBodyGlobalPosition()
		if app.ENABLE_BRAVE_CAPE_RENEWAL:
			if self.wndBraveCape:
				self.wndBraveCape.AdjustPosition(body_x, body_y)

		if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
			if self.wndMultiple:
				self.wndMultiple.AdjustPositionAndSize()

	# 악세서리 슬롯 테두리 추가, 제거.
	## HilightSlot Change
	def DeactivateSlot(self, slotindex, type):
		if type == wndMgr.HILIGHTSLOT_MAX:
			return

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if type == wndMgr.HILIGHTSLOT_CHANGE_LOOK:
				self.__DelHighlightSlotChangeLook(slotindex)

	## HilightSlot Change
	def ActivateSlot(self, slotindex, type):
		if type == wndMgr.HILIGHTSLOT_MAX:
			return

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if type == wndMgr.HILIGHTSLOT_CHANGE_LOOK:
				self.__AddHighlightSlotChangeLook(slotindex)

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def __AddHighlightSlotChangeLook(self, slotIndex):
			if not slotIndex in self.listHighlightedChangeLookSlot:
				self.listHighlightedChangeLookSlot.append(slotIndex)

		def __DelHighlightSlotChangeLook(self, slotIndex):
			if slotIndex in self.listHighlightedChangeLookSlot:
				if slotIndex >= player.INVENTORY_PAGE_SIZE:
					self.wndItem.DeactivateSlot(slotIndex - (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE))
					self.wndItem.SetCanMouseEventSlot(slotIndex - (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE))
				else:
					self.wndItem.DeactivateSlot(slotIndex)
					self.wndItem.SetCanMouseEventSlot(slotIndex)
				self.listHighlightedChangeLookSlot.remove(slotIndex)

	## 하이라이트 리프레쉬.
	def __HighlightSlot_Refresh(self):
		## 악세서리.
		for i in range(self.wndItem.GetSlotCount()):
			slotNumber = self.__InventoryLocalSlotPosToGlobalSlotPos(i)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if slotNumber in self.listHighlightedChangeLookSlot:
					self.wndItem.ActivateSlotOld(i)
					self.wndItem.SetSlotDiffuseColor(i, wndMgr.COLOR_TYPE_RED)
					self.wndItem.SetCantMouseEventSlot(i)

			## HilightSlot Change
			if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
				if slotNumber in self.listHighlightedSlot:
					self.wndItem.ActivateSlotOld(i)

	## 악세서리 용 하이라이트 list 클리어.
	def __HighlightSlot_Clear(self):
		## 악세서리
		for i in range(self.wndItem.GetSlotCount()):
			slotNumber = self.__InventoryLocalSlotPosToGlobalSlotPos(i)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if slotNumber in self.listHighlightedChangeLookSlot:
					self.wndItem.DeactivateSlot(i)
					self.wndItem.SetCanMouseEventSlot(i)
					self.listHighlightedChangeLookSlot.remove(slotNumber)

			## HilightSlot Change
			if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
				if slotNumber in self.listHighlightedSlot:
					self.wndItem.DeactivateSlot(i)
					self.listHighlightedSlot.remove(slotNumber)

	if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
		# 슬롯 highlight 관련
		## 추가
		def HighlightSlot(self, slot):
			#slot값에 대한 예외처리.
			if slot > player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT:
				return

			if not slot in self.listHighlightedSlot:
				self.listHighlightedSlot.append(slot)

		## 삭제
		def DelHighlightSlot(self, inventorylocalslot):
			if inventorylocalslot in self.listHighlightedSlot:
				if inventorylocalslot >= player.INVENTORY_PAGE_SIZE:
					self.wndItem.DeactivateSlot(inventorylocalslot - (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE))
				else:
					self.wndItem.DeactivateSlot(inventorylocalslot)

				self.listHighlightedSlot.remove(inventorylocalslot)
		# 슬롯 highlight 관련 끝

	# wj.2014.12.2. 인벤토리와 DS인벤 간의 상태를 확인 및 설정하기 위한 함수.
	def IsDlgQuestionShow(self):
		if self.dlgQuestion.IsShow():
			return True
		else:
			return False

	def CancelDlgQuestion(self):
		self.__Cancel()

	def SetUseItemMode(self, bUse):
		self.wndItem.SetUseMode(bUse)

	def GetInventoryPageIndex(self):
		## 0 or 1
		return self.inventoryPageIndex

	def OverInToolTip(self, arg):
		arglen = len(str(arg))
		pos_x, pos_y = wndMgr.GetMousePosition()

		self.toolTip.ClearToolTip()
		self.toolTip.SetThinBoardSize(11 * arglen)
		self.toolTip.SetToolTipPosition(pos_x + 5, pos_y - 5)
		self.toolTip.AppendTextLine(arg, 0xffffff00)
		self.toolTip.Show()

	def OverOutToolTip(self):
		self.toolTip.Hide()

	def EventProgress(self, event_type, idx):
		if "mouse_over_in" == str(event_type):
			if idx == 0:
				self.OverInToolTip(localeInfo.CHEQUE_SYSTEM_UNIT_YANG)
			elif app.ENABLE_GEM_SYSTEM and idx == 1 :
				self.OverInToolTip(localeInfo.GEM_SYSTEM_NAME)
			else:
				return
		elif "mouse_over_out" == str(event_type):
			self.OverOutToolTip()
		else:
			return

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def SetAcceWindow(self, wndAcceCombine, wndAcceAbsorption):
			self.wndAcceCombine = wndAcceCombine
			self.wndAcceAbsorption = wndAcceAbsorption

		def isShowAcceWindow(self):
			if self.wndAcceCombine:
				if self.wndAcceCombine.IsShow():
					return 1

			if self.wndAcceAbsorption:
				if self.wndAcceAbsorption.IsShow():
					return 1

			return 0

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def __UseItemPet(self, slotIndex):
			itemSubType = item.GetItemSubType()		
			if item.PET_SKILL == itemSubType:
				if self.interface and self.interface.wndPetInfoWindow:
					self.interface.wndPetInfoWindow.RequestLearnSkillBook(slotIndex)
			elif item.PET_EGG == itemSubType:
				self.petHatchingWindow.HatchingWindowOpen(player.INVENTORY, slotIndex)
				
			elif item.PET_UPBRINGING == itemSubType:
				petID = player.GetItemMetinSocket(player.INVENTORY, slotIndex, 2)
				endTime = player.GetItemMetinSocket(player.INVENTORY, slotIndex, 0)
				if petID and app.GetGlobalTimeStamp() >= endTime:
					if self.interface and self.interface.wndPetInfoWindow:
						self.interface.wndPetInfoWindow.OpenInspectedPet(slotIndex, petID)
					return
				if self.__CanUseGrowthPet(slotIndex):
					self.__SendUseItemPacket(slotIndex)
						
			elif item.PET_BAG == itemSubType:
				if self.__CanUsePetBagItem(slotIndex):
					if self.questionDialog:
						self.questionDialog.Close()
						
					self.questionDialog = uiCommon.QuestionDialog()
					self.questionDialog.SetText(localeInfo.INVENTORY_REALLY_USE_PET_BAG_TAKE_OUT)
					self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__UseItemQuestionDialog_OnAccept))
					self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__UseItemQuestionDialog_OnCancel))
					self.questionDialog.slotIndex = slotIndex
					self.questionDialog.Open()

			if item.PET_SKILL_ALL_DEL_BOOK == itemSubType:
				pet_id = player.GetActivePetItemId()
				if 0 == pet_id:
					return
				if not any(state[1] for state in growthpetpresentation.SkillSlots(pet_id)):
					popup = uiCommon.PopupDialog()
					popup.SetText(localeInfo.PET_EMPTY_SKILL_SLOT_USE_ITEM)
					popup.SetAcceptEvent(self.__OnClosePopupDialog)
					popup.Open()
					self.pop = popup
					return
			
				self.PetSkillAllDelBookIndex = slotIndex
				self.SetCantMouseEventSlot( self.PetSkillAllDelBookIndex )
				
				self.PetSkillDelDlg.SetAcceptEvent(ui.__mem_func__(self.__PetSkillDeleteQuestionDialogAccept))
				self.PetSkillDelDlg.SetCancelEvent(ui.__mem_func__(self.__PetSkillDeleteQuestionDialogCancel))
				
				self.PetSkillDelDlg.SetText1( localeInfo.PET_SKILL_DELETE_QUESTION_DLG_MSG1 )
				self.PetSkillDelDlg.SetText2( localeInfo.PET_SKILL_DELETE_QUESTION_DLG_MSG2 )
				(w,h) = self.PetSkillDelDlg.GetTextSize1()
				self.PetSkillDelDlg.SetWidth(w+100)
				self.PetSkillDelDlg.Open()
				
		def __OnClosePopupDialog(self):
			self.pop = None

		def __ActivePetHighlightSlot(self, slotNumber):
			active_id = player.GetActivePetItemId()
			
			if active_id == player.GetItemMetinSocket(player.INVENTORY, slotNumber, 2):
				
				if slotNumber >= player.INVENTORY_PAGE_SIZE:
					slotNumber -= (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE)
			
				self.wndItem.ActivateSlotOld(slotNumber)
			else:
				if slotNumber >= player.INVENTORY_PAGE_SIZE:
					slotNumber -= (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE)
					
				self.wndItem.DeactivateSlot(slotNumber)

		def __SetCoolTimePetItemSlot(self, slotNumber, itemVnum):
		
			item.SelectItem(itemVnum)
			itemSubType = item.GetItemSubType()
		
			if itemSubType not in [item.PET_UPBRINGING, item.PET_BAG]:
				return
				
			if itemSubType == item.PET_BAG:
				id = player.GetItemMetinSocket(player.INVENTORY, slotNumber, 2)
				if id == 0:
					return
			
			(limitType, limitValue) = item.GetLimit(0)

			if itemSubType == item.PET_UPBRINGING:
				limitValue = player.GetItemMetinSocket(player.INVENTORY, slotNumber, 1)
					
			if limitType in [item.LIMIT_REAL_TIME, item.LIMIT_REAL_TIME_START_FIRST_USE]:
								
				sock_time   = player.GetItemMetinSocket(player.INVENTORY, slotNumber, 0)
				
				remain_time = max(0, sock_time - app.GetGlobalTimeStamp())
			
				if slotNumber >= player.INVENTORY_PAGE_SIZE:
					slotNumber -= (self.inventoryPageIndex * player.INVENTORY_PAGE_SIZE)

				self.wndItem.SetSlotCoolTimeInverse(slotNumber, limitValue, limitValue - remain_time)

		def __IsPetItem(self, srcItemVID):
			item.SelectItem(srcItemVID)
			
			if item.GetItemType() == item.ITEM_TYPE_PET:
				return True
			
			return False

		def __SendUsePetItemToItemPacket(self, srcItemVID, srcItemSlotPos, dstItemSlotPos):
			if self.__CanUseSrcPetItemToDstPetItem(srcItemVID, srcItemSlotPos, dstItemSlotPos):
				srcItemVnum		= player.GetItemIndex(srcItemSlotPos)
				item.SelectItem( srcItemVnum )
				srcItemType		= item.GetItemType()
				srcItemSubType	= item.GetItemSubType()
				
				if item.ITEM_TYPE_PET == srcItemType:					
					if srcItemSubType in [item.PET_FEEDSTUFF, item.PET_BAG]:
						self.__OpenPetItemQuestionDialog(srcItemSlotPos, dstItemSlotPos)
					elif item.PET_NAME_CHANGE == srcItemSubType:
						self.__UseItemPetNameChange(srcItemSlotPos, dstItemSlotPos)
				return True
				
			return False
			
		def __UseItemPetNameChange(self, srcSlotPos, dstSlotPos):
			if self.petNameChangeWindow:
				self.petNameChangeWindow.NameChangeWindowOpen(srcSlotPos, dstSlotPos)

		def __IsUsablePetItem(self, srcItemVNum):
			item.SelectItem(srcItemVNum)
			srcItemType		= item.GetItemType()
			srcItemSubType	= item.GetItemSubType()

			if srcItemType != item.ITEM_TYPE_PET:
				return False
			
			if srcItemSubType not in [item.PET_UPBRINGING, item.PET_FEEDSTUFF, item.PET_BAG, item.PET_NAME_CHANGE]:
				return False
			
			return True

		def __CanUseSrcPetItemToDstPetItem(self, srcItemVNum, srcSlotPos, dstSlotPos):
			item.SelectItem(srcItemVNum)
			srcItemType		= item.GetItemType()
			srcItemSubType	= item.GetItemSubType()
			
			if srcItemType != item.ITEM_TYPE_PET:
				return False
			
			if srcItemSubType == item.PET_FEEDSTUFF:		
				detIndex = player.GetItemIndex(dstSlotPos)
				item.SelectItem(detIndex)
				
				dstItemType		= item.GetItemType()
				dstItemSubType	= item.GetItemSubType()
				
				if dstItemType != item.ITEM_TYPE_PET:
					return False
					
				if dstItemSubType not in [item.PET_UPBRINGING]:
					return False
					
				if dstItemSubType == item.PET_BAG:
					incaseTime = player.GetItemMetinSocket(dstSlotPos, 1)
					if incaseTime == 0:
						return False
			
			elif srcItemSubType == item.PET_BAG:
				detIndex = player.GetItemIndex(dstSlotPos)
				item.SelectItem(detIndex)
				
				dstItemType		= item.GetItemType()
				dstItemSubType	= item.GetItemSubType()
				
				if dstItemType != item.ITEM_TYPE_PET:
					return False
					
				if dstItemSubType not in [item.PET_UPBRINGING, item.PET_BAG]:
					return False
			
				lifeTime = player.GetItemMetinSocket(dstSlotPos, 0)
					
				if dstItemSubType == item.PET_UPBRINGING:
					if lifeTime < app.GetGlobalTimeStamp():
						return False

					srcIncase = player.GetItemMetinSocket(srcSlotPos, 1)
					if srcIncase != 0:
						return False
					
				elif dstItemSubType == item.PET_BAG:
					if lifeTime > app.GetGlobalTimeStamp():
						return False
						
					srcIncase = player.GetItemMetinSocket(srcSlotPos, 1)
					if srcIncase != 0:
						return False
					
					destIncase = player.GetItemMetinSocket(dstSlotPos, 1)
					if destIncase == 0:
						return False
						
			elif srcItemSubType == item.PET_NAME_CHANGE:
				detIndex = player.GetItemIndex(dstSlotPos)
				item.SelectItem(detIndex)
				
				dstItemType		= item.GetItemType()
				dstItemSubType	= item.GetItemSubType()
				
				if dstItemType != item.ITEM_TYPE_PET:
					return False
					
				if dstItemSubType not in [item.PET_UPBRINGING]:
					return False
					
			else:
				return False
			
			return True

		def __CanUseGrowthPet(self, slotIndex):
			if not player.GetItemMetinSocket(player.INVENTORY, slotIndex, 2):
				return False
				
			(limitType, limitValue) = item.GetLimit(0)
			remain_time = 999
			if item.LIMIT_REAL_TIME == limitType:
				sock_time   = player.GetItemMetinSocket(player.INVENTORY, slotIndex, 0)
				if app.GetGlobalTimeStamp() > sock_time:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_SUMMON_BECAUSE_LIFE_TIME_END)
					return False
					
			return True

		def __CanUsePetBagItem(self, slotIndex):
			if not player.GetItemMetinSocket(player.INVENTORY, slotIndex, 2):
				return False
				
			(limitType, limitValue) = item.GetLimit(0)
			remain_time = 999
			if item.LIMIT_REAL_TIME_START_FIRST_USE == limitType:
				sock_time   = player.GetItemMetinSocket(player.INVENTORY, slotIndex, 0)
				use_cnt	    = player.GetItemMetinSocket(player.INVENTORY, slotIndex, 1)
				
				if use_cnt:
					if app.GetGlobalTimeStamp() > sock_time:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_USE_BAG)
						return False;
						
			return True

		def __CanAttachGrowthPetItem(self, itemVNum, itemSlotIndex):
			activePetId = player.GetActivePetItemId()
			if activePetId == 0:
				return True
			
			item.SelectItem(itemVNum)
			itemType	= item.GetItemType()
			itemSubType = item.GetItemSubType()
			
			if item.ITEM_TYPE_PET == itemType and itemSubType == item.PET_UPBRINGING:
				petId = player.GetItemMetinSocket(itemSlotIndex, 2)
				if petId == activePetId:
					return False
					
					
			return True

		def SetPetHatchingWindow(self, window):
			self.petHatchingWindow = window

		def SetPetNameChangeWindow(self, window):
			self.petNameChangeWindow = window

		def SetPetFeedWindow(self, window):
			self.petFeedWindow = window

		def ItemMoveFeedWindow(self, slotWindow, slotIndex):
			if not self.petFeedWindow:
				return
				
			self.petFeedWindow.ItemMoveFeedWindow(slotWindow, slotIndex)

		def __OpenPetBagQuestionDialog(self, srcItemSlotPos, dstItemSlotPos):
			if self.interface.IsShowDlgQuestionWindow():
				self.interface.CloseDlgQuestionWindow()

		def __OpenPetItemQuestionDialog(self, srcItemPos, dstItemPos):
			if self.interface.IsShowDlgQuestionWindow():
				self.interface.CloseDlgQuestionWindow()
			
			getItemVNum=player.GetItemIndex
			self.srcItemPos = srcItemPos
			self.dstItemPos = dstItemPos

			srcItemVnum = getItemVNum(srcItemPos)
			dstItemVnum = getItemVNum(dstItemPos)
			
			item.SelectItem( srcItemVnum )
			src_item_name = item.GetItemName( srcItemVnum )
			srcItemType		= item.GetItemType()
			srcItemSubType	= item.GetItemSubType()
			
			item.SelectItem( dstItemVnum )
			dst_item_name = item.GetItemName( getItemVNum(dstItemPos) )
			
			self.PetItemQuestionDlg.SetAcceptEvent(ui.__mem_func__(self.__PetItemAccept))
			self.PetItemQuestionDlg.SetCancelEvent(ui.__mem_func__(self.__PetItemCancel))
			
			if item.ITEM_TYPE_PET == srcItemType:
				if item.PET_FEEDSTUFF == srcItemSubType:
					self.PetItemQuestionDlg.SetText( localeInfo.INVENTORY_REALLY_USE_PET_FEEDSTUFF_ITEM % ( src_item_name, dst_item_name ) )
					self.PetItemQuestionDlg.Open()
				
				elif item.PET_BAG == srcItemSubType:
					self.PetItemQuestionDlg.SetText( localeInfo.INVENTORY_REALLY_USE_PET_BAG_ITEM )
					self.PetItemQuestionDlg.Open()			
				
		def __PetItemAccept(self):
			self.PetItemQuestionDlg.Close()
			self.__SendUseItemToItemPacket(self.srcItemPos, self.dstItemPos)
			self.srcItemPos = (0, 0)
			self.dstItemPos = (0, 0)
			self.srcItemWindow = None
			self.dstItemWindow = None

		def __PetItemCancel(self):
			self.srcItemPos = (0, 0)
			self.dstItemPos = (0, 0)
			self.PetItemQuestionDlg.Close()

		def __PetSkillDeleteQuestionDialogAccept(self):
			net.SendPetDeleteAllSkill( self.PetSkillAllDelBookIndex )	
			self.__PetSkillDeleteQuestionDialogCancel()
			
		def __PetSkillDeleteQuestionDialogCancel(self):
			self.PetSkillDelDlg.Close()
			self.SetCanMouseEventSlot( self.PetSkillAllDelBookIndex )
			self.PetSkillAllDelBookIndex = -1
			
		def SetCanMouseEventSlot(self, inven_slot_index):
			if inven_slot_index >= player.INVENTORY_PAGE_SIZE:
				page = self.GetInventoryPageIndex() # range 0,1,2,3
				inven_slot_index -= (page * player.INVENTORY_PAGE_SIZE)
			self.wndItem.SetCanMouseEventSlot(inven_slot_index)
			
		def SetCantMouseEventSlot(self, inven_slot_index):
			if inven_slot_index >= player.INVENTORY_PAGE_SIZE:
				page = self.GetInventoryPageIndex() # range 0,1,2,3
				inven_slot_index -= (page * player.INVENTORY_PAGE_SIZE)
			self.wndItem.SetCantMouseEventSlot(inven_slot_index)

	if app.ENABLE_AURA_SYSTEM:
		def SetAuraWindow(self, wndAura):
			self.wndAura = wndAura
			
		def isShowAuraWindow(self):
			if self.wndAura:
				if self.wndAura.IsShow():
					return 1

			return 0
		def __UseItemAuraQuestionDialog_OnAccept(self):
			self.questionDialog.Close()
			net.SendAuraRefineCheckIn(*(self.questionDialog.srcItem + self.questionDialog.dstItem + (player.GetAuraRefineWindowType(),)))
			self.questionDialog.srcItem = (0, 0)
			self.questionDialog.dstItem = (0, 0)

		def __UseItemAuraQuestionDialog_Close(self):
			self.questionDialog.Close()

			self.questionDialog.srcItem = (0, 0)
			self.questionDialog.dstItem = (0, 0)

		def __UseItemAura(self, slotIndex):
			AuraSlot = player.FineMoveAuraItemSlot()
			UsingAuraSlot = player.FindActivatedAuraSlot(player.INVENTORY, slotIndex)
			AuraVnum = player.GetItemIndex(slotIndex)
			item.SelectItem(AuraVnum)
			if player.GetAuraCurrentItemSlotCount() >= player.AURA_SLOT_MAX <= UsingAuraSlot:
				return

			if player.IsEquipmentSlot(slotIndex):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EQUIPITEM)
				return

			if app.ENABLE_SOUL_BIND_SYSTEM and player.GetItemSealDate(player.INVENTORY, slotIndex):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_SEALITEM)
				return

			if player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_ABSORB:
				isAbsorbItem = False
				if item.GetItemType() == item.ITEM_TYPE_COSTUME:
					if item.GetItemSubType() == item.COSTUME_TYPE_AURA:
						if player.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM) == 0:
							if UsingAuraSlot == player.AURA_SLOT_MAX:
								if AuraSlot != player.AURA_SLOT_MAIN:
									return

								net.SendAuraRefineCheckIn(player.INVENTORY, slotIndex, player.AURA_REFINE, AuraSlot, player.GetAuraRefineWindowType())

						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_ABSORBITEM)
							return

					else:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_ABSORBITEM)
						return

				elif item.GetItemType() == item.ITEM_TYPE_ARMOR:
					if item.GetItemSubType() in [item.ARMOR_SHIELD, item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR]:
						if player.FindUsingAuraSlot(player.AURA_SLOT_MAIN) == player.NPOS():
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_REGISTER_AURAITEM)
							return

						isAbsorbItem = True
					else:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_ABSORBITEM)
						return

				else:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_ABSORBITEM)
					return

				if isAbsorbItem:
					if UsingAuraSlot == player.AURA_SLOT_MAX:
						if AuraSlot != player.AURA_SLOT_SUB:
							if player.FindUsingAuraSlot(player.AURA_SLOT_SUB) == player.NPOS():
								AuraSlot = player.AURA_SLOT_SUB
							else:
								return

						self.questionDialog = uiCommon.QuestionDialog()
						self.questionDialog.SetText(localeInfo.AURA_NOTICE_DEL_ABSORDITEM)
						self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__UseItemAuraQuestionDialog_OnAccept))
						self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__UseItemAuraQuestionDialog_Close))
						self.questionDialog.srcItem = (player.INVENTORY, slotIndex)
						self.questionDialog.dstItem = (player.AURA_REFINE, AuraSlot)
						self.questionDialog.Open()

			elif player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_GROWTH:
				if UsingAuraSlot == player.AURA_SLOT_MAX:
					if AuraSlot == player.AURA_SLOT_MAIN:
						if item.GetItemType() == item.ITEM_TYPE_COSTUME:
							if item.GetItemSubType() == item.COSTUME_TYPE_AURA:
								socketLevelValue = player.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
								curLevel = (socketLevelValue // 100000) - 1000
								curExp = socketLevelValue % 100000;
								if curLevel >= player.AURA_MAX_LEVEL:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_MAX_LEVEL)
									return

								if curExp >= player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_NEED_EXP):
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_GROWTHITEM)
									return

								net.SendAuraRefineCheckIn(player.INVENTORY, slotIndex, player.AURA_REFINE, AuraSlot, player.GetAuraRefineWindowType())

							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
								return

						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
							return

					elif AuraSlot == player.AURA_SLOT_SUB:
						if player.FindUsingAuraSlot(player.AURA_SLOT_MAIN) != player.NPOS():
							if item.GetItemType() == item.ITEM_TYPE_RESOURCE:
								if item.GetItemSubType() == item.RESOURCE_AURA:
									if UsingAuraSlot == player.AURA_SLOT_MAX:
										if AuraSlot != player.AURA_SLOT_SUB:
											return

										net.SendAuraRefineCheckIn(player.INVENTORY, slotIndex, player.AURA_REFINE, AuraSlot, player.GetAuraRefineWindowType())
								else:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURARESOURCE)
									return

							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURARESOURCE)
								return

						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_REGISTER_AURAITEM)
							return

			elif player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_EVOLVE:
				if UsingAuraSlot == player.AURA_SLOT_MAX:
					if AuraSlot == player.AURA_SLOT_MAIN:
						if item.GetItemType() == item.ITEM_TYPE_COSTUME:
							if item.GetItemSubType() == item.COSTUME_TYPE_AURA:
								socketLevelValue = player.GetItemMetinSocket(slotIndex, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
								if auraprogression.Grade(AuraVnum) == 6:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_MAX_LEVEL)
									return

								if not auraprogression.IsReadyToEvolve(AuraVnum, socketLevelValue):
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EVOLUTION_ITEM)
									return

								if player.FindUsingAuraSlot(AuraSlot) != player.NPOS():
									return

								net.SendAuraRefineCheckIn(player.INVENTORY, slotIndex, player.AURA_REFINE, AuraSlot, player.GetAuraRefineWindowType())

							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
								return

						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
							return

					elif AuraSlot == player.AURA_SLOT_SUB:
						Cell = player.FindUsingAuraSlot(player.AURA_SLOT_MAIN)
						if Cell == player.NPOS():
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_REGISTER_AURAITEM)
							return

						auraVnum = player.GetItemIndex(Cell[0], Cell[1])
						socketLevelValue = player.GetItemMetinSocket(*(Cell + (player.ITEM_SOCKET_AURA_CURRENT_LEVEL,)))
						if auraprogression.Grade(auraVnum) == 6:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_MAX_LEVEL)
							return

						if not auraprogression.IsReadyToEvolve(auraVnum, socketLevelValue):
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EVOLUTION_ITEM)
							return

						gradeLevel = auraprogression.GradeLevel(auraVnum)
						if AuraVnum != player.GetAuraRefineInfo(gradeLevel, player.AURA_REFINE_INFO_MATERIAL_VNUM):
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EVOLUTION_ITEM)
							return

						if player.GetItemCount(slotIndex) < player.GetAuraRefineInfo(gradeLevel, player.AURA_REFINE_INFO_MATERIAL_COUNT):
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EVOLUTION_ITEMCOUNT)
							return

						if UsingAuraSlot == player.AURA_SLOT_MAX:
							if AuraSlot != player.AURA_SLOT_MAX:
								if player.FindUsingAuraSlot(AuraSlot) != player.NPOS():
									return

							net.SendAuraRefineCheckIn(player.INVENTORY, slotIndex, player.AURA_REFINE, AuraSlot, player.GetAuraRefineWindowType())

	if app.ENABLE_DSS_ACTIVE_EFFECT:
		def UseDSSButtonEffect(self, enable):
			return

	if app.ENABLE_BRAVE_CAPE_RENEWAL:
		def ClickBraveCape(self):
			if self.wndBraveCape:
				if self.wndBraveCape.IsShow():
					self.wndBraveCape.Close()
				else:
					self.wndBraveCape.Open()

	if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
		def OnUpdate(self):
			if osfInfo.MULTIPLE_MODE != -1:
				if self.wndItem:
					if not self.wndItem.IsLeftMouseClicked():
						osfInfo.MULTIPLE_MODE = -1

		def AddToMultipleList(self, slot, bSetMode = False, bPrintInfo = True):
			slot = int(slot)
				
			if slot in osfInfo.MULTIPLE_LIST:
				return
				
			if len(osfInfo.MULTIPLE_LIST) == 0:
				if self.wndMultiple.IsTypeSell() and not osfInfo.CanSellItem(slot):
					if osfInfo.CanDestroyItem(slot):
						self.wndMultiple.OnPressFragmentBtn()
					else:
						if bPrintInfo:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL_OR_DESTROY)
						return
				elif self.wndMultiple.IsTypeDestroy() and not osfInfo.CanDestroyItem(slot):
					if osfInfo.CanSellItem(slot):
						self.wndMultiple.OnPressSellBtn()
					else:
						if bPrintInfo:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL_OR_DESTROY)
						return
			else:
				if self.wndMultiple.IsTypeSell() and not osfInfo.CanSellItem(slot):
					if bPrintInfo:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL)
					return
					
				if self.wndMultiple.IsTypeDestroy() and not osfInfo.CanDestroyItem(slot):
					if bPrintInfo:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_DESTROY)
					return
						
			if bSetMode:
				osfInfo.MULTIPLE_MODE = osfInfo.MULTIPLE_MODE_ADD
						
			if self.wndMultiple.IsOpeningInventory() == False:
				self.wndMultiple.Show(True)
			
			osfInfo.MULTIPLE_LIST.append(int(slot))
			self.wndMultiple.UpdateItemCount(int(slot), 1)
			self.wndMultiple.UpdatePrice(int(slot), 1)
			
			self.interface.RefreshMarkInventoryBag()
			
		def RemoveFromMultipleList(self, slot):
			if slot in osfInfo.MULTIPLE_LIST:
				osfInfo.MULTIPLE_LIST.remove(int(slot))
				self.wndMultiple.UpdateItemCount(int(slot), 2)
				self.wndMultiple.UpdatePrice(int(slot), 2)
				self.RefreshBagSlotWindow()
				
				if len(osfInfo.MULTIPLE_LIST) < 1:
					self.wndMultiple.CloseInventory()

if app.ENABLE_BRAVE_CAPE_RENEWAL:
	import os
	class BraveCapeWindow(ui.Board):
		__children={}
		class SliderBarNew(ui.Window):
			def __init__(self):
				ui.Window.__init__(self)
				self.curPos = 1.0
				self.pageSize = 1.0
				self.eventChange = None
				self.__Load()

			def __Load(self):
				IMG_DIR = "d:/ymir work/ui/game/bravery_cape/"

				img = ui.ImageBox()
				img.SetParent(self)
				img.LoadImage(IMG_DIR+"slider_bg.tga")
				img.Show()
				self.backGroundImage = img

				self.SetSize(self.backGroundImage.GetWidth(), self.backGroundImage.GetHeight())

				cursor = ui.DragButton()
				cursor.AddFlag("movable")
				cursor.AddFlag("restrict_y")
				cursor.SetParent(self)
				cursor.SetMoveEvent(ui.__mem_func__(self.__OnMove))
				cursor.SetUpVisual(IMG_DIR+"drag.tga")
				cursor.SetOverVisual(IMG_DIR+"drag.tga")
				cursor.SetDownVisual(IMG_DIR+"drag.tga")
				cursor.Show()
				self.cursor = cursor

				##
				self.cursor.SetRestrictMovementArea(0, 0, self.backGroundImage.GetWidth(), 0)
				self.pageSize = self.backGroundImage.GetWidth() - self.cursor.GetWidth()

			def __OnMove(self):
				(xLocal, yLocal) = self.cursor.GetLocalPosition()
				self.curPos = float(xLocal) / float(self.pageSize)
				if self.eventChange:
					self.eventChange()
			def SetSliderPos(self, pos):
				self.curPos = pos
				self.cursor.SetPosition(int(self.pageSize * pos), 0)
			def GetSliderPos(self):
				return self.curPos
			def SetEvent(self, event):
				self.eventChange = event
			def Enable(self):
				self.cursor.Show()
			def Disable(self):
				self.cursor.Hide()

		def Destroy(self):
			self.SaveData()
			self.__children={}

		def CreateWindow(self, classPtr, parent, pos):
			window = classPtr
			window.SetParent(parent)
			window.SetPosition(*pos)
			window.Show()
			return window

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
					
		def __init__(self):
			ui.Board.__init__(self)
			self.SetSize(140, 130 + 44)
			self.AddFlag("attach")
			self.AddFlag("float")

			self.__children["firstOpened"] = app.GetGlobalTimeStamp() + 5

			IMG_DIR = "d:/ymir work/ui/game/bravery_cape/"

			BRAVE_CAPE_ITEM_IDX = 501002

			item.SelectItem(BRAVE_CAPE_ITEM_IDX)

			bgImg = self.CreateWindow(ui.ImageBox(), self, (5, 6))
			bgImg.LoadImage(IMG_DIR+"bg.tga")
			self.__children["bgImg"] = bgImg

			timeTextVisual = self.CreateWindow(ui.TextLine(), bgImg, (13, 60))
			timeTextVisual.SetText(localeInfo.BRAVE_CAPE_SECONDS)
			self.__children["timeTextVisual"] = timeTextVisual

			timeSlider = self.CreateWindow(self.SliderBarNew(), bgImg, (13, 73 + 5))
			timeSlider.SetEvent(ui.__mem_func__(self.OnChangeTimeSlider))
			self.__children["timeSlider"] = timeSlider

			timeBg = self.CreateWindow(ui.ImageBox(), bgImg, (77, 64))
			timeBg.LoadImage(IMG_DIR+"input_output.tga")
			self.__children["timeBg"] = timeBg

			timeText = self.CreateWindow(ui.TextLine(), timeBg, (0, 0))
			timeText.SetAllAlign()
			timeText.SetText("0")
			self.__children["timeText"] = timeText

			rangeTextVisual = self.CreateWindow(ui.TextLine(), bgImg, (13, 73 + 22 + 17 + 5 - 18))
			rangeTextVisual.SetText(localeInfo.BRAVE_CAPE_RANGE)
			self.__children["rangeTextVisual"] = rangeTextVisual

			rangeSlider = self.CreateWindow(self.SliderBarNew(), bgImg, (13, 73 + 22 + 17 + 5))
			rangeSlider.SetEvent(ui.__mem_func__(self.OnChangeRangeSlider))
			self.__children["rangeSlider"] = rangeSlider

			rangeBg = self.CreateWindow(ui.ImageBox(), bgImg, (77, 95 + 8))
			rangeBg.LoadImage(IMG_DIR+"input_output.tga")
			self.__children["rangeBg"] = rangeBg

			rangeText = self.CreateWindow(ui.TextLine(), rangeBg, (0, 0))
			rangeText.SetAllAlign()
			rangeText.SetText("0")
			self.__children["rangeText"] = rangeText

			itemIcon = self.CreateWindow(ui.ImageBox(), bgImg, (50, 13))
			itemIcon.LoadImage(item.GetIconImageFileName())
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.__OverOutItem)
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.__OverInItem, BRAVE_CAPE_ITEM_IDX)
			self.__children["itemIcon"] = itemIcon

			startBtn = self.CreateWindow(ui.Button(), bgImg, (6, 95 + 39))
			startBtn.SetUpVisual(IMG_DIR+"btn_start_0.png")
			startBtn.SetOverVisual(IMG_DIR+"btn_start_1.png")
			startBtn.SetDownVisual(IMG_DIR+"btn_start_2.png")
			startBtn.SetDisableVisual(IMG_DIR+"btn_start_0.png")
			startBtn.SAFE_SetEvent(self.__ClickStatusBtn, "ACTIVE")
			startBtn.SetText(localeInfo.BRAVE_CAPE_START)
			self.__children["startBtn"] = startBtn

			stopBtn = self.CreateWindow(ui.Button(), bgImg, (66, 95 + 39))
			stopBtn.SetUpVisual(IMG_DIR+"btn_stop_0.png")
			stopBtn.SetOverVisual(IMG_DIR+"btn_stop_1.png")
			stopBtn.SetDownVisual(IMG_DIR+"btn_stop_2.png")
			stopBtn.SetDisableVisual(IMG_DIR+"btn_stop_2.png")
			stopBtn.SAFE_SetEvent(self.__ClickStatusBtn, "DEACTIVE")
			stopBtn.SetText(localeInfo.BRAVE_CAPE_STOP)
			self.__children["stopBtn"] = stopBtn

			expandBtn = self.CreateWindow(ui.Button(), self, (-5, 30))
			expandBtn.SetUpVisual("d:/ymir work/ui/game/belt_inventory/btn_minimize_normal.tga")
			expandBtn.SetOverVisual("d:/ymir work/ui/game/belt_inventory/btn_minimize_over.tga")
			expandBtn.SetDownVisual("d:/ymir work/ui/game/belt_inventory/btn_minimize_down.tga")
			expandBtn.SAFE_SetEvent(self.Close)
			self.__children["expandBtn"] = expandBtn

			self.__children["second"] = 0
			self.__children["range"] = 0
			self.__children["status"] = False
			self.Refresh()

		def Refresh(self):
			(second, range, posTime, posSlider) = (self.__children["second"], self.__children["range"], 0.0, 0.0)
			if second > 5800:
				second = 5800
			if range > 7000:
				range = 7000

			self.__children["timeText"].SetText(str((second//100)+2))
			self.__children["rangeText"].SetText(str(range))

			self.__children["timeSlider"].SetSliderPos((1.0/5800.0)*second)
			self.__children["rangeSlider"].SetSliderPos((1.0/7000.0)*range)

			self.__children["second"] = second
			self.__children["range"] = range

		def Open(self):
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				if interface.wndInventory:
					interface.wndInventory.disbandBtn.Hide()
			self.Show()

		def Close(self):
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				if interface.wndInventory:
					interface.wndInventory.disbandBtn.Show()
			self.Hide()

		def __ClickStatusBtn(self, type):
			if type == "ACTIVE":
				net.SendChatPacket("/brave_cape active {} {}".format((self.__children["second"]//100)+2, self.__children["range"]))
			elif type == "DEACTIVE":
				net.SendChatPacket("/brave_cape deactive")

		def AdjustPosition(self, x, y):
			self.SetPosition(x+8 - self.GetWidth(), y + 180)

		if app.ENABLE_WINDOW_RESIZE:
			def OnResize(self):
				interface = osfInfo.GetInterfaceInstance()
				if interface and interface.wndInventory:
					self.AdjustPosition(*interface.wndInventory.GetInventoryBodyGlobalPosition())
		def OnChangeRangeSlider(self):
			val = int(((1.0/7000.0)*(self.__children["rangeSlider"].GetSliderPos()*7000))*7000)
			self.__children["range"] = val
			self.Refresh()
		def OnChangeTimeSlider(self):
			val = int(((1.0/5800.0)*(self.__children["timeSlider"].GetSliderPos()*5800))*5800)
			self.__children["second"] = val
			self.Refresh()
		def SetStatus(self, status):
			self.__children["status"] = True if int(status) == 1 else False
			if self.__children["status"]:
				self.__children["startBtn"].Disable()
				self.__children["stopBtn"].Enable()
			else:
				self.__children["stopBtn"].Disable()
				self.__children["startBtn"].Enable()
			self.Refresh()
		def SaveData(self):
			try:
				file = open("UserData/bravery_cape/{}.cfg".format(player.GetName()), "w+")
				file.write("{}#{}#{}\n".format(1 if (self.__children["status"] if "status" in self.__children else False) == True else 0, self.__children["second"], self.__children["range"]))
				file.close()
			except:
				pass
		def LoadData(self):
			try:
				splitList = open("UserData/bravery_cape/{}.cfg".format(player.GetName()), "r").readlines()[0].split("#")
				self.__children["status"] = True if int(splitList[0]) == 1 else False
				self.__children["second"] = int(splitList[1])
				self.__children["range"] = int(splitList[2])
				self.Refresh()
				if self.__children["status"]:
					self.__ClickStatusBtn("ACTIVE")
				os.remove("UserData/bravery_cape/{}.cfg".format(player.GetName()))
			except:
				pass
