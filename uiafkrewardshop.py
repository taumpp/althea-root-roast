"""Item Shop AFK page. Balances, prices and purchases belong to the server."""
import app
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


# Optional "coming soon" art of the closed AFK shop (480x170 px, R1 item shop kit); missing file = nothing drawn.
SOON_IMAGE = 'd:/ymir work/ui/public/althea_r1_itemshop/afk_coming_soon.png'
SOON_IMAGE_POS = (135, 150)


def _FileExists(path):
    checker = getattr(app, 'IsExistFile', None)
    if checker is not None:
        try:
            return bool(checker(path))
        except Exception:
            return False
    try:
        import pack
        return bool(pack.Exist(path))
    except Exception:
        return False


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
    catalog = [data[i] for i in (6, 7, 8, 9)]
    # An all-zero catalog = the server keeps the shop hidden (AFK_SHOP_ENABLED 0); the balance still counts.
    if data[2] != 100 or data[1] > data[2] or data[5] > 6 or (any(catalog) and not all(catalog)):
        return None
    return tuple(data)


def ShopOffered(data=None):
    # The AFK shop exists only while the server sends its catalog (server CONFIG AFK_SHOP_ENABLED 1).
    if data is None:
        data = Snapshot()
    return data is not None and all(data[i] for i in (6, 7, 8, 9))


REASONS = (
    ('AFK_SHOP_EARNING', 'Earning AFK points'),
    ('AFK_SHOP_QUALIFYING', 'Waiting for 10 minutes of inactivity'),
    ('AFK_SHOP_INELIGIBLE', 'AFK points require an AFK zone (city safe zone)'),
    ('AFK_SHOP_IDENTITY', 'Device verification is required for AFK rewards'),
    ('AFK_SHOP_DEVICE_BUSY', 'Another account on this device is active or earning AFK points'),
    ('AFK_SHOP_UNAVAILABLE', 'AFK points are unavailable.'),
    ('AFK_SHOP_LIMIT', 'Weekly earning limit reached'),
)


_cause = 0
CAUSES = {
    1: ('AFK_SHOP_CAUSE_OUTSIDE', 'AFK points paused: outside an AFK zone'),
    2: ('AFK_SHOP_CAUSE_DUNGEON', 'AFK points paused: dungeon, arena, war or PvP fight'),
    3: ('AFK_SHOP_CAUSE_DEAD', 'AFK points paused: dead or stunned'),
    4: ('AFK_SHOP_CAUSE_COMBAT', 'AFK points paused: combat in the last 10 s'),
    5: ('AFK_SHOP_CAUSE_WINDOW', 'AFK points paused: shop, storage, trade or crafting window open'),
    6: ('AFK_SHOP_CAUSE_OBSERVER', 'AFK points paused: observer mode'),
    7: ('AFK_SHOP_CAUSE_TRADE', 'AFK points paused: recent trade, storage or upgrade'),
}


def SetCause(code):
    global _cause
    # The command has one unsigned decimal argument. Future codes use the
    # generic reason, malformed input must not overwrite the last valid cause.
    if not isinstance(code, (str, int)) or isinstance(code, bool):
        return False
    value = str(code)
    if not value or any(char not in '0123456789' for char in value):
        return False
    try:
        _cause = int(value)
    except ValueError:
        return False
    return True


_zones = ()
MAX_ZONE_MAPS = 32


def SetZones(maps):
    """AfkRewardZonesV1 <map,map,...>: the server's AFK zone maps in order.

    None clears the list (new game session). Malformed input keeps the last
    valid list; an old server never sends the command and the line stays hidden.
    """
    global _zones
    if maps is None:
        _zones = ()
        return True
    if not isinstance(maps, str):
        return False
    result = []
    for part in maps.split(','):
        if not part or len(part) > 4 or any(char not in '0123456789' for char in part):
            return False
        value = int(part)
        if value < 1 or value in result:
            return False
        result.append(value)
    if not result or len(result) > MAX_ZONE_MAPS:
        return False
    _zones = tuple(result)
    return True


def ZoneName(mapIndex):
    # Locale short name, then the minimap name, then a numbered fallback.
    for name in (getattr(localeInfo, 'AFK_SHOP_ZONE_MAP_%d' % mapIndex, None),
                 getattr(localeInfo, 'MINIMAP_ZONE_NAME_DICT_BY_IDX', {}).get(mapIndex)):
        if isinstance(name, str) and name.strip():
            return name.strip()
    return Text('AFK_SHOP_ZONE_MAP_FALLBACK', 'map %d') % mapIndex


