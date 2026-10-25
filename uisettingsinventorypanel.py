"""Inventory tab of Settings -> Panely tlačítek (owner review 2026-10-04).

Compact visual editor on the shared ``uibuttonpanelpage.ButtonPanelPage``:

* right edge: the rail preview, one strip per column (column 1 next to the
  inventory body on the right), only the assigned buttons plus one "+"; with
  one full column a dim "+" in the column-2 position adds the second column;
* left: title, count, "?" help, "1 sloupec / 2 sloupce / Vyrovnat", search
  and the icon groups "V liště / V menu Další / Skryto".

Mode row (owner 2026-10-04): "Sloupce" (today's one or two columns, the
"Šipka:" row chooses the column-2 control) or "Strany" (default: one column,
pages 1-3; the "Přepínač:" row places the page switcher, "Kolečko" turns the
mouse-wheel flipping on/off). In the pages mode the tabs "1 2 3" above the
preview choose the page that is edited and shown in game; dropping an icon or
a slot on a tab moves that function to the page.

Every change is saved at once (``inventoryrail`` / ``buttonpanelstore``) and
applied to the in-game rail. "Reset this page" restores today's twelve.
"""
import ui
import uicrimsoncontrols as crimson
import fontconfig
import inventoryrail as rail
import uiinventoryrailmenu as adapter
import buttonpanelsettings as panelsettings
from settingslocale import Text as T
from uibuttonpanelpage import ButtonPanelPage, CELL, VIEW_WIDTH, DIM as INK_DIM

RAIL_PATH = 'd:/ymir work/ui/game/crimson_ember/inventory/'
STRIP_WIDTH = 34
STRIP_STEP = 36
TAB_PATH = RAIL_PATH + 'rail_tab_'
TAB_HEIGHT = 37
GROUPS_TOP = 108
HEAD_PATH = RAIL_PATH + 'rail_head_'
STYLE_LABELS = (('top', ('Nahoře', 'Top')), ('bottom', ('Dole', 'Bottom')), ('cog', ('U kola', 'At cog')))
MODE_LABELS = ((rail.MODE_COLUMNS, ('Sloupce', 'Columns')), (rail.MODE_PAGES, ('Strany', 'Pages')))
SWITCH_LABELS = ((rail.SWITCH_BOTTOM, ('Dole', 'Below')), (rail.SWITCH_SIDE, ('Vedle ⋯', 'By ⋯')),
                 (rail.SWITCH_TOP, ('Nahoře', 'Top')))
PAGE_TAB = 28          # page tab step (26x24 buttons) above the preview
PAGE_TABS_HEIGHT = 26  # the preview strip starts below the tabs in the pages mode
PAGE_ART = RAIL_PATH + 'rail_page'


