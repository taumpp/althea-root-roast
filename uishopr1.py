# -*- coding: utf-8 -*-
"""The shop windows in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md), drawn INTO the original windows.

* Obchod NPC and Osobní obchod: uishop.ShopDialog opens both (the private shop of another player too - the old
  uiprivateshop.PrivateShopDialog is never created). R1: frame and header, the original grid with the R1 item slot C,
  Koupit / Prodat as R1 buttons (the active trade mode is the primary one with the vein), Zavřít obchod as an R1
  button. The window keeps its size: 344 x the rows of the packed grid. The shop of an upgrade NPC (CraftToolShopV1,
  NASTROJ-OKNO = A) adds "Vylepšit nástroj" (primary) right of Koupit / Prodat; the three fill the row between the
  window's margins.
  A private shop shows the seller's sign (the text above the seller's head, uiprivateshopbuilder's sign of that vid)
  as the window title instead of "Obchod". A private shop with two pages lays page 1 into the left five columns and
  page 2 into the right five (one continuous ten column grid as before) and names the halves "Strana 1 / Strana 2"
  under the grid; with one page there is no caption (it would name something that is not there).
* Otevřít obchod (uiprivateshopbuilder.PrivateShopBuilder, 184 x 380): frame and header, the shop name in an R1 well,
  the original 5 x 8 grid (the R1 item slot C), one line on what the name is for, Zavřít | Otevřít (the main action
  on the right).
* The sign above the seller (PrivateShopAdvertisementBoard): the R1 panel and the kit text font.

The original buttons stay the window's objects: the R1 buttons stand in for them through small adapters with the
same calls (Show / Hide / Down / SetUp / IsDown / SetPosition), so every original handler (OnBuy, OnSell,
CancelShopping, AskClosePrivateShop, OnOk, OnClose) runs unchanged. Settings -> "Starý vzhled" keeps the original
windows; a failure while building traces to syserr and keeps the original look.
"""
import ui

import uir1
import uir1layout as L
import uir1tokens as T

SHOP_W = 344
BUY_W = SELL_W = 96
BUTTON_GAP = 8
TOOL_W = SHOP_W - 2 * T.PAD - BUY_W - SELL_W - 2 * BUTTON_GAP      # "Vylepšit nástroj": the rest of the row
CLOSE_W = 148
CAPTION_H = 16          # the "Strana 1 / Strana 2" line between the grid and the footer (two page shops only)
GRID_X = 12
HALF_W = 5 * 32
TITLE_MARGIN = 44       # header title room: the X and some air on both sides
ORIGINAL_SLOT_BASE = 'd:/ymir work/ui/public/Slot_Base.sub'


def Tr(czech, english):
    return uir1.Tr_(czech, english)


def FitTitle(header, text, width):
    """The longest prefix of ``text`` (with "...") whose upper case title fits ``width`` px."""
    line = header.title
    shown = text
    line.SetText(uir1.Upper(shown))
    while uir1.TextWidth(line) > width and len(shown) > 1:
        shown = shown[:-1].rstrip()
        line.SetText(uir1.Upper(shown + '...'))
    return shown if shown == text else shown + '...'


class ToggleAdapter(object):
    """Stands in for an original ui.ToggleButton (the shop's Koupit / Prodat): Down / SetUp / IsDown drive the R1
    button's primary state, a click toggles and calls the original toggle events."""

    def __init__(self, button, y_offset=0):
        self.button = button
        self.down = False
        self.on_down = self.on_up = None
        self.y_offset = y_offset
        button.SetEvent(self.Toggle)

    def Toggle(self):
        if self.down:
            self.SetUp()
            if self.on_up:
                self.on_up()
        else:
            self.Down()
            if self.on_down:
                self.on_down()

    def Down(self):
        self.down = True
        self.button.SetPrimary(True)

    def SetUp(self):
        self.down = False
        self.button.SetPrimary(False)

    def IsDown(self):
        return self.down

    def SetPosition(self, unused_x, y):
        self.button.SetPosition(self.button.GetLocalPosition()[0], int(y) + self.y_offset)

    def Show(self):
        self.button.Show()

    def Hide(self):
        self.button.Hide()

    def IsShow(self):
        return self.button.IsShow()

    def Destroy(self):
        self.on_down = self.on_up = None
        self.button.callback = None
        self.button.Hide()


class ButtonAdapter(ToggleAdapter):
    """Stands in for an original ui.Button: Show / Hide / SetPosition / SetEvent / Enable / Disable."""

    def __init__(self, button, event=None, y_offset=0):
        ToggleAdapter.__init__(self, button, y_offset)
        button.SetEvent(event)

    def SetEvent(self, event, *args):
        self.button.SetEvent((lambda: event(*args)) if args else event)

    def Enable(self):
        self.button.Enable()

    def Disable(self):
        self.button.Disable()


