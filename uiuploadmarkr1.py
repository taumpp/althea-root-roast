# -*- coding: utf-8 -*-
"""Znak cechu (the guild mark picker, uiuploadmark.MarkSelectDialog) in the Althea R1 look "Krvavá žíla"
(docs/ALTHEA_R1_KIT.md). Settings -> "Starý vzhled" or a failed build keep uiuploadmark.MarkSelectWindow.

A new window (uir1.Window, float + movable) of the original's size (452 x 390 px): the R1 frame and header (title,
vein, plain X; Esc and the X close it, the whole header row drags it), the searched folder, the list of every
candidate in the upload folder (a placeholder square, the file name and why it can or cannot be used; a usable row
selects on click, the R1 scroll bar and the mouse wheel scroll), and the footer Otevřít složku / Obnovit / Nahrát znak
(primary, enabled with a selection). No preview: an upload-folder image cannot be drawn by the released client
(wndMgr.LoadImage reads packed resources only), see test_guild_mark_picker_disk_safety.

The folder access comes from uiuploadmark (``folder``: List / Describe / Path / Open), so this module does not
import the original picker.
"""
import ui

import uir1
import uir1tokens as T

WHAT = 'guild mark picker'
W, H = 452, 390               # uiguildv2widgets px(580) x px(500): the original window's size
PAD = T.PAD
TITLE = 'Znak cechu'
INTRO_Y = 34                  # the format line
FOLDER_Y = 56                 # Složka: <path>
LINE_H = 22
LIST_Y = 88                   # first row (the panel frame 2 px around it)
LIST_PITCH = 44
LIST_ROWS = 5
LIST_W = W - 2 * PAD
ROW_W = LIST_W - 4 - T.SCROLL_W - 6
SQUARE = 34                   # the placeholder of the mark (32 x 32 px inside a 1 px line)
TEXT_X = 8 + SQUARE + 10
HINT_Y = LIST_Y + LIST_ROWS * LIST_PITCH + 8
FOOTER_Y = H - PAD - T.BTN_H
FOLDER_W, REFRESH_W, UPLOAD_W = 150, 104, 150

FORMATS = 'Obrázek 32 x 32 px ve formátu PNG, TGA, BMP nebo JPG.'
NONE_USABLE = 'Žádný soubor zatím nesplňuje podmínky. Oprav ho a klikni na Obnovit.'
EMPTY = ('Ve složce zatím není žádný obrázek.',
         'Vlož do složky upload obrázek 32 x 32 px ve formátu',
         'PNG, TGA, BMP nebo JPG a klikni na Obnovit.',
         'Tlačítko Otevřít složku ji otevře.')
NEED_SELECTION = 'Vyber obrázek 32 x 32 px'

_failed = []


def FitTail(line, text, width, ellipsis='...'):
    """Like uir1.Fit, but keeps the END of ``text`` (the folder of a path is its last part)."""
    line.SetText(text)
    if uir1.TextWidth(line) <= width:
        return text
    cut = text
    while len(cut) > 1:
        cut = cut[1:]
        if str is bytes and 0x80 <= ord(cut[0]) < 0xC0:
            continue                    # Python 2 UTF-8 bytes: never start inside a character
        shown = ellipsis + cut.lstrip()
        line.SetText(shown)
        if uir1.TextWidth(line) <= width:
            return shown
    return line.GetText()


class Page(ui.Window):
    """Not pickable container (window coordinates)."""

    def __init__(self, parent, x, y, w, h):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.Show()


