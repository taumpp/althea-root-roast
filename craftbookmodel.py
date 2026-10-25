# -*- coding: utf-8 -*-
"""Model of the craft book (Řemeslná kniha): the fishing, mining and woodcutting statistics of the character.

Pure Python (no engine module), so it can be tested on its own. The server answers "/craft state" with
CHAT_TYPE_COMMAND lines, one snapshot at a time:

    CraftBeginV1 <version=1>
    CraftFishV1 <casts> <games_completed> <catches> <nothing> <escaped> <abandoned> <seconds_at_water>
                <current_streak> <best_streak>
    CraftFishRowV1 <item_vnum> <count> <best_length>        0..n rows, best_length = cm * 100 (item socket 0)
    CraftMineV1 <attempts> <successes> <ore_total> <seconds_at_vein>
    CraftMineRowV1 <vein_mob_vnum> <raw_ore_item_vnum> <amount>   0..n rows
    CraftCheckV1 <great> <good> <miss>           the mining skill check (krok 2); an older server has no such line
    CraftWoodV1 <cuts> <wood> <seconds> <cuts_today> <daily_limit> <minigame_on>     woodcutting (optional)
    CraftWoodRowV1 <tree_vnum> <wood_vnum> <tier> <pieces>  0..n rows
    CraftWoodCheckV1 <great> <good> <miss> <perfect>        the woodcutting rhythm bar (woodcheckmodel)
    CraftEndV1

A snapshot becomes the shown one only on CraftEndV1 after a CraftBeginV1 of a known version with both summary
lines (CraftCheckV1 and the CraftWood* lines are optional: without them the counters are 0 and has_wood is False);
a new CraftBeginV1 drops what came
before it, a partial snapshot never replaces the last complete one.
A malformed recognized record discards the pending snapshot. Unknown commands
and rows outside a snapshot are ignored. Oversized collections never publish truncated data.
"""

VERSION = 1
MAX_ROWS = 512              # rows of one kind kept from one snapshot (a broken stream cannot grow without end)
MAX_VALUE = 2 ** 63 - 1

FISH_FIELDS = ('casts', 'games_completed', 'catches', 'nothing', 'escaped', 'abandoned', 'seconds_at_water',
               'current_streak', 'best_streak')
MINE_FIELDS = ('attempts', 'successes', 'ore_total', 'seconds_at_vein')
CHECK_FIELDS = ('great', 'good', 'miss')                # the mining skill check (miningcheckmodel)
WOOD_FIELDS = ('cuts', 'wood', 'seconds', 'cuts_today', 'daily_limit', 'minigame_on')
WOOD_CHECK_FIELDS = ('great', 'good', 'miss', 'perfect')  # the woodcutting rhythm bar (woodcheckmodel)

BEGIN, FISH, FISH_ROW, MINE, MINE_ROW, END = ('CraftBeginV1', 'CraftFishV1', 'CraftFishRowV1', 'CraftMineV1',
                                              'CraftMineRowV1', 'CraftEndV1')
CHECK = 'CraftCheckV1'
WOOD, WOOD_ROW, WOOD_CHECK = 'CraftWoodV1', 'CraftWoodRowV1', 'CraftWoodCheckV1'
ARITY = {BEGIN: 1, FISH: len(FISH_FIELDS), FISH_ROW: 3, MINE: len(MINE_FIELDS), MINE_ROW: 3, CHECK: len(CHECK_FIELDS),
         WOOD: len(WOOD_FIELDS), WOOD_ROW: 4, WOOD_CHECK: len(WOOD_CHECK_FIELDS), END: 0}

def _number(token):
    """A whole number >= 0 from a server token, else None."""
    if isinstance(token, bool):
        return None
    if isinstance(token, int):
        value = token
    else:
        text = str(token).strip()
        if not text.isdigit():
            return None
        value = int(text)
    if value < 0 or value > MAX_VALUE:
        return None
    return value


def _numbers(args, count):
    if args is None or len(args) != count:
        return None
    values = [_number(arg) for arg in args]
    if any(value is None for value in values):
        return None
    return values


class Stats(object):
    """Named counters (attributes from ``fields``), all 0 by default."""

    def __init__(self, fields, values=None):
        self.fields = fields
        for name, value in zip(fields, values or [0] * len(fields)):
            setattr(self, name, value)

    def Values(self):
        return tuple(getattr(self, name) for name in self.fields)

    def IsEmpty(self):
        return not any(self.Values())


