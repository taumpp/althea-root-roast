import ui
import chr
import player
import app
import net

VIEW_EQUIP_EQUIPMENT_PAGE_SLOTS = (
	0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 20, 21, 25,
)

VIEW_EQUIP_COSTUME_PAGE_SLOTS = (
	11, 12, 13, 15, 16, 17, 22, 23, 24,
)

class EquipmentDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadDialog()

		self.vid = None
		self.eventClose = None
		self.itemDataDict = {}
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			self.refineElementDict = {}
		self.tooltipItem = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/EquipmentDialog.py")

			getObject = self.GetChild
			self.board = getObject("Board")
			self.maskEquipment = getObject("Equipment_Base")
			self.maskCostume = getObject("Costume_Base")
			self.slotWindow = getObject("EquipmentSlot")
			self.costumeSlotWindow = getObject("CostumeSlot")

			self.imageTab = []
			self.imageTab.append(getObject("window_tabs_1"))
			self.imageTab.append(getObject("window_tabs_2"))

			self.equipmentTab = []
			self.equipmentTab.append(getObject("ViewEquip_Tab_01"))
			self.equipmentTab.append(getObject("ViewEquip_Tab_02"))

		except:
			import exception
			exception.Abort("EquipmentDialog.LoadDialog.BindObject")

		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.slotWindow.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.slotWindow.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.costumeSlotWindow.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.costumeSlotWindow.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		self.equipmentTab[0].SetEvent(lambda arg=0: self.SetEquipmentPage(arg))
		self.equipmentTab[1].SetEvent(lambda arg=1: self.SetEquipmentPage(arg))

	def SetEquipmentPage(self, page):
		self.maskEquipment.Hide()
		self.maskCostume.Hide()
		for i in range(2):
			self.imageTab[i].Hide()
			self.equipmentTab[i].SetUp()

		if page == 0:
			self.maskEquipment.Show()
			self.imageTab[0].Show()
			self.equipmentTab[0].Down()
		else:
			self.maskCostume.Show()
			self.imageTab[1].Show()
			self.equipmentTab[1].Down()

	def __GetSlotWindow(self, slotIndex):
		if slotIndex in VIEW_EQUIP_COSTUME_PAGE_SLOTS:
			return self.costumeSlotWindow
		return self.slotWindow

	def Open(self, vid):
		self.vid = vid
		self.itemDataDict = {}
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			self.refineElementDict = {}

		name = chr.GetNameByVID(vid)
		self.board.SetTitleName(name)

		self.SetCenterPosition()
		self.SetTop()
		self.SetEquipmentPage(0)
		self.Show()

	def Close(self):
		self.itemDataDict = {}
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			self.refineElementDict = {}
		self.tooltipItem = None
		self.Hide()

		if self.eventClose:
			self.eventClose(self.vid)

	def Destroy(self):
		self.eventClose = None
		self.Close()
		self.ClearDictionary()

		self.board = None
		self.slotWindow = None
		self.costumeSlotWindow = None
		self.maskEquipment = None
		self.maskCostume = None

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def SetEquipmentDialogItem(self, slotIndex, vnum, count, dwChangeLookVnum):
			if count <= 1:
				count = 0

			slotWindow = self.__GetSlotWindow(slotIndex)
			slotWindow.SetItemSlot(slotIndex, vnum, count)

			emptySocketList = []
			emptyAttrList = []
			if app.ENABLE_APPLY_RANDOM:
				emptyApplyRandomList = []

			for i in range(player.METIN_SOCKET_MAX_NUM):
				emptySocketList.append(0)
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				emptyAttrList.append((0, 0))

			if app.ENABLE_APPLY_RANDOM:
				for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
					emptyApplyRandomList.append((0, 0))
				self.itemDataDict[slotIndex] = (vnum, count, emptySocketList, emptyAttrList, emptyApplyRandomList, dwChangeLookVnum)
			else:
				self.itemDataDict[slotIndex] = (vnum, count, emptySocketList, emptyAttrList, dwChangeLookVnum)

			if not dwChangeLookVnum == 0:
				slotWindow.SetSlotCoverImage(slotIndex, "icon/item/ingame_convert_Mark.tga")
			else:
				slotWindow.EnableSlotCoverImage(slotIndex, False)
	else:
		def SetEquipmentDialogItem(self, slotIndex, vnum, count):
			if count <= 1:
				count = 0

			slotWindow = self.__GetSlotWindow(slotIndex)
			slotWindow.SetItemSlot(slotIndex, vnum, count)

			emptySocketList = []
			emptyAttrList = []
			for i in range(player.METIN_SOCKET_MAX_NUM):
				emptySocketList.append(0)
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				emptyAttrList.append((0, 0))
			self.itemDataDict[slotIndex] = (vnum, count, emptySocketList, emptyAttrList)

	def SetEquipmentDialogSocket(self, slotIndex, socketIndex, value):
		if not slotIndex in self.itemDataDict:
			return
		if socketIndex < 0 or socketIndex > player.METIN_SOCKET_MAX_NUM:
			return
		self.itemDataDict[slotIndex][2][socketIndex] = value

	def SetEquipmentDialogAttr(self, slotIndex, attrIndex, type, value):
		if not slotIndex in self.itemDataDict:
			return
		if attrIndex < 0 or attrIndex > player.ATTRIBUTE_SLOT_MAX_NUM:
			return
		self.itemDataDict[slotIndex][3][attrIndex] = (type, value)

	if app.ENABLE_APPLY_RANDOM:
		def SetEquipmentDialogApplyRandom(self, slotIndex, ApplyRandomIndex, type, value):
			if not slotIndex in self.itemDataDict:
				return
			if ApplyRandomIndex < 0 or ApplyRandomIndex > player.APPLY_RANDOM_SLOT_MAX_NUM:
				return
			self.itemDataDict[slotIndex][4][ApplyRandomIndex] = (type, value)

	if app.ENABLE_REFINE_ELEMENT_SYSTEM:
		def SetEquipmentDialogRefineElement(self, slotIndex, applyType, grade, values, bonusValues):
			if not slotIndex in self.itemDataDict:
				return
			self.refineElementDict[slotIndex] = (applyType, grade, values, bonusValues)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetCloseEvent(self, event):
		self.eventClose = event

	def OverInItem(self, slotIndex):
		if None == self.tooltipItem:
			return

		if not slotIndex in self.itemDataDict:
			return

		itemVnum = self.itemDataDict[slotIndex][0]
		if 0 == itemVnum:
			return

		self.tooltipItem.ClearToolTip()
		metinSlot = self.itemDataDict[slotIndex][2]
		attrSlot = self.itemDataDict[slotIndex][3]
		refine_element = self.refineElementDict.get(slotIndex) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
		if app.ENABLE_APPLY_RANDOM:
			aApplyRandom = self.itemDataDict[slotIndex][4]
			self.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot, refine_element=refine_element, apply_random_list=aApplyRandom,
				rarity_key=(getattr(net, "RARITY_CONTEXT_EQUIPMENT", 4), 0, slotIndex, self.vid, 0))
		else:
			self.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot, refine_element=refine_element,
				rarity_key=(getattr(net, "RARITY_CONTEXT_EQUIPMENT", 4), 0, slotIndex, self.vid, 0))

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if app.ENABLE_APPLY_RANDOM:
				self.tooltipItem.AppendChangeLookInfoItemVnum(self.itemDataDict[slotIndex][5])
			else:
				self.tooltipItem.AppendChangeLookInfoItemVnum(self.itemDataDict[slotIndex][4])
		self.tooltipItem.ShowToolTip()

	def OverOutItem(self):
		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True