def ZonesText():
    if not _zones:
        return ''
    return Text('AFK_SHOP_ZONES', 'AFK zones (squares): %s') % ', '.join(ZoneName(index) for index in _zones)


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
        # Below the offer cards when the shop is open, in the delivery line's place when it is closed.
        self.zonesText = self._Label(18, 307, '')
        self._Label(18, 330, Text('AFK_SHOP_RULES', 'Hours 1-4: 1 point/hour. From hour 5: 2 points/hour.'))
        self._Label(18, 353, Text('AFK_SHOP_RESET', 'Weekly limit resets Monday 00:00 (Prague). Unspent points remain.'))
        self.deliveryText = self._Label(18, 376, Text('AFK_SHOP_DELIVERY', 'Rewards go to your inventory. If full, free space and reopen this page.'))
        self.resultText = self._Label(18, 409, '')
        # Closed shop (the server sends no catalog, AFK_SHOP_ENABLED 0): notice, what the points will buy, optional art.
        self.closedText = self._Label(18, 100, Text('AFK_SHOP_DISABLED',
            'The AFK shop is closed for now. Your points keep adding up and the shop opens soon.'))
        self.soonText = self._Label(18, 123, Text('AFK_SHOP_SOON_DESC',
            'Soon you can spend AFK points on rewards such as VIP and rings. You are collecting points already.'))
        self.soonImage = None
        if _FileExists(SOON_IMAGE):
            image = ui.ImageBox()
            image.SetParent(self)
            image.SetPosition(*SOON_IMAGE_POS)
            image.AddFlag('not_pick')
            try:
                image.LoadImage(SOON_IMAGE)
                self.soonImage = image
                self.widgets.append(image)
            except Exception:
                self.soonImage = None
        for catalog in (1, 2):
            y = 116 + (catalog - 1) * 98
            icon = ui.ImageBox()
            icon.SetParent(self)
            icon.SetPosition(24, y + 12)
            # Hovering the reward icon shows the item tooltip, like an Item Shop offer.
            icon.SAFE_SetStringEvent('MOUSE_OVER_IN', self.OverInOffer, catalog)
            icon.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.OverOutOffer)
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
        closed = self.current is not None and not ShopOffered(self.current)
        for widget in (self.closedText, self.soonText, self.soonImage):
            if widget is not None:
                widget.Show() if closed else widget.Hide()
        self.deliveryText.Hide() if closed else self.deliveryText.Show()
        self.zonesText.SetPosition(18, 376 if closed else 307)
        self.zonesText.SetText(ZonesText() if self.current is not None else '')
        if closed:
            # Points and rules stay; no offers and no buy buttons until the server sends the catalog.
            balance, earned, cap, reason = self.current[0], self.current[1], self.current[2], self.current[5]
            self.weeklyText.SetText('%s: %d    %s' % (Text('AFK_SHOP_BALANCE', 'AFK points'), balance,
                                                     Text('AFK_SHOP_WEEKLY', 'Earned this week: %d/%d') % (earned, cap)))
            self.statusText.SetText(Text(*self._Reason(reason)))
            for card in self.cards.values():
                card['buy'].Disable()
                for key in ('icon', 'title', 'price', 'description', 'buy'):
                    card[key].Hide()
            self.current = None
            return
        if self.current is None:
            # No offer from the server (yet): the page stays reachable, without the server-owned offers.
            self.weeklyText.SetText('')
            self.statusText.SetText(Text('AFK_SHOP_UNAVAILABLE', 'AFK points are unavailable.'))
            for card in self.cards.values():
                card['buy'].Disable()
                for key in ('icon', 'title', 'price', 'description', 'buy'):
                    card[key].Hide()
            return
        for card in self.cards.values():
            for key in ('title', 'price', 'description', 'buy'):
                card[key].Show()
        balance, earned, cap, streak, qualification, reason, vip, vipPrice, ring, ringPrice = self.current
        self.weeklyText.SetText(Text('AFK_SHOP_WEEKLY', 'Earned this week: %d/%d') % (earned, cap))
        self.statusText.SetText(Text(*self._Reason(reason)))
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

    def _Tooltip(self):
        try:
            import osfInfo
            interface = osfInfo.GetInterfaceInstance()
        except Exception:
            return None
        return getattr(interface, 'tooltipItem', None) if interface else None

    def OverInOffer(self, catalog):
        if self.current is None or catalog not in self.cards:
            return
        vnum = self.current[6 if catalog == 1 else 8]
        tooltip = self._Tooltip()
        if tooltip and vnum:
            tooltip.SetItemToolTip(vnum, itemShopOffer=True)

    def OverOutOffer(self):
        tooltip = self._Tooltip()
        if tooltip:
            tooltip.HideToolTip()

    def _Reason(self, reason):
        if reason == 2 and _cause > 0:
            return CAUSES.get(_cause, REASONS[2])
        return REASONS[reason] if 0 <= reason < len(REASONS) else REASONS[5]

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
        self.OverOutOffer()
        self.Hide()

    def Destroy(self):
        self.Close()
        self.cards = {}
        self.widgets = []