class FishRow(object):
    def __init__(self, vnum, count, best_length):
        self.vnum, self.count, self.best_length = vnum, count, best_length


class MineRow(object):
    def __init__(self, vein_vnum, ore_vnum, amount):
        self.vein_vnum, self.ore_vnum, self.amount = vein_vnum, ore_vnum, amount


class WoodRow(object):
    def __init__(self, tree_vnum, wood_vnum, tier, pieces):
        self.tree_vnum, self.wood_vnum, self.tier, self.pieces = tree_vnum, wood_vnum, tier, pieces


class Snapshot(object):
    """One complete answer of the server."""

    def __init__(self, version=VERSION):
        self.version = version
        self.fish = Stats(FISH_FIELDS)
        self.mine = Stats(MINE_FIELDS)
        self.check = Stats(CHECK_FIELDS)                # the mining skill check: 0 0 0 without a CraftCheckV1 line
        self.wood = Stats(WOOD_FIELDS)                  # woodcutting: 0 without a CraftWoodV1 line (has_wood False)
        self.wood_check = Stats(WOOD_CHECK_FIELDS)
        self.fish_rows = []
        self.mine_rows = []
        self.wood_rows = []
        self.has_fish = self.has_mine = self.has_wood = False

    def IsEmpty(self):
        """Nothing recorded yet: every counter 0 and no row with a count."""
        return (self.fish.IsEmpty() and self.mine.IsEmpty() and self.check.IsEmpty() and
                self.wood.IsEmpty() and self.wood_check.IsEmpty() and
                not any(row.count for row in self.fish_rows) and
                not any(row.amount for row in self.mine_rows) and
                not any(row.pieces for row in self.wood_rows))

    def FishSuccess(self):
        return Ratio(self.fish.catches, self.fish.games_completed)

    def MineSuccess(self):
        return Ratio(self.mine.successes, self.mine.attempts)

    def FishRows(self):
        """Species sorted by catches (most first), then by the longest piece, then by vnum."""
        return sorted(self.fish_rows, key=lambda row: (-row.count, -row.best_length, row.vnum))

    def MineRows(self):
        """Veins sorted by the ore they gave (most first), then by vnum."""
        return sorted(self.mine_rows, key=lambda row: (-row.amount, row.ore_vnum, row.vein_vnum))

    def LongestFish(self):
        """The row with the longest piece, or None."""
        rows = [row for row in self.fish_rows if row.best_length > 0]
        return max(rows, key=lambda row: (row.best_length, -row.vnum)) if rows else None

    def MostCaughtFish(self):
        rows = self.FishRows()
        return rows[0] if rows and rows[0].count > 0 else None

    def RichestVein(self):
        rows = self.MineRows()
        return rows[0] if rows and rows[0].amount > 0 else None

    def WoodRows(self):
        """Trees sorted by tier, then by vnum."""
        return sorted(self.wood_rows, key=lambda row: (row.tier, row.tree_vnum))

    def WoodMarks(self):
        """Every mark of the rhythm bar (výborně + dobře + vedle)."""
        check = self.wood_check
        return check.great + check.good + check.miss


class CraftBookModel(object):
    """Collects the server lines; ``snapshot`` is the last complete snapshot (None before the first one)."""

    def __init__(self):
        self.snapshot = None
        self.pending = None
        self.received_rows = False
        self.revision = 0           # +1 with every complete snapshot

    def Feed(self, command, args=()):
        """One server line (command and its fields as strings). True when it completed a snapshot."""
        args = tuple(args or ())
        if command == BEGIN:
            self.received_rows = False
            values = _numbers(args, 1)
            self.pending = Snapshot(values[0]) if values is not None and values[0] == VERSION else None
            return False
        pending = self.pending
        if pending is None or command not in ARITY:
            return False
        if command == END:
            self.pending = None
            if args or (self.received_rows and not (pending.has_fish and pending.has_mine)):
                return False
            self.snapshot = pending
            self.revision += 1
            return True
        self.received_rows = True
        values = _numbers(args, ARITY[command])
        if values is None:
            self.pending = None
            return False
        if command == FISH:
            pending.fish = Stats(FISH_FIELDS, values)
            pending.has_fish = True
        elif command == MINE:
            pending.mine = Stats(MINE_FIELDS, values)
            pending.has_mine = True
        elif command == CHECK:
            pending.check = Stats(CHECK_FIELDS, values)
        elif command == WOOD:
            pending.wood = Stats(WOOD_FIELDS, values)
            pending.has_wood = True
        elif command == WOOD_CHECK:
            pending.wood_check = Stats(WOOD_CHECK_FIELDS, values)
        elif command == WOOD_ROW:
            if values[0] and values[2] <= 1000 and len(pending.wood_rows) < MAX_ROWS:
                pending.wood_rows.append(WoodRow(*values))
            else:
                self.pending = None
        elif command == FISH_ROW:
            if values[0] and len(pending.fish_rows) < MAX_ROWS:
                pending.fish_rows.append(FishRow(*values))
            else:
                self.pending = None
        elif command == MINE_ROW:
            if (values[0] or values[1]) and len(pending.mine_rows) < MAX_ROWS:
                pending.mine_rows.append(MineRow(*values))
            else:
                self.pending = None
        return False

    def Line(self, line):
        """A whole command line ("CraftFishRowV1 27803 12 4820")."""
        tokens = (line or '').split()
        if not tokens:
            return False
        return self.Feed(tokens[0], tokens[1:])


