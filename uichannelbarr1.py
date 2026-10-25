# -*- coding: utf-8 -*-
"""The channel bar in the R1 look (``uichannelbar`` keeps the model, the probe, the pinning and the original look).

Two styles, chosen in Settings -> Vzhled -> "Lišta kanálů" (``settingslook`` key ``channel_bar_style``):

* ``StepperBar`` ("Krokovač", the default), 30 px high: ‹ and › are CH- / CH+ (``uichannelbar.StepTarget``: round
  the ends like the CH+ / CH- shortcuts, past a hidden VIP or an offline channel), "CH 3" in Cinzel, a small row of
  evenly spaced numbers for a direct jump, then the pin and the X. Minimap A2 (owner 8. 10. 2026): no red line, no
  mark and no load dot in the bar - the current number is only brighter (ivory), the others are dimmed, an offline
  one is dimmed further and not clickable; the load of a channel is in its tooltip (and in the list style).
* ``ListBar`` ("Seznam"), 142 px wide: an R1 header "KANÁL" with the pin and the X, one row per channel with its
  load in words (volno / rušno / plno / offline / tady jsi), the current row selected.

Both: CH99, the hub and an instance show the reason in every tooltip and dim every channel (the server refuses
the change there); the pin (closed = a movable window that never closes, shows again after login, remembers its
place) works like the lock of the original bar; the whole bar but its controls drags it ('float' + 'movable', every
text and image 'not_pick'). An exception while the bar refreshes hands over to the original bar
(``uichannelbar.FallBack``, traced).
"""
import ui

import uir1
import uir1tokens as T
import uir1kanalart as A
import uichannelbar as model
from settingslocale import Text as Tr

AMBER = 0xFFDEA646           # busy: the only warm colour besides the red
SEPARATOR = 0xFF3C3838
HOVER_ALPHA = 0.55

STEPPER_H = 30
PAD = 6
ARROW_W, ARROW_H = 16, 24
NUM_W = 19                   # one cell per number (Noto Sans digits have one width): evenly spaced
LABEL_MIN = 40
PIN = 13
LIST_W = 142
ROW_H = 19
ROWS_TOP = T.HEAD_H + 3


def Create(interface, kind):
    """The R1 bar of ``kind`` ('stepper' / 'list'), laid out once (a failure raises here, before it is shown)."""
    window = (ListBar if kind == model.LIST else StepperBar)(interface)
    window.Build()
    return window


def _Image(parent, path, x, y):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(path)
    image.SetPosition(int(x), int(y))
    image.Show()
    image.r1_path = path
    return image


def _Swap(image, path):
    """LoadImage only when the texture changes (a new image instance every time)."""
    if image.r1_path != path:
        image.LoadImage(path)
        image.r1_path = path


def ArtPath(name):
    return A.ROOT + name


# --------------------------------------------------------------------------- tooltip
class Tip(uir1.Hint):
    """The bar's hover tooltip: the one R1 hint (uir1.Hint) - lines [(text, colour)], the
    first one the name above the vein, the others under it in their own colour (the load of a channel amber / red);
    above the control (or right of it), never over it, clamped to the screen. Floating and never pickable."""

    def ShowAt(self, owner, lines, side='above'):
        lines = list(lines or ())
        title = lines[0][0] if lines else ''
        x, y = owner.GetGlobalPosition()
        uir1.Hint.ShowAt(self, (x, y, owner.GetWidth(), owner.GetHeight()), title, lines[1:],
                         'right' if side == 'right' else 'above', owner=owner)

    def Texts(self):
        """The shown lines (the name first) - what the player reads."""
        if not self.IsShow():
            return []
        return [self.title.GetText()] + [line.GetText() for line in self.lines if line.IsShow()]


# --------------------------------------------------------------------------- controls
class Control(uir1.Interactive):
    """A clickable part of the bar: hover band (made first), the tooltip of ``tip()`` while hovered."""

    side = 'above'

    def __init__(self, bar, w, h, band=None):
        uir1.Interactive.__init__(self)
        self.bar = bar
        self.SetParent(bar)
        self.SetSize(w, h)
        self.band = None
        if band is not None:
            bx, by, bw, bh = band
            self.band = uir1.Rect(self, bx, by, bw, bh, T.BAND_HOVER, HOVER_ALPHA)
            self.band.Hide()
        self.lines = []
        self.Show()

    def SetTip(self, lines):
        self.lines = lines
        if self.hovered and self.bar.tip is not None:
            self.bar.tip.ShowAt(self, lines, self.side)

    def OnMouseOverIn(self):
        uir1.Interactive.OnMouseOverIn(self)
        if self.lines and self.bar.tip is not None:
            self.bar.tip.ShowAt(self, self.lines, self.side)

    def OnMouseOverOut(self):
        uir1.Interactive.OnMouseOverOut(self)
        if self.bar.tip is not None:
            self.bar.tip.HideFor(self)

    def paint(self):
        if self.band is not None:
            if self.hovered and self.enabled:
                self.band.Show()
            else:
                self.band.Hide()


