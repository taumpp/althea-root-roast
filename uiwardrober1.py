# -*- coding: utf-8 -*-
"""Šatník (Obchod -> Šatník, the costume preview on the character) in the R1 look, variant C "jedna řada záložek,
karty s cenou" (owner's choice 9. 10. 2026, preview round ui-navrhy-r1/kolo-20261009-satnik).

WardrobeR1Window is the original uiwardrobe.WardrobeWindow with a new face: the catalogue, the filters, the offers,
the set, the render target, the purchase and every event handler are the original methods; only the widgets and the
methods that draw them are R1 ones.

* the R1 frame and the header "ŠATNÍK" like POSTAVA (uir1.BoardSkin on the window's own BoardWithTitleBar: the title
  bar stays the invisible drag handle), the plain X;
* left: the 3D preview (render target 4) on the night lake of the Mount window, ‹ › rotate it, a drag rotates, the
  wheel zooms;
* right: the category tabs Vše | Tělo | Účes | Zbraň | Šerpa | Efekty in one row (the chosen one = the lighter cell
  and ivory text, no red line - PRAVIDLA-UI 3), the search "Hledat název nebo číslo", Zdroj: [x] IS obchod
  [x] Ve hře (both = Vše; the last ticked one cannot be cleared), the cards 64 x 96 (8 x 3 = 24 a page) with the
  icon at its native size and the price under it (coin + number, "ve hře" for a game costume), a piece of the set
  with the light outline, the pages ‹ 1 2 3 4 5 › (the wheel over the cards pages them);
* the bottom bar: Sestava (6 tall slots, a right click takes the piece off), Cena IS položek v sestavě, Reset (its
  hint C "Reset - Sundá z náhledu všechny kousky sestavy") | the chosen piece, "IS obchod · 249 mincí" and the
  primary Koupit (only for an IS piece; the shop's purchase dialog asks, Ano on the left).

Tahoma 12 for every text, tab, button and price (PRAVIDLA-UI "Písmo textu", 9. 10. 2026); the title in the R1
title font. Every widget is made once: the 24 cards are a pool that a page fills, a resolution change only moves and
resizes them. The window fits the game window (Fit: 1366 x 768 and half of 1920 x 1080 = 960 x 1080 at full size; a
narrower screen gets a narrower preview first, then fewer card columns, a lower one two rows) and comes back on
screen after a resolution change (polled in OnUpdate, two int reads a frame while the window is shown).

Settings -> "Starý vzhled" keeps the original window (uiwardrobe.CreateWindow); when building or redrawing the R1
window raises, the failure is traced to syserr (uir1.TraceFailure) and the original window takes over.
"""
import item
import renderTarget
import ui
import wndMgr

import uikit
import uir1
import uir1layout as L
import uir1tokens as T
import uiwardrobe
import uiwheel

TAH = 'Tahoma:12'
ART = 'd:/ymir work/ui/public/althea_r1_wardrobe/'
PREVIEW_BG = 'd:/ymir work/ui/game/crimson_ember/mount_system/k1/preview_254x266.png'   # the Mount window's lake
COIN = u'|Ikey/mini_coin|i'

BASE_W, BASE_H = 940, 565
SCREEN_MARGIN = 16          # free screen edge around the window
PREVIEW_W, PREVIEW_MIN = 340, 240
COLS, ROWS, MIN_COLS = 8, 3, 6
CARD_W, CARD_H, CARD_GAP = 64, 96, 4
CARD_ICON = (16, 6, 32, 64)  # the icon box of a card: native 32 x 64, a 32 x 96 weapon at 2/3
PAGE_SIZE = COLS * ROWS      # 24: the card pool
SLOT_W, SLOT_H, SLOT_GAP = 32, 64, 8
BAR_H = 100
PAD = 12
GAP = 8
SEARCH_W = 250
BUY_W = 130
RESET_W = 90
CHEV = 24
RENDER_H = 396          # the preview's render target at the full window size (565 px)
DETAIL_MIN = 190        # the narrowest name / price column beside Koupit


