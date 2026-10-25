# -*- coding: utf-8 -*-
"""What the client itself knows about a teleport destination: its bosses, metin stones and world bosses (presentation
only, the atlas catalog stays the warp authority).

Nothing is typed in by hand. The mobs of a map come from servergamedata.MOB_MAPS (generated from the server regen
files by tools/build_server_game_data.py; WORLD_BOSS_SPAWNS adds the map of a world boss), their kind from the native
wiki categories (locale/common/wiki_mob_categories.txt: low_boss = poloboss, high_boss = boss, stone = metin), their
name and level from the binary mob_proto (nonplayer.GetMonsterName / GetMonsterLevel) and their drop from the
connected server (Drops: the wiki catalogue of the session, else what the server sent for a targeted mob; never a
table packed with the client). A respawn is shown only for a boss the boss tracker catalogue
(servergamedata.BOSS_TRACK) lists on that map. What the client does not have (spawn counts, the level range of the
ordinary mobs, respawn of the other bosses, the world boss window) is left out, never guessed.
"""
import servergamedata

CATEGORIES_FILE = 'locale/common/wiki_mob_categories.txt'
KIND_LABELS = {
    'low_boss': u'poloboss',
    'high_boss': u'boss',
    'stone': u'meteor',
    'world_boss': u'světový boss',
}
BOSS_CATEGORIES = ('low_boss', 'high_boss')
DROP_SHOWN = 6                        # item slots in a tooltip, the rest is "+ N dalších ve Wiki"

_categories = None
_maps = {}


def Reset():
    """Forgets the cached categories and maps (tests; a locale reload)."""
    global _categories
    _categories = None
    _maps.clear()


def _ReadLines():
    """Lines of the category file; the client's open() reads a packed file (system.pack_file)."""
    stream = open(CATEGORIES_FILE, 'r')
    try:
        return stream.readlines()
    finally:
        stream.close()


def LoadCategories():
    """{mob vnum: category} of the native wiki; an unreadable file gives {} (the panel then shows nothing)."""
    global _categories
    if _categories is not None:
        return _categories
    result = {}
    try:
        lines = _ReadLines()
    except Exception:
        return result                          # not cached: the next call may find the pack
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        fields = line.split()
        if len(fields) != 2:
            continue
        try:
            result[int(fields[1])] = fields[0]
        except ValueError:
            continue
    _categories = result
    return result


class Mob(object):
    """One boss / metin / world boss row: vnum, name, level, category (the wiki's), respawn seconds or None, world
    boss channels (first, last) or None."""

    def __init__(self, vnum, name, level, category, respawn=None, channels=None):
        self.vnum = vnum
        self.name = name
        self.level = level
        self.category = category
        self.respawn = respawn
        self.channels = channels

    def Kind(self):
        return KIND_LABELS.get(self.category, u'')

    def IsWorld(self):
        return self.category == 'world_boss'


class Info(object):
    """The rows of one destination: ``bosses`` (bosses, then world bosses) and ``metins``."""

    def __init__(self, bosses=(), metins=()):
        self.bosses = list(bosses)
        self.metins = list(metins)

    def Empty(self):
        return not (self.bosses or self.metins)


def _TrackedRespawn(vnum, map_index):
    for row in servergamedata.BOSS_TRACK.values():
        if row[0] == vnum and row[1] == map_index and row[5]:
            return int(row[5])
    return None


def _Entry(vnum, category, map_index, channels=None):
    import nonplayer
    name = nonplayer.GetMonsterName(vnum)
    if not name:
        return None
    respawn = _TrackedRespawn(vnum, map_index) if category in BOSS_CATEGORIES else None
    return Mob(vnum, name, int(nonplayer.GetMonsterLevel(vnum)), category, respawn, channels)


def _Merged(rows):
    """Same name and kind = one row (the server has two vnums for Quag Primus): the first vnum stays."""
    seen = set()
    result = []
    for row in rows:
        key = (row.name, row.category)
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def _Trace(what):
    """Traces a failure of the map info to syserr; the list itself goes on without it."""
    try:
        import dbg
        import traceback
        dbg.TraceError('Teleportace: %s failed, the map info is left out.' % what)
        for line in traceback.format_exc().splitlines():
            dbg.TraceError(line)
    except Exception:
        pass


