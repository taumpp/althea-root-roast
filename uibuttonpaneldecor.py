"""Badge / state overlay drawn on one button-panel button (``buttonpanelbadges.Decor``).

A non-pickable child of the button, so clicks, hover and the right-click menu
stay the button's own. Two geometries:

* ``KIND_MEDALLION`` - the 28x28 minimap launcher (also the More/picker grids);
  rim 36x36 at (-4,-4), countdown disc 24x24 at (2,2), dot 11 px at (18,-2),
  number badge 18 px at (14,-4) (it overhangs the top-right edge like the album
  badge but stays inside the 6 px gap of the More grid and below the screen top);
* ``KIND_RAIL`` - the 37x37 rail carrier with its 24x24 icon at (7,5); frame
  37x37 at (0,0), countdown square 26x26 at (6,4), dot 11 px at (25,1), number
  badge 19 px at (20,0) (inside the 42 px rail column);
* ``KIND_DOT`` - a "More" control of any size: only the dot, at ``dot``.

Owner 2026-10-04 (in-game screenshot, "9+" unreadable): number badges 14/16 ->
18/19 px with 11/12 b digits (two digits one size smaller, never below 10),
countdown text 9/10 -> 11/12 b, cream with the dark outline, and the dots
9 -> 11 px. The countdown text drops lower while a number badge is shown so
the badge never covers it.

The countdown uses the native image cool time (``ImageBox.SetCoolTime``): the
dark sector covers the remaining part and shrinks by itself; the text in the
middle is refreshed here. The ruby badge pulses like the pet-album reminder
(2.4 s, 70-100 % opacity, never invisible) when ``pulse`` is on; the gold one
never pulses. ``STATE_RUNNING`` turns a spark around the rim; ``STATE_ROLLING``
(the Switchbot) plays the green glow of the Switchbot slot round the edge.
"""
import math

import app
import ui

import buttonpanelbadges as badges

ART = 'd:/ymir work/ui/game/crimson_ember/button_panel_badges/'
KIND_MEDALLION = 'medallion'
KIND_RAIL = 'rail'
KIND_DOT = 'dot'   # a "More" control: only the aggregated dot (Strongest), at ``dot``

PULSE_PERIOD = 2.4
SPARK_PERIOD = 1.6
CREAM = 0xFFF4DA9C
VEIL_TEXT = 0xFFC8BEAA
IVORY = 0xFFF6EEE0      # uir1tokens.IVORY: the number of an R1 channel launcher

WindowDestroy = getattr(ui, 'WindowDestroy', lambda method: method)

_GEOMETRY = {
    KIND_MEDALLION: dict(
        size=(28, 28), ring=('ring_medallion.png', -4, -4), spark=('spark_medallion.png', -4, -4),
        cool=('cool_medallion.png', 2, 2), veil=('veil_medallion.png', 0, 0), centre=(14, 14), below=(14, 19),
        glow=('glow/medallion_%02d.png', -4, -4),
        dot=(18, -2), count=('count_action_18.png', 14, -4, 18, 11), font=11),
    KIND_RAIL: dict(
        size=(37, 37), ring=('frame_rail.png', 0, 0), spark=('spark_rail.png', 0, 0),
        cool=('cool_rail.png', 6, 4), veil=('veil_rail.png', 0, 0), centre=(19, 17), below=(19, 25),
        glow=('glow/rail_%02d.png', 0, 0),
        dot=(25, 1), count=('count_action_19.png', 20, 0, 19, 12), font=12),
}
# Switchbot glow: frames from tools/build_button_panel_badges.py, 2 UI ticks each (~0.93 s).
GLOW_FRAMES = 28
GLOW_DELAY = 2
# Two-digit numbers ("9+", "12") use one size smaller, but never below this.
MIN_COUNT_FONT = 10


def _image(parent, name, x, y, expanded=False):
    image = ui.ExpandedImageBox() if expanded else ui.ImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(name if name.startswith('d:/') else ART + name)
    image.SetPosition(x, y)
    image.Hide()
    return image


def _text(parent, font):
    line = ui.TextLine()
    line.SetParent(parent)
    line.AddFlag('not_pick')
    line.SetFontName('Tahoma:%db' % font)
    line.SetHorizontalAlignCenter()
    line.SetVerticalAlignCenter()
    if hasattr(line, 'SetOutline'):
        line.SetOutline(True)
    line.Hide()
    return line


def NumeralFont(kind, text):
    """Font of the big number of an R1 launcher (``Decor.numeral``): Cinzel between the two red arrows (one size
    smaller for two digits, CH99), Tahoma bold with an EXE that does not render the Althea fonts (uikit.FontSet)."""
    try:
        import uikit
        serif = uikit.FontSet() == 'B'
    except Exception:
        serif = False
    one = len(text) < 2
    if kind == KIND_RAIL:
        return ('Althea Caps:21a' if one else 'Althea Caps:15a') if serif else ('Tahoma:14b' if one else 'Tahoma:12b')
    return ('Althea Caps:17a' if one else 'Althea Caps:13a') if serif else ('Tahoma:13b' if one else 'Tahoma:11b')


