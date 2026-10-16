"""Item Shop AFK page. Balances, prices and purchases belong to the server."""
import ui
import net
import item
import localeInfo
import uiCommon
import uicrimsoncontrols


def Text(key, fallback):
    return getattr(localeInfo, key, fallback)


def IsSupported():
    # Older executables expose readiness only; keep their fail-closed fallback.
    offered = getattr(net, "HasAfkRewardsOffer", None)
    if offered is not None:
        return bool(offered())
    return bool(getattr(net, "IsAfkRewardsAvailable", lambda: False)())


def Snapshot():
    available = getattr(net, 'IsAfkRewardsAvailable', None)
    getter = getattr(net, 'GetAfkRewardsSnapshot', None)
    if not available or not getter or not available():
        return None
    data = getter()
    if not isinstance(data, (tuple, list)) or len(data) != 10:
        return None
    if any(not isinstance(value, int) or value < 0 for value in data):
        return None
    if data[2] != 100 or data[1] > data[2] or data[5] > 6 or not all(data[i] for i in (6, 7, 8, 9)):
        return None
    return tuple(data)


class AfkRewardShop(ui.Window):
    def __init__(self, parent):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(200, 76)
        self.SetSize(750, 445)
        self.widgets = []
        self.cards = {}
        self.question = None
        self.selectedOffer = None
        self.current = None
        self._Label(18, 10, Text('AFK_SHOP_TITLE', 'AFK shop'))
        self.weeklyText = self._Label(18, 43, '')
        self.statusText = self._Label(18, 68, '')
        self._Label(18, 330, Text('AFK_SHOP_RULES', 'Hours 1-4: 1 point/hour. From hour 5: 2 points/hour.'))
        self._Label(18, 353, Text('AFK_SHOP_RESET', 'Weekly limit resets Monday 00:00 (Prague). Unspent points remain.'))
        self._Label(18, 376, Text('AFK_SHOP_DELIVERY', 'Rewards go to your inventory. If full, free space and reopen this page.'))
        self.resultText = self._Label(18, 409, '')
        for catalog in (1, 2):
            y = 116 + (catalog - 1) * 98
            icon = ui.ImageBox()
            icon.SetParent(self)
            icon.SetPosition(24, y + 12)
            icon.AddFlag('not_pick')
            self.widgets.append(icon)
            title = self._Label(76, y + 5, '')
            price = self._Label(76, y + 31, '')
            description = self._Label(76, y + 55, Text('AFK_SHOP_BOUND', '7 days from delivery. Cannot be traded.'))
            buy = ui.Button()
            buy.SetParent(self)
            buy.SetPosition(553, y + 16)
            uicrimsoncontrols.ApplyVisuals(buy, '170x24')
            buy.SetText(Text('AFK_SHOP_BUY', 'Buy with AFK points'))
            buy.SetEvent(self.AskBuy, catalog)
            buy.Show()
            self.widgets.append(buy)
            self.cards[catalog] = dict(icon=icon, title=title, price=price, buy=buy, description=description)
        self.Refresh()

    def _Label(self, x, y, text):
        label = ui.TextLine()
        label.SetParent(self)
        label.AddFlag('not_pick')
        label.SetPosition(x, y)
        label.SetFontName('Tahoma:14')
        label.SetText(text)
        label.Show()
        self.widgets.append(label)
        return label

    def Refresh(self):
        self.current = Snapshot()
        if self.current is None:
            self.weeklyText.SetText('')
            self.statusText.SetText(Text('AFK_SHOP_UNAVAILABLE', 'AFK points are unavailable.'))
            for card in self.cards.values():
                card['buy'].Disable()
            return
        balance, earned, cap, streak, qualification, reason, vip, vipPrice, ring, ringPrice = self.current
        self.weeklyText.SetText(Text('AFK_SHOP_WEEKLY', 'Earned this week: %d/%d') % (earned, cap))
        reasons = (
            ('AFK_SHOP_EARNING', 'Earning AFK points'),
            ('AFK_SHOP_QUALIFYING', 'Waiting for 10 minutes of inactivity'),
            ('AFK_SHOP_INELIGIBLE', 'AFK rewards require a safe zone in the first city'),
            ('AFK_SHOP_IDENTITY', 'Device verification is required for AFK rewards'),
            ('AFK_SHOP_DEVICE_BUSY', 'Another account on this device is active or earning AFK points'),
            ('AFK_SHOP_UNAVAILABLE', 'AFK points are unavailable.'),
            ('AFK_SHOP_LIMIT', 'Weekly earning limit reached'),
        )
        self.statusText.SetText(Text(*reasons[reason]))
        for catalog, vnum, price in ((1, vip, vipPrice), (2, ring, ringPrice)):
            card = self.cards[catalog]
            item.SelectItem(vnum)
            card['title'].SetText(item.GetItemName())
            card['icon'].LoadImage(item.GetIconImageFileName())
            card['icon'].Show()
            card['price'].SetText(Text('AFK_SHOP_PRICE', '%d AFK points') % price)
            if balance >= price and reason != 5:
                card['buy'].Enable()
            else:
                card['buy'].Disable()

    def AskBuy(self, catalog):
        self.CancelQuestion()
        self.Refresh()
        if self.current is None or catalog not in self.cards or self.current[5] == 5:
            return
        index = 6 if catalog == 1 else 8
        vnum, price = self.current[index:index + 2]
        if self.current[0] < price:
            return
        self.selectedOffer = (catalog, vnum, price)
        item.SelectItem(vnum)
        dialog = uiCommon.QuestionDialog2()
        dialog.SetText1(Text('AFK_SHOP_CONFIRM', 'Buy %s?') % item.GetItemName())
        dialog.SetText2(Text('AFK_SHOP_PRICE', '%d AFK points') % price)
        dialog.SetAcceptEvent(self._AcceptBuy)
        dialog.SetCancelEvent(self.CancelQuestion)
        dialog.OnPressEscapeKey = self.CancelQuestion
        dialog.SetCenterPosition()
        dialog.Show()
        dialog.SetTop()
        self.question = dialog

    def _AcceptBuy(self):
        selected = self.selectedOffer
        self.CancelQuestion()
        self.Refresh()
        if not selected or self.current is None or self.current[5] == 5:
            return
        catalog, vnum, price = selected
        index = 6 if catalog == 1 else 8
        if self.current[index:index + 2] != (vnum, price) or self.current[0] < price:
            self.resultText.SetText(Text('AFK_SHOP_CHANGED', 'The offer changed. Please select it again.'))
            return
        sender = getattr(net, 'SendAfkRewardPurchase', None)
        if sender and sender(catalog):
            self.resultText.SetText(Text('AFK_SHOP_PENDING', 'Processing purchase...'))
        else:
            self.resultText.SetText(Text('AFK_SHOP_RETRY', 'Purchase unavailable or another purchase is pending.'))

    def OnPurchaseResult(self, result, balance):
        messages = (
            ('AFK_SHOP_BOUGHT', 'Purchased. Delivery to your inventory is pending if it is full.'),
            ('AFK_SHOP_BOUGHT', 'Purchased. Delivery to your inventory is pending if it is full.'),
            ('AFK_SHOP_NO_POINTS', 'Not enough AFK points.'),
            ('AFK_SHOP_BOX_FULL', 'Free inventory space to receive your previous purchases first.'),
            ('AFK_SHOP_CONFLICT', 'Purchase could not be confirmed. Reopen the shop.'),
            ('AFK_SHOP_RETRY', 'Purchase unavailable or another purchase is pending.'),
            ('AFK_SHOP_INVALID', 'This AFK offer is unavailable.'),
        )
        if 0 <= result < len(messages):
            self.resultText.SetText(Text(*messages[result]))
        self.Refresh()

    def CancelQuestion(self):
        if self.question:
            self.question.Hide()
            self.question.SetAcceptEvent(lambda: None)
            self.question.SetCancelEvent(lambda: None)
            self.question.OnPressEscapeKey = lambda: True
            self.question = None
        self.selectedOffer = None
        return True

    def Close(self):
        self.CancelQuestion()
        self.Hide()

    def Destroy(self):
        self.Close()
        self.cards = {}
        self.widgets = []
