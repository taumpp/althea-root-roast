"""Configurable minimap launcher panel: catalogue, rings, "More" menu, storage.

The catalogue reuses the keybinding action registry (``keybindings.py``), so a
panel button and its shortcut share one stable action ID and one interface
callback. Panel-only functions without a keyboard action (the rated arena and
the inventory-rail windows) are added here with IDs in the same namespace.

Every function has one of three states: in a launcher ring (``slots``, in
order: five in ring 1, then seven in ring 2), in the "More" menu (the default
for every other function) or hidden. The state is presentation only and is
stored per PC in the ``minimap`` section of ``UserData/button-panels.json``
(``buttonpanelstore``). Without a stored section the default five are shown.
Unknown, retired, duplicate or disabled IDs are ignored, and at most
``MAX_SLOTS`` functions are placed in the rings.
"""

try:
    import app
except ImportError:
    app = None

import buttonpanelstore

SECTION = 'minimap'
RING_SIZES = (5, 7)
MAX_SLOTS = sum(RING_SIZES)
STATE_RING, STATE_MENU, STATE_HIDDEN = 'ring', 'menu', 'hidden'

# Default ring 1 (owner 2026-10-04): the ALTHEA-611 order without the rated
# arena, which stays available in the catalogue and in the "More" menu while
# the server has it open (``server_feature``), and
# without the Battle Pass, switched off on 2026-10-05 (keybindings.py
# RETIRED_ACTION_IDS).
DEFAULT_IDS = (
    'system.custom_ports',
    'information.skill_tree',
    'information.ranking',
    'information.event_calendar',
)

# Layout revision written with every saved minimap section. A section saved
# before revision 2 gets the skill tree launcher back once (``RESTORE_ONCE``):
# the panel used to offer it only as a default, so a layout filled by hand
# lost the button around the minimap and players looked for it in vain. After
# the next save the player's choice is final - moved to "More" or hidden, it
# stays there.
LAYOUT_REV = 2
RESTORE_ONCE = ('information.skill_tree',)

# Keyboard actions that never belong on the panel.
EXCLUDED_IDS = frozenset((
    'information.minimap',  # would hide the panel it is placed on
    'system.auto_hunt',     # removed from player menus (ALTHEA-465)
    'system.mining_check',  # the key of the mining skill check (uiminingcheck), not a window
))


class PanelAction(object):
    """One selectable panel function (no callback reference is retained).

    ``feature`` is the client build flag (``app``); ``server_feature`` a
    server-owned switch (``featureavailability`` name): while the server
    reports it off the function is not offered anywhere (rings, "More",
    Settings), and a stored layout keeps its place for when it reopens.
    """
    __slots__ = ('action_id', 'locale_key', 'fallback', 'callback_name', 'feature', 'server_feature')

    def __init__(self, action_id, locale_key, fallback, callback_name=None, feature=None, server_feature=None):
        self.action_id = action_id
        self.locale_key = locale_key
        self.fallback = fallback
        self.callback_name = callback_name
        self.feature = feature
        self.server_feature = server_feature


# Panel-only functions: (Czech, English) fallback when the locale key is absent.
EXTRA_ACTIONS = (
    PanelAction('system.pvp_matchmaking', 'MINIMAP_PANEL_RANKED_ARENA',
                ('Hodnocená aréna', 'Rated arena'), 'TogglePvPMatchmakingWindow', 'ENABLE_PVP_MATCHMAKING',
                server_feature='ranked_arena'),
    PanelAction('system.biolog', 'TOOLTIP_TEXT_MINIMAP_BIOLOG',
                ('Biolog', 'Biologist'), 'ToggleBiologWindow', 'ENABLE_BIOLOG_SYSTEM'),
    PanelAction('system.talisman', 'TALISMAN_WINDOW_TOOLTIP',
                ('Talismany', 'Talismans'), 'ToggleTalismanWindow'),
    PanelAction('system.mission_books', 'MINIMAP_PANEL_MISSION_BOOKS',
                ('Knihy misí', 'Mission books'), 'ToggleMissionBooks'),
    PanelAction('system.dew_craft', 'MINIMAP_PANEL_DEW_CRAFT',
                ('Výroba ros', 'Dew crafting'), 'ToggleDewCraftWindow', 'ENABLE_CUBE_RENEWAL'),
    PanelAction('system.quick_equip', 'MINIMAP_PANEL_QUICK_EQUIP',
                ('Rychlá výměna setu', 'Quick set swap'), 'ToggleQuickEquipWindow'),
    # Opens the channel bar at the button (root/uichannelbar.py, owner 2026-10-04);
    # the callback is the fallback and the availability check (ESC menu).
    PanelAction('system.channel_switch', 'MINIMAP_PANEL_CHANNEL_SWITCH',
                ('Změna kanálu', 'Change channel'), 'OpenSystemDialog', 'ENABLE_MOVE_CHANNEL'),
)
_EXTRAS_BY_ID = dict((action.action_id, action) for action in EXTRA_ACTIONS)

