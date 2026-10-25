# -*- coding: utf-8 -*-
"""R1 character selection and creation, with a single-actor fallback for the hall.

One column on the left (title, rows, detail, actions), the emblem and the character as the scene on the right. The
Living Sigil windows (root/new_introselect.py, root/new_introcreate.py) keep their data, network, character render
and key handling; this module only draws the column and calls their methods:

* select: rows of the account's characters (portrait, name, level on the right, guild and play time), empty rows
  "Vytvořit postavu", the selected character (name and level, family name / guild / played, four stats), HRÁT with
  the hint "Enter · dvojklik na postavu", Vytvořit / Smazat / Ukončit; the delete confirmation is a modal dialog
  with the character card, the code field, the dark blood Smazat on the left and Zrušit on the right;
* create: the form top-down (job rows, gender and look, the name with its rules and the error under the field,
  Vytvořit disabled until the name is valid, Zpět), the job name and the starting stats under the character.

Profiles like the proposal: >= 1080 px high 1.0, >= 900 px 5/6, else 0.8 with a 13 px floor for every font.
Native R1 pieces only (9-slice frames, the vein, filled rectangles, the R1 field); nothing is stretched.
Settings -> "Starý vzhled" (uir1.UseR1() false) keeps Living Sigil; any exception while building or refreshing puts
the Living Sigil column back (uir1.TraceFailure) and the screen keeps working.
"""
import ui
import wndMgr

import uir1
import uir1tokens as T

WHAT = 'pregame'

ROW_OCCUPIED, ROW_EMPTY, ROW_GAP = 68, 40, 6
COLUMN_W = 440
PORTRAIT = 43

# the Living Sigil widgets that stay as the scene; everything else of the column is hidden while R1 is on
SCENE = ('BackGround', 'giant_brand_mark', 'character_render_area', 'brand_logo')


def Signed(color):
    """A packed colour as the signed int the x64 engine binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color >= 0x80000000 else color


def Text(parent, text, x, y, font, color, align='left', valign='top'):
    """A text line; valign='center' centres the font CELL on y by position (top-aligned line, like uir1.CellTop) -
    never the engine's vertical centre, which clips and shifts (docs of uir1.RowText)."""
    line = ui.TextLine()
    line.SetParent(parent)
    line.AddFlag('not_pick')
    line.SetFontName(font)                  # before the first text: SetFontName on a line with text garbles it
    line.SetPackedFontColor(Signed(color))
    if align == 'center':
        line.SetHorizontalAlignCenter()
    elif align == 'right':
        line.SetHorizontalAlignRight()
    line.r1_center = valign == 'center'
    line.r1_font = font
    Move(line, x, y)
    line.SetText(text)
    line.Show()
    return line


def Move(line, x, y):
    """Positions a line made by Text(); a centred one gets its cell centred on y."""
    if getattr(line, 'r1_center', False):
        y = int(y) - uir1.FontCell(line.r1_font) // 2
    line.SetPosition(int(x), int(y))


def Font(line, font, text=None):
    """Font change of a line that may show text: emptied first (uir1.SetFont), otherwise the engine draws the old
    glyph run from the new font's atlas - the garbage "ÍPĎHO+Č$IOOX.HT" of the empty rows (in-game 8. 10.)."""
    uir1.SetFont(line, font, text)
    line.r1_font = font


def SetColor(line, color):
    line.SetPackedFontColor(Signed(color))


def Width(line):
    try:
        return int(line.GetTextSize()[0])
    except Exception:
        return 0


class Geo(object):
    """Scale of the column. The proposal's sizes x 1.25 (owner 9. 10.: "celé o 20-30 % větší") on >= 1080 px,
    5/6 of that on >= 900 px, 1.0 below; Attach* shrink it further when the column would not fit the height.
    Text in Tahoma (PRAVIDLA-UI "Písmo textu" 9. 10.: classic Metin2 Tahoma, sharp, never under 12 px); the
    screen title like the window title POSTAVA (Cinzel 16, the red line), not scaled."""

    def __init__(self, width, height, scale=None):
        self.W, self.H = int(width), int(height)
        if scale is not None:
            self.s = float(scale)
        elif self.H >= 1080:
            self.s = 1.25
        elif self.H >= 900:
            self.s = 1.25 * 5.0 / 6.0
        else:
            self.s = 1.0
        self.tight = self.H < 900
        self.margin = max(24, int(self.W * 0.05))
        self.cw = self.P(COLUMN_W)
        self.stage = (self.margin + self.cw + self.P(24) + self.W - self.margin) // 2

    def P(self, value):
        return int(round(value * self.s))

    def noto(self, size, bold=False):
        """Text of the proposal's Noto ``size`` in Tahoma (Tahoma is ~0.8 of Noto's cell), never under 12 px."""
        return 'Tahoma:%d%s' % (max(12, int(round(size * 0.8 * self.s))), 'b' if bold else '')

    def caps(self, size):
        """Button labels and the job name: bold Tahoma (the text rule covers the buttons too)."""
        return self.noto(size, bold=True)

    def title(self):
        return T.FONTS['B']['title']        # the window title of R1 (POSTAVA): Cinzel 16


def LogoHeight(g):
    return int(round(96 * g.s))      # living_sigil/logo_horizontal_280x96.png at the column's scale


