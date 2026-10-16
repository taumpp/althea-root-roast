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

MAX_COUNT = 20

class SupportUpgrade(ui.ScriptWindow):

	def __init__(self): 
		self.isLoaded = 0
		
		self.board = None
		self.slots = None
		self.cancelBtn = None
		self.confirmBtn = None
		self.toolTipSkill = 0
		self.curCount = 1
		self.useExorcismBook = 1
		self.useLuckBook = 1
		self.skillID = 1
		self.itemUpgraderImg = None
		self.itemUpgraderVnum = 0
		self.itemExorcismVnum = 0
		self.itemReadingVnum = 0
		self.itemExorcism = 0
		self.itemReading = 0
		self.toolTipItem = None
		self.isItemToolTipHidden = True
		
		ui.ScriptWindow.__init__(self)
		self.__LoadWindow()

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/buffupgrade.py")
		except:
			import exception
			exception.Abort("SupportUpgrade.__LoadWindow error")
			
		try:
			self.board = self.GetChild("board")
			self.slots = self.GetChild("SkillSlots")
			
			self.confirmBtn = self.GetChild("confirm")
			self.cancelBtn = self.GetChild("cancel")
			self.countText = self.GetChild("currentCount")
			self.countControl = self.GetChild("CountController")
			self.countControl.SetEvent(ui.__mem_func__(self.OnChangeCount))
			
			self.slots.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectSkill))
			self.slots.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectSkill))
			self.slots.SetUnselectItemSlotEvent(ui.__mem_func__(self.SelectSkill))
			self.slots.SetUseSlotEvent(ui.__mem_func__(self.SelectSkill))
			self.slots.SetPressedSlotButtonEvent(ui.__mem_func__(self.SelectSkill))
			self.slots.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
			self.slots.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			
			for xx in range(5):
				self.slots.SetCoverButton(xx+1)
			
			self.board.SetCloseEvent(self.Hide)
			self.cancelBtn.SetEvent(ui.__mem_func__(self.Hide))
			self.confirmBtn.SetEvent(ui.__mem_func__(self.Confirm))

			self.itemUpgraderImg = ui.ImageBox()
			self.itemUpgraderImg.SetParent(self)
			self.itemUpgraderImg.LoadImage("icon/item/50513.tga")
			self.itemUpgraderImg.SetPosition(195, 127)
			self.itemUpgraderImg.Show()

			self.SlotLuckItem = ui.ImageBox()
			self.SlotLuckItem.SetParent(self)
			self.SlotLuckItem.SetPosition(60, 127)
			self.SlotLuckItem.LoadImage("d:/ymir work/ui/public/Slot_Base.sub")
			self.SlotLuckItem.Show()

			self.itemExorcism = ui.ImageBox()
			self.itemExorcism.SetParent(self.SlotLuckItem)
			self.itemExorcism.LoadImage("icon/item/71001.tga")
			self.itemExorcism.SetPosition(0, 0)
			self.itemExorcism.Show()

			self.checkBoxLuck = ui.CheckBox()
			self.checkBoxLuck.SetParent(self)
			self.checkBoxLuck.SetPosition(35, 138)
			self.checkBoxLuck.SetEvent(ui.__mem_func__(self.SetUseLuckBook), "ON_CHECK", 1)
			self.checkBoxLuck.SetEvent(ui.__mem_func__(self.SetUseLuckBook), "ON_UNCKECK", 0)
			self.checkBoxLuck.SetCheckStatus(1)
			self.checkBoxLuck.Show()

			self.SlotTimeItem = ui.ImageBox()
			self.SlotTimeItem.SetParent(self)
			self.SlotTimeItem.SetPosition(136, 127)
			self.SlotTimeItem.LoadImage("d:/ymir work/ui/public/Slot_Base.sub")
			self.SlotTimeItem.Show()

			self.itemReading = ui.ImageBox()
			self.itemReading.SetParent(self.SlotTimeItem)
			self.itemReading.LoadImage("icon/item/71094.tga")
			self.itemReading.SetPosition(0, 0)
			self.itemReading.Show()

			self.checkBoxTime = ui.CheckBox()
			self.checkBoxTime.SetParent(self)
			self.checkBoxTime.SetPosition(111, 138)
			self.checkBoxTime.SetEvent(ui.__mem_func__(self.SetUseExorcismBook), "ON_CHECK", 1)
			self.checkBoxTime.SetEvent(ui.__mem_func__(self.SetUseExorcismBook), "ON_UNCKECK", 0)
			self.checkBoxTime.SetCheckStatus(1)
			self.checkBoxTime.Show()
			
		except:
			import exception
			exception.Abort("SupportUpgrade.LoadWindow.BindObject")
			
		self.SetCenterPosition()
		
	def OnUpdate(self):
		if self.toolTipItem:
			if self.itemUpgraderImg != None:
				if self.itemUpgraderImg.IsIn():
					self.OverInUpgraderItem()
				elif self.itemExorcism.IsIn():
					self.OverInExorcismItem()
				elif self.itemReading.IsIn():
					self.OverInReadingItem()
				elif not self.isItemToolTipHidden:
					self.OverOutUpgraderItem()
		
	def SetSkill(self, skillID):
		self.skillID = skillID
		self.SetSlotSkill(skillID)
		# 1 = Dragon's Aid 196 (96+100)
		# 2 = Blessing 194 (94+100)
		# 3 = Reflect 195 (95+100)
		# 4 = Swiftness 197 (97+100)
		# 5 = Attack Up 198 (98+100)
		
	def SetSlotSkill(self, skillID):
		skillVnum = {
			1 : 196,
			2 : 194,
			3 : 195,
			4 : 197,
			5 : 198,
		}
		
		skillName = skill.GetSkillName(skillVnum[skillID], osfInfo.SUPPORT_SKILLS[skillID]["GRADE"])
		self.board.SetTitleName(localeInfo.SUPPORT_UPGRADING_SKILL % skillName)
		
		for i in range(5):
			self.slots.SetSkillSlotNew(i+1, skillVnum[i+1], osfInfo.SUPPORT_SKILLS[i+1]["GRADE"], osfInfo.SUPPORT_SKILLS[i+1]["LVL"])
			self.slots.SetSlotCountNew(i+1, osfInfo.SUPPORT_SKILLS[i+1]["GRADE"], osfInfo.SUPPORT_SKILLS[i+1]["LVL"])
			
		self.slots.ActivateSlot(skillID)
		self.DeactivateSlotEffects(skillID)
		
		skillToBookVnum = {
			1 : 50496,
			2 : 50494,
			3 : 50495,
			4 : 50510,
			5 : 50511,
		}
		
		selectedSkillLevel = osfInfo.SUPPORT_SKILLS[skillID]["REAL_LVL"]
		itemUpgrader = 0
		if selectedSkillLevel < 30:
			itemUpgrader = skillToBookVnum[skillID]
			self.itemExorcismVnum = 71001
			self.itemReadingVnum = 71094
		elif selectedSkillLevel < 40:
			itemUpgrader = 50513
			self.itemExorcismVnum = 71001
			self.itemReadingVnum = 71094

		self.itemUpgraderVnum = itemUpgrader
		
		item.SelectItem(itemUpgrader)
		self.itemUpgraderImg.LoadImage(item.GetIconImageFileName())
		
		item.SelectItem(self.itemExorcismVnum)
		self.itemExorcism.LoadImage(item.GetIconImageFileName())
		
		item.SelectItem(self.itemReadingVnum)
		self.itemReading.LoadImage(item.GetIconImageFileName())

	def SetUseExorcismBook(self, checkType, bUse):
		self.useExorcismBook = bUse
		
	def SetUseLuckBook(self, checkType, bUse):
		self.useLuckBook = bUse
		
	def OnChangeCount(self):
		openTemp = int(self.countControl.GetSliderPos() * MAX_COUNT)
		if openTemp == 0:
			self.SetCount(1)
		else:
			self.SetCount(openTemp)
			
	def SetCount(self, amount):
		self.curCount = amount
		self.countText.SetText(str(amount) + "x")
		# self.checkBoxLuck.SetTextInfo(localeInfo.SOUL_STONE_USE + " " + str(self.curCount) + "x " + localeInfo.SOUL_STONE_ITEM_1)
		# self.checkBoxTime.SetTextInfo(localeInfo.SOUL_STONE_USE + " " + str(self.curCount) + "x " + localeInfo.SOUL_STONE_ITEM_2)
		
	def SelectSkill(self, index):
		if osfInfo.SUPPORT_SKILLS[index]["REAL_LVL"] >= 40:
			return
			
		self.SetSkill(index)
		
		self.DeactivateSlotEffects(index)
				
	def DeactivateSlotEffects(self, skillID):
		startSlotIndex = self.slots.GetStartIndex()
		for i in range(6):
			slotIndex = i + startSlotIndex
			if slotIndex != skillID:
				self.slots.DeactivateSlot(slotIndex)
		
	def OverInItem(self, slotNumber):
		if 0 == self.toolTipSkill:
			return
		
		skillVnum = {
			1 : 196,
			2 : 194,
			3 : 195,
			4 : 197,
			5 : 198,
		}
		
		skillIndex = skillVnum[slotNumber]
		skillLevel = osfInfo.SUPPORT_SKILLS[slotNumber]["LVL"]
		skillGrade = osfInfo.SUPPORT_SKILLS[slotNumber]["GRADE"]
		skillRealLvl = osfInfo.SUPPORT_SKILLS[slotNumber]["REAL_LVL"]
		
		self.toolTipSkill.SetSupportSkill(skillIndex, skillLevel, skillGrade, skillRealLvl)
		
	def OverOutItem(self):
		if 0 != self.toolTipSkill:
			self.toolTipSkill.HideToolTip()
		
	def SetSkillToolTip(self, toolTipSkill):
		self.toolTipSkill = toolTipSkill
		
	def Confirm(self):
		strArg = str(self.skillID) + " " + str(self.curCount) + " " + str(self.useExorcismBook) + " " + str(self.useLuckBook)
		net.SendChatPacket("/support_upgrade " + str(strArg))
		self.Close()

	def OnPressEscapeKey(self):
		self.Hide()
		return True
		
	def Show(self):
		self.checkBoxTime.SetCheckStatus(self.useExorcismBook)
		self.checkBoxLuck.SetCheckStatus(self.useLuckBook)
		self.countControl.SetSliderPos(0.0)
		self.SetCount(1)		
		ui.ScriptWindow.Show(self)
		
	def Close(self):
		self.Hide()
		
	def Hide(self):
		if 0 != self.toolTipSkill:
			self.toolTipSkill.Hide()
			
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
			
		ui.ScriptWindow.Hide(self)
		
	def SetItemToolTip(self, itemTooltip):
		self.toolTipItem = itemTooltip
		
	def __ShowToolTip(self, itemVnum):
		if self.toolTipItem:
			self.toolTipItem.SetItemOnlyVnum(itemVnum)
			
	def OverInItem2(self, index):
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

	def OverInUpgraderItem(self):
		self.__ShowToolTip(self.itemUpgraderVnum)
		self.isItemToolTipHidden = False
		
	def OverInExorcismItem(self):
		self.__ShowToolTip(self.itemExorcismVnum)
		self.isItemToolTipHidden = False
		
	def OverInReadingItem(self):
		self.__ShowToolTip(self.itemReadingVnum)
		self.isItemToolTipHidden = False

	def OverOutUpgraderItem(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
			
		self.isItemToolTipHidden = True
		
	def Destroy(self):
		self.ClearDictionary()
		self.board = None
		self.slots = None
		self.cancelBtn = None
		self.confirmBtn = None
		self.toolTipSkill = 0
		self.curCount = 1
		self.useExorcismBook = 1
		self.useLuckBook = 1
		self.itemUpgraderImg = None
		self.itemUpgraderVnum = 0
		self.itemExorcismVnum = 0
		self.itemReadingVnum = 0
		self.itemExorcism = 0
		self.itemReading = 0
		self.toolTipItem = None
		self.isItemToolTipHidden = True

	def __del__(self): 
		ui.ScriptWindow.__del__(self) 
