import ui
import app
import localeInfo
import constInfo
import player
import net
import chrmgr
import wndMgr
import mouseModule
import guild
import skill
import item
import chr
import uiToolTip
import chat

class AutoHuntingSystemWindow(ui.ScriptWindow):
	AUTO_COOLTIME_POS_Y = 4
	AUTO_COOLTIME_POS_X = 6
	AUTO_COOLTIME_MAX = AUTO_COOLTIME_POS_Y * AUTO_COOLTIME_POS_X
	AUTO_ONOFF_START = 1
	AUTO_ONOFF_ATTACK = 2
	AUTO_ONOFF_SKILL = 3
	AUTO_ONOFF_POSITION = 4
	AUTO_ONOFF_AUTO_RANGE = 5
	AUTO_ONOFF_AUTO_RESTART = 6

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.ResetAttributes()
		self.AutoSystemToolTipList = [
			localeInfo.AUTO_TOOLTIP_LINE1, localeInfo.AUTO_TOOLTIP_LINE2,
			localeInfo.AUTO_TOOLTIP_LINE3, localeInfo.AUTO_TOOLTIP_LINE4,
			localeInfo.AUTO_TOOLTIP_LINE5, localeInfo.AUTO_TOOLTIP_LINE6,
			localeInfo.AUTO_TOOLTIP_LINE7, localeInfo.AUTO_TOOLTIP_LINE8,
		]
		self._EnsureLoaded()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		self.ResetAttributes()

	def ResetAttributes(self):
		self.isloded = 0
		self.isOpen = 0
		self.tooltipSkill = 0
		self.tooltipItem = 0
		self.autostartonoff = 0
		self.autoslotindex = {}
		self.timeeditlist = {}
		self.autoonoffbuttonlist = []
		self.saveButton = 0
		self.autoslot = None
		self.autoPotionSlot = None
		self.AutoSkillClearButton = None
		self.AutoPositionClearButton = None
		self.AutoAllClearButton = None
		self.AutoToolTipButton = None
		self.AutoToolTip = None
		self.autoAttackOptionWindow = None
		self.autoHuntingRangeWindow = None
		self.autoAttackOptionButton = None
		self.autoRangeSelectButton = None
		self.closegame = False
		self.isFirstReadFile = False
		for i in range(player.AUTO_SKILL_SLOT_MAX):
			self.autoslotindex[i] = 0
		for i in range(player.AUTO_POSITINO_SLOT_START, player.AUTO_POSITINO_SLOT_MAX):
			self.autoslotindex[i] = 0

	def __LoadWindow(self):
		try:
			GetObject = self.GetChild
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/autohuntingwindow.py")
			self.GetChild("board").SetCloseEvent(ui.__mem_func__(self.Close))

			self.saveButton = self.GetChild("SaveButton")
			self.saveButton.SetEvent(ui.__mem_func__(self.SaveAutoInfo))

			autostartbutton = self.GetChild("StartButton")
			autostartbutton.SetEvent(ui.__mem_func__(self.AutoOnOff), 1, self.AUTO_ONOFF_START, 0)
			self.autoonoffbuttonlist.append(autostartbutton)

			autoendbutton = self.GetChild("EndButton")
			autoendbutton.SetEvent(ui.__mem_func__(self.AutoOnOff), 0, self.AUTO_ONOFF_START, 1)
			self.autoonoffbuttonlist.append(autoendbutton)

			autoattackbutton = self.GetChild("AutoAttackButton")
			autoattackbutton.SetToggleUpEvent(ui.__mem_func__(self.AutoOnOff), 0, self.AUTO_ONOFF_ATTACK, 2)
			autoattackbutton.SetToggleDownEvent(ui.__mem_func__(self.AutoOnOff), 1, self.AUTO_ONOFF_ATTACK, 2)
			self.autoonoffbuttonlist.append(autoattackbutton)

			autorangebutton = self.GetChild("AutoRangeButton")
			autorangebutton.SetToggleUpEvent(ui.__mem_func__(self.AutoOnOff), 0, self.AUTO_ONOFF_AUTO_RANGE, 3)
			autorangebutton.SetToggleDownEvent(ui.__mem_func__(self.AutoOnOff), 1, self.AUTO_ONOFF_AUTO_RANGE, 3)
			self.autoonoffbuttonlist.append(autorangebutton)

			autopositionbutton = self.GetChild("AutoPotionButton")
			autopositionbutton.SetToggleUpEvent(ui.__mem_func__(self.AutoOnOff), 0, self.AUTO_ONOFF_POSITION, 4)
			autopositionbutton.SetToggleDownEvent(ui.__mem_func__(self.AutoOnOff), 1, self.AUTO_ONOFF_POSITION, 4)
			self.autoonoffbuttonlist.append(autopositionbutton)

			autoskillbutton = self.GetChild("AutoSkillButton")
			autoskillbutton.SetToggleUpEvent(ui.__mem_func__(self.AutoOnOff), 0, self.AUTO_ONOFF_SKILL, 5)
			autoskillbutton.SetToggleDownEvent(ui.__mem_func__(self.AutoOnOff), 1, self.AUTO_ONOFF_SKILL, 5)
			self.autoonoffbuttonlist.append(autoskillbutton)

			autoresetbutton = self.GetChild("AutoRestartHereButton")
			autoresetbutton.SetToggleUpEvent(ui.__mem_func__(self.AutoOnOff), 0, self.AUTO_ONOFF_AUTO_RESTART, 6)
			autoresetbutton.SetToggleDownEvent(ui.__mem_func__(self.AutoOnOff), 1, self.AUTO_ONOFF_AUTO_RESTART, 6)
			self.autoonoffbuttonlist.append(autoresetbutton)

			self.AutoSkillClearButton = self.GetChild("SkillSettingClearButton")
			self.AutoSkillClearButton.SetEvent(ui.__mem_func__(self.AutoSkillClear))
			self.AutoPositionClearButton = self.GetChild("PotionSettingClearButton")
			self.AutoPositionClearButton.SetEvent(ui.__mem_func__(self.AutoPositionClear))
			self.AutoAllClearButton = self.GetChild("SettingAllClearButton")
			self.AutoAllClearButton.SetEvent(ui.__mem_func__(self.AutoAllClear))

			for x in range(self.AUTO_COOLTIME_MAX):
				childname = "editline" + str(x)
				self.timeeditlist[x] = self.GetChild(childname)
				self.timeeditlist[x].SetEscapeEvent(ui.__mem_func__(self.Close))

			self.autoslot = self.GetChild("AutoHuntingSkillSlot")
			self.autoslot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			self.autoslot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectActiveSkillEmptySlot))
			self.autoslot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectActiveSkillSlot))
			self.autoslot.SetOverInItemEvent(ui.__mem_func__(self.OverActiveSkillSlot))
			self.autoslot.SetOverOutItemEvent(ui.__mem_func__(self.OverSkillSlotOutItem))
			self.autoslot.Show()

			self.autoPotionSlot = self.GetChild("AutoHuntingPotionSlot")
			self.autoPotionSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			self.autoPotionSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectActivePotionEmptySlot))
			self.autoPotionSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectActivePotionSlot))
			self.autoPotionSlot.SetOverInItemEvent(ui.__mem_func__(self.OverActivePotionSlot))
			self.autoPotionSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverSkillSlotOutItem))
			self.autoPotionSlot.Show()

			self.AutoToolTipButton = self.GetChild("HelpButton")
			self.AutoToolTip = self.__CreateGameTypeToolTip(localeInfo.AUTO_TOOLTIP_TITLE,self.AutoSystemToolTipList)
			self.AutoToolTip.SetTop()
			self.AutoToolTipButton.SetToolTipWindow(self.AutoToolTip)

			self.autoAttackOptionWindow = AutoAttackOptionWindow()
			self.autoAttackOptionWindow.BindAutoHuntingWindow(self)
			self.autoAttackOptionWindow.Hide()

			self.autoHuntingRangeWindow = AutoHuntingRangeWindow()
			self.autoHuntingRangeWindow.BindAutoHuntingWindow(self)
			self.autoHuntingRangeWindow.Hide()

			self.autoAttackOptionButton = self.GetChild("AutoAttackOptionButton")
			self.autoAttackOptionButton.SetEvent(ui.__mem_func__(self.ToggleAutoAttackOptionWindow))

			self.autoRangeSelectButton = self.GetChild("AutoRangeSelectButton")
			self.autoRangeSelectButton.SetEvent(ui.__mem_func__(self.ToggleAutoHuntingRangeWindow))

			for i in range(2, 7):
				if i < len(self.autoonoffbuttonlist):
					self.autoonoffbuttonlist[i].SetText(localeInfo.CHATTING_SETTING_LANGUAGE_OFF)

		except:
			import exception
			exception.Abort("AutoHuntingSystemWindow.__LoadWindow.UIScript/autohuntingwindow.py")

	def __CreateGameTypeToolTip(self, title, descList):
		toolTip = uiToolTip.ToolTip()
		toolTip.SetTitle(title)
		toolTip.AppendSpace(5)

		for desc in descList:
			toolTip.AutoAppendTextLine(desc)

		toolTip.AlignHorizonalCenter()
		toolTip.SetTop()
		return toolTip

	def _ClearSlotRange(self, slotRange):
		for i in slotRange:
			self.autoslotindex[i] = 0

	def AutoSkillClear(self):
		if not self.GetAutoStartonoff():
			player.ClearAutoSKillSlot()
			self.RefreshAutoSkillSlot()
			self._ClearSlotRange(range(player.AUTO_SKILL_SLOT_MAX))

	def AutoPositionClear(self):
		if not self.GetAutoStartonoff():
			player.ClearAutoPositionSlot()
			self.RefreshAutoPositionSlot()
			self._ClearSlotRange(range(player.AUTO_POSITINO_SLOT_START, player.AUTO_POSITINO_SLOT_MAX))

	def AutoAllClear(self):
		if not self.GetAutoStartonoff():
			player.ClearAutoAllSlot()
			self.RefreshAutoSkillSlot()
			self.RefreshAutoPositionSlot()
			self._ClearSlotRange(range(player.AUTO_SKILL_SLOT_MAX))
			self._ClearSlotRange(range(player.AUTO_POSITINO_SLOT_START, player.AUTO_POSITINO_SLOT_MAX))

	def CheckCooltimeText(self, cooltime):
		try:
			return int(cooltime) if cooltime else 0
		except ValueError:
			return 0

	def AutoOnOff(self, onoff, type, number, command = False):
		if not self.isloded:
			return

		if type == self.AUTO_ONOFF_START:
			if onoff == 1:
				if player.CanStartAuto() == False:
					return

				if player.GetItemIndex(player.EQUIPMENT, item.EQUIPMENT_WEAPON) == 0:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AUTO_HUNTING_MSG_CANNOT_START_WITHOUT_WEAPON)
					return

				for i in range(player.AUTO_SKILL_SLOT_MAX):
					cooltime = self.timeeditlist[i].GetText()
					cooltime = self.CheckCooltimeText(cooltime)
					cooltime = player.CheckSkillSlotCoolTime(i, self.autoslotindex[i], int(cooltime))
					if not cooltime == 0:
						player.SetAutoSlotCoolTime(i, int(cooltime))
						self.timeeditlist[i].SetText(str(cooltime))

				for i in range(player.AUTO_POSITINO_SLOT_START, player.AUTO_POSITINO_SLOT_MAX):
					cooltime = self.timeeditlist[i-1].GetText()
					cooltime = self.CheckCooltimeText(cooltime)
					cooltime = player.CheckPositionSlotCoolTime(i, self.autoslotindex[i], int(cooltime))
					if not cooltime == 0:
						player.SetAutoSlotCoolTime(i,int(cooltime))
						self.timeeditlist[i - 1].SetText(str(cooltime))
			else:
				for i in range(player.AUTO_POSITINO_SLOT_START, player.AUTO_POSITINO_SLOT_MAX):
					self.SetAutoCooltime(i, 0)

			player.AutoStartOnOff(onoff, command)
			self.autostartonoff = onoff

			if onoff == 1 and self.autoAttackOptionWindow:
				self.autoAttackOptionWindow.ApplyFilters()

			self.autoonoffbuttonlist[number].Down()
			self.autoonoffbuttonlist[number].Disable()
			if onoff == 1:
				number = number + 1

				if self.autoRangeSelectButton:
					self.autoRangeSelectButton.Disable()
				if self.autoHuntingRangeWindow and self.autoHuntingRangeWindow.IsShow():
					self.autoHuntingRangeWindow.Close()
			else:
				number = number - 1

				if self.autoRangeSelectButton:
					self.autoRangeSelectButton.Enable()

			self.autoonoffbuttonlist[number].SetUp()
			self.autoonoffbuttonlist[number].Enable()

		elif type == self.AUTO_ONOFF_ATTACK:
			player.AutoAttackOnOff(onoff)
		elif type == self.AUTO_ONOFF_SKILL:
			player.AutoSkillOnOff(onoff)
		elif type == self.AUTO_ONOFF_POSITION:
			player.AutoPositionOnOff(onoff)
		elif type == self.AUTO_ONOFF_AUTO_RANGE:
			if self.autostartonoff:
				if onoff == 1:
					self.autoonoffbuttonlist[number].SetUp()
				else:
					self.autoonoffbuttonlist[number].Down()
				return
			player.AutoRangeOnOff(onoff)
		elif type == self.AUTO_ONOFF_AUTO_RESTART:
			net.SendCommandPacket("/res_auto " + str(1 if onoff else 0))
			player.SetAutoRestart(bool(onoff))

		if type != self.AUTO_ONOFF_START:
			self.autoonoffbuttonlist[number].SetText(localeInfo.CHATTING_SETTING_LANGUAGE_ON if onoff else localeInfo.CHATTING_SETTING_LANGUAGE_OFF)

		if command == True:
			if onoff == False:
				self.Close()
				return

	def _EnsureLoaded(self):
		if not self.isloded:
			self.isloded = 1
			self.__LoadWindow()
			self.SetCenterPosition()

	def LoadAutoWindow(self):
		self._EnsureLoaded()
		self.ReadAutoInfo()

	def Show(self):
		self._EnsureLoaded()

		self.SetTop()
		self.ReadAutoInfo()
		self.RefreshAutoPositionSlot()
		self.RefreshAutoSkillSlot()
		self.isOpen = 1

		if not item.CheckAffect(chr.AFFECT_AUTO_USE, 0):
			for i in range(4, 7):
				self.autoonoffbuttonlist[i].Down()
				self.autoonoffbuttonlist[i].Disable()
			player.AutoSkillOnOff(0)
			player.AutoPositionOnOff(0)
		else:
			for i in range(4, 7):
				self.autoonoffbuttonlist[i].Enable()
				self.autoonoffbuttonlist[i].SetUp()

		ui.ScriptWindow.Show(self)

	def _GetUserDataPath(self):
		name = str(chr.GetName())
		if name == "0":
			return None
		return "UserData/auto_hunting/" + name

	def ReadAutoInfo(self):
		filePath = self._GetUserDataPath()
		if not filePath:
			return

		import os
		if not os.path.exists(filePath):
			return

		lines = open(filePath, "r").readlines()

		for slotindex in range(player.AUTO_POSITINO_SLOT_MAX):
			idx = slotindex * 2
			if idx + 1 >= len(lines):
				break
			try:
				slotID = int(lines[idx].strip())
				slotCD = int(lines[idx + 1].strip())
			except ValueError:
				continue
			if slotID != 0:
				if slotindex < player.AUTO_SKILL_SLOT_MAX:
					player.SetAutoSkillSlotIndex(slotindex, slotID)
				else:
					player.SetAutoPositionSlotIndex(slotindex, slotID)
			player.SetAutoSlotCoolTime(slotindex, slotCD)

		lineIndex = player.AUTO_POSITINO_SLOT_MAX * 2
		while lineIndex < len(lines):
			line = lines[lineIndex].strip()
			if line == "[OPTION]":
				lineIndex += 1
				if lineIndex < len(lines) and self.autoAttackOptionWindow:
					self.autoAttackOptionWindow.SaveFileLoad(lines[lineIndex].strip())
				lineIndex += 1
			elif line == "[RANGE]":
				lineIndex += 1
				if lineIndex < len(lines) and self.autoHuntingRangeWindow:
					self.autoHuntingRangeWindow.LoadSaveData(lines[lineIndex].strip())
				lineIndex += 1
			else:
				lineIndex += 1

		self.isFirstReadFile = True
		self.RefreshAutoPositionSlot()
		self.RefreshAutoSkillSlot()

	def _ValidateSlotCooltime(self, slotindex, editIndex, checkFunc):
		cooltime = self.CheckCooltimeText(self.timeeditlist[editIndex].GetText())
		cooltime = checkFunc(slotindex, self.autoslotindex[slotindex], int(cooltime))
		if cooltime != 0:
			player.SetAutoSlotCoolTime(slotindex, int(cooltime))
			self.timeeditlist[editIndex].SetText(str(cooltime))

	def SlotKontrol(self):
		for i in range(player.AUTO_SKILL_SLOT_MAX):
			if self.autoslotindex[i] == 0:
				self.timeeditlist[i].SetText("")
			self._ValidateSlotCooltime(i, i, player.CheckSkillSlotCoolTime)
		for i in range(player.AUTO_POSITINO_SLOT_START + 1, player.AUTO_POSITINO_SLOT_MAX):
			self._ValidateSlotCooltime(i, i - 1, player.CheckSkillSlotCoolTime)

	def SaveAutoInfo(self):
		filePath = self._GetUserDataPath()
		if not filePath:
			return

		self.SlotKontrol()

		import os
		if not os.path.exists('UserData/auto_hunting/'):
			os.makedirs('UserData/auto_hunting/')

		if self.autoAttackOptionWindow:
			self.autoAttackOptionWindow.ApplyFilters()

		f = old_open(filePath, 'w')
		for slotindex in range(player.AUTO_POSITINO_SLOT_MAX):
			iPos = player.GetAutoSlotIndex(slotindex)
			if iPos != 0:
				f.write(str(iPos) + '\n')
				dSure = player.GetAutoSlotCoolTime(slotindex)
				f.write(str(dSure) + '\n' if dSure != 0 else '0\n')
			else:
				f.write('0\n0\n')
		if self.autoAttackOptionWindow:
			f.write('[OPTION]\n')
			f.write(self.autoAttackOptionWindow.GetSaveLineStr() + '\n')
		if self.autoHuntingRangeWindow:
			f.write('[RANGE]\n')
			f.write(self.autoHuntingRangeWindow.GetSaveLineStr() + '\n')
		f.close()

	def Close(self):
		self.Hide()
		self.isOpen = 0
		self.EditLineKillFocus()
		if self.autoAttackOptionWindow:
			self.autoAttackOptionWindow.Close()
		if self.autoHuntingRangeWindow:
			self.autoHuntingRangeWindow.Close()

	def EditLineKillFocus(self):
		for x in range(self.AUTO_COOLTIME_MAX):
			self.timeeditlist[x].KillFocus()

	def ToggleSubWindow(self, showWnd, hideWnd):
		if not showWnd:
			return
		if showWnd.IsShow():
			showWnd.Close()
		else:
			x, y = self.GetGlobalPosition()
			showWnd.AdjustWindowPosition(x, y)
			showWnd.Show()
			showWnd.SetTop()
			if hideWnd:
				hideWnd.Close()

	def ToggleAutoAttackOptionWindow(self):
		self.ToggleSubWindow(self.autoAttackOptionWindow, self.autoHuntingRangeWindow)

	def ToggleAutoHuntingRangeWindow(self):
		if self.autostartonoff:
			return

		self.ToggleSubWindow(self.autoHuntingRangeWindow, self.autoAttackOptionWindow)

	def OnMoveWindow(self, x, y):
		if self.autoAttackOptionWindow and self.autoAttackOptionWindow.IsShow():
			self.autoAttackOptionWindow.AdjustWindowPosition(x, y)
		if self.autoHuntingRangeWindow and self.autoHuntingRangeWindow.IsShow():
			self.autoHuntingRangeWindow.AdjustWindowPosition(x, y)

	def Destroy(self):
		self.isloded = 0
		self.Hide()

		if self.tooltipSkill:
			self.tooltipSkill.HideToolTip()

		if self.autoAttackOptionWindow:
			self.autoAttackOptionWindow.Destroy()
			self.autoAttackOptionWindow = None

		if self.autoHuntingRangeWindow:
			self.autoHuntingRangeWindow.Destroy()
			self.autoHuntingRangeWindow = None

		self.ResetAttributes()

	def OnActivateSkill(self):
		if self.isOpen:
			self.RefreshAutoSkillSlot()

	def OnDeactivateSkill(self, slotindex):
		if self.isOpen:
			for i in range(player.AUTO_SKILL_SLOT_MAX):
				(Position) = player.GetAutoSlotIndex(i)
				if slotindex == Position:
					self.autoslot.DeactivateSlot(i)

	def OnUseSkill(self, slotindex, coolTime):
		if self.isOpen:
			self.RefreshAutoSkillSlot()

	def SetSkillToolTip(self, tooltip):
		self.tooltipSkill = tooltip

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def SetAutoCooltime(self, slotindex, cooltime):
		self.autoslot.SetSlotCoolTime(slotindex, cooltime, 0)

	def SetCloseGame(self):
		self.closegame = True

	def GetAutoStartonoff(self):
		return self.autostartonoff

	def RefreshAutoPositionSlot(self):
		for slotindex in range(player.AUTO_POSITINO_SLOT_START + 1, player.AUTO_POSITINO_SLOT_MAX):
			localSlotIndex = slotindex - player.AUTO_POSITINO_SLOT_START - 1
			Position = player.GetAutoSlotIndex(slotindex)
			if Position == 0:
				self.autoPotionSlot.ClearSlot(localSlotIndex)
				self.timeeditlist[slotindex-1].SetText("")
				self.autoslotindex[slotindex] = 0
				continue

			if app.ENABLE_EXTEND_INVEN_SYSTEM:
				itemIndex = player.GetItemIndex(player.SLOT_TYPE_INVENTORY, Position)
				itemCount = player.GetItemCount(player.SLOT_TYPE_INVENTORY, Position)
			else:
				itemIndex = player.GetItemIndex(Position)
				itemCount = player.GetItemCount(Position)

			if itemCount <= 1:
				itemCount = 0

			self.autoPotionSlot.SetItemSlot(localSlotIndex, itemIndex, itemCount)
			self.autoslotindex[slotindex] = Position

			coolTime = player.GetAutoSlotCoolTime(slotindex)
			if self.timeeditlist[slotindex - 1].GetText() == "":
				self.timeeditlist[slotindex - 1].SetText(str(coolTime))

			if itemIndex == 0:
				self.autoPotionSlot.ClearSlot(localSlotIndex)
				self.timeeditlist[slotindex - 1].SetText("")
				player.SetAutoPositionSlotIndex(slotindex, 0)
				self.RefreshAutoPositionSlot()

		self.autoPotionSlot.RefreshSlot()

	def RefreshAutoSkillSlot(self):
		for slotindex in range(player.AUTO_SKILL_SLOT_MAX):
			Position = player.GetAutoSlotIndex(slotindex)

			if Position == 0:
				self.autoslot.ClearSlot(slotindex)
				self.timeeditlist[slotindex].SetText("")
				self.autoslotindex[slotindex] = 0
				continue

			skillIndex = player.GetSkillIndex(Position)
			if 0 == skillIndex:
				self.autoslot.ClearSlot(slotindex)

			skillType = skill.GetSkillType(skillIndex)
			if skill.SKILL_TYPE_GUILD == skillType:
				skillGrade = 0
				skillLevel = guild.GetSkillLevel(Position)
			else:
				skillGrade = player.GetSkillGrade(Position)
				skillLevel = player.GetSkillLevel(Position)

			self.autoslot.SetSkillSlotNew(slotindex, skillIndex, skillGrade, skillLevel)
			self.autoslot.SetSlotCountNew(slotindex, skillGrade, skillLevel)
			self.autoslot.SetCoverButton(slotindex)

			if player.IsSkillCoolTime(Position):
				(coolTime, elapsedTime) = player.GetSkillCoolTime(Position)
				self.autoslot.SetSlotCoolTime(slotindex, coolTime, elapsedTime)

			if player.IsSkillActive(Position):
				self.autoslot.ActivateSlot(slotindex)

			self.autoslotindex[slotindex] = Position

			coolTime = player.GetAutoSlotCoolTime(slotindex)
			if self.timeeditlist[slotindex].GetText() == "":
				self.timeeditlist[slotindex].SetText(str(coolTime))

		self.autoslot.RefreshSlot()

	def AddAutoSlot(self, slotindex):
		AttachedSlotType = mouseModule.mouseController.GetAttachedType()
		AttachedSlotNumber = mouseModule.mouseController.GetAttachedSlotNumber()
		AttachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()

		if slotindex <= player.AUTO_SKILL_SLOT_MAX:
			if player.SLOT_TYPE_SKILL == AttachedSlotType:
				player.SetAutoSkillSlotIndex(slotindex,AttachedSlotNumber)
				self.RefreshAutoSkillSlot()
			elif player.SLOT_TYPE_AUTO == AttachedSlotType:
				if slotindex == AttachedSlotNumber:
					return
				if AttachedSlotNumber >= player.AUTO_SKILL_SLOT_MAX:
					return
				player.SetAutoSkillSlotIndex(slotindex,AttachedItemIndex)
				self.RefreshAutoSkillSlot()
		else:
			if player.SLOT_TYPE_INVENTORY == AttachedSlotType:
				itemIndex = player.GetItemIndex(AttachedSlotNumber)
				item.SelectItem(itemIndex)
				ItemType = item.GetItemType()
				ItemSubType	= item.GetItemSubType()
				itemRemaintime = 0

				VALID_USE_SUBTYPES = (
					item.USE_POTION, item.USE_POTION_TOWER, item.USE_ABILITY_UP,
					item.USE_POTION_NODELAY, item.USE_POTION_NODELAY_TOWER,
					item.USE_CALL, item.USE_AFFECT,
				)

				if ItemType == item.ITEM_TYPE_USE:
					if ItemSubType == item.USE_ABILITY_UP:
						itemRemaintime = item.GetValue(1)
					elif ItemSubType == item.USE_AFFECT:
						itemRemaintime = item.GetValue(3)

					if ItemSubType in VALID_USE_SUBTYPES and itemRemaintime < 9999:
						player.SetAutoPositionSlotIndex(slotindex, AttachedSlotNumber)
						self.RefreshAutoPositionSlot()

				elif ItemType == item.ITEM_TYPE_BLEND:
					player.SetAutoPositionSlotIndex(slotindex, AttachedSlotNumber)
					self.RefreshAutoPositionSlot()

			elif player.SLOT_TYPE_AUTO == AttachedSlotType:
				if slotindex == AttachedSlotNumber:
					return
				if AttachedSlotNumber <= player.AUTO_SKILL_SLOT_MAX:
					return
				player.SetAutoPositionSlotIndex(slotindex,AttachedItemIndex)
				self.RefreshAutoPositionSlot()

		mouseModule.mouseController.DeattachObject()

	def SelectActiveSkillEmptySlot(self, slotindex):
		if self.autostartonoff:
			return

		if mouseModule.mouseController.isAttached():
			self.AddAutoSlot(slotindex)

	def SelectActiveSkillSlot(self,slotindex):
		mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_AUTO, slotindex, self.autoslotindex[slotindex])

	def OverActiveSkillSlot(self,slotindex):
		if mouseModule.mouseController.isAttached():
			return

		Position = player.GetAutoSlotIndex(slotindex)
		if Position == 0:
			return
		skillIndex = player.GetSkillIndex(Position)
		skillType = skill.GetSkillType(skillIndex)
		if skill.SKILL_TYPE_GUILD == skillType:
			skillGrade = 0
			skillLevel = guild.GetSkillLevel(Position)
		else:
			skillGrade = player.GetSkillGrade(Position)
			skillLevel = player.GetSkillLevel(Position)
		self.tooltipSkill.SetSkillNew(Position, skillIndex, skillGrade, skillLevel)

	def OverSkillSlotOutItem(self):
		if self.tooltipSkill:
			self.tooltipSkill.HideToolTip()
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def _GetPotionBackendIndex(self, localSlotIndex):
		return localSlotIndex + player.AUTO_POSITINO_SLOT_START + 1

	def SelectActivePotionEmptySlot(self, localSlotIndex):
		if self.autostartonoff:
			return
		if mouseModule.mouseController.isAttached():
			self.AddAutoSlot(self._GetPotionBackendIndex(localSlotIndex))

	def SelectActivePotionSlot(self, localSlotIndex):
		backendSlotIndex = self._GetPotionBackendIndex(localSlotIndex)
		mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_AUTO, backendSlotIndex, self.autoslotindex.get(backendSlotIndex, 0))

	def OverActivePotionSlot(self, localSlotIndex):
		if mouseModule.mouseController.isAttached():
			return
		Position = player.GetAutoSlotIndex(self._GetPotionBackendIndex(localSlotIndex))
		if Position == 0:
			return
		if app.ENABLE_EXTEND_INVEN_SYSTEM:
			self.tooltipItem.SetInventoryItem(Position, player.SLOT_TYPE_INVENTORY)
		else:
			self.tooltipItem.SetInventoryItem(Position)
		self.tooltipSkill.HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True

