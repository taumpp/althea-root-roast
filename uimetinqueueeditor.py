import json
import os
import time

import grp
import nonplayer
import ui
import uicrimsoncontrols
import wndMgr

import metinqueuepresets as presets
import uimetinqueueappearance as appearance
from uicolorpicker import UnpackRgb


class EditorController(appearance.MetinQueueAppearanceController):
	SLIDER_BINDINGS = appearance.MetinQueueAppearanceController.SLIDER_BINDINGS + (
		("SparkDensitySlider", "SparkDensityValue", 17, (0, 200)),
		("RingLineWidthSlider", "RingLineWidthValue", 18, (25, 300)),
		("AnimationSpeedSlider", "AnimationSpeedValue", 20, (25, 200)),
	)

	def Bind(self, page, closeOwner):
		if not appearance.MetinQueueAppearanceController.Bind(self, page, closeOwner):
			return False
		for name, index in (("SparksToggle", 16), ("PulseToggle", 19)):
			toggle = page.GetChild(name)
			event = lambda widget=toggle, field=index: self._SetExtraToggle(field, widget.IsDown())
			toggle.SetToggleUpEvent(event)
			toggle.SetToggleDownEvent(event)
		page.GetChild("AccentSwatch").SetMouseLeftButtonDownEvent(self.OpenAccentPicker)
		return True

	def _SetExtraToggle(self, index, enabled):
		if self._syncing or self.draft is None:
			return
		self.draft[index] = 1 if enabled else 0
		self._SyncEnabledStates()
		self._UpdatePreview()

	def _SetNearbyFillEnabled(self, enabled):
		appearance.MetinQueueAppearanceController._SetNearbyFillEnabled(self, enabled)
		if self.page:
			self.page.RefreshSummary()

	def _SyncUi(self):
		appearance.MetinQueueAppearanceController._SyncUi(self)
		if self.page and self.draft:
			self._SyncToggle(self.page.GetChild("SparksToggle"), bool(self.draft[16]))
			self._SyncToggle(self.page.GetChild("PulseToggle"), bool(self.draft[19]))
			self.page.RefreshSummary()

	def _SyncEnabledStates(self):
		appearance.MetinQueueAppearanceController._SyncEnabledStates(self)
		bodyMesh = self.draft[0] and self.draft[11] >= 2
		ringMesh = self.draft[1] and self.draft[12] >= 3
		for name, enabled in (("SparkDensitySlider", bodyMesh and self.draft[16]),
			("RingLineWidthSlider", ringMesh), ("AnimationSpeedSlider", bodyMesh or ringMesh),
			("SparksToggle", bodyMesh), ("PulseToggle", bodyMesh or ringMesh)):
			widget = self.page.GetChild(name)
			if enabled:
				widget.Enable()
			else:
				widget.Disable()

	def _SyncStyleLabels(self):
		appearance.MetinQueueAppearanceController._SyncStyleLabels(self)
		mesh = self.draft[11] >= 2
		self.page.GetChild("BodyStretchLabel").SetText(u"Poloměr" if mesh else u"Protažení")
		self.page.GetChild("BodyFillLabel").SetText(u"Šířka proudů" if mesh else u"Výplň")
		serpent = self.draft[11] == 6
		self.page.GetChild("BodyDensityLabel").SetText(u"Hustota jisker obalu" if serpent else u"Hustota obalu")
		self.bodyStyleButton.SetToolTipText(u"Dvě hadí spirály; hustota mění jiskry obalu."
			if serpent else self._StyleText(self._BodyStyleLabels(), self.draft[11]))
		self._SyncEnabledStates()

	def _SyncColor(self):
		appearance.MetinQueueAppearanceController._SyncColor(self)
		red, green, blue = UnpackRgb(self.draft[15])
		self.page.GetChild("AccentSwatch").SetColor(grp.GenerateColor(red / 255.0, green / 255.0, blue / 255.0, 1.0))

	def OpenAccentPicker(self):
		if self.draft is not None:
			self.colorPicker.Open(self.draft[15], self._SetAccent, self._DefaultAccent)

	def _SetAccent(self, rgb):
		self.draft[15] = int(rgb) & 0xFFFFFF
		self._SyncColor()
		self._UpdatePreview()

	def _DefaultAccent(self):
		self._SetAccent(self.backend.Defaults()[15])

	def SetPreset(self, index):
		if self.draft is None:
			return
		self.colorPicker.Cancel()
		self.draft = list(self.backend.Normalize(presets.PRESETS[index][2]))
		self._SyncUi()
		self._UpdatePreview()

	def SetModel(self, vnum):
		if vnum not in presets.MODEL_VNUMS:
			return
		self.previewVnum = vnum
		self._RemovePreview()
		self._CreatePreview()
		self.page.RefreshSummary()

	def Apply(self):
		applied = appearance.MetinQueueAppearanceController.Apply(self)
		if self.page:
			if applied:
				self.page.SetStatus(u"Uloženo v relaci náhledu." if self.backend.offline else u"Nastavení fronty uloženo.")
			else:
				self.page.SetStatus(u"Nastavení se nepodařilo uložit. Návrh zůstává otevřený.")
		return applied

	def _UpdatePreview(self):
		appearance.MetinQueueAppearanceController._UpdatePreview(self)
		if self.page:
			self.page.RefreshSummary()

	def _CreatePreview(self):
		appearance.MetinQueueAppearanceController._CreatePreview(self)
		if self.page and self.previewIndex is None:
			self.page.SetStatus(u"Náhled nelze načíst. Zkontrolujte shodu klienta a balíčků.")


