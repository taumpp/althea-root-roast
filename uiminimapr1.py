# -*- coding: utf-8 -*-
"""The minimap (uiminimap.MiniMap) in the R1 look: "Minimapa A2" (owner 8. 10. 2026).

The minimap keeps its shapes, places and functions; only the art and the channel line on the pennant change
(tools/build_althea_r1_minimapa.py, ``althea_r1_minimapa/``):

* the round buttons stay today's medallions in the R1 colours: graphite outer ring, a deep dark red inner ring, the
  coloured icon unchanged. The launchers of the button panel get them through ``minimappanelicons.Family``, the
  small ring controls (close, atlas, more, settings, zoom + / -) here. An open window has a brighter red inner ring
  (``uibuttonpaneldecor``), a notification keeps its red dot;
* no arc between the launchers (``minimappanelicons.R1_ARC`` = 'none'; 'edge' draws the arc concentric with the
  map under the outer edge of the launchers);
* the ring of the map and the pennant in R1 colours; the pennant keeps its shape with the tail, the logo, the time
  and the date;
* "‹ CH 3 ›" higher on the pennant, in its straight part: ‹ / › are CH- / CH+ (``uichannelbar.StepChannel``), the
  label opens the channel bar; a gap between "CH" and the number, both ivory, no red line under them.

Settings -> "Starý vzhled" keeps today's minimap. A failure while dressing is traced (uir1.TraceFailure), the
original art comes back (``Restore``) and the R1 look is not tried again in this session.
"""
import ui

import uir1
import uir1tokens as T
import uir1minimapaart as A
import minimappanelicons
from settingslocale import Text as Tr

CRIMSON = 'd:/ymir work/ui/game/crimson_ember/'
# child name -> (R1 control, the original art of uiscript/uiscript/minimap.py)
CONTROLS = (
    ('MiniMapHideButton', 'close', CRIMSON + 'minimap/close_%s.png'),
    ('AtlasShowButton', 'atlas', CRIMSON + 'minimap/atlas_%s.png'),
    ('LauncherMoreButton', 'more', CRIMSON + 'minimap_panel/more_%s.png'),
    ('LauncherSettingsButton', 'settings', CRIMSON + 'inventory/rail_settings_%s.png'),
    ('ScaleUpButton', 'zoom_in', CRIMSON + 'minimap/zoom_in_%s.png'),
    ('ScaleDownButton', 'zoom_out', CRIMSON + 'minimap/zoom_out_%s.png'),
)
FRAME = 'd:/ymir work/ui/public/crimson/windows/minimap/frame.tga'
PENNANT = CRIMSON + 'minimap/status_pennant/v1/carrier.png'
PENNANT_SCALE = 0.85
ORBITS = (('LauncherOrbit', 'orbit/edge_ring1.png'), ('LauncherOrbitOuter', 'orbit/edge_ring2.png'))

# Rows on the pennant (from its top; design sheet R-doporuceni.png): the clock and the date as in the A2 sheet, the
# channel line in the straight part of the pennant above the tail.
CLOCK_DY, DATE_DY, CHANNEL_DY = 46, 62, 82
# The original rows (uiscript/uiscript/minimap.py), for Restore.
ORIGINAL_ROWS = (('StatusClock', 48, 'Tahoma:13b', (244, 237, 217)), ('StatusDate', 64, 'Tahoma:12', (222, 212, 190)))
CHEVRON = 10
CH_GAP = 4               # "CH" -> the number
ARROW_GAP = 4            # chevron -> text
ARROW_W, ROW_H = 14, 16  # hit box of a chevron, height of the channel line

_failed = [False]


def UseR1():
    return uir1.UseR1() and not _failed[0]


def _Color(rgb):
    """Packed 0xAARRGGBB like uir1tokens."""
    r, g, b = rgb
    return 0xFF000000 | r << 16 | g << 8 | b


def Art(name):
    return A.ROOT + name


def SetButtonArt(button, pattern):
    button.SetUpVisual(pattern % 'normal')
    button.SetOverVisual(pattern % 'hover')
    button.SetDownVisual(pattern % 'pressed')


