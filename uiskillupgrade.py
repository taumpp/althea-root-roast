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
from settingslocale import Text as T

LEGACY_MAX_COUNT = 20
SOUL_STONE_MAX_COUNT = 100
SETTINGS_PATH = "d:/ymir work/ui/game/crimson_ember/gameoption/"
ZEN_BEAN = 70102
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

	def __init__(self): 
		self.isLoaded = 0
		
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
			self.countControl = self.GetChild("CountController")
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

			self.SoulStone = ui.ImageBox()
			self.SoulStone.SetParent(self.GetChild("soul_icon"))
			self.SoulStone.LoadImage("icon/item/50513.tga")
			self.SoulStone.SetPosition(0, 0)
			self.SoulStone.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem2)
			self.SoulStone.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem2, "upgrader")
			self.SoulStone.Show()

			self.ReadingMaterialSlot = ui.ImageBox()
			self.ReadingMaterialSlot.SetParent(self)
			self.ReadingMaterialSlot.LoadImage("d:/ymir work/ui/public/Slot_Base.sub")
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
				background.LoadImage("d:/ymir work/ui/public/Slot_Base.sub")
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
		self.__RefreshSkillPage()

	def SetUpgradeItem(self, upgradeVnum):
		self.selectedSlot = 0
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
		self.countControl.SetPosition(66, height - 65)
		self.countText.SetPosition(194, height - 68)
		self.confirmBtn.SetPosition(30, height - 37)
		self.cancelBtn.SetPosition(154, height - 37)
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

	def AvailableCount(self):
		maximum = skillbookpolicy.MAX_SELECTED_BOOKS if self.IsUniversalBook() else LEGACY_MAX_COUNT
		if self.UsesSoulStone():
			maximum = SOUL_STONE_MAX_COUNT
		if self.itemUpgraderVnum == sagebuff.STONE_VNUM:
			material, required, cap = sagebuff.ReadingTerms(item)
			if material <= 0 or required <= 0 or cap <= 0:
				return 0
			maximum = min(maximum, player.GetItemCountByVnum(material) // required)
		maximum = min(maximum, self.GetVnumCount())
		if self.useExorcismBook:
			maximum = min(maximum, player.GetItemCountByVnum(self.itemTimeVnum))
		if self.useLuckBook:
			maximum = min(maximum, player.GetItemCountByVnum(self.itemLuckVnum))
		return max(0, int(maximum))

	def OnChangeCount(self):
		maximum = max(1, self.AvailableCount())
		steps = maximum if self.IsUniversalBook() else maximum - 1
		selected = 1 + int(round(self.countControl.GetSliderPos() * steps))
		self.SetCount(0 if self.IsUniversalBook() and selected > maximum else selected)

	def GetVnumCount(self):
		if not self.itemUpgraderVnum:
			return 0
		return player.GetItemCountByVnum(self.itemUpgraderVnum)

	def RefreshItemCounts(self):
		for role, vnum in (("upgrader", self.itemUpgraderVnum),
				("luck", self.itemLuckVnum), ("time", self.itemTimeVnum), ("zen", self.itemZenVnum)):
			count = max(0, int(player.GetItemCountByVnum(vnum))) if vnum else 0
			self.itemCountTexts[role].SetText(str(count))
		if self.itemUpgraderVnum == sagebuff.STONE_VNUM:
			material = sagebuff.ReadingTerms(item)[0]
			count = max(0, int(player.GetItemCountByVnum(material))) if material > 0 else 0
			self.itemCountTexts["material"].SetText(str(count))
		self.SetCount(self.curCount)

	def SetCount(self, count):
		maximum = max(1, self.AvailableCount())
		if self.IsUniversalBook() and count == 0:
			self.curCount = 0
			self.countText.SetText(T("Do G", "Until G"))
			self.countControl.SetSliderPos(1.0)
			return
		self.curCount = min(maximum, max(1, int(count)))
		self.countText.SetText("%dx" % self.curCount)
		steps = maximum if self.IsUniversalBook() else max(1, maximum - 1)
		self.countControl.SetSliderPos(float(self.curCount - 1) / steps)

	def SelectSkill(self, index):
		if not 0 <= index < len(self.isSlotSelectable) or not self.isSlotSelectable[index]:
			return
			
		self.slots.ActivateSlot(index)
		self.selectedSlot = index
		
		slotCount = 6
		startSlotIndex = SKILL_SLOT_START
		for i in range(slotCount):
			slotIndex = i + startSlotIndex
			if slotIndex != index:
				self.slots.DeactivateSlot(slotIndex)
		
	def SelectEmptySlot(self, index):
		pass
		
	def ClickSkillSlot(self, index):
		if not 0 <= index < len(self.isSlotSelectable) or not self.isSlotSelectable[index]:
			return
			
		self.slots.ActivateSlot(index)
		self.selectedSlot = index
		
		slotCount = 6
		startSlotIndex = SKILL_SLOT_START
		for i in range(slotCount):
			slotIndex = i + startSlotIndex
			if slotIndex != index:
				self.slots.DeactivateSlot(slotIndex)

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
		
	def __RefreshSkillPage(self):
		slotCount = 6
		skillPage = self.slots

		startSlotIndex = SKILL_SLOT_START
		self.isSlotSelectable = [False for x in range(startSlotIndex + slotCount)]
		universalBook = self.itemUpgraderVnum == skillbookpolicy.UNIVERSAL_SKILL_BOOK

		getSkillType=skill.GetSkillType
		getSkillIndex=player.GetSkillIndex
		getSkillGrade=player.GetSkillGrade
		getSkillLevel=player.GetSkillLevel
		getSkillLevelUpPoint=skill.GetSkillLevelUpPoint
		getSkillMaxLevel=skill.GetSkillMaxLevel
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
			if universalBook and not skillbookpolicy.CanReadUniversal(
					net.GetMainActorRace(), net.GetMainActorSkillGroup(), skillIndex, skillGrade):
				continue

			## ACTIVE
			if skill.SKILL_TYPE_ACTIVE == skillType:
				realSlotIndex = slotIndex
				skillPage.SetSkillSlotNew(realSlotIndex, skillIndex, skillGrade, skillLevel)
				skillPage.SetCoverButton(realSlotIndex)

				skillPage.SetSlotCountNew(realSlotIndex, skillGrade, skillLevel)

				cannotUpgrade = (self.itemUpgraderVnum == sagebuff.STONE_VNUM and
					not sagebuff.CanRead(skillIndex, skillGrade, skillLevel,
					pvmpersonal.current().rows if pvmpersonal.current() else ()))
				if self.itemUpgraderVnum not in [50513, sagebuff.STONE_VNUM, 72811, skillbookpolicy.UNIVERSAL_SKILL_BOOK]:
					item.SelectItem(self.itemUpgraderVnum)
					if item.GetValue(0) != skillIndex:
						cannotUpgrade = True

				if skillGrade != self.currentSkillGrade or cannotUpgrade == True:
					self.isSlotSelectable[slotIndex] = False
					skillPage.DisableCoverButton(realSlotIndex)
				else:
					self.isSlotSelectable[slotIndex] = True

		if not 0 < self.selectedSlot < len(self.isSlotSelectable) or not self.isSlotSelectable[self.selectedSlot]:
			self.selectedSlot = 0
		else:
			skillPage.ActivateSlot(self.selectedSlot)
		skillPage.RefreshSlot()
			
	def SetSkillToolTip(self, toolTipSkill):
		self.toolTipSkill = toolTipSkill
		
	def Confirm(self):
		self.__RefreshSkillPage()
		self.SetCount(self.curCount)
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
			self.Hide()
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SOUL_STONE_GUI)

	def OnPressEscapeKey(self):
		self.Hide()
		return True
		
	def Refresh(self):
		self.__RefreshSkillPage()
		self.RefreshItemCounts()
		self.SetCount(self.curCount)
		
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
		self.__RefreshSkillPage()

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

		ui.ScriptWindow.Show(self)
		
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
