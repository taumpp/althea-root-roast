"""Configurable inventory shortcut rail: catalogue, columns, "More" state, storage.

The rail next to the inventory body (``uitaskbar.ExpandedTaskBar``) shows the
functions the player placed there, in one or two columns of at most
``MAX_PER_COLUMN`` buttons each (13 fit the 585 px inventory body; a 14th would
end below the window and, at 1024x768, over the taskbar). Column 1 is the
column next to the body (today's rail), column 2 sits outside it.

Every function has one of three states: on the rail (``columns``), in the
shared "More" menu (the default for every other function) or hidden. The
small "⋯" bar below column 1 opens the shared "More" window; it takes no
slot and is always shown (owner 2026-10-04: 13 buttons end at y 570, the
12 px bar at 582, inside the 585 px body). Without a stored section the rail is exactly today's twelve
buttons in today's order, in one column.

Two modes (owner 2026-10-04, chosen in Settings):

* ``pages`` (default): one column with up to three pages of 13 buttons, like
  the skillbar; a small page switcher (up, gold page number, down) appears
  only when more than one page has buttons, empty pages are skipped. The
  switcher sits left of the first row (``top``, default), left of the last
  row next to "⋯" (``side``) or replaces the "⋯" bar below the rail
  (``bottom``; "⋯" then moves above the rail beside the cogwheel). ``side``
  and ``bottom`` keep the rail as tall as its longest page, so the switcher
  never moves when the page changes. The mouse wheel over the rail flips pages
  (``wheel``, on by default).
* ``columns``: today's one or two columns, column 2 pushed in/out by an ear or
  an arrow beside the cogwheel (``tab_style``).

Both modes share the same lists: column 2 is page 2, so switching modes (and
the migration of a stored two-column rail to pages) never moves a button. Page
3 is kept while the columns mode is chosen; its functions are then offered in
the More window.

Storage: the ``inventory`` section of ``UserData/button-panels.json``
(``buttonpanelstore``, shared with the minimap panel), per PC, presentation
only; fields equal to their default are not written::

    {"columns": [["inventory.special", ...], ["system.mount", ...], [...]], "hidden": [...],
     "mode": "columns", "collapsed": true, "tab_style": "bottom",
     "page": 1, "switch_style": "side", "wheel": false}

The catalogue is the minimap panel catalogue (``minimappanel.Catalog``): the
same action IDs, labels and callbacks; the minimap and the rail never share
slots, only the IDs.
"""
import buttonpanelstore
import minimappanel

SECTION = 'inventory'
MAX_PER_COLUMN = 13
MAX_COLUMNS = 2
MAX_SLOTS = MAX_PER_COLUMN * MAX_COLUMNS
MAX_PAGES = 3
MAX_LISTS = max(MAX_COLUMNS, MAX_PAGES)
MODE_COLUMNS, MODE_PAGES = 'columns', 'pages'
MODES = (MODE_COLUMNS, MODE_PAGES)
# Where the page switcher sits (owner 2026-10-04): 'top' = left of the first row
# (default, where the column-2 ear is), 'side' = left of the last row next to "⋯",
# 'bottom' = instead of the "⋯" bar below the rail ("⋯" moves beside the cogwheel).
SWITCH_TOP, SWITCH_SIDE, SWITCH_BOTTOM = 'top', 'side', 'bottom'
SWITCH_STYLES = (SWITCH_TOP, SWITCH_SIDE, SWITCH_BOTTOM)
# An empty slot added with "+" in Settings (owner 2026-10-04): kept in the stored
# column so the player can fill it later; the in-game rail skips it.
EMPTY = ''
# How column 2 is pushed in/out (owner 2026-10-04, chosen in Settings):
# 'top' = ear next to the first row (default), 'bottom' = ear next to the last
# row of the shorter column, 'cog' = arrow button beside the cogwheel above.
# The ear hangs on the OUTER edge of the rail: on column 2 while it is out, on
# column 1 while it is pushed in; the columns touch (owner play test 2026-10-05:
# an ear between the columns stuck to column 1 and left a gap).
TAB_TOP, TAB_BOTTOM, TAB_COG = 'top', 'bottom', 'cog'
TAB_STYLES = (TAB_TOP, TAB_BOTTOM, TAB_COG)
STATE_RAIL, STATE_MENU, STATE_HIDDEN = 'rail', minimappanel.STATE_MENU, minimappanel.STATE_HIDDEN

