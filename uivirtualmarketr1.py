# -*- coding: utf-8 -*-
"""Virtuální tržiště in the Althea R1 look (visual only; docs/ALTHEA_R1_KIT.md).

uivirtualmarket.VirtualMarketWindow stays the window and keeps every control, hit box, event and rule (the search
check boxes stay real two-way ui.ToggleButton controls, a result row and its check box stay two hit targets of the
same selection, the category rail keeps uicrimsonember.SettingsScrollBar, the seller names stay underlined links,
the edit lines route Escape to the window). R1 changes only how they are drawn:

* the window frame and header: uir1.BoardSkin on the window's own BoardWithTitleBar (the title in Cinzel, the red
  vein under it, the plain X);
* the market's own control set in R1 (tools/build_althea_r1_trh.py, the SAME names and sizes as the original set in
  crimson_ember/virtual_market/): Path() gives uivirtualmarket the R1 file for every texture the set has, anything
  else (icons) stays the original art; the item slots (result rows, Můj obchod and the delivery / return grids) use
  the R1 item slot C (SlotBase(), uir1.SLOT_CELL);
* texts in the R1 colours (Label()), section and control texts in Noto Sans; prices, Yang and owner states keep
  their colours; the seller and text links in R1 colours, still underlined in the colour of their text;
* the scroll bars (SettingsScrollBar) drawn as the narrow R1 bar - the bar, its thumb size and mechanics unchanged;
* the search suggestion list (uivirtualmarket.SearchSuggestionDropdown) is built in R1 by the market itself: the
  opaque dark well, the thin panel outline, the R1 hover band and text colours.

The window keeps its 800 x 590 size. Settings -> "Starý vzhled" (settingslook 'legacy') shows the original window;
uivirtualmarket builds the original look when building this one raises.
"""
import grp

import uir1 as R
import uir1layout as RL
import uir1tokens as T

MARKET_DIR = 'd:/ymir work/ui/game/crimson_ember/virtual_market/'
R1_DIR = 'd:/ymir work/ui/public/althea_r1_trh/market/'
TITLE = 'Virtuální tržiště'


def _files():
    """The relative paths of the R1 market set (tools/build_althea_r1_trh.py, test_r1_virtual_market checks it)."""
    files = set()
    for role in ('market', 'owner_shop', 'deliveries', 'returns'):
        for state in ('normal', 'hover', 'pressed', 'selected', 'disabled'):
            files.add('tab/%s_%s.png' % (role, state))
    for state in ('normal', 'hover', 'pressed', 'selected', 'disabled'):
        files.update(('category/row_%s.png' % state, 'surface/result_%s.png' % state,
                      'choice/checkbox_%s.png' % state))
    for state in ('normal', 'hover', 'pressed', 'disabled'):
        for name in ('button/account_action', 'button/action', 'button/buy', 'button/create', 'button/pagination',
                     'control/search', 'control/filter'):
            files.add('%s_%s.png' % (name, state))
    files.update(('button/create_selected.png', 'button/pagination_selected.png', 'surface/result_alternate.png',
                  'surface/data_header.png', 'surface/account_header.png', 'field/search_normal.png',
                  'field/search_focused.png', 'field/search_disabled.png', 'field/account_value.png', 'field/name.png',
                  'panel/discovery.png', 'panel/workspace.png', 'panel/account_toolbar.png', 'panel/market_footer.png',
                  'panel/empty.png', 'panel/closed_shop.png'))
    return frozenset(files)


FILES = _files()
FILTERS_ORIGINAL = 'd:/ymir work/ui/public/crimson/controls/market_filters/'
FILTER_INPUTS = {'d:/ymir work/ui/public/crimson/controls/inputs/parameter_02.tga': 'filters/input_61.png',
                 'd:/ymir work/ui/public/crimson/controls/inputs/parameter_03.tga': 'filters/input_90.png',
                 'd:/ymir work/ui/public/crimson/controls/inputs/parameter_06.tga': 'filters/input_220.png',
                 'd:/ymir work/ui/public/crimson_close_01.tga': 'filters/remove_normal.png',
                 'd:/ymir work/ui/public/crimson_close_02.tga': 'filters/remove_hover.png',
                 'd:/ymir work/ui/public/crimson_close_03.tga': 'filters/remove_pressed.png'}
