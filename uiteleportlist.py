# -*- coding: utf-8 -*-
"""Approved C11 list, composed inside the existing teleport atlas shell."""
import fontconfig
import player
import teleportlistdata
import ui
import uicrimsoncontrols
import wndMgr


SKIN = "d:/ymir work/ui/game/crimson_ember/teleport_atlas/list_c11/"
TEXT = 0xffe8e0cf
DIM = 0xffaaa391
GOLD = 0xffe7c77d
CATEGORY_ICON_BOUNDS = {
	"compass": (1, 1, 17, 17),
	"town": (1, 2, 17, 16),
	"sword": (3, 1, 15, 17),
	"crossed_swords": (1, 1, 17, 17),
}


def Scaled(value, scale):
	return int(round(value * scale))


def Image(parent, path, x, y, scale):
	image = ui.ExpandedImageBox()
	image.SetParent(parent)
	image.AddFlag("not_pick")
	image.LoadImage(SKIN + path)
	image.SetScale(scale, scale)
	image.SetPosition(Scaled(x, scale), Scaled(y, scale))
	image.Show()
	return image


def Label(parent, text, x, y, scale, role=fontconfig.ROLE_CONTROL, color=TEXT, align="left"):
	label = ui.TextLine()
	label.SetParent(parent)
	label.AddFlag("not_pick")
	# The atlas uses the fixed native C11 type scale, including the 800px fallback.
	label.SetFontName(fontconfig.FontForRole(role, 0))
	label.SetText(text)
	label.SetPackedFontColor(color)
	label.SetOutline()
	label.SetVerticalAlignCenter()
	if align == "center":
		label.SetHorizontalAlignCenter()
	elif align == "right":
		label.SetHorizontalAlignRight()
	label.SetPosition(Scaled(x, scale), Scaled(y, scale))
	label.Show()
	return label


class ListControl(ui.Button):
	"""Native button hit testing and capture with coordinated decorative states."""
	def __init__(self, page, family, width, height):
		ui.Button.__init__(self)
		self.page = page
		self.scale = page.scale
		self.family = family
		self.selected = False
		self.locked = False
		self.visualState = None
		self.width = width
		self.height = height
		self.SetParent(page)
		self.SetOnRunMouseWheelEvent(self._Wheel)
		self._SetCarrier()

	def _Wheel(self, down):
		if self.page:
			self.page.Scroll(1 if down else -1)

	def _SetCarrier(self):
		base = "disabled" if self.locked else "selected" if self.selected else "normal"
		over = base if base != "normal" else "hover"
		down = base if base != "normal" else "pressed"
		self.SetUpVisual(self._NativeVisual(base))
		self.SetOverVisual(self._NativeVisual(over))
		self.SetDownVisual(self._NativeVisual(down))
		self.SetDisableVisual(self._NativeVisual("disabled"))
		wndMgr.SetScale(self.hWnd, self.scale, self.scale)
		self.SetSize(Scaled(self.width, self.scale), Scaled(self.height, self.scale))
		self.visualState = None

	def _NativeVisual(self, state):
		return SKIN + self.family + "_" + state + ".png"

	def OnUpdate(self):
		state = ("disabled" if self.locked else "selected" if self.selected
			else "pressed" if self.IsDown() else "hover" if self.IsIn() else "normal")
		if state != self.visualState:
			self.visualState = state
			self._Decorate(state)

	def Destroy(self):
		self.Hide()
		self.SetEvent(None)
		self.SetOnRunMouseWheelEvent(None)
		self.page = None


