# -*- coding: utf-8 -*-
"""Compact editor. Draft colors affect an isolated native spell scene only."""
import cfg
import grp
import player
import renderTarget
import skill
import ui
import uiScriptLocale
from uicolorpicker import HexToRgb, RgbToHex, UnpackRgb


def _Bound(method, *args):
	callback = ui.__mem_func__(method)
	return lambda: callback(*args)


def _NativeColor(argb):
	# wndMgr/grp take signed C int colors, while authored ARGB uses uint32.
	return argb - 0x100000000 if argb >= 0x80000000 else argb


def _ReadHex(text):
	value = str(text).strip()
	if value.startswith("#"):
		value = value[1:]
	if len(value) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
		raise ValueError("Expected six hexadecimal digits")
	return HexToRgb(value)


def HsvToRgb(hue, saturation, value):
	sector = (hue % 1.0) * 6.0
	index = int(sector)
	fraction = sector - index
	p = value * (1.0 - saturation)
	q = value * (1.0 - saturation * fraction)
	t = value * (1.0 - saturation * (1.0 - fraction))
	rgb = ((value, t, p), (q, value, p), (p, value, t),
		(p, q, value), (t, p, value), (value, p, q))[index]
	return tuple(int(round(channel * 255)) for channel in rgb)


def RgbToHsv(rgb):
	r, g, b = [channel / 255.0 for channel in rgb]
	value, low = max(r, g, b), min(r, g, b)
	delta = value - low
	if not delta:
		return 0.0, 0.0, value
	if value == r:
		hue = ((g - b) / delta) % 6.0
	elif value == g:
		hue = (b - r) / delta + 2.0
	else:
		hue = (r - g) / delta + 4.0
	return hue / 6.0, delta / value, value


def PackColor(rgb):
	r, g, b = rgb
	# A nonzero alpha byte distinguishes custom black from original (zero).
	return 0x01000000 | (r << 16) | (g << 8) | b


