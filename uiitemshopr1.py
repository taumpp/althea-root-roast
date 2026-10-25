# -*- coding: utf-8 -*-
"""The Item Shop (uiitemshop.ItemShopWindow, "Obchod", /ishop data) in the R1 look ("Krvavá žíla",
docs/ALTHEA_R1_KIT.md), drawn INTO the original window. Visual only.

The window keeps its 1001 x 570 size, its lists and every function: the categories (with Šatník and the sub
category menu of Záře), the search, the offers with the item tooltips, the right-click preview, the likes, the
quantity, Koupit with its confirmation dialog, Nákupy (the history), Oblíbené položky, Nabídky, Koupit mince, the
Dračí mince and AFK body balances, the AFK obchod page, the vouchers, the HOT / NEW / OFFER ribbons, the discount
and the time-limited offers and the closed shop (ItemShopClosed). R1 changes only how they are drawn:

* the frame and the header (uir1.BoardSkin on the window's own BoardWithTitleBar: the title in Cinzel, the vein,
  the plain X; the original title bar stays as the invisible drag handle);
* the shop's own textures in R1 (tools/build_althea_r1_itemshop.py, the SAME sizes as patch_fw/.../ui/game/ishop):
  Path() gives uiitemshop the R1 file for every texture of the set, the like / dislike buttons included (outlined
  thumbs in the kit's green / red, the player's own vote filled); the item icons, the coin, the ribbons, the banner
  and the loading spinner stay the original art;
* the toolbar buttons as R1 buttons (Koupit mince the primary one), the search as the R1 search field around the
  window's own edit line, the narrow R1 scroll bars, the texts in the R1 font roles and colours;
* the offer cards: the name, the price, the quantity, the likes and Koupit laid out for the R1 fonts;
* the purchase confirmation as an R1 dialog (no header, Ano on the right with the vein, Zrušit on the left).

Every original control keeps its events and the window's methods run unchanged: uiitemshop asks Theme (the module
global uiitemshop._r1 while the R1 look is on) for texture paths, fonts and positions while it builds cards, rows and
dialogs. Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window; when building or redrawing
the R1 look raises, the failure is traced to syserr (uir1.TraceFailure) and the original look comes back.
"""
import re

import ui

import uir1
import uir1layout as L
import uir1skin
import uir1tokens as T
import itemshopcategories as categoryData

ORIGINAL_DIR = 'd:/ymir work/ui/game/ishop/'
R1_DIR = 'd:/ymir work/ui/public/althea_r1_itemshop/'

# original file name (or an R1-only state) -> the R1 file of tools/build_althea_r1_itemshop.py
FILES = {
    'bg.tga': 'bg.png', 'bg_log': 'bg_log.png', 'item_box.tga': 'card.png',
    'category_no_selected.tga': 'category_normal.png', 'category_hover': 'category_hover.png',
    'category_selected.tga': 'category_selected.png',
    'submenu_selected.tga': 'submenu_normal.png', 'submenu_selected2.tga': 'submenu_hover.png',
    'submenu_down': 'submenu_selected.png',
    'buy_0.tga': 'buy_normal.png', 'buy_1.tga': 'buy_hover.png', 'buy_2.tga': 'buy_hover.png',
    'button_buy_disabled.tga': 'buy_disabled.png',
    'count_left.tga': 'count_left.png', 'count_back.tga': 'count_back.png', 'count_right.tga': 'count_right.png',
    'purch_img.tga': 'log_row.png',
    'like.tga': 'like_normal.png', 'like_hover.tga': 'like_hover.png', 'like_active': 'like_active.png',
    'dislike.tga': 'dislike_normal.png', 'dislike_hover.tga': 'dislike_hover.png', 'dislike_active': 'dislike_active.png',
}
SIZES = {'bg.png': (981, 528), 'bg_log.png': (981, 528), 'card.png': (250, 128), 'category_normal.png': (150, 55),
         'category_hover.png': (150, 55), 'category_selected.png': (150, 55), 'submenu_normal.png': (115, 39),
         'submenu_hover.png': (115, 39), 'submenu_selected.png': (115, 39), 'buy_normal.png': (70, 27),
         'buy_hover.png': (70, 27), 'buy_disabled.png': (70, 27), 'count_left.png': (16, 17),
         'count_back.png': (20, 17), 'count_right.png': (16, 17), 'log_row.png': (927, 28),
         'afk_buy_normal.png': (170, 24), 'afk_buy_hover.png': (170, 24), 'afk_buy_pressed.png': (170, 24),
         'afk_buy_disabled.png': (170, 24), 'tool_purchase.png': (14, 14), 'tool_hot.png': (14, 14),
         'tool_offer.png': (14, 14), 'like_normal.png': (20, 21), 'like_hover.png': (20, 21),
         'like_active.png': (20, 21), 'dislike_normal.png': (20, 21), 'dislike_hover.png': (20, 21),
         'dislike_active.png': (20, 21)}

