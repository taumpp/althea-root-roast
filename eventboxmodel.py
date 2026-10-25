# -*- coding: utf-8 -*-
"""EventBoxV1: atomic S/E snapshots, immediate B/M and visible-window P.
All gameplay values come from the server, including the item of the box
(box_vnum, the last field of S).
"""
import time

PREFIX = "EventBoxV1"
COMMAND = "/ebox_ui"
REFRESH_SECONDS = 10.0
REQUEST_GAP = 1.0  # server throttle: 900 ms
RETRY_SECONDS = 4.0
STATE_FIELDS = (
    "on", "phase", "now", "start", "end", "points", "need", "cd_until", "cd_sec",
    "today", "cap", "today_dev", "cap_dev", "drop_stop", "open_stop", "loot_ok", "mult_pct",
    "metin", "boss", "dungeon_boss", "mining", "fishing", "woodcut", "min_level",
    "min_hit_pct", "captcha", "boxes_in_inventory", "box_vnum",
)
# M arguments are numeric; timestamp positions are formatted in Prague by the client.
MESSAGE_ARGS = {
    'granted': ('number', 'cap'), 'progress': ('number', 'number'), 'before_start': ('time',),
    'drop_stopped': (), 'open_stopped': (), 'open_expired': ('time',), 'loot_off': (),
    'inventory_full': (), 'cooldown': ('time',), 'capped': ('number', 'cap', 'device', 'cap', 'time'),
}


def ChatMessage(key, args):
    # Also used while the window has never been opened. Keep engine imports lazy.
    import chat
    import localeInfo
    WEEKDAYS_LOCAL = tuple(localeInfo.EVENT_BOX_WEEKDAYS.split(','))
    formatted = []
    for kind, value in zip(MESSAGE_ARGS[key], args):
        if kind == 'time':
            local = time.gmtime(value + PragueOffset(value))
            value = localeInfo.EVENT_BOX_DATE % (WEEKDAYS_LOCAL[local.tm_wday],
                    local.tm_mday, local.tm_mon, local.tm_hour, local.tm_min)
        elif kind == 'cap' and value == 0:
            value = localeInfo.EVENT_BOX_UNLIMITED
        elif kind == 'device' and value < 0:
            value = localeInfo.EVENT_BOX_UNKNOWN
        formatted.append(value)
    text = getattr(localeInfo, 'EVENT_BOX_MSG_' + key.upper())
    if formatted:
        text = text % tuple(formatted)
    chat.AppendChat(chat.CHAT_TYPE_INFO, text)


def _DaysFromCivil(year, month, day):
	y = year - (1 if month <= 2 else 0)
	era = (y if y >= 0 else y - 399) // 400
	yoe = y - era * 400
	mp = (month + 9) % 12
	doy = (153 * mp + 2) // 5 + day - 1
	doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
	return era * 146097 + doe - 719468


def _LastSundayUtc(year, month):
	last = _DaysFromCivil(year, month, 31)
	weekday = (last + 4) % 7  # 0 = Sunday (1970-01-01 was a Thursday)
	return (last - weekday) * 86400 + 3600


def PragueOffset(epoch):
	"""EU rule: summer time from the last Sunday of March 01:00 UTC to the last Sunday of October 01:00 UTC."""
	epoch = int(epoch)
	year = time.gmtime(epoch).tm_year
	return 7200 if _LastSundayUtc(year, 3) <= epoch < _LastSundayUtc(year, 10) else 3600


WEEKDAYS = ("",) * 7  # time.struct_time.tm_wday: 0 = Monday


def FormatPrague(epoch, withDay=True):
	"""'ne 25. 10. 23:59' (or '23:59') in Prague time, whatever the player's PC zone is."""
	if not epoch:
		return "-"
	local = time.gmtime(int(epoch) + PragueOffset(epoch))
	clock = "%02d:%02d" % (local.tm_hour, local.tm_min)
	if not withDay:
		return clock
	return "%s %d. %d. %s" % (WEEKDAYS[local.tm_wday], local.tm_mday, local.tm_mon, clock)


def EndDay(epoch):
	"""Civil day immediately before an exclusive Prague deadline."""
	previous = int(epoch) - 1
	return time.gmtime(previous + PragueOffset(previous))


def FormatEnd(epoch):
	if not epoch:
		return "-"
	local = EndDay(epoch)
	return "%s %d. %d. 24:00" % (WEEKDAYS[local.tm_wday], local.tm_mday, local.tm_mon)


