# -*- coding: utf-8 -*-
"""The function picker of the button panels ("Další" and "Slot n") in the R1 look.

uibuttonpanelpicker.FunctionPicker stays the window and keeps every function: the title given by Open, the live
search over every function (Escape closes, Enter runs the first match), the grid of the ORIGINAL round function
medallions with their marks, tooltips and badges, the empty text, the placement above the taskbar, the Open / Close
callbacks and both modes (run a function / pick for a slot). This module only gives it the R1 look:

* the R1 frame with the title in Cinzel, the vein and the plain X (Close) instead of the board and its title bar;
* the search as an R1 search field around the picker's own edit line (magnifier, the clear X while there is text);
* the empty text in the kit font.

The medallions keep their size and position, the board keeps its size formula, so the header and the field fit the
space the original title bar and search bar used. The picker is itself the movable board: a mouse-down on the
header (not pickable) reaches it and drags it. Settings -> "Starý vzhled" (settingslook 'legacy') shows the
original board; a failure while building R1 is traced and the original board is restored (no retry).
"""
import ui

import uir1
import uir1tokens as T

TITLE_FALLBACK = u'Další'
FIELD_X, FIELD_Y = 12, 36          # the original search bar: background at (PAD_X - 2, 36)

_failed = False


def UseR1():
    """R1 unless Settings -> "Starý vzhled" chose the original look, or R1 already failed in this session."""
    return not _failed and uir1.UseR1()


class PickerSkin(object):
    """R1 layer of one FunctionPicker. Begin() makes the container first (so everything the picker creates later
    draws above it); Finish() builds the chrome into it and wraps the search line."""

    def __init__(self, picker):
        self.picker = picker
        self.kit = uir1.Kit()
        self.layer = None
        self.chrome = None
        self.field = None
        self.undo = []

    # ------------------------------------------------------------------ build
    def Begin(self):
        picker = self.picker
        layer = ui.Window()
        layer.SetParent(picker)
        layer.AddFlag('not_pick')
        layer.SetPosition(0, 0)
        layer.SetSize(picker.GetWidth(), picker.GetHeight())
        layer.Show()
        self.layer = layer

    def Finish(self, width, height):
        picker = self.picker
        kit = self.kit
        self.layer.SetSize(width, height)
        self.chrome = uir1.Chrome(self.layer, kit, width, height, TITLE_FALLBACK, on_close=self._Close)
        self._HideOriginalChrome()
        # The picker's own edit line inside the R1 search field (Escape / Enter / IME events stay on it).
        search = picker.search
        hint = getattr(search, 'infoMsg', '') or ''
        position = search.GetLocalPosition()
        size = (search.GetWidth(), search.GetHeight())
        self.undo.append(lambda: (search.SetParent(picker), search.SetPosition(*position),
                                  search.SetSize(*size), search.SetMax(30)))
        self.field = uir1.SearchField(picker, kit, FIELD_X, FIELD_Y, width - 2 * FIELD_X, hint=hint, edit=search,
                                      max_len=30, on_search=self._Search, on_clear=self._Search)
        background = getattr(picker, 'searchBackground', None)
        if background is not None:
            background.Hide()
            self.undo.append(background.Show)
        empty = picker.emptyText
        font = getattr(empty, 'font', None)
        uir1.SetFont(empty, kit.font('text_s'))
        empty.SetPackedFontColor(T.INK_DIM)
        self.undo.append(lambda: font and uir1.SetFont(empty, font))

    def _HideOriginalChrome(self):
        picker = self.picker
        widgets = list(getattr(picker, 'Corners', [])) + list(getattr(picker, 'Lines', []))
        widgets += [getattr(picker, 'Base', None), getattr(picker, 'titleBar', None)]
        for widget in widgets:
            if widget is not None and widget.IsShow():
                widget.Hide()
                self.undo.append(widget.Show)

    def Abort(self):
        for step in reversed(self.undo):
            try:
                step()
            except Exception:
                pass
        self.undo = []
        for widget in (self.field, self.layer):
            if widget is not None:
                try:
                    widget.Hide()
                except Exception:
                    pass
        self.field = self.chrome = self.layer = None

    # ------------------------------------------------------------------ the picker's hooks
    def Resize(self, width, height):
        if self.layer is None:
            return
        self.layer.SetSize(width, height)
        if self.chrome is not None:
            self.chrome.frame.Resize(width, height)

    def SetTitle(self, title):
        if self.chrome is not None:
            self.chrome.SetTitle(title)

    def _Close(self):
        self.picker.Close()

    def _Search(self):
        self.picker.Refresh()

    def Destroy(self):
        self.undo = []
        if self.field is not None:
            self.field.on_clear = None
            self.field.Hide()
        if self.chrome is not None:
            self.chrome.Destroy()
        self.field = self.chrome = self.layer = None
        self.picker = None


def Begin(picker):
    """The R1 container for a FunctionPicker being built, or None ('legacy', an earlier failure or a failure now)."""
    global _failed
    if not UseR1():
        return None
    skin = PickerSkin(picker)
    try:
        skin.Begin()
    except Exception:
        _failed = True
        uir1.TraceFailure(TITLE_FALLBACK)
        skin.Abort()
        return None
    return skin


def Finish(skin, width, height):
    """Builds the R1 chrome and field; on a failure the original board is restored and None returned."""
    global _failed
    try:
        skin.Finish(width, height)
    except Exception:
        _failed = True
        uir1.TraceFailure(TITLE_FALLBACK)
        skin.Abort()
        return None
    return skin
