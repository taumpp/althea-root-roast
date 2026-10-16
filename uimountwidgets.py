import app
import fontconfig
import item
import ui
import wndMgr
import uicrimsoncontrols
from uicrimsonember import SettingsScrollBar


ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/mount_system/"
SETTINGS_SECTION = ASSET_ROOT + "section_settings_358x28.png"
TEXT_COLOR = 0xffe4dacb
MUTED_COLOR = 0xff9f968c
VALUE_COLOR = 0xffffdc63
POSITIVE_COLOR = 0xff63e86d
BLUE_COLOR = 0xff58bfff


def _OwnChild(parent, child):
	if not hasattr(parent, "_mountOwnedChildren"):
		parent._mountOwnedChildren = []
	parent._mountOwnedChildren.append(child)
	return child


def CreateText(parent, x, y, text=u"", color=TEXT_COLOR, align="left",
				fontRole=None, outline=False, verticalAlign=None):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	if fontRole is not None:
		line.SetFontName(fontconfig.FontForRole(fontRole))
	if outline:
		line.SetOutline()
	if align == "center":
		line.SetHorizontalAlignCenter()
	elif align == "right":
		line.SetHorizontalAlignRight()
	if verticalAlign == "center":
		line.SetVerticalAlignCenter()
	line.AddFlag("not_pick")
	line.SetPackedFontColor(color)
	line.SetText(text)
	line.Show()
	return _OwnChild(parent, line)


def CreateImage(parent, x, y, filename, not_pick=True):
	image = ui.ImageBox()
	image.SetParent(parent)
	image.SetPosition(x, y)
	image.LoadImage(ASSET_ROOT + filename)
	if not_pick:
		image.AddFlag("not_pick")
	image.Show()
	return _OwnChild(parent, image)


def _ScrollMetrics(viewportHeight, contentHeight, tempSpace, minimumHeight):
	height = max(1, int(viewportHeight))
	contentHeight = max(0, int(contentHeight))
	usableHeight = max(1, height - max(0, int(tempSpace)))
	overflow = max(0, contentHeight - height)
	fullThumbScale = float(usableHeight) / float(height)
	if not overflow:
		return (0, fullThumbScale)
	minimumScale = min(
		fullThumbScale,
		float(max(1, int(minimumHeight))) / float(height),
	)
	contentScale = float(usableHeight) / float(max(height, contentHeight))
	return (overflow, max(minimumScale, min(fullThumbScale, contentScale)))


def _TaskPanelHeight(taskCount, rowHeight=35, bottomPadding=4):
	return max(0, int(taskCount)) * int(rowHeight) + int(bottomPadding)


def CreateSettingsSection(parent, x, y, text):
	section = ui.ImageBox()
	section.SetParent(parent)
	section.SetPosition(x, y)
	section.LoadImage(SETTINGS_SECTION)
	section.AddFlag("not_pick")
	section.Show()
	_OwnChild(parent, section)
	section.label = CreateText(
		parent, x + 17, y + 14, text, TEXT_COLOR,
		fontRole=fontconfig.ROLE_SECTION, outline=True,
		verticalAlign="center",
	)
	return section


class SemanticButton(ui.Button):
	def __init__(self, parent, x, y, text, event=None):
		ui.Button.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		uicrimsoncontrols.ApplyVisuals(self, "170x24")
		self.SetText(text)
		if event:
			self.SetEvent(event)
		self.Show()


class CompactSemanticButton(ui.Button):
	WIDTH = 80
	HEIGHT = 24

	def __init__(self, parent, x, y, text, event=None):
		ui.Button.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(self.WIDTH, self.HEIGHT)
		uicrimsoncontrols.ApplyVisuals(self, "80x24")
		self.SetText(text)
		if event:
			self.SetEvent(event)
		self.Show()


