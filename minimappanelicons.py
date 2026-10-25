"""The only function -> icon table of the configurable minimap panel.

Every icon is a state-complete 28x28 Crimson Ember medallion family:
``<stem>_normal.png``, ``<stem>_hover.png`` and ``<stem>_pressed.png``.
Change icons here only; the minimap, the settings preview and the settings
list all resolve them through ``Family``/``Visual``. A function without any
available medallion uses the empty placeholder carrier and the runtime draws a
native "?" over it.

Resolution order for one action ID:
0. ``R1_CHANNEL_IDS`` in the R1 look (not Settings -> "Starý vzhled"): the R1
   channel launchers (``tools/build_althea_r1_kanal.py``, ``althea_r1_kanal/``)
   when they are packed - "Změna kanálu" as two red arrows with the current
   channel's number as native text (``buttonpanelstatus.ChannelSwitch``),
   channel N as its number between two red arrows.
1. ``APPROVED`` - the ALTHEA-611 art shipped today. The default six keep it
   until the team approves the game set for them (``USE_GAME_SET_FOR_DEFAULTS``).
2. ``GAME_SET_IDS`` - the 2026-10-04 game icon set
   (``system_shortcuts/<action id with '.' -> '_'>_<state>.png``), used only
   when its files are packed, so the set can ship separately.
3. ``DERIVED`` - medallions built from the main taskbar buttons (character,
   inventory, community) and the minimap atlas control by
   ``tools/build_minimap_panel_extras.py``.
4. ``LEGACY`` - approved medallions kept from the earlier seven-launcher layout.
5. ``PLACEHOLDER``.

In the R1 look every family above (the R1 channel launchers included) is drawn from its R1 version
(``R1Family``: ``althea_r1_minimapa/medallion/...``, tools/build_althea_r1_minimapa.py: today's round
medallion with a graphite outer ring, a deep dark red inner ring and the same icon) when all its states are
packed; "Starý vzhled" and an unpacked R1 version keep the family itself.
"""

SHORTCUTS = 'd:/ymir work/ui/game/crimson_ember/system_shortcuts/'
R1_KANAL = 'd:/ymir work/ui/public/althea_r1_kanal/'
MINIMAP = 'd:/ymir work/ui/game/crimson_ember/minimap/'
PANEL = 'd:/ymir work/ui/game/crimson_ember/minimap_panel/'
R1_MINIMAPA = 'd:/ymir work/ui/public/althea_r1_minimapa/'
# R1 look: the arc between the launchers of the minimap and its Settings preview. 'none' (minimap A2, owner
# 8. 10. 2026: the buttons read better and still form the ring) or 'edge' (orbit/edge_ring<n>.png of
# tools/build_althea_r1_minimapa.py, concentric with the map under the outer edge of the launchers).
R1_ARC = 'none'
R1_FOLDERS = ((SHORTCUTS, 'medallion/shortcuts/'), (MINIMAP, 'medallion/minimap/'), (PANEL, 'medallion/panel/'))
STATES = ('normal', 'hover', 'pressed')
PLACEHOLDER = SHORTCUTS + 'placeholder'
PLACEHOLDER_MARK = '?'
# Owner 2026-10-04: the chosen game set replaces the old medallions everywhere
# (e.g. mount = 15c horse medallion); approved art stays the fallback when the
# game set is not packed.
USE_GAME_SET_FOR_DEFAULTS = True

APPROVED = {
    'system.battle_pass': SHORTCUTS + 'battle_pass',
    'system.custom_ports': SHORTCUTS + 'saved_positions',
    'information.skill_tree': SHORTCUTS + 'skill_tree',
    'information.ranking': SHORTCUTS + 'player_ranking',
    'information.event_calendar': SHORTCUTS + 'event_calendar',
    'system.pvp_matchmaking': SHORTCUTS + 'arena',
}

# tools/button_panel_icons/mapping.json (functions 1-47); every ID has all four
# files packed (ci/tests/test_button_panel_icon_set.py).
GAME_SET_IDS = frozenset((
    'system.battle_pass', 'system.custom_ports', 'information.skill_tree',
    'information.ranking', 'information.event_calendar', 'system.pvp_matchmaking',
    'information.dungeon', 'system.shop_search', 'system.biolog', 'system.teleport',
    'system.switchbot', 'inventory.special', 'inventory.dragon_soul', 'system.pet',
    'system.mount', 'system.talisman', 'system.mission_books', 'system.dew_craft',
    'system.quick_equip', 'system.item_shop', 'information.wiki', 'system.help',
    'system.options', 'information.boss_track', 'system.drop_tracker', 'system.reward',
    'system.support', 'system.exchange_log', 'system.destroyed_items', 'system.chat_log',
    'information.countdowns', 'system.quick_buffs',
    'system.channel_switch',  # mapping.json 33 (33w), channel_N: 34-42
    'channel.1', 'channel.2', 'channel.3', 'channel.4', 'channel.5', 'channel.6', 'channel.7',
    'channel.8', 'channel.9',
    'character.skills', 'character.quests', 'character.emotes', 'community.guild',  # 43a 44d 45c 46h
    'system.craft_book',  # 47 Řemeslná kniha (B3, 8. 10. 2026)
))