VALUE = 0xFFE8C77A          # the balances keep their gold value colour; numbers in R1 gold
BADGE = 0xFF8BBDFF          # the voucher badge keeps its blue

# the toolbar (the board's coordinates; the board lies at (10, 32) of the window): the row 0 .. 60
BAR_Y = 30                  # the middle of the toolbar row
COIN = (8, 20)
TEXT_X = 35
BALANCE_ROW = 20            # line distance of the two-line balances
BUTTON_GAP = 6
BUTTON_PAD = 12
SEARCH_W, SEARCH_MIN, SEARCH_LAST = 210, 150, 110
BOARD_W = 981
# the icons of Nákupy / Oblíbené položky / Nabídky. The locale labels carry them as inline images ("|Ikey/purchase|i
# Nákupy"): the engine draws that 18 px image on the text line with its bottom on the bottom of the line cell, so in
# the 26 px button it sits 2 px low (5 px above it, 1 px below), as tall as the plate allows and with a different ink
# width per icon. 'inline' = that (today's look), 'r1' = the label without the inline image and an R1 line icon of
# TOOL_ICONS beside it (centred with the label as one block, on the axis of the label's ink), 'text' = the label
# without the inline image. Owner's choice 2026-10-15: 'r1' (preview img-ishop-lista-A-20261015).
TOOL_ICON_MODE = 'r1'
TOOL_ICONS = {'purchasesBtn': 'tool_purchase.png', 'hotItemsBtn': 'tool_hot.png', 'offersBtn': 'tool_offer.png'}
TOOL_ICON_GAP = 6           # icon -> label
TOOL_ICON_DY = 1            # the label's ink (Tahoma caps) sits 1 px below the plate's centre
INLINE_IMAGE = re.compile(r'\|I[^|]*\|i\s*')
SCROLL_X = 962              # the narrow bars in the offer panel (the original bars at 960, 13 px wide)
SCROLL_STEP = 0.07
SCROLL_THUMB = 0.18         # the original thumb: a fixed 82 px of the 445 px bar

# the offer card (250 x 128, cards every 250 px, rows every 132 px; uiitemshop.ItemShopItem)
NAME = (60, 7)
NAME_W = 178
PRICE = (60, 29)
PRICE_ROW = 20
INFO_Y = 70                 # quantity stepper / voucher badge on the left, the remaining time on the right
INFO_RIGHT = 241
ACTION_Y = 95               # likes on the left, Koupit on the right
BUY = (171, ACTION_Y)
LIKE_X, DISLIKE_X = 60, 114
CATEGORY_ROW = 48           # the visible part of a category row (rows every 50 px)
SUB_ROW = 39
LOG_ROW = 28


def Strip(text):
    """The text without the colour prefix the categories carry ("|cfffffed Name")."""
    if text.startswith('|c') and len(text) >= 10:
        return text[10:].lstrip()
    return text


def Retext(multi, text, font=None, rgb=None, rangeText=None):
    """uiitemshop.MultiTextLine laid out again: its lines in ``font`` (new lines, so no glyphs of the old font stay),
    the old lines hidden (MultiTextLine.SetText keeps a single old line). ``rgb``: the MultiTextLine colour, floats
    0 .. 1 like ui.TextLine.SetFontColor (Rgb(packed)); (0, 0, 0) = the default colour. Later SetText calls of
    the shop make their lines in this font and colour too."""
    for line in list(multi.children):
        line.Hide()
    multi.children = []
    if font is not None:
        multi.fontName = font
    if rgb is not None:
        multi.rgb = rgb
    if rangeText is not None:
        multi.rangeText = rangeText
    if text:                                # no empty line: SetText would keep it above the next text
        multi.SetText(text)


