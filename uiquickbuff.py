import time

import app
import chat
import chr
import item
import mouseModule
import net
import player
import ui
import uiScriptLocale
import uiToolTip
import wndMgr

import quickbuffcatalog
import quickbuffmodel
import quickbuffruntime
import servergamedata


PUBLIC_PATH = "d:/ymir work/ui/public/"
ACTION_PATH = PUBLIC_PATH + "crimson/controls/actions/"
SETTINGS_PATH = "d:/ymir work/ui/game/crimson_ember/gameoption/"
SLOT_PATH = PUBLIC_PATH + "Slot_Base.sub"
TEXT_COLOR = 0xffe4dacb
MUTED_COLOR = 0xff9f968c
GOLD_COLOR = 0xffffdc63
ACTIVE_COLOR = 0xff63e86d
SLOT_COLUMNS = 8
SLOT_COUNT = quickbuffmodel.MAX_SELECTED_COUNT
SLOT_STEP_X = 45
SLOT_STEP_Y = 50

# The server uses one affect per cooked-fish family; the families and affect
# types are the server fishing catalog (servergamedata.COOKED_FISH_BUFFS).
def _CookedFishAffects():
	affects = {}
	for affect, ordinary, improved, apply in servergamedata.COOKED_FISH_BUFFS:
		affects[ordinary] = affect
		affects[improved] = affect
	return affects


ACTIVE_AFFECT_BY_VNUM = _CookedFishAffects()
ACTIVE_AFFECT_BY_VNUM.update({
	71027: chr.AFFECT_DRAGON_GOD_1,
	71028: chr.AFFECT_DRAGON_GOD_2,
	71029: chr.AFFECT_DRAGON_GOD_3,
	71030: chr.AFFECT_DRAGON_GOD_4,
	71044: chr.AFFECT_CRITICAL,
	71045: chr.AFFECT_PENETRATE,
})


def _Locale(key, fallback):
	return getattr(uiScriptLocale, key, fallback)


def _Text(parent, x, y, value="", color=TEXT_COLOR, center=False):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	line.AddFlag("not_pick")
	if center:
		line.SetHorizontalAlignCenter()
	line.SetPackedFontColor(color)
	line.SetText(value)
	line.Show()
	return line


def _Button(parent, x, y, label, callback, width="middle", radio=False):
	button = ui.RadioButton() if radio else ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	if radio:
		button.SetUpVisual(ACTION_PATH + "%s_normal.png" % width)
		button.SetOverVisual(ACTION_PATH + "%s_hover.png" % width)
		button.SetDownVisual(ACTION_PATH + "%s_pressed.png" % width)
	else:
		button.SetUpVisual(PUBLIC_PATH + "%s_button_01.sub" % width)
		button.SetOverVisual(PUBLIC_PATH + "%s_button_02.sub" % width)
		button.SetDownVisual(PUBLIC_PATH + "%s_button_03.sub" % width)
	button.SetText(label)
	button.SetEvent(callback)
	button.Show()
	return button


def _Toggle(parent, x, y, on_event, off_event):
	button = ui.ToggleButton()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual(SETTINGS_PATH + "checkbox_unselected.tga")
	button.SetOverVisual(SETTINGS_PATH + "checkbox_hover.tga")
	button.SetDownVisual(SETTINGS_PATH + "checkbox_selected.tga")
	button.SetToggleDownEvent(on_event)
	button.SetToggleUpEvent(off_event)
	button.Show()
	return button


