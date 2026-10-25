"""Shared page of Settings -> Panely tlačítek (minimap and inventory tabs).

Owner review 2026-10-04 ("hnusné, vylité"): the tab is a compact visual
editor that fits the 352x456 settings viewport.

* Preview: only the assigned buttons plus ONE "+" for the next free slot.
  No text is drawn in or next to the preview; a function's name is a hover
  tooltip (``HoverTip``: the TOP_MOST game tooltip board placed outside the
  hovered widget, so nothing covers it and it never stays on screen).
* Overview: a grid of 28 px medallions split into small groups (e.g. "V liště
  / V menu Další / Skryto"), filtered by a small search field.
* Click a slot: the shared picker for that slot. Click slot A, then slot B
  (while the picker is open): swap. Drag a button or a grid icon onto a slot
  (assign/swap) or onto a group (change state); dropping anywhere else puts
  it back. Click a grid icon outside the panel: add it to the next free slot.
* Help is one "?" button with a tooltip.

Subclasses provide the model: slot geometry, groups and the operations.
"""
import math

import ui
import fontconfig
from settingslocale import Text as T

INK = (.88, .85, .78)
DIM = (.68, .64, .58)
GOLD = (.84, .71, .47)
MUTED = (.55, .5, .46)
SHORTCUTS = 'd:/ymir work/ui/game/crimson_ember/system_shortcuts/'
SEARCH_ART = 'd:/ymir work/ui/game/crimson_ember/inventory/'
PLACEHOLDER = tuple(SHORTCUTS + 'placeholder_%s.png' % state for state in ('normal', 'hover', 'pressed'))
BADGE_OFF = 'd:/ymir work/ui/game/crimson_ember/button_panel_badges/dot_off.png'
# A small quiet dot: the function has a badge or a state (right click offers it).
BADGE_SUPPORT = 'd:/ymir work/ui/game/crimson_ember/button_panel_badges/dot_support.png'
VIEW_WIDTH = 352
CELL = 30
ICON = 28
DRAG_THRESHOLD = 4
DROP_MARGIN = 4
GROUP_GAP = 2
GROUP_COLOR = (.055, .043, .043, .85)


def SetVisuals(button, visuals):
    button.SetUpVisual(visuals[0])
    button.SetOverVisual(visuals[1])
    button.SetDownVisual(visuals[2])


def _OnRightClick(button, event, *args):
    # ui.Button.OnMouseRightButtonUp only dispatches its string-event table.
    setter = getattr(button, 'SAFE_SetStringEvent', None)
    if setter is not None:
        setter('MOUSE_RIGHT_BUTTON_UP', event, *args)


def Fold(text):
    """Accent-insensitive search key, shared with the More window (``minimappanel.SearchText``)."""
    import minimappanel
    return minimappanel.SearchText(text)


class HoverTip(object):
    """Polled hover tooltip of the settings previews and grids.

    Drag buttons cannot use per-button tooltips (the native mouse-out shows
    them again), and a text child would be drawn under neighbouring widgets.
    The page polls ``IsIn`` in OnUpdate and shows the shared TOP_MOST
    ``PanelToolTip`` outside the hovered widget.
    """

    def __init__(self, owner):
        import uibuttonpaneltooltip
        self.owner = owner
        self.tooltip = uibuttonpaneltooltip.PanelToolTip()
        self.current = None

    def Update(self, entries):
        for entry in entries:
            widget, text = entry[0], entry[1]
            side = entry[2] if len(entry) > 2 else 'above'
            if widget is None or not text or not widget.IsShow():
                continue
            is_in = getattr(widget, 'IsIn', None)
            if is_in is None or not is_in():
                continue
            if self.current != (widget, text):
                edge = entry[3] if len(entry) > 3 else None
                self.tooltip.Show(widget, text, side, edge)
                self.current = (widget, text)
            return text
        self.Hide()
        return None

    def IsShow(self):
        return self.tooltip.IsShow()

    def Text(self):
        return self.tooltip.text if self.tooltip.IsShow() else None

    def Hide(self):
        self.current = None
        self.tooltip.Hide()

    def Destroy(self):
        self.Hide()
        self.tooltip.Destroy()
        self.owner = None


class PanelSearch(ui.EditLine):
    def __init__(self, owner):
        ui.EditLine.__init__(self)
        self.page = owner

    def OnIMEUpdate(self):
        ui.EditLine.OnIMEUpdate(self)
        if self.page is not None:
            self.page.OnSearch()