def FormatClock(epoch):
	"""'18:03:12' in Prague time (the time of the last answer in the window)."""
	local = time.gmtime(int(epoch) + PragueOffset(epoch))
	return "%02d:%02d:%02d" % (local.tm_hour, local.tm_min, local.tm_sec)


class State(object):
    def __init__(self):
        self.available = False
        self.values = dict.fromkeys(STATE_FIELDS, 0)
        self.receivedAt = 0.0

    def __getitem__(self, key):
        return self.values[key]

    @property
    def box_vnum(self):
        return self.values['box_vnum']

    def Now(self, clock=None):
        clock = time.time() if clock is None else clock
        return self['now'] + max(0, int(clock - self.receivedAt))

    def Capped(self):
        return ((self['cap'] > 0 and self['today'] >= self['cap']) or
                (self['cap_dev'] > 0 and self['today_dev'] >= self['cap_dev']))

    def DailyLimit(self):
        limits = [(self[today], self[cap]) for today, cap in
                  (('today', 'cap'), ('today_dev', 'cap_dev')) if self[cap] > 0 and self[today] >= 0]
        return min(limits, key=lambda value: value[1] - max(0, value[0])) if limits else None

    def CanOpen(self):
        return (self.available and self['phase'] != 2 and self['loot_ok'] and not self['open_stop']
                and self['start'] <= self.Now() < self['end'] and self['boxes_in_inventory'] > 0)


class Receiver(object):
    def __init__(self):
        self.state = State()
        self.pending = None
        self.loot = []
        self.lootPending = None
        self.visible = False
        self.buttonOn = False
        self.listener = None
        self.buttonListener = None
        self.uiEnabled = False
        self.messageListener = ChatMessage
        self.sender = None
        self.lastRequest = -REQUEST_GAP
        self.sentAt = self.answeredAt = 0.0
        self.waiting = self.queued = False

    def ServerLine(self, line, clock=None):
        tokens = line.split()
        if len(tokens) < 2 or tokens[0] != PREFIX:
            return False
        kind, args = tokens[1], tokens[2:]
        clock = time.time() if clock is None else clock
        try:
            if kind == 'LB' and not args:
                # A new set starts; the visible list is replaced atomically at LE so an
                # identical refresh (every /ebox_ui answer) never tears the grid down.
                self.lootPending = []
                return True
            if kind == 'L':
                if self.lootPending is None or len(args) != 3:
                    return False
                vnum, count, tier = map(int, args)
                if vnum <= 0 or not 1 <= count <= 200 or not 0 <= tier <= 3:
                    return False
                self.lootPending.append((vnum, count, tier))
                return True
            if kind == 'LE' and not args and self.lootPending is not None:
                changed = self.loot != self.lootPending
                self.loot, self.lootPending = self.lootPending, None
                if changed:
                    self._Notify()
                return True
            if kind == 'M':
                if not args or args[0] not in MESSAGE_ARGS:
                    return False
                key, raw = args[0], args[1:]
                if len(raw) != len(MESSAGE_ARGS[key]):
                    return False
                numbers = tuple(map(int, raw))
                if any(value < (-1 if kind == 'device' else 0)
                       for kind, value in zip(MESSAGE_ARGS[key], numbers)):
                    return False
                if self.messageListener:
                    self.messageListener(key, numbers)
                return True
            if kind == 'B' and len(args) in (1, 2) and all(a in ('0', '1') for a in args):
                changed = self.buttonOn != (args[0] == '1')
                self.buttonOn = args[0] == '1'
                # B <on> [<ui>]: ui 1 = the server shows the HUD button and window
                # (event_box_config ui_enabled / flag ebox_ui). Missing = 0 (hidden);
                # the box tooltip and "Show contents" work either way.
                self.uiEnabled = len(args) == 2 and args[1] == '1'
                if self.buttonListener:
                    self.buttonListener(self.HudVisible())
                if self.state.available:
                    self.state.values['on'] = int(self.buttonOn)
                    if self.pending is not None:
                        self.pending.values['on'] = int(self.buttonOn)
                    self._Notify()
                if self.visible and changed:
                    self.Request(clock)
                elif self.buttonOn and not self.state.available and not self.waiting:
                    self.Request(clock, bootstrap=True)
                return True
            if kind == 'S':
                self.pending = None
                if len(args) != len(STATE_FIELDS):
                    return False
                values = dict(zip(STATE_FIELDS, map(int, args)))
                if (values['phase'] not in range(3) or values['need'] <= 0 or
                        values['today_dev'] < -1 or not 0 <= values['min_hit_pct'] <= 100 or
                        any(values[k] not in (0, 1) for k in ('on', 'drop_stop', 'open_stop', 'loot_ok', 'captcha')) or
                        any(v < 0 for k, v in values.items() if k not in ('today_dev', 'min_hit_pct')) or
                        not values['start'] < values['end'] or values['box_vnum'] <= 0):
                    return False
                self.pending = State()
                self.pending.values = values
                self.pending.receivedAt = clock
                self.pending.available = True
                return True
            if kind == 'P' and len(args) == 3:
                values = list(map(int, args))
                if min(values) < 0 or not values[1]:
                    return False
                if self.visible and self.state.available:
                    for state in (self.state, self.pending):
                        if state is not None:
                            state.values.update(zip(('points', 'need', 'cd_until'), values))
                    self._Notify()
                return True
            if kind == 'E' and not args:
                self.state, self.pending = self.pending or State(), None
                self.waiting = False
                self.answeredAt = clock
                self._Notify()
                return True
        except (ValueError, TypeError, OverflowError):
            if kind in ('S', 'E'):
                self.pending = None
        if kind in ('S', 'E'):
            self.pending = None
        return False

    def HudVisible(self):
        return self.buttonOn and self.uiEnabled

    def _Notify(self):
        if self.listener:
            self.listener()

    def Request(self, clock=None, bootstrap=False):
        clock = time.time() if clock is None else clock
        if (not self.visible and not bootstrap) or self.sender is None:
            return False
        if clock - self.lastRequest < REQUEST_GAP:
            self.queued = True
            return False
        self.lastRequest = self.sentAt = clock
        self.waiting, self.queued = True, False
        self.sender(COMMAND)
        return True

    def Pump(self, clock=None):
        if not self.visible:
            return False
        clock = time.time() if clock is None else clock
        if self.waiting and clock - self.sentAt >= RETRY_SECONDS:
            self.waiting, self.queued = False, True
        if self.queued and clock - self.lastRequest >= REQUEST_GAP:
            return self.Request(clock)
        return False

    def Close(self):
        self.visible = self.waiting = self.queued = False
        self.pending = None


