# -*- coding: utf-8 -*-
"""R1 pieces of the HUD ("Krvavá žíla", docs/ALTHEA_R1_KIT.md): the HP gauge of the party members and of the HP bar
over the own character (uiparty.PartyMemberInfoBoard, uiplayergauge.PlayerGauge).

Gauge is the R1 HP bar: a dark track with the graphite outline of the R1 controls and the fill in the blood red of
the kit with a lighter top line (green while the character is poisoned, like the original gauge_lime). It keeps the
height of the original gauge (7 px), so nothing around it moves.

GaugeSkin draws a Gauge INTO an existing ui.Gauge in place: the original slot and fill images are hidden, the R1 bar
is a not pickable child of the gauge (it moves, shows and hides with it), the gauge's SetPercentage and SetGaugeColor
(instance wrappers, weak references only) feed it; Restore() brings the original look back. Every value the window
sets still reaches the original gauge, so the original look comes back with the current value.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original gauge: Dress returns None. A failure is traced
(uir1.TraceFailure), the original look comes back and that kind of window is not dressed again in this session.
"""
import weakref

import ui

import uir1
import uir1tokens as T

HEIGHT = 7                      # the original gauge's height (ui.Gauge.SLOT_HEIGHT)
TRACK = 0x0A0909                # the dark well of the track
FILLS = {
    # colour: (fill, top line) - the original gauge colours the windows use (gauge_<colour>.tga)
    'red': (T.RED_DK, T.RED_HI),
    'lime': (0xFF4E8A2E, 0xFF8FCB7C),
}
TOP_ALPHA = 0.7
# The textured bar (party rows): the fill is the original gauge tile (gauge_<colour>.tga, 16 x 8, native size, the
# colour the game has always had for its HP bars), its first TILE_ROWS rows; the bottom line of the bar is the R1
# outline, the top edge is the tile's own dark first row.
TILE_PATH = 'd:/ymir work/ui/pattern/gauge_%s.tga'
TILE_W, TILE_H, TILE_ROWS = 16, 8, 6

_failed = set()