# --------------------------------------------------------------------------- derived values and formatting
def Ratio(part, whole):
    """part / whole in 0..1 (0 without a whole)."""
    if not whole or whole <= 0:
        return 0.0
    return max(0.0, min(1.0, float(part) / float(whole)))


def FormatNumber(value):
    """12480 -> "12 480" (groups of three digits split by a space)."""
    value = int(value or 0)
    sign = '-' if value < 0 else ''
    digits = str(abs(value))
    groups = []
    while len(digits) > 3:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    groups.insert(0, digits)
    return sign + ' '.join(groups)


def FormatPercent(ratio):
    """0.447 -> "44,7 %" (one decimal, a decimal comma)."""
    tenths = int(round(max(0.0, min(1.0, float(ratio or 0.0))) * 1000))
    return '%d,%d %%' % (tenths // 10, tenths % 10)


def FormatDuration(seconds):
    """Whole minutes: "41 h 12 min", "3 h", "5 min"; under a minute in seconds ("45 s"), nothing yet "0 min"."""
    seconds = max(0, int(seconds or 0))
    if 0 < seconds < 60:
        return '%d s' % seconds
    minutes = seconds // 60
    hours, minutes = divmod(minutes, 60)
    if not hours:
        return '%d min' % minutes
    if not minutes:
        return '%s h' % FormatNumber(hours)
    return '%s h %d min' % (FormatNumber(hours), minutes)


def FormatLength(value):
    """Item socket 0 (cm * 100): 4820 -> "48,2 cm", 12100 -> "1,21 m", 0 -> "-"."""
    value = max(0, int(value or 0))
    if not value:
        return '-'
    tenths = (value + 5) // 10
    if value >= 10000 or tenths >= 1000:
        hundredths = (value + 50) // 100
        return '%s,%02d m' % (FormatNumber(hundredths // 100), hundredths % 100)
    return '%d,%d cm' % (tenths // 10, tenths % 10)


# --------------------------------------------------------------------------- the book (round 6): collection, chapters
class AtlasEntry(object):
    def __init__(self, counter, vnum, have, need):
        self.counter, self.vnum, self.have, self.need = counter, vnum, have, need
        self.identity = (counter, vnum)


class AtlasChapter(object):
    def __init__(self, key, ordinal, size):
        self.key, self.ordinal, self.size = key, ordinal, size
        self.entries = []


def Numeral(number):
    out = ''
    for value, letters in ((1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'),
                           (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')):
        while number >= value:
            out += letters
            number -= value
    return out


def Chapters(mastery, craft):
    owner = mastery.Craft(craft) if mastery and mastery.enabled else None
    return [(Numeral(c.ordinal), c.key, c.entries) for c in owner.chapters] if owner and owner.enabled else []


def FishCollection(snapshot):
    """{vnum: (count, best_length)} of the caught species."""
    out = {}
    for row in (snapshot.fish_rows if snapshot else ()):
        if row.count > 0:
            count, best = out.get(row.vnum, (0, 0))
            out[row.vnum] = (count + row.count, max(best, row.best_length))
    return out


def Got(entries):
    return sum(e.have >= e.need for e in entries)


def LeastCaughtFish(snapshot):
    rows = [row for row in (snapshot.fish_rows if snapshot else ()) if row.count > 0]
    return min(rows, key=lambda row: (row.count, row.vnum)) if rows else None


def Share(part, whole):
    """A whole percent of part in whole: "4 %" (under 1 but more than 0: "<1 %")."""
    if not whole or part <= 0:
        return '0 %'
    value = 100.0 * part / whole
    return '<1 %' if value < 1 else '%d %%' % int(round(value))


def Goals(chapters, current_streak=None, best_streak=None, limit=3):
    """Unfinished species and total remaining pieces, never a count of unseen icons."""
    goals = []
    for numeral, unused, entries in chapters:
        missing = [e for e in entries if e.have < e.need]
        if missing:
            goals.append(('GOAL_CHAPTER', (numeral, len(missing), sum(e.need - e.have for e in missing))))
    if current_streak is not None:
        streak = ('GOAL_STREAK', (max(1, best_streak - current_streak + 1),)) if best_streak else \
                 ('GOAL_STREAK_FIRST', (5,))
        goals.insert(min(1, len(goals)), streak)
    return goals[:limit]


def LoadBookModes(lines):
    """Generated item variant maps and wood item -> is_rare modes, loaded once."""
    out = {}
    for line in lines:
        fields = line.strip().split('\t')
        if len(fields) == 3 and fields[0] in ('fishing', 'mining'):
            if fields[1].isdigit() and fields[2].isdigit():
                rare, ordinary = int(fields[1]), int(fields[2])
                if rare and ordinary and rare != ordinary:
                    out.setdefault(fields[0], {})[ordinary] = rare
        elif len(fields) == 3 and fields[0] == 'wood' and fields[1].isdigit() and fields[2].isdigit():
            # glowing wood (owner 21. 10. 2026): "wood <glowing item> <wood item>", a variant like a glowing fish
            rare, ordinary = int(fields[1]), int(fields[2])
            if rare and ordinary and rare != ordinary:
                out.setdefault('wood', {})[ordinary] = rare
        elif len(fields) == 3 and fields[0] == 'wood' and fields[1].isdigit() and fields[2] in ('normal', 'rare'):
            # an older export without glowing wood: tiers split into normal | rare
            if int(fields[1]):
                out.setdefault('wood_kind', {})[int(fields[1])] = fields[2] == 'rare'
    return out


def WoodModeRows(entries, kinds, rare=False):
    """Filter server chapter entries by wood item; absent modes keep the whole chapter."""
    return [(entry.identity, entry.vnum) for entry in entries
            if not kinds or bool(kinds.get(entry.vnum, False)) == bool(rare)]


def WoodModeSwitchRows(entries, kinds):
    """Rare rows when the chapter holds both ordinary and rare wood, else [] (no switch).

    A2: chapter I has only ordinary and chapter II only rare wood, so neither shows the switch
    and each lists its whole chapter."""
    rare = WoodModeRows(entries, kinds, True) if kinds else []
    return rare if rare and WoodModeRows(entries, kinds, False) else []


def BookModeRows(entries, variants, rare=False, ores=None):
    """(counter/vnum identity, displayed item); pure entries already are item vnums."""
    rows = []
    for entry in entries:
        ordinary = (ores or {}).get(entry.vnum, 0) if entry.counter == 'vein' else entry.vnum
        shown = variants.get(ordinary, 0) if rare else ordinary
        if not rare or shown:
            rows.append((entry.identity, shown))
    return rows


def BookModeCollection(snapshot, rows, entries, rare=False):
    """Chapter progress is authoritative; optional variant browsing uses exact stats counters."""
    if not rare:
        best = FishCollection(snapshot)
        return {e.identity: (e.have, best.get(e.vnum, (0, 0))[1] if e.counter == 'fish' else 0)
                for e in entries if e.have > 0}
    fish = FishCollection(snapshot)
    pure = {}
    for row in snapshot.mine_rows if snapshot else ():
        if row.vein_vnum == 0 and row.amount > 0:
            pure[row.ore_vnum] = (pure.get(row.ore_vnum, (0, 0))[0] + row.amount, 0)
    wood = {}
    for row in snapshot.wood_rows if snapshot else ():
        if row.pieces > 0:
            wood[row.wood_vnum] = (wood.get(row.wood_vnum, (0, 0))[0] + row.pieces, 0)
    source = lambda identity: fish if identity[0] == 'fish' else (wood if identity[0] == 'wood' else pure)
    return {identity: source(identity)[item] for identity, item in rows if item in source(identity)}