class Chevron(uir1.Interactive):
    """‹ / › of the pennant: CH- / CH+ with the minimap's transparent tooltip."""

    def __init__(self, line, direction, step):
        uir1.Interactive.__init__(self)
        self.line, self.direction, self.step = line, direction, step
        self.SetParent(line)
        self.SetSize(ARROW_W, ROW_H)
        self.glyph = uir1.Image(self, uir1.ChevronPath(direction, 'normal'), (ARROW_W - CHEVRON) // 2,
                                (ROW_H - CHEVRON) // 2)
        self.callback = lambda: line.Step(step)
        self.Show()

    def paint(self):
        if getattr(self, 'glyph', None) is not None:
            self.glyph.LoadImage(uir1.ROOT + uir1.ChevronPath(self.direction, 'hover' if self.hovered else 'normal'))

    def OnMouseOverIn(self):
        uir1.Interactive.OnMouseOverIn(self)
        self.line.ShowTip(self, self.line.StepTip(self.step))

    def OnMouseOverOut(self):
        uir1.Interactive.OnMouseOverOut(self)
        self.line.HideTip(self)


class Label(uir1.Interactive):
    """"CH 3" of the pennant: opens the channel bar ("Změna kanálu")."""

    def __init__(self, line):
        uir1.Interactive.__init__(self)
        self.line = line
        self.SetParent(line)
        self.callback = line.OpenBar
        self.Show()

    def OnMouseOverIn(self):
        uir1.Interactive.OnMouseOverIn(self)
        self.line.ShowTip(self, Tr('Změna kanálu', 'Change channel'))

    def OnMouseOverOut(self):
        uir1.Interactive.OnMouseOverOut(self)
        self.line.HideTip(self)


class ChannelLine(ui.Window):
    """‹ CH 3 › centred on (cx, cy): the chevrons, "CH" and the number in Cinzel (ivory), a gap between them."""

    def __init__(self, parent, kit, cx, cy, minimap, tooltip_class):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.minimap = minimap
        self.cx, self.cy = cx, cy
        self.prev = Chevron(self, 'left', -1)
        self.label = Label(self)
        self.ch = uir1.Text(self, 'CH', 0, ROW_H // 2, kit.font('button_s'), T.IVORY)
        self.number = uir1.Text(self, '', 0, ROW_H // 2, kit.font('button_s'), T.IVORY)
        self.next = Chevron(self, 'right', 1)
        self.tip = tooltip_class() if tooltip_class else None
        if self.tip is not None:
            self.tip.Hide()
        self.tipOwner = None
        self.text = None
        self.Hide()

    def SetChannel(self, text):
        """The text of the original ServerInfo ("CH3", the hub as "CH1", "CH99", '' = no channel)."""
        text = text or ''
        if text == self.text:
            return
        self.text = text
        if not text.startswith('CH') or len(text) < 3:
            self.Hide()
            return
        self.number.SetText(text[2:])
        wa, wb = uir1.TextWidth(self.ch), uir1.TextWidth(self.number)
        label_w = wa + CH_GAP + wb
        x = 0
        self.prev.SetPosition(x, 0)
        x += ARROW_W - (ARROW_W - CHEVRON) // 2 + ARROW_GAP
        self.label.SetPosition(x, 0)
        self.label.SetSize(label_w, ROW_H)
        self.ch.SetPosition(x, ROW_H // 2 - 1)
        self.number.SetPosition(x + wa + CH_GAP, ROW_H // 2 - 1)
        x += label_w + ARROW_GAP - (ARROW_W - CHEVRON) // 2
        self.next.SetPosition(x, 0)
        w = x + ARROW_W
        self.SetSize(w, ROW_H)
        self.SetPosition(int(self.cx - w / 2.0 + 0.5), self.cy - ROW_H // 2)
        self.Show()

    # ---------------------------------------------------------------------- actions
    def _Interface(self):
        return getattr(self.minimap, 'interface', None)

    def Step(self, step):
        import uichannelbar
        return uichannelbar.StepChannel(self._Interface(), step)

    def StepTip(self, step):
        import uichannelbar
        target = uichannelbar.StepChannelTarget(self._Interface(), step)
        if target is None:
            return Tr('Jiný kanál teď není k dispozici.', 'No other channel now.')
        if step > 0:
            return Tr('CH+ : přepnout na CH%d', 'CH+ : switch to CH%d') % target
        return Tr('CH- : přepnout na CH%d', 'CH- : switch to CH%d') % target

    def OpenBar(self):
        import uichannelbar
        return uichannelbar.Toggle(self._Interface())

    # ---------------------------------------------------------------------- tooltip (the R1 hint)
    def ShowTip(self, owner, text):
        if self.tip is None:
            return
        self.tipOwner = owner
        self.tip.SetText(text)
        x, y = owner.GetGlobalPosition()
        self.tip.SetTooltipPosition(x + owner.GetWidth() // 2, y + owner.GetHeight() + 2)
        if hasattr(self.tip, 'SetAnchor'):            # the R1 hint: placed at the chevron, never over it
            self.tip.SetAnchor((x, y, owner.GetWidth(), owner.GetHeight()))
        self.tip.Show()

    def HideTip(self, owner=None):
        if self.tip is not None and (owner is None or owner is self.tipOwner):
            self.tipOwner = None
            self.tip.Hide()

    def Destroy(self):
        self.HideTip()
        self.tip = None
        self.minimap = None
        self.Hide()


class Dress(object):
    """The R1 art on a loaded uiminimap.MiniMap (``Apply``) and back (``Restore``)."""

    def __init__(self, minimap, tooltip_class=None):
        self.minimap = minimap
        self.tooltipClass = tooltip_class
        self.kit = uir1.Kit()
        self.channel = None
        self.serverInfo = None
        self.applied = []

    def _Child(self, name):
        minimap = self.minimap
        return minimap.GetChild(name) if minimap.IsChild(name) else None

    def Apply(self):
        frame = self._Child('OpenWindowBGI')
        if frame is not None:
            frame.LoadImage(Art('frame.png'))
            self.applied.append('frame')
        for name, control, unused in CONTROLS:
            button = self._Child(name)
            if button is not None:
                SetButtonArt(button, Art('control/%s_%%s.png' % control))
                self.applied.append(name)
        if minimappanelicons.R1_ARC == 'edge':
            for name, art in ORBITS:
                orbit = self._Child(name)
                if orbit is not None:
                    orbit.LoadImage(Art(art))
                    orbit.SetPosition(*A.ORBITS[art])
                    self.applied.append(name)
        pennant = self._Child('StatusPennant')
        if pennant is None:
            return self
        pennant.LoadImage(Art('pennant.png'))
        pennant.SetScale(PENNANT_SCALE, PENNANT_SCALE)          # LoadImage reset it (a new image instance)
        getattr(pennant, 'SetLinearFiltering', lambda enabled: None)(True)
        self.applied.append('pennant')
        top = pennant.GetLocalPosition()[1]
        for name, dy, role, color in (('StatusClock', CLOCK_DY, 'text', T.IVORY),
                                      ('StatusDate', DATE_DY, 'text_xs', T.INK_DIM)):
            line = self._Child(name)
            if line is not None:
                x = line.GetLocalPosition()[0]
                uir1.SetFont(line, self.kit.font(role))
                line.SetPackedFontColor(color)
                line.SetPosition(x, top + dy)
                self.applied.append(name)
        info = self._Child('ServerInfo')
        parent = self._Child('OpenWindow')
        if info is not None and parent is not None:
            cx = info.GetLocalPosition()[0]
            self.channel = ChannelLine(parent, self.kit, cx, top + CHANNEL_DY, self.minimap, self.tooltipClass)
            self.channel.SetChannel(info.GetText())
            self.serverInfo = info
            original = info.SetText
            channel = self.channel

            def SetText(text, *args):
                original(text, *args)
                channel.SetChannel(text)
            info.SetText = SetText                              # the minimap keeps writing the original line
            info.Hide()
            self.applied.append('ServerInfo')
        return self

    def Orbits(self, inner, outer):
        """After the minimap clipped its connectors: no arc in the 'none' mode."""
        if minimappanelicons.R1_ARC != 'edge':
            for orbit in (inner, outer):
                if orbit:
                    orbit.Hide()

    def Restore(self):
        """The original art (after a failure); what was not changed stays."""
        done, self.applied = self.applied, []
        if 'frame' in done:
            self._Child('OpenWindowBGI').LoadImage(FRAME)
        for name, unused, pattern in CONTROLS:
            if name in done:
                SetButtonArt(self._Child(name), pattern)
        if 'pennant' in done:
            pennant = self._Child('StatusPennant')
            pennant.LoadImage(PENNANT)
            pennant.SetScale(PENNANT_SCALE, PENNANT_SCALE)
            getattr(pennant, 'SetLinearFiltering', lambda enabled: None)(True)
            top = pennant.GetLocalPosition()[1]
            for name, dy, font, rgb in ORIGINAL_ROWS:
                if name in done:
                    line = self._Child(name)
                    uir1.SetFont(line, font)
                    line.SetPackedFontColor(_Color(rgb))
                    line.SetPosition(line.GetLocalPosition()[0], top + dy)
        if self.serverInfo is not None:
            self.serverInfo.__dict__.pop('SetText', None)
            self.serverInfo.Show()
            self.serverInfo = None
        if self.channel is not None:
            self.channel.Destroy()
            self.channel = None
        # the edge arcs: the minimap rebuilds its launcher panel with the original connectors
        for name, unused in ORBITS:
            if name in done:
                orbit = self._Child(name)
                orbit.LoadImage({'LauncherOrbit': CRIMSON + 'minimap/launcher_orbit.png',
                                 'LauncherOrbitOuter': CRIMSON + 'minimap_panel/orbit_outer.png'}[name])
                orbit.SetPosition(*{'LauncherOrbit': (-72, 0), 'LauncherOrbitOuter': (-71, 10)}[name])

    def Destroy(self):
        if self.channel is not None:
            self.channel.Destroy()
            self.channel = None
        self.serverInfo = None
        self.minimap = None


def Create(minimap, tooltip_class=None):
    """The applied dress, or None (Starý vzhled, or a failure: traced, the original art back, not retried)."""
    if not UseR1():
        return None
    dress = Dress(minimap, tooltip_class)
    try:
        return dress.Apply()
    except Exception:
        _failed[0] = True
        uir1.TraceFailure('Minimapa')
        try:
            dress.Restore()
        except Exception:
            pass
        return None
