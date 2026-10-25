# -*- coding: utf-8 -*-
# Terms of a sale to an NPC shop. The connected server sends them
# (EconomyViewV1) at every entry into the game and after every change; the
# three constants are what a server without that command pays.
PRICE_DIVISOR = 5
SHOP_TAX_PERCENT = 3
BULK_SELL_TAX_PERCENT = 0

SCHEMA = 1
SELL_GROUP = "sell"

_terms = None
_generation = 0
_watchers = []
_traced = False


def Terms():
    """(divisor, shop tax percent, bulk sale tax percent) of the next sale."""
    if _terms is not None:
        return _terms
    return (PRICE_DIVISOR, SHOP_TAX_PERCENT, BULK_SELL_TAX_PERCENT)


def IsServerFed():
    return _terms is not None


def Generation():
    return _generation


def _Price(unitPrice, count, countPerGold, taxPercent, divisor):
    if countPerGold:
        price = count // unitPrice if unitPrice else count
    else:
        price = unitPrice * count
    price //= divisor
    return price - price * taxPercent // 100


def SellPrice(unitPrice, count, countPerGold=False):
    divisor, shopTax, bulkTax = Terms()
    return _Price(unitPrice, count, countPerGold, shopTax, divisor)


def BulkSellPrice(unitPrice, count, countPerGold=False):
    divisor, shopTax, bulkTax = Terms()
    return _Price(unitPrice, count, countPerGold, bulkTax, divisor)


def _Number(text):
    try:
        if not text.isdigit():
            return None
        return int(text)
    except (AttributeError, TypeError, ValueError):
        return None


def _Parse(args):
    if len(args) < 2:
        return None
    schema, generation = _Number(args[0]), _Number(args[1])
    if schema != SCHEMA or not generation or generation > 2147483647:
        return None
    terms = None
    index = 2
    while index < len(args):
        if args[index] != SELL_GROUP:
            index += 1
            continue
        values = [_Number(value) for value in args[index + 1:index + 4]]
        if terms is not None or len(values) != 3 or None in values:
            return None
        divisor, shopTax, bulkTax = values
        if not (1 <= divisor <= 1000000 and 0 <= shopTax <= 100 and 0 <= bulkTax <= 100):
            return None
        terms = (divisor, shopTax, bulkTax)
        index += 4
    if terms is None:
        return None
    return generation, terms


def Receive(*args):
    """EconomyViewV1 <schema> <generation> sell <divisor> <shop tax> <bulk tax> [more groups]."""
    global _terms, _generation, _traced
    parsed = _Parse(args)
    if parsed is None:
        if not _traced:
            _traced = True
            try:
                import dbg
                dbg.TraceError("EconomyViewV1 ignored: %s" % " ".join(str(value) for value in args)[:120])
            except Exception:
                pass
        return False
    before = Terms()
    _generation, _terms = parsed
    if _terms != before:
        _Changed()
    return True


def Reset():
    """A new game session: the server it reaches speaks for itself."""
    global _terms, _generation
    before = Terms()
    _terms, _generation = None, 0
    if Terms() != before:
        _Changed()


def _Shown(window):
    try:
        return bool(window.IsShow())
    except Exception:
        return False


def Watch(window, callback):
    """Call ``callback`` when the terms change while ``window`` is shown (a sale question closes itself)."""
    _watchers[:] = [row for row in _watchers if row[0] is not window and _Shown(row[0])][-7:]
    _watchers.append((window, callback))


def _Changed():
    rows = list(_watchers)
    del _watchers[:]
    for window, callback in rows:
        if not _Shown(window):
            continue
        try:
            callback()
        except Exception:
            pass
        if _Shown(window):
            _watchers.append((window, callback))


class Receiver(object):
    def Receive(self, *args):
        Receive(*args)


receiver = Receiver()
