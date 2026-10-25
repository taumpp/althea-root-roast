# -*- coding: utf-8 -*-
"""The Instaswitchbot window in the R1 look, variant A "Přepis 1:1" (owner's choice 9. 10. 2026, preview round
ui-navrhy-r1/kolo-20261009-instaswitchbot), drawn INTO uiswitchbot.InstantSwitchbotWindow.

The layout of the original window stays (the target slot left of the bonus rows, the change item, the fee and the one
main button at the bottom), drawn from the parts of the R1 switchbot (root/uiswitchbotr1.py) - nothing of the original
window is re-created, every function keeps running through the original handlers:

* 374 x 243 (the original 374 x 266): the R1 frame and the header like the POSTAVA window (Cinzel capitals, the vein,
  the plain X), two R1 panels drawn into the window's backdrop (made first, so they lie under the content);
* the target: the original 1 x 3 grid (32 px cells) with the R1 item slot C; the hover over an empty slot shows the
  one-line R1 hint "Přetáhni sem předmět z inventáře" (no vein);
* the bonus rows: the R1 switchbot rows (uiswitchbotr1.RowSkin: the bonus name, the magnifier, the X and the value field
  with the chevron of the value picker). A row the target has no room for (no item, no catalog yet, past
  catalog['slots']) is not hidden as before but shown disabled: the window has no black area;
* "Předmět změny" as the card of the R1 switchbot (icon, name, count, chevron of the original scroll picker); its menu in
  the R1 tooltip frame with 40 px rows, the hover lightens a row (no red);
* the fee as the one R1 yang price of the client (root/uir1price.py, the coin, "500.000.000 Yang",
  red when the player has less) right above the one primary button "Točit okamžitě" (an adapter of the original
  button: Refresh enables / disables it as before, disabled it is grey); the original coin and number stay for
  "Starý vzhled";
* the texts of the bonus rows in the ink the normal R1 switchbot shows them in (ROW_INK, owner 10. 10.);
* every text in Tahoma 12 (PRAVIDLA-UI 9. 10.), the window title in the R1 title font.

Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr and keeps it too.
"""
import ui
import wndMgr

import uir1
import uir1layout as L
import uir1price
import uir1tokens as T
import uiswitchbotr1 as R1

SIZE = (374, 243)               # variant A (the original is 374 x 266)
PANEL_X = 8                     # the panels inside the frame
ROW_H = 27                      # the original row pitch (uiswitchbot.INPUT_HEIGHT), a 24 px field
ROWS = 5
INSET = 6                       # the slot and the rows inside the main panel
SLOT_GAP = 8                    # slot -> rows
MAIN_H = ROWS * ROW_H + 9       # 144
PANEL_GAP = 4
FOOTER_H = 56
CARD_X, CARD_DY, CARD_W = 16, 8, 200
BUTTON_W = 136
BUTTON_RIGHT = 12               # the button (and the fee above it) from the footer panel's right edge
FEE_DY, FEE_H = 6, 16
HINT_DX, HINT_DY = 20, 34       # the slot hint from the slot's top left
POPUP_FILL, POPUP_FILL_ALPHA = 0xFF0C0B0C, 0.94     # the R1 tooltip fill (uir1.Frame 'tooltip')
ROW_TEXT_X = R1.CARD_TEXT_X
ORIGINAL_SLOT_BASE = R1.ORIGINAL_SLOT_BASE
_Signed = R1._Signed
# The ink of the bonus rows: what the normal R1 switchbot shows (owner 10. 10.: "copy the switchbot's rows, they are
# bright there"). RowSkin hands its tokens to SetPackedFontColor unsigned, which the x64 binding drops, so the normal
# window draws the bonus name, "Vyber bonus..." and the "-" of the value in the engine's default text colour, white
# (-1, the colour RowSkin.Restore gives the number line back). The Instaswitchbot sets it signed and explicitly: its
# disabled rows must not leave a darker colour behind when they become usable (the "Šance na bezvědomí" stuck grey).
ROW_INK = -1


def Tr(czech, english):
    return uir1.Tr_(czech, english)


