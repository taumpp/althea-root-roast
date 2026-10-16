import app
from mountexpeditiontexts import ExpeditionTexts
import chat
import item
import mountcorebonus
import mouseModule
import net
import nonplayer
import player
import ui
import uiScriptLocale
import uitooltip
import WikiRenderTarget
import uimountk1 as K1
from uimountfeed import MountFeedWindow, InventoryStack, IsInventorySource

from uimountmodel import MountSystemViewModel, ELEMENT_NAMES, ELEMENT_ASSETS, GEAR_BONUSES
from uimountwidgets import (
	ASSET_ROOT,
	CreateImage,
	DynamicScrollViewport,
	EquipmentSlot,
	SemanticButton,
)


MOUNT_SKIN_WEAR_CELL = 21
GEAR_SLOT_COUNT = 5
MOUNT_LAYOUT = {
	"section": (16, 41, 260, 28),
	"main_group": (16, 73, 260, 272),
	"render_target": (19, 76, 254, 266),
	"equipment_section": (16, 353, 468, 28),
	"equipment_backing": (16, 385, 468, 58),
	"progress_section": (284, 41, 200, 28),
	"mount_progress": (284, 73, 200, 272),
	"feed_action": (165, 460, 170, 24),
}
SLOT_LAYOUT = (
	("skin", 298, 86, 32, 32),
	("saddle", 48, 393, 32, 32),
	("horseshoes", 141, 393, 32, 32),
	("bridle", 234, 393, 32, 32),
	("armor", 327, 393, 32, 32),
	("prismatic", 420, 393, 32, 32),
)
SLOT_HINTS = {
	"saddle": "slot_hint_saddle_32x32.png",
	"armor": "slot_hint_armor_32x32.png",
	"skin": "slot_hint_skin_32x32.png",
	"horseshoes": "slot_hint_horseshoes_32x32.png",
	"bridle": "slot_hint_bridle_32x32.png",
	"prismatic": "slot_hint_prismatic_32x32.png",
}
GEAR_LAYOUT_TO_SUBTYPE = {
	"saddle": 0,
	"horseshoes": 1,
	"bridle": 2,
	"armor": 3,
	"prismatic": 4,
}


def _Locale(key, fallback):
	return getattr(uiScriptLocale, key, fallback)


