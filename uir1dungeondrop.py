# -*- coding: utf-8 -*-
"""Kořist - <dungeon> (uidungeondrop.DungeonDropWindow, the boss loot of a dungeon opened from Dungeony) in the R1
look "Krvavá žíla" (owner 8. 10. 2026, DEV 63: the window still had the old title bar and the bronze frame).

The window keeps its layout, its content and its behaviour (the live /dungeon_info drops reply, the item tooltips,
the chest preview, the mouse wheel and the scrolling, Esc and the X). The R1 look is drawn into it:

* the frame, the header (title in Cinzel, the red vein, the plain X) and the background: the shared R1 frame
  (uir1frame.REGISTRY, board=None: the window is the board, built in code);
* the 6 x 4 reward cells: the R1 item slot C (uir1.SLOT_CELL, 32 px like the original slot.png) under the icons;
* "Kořist z bosse", the item count and "nic" in the R1 font (Noto Sans) and the R1 text colours;
* the narrow R1 scroll bar (uir1.ScrollBar) at the place of the crimson track / thumb: it follows the window's own
  offset after every refresh and drives the same offset.

Settings -> "Starý vzhled" keeps the original window. A failure while dressing or while following a refresh is traced
(uir1.TraceFailure), the original look comes back (uir1frame FrameSkin.Fail) and the class is not dressed again in
this session.
"""
import weakref

import uir1
import uir1frame
import uir1tokens as T

import dungeondropmodel as model

ORIGINAL_CELL = "d:/ymir work/ui/slot.png"
TEXTS = (('heading', 'text_s', 'INK'), ('total', 'text_s', 'INK_DIM'), ('empty', 'text_s', 'MUTED'))
SCROLL_X, SCROLL_Y = 240, 57                     # the original thumb column (x 240, rows from y 57)


def _Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def Dress(window):
    """The R1 look on a built DungeonDropWindow; returns the DropSkin or None (Starý vzhled, a failure)."""
    frame = uir1frame.Dress(window)
    if frame is None:
        return None
    try:
        return DropSkin(window, frame)
    except Exception:
        frame.Fail()
        return None


class DropSkin(object):
    def __init__(self, window, frame):
        self.frame = frame
        self.window = frame.window                     # weak proxy (the window holds its frame)
        self.kit = uir1.Kit()
        self.scroll = None
        self.dragging = False
        for cell in window.cells:
            background = cell.background
            background.LoadImage(uir1.SLOT_CELL)
            frame.undo.append(lambda background=background: background.LoadImage(ORIGINAL_CELL))
        for name, role, color in TEXTS:
            line = getattr(window, name)
            uir1.SetFont(line, self.kit.font(role))
            line.SetPackedFontColor(_Signed(getattr(T, color)))
            frame.undo.append(lambda line=line: self._OriginalText(line))
        # weak references only: the bar holds its events and the window holds the _Refresh wrapper; a strong way
        # back would make a cycle of objects with __del__ (ui.Window), which Python 2 never frees
        me = weakref.ref(self)

        def scrolled():
            skin = me()
            if skin is not None:
                skin.OnScroll()

        def wheel(length):
            skin = me()
            return skin.window.OnMouseWheel(length) if skin is not None else False

        def refreshed():
            skin = me()
            if skin is not None:
                skin.Follow()
        bar = uir1.ScrollBar(self.kit)
        bar.SetParent(window)
        bar.SetPosition(SCROLL_X, SCROLL_Y)
        bar.SetScrollBarSize(window.TRACK_HEIGHT)
        bar.SetScrollEvent(scrolled)
        bar.OnMouseWheel = wheel
        bar.Hide()
        self.scroll = bar
        frame.undo.append(self._Undo)
        frame.wrapped.append(uir1frame._Wrap(window, '_Refresh', refreshed))
        self.Follow()

    @staticmethod
    def _OriginalText(line):
        text = line.GetText()
        line.SetText('')
        line.SetFontName('Tahoma:11')                  # the window's own font (DungeonDropWindow._Text)
        line.SetText(text)
        line.SetPackedFontColor(_Signed(0xFFFFFFFF))

    def _Undo(self):
        """Back to the crimson track / thumb (the window's _Refresh is unwrapped before this runs)."""
        bar, self.scroll = self.scroll, None
        if bar is not None:
            bar.Hide()
        self.window._Refresh()

    # the window's state -> the R1 scroll bar ----------------------------------------------------------------------
    def Follow(self):
        try:
            self._Follow()
        except Exception:
            self.frame.Fail()

    def _Follow(self):
        window, bar = self.window, self.scroll
        if bar is None:
            return
        window.track.Hide()
        window.thumb.Hide()
        count = len(window.entries)
        maximum = model.max_offset(count)
        if not maximum:
            bar.Hide()
            return
        rows = (count + model.COLUMNS - 1) // model.COLUMNS
        bar.SetMiddleBarSize(float(model.VISIBLE_ROWS) / rows)
        if not self.dragging:
            bar.SetPos(float(window.offset) / maximum, False)
        bar.Show()

    def OnScroll(self):
        window = self.window
        maximum = model.max_offset(len(window.entries))
        if not maximum or self.scroll is None:
            return
        offset = int(round(self.scroll.GetPos() * maximum))
        if offset != window.offset:
            window.offset = offset
            self.dragging = True
            try:
                window._Refresh()
            finally:
                self.dragging = False
