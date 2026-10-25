# -*- coding: utf-8 -*-
"""The "Historie" view of "Můj obchod" in the virtual market (docs/invariants/market-sales-history.md).

uivirtualmarket builds it into the owner tab and passes itself as ``vm`` so the view uses the market's own helpers
(labels, images, Yang texts, the R1 theme). The data and the requests live in root/marketsaleshistory.py; this file
only draws. Building it must never break the market: VirtualMarketWindow catches any exception and keeps the
owner tab without the switch.
"""
import ui

import marketlayout
import marketsaleshistory as model

VIEW_LISTINGS = "listings"
VIEW_HISTORY = "history"

PANEL_W = 541
PANEL_H = 470
SUMMARY_Y = 0
SUMMARY_H = 38
HEADER_Y = 44
# The rows are the market result rows (uivirtualmarket.CrimsonMarketRow, owner 22. 10.: "proč sis vymyslel nový typ
# tabulky"): the market header, then the rows as far below it as in the market (MARKET_ROWS_Y). v4 (owner 22. 10.,
# a weapon row was three empty cells tall, 3 rows a page): every row has the fixed base height
# (marketlayout.BASE_ROW_HEIGHT) and shows its item in ONE slot cell (compactItem, R1 kit "Item slots"), so a page
# holds as many rows as fit the room above the page strip whatever the items are.
FOOTER_Y = 402
FOOTER_H = 38
SUMMARY_CENTERS = (92, 270, 448)

SWITCH_W = 150
SWITCH_H = 24
SWITCH_X = (PANEL_W - SWITCH_W) // 2
SWITCH_Y = 2

DIM = 0xff9e8c7c
INK = 0xffeadfc8
NO_BUYER = "-"


def _T(vm, key, fallback):
    return vm._Text(key, fallback)


def RowsY(vm):
    return HEADER_Y + vm.MARKET_ROWS_Y


def RowsHeight(vm):
    """The room of the rows: the market's rule (MARKET_ROWS_HEIGHT = footer - rows - 1)."""
    return FOOTER_Y - RowsY(vm) - 1


def Columns(vm):
    """The history header in the market header: the time over the check box column, then the market's own columns
    (the item column moved like the row's slot and name), the buyer where the market shows the seller."""
    return (("VIRTUAL_MARKET_SALES_TIME", "\u010cAS", vm.ROW_LEAD_CENTER_X),
            ("VIRTUAL_MARKET_ITEM", "P\u0158EDM\u011aT", vm.ITEM_COLUMN_CENTER_X + vm.ROW_LEAD_SHIFT),
            ("VIRTUAL_MARKET_COUNT", "PO\u010cET", vm.COUNT_CENTER_X),
            ("VIRTUAL_MARKET_PRICE", "CENA", vm.PRICE_COLUMN_CENTER_X),
            ("VIRTUAL_MARKET_SALES_BUYER", "KUPEC", vm.SELLER_CENTER_X))


def RowHeight():
    """The fixed height of a history row: the base market row (a tall item is scaled into one slot cell)."""
    return marketlayout.RowHeight(1)


def PageSizes(count, available):
    """Rows per page for ``count`` rows of the fixed history row height in ``available`` px."""
    return [len(page) for page in marketlayout.PackRows([1] * int(count), available)]


class ViewSwitch(object):
    """Nabídky | Historie in the owner header: the R1 segment, or two underlined text buttons in the original look."""

    def __init__(self, vm, parent, event):
        self.vm = vm
        self.event = event
        self.value = VIEW_LISTINGS
        self.segment = None
        self.buttons = {}
        labels = ((VIEW_LISTINGS, _T(vm, "VIRTUAL_MARKET_OWNER_VIEW_LISTINGS", "Nab\u00eddky")),
                  (VIEW_HISTORY, _T(vm, "VIRTUAL_MARKET_OWNER_VIEW_HISTORY", "Historie")))
        if vm._R1 is not None:
            import uir1
            self.segment = uir1.Segment(parent, vm._R1.kit, labels, self._Select,
                                        font=vm._R1.kit.font('text_xs'), width=SWITCH_W, height=SWITCH_H)
            self.segment.SetPosition(SWITCH_X, SWITCH_Y)
            self.segment.SetValue(self.value)
            self.widgets = (self.segment,)
        else:
            half = SWITCH_W // 2
            for index, (value, text) in enumerate(labels):
                self.buttons[value] = vm._UnderlinedTextButton(
                    parent, SWITCH_X + index * half, SWITCH_Y, half, SWITCH_H, text,
                    lambda selected=value: self._Select(selected))
            self.widgets = tuple(self.buttons.values())
            self._PaintLegacy()

    def _Select(self, value):
        if self.event:
            self.event(value)

    def SetValue(self, value):
        self.value = value
        if self.segment is not None:
            self.segment.SetValue(value)
        else:
            self._PaintLegacy()

    def _PaintLegacy(self):
        for value, button in self.buttons.items():
            color = 0xfff7c81c if value == self.value else button.NORMAL_COLOR
            button.label.SetPackedFontColor(color)

    def Show(self):
        for widget in self.widgets:
            widget.Show()

    def Hide(self):
        for widget in self.widgets:
            widget.Hide()

    def Destroy(self):
        self.Hide()
        self.event = None
        self.segment = None
        self.buttons = {}
        self.widgets = ()