class AutoAttackOptionWindow(ui.ScriptWindow):
	CHECK_BOX_BASE_POSITION_X = 16
	CHECK_BOX_BASE_POSITION_Y = 16
	CHECK_BOX_INTERVAL_Y = 16
	SAVE_FILE_INDEX_CHECKBOX_MAX = 7
	SAVE_FILE_INDEX_LEVEL_MAX = 8
	SAVE_FILE_INDEX_LEVEL_MIN = 7

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__checkbox_back_img_list = []
		self.__checkbox_text_list = []
		self.__checkbox_list = []
		self.__auto_attack_level_min = None
		self.__auto_attack_level_max = None
		self.__auto_window = None
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.Close()
		self.__checkbox_back_img_list = []
		self.__checkbox_text_list = []
		self.__checkbox_list = []
		self.__auto_attack_level_min = None
		self.__auto_attack_level_max = None
		self.__auto_window = None

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/autoattackoptionwindow.py")

			checkbox_text_list = [
				localeInfo.AUTO_HUNTING_OPTION_PAWN,
				localeInfo.AUTO_HUNTING_OPTION_S_PAWN,
				localeInfo.AUTO_HUNTING_OPTION_KNIGHT,
				localeInfo.AUTO_HUNTING_OPTION_S_KNIGHT,
				localeInfo.AUTO_HUNTING_OPTION_KING,
				localeInfo.AUTO_HUNTING_OPTION_BOSS,
				localeInfo.AUTO_HUNTING_OPTION_STONE,
			]

			CHECK_IMG = "d:/ymir work/ui/game/auto_hunting/auto_attack_check_back_img.sub"
			CHECK_BOX_IMG = "d:/ymir work/ui/game/auto_hunting/auto_attack_check_box.sub"
			board = self.GetChild("board")

			for i, label in enumerate(checkbox_text_list):
				backImg = ui.ImageBox()
				backImg.SetParent(board)
				backImg.LoadImage(CHECK_IMG)
				backImg.SetPosition(self.CHECK_BOX_BASE_POSITION_X, self.CHECK_BOX_BASE_POSITION_Y + i * self.CHECK_BOX_INTERVAL_Y)
				backImg.SetEvent(ui.__mem_func__(self.OnClickCheckBoxBackImage), "mouse_click", i)
				backImg.Show()
				self.__checkbox_back_img_list.append(backImg)

				textLine = ui.TextLine()
				textLine.SetParent(backImg)
				textLine.SetPosition(16, 0)
				textLine.SetText(label)
				textLine.Show()
				self.__checkbox_text_list.append(textLine)

				checkBox = ui.ImageBox()
				checkBox.SetParent(backImg)
				checkBox.LoadImage(CHECK_BOX_IMG)
				checkBox.SetPosition(2, 2)
				checkBox.SetEvent(ui.__mem_func__(self.OnClickCheckBoxBackImage), "mouse_click", i)
				checkBox.Show()
				self.__checkbox_list.append(checkBox)

			self.__auto_attack_level_min = self.GetChild("auto_attack_level_min")
			self.__auto_attack_level_max = self.GetChild("auto_attack_level_max")

			if self.__auto_attack_level_min:
				self.__auto_attack_level_min.SetText("15")
			if self.__auto_attack_level_max:
				self.__auto_attack_level_max.SetText("15")

			clearButton = self.GetChild("ClearButton")
			clearButton.SetEvent(ui.__mem_func__(self.OnClickClearButton))

			acceptButton = self.GetChild("AcceptButton")
			acceptButton.SetEvent(ui.__mem_func__(self.__Accept))

			self.__ApplyToPlayer()

		except:
			import exception
			exception.Abort("AutoAttackOptionWindow.__LoadWindow")

	def BindAutoHuntingWindow(self, auto_window):
		import weakref
		self.__auto_window = weakref.proxy(auto_window)

	def OnClickCheckBoxBackImage(self, event_type, index):
		if index < 0 or index >= len(self.__checkbox_list):
			return
		checkbox = self.__checkbox_list[index]
		if checkbox.IsShow():
			checkbox.Hide()
		else:
			checkbox.Show()

	def OnClickClearButton(self):
		for checkbox in self.__checkbox_list:
			checkbox.Show()
		if self.__auto_attack_level_min:
			self.__auto_attack_level_min.SetText("15")
		if self.__auto_attack_level_max:
			self.__auto_attack_level_max.SetText("15")
		self.__ApplyToPlayer()

	def __SafeInt(self, text):
		try:
			if not text:
				return 0
			return int(text)
		except ValueError:
			return 0

	def __ApplyToPlayer(self):
		flags = 0
		for i, cb in enumerate(self.__checkbox_list):
			if cb.IsShow():
				flags |= (1 << i)
		player.SetAutoAttackMonsterFlags(flags)

		lmin = self.__SafeInt(self.__auto_attack_level_min.GetText()) if self.__auto_attack_level_min else 0
		lmax = self.__SafeInt(self.__auto_attack_level_max.GetText()) if self.__auto_attack_level_max else 0
		player.SetAutoAttackLevelRange(lmin, lmax)

	def ApplyFilters(self):
		self.__ApplyToPlayer()

	def __Accept(self):
		self.__ApplyToPlayer()
		self.Hide()

	def Show(self):
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()

	def AdjustWindowPosition(self, x, y):
		self.SetPosition(x + 254, y + 300)

	def GetSaveLineStr(self):
		parts = ["1" if cb.IsShow() else "0" for cb in self.__checkbox_list]
		parts.append(self.__auto_attack_level_min.GetText() if self.__auto_attack_level_min else "")
		parts.append(self.__auto_attack_level_max.GetText() if self.__auto_attack_level_max else "")
		return "\t".join(parts)

	def SaveFileLoad(self, save_data):
		if not save_data:
			return
		tokens = save_data.split("\t")
		for i in range(min(len(tokens), len(self.__checkbox_list))):
			if tokens[i] == "1":
				self.__checkbox_list[i].Show()
			else:
				self.__checkbox_list[i].Hide()

		if self.__auto_attack_level_min and len(tokens) > self.SAVE_FILE_INDEX_LEVEL_MIN:
			self.__auto_attack_level_min.SetText(tokens[self.SAVE_FILE_INDEX_LEVEL_MIN])
		if self.__auto_attack_level_max and len(tokens) > self.SAVE_FILE_INDEX_LEVEL_MAX:
			self.__auto_attack_level_max.SetText(tokens[self.SAVE_FILE_INDEX_LEVEL_MAX])

		self.__ApplyToPlayer()