# Today's rail (locale/locale/common/ui/expandedtaskbar.py button_specs), in order.
DEFAULT_IDS = (
    'inventory.special',
    'system.quick_equip',
    'inventory.dragon_soul',
    'system.biolog',
    'system.teleport',
    'system.pet',
    'system.shop_search',
    'system.switchbot',
    'system.talisman',
    'system.mission_books',
    'system.mount',
    'system.dew_craft',
)

# Catalogue functions that make no sense on the inventory rail.
EXCLUDED_IDS = frozenset((
    'inventory.normal',  # would close the window the rail belongs to
))


def Catalog(interface):
    """Panel functions offered for the rail (minimap catalogue minus exclusions)."""
    return [entry for entry in minimappanel.Catalog(interface) if entry.action_id not in EXCLUDED_IDS]


def KnownIds(catalog_ids, rail_ids=()):
    """Every ID the rail may show: the rail's own buttons and the catalogue.

    "More" is not a slot: the rail always has a small "⋯" bar below column 1
    that opens the More window.
    """
    known = []
    for action_id in tuple(rail_ids) + tuple(catalog_ids):
        if action_id not in known and action_id not in EXCLUDED_IDS:
            known.append(action_id)
    return tuple(known)


class RailState(object):
    """The rail lists (tuple of 1-3 tuples), the functions hidden from "More" and
    the layout options of both modes.

    ``columns`` holds the lists of both modes: columns 1-2 in the columns mode
    (a third list is kept, parked), pages 1-3 in the pages mode. The constructor
    defaults to the columns mode; ``DefaultState`` and a stored section without
    ``mode`` use pages.

    Owner 2026-10-04: collapsing never deletes; column 2 keeps its buttons and
    comes back exactly as it was. A collapsed column's functions are offered
    in the More window.
    """
    __slots__ = ('columns', 'hidden', 'collapsed', 'tab_style', 'mode', 'page', 'switch_style', 'wheel')

    def __init__(self, columns=((),), hidden=(), collapsed=False, tab_style=TAB_TOP, mode=MODE_COLUMNS,
                 page=0, switch_style=SWITCH_TOP, wheel=True):
        columns = tuple(tuple(column) for column in columns)[:MAX_LISTS] or ((),)
        self.columns = columns
        self.mode = mode if mode in MODES else MODE_PAGES
        shown = self.Slots()
        self.hidden = frozenset(action for action in hidden if action not in shown)
        self.collapsed = bool(collapsed) and self.HasSecond()
        self.tab_style = tab_style if tab_style in TAB_STYLES else TAB_TOP
        self.page = page if isinstance(page, int) and 0 <= page < MAX_PAGES else 0
        self.switch_style = switch_style if switch_style in SWITCH_STYLES else SWITCH_TOP
        self.wheel = wheel is not False

    def _Key(self):
        return (self.columns, self.hidden, self.collapsed, self.tab_style, self.mode, self.page,
                self.switch_style, self.wheel)

    def __eq__(self, other):
        return isinstance(other, RailState) and self._Key() == other._Key()

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'RailState(%r, %r, collapsed=%r, tab_style=%r, mode=%r, page=%r, switch_style=%r, wheel=%r)' % (
            self.columns, sorted(self.hidden), self.collapsed, self.tab_style, self.mode, self.page,
            self.switch_style, self.wheel)

    def Replace(self, **changes):
        """A copy with some fields changed (every operation keeps the other options)."""
        values = dict((name, getattr(self, name)) for name in self.__slots__)
        values.update(changes)
        return RailState(**values)

    def IsPages(self):
        return self.mode == MODE_PAGES

    def ListCount(self):
        """How many lists the mode uses: 2 columns or 3 pages."""
        return MAX_PAGES if self.IsPages() else MAX_COLUMNS

    def Lists(self):
        """The lists of the current mode (a parked third list is left out)."""
        return self.columns[:self.ListCount()]

    def HasSecond(self):
        """Column 2 has at least one function (what the game shows and the tab controls)."""
        return len(self.columns) > 1 and any(action != EMPTY for action in self.columns[1])

    def HasSecondColumn(self):
        """Column 2 exists in the editor (functions or empty slots)."""
        return len(self.columns) > 1 and bool(self.columns[1])

    def TabRow(self):
        """Row the ear sits beside: 0 ('top') or the last row of the shorter column ('bottom'),
        the same in both states so pushing in/out never makes the ear jump."""
        if not self.HasSecond():
            return 0
        first = len([a for a in self.columns[0] if a != EMPTY])
        second = len([a for a in self.columns[1] if a != EMPTY])
        return TabRowOf(self.tab_style, first, second)

    # Pages -----------------------------------------------------------------------
    def PageIds(self, page):
        return self.columns[page] if 0 <= page < len(self.columns) else ()

    def ContentPages(self):
        """Pages with at least one function (page 1 when the rail is empty)."""
        pages = [page for page in range(min(MAX_PAGES, len(self.columns)))
                 if any(action != EMPTY for action in self.columns[page])]
        return pages or [0]

    def ActivePage(self):
        """The shown page: the stored one, or the first page with functions when it is empty."""
        pages = self.ContentPages()
        return self.page if self.page in pages else pages[0]

    def ShowsSwitch(self):
        return self.IsPages() and len(self.ContentPages()) > 1

    def PageRows(self):
        """Buttons of the longest page (the fixed rail height of the 'side'/'bottom' switcher)."""
        return max(len([a for a in self.PageIds(page) if a != EMPTY]) for page in self.ContentPages())

    def VisibleColumns(self):
        """Columns shown in game: the active page; or column 1 plus column 2 when it has
        buttons and is pushed out."""
        if self.IsPages():
            return (self.PageIds(self.ActivePage()),)
        if self.HasSecond() and not self.collapsed:
            return self.columns[:2]
        return self.columns[:1]

    def Slots(self):
        """Assigned functions of the current mode (empty slots excluded)."""
        return tuple(action for column in self.Lists() for action in column if action != EMPTY)

    def ColumnCount(self):
        return len(self.columns)

    def Of(self, action_id):
        if action_id in self.Slots():
            return STATE_RAIL
        return STATE_HIDDEN if action_id in self.hidden else STATE_MENU

    def Where(self, action_id):
        """(column or page, index) of a function on the rail, or None."""
        if action_id == EMPTY:
            return None
        for column_index, column in enumerate(self.Lists()):
            if action_id in column:
                return column_index, column.index(action_id)
        return None


