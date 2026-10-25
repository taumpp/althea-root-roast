"""Minimap tab of Settings -> Panely tlačítek (owner review 2026-10-04).

Compact visual editor on the shared ``uibuttonpanelpage.ButtonPanelPage``:

* right: the minimap frame with both launcher rings at their real offsets;
  only the assigned launchers plus ONE "+" on the next free slot (ring 1
  first, then ring 2), both connectors clipped like in game, the fixed
  "More" control;
* left: title, "?" help, ring counts and the search field;
* below: icon groups "Kruh 1 / Kruh 2 / Další / Skryto".

Every change is saved at once (``minimappanel`` / ``buttonpanelstore``) and
applied to the minimap. "Reset this page" restores the default five.
"""
import ui
import buttonpanellayout as layout
import minimappanel as panel
import minimappanelicons as icons
import uiminimappanelmenu as adapter
import buttonpanelsettings as panelsettings
from settingslocale import Text as T
from uibuttonpanelpage import ButtonPanelPage

FRAME = 'd:/ymir work/ui/public/crimson/windows/minimap/frame.tga'
ORBIT = 'd:/ymir work/ui/game/crimson_ember/minimap/launcher_orbit.png'
PANEL_ART = 'd:/ymir work/ui/game/crimson_ember/minimap_panel/'
# Launcher positions (uiscript/uiscript/minimap.py _MINIMAP_LAUNCHER_ARCS).
ARC = ((-15, 4), (-27, 33), (-32, 64), (-23, 94), (-4, 119),
       (-62, 4), (-72, 34), (-73, 65), (-67, 96), (-54, 124), (-33, 148), (-8, 167))
ORBIT_POS, ORBIT_HEIGHT = (-72, 0), 176
OUTER_POS, OUTER_HEIGHT = (-71, 10), 179
MORE_POS = (111, 50)
PREVIEW_X = 216
GROUPS_TOP = 198