class _Swatch(ui.Window):
	def __init__(self, callback, clear=None):
		ui.Window.__init__(self)
		self.callback, self.clear = callback, clear
		self.color, self.selected = 0, False
		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.AddFlag("not_pick")
		self.label.SetOutline()
		self.label.SetHorizontalAlignCenter()
		self.label.Show()

	def SetLabel(self, text):
		self.label.SetPosition(self.GetWidth() // 2, (self.GetHeight() - 12) // 2)
		self.label.SetText(text)

	def OnRender(self):
		x, y = self.GetGlobalPosition()
		grp.SetColor(_NativeColor(0xffffd695 if self.selected else 0xff61564c))
		grp.RenderBar(x, y, self.GetWidth(), self.GetHeight())
		grp.SetColor(_NativeColor((0xff000000 | (self.color & 0xffffff)) if self.color else 0xff29272a))
		grp.RenderBar(x + 1, y + 1, self.GetWidth() - 2, self.GetHeight() - 2)

	def OnMouseLeftButtonDown(self):
		self.callback()
		return True

	def OnMouseRightButtonDown(self):
		if self.clear:
			self.clear()
		return True


class _Palette(ui.Window):
	def __init__(self, callback):
		ui.Window.__init__(self)
		self.callback, self.pressed = callback, False
		self.hue, self.saturation = 0.0, 0.0
		self.image = ui.ImageBox()
		self.image.SetParent(self)
		self.image.AddFlag("not_pick")
		self.image.LoadImage("skillcolor_preview_palette.png")
		self.image.Show()
		self.SetSize(204, 78)
		self.dot = ui.Bar()
		self.dot.SetParent(self)
		self.dot.AddFlag("not_pick")
		self.dot.SetSize(3, 3)
		self.dot.SetColor(_NativeColor(0xffffffff))
		self.dot.Show()

	def SetSelection(self, hue, saturation):
		self.hue, self.saturation = hue, saturation
		self.dot.SetPosition(int(hue * 201), int((1.0 - saturation) * 75))

	def _Pick(self):
		x, y = self.GetMouseLocalPosition()
		self.callback(max(0.0, min(1.0, x / 203.0)),
			1.0 - max(0.0, min(1.0, y / 77.0)))

	def OnMouseLeftButtonDown(self):
		self.pressed = True
		self._Pick()
		return True

	def OnMouseLeftButtonUp(self):
		self.pressed = False
		return True

	def OnMouseOverOut(self):
		self.pressed = False

	def OnUpdate(self):
		if self.pressed and self.IsIn():
			self._Pick()


class _Brightness(ui.Window):
	"""One pick surface for the entire gradient, including both endpoints."""
	def __init__(self, callback):
		ui.Window.__init__(self)
		self.callback, self.pressed, self.value = callback, False, 1.0
		self.SetSize(171, 12)
		self.image = ui.ImageBox()
		self.image.SetParent(self)
		self.image.AddFlag("not_pick")
		self.image.LoadImage("skillcolor_preview_value.png")
		self.image.Show()
		self.cursor = ui.Bar()
		self.cursor.SetParent(self)
		self.cursor.AddFlag("not_pick")
		self.cursor.SetSize(3, 12)
		self.cursor.SetColor(_NativeColor(0xffffd695))
		self.cursor.Show()

	def SetSliderPos(self, value):
		self.value = max(0.0, min(1.0, value))
		self.cursor.SetPosition(int(round(self.value * (self.GetWidth() - 3))), 0)

	def GetSliderPos(self):
		return self.value

	def _Pick(self):
		x, _ = self.GetMouseLocalPosition()
		self.SetSliderPos(x / float(self.GetWidth() - 1))
		self.callback()

	def OnMouseLeftButtonDown(self):
		self.pressed = True
		self._Pick()
		return True

	def OnMouseLeftButtonUp(self):
		if self.pressed:
			self._Pick()
		self.pressed = False
		return True

	def OnUpdate(self):
		if self.pressed:
			self._Pick()


class _Preview(ui.RenderTarget):
	def __init__(self):
		ui.RenderTarget.__init__(self)
		self.sceneIndex, self.drag = -1, None
		self.ResetView()

	def ResetView(self):
		self.yaw, self.pitch, self.zoom = 45.0, 25.0, 1.0
		self.panX = self.panY = 0.0
		self._SendCamera()

	def _SendCamera(self):
		if self.sceneIndex >= 0 and hasattr(renderTarget, "SetSkillPreviewCamera"):
			renderTarget.SetSkillPreviewCamera(self.sceneIndex, self.yaw, self.pitch,
				self.zoom, self.panX, self.panY)

	def _Start(self, mode):
		self.drag = mode
		self.lastMouse = self.GetMouseLocalPosition()
		return True

	def OnMouseLeftButtonDown(self):
		return self._Start("pan")

	def OnMouseRightButtonDown(self):
		return self._Start("orbit")

	def OnMouseLeftButtonUp(self):
		self.drag = None
		return True

	def OnMouseRightButtonUp(self):
		self.drag = None
		return True

	def OnRunMouseWheel(self, delta):
		if delta:
			self.zoom = max(0.1, min(3.0, self.zoom * (0.9 if delta > 0 else 1.0 / 0.9)))
			self._SendCamera()
		return True

	def OnUpdate(self):
		if self.drag is None or self.sceneIndex < 0:
			return
		x, y = self.GetMouseLocalPosition()
		dx, dy = x - self.lastMouse[0], y - self.lastMouse[1]
		self.lastMouse = x, y
		if not (dx or dy):
			return
		if self.drag == "orbit":
			self.yaw = (self.yaw - dx * 0.5) % 360.0
			self.pitch = max(-80.0, min(80.0, self.pitch + dy * 0.5))
		else:
			self.panX = max(-2.0, min(2.0, self.panX - dx / float(self.GetWidth())))
			self.panY = max(-2.0, min(2.0, self.panY + dy / float(self.GetHeight())))
		self._SendCamera()


class _OriginalButton(ui.Button):
	def __init__(self, callback):
		ui.Button.__init__(self)
		self.callback = callback

	def DownEvent(self):
		self.callback(True)

	def CallEvent(self):
		self.callback(False)

	def OnMouseOverOut(self):
		self.callback(False)


class SkillColorWindow(ui.BoardWithTitleBar):
	def __init__(self, skillSlot, skillIndex):
		# ui.Window.__init__ invokes our Hide before any child is constructed.
		self.palette = self.hexEdit = self.preview = self.brightness = None
		self.previewIndex = -1
		self.comparing = False
		ui.BoardWithTitleBar.__init__(self)
		self.skillSlot, self.skillIndex = skillSlot, skillIndex
		self.draft, self.layer, self.comparing = [0] * 5, 0, False
		self.hue, self.saturation, self.value = 0.0, 1.0, 1.0
		self.updatingHex, self.hexValid = False, True
		self.children, self.swatches, self.presets = [], [], []
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(440, 340)
		self.SetTitleName(uiScriptLocale.SKILL_COLOR_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self._Text(14, 39, "S", 0xffe5c177)
		self._Text(36, 39, skill.GetSkillName(skillIndex), 0xffeee6d6)
		self._Text(14, 60, "Náhled schopnosti", 0xffb8afa1)
		self._Bar(14, 78, 190, 176, 0xff5c4b3b)
		self._Bar(15, 79, 188, 174, 0xff121215)
		self.preview = self._Keep(_Preview(), 15, 79, 188, 174)
		self.preview.Hide()
		self._Text(14, 257, "Levý tah: posun | pravý: otáčení", 0xffb8afa1)
		self._Text(14, 273, "Kolečko: přiblížení", 0xffb8afa1)
		self._Button(116, 273, "Vrátit pohled", self.ResetView, "88x21")
		self.previewMessage = self._Text(109, 167, "Náhled není dostupný", 0xffb8afa1)
		self.previewMessage.SetHorizontalAlignCenter()
		self.layerLabel = self._Text(219, 78, "Vrstva 1", 0xffe5c177)
		self._Button(335, 74, "Původní vrstva", self.ResetLayer, "88x21")
		for index in range(5):
			swatch = _Swatch(_Bound(self.SelectLayer, index))
			self._Keep(swatch, 219 + index * 42, 101, 36, 27)
			swatch.SetLabel(str(index + 1))
			self.swatches.append(swatch)
		self.palette = self._Keep(_Palette(ui.__mem_func__(self.SelectPalette)), 219, 140)
		self._Text(219, 228, "Jas", 0xffb8afa1)
		self.brightness = self._Keep(_Brightness(ui.__mem_func__(self.SelectBrightness)), 252, 228)
		self._Text(219, 250, "HEX", 0xffb8afa1)
		self._Bar(252, 247, 78, 21, 0xff302b29)
		self.hexEdit = self._Keep(ui.EditLine(), 258, 250, 66, 16)
		self.hexEdit.SetMax(7)
		self.hexEdit.OnIMEUpdate = ui.__mem_func__(self.OnHexUpdate)
		self.hexEdit.SetReturnEvent(ui.__mem_func__(self.ApplyHex))
		self.hexEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self._Button(335, 247, "Přidat barvu", self.AddPreset, "88x21")
		self._Text(219, 39, "Oblíbené barvy", 0xffe5c177)
		self.presetMessage = self._Text(219, 60, "Klik: použít | pravý: smazat", 0xffb8afa1)
		for index in range(10):
			swatch = _Swatch(_Bound(self.SelectPreset, index),
				_Bound(self.DeletePreset, index))
			self._Keep(swatch, 219 + index * 21, 275, 15, 17)
			self.presets.append(swatch)
		self._Button(14, 306, "Původní (držet)", self.Compare, hold=True)
		self.replayButton = self._Button(170, 306, "Přehrát", self.Replay)
		self.saveButton = self._Button(325, 306, "Uložit", self.Save)

	def _Keep(self, widget, x, y, width=None, height=None):
		widget.SetParent(self)
		widget.SetPosition(x, y)
		if width is not None:
			widget.SetSize(width, height)
		widget.Show()
		self.children.append(widget)
		return widget

	def _Text(self, x, y, text, color):
		widget = self._Keep(ui.TextLine(), x, y)
		widget.AddFlag("not_pick")
		widget.SetText(text)
		widget.SetPackedFontColor(_NativeColor(color))
		return widget

	def _Bar(self, x, y, width, height, color):
		widget = self._Keep(ui.Bar(), x, y, width, height)
		widget.AddFlag("not_pick")
		widget.SetColor(_NativeColor(color))
		return widget

	def _Button(self, x, y, text, callback, size="100x21", hold=False):
		widget = _OriginalButton(ui.__mem_func__(callback)) if hold else ui.Button()
		prefix = "d:/ymir work/ui/public/crimson/controls/unified/button_%s_" % size
		widget.SetUpVisual(prefix + "normal.png")
		widget.SetOverVisual(prefix + "hover.png")
		widget.SetDownVisual(prefix + "pressed.png")
		widget.SetText(text)
		if not hold:
			widget.SetEvent(ui.__mem_func__(callback))
		return self._Keep(widget, x, y)

	def Show(self):
		if self.IsShow():
			self.SetTop()
			return
		self.draft = [0 if value in (0, 99999999) else value
			for value in player.GetSkillColor(self.skillSlot)]
		self.comparing = False
		self.previewIndex = renderTarget.CreateSkillPreview(self.skillIndex, 188, 174)
		if self.previewIndex >= 0:
			self.preview.SetRenderTarget(self.previewIndex)
			self.preview.sceneIndex = self.previewIndex
			self.preview.ResetView()
			self.preview.Show()
			self.previewMessage.Hide()
			self.replayButton.Enable()
		else:
			self.preview.Hide()
			self.previewMessage.Show()
			self.replayButton.Disable()
		self._RefreshPresets()
		self.presetMessage.SetText("Klik: použít | pravý: smazat")
		self.SelectLayer(0)
		self._SendPreview()
		self.SetCenterPosition()
		ui.BoardWithTitleBar.Show(self)
		self.SetTop()

	def Hide(self):
		# Character tabs also call Hide directly; it must release native scenes.
		self.Close()

	def Close(self):
		if self.palette is not None:
			self.palette.pressed = False
		if self.brightness is not None:
			self.brightness.pressed = False
		if self.hexEdit is not None:
			self.hexEdit.KillFocus()
		if self.preview is not None:
			self.preview.drag = None
			self.preview.sceneIndex = -1
			self.preview.Hide()
		index, self.previewIndex = self.previewIndex, -1
		if index >= 0:
			renderTarget.CloseSkillPreview(index)
		self.comparing = False
		ui.BoardWithTitleBar.Hide(self)

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def SelectLayer(self, index):
		self.layer = index
		self.layerLabel.SetText("Vrstva %d" % (index + 1))
		self._RefreshColor()

	def _RefreshColor(self, updateHsv=True):
		value = self.draft[self.layer]
		if updateHsv:
			self.hue, self.saturation, self.value = RgbToHsv(UnpackRgb(value or 0xffffff))
		self.palette.SetSelection(self.hue, self.saturation)
		self.brightness.SetSliderPos(self.value)
		self.updatingHex = True
		self.hexEdit.SetText(RgbToHex(value) if value else "")
		self.updatingHex = False
		self.hexValid = True
		self.hexEdit.SetPackedFontColor(_NativeColor(0xffeee6d6))
		self.saveButton.Enable()
		for index, swatch in enumerate(self.swatches):
			swatch.color, swatch.selected = self.draft[index], index == self.layer

	def _SetRgb(self, rgb, updateHsv=True):
		self.draft[self.layer] = PackColor(rgb)
		self._RefreshColor(updateHsv)
		self._SendPreview()

	def SelectPalette(self, hue, saturation):
		self.hue, self.saturation = hue % 1.0, saturation
		self._SetRgb(HsvToRgb(self.hue, self.saturation, self.value), False)

	def SelectBrightness(self):
		self.value = self.brightness.GetSliderPos()
		self._SetRgb(HsvToRgb(self.hue, self.saturation, self.value), False)

	def OnHexUpdate(self):
		ui.EditLine.OnIMEUpdate(self.hexEdit)
		if not self.updatingHex:
			self.ApplyHex()

	def ApplyHex(self):
		try:
			rgb = UnpackRgb(_ReadHex(self.hexEdit.GetText()))
		except ValueError:
			self.hexValid = False
			self.hexEdit.SetPackedFontColor(_NativeColor(0xffee7777))
			self.saveButton.Disable()
			return False
		# Preserve cursor/typed casing while editing the hex field.
		self.draft[self.layer] = PackColor(rgb)
		self.hue, self.saturation, self.value = RgbToHsv(rgb)
		self.palette.SetSelection(self.hue, self.saturation)
		self.brightness.SetSliderPos(self.value)
		self.swatches[self.layer].color = self.draft[self.layer]
		self.hexValid = True
		self.hexEdit.SetPackedFontColor(_NativeColor(0xffeee6d6))
		self.saveButton.Enable()
		self._SendPreview()
		return True

	def ResetLayer(self):
		self.draft[self.layer] = 0
		self._RefreshColor()
		self._SendPreview()

	def _SendPreview(self):
		if self.previewIndex >= 0:
			colors = [0] * 5 if self.comparing else self.draft
			renderTarget.SetSkillPreviewColors(self.previewIndex, *colors)

	def Compare(self, original):
		self.comparing = original
		self._SendPreview()

	def ResetView(self):
		self.preview.ResetView()

	def Replay(self):
		if self.previewIndex >= 0:
			renderTarget.ReplaySkillPreview(self.previewIndex)

	def Save(self):
		if not self.hexValid:
			return False
		player.SetSkillColor(self.skillSlot, *self.draft)
		self.Close()
		return True

	def _ReadPresets(self):
		values = []
		for text in (cfg.Get(cfg.SAVE_SKILL_COLOR, str(self.skillSlot), "") or "").split():
			try:
				values.append(_ReadHex(text))
			except ValueError:
				continue
		return values[:10]

	def _RefreshPresets(self):
		values = self._ReadPresets()
		for index, swatch in enumerate(self.presets):
			swatch.color = (0x01000000 | values[index]) if index < len(values) else 0
			swatch.SetLabel("" if index < len(values) else "·")

	def SelectPreset(self, index):
		values = self._ReadPresets()
		if index < len(values):
			self._SetRgb(UnpackRgb(values[index]))
		else:
			self.presetMessage.SetText("Barvu uložíš přes Přidat barvu.")

	def AddPreset(self):
		values = self._ReadPresets()
		if not self.hexValid or not self.draft[self.layer]:
			self.presetMessage.SetText("Nejprve vyber vlastní barvu.")
			return False
		if len(values) >= 10:
			self.presetMessage.SetText("Plno: pravým barvu smažeš.")
			return False
		values.append(self.draft[self.layer] & 0xffffff)
		cfg.Set(cfg.SAVE_SKILL_COLOR, str(self.skillSlot), " ".join(RgbToHex(value) for value in values))
		self._RefreshPresets()
		self.presetMessage.SetText("Barva uložena (%d/10)." % len(values))
		return True

	def DeletePreset(self, index):
		values = self._ReadPresets()
		if index < len(values):
			del values[index]
			self.presetMessage.SetText("Barva smazána (%d/10)." % len(values))
			cfg.Set(cfg.SAVE_SKILL_COLOR, str(self.skillSlot), " ".join(RgbToHex(value) for value in values))
			self._RefreshPresets()