def ForMap(map_index):
    """Info of the destination whose server map index is ``map_index`` (cached; never raises, an empty Info when the
    categories are unavailable or the data fail)."""
    if map_index in _maps:
        return _maps[map_index]
    try:
        categories = LoadCategories()
        if not categories:
            return Info()                      # the pack may not be readable yet: not cached
        info = _Build(map_index, categories)
    except Exception:
        _Trace('informace o mape %s' % map_index)
        return Info()
    _maps[map_index] = info
    return info


def _Build(map_index, categories):
    bosses, metins, world = [], [], []
    for vnum, maps in servergamedata.MOB_MAPS.items():
        if map_index not in maps:
            continue
        category = categories.get(vnum)
        if category in BOSS_CATEGORIES or category == 'stone':
            row = _Entry(vnum, category, map_index)
            if row is not None:
                (metins if category == 'stone' else bosses).append(row)
    for vnum, spawn in getattr(servergamedata, 'WORLD_BOSS_SPAWNS', {}).items():
        if spawn[0] == map_index:
            row = _Entry(vnum, 'world_boss', map_index, (spawn[1], spawn[2]))
            if row is not None:
                world.append(row)
    key = lambda row: (row.level, row.vnum)
    return Info(_Merged(sorted(bosses, key=key)) + _Merged(sorted(world, key=key)), _Merged(sorted(metins, key=key)))


# --------------------------------------------------------------------------- texts
def Plural(count, one, few, many):
    """Czech plural: 1 boss, 2-4 bossové, 5 bossů."""
    if count == 1:
        return one
    return few if 2 <= count <= 4 else many


def Summary(info):
    """"1 boss · 3 metiny" (nothing for an empty kind, "" for no data)."""
    parts = []
    if info.bosses:
        count = len(info.bosses)
        parts.append(u'%d %s' % (count, Plural(count, u'boss', u'bossové', u'bossů')))
    if info.metins:
        count = len(info.metins)
        parts.append(u'%d %s' % (count, Plural(count, u'meteor', u'meteory', u'meteorů')))
    return u' · '.join(parts)


def DurationText(seconds):
    """600 -> "10 min", 45 -> "45 s", 3600 -> "1 h", 90 -> "~2 min"."""
    seconds = int(seconds)
    if seconds >= 3600 and seconds % 3600 == 0:
        return u'%d h' % (seconds // 3600)
    if seconds < 120 and seconds % 60:
        return u'%d s' % seconds
    if seconds % 60 == 0:
        return u'%d min' % (seconds // 60)
    return u'~%d min' % int(round(seconds / 60.0))


def Facts(row):
    """Lines of a tooltip under the name: level and kind, then what the data says about the respawn / channels."""
    lines = [u'Lv %d · %s' % (row.level, row.Kind())]
    if row.respawn:
        lines.append(u'Respawn: %s' % DurationText(row.respawn))
    if row.channels:
        first, last = row.channels
        lines.append(u'Kanály: CH%d' % first if first == last else u'Kanály: CH%d–%d' % (first, last))
        lines.append(u'Místo výskytu je tajné')
    return lines


def Drops(vnum, map_index=None):
    """[(item vnum, count)] the drop of the mob on that map, an item once ([] = none / unknown).

    The connected server is the only source. First the wiki catalogue of this session (wikicatalog.MobDrops: the rows
    the server built from its live drop tables for exactly the teleport destinations). While it has not arrived, or
    does not list the mob on the map, nonplayer.GetMonsterItemDrop, which the server fills for a mob the player has
    targeted in this session. Otherwise nothing: the tooltip has no "Drop" block. Never the table packed with the
    client, which a live change on the server leaves behind."""
    if map_index is not None:
        try:
            import wikicatalog
            listed = wikicatalog.MobDrops(map_index, vnum)
        except Exception:
            listed = None
        if listed is not None:
            return listed
    result = []
    try:
        import nonplayer
        pages, rows = nonplayer.GetMonsterItemDrop(vnum)
    except Exception:
        return []
    seen = set()
    for row in rows:
        item_vnum, count = row[2], row[3]
        if item_vnum in seen:
            continue
        seen.add(item_vnum)
        result.append((item_vnum, count))
    return result


def DropsStamp():
    """Changes when Drops may answer differently for an untargeted mob (a new wiki catalogue, or none)."""
    try:
        import wikicatalog
        return wikicatalog.DropsStamp()
    except Exception:
        return 0


def WikiLink(vnum):
    """The hyperlink of the wiki page of a mob (interfacemodule.MakeHyperlinkTooltip)."""
    return 'wiki:NEW#%d#1' % int(vnum)
