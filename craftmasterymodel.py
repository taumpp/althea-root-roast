# -*- coding: utf-8 -*-
"""Model of the craft mastery tree (strom mistrovství): craft levels, points and node ranks of the character.

Pure Python (no engine module), so it can be tested on its own. The server (docs/CRAFT_MASTERY.md) answers "/craft_mastery state" with CHAT_TYPE_COMMAND lines, one snapshot at a time:

    CraftMasteryBeginV1 <version=1> <enabled 0|1>
    CraftMasteryCraftV1 <craft> <enabled> <level> <max_level> <exp_into> <exp_next> <points_total> <points_spent>
                        <atlas_done> <atlas_chapters> <atlas_points_max> <apex_threshold> <reset_yang>
    CraftMasteryNodeV1 <craft> <id> <column> <row> <active> <rank> <max_rank> <min_level> <next_cost> <can_buy>
                       <effect> [<value>=<r1>/<r2>...]...
    CraftMasteryCostV1 <craft> <id> <vnum> <count> [...]   items the next rank takes (bones, shells)
    CraftMasteryEndV1

and after a level-up, outside a snapshot:

    CraftMasteryLevelV1 <craft> <level> <free_points>

and after every gathering result that gave EXP (15. 10.: the book's level bar moved only with a new snapshot):

    CraftMasteryExpV1 <craft> <level> <exp_into> <exp_next>

which updates the shown snapshot in place (one short line per result, never a whole snapshot).

<craft> 0 fishing, 1 mining, 2 woodcut; <column> 0 hand (Ruka), 1 eye (Oko), 2 endurance (Vytrvalost), 3 apex;
<can_buy> ok / disabled / unknown / inactive / max / level / prerequisite / apex / points. Every number comes from
the server catalog; the client keeps no copy of costs or effect values. A snapshot replaces the shown one only on
CraftMasteryEndV1; a malformed line drops the pending snapshot. Buying sends "/craft_mastery buy <craft> <id>".

The craft book shows it on its Strom page and the levels on its craft switch (root/uicraftbook.py).
"""

import craftbookmodel as Book

VERSION = 1
REQUEST = '/craft_mastery state'
BUY = '/craft_mastery buy %s %s'
CRAFT_KEYS = ('fishing', 'mining', 'woodcut')
COLUMN_KEYS = ('hand', 'eye', 'endurance', 'apex')
BUY_RESULTS = ('ok', 'disabled', 'unknown', 'inactive', 'max', 'level', 'prerequisite', 'apex', 'points', 'items')
MAX_NODES = 64

BEGIN = 'CraftMasteryBeginV1'
CRAFT = 'CraftMasteryCraftV1'
NODE = 'CraftMasteryNodeV1'
END = 'CraftMasteryEndV1'
LEVEL = 'CraftMasteryLevelV1'
COST = 'CraftMasteryCostV1'
EXP = 'CraftMasteryExpV1'
CHAPTER = 'CraftMasteryChapterV1'
ENTRY = 'CraftMasteryEntryV1'
COMMANDS = (BEGIN, CRAFT, NODE, END, LEVEL, COST, EXP, CHAPTER, ENTRY)
CRAFT_FIELDS = ('craft', 'enabled', 'level', 'max_level', 'exp_into', 'exp_next', 'points_total', 'points_spent',
                'atlas_done', 'atlas_chapters', 'atlas_points_max', 'apex_threshold', 'reset_yang')
MAX_VALUE = 2 ** 63 - 1


def _int(token):
    try:
        value = int(token)
    except (TypeError, ValueError):
        return None
    if value < 0 or value > MAX_VALUE or str(value) != token:
        return None
    return value


def _ints(tokens):
    values = [_int(t) for t in tokens]
    return None if None in values else values


def _ident(token):
    return bool(token) and len(token) <= 40 and all(c.isalnum() or c == '_' for c in token)


class Craft(object):
    def __init__(self, values):
        for name, value in zip(CRAFT_FIELDS, values):
            setattr(self, name, value)
        self.nodes = []
        self.chapters = []
        self.has_chapters = False

    def Free(self):
        return max(0, self.points_total - self.points_spent)

    def Node(self, node_id):
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def Column(self, column):
        """The nodes of one column, top row first."""
        return sorted([n for n in self.nodes if n.column == column], key=lambda n: n.row)


class Node(object):
    def __init__(self, node_id, column, row, active, rank, max_rank, min_level, next_cost, can_buy, effect, values):
        self.id = node_id
        self.column = column
        self.row = row
        self.active = active
        self.rank = rank
        self.max_rank = max_rank
        self.min_level = min_level
        self.next_cost = next_cost
        self.can_buy = can_buy
        self.effect = effect
        self.values = values        # {name: [rank 1, rank 2, ...]}
        self.items = []             # [(vnum, count)] the next rank takes besides points (CraftMasteryCostV1)

    def Value(self, name, rank=None):
        """The named effect value at `rank` (default: the current rank; 0 for rank 0 or an unknown name)."""
        ranks = self.values.get(name) or []
        rank = self.rank if rank is None else rank
        return ranks[rank - 1] if 0 < rank <= len(ranks) else 0


class Snapshot(object):
    def __init__(self, enabled):
        self.enabled = enabled
        self.crafts = {}            # craft index -> Craft

    def Craft(self, craft):
        return self.crafts.get(craft)


