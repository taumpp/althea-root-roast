# -*- coding: utf-8 -*-
"""Rychlá změna výbavy (uiquickequip.QuickEquipWindow, 530 x 338) and its set name dialog (310 x 152) in the R1 look
("Krvavá žíla", docs/ALTHEA_R1_KIT.md), drawn INTO the original windows:

* the R1 frame and header with the plain X; the original title bar stays as an invisible drag handle (the window
  flags do not change);
* no crimson strips: the content background is the R1 panel, the set list a lighter side column, the section
  headings Noto Sans with a quiet fading line under them, the footer under a quiet line;
* the equipment and costume boards keep their art and slot outlines, recoloured to graphite
  (tools/build_althea_r1_vybava.py, the crops of today's .sub files, so the slots stay aligned); the costume slot
  frames are the recoloured inventory ones (althea_r1_postava); item icons and the rename glyph stay;
* set rows: a lighter fill under the mouse, the selected set a dark fill with the red line under the row, Noto Sans
  texts top-aligned in their cell;
* "Nová sada" a secondary and "Použít sadu" the primary R1 button standing in for the original buttons (the
  window's Enable / Disable / Show / Hide reach them through an adapter);
* the name dialog: R1 frame and header, the R1 field around the SAME edit line, Zrušit / Uložit as R1 buttons.

Every original object and handler stays. Settings -> "Starý vzhled" keeps the original windows; a failure while
building traces to syserr and keeps the original look.
"""
import ui

import uikit
import uir1
import uir1layout as L
import uir1skin
import uir1tokens as T
import uir1vybava as V
import quickequipstyle as style

ROOT = 'd:/ymir work/ui/public/althea_r1_vybava/quick_equip/'
INV = 'd:/ymir work/ui/game/crimson_ember/inventory/'
PANEL = 'd:/ymir work/ui/game/crimson_ember/quick_equip/'
COSTUME_SLOT = 'd:/ymir work/ui/public/althea_r1_postava/inventory/costume_slot_transparent.png'
ROW_W, ROW_H = 159, 36
NAME_LIMIT = (114, 98)          # px of a set name: the permanent first set / a set with the rename glyph
PANEL_FILL = 0xFF141213


def _colour(packed):
    return uikit.GenerateColor(packed, 1.0)


class RowSkin(object):
    """One _SetRow in R1: its own fill bar shows the state (hover / selected), the red band line under a selected
    row, the accent strip and the top edge hidden, Noto Sans texts top-aligned."""

    def __init__(self, rec, row, kit):
        self.row, self.kit = row, kit
        self.hover = False
        self.name_text = ''
        self.line = uir1.Ops(row, [])                 # after the row's texts; it lies under them (no overlap)
        self.fonts = (kit.font('text_s'), kit.font('text'), kit.font('text_b'))
        rec.Hide(row.accent)
        rec.Hide(row.topEdge)
        rec.Font(row.number, self.fonts[0], T.INK_DIM, style.DENSE_FONT, style.argb(0xffc29783))
        rec.Position(row.number, 11, uir1.CellTop(ROW_H, self.fonts[0]))
        rec.Position(row.name, 34, uir1.CellTop(ROW_H, self.fonts[1]))
        rec.Call(lambda: row.selectedArrow.SetPackedFontColor(T.RED_HI),
                 lambda: row.selectedArrow.SetPackedFontColor(style.argb(0xffe2a1a4)))
        self.base_set = row.SetData                   # the class method, before the instance override
        row.SetData = self.SetData
        row.OnMouseOverIn = self.OnMouseOverIn
        row.OnMouseOverOut = self.OnMouseOverOut
        rec.Call(lambda: None, self.Undo)

    def SetData(self, index, name, selected):
        self.base_set(index, name, selected)
        if index is None:
            return
        row = self.row
        font = self.fonts[2] if selected else self.fonts[1]
        uir1.SetFont(row.name, font)
        row.name.SetPosition(34, uir1.CellTop(ROW_H, font))
        uir1.Fit(row.name, name, NAME_LIMIT[1 if index else 0])
        row.name.SetPackedFontColor(T.IVORY if selected else T.INK)
        row.accent.Hide()
        row.topEdge.Hide()
        self.Paint()

    def Paint(self):
        row = self.row
        state = 'selected' if row.selected else ('hover' if self.hover else 'normal')
        if state == 'normal':
            row.background.Hide()
        else:
            colour = T.BAND_SELECTED if state == 'selected' else T.BAND_HOVER
            row.background.SetColor(uikit.GenerateColor(colour, T.BAND_ALPHA[state]))
            row.background.Show()
        self.line.Apply(L.band_line(0, ROW_H, ROW_W) if state == 'selected' else [])

    def OnMouseOverIn(self):
        self.hover = True
        self.Paint()

    def OnMouseOverOut(self):
        self.hover = False
        self.Paint()

    def Undo(self):
        row = self.row
        for name in ('SetData', 'OnMouseOverIn', 'OnMouseOverOut'):
            if name in row.__dict__:
                delattr(row, name)
        self.line.Hide()
        row.background.Show()