def TabRowOf(style, first, second):
    """Row of the column-2 ear for column lengths ``first`` / ``second`` (buttons the game shows): 0 for 'top'
    (and 'cog', which has no ear), the last row of the shorter column for 'bottom'."""
    if style != TAB_BOTTOM or not second:
        return 0
    return max(0, min(first, second) - 1)


def _normalize_columns(columns, known_ids, column_count=None):
    known = set(known_ids)
    if not isinstance(columns, (list, tuple)):
        return ((),)
    result, seen = [], set()
    for column in list(columns)[:MAX_LISTS]:
        kept = []
        if isinstance(column, (list, tuple)):
            for action_id in column:
                if action_id == EMPTY or (isinstance(action_id, str) and action_id in known and action_id not in seen):
                    if action_id != EMPTY:
                        seen.add(action_id)
                    kept.append(action_id)
                    if len(kept) >= MAX_PER_COLUMN:
                        break
        result.append(tuple(kept))
    if column_count is not None:
        result = (result + [()] * MAX_COLUMNS)[:max(1, min(MAX_COLUMNS, column_count))]
    return tuple(result) or ((),)


def DefaultState(known_ids):
    return RailState(_normalize_columns((DEFAULT_IDS,), known_ids), (), mode=MODE_PAGES)


def Normalize(state, known_ids):
    columns = _normalize_columns(state.columns, known_ids)
    hidden = [action for action in sorted(state.hidden) if action in set(known_ids)]
    return state.Replace(columns=columns, hidden=hidden)


