# -*- coding: utf-8 -*-
"""The small context menu of the button panels in the R1 look (the minimap launchers and the inventory rail).

``uibuttonpanelcontext.ContextMenu`` stays the window and keeps everything it does: the entries ``(label,
callback)``, the full-screen layer behind it that closes it on any outside click, Escape, the width the callers place
it by (``uibuttonpanelcontext.WIDTH``) and the clamp to the screen. This module is the one shared R1 drawing of it,
in the colours of minimap A2:

* the R1 dialog frame (graphite with the hairline, the panel background, the soft shadow outside);
* one lightly rounded row per entry: the secondary R1 plate of 22 px (``button/secondary_22``), the label in Noto
  Sans on the left. The mouse brightens the row (lighter plate and outline, ivory text); no red line, no mark.

Settings -> "Starý vzhled" keeps the original Crimson buttons. A failure while building or laying out R1 is traced
(uir1.TraceFailure), the original menu is shown and R1 is not tried again in this session.
"""
import uir1
import uir1layout as L
import uir1tokens as T

ROW_H = T.BTN_H_S        # 22 px rounded row
ROW_GAP = 2
PAD = 4                  # frame -> first / last row, left / right
TEXT_X = 10              # label inset in its row
WHAT = u'Kontextová nabídka panelu tlačítek'

_failed = [False]


def Signed(colour):
    """wndMgr wants a signed 32-bit ARGB (the x64 binding ignores values >= 0x80000000)."""
    colour = int(colour) & 0xFFFFFFFF
    return int(colour - 0x100000000 if colour >= 0x80000000 else colour)


def UseR1():
    """R1 unless Settings -> "Starý vzhled" chose the original look, or R1 already failed in this session."""
    return not _failed[0] and uir1.UseR1()


def Failed():
    """Traces the failure; the original menu is used for the rest of the session."""
    _failed[0] = True
    uir1.TraceFailure(WHAT)


def Height(count):
    count = max(1, int(count))
    return 2 * PAD + count * ROW_H + (count - 1) * ROW_GAP


def RowTop(index):
    return PAD + int(index) * (ROW_H + ROW_GAP)


class Row(uir1.Interactive):
    """One entry: the rounded plate and its label; hover = the brighter plate and ivory text."""

    def __init__(self, parent, kit, width):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.w = int(width)
        self.SetSize(self.w, ROW_H)
        self.ops = uir1.Ops(self, L.button(False, True, 'normal', self.w))     # the plate before the label
        self.font = kit.font('text_s')
        self.label = uir1.Text(self, '', TEXT_X, uir1.CellTop(ROW_H, self.font), self.font, Signed(T.INK),
                               valign='top')
        self.paint()

    def Set(self, x, y, width, text, callback):
        self.w = int(width)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, ROW_H)
        self.hovered = self.pressed = False
        uir1.Fit(self.label, text, self.w - 2 * TEXT_X)
        self.SetEvent(callback)
        self.paint()
        self.Show()

    def paint(self):
        state = self.state()
        self.ops.Apply(L.button(False, True, state, self.w))
        bright = state in ('hover', 'pressed')
        self.label.SetPackedFontColor(Signed(T.IVORY if bright else T.INK))


class MenuPanel(object):
    """The R1 frame and rows inside ``parent`` (the menu window). ``Layout(entries, width, run)`` -> height."""

    def __init__(self, parent):
        self.parent = parent
        self.kit = uir1.Kit()
        self.frame = uir1.Frame(parent, 0, 0, 1, Height(1), kind='dialog')     # under the rows made after it
        self.rows = []

    def Layout(self, entries, width, run):
        entries = list(entries)
        width = int(width)
        height = Height(len(entries))
        self.frame.Resize(width, height)
        self.frame.Show()
        for index, (label, callback) in enumerate(entries):
            if index >= len(self.rows):
                self.rows.append(Row(self.parent, self.kit, width - 2 * PAD))
            self.rows[index].Set(PAD, RowTop(index), width - 2 * PAD, label,
                                 lambda chosen=callback: run(chosen))
        for row in self.rows[len(entries):]:
            row.Hide()
        return height

    def Shown(self):
        return [row for row in self.rows if row.IsShow()]

    def Hide(self):
        for widget in [self.frame] + self.rows:
            try:
                widget.Hide()
            except Exception:
                pass

    def Destroy(self):
        self.Hide()
        for row in self.rows:
            row.SetEvent(None)
        self.rows = []
        self.frame = None
        self.parent = None
