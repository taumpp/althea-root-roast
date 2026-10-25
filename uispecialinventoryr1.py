# -*- coding: utf-8 -*-
"""Úschovna (the storage window "Sklad", uispecialinventory.SpecialInventoryWindow with the safebox and the item
mall inside it) in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md), drawn INTO the original window.

The window keeps its 272 px width (176 for the old 5 x 9 safebox layout), its 8 x 8 grid, its eight categories and
every function. R1, variant V2 "Stránky v hlavičce" (owner choice 2026-10-08, ui-navrhy-r1/kolo-20261008-
specialni-inventar):
  * frame and header (the title follows the category as before: Sklad, Úschovna předmětů, Knihy, ...), the X;
  * the search row: Seskupit and Seřadit as small R1 buttons with the original glyphs, the R1 search field around
    the original EditLine (the same filter, the same Esc), the clear cross - the field is shorter: the pages I - III
    sit right of it as one R1 segment (the selected page a dark well with the red line under its label);
  * the 8 x 8 grid (and the safebox / mall grids, the search result grid) with the R1 item slot C (uir1.SLOT_CELL,
    team choice 2026-10-07) as the slot base image: the engine grid and the items stay where they were;
  * under the grid only the eight categories in ONE row, today's grey icons scaled to 31 px on the grid columns
    (CButton::SetScale), the selected one with the vein under it; no category background;
  * so the window is COMPACT_DROP (65) px lower (the top stays where it was).
The old 5 x 9 safebox layout (176 px wide: no room for one row of eight) keeps the earlier R1 arrangement: the pages
under the grid, the categories in two rows on their background, the full window height.

The original page tabs and the search row stay the window's attributes through small adapters with the calls the
window makes (Down / SetUp / Show / Hide / SetEvent, Show / Hide / GetWidth / SetPosition), so every original
method runs unchanged. Settings -> "Starý vzhled" keeps the original window (the uiscript is unchanged: the pages
under the grid, the categories in two rows, 272 x 431); a failure while building traces to syserr and keeps the
original look.
"""
import ui
import wndMgr

import uir1
import uir1obchodyart as A
import uir1tokens as T

ORIGINAL_SLOT_BASE = 'd:/ymir work/ui/public/Slot_Base.sub'
ORIGINAL_CAT_BACKGROUND = 'd:/ymir work/ui/game/special_inventory/cat_background.tga'
SEARCH_Y = 33
GLYPH_BUTTON_W = 24
GAP = 4
CATEGORY_SHIFT = 4      # two-row layout: the category background 4 px lower (room for the 24 px page segment)
VEIN_INSET = 3          # the selected category's vein a little narrower than its button

# V2 "Stránky v hlavičce" (the compact layout of the 272 px window)
COMPACT_MIN_WIDTH = 272     # the 8 x 8 grid fits: one row of eight categories under it
COMPACT_DROP = 65           # the window this much lower than the uiscript's 431 px
CAT_SIZE = 31               # a category icon scaled from 34 x 32 to 31 x 31
CAT_STEP = 32               # on the grid columns
CAT_GAP = 4                 # grid bottom -> the category row
CAT_ROW_H = CAT_SIZE + 4    # the row window: the icons and the vein under the selected one
PAGE_CELL_W = 22            # I, II (IV, V)
PAGE_CELL_W_WIDE = 26       # III
CATEGORY_NAMES = ('SkillBookButton', 'UpgradeItemsButton', 'stoneButton', 'GiftBoxButton', 'SwitchButton',
                  'SafeboxButton', 'MallButton', 'ConsumableButton')


def Tr(czech, english):
    return uir1.Tr_(czech, english)


def Locale(module, key, fallback):
    """A client string (localeInfo / uiScriptLocale) or the fallback."""
    try:
        value = getattr(__import__(module), key, None)
    except ImportError:
        value = None
    return value if isinstance(value, str) and value and value != key else fallback


def Glyph(parent, path, x, y):
    """An original glyph (the builder's R1 art) on an R1 button, not pickable: the button takes the click."""
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(path)
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


class PageCell(uir1.SegmentCell):
    """One page (I / II / III) of the page segment, with the original page tooltip as the R1 hover hint."""
    tooltip = ''

    def OnMouseOverIn(self):
        uir1.SegmentCell.OnMouseOverIn(self)
        if self.tooltip:
            uir1.ShowHint(self.segment.kit, self, self.tooltip)

    def OnMouseOverOut(self):
        uir1.SegmentCell.OnMouseOverOut(self)
        if self.tooltip:
            uir1.HideHint()


