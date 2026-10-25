# -*- coding: utf-8 -*-
"""The crafting window (uicrafting.CubeRenewalWindows: "Výroba ros" and "Výroba | <NPC>") in the R1 look ("Krvavá
žíla", docs/ALTHEA_R1_KIT.md), drawn INTO the original window.

The window keeps its 660 x 556 size, its layout and every function (server quotes, the category menu, the search,
the recipe list, the materials with the selectable stacks, the quantity, Max and Vyrobit). R1:
  * frame and header with the title (it follows the catalogue as before) and the plain X;
  * the category picker as an R1 field with the chevron, its menu as an R1 drop-down list (hover / selected rows);
  * the search as the R1 search field around the window's own edit line (magnifier, the clear cross);
  * the recipe rows: Noto Sans names, the selected row a dark well with the red line under it, hover rows lighter;
    the original item icons on the R1 item slot C (uir1.SLOT_CELL);
  * the result panel and the material rows as R1 inner panels, the counts green / red as before;
  * the narrow R1 scroll bars, the R1 check box "Použít libovolné", the quiet R1 dividers;
  * -, the quantity field, +, Max as small R1 buttons / field, Vyrobit as the primary R1 button.

The original widgets stay the window's attributes or are swapped for R1 ones with the same calls (SetText, Enable /
Disable, Show / Hide, SetPos ...), so every method of the window runs unchanged. Settings -> "Starý vzhled" keeps the
original window; a failure traces to syserr and the window falls back to its original look (Restore).
"""
from weakref import proxy

import ui

import uikit
import uir1
import uir1layout as L
import uir1tokens as T
from craftinglocale import Text as CraftText

ORIGINAL_SLOT_BASE = 'd:/ymir work/ui/slot.png'
import ownedcount
GREEN = ownedcount.GREEN    # enough materials (the game's positive green, a step calmer on graphite); every item price
SHORT = ownedcount.SHORT    # missing materials / not enough Yang
VALUE = 0xFFE8C77A          # numbers and the dew effect: the warm gold of the original values
LIST_X, LIST_W = 20, 174    # the left column (picker, search, list + its scroll bar)
SELECT_Y, SEARCH_Y = 36, 70
LIST_SCROLL_X = LIST_X + LIST_W - T.SCROLL_W
DETAIL_X, DETAIL_W = 220, 424
DETAIL_SCROLL_X = DETAIL_X + DETAIL_W - T.SCROLL_W
# one grid for the right column. The material rows are as wide as the result panel above them (narrower
# only by the scroll bar when they scroll); the icon and the name of a row sit under the result's icon and name, the
# counts and their caption share one right edge. Vertically one 10 px gap: the rows' viewport, the divider, Šance /
# cost, the status line and the button row (507, the original row) follow each other with it.
GAP = 10
ROW_PAD = 10                # icon left / counts right inside a row (the result icon sits 10 px in the panel too)
ROW_ICON_X = ROW_PAD
ROW_LABEL_X = 52            # the result name: window.name at DETAIL_X + 52
SCROLL_GAP = 6              # between the narrower rows and the scroll bar
P = T.PROFILE_WINDOW         # the layout profile of this window (docs/ALTHEA_R1_KIT.md chap. 0)


def Rows(window_h, cell):
    """The rows of the bottom of the right column from the window's height and the text cell of ROW_TEXT:
    the quantity row (field FIELD_H, Vyrobit centred on it) with its button the profile's pad above the bottom edge;
    Šance / cost the last content line P['foot_gap'] (= the gap under the row) above the top of the button row
    (owner 13. 10.: "mezera od toho nahoře? Od těch yangů?"); the status line ("Chybí suroviny.") above it with the
    info leading P['line_gap'], then the divider and the bottom of the material rows' viewport (GAP each)."""
    button_y = window_h - P['pad'] - P['btn'] - (T.FIELD_H - P['btn']) // 2
    row_top = button_y + (T.FIELD_H - P['btn']) // 2
    chance_y = row_top - P['foot_gap'] - cell
    status_y = chance_y - P['line_gap'] - cell
    divider_y = status_y - GAP - 1
    return dict(button_y=button_y, row_top=row_top, chance_y=chance_y, status_y=status_y, divider_y=divider_y,
                detail_bottom=divider_y - GAP)