class FileRow(uir1.Interactive):
    """One candidate: a usable file selects on click (dark well with the red line), hover lightens it; a file that
    cannot be used is shown dimmed with the reason and takes no click."""

    def __init__(self, box, kit, index, on_select):
        uir1.Interactive.__init__(self)
        self.on_select = on_select
        self.SetParent(box)
        self.SetPosition(0, index * LIST_PITCH)
        self.SetSize(ROW_W, LIST_PITCH)
        h = LIST_PITCH - 2
        self.band = uir1.Band(self, 0, 0, ROW_W, h)
        top = (h - SQUARE) // 2
        self.square = uir1.Rect(self, 8, top, SQUARE, SQUARE, T.LINE)
        self.well = uir1.Rect(self, 9, top + 1, SQUARE - 2, SQUARE - 2, T.INNER)
        name, status = kit.font('text'), kit.font('text_s')
        gap = max(0, (h - uir1.FontCell(name) - uir1.FontCell(status)) // 3)
        self.name = uir1.Text(self, '', TEXT_X, gap, name, T.INK, valign='top')
        self.status = uir1.Text(self, '', TEXT_X, h - gap - uir1.FontCell(status), status, T.INK_DIM, valign='top')
        self.fileName = None
        self.selected = False
        self.callback = self.Select
        self.Hide()

    def Set(self, fileName, usable, status, selected):
        self.fileName = fileName
        self.selected = bool(selected and usable)
        limit = ROW_W - TEXT_X - 10
        uir1.Fit(self.name, fileName, limit)
        uir1.Fit(self.status, status, limit)
        self.name.SetPackedFontColor(T.IVORY if self.selected else (T.INK if usable else T.MUTED))
        self.status.SetPackedFontColor(T.INK_DIM if usable else T.RED_HI)
        self.well.SetColor(uir1.GenerateColor(T.BAND_SELECTED if usable else T.INNER, 1.0))
        self.Enable() if usable else self.Disable()
        self.Show()

    def Select(self):
        if self.on_select and self.fileName:
            self.on_select(self.fileName)

    def paint(self):
        if not hasattr(self, 'band'):
            return
        if self.selected:
            self.band.SetState('selected')
        elif self.enabled and self.hovered:
            self.band.SetState('hover')
        else:
            self.band.SetState('normal')


class MarkSelectWindowR1(uir1.Window):
    """The picker; ``owner`` is the MarkSelectDialog (owner.Select(fileName) after Nahrát znak)."""

    def __init__(self, owner, folder):
        self.built = False
        self.kit = uir1.Kit()
        uir1.Window.__init__(self, self.kit, W, H, TITLE)
        self.owner = owner
        self.folder = folder
        self.files = []
        self.selected = None
        self.offset = 0
        self.positioned = False

    def Build(self):
        kit = self.kit
        text_s = kit.font('text_s')
        self.intro = uir1.Text(self, FORMATS, PAD, INTRO_Y + uir1.CellTop(LINE_H, text_s), text_s, T.INK_DIM,
                               valign='top')
        self.folderLabel = uir1.Text(self, 'Složka:', PAD, FOLDER_Y + uir1.CellTop(LINE_H, text_s), text_s,
                                     T.INK_DIM, valign='top')
        self.folderX = PAD + uir1.TextWidth(self.folderLabel) + 6
        self.folderPath = uir1.Text(self, '', self.folderX, FOLDER_Y + uir1.CellTop(LINE_H, text_s), text_s,
                                    T.IVORY, valign='top')
        self.listFrame = uir1.Frame(self, PAD, LIST_Y - 2, LIST_W, LIST_ROWS * LIST_PITCH + 4, 'panel')
        self.listBox = Page(self, PAD + 2, LIST_Y, LIST_W - 4, LIST_ROWS * LIST_PITCH)
        self.rows = [FileRow(self.listBox, kit, index, self.Choose) for index in range(LIST_ROWS)]
        self.scroll = uir1.ScrollBar(kit)
        self.scroll.SetParent(self.listBox)
        self.scroll.SetPosition(LIST_W - 4 - T.SCROLL_W - 2, 0)
        self.scroll.SetScrollBarSize(LIST_ROWS * LIST_PITCH)
        self.scroll.SetScrollEvent(self.OnScroll)
        self.scroll.Hide()
        text = kit.font('text')
        self.empty = []
        for index, line in enumerate(EMPTY):
            font, colour = (text, T.IVORY) if index == 0 else (text_s, T.INK_DIM)
            y = LIST_Y + 16 + (0 if index == 0 else 12 + index * LINE_H)
            self.empty.append(uir1.Text(self, line, PAD + 16, y, font, colour, valign='top'))
        self.emptyPath = uir1.Text(self, '', PAD + 16, LIST_Y + 16 + 12 + 4 * LINE_H + 8, text_s, T.IVORY,
                                   valign='top')
        self.hint = uir1.Text(self, '', PAD, HINT_Y + uir1.CellTop(LINE_H, text_s), text_s, T.RED_HI, valign='top')
        self.openButton = uir1.Button(self, kit, PAD, FOOTER_Y, FOLDER_W, 'Otevřít složku', event=self.OpenFolder)
        self.refreshButton = uir1.Button(self, kit, PAD + FOLDER_W + 8, FOOTER_Y, REFRESH_W, 'Obnovit',
                                         event=self.Refresh)
        self.uploadButton = uir1.Button(self, kit, W - PAD - UPLOAD_W, FOOTER_Y, UPLOAD_W, 'Nahrát znak',
                                        primary=True, event=self.Upload)
        self.built = True

    # ------------------------------------------------------------------ the original window's API
    def Open(self):
        if not self.positioned:
            self.SetCenterPosition()
            self.positioned = True
        self.Refresh()
        self.Show()
        self.SetTop()

    def Refresh(self):
        self.files = [(fileName,) + tuple(self.folder.Describe(fileName)) for fileName in self.folder.List()]
        if self.selected not in [fileName for fileName, usable, status in self.files if usable]:
            self.selected = None
        self.offset = min(self.offset, self.Overflow())
        self.Render()

    def Choose(self, fileName):
        if fileName in [name for name, usable, status in self.files if usable]:
            self.selected = fileName
            self.Render()

    def Upload(self):
        fileName = self.selected
        if not fileName:
            return False
        self.Close()
        if self.owner:
            self.owner.Select(fileName)
        return True

    def OpenFolder(self):
        self.folder.Open()

    def Close(self):
        uir1.HideHint()
        self.Hide()

    def Destroy(self):
        self.Close()
        self.owner = None
        self.folder = None

    # ------------------------------------------------------------------ drawing
    def Overflow(self):
        return max(0, len(self.files) - LIST_ROWS)

    def Render(self):
        path = self.folder.Path()
        FitTail(self.folderPath, path, W - PAD - self.folderX)
        listed = bool(self.files)
        overflow = self.Overflow()
        for index, row in enumerate(self.rows):
            position = self.offset + index
            if listed and position < len(self.files):
                fileName, usable, status = self.files[position]
                row.Set(fileName, usable, status, fileName == self.selected)
            else:
                row.Hide()
        if overflow:
            self.scroll.SetMiddleBarSize(float(LIST_ROWS) / len(self.files))
            self.scroll.SetScrollStep(1.0 / overflow)
            self.scroll.SetPos(float(self.offset) / overflow, False)
            self.scroll.Show()
        else:
            self.scroll.Hide()
        for line in self.empty:
            line.Show() if not listed else line.Hide()
        FitTail(self.emptyPath, path, LIST_W - 32)
        self.emptyPath.Show() if not listed else self.emptyPath.Hide()
        usable = [fileName for fileName, ok, status in self.files if ok]
        self.hint.SetText(NONE_USABLE if listed and not usable else '')
        if self.selected:
            self.uploadButton.Enable()
            self.uploadButton.SetToolTipText(None)
        else:
            self.uploadButton.Disable()
            self.uploadButton.SetToolTipText(NEED_SELECTION)

    def OnScroll(self):
        overflow = self.Overflow()
        if overflow:
            offset = int(round(self.scroll.GetPos() * overflow))
            if offset != self.offset:
                self.offset = offset
                self.Render()

    def OnMouseWheel(self, delta):
        overflow = self.Overflow()
        if not self.built or not overflow:
            return False
        self.offset = max(0, min(overflow, self.offset + (-1 if delta > 0 else 1)))
        self.scroll.SetPos(float(self.offset) / overflow, False)
        self.Render()
        return True


def Create(owner, folder):
    """The R1 picker, or None with Settings -> "Starý vzhled" or after a failure (traced once; the caller then
    builds the original picker)."""
    if _failed or not uir1.UseR1():
        return None
    window = None
    try:
        window = MarkSelectWindowR1(owner, folder)
        window.Build()
        window.Hide()
        return window
    except Exception:
        _failed.append(WHAT)
        uir1.TraceFailure(WHAT)
        if window is not None:
            try:
                window.Hide()
            except Exception:
                pass
        return None