class MountSystemWindow(ui.BoardWithTitleBar):
	WINDOW_WIDTH = 500
	WINDOW_HEIGHT = 500
	SWITCH_WIDTH = 36
	SWITCH_HEIGHT = 36
	ELEMENT_SCROLLBAR_X = 470

	def __init__(self):
		# Window.__init__ dispatches to our Hide before building the board.
		self.feedWindow = None
		self.tooltipItem = None
		self.infoTooltip = None
		self.renderIndex = None
		self.renderView = None
		self.taskRows = []
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.AddFlag("ignore_size")
		self.AddFlag("not_pick")
		self.SetSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()

		self.expeditionTexts = ExpeditionTexts()
		self.model = MountSystemViewModel(self.expeditionTexts.coreEquipmentText)
		self.capability = False
		self.activePage = "mount"
		self.requestSequence = 0
		self.pendingSequence = None
		self.snapshotPending = False
		self.equipmentRefreshSignature = None
		self.infoTooltip = uitooltip.ToolTip(260)
		self.slotRows = {}
		self.elementRows = []
		self.displayedElementId = None
		self.body = ui.Bar()
		self.body.SetParent(self)
		self.body.SetPosition(6, 31)
		self.body.SetSize(488, 463)
		self.body.SetColor(0xff090807)
		self.body.AddFlag("not_pick")
		self.body.Show()

		self.mountPage = self.__CreatePage()
		self.elementsPage = self.__CreatePage()
		self.__BuildMountPage()
		self.__BuildElementsPage()
		self.mountSwitch = self.__CreateSwitch(
			"mount", ui.__mem_func__(self.__ShowMountPage)
		)
		self.elementsSwitch = self.__CreateSwitch(
			"elements", ui.__mem_func__(self.__ShowElementsPage)
		)
		self.loadingText = K1.Text(
			self, self.WINDOW_WIDTH // 2, 38,
			_Locale("MOUNT_SYSTEM_LOADING", u"Načítání…"),
			size=11, color=K1.MUTED, align="center",
		)
		self.loadingText.Hide()
		self.__ShowPage("mount")
		self.__SetInteractive(False)
		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def __CreatePage(self):
		page = ui.Window()
		page.SetParent(self)
		page.SetPosition(0, 23)
		page.SetSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT - 23)
		page.Show()
		return page

	def __PlaceImage(self, parent, layoutName, filename):
		x, y, unusedWidth, unusedHeight = MOUNT_LAYOUT[layoutName]
		return CreateImage(parent, x, y - 23, filename)

	def __Label(self, parent, x, baseline, *args, **kwargs):
		return K1.Text(parent, x, baseline - 23, *args, **kwargs)

	def __BuildMountPage(self):
		self.mountSection = K1.Section(self.mountPage, 16, 18, 260, u"Tvůj mount")
		self.mainPanel = self.__PlaceImage(
			self.mountPage, "main_group", "k1/surface_260x272.png"
		)
		self.equipmentBacking = self.__PlaceImage(
			self.mountPage, "equipment_backing", "k1/surface_468x58.png"
		)
		self.previewBackdrop = K1.Image(self.mountPage, 19, 53, "preview_254x266.png")
		K1.Section(self.mountPage, 16, 330, 468, u"Výbava mounta")
		self.progressPanel = self.__PlaceImage(self.mountPage, "mount_progress", "k1/surface_200x272.png")

		self.renderView = ui.WikiRenderTargetUi()
		self.renderView.SetParent(self.mountPage)
		self.renderView.SetPosition(19, 53)
		self.renderView.SetSize(254, 266)
		self.renderView.SetClippingMaskWindow(self.mainPanel)
		self.renderView.Hide()
		self.noMountText = self.__Label(
			self.mountPage, 146, 218, self.model.mount_empty_text,
			color=K1.MUTED, align="center",
		)

		self.equipmentSlots = {}
		for name, x, y, width, height in SLOT_LAYOUT:
			slot = EquipmentSlot(
				self.mountPage, x, y - 23, width, height, SLOT_HINTS[name]
			)
			wearCell = (
				MOUNT_SKIN_WEAR_CELL if name == "skin"
				else 46 + GEAR_LAYOUT_TO_SUBTYPE[name]
			)
			slot.SetSelectEmptySlotEvent(
				lambda unusedSlot=0, cell=wearCell: self.__DropToWearCell(cell)
			)
			slot.SetSelectItemSlotEvent(
				lambda unusedSlot=0, cell=wearCell: self.__PickWearCell(cell)
			)
			slot.SetUseSlotEvent(
				lambda unusedSlot=0, cell=wearCell: self.__UseWearCell(cell)
			)
			slot.SetUnselectItemSlotEvent(
				lambda unusedSlot=0, cell=wearCell: self.__UseWearCell(cell)
			)
			slot.SetOverInItemEvent(
				lambda unusedSlot=0, key=name: self.__OverInEquipment(key)
			)
			slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutEquipment))
			self.equipmentSlots[name] = slot

		self.progressSection = K1.Section(self.mountPage, 284, 18, 200, u"Duše mounta")
		self.__Label(self.mountPage, 342, 106, u"Pečeť / vzhled", color=K1.GOLD, bold=True)
		for x, label in ((64, u"Sedlo · Lv. 5"), (157, u"Podkovy · Lv. 10"), (250, u"Uzda · Lv. 15"), (343, u"Zbroj · Lv. 20"), (436, u"Jádro · Lv. 25")):
			self.__Label(self.mountPage, x, 437, label, size=11, align="center")
		for y in (132, 243):
			K1.Image(self.mountPage, 298, y - 23, "divider_172x1.png")
		K1.Image(self.mountPage, 298, 123, "level_48x64.png")
		self.__Label(self.mountPage, 315, 166, u"Lv.", size=11, color=K1.GOLD, align="center")
		self.soulLevel = self.__Label(self.mountPage, 315, 188, u"—", size=18, color=K1.GOLD, align="center", bold=True)
		self.__Label(self.mountPage, 356, 155, u"Zkušenosti", color=K1.GOLD, bold=True)
		self.soulPercent = self.__Label(self.mountPage, 470, 209, u"—", size=17, color=K1.BLUE, align="right", bold=True)
		self.soulSegments = []
		for index in range(4):
			segment = K1.SoulOrb(
				self.mountPage, 356 + index * 25, 143,
				index + 1,
			)
			self.soulSegments.append(segment)
		self.soulExp = self.__Label(self.mountPage, 298, 229, u"—", color=K1.BLUE)
		self.__Label(self.mountPage, 298, 255, u"Rychlost mounta", size=11, color=K1.GOLD)
		self.soulSpeed = self.__Label(self.mountPage, 470, 255, u"—", color=K1.GREEN, align="right")
		self.__Label(self.mountPage, 298, 276, u"2 % / úroveň · při jízdě", size=11, color=K1.MUTED)
		self.__Label(self.mountPage, 298, 302, u"Další výbava", color=K1.GOLD)
		self.unlockRows = []
		for y in (324,):
			self.unlockRows.append((
				self.__Label(self.mountPage, 298, y, u"", color=K1.MUTED),
				self.__Label(self.mountPage, 470, y, u"—", color=K1.MUTED, align="right"),
			))
		feedX, feedY, unusedWidth, unusedHeight = MOUNT_LAYOUT["feed_action"]
		self.feedButton = SemanticButton(
			self.mountPage, feedX, feedY - 23,
			_Locale("MOUNT_SYSTEM_FEED", u"Nakrmit"),
			ui.__mem_func__(self.__OpenFeed),
		)

	def __BuildElementsPage(self):
		self.elementsSection = K1.Section(self.elementsPage, 16, 18, 218, u"Živly")
		self.detailSection = K1.Section(self.elementsPage, 242, 18, 242, u"Vyber živel")
		for index in range(6):
			row = K1.ElementRow(self.elementsPage, lambda index=index: self.__ToggleElement(index))
			row.SetPosition(16, 50 + index * 58)
			row.SetData({"element_id": index, "name": ELEMENT_NAMES[index], "icon": ELEMENT_ASSETS[index], "state": "normal", "bonus_text": u"—", "opened": False})
			self.elementRows.append(row)
		self.coreInfo = ui.Window()
		self.coreInfo.SetParent(self.elementsPage)
		self.coreInfo.SetPosition(16, 404)
		self.coreInfo.SetSize(218, 57)
		self.coreInfo.SAFE_SetOverInEvent(self.__OverInCore)
		self.coreInfo.SAFE_SetOverOutEvent(self.__HideInfo)
		self.coreInfo.Show()
		K1.Surface(self.coreInfo, 0, 0, 218, 57)
		CreateImage(self.elementsPage, 25, 416, "slot_hint_prismatic_32x32.png")
		self.__Label(self.elementsPage, 68, 447, u"Prizmatické jádro", color=K1.GOLD, bold=True)
		self.overallCount = self.__Label(self.elementsPage, 68, 469, u"—", size=11, color=K1.MUTED)
		K1.Surface(self.elementsPage, 242, 50, 242, 411)
		self.detailBackdrop = K1.Image(self.elementsPage, 245, 53, "detail_fire_236x111.png")
		self.detailIcon = CreateImage(self.elementsPage, 257, 77, "element_fire_24.png")
		self.detailBonusTitle = self.__Label(self.elementsPage, 293, 111, u"Bonus větve", color=K1.GOLD)
		self.detailBonus = self.__Label(self.elementsPage, 467, 155, u"—", size=23, color=K1.BLUE, align="right", bold=True)
		self.detailProgress = K1.Progress(self.elementsPage, 258, 149, 210)
		self.tasksIcon = K1.Image(self.elementsPage, 258, 176, "glyph_tasks_24.png")
		self.tasksHeading = self.__Label(self.elementsPage, 290, 215, u"ÚKOLY VĚTVE", color=K1.GOLD, bold=True)
		self.detailHint = self.__Label(self.elementsPage, 363, 294, u"Vyber živel vlevo", color=K1.MUTED, align="center")
		self.taskViewport = DynamicScrollViewport(
			self.elementsPage, 258, 205, 210, 247,
			scrollParent=self.elementsPage,
			scrollPosition=(self.ELEMENT_SCROLLBAR_X, 207), contentInset=0,
		)
		self.__ShowElementDetail(False)

	def __ShowElementDetail(self, visible):
		for widget in (self.detailBackdrop, self.detailIcon, self.detailBonusTitle, self.detailBonus, self.detailProgress, self.tasksIcon, self.tasksHeading, self.taskViewport):
			widget.Show() if visible else widget.Hide()
		if visible:
			self.detailHint.Hide()
		else:
			self.detailHint.Show()
			self.taskViewport.scroll.Hide()

	def __CreateSwitch(self, kind, event):
		glyph = "glyph_mount_20.png" if kind == "mount" else "glyph_elements_20.png"
		return K1.SideTab(self, glyph, event)

	def __SetSwitchSelected(self, button, kind, selected):
		button.SetSelected(selected)

	def __ShowMountPage(self):
		self.__ShowPage("mount")

	def __ShowElementsPage(self):
		self.__ShowPage("elements")

	def __ShowPage(self, page):
		if page != "mount" and self.feedWindow:
			self.feedWindow.Close()
		self.__HideInfo()
		self.__OverOutEquipment()
		for row in self.taskRows:
			row.HideToolTip()
		if page == "elements":
			self.activePage = "elements"
			self.mountPage.Hide()
			self.elementsPage.Show()
			self.SetTitleName(
				_Locale("MOUNT_SYSTEM_ELEMENTS_TITLE", u"Elementární výpravy")
			)
			self.__HideRenderTarget()
		else:
			self.activePage = "mount"
			self.elementsPage.Hide()
			self.mountPage.Show()
			self.SetTitleName(
				_Locale("MOUNT_SYSTEM_TITLE", u"Systém mounta")
			)
			self.__RefreshRenderTarget()
		self.mountSwitch.SetPosition(494, 107)
		self.elementsSwitch.SetPosition(494, 141)
		self.__SetSwitchSelected(
			self.mountSwitch, "mount", self.activePage == "mount"
		)
		self.__SetSwitchSelected(
			self.elementsSwitch, "elements", self.activePage == "elements"
		)

	def __SetInteractive(self, enabled):
		canMutate = bool(
			enabled and self.capability and self.model.revision >= 0
			and self.pendingSequence is None
			and not self.snapshotPending
			and self.__CanMutate()
		)
		if canMutate and self.model.soul["next_exp"] > 0:
			self.feedButton.Enable()
		else:
			self.feedButton.Disable()
		for row in self.taskRows:
			row.SetEnabled(canMutate)
		if self.feedWindow:
			self.feedWindow.RefreshControls()

	def SetCapability(self, enabled):
		self.capability = bool(enabled)
		if not self.capability:
			self.ResetRuntime()
		self.__SetInteractive(self.capability and self.model.revision >= 0)

	def ApplySnapshot(self, snapshot):
		previousNonce = self.model.session_nonce
		try:
			changed = self.model.apply_snapshot(snapshot)
		except (TypeError, ValueError) as error:
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Mount systém: %s" % error)
			return False
		if not changed:
			return False
		if self.feedWindow:
			if previousNonce != self.model.session_nonce:
				self.feedWindow.basket.stop()
				self.feedWindow.basket.clear()
			else:
				self.feedWindow.basket.snapshot(self.model.revision, self.model.session_nonce)
		if not self.feedWindow or not self.feedWindow.basket.busy:
			self.pendingSequence = None
		self.snapshotPending = False
		self.loadingText.Hide()
		self.__OverOutEquipment()
		self.__RefreshMountPage()
		self.__RefreshElementsPage()
		self.__SetInteractive(True)
		self.RefreshEquipment()
		if self.feedWindow:
			self.feedWindow.Refresh()
			self.__ConsumeCrystal()
		return True

	def RefreshEquipment(self):
		if not self.IsShow() or not self.__CanMutate():
			return
		wearCells = (MOUNT_SKIN_WEAR_CELL,) + tuple(range(46, 46 + GEAR_SLOT_COUNT))
		actual = tuple(player.GetItemIndex(self.__GlobalWearSlot(cell)) for cell in wearCells)
		snapshot = (self.model.skin_vnum,) + tuple(row["item_vnum"] for row in self.model.gear)
		if actual == snapshot:
			self.equipmentRefreshSignature = None
		elif actual != self.equipmentRefreshSignature:
			self.equipmentRefreshSignature = actual
			if not self.__RequestSnapshot():
				self.equipmentRefreshSignature = None

	def __RefreshMountPage(self):
		self.__RefreshSlots()
		self.__RefreshRenderTarget()
		soul = self.model.soul
		self.soulLevel.SetText(u"%d" % soul["level"])
		self.soulSpeed.SetText(u"+%d %%" % soul["speed_bonus_percent"])
		self.soulPercent.SetText(u"%d %%" % soul["percent"])
		self.soulExp.SetText(soul["exp_text"])
		for segment, fillRatio in zip(
			self.soulSegments, soul["segment_fill"]
		):
			segment.SetValue(fillRatio)
		locked = [row for row in self.model.gear if row["locked"]]
		label, value = self.unlockRows[0]
		if locked:
			row = locked[0]
			label.SetText(u"Jádro" if row["subtype"] == 4 else row["name"])
			value.SetText(row["unlock_text"].replace(u"Odemkne se na úrovni Duše ", u"Lv. "))
			K1.SetColor(value, K1.GOLD)
		else:
			label.SetText(u"Všech 5 slotů")
			value.SetText(u"Odemčeno")
			K1.SetColor(value, K1.GREEN)

	def __RefreshSlots(self):
		skinRow = {
			"item_vnum": self.model.skin_vnum,
			"item_id": 0,
			"locked": False,
			"empty": self.model.skin_vnum == 0,
		}
		self.equipmentSlots["skin"].SetRow(skinRow)
		self.slotRows["skin"] = skinRow
		for name, subtype in GEAR_LAYOUT_TO_SUBTYPE.items():
			row = self.model.gear[subtype]
			self.equipmentSlots[name].SetRow(row)
			self.slotRows[name] = row
		if self.model.gear and not self.model.gear[4]["empty"]:
			self.model.set_prismatic_equipped(True)

	def __RefreshElementsPage(self):
		self.__HideInfo()
		completed = len([
			row for row in self.model.elements if row["state"] == "completed"
		])
		self.overallCount.SetText(u"%d / 6 dokončených větví" % completed)
		oldPosition = self.taskViewport.scroll.GetPos()
		for row in self.taskRows:
			row.HideToolTip()
		self.taskViewport.Reset()
		self.taskRows = []
		selected = None
		for element in self.model.elements:
			elementId = element["element_id"]
			self.elementRows[elementId].SetData(element)
			if element["opened"]:
				selected = element
		if selected is None:
			self.detailSection.label.SetText(u"Vyber živel")
			self.detailHint.SetText(u"Vyber živel vlevo")
			self.__ShowElementDetail(False)
			self.displayedElementId = None
			return
		self.__ShowElementDetail(True)
		self.detailSection.label.SetText(selected["name"])
		self.detailIcon.LoadImage(ASSET_ROOT + selected["icon"])
		self.detailBackdrop.LoadImage(K1.K1_ROOT + "detail_%s_236x111.png" % K1.ELEMENT_KEYS[selected["element_id"]])
		self.detailBonus.SetText(selected["bonus_text"].lstrip("+"))
		self.detailProgress.SetValue(selected["bonus_basis_points"], 2000)
		for task in selected["tasks"]:
			taskId = task["task_id"]
			taskRow = K1.TaskRow(self.taskViewport.content, lambda taskId=taskId: self.__SubmitTask(taskId))
			taskRow.SetData(task, self.__TaskName(task), len(self.taskRows) + 1)
			taskRow.SetEnabled(self.capability and self.pendingSequence is None and self.model.revision >= 0)
			self.taskRows.append(taskRow)
		for index, row in enumerate(self.taskRows):
			self.taskViewport.AddRow(row, row.HEIGHT, gap=6 if index + 1 < len(self.taskRows) else 0)
		self.taskViewport.Finalize()
		if self.displayedElementId == selected["element_id"] and self.taskViewport.hasOverflow:
			self.taskViewport.scroll.SetPos(oldPosition)
		self.displayedElementId = selected["element_id"]
		if not self.taskRows:
			self.detailHint.SetText(u"Větev dokončena" if selected["state"] == "completed" else u"Žádné dostupné úkoly")
			self.detailHint.Show()

	def __ToggleElement(self, elementId):
		if self.model.open_element(elementId):
			self.__RefreshElementsPage()

	def __TaskName(self, task):
		label = self.expeditionTexts.Get(task)
		if label is not None:
			return label
		if task["event_kind"] == 3:
			try:
				item.SelectItem(task["target_vnum"])
				name = item.GetItemName()
			except (RuntimeError, TypeError):
				name = u"item #%d" % task["target_vnum"]
			return u"Odevzdej %s" % name
		try:
			name = nonplayer.GetMonsterName(task["target_vnum"])
		except (RuntimeError, TypeError):
			name = u"cíl #%d" % task["target_vnum"]
		return (u"Znič %s" if task["event_kind"] == 2 else u"Poraz %s") % name

	def __EnsureRenderTarget(self):
		if self.renderIndex is not None:
			return True
		try:
			self.renderIndex = int(WikiRenderTarget.GetFreeIndex(86, 1000000))
			if self.renderIndex < 1:
				raise RuntimeError("no free render target")
			self.renderView.SetRenderTarget(self.renderIndex)
			WikiRenderTarget.SetBackground(
				self.renderIndex,
				K1.K1_ROOT + "preview_254x266.png",
			)
			WikiRenderTarget.SetRotation(self.renderIndex, False)
			return True
		except (AttributeError, RuntimeError, TypeError, ValueError):
			self.__RemoveRenderTarget()
			return False

	def __RefreshRenderTarget(self):
		if self.activePage != "mount" or not self.IsShow() or not self.model.mount_race:
			self.__HideRenderTarget()
			self.noMountText.SetText(self.model.mount_empty_text)
			self.noMountText.Show()
			return
		if not self.__EnsureRenderTarget():
			self.noMountText.SetText(u"Náhled mounta není dostupný")
			self.noMountText.Show()
			return
		WikiRenderTarget.SetVisibility(self.renderIndex, False)
		WikiRenderTarget.SelectModel(self.renderIndex, self.model.mount_race)
		WikiRenderTarget.SetVisibility(self.renderIndex, True)
		self.renderView.Show()
		self.noMountText.Hide()

	def __HideRenderTarget(self):
		if self.renderIndex is not None:
			try:
				WikiRenderTarget.SetVisibility(self.renderIndex, False)
			except (AttributeError, RuntimeError):
				pass
		if self.renderView:
			self.renderView.Hide()

	def __RemoveRenderTarget(self):
		index = self.renderIndex
		self.renderIndex = None
		if self.renderView:
			self.renderView.Hide()
		if index is not None:
			try:
				WikiRenderTarget.Remove(index)
			except (AttributeError, RuntimeError):
				try:
					WikiRenderTarget.SetVisibility(index, False)
					WikiRenderTarget.ResetModel(index)
				except (AttributeError, RuntimeError):
					pass

	def __OverInEquipment(self, key):
		if not self.tooltipItem:
			return
		self.tooltipItem.HideToolTip()
		row = self.slotRows.get(key)
		if not row:
			return
		wearCell = MOUNT_SKIN_WEAR_CELL if key == "skin" else 46 + GEAR_LAYOUT_TO_SUBTYPE[key]
		globalSlot = self.__GlobalWearSlot(wearCell)
		if player.GetItemIndex(globalSlot):
			self.tooltipItem.SetInventoryItem(globalSlot, player.INVENTORY, appendShortcuts=False)
		elif key != "skin" and self.infoTooltip:
			self.infoTooltip.ClearToolTip()
			self.infoTooltip.AppendTextLine(row["name"])
			self.infoTooltip.AppendTextLine(row["unlock_text"])
			for bonus in GEAR_BONUSES[GEAR_LAYOUT_TO_SUBTYPE[key]]:
				self.infoTooltip.AppendTextLine(bonus)
			self.infoTooltip.ShowToolTip()

	def __OverOutEquipment(self):
		self.__HideInfo()
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __OverInCore(self):
		self.infoTooltip.ClearToolTip()
		self.infoTooltip.AppendTextLine(u"Prizmatické jádro")
		self.infoTooltip.AppendTextLine(self.model.prismatic["text"])
		self.infoTooltip.AppendTextLine(self.expeditionTexts.coreEquipmentText)
		for bonus in GEAR_BONUSES[4]:
			self.infoTooltip.AppendTextLine(bonus)
		self.infoTooltip.ShowToolTip()

	def __HideInfo(self):
		if self.infoTooltip is not None:
			self.infoTooltip.HideToolTip()

	def __CanMutate(self, feeding=False):
		return (self.capability and self.model.revision >= 0
			and self.pendingSequence is None and not self.snapshotPending
			and (feeding or not getattr(self, "feedWindow", None)
				or not (self.feedWindow.basket.active or self.feedWindow.basket.busy)))

	def __GlobalWearSlot(self, wearCell):
		return player.EQUIPMENT_SLOT_START + wearCell

	def __DropToWearCell(self, wearCell):
		if not self.__CanMutate() or not mouseModule.mouseController.isAttached():
			return
		if wearCell >= 46:
			row = self.model.gear[wearCell - 46]
			if row["locked"]:
				chat.AppendChat(chat.CHAT_TYPE_INFO, row["unlock_text"])
				return
		source = mouseModule.mouseController.GetAttachedSlotNumber()
		slotType = mouseModule.mouseController.GetAttachedType()
		if slotType != player.SLOT_TYPE_INVENTORY and not IsInventorySource(slotType, source):
			return
		sourceVnum = player.GetItemIndex(player.INVENTORY, source)
		if sourceVnum == mountcorebonus.SEAL_VNUM:
			if not IsInventorySource(slotType, source):
				return
			target = self.__GlobalWearSlot(wearCell)
			if wearCell == mountcorebonus.CORE_WEAR_CELL and mountcorebonus.CanUseSeal(
				sourceVnum, player.GetItemIndex(target)):
				net.SendItemUseToItemPacket(source, target)
				mouseModule.mouseController.DeattachObject()
			return
		if slotType != player.SLOT_TYPE_INVENTORY:
			return
		count = mouseModule.mouseController.GetAttachedItemCount()
		net.SendItemMovePacket(
			source, self.__GlobalWearSlot(wearCell), count
		)
		mouseModule.mouseController.DeattachObject()

	def __UseWearCell(self, wearCell):
		if not self.__CanMutate():
			return
		if mouseModule.mouseController.isAttached():
			self.__DropToWearCell(wearCell)
			return
		if wearCell >= 46 and self.model.gear[wearCell - 46]["locked"]:
			chat.AppendChat(
				chat.CHAT_TYPE_INFO,
				self.model.gear[wearCell - 46]["unlock_text"],
			)
			return
		globalSlot = self.__GlobalWearSlot(wearCell)
		if player.GetItemIndex(globalSlot):
			net.SendItemUsePacket(globalSlot)

	def __PickWearCell(self, wearCell):
		if not self.__CanMutate():
			return
		if wearCell >= 46 and self.model.gear[wearCell - 46]["locked"]:
			chat.AppendChat(
				chat.CHAT_TYPE_INFO,
				self.model.gear[wearCell - 46]["unlock_text"],
			)
			return
		if mouseModule.mouseController.isAttached():
			self.__DropToWearCell(wearCell)
			return
		vnum = player.GetItemIndex(self.__GlobalWearSlot(wearCell))
		if vnum:
			mouseModule.mouseController.AttachObject(
				self, player.SLOT_TYPE_INVENTORY,
				self.__GlobalWearSlot(wearCell), vnum, 1
			)

	def __AttachedInventory(self):
		if not mouseModule.mouseController.isAttached():
			chat.AppendChat(
				chat.CHAT_TYPE_INFO,
				u"Nejprve uchopte požadovaný item v inventáři.",
			)
			return None
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			return None
		return (
			mouseModule.mouseController.GetAttachedSlotNumber(),
			max(1, mouseModule.mouseController.GetAttachedItemCount()),
		)

	def __NextSequence(self):
		self.requestSequence += 1
		return self.requestSequence

	def __BeginMutation(self, sequence):
		self.pendingSequence = sequence
		self.__SetInteractive(False)

	def CanStartFeeding(self):
		return (self.IsShow() and self.activePage == "mount" and self.__CanMutate()
			and self.model.soul["next_exp"] > 0)

	def __OpenFeed(self):
		if not self.__CanMutate():
			return
		if self.model.soul["next_exp"] <= 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Duše mounta už dosáhla maximální úrovně.")
			return
		if not self.feedWindow:
			self.feedWindow = MountFeedWindow(self)
		self.feedWindow.Open()

	def StartFeeding(self):
		if not self.feedWindow or not self.feedWindow.IsShow() or not self.CanStartFeeding():
			return
		if not self.feedWindow.basket.validate(InventoryStack):
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Vybrané krystaly se změnily. Vlož je znovu.")
			self.feedWindow.basket.clear()
			self.feedWindow.Refresh()
			return
		if self.feedWindow.basket.start():
			self.__ConsumeCrystal()

	def __ConsumeCrystal(self):
		feed = self.feedWindow
		if not feed or not feed.basket.active or feed.basket.busy:
			return
		if not feed.IsShow() or not self.IsShow() or self.activePage != "mount":
			feed.basket.clear()
			return
		if not self.__CanMutate(feeding=True):
			return
		if self.model.soul["next_exp"] <= 0:
			feed.basket.stop()
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Duše mounta dosáhla maximální úrovně. Zbylé krystaly zůstaly v inventáři.")
			self.__SetInteractive(True)
			return
		if not feed.basket.validate(InventoryStack):
			feed.basket.stop()
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Krmení zastaveno: vybrané krystaly se změnily. Vlož je znovu.")
			self.__SetInteractive(True)
			return
		index, row = next((index, row) for index, row in enumerate(feed.basket.slots) if row)
		sequence = self.__NextSequence()
		if net.SendMountSystemConsumeCrystal(
			player.INVENTORY, row[0], row[2], self.model.revision,
			self.model.session_nonce, sequence,
		):
			feed.basket.sent(index, sequence, self.model.revision, self.model.session_nonce)
			feed.deadline = app.GetTime() + 20.0
			self.__BeginMutation(sequence)
		else:
			feed.basket.stop()
			chat.AppendChat(chat.CHAT_TYPE_INFO, u"Krmení se nepodařilo odeslat. Krystaly zůstaly v inventáři.")
			self.__SetInteractive(True)

	def FeedTimedOut(self):
		if not self.feedWindow or not self.feedWindow.basket.busy:
			return
		self.feedWindow.basket.stop()
		self.pendingSequence = None
		chat.AppendChat(chat.CHAT_TYPE_INFO, u"Potvrzení krmení nedorazilo. Obnovuji stav; zkontroluj zbývající krystaly.")
		self.__RequestSnapshot()

	def __SubmitTask(self, taskId):
		if not self.__CanMutate():
			return
		attached = self.__AttachedInventory()
		if not attached or self.pendingSequence is not None:
			return
		sequence = self.__NextSequence()
		if net.SendMountSystemSubmitTaskItem(
			taskId, player.INVENTORY, attached[0], attached[1],
			self.model.revision, self.model.session_nonce, sequence,
		):
			self.__BeginMutation(sequence)
			mouseModule.mouseController.DeattachObject()

	def HandleActionResult(self, sequence, revision, result):
		if self.feedWindow and self.feedWindow.basket.busy:
			basket = self.feedWindow.basket
			if not basket.acknowledge(int(sequence), int(revision), int(result)):
				return
			if int(result) != 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, u"Krmení bylo odmítnuto. Zkontroluj zbývající krystaly.")
			resolved = basket.snapshot(self.model.revision, self.model.session_nonce)
			if not basket.busy:
				self.pendingSequence = None
			self.feedWindow.Refresh()
			self.__SetInteractive(True)
			if resolved:
				self.__ConsumeCrystal()
			return
		if self.pendingSequence == int(sequence):
			self.pendingSequence = None
		self.__SetInteractive(True)
		self.RefreshEquipment()

	def HandleError(self, unusedCode, messageKey, refreshRequired):
		if self.feedWindow:
			self.feedWindow.basket.stop()
			self.feedWindow.Refresh()
		self.pendingSequence = None
		self.snapshotPending = False
		chat.AppendChat(
			chat.CHAT_TYPE_INFO,
			_Locale(messageKey, u"Akci mount systému se nepodařilo provést."),
		)
		self.__SetInteractive(True)
		if refreshRequired and self.capability:
			self.__RequestSnapshot()

	def __RequestSnapshot(self):
		self.requestSequence += 1
		self.snapshotPending = True
		self.loadingText.Show()
		self.__SetInteractive(False)
		if net.SendMountSystemOpen():
			return True
		self.snapshotPending = False
		self.loadingText.Hide()
		self.__SetInteractive(True)
		return False

	def Open(self):
		if not self.capability:
			return False
		if self.feedWindow:
			self.feedWindow.Close()
			self.feedWindow.basket.stop()
		self.Show()
		self.SetTop()
		self.__RequestSnapshot()
		self.__RefreshRenderTarget()
		return True

	def Close(self):
		self.Hide()

	def Hide(self):
		if getattr(self, "feedWindow", None):
			self.feedWindow.Close()
		for row in self.taskRows:
			row.HideToolTip()
		self.__HideRenderTarget()
		self.__OverOutEquipment()
		ui.BoardWithTitleBar.Hide(self)

	def OnUpdate(self):
		# The basket may be closed while a request is in flight. Its hidden
		# native window no longer receives OnUpdate, so the owner keeps the timer.
		feed = self.feedWindow
		if feed and feed.basket.busy and feed.deadline and app.GetTime() >= feed.deadline:
			feed.deadline = 0.0
			self.FeedTimedOut()

	def Toggle(self):
		if self.IsShow():
			self.Close()
			return True
		return self.Open()

	def ResetRuntime(self):
		self.Close()
		if self.feedWindow:
			self.feedWindow.basket.stop()
		self.__RemoveRenderTarget()
		self.model.clear()
		self.requestSequence = 0
		self.pendingSequence = None
		self.snapshotPending = False
		self.equipmentRefreshSignature = None
		self.loadingText.Hide()
		self.__SetInteractive(False)
		for slot in self.equipmentSlots.values():
			slot.SetRow(None)
		self.slotRows = {}
		self.taskViewport.Reset()
		self.taskRows = []
		self.displayedElementId = None
		self.__ShowElementDetail(False)
		self.detailSection.label.SetText(u"Vyber živel")
		self.detailHint.SetText(u"Vyber živel vlevo")
		self.soulLevel.SetText(u"—")
		self.soulPercent.SetText(u"—")
		self.soulExp.SetText(u"—")
		self.soulSpeed.SetText(u"—")
		for orb in self.soulSegments:
			orb.SetValue(0)
		for label, value in self.unlockRows:
			label.SetText(u"")
			value.SetText(u"—")
		for index, row in enumerate(self.elementRows):
			row.SetData({"element_id": index, "name": ELEMENT_NAMES[index], "icon": ELEMENT_ASSETS[index], "state": "normal", "bonus_text": u"—", "opened": False})
		self.overallCount.SetText(u"—")

	def Destroy(self):
		self.ResetRuntime()
		if self.feedWindow:
			self.feedWindow.Destroy()
			self.feedWindow = None
		self.mountPage = None
		self.elementsPage = None
		self.mountSwitch = None
		self.elementsSwitch = None
		self.renderView = None
		self.tooltipItem = None
		self.equipmentSlots = {}
		self.elementRows = []
		self.taskRows = []

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		return self.OnPressEscapeKey()

	def OnMouseWheel(self, delta):
		if self.activePage == "elements" and self.taskViewport.IsShow() and self.taskViewport.IsIn():
			self.taskViewport.OnMouseWheel(delta)
		return True
