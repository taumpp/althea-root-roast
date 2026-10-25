# -*- coding: utf-8 -*-
"""Teleportace (uiteleport.TeleportAtlasWindow) in the R1 look: the frame, the tooltips and the list page change.

The window keeps its 860 x 513 size (scaled down on a narrow screen exactly as before) and every function: the painted
atlas with its regions, portals, name plates and hover / selection lifts, the "Mapy" / "Dungeony" side switches, the
"Zobrazit jako seznam" check box with its saved preference, the list page, the embedded dungeon page, the level hint
over a portal, the destination dialog of the main city, Esc and the close cross. R1 draws:

* the R1 window frame with the title "Teleportace" (Cinzel), the vein under it and the plain X instead of the board
  and its crimson title bar; the window is dragged by the header row like by the original title bar (uir1drag); the frame edges and the header lie above the map and the pages (the painted ocean fills
  the board up to its edges, so the frame is drawn over it); the old double frame over the map is not drawn;
* the side switches as dark R1 plates (the selected one with the vein under it) with the ORIGINAL map pin and dungeon
  gate icons (taken from the original switch art), an R1 tooltip with the switch name;
* the list check box "Zobrazit jako seznam" in the header row, left of the title, without a frame (the header is dark
  over the map and over the list);
* the level hint ("Přístup od úrovně" + the level in gold) in an R1 tooltip frame;
* the destination dialog: R1 dialog frame with the title, vein and X; the choices are R1 buttons (a locked one
  disabled);
* the list page ("Zobrazit jako seznam", uiteleportlist.TeleportListPage): the category buttons are R1 secondary
  buttons (the selected one is the brighter plate with the brightest label, never a red line) with the count of maps
  in the same row; the map rows are the original photographs straight in the window (no card frame, 7 per page, the
  selection is a brighter outline of the photograph) with R1 name / level plates, the name over the summary of the map
  ("1 boss · 3 metiny"); the detail panel is a graphite panel with the title, a strip of the original detail
  photograph, the Bossové and Metiny of the map in a scrolling list (R1 scroll bar only when they do not fit; the
  tooltip of a row shows level, kind and drop, a click opens the mob in the Wiki: teleportmapinfo) and the primary R1
  button "Teleportovat" fixed under it (BuildList).

The map itself (ocean, regions, portals, name plates) does not move and is not recoloured. Settings -> "Starý vzhled"
(settingslook 'legacy') shows the original window; a failure while building R1 shows the original window too (traced
to syserr, uir1.TraceFailure).
"""
import ui
import wndMgr

import teleportmapinfo
import uir1
import uir1drag
import uir1layout as L
import uir1tokens as T

SWITCH_ART = "d:/ymir work/ui/game/crimson_ember/teleport_atlas/switch_v10/btn_%s_normal.png"
SWITCH_SIZE = 36
# The icon square of the original switch art (36 x 36): the pin and the gate lie inside (8, 8) - (28, 28); the plate
# of the original art around it is not drawn.
SWITCH_ICON = (8, 8, 20, 20)
LEVEL_GOLD = 0xFFF7C81C           # the level value keeps today's gold
HINT_H = 28
HINT_PAD = 8
DIALOG_ROW_H = 22                 # R1 small button inside the 24 px row slot of the dialog


def UseR1():
    return uir1.UseR1()


def _Crop(widget, x, y, w, h, tw, th):
    """Shows only (x, y, w, h) of a tw x th texture (negative rendering rect = cut away), at the widget position."""
    widget.SetRenderingRect(-float(x) / tw, -float(y) / th, -float(tw - x - w) / tw, -float(th - y - h) / th)


# --------------------------------------------------------------------------- side switches
class SwitchPlate(uir1.Interactive):
    """R1 plate of the side switch (same 36 x 36 hit box, same SetSelected / OnClick as uiteleport.AtlasSwitchButton):
    a dark panel, the original icon, a lighter outline under the mouse, the vein under the selected plate. Its hover
    text ("Mapy", "Dungeony") is the one R1 hint (uir1.ShowHint) beside the plate, like every one-line hint."""

    def __init__(self, owner, kit, callback, tooltip, kind):
        uir1.Interactive.__init__(self)
        self.owner = owner
        self.kit = kit
        self.selected = False
        self.SetSize(SWITCH_SIZE, SWITCH_SIZE)
        self.frame = uir1.Frame(self, 0, 0, SWITCH_SIZE, SWITCH_SIZE, 'panel')
        self.outline = [uir1.Rect(self, x, y, w, h, T.HAIR) for x, y, w, h in (
            (0, 0, SWITCH_SIZE, 1), (0, SWITCH_SIZE - 1, SWITCH_SIZE, 1),
            (0, 0, 1, SWITCH_SIZE), (SWITCH_SIZE - 1, 0, 1, SWITCH_SIZE))]
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.LoadImage(SWITCH_ART % kind)
        self.icon.SetPosition(0, 0)
        ix, iy, iw, ih = SWITCH_ICON
        _Crop(self.icon, ix, iy, iw, ih, SWITCH_SIZE, SWITCH_SIZE)
        self.icon.Show()
        self.vein = uir1.Vein(self, 3, SWITCH_SIZE - 1, SWITCH_SIZE - 6)
        self.tooltipText = tooltip
        self.callback = callback
        self.paint()

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def OnClick(self):
        if self.callback:
            self.callback()

    def click(self):
        self.OnClick()

    def paint(self):
        state = self.state()
        for bar in self.outline:
            bar.Show() if state in ('hover', 'pressed') else bar.Hide()
        self.vein.Show() if self.selected else self.vein.Hide()
        self.icon.SetAlpha(1.0 if (self.selected or state != 'normal') else 0.82)

    def OnMouseOverIn(self):
        uir1.Interactive.OnMouseOverIn(self)
        if self.tooltipText:
            uir1.ShowHint(self.kit, self, self.tooltipText, side='right')

    def OnMouseOverOut(self):
        uir1.Interactive.OnMouseOverOut(self)
        uir1.HideHint(self)

    def Destroy(self):
        uir1.HideHint(self)
        self.callback = None
        self.owner = None


