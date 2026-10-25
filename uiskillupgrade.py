import ui 
import wndMgr
import player
import constInfo
import item
import chat
import skill
import uiToolTip
import net
import localeInfo
import osfInfo
import skillbookpolicy
import sagebuff
import pvmpersonal
import ownedcount
from settingslocale import Text as T

LEGACY_MAX_COUNT = 20
SOUL_STONE_MAX_COUNT = 100
SOUL_STONE = 50513           # the spirit stone (duchovní kámen): G -> P
GRADE_BOOKS = 1              # the skill grade the books read (M -> G)
GRADE_SOUL_STONE = 2         # the skill grade the spirit stone reads (G -> P)
SETTINGS_PATH = "d:/ymir work/ui/game/crimson_ember/gameoption/"
ZEN_BEAN = 70102
SLOT_BASE = "d:/ymir work/ui/public/Slot_Base.sub"


def SetCellImage(window, image):
	"""The background of an item cell: the R1 item slot C while the shared R1 frame (root/uir1frame.py) dresses the
	window, else the original Slot_Base.sub."""
	try:
		import uir1frame
	except Exception:
		image.LoadImage(SLOT_BASE)
		return
	uir1frame.SetCellImage(window, image, SLOT_BASE)
SKILL_SLOT_START = 1


class ReadingCheckBox(ui.Button):
	def __init__(self, callback):
		ui.Button.__init__(self)
		self.callback = callback
		self.checked = False
		ui.Button.SetEvent(self, ui.__mem_func__(self.Toggle))
		self.SetCheckStatus(False)

	def SetCheckStatus(self, checked):
		self.checked = bool(checked)
		self.SetUpVisual(SETTINGS_PATH + ("checkbox_selected.tga" if self.checked else "checkbox_unselected.tga"))
		self.SetOverVisual(SETTINGS_PATH + ("checkbox_selected.tga" if self.checked else "checkbox_hover.tga"))
		self.SetDownVisual(SETTINGS_PATH + "checkbox_selected.tga")

	def Toggle(self):
		self.SetCheckStatus(not self.checked)
		self.callback("CHECK", int(self.checked))


