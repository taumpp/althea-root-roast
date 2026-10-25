"""The only function -> icon table of the inventory shortcut rail.

A rail button is the 37x37 ``rail_button`` carrier with a 24x24 icon at (7,5).
Resolution order for one action ID:

0. The R1 channel launchers (``minimappanelicons.R1Channel``), rail size
   ``althea_r1_kanal/<id>.png``, in the R1 look when packed.
1. The 2026-10-04 game icon set, rail size: ``system_shortcuts/<id with
   '.' -> '_'>.png`` when packed (``tools/button_panel_icons/mapping.json`` rail_24);
   used for the default twelve too (``USE_GAME_SET_FOR_DEFAULTS``).
2. ``APPROVED`` - the approved item-art of today's twelve rail buttons
   (``locale/locale/common/ui/expandedtaskbar.py``) when the set is absent.
3. Fallback: the function's 28x28 minimap medallion (``minimappanelicons``),
   drawn at (4,4) on the carrier; a missing medallion shows the placeholder
   with a native "?".
"""
import minimappanelicons

SHORTCUTS = 'd:/ymir work/ui/game/crimson_ember/system_shortcuts/'
RAIL = 'd:/ymir work/ui/game/crimson_ember/inventory/'
ICON_POS = (7, 5)
MEDALLION_POS = (4, 4)

APPROVED = {
    'inventory.special': SHORTCUTS + 'special_bag_leather_v3.png',
    'system.quick_equip': SHORTCUTS + 'quick_equip_sets_B_24.png',
    'inventory.dragon_soul': SHORTCUTS + 'legendary_diamond_114300.png',
    'system.biolog': SHORTCUTS + 'orc_tooth_30006.png',
    'system.teleport': SHORTCUTS + 'teleport_ring_70058.png',
    'system.pet': SHORTCUTS + 'pet_paw_new_v1.png',
    'system.shop_search': SHORTCUTS + 'market_search_blue_v1.png',
    'system.switchbot': SHORTCUTS + 'enchant_71084.png',
    'system.talisman': SHORTCUTS + 'talisman_9600.png',
    'system.mission_books': SHORTCUTS + 'mission_book_50310.png',
    'system.mount': SHORTCUTS + 'mount_horse_new_v1.png',
    'system.dew_craft': SHORTCUTS + 'red_dew_50821.png',
}
SETTINGS = RAIL + 'rail_settings_'
STATES = ('normal', 'hover', 'pressed')

# Owner 2026-10-04: the chosen game set (rail_24) replaces the approved item-art
# for the default twelve too when it is packed; the item-art stays the fallback.
USE_GAME_SET_FOR_DEFAULTS = True

# Optional file-existence hook (tests); the client uses app.IsExistFile.
FILE_EXISTS = None
_resolved = {}


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


def GameSetIcon(action_id):
    return SHORTCUTS + action_id.replace('.', '_') + '.png'


def _resolve(action_id, r1=False):
    if r1 and minimappanelicons.R1Channel(action_id):
        icon = minimappanelicons.R1ChannelFamily(action_id) + '.png'
        if _exists(icon):
            return icon, ICON_POS, ''
    if USE_GAME_SET_FOR_DEFAULTS or action_id not in APPROVED:
        if action_id in minimappanelicons.GAME_SET_IDS and _exists(GameSetIcon(action_id)):
            return GameSetIcon(action_id), ICON_POS, ''
    if action_id in APPROVED:
        return APPROVED[action_id], ICON_POS, ''
    return minimappanelicons.Visual(action_id, 'normal'), MEDALLION_POS, minimappanelicons.Mark(action_id)


def Icon(action_id):
    """(image path, position on the 37x37 carrier, native mark text)."""
    # The look is in the key of every function: the medallion fallback is drawn in the R1 colours in the R1 look.
    key = (action_id, minimappanelicons.R1Look())
    if key not in _resolved:
        _resolved[key] = _resolve(*key)
    return _resolved[key]


def ClearCache():
    _resolved.clear()


def PickerVisuals(action_id):
    """Three medallion states for the shared picker (28 px grid)."""
    return tuple(minimappanelicons.Visual(action_id, state) for state in STATES)


def PickerMark(action_id):
    return minimappanelicons.Mark(action_id)


def SettingsVisual(state):
    return SETTINGS + state + '.png'
