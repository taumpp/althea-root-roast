# -*- coding: utf-8 -*-
"""The notice "Vstup do dungeonu - Kroucený klíč 1 x - Vstupenka použita" in the Althea R1 look (docs/ALTHEA_R1_KIT.md).

ticketnoticemodel decides WHEN (the auto ticket pickup is not shown as a pickup, the used ticket is told once);
this module only draws it: a small toast on the left (x 16, about 30 % of the screen height), it slides in from
the left with a fade (0.22 s, ease-out), stays 4.5 s, and fades out with an 8 px slide (0.35 s). Several notices
queue. Not pickable: it never takes a click from the game.

Presentation styles:

* 'C' - a small R1 window: the graphite frame with the bronze hairline, the title "VSTUP DO DUNGEONU" in Cinzel
  over the red vein, the ticket in the item slot C, its name, "1 x" and "Vstupenka použita" (chosen, default);
* 'A' - a card on the see-through tooltip frame: heading "VSTUPENKA POUŽITA", a quiet divider, a 2 px red mark;
* 'B' - a compact strip on the dark panel: "Pro vstup byla použita:" + the name, the red line under the row.

Another style = change STYLE. The brand red #D30D0E is only an accent (vein / mark / line). Settings -> "Starý
vzhled" (settingslook 'legacy') and a failure while drawing (traced once, not retried) put a chat line instead.
"""
import app
import chat
import item
import ui
import wndMgr

import uikit
import uir1
import uir1layout as L
import uir1tokens as T

import ticketnoticemodel

WHAT = u'Notifikace vstupenky'
STYLE = 'C'

TARGET_X = 16
TOP_RATIO = 0.30
ENTER_SECONDS = 0.22
HOLD_SECONDS = 4.5
LEAVE_SECONDS = 0.35
LEAVE_SLIDE = 8
MAX_QUEUE = 8

TEXTS = {
    ticketnoticemodel.CONTEXT_DUNGEON: {
        'title': u'Vstup do dungeonu',      # C
        'heading': u'Vstupenka použita',    # A
        'lead': u'Pro vstup byla použita:', # B
        'detail_a': u'Pro vstup do dungeonu',
        'detail_c': u'Vstupenka použita',
        'chat': u'Pro vstup do dungeonu byla použita vstupenka: %s (%d x)',
    },
}

_failed = set()


def UseR1():
    return WHAT not in _failed and uir1.UseR1()


def Fail():
    _failed.add(WHAT)
    uir1.TraceFailure(WHAT)


def CountText(count):
    return u'%d \u00d7' % int(count)


def _Faded(color, alpha):
    return uir1.SignedColor((int(round(255 * max(0.0, min(1.0, alpha)))) << 24) | (int(color) & 0xFFFFFF))


def ItemName(vnum):
    try:
        item.SelectItem(int(vnum))
        return item.GetItemName() or u''
    except Exception:
        return u''


def ChatLine(vnum, count, context=ticketnoticemodel.CONTEXT_DUNGEON):
    texts = TEXTS.get(context, TEXTS[ticketnoticemodel.CONTEXT_DUNGEON])
    return texts['chat'] % (ItemName(vnum), int(count))


