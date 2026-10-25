# -*- coding: utf-8 -*-
"""The event calendar (Kalendář událostí) in the R1 look (docs/ALTHEA_R1_KIT.md).

uieventcalendar.EventCalendarWindow stays the window (650 x 592 on every screen) with every function: the week strip
(a click on a day, the week arrows), the day list of events (two columns of five, paging when there are more, the
mouse wheel, the event tooltip under the mouse, a click selects), the detail of the selected event (the original
picture opens a running minigame, the description shows the full conditions), the previous / next day buttons and
the "Dnes" button, Esc and the X close it. The window's own Refresh fills the widgets built here: they carry the same
attribute names and methods as the original ones.

R1 changes only the look: the graphite frame with the title and the vein, the plain X, the week strip as variant 1
(the day text and the event count as today, the selected day in a graphite box, today a short red vein on top) or
variant 2 (a card per day: weekday, big date, the count in words, today "DNES" in red, the selected card brighter
with the vein at its bottom) - one constant, WEEK_VARIANT; the event rows on a dark panel (the selected row a lighter
band with a red mark on the left), the detail panel, R1 buttons in the footer. The ORIGINAL event pictures and the
original status colours (green running, gold time, grey ended) stay.

Filled with events (the local mock of player.event_table, 2026-10-07) two things broke and are fixed here:
* the footer pager ("< 1 / 2 >", shown from eleven events of a day) touched both its neighbours (4 px to "Předchozí
  den", 2 px to "Dnes"): the day buttons are DAY_W wide and the pager is centred in the gap left of "Dnes";
* the detail's "Všechna království: | všechny kanály" showed the colour code of the locale text (|cFF97AE99 ... |h|r),
  a colon before the bar and did not fit its column: the R1 detail shows CleanMetadata() of the original text and its
  right column (DETAIL_COLUMN) starts 7 px further left, so the cleaned line fits;
* the rows of one state were ordered by the event id ("Za 25 min" after "Za 19 h"): R1 orders them by start.

Settings -> "Starý vzhled" (settingslook 'legacy') shows the original window; a failure while building R1 is traced
to syserr and the window is built in the original look (also on every later window in this session).
"""
import re
import weakref
from _weakref import proxy

import ui

import uir1
import uir1tokens as T

WEEK_VARIANT = 1        # 1 = "jako dnes" (text + count), 2 = "karty dnů" (card per day)
TITLE = 'Kalendář událostí'

