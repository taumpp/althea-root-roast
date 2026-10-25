# -*- coding: utf-8 -*-
"""Sledování dropu (the drop tracker window) in the Althea R1 look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md).

uidroptracker.DropTrackerWindow keeps the window (ui.BoardWithTitleBar, float + movable, 430 x 480 for the summary
and 760 x 500 for the details) and every function: the recording state and the session time, the Zabití /
Předměty cards, the five most frequent drops (left click opens the details of the item, right click hides it, the
icon shows the item tooltip), the three main sources, Pozastavit / Pokračovat, Smazat, Detaily; in the details
Zpět, Souhrn / Záznam, the filters (time, source, icon lifetime, hidden items), the table Předmět / Zdroj / Počet /
Čas with the expandable sources of an item and the pages. The window logic (Refresh, SetDetailed, the model calls)
stays in uidroptracker; this module only builds the widgets it drives, with the same attribute names:

* the board gets the R1 frame and header (title, vein, plain X) through uir1.BoardSkin; the crimson board art and
  title bar are hidden, the board's base becomes the R1 background (re-tiled after every size change);
* the cards are R1 panels, the row lists R1 rows (hover band, divider), the headings R1 sections;
* the buttons are R1 buttons (Detaily the primary one), Souhrn / Záznam an R1 segment (the window's "* " marker of
  the selected mode selects the cell instead of being shown), the pages small R1 buttons.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building the R1 look
restores the original look (traced to syserr) and the R1 look is not tried again in this session.
"""
import ui

import uir1
import uir1tokens as T

import uidroptracker as D

WHAT = u'Sledování dropu'
COMPACT_ROW = (12, 143, 406, 34, 37)      # x, y, width, height, pitch of the five drop rows (original geometry)
SOURCE_ROW = (12, 356, 406, 23)           # x, first y, width, pitch of the three source rows
DETAIL_ROW = (10, 125, 740, 30, 32)       # x, y, width, height, pitch of the ten table rows
TOOLBAR_Y = 33                            # the detail toolbar (small 22 px buttons)
STATUS_Y = 63                             # the detail status line / the second filter row
COLUMNS_Y = 100                           # the table headings
VALUE_COLOR = 0xFFE8C77A                  # amounts: the warm gold of the original numbers, a little calmer
GREEN = D.COLOR_GREEN
PAUSED = D.COLOR_RED

_failed = set()


def UseR1():
    return WHAT not in _failed and uir1.UseR1()


def Fail():
    _failed.add(WHAT)
    uir1.TraceFailure(WHAT)


# --------------------------------------------------------------------------- rows
class Row(uir1.Interactive):
    """A clickable list row: the hover band (lighter graphite) and a quiet divider under it. Left / right clicks go to
    the owner row's handlers; the hover is kept while the mouse is over the item icon inside the row."""

    def __init__(self, parent, x, y, w, h):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.band = uir1.Band(self, 0, 0, int(w), int(h))
        self.divider = uir1.Divider(self, 0, int(h) - 1, int(w))
        self.on_left = self.on_right = None
        self.icon_hover = False

    def paint(self):
        self.band.SetState('hover' if (self.hovered or self.icon_hover) and self.enabled else 'normal')

    def SetIconHover(self, hovered):
        self.icon_hover = bool(hovered)
        self.paint()

    def click(self):
        if self.on_left:
            self.on_left()

    def OnMouseRightButtonUp(self):
        if self.on_right:
            self.on_right()
        return True


def _Icon(row, owner_row):
    """The item icon (ui.ImageBox like the original: _LoadItemIcon scales it): its hover shows the item tooltip."""
    icon = ui.ImageBox()
    icon.SetParent(row)
    icon.SetPosition(10, 2)

    def over_in():
        row.SetIconHover(True)
        owner_row._ShowToolTip()

    def over_out():
        row.SetIconHover(False)
        owner_row._HideToolTip()
    icon.OnMouseOverIn = over_in
    icon.OnMouseOverOut = over_out
    icon.Show()
    return icon


