# -*- coding: utf-8 -*-
"""Stone queue preview v5 (2026-10-05): the big live 3D preview of the settings page and the editor.

MeteorPreviewView  kit widgets (v5 kit): hairline frame, native render target (ui.WikiRenderTargetUi), input
                   layer, overlays (effect name, hint), the character for scale with its chip: the warrior model
                   in full colours, ONE still front view (root/meteorcharacter.py; 2026-10-06, round 3: "ne
                   otáčející se", always visible, the same however the stone is turned): it stands where the
                   default view puts it, scales with the zoom and the stone size, follows a pan and is kept
                   inside the preview - never hidden while the chip is on; the old silhouette by CHARACTER_STYLE
MeteorPreviewController
                   the existing library draft controller (uimetinqueuelibrarycontroller.DesignController: one
                   session, drafts never written before Save) plus the v5 camera:
                     - framing from meteorpreviewcamera (stone 46 % of the height, base 71 % down), set through
                       WikiRenderTarget.SetModelV3Eye / SetModelV3Target after every native selection;
                     - "Velikost kamenů ve světě" live by the camera distance (SetViewScale);
                     - wheel zoom is a factor of that distance (no native Zoom: it would fight the framing);
                     - left drag pans, right drag orbits (native PanMetinQueuePreview / RotateEyeAroundTarget),
                       slow auto rotation stays native (12 deg/s); ResetCamera() without re-creating the actor;
                     - dark studio backdrop (tools/build_meteor_preview_assets.py) instead of the wooden room.
Everything native is optional (hasattr): an older EXE keeps the native framing and still shows the preview.
Needs the v5 Althea UI kit (Chip, Section, EditField, ScrollBar, button role ruby_s).
"""
import grp
import ui
import wndMgr

import meteorcharacter as ring   # the warrior image (generated)
import meteorpreviewcamera as camera
import uikit
import uikittokens as T
from settingslocale import Text as Tr
from uimetinqueuelibrarycontroller import DesignController
import uimetinqueueappearance as appearance
import metinqueuelibrary as design

try:
    import WikiRenderTarget
except ImportError:  # offline tools
    WikiRenderTarget = None

PAN_LIMIT = 0.75            # CRenderTarget::PanMetinQueuePreview clamps each axis to +-0.75
DRAG_NONE, DRAG_PAN, DRAG_ORBIT = 0, 1, 2   # = uimetinqueueappearance.PREVIEW_DRAG_*
ROTATION_SENSITIVITY = 0.45   # = PREVIEW_ROTATION_SENSITIVITY; the tilt range is meteorpreviewcamera.PITCH_RANGE
SILHOUETTE = camera.ASSET_ROOT + 'silhouette.png'
SILHOUETTE_SIZE = (100, 192)
# 'model' = the warrior render (2026-10-06: "model válečníka" instead of the silhouette; a real 3D actor beside
# the stone needs C++ - CRenderTarget holds one model), 'silhouette' = the dark figure of 2026-10-05.
CHARACTER_STYLE = 'model'
# Real 3D warrior in the preview scene when the EXE has WikiRenderTarget.SetMetinQueueCompanion (2026-10-06):
# turns, pans and zooms with the stone. Without it the 2D image above is the fallback.
COMPANION = dict(race=0, armor=0, weapon=19, hair=0, rotation=0.0)


def NativeCompanion():
    return bool(_native('SetMetinQueueCompanion') and _native('PlaceMetinQueueCompanion'))


def CharacterArt():
    """(texture, (w, h), (feet x, feet y), px of 174 units) of the character overlay: the one front view of the
    warrior (meteorcharacter, generated) or the old flat silhouette."""
    if CHARACTER_STYLE == 'silhouette':
        w, h = SILHOUETTE_SIZE
        return SILHOUETTE, (w, h), (w * 0.5, h - 2.0), float(h - 2)
    return camera.ASSET_ROOT + ring.FRONT, ring.FRONT_SIZE, ring.FRONT_FEET, float(ring.FRONT_REF)


_STATE = {'silhouette': True}   # one switch for the page and the editor (until the client restarts)


def SilhouetteEnabled():
    return _STATE['silhouette']


def SetSilhouetteEnabled(on):
    _STATE['silhouette'] = bool(on)


def StoneScale():
    """World stone scale of the native setting (0..1 -> 1.0..2.0); 1.0 without the option."""
    try:
        import systemSetting
        return 1.0 + max(0.0, min(1.0, float(systemSetting.GetMetinstoneScale())))
    except Exception:
        return 1.0