class MetinQueueEditor(ui.BoardWithTitleBar):
	"""The same native controls and render target in game and in the offline host."""
	def __new__(cls, backend=None, onClose=None):
		if appearance.HasDesignV3():
			from uimetinqueuedesigneditor import MetinQueueDesignEditor
			return MetinQueueDesignEditor(backend, onClose)
		return object.__new__(cls)

	def __init__(self, backend=None, onClose=None):
		ui.BoardWithTitleBar.__init__(self)
		self.backend = backend or presets.GameBackend()
		if self.backend.version < 2:
			raise RuntimeError("Meteor queue editor requires appearance API v2")
		self.closeEvent = onClose
		self.widgets = {}
		self.children = []
		self.panes = []
		self.tabs = []
		self.presetButtons = []
		self.activePane = 0
		self.controller = None
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName(u"Náhled fronty meteorů" if self.backend.offline else u"Editor fronty meteorů")
		self.SetCloseEvent(self.Close)
		self._Build()
		self._BindController()

	def _BindController(self):
		self.controller = EditorController(self.backend)
		if not self.controller.Bind(self, self.Close):
			raise RuntimeError("Meteor queue editor widget binding failed")
		self.GetChild("MainColorButton").SetEvent(self.controller.OpenColorPicker)
		self.GetChild("AccentColorButton").SetEvent(self.controller.OpenAccentPicker)

	def GetChild(self, name):
		return self.widgets[name]

	def _Keep(self, widget, parent, x, y, name=None):
		widget.SetParent(parent)
		widget.SetPosition(int(x), int(y))
		widget.Show()
		self.children.append(widget)
		if name:
			self.widgets[name] = widget
		return widget

	def _Text(self, parent, x, y, text, name=None):
		widget = self._Keep(ui.TextLine(), parent, x, y, name)
		widget.AddFlag("not_pick")
		widget.SetText(text)
		return widget

	def _Button(self, parent, x, y, text, event, family="88x21", name=None):
		widget = self._Keep(ui.Button(), parent, x, y, name)
		uicrimsoncontrols.ApplyVisuals(widget, family)
		widget.SetText(text)
		widget.SetEvent(event)
		return widget

	def _Toggle(self, parent, x, y, text, name):
		widget = self._Keep(ui.ToggleButton(), parent, x, y, name)
		widget.SetUpVisual("d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_unselected.tga")
		widget.SetOverVisual("d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_hover.tga")
		widget.SetDownVisual("d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_selected.tga")
		self._Text(parent, x + 22, y + 1, text)
		return widget

	def _Slider(self, pane, y, name, label):
		self._Text(pane, 0, y, label, name + "Label").SetLimitWidth(236)
		value = self._Text(pane, 236, y + 9, "100%", name + "Value")
		value.SetHorizontalAlignRight()
		self._Keep(ui.SliderBar(), pane, 0, y + 13, name + "Slider")

	def _Build(self):
		width = min(820, max(600, wndMgr.GetScreenWidth() - 24))
		height = min(620, max(456, wndMgr.GetScreenHeight() - 24))
		self.SetSize(width, height)
		self.layoutScreen = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		leftWidth = width - 292
		rightX = width - 260
		presetX = (width - (6 * 88 + 5 * 4)) // 2
		for index, (key, label, values) in enumerate(presets.PRESETS):
			button = self._Button(self, presetX + index * 92, 37, label,
				lambda selected=index: self.controller.SetPreset(selected))
			self.presetButtons.append(button)
		self._Button(self, 16, 65, u"Model", self._CycleModel, "199x27", "ModelButton")
		self._Button(self, 223, 68, u"Kamera", self._ResetCamera, "61x21").SetToolTipText(u"Obnovit polohu a přiblížení náhledu")

		frame = self._Keep(ui.Bar(), self, 16, 100, "PreviewFrame")
		frame.SetSize(leftWidth, height - 205)
		frame.SetColor(grp.GenerateColor(0.035, 0.026, 0.035, 1.0))
		preview = self._Keep(ui.WikiRenderTargetUi(), frame, 2, 2, "MetinQueuePreview")
		preview.SetSize(leftWidth - 4, height - 209)
		preview.Hide()
		inputWindow = self._Keep(ui.Window(), frame, 2, 2, "PreviewInput")
		inputWindow.SetSize(leftWidth - 4, height - 209)
		hints = self._Keep(ui.Window(), self, 16, height - 99, "PreviewInstructions")
		hints.SetSize(leftWidth, 34)
		self._Text(hints, 0, 0, u"Levé: posun. Pravé: otočení.").SetLimitWidth(leftWidth)
		self._Text(hints, 0, 16, u"Kolečko: přiblížení. Kamera: reset.").SetLimitWidth(leftWidth)
		self._Toggle(self, 16, height - 61, u"Blízké meteory (40 m)", "NearbyFillToggle")
		if self.backend.offline:
			self.GetChild("NearbyFillToggle").SetToolTipText(u"Součást exportu; offline scéna nezobrazuje okolní svět.")

		self._Button(self, rightX, 100, u"Hlavní barva", lambda: None, name="MainColorButton")
		self._Button(self, rightX + 124, 100, u"Akcent", lambda: None, name="AccentColorButton")
		self.GetChild("AccentColorButton").SetToolTipText(u"Barva jisker nových stylů obalu")
		for name, x in (("ColorSwatch", rightX + 93), ("AccentSwatch", rightX + 217)):
			swatch = self._Keep(ui.Bar(), self, x, 101, name)
			swatch.SetSize(22, 19)
		self._Toggle(self, rightX, 131, u"Obal", "BodyToggle")
		self._Toggle(self, rightX + 124, 131, u"Kruh", "RingToggle")
		for index, label in enumerate((u"Obal", u"Kruh", u"Pohyb")):
			self.tabs.append(self._Button(self, rightX + index * 81, 158, label,
				lambda selected=index: self._SetPane(selected), "78x21"))
		for unused in range(3):
			pane = self._Keep(ui.Window(), self, rightX, 190)
			pane.SetSize(244, height - 267)
			self.panes.append(pane)
		body, ring, motion = self.panes
		self._Text(body, 0, 3, u"Styl obalu")
		self._Button(body, 148, 0, "", lambda: None, name="BodyStyleButton")
		self._Text(ring, 0, 3, u"Styl kruhu")
		self._Button(ring, 148, 0, "", lambda: None, name="RingStyleButton")
		for row, (name, label) in enumerate((
			("BodyReach", u"Výška"), ("BodyStretch", u"Poloměr / roztažení"),
			("BodyDensity", u"Hustota"), ("BodyFill", u"Šířka proudů / výplň"),
			("BodyIntensity", u"Jas"), ("BodyGap", u"Odstup od kamene"),
		)):
			self._Slider(body, 28 + row * 27, name, label)
		for row, (name, label) in enumerate((
			("RingDiameter", u"Průměr"), ("RingThickness", u"Jas"),
			("RingLineWidth", u"Šířka čar"), ("RingGap", u"Odstup od kamene"),
		)):
			self._Slider(ring, 28 + row * 35, name, label)
		self._Toggle(motion, 0, 4, u"Jiskry", "SparksToggle")
		self._Toggle(motion, 124, 4, u"Pulzování", "PulseToggle")
		self._Slider(motion, 40, "SparkDensity", u"Hustota jisker")
		self._Slider(motion, 80, "AnimationSpeed", u"Rychlost animace")
		self._Text(motion, 0, 127, u"Změny se zobrazují v náhledu.")
		self._Text(motion, 0, 144, u"Použít uloží celý návrh.")
		self._Text(self, rightX, height - 66, "", "Status").SetLimitWidth(244)
		self._Button(self, 16, height - 33, u"Výchozí", lambda: None, name="RestoreDefaultsButton")
		if self.backend.offline:
			self._Button(self, 112, height - 33, u"Export JSON", self.Export, "100x21").SetToolTipText(u"Uložit návrh do UserData/queue-viewer")
		for name, label, x in (("ApplyButton", u"Použít", width - 292),
			("OkButton", u"OK", width - 196), ("CancelButton", u"Zrušit", width - 100)):
			self._Button(self, x, height - 33, label, lambda: None, name=name)
		self._SetPane(0)

	def _SetPane(self, index):
		self.activePane = index
		for number, pane in enumerate(self.panes):
			if number == index:
				pane.Show()
			else:
				pane.Hide()
			self.tabs[number].SetUpVisual(uicrimsoncontrols.Visual("78x21", "selected" if number == index else "normal"))

	def _CycleModel(self):
		index = presets.MODEL_VNUMS.index(self.controller.previewVnum)
		self.controller.SetModel(presets.MODEL_VNUMS[(index + 1) % len(presets.MODEL_VNUMS)])

	def _ResetCamera(self):
		self.controller.SetModel(self.controller.previewVnum)

	def RefreshSummary(self):
		if not self.controller or self.controller.draft is None:
			return
		draft = tuple(self.controller.draft)
		for index, button in enumerate(self.presetButtons):
			selected = draft == presets.PRESETS[index][2]
			button.SetUpVisual(uicrimsoncontrols.Visual("88x21", "selected" if selected else "normal"))
		vnum = self.controller.previewVnum
		name = nonplayer.GetMonsterName(vnum) or (u"Meteor %d" % vnum)
		self.GetChild("ModelButton").SetText(name)
		self.GetChild("ModelButton").SetToolTipText(u"%s (%d) — přepnout model" % (name, vnum))
		if self.controller.previewIndex is None:
			return
		changed = draft != self.controller.original or self.controller.draftNearbyFill != self.controller.originalNearbyFill
		self.SetStatus(u"Rozepsaný návrh" if changed else (u"Samostatný náhled" if self.backend.offline else u"Uložené nastavení"))

	def SetStatus(self, text):
		self.GetChild("Status").SetText(text)
		# Full failure messages remain accessible even in the compact screen size.
		self.GetChild("ApplyButton").SetToolTipText(text)

	def Open(self, draft=None, nearby=None):
		self.controller.BeginSession()
		if draft is not None:
			self.controller.draft = list(self.backend.Normalize(draft))
			self.controller.draftNearbyFill = 1 if nearby else 0
			self.controller._SyncUi()
			self.controller._UpdatePreview()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()
		self.SetFocus()

	def Close(self):
		if self.controller:
			self.controller.Discard()
		self.KillFocus()
		self.Hide()
		if self.closeEvent:
			self.closeEvent()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		screen = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		if screen == self.layoutScreen or not self.controller or self.controller.draft is None:
			return
		# Keep the draft while rebuilding only UI/target dimensions after a resize.
		draft = tuple(self.controller.draft)
		nearby = self.controller.draftNearbyFill
		vnum, pane = self.controller.previewVnum, self.activePane
		self.controller.Destroy()
		self.controller = None
		self.metinQueueAppearanceController = None
		for child in self.children:
			child.Hide()
		self.children = []
		self.widgets = {}
		self.panes, self.tabs, self.presetButtons = [], [], []
		self._Build()
		self._BindController()
		self.controller.previewVnum = vnum
		self.Open(draft, nearby)
		self._SetPane(pane)

	def Destroy(self):
		if self.controller:
			self.controller.Destroy()
		self.controller = None
		self.metinQueueAppearanceController = None
		self.closeEvent = None
		self.Hide()
		self.widgets.clear()
		self.children = []
		self.panes = []
		self.tabs = []
		self.presetButtons = []

	def Export(self):
		if not self.backend.offline or self.controller.draft is None:
			return
		values = self.backend.Normalize(self.controller.draft)
		payload = {
			"schema": "althea.metin-queue-appearance", "version": 2,
			"appearance": list(values),
			"fields": dict(zip(presets.FIELD_NAMES, values)),
			"nearbyFillEnabled": self.controller.draftNearbyFill,
			"previewVnum": self.controller.previewVnum,
		}
		# No user-selected paths and no write through the pack-aware open shim.
		directory = os.path.join("UserData", "queue-viewer")
		try:
			if not os.path.isdir(directory):
				os.makedirs(directory)
			stem = "appearance-" + time.strftime("%Y%m%d-%H%M%S")
			for suffix in range(1000):
				filename = stem + ("-%d" % suffix if suffix else "") + ".json"
				path = os.path.join(directory, filename)
				try:
					with old_open(path, "x") as output:
						output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
					self.SetStatus(u"Export: " + filename)
					return
				except FileExistsError:
					continue
			raise IOError("No unused queue-viewer export filename")
		except (IOError, OSError, TypeError, ValueError):
			self.SetStatus(u"Export do UserData/queue-viewer se nezdařil.")
