# -*- coding: utf-8 -*-
"""Zahodit předmět (uicommon.QuestionDropDialog, ENABLE_NEW_DROP_DIALOG: an item dragged out of the inventory) and
Nákup více kusů (uicommon.BuyMultipleDialog, a stackable shop item) as compact R1 dialogs - "Zahodit předmět" (owner 8. 10. 2026, DEV 74: a frameless black box, three full-width buttons stacked on the right
with dead space and the item icon floating outside the box on the left).

* the R1 window frame with the header "Zahodit předmět" (Cinzel, the red vein, the plain X = Esc);
* the item in the slot C (one cell, or the single tall slot of a 2 / 3 cell item) on the left of the question,
  inside the dialog; the item name in its rarity colour (itemrarityaura, the server's grade) when it has one;
* the buttons in one row at the bottom: Ano, Zničit (the destructive one: the kit's dark blood red vein), Ne; a
  caller that hides Zničit gets the two-button row; the dialog is as wide as the question needs, no dead space.

Every position is absolute (left aligned): the real engine does not keep the uiscript's centre alignment of the slot
window after a SetPosition (DEV 74: the item at x -85 from the box). The dialog keeps its API, events and states
(SetAcceptEvent / SetDestroyEvent / SetCancelEvent, the anti flags, SetPending, the tooltip over the item, Esc); the
R1 buttons stand in for the native ones (uir1dialog.DialogButton). "Starý vzhled" keeps the original dialog; a
failure while building or laying out brings the original back (uir1.TraceFailure) and is not tried again.

Nákup více kusů (BuyDialogSkin, the same treatment; owner 8. 10. 2026: its item slot moved out of the box the same way):
the header "Nákup více kusů", the shop item in the slot C on the left, beside it the price line (with the sigil price
icon when the dialog shows one) and the quantity row ("Zadej počet" + the R1 field around the SAME edit line: its
update / return / escape events stay), Koupit (the primary action, as wide as its price label) and Zrušit in one row,
the confirmation on the left like in every dialog of the client.
"""
import weakref

import ui

import uir1
import uir1layout as L
import uir1tokens as T

SLOT_BASE = 'd:/ymir work/ui/public/Slot_Base.sub'
GAP = 10                 # px between the buttons and between the item and the question
BODY_GAP = 10            # px from the header vein to the body and from the body to the buttons
W_MIN, W_MAX = 300, 460  # the dialog grows with the question between these widths
QTY_W = 70               # the quantity field (4 digits)
SIGIL_SCALE = 0.625      # the sigil price icon as BuyMultipleDialog scales it
_failed = {'drop': False, 'buy': False}


def _Signed(color):
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def RarityColor(grade):
    """'|cFFRRGGBB' of an item rarity grade (itemrarityaura.COLORS), None for grade 0 / unknown."""
    try:
        import itemrarityaura
        grade = int(grade)
        if grade <= 0 or grade >= len(itemrarityaura.COLORS):
            return None
        r, g, b, unused = itemrarityaura.COLORS[grade]
        return '|cFF%02X%02X%02X' % tuple(int(max(0.0, min(1.0, v)) * 255 + 0.5) for v in (r, g, b))
    except Exception:
        return None


def Dress(dialog, cls=None):
    """The R1 look on a freshly loaded QuestionDropDialog (or ``cls`` on its dialog); the skin, or None (Starý vzhled,
    a failure)."""
    cls = cls or DropDialogSkin
    if _failed[cls.KIND] or not uir1.UseR1():
        return None
    try:
        return cls(dialog)
    except Exception:
        Fail(None, dialog, cls)
        return None


def DressBuy(dialog):
    """The R1 look on a freshly loaded BuyMultipleDialog."""
    return Dress(dialog, BuyDialogSkin)


def Fail(skin, dialog, cls=None):
    cls = cls or type(skin)
    _failed[cls.KIND] = True
    uir1.TraceFailure(cls.NAME)
    holder = skin if skin is not None else getattr(dialog, 'r1drop', None)
    if holder is not None:
        holder.Undo()
    try:
        dialog.r1drop = None
    except Exception:
        pass


