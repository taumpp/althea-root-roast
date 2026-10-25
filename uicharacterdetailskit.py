# -*- coding: utf-8 -*-
"""The character window's side panel "Bonusy" / "Statistiky" in the Althea R1 look (docs/ALTHEA_R1_KIT.md).

uicharacterdetails.CharacterDetailsUI keeps the window (247 x 405 next to the character window, the uiscript
layout, the bonus and kill tables, the row tooltip) and draws this panel INTO it, as uiescmenu does for the ESC
menu, unless Settings -> "Starý vzhled" chose the original look (settingslook 'legacy'). A build failure keeps
the original panel (traced to syserr). The functions stay those of the original panel:

  tabs        Bonusy | Statistiky (the window's SetCategory), the search loses the focus on a switch
  search      live filter over the bonus names: a flat list of the matching rows, scrolled back to the top;
              case and Czech accents are ignored (textcase.SearchKey: "ve", "vě", "VĚ" all find "Síla větru")
  sections    PVM / PVP / Útočné / Obranné atributy, all collapsed at first; a click on the heading toggles one
  scrolling   the scrollbar and the mouse wheel over the bonus list
  rows        bonus name (first letter upper case) + the player's value (player.GetStatus) read on every
              Refresh; the full name as the row tooltip (the label takes the room the value leaves; only a name
              longer than that is shortened with "..." in the row, the search sees the full name)
  statistics  the six kill counters (player.GetKillLOG, dotted numbers)
  sources     a click on a bonus row unfolds "odkud bonus mám" right under it (uibonussources.Cascade over
              ``sources(bonus)`` -> bonussources.Breakdown): the rows below move down, a second click folds it; the
              open row keeps the selected band; a hover on an equipment source shows that item's tooltip
              (``item_in(cell)`` / ``item_out()``)

ONE panel for both tabs: the tab switch only shows the other page, the window rectangle never
changes. The statistics rows are the bonus rows (ROW_H, the same label / value fonts, the same left edge, label
column and value column) in the same list frame under the tabs.

* Look: the R1 window frame (graphite, the bronze hairline; the panel has no header of its own), the R1 tab row
  (the selected tab is a dark well with the red line under it, not a red plate), the R1 search field (magnifier,
  clear X), section headings with a chevron (right = collapsed, down = expanded) and a fading hairline, rows with
  the label on the left and the value right-aligned in one column in ivory (a zero value muted), a fine graphite
  row line and the hover band, the narrow R1 scroll bar; Noto Sans via uir1.Kit() (Tahoma only as the automatic
  fallback of an old EXE).
* The window is PANEL_W x 405 (the height of the character window) on every screen and in both tabs: wide enough
  for the common bonus names in one row (a longer one keeps "..." and its full name in the row tooltip).
"""
import ui
from _weakref import proxy

import textcase
import uikit
import uir1
import uir1tokens as T

PAD = 12                # frame edge -> content
TAB_GAP = 10            # tabs -> search field / statistics
FIELD_GAP = 8           # search field -> list
HEAD_H = 28             # section heading row
ROW_H = 26              # bonus row and statistics row (one row style in both tabs)
PANEL_W = 320           # the panel width in both tabs (the original uiscript board is 247)
SECTION_GAP = 4         # space after an expanded section
INDENT = 16             # chevron + gap; the row labels start under the heading text
VALUE_X = 6             # value column: right-aligned this far from the row's right edge
VALUE_GAP = 8           # label end -> value start
WHEEL_ROWS = 3          # rows per mouse wheel step
LABEL_FONT = 'text'
VALUE_FONT = 'text_b'
ROW_LINE_ALPHA = 0.55   # the graphite row line, quieter than a divider
ELLIPSIS = '...'


def UseKitLook():
    """The R1 panel unless Settings -> "Starý vzhled" chose the original look (settingslook 'legacy')."""
    return uir1.UseR1()


def _Tr(czech, english):
    try:
        from settingslocale import Text
        return Text(czech, english)
    except Exception:
        return czech