def InstantFee():
    """The instant fee of the server catalog (0 while it is unknown)."""
    try:
        import bonuscatalog
        return int(bonuscatalog.InstantFee() or 0)
    except Exception:
        return 0


def HintText():
    return Tr(u'Přetáhni sem předmět z inventáře', 'Drag an item here from the inventory')


class TahomaKit(uir1.Kit):
    """Tahoma 12 for every text, button and hint (PRAVIDLA-UI "Písmo textu", 9. 10. 2026); the window title stays the
    R1 title (Cinzel capitals, like the POSTAVA window)."""

    def font(self, role='text'):
        return uir1.Kit.font(self, 'title' if role == 'title' else 'tahoma')


def Layout(w=SIZE[0], h=SIZE[1]):
    """The geometry of variant A (window coordinates): the panels, the slot, the rows, the card, the fee and the
    button (the numbers of the preview generator, _skript/insta.py draw_a)."""
    top = L.header(w)['content_top'] + 2
    footer_y = top + MAIN_H + PANEL_GAP
    slot = (PANEL_X + INSET, top + INSET)
    rows_x = slot[0] + T.SLOT + SLOT_GAP
    button_x = w - PANEL_X - BUTTON_RIGHT - BUTTON_W
    return dict(
        main=(PANEL_X, top, w - 2 * PANEL_X, MAIN_H),
        footer=(PANEL_X, footer_y, w - 2 * PANEL_X, FOOTER_H),
        slot=slot,
        rows=(rows_x, top + INSET, w - 2 * PANEL_X - (rows_x - PANEL_X) - INSET),
        card=(CARD_X, footer_y + CARD_DY, CARD_W),
        fee=(button_x, footer_y + FEE_DY, BUTTON_W, FEE_H),
        button=(button_x, footer_y + FOOTER_H - 8 - T.BTN_H_S, BUTTON_W),
    )


class InstantRowSkin(R1.RowSkin):
    """The R1 switchbot row (RowSkin) at its place in the Instaswitchbot; ``off`` = the target has no room for the row
    (no item, no catalog, past its slots): both fields disabled, a grey "Vyber bonus..." and "-", nothing clickable,
    the original number line hidden."""

    def __init__(self, skin, row, width, x, y):
        self.off = False
        self.drawn_off = None
        R1.RowSkin.__init__(self, skin, row, width)
        row.SetPosition(x, y)

    def SetOff(self, off):
        self.off = bool(off)

    def Sync(self):
        off = self.off
        if off != self.drawn_off:
            self.drawn_off = off
            state = 'disabled' if off else 'normal'
            self.type_field.Apply(self.type_field.w, state)
            self.value_field.Apply(self.value_field.w, state)
            self.value_text.SetPackedFontColor(ROW_INK)
            self.key = None
        if not off:
            R1.RowSkin.Sync(self)
            self.text.SetPackedFontColor(ROW_INK)       # RowSkin's own (unsigned) colour does not reach the engine
            return
        row = self.row
        if row.valueEditLine.IsShow():
            row.valueEditLine.Hide()
        if self.key == 'off':
            return
        self.key = 'off'
        uir1.Fit(self.text, Tr('Vyber bonus...', 'Choose a bonus...'), self.search_x - 8 - 4)
        self.text.SetPackedFontColor(ROW_INK)           # the field's disabled well and magnifier say "off", not the ink
        self.search.Disable()
        self.search.SetPosition(self.clear_x - 2, self.search.GetLocalPosition()[1])
        self.clear.Hide()
        self.chevron.Hide()
        self.value_text.SetText('-')
        self.value_text.Show()


class TooltipBoard(R1.FieldSkin):
    """The R1 tooltip frame drawn with a ThinBoardCircle's OWN corner and line images (made before its children, so
    the frame lies under them), its base bar as the dark fill: the scroll menu of the original picker."""

    def __init__(self, board):
        base = getattr(board, 'Base', None)
        self.base_pos = base.GetLocalPosition() if base is not None else (0, 0)
        R1.FieldSkin.__init__(self, board, board.GetWidth())

    def Apply(self, w, state='normal'):
        board = self.board
        self.w, h = int(w), int(board.GetHeight())
        self.ops.Apply(L.frame('tooltip', self.w, h))
        if self.base is not None:
            self.base.SetPosition(1, 1)
            self.base.SetSize(max(1, self.w - 2), max(1, h - 2))
            self.base.SetColor(uir1.GenerateColor(POPUP_FILL, POPUP_FILL_ALPHA))
            self.base.Show()

    def Restore(self):
        if self.base is not None:
            self.base.SetPosition(*self.base_pos)
            try:
                self.base.SetColor(self.board.BOARD_COLOR)
            except Exception:
                pass
        R1.FieldSkin.Restore(self)


