import chat
import item
import localeInfo
import mouseModule
import net
import player
import resonanceuihelpers
import ui
import ownedcount


RESONANCE_SLOT_COUNT = 3
RESONANCE_SEAL_FIRST = 79640
RESONANCE_SEAL_LAST = 79681
RESONANCE_CONTEXT_INVENTORY = 1
SUPPORTED_ARMOR_SUBTYPES = (item.ARMOR_HEAD, item.ARMOR_SHIELD, item.ARMOR_FOOTS)
SLOT_IMAGE = "d:/ymir work/ui/game/crimson_ember/inventory/item_slot_framed.sub"
ITEM_MAX_COUNT = 9999
RESONANCE_RESULT_MESSAGES = {
	getattr(net, "RESONANCE_RESULT_DISABLED", 1): ("RESONANCE_SYSTEM_UNAVAILABLE", "The resonance seal system is unavailable."),
	getattr(net, "RESONANCE_RESULT_BUSY", 2): ("RESONANCE_BUSY", "Another resonance action is still running."),
	getattr(net, "RESONANCE_RESULT_INVALID_HOST", 3): ("RESONANCE_INVALID_HOST", "Invalid resonance item."),
	getattr(net, "RESONANCE_RESULT_INVALID_SEAL", 4): ("RESONANCE_INVALID_SEAL", "This seal is no longer available or compatible."),
	getattr(net, "RESONANCE_RESULT_INVALID_SLOT", 5): ("RESONANCE_INVALID_SLOT", "The selected resonance slot is no longer valid."),
	getattr(net, "RESONANCE_RESULT_LOCKED_SLOT", 6): ("RESONANCE_SLOT_LOCKED", "This resonance slot is locked."),
	getattr(net, "RESONANCE_RESULT_OCCUPIED_SLOT", 7): ("RESONANCE_SLOT_OCCUPIED", "This resonance slot is already occupied."),
	getattr(net, "RESONANCE_RESULT_DUPLICATE_FAMILY", 8): ("RESONANCE_DUPLICATE_FAMILY", "This seal family is already inserted."),
	getattr(net, "RESONANCE_RESULT_INVENTORY_FULL", 9): ("RESONANCE_INVENTORY_FULL", "Free an inventory slot before removing this seal."),
	getattr(net, "RESONANCE_RESULT_CORRUPT_STATE", 10): ("RESONANCE_CORRUPT_STATE", "This item's resonance state requires administrator repair."),
	getattr(net, "RESONANCE_RESULT_TARGET_CHANGED", 11): ("RESONANCE_TARGET_CHANGED", "The selected item changed. Select it again."),
	getattr(net, "RESONANCE_RESULT_ALREADY_UNLOCKED", 12): ("RESONANCE_ALREADY_UNLOCKED", "This resonance slot is already unlocked."),
	getattr(net, "RESONANCE_RESULT_PREVIOUS_SLOT_LOCKED", 13): ("RESONANCE_PREVIOUS_SLOT_LOCKED", "Unlock the previous resonance slot first."),
	getattr(net, "RESONANCE_RESULT_NOT_ENOUGH_KEYS", 14): ("RESONANCE_NOT_ENOUGH_KEYS", "You do not have enough Resonance Keys."),
	getattr(net, "RESONANCE_RESULT_NOT_ENOUGH_YANG", 15): ("RESONANCE_NOT_ENOUGH_YANG", "You do not have enough Yang."),
}


def _YangText(amount):
	"""The cost as the one R1 yang price of the client ("1.000.000 Yang", root/uir1price.py
	) beside the window's own coin; "Starý vzhled" keeps localeInfo.NumberToMoneyString."""
	try:
		import uir1price
		return uir1price.Text(amount, lambda: localeInfo.NumberToMoneyString(amount))
	except Exception:
		return localeInfo.NumberToMoneyString(amount)


def _Locale(key, fallback):
	return getattr(localeInfo, key, fallback)


def IsSealVnum(vnum):
	return RESONANCE_SEAL_FIRST <= int(vnum) <= RESONANCE_SEAL_LAST