def Fit(line, text, width):
    """Sets ``text`` on ``line``, shortened with "..." to ``width`` px; returns the shown text."""
    return uir1.Fit(line, text, width, ELLIPSIS)


class Row(uikit.HitArea):
    """Label left, value right-aligned in the value column, a fine row line; the hover band and the row tooltip
    (``on_in(name)`` / ``on_out()``) while the mouse is on it."""

    def __init__(self, parent, kit, w, h, name, indent=INDENT, on_in=None, on_out=None, label_font=LABEL_FONT,
                 value_font=VALUE_FONT):
        uikit.HitArea.__init__(self, parent, 0, 0, w, h)
        self.name = name
        self.on_in, self.on_out = on_in, on_out
        # Children draw in creation order: band under the texts, the row line last.
        self.band = uir1.Band(self, 0, 0, w, h - 1)
        # Top-aligned cells centred by position (uir1.RowText): the whole text cell stays inside the row.
        self.label = uir1.RowText(self, '', indent, h, kit.font(label_font), T.INK)
        self.value = uir1.RowText(self, '0', w - VALUE_X, h, kit.font(value_font), T.IVORY, align='right')
        self.line = uikit.HLine(self, 0, h - 1, w, T.LINE, ROW_LINE_ALPHA)
        self.w, self.indent, self.room = w, indent, None
        self.selected = False
        self.shown = name.strip()
        self._FitLabel()
        self.Hide()

    def _FitLabel(self):
        """The label gets the row width the value leaves (most values are short): "..." only when it still does not
        fit; refitted when the value width changes."""
        room = self.w - self.indent - VALUE_X - uikit.TextWidth(self.value) - VALUE_GAP
        if room != self.room:
            self.room = room
            self.shown = Fit(self.label, self.name.strip(), room)

    def SetValue(self, text):
        text = str(text)
        if text != self.value.GetText():
            self.value.SetText(text)
            self._FitLabel()
        self.value.SetPackedFontColor(T.MUTED if text.rstrip('%') in ('0', '0.0', '--') else T.IVORY)

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def paint(self):
        self.band.SetState('selected' if getattr(self, 'selected', False) else
                           'hover' if self.hovered else 'normal')

    def OnMouseOverIn(self):
        uikit.HitArea.OnMouseOverIn(self)
        if self.on_in:
            self.on_in(self.name)

    def OnMouseOverOut(self):
        uikit.HitArea.OnMouseOverOut(self)
        if self.on_out:
            self.on_out()


