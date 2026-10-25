# -*- coding: utf-8 -*-
"""Input of Settings v5 -> Panely tlačítek (2026-10-05, design v4.1): mixin of ``PanelsPage``.

* Drag and drop: a press on a function tile starts a drag after 4 px (``ui.Window`` mouse capture: the
  release always reaches the pressed tile). The ghost icon follows the mouse; the gold dashed frame shows the
  place where the function LANDS (places are packed like in game) and a small note says "Pusť: … / kruh 2,
  místo 3" (or what it replaces). Targets: the preview places, the rail page tabs 1-3, the rail columns and
  the minimap (= first free place), the catalogue sections (Kruh / Na liště = first free place, V menu Další,
  Skryto, Kanály). A click on a catalogue icon adds it to the first free place.
* Right click on a function: Odznak, Stav a odpočet (the per-function switches), Přesunout do Další / Přidat,
  Skrýt / Zobrazit v Další, Vrátit na výchozí místo.
* Hover tooltips (free place: "Volné místo – přetáhni sem funkci z katalogu"), "i" bubbles with a small preview,
  the reset dialog with the exact text and the 4-step guide (``tour_seen``).
"""
import buttonpanelsv5 as model
import inventoryrail as rail
import minimappanel as panel
from settingslocale import Text as Tr
from uisettingspanelsv5widgets import (Tip, ContextMenu, Bubble, ResetDialog, Ghost, TourBox, Outline, GlobalRect,
                                       Inside, Mouse, V5, Bar)

DRAG_THRESHOLD = 4
INFO_DELAY = 0.6      # s the mouse rests on a setting before its help bubble shows (never on a click)
_SESSION = {'tour_shown': False}


