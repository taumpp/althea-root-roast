# -*- coding: utf-8 -*-
"""R1 frame for the hover boards that are original ui.ThinBoard tooltips built in code.

uiToolTip.ToolTip (item / skill tooltips) swaps its thin board for the R1 'tooltip' frame (uir1.Frame: thin graphite
outline, the dark tooltip fill, a soft shadow) in its own constructor. The other hover boards - the active-effect
summary (uiaffectsummary) and the meteor tooltip (uimeteortooltip) - are ui.ThinBoard subclasses of their own and kept
the thin board, so next to an item tooltip they looked like another game. Dress(board) gives them the very same frame
the same way ToolTip does it (decision 2026-10-07: tooltips stay transparent and in the existing style, only the
content is corrected), so there is one tooltip look.

    self.r1Frame = uitooltipskin.Dress(self)         # in the constructor, before the board's own content is made
    def SetSize(self, width, height):                # a board that changes its size: the frame follows it
        ui.ThinBoard.SetSize(self, width, height)
        if self.r1Frame is not None:
            self.r1Frame.Resize(self.GetWidth(), self.GetHeight())

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the thin board; so does any failure (traced by
uir1.TraceFailure, the thin board pieces are shown again).

A board that lives for the whole session follows a later look switch (both ways) when it is shown again:

    self.r1Frame = uitooltipskin.Sync(self, (self.title, self.viewport))   # before Show(): the content it names is
                                                                          # raised above a frame made now
"""


def _Pieces(board):
    return list(board.Corners) + list(board.Lines) + [board.Base]


def Dress(board):
    """The R1 tooltip frame drawn instead of the thin board's own corners, lines and base, or None (original look,
    failure). Call it right after the ThinBoard constructor: the frame is made before the content and lies under it."""
    frame = None
    try:
        import uir1
        board.r1Generation = uir1.LookGeneration()
        if not uir1.UseR1():
            return None
        frame = uir1.Frame(board, 0, 0, 1, 1, "tooltip")
        for piece in _Pieces(board):
            piece.Hide()
        if board.GetWidth() > 0 and board.GetHeight() > 0:     # a board made at its final size (meteor tooltip)
            frame.Resize(board.GetWidth(), board.GetHeight())
    except Exception:
        try:
            import uir1
            uir1.TraceFailure("tooltip")
        except Exception:
            pass
        if frame is not None:
            try:
                frame.Hide()            # the fill is a child window: hidden with the frame
                frame.Destroy()
            except Exception:
                pass
        try:
            for piece in _Pieces(board):
                piece.Show()
        except Exception:
            pass
        return None
    return frame


def Sync(board, content=()):
    """The frame of the look in use now when Settings switched the look since ``board`` was dressed
    (uir1.LookGeneration); else the frame it has. A new R1 frame is made last, so ``content`` (the board's own
    children made after the first Dress) is raised above it again. Returns the frame (None: the original look)."""
    frame = getattr(board, 'r1Frame', None)
    try:
        import uir1
        generation = uir1.LookGeneration()
    except Exception:
        return frame
    if getattr(board, 'r1Generation', generation) == generation:
        return frame
    if frame is not None:
        try:
            frame.Hide()
            frame.Destroy()
        except Exception:
            pass
    board.r1Frame = None
    for piece in _Pieces(board):
        piece.Show()
    frame = Dress(board)
    board.r1Frame = frame
    if frame is not None:
        import uir1
        uir1.Restack(board, content)
    return frame
