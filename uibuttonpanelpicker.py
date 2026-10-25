"""Shared function picker of the configurable button panels.

One small Crimson board with a search field and a grid of 28px medallions,
used in two modes by both panels (minimap and inventory rail):

* "More" (run): no query shows the functions in the "More" state; a click
  runs the function.
* "Pick for slot N": shows every function plus an optional "Empty slot"
  item; a click hands the choice back to the caller (assign/swap).

A query always searches every function by name, with or without Czech
diacritics. Each medallion's tooltip carries the name and, when bound, the
keyboard shortcut. Selecting closes the board; ESC closes it too. Opening never takes the
keyboard focus; a click into the search field does. The caller
supplies the items, so the picker knows nothing about a specific panel.
"""
import ui
import fontconfig
from settingslocale import Text as T

IMG = 'd:/ymir work/ui/game/crimson_ember/gameoption/'
EMPTY_ID = ''
COLUMNS = 6
CELL = 34
PAD_X, GRID_TOP = 14, 72
WIDTH = PAD_X * 2 + COLUMNS * CELL - 6
# Keep the board above the main taskbar (37 px, locale/common/ui/taskbar.py) with a gap.
BOTTOM_RESERVE = 40
INK = (.88, .85, .78)
DIM = (.68, .64, .58)


def _HintText(cell):
    """The hint of a cell: its name, or (name, status lines) for a function with a live state (the rated arena:
    buttonpanelstatus.HintBody)."""
    text = getattr(cell, 'panelTooltip', '')
    action_id = getattr(cell, 'panelActionId', None)
    if action_id:
        try:
            import buttonpanelstatus
            body = buttonpanelstatus.HintBody(action_id, buttonpanelstatus.Context(None))
        except Exception:
            body = None
        if body:
            return (text, body)
    return text


class PickerItem(object):
    __slots__ = ('action_id', 'label', 'tooltip', 'visuals', 'mark', 'search')

    def __init__(self, action_id, label, tooltip, visuals, mark='', search=''):
        self.action_id = action_id
        self.label = label
        self.tooltip = tooltip
        self.visuals = visuals  # (normal, hover, pressed)
        self.mark = mark
        self.search = search or label


def SearchText(text):
    """The one accent-insensitive search key of every panel (``minimappanel.SearchText``)."""
    import minimappanel
    return minimappanel.SearchText(text)


def Matches(item, query):
    query = SearchText(query).strip()
    return not query or query in SearchText(item.search) or query in SearchText(item.action_id)


class PickerSearch(ui.EditLine):
    def __init__(self, owner):
        ui.EditLine.__init__(self)
        self.owner = owner
        self.SetEscapeEvent(owner.Close)
        self.SetReturnEvent(owner.RunFirst)

    def OnIMEUpdate(self):
        ui.EditLine.OnIMEUpdate(self)
        self.owner.Refresh()


def _R1Begin(picker):
    """The R1 look (root/uir1picker.py) unless Settings -> "Starý vzhled" chose the original board; None also when the
    R1 runtime cannot load (the original board then stays as it is)."""
    try:
        import uir1picker
    except Exception:
        return None
    return uir1picker.Begin(picker)