def LoadState(known_ids, path=None):
    section = buttonpanelstore.ReadSection(SECTION, path)
    if not isinstance(section, dict) or not isinstance(section.get('columns'), list) or not section['columns']:
        return DefaultState(known_ids)
    columns = _normalize_columns(section['columns'], known_ids)
    if not any(a != EMPTY for c in columns for a in c) and any(section['columns']):
        # Only unknown/retired functions were saved: fall back to today's rail.
        return DefaultState(known_ids)
    hidden = section.get('hidden', [])
    hidden = [action for action in hidden if isinstance(action, str) and action in set(known_ids)] \
        if isinstance(hidden, list) else []
    # A section of the first rail versions has no mode: it becomes pages (column 2 = page 2).
    return RailState(columns, hidden, section.get('collapsed') is True, section.get('tab_style', TAB_TOP),
                     section.get('mode', MODE_PAGES), section.get('page', 0),
                     section.get('switch_style', SWITCH_TOP), section.get('wheel') is not False)


def SaveState(state, known_ids, path=None, forget_unavailable=False):
    """Persist a state; the default state removes the section (follow defaults).

    Functions stored earlier but not offered now stay stored in their column at
    their places unless ``forget_unavailable`` (Restore defaults), as on the minimap.
    A failed write keeps the old file; ``buttonpanelstore.LastError()`` says why.
    """
    result = Normalize(state, known_ids)
    stored = None if forget_unavailable else buttonpanelstore.ReadSection(SECTION, path)
    stored = stored if isinstance(stored, dict) else {}
    stored_columns = stored.get('columns') if isinstance(stored.get('columns'), list) else []
    columns = []
    for index in range(min(MAX_LISTS, max(len(result.columns), len(stored_columns)))):
        column = result.columns[index] if index < len(result.columns) else ()
        old = stored_columns[index] if index < len(stored_columns) else ()
        columns.append(buttonpanelstore.KeepUnavailable(column, old, known_ids))
    while len(columns) > len(result.columns) and not columns[-1]:
        columns.pop()
    kept_hidden = buttonpanelstore.Unavailable(stored.get('hidden'), known_ids)
    kept = sum(len(column) for column in columns) != sum(len(column) for column in result.columns)
    value = None if result == DefaultState(known_ids) and not kept and not kept_hidden else dict(
        columns=columns, hidden=sorted(set(result.hidden) | set(kept_hidden)))
    if value is not None and result.collapsed:
        value['collapsed'] = True
    if value is not None and result.tab_style != TAB_TOP:
        value['tab_style'] = result.tab_style
    if value is not None:
        for name, default in (('mode', MODE_PAGES), ('page', 0), ('switch_style', SWITCH_TOP), ('wheel', True)):
            if getattr(result, name) != default:
                value[name] = getattr(result, name)
    buttonpanelstore.WriteSection(SECTION, value, path)
    return result


def MenuIds(state, known_ids):
    """Functions of the "More" window, in catalogue order: the "More" state plus,
    while column 2 is pushed in, the buttons of that column (functions on other
    pages are one page away, not in More)."""
    pushed_in = set(state.columns[1]) if state.collapsed and not state.IsPages() else set()
    return tuple(action for action in known_ids
                 if state.Of(action) == STATE_MENU or action in pushed_in)


# Column count --------------------------------------------------------------------
def SplitHalves(ids):
    """Two columns from one order: the first half (rounded up) next to the body."""
    ids = tuple(ids)
    half = (len(ids) + 1) // 2
    return ids[:half], ids[half:]


def SetCollapsed(state, collapsed):
    """Push column 2 in or out; its buttons are kept either way."""
    return state.Replace(collapsed=collapsed)


def SetTabStyle(state, style):
    """Choose how column 2 is pushed in/out (Settings); nothing else changes."""
    return state.Replace(tab_style=style)


# Pages --------------------------------------------------------------------------------
def SetMode(state, mode):
    """Columns or pages; the lists stay as they are (column 2 = page 2)."""
    return state.Replace(mode=mode)