class ButtonPanelPage(object):
    """Base of one tab: header, search, preview pool, icon groups, drag and tooltips."""

    TITLE = ''
    HELP = ''
    GROUP_PER_ROW = 8
    GROUP_LABEL_WIDTH = 0        # 0 = label above the row, otherwise inline label width
    GROUP_LEFT = 0
    SEARCH_POS = (0, 52)          # relative to the page top
    STATUS_POS = None             # (x, y) relative to the page top; None = below the groups
    SLOT_TIP_SIDE = 'left'        # preview tooltips sit outside the panel
    STATUS_WIDTH = 230

    def __init__(self, owner):
        self.owner = owner
        self.top = 0
        self.picker = None
        self.pending = None
        self.selected = None
        self.tip = None
        self.query = ''
        self._Reset()

    def _Reset(self):
        self.slots = {}          # slot key -> (button, mark)
        self.slot_homes = {}     # slot key -> (x, y) in content coordinates
        self.slot_actions = {}   # slot key -> action id or None ("+")
        self.icons = {}          # action id -> (button, mark)
        self.icon_homes = {}
        self.group_rects = {}    # group key -> (x, y, w, h)
        self.group_widgets = {}
        self.widgets = {}
        self.dragging = None
        self.badge_marks = {}    # id(button) -> [ImageBox, image]: crossed dot (badge off) or support dot
        self.tip_entries = None  # hover texts, rebuilt after Sync (not per frame)

    # Model hooks (subclasses) --------------------------------------------------
    def Label(self, action_id):
        raise NotImplementedError

    def Visuals(self, action_id):
        raise NotImplementedError

    def Mark(self, action_id):
        return ''

    def Known(self):
        raise NotImplementedError

    def Groups(self):
        """[(group key, label, [action ids])] in display order."""
        raise NotImplementedError

    def SlotLayout(self):
        """[(slot key, (x, y) content position, action id or None for "+")]."""
        raise NotImplementedError

    def BuildHeader(self, y):
        """Extra header controls; returns nothing."""

    def SyncHeader(self):
        pass

    def SlotTitle(self, key):
        return ''

    def OpenSlotPicker(self, key):
        raise NotImplementedError

    def DropOnSlot(self, source, key):
        raise NotImplementedError

    def DropOnGroup(self, source, group):
        raise NotImplementedError

    def SwapSlots(self, first, second):
        raise NotImplementedError

    def AddAction(self, action_id):
        raise NotImplementedError

    def IconClickAdds(self, action_id):
        return False

    def RestoreDefaults(self):
        raise NotImplementedError

    def Reload(self):
        raise NotImplementedError

    # Construction ----------------------------------------------------------------
    def Build(self, top=0):
        v = self.owner
        self.top = top
        self.pending = None
        self._Reset()
        self.Reload()
        self.widgets['title'] = v.text(self.TITLE, 0, top + 2, bold=True, width=150)
        self.widgets['count'] = v.text('', 0, top + 4, small=True, width=70, color=GOLD)
        help_button = v._keep(ui.Button(), 0, top)
        SetVisuals(help_button, PLACEHOLDER)
        help_mark = ui.TextLine()
        help_mark.SetParent(help_button)
        help_mark.SetPosition(ICON // 2, 7)
        help_mark.SetHorizontalAlignCenter()
        help_mark.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_SECTION))
        help_mark.SetFontColor(*INK)
        help_mark.AddFlag('not_pick')
        help_mark.SetText('?')
        help_mark.Show()
        self.widgets['help'] = help_button
        self.BuildHeader(top)
        sx, sy = self.SEARCH_POS
        field = v._keep(ui.ImageBox(), sx, top + sy)
        field.LoadImage(SEARCH_ART + 'search_input_normal.png')
        field.AddFlag('not_pick')
        search = v._keep(PanelSearch(self), sx + 6, top + sy + 3)
        search.SetSize(90, 16)
        search.SetMax(20)
        search.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
        search.SetInfoMessage(T('Hledat...', 'Search…'))
        search.SetEscapeEvent(getattr(v, 'OnPressEscapeKey', None))
        search.SetText(self.query)
        if hasattr(v, 'edit_lines'):
            v.edit_lines.append(search)
        self.widgets['search'] = search
        self.widgets['status'] = v.text('', 0, 0, small=True, width=self.STATUS_WIDTH, color=GOLD)
        for key, label, ids in self.Groups():
            text = v.text(label, 0, 0, small=True, bold=True, width=self.GROUP_LABEL_WIDTH or 120, color=GOLD)
            bar = v._bar(0, 0, 10, 10, GROUP_COLOR)
            empty = v.text(T('přetáhni sem', 'drop here'), 0, 0, small=True, width=120, color=MUTED)
            self.group_widgets[key] = (text, bar, empty)
        for action_id in self.Known():
            self._Icon(action_id)
        if self.tip is None:
            self.tip = HoverTip(v)
        self.Sync()
        return self.ContentBottom()

    def _DragArea(self):
        return (0, self.top, VIEW_WIDTH, 456 - self.top + 200)

    def _NewDragButton(self, x, y):
        v = self.owner
        button = v._keep(ui.DragButton(), x, y)
        button.SetRestrictMovementArea(*self._DragArea())
        mark = ui.TextLine()
        mark.SetParent(button)
        mark.SetPosition(ICON // 2, 6)
        mark.SetHorizontalAlignCenter()
        mark.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_SECTION))
        mark.SetFontColor(*INK)
        mark.AddFlag('not_pick')
        mark.Show()
        return button, mark

    def _Icon(self, action_id):
        if action_id not in self.icons:
            button, mark = self._NewDragButton(0, 0)
            button.SetMoveEvent(lambda selected=action_id: self._DragStart(('icon', selected)))
            button.SetEvent(lambda selected=action_id: self._Release(('icon', selected)))
            SetVisuals(button, self.Visuals(action_id))
            mark.SetText(self.Mark(action_id))
            # Right click: the per-button badge / state switches (root/uibuttonpanelbadges.py).
            _OnRightClick(button, self.OpenBadgeMenu, ('icon', action_id))
            self.icons[action_id] = (button, mark)
        return self.icons[action_id]

    def _Slot(self, key):
        if key not in self.slots:
            button, mark = self._NewDragButton(0, 0)
            button.SetMoveEvent(lambda selected=key: self._DragStart(('slot', selected)))
            button.SetEvent(lambda selected=key: self._Release(('slot', selected)))
            _OnRightClick(button, self.OpenBadgeMenu, ('slot', key))
            self.slots[key] = (button, mark)
        return self.slots[key]

    # Layout ----------------------------------------------------------------------
    def ContentBottom(self):
        return self.widgets.get('bottom', 456)

    def GroupsTop(self):
        raise NotImplementedError

    def Sync(self):
        if not self.widgets:
            return
        self.SyncHeader()
        self._SyncSlots()
        self._SyncGroups()
        self._SyncBadgeMarks()
        self.tip_entries = None

    def _SyncSlots(self):
        layout = self.SlotLayout()
        shown = set()
        self.slot_homes, self.slot_actions = {}, {}
        for key, (x, y), action_id in layout:
            button, mark = self._Slot(key)
            shown.add(key)
            self.slot_homes[key] = (x, y)
            self.slot_actions[key] = action_id
            if self.dragging != ('slot', key):
                button.SetPosition(x, y)
            if action_id is None:
                SetVisuals(button, PLACEHOLDER)
                mark.SetText('+')
                mark.SetFontColor(*INK)
            elif action_id == '':
                # An empty slot added with "+": click it to choose its function.
                visuals = list(PLACEHOLDER)
                if key == self.pending:
                    visuals[0] = visuals[1]
                SetVisuals(button, visuals)
                mark.SetText('')
            else:
                visuals = list(self.Visuals(action_id))
                if key == self.pending or action_id == self.selected:
                    visuals[0] = visuals[1]
                SetVisuals(button, visuals)
                mark.SetText(self.Mark(action_id))
            button.Show()
        for key, (button, mark) in self.slots.items():
            if key not in shown:
                button.Hide()

    def _Matches(self, action_id):
        if not self.query:
            return True
        query = Fold(self.query).strip()
        if not query or query in Fold(self.Label(action_id)) or query in Fold(action_id):
            return True
        import minimappanel
        return query in Fold(minimappanel.SearchAliases(action_id))

    def _SyncGroups(self):
        per_row = self.GROUP_PER_ROW
        label_width = self.GROUP_LABEL_WIDTH
        x0 = self.GROUP_LEFT
        y = self.GroupsTop()
        self.group_rects, self.icon_homes = {}, {}
        placed = set()
        for key, label, ids in self.Groups():
            text, bar, empty = self.group_widgets[key]
            ids = [action_id for action_id in ids if action_id in self.icons and self._Matches(action_id)]
            if label_width:
                text.SetPosition(x0, y + 8)
                gx, gy = x0 + label_width, y
            else:
                text.SetPosition(x0, y)
                gx, gy = x0, y + 14
            rows = max(1, int(math.ceil(len(ids) / float(per_row))))
            width, height = per_row * CELL, rows * CELL
            bar.SetPosition(gx - 1, gy - 1)
            bar.SetSize(width + 1, height + 1)
            self.group_rects[key] = (gx - 1, gy - 1, width + 2, height + 2)
            if ids:
                empty.Hide()
            else:
                empty.SetPosition(gx + 6, gy + 8)
                empty.Show()
            for index, action_id in enumerate(ids):
                button, mark = self.icons[action_id]
                home = (gx + (index % per_row) * CELL, gy + (index // per_row) * CELL)
                self.icon_homes[action_id] = home
                if self.dragging != ('icon', action_id):
                    button.SetPosition(*home)
                button.Show()
                placed.add(action_id)
            y = gy + height + GROUP_GAP
        for action_id, (button, mark) in self.icons.items():
            if action_id not in placed:
                button.Hide()
        if self.STATUS_POS is None:
            self.widgets['status'].SetPosition(x0, y + 2)
            y += 20
        else:
            self.widgets['status'].SetPosition(self.STATUS_POS[0], self.top + self.STATUS_POS[1])
        self.widgets['bottom'] = y

    # Badge switches (owner 2026-10-04) ---------------------------------------------
    def _BadgeMark(self, button, image):
        entry = self.badge_marks.get(id(button))
        if entry is None:
            mark = ui.ImageBox()
            mark.SetParent(button)
            mark.AddFlag('not_pick')
            entry = self.badge_marks[id(button)] = [mark, None]
        mark = entry[0]
        if entry[1] != image:
            entry[1] = image
            mark.LoadImage(image)
            mark.SetPosition(*((ICON - 9, -1) if image == BADGE_OFF else (ICON - 7, 1)))
        return mark

    def _SyncBadgeMarks(self):
        """A crossed grey dot on every icon whose badge the player turned off; a
        small quiet dot on the others that have a badge or a state (owner
        2026-10-04: show where the right click offers them)."""
        try:
            import buttonpanelbadges
            off = set(buttonpanelbadges.Load().off)
        except Exception:
            off = set()
        try:
            import uisettingsbuttonbadges
            supported = uisettingsbuttonbadges.IsSupported
        except Exception:
            supported = lambda unused: False
        targets = [(button, action_id) for action_id, (button, unused) in self.icons.items()]
        targets += [(self.slots[key][0], action_id) for key, action_id in self.slot_actions.items()
                    if key in self.slots]
        for button, action_id in targets:
            if action_id in off:
                self._BadgeMark(button, BADGE_OFF).Show()
            elif supported(action_id):
                self._BadgeMark(button, BADGE_SUPPORT).Show()
            elif id(button) in self.badge_marks:
                self.badge_marks[id(button)][0].Hide()

    def OpenBadgeMenu(self, source):
        kind, value = source
        action_id = value if kind == 'icon' else self.slot_actions.get(value)
        if not action_id or self.dragging is not None:
            return
        import uibuttonpanelbadges
        entries = uibuttonpanelbadges.ContextEntries(action_id)
        if not entries:
            return
        import uibuttonpanelcontext
        if getattr(self, 'badge_menu', None) is None:
            self.badge_menu = uibuttonpanelcontext.ContextMenu()
        button = self._SourceButton(source)
        (x, y) = button.GetGlobalPosition() if button is not None else (0, 0)
        wrapped = [(label, lambda run=callback: self._BadgeChanged(run)) for label, callback in entries]
        self.badge_menu.Open(wrapped, (x + ICON + 4, y))

    def _BadgeChanged(self, callback):
        callback()
        self._SyncBadgeMarks()

    # Hover tooltips --------------------------------------------------------------
    def OnUpdate(self):
        if self.tip is None or not self.widgets or self.dragging is not None:
            if self.tip is not None:
                self.tip.Hide()
            return
        # Labels read the shortcut table and the locale (audit 2.1): build them once
        # per Sync, the frame loop only tests IsIn.
        if self.tip_entries is None:
            self.tip_entries = self._TipEntries()
        self.tip.Update(self.tip_entries)

    def _TipEntries(self):
        entries = [(self.widgets.get('help'), self.HELP, 'above')] + list(self.ExtraTips())
        edge = self.SlotTipEdge()
        for key, (button, mark) in self.slots.items():
            action_id = self.slot_actions.get(key)
            text = self.Label(action_id) if action_id else self.SlotTitle(key)
            entries.append((button, text, self.SLOT_TIP_SIDE, edge))
        for action_id, (button, mark) in self.icons.items():
            entries.append((button, self.Label(action_id), 'above'))
        return entries

    def ExtraTips(self):
        """Extra (widget, text, side) hover tooltips of a tab."""
        return ()

    def SlotTipEdge(self):
        """Global x left of every preview slot: a slot tooltip never covers another slot."""
        xs = [x for (x, y) in self.slot_homes.values()]
        content = getattr(self.owner, 'content', None)
        if not xs or content is None or not hasattr(content, 'GetGlobalPosition'):
            return None
        return content.GetGlobalPosition()[0] + min(xs)

    # Search ------------------------------------------------------------------------
    def OnSearch(self):
        search = self.widgets.get('search')
        self.query = search.GetText() if search else ''
        self._SyncGroups()

    # Drag & click ------------------------------------------------------------------
    def _DragStart(self, source):
        if self.dragging is None:
            self.dragging = source
            button = self._SourceButton(source)
            if button is not None:
                button.SetTop()
            if self.tip is not None:
                self.tip.Hide()

    def _SourceButton(self, source):
        kind, key = source
        pair = (self.slots if kind == 'slot' else self.icons).get(key)
        return pair[0] if pair else None

    def _Home(self, source):
        kind, key = source
        return (self.slot_homes if kind == 'slot' else self.icon_homes).get(key)

    def _Release(self, source):
        button = self._SourceButton(source)
        home = self._Home(source)
        dragging, self.dragging = self.dragging, None
        if button is None or home is None:
            return
        x, y = button.GetLocalPosition()
        moved = abs(x - home[0]) + abs(y - home[1]) > DRAG_THRESHOLD
        button.SetPosition(*home)
        if dragging == source and moved:
            target = self.HitTest((x + ICON // 2, y + ICON // 2), source)
            if target is not None:
                self._ClosePicker()
                kind, key = target
                if kind == 'slot':
                    self.DropOnSlot(source, key)
                else:
                    self.DropOnGroup(source, key)
            else:
                self.Sync()
            return
        if source[0] == 'slot':
            self.OnClickSlot(source[1])
        else:
            self.OnClickIcon(source[1])

    def HitTest(self, point, source=None):
        px, py = point
        for key, (x, y) in self.slot_homes.items():
            if source == ('slot', key):
                continue
            if x - DROP_MARGIN <= px < x + ICON + DROP_MARGIN and y - DROP_MARGIN <= py < y + ICON + DROP_MARGIN:
                return ('slot', key)
        for key, (x, y, w, h) in self.group_rects.items():
            if x <= px < x + w and y <= py < y + h:
                return ('group', key)
        return None

    def IsPlusKey(self, key):
        return False

    def OnPlus(self, key):
        self.OpenSlotPicker(key)

    def OnClickSlot(self, key):
        if self.pending is None and self.IsPlusKey(key):
            self.OnPlus(key)
            return
        if self.pending is not None and self.pending != key:
            first = self.pending
            self._ClosePicker()
            self.SwapSlots(first, key)
            return
        if self.pending == key:
            self._ClosePicker()
            self.Sync()
            return
        self.pending = key
        action_id = self.slot_actions.get(key)
        if action_id:
            self.selected = action_id
        self.Sync()
        self.OpenSlotPicker(key)

    def OnClickIcon(self, action_id):
        self.selected = action_id
        if self.IconClickAdds(action_id):
            self.AddAction(action_id)
        else:
            self.Sync()

    # Picker --------------------------------------------------------------------
    def Picker(self):
        if self.picker is None:
            import uibuttonpanelpicker
            self.picker = uibuttonpanelpicker.FunctionPicker()
        return self.picker

    def PickerPosition(self):
        v = self.owner
        x, y = v.GetGlobalPosition() if hasattr(v, 'GetGlobalPosition') else (0, 0)
        width = v.GetWidth() if hasattr(v, 'GetWidth') else 616
        return (x + width + 4, y + 40)

    def PickerClosed(self):
        self.pending = None
        if self.widgets:
            self.Sync()

    def _ClosePicker(self):
        self.pending = None
        if self.picker is not None and self.picker.IsShow():
            self.picker.Close()

    def Status(self, text):
        if 'status' in self.widgets:
            self.widgets['status'].SetText(text)

    def Detach(self):
        """The page widgets are being cleared: drop references, close the picker."""
        self._Reset()
        self._ClosePicker()
        if self.tip is not None:
            self.tip.Hide()

    def Destroy(self):
        self.Detach()
        if getattr(self, 'badge_menu', None) is not None:
            self.badge_menu.Destroy()
            self.badge_menu = None
        if self.picker is not None:
            self.picker.Destroy()
            self.picker = None
        if self.tip is not None:
            self.tip.Destroy()
            self.tip = None