class Heading(uikit.HitArea):
    """Collapsible section heading: chevron (right = collapsed, down = expanded) and the R1 section heading
    (text_sb + the fading hairline); a click toggles the section."""

    def __init__(self, parent, kit, w, title, event):
        uikit.HitArea.__init__(self, parent, 0, 0, w, HEAD_H)
        self.kit = kit
        self.expanded = False
        self.band = uir1.Band(self, 0, 2, w, HEAD_H - 4)
        cs = T.CHEVRON
        self.chevron = uir1.Image(self, uir1.ChevronPath('right'), 2, (HEAD_H - cs) // 2)
        self.section = uir1.Section(self, kit, INDENT, 0, w - INDENT, title)
        self.section.SetPosition(INDENT, (HEAD_H - self.section.Height()) // 2)
        self.title = title
        self.callback = event
        self.Hide()

    def SetExpanded(self, expanded):
        self.expanded = bool(expanded)
        self.paint()

    def paint(self):
        state = 'active' if self.hovered else 'normal'
        shape = 'down' if self.expanded else 'right'
        self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath(shape, state))
        self.section.label.SetPackedFontColor(T.IVORY if self.hovered or self.expanded else T.INK_DIM)
        self.band.SetState('hover' if self.hovered else 'normal')


class BonusPanel(ui.Window):
    """The panel inside ``owner`` (CharacterDetailsUI). ``spec``: tabs (two labels), sections [(title,
    [(name, point)])], stats [(label, kind)], value(point) -> number, stat(kind) -> text, and the callbacks close(),
    row_in(name), row_out()."""

    def __init__(self, owner, spec):
        ui.Window.__init__(self)
        self.owner = owner
        self.spec = dict(spec)
        self.kit = uir1.Kit()
        self.tab = 0
        self.query = ''
        self.offset = 0
        self.content_h = 0
        self.cascade = None
        self.cascade_row = None
        self.SetParent(owner)
        self.AddFlag('not_pick')
        self.SetPosition(0, 0)
        self.W, self.H = int(owner.GetWidth()), int(owner.GetHeight())
        self.SetSize(self.W, self.H)      # the owner's rectangle (CharacterDetailsUI sizes it to PANEL_W x 405)
        try:
            self._Build()
        except Exception:
            self.Hide()          # a half-built panel must not cover the original one the owner falls back to
            raise
        self.Show()

    # ------------------------------------------------------------------ build
    def _Build(self):
        k, W, H = self.kit, self.W, self.H
        iw = W - 2 * PAD
        self.iw = iw
        # Frame first: everything else draws above it.
        self.frame = uir1.Frame(self, 0, 0, W, H, 'window')
        tabs = self.spec['tabs']
        self.tabs = uir1.Segment(self, k, [(0, tabs[0]), (1, tabs[1])], event=self.SetTab, width=iw)
        sh = T.SEG_H
        self.tabs.SetPosition(PAD, PAD)
        self.tabs.SetValue(0)
        top = PAD + sh + TAB_GAP
        self.top = top

        # Bonus page: search field, clipped list, scrollbar.
        self.bonus_page = self._Page()
        self.search = uir1.SearchField(self.bonus_page, k, PAD, top, iw, hint=_Tr('Hledat bonus...', 'Search bonus...'),
                                       on_clear=self._OnSearchCleared)
        edit = self.search.edit
        edit.OnIMEUpdate = self._OnSearchInput
        if self.spec.get('close'):
            edit.SetEscapeEvent(self.spec['close'])
        vy = top + self.search.h + FIELD_GAP
        self.view_h = H - PAD - vy
        self.scrollbar = uir1.ScrollBar(k)
        sw = self.scrollbar.Width()
        self.view_w = iw - sw - 2
        self.viewport = ui.Window()
        self.viewport.SetParent(self.bonus_page)
        self.viewport.SetPosition(PAD, vy)
        self.viewport.SetSize(self.view_w, self.view_h)
        self.viewport.EnableScissorRect()
        self.viewport.OnMouseWheel = self.OnMouseWheel
        self.viewport.Show()
        self.content = ui.Window()
        self.content.SetParent(self.viewport)
        self.content.SetPosition(0, 0)
        self.content.SetSize(self.view_w, self.view_h)
        self.content.OnMouseWheel = self.OnMouseWheel
        self.content.Show()
        self.scrollbar.SetParent(self.bonus_page)
        self.scrollbar.SetPosition(PAD + iw - sw, vy)
        self.scrollbar.SetScrollBarSize(self.view_h)
        self.scrollbar.SetScrollEvent(self._OnScroll)
        self.scrollbar.OnMouseWheel = self.OnMouseWheel
        self.scrollbar.middleBar.OnMouseWheel = self.OnMouseWheel
        self.scrollbar.Hide()
        self.headings, self.rows = [], []
        row_in, row_out = self.spec.get('row_in'), self.spec.get('row_out')
        sources = self.spec.get('sources')
        for index, (title, entries) in enumerate(self.spec['sections']):
            heading = Heading(self.content, k, self.view_w, title, lambda index=index: self.ToggleSection(index))
            heading.SetWheelEvent(self.OnMouseWheel)
            self.headings.append(heading)
            rows = []
            for name, point in entries:
                # Every name with a capital first letter ("Šance odrazit ...": the value-first tooltip strings).
                row = Row(self.content, k, self.view_w, ROW_H, textcase.CapitalFirst(name.strip()), on_in=row_in,
                          on_out=row_out)
                row.point = point
                if sources:
                    row.SetEvent(lambda row=row, owner=proxy(self): owner.ToggleSources(row))
                row.SetWheelEvent(self.OnMouseWheel)
                rows.append(row)
            self.rows.append(rows)
        self.empty = uikit.Text(self.content, _Tr('Žádný bonus neodpovídá hledání.', 'No bonus matches the search.'),
                                self.view_w // 2, 8, k.font('text_s'), T.MUTED, align='center', valign='top')
        self.empty.Hide()

        # Statistics page: the kill counters as bonus rows (same width, height, fonts and columns as the list).
        self.stat_page = self._Page()
        self.stat_rows = []
        y = top
        for label, kind in self.spec['stats']:
            row = Row(self.stat_page, k, self.view_w, ROW_H, label)
            row.kind = kind
            row.SetPosition(PAD, y)
            row.Show()
            self.stat_rows.append(row)
            y += ROW_H
        self.stat_page.Hide()

    def _Page(self):
        page = ui.Window()
        page.SetParent(self)
        page.AddFlag('not_pick')
        page.SetPosition(0, 0)
        page.SetSize(self.W, self.H)
        page.Show()
        return page

    # ------------------------------------------------------------------ tabs
    def SetTab(self, index):
        self.tab = 1 if index == 1 else 0
        self.tabs.SetValue(self.tab)
        try:
            self.search.edit.KillFocus()
        except Exception:
            pass
        if self.tab == 0:
            self.bonus_page.Show()
            self.stat_page.Hide()
        else:
            self.bonus_page.Hide()
            self.stat_page.Show()
        self.Refresh()

    # ------------------------------------------------------------------ search / sections
    def _OnSearchInput(self):
        ui.EditLine.OnIMEUpdate(self.search.edit)
        self.search.SyncClear()
        self._Filter()

    def _OnSearchCleared(self):
        self._Filter()

    def _Filter(self):
        query = textcase.SearchKey(self.search.edit.GetText())   # "ve" / "VĚ" find "větru" (no case, no accents)
        if query:
            self.scrollbar.SetPos(0, False)      # a search starts at the top (as the original panel)
        self.query = query
        self.Layout()

    def ToggleSection(self, index):
        heading = self.headings[index]
        heading.SetExpanded(not heading.expanded)
        self.Layout()

    def Visible(self, row):
        visible = self.spec.get("visible")
        return visible(row.point) if visible else True

    def Matches(self, row):
        return self.query in textcase.SearchKey(row.name)

    # ------------------------------------------------------------------ layout / values
    def Layout(self):
        y = 0
        matches = 0
        if self.cascade is not None:
            self.cascade.Hide()        # shown again under its row if that row is placed
        for heading, rows in zip(self.headings, self.rows):
            if self.query:
                heading.Hide()
                for row in rows:
                    if self.Visible(row) and self.Matches(row):
                        row.SetPosition(0, y)
                        row.Show()
                        y += ROW_H
                        y = self._PlaceCascade(row, y)
                        matches += 1
                    else:
                        row.Hide()
                continue
            heading.SetPosition(0, y)
            heading.Show()
            y += HEAD_H
            for row in rows:
                if heading.expanded and self.Visible(row):
                    row.SetPosition(0, y)
                    row.Show()
                    y += ROW_H
                    y = self._PlaceCascade(row, y)
                else:
                    row.Hide()
            if heading.expanded:
                y += SECTION_GAP
        if self.query and not matches:
            self.empty.Show()
            y = max(y, uikit.FontCell(self.kit.font('text_s')) + 16)
        else:
            self.empty.Hide()
        self.content_h = y
        self.content.SetSize(self.view_w, max(self.view_h, y))
        scroll = y - self.view_h
        if scroll > 0:
            self.scrollbar.SetMiddleBarSize(float(self.view_h) / float(y))
            self.scrollbar.SetScrollStep(min(1.0, float(WHEEL_ROWS * ROW_H) / scroll))
            self.scrollbar.Show()
            self.scrollbar.SetPos(self.scrollbar.GetPos(), False)
        else:
            self.scrollbar.SetPos(0, False)
            self.scrollbar.Hide()
        self._OnScroll()

    def _OnScroll(self):
        scroll = max(0, self.content_h - self.view_h)
        self.offset = int(round(self.scrollbar.GetPos() * scroll)) if scroll else 0
        self.content.SetPosition(0, -self.offset)

    # ------------------------------------------------------------------ bonus sources (cascade under a row)
    def BonusRows(self):
        return [row for rows in self.rows for row in rows]

    def _PlaceCascade(self, row, y):
        cascade = self.cascade
        if cascade is None or row is not self.cascade_row:
            return y
        cascade.SetPosition(0, y)
        cascade.Show()
        return y + cascade.Height()

    def _Breakdown(self, row):
        return self.spec['sources'](row.point)

    def ToggleSources(self, row):
        """Unfold the sources of ``row`` under it; a second click on the open row folds them."""
        if self.cascade_row is row:
            self.CloseSources()
            return
        if self.cascade is None:
            import uibonussources
            self.cascade = uibonussources.Cascade(self.content, self.kit, self.view_w, on_resize=self._OnCascadeResize,
                                                  wheel=self.OnMouseWheel, item_in=self.spec.get('item_in'),
                                                  item_out=self.spec.get('item_out'))
        self.cascade.Reset()
        if self.cascade_row is not None:
            self.cascade_row.SetSelected(False)
        self.cascade_row = row
        row.SetSelected(True)
        self.cascade.SetContent(self._Breakdown(row))
        self.Layout()
        self._Reveal(row)

    def CloseSources(self):
        if self.cascade_row is not None:
            self.cascade_row.SetSelected(False)
        self.cascade_row = None
        if self.cascade is not None:
            self.cascade.Hide()
        out = self.spec.get('item_out')
        if out:
            out()
        self.Layout()

    def _OnCascadeResize(self):
        self.Layout()
        if self.cascade_row is not None:
            self._Reveal(self.cascade_row)

    def _Reveal(self, row):
        """Scroll so that the open row and as much of its cascade as fits are in view."""
        scroll = self.content_h - self.view_h
        if scroll <= 0 or not row.IsShow():
            return
        top = row.y if hasattr(row, 'y') else row.GetLocalPosition()[1]
        bottom = top + ROW_H + (self.cascade.Height() if self.cascade is not None else 0)
        offset = self.offset
        if bottom > offset + self.view_h:
            offset = bottom - self.view_h
        if top < offset or bottom - top > self.view_h:
            offset = top
        offset = max(0, min(scroll, offset))
        if offset != self.offset:
            self.scrollbar.SetPos(float(offset) / scroll, False)
            self._OnScroll()

    def Refresh(self):
        value, stat = self.spec.get('value'), self.spec.get('stat')
        for rows in self.rows:
            for row in rows:
                row.SetValue(value(row.point) if value else 0)
        if self.cascade_row is not None and self.cascade is not None:
            self.cascade.SetContent(self._Breakdown(self.cascade_row))
        for row in self.stat_rows:
            row.SetValue(stat(row.kind) if stat else 0)
        if self.tab == 0:
            self.Layout()

    def OnMouseWheel(self, delta):
        if self.tab == 0 and self.scrollbar.IsShow() and delta:
            self.scrollbar.OnUp() if delta > 0 else self.scrollbar.OnDown()
            return True
        return False

    # ------------------------------------------------------------------ teardown
    def Destroy(self):
        """Hide and break the callback cycles (row / heading -> lambda -> panel)."""
        self.Hide()
        for heading in self.headings:
            heading.callback = None
        for rows in self.rows:
            for row in rows:
                row.on_in = row.on_out = row.callback = None
        if self.cascade is not None:
            self.cascade.Destroy()
        self.cascade = self.cascade_row = None
        try:
            self.search.edit.KillFocus()
            del self.search.edit.OnIMEUpdate     # back to ui.EditLine's own handler
        except Exception:
            pass
        self.search.on_clear = None
        self.tabs.callback = None
        self.scrollbar.Destroy()
        self.frame.Destroy()
        self.headings, self.rows, self.stat_rows = [], [], []
        self.spec = {}
        self.owner = None