DERIVED = {
    'character.status': PANEL + 'taskbar_character',
    'inventory.normal': PANEL + 'taskbar_inventory',
    'community.messenger': PANEL + 'taskbar_community',
    'information.atlas': PANEL + 'atlas',
}

LEGACY = {
    'information.dungeon': MINIMAP + 'dungeon_info',
    'system.shop_search': MINIMAP + 'market_search',
    'system.biolog': MINIMAP + 'biolog',
}

# The R1 channel launchers (the same file names as the game set, in R1_KANAL).
R1_CHANNEL_IDS = frozenset(['system.channel_switch'] + ['channel.%d' % index for index in range(1, 10)])

# Optional file-existence hook (tests); the client uses app.IsExistFile.
FILE_EXISTS = None
_resolved = {}


def R1Look():
    """The R1 look is on (Settings -> "Starý vzhled" off). Unknown -> the original art."""
    try:
        import settingslook
        return settingslook.Get('look') != 'legacy'
    except Exception:
        return False


def R1ChannelFamily(action_id):
    return R1_KANAL + action_id.replace('.', '_')


def R1Channel(action_id):
    """True when ``action_id`` shows its R1 channel launcher now (R1 look and its art packed)."""
    return BaseFamily(action_id) == R1ChannelFamily(action_id)


def R1Family(family):
    """The R1 version of a launcher family (``althea_r1_minimapa/medallion/...``), None for an unknown folder."""
    for prefix, folder in R1_FOLDERS + ((R1_KANAL, 'medallion/kanal/'),):
        if family.startswith(prefix):
            return R1_MINIMAPA + folder + family[len(prefix):]
    return None


def R1Art(name):
    """``althea_r1_minimapa/<name>`` in the R1 look when it is packed, else None (the original art)."""
    path = R1_MINIMAPA + name
    return path if R1Look() and _exists(path) else None


def GameSetFamily(action_id):
    return SHORTCUTS + action_id.replace('.', '_')


def _exists(path):
    checker = FILE_EXISTS
    if checker is None:
        try:
            import app
        except ImportError:
            return False
        checker = getattr(app, 'IsExistFile', None)
    try:
        return bool(checker and checker(path))
    except Exception:
        return False


def _resolve(action_id, r1=False):
    if r1 and action_id in R1_CHANNEL_IDS:
        family = R1ChannelFamily(action_id)
        if all(_exists(family + '_' + state + '.png') for state in STATES):
            return family
    if action_id in APPROVED and not USE_GAME_SET_FOR_DEFAULTS:
        return APPROVED[action_id]
    if action_id in GAME_SET_IDS:
        family = GameSetFamily(action_id)
        if all(_exists(family + '_' + state + '.png') for state in STATES):
            return family
    if action_id in APPROVED:
        return APPROVED[action_id]
    if action_id in DERIVED:
        return DERIVED[action_id]
    return LEGACY.get(action_id, PLACEHOLDER)


def BaseFamily(action_id):
    """The family of today's art (the R1 channel launcher in the R1 look), before the R1 colours."""
    key = (action_id, action_id in R1_CHANNEL_IDS and R1Look())
    if key not in _resolved:
        _resolved[key] = _resolve(*key)
    return _resolved[key]


def Family(action_id):
    """The family drawn now: the R1 version of ``BaseFamily`` in the R1 look when all its states are packed."""
    family = BaseFamily(action_id)
    if not R1Look():
        return family
    key = ('r1', family)
    if key not in _resolved:
        r1 = R1Family(family)
        _resolved[key] = r1 if r1 and all(_exists(r1 + '_' + state + '.png') for state in STATES) else family
    return _resolved[key]


def ClearCache():
    _resolved.clear()


def HasIcon(action_id):
    return BaseFamily(action_id) != PLACEHOLDER


def Visual(action_id, state='normal'):
    if state not in STATES:
        raise ValueError('Unknown launcher state: %s' % state)
    return Family(action_id) + '_' + state + '.png'


# Native text on the placeholder for functions whose art is still pending.
PLACEHOLDER_MARKS = {'system.channel_switch': 'CH'}
PLACEHOLDER_MARKS.update(('channel.%d' % index, 'CH%d' % index) for index in range(1, 10))


def Mark(action_id):
    """Native text drawn over the medallion: '?' (or a short code) for a missing icon."""
    return '' if HasIcon(action_id) else PLACEHOLDER_MARKS.get(action_id, PLACEHOLDER_MARK)