class KpiCard(D.KpiCard):
    """Zabití / Předměty: an R1 panel with the label and the value (Noto Sans, ivory)."""

    def __init__(self, parent, kit, x, title):
        self.panel = uir1.Frame(parent, x, 58, 198, 57, 'panel')
        self.title = uir1.Text(self.panel, title, 99, 8, kit.font('text_s'), T.INK_DIM, align='center', valign='top')
        self.value = uir1.Text(self.panel, '0', 99, 27, kit.font('text_b'), T.IVORY, align='center', valign='top')


class CompactDropRow(D.CompactDropRow):
    def __init__(self, owner, parent, kit, rowIndex):
        self.owner = owner
        self.data = None
        x, y, w, h, pitch = COMPACT_ROW
        self.panel = Row(parent, x, y + rowIndex * pitch, w, h)
        self.panel.on_left = self._OnLeftClick
        self.panel.on_right = self._OnRightClick
        self.icon = _Icon(self.panel, self)
        font = kit.font('text_s')
        self.name = uir1.Text(self.panel, '', 52, 1, font, T.INK, valign='top', limit=225)
        self.source = uir1.Text(self.panel, '', 52, 17, font, T.INK_DIM, valign='top', limit=265)
        self.amount = uir1.Text(self.panel, '', 394, uir1.CellTop(h, font), font, VALUE_COLOR, align='right',
                                valign='top')
        self.panel.Hide()


class CompactSourceRow(D.CompactSourceRow):
    def __init__(self, parent, kit, rowIndex):
        x, y0, w, pitch = SOURCE_ROW
        font = kit.font('text_s')
        y = y0 + rowIndex * pitch + uir1.CellTop(pitch, font)
        self.rank = uir1.Text(parent, '#%d' % (rowIndex + 1), x + 6, y, font, T.MUTED, valign='top')
        self.name = uir1.Text(parent, '', x + 36, y, font, T.INK, valign='top', limit=220)
        self.meta = uir1.Text(parent, '', x + w - 4, y, font, T.INK_DIM, align='right', valign='top')
        self.Hide()


class DetailDropRow(D.DetailDropRow):
    """A table row; the window's SetData places the name for an item or a source child (x 43 / 25), the R1 row
    keeps the name's cell top and maps the original colours to the R1 ink."""

    COLORS = {D.COLOR_TEXT: T.INK, D.COLOR_SOURCE: T.INK_DIM}

    def __init__(self, owner, parent, kit, rowIndex):
        self.owner = owner
        self.data = None
        x, y, w, h, pitch = DETAIL_ROW
        self.panel = Row(parent, x, y + rowIndex * pitch, w, h)
        self.panel.on_left = self._OnLeftClick
        self.panel.on_right = self._OnRightClick
        self.icon = _Icon(self.panel, self)
        font = kit.font('text_s')
        self.top = uir1.CellTop(h, font)
        self.name = uir1.Text(self.panel, '', 43, self.top, font, T.INK, valign='top', limit=295)
        self.source = uir1.Text(self.panel, '', 400, self.top, font, T.INK_DIM, align='center', valign='top',
                                limit=245)
        self.amount = uir1.Text(self.panel, '', 615, self.top, font, VALUE_COLOR, align='center', valign='top')
        self.age = uir1.Text(self.panel, '', 705, self.top, font, T.MUTED, align='center', valign='top')
        self.panel.Hide()

    def SetData(self, data, now):
        D.DetailDropRow.SetData(self, data, now)
        x = self.name.GetLocalPosition()[0]
        self.name.SetPosition(x, self.top)
        is_child = bool(data.get('is_source_child'))
        self.name.SetPackedFontColor(T.INK_DIM if is_child else T.INK)


