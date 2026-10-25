# -*- coding: utf-8 -*-
# Vylepšování buffy: the Buffi (support shaman) skill upgrade window opened by the "+" buttons of the Šamanská deska.
#
# The same window as "Okno vylepšení dovedností" (uiSkillUpgrade.SkillUpgradeWindow, uiscript skillupgrade.py): the
# skill row, the book / soul stone with the two reading supports (Exorcism scroll 71001, Concentrated reading 71094)
# and their check boxes, the item counts, the slider with "Do G", Potvrdit / Zrušit, its R1 look (the shared R1 frame,
# root/uir1frame.py, item slot C) and "Starý vzhled". Only the Buffi bits differ:
#
# * the skill row shows the five Buffi skills (osfInfo.SUPPORT_SKILLS); every skill below P can be chosen and the
#   choice picks its reading item: the book of that spell until G (level < 30), the server-selected Buffi soul stone until P;
# * the book stage reads like the books of the character skills: the count up to 55 or "Do G" (the server reads
#   until G), the soul stone stage up to 100 attempts;
# * Potvrdit sends "/support_upgrade <skill 1-5> <count | all> <exorcism> <concentrated>" (the server command of the
#   Buffi skills; the arguments as skillbookpolicy.UniversalReadArguments writes them for the character skills).
#   Soul-stone reads also share the optional Zen Bean control and append its flag when checked.
import chat
import localeInfo
import net
import osfInfo
import skillbookpolicy
import servergamedata
import uiSkillUpgrade

SKILL_COUNT = 5
SKILL_VNUMS = {1: 196, 2: 194, 3: 195, 4: 197, 5: 198}         # the client skill vnums of the Buffi skills
SKILL_BOOKS = {1: 50496, 2: 50494, 3: 50495, 4: 50510, 5: 50511}  # the book of each spell (M -> G)
SOUL_STONE = servergamedata.BUFF_SOUL_STONE                       # G -> P, server authority
BOOK_STAGE_END = 30          # REAL_LVL 30 = G1
MAX_LEVEL = 40               # REAL_LVL 40 = P


def HeaderTitle(titleFormat):
	"""The window name of the locale title "Vylepšování buffy [%s]" (the part before the skill name): the full title
	with a long skill name ("Uhánět rychlostí větru") does not fit beside the X of the R1 header."""
	try:
		head = titleFormat.split("%s")[0].rstrip(" [(:-")
	except Exception:
		head = ""
	return head or titleFormat


