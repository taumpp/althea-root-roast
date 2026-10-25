# -*- coding: utf-8 -*-
"""The switchbot's saved presets ("Uložené předvolby", uiswitchbot.ConfigurationWindow) in the R1 look ("Krvavá žíla",
docs/ALTHEA_R1_KIT.md), drawn INTO the original window like the attribute picker (root/uiswitchbotsearchr1.py).

The window keeps its size (250 x 430), its flags (it stays attached to the switchbot and is not movable), its name
line (the same edit line: Esc closes), its list (the same ui.ListBoxEx and the window's own LoadConfigurations /
scroll handling) and every handler (Uložit, Načíst, Vymazat). This module only re-skins it:

* the R1 frame and header (Cinzel title, vein, plain X = the window's Close) on the board; the original title bar
  stays as the invisible drag handle;
* the name as an R1 field around the window's own edit line, with the hint "Název předvolby", and Uložit as the
  primary R1 button beside it;
* the list in a dark R1 panel; a row is 24 px: the name in Noto Sans (shortened with "..." before the buttons),
  Načíst as a small R1 button, Vymazat as the clear X; the mouse over a row lights its band;
* the narrow R1 scroll bar (the list's scroll events and the mouse wheel as before);
* a quiet hint in the empty panel while no preset is saved.

Rows are created again on every LoadConfigurations (the window's design): an R1 row keeps no reference back to
itself (no reference cycle, so a replaced row is freed and its engine window destroyed), and a replaced row is
hidden. Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr, restores
the original window and the R1 look is not tried again in this session.
"""
import weakref

import localeInfo
import ui

import uir1
import uir1tokens as T

WINDOW = u'Switchbot - předvolby'
PAD = 8                    # the original BORDER_SPACE: list and field inset
FIELD_Y = 31               # the name field under the header (HEAD_H 27 + the vein)
SAVE_W = 76                # Uložit
GAP = 5                    # field -> Uložit, field -> list panel
ROW_H = 24                 # LIST_ITEM_HEIGHT of an R1 row (the window's list step is this + 1)
ROW_X = 8                  # row text inset
ROW_GAP = 6                # text -> buttons
LOAD_W = 62                # Načíst
BAND_W = 240               # a row band is made this wide, then resized with the row
SCROLL_GAP = 4             # list panel -> scroll bar (the window keeps 20 px for the bar)
BAND_PAD = 1

_failed = []


def UseR1():
    return not _failed and uir1.UseR1()


def _Tr(czech, english):
    return uir1.Tr_(czech, english)


def _Label(name, czech, english):
    return getattr(localeInfo, name, None) or _Tr(czech, english)