MENU_ROW_H = 26
ROW_TEXT = 'text_s'


def Tr(czech, english):
    return uir1.Tr_(czech, english)


def Transparent():
    return uir1.GenerateColor(0x000000, 0.0)


class Select(uikit.Interactive):
    """The category picker: an R1 field well with the label on the left and the chevron on the right (up while its
    menu is open). The API of uicraftingcontrols.FlatButton the window calls: SetText / GetText / SetArrow /
    SetSelected / Enable / Disable."""

    def __init__(self, parent, kit, x, y, w, text, event):
        uikit.Interactive.__init__(self)
        self.kit = kit
        self.w, self.h = int(w), T.FIELD_H
        self.expanded = False
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, self.h)
        self.ops = uir1.Ops(self, L.field('normal', self.w))            # the well before the label and the chevron
        font = kit.font(ROW_TEXT)
        self.label = uir1.RowText(self, '', 9, self.h, font, T.INK)
        self.chevron = uir1.Image(self, uir1.ChevronPath('down'), self.w - 9 - T.CHEVRON, (self.h - T.CHEVRON) // 2)
        self.callback = event
        self.SetText(text)
        self.Show()

    def SetText(self, text):
        uir1.Fit(self.label, str(text), self.w - 9 - T.CHEVRON - 14)

    def GetText(self):
        return self.label.GetText()

    def SetArrow(self, expanded):
        self.expanded = bool(expanded)
        self.paint()

    def SetSelected(self, selected):
        pass

    def paint(self):
        state = self.state()
        self.ops.Apply(L.field({'pressed': 'hover'}.get(state, 'focus' if self.expanded else state), self.w))
        chevron = {'pressed': 'active', 'normal': 'active' if self.expanded else 'normal'}.get(state, state)
        self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath('up' if self.expanded else 'down', chevron))
        self.label.SetPackedFontColor(T.DISABLED if state == 'disabled' else
                                      (T.IVORY if self.expanded or state == 'hover' else T.INK))


class MenuRow(uikit.Interactive):
    """One row of the category menu: the band (hover lighter, the selected one the dark well with the red line), the
    name and the recipe count."""

    def __init__(self, parent, kit, x, y, w, text, count, selected, event):
        uikit.Interactive.__init__(self)
        self.selected = bool(selected)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), MENU_ROW_H)
        self.band = uir1.Band(self, 0, 0, int(w), MENU_ROW_H - 1)      # before the texts
        font = kit.font(ROW_TEXT)
        self.label = uir1.RowText(self, '', 10, MENU_ROW_H, font, T.INK)
        uir1.Fit(self.label, text, int(w) - 56)
        self.count = uir1.Text(self, str(count), int(w) - 10, uir1.CellTop(MENU_ROW_H, font), font, T.MUTED,
                               align='right', valign='top')
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        hover = self.state() in ('hover', 'pressed')
        self.band.SetState('selected' if self.selected else ('hover' if hover else 'normal'))
        self.label.SetPackedFontColor(T.IVORY if self.selected or hover else T.INK_DIM)
        self.count.SetPackedFontColor(VALUE if self.selected else T.MUTED)


class Panel(object):
    """An R1 inner panel drawn INTO an original ui.Bar: the bar turns transparent and gets the panel frame as its
    child, so the panel keeps the bar's place in the draw order (under the window's later children: the texts)."""

    def __init__(self, bar):
        self.bar = bar
        self.frame = uir1.Frame(bar, 0, 0, bar.GetWidth(), bar.GetHeight(), 'panel')
        bar.SetColor(Transparent())

    def Resize(self, w, h):
        self.frame.Resize(w, h)

    def Restore(self, color):
        self.frame.Hide()
        self.frame.Destroy()
        self.bar.SetColor(color)