def SetSwitchStyle(state, style):
    return state.Replace(switch_style=style)


def SetWheel(state, wheel):
    return state.Replace(wheel=bool(wheel))


def SetPage(state, page):
    """Show (and, in Settings, edit) one page; an empty page shows the first page with functions."""
    return state.Replace(page=max(0, min(MAX_PAGES - 1, int(page))))


def FlipPage(state, step):
    """Previous (-1) / next (+1) page with functions, round the end."""
    pages = state.ContentPages()
    index = pages.index(state.ActivePage())
    return state.Replace(page=pages[(index + step) % len(pages)])


def MoveToPage(state, action, page):
    """Settings: an icon dropped on a page tab goes to that page (first empty slot, else
    the end). Returns None when that page is full."""
    if not 0 <= page < MAX_PAGES:
        return state
    columns = [[item for item in column if item != action] for column in state.columns]
    while len(columns) <= page:
        columns.append([])
    target = columns[page]
    if EMPTY in target:
        target[target.index(EMPTY)] = action
    elif len(target) < MAX_PER_COLUMN:
        target.append(action)
    else:
        return None
    hidden = set(state.hidden)
    hidden.discard(action)
    return state.Replace(columns=columns, hidden=hidden)


def Balance(state):
    """Columns mode: re-split the two columns into equal halves (a parked page 3 stays).
    Pages mode: unchanged."""
    if state.IsPages():
        return state
    columns = SplitHalves(state.Slots()[:MAX_SLOTS]) + tuple(state.columns[MAX_COLUMNS:])
    return state.Replace(columns=columns, collapsed=False)


# Slot operations (column, index) ----------------------------------------------------
def _With(state, columns, hidden=None):
    """New state from edited columns; a column 2 that just got its first button is shown."""
    was_empty = not state.HasSecond()
    new = state.Replace(columns=columns, hidden=state.hidden if hidden is None else hidden)
    if was_empty and new.HasSecond():
        new = new.Replace(collapsed=False)
    return new


def _columns(state, column=None):
    """Mutable columns; addressing a list the mode allows but that does not exist yet
    appends empty lists up to it."""
    columns = [list(column) for column in state.columns]
    if column is not None and len(columns) <= column < state.ListCount():
        while len(columns) <= column:
            columns.append([])
    return columns


def _Order(state, prefer):
    """Lists to fill: the preferred one (pages: the shown page) first, then in order."""
    count = state.ListCount()
    order = list(range(count))
    if prefer is None and state.IsPages():
        prefer = state.ActivePage()
    if prefer is not None and 0 <= prefer < count:
        order.remove(prefer)
        order.insert(0, prefer)
    return order


def AddToRail(state, action, prefer=None):
    """Put ``action`` into the first list with room (pages: the shown page first); a full
    single column gets a second column automatically (owner 2026-10-04). Returns None
    when every list of the mode is full."""
    if state.Of(action) == STATE_RAIL:
        return state
    columns = [[item for item in column if item != action] for column in state.columns]
    hidden = set(state.hidden)
    hidden.discard(action)
    for index in _Order(state, prefer):
        while len(columns) <= index:
            columns.append([])
        column = columns[index]
        if EMPTY in column:
            column[column.index(EMPTY)] = action
        elif len(column) < MAX_PER_COLUMN:
            column.append(action)
        else:
            continue
        result = _With(state, columns, hidden)
        return SetCollapsed(result, False) if index == 1 and not state.IsPages() else result
    return None


def AddEmpty(state, column):
    """Settings "+": append an empty slot to ``column`` (a page in the pages mode); in the
    columns mode a full column 1 gets a second column with the empty slot. Returns None
    when there is no room."""
    if not 0 <= column < state.ListCount():
        return None
    columns = _columns(state, column)
    if len(columns[column]) >= MAX_PER_COLUMN:
        if column == 0 and not state.IsPages() and not state.HasSecondColumn():
            columns = (columns + [[]])[:max(2, len(columns))]
            columns[1] = [EMPTY]
            return state.Replace(columns=columns, collapsed=False)
        return None
    columns[column].append(EMPTY)
    return state.Replace(columns=columns, collapsed=False if column == 1 else state.collapsed)