class MenuSkin(object):
    """The scroll menu of the original ScrollPicker (its rows are made by ScrollPicker.BuildRows whenever the offered
    scrolls change): the R1 tooltip frame, the rows without their boards, Tahoma 12 (the name in ivory, the count
    dimmed) and the hover as a lighter row. Restore drops the dressed rows: the picker builds original ones again."""

    def __init__(self, skin, picker):
        self.skin, self.picker = skin, picker
        self.font = skin.kit.font('text')
        self.dressed = []
        self.frame = TooltipBoard(picker.popup)
        self._DropRows()
        self.build = picker.BuildRows
        picker.BuildRows = self.BuildRows

    def _DropRows(self):
        picker = self.picker
        for row in picker.rows:
            row.Hide()
        picker.rows = []
        picker.menu = None              # never equal to a tuple: the next BuildRows makes the rows again

    def BuildRows(self):
        picker = self.picker
        before = picker.rows
        self.build()
        if picker.rows is not before:
            self.dressed = [self._Dress(row) for row in picker.rows]
        for row in picker.rows:
            row.Base.Hide()                 # no row stays lit from the last opening
        self.frame.Apply(picker.popup.GetWidth())      # BuildRows sized the popup: its board laid its images out again

    def _Dress(self, row):
        clear = R1.Clear(row)
        for line, y, color in ((row.name, 6, T.IVORY), (row.count, 22, T.INK_DIM)):
            uir1.SetFont(line, self.font)
            line.SetPackedFontColor(_Signed(color))
            line.SetPosition(ROW_TEXT_X, y)
        base = row.Base
        base.SetPosition(0, 0)
        base.SetSize(row.GetWidth(), row.GetHeight())
        base.SetColor(uir1.GenerateColor(T.BAND_HOVER, T.BAND_ALPHA['hover']))
        base.Hide()
        row.OnMouseOverIn = base.Show
        row.OnMouseOverOut = base.Hide
        return clear

    def Restore(self):
        picker = self.picker
        picker.__dict__.pop('BuildRows', None)
        for row in picker.rows:
            row.__dict__.pop('OnMouseOverIn', None)
            row.__dict__.pop('OnMouseOverOut', None)
        self._DropRows()
        self.dressed = []
        self.frame.Restore()