class FunctionPicker(ui.BoardWithTitleBar):
    def __init__(self):
        self.items = []
        self.default_ids = ()
        self.empty_item = None
        self.on_select = None
        self.on_close = None
        self.cells = []
        self.shown = []
        self.badges = None
        self.badgeInterface = None
        self.r1 = None
        ui.BoardWithTitleBar.__init__(self)
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetCloseEvent(self.Close)
        self.r1 = _R1Begin(self)
        background = ui.ImageBox()
        background.SetParent(self)
        background.SetPosition(PAD_X - 2, 36)
        background.LoadImage(IMG + 'search_bg.tga')
        background.AddFlag('not_pick')
        background.Show()
        self.searchBackground = background
        search = PickerSearch(self)
        search.SetParent(self)
        search.SetPosition(PAD_X + 6, 40)
        search.SetSize(WIDTH - PAD_X * 2 - 16, 18)
        search.SetMax(30)
        search.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
        search.SetInfoMessage(T('Hledat funkci...', 'Search function…'))
        search.Show()
        self.search = search
        empty = ui.TextLine()
        empty.SetParent(self)
        empty.SetPosition(WIDTH // 2, GRID_TOP + 6)
        empty.SetHorizontalAlignCenter()
        empty.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
        empty.SetFontColor(*DIM)
        empty.AddFlag('not_pick')
        self.emptyText = empty
        self.SetSize(WIDTH, GRID_TOP + CELL + 14)
        if self.r1 is not None:
            import uir1picker
            self.r1 = uir1picker.Finish(self.r1, self.GetWidth(), self.GetHeight())

    def SetSize(self, width, height):
        ui.BoardWithTitleBar.SetSize(self, width, height)
        if getattr(self, 'r1', None) is not None:
            self.r1.Resize(width, height)

    def SetTitleName(self, title):
        ui.BoardWithTitleBar.SetTitleName(self, title)
        if getattr(self, 'r1', None) is not None:
            self.r1.SetTitle(title)

    def Destroy(self):
        self.Close()
        if getattr(self, 'tooltip', None) is not None:
            self.tooltip.Destroy()
            self.tooltip = None
        self.on_select = self.on_close = None
        if self.badges is not None:
            self.badges.Destroy()
        self.badges = self.badgeInterface = None
        self.items, self.cells = [], []
        self.search.owner = None
        if self.r1 is not None:
            self.r1.Destroy()
            self.r1 = None

    def _ToolTip(self):
        if getattr(self, 'tooltip', None) is None:
            import uibuttonpaneltooltip
            self.tooltip = uibuttonpaneltooltip.PanelToolTip()
        return self.tooltip

    def _Cell(self, index):
        while len(self.cells) <= index:
            button = ui.Button()
            button.SetParent(self)
            button.panelTooltip = ''
            if hasattr(button, 'SetShowToolTipEvent'):
                import uibuttonpaneltooltip
                from _weakref import proxy
                uibuttonpaneltooltip.Attach(button, self._ToolTip(),
                                            lambda cell=proxy(button): _HintText(cell), 'above')
            mark = ui.TextLine()
            mark.SetParent(self)
            mark.SetHorizontalAlignCenter()
            mark.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_SECTION))
            mark.SetFontColor(*INK)
            mark.AddFlag('not_pick')
            self.cells.append((button, mark))
        return self.cells[index]

    def Open(self, title, items, default_ids, on_select, position, empty_item=None, on_close=None,
             anchor_height=0):
        """Show ``items``; without a query only ``default_ids`` (None = all).

        ``position`` is the preferred top-left corner. The board is placed only
        after its final size is known (also on the first opening) and kept fully
        on screen above the taskbar; when it does not fit below, it opens upwards,
        its bottom aligned with the bottom of the anchor (``anchor_height``).
        """
        self.SetTitleName(title)
        self.items = list(items)
        self.default_ids = None if default_ids is None else tuple(default_ids)
        self.empty_item = empty_item
        self.on_select = on_select
        self.on_close = on_close
        self.requested = (int(position[0]), int(position[1]), max(0, int(anchor_height)))
        self.search.SetText('')
        self.Refresh()
        self.Show()
        self.SetTop()
        # No keyboard focus on open (audit 2.3): the board is often opened in
        # combat and a focused search field would swallow skill keys, F1-F4 and
        # WASD. A click into the field focuses it (native EditLine); Enter then
        # runs the first result.

    def Close(self):
        if getattr(self, 'tooltip', None) is not None:
            self.tooltip.Hide()
        was_open = self.IsShow()
        search = getattr(self, 'search', None)
        if search:
            # Only release our own focus: never take it from another edit line (chat).
            is_focus = getattr(search, 'IsFocus', None)
            if is_focus is None or is_focus():
                search.KillFocus()
        self.Hide()
        callback, self.on_close = self.on_close, None
        if was_open and callback:
            callback()
        return True

    def OnPressEscapeKey(self):
        return self.Close()

    def Refresh(self):
        query = self.search.GetText().strip()
        if query:
            shown = [item for item in self.items if Matches(item, query)]
        elif self.default_ids is None:
            shown = list(self.items)
        else:
            wanted = set(self.default_ids)
            shown = [item for item in self.items if item.action_id in wanted]
        if self.empty_item is not None and not query:
            shown = [self.empty_item] + shown
        self.shown = [item.action_id for item in shown]
        for index, item in enumerate(shown):
            button, mark = self._Cell(index)
            x = PAD_X + (index % COLUMNS) * CELL
            y = GRID_TOP + (index // COLUMNS) * CELL
            button.SetPosition(x, y)
            button.SetUpVisual(item.visuals[0])
            button.SetOverVisual(item.visuals[1])
            button.SetDownVisual(item.visuals[2])
            # One TOP_MOST tooltip above the cell (a per-button tooltip child would
            # be drawn under the neighbouring cells).
            button.panelTooltip = item.tooltip
            button.panelActionId = item.action_id
            button.SetEvent(lambda selected=item.action_id: self.Run(selected))
            mark.SetPosition(x + 14, y + 6)
            mark.SetText(item.mark)
            button.Show()
            mark.Show()
        for button, mark in self.cells[len(shown):]:
            button.Hide()
            mark.Hide()
        if self.badges is not None:
            self.badges.Sync([(self.cells[index][0], action_id) for index, action_id in enumerate(self.shown)])
        if shown:
            self.emptyText.Hide()
        else:
            self.emptyText.SetText(T('Nic nenalezeno', 'Nothing found') if query
                                   else T('Všechny funkce jsou na panelu', 'Every function is on the panel'))
            self.emptyText.Show()
        rows = max(1, (len(shown) + COLUMNS - 1) // COLUMNS)
        self.SetSize(WIDTH, GRID_TOP + rows * CELL + 10)
        self.Place()

    def Place(self):
        """Clamp the board to the screen above the taskbar (after every resize)."""
        requested = getattr(self, 'requested', None)
        if requested is None:
            return
        x, y, anchor_height = requested
        width, height = self.GetWidth(), self.GetHeight()
        try:
            import wndMgr
            screen_w, screen_h = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        except (ImportError, AttributeError):
            screen_w = screen_h = None
        if screen_h is not None:
            bottom = screen_h - BOTTOM_RESERVE
            if y + height > bottom and anchor_height:
                y = y + anchor_height - height  # open upwards from the anchor
            x = max(0, min(x, screen_w - width))
            y = max(0, min(y, bottom - height))
        self.SetPosition(max(0, x), max(0, y))

    def EnableBadges(self, interface):
        """Show badges and states on the cells (the in-game "More" board)."""
        from _weakref import proxy
        try:
            self.badgeInterface = proxy(interface) if interface is not None else None
        except TypeError:  # already a weak proxy (the minimap keeps one)
            self.badgeInterface = interface
        if self.badges is None:
            import uibuttonpanelbadges
            self.badges = uibuttonpanelbadges.PanelBadges('medallion')

    def OnUpdate(self):
        if self.badges is not None and self.IsShow():
            self.badges.Update(self.badgeInterface)

    def Run(self, action_id):
        callback = self.on_select
        self.on_select = None
        self.Close()
        if callback:
            callback(action_id or None)

    def RunFirst(self):
        for action_id in self.shown:
            if action_id:
                self.Run(action_id)
                return