# Minimap hover texts kept from the fixed six-button layout.
TOOLTIP_KEYS = {
    'system.battle_pass': 'TOOLTIP_TEXT_MINIMAP_BATTLEPASS',
    'information.skill_tree': 'SKILL_TREE_TITLE',
    'information.ranking': 'TOOLTIP_TEXT_MINIMAP_RANKING',
    'information.event_calendar': 'TOOLTIP_TEXT_MINIMAP_CALENDAR',
    # The craft book is a keybinding action (system.craft_book, unbound by default) in "Další" by default.
    'system.craft_book': 'MINIMAP_PANEL_CRAFT_BOOK',
}


def _feature_enabled(name):
    return bool(name is None or (app is not None and getattr(app, name, False)))


def _server_open(name):
    """A server-owned switch (featureavailability.IsShown); hidden when unknown."""
    if name is None:
        return True
    try:
        import featureavailability
        return bool(featureavailability.IsShown(name))
    except Exception:
        return False


def ServerOpen(action_id):
    """False while the server reports a panel-only function's feature off."""
    extra = _EXTRAS_BY_ID.get(action_id)
    return extra is None or _server_open(extra.server_feature)


def _keybindings():
    try:
        import keybindings
    except ImportError:
        return None
    return keybindings


def _channel_actions(module, interface):
    """The keybinding channel actions (``channel.N``): same callback as the
    shortcut and the ESC menu (``uisystem.RequestChannelChange``)."""
    loader = getattr(module, '_load_uisystem', None)
    try:
        uisystem = loader() if callable(loader) else None
    except Exception:
        uisystem = None
    count = getattr(uisystem, 'GetChannelCount', None)
    request = getattr(uisystem, 'RequestChannelChange', None)
    if not callable(count) or not callable(request):
        return []
    try:
        channel_count = int(count())
    except Exception:
        return []
    return [action for action in module.build_actions(interface, channel_count, request)
            if action.action_id.startswith('channel.')]


def ChannelIndex(action_id):
    if isinstance(action_id, str) and action_id.startswith('channel.'):
        try:
            return int(action_id.split('.', 1)[1])
        except ValueError:
            return None
    return None


def Catalog(interface):
    """Available panel functions in display order (keybinding order, extras, then channels)."""
    if interface is None:
        return []
    entries = []
    module = _keybindings()
    if module is not None:
        for action in module.build_actions(interface, 0):
            if action.action_id in EXCLUDED_IDS or action.action_id in _EXTRAS_BY_ID:
                continue
            entries.append(PanelAction(action.action_id, action.locale_key, (action.action_id, action.action_id)))
    for extra in EXTRA_ACTIONS:
        if (_feature_enabled(extra.feature) and _server_open(extra.server_feature)
                and callable(getattr(interface, extra.callback_name, None))):
            entries.append(extra)
    if module is not None:
        # One button per channel (owner 2026-10-04), exactly like the channel shortcuts.
        for action in _channel_actions(module, interface):
            index = ChannelIndex(action.action_id)
            entries.append(PanelAction(action.action_id, action.locale_key,
                                       ('Kanál %d' % index, 'Channel %d' % index)))
    return entries


def SearchAliases(action_id):
    """Extra search words: "ch 2", "kanal 2", "kanál" find the channel buttons."""
    index = ChannelIndex(action_id)
    if index is not None:
        return 'CH %d CH%d kanál %d kanal %d channel %d' % ((index,) * 5)
    if action_id == 'system.channel_switch':
        return 'CH kanál kanal channel'
    return ''


def AvailableIds(interface):
    return tuple(entry.action_id for entry in Catalog(interface))


CHANNEL_SWITCH = 'system.channel_switch'


def Invoke(action_id, interface):
    """Run one panel function through its keybinding or panel-only callback."""
    callback = None
    extra = _EXTRAS_BY_ID.get(action_id)
    if extra is not None:
        if interface is not None and _feature_enabled(extra.feature):
            callback = getattr(interface, extra.callback_name, None)
            if action_id == CHANNEL_SWITCH and callable(callback) and _OpenChannelBar(interface):
                return True
    elif action_id not in EXCLUDED_IDS:
        module = _keybindings()
        manager = module.GetManager() if module is not None else None
        if manager is not None:
            try:
                callback = manager.get_action(action_id).callback
            except KeyError:
                callback = None
        if callback is None and interface is not None and module is not None:
            actions = (_channel_actions(module, interface) if ChannelIndex(action_id) is not None
                       else module.build_actions(interface, 0))
            for action in actions:
                if action.action_id == action_id:
                    callback = action.callback
                    break
    if not callable(callback):
        return False
    callback()
    return True


