# -*- coding: utf-8 -*-
"""Sale history of the player's market shop ("Můj obchod" -> Historie).

The game server answers the chat
command "/market_sales [before]" with command lines; game.py hands every line
that starts with "MarketSalesV1" to RECEIVER.ServerLine:

    MarketSalesV1 C 2                                   capability (on login; 1 = the 21. 10. server)
    MarketSalesV1 S <before> <status>                   refused / failed
    MarketSalesV1 H <before> <more> <next> <rows> <today> <week> <month> <count>
    MarketSalesV1 R <before> <credit> <sold_at> <vnum> <count> <price> [<buyer>]
    MarketSalesV1 I <before> <credit> <rarity> <transmutation> <6 sockets> <7 x type value> <4 x type value>
    MarketSalesV1 E <before>

Nothing is asked until the tab is opened; a server page holds 50 sales, the
window shows a page of them (layout(rows) -> rows per page: the view fits its fixed-height rows into its room,
a tall item in one slot cell since v4; without it ROWS_PER_PAGE) and asks for the next server page only when
the player pages past the loaded rows. Since capability 2 a row names the buyer
(current character name, "-" = deleted character; only the seller gets it) and the I line after it carries the
sold piece for the item tooltip (no I line = the tooltip shows the item by vnum).
A row is (credit, sold_at, vnum, count, price, buyer, item): buyer "" when unknown, item None or a dict
{"rarity", "transmutation", "sockets", "attributes", "random"}.
Pure Python (no game modules at import), so it loads outside the game too.
"""
import time

# Rows of a page without a layout, and the guess for pages not loaded yet: 6 market rows (51 px) fit the view.
ROWS_PER_PAGE = 6
SERVER_PAGE = 50
# The game accepts one request per player and second (kRateLimitMs 1000).
REQUEST_GAP = 1.05
COMMAND = "/market_sales"
PREFIX = "MarketSalesV1"

STATUS_DISABLED = 1
STATUS_UNAVAILABLE = 2
STATUS_INVALID = 3
STATUS_RATE_LIMITED = 4
STATUS_INTERNAL = 5


# --------------------------------------------------------------------------- Prague time
def _LastSunday(year, month):
    """Day of month of the last Sunday of March / October (both have 31 days)."""
    # time.gmtime of the 31st: tm_wday 0 = Monday ... 6 = Sunday
    weekday = time.gmtime(_UtcEpoch(year, month, 31)).tm_wday
    return 31 - ((weekday + 1) % 7)


def _UtcEpoch(year, month, day, hour=0):
    # days from civil (proleptic Gregorian), no dependency on the PC time zone
    y = year - (1 if month <= 2 else 0)
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    mp = (month + 9) % 12
    doy = (153 * mp + 2) // 5 + day - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    days = era * 146097 + doe - 719468
    return days * 86400 + hour * 3600


def PragueOffset(epoch):
    """Seconds Prague is ahead of UTC at the UTC epoch (EU rule: summer time from the last Sunday of March 01:00
    UTC to the last Sunday of October 01:00 UTC)."""
    year = time.gmtime(int(epoch)).tm_year
    start = _UtcEpoch(year, 3, _LastSunday(year, 3), 1)
    end = _UtcEpoch(year, 10, _LastSunday(year, 10), 1)
    return 7200 if start <= int(epoch) < end else 3600


def PragueTime(epoch):
    """time.struct_time of the Prague wall clock at a UTC epoch."""
    epoch = int(epoch)
    return time.gmtime(epoch + PragueOffset(epoch))


def FormatTime(epoch):
    """'21.10. 14:32' in Prague time, whatever the player's PC zone is."""
    if not epoch:
        return "-"
    local = PragueTime(epoch)
    return "%d.%d. %02d:%02d" % (local.tm_mday, local.tm_mon, local.tm_hour, local.tm_min)


