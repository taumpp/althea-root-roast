# -*- coding: utf-8 -*-
"""Settings v5 -> Panely tlačítek: the pure model of the page (2026-10-05, design v4.1).

No window code here; ``uisettingspanelsv5`` draws the page from it. Storage stays the existing models
(``minimappanel`` / ``inventoryrail`` / ``buttonpanelbadges`` / ``uichannelbar``), so the format of
``UserData/button-panels.json`` is unchanged; the only addition is the small ``settings_page`` section
(``tour_seen``), which older clients keep untouched (``buttonpanelstore`` writes unknown sections back).

Places are PACKED like in game: the minimap and the rail skip the empty slots ('') that the old "+" of
the A7 page stored, so the n-th function always sits on the n-th place. Every operation here returns a new
state with the empty slots removed (``Pack``); what the preview shows is exactly what the game shows.
"""
import buttonpanelstore
import inventoryrail as rail
import minimappanel as panel

TAB_MINIMAP, TAB_RAIL, TAB_BADGES = 'minimap', 'inventory', 'badges'
TABS = (TAB_MINIMAP, TAB_RAIL, TAB_BADGES)
# Old tab keys (buttonpanelsettings.Open from the cogwheels) and search highlights -> tab.
TAB_ALIASES = {'minimap': TAB_MINIMAP, 'inventory': TAB_RAIL, 'rail': TAB_RAIL, 'badges': TAB_BADGES,
               'channels': TAB_BADGES}
HIGHLIGHT_TABS = {'minimap_panel': TAB_MINIMAP, 'minimap_panel_order': TAB_MINIMAP,
                  'minimap_panel_more': TAB_MINIMAP, 'inventory_panel': TAB_RAIL}

SECTION = 'settings_page'
EMPTY = ''


def TabOf(key):
    return TAB_ALIASES.get(key)


def IsChannel(action_id):
    return panel.ChannelIndex(action_id) is not None


def Pack(ids):
    """The functions of a list without the empty slots (what the game shows)."""
    return tuple(action for action in ids if action != EMPTY)


# Tour (4 steps) ------------------------------------------------------------------------------------
def TourSeen(path=None):
    section = buttonpanelstore.ReadSection(SECTION, path)
    return isinstance(section, dict) and section.get('tour_seen') is True


def MarkTourSeen(path=None):
    """Remember the finished or skipped tour; False when the file cannot be written (newer client, disk)."""
    section = buttonpanelstore.ReadSection(SECTION, path)
    section = dict(section) if isinstance(section, dict) else {}
    section['tour_seen'] = True
    return buttonpanelstore.WriteSection(SECTION, section, path)


# Minimap -------------------------------------------------------------------------------------------
def MinimapPacked(state):
    return panel.PanelState(Pack(state.slots), state.hidden)


def MinimapPlace(state, action, index):
    """Put ``action`` on place ``index`` (packed) of the rings.

    A function already in the rings moves there (the others close up); a new one is inserted. When all
    12 places are taken, a new function replaces the one on that place, which goes to "More".
    Returns ``(state, replaced action or None)`` or ``(None, None)`` when nothing can change.
    """
    slots = list(Pack(state.slots))
    hidden = set(state.hidden)
    hidden.discard(action)
    index = max(0, int(index))
    replaced = None
    if action in slots:
        source = slots.index(action)
        del slots[source]
        slots.insert(min(index, len(slots)), action)
    elif len(slots) < panel.MAX_SLOTS:
        slots.insert(min(index, len(slots)), action)
    elif index < len(slots):
        replaced, slots[index] = slots[index], action
    else:
        return None, None
    return panel.PanelState(slots, hidden), replaced


def MinimapAppend(state, action):
    return MinimapPlace(state, action, panel.MAX_SLOTS)


def MinimapRemove(state, action, hide=False):
    """Out of the rings into "More" (or hidden)."""
    slots = [item for item in Pack(state.slots) if item != action]
    hidden = set(state.hidden)
    if hide:
        hidden.add(action)
    else:
        hidden.discard(action)
    return panel.PanelState(slots, hidden)


def MinimapDefaultIndex(action, known_ids):
    layout = panel.DefaultLayout(known_ids)
    return layout.index(action) if action in layout else None


def MinimapToDefault(state, action, known_ids):
    """"Vrátit na výchozí místo": its default place in ring 1, or "More" for every other function."""
    index = MinimapDefaultIndex(action, known_ids)
    if index is None:
        return MinimapRemove(state, action), None
    return MinimapPlace(state, action, index)


def MinimapSections(state, known_ids):
    """Catalogue sections of the Minimapa tab: [(key, ids)] in display order."""
    slots = Pack(state.slots)
    ring1, ring2 = slots[:panel.RING_SIZES[0]], slots[panel.RING_SIZES[0]:panel.MAX_SLOTS]
    menu = [a for a in known_ids if state.Of(a) == panel.STATE_MENU]
    return (('ring1', list(ring1)), ('ring2', list(ring2)),
            ('menu', [a for a in menu if not IsChannel(a)]),
            ('hidden', [a for a in known_ids if state.Of(a) == panel.STATE_HIDDEN]),
            ('channels', [a for a in menu if IsChannel(a)]))


# Inventory rail ------------------------------------------------------------------------------------
def RailPacked(state):
    return state.Replace(columns=tuple(Pack(column) for column in state.columns) or ((),))


def RailLists(state):
    """The lists the editor shows: the pages of the pages mode, both columns of the columns mode."""
    lists = [Pack(column) for column in state.columns[:state.ListCount()]]
    while len(lists) < state.ListCount():
        lists.append(())
    return lists


def RailWhere(state, action):
    for column, ids in enumerate(RailLists(state)):
        if action in ids:
            return column, ids.index(action)
    return None


