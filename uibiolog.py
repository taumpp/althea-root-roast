# -*- coding: utf-8 -*-

import app
import chat
import fontconfig
import item
import localeInfo
import net
import os
import osfInfo
import player
import re
import servergamedata
import ui
import uicrimsoncontrols
from uicrimsonember import SettingsScrollBar
from uimountwidgets import MountProgressBar
from uiToolTip import GET_AFFECT_STRING


WIDTH = 632
HEIGHT = 459
ROW_WIDTH = 208
ROW_HEIGHT = 42
ROW_STEP = 53
VISIBLE_ROW_COUNT = 6

ELIXIR_PERCENT_STATUS = False
ELIXIR_TIME_STATUS = False
REMINDER_COOLDOWN_SIGNATURE = None
REMINDER_COOLDOWN_WAS_PENDING = False
REMINDER_NOTIFICATION_SENT = False
REMINDER_SELECTION = (None, False)
VISIBILITY_VERSION = 1
VISIBILITY_ROOT = "UserData/biolog_registry"

ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/biolog/"
MOUNT_ROOT = "d:/ymir work/ui/game/crimson_ember/mount_system/"
CHECKBOX_ROOT = "d:/ymir work/ui/game/crimson_ember/gameoption/"
REMINDER_ICON = "d:/ymir work/ui/game/crimson_ember/dungeon_teleport/icon/bell_20.png"
EYE_ROOT = "d:/ymir work/ui/game/dungeon_info/"

TEXT_COLOR = 0xffebe7e0
MUTED_COLOR = 0xff9d968d
QUIET_COLOR = 0xff6c6863
GOLD_COLOR = 0xffcfb16d
RUBY_COLOR = 0xffe32f52
DIVIDER_COLOR = 0xff3b1719


def _BiologApply(name):
	return getattr(item, name, 0)


def _LegacyBiologRow(row):
	(index, level, vnum, count, cooldown, chance, stone, choice, elixir,
	 elixirCost, clock, clockCost, rewards) = row
	pairs = [value for (name, amount) in rewards[:4] for value in (_BiologApply(name), amount)]
	pairs += [0] * (8 - len(pairs))
	return [level, vnum, count, cooldown, chance, stone] + pairs + [choice, elixir, clock]


def BiologCatalogRows():
	"""Server snapshot prefix (BiologRow3 fields 1..23) for every research."""
	rows = []
	for row in servergamedata.BIOLOG:
		(index, level, vnum, count, cooldown, chance, stone, choice, elixir,
		 elixirCost, clock, clockCost, rewards) = row
		pairs = [value for (name, amount) in rewards for value in (_BiologApply(name), amount)]
		pairs += [0] * (12 - len(pairs))
		rows.append([index, level, vnum, count, cooldown, stone, choice, elixir,
			elixirCost, clock, clockCost] + pairs)
	return rows


# Legacy window view of the server catalogue. Generated from althea/server
# share/locale/europe/biolog_catalog.txt (servergamedata.BIOLOG); only the
# first four rewards fit this layout, BiologCatalogRows() carries all six.
# level, item, count, time, chance, stone, four affect pairs, choose, elixir, clock
bio_data = [[0] * 17] + [_LegacyBiologRow(row) for row in servergamedata.BIOLOG]


def _Text(key, fallback):
	return getattr(localeInfo, key, fallback)


def _SafeCharacterKey(name):
	return "".join(character if character.isalnum() or character in "_-" else "_"
		for character in str(name)) or "unknown"


def _VisibilityPath(characterName):
	return "%s/%s_visibility" % (VISIBILITY_ROOT, _SafeCharacterKey(characterName))


def _DecodeHiddenResearch(raw, maximumIndex):
	tokens = raw.strip().split("\t")
	if not tokens or tokens[0] != str(VISIBILITY_VERSION):
		return set()
	indexes = set()
	for value in tokens[1:]:
		if not value.isdigit():
			continue
		index = int(value)
		if 0 < index <= int(maximumIndex):
			indexes.add(index)
	return indexes


def _LoadHiddenResearch(characterName, maximumIndex):
	try:
		settings = open(_VisibilityPath(characterName), "r")
		raw = settings.read()
		settings.close()
		return _DecodeHiddenResearch(raw, maximumIndex)
	except:
		return set()


def _SaveHiddenResearch(characterName, indexes):
	try:
		if not os.path.isdir(VISIBILITY_ROOT):
			os.makedirs(VISIBILITY_ROOT)
		values = [str(VISIBILITY_VERSION)] + [str(index) for index in sorted(indexes)]
		settings = open(_VisibilityPath(characterName), "w")
		settings.write("\t".join(values))
		settings.close()
		return True
	except:
		return False


def _CreateText(parent, x, y, text=u"", color=TEXT_COLOR, role=None, align="left"):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	if role:
		line.SetFontName(fontconfig.FontForRole(role))
	if align == "center":
		line.SetHorizontalAlignCenter()
	elif align == "right":
		line.SetHorizontalAlignRight()
	line.SetPackedFontColor(color)
	line.SetText(text)
	line.AddFlag("not_pick")
	line.Show()
	return line


def _CreateImage(parent, x, y, filename, notPick=True):
	image = ui.ImageBox()
	image.SetParent(parent)
	image.SetPosition(x, y)
	image.LoadImage(filename)
	if notPick:
		image.AddFlag("not_pick")
	image.Show()
	return image


def _CreateDivider(parent, x, y, width):
	bar = ui.Bar()
	bar.SetParent(parent)
	bar.SetPosition(x, y)
	bar.SetSize(width, 2)
	bar.SetColor(DIVIDER_COLOR)
	bar.AddFlag("not_pick")
	bar.Show()
	return bar


def _MakeSettingsToggle(parent, x, y, checkedEvent, uncheckedEvent, tooltip=None):
	toggle = ui.ToggleButton()
	toggle.SetParent(parent)
	toggle.SetPosition(x, y)
	toggle.SetUpVisual(CHECKBOX_ROOT + "checkbox_unselected.tga")
	toggle.SetOverVisual(CHECKBOX_ROOT + "checkbox_hover.tga")
	toggle.SetDownVisual(CHECKBOX_ROOT + "checkbox_selected.tga")
	toggle.SetToggleDownEvent(checkedEvent)
	toggle.SetToggleUpEvent(uncheckedEvent)
	if tooltip:
		toggle.SetToolTipText(tooltip)
	toggle.Show()
	return toggle