class SideNavigationButton(ui.RadioButton):
	NORMAL = ASSET_ROOT + "switch_48x36_normal.png"
	HOVER = ASSET_ROOT + "switch_48x36_hover.png"
	PRESSED = ASSET_ROOT + "switch_48x36_pressed.png"
	ACTIVE = ASSET_ROOT + "switch_48x36_active.png"
	SELECTED = ASSET_ROOT + "switch_48x36_selected.png"
	DISABLED = ASSET_ROOT + "switch_48x36_disabled.png"

	def __init__(self, parent, glyph, event):
		ui.RadioButton.__init__(self)
		self.SetParent(parent)
		self.SetSize(48, 36)
		self.SetEvent(event)
		self.glyph = CreateImage(self, 18, 8, glyph)
		self.SetSelected(False)
		self.Enable()
		self.Show()

	def SetSelected(self, selected):
		if selected:
			self.SetUpVisual(self.ACTIVE)
			self.SetOverVisual(self.ACTIVE)
			self.SetDownVisual(self.SELECTED)
			self.Down()
		else:
			self.SetUpVisual(self.NORMAL)
			self.SetOverVisual(self.HOVER)
			self.SetDownVisual(self.PRESSED)
			self.SetUp()
		self.SetDisableVisual(self.DISABLED)


class MountProgressBar(ui.Window):
	PRESETS = {
		"overall": (
			268, 12, "progress_overall_track_268x12.png",
			"progress_overall_fill_260x4.png", 4, 4, 260,
		),
		"task": (
			285, 15, "progress_task_track_285x15.png",
			"progress_task_fill_279x9.png", 3, 3, 279,
		),
		"parent": (
			127, 12, "progress_parent_track_127x12.png",
			"progress_parent_fill_119x4.png", 4, 4, 119,
		),
	}

	def __init__(self, parent, x, y, role="task"):
		ui.Window.__init__(self)
		if role not in self.PRESETS:
			raise ValueError("unsupported progress role")
		width, height, trackName, fillName, fillX, fillY, innerWidth = self.PRESETS[role]
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.AddFlag("not_pick")
		self.track = CreateImage(self, 0, 0, trackName)
		self.fill = ui.ExpandedImageBox()
		self.fill.SetParent(self)
		self.fill.SetPosition(fillX, fillY)
		self.fill.LoadImage(ASSET_ROOT + fillName)
		self.fill.AddFlag("not_pick")
		self.fill.SetClippingMaskWindow(self)
		self.fill.Show()
		self.innerWidth = innerWidth
		self.SetValue(0, 1)
		self.Show()

	def SetValue(self, current, maximum):
		try:
			maximum = max(1, int(maximum))
			current = max(0, min(maximum, int(current)))
		except (TypeError, ValueError):
			current, maximum = 0, 1
		if current <= 0:
			self.fill.Hide()
			return
		self.fill.SetRenderingRect(
			0.0, 0.0, -1.0 + float(current) / float(maximum), 0.0
		)
		self.fill.Show()



class MountSoulOrb(ui.Window):
	SIZE = 19

	def __init__(self, parent, x, y, index):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(self.SIZE, self.SIZE)
		self.empty = CreateImage(
			self, 0, 0, "soul_orb_empty_%02d_19x19.png" % int(index)
		)
		self.fill = ui.ExpandedImageBox()
		self.fill.SetParent(self)
		self.fill.SetPosition(0, 0)
		self.fill.LoadImage(ASSET_ROOT + "soul_orb_full_19x19.png")
		self.fill.AddFlag("not_pick")
		self.fill.Hide()
		self.Show()

	def SetValue(self, ratio):
		try:
			ratio = max(0.0, min(1.0, float(ratio)))
		except (TypeError, ValueError):
			ratio = 0.0
		if ratio <= 0.0:
			self.fill.Hide()
			return
		self.fill.SetRenderingRect(0.0, -1.0 + ratio, 0.0, 0.0)
		self.fill.Show()


