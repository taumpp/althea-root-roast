# -*- coding: utf-8 -*-
"""Systémové zprávy (uisystemnotifications.MessageWindow) in the Althea R1 look "Krvavá žíla".

The window keeps its width (332), its flags (movable, float), the three message cards with the scroll bar and the
mouse wheel, "Otevřít" on a card, "Nastavení" and "Přečíst vše" in the footer and the hover tooltip with the whole
message (the tooltip is not changed). uisystemnotifications keeps all of that logic (layout, scrolling, reading,
navigation); this module only draws it in R1 (same attribute names):

* the R1 frame and the red R1 header (title, vein, plain X) over the window's own board (uir1.BoardSkin); the crimson
  board art and the title bar are hidden, the frame spans the whole width;
* every message a card: an R1 panel (a dark well with a thin outline) with the source ("Switchbot") and the time in a
  heading over a quiet divider, the icon (an item in the item slot C), the title and the text in Noto Sans; an unread
  card is brighter than a read one, the mouse over a card only lightens it (no red line, no plate);
* "Otevřít" is a link in the brand red #D30D0E (grey once the message is read), "Nastavení" a grey link with the
  original gear (tinted grey, the bronze of the texture is gone), "Přečíst vše" an R1 button, the narrow R1 scroll bar;
* compact: the cards are 66 px (80 in the original) and the footer is lower, so the whole window is 285 px high
  (316 in the original).

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building or laying out
R1 restores the original look (traced to syserr) and R1 is not tried again in this session.
"""
import time
import weakref

import ui

import uir1
import uir1layout as L
import uir1tokens as T

import uipermanenttasksr1 as R
import uisystemnotifications as N
from systemnotificationlocale import Text

WHAT = u'Systémové zprávy'

WIDTH = 332
LIST_TOP = 31                   # the cards start right under the header (34 in the original)
ROW_H = 66                      # a card (76 in the original)
PITCH = 70                      # card + 4 px gap (80 in the original)
FOOTER = 44                     # under the last card (42 in the original, the controls are 26 px)
FOOTER_Y = 38                   # footer controls: 12 px above the bottom edge
PAD = T.PAD
ROW_X = PAD
ROW_W = WIDTH - 2 * PAD                         # 308
SCROLL_X = WIDTH - PAD - T.SCROLL_W             # 312
ROW_W_SCROLL = SCROLL_X - 6 - ROW_X             # 294
FOOTER_H = T.BTN_H                              # the button and the link share the row

HEAD_H = 21                     # the heading of a card: source and time
DIVIDER_Y = 20
INNER = 8                       # the divider keeps this from the sides of a card
SIDE = 10                       # texts keep this from the sides of a card
ICON_X, ICON_Y, ICON_W = 8, 27, 41              # the 41 x 32 box of the original icon
TEXT_X = 57
NAME_Y = 26
MESSAGE_Y = 44
GEAR_SIZE = 20
GEAR_TINT = (0.70, 0.78, 1.00)  # bronze x this = neutral grey (the texture is R 184 / G 165 / B 128 at its brightest)
LINK_GAP = 6

# Where the original window got its numbers (set on the window while R1 is drawn).
METRICS = dict(LIST_TOP=LIST_TOP, ROW_HEIGHT=PITCH, FOOTER=FOOTER, ROW_X=ROW_X, ROW_WIDTH=ROW_W,
               ROW_WIDTH_SCROLL=ROW_W_SCROLL, SCROLL_X=SCROLL_X, FOOTER_Y=FOOTER_Y, SETTINGS_X=PAD)


def _Height(window):
    return window.LIST_TOP + window.capacity * window.ROW_HEIGHT + window.FOOTER