class DropDialogSkin(object):
    KIND, NAME = 'drop', 'Zahodit předmět'
    TITLE = (u'Zahodit předmět', 'Drop item')
    # child, dialog attribute, the red-vein plate (Zničit: the destructive one) - from left to right
    BUTTONS = (('accept', 'acceptButton', False), ('destroy', 'destroyButton', True),
               ('cancel', 'cancelButton', False))
    HIDE = ('thinboard', 'button_holder')

    def __init__(self, dialog):
        self.dialog = weakref.proxy(dialog)
        self.kit = uir1.Kit()
        self.undo = []
        self.wrapped = []
        self.buttons = []
        self.frame = None
        self.cells = 1
        self.laying = False
        dialog.r1drop = self
        try:
            self._Build(dialog)
            self.Layout()
        except Exception:
            self.Undo()
            dialog.r1drop = None
            raise

    # build -----------------------------------------------------------------------------------------------------
    def _Build(self, dialog):
        import uir1dialog
        kit, board = self.kit, dialog.board
        me = weakref.ref(self)

        def close():
            skin = me()
            if skin is not None:
                skin.dialog.OnPressEscapeKey()
        size = (dialog.GetWidth(), dialog.GetHeight(), board.GetWidth(), board.GetHeight())
        self.frame = uir1.BoardSkin(board, kit, title=uir1.Tr_(*self.TITLE), on_close=close)
        self.undo.append(self._RestoreFrame)

        def size_back(dialog=dialog, board=board, size=size):
            dialog.SetSize(size[0], size[1])
            board.SetSize(size[2], size[3])
        self.undo.append(size_back)                  # runs before the frame's restore (undo goes backwards)
        for name in self.HIDE:
            widget = dialog.GetChild(name)
            if widget.IsShow():
                widget.Hide()
                self.undo.append(widget.Show)
        # the item: no engine slot base (alpha 0), the R1 cell / tall slot drawn under the slot window
        slot = dialog.itemSlot
        at = slot.GetLocalPosition()
        slot_size = (slot.GetWidth(), slot.GetHeight())          # 32 x 200 in the uiscript: below the dialog
        slot.SetSlotBaseImage(SLOT_BASE, 1.0, 1.0, 1.0, 0.0)
        slot.SetWindowHorizontalAlignLeft()
        self.cell = ui.ExpandedImageBox()
        self.cell.SetParent(board)
        self.cell.AddFlag('not_pick')
        self.cell.LoadImage(uir1.SLOT_CELL)
        self.cell.Show()
        holder = ui.Window()                     # a re-parent moves the slot window above the cell
        slot.SetParent(holder)
        slot.SetParent(board)

        def slot_back(slot=slot, at=at, size=slot_size):
            slot.SetSize(*size)
            slot.SetSlotBaseImage(SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
            slot.SetWindowHorizontalAlignCenter()
            slot.SetPosition(*at)
        self.undo.append(slot_back)
        self.undo.append(self.cell.Hide)
        # the question
        line = dialog.textLine
        line_at = line.GetLocalPosition()
        uir1.SetFont(line, kit.font('text'))
        line.SetPackedFontColor(_Signed(T.INK))
        line.SetWindowHorizontalAlignLeft()
        line.SetHorizontalAlignLeft()

        def line_back(line=line, at=line_at):
            text = line.GetText()
            line.SetText('')
            if hasattr(line, 'SetDefaultFontName'):          # the uiscript line has no "fontname"
                line.SetDefaultFontName()
            else:
                line.SetFontName('Tahoma:12')
            line.SetText(text)
            line.SetPackedFontColor(_Signed(0xFFFFFFFF))
            line.__dict__.pop('_r1drop_font', None)
            line.SetWindowHorizontalAlignCenter()
            line.SetHorizontalAlignCenter()
            line.SetPosition(*at)
        self.undo.append(line_back)
        # the buttons: R1 stand-ins with the native API, in one row
        elements = getattr(dialog, 'ElementDictionary', None)
        for name, attr, destructive in self.BUTTONS:
            native = dialog.GetChild(name)
            button = uir1dialog.DialogButton(board, kit, native, destructive, False)
            if hasattr(native, 'IsShow') and not native.IsShow():
                button.Hide()
            self.buttons.append((name, attr, native, button))
            if elements is not None:
                elements[name] = button
            setattr(dialog, attr, button)
            self.undo.append(lambda name=name, attr=attr, native=native, button=button:
                             self._RestoreButton(name, attr, native, button))
        self._BuildExtra(dialog)
        # the dialog's own calls that change the layout
        for target, method in ((line, 'SetText'),) + tuple((button, verb) for unused, unused2, unused3, button in
                                                             self.buttons for verb in ('Show', 'Hide', 'SetText')):
            self._Wrap(target, method)
        self._Wrap(dialog, 'SetItemSlot', self._ItemChanged)

    def _BuildExtra(self, dialog):
        """More of the dialog drawn in R1 (BuyDialogSkin: the quantity row)."""

    def _Wrap(self, target, name, after=None):
        me = weakref.ref(self)

        def changed(*args):
            skin = me()
            if skin is not None:
                (after or skin.Changed)(*args)
        own = target.__dict__.get(name)
        ref = weakref.ref(target)
        if own is not None:
            original = own
        else:
            function = getattr(target.__class__, name)

            def original(*args):
                obj = ref()
                return function(obj, *args) if obj is not None else None

        def wrapper(*args):
            result = original(*args)
            changed(*args)
            return result
        setattr(target, name, wrapper)
        self.wrapped.append((ref, name, own))

    def _RestoreFrame(self):
        if self.frame is not None:
            self.frame.Restore()

    def _RestoreButton(self, name, attr, native, button):
        button.Hide()
        elements = getattr(self.dialog, 'ElementDictionary', None)
        if elements is not None:
            elements[name] = native
        setattr(self.dialog, attr, native)
        # the caller's events and states move back to the native button
        native.SetEvent(button.eventFunc, *button.eventArgs) if button.eventFunc else None
        if not button.enabled:
            native.Down()
            native.Disable()

    # updates ---------------------------------------------------------------------------------------------------
    def Changed(self, *unused):
        if self.laying:                  # a button the layout itself shows / repaints
            return
        try:
            self.Layout()
        except Exception:
            Fail(self, self.dialog)

    def _ItemChanged(self, slotIndex):
        try:
            import item
            try:
                self.cells = max(1, min(3, int(item.GetItemSize()[1])))    # SetItemSlot selected the item
            except (TypeError, ValueError, IndexError):
                self.cells = 1
            name = item.GetItemName()
            self._ColourName(name, self._Grade(slotIndex))
            self.Layout()
        except Exception:
            Fail(self, self.dialog)

    @staticmethod
    def _Grade(slotIndex):
        try:
            import itemrarityaura
            return itemrarityaura.InventoryGrade(slotIndex)
        except Exception:
            return 0

    def _ColourName(self, name, grade):
        """The item name in the question in its rarity colour (the rest stays in the ink colour)."""
        color = RarityColor(grade)
        line = self.dialog.textLine
        text = line.GetText()
        if not color or not name or name not in text or '|c' in text:
            return
        line.SetText(text.replace(name, color + name + '|r', 1))

    def Layout(self):
        self.laying = True
        try:
            self._Layout()
        finally:
            self.laying = False

    def _FitLine(self, room):
        """The question in the text role, the smaller role when it would not fit ``room``; its width."""
        line, kit = self.dialog.textLine, self.kit
        line.SetWindowHorizontalAlignLeft()             # BuyMultipleDialog centres it again on every SetItemSlot
        line.SetHorizontalAlignLeft()
        font = kit.font('text')
        if getattr(line, '_r1drop_font', None) != font:
            uir1.SetFont(line, font)
            line._r1drop_font = font
        if uir1.TextWidth(line) > room:
            small = kit.font('text_s')
            uir1.SetFont(line, small)
            line._r1drop_font = small
        return min(room, uir1.TextWidth(line))

    def _Item(self, top, body_h):
        """The item column centred on the body: the R1 cell / tall slot and the slot window above it."""
        item_h = T.SLOT * self.cells
        item_y = top + (body_h - item_h) // 2
        self.cell.LoadImage(uir1.ROOT + L.slot_path(item_h))
        self.cell.SetPosition(T.PAD, item_y)
        self.dialog.itemSlot.SetPosition(T.PAD, item_y)
        self.dialog.itemSlot.SetSize(T.SLOT, item_h + self.cells - 1)    # the uiscript's slots are 33 px apart

    def _Size(self, w, h):
        dialog = self.dialog
        if (w, h) != (dialog.board.GetWidth(), dialog.board.GetHeight()):
            dialog.SetSize(w, h)
            dialog.board.SetSize(w, h)
            self.frame.Resize(w, h)

    def _Layout(self):
        dialog = self.dialog
        line = dialog.textLine
        shown = [button for unused, unused2, unused3, button in self.buttons if button.IsShow()]
        text_x = T.PAD + T.SLOT + GAP
        text_w = self._FitLine(W_MAX - text_x - T.PAD)
        row_w = len(shown) * T.BTN_W + max(0, len(shown) - 1) * GAP
        w = max(W_MIN, text_x + text_w + T.PAD, row_w + 2 * T.PAD)
        item_h = T.SLOT * self.cells
        body_h = max(item_h, uir1.FontCell(line._r1drop_font))
        top = T.HEAD_H + BODY_GAP
        by = top + body_h + BODY_GAP + 2
        h = by + T.BTN_H + T.PAD
        # the item column and the question beside it, both centred on the body
        self._Item(top, body_h)
        line.SetVerticalAlignCenter()
        line.SetPosition(text_x, top + body_h // 2)
        x = (w - row_w) // 2
        for button in shown:
            button.SetPosition(x, by)
            button.SetWidth(T.BTN_W)
            x += T.BTN_W + GAP
        self._Size(w, h)

    # teardown --------------------------------------------------------------------------------------------------
    def Undo(self):
        wrapped, self.wrapped = self.wrapped, []
        for ref, name, own in reversed(wrapped):
            target = ref()
            if target is None:
                continue
            try:
                if own is not None:
                    setattr(target, name, own)
                elif name in target.__dict__:
                    delattr(target, name)
            except Exception:
                pass
        undo, self.undo = self.undo, []
        for step in reversed(undo):
            try:
                step()
            except Exception:
                pass


class BuyDialogSkin(DropDialogSkin):
    """Nákup více kusů (uicommon.BuyMultipleDialog): see the module doc."""
    KIND, NAME = 'buy', u'Nákup více kusů'
    TITLE = (u'Nákup více kusů', 'Buy several')
    BUTTONS = (('accept', 'acceptButton', True), ('cancel', 'cancelButton', False))     # Koupit on the left, Zrušit right

    def _BuildExtra(self, dialog):
        kit, board = self.kit, dialog.board
        edit = dialog.quantityEditValue
        well = dialog.GetChild('money_slot')
        restore = (edit.GetLocalPosition(), edit.GetWidth(), edit.GetHeight())
        self.field = uir1.Field(board, kit, 0, 0, QTY_W, edit=edit, max_len=4)

        def put_back(edit=edit, well=well, restore=restore):
            edit.SetParent(well)
            edit.SetPosition(*restore[0])
            edit.SetSize(restore[1], restore[2])
        self.undo.append(put_back)
        self.undo.append(self.field.Hide)
        self.label = uir1.Text(board, dialog.GetChild('pleaseEnter').GetText(), 0, 0, kit.font('text_s'),
                               _Signed(T.INK_DIM))
        self.undo.append(self.label.Hide)

    def _ItemChanged(self, slotIndex):
        """SetItemSlot ends on the price item of an item price (PriceType 3): the shop item is selected again for
        its size. Shop items have no rarity grade of their own."""
        try:
            import item
            import shop
            item.SelectItem(shop.GetItemID(slotIndex))
            try:
                self.cells = max(1, min(3, int(item.GetItemSize()[1])))
            except (TypeError, ValueError, IndexError):
                self.cells = 1
            self.Layout()
        except Exception:
            Fail(self, self.dialog)

    def _Layout(self):
        dialog, kit = self.dialog, self.kit
        line = dialog.textLine
        text_x = T.PAD + T.SLOT + GAP
        icon = getattr(dialog, 'sigilPriceIcon', None)
        icon = icon if icon is not None and icon.IsShow() else None
        icon_w = int(icon.GetWidth() * SIGIL_SCALE) + 5 if icon is not None else 0
        text_w = self._FitLine(W_MAX - text_x - T.PAD - icon_w)
        cell = uir1.FontCell(line._r1drop_font)
        label_w = uir1.TextWidth(self.label)
        qty_w = label_w + 8 + QTY_W
        accept, cancel = [button for unused, unused2, unused3, button in self.buttons]
        cancel.SetWidth(T.BTN_W)
        accept.FitWidth(T.BTN_W)
        row_w = accept.GetWidth() + GAP + cancel.GetWidth()
        w = min(W_MAX, max(W_MIN, text_x + max(icon_w + text_w, qty_w) + T.PAD, row_w + 2 * T.PAD))
        item_h = T.SLOT * self.cells
        top = T.HEAD_H + BODY_GAP
        rows_h = cell + 6 + T.FIELD_H
        body_h = max(item_h, rows_h)
        by = top + body_h + BODY_GAP + 2
        h = by + T.BTN_H + T.PAD
        self._Item(top, body_h)
        y = top + (body_h - rows_h) // 2
        if icon is not None:
            icon.SetPosition(text_x, y + (cell - int(icon.GetHeight() * SIGIL_SCALE)) // 2)
        line.SetVerticalAlignCenter()
        line.SetPosition(text_x + icon_w, y + cell // 2)
        qy = y + cell + 6
        self.label.SetPosition(text_x, qy + T.FIELD_H // 2)            # uir1.Text: centred on y
        self.field.SetPosition(text_x + label_w + 8, qy)
        x = (w - row_w) // 2
        accept.SetPosition(x, by)
        cancel.SetPosition(x + accept.GetWidth() + GAP, by)
        self._Size(w, h)