def _native(name):
    return getattr(WikiRenderTarget, name, None) if WikiRenderTarget is not None else None


def RecordName(draft):
    """'Pulzující obal · Klasický vír' (prstenec vypnutý / obal vypnutý named)."""
    body = design.BY_NUMBER[draft[design.PRESET]][2] if draft[design.BODY_ENABLED] else Tr('bez obalu', 'no body')
    ring = (design.RING_NAMES.get(draft[design.RING_STYLE], '') if draft[design.RING_ENABLED]
            else Tr('bez prstence', 'no ring'))
    return u'%s | %s' % (body, ring)


def ColorName(rgb):
    return Tr('Zlatá', 'Gold') if rgb == design.GOLD else '#%06X' % (rgb & 0xFFFFFF)


class MeteorPreviewView(object):
    """Frame + render target + overlays at (x, y, w, h) of parent. track(widget) registers page widgets."""

    def __init__(self, parent, kit, x, y, w, h, track=None, compact=False, camera=False):
        self.parent, self.kit = parent, kit
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.widgets = []
        self.track = track
        self.on_silhouette = None
        self.silhouette_allowed = True
        k = kit
        # Hairline brass frame (light borders, v5) around a dark fill shown while the target loads.
        self.fill = self._keep(ui.Bar(), x, y)
        self.fill.SetSize(self.w, self.h)
        self.fill.SetColor(uikit.GenerateColor(0x0B0A0D))
        self.fill.AddFlag('not_pick')
        for bx, by, bw, bh in ((x - 1, y - 1, w + 2, 1), (x - 1, y + h, w + 2, 1),
                               (x - 1, y, 1, h), (x + w, y, 1, h)):
            line = self._keep(ui.Bar(), bx, by)
            line.SetSize(bw, bh)
            line.SetColor(uikit.GenerateColor(T.BRONZE_LINE))
            line.AddFlag('not_pick')
        self.target = self._keep(ui.WikiRenderTargetUi(), x, y)
        self.target.SetSize(self.w, self.h)
        self.target.AddFlag('not_pick')
        self.target.Hide()
        self.silhouette = self._keep(ui.ExpandedImageBox(), x, y)
        self.silhouette.AddFlag('not_pick')
        self.character_path = CharacterArt()[0]
        self.silhouette.LoadImage(self.character_path)
        linear = getattr(self.silhouette, 'SetLinearFiltering', None)
        if linear:
            linear(True)
        self.silhouette.Hide()
        self.input = self._keep(ui.Window(), x, y)
        self.input.SetSize(self.w, self.h)
        # The gesture hint shows while the mouse is over the preview (no text over the effect otherwise).
        self.input.OnMouseOverIn = ui.__mem_func__(self._HintIn)
        self.input.OnMouseOverOut = ui.__mem_func__(self._HintOut)
        pad = 12 if k.prof == '1080' else 9
        self.pad = pad
        self.title = uikit.Text(parent, '', x + pad, y + pad, k.font('Mb'), T.GOLD_HI, valign='top', outline=True)
        self.subtitle = uikit.Text(parent, '', x + pad, y + pad + k.cell('Mb') + 4, k.font('S'), T.INK_DIM,
                                   valign='top', outline=True)
        hint = (Tr('Pravé tl.: otočit | kolečko: zoom', 'Right: rotate · wheel: zoom') if compact else
                Tr('Pravé tlačítko: otočit | levé: posunout | kolečko: přiblížit',
                   'Right button: rotate · left: pan · wheel: zoom'))
        self.hint = uikit.Text(parent, hint, x + pad, y + h - pad - k.cell('S'), k.font('S'), T.MUTED,
                               valign='top', outline=True)
        self.status = uikit.Text(parent, '', x + w // 2, y + h // 2, k.font('M'), T.INK_DIM, align='center',
                                 outline=True)
        for widget in (self.title, self.subtitle, self.hint, self.status):
            self._track(widget)
        self.hint.Hide()
        # Silhouette switch: a v5 kit chip, top right, above the input layer (it must stay clickable).
        self.toggle = uikit.Chip(parent, k, 0, 0, Tr('Postava pro srovnání', 'Character for scale'),
                                 on=SilhouetteEnabled(), event=self._FlipSilhouette)
        self.toggle.SetPosition(x + w - pad - self.toggle.Width(), y + pad)
        self._track(self.toggle)
        self.placement = None
        # "Výchozí pohled" (settings page; the editor has its Kamera button under the preview): shown while the view
        # is rotated, panned or zoomed. The silhouette is a flat overlay, true only for the default view - after an
        # orbit it is hidden and on the page nothing brought it back (owner play test 2026-10-05: "silueta prostě
        # zmizela a nikde není"). Above the input layer, so it stays clickable.
        self.on_camera = None
        self.camera = None
        if camera:
            self.camera = uikit.Button(parent, k, 0, 0, 0, Tr('Výchozí pohled', 'Default view'), role='secondary',
                                       icon='camera', event=self._ResetCamera)
            self.camera.FitWidth()
            self.camera.SetPosition(x + w - pad - self.camera.w, y + h - pad - self.camera.h)
            self._track(self.camera)
            self.camera.Hide()

    # ---------------------------------------------------------------- widgets
    def _track(self, widget):
        self.widgets.append(widget)
        if self.track:
            self.track(widget)
        return widget

    def _keep(self, widget, x, y):
        widget.SetParent(self.parent)
        widget.SetPosition(int(x), int(y))
        widget.Show()
        return self._track(widget)

    def SetTitle(self, title, subtitle=''):
        self.title.SetText(title)
        self.subtitle.SetText(subtitle)
        k, pad = self.kit, self.pad
        self.subtitle.SetPosition(self.x + pad, self.y + pad + (k.cell('Mb') + 4 if title else 3))

    def SetStatus(self, text):
        self.status.SetText(text or '')

    def Backdrop(self):
        return camera.backdrop(float(self.w) / max(1, self.h))

    def Aspect(self):
        return float(self.w) / max(1, self.h)

    def _HintIn(self):
        self.hint.Show()

    def _HintOut(self):
        self.hint.Hide()

    def _ResetCamera(self):
        if self.on_camera:
            self.on_camera()

    def SetDefaultView(self, default):
        """The camera button shows while the view is not the default one."""
        if self.camera is not None:
            self.camera.Hide() if default else self.camera.Show()

    # ---------------------------------------------------------------- silhouette
    def _FlipSilhouette(self):
        SetSilhouetteEnabled(not SilhouetteEnabled())
        self.toggle.SetOn(SilhouetteEnabled())
        self._PlaceSilhouette()
        if self.on_silhouette:
            self.on_silhouette()

    def PlaceSilhouette(self, framing, pan=(0.0, 0.0), allowed=True, orbit=(0.0, 0.0)):
        """Places the character for the framing (zoom, stone size) and the pan. ``orbit`` is ignored: the warrior is
        a still front view (kolo 3), a turn of the stone does not move or change it. ``allowed`` = False hides the
        old flat silhouette (CHARACTER_STYLE 'silhouette', true only for the default view)."""
        self.placement = (framing, tuple(pan))
        self.silhouette_allowed = allowed
        self._PlaceSilhouette()

    def CharacterRect(self):
        """(left, top, scale) of the character in the view, or None without a placement. Feet where the default view
        puts them (framing.silhouette at pitch 0 / yaw 0), 174 units scaled like the stone; kept whole inside the view
        (2 px margin): pushed in from an edge, and scaled down only when it would be taller than the view."""
        if not self.placement:
            return None
        framing, pan = self.placement
        fx, fy, fh = framing.silhouette(0.0, 0.0)
        feet_x, feet_y = camera.to_pixels(fx, fy, self.w, self.h, pan)
        path, (sw, sh), (ax, ay), ref = CharacterArt()
        scale = max(fh * 0.5 * self.h, 12.0) / float(ref)
        scale = min(scale, (self.h - 4.0) / sh, (self.w - 4.0) / sw)
        left = min(max(feet_x - ax * scale, 2.0), self.w - 2.0 - sw * scale)
        top = min(max(feet_y - ay * scale, 2.0), self.h - 2.0 - sh * scale)
        return left, top, scale

    def _PlaceSilhouette(self):
        self.toggle.SetOn(SilhouetteEnabled())
        if not self.placement or not SilhouetteEnabled() or not self.silhouette_allowed or not self.target.IsShow():
            self.silhouette.Hide()
            return
        path = CharacterArt()[0]
        if path != self.character_path:
            self.character_path = path
            self.silhouette.LoadImage(path)
        left, top, scale = self.CharacterRect()
        self.silhouette.SetScale(scale, scale)
        self.silhouette.SetPosition(int(round(self.x + left)), int(round(self.y + top)))
        self.silhouette.Show()

    def Destroy(self):
        for widget in self.widgets:
            widget.Hide()
        self.widgets = []
        self.on_silhouette = self.on_camera = None