class QuickEquipSkin(object):
    """R1 into one QuickEquipWindow (after its constructor loaded the uiscript and made the set rows)."""

    def __init__(self, window):
        self.window = window
        self.kit = kit = uir1.Kit()
        self.rec = rec = uir1skin.Recorder()
        self.skin = self.handle = None
        self.widgets = []
        self.adapters = []
        self.rows = []
        child = window.GetChild
        try:
            board = child('Board')
            self.skin = uir1.BoardSkin(board, kit, child('TitleName').GetText(), on_close=ui.__mem_func__(window.Close))
            self.handle = V.DragHandle(child('TitleBar'), (child('TitleName'),))
            self._Surfaces(board)
            self._Texts()
            self._Panels()
            self._Buttons(board)
            self.rows = [RowSkin(rec, row, kit) for row in window.rows]
        except Exception:
            self.Restore()
            raise

    # ------------------------------------------------------------------ build
    def _Surfaces(self, board):
        child, rec = self.window.GetChild, self.rec
        for name in ('ContentSurface', 'SetsHeadingSurface', 'SetsHeadingDivider', 'EquipmentHeadingSurface',
                     'EquipmentHeadingDivider', 'CostumeHeadingSurface', 'CostumeHeadingDivider', 'FooterDivider',
                     'FooterSurface'):
            rec.Hide(child(name))
        for name, colour, original in (('SetsSurface', T.SIDE, 0xff0c0b0b), ('SetsDivider', T.LINE, 0xff675043)):
            bar = child(name)
            rec.Call(lambda bar=bar, colour=colour: bar.SetColor(_colour(colour)),
                     lambda bar=bar, original=original: bar.SetColor(style.argb(original)))
        for x, w in ((15, 167), (196, 155), (363, 155)):
            self.widgets.append(uir1.Divider(board, x, 64, w))
        self.widgets.append(uir1.Divider(board, 15, 286, 501))

    def _Texts(self):
        child, rec, kit = self.window.GetChild, self.rec, self.kit
        head = kit.font('text_sb')
        small = kit.font('text_s')
        top = 40 + uir1.CellTop(25, head)
        for name, x in (('SetsHeading', 25), ('EquipmentHeading', 273), ('CostumeHeading', 440)):
            line = child(name)
            rec.Font(line, head, T.INK, style.BOLD_FONT, style.argb(0xffe1d4c4))
            rec.Position(line, x, top)
        count = child('SetsCount')
        rec.Font(count, small, T.INK_DIM, style.DENSE_FONT, style.argb(0xffb49f8a))
        rec.Position(count, 172, 40 + uir1.CellTop(25, small))
        rec.Call(count.SetHorizontalAlignRight, count.SetHorizontalAlignLeft)
        hint = child('DragHint')
        rec.Font(hint, small, T.INK_DIM, style.DENSE_FONT, style.argb(0xffc8b39d))
        rec.Position(hint, 357, 266)
        name = child('SelectedSetName')
        rec.Font(name, kit.font('text_b'), T.IVORY, style.BOLD_FONT, style.argb(0xffe1d4c4))
        rec.Position(name, 24, 289)
        sub = child('SelectedSetHint')
        rec.Font(sub, small, T.INK_DIM, style.DENSE_FONT, style.argb(0xffbdaa95))
        rec.Position(sub, 24, 289 + uir1.FontCell(kit.font('text_b')))

    def _Panels(self):
        child, rec = self.window.GetChild, self.rec
        for prefix, kind in (('EquipmentPanel', 'equipment'), ('CostumePanel', 'costume')):
            fill = child(prefix + 'Fill')
            rec.Call(lambda fill=fill: fill.SetColor(_colour(PANEL_FILL)),
                     lambda fill=fill: fill.SetColor(style.argb(0xff191614)))
            for edge in ('Top', 'Bottom', 'Left', 'Right'):
                bar = child(prefix + edge)
                rec.Call(lambda bar=bar: bar.SetColor(_colour(T.LINE)),
                         lambda bar=bar: bar.SetColor(style.argb(0xff5d5042)))
            rec.Image(child(prefix + 'Artwork'), ROOT + 'panel_%s_inner.png' % kind,
                      PANEL + 'panel_%s_inner.sub' % kind)
        rec.Image(child('EquipmentCompletion'), ROOT + 'equipment_slot_completion.png',
                  INV + 'equipment_slot_completion.png')
        rec.SlotBase(child('CostumeSlots'), COSTUME_SLOT, INV + 'costume_slot_transparent.sub')

    def _Buttons(self, board):
        window, kit = self.window, self.kit
        for attr, w, y, primary, small in (('newButton', 100, 252, False, True),
                                           ('applyButton', 170, 295, True, False)):
            original = getattr(window, attr)
            x = original.GetLocalPosition()[0]
            button = uir1.Button(board, kit, x, y, w, original.GetText(), primary=primary, small=small)
            self.widgets.append(button)
            adapter = V.Swap(window, attr, original, button, enabled=False)
            adapter.SetEvent(ui.__mem_func__(getattr(window, '_' + ('NewSet' if attr == 'newButton' else 'Apply'))))
            self.adapters.append((attr, adapter))

    # ------------------------------------------------------------------ restore
    def Restore(self):
        window = self.window
        if window is None:
            return
        for attr, adapter in self.adapters:
            V.Unswap(window, attr, adapter)
        self.adapters = []
        V.Fail(self.widgets)
        self.widgets = []
        self.rec.Undo()
        if self.handle is not None:
            self.handle.Restore()
        if self.skin is not None:
            self.skin.Restore()
            self.skin.Destroy()
        self.skin = self.handle = None
        self.rows = []
        self.window = None
        try:
            window.Refresh()
        except Exception:
            pass

    Destroy = Restore