class QuickBuffWindow(ui.BoardWithTitleBar):
	WIDTH = 408
	HEIGHT = 445

	def __init__(self, system):
		ui.BoardWithTitleBar.__init__(self)
		self.system = system
		self.children = []
		self.checkboxes = []
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName(_Locale("QUICK_BUFF_TITLE", "Rychlá aktivace"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()
		self._Build()
		self.Hide()

	def _Own(self, child):
		self.children.append(child)
		return child

	def _Build(self):
		self._Own(_Text(self, 20, 30, _Locale("QUICK_BUFF_DRAG_HINT", "Přetáhni předměty z inventáře a kliknutím je vyber."), MUTED_COLOR))
		self._Own(_Text(self, 20, 52, _Locale("QUICK_BUFF_PROFILE", "PROFIL"), GOLD_COLOR))
		self.profilePvm = self._Own(_Button(self, 87, 50, "PVM", ui.__mem_func__(self._SelectPvm), "small", True))
		self.profilePvp = self._Own(_Button(self, 172, 50, "PVP", ui.__mem_func__(self._SelectPvp), "small", True))
		self.selectionCount = self._Own(_Text(self, 340, 53, "", TEXT_COLOR, True))
		self._Own(_Text(self, 20, 88, _Locale("QUICK_BUFF_ITEMS", "PŘEDMĚTY K AKTIVACI"), GOLD_COLOR))

		self.gridBackground = ui.Bar()
		self.gridBackground.SetParent(self)
		self.gridBackground.SetPosition(18, 101)
		self.gridBackground.SetSize(372, 252)
		self.gridBackground.SetColor(0x990b0807)
		self.gridBackground.Show()
		self._Own(self.gridBackground)
		for x, y, width, height in ((18, 101, 372, 1), (18, 352, 372, 1),
			(18, 101, 1, 252), (389, 101, 1, 252), (20, 390, 368, 1)):
			line = ui.Bar()
			line.SetParent(self)
			line.SetPosition(x, y)
			line.SetSize(width, height)
			line.SetColor(0xff57432c)
			line.AddFlag("not_pick")
			line.Show()
			self._Own(line)

		self.grid = ui.GridSlotWindow()
		self.grid.SetParent(self.gridBackground)
		self.grid.SetPosition(8, 4)
		self.grid.SetSize(358, 248)
		self.grid.ArrangeSlot(0, SLOT_COLUMNS, SLOT_COUNT // SLOT_COLUMNS,
			32, 32, SLOT_STEP_X - 32, SLOT_STEP_Y - 32)
		self.grid.SetSlotBaseImage(SLOT_PATH, 1.0, 1.0, 1.0, 1.0)
		self.grid.SetSelectEmptySlotEvent(ui.__mem_func__(self._SelectSlot))
		self.grid.SetSelectItemSlotEvent(ui.__mem_func__(self._SelectSlot))
		self.grid.SetUnselectItemSlotEvent(ui.__mem_func__(self._RemoveSlot))
		self.grid.SetOverInItemEvent(ui.__mem_func__(self._OverInItem))
		self.grid.SetOverOutItemEvent(ui.__mem_func__(self._OverOutItem))
		self.grid.Show()
		self._Own(self.grid)
		for index in range(SLOT_COUNT):
			check = _Toggle(
				self.grid, (index % SLOT_COLUMNS) * SLOT_STEP_X + 9,
				(index // SLOT_COLUMNS) * SLOT_STEP_Y + 33,
				lambda index=index: self._SetSlotEnabled(index, True),
				lambda index=index: self._SetSlotEnabled(index, False),
			)
			self.checkboxes.append(check)

		self.autoVip = self._Own(_Toggle(self, 76, 361,
			ui.__mem_func__(self._EnableAutoVip),
			ui.__mem_func__(self._DisableAutoVip)))
		self._Own(_Text(self, 20, 362, "Auto VIP"))
		self.statusText = self._Own(_Text(self, 310, 362, "", MUTED_COLOR, True))
		self.activateButton = self._Own(_Button(self, 20, 399,
			_Locale("QUICK_BUFF_ACTIVATE", "Aktivovat buffy"),
			ui.__mem_func__(self.system.Activate), "xlarge"))
		self.clearButton = self._Own(_Button(self, 310, 399, _Locale("QUICK_BUFF_CLEAR", "Vymazat"),
			ui.__mem_func__(self._ClearProfile), "middle"))

	def _SelectPvm(self):
		self._SelectProfile("pvm")

	def _SelectPvp(self):
		self._SelectProfile("pvp")

	def _SelectProfile(self, profile):
		if self.system.model.SetProfile(profile):
			self.system.controller.OnProfileChanged()
			self.system.model.Save()
		self.Refresh()

	def _SetAutoVip(self, enabled):
		self.system.model.SetAutoEnabled(enabled)
		self.system.model.Save()
		self.RefreshStatus()

	def _EnableAutoVip(self):
		self._SetAutoVip(True)

	def _DisableAutoVip(self):
		self._SetAutoVip(False)

	def _SetSlotEnabled(self, index, enabled):
		if self.system.model.SetSlotEnabled(index, enabled):
			self.system.controller.OnProfileChanged()
			self.system.model.Save()
		self.RefreshSlots()

	def _AttachedInventoryVnum(self):
		mouse = mouseModule.mouseController
		if not mouse.isAttached():
			return 0
		allowed_types = [player.SLOT_TYPE_INVENTORY]
		for name in (
			"SLOT_TYPE_SKILL_BOOK_INVENTORY", "SLOT_TYPE_UPGRADE_ITEMS_INVENTORY",
			"SLOT_TYPE_STONE_INVENTORY", "SLOT_TYPE_GIFT_BOX_INVENTORY",
			"SLOT_TYPE_SWITCH_INVENTORY", "SLOT_TYPE_COSTUME_INVENTORY",
			"SLOT_TYPE_CONSUMABLE_INVENTORY",
		):
			value = getattr(player, name, None)
			if value is not None:
				allowed_types.append(value)
		if mouse.GetAttachedType() not in allowed_types:
			return 0
		vnum = mouse.GetAttachedItemIndex()
		if vnum not in quickbuffcatalog.ALLOWED_VNUMS:
			return 0
		if self.system.scanner.Find(vnum) is None:
			return 0
		if self.system.policy.Describe(vnum, self.system.scanner.Find(vnum)) is None:
			return 0
		return vnum

	def _SelectSlot(self, index):
		vnum = self._AttachedInventoryVnum()
		if not vnum:
			if mouseModule.mouseController.isAttached():
				chat.AppendChat(chat.CHAT_TYPE_INFO,
					_Locale("QUICK_BUFF_RESTRICTED", "Sem lze vložit jen ryby, elixíry, kritický a pronikavý útok a předměty dračího boha."))
			return
		if self.system.model.SetSlot(index, vnum):
			self.system.controller.OnProfileChanged()
			self.system.model.Save()
		self.RefreshSlots()
		mouseModule.mouseController.DeattachObject()

	def _RemoveSlot(self, index):
		if self.system.model.RemoveSlot(index):
			self.system.controller.OnProfileChanged()
			self.system.model.Save()
		self.RefreshSlots()

	def _ClearProfile(self):
		if self.system.model.ClearProfile():
			self.system.controller.OnProfileChanged()
			self.system.model.Save()
		self.RefreshSlots()

	def _OverInItem(self, index):
		slots = self.system.model.Slots()
		if 0 <= index < len(slots) and slots[index]:
			self.tooltipItem.SetItemToolTip(slots[index])

	def _OverOutItem(self):
		self.tooltipItem.HideToolTip()

	def RefreshSlots(self):
		slots = self.system.model.Slots()
		enabled = self.system.model.EnabledSlots()
		for index, vnum in enumerate(slots):
			if vnum:
				self.grid.SetItemSlot(index, vnum)
				self.checkboxes[index].Show()
				if enabled[index]:
					self.checkboxes[index].Down()
				else:
					self.checkboxes[index].SetUp()
			else:
				self.grid.ClearSlot(index)
				self.checkboxes[index].Hide()
		self.grid.RefreshSlot()
		self.selectionCount.SetText(_Locale("QUICK_BUFF_SELECTED_COUNT", "%d / %d vybráno") %
			(len(self.system.model.ExecutionVnums()), SLOT_COUNT))
		if self.system.model.active_profile == "pvm":
			self.profilePvm.Down()
			self.profilePvp.SetUp()
		else:
			self.profilePvp.Down()
			self.profilePvm.SetUp()

	def RefreshStatus(self):
		if not self.system.model.auto_enabled:
			label, color = _Locale("QUICK_BUFF_AUTO_OFF", "Auto VIP je vypnuté"), MUTED_COLOR
		elif not self.system.controller.vip_active:
			label, color = _Locale("QUICK_BUFF_AUTO_WAITING", "Auto VIP čeká na nasazené VIP"), GOLD_COLOR
		else:
			label, color = _Locale("QUICK_BUFF_AUTO_ACTIVE", "Auto VIP je aktivní"), ACTIVE_COLOR
		self.statusText.SetPackedFontColor(color)
		self.statusText.SetText(label)

	def Refresh(self):
		if self.system.model.auto_enabled:
			self.autoVip.Down()
		else:
			self.autoVip.SetUp()
		self.RefreshSlots()
		self.RefreshStatus()

	def _RestorePosition(self):
		position = self.system.model.window_position
		if position is None:
			self.SetCenterPosition()
			return
		x = max(0, min(int(position[0]), wndMgr.GetScreenWidth() - self.WIDTH))
		y = max(0, min(int(position[1]), wndMgr.GetScreenHeight() - self.HEIGHT))
		self.SetPosition(x, y)

	def Open(self):
		if not self.IsShow():
			self._RestorePosition()
			self.Show()
		self.Refresh()
		self.SetTop()

	def Close(self):
		if self.system and self.system.model.path:
			self.system.model.SetWindowPosition(self.GetGlobalPosition())
			self.system.model.Save(force=True)
		self._OverOutItem()
		self.Hide()

	def Destroy(self):
		self.Close()
		self.tooltipItem = None
		self.children = []
		self.checkboxes = []
		self.system = None

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		return self.OnPressEscapeKey()


class QuickBuffSystem(object):
	def __init__(self):
		self.affectShower = None
		self.model = quickbuffmodel.QuickBuffModel()
		self.policy = quickbuffruntime.QuickBuffItemPolicy(
			item, player, quickbuffcatalog.ALLOWED_VNUMS
		)
		self.scanner = quickbuffruntime.InventoryScanner(
			item, player, quickbuffcatalog.DEFAULT_CATALOG_VNUMS,
			quickbuffcatalog.EXCLUDED_CATALOG_VNUMS,
		)
		self.controller = quickbuffruntime.QuickBuffController(
			self.model, self.policy, self.scanner, net, player, now_fn=time.time,
			active_effect_remaining_fn=self._ActiveEffectRemaining,
		)
		self.window = QuickBuffWindow(self)
		self._EnsureIdentity()

	def SetAffectShower(self, shower):
		self.affectShower = shower

	def _ActiveEffectRemaining(self, vnum):
		if not self.affectShower:
			return 0
		affect = ACTIVE_AFFECT_BY_VNUM.get(vnum)
		if affect is None:
			return 0
		image = self.affectShower.affectImageDict.get(affect)
		if image is None:
			return 0
		return max(0, image.GetEndTime() - app.GetGlobalTimeStamp())

	def _PlayerName(self):
		for functionName in ("GetName", "GetMainCharacterName"):
			function = getattr(player, functionName, None)
			if callable(function):
				try:
					name = function()
				except (RuntimeError, TypeError, ValueError):
					continue
				if name:
					return str(name)
		return ""

	def _EnsureIdentity(self):
		name = self._PlayerName()
		if name:
			self.model.SetIdentity(name)
			if self.model.RetainVnums(quickbuffcatalog.ALLOWED_VNUMS):
				self.controller.OnProfileChanged()
				self.model.Save(force=True)
		return bool(self.model.path)

	def Activate(self):
		self._EnsureIdentity()
		if not self.controller.QueueManual():
			chat.AppendChat(chat.CHAT_TYPE_INFO,
				_Locale("QUICK_BUFF_NO_ITEMS", "Není dostupný žádný nastavený buff."))

	def OpenSettings(self):
		self._EnsureIdentity()
		self.window.Open()

	def OnVipStatus(self, active):
		self.controller.OnVipStatus(active)
		if self.window and self.window.IsShow():
			self.window.RefreshStatus()

	def Tick(self):
		self._EnsureIdentity()
		self.controller.Tick()
		if self.window and self.window.IsShow():
			self.window.RefreshStatus()

	def Destroy(self):
		self.controller.Destroy()
		if self.window:
			self.window.Destroy()
		self.window = None
		self.controller = None
		self.scanner = None
		self.policy = None
		self.model = None