def IsResonanceKey(vnum):
	return resonanceuihelpers.IsResonanceKey(vnum)


def SealFamily(vnum):
	if not IsSealVnum(vnum):
		return -1
	return (int(vnum) - RESONANCE_SEAL_FIRST) // 6


def IsSupportedHostVnum(vnum):
	if not vnum:
		return False
	item.SelectItem(int(vnum))
	return item.GetItemType() == item.ITEM_TYPE_ARMOR and item.GetItemSubType() in SUPPORTED_ARMOR_SUBTYPES


def _HasSealDestination(vnum):
	for cell in range(player.INVENTORY_SLOT_COUNT):
		itemVnum = player.GetItemIndex(player.INVENTORY, cell)
		if not itemVnum:
			return True
		if int(itemVnum) == int(vnum) and player.GetItemCount(player.INVENTORY, cell) < ITEM_MAX_COUNT:
			return True
	return False


class ResonanceUnlockDialog(ui.ScriptWindow):
	YANG_BAR_IMAGE = "d:/ymir work/ui/game/crimson_ember/inventory/currency_footer.png"
	YANG_BAR_X = 38
	YANG_BAR_WIDTH = 228
	YANG_BAR_SOURCE_WIDTH = 160.0
	YANG_BAR_HEIGHT = 23

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'acceptButton')
		self.targetWindow = player.INVENTORY
		self.targetCell = -1
		self.targetInstanceId = 0
		self.targetSlot = -1
		self.hostVnum = 0
		self.keyVnum = 0
		self.tooltipItem = None
		self.yangParts = []
		self.__LoadWindow()

	def __LoadWindow(self):
		try:
			loader = ui.PythonScriptLoader()
			loader.LoadScriptFile(self, "uiscript/resonanceunlockdialog.py")
		except:
			import exception
			exception.Abort("ResonanceUnlockDialog.__LoadWindow.LoadObject")

		try:
			self.titleBar = self.GetChild("TitleBar")
			self.currentItemSlot = self.GetChild("CurrentItemSlot")
			self.resultItemSlot = self.GetChild("ResultItemSlot")
			self.materialSlot = self.GetChild("MaterialSlot")
			self.materialName = self.GetChild("MaterialName")
			self.materialCount = self.GetChild("MaterialCount")
			self.yangPanel = self.GetChild("YangPanel")
			self.slotText = self.GetChild("SlotText")
			self.acceptButton = self.GetChild("AcceptButton")
			self.cancelButton = self.GetChild("CancelButton")
		except:
			import exception
			exception.Abort("ResonanceUnlockDialog.__LoadWindow.BindObject")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		self.acceptButton.SetEvent(ui.__mem_func__(self.__Accept))
		self.cancelButton.SetEvent(ui.__mem_func__(self.Close))
		self.currentItemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInHost))
		self.currentItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		self.resultItemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInHost))
		self.resultItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		self.materialSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInKey))
		self.materialSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		self.__CreateYangRow()
		self.Hide()

	def __CreateYangRow(self):
		background = ui.ExpandedImageBox()
		background.SetParent(self.yangPanel)
		background.SetPosition(self.YANG_BAR_X, 0)
		background.LoadImage(self.YANG_BAR_IMAGE)
		background.SetScale(
			float(self.YANG_BAR_WIDTH) / self.YANG_BAR_SOURCE_WIDTH, 1.0
		)
		background.AddFlag("not_pick")
		background.Show()

		moneyIcon = ui.ImageBox()
		moneyIcon.SetParent(self.yangPanel)
		moneyIcon.SetPosition(20, (self.YANG_BAR_HEIGHT - 16) // 2)
		moneyIcon.LoadImage("d:/ymir work/ui/game/crimson_ember/inventory/icon_yang.png")
		moneyIcon.AddFlag("not_pick")
		moneyIcon.Show()

		self.costText = ui.TextLine()
		self.costText.SetParent(self.yangPanel)
		self.costText.SetPosition(
			self.YANG_BAR_X + self.YANG_BAR_WIDTH - 5,
			self.YANG_BAR_HEIGHT // 2,
		)
		self.costText.SetHorizontalAlignRight()
		self.costText.SetVerticalAlignCenter()
		self.costText.SetOutline()
		self.costText.AddFlag("not_pick")
		self.costText.Show()
		self.yangParts = [background, moneyIcon, self.costText]

	def Destroy(self):
		self.Close()
		self.ClearDictionary()
		self.tooltipItem = None
		self.yangParts = []

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def Open(self, targetWindow, targetCell, targetInstanceId, targetSlot,
			hostVnum, keyVnum, requiredKeyCount, yangCost):
		if getattr(net, "IsResonanceMutationPending", lambda: False)():
			return False
		if int(targetInstanceId) <= 0 or int(targetSlot) not in range(RESONANCE_SLOT_COUNT):
			return False
		self.targetWindow = int(targetWindow)
		self.targetCell = int(targetCell)
		self.targetInstanceId = int(targetInstanceId)
		self.targetSlot = int(targetSlot)
		self.hostVnum = int(hostVnum)
		self.keyVnum = int(keyVnum)

		for slotWindow in (self.currentItemSlot, self.resultItemSlot):
			for slotIndex in range(3):
				slotWindow.ClearSlot(slotIndex)
				slotWindow.DeactivateSlot(slotIndex)
			slotWindow.SetItemSlot(0, self.hostVnum, 0)
			slotWindow.RefreshSlot()
		self.resultItemSlot.ActivateSlot(self.targetSlot)
		self.resultItemSlot.RefreshSlot()

		self.materialSlot.ClearSlot(0)
		self.materialSlot.SetItemSlot(0, self.keyVnum, 0)
		self.materialSlot.RefreshSlot()
		item.SelectItem(self.keyVnum)
		self.materialName.SetText(item.GetItemName())
		# "owned / need" green / red (root/ownedcount.py)
		self.requiredKeyCount = int(requiredKeyCount)
		ownedcount.Paint(self.materialCount, ownedcount.Owned(self.keyVnum), self.requiredKeyCount)
		self.costText.SetText(_YangText(int(yangCost)))
		self.slotText.SetText(u"%d. %s -> %s" % (
			self.targetSlot + 1,
			_Locale("RESONANCE_LOCKED_SLOT", "Locked"),
			_Locale("RESONANCE_EMPTY_SLOT", "Empty"),
		))
		self.SetTop()
		self.Show()
		return True

	def RefreshOwnedCounts(self):
		"""The keys' "owned / need" again (the interface calls it when the inventory changes)."""
		if getattr(self, "keyVnum", 0) and getattr(self, "requiredKeyCount", 0):
			ownedcount.Paint(self.materialCount, ownedcount.Owned(self.keyVnum), self.requiredKeyCount)

	def Close(self):
		self.Hide()
		self.targetCell = -1
		self.targetInstanceId = 0
		self.targetSlot = -1
		self.hostVnum = 0
		self.keyVnum = 0
		self.__OverOutItem()

	def __Accept(self):
		if self.targetCell < 0 or self.targetInstanceId <= 0 or self.targetSlot < 0:
			return
		if getattr(net, "IsResonanceMutationPending", lambda: False)():
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_BUSY", "Another resonance action is still running."
			))
			return
		if net.UnlockResonanceSlot(
			self.targetWindow, self.targetCell,
			self.targetInstanceId, self.targetSlot,
		):
			self.Close()

	def __OverInHost(self, unusedSlot=0):
		if self.tooltipItem and self.targetCell >= 0:
			self.tooltipItem.SetInventoryItem(self.targetCell, self.targetWindow)

	def __OverInKey(self, unusedSlot=0):
		if self.tooltipItem and self.keyVnum:
			self.tooltipItem.SetItemToolTip(self.keyVnum)

	def __OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class ResonanceWindow(ui.BoardWithTitleBar):
	WIDTH = 332
	HEIGHT = 206

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetCenterPosition()
		self.SetTitleName(_Locale("RESONANCE_WINDOW_TITLE", "Resonance Seals"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.targetWindow = player.INVENTORY
		self.targetCell = -1
		self.targetVnum = 0
		self.targetInstanceId = 0
		self.pendingSealCell = None
		self.unlockedMask = 0
		self.metadataSlots = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
		self.tooltipItem = None
		self.unlockDialog = ResonanceUnlockDialog()
		self.children = []
		self.__Build()
		self.Hide()

	def __MakeText(self, x, y, text, center=False, color=None):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		if color is not None:
			line.SetPackedFontColor(color)
		line.SetText(text)
		line.Show()
		self.children.append(line)
		return line

	def __Build(self):
		self.instruction = self.__MakeText(
			self.WIDTH // 2, 36,
			_Locale("RESONANCE_SELECT_ITEM", "Insert a helmet, shield or boots."),
			True,
		)
		self.hostSlot = ui.SlotWindow()
		self.hostSlot.SetParent(self)
		self.hostSlot.SetPosition(27, 66)
		self.hostSlot.SetSize(32, 32)
		self.hostSlot.AppendSlot(0, 0, 0, 32, 32)
		self.hostSlot.SetSlotBaseImage(SLOT_IMAGE, 1.0, 1.0, 1.0, 1.0)
		self.hostSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__SelectHost))
		self.hostSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectHost))
		self.hostSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInHost))
		self.hostSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		self.hostSlot.Show()
		self.children.append(self.hostSlot)
		self.__MakeText(43, 104, _Locale("RESONANCE_HOST", "Item"), True, 0xffaaa39a)

		self.sealSlots = ui.SlotWindow()
		self.sealSlots.SetParent(self)
		self.sealSlots.SetPosition(108, 66)
		self.sealSlots.SetSize(164, 32)
		for slotIndex in range(RESONANCE_SLOT_COUNT):
			self.sealSlots.AppendSlot(slotIndex, slotIndex * 64, 0, 32, 32)
		self.sealSlots.SetSlotBaseImage(SLOT_IMAGE, 1.0, 1.0, 1.0, 1.0)
		self.sealSlots.SetSelectEmptySlotEvent(ui.__mem_func__(self.__InsertSeal))
		self.sealSlots.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectSeal))
		self.sealSlots.SetUnselectItemSlotEvent(ui.__mem_func__(self.__RemoveSeal))
		self.sealSlots.SetUseSlotEvent(ui.__mem_func__(self.__RemoveSeal))
		self.sealSlots.SetOverInItemEvent(ui.__mem_func__(self.__OverInSeal))
		self.sealSlots.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		self.sealSlots.Show()
		self.children.append(self.sealSlots)

		self.slotLabels = []
		for slotIndex in range(RESONANCE_SLOT_COUNT):
			label = self.__MakeText(124 + slotIndex * 64, 104, "", True, 0xffaaa39a)
			self.slotLabels.append(label)
		self.removeHint = self.__MakeText(
			self.WIDTH // 2, 143,
			_Locale("RESONANCE_REMOVE_HINT", "Right-click a seal to remove it."),
			True, 0xffaaa39a,
		)

	def Destroy(self):
		self.Close()
		if self.unlockDialog:
			self.unlockDialog.Destroy()
		self.unlockDialog = None
		self.children = []
		self.slotLabels = []
		self.hostSlot = None
		self.sealSlots = None
		self.tooltipItem = None

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem
		if self.unlockDialog:
			self.unlockDialog.SetItemToolTip(tooltipItem)

	def SetTarget(self, targetCell, pendingSealCell=None):
		vnum = player.GetItemIndex(player.INVENTORY, int(targetCell))
		if not IsSupportedHostVnum(vnum):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_INVALID_HOST", "Invalid resonance item."))
			return False
		self.__CloseUnlockDialog()
		self.targetWindow = player.INVENTORY
		self.targetCell = int(targetCell)
		self.targetVnum = int(vnum)
		self.targetInstanceId = 0
		self.pendingSealCell = pendingSealCell
		self.hostSlot.SetItemSlot(0, vnum, 0)
		self.hostSlot.RefreshSlot()
		self.Refresh()
		return True

	def Open(self, targetCell=None, pendingSealCell=None):
		if not getattr(net, "IsResonanceAvailable", lambda: False)():
			return False
		if targetCell is not None:
			if not self.SetTarget(targetCell, pendingSealCell):
				return False
		else:
			self.__ResetTarget()
		self.Show()
		self.SetTop()
		self.Refresh()
		return True

	def InsertResonanceSealDirect(self, targetCell, sourceCell):
		if not getattr(net, "IsResonanceAvailable", lambda: False)():
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_SYSTEM_UNAVAILABLE", "The resonance seal system is unavailable."
			))
			return False
		if getattr(net, "IsResonanceMutationPending", lambda: False)():
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_BUSY", "Another resonance action is still running."
			))
			return False

		targetCell = int(targetCell)
		sourceCell = int(sourceCell)
		sealVnum = player.GetItemIndex(player.INVENTORY, sourceCell)
		if not IsSealVnum(sealVnum):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_INVALID_SEAL", "This seal is no longer available or compatible."
			))
			return False
		if not IsSupportedHostVnum(player.GetItemIndex(player.INVENTORY, targetCell)):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_INVALID_HOST", "Invalid resonance item."
			))
			return False

		try:
			instanceId, unlockedMask, metadataSlots = resonanceuihelpers.NormalizeMetadata(
				net.GetResonanceMetadata(
					RESONANCE_CONTEXT_INVENTORY, player.INVENTORY,
					targetCell, 0, 0,
				)
			)
		except (AttributeError, RuntimeError, TypeError, ValueError):
			instanceId, unlockedMask, metadataSlots = resonanceuihelpers.EMPTY_METADATA
		if not int(instanceId):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_TARGET_CHANGED", "The selected item changed. Select it again."
			))
			return False

		families = [SealFamily(row[0]) for row in metadataSlots if row[0]]
		if SealFamily(sealVnum) in families:
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_DUPLICATE_FAMILY", "Duplicate seal family."
			))
			return False
		slotIndex = resonanceuihelpers.FirstUnlockedEmptySlot(unlockedMask, metadataSlots)
		if slotIndex is None:
			if int(unlockedMask) != 7:
				chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
					"RESONANCE_SLOT_LOCKED", "This resonance slot is locked."
				))
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
					"RESONANCE_SLOT_OCCUPIED", "This resonance slot is already occupied."
				))
			return False

		if net.InsertResonanceSeal(
			player.INVENTORY, sourceCell, player.INVENTORY,
			targetCell, int(instanceId), int(slotIndex),
		):
			mouseModule.mouseController.DeattachObject()
			return True
		return False

	def OpenUnlockFromKey(self, targetCell, sourceKeyCell):
		if not getattr(net, "IsResonanceAvailable", lambda: False)():
			return False
		if getattr(net, "IsResonanceMutationPending", lambda: False)():
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_BUSY", "Another resonance action is still running."
			))
			return False
		if not IsResonanceKey(
			player.GetItemIndex(player.INVENTORY, int(sourceKeyCell))
		):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_NOT_ENOUGH_KEYS", "You do not have enough Resonance Keys."
			))
			return False
		if not self.SetTarget(targetCell):
			return False
		targetSlot = resonanceuihelpers.NextLockedSlot(self.unlockedMask)
		if targetSlot is None:
			key = "RESONANCE_ALREADY_UNLOCKED" if self.unlockedMask == 7 else "RESONANCE_CORRUPT_STATE"
			fallback = "All resonance slots are already unlocked." if self.unlockedMask == 7 else "This item's resonance state requires administrator repair."
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(key, fallback))
			return False
		if not self.targetInstanceId:
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(
				"RESONANCE_TARGET_CHANGED", "The selected item changed. Select it again."
			))
			return False
		return self.__OpenUnlockDialog(targetSlot)

	def Close(self):
		self.__CloseUnlockDialog()
		self.pendingSealCell = None
		self.Hide()

	def ResetRuntime(self):
		self.Close()
		self.__ResetTarget()

	def __ResetTarget(self):
		self.__CloseUnlockDialog()
		self.targetCell = -1
		self.targetVnum = 0
		self.targetInstanceId = 0
		self.pendingSealCell = None
		self.unlockedMask = 0
		self.metadataSlots = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
		if self.hostSlot:
			self.hostSlot.ClearSlot(0)
			self.hostSlot.RefreshSlot()
		if self.sealSlots:
			for slotIndex in range(RESONANCE_SLOT_COUNT):
				self.sealSlots.ClearSlot(slotIndex)
				self.sealSlots.DeactivateSlot(slotIndex)
				self.slotLabels[slotIndex].SetText("")
			self.sealSlots.RefreshSlot()

	def Refresh(self):
		if self.targetCell < 0:
			return
		currentVnum = player.GetItemIndex(self.targetWindow, self.targetCell)
		if int(currentVnum) != self.targetVnum or not IsSupportedHostVnum(currentVnum):
			self.__ResetTarget()
			return
		try:
			instanceId, self.unlockedMask, self.metadataSlots = resonanceuihelpers.NormalizeMetadata(
				net.GetResonanceMetadata(
					RESONANCE_CONTEXT_INVENTORY, self.targetWindow,
					self.targetCell, 0, 0,
				)
			)
		except (AttributeError, RuntimeError, TypeError, ValueError):
			instanceId = 0
			self.unlockedMask = 0
			self.metadataSlots = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
		instanceId = int(instanceId)
		if self.targetInstanceId and instanceId != self.targetInstanceId:
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_TARGET_CHANGED", "The selected item changed. Select it again."))
			self.__ResetTarget()
			return
		if not self.targetInstanceId and instanceId:
			self.targetInstanceId = instanceId
		for slotIndex in range(RESONANCE_SLOT_COUNT):
			self.sealSlots.ClearSlot(slotIndex)
			self.sealSlots.DeactivateSlot(slotIndex)
		highlightedPendingSlot = False
		for slotIndex in range(RESONANCE_SLOT_COUNT):
			unlocked = bool(self.unlockedMask & (1 << slotIndex))
			vnum, baseValue, effectiveValue = self.metadataSlots[slotIndex]
			if vnum:
				self.sealSlots.SetItemSlot(slotIndex, vnum, 0)
				self.slotLabels[slotIndex].SetText("+%d%%" % effectiveValue)
			elif unlocked:
				self.slotLabels[slotIndex].SetText(_Locale("RESONANCE_EMPTY_SLOT", "Empty"))
			else:
				self.slotLabels[slotIndex].SetText(_Locale("RESONANCE_LOCKED_SLOT", "Locked"))
			if (not highlightedPendingSlot and self.pendingSealCell is not None
					and unlocked and not vnum):
				self.sealSlots.ActivateSlot(slotIndex)
				self.pendingSealCell = int(self.pendingSealCell)
				highlightedPendingSlot = True
		self.sealSlots.RefreshSlot()

	def __SelectHost(self, unusedSlot=0):
		if not mouseModule.mouseController.isAttached():
			return
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			return
		cell = mouseModule.mouseController.GetAttachedSlotNumber()
		if self.SetTarget(cell):
			mouseModule.mouseController.DeattachObject()

	def __AttachedSealCell(self):
		if self.pendingSealCell is not None:
			cell = self.pendingSealCell
			self.pendingSealCell = None
			return cell
		if not mouseModule.mouseController.isAttached():
			return None
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			return None
		return mouseModule.mouseController.GetAttachedSlotNumber()

	def __InsertSeal(self, slotIndex):
		if self.targetCell < 0:
			return
		if not self.__CanMutate():
			return
		slotIndex = int(slotIndex)
		if not self.unlockedMask & (1 << slotIndex):
			if self.pendingSealCell is not None or mouseModule.mouseController.isAttached():
				chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_SLOT_LOCKED", "This slot is locked."))
			else:
				self.__OpenUnlockDialog(slotIndex)
			return
		if self.metadataSlots[slotIndex][0]:
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_SLOT_OCCUPIED", "This resonance slot is already occupied."))
			return
		sourceCell = self.__AttachedSealCell()
		if sourceCell is None:
			return
		sealVnum = player.GetItemIndex(player.INVENTORY, int(sourceCell))
		if not IsSealVnum(sealVnum):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_INVALID_SEAL", "This seal is no longer available or compatible."))
			return
		families = [SealFamily(row[0]) for row in self.metadataSlots if row[0]]
		if SealFamily(sealVnum) in families:
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_DUPLICATE_FAMILY", "Duplicate seal family."))
			return
		if net.InsertResonanceSeal(
			player.INVENTORY, int(sourceCell), self.targetWindow,
			self.targetCell, self.targetInstanceId, slotIndex,
		):
			mouseModule.mouseController.DeattachObject()

	def __OpenUnlockDialog(self, slotIndex):
		if self.unlockedMask != (1 << int(slotIndex)) - 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_PREVIOUS_SLOT_LOCKED", "Unlock the previous resonance slot first."))
			return False
		try:
			keyVnum, keyCounts, yangCosts = net.GetResonanceUnlockConfig()
			keyCount = int(keyCounts[int(slotIndex)])
			yangCost = int(yangCosts[int(slotIndex)])
		except (AttributeError, IndexError, RuntimeError, TypeError, ValueError):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_SYSTEM_UNAVAILABLE", "The resonance seal system is unavailable."))
			return False
		self.__CloseUnlockDialog()
		return self.unlockDialog.Open(
			self.targetWindow, self.targetCell, self.targetInstanceId,
			int(slotIndex), self.targetVnum, int(keyVnum), keyCount, yangCost,
		)

	def __CloseUnlockDialog(self):
		if self.unlockDialog:
			self.unlockDialog.Close()

	def __SelectSeal(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			self.__InsertSeal(slotIndex)

	def __RemoveSeal(self, slotIndex):
		if self.targetCell < 0 or not self.metadataSlots[int(slotIndex)][0]:
			return
		if not self.__CanMutate():
			return
		if not _HasSealDestination(self.metadataSlots[int(slotIndex)][0]):
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_INVENTORY_FULL", "Free an inventory slot before removing this seal."))
			return
		net.RemoveResonanceSeal(
			self.targetWindow, self.targetCell, self.targetInstanceId, int(slotIndex)
		)

	def __CanMutate(self):
		if getattr(net, "IsResonanceMutationPending", lambda: False)():
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_BUSY", "Another resonance action is still running."))
			return False
		if not self.targetInstanceId:
			chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale("RESONANCE_TARGET_CHANGED", "The selected item changed. Select it again."))
			return False
		return True

	def __OverInHost(self, unusedSlot=0):
		if self.tooltipItem and self.targetCell >= 0:
			self.tooltipItem.SetInventoryItem(self.targetCell, self.targetWindow)

	def __OverInSeal(self, slotIndex):
		if not self.tooltipItem:
			return
		vnum = self.metadataSlots[int(slotIndex)][0]
		if vnum:
			self.tooltipItem.SetItemToolTip(vnum)

	def __OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnMetadataChanged(self, context, windowOrSide, slot, unusedVid, unusedPublicId):
		if int(context) == RESONANCE_CONTEXT_INVENTORY and int(windowOrSide) == self.targetWindow and int(slot) == self.targetCell:
			self.Refresh()

	def OnUnlockConfigChanged(self):
		self.__CloseUnlockDialog()

	def OnMutationResult(self, unusedRequestId, result, unusedSlot, unusedVnum):
		result = int(result)
		if result == getattr(net, "RESONANCE_RESULT_OK", 0):
			return
		key, fallback = RESONANCE_RESULT_MESSAGES.get(
			result,
			("RESONANCE_MUTATION_FAILED", "The resonance seal action failed."),
		)
		chat.AppendChat(chat.CHAT_TYPE_INFO, _Locale(key, fallback))
		if result == getattr(net, "RESONANCE_RESULT_TARGET_CHANGED", 11):
			self.__ResetTarget()

	def OnPressEscapeKey(self):
		self.Close()
		return True