class MeteorPreviewController(DesignController):
    """DesignController with the v5 camera. page.widgets must hold Preview / PreviewInput (the view's)."""

    def __init__(self, page, backend, view):
        self.view = view
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.actorScale = 1.0
        self.viewScale = StoneScale()
        self.orbiting = False
        DesignController.__init__(self, page, backend)
        self.companion = False
        view.on_silhouette = self._PlaceSilhouette
        view.on_camera = self.ResetCamera

    # ---------------------------------------------------------------- binding
    def _BindPreview(self):
        self.preview = self.view.target
        self.previewInput = self.view.input
        for eventName, callback in (
            ("OnMouseLeftButtonDown", self._StartPreviewPan),
            ("OnMouseLeftButtonUp", self._StopPreviewDrag),
            ("OnMouseRightButtonDown", self._StartPreviewOrbit),
            ("OnMouseRightButtonUp", self._StopPreviewDrag),
            ("OnMouseWheel", self.OnMouseWheel),
        ):
            setattr(self.previewInput, eventName, ui.__mem_func__(callback))

    # ---------------------------------------------------------------- native target
    def _CreatePreview(self):
        if self.draft is None:
            return
        self.zoom, self.pan, self.orbiting = 1.0, [0.0, 0.0], False
        self.previewPitch = self.previewYaw = 0.0
        self.actorScale = StoneScale()  # the native actor takes the world scale when it is created
        try:
            index = int(WikiRenderTarget.GetFreeIndex(164, 236))
            if index < 1:
                raise RuntimeError("no free render-target index")
            self.previewIndex = index
            self.preview.SetRenderTarget(index)
            WikiRenderTarget.SetBackground(index, self.view.Backdrop())
            if not design.SelectPreview(index, self.previewVnum, self.draft):
                raise RuntimeError("preview model could not be selected")
            self.companion = False   # a native selection resets the scene (ResetModel clears the companion)
            WikiRenderTarget.SetVisibility(index, True)
            self.preview.Show()
            self.previewCurrent = True
            self.previewNeedsSelection = False
            self.view.SetStatus('')
            self._ApplyCamera()
            self.page.RefreshStatus()
        except (AttributeError, RuntimeError, TypeError, ValueError, OSError) as error:
            import dbg
            dbg.TraceError("[MeteorPreview] Preview unavailable: %s" % error)
            self._RemovePreview()
            self.view.SetStatus(Tr('Náhled nelze načíst.', 'The preview cannot be loaded.'))
            self.page.SetStatus(u"Náhled nelze načíst. Je potřeba odpovídající klient a balíčky.")

    def _UpdatePreview(self, reframe=False):
        selecting = bool(reframe or self.previewNeedsSelection)
        had_target = self.previewIndex is not None
        DesignController._UpdatePreview(self, reframe)
        # A new native selection resets the native camera, pan and orbit: put the v5 framing back.
        if had_target and selecting and self.previewCurrent and self.previewIndex is not None:
            self.companion = False   # the re-selection cleared the native companion
            self.zoom, self.pan, self.orbiting = 1.0, [0.0, 0.0], False
            self.previewPitch = self.previewYaw = 0.0     # the native selection reset its view rotation too
            self._ApplyCamera()

    def _RemovePreview(self):
        self.companion = False
        DesignController._RemovePreview(self)
        if getattr(self, 'view', None):
            self.view.silhouette.Hide()

    def _Framing(self):
        return camera.Framing(self.previewVnum, self.view.Aspect(), self.actorScale, self.viewScale, self.zoom)

    def _ApplyCamera(self):
        if self.previewIndex is None:
            return False
        eye, target = _native('SetModelV3Eye'), _native('SetModelV3Target')
        if not eye or not target:
            self._PlaceSilhouette()   # older EXE: the native framing stays (smaller stone); the warrior shows anyway
            return False
        framing = self._Framing()
        target(self.previewIndex, *[float(v) for v in framing.target()])
        eye(self.previewIndex, *[float(v) for v in framing.eye()])
        self._PlaceSilhouette(framing)
        return True

    def DefaultView(self):
        return not self.orbiting and not (self.pan[0] or self.pan[1]) and abs(self.zoom - 1.0) < 1e-6

    def _SyncCompanion(self, framing=None):
        """True when the native 3D companion handles the character (then the 2D image stays hidden)."""
        if self.previewIndex is None or not NativeCompanion():
            return False
        if not SilhouetteEnabled():
            clear = _native('ClearMetinQueueCompanion')
            if clear and self.companion:
                clear(self.previewIndex)
            self.companion = False
            return True
        x, y, scale = (framing or self._Framing()).companion_world()
        c = COMPANION
        if self.companion:
            self.companion = bool(_native('PlaceMetinQueueCompanion')(
                self.previewIndex, float(x), float(y), float(c['rotation']), float(scale)))
        if not self.companion:
            self.companion = bool(_native('SetMetinQueueCompanion')(
                self.previewIndex, int(c['race']), int(c['armor']), int(c['weapon']), int(c['hair']),
                float(x), float(y), float(c['rotation']), float(scale)))
        return self.companion

    def _PlaceSilhouette(self, framing=None):
        if self.previewIndex is None:
            self.view.silhouette.Hide()
            self.view.SetDefaultView(True)
            return
        if self._SyncCompanion(framing):
            self.view.silhouette.Hide()
            self.view.toggle.SetOn(SilhouetteEnabled())
            self.view.SetDefaultView(self.DefaultView())
            return
        # The warrior stands still for a turn (kolo 3); only the old flat silhouette hides for a rotation.
        self.view.PlaceSilhouette(framing or self._Framing(), self.pan,
                                  allowed=CHARACTER_STYLE != 'silhouette' or not self.orbiting)
        self.view.SetDefaultView(self.DefaultView())

    # ---------------------------------------------------------------- v5 camera API
    def SetViewScale(self, scale):
        scale = camera.clamp(float(scale), camera.SIZE_RANGE[0], camera.SIZE_RANGE[1])
        if abs(scale - self.viewScale) < 1e-4:
            return False
        self.viewScale = scale
        self._ApplyCamera()
        return True

    def ResetCamera(self):
        """Default view of the same actor: no re-selection, the marker animation keeps running."""
        if self.previewIndex is None:
            if self.draft is not None:
                self._CreatePreview()
            return
        self._StopPreviewDrag()
        self.previewPitch = self.previewYaw = 0.0
        rotate, pan = _native('RotateEyeAroundTarget'), _native('PanMetinQueuePreview')
        if rotate:
            rotate(self.previewIndex, 0.0, 0.0)
        if pan and (self.pan[0] or self.pan[1]):
            pan(self.previewIndex, -self.pan[0], -self.pan[1])
        self.pan, self.zoom, self.orbiting = [0.0, 0.0], 1.0, False
        self._ApplyCamera()

    def OnMouseWheel(self, nLen):
        if self.previewIndex is None:
            return False
        if not _native('SetModelV3Eye'):
            return appearance.MetinQueueAppearanceController.OnMouseWheel(self, nLen)
        factor = camera.ZOOM_STEP if nLen > 0 else 1.0 / camera.ZOOM_STEP
        self.zoom = camera.clamp(self.zoom * factor, camera.ZOOM_RANGE[0], camera.ZOOM_RANGE[1])
        self._ApplyCamera()
        return True

    def OnUpdate(self):
        self._SampleSliders()
        mode = getattr(self, 'previewDragMode', DRAG_NONE)
        if mode == DRAG_NONE or self.previewIndex is None:
            return
        xMouse, yMouse = wndMgr.GetMousePosition()
        deltaX, deltaY = xMouse - self.lastMouseX, yMouse - self.lastMouseY
        self.lastMouseX, self.lastMouseY = xMouse, yMouse
        if not (deltaX or deltaY):
            return
        if mode == DRAG_PAN:
            dx = float(deltaX) / max(1, self.view.w)
            dy = float(deltaY) / max(1, self.view.h)
            pan = _native('PanMetinQueuePreview')
            if pan:
                pan(self.previewIndex, dx, dy)
                self.pan = [camera.clamp(self.pan[0] + dx, -PAN_LIMIT, PAN_LIMIT),
                            camera.clamp(self.pan[1] + dy, -PAN_LIMIT, PAN_LIMIT)]
                self._PlaceSilhouette()
            return
        self.previewYaw += float(deltaX) * ROTATION_SENSITIVITY
        # The tilt stays between 5 and 60 deg of elevation (camera.PITCH_RANGE): no look from under the ground and
        # always a warrior frame close to the view.
        self.previewPitch = camera.clamp(self.previewPitch + float(deltaY) * ROTATION_SENSITIVITY,
                                         camera.PITCH_RANGE[0], camera.PITCH_RANGE[1])
        WikiRenderTarget.RotateEyeAroundTarget(self.previewIndex, self.previewPitch, self.previewYaw)
        # The warrior does not turn (kolo 3); the old flat silhouette is true only for the default view direction.
        self.orbiting = bool(self.previewPitch or self.previewYaw)
        if CHARACTER_STYLE == 'silhouette':
            self._PlaceSilhouette()
        else:
            self.view.SetDefaultView(self.DefaultView())

    def Destroy(self):
        DesignController.Destroy(self)
        self.view = None
