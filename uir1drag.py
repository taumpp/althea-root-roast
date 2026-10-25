# -*- coding: utf-8 -*-
"""Dragging a window by its R1 header.

The original windows were dragged by their title bar: ui.TitleBar has the 'attach' flag, and a mouse-down on an
'attach' window is handed to the ROOT window (CWindowManager::RunMouseLeftButtonDown -> GetRoot), which moves when
it is 'movable'. The R1 look hides that title bar and draws a not-pickable header, so a mouse-down on the header
reached the board under it (not movable) and the window stood still. DragStrip puts the title bar's job back: an
invisible pickable strip with 'attach' over the header row, leaving the X free on the right.
"""
import ui

import uir1tokens as T

X_RESERVE = T.X_HIT + 10        # the plain X and its margin stay clickable


class DragStrip(ui.Window):
    """Invisible 'attach' strip over the header row of an R1 window (x, y relative to ``parent``). Mouse-downs on
    it move the root window like the original title bar. 'float', so Raise() keeps it above content that a page
    switch raised over the header row."""

    def __init__(self, parent, w, h=T.HEAD_H, x=0, y=0, reserve=X_RESERVE):
        ui.Window.__init__(self)
        self.reserve = int(reserve)
        self.SetParent(parent)
        self.AddFlag('attach')
        self.AddFlag('float')
        self.SetPosition(int(x), int(y))
        self.h = int(h)
        self.Resize(w)
        self.Show()

    def Resize(self, w, h=None):
        if h is not None:
            self.h = int(h)
        self.SetSize(max(0, int(w) - self.reserve), self.h)

    def Raise(self):
        self.SetTop()