def MultiText(multi):
    return '\n'.join(line.GetText() for line in multi.children)


def MultiWidth(multi):
    return max([uir1.TextWidth(line) for line in multi.children] or [0])


def Rgb(packed):
    """A packed colour as the floats of ui.TextLine.SetFontColor (wndMgr.SetFontColor takes 0 .. 1)."""
    return (((packed >> 16) & 255) / 255.0, ((packed >> 8) & 255) / 255.0, (packed & 255) / 255.0)


def ToolLabel(text, mode=None):
    """The toolbar label: with its inline image ('inline') or without it ('r1', 'text')."""
    if (mode or TOOL_ICON_MODE) == 'inline':
        return text
    return INLINE_IMAGE.sub('', text).strip()


class ToolButton(uir1.Button):
    """R1 button in place of an original ui.Button of the toolbar: SetEvent(func, *args) / CallEvent like ui.Button,
    Enable / Disable / Show / Hide / SetPosition of R1. ``icon``: an R1 icon (path) left of the label; the icon, the
    gap and the label are centred as one block, the icon on the axis of the label's ink."""

    def __init__(self, parent, kit, text, event, primary=False, icon=None):
        self.icon = None
        uir1.Button.__init__(self, parent, kit, 0, 0, 96, text, primary=primary)
        self.eventFunc, self.eventArgs = event, ()
        if icon:
            image = ui.ExpandedImageBox()
            image.SetParent(self)
            image.AddFlag('not_pick')
            image.LoadImage(icon)
            image.Show()
            self.icon = image
            self.paint()

    def IconRoom(self):
        return self.icon.GetWidth() + TOOL_ICON_GAP if self.icon is not None else 0

    def FitWidth(self, minimum=0, pad=12):
        uir1.Button.FitWidth(self, minimum, pad)
        if self.icon is not None:
            self.SetWidth(max(int(minimum), self.w + self.IconRoom()))
        return self.w

    def paint(self):
        uir1.Button.paint(self)
        if getattr(self, 'icon', None) is None:
            return
        room = self.IconRoom()
        x, top = self.label.GetLocalPosition()
        width = uir1.TextWidth(self.label)
        left = (self.w - room - width) // 2
        self.label.SetPosition(left + room + width // 2, top)
        down = top - uir1.CellTop(self.h, self.font)           # 1 px while pressed, like the label
        self.icon.SetPosition(left, (self.h - self.icon.GetHeight()) // 2 + TOOL_ICON_DY + down)

    def SetEvent(self, func, *args):
        self.eventFunc, self.eventArgs = func, args

    def CallEvent(self):
        if self.eventFunc:
            self.eventFunc(*self.eventArgs)

    def click(self):
        self.CallEvent()


# --------------------------------------------------------------------------- what uiitemshop asks while it builds
class Theme(object):
    """Texture paths, fonts and positions of the R1 look for the parts uiitemshop builds after the window: the offer
    cards, the category and sub category rows, the history rows and the purchase dialog."""

    def __init__(self, kit, skin=None):
        self.kit = kit
        self.skin = skin

    @staticmethod
    def Path(name):
        """The R1 file for an original Item Shop file name (or an R1-only state), else None."""
        name = name.replace(ORIGINAL_DIR, '')
        rel = FILES.get(name)
        return R1_DIR + rel if rel else None

    def Font(self, role):
        return self.kit.font(role)

    def Fail(self):
        """A redraw raised: the window goes back to the original look (uiitemshop already traced it)."""
        if self.skin is not None:
            self.skin.Restore()

    # ------------------------------------------------------------------ the offer cards
    def CardIcon(self, image):
        """Centre a non-costume icon in the card well at its native resolution."""
        x, y, width, height = L.ITEMSHOP_ICON_SLOT
        image.SetPosition(x + (width - image.GetWidth()) // 2,
                          y + (height - image.GetHeight()) // 2)

    def CardName(self, line, name):
        uir1.SetFont(line, self.Font('text_s'), '')
        line.SetPackedFontColor(T.IVORY)
        line.SetPosition(*NAME)
        uir1.Fit(line, name, NAME_W)

    def CardPrice(self, multi):
        """Before the price text is set: the R1 font, colour and line distance (new lines take them)."""
        multi.SetPosition(*PRICE)
        multi.fontName = self.Font('text_s')
        multi.rangeText = PRICE_ROW
        multi.rgb = Rgb(T.INK)

    def CardStrike(self, multi, line, text):
        """The red line over the old price of a discounted offer: measured in the R1 font (the coin icon and the
        space before the price, then the price)."""
        probe = ui.TextLine()
        probe.SetFontName(self.Font('text_s'))
        probe.SetText(u'|Ikey/mini_coin|i ')
        x = uir1.TextWidth(probe)
        probe.SetText(text)
        w = uir1.TextWidth(probe)
        line.SetScale(float(max(1, w)) / 10.0, 1.0)
        line.SetPosition(x, uir1.FontCell(self.Font('text_s')) // 2 + 1)

    def CardTime(self, line):
        uir1.SetFont(line, self.Font('text_s'))
        line.SetHorizontalAlignRight()
        line.SetPosition(INFO_RIGHT, INFO_Y)

    def CardBadge(self, line):
        uir1.SetFont(line, self.Font('text_s'))
        line.SetPackedFontColor(BADGE)
        line.SetPosition(NAME[0], INFO_Y)

    def CardBuy(self, card, button, label):
        """Koupit: the R1 primary plate (the texture), its label top-aligned and centred by position."""
        button.SetPosition(*BUY)
        label.Hide()
        font = self.Font('button_s')
        text = uir1.Text(button, label.GetText(), 35, uir1.CellTop(27, font), font, T.PRIMARY_TEXT, align='center',
                         valign='top')
        card.childrenTextLine['buyBtnText'] = text
        return text

    def CardCount(self, card):
        images, texts = card.childrenImages, card.childrenTextLine
        left, back, right = images['CountLeft'], images['CountBg'], images['CountRight']
        left.SetPosition(NAME[0], INFO_Y)
        back.SetPosition(NAME[0] + left.GetWidth(), INFO_Y)
        right.SetPosition(NAME[0] + left.GetWidth() + back.GetWidth(), INFO_Y)
        count = texts['CountText']
        font = self.Font('text_s')
        uir1.SetFont(count, font)
        count.SetPackedFontColor(T.IVORY)
        count.SetPosition(3, uir1.CellTop(back.GetHeight(), font) - 1)
        units = texts.get('CountUnits')
        if units:
            uir1.SetFont(units, font)
            units.SetPackedFontColor(T.INK_DIM)
            units.SetPosition(NAME[0] + left.GetWidth() + back.GetWidth() + right.GetWidth() + 4,
                              INFO_Y + uir1.CellTop(back.GetHeight(), font) - 1)

    def CardReactions(self, card):
        images, texts = card.childrenImages, card.childrenTextLine
        font = self.Font('text_s')
        for icon, count, x in (('likeBtn', 'likeCountText', LIKE_X), ('dislikeBtn', 'dislikeCountText', DISLIKE_X)):
            image = images[icon]
            image.SetPosition(x, ACTION_Y + 3)
            line = texts[count]
            uir1.SetFont(line, font)
            line.SetHorizontalAlignLeft()
            line.SetPackedFontColor(T.INK_DIM)
            line.SetPosition(x + image.GetWidth() + 4, ACTION_Y + 3 + uir1.CellTop(image.GetHeight(), font))

    # ------------------------------------------------------------------ categories
    def CategoryText(self, item):
        """The category name in the R1 text role, centred in the 48 px row, without the colour prefix."""
        text = item.categoryText
        if text is None:
            return
        font = self.Font('text')
        Retext(text, Strip(MultiText(text)), font, Rgb(T.INK_DIM), 17)
        text.SetPosition(item.GetWidth() // 2, uir1.CellTop(CATEGORY_ROW, font))
        for line in text.children:
            line.AddFlag('not_pick')

    def CategoryState(self, item, state):
        text = item.categoryText
        if text is None:
            return
        for line in text.children:
            line.SetPackedFontColor(T.INK_DIM if state == 'normal' else T.IVORY)

    def SubMenu(self, container, count):
        """The R1 tooltip frame of the sub category menu, made before its rows (drawn under them)."""
        frame = uir1.Frame(container, 0, 0, 115, count * SUB_ROW, 'tooltip',
                           fill_alpha=uir1.MENU_FILL_ALPHA)                 # a menu, no tooltip: near opaque
        container.r1frame = frame
        return frame

    def SubMenuText(self, multi):
        font = self.Font('text_s')
        multi.SetPosition(115 // 2, uir1.CellTop(SUB_ROW, font))
        multi.fontName = font
        multi.rgb = Rgb(T.INK)

    def SubMenuPlace(self, container, item):
        """The menu beside its category row: the row's y on the board, which lies below the header (uiitemshop
        places it by the list's board position as if the board were the window)."""
        children = self.skin.window.children
        board_x, board_y = children['boardImage'].GetLocalPosition()
        listbox = children['categoryListBox']
        list_x, list_y = listbox.GetLocalPosition()
        top = board_y + list_y + max(0, item.GetLocalPosition()[1])
        bottom = board_y + list_y + listbox.GetHeight()
        container.SetPosition(board_x + list_x + item.GetWidth() + 2, min(top, bottom - container.GetHeight()))

    # ------------------------------------------------------------------ the purchase history
    def LogText(self, line, header):
        font = self.Font('text_sb' if header else 'text_s')
        uir1.SetFont(line, font)
        line.SetPackedFontColor(T.INK_DIM if header else T.INK)
        x = line.GetLocalPosition()[0]
        line.SetPosition(x, uir1.CellTop(LOG_ROW, font) if not header else 4)

    # ------------------------------------------------------------------ the purchase dialog
    def BuyDialog(self, dialog):
        return BuyDialogSkin(dialog, self.kit)


class BuyDialogSkin(object):
    """uiitemshop.BuyWindow in R1: the R1 dialog frame (made before the text: drawn under it), the message in the
    dialog role, Ano (the main action, on the left, with the vein) and Zrušit as R1 buttons with the ui.Button API
    the shop calls (SetEvent, CallEvent). The window keeps its size rule (256 x 142 at least)."""

    def __init__(self, dialog, kit):
        self.dialog = dialog
        self.kit = kit
        self.rec = uir1skin.Recorder()
        self.frame = None
        self.buttons = {}
        try:
            for widget in list(getattr(dialog, 'Corners', None) or ()) + \
                    list(getattr(dialog, 'Lines', None) or ()) + [getattr(dialog, 'Base', None)]:
                if widget:
                    self.rec.Hide(widget)
            self.frame = uir1.DialogFrame(dialog, 0, 0, max(1, dialog.GetWidth()), max(1, dialog.GetHeight()))
        except Exception:
            self.Undo()
            raise

    def Dress(self):
        """After the original made its text and buttons."""
        import uir1dialog
        dialog = self.dialog
        text = dialog.children['buyText']
        self.rec.Call(lambda: None, lambda: Retext(text, MultiText(text), 'Tahoma:16', (0, 0, 0), 25))
        Retext(text, MultiText(text), self.kit.font('message'), Rgb(T.INK), uir1.FontCell(self.kit.font('message')) + 5)
        for name, primary in (('yesBtn', True), ('cancelBtn', False)):
            native = dialog.children[name]
            self.rec.Hide(native)
            button = uir1dialog.DialogButton(dialog, self.kit, native, primary, False)
            self.buttons[name] = button
            dialog.children[name] = button
            self.rec.Call(lambda: None, lambda name=name, native=native: dialog.children.__setitem__(name, native))
        self.Layout()

    def Layout(self):
        dialog = self.dialog
        w, h = dialog.GetWidth(), dialog.GetHeight()
        self.frame.Resize(w, h)
        text = dialog.children['buyText']
        if text.fontName != self.kit.font('message'):
            Retext(text, MultiText(text), self.kit.font('message'), Rgb(T.INK),
                   uir1.FontCell(self.kit.font('message')) + 5)
        text.SetPosition(w // 2, 22)
        y = h - T.PAD - T.BTN_H
        cancel, yes = self.buttons.get('cancelBtn'), self.buttons.get('yesBtn')
        if cancel is not None and yes is not None:
            yes.SetPosition(w // 2 - 8 - yes.GetWidth(), y)
            cancel.SetPosition(w // 2 + 8, y)

    def Undo(self):
        for button in self.buttons.values():
            button.Hide()
        if self.frame is not None:
            self.frame.Hide()
        self.rec.Undo()
        self.buttons = {}


# --------------------------------------------------------------------------- the window
class ShopSkin(object):
    """R1 into one ItemShopWindow after its LoadWindow. Every change of an original control is recorded
    (uir1skin.Recorder), so Restore() brings the original look back."""

    def __init__(self, window, on_restore=None):
        self.window = window
        self.on_restore = on_restore            # uiitemshop: forget the theme (its module global)
        self.kit = kit = uir1.Kit()
        self.theme = Theme(kit, self)
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.buttons = {}
        self.board_skin = None
        self.search = None
        self.restored = False
        self.afk_styled = []
        children = window.children
        try:
            self.board_skin = uir1.BoardSkin(window, kit, window.titleName.GetText(),
                                             on_close=ui.__mem_func__(window.Close))
            board = children['boardImage']
            self.rec.Image(board, self.theme.Path('bg.tga'), ORIGINAL_DIR + 'bg.tga')
            self._Balances()
            self._Buttons()
            self._Search()
            for key, listbox in (('categoryScrollBar', 'categoryListBox'), ('itemScrollBar', 'itemListBox'), ('PurchasesScrollBar', 'PurchasesListBox')):
                self._Scroll(key, listbox)
            for item in children['categoryListBox'].GetItems():
                self._Category(item)
            window.RefreshAfkRewards()                  # the R1 buttons take the AFK state
            self.LayoutHeader()
        except Exception:
            self.Restore()
            raise

    # ------------------------------------------------------------------ build helpers
    def _Balances(self):
        font = self.kit.font('text_s')
        for key in ('dragonCoinText', 'afkBalanceText'):
            multi = self.window.children.get(key)
            if multi is None:
                continue
            old = (multi.fontName, multi.rgb, multi.rangeText, multi.GetLocalPosition())
            self.rec.Call(lambda: None, lambda multi=multi, old=old: (
                Retext(multi, MultiText(multi), old[0], old[1], old[2]), multi.SetPosition(*old[3])))
            Retext(multi, MultiText(multi), font, Rgb(T.INK_DIM), BALANCE_ROW)

    def _Buttons(self):
        import localeInfo
        import uiafkrewardshop
        window = self.window
        labels = (('buyCoinBtn', localeInfo.ITEMSHOP_BUY_COIN, window.BuyDragonCoin, True),
                  ('purchasesBtn', localeInfo.ITEMSHOP_PURCHASES, window.PurchaseBtn, False),
                  ('hotItemsBtn', localeInfo.ITEMSHOP_HOTITEMS, window.HotItems, False),
                  ('offersBtn', localeInfo.ITEMSHOP_OFFERS, window.OfferItems, False),
                  ('afkShopButton', uiafkrewardshop.Text('AFK_SHOP_TITLE', 'AFK shop'), window.OpenAfkShop, False),
                  ('costumeExchangeBtn', localeInfo.ITEMSHOP_COSTUME_EXCHANGE_BUTTON, window.OpenCostumeExchange, False))
        board = window.children['boardImage']
        for key, text, event, primary in labels:
            native = window.children.get(key)
            if native is None:
                continue
            icon = R1_DIR + TOOL_ICONS[key] if TOOL_ICON_MODE == 'r1' and key in TOOL_ICONS else None
            button = ToolButton(board, self.kit, ToolLabel(text), ui.__mem_func__(event), primary=primary, icon=icon)
            button.FitWidth(pad=BUTTON_PAD)
            button.Show() if native.IsShow() else button.Hide()
            self.rec.Hide(native)
            self.buttons[key] = button
            self.widgets.append(button)
            window.children[key] = button
            self.rec.Call(lambda: None, lambda key=key, native=native: window.children.__setitem__(key, native))
        if 'costumeExchangeBtn' in self.buttons:                # the short label; the full name is the hint
            self.buttons['costumeExchangeBtn'].SetToolTipText(localeInfo.ITEMSHOP_COSTUME_EXCHANGE)

    def _Search(self):
        import localeInfo
        window = self.window
        children = window.children
        edit, back = children['itemSearch'], children['itemSearchBg']
        board = children['boardImage']
        overlay = getattr(edit, 'overLay', None)
        quiet = ui.TextLine()                           # the EditLine shows its overLay again on every change
        quiet.SetParent(board)
        quiet.Hide()
        self.widgets.append(quiet)
        if overlay is not None:
            self.rec.Hide(overlay)
            self.rec.Call(lambda: setattr(edit, 'overLay', quiet), lambda: setattr(edit, 'overLay', overlay))
        old_font = getattr(edit, 'r1_font', None) or 'Tahoma:14'
        old_back = getattr(edit, 'backText', None)
        x, y = edit.GetLocalPosition()
        w, h = edit.GetWidth(), edit.GetHeight()

        def undo():
            line = getattr(edit, 'backText', None)
            if line is not None and line is not old_back:
                line.Hide()
            edit.backText = old_back
            edit.SetParent(back)
            edit.SetPosition(x, y)
            edit.SetSize(w, h)
            uir1.SetFont(edit, old_font)
            edit.SetFontColor(128, 128, 128)
        self.rec.Call(lambda: None, undo)
        self.search = uir1.SearchField(board, self.kit, BOARD_W - SEARCH_W, BAR_Y - T.FIELD_H // 2, SEARCH_W,
                                       hint=Strip(localeInfo.ITEMSHOP_ITEMSEARCH_DEFAULT_TEXT), edit=edit, max_len=25,
                                       on_clear=ui.__mem_func__(window.RefreshSearch), font=self.kit.font('text_s'))
        edit.SetPackedFontColor(T.INK)
        self.widgets.append(self.search)
        self.rec.Hide(back)

    def _Scroll(self, key, listbox_key):
        window = self.window
        original = window.children[key]
        listbox = window.children[listbox_key]
        bar = uir1.ScrollBar(self.kit)
        bar.SetParent(window.children['boardImage'])
        bar.SetPosition(*(categoryData.SCROLL_POSITION if listbox_key == 'categoryListBox' else
                          (SCROLL_X, original.GetLocalPosition()[1])))
        bar.SetScrollBarSize(categoryData.SCROLL_HEIGHT if listbox_key == 'categoryListBox' else 445)
        bar.SetMiddleBarSize(SCROLL_THUMB)
        bar.SetScrollStep(original.GetScrollStep())
        bar.Show() if original.IsShow() else bar.Hide()
        self.widgets.append(bar)
        self.rec.Hide(original)
        listbox.SetScrollBar(bar)
        window.children[key] = bar
        self.rec.Call(lambda: None, lambda: (listbox.SetScrollBar(original), window.children.__setitem__(key, original)))

    def _Category(self, item):
        state = 'selected' if item.categoryIndex == getattr(self.window, 'categoryIndex', None) else 'normal'
        name = 'category_selected.tga' if state == 'selected' else 'category_no_selected.tga'
        self.rec.Image(item, self.theme.Path(name), ORIGINAL_DIR + name)
        text = item.categoryText
        if text is not None:
            old = (text.fontName, text.rgb, text.rangeText, text.GetLocalPosition(), MultiText(text))

            def undo(text=text, old=old, item=item):
                Retext(text, old[4], old[0], old[1], old[2])
                text.SetPosition(*old[3])
                for line in text.children:
                    line.AddFlag('not_pick')
            self.rec.Call(lambda: None, undo)
        self.theme.CategoryText(item)
        self.theme.CategoryState(item, state)
        self.rec.Call(item.OnRender, item.OnRender)

    # ------------------------------------------------------------------ redraws the window asks for
    def LayoutHeader(self):
        """The toolbar after uiitemshop.RefreshAfkRewards placed it: the coin, the balances, the buttons from the left,
        the search on the right (narrower when the buttons need the room)."""
        children = self.window.children
        afk = children.get('afkBalanceText')
        afk_shown = afk is not None and afk.IsShow()
        children['leftDragonCoinImage'].SetPosition(*COIN)
        coin = children['dragonCoinText']
        coin.SetPosition(TEXT_X, BAR_Y - BALANCE_ROW)
        x = TEXT_X + max(MultiWidth(coin), 70) + 18
        if afk_shown:
            afk.SetPosition(x, BAR_Y - BALANCE_ROW)
            x += max(MultiWidth(afk), 60) + 18
        buttons = [self.buttons[key] for key in ('buyCoinBtn', 'purchasesBtn', 'hotItemsBtn', 'offersBtn',
                                                 'afkShopButton', 'costumeExchangeBtn')
                   if key in self.buttons and self.buttons[key].IsShow()]
        # the labels' padding shrinks before the search does (an EXE with Tahoma, a longer translation)
        for pad in (BUTTON_PAD, 8, 5):
            end = x + sum(button.FitWidth(pad=pad) + BUTTON_GAP for button in buttons) - BUTTON_GAP
            if end + 12 <= BOARD_W - SEARCH_MIN:
                break
        for button in buttons:
            button.SetPosition(x, BAR_Y - T.BTN_H // 2)
            x += button.GetWidth() + BUTTON_GAP
        if self.search is not None:
            room = BOARD_W - (x - BUTTON_GAP + 12)
            w = max(SEARCH_LAST, min(SEARCH_W, room))
            self.search.SetWidth(w)
            self.search.SetPosition(BOARD_W - w, BAR_Y - T.FIELD_H // 2)
            self.search.clear.SetPosition(w - self.search.clear.GetWidth() - 3, self.search.clear.GetLocalPosition()[1])

    def Page(self, page):
        """The board of the catalogue (category + offer panels) or of the history (one panel)."""
        name = 'bg_log' if page == 'log' else 'bg.tga'
        board = self.window.children['boardImage']
        board.LoadImage(self.theme.Path(name))

    def StyleAfk(self, page):
        """The AFK page (uiafkrewardshop.AfkRewardShop): texts in the R1 roles, the crimson buy buttons as R1 ones."""
        if page is None or page in self.afk_styled:
            return
        self.afk_styled.append(page)
        import uicrimsoncontrols
        font, title = self.kit.font('text_s'), self.kit.font('text_b')
        first = True
        for widget in list(getattr(page, 'widgets', ())):
            if isinstance(widget, ui.TextLine):
                self.rec.Font(widget, title if first else font, T.IVORY if first else T.INK, 'Tahoma:14')
                first = False
        for card in getattr(page, 'cards', {}).values():
            for key in ('title', 'price'):
                card[key].SetPackedFontColor(T.IVORY if key == 'title' else VALUE)
            card['description'].SetPackedFontColor(T.INK_DIM)
            buy = card['buy']
            states = ('normal', 'hover', 'pressed', 'disabled')
            self.rec.Visuals(buy, [R1_DIR + 'afk_buy_%s.png' % s for s in states],
                             [uicrimsoncontrols.Visual('170x24', s) for s in states])
            line = getattr(buy, 'ButtonText', None)
            if line is not None:
                self.rec.Font(line, self.kit.font('button_s'), T.PRIMARY_TEXT, None)

    # ------------------------------------------------------------------ the way back
    def Restore(self):
        """The original look again (Settings, or after a failure)."""
        if self.restored:
            return
        self.restored = True
        if self.on_restore is not None:
            self.on_restore(self.theme)
        for widget in self.widgets:
            try:
                widget.Hide()
            except Exception:
                pass
        self.rec.Undo()
        if self.board_skin is not None:
            self.board_skin.Restore()
        try:
            self.window.RefreshAfkRewards()             # the original toolbar positions
        except Exception:
            pass
        if getattr(self.window, 'r1skin', None) is self:
            self.window.r1skin = None

    def Destroy(self):
        if self.on_restore is not None:
            self.on_restore(self.theme)
        self.on_restore = None
        for widget in self.widgets:
            try:
                widget.Hide()
            except Exception:
                pass
        self.widgets = []
        self.buttons = {}
        self.search = None
        self.theme.skin = None
