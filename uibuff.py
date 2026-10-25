import ui
import uicrimsoncontrols
import player
import mouseModule
import net
import app
import item
import chat
import localeInfo
import constInfo
import wndMgr
import osfInfo
import uiCommon

def IsVipElfOutfit(vnum):
	# Elf-form Buffi only; the range has one definition, in constInfo.
	return constInfo.IS_VIP_ELF_OUTFIT(vnum)

def SyncR1(window):
	"""The R1 look (root/uibuffr1.py) repeats the values the window just changed."""
	skin = getattr(window, "r1Skin", None)
	if skin:
		skin.SyncSafe()


AFFECT_DICT = {
		item.APPLY_INT : localeInfo.TOOLTIP_INT,
	}
		
class SupportEquipment(ui.ImageBox):
	def __del__(self):
		ui.ImageBox.__del__(self)
		
	def Destroy(self):
		self.Hide()
		self.wndEquip = None

	def __init__(self):
		ui.ImageBox.__init__(self)
		self.wndEquip = None
		self.Destroy()
	
	def LoadWindow(self, parent):
		self.LoadImage("d:/ymir work/ui/game/support/shaman_base.png")


		self.board = ui.Window()
		self.board.SetParent(self)
		self.board.AddFlag("attach")
		self.board.AddFlag("not_pick")
		self.board.SetSize(400, 400)
		self.board.SetPosition(0, 0)
		self.board.Show()

		wndEquip = ui.SlotWindow()
		wndEquip.SetParent(self)
		wndEquip.SetSize(165,126)
		wndEquip.SetPosition(0,0)
		wndEquip.SetOverInItemEvent(ui.__mem_func__(parent.OverInItem))
		wndEquip.SetOverOutItemEvent(ui.__mem_func__(parent.OverOutItem))
		wndEquip.SetSelectEmptySlotEvent(ui.__mem_func__(parent.OnSelectEmptySlot))
		wndEquip.SetSelectItemSlotEvent(ui.__mem_func__(parent.OnSelectItemSlot))
		wndEquip.SetOverInEvent(ui.__mem_func__(parent.OverInItem2))
		wndEquip.SetOverOutEvent(ui.__mem_func__(parent.OverOutItem))
		wndEquip.AppendSlot(1,68,45,32,64)
		wndEquip.AppendSlot(2,68,10,32,32)
		wndEquip.AppendSlot(3,18,14,32,96)
		wndEquip.AppendSlot(5,116,80,32,32)
		wndEquip.AppendSlot(4,116,46,32,32)
		wndEquip.AppendSlot(6,116,14,32,32)
		wndEquip.Show()
		self.wndEquip = wndEquip

	def OnMoveWindow(self, x, y):
		self.SetPosition(x - self.GetWidth() + 2, y + 30)