def RailPlace(state, action, column, index):
    """Put ``action`` on place ``index`` of list ``column`` (a page or a column).

    Moving inside one list reorders it; from another list it is inserted (when the target list is full the
    two functions swap places); a new function is inserted, or replaces the function on that place when the
    list is full (that one goes to "More"). Returns ``(state, replaced or None)`` or ``(None, None)``.
    """
    if not 0 <= column < state.ListCount():
        return None, None
    lists = [list(ids) for ids in RailLists(state)]
    parked = [Pack(c) for c in state.columns[state.ListCount():]]
    hidden = set(state.hidden)
    hidden.discard(action)
    target = lists[column]
    index = max(0, int(index))
    replaced = None
    where = RailWhere(state, action)
    if where is not None and where[0] == column:
        del target[where[1]]
        target.insert(min(index, len(target)), action)
    elif where is not None:
        source = lists[where[0]]
        if len(target) < rail.MAX_PER_COLUMN:
            del source[where[1]]
            target.insert(min(index, len(target)), action)
        elif index < len(target):
            source[where[1]], target[index] = target[index], action
        else:
            return None, None
    elif len(target) < rail.MAX_PER_COLUMN:
        target.insert(min(index, len(target)), action)
    elif index < len(target):
        replaced, target[index] = target[index], action
    else:
        return None, None
    columns = [tuple(ids) for ids in lists] + list(parked)
    while len(columns) > 1 and not columns[-1]:
        columns.pop()
    result = state.Replace(columns=columns, hidden=hidden)
    if not state.IsPages() and column == 1:
        result = result.Replace(collapsed=False)   # a function dropped on column 2 shows it
    return result, replaced


def RailAppend(state, action, column=None):
    """The first place with room: the given list, else the shown page / column 1 first (rail.AddToRail)."""
    if column is not None:
        lists = RailLists(state)
        if 0 <= column < len(lists) and len(lists[column]) < rail.MAX_PER_COLUMN:
            return RailPlace(state, action, column, rail.MAX_PER_COLUMN)
    if RailWhere(state, action) is not None:
        return state, None
    result = rail.AddToRail(RailPacked(state), action, column)
    return (result, None) if result is not None else (None, None)


def RailRemove(state, action, hide=False):
    result = rail.SetFunctionState(RailPacked(state), action, rail.STATE_HIDDEN if hide else rail.STATE_MENU)
    return result


def RailDefaultIndex(action, known_ids):
    layout = rail.DefaultState(known_ids).columns[0]
    return layout.index(action) if action in layout else None


def RailToDefault(state, action, known_ids):
    index = RailDefaultIndex(action, known_ids)
    if index is None:
        return RailRemove(state, action), None
    return RailPlace(state, action, 0, index)


def RailSections(state, known_ids):
    """Catalogue sections of the Lišta tab: [(key, ids)]; 'rail' lists every function on the rail."""
    on_rail = [a for ids in RailLists(state) for a in ids]
    menu = [a for a in known_ids if state.Of(a) == rail.STATE_MENU]
    return (('rail', on_rail),
            ('menu', [a for a in menu if not IsChannel(a)]),
            ('hidden', [a for a in known_ids if state.Of(a) == rail.STATE_HIDDEN]),
            ('channels', [a for a in menu if IsChannel(a)]))


def RailContentPages(state):
    return [page for page, ids in enumerate(RailLists(state)) if ids] if state.IsPages() else []


# Reset (Obnovit stránku) -----------------------------------------------------------------------------
SCOPE_TAB, SCOPE_PAGE = 'tab', 'page'


def ResetTabs(tab, scope):
    return TABS if scope == SCOPE_PAGE else (tab,)


# Channel bar lock (uichannelbar, section 'channel_bar') ------------------------------------------------
CHANNEL_BAR = 'channel_bar'


def ChannelBarPinned(path=None):
    section = buttonpanelstore.ReadSection(CHANNEL_BAR, path)
    return isinstance(section, dict) and section.get('pinned') is True


def SetChannelBarPinned(pinned, path=None):
    """The same section as ``uichannelbar.BarSettings``: absent = popup, {'pinned': True[, x, y]} = pinned."""
    section = buttonpanelstore.ReadSection(CHANNEL_BAR, path)
    value = None
    if pinned:
        value = {'pinned': True}
        if isinstance(section, dict):
            x, y = section.get('x'), section.get('y')
            if isinstance(x, int) and isinstance(y, int) and not isinstance(x, bool) and not isinstance(y, bool):
                value.update(x=x, y=y)
    return buttonpanelstore.WriteSection(CHANNEL_BAR, value, path)


# Tour dimming --------------------------------------------------------------------------------------
def Complement(width, height, holes):
    """Rectangles covering (0, 0, width, height) except the ``holes`` [(x, y, w, h)] (the dimmed parts of
    the window while the tour highlights the holes). Horizontal bands, left to right."""
    clipped = []
    for x, y, w, h in holes:
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(int(width), int(x + w)), min(int(height), int(y + h))
        if x1 > x0 and y1 > y0:
            clipped.append((x0, y0, x1, y1))
    edges = sorted(set([0, int(height)] + [y for hole in clipped for y in (hole[1], hole[3])]))
    result = []
    for top, bottom in zip(edges, edges[1:]):
        if bottom <= top:
            continue
        spans = sorted((x0, x1) for x0, y0, x1, y1 in clipped if y0 < bottom and y1 > top)
        x = 0
        for x0, x1 in spans:
            if x0 > x:
                result.append((x, top, x0 - x, bottom - top))
            x = max(x, x1)
        if x < width:
            result.append((x, top, int(width) - x, bottom - top))
    return result