# --------------------------------------------------------------------------- pieces
class Plate(ui.Window):
    """A row / button plate: the R1 panel frame (9-slice) with a shade over it for the state (selected = brighter,
    hover = a little brighter, empty = darker). No red for the selection (R1 rule 3)."""

    SHADE = {'normal': (0x000000, 0.0), 'hover': (0xFFFFFF, 0.05), 'selected': (0xFFFFFF, 0.10),
             'pressed': (0x000000, 0.25), 'empty': (0x000000, 0.35), 'disabled': (0x000000, 0.45)}

    def __init__(self, parent, x, y, w, h, kind='panel'):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.frame = uir1.Frame(self, 0, 0, w, h, kind)
        self.shade = uir1.Rect(self, 1, 1, max(1, w - 2), max(1, h - 2), 0x000000, 0.0)
        self.shade.AddFlag('not_pick')
        self.edge = uir1.Rect(self, 3, 1, max(1, w - 6), 1, 0x605A58, 0.0)    # the bright top edge of the selection
        self.Show()

    def SetState(self, state):
        color, alpha = self.SHADE.get(state, self.SHADE['normal'])
        self.shade.SetColor(uir1.GenerateColor(color, alpha))
        self.edge.SetColor(uir1.GenerateColor(0x605A58, 1.0 if state == 'selected' else 0.0))

    def Resize(self, w, h):
        self.SetSize(int(w), int(h))
        self.frame.Resize(w, h)
        self.shade.SetSize(max(1, w - 2), max(1, h - 2))
        self.edge.SetSize(max(1, w - 6), 1)