class CraftingSkin(object):
    """R1 into one CubeRenewalWindows after its _Build. ``legacy_color`` packs an original ARGB colour (the window's
    controls.packed_color), used to give the original widgets their colours back."""

    LABELS = ('recipeCount', 'name', 'outputCount', 'materialCaption', 'countCaption', 'chanceCaption', 'chance',
              'cost', 'quantityLabel', 'quantityCaption')

    def __init__(self, window, legacy_color):
        self.window = window
        self.legacy_color = legacy_color
        self.kit = kit = uir1.Kit()
        self.rows = Rows(window.GetHeight(), uir1.FontCell(kit.font(ROW_TEXT)))
        self.DETAIL_BOTTOM = self.rows['detail_bottom']         # read by uicrafting for the viewport's height
        self.swapped = {}
        self.hidden = []
        self.labels = {}
        self.widgets = []
        self.hero = None
        self.select = self.search = self.check = self.amount = None
        self.price = None
        owner = proxy(window)
        self.skin = uir1.BoardSkin(window.board, kit, window.board.titleName.GetText(),
                                   on_close=ui.__mem_func__(window.Close))
        try:
            window.columnRule.SetColor(uir1.GenerateColor(T.LINE, 1.0))
            # the column rule runs down to the bottom of the quantity row (it ended with the original row)
            self.column_rule_h = window.columnRule.GetHeight()
            top = window.columnRule.GetLocalPosition()[1]
            bottom = self.rows['button_y'] + T.FIELD_H
            window.columnRule.SetSize(window.columnRule.GetWidth(), max(self.column_rule_h, bottom - top))
            for name in ('listRule', 'footerRule'):
                self._Hide(getattr(window, name))
            self.widgets.append(uir1.Divider(window, LIST_X, 508, LIST_W))
            self.widgets.append(uir1.Divider(window, DETAIL_X, self.rows['divider_y'], DETAIL_W))
            # left column: the category picker and the search
            original = window.categoryButton
            self._Hide(original)
            self.select = Select(window, kit, LIST_X, SELECT_Y, LIST_W, original.GetText(),
                                 ui.__mem_func__(window.ToggleMenu))
            self._Swap('categoryButton', self.select)
            self._Hide(window.searchBack)
            edit = window.search
            self.search_pos = edit.GetLocalPosition()
            self.search = uir1.SearchField(window, kit, LIST_X, SEARCH_Y, LIST_W, edit=edit, max_len=40,
                                           on_clear=ui.__mem_func__(window.Filter))
            self.search.SetHint(CraftText('SEARCH'))
            # the scroll bars
            self._Scroll('listScroll', LIST_SCROLL_X, 109, window.listHeight, window.ScrollList, window.OnListWheel)
            self._Scroll('detailScroll', DETAIL_SCROLL_X, window.detailViewport.GetLocalPosition()[1],
                         window.detailHeight, window.ScrollDetail, window.OnDetailWheel)
            # the result panel and the texts
            self.hero = Panel(window.heroBackground)
            fonts = dict(recipeCount=ROW_TEXT, name='text', outputCount=ROW_TEXT, materialCaption='text_sb',
                         countCaption=ROW_TEXT, chanceCaption=ROW_TEXT, chance=ROW_TEXT, cost=ROW_TEXT,
                         quantityLabel=ROW_TEXT, quantityCaption=ROW_TEXT)
            colors = dict(recipeCount=T.MUTED, name=T.IVORY, outputCount=T.INK_DIM, materialCaption=T.INK_DIM,
                          countCaption=T.MUTED, chanceCaption=T.INK_DIM, chance=VALUE, cost=VALUE,
                          quantityLabel=T.INK_DIM, quantityCaption=T.INK_DIM)
            for name in self.LABELS:
                line = getattr(window, name)
                self.labels[name] = line.GetLocalPosition()
                uir1.SetFont(line, kit.font(fonts[name]))
                line.SetPackedFontColor(colors[name])
            # "Recepty: N" on the line of "Počet" (the quantity row)
            caption_y = uir1.CellTop(T.FIELD_H, kit.font(ROW_TEXT)) + self.rows['button_y']
            window.recipeCount.SetPosition(LIST_X, caption_y)
            window.quantityCaption.SetPosition(DETAIL_X, caption_y)
            window.quantityLabel.SetPosition(DETAIL_X, self.rows['status_y'])
            window.chanceCaption.SetPosition(DETAIL_X, self.rows['chance_y'])
            window.cost.SetPosition(DETAIL_X + DETAIL_W, self.rows['chance_y'])
            # the price: the shared R1 price (root/uir1price.py, the coin, "10.000.000 Yang" in Tahoma
            # 12, red when the player has less) right-aligned where the cost line was; the line stays hidden
            import uir1price
            window.cost.Hide()
            self.hidden.append(window.cost)
            self.price = uir1price.Price(window, DETAIL_X + DETAIL_W, self.rows['chance_y'], 'right')
            self.widgets.append(self.price)
            self.PlaceChance()
            # the check box "Použít libovolné"
            self._Hide(window.check)
            self._Hide(window.checkLabel)
            self.check = uir1.CheckBox(window.checkArea, kit, 0, 4, window.checkLabel.GetText(), on=window.useAny,
                                       event=ui.__mem_func__(window.ToggleUseAny), font=kit.font(ROW_TEXT))
            # the quantity row: -, the field, +, Max, Vyrobit
            self._Hide(window.inputBack)
            self.input_pos = window.input.GetLocalPosition()
            self.input_area_pos = window.inputArea.GetLocalPosition()
            window.inputArea.SetPosition(self.input_area_pos[0], self.rows['button_y'])
            self.amount = uir1.Field(window.inputArea, kit, 0, 0, window.inputArea.GetWidth(), edit=window.input,
                                     max_len=4, number=True)
            row = self.rows['button_y'] + (T.FIELD_H - T.BTN_H_S) // 2
            glyph = kit.font('button')                  # - and + in the larger cut: the small one is a speck
            for name, x, w, text, event, font in (
                    ('minus', 261, 26, '-', lambda r=owner: r.SetAmount(r.amount - 1), glyph),
                    ('plus', 333, 26, '+', lambda r=owner: r.SetAmount(r.amount + 1), glyph),
                    ('maxButton', 365, 80, window.maxButton.GetText(), lambda r=owner: r.SetAmount(r.maximum), None)):
                self._Hide(getattr(window, name))
                self._Swap(name, uir1.Button(window, kit, x, row, w, text, small=True, event=event, font=font))
            self._Hide(window.make)
            make_y = self.rows['button_y'] + (T.FIELD_H - T.BTN_H) // 2
            self._Swap('make', uir1.Button(window, kit, DETAIL_X + DETAIL_W - 170, make_y,
                                           170, window.make.GetText(), primary=True,
                                           event=ui.__mem_func__(window.Make)))
            window.controlEnabled = {}
            window.makeEnabled = None
            window.checkEnabled = None
        except Exception:
            self.Restore()
            raise

    # ------------------------------------------------------------------ build helpers
    def _Hide(self, widget):
        if widget.IsShow():
            self.hidden.append(widget)
        widget.Hide()

    def _Swap(self, name, widget):
        self.swapped.setdefault(name, getattr(self.window, name))
        setattr(self.window, name, widget)

    def _Scroll(self, name, x, y, height, on_scroll, on_wheel):
        window = self.window
        original = getattr(window, name)
        bar = uir1.ScrollBar(self.kit)
        bar.SetParent(window)
        bar.SetPosition(x, y)
        bar.SetScrollBarSize(height)
        bar.SetScrollEvent(ui.__mem_func__(on_scroll))
        bar.OnMouseWheel = ui.__mem_func__(on_wheel)
        bar.Show() if original.IsShow() else bar.Hide()
        original.Hide()
        self._Swap(name, bar)

    # ------------------------------------------------------------------ used by the window
    ROW_ICON_X = ROW_ICON_X

    @staticmethod
    def RowWidth(content_height, view_height):
        """Width of the material rows: the result panel's, minus the scroll bar and its gap when they scroll."""
        if content_height > view_height:
            return DETAIL_W - T.SCROLL_W - SCROLL_GAP
        return DETAIL_W

    @staticmethod
    def SlotBase(height=T.SLOT):
        """The R1 item slot C for one of the window's single slots (32, 64 or 96 px tall: the item's height)."""
        return uir1.SlotBase(height)

    def Ink(self, color, values):
        """R1 colour of an original colour constant: values = the window's (INK, MUTED, GOLD, GREEN, RED)."""
        ink, muted, gold, green, red = values
        return {ink: T.INK, muted: T.MUTED, gold: VALUE, green: GREEN, red: SHORT}.get(color, T.INK)

    def SetTitle(self, title):
        self.skin.SetTitle(title)

    def Cost(self, amount, affordable=None):
        """The price of the recipe times the amount (None: no recipe) in the R1 price."""
        if self.price is None:
            return
        if amount is None:
            self.price.Clear()
        else:
            self.price.SetPrice(amount, affordable)

    def PlaceChance(self):
        window = self.window
        x, y = window.chanceCaption.GetLocalPosition()
        window.chance.SetPosition(x + uir1.TextWidth(window.chanceCaption) + 8, y)

    def ListRow(self, row, name, height, selected, collection):
        """The band and the name of one recipe row (the icon is the window's); returns (band, name line)."""
        band = uir1.Band(row, 0, 0, row.GetWidth(), height - 2, 'selected' if selected else 'normal')
        collection.append(band)
        line = uir1.RowText(row, '', 46, height - 2, self.kit.font(ROW_TEXT), T.IVORY if selected else T.INK_DIM)
        collection.append(line)
        self.window._Fit(line, name, row.GetWidth() - 46 - 8)
        return band, line

    def Hero(self, height, dew_line=None):
        """The result panel resized to ``height``; the name, the output count and the dew effect centred in it."""
        window = self.window
        self.hero.Resize(DETAIL_W, height)
        name, small = self.kit.font('text'), self.kit.font(ROW_TEXT)
        lines = [(window.name, name), (window.outputCount, small)] + ([(dew_line, small)] if dew_line else [])
        total = sum(uir1.FontCell(font) for unused, font in lines) + 3 * (len(lines) - 1)
        y = 36 + (height - total) // 2
        for line, font in lines:
            line.SetPosition(window.name.GetLocalPosition()[0], y)
            y += uir1.FontCell(font) + 3

    def DewLine(self, collection):
        line = uir1.Text(self.window, '', self.window.name.GetLocalPosition()[0], 0, self.kit.font(ROW_TEXT), VALUE,
                         valign='top')
        collection.append(line)
        return line

    def Captions(self, top, width=DETAIL_W):
        """The material captions above the rows starting at ``top`` (one text row, the check box on it); the count
        caption ends where the counts of the ``width`` px rows end."""
        window = self.window
        y = top - 26
        window.materialCaption.SetPosition(DETAIL_X, y)
        window.countCaption.SetPosition(DETAIL_X + int(width) - ROW_PAD, y)
        # the check box label on the text row of the captions: the box (CHECK, or the label's cell when taller) lies 4 px
        # into the check area and centres its label (uir1.CheckBox), so the area moves up by the label's offset in it
        cell = uir1.FontCell(self.kit.font(ROW_TEXT))
        window.checkArea.SetPosition(335, y - 4 - (max(T.CHECK, cell) // 2 - cell // 2))
        window.detailScroll.SetPosition(DETAIL_SCROLL_X, top)

    def MaterialRow(self, parent, width, height, head, collection):
        """The R1 panel of one material row (made before its icon and texts)."""
        frame = uir1.Frame(parent, 0, 0, width, height - 2, 'panel')
        collection.append(frame)
        return frame

    def MaterialTexts(self, parent, head, name, counts, enough, collection):
        font = self.kit.font(ROW_TEXT)
        width = parent.GetWidth()
        label = uir1.RowText(parent, '', ROW_LABEL_X, head, font, T.INK)
        collection.append(label)
        self.window._Fit(label, name, width - ROW_LABEL_X - 96)      # 96: the counts ("12,3k / 99,9k")
        count = uir1.Text(parent, counts, width - ROW_PAD, uir1.CellTop(head, font), font, GREEN if enough else SHORT,
                          align='right', valign='top')
        collection.append(count)
        return label, count

    def PaintCheck(self, on, enabled):
        self.check.SetOn(on)
        if enabled != self.check.IsEnabled():
            self.check.Enable() if enabled else self.check.Disable()

    def Menu(self, menu, groups, current, counts, select, collection):
        """The category menu as an R1 drop-down list as wide as the picker; returns its height."""
        w, h = LIST_W, len(groups) * MENU_ROW_H + 8
        menu.SetSize(w, h)
        frame = uir1.Frame(menu, 0, 0, w, h, 'dialog')
        collection.append(frame)
        for index, group in enumerate(groups):
            row = MenuRow(menu, self.kit, 4, 4 + index * MENU_ROW_H, w - 8, group or Tr(u'Vše', 'All'),
                          counts[index], group == current, lambda g=group: select(g))
            collection.append(row)
        return h

    # ------------------------------------------------------------------ back to the original look
    def Restore(self):
        window = self.window
        if window is None:
            return
        for name, original in self.swapped.items():
            widget = getattr(window, name)
            if widget is original:
                continue
            shown = widget.IsShow()
            widget.Hide()
            if name in ('listScroll', 'detailScroll'):
                widget.Destroy()
                original.Show() if shown else original.Hide()
            setattr(window, name, original)
        if self.search is not None:
            edit = self.search.edit
            self.search.Hide()
            edit.SetParent(window)
            edit.SetPosition(*self.search_pos)
            edit.SetSize(158, 16)
            uir1.SetFont(edit, 'Tahoma:12')
        if self.amount is not None:
            window.inputArea.SetPosition(*self.input_area_pos)
            edit = self.amount.edit
            self.amount.Hide()
            edit.SetParent(window.inputArea)
            edit.SetPosition(*self.input_pos)
            uir1.SetFont(edit, 'Tahoma:13')
        if self.select is not None:
            window.categoryButton.SetText(window.category or CraftText('ALL'))
        if self.check is not None:
            self.check.Hide()
        if self.hero is not None:
            self.hero.Restore(self.legacy_color(0xff11110f))
        for name, position in self.labels.items():
            font, color = window.LEGACY_LABELS[name]
            line = getattr(window, name)
            line.SetPosition(*position)
            uir1.SetFont(line, font)
            line.SetPackedFontColor(self.legacy_color(color))
        for widget in self.widgets:
            widget.Hide()
        for widget in self.hidden:
            widget.Show()
        window.columnRule.SetColor(self.legacy_color(0xff342d24))
        if getattr(self, 'column_rule_h', None):
            window.columnRule.SetSize(window.columnRule.GetWidth(), self.column_rule_h)
        self.skin.Restore()
        self.skin.Destroy()
        window.controlEnabled = {}
        window.makeEnabled = None
        window.checkEnabled = None
        self.window = None

    Destroy = Restore