class EquipmentSlot(ui.Window):
	def __init__(self, parent, x, y, width=32, height=32, hintName=None):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		frame = "slot_wide_64x32.png" if width == 64 else "slot_item_32x32.png"
		self.frame = CreateImage(self, 0, 0, frame)
		self.hint = CreateImage(self, 0, 0, hintName) if hintName else None
		self.slot = ui.SlotWindow()
		self.slot.SetParent(self)
		self.slot.SetPosition(0, 0)
		self.slot.SetSize(width, height)
		self.slot.AppendSlot(0, 0, 0, width, height)
		self.slot.Show()
		# A low-strength native additive pass lifts the original metal highlights.
		# No resampling, new item identity, world-lighting change or alpha square.
		self.iconLight = ui.ExpandedImageBox()
		self.iconLight.SetParent(self)
		self.iconLight.SetPosition(0, 0)
		self.iconLight.AddFlag("not_pick")
		self.iconLight.Hide()
		self.lightEquipment = bool(hintName and "skin" not in hintName)
		self.lock = CreateImage(
			self, (width - 32) // 2, (height - 32) // 2, "glyph_lock_brass_32x32.png"
		)
		self.lock.Hide()
		self.row = None
		self.Show()

	def SetRow(self, row):
		self.row = row
		self.slot.ClearSlot(0)
		hasItem = bool(row and row.get("item_vnum"))
		if hasItem:
			self.slot.SetItemSlot(0, row["item_vnum"], 0)
		self.iconLight.Hide()
		if hasItem and self.lightEquipment and not row.get("locked"):
			item.SelectItem(row["item_vnum"])
			self.iconLight.LoadImage(item.GetIconImageFileName())
			self.iconLight.SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)
			self.iconLight.SetDiffuseColor(1.0, 1.0, 1.0, 0.28)
			self.iconLight.Show()
		if self.hint:
			if hasItem:
				self.hint.Hide()
			else:
				self.hint.Show()
		self.SetLocked(bool(row and row.get("locked")))
		self.slot.RefreshSlot()

	def SetLocked(self, locked):
		if locked:
			self.iconLight.Hide()
			self.lock.Show()
			self.slot.DisableSlot(0)
		else:
			self.lock.Hide()
			self.slot.EnableSlot(0)

	def SetSelectEmptySlotEvent(self, event):
		self.slot.SetSelectEmptySlotEvent(event)

	def SetSelectItemSlotEvent(self, event):
		self.slot.SetSelectItemSlotEvent(event)

	def SetUseSlotEvent(self, event):
		self.slot.SetUseSlotEvent(event)

	def SetUnselectItemSlotEvent(self, event):
		self.slot.SetUnselectItemSlotEvent(event)

	def SetOverInItemEvent(self, event):
		self.slot.SetOverInItemEvent(event)
		if app.ENABLE_SLOT_TOOLTIP_INFO:
			self.slot.SetOverInEvent(event)

	def SetOverOutItemEvent(self, event):
		self.slot.SetOverOutItemEvent(event)
		if app.ENABLE_SLOT_TOOLTIP_INFO:
			self.slot.SetOverOutEvent(event)


class ElementAccordionRow(ui.Window):
	HEIGHT = 34
	TEXT_CENTER_Y = 9
	PROGRESS_Y = 18

	def __init__(self, parent, event):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetSize(350, self.HEIGHT)
		self.button = ui.Button()
		self.button.SetParent(self)
		self.button.SetPosition(0, 0)
		self.button.SetSize(350, self.HEIGHT)
		self.button.SetEvent(event)
		self.button.Show()
		self.icon = CreateImage(self, 5, 5, "element_fire_24.png")
		self.name = CreateText(self, 37, self.TEXT_CENTER_Y, verticalAlign="center")
		self.value = CreateText(self, 321, self.TEXT_CENTER_Y, align="right", verticalAlign="center")
		self.progress = MountProgressBar(self, 201, self.PROGRESS_Y, "parent")
		self.glyph = CreateImage(self, 325, 8, "glyph_right_8.png")
		self.Show()

	def SetData(self, row):
		state = row["state"]
		carrier = ASSET_ROOT + row["carrier"]
		self.button.SetUpVisual(carrier)
		self.button.SetOverVisual(
			ASSET_ROOT + "element_parent_350x34_hover.png"
			if state != "locked" else carrier
		)
		self.button.SetDownVisual(
			ASSET_ROOT + "element_parent_350x34_opened.png"
			if state != "locked" else carrier
		)
		self.icon.LoadImage(ASSET_ROOT + row["icon"])
		self.name.SetText(row["name"])
		self.value.SetText(row["bonus_text"])
		self.progress.SetValue(row.get("bonus_basis_points", 0), 2000)
		if state == "completed":
			glyph = "glyph_check_8.png"
		elif state == "locked":
			glyph = "glyph_lock_8.png"
		elif row.get("opened"):
			glyph = "glyph_down_8.png"
		else:
			glyph = "glyph_right_8.png"
		self.glyph.LoadImage(ASSET_ROOT + glyph)


