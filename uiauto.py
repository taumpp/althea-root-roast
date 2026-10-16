import ui
import app
import uiScriptLocale
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

class AutoWindow(ui.ScriptWindow):
	AUTO_COOLTIME_POS_Y = 4
	AUTO_COOLTIME_POS_X = 6
	AUTO_COOLTIME_MAX = AUTO_COOLTIME_POS_Y * AUTO_COOLTIME_POS_X

	AUTO_TOOLTIP_CLEAR_HEIGHT = 12
	AUTO_TOOLTIP_CLEAR_WIDTH = 66

	ITEM_REMAIN_TIME_MAX = 9999

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.is_loaded = False
		self.is_read = False

		self.tooltip_skill = 0
		self.tooltip_item = 0

		self.auto_start_is_onoff = 0

		# Slots
		self.auto_slot = None
		self.auto_slot_index = {}
		for i in range(player.AUTO_SKILL_SLOT_MAX):
			self.auto_slot_index[i] = 0
		for i in range(player.AUTO_POTION_SLOT_START, player.AUTO_POTION_SLOT_MAX):
			self.auto_slot_index[i] = player.ITEM_SLOT_COUNT
		self.time_edit_list = {}
		self.auto_onoff_button_list = []

		# Buttons
		self.auto_skill_clear_button = None
		self.auto_potion_clear_button = None
		self.auto_all_clear_button = None

		self.auto_tooltip_button = None
		self.auto_tooltip = None
		self.auto_system_tooltip_list = [
			localeInfo.AUTO_TOOLTIP_LINE1,
			localeInfo.AUTO_TOOLTIP_LINE2,
			localeInfo.AUTO_TOOLTIP_LINE3,
			localeInfo.AUTO_TOOLTIP_LINE4,
			localeInfo.AUTO_TOOLTIP_LINE5
		]
		self.auto_tooltip_clear = None

		self.is_read = False
		self.LoadAutoWindow()
		if app.ENABLE_ANIMATED_WINDOW:
			self.AddFlag("animate")

	def __del__(self):
		ui.ScriptWindow.__del__(self)

		self.is_loaded = False
		self.is_read = False

		self.tooltip_skill = 0
		self.tooltip_item = 0

		self.auto_start_is_onoff = 0

		# Slots
		self.auto_slot = None
		self.auto_slot_index = {}
		self.time_edit_list = {}
		self.auto_onoff_button_list = []

		# Buttons
		self.auto_skill_clear_button = None
		self.auto_potion_clear_button = None
		self.auto_all_clear_button = None

		self.auto_tooltip_button = None
		self.auto_tooltip = None
		self.auto_tooltip_clear = None

		self.is_read = False

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/AutoWindow.py")
			self.GetChild("board").SetCloseEvent(ui.__mem_func__(self.Close))

			auto_save_button = self.GetChild("AutoSaveOnButton")
			auto_save_button.SetEvent(ui.__mem_func__(self.__AutoSave))

			auto_on_button = self.GetChild("AutoStartOnButton")
			auto_on_button.SetEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_START, True)
			self.auto_onoff_button_list.append(auto_on_button)

			auto_off_button = self.GetChild("AutoStartOffButton")
			auto_off_button.SetEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_START, False)
			self.auto_onoff_button_list.append(auto_off_button)

			auto_attack_button = self.GetChild("AutoAttackButton")
			auto_attack_button.SetToggleDownEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_ATTACK, True)
			auto_attack_button.SetToggleUpEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_ATTACK, False)
			self.auto_onoff_button_list.append(auto_attack_button)

			auto_range_button = self.GetChild("AutoRangeButton")
			auto_range_button.SetToggleDownEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_RANGE, True)
			auto_range_button.SetToggleUpEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_RANGE, False)
			self.auto_onoff_button_list.append(auto_range_button)

			auto_potion_button = self.GetChild("AutoPotionButton")
			auto_potion_button.SetToggleDownEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_POTION, True)
			auto_potion_button.SetToggleUpEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_POTION, False)
			self.auto_onoff_button_list.append(auto_potion_button)

			auto_skill_button = self.GetChild("AutoSkillButton")
			auto_skill_button.SetToggleDownEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_SKILL, True)
			auto_skill_button.SetToggleUpEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_SKILL, False)
			self.auto_onoff_button_list.append(auto_skill_button)

			auto_restart_button = self.GetChild("AutoRestartHereButton")
			auto_restart_button.SetToggleDownEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_RESTART, True)
			auto_restart_button.SetToggleUpEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_RESTART, False)
			self.auto_onoff_button_list.append(auto_restart_button)

			auto_atk_button_button = self.GetChild("AutoAttackStoneButton")
			auto_atk_button_button.SetToggleDownEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_ATTACK_STONE, True)
			auto_atk_button_button.SetToggleUpEvent(ui.__mem_func__(self.__OnClickAutoOnOffButton), chrmgr.AUTO_ONOFF_ATTACK_STONE, False)
			self.auto_onoff_button_list.append(auto_atk_button_button)

			self.auto_tooltip_clear = uiToolTip.ToolTip()
			self.auto_tooltip_clear.ClearToolTip()
			self.auto_tooltip_clear.SetThinBoardSize(11 * len(localeInfo.AUTO_TOOLTIP_CLEAR))
			self.auto_tooltip_clear.SetTitle(localeInfo.AUTO_TOOLTIP_CLEAR)
			self.auto_tooltip_clear.Hide()

			self.auto_skill_clear_button = self.GetChild("AutoSkillClearButton")
			self.auto_skill_clear_button.SetEvent(ui.__mem_func__(self.__AutoSkillClear))
			self.auto_skill_clear_button.OnMouseOverIn = lambda arg = True : ui.__mem_func__(self.auto_tooltip_clear.Show)()
			self.auto_skill_clear_button.OnMouseOverOut = lambda arg = False : ui.__mem_func__(self.auto_tooltip_clear.Hide)()

			self.auto_potion_clear_button = self.GetChild("AutoPotionClearButton")
			self.auto_potion_clear_button.SetEvent(ui.__mem_func__(self.__AutoPotionClear))
			self.auto_potion_clear_button.OnMouseOverIn = lambda arg = True : ui.__mem_func__(self.auto_tooltip_clear.Show)()
			self.auto_potion_clear_button.OnMouseOverOut = lambda arg = False : ui.__mem_func__(self.auto_tooltip_clear.Hide)()

			self.auto_all_clear_button = self.GetChild("AutoAllClearButton")
			self.auto_all_clear_button.SetEvent(ui.__mem_func__(self.__AutoAllClear))
			self.auto_all_clear_button.OnMouseOverIn = lambda arg = True : ui.__mem_func__(self.auto_tooltip_clear.Show)()
			self.auto_all_clear_button.OnMouseOverOut = lambda arg = False : ui.__mem_func__(self.auto_tooltip_clear.Hide)()

			for x in range(self.AUTO_COOLTIME_MAX):
				childname = "editline" + str(x)
				self.time_edit_list[x] = self.GetChild(childname)
				self.time_edit_list[x].SetEscapeEvent(ui.__mem_func__(self.Close))

			self.auto_slot = self.GetChild("Auto_Active_Skill_Slot_Table")
			self.auto_slot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			self.auto_slot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__SelectActiveSkillEmptySlot))
			self.auto_slot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectActiveSkillSlot))
			self.auto_slot.SetOverInItemEvent(ui.__mem_func__(self.__OverActiveSkillSlot))
			self.auto_slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverSkillSlotOutItem))
			self.auto_slot.Show()

			self.auto_tooltip_button = self.GetChild("AutoToolTipButton")
			self.auto_tooltip = self.__CreateGameTypeToolTip(localeInfo.AUTO_TOOLTIP_TITLE, self.auto_system_tooltip_list)
			self.auto_tooltip.SetTop()
			self.auto_tooltip_button.SetToolTipWindow(self.auto_tooltip)
		except:
			import exception
			exception.Abort("AutoWindow.__LoadWindow.UIScript/AutoWindow.py")

	def __CreateGameTypeToolTip(self, title, desc_list):
		toolTip = uiToolTip.ToolTip()
		toolTip.SetTitle(title)
		toolTip.AppendSpace(5)

		for desc in desc_list:
			toolTip.AutoAppendTextLine(desc)

		toolTip.AlignHorizonalCenter()
		toolTip.SetTop()
		return toolTip

	def __AutoSkillClear(self):
		if self.GetAutoStartonoff() == False:
			player.ClearAutoSkillSlot()
			self.RefreshAutoSkillSlot()
			for i in range(player.AUTO_SKILL_SLOT_MAX):
				self.auto_slot_index[i] = 0

	def __AutoPotionClear(self):
		if self.GetAutoStartonoff() == False:
			player.ClearAutoPotionSlot()
			self.RefreshAutoPotionSlot()
			for i in range(player.AUTO_POTION_SLOT_START, player.AUTO_POTION_SLOT_MAX):
				self.auto_slot_index[i] = player.ITEM_SLOT_COUNT

	def __AutoAllClear(self):
		if self.GetAutoStartonoff() == False:
			for i in range(chrmgr.AUTO_ONOFF_ATTACK, chrmgr.AUTO_ONOFF_MAX):
				self.__OnClickAutoOnOffButton(i, False)

			if not item.CheckAffect(chr.NEW_AFFECT_AUTO_HUNT, 0):
				for i in range(1, 8):
					self.auto_onoff_button_list[i].Down()
					self.auto_onoff_button_list[i].Disable()

	def __IsNumberic(self, text):
		try:
			int(text)
			return True
		except ValueError:
			return False

	def __CheckCoolTimeText(self, cool_time):
		if cool_time == "":
			return 0

		if not self.__IsNumberic(cool_time):
			return 0

		return cool_time

	def __OnClickAutoOnOffButton(self, type, onoff, command = False):
		if not self.is_loaded:
			return

		if type == chrmgr.AUTO_ONOFF_START:
			if not item.CheckAffect(chr.NEW_AFFECT_AUTO_HUNT, 0):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AUTO_NEED_ITEM)
				return

			if onoff == True:
				for i in range(player.AUTO_SKILL_SLOT_MAX):
					cool_time = self.time_edit_list[i].GetText()
					cool_time = self.__CheckCoolTimeText(cool_time)
					cool_time = player.CheckSkillSlotCoolTime(i, self.auto_slot_index[i], int(cool_time))
					if self.auto_slot_index[i] == 0:
						self.time_edit_list[i].SetText("")
					if not cool_time == 0:
						player.SetAutoSlotCoolTime(i, int(cool_time))
						self.time_edit_list[i].SetText(str(cool_time))

				for i in range(player.AUTO_POTION_SLOT_START, player.AUTO_POTION_SLOT_MAX):
					cool_time = self.time_edit_list[i - 1].GetText()
					cool_time = self.__CheckCoolTimeText(cool_time)
					cool_time = player.CheckPotionSlotCoolTime(i, self.auto_slot_index[i], int(cool_time))
					if not cool_time == 0:
						player.SetAutoSlotCoolTime(i, int(cool_time))
						self.time_edit_list[i - 1].SetText(str(cool_time))
			else:
				for i in range(player.AUTO_POTION_SLOT_START, player.AUTO_POTION_SLOT_MAX):
					self.SetAutoCooltime(i, 0)

			self.auto_start_is_onoff = onoff
		else:
			chrmgr.SetAutoSystemByType(type, onoff)

		cmd_packet = str(int(self.auto_start_is_onoff == True))
		for i in range(chrmgr.AUTO_ONOFF_ATTACK, chrmgr.AUTO_ONOFF_MAX):
			cmd_packet += " " + str(chrmgr.GetAutoSystemByType(i))
		net.SendChatPacket("/auto_onoff " + cmd_packet)

		if command == True:
			if chrmgr.GetAutoOnOff() == False:
				self.Close()
				return

		if type == chrmgr.AUTO_ONOFF_START:
			if onoff == True:
				self.auto_onoff_button_list[type].Down()
				self.auto_onoff_button_list[type].Disable()

				self.auto_onoff_button_list[type + 1].SetUp()
				self.auto_onoff_button_list[type + 1].Enable()
			else:
				self.auto_onoff_button_list[type].SetUp()
				self.auto_onoff_button_list[type].Enable()

				self.auto_onoff_button_list[type + 1].Down()
				self.auto_onoff_button_list[type + 1].Disable()
		else:
			if onoff != True:
				self.auto_onoff_button_list[type + 1].SetText(uiScriptLocale.AUTO_OFF)
				self.auto_onoff_button_list[type + 1].SetUp()
			else:
				self.auto_onoff_button_list[type + 1].SetText(uiScriptLocale.AUTO_ON)
				self.auto_onoff_button_list[type + 1].Down()

	def LoadAutoWindow(self):
		if self.is_loaded == 0:
			self.is_loaded = 1
			self.__LoadWindow()
			self.SetCenterPosition()

			import os
			import errno
			directory = 'UserData/auto/'
			try:
				os.makedirs(directory, mode=0o755)
			except OSError as e:
				if e.errno != errno.EEXIST:
					pass

			self.__ReadAutoInfo()

			if self.auto_onoff_button_list:
				self.auto_onoff_button_list[chrmgr.AUTO_ONOFF_START + 1].Down()
				self.auto_onoff_button_list[chrmgr.AUTO_ONOFF_START + 1].Disable()

	def Show(self):
		if self.is_loaded == 0:
			self.is_loaded = 1
			self.__LoadWindow()
			self.SetCenterPosition()

		self.SetTop()
		self.__ReadAutoInfo()
		self.RefreshAutoPotionSlot()
		self.RefreshAutoSkillSlot()

		if not item.CheckAffect(chr.NEW_AFFECT_AUTO_HUNT, 0):
			for i in range(1, 8):
				self.auto_onoff_button_list[i].Down()
				self.auto_onoff_button_list[i].Disable()

		ui.ScriptWindow.Show(self)

	def __ReadAutoInfo(self):
		if (str)(chr.GetName()) == "0":
			return

		player.ClearAutoAllSlot()

		try:
			handle = app.OpenTextFile('UserData/auto/' + chr.GetName())
			count = app.GetTextFileLineCount(handle)
			count = count // 2
			index = 0

			if count > 0:
				for slot_index in range(count):
					slot_line = app.GetTextFileLine(handle, index)

					if slot_index < player.AUTO_SKILL_SLOT_MAX:
						player.SetAutoSkillSlotIndex(slot_index, int(slot_line))
					else:
						player.SetAutoPotionSlotIndex(slot_index + 1, int(slot_line))

					line = app.GetTextFileLine(handle, index + 1)
					if not line == "":
						if slot_index < player.AUTO_SKILL_SLOT_MAX:
							cooltime = player.CheckSkillSlotCoolTime(slot_index, int(slot_line), int(line))
							player.SetAutoSlotCoolTime(slot_index, int(cooltime))
							self.time_edit_list[slot_index].SetText(str(cooltime))
						else:
							cooltime = player.CheckPotionSlotCoolTime(slot_index + 1, int(slot_line), int(line))
							player.SetAutoSlotCoolTime(slot_index + 1, int(cooltime))
							self.time_edit_list[slot_index].SetText(str(cooltime))

					index += 2

			app.CloseTextFile(handle)
			self.is_read = True
		except:
			self.is_read = False

		self.RefreshAutoPotionSlot()
		self.RefreshAutoSkillSlot()

	def __SaveAutoInfo(self):
		if self.auto_start_is_onoff:
			return

		if (str)(chr.GetName()) == "0":
			return

		import os
		if os.path.exists('UserData/auto/') is False:
			os.makedirs('UserData/auto')

		output_file = open('UserData/auto/' + chr.GetName(), 'w')

		for slot_index in range(player.AUTO_SKILL_SLOT_MAX):
			line_str = str(self.auto_slot_index[slot_index]) + '\n'
			output_file.write(line_str)

			if not self.time_edit_list[slot_index].GetText() == "":
				cooltime = player.CheckSkillSlotCoolTime(slot_index, self.auto_slot_index[slot_index], int(self.time_edit_list[slot_index].GetText()))
				line_str = str(cooltime) + '\n'
			else:
				line_str = self.time_edit_list[slot_index].GetText() + '\n'
			output_file.write(line_str)

		for slot_index in range(player.AUTO_POTION_SLOT_START, player.AUTO_POTION_SLOT_MAX):
			line_str = str(self.auto_slot_index[slot_index]) + '\n'
			output_file.write(line_str)

			if not self.time_edit_list[slot_index - 1].GetText() =="":
				cooltime = player.CheckPotionSlotCoolTime(slot_index, self.auto_slot_index[slot_index], int(self.time_edit_list[slot_index - 1].GetText()))
				line_str = str(cooltime) + '\n'
			else:
				line_str = self.time_edit_list[slot_index - 1].GetText() + '\n'
			output_file.write(line_str)

		output_file.close()

	def __AutoSave(self):
		self.__SaveAutoInfo()

	def Close(self):
		self.Hide()
		self.__SaveAutoInfo()
		self.__EditLineKillFocus()

	def __EditLineKillFocus(self):
		for x in range(self.AUTO_COOLTIME_MAX):
			self.time_edit_list[x].KillFocus()

	def Destroy(self):
		self.is_loaded = 0
		self.Hide()
		if 0 != self.tooltip_skill:
			self.tooltip_skill.HideToolTip()

	def OnActivateSkill(self):
		self.RefreshAutoSkillSlot()

	def OnDeactivateSkill(self, slot_index):
		for i in range(player.AUTO_SKILL_SLOT_MAX):
			position = player.GetAutoSlotIndex(slot_index)
			if slot_index == position:
				self.auto_slot.DeactivateSlot(i)

	def OnUseSkill(self):
		self.RefreshAutoSkillSlot()

	def SetSkillToolTip(self, tooltip_skill):
		self.tooltip_skill = tooltip_skill

	def SetItemToolTip(self, tooltip_item):
		self.tooltip_item = tooltip_item

	def SetAutoCooltime(self, slot_index, cool_time):
		self.auto_slot.SetSlotCoolTime(slot_index, cool_time, 0)

	def OnGameOver(self):
		if not item.CheckAffect(chr.NEW_AFFECT_AUTO_USE, 0):
			self.__OnClickAutoOnOffButton(chrmgr.AUTO_ONOFF_ATTACK, False)

	def GetAutoStartonoff(self):
		return self.auto_start_is_onoff

	def RefreshAutoPotionSlot(self):
		if not self.auto_slot:
			return

		for slot_index in range(player.AUTO_POTION_SLOT_START, player.AUTO_POTION_SLOT_MAX):
			position = player.GetAutoSlotIndex(slot_index)
			if position == player.ITEM_SLOT_COUNT:
				self.auto_slot.ClearSlot(slot_index)
				self.time_edit_list[slot_index - 1].SetText("")
				self.auto_slot_index[slot_index] = player.ITEM_SLOT_COUNT
				continue

			item_index = player.GetItemIndex(position)
			item_count = player.GetItemCount(position)

			if item_count <= 1:
				item_count = 0

			self.auto_slot.SetItemSlot(slot_index, item_index, item_count)
			self.auto_slot_index[slot_index] = position

			cool_time = player.GetAutoSlotCoolTime(slot_index)
			if self.time_edit_list[slot_index - 1].GetText() == "":
				self.time_edit_list[slot_index - 1].SetText(str(cool_time))

			if item_index == 0:
				self.auto_slot.ClearSlot(slot_index)
				self.time_edit_list[slot_index - 1].SetText("")
				player.SetAutoPotionSlotIndex(slot_index, player.ITEM_SLOT_COUNT)
				self.RefreshAutoPotionSlot()

		self.auto_slot.RefreshSlot()

		#if self.is_read:
		#	self.__SaveAutoInfo()
		#else:
		#	self.__ReadAutoInfo()

	def RefreshAutoSkillSlot(self):
		for slot_index in range(player.AUTO_SKILL_SLOT_MAX):
			position = player.GetAutoSlotIndex(slot_index)
			if position == 0:
				self.auto_slot.ClearSlot(slot_index)
				self.time_edit_list[slot_index].SetText("")
				self.auto_slot_index[slot_index] = 0
				continue

			skill_index = player.GetSkillIndex(position)
			if 0 == skill_index:
				self.auto_slot.ClearSlot(slot_index)

			skill_type = skill.GetSkillType(skill_index)
			if skill.SKILL_TYPE_GUILD == skill_type:
				import guild
				skill_grade = 0
				skill_level = guild.GetSkillLevel(position)
			else:
				skill_grade = player.GetSkillGrade(position)
				skill_level = player.GetSkillLevel(position)

			self.auto_slot.SetSkillSlotNew(slot_index, skill_index, skill_grade, skill_level)
			self.auto_slot.SetSlotCountNew(slot_index, skill_grade, skill_level)
			self.auto_slot.SetCoverButton(slot_index)

			if player.IsSkillCoolTime(position):
				(cool_time, elapsed_time) = player.GetSkillCoolTime(position)
				self.auto_slot.SetSlotCoolTime(slot_index, cool_time, elapsed_time)

			if player.IsSkillActive(position):
				self.auto_slot.ActivateSlot(slot_index)

			self.auto_slot_index[slot_index] = position

			cool_time = player.GetAutoSlotCoolTime(slot_index)
			if self.time_edit_list[slot_index].GetText() == "":
				self.time_edit_list[slot_index].SetText(str(cool_time))

		self.auto_slot.RefreshSlot()

	def RefreshSkillCoolTime(self): pass

	def __AddAutoSlot(self, slot_index):
		attached_slot_type = mouseModule.mouseController.GetAttachedType()
		attached_slot_number = mouseModule.mouseController.GetAttachedSlotNumber()
		attached_item_index = mouseModule.mouseController.GetAttachedItemIndex()

		if slot_index < player.AUTO_SKILL_SLOT_MAX:
			if player.SLOT_TYPE_SKILL == attached_slot_type:
				player.SetAutoSkillSlotIndex(slot_index, attached_slot_number)
				self.RefreshAutoSkillSlot()

			elif player.SLOT_TYPE_AUTO == attached_slot_type:
				if slot_index == attached_slot_number:
					return

				if attached_slot_number >= player.AUTO_SKILL_SLOT_MAX:
					return

				player.SetAutoSkillSlotIndex(slot_index, attached_item_index)
				self.RefreshAutoSkillSlot()
		else:
			if player.SLOT_TYPE_INVENTORY == attached_slot_type:
				item_index = player.GetItemIndex(attached_slot_number)
				item.SelectItem(item_index)

				item_type = item.GetItemType()
				item_subtype = item.GetItemSubType()
				item_remain_time = 0

				if not item_type == item.ITEM_TYPE_USE:
					return

				if item_type == item.USE_ABILITY_UP:
					item_remain_time = item.GetValue(1)
				elif item_type == item.USE_AFFECT:
					item_remain_time = item.GetValue(3)

				if item_subtype == item.USE_POTION \
				or item_subtype == item.USE_CALL \
				or item_subtype == item.USE_ABILITY_UP \
				or item_subtype == item.USE_POTION_NODELAY \
				or item_subtype == item.USE_AFFECT:
					if item_remain_time < self.ITEM_REMAIN_TIME_MAX:
						player.SetAutoPotionSlotIndex(slot_index, attached_slot_number)
						self.RefreshAutoPotionSlot()

			elif player.SLOT_TYPE_AUTO == attached_slot_type:
				if slot_index == attached_slot_number:
					return

				if attached_slot_number <= player.AUTO_SKILL_SLOT_MAX:
					return

				player.SetAutoPotionSlotIndex(slot_index, attached_item_index)
				self.RefreshAutoPotionSlot()

		mouseModule.mouseController.DeattachObject()

	def __SelectActiveSkillEmptySlot(self, slot_index):
		if self.auto_start_is_onoff:
			return

		if True == mouseModule.mouseController.isAttached():
			self.__AddAutoSlot(slot_index)

	def __SelectActiveSkillSlot(self, slot_index):
		if False == mouseModule.mouseController.isAttached():
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_AUTO, slot_index, self.auto_slot_index[slot_index])

	def __OverActiveSkillSlot(self, slot_index):
		if mouseModule.mouseController.isAttached():
			return

		if slot_index <= player.AUTO_SKILL_SLOT_MAX:
			position = player.GetAutoSlotIndex(slot_index)
			if position == 0:
				return

			skill_index = player.GetSkillIndex(position)
			skill_type = skill.GetSkillType(skill_index)
			if skill.SKILL_TYPE_GUILD == skill_type:
				import guild
				skill_grade = 0
				skill_level = guild.GetSkillLevel(position)
			else:
				skill_grade = player.GetSkillGrade(position)
				skill_level = player.GetSkillLevel(position)

			self.tooltip_skill.SetSkillNew(position, skill_index, skill_grade, skill_level)
		else:
			position = player.GetAutoSlotIndex(slot_index)
			if position == player.ITEM_SLOT_COUNT:
				return

			self.tooltip_item.SetInventoryItem(position)
			self.tooltip_skill.HideToolTip()

	def __OverSkillSlotOutItem(self):
		if 0 != self.tooltip_skill:
			self.tooltip_skill.HideToolTip()

		if 0 != self.tooltip_item:
			self.tooltip_item.HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True
