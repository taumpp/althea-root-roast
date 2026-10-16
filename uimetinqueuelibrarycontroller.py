import dbg
import grp
import nonplayer
import ui
import uicrimsoncontrols
import WikiRenderTarget
import wndMgr
import systemSetting
import uimetinqueueappearance as appearance
from uicolorpicker import UnpackRgb

import metinqueuelibrary as design


def _Ranges(preset):
	return design.Ranges(preset) if hasattr(design, "Ranges") else design.RANGES


def _Rings(preset=None):
	return design.RingChoices(preset) if hasattr(design, "RingChoices") else design.RING_STYLE_CHOICES


def _ValueText(field, value):
	return design.DisplayValue(field, value)


class DesignController(appearance.MetinQueueAppearanceController):
	"""Reuse the existing native camera gestures, with an independent design session."""
	def __init__(self, page, backend):
		appearance.MetinQueueAppearanceController.__init__(self, backend)
		self.page = page
		self.profiles = {}
		self.originalProfiles = {}
		self.previewCurrent = False
		self.previewNeedsSelection = False
		self.resetAllPending = False
		self.undoReset = None
		self._BindPreview()

	def _BindPreview(self):
		self.preview = self.page.widgets["Preview"]
		self.previewInput = self.page.widgets["PreviewInput"]
		for eventName, callback in (
			("OnMouseLeftButtonDown", self._StartPreviewPan),
			("OnMouseLeftButtonUp", self._StopPreviewDrag),
			("OnMouseRightButtonDown", self._StartPreviewOrbit),
			("OnMouseRightButtonUp", self._StopPreviewDrag),
			("OnMouseWheel", self.OnMouseWheel),
		):
			setattr(self.previewInput, eventName, ui.__mem_func__(callback))

	def BeginSession(self, draft=None, nearby=None):
		self.Discard()
		try:
			self.original = self.backend.Read()
			self.originalProfiles = self.backend.Profiles()
			self.originalProfiles[self.original[0]] = self.original
			self.originalNearbyFill = self.backend.ReadNearby()
		except (AttributeError, RuntimeError, TypeError, ValueError, OSError):
			self.page.SetStatus(u"Nastavení nelze načíst. Zavřete a znovu otevřete editor.")
			return False
		self.profiles = dict((key, list(values)) for key, values in self.originalProfiles.items())
		self.draftNearbyFill = self.originalNearbyFill if nearby is None else (1 if nearby else 0)
		selected = self.original[design.PRESET]
		if draft is not None and len(draft) == len(design.DEFAULT):
			values = self.backend.Normalize(draft)
			selected = values[design.PRESET]
			self.profiles[selected] = list(values)
		self.draft = self.profiles[selected]
		self.page.syncedPreset = None
		self._SyncUi()
		self._CreatePreview()
		return True

	def Discard(self):
		self.colorPicker.Cancel()
		self._RemovePreview()
		if hasattr(design, "ClearPreview"):
			design.ClearPreview()
		self.profiles = {}
		self.originalProfiles = {}
		self.draft = None
		self.original = None
		self.resetAllPending = False
		self.undoReset = None

	def Destroy(self):
		self.Discard()
		self.page = None
		self.preview = None
		self.previewInput = None

	def Select(self, preset):
		if self.draft is None or preset not in self.profiles:
			self.page.SetStatus(u"Tento efekt čeká na převedení do testovacího klienta.")
			return
		self._SampleSliders()
		self.colorPicker.Cancel()
		changedPreset = self.draft[design.PRESET] != preset
		self.draft = self.profiles[preset]
		self._SyncUi()
		self._UpdatePreview(reframe=changedPreset)

	def Apply(self):
		if self.draft is None:
			return False
		self._SampleSliders()
		try:
			committed, nearby = self.backend.ApplyProfiles(self.profiles,
				self.draft[design.PRESET], self.draftNearbyFill)
		except (AttributeError, RuntimeError, TypeError, ValueError, OSError):
			self.page.SetStatus(u"Uložení se nezdařilo. Rozepsané návrhy zůstávají otevřené.")
			return False
		self.original = committed
		self.originalProfiles = dict((key, self.backend.Normalize(values))
			for key, values in self.profiles.items())
		self.profiles = dict((key, list(values)) for key, values in self.originalProfiles.items())
		self.resetAllPending = False
		self.undoReset = None
		self.originalProfiles[committed[0]] = committed
		self.profiles[committed[0]] = list(committed)
		self.draft = self.profiles[committed[0]]
		self.originalNearbyFill = nearby
		self.draftNearbyFill = nearby
		self._SyncUi()
		self._UpdatePreview()
		if self.previewCurrent:
			self.page.SetStatus(u"Nastavení uloženo.")
		return True

	def _RememberReset(self):
		self._SampleSliders()
		self.undoReset = (dict((key, list(values)) for key, values in self.profiles.items()),
			self.draft[design.PRESET], self.draftNearbyFill)

	def RestoreAllDefaults(self):
		if self.draft is None:
			return
		self._RememberReset()
		self.colorPicker.Cancel()
		self.profiles[28] = list(self.backend.Defaults(28))
		self.draft = self.profiles[28]
		self._SyncUi()
		self._UpdatePreview(reframe=True)

	def RestoreDefaults(self):
		if self.draft is None:
			return
		self._RememberReset()
		self.colorPicker.Cancel()
		preset, ring = self.draft[design.PRESET], self.draft[design.RING_STYLE]
		self.profiles[preset] = list(self.backend.Defaults(preset))
		self.draft = self.profiles[preset]
		self.draft[design.RING_STYLE] = ring
		self._SyncUi()
		self._UpdatePreview()

	def UndoReset(self):
		if self.undoReset is None:
			return
		self.colorPicker.Cancel()
		self.profiles, selected, self.draftNearbyFill = self.undoReset
		self.draft = self.profiles[selected]
		self.undoReset = None
		self._SyncUi()
		self._UpdatePreview(reframe=True)

	def SetValue(self, field, value):
		if self._syncing or self.draft is None or not design.Supports(self.draft[0], field, self.draft):
			return
		self.draft[field] = value
		if field == design.RING_STYLE:
			self.draft[design.RING_ENABLED] = 1
		if field in (design.PRIMARY, design.ACCENT) or (field == design.ACCENT_ENABLED and value):
			if self.draft[design.COLOR_STRENGTH] == 0:
				self.draft[design.COLOR_STRENGTH] = 100
		self.draft[:] = self.backend.Normalize(self.draft)
		self._SyncUi()
		self._UpdatePreview()

	def Cycle(self, field, choices):
		if self.draft is None:
			return
		values = [entry[0] for entry in choices]
		self.SetValue(field, values[(values.index(self.draft[field]) + 1) % len(values)])

	def OpenColor(self, field):
		if self.draft is None or not design.Supports(self.draft[0], field, self.draft):
			return
		if field == design.ACCENT and not self.draft[design.ACCENT_ENABLED]:
			return
		preset = self.draft[design.PRESET]
		self.colorPicker.Open(self.draft[field],
			lambda rgb: self.SetValue(field, rgb),
			lambda: self.SetValue(field, self.backend.Defaults(preset)[field]))

	def SetNearby(self, enabled):
		if self._syncing or self.draft is None:
			return
		self.draftNearbyFill = 1 if enabled else 0
		self.page.RefreshStatus()

	def _SampleSliders(self):
		if self._syncing or self.draft is None:
			return False
		changed = False
		for field, (pane, row, slider, valueText) in self.page.sliders.items():
			if pane != self.page.activePane or not design.Supports(self.draft[0], field, self.draft):
				continue
			minimum, maximum = _Ranges(self.draft[0])[field]
			raw = appearance.SliderToPercent(slider.GetSliderPos(), minimum, maximum)
			step = design.STEPS.get(field, 1)
			value = min(maximum, minimum + ((raw - minimum + step // 2) // step) * step)
			if value != self.draft[field]:
				self.draft[field] = value
				valueText.SetText(_ValueText(field, value))
				changed = True
		if changed:
			self._UpdatePreview()
		return changed

	def _SyncUi(self):
		if self.draft is None:
			return
		self._syncing = True
		try:
			self.page.Sync()
		finally:
			self._syncing = False

	def _CreatePreview(self):
		if self.draft is None:
			return
		try:
			# This API reserves an ID in [minimum, maximum), not a texture size.
			# SetRenderTarget allocates the texture from the widget dimensions.
			index = int(WikiRenderTarget.GetFreeIndex(164, 236))
			if index < 1:
				raise RuntimeError("no free render-target index")
			self.previewIndex = index
			self.preview.SetRenderTarget(index)
			WikiRenderTarget.SetBackground(index, "d:/ymir work/ui/render_target/render_target_bg.dds")
			if not design.SelectPreview(index, self.previewVnum, self.draft):
				raise RuntimeError("preview model could not be selected")
			WikiRenderTarget.SetVisibility(index, True)
			self.preview.Show()
			self.previewCurrent = True
			self.previewNeedsSelection = False
			self.page.RefreshStatus()
		except (AttributeError, RuntimeError, TypeError, ValueError, OSError) as error:
			dbg.TraceError("[MetinQueueDesign] Preview unavailable: %s" % error)
			self._RemovePreview()
			self.page.SetStatus(u"Náhled nelze načíst. Je potřeba odpovídající klient a balíčky.")

	def _UpdatePreview(self, reframe=False):
		if self.draft is None:
			return
		self.previewNeedsSelection = self.previewNeedsSelection or reframe
		if self.previewIndex is None:
			self._CreatePreview()
			return
		try:
			# A different body frames its full extent. Tuning the same body uses
			# Set in place, retaining the camera and running particle animation.
			updated = (design.SelectPreview(self.previewIndex, self.previewVnum, self.draft)
				if self.previewNeedsSelection else design.UpdatePreview(self.previewIndex, self.draft))
			if updated:
				if self.previewNeedsSelection:
					self.previewPitch = self.previewYaw = 0.0
					self._StopPreviewDrag()
				self.previewCurrent = True
				self.previewNeedsSelection = False
				self.page.RefreshStatus()
				return
		except (AttributeError, RuntimeError, TypeError, ValueError, OSError):
			pass
		# A temporary update failure must not destroy the actor or its camera.
		# The next interaction retries the same native target in place.
		self.previewCurrent = False
		self.page.SetStatus(u"Náhled čeká na aktualizaci. Další změna ji zkusí znovu.")

	def _RemovePreview(self):
		appearance.MetinQueueAppearanceController._RemovePreview(self)
		self.previewCurrent = False
		self.previewNeedsSelection = False
		if getattr(self, "preview", None):
			self.preview.Hide()

	def SetModel(self, vnum):
		if vnum not in design.MODEL_VNUMS or self.draft is None:
			return
		self.previewVnum = vnum
		self._RemovePreview()
		self._CreatePreview()
		self.page.SyncModel()