def _OpenChannelBar(interface):
    """The channel bar instead of the whole ESC menu; False falls back to the menu."""
    try:
        import uichannelbar
    except Exception:
        return False
    return uichannelbar.Toggle(interface)


def _text(key, fallback):
    try:
        import uiScriptLocale
        value = getattr(uiScriptLocale, key, None)
    except ImportError:
        value = None
    if isinstance(value, str) and value:
        return value
    if fallback[0] == fallback[1]:
        return fallback[0]
    try:
        from settingslocale import Text
        return Text(fallback[0], fallback[1])
    except ImportError:
        return fallback[0]


def MoreLabel():
    return _text('MINIMAP_PANEL_MORE', ('Další', 'More'))


def SettingsLabel():
    return _text('MINIMAP_PANEL_SETTINGS', ('Nastavení panelu', 'Panel settings'))


def Label(entry):
    label = _text(entry.locale_key, entry.fallback)
    if ChannelIndex(entry.action_id) in VIP_CHANNELS:
        label += _text('MINIMAP_PANEL_VIP_ONLY', (' | jen s VIP', ' · VIP only'))
    return label


# VIP channels (uisystem.RequestChannelChange): without VIP their buttons are not
# shown in game at all (owner 2026-10-04: "prostě ho tam mít nebudu"); Settings
# keeps them, labelled "jen s VIP", and the stored layouts keep them too.
VIP_CHANNELS = (6, 7)


def VipActive():
    try:
        import player
        return bool(player.IsVipActive())
    except Exception:
        return False


def ShownInGame(entries):
    """The catalogue entries a panel shows in game: no VIP channel without VIP."""
    vip = VipActive()
    return [entry for entry in entries if vip or ChannelIndex(entry.action_id) not in VIP_CHANNELS]


def _ShownKey():
    """What decides which catalogue entries show: VIP and the server switches."""
    gates = tuple(_server_open(extra.server_feature) for extra in EXTRA_ACTIONS if extra.server_feature)
    return VipActive(), gates


def VipChanged(owner):
    """True once when VIP started or ended, or a server switch (the rated arena)
    opened or paused, since ``owner`` last built its panel (``owner._panelVip``,
    set by ``MarkVip`` at every rebuild)."""
    key = _ShownKey()
    last = getattr(owner, '_panelVip', None)
    owner._panelVip = key
    return last is not None and last != key


def MarkVip(owner):
    owner._panelVip = _ShownKey()


def TooltipText(entry):
    key = TOOLTIP_KEYS.get(entry.action_id)
    return _text(key, (Label(entry), Label(entry))) if key else Label(entry)


def Normalize(ids, known_ids, limit=MAX_SLOTS):
    """Keep known IDs once, in order, and at most ``limit`` of them."""
    known = set(known_ids)
    result = []
    if not isinstance(ids, (list, tuple)):
        return ()
    for action_id in ids:
        if isinstance(action_id, str) and action_id in known and action_id not in result:
            result.append(action_id)
            if len(result) >= limit:
                break
    return tuple(result)


EMPTY = ''


def NormalizeSlots(ids, known_ids, limit=MAX_SLOTS):
    """Like ``Normalize`` but keeps the empty slots ('') added with "+" in Settings."""
    known = set(known_ids)
    result = []
    if not isinstance(ids, (list, tuple)):
        return ()
    for action_id in ids:
        if action_id == EMPTY or (isinstance(action_id, str) and action_id in known and action_id not in result):
            result.append(action_id)
            if len(result) >= limit:
                break
    return tuple(result)


def DefaultLayout(known_ids):
    return Normalize(DEFAULT_IDS, known_ids)


class PanelState(object):
    """Ring order plus the functions hidden from the "More" menu."""
    __slots__ = ('slots', 'hidden')

    def __init__(self, slots=(), hidden=()):
        self.slots = tuple(slots)
        self.hidden = frozenset(action for action in hidden if action not in self.slots)

    def __eq__(self, other):
        return isinstance(other, PanelState) and (self.slots, self.hidden) == (other.slots, other.hidden)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'PanelState(%r, %r)' % (self.slots, sorted(self.hidden))

    def Of(self, action_id):
        if action_id in self.slots:
            return STATE_RING
        return STATE_HIDDEN if action_id in self.hidden else STATE_MENU


def DefaultState(known_ids):
    return PanelState(DefaultLayout(known_ids), ())