class Arrow(Control):
    """‹ / ›: CH- / CH+ (the R1 chevron, its hover band, dimmed where no change is possible)."""

    def __init__(self, bar, direction, event):
        Control.__init__(self, bar, ARROW_W, ARROW_H, (0, 3, ARROW_W, 18))
        self.direction = direction
        self.glyph = uir1.Image(self, uir1.ChevronPath(direction, 'normal'), 3 if direction == 'left' else 4, 7)
        self.glyph.r1_path = uir1.ROOT + uir1.ChevronPath(direction, 'normal')
        self.callback = event
        self.paint()

    def paint(self):
        Control.paint(self)
        state = 'disabled' if not self.enabled else ('hover' if self.hovered else 'normal')
        _Swap(self.glyph, uir1.ROOT + uir1.ChevronPath(self.direction, state))


class Number(Control):
    """One channel of the stepper's number row."""

    def __init__(self, bar, kit, channel):
        Control.__init__(self, bar, NUM_W, ARROW_H, (0, 2, NUM_W, 20))
        self.channel = channel
        self.text = uir1.Text(self, str(channel), NUM_W // 2, 11, kit.font('text_s'), T.INK_DIM, align='center')
        self.current, self.load = False, ''
        self.callback = lambda: bar.Switch(channel)

    def Apply(self, cell):
        self.current, self.load = cell.current, cell.load
        self.SetTip(_CellTip(cell))
        (self.Enable if cell.enabled else self.Disable)()

    def paint(self):
        Control.paint(self)
        current = getattr(self, 'current', False)
        if getattr(self, 'text', None) is None:
            return
        if current or (self.hovered and self.enabled):
            colour = T.IVORY
        elif not self.enabled:
            colour = T.DISABLED
        else:
            colour = T.INK_DIM
        self.text.SetPackedFontColor(colour)


class Pin(Control):
    """The pin (the lock of the original bar): pinned = upright with the red head."""

    def __init__(self, bar, w, h, gx, gy):
        Control.__init__(self, bar, w, h)
        self.pinned = False
        self.glyph = _Image(self, ArtPath('pin/off_normal.png'), gx, gy)
        self.callback = bar.TogglePin
        self.paint()

    def SetPinned(self, pinned):
        self.pinned = bool(pinned)
        if pinned:
            self.SetTip([(Tr('Odepnout lištu', 'Unpin the bar'), T.INK),
                         (Tr('Lištu pak zavřeš křížkem nebo Esc.', 'Then the cross or Esc closes it.'), T.MUTED)])
        else:
            self.SetTip([(Tr('Připnout lištu', 'Pin the bar'), T.INK),
                         (Tr('Připnutá lišta zůstane i po přihlášení.', 'A pinned bar stays, also after login.'),
                          T.MUTED)])
        self.paint()

    def paint(self):
        state = 'hover' if self.hovered else 'normal'
        _Swap(self.glyph, ArtPath('pin/%s_%s.png' % ('on' if getattr(self, 'pinned', False) else 'off', state)))


class Cross(uir1.Close):
    """The plain X of R1 with the bar's tooltip."""

    def __init__(self, bar, event):
        self.bar = bar
        uir1.Close.__init__(self, bar, 0, 0, event)

    def OnMouseOverIn(self):
        uir1.Close.OnMouseOverIn(self)
        if self.bar.tip is not None:
            self.bar.tip.ShowAt(self, [(Tr('Zavřít (Esc)', 'Close (Esc)'), T.INK)])

    def OnMouseOverOut(self):
        uir1.Close.OnMouseOverOut(self)
        if self.bar.tip is not None:
            self.bar.tip.HideFor(self)


def _CellTip(cell):
    lines = [(cell.tooltip, T.INK)]
    if cell.note:
        lines.append((cell.note, AMBER if cell.load == 'busy' else T.RED_HI))
    return lines


def _BlockedReason(cells):
    """The reason every channel is dimmed (hub / CH99 / instance: ``uichannelbar.Layout`` gives every channel that is
    not offline this tooltip and disables it), or ''."""
    for cell in cells:
        if not cell.enabled and not cell.offline:
            return cell.tooltip
    return ''


# --------------------------------------------------------------------------- the bars
class R1Bar(model.BarBehaviour, ui.Window):
    """What both R1 styles share: the frame (made first), the tooltip, the refresh with the fallback."""

    def __init__(self, interface):
        ui.Window.__init__(self)
        self.interface = interface
        self.settings = model.Load()
        self.AddFlag('float')
        self.AddFlag('movable')
        self.kit = uir1.Kit()
        self.tip = None
        self.frame = uir1.Frame(self, 0, 0, 40, 30, 'window')
        self.cells = []
        self.shown = None
        self.nextRefresh = 0.0

    def Build(self):
        self.tip = Tip(self.kit)
        self._Refresh(True)

    def Refresh(self, force=False):
        try:
            self._Refresh(force)
        except Exception:
            model.FallBack(self)

    def _Refresh(self, force):
        cells, tag = self.Model()
        key = (tuple(cell.Key() for cell in cells), tag, self.settings.pinned)
        if key == self.shown and not force:
            return
        self.shown = key
        self.cells = cells
        self.Layout(cells, tag)

    def _Enabled(self, channel):
        return any(cell.channel == channel and cell.enabled and not cell.current for cell in self.cells)

    def _HideTip(self):
        if self.tip is not None:
            self.tip.HideFor()

    def Resize(self, w, h):
        self.SetSize(w, h)
        self.frame.Resize(w, h)

    def Destroy(self):
        self.Hide()
        if self.tip is not None:
            self.tip.Destroy()
        self.tip = None
        self.interface = None


class StepperBar(R1Bar):
    """‹ CH 3 › | 1 2 3 4 5 | pin X (proposal 3, about 250 x 30)."""

    def __init__(self, interface):
        R1Bar.__init__(self, interface)
        kit = self.kit
        self.prev = Arrow(self, 'left', lambda: self.Step(-1))
        self.label = uir1.Text(self, '', 0, STEPPER_H // 2 - 1, kit.font('button'), T.IVORY, align='center')
        self.next = Arrow(self, 'right', lambda: self.Step(1))
        self.separator = uir1.Rect(self, 0, 7, 1, 16, SEPARATOR)
        self.numbers = []
        self.pin = Pin(self, 16, ARROW_H, 2, 6)
        self.close = Cross(self, self.Close)

    def _Number(self, index):
        while len(self.numbers) <= index:
            self.numbers.append(Number(self, self.kit, 0))
        return self.numbers[index]

    def Layout(self, cells, tag):
        current = [cell for cell in cells if cell.current]
        if tag:
            label = tag
        elif current:
            label = 'CH %d' % current[0].channel
        else:
            label = '-'
        self.label.SetText(label)
        lw = max(LABEL_MIN, uir1.TextWidth(self.label) + 6)
        x = PAD - 2
        self.prev.SetPosition(x, 3)
        x = PAD + 14
        self.label.SetPosition(x + lw // 2, STEPPER_H // 2 - 1)
        x += lw
        self.next.SetPosition(x - 2, 3)
        x += 14 + 8
        self.separator.SetPosition(x, 7)
        x += 1 + 6
        reason = _BlockedReason(cells)
        self._ArrowTips(cells, reason)
        for index, cell in enumerate(cells):
            number = self._Number(index)
            if number.channel != cell.channel:
                number.channel = cell.channel
                number.text.SetText(str(cell.channel))
                number.callback = (lambda channel=cell.channel: self.Switch(channel))
            number.SetPosition(x, 3)
            number.Apply(cell)
            number.Show()
            x += NUM_W
        for number in self.numbers[len(cells):]:
            number.Hide()
        x += 6
        self.pin.SetPosition(x - 2, 3)
        self.pin.SetPinned(self.settings.pinned)
        x += PIN
        if self.settings.pinned:
            self.close.Hide()
        else:
            x += 6
            self.close.SetPosition(x - 4, 5)
            self.close.Show()
            x += 12
        self.Resize(x + PAD, STEPPER_H)

    def _ArrowTips(self, cells, reason):
        hint = (Tr('Klávesu nastavíš v Nastavení > Klávesy.', 'Set a key in Settings > Keys.'), T.MUTED)
        for arrow, step, text in ((self.prev, -1, Tr('CH- : přepnout na CH%d', 'CH- : switch to CH%d')),
                                  (self.next, 1, Tr('CH+ : přepnout na CH%d', 'CH+ : switch to CH%d'))):
            target = model.StepTarget(cells, step)
            if target is not None:
                arrow.Enable()
                arrow.SetTip([(text % target, T.INK), hint])
            else:
                arrow.Disable()
                arrow.SetTip([(reason or Tr('Jiný kanál teď není k dispozici.', 'No other channel now.'), T.INK)])


class Row(Control):
    """One row of the list: "CH 3" left, its load in words right; selected = the current channel."""

    side = 'right'
    WORDS = {'free': (('volno', 'free'), T.MUTED), 'busy': (('rušno', 'busy'), AMBER),
             'full': (('plno', 'full'), T.RED_HI), 'off': (('offline', 'offline'), T.DISABLED),
             'current': (('tady jsi', 'you are here'), T.IVORY), 'blocked': (('nejde', 'no change'), T.DISABLED)}

    def __init__(self, bar, kit):
        w = LIST_W - 8
        Control.__init__(self, bar, w, ROW_H)
        self.state = 'free'
        self.selected = uir1.Band(self, 0, 0, w, ROW_H)
        self.name = uir1.RowText(self, '', 6, ROW_H, kit.font('button'), T.INK)
        self.word = uir1.RowText(self, '', w - 6, ROW_H, kit.font('text_s'), T.MUTED, align='right')
        self.channel = 0

    def Apply(self, name, state, tip):
        self.state = state
        self.name.SetText(name)
        (cz, en), unused = self.WORDS[state]
        self.word.SetText(Tr(cz, en))
        self.SetTip(tip)
        (self.Enable if state in ('free', 'busy', 'full') else self.Disable)()
        self.paint()

    def paint(self):
        state = getattr(self, 'state', 'free')
        selected = getattr(self, 'selected', None)
        if selected is None:
            return
        hover = self.hovered and self.enabled
        selected.SetState('selected' if state == 'current' else ('hover' if hover else 'normal'))
        if state == 'current' or hover:
            self.name.SetPackedFontColor(T.IVORY)
        elif state in ('off', 'blocked'):
            self.name.SetPackedFontColor(T.DISABLED)
        else:
            self.name.SetPackedFontColor(T.INK)
        colour = self.WORDS[state][1]
        if hover and state == 'free':
            colour = T.INK_DIM
        self.word.SetPackedFontColor(colour)


class ListBar(R1Bar):
    """KANÁL header with the pin and the X, one row per channel with its load (proposal 4, 142 px wide)."""

    def __init__(self, interface):
        R1Bar.__init__(self, interface)
        self.frame.Resize(LIST_W, 60)
        self.header = uir1.Header(self, self.kit, LIST_W, Tr('Kanál', 'Channel'), on_close=self.Close, align='left')
        self.pin = Pin(self, 19, 20, 3, 4)
        self.rows = []

    def _Row(self, index):
        while len(self.rows) <= index:
            self.rows.append(Row(self, self.kit))
        return self.rows[index]

    def Layout(self, cells, tag):
        items = []
        reason = _BlockedReason(cells)
        if tag:
            items.append((None, tag, 'current', [(reason or Tr('Tady jsi.', 'You are here.'), T.INK)]))
        for cell in cells:
            if cell.current:
                state = 'current'
            elif cell.offline:
                state = 'off'
            elif not cell.enabled:
                state = 'blocked'
            else:
                state = cell.load or 'free'
            items.append((cell.channel, 'CH %d' % cell.channel, state, _CellTip(cell)))
        y = ROWS_TOP
        for index, (channel, name, state, tip) in enumerate(items):
            row = self._Row(index)
            row.SetPosition(4, y)
            if channel is not None and row.channel != channel:
                row.callback = (lambda number=channel: self.Switch(number))
            row.channel = channel or 0
            if channel is None:
                row.callback = None
            row.Apply(name, state, tip)
            row.Show()
            y += ROW_H
        for row in self.rows[len(items):]:
            row.Hide()
        close = self.header.close
        cx = close.GetLocalPosition()[0]                    # the X's click area (by the header row, T.X_HIT)
        if self.settings.pinned:
            close.Hide()
            self.pin.SetPosition(cx, 4)                                                       # in the X's place
        else:
            close.Show()
            self.pin.SetPosition(cx - 2 - self.pin.GetWidth(), 4)                            # beside it
        self.pin.SetPinned(self.settings.pinned)
        self.Resize(LIST_W, y + 5)
