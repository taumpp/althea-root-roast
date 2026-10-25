# -*- coding: utf-8 -*-
"""The switchbot's attribute picker ("Vybrat atribut", uiswitchbot.SearchListWindow) in the R1 look ("Krvavá žíla",
docs/ALTHEA_R1_KIT.md), drawn INTO the original window. Both callers use it: the bonus rows of the switchbot and
Instaswitchbot.

The window keeps its size (340 x 260), its flags, its search (the same edit line: every key filters the list through
the window's own IME hook, Enter accepts, Esc closes), the list (the same ui.ListBoxEx: the window's own refresh,
scroll steps, selection and accept / cancel handlers) and every caller callback. This module only re-skins it:

* the R1 frame and header (Cinzel title, vein, plain X = the window's Close) on the board; the original title bar
  stays as the invisible drag handle;
* the search as an R1 search field around the window's own edit line (magnifier, the clear X while there is text);
* the list in a dark R1 panel; rows 18 px with Spectral text (top-aligned at CellTop), hover = the lighter band,
  the selected row = the dark band with the red line, an attribute that cannot be chosen greyed with its reason;
* the narrow R1 scroll bar (the list's scroll events and the mouse wheel as before);
* Přijmout (primary, on the left) and Zrušit as R1 buttons calling the window's own cancel / accept.

Rows are created again on every search (the window's design): an R1 row keeps no reference back to itself (no
reference cycle, so a replaced row is freed and its engine window destroyed), and a replaced row is hidden.
Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr, restores the
original window and the R1 look is not tried again in this session.
"""
import weakref

import ui

import uir1
import uir1tokens as T

WINDOW = u'Switchbot - výběr atributu'
ROW_H = 18                 # list row (Spectral 16 cell + 2)
ROW_X = 8                  # row text inset
PAD = 8                    # the original BORDER_SPACE: list and field inset, kept for the window's own resizes
FIELD_Y = 31               # the search field under the header (HEAD_H 27 + the vein)
LIST_GAP = 5               # field -> list panel
BUTTON_W, BUTTON_GAP = 110, 10
BOTTOM = 12                # buttons -> window bottom
BUTTON_TOP_GAP = 8         # list panel -> buttons
SCROLL_GAP = 4             # list panel -> scroll bar (the window keeps 16 px for the bar)
BAND_W = 200               # a row band is made this wide (every image of its red line exists), then resized

_failed = []


def UseR1():
    return not _failed and uir1.UseR1()


def _Tr(czech, english):
    return uir1.Tr_(czech, english)


def RowClass(original):
    """The R1 row class for one window: the original SearchListItem's behaviour (key, value, enabled, the click that
    selects, Down / SetUp / IsDown, GetText, MatchText) with an R1 face. ``rows`` holds the rows made, weakly."""

    class Row(original):
        LIST_ITEM_HEIGHT = ROW_H
        DISABLED_COLOR = T.DISABLED
        rows = weakref.WeakSet()
        kit = None

        def __init__(self, key, value, enabled=True, note=''):
            ui.Window.__init__(self)
            self.key = key
            self.value = value
            self.enabled = enabled
            self.isDown = False
            self.onClickEvent = None
            self.state = None
            kit = Row.kit or uir1.Kit()
            Row.kit = kit
            self.font = kit.font('text_s')
            # The band first (under the text). It keeps no reference to this row: rows are re-created on every
            # search and a cycle through an object with __del__ is never freed (its window would stay drawn).
            self.band = uir1.Band(self, 0, 0, BAND_W, ROW_H - 1)   # wide: all line images made now
            self.band.parent = None
            self.band.line.parent = None
            self.textLine = uir1.RowText(self, str(value) + (' (%s)' % note if note else ''), ROW_X, ROW_H,
                                         self.font, T.INK if enabled else T.DISABLED)
            Row.rows.add(self)

        def SetSize(self, width, height):
            ui.Window.SetSize(self, width, height)
            self.band.Resize(0, 0, max(1, int(width)), ROW_H - 1)

        def State(self):
            if self.isDown:
                return 'selected'
            if self.enabled and self.IsIn():
                return 'hover'
            return 'normal'

        def Paint(self):
            state = self.State()
            if state == self.state:
                return
            self.state = state
            self.band.SetState(state)
            if self.enabled:
                self.textLine.SetPackedFontColor(T.IVORY if state == 'selected' else T.INK)

        def OnRender(self):
            self.Paint()

        def OnMouseOverIn(self):
            self.Paint()

        def OnMouseOverOut(self):
            self.Paint()

        def SetUp(self):
            original.SetUp(self)
            self.Paint()

        def Down(self):
            original.Down(self)
            self.Paint()

    return Row