def _Signed(color):
    """wndMgr takes a signed C int; a packed ARGB >= 0x80000000 would be ignored (PRAVIDLA-UI, Kód)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


IVORY = _Signed(T.IVORY)
INK = _Signed(T.INK)
INK_DIM = _Signed(T.INK_DIM)
MUTED = _Signed(T.MUTED)
LINE = T.LINE & 0xFFFFFF


def ScreenSize():
    try:
        return int(wndMgr.GetScreenWidth()), int(wndMgr.GetScreenHeight())
    except Exception:
        return 1024, 768


def Fit(screen_w, screen_h):
    """The window for a game window of screen_w x screen_h: dict(W, H, pw (preview width), cols, rows). The full
    940 x 565 when it fits within SCREEN_MARGIN; a narrower screen takes the room from the preview first (down to
    PREVIEW_MIN), then whole card columns (down to MIN_COLS); a lower screen shows two rows of cards."""
    avail_w = int(screen_w) - 2 * SCREEN_MARGIN
    avail_h = int(screen_h) - 2 * SCREEN_MARGIN
    cols, rows, pw, w, h = COLS, ROWS, PREVIEW_W, BASE_W, BASE_H
    if avail_w < w:
        pw = max(PREVIEW_MIN, PREVIEW_W - (w - avail_w))
        w -= PREVIEW_W - pw
        while w > avail_w and cols > MIN_COLS:
            cols -= 1
            w -= CARD_W + CARD_GAP
    if avail_h < h:
        rows = 2
        h -= CARD_H + CARD_GAP
    return dict(W=w, H=h, pw=pw, cols=cols, rows=rows)


def PriceText(price, unit=True):
    """The price like the Item Shop: the coin and the number ("249 mincí" with the unit)."""
    return u'%s %d%s' % (COIN, int(price), u' minc\u00ed' if unit else u'')


def _Guard(method):
    """An R1 handler: a failure is traced and the original window takes over (WardrobeR1Window.Fail)."""
    def run(self, *args):
        try:
            return method(self, *args)
        except Exception:
            if getattr(self, 'opening', False):
                # Unwind the original Open before replacing its shared render target.
                raise
            self.Fail()
            return None
    run.__name__ = method.__name__
    run.__doc__ = method.__doc__
    return run


def _Base(name):
    """The original method of uiwardrobe.WardrobeWindow as a plain function (Python 2 and 3)."""
    return uiwardrobe.WardrobeWindow.__dict__[name]


class TahomaKit(uir1.Kit):
    """Tahoma 12 for every text, button and tab (PRAVIDLA-UI "Písmo textu", 9. 10. 2026); the window title stays the
    R1 title like POSTAVA."""

    def font(self, role='text'):
        return uir1.Kit.font(self, 'title' if role == 'title' else 'tahoma')


def _Text(parent, x, y, color=INK, align='left'):
    """A Tahoma 12 line, top-aligned (the font is set before any text: no SetFont over a shown text)."""
    return uikit.Text(parent, u'', x, y, TAH, color, align, 'top')


# --------------------------------------------------------------------------- controls
class TabCell(uikit.Interactive):
    """One cell of the category row: the chosen cell = the lighter segment cell and ivory text, the mouse only
    brightens the text of the others (no red line)."""

    def __init__(self, tabs, index, pos, text):
        uikit.Interactive.__init__(self)
        self.tabs, self.index, self.pos = tabs, index, pos
        self.selected = False
        self.w = 0
        self.SetParent(tabs)
        self.ops = uir1.Ops(self, L.segment_cell(pos, 'normal', 16))     # images before the label (drawn under it)
        self.label = _Text(self, 0, 0, INK_DIM, 'center')
        self.label.SetText(text)
        self.Show()

    def Place(self, x, w):
        self.w = int(w)
        self.SetPosition(int(x), 0)
        self.SetSize(self.w, T.SEG_H)
        self.label.SetPosition(self.w // 2, uir1.CellTop(T.SEG_H, TAH) - 1)
        self.paint()

    def paint(self):
        if not self.w:
            return
        self.ops.Apply(L.segment_cell(self.pos, 'hover' if self.selected else 'normal', self.w))
        self.label.SetPackedFontColor(IVORY if self.selected else (INK if self.hovered else INK_DIM))

    def click(self):
        if self.tabs.callback:
            self.tabs.callback(self.tabs.values[self.index])


class Tabs(ui.Window):
    def __init__(self, parent, options, event):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.values = [value for value, unused in options]
        self.callback = event
        n = len(options)
        self.cells = [TabCell(self, i, 'first' if i == 0 else ('last' if i == n - 1 else 'mid'), label)
                      for i, (unused, label) in enumerate(options)]
        self.Show()

    def Place(self, x, y, w):
        n = len(self.cells)
        base = int(w) // n
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), T.SEG_H)
        cx = 0
        for i, cell in enumerate(self.cells):
            cw = base if i < n - 1 else int(w) - base * (n - 1)
            cell.Place(cx, cw)
            cx += cw

    def SetValue(self, value):
        for cell, v in zip(self.cells, self.values):
            if (v == value) != cell.selected:
                cell.selected = v == value
                cell.paint()

    def Destroy(self):
        self.callback = None
        for cell in self.cells:
            cell.tabs = None
        self.cells = []


class ChevronButton(uir1.Button):
    """A small R1 button with an R1 chevron (the pages, the rotation)."""

    def __init__(self, parent, kit, direction, event):
        self.direction = direction
        self.chevron = None
        uir1.Button.__init__(self, parent, kit, 0, 0, CHEV, '', small=True, event=event)
        self.chevron = uir1.Image(self, uir1.ChevronPath(direction), (CHEV - T.CHEVRON) // 2,
                                  (self.h - T.CHEVRON) // 2)
        self.paint()

    def paint(self):
        uir1.Button.paint(self)
        if self.chevron is not None:
            state = self.state()
            state = state if state in ('disabled', 'hover') else 'normal'
            if getattr(self, 'chevron_state', None) != state:
                self.chevron_state = state
                self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath(self.direction, state))


class PageCell(uikit.Interactive):
    W = 22

    def __init__(self, parent, event):
        uikit.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetSize(self.W, L.button_height(True))
        # the images of the current page made now (before the label: drawn under it; not on the first page change)
        self.ops = uir1.Ops(self, self.CurrentOps())
        self.ops.Apply([])
        self.label = _Text(self, self.W // 2, uir1.CellTop(L.button_height(True), TAH) - 1, INK_DIM, 'center')
        self.page = 0
        self.current = False
        self.callback = event
        self.paint()
        self.Show()

    def CurrentOps(self):
        h = L.button_height(True)
        return [(k, p, x, y + (h - T.SEG_H) // 2, w, hh)
                for k, p, x, y, w, hh in L.segment_cell('single', 'hover', self.W)]

    def Set(self, page, current):
        self.page = page
        self.current = bool(current)
        self.label.SetText(str(page + 1))
        self.paint()

    def paint(self):
        self.ops.Apply(self.CurrentOps() if self.current else [])
        self.label.SetPackedFontColor(IVORY if self.current else (INK if self.hovered else INK_DIM))

    def click(self):
        if self.callback and not self.current:
            self.callback(self.page)


class Card(uikit.Interactive):
    """A catalogue card (pooled): the card texture by state, the icon, the price row."""

    def __init__(self, parent, select, over_in, over_out):
        uikit.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetSize(CARD_W, CARD_H)
        self.back = ui.ExpandedImageBox()
        self.back.SetParent(self)
        self.back.AddFlag('not_pick')
        self.back.Show()
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.Hide()
        cell = uir1.FontCell(TAH)
        self.price = _Text(self, CARD_W // 2, CARD_H - 12 - cell // 2, INK, 'center')
        self.select, self.over_in, self.over_out = select, over_in, over_out
        self.vnum = 0
        self.icon_path = None
        self.member = False
        self.shown_state = None
        self.paint()
        self.Hide()

    def Set(self, data, price, member):
        self.vnum = data['vnum']
        self.member = bool(member)
        path = data['icon']
        if path != self.icon_path:
            self.icon_path = path
            try:
                self.icon.LoadImage(path)
            except RuntimeError:
                self.icon.LoadImage(uiwardrobe.FALLBACK_ITEM_ICON)
            w, h = max(1, self.icon.GetWidth()), max(1, self.icon.GetHeight())
            x, y, bw, bh = CARD_ICON
            scale = min(1.0, bw / float(w), bh / float(h))
            self.icon.SetScale(scale, scale)
            self.icon.SetPosition(int(x + (bw - w * scale) / 2), int(y + (bh - h * scale) / 2))
        self.icon.Show()
        if price is None:
            self.price.SetText(u've h\u0159e')
            self.price.SetPackedFontColor(MUTED)
        else:
            self.price.SetText(PriceText(price, unit=False))
            self.price.SetPackedFontColor(INK)
        self.paint()
        self.Show()

    def Clear(self):
        self.vnum = 0
        self.Hide()

    def state(self):
        if self.member:
            return 'selected'
        return 'hover' if self.hovered else 'normal'

    def paint(self):
        state = self.state()
        if state != self.shown_state:
            self.shown_state = state
            self.back.LoadImage(ART + 'card_%s.png' % state)

    def click(self):
        if self.vnum and self.select:
            self.select(self.vnum)

    def OnMouseOverIn(self):
        uikit.Interactive.OnMouseOverIn(self)
        if self.vnum and self.over_in:
            self.over_in(self.vnum)

    def OnMouseOverOut(self):
        uikit.Interactive.OnMouseOverOut(self)
        if self.over_out:
            self.over_out()

    def Destroy(self):
        self.select = self.over_in = self.over_out = None
        self.vnum = 0


class LoadoutSlot(uikit.Interactive):
    """A slot of the set: the tall slot C (32 x 64), the piece's icon (fit into the slot), the item tooltip under the
    mouse, a right click takes the piece off. SetItem(vnum) like uiwardrobe.WardrobeLoadoutCard."""

    def __init__(self, parent, index, remove, over_in, over_out):
        uikit.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetSize(SLOT_W, SLOT_H)
        self.cell = uir1.SlotCell(self, 0, 0, SLOT_H)
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.Hide()
        self.slotIndex = index
        self.vnum = 0
        self.removeEvent, self.over_in, self.over_out = remove, over_in, over_out
        self.Show()

    def SetItem(self, vnum):
        self.vnum = int(vnum or 0)
        if not self.vnum:
            self.icon.Hide()
            return
        item.SelectItem(self.vnum)
        try:
            self.icon.LoadImage(item.GetIconImageFileName())
        except RuntimeError:
            self.icon.LoadImage(uiwardrobe.FALLBACK_ITEM_ICON)
        w, h = max(1, self.icon.GetWidth()), max(1, self.icon.GetHeight())
        scale = min(1.0, SLOT_W / float(w), SLOT_H / float(h))
        self.icon.SetScale(scale, scale)
        self.icon.SetPosition(int((SLOT_W - w * scale) / 2), int((SLOT_H - h * scale) / 2))
        self.icon.Show()

    def OnMouseRightButtonDown(self):
        if self.vnum and self.removeEvent:
            self.removeEvent(self.slotIndex)
        return True

    def OnMouseOverIn(self):
        uikit.Interactive.OnMouseOverIn(self)
        if self.over_in:
            self.over_in(self.slotIndex)

    def OnMouseOverOut(self):
        uikit.Interactive.OnMouseOverOut(self)
        if self.over_out:
            self.over_out()

    def Destroy(self):
        self.removeEvent = self.over_in = self.over_out = None
        self.vnum = 0


# --------------------------------------------------------------------------- the window
class WardrobeR1Window(uiwardrobe.WardrobeWindow):
    isR1 = True

    def _BuildWindow(self):
        # Hide / Close / OnUpdate / Destroy stay safe before (or after a failed) build
        self.kit = TahomaKit()
        self.fit = None
        self.screen = None
        self.pageSize = PAGE_SIZE
        self.lastData = None
        self.failed = False
        self.opening = False
        self.boardSkin = None
        self.pool = []
        self.pageCells = []
        self.r1widgets = []
        kit = self.kit
        title = uiwardrobe._Text("WARDROBE_TITLE", u"\u0160atn\u00edk")
        self.SetSize(BASE_W, BASE_H)
        self.SetTitleName(title)
        self.SetCloseEvent(self.Close)
        self.AddFlag("movable")
        self.AddFlag("float")
        self.boardSkin = uir1.BoardSkin(self, kit, title, on_close=self.Close)

        # frames first: everything made later draws above them
        self.previewPanel = uir1.Frame(self, 0, 0, 1, 1, 'panel')
        self.gridPanel = uir1.Frame(self, 0, 0, 1, 1, 'panel')
        self.barPanel = uir1.Frame(self, 0, 0, 1, 1, 'panel')

        renderWindow = ui.RenderTarget()
        renderWindow.SetParent(self)
        # The size BEFORE SetRenderTarget: the engine makes the target's texture from the window's size then
        # (CRenderTarget::SetRenderTarget -> CRenderTargetManager::CreateRenderTarget refuses 0 x 0, the index stays
        # unset and nothing is drawn - the empty preview of the first in-game test, 9. 10.). Relayout only moves it.
        renderWindow.SetSize(PREVIEW_W - 12, RENDER_H)
        renderWindow.SetRenderTarget(uiwardrobe.RENDER_TARGET_INDEX)
        renderWindow.SetMouseLeftButtonDownEvent(self._StartDrag)
        renderWindow.SetMouseLeftButtonUpEvent(self._StopDrag)
        renderWindow.SetOnRunMouseWheelEvent(self._OnMouseWheel)
        renderWindow.Show()
        self.renderWindow = renderWindow
        self.rotateLeftButton = ChevronButton(self, kit, 'left', self._RotateLeft)
        self.rotateRightButton = ChevronButton(self, kit, 'right', self._RotateRight)
        for button in (self.rotateLeftButton, self.rotateRightButton):
            if hasattr(button, 'SetOnRunMouseWheelEvent'):         # ui.Window of the game: the wheel zooms here too
                button.SetOnRunMouseWheelEvent(self._OnMouseWheel)

        self.typeTabs = Tabs(self, [(name, uiwardrobe._Text(key, fallback))
                                    for name, unused, key, fallback in self.TYPE_FILTERS], self._SelectType)
        self.search = uir1.SearchField(self, kit, 0, 0, SEARCH_W, hint=u'Hledat n\u00e1zev nebo \u010d\u00edslo',
                                       max_len=40, on_clear=self._OnSearchCleared, font=TAH)
        self.searchEdit = self.search.edit
        self.searchEdit.SetPackedFontColor(INK)
        self.searchEdit.OnIMEUpdate = self._OnSearchUpdate
        self.searchEdit.SetEscapeEvent(self.Close)
        self.sourceLabel = _Text(self, 0, 0, MUTED, 'right')
        self.sourceLabel.SetText(u'Zdroj:')
        self.shopCheck = uir1.CheckBox(self, kit, 0, 0, u'IS obchod', True, lambda: self._ToggleSource('shop'),
                                       font=TAH)
        self.gameCheck = uir1.CheckBox(self, kit, 0, 0, u'Ve h\u0159e', True, lambda: self._ToggleSource('game'),
                                       font=TAH)

        self.cardsBoard = ui.Window()
        self.cardsBoard.SetParent(self)
        self.cardsBoard.Show()
        uiwheel.Pages(self.cardsBoard, self._PreviousPage, self._NextPage)     # the wheel over the cards pages them
        self.pool = [Card(self.cardsBoard, self._SelectItem, self._OverInItem, self._OverOutItem)
                     for unused in range(PAGE_SIZE)]
        self.emptyText = _Text(self, 0, 0, MUTED, 'center')
        self.emptyText.SetText(uiwardrobe._Text("WARDROBE_EMPTY",
                                                u"\u017d\u00e1dn\u00e9 odpov\u00eddaj\u00edc\u00ed p\u0159edm\u011bty"))
        self.emptyText.Hide()
        self.previousButton = ChevronButton(self, kit, 'left', self._PreviousPage)
        self.pageCells = [PageCell(self, self._GoToPage) for unused in range(uiwardrobe.PAGE_WINDOW_SIZE)]
        self.nextButton = ChevronButton(self, kit, 'right', self._NextPage)

        self.setLabel = _Text(self, 0, 0, INK)
        self.setLabel.SetText(u'Sestava')
        for index in range(len(self.SELECTED_SLOT_TYPES)):
            self.loadoutCards.append(LoadoutSlot(self, index, self._RemoveSelectedSlot, self._OverInSelectedSlot,
                                                 self._OverOutItem))
        self.priceLabel = _Text(self, 0, 0, INK_DIM)
        self.priceLabel.SetText(u'Cena IS polo\u017eek v sestav\u011b')
        self.totalPriceText = _Text(self, 0, 0, INK)
        self.resetButton = uir1.Button(self, kit, 0, 0, RESET_W, uiwardrobe._Text("WARDROBE_RESET", u"Reset"),
                                       small=True, event=self._ResetSelection, font=TAH)
        self.resetButton.SetToolTipText(u'Reset\nSund\u00e1 z n\u00e1hledu v\u0161echny kousky sestavy')
        self.divider = uikit.Rect(self, 0, 0, 1, 1, LINE, 1.0)
        self.selectedName = _Text(self, 0, 0, INK)
        self.selectedSource = _Text(self, 0, 0, INK_DIM)
        self.buyButton = uir1.Button(self, kit, 0, 0, BUY_W, uiwardrobe._Text("WARDROBE_BUY", u"Koupit"),
                                     primary=True, event=self._BuySelected, font=TAH)
        # (a fixed font on both buttons: the kit measures a probe line on every paint otherwise)
        self.buyButton.Hide()
        self.r1widgets = [self.previewPanel, self.gridPanel, self.barPanel, self.rotateLeftButton,
                          self.rotateRightButton, self.typeTabs, self.search, self.shopCheck, self.gameCheck,
                          self.previousButton, self.nextButton, self.resetButton, self.buyButton]
        self.Relayout()
        self.SetCenterPosition()

    # ------------------------------------------------------------------ layout (no window is made here)
    def Relayout(self, screen=None):
        self.screen = screen or ScreenSize()
        fit = Fit(*self.screen)
        self.fit = fit
        W, H, pw, cols, rows = fit['W'], fit['H'], fit['pw'], fit['cols'], fit['rows']
        self.pageSize = cols * rows
        self.SetSize(W, H)
        self.boardSkin.Resize(W, H)
        top = self.boardSkin.ContentTop()
        y0 = top + GAP
        bar_y = H - PAD - BAR_H
        ph = bar_y - GAP - y0
        cell = uir1.FontCell(TAH)
        sh = L.button_height(True)

        # the preview
        self.previewPanel.SetPosition(PAD, y0)
        self.previewPanel.Resize(pw, ph)
        self.renderWindow.SetPosition(PAD + 6, y0 + 6)
        self.renderWindow.SetSize(pw - 12, ph - 12)
        ry = y0 + ph - 12 - sh
        self.rotateLeftButton.SetPosition(PAD + 12, ry)
        self.rotateRightButton.SetPosition(PAD + pw - 12 - CHEV, ry)

        # the catalogue
        cx0 = PAD + pw + 10
        cw = W - PAD - cx0
        self.typeTabs.Place(cx0, y0, cw)
        fy = y0 + T.SEG_H + GAP
        self.gameCheck.SetPosition(cx0 + cw - self.gameCheck.Width(), fy + (T.FIELD_H - self.gameCheck.h) // 2)
        sx = cx0 + cw - self.gameCheck.Width() - 18 - self.shopCheck.Width()
        self.shopCheck.SetPosition(sx, fy + (T.FIELD_H - self.shopCheck.h) // 2)
        self.sourceLabel.SetPosition(sx - 10, fy + uir1.CellTop(T.FIELD_H, TAH))
        label_w = uir1.TextWidth(self.sourceLabel)
        self.search.SetPosition(cx0, fy)
        self.search.SetWidth(max(140, min(SEARCH_W, sx - 10 - label_w - 16 - cx0)))
        self.search.clear.SetPosition(self.search.w - self.search.clear.GetWidth() - 3,
                                      self.search.clear.GetLocalPosition()[1])
        gy0 = fy + T.FIELD_H + GAP
        gh = bar_y - GAP - gy0
        self.gridPanel.SetPosition(cx0, gy0)
        self.gridPanel.Resize(cw, gh)
        grid_w = cols * (CARD_W + CARD_GAP) - CARD_GAP
        grid_h = rows * (CARD_H + CARD_GAP) - CARD_GAP
        self.cardsBoard.SetPosition(cx0 + (cw - grid_w) // 2, gy0 + 10)
        self.cardsBoard.SetSize(grid_w, grid_h)
        for index, card in enumerate(self.pool):
            card.SetPosition((index % cols) * (CARD_W + CARD_GAP), (index // cols) * (CARD_H + CARD_GAP))
        self.emptyText.SetPosition(cx0 + cw // 2, gy0 + 10 + grid_h // 2 - cell // 2)
        self.pagerCenter = cx0 + cw // 2
        self.pagerY = gy0 + gh - 10 - sh

        # the bottom bar
        self.barPanel.SetPosition(PAD, bar_y)
        self.barPanel.Resize(W - 2 * PAD, BAR_H)
        lx0 = PAD + 12
        self.setLabel.SetPosition(lx0, bar_y + 8)
        for index, slot in enumerate(self.loadoutCards):
            slot.SetPosition(lx0 + index * (SLOT_W + SLOT_GAP), bar_y + 28)
        lx = lx0 + len(self.loadoutCards) * (SLOT_W + SLOT_GAP) - SLOT_GAP + 16
        self.priceLabel.SetPosition(lx, bar_y + 8)
        self.totalPriceText.SetPosition(lx, bar_y + 46 - cell // 2)
        self.resetButton.SetPosition(lx, bar_y + BAR_H - 10 - sh)
        column = max(uir1.TextWidth(self.priceLabel), RESET_W)
        vx = lx + max(column + 24, 210 + (W - BASE_W))
        self.divider.SetPosition(vx, bar_y + 10)
        self.divider.SetSize(1, BAR_H - 20)
        dx = vx + 16
        bw = BUY_W if W >= BASE_W - 40 else 100
        self.buyButton.SetWidth(bw)
        bx = W - PAD - 16 - bw
        if bx - 12 - dx >= DETAIL_MIN:
            # the name and "IS obchod · cena" on the left, Koupit on the right (variant C)
            self.buyButton.SetPosition(bx, bar_y + (BAR_H - T.BTN_H) // 2)
            ny = bar_y + (BAR_H - (2 * cell + 4)) // 2
            self.detailWidth = bx - 12 - dx
        else:
            # a narrow window: Koupit under the two lines
            self.buyButton.SetPosition(dx, bar_y + BAR_H - 12 - T.BTN_H)
            ny = bar_y + 12
            self.detailWidth = max(40, W - PAD - 16 - dx)
        self.selectedName.SetPosition(dx, ny)
        self.selectedSource.SetPosition(dx, ny + cell + 4)
        self._ShowSelected()
        if self.filteredCatalogue is not None:
            self.currentPage = min(self.currentPage, max(0, self._GetPageCount() - 1))
            self._RefreshPage()

    def Clamp(self):
        """Never past an edge of the game window (the window is never larger than the screen minus margins)."""
        sw, sh = self.screen or ScreenSize()
        x, y = self.GetLocalPosition()
        w, h = self.GetWidth(), self.GetHeight()
        self.SetPosition(max(0, min(x, sw - w)), max(0, min(y, sh - h)))

    def OnChangeResolution(self):
        """The game window changed size: the layout for it (once) and the window centred on it again."""
        if self.fit is None or ScreenSize() == self.screen:
            return
        self.Relayout()
        self.SetCenterPosition()
        self.Clamp()

    def OnUpdate(self):
        if self.fit is not None and ScreenSize() != self.screen:
            try:
                self.OnChangeResolution()
            except Exception:
                self.Fail()
                return
        uiwardrobe.WardrobeWindow.OnUpdate(self)

    # ------------------------------------------------------------------ the original handlers, drawn in R1
    def Open(self, itemshopData):
        self.lastData = itemshopData
        self.opening = True
        try:
            if self.fit is None or ScreenSize() != self.screen:
                self.Relayout()
            # the lake BEFORE the original Open sets its brown hall: the engine keeps the first background of a
            # target (CRenderTarget::CreateBackground returns at once when it has one)
            renderTarget.SetBackground(uiwardrobe.RENDER_TARGET_INDEX, PREVIEW_BG)
            uiwardrobe.WardrobeWindow.Open(self, itemshopData)
            if self.failed:                 # a guarded handler inside Open fell back already
                self.Hide()
                return
            self._ShowSelected()
            self.Clamp()
        except Exception:
            self.Fail()
        finally:
            self.opening = False

    def _RefreshButtons(self):
        self.typeTabs.SetValue(self.currentType)
        self.shopCheck.SetOn(self.currentSource in (uiwardrobe.SOURCE_ALL, uiwardrobe.SOURCE_ITEMSHOP))
        self.gameCheck.SetOn(self.currentSource in (uiwardrobe.SOURCE_ALL, uiwardrobe.SOURCE_GAME))

    def _ToggleSource(self, which):
        """Zdroj: the two ticks map to SOURCE_ALL / ITEMSHOP / GAME; the last ticked one stays ticked."""
        shop = self.currentSource in (uiwardrobe.SOURCE_ALL, uiwardrobe.SOURCE_ITEMSHOP)
        game = self.currentSource in (uiwardrobe.SOURCE_ALL, uiwardrobe.SOURCE_GAME)
        if which == 'shop':
            shop = not shop
        else:
            game = not game
        if not shop and not game:
            self._RefreshButtons()
            return
        self._SelectSource(uiwardrobe.SOURCE_ALL if shop and game else
                           (uiwardrobe.SOURCE_ITEMSHOP if shop else uiwardrobe.SOURCE_GAME))
    _ToggleSource = _Guard(_ToggleSource)

    def _OnSearchCleared(self):
        self.currentPage = 0
        self._ApplyFilters()
    _OnSearchCleared = _Guard(_OnSearchCleared)

    def _ClearCards(self):
        for card in self.pool:
            card.Clear()
        self.cards = []

    def _GetPageCount(self):
        size = max(1, self.pageSize)
        return (len(self.filteredCatalogue) + size - 1) // size

    def _RefreshPage(self):
        start = self.currentPage * self.pageSize
        entries = self.filteredCatalogue[start:start + self.pageSize]
        members = set(self.selectedItems.values())
        members.add(self.currentVnum)
        self.cards = []
        for index, card in enumerate(self.pool):
            if index < len(entries):
                data = entries[index]
                offer = self.itemshopOffers.get(data['vnum']) if data['is_shop'] else None
                card.Set(data, self._OfferPrice(offer) if offer is not None else None, data['vnum'] in members)
                self.cards.append(card)
            else:
                card.Clear()
        self._RefreshPagination()

    def _RefreshPagination(self):
        pageCount = self._GetPageCount()
        if not pageCount:
            self.previousButton.Hide()
            self.nextButton.Hide()
            for cell in self.pageCells:
                cell.Hide()
            self.emptyText.Show()
            return
        self.emptyText.Hide()
        visible = min(uiwardrobe.PAGE_WINDOW_SIZE, pageCount)
        first = max(0, min(self.currentPage - visible // 2, pageCount - visible))
        gap = 3
        total = CHEV + gap + visible * PageCell.W + (visible - 1) * gap + gap + CHEV
        x = self.pagerCenter - total // 2
        y = self.pagerY
        self.previousButton.SetPosition(x, y)
        self.previousButton.Show()
        self.previousButton.Enable() if self.currentPage > 0 else self.previousButton.Disable()
        x += CHEV + gap
        for slot, cell in enumerate(self.pageCells):
            if slot >= visible:
                cell.Hide()
                continue
            cell.SetPosition(x, y)
            cell.Set(first + slot, first + slot == self.currentPage)
            cell.Show()
            x += PageCell.W + gap
        self.nextButton.SetPosition(x, y)
        self.nextButton.Show()
        self.nextButton.Enable() if self.currentPage + 1 < pageCount else self.nextButton.Disable()

    def _SelectItem(self, vnum):
        data = next((entry for entry in self.catalogue if entry["vnum"] == vnum), None)
        if data is None:
            return
        self._SelectAppearance(data)
        self.currentVnum = vnum
        self._ShowSelected()
        self._RefreshPage()
        self._RefreshLoadoutCards()
        self._RefreshModel()
    _SelectItem = _Guard(_SelectItem)

    def _ShowSelected(self):
        """The chosen piece: its name, "IS obchod · 249 mincí" and Koupit, or "Ve hře – jen náhled" (no Koupit)."""
        data = next((entry for entry in self.catalogue if entry["vnum"] == self.currentVnum), None) \
            if self.currentVnum else None
        if data is None:
            self.selectedName.SetText(u'')
            self.selectedSource.SetText(u'')
            self.buyButton.Hide()
            return
        uir1.Fit(self.selectedName, data["name"], getattr(self, 'detailWidth', 300))
        offer = self.itemshopOffers.get(data["vnum"]) if data["is_shop"] else None
        if offer is not None:
            self.selectedSource.SetText(u'IS obchod  \u00b7  ' + PriceText(self._OfferPrice(offer)))
            self.buyButton.Show()
        else:
            self.selectedSource.SetText(u'Ve h\u0159e \u2013 jen n\u00e1hled')
            self.buyButton.Hide()

    def _RefreshTotalPrice(self):
        total = sum(self._OfferPrice(self.itemshopOffers[vnum]) for vnum in self.selectedItems.values()
                    if vnum in self.itemshopOffers)
        self.totalPriceText.SetText(PriceText(total))

    # every other handler is the original one, guarded: a failure brings the original window
    _ApplyFilters = _Guard(_Base('_ApplyFilters'))
    _GoToPage = _Guard(_Base('_GoToPage'))
    _PreviousPage = _Guard(_Base('_PreviousPage'))
    _NextPage = _Guard(_Base('_NextPage'))
    _SelectSource = _Guard(_Base('_SelectSource'))
    _SelectType = _Guard(_Base('_SelectType'))
    _OnSearchUpdate = _Guard(_Base('_OnSearchUpdate'))
    _RemoveSelectedSlot = _Guard(_Base('_RemoveSelectedSlot'))
    _ResetSelection = _Guard(_Base('_ResetSelection'))
    _BuySelected = _Guard(_Base('_BuySelected'))

    # ------------------------------------------------------------------ the way back
    def Fail(self):
        """Building or drawing the R1 window raised: traced to syserr, the original window takes over (with the same
        offers, opened again when this one was shown); later opens in this session use the original window too."""
        if getattr(self, 'failed', False):
            return
        self.failed = True
        uir1.TraceFailure('Satnik (wardrobe)')
        uiwardrobe.MarkR1Failed()
        owner, data = self.owner, getattr(self, 'lastData', None)
        try:
            shown = bool(self.IsShow()) or bool(getattr(self, 'opening', False))
        except Exception:
            shown = True
        try:
            self.Close()
        except Exception:
            pass
        # Destroy closes the shared render target; finish it before opening the fallback.
        try:
            self.Destroy()
        except Exception:
            pass
        if owner is not None and getattr(owner, 'wardrobeWindow', None) is self:
            legacy = uiwardrobe.WardrobeWindow(owner)
            owner.wardrobeWindow = legacy
            if shown and data is not None:
                legacy.Open(data)

    def Close(self):
        self.isDragging = False
        renderTarget.SetVisibility(uiwardrobe.RENDER_TARGET_INDEX, False)
        self._OverOutItem()
        reset = getattr(self, 'resetButton', None)
        if reset is not None:
            uir1.HideHint(reset)
        self.Hide()

    def Destroy(self):
        uiwardrobe.WardrobeWindow.Destroy(self)
        for card in getattr(self, 'pool', ()):
            card.Hide()
            card.Destroy()
        self.pool = []
        for widget in getattr(self, 'r1widgets', ()):
            for name in ('Destroy',):
                try:
                    getattr(widget, name)()
                except Exception:
                    pass
        self.r1widgets = []
        for cell in getattr(self, 'pageCells', ()):
            cell.callback = None
        self.pageCells = []
        if getattr(self, 'boardSkin', None) is not None:
            self.boardSkin.Destroy()
            self.boardSkin = None
        self.lastData = None