class MinimapPanelPage(ButtonPanelPage):
    TITLE = T('Minimapa', 'Minimap')
    HELP = T('Klik = výběr funkce | tah = prohození nebo stav | klik na ikonu dole = přidat | ve hře pravý klik',
             'Click = choose · drag = swap or state · click an icon below = add · in game: right click')
    GROUP_PER_ROW = 10
    GROUP_LABEL_WIDTH = 46
    SEARCH_POS = (0, 64)
    STATUS_POS = (0, 92)
    STATUS_WIDTH = 140

    def __init__(self, owner):
        self.catalog = []
        self.entries = {}
        self.state = panel.PanelState()
        ButtonPanelPage.__init__(self, owner)

    @property
    def layout(self):
        return self.state.slots

    # Model ---------------------------------------------------------------------
    def _Interface(self):
        getter = getattr(getattr(self.owner, 'backend', None), 'interface', None)
        return getter() if callable(getter) else None

    def _Known(self):
        return tuple(entry.action_id for entry in self.catalog)

    def Reload(self):
        self.catalog = panel.Catalog(self._Interface())
        self.entries = dict((entry.action_id, entry) for entry in self.catalog)
        self.state = panel.LoadState(self._Known())

    def Known(self):
        return self._Known()

    def Label(self, action_id):
        entry = self.entries.get(action_id)
        if entry is None:
            return ''
        label = panel.Label(entry)
        shortcut = panel.ShortcutText(action_id)
        return '%s  [%s]' % (label, shortcut) if shortcut else label

    def Visuals(self, action_id):
        return tuple(icons.Visual(action_id, state) for state in icons.STATES)

    def Mark(self, action_id):
        return icons.Mark(action_id)

    def Groups(self):
        ring1, ring2 = panel.Rings(self.layout)
        known = self._Known()
        return (('ring1', T('Kruh 1', 'Ring 1'), list(layout.Assigned(ring1))),
                ('ring2', T('Kruh 2', 'Ring 2'), list(layout.Assigned(ring2))),
                ('menu', T('Další', 'More'), [a for a in known if self.state.Of(a) == panel.STATE_MENU]),
                ('hidden', T('Skryto', 'Hidden'), [a for a in known if self.state.Of(a) == panel.STATE_HIDDEN]))

    def GroupsTop(self):
        return self.top + GROUPS_TOP

    def SlotHome(self, index):
        return (PREVIEW_X + ARC[index][0], self.top + ARC[index][1])

    def SlotLayout(self):
        result = [(index, self.SlotHome(index), action_id) for index, action_id in enumerate(self.layout)]
        if len(self.layout) < panel.MAX_SLOTS:
            result.append((('plus',), self.SlotHome(len(self.layout)), None))
        return result

    def SlotTitle(self, key):
        if key == ('plus',):
            return T('Přidat prázdné místo', 'Add an empty slot')
        if key < len(self.layout) and self.layout[key] == layout.EMPTY:
            return T('Prázdné místo - klikni a vyber funkci', 'Empty slot – click to choose')
        return adapter.SlotTitle(key)

    def IsPlusKey(self, key):
        return key == ('plus',)

    def OnPlus(self, key):
        """"+" only adds an empty slot; clicking it then chooses the function (owner 2026-10-04)."""
        self._Commit(panel.PanelState(layout.AddEmpty(self.layout, panel.MAX_SLOTS), self.state.hidden))

    # Header ----------------------------------------------------------------------
    def BuildHeader(self, top):
        v = self.owner
        self.widgets['help'].SetPosition(76, top - 3)
        self.widgets['count'].SetPosition(0, top + 24)
        self.widgets['ring2'] = v.text('', 0, top + 40, small=True, width=100, color=(.84, .71, .47))
        ox, oy = PREVIEW_X, top
        frame = v._keep(ui.ImageBox(), ox, oy)
        frame.LoadImage(FRAME)
        frame.AddFlag('not_pick')
        orbit = v._keep(ui.ExpandedImageBox(), ox + ORBIT_POS[0], oy + ORBIT_POS[1])
        orbit.LoadImage(ORBIT)
        orbit.AddFlag('not_pick')
        outer = v._keep(ui.ExpandedImageBox(), ox + OUTER_POS[0], oy + OUTER_POS[1])
        outer.LoadImage(PANEL_ART + 'orbit_outer.png')
        outer.AddFlag('not_pick')
        more = v._keep(ui.ImageBox(), ox + MORE_POS[0], oy + MORE_POS[1])
        more.LoadImage(PANEL_ART + 'more_normal.png')
        more.AddFlag('not_pick')
        self.widgets['orbit'], self.widgets['outer'], self.widgets['more'] = orbit, outer, more

    def SyncHeader(self):
        ring1, ring2 = panel.Rings(self.layout)
        self.widgets['count'].SetText(T('Kruh 1: %d / %d', 'Ring 1: %d / %d')
                                      % (len(layout.Assigned(ring1)), panel.RING_SIZES[0]))
        self.widgets['ring2'].SetText(T('Kruh 2: %d / %d', 'Ring 2: %d / %d')
                                      % (len(layout.Assigned(ring2)), panel.RING_SIZES[1]))
        # Like the game (uiminimap.ApplyLauncherLayout): a connector ends under the
        # last function of its ring, empty places do not extend it.
        for key, top, height, offset, ring in (('orbit', ORBIT_POS[1], ORBIT_HEIGHT, 0, ring1),
                                               ('outer', OUTER_POS[1], OUTER_HEIGHT, len(ring1), ring2)):
            used = [index for index, action in enumerate(ring) if action != layout.EMPTY]
            self._ClipOrbit(self.widgets[key], top, height,
                            ARC[offset + used[-1]][1] if len(used) >= 2 else None)

    def _ClipOrbit(self, orbit, top, height, last_y):
        if last_y is None:
            orbit.Hide()
            return
        orbit.SetRenderingRect(0.0, 0.0, 0.0, float(last_y + 14 - top - height) / height)
        orbit.Show()

    # Operations ------------------------------------------------------------------
    def _Commit(self, state, status='', forget_unavailable=False):
        try:
            self.state = panel.SaveState(state, self._Known(), forget_unavailable=forget_unavailable)
            error = panelsettings.StoreErrorText()
        except (ValueError, TypeError):
            error = T('Nastavení panelu se nepodařilo uložit.', 'Could not save the panel settings.')
        if error:
            # Nothing was written: show what the game shows.
            self.state = panel.LoadState(self._Known())
            status = error
        self._Applied(status)

    def _Applied(self, status=''):
        minimap = getattr(self._Interface(), 'wndMiniMap', None)
        if minimap and hasattr(minimap, 'RefreshLauncherPanel'):
            minimap.RefreshLauncherPanel()
        self.Status(status)
        self.Sync()

    def _Index(self, key):
        return len(self.layout) if key == ('plus',) else key

    def OpenSlotPicker(self, key):
        adapter.OpenSlotPicker(self.Picker(), self._Interface(), self._Index(key), self._Picked,
                               self.PickerPosition(), on_close=self.PickerClosed)

    def _Picked(self):
        self.state = panel.LoadState(self._Known())
        self._Applied(panelsettings.StoreErrorText())

    def SwapSlots(self, first, second):
        self._Commit(panel.PanelState(layout.SwapSlots(self.layout, self._Index(first), self._Index(second)),
                                      self.state.hidden))

    def DropOnSlot(self, source, key):
        kind, value = source
        if kind == 'slot':
            self.SwapSlots(value, key)
            return
        slots = layout.AssignSlot(self.layout, self._Index(key), value, panel.MAX_SLOTS)
        hidden = set(self.state.hidden)
        hidden.discard(value)
        self._Commit(panel.PanelState(slots, hidden))

    def DropOnGroup(self, source, group):
        kind, value = source
        action_id = (self.layout[value] if kind == 'slot' and isinstance(value, int) and value < len(self.layout)
                     else value if kind == 'icon' else None)
        if not action_id:
            self.Sync()
            return
        if group in ('ring1', 'ring2'):
            self.AddAction(action_id)
            return
        self.SetState(action_id, panel.STATE_HIDDEN if group == 'hidden' else panel.STATE_MENU)

    def IconClickAdds(self, action_id):
        return self.state.Of(action_id) != panel.STATE_RING

    def AddAction(self, action_id):
        self.SetState(action_id, panel.STATE_RING)

    def SetState(self, action_id, chosen):
        slots = list(self.state.slots)
        hidden = set(self.state.hidden)
        if chosen == self.state.Of(action_id):
            self.Sync()
            return True
        if chosen == panel.STATE_RING:
            if len(slots) >= panel.MAX_SLOTS and layout.EMPTY not in slots:
                self.Status(T('Kruhy pojmou nejvýš %d tlačítek.', 'The rings hold at most %d buttons.')
                            % panel.MAX_SLOTS)
                self.Sync()
                return False
            # The first empty slot, else the next free place (ring 1 first, then ring 2).
            slots = list(layout.FillFirstEmpty(slots, action_id, panel.MAX_SLOTS))
            hidden.discard(action_id)
        else:
            slots = list(layout.RemoveAction(slots, action_id))
            if chosen == panel.STATE_HIDDEN:
                hidden.add(action_id)
            else:
                hidden.discard(action_id)
        self._Commit(panel.PanelState(slots, hidden))
        return True

    def RestoreDefaults(self):
        self._ClosePicker()
        self.selected = None
        self._Commit(panel.DefaultState(self._Known()), forget_unavailable=True)
