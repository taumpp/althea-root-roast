"""Minimap adapter of the shared button-panel picker and context menu.

* "More" (``OpenMore``): the functions in the "More" state; a click runs one.
* Slot picker (``OpenSlotPicker``): every function plus "Empty slot" for one
  launcher slot; the choice is saved at once (a function shown elsewhere
  swaps places) and ``on_done`` refreshes the views.
* Launcher context menu (``SlotMenuEntries``): Change… / Remove / Move to More.

Used by the minimap (right click or Shift+click on a launcher, the "More"
control) and by Settings -> Panely tlačítek -> Minimapa.
"""
import buttonpanellayout as layout
import minimappanel as panel
import minimappanelicons as icons
from settingslocale import Text as T
from uibuttonpanelpicker import PickerItem, EMPTY_ID


def Items(entries):
    items = []
    for entry in entries:
        label = panel.Label(entry)
        shortcut = panel.ShortcutText(entry.action_id)
        items.append(PickerItem(entry.action_id, label, '%s  [%s]' % (label, shortcut) if shortcut else label,
                                tuple(icons.Visual(entry.action_id, state) for state in icons.STATES),
                                icons.Mark(entry.action_id),
                                (label + ' ' + panel.SearchAliases(entry.action_id)).strip()))
    return items


def EmptyItem():
    return PickerItem(EMPTY_ID, T('Prázdný slot', 'Empty slot'), T('Prázdný slot', 'Empty slot'),
                      tuple(icons.Visual(None, state) for state in icons.STATES), '')


def OpenMore(picker, interface, run_action, position):
    entries = panel.ShownInGame(panel.Catalog(interface))
    known = tuple(entry.action_id for entry in entries)
    menu = panel.MenuIds(panel.LoadState(known), known)
    picker.Open(panel.MoreLabel(), Items(entries), menu, lambda action: action and run_action(action), position)


def _Saved(state):
    """A failed write (newer file, disk, second client) says so in the chat (audit 1.4)."""
    import buttonpanelsettings
    buttonpanelsettings.ReportStoreError()
    return state


def AssignSlot(interface, index, action):
    """Put ``action`` (None = empty) into launcher slot ``index`` and save."""
    known = panel.AvailableIds(interface)
    state = panel.LoadState(known)
    slots = layout.AssignSlot(state.slots, index, action, panel.MAX_SLOTS)
    hidden = set(state.hidden)
    hidden.discard(action)
    return _Saved(panel.SaveState(panel.PanelState(slots, hidden), known))


def SetFunctionState(interface, action, chosen):
    """Move one function to the "More" menu or hide it (removing it from the rings)."""
    known = panel.AvailableIds(interface)
    state = panel.LoadState(known)
    slots = layout.RemoveAction(state.slots, action)
    hidden = set(state.hidden)
    if chosen == panel.STATE_HIDDEN:
        hidden.add(action)
    else:
        hidden.discard(action)
    return _Saved(panel.SaveState(panel.PanelState(slots, hidden), known))


def SlotTitle(index):
    ring = 1 if index < panel.RING_SIZES[0] else 2
    return T('Slot %d (kruh %d)', 'Slot %d (ring %d)') % (index + 1, ring)


def OpenSlotPicker(picker, interface, index, on_done, position, on_close=None):
    entries = panel.Catalog(interface)

    def chosen(action):
        AssignSlot(interface, index, action)
        if on_done:
            on_done()
    picker.Open(SlotTitle(index), Items(entries), None, chosen, position, EmptyItem(), on_close)


def SlotMenuEntries(open_picker, interface, action, on_done):
    """Context menu entries for a launcher showing ``action``."""
    def remove():
        SetFunctionState(interface, action, panel.STATE_HIDDEN)
        on_done()

    def to_more():
        SetFunctionState(interface, action, panel.STATE_MENU)
        on_done()
    return ((T('Změnit...', 'Change…'), open_picker),
            (T('Odebrat', 'Remove'), remove),
            (T('Přesunout do Další', 'Move to More'), to_more))