# --------------------------------------------------------------------------- the card
class Row(N._MessageRow):
    """A message card with the widgets of _MessageRow in R1; the window drives it exactly as the original row
    (SetEntry, the hover hint, a click on the card activates the message)."""

    def __init__(self, owner, kit):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.SetParent(owner)
        self.kit = kit
        self.identity = None
        self.entry = None
        self.pressed = False
        self.hovered = False
        self.active = True                  # False once R1 fell back: the window's loop may still call this row
        font, small, heading = kit.font('text'), kit.font('text_s'), kit.font('text_sb')
        self.panel = uir1.Frame(self, 0, 0, ROW_W, ROW_H, 'panel')          # first: under everything
        self.band = uir1.Band(self, 2, 2, ROW_W - 4, ROW_H - 4)             # the lighter well under the mouse
        self.divider = uir1.Divider(self, INNER, DIVIDER_Y, ROW_W - 2 * INNER)
        self.category = uir1.Text(self, '', SIDE, uir1.CellTop(HEAD_H, heading), heading, R.Signed(T.INK_DIM),
                                  valign='top')
        self.stamp = uir1.Text(self, '', ROW_W - SIDE, uir1.CellTop(HEAD_H, small), small, R.Signed(T.MUTED),
                               align='right', valign='top')
        self.cell = uir1.SlotCell(self, ICON_X, ICON_Y)                     # the item slot C under an item icon
        self.cell.Hide()
        self.icon = ui.ImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.name = uir1.Text(self, '', TEXT_X, NAME_Y, font, R.Signed(T.INK), valign='top')
        self.message = uir1.Text(self, '', TEXT_X, MESSAGE_Y, small, R.Signed(T.INK_DIM), valign='top')
        self.openLabel = uir1.Text(self, Text("OPEN"), ROW_W - SIDE, NAME_Y, small, R.Signed(T.RED), align='right',
                                   valign='top')

    def SetEntry(self, entry, width):
        if not self.active:
            return                          # R1 fell back while the window was laying its rows out
        try:
            self._SetEntry(entry, width)
        except Exception:
            guard = self.owner.__dict__.get('r1')
            if not guard:
                raise                       # still building: Build() falls back
            R.Fail(WHAT)
            guard.Fallback()

    def _SetEntry(self, entry, width):
        entry = N.DisplayEntry(entry)
        self.entry = entry
        self.identity = entry["id"]
        self.SetSize(width, ROW_H)
        self.panel.Resize(width, ROW_H)
        self.band.Resize(2, 2, width - 4, ROW_H - 4)
        self.divider.SetSize(width - 2 * INNER, T.RULE_H)
        self.divider.Apply(L.divider(0, 0, width - 2 * INNER))
        key = N.CATEGORY_STYLE[entry["category"]][0]
        self.category.SetText(Text(key))
        self.stamp.SetPosition(width - SIDE, self.stamp.GetLocalPosition()[1])
        self.stamp.SetText(time.strftime("%H:%M", time.localtime(entry["created"])))
        self.openLabel.SetPosition(width - SIDE, NAME_Y)
        open_width = self.openLabel.GetTextSize()[0]
        N._Fit(self.category, Text(key), width - self.stamp.GetTextSize()[0] - 3 * SIDE)
        N._Fit(self.name, entry["title"], width - TEXT_X - open_width - 2 * SIDE)
        N._Fit(self.message, entry["message"], width - TEXT_X - SIDE)
        self._Icon(entry)
        self._Paint()
        self.Show()

    def _Icon(self, entry):
        self.icon.Hide()
        self.cell.Hide()
        path = N.IconPath(entry)
        if not path:
            return
        try:
            self.icon.LoadImage(path)
            x = ICON_X + (ICON_W - self.icon.GetWidth()) // 2
            y = ICON_Y + (32 - self.icon.GetHeight()) // 2
            self.icon.SetPosition(x, y)
            self.icon.Show()
            if entry["category"] != "dungeon":          # an item, not a boss portrait
                self.cell.SetPosition(x, y)
                self.cell.Show()
        except (RuntimeError, OSError):
            pass

    def _Paint(self):
        entry = self.entry
        if not entry:
            return
        unread = not entry["read"]
        self.band.SetState('hover' if self.hovered else 'normal')
        self.category.SetPackedFontColor(R.Signed(T.INK_DIM if unread else T.MUTED))
        self.name.SetPackedFontColor(R.Signed(T.IVORY if unread else T.INK_DIM))
        self.message.SetPackedFontColor(R.Signed(T.INK_DIM if unread else T.MUTED))
        if self.pressed:
            link = T.MUTED
        else:
            link = T.RED if unread else (T.INK_DIM if self.hovered else T.MUTED)
        self.openLabel.SetPackedFontColor(R.Signed(link))

    def OnMouseOverIn(self):
        self.hovered = True
        self._Paint()
        if self.entry:
            self.owner.ShowHint(self.entry["title"] + "\n" + self.entry["message"])

    def OnMouseOverOut(self):
        self.pressed = False
        self.hovered = False
        self.owner.HideHint()
        self._Paint()

    def OnMouseLeftButtonDown(self):
        self.pressed = True
        self._Paint()
        return True

    def OnMouseLeftButtonUp(self):
        pressed = self.pressed
        self.pressed = False
        self.owner.HideHint()
        self._Paint()
        if pressed and self.identity is not None:
            self.owner.Activate(self.identity)
        return True

    def Destroy(self):
        self.Hide()
        self.owner = self.entry = None
        self.panel = self.band = self.divider = self.cell = self.icon = None
        self.category = self.stamp = self.name = self.message = self.openLabel = None