class SkillUpgradeWindow(ui.ScriptWindow):

	statusText = None		# the status line ("Dovednost je na maximu" / "Nemáš knihy" / "Chybí ti: ..."), the window stays open
	r1controls = None		# the R1 buttons and count slider (root/uir1skillupgrade.py), None = the original controls
	serverUpgrader = 0       # item acknowledged by OpenSkillUpgrade
	requestedItem = 0        # outstanding inventory-use request
	chosenSlot = 0           # preserved across server reopen

	def __init__(self): 
		self.isLoaded = 0
		
		self.board = None
		self.slots = None
		self.cancelBtn = None
		self.confirmBtn = None
		self.statusText = None
		self.r1controls = None
		self.toolTipSkill = 0
		self.selectedSlot = 0
		self.isSlotSelectable = [0 for x in range(7)]
		self.curCount = 1
		self.useExorcismBook = 1
		self.useLuckBook = 1
		self.useZenBean = 0
		
		self.itemUpgraderVnum = 0
		self.itemLuckVnum = 0
		self.itemTimeVnum = 0
		self.itemZenVnum = ZEN_BEAN
		self.currentSkillGrade = 0
		self.ReadingMaterialSlot = None
		self.ReadingMaterial = None
		self.readingPairCheck = None
		self.readingPlus = None
		self.readingRequiredCount = None
		
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'confirmBtn')
		self.__LoadWindow()

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/skillupgrade.py")
		except:
			import exception
			exception.Abort("SkillUpgradeWindow.__LoadWindow error")
			
		try:
			self.board = self.GetChild("board")
			self.slots = self.GetChild("SkillSlots")
			
			self.confirmBtn = self.GetChild("confirm")
			self.defaultConfirmText = self.confirmBtn.GetText()
			self.cancelBtn = self.GetChild("cancel")
			self.countText = self.GetChild("currentCount")
			# the status line above the buttons ("Dovednost je na maximu" / "Nemáš knihy"): the window stays open
			self.statusText = ui.TextLine()
			self.statusText.SetParent(self)
			self.statusText.AddFlag("not_pick")
			self.statusText.SetHorizontalAlignCenter()
			self.statusText.SetOutline()
			self.statusText.SetText("")
			self.statusText.Show()
			self.countControl = self.GetChild("CountController")
			# R1 look of the two buttons and the count slider (root/uir1skillupgrade.py); "Starý vzhled", a window
			# without the R1 frame and a failure keep the original controls
			try:
				import uir1skillupgrade
				uir1skillupgrade.Dress(self)
			except Exception:
				self.r1controls = None
			self.countControl.SetButtonVisual(SETTINGS_PATH + "slider/", "small_thumb_01.tga", "small_thumb_02.tga", "small_thumb_03.tga")
			self.countControl.SetBackgroundVisual(SETTINGS_PATH + "slider/small_track.tga")
			self.countControl.SetEvent(ui.__mem_func__(self.OnChangeCount))
			
			self.slots.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			self.slots.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectSkill))
			self.slots.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
			self.slots.SetUnselectItemSlotEvent(ui.__mem_func__(self.ClickSkillSlot))
			self.slots.SetUseSlotEvent(ui.__mem_func__(self.ClickSkillSlot))
			self.slots.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
			self.slots.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			
			self.board.SetCloseEvent(self.Hide)
			self.cancelBtn.SetEvent(ui.__mem_func__(self.Hide))
			self.confirmBtn.SetEvent(ui.__mem_func__(self.Confirm))

			SetCellImage(self, self.GetChild("soul_icon"))
			self.SoulStone = ui.ImageBox()
			self.SoulStone.SetParent(self.GetChild("soul_icon"))
			self.SoulStone.LoadImage("icon/item/50513.tga")
			self.SoulStone.SetPosition(0, 0)
			self.SoulStone.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem2)
			self.SoulStone.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem2, "upgrader")
			self.SoulStone.Show()

			self.ReadingMaterialSlot = ui.ImageBox()
			self.ReadingMaterialSlot.SetParent(self)
			SetCellImage(self, self.ReadingMaterialSlot)
			self.ReadingMaterial = ui.ImageBox()
			self.ReadingMaterial.SetParent(self.ReadingMaterialSlot)
			self.ReadingMaterial.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem2)
			self.ReadingMaterial.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem2, "material")
			self.ReadingMaterial.Show()
			self.readingPairCheck = ui.ImageBox()
			self.readingPairCheck.SetParent(self)
			self.readingPairCheck.AddFlag("not_pick")
			self.readingPairCheck.LoadImage(SETTINGS_PATH + "checkbox_selected.tga")
			self.readingPlus = ui.TextLine()
			self.readingPlus.SetParent(self)
			self.readingPlus.AddFlag("not_pick")
			self.readingPlus.SetText("+")
			self.readingPlus.SetOutline()
			self.readingRequiredCount = ui.TextLine()
			self.readingRequiredCount.SetParent(self)
			self.readingRequiredCount.AddFlag("not_pick")
			self.readingRequiredCount.SetOutline()

			for role, name, vnum, x, callback in (
				("luck", "Luck", 71094, 90, self.SetUseLuckBook),
				("time", "Time", 71001, 156, self.SetUseExorcismBook),
				("zen", "Zen", ZEN_BEAN, 222, self.SetUseZenBean)):
				background = ui.ImageBox()
				background.SetParent(self)
				background.SetPosition(x, 127)
				SetCellImage(self, background)
				background.Show()
				icon = ui.ImageBox()
				icon.SetParent(background)
				item.SelectItem(vnum)
				icon.LoadImage(item.GetIconImageFileName())
				icon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem2)
				icon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem2, role)
				icon.Show()
				check = ReadingCheckBox(ui.__mem_func__(callback))
				check.SetParent(self)
				check.SetPosition(x - 22, 135)
				check.SetCheckStatus(role != "zen")
				check.SetToolTipText(item.GetItemName())
				if role == "zen":
					check.SetToolTipText(T("Doplnit hodnost pro další čtení", "Restore rank for the next reading"))
				check.Show()
				setattr(self, "Slot" + name + "Item", background)
				setattr(self, name + "Item", icon)
				setattr(self, "checkBox" + name, check)

			self.itemCountTexts = {}
			for role, icon in (("upgrader", self.SoulStone), ("material", self.ReadingMaterial), ("luck", self.LuckItem),
					("time", self.TimeItem), ("zen", self.ZenItem)):
				count = ui.TextLine()
				count.SetParent(icon)
				count.AddFlag("not_pick")
				count.SetPosition(32, 23)
				count.SetHorizontalAlignRight()
				count.SetOutline()
				count.SetText("0")
				count.Show()
				self.itemCountTexts[role] = count

		except:
			import exception
			exception.Abort("SkillUpgradeWindow.LoadWindow.BindObject")
			
		self.SetCenterPosition()
		self.RefreshSkillPage()

	def SetUpgradeItem(self, upgradeVnum, local=False):
		"""The item the window reads with. The server opens the window with it (OpenSkillUpgrade, it remembers the
		item for /soul_stone); local=True: only the window shows another item, the server still has the old one."""
		self.selectedSlot = 0
		if not local:
			self.serverUpgrader = upgradeVnum
			self.requestedItem = 0
		self.itemUpgraderVnum = upgradeVnum
		
		upgradeItems = {}
		upgradeItems[skillbookpolicy.UNIVERSAL_SKILL_BOOK] = {
			"LUCK_ITEM" : 71094,
			"TIME_ITEM" : 71001,
			"SKILL_GRADE" : 1,
		}
		upgradeItems[50513] = {
			"LUCK_ITEM" : 71094,
			"TIME_ITEM" : 71001,
			"SKILL_GRADE" : 2,
		}
		upgradeItems[sagebuff.STONE_VNUM] = {
			"LUCK_ITEM" : 71094,
			"TIME_ITEM" : 71001,
			"SKILL_GRADE" : 3,
		}
		upgradeItems[72811] = {
			"LUCK_ITEM" : 72813,
			"TIME_ITEM" : 72812,
			"SKILL_GRADE" : 3,
		}
		
		self.itemUpgraderVnum = upgradeVnum
		
		item.SelectItem(upgradeVnum)
		self.SoulStone.LoadImage(item.GetIconImageFileName())
		
		if upgradeVnum not in upgradeItems: #Books
			self.itemLuckVnum = 71094
			item.SelectItem(71094)
			self.LuckItem.LoadImage(item.GetIconImageFileName())
			
			self.itemTimeVnum = 71001
			item.SelectItem(71001)
			self.TimeItem.LoadImage(item.GetIconImageFileName())

			self.currentSkillGrade = 1
		else: #Soul stone
			self.itemLuckVnum = upgradeItems[upgradeVnum]["LUCK_ITEM"]
			item.SelectItem(self.itemLuckVnum)
			self.LuckItem.LoadImage(item.GetIconImageFileName())
			
			self.itemTimeVnum = upgradeItems[upgradeVnum]["TIME_ITEM"]
			item.SelectItem(self.itemTimeVnum)
			self.TimeItem.LoadImage(item.GetIconImageFileName())
			
			self.currentSkillGrade = upgradeItems[upgradeVnum]["SKILL_GRADE"]
		
		for vnum, checkbox in ((self.itemLuckVnum, self.checkBoxLuck), (self.itemTimeVnum, self.checkBoxTime)):
			item.SelectItem(vnum)
			checkbox.SetToolTipText(item.GetItemName())
		self.RefreshItemCounts()

	def OverInItem2(self, itemType):
		if itemType == "luck":
			index = self.itemLuckVnum
		elif itemType == "time":
			index = self.itemTimeVnum
		elif itemType == "material":
			index = sagebuff.ReadingTerms(item)[0]
		elif itemType == "zen":
			index = self.itemZenVnum
		else:
			index = self.itemUpgraderVnum
			
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.SetItemToolTip(index)
				if itemType == "zen":
					interface.tooltipItem.AppendTextLine(localeInfo.SKILL_UPGRADE_ZEN_HINT)
				interface.tooltipItem.ShowToolTip()

	def OverOutItem2(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()

	def IsUniversalBook(self):
		return self.itemUpgraderVnum == skillbookpolicy.UNIVERSAL_SKILL_BOOK

	def UsesSoulStone(self):
		return self.itemUpgraderVnum in (50513, sagebuff.STONE_VNUM)

	def FollowsSkillGrade(self):
		return bool(self.itemUpgraderVnum) and (self.currentSkillGrade == GRADE_BOOKS or self.itemUpgraderVnum == SOUL_STONE)

	def ItemForSkill(self, slot):
		if self.FollowsSkillGrade():
			if player.GetSkillGrade(slot) == GRADE_SOUL_STONE:
				return SOUL_STONE
			if self.currentSkillGrade == GRADE_BOOKS and not self.IsUniversalBook():
				item.SelectItem(self.itemUpgraderVnum)
				if item.GetValue(0) == player.GetSkillIndex(slot):
					return self.itemUpgraderVnum
			return skillbookpolicy.UNIVERSAL_SKILL_BOOK
		return self.itemUpgraderVnum

	def UpdateSelectedItem(self, synchronize=True):
		"""Shared by character and Buffi: the selected skill determines the displayed requirements."""
		if not self.selectedSlot:
			return
		wanted = self.ItemForSkill(self.selectedSlot)
		if wanted != self.itemUpgraderVnum:
			slot = self.selectedSlot
			self.SetUpgradeItem(wanted, local=True)
			self.selectedSlot = slot
			self.ConfigureReadingControls()
			self.SetCount(0 if self.IsUniversalBook() else 1)
		if synchronize and self.FollowsSkillGrade() and not self.requestedItem:
			self.SynchronizeReadingItem()

	def SynchronizeReadingItem(self):
		"""Use the existing inventory packet; never read before the server acknowledges the item.
		A later Confirm retries a refused request. Selection itself does not depend on item ownership."""
		if self.serverUpgrader == self.itemUpgraderVnum and not self.requestedItem:
			return True
		import quickbuffruntime
		position = quickbuffruntime.InventoryScanner(item, player).Find(self.itemUpgraderVnum)
		if position is not None:
			self.requestedItem = self.itemUpgraderVnum
			net.SendItemUsePacket(position)
		return False

	def PlaceControls(self, height):
		"""The count slider, its text and the two buttons of a board ``height`` px high (the original places)."""
		self.countControl.SetPosition(66, height - 65)
		if self.statusText is not None:
			self.statusText.SetPosition(142, height - 86)
		self.countText.SetPosition(194, height - 68)
		self.confirmBtn.SetPosition(30, height - 37)
		self.cancelBtn.SetPosition(154, height - 37)

	def LayoutControls(self, height):
		"""The controls at their places; the R1 buttons and slider (root/uir1skillupgrade.py) in their own rows."""
		self.PlaceControls(height)
		skin = self.r1controls
		if skin is None:
			return
		try:
			skin.Layout(height)
		except Exception:
			import uir1skillupgrade
			uir1skillupgrade.Fail(self)
			self.PlaceControls(height)

	def ConfigureReadingControls(self):
		self.countControl.Show()
		self.checkBoxTime.Show()
		self.checkBoxLuck.Show()
		self.confirmBtn.SetText(self.defaultConfirmText)
		if self.UsesSoulStone():
			self.SlotZenItem.Show()
			self.checkBoxZen.Show()
		else:
			self.SlotZenItem.Hide()
			self.checkBoxZen.Hide()
		sageReading = self.itemUpgraderVnum == sagebuff.STONE_VNUM
		height = 286 if sageReading else 246
		self.SetSize(284, height)
		self.board.SetSize(284, height)
		self.LayoutControls(height)
		supportY = 167 if sageReading else 127
		positions = (92, 68, 134) if sageReading else ((24, 90, 156) if self.UsesSoulStone() else (42, 124, 206))
		self.GetChild("soul_icon").SetPosition(positions[0], 127)
		self.SlotLuckItem.SetPosition(positions[1], supportY)
		self.SlotTimeItem.SetPosition(positions[2], supportY)
		self.checkBoxLuck.SetPosition(positions[1] - 22, supportY + 8)
		self.checkBoxTime.SetPosition(positions[2] - 22, supportY + 8)
		self.SlotZenItem.SetPosition(200 if sageReading else 222, supportY)
		self.checkBoxZen.SetPosition(178 if sageReading else 200, supportY + 8)
		for widget in (self.ReadingMaterialSlot, self.readingPairCheck, self.readingPlus, self.readingRequiredCount):
			widget.Hide()
		if sageReading:
			material, required, cap = sagebuff.ReadingTerms(item)
			if material > 0 and required > 0:
				item.SelectItem(material)
				self.ReadingMaterial.LoadImage(item.GetIconImageFileName())
				self.ReadingMaterialSlot.SetPosition(152, 127)
				self.readingPairCheck.SetPosition(70, 135)
				self.readingPlus.SetPosition(134, 135)
				self.readingRequiredCount.SetPosition(190, 137)
				self.readingRequiredCount.SetText("%dx" % required)
				for widget in (self.ReadingMaterialSlot, self.readingPairCheck, self.readingPlus, self.readingRequiredCount):
					widget.Show()

	def SetUseExorcismBook(self, checkType, bUse):
		self.useExorcismBook = int(bool(bUse))
		self.SetCount(self.curCount)

	def SetUseLuckBook(self, checkType, bUse):
		self.useLuckBook = int(bool(bUse))
		self.SetCount(self.curCount)

	def SetUseZenBean(self, checkType, bUse):
		self.useZenBean = int(bool(bUse))
		self.PaintItemCounts()

	def MaxCount(self):
		"""The most attempts one request may ask for (the server caps them the same way)."""
		maximum = skillbookpolicy.MAX_SELECTED_BOOKS if self.IsUniversalBook() else LEGACY_MAX_COUNT
		if self.UsesSoulStone():
			maximum = SOUL_STONE_MAX_COUNT
		return maximum

	def AvailableCount(self):
		maximum = self.MaxCount()
		if self.itemUpgraderVnum == sagebuff.STONE_VNUM:
			material, required, cap = sagebuff.ReadingTerms(item)
			if material <= 0 or required <= 0 or cap <= 0:
				return 0
			maximum = min(maximum, ownedcount.Owned(material) // required)
		maximum = min(maximum, self.GetVnumCount())
		if self.useExorcismBook:
			maximum = min(maximum, ownedcount.Owned(self.itemTimeVnum))
		if self.useLuckBook:
			maximum = min(maximum, ownedcount.Owned(self.itemLuckVnum))
		return max(0, int(maximum))

	def OnChangeCount(self):
		maximum = max(1, self.AvailableCount())
		steps = maximum if self.IsUniversalBook() else maximum - 1
		selected = 1 + int(round(self.countControl.GetSliderPos() * steps))
		self.SetCount(0 if self.IsUniversalBook() and selected > maximum else selected)

	def GetVnumCount(self):
		if not self.itemUpgraderVnum:
			return 0
		return ownedcount.Owned(self.itemUpgraderVnum)

	def RefreshItemCounts(self):
		self.SetCount(self.curCount)		# repaints the counts (PaintItemCounts)
		self.RefreshStatus()

	def PaintItemCounts(self):
		"""The count on each item icon: "owned/need" for the chosen number of readings, green / red like every item
		price (root/ownedcount.py); only "owned" for an item that is not used (unchecked) or while
		the need is open ("Do G")."""
		texts = getattr(self, "itemCountTexts", None)
		if not texts:
			return
		attempts = max(0, int(self.curCount or 0)) if any(self.isSlotSelectable) else 0
		rows = [("upgrader", self.itemUpgraderVnum, attempts),
			("luck", self.itemLuckVnum, attempts if self.useLuckBook else 0),
			("time", self.itemTimeVnum, attempts if self.useExorcismBook else 0),
			("zen", self.itemZenVnum, 0)]
		if self.itemUpgraderVnum == sagebuff.STONE_VNUM:
			material, required, unusedCap = sagebuff.ReadingTerms(item)
			rows.append(("material", material, max(0, required) * attempts))
		for role, vnum, need in rows:
			line = texts.get(role)
			if line is None:
				continue
			owned = ownedcount.Owned(vnum) if vnum and vnum > 0 else 0
			if need > 0:
				ownedcount.Paint(line, owned, need, compact=True)
			else:
				line.SetPackedFontColor(-1)		# white, the stack count look
				line.SetText(ownedcount.Short(owned))

	def NothingToReadText(self):
		"""Why Potvrdit has nothing to do (the max level, no books), empty while a reading is possible."""
		if not self.itemUpgraderVnum:
			return ""
		if not any(self.isSlotSelectable):
			return T("Dovednost je na maximu", "The skill is at its maximum")
		if self.AvailableCount() < 1:
			missing = self.MissingItems()
			if not missing or self.itemUpgraderVnum in missing:
				return T("Nemáš kameny", "You have no stones") if self.UsesSoulStone() else T("Nemáš knihy", "You have no books")
			names = []
			for vnum in missing:
				item.SelectItem(vnum)
				names.append(item.GetItemName())
			return getattr(localeInfo, "SKILL_UPGRADE_MISSING", "%s") % ", ".join(names)
		return ""

	def MissingItems(self):
		"""The items one more reading lacks, in the order of the window: the book / stone, the checked reading supports
		(Exorcism scroll, Concentrated reading) and the material of the sage stone. "Nemáš knihy" only for the book,
		a missing support by its name (the tester had the books and lacked the Exorcism scrolls)."""
		need = [(self.itemUpgraderVnum, 1)]
		if self.useExorcismBook:
			need.append((self.itemTimeVnum, 1))
		if self.useLuckBook:
			need.append((self.itemLuckVnum, 1))
		if self.itemUpgraderVnum == sagebuff.STONE_VNUM:
			material, required, unusedCap = sagebuff.ReadingTerms(item)
			if material > 0 and required > 0:
				need.append((material, required))
		return [vnum for vnum, count in need if vnum and ownedcount.Owned(vnum) < count]

	def RefreshStatus(self):
		"""The status line and Potvrdit (disabled when there is nothing to read); the window itself stays open."""
		if self.statusText is None:
			return
		text = self.NothingToReadText()
		self.statusText.SetText(text)
		if text:
			self.confirmBtn.Disable()
		else:
			self.confirmBtn.Enable()

	def SetCount(self, count):
		maximum = max(1, self.AvailableCount())
		if self.IsUniversalBook() and count == 0:
			self.curCount = 0
			self.countText.SetText(T("Do G", "Until G"))
			self.countControl.SetSliderPos(1.0)
			self.PaintItemCounts()
			return
		self.curCount = min(maximum, max(1, int(count)))
		self.countText.SetText("%dx" % self.curCount)
		steps = maximum if self.IsUniversalBook() else max(1, maximum - 1)
		self.countControl.SetSliderPos(float(self.curCount - 1) / steps)
		self.PaintItemCounts()

	def SelectSkill(self, index):
		self.ClickSkillSlot(index)

	def SelectEmptySlot(self, index):
		pass
		
	def ClickSkillSlot(self, index):
		if not 0 <= index < len(self.isSlotSelectable) or not self.isSlotSelectable[index]:
			return
			
		self.slots.ActivateSlot(index)
		self.selectedSlot = index
		self.chosenSlot = index
		
		slotCount = 6
		startSlotIndex = SKILL_SLOT_START
		for i in range(slotCount):
			slotIndex = i + startSlotIndex
			if slotIndex != index:
				self.slots.DeactivateSlot(slotIndex)

		self.UpdateSelectedItem()
		self.RefreshItemCounts()

	def OverInItem(self, slotNumber):
		if 0 == self.toolTipSkill:
			return

		srcSlotIndex = self.__RealSkillSlotToSourceSlot(slotNumber)
		skillIndex = player.GetSkillIndex(srcSlotIndex)
		skillLevel = player.GetSkillLevel(srcSlotIndex)
		skillGrade = player.GetSkillGrade(srcSlotIndex)
		skillType = skill.GetSkillType(skillIndex)
		
		if skill.SKILL_TYPE_ACTIVE == skillType:
			self.toolTipSkill.SetSkillNew(srcSlotIndex, skillIndex, skillGrade, skillLevel)
			# rebuilt from the new level / grade on RefreshSkill while the mouse stays on the slot
			self.toolTipSkill.RememberRefresh(self.OverInItem, slotNumber)

	def OverOutItem(self):
		if 0 != self.toolTipSkill:
			self.toolTipSkill.HideToolTip()
		
	def __GetRealSkillSlot(self, skillGrade, skillSlot):
		return skillSlot + min(skill.SKILL_GRADE_COUNT-1, skillGrade)*skill.SKILL_GRADE_STEP_COUNT
		
	def __RealSkillSlotToSourceSlot(self, realSkillSlot):
		if realSkillSlot > 100:
			return realSkillSlot

		return realSkillSlot % skill.SKILL_GRADE_STEP_COUNT
		
	def __GetSkillGradeFromSlot(self, skillSlot):
		return skillSlot // skill.SKILL_GRADE_STEP_COUNT
		
	def RefreshSkillPage(self):
		"""The skill row (uibuffupgrade.SupportUpgrade shows the Buffi skills in the same window)."""
		self.__RefreshSkillPage()

	def __RefreshSkillPage(self):
		slotCount = 6
		skillPage = self.slots

		startSlotIndex = SKILL_SLOT_START
		self.isSlotSelectable = [False for x in range(startSlotIndex + slotCount)]

		getSkillType=skill.GetSkillType
		getSkillIndex=player.GetSkillIndex
		getSkillGrade=player.GetSkillGrade
		getSkillLevel=player.GetSkillLevel
		for i in range(slotCount):

			slotIndex = i + startSlotIndex
			skillIndex = getSkillIndex(slotIndex)

			skillPage.ClearSlot(slotIndex)
			skillPage.DeactivateSlot(slotIndex)

			if 0 == skillIndex:
				continue

			skillGrade = getSkillGrade(slotIndex)
			skillLevel = getSkillLevel(slotIndex)
			skillType = getSkillType(skillIndex)
			# Keep every skill visible; M and G share one selection row.

			## ACTIVE
			if skill.SKILL_TYPE_ACTIVE == skillType:
				realSlotIndex = slotIndex
				skillPage.SetSkillSlotNew(realSlotIndex, skillIndex, skillGrade, skillLevel)
				skillPage.SetCoverButton(realSlotIndex)

				skillPage.SetSlotCountNew(realSlotIndex, skillGrade, skillLevel)

				if self.FollowsSkillGrade():
					canRead = skillGrade in (GRADE_BOOKS, GRADE_SOUL_STONE) and skillbookpolicy.CanReadUniversal(
						net.GetMainActorRace(), net.GetMainActorSkillGroup(), skillIndex, GRADE_BOOKS)
				else:
					canRead = skillGrade == self.currentSkillGrade
					if self.itemUpgraderVnum == sagebuff.STONE_VNUM:
						canRead = canRead and sagebuff.CanRead(skillIndex, skillGrade, skillLevel,
							pvmpersonal.current().rows if pvmpersonal.current() else ())
				self.isSlotSelectable[slotIndex] = canRead
				if not canRead:
					skillPage.DisableCoverButton(realSlotIndex)

		if not 0 < self.selectedSlot < len(self.isSlotSelectable) or not self.isSlotSelectable[self.selectedSlot]:
			self.selectedSlot = 0
		else:
			skillPage.ActivateSlot(self.selectedSlot)
		skillPage.RefreshSlot()
			
	def SetSkillToolTip(self, toolTipSkill):
		self.toolTipSkill = toolTipSkill
		
	def Confirm(self):
		self.RefreshSkillPage()
		self.SetCount(self.curCount)
		self.UpdateSelectedItem(synchronize=False)
		if self.selectedSlot and self.FollowsSkillGrade() and not self.SynchronizeReadingItem():
			return
		if self.selectedSlot != 0:
			srcSlotIndex = self.__RealSkillSlotToSourceSlot(self.selectedSlot)
			skillIndex = player.GetSkillIndex(srcSlotIndex)

			if self.itemUpgraderVnum == sagebuff.STONE_VNUM and self.AvailableCount() < 1:
				return
			if self.IsUniversalBook():
				strArg = skillbookpolicy.UniversalReadArguments(skillIndex, self.curCount, self.useExorcismBook, self.useLuckBook)
			else:
				strArg = "%d %d %d %d" % (skillIndex, self.curCount, self.useExorcismBook, self.useLuckBook)
				if self.UsesSoulStone() and self.useZenBean:
					strArg += " %d" % self.useZenBean
			net.SendChatPacket("/soul_stone " + str(strArg))
			# the window stays open: the player closes it (reads again, another skill, looks at the stats)
			self.Refresh()
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SOUL_STONE_GUI)

	def OnPressEscapeKey(self):
		self.Hide()
		return True
		
	def Refresh(self):
		if not self.IsShow():
			return
		slot = self.selectedSlot
		self.RefreshSkillPage()
		if not self.selectedSlot:
			self.SelectReadableSkill(after=slot)
		self.UpdateSelectedItem()
		self.RefreshItemCounts()

	def SelectReadableSkill(self, preferred=(), after=0):
		"""Chooses a readable skill: ``preferred`` first, then the row from the slot after ``after``
		around. False: none."""
		count = len(self.isSlotSelectable)
		row = list(range(SKILL_SLOT_START, count))
		start = row.index(after) + 1 if after in row else 0
		for slot in list(preferred) + row[start:] + row[:start]:
			if 0 < slot < count and self.isSlotSelectable[slot]:
				self.ClickSkillSlot(slot)
				return True
		return False

	def Show(self):
		if self.IsUniversalBook():
			self.useExorcismBook = self.useLuckBook = 1
		self.ConfigureReadingControls()
		self.RefreshItemCounts()
		self.checkBoxTime.SetCheckStatus(self.useExorcismBook)
		self.checkBoxLuck.SetCheckStatus(self.useLuckBook)
		self.checkBoxZen.SetCheckStatus(self.useZenBean)
		self.SetCount(0 if self.IsUniversalBook() else 1)
		self.selectedSlot = 0
		self.RefreshSkillPage()
		self.SelectBookSkill()
		self.RefreshStatus()
		ui.ScriptWindow.Show(self)

	def SelectBookSkill(self):
		"""The skill chosen when the window opens: the skill of a book of one skill, else the skill chosen last, else
		the first one this item reads (as Vylepšování buffy opens on its skill), so Potvrdit reads right away."""
		if self.itemUpgraderVnum and self.itemUpgraderVnum not in [50513, sagebuff.STONE_VNUM, 72811, skillbookpolicy.UNIVERSAL_SKILL_BOOK]:
			item.SelectItem(self.itemUpgraderVnum)
			targetSkill = item.GetValue(0)

			if targetSkill > 0:
				startSlotIndex = SKILL_SLOT_START
				for i in range(skillbookpolicy.STANDARD_SKILL_COUNT):
					slotIndex = startSlotIndex + i
					if player.GetSkillIndex(slotIndex) == targetSkill and self.isSlotSelectable[slotIndex]:
						self.ClickSkillSlot(slotIndex)
						break
		if not self.selectedSlot:
			self.SelectReadableSkill((self.chosenSlot,))
		
	def Hide(self):
		self.OverOutItem2()
		if 0 != self.toolTipSkill:
			self.toolTipSkill.Hide()
			
		ui.ScriptWindow.Hide(self)
		
	def Destroy(self):
		self.itemCountTexts = {}
		self.ReadingMaterialSlot = None
		self.ReadingMaterial = None
		self.readingPairCheck = None
		self.readingPlus = None
		self.readingRequiredCount = None
		self.r1controls = None
		self.ClearDictionary()
		self.board = None
		self.slots = None
		self.cancelBtn = None
		self.confirmBtn = None
		self.toolTipSkill = 0
		self.selectedSlot = 0
		self.isSlotSelectable = [0 for x in range(7)]
		self.curCount = 1
		self.useExorcismBook = 1
		self.useLuckBook = 1

	def __del__(self): 
		ui.ScriptWindow.__del__(self) 