def PulseAlpha(now):
    """Shared clock of every ruby badge (same curve as the pet-album reminder)."""
    return 0.70 + 0.30 * (0.5 - 0.5 * math.cos(2.0 * math.pi * now / PULSE_PERIOD))


def _alpha_color(alpha, rgb):
    color = (int(alpha * 255) << 24) | (rgb & 0xFFFFFF)
    return color - 0x100000000 if color >= 0x80000000 else color


def MatchAlbumRailBadge(badge):
    """Give the pet button's album count (``uipetalbumcapturebadge``, 16 px art)
    the rail number badge's 19 px art, font and place: both sit in the same
    corner and must not differ in size. The album art file stays unchanged."""
    name, x, y, size, font = _GEOMETRY[KIND_RAIL]['count']
    try:
        badge.size, badge.fontSize = size, font
        badge.SetSize(size, size)
        badge.SetPosition(x, y)
        badge.background.LoadImage(ART + name)
        badge.label.SetPosition(size // 2, size // 2)
        if hasattr(badge.label, 'SetOutline'):
            badge.label.SetOutline(True)
        badge.count = None   # re-apply the font on the next refresh
        badge.Refresh()
    except (AttributeError, TypeError):
        pass


def _Ring(kind, ring):
    """The rim of an open window / the current channel: on a medallion in the R1 look the inner ring of the R1
    medallion in a brighter red (althea_r1_minimapa/ring_active.png, minimap A2) instead of the gold rim."""
    if kind == KIND_MEDALLION:
        try:
            import minimappanelicons
            path = minimappanelicons.R1Art('ring_active.png')
        except Exception:
            path = None
        if path:
            return (path,) + tuple(ring[1:])
    return ring


class ButtonDecor(ui.Window):
    def __init__(self, button, kind=KIND_MEDALLION, dot=None):
        ui.Window.__init__(self)
        self.button = button
        self.kind = kind if kind in _GEOMETRY or kind == KIND_DOT else KIND_MEDALLION
        geometry = dict(_GEOMETRY.get(self.kind, _GEOMETRY[KIND_MEDALLION]))
        if self.kind == KIND_DOT:
            geometry['dot'] = tuple(dot) if dot else (13, -3)
            geometry.pop('glow', None)
        self.geometry = geometry
        self.SetParent(button)
        self.SetPosition(0, 0)
        self.SetSize(*geometry['size'])
        self.AddFlag('not_pick')
        self.ring = _image(self, *_Ring(self.kind, geometry['ring']))
        self.spark = _image(self, *geometry['spark'], expanded=True)
        # Created here (under the badge and the text); its frames load on first use.
        self.glow = None
        if 'glow' in geometry:
            self.glow = ui.AniImageBox()
            self.glow.SetParent(self)
            self.glow.AddFlag('not_pick')
            self.glow.SetPosition(*geometry['glow'][1:])
            self.glow.Hide()
        self.glowLoaded = False
        self.veil = _image(self, *geometry['veil'])
        self.cool = _image(self, *geometry['cool'])
        self.label = _text(self, geometry['font'])
        self.labelFont = 'Tahoma:%db' % geometry['font']
        self.label.SetPosition(*geometry['centre'])
        self.labelPlace = geometry['centre']
        dx, dy = geometry['dot']
        self.dots = {
            badges.BADGE_ACTION: _image(self, 'dot_action.png', dx, dy),
            badges.BADGE_INFO: _image(self, 'dot_info.png', dx, dy),
        }
        name, bx, by, size, font = geometry['count']
        self.countImage = _image(self, name, bx, by)
        self.countText = _text(self, font)
        self.countText.SetPosition(bx + size // 2, by + size // 2)
        self.countSize = (size, font)
        self.decor = badges.EMPTY
        self.pulse = True
        self.coolEnd = None
        self.coolTotal = None
        self.flashing = False
        self.Show()

    def __del__(self):
        ui.Window.__del__(self)

    # State ----------------------------------------------------------------------
    def SetDecor(self, decor, pulse=True):
        decor = decor or badges.EMPTY
        if decor == self.decor and bool(pulse) == self.pulse and (decor.remaining is None) == (self.coolEnd is None):
            return
        self.decor = decor
        self.pulse = bool(pulse)
        self._ApplyState(decor)
        self._ApplyCountdown(decor)
        self._ApplyBadge(decor)
        self._ApplyLabel()

    def _ApplyState(self, decor):
        state = decor.state
        if state in (badges.STATE_ACTIVE, badges.STATE_RUNNING, badges.STATE_CURRENT):
            self.ring.Show()
        else:
            self.ring.Hide()
        if state == badges.STATE_RUNNING:
            self.spark.Show()
        else:
            self.spark.Hide()
        self._ShowGlow(state == badges.STATE_ROLLING)
        if state == badges.STATE_UNAVAILABLE:
            self.veil.Show()
        else:
            self.veil.Hide()
        # The current channel stays bright: gold rim only. The pressed visual of
        # the launchers is the dimmed one (owner 2026-10-04: "Kanál 1 je šedý").
        flash = bool(decor.flash)
        if flash != self.flashing and self.button is not None:
            try:
                (self.button.EnableFlash if flash else self.button.DisableFlash)()
            except (AttributeError, TypeError):
                pass
        self.flashing = flash

    def _ShowGlow(self, show):
        if self.glow is None:
            return
        if not show:
            self.glow.Hide()
            return
        if not self.glowLoaded:
            self.glowLoaded = True
            pattern = self.geometry['glow'][0]
            for index in range(GLOW_FRAMES):
                self.glow.AppendImage(ART + pattern % index)
            self.glow.SetDelay(GLOW_DELAY)
        self.glow.Show()

    def _ApplyCountdown(self, decor):
        if decor.remaining is None:
            self.coolEnd = self.coolTotal = None
            self.cool.Hide()
            return
        now = app.GetTime()
        end = now + decor.remaining
        total = decor.total or decor.remaining
        # Re-arm only on a real change: providers report every tick.
        if self.coolEnd is None or abs(end - self.coolEnd) > 1.0 or total != self.coolTotal:
            self.coolEnd, self.coolTotal = end, total
            self.cool.SetCoolTime(float(total))
            self.cool.SetStartCoolTime(float(end - total))
        self.cool.Show()

    def _ApplyBadge(self, decor):
        for kind, image in self.dots.items():
            if decor.badge == kind and not decor.count:
                image.Show()
            else:
                image.Hide()
        if decor.badge and decor.count:
            label = getattr(decor, 'BadgeLabel', None)
            text = label() if label is not None else badges.BadgeText(decor.count)
            size, font = self.countSize
            countFont = 'Tahoma:%db' % max(MIN_COUNT_FONT, font - (1 if len(text) > 1 else 0))
            if countFont != getattr(self, 'countFont', None):
                # A font swap alone keeps the old glyph layout (CTextLine::SetFontName): empty the line first.
                self.countText.SetText('')
                self.countText.SetFontName(countFont)
                self.countFont = countFont
            self.countText.SetText(text)
            self.countImage.Show()
            self.countText.Show()
        else:
            self.countImage.Hide()
            self.countText.Hide()
        self._Pulse(app.GetTime())

    def _ApplyLabel(self):
        countdown = self.CountdownText(app.GetTime())
        written = getattr(self.decor, 'ShowsCountdownText', None)
        if written is not None and not written():
            countdown = ''              # the seconds ride in the badge (buttonpanelbadges.SecondsBadge)
        text = countdown or self.decor.label
        if text:
            # Below the centre while a number badge sits in the top-right corner.
            place = self.geometry['below'] if self.decor.badge and self.decor.count else self.geometry['centre']
            if place != self.labelPlace:
                self.labelPlace = place
                self.label.SetPosition(*place)
            numeral = self.decor.numeral and not countdown
            font = NumeralFont(self.kind, text) if numeral else 'Tahoma:%db' % self.geometry['font']
            if font != self.labelFont:
                # A font swap alone keeps the old glyph layout (CTextLine::SetFontName): empty the line first.
                self.label.SetText('')
                self.label.SetFontName(font)
                self.labelFont = font
            self.label.SetText(text)
            if numeral:
                colour = IVORY
            else:
                colour = VEIL_TEXT if self.decor.state == badges.STATE_UNAVAILABLE else CREAM
            self.label.SetPackedFontColor(colour)
            self.label.Show()
        else:
            self.label.Hide()

    def CountdownText(self, now):
        if self.coolEnd is None:
            return ''
        return badges.FormatRemaining(self.coolEnd - now)

    # Animation ------------------------------------------------------------------
    def _Pulse(self, now):
        decor = self.decor
        alpha = PulseAlpha(now) if self.pulse and decor.badge == badges.BADGE_ACTION else 1.0
        target = self.countImage if decor.count else self.dots.get(decor.badge)
        if target is not None and hasattr(target, 'SetAlpha'):
            target.SetAlpha(alpha)
        if decor.count:
            self.countText.SetPackedFontColor(_alpha_color(alpha, CREAM))

    def OnUpdate(self):
        if self.decor.IsEmpty():
            return
        now = app.GetTime()
        if self.decor.badge:
            self._Pulse(now)
        if self.decor.state == badges.STATE_RUNNING:
            if self.kind == KIND_MEDALLION:
                self.spark.SetRotation((now % SPARK_PERIOD) / SPARK_PERIOD * 360.0)
            else:
                # The octagon is not round: step the spark by quarter turns.
                self.spark.SetRotation(90.0 * int((now % SPARK_PERIOD) / SPARK_PERIOD * 4))
        if self.coolEnd is not None:
            if now >= self.coolEnd:
                self.coolEnd = self.coolTotal = None
                self.cool.Hide()
            self._ApplyLabel()

    @WindowDestroy
    def Destroy(self):
        if self.flashing and self.button is not None:
            try:
                self.button.DisableFlash()
            except (AttributeError, TypeError):
                pass
        self.Hide()
        self.button = None
        self.ring = self.spark = self.veil = self.cool = self.label = self.glow = None
        self.dots = {}
        self.countImage = self.countText = None