class PageTabs(ui.Window):
    """The pages as one R1 segment (24 px, the height of the search field): first / mid / last cells."""

    def __init__(self, parent, kit, labels, tooltips):
        ui.Window.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.height = T.SEG_H                       # uir1.SegmentCell sizes its cell by the segment's height
        self.font = kit.font('text_s')              # the page numbers in the main inventory's font (uiinventoryr1)
        self.on_hover = None
        self.events = [None] * len(labels)
        n = len(labels)
        self.cells = []
        x = 0
        for index, label in enumerate(labels):
            pos = 'single' if n == 1 else ('first' if index == 0 else ('last' if index == n - 1 else 'mid'))
            cell = PageCell(self, index, pos, label)
            cell.tooltip = tooltips[index]
            w = PAGE_CELL_W_WIDE if len(label) > 2 else PAGE_CELL_W
            cell.Place(x, w)
            x += w
            self.cells.append(cell)
        self.w = x
        self.SetSize(self.w, T.SEG_H)
        self.Show()

    def Select(self, index):
        event = self.events[index]
        if event:
            event()

    def SyncShown(self):
        """The segment window itself shown while any page is (all are hidden in the legacy safebox)."""
        if any(cell.IsShow() for cell in self.cells):
            self.Show()
        else:
            self.Hide()


class TabAdapter(object):
    """Stands in for one original page radio button (Inventory_Tab_0x): one cell of the page segment."""

    def __init__(self, tabs, index):
        self.tabs, self.index = tabs, index
        self.cell = tabs.cells[index]

    def SetEvent(self, event, *args):
        self.tabs.events[self.index] = (lambda: event(*args)) if args else event

    def Down(self):
        self.cell.selected = True
        self.cell.paint()

    def SetUp(self):
        self.cell.selected = False
        self.cell.paint()

    def IsDown(self):
        return self.cell.selected

    def Show(self):
        self.cell.Show()
        self.tabs.SyncShown()

    def Hide(self):
        self.cell.Hide()
        self.tabs.SyncShown()

    def IsShow(self):
        return self.cell.IsShow()


def ScaleButton(button, w, h, natural):
    """A category button at w x h (natural = its texture size): CButton::SetScale scales its four visuals and
    multiplies the CURRENT window size, so the scale is absolute from the natural size and the size is set exactly
    after it (no float truncation to 30 px). w x h == natural brings the button back to its texture."""
    nw, nh = natural
    wndMgr.SetScale(button.hWnd, float(w) / nw, float(h) / nh)
    button.SetSize(int(w), int(h))


class SearchRowAdapter(object):
    """Stands in for the original search bar base image: the window shows / hides / centres it."""

    def __init__(self, skin):
        self.skin = skin

    def Show(self):
        for widget in self.skin.search_widgets:
            widget.Show()

    def Hide(self):
        for widget in self.skin.search_widgets:
            widget.Hide()

    def IsShow(self):
        return self.skin.field.IsShow()

    def GetWidth(self):
        return self.skin.w

    def GetLocalPosition(self):
        return 0, SEARCH_Y

    def SetPosition(self, x, y):
        pass                                    # the row follows the window width (Skin.Resize)