# --------------------------------------------------------------------------- model
def _Int(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(value)
    if number < 0:
        raise ValueError(value)
    return number


def _Signed(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(value)


SOCKETS = 6
ATTRIBUTES = 7
RANDOM_APPLIES = 4
ITEM_FIELDS = 2 + SOCKETS + 2 * ATTRIBUTES + 2 * RANDOM_APPLIES
CAPABILITIES = ("1", "2")


def _Pairs(values):
    return [(values[index], values[index + 1]) for index in range(0, len(values), 2)]


def ParseItem(args):
    """The fields of an I line after <before> <credit> as the tooltip dict."""
    if len(args) != ITEM_FIELDS:
        raise ValueError(args)
    values = [_Signed(value) for value in args]
    sockets = values[2:2 + SOCKETS]
    pairs = values[2 + SOCKETS:]
    if min(values[:2] + sockets) < 0:
        raise ValueError(args)
    return {"rarity": values[0], "transmutation": values[1], "sockets": sockets,
            "attributes": _Pairs(pairs[:2 * ATTRIBUTES]), "random": _Pairs(pairs[2 * ATTRIBUTES:])}


class SalesHistory(object):
    """The loaded pages of one character. send(text) sends a chat command, clock() returns seconds."""

    def __init__(self, send=None, clock=None):
        self.send = send
        self.clock = clock or time.time
        self.listeners = []
        self.available = False
        self.layout = None          # callable(rows) -> [rows per page], set by the view
        self.Reset()

    # ---- state --------------------------------------------------------------------------------------------
    def Reset(self):
        self.rows = []
        self.totals = None          # (today, week, month, count)
        self.hasMore = False
        self.nextBefore = 0
        self.loaded = False
        self.status = 0
        self.waiting = None         # the <before> of the request in flight
        self.queued = None          # a request waiting for the rate gap
        self.lastSent = None
        self.buffer = None
        self.page = 0

    def AddListener(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def RemoveListener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _Changed(self):
        for callback in list(self.listeners):
            try:
                callback()
            except Exception:
                pass

    # ---- requests -----------------------------------------------------------------------------------------
    def Open(self):
        """The tab was opened: the newest page again (sales may have happened meanwhile), page 1."""
        self.page = 0
        self.status = 0
        self._Request(0)
        self._Changed()

    def Refresh(self):
        self.Open()

    def IsLoading(self):
        return self.waiting is not None or self.queued is not None

    def _Request(self, before):
        if self.waiting is not None and self.waiting == before:
            return
        self.queued = before
        self.Tick()

    def Tick(self):
        """Sends a queued request once the rate gap has passed (the window calls it from OnUpdate)."""
        if self.queued is None or self.waiting is not None:
            return False
        now = self.clock()
        if self.lastSent is not None and now - self.lastSent < REQUEST_GAP - 1e-6:
            return False
        before, self.queued = self.queued, None
        self.lastSent = now
        self.waiting = before
        self.buffer = None
        if self.send:
            self.send("%s %d" % (COMMAND, before) if before else COMMAND)
        return True

    # ---- pages --------------------------------------------------------------------------------------------
    def Count(self):
        if self.totals is None:
            return len(self.rows)
        return max(self.totals[3], len(self.rows))

    def _Pages(self):
        """[(start, end)] of the finished pages of the loaded rows. While the server has more, the last loaded page
        is not finished (the next server page may still fill it)."""
        sizes = None
        if self.layout is not None and self.rows:
            try:
                sizes = [int(size) for size in self.layout(self.rows)]
            except Exception:
                sizes = None
            if sizes is not None and (sum(sizes) != len(self.rows) or min(sizes) < 1):
                sizes = None
        if sizes is None:
            sizes = [min(ROWS_PER_PAGE, len(self.rows) - start) for start in range(0, len(self.rows), ROWS_PER_PAGE)]
        pages, start = [], 0
        for size in sizes:
            pages.append((start, start + size))
            start += size
        if self.hasMore and pages:
            pages.pop()
        return pages

    def _Bounds(self, page):
        pages = self._Pages()
        if page < len(pages):
            return pages[page]
        start = (pages[-1][1] if pages else 0) + (page - len(pages)) * ROWS_PER_PAGE
        return (start, start + ROWS_PER_PAGE)

    def PageCount(self):
        pages = self._Pages()
        rest = max(0, self.Count() - (pages[-1][1] if pages else 0)) if self.hasMore or not self.loaded else 0
        return max(1, len(pages) + (rest + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)

    def SetPage(self, page):
        page = max(0, min(int(page), self.PageCount() - 1))
        self.page = page
        self._EnsureRows()
        self._Changed()

    def NextPage(self):
        self.SetPage(self.page + 1)

    def PreviousPage(self):
        self.SetPage(self.page - 1)

    def VisibleRows(self):
        start, end = self._Bounds(self.page)
        return self.rows[start:end]

    def PageReady(self):
        """True when the visible page is loaded (or nothing more exists)."""
        return not self.hasMore or self.page < len(self._Pages())

    def _EnsureRows(self):
        if self.loaded and not self.PageReady() and self.nextBefore:
            self._Request(self.nextBefore)

    # ---- server lines -------------------------------------------------------------------------------------
    def ServerLine(self, line):
        tokens = line.split()
        if not tokens or tokens[0] != PREFIX or len(tokens) < 2:
            return False
        try:
            return self._Apply(tokens[1], tokens[2:])
        except (ValueError, IndexError):
            # A malformed line ends the request: the window offers a refresh.
            self.waiting = None
            self.buffer = None
            self.status = STATUS_INTERNAL
            self._Changed()
            return True

    def _Apply(self, kind, args):
        if kind == "C":
            self.available = len(args) == 1 and args[0] in CAPABILITIES
            self.Reset()
            self._Changed()
            return True
        if not args:
            raise ValueError(kind)
        before = _Int(args[0])
        if before != self.waiting:
            return True             # a reply to a request the window no longer waits for
        if kind == "S":
            status = _Int(args[1])
            self.waiting = None
            if status == STATUS_RATE_LIMITED:
                self.queued = before        # asked again after the gap
            else:
                self.status = status
            self._Changed()
            return True
        if kind == "H":
            if len(args) != 8:
                raise ValueError(args)
            values = [_Int(value) for value in args[1:]]
            more, nextBefore, rows, today, week, month, count = values
            if more not in (0, 1) or (more == 1) != (nextBefore != 0) or rows > SERVER_PAGE:
                raise ValueError(args)
            self.buffer = {"more": more == 1, "next": nextBefore, "rows": rows,
                           "totals": (today, week, month, count), "items": []}
            return True
        if kind == "R":
            if self.buffer is None or len(args) not in (6, 7):
                raise ValueError(args)
            credit, soldAt, vnum, count, price = [_Int(value) for value in args[1:6]]
            if not credit or not vnum or not count or not price:
                raise ValueError(args)
            buyer = args[6] if len(args) == 7 and args[6] != "-" else ""
            self.buffer["items"].append((credit, soldAt, vnum, count, price, buyer, None))
            return True
        if kind == "I":
            # The sold piece of the row just received (same credit).
            items = self.buffer["items"] if self.buffer is not None else None
            if not items or len(args) != 2 + ITEM_FIELDS or _Int(args[1]) != items[-1][0]:
                raise ValueError(args)
            items[-1] = items[-1][:6] + (ParseItem(args[2:]),)
            return True
        if kind == "E":
            buffer, self.buffer = self.buffer, None
            self.waiting = None
            if buffer is None or len(buffer["items"]) != buffer["rows"]:
                raise ValueError(args)
            if before == 0:
                self.rows = []
            last = self.rows[-1][0] if self.rows else None
            for row in buffer["items"]:
                if last is None or row[0] < last:
                    self.rows.append(row)
                    last = row[0]
            self.totals = buffer["totals"]
            self.hasMore = buffer["more"]
            self.nextBefore = buffer["next"]
            self.loaded = True
            self.status = 0
            self.page = min(self.page, self.PageCount() - 1)
            self._EnsureRows()
            self._Changed()
            return True
        raise ValueError(kind)


def _SendChat(text):
    import net
    net.SendChatPacket(text)


RECEIVER = SalesHistory(send=_SendChat)


def ServerLine(line):
    return RECEIVER.ServerLine(line)


def UnitParts(total, count):
    """Yang per piece of a sold stack: ('exact', n), ('approx', rounded n) or ('fraction', a, b) below 1 Yang."""
    total, count = int(total), max(1, int(count))
    if total % count == 0:
        return ("exact", total // count)
    if total >= count:
        return ("approx", (2 * total + count) // (2 * count))
    a, b = total, count
    while b:
        a, b = b, a % b
    return ("fraction", total // a, count // a)


def FormatAmount(amount):
    """1250000 -> "1.250.000" (the grouping of the R1 Yang price)."""
    return "{:,}".format(int(amount)).replace(",", ".")
