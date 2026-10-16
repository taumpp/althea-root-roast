import app
import dbg
import grp
import systemSetting
import ui
import uiScriptLocale
import WikiRenderTarget
import wndMgr
import metinqueuepresets

from uicolorpicker import ColorPickerDialog, UnpackRgb


BODY_STRETCH_RANGE = (25, 300)
BODY_REACH_RANGE = (25, 500)
BODY_DENSITY_RANGE = (25, 300)
BODY_FILL_RANGE = (25, 300)
BODY_INTENSITY_RANGE = (25, 300)
RING_DIAMETER_RANGE = (25, 300)
RING_THICKNESS_RANGE = (25, 300)
BODY_GAP_RANGE = (0, 100)
RING_GAP_RANGE = (0, 100)

BODY_STYLE_CONTINUOUS = 0
BODY_STYLE_PULSE = 1
RING_STYLE_CLASSIC = 0
RING_STYLE_WAVE = 1
RING_STYLE_DOUBLE = 2
BODY_STYLE_RANGE = (0, 1)
RING_STYLE_RANGE = (0, 2)

DEFAULT_APPEARANCE = (
	1, 1, 0, 0, 100, 100, 100, 100, 100, 100, 100,
	BODY_STYLE_CONTINUOUS, RING_STYLE_CLASSIC, 0, 0,
)
APPEARANCE_PERCENT_RANGES = {
	4: BODY_STRETCH_RANGE,
	5: BODY_DENSITY_RANGE,
	6: BODY_INTENSITY_RANGE,
	7: RING_DIAMETER_RANGE,
	8: RING_THICKNESS_RANGE,
	9: BODY_REACH_RANGE,
	10: BODY_FILL_RANGE,
	13: BODY_GAP_RANGE,
	14: RING_GAP_RANGE,
}
DEFAULT_NEARBY_FILL_ENABLED = 1
AUTHORED_COLOR_PREVIEW = 0xAD3DFF
PREVIEW_VNUM = 8001
PREVIEW_ROTATION_SENSITIVITY = 0.45
PREVIEW_PITCH_LIMIT = 65.0
PREVIEW_DRAG_NONE = 0
PREVIEW_DRAG_PAN = 1
PREVIEW_DRAG_ORBIT = 2
IMG_DIR = "d:/ymir work/ui/game/crimson_ember/gameoption/"
BODY_STYLE_LABELS = (
	("OPTION_METIN_QUEUE_BODY_STYLE_CONTINUOUS", "Continuous"),
	("OPTION_METIN_QUEUE_BODY_STYLE_PULSE", "Pulse"),
)
RING_STYLE_LABELS = (
	("OPTION_METIN_QUEUE_RING_STYLE_CLASSIC", "Classic"),
	("OPTION_METIN_QUEUE_RING_STYLE_WAVE", "Wave"),
	("OPTION_METIN_QUEUE_RING_STYLE_DOUBLE", "Double"),
)


def SliderToPercent(position, minimum, maximum):
	position = max(0.0, min(1.0, float(position)))
	return int(round(minimum + position * (maximum - minimum)))


def PercentToSlider(value, minimum, maximum):
	value = max(minimum, min(maximum, int(value)))
	return float(value - minimum) / float(maximum - minimum)


def NormalizeAppearance(values):
	try:
		result = list(values)
	except TypeError:
		return DEFAULT_APPEARANCE
	if len(result) < 9 or len(result) > len(DEFAULT_APPEARANCE):
		return DEFAULT_APPEARANCE
	result.extend(DEFAULT_APPEARANCE[len(result):])
	try:
		result[0] = 1 if result[0] else 0
		result[1] = 1 if result[1] else 0
		result[2] = 1 if result[2] else 0
		result[3] = int(result[3]) & 0xFFFFFF if result[2] else 0
		for index, bounds in APPEARANCE_PERCENT_RANGES.items():
			result[index] = max(bounds[0], min(bounds[1], int(result[index])))
		result[11] = max(
			BODY_STYLE_RANGE[0],
			min(BODY_STYLE_RANGE[1], int(result[11])),
		)
		result[12] = max(
			RING_STYLE_RANGE[0],
			min(RING_STYLE_RANGE[1], int(result[12])),
		)
	except (TypeError, ValueError):
		return DEFAULT_APPEARANCE
	return tuple(result)


def _Locale(name, fallback):
	return getattr(uiScriptLocale, name, fallback)