def Rings(slots):
    """Split a slot order into (ring 1, ring 2)."""
    return tuple(slots[:RING_SIZES[0]]), tuple(slots[RING_SIZES[0]:MAX_SLOTS])


def MenuIds(state, known_ids):
    """Functions of the "More" menu, in catalogue order."""
    return tuple(action for action in known_ids if state.Of(action) == STATE_MENU)


def _saved(path=None):
    section = buttonpanelstore.ReadSection(SECTION, path)
    if not isinstance(section, dict) or not isinstance(section.get('slots'), list):
        return None
    hidden = section.get('hidden', [])
    rev = section.get('rev', 1)
    return dict(slots=section['slots'], hidden=hidden if isinstance(hidden, list) else [],
                rev=rev if isinstance(rev, int) and not isinstance(rev, bool) else 1)


def RestoreOnce(slots, hidden, known_ids):
    """Put the ``RESTORE_ONCE`` functions back into a layout saved before ``LAYOUT_REV``.

    Each goes to its default place (the skill tree: ring 1, place 2) unless the
    layout already has it or the player hid it. In full rings it takes the first
    empty place after that; without one the last function moves to "More".
    """
    slots = list(slots)
    known = set(known_ids)
    for action in RESTORE_ONCE:
        if action not in known or action in slots or action in hidden:
            continue
        index = min(list(DEFAULT_IDS).index(action) if action in DEFAULT_IDS else len(slots), len(slots))
        slots.insert(index, action)
        if len(slots) > MAX_SLOTS:
            empty = [place for place in range(index + 1, len(slots)) if slots[place] == EMPTY]
            del slots[empty[0] if empty else MAX_SLOTS]
    return tuple(slots)


def LoadState(known_ids, path=None):
    saved = _saved(path)
    if saved is None:
        return DefaultState(known_ids)
    slots = NormalizeSlots(saved['slots'], known_ids)
    if saved['slots'] and not slots:
        # Only unknown/retired functions were saved: fall back to the default rings.
        slots = DefaultLayout(known_ids)
    hidden = Normalize(saved['hidden'], known_ids, limit=max(1, len(known_ids)))
    if saved['rev'] < LAYOUT_REV:
        slots = RestoreOnce(slots, hidden, known_ids)
    return PanelState(slots, hidden)


def LoadLayout(known_ids, path=None):
    return LoadState(known_ids, path).slots


def SaveState(state, known_ids, path=None, forget_unavailable=False):
    """Persist a state; the default state removes the section (follow defaults).

    Functions stored earlier but not offered now (a feature flag, a missing
    callback, a channel above today's count) stay stored at their places unless
    ``forget_unavailable`` (Restore defaults); see ``buttonpanelstore.KeepUnavailable``.
    A failed write keeps the old file; ``buttonpanelstore.LastError()`` says why.
    """
    slots = NormalizeSlots(state.slots, known_ids)
    hidden = Normalize(sorted(state.hidden), known_ids, limit=max(1, len(known_ids)))
    result = PanelState(slots, hidden)
    stored = None if forget_unavailable else _saved(path)
    kept_slots = buttonpanelstore.KeepUnavailable(result.slots, stored['slots'], known_ids) \
        if stored else list(result.slots)
    kept_hidden = buttonpanelstore.Unavailable(stored['hidden'], known_ids) if stored else []
    if result == DefaultState(known_ids) and len(kept_slots) == len(result.slots) and not kept_hidden:
        value = None
    else:
        value = dict(slots=kept_slots, hidden=sorted(set(result.hidden) | set(kept_hidden)), rev=LAYOUT_REV)
    buttonpanelstore.WriteSection(SECTION, value, path)
    return result


def ShortcutText(action_id):
    """Current keyboard shortcut of a catalogue function ('' when unbound)."""
    module = _keybindings()
    manager = module.GetManager() if module is not None else None
    if manager is None:
        return ''
    try:
        shortcut = manager.clone_state().get(action_id)
    except (KeyError, AttributeError):
        return ''
    if shortcut is None:
        return ''
    try:
        return shortcut.display()
    except Exception:
        return ''


# The embedded client omits unicodedata: fold Czech search terms with plain
# string operations (same rule as the settings search).
_SEARCH_FOLD = str.maketrans('áčďéěíňóřšťúůýž', 'acdeeinorstuuyz')


def SearchText(text):
    return ''.join(c for c in str(text).casefold().translate(_SEARCH_FOLD)
                   if not '\u0300' <= c <= '\u036f')


def Matches(entry, query):
    query = SearchText(query).strip()
    return (not query or query in SearchText(Label(entry)) or query in SearchText(entry.action_id)
            or query in SearchText(SearchAliases(entry.action_id)))