class NameDialogSkin(object):
    """R1 into the set name dialog (_NameDialog): frame + header, the R1 field around the same edit line, R1
    buttons calling the dialog's own Accept / Close."""

    def __init__(self, dialog):
        self.dialog = dialog
        self.kit = kit = uir1.Kit()
        self.rec = rec = uir1skin.Recorder()
        self.skin = self.handle = self.field = None
        self.widgets = []
        child = dialog.GetChild
        try:
            board = dialog.board
            self.skin = uir1.BoardSkin(board, kit, board.titleName.GetText(), on_close=ui.__mem_func__(dialog.Close))
            self.handle = V.DragHandle(board.titleBar, (board.titleName,))
            label = child('NameLabel')
            rec.Font(label, kit.font('text_sb'), T.INK_DIM)
            rec.Position(label, 26, 44)
            slot = child('InputSlot')
            rec.Hide(slot)
            edit = dialog.input
            ex, ey = edit.GetLocalPosition()
            ew, eh = edit.GetWidth(), edit.GetHeight()
            self.field = uir1.Field(board, kit, 25, 65, 260, edit=edit, max_len=24)
            rec.Call(lambda: None, lambda: self._EditBack(edit, slot, ex, ey, ew, eh))
            for name, text, x, primary, event in (('SaveButton', u'Uložit', 45, True, dialog.Accept),
                                                  ('CancelButton', u'Zrušit', 165, False, dialog.Close)):
                original = child(name)
                button = uir1.Button(board, kit, x, 106, 100, text, primary=primary, event=ui.__mem_func__(event))
                self.widgets.append(button)
                import uiconfirm
                rec.Call(lambda: None, uiconfirm.Visual(original, button))
                rec.Hide(original)
            set_title = board.SetTitleName
            rec.Call(lambda: setattr(board, 'SetTitleName', self.SetTitleName),
                     lambda: board.__dict__.pop('SetTitleName', None))
            self.set_title = set_title
        except Exception:
            self.Restore()
            raise

    def _EditBack(self, edit, slot, x, y, w, h):
        edit.SetParent(slot)
        edit.SetPosition(x, y)
        edit.SetSize(w, h)
        text = edit.GetText()
        edit.SetText('')
        edit.SetDefaultFontName()
        edit.SetText(text)

    def SetTitleName(self, name):
        self.set_title(name)
        if self.skin is not None:
            self.skin.SetTitle(name)

    def Restore(self):
        if self.dialog is None:
            return
        V.Fail(self.widgets)
        if self.field is not None:
            self.field.Hide()
        self.rec.Undo()
        if self.handle is not None:
            self.handle.Restore()
        if self.skin is not None:
            self.skin.Restore()
            self.skin.Destroy()
        self.skin = self.handle = self.field = None
        self.widgets = []
        self.dialog = None

    Destroy = Restore
