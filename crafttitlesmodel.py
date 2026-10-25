# -*- coding: utf-8 -*-
"""Model of the own craft titles and tool skins (the "Tituly a vzhled" page of the craft book, owner TIT-KNIHA = B).

Pure Python (no engine module), so it can be tested on its own. The server (catalog share/conf/craft_titles_v1.json) answers "/craft_mastery titles" with CHAT_TYPE_COMMAND lines, one snapshot
at a time:

    CraftTitlesBeginV1 <version=1> <enabled 0|1>
    CraftTitleV1 <id> <level> <book_fishing> <book_mining> <book_woodcut>      catalog order, lowest title first
    CraftTitleSkinV1 <id> <craft> <need level|apex> <need_level> <unlocked 0|1> <chosen 0|1>
    CraftTitlesBookV1 <count_fishing> <count_mining> <count_woodcut>           the book counters of the catalog's
                                                                              book_flags (catches, successful runs,
                                                                              cuts)
    CraftTitlesEndV1 <current title id|->

<craft> fishing / mining / woodcut (craftmasterymodel.CRAFT_KEYS); <need_level> is 0 for an apex skin. The current
title is the server's (the best craft: level and book of the same craft, TitleOf); the client keeps no threshold,
title or skin of its own. A snapshot replaces the shown one only on CraftTitlesEndV1 with the book line seen; a
malformed line drops the pending snapshot. Choosing a skin sends "/craft_mastery skin <craft> <id|0>" (0 = none).
"""

VERSION = 1
REQUEST = '/craft_mastery titles'
SKIN = '/craft_mastery skin %s %s'
NO_SKIN = '0'
CRAFT_KEYS = ('fishing', 'mining', 'woodcut')
NEEDS = ('level', 'apex')
NO_TITLE = '-'
MAX_TITLES = 16
MAX_SKINS = 32

BEGIN = 'CraftTitlesBeginV1'
TITLE = 'CraftTitleV1'
SKIN_LINE = 'CraftTitleSkinV1'
BOOK = 'CraftTitlesBookV1'
END = 'CraftTitlesEndV1'
COMMANDS = (BEGIN, TITLE, SKIN_LINE, BOOK, END)
PREFIX = 'CraftTitle'           # every line of this answer starts with it (the game.py dispatch)
MAX_VALUE = 2 ** 63 - 1

WORN, EARNED, NEXT, LOCKED = 'worn', 'earned', 'next', 'locked'


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


class Title(object):
    def __init__(self, title_id, level, book):
        self.id = title_id
        self.level = level
        self.book = tuple(book)         # the book count per craft index

    def Book(self, craft):
        return self.book[craft] if 0 <= craft < len(self.book) else 0


class Skin(object):
    def __init__(self, skin_id, craft, need, need_level, unlocked, chosen):
        self.id = skin_id
        self.craft = craft              # craft index
        self.need = need                # 'level' or 'apex'
        self.need_level = need_level
        self.unlocked = unlocked
        self.chosen = chosen


class Snapshot(object):
    def __init__(self, enabled):
        self.enabled = enabled
        self.titles = []
        self.skins = []
        self.book = None                # (fishing, mining, woodcut) counters
        self.current = -1               # index of the current title, -1 = none yet

    def Title(self, title_id):
        for index, title in enumerate(self.titles):
            if title.id == title_id:
                return index
        return -1

    def Current(self):
        return self.titles[self.current] if 0 <= self.current < len(self.titles) else None

    def Next(self):
        """The title after the current one (None at the top)."""
        index = self.current + 1
        return self.titles[index] if index < len(self.titles) else None

    def Target(self):
        """The title the progress is measured against: the next one, at the top the top one."""
        return self.Next() or (self.titles[-1] if self.titles else None)

    def State(self, index):
        if index == self.current:
            return WORN
        if index < self.current:
            return EARNED
        return NEXT if index == self.current + 1 else LOCKED

    def BookCount(self, craft):
        return self.book[craft] if self.book and 0 <= craft < len(self.book) else 0

    def Skins(self, craft):
        return [skin for skin in self.skins if skin.craft == craft]

    def Chosen(self, craft):
        """The id of the chosen skin of a craft, None = no look."""
        for skin in self.Skins(craft):
            if skin.chosen:
                return skin.id
        return None


class CraftTitlesModel(object):
    """Collects the server lines; ``snapshot`` is the last complete one (None before the first)."""

    def __init__(self):
        self.snapshot = None
        self.pending = None
        self.revision = 0

    def Feed(self, command, args=()):
        """One server line. True when it completed a snapshot."""
        args = tuple(args or ())
        if command == BEGIN:
            values = _ints(args)
            ok = values is not None and len(values) == 2 and values[0] == VERSION and values[1] in (0, 1)
            self.pending = Snapshot(bool(values[1])) if ok else None
            return False
        pending = self.pending
        if pending is None or command not in COMMANDS:
            return False
        if command == TITLE:
            values = _ints(args[1:])
            if len(args) != 2 + len(CRAFT_KEYS) or not _ident(args[0]) or values is None or \
                    pending.Title(args[0]) >= 0 or len(pending.titles) >= MAX_TITLES:
                return self.Drop()
            pending.titles.append(Title(args[0], values[0], values[1:]))
            return False
        if command == SKIN_LINE:
            values = _ints(args[3:])
            if len(args) != 6 or not _ident(args[0]) or args[1] not in CRAFT_KEYS or args[2] not in NEEDS or \
                    values is None or values[1] not in (0, 1) or values[2] not in (0, 1) or \
                    len(pending.skins) >= MAX_SKINS or any(skin.id == args[0] for skin in pending.skins):
                return self.Drop()
            craft = CRAFT_KEYS.index(args[1])
            need_level, unlocked, chosen = values
            if (chosen and (not unlocked or pending.Chosen(craft) is not None)) or \
                    (args[2] == 'level') != (need_level > 0):
                return self.Drop()
            pending.skins.append(Skin(args[0], craft, args[2], need_level, bool(unlocked), bool(chosen)))
            return False
        if command == BOOK:
            values = _ints(args)
            if values is None or len(values) != len(CRAFT_KEYS) or pending.book is not None:
                return self.Drop()
            pending.book = tuple(values)
            return False
        # END
        self.pending = None
        if len(args) != 1 or pending.book is None:
            return False
        if args[0] != NO_TITLE:
            pending.current = pending.Title(args[0])
            if pending.current < 0:
                return False
        self.snapshot = pending
        self.revision += 1
        return True

    def Drop(self):
        self.pending = None
        return False

    def Line(self, line):
        tokens = (line or '').split()
        return self.Feed(tokens[0], tokens[1:]) if tokens else False

    def Choose(self, craft, skin_id):
        """The command that chooses a skin of a craft (None = no look); the shown snapshot takes the choice at once
        (the server answers with a new snapshot). None when the skin is not unlocked or nothing changes."""
        snapshot = self.snapshot
        if snapshot is None or not 0 <= craft < len(CRAFT_KEYS):
            return None
        skins = snapshot.Skins(craft)
        if skin_id is not None and not any(skin.id == skin_id and skin.unlocked for skin in skins):
            return None
        if snapshot.Chosen(craft) == skin_id:
            return None
        for skin in skins:
            skin.chosen = skin.id == skin_id
        self.revision += 1
        return SkinCommand(craft, skin_id)


def SkinCommand(craft, skin_id):
    """The chat command that chooses a skin of a craft (None = no look)."""
    return SKIN % (CRAFT_KEYS[craft], skin_id or NO_SKIN)