R1_ROOT = 'd:/ymir work/ui/public/althea_r1_trh/'


def _filter_files():
    files = set()
    for w in (100, 272, 360):
        for state in ('normal', 'hover', 'open', 'disabled'):
            files.add('dropdown_%s_%d.png' % (state, w))
    for w in (88, 100, 278):
        for state in ('normal', 'hover', 'selected', 'disabled'):
            files.add('selection_row_%s_%d.png' % (state, w))
    return frozenset(files)


FILTER_FILES = _filter_files()
# The advanced filter dialog (root/uimarketfilters.py): text colours and the action button families.
FILTER_COLORS = {0xffeadfc8: T.INK, 0xffb4aa98: T.INK_DIM, 0xffdab16c: T.IVORY}
FILTER_ACTIONS = {'100x21': R1_ROOT + 'filters/action_100x21', '170x24': R1_DIR + 'button/create'}

# Original packed colours of the market texts -> R1 (prices / Yang / owner states use SetFontColor and stay).
COLORS = {
    0xffeadfc8: T.INK,          # cream body text, headers
    0xffd8cbb5: T.INK,          # check box labels, search title
    0xff9e8c7c: T.INK_DIM,      # "Kategorie", details, active sellers
    0xfff7c81c: T.IVORY,        # gold titles (empty state, sidebar)
    0xffffd500: T.IVORY,        # closed shop title
    0xffd0d0d0: T.INK_DIM,      # owner state / lease before their value colour
}
BUTTON_FONT = 'text_s'


def _color(packed):
    return (((packed >> 16) & 255) / 255.0, ((packed >> 8) & 255) / 255.0, (packed & 255) / 255.0, 1.0)


LINK_NORMAL = grp.GenerateColor(*_color(T.INK))
LINK_HOVER = grp.GenerateColor(*_color(T.RED_HI))


class Theme(object):
    """What uivirtualmarket asks while it builds and redraws in the R1 look."""

    def __init__(self, kit=None):
        self.kit = kit or R.Kit()
        self.link_normal, self.link_hover = LINK_NORMAL, LINK_HOVER

    # paths -------------------------------------------------------------------------------------------------
    @staticmethod
    def Path(path):
        """The R1 file for an original market texture path, else None (the original stays)."""
        if path.startswith(MARKET_DIR) and path[len(MARKET_DIR):] in FILES:
            return R1_DIR + path[len(MARKET_DIR):]
        if path.startswith(FILTERS_ORIGINAL) and path[len(FILTERS_ORIGINAL):] in FILTER_FILES:
            return R1_ROOT + 'filters/' + path[len(FILTERS_ORIGINAL):]
        if path in FILTER_INPUTS:
            return R1_ROOT + FILTER_INPUTS[path]
        return None

    @staticmethod
    def SlotBase():
        """The slot base image of the market's item slots: the R1 item slot C."""
        return R.SLOT_CELL

    @staticmethod
    def ActionPrefix(family):
        """R1 file prefix (+ _<state>.png) of a filter dialog action button family, else None."""
        return FILTER_ACTIONS.get(family)

    @staticmethod
    def FilterColor(color):
        return FILTER_COLORS.get(color, color)

    def FilterSkin(self, dialog, title, scroll=None):
        return FilterSkin(dialog, self, title, scroll)

    # texts -------------------------------------------------------------------------------------------------
    def Font(self, role, font):
        """Section and control texts in the kit text roles; body and dense texts (rows, prices, grids) keep theirs."""
        if role == 'section':
            return self.kit.font('text_sb')
        if role == 'control':
            return self.kit.font('text_s')
        return font

    @staticmethod
    def Color(color):
        return COLORS.get(color & 0xFFFFFFFF if isinstance(color, int) else color, color)

    def StyleButtonText(self, button, primary=False):
        line = getattr(button, 'ButtonText', None)
        if line is None:
            return
        R.SetFont(line, self.kit.font('text_sb' if primary else BUTTON_FONT), line.GetText())
        line.SetPackedFontColor(T.PRIMARY_TEXT if primary else T.BUTTON_TEXT)