class SupportMainGui(ui.ScriptWindow):
	class TextToolTip(ui.Window):
		def __init__(self, y):
			ui.Window.__init__(self, "TOP_MOST")

			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetHorizontalAlignLeft()
			textLine.SetOutline()
			textLine.Show()
			self.y = y
			self.textLine = textLine

		def __del__(self):
			ui.Window.__del__(self)

		def SetText(self, text):
			self.textLine.SetText(text)

		def OnRender(self):
			(mouseX, mouseY) = wndMgr.GetMousePosition()
			self.textLine.SetPosition(mouseX, mouseY - 60 + self.y)

	def __init__(self, vnum = 0):
		ui.ScriptWindow.__init__(self)
		self.minimizeBtn = None
		self.equipSlot = None
		self.vnum = vnum
		self.questionDialog = None
		self.toolTipItem = None
		self.interface = None
		self.toolTipSkill = 0
		self.progressPanel = None
		self.progressGauge = None
		self.progressLevelText = None
		self.progressExpText = None
		self.progressPassiveText = None
		self.progressStatusText = None
		self.healingSkillsUnlocked = False
		self.expMode = 1
		self.form = 0
		self.expModeButtons = []
		self.r1Skin = None
		
		self.childrenList = []
		
		self.__LoadWindow()

	def OnMoveWindow(self, x, y):
		(x, y) = self.GetGlobalPosition()

		if self.equipSlot:
			if self.equipSlot.IsShow():
				self.equipSlot.OnMoveWindow(x, y)
				if self.minimizeBtn != None:
					(x, y) = self.equipSlot.GetGlobalPosition()
					self.minimizeBtn.SetPosition(x - self.minimizeBtn.GetWidth(), y + 5)
			else:
				if self.minimizeBtn != None:
					self.minimizeBtn.SetPosition(x - self.minimizeBtn.GetWidth() + 3, y + 45)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Show(self):
		ui.ScriptWindow.Show(self)
		
		self.minimizeBtn.Show()
		self.equipSlot.Hide()
		self.OnMoveWindow(0, 0)

	def Close(self):
		if self.questionDialog:
			self.questionDialog.Close()
			
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
			
		if 0 != self.toolTipSkill:
			self.toolTipSkill.Hide()

		self.minimizeBtn.Hide()
		self.equipSlot.Hide()

		self.Hide()
		
	def OnPressEscapeKey(self):
		self.Close()
		return True
		
	def Destroy(self):
		if getattr(self, "r1Skin", None):
			self.r1Skin.Destroy()
		self.r1Skin = None
		self.minimizeBtn.Hide()
		self.minimizeBtn.Destroy()
		self.minimizeBtn = None

		self.equipSlot.Hide()
		self.equipSlot.Destroy()
		self.equipSlot = None

		self.ClearDictionary()
		
		if self.questionDialog:
			self.questionDialog.Close()
			
		if 0 != self.toolTipSkill:
			self.toolTipSkill.Hide()
			
		self.questionDialog = None
		self.toolTipItem = None
		self.interface = None
		self.toolTipSkill = 0
		self.progressPanel = None
		self.progressGauge = None
		self.progressLevelText = None
		self.progressExpText = None
		self.progressPassiveText = None
		self.progressStatusText = None

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/buffinformationwindow.py")
		except:
			import exception
			exception.Abort("buffinformationwindow.LoadWindow.LoadObject")
			
		try:
			self.supportname = self.GetChild("SupportsName")
			self.supportInt = self.GetChild("SupportInt")
			self.progressPanel = self.GetChild("ProgressWindow")

			self.progressGauge = ui.Gauge()
			self.progressGauge.SetParent(self.progressPanel)
			self.progressGauge.MakeGauge(150, "pink")
			self.progressGauge.SetPosition(39, 22)
			self.progressGauge.Show()

			self.progressLevelText = ui.TextLine()
			self.progressLevelText.SetParent(self.progressPanel)
			self.progressLevelText.SetPosition(8, 5)
			self.progressLevelText.SetOutline()
			self.progressLevelText.SetPackedFontColor(0xffECC576)
			self.progressLevelText.Show()

			self.progressPassiveText = ui.TextLine()
			self.progressPassiveText.SetParent(self.progressPanel)
			self.progressPassiveText.SetPosition(220, 5)
			self.progressPassiveText.SetHorizontalAlignRight()
			self.progressPassiveText.SetOutline()
			self.progressPassiveText.SetPackedFontColor(0xffECC576)
			self.progressPassiveText.Show()

			self.progressExpText = ui.TextLine()
			self.progressExpText.SetParent(self.progressPanel)
			self.progressExpText.SetPosition(114, 20)
			self.progressExpText.SetHorizontalAlignCenter()
			self.progressExpText.SetOutline()
			self.progressExpText.Show()

			self.progressStatusText = ui.TextLine()
			self.progressStatusText.SetParent(self.progressPanel)
			self.progressStatusText.SetPosition(114, 38)
			self.progressStatusText.SetHorizontalAlignCenter()
			self.progressStatusText.SetOutline()
			self.progressStatusText.Show()

			self.expModeButtons = []
			for index, label in enumerate(("Vypnuto", "Rovnoměrně", "Prioritní")):
				button = ui.RadioButton()
				button.SetParent(self)
				uicrimsoncontrols.ApplyVisuals(button, "72x24")
				button.SetText(label)
				button.SetPosition(15 + index * 77, 142)
				button.SetEvent(lambda mode=index: self.OnSelectExpMode(mode))
				button.Show()
				self.expModeButtons.append(button)

			self.skillLock_4 = self.GetChild("SkillLocked_4")
			self.skillLock_5 = self.GetChild("SkillLocked_5")

			self.upgradeBtn_1 = self.GetChild("upgradeBtn_1")
			self.upgradeBtn_2 = self.GetChild("upgradeBtn_2")
			self.upgradeBtn_3 = self.GetChild("upgradeBtn_3")
			self.upgradeBtn_4 = self.GetChild("upgradeBtn_4")
			self.upgradeBtn_5 = self.GetChild("upgradeBtn_5")
			
			self.upgradeBtn_1.SetEvent(lambda arg=1: self.OnClickUpgradeSkill(arg))
			self.upgradeBtn_2.SetEvent(lambda arg=2: self.OnClickUpgradeSkill(arg))
			self.upgradeBtn_3.SetEvent(lambda arg=3: self.OnClickUpgradeSkill(arg))
			self.upgradeBtn_4.SetEvent(lambda arg=4: self.OnClickUpgradeSkill(arg))
			self.upgradeBtn_5.SetEvent(lambda arg=5: self.OnClickUpgradeSkill(arg))

			self.equipSlot = SupportEquipment()
			self.equipSlot.LoadWindow(self)
			self.equipSlot.Hide()

			minimizeBtn = ui.Button()
			minimizeBtn.SetUpVisual("d:/ymir work/ui/game/belt_inventory/btn_minimize_normal.tga")
			minimizeBtn.SetOverVisual("d:/ymir work/ui/game/belt_inventory/btn_minimize_over.tga")
			minimizeBtn.SetDownVisual("d:/ymir work/ui/game/belt_inventory/btn_minimize_down.tga")
			minimizeBtn.SetEvent(self.clickMinimize)
			minimizeBtn.Hide()
			self.minimizeBtn = minimizeBtn
			
			# SKILL 1: Dragon's Aid
			self.skill1 = self.GetChild("Buffi_Skill_1")
			self.skill1.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[0], 0, 0)
			self.skill1.SetSlotCountNew(0, 0, 0)
			self.skill1.SetCoverButton(0)
			self.skill1.SetOverInItemEvent(ui.__mem_func__(self.OverInSkill))
			self.skill1.SetOverOutItemEvent(ui.__mem_func__(self.OverOutSkill))
			
			# SKILL 2: Blessing
			self.skill2 = self.GetChild("Buffi_Skill_2")
			self.skill2.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[1], 0, 0)
			self.skill2.SetSlotCountNew(0, 0, 0)
			self.skill2.SetCoverButton(0)
			self.skill2.SetOverInItemEvent(ui.__mem_func__(self.OverInSkill2))
			self.skill2.SetOverOutItemEvent(ui.__mem_func__(self.OverOutSkill))
			
			# SKILL 3: Reflect
			self.skill3 = self.GetChild("Buffi_Skill_3")
			self.skill3.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[2], 0, 0)
			self.skill3.SetSlotCountNew(0, 0, 0)
			self.skill3.SetCoverButton(0)
			self.skill3.SetOverInItemEvent(ui.__mem_func__(self.OverInSkill3))
			self.skill3.SetOverOutItemEvent(ui.__mem_func__(self.OverOutSkill))
			
			# SKILL 4: Swiftness (movement) [kwaesok]
			self.skill4 = self.GetChild("Buffi_Skill_4")
			self.skill4.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[3], 0, 0)
			self.skill4.SetSlotCountNew(0, 0, 0)
			self.skill4.SetCoverButton(0)
			self.skill4.SetOverInItemEvent(ui.__mem_func__(self.OverInSkill4))
			self.skill4.SetOverOutItemEvent(ui.__mem_func__(self.OverOutSkill))
			
			# SKILL 5: Attack Up [jeungryeok]
			self.skill5 = self.GetChild("Buffi_Skill_5")
			self.skill5.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[4], 0, 0)
			self.skill5.SetSlotCountNew(0, 0, 0)
			self.skill5.SetCoverButton(0)
			self.skill5.SetOverInItemEvent(ui.__mem_func__(self.OverInSkill5))
			self.skill5.SetOverOutItemEvent(ui.__mem_func__(self.OverOutSkill))

			self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.Close))
			
			self.SetDefaultInfo()
			self.OnMoveWindow(0, 0)

		except:
			import exception
			exception.Abort("PetInformationWindow.LoadWindow.BindObject")

		self.__ApplyR1Look()

	def __ApplyR1Look(self):
		"""R1 look (root/uibuffr1.py) unless Settings -> "Starý vzhled" chose the original one; a build failure
		undoes every change and keeps the original look (traced to syserr, not tried again this session)."""
		self.r1Skin = None
		try:
			import uibuffr1
			self.r1Skin = uibuffr1.Build(self)
		except Exception:
			self.r1Skin = None

	def clickMinimize(self):
		if self.equipSlot:
			if self.equipSlot.IsShow():
				self.equipSlot.Hide()
			else:
				self.equipSlot.Show()
			self.OnMoveWindow(0, 0)

	def SetItemToolTip(self, itemTooltip):
		self.toolTipItem = itemTooltip
		
	def SetSkillToolTip(self, toolTipSkill):
		self.toolTipSkill = toolTipSkill
		
	def BindInterface(self, interface):
		self.interface = interface

	def __ShowToolTip(self, slotIndex):
		if self.toolTipItem:
			self.toolTipItem.SetSupportEquipmentItem(osfInfo.SUPPORT_EQUIPMENT[slotIndex])
	
	def OverInItem2(self, slotIndex):
		toolTipItem = self.toolTipItem
		if toolTipItem:
			toolTipItem.ClearToolTip()
			slotNames = {
				1: [localeInfo.SHOP_SEARCH_CAT_COSTUME,toolTipItem.NORMAL_COLOR],
				2: [localeInfo.SHOP_SEARCH_CAT_COSTUME_HAIR,toolTipItem.NORMAL_COLOR],
				3: [localeInfo.SHOP_SEARCH_CAT_COSTUME_WEAPON,toolTipItem.NORMAL_COLOR],
				5: [localeInfo.TOOLTIP_ARMOR_EFFECT,toolTipItem.NORMAL_COLOR],
				4: [localeInfo.TOOLTIP_WEAPON_EFFECT,toolTipItem.NORMAL_COLOR],
				6: [localeInfo.TOOLTIP_SKIN_ACCE,toolTipItem.NORMAL_COLOR],
			}
			
			if slotIndex in slotNames:
				toolTipItem.AlignHorizonalCenter()
				toolTipItem.AutoAppendNewTextLine(slotNames[slotIndex][0],slotNames[slotIndex][1])
				toolTipItem.ShowToolTip()

	def OverInItem(self, slotIndex):
		self.__ShowToolTip(slotIndex)

	def OverOutItem(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
			
	# 1 = Dragon's Aid 196 (96+100)
	# 2 = Blessing 194 (94+100)
	# 3 = Reflect 195 (95+100)
	# 4 = Swiftness 197 (97+100)
	# 5 = Attack Up 198 (98+100)
	
	def SetupSkillTooltip(self, skill):
		skillIndex = osfInfo.SUPPORT_SKILL_VNUMS[skill - 1]
		skillLevel = osfInfo.SUPPORT_SKILLS[skill]["LVL"]
		skillGrade = osfInfo.SUPPORT_SKILLS[skill]["GRADE"]
		skillRealLvl = osfInfo.SUPPORT_SKILLS[skill]["REAL_LVL"]
		
		self.toolTipSkill.SetSupportSkill(skillIndex, skillLevel, skillGrade, skillRealLvl)
		# the open tooltip is rebuilt from the new level when SetSkillLvl brings it
		remember = getattr(self.toolTipSkill, "RememberRefresh", None)
		if remember:
			remember(self.SetupSkillTooltip, skill)
			
	def OverOutSkill(self):
		if 0 != self.toolTipSkill:
			self.toolTipSkill.HideToolTip()
			
	def OverInSkill(self, skill):
		skillID = 1
		self.SetupSkillTooltip(skillID)
		
	def OverInSkill2(self, skill):
		skillID = 2
		self.SetupSkillTooltip(skillID)
		
	def OverInSkill3(self, skill):
		skillID = 3
		self.SetupSkillTooltip(skillID)
		
	def OverInSkill4(self, skill):
		skillID = 4
		self.SetupSkillTooltip(skillID)
		
	def OverInSkill5(self, skill):
		skillID = 5
		self.SetupSkillTooltip(skillID)

	def SetPremiumSkill(self, isPremium):
		self.healingSkillsUnlocked = bool(isPremium)
		if self.healingSkillsUnlocked:
			self.skillLock_4.Hide()
			self.skillLock_5.Hide()
		else:
			self.skillLock_4.Show()
			self.skillLock_5.Show()
			self.upgradeBtn_4.Hide()
			self.upgradeBtn_5.Hide()
		SyncR1(self)

	def OnClickUpgradeSkill(self, skill):
		if self.interface:
			self.interface.OpenSupportUpgrade(skill)
			
	def SkillLevelToLvl(self, lvl):
		grade = osfInfo.SkillLevelToGrade(lvl)

		if grade == 3:
			return lvl - 40 + 1
		if grade == 2:
			return lvl - 30 + 1
		if grade == 1:
			return lvl - 20 + 1
		else:
			return lvl
			
	def SetSkillLvl(self, skill_1, skill_2, skill_3, skill_4, skill_5):
		
		skill_1_grade = osfInfo.SkillLevelToGrade(skill_1)
		skill_1_lvl = osfInfo.SkillLevelToLvl(skill_1)
		
		osfInfo.SUPPORT_SKILLS[1]["GRADE"] = skill_1_grade
		osfInfo.SUPPORT_SKILLS[1]["LVL"] = skill_1_lvl
		osfInfo.SUPPORT_SKILLS[1]["REAL_LVL"] = skill_1
		
		self.skill1.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[0], skill_1_grade, skill_1_lvl)
		self.skill1.SetSlotCountNew(0, skill_1_grade, skill_1_lvl)
		
		if skill_1 >= 40: #max_lvl
			self.upgradeBtn_1.Hide()
		else:
			self.upgradeBtn_1.Show()
		
		skill_2_grade = osfInfo.SkillLevelToGrade(skill_2)
		skill_2_lvl = osfInfo.SkillLevelToLvl(skill_2)
		
		osfInfo.SUPPORT_SKILLS[2]["GRADE"] = skill_2_grade
		osfInfo.SUPPORT_SKILLS[2]["LVL"] = skill_2_lvl
		osfInfo.SUPPORT_SKILLS[2]["REAL_LVL"] = skill_2
		
		self.skill2.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[1], skill_2_grade, skill_2_lvl)
		self.skill2.SetSlotCountNew(0, skill_2_grade, skill_2_lvl)
		
		if skill_2 >= 40: #max_lvl
			self.upgradeBtn_2.Hide()
		else:
			self.upgradeBtn_2.Show()
		
		skill_3_grade = osfInfo.SkillLevelToGrade(skill_3)
		skill_3_lvl = osfInfo.SkillLevelToLvl(skill_3)
		
		osfInfo.SUPPORT_SKILLS[3]["GRADE"] = skill_3_grade
		osfInfo.SUPPORT_SKILLS[3]["LVL"] = skill_3_lvl
		osfInfo.SUPPORT_SKILLS[3]["REAL_LVL"] = skill_3
		
		self.skill3.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[2], skill_3_grade, skill_3_lvl)
		self.skill3.SetSlotCountNew(0, skill_3_grade, skill_3_lvl)
		
		if skill_3 >= 40: #max_lvl
			self.upgradeBtn_3.Hide()
		else:
			self.upgradeBtn_3.Show()
		
		skill_4_grade = osfInfo.SkillLevelToGrade(skill_4)
		skill_4_lvl = osfInfo.SkillLevelToLvl(skill_4)
		
		osfInfo.SUPPORT_SKILLS[4]["GRADE"] = skill_4_grade
		osfInfo.SUPPORT_SKILLS[4]["LVL"] = skill_4_lvl
		osfInfo.SUPPORT_SKILLS[4]["REAL_LVL"] = skill_4
		
		self.skill4.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[3], skill_4_grade, skill_4_lvl)
		self.skill4.SetSlotCountNew(0, skill_4_grade, skill_4_lvl)
		
		if skill_4 >= 40: #max_lvl
			self.upgradeBtn_4.Hide()
		elif self.healingSkillsUnlocked:
			self.upgradeBtn_4.Show()
		
		skill_5_grade = osfInfo.SkillLevelToGrade(skill_5)
		skill_5_lvl = osfInfo.SkillLevelToLvl(skill_5)
		
		osfInfo.SUPPORT_SKILLS[5]["GRADE"] = skill_5_grade
		osfInfo.SUPPORT_SKILLS[5]["LVL"] = skill_5_lvl
		osfInfo.SUPPORT_SKILLS[5]["REAL_LVL"] = skill_5
		
		self.skill5.SetSkillSlotNew(0, osfInfo.SUPPORT_SKILL_VNUMS[4], skill_5_grade, skill_5_lvl)
		self.skill5.SetSlotCountNew(0, skill_5_grade, skill_5_lvl)
		
		if skill_5 >= 40: #max_lvl
			self.upgradeBtn_5.Hide()
		elif self.healingSkillsUnlocked:
			self.upgradeBtn_5.Show()
		# the open reading window shows the new level
		if self.interface and hasattr(self.interface, "RefreshReadingWindows"):
			self.interface.RefreshReadingWindows()
		# and so does an open Buffi skill tooltip (this window's or the reading window's)
		tooltip = getattr(self.interface, "tooltipSkill", None) if getattr(self, "interface", None) else None
		if tooltip and hasattr(tooltip, "RefreshShown"):
			tooltip.RefreshShown()

	def SetDefaultInfo(self):
		self.supportname.SetText("")
		self.supportInt.SetText("")

		self.skillLock_4.Show()
		self.skillLock_5.Show()
		self.healingSkillsUnlocked = False

		self.upgradeBtn_1.Show()
		self.upgradeBtn_2.Show()
		self.upgradeBtn_3.Show()
		self.upgradeBtn_4.Show()
		self.upgradeBtn_5.Show()

		for i in range(7):
			self.equipSlot.wndEquip.ClearSlot(i)

		self.SetProgress(1, 0, 1000, 0, 0, 0)

	def SetProgress(self, level, currentExp, requiredExp, passivePoints, healingUnlocked, expMode=1, form=0, hairEnabled=1):
		level = max(1, int(level))
		currentExp = max(0, int(currentExp))
		requiredExp = max(0, int(requiredExp))
		passivePoints = max(0, int(passivePoints))
		healingUnlocked = int(healingUnlocked) != 0
		self.expMode = max(0, min(2, int(expMode)))
		self.form = int(form)
		self.RefreshExpModeButtons()
		if self.equipSlot:
			if self.form or not int(hairEnabled):
				self.equipSlot.wndEquip.ClearSlot(2)
				self.equipSlot.wndEquip.DisableSlot(2)
			else:
				self.equipSlot.wndEquip.EnableSlot(2)

		self.SetPremiumSkill(healingUnlocked)
		self.progressLevelText.SetText("Úroveň %d" % level)
		self.progressPassiveText.SetText("Pasivní body: %d" % passivePoints)
		if requiredExp > 0:
			self.progressGauge.SetPercentage(min(currentExp, requiredExp), requiredExp)
			self.progressExpText.SetText("%d / %d EXP" % (currentExp, requiredExp))
		else:
			self.progressGauge.SetPercentage(1, 1)
			self.progressExpText.SetText("MAX")

		if level >= 100:
			self.progressStatusText.SetText("Maximální úroveň")
			self.progressStatusText.SetPackedFontColor(0xffECC576)
		elif not healingUnlocked:
			self.progressStatusText.SetText("BZK od úrovně hráče 90")
			self.progressStatusText.SetPackedFontColor(0xffB8B8B8)
		elif self.expMode == 0:
			self.progressStatusText.SetText("Získávání EXP vypnuto")
			self.progressStatusText.SetPackedFontColor(0xffD69A72)
		else:
			self.progressStatusText.SetText("Získávání BZK aktivní")
			self.progressStatusText.SetPackedFontColor(0xff8AC28F)
		SyncR1(self)

	def RefreshExpModeButtons(self):
		for index, button in enumerate(self.expModeButtons):
			button.Down() if index == self.expMode else button.SetUp()

	def OnSelectExpMode(self, mode):
		self.RefreshExpModeButtons()
		if not self.healingSkillsUnlocked:
			return
		net.SendChatPacket("/support_exp_mode %d" % int(mode))


	def SetInteligence(self, inteligence):
		self.supportInt.SetText("%s %d" % (localeInfo.SUPPORT_INT, int(inteligence)))
		player.SetSupportIntPoint(inteligence)
		SyncR1(self)
		
	def SetArmor(self, vnum):
		osfInfo.SUPPORT_EQUIPMENT[osfInfo.SUPPORT_SLOT_ARMOR] = vnum
		self.equipSlot.wndEquip.SetItemSlot(1, int(vnum), 0)
		
	def SetHair(self, vnum):
		osfInfo.SUPPORT_EQUIPMENT[osfInfo.SUPPORT_SLOT_HAIR] = vnum
		self.equipSlot.wndEquip.SetItemSlot(2, int(vnum), 0)
		
	def SetWeapon(self, vnum):
		osfInfo.SUPPORT_EQUIPMENT[osfInfo.SUPPORT_SLOT_WEAPON] = vnum
		self.equipSlot.wndEquip.SetItemSlot(3, int(vnum), 0)
		
	def SetWeaponShining(self, vnum):
		osfInfo.SUPPORT_EQUIPMENT[osfInfo.SUPPORT_SLOT_EFFECT_WEAPON] = vnum
		self.equipSlot.wndEquip.SetItemSlot(4, int(vnum), 0)
		
	def SetArmorShining(self, vnum):
		osfInfo.SUPPORT_EQUIPMENT[osfInfo.SUPPORT_SLOT_EFFECT_ARMOR] = vnum
		self.equipSlot.wndEquip.SetItemSlot(5, int(vnum), 0)
		
	def SetAcce(self, vnum):
		osfInfo.SUPPORT_EQUIPMENT[osfInfo.SUPPORT_SLOT_SASH] = vnum
		self.equipSlot.wndEquip.SetItemSlot(6, int(vnum), 0)
		
	def SetName(self, name):
		if name == player.GetMainCharacterName():
			self.supportname.SetText(localeInfo.UNNAMED)
		else:
			self.supportname.SetText(name)
		SyncR1(self)

	def OnSelectItemSlot(self, selectedSlotPos):
		if self.form and selectedSlotPos == osfInfo.SUPPORT_SLOT_HAIR:
			return
		if self.form and not mouseModule.mouseController.isAttached():
			if selectedSlotPos == osfInfo.SUPPORT_SLOT_ARMOR:
				net.SendChatPacket("/support_elf_remove")
			return
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			if attachedSlotType != player.SLOT_TYPE_INVENTORY:
				return
				
			mouseModule.mouseController.DeattachObject()

			self.EquipFromInventory(attachedSlotPos, selectedSlotPos)
	
	# Shared by dragging an inventory item onto an equipment slot and by a right
	# click on a VIP elf outfit in the inventory (uiinventory.__UseItem): same
	# client checks, confirmation dialog and /support_system request.
	def EquipFromInventory(self, attachedSlotPos, selectedSlotPos):
		itemVnum = player.GetItemIndex(attachedSlotPos)
		item.SelectItem(itemVnum)
		elf = bool(self.form)
		if elf and selectedSlotPos != osfInfo.SUPPORT_SLOT_ARMOR:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.VIP_ELF_PARTS_BAKED)
			return
		if elf != IsVipElfOutfit(itemVnum):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.VIP_ELF_WRONG_FORM)
			return
		itemName = item.GetItemName()
		itemType = item.GetItemType()
		itemSubType = item.GetItemSubType()
		
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.FEMALE_COSTUME_ONLY)
			return
			
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_SHAMAN):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_CANNOT_BE_EQUIPPED_FOR_SHAMAN)
			return
			
		canPut = False
			
		if selectedSlotPos == osfInfo.SUPPORT_SLOT_ARMOR:
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_BODY:
				canPut = True
				
			if not canPut:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PUT_HERE_ONLY_COSTUMES)
				return
				
		if selectedSlotPos == osfInfo.SUPPORT_SLOT_HAIR:
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_HAIR:
				canPut = True
				
			if not canPut:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PUT_HERE_ONLY_HAIR)
				return
				
		if selectedSlotPos == osfInfo.SUPPORT_SLOT_WEAPON:
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_WEAPON:
				canPut = True
				
			if not canPut:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PUT_HERE_ONLY_WEAPON)
				return
				
		if selectedSlotPos == osfInfo.SUPPORT_SLOT_EFFECT_WEAPON:
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_EFFECT_WEAPON:
				canPut = True
				
			if not canPut:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PUT_HERE_ONLY_EFFECT_WEAPON)
				return
				
		if selectedSlotPos == osfInfo.SUPPORT_SLOT_EFFECT_ARMOR:
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_EFFECT_ARMOR:
				canPut = True
				
			if not canPut:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PUT_HERE_ONLY_EFFECT_ARMOR)
				return
				
		if selectedSlotPos == osfInfo.SUPPORT_SLOT_SASH:
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_ACCE_SKIN:
				canPut = True
				
			if not canPut:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PUT_HERE_ONLY_SASH)
				return

		# A repeated right click must not leave an older dialog bound to this one.
		if self.questionDialog:
			self.questionDialog.Close()
		questionDialog = uiCommon.QuestionDialog2()
		questionDialog.SetText1(localeInfo.SUPPORT_EQUIP_ITEM_WARNING_1 % itemName)
		questionDialog.SetText2(localeInfo.SUPPORT_EQUIP_ITEM_WARNING_2)
		if elf:
			questionDialog.SetText1(localeInfo.VIP_ELF_EQUIP_1 % itemName)
			questionDialog.SetText2(localeInfo.VIP_ELF_EQUIP_2)
		questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnAcceptEquipItem))
		questionDialog.SetCancelEvent(self.OnCancelEquipItem)
		questionDialog.attachedSlotPos = attachedSlotPos
		questionDialog.selectedSlotPos = selectedSlotPos
		questionDialog.Open()
		self.questionDialog = questionDialog
	
	def OnSelectEmptySlot(self, selectedSlotPos):
		self.OnSelectItemSlot(selectedSlotPos)
			
	def OnAcceptEquipItem(self):
		attachedSlotPos = self.questionDialog.attachedSlotPos
		selectedSlotPos = self.questionDialog.selectedSlotPos

		if selectedSlotPos == 1:
			net.SendChatPacket("/support_system %s" % (str(attachedSlotPos)))
		if selectedSlotPos == 3:
			net.SendChatPacket("/support_system_w %s" % (str(attachedSlotPos)))
		if selectedSlotPos == 2 and not self.form:
			net.SendChatPacket("/support_system_d %s" % (str(attachedSlotPos)))
		if selectedSlotPos == 5:
			net.SendChatPacket("/support_system_a_shining %s" % (str(attachedSlotPos)))
		if selectedSlotPos == 4:
			net.SendChatPacket("/support_system_w_shining %s" % (str(attachedSlotPos)))
		if selectedSlotPos == 6:
			net.SendChatPacket("/support_system_acce %s" % (str(attachedSlotPos)))
	
		self.questionDialog.Close()
		self.questionDialog = None
	
	def OnCancelEquipItem(self):
		self.questionDialog.Close()
		self.questionDialog = None
		