class Toast(ui.Window):
    """One drawn notice. Layout(style, vnum, count, context) builds it; SetAlpha fades everything."""

    def __init__(self, kit, style, vnum, count, context):
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.AddFlag('not_pick')
        self.kit = kit
        self.style = style if style in ('A', 'B', 'C') else 'C'
        self.layers = []
        self.texts = []          # (line, packed colour)
        self.bars = []           # (bar, packed rgb, alpha)
        self.icon = None
        texts = TEXTS.get(context, TEXTS[ticketnoticemodel.CONTEXT_DUNGEON])
        getattr(self, '_Build' + self.style)(texts, int(vnum), int(count))

    # ----------------------------------------------------------------- pieces
    def _Layer(self, x, y, w, h, ops):
        layer = uir1.Layer(self, x, y, w, h, ops)
        self.layers.append(layer)
        return layer

    def _Text(self, text, x, y, role, color, align='left'):
        line = uir1.Text(self, text, x, y, self.kit.font(role), _Faded(color, 1.0), align=align, valign='top')
        self.texts.append((line, color))
        return line

    def _Bar(self, x, y, w, h, rgb, alpha=1.0):
        bar = uikit.Rect(self, x, y, w, h, rgb, alpha)
        self.bars.append((bar, rgb, alpha))
        return bar

    def _Slot(self, x, y, vnum):
        self._Layer(x, y, T.SLOT, T.SLOT, L.slot_cell(0, 0))
        icon = ui.ExpandedImageBox()
        icon.SetParent(self)
        icon.AddFlag('not_pick')
        try:
            item.SelectItem(vnum)
            icon.LoadImage(item.GetIconImageFileName())
            icon.SetPosition(x, y)
            icon.Show()
        except Exception:
            icon.Hide()
        self.icon = icon

    def _NameAndCount(self, vnum, count, x, y, right):
        countLine = self._Text(CountText(count), right, y + 1, 'text_s', T.IVORY, align='right')
        name = self._Text(u'', x, y, 'text', T.INK)
        uir1.Fit(name, ItemName(vnum), max(40, right - x - uikit.TextWidth(countLine) - 10))
        return name

    # ----------------------------------------------------------------- styles
    def _BuildC(self, texts, vnum, count):
        w = 260
        cell, small = uikit.FontCell(self.kit.font('text')), uikit.FontCell(self.kit.font('text_s'))
        top = T.HEAD_H + T.CONTENT_GAP + 6
        h = max(top + 2 + T.SLOT, top + cell + small) + 10
        self.SetSize(w, h)
        self._Layer(0, 0, w, h, L.frame('window', w, h, 'panel'))
        title = self._Text(uikit.Upper(texts['title']), 0, 0, 'title', T.IVORY)
        title.SetText(uir1.WordGap(title.GetText(), self.kit.font('title')))
        head = L.header(w, uikit.TextWidth(title), close=False)
        title.SetPosition(head['title'][0], uir1.CellTop(T.HEAD_H, self.kit.font('title')))
        self._Layer(0, 0, w, T.HEAD_H + T.VEIN_H, head['vein'])
        self._Slot(14, top + 2, vnum)
        self._NameAndCount(vnum, count, 54, top, w - 14)
        self._Text(texts['detail_c'], 54, top + cell, 'text_s', T.MUTED)

    def _BuildA(self, texts, vnum, count):
        w = 268
        cell, small = uikit.FontCell(self.kit.font('text')), uikit.FontCell(self.kit.font('text_s'))
        head = 25
        top = head + 5
        h = max(top + T.SLOT, top + cell + small) + 8
        self.SetSize(w, h)
        self._fill = self._Bar(1, 1, w - 2, h - 2, uir1.TOOLTIP_FILL, uir1.TOOLTIP_FILL_ALPHA)
        self._Layer(0, 0, w, h, L.frame('tooltip', w, h))
        self._Bar(1, 8, 2, h - 16, T.RED & 0xFFFFFF)
        self._Text(uikit.Upper(texts['heading']), 14, uir1.CellTop(head, self.kit.font('button_s')), 'button_s',
                   T.INK_DIM)
        self._Layer(0, 0, w, h, L.divider(10, head, w - 20))
        self._Slot(14, top + 1, vnum)
        self._NameAndCount(vnum, count, 54, top, w - 12)
        self._Text(texts['detail_a'], 54, top + cell, 'text_s', T.MUTED)

    def _BuildB(self, texts, vnum, count):
        w = 300
        cell, small = uikit.FontCell(self.kit.font('text')), uikit.FontCell(self.kit.font('text_s'))
        h = max(46, 5 + small + cell + 6)
        self.SetSize(w, h)
        self._Layer(0, 0, w, h, L.frame('panel', w, h, 'panel_dark'))
        self._Slot(7, (h - T.SLOT) // 2, vnum)
        self._Text(texts['lead'], 47, 4, 'text_s', T.INK_DIM)
        self._NameAndCount(vnum, count, 47, 4 + small, w - 12)
        self._Layer(0, 0, w, h, L.band_line(2, h - 1, w - 4))

    # ----------------------------------------------------------------- fading
    def SetAlpha(self, alpha):
        alpha = max(0.0, min(1.0, float(alpha)))
        for layer in self.layers:
            layer.ops.SetAlpha(alpha)
        for line, color in self.texts:
            line.SetPackedFontColor(_Faded(color, alpha))
        for bar, rgb, base in self.bars:
            bar.SetColor(uikit.GenerateColor(rgb, base * alpha))
        if self.icon is not None:
            self.icon.SetAlpha(alpha)

    def Destroy(self):
        for layer in self.layers:
            layer.Destroy()
        self.layers, self.texts, self.bars, self.icon = [], [], [], None
        self.Hide()


class TicketNotice(ui.Window):
    """The queue and the motion. Push(vnum, count, context); the game calls OnUpdate every frame (it is a window: the
    engine calls it while shown)."""

    def __init__(self, style=None):
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.AddFlag('not_pick')
        self.style = style or STYLE
        self.queue = []
        self.toast = None
        self.state = 'idle'
        self.started = 0.0
        self.SetSize(1, 1)

    def Push(self, vnum, count, context=ticketnoticemodel.CONTEXT_DUNGEON):
        if not UseR1():
            chat.AppendChat(chat.CHAT_TYPE_INFO, ChatLine(vnum, count, context))
            return False
        self.queue.append((int(vnum), int(count), context))
        del self.queue[:-MAX_QUEUE]
        if self.state == 'idle':
            self._Next()
        return True

    def _Next(self):
        self._Drop()
        if not self.queue:
            self.state = 'idle'
            self.Hide()
            return
        vnum, count, context = self.queue.pop(0)
        try:
            toast = Toast(uir1.Kit(), self.style, vnum, count, context)
            toast.SetParent(self)
            toast.SetPosition(0, 0)
            toast.Show()
        except Exception:
            Fail()
            self._Drop()
            chat.AppendChat(chat.CHAT_TYPE_INFO, ChatLine(vnum, count, context))
            self.queue = []
            self.state = 'idle'
            self.Hide()
            return
        self.toast = toast
        self.SetSize(toast.GetWidth(), toast.GetHeight())
        self.state = 'enter'
        self.started = app.GetTime()
        self._Place(-toast.GetWidth(), 0.0)
        self.Show()
        self.SetTop()

    def _Drop(self):
        if self.toast is not None:
            self.toast.Destroy()
            self.toast = None

    def _Top(self):
        return max(110, int(wndMgr.GetScreenHeight() * TOP_RATIO))

    def _Place(self, x, alpha):
        self.SetPosition(int(x), self._Top())
        if self.toast is not None:
            self.toast.SetAlpha(alpha)

    def OnUpdate(self):
        if self.toast is None:
            return
        elapsed = max(0.0, app.GetTime() - self.started)
        w = self.toast.GetWidth()
        if self.state == 'enter':
            t = min(1.0, elapsed / ENTER_SECONDS)
            eased = 1.0 - pow(1.0 - t, 3)
            self._Place(-w + (TARGET_X + w) * eased, t)
            if t >= 1.0 - 1e-6:
                self.state, self.started = 'hold', app.GetTime()
        elif self.state == 'hold':
            if elapsed >= HOLD_SECONDS:
                self.state, self.started = 'leave', app.GetTime()
        elif self.state == 'leave':
            t = min(1.0, elapsed / LEAVE_SECONDS)
            self._Place(TARGET_X - LEAVE_SLIDE * t, 1.0 - t)
            if t >= 1.0 - 1e-6:
                self._Next()

    def Destroy(self):
        self.queue = []
        self._Drop()
        self.state = 'idle'
        self.Hide()