# --------------------------------------------------------------------------- "Nastavení"
class Link(uir1.Interactive):
    """The gear and "Nastavení" as a quiet R1 link: grey, brighter under the mouse, dim while pressed."""

    def __init__(self, parent, kit, callback):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.callback = callback
        font = kit.font('text_s')
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.LoadImage(N.GEAR)
        self.icon.SetPosition(0, (FOOTER_H - GEAR_SIZE) // 2)
        self.icon.Show()
        self.label = uir1.Text(self, Text("SETTINGS"), GEAR_SIZE + LINK_GAP, uir1.CellTop(FOOTER_H, font), font,
                               R.Signed(T.INK_DIM), valign='top')
        self.SetSize(GEAR_SIZE + LINK_GAP + uir1.TextWidth(self.label) + 2, FOOTER_H)
        self.paint()
        self.Show()

    def paint(self):
        state = self.state()
        factor, color = {'hover': (1.0, T.IVORY), 'pressed': (0.75, T.MUTED)}.get(state, (0.85, T.INK_DIM))
        self.icon.SetDiffuseColor(GEAR_TINT[0] * factor, GEAR_TINT[1] * factor, GEAR_TINT[2] * factor, 1.0)
        self.label.SetPackedFontColor(R.Signed(color))

    def Destroy(self):
        self.Hide()
        self.callback = None
        self.icon = self.label = None


# --------------------------------------------------------------------------- the skin
class Skin(R.SkinBase):
    rows = ()

    def Build(self):
        win, kit = self.window, self.kit
        title = Text("TITLE")
        try:
            title = win.titleName.GetText() or title
        except Exception:
            pass

        # The controls first (their size decides the footer), then the geometry of the window.
        button = uir1.Button(win, kit, 0, 0, T.BTN_W, Text("MARK_ALL_READ"), event=win.read_all_callback)
        button.FitWidth(T.BTN_W)
        self.own(button)
        metrics = dict(METRICS, READ_X=WIDTH - PAD - button.GetWidth(), INSET=0)

        def apply_geometry():
            for name, value in metrics.items():
                setattr(win, name, value)
            win.SetSize(win.WIDTH, _Height(win))

        def restore_geometry():
            for name in metrics:
                win.__dict__.pop(name, None)
            win.SetSize(win.WIDTH, _Height(win))
        self.reload(restore_geometry, apply_geometry)

        self.board = uir1.BoardSkin(win.board, kit, title, on_close=ui.__mem_func__(win.Close))
        self.hide(win.titleBar)             # the R1 header drags and closes; the bar would lie over its X

        for row in win.rows:
            self.hide(row)
        rows = [self.own(Row(win, kit)) for unused in range(len(win.rows))]
        self.rows = rows
        self.swaps.append((win, 'rows', None, win.rows))
        win.rows = rows

        bar = uir1.ScrollBar(kit)
        bar.SetParent(win)
        bar.SetScrollEvent(ui.__mem_func__(win._Scroll))
        self.swap(win, 'scroll', bar)
        self.swap(win, 'settings', Link(win, kit, win.settings_callback))
        self.swap(win, 'readAll', button)
        self.swap(win, 'empty', uir1.Text(win, Text("EMPTY"), WIDTH // 2, LIST_TOP + 20, kit.font('text_s'),
                                          R.Signed(T.MUTED), align='center', valign='top'))
        win._LayoutRows()
        return self

    def Layout(self, width, height):
        """After the window sized itself (_Frame.SetSize): the frame and the header follow."""
        self.board.Resize(width, height)

    def Undo(self):
        for row in self.rows:
            row.active = False
        R.SkinBase.Undo(self)

    def Destroy(self):
        board = self.board
        self.window = None
        self.widgets, self.swaps, self.hidden, self.moved, self.reloads = [], [], [], [], []
        self.board = None
        if board is not None:
            board.Destroy()


class Guard(object):
    """The window's handle on the skin: every call runs guarded; a failure restores the original look."""

    def __init__(self, skin):
        self.skin = skin

    def __nonzero__(self):
        return self.skin is not None

    __bool__ = __nonzero__

    def Layout(self, width, height):
        if self.skin is None:
            return
        try:
            self.skin.Layout(width, height)
        except Exception:
            R.Fail(WHAT)
            self.Fallback()

    def Fallback(self):
        skin, self.skin = self.skin, None
        if skin is None:
            return
        window = skin.window
        skin.Undo()
        if window is None:
            return
        window.r1 = None
        try:
            window.SetSize(window.WIDTH, _Height(window))
            window._LayoutRows()
        except Exception:
            uir1.TraceFailure(WHAT + u' (original look)')

    def Destroy(self):
        if self.skin is not None:
            self.skin.Destroy()
        self.skin = None


def Build(window):
    """The R1 look of a MessageWindow (its original widgets already made), or None for the original look
    ("Starý vzhled", or R1 failed: then the original look is back)."""
    if not R.UseR1(WHAT):
        return None
    skin = Skin(window)
    try:
        skin.Build()
    except Exception:
        R.Fail(WHAT)
        skin.Undo()
        return None
    return Guard(skin)
