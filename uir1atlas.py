# -*- coding: utf-8 -*-
"""Velká mapa (uiminimap.AtlasWindow, key M) in the R1 look: only the frame and the tooltip change.

The window keeps every function: the atlas drawn by the game (map image, markers, the player arrow), fitting to the
screen, resizing by dragging the outer edge, the GM teleport click, the marker tooltip with the boss respawn time
and the guild mark, the close cross and Esc. The map is not recoloured or moved sideways. R1 draws:

* its own frame instead of the shared board: graphite frame, the title (Cinzel) with the vein under it and the plain
  X. The R1 header is 27 px high (+ 2 px gap), the original title bar 23 px, so the window is 6 px taller; the map
  keeps its size and scale (uiminimap passes the R1 title height to atlaslayout); the window is dragged by the
  header row like by the original title bar (uir1drag);
* the marker tooltip in an R1 tooltip frame: the name in the colour the game gives it, a short vein, the
  coordinates under it (and the respawn time of a boss).

Settings -> "Starý vzhled" (settingslook 'legacy') shows the original window; a failure while building R1 shows the
original window too (traced to syserr, uir1.TraceFailure).
"""
import ui

import uir1
import uir1drag

CURSOR_DX = 14         # tooltip right of / below the cursor
CURSOR_DY = 6
EDGE = 4               # tooltip stays this far inside the map board
DEFAULT_TITLE = u"Velká mapa"


def UseR1():
    return uir1.UseR1()


class MapTooltip(uir1.HintFace, ui.Window):
    """Marker tooltip: the one R1 hint face (uir1.HintFace) - the name (colour from the game)
    above the vein, the coordinates and an optional extra line (respawn time) under it. Not pickable; the owner places
    it with Place() (it follows the cursor inside the map)."""

    def __init__(self, kit):
        ui.Window.__init__(self)
        self.AddFlag('not_pick')
        self.kit = kit
        self._InitFace()
        self.SetContent(' ', [' ', ' '])            # the name, coordinates and extra lines exist from the start
        self.w = self.h = 0
        self.Hide()

    # the parts the atlas and its tests read
    name = property(lambda self: self.title)
    coords = property(lambda self: self.lines[0])
    extra = property(lambda self: self.lines[1])

    def SetEntry(self, name, x, y, color=None, extra=''):
        body = [u"%d, %d" % (int(x), int(y))] + ([extra] if extra else [])
        self.w, self.h = self.SetContent(name, body, color)

    def Place(self, mouse_x, mouse_y, board_w, board_h):
        """Right of and below the cursor; on the other side of it near the right / bottom edge of the map."""
        x, y = mouse_x + CURSOR_DX, mouse_y + CURSOR_DY
        if x + self.w > board_w - EDGE:
            x = mouse_x - CURSOR_DX - self.w
        if y + self.h > board_h - EDGE:
            y = board_h - EDGE - self.h
        self.SetPosition(max(EDGE, int(x)), max(EDGE, int(y)))

    def MarkPosition(self):
        """Where the guild mark (half size, 16 px) goes: left of the tooltip, level with the name."""
        x, y = self.GetLocalPosition()
        return x - 18, y + 4

    # The MapTextToolTip API, so code written for the original tooltip keeps working.
    def SetText(self, text):
        self.w, self.h = self.SetContent(text)

    def SetTextColor(self, color):
        self.title.SetPackedFontColor(color)

    def SetTooltipPosition(self, x, y):
        self.SetPosition(int(x), int(y))

    def GetTextSize(self):
        return self.w, self.h


class AtlasDress(object):
    """The R1 face of the atlas board: hides the board's own chrome (corners, edges, background, title bar with its
    close button) and draws the R1 frame and header INTO the board, before the atlas renderer is added, so the map
    and the tooltips draw above them."""

    def __init__(self, board):
        self.kit = uir1.Kit()
        self.board = board
        self.hidden = []
        self.frame = self.header = self.drag = None
        self.title = DEFAULT_TITLE

    def Build(self, window):
        board = self.board
        name = getattr(board, 'titleName', None)
        title = ''
        if name is not None:
            try:
                title = name.GetText()
            except Exception:
                title = ''
        self.title = title or DEFAULT_TITLE
        for widget in list(getattr(board, 'Corners', [])) + list(getattr(board, 'Lines', [])) + \
                [getattr(board, 'Base', None), getattr(board, 'titleBar', None)]:
            if widget is not None:
                widget.Hide()
                self.hidden.append(widget)
        w, h = board.GetWidth(), board.GetHeight()
        self.frame = uir1.Frame(board, 0, 0, w, h, 'window')
        self.header = uir1.Header(board, self.kit, w, self.title, on_close=ui.__mem_func__(window.Close))
        # The original title bar ('attach') dragged the movable atlas window: the strip over the header row does.
        self.drag = uir1drag.DragStrip(board, w)

    def TitleHeight(self):
        return self.header.ContentTop()

    def RequiredWidth(self):
        self.header.SetTitle(self.title)
        return uir1.TextWidth(self.header.title) + 80

    def Resize(self, w, h):
        self.frame.Resize(w, h)
        self.header.w = int(w)
        self.header.SetSize(int(w), self.header.GetHeight())
        shown = uir1.Fit(self.header.title, uir1.Upper(self.title), max(1, int(w) - 80))
        self.header.SetTitle(shown)
        self.drag.Resize(w)

    def SetTitle(self, title):
        self.title = title or DEFAULT_TITLE
        self.Resize(self.header.w, self.frame.GetHeight())

    def Tooltip(self):
        return MapTooltip(self.kit)

    def Undo(self):
        for widget in (self.frame, self.header, self.drag):
            if widget is not None:
                widget.Hide()
        for widget in self.hidden:
            widget.Show()
        self.hidden = []


def Dress(window):
    """AtlasDress of the window's board, or None (the original look) after a traced failure."""
    dress = AtlasDress(window.board)
    try:
        dress.Build(window)
        return dress
    except Exception:
        uir1.TraceFailure(u"Velká mapa")
        dress.Undo()
        return None
