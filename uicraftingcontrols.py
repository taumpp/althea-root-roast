# -*- coding: utf-8 -*-
"""Measured, native components from the owner-approved compact crafting 03.

Only the manufacture action uses the shared Crimson artwork. The category
picker and quantity controls are the flat components drawn in the proposal.
All labels, states and hit areas remain live UI, without a flattened skin.
"""
import ui

INK = 0xffe4d9c9
MUTED = 0xffb3a691
GOLD = 0xffc8aa78
RULE = 0xff3c342a


def packed_color(argb):
    """Preserve ARGB bits at wndMgr's signed 32-bit color boundary."""
    bits = int(argb) & 0xffffffff
    return bits - 0x100000000 if bits & 0x80000000 else bits


def bar(parent, x, y, width, height, color):
    child = ui.Bar()
    child.SetParent(parent)
    child.SetPosition(x, y)
    child.SetSize(width, height)
    child.SetColor(packed_color(color))
    child.AddFlag('not_pick')
    child.Show()
    return child


def border(parent, width, height, color):
    return [bar(parent, x, y, w, h, color) for x, y, w, h in (
        (0, 0, width, 1), (0, height-1, width, 1),
        (0, 1, 1, height-2), (width-1, 1, 1, height-2))]


class Field(ui.Window):
    def __init__(self, width, height, color=RULE):
        ui.Window.__init__(self)
        self.SetSize(width, height)
        self.AddFlag('not_pick')
        self.parts = [bar(self, 0, 0, width, height, 0xff090909)]
        self.parts.extend(border(self, width, height, color))


class FlatButton(ui.Window):
    def __init__(self, width, height, text, callback, framed=True, left=False):
        ui.Window.__init__(self)
        self.SetSize(width, height)
        self.callback = callback
        self.enabled = True
        self.hovered = False
        self.pressed = False
        self.framed = framed
        self.selected = False
        self.expanded = False
        self.parts = []
        self.glyph = []
        self.background = bar(self, 0, 0, width, height, 0xff181513)
        self.parts.append(self.background)
        self.edges = border(self, width, height, RULE) if framed else []
        self.parts.extend(self.edges)
        self.highlight = bar(self, 1, 1, width-2, 1, 0xff776044) if framed else None
        if self.highlight:
            self.parts.append(self.highlight)
        self.label = ui.TextLine()
        self.label.SetParent(self)
        self.label.SetFontName('Tahoma:12')
        self.label.SetPosition(7 if left else width//2, height//2)
        if not left:
            self.label.SetHorizontalAlignCenter()
        self.label.SetVerticalAlignCenter()
        self.label.AddFlag('not_pick')
        self.label.Show()
        self.parts.append(self.label)
        self.SetText(text)

    def SetText(self, text):
        self.label.SetText(str(text))
        self._Paint()

    def GetText(self):
        return self.label.GetText()

    def SetSelected(self, selected):
        self.selected = selected
        self._Paint()

    def SetArrow(self, expanded):
        self.expanded = expanded
        for part in self.glyph:
            part.Hide()
        self.glyph = []
        # A 9x5 chevron, authored as native pixels, like the proposal.
        x, y = self.GetWidth()-18, (self.GetHeight()-5)//2
        color = GOLD if expanded else MUTED
        for i in range(5):
            yy = y+(4-i if expanded else i)
            self.glyph.append(bar(self, x+i, yy, 1, 1, color))
            if i != 4:
                self.glyph.append(bar(self, x+8-i, yy, 1, 1, color))

    def Enable(self):
        self.enabled = True
        self._Paint()

    def Disable(self):
        self.enabled = False
        self.pressed = False
        self._Paint()

    def _Paint(self):
        active = self.hovered or self.selected
        fill = (0xff10100e if not self.enabled else
                0xff39272a if self.pressed or self.selected else
                0xff24201a if self.hovered else
                0xff181513 if self.framed else 0x00000000)
        self.background.SetColor(packed_color(fill))
        edge = 0xff302b23 if not self.enabled else GOLD if active else 0xff594b38
        for part in self.edges:
            part.SetColor(packed_color(edge))
        if self.highlight:
            self.highlight.SetColor(packed_color(0xff776044 if self.enabled else 0xff28241e))
        self.label.SetPackedFontColor(packed_color(0xff776f62 if not self.enabled else
                                      GOLD if active or not self.framed else INK))

    def OnMouseOverIn(self):
        self.hovered = True
        self._Paint()

    def OnMouseOverOut(self):
        self.hovered = False
        self.pressed = False
        self._Paint()

    def OnMouseLeftButtonDown(self):
        if self.enabled:
            self.pressed = True
            self._Paint()
        return True

    def OnMouseLeftButtonUp(self):
        activate = self.enabled and self.pressed
        self.pressed = False
        self._Paint()
        if activate:
            self.callback()
        return True


def search_glyph(parent):
    # Fixed 12x12 magnifier from the reference; the edit starts after it.
    return [bar(parent, x, y, w, h, MUTED) for x, y, w, h in (
        (3, 0, 3, 1), (1, 1, 2, 1), (6, 1, 2, 1), (0, 2, 1, 4),
        (8, 2, 1, 4), (1, 6, 2, 1), (6, 6, 2, 1), (3, 7, 3, 1),
        (7, 7, 2, 2), (9, 9, 2, 2), (11, 11, 1, 1))]
