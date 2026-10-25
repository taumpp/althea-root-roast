# -*- coding: utf-8 -*-
"""R1 skin of an existing window: every change of an original control is recorded, so a failed build can be undone.

The inventory (uiinventoryr1) and the character window (uicharacterr1) keep their original controls - slots, grids,
radio buttons, the edit line, the +/- buttons, every event and tooltip - and only re-skin them for the R1 look
(docs/ALTHEA_R1_KIT.md). A Recorder applies one change at a time and remembers how to put the original back; when
building the R1 look raises, Undo() restores the original look (newest change first) and the window stays usable.

The look is chosen when the window is built (the game builds these windows again after a teleport or a new login),
so Settings -> "Starý vzhled" applies to them from the next build.
"""
import uir1
import uir1tokens as T


class Recorder(object):
    """Applies changes to original controls and keeps the way back (Undo)."""

    def __init__(self):
        self.undo = []

    def _keep(self, fn):
        self.undo.append(fn)

    def Image(self, widget, path, original):
        """LoadImage (an ImageBox keeps its size = the image size; the R1 copies have the original sizes)."""
        widget.LoadImage(path)
        self._keep(lambda: widget.LoadImage(original))

    def Visuals(self, button, paths, originals):
        """Button visuals: up, over, down[, disabled] (None = leave that state alone)."""
        setters = ('SetUpVisual', 'SetOverVisual', 'SetDownVisual', 'SetDisableVisual')
        for setter, path in zip(setters, paths):
            if path is not None:
                getattr(button, setter)(path)

        def back():
            for setter, path in zip(setters, originals):
                if path is not None:
                    getattr(button, setter)(path)
        self._keep(back)

    def SlotBase(self, slot, path, original):
        slot.SetSlotBaseImage(path, 1.0, 1.0, 1.0, 1.0)
        self._keep(lambda: slot.SetSlotBaseImage(original, 1.0, 1.0, 1.0, 1.0))

    def Position(self, widget, x, y):
        ox, oy = widget.GetLocalPosition()
        widget.SetPosition(int(x), int(y))
        self._keep(lambda: widget.SetPosition(ox, oy))

    def Size(self, widget, w, h):
        ow, oh = widget.GetWidth(), widget.GetHeight()
        widget.SetSize(int(w), int(h))
        self._keep(lambda: widget.SetSize(ow, oh))

    def Hide(self, widget):
        shown = widget.IsShow()
        widget.Hide()
        self._keep(lambda: widget.Show() if shown else None)

    def Parent(self, widget, parent, x, y, original_parent):
        ox, oy = widget.GetLocalPosition()
        widget.SetParent(parent)
        widget.SetPosition(int(x), int(y))

        def back():
            widget.SetParent(original_parent)
            widget.SetPosition(ox, oy)
        self._keep(back)

    def Font(self, line, font, color, original_font=None, original_color=0xFFFFFFFF):
        """Font and colour of an original text line (uir1.SetFont lays the text out again). original_font None =
        the client's default font (a uiscript text without "fontname")."""
        uir1.SetFont(line, font)
        line.SetPackedFontColor(color)

        def back():
            text = line.GetText()
            line.SetText('')
            if original_font is None:
                line.SetDefaultFontName()
            else:
                line.SetFontName(original_font)
            line.SetText(text)
            line.SetPackedFontColor(original_color)
        self._keep(back)

    def Call(self, do, undo):
        """Any other change: do() now, undo() on Undo."""
        do()
        self._keep(undo)

    def Undo(self):
        for fn in reversed(self.undo):
            try:
                fn()
            except Exception:
                pass
        self.undo = []


def Destroy(widgets):
    """Hide and destroy R1 widgets of a failed build (a half-built R1 layer must not cover the original look)."""
    for widget in widgets:
        if widget is None:
            continue
        try:
            widget.Hide()
            if hasattr(widget, 'Destroy'):
                widget.Destroy()
        except Exception:
            pass


class Mirror(object):
    """An original text line shown as an R1 text: the original keeps receiving the values from the window (and stays
    hidden), the R1 line repeats it after every refresh (Sync), optionally reformatted. The R1 line lives in the
    parent given, so it is hidden with it."""

    def __init__(self, rec, line, parent, x, y, font, color, align='center', fmt=None):
        self.line, self.fmt = line, fmt
        self.text = uir1.Text(parent, '', x, y, font, color, align=align)
        rec.Hide(line)
        self.Sync()

    def Sync(self):
        value = self.line.GetText()
        value = self.fmt(value) if self.fmt else value
        if value != self.text.GetText():
            self.text.SetText(value)

    def Destroy(self):
        self.text.Hide()


class TooltipProxy(uir1.HitArea):
    """Invisible R1 hit area that shows the tooltip of an original (hidden) control: its OnMouseOverIn / Out."""

    def __init__(self, parent, x, y, w, h, original):
        uir1.HitArea.__init__(self, parent, x, y, w, h)
        self.original = original

    def OnMouseOverIn(self):
        uir1.HitArea.OnMouseOverIn(self)
        handler = getattr(self.original, 'OnMouseOverIn', None)
        if handler:
            handler()

    def OnMouseOverOut(self):
        uir1.HitArea.OnMouseOverOut(self)
        handler = getattr(self.original, 'OnMouseOverOut', None)
        if handler:
            handler()


def ProxySegment(parent, kit, x, y, items, widths, font=None):
    """R1 tabs in front of original (hidden) radio buttons: items = [(value, label, button)]. A click runs the
    original button's own event (CallEvent: its sound and handler), the hover shows its tooltip; the window's state
    is shown with SetValue(value)."""
    buttons = dict((value, button) for value, unused, button in items)

    def select(value):
        button = buttons.get(value)
        if button is not None:
            button.CallEvent()
    segment = uir1.Segment(parent, kit, [(value, label) for value, label, unused in items], event=select,
                           font=font or kit.font('text_s'))
    cx = 0
    for cell, w, (value, unused, button) in zip(segment.cells, widths, items):
        cell.Place(cx, w)
        cx += w
        _HoverTooltip(cell, button)
    segment.width = cx
    segment.SetSize(cx, T.SEG_H)
    segment.SetPosition(int(x), int(y))
    return segment


def _HoverTooltip(cell, button):
    """The hidden original button's tooltip text as the R1 hint above the R1 cell (its own tooltip window, if any,
    shows through its ShowToolTip as before)."""
    base_in, base_out = cell.OnMouseOverIn, cell.OnMouseOverOut

    def text():
        tip = getattr(button, 'ToolTipText', None)
        return tip.GetText() if isinstance(tip, uir1.TextTip) else ''

    def over_in():
        base_in()
        if text():
            uir1.ShowHint(None, cell, text())
        elif button is not None and hasattr(button, 'ShowToolTip'):
            button.ShowToolTip()

    def over_out():
        base_out()
        uir1.HideHint(cell)
        if button is not None and hasattr(button, 'HideToolTip'):
            button.HideToolTip()
    cell.OnMouseOverIn = over_in
    cell.OnMouseOverOut = over_out