class ElementTaskRow(ui.Window):
	HEIGHT = 35
	WIDTH = 328
	TEXT_CENTER_Y = 9
	PROGRESS_Y = 20

	def __init__(self, parent, submit_event=None):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.name = CreateText(self, 9, self.TEXT_CENTER_Y, verticalAlign="center")
		self.name.SetLimitWidth(205)
		self.counter = CreateText(self, 317, self.TEXT_CENTER_Y, align="right", verticalAlign="center")
		self.progress = MountProgressBar(self, 32, self.PROGRESS_Y, "task")
		self.submit = None
		if submit_event:
			self.submit = SemanticButton(
				self, 158, 5, u"Odevzdat", submit_event
			)
			self.submit.Hide()
		self.Show()

	def SetData(self, row, name):
		self.name.SetText(name)
		self.counter.SetText(row["progress_text"])
		self.progress.SetValue(row["progress"], row["target"])
		if self.submit:
			if row["event_kind"] == 3 and not row["complete"]:
				self.name.SetLimitWidth(140)
				self.counter.Hide()
				self.progress.Hide()
				self.submit.Show()
			else:
				self.name.SetLimitWidth(205)
				self.counter.Show()
				self.progress.Show()
				self.submit.Hide()




class DynamicScrollViewport(ui.Window):
	def __init__(
		self, parent, x, y, width, height, keepScrollVisible=False,
		scrollParent=None, scrollPosition=None, contentInset=14,
	):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.EnableScissorRect()
		self.keepScrollVisible = bool(keepScrollVisible)
		self.hasOverflow = False
		self.rows = []
		self.contentHeight = 0
		self.contentInset = max(0, int(contentInset))
		self.content = ui.Window()
		self.content.SetParent(self)
		self.content.SetPosition(0, 0)
		self.content.SetSize(width - self.contentInset, height)
		self.content.Show()
		self.scroll = SettingsScrollBar()
		scrollOwner = scrollParent if scrollParent is not None else self
		self.scroll.SetParent(scrollOwner)
		scrollX, scrollY = scrollPosition or (width - 13, 2)
		self.scroll.SetPosition(scrollX, scrollY)
		self.scroll.SetScrollBarSize(height - 4)
		self.scroll.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scroll.Hide()
		self.Show()

	def Reset(self):
		for row in self.rows:
			row.Hide()
		self.rows = []
		self.contentHeight = 0
		self.content.SetPosition(0, 0)
		self.hasOverflow = False
		self.scroll.UnlockScroll()
		self.scroll.SetPos(0.0)

	def AddRow(self, row, height, indent=0, gap=2):
		row.SetParent(self.content)
		row.SetPosition(indent, self.contentHeight)
		row.Show()
		self.rows.append(row)
		self.contentHeight += int(height) + int(gap)

	def Finalize(self):
		self.content.SetSize(self.GetWidth() - self.contentInset, max(self.GetHeight(), self.contentHeight))
		overflow, thumbScale = _ScrollMetrics(
			self.GetHeight(), self.contentHeight,
			self.scroll.TEMP_SPACE,
			self.scroll.MINIMUM_THUMB_HEIGHT,
		)
		self.hasOverflow = overflow > 0
		if self.hasOverflow:
			self.scroll.UnlockScroll()
			self.scroll.SetMiddleBarSize(thumbScale)
			self.scroll.SetScrollStep(
				min(1.0, 40.0 / float(max(1, overflow)))
			)
			self.scroll.Show()
		elif self.keepScrollVisible:
			self.scroll.UnlockScroll()
			self.scroll.SetMiddleBarSize(thumbScale)
			self.scroll.SetPos(0.0)
			self.scroll.LockScroll()
			self.scroll.Show()
		else:
			self.scroll.UnlockScroll()
			self.scroll.SetPos(0.0)
			self.scroll.Hide()
		self.__OnScroll()

	def __OnScroll(self):
		overflow = max(0, self.contentHeight - self.GetHeight())
		self.content.SetPosition(0, -int(float(overflow) * self.scroll.GetPos()))

	def OnMouseWheel(self, delta):
		if self.hasOverflow and self.scroll.IsShow():
			if delta > 0:
				self.scroll.OnUp()
				return True
			if delta < 0:
				self.scroll.OnDown()
				return True
		return False


class ElementTaskPanel(ui.Window):
	WIDTH = 328
	HEIGHT = 4

	def __init__(self, parent):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.rows = []
		self.Show()

	def AddTask(self, row):
		row.SetParent(self)
		row.SetPosition(0, len(self.rows) * row.HEIGHT)
		row.Show()
		self.rows.append(row)

	def Finalize(self):
		self.HEIGHT = _TaskPanelHeight(len(self.rows))
		self.SetSize(self.WIDTH, self.HEIGHT)