class AutoHuntingRangeWindow(ui.ScriptWindow):
	AUTO_HUNTING_MIN_RANGE = 2000
	AUTO_HUNTING_DEFAULT_RANGE = 4000
	AUTO_HUNTING_MAX_RANGE = 8000
	UNITS_PER_METER = 100

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__slider_bar = None
		self.__range_text = None
		self.__auto_window = None
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.Close()
		self.__slider_bar = None
		self.__range_text = None
		self.__auto_window = None

	def __FormatMeters(self, rangeValue):
		return "%dM" % (rangeValue // self.UNITS_PER_METER)

	def __ClampRange(self, value):
		return max(self.AUTO_HUNTING_MIN_RANGE, min(self.AUTO_HUNTING_MAX_RANGE, value))

	def __SliderPosFromRange(self, rangeValue):
		span = self.AUTO_HUNTING_MAX_RANGE - self.AUTO_HUNTING_MIN_RANGE
		if span <= 0:
			return 0.0
		return float(rangeValue - self.AUTO_HUNTING_MIN_RANGE) / float(span)

	def __RangeFromSliderPos(self, pos):
		return int(self.AUTO_HUNTING_MIN_RANGE + pos * (self.AUTO_HUNTING_MAX_RANGE - self.AUTO_HUNTING_MIN_RANGE))

	def _UpdateRangeUI(self, rangeValue):
		if self.__slider_bar:
			self.__slider_bar.SetSliderPos(self.__SliderPosFromRange(rangeValue))
		if self.__range_text:
			self.__range_text.SetText(self.__FormatMeters(rangeValue))

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/autohuntingrangewindow.py")

			self.__slider_bar = self.GetChild("hunting_range_sliderbar")
			self.__slider_bar.SetEvent(ui.__mem_func__(self.__OnMoveSliderBar))

			self.__range_text = self.GetChild("range_text")

			self.GetChild("AcceptButton").SetEvent(ui.__mem_func__(self.__Accept))

			currentRange = player.GetAutoHuntingRange()
			if currentRange <= 0:
				currentRange = self.AUTO_HUNTING_DEFAULT_RANGE
				player.SetAutoHuntingRange(currentRange)
			self._UpdateRangeUI(self.__ClampRange(currentRange))

		except:
			import exception
			exception.Abort("AutoHuntingRangeWindow.__LoadWindow")

	def BindAutoHuntingWindow(self, auto_window):
		import weakref
		self.__auto_window = weakref.proxy(auto_window)

	def __OnMoveSliderBar(self):
		rangeValue = self.__ClampRange(self.__RangeFromSliderPos(self.__slider_bar.GetSliderPos()))
		self.__range_text.SetText(self.__FormatMeters(rangeValue))
		player.SetAutoHuntingRange(rangeValue)
		player.SetAutoHuntRangeEffect(float(rangeValue))

	def __Accept(self):
		pos = self.__slider_bar.GetSliderPos() if self.__slider_bar else 0.5
		rangeValue = self.__ClampRange(self.__RangeFromSliderPos(pos))
		player.SetAutoHuntingRange(rangeValue)
		player.SetAutoHuntRangeEffect(0.0)
		self.Hide()

	def Show(self):
		currentRange = self.__ClampRange(player.GetAutoHuntingRange() or self.AUTO_HUNTING_DEFAULT_RANGE)
		self._UpdateRangeUI(currentRange)
		player.SetAutoHuntingRange(currentRange)
		player.SetAutoHuntRangeEffect(float(currentRange))
		ui.ScriptWindow.Show(self)

	def Close(self):
		player.SetAutoHuntRangeEffect(0.0)
		self.Hide()

	def ClearRangeInfo(self):
		self._UpdateRangeUI(self.AUTO_HUNTING_DEFAULT_RANGE)
		player.SetAutoHuntingRange(self.AUTO_HUNTING_DEFAULT_RANGE)

	def AdjustWindowPosition(self, x, y):
		self.SetPosition(x + 254, y + 380)

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def GetSaveLineStr(self):
		rangeValue = player.GetAutoHuntingRange()
		if not rangeValue:
			rangeValue = self.AUTO_HUNTING_DEFAULT_RANGE
		return str(self.__ClampRange(rangeValue))

	def LoadSaveData(self, save_data):
		if not save_data:
			return
		try:
			rangeValue = self.__ClampRange(int(save_data))
			self._UpdateRangeUI(rangeValue)
			player.SetAutoHuntingRange(rangeValue)
		except:
			pass
