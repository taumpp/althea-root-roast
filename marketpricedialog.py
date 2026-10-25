# -*- coding: utf-8 -*-
"""Exact unit-price feedback, optional matching-stack repricing and "Vložit vše (N×)" for a new offer.

"Vložit vše" (owner 21. 10.): "Po [X] ks · Hromádek: [N]" - every listing has X pieces (the first offer's count by
default, at most the biggest stack: one listing comes from one inventory slot) and N listings (as many as the
inventory gives at X, at most the shop's free cells). With the box checked the price field is the price of 1 piece;
each listing is X pieces for X times that price, a rest stays in the inventory."""
import localeInfo
import ui
import uiCommon


def UnitPriceText(total, count, r1=False):
    """The price per piece; ``r1``: a whole amount as the one R1 yang price of the client ("1.000 Yang / ks",
    root/uir1price.py) - the dialog is in the R1 look."""
    total, count = int(total), int(count)
    if total <= 0 or count <= 0:
        return ""
    if total % count == 0:
        if r1:
            import uir1price
            return "%s / ks" % uir1price.FormatYang(total // count)
        return "%s / ks" % localeInfo.NumberToMoneyString(total // count)
    # Keep the exact ratio: rounding the unit price first would distort stacks.
    a, b = total, count
    while b:
        a, b = b, a % b
    return "%s/%s Yang / ks" % (total // a, count // a)


def _Yang(amount, r1=False):
    if r1:
        import uir1price
        return uir1price.FormatYang(amount)
    return localeInfo.NumberToMoneyString(amount)


def OfferAllListings(stacks, room, piece):
    """How many listings of ``piece`` pieces the ``stacks`` (piece counts of the inventory slots) give, at most
    ``room`` (the shop's free cells for the item): a listing comes from one slot, a smaller rest stays."""
    piece = int(piece)
    if piece <= 0:
        return 0
    return max(0, min(int(room), sum(int(count) // piece for count in stacks)))


def _Number(edit):
    try:
        return int(edit.GetText()) if edit is not None else None
    except (TypeError, ValueError):
        return None


class MarketPriceDialog(uiCommon.MoneyInputDialog):
    def __init__(self):
        uiCommon.MoneyInputDialog.__init__(self)
        self.itemCount = 1
        self.bulkAvailable = False
        self.offerAllCount = 0                  # listings at the default piece count; 0 = no "Vložit vše"
        self.offerAllStacks = ()
        self.offerAllRoom = 0
        self.lastPiece = None
        self.lastChecked = False
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
            "Stejná cena za kus pro všechny shodné předměty"))
        self.matching.Hide()
        # "Po [X] ks · Hromádek: [N]" and the summary line under it
        self.pieceLabel, self.pieceUnit, self.stacksLabel, self.summary = (ui.TextLine() for unused in range(4))
        for line in (self.pieceLabel, self.pieceUnit, self.stacksLabel, self.summary):
            line.SetParent(self.board)
            line.Hide()
        self.pieceField = self.pieceEdit = None   # built on the first Open: the dialog's look is known then
        self.stacksField = self.stacksEdit = None

    def _BuildField(self, digits):
        skin = getattr(self, "r1skin", None)
        if skin:
            import uir1
            field = uir1.Field(self.board, skin.kit, 0, 0, 64, number=True, max_len=digits)
            edit = field.edit
        else:
            field = getattr(ui, "SlotBar", ui.Window)()
            field.SetParent(self.board)
            field.SetSize(64, 18)
            edit = ui.EditLine()
            edit.SetParent(field)
            edit.SetPosition(4, 2)
            edit.SetSize(58, 16)
            edit.SetMax(digits)
            edit.SetNumberMode()
            edit.Show()
        field.Hide()
        return field, edit

    def _BuildStacksField(self):
        if self.stacksEdit is not None:
            return
        self.pieceField, self.pieceEdit = self._BuildField(5)
        self.stacksField, self.stacksEdit = self._BuildField(5)

    def _OfferAllWidgets(self):
        return [w for w in (self.pieceLabel, self.pieceField, self.pieceUnit, self.stacksLabel, self.stacksField,
            self.summary) if w is not None]

    def GetOfferAllPiece(self):
        """X: pieces in every listing, the field's value within 1..the biggest stack; the first offer's count
        when the field is empty or not a number."""
        if not self.offerAllCount:
            return 0
        biggest = max(self.offerAllStacks) if self.offerAllStacks else self.itemCount
        value = _Number(self.pieceEdit)
        return max(1, min(biggest, self.itemCount if value is None else value))

    def MaxOfferAllCount(self):
        """N at most: the listings the inventory gives at the current X, at most the free cells."""
        return OfferAllListings(self.offerAllStacks, self.offerAllRoom, self.GetOfferAllPiece())

    def GetOfferAllCount(self):
        """N: the number of listings "Vložit vše" makes, the first one included: the field's value within 1..max,
        the max when the field is empty or not a number."""
        if not self.offerAllCount:
            return 0
        most = self.MaxOfferAllCount()
        value = _Number(self.stacksEdit)
        return max(min(1, most), min(most, most if value is None else value))

    def SetContext(self, count, bulkAvailable=False, offerAllCount=0, offerAllStacks=None, offerAllRoom=None):
        """``bulkAvailable``: a repriced listing may reprice its matching stacks too. ``offerAllStacks``: piece
        counts of the item's inventory slots a new offer may take ("Vložit vše"), ``offerAllRoom`` the shop's free
        cells for it; offered when they give 2 pieces and 2 cells. ``offerAllCount`` alone (an older caller): that
        many stacks of ``count`` pieces. The one check box serves either."""
        self.itemCount = max(1, int(count))
        self.bulkAvailable = bool(bulkAvailable)
        if offerAllStacks is None:
            offerAllStacks = [self.itemCount] * int(offerAllCount) if int(offerAllCount) >= 2 else []
            offerAllRoom = int(offerAllCount)
        self.offerAllStacks = tuple(int(c) for c in offerAllStacks if int(c) > 0)
        self.offerAllRoom = int(offerAllRoom or 0)
        possible = not self.bulkAvailable and sum(self.offerAllStacks) >= 2 and self.offerAllRoom >= 2
        self.offerAllCount = max(1, OfferAllListings(self.offerAllStacks, self.offerAllRoom, self.itemCount)) \
            if possible else 0

    def _CheckBoxShown(self):
        return self.bulkAvailable or self.offerAllCount > 0

    def Open(self):
        self.matching.SetChecked(0)
        if self.offerAllCount:
            self.matching.SetText(getattr(localeInfo, "VIRTUAL_MARKET_OFFER_ALL_SPLIT", "Vložit vše"))
        else:
            self.matching.SetText(getattr(localeInfo, "VIRTUAL_MARKET_REPRICE_MATCHING",
                "Stejná cena za kus pro všechny shodné předměty"))
        self.matching.Show() if self._CheckBoxShown() else self.matching.Hide()
        if self.offerAllCount:
            self._BuildStacksField()
            self.pieceLabel.SetText(getattr(localeInfo, "VIRTUAL_MARKET_OFFER_ALL_PIECE", "Po"))
            self.pieceUnit.SetText(getattr(localeInfo, "VIRTUAL_MARKET_OFFER_ALL_PIECE_UNIT", "ks"))
            self.stacksLabel.SetText(getattr(localeInfo, "VIRTUAL_MARKET_OFFER_ALL_COUNT", "Hromádek:"))
            self.pieceEdit.SetText(str(self.itemCount))
            self.stacksEdit.SetText(str(self.offerAllCount))
        for widget in self._OfferAllWidgets():
            widget.Hide()                       # shown while the box is checked (OnUpdate)
        self.lastPiece = self.itemCount if self.offerAllCount else None
        self.lastChecked = False
        self.lastTotal = None
        uiCommon.MoneyInputDialog.Open(self)
        self.SetAveragePriceText(getattr(localeInfo,
            "VIRTUAL_MARKET_BUNDLE_PRICE", "Cena za %d ks") % self.itemCount)
        self._LayoutMarket()
        self.SetCenterPosition()
        self.OnUpdate()

    def _LayoutMarket(self):
        # The base money layout does not know about our unit price or checkbox.
        skin = getattr(self, "r1skin", None)
        width, gap = 420, 8
        y = 8 if skin else 32
        if skin:
            import uir1
            import uir1tokens as T
            uir1.SetFont(self.unitPrice, skin.kit.font("text_s"))
            uir1.SetFont(self.stacksLabel, skin.kit.font("text_s"))
            if skin.title is not None and skin.title.GetText():
                cell = skin.kit.cell("text")
                skin.title.SetPosition(width // 2, y + cell // 2)
                y += cell + gap
            cell, fieldHeight = skin.kit.cell("text_s"), T.FIELD_H
        else:
            cell, fieldHeight = 16, 18
        self.unitPrice.SetVerticalAlignCenter()
        average = self.GetChild("AverageValue")
        average.SetVerticalAlignCenter()
        average.SetPosition(0, y + cell // 2)
        y += cell + gap
        field = skin.field if skin else self.GetChild("InputSlot")
        if skin:
            field.SetWidth(width - 2 * T.PAD)
        field.SetPosition(T.PAD if skin else 0, y)
        y += fieldHeight + gap
        self.moneyText.SetVerticalAlignCenter()
        self.moneyText.SetPosition(0, y + cell // 2)
        y += cell + gap
        self.unitPrice.SetPosition(0, y + cell // 2)
        y += cell + gap
        if self._CheckBoxShown():
            self.matching.SetPosition(18, y)
            y += max(18, self.matching.GetHeight()) + gap
        if self.offerAllCount and self.stacksField is not None and self.matching.IsChecked():
            # "Po [X] ks      Hromádek: [N]" under the check box, N right-aligned to the inner edge; the summary
            # "N × X ks = celkem Y ks, zbude Z ks" under them.
            fieldHeight = T.FIELD_H if skin else 18
            right = width - (T.PAD if skin else 18)
            middle = y + fieldHeight // 2
            for line in (self.pieceLabel, self.pieceUnit, self.stacksLabel, self.summary):
                if skin:
                    uir1.SetFont(line, skin.kit.font("text_s"))
                line.SetVerticalAlignCenter()
            self.pieceLabel.SetPosition(18, middle)
            labelWidth = self.pieceLabel.GetTextSize()[0] if hasattr(self.pieceLabel, "GetTextSize") else 20
            self.pieceField.SetPosition(18 + labelWidth + 6, y)
            self.pieceUnit.SetPosition(18 + labelWidth + 6 + 64 + 6, middle)
            self.stacksField.SetPosition(right - 64, y)
            self.stacksLabel.SetHorizontalAlignRight()
            self.stacksLabel.SetPosition(right - 64 - 6, middle)
            y += fieldHeight + gap
            self.summary.SetPosition(18, y + cell // 2)
            y += cell + gap
        buttons = (self.acceptButton, self.cancelButton)
        buttonWidth = sum(button.GetWidth() for button in buttons) + 10
        x = (width - buttonWidth) // 2
        for button in buttons:
            button.SetPosition(x if skin else x - (width - button.GetWidth()) // 2, y)
            x += button.GetWidth() + 10
        height = y + max(button.GetHeight() for button in buttons) + 12
        self.SetSize(width, height)
        self.board.SetSize(width, height)
        if skin:
            skin.frame.Resize(width, height)

    def SetTitle(self, name):
        uiCommon.MoneyInputDialog.SetTitle(self, name)
        if hasattr(self, "unitPrice"):
            self._LayoutMarket()

    def IsMatching(self):
        return self.bulkAvailable and self.matching.IsChecked()

    def IsOfferAll(self):
        """The box is checked: the price is of 1 piece, the offer is N listings of X pieces (N may be 1: one
        listing of X pieces split from the stack)."""
        return self.offerAllCount > 0 and bool(self.matching.IsChecked()) and self.GetOfferAllCount() >= 1

    def SetValue(self, value):
        uiCommon.MoneyInputDialog.SetValue(self, value)
        self.OnUpdate()

    def _OfferAllChanged(self, checked):
        """The box toggled: the price field switches between the offer's price and the price of 1 piece, the
        fields and the summary show or hide."""
        self.lastChecked = checked
        value = int(self.GetValue() or 0)
        if value > 0:
            unit = value // self.itemCount if checked else value * self.itemCount
            uiCommon.MoneyInputDialog.SetValue(self, max(1, unit))
        self.SetAveragePriceText(getattr(localeInfo, "VIRTUAL_MARKET_UNIT_PRICE", "Cena za 1 ks") if checked else
            getattr(localeInfo, "VIRTUAL_MARKET_BUNDLE_PRICE", "Cena za %d ks") % self.itemCount)
        for widget in self._OfferAllWidgets():
            widget.Show() if checked else widget.Hide()
        self._LayoutMarket()
        self.lastTotal = None

    def OnUpdate(self):
        checked = bool(self.offerAllCount and self.matching.IsChecked())
        if checked != self.lastChecked:
            self._OfferAllChanged(checked)
        if checked:
            piece = self.GetOfferAllPiece()
            if piece != self.lastPiece:
                # a new X: N follows to every listing the inventory gives at it
                self.lastPiece = piece
                self.stacksEdit.SetText(str(self.MaxOfferAllCount()))
                self.lastTotal = None
        total = self.GetValue()
        key = (total, checked, self.GetOfferAllCount() if checked else 0)
        if key != self.lastTotal:
            self.lastTotal = key
            r1 = getattr(self, "r1skin", None) is not None
            if not checked:
                self.unitPrice.SetText(UnitPriceText(total, self.itemCount, r1))
                return
            piece, listings = self.GetOfferAllPiece(), self.GetOfferAllCount()
            self.unitPrice.SetText(getattr(localeInfo, "VIRTUAL_MARKET_OFFER_ALL_LISTING", "Nabídka: %d ks za %s") % (
                piece, _Yang(int(total or 0) * piece, r1)))
            whole = sum(self.offerAllStacks)
            self.summary.SetText(getattr(localeInfo, "VIRTUAL_MARKET_OFFER_ALL_SUMMARY",
                "%d × %d ks = celkem %d ks, zbude %d ks") % (listings, piece, listings * piece,
                whole - listings * piece))
