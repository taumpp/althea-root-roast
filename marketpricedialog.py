# -*- coding: utf-8 -*-
"""Exact unit-price feedback and optional matching-stack repricing."""
import localeInfo
import ui
import uiCommon


def UnitPriceText(total, count):
    total, count = int(total), int(count)
    if total <= 0 or count <= 0:
        return ""
    if total % count == 0:
        return "%s / ks" % localeInfo.NumberToMoneyString(total // count)
    # Keep the exact ratio: rounding the unit price first would distort stacks.
    a, b = total, count
    while b:
        a, b = b, a % b
    return "%s/%s Yang / ks" % (total // a, count // a)


class MarketPriceDialog(uiCommon.MoneyInputDialog):
    def __init__(self):
        uiCommon.MoneyInputDialog.__init__(self)
        self.itemCount = 1
        self.bulkAvailable = False
        self.lastTotal = None
        self.SetSize(420, 186)
        self.board.SetSize(420, 186)
        self.acceptButton.SetPosition(-36, 154)
        self.cancelButton.SetPosition(35, 154)
        self.unitPrice = ui.TextLine()
        self.unitPrice.SetParent(self.board)
        self.unitPrice.SetWindowHorizontalAlignCenter()
        self.unitPrice.SetHorizontalAlignCenter()
        self.unitPrice.SetPosition(0, 101)
        self.unitPrice.Show()
        self.matching = ui.CheckBox_N()
        self.matching.SetParent(self.board)
        self.matching.SetPosition(18, 125)
        self.matching.SetText(getattr(localeInfo, "VIRTUAL_MARKET_REPRICE_MATCHING",
            "Stejná cena za kus pro všechny shodné položky"))
        self.matching.Hide()

    def SetContext(self, count, bulkAvailable=False):
        self.itemCount = max(1, int(count))
        self.bulkAvailable = bool(bulkAvailable)

    def Open(self):
        self.matching.SetChecked(0)
        self.matching.Show() if self.bulkAvailable else self.matching.Hide()
        self.lastTotal = None
        uiCommon.MoneyInputDialog.Open(self)
        self.SetAveragePriceText(getattr(localeInfo,
            "VIRTUAL_MARKET_BUNDLE_PRICE", "Cena za %d ks") % self.itemCount)
        self.OnUpdate()

    def IsMatching(self):
        return self.bulkAvailable and self.matching.IsChecked()

    def SetValue(self, value):
        uiCommon.MoneyInputDialog.SetValue(self, value)
        self.OnUpdate()

    def OnUpdate(self):
        total = self.GetValue()
        if total != self.lastTotal:
            self.lastTotal = total
            self.unitPrice.SetText(UnitPriceText(total, self.itemCount))