# --------------------------------------------------------------------------- scroll bars
class ScrollSkin(object):
    """uicrimsonember.SettingsScrollBar drawn as the narrow R1 bar: the bar's own three track images (made before its
    thumb, so they stay under it) show the R1 track (8 px, centred in the bar's 12 px column) and the thumb's images
    are replaced by the R1 thumb (6 px with the red vein) inside the bar's own 8 px MiddleBar. The bar's size, the
    thumb size (its minimum included), dragging, the click into the track and the wheel are the bar's own."""

    def __init__(self, bar):
        self.bar = bar
        self.x = max(0, (bar.SCROLLBAR_WIDTH - T.SCROLL_W) // 2)
        self.track = R.Ops(bar, dx=self.x)
        self.track.items = [bar.middleImage, bar.topImage, bar.bottomImage]
        thumb = bar.middleBar
        for name in ('top', 'topScale', 'bottom', 'bottomScale', 'middle'):
            image = getattr(thumb, name, None)
            if image is not None:
                image.Hide()
        self.thumb = R.Ops(thumb)
        self._bar_size = bar.SetScrollBarSize
        self._thumb_size = thumb.SetSize
        bar.SetScrollBarSize = self.SetScrollBarSize        # the bar's own calls go through the skin
        thumb.SetSize = self.SetThumbSize
        self._Track()
        self._Thumb()

    def SetScrollBarSize(self, height):
        self._bar_size(height)
        self._Track()

    def SetThumbSize(self, height):
        self._thumb_size(height)
        self._Thumb()

    def _Track(self):
        self.track.Apply(RL.vscroll('track', 'normal', 0, 0, max(T.SCROLL_MIN, self.bar.GetHeight())))

    def _Thumb(self):
        thumb = self.bar.middleBar
        self.thumb.dx = max(0, (thumb.GetWidth() - T.THUMB_W) // 2)
        self.thumb.Apply(RL.vscroll('thumb', 'normal', 0, 0, max(1, thumb.GetHeight())))


# --------------------------------------------------------------------------- the filter dialogs
class FilterSkin(object):
    """The R1 frame and header of the advanced filter dialog or its picker (BoardWithTitleBar), the picker's scroll
    bar in R1. Resize() after the dialog re-laid its height, SetTitle() when the picker shows another title."""

    def __init__(self, dialog, theme, title, scroll=None):
        self.board = R.BoardSkin(dialog, theme.kit, title, on_close=dialog.Close)
        self.scroll = ScrollSkin(scroll) if scroll is not None else None

    def SetTitle(self, title):
        self.board.SetTitle(title)

    def Resize(self, w, h):
        self.board.Resize(w, h)

    def Restore(self):
        self.board.Restore()


# --------------------------------------------------------------------------- the window
class MarketSkin(object):
    """The R1 look of one VirtualMarketWindow, made after its _Build. If making it raises, what was made is restored
    before the exception goes on (the window then builds its original look)."""

    def __init__(self, window, theme):
        self.window = window
        self.theme = theme
        self.board = self.dropdown = None
        self.scrolls = []
        try:
            self.board = R.BoardSkin(window, theme.kit, TITLE, on_close=window.Close)
            self.scrolls.append(ScrollSkin(window.categoryScrollBar))
            # The search suggestion list draws its R1 well, outline and rows itself (uivirtualmarket builds it in the
            # R1 look while the theme is set); only its scroll bar is the R1 bar here.
            dropdown = getattr(window, 'suggestionDropdown', None)
            if dropdown is not None:
                self.scrolls.append(ScrollSkin(dropdown.scrollBar))
            theme.StyleButtonText(window.buySelectedButton, primary=True)
            theme.StyleButtonText(window.retryButton)
            theme.StyleButtonText(window.createButton, primary=True)
        except Exception:
            self.Restore()
            raise

    def Restore(self):
        for board in (self.board, self.dropdown):
            if board is not None:
                board.Restore()

    def Destroy(self):
        for board in (self.board, self.dropdown):
            if board is not None:
                board.Destroy()
        self.board = self.dropdown = None
        self.scrolls = []