# --------------------------------------------------------------------------- "Zobrazit jako seznam"
TOGGLE_X = 14


class ListToggle(ui.Window):
    """The list check box in the header row of the window, left of the title: the R1 check box with the whole label and
    no frame of its own (the header is dark in both views); the API of ui.CheckBox_N that the window uses (SetChecked,
    IsChecked, SetEvent, SetText, SetTextColor, text). A click on the box or the label flips the box, then calls the
    event."""

    def __init__(self, parent, kit, text, checked):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('float')
        self.kit = kit
        self.eventFunc = None
        self.box = uir1.CheckBox(self, kit, 0, 0, text, bool(checked), event=self.__Click, font=kit.font('text_s'))
        self.text = self.box.label
        self.SetSize(self.box.Width(), self.box.h)
        # on the row of the title: the centre of the header text, HEAD_H // 2 + 1
        self.SetPosition(TOGGLE_X, T.HEAD_H // 2 + 1 - self.box.h // 2)

    def __Click(self):
        self.box.SetOn(not self.box.IsOn())
        if self.eventFunc:
            self.eventFunc()

    def SetEvent(self, event):
        self.eventFunc = event

    def SetChecked(self, checked):
        self.box.SetOn(checked)

    def IsChecked(self):
        return self.box.IsOn()

    def SetText(self, text):
        if self.text is not None:
            self.text.SetText(text)

    def SetTextColor(self, color):
        pass

    def Destroy(self):
        self.eventFunc = None
        self.box.callback = None


# --------------------------------------------------------------------------- level hint
class LevelHint(object):
    """Builds the R1 face of uiteleport.AtlasLevelHint inside it: tooltip frame, the original level icon, the label and
    the level in gold. The hint grows to its text (hint.WIDTH is set per hint; the window centres it with it)."""

    def __init__(self, hint, kit, icon_path, label):
        self.hint = hint
        self.kit = kit
        self.frame = uir1.TooltipFrame(hint)
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(hint)
        self.icon.AddFlag('not_pick')
        self.icon.LoadImage(icon_path)
        self.icon.SetPosition(HINT_PAD - 1, (HINT_H - 20) // 2)
        self.icon.Show()
        self.label = uir1.RowText(hint, label, HINT_PAD + 24, HINT_H, kit.font('text_s'), T.INK)
        self.value = uir1.RowText(hint, '', 0, HINT_H, kit.font('text_sb'), LEVEL_GOLD)
        self.SetLevel(0)

    def SetLevel(self, level):
        self.value.SetText(u"%d" % int(level))
        x = HINT_PAD + 24 + uir1.TextWidth(self.label) + 6
        self.value.SetPosition(x, uir1.CellTop(HINT_H, self.kit.font('text_sb')))
        w = x + uir1.TextWidth(self.value) + HINT_PAD + 2
        self.hint.WIDTH = w
        self.hint.SetSize(w, HINT_H)
        self.frame.Apply(w, HINT_H)


# --------------------------------------------------------------------------- destination dialog
class DialogBoard(ui.Window):
    """R1 replacement of the dialog's BoardWithTitleBar: dialog frame, header with the title, vein and X. The API the
    dialog uses: SetSize, SetTitleName, SetCloseEvent."""

    def __init__(self, kit, w, h):
        ui.Window.__init__(self)
        self.kit = kit
        self.closeEvent = None
        self.w, self.h = int(w), int(h)
        self.frame = uir1.Frame(self, 0, 0, self.w, self.h, 'dialog')
        self.header = uir1.Header(self, kit, self.w, '', on_close=self.__Close)
        # The original dialog's title bar ('attach') dragged the teleport window: the strip does the same.
        self.drag = uir1drag.DragStrip(self, self.w)
        self.title = ''
        ui.Window.SetSize(self, self.w, self.h)

    def __Close(self):
        if self.closeEvent:
            self.closeEvent()

    def SetSize(self, w, h):
        self.w, self.h = int(w), int(h)
        ui.Window.SetSize(self, self.w, self.h)
        self.frame.Resize(self.w, self.h)
        self.drag.Resize(self.w)

    def SetTitleName(self, title):
        self.title = title
        self.header.SetTitle(title)

    def SetCloseEvent(self, event):
        self.closeEvent = event


class LocationRow(uir1.Button):
    """R1 choice row of the destination dialog (the API of uiteleport.CrimsonLocationRow)."""

    def __init__(self, parent, kit, callback, width):
        uir1.Button.__init__(self, parent, kit, 0, 0, width, '', small=True, event=self.OnClick)
        self.rowCallback = callback
        self.destinationId = None
        self.available = True

    def SetPosition(self, x, y):
        # The row slot is 24 px high, the R1 row button 22 px: centred in the slot.
        uir1.Button.SetPosition(self, x, y + 1)

    def SetLocation(self, label, destination_id):
        self.destinationId = destination_id
        self.available = destination_id is not None
        self.SetText(label)
        if self.available:
            self.Enable()
        else:
            self.Disable()

    def OnClick(self):
        if self.available and self.rowCallback:
            self.rowCallback(self.destinationId)

    def Destroy(self):
        self.rowCallback = None
        self.callback = None


# --------------------------------------------------------------------------- the window frame
class AtlasFrame(object):
    """R1 frame of the whole atlas board. Begin() (right after the board is made, before the map): hides the board's
    own chrome and lays the R1 background; Finish() (after the map and the pages): the frame edges and the header
    over everything, float, so Raise() keeps them on top after a page switch."""

    def __init__(self, board, kit, w, h, title, on_close):
        self.board = board
        self.kit = kit
        self.hidden = []
        for widget in list(getattr(board, 'Corners', [])) + list(getattr(board, 'Lines', [])) + \
                [getattr(board, 'Base', None), getattr(board, 'titleBar', None)]:
            if widget is not None:
                widget.Hide()
                self.hidden.append(widget)
        self.back = uir1.Frame(board, 0, 0, w, h, 'window')
        self.size = (int(w), int(h))
        self.title = title
        self.on_close = on_close
        self.edges = None
        self.header = None
        self.drag = None

    def Finish(self):
        w, h = self.size
        self.edges = uir1.Frame(self.board, 0, 0, w, h, 'window', bg=None)
        self.edges.AddFlag('float')
        self.header = uir1.Header(self.board, self.kit, w, self.title, on_close=self.on_close)
        self.header.AddFlag('float')
        # Drags the teleport window by the header row like the original title bar ('attach' -> the root).
        self.drag = uir1drag.DragStrip(self.board, w)
        self.Raise()

    def Raise(self):
        """Frame edges, header and the drag strip above whatever a page switch raised (the pages start at y = 22,
        inside the header row)."""
        for widget in (self.edges, self.header, self.drag):
            if widget is not None:
                widget.Show()
                widget.SetTop()

    def Widgets(self):
        return [w for w in (self.back, self.edges, self.header, self.drag) if w is not None]

    def Undo(self):
        for widget in self.Widgets():
            widget.Hide()
        for widget in self.hidden:
            widget.Show()
        self.hidden = []


# --------------------------------------------------------------------------- the list page (uiteleportlist)
LIST_SKIN = "d:/ymir work/ui/game/crimson_ember/teleport_atlas/list_c11/"     # the photographs and the one-colour glyphs
ROW_EDGE_HOVER = 0xFF4E4846           # the row outline under the mouse: between the R1 panel hairline (3E3937) ...
ROW_EDGE_SELECTED = 0xFF605856        # ... and the outline of a hovered R1 button (the selected row)
PHOTO_LOCKED_ALPHA = 218.0 / 255.0    # a map above the player's level: its photograph stays a little dimmer
NAME_PLATE_ALPHA = 0.86
LEVEL_PLATE_ALPHA = 0.94
LIST_GAP = 6                          # glyph - label gap of a category button


def Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color & 0x80000000 else color


def _Scaled(value, scale):
    return int(round(value * scale))


def _Line(parent, text, x, top, height, font, color, align='left'):
    """Text of the list: top-aligned at ``top`` + CellTop(height) (the whole font cell inside its row), the colour signed."""
    return uir1.Text(parent, text, x, top + uir1.CellTop(height, font), font, Signed(color), align=align, valign='top')


class Edge(object):
    """1 px outline of a w x h rectangle: four bars over the whole edge (not pickable). The brighter graphite outline of
    the selected / hovered row over the hairline of its card."""

    def __init__(self, parent, w, h, color):
        w, h = max(2, int(w)), max(2, int(h))
        self.bars = [uir1.Rect(parent, x, y, bw, bh, color) for x, y, bw, bh in (
            (0, 0, w, 1), (0, h - 1, w, 1), (0, 0, 1, h), (w - 1, 0, 1, h))]
        self.color = color

    def SetColor(self, color):
        if color != self.color:
            self.color = color
            for bar in self.bars:
                bar.SetColor(uir1.GenerateColor(color))

    def Show(self):
        for bar in self.bars:
            bar.Show()

    def Hide(self):
        for bar in self.bars:
            bar.Hide()


class RowPlate(object):
    """Name / level plate of a row: the R1 small button plate (22 px, lightly rounded, native caps and tiles) over the photograph,
    a little see-through like the original plates; SetState normal / hover / disabled."""
    H = T.BTN_H_S

    def __init__(self, parent, x, y, w, alpha):
        self.w = int(w)
        self.state = None
        self.ops = uir1.Ops(parent, None, int(x), int(y))
        self.ops.SetAlpha(alpha)
        self.SetState('normal')

    def SetState(self, state):
        if state != self.state:
            self.state = state
            self.ops.Apply(L.button(False, True, state, self.w))


class ListTab(uir1.Interactive):
    """Category button of the list (the API of uiteleportlist.CategoryButton): an R1 secondary button with the original
    one-colour glyph. The selection is brightness: the selected button is the lighter plate with the brightest label
    and glyph, the others the dark plate with the dimmer label (no red line, no red frame)."""

    def __init__(self, page, kit, scale, category, text, glyph, ink):
        uir1.Interactive.__init__(self)
        self.page = page
        self.category = category
        self.glyph = glyph
        self.selected = False
        self.w, self.h = _Scaled(132, scale), L.button_height(False)
        self.SetParent(page)
        self.SetSize(self.w, self.h)
        self.plate = uir1.Ops(self, L.button(False, False, 'normal', self.w))       # plate before the glyph and the label
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.LoadImage(LIST_SKIN + 'icon_%s_normal.png' % glyph)
        self.icon.Show()
        self.iconState = 'normal'
        self.font = kit.font('button_s')
        self.label = uir1.Text(self, text, 0, 0, self.font, Signed(T.INK_DIM), valign='top')
        # The glyph ink + the gap + the label are centred together (the plate is the same for every width).
        left, top, right, bottom = ink
        start = (self.w - (right - left) - LIST_GAP - uir1.TextWidth(self.label)) // 2
        self.icon.SetPosition(start - left, (self.h - (top + bottom)) // 2)
        self.label.SetPosition(start + (right - left) + LIST_GAP, uir1.CellTop(self.h, self.font))
        self.SetEvent(self._Select)
        self.Show()
        self.paint()

    def _Select(self):
        if self.page:
            self.page.SetCategory(self.category)

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def paint(self):
        state = self.state()
        bright = self.selected or state in ('hover', 'pressed')
        self.plate.Apply(L.button(False, False, 'pressed' if state == 'pressed' else
                                  ('hover' if self.selected else 'normal'), self.w))
        self.label.SetPackedFontColor(Signed(T.PRIMARY_TEXT if self.selected else (T.INK if bright else T.INK_DIM)))
        glyph_state = 'selected' if bright else 'normal'
        if glyph_state != self.iconState:
            self.iconState = glyph_state
            self.icon.LoadImage(LIST_SKIN + 'icon_%s_%s.png' % (self.glyph, glyph_state))

    def OnRunMouseWheel(self, length):
        return self.page.OnRunMouseWheel(length) if self.page else False

    def Destroy(self):
        self.Hide()
        self.callback = None
        self.page = None


# list geometry at scale 1 (page coordinates; the page lies 22 px under the top of the window, under the header row)
LIST_ROWS = 7                         # map rows per page (the original list shows 5)
ROW_W, ROW_H, ROW_STEP = 456, 56, 60  # the photograph is the row: 456 x 56, nothing around it
LIST_TOP = 54
TAB_TOP = 18
PANEL_X, PANEL_Y, PANEL_W, PANEL_BOTTOM = 504, 54, 299, 470      # the bottom lies 21 px over the window edge
PANEL_PAD = 10                        # the side space of the panel, also under the action button
DETAIL_SIZE = (273, 185)              # the detail photograph; the panel shows PHOTO_H px of its height
PHOTO_H = 56
PHOTO_FOCUS = 0.55                    # where the strip lies in the photograph (0 = top, 1 = bottom)
INFO_ROW_H = 20
INFO_GAP = 4                          # under a section
BAR_SPACE = 14                        # scroll bar (8 px) + the space before it
TIP_PAD = 10
TIP_MAX = (320, 330)


def ButtonTop(scale):
    """y of the action button: its bottom lies PANEL_PAD (10 px, as the space at the sides) over the panel bottom."""
    return _Scaled(PANEL_BOTTOM, scale) - PANEL_PAD - T.BTN_H


class ListRow(uir1.Interactive):
    """One map row of the list (the API of uiteleportlist.DestinationRow): the original map photograph straight in the
    window (456 x 56, no card frame, no outline of its own), a dark plate over its left part with the name and under it
    the summary of the map ("1 boss · 3 metiny", teleportmapinfo), the R1 level plate ("Od N") on the right, a lock
    for a map above the player's level. The selected row has the brighter outline of the photograph, the arrow and the
    brightest text; a locked row a dimmer photograph and text; the mouse brightens the outline and the text."""

    def __init__(self, page, kit, scale):
        uir1.Interactive.__init__(self)
        self.page = page
        self.scale = scale
        self.destinationId = None
        self.selected = False
        self.locked = False
        w, h = _Scaled(ROW_W, scale), _Scaled(ROW_H, scale)
        self.SetParent(page)
        self.SetSize(w, h)
        self.photo = ui.ExpandedImageBox()
        self.photo.SetParent(self)
        self.photo.AddFlag('not_pick')
        self.photo.SetPosition(0, 0)
        self.photo.Show()
        self.edge = Edge(self, w, h, ROW_EDGE_SELECTED)
        self.font = kit.font('text_s')
        small = kit.font('text_xs')
        self.lineH, self.statsH = uir1.FontCell(self.font), uir1.FontCell(small)
        self.plateH = min(h - 4, max(_Scaled(40, scale), self.lineH + self.statsH + 10))
        self.plateY = (h - self.plateH) // 2
        plateX, plateW = _Scaled(9, scale), _Scaled(238, scale)
        self.plate = uir1.Ops(self, None, plateX, self.plateY)
        self.plate.Apply(L.frame('panel', plateW, self.plateH, 'panel_dark'))
        self.plate.SetAlpha(NAME_PLATE_ALPHA)
        levelX, levelW = _Scaled(362, scale), _Scaled(86, scale)
        levelY = (h - RowPlate.H) // 2
        self.levelPlate = RowPlate(self, levelX, levelY, levelW, LEVEL_PLATE_ALPHA)
        self.arrowX = _Scaled(17, scale)
        self.arrow = uir1.Image(self, uir1.ChevronPath('right', 'hover'), self.arrowX, 0)
        self.lock = ui.ExpandedImageBox()
        self.lock.SetParent(self)
        self.lock.AddFlag('not_pick')
        self.lock.LoadImage(LIST_SKIN + 'icon_lock_normal.png')
        self.lock.SetPosition(_Scaled(340, scale), h // 2 - 6)
        self.lock.Show()
        self.nameX = _Scaled(32, scale)
        self.nameWidth = plateX + plateW - self.nameX - 8
        self.name = _Line(self, '', self.nameX, 0, self.lineH, self.font, T.INK)
        self.stats = _Line(self, '', self.nameX, 0, self.statsH, small, T.INK_DIM)
        self.minimum = _Line(self, '', levelX + levelW // 2, levelY, RowPlate.H, self.font, T.INK, 'center')
        self.SetEvent(self._Select)
        self._Place(True)
        self.paint()

    def _Select(self):
        if self.page and self.destinationId:
            self.page.Select(self.destinationId)

    def _Place(self, two_lines):
        """The name alone is centred in the plate, with the summary the two lines are."""
        block = self.lineH + 2 + self.statsH if two_lines else self.lineH
        top = self.plateY + (self.plateH - block) // 2
        self.name.SetPosition(self.nameX, top)
        self.stats.SetPosition(self.nameX, top + self.lineH + 2)
        self.arrow.SetPosition(self.arrowX, top + self.lineH // 2 - T.CHEVRON // 2)

    def SetDestination(self, destination, selected, level):
        if self.destinationId != destination['id']:
            self.destinationId = destination['id']
            self.photo.LoadImage(LIST_SKIN + 'scenes/' + self.destinationId + '_row.png')
            self.photo.SetScale(self.scale, self.scale)
        self.selected = bool(selected)
        self.locked = level < destination['level']
        self.photo.SetAlpha(PHOTO_LOCKED_ALPHA if self.locked else 1.0)
        uir1.Fit(self.name, destination['name'], self.nameWidth)
        summary = teleportmapinfo.Summary(teleportmapinfo.ForMap(destination.get('map_index')))
        uir1.Fit(self.stats, summary, self.nameWidth)
        self._Place(bool(summary))
        self.minimum.SetText(u'Od %d' % destination['level'])
        self.paint()
        self.Show()

    def paint(self):
        state = self.state()
        hover = state in ('hover', 'pressed')
        if self.selected or state == 'pressed':
            self.edge.SetColor(ROW_EDGE_SELECTED)
            self.edge.Show()
        elif hover:
            self.edge.SetColor(ROW_EDGE_HOVER)
            self.edge.Show()
        else:
            self.edge.Hide()
        self.levelPlate.SetState('hover' if self.selected else ('disabled' if self.locked else 'normal'))
        bright = self.selected or hover
        if self.locked:
            color = T.INK_DIM if bright else T.MUTED
            dim = T.MUTED if bright else T.DISABLED
        else:
            color = T.IVORY if bright else T.INK
            dim = T.INK_DIM
        self.name.SetPackedFontColor(Signed(color))
        self.stats.SetPackedFontColor(Signed(dim))
        self.minimum.SetPackedFontColor(Signed(color))
        self.arrow.Show() if self.selected else self.arrow.Hide()
        self.lock.Show() if self.locked else self.lock.Hide()

    def OnRunMouseWheel(self, length):
        return self.page.OnRunMouseWheel(length) if self.page else False

    def Destroy(self):
        self.Hide()
        self.callback = None
        self.page = None


# --------------------------------------------------------------------------- the map information (right panel)
def _WikiInterface():
    """The interface that opens the wiki page of a mob (MakeHyperlinkTooltip), None when the client has no wiki."""
    try:
        import app
        import osfInfo
        if not getattr(app, 'ENABLE_WIKI', False):
            return None
        interface = osfInfo.GetInterfaceInstance()
        return interface if interface is not None and hasattr(interface, 'MakeHyperlinkTooltip') else None
    except Exception:
        return None


def _UseWikiCatalog():
    """The drop of a tooltip is read from the wiki catalogue: tell the wiki that its data are in use, so that a
    catalogue the server has marked as changed is refetched (lazily, by the wiki itself)."""
    interface = _WikiInterface()
    use = getattr(interface, 'UseWikiCatalog', None)
    if use is not None:
        try:
            use()
        except Exception:
            _TraceClick('wiki catalogue')


def _TraceClick(what):
    try:
        import dbg
        import traceback
        dbg.TraceError('Teleportace: %s failed.' % what)
        for line in traceback.format_exc().splitlines():
            dbg.TraceError(line)
    except Exception:
        pass


class InfoTip(ui.Window):
    """R1 tooltip of a boss / metin / world boss row (the transparent R1 tooltip frame): the name with the vein, the
    facts the data hold (level and kind, respawn, world boss channels), a row of the first drops as R1 item slots
    ("+ N dalších ve Wiki" for the rest) and the hint that a click opens the Wiki. Floats over the page, never takes
    the mouse."""

    def __init__(self, parent, kit, row, wiki, map_index=None):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.AddFlag('float')
        self.refs = []                                  # a window without a reference in Python is gone in the engine
        self.frame = uir1.TooltipFrame(self)
        self.frame.Apply(*TIP_MAX)                      # every frame image first: they lie under the text
        big, font, small = kit.font('text_b'), kit.font('text_s'), kit.font('text_xs')
        pad = TIP_PAD
        widths = []
        y = pad
        title = self._Keep(_Line(self, row.name, pad, y, 22, big, T.IVORY))
        widths.append(uir1.TextWidth(title))
        y += 24
        veinY = y
        y += 6
        for index, text in enumerate(teleportmapinfo.Facts(row)):
            line = self._Keep(_Line(self, text, pad, y, 17, font, T.INK if index else T.INK_DIM))
            widths.append(uir1.TextWidth(line))
            y += 17
        drops = self._Drops(row.vnum, map_index)
        if drops:
            y += 6
            self._Keep(_Line(self, u'Drop', pad, y, 16, small, T.INK_DIM))
            y += 17
            shown = drops[:teleportmapinfo.DROP_SHOWN]
            x, tall = pad, T.SLOT
            for item_vnum, count, icon, height in shown:
                self._Keep(uir1.SlotCell(self, x, y, height))
                image = ui.ExpandedImageBox()
                image.SetParent(self)
                image.AddFlag('not_pick')
                image.LoadImage(icon)
                image.SetPosition(x, y)
                image.Show()
                self._Keep(image)
                if count > 1:
                    self._Keep(_Line(self, u'%d' % count, x + T.SLOT - 3, y + height - 15, 14, small, T.IVORY, 'right'))
                x += T.SLOT + 2
                tall = max(tall, height)
            widths.append(x - 2 - pad)
            y += tall
            if len(drops) > len(shown):
                y += 1
                self._Keep(_Line(self, u'+ %d dalších ve Wiki' % (len(drops) - len(shown)), pad, y, 16, small,
                                 T.INK_DIM))
                y += 16
        if wiki:
            y += 6
            hint = self._Keep(_Line(self, u'Klik: otevřít ve Wiki', pad, y, 16, small, T.MUTED))
            widths.append(uir1.TextWidth(hint))
            y += 16
        w, h = max(widths) + 2 * pad, y + pad
        self.SetSize(w, h)
        self.frame.Apply(w, h)
        self.frame.Vein(pad, veinY, min(w - 2 * pad, 150))
        self.Hide()

    def _Keep(self, widget):
        self.refs.append(widget)
        return widget

    def _Drops(self, vnum, map_index=None):
        """[(item vnum, count, icon path, slot height)] of the drops whose item the client knows."""
        result = []
        try:
            import item
            for item_vnum, count in teleportmapinfo.Drops(vnum, map_index):
                item.SelectItem(item_vnum)
                icon = item.GetIconImageFileName()
                if not icon:
                    continue
                height = T.SLOT * max(1, min(3, int(item.GetItemSize()[1])))
                result.append((item_vnum, count, icon, height))
        except Exception:
            return []
        return result


class InfoRow(uir1.Interactive):
    """A boss / metin row of the right panel: level, name (shortened with "..."), a chevron when the Wiki can open its
    page. The mouse lights the row and shows its tooltip, a click opens the mob in the Wiki."""

    def __init__(self, panel, kit, parent, y, width, row):
        uir1.Interactive.__init__(self)
        self.panel = panel
        self.row = row
        self.wiki = panel.wiki
        self.SetParent(parent)
        self.SetPosition(0, y)
        self.SetSize(width, INFO_ROW_H)
        self.fill = uir1.Rect(self, 0, 0, width, INFO_ROW_H, T.BAND_HOVER, 0.0)
        font = kit.font('text_s')
        self.level = _Line(self, u'%d' % row.level, 24, 0, INFO_ROW_H, font, T.INK_DIM, 'right')
        self.name = _Line(self, '', 34, 0, INFO_ROW_H, font, T.INK)
        uir1.Fit(self.name, row.name, width - 34 - (22 if self.wiki else 8))
        self.chevron = None
        if self.wiki:
            self.chevron = uir1.Image(self, uir1.ChevronPath('right', 'normal'), width - 12,
                                      INFO_ROW_H // 2 - T.CHEVRON // 2)
        self.shownState = None
        self.SetEvent(self._Open)
        self.paint()
        self.Show()

    def _Open(self):
        if not self.wiki:
            return
        interface = _WikiInterface()
        if interface is None:
            return
        try:
            interface.MakeHyperlinkTooltip(teleportmapinfo.WikiLink(self.row.vnum))
        except Exception:
            _TraceClick('wiki %d' % self.row.vnum)

    def paint(self):
        hover = self.state() in ('hover', 'pressed')
        self.fill.SetColor(uir1.GenerateColor(T.BAND_HOVER, 0.55 if hover else 0.0))
        self.name.SetPackedFontColor(Signed(T.IVORY if hover else T.INK))
        self.level.SetPackedFontColor(Signed(T.INK if hover else T.INK_DIM))
        if self.chevron is not None and hover != self.shownState:
            self.chevron.LoadImage(T.ROOT + uir1.ChevronPath('right', 'hover' if hover else 'normal'))
        self.shownState = hover

    def OnMouseOverIn(self):
        uir1.Interactive.OnMouseOverIn(self)
        if self.panel:
            self.panel.ShowTip(self)

    def OnMouseOverOut(self):
        uir1.Interactive.OnMouseOverOut(self)
        if self.panel:
            self.panel.HideTip()

    def Destroy(self):
        self.Hide()
        self.callback = None
        self.__dict__.pop('OnMouseWheel', None)
        self.panel = None


class InfoPanel(object):
    """The right panel of the R1 list under the title, the minimal level and the photograph strip: the Bossové and Metiny
    of the selected map (teleportmapinfo), a scrolling list inside a window that renders inside its own rectangle
    (SetInsideRender) with the R1 scroll bar, which shows only when the rows do not fit. The action button lies
    fixed under it."""

    def __init__(self, page, kit, scale):
        self.page, self.kit, self.scale = page, kit, scale
        self.wiki = _WikiInterface() is not None
        self.rows = []
        self.widgets = []
        self.layout = []
        self.tips = {}
        self.tipStamp = 0
        self.mapIndex = None
        self.tip = None
        self.tipRow = None
        self.destinationId = None
        self.info = None
        self.contentH = 0
        self.offset = 0
        x, y = _Scaled(PANEL_X + PANEL_PAD, scale), _Scaled(PANEL_Y + 142, scale)
        self.viewW = _Scaled(PANEL_W - 2 * PANEL_PAD, scale)
        self.viewH = ButtonTop(scale) - 8 - y
        self.view = ui.Window()
        self.view.SetParent(page)
        self.view.SetPosition(x, y)
        self.view.SetSize(self.viewW, self.viewH)
        self.view.SetInsideRender(True)
        self.view.OnMouseWheel = self.Wheel
        self.view.Show()
        self.bar = uir1.ScrollBar(kit)
        self.bar.SetParent(page)
        self.bar.SetPosition(_Scaled(PANEL_X + PANEL_W - PANEL_PAD, scale) - T.SCROLL_W, y)
        self.bar.SetScrollBarSize(self.viewH)
        self.bar.SetScrollEvent(self.OnScroll)
        self.bar.OnMouseWheel = self.Wheel
        self.bar.Hide()

    # -- the photograph strip and the footer
    def CropPhoto(self):
        """The strip of the card (273 x 56 at scale 1) of the 273 x 185 detail photograph: a rendering rect, no new
        texture. The engine leaves a cropped image where it lies uncropped (the cut part is just not drawn), so the
        window moves up / left by the cut. A rendering rect is in texture pixels, so a scaled photograph would be
        drawn distorted: the strip is the native-size middle of the photograph at every window scale (the card is
        smaller on a narrow screen, the photograph is never scaled)."""
        tw, th = DETAIL_SIZE
        w, h = min(tw, _Scaled(tw, self.scale)), min(th, _Scaled(PHOTO_H, self.scale))
        x, y = (tw - w) // 2, int(round((th - h) * PHOTO_FOCUS))
        photo = self.page.detailPhoto
        photo.SetScale(1.0, 1.0)
        _Crop(photo, x, y, w, h, tw, th)
        photo.SetPosition(_Scaled(PANEL_X + 13, self.scale) - x, _Scaled(PANEL_Y + 74, self.scale) - y)

    def PlaceFooter(self):
        """"11 map v kategorii" ends 20 px before "Tvoje úroveň: N", whatever the width of that text; on a narrow
        screen (the window is scaled down, the buttons are not) the gap shrinks to 8 px and, when the count would
        still touch the category buttons, it is left out (the count is only a hint)."""
        page, footer = self.page, self.page.footer
        if not footer.GetText():                 # no category count line any more
            footer.Hide()
            return
        tabs_right = max([tab.GetLocalPosition()[0] + tab.GetWidth() for tab in page.tabs] or [0])
        right = page.playerLevel.GetLocalPosition()[0] - uir1.TextWidth(page.playerLevel)
        width = uir1.TextWidth(footer)
        for gap in (20, 14, 8):
            if right - gap - width >= tabs_right + 6:
                footer.SetPosition(right - gap, footer.GetLocalPosition()[1])
                footer.Show()
                return
        footer.Hide()

    # -- the rows
    def _Clear(self):
        self.HideTip()
        for row in self.rows:
            row.Destroy()
        for widget in self.widgets:
            widget.Hide()
        self.rows, self.widgets, self.layout, self.tips = [], [], [], {}

    def Update(self, destination, photo_changed):
        if photo_changed:
            self.CropPhoto()
        self.PlaceFooter()
        info = teleportmapinfo.ForMap(destination.get('map_index'))
        if destination['id'] == self.destinationId and info is self.info:
            return
        self.destinationId, self.info = destination['id'], info
        self.mapIndex = destination.get('map_index')
        self.wiki = _WikiInterface() is not None
        self._Clear()
        sections = []
        if info.bosses:
            sections.append((u'Bossové', info.bosses))
        if info.metins:
            sections.append((u'Meteory', info.metins))
        head = self.kit.cell('text_sb') + 6
        self.contentH = sum(head + INFO_ROW_H * len(rows) + INFO_GAP for _title, rows in sections)
        overflow = self.contentH > self.viewH
        width = self.viewW - (BAR_SPACE if overflow else 0)
        y = 0
        for title, rows in sections:
            section = uir1.Section(self.view, self.kit, 0, y, width, title, Signed(T.INK_DIM))
            self.widgets.append(section)
            self.layout.append((section, y))
            y += head
            for row in rows:
                item = InfoRow(self, self.kit, self.view, y, width, row)
                item.SetWheelEvent(self.Wheel)
                self.rows.append(item)
                self.layout.append((item, y))
                y += INFO_ROW_H
            y += INFO_GAP
        if overflow:
            self.bar.SetMiddleBarSize(float(self.viewH) / self.contentH)
            self.bar.SetScrollStep(float(INFO_ROW_H) / (self.contentH - self.viewH))
            self.bar.SetPos(0.0, False)
            self.bar.Show()
        else:
            self.bar.Hide()
        self.offset = 0
        self._Move()

    # -- scrolling
    def _Move(self):
        for widget, y in self.layout:
            widget.SetPosition(0, y - self.offset)

    def OnScroll(self):
        span = max(0, self.contentH - self.viewH)
        self.offset = int(round(max(0.0, min(1.0, self.bar.GetPos())) * span))
        self.HideTip()
        self._Move()

    def Wheel(self, length):
        span = self.contentH - self.viewH
        if span <= 0:
            return False
        self.bar.SetPos(self.bar.GetPos() + (float(INFO_ROW_H) / span) * (1 if length < 0 else -1))
        return True

    # -- the tooltip
    def ShowTip(self, row):
        self.HideTip()
        _UseWikiCatalog()
        # A tooltip is kept per row; a new wiki catalogue (a live change on the server) rebuilds them all.
        stamp = teleportmapinfo.DropsStamp()
        if stamp != self.tipStamp:
            self.tips, self.tipStamp = {}, stamp
        key = row.row.vnum
        tip = self.tips.get(key)
        if tip is None:
            tip = self.tips[key] = InfoTip(self.page, self.kit, row.row, self.wiki, self.mapIndex)
        gx, gy = row.GetGlobalPosition()
        px, py = self.page.GetGlobalPosition()
        x = max(2, gx - px - tip.GetWidth() - 6)
        y = max(2, min(gy - py - 8, self.page.GetHeight() - tip.GetHeight() - 2))
        tip.SetPosition(x, y)
        tip.Show()
        tip.SetTop()
        self.tip = tip
        self.tipRow = row

    def UpdateTip(self):
        # Constant-time revision check; rebuild only the currently hovered row
        # when an atomic catalogue installation changes its data.
        if self.tip is not None and self.tipRow is not None and teleportmapinfo.DropsStamp() != self.tipStamp:
            self.ShowTip(self.tipRow)

    def HideTip(self):
        self.tipRow = None
        if self.tip is not None:
            self.tip.Hide()
            self.tip = None

    def Destroy(self):
        self.HideTip()
        for row in self.rows:
            row.Destroy()
        self.rows = []
        self.bar.eventScroll = None
        self.bar.__dict__.pop('OnMouseWheel', None)          # the handlers this panel put on the engine's windows
        self.view.__dict__.pop('OnMouseWheel', None)
        self.tips = {}
        self.page = None


def BuildList(page, kit, scale, categories, glyph_ink):
    """The R1 face of uiteleportlist.TeleportListPage (821 x 491 at scale 1): fills the attributes the page logic uses
    (tabs, rows, scrollBar, playerLevel, footer, detailTitle, detailMinimum, detailPhoto, teleportButton, infoPanel)
    and keeps every other widget in page.widgets. The page background is the R1 window background of the atlas frame
    (no interior picture). The list has no title line of its own (the switch "Zobrazit jako seznam" is in the header of
    the window) and no frames: the category buttons and the count of maps share the first row, the map photographs
    follow in 7 rows of 60 px, the panel lies on the right down to the same space under it as at its sides."""
    def S(value):
        return _Scaled(value, scale)

    def keep(widget):
        page.widgets.append(widget)
        return widget

    page.model.PAGE_SIZE = LIST_ROWS
    font_s, font_b = kit.font('text_s'), kit.font('text_b')
    tab_top = S(TAB_TOP)
    page.playerLevel = keep(_Line(page, '', S(800), tab_top, S(28), font_s, T.INK_DIM, 'right'))
    for index, (key, text, glyph) in enumerate(categories):
        tab = ListTab(page, kit, scale, key, text, glyph, glyph_ink[glyph])
        tab.SetPosition(S(20 + 138 * index), tab_top + (S(28) - tab.h) // 2)
        page.tabs.append(tab)
    for index in range(LIST_ROWS):
        row = ListRow(page, kit, scale)
        row.SetPosition(S(20), S(LIST_TOP + ROW_STEP * index))
        page.rows.append(row)
    page.scrollBar = uir1.ScrollBar(kit)
    page.scrollBar.SetParent(page)
    page.scrollBar.SetPosition(S(490), S(LIST_TOP))
    page.scrollBar.SetScrollBarSize(S(LIST_ROWS * ROW_STEP - 4))
    page.scrollBar.SetScrollEvent(page._OnScroll)
    page.scrollBar.OnRunMouseWheel = page.OnRunMouseWheel
    page.footer = keep(_Line(page, '', S(686), tab_top, S(28), kit.font('text_xs'), T.INK_DIM, 'right'))
    # the right panel: title, minimum level, the photograph strip in its card, then the information and the action
    px, py = PANEL_X, PANEL_Y
    keep(uir1.Frame(page, S(px), S(py), S(PANEL_W), S(PANEL_BOTTOM) - S(py), 'panel'))
    page.detailTitle = keep(_Line(page, '', S(px + PANEL_W // 2), S(py + 6), 30, font_b, T.IVORY, 'center'))
    keep(uir1.Divider(page, S(px + PANEL_PAD), S(py + 38), S(PANEL_W - 2 * PANEL_PAD)))
    level_icon = ui.ExpandedImageBox()
    level_icon.SetParent(page)
    level_icon.AddFlag('not_pick')
    level_icon.LoadImage(LIST_SKIN + 'icon_level_normal.png')
    level_icon.SetPosition(S(px + 15), S(py + 47))
    level_icon.Show()
    keep(level_icon)
    keep(_Line(page, u'Minimální úroveň', S(px + 34), S(py + 44), 18, font_s, T.INK_DIM))
    page.detailMinimum = keep(_Line(page, '', S(px + PANEL_W - 14), S(py + 44), 18, font_b, T.IVORY, 'right'))
    keep(uir1.Frame(page, S(px + 9), S(py + 70), S(DETAIL_SIZE[0] + 8), S(PHOTO_H + 8), 'panel'))   # under the strip
    page.detailPhoto = ui.ExpandedImageBox()
    page.detailPhoto.SetParent(page)
    page.detailPhoto.AddFlag('not_pick')
    page.detailPhoto.SetPosition(S(px + 13), S(py + 74))
    page.detailPhoto.Show()
    page.infoPanel = InfoPanel(page, kit, scale)
    button = uir1.Button(page, kit, S(px + 60), ButtonTop(scale), S(180), u'Teleportovat', primary=True,
                         event=page.Teleport)
    page.teleportButton = button
    return page


class Skin(object):
    """Everything the window needs to build its R1 face; one per window."""

    def __init__(self):
        self.kit = uir1.Kit()
        self.frame = None

    def Switch(self, owner, callback, tooltip, kind):
        return SwitchPlate(owner, self.kit, callback, tooltip, kind)

    def BeginFrame(self, board, w, h, title, on_close):
        self.frame = AtlasFrame(board, self.kit, w, h, title, on_close)
        return self.frame

    def ListToggle(self, parent, text, checked):
        return ListToggle(parent, self.kit, text, checked)

    def Raise(self):
        if self.frame is not None:
            self.frame.Raise()


def Trace(what):
    uir1.TraceFailure(what)