def _SnapshotList(values, size, empty):
    values = list(values or ())[:size]
    return values + [empty] * (size - len(values))


def FillTooltip(vm, tooltip, sale):
    """The normal item tooltip of a sold piece: its bonuses from the market escrow snapshot (server capability 2),
    else the item by vnum with a note; then when it sold and who bought it."""
    import app
    import player
    soldAt, vnum = sale[1:3]
    buyer = sale[5] if len(sale) > 5 else ""
    piece = sale[6] if len(sale) > 6 else None
    socketCount = int(getattr(player, "METIN_SOCKET_MAX_NUM", model.SOCKETS))
    attributeCount = int(getattr(player, "ATTRIBUTE_SLOT_MAX_NUM", model.ATTRIBUTES))
    tooltip.ClearToolTip()
    if piece:
        options = {"rarity_preview_grade": int(piece.get("rarity", 0))}
        if getattr(app, "ENABLE_APPLY_RANDOM", 0):
            options["apply_random_list"] = _SnapshotList(
                [tuple(pair) for pair in piece.get("random", ())],
                int(getattr(player, "APPLY_RANDOM_SLOT_MAX_NUM", model.RANDOM_APPLIES)), (0, 0))
        tooltip.AddItemData(int(vnum), _SnapshotList(piece.get("sockets"), socketCount, 0),
                            _SnapshotList([tuple(pair) for pair in piece.get("attributes", ())], attributeCount,
                                          (0, 0)), **options)
        transmutation = int(piece.get("transmutation", 0))
        if transmutation and hasattr(tooltip, "AppendChangeLookInfoItemVnum"):
            tooltip.AppendChangeLookInfoItemVnum(transmutation)
    else:
        tooltip.AddItemData(int(vnum), [0] * socketCount, [(0, 0)] * attributeCount, rarity_preview_grade=0)
        tooltip.AppendTextLine(_T(vm, "VIRTUAL_MARKET_SALES_TOOLTIP_NO_SNAPSHOT",
                                  "Bonusy prodan\u00e9ho kusu nejsou ulo\u017een\u00e9."), tooltip.NORMAL_COLOR)
    tooltip.AppendSpace(5)
    tooltip.AppendTextLine(_T(vm, "VIRTUAL_MARKET_SALES_TOOLTIP_SOLD", "Prod\u00e1no: %s") % model.FormatTime(soldAt),
                           tooltip.NORMAL_COLOR)
    tooltip.AppendTextLine(_T(vm, "VIRTUAL_MARKET_SALES_TOOLTIP_BUYER", "Kupec: %s") % (buyer or NO_BUYER),
                           tooltip.NORMAL_COLOR)
    tooltip.ResizeToolTip()