class InstantSkin(object):
    """R1 into one uiswitchbot.InstantSwitchbotWindow (at the end of its __init__)."""

    def __init__(self, window):
        self.window = window
        self.kit = TahomaKit()
        self.layout = Layout()
        self.rows, self.panels, self.clears = [], [], []
        self.original_size = (window.GetWidth(), window.GetHeight())
        self.original_start = window.start
        self.board = None
        try:
            self._Build()
        except Exception:
            self.Restore()
            raise

    def _Build(self):
        window, kit, layout = self.window, self.kit, self.layout
        font = kit.font('text')
        window.SetSize(*SIZE)
        self.board = uir1.BoardSkin(window, kit, window.titleName.GetText() or 'Instaswitchbot', on_close=window.Close)
        for key in ('main', 'footer'):
            x, y, w, h = layout[key]
            self.panels.append(uir1.Frame(window.backdrop, x, y, w, h, 'panel'))

        # the target slot
        slot = window.itemSlot
        self.slot_pos = slot.GetLocalPosition()
        slot.SetPosition(*layout['slot'])
        slot.SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0)
        self.hint = uir1.Hint(kit)
        self.hint_shown = False

        # the bonus rows
        x, y, width = layout['rows']
        for index, row in enumerate(window.rows):
            self.rows.append(InstantRowSkin(self, row, width, x, y + index * ROW_H))

        # Předmět změny: the card of the R1 switchbot
        picker = window.picker
        choice = picker.choice
        self.picker_pos = picker.GetLocalPosition()
        self.picker_size = (picker.GetWidth(), picker.GetHeight())
        cx, cy, cw = layout['card']
        picker.SetPosition(cx, cy)
        picker.SetSize(cw, self.picker_size[1])
        choice.SetSize(cw, choice.GetHeight())
        self.clears.append(R1.Clear(choice))
        self.picker_hidden = [choice.name, choice.count, picker.arrow]
        for widget in self.picker_hidden:
            widget.Hide()
        self.card_name = uir1.Text(choice, '', ROW_TEXT_X, 6, font, _Signed(T.IVORY), valign='top')
        self.card_count = uir1.Text(choice, '', ROW_TEXT_X, 22, font, _Signed(T.INK_DIM), valign='top')
        self.card_chevron = R1.Chevron(choice, 'chevron/down_%s.png', cw - 6 - R1.CHEVRON_W,
                                       (choice.GetHeight() - R1.CHEVRON_W) // 2, T.CHEVRON, self.ToggleMenu,
                                       R1.CHEVRON_W)
        choice.SetOnMouseLeftButtonUpEvent(self.ToggleMenu)
        self.menu = MenuSkin(self, picker)

        # the fee (the R1 yang price) and the one main button
        self.yang_pos = window.yangIcon.GetLocalPosition()
        window.fee.Hide()
        window.yangIcon.Hide()
        fx, fy, fw, fh = layout['fee']
        self.fee_right, self.fee_y, self.fee_h = fx + fw, fy, fh
        self.fee = uir1price.Price(window, self.fee_right, fy + (fh - uir1price.ICON_H) // 2, 'right')
        bx, by, bw = layout['button']
        original = self.original_start
        self.start = uir1.Button(window, kit, bx, by, bw, original.GetText(), primary=True, small=True,
                                 event=window.Start, font=font)
        original.Hide()
        window.start = R1.ButtonAdapter(self.start)
        window.start.Enable() if uir1.IsEnabled(original, default=False) else window.start.Disable()

        # every frame: the rows, the card, the fee and the hint follow the original controls
        self.ticker = ui.Window()
        self.ticker.SetParent(window)
        self.ticker.AddFlag('not_pick')
        self.ticker.SetSize(0, 0)
        self.ticker.OnUpdate = self.Sync
        self.ticker.Show()
        self.Sync()

    # ------------------------------------------------------------------ state
    def ToggleMenu(self):
        """The chevron / a click on the card: the original picker's menu, not without a target (nothing to change)."""
        picker = self.window.picker if self.window else None
        if picker is None:
            return
        if picker.choice.vnum or (picker.popup and picker.popup.IsShow()):
            picker.Toggle()

    def Sync(self):
        window = self.window
        if window is None:
            return
        catalog = window.rows[0].provider.Catalog() if window.rows else None
        for index, skin in enumerate(self.rows):
            off = not (catalog and catalog['values'] and index < catalog['slots'])
            skin.SetOff(off)
            if off and not skin.row.IsShow():
                skin.row.Show()             # the original hides a row without room: R1 shows it disabled
            skin.Sync()
        self._SyncCard()
        self._SyncFee()
        self._SyncHint()

    def _SyncCard(self):
        picker = self.window.picker
        choice = picker.choice
        key = (choice.vnum, choice.name.GetText(), choice.count.GetText())
        if key != getattr(self, '_card', None):
            self._card = key
            if choice.vnum:
                uir1.Fit(self.card_name, key[1], choice.GetWidth() - ROW_TEXT_X - 26)
                self.card_name.SetPackedFontColor(_Signed(T.IVORY))
                self.card_name.SetPosition(ROW_TEXT_X, 6)
                self.card_count.SetText(key[2])
                self.card_count.Show()
            else:
                self.card_name.SetText('-')
                self.card_name.SetPackedFontColor(_Signed(T.MUTED))
                self.card_name.SetPosition(ROW_TEXT_X, uir1.CellTop(choice.GetHeight(), self.kit.font('text')))
                self.card_count.Hide()
        enabled = bool(picker.enabled and choice.vnum)
        if enabled != self.card_chevron.IsEnabled():
            self.card_chevron.Enable() if enabled else self.card_chevron.Disable()

    def _SyncFee(self):
        fee = InstantFee()
        key = (fee, uir1price.CanAfford(fee) if fee else None)
        if key == getattr(self, '_fee', None):
            return
        self._fee = key
        if fee:
            self.fee.SetPrice(fee, key[1])
        else:
            self.fee.Clear()                            # no catalog yet: no price (the original shows "-")

    def SlotHovered(self):
        window = self.window
        if window is None or not window.IsShow():
            return False
        slot = window.itemSlot
        try:
            mx, my = wndMgr.GetMousePosition()
        except Exception:
            return False
        x, y = slot.GetGlobalPosition()
        return x <= mx < x + slot.GetWidth() and y <= my < y + slot.GetHeight()

    def _SyncHint(self):
        window = self.window
        empty = window.displayedVnum == 0
        if empty and self.SlotHovered():
            if not self.hint_shown:
                self.hint_shown = True
                x, y = window.itemSlot.GetGlobalPosition()
                self.hint.ShowAt((x, y, window.itemSlot.GetWidth(), window.itemSlot.GetHeight()), HintText())
                try:
                    sw, sh = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
                except Exception:
                    sw, sh = 1920, 1080
                self.hint.SetPosition(max(0, min(x + HINT_DX, sw - self.hint.GetWidth())),
                                      max(0, min(y + HINT_DY, sh - self.hint.GetHeight())))
        else:
            self.HideHint()

    def HideHint(self):
        hint = getattr(self, 'hint', None)
        if hint is not None and self.hint_shown:
            self.hint_shown = False
            hint.Hide()

    # ------------------------------------------------------------------ restore
    def Restore(self):
        window = self.window
        if window is None:
            return
        self.window = None
        ticker = getattr(self, 'ticker', None)
        if ticker is not None:
            ticker.OnUpdate = lambda: None
            ticker.Hide()
        hint = getattr(self, 'hint', None)
        if hint is not None:
            hint.Destroy()
        for skin in self.rows:
            skin.Restore()
        catalog = window.rows[0].provider.Catalog() if window.rows else None
        for index, row in enumerate(window.rows):
            if not (catalog and catalog['values'] and index < catalog['slots']):
                row.Hide()                  # the original hides a row without room
        if hasattr(self, 'slot_pos'):
            window.itemSlot.SetPosition(*self.slot_pos)
            window.itemSlot.SetSlotBaseImage(ORIGINAL_SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
        menu = getattr(self, 'menu', None)
        if menu is not None:
            menu.Restore()
        picker = window.picker
        if hasattr(self, 'picker_pos'):
            picker.SetPosition(*self.picker_pos)
            picker.SetSize(*self.picker_size)
            picker.choice.SetSize(self.picker_size[0], picker.choice.GetHeight())
            picker.choice.SetOnMouseLeftButtonUpEvent(picker.Toggle)
        for widget in getattr(self, 'picker_hidden', []):
            widget.Show()
        for clear in self.clears:
            clear.Restore()
        for name in ('card_name', 'card_count', 'card_chevron', 'fee', 'start'):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.Hide()
                if name == 'fee' and hasattr(widget, 'Destroy'):
                    widget.Destroy()
                if hasattr(widget, 'callback'):
                    widget.callback = None
        if hasattr(self, 'yang_pos'):
            window.yangIcon.SetPosition(*self.yang_pos)
            window.yangIcon.Show()
            window.fee.Show()
        original = self.original_start
        if isinstance(window.start, R1.ButtonAdapter):
            original.Enable() if window.start.IsEnabled() else original.Disable()
        window.start = original
        original.Show()
        for panel in self.panels:
            panel.Hide()
            panel.Destroy()
        self.panels = []
        window.SetSize(*self.original_size)
        if self.board is not None:
            self.board.Restore()
            self.board.Destroy()
            self.board = None

    Destroy = Restore
