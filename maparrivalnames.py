"""Resolve map-arrival titles from the existing player and locale catalogues."""

import app
import gmmapcatalog
import localeInfo
import teleportmapdata


# root/atlasinfo.txt calls runtime map 64 map_a2; the GM/server catalogue uses
# map_n_threeway. These are identifiers for the same map, not separate titles.
_INTERNAL_NAME_ALIASES = {
    "map_a2": "map_n_threeway",
    # Three server instances share the atlas's single Colony map identity.
    "metin2_map_e1_01": "metin2_map_e1",
    "metin2_map_e1_02": "metin2_map_e1",
    "metin2_map_e1_03": "metin2_map_e1",
    # Published clients still host these atlas identities. An alias alone does
    # not expose a retired map: its active catalogue entry is still required.
    "metin2_map_monkeydungeon": "metin2_map_monkey_dungeon",
    "metin2_map_monkeydungeon_02": "metin2_map_monkey_dungeon2",
    "metin2_map_monkeydungeon_03": "metin2_map_monkey_dungeon3",
}

# Match system.__DecodePackText__: source scripts are UTF-8, historical locale
# bytes use their locale's Windows codepage before the native default codepage.
# Do not import system here: importing the bootstrap can reinstall its hooks.
_LOCALE_ENCODINGS = {
    "ymir": "cp949", "kr": "cp949", "we_korea": "cp949",
    "ru": "cp1251",
    "cz": "cp1250", "pl": "cp1250", "hu": "cp1250", "ro": "cp1250",
    "gr": "cp1253", "tr": "cp1254", "ae": "cp1256",
    "en": "cp1252", "de": "cp1252", "es": "cp1252", "fr": "cp1252",
    "it": "cp1252", "pt": "cp1252",
}


def _text(value):
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, (bytes, bytearray)):
        return ""

    locale_name = app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower()
    encodings = ["utf-8-sig", _LOCALE_ENCODINGS.get(locale_name)]
    try:
        encodings.append("cp%d" % app.GetDefaultCodePage())
    except (AttributeError, TypeError, ValueError):
        pass
    encodings.extend(("cp949", "cp1252", "latin-1"))
    for encoding in encodings:
        if not encoding:
            continue
        try:
            return value.decode(encoding).strip()
        except (LookupError, UnicodeDecodeError):
            pass
    return ""


def _map_key(map_name):
    # Real atlas paths include season1/ and season2/. Basename normalization
    # handles those and Windows paths without inventing seasonal map aliases.
    name = _text(map_name).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()
    return _INTERNAL_NAME_ALIASES.get(name, name)


def resolve(map_name):
    """Return the catalogue's Unicode title, or empty text for an unknown map.

    Read the catalogues on demand so new destinations/localized entries need no
    second title table or resolver update. Never prettify an internal filename.
    """
    key = _map_key(map_name)
    if not key:
        return ""

    map_index = next((
        index for index, internal_name in gmmapcatalog.RUNTIME_MAPS
        if _map_key(internal_name) == key
    ), None)

    if map_index is not None:
        for destination in teleportmapdata.DESTINATIONS:
            if destination.get("map_index") == map_index:
                title = _text(destination.get("name"))
                if title:
                    return title

    for internal_name, title in getattr(localeInfo, "MINIMAP_ZONE_NAME_DICT", {}).items():
        if _map_key(internal_name) == key:
            title = _text(title)
            if title:
                return title

    if map_index is not None:
        by_index = getattr(localeInfo, "MINIMAP_ZONE_NAME_DICT_BY_IDX", {})
        return _text(by_index.get(map_index))
    return ""