class SalesHistoryPanel(object):
    """The history view: summary strip, the market's column header and result rows, the page strip.

    The rows are uivirtualmarket.CrimsonMarketRow (the market results row) without the check box: the time in its
    place, the item in its slot (the item tooltip of the sold piece over the slot only), count, the price over the
    price per piece, the buyer as the underlined player link and the envelope (a message to the buyer).
    tooltip() returns the game's item tooltip (interface.tooltipItem) or None; whisper((buyer, vnum)) and
    searchPlayer(name) are the window's. Every widget is kept in self.decor / self.headers / self.rows: an image or
    text line nobody references is destroyed by the client right away (21. 10. header bug)."""

    def __init__(self, vm, body, x, y, tooltip=None, whisper=None, searchPlayer=None):
        self.vm = vm
        self.history = model.RECEIVER
        self.tooltip = tooltip
        self.whisper = whisper
        self.searchPlayer = searchPlayer
        self.rows = []
        self.tooltipShown = False
        self.decor = []
        panel = self.panel = vm._Container(body, x, y, PANEL_W, PANEL_H)
        self.decor.append(vm._Image(panel, 8, SUMMARY_Y, vm.CRIMSON_MARKET_DIR + "panel/account_toolbar.png"))
        self.summary = []
        for key, fallback, centerX in (
                ("VIRTUAL_MARKET_SALES_TODAY", "Dnes:", SUMMARY_CENTERS[0]),
                ("VIRTUAL_MARKET_SALES_WEEK", "7 dn\u00ed:", SUMMARY_CENTERS[1]),
                ("VIRTUAL_MARKET_SALES_MONTH", "30 dn\u00ed:", SUMMARY_CENTERS[2])):
            prefix = vm._Label(panel, 0, SUMMARY_H // 2, _T(vm, key, fallback).rstrip() + " ", DIM)
            prefix.SetVerticalAlignCenter()
            value = vm._Label(panel, 0, SUMMARY_H // 2, vm._YangText(0), INK)
            value.SetVerticalAlignCenter()
            value.SetFontColor(*vm.CURRENCY_YANG_COLOR)
            self.summary.append((prefix, value, centerX))
        self.headers = vm.DataHeader(panel, 0, HEADER_Y, Columns(vm))
        self.rowsY = RowsY(vm)
        self.rowsHeight = RowsHeight(vm)
        self.message = vm._Label(panel, PANEL_W // 2, self.rowsY + self.rowsHeight // 2, "", DIM)
        self.message.SetHorizontalAlignCenter()
        self.message.SetVerticalAlignCenter()
        self.decor.append(vm._Image(panel, 8, FOOTER_Y, vm.CRIMSON_MARKET_DIR + "panel/account_toolbar.png"))
        self.note = vm._Label(panel, 20, FOOTER_Y + FOOTER_H // 2,
                              _T(vm, "VIRTUAL_MARKET_SALES_NOTE", "Posledn\u00edch 30 dn\u00ed \u00b7 pra\u017esk\u00fd \u010das"), DIM)
        self.note.SetVerticalAlignCenter()
        self.prevButton = vm._CrimsonIconButton(panel, vm.ACCOUNT_PREV_X, FOOTER_Y + vm.ACCOUNT_PAGE_Y,
                                                "button/pagination", self.history.PreviousPage,
                                                "icon/arrow_left.png", vm.PAGINATION_ICON_X, vm.PAGINATION_ICON_Y)
        self.nextButton = vm._CrimsonIconButton(panel, vm.ACCOUNT_NEXT_X, FOOTER_Y + vm.ACCOUNT_PAGE_Y,
                                                "button/pagination", self.history.NextPage,
                                                "icon/arrow_right.png", vm.PAGINATION_ICON_X, vm.PAGINATION_ICON_Y)
        self.page = vm._Label(panel, vm.ACCOUNT_PAGE_CENTER_X, FOOTER_Y + FOOTER_H // 2, "", INK)
        self.page.SetHorizontalAlignCenter()
        self.page.SetVerticalAlignCenter()
        self.refreshButton = vm._UnderlinedTextButton(
            panel, 430, FOOTER_Y + 7, 90, 24,
            _T(vm, "VIRTUAL_MARKET_SALES_REFRESH", "Obnovit"), self.history.Refresh)
        self.layout = ui.__mem_func__(self._PageSizes)
        self.history.layout = self.layout
        self.listener = ui.__mem_func__(self.Refresh)
        self.history.AddListener(self.listener)
        self.panel.Hide()

    # ---- visibility -----------------------------------------------------------------------------------
    def Show(self):
        self.panel.Show()
        self.Refresh()

    def Hide(self):
        self.HideSaleTooltip()
        self.panel.Hide()

    # ---- tooltip --------------------------------------------------------------------------------------
    def _Tooltip(self):
        try:
            return self.tooltip() if self.tooltip else None
        except Exception:
            return None

    def ShowSaleTooltip(self, sale):
        tooltip = self._Tooltip()
        if not tooltip or not sale or not self.IsShow():
            return
        try:
            FillTooltip(self.vm, tooltip, sale)
            tooltip.ShowToolTip()
            self.tooltipShown = True
        except Exception:
            self.tooltipShown = True
            self.HideSaleTooltip()

    def HideSaleTooltip(self):
        """Hides the item tooltip only when a history slot showed it (it is the game's shared item tooltip)."""
        if not self.tooltipShown:
            return
        self.tooltipShown = False
        tooltip = self._Tooltip()
        if tooltip:
            try:
                tooltip.HideToolTip()
            except Exception:
                pass

    def IsShow(self):
        return bool(self.panel.IsShow())

    def Open(self):
        """The view was chosen: ask for the newest page (only now, never in the background)."""
        self.Show()
        self.history.Open()

    def Update(self):
        if self.IsShow():
            self.history.Tick()

    def Destroy(self):
        self.HideSaleTooltip()
        self.history.RemoveListener(self.listener)
        if self.history.layout is self.layout:
            self.history.layout = None
        self.layout = None
        self.listener = None
        self._ClearRows()
        self.tooltip = None
        self.whisper = None
        self.searchPlayer = None
        self.headers = []
        self.decor = []
        self.panel.Hide()

    # ---- drawing --------------------------------------------------------------------------------------
    def Refresh(self):
        if not self.IsShow():
            return
        vm = self.vm
        totals = self.history.totals or (0, 0, 0, 0)
        for (prefix, value, centerX), amount in zip(self.summary, totals[:3]):
            value.SetText(vm._YangText(amount))
            value.SetFontColor(*vm.CURRENCY_YANG_COLOR)
            vm._CenterAccountValuePair(prefix, value, centerX, SUMMARY_H // 2)
        visible = self.history.VisibleRows() if self.history.loaded else []
        self.HideSaleTooltip()
        self._ClearRows()
        rowY = 0
        height = RowHeight()
        for sale in visible:
            if self.rows and rowY + height > self.rowsHeight:
                break
            self.rows.append(self._Row(sale, self.rowsY + rowY))
            rowY += height
        self.message.SetText(self._Message(visible))
        pages = self.history.PageCount()
        self.page.SetText("%d / %d" % (self.history.page + 1, pages))
        self.prevButton.Show() if self.history.page > 0 else self.prevButton.Hide()
        self.nextButton.Show() if self.history.page + 1 < pages else self.nextButton.Hide()

    # ---- rows -----------------------------------------------------------------------------------------
    def _PageSizes(self, rows):
        """The model's pages: as many fixed-height rows as fit the room of the rows."""
        return PageSizes(len(rows), self.rowsHeight)

    def _Row(self, sale, y):
        vm = self.vm
        credit, soldAt, vnum, count, price = sale[:5]
        buyer = sale[5] if len(sale) > 5 else ""
        date, _, clock = model.FormatTime(soldAt).partition(" ")
        row = vm.CrimsonMarketRow(
            self.panel, y, vnum, count, "", "", buyer or NO_BUYER, "", None, (credit, vnum, price),
            messageEvent=self.whisper if buyer else None,
            tooltipIn=lambda shown=sale: self.ShowSaleTooltip(shown), tooltipOut=self.HideSaleTooltip,
            messagePayload=(buyer, vnum),
            sellerSearchEvent=self.searchPlayer if buyer else None, sellerSearchPayload=buyer,
            selectionMode=False, checkbox=False, rowTooltip=False, lead=(date, clock), compactItem=True,
            messageHint=_T(vm, "VIRTUAL_MARKET_MESSAGE_BUYER", "Napsat kupci"))
        row.SetPosition(0, y)
        return row

    def _ClearRows(self):
        for row in self.rows:
            row.Destroy()
        self.rows = []

    def _Message(self, visible):
        vm = self.vm
        status = self.history.status
        if status == model.STATUS_DISABLED:
            return _T(vm, "VIRTUAL_MARKET_SALES_DISABLED", "Trh je te\u010f zav\u0159en\u00fd.")
        if status:
            return _T(vm, "VIRTUAL_MARKET_SALES_UNAVAILABLE", "Historie prodej\u016f te\u010f nen\u00ed dostupn\u00e1. Zkus Obnovit pozd\u011bji.")
        if visible:
            return ""
        if self.history.IsLoading() or not self.history.loaded or not self.history.PageReady():
            return _T(vm, "VIRTUAL_MARKET_SALES_LOADING", "Na\u010d\u00edt\u00e1m historii prodej\u016f...")
        return _T(vm, "VIRTUAL_MARKET_SALES_EMPTY", "Za posledn\u00edch 30 dn\u00ed jsi nic neprodal.")