class ShopSkin(object):
    """R1 into one uishop.ShopDialog (after its LoadDialog bound the children)."""

    def __init__(self, dialog, title):
        self.dialog = dialog
        self.kit = uir1.Kit()
        self.title = title
        self.captions = []
        self.halves = False
        self.originals = (dialog.btnBuy, dialog.btnSell, dialog.btnClose, dialog.btnCraftTool)
        self.skin = uir1.BoardSkin(dialog.board, self.kit, title, on_close=dialog.Close, hide=(dialog.titleBar,))
        try:
            board, kit = dialog.board, self.kit
            footer = dialog.btnBuy.GetLocalPosition()[1]
            left = (SHOP_W - BUY_W - SELL_W - BUTTON_GAP) // 2
            y = footer - 1
            self.buy = ToggleAdapter(uir1.Button(board, kit, left, y, BUY_W, dialog.btnBuy.GetText()), -1)
            self.sell = ToggleAdapter(uir1.Button(board, kit, left + BUY_W + BUTTON_GAP, y, SELL_W,
                                                  dialog.btnSell.GetText()), -1)
            self.close = ButtonAdapter(uir1.Button(board, kit, (SHOP_W - CLOSE_W) // 2, y, CLOSE_W,
                                                   dialog.btnClose.GetText()), dialog.AskClosePrivateShop, -1)
            self.tool = ButtonAdapter(uir1.Button(board, kit, 0, y, TOOL_W, dialog.btnCraftTool.GetText(),
                                                  primary=True), dialog.OnCraftTool, -1)
            for adapter, original in zip((self.buy, self.sell, self.close, self.tool), self.originals):
                adapter.Show() if original.IsShow() else adapter.Hide()
                original.Hide()
            self.buy.on_down, self.buy.on_up = dialog.OnBuy, dialog.CancelShopping
            self.sell.on_down, self.sell.on_up = dialog.OnSell, dialog.CancelShopping
            for index, text in enumerate((Tr('Strana 1', 'Page 1'), Tr('Strana 2', 'Page 2'))):
                caption = uir1.Text(board, text, GRID_X + HALF_W * index + HALF_W // 2, 0, kit.font('text_s'),
                                    T.INK_DIM, align='center', valign='top')
                caption.Hide()
                self.captions.append(caption)
            dialog.btnBuy, dialog.btnSell, dialog.btnClose, dialog.btnCraftTool = self.buy, self.sell, self.close, self.tool
            self.LayoutFooter(self.tool.IsShow())
        except Exception:
            self.Restore()
            raise

    # ------------------------------------------------------------------ used by ShopDialog
    @staticmethod
    def SlotBase():
        return uir1.SLOT_CELL

    def CaptionHeight(self):
        return CAPTION_H if self.halves else 0

    def SetHalves(self, halves):
        self.halves = bool(halves)

    def LayoutFooter(self, tool):
        """Koupit / Prodat centred; with "Vylepšit nástroj" the three of them between the window's margins."""
        adapters = (self.buy, self.sell, self.tool) if tool else (self.buy, self.sell)
        widths = [adapter.button.GetWidth() for adapter in adapters]
        x = (SHOP_W - sum(widths) - BUTTON_GAP * (len(widths) - 1)) // 2
        for adapter, width in zip(adapters, widths):
            adapter.button.SetPosition(x, adapter.button.GetLocalPosition()[1])
            x += width + BUTTON_GAP

    def SetTitle(self, text):
        header = self.skin.header
        self.skin.SetTitle(FitTitle(header, text or self.title, SHOP_W - 2 * TITLE_MARGIN))

    def Resize(self, w, h, grid_bottom):
        self.skin.Resize(w, h)
        for caption in self.captions:
            caption.SetPosition(caption.GetLocalPosition()[0], grid_bottom + 1)
            caption.Show() if self.halves else caption.Hide()

    def Restore(self):
        """The original look again (the original buttons back on the dialog)."""
        dialog = self.dialog
        if dialog is None:
            return
        for name, original in zip(('buy', 'sell', 'close', 'tool'), self.originals):
            adapter = getattr(self, name, None)
            if adapter is not None:
                if adapter.IsShow():
                    original.Show()
                adapter.Destroy()
        dialog.btnBuy, dialog.btnSell, dialog.btnClose, dialog.btnCraftTool = self.originals
        for caption in self.captions:
            caption.Hide()
        self.skin.Restore()
        self.skin.Destroy()
        self.dialog = None

    Destroy = Restore