def _ItemName(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetItemName()
	except:
		return "-"


def _ItemIcon(vnum):
	try:
		item.SelectItem(vnum)
		filename = item.GetIconImageFileName()
		if filename and filename.find("gr2") == -1:
			return filename
	except:
		pass
	return ""


def _ShouldNotifyReady(wasPending, alreadySent, reminderEnabled):
	return bool(wasPending and not alreadySent and reminderEnabled)


def _ReminderSignature(level, cooldownTime):
	try:
		characterName = player.GetName()
	except:
		characterName = ""
	return (characterName, int(level), int(cooldownTime))


def _RestoreReminderState(signature, cooldownTime, now):
	global REMINDER_COOLDOWN_SIGNATURE
	global REMINDER_COOLDOWN_WAS_PENDING
	global REMINDER_NOTIFICATION_SENT
	if signature != REMINDER_COOLDOWN_SIGNATURE:
		REMINDER_COOLDOWN_SIGNATURE = signature
		REMINDER_COOLDOWN_WAS_PENDING = int(cooldownTime) > int(now)
		REMINDER_NOTIFICATION_SENT = False
	return (REMINDER_COOLDOWN_WAS_PENDING, REMINDER_NOTIFICATION_SENT)


def _StoreReminderState(signature, wasPending, notificationSent):
	global REMINDER_COOLDOWN_SIGNATURE
	global REMINDER_COOLDOWN_WAS_PENDING
	global REMINDER_NOTIFICATION_SENT
	REMINDER_COOLDOWN_SIGNATURE = signature
	REMINDER_COOLDOWN_WAS_PENDING = bool(wasPending)
	REMINDER_NOTIFICATION_SENT = bool(notificationSent)



def _StoreReminderSelection(enabled):
	global REMINDER_SELECTION
	REMINDER_SELECTION = (player.GetName(), bool(enabled))


def _RestoreReminderSelection():
	# Stone/gift snapshots omit the bell flag; retain it across same-character
	# warp reconstruction, while real logout resets this presentation preference.
	character, enabled = REMINDER_SELECTION
	return bool(character == player.GetName() and enabled)


def ResetReminderState():
	global REMINDER_SELECTION
	REMINDER_SELECTION = (None, False)
	global REMINDER_COOLDOWN_SIGNATURE
	global REMINDER_COOLDOWN_WAS_PENDING
	global REMINDER_NOTIFICATION_SENT
	REMINDER_COOLDOWN_SIGNATURE = None
	REMINDER_COOLDOWN_WAS_PENDING = False
	REMINDER_NOTIFICATION_SENT = False


class BiologResearchRow(ui.Window):
	def __init__(self, parent, owner):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetSize(ROW_WIDTH, ROW_STEP)
		self.owner = owner
		self.index = 0
		self.rowState = "locked"

		self.carrier = ui.Button()
		self.carrier.SetParent(self)
		self.carrier.SetPosition(0, 5)
		self.carrier.SetSize(ROW_WIDTH, ROW_HEIGHT)
		self.carrier.SetEvent(self._OnSelect)
		self.carrier.Show()

		self.icon = _CreateImage(self, 7, 10, ASSET_ROOT + "row_normal_208x42.png", False)
		self.icon.SetSize(32, 32)
		self.icon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.owner.OverOutItem)
		self.icon.SetMouseLeftButtonUpEvent(self._OnSelect)
		self.name = _CreateText(self, 47, 13, role=fontconfig.ROLE_CONTROL)
		self.name.SetLimitWidth(143)
		self.state = _CreateText(self, 47, 29, role=fontconfig.ROLE_DENSE)
		self.level = _CreateText(self, 201, 29, color=GOLD_COLOR, role=fontconfig.ROLE_DENSE, align="right")
		self.glyph = _CreateImage(self, 196, 10, MOUNT_ROOT + "glyph_lock_8.png")
		self.eye = ui.Button()
		self.eye.SetParent(self)
		self.eye.SetPosition(191, 14)
		self.eye.SetUpVisual(EYE_ROOT + "btn_hide_1.png")
		self.eye.SetOverVisual(EYE_ROOT + "btn_hide_2.png")
		self.eye.SetDownVisual(EYE_ROOT + "btn_hide_3.png")
		self.eye.SetEvent(self._OnHide)
		self.eye.SetToolTipText(_Text("BIO_HIDE_COMPLETED", u"Skrýt dokončený výzkum"))
		self.eye.Hide()
		self.Show()

	def _OnSelect(self):
		self.owner.SelectResearch(self.index)

	def _OnHide(self):
		self.owner.HideCompletedResearch(self.index)

	def SetData(self, index, activeIndex, selectedIndex):
		self.index = index
		data = bio_data[index]
		if index < activeIndex:
			state = "completed"
		elif index == activeIndex:
			state = "active"
		else:
			state = "locked"

		self.rowState = state
		self.carrier.Enable()
		self.carrier.SetUpVisual(ASSET_ROOT + "row_normal_208x42.png")
		self.carrier.SetOverVisual(ASSET_ROOT + "row_hover_208x42.png")
		self.carrier.SetDownVisual(ASSET_ROOT + "row_selected_208x42.png")
		self.carrier.SetDisableVisual(ASSET_ROOT + "row_disabled_208x42.png")
		if index == selectedIndex:
			self.carrier.SetUpVisual(ASSET_ROOT + "row_selected_208x42.png")
			self.carrier.SetOverVisual(ASSET_ROOT + "row_selected_208x42.png")
			self.carrier.Down()
		else:
			self.carrier.SetUp()

		iconPath = _ItemIcon(data[1])
		if iconPath:
			self.icon.LoadImage(iconPath)
			self.icon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.owner.OverInItem, data[1])
			self.icon.Show()
		else:
			self.icon.Hide()
		self.name.SetText(_ItemName(data[1]))
		self.level.SetText("Lv. %d" % data[0])
		if state == "completed":
			self.state.SetText(_Text("BIO_COMPLETED", u"Dokončeno"))
			self.state.SetPackedFontColor(GOLD_COLOR)
			self.name.SetPackedFontColor(TEXT_COLOR)
			self.glyph.LoadImage(MOUNT_ROOT + "glyph_check_8.png")
		elif state == "active":
			self.state.SetText(_Text("BIO_ACTIVE_STATE", u"Aktivní"))
			self.state.SetPackedFontColor(RUBY_COLOR)
			self.name.SetPackedFontColor(TEXT_COLOR)
			self.glyph.LoadImage(MOUNT_ROOT + "glyph_right_8.png")
		else:
			self.state.SetText(_Text("BIO_LOCKED", u"Uzamčeno"))
			self.state.SetPackedFontColor(QUIET_COLOR)
			self.name.SetPackedFontColor(QUIET_COLOR)
			self.level.SetPackedFontColor(QUIET_COLOR)
			self.glyph.LoadImage(MOUNT_ROOT + "glyph_lock_8.png")
		if state != "locked":
			self.level.SetPackedFontColor(GOLD_COLOR)
		self.eye.Hide()
		self.glyph.Show()

	def OnUpdate(self):
		if self.rowState == "completed" and self.IsIn():
			self.glyph.Hide()
			self.eye.Show()
		else:
			self.eye.Hide()
			self.glyph.Show()


