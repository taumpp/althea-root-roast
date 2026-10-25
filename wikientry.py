"""Shared catalogue scope and native localization; no login-time work."""
import item
import localeInfo
import wikicatalog as M
from wikilocale import Text as L


def TabScope():
    import teleportmapdata
    import uidungeontrack
    return M.tab_scope(teleportmapdata.DESTINATIONS, uidungeontrack.dungeonData)


def ItemName(vnum):
    if item.SelectItemWiki(int(vnum)):
        return item.GetItemName()
    return L('unknown_item')+' '+str(vnum)


def LocalizeCatalog(catalog):
    import nonplayer
    import teleportmapdata
    import uidungeontrack
    teleport_names = {M.number(row['map_index']): row.get('name')
                      for row in teleportmapdata.DESTINATIONS}
    map_names = getattr(localeInfo, 'MINIMAP_ZONE_NAME_DICT_BY_IDX', {})
    dungeon_names = getattr(localeInfo, 'DUNGEON_DISPLAY_NAMES', {})
    for map_index, location in catalog.maps.items():
        boss = M.number(location.get('boss'))
        location['name'] = (teleport_names.get(map_index)
                            or uidungeontrack.dungeonData.get(boss, {}).get('name')
                            or dungeon_names.get(boss) or map_names.get(map_index)
                            or location.get('name') or nonplayer.GetMonsterName(boss))