class InventoryPanelPage(ButtonPanelPage):
    TITLE = T('Lišta u inventáře', 'Inventory rail')
    HELP = T('Klik = výběr funkce | tah = prohození nebo stav | klik na ikonu dole = přidat | ve hře pravý klik',
             'Click = choose · drag = swap or state · click an icon below = add · in game: right click')
    GROUP_PER_ROW = 8
    GROUP_LABEL_WIDTH = 0
    SEARCH_POS = (0, 80)

    def __init__(self, owner):
        self.entries = {}
        self.known = ()
        self.state = rail.RailState()
        self.edit_page = 0
        ButtonPanelPage.__init__(self, owner)

    # Model ---------------------------------------------------------------------
    def _Interface(self):
        getter = getattr(getattr(self.owner, 'backend', None), 'interface', None)
        return getter() if callable(getter) else None

    def _RailNamedIds(self, interface):
        bar = getattr(interface, 'wndExpandedTaskBar', None) if interface is not None else None
        getter = getattr(bar, 'RailKnownIds', None)
        if callable(getter):
            try:
                return tuple(getter())
            except Exception:
                pass
        return rail.DEFAULT_IDS

    def Reload(self):
        interface = self._Interface()
        self.entries = adapter.Entries(interface)
        self.known = rail.KnownIds(tuple(self.entries), self._RailNamedIds(interface))
        self.state = rail.LoadState(self.known)
        self.edit_page = self.state.page

    def _Pages(self):
        return self.state.IsPages()

    def _StripTop(self):
        return self.top + (PAGE_TABS_HEIGHT if self._Pages() else 0)

    def Known(self):
        return tuple(a for a in self.known if a in self.entries)

    def Label(self, action_id):
        return adapter.Tooltip(self.entries, action_id) if action_id else ''

    def Visuals(self, action_id):
        import inventoryrailicons
        return inventoryrailicons.PickerVisuals(action_id)

    def Mark(self, action_id):
        import inventoryrailicons
        return inventoryrailicons.PickerMark(action_id)

    def Groups(self):
        known = self.Known()
        shown = self.state.Slots()
        return (('rail', T('V liště', 'On the rail'), [a for a in shown if a in known]),
                ('menu', T('V menu Další', 'In More'), [a for a in known if self.state.Of(a) == rail.STATE_MENU]),
                ('hidden', T('Skryto', 'Hidden'), [a for a in known if self.state.Of(a) == rail.STATE_HIDDEN]))

    def GroupsTop(self):
        return self.top + GROUPS_TOP

    def _StripX(self, column):
        """Like in game: column 1 at the right edge, column 2 right left of it (the columns touch), the ear
        (styles top/bottom) on the outer edge of column 2 (owner play test 2026-10-05)."""
        x = VIEW_WIDTH - STRIP_WIDTH - 2
        if column == 0:
            return x
        return x - STRIP_STEP

    def _EditorColumns(self):
        """Column 2 is edited whenever it has buttons, also while pushed in (columns mode)."""
        if self._Pages():
            return (self.state.PageIds(self.edit_page),)
        return self.state.columns[:2] if self.state.HasSecondColumn() else self.state.columns[:1]

    def SlotLayout(self):
        layout = []
        columns = self._EditorColumns()
        top = self._StripTop()
        for column, ids in enumerate(columns):
            x = self._StripX(column) + 3
            key_column = self.edit_page if self._Pages() else column
            for index, action_id in enumerate(ids):
                layout.append(((key_column, index), (x, top + 3 + index * CELL), action_id))
            if len(ids) < rail.MAX_PER_COLUMN:
                layout.append((('plus', key_column), (x, top + 3 + len(ids) * CELL), None))
        if self._Pages():
            return layout
        if len(columns) == 1 and len(columns[0]) >= rail.MAX_PER_COLUMN:
            # Full single column: a "+" in the column-2 position adds the second column.
            layout.append((('plus', 1), (self._StripX(1) + 3, self.top + 3), None))
        return layout

    def IsPlusKey(self, key):
        return key[0] == 'plus'

    def OnPlus(self, key):
        """"+" only adds an empty slot (or column 2 when column 1 is full); the player
        then clicks the new empty slot to choose its function (owner 2026-10-04)."""
        self._Commit(rail.AddEmpty(self.state, key[1]))

    def ExtraTips(self):
        tips = []
        modes = {rail.MODE_COLUMNS: T('Jeden nebo dva sloupce vedle sebe', 'One or two columns side by side'),
                 rail.MODE_PAGES: T('Jeden sloupec, strany 1-3 jako u lišty schopností',
                                    'One column, pages 1-3 like the skillbar')}
        for mode, button in self.widgets.get('modes', {}).items():
            tips.append((button, modes[mode], 'above'))
        if self._Pages():
            switches = {rail.SWITCH_BOTTOM: T('Přepínač stran pod lištou místo „⋯“ („⋯“ nad lištou u kola)',
                                              'Page switcher below the rail instead of "⋯" ("⋯" above it)'),
                        rail.SWITCH_SIDE: T('Přepínač stran vlevo u posledního řádku, vedle „⋯“',
                                            'Page switcher left of the last row, next to "⋯"'),
                        rail.SWITCH_TOP: T('Přepínač stran vlevo u prvního řádku (místo ouška)',
                                           'Page switcher left of the first row')}
            for style, button in self.widgets.get('switches', {}).items():
                tips.append((button, switches[style], 'above'))
            if self.widgets.get('wheel') is not None:
                tips.append((self.widgets['wheel'], T('Kolečko myši nad lištou přepíná strany',
                                                      'The mouse wheel over the rail flips pages'), 'above'))
            for page, button in enumerate(self.widgets.get('page_tabs', ())):
                tips.append((button, T('Strana %d - upravit a ukázat ve hře | přetáhni sem ikonu = přesun na stranu',
                                       'Page %d – edit and show in game · drop an icon here to move it')
                             % (page + 1), 'above'))
            return tuple(tips)
        if self.state.HasSecond():
            text = (T('Vysunout 2. sloupec', 'Show column 2') if self.state.collapsed
                    else T('Zasunout 2. sloupec', 'Hide column 2'))
            for key in ('tab', 'head'):
                if self.widgets.get(key) is not None:
                    tips.append((self.widgets[key], text, 'left'))
        names = {'top': T('Šipka u horního řádku 2. sloupce', 'Ear at the top row of column 2'),
                 'bottom': T('Šipka u spodního řádku kratšího sloupce', 'Ear at the bottom row of the shorter column'),
                 'cog': T('Šipka vedle ozubeného kola nad lištou', 'Arrow beside the cogwheel above the rail')}
        for style, button in self.widgets.get('styles', {}).items():
            tips.append((button, names[style], 'above'))
        return tuple(tips)

    def SlotTitle(self, key):
        if key[0] != 'plus' and key in self.slot_actions and self.slot_actions[key] == rail.EMPTY:
            return T('Prázdné místo - klikni a vyber funkci', 'Empty slot – click to choose')
        if key[0] == 'plus':
            if not self._Pages() and key[1] >= len(self._EditorColumns()):
                return T('Přidat 2. sloupec', 'Add a second column')
            return T('Přidat prázdné místo', 'Add an empty slot')
        return adapter.SlotTitle(key[0], key[1], self._Pages())

    # Header ----------------------------------------------------------------------
    def BuildHeader(self, top):
        v = self.owner
        self.widgets['count'].SetPosition(178, top + 4)
        self.widgets['help'].SetPosition(222, top - 3)
        # Column 2 is never deleted by hiding it (owner 2026-10-04): one button pushes it
        # in or out, exactly like the arrow tab next to the rail in game.
        self.widgets['modes'] = {}
        for index, (mode, label) in enumerate(MODE_LABELS):
            button = v._keep(ui.Button(), index * 63, top + 24)
            crimson.ApplyVisuals(button, '61x21')
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
            button.SetText(T(*label))
            button.SetEvent(lambda chosen=mode: self.SetMode(chosen))
            self.widgets['modes'][mode] = button
        # A checkbox, not a "Kolečko: ne" button (owner 2026-10-04: the button text read
        # like an action, the wheel ended up off and "did nothing" in game).
        wheel = v._keep(ui.Button(), 132, top + 28)
        wheel.SetEvent(self.ToggleWheel)
        self.widgets['wheel'] = wheel
        self.widgets['wheel_label'] = v.text(T('Kolečko myši přepíná strany', 'Mouse wheel flips pages'),
                                             152, top + 27, small=True, width=196, color=INK_DIM)
        self.widgets['switch_label'] = v.text(T('Přepínač:', 'Switcher:'), 0, top + 55, small=True, width=52,
                                              color=INK_DIM)
        self.widgets['switches'] = {}
        for index, (style, label) in enumerate(SWITCH_LABELS):
            button = v._keep(ui.Button(), 54 + index * 63, top + 52)
            crimson.ApplyVisuals(button, '61x21')
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
            button.SetText(T(*label))
            button.SetEvent(lambda chosen=style: self.SetSwitchStyle(chosen))
            self.widgets['switches'][style] = button
        self.widgets['page_tabs'] = []
        for page in range(rail.MAX_PAGES):
            button = v._keep(ui.Button(), VIEW_WIDTH - (rail.MAX_PAGES - page) * PAGE_TAB, top)
            crimson.ApplyVisuals(button, '26x24')
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
            button.SetText(str(page + 1))
            button.SetEvent(lambda chosen=page: self.SelectPage(chosen))
            self.widgets['page_tabs'].append(button)
        toggle = v._keep(ui.Button(), 130, top + 24)
        crimson.ApplyVisuals(toggle, '61x21')
        toggle.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
        toggle.SetEvent(self.ToggleCollapsed)
        self.widgets['toggle'] = toggle
        balance = v._keep(ui.Button(), 193, top + 24)
        crimson.ApplyVisuals(balance, '61x21')
        balance.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
        balance.SetText(T('Vyrovnat', 'Balance'))
        balance.SetEvent(self.Balance)
        self.widgets['balance'] = balance
        self.widgets['strips'] = []
        for column in range(rail.MAX_COLUMNS):
            strip = v._keep(ui.ExpandedImageBox(), self._StripX(column), top)
            strip.LoadImage(RAIL_PATH + 'rail_background.png')
            strip.AddFlag('not_pick')
            self.widgets['strips'].append(strip)
        # The in-game "⋯" bar below column 1 (opens More, takes no slot).
        more_bar = v._keep(ui.ExpandedImageBox(), self._StripX(0), top)
        more_bar.LoadImage(RAIL_PATH + 'rail_more_bar_normal.png')
        more_bar.SetScale(float(STRIP_WIDTH) / 37.0, 1.0)
        more_bar.AddFlag('not_pick')
        self.widgets['more_bar'] = more_bar
        # Page switcher preview (pages mode): the plate left of the strip, or the bar.
        self.widgets['plate'] = []
        for stem in ('_up_normal.png', '_num_1.png', '_down_normal.png'):
            image = v._keep(ui.ExpandedImageBox(), 0, top)
            image.LoadImage(PAGE_ART + stem)
            image.AddFlag('not_pick')
            self.widgets['plate'].append(image)
        self.widgets['pagebar'] = []
        for stem in ('bar_up_normal.png', 'bar_num_1.png', 'bar_down_normal.png'):
            image = v._keep(ui.ExpandedImageBox(), 0, top)
            image.LoadImage(PAGE_ART + stem)
            image.AddFlag('not_pick')
            self.widgets['pagebar'].append(image)
        tab = v._keep(ui.Button(), 0, top)
        tab.SetEvent(self.ToggleCollapsed)
        self.widgets['tab'] = tab
        head = v._keep(ui.Button(), 0, top)
        head.SetEvent(self.ToggleCollapsed)
        self.widgets['head'] = head
        # "Šipka": how column 2 is pushed in/out in game (owner 2026-10-04: A, B, D).
        self.widgets['style_label'] = v.text(T('Šipka:', 'Arrow:'), 0, top + 55, small=True, width=40,
                                             color=INK_DIM)
        self.widgets['styles'] = {}
        for index, (style, label) in enumerate(STYLE_LABELS):
            button = v._keep(ui.Button(), 40 + index * 63, top + 52)
            crimson.ApplyVisuals(button, '61x21')
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
            button.SetText(T(*label))
            button.SetEvent(lambda chosen=style: self.SetTabStyle(chosen))
            self.widgets['styles'][style] = button

    @staticmethod
    def _Toggle(widget, visible):
        if visible:
            widget.Show()
        else:
            widget.Hide()

    def _Select(self, buttons, chosen):
        for key, button in buttons.items():
            if key == chosen:
                button.Down()
            else:
                button.SetUp()

    def _SyncPages(self, pages, strip_top, bar_y):
        """Mode-specific controls, the page tabs and the switcher preview."""
        self._Select(self.widgets['modes'], self.state.mode)
        self._Toggle(self.widgets['wheel'], pages)
        self._Toggle(self.widgets['wheel_label'], pages)
        import uisettingsbuttonbadges
        uisettingsbuttonbadges.CheckVisuals(self.widgets['wheel'], self.state.wheel)
        self._Toggle(self.widgets['switch_label'], pages)
        self._Toggle(self.widgets['style_label'], not pages)
        for button in self.widgets['switches'].values():
            self._Toggle(button, pages)
        for button in self.widgets['styles'].values():
            self._Toggle(button, not pages)
        if pages:
            self._Select(self.widgets['switches'], self.state.switch_style)
        content = self.state.ContentPages()
        for page, button in enumerate(self.widgets['page_tabs']):
            self._Toggle(button, pages)
            if page == self.edit_page:
                button.Down()
            else:
                button.SetUp()
            button.SetText(str(page + 1) if page in content or page == self.edit_page else '·%d' % (page + 1))
        switch = self.state.switch_style if pages and self.state.ShowsSwitch() else None
        number = self.state.ActivePage() + 1
        plate, bar = self.widgets['plate'], self.widgets['pagebar']
        plate[1].LoadImage(PAGE_ART + '_num_%d.png' % number)
        bar[1].LoadImage(PAGE_ART + 'bar_num_%d.png' % number)
        x = self._StripX(0)
        if switch in (rail.SWITCH_TOP, rail.SWITCH_SIDE):
            y = strip_top + 3 if switch == rail.SWITCH_TOP else bar_y + 12 - 37
            for image, dy in zip(plate, (0, 14, 23)):
                image.SetPosition(x - 14, y + dy)
                image.Show()
        else:
            for image in plate:
                image.Hide()
        self._Toggle(self.widgets['more_bar'], switch != rail.SWITCH_BOTTOM)
        for image, dx in zip(bar, (0, 13, 24)):
            if switch == rail.SWITCH_BOTTOM:
                image.SetPosition(x + dx * STRIP_WIDTH // 37, bar_y)
                image.SetScale(float(STRIP_WIDTH) / 37.0, 1.0)
                image.Show()
            else:
                image.Hide()

    def SyncHeader(self):
        pages = self._Pages()
        count = len(self.state.Slots())
        second = self.state.HasSecond() and not pages
        columns = self._EditorColumns()
        strip_top = self._StripTop()
        limit = rail.MAX_PER_COLUMN * (rail.MAX_PAGES if pages else (2 if second else 1))
        self.widgets['count'].SetText('%d / %d' % (count, limit))
        toggle = self.widgets['toggle']
        if second:
            toggle.SetText(T('Vysunout', 'Show') if self.state.collapsed else T('Zasunout', 'Hide'))
            toggle.Show()
        else:
            toggle.Hide()
        balance = self.widgets['balance']
        balance.SetPosition(193 if second else 130, self.top + 24)
        self._Toggle(balance, count >= 2 and not pages)
        rows_fixed = None
        if pages and self.state.ShowsSwitch() and self.state.switch_style != rail.SWITCH_TOP:
            # Like in game: as tall as the longest page, so the switcher below never moves.
            rows_fixed = self.state.PageRows()
        bar_y = strip_top + 4
        for column, strip in enumerate(self.widgets['strips']):
            if column < len(columns):
                ids = columns[column]
                rows = len(ids) + (1 if len(ids) < rail.MAX_PER_COLUMN else 0)
                if column == 0 and rows_fixed is not None:
                    rows = max(rows, rows_fixed)
                height = 6 + rows * CELL + (14 if column == 0 else 0)
                if column == 0:
                    bar_y = strip_top + 4 + rows * CELL
                    self.widgets['more_bar'].SetPosition(self._StripX(0), bar_y)
                strip.SetPosition(self._StripX(column), strip_top)
                strip.SetScale(float(STRIP_WIDTH) / 42.0, float(height) / 334.0)
                if hasattr(strip, 'SetAlpha'):
                    strip.SetAlpha(0.45 if column == 1 and self.state.collapsed else 1.0)
                strip.Show()
            else:
                strip.Hide()
        self._SyncPages(pages, strip_top, bar_y)
        if not pages:
            self._Select(self.widgets['styles'], self.state.tab_style)
        tab, head = self.widgets['tab'], self.widgets['head']
        stem = 'expand' if self.state.collapsed else 'minimize'
        if second and self.state.tab_style == rail.TAB_COG:
            tab.Hide()
            head.SetUpVisual(HEAD_PATH + stem + '_normal.png')
            head.SetOverVisual(HEAD_PATH + stem + '_hover.png')
            head.SetDownVisual(HEAD_PATH + stem + '_pressed.png')
            # In game it sits beside the cogwheel above the rail; here left of column 2's top.
            head.SetPosition(self._StripX(1) - 24, self.top + 3 + 14 - 11)
            head.Show()
        elif second:
            head.Hide()
            tab.SetUpVisual(TAB_PATH + stem + '_normal.png')
            tab.SetOverVisual(TAB_PATH + stem + '_over.png')
            tab.SetDownVisual(TAB_PATH + stem + '_down.png')
            # Like in game: one button high, centred on its row of column 2
            # ("top" = first row, "bottom" = last row of the shorter column).
            row = self.state.TabRow()
            outer = self._StripX(1 if len(self._EditorColumns()) > 1 else 0)
            tab.SetPosition(outer - 11, self.top + 3 + row * CELL + 14 - TAB_HEIGHT // 2)
            tab.Show()
        else:
            tab.Hide()
            head.Hide()

    # Operations ------------------------------------------------------------------
    def _Commit(self, state, status='', forget_unavailable=False):
        if state is None:
            self.Status(T('Lišta je plná (3 x 13).', 'The rail is full (3 x 13).') if self._Pages()
                        else T('Lišta je plná (2 x 13).', 'The rail is full (2 x 13).'))
            self.Sync()
            return
        try:
            self.state = rail.SaveState(state, self.known, forget_unavailable=forget_unavailable)
            error = panelsettings.StoreErrorText()
        except (ValueError, TypeError):
            error = T('Nastavení lišty se nepodařilo uložit.', 'Could not save the rail settings.')
        if error:
            # Nothing was written: show what the game shows.
            self.state = rail.LoadState(self.known)
            status = error
        bar = getattr(self._Interface(), 'wndExpandedTaskBar', None)
        if bar and hasattr(bar, 'RefreshRail'):
            bar.RefreshRail()
        self.Status(status)
        self.Sync()

    def _Target(self, key):
        """(column, index) of a slot key; "+" means the end of its column."""
        if key[0] == 'plus':
            column = key[1]
            ids = self.state.columns[column] if column < self.state.ColumnCount() else ()
            return column, len(ids)
        return key

    def OpenSlotPicker(self, key):
        column, index = self._Target(key)
        adapter.OpenSlotPicker(self.Picker(), self.entries, self.known, column, index, self._Picked,
                               self.PickerPosition(), on_close=self.PickerClosed)

    def _Picked(self):
        self.state = rail.LoadState(self.known)
        bar = getattr(self._Interface(), 'wndExpandedTaskBar', None)
        if bar and hasattr(bar, 'RefreshRail'):
            bar.RefreshRail()
        self.Status(panelsettings.StoreErrorText())
        self.Sync()

    def SwapSlots(self, first, second):
        if first[0] == 'plus':
            first, second = second, first
        if first[0] == 'plus':
            self.Sync()
            return
        self._Commit(rail.SwapSlots(self.state, first, self._Target(second)))

    def DropOnSlot(self, source, key):
        kind, value = source
        if kind == 'slot':
            self.SwapSlots(value, key)
            return
        column, index = self._Target(key)
        self._Commit(rail.AssignSlot(self.state, column, index, value))

    def _SourceAction(self, source):
        kind, value = source
        return self.slot_actions.get(value) if kind == 'slot' else value

    def DropOnGroup(self, source, group):
        action_id = self._SourceAction(source)
        if not action_id:
            self.Sync()
            return
        if isinstance(group, tuple) and group[0] == 'page':
            state = rail.MoveToPage(self.state, action_id, group[1])
            if state is None:
                self.Status(T('Strana %d je plná (13).', 'Page %d is full (13).') % (group[1] + 1))
                self.Sync()
                return
            self._Commit(state, T('Přesunuto na stranu %d.', 'Moved to page %d.') % (group[1] + 1))
            return
        if group == 'rail':
            self.AddAction(action_id)
            return
        chosen = rail.STATE_HIDDEN if group == 'hidden' else rail.STATE_MENU
        self._Commit(rail.SetFunctionState(self.state, action_id, chosen))

    def IconClickAdds(self, action_id):
        return self.state.Of(action_id) != rail.STATE_RAIL

    def AddAction(self, action_id):
        if self.state.Of(action_id) == rail.STATE_RAIL:
            self.Sync()
            return
        self._Commit(rail.AddToRail(self.state, action_id, self.edit_page if self._Pages() else None))

    # Pages mode ------------------------------------------------------------------
    def SetMode(self, mode):
        self._ClosePicker()
        state = rail.SetMode(self.state, mode)
        if mode == rail.MODE_PAGES:
            self.edit_page = state.ActivePage()
            state = rail.SetPage(state, self.edit_page)
        self._Commit(state)

    def SetSwitchStyle(self, style):
        self._Commit(rail.SetSwitchStyle(self.state, style))

    def ToggleWheel(self):
        self._Commit(rail.SetWheel(self.state, not self.state.wheel))

    def SelectPage(self, page):
        """Edit this page; it is also the page shown in game (an empty page shows page 1)."""
        self._ClosePicker()
        self.edit_page = page
        self._Commit(rail.SetPage(self.state, page))

    def _PageTabRects(self):
        if not self._Pages():
            return ()
        return tuple((page, (VIEW_WIDTH - (rail.MAX_PAGES - page) * PAGE_TAB, self.top, 26, 24))
                     for page in range(rail.MAX_PAGES))

    def HitTest(self, point, source=None):
        """Page tabs are drop targets too: dropping a function there moves it to that page."""
        px, py = point
        for page, (x, y, w, h) in self._PageTabRects():
            if x - 2 <= px < x + w + 2 and y - 2 <= py < y + h + 2:
                return ('group', ('page', page))
        return ButtonPanelPage.HitTest(self, point, source)

    def SetTabStyle(self, style):
        self._Commit(rail.SetTabStyle(self.state, style))

    def ToggleCollapsed(self):
        """Push column 2 in or out; its buttons stay (owner 2026-10-04)."""
        if not self.state.HasSecond():
            self.Sync()
            return
        self._Commit(rail.SetCollapsed(self.state, not self.state.collapsed))

    def Balance(self):
        self._Commit(rail.Balance(self.state))

    def RestoreDefaults(self):
        self._ClosePicker()
        self.selected = None
        self._Commit(rail.DefaultState(self.known), forget_unavailable=True)
