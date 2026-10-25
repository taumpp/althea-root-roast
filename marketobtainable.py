# -*- coding: utf-8 -*-
"""The market's search suggestions and category rail offer only items a player can get.

locale/common/market_obtainable.txt lists them: the tradeable items that drop on the active maps and in the dungeons,
come from chests, the cube, refining, NPC shops, quests, crafts, or the item shop. Each data line is
"<vnum>\\t<Z|IS>" (Z = in the game, IS = item shop only). Without the file (an older pack) nothing is filtered.
No engine dependencies, so ci/tests can load it."""

PATH = "locale/common/market_obtainable.txt"
SUGGESTION_LIMIT = 64

_allowed = None
_loaded = False


def Parse(lines):
    """The vnums of the file's data lines; '#' starts a comment. An unreadable line is skipped."""
    allowed = set()
    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("utf-8", "replace")
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        head = text.split("\t", 1)[0].strip()
        if head.isdigit():
            allowed.add(int(head))
    return frozenset(allowed)


def Allowed():
    """The whitelist (frozenset of vnums), or None when the pack has no list: then the market filters nothing."""
    global _allowed, _loaded
    if not _loaded:
        _loaded = True
        try:
            lines = open(PATH, "r").readlines()
        except (IOError, OSError):
            lines = None
        if lines:
            allowed = Parse(lines)
            _allowed = allowed if allowed else None
    return _allowed


def FilterCatalog(catalog, pairs):
    """The market filter catalog rows (kind, subtype, ...) whose (kind, subtype) has an obtainable item. pairs None =
    no whitelist: the catalog stays whole."""
    if pairs is None:
        return list(catalog)
    return [row for row in catalog if (row[0], row[1]) in pairs]


def MatchNames(entries, query, fold, limit=SUGGESTION_LIMIT):
    """The suggestion names for a typed text like the engine's item.GetItemNamesByName: entries are (folded name,
    name) of the obtainable items, a name containing the folded query matches; names starting with it first, then by
    the folded name; one row per folded name; at most `limit`."""
    needle = fold(query)
    if not needle:
        return []
    matches = []
    for folded, name in entries:
        position = folded.find(needle)
        if position >= 0:
            matches.append((position != 0, folded, name))
    matches.sort()
    result, previous = [], None
    for unused, folded, name in matches:
        if folded == previous:
            continue
        previous = folded
        result.append(name)
        if len(result) >= limit:
            break
    return result