def HasDesignV3():
	if hasattr(systemSetting, "SetQueueSpiritPreviewDraft"):
		return True
	# Keep V1/V2 hosts independent of V3 modules until both native bridges exist.
	try:
		if (systemSetting.GetMetinQueueDesignVersion() < 3
			or WikiRenderTarget.GetMetinQueueDesignVersion() < 3):
			return False
	except (AttributeError, TypeError, RuntimeError):
		return False
	import metinqueuedesign
	return metinqueuedesign.HasV3()


class MetinQueueAppearanceController(object):
	REQUIRED_WIDGET_NAMES = (
		"ColorSwatch",
		"PreviewFrame",
		"MetinQueuePreview",
		"PreviewInput",
		"PreviewInstructions",
		"BodyToggle",
		"RingToggle",
		"NearbyFillToggle",
		"BodyStyleButton",
		"RingStyleButton",
		"ApplyButton",
		"OkButton",
		"CancelButton",
		"RestoreDefaultsButton",
	)
	SLIDER_BINDINGS = (
		("BodyReachSlider", "BodyReachValue", 9, BODY_REACH_RANGE),
		("BodyStretchSlider", "BodyStretchValue", 4, BODY_STRETCH_RANGE),
		("BodyDensitySlider", "BodyDensityValue", 5, BODY_DENSITY_RANGE),
		("BodyFillSlider", "BodyFillValue", 10, BODY_FILL_RANGE),
		("BodyIntensitySlider", "BodyIntensityValue", 6, BODY_INTENSITY_RANGE),
		("BodyGapSlider", "BodyGapValue", 13, BODY_GAP_RANGE),
		("RingDiameterSlider", "RingDiameterValue", 7, RING_DIAMETER_RANGE),
		("RingGapSlider", "RingGapValue", 14, RING_GAP_RANGE),
		("RingThicknessSlider", "RingThicknessValue", 8, RING_THICKNESS_RANGE),
	)

	def __init__(self, backend=None):
		self.backend = backend or metinqueuepresets.GameBackend()
		self.designEntry = None
		self.previewVnum = PREVIEW_VNUM
		self.editor = None
		self.page = None
		self.closeOwner = None
		self.original = None
		self.draft = None
		self.originalNearbyFill = DEFAULT_NEARBY_FILL_ENABLED
		self.draftNearbyFill = DEFAULT_NEARBY_FILL_ENABLED
		self.previewIndex = None
		self.previewDragMode = PREVIEW_DRAG_NONE
		self.lastMouseX = 0
		self.lastMouseY = 0
		self.previewPitch = 0.0
		self.previewYaw = 0.0
		self._syncing = False
		self.colorPicker = ColorPickerDialog()
		self.sliders = []
		self.bodySliders = []
		self.ringSliders = []
		self.bodyToggle = None
		self.ringToggle = None
		self.nearbyFillToggle = None
		self.bodyStyleButton = None
		self.ringStyleButton = None
		self.previewInput = None

	def _GetRequiredWidgets(self, scriptWindow):
		names = list(self.REQUIRED_WIDGET_NAMES)
		for sliderName, valueName, unusedIndex, unusedRange in self.SLIDER_BINDINGS:
			names.append(sliderName)
			names.append(valueName)
		widgets = {}
		try:
			for name in names:
				widgets[name] = scriptWindow.GetChild(name)
		except KeyError as error:
			missingName = error.args[0] if error.args else "unknown"
			dbg.TraceError(
				"Metin queue appearance disabled: incompatible UIScript "
				"(missing %s)" % missingName
			)
			return None
		return widgets

	def Bind(self, scriptWindow, closeOwner):
		if HasDesignV3():
			from uimetinqueuedesigneditor import DesignOptionsEntry
			self.designEntry = DesignOptionsEntry(scriptWindow, closeOwner, self.backend)
			scriptWindow.metinQueueAppearanceController = self
			return True
		widgets = self._GetRequiredWidgets(scriptWindow)
		if widgets is None:
			return False
		self.page = scriptWindow
		self.closeOwner = closeOwner
		self.colorSwatch = widgets["ColorSwatch"]
		self.previewFrame = widgets["PreviewFrame"]
		self.preview = widgets["MetinQueuePreview"]
		self.previewInput = widgets["PreviewInput"]
		self.previewInstructions = widgets["PreviewInstructions"]
		self.bodyToggle = widgets["BodyToggle"]
		self.ringToggle = widgets["RingToggle"]
		self.nearbyFillToggle = widgets["NearbyFillToggle"]
		self.bodyStyleButton = widgets["BodyStyleButton"]
		self.ringStyleButton = widgets["RingStyleButton"]
		for toggle, event in (
			(self.bodyToggle, ui.__mem_func__(self._OnBodyToggle)),
			(self.ringToggle, ui.__mem_func__(self._OnRingToggle)),
			(self.nearbyFillToggle,
			 ui.__mem_func__(self._OnNearbyFillToggle)),
		):
			toggle.SetToggleUpEvent(event)
			toggle.SetToggleDownEvent(event)
		for widget in (
			self.previewFrame,
			self.preview,
			self.colorSwatch,
		):
			widget.SetClippingMaskWindow(scriptWindow)

		self.sliders = []
		for sliderName, valueName, tupleIndex, valueRange in self.SLIDER_BINDINGS:
			slider = widgets[sliderName]
			valueText = widgets[valueName]
			slider.SetEvent(lambda index=tupleIndex, bounds=valueRange: self._OnSlider(index, bounds))
			if hasattr(slider, "SetButtonVisual"):
				slider.SetButtonVisual(IMG_DIR + "slider/", "small_thumb_01.tga", "small_thumb_02.tga", "small_thumb_03.tga")
				slider.SetBackgroundVisual(IMG_DIR + "slider/small_track.tga")
			self.sliders.append((slider, valueText, tupleIndex, valueRange))
		self.bodySliders = [
			entry[0] for entry in self.sliders
			if entry[2] in (9, 4, 5, 10, 6, 13)
		]
		self.ringSliders = [
			entry[0] for entry in self.sliders
			if entry[2] in (7, 14, 8)
		]
		self.bodyStyleButton.SetEvent(ui.__mem_func__(self._CycleBodyStyle))
		self.ringStyleButton.SetEvent(ui.__mem_func__(self._CycleRingStyle))

		self.colorSwatch.SetMouseLeftButtonDownEvent(
			ui.__mem_func__(self.OpenColorPicker)
		)
		widgets["ApplyButton"].SetEvent(ui.__mem_func__(self.Apply))
		widgets["OkButton"].SetEvent(ui.__mem_func__(self.Ok))
		widgets["CancelButton"].SetEvent(ui.__mem_func__(self.Cancel))
		widgets["RestoreDefaultsButton"].SetEvent(ui.__mem_func__(self.RestoreDefaults))

		self.previewInput.OnMouseLeftButtonDown = ui.__mem_func__(
			self._StartPreviewPan
		)
		self.previewInput.OnMouseLeftButtonUp = ui.__mem_func__(
			self._StopPreviewDrag
		)
		self.previewInput.OnMouseRightButtonDown = ui.__mem_func__(
			self._StartPreviewOrbit
		)
		self.previewInput.OnMouseRightButtonUp = ui.__mem_func__(
			self._StopPreviewDrag
		)
		self.previewInput.OnUpdate = ui.__mem_func__(self.OnUpdate)
		self.previewInput.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)
		scriptWindow.metinQueueAppearanceController = self
		try:
			entry = scriptWindow.GetChild("OpenEditorButton")
			if self.backend.version >= 2:
				entry.SetEvent(ui.__mem_func__(self.OpenEditor))
				entry.Show()
			else:
				entry.Hide()
		except KeyError:
			pass
		return True

	def OpenEditor(self):
		if self.designEntry:
			self.designEntry.OpenEditor()
			return
		if self.backend.version < 2 or self.draft is None:
			return
		import uimetinqueueeditor
		draft, nearby = tuple(self.draft), self.draftNearbyFill
		if self.closeOwner:
			self.closeOwner()
		else:
			self.Discard()
		if self.editor is None:
			self.editor = uimetinqueueeditor.MetinQueueEditor(self.backend)
		self.editor.Open(draft, nearby)

	def BeginSession(self):
		if self.designEntry:
			self.designEntry.BeginSession()
			return
		if not self.page:
			return
		self._RemovePreview()
		try:
			committed = self.backend.Read()
		except (AttributeError, RuntimeError, TypeError):
			committed = self.backend.Normalize(DEFAULT_APPEARANCE)
		try:
			nearbyFill = self.backend.ReadNearby()
		except (AttributeError, RuntimeError, TypeError):
			nearbyFill = DEFAULT_NEARBY_FILL_ENABLED
		self.original = committed
		self.draft = list(committed)
		self.originalNearbyFill = nearbyFill
		self.draftNearbyFill = nearbyFill
		self._SyncUi()
		self._CreatePreview()

	def Discard(self):
		if self.designEntry:
			self.designEntry.Discard()
			return
		if self.page:
			try:
				committed = self.backend.Read()
			except (AttributeError, RuntimeError, TypeError):
				committed = self.original or self.backend.Normalize(DEFAULT_APPEARANCE)
			self.original = committed
			self.draft = list(committed)
			try:
				nearbyFill = self.backend.ReadNearby()
			except (AttributeError, RuntimeError, TypeError):
				nearbyFill = self.originalNearbyFill
			self.originalNearbyFill = nearbyFill
			self.draftNearbyFill = nearbyFill
			self._SyncUi()
		self._RemovePreview()
		self.colorPicker.Cancel()

	def Destroy(self):
		if self.designEntry:
			self.designEntry.Destroy()
			self.designEntry = None
		self.Discard()
		if self.editor:
			self.editor.Destroy()
		self.editor = None
		self.bodyToggle = None
		self.ringToggle = None
		self.nearbyFillToggle = None
		self.bodyStyleButton = None
		self.ringStyleButton = None
		self.previewInput = None
		self.page = None
		self.closeOwner = None
		self.sliders = []
		self.bodySliders = []
		self.ringSliders = []

	def Apply(self):
		if self.designEntry:
			return False
		if self.draft is None:
			return False
		try:
			committed, nearbyFill = self.backend.Apply(self.draft, self.draftNearbyFill)
		except (AttributeError, RuntimeError, TypeError):
			return False
		self.original = committed
		self.draft = list(committed)
		self.originalNearbyFill = nearbyFill
		self.draftNearbyFill = nearbyFill
		self._SyncUi()
		self._UpdatePreview()
		return True

	def _CallAppearanceBridge(self, function, prefixArgs=()):
		prefixArgs = tuple(prefixArgs)
		if self.backend.version >= 2:
			return function(*(prefixArgs + tuple(self.draft)))
		lastTypeError = None
		for fieldCount in (len(self.draft), 13, 11):
			try:
				result = function(*(
					prefixArgs + tuple(self.draft[:fieldCount])
				))
			except TypeError as error:
				lastTypeError = error
				continue
			if result is not None:
				return result
		if lastTypeError is not None:
			raise lastTypeError
		return None

	def Ok(self):
		if self.Apply() and self.closeOwner:
			self.closeOwner()

	def Cancel(self):
		self.Discard()
		if self.closeOwner:
			self.closeOwner()

	def RestoreDefaults(self):
		if self.draft is None:
			return
		self.draft = list(self.backend.Defaults())
		self.draftNearbyFill = DEFAULT_NEARBY_FILL_ENABLED
		self._SyncUi()
		self._UpdatePreview()

	def _SetBodyEnabled(self, enabled):
		if self._syncing or self.draft is None:
			return
		self.draft[0] = 1 if enabled else 0
		self._SyncEnabledStates()
		self._SyncColor()
		self._UpdatePreview()

	def _SetRingEnabled(self, enabled):
		if self._syncing or self.draft is None:
			return
		self.draft[1] = 1 if enabled else 0
		self._SyncEnabledStates()
		self._SyncColor()
		self._UpdatePreview()

	def _SetNearbyFillEnabled(self, enabled):
		if self._syncing or self.draft is None:
			return
		self.draftNearbyFill = 1 if enabled else 0

	def _OnBodyToggle(self):
		if self._syncing:
			return
		self._SetBodyEnabled(self.bodyToggle.IsDown())

	def _OnRingToggle(self):
		if self._syncing:
			return
		self._SetRingEnabled(self.ringToggle.IsDown())

	def _OnNearbyFillToggle(self):
		if self._syncing:
			return
		self._SetNearbyFillEnabled(self.nearbyFillToggle.IsDown())

	def _CycleBodyStyle(self):
		if self._syncing or self.draft is None or not self.draft[0]:
			return
		self.draft[11] = (self.draft[11] + 1) % len(self._BodyStyleLabels())
		self._SyncStyleLabels()
		self._SyncColor()
		self._UpdatePreview()

	def _CycleRingStyle(self):
		if self._syncing or self.draft is None or not self.draft[1]:
			return
		self.draft[12] = (self.draft[12] + 1) % len(self._RingStyleLabels())
		self._SyncStyleLabels()
		self._SyncColor()
		self._UpdatePreview()

	def _StyleText(self, labels, index):
		key, fallback = labels[index]
		return _Locale(key, fallback)

	def _BodyStyleLabels(self):
		return BODY_STYLE_LABELS + (metinqueuepresets.NEW_STYLE_LABELS if self.backend.version >= 2 else ())

	def _RingStyleLabels(self):
		return RING_STYLE_LABELS + (metinqueuepresets.NEW_STYLE_LABELS if self.backend.version >= 2 else ())

	def _SyncStyleLabels(self):
		self.bodyStyleButton.SetText(
			self._StyleText(self._BodyStyleLabels(), self.draft[11])
		)
		self.ringStyleButton.SetText(
			self._StyleText(self._RingStyleLabels(), self.draft[12])
		)

	def _SampleSliders(self):
		if self._syncing or self.draft is None:
			return False
		changed = False
		for slider, valueText, boundIndex, boundRange in self.sliders:
			value = SliderToPercent(
				slider.GetSliderPos(), boundRange[0], boundRange[1]
			)
			if value == self.draft[boundIndex]:
				continue
			self.draft[boundIndex] = value
			valueText.SetText(self._PercentText(value))
			changed = True
		if changed:
			self._UpdatePreview()
		return changed

	def _OnSlider(self, unusedTupleIndex=None, unusedValueRange=None):
		self._SampleSliders()

	def OpenColorPicker(self):
		if self.draft is None:
			return
		initialRgb = self.draft[3] if self.draft[2] else self._AuthoredColorPreview()
		self.colorPicker.Open(initialRgb, self._SetCustomColor, self._UseAuthoredColor)

	def _AuthoredColorPreview(self):
		if self.backend.version >= 2:
			if self.draft[0] and self.draft[11] >= 2:
				return metinqueuepresets.PRESETS[self.draft[11] - 1][2][3]
			if self.draft[1] and self.draft[12] >= 3:
				return metinqueuepresets.PRESETS[self.draft[12] - 2][2][3]
		return AUTHORED_COLOR_PREVIEW

	def _SetCustomColor(self, rgb):
		if self.draft is None:
			return
		self.draft[2] = 1
		self.draft[3] = int(rgb) & 0xFFFFFF
		self._SyncColor()
		self._UpdatePreview()

	def _UseAuthoredColor(self):
		if self.draft is None:
			return
		self.draft[2] = 0
		self.draft[3] = 0
		self._SyncColor()
		self._UpdatePreview()

	def _PercentText(self, value):
		formatText = _Locale("OPTION_METIN_QUEUE_PERCENT", "%d%%")
		try:
			return formatText % int(value)
		except TypeError:
			return "%d%%" % int(value)

	def _SyncUi(self):
		if self.draft is None:
			return
		self._syncing = True
		try:
			self._SyncToggle(self.bodyToggle, bool(self.draft[0]))
			self._SyncToggle(self.ringToggle, bool(self.draft[1]))
			self._SyncToggle(
				self.nearbyFillToggle, bool(self.draftNearbyFill)
			)
			for slider, valueText, tupleIndex, valueRange in self.sliders:
				slider.SetSliderPos(PercentToSlider(self.draft[tupleIndex], valueRange[0], valueRange[1]))
				valueText.SetText(self._PercentText(self.draft[tupleIndex]))
		finally:
			self._syncing = False
		self._SyncColor()
		self._SyncStyleLabels()
		self._SyncEnabledStates()

	def _SyncToggle(self, toggle, checked):
		wasSyncing = self._syncing
		self._syncing = True
		try:
			if checked:
				toggle.Down()
			else:
				toggle.SetUp()
		finally:
			self._syncing = wasSyncing

	def _SyncEnabledStates(self):
		if self.draft[0]:
			self.bodyStyleButton.Enable()
		else:
			self.bodyStyleButton.Disable()
		for slider in self.bodySliders:
			if self.draft[0]:
				slider.Enable()
			else:
				slider.Disable()
		if self.draft[1]:
			self.ringStyleButton.Enable()
		else:
			self.ringStyleButton.Disable()
		for slider in self.ringSliders:
			if self.draft[1]:
				slider.Enable()
			else:
				slider.Disable()

	def _SyncColor(self):
		if self.draft[2]:
			rgb = self.draft[3]
		else:
			rgb = self._AuthoredColorPreview()
		red, green, blue = UnpackRgb(rgb)
		self.colorSwatch.SetColor(grp.GenerateColor(red / 255.0, green / 255.0, blue / 255.0, 1.0))

	def _CreatePreview(self):
		self.previewInstructions.Show()
		self.previewDragMode = PREVIEW_DRAG_NONE
		self.previewPitch = 0.0
		self.previewYaw = 0.0
		try:
			# This bridge takes a reserved index interval, not pixel dimensions.
			# WikiRenderTargetUi.SetRenderTarget creates the native target at its size.
			index = int(WikiRenderTarget.GetFreeIndex(164, 236))
			if index < 1:
				raise RuntimeError("no free render-target index")
			self.previewIndex = index
			self.preview.SetRenderTarget(index)
			WikiRenderTarget.SetBackground(
				index, "d:/ymir work/ui/render_target/render_target_bg.dds"
			)
			select = (WikiRenderTarget.SelectMetinQueuePreviewV2 if self.backend.version >= 2
				else WikiRenderTarget.SelectMetinQueuePreview)
			if not self._CallAppearanceBridge(
				select,
				(index, self.previewVnum),
			):
				raise RuntimeError("preview model could not be selected")
			WikiRenderTarget.SetVisibility(index, True)
			self.preview.Show()
		except (AttributeError, RuntimeError, TypeError, ValueError) as error:
			dbg.TraceError("[MetinQueueAppearance] Preview retry failed: %s" % error)
			self._RemovePreview()

	def _UpdatePreview(self):
		if self.draft is None:
			return
		if self.previewIndex is None:
			self._CreatePreview()
			return
		try:
			update = (WikiRenderTarget.SetMetinQueuePreviewAppearanceV2 if self.backend.version >= 2
				else WikiRenderTarget.SetMetinQueuePreviewAppearance)
			if self._CallAppearanceBridge(
				update,
				(self.previewIndex,),
			):
				return
		except (AttributeError, RuntimeError, TypeError):
			pass
		self._RemovePreview()

	def _RemovePreview(self):
		index = self.previewIndex
		self.previewIndex = None
		self.previewDragMode = PREVIEW_DRAG_NONE
		self.previewPitch = 0.0
		self.previewYaw = 0.0
		if index is not None:
			try:
				WikiRenderTarget.Remove(index)
			except (AttributeError, RuntimeError):
				pass

	def _StartPreviewDragMode(self, mode):
		self.previewDragMode = mode
		self.lastMouseX, self.lastMouseY = wndMgr.GetMousePosition()

	def _StartPreviewPan(self):
		self._StartPreviewDragMode(PREVIEW_DRAG_PAN)

	def _StartPreviewOrbit(self):
		self._StartPreviewDragMode(PREVIEW_DRAG_ORBIT)

	def _StopPreviewDrag(self):
		self.previewDragMode = PREVIEW_DRAG_NONE

	def OnUpdate(self):
		self._SampleSliders()
		if self.previewDragMode == PREVIEW_DRAG_NONE or self.previewIndex is None:
			return
		xMouse, yMouse = wndMgr.GetMousePosition()
		deltaX = xMouse - self.lastMouseX
		deltaY = yMouse - self.lastMouseY
		self.lastMouseX = xMouse
		self.lastMouseY = yMouse
		if self.previewDragMode == PREVIEW_DRAG_PAN:
			if deltaX or deltaY:
				width = max(1, int(self.preview.GetWidth()))
				height = max(1, int(self.preview.GetHeight()))
				try:
					WikiRenderTarget.PanMetinQueuePreview(
						self.previewIndex,
						float(deltaX) / float(width),
						float(deltaY) / float(height),
					)
				except AttributeError:
					pass
			return
		if deltaX or deltaY:
			self.previewYaw += float(deltaX) * PREVIEW_ROTATION_SENSITIVITY
			self.previewPitch = max(
				-PREVIEW_PITCH_LIMIT,
				min(
					PREVIEW_PITCH_LIMIT,
					self.previewPitch
					+ float(deltaY) * PREVIEW_ROTATION_SENSITIVITY,
				),
			)
			WikiRenderTarget.RotateEyeAroundTarget(
				self.previewIndex, self.previewPitch, self.previewYaw
			)

	def OnMouseWheel(self, nLen):
		if self.previewIndex is None:
			return False
		direction = app.CAMERA_TO_NEGATIVE if nLen > 0 else app.CAMERA_TO_POSITIVE
		WikiRenderTarget.Zoom(self.previewIndex, direction)
		return True
