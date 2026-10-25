import dungeonequipmentbinding
import item
import dbg
import mouseModule
import net
import player
import snd
import ui
import uiScriptLocale


TALISMAN_EQUIPMENT_CELL_NAMES = (
	"EQUIPMENT_TALISMAN_HUNTER",
	"EQUIPMENT_TALISMAN_GUARDIAN",
	"EQUIPMENT_TALISMAN_BREAKER",
	"EQUIPMENT_TALISMAN_PROTECTOR",
	"EQUIPMENT_TALISMAN_CONQUEROR",
	"EQUIPMENT_TALISMAN_HEART",
)
TALISMAN_EQUIPMENT_CELLS = tuple(
	getattr(item, name, -1) for name in TALISMAN_EQUIPMENT_CELL_NAMES
)
TALISMAN_HEART_CELL = TALISMAN_EQUIPMENT_CELLS[-1]
TALISMAN_WATERMARK_NAMES = (
	"TalismanWatermarkHunter",
	"TalismanWatermarkGuardian",
	"TalismanWatermarkBreaker",
	"TalismanWatermarkProtector",
	"TalismanWatermarkConqueror",
	"TalismanWatermarkHeart",
)
TALISMAN_FAMILY_RANGES = (
	(9600, 9650),
	(9830, 9880),
	(10060, 10110),
	(10290, 10340),
	(10520, 10570),
)


def TalismanCellForVnum(vnum):
	for index, familyRange in enumerate(TALISMAN_FAMILY_RANGES):
		if familyRange[0] <= vnum <= familyRange[1]:
			return TALISMAN_EQUIPMENT_CELLS[index]
	if 10750 <= vnum <= 10754:
		return TALISMAN_HEART_CELL
	return -1


def IsHeartActive():
	heartVnum = player.GetItemIndex(TALISMAN_HEART_CELL)
	if heartVnum < 10750 or heartVnum > 10754:
		return False
	requiredRefine = 25
	for equipmentCell, familyRange in zip(
		TALISMAN_EQUIPMENT_CELLS[:-1], TALISMAN_FAMILY_RANGES
	):
		vnum = player.GetItemIndex(equipmentCell)
		if vnum < familyRange[0] or vnum > familyRange[1]:
			return False
		if vnum - familyRange[0] < requiredRefine:
			return False
	return True


def IsSupported():
	return (
		all(cell >= 0 for cell in TALISMAN_EQUIPMENT_CELLS)
		and len(set(TALISMAN_EQUIPMENT_CELLS)) == 6
	)


class TalismanWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.Children = []
		self.dungeonLockOverlays = {}
		self.ElementDictionary = {}
		self.tooltipItem = None
		self.capability = False
		self.closeEvent = None
		self.r1 = None
		self.r1Failed = False
		self.isLoaded = self.__LoadWindow()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def ClearDictionary(self):
		self.Children = []
		self.ElementDictionary = {}

	def InsertChild(self, name, child):
		self.ElementDictionary[name] = child

	def GetChild(self, name):
		return self.ElementDictionary[name]

	def __LoadWindow(self):
		path = uiScriptLocale.LOCALE_UISCRIPT_PATH + "talismanwindow.py"
		loader = ui.PythonScriptLoader()
		try:
			if not loader.LoadScriptFile(self, path, False):
				dbg.TraceError("TalismanWindow.LoadScript path=%s" % path)
				return False
		except Exception as error:
			dbg.TraceError(
				"TalismanWindow.LoadScript path=%s error=%s" % (path, error)
			)
			return False

		children = {}
		for childName in (
			"TalismanSlots", "TalismanActive"
		) + TALISMAN_WATERMARK_NAMES:
			try:
				children[childName] = self.GetChild(childName)
			except Exception as error:
				dbg.TraceError(
					"TalismanWindow.BindChild child=%s error=%s" %
					(childName, error)
				)
				return False
		self.slots = children["TalismanSlots"]
		self.activeImage = children["TalismanActive"]
		self.watermarks = dict(zip(
			TALISMAN_EQUIPMENT_CELLS,
			(children[name] for name in TALISMAN_WATERMARK_NAMES),
		))
		self.SetTitleName(
			getattr(uiScriptLocale, "TALISMAN_WINDOW_TITLE", "Talismans")
		)
		ui.BoardWithTitleBar.SetCloseEvent(
			self, ui.__mem_func__(self.__RequestClose)
		)
		self.slots.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		self.slots.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		self.slots.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		self.slots.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		self.slots.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.slots.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.activeImage.Hide()
		return True

	def IsLoaded(self):
		return self.isLoaded

	def __SyncLook(self):
		"""The R1 look (root/uitalismanr1.py) unless Settings -> "Starý vzhled" chose the original window; the switch
		takes effect on the next opening. A failure traces to syserr and keeps the original look (not retried)."""
		try:
			import uir1
			wanted = uir1.UseR1() and not self.r1Failed
		except Exception:
			wanted = False
		if wanted and not self.r1:
			try:
				import uitalismanr1
				self.r1 = uitalismanr1.TalismanSkin(self)
			except Exception:
				uir1.TraceFailure("the talisman window")
				self.r1Failed = True
				self.r1 = None
		elif not wanted and self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetCloseEvent(self, closeEvent):
		self.closeEvent = closeEvent

	def __RequestClose(self):
		if self.closeEvent:
			self.closeEvent()
		else:
			self.Close()

	def SetCapability(self, enabled):
		self.capability = bool(enabled)
		if not self.capability:
			self.Close()

	def Refresh(self):
		dungeonequipmentbinding.HideWindow(self.dungeonLockOverlays, self.slots)
		for equipmentCell in TALISMAN_EQUIPMENT_CELLS:
			vnum = player.GetItemIndex(equipmentCell)
			if vnum:
				self.slots.SetItemSlot(equipmentCell, vnum, 0)
				dungeonequipmentbinding.SetOverlay(self.dungeonLockOverlays, self.slots, equipmentCell, equipmentCell, vnum)
				self.watermarks[equipmentCell].Hide()
			else:
				self.slots.ClearSlot(equipmentCell)
				self.watermarks[equipmentCell].Show()
		self.slots.RefreshSlot()
		if IsHeartActive():
			self.activeImage.Show()
		else:
			self.activeImage.Hide()

	def SelectEmptySlot(self, equipmentCell):
		if not self.capability or not mouseModule.mouseController.isAttached():
			return
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			return
		sourceCell = mouseModule.mouseController.GetAttachedSlotNumber()
		if player.IsEquipmentSlot(sourceCell):
			return
		vnum = player.GetItemIndex(sourceCell)
		if TalismanCellForVnum(vnum) != equipmentCell:
			return
		net.SendItemUsePacket(sourceCell)
		mouseModule.mouseController.DeattachObject()

	def SelectItemSlot(self, equipmentCell):
		if not self.capability:
			return
		if mouseModule.mouseController.isAttached():
			self.SelectEmptySlot(equipmentCell)
			return
		vnum = player.GetItemIndex(equipmentCell)
		if not vnum:
			return
		mouseModule.mouseController.AttachObject(
			self, player.SLOT_TYPE_INVENTORY, equipmentCell, vnum, 1
		)
		snd.PlaySound("sound/ui/pick.wav")

	def UseItemSlot(self, equipmentCell):
		if not self.capability:
			return
		if mouseModule.mouseController.isAttached():
			self.SelectEmptySlot(equipmentCell)
			return
		if player.GetItemIndex(equipmentCell):
			net.SendItemUsePacket(equipmentCell)

	def OverInItem(self, equipmentCell):
		if self.tooltipItem:
			self.tooltipItem.SetInventoryItem(equipmentCell)

	def OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def Open(self):
		if not self.capability:
			return False
		if self.isLoaded:
			self.__SyncLook()
		self.Refresh()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()
		return True

	def Toggle(self):
		if self.IsShow():
			self.Close()
			return True
		return self.Open()

	def Close(self):
		self.OverOutItem()
		self.Hide()

	def Destroy(self):
		dungeonequipmentbinding.Clear(getattr(self, "dungeonLockOverlays", {}))
		self.Close()
		if getattr(self, "r1", None):
			r1, self.r1 = self.r1, None
			r1.Destroy()
		self.tooltipItem = None
		self.closeEvent = None
		self.slots = None
		self.activeImage = None
		self.watermarks = {}
		self.ClearDictionary()

	def OnPressEscapeKey(self):
		self.__RequestClose()
		return True