# --------------------------------------------------------------------------- the mode switch
class ModeTab(object):
    """Souhrn or Záznam of the R1 segment, driven like the original button: the window sets "* Souhrn" for the
    selected mode (the marker selects the cell, the label stays plain) and shows / hides it with the detail view."""

    def __init__(self, segment, index, value):
        self.segment, self.index, self.value = segment, index, value
        self.text = ''

    def SetText(self, text):
        self.text = text
        selected = text.startswith('* ')
        label = text[2:] if selected else text
        cell = self.segment.cells[self.index]
        if cell.label.GetText() != label:
            cell.label.SetText(label)
        if selected:
            self.segment.SetValue(self.value)

    def GetText(self):
        return self.text

    def Show(self):
        self.segment.Show()

    def Hide(self):
        self.segment.Hide()


# --------------------------------------------------------------------------- the build
class Skin(object):
    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.widgets = []
        self.board = None

    def own(self, widget):
        self.widgets.append(widget)
        return widget

    def Build(self):
        window, kit = self.window, self.kit
        self.board = uir1.BoardSkin(window, kit, D._Locale('DROP_TRACKER_TITLE', 'Drop tracker'),
                                    on_close=ui.__mem_func__(window.Close))
        self.BuildCompact()
        self.BuildDetails()
        return self

    def text(self, text, x, y, color=T.INK_DIM, align='left', font=None):
        return self.own(uir1.Text(self.window, text, x, y, font or self.kit.font('text_s'), color, align=align,
                                  valign='top'))

    def button(self, x, y, w, text, event, args=(), primary=False, small=False):
        def call():
            event(*args)
        return self.own(uir1.Button(self.window, self.kit, x, y, w, text, primary=primary, small=small, event=call))

    def BuildCompact(self):
        window, kit = self.window, self.kit
        L = D._Locale
        window.compactStatus = self.text('', 14, 34, GREEN)
        window.compactDuration = self.text('', 416, 34, T.INK_DIM, align='right')
        window.compactWidgets.extend((window.compactStatus, window.compactDuration))

        window.kpiKills = KpiCard(window, kit, 12, L('DROP_TRACKER_KILLS', 'Kills'))
        window.kpiItems = KpiCard(window, kit, 220, L('DROP_TRACKER_ITEMS', 'Items'))
        self.own(window.kpiKills.panel)
        self.own(window.kpiItems.panel)

        window.topDropsTitle = self.own(uir1.Section(window, kit, 12, 121, 406, L('DROP_TRACKER_TOP_DROPS',
                                                                                  'Top drops')))
        window.compactEmpty = self.text(L('DROP_TRACKER_EMPTY', 'No drops in the selected scope yet'), 215, 228,
                                        T.MUTED, align='center')
        window.compactWidgets.extend((window.topDropsTitle, window.compactEmpty))
        for rowIndex in range(D.COMPACT_DROP_COUNT):
            row = CompactDropRow(window, window, kit, rowIndex)
            self.own(row.panel)
            window.compactRows.append(row)

        window.topSourcesTitle = self.own(uir1.Section(window, kit, 12, 333, 406, L('DROP_TRACKER_TOP_SOURCES',
                                                                                    'Top sources')))
        window.compactWidgets.append(window.topSourcesTitle)
        for rowIndex in range(D.COMPACT_SOURCE_COUNT):
            row = CompactSourceRow(window, kit, rowIndex)
            self.widgets.extend((row.rank, row.name, row.meta))
            window.sourceRows.append(row)

        # Footer: three equal buttons inside the 12 px padding; Detaily (the way on) is the primary one.
        y = window.COMPACT_HEIGHT - T.PAD - T.BTN_H
        w = (window.COMPACT_WIDTH - 2 * T.PAD - 2 * 10) // 3
        window.compactPauseButton = self.button(T.PAD, y, w, '', window.TogglePause)
        window.resetButton = self.button(T.PAD + w + 10, y, w, L('DROP_TRACKER_RESET', 'Reset'), window.Reset)
        window.detailsButton = self.button(T.PAD + 2 * (w + 10), y, w, L('DROP_TRACKER_OPEN_DETAILS', 'Details >'),
                                           window.SetDetailed, (True,), primary=True)
        window.compactWidgets.extend((window.compactPauseButton, window.resetButton, window.detailsButton))

    def BuildDetails(self):
        window, kit = self.window, self.kit
        L = D._Locale
        width = window.DETAIL_WIDTH
        y = TOOLBAR_Y
        window.backButton = self.button(T.PAD, y, 72, L('DROP_TRACKER_BACK', '< Back'), window.SetDetailed,
                                        (False,), small=True)
        segment = self.own(uir1.Segment(window, kit, [('summary', L('DROP_TRACKER_SUMMARY', 'Items')),
                                                      ('log', L('DROP_TRACKER_LOG', 'History'))],
                                        event=window.SetMode, font=kit.font('text_s'), min_cell=78))
        segment.SetPosition(T.PAD + 72 + 8, y - 1)
        self.segment = segment
        window.modeSummary = ModeTab(segment, 0, 'summary')
        window.modeLog = ModeTab(segment, 1, 'log')
        x = T.PAD + 72 + 8 + segment.Width() + 8
        window.filtersButton = self.button(x, y, 104, L('DROP_TRACKER_FILTERS', 'Filters'), window.ToggleAdvanced,
                                           small=True)
        window.detailPauseButton = self.button(width - T.PAD - 104, y, 104, '', window.TogglePause, small=True)
        window.detailWidgets.extend((window.backButton, window.modeSummary, window.modeLog, window.filtersButton,
                                     window.detailPauseButton))

        x += 104 + 8
        window.timeButton = self.button(x, y, 84, '', window.CycleTimeWindow, small=True)
        window.sourceButton = self.button(x + 84 + 8, y, 96, '', window.CycleSourceFilter, small=True)
        window.hiddenButton = self.button(width - T.PAD - 104, STATUS_Y - 4, 104, '', window.ToggleHidden,
                                          small=True)
        window.recentLifetimeButton = self.button(width - T.PAD - 2 * 104 - 8, STATUS_Y - 4, 104, '',
                                                  window.CycleRecentLifetime, small=True)
        window.advancedWidgets.extend((window.timeButton, window.sourceButton, window.recentLifetimeButton,
                                       window.hiddenButton))

        window.detailStatus = self.text('', 14, STATUS_Y, T.INK_DIM)
        window.detailHint = self.text(L('DROP_TRACKER_DETAIL_HINT', 'Left click expands sources | Right click hides'),
                                      width - 14, STATUS_Y, T.MUTED, align='right')
        window.detailEmpty = self.text(L('DROP_TRACKER_EMPTY', 'No drops in the selected scope yet'), 380, 262,
                                       T.MUTED, align='center')
        window.detailWidgets.extend((window.detailStatus, window.detailHint, window.detailEmpty))

        headers = ((52, L('DROP_TRACKER_ITEM', 'Item'), 'left'), (410, L('DROP_TRACKER_SOURCE', 'Source'), 'center'),
                   (625, L('DROP_TRACKER_AMOUNT', 'Amount'), 'center'), (715, L('DROP_TRACKER_AGE', 'Age'), 'center'))
        for x, text, align in headers:
            window.detailWidgets.append(self.text(text, x, COLUMNS_Y, T.INK_DIM, align=align,
                                                  font=kit.font('text_sb')))
        window.detailWidgets.append(self.own(uir1.Divider(window, DETAIL_ROW[0], COLUMNS_Y + kit.cell('text_sb') + 3,
                                                          DETAIL_ROW[2])))

        for rowIndex in range(D.DETAIL_ROW_COUNT):
            row = DetailDropRow(window, window, kit, rowIndex)
            self.own(row.panel)
            window.detailRows.append(row)

        y = window.DETAIL_HEIGHT - T.PAD - T.BTN_H_S
        window.previousButton = self.button(width // 2 - 80, y, 30, '<', window.PreviousPage, small=True)
        window.pageText = self.text('', width // 2, y + uir1.CellTop(T.BTN_H_S, kit.font('text_s')), T.INK_DIM,
                                    align='center')
        window.nextButton = self.button(width // 2 + 50, y, 30, '>', window.NextPage, small=True)
        window.detailWidgets.extend((window.previousButton, window.pageText, window.nextButton))

    def Resize(self, w, h):
        self.board.Resize(w, h)

    def Undo(self):
        """A failed build: the R1 widgets go, the board gets its original art back, the window's lists are empty."""
        for widget in reversed(self.widgets):
            try:
                widget.Hide()
            except Exception:
                pass
        self.widgets = []
        if self.board is not None:
            try:
                self.board.Restore()
            except Exception:
                pass
        window = self.window
        for name in ('compactWidgets', 'detailWidgets', 'advancedWidgets', 'compactRows', 'sourceRows',
                     'detailRows'):
            setattr(window, name, [])


def Build(window):
    """The R1 look of a DropTrackerWindow (its board already made, its lists empty); None when the original look is
    used ("Starý vzhled", or the R1 look failed - then the original look is back and the window builds it)."""
    if not UseR1():
        return None
    skin = Skin(window)
    try:
        return skin.Build()
    except Exception:
        Fail()
        skin.Undo()
        return None


# --------------------------------------------------------------------------- the strip of the latest drops
# The strip of the latest drops on the bottom bar (D.TaskBarDropStrip) and its free variant (D.FloatingDropStrip):
# every icon on the R1 item slot C (the cell drawn under the icon, nothing else moves), the hover as the R1 row
# hover, the amount in the calmer gold of the R1 drop tracker (signed for the x64 binding), the grip of the free strip
# and its edit backdrop in graphite (the editing grip in dark blood red). "Starý vzhled" keeps the original strip;
# a failure is traced and the strip keeps its original look for the rest of the session.
STRIP = u'the strip of the latest drops'
STRIP_HOVER = (T.BAND_HOVER, 0.75)
STRIP_BACKDROP = (0x141213, 0.6)
GRIP = {'normal': (T.BORDER, 0.55, T.MUTED), 'hover': (T.BAND_HOVER, 0.9, T.INK), 'editing': (T.RED_DK, 0.6, T.IVORY)}


def _Signed(color):
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color & 0x80000000 else color


class StripLook(object):
    """The R1 strip look shared by every icon and grip of a strip (None from StripR1 = the original look)."""

    def Cell(self, icon):
        """The R1 item slot C under one strip icon: made by the icon before its own hover, image and amount."""
        return uir1.SlotCell(icon, 0, 0)

    def Hover(self, alpha=1.0):
        colour, own = STRIP_HOVER
        return uir1.GenerateColor(colour, own * max(0.0, min(1.0, float(alpha))))

    def Backdrop(self):
        return uir1.GenerateColor(*STRIP_BACKDROP)

    def Amount(self, alpha=1.0):
        alpha_byte = max(0, min(255, int(float(alpha) * 255.0)))
        return _Signed((alpha_byte << 24) | (VALUE_COLOR & 0x00FFFFFF))

    def Grip(self, state):
        """(bar colour, label colour) of the free strip's grip: 'normal', 'hover' or 'editing'."""
        colour, alpha, ink = GRIP[state]
        return uir1.GenerateColor(colour, alpha), _Signed(ink)


def StripR1():
    """The R1 look of the strips, or None (the original look: "Starý vzhled" or an earlier failure)."""
    if STRIP in _failed or not uir1.UseR1():
        return None
    return StripLook()


def StripFailed():
    _failed.add(STRIP)
    uir1.TraceFailure(STRIP)
