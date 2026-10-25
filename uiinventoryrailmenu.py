"""Inventory-rail adapter of the shared button-panel picker and context menu.

* "More" (``OpenMore``): the functions in the rail's "More" state; a click runs one.
* Slot picker (``OpenSlotPicker``): every function plus "Empty slot" for one
  rail slot (column, index); the choice is saved at once (a function already on
  the rail swaps places) and ``on_done`` refreshes the views.
* Rail context menu (``SlotMenuEntries``): Change… / Remove / Move to More.
* ``OpenSettings``: Settings -> Panely tlačítek with the Inventory tab.

The picker (``uibuttonpanelpicker``) and the context menu
(``uibuttonpanelcontext``) are the shared components of the minimap panel.
"""
import inventoryrail as rail
import inventoryrailicons as icons
import minimappanel
from settingslocale import Text as T
from uibuttonpanelpicker import PickerItem, EMPTY_ID


def MoreLabel():
    return minimappanel.MoreLabel()


def Entries(interface):
    """Catalogue entries by ID."""
    entries = dict((entry.action_id, entry) for entry in rail.Catalog(interface))
    return entries


def Label(entries, action_id):
    entry = entries.get(action_id)
    return minimappanel.Label(entry) if entry is not None else action_id


def Tooltip(entries, action_id):
    label = Label(entries, action_id)
    shortcut = minimappanel.ShortcutText(action_id)
    return '%s  [%s]' % (label, shortcut) if shortcut else label


def Items(entries, known_ids):
    items = []
    for action_id in known_ids:
        if action_id not in entries:
            continue
        label = Label(entries, action_id)
        items.append(PickerItem(action_id, label, Tooltip(entries, action_id),
                                icons.PickerVisuals(action_id), icons.PickerMark(action_id),
                                (label + ' ' + minimappanel.SearchAliases(action_id)).strip()))
    return items


def EmptyItem():
    import minimappanelicons
    return PickerItem(EMPTY_ID, T('Prázdný slot', 'Empty slot'), T('Prázdný slot', 'Empty slot'),
                      tuple(minimappanelicons.Visual(None, state) for state in minimappanelicons.STATES), '')


def SlotTitle(column, index, pages=False):
    if pages:
        return T('Strana %d | slot %d', 'Page %d · slot %d') % (column + 1, index + 1)
    return T('Slot %d.%d (lišta)', 'Slot %d·%d (rail)') % (column + 1, index + 1)


def OpenMore(picker, entries, known_ids, run_action, position, anchor_height=0):
    state = rail.LoadState(known_ids)
    menu = rail.MenuIds(state, known_ids)
    items = Items(entries, known_ids)
    picker.Open(MoreLabel(), items, menu, lambda action: action and run_action(action), position,
                anchor_height=anchor_height)


def Commit(state, known_ids):
    """Save from a game path; a failed write says so in the chat (audit 1.4)."""
    import buttonpanelsettings
    result = rail.SaveState(state, known_ids)
    buttonpanelsettings.ReportStoreError()
    return result


def OpenSlotPicker(picker, entries, known_ids, column, index, on_done, position, on_close=None,
                   anchor_height=0):
    def chosen(action):
        state = rail.LoadState(known_ids)
        Commit(rail.AssignSlot(state, column, index, action), known_ids)
        if on_done:
            on_done()
    pages = rail.LoadState(known_ids).IsPages()
    picker.Open(SlotTitle(column, index, pages), Items(entries, known_ids), None, chosen, position, EmptyItem(), on_close,
                anchor_height=anchor_height)


def SetFunctionState(known_ids, action, chosen):
    state = rail.SetFunctionState(rail.LoadState(known_ids), action, chosen)
    if state is None:
        return None
    return Commit(state, known_ids)


def SlotMenuEntries(open_picker, known_ids, action, on_done, open_settings=None):
    """Context menu entries for a rail button showing ``action``."""
    def remove():
        SetFunctionState(known_ids, action, rail.STATE_HIDDEN)
        on_done()

    def to_more():
        SetFunctionState(known_ids, action, rail.STATE_MENU)
        on_done()
    entries = [(T('Změnit...', 'Change…'), open_picker),
               (T('Odebrat', 'Remove'), remove),
               (T('Přesunout do Další', 'Move to More'), to_more)]
    if open_settings is not None:
        entries.append((T('Nastavení lišty...', 'Rail settings…'), open_settings))
    return tuple(entries)


def OpenSettings(interface, tab='inventory'):
    """Settings -> Panely tlačítek, on the given tab (ESC menu path)."""
    import buttonpanelsettings
    return buttonpanelsettings.Open(interface, tab)


def ToggleSettings(interface, tab='inventory'):
    """The cogwheel: open Panely tlačítek, a second click closes Settings."""
    import buttonpanelsettings
    return buttonpanelsettings.Toggle(interface, tab)