class SearchSkin(object):
    """R1 into one SearchListWindow (after MakeWindow). Build failure: Undo() and re-raise."""

    def __init__(self, window):
        # weakly: the window holds this skin (window.r1); a cycle through ui.Window (__del__) is never freed
        self.window = weakref.proxy(window)
        self.kit = uir1.Kit()
        self.undo = []
        self.board = None
        try:
            self._Build(window)
        except Exception:
            self.Undo()
            raise
        # built: nothing to undo any more (the window is re-created for every search); drop the strong references
        self.undo = []
        self.board.board = None

    def _Keep(self, undo):
        self.undo.append(undo)

    def _Build(self, w):
        kit = self.kit
        width, height = w.GetWidth(), w.GetHeight()
        title = w.titleName.GetText() if getattr(w, 'titleName', None) is not None else ''
        self.board = uir1.BoardSkin(w, kit, title or _Tr(u'Vybrat atribut', 'Select the attribute'),
                                    on_close=ui.__mem_func__(w.Close))
        self._Keep(self.board.Restore)
        uir1.Front(w)               # 'float': a click on it brings it in front of the switchbot again
        # the search: the window's own edit line in the R1 field (its IME / Enter / Esc hooks stay)
        edit, holder = w.searchEditLine, w.searchInput
        position, size = edit.GetLocalPosition(), (edit.GetWidth(), edit.GetHeight())
        holder.Hide()

        def back_edit():
            holder.Show()
            edit.SetParent(holder)
            edit.SetPosition(*position)
            edit.SetSize(*size)
            text = edit.GetText()
            edit.SetText('')
            edit.SetDefaultFontName()
            edit.SetText(text)
        self._Keep(back_edit)
        self.field = uir1.SearchField(w, kit, PAD, FIELD_Y, width - 2 * PAD, edit=edit, max_len=50,
                                      on_search=self._Refresh, on_clear=self._Refresh, font=kit.font('text_s'))
        self._Keep(self.field.Hide)
        # the list: the same container, list box and refresh; R1 rows, the R1 panel and the R1 scroll bar
        container, box = w.container, w.listBox
        top = FIELD_Y + T.FIELD_H + LIST_GAP
        self.list_h = height - top - BOTTOM - T.BTN_H - BUTTON_TOP_GAP
        cpos, csize = container.GetLocalPosition(), (container.GetWidth(), container.GetHeight())
        original_row = w.SearchListItem
        w.SearchListItem = self.Row = RowClass(original_row)

        def back_list():
            w.__dict__.pop('SearchListItem', None)
            container.SetPosition(*cpos)
            container.SetSize(*csize)
            box.SetItemStep(original_row.LIST_ITEM_HEIGHT)
            box.SetViewItemCount(csize[1] // original_row.LIST_ITEM_HEIGHT)
        self._Keep(back_list)
        container.SetPosition(PAD, top)
        container.SetSize(container.GetWidth(), self.list_h)
        self.panel = uir1.BoardSkin(container, kit, kind='panel')
        self._Keep(self.panel.Restore)
        box.SetItemStep(ROW_H)
        box.SetViewItemCount((self.list_h - 4) // ROW_H)
        old_bar = w.scrollBar
        self.scroll = uir1.ScrollBar(kit)
        self.scroll.SetParent(w)
        self.scroll.SetPosition(width - PAD - 16 + SCROLL_GAP, top + 2)
        self.scroll.SetScrollBarSize(self.list_h - 4)
        w.scrollBar = self.scroll
        box.SetScrollBar(self.scroll)
        old_bar.Hide()

        def back_bar():
            self.scroll.Hide()
            w.scrollBar = old_bar
            box.SetScrollBar(old_bar)
        self._Keep(back_bar)
        # the buttons: Přijmout (the main action on the left), Zrušit
        x = (width - 2 * BUTTON_W - BUTTON_GAP) // 2
        y = height - BOTTOM - T.BTN_H
        accept, cancel = w.acceptButton, w.cancelButton
        self.accept = uir1.Button(w, kit, x, y, BUTTON_W,
                                  accept.GetText() or _Tr(u'Přijmout', 'Accept'), primary=True,
                                  event=ui.__mem_func__(getattr(w, '_SearchListWindow__OnAccept')))
        self.cancel = uir1.Button(w, kit, x + BUTTON_W + BUTTON_GAP, y, BUTTON_W,
                                  cancel.GetText() or _Tr(u'Zrušit', 'Cancel'),
                                  event=ui.__mem_func__(getattr(w, '_SearchListWindow__OnCancel')))
        for button in (accept, cancel):
            button.Hide()
            self._Keep(button.Show)
        self._Keep(self.cancel.Hide)
        self._Keep(self.accept.Hide)
        self._Refresh()

    # ------------------------------------------------------------------ hooks of the window
    def _Refresh(self):
        refresh = getattr(self.window, '_SearchListWindow__RefreshListBox', None)
        if refresh is not None:
            refresh()

    def SetTitle(self, title):
        if self.board is not None:
            self.board.SetTitle(title)

    def Sync(self):
        """After the window laid its list out (SearchListWindow.__AdjustScrollbar: the panel narrows by the scroll
        bar's room while the list scrolls): the R1 panel follows, rows no longer in the list are hidden."""
        w = self.window
        self.panel.Resize(w.container.GetWidth(), w.container.GetHeight())
        current = set(id(row) for row in w.listBox.GetItems())
        for row in list(self.Row.rows):
            if id(row) not in current and row.IsShow():
                row.Hide()

    def Undo(self):
        for step in reversed(self.undo):
            try:
                step()
            except Exception:
                pass
        self.undo = []


def Build(window):
    """The R1 skin of a SearchListWindow (after MakeWindow) or None (Starý vzhled, or the build failed: traced, the
    original window kept, not tried again in this session)."""
    if not UseR1():
        return None
    try:
        return SearchSkin(window)
    except Exception:
        _failed.append(1)
        uir1.TraceFailure(WINDOW)
        return None