class DropMarker(object):
    """Gold dashed frame of the landing place, or a thin outline around a target area (float, not pickable)."""

    def __init__(self):
        import ui
        self.window = ui.Window()
        self.window.AddFlag('float')
        self.window.AddFlag('not_pick')
        self.image = ui.ExpandedImageBox()
        self.image.SetParent(self.window)
        self.image.AddFlag('not_pick')
        self.outline = Outline(self.window, alpha=1.0, thickness=2)

    def Frame(self, rect, size, scale):
        x, y, w, h = rect
        path = V5 + 'target_%d.png' % size
        side = int(round(size * scale))
        self.window.SetPosition(int(x + w // 2 - side // 2), int(y + h // 2 - side // 2))
        self.window.SetSize(side, side)
        self.image.LoadImage(path)
        self.image.SetScale(float(scale), float(scale))
        self.image.SetPosition(0, 0)
        self.image.Show()
        self.outline.Hide()
        self.window.Show()
        self.window.SetTop()

    def Area(self, rect):
        x, y, w, h = rect
        self.window.SetPosition(int(x), int(y))
        self.window.SetSize(int(w), int(h))
        self.image.Hide()
        self.outline.Set(0, 0, w, h)
        self.window.Show()
        self.window.SetTop()

    def Hide(self):
        self.window.Hide()

    def IsShow(self):
        return self.window.IsShow()


def _Now():
    try:
        import app
        return app.GetTime()
    except Exception:
        return 0.0


def _Inflate(rect, d):
    x, y, w, h = rect
    return x - d, y - d, w + 2 * d, h + 2 * d


def _Intersect(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    return (x0, y0, x1 - x0, y1 - y0) if x1 > x0 and y1 > y0 else None


class PanelsInput(object):
    def __init__(self):
        self.tip = self.menu = self.bubble = self.reset_dialog = self.ghost = self.marker = self.tour_box = None
        self.press = None
        self.dragging = False
        self.drop = None
        self.menu_action = None
        self.hover_tile = None
        self.tour_step = None
        self.tour_widgets = []
        self.decor = {}
        self.mini_tiles = []
        self.info_pending = None    # (key, InfoZone, time due) of the hover help
        self.info_quiet = None      # the group just clicked: no help until the mouse leaves it

    # ------------------------------------------------------------------ popups
    def _Tip(self):
        if self.tip is None:
            self.tip = Tip(self.kit)
        return self.tip

    def menu_open(self):
        return self.menu is not None and self.menu.IsShow()

    def HidePopups(self):
        for popup in (self.tip, self.ghost, self.marker):
            if popup is not None:
                popup.Hide()
        for popup in (self.menu, self.bubble):
            if popup is not None and popup.IsShow():
                popup.Close()
        if self.reset_dialog is not None and self.reset_dialog.IsShow():
            self.reset_dialog.Close()
        self.hover_tile = None

    def DestroyPopups(self):
        self.EndTour(mark=False)
        for popup in (self.tip, self.menu, self.bubble, self.reset_dialog, self.ghost, self.tour_box):
            if popup is not None:
                popup.Destroy() if hasattr(popup, 'Destroy') else popup.Hide()
        if self.marker is not None:
            self.marker.Hide()
        self.tip = self.menu = self.bubble = self.reset_dialog = self.ghost = self.marker = self.tour_box = None

    def OnPressEscapeKey(self):
        """Esc closes the page's own popups first (True = handled)."""
        if self.dragging:
            self.CancelDrag()
            return True
        if self.reset_dialog is not None and self.reset_dialog.IsShow():
            self.reset_dialog.Cancel()
            return True
        for popup in (self.menu, self.bubble):
            if popup is not None and popup.IsShow():
                popup.Close()
                return True
        if self.tour_step is not None:
            self.EndTour(mark=True)
            return True
        return False

    # ------------------------------------------------------------------ texts
    def PlaceText(self, tab, column, index):
        if tab == model.TAB_MINIMAP:
            if index < panel.RING_SIZES[0]:
                return Tr('kruh 1, místo %d', 'ring 1, place %d') % (index + 1)
            return Tr('kruh 2, místo %d', 'ring 2, place %d') % (index + 1 - panel.RING_SIZES[0])
        if self.rl_state.IsPages():
            return Tr('strana %d, místo %d', 'page %d, place %d') % (column + 1, index + 1)
        return Tr('%d. sloupec, místo %d', 'column %d, place %d') % (column + 1, index + 1)

    def WhereText(self, action):
        if self.tab == model.TAB_MINIMAP:
            state = self.mm_state
            slots = model.Pack(state.slots)
            if action in slots:
                return self.PlaceText(model.TAB_MINIMAP, 0, slots.index(action))
            hidden = state.Of(action) == panel.STATE_HIDDEN
        else:
            where = model.RailWhere(self.rl_state, action)
            if where is not None:
                return self.PlaceText(model.TAB_RAIL, where[0], where[1])
            hidden = self.rl_state.Of(action) == rail.STATE_HIDDEN
        return Tr('skryto', 'hidden') if hidden else Tr('v menu Další', 'in the More menu')

    def TileHover(self, tile, inside):
        if self.dragging:
            return
        if not inside:
            if self.hover_tile is tile and self.tip is not None:
                self.tip.Hide()
            self.hover_tile = None
            return
        self.hover_tile = tile
        side = 'above' if tile.source and tile.source[0].startswith('catalog') else 'left'
        if tile.action is None:
            title, body = Tr('Volné místo', 'Free place'), Tr('přetáhni sem funkci z katalogu',
                                                             'drag a function here from the catalogue')
        else:
            title = self.Label(tile.action)
            body = self.WhereText(tile.action)
            shortcut = self.Shortcut(tile.action)
            if shortcut:
                body = '%s | %s' % (body, shortcut)
        self._Tip().ShowAt(GlobalRect(tile), title, body, side)

    # ------------------------------------------------------------------ drag and drop
    def TilePress(self, tile):
        if self.menu_open():
            self.menu.Close()
        self.press = (tile, Mouse())
        self.dragging = False
        self.drop = None

    def TileRelease(self, tile):
        press, self.press = self.press, None
        dragging, drop = self.dragging, self.drop
        self.dragging = False
        self.drop = None
        if self.ghost is not None:
            self.ghost.Hide()
        if self.marker is not None:
            self.marker.Hide()
        if self.tip is not None:
            self.tip.Hide()
        if press is None or press[0] is not tile:
            return
        if dragging:
            if drop is not None:
                self.Drop(tile.action, drop)
            return
        self.ClickTile(tile)

    def CancelDrag(self):
        self.press = None
        self.dragging = False
        self.drop = None
        for popup in (self.ghost, self.marker):
            if popup is not None:
                popup.Hide()

    def _UpdateDrag(self):
        if self.press is None:
            return
        tile, (x0, y0) = self.press
        x, y = Mouse()
        if not self.dragging:
            if tile.action is None or abs(x - x0) + abs(y - y0) <= DRAG_THRESHOLD:
                return
            self.dragging = True
            if self.tip is not None:
                self.tip.Hide()
            if self.ghost is None:
                self.ghost = Ghost()
            import minimappanelicons
            self.ghost.Start(minimappanelicons.Visual(tile.action, 'normal'))
        self.ghost.Move(x, y)
        self._AutoScroll(x, y)
        self.drop = self.HitTest((x, y), tile.action)
        self._ShowDrop(tile.action, self.drop)

    def _AutoScroll(self, x, y):
        """While dragging, the catalogue scrolls when the cursor is at the top / bottom edge of the content (the
        wells further down are then reachable without the wheel)."""
        view = self._ViewRect()
        scrollbar = getattr(self.window, 'scrollbar', None)
        if view is None or scrollbar is None or not scrollbar.IsShow() or not view[0] <= x < view[0] + view[2]:
            return
        edge = 26
        if view[1] - 40 <= y < view[1] + edge:
            delta = 1
        elif view[1] + view[3] - edge <= y < view[1] + view[3] + 40:
            delta = -1
        else:
            return
        try:
            import app
            now = app.GetTime()
        except Exception:
            now = None
        if now is not None and now - getattr(self, '_scrolled_at', -1.0) < 0.08:
            return
        self._scrolled_at = now if now is not None else 0.0
        self.window.OnMouseWheel(delta)

    def _Targets(self):
        targets = []
        if self.tab == model.TAB_MINIMAP and self.mm_view is not None and self.mm_view.interactive:
            for index, tile in self.mm_view.Places():
                targets.append((('place', model.TAB_MINIMAP, 0, index), _Inflate(GlobalRect(tile), 3), tile))
            if self.focus is not None:
                targets.append((('strip', model.TAB_MINIMAP, 0), self._PreviewGlobal(self.focus), None))
        if self.tab == model.TAB_RAIL and self.rl_view is not None and self.rl_view.interactive:
            for (column, index), tile in self.rl_view.Places():
                targets.append((('place', model.TAB_RAIL, column, index), _Inflate(GlobalRect(tile), 2), tile))
            if self.page_tabs is not None:
                for page, cell in enumerate(self.page_tabs.cells):
                    targets.append((('page', page), _Inflate(GlobalRect(cell), 2), None))
            for column, rect in self.rl_view.rects:
                targets.append((('strip', model.TAB_RAIL, column), self._PreviewGlobal(rect), None))
        if self.catalog is not None:
            view = self._ViewRect()
            for key, rect in self.catalog.Rects().items():
                visible = _Intersect(rect, view) if view is not None else rect
                if visible is not None:
                    targets.append((('section', key), visible, None))
        return targets

    def _PreviewGlobal(self, rect):
        px, py = self.geo['preview_parent'].GetGlobalPosition()
        return rect[0] + px, rect[1] + py, rect[2], rect[3]

    def _ViewRect(self):
        view = self.geo.get('view')
        if not view:
            return None
        wx, wy = self.window.GetGlobalPosition()
        return view[0] + wx, view[1] + wy, view[2], view[3]

    def HitTest(self, point, action):
        for target, rect, tile in self._Targets():
            if Inside(rect, point):
                return self.Landing(target, action)
        return None

    def Landing(self, target, action):
        """Where ``action`` ends up for this target: dict(target, tab, column, index, replaced, swap, text) or
        None when nothing would change (full)."""
        kind = target[0]
        if kind in ('place', 'strip') and target[1] == model.TAB_MINIMAP:
            slots = list(model.Pack(self.mm_state.slots))
            moving = action in slots
            if moving:
                slots.remove(action)
            index = target[3] if kind == 'place' else len(slots)
            index = min(index, len(slots))
            replaced = None
            if not moving and len(slots) >= panel.MAX_SLOTS:
                if index >= len(slots):
                    return None
                replaced = slots[index]
            return dict(target=target, tab=model.TAB_MINIMAP, column=0, index=index, replaced=replaced, swap=None)
        if kind in ('place', 'strip'):
            lists = [list(ids) for ids in model.RailLists(self.rl_state)]
            column = target[2]
            where = model.RailWhere(self.rl_state, action)
            ids = lists[column]
            if where is not None and where[0] == column:
                ids.remove(action)
            index = target[3] if kind == 'place' else len(ids)
            index = min(index, len(ids))
            replaced = swap = None
            if len(ids) >= rail.MAX_PER_COLUMN and not (where is not None and where[0] == column):
                if index >= len(ids):
                    return None
                if where is not None:
                    swap = ids[index]
                else:
                    replaced = ids[index]
            return dict(target=target, tab=model.TAB_RAIL, column=column, index=index, replaced=replaced, swap=swap)
        if kind == 'page':
            return dict(target=target, tab=model.TAB_RAIL, column=target[1], index=None, replaced=None, swap=None)
        return dict(target=target, tab=self.tab, column=None, index=None, replaced=None, swap=None)

    def _LandingTile(self, drop):
        if drop['index'] is None:
            return None
        if drop['tab'] == model.TAB_MINIMAP and self.mm_view is not None:
            tiles = self.mm_view.tiles
            return tiles[drop['index']] if drop['index'] < len(tiles) else None
        if self.rl_view is not None:
            for (column, index), tile in self.rl_view.Places():
                if column == drop['column'] and index == drop['index']:
                    return tile
        return None

    def DropText(self, action, drop):
        target = drop['target']
        if target[0] == 'section':
            key = target[1]
            if key in ('menu', 'channels'):
                where = Tr('do menu Další', 'to the More menu')
            elif key == 'hidden':
                where = Tr('skrýt', 'hide')
            elif self.tab == model.TAB_MINIMAP:
                where = Tr('na první volné místo v kruzích', 'to the first free place in the rings')
            else:
                where = Tr('na první volné místo na liště', 'to the first free place on the rail')
        elif target[0] == 'page':
            where = Tr('na stranu %d', 'to page %d') % (target[1] + 1)
        else:
            where = self.PlaceText(drop['tab'], drop['column'], drop['index'])
            if drop['replaced']:
                where += Tr(' | nahradí: %s (půjde do Další)', ' · replaces: %s (goes to More)') % self.Label(
                    drop['replaced'])
            elif drop['swap']:
                where += Tr(' | prohodí se s: %s', ' · swaps with: %s') % self.Label(drop['swap'])
        return Tr('Pusť: %s', 'Drop: %s') % self.Label(action), where

    def _ShowDrop(self, action, drop):
        if drop is None:
            if self.marker is not None:
                self.marker.Hide()
            if self.tip is not None:
                self.tip.Hide()
            return
        if self.marker is None:
            self.marker = DropMarker()
        tile = self._LandingTile(drop)
        target = drop['target']
        if tile is not None:
            size = 43 if tile.kind == 'rail' else 34
            self.marker.Frame(GlobalRect(tile), size, tile.scale)
            anchor = GlobalRect(tile)
        else:
            rect = None
            for candidate, area, unused in self._Targets():
                if candidate == target:
                    rect = area
                    break
            if rect is None:
                self.marker.Hide()
                return
            self.marker.Area(rect)
            anchor = rect
        title, body = self.DropText(action, drop)
        self._Tip().ShowAt(anchor, title, body, 'left' if target[0] != 'section' else 'above')

    def Drop(self, action, drop):
        target = drop['target']
        kind = target[0]
        if kind in ('place', 'strip') and drop['tab'] == model.TAB_MINIMAP:
            state, replaced = model.MinimapPlace(self.mm_state, action, drop['index'])
            self.CommitMinimap(state, self._ReplacedText(replaced))
        elif kind in ('place', 'strip'):
            state, replaced = model.RailPlace(self.rl_state, action, drop['column'], drop['index'])
            self.CommitRail(state, self._ReplacedText(replaced))
        elif kind == 'page':
            state = rail.MoveToPage(model.RailPacked(self.rl_state), action, target[1])
            if state is None:
                self.SetStatus(Tr('Strana %d je plná (13).', 'Page %d is full (13).') % (target[1] + 1), error=True)
                return
            self.CommitRail(state, Tr('Přesunuto na stranu %d.', 'Moved to page %d.') % (target[1] + 1))
        else:
            self.DropOnSection(action, target[1])

    def _ReplacedText(self, replaced):
        if not replaced:
            return ''
        return Tr('Do menu Další přesunuto: %s.', 'Moved to the More menu: %s.') % self.Label(replaced)

    def DropOnSection(self, action, key):
        if key in ('ring1', 'ring2', 'rail'):
            self.AddToPanel(action)
        elif key == 'hidden':
            self.MoveOut(action, hide=True)
        else:
            self.MoveOut(action, hide=False)

    def AddToPanel(self, action):
        if self.tab == model.TAB_MINIMAP:
            if action in model.Pack(self.mm_state.slots):
                return
            state, replaced = model.MinimapAppend(self.mm_state, action)
            self.CommitMinimap(state)
        elif self.tab == model.TAB_RAIL:
            if model.RailWhere(self.rl_state, action) is not None:
                return
            state, replaced = model.RailAppend(self.rl_state, action, self.edit_page if self.rl_state.IsPages() else None)
            self.CommitRail(state)

    def MoveOut(self, action, hide=False):
        if self.tab == model.TAB_MINIMAP:
            self.CommitMinimap(model.MinimapRemove(self.mm_state, action, hide))
        elif self.tab == model.TAB_RAIL:
            self.CommitRail(model.RailRemove(self.rl_state, action, hide))

    def ToDefault(self, action):
        if self.tab == model.TAB_MINIMAP:
            state, replaced = model.MinimapToDefault(self.mm_state, action, self.mm_known)
            self.CommitMinimap(state, self._ReplacedText(replaced))
        elif self.tab == model.TAB_RAIL:
            state, replaced = model.RailToDefault(self.rl_state, action, self.rl_known)
            self.CommitRail(state, self._ReplacedText(replaced))

    def ClickTile(self, tile):
        """A click on a catalogue icon outside the panel adds it to the first free place (as on the A7 page)."""
        if tile.action is None or not tile.source or not tile.source[0].startswith('catalog'):
            return
        if self.tab in (model.TAB_MINIMAP, model.TAB_RAIL):
            self.AddToPanel(tile.action)

    # ------------------------------------------------------------------ right click
    def _DefaultDiffers(self, action):
        """"Vrátit na výchozí místo" only for a function whose default place is on the panel and that is not
        there now (for the others the default is the More menu, offered as "Přesunout do Další")."""
        if self.tab == model.TAB_MINIMAP:
            if model.MinimapDefaultIndex(action, self.mm_known) is None:
                return False
            state, unused = model.MinimapToDefault(self.mm_state, action, self.mm_known)
            return state is not None and model.MinimapPacked(state) != model.MinimapPacked(self.mm_state)
        if model.RailDefaultIndex(action, self.rl_known) is None:
            return False
        state, unused = model.RailToDefault(self.rl_state, action, self.rl_known)
        return state is not None and model.RailPacked(state) != model.RailPacked(self.rl_state)

    def ContextActions(self, action):
        if self.tab == model.TAB_MINIMAP:
            on_panel = action in model.Pack(self.mm_state.slots)
            hidden = self.mm_state.Of(action) == panel.STATE_HIDDEN
            add = Tr('Přidat do kruhů', 'Add to the rings')
        else:
            on_panel = model.RailWhere(self.rl_state, action) is not None
            hidden = self.rl_state.Of(action) == rail.STATE_HIDDEN
            add = Tr('Přidat na lištu', 'Add to the rail')
        actions = []
        if on_panel:
            actions.append((Tr('Přesunout do Další', 'Move to More'), lambda: self.MoveOut(action)))
        else:
            actions.append((add, lambda: self.AddToPanel(action)))
            if hidden:
                actions.append((Tr('Zobrazit v menu Další', 'Show in the More menu'), lambda: self.MoveOut(action)))
        if not hidden:
            actions.append((Tr('Skrýt', 'Hide'), lambda: self.MoveOut(action, hide=True)))
        if self._DefaultDiffers(action):
            actions.append((Tr('Vrátit na výchozí místo', 'Back to its default place'), lambda: self.ToDefault(action)))
        return actions

    def ContextToggles(self, action):
        try:
            import buttonpanelbadges as badges
            import buttonpanelstatus as status
            has_badge, has_state = status.Capabilities(action)
            settings = badges.Load()
        except Exception:
            return []
        toggles = []
        if has_badge:
            toggles.append((Tr('Odznak', 'Badge'), action not in settings.off, settings.enabled,
                            lambda: self.ToggleFunctionBadge(action, 'badge')))
        if has_state:
            toggles.append((Tr('Stav a odpočet', 'State and countdown'), action not in settings.state_off,
                            settings.state, lambda: self.ToggleFunctionBadge(action, 'state')))
        return toggles

    def TileContext(self, tile):
        if tile.action is None or self.dragging:
            return
        if self.tab not in (model.TAB_MINIMAP, model.TAB_RAIL):
            return
        if self.tip is not None:
            self.tip.Hide()
        if self.menu is None:
            self.menu = ContextMenu(self.kit)
        self.menu_action = tile.action
        self.menu_rect = GlobalRect(tile)
        self.menu.on_close = self._MenuClosed
        self.menu.Open(self.Label(tile.action), self.ContextToggles(tile.action), self.ContextActions(tile.action),
                       self.menu_rect)
        self.Sync()

    def _MenuClosed(self):
        self.menu_action = None
        if self.built:
            self.Sync()

    def ToggleFunctionBadge(self, action, kind):
        import buttonpanelbadges as badges
        settings = badges.Load()
        if kind == 'badge':
            settings.SetBadge(action, action in settings.off)
        else:
            settings.SetState(action, action in settings.state_off)
        if not badges.Save(settings):
            self.StoreError()
        self.BadgesChanged()
        if self.menu_open() and self.menu_action == action:
            self.menu.on_close = None
            self.menu.Close()
            self.menu.on_close = self._MenuClosed
            self.menu.Open(self.Label(action), self.ContextToggles(action), self.ContextActions(action),
                           self.menu_rect)

    # ------------------------------------------------------------------ badges on the tiles
    def _BadgeTiles(self):
        medallion, rail_tiles, minis = [], [], []
        if self.catalog is not None:
            # P1: the catalogue medallions are drawn scaled (TILE px); the full badge decor fits only 1:1 tiles.
            for unused, tile in self.catalog.Tiles():
                (medallion if tile.scale == 1.0 else minis).append(tile)
        for view in (self.mm_view, self.rl_view):
            if view is None:
                continue
            for unused, tile in view.Places():
                if tile.action is None:
                    continue
                if tile.scale == 1.0:
                    (rail_tiles if tile.kind == 'rail' else medallion).append(tile)
                else:
                    minis.append(tile)
        return medallion, rail_tiles, minis

    def SyncBadges(self):
        try:
            import uibuttonpanelbadges
            settings = uibuttonpanelbadges.Settings()
        except Exception:
            return
        medallion, rail_tiles, minis = self._BadgeTiles()
        off = set(settings.off)
        for tile in medallion + rail_tiles + minis:
            tile.SetBadgeOff(tile.action in off)
        try:
            for kind, tiles in (('medallion', medallion), ('rail', rail_tiles)):
                if kind not in self.decor:
                    self.decor[kind] = uibuttonpanelbadges.PanelBadges(kind)
                self.decor[kind].Sync([(tile, tile.action) for tile in tiles])
        except Exception:
            pass
        self.mini_tiles = minis

    def UpdateBadges(self):
        try:
            import uibuttonpanelbadges
            interface = self.Interface()
            for decor in self.decor.values():
                decor.Update(interface)
            if self.mini_tiles:
                shown = uibuttonpanelbadges.Evaluate(interface, [tile.action for tile in self.mini_tiles])
                for tile in self.mini_tiles:
                    tile.SetMini(shown.get(tile.action))
        except Exception:
            pass

    def DropBadges(self):
        for decor in self.decor.values():
            try:
                decor.Destroy()
            except Exception:
                pass
        self.decor = {}
        self.mini_tiles = []
        self.info_pending = None    # (key, InfoZone, time due) of the hover help

    def OnUpdate(self):
        if not self.built:
            return
        self._UpdateDrag()
        self._InfoTick()
        self.UpdateBadges()
        tile = self.hover_tile
        if tile is not None and not tile.IsShow() and self.tip is not None:
            self.tip.Hide()
            self.hover_tile = None

    def AttachTip(self, widget, title, body='', side='above'):
        """A hover tooltip on any page widget (page tabs, the rail ear); the widget's own hover still runs."""
        cls = type(widget)

        def over_in():
            cls.OnMouseOverIn(widget)
            if not self.dragging:
                self._Tip().ShowAt(GlobalRect(widget), title() if callable(title) else title,
                                   body() if callable(body) else body, side)

        def over_out():
            cls.OnMouseOverOut(widget)
            if self.tip is not None:
                self.tip.Hide()
        widget.OnMouseOverIn = over_in
        widget.OnMouseOverOut = over_out

    # ------------------------------------------------------------------ help bubbles (hover with a delay)
    def OpenInfo(self, key):
        """The help bubble of a setting (text + small preview) under its group. Not modal and not pickable: it never
        takes a click from the page; it goes away when the mouse leaves the group or a control is used."""
        import uisettingspanelsv5help as help_texts
        title, paragraphs, figure = help_texts.Info(self, key)
        if self.bubble is None:
            self.bubble = Bubble(self.kit, modal=False)
        anchor = next((d for d in self.info_dots if getattr(d, 'info_key', None) == key), None)
        rect = GlobalRect(anchor) if anchor is not None else (0, 0, 0, 0)
        self.bubble.Open(title, paragraphs, rect, figure, side='below')
        self.bubble.info_key = key

    def HoverInfo(self, key, anchor=None):
        """Start the help of ``key`` as if the mouse had just entered its group (it still has to stay there)."""
        if self.bubble is not None and self.bubble.IsShow() and getattr(self.bubble, 'info_key', None) == key:
            return
        zone = anchor if anchor is not None else next((d for d in self.info_dots if d.info_key == key), None)
        self.info_pending = (key, zone, _Now() + INFO_DELAY)

    def CloseInfo(self):
        self.info_pending = None
        if self.bubble is not None and self.bubble.IsShow():
            self.bubble.Close()

    def _InfoZoneAt(self, mouse):
        """The setting group under the mouse (InfoZone rectangles, polled - no window lies over a control); None
        while a popup, the guide or a drag owns the mouse or the point is outside the visible content."""
        if self.dragging:
            return None
        for popup in (self.menu, self.reset_dialog, self.tour_box):
            if popup is not None and popup.IsShow():
                return None
        clip = getattr(self.window, 'viewport', None)
        if clip is not None and not Inside(GlobalRect(clip), mouse):
            return None
        for zone in self.info_dots:
            if zone.IsShow() and Inside(GlobalRect(zone), mouse):
                return zone
        return None

    def _InfoTick(self):
        """Every frame (2026-10-06: help only after the mouse RESTS on a setting, never from a click): the
        group under the mouse starts its INFO_DELAY; the bubble closes when the mouse leaves its group. After a
        click the group stays quiet until the mouse leaves it."""
        zone = self._InfoZoneAt(Mouse())
        key = zone.info_key if zone is not None else None
        if key != self.info_quiet:
            self.info_quiet = None
        bubble_key = getattr(self.bubble, 'info_key', None) if self.bubble is not None and self.bubble.IsShow() else None
        if bubble_key is not None:
            if key != bubble_key:
                self.CloseInfo()
            return
        if key is None or key == self.info_quiet:
            self.info_pending = None
            return
        now = _Now()
        pending = self.info_pending
        if pending is None or pending[0] != key:
            self.info_pending = (key, zone, now + INFO_DELAY)
            return
        if now >= pending[2]:
            self.info_pending = None
            self.OpenInfo(key)

    # ------------------------------------------------------------------ reset
    def AskReset(self):
        import uisettingspanelsv5help as help_texts
        if self.reset_dialog is None:
            self.reset_dialog = ResetDialog(self.kit, Tr('Potvrzení', 'Confirm'), Tr('Obnovit', 'Reset'),
                                            Tr('Zrušit', 'Cancel'),
                                            ((model.SCOPE_TAB, Tr('Jen tuto záložku', 'This tab only')),
                                             (model.SCOPE_PAGE, Tr('Celou stránku', 'The whole page'))))
        self.reset_dialog.owner = self.window
        self.reset_dialog.Open(lambda scope: help_texts.ResetText(self, scope), self.RestoreDefaults, model.SCOPE_TAB)

    # ------------------------------------------------------------------ guide
    def MaybeStartTour(self):
        if self.tour_step is not None:
            self.ShowTourStep()
            return
        if _SESSION['tour_shown'] or self.ReadOnly() or self.tab == model.TAB_BADGES:
            return
        try:
            seen = model.TourSeen()
        except Exception:
            seen = True
        if seen:
            return
        _SESSION['tour_shown'] = True
        self.tour_step = 0
        self.ShowTourStep()

    def ShowTourStep(self):
        import uisettingspanelsv5help as help_texts
        self._ClearTour()
        steps = help_texts.TourSteps(self)
        if self.tour_step is None or self.tour_step >= len(steps):
            self.EndTour(mark=True)
            return
        title, paragraphs, holes, box, arrow = steps[self.tour_step]
        window = self.window
        wx, wy = window.GetGlobalPosition()
        local = [(x - wx, y - wy, w, h) for x, y, w, h in holes]
        for rect in model.Complement(window.GetWidth(), window.GetHeight(), local):
            # Pickable: outside the highlighted parts the window does not react while the guide is shown.
            bar = Bar(window, 0xFF000000, 0.62, pick=True)
            bar.SetPosition(rect[0], rect[1])
            bar.SetSize(rect[2], rect[3])
            bar.SetTop()
            self.tour_widgets.append(bar)
        for rect in local:
            outline = Outline(window, packed=0xFFDCB46E, alpha=1.0, thickness=2)
            outline.Set(*_Inflate(rect, 4))
            outline.SetTop()
            self.tour_widgets.extend(outline.Widgets())
        if arrow is not None:
            self.tour_widgets.extend(help_texts.Arrow(window, self.kit, (arrow[0] - wx, arrow[1] - wy),
                                                      (arrow[2] - wx, arrow[1] - wy)))
        if self.tour_box is None:
            self.tour_box = TourBox(self.kit, self.SkipTour, self.NextTourStep)
        last = self.tour_step == len(steps) - 1
        self.tour_box.ShowStep(title, paragraphs, self.tour_step, len(steps), Tr('Přeskočit', 'Skip'),
                               Tr('Hotovo', 'Done') if last else Tr('Další ›', 'Next ›'), box)

    def NextTourStep(self):
        if self.tour_step is None:
            return
        self.tour_step += 1
        self.ShowTourStep()

    def SkipTour(self):
        self.EndTour(mark=True)

    def _ClearTour(self):
        for widget in self.tour_widgets:
            widget.Hide()
        self.tour_widgets = []

    def EndTour(self, mark=True, keep_step=False):
        self._ClearTour()
        if self.tour_box is not None:
            self.tour_box.Hide()
        if not keep_step:
            was = self.tour_step is not None
            self.tour_step = None
            if mark and was:
                try:
                    model.MarkTourSeen()
                except Exception:
                    pass