def _parse_values(tokens, max_rank):
    values = {}
    for token in tokens:
        name, sep, text = token.partition('=')
        if not sep or not _ident(name) or name in values:
            return None
        ranks = _ints(text.split('/'))
        if ranks is None or len(ranks) != max_rank:
            return None
        values[name] = ranks
    return values


class CraftMasteryModel(object):
    """Collects the server lines; ``snapshot`` is the last complete one (None before the first)."""

    def __init__(self):
        self.snapshot = None
        self.pending = None
        self.revision = 0
        self.level_ups = []         # (craft, level, free points) since the last TakeLevelUps()

    def Feed(self, command, args=()):
        """One server line. True when it completed a snapshot."""
        args = tuple(args or ())
        if command == LEVEL:
            values = _ints(args)
            if values is not None and len(values) == 3 and values[0] < len(CRAFT_KEYS):
                self.level_ups.append(tuple(values))
            return False
        if command == EXP:
            return self._FeedExp(args)
        if command == BEGIN:
            values = _ints(args)
            ok = values is not None and len(values) == 2 and values[0] == VERSION and values[1] in (0, 1)
            self.pending = Snapshot(bool(values[1])) if ok else None
            return False
        pending = self.pending
        if pending is None or command not in COMMANDS:
            return False
        if command == END:
            self.pending = None
            if args or any(c.has_chapters and (len(c.chapters) != c.atlas_chapters or
                          any(len(ch.entries) != ch.size for ch in c.chapters)) for c in pending.crafts.values()):
                return False
            self.snapshot = pending
            self.revision += 1
            return True
        if command == CRAFT:
            values = _ints(args)
            if values is None or len(values) != len(CRAFT_FIELDS) or values[0] >= len(CRAFT_KEYS) or \
                    values[0] in pending.crafts:
                self.pending = None
                return False
            pending.crafts[values[0]] = Craft(values)
            return False
        if command in (CHAPTER, ENTRY):
            owner = pending.crafts.get(_int(args[0])) if args else None
            key = args[1] if len(args) > 1 else ''
            chapter = next((c for c in owner.chapters if c.key == key), None) if owner else None
            valid = owner is not None and _ident(key)
            if command == CHAPTER:
                values = _ints(args[2:])
                valid = valid and chapter is None and len(args) == 4 and values is not None
                valid = valid and 1 <= values[0] <= 64 and 1 <= values[1] <= Book.MAX_ROWS and len(owner.chapters) < 64
                valid = valid and not any(c.ordinal == values[0] for c in owner.chapters)
                if valid:
                    owner.has_chapters = True
                    owner.chapters.append(Book.AtlasChapter(key, *values))
            else:
                values = _ints(args[3:])
                valid = valid and chapter is not None and len(args) == 6 and values is not None
                valid = valid and args[2] in ('fish', 'vein', 'pure', 'wood') and values[0] > 0 and values[2] > 0
                valid = valid and len(chapter.entries) < chapter.size and not any(
                    e.identity == (args[2], values[0]) for e in chapter.entries)
                if valid:
                    chapter.entries.append(Book.AtlasEntry(args[2], *values))
            if not valid:
                self.pending = None
            return False
        if command == COST:
            values = _ints(args[2:])
            craft = _int(args[0]) if args else None
            owner = pending.crafts.get(craft) if craft is not None else None
            node = owner.Node(args[1]) if owner and len(args) > 1 else None
            if node is None or values is None or not values or len(values) % 2:
                self.pending = None
                return False
            node.items = [(values[k], values[k + 1]) for k in range(0, len(values), 2)]
            return False
        # NODE
        if len(args) < 11:
            self.pending = None
            return False
        numbers = _ints(args[2:9])
        craft = _int(args[0])
        owner = pending.crafts.get(craft) if craft is not None else None
        if numbers is None or owner is None or not _ident(args[1]) or args[9] not in BUY_RESULTS or \
                not _ident(args[10]) or len(owner.nodes) >= MAX_NODES or owner.Node(args[1]) is not None:
            self.pending = None
            return False
        column, row, active, rank, max_rank, min_level, next_cost = numbers
        values = _parse_values(args[11:], max_rank)
        if column >= len(COLUMN_KEYS) or active not in (0, 1) or rank > max_rank or values is None:
            self.pending = None
            return False
        owner.nodes.append(Node(args[1], column, row, bool(active), rank, max_rank, min_level, next_cost,
                                args[9], args[10], values))
        return False

    def _FeedExp(self, args):
        """CraftMasteryExpV1: the level and EXP of one craft of the shown snapshot. True when it changed them."""
        values = _ints(args)
        if values is None or len(values) != 4 or values[0] >= len(CRAFT_KEYS) or self.snapshot is None:
            return False
        craft = self.snapshot.Craft(values[0])
        level, exp_into, exp_next = values[1:]
        if craft is None or not 1 <= level <= craft.max_level or (exp_next and exp_into >= exp_next):
            return False
        if (craft.level, craft.exp_into, craft.exp_next) == (level, exp_into, exp_next):
            return False
        craft.level, craft.exp_into, craft.exp_next = level, exp_into, exp_next
        self.revision += 1
        return True

    def Line(self, line):
        tokens = (line or '').split()
        return self.Feed(tokens[0], tokens[1:]) if tokens else False

    def TakeLevelUps(self):
        out, self.level_ups = self.level_ups, []
        return out


def BuyCommand(craft, node_id):
    """The chat command that buys the next rank of a node."""
    return BUY % (CRAFT_KEYS[craft], node_id)