class StorageSkin(object):
    """R1 into one SpecialInventoryWindow after its __LoadWindow; ``tab_events`` are the page callbacks."""

    def __init__(self, window, tab_events, on_stack=None, on_sort=None, on_search_update=None):
        self.window = window
        self.kit = kit = uir1.Kit()
        board = window.board
        self.w = window.GetWidth()
        self.originals = dict(tabs=list(window.inventoryTab), search=window.wndSearchBarBase)
        self.search_widgets = []
        self.vein = None
        self.field = None
        self.row = None
        self.selected = None
        self.compact = False
        self.base_h = window.GetHeight()
        self.skin = uir1.BoardSkin(board, kit, window.titleName.GetText(), on_close=window.Close,
                                   hide=(window.titleBar,))
        try:
            # search row: the original EditLine moves into the R1 field (a new parent: it draws above the well)
            edit = getattr(window, 'wndSearchEdit', None)
            if edit is not None and window.wndSearchBarBase is not None:
                self.edit_parent = window.wndNameSlot
                self.edit_pos = edit.GetLocalPosition()
                self.stack = uir1.Button(board, kit, 0, SEARCH_Y + 1, GLYPH_BUTTON_W, '', small=True, event=on_stack)
                self.sort = uir1.Button(board, kit, 0, SEARCH_Y + 1, GLYPH_BUTTON_W, '', small=True, event=on_sort)
                for button, name, tip in ((self.stack, 'glyph_stack.png', Locale('localeInfo', 'INVENTORY_STACK_TOOLTIP',
                                                                                  Tr('Seskupit', 'Stack'))),
                                          (self.sort, 'glyph_sort.png', Locale('uiScriptLocale',
                                                                               'INVENTORY_ITEM_SORT_TOOLTIP',
                                                                               Tr('Seřadit', 'Sort')))):
                    gw, gh = A.SIZES[name]
                    button.glyph = Glyph(button, A.ROOT + name, (GLYPH_BUTTON_W - gw) // 2, (T.BTN_H_S - gh) // 2)
                    button.SetToolTipText(tip)
                self.has_sort = on_stack is not None
                self.field = uir1.SearchField(board, kit, 0, SEARCH_Y, 100, edit=edit, max_len=55,
                                              on_clear=on_search_update)
                hint = getattr(edit, 'infoMsg', '') or Tr('Hledat předměty...', 'Search items...')
                self.field.SetHint(hint)
                self.search_widgets = [self.stack, self.sort, self.field] if self.has_sort else [self.field]
                if not self.has_sort:
                    self.stack.Hide()
                    self.sort.Hide()
                self.tooltips = (window.btnSearchStack, window.btnSearchSort)
                shown = window.wndSearchBarBase.IsShow()
                window.wndSearchBarBase.Hide()
                window.wndSearchBarBase = SearchRowAdapter(self)
                if not shown:
                    window.wndSearchBarBase.Hide()
            # pages: one R1 segment (in the header right of the search field, or under the grid when narrow)
            self.tab_y = window.inventoryTab[0].GetLocalPosition()[1] - 2
            labels = [('I', 'II', 'III', 'IV', 'V')[index] for index in range(len(self.originals['tabs']))]
            tips = [Locale('uiScriptLocale', 'INVENTORY_PAGE_BUTTON_TOOLTIP_%d' % (index + 1), '')
                    for index in range(len(labels))]
            self.pages = PageTabs(board, kit, labels, tips)
            self.tabs = []
            for index, original in enumerate(self.originals['tabs']):
                adapter = TabAdapter(self.pages, index)
                adapter.SetEvent(tab_events[index])
                if index == window.inventoryPageIndex:
                    adapter.Down()
                adapter.Show() if original.IsShow() else adapter.Hide()
                original.Hide()
                self.tabs.append(adapter)
            window.inventoryTab = self.tabs
            # categories: two rows on the recoloured background, or one row of 31 px icons (compact)
            background = window.categoryBackground
            self.cat_pos = background.GetLocalPosition()
            self.categories = [getattr(window, name) for name in CATEGORY_NAMES]
            self.cat_origin = [(button.GetLocalPosition(), (button.GetWidth(), button.GetHeight()))
                               for button in self.categories]
            background.SetPosition(self.cat_pos[0], self.cat_pos[1] + CATEGORY_SHIFT)
            background.LoadImage(A.CAT_BACKGROUND)
            self.cat_parent = background
            self._MakeVein()
            grid = window.wndItem
            self.grid_x = grid.GetLocalPosition()[0]
            self.grid_bottom = grid.GetLocalPosition()[1] + grid.GetHeight()
            self.SetSlotBases(uir1.SLOT_CELL)
            self.Resize(self.w)
        except Exception:
            self.Restore()
            raise

    # ------------------------------------------------------------------ used by the window
    @staticmethod
    def SlotBase():
        return uir1.SLOT_CELL

    def SetSlotBases(self, path):
        window = self.window
        grids = [getattr(window, 'wndItem', None), getattr(window, 'wndItemSRC', None)]
        for provider in (getattr(window, 'safebox', None), getattr(window, 'mall', None)):
            try:
                grids.append(getattr(provider, 'wndItem', None) if provider else None)
            except ReferenceError:
                pass
        for grid in grids:
            if grid:
                grid.SetSlotBaseImage(path, 1.0, 1.0, 1.0, 1.0)

    def SetTitle(self, title):
        self.skin.SetTitle(title)

    def SetCategory(self, button):
        """The vein under the selected category button (bottom aligned in the uiscript: CWindow::UpdateRect puts it
        at parent height - y, in the background and in the compact row alike)."""
        if self.vein is None:
            return
        self.selected = button
        x, y = button.GetLocalPosition()
        top = self.cat_parent.GetHeight() - y
        self.vein.SetWidth(button.GetWidth() - 2 * VEIN_INSET)
        self.vein.SetPosition(x + VEIN_INSET, top + button.GetHeight() - T.VEIN_ROW)
        self.vein.Show()

    def _MakeVein(self):
        """The vein made after the category buttons of its parent (children draw in the order they were added)."""
        if self.vein is not None:
            self.vein.Hide()
        self.vein = uir1.Vein(self.cat_parent, 0, 0, 34 - 2 * VEIN_INSET)
        self.vein.Hide()

    def _SetCompact(self, compact):
        """V2: the eight categories in one row of 31 px icons under the grid (a new row window, the buttons
        re-parented into it bottom aligned as in the uiscript); otherwise back on the two-row background."""
        if compact == self.compact:
            return
        self.compact = compact
        background = self.window.categoryBackground
        if compact:
            self.row = ui.Window()
            self.row.SetParent(self.window.board)
            self.row.SetSize(len(self.categories) * CAT_STEP, CAT_ROW_H)
            self.row.Show()
            for index, button in enumerate(self.categories):
                button.SetParent(self.row)
                ScaleButton(button, CAT_SIZE, CAT_SIZE, self.cat_origin[index][1])
                button.SetPosition(index * CAT_STEP, CAT_ROW_H)
            background.Hide()
            self.cat_parent = self.row
        else:
            for button, (pos, natural) in zip(self.categories, self.cat_origin):
                button.SetParent(background)
                ScaleButton(button, natural[0], natural[1], natural)
                button.SetPosition(*pos)
            background.Show()
            self.cat_parent = background
            if self.row is not None:
                self.row.Hide()
                self.row = None
        self._MakeVein()
        if self.selected is not None:
            self.SetCategory(self.selected)

    def Resize(self, w):
        window = self.window
        self.w = int(w)
        self._SetCompact(self.w >= COMPACT_MIN_WIDTH)
        h = self.base_h - COMPACT_DROP if self.compact else self.base_h
        if window.GetHeight() != h:
            window.SetSize(self.w, h)
            window.board.SetSize(self.w, h)
            window.UpdateRect()             # CWindow::SetSize keeps the children's rects (the centred loading image)
        self.skin.Resize(self.w, h)
        margin = T.PAD - 4
        if self.compact:
            pages_x, pages_y = self.w - margin - self.pages.w, SEARCH_Y
            self.row.SetPosition(self.grid_x, self.grid_bottom + CAT_GAP)
        else:
            pages_x, pages_y = (self.w - self.pages.w) // 2, self.tab_y
            background = window.categoryBackground
            background.SetPosition(background.GetLocalPosition()[0], self.cat_pos[1] + CATEGORY_SHIFT)
        self.pages.SetPosition(pages_x, pages_y)
        if self.field is not None:
            x = margin
            self.stack.SetPosition(x, SEARCH_Y)
            self.sort.SetPosition(x + GLYPH_BUTTON_W + GAP, SEARCH_Y)
            fx = x + 2 * (GLYPH_BUTTON_W + GAP) if self.has_sort else x
            right = pages_x - GAP if self.compact else self.w - margin
            self.field.SetPosition(fx, SEARCH_Y)
            self._ResizeField(right - fx)

    def _ResizeField(self, w):
        field = self.field
        field.w = int(w)
        field.SetSize(field.w, field.h)
        edit = field.edit
        lead, trail = T.ICON + 6, T.CLEAR + 8
        edit.SetSize(field.w - 2 * field.pad - lead - trail, edit.GetHeight())
        hit = T.CLEAR + 6
        field.clear.SetPosition(field.w - hit - 3, (field.h - hit) // 2)
        field.paint()

    # ------------------------------------------------------------------ back to the original look
    def Restore(self):
        window = self.window
        if window is None:
            return
        tabs = getattr(self, 'tabs', [])
        for adapter, original in zip(tabs, self.originals['tabs']):
            if adapter.IsShow():
                original.Show()
            original.Down() if adapter.IsDown() else original.SetUp()
        if getattr(self, 'pages', None) is not None:
            self.pages.events = [None] * len(self.pages.events)
            self.pages.Hide()
        window.inventoryTab = self.originals['tabs']
        if self.field is not None:
            shown = self.field.IsShow()
            for widget in self.search_widgets:
                widget.Hide()
            edit = self.field.edit
            edit.SetParent(self.edit_parent)
            edit.SetPosition(*self.edit_pos)
            uir1.SetFont(edit, 'Tahoma:12', edit.GetText())
            self.field.on_clear = None
            self.stack.callback = self.sort.callback = None
            window.wndSearchBarBase = self.originals['search']
            if shown:
                window.wndSearchBarBase.Show()
        if getattr(self, 'cat_origin', None):
            self._SetCompact(False)
        if self.vein is not None:
            self.vein.Hide()
        if getattr(self, 'cat_pos', None):
            window.categoryBackground.SetPosition(*self.cat_pos)
            window.categoryBackground.LoadImage(ORIGINAL_CAT_BACKGROUND)
        if window.GetHeight() != self.base_h:
            window.SetSize(window.GetWidth(), self.base_h)
            window.board.SetSize(window.GetWidth(), self.base_h)
            window.UpdateRect()
        self.SetSlotBases(ORIGINAL_SLOT_BASE)
        self.skin.Restore()
        self.skin.Destroy()
        self.window = None

    Destroy = Restore