def AssignSlot(state, column, index, action):
    """Put ``action`` into (column, index); ``None`` empties the slot.

    A function already on the rail swaps places with the slot's function (or
    moves to the end of the target column when the target slot is empty).
    """
    columns = _columns(state, column)
    if not 0 <= column < len(columns):
        return state
    hidden = set(state.hidden)
    target = columns[column]
    if action is None:
        # A function slot becomes an empty slot; an empty slot is removed.
        if index < len(target):
            if target[index] == EMPTY:
                del target[index]
            else:
                target[index] = EMPTY
        return _With(state, columns, hidden)
    hidden.discard(action)
    where = state.Where(action)
    if where is not None and where[0] == column:
        source = where[1]
        if index < len(target):
            target[source], target[index] = target[index], target[source]
        else:
            target.append(target.pop(source))
        return _With(state, columns, hidden)
    if where is not None:
        source_column, source_index = where
        if index < len(target):
            columns[source_column][source_index], target[index] = target[index], action
        elif len(target) < MAX_PER_COLUMN:
            del columns[source_column][source_index]
            target.append(action)
        return _With(state, columns, hidden)
    if index < len(target):
        target[index] = action
    elif len(target) < MAX_PER_COLUMN:
        target.append(action)
    return _With(state, columns, hidden)


def SwapSlots(state, first, second):
    """Swap two (column, index) slots; an empty target moves the function to that column's end."""
    (c1, i1), (c2, i2) = first, second
    columns = _columns(state, max(c1, c2))
    if not (0 <= c1 < len(columns) and 0 <= c2 < len(columns)) or first == second:
        return state
    if c1 == c2:
        column = columns[c1]
        count = len(column)
        if i1 < count and i2 < count:
            column[i1], column[i2] = column[i2], column[i1]
        elif min(i1, i2) < count:
            column.append(column.pop(min(i1, i2)))
        return _With(state, columns)
    a_ok, b_ok = i1 < len(columns[c1]), i2 < len(columns[c2])
    if a_ok and b_ok:
        columns[c1][i1], columns[c2][i2] = columns[c2][i2], columns[c1][i1]
    elif a_ok and len(columns[c2]) < MAX_PER_COLUMN:
        columns[c2].append(columns[c1].pop(i1))
    elif b_ok and len(columns[c1]) < MAX_PER_COLUMN:
        columns[c1].append(columns[c2].pop(i2))
    return _With(state, columns)


def SetFunctionState(state, action, chosen):
    """Move one function to the rail (first free slot), the More menu or hidden."""
    if chosen == STATE_RAIL:
        return AddToRail(state, action)  # None when every list is full
    columns = _columns(state)
    hidden = set(state.hidden)
    columns = [[item for item in column if item != action] for column in columns]
    if chosen == STATE_HIDDEN:
        hidden.add(action)
    else:
        hidden.discard(action)
    return _With(state, columns, hidden)


# Default position of the Special inventory window ---------------------------------
# Its default right edge is SCREEN_WIDTH - 297; the second rail column starts at
# SCREEN_WIDTH - 299, so with two columns the window yields 4 px (owner 2026-10-04).
# The 10 px expand/collapse tab left of the rail adds 10 more (14 px) while column 2
# is pushed out; pushed in, the rail ends at SW - 267 and needs no shift.
SPECIAL_INVENTORY_SHIFT = 14


def SpecialInventoryShift(path=None):
    """Extra left offset of the Special inventory default position (0 or 14 px).

    Pages mode: one column plus the 13 px switcher ends at SW - 270, clear of the
    window's right edge at SW - 297, so it never needs a shift."""
    section = buttonpanelstore.ReadSection(SECTION, path)
    if not isinstance(section, dict) or section.get('mode', MODE_PAGES) != MODE_COLUMNS:
        return 0
    columns = section.get('columns')
    second = isinstance(columns, list) and len(columns) >= 2 and isinstance(columns[1], list) and columns[1]
    return SPECIAL_INVENTORY_SHIFT if second and section.get('collapsed') is not True else 0