class SupportUpgrade(uiSkillUpgrade.SkillUpgradeWindow):

	def __init__(self):
		self.skillID = 0
		self.toolTipItem = None
		uiSkillUpgrade.SkillUpgradeWindow.__init__(self)
		self.board.SetTitleName(HeaderTitle(localeInfo.SUPPORT_UPGRADING_SKILL))

	# ------------------------------------------------------------------ the Buffi skills
	def RealLevel(self, skillID):
		try:
			return int(osfInfo.SUPPORT_SKILLS[skillID]["REAL_LVL"])
		except Exception:
			return MAX_LEVEL

	def IsBookStage(self):
		return 0 < self.skillID and self.RealLevel(self.skillID) < BOOK_STAGE_END

	def SoulStoneSkill(self):
		"""The skill of the Buffi soul stone (OpenSupportUpgrade 0): the first one between G and P, else the first one
		below P, else the first one."""
		order = sorted(SKILL_VNUMS)
		for slot in order:
			if BOOK_STAGE_END <= self.RealLevel(slot) < MAX_LEVEL:
				return slot
		for slot in order:
			if self.RealLevel(slot) < MAX_LEVEL:
				return slot
		return order[0]

	def SetSkill(self, skillID):
		"""Opens the window for one Buffi skill (1 - 5): its reading item and the title; 0: the soul stone skill."""
		if 0 == skillID:
			skillID = self.SoulStoneSkill()
		if skillID not in SKILL_VNUMS:
			return
		self.skillID = skillID
		self.SetUpgradeItem(SKILL_BOOKS[skillID] if self.IsBookStage() else SOUL_STONE)
		self.board.SetTitleName(HeaderTitle(localeInfo.SUPPORT_UPGRADING_SKILL))
		if self.IsShow():
			self.Show()

	def SetSlotSkill(self, skillID):
		self.SetSkill(skillID)

	def RefreshSkillPage(self):
		skillPage = self.slots
		startSlotIndex = uiSkillUpgrade.SKILL_SLOT_START
		self.isSlotSelectable = [False for x in range(startSlotIndex + 6)]
		for i in range(6):
			slotIndex = startSlotIndex + i
			skillPage.ClearSlot(slotIndex)
			skillPage.DeactivateSlot(slotIndex)
			if slotIndex not in SKILL_VNUMS:
				continue
			info = osfInfo.SUPPORT_SKILLS[slotIndex]
			skillPage.SetSkillSlotNew(slotIndex, SKILL_VNUMS[slotIndex], info["GRADE"], info["LVL"])
			skillPage.SetSlotCountNew(slotIndex, info["GRADE"], info["LVL"])
			skillPage.SetCoverButton(slotIndex)
			if self.RealLevel(slotIndex) < MAX_LEVEL:
				self.isSlotSelectable[slotIndex] = True
			else:
				skillPage.DisableCoverButton(slotIndex)
		if 0 < self.selectedSlot < len(self.isSlotSelectable) and self.isSlotSelectable[self.selectedSlot]:
			skillPage.ActivateSlot(self.selectedSlot)
		else:
			self.selectedSlot = 0
		skillPage.RefreshSlot()

	def SelectBookSkill(self):
		if self.skillID and self.isSlotSelectable[self.skillID]:
			uiSkillUpgrade.SkillUpgradeWindow.ClickSkillSlot(self, self.skillID)

	def SelectSkill(self, index):
		self.__Choose(index)

	def ClickSkillSlot(self, index):
		self.__Choose(index)

	def __Choose(self, index):
		"""Another skill: its own reading item (book or soul stone), the count from the start."""
		if not 0 <= index < len(self.isSlotSelectable) or not self.isSlotSelectable[index]:
			return
		if index != self.skillID:
			self.SetSkill(index)
		uiSkillUpgrade.SkillUpgradeWindow.ClickSkillSlot(self, index)

	# ------------------------------------------------------------------ the reading rules
	def IsUniversalBook(self):
		"""The book stage reads like the character skill books: up to 55 or "Do G"."""
		return self.IsBookStage()

	def UsesSoulStone(self):
		return self.itemUpgraderVnum == SOUL_STONE

	def MaxCount(self):
		return skillbookpolicy.MAX_SELECTED_BOOKS if self.IsBookStage() else uiSkillUpgrade.SOUL_STONE_MAX_COUNT

	def Confirm(self):
		self.RefreshSkillPage()
		self.SetCount(self.curCount)
		if self.selectedSlot not in SKILL_VNUMS:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SOUL_STONE_GUI)
			return
		count = self.curCount if self.curCount > 0 else 0
		arguments = skillbookpolicy.UniversalReadArguments(
			self.selectedSlot, count, self.useExorcismBook, self.useLuckBook)
		if self.UsesSoulStone() and self.useZenBean:
			arguments += " %d" % self.useZenBean
		net.SendChatPacket("/support_upgrade " + arguments)
		# the window stays open (see uiskillupgrade.SkillUpgradeWindow.Confirm)
		self.Refresh()

	def ItemForSkill(self, slot):
		self.skillID = slot
		return SKILL_BOOKS[slot] if self.IsBookStage() else SOUL_STONE

	def FollowsSkillGrade(self):
		return False

	# ------------------------------------------------------------------ tooltips
	def OverInItem(self, slotNumber):
		if 0 == self.toolTipSkill or slotNumber not in SKILL_VNUMS:
			return
		info = osfInfo.SUPPORT_SKILLS[slotNumber]
		self.toolTipSkill.SetSupportSkill(SKILL_VNUMS[slotNumber], info["LVL"], info["GRADE"], info["REAL_LVL"])
		# rebuilt from the new level when the Buffi levels arrive (uibuff.SetSkillLvl)
		remember = getattr(self.toolTipSkill, "RememberRefresh", None)
		if remember:
			remember(self.OverInItem, slotNumber)

	def SetItemToolTip(self, itemTooltip):
		self.toolTipItem = itemTooltip

	def OverInItem2(self, itemType):
		"""The tooltip of the book / soul stone and of the two reading supports, as the original Buffi window showed it:
		ItemToolTip.SetItemOnlyVnum (the item name, its description and the GM Vnum / ItemType / ItemSubType lines).
		The inherited SetItemToolTip(vnum) would take the character skill book branch of ItemToolTip.AddItemData
		(ITEM_TYPE_SKILLBOOK 50401 - 50511) and show the skill of the book ("Zrcadlit Kniha schopností" with the three
		grade icons) instead of the book of the spell."""
		vnum = {"upgrader": self.itemUpgraderVnum, "luck": self.itemLuckVnum, "time": self.itemTimeVnum,
			"zen": self.itemZenVnum}.get(itemType)
		tooltip = self.toolTipItem
		if tooltip is None:
			interface = osfInfo.GetInterfaceInstance()
			tooltip = interface.tooltipItem if interface else None
		if not vnum or tooltip is None:
			return uiSkillUpgrade.SkillUpgradeWindow.OverInItem2(self, itemType)
		tooltip.SetItemOnlyVnum(vnum)

	def Destroy(self):
		self.toolTipItem = None
		uiSkillUpgrade.SkillUpgradeWindow.Destroy(self)
