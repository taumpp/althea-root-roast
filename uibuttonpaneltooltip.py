"""One floating name tooltip for the configurable button panels.

Button.SetToolTipText draws the text as a child of the button, 19 px above
it, so on the inventory rail it lands under the neighbouring button and is
cut in half (owner bug 2026-10-04); on ui.DragButton the native mouse-out
even shows it again. Panels therefore never use per-button tooltips: one
``uiToolTip.ToolTip`` (a TOP_MOST board like every other game tooltip) is
shown next to the hovered widget, outside the panel:

* ``'left'``: left of the widget, vertically centred (rail, preview strips);
* ``'above'``: centred above the widget (grids, small controls).

It is clamped to the screen and flips to the other side when needed.

In the R1 look the name shows in the one R1 hint (uir1.Hint): the same sides, the hint
watches the anchor like the tooltip did. "Starý vzhled" (or no R1 kit) keeps the tooltip board.
"""
GAP = 4
PADDING = 10


class PanelToolTip(object):
    def __init__(self):
        self.tip = None
        self.text = None
        self.anchor = None

    def _Tip(self):
        if self.tip is None:
            import uiToolTip
            tip = uiToolTip.ToolTip()
            tip.SetFollow(False)
            tip.Hide()
            # Hide as soon as the anchor is no longer hovered (e.g. its window closed).
            tip.OnUpdate = self._Watch
            self.tip = tip
        return self.tip

    def _SetText(self, text):
        tip = self._Tip()
        if text == self.text and not getattr(self, 'r1', False):
            return
        tip.ClearToolTip()
        line = tip.AutoAppendTextLine(text, tip.TITLE_COLOR, False)
        width = line.GetTextSize()[0] if hasattr(line, 'GetTextSize') else 0
        tip.toolTipWidth = width + 2 * PADDING
        line.SetPosition(PADDING, line.GetLocalPosition()[1])
        tip.ResizeToolTip()
        self.text = text

    def Show(self, widget, text, side='left', left_edge=None):
        """``left_edge``: global x of the panel's left edge for ``'left'`` (so a
        tooltip of an inner column never covers the outer column)."""
        body = None
        if isinstance(text, tuple):              # (name, status lines): the lines only in the R1 hint
            text, body = text
        if widget is None or not text:
            self.Hide()
            return
        self.body = body
        if self._R1Show(widget, text, side, left_edge):
            return
        self._SetText(text)
        self.r1 = False
        tip = self.tip
        width, height = tip.GetWidth(), tip.GetHeight()
        wx, wy = widget.GetGlobalPosition()
        ww, wh = widget.GetWidth(), widget.GetHeight()
        import wndMgr
        screen_w, screen_h = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        if side == 'above':
            x, y = wx + ww // 2 - width // 2, wy - height - GAP
            if y < 0:
                y = wy + wh + GAP
        else:
            edge = wx if left_edge is None else min(wx, int(left_edge))
            x, y = edge - width - GAP, wy + wh // 2 - height // 2
            if x < 0:
                x = wx + ww + GAP
        x = max(0, min(x, screen_w - width))
        y = max(0, min(y, screen_h - height))
        tip.SetPosition(x, y)
        self.anchor = widget
        tip.ShowToolTip()

    def _R1Show(self, widget, text, side, left_edge):
        """The R1 hint at the widget ('left' from the panel's left edge), or False (original look)."""
        try:
            import uir1
            if not uir1.UseR1():
                return False
            x, y = widget.GetGlobalPosition()
            uir1.ShowHintAt((x, y, widget.GetWidth(), widget.GetHeight()), text, getattr(self, 'body', None), side='left' if side != 'above'
                            else 'above', edge=left_edge if side != 'above' else None, owner=self, watch=widget)
        except Exception:
            return False
        if self.tip is not None:
            self.tip.HideToolTip()
        self.anchor = widget
        self.text = text
        self.r1 = True
        return True

    def _Watch(self):
        anchor = self.anchor
        try:
            hovered = anchor is not None and anchor.IsShow() and anchor.IsIn()
        except ReferenceError:
            hovered = False
        if not hovered:
            self.Hide()

    def Hide(self, widget=None):
        if widget is not None and widget is not self.anchor:
            return
        self.anchor = None
        if getattr(self, 'r1', False):
            self.r1 = False
            import uir1
            uir1.HideHint(self)
        if self.tip is not None:
            self.tip.HideToolTip()

    def IsShow(self):
        if getattr(self, 'r1', False):
            import uir1
            return uir1.HintShownFor(self)
        return self.tip is not None and self.tip.IsShow()

    def Destroy(self):
        self.Hide()
        if self.tip is not None:
            self.tip.Hide()
        self.tip = None


def Attach(button, tooltip, text_getter, side='left', edge_getter=None):
    """Show ``tooltip`` while the mouse is over a plain ui.Button (not a DragButton).

    Uses the button's native ShowToolTip/HideToolTip hooks; the button must not
    have a SetToolTipText child.
    """
    from _weakref import proxy
    target = proxy(button)
    button.SetShowToolTipEvent(lambda: tooltip.Show(target, text_getter(), side,
                                                    edge_getter() if edge_getter else None))
    button.SetHideToolTipEvent(lambda: tooltip.Hide(target))