RECEIVER = Receiver()


def ServerLine(line):
    return RECEIVER.ServerLine(line)


def BoxTooltipLines(vnum):
    """Shared by inventory tooltip and offline preview; never changes selected item."""
    import item
    import localeInfo
    s = RECEIVER.state
    if not s.available or vnum != s.box_vnum:
        return []
    def date(epoch):
        local = time.gmtime(epoch + PragueOffset(epoch))
        return localeInfo.EVENT_BOX_DATE % (localeInfo.EVENT_BOX_WEEKDAYS.split(',')[local.tm_wday],
                local.tm_mday, local.tm_mon, local.tm_hour, local.tm_min)
    day = EndDay(s['end'])
    end = localeInfo.EVENT_BOX_END_DATE % (localeInfo.EVENT_BOX_WEEKDAYS.split(',')[day.tm_wday], day.tm_mday, day.tm_mon)
    lines = [localeInfo.EVENT_BOX_TERM % (date(s['start']), end),
             localeInfo.EVENT_BOX_DISAPPEAR % (localeInfo.EVENT_BOX_DEADLINE_DAYS.split(',')[day.tm_wday], day.tm_mday, day.tm_mon)]
    # No reward list here; "Show contents" (chest preview) lists them.
    item.SelectItem(vnum)
    return lines


def ChestPages(vnum, cols=5, rows=8):
    """Chest preview pages for the server box_vnum from the latest LB/L/LE list (no odds).
    Same {page: {slot: (vnum, count)}} shape as the server chest drop reply; items are
    first-fit packed by their vertical size into the 5 x 8 preview grid. None = not ours."""
    s = RECEIVER.state
    if not s.available or vnum != s.box_vnum or not RECEIVER.loot:
        return None
    import item
    pages, page, used = {}, 1, set()
    try:
        for reward, count, tier in RECEIVER.loot:
            item.SelectItem(reward)
            height = max(1, min(rows, item.GetItemSize()[1]))
            for attempt in (0, 1):
                slot = next((index for index in range(cols * rows)
                             if index // cols + height <= rows and
                             not any(index + k * cols in used for k in range(height))), None)
                if slot is not None:
                    break
                page, used = page + 1, set()
            used.update(slot + k * cols for k in range(height))
            pages.setdefault(page, {})[slot] = (reward, count)
    finally:
        item.SelectItem(vnum)
    return pages