class CategoryButton(ListControl):
	def __init__(self, page, category, text, glyph):
		ListControl.__init__(self, page, "tab", 132, 28)
		self.category = category
		self.glyph = glyph
		self.icon = Image(self, "icon_" + glyph + "_normal.png", 0, 5, self.scale)
		self.label = Label(self, text, 0, 14, self.scale)
		# Center the combined icon + gap + measured text, not the label alone.
		left, top, right, bottom = CATEGORY_ICON_BOUNDS[glyph]
		icon_width = Scaled(right - left, self.scale)
		gap = Scaled(6, self.scale)
		start = (self.GetWidth() - icon_width - gap - self.label.GetTextSize()[0]) // 2
		self.icon.SetPosition(start - Scaled(left, self.scale),
			(self.GetHeight() - Scaled(top + bottom, self.scale)) // 2)
		self.label.SetPosition(start + icon_width + gap, self.GetHeight() // 2)
		self.SetEvent(self._Select)

	def _Select(self):
		if self.page:
			self.page.SetCategory(self.category)

	def SetSelected(self, selected):
		self.selected = selected
		self._SetCarrier()
		self.OnUpdate()

	def _Decorate(self, state):
		self.icon.LoadImage(SKIN + "icon_" + self.glyph + "_" + state + ".png")
		self.icon.SetScale(self.scale, self.scale)
		self.label.SetPackedFontColor(GOLD if self.selected else TEXT)


class DestinationRow(ListControl):
	def __init__(self, page):
		ListControl.__init__(self, page, "frame_c", 466, 66)
		self.destinationId = None
		self.photo = Image(self, "scenes/all_in_one_row.png", 5, 5, self.scale)
		self.frame = Image(self, "frame_c_normal.png", 0, 0, self.scale)
		self.namePlate = Image(self, "label_c_normal.png", 14, 18, self.scale)
		self.namePlate.SetAlpha(212.0 / 255.0)
		self.levelPlate = Image(self, "level_normal.png", 366, 18, self.scale)
		self.levelPlate.SetAlpha(238.0 / 255.0)
		self.name = Label(self, "", 43, 33, self.scale)
		self.minimum = Label(self, "", 407, 33, self.scale, align="center")
		self.arrow = Image(self, "icon_right_selected.png", 22, 27, self.scale)
		self.lock = Image(self, "icon_lock_normal.png", 346, 27, self.scale)
		self.SetEvent(self._Select)

	def _NativeVisual(self, state):
		# Native hit testing/capture uses a transparent carrier. The real frame
		# is drawn exactly once above the photograph, before the name/level plates.
		return SKIN + "hit_466x66.png"

	def _Select(self):
		if self.page and self.destinationId:
			self.page.Select(self.destinationId)

	def SetDestination(self, destination, selected, level):
		if self.destinationId != destination["id"]:
			self.destinationId = destination["id"]
			self.photo.LoadImage(SKIN + "scenes/" + self.destinationId + "_row.png")
			self.photo.SetScale(self.scale, self.scale)
		self.selected = selected
		self.locked = level < destination["level"]
		self.name.SetText(destination["name"])
		self.minimum.SetText("Od %d" % destination["level"])
		self.photo.SetAlpha(218.0 / 255.0 if self.locked else 1.0)
		self._SetCarrier()
		self.OnUpdate()
		self.Show()

	def _Decorate(self, state):
		self.frame.LoadImage(SKIN + "frame_c_" + state + ".png")
		self.frame.SetScale(self.scale, self.scale)
		self.namePlate.LoadImage(SKIN + "label_c_" + state + ".png")
		self.levelPlate.LoadImage(SKIN + "level_" + state + ".png")
		self.namePlate.SetScale(self.scale, self.scale)
		self.namePlate.SetAlpha(212.0 / 255.0)
		self.levelPlate.SetScale(self.scale, self.scale)
		self.levelPlate.SetAlpha(238.0 / 255.0)
		color = DIM if self.locked else GOLD if self.selected else TEXT
		self.name.SetPackedFontColor(color)
		self.minimum.SetPackedFontColor(color)
		if self.selected:
			self.arrow.Show()
		else:
			self.arrow.Hide()
		if self.locked:
			self.lock.Show()
		else:
			self.lock.Hide()


class TeleportListPage(ui.Window):
	def __init__(self, owner, scale=1.0, category="all"):
		ui.Window.__init__(self)
		self.owner = owner
		self.scale = scale
		self.model = teleportlistdata.TeleportListModel(category)
		self.lastLevel = None
		self.detailDestinationId = None
		self.updatingScroll = False
		self.widgets = []
		self.rows = []
		self.tabs = []
		self.SetSize(Scaled(821, scale), Scaled(491, scale))
		self._Build()
		self.Refresh()

	def _Image(self, path, x, y):
		image = Image(self, path, x, y, self.scale)
		self.widgets.append(image)
		return image

	def _Label(self, text, x, y, role=fontconfig.ROLE_CONTROL, color=TEXT, align="left"):
		label = Label(self, text, x, y, self.scale, role, color, align)
		self.widgets.append(label)
		return label

	def _Build(self):
		self._Image("interior.png", 0, 0)
		self._Label("Seznam map", 22, 26, fontconfig.ROLE_LARGE_BOLD)
		self.playerLevel = self._Label("", 800, 65, fontconfig.ROLE_DENSE, DIM, "right")
		for index, (key, text, icon) in enumerate(teleportlistdata.CATEGORIES):
			tab = CategoryButton(self, key, text, icon)
			tab.SetPosition(Scaled(20 + 138 * index, self.scale), Scaled(51, self.scale))
			tab.Show()
			self.tabs.append(tab)
		for index in range(self.model.PAGE_SIZE):
			row = DestinationRow(self)
			row.SetPosition(Scaled(20, self.scale), Scaled(89 + 70 * index, self.scale))
			self.rows.append(row)
		self.scrollBar = ui.ScrollBarFlat()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(Scaled(489, self.scale), Scaled(89, self.scale))
		self.scrollBar.SetScrollBarSize(Scaled(346, self.scale))
		self.scrollBar.SetScrollEvent(self._OnScroll)
		self.footer = self._Label("", 28, 464, fontconfig.ROLE_DENSE, DIM)
		self._Image("panel_c_normal.png", 504, 89)
		self._Image("title_c.png", 514, 99)
		self.detailTitle = self._Label("", 653, 115, fontconfig.ROLE_LARGE_BOLD, GOLD, "center")
		self._Image("icon_level_normal.png", 519, 148)
		self._Label("Minimální úroveň", 538, 155, fontconfig.ROLE_BODY, DIM)
		self.detailMinimum = self._Label("", 789, 155, fontconfig.ROLE_LARGE_BOLD, GOLD, "right")
		self.detailPhoto = self._Image("scenes/all_in_one_detail.png", 517, 179)
		self._Image("hero_c_normal.png", 513, 175)
		self.teleportButton = ui.Button()
		self.teleportButton.SetParent(self)
		uicrimsoncontrols.ApplyVisuals(self.teleportButton, "180x25")
		wndMgr.SetScale(self.teleportButton.hWnd, self.scale, self.scale)
		self.teleportButton.SetSize(Scaled(180, self.scale), Scaled(25, self.scale))
		self.teleportButton.SetPosition(Scaled(564, self.scale), Scaled(421, self.scale))
		self.teleportButton.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL, 0))
		self.teleportButton.SetText("Teleportovat")
		self.teleportButton.SetEvent(self.Teleport)
		self.teleportButton.Show()

	def SetCategory(self, category):
		self.model.SetCategory(category)
		self.Refresh()
		if self.owner:
			self.owner.SaveListPreferences()

	def Select(self, destination_id):
		if self.model.Select(destination_id):
			self.Refresh()

	def Scroll(self, delta):
		self.model.Scroll(delta)
		self.Refresh()

	def _OnScroll(self):
		if not self.updatingScroll:
			target = int(round(self.scrollBar.GetPos() * self.model.MaxOffset()))
			self.Scroll(target - self.model.offset)

	def OnRunMouseWheel(self, nLen):
		self.Scroll(1 if nLen < 0 else -1)
		return True

	def Refresh(self):
		level = player.GetStatus(player.LEVEL)
		self.lastLevel = level
		self.playerLevel.SetText("Tvoje úroveň: %d" % level)
		for tab in self.tabs:
			tab.SetSelected(tab.category == self.model.category)
		visible = self.model.Visible()
		for index, row in enumerate(self.rows):
			if index < len(visible):
				row.SetDestination(visible[index], visible[index]["id"] == self.model.selectedId, level)
			else:
				row.Hide()
		count = len(self.model.Destinations())
		self.footer.SetText("%d %s v kategorii" % (count, "mapa" if count == 1 else "mapy" if count < 5 else "map"))
		if self.model.MaxOffset():
			self.updatingScroll = True
			self.scrollBar.SetMiddleBarSize(float(self.model.PAGE_SIZE) / count)
			self.scrollBar.SetScrollStep(1.0 / self.model.MaxOffset())
			self.scrollBar.SetPos(float(self.model.offset) / self.model.MaxOffset())
			self.updatingScroll = False
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		selected = self.model.Selected()
		if selected:
			self.detailTitle.SetText(selected["name"])
			self.detailMinimum.SetText(str(selected["level"]))
			if self.detailDestinationId != selected["id"]:
				self.detailPhoto.LoadImage(SKIN + "scenes/" + selected["id"] + "_detail.png")
				self.detailPhoto.SetScale(self.scale, self.scale)
				self.detailDestinationId = selected["id"]
		if self.model.CanTeleport(level):
			self.teleportButton.Enable()
		else:
			self.teleportButton.Disable()

	def Teleport(self):
		self.Refresh()
		if self.owner and self.model.CanTeleport(player.GetStatus(player.LEVEL)):
			self.owner.SelectDestination(self.model.selectedId)

	def OnUpdate(self):
		if not self.IsShow():
			return
		if player.GetStatus(player.LEVEL) != self.lastLevel:
			self.Refresh()
		# Native CButton::OnUpdate does not dispatch Python OnUpdate. The page is
		# a CWindow, so it also drives the plates and glyphs of its native buttons.
		for control in self.tabs + self.rows:
			if control.IsShow():
				control.OnUpdate()

	def Destroy(self):
		self.Hide()
		self.owner = None
		for control in self.rows + self.tabs:
			control.Destroy()
		self.teleportButton.SetEvent(None)
		self.scrollBar.SetScrollEvent(None)
		self.scrollBar.Destroy()
		self.rows = []
		self.tabs = []
		self.widgets = []