class PlateButton(uir1.Interactive):
    """A button of any size from R1 pieces: the panel plate, a Cinzel label; primary = the red vein along the bottom
    (the main action), danger = the dark blood fill of an irreversible action (Smazat), choice = a toggle that is on
    shows brightness (Muž / Žena, Typ 1 / 2)."""

    def __init__(self, parent, x, y, w, h, text, font, event=None, primary=False, danger=False):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.w, self.h = int(w), int(h)
        self.primary, self.danger, self.on = bool(primary), bool(danger), False
        self.plate = Plate(self, 0, 0, w, h, 'window' if primary else 'panel')
        self.fill = uir1.Rect(self, 2, 2, max(1, w - 4), max(1, h - 4), 0x46080A, 0.9 if danger else 0.0)
        self.fill.AddFlag('not_pick')
        self.vein = uir1.Vein(self, 3, h - 2, w - 6) if (primary or danger) else None
        self.font = font
        self.label = Text(self, text, w // 2, h // 2, font, T.BUTTON_TEXT, align='center', valign='center')
        self.callback = event
        self.paint()
        self.Show()

    def SetOn(self, on):
        self.on = bool(on)
        self.paint()

    def SetText(self, text):
        self.label.SetText(text)

    def paint(self):
        state = self.state()
        if self.on and state == 'normal':
            state = 'selected'
        self.plate.SetState(state)
        if not self.enabled:
            color = T.DISABLED
        elif self.primary or self.danger or self.on:
            color = T.IVORY
        else:
            color = T.BUTTON_TEXT if state != 'hover' else T.IVORY
        SetColor(self.label, color)
        if self.vein is not None:
            if self.enabled:
                self.vein.Show()
            else:
                self.vein.Hide()
        Move(self.label, self.w // 2, self.h // 2 + (1 if state == 'pressed' else 0))


class StatBar(ui.Window):
    """A thicker stat bar: the dark track with a graphite hairline, the dark blood fill."""

    def __init__(self, parent, x, y, w, h):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.w, self.h = int(w), int(h)
        self.edge = uir1.Rect(self, 0, 0, w, h, 0x3C3634, 1.0)
        self.track = uir1.Rect(self, 1, 1, max(1, w - 2), max(1, h - 2), 0x080707, 0.92)
        self.fill = uir1.Rect(self, 1, 1, 1, max(1, h - 2), 0x6E0A0C, 1.0)
        self.top = uir1.Rect(self, 1, 1, 1, 1, 0xB01414, 1.0)
        self.Show()

    def SetRatio(self, ratio):
        width = int(round((self.w - 2) * max(0.0, min(1.0, float(ratio)))))
        for bar in (self.fill, self.top):
            if width > 0:
                bar.SetSize(width, bar.GetHeight())
                bar.Show()
            else:
                bar.Hide()


class Portrait(ui.ExpandedImageBox):
    """The race face of a row (the Living Sigil .sub portraits), scaled to the row's size."""

    def __init__(self, parent, x, y, size):
        ui.ExpandedImageBox.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.size = int(size)
        self.Show()

    def Load(self, path):
        try:
            self.LoadImage(path)
            w = max(1, self.GetWidth())
            scale = float(self.size) / float(w)
            self.SetScale(scale, scale)
        except Exception:
            pass


class Row(uir1.Interactive):
    """One character row (or an empty one): click selects, double click plays (or creates)."""

    def __init__(self, column, index):
        uir1.Interactive.__init__(self)
        self.column, self.index = column, index
        self.SetParent(column.root)
        self.plate = Plate(self, 0, 0, 10, 10)
        self.face = Portrait(self, 0, 0, PORTRAIT)
        self.plus = None
        self.name = Text(self, '', 0, 0, column.f_name, T.INK_DIM)
        self.meta = Text(self, '', 0, 0, column.f_small, T.MUTED)
        self.level = Text(self, '', 0, 0, column.f_level, T.INK_DIM, align='right', valign='center')
        self.lv = Text(self, 'Lv.', 0, 0, column.f_small, T.MUTED, align='right', valign='center')
        self.data = None
        self.selected = False
        self.Show()

    def Place(self, x, y, w, h):
        g = self.column.g
        self.SetPosition(x, y)
        self.SetSize(w, h)
        self.w, self.h = w, h
        self.plate.Resize(w, h)
        size = PORTRAIT if g.s >= 0.95 else 36
        self.face.size = size
        self.face.SetPosition(g.P(12), (h - size) // 2)
        tx = g.P(12) + size + g.P(16)
        self.name.SetPosition(tx, h // 2 - g.P(21))
        self.meta.SetPosition(tx, h // 2 + g.P(3))
        Move(self.level, w - g.P(16), h // 2)
        self.empty_x = g.P(16)

    def SetData(self, data, face_path, selected):
        """data = (name, level, guild, played) or None for an empty row."""
        self.data, self.selected = data, bool(selected)
        g = self.column.g
        if data is None:
            self.face.Hide()
            self.level.Hide()
            self.lv.Hide()
            self.meta.Hide()
            Font(self.name, self.column.f_text, self.column.texts['empty'])
            box = g.P(22) if g.s >= 0.95 else g.P(20)
            if self.plus is None:
                self.plus = Plate(self, 0, 0, box, box)
                self.plus_label = Text(self.plus, '+', box // 2, box // 2, self.column.f_text, T.INK, align='center',
                                       valign='center')
            self.plus.SetPosition(self.empty_x, (self.h - box) // 2)
            self.plus.Show()
            self.name.SetPosition(self.empty_x + box + g.P(12), (self.h - uir1.FontCell(self.column.f_text)) // 2)
            SetColor(self.name, T.MUTED)
        else:
            name, level, guild, played = data
            if self.plus is not None:
                self.plus.Hide()
            self.face.Load(face_path)
            self.face.Show()
            Font(self.name, self.column.f_name, name)
            # no guild: only the play time, no empty separator
            self.meta.SetText('   ·   '.join(part for part in (guild, played) if part))
            self.meta.Show()
            self.level.SetText(str(level))
            self.level.Show()
            Move(self.lv, self.w - g.P(16) - Width(self.level) - g.P(6), self.h // 2 + g.P(3))
            self.lv.Show()
            tx = g.P(12) + self.face.size + g.P(16)
            self.name.SetPosition(tx, self.h // 2 - g.P(21))
            SetColor(self.name, T.IVORY if selected else T.INK_DIM)
            SetColor(self.meta, T.INK_DIM if selected else T.MUTED)
            SetColor(self.level, T.IVORY if selected else T.INK_DIM)
        self.paint()

    def paint(self):
        if self.data is None:
            self.plate.SetState('hover' if self.hovered else 'empty')
        else:
            self.plate.SetState('selected' if self.selected else ('hover' if self.hovered else 'normal'))

    def click(self):
        self.column.OnRow(self.index)

    def OnMouseLeftButtonDoubleClick(self):
        self.column.OnRowDouble(self.index)
        return True


class Stats(object):
    """VIT / INT / SÍL / POH in two columns: label, bar, value."""

    LABELS = ('VIT', 'INT', 'SÍL', 'POH')

    def __init__(self, parent, g, font):
        self.g, self.font = g, font
        self.labels = [Text(parent, label, 0, 0, font, T.INK_DIM, valign='center') for label in self.LABELS]
        self.bars = [StatBar(parent, 0, 0, g.P(136), max(6, g.P(8))) for unused in self.LABELS]
        self.values = [Text(parent, '0', 0, 0, font, T.INK, valign='center') for unused in self.LABELS]

    def Place(self, x, y, colw, rowh=None, label_w=None):
        g = self.g
        rowh = g.P(30) if rowh is None else rowh
        label_w = g.P(44) if label_w is None else label_w
        bar_h = max(6, g.P(8))
        for i in range(4):
            cx = x + (i % 2) * colw
            cy = y + (i // 2) * rowh
            Move(self.labels[i], cx, cy + bar_h // 2)
            self.bars[i].SetPosition(cx + label_w, cy)
            Move(self.values[i], cx + label_w + g.P(136) + g.P(10), cy + bar_h // 2)

    def Set(self, values, ratio):
        for i, value in enumerate(list(values)[:4]):
            self.values[i].SetText(str(value))
            self.bars[i].SetRatio(ratio(value))

    def Show(self, show=True):
        for widget in self.labels + self.bars + self.values:
            widget.Show() if show else widget.Hide()


def _hide_column(window, keep=()):
    """Hides the Living Sigil column (every widget of dlgBoard except the scene and ``keep`` - the widgets the R1
    column adopted, e.g. the name EditLine: a hidden edit line takes no keys); returns them for Undo."""
    hidden = []
    board = getattr(window, 'dlgBoard', None)
    children = getattr(board, 'ElementDictionary', {}) or {}
    for name, widget in list(children.items()):
        if name in SCENE or widget is board or any(widget is kept for kept in keep):
            continue
        try:
            if widget.IsShow():
                widget.Hide()
                hidden.append(widget)
        except Exception:
            pass
    return hidden


def _root(window, g):
    root = ui.Window()
    root.SetParent(window.dlgBoard)
    root.SetPosition(0, 0)
    root.SetSize(g.W, g.H)
    root.AddFlag('not_pick')
    root.Show()
    return root


def _place_scene(window, g, logo_y):
    """The logo above the column, the emblem and the character centred on the stage right of the column."""
    board = window.dlgBoard
    try:
        logo = (getattr(board, 'ElementDictionary', None) or {}).get('brand_logo') or board.GetChild('brand_logo')
        logo.SetPosition(g.margin, logo_y)      # first: a failing SetScale must not leave the logo under the title
    except Exception:
        logo = None
    try:
        logo.SetScale(g.s, g.s)
    except Exception:
        pass
    try:
        area = window.renderArea
        area.SetPosition(g.stage - area.GetWidth() // 2, area.GetLocalPosition()[1])
    except Exception:
        pass
    try:
        mark = window.brandMark
        mark.SetPosition(g.stage - mark.GetWidth() // 2, mark.GetLocalPosition()[1])
    except Exception:
        pass


# =========================================================================== character select
def CancelOwnedDelete(column):
    dialog = getattr(column, 'dialog', None)
    window = column.window
    if dialog is not None and getattr(window, 'privateInputBoard', None) is dialog:
        window.CancelInputPrivateCode()


class SelectColumn(object):
    """The select column on window.dlgBoard; window = new_introselect.SelectCharacterWindow."""

    texts = {'title': 'Výběr postavy', 'empty': 'Vytvořit postavu', 'play': 'Hrát', 'hint': 'Enter  ·  dvojklik na postavu',
             'create': 'Vytvořit', 'delete': 'Smazat', 'exit': 'Ukončit', 'family': 'Rodové jméno', 'guild': 'Cech',
             'played': 'Odehráno'}

    def __init__(self, window, rows=5, scale=None):
        self.window = window
        self.root, self.hidden, self.dialog = None, [], None
        self.keep = ()
        self.g = g = Geo(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight(), scale)
        self.f_title, self.f_name, self.f_small = g.title(), g.noto(19, True), g.noto(15)
        self.f_text, self.f_level, self.f_big = g.noto(17), g.noto(24, True), g.noto(30, True)
        self.hidden = _hide_column(window)
        self.root = _root(window, g)
        self.title = Text(self.root, self.texts['title'].upper(), 0, 0, self.f_title, T.IVORY)
        self.titleVein = uir1.Vein(self.root, 0, 0, g.P(200))
        self.rows = [Row(self, index) for index in range(rows)]
        self.nameText = Text(self.root, '', 0, 0, self.f_big, T.IVORY)
        self.levelText = Text(self.root, '', 0, 0, self.f_big, T.IVORY, align='right')
        self.lvText = Text(self.root, 'Lv.', 0, 0, self.f_text, T.MUTED, align='right')
        self.divider = uir1.Divider(self.root, 0, 0, g.cw)
        self.infoLabels = [Text(self.root, self.texts[key].upper(), 0, 0, g.noto(15), T.INK_DIM)
                           for key in ('family', 'guild', 'played')]
        self.infoValues = [Text(self.root, '', 0, 0, g.noto(20, True), T.IVORY) for unused in range(3)]
        self.stats = Stats(self.root, g, self.f_text)
        self.play = PlateButton(self.root, 0, 0, g.cw, g.P(56), self.texts['play'].upper(), g.caps(24),
                                event=self.OnPlay, primary=True)
        self.hint = Text(self.root, self.texts['hint'], 0, 0, g.noto(14), T.MUTED, align='center')
        bw = (g.cw - g.P(16)) // 3
        self.actions = [PlateButton(self.root, 0, 0, bw, g.P(34), self.texts[key].upper(), g.caps(15), event=event)
                        for key, event in (('create', self.OnCreate), ('delete', self.OnDelete), ('exit', self.OnExit))]
        self.dialog = None
        self.Layout()
        self.Refresh()

    # ------------------------------------------------------------------ layout
    def ContentHeight(self, count):
        """Height from the title to the bottom of Vytvořit / Smazat / Ukončit with ``count`` characters (the same
        steps as Layout)."""
        g = self.g
        rows = sum((g.P(ROW_OCCUPIED) if index < count else g.P(ROW_EMPTY)) + g.P(ROW_GAP)
                   for index in range(len(self.rows)))
        return (g.P(54) + rows + g.P(26) - g.P(ROW_GAP) + g.P(44) + g.P(12) + g.P(62) + g.P(74) + g.P(56) + g.P(22)
                + g.P(14) + g.P(34))

    def Top(self, count):
        """(logo y, gap under the logo): the column moves up so BOTTOM_GAP stays free under it (owner 9. 10.,
        5 characters: the buttons sat on the screen edge) - first the gap under the logo shrinks (down to 12 px
        x scale), then the logo goes up (down to 12 px from the top). Sizes never change here."""
        g = self.g
        logo_y = g.P(40) if g.tight else g.P(58)
        gap = g.P(24) if g.tight else g.P(40)
        over = logo_y + LogoHeight(g) + gap + self.ContentHeight(count) - (g.H - BOTTOM_GAP)
        if over > 0:
            cut = min(over, max(0, gap - g.P(12)))
            gap, over = gap - cut, over - cut
        if over > 0:
            cut = min(over, max(0, logo_y - 12))
            logo_y, over = logo_y - cut, over - cut
        return logo_y, gap

    def WorstBottom(self):
        """The bottom with every row occupied, the column moved up as far as Top allows (for _Fit)."""
        logo_y, gap = self.Top(len(self.rows))
        return logo_y + LogoHeight(self.g) + gap + self.ContentHeight(len(self.rows))

    def Layout(self):
        g = self.g
        x0 = g.margin
        count = self.Count()
        logo_y, gap = self.Top(count)
        _place_scene(self.window, g, logo_y)
        y = logo_y + LogoHeight(g) + gap
        self.title.SetPosition(x0, y)
        # the title keeps the window-title size (Cinzel 16): its red line follows the font cell, not the scale
        self.titleVein.SetPosition(x0 - 4, y + uir1.FontCell(g.title()) + 6 - T.VEIN_ROW)
        y += g.P(54)
        for index, row in enumerate(self.rows):
            h = g.P(ROW_OCCUPIED) if index < count else g.P(ROW_EMPTY)
            row.Place(x0, y, g.cw, h)
            y += h + g.P(ROW_GAP)
        y += g.P(26) - g.P(ROW_GAP)
        self.nameText.SetPosition(x0, y - g.P(4))
        self.levelText.SetPosition(x0 + g.cw, y - g.P(4))
        self.lvY = y + g.P(10)
        y += g.P(44)
        self.divider.SetPosition(x0, y)
        y += g.P(12)
        cx = x0
        for label, value, step in zip(self.infoLabels, self.infoValues, (150, 130, 0)):
            label.SetPosition(cx, y)
            value.SetPosition(cx, y + g.P(21))
            cx += g.P(step)
        y += g.P(62)
        self.stats.Place(x0, y, g.P(228))
        y += g.P(74)
        self.play.SetPosition(x0, y)
        self.hint.SetPosition(x0 + g.cw // 2, y + g.P(56) + g.P(6))
        y += g.P(56) + g.P(22) + g.P(14)
        bw = (g.cw - g.P(16)) // 3
        for index, button in enumerate(self.actions):
            button.SetPosition(x0 + index * (bw + g.P(8)), y)

    # ------------------------------------------------------------------ data
    def Count(self):
        try:
            return int(self.window.mycharacters.GetMyCharacterCount())
        except Exception:
            return 0

    def Detail(self, slot):
        """(name, level, guild, played, family) of a display slot, from the window's account data."""
        window = self.window
        data = window.mycharacters.GetDisplayData(slot) or {}
        conqueror = int(data.get('CONQUEROR_LEVEL', 0) or 0)
        level = conqueror if conqueror > 0 else int(data.get('LEVEL', 0) or 0)
        guild = (data.get('GUILDNAME') or '').strip()
        played = window.FormatPlayTime(data.get('PLAYTIME', 0))
        return data.get('NAME', ''), level, guild, played, getattr(window, 'familyName', '') or '–'

    def Refresh(self):
        window, g = self.window, self.g
        self.hidden.extend(_hide_column(window, self.keep))   # Living Sigil shows its rows again (reload, stats)
        count = self.Count()
        selected = getattr(window, 'SelectSlot', -1)
        self.Layout()
        for index, row in enumerate(self.rows):
            if index < count:
                name, level, guild, played, unused = self.Detail(index)
                race = window.mycharacters.GetRace(index)
                face = window.RACE_FACE_PATH.get(race, '') + ('1.sub' if index == selected else '2.sub')
                row.SetData((name, level, guild, played), face, index == selected)
            else:
                row.SetData(None, None, False)
        has = 0 <= (selected if selected is not None else -1) < count
        for widget in [self.nameText, self.levelText, self.lvText, self.divider] + self.infoLabels + self.infoValues:
            widget.Show() if has else widget.Hide()
        self.stats.Show(has)
        if has:
            name, level, guild, played, family = self.Detail(selected)
            self.nameText.SetText(name)
            self.levelText.SetText(str(level))
            self.lvText.SetPosition(g.margin + g.cw - Width(self.levelText) - g.P(8), self.lvY)
            for value, text in zip(self.infoValues, (family, guild or '–', played)):
                value.SetText(text)
            self.stats.Set(window.statpoint, window.StatRatio)
            self.play.Enable()
            self.actions[1].Enable()
        else:
            self.play.Disable()
            self.actions[1].Disable()

    # ------------------------------------------------------------------ actions
    def Bottom(self):
        return max(b.GetGlobalPosition()[1] + b.GetHeight() for b in self.actions)

    def OnRow(self, index):
        window = self.window
        if getattr(window, 'Disable', False):
            return
        if index < self.Count():
            if index != window.SelectSlot:
                try:
                    import snd
                    snd.PlaySound('sound/ui/click.wav')
                except Exception:
                    pass
                window.SelectButton(index)
        else:
            window.CreateCharacterInRow(index)

    def OnRowDouble(self, index):
        if index < self.Count():
            self.OnRow(index)
            self.OnPlay()
        else:
            self.window.CreateCharacterInRow(index)

    def OnPlay(self):
        if not getattr(self.window, 'Disable', False):
            self.window.StartGameButton()

    def OnCreate(self):
        if not getattr(self.window, 'Disable', False):
            self.window.CreateCharacterButton()

    def OnDelete(self):
        if not getattr(self.window, 'Disable', False):
            self.window.InputPrivateCode()

    def OnExit(self):
        self.window.ExitButton()

    def SetEnabled(self, enabled):
        for widget in [self.play] + self.actions:
            widget.Enable() if enabled else widget.Disable()
        if enabled:
            self.Refresh()

    # ------------------------------------------------------------------ delete confirmation
    def OpenDelete(self, number_mode, max_len, accept, cancel):
        self.CloseDelete()
        selected = self.window.SelectSlot
        name, level, guild, played, unused = self.Detail(selected)
        race = self.window.mycharacters.GetRace(selected)
        self.dialog = DeleteDialog(self, (name, level, guild, played), self.window.RACE_FACE_PATH.get(race, '') + '1.sub',
                                   number_mode, max_len, accept, cancel)
        return self.dialog

    def CloseDelete(self):
        if self.dialog is not None:
            self.dialog.Destroy()
            self.dialog = None

    def Destroy(self):
        CancelOwnedDelete(self)
        self.CloseDelete()
        self.root.Hide()
        self.root = None
        self.rows = []

    def Undo(self):
        """Back to the Living Sigil column (after a failure)."""
        try:
            CancelOwnedDelete(self)
            self.CloseDelete()
            if self.root is not None:
                self.root.Hide()
            for widget in self.hidden:
                widget.Show()
        except Exception:
            pass


class DeleteDialog(ui.Window):
    """Modal delete confirmation: the darkened screen, the character card, 'Smazání nejde vrátit. Zadej kód ze správy
    účtu.', the code field, the dark blood Smazat (left, the confirmation) and Zrušit (right)."""

    def __init__(self, column, card, face, number_mode, max_len, accept, cancel):
        ui.Window.__init__(self)
        import uiconfirm
        uiconfirm.Bind(self, 'acceptButton')
        g = column.g
        self.accept_cb, self.cancel_cb = accept, cancel
        self.SetParent(column.root)
        self.SetPosition(0, 0)
        self.SetSize(g.W, g.H)
        self.scrim = uir1.Rect(self, 0, 0, g.W, g.H, 0x000000, 0.47)
        w = max(g.P(420), 380)
        h = 12 + g.P(12) + g.P(56) + g.P(12) + g.P(28) + T.FIELD_H + g.P(16) + g.P(30) + g.P(16) + 30
        x, y = (g.W - w) // 2, (g.H - h) // 2
        self.frame = uir1.Frame(self, x, y, w, h, 'dialog')
        self.title = Text(self, 'Smazat postavu'.upper(), x + w // 2, y + 8, g.title(), T.IVORY, align='center')
        self.vein = uir1.Vein(self, x + 12, y + 30, w - 24)
        yy = y + 30 + g.P(12)
        self.card = Plate(self, x + g.P(16), yy, w - 2 * g.P(16), g.P(56))
        self.card.SetState('normal')
        size = PORTRAIT if g.s >= 0.95 else 36
        self.face = Portrait(self.card, g.P(10), (g.P(56) - size) // 2, size)
        self.face.Load(face)
        name, level, guild, played = card
        self.cardName = Text(self.card, name, g.P(10) + size + g.P(12), g.P(9), g.noto(19, True), T.IVORY)
        self.cardMeta = Text(self.card, '  ·  '.join(p for p in ('Lv. %d' % level, guild, played) if p), g.P(10) + size + g.P(12),
                             g.P(31), g.noto(15), T.INK_DIM)
        yy += g.P(56) + g.P(12)
        self.message = Text(self, 'Smazání nejde vrátit. Zadej kód ze správy účtu.', x + g.P(16), yy, g.noto(17), T.INK)
        yy += g.P(28)
        kit = uir1.Kit()
        self.field = uir1.Field(self, kit, x + g.P(16), yy, w - 2 * g.P(16), max_len=max_len, number=number_mode,
                                font=g.noto(17))
        self.field.edit.SetSecret()
        self.field.edit.SetReturnEvent(ui.__mem_func__(self.Accept))
        self.field.edit.SetEscapeEvent(ui.__mem_func__(self.Cancel))
        bw = g.P(120)
        by = y + h - g.P(16) - g.P(30)
        # the owner's rule (8. 10., PRAVIDLA-UI.md): the confirmation on the left, the cancel on the right
        self.acceptButton = PlateButton(self, x + w - g.P(16) - 2 * bw - g.P(8), by, bw, g.P(30), 'SMAZAT', g.caps(15),
                                        event=self.Accept, danger=True)
        self.cancelButton = PlateButton(self, x + w - g.P(16) - bw, by, bw, g.P(30), 'ZRUŠIT', g.caps(15),
                                        event=self.Cancel)
        self.Show()
        self.SetTop()
        self.field.Focus()

    def GetText(self):
        return self.field.edit.GetText()

    def Accept(self):
        if self.accept_cb:
            self.accept_cb()
        return True

    def Cancel(self):
        if self.cancel_cb:
            self.cancel_cb()
        return True

    def OnPressEscapeKey(self):
        return self.Cancel()

    def Destroy(self):
        try:
            self.field.edit.KillFocus()
        except Exception:
            pass
        self.Hide()


# =========================================================================== character creation
class CreateColumn(object):
    """The creation form on window.dlgBoard; window = new_introcreate.CreateCharacterWindow."""

    texts = {'title': 'Tvorba postavy', 'job': 'Povolání', 'gender': 'Pohlaví', 'shape': 'Typ',
             'name': 'Jméno postavy', 'rules': '2–16 znaků', 'create': 'Vytvořit', 'back': 'Zpět',
             'stats': 'Počáteční statistiky', 'male': 'Muž', 'female': 'Žena', 'shape_n': 'Typ %d'}

    def __init__(self, window, jobs, face_of, name_error, scale=None):
        """jobs = [job names]; face_of(index, selected) -> portrait path; name_error(text) -> None or a message."""
        self.window, self.jobs, self.face_of, self.name_error = window, list(jobs), face_of, name_error
        self.root, self.hidden = None, []
        self.keep = (getattr(window, 'editCharacterName', None),)      # adopted by the R1 name field
        self.g = g = Geo(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight(), scale)
        self.f_name, self.f_small, self.f_text = g.noto(19, True), g.noto(15), g.noto(17)
        self.hidden = _hide_column(window, self.keep)
        self.root = _root(window, g)
        self.title = Text(self.root, self.texts['title'].upper(), 0, 0, g.title(), T.IVORY)
        self.titleVein = uir1.Vein(self.root, 0, 0, g.P(210))
        self.jobLabel = Text(self.root, self.texts['job'], 0, 0, self.f_small, T.INK_DIM)
        self.jobRows = [JobRow(self, index, name) for index, name in enumerate(self.jobs)]
        self.genderLabel = Text(self.root, self.texts['gender'], 0, 0, self.f_small, T.INK_DIM)
        self.shapeLabel = Text(self.root, self.texts['shape'], 0, 0, self.f_small, T.INK_DIM)
        q = 10
        self.gender = [PlateButton(self.root, 0, 0, q, g.P(36), text.upper(), g.caps(15), event=lambda i=i: window.SelectGender(i))
                       for i, text in enumerate((self.texts['male'], self.texts['female']))]
        # digits in Noto: Cinzel draws 1 like a Roman I
        self.shape = [PlateButton(self.root, 0, 0, q, g.P(36), self.texts['shape_n'] % (i + 1), g.noto(16),
                                  event=lambda i=i: window.SelectShape(i)) for i in range(2)]
        self.nameLabel = Text(self.root, self.texts['name'], 0, 0, self.f_small, T.INK_DIM)
        self.counter = Text(self.root, '', 0, 0, self.f_small, T.MUTED, align='right')
        self.error = Text(self.root, '', 0, 0, self.f_text, T.IVORY)
        self.errorMark = uir1.Rect(self.root, 0, 0, max(4, g.P(4)), max(14, g.P(16)), 0xD30D0E, 1.0)
        self.create = PlateButton(self.root, 0, 0, g.cw, g.P(56), self.texts['create'].upper(), g.caps(24),
                                  event=self.OnCreate, primary=True)
        self.back = PlateButton(self.root, 0, 0, g.P(120), g.P(34), self.texts['back'].upper(), g.caps(15),
                                event=self.OnBack)
        self.jobName = Text(self.root, '', 0, 0, g.caps(30), T.IVORY, align='center')
        self.statsLabel = Text(self.root, self.texts['stats'], 0, 0, self.f_small, T.MUTED, align='center')
        self.stats = Stats(self.root, g, self.f_text)
        self.Layout()

    def Layout(self):
        g = self.g
        x0 = g.margin
        logo_y = g.P(40) if g.tight else g.P(58)
        _place_scene(self.window, g, logo_y)
        y = logo_y + int(round(96 * g.s)) + (g.P(24) if g.tight else g.P(40))
        self.title.SetPosition(x0, y)
        # the title keeps the window-title size (Cinzel 16): its red line follows the font cell, not the scale
        self.titleVein.SetPosition(x0 - 4, y + uir1.FontCell(g.title()) + 6 - T.VEIN_ROW)
        y += g.P(54)
        self.jobLabel.SetPosition(x0, y)
        y += g.P(24)
        rh = g.P(54)
        for row in self.jobRows:
            row.Place(x0, y, g.cw, rh)
            y += rh + g.P(6)
        y += g.P(10)
        half = (g.cw - g.P(8)) // 2
        q = half // 2 - g.P(2)
        self.genderLabel.SetPosition(x0, y)
        self.shapeLabel.SetPosition(x0 + half + g.P(8), y)
        y += g.P(24)
        for i, button in enumerate(self.gender):
            button.SetSize(q, g.P(36))
            button.w = q
            button.plate.Resize(q, g.P(36))
            button.SetPosition(x0 + i * (q + g.P(4)), y)
        for i, button in enumerate(self.shape):
            button.SetSize(q, g.P(36))
            button.w = q
            button.plate.Resize(q, g.P(36))
            button.SetPosition(x0 + half + g.P(8) + i * (q + g.P(4)), y)
        for button in self.gender + self.shape:
            button.paint()
        y += g.P(56)
        self.nameLabel.SetPosition(x0, y)
        self.counter.SetPosition(x0 + g.cw, y)
        self.fieldY = y + g.P(24)
        self.errorY = self.fieldY + T.FIELD_H + g.P(8)
        self.error.SetPosition(x0 + g.P(16), self.errorY)
        self.errorMark.SetPosition(x0, self.errorY + 2)
        y += g.P(112) - (g.P(44) - T.FIELD_H)
        self.create.SetPosition(x0, y)
        y += g.P(56) + g.P(70) - g.P(30)
        self.back.SetPosition(x0, y)
        # the job name and the starting stats under the character
        try:
            area = self.window.renderArea
            ax, ay = area.GetLocalPosition()
            feet = ay + area.GetHeight()
        except Exception:
            feet = g.H - g.P(160)
        feet = min(feet, g.H - g.P(40) - g.P(118) - g.P(36))
        self.jobName.SetPosition(g.stage, feet + g.P(16))
        self.statsLabel.SetPosition(g.stage, feet + g.P(52))
        lw, bw = g.P(44), g.P(136)
        colw = lw + bw + g.P(10) + g.P(22) + g.P(30)
        self.stats.Place(g.stage - (colw + lw + bw + g.P(10) + g.P(22)) // 2, feet + g.P(76), colw)

    def AttachField(self, edit):
        """Puts the window's name EditLine into an R1 field (the same line: its events and focus stay)."""
        g = self.g
        try:
            self.editHome = (getattr(self.window, 'nameField', None), edit.GetLocalPosition())
        except Exception:
            self.editHome = None
        self.field = uir1.Field(self.root, uir1.Kit(), g.margin, self.fieldY, g.cw, edit=edit, max_len=16,
                                font=g.noto(20))
        # The line was hidden with the Living Sigil column before (no keys reach a hidden edit line) and its
        # focus was set while it still sat in the old field: show it and give it the keyboard again.
        edit.Show()
        if not getattr(self.window, 'controlsLocked', False):
            self.field.Focus()
        return self.field

    def Refresh(self):
        window = self.window
        self.hidden.extend(_hide_column(window, self.keep))
        for index, row in enumerate(self.jobRows):
            row.SetSelected(index == window.job_id)
        for index, button in enumerate(self.gender):
            button.SetOn(index == window.gender)
        for index, button in enumerate(self.shape):
            button.SetOn(index == window.shape)
        try:
            female_possible = window.M2_CONST_ID[window.job_id][1] != -1
        except Exception:
            female_possible = True
        self.gender[1].Show() if female_possible else self.gender[1].Hide()
        if 0 <= window.job_id < len(self.jobs):
            self.jobName.SetText(self.jobs[window.job_id].upper())
        self.stats.Set(window.statpoint, lambda value: max(0.0, min(1.0, float(value) / 8.0)))
        self.RefreshName()
        hall = getattr(self, 'hall', None)
        if hall is not None and not hall.failed:
            hall.Refresh()

    def RefreshName(self, server_error=None):
        try:
            text = self.window.editCharacterName.GetText()
        except Exception:
            text = ''
        self.counter.SetText('%s  ·  %d / 16' % (self.texts['rules'], len(text)))
        message = server_error if server_error else (self.name_error(text) if text else None)
        if message:
            self.error.SetText(message)
            self.error.Show()
            self.errorMark.Show()
        else:
            self.error.Hide()
            self.errorMark.Hide()
        valid = bool(text) and not message
        locked = getattr(self.window, 'controlsLocked', False)
        self.create.Enable() if (valid and not locked) else self.create.Disable()

    def Bottom(self):
        stats = self.stats.values[3].GetGlobalPosition()[1] + uir1.FontCell(self.stats.font)
        return max(self.back.GetGlobalPosition()[1] + self.back.GetHeight(), stats)

    def OnCreate(self):
        self.window.CreateCharacterButton()

    def OnBack(self):
        self.window.CancelButton()

    def SetEnabled(self, enabled):
        for widget in [row for row in self.jobRows] + self.gender + self.shape + [self.back]:
            widget.Enable() if enabled else widget.Disable()
        self.RefreshName()
        hall = getattr(self, 'hall', None)
        if hall is not None and not hall.failed:
            hall.SetEnabled(enabled)

    def Destroy(self):
        hall = getattr(self, 'hall', None)
        if hall is not None:
            self.hall = None
            try:
                hall.Destroy()
            except Exception:
                uir1.TraceFailure(WHAT + ' create hall destroy')
        # Native parent destruction invalidates child callbacks. Return the shared
        # edit before dropping the form, including during a resolution rebuild.
        self.RestoreField()
        self.root.Hide()
        self.root = None

    def RestoreField(self):
        home = getattr(self, 'editHome', None)
        edit = getattr(self.window, 'editCharacterName', None)
        if home and home[0] is not None and edit is not None:
            edit.SetParent(home[0])
            edit.SetPosition(*home[1])
            self.editHome = None

    def Undo(self):
        hall = getattr(self, 'hall', None)
        if hall is not None:
            self.hall = None
            try:
                hall.Undo()
            except Exception:
                pass
        try:
            if self.root is not None:
                self.root.Hide()
            for widget in self.hidden:
                widget.Show()
            self.RestoreField()
            edit = getattr(self.window, 'editCharacterName', None)
            if edit is not None:
                edit.Show()
                edit.SetFocus()
        except Exception:
            pass


class JobRow(uir1.Interactive):
    def __init__(self, column, index, name):
        uir1.Interactive.__init__(self)
        self.column, self.index = column, index
        self.SetParent(column.root)
        self.plate = Plate(self, 0, 0, 10, 10)
        self.face = Portrait(self, 0, 0, PORTRAIT)
        self.name = Text(self, name, 0, 0, column.f_name, T.INK_DIM, valign='center')
        self.selected = False
        self.Show()

    def Place(self, x, y, w, h):
        g = self.column.g
        self.SetPosition(x, y)
        self.SetSize(w, h)
        self.plate.Resize(w, h)
        size = PORTRAIT if g.s >= 0.95 else 36
        self.face.size = size
        self.face.SetPosition(g.P(12), (h - size) // 2)
        Move(self.name, g.P(12) + size + g.P(16), h // 2)

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.face.Load(self.column.face_of(self.index, self.selected))
        SetColor(self.name, T.IVORY if self.selected else T.INK_DIM)
        self.paint()

    def paint(self):
        if not self.enabled:
            self.plate.SetState('disabled')
        else:
            self.plate.SetState('selected' if self.selected else ('hover' if self.hovered else 'normal'))

    def click(self):
        self.column.window.SelectJob(self.index)


# =========================================================================== entry points
BOTTOM_GAP = 24        # px the column keeps above the bottom edge (owner 9. 10.: "dole vzduch")


def _BuildColumn(kind, *args):
    column = kind.__new__(kind)
    try:
        column.__init__(*args)
    except Exception:
        column.Undo()
        raise
    return column


def _Fit(build, column=None):
    """Builds the column at its profile scale; when it would not fit the screen height it is built again, scaled
    down so its bottom ends BOTTOM_GAP px above the edge (1366 x 768 / 1024 x 768)."""
    column = build(None)
    limit = column.g.H - BOTTOM_GAP
    # the select column is fitted for a FULL account (5 occupied rows are taller than empty ones), so the size
    # does not change when characters are created or deleted
    worst = getattr(column, 'WorstBottom', None)
    bottom = worst() if worst else column.Bottom()
    if bottom > limit:
        scale = column.g.s * float(limit) / float(bottom) * 0.995
        hidden = column.hidden
        column.root.Hide()
        try:
            column = build(scale)
        except Exception:
            column.Undo()
            raise
        column.hidden = hidden + column.hidden          # Undo must still bring the Living Sigil widgets back
    return column
def AttachSelect(window, allow_hall=True):
    """The R1 select column for window, or None (Starý vzhled, or building failed: Living Sigil stays)."""
    if not uir1.UseR1():
        return None
    column = None
    try:
        rows = 5
        try:
            import app
            if not app.ENABLE_PLAYER_PER_ACCOUNT5:
                rows = 4
        except Exception:
            pass
        # the hall with the characters in an arc (root/uipregamehall.py); None = switched off
        # (off=1 in pregame-hall.cfg), a screen under 800 x 600 or it failed -> this R1 column as before
        try:
            try:
                import uipregamehall
            except ImportError:         # an engine / test without chr, grp: the column
                uipregamehall = None
            hall = uipregamehall.Attach(window, rows) if allow_hall and uipregamehall else None
            if hall is not None:
                return hall
        except Exception:
            uir1.TraceFailure(WHAT + ' hall')
        column = _Fit(lambda scale: _BuildColumn(SelectColumn, window, rows, scale))
        return column
    except Exception:
        uir1.TraceFailure(WHAT + ' select')
        if column is not None:
            column.Undo()
        return None


def AttachCreate(window, jobs, face_of, name_error):
    if not uir1.UseR1():
        return None
    column = None
    try:
        column = _Fit(lambda scale: _BuildColumn(CreateColumn, window, jobs, face_of, name_error, scale))
        column.AttachField(window.editCharacterName)
        # the creation in the hall (root/uipregamehall.py): the same scene as the select; None = the column alone
        try:
            import uipregamehall
        except ImportError:
            uipregamehall = None
        try:
            column.hall = uipregamehall and uipregamehall.AttachCreate(window, column)
        except Exception:
            uir1.TraceFailure(WHAT + ' create hall')
            column.hall = None
        column.Refresh()
        return column
    except Exception:
        uir1.TraceFailure(WHAT + ' create')
        if column is not None:
            column.Undo()
        return None


def Active(column):
    return column is not None and not getattr(column, 'failed', False)


def Safe(column, method, *args):
    """Calls column.method(*args); a failure puts the Living Sigil column back for good and returns None."""
    if not Active(column):
        return None
    try:
        return getattr(column, method)(*args)
    except Exception:
        uir1.TraceFailure(WHAT + ' ' + method)
        column.failed = True
        column.Undo()
        return None