class BiologWindow(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag("float")
		self.AddFlag("movable")
		if app.ENABLE_ANIMATED_WINDOW:
			self.AddFlag("animate")
		self.SetWindowName("BiologWindow")
		self.SetSize(WIDTH, HEIGHT)
		self.SetCenterPosition()

		self.children = []
		self.bioLevel = 0
		self.dataKnown = False
		self.bioCount = 0
		self.bioTime = 0
		self.needUpdate = True
		self.cooldownWasPending = False
		self.readyNotificationSent = False
		self.cooldownSignature = None
		self.registryStart = 0
		self.mode = "empty"
		self.completedAll = False
		self.detailIndex = 0
		self.detailSelectionExplicit = False
		self.activeDisplay = None
		try:
			characterName = player.GetName()
		except:
			characterName = ""
		self.hiddenCompleted = _LoadHiddenResearch(characterName, len(bio_data) - 1)
		self._BuildWindow()

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		game = osfInfo.GetGameInstance()
		if game:
			game.RemoveLoopEvent("bio")
		self.children = []
		ui.Window.Destroy(self)

	def ResetReminderState(self):
		ResetReminderState()

	def _Own(self, child):
		self.children.append(child)
		return child

	def _BuildWindow(self):
		self.body = self._Own(_CreateImage(self, 0, 23, ASSET_ROOT + "body_632x436.png"))

		self.titleBar = ui.TitleBar()
		self.titleBar.SetParent(self)
		self.titleBar.MakeTitleBar(WIDTH, "red")
		self.titleBar.SetPosition(0, 0)
		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		self.titleBar.Show()
		self._Own(self.titleBar)
		self.titleText = self._Own(_CreateText(
			self.titleBar, 22, 5,
			_Text("BIO_RESEARCH_TITLE", u"Biologický výzkum"),
			TEXT_COLOR, fontconfig.ROLE_WINDOW_TITLE,
		))

		self.registryTitle = self._Own(_CreateText(
			self, 14, 43, _Text("BIO_RESEARCH_REGISTRY", u"VÝZKUMNÝ REGISTR"),
			TEXT_COLOR, fontconfig.ROLE_SECTION,
		))
		self.registryCount = self._Own(_CreateText(
			self, 240, 43, "0 / 10", GOLD_COLOR, fontconfig.ROLE_CONTROL, "right",
		))
		self.registrySubtitle = self._Own(_CreateText(
			self, 14, 64, _Text("BIO_ALL_RESEARCH", u"Všechny výzkumy"),
			MUTED_COLOR, fontconfig.ROLE_DENSE,
		))
		self.restoreHiddenButton = ui.Button()
		self.restoreHiddenButton.SetParent(self)
		self.restoreHiddenButton.SetPosition(205, 59)
		self.restoreHiddenButton.SetUpVisual("d:/ymir work/ui/game/windows/refresh_titlebar_up.sub")
		self.restoreHiddenButton.SetOverVisual("d:/ymir work/ui/game/windows/refresh_titlebar_over.sub")
		self.restoreHiddenButton.SetDownVisual("d:/ymir work/ui/game/windows/refresh_titlebar_down.sub")
		self.restoreHiddenButton.SetEvent(ui.__mem_func__(self.RestoreHiddenResearch))
		self.restoreHiddenButton.SetToolTipText(_Text("BIO_RESTORE_HIDDEN", u"Obnovit skryté výzkumy"))
		self.restoreHiddenButton.Hide()
		self._Own(self.restoreHiddenButton)

		self.registryViewport = ui.Window()
		self.registryViewport.SetParent(self)
		self.registryViewport.SetPosition(12, 82)
		self.registryViewport.SetSize(218, 318)
		self.registryViewport.Show()
		self._Own(self.registryViewport)
		self.registryRows = []
		for rowIndex in range(VISIBLE_ROW_COUNT):
			row = BiologResearchRow(self.registryViewport, self)
			row.SetPosition(0, rowIndex * ROW_STEP)
			self.registryRows.append(row)
			self._Own(row)

		self.registryScroll = SettingsScrollBar()
		self.registryScroll.SetParent(self)
		self.registryScroll.SetPosition(230, 82)
		self.registryScroll.SetScrollBarSize(318)
		self.registryScroll.SetMiddleBarSize(float(VISIBLE_ROW_COUNT) / float(len(bio_data) - 1))
		self.registryScroll.SetScrollStep(1.0 / float((len(bio_data) - 1) - VISIBLE_ROW_COUNT))
		self.registryScroll.SetScrollEvent(ui.__mem_func__(self._OnRegistryScroll))
		self.registryScroll.Show()
		self._Own(self.registryScroll)

		self._BuildDetail()
		self._RefreshRegistry()

	def _BuildDetail(self):
		x = 264
		self.heroLabel = self._Own(_CreateText(
			self, x, 39, _Text("BIO_ACTIVE_RESEARCH", u"AKTIVNÍ VÝZKUM"),
			GOLD_COLOR, fontconfig.ROLE_SECTION,
		))
		self.heroSlot = self._Own(_CreateImage(self, x, 72, MOUNT_ROOT + "slot_item_32x32.png"))
		self.missionIcon = self._Own(_CreateImage(self, x, 72, MOUNT_ROOT + "slot_item_32x32.png", False))
		self.missionIcon.SetSize(32, 32)
		self.missionIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
		self.missionName = self._Own(_CreateText(
			self, x + 42, 61, "-", TEXT_COLOR, fontconfig.ROLE_LARGE_BOLD,
		))
		self.missionName.SetLimitWidth(238)
		self.metadataText = self._Own(_CreateText(
			self, x + 42, 89, "-", MUTED_COLOR, fontconfig.ROLE_DENSE,
		))
		self.metadataText.SetLimitWidth(238)
		self.levelCaption = self._Own(_CreateText(
			self, x + 42, 94, _Text("BIO_LEVEL_CAPTION", u"ÚROVEŇ"),
			MUTED_COLOR, fontconfig.ROLE_DENSE,
		))
		self.levelValue = self._Own(_CreateText(self, x + 91, 94, "-", GOLD_COLOR, fontconfig.ROLE_CONTROL))
		self.metaSeparator = self._Own(_CreateText(self, x + 112, 94, "|", QUIET_COLOR, fontconfig.ROLE_DENSE))
		self.inventoryCaption = self._Own(_CreateText(
			self, x + 123, 94, _Text("BIO_IN_INVENTORY", u"V BATOHU"),
			MUTED_COLOR, fontconfig.ROLE_DENSE,
		))
		self.inventoryValue = self._Own(_CreateText(self, x + 181, 94, "0", GOLD_COLOR, fontconfig.ROLE_CONTROL))
		for widget in (
			self.levelCaption, self.levelValue, self.metaSeparator,
			self.inventoryCaption, self.inventoryValue,
		):
			widget.Hide()
		self.portrait = self._Own(_CreateImage(self, 552, 37, ASSET_ROOT + "portrait_chaegirab_62x104.png"))
		self._Own(_CreateDivider(self, x, 153, 346))

		self.progressCaption = self._Own(_CreateText(
			self, x, 164, _Text("BIO_RESEARCH_PROGRESS", u"POSTUP VÝZKUMU"),
			GOLD_COLOR, fontconfig.ROLE_SECTION,
		))
		self.progressCaption.Hide()
		self.progressText = self._Own(_CreateText(self, x, 172, "0 / 0", TEXT_COLOR, fontconfig.ROLE_LARGE_BOLD))
		self.progressPercent = self._Own(_CreateText(self, x + 346, 173, "0 %", MUTED_COLOR, fontconfig.ROLE_CONTROL, "right"))
		self.progressBar = MountProgressBar(self, x, 194, "overall")
		self._Own(self.progressBar)
		self._Own(_CreateDivider(self, x, 220, 346))

		self.rewardCaption = self._Own(_CreateText(
			self, 452, 244, _Text("BIO_REWARD", u"ODMĚNA"),
			GOLD_COLOR, fontconfig.ROLE_SECTION,
		))
		self.missionGiftText = self._Own(_CreateText(self, 452, 271, "-", GOLD_COLOR, fontconfig.ROLE_LARGE_BOLD))
		self.missionGiftText.SetLimitWidth(158)
		self.rewardDetailText = self._Own(_CreateText(
			self, 452, 295, "-", MUTED_COLOR, fontconfig.ROLE_DENSE,
		))
		self.rewardDetailText.SetLimitWidth(158)
		self.rewardHint = self._Own(_CreateText(
			self, 452, 315,
			_Text("BIO_REWARD_HINT", u"Připíše se po dokončení výzkumu."),
			MUTED_COLOR, fontconfig.ROLE_DENSE,
		))
		self.rewardHint.Hide()
		self.infoDivider = ui.Bar()
		self.infoDivider.SetParent(self)
		self.infoDivider.SetPosition(437, 238)
		self.infoDivider.SetSize(2, 112)
		self.infoDivider.SetColor(DIVIDER_COLOR)
		self.infoDivider.AddFlag("not_pick")
		self.infoDivider.Show()
		self._Own(self.infoDivider)

		self.statusCaption = self._Own(_CreateText(
			self, x, 244, _Text("BIO_NEXT_SUBMISSION", u"DALŠÍ ODEVZDÁNÍ"),
			GOLD_COLOR, fontconfig.ROLE_SECTION,
		))
		self.statusText = self._Own(_CreateText(self, x, 271, localeInfo.BIO_DONT_HAVE_MISSION, RUBY_COLOR, fontconfig.ROLE_LARGE_BOLD))
		self.statusText.SetLimitWidth(158)
		self.intervalText = self._Own(_CreateText(self, x + 346, 347, "", MUTED_COLOR, fontconfig.ROLE_DENSE, "right"))
		self.intervalText.Hide()
		self._Own(_CreateDivider(self, x, 371, 346))

		self.elixirPercent = self._Own(_CreateImage(self, x, 395, MOUNT_ROOT + "slot_item_32x32.png", False))
		self.elixirPercent.SetSize(32, 32)
		self.elixirPercent.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
		self.chanceLabel = self._Own(_CreateText(self, x + 36, 404, _Text("BIO_CHANCE", u"Šance"), TEXT_COLOR, fontconfig.ROLE_DENSE))
		self.checkBoxElixirPercent = self._Own(_MakeSettingsToggle(
			self, x + 72, 404,
			lambda: self.CheckBoxEvent(None, "ELIXIR_PERCENT", True),
			lambda: self.CheckBoxEvent(None, "ELIXIR_PERCENT", False),
		))

		self.elixirTime = self._Own(_CreateImage(self, x + 91, 395, MOUNT_ROOT + "slot_item_32x32.png", False))
		self.elixirTime.SetSize(32, 32)
		self.elixirTime.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
		self.timeLabel = self._Own(_CreateText(self, x + 127, 404, _Text("BIO_TIME", u"Čas"), TEXT_COLOR, fontconfig.ROLE_DENSE))
		self.checkBoxElixirTime = self._Own(_MakeSettingsToggle(
			self, x + 152, 404,
			lambda: self.CheckBoxEvent(None, "ELIXIR_TIME", True),
			lambda: self.CheckBoxEvent(None, "ELIXIR_TIME", False),
		))

		self.reminderIcon = self._Own(_CreateImage(self, x + 174, 401, REMINDER_ICON))
		self.reminderLabel = self._Own(_CreateText(
			self, x + 197, 404, _Text("BIO_REMINDER", u"Budík"),
			TEXT_COLOR, fontconfig.ROLE_DENSE,
		))
		reminderTooltip = _Text(
			"BIO_REMINDER_TOOLTIP",
			u"Zobrazit oznámení, až bude možné znovu odevzdávat.",
		)
		self.checkBoxCall = self._Own(_MakeSettingsToggle(
			self, x + 231, 404,
			lambda: self.CheckBoxEvent(None, "CALL", True),
			lambda: self.CheckBoxEvent(None, "CALL", False),
			reminderTooltip,
		))

		self.submitButton = ui.Button()
		self.submitButton.SetParent(self)
		self.submitButton.SetPosition(522, 401)
		self.submitButton.SetSize(88, 21)
		uicrimsoncontrols.ApplyVisuals(self.submitButton, "88x21")
		self.submitButton.SetText(_Text("BIO_SUBMIT_SHORT", u"Odevzdat"))
		self.submitButton.SetEvent(ui.__mem_func__(self.GiveMission))
		self.submitButton.Show()
		self._Own(self.submitButton)

		self.giftFirst = self._CreateGiftButton(264, 261, 0)
		self.giftSecond = self._CreateGiftButton(440, 261, 1)
		self.giftThird = self._CreateGiftButton(352, 286, 2)

		global ELIXIR_PERCENT_STATUS, ELIXIR_TIME_STATUS
		self._SetToggle(self.checkBoxElixirPercent, ELIXIR_PERCENT_STATUS)
		self._SetToggle(self.checkBoxElixirTime, ELIXIR_TIME_STATUS)
		self._SetToggle(self.checkBoxCall, _RestoreReminderSelection())

	def _CreateGiftButton(self, x, y, index):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetSize(170, 24)
		uicrimsoncontrols.ApplyVisuals(button, "170x24")
		button.SetEvent(lambda giftIndex=index: self.ClickGift(giftIndex))
		button.Hide()
		return self._Own(button)

	def _SetToggle(self, toggle, enabled):
		if enabled:
			toggle.Down()
		else:
			toggle.SetUp()

	def _SetBoostersVisible(self, visible):
		widgets = (
			self.elixirPercent, self.chanceLabel, self.checkBoxElixirPercent,
			self.elixirTime, self.timeLabel, self.checkBoxElixirTime,
		)
		for widget in widgets:
			widget.Show() if visible else widget.Hide()

	def _SetReminderVisible(self, visible):
		for widget in (self.reminderIcon, self.reminderLabel, self.checkBoxCall):
			widget.Show() if visible else widget.Hide()

	def _SetActionsVisible(self, visible):
		self._SetBoostersVisible(visible)
		self._SetReminderVisible(visible)
		self.submitButton.Show() if visible else self.submitButton.Hide()

	def _SetGiftButtonsVisible(self, visible):
		for button in (self.giftFirst, self.giftSecond, self.giftThird):
			button.Show() if visible else button.Hide()

	def _SetCompactInfoVisible(self, visible):
		widgets = (
			self.statusCaption, self.statusText, self.rewardCaption,
			self.missionGiftText, self.rewardDetailText, self.infoDivider,
		)
		for widget in widgets:
			widget.Show() if visible else widget.Hide()

	def _OnRegistryScroll(self):
		maximumStart = max(0, len(self.VisibleResearchIndexes()) - VISIBLE_ROW_COUNT)
		self.registryStart = int(round(self.registryScroll.GetPos() * maximumStart))
		self._RefreshRegistry()

	def _ActiveIndex(self):
		return len(bio_data) if self.completedAll else self.bioLevel

	def _IsCompletedIndex(self, index):
		return bool(self.completedAll or (0 < index < self._ActiveIndex()))

	def VisibleResearchIndexes(self):
		return [index for index in range(1, len(bio_data))
			if not (self._IsCompletedIndex(index) and index in self.hiddenCompleted)]

	def _SaveVisibility(self):
		try:
			characterName = player.GetName()
		except:
			characterName = ""
		_SaveHiddenResearch(characterName, self.hiddenCompleted)

	def HideCompletedResearch(self, index):
		if not self._IsCompletedIndex(index):
			return False
		self.hiddenCompleted.add(int(index))
		self._SaveVisibility()
		if self.detailIndex == index:
			self.detailSelectionExplicit = False
			if self.bioLevel:
				self.SelectResearch(self.bioLevel)
			elif self.completedAll:
				visibleIndexes = self.VisibleResearchIndexes()
				if visibleIndexes:
					nearestIndex = min(visibleIndexes, key=lambda value: abs(value - index))
					self.SelectResearch(nearestIndex)
				else:
					self.LoadEmpty(True)
			else:
				self.detailIndex = 0
		self._RefreshRegistry()
		return True

	def RestoreHiddenResearch(self):
		self.hiddenCompleted.clear()
		self._SaveVisibility()
		self.registryStart = 0
		self.detailSelectionExplicit = False
		if self.bioLevel:
			self.SelectResearch(self.bioLevel)
		elif self.completedAll:
			self.SelectResearch(1)
		else:
			self.detailIndex = 0
			self._RefreshRegistry()
		self._FocusActiveRow()

	def _RefreshRegistry(self):
		if self.completedAll:
			activeIndex = len(bio_data)
			completed = len(bio_data) - 1
		else:
			activeIndex = self.bioLevel if 0 < self.bioLevel < len(bio_data) else 0
			completed = max(0, activeIndex - 1)
		visibleIndexes = self.VisibleResearchIndexes()
		maximumStart = max(0, len(visibleIndexes) - VISIBLE_ROW_COUNT)
		self.registryStart = max(0, min(self.registryStart, maximumStart))
		self.registryCount.SetText("%d / %d" % (completed, len(bio_data) - 1))
		if self.hiddenCompleted:
			self.restoreHiddenButton.Show()
		else:
			self.restoreHiddenButton.Hide()
		for rowOffset, row in enumerate(self.registryRows):
			visibleOffset = self.registryStart + rowOffset
			if visibleOffset >= len(visibleIndexes):
				row.Hide()
				continue
			row.SetData(visibleIndexes[visibleOffset], activeIndex, self.detailIndex)
			row.Show()
		if maximumStart:
			self.registryScroll.SetMiddleBarSize(
				float(VISIBLE_ROW_COUNT) / float(len(visibleIndexes)))
			self.registryScroll.SetScrollStep(1.0 / float(maximumStart))
			self.registryScroll.Show()
		else:
			self.registryScroll.Hide()

	def _FocusActiveRow(self):
		if not self.bioLevel:
			return
		visibleIndexes = self.VisibleResearchIndexes()
		if self.bioLevel not in visibleIndexes:
			return
		maximumStart = max(0, len(visibleIndexes) - VISIBLE_ROW_COUNT)
		start = max(0, min(maximumStart, visibleIndexes.index(self.bioLevel) - 2))
		self.registryStart = start
		if maximumStart:
			self.registryScroll.SetPos(float(start) / float(maximumStart))
		else:
			self._RefreshRegistry()

	def _SetMissionIcon(self, vnum):
		iconPath = _ItemIcon(vnum)
		if not iconPath:
			self.missionIcon.Hide()
			return
		self.missionIcon.LoadImage(iconPath)
		self.missionIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, vnum)
		self.missionIcon.Show()

	def _SetBoosterIcon(self, widget, vnum):
		iconPath = _ItemIcon(vnum)
		if not iconPath:
			widget.Hide()
			return
		widget.LoadImage(iconPath)
		widget.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, vnum)
		widget.Show()

	def _RewardText(self, level):
		if level == 7:
			return localeInfo.BIO_ALL_DEFENSE_CHARACTER % 10
		if level == 8:
			return localeInfo.BIO_ALL_ATT_CHARACTER % 10
		parts = []
		data = bio_data[level]
		for offset in (6, 8, 10, 12):
			if data[offset]:
				parts.append(self.GetAffectString(data[offset], data[offset + 1]))
		return " , ".join(parts) if parts else "-"

	def _SplitReward(self, text, value, percent):
		text = text or "-"
		value = int(value)
		pattern = r"\s*[+-]?\s*%d\s*%%\s*" % abs(value)
		label = re.sub(pattern, " ", text, count=1)
		if label == text:
			pattern = r"\s*[+-]?\s*%d\s*" % abs(value)
			label = re.sub(pattern, " ", text, count=1)
		label = label.strip(" \t:-,|") or text
		primary = "+%d %%" % value if percent else "%+d" % value
		return primary, label

	def _CompactReward(self, level):
		data = bio_data[level]
		if data[14]:
			return (
				_Text("BIO_REWARD_CHOICE_COUNT", u"Výběr 1 ze 3"),
				_Text("BIO_REWARD_CHOICE_TYPES", u"ZB / Obrana / Útok"),
			)
		rewards = [(data[offset], data[offset + 1]) for offset in (6, 8, 10, 12) if data[offset]]
		if not rewards:
			return "-", "-"
		# The catalogue is server data; group the class sets by kind, not by row id.
		kinds = set(kind for kind, value in rewards)
		values = set(value for kind, value in rewards)
		if len(rewards) == 4 and len(values) == 1:
			resist = set(getattr(item, name, -1) for name in (
				"APPLY_RESIST_WARRIOR", "APPLY_RESIST_ASSASSIN", "APPLY_RESIST_SURA", "APPLY_RESIST_SHAMAN"))
			attack = set(getattr(item, name, -1) for name in (
				"APPLY_ATTBONUS_WARRIOR", "APPLY_ATTBONUS_ASSASSIN", "APPLY_ATTBONUS_SURA", "APPLY_ATTBONUS_SHAMAN"))
			if kinds == resist:
				return "4x +%d %%" % rewards[0][1], _Text("BIO_CLASS_DEFENSES", u"Obrana proti povoláním")
			if kinds == attack:
				return "4x +%d %%" % rewards[0][1], _Text("BIO_CLASS_ATTACKS", u"Silný proti povoláním")
		affectType, value = rewards[0]
		percent = affectType in (item.APPLY_MOV_SPEED, item.APPLY_ATT_SPEED)
		primary, detail = self._SplitReward(self.GetAffectString(affectType, value), value, percent)
		# The legacy row holds four rewards; the catalogue may grant up to six.
		total = len(servergamedata.BIOLOG[level - 1][12]) if 0 < level <= len(servergamedata.BIOLOG) else len(rewards)
		if total > 1:
			detail = "%s (+%d)" % (detail, total - 1)
		return primary, detail

	def _RenderMission(self, level, iconVnum, count, total, inventoryVnum=None, nameText=None):
		data = bio_data[level]
		if inventoryVnum is None:
			inventoryVnum = data[1]
		self._SetMissionIcon(iconVnum)
		self.missionName.SetText(nameText if nameText is not None else _ItemName(data[1]))
		self.levelValue.SetText(str(data[0]))
		try:
			inventoryCount = max(0, int(player.GetItemCountByVnum(inventoryVnum)))
		except:
			inventoryCount = 0
		self.inventoryValue.SetText(str(inventoryCount))
		self.metadataText.SetText("Lv. %d  |  %s %d  |  %d min" % (
			data[0], _Text("BIO_IN_INVENTORY", u"V batohu"), inventoryCount,
			max(1, int(data[3]) // 60),
		))
		self.progressText.SetText("%d / %d" % (count, total))
		percentage = int(float(count) * 100.0 / float(max(1, total)))
		self.progressPercent.SetText("%d %%" % percentage)
		self.progressBar.SetValue(count, total)
		rewardPrimary, rewardDetail = self._CompactReward(level)
		self.missionGiftText.SetText(rewardPrimary)
		self.rewardDetailText.SetText(rewardDetail)
		self.intervalText.SetText("")
		self._RefreshRegistry()

	def _ApplyMission(self, level, iconVnum, count, total, inventoryVnum=None, nameText=None):
		if inventoryVnum is None:
			inventoryVnum = bio_data[level][1]
		self.bioLevel = level
		self.completedAll = False
		self.bioCount = count
		self.activeDisplay = (level, iconVnum, count, total, inventoryVnum, nameText)
		self._RenderMission(level, iconVnum, count, total, inventoryVnum, nameText)
		self._FocusActiveRow()

	def _ShowPreview(self, index, completed):
		data = bio_data[index]
		count = data[2] if completed else 0
		self.detailIndex = index
		self._RenderMission(index, data[1], count, data[2], data[1])
		self.heroLabel.SetText(_Text(
			"BIO_COMPLETED_RESEARCH" if completed else "BIO_PREVIEW_RESEARCH",
			u"Dokončený výzkum" if completed else u"Náhled výzkumu",
		))
		self._SetNormalDetailVisibility()
		self._SetActionsVisible(False)
		self._SetGiftButtonsVisible(False)
		if completed:
			self.statusText.SetText(_Text("BIO_COMPLETED", u"Dokončeno"))
			self.statusText.SetPackedFontColor(GOLD_COLOR)
		else:
			self.statusText.SetText(_Text("BIO_UNLOCK_LEVEL_SHORT", u"Lv. %d") % data[0])
			self.statusText.SetPackedFontColor(MUTED_COLOR)

	def _RestoreActiveDetail(self):
		if not self.activeDisplay:
			return
		self.detailIndex = self.bioLevel
		self.heroLabel.SetText(_Text("BIO_ACTIVE_RESEARCH", u"AKTIVNÍ VÝZKUM"))
		self._RenderMission(*self.activeDisplay)
		self._SetNormalDetailVisibility()
		if self.mode == "mission":
			self._SetActionsVisible(True)
			self.OnUpdate()
		elif self.mode == "stone":
			self._SetBoostersVisible(False)
			self._SetReminderVisible(True)
			self.submitButton.Show()
			self.statusText.SetText(localeInfo.BIO_FIND_STONE)
			self.statusText.SetPackedFontColor(GOLD_COLOR)
		elif self.mode == "gift":
			self._SetActionsVisible(False)
			self._SetCompactInfoVisible(False)
			self._SetGiftButtonsVisible(True)

	def SelectResearch(self, index):
		index = int(index)
		if index <= 0 or index >= len(bio_data):
			return False
		if index == self.bioLevel and not self.completedAll:
			self.detailSelectionExplicit = False
			self._RestoreActiveDetail()
		else:
			self.detailSelectionExplicit = True
			self._ShowPreview(index, self._IsCompletedIndex(index))
		self._RefreshRegistry()
		return True

	def _ResolveDetailAfterLoad(self):
		if (self.detailSelectionExplicit and 0 < self.detailIndex < len(bio_data)
				and self.detailIndex in self.VisibleResearchIndexes()
				and self.detailIndex != self.bioLevel):
			self._ShowPreview(self.detailIndex, self._IsCompletedIndex(self.detailIndex))
			return
		self.detailSelectionExplicit = False
		self._RestoreActiveDetail()

	def _SetNormalDetailVisibility(self):
		self._SetCompactInfoVisible(True)
		self.rewardHint.Hide()
		self.submitButton.Show()
		self._SetGiftButtonsVisible(False)

	def CheckBoxEvent(self, name, type, flag):
		if type == "ELIXIR_PERCENT":
			global ELIXIR_PERCENT_STATUS
			ELIXIR_PERCENT_STATUS = bool(flag)
		elif type == "ELIXIR_TIME":
			global ELIXIR_TIME_STATUS
			ELIXIR_TIME_STATUS = bool(flag)
		elif type == "CALL":
			_StoreReminderSelection(flag)
			if flag:
				net.SendChatPacket("/bio_notification 1")
				self.readyNotificationSent = False
				self.cooldownWasPending = self.bioTime > app.GetGlobalTimeStamp()
				_StoreReminderState(
					self.cooldownSignature,
					self.cooldownWasPending,
					self.readyNotificationSent,
				)
				self._StartReminderLoop()
			else:
				net.SendChatPacket("/bio_notification 0")
				self._StopReminderLoop()

			interface = osfInfo.GetInterfaceInstance()
			if interface and hasattr(interface, "RefreshCountdownHUDSelection"):
				interface.RefreshCountdownHUDSelection(bool(flag))

	def _StartReminderLoop(self):
		game = osfInfo.GetGameInstance()
		if game:
			game.AddLoopEvent("bio", ui.__mem_func__(self.OnUpdate))

	def _StopReminderLoop(self):
		game = osfInfo.GetGameInstance()
		if game:
			game.RemoveLoopEvent("bio")

	def _NotifyReadyOnce(self):
		if not _ShouldNotifyReady(
			self.cooldownWasPending,
			self.readyNotificationSent,
			self.checkBoxCall.IsDown(),
		):
			return
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			iconVnum = 0
			if 0 <= self.bioLevel < len(bio_data):
				iconVnum = bio_data[self.bioLevel][1]
			accepted = interface.PushBiologReadyNotification(
				_Text("BIO_READY_NOTIFICATION_TITLE", u"Biologický výzkum"),
				_Text("BIO_READY_NOTIFICATION_MESSAGE", u"Můžeš znovu odevzdávat"),
				iconVnum,
				self.cooldownSignature,
			)
			if not accepted:
				return
			self.readyNotificationSent = True
			_StoreReminderState(
				self.cooldownSignature,
				self.cooldownWasPending,
				self.readyNotificationSent,
			)

	def OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.tooltipItem:
			interface.tooltipItem.HideToolTip()

	def OverInItem(self, index):
		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.tooltipItem:
			interface.tooltipItem.SetItemToolTip(index)
			interface.tooltipItem.ShowToolTip()

	def GetAffectString(self, affectType, affectValue):
		if not affectType:
			return "None"
		return GET_AFFECT_STRING(affectType, affectValue)

	def LoadData(self, level, count, time, enableNotification):
		_StoreReminderSelection(int(enableNotification) == 1)
		self.dataKnown = True
		if level <= 0 or level >= len(bio_data):
			self.LoadEmpty()
			return
		newSignature = _ReminderSignature(level, time)
		self.cooldownSignature = newSignature
		self.bioTime = int(time)
		self.cooldownWasPending, self.readyNotificationSent = _RestoreReminderState(
			newSignature, self.bioTime, app.GetGlobalTimeStamp(),
		)
		self.needUpdate = False
		self.mode = "mission"
		self._SetToggle(self.checkBoxCall, int(enableNotification) == 1)
		self._ApplyMission(level, bio_data[level][1], int(count), bio_data[level][2])
		self._SetBoosterIcon(self.elixirPercent, bio_data[level][15])
		self._SetBoosterIcon(self.elixirTime, bio_data[level][16])
		self._SetBoostersVisible(True)
		self._SetNormalDetailVisibility()
		self._ResolveDetailAfterLoad()
		self.OnUpdate()
		if (self.checkBoxCall.IsDown() and self.cooldownWasPending
				and not self.readyNotificationSent and not self.needUpdate):
			self._StartReminderLoop()
		else:
			self._StopReminderLoop()

	def LoadStone(self, level):
		self.dataKnown = True
		if level <= 0 or level >= len(bio_data):
			self.LoadEmpty()
			return
		stoneVnum = bio_data[level][5] or bio_data[level][1]
		self.bioTime = 0
		self.needUpdate = True
		self.cooldownWasPending = False
		self.mode = "stone"
		self._StopReminderLoop()
		stoneName = _ItemName(stoneVnum)
		missionName = "%s - %s" % (stoneName, _ItemName(bio_data[level][1]))
		self._ApplyMission(
			level, stoneVnum, bio_data[level][2], bio_data[level][2],
			stoneVnum, missionName,
		)
		self._SetBoostersVisible(False)
		self._SetNormalDetailVisibility()
		self.statusText.SetText(localeInfo.BIO_FIND_STONE)
		self.statusText.SetPackedFontColor(GOLD_COLOR)
		self._ResolveDetailAfterLoad()

	def LoadGift(self, level):
		self.dataKnown = True
		if level <= 0 or level >= len(bio_data):
			self.LoadEmpty()
			return
		iconVnum = bio_data[level][5] or bio_data[level][1]
		self.bioTime = 0
		self.needUpdate = True
		self.cooldownWasPending = False
		self.mode = "gift"
		self._StopReminderLoop()
		self._ApplyMission(level, iconVnum, bio_data[level][2], bio_data[level][2])
		self._SetBoostersVisible(False)
		self.submitButton.Hide()
		self._SetCompactInfoVisible(False)
		for index, button in enumerate((self.giftFirst, self.giftSecond, self.giftThird)):
			offset = 6 + index * 2
			button.SetText(self.GetAffectString(bio_data[level][offset], bio_data[level][offset + 1]))
		self._SetGiftButtonsVisible(True)
		self._ResolveDetailAfterLoad()

	def LoadEmpty(self, completed=False):
		self.dataKnown = True
		self.bioLevel = 0
		self.completedAll = bool(completed)
		self.bioCount = 0
		self.bioTime = 0
		self.needUpdate = True
		self.cooldownWasPending = False
		self.mode = "empty"
		self.activeDisplay = None
		self.missionIcon.Hide()
		self.missionName.SetText("-")
		self.metadataText.SetText("-")
		self.levelValue.SetText("-")
		self.inventoryValue.SetText("0")
		self.progressText.SetText("0 / 0")
		self.progressPercent.SetText("0 %")
		self.progressBar.SetValue(0, 1)
		self.missionGiftText.SetText("-")
		self.rewardDetailText.SetText("-")
		self.intervalText.SetText("")
		if self.completedAll:
			self.statusText.SetText(_Text("BIO_COMPLETED", u"Dokončeno"))
			self.statusText.SetPackedFontColor(GOLD_COLOR)
		else:
			self.statusText.SetText(localeInfo.BIO_DONT_HAVE_MISSION)
			self.statusText.SetPackedFontColor(MUTED_COLOR)
		self._SetBoostersVisible(False)
		self._SetNormalDetailVisibility()
		self.submitButton.Hide()
		self._SetReminderVisible(False)
		if (self.completedAll and self.detailSelectionExplicit
				and 0 < self.detailIndex < len(bio_data)):
			self._ShowPreview(self.detailIndex, True)
		else:
			self.detailIndex = 0
			self.detailSelectionExplicit = False
		self._RefreshRegistry()
		self._StopReminderLoop()

	def GiveMission(self):
		if self.bioLevel == 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.BIO_CANNOT_ASSIGNMENT)
			return
		net.SendChatPacket("/bio mission %d %d" % (
			self.mode == "mission" and self.checkBoxElixirPercent.IsDown(),
			self.mode == "mission" and self.checkBoxElixirTime.IsDown(),
		))

	def ClickGift(self, index):
		net.SendChatPacket("/bio gift %d" % index)

	def OnUpdate(self):
		if self.needUpdate:
			return True
		showActiveStatus = self.detailIndex == self.bioLevel
		if self.bioTime == 0:
			if showActiveStatus:
				self.statusText.SetText(_Text("BIO_READY_SHORT", u"Připraveno"))
				self.statusText.SetPackedFontColor(RUBY_COLOR)
			self.needUpdate = True
			return True

		remaining = self.bioTime - app.GetGlobalTimeStamp()
		if remaining <= 0:
			if showActiveStatus:
				self.statusText.SetText(_Text("BIO_READY_SHORT", u"Připraveno"))
				self.statusText.SetPackedFontColor(RUBY_COLOR)
			self._NotifyReadyOnce()
			self.needUpdate = True
			return True

		text = "%02d:%02d:%02d" % (
			osfInfo.minutetohour(remaining),
			osfInfo.minutetominute(remaining),
			osfInfo.minutetosecond(remaining),
		)
		if showActiveStatus:
			self.statusText.SetText(_Text("BIO_COOLDOWN_IN", u"za %s") % text)
			self.statusText.SetPackedFontColor(MUTED_COLOR)
		return False

	def Open(self):
		self.Show()
		self.SetCenterPosition()
		self.SetTop()

	def Close(self):
		self.Hide()
		if self.checkBoxCall.IsDown() and self.cooldownWasPending and not self.readyNotificationSent:
			self._StartReminderLoop()

	def OnMouseWheel(self, delta):
		if delta > 0:
			self.registryScroll.OnUp()
			return True
		if delta < 0:
			self.registryScroll.OnDown()
			return True
		return False

	def OnPressEscapeKey(self):
		self.Close()
		return True