def RowClass(original):
    """The R1 row class for one window: the original ConfigurationLine's calls (Load, SetLoadEvent, SetDeleteEvent,
    the id and name) with an R1 face. ``rows`` holds the rows made, weakly."""

    class Row(original):
        LIST_ITEM_HEIGHT = ROW_H
        rows = weakref.WeakSet()
        kit = None

        def __init__(self, width):
            ui.Window.__init__(self)
            self.id = 0
            self.name = u''
            self.loadEvent = None
            self.deleteEvent = None
            self.state = None
            kit = Row.kit or uir1.Kit()
            Row.kit = kit
            self.font = kit.font('text_s')
            # The band first (under the texts). It keeps no reference to this row: rows are re-created on every
            # LoadConfigurations and a cycle through an object with __del__ is never freed.
            self.band = uir1.Band(self, 0, 0, BAND_W, ROW_H - BAND_PAD)
            self.band.parent = None
            self.band.line.parent = None
            self.nameLine = uir1.RowText(self, u'', ROW_X, ROW_H, self.font, T.INK)
            self.load = uir1.Button(self, kit, 0, 1, LOAD_W, _Label('SWITCHBOT_LOAD_CONFIGURATION', u'Načíst', 'Load'),
                                    small=True, event=ui.__mem_func__(self._OnLoad))
            hit = T.CLEAR + 8
            self.delete = uir1.Glyph(self, 'icon/clear_%s.png', 0, (ROW_H - hit) // 2, T.CLEAR,
                                     ui.__mem_func__(self._OnDelete), hit)
            self.delete.SetToolTipText(_Label('SWITCHBOT_CLEAR_CONFIGURATION', u'Vymazat', 'Delete'))
            self.SetSize(width, ROW_H)
            Row.rows.add(self)

        def SetSize(self, width, height):
            ui.Window.SetSize(self, width, height)
            self.band.Resize(0, 0, max(1, int(width)), ROW_H - BAND_PAD)
            hit = self.delete.GetWidth()
            self.delete.SetPosition(max(0, int(width) - 4 - hit), (ROW_H - hit) // 2)
            self.load.SetPosition(max(0, self.delete.GetLocalPosition()[0] - 2 - LOAD_W), 1)
            self._Fit()

        def Load(self, id, name):
            self.id = id
            self.name = name
            self._Fit()

        def _Fit(self):
            room = self.load.GetLocalPosition()[0] - ROW_GAP - ROW_X
            uir1.Fit(self.nameLine, self.name, max(1, room))

        def _OnLoad(self):
            if self.loadEvent:
                self.loadEvent(self.id)

        def _OnDelete(self):
            if self.deleteEvent:
                self.deleteEvent(self.id)

        def Paint(self):
            state = 'hover' if self.IsIn() else 'normal'
            if state == self.state:
                return
            self.state = state
            self.band.SetState(state)

        def OnRender(self):
            self.Paint()

        def OnMouseOverIn(self):
            self.Paint()

        def OnMouseOverOut(self):
            self.Paint()

    return Row


class PresetsSkin(object):
    """R1 into one ConfigurationWindow (after its __LoadWindow). Build failure: Undo() and re-raise."""

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

    def _Keep(self, undo):
        self.undo.append(undo)

    def _Build(self, w):
        kit = self.kit
        width, height = w.GetWidth(), w.GetHeight()
        title = w.titleName.GetText() if getattr(w, 'titleName', None) is not None else ''
        self.board = uir1.BoardSkin(w, kit, title or _Label('SWITCHBOT_CONFIGURATION_TITLE', u'Uložené předvolby',
                                                            'Saved presets'),
                                    on_close=ui.__mem_func__(w.Close))
        self._Keep(self.board.Restore)
        uir1.Front(w)               # 'float': a click on it brings it in front of the switchbot again
        # the name: the window's own edit line in the R1 field (its Esc hook stays), Uložit beside it
        edit, holder = w.nameEditLine, w.nameInput
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
        field_w = width - 2 * PAD - SAVE_W - GAP
        self.field = uir1.Field(w, kit, PAD, FIELD_Y, field_w, hint=_Tr(u'Název předvolby', 'Preset name'),
                                edit=edit, max_len=32, font=kit.font('text_s'))
        self._Keep(self.field.Hide)
        original_save = w.saveButton
        self.save = uir1.Button(w, kit, PAD + field_w + GAP, FIELD_Y - (T.BTN_H - T.FIELD_H) // 2, SAVE_W,
                                original_save.GetText() or _Label('SWITCHBOT_SAVE', u'Uložit', 'Save'),
                                primary=True, event=ui.__mem_func__(getattr(w, '_ConfigurationWindow__OnSave')))
        original_save.Hide()
        self._Keep(original_save.Show)
        self._Keep(self.save.Hide)
        # the list: the same container, list box and loading; R1 rows, the R1 panel and the R1 scroll bar
        container, box = w.container, w.listBox
        top = FIELD_Y + T.FIELD_H + GAP
        self.list_h = height - top - PAD
        cpos, csize = container.GetLocalPosition(), (container.GetWidth(), container.GetHeight())
        original_row = w.ConfigurationLine
        w.ConfigurationLine = self.Row = RowClass(original_row)

        def back_list():
            window = self.window
            window.__dict__.pop('ConfigurationLine', None)
            container.SetPosition(*cpos)
            container.SetSize(*csize)
            box.SetItemStep(original_row.LIST_ITEM_HEIGHT + 1)
            box.SetViewItemCount(getattr(window, '_ConfigurationWindow__GetViewItemCount')())
        self._Keep(back_list)
        container.SetPosition(PAD, top)
        container.SetSize(container.GetWidth(), self.list_h)
        self.panel = uir1.BoardSkin(container, kit, kind='panel')
        self._Keep(self.panel.Restore)
        box.SetItemStep(ROW_H + 1)
        box.SetViewItemCount(getattr(w, '_ConfigurationWindow__GetViewItemCount')())
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
            self.window.scrollBar = old_bar
            box.SetScrollBar(old_bar)
        self._Keep(back_bar)
        # while nothing is saved the empty panel says what to do
        self.empty_text = _Tr(u'Zatím žádné předvolby.', 'No presets yet.')
        self.empty_note = _Tr(u'Napiš název a ulož bonusy slotu.', 'Type a name and save the slot.')
        self.empty = uir1.RowText(container, self.empty_text, ROW_X, ROW_H, kit.font('text_s'), T.INK_DIM)
        self.empty.SetPosition(ROW_X, 4)
        self.note = uir1.RowText(container, self.empty_note, ROW_X, ROW_H, kit.font('text_s'), T.MUTED)
        self.note.SetPosition(ROW_X, 4 + ROW_H)
        for line in (self.empty, self.note):
            line.Hide()
            self._Keep(line.Hide)
        self.Sync()

    # ------------------------------------------------------------------ hooks of the window
    def Sync(self):
        """After the window loaded its list (LoadConfigurations -> __AdjustScrollbar: the panel narrows by the scroll
        bar's room while the list scrolls): the R1 panel follows, rows no longer in the list are hidden, the hint
        shows while the list is empty."""
        w = self.window
        self.panel.Resize(w.container.GetWidth(), w.container.GetHeight())
        current = set(id(row) for row in w.listBox.GetItems())
        for row in list(self.Row.rows):
            if id(row) not in current and row.IsShow():
                row.Hide()
        if len(w.listBox.GetItems()):
            self.empty.Hide()
            self.note.Hide()
        else:
            room = max(1, w.container.GetWidth() - 2 * ROW_X)
            uir1.Fit(self.empty, self.empty_text, room)
            uir1.Fit(self.note, self.empty_note, room)
            self.empty.Show()
            self.note.Show()

    def Undo(self):
        for step in reversed(self.undo):
            try:
                step()
            except Exception:
                pass
        self.undo = []

    def Restore(self):
        """Starý vzhled: the original window again (the window lists its rows again on its next Open)."""
        self.Undo()
        if self.board is not None:
            self.board.Destroy()
            self.board = None

    Destroy = Restore


def Build(window):
    """The R1 skin of a ConfigurationWindow (after __LoadWindow) or None (Starý vzhled, or the build failed: traced,
    the original window kept, not tried again in this session)."""
    if not UseR1():
        return None
    try:
        return PresetsSkin(window)
    except Exception:
        _failed.append(1)
        uir1.TraceFailure(WINDOW)
        return None