WIDTH, HEIGHT = 650, 592
ROW_W, ROW_H = 303, 52
WEEK_X, WEEK_PITCH = 50, 78
WEEK = {1: dict(y=72, w=74, h=44, arrow_y=81), 2: dict(y=66, w=72, h=56, arrow_y=83)}
ARROW_X = (18, 604)
EVENTS_BOX = (16, 134, 619, 292)
DETAIL_BOX = (16, 432, 619, 116)
DETAIL_COLUMN = (452, 177)         # the detail's right column (x, width up to 6 px before the panel edge), line at x - 14
FOOTER_Y = 556
DAY_W, TODAY_X, TODAY_W = 128, 250, 150       # "< Předchozí den" / "Další den >" and the centred "Dnes" button
PAGER_LABEL_W = 34                            # the pager "< 1 / 2 >": centred between "Předchozí den" and "Dnes"
_PAGER_X = 16 + DAY_W + (TODAY_X - 16 - DAY_W - (26 + PAGER_LABEL_W + 26)) // 2
PAGER = dict(prev=(_PAGER_X, 558), next=(_PAGER_X + 26 + PAGER_LABEL_W, 558),
             label=(_PAGER_X + 26 + PAGER_LABEL_W // 2, None))   # label: centred on the footer row
_CODES = re.compile(r'\|c[0-9A-Fa-f]{8}|\|[hHr]')

# Plain fills of the week strip (packed RGB): the mock-up's graphite boxes.
BOX_SELECTED = (0x605856, 0x1E1B1C)
BOX_HOVER = (0x484240, 0x1E1B1C)
CARD_NORMAL = (0x383434, 0x0C0B0B)
CARD_SELECTED = (0x6E6462, 0x1E1B1C)
CARD_HOVER = (0x5A5452, 0x141213)
ROW_FILL = 0x2C2627
ROW_HOVER = 0x231F20

_failed = False


def UseR1():
    """R1 unless Settings -> "Starý vzhled" chose the original look, or R1 already failed in this session."""
    return not _failed and uir1.UseR1()


def _Tr(czech, english):
    try:
        from settingslocale import Text
        return Text(czech, english)
    except Exception:
        return czech


def CountWords(count):
    """Event count in words: "žádné", "1 událost", "3 události", "5 událostí"."""
    count = int(count)
    if count <= 0:
        return _Tr('žádné', 'none')
    if count == 1:
        return _Tr('1 událost', '1 event')
    if count < 5:
        return _Tr('%d události' % count, '%d events' % count)
    return _Tr('%d událostí' % count, '%d events' % count)


def Sized(font, size):
    """The kit font descriptor with another pixel size ('Noto Sans:17a' -> 'Noto Sans:21a')."""
    family, _, spec = font.rpartition(':')
    digits = ''.join(ch for ch in spec if ch.isdigit())
    return '%s:%d%s' % (family, int(size), spec[len(digits):])


def CleanMetadata(text):
    """The detail's "kingdom | channel" without the colour / link codes and the colon of the locale's kingdom names
    ("|cFF97AE99Všechna království:|h|r | všechny kanály" -> "Všechna království | všechny kanály")."""
    text = _CODES.sub('', text or '')
    return re.sub(r'\s*:\s*(\||$)', lambda match: ' |' if match.group(1) else '', text).strip()


class _Metadata(object):
    """window.GetEventMetadata for the R1 detail and tooltip: the original text, cleaned (a weak bound method)."""

    def __init__(self, method):
        self.method = ui.__mem_func__(method)

    def __call__(self, row):
        return CleanMetadata(self.method(row))


class _Order(object):
    """window.EventOrder for R1: running first, then upcoming / scheduled / ended, each by its START (the original
    orders a state by the event id: "Za 25 min" came after "Za 19 h"); the id breaks ties."""
    PRIORITY = {'active': 0, 'upcoming': 1, 'scheduled': 2, 'ended': 3}

    def __init__(self, state, start, ident):
        self.state = ui.__mem_func__(state)
        self.start, self.ident = start, ident

    def __call__(self, row):
        return (self.PRIORITY.get(self.state(row), 4), int(row[self.start]), int(row[self.ident]))


class _Call(object):
    """A weak bound method (ui.__mem_func__) with fixed arguments: the R1 buttons call it without arguments."""

    def __init__(self, method, *args):
        self.method = ui.__mem_func__(method)
        self.args = args

    def __call__(self):
        return self.method(*self.args)


class Box(object):
    """Graphite box from plain ui.Bar fills: the fill and a 1 px outline (created before the texts above it)."""

    def __init__(self, parent, x, y, w, h, colours, alpha=1.0):
        self.fill = uir1.Rect(parent, x + 1, y + 1, max(1, w - 2), max(1, h - 2), colours[1], alpha)
        self.lines = [uir1.Rect(parent, x, y, w, 1, colours[0]), uir1.Rect(parent, x, y + h - 1, w, 1, colours[0]),
                      uir1.Rect(parent, x, y + 1, 1, h - 2, colours[0]),
                      uir1.Rect(parent, x + w - 1, y + 1, 1, h - 2, colours[0])]
        self.alpha = alpha
        self.colours = None
        self.SetColours(colours, alpha)

    def SetColours(self, colours, alpha=None):
        alpha = self.alpha if alpha is None else alpha
        if (colours, alpha) == self.colours:
            return
        self.colours = (colours, alpha)
        self.fill.SetColor(uir1.GenerateColor(colours[1], alpha))
        for line in self.lines:
            line.SetColor(uir1.GenerateColor(colours[0]))

    def Widgets(self):
        return [self.fill] + self.lines

    def Show(self):
        for widget in self.Widgets():
            widget.Show()

    def Hide(self):
        for widget in self.Widgets():
            widget.Hide()


class ArrowButton(uir1.Button):
    """Small R1 button with a chevron (week / page arrows). calendarGlyph keeps the window's SetAlpha call harmless:
    the disabled state already shows the dim chevron."""

    class _Glyph(object):
        def SetAlpha(self, alpha):
            pass

    def __init__(self, parent, kit, x, y, direction, event):
        self.direction = direction
        self.chevron = None
        uir1.Button.__init__(self, parent, kit, x, y, 26, '', small=True, event=event)
        self.chevron = uir1.Image(self, uir1.ChevronPath(direction), (26 - T.CHEVRON) // 2, (self.h - T.CHEVRON) // 2)
        self.calendarGlyph = self._Glyph()
        self.paint()

    def paint(self):
        uir1.Button.paint(self)
        if self.chevron is not None:
            state = {'pressed': 'active'}.get(self.state(), self.state())
            self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath(self.direction, state))


class WeekDay(ui.Window):
    """One day of the week strip with the API of uieventcalendar.CalendarWeekDay (SetDate, a click selects)."""

    def __init__(self, owner, kit, variant):
        ui.Window.__init__(self)
        self.owner = proxy(owner)
        self.kit = kit
        self.variant = variant
        self.dateKey = None
        self.selected = self.allowed = self.today = False
        self.hovered = False
        self.count_value = 0
        geo = WEEK[variant]
        self.w, self.h = geo['w'], geo['h']
        self.SetParent(owner)
        self.SetSize(self.w, self.h)
        self.box = Box(self, 0, 0, self.w, self.h, CARD_NORMAL if variant == 2 else BOX_SELECTED,
                       0.9 if variant == 2 else 1.0)
        # Texts are top-aligned lines centred by position (uir1.CellTop): the engine clips a text line to its parent
        # from the line's y down by the text height, so the whole font cell stays inside the day cell.
        if variant == 1:
            self.vein = uir1.Vein(self, 20, 1, 34)
            self.label = self.Line(13, kit.font('text_s'), T.INK)
            self.date = None
            self.count = self.Line(31, kit.font('text_s'), T.INK_DIM)
        else:
            self.vein = uir1.Vein(self, 4, self.h - 2, self.w - 8)
            self.label = self.Line(10, kit.font('text_sb'), T.MUTED)
            self.date = self.Line(26, Sized(kit.font('text_b'), kit.cell('text_b') + 4), T.INK)
            self.count = self.Line(46, kit.font('text_s'), T.INK_DIM)
        self.vein.Hide()
        self.Show()

    def Line(self, centre, font, color):
        """A centred text whose font cell is centred on row ``centre`` (kept inside the cell)."""
        top = max(0, min(self.h - uir1.FontCell(font), centre - uir1.FontCell(font) // 2))
        return uir1.Text(self, '', self.w // 2, top, font, color, align='center', valign='top')

    def SetDate(self, dateKey, count, selected, today, allowed):
        import datetime
        import localeInfo
        self.dateKey, self.selected, self.today, self.allowed = dateKey, selected, today, allowed
        self.count_value = count
        day = datetime.date(*dateKey)
        weekday = getattr(localeInfo, 'EVENT_CALENDAR_WEEKDAY_%d' % day.weekday())
        if self.variant == 1:
            uir1.SetFont(self.label, self.kit.font('text_sb' if selected else 'text_s'),
                         localeInfo.EVENT_CALENDAR_WEEK_DATE % (weekday, day.day, day.month))
            self.label.SetPackedFontColor(T.IVORY if (selected or today) else T.INK if allowed else T.DISABLED)
        else:
            self.label.SetText(_Tr('DNES', 'TODAY') if today else uir1.Upper(weekday))
            self.label.SetPackedFontColor(T.RED_HI if today else T.INK if selected else T.MUTED)
            self.date.SetText('%d.' % day.day)
            self.date.SetPackedFontColor(T.IVORY if selected else T.INK if (allowed and count) else T.DISABLED)
        self.count.SetText(CountWords(count))
        self.count.SetPackedFontColor(T.INK if selected else T.INK_DIM if (allowed and count) else T.DISABLED)
        self.Paint()
        self.Show()

    def Paint(self):
        hover = self.hovered and self.allowed and not self.selected
        if self.variant == 1:
            if self.selected or hover:
                self.box.SetColours(BOX_SELECTED if self.selected else BOX_HOVER, 1.0 if self.selected else 0.6)
                self.box.Show()
            else:
                self.box.Hide()
            self.vein.Show() if self.today else self.vein.Hide()
        else:
            self.box.SetColours(CARD_SELECTED if self.selected else CARD_HOVER if hover else CARD_NORMAL, 0.9)
            self.box.Show()
            self.vein.Show() if self.selected else self.vein.Hide()

    def OnMouseOverIn(self):
        self.hovered = True
        self.Paint()

    def OnMouseOverOut(self):
        self.hovered = False
        self.Paint()

    def OnMouseLeftButtonDown(self):
        if self.allowed and self.dateKey:
            self.owner.SelectDate(self.dateKey)
        return True


def MakeEventRowClass(base):
    """R1 event row: the original CalendarEventRow logic (texts, original status colours, pictures, tooltip, click)
    with an R1 plate instead of the row textures. The original SetEvent loads row_selected.png for the selected row;
    the plate reads that choice."""

    class Plate(object):
        def __init__(self, row):
            self.fill = uir1.Rect(row, 3, 1, ROW_W - 5, ROW_H, ROW_FILL)
            self.mark = uir1.Rect(row, 3, 1, 2, ROW_H, T.RED)
            self.hover = uir1.Rect(row, 3, 1, ROW_W - 5, ROW_H, ROW_HOVER, 0.85)
            self.Set('normal')

        def LoadImage(self, path):
            self.Set('selected' if 'row_selected' in path else 'normal')

        def Set(self, state):
            self.state = state
            self.fill.Show() if state == 'selected' else self.fill.Hide()
            self.mark.Show() if state == 'selected' else self.mark.Hide()
            self.hover.Show() if state == 'hover' else self.hover.Hide()

    class EventRow(base):
        WIDTH, HEIGHT = ROW_W, ROW_H

        def __init__(self, parent, owner, kit, divider=True):
            ui.Window.__init__(self)
            self.owner = proxy(owner)
            self.eventData = None
            self.selected = False
            self.SetParent(parent)
            self.SetSize(self.WIDTH, self.HEIGHT)
            self.background = Plate(self)
            self.divider = uir1.Divider(self, 8, ROW_H + 1, ROW_W - 15) if divider else None
            self.icon = ui.ExpandedImageBox()
            self.icon.SetParent(self)
            self.icon.AddFlag('not_pick')
            self.icon.SetPosition(8, 10)
            self.icon.Show()
            self.name = uir1.Text(self, '', 52, 6, kit.font('text_sb'), T.IVORY, valign='top', limit=240)
            self.clock = uir1.Text(self, '', 52, 28, kit.font('text_s'), T.INK_DIM, valign='top', limit=139)
            self.status = uir1.Text(self, '', 293, 28, kit.font('text_s'), T.INK_DIM, align='right', valign='top',
                                    limit=110)

        def OnMouseOverIn(self):
            if not self.selected:
                self.background.Set('hover')
            if self.eventData:
                self.owner.ShowEventTooltip(self.eventData)

    return EventRow


class EmptyDay(object):
    """The empty state of a day without events, with the Show / Hide / IsShow of the original emptyDay text (the
    window's Refresh calls them): centred in the list panel "Žádné události", a hint under it and, when a later day
    in the calendar's range has events, a small button that selects it. While shown, the list's column line and the
    detail panel's line are hidden (the window itself hides the detail texts); the empty detail frame stays."""

    SEARCH_DAYS = 40

    def __init__(self, skin, window):
        import localeInfo
        kit = skin.kit
        self.skin = skin
        self.ref = weakref.ref(window)
        self.nextDate = None
        x, y, w, h = EVENTS_BOX
        cx = x + w // 2
        title_cell, hint_cell = kit.cell('text_b'), kit.cell('text_s')
        top = y + (h - (title_cell + 6 + hint_cell + 12 + T.BTN_H_S)) // 2
        self.title = skin.Text(cx, top, localeInfo.EVENT_CALENDAR_EMPTY_DAY, role='text_b', color=T.IVORY,
                               align='center', limit=590)
        self.hint = skin.Text(cx, top + title_cell + 6, _Tr('Tento den se nic nekoná.', 'Nothing happens on this day.'),
                              color=T.INK_DIM, align='center', limit=590)
        self.buttonY = top + title_cell + 6 + hint_cell + 12
        self.button = skin.Own(uir1.Button(window, kit, cx - 100, self.buttonY, 200, '', small=True,
                                           event=_Call(self.SelectNext)))
        self.shown = True
        self.Hide()

    @property
    def window(self):
        return self.ref()

    def NextDayWithEvents(self):
        """The first later day (within the calendar's allowed range) that has an event, else None."""
        import datetime
        window, g = self.window, self.skin.names
        logic = g['eventcalendarlogic']
        rows = [row for dayRows in g['server_event_data'].values() for row in dayRows.values()]
        if not rows:
            return None
        day = datetime.date(*window.selectedDate)
        for unused in range(self.SEARCH_DAYS):
            day += datetime.timedelta(days=1)
            key = (day.year, day.month, day.day)
            if not logic.IsDateAllowed(key, window.anchorDate):
                return None
            if logic.EventsForDay(rows, key, g['EVENT_START_TIME'], g['EVENT_END_TIME']):
                return key
        return None

    def Show(self):
        import datetime
        import localeInfo
        self.shown = True
        for widget in (self.skin.columnLine, self.skin.detailLine):
            if widget is not None:
                widget.Hide()
        self.title.Show()
        self.hint.Show()
        self.nextDate = self.NextDayWithEvents()
        if self.nextDate is None:
            self.button.Hide()
            return
        day = datetime.date(*self.nextDate)
        label = localeInfo.EVENT_CALENDAR_WEEK_DATE % (
            getattr(localeInfo, 'EVENT_CALENDAR_WEEKDAY_%d' % day.weekday()), day.day, day.month)
        text = _Tr('Další den s událostmi: %s >' % label, 'Next day with events: %s >' % label)
        if self.button.GetText() != text:
            self.button.SetText(text)
            width = self.button.FitWidth(160, 14)
            self.button.SetPosition(EVENTS_BOX[0] + (EVENTS_BOX[2] - width) // 2, self.buttonY)
        self.button.Show()

    def Hide(self):
        self.shown = False
        for widget in (self.title, self.hint, self.button):
            widget.Hide()
        for widget in (self.skin.columnLine, self.skin.detailLine):
            if widget is not None:
                widget.Show()

    def IsShow(self):
        return self.shown

    def SelectNext(self):
        if self.nextDate is not None and self.window is not None:
            self.window.SelectDate(self.nextDate)


class CalendarSkin(object):
    """Builds the whole content of the calendar in the R1 look into the window (instead of the original
    __BuildWindow). Every widget it makes is added to window.children, like the original ones."""

    def __init__(self, window, names):
        self.ref = weakref.ref(window)
        self.names = names
        self.kit = uir1.Kit()
        self.variant = WEEK_VARIANT if WEEK_VARIANT in WEEK else 1
        self.hidden = []
        self.chrome = None
        self.titleVein = None
        self.columnLine = self.detailLine = None

    @property
    def window(self):
        return self.ref()

    def Own(self, widget):
        self.window.children.append(widget)
        return widget

    def Text(self, x, y, text='', role='text_s', color=T.INK, align='left', valign='top', limit=None, font=None):
        return self.Own(uir1.Text(self.window, text, x, y, font or self.kit.font(role), color, align, valign,
                                  limit=limit))

    def Image(self, x, y, path):
        image = ui.ExpandedImageBox()
        image.SetParent(self.window)
        image.AddFlag('not_pick')
        image.SetPosition(x, y)
        image.LoadImage(path)
        image.Show()
        return self.Own(image)

    def HideOriginalChrome(self, window):
        board = [getattr(window, 'Base', None), getattr(window, 'titleArt', None), window.titleName,
                 window.titleBar.btnClose] + list(getattr(window, 'Corners', [])) + list(getattr(window, 'Lines', []))
        for widget in board:
            if widget is not None:
                widget.Hide()
                self.hidden.append(widget)

    def Build(self, window):
        g, kit = self.names, self.kit
        self.chrome = uir1.Chrome(window, kit, WIDTH, HEIGHT, _Tr(TITLE, 'Event calendar'), on_close=_Call(window.Close))
        self.HideOriginalChrome(window)
        for widget in self.chrome.Widgets():
            self.Own(widget)
        art = g['DAY_VIEW_ART']
        # header row: calendar picture, the date, the day count
        self.Image(16, 37, art + 'calendar_24.png')
        window.dateTitle = self.Text(50, 49 - kit.cell('text_b') // 2, role='text_b', color=T.IVORY, limit=350)
        window.dayCount = self.Text(WIDTH - 16, 49 - kit.cell('text_s') // 2, color=T.INK_DIM, align='right', limit=210)
        window.GetEventCount = CountWords        # "5 událostí" in the header and the week strip
        window.GetEventMetadata = _Metadata(window.GetEventMetadata)
        window.EventOrder = _Order(window.GetEventState, g['EVENT_START_TIME'], g['EVENT_ID'])
        # week strip
        geo = WEEK[self.variant]
        window.previousWeek = self.Own(ArrowButton(window, kit, ARROW_X[0], geo['arrow_y'], 'left',
                                                   _Call(window._EventCalendarWindow__ChangeWeek, -1)))
        window.nextWeek = self.Own(ArrowButton(window, kit, ARROW_X[1], geo['arrow_y'], 'right',
                                               _Call(window._EventCalendarWindow__ChangeWeek, 1)))
        for index in range(g['CALENDAR_LAYOUT']['week_days']):
            day = WeekDay(window, kit, self.variant)
            day.SetPosition(WEEK_X + index * WEEK_PITCH, geo['y'])
            window.weekDays.append(self.Own(day))
        self.Own(uir1.Divider(window, 16, 127, 619))
        # the day's events: a dark panel, two columns of five rows
        x, y, w, h = EVENTS_BOX
        self.Own(uir1.Frame(window, x, y, w, h, 'panel'))
        self.columnLine = self.Own(uir1.Rect(window, 325, 144, 1, 272, T.LINE))
        layout = g['CALENDAR_LAYOUT']
        per_column = layout['rows_per_column']
        row_class = MakeEventRowClass(g['CalendarEventRow'])
        for index in range(layout['page_size']):
            row = row_class(window, window, kit, divider=index % per_column != per_column - 1)
            row.SetPosition(layout['row_origin'][0] + (index // per_column) * layout['column_pitch'],
                            layout['row_origin'][1] + (index % per_column) * window.ROW_PITCH)
            row.Hide()
            window.eventRows.append(self.Own(row))
        import localeInfo
        window.emptyDay = EmptyDay(self, window)      # the window's Refresh shows it on a day without events
        # detail of the selected event
        x, y, w, h = DETAIL_BOX
        self.Own(uir1.Frame(window, x, y, w, h, 'panel'))
        window.detailIcon = self.Image(29, 446, art + 'icons/bonus_event_45.png')
        window.detailTitle = self.Text(90, 439, role='text_b', color=T.IVORY, limit=340)
        self.titleVein = uir1.Vein(window.detailTitle, 0, 22, 180)    # hidden with the title (no event)
        window.detailDescription = self.Text(90, 467, limit=334)
        window.detailDescription2 = self.Text(90, 485, limit=334)
        window.detailMeasure = self.Text(0, 0)
        window.detailMeasure.Hide()
        window.detailBonus = self.Text(90, 513, role='text_sb', color=g['TIME_TEXT_COLOR'], limit=334)
        cx, cw = DETAIL_COLUMN
        self.detailLine = self.Own(uir1.Rect(window, cx - 14, 444, 1, 92, T.LINE))
        window.detailStatus = self.Text(cx, 439, role='text_sb', limit=cw)
        window.detailClock = self.Image(cx - 1, 467, art + 'clock_20.png')
        window.detailStart = self.Text(cx + 25, 468, limit=cw - 25)
        window.detailCountdown = self.Text(cx, 494, color=T.INK_DIM, limit=cw)
        # "Všechna království | všechny kanály" (CleanMetadata) fits the column only in the small size (14 px)
        window.detailMetadata = self.Text(cx, 521, color=T.MUTED, limit=cw,
                                          font=Sized(kit.font('text_s'), kit.cell('text_s') - 2))
        window.infoButton = self.HitArea(90, 467, 334, 36, window._EventCalendarWindow__ShowSelectedTooltip,
                                         localeInfo.EVENT_CALENDAR_DETAILS)
        window.actionButton = self.HitArea(29, 446, 45, 45, window._EventCalendarWindow__ActivateSelected,
                                           localeInfo.EVENT_CALENDAR_OPEN_EVENT)
        # footer: previous day, today (the main action), next day, paging between them
        window.previousButton = self.Button(16, DAY_W, localeInfo.EVENT_CALENDAR_PREVIOUS_DAY,
                                            _Call(window._EventCalendarWindow__ChangeDay, -1))
        window.todayButton = self.Button(TODAY_X, TODAY_W, '', _Call(window._EventCalendarWindow__SelectToday),
                                         primary=True)
        window.nextButton = self.Button(WIDTH - 16 - DAY_W, DAY_W, localeInfo.EVENT_CALENDAR_NEXT_DAY,
                                        _Call(window._EventCalendarWindow__ChangeDay, 1))
        window.previousPage = self.Own(ArrowButton(window, kit, PAGER['prev'][0], PAGER['prev'][1], 'left',
                                                   _Call(window._EventCalendarWindow__ChangePage, -1)))
        window.nextPage = self.Own(ArrowButton(window, kit, PAGER['next'][0], PAGER['next'][1], 'right',
                                               _Call(window._EventCalendarWindow__ChangePage, 1)))
        window.pageLabel = self.Text(PAGER['label'][0], FOOTER_Y + uir1.CellTop(T.BTN_H, kit.font('text_s')),
                                     color=T.INK_DIM, align='center', limit=PAGER_LABEL_W)

    def Button(self, x, w, text, event, primary=False):
        button = self.Own(uir1.Button(self.window, self.kit, x, FOOTER_Y, w, text, primary=primary, event=event))
        button.calendarLabel = button.label        # the window's Refresh writes "Dnes | 14:32" into it
        return button

    def HitArea(self, x, y, w, h, method, tooltip):
        button = ui.Button()
        button.SetParent(self.window)
        button.SetPosition(x, y)
        button.SetSize(w, h)
        button.SetEvent(ui.__mem_func__(method))
        button.SetToolTipText(tooltip)
        button.Show()
        return self.Own(button)

    def Abort(self):
        """Undo the R1 build: what it made is hidden, the original board chrome is shown again."""
        for widget in self.hidden:
            widget.Show()
        self.hidden = []
        if self.chrome is not None:
            self.chrome.Hide()
        self.chrome = None
        window = self.window
        if window is not None:
            window.__dict__.pop('GetEventCount', None)
            window.__dict__.pop('GetEventMetadata', None)
            window.__dict__.pop('EventOrder', None)


def Build(window, names):
    """Builds the R1 calendar into ``window`` (``names`` = the globals of uieventcalendar) and returns the skin, or
    None after a traced failure: then everything R1 made is gone and the caller builds the original window."""
    global _failed
    start = len(window.children)
    skin = CalendarSkin(window, names)
    try:
        skin.Build(window)
        return skin
    except Exception:
        _failed = True
        uir1.TraceFailure('Kalendář událostí')
        for widget in window.children[start:]:
            try:
                widget.Hide()
            except Exception:
                pass
        del window.children[start:]
        skin.Abort()
        return None