def Signed(color):
    """A packed 0xAARRGGBB colour for wndMgr.SetFontColor / SetPackedFontColor: the x64 binding parses a C int and
    silently ignores a colour >= 0x80000000, so those go in as the signed value."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color & 0x80000000 else color


def UseR1(what):
    return what not in _failed and uir1.UseR1()


def Fail(what):
    _failed.add(what)
    uir1.TraceFailure(what)


class Gauge(ui.Window):
    """R1 HP bar: the graphite outline, a dark track and the fill up to the value (1 px inside the outline).

    ``textured`` (the party rows): the fill is the original gauge tile instead of a flat colour, so the bar has the
    colour of the game's own HP bars (owner 8. 10. 2026: not a bright flat red). The bar is then open at the top (the
    first row of the tile is its edge): the outline runs along the left, right and bottom, the fill is
    ``TILE_ROWS`` px high from the top."""

    def __init__(self, parent, x, y, w, h=HEIGHT, color='red', textured=False):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.w, self.h = max(4, int(w)), max(4, int(h))
        self.textured = bool(textured)
        self.SetSize(self.w, self.h)
        self.outline = uir1.Rect(self, 0, 0, self.w, self.h, T.BORDER)
        self.color = None
        self.value, self.maximum, self.fill_w = 0, 1, -1
        if self.textured:
            self.rows = min(TILE_ROWS, self.h - 1)
            self.track = uir1.Rect(self, 1, 0, self.w - 2, self.h - 1, TRACK)
            self.top = None
            self.fill = ui.ExpandedImageBox()
            self.fill.SetParent(self)
            self.fill.AddFlag('not_pick')
            self.fill.SetPosition(1, 0)
            self.fill.Hide()
        else:
            self.track = uir1.Rect(self, 1, 1, self.w - 2, self.h - 2, TRACK)
            self.fill = uir1.Rect(self, 1, 1, 1, self.h - 2, FILLS['red'][0])
            self.top = uir1.Rect(self, 1, 1, 1, 1, FILLS['red'][1], TOP_ALPHA)
        self.SetColor(color)
        self.SetValue(0, 1)
        self.Show()

    def SetColor(self, color):
        if color not in FILLS:
            color = 'red'
        if color == self.color:
            return
        self.color = color
        if self.textured:
            self.fill.LoadImage(TILE_PATH % color)      # a new image instance: the rendering rect is set again
            self._Tile()
            return
        fill, top = FILLS[color]
        self.fill.SetColor(uir1.GenerateColor(fill, 1.0))
        self.top.SetColor(uir1.GenerateColor(top, TOP_ALPHA))

    def _Tile(self):
        """The tile cut to ``fill_w`` x ``rows`` px: a rendering rect is a fraction of the image size (-1 = nothing,
        more than 0 repeats the tile; every value here is a multiple of 1/16 and 1/8, exact in a float)."""
        if self.fill_w > 0:
            self.fill.SetRenderingRect(0.0, 0.0, float(self.fill_w) / TILE_W - 1.0, float(self.rows) / TILE_H - 1.0)

    def SetValue(self, value, maximum):
        try:
            maximum = float(maximum)
            ratio = min(1.0, max(0.0, float(value) / maximum)) if maximum > 0 else 0.0
        except (TypeError, ValueError, ZeroDivisionError):
            ratio = 0.0
        self.value, self.maximum = value, maximum
        width = int((self.w - 2) * ratio)
        if width == self.fill_w:
            return
        self.fill_w = width
        if width <= 0:
            self.fill.Hide()
            if self.top is not None:
                self.top.Hide()
            return
        if self.textured:
            self._Tile()
            self.fill.Show()
            return
        self.fill.SetSize(width, self.h - 2)
        self.top.SetSize(width, 1)
        self.fill.Show()
        self.top.Show()

    def FillWidth(self):
        return max(0, self.fill_w)


def _Wrap(target, name, after):
    """``target.<name>`` runs the original method, then ``after(*args)``; weak references only (a ui.Window with
    __del__ in a reference cycle is never freed by Python 2). Returns the undo record."""
    own = target.__dict__.get(name)
    ref = weakref.ref(target)
    if own is not None:
        original = own
    else:
        function = getattr(target.__class__, name)

        def original(*args):
            obj = ref()
            return function(obj, *args) if obj is not None else None

    def wrapper(*args):
        result = original(*args)
        after(*args)
        return result
    setattr(target, name, wrapper)
    return (ref, name, own)


def _Unwrap(record):
    ref, name, own = record
    target = ref()
    if target is None:
        return
    if own is not None:
        setattr(target, name, own)
    elif name in target.__dict__:
        delattr(target, name)


Wrap, Unwrap = _Wrap, _Unwrap       # for the other R1 skins of HUD windows (uipartyr1)

ORIGINAL_PARTS = ('imgLeft', 'imgCenter', 'imgRight', 'imgGauge')


class GaugeSkin(object):
    """The R1 bar drawn into one ui.Gauge (see the module doc). ``what`` names the window in the failure trace."""

    def __init__(self, gauge, what, color='red', textured=False):
        self.what = what
        self.gaugeRef = weakref.ref(gauge)
        self.hidden = []
        self.wrapped = []
        self.bar = None
        try:
            for name in ORIGINAL_PARTS:
                part = getattr(gauge, name, None)
                if part is not None and part.IsShow():
                    part.Hide()
                    self.hidden.append(part)
            self.bar = Gauge(gauge, 0, 0, gauge.GetWidth() or getattr(gauge, 'width', 0), HEIGHT, color, textured)
            percentage = getattr(gauge, 'percentage', None) or (getattr(gauge, 'lastCurValue', None),
                                                                getattr(gauge, 'lastMaxValue', None))
            if percentage[0] is not None and percentage[1] is not None:
                self.bar.SetValue(*percentage)
            me = weakref.ref(self)

            def percentage_changed(value, maximum, *unused):
                skin = me()
                if skin is not None:
                    skin._Call(skin.bar.SetValue, value, maximum)

            def colour_changed(color, *unused):
                skin = me()
                if skin is not None:
                    skin._Call(skin.bar.SetColor, color)
            self.wrapped.append(_Wrap(gauge, 'SetPercentage', percentage_changed))
            if hasattr(gauge, 'SetGaugeColor'):
                self.wrapped.append(_Wrap(gauge, 'SetGaugeColor', colour_changed))
            gauge.r1gauge = self
        except Exception:
            self.Restore()
            raise

    def _Call(self, function, *args):
        try:
            function(*args)
        except Exception:
            Fail(self.what)
            self.Restore()

    def SetPoison(self, poisoned):
        """The poison colour of a gauge whose window loads gauge_lime / gauge_red itself (PlayerGauge)."""
        if self.bar is not None:
            self._Call(self.bar.SetColor, 'lime' if poisoned else 'red')

    def Restore(self):
        wrapped, self.wrapped = self.wrapped, []
        for record in reversed(wrapped):
            try:
                _Unwrap(record)
            except Exception:
                pass
        hidden, self.hidden = self.hidden, []
        for part in hidden:
            try:
                part.Show()
            except Exception:
                pass
        if self.bar is not None:
            try:
                self.bar.Hide()
            except Exception:
                pass
        gauge = self.gaugeRef()
        if gauge is not None and gauge.__dict__.get('r1gauge') is self:
            gauge.r1gauge = None


def DressGauge(gauge, what, color='red', textured=False):
    """The R1 bar in ``gauge`` (a ui.Gauge after MakeGauge), or None: the original look ("Starý vzhled") or a failure
    (traced, the original gauge back, not tried again for ``what``)."""
    if not UseR1(what):
        return None
    try:
        return GaugeSkin(gauge, what, color, textured)
    except Exception:
        Fail(what)
        return None