def SignText(vid):
    """The seller's sign of a private shop (the text above the seller's head), '' when there is none."""
    try:
        import uiprivateshopbuilder
        board = uiprivateshopbuilder.g_privateShopAdvertisementBoardDict.get(vid)
        return board.textLine.GetText() if board is not None else ''
    except Exception:
        return ''


# --------------------------------------------------------------------------- Otevřít obchod
BUILDER_W, BUILDER_H = 184, 380
NAME_Y = 35
GRID_Y = 64             # the 5 x 8 grid 6 px higher than the original (70): room for the note above the buttons
NOTE_GAP = 3


class BuilderSkin(object):
    """R1 into uiprivateshopbuilder.PrivateShopBuilder (after its __LoadWindow)."""

    def __init__(self, builder, board, title, name_slot, name_line, ok, close):
        self.builder = builder
        self.kit = kit = uir1.Kit()
        self.name_slot, self.name_line = name_slot, name_line
        self.name_parent = name_slot
        self.name_pos = name_line.GetLocalPosition()
        self.originals = (ok, close)
        self.skin = uir1.BoardSkin(board, kit, title, on_close=builder.OnClose, hide=(builder.titleBar,))
        try:
            iw = BUILDER_W - 2 * T.PAD
            self.well = uir1.Layer(board, T.PAD, NAME_Y, iw, T.FIELD_H, L.field('normal', iw))
            name_slot.Hide()
            name_line.SetParent(board)          # a new parent: the name now draws above the well
            uir1.SetFont(name_line, kit.font('text'), name_line.GetText())
            name_line.SetPackedFontColor(T.INK)
            name_line.SetPosition(T.PAD + 8, NAME_Y + (T.FIELD_H - kit.cell('text')) // 2)
            self.grid_pos = builder.itemSlot.GetLocalPosition()
            builder.itemSlot.SetPosition(self.grid_pos[0], GRID_Y)
            grid_bottom = GRID_Y + builder.itemSlot.GetHeight()
            self.note = uir1.Text(board, '', BUILDER_W // 2, grid_bottom + NOTE_GAP, kit.font('text_s'), T.INK_DIM,
                                  align='center', valign='top')
            uir1.Fit(self.note, Tr('Nápis uvidí ostatní nad tebou.', 'Others see the sign above you.'), iw)
            y = BUILDER_H - T.PAD - T.BTN_H
            half = (iw - BUTTON_GAP) // 2
            self.ok = uir1.Button(board, kit, T.PAD, y, half, Tr('Otevřít', 'Open'), primary=True,
                                  event=builder.OnOk)
            self.close = uir1.Button(board, kit, T.PAD + half + BUTTON_GAP, y, iw - half - BUTTON_GAP,
                                     close.GetText() or Tr('Zavřít', 'Close'), event=builder.OnClose)
            ok.Hide()
            close.Hide()
            builder.itemSlot.SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0)
        except Exception:
            self.Restore()
            raise

    def Restore(self):
        if self.builder is None:
            return
        for name in ('well', 'note', 'ok', 'close'):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.Hide()
                if hasattr(widget, 'callback'):
                    widget.callback = None
        self.name_line.SetParent(self.name_parent)
        self.name_line.SetPosition(*self.name_pos)
        uir1.SetFont(self.name_line, 'Tahoma:12', self.name_line.GetText())
        self.name_slot.Show()
        self.builder.itemSlot.SetSlotBaseImage(ORIGINAL_SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
        if getattr(self, 'grid_pos', None):
            self.builder.itemSlot.SetPosition(*self.grid_pos)
        for original in self.originals:
            original.Show()
        self.skin.Restore()
        self.skin.Destroy()
        self.builder = None

    Destroy = Restore


# --------------------------------------------------------------------------- the sign above the seller
SIGN_H = 22
SIGN_PAD = 10


def SkinSign(board):
    """R1 panel + the kit text font on one PrivateShopAdvertisementBoard after its Open(vid, text); returns the skin."""
    kit = uir1.Kit()
    text = board.textLine.GetText()
    uir1.SetFont(board.textLine, kit.font('text_s'), text)
    board.textLine.SetPackedFontColor(T.INK)
    w = uir1.TextWidth(board.textLine) + 2 * SIGN_PAD
    ui.Window.SetSize(board, w, SIGN_H)          # below the 32 px minimum of ThinBoard.SetSize (its corners hide)
    return uir1.BoardSkin(board, kit, kind='panel', w=w, h=SIGN_H)
