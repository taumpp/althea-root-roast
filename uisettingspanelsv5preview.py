# -*- coding: utf-8 -*-
"""Preview of Settings v5 -> Panely tlačítek (2026-10-05, design v4.1): "Náhled ve hře".

The same art and geometry as in game, at any scale:

* ``MinimapView`` - the minimap ring (frame.tga; the R1 ring, the R1 medallions and no arc in the R1 look, as the
  game's minimap draws them: uiminimapr1, minimap A2), both launcher rings at the ``_MINIMAP_LAUNCHER_ARCS``
  offsets of uiscript/minimap.py, their connectors clipped under the last shown launcher like in game, the
  fixed "More" control; in the editor every one of the 12 places is shown (free = dotted circle, in the R1 look
  the empty R1 medallion);
* ``RailView`` - the inventory rail like ``uitaskbar.ExpandedTaskBar.RePositionButton``: 42 px columns,
  37 px carriers with the 24 px rail icons, the "⋯" bar under column 1, the page switcher of the pages mode
  (plate left of the first / last row, or the bar instead of "⋯"), the column-2 ear or the arrow beside the
  cogwheel; in the editor every list is shown in full height (13 places, free = dotted circle); in the R1 look
  every place is the round minimap A2 button (free = the empty R1 medallion) on the R1 rail frames;
* ``Legend`` - the marks used in the previews.

Dimmed thumbnails (the panel edited on the other tab, the help bubbles) are static (not pickable).
"""
import ui

import uikit
import uikittokens as T
import inventoryrail as rail
import buttonpanelsv5 as model
from settingslocale import Text as Tr
from uisettingspanelsv5widgets import Image, Tile, V5, BADGE_ART, VipTag, SmallFont, FreeLegend, R1Medallions

FRAME = 'd:/ymir work/ui/public/crimson/windows/minimap/frame.tga'
ORBIT = 'd:/ymir work/ui/game/crimson_ember/minimap/launcher_orbit.png'
PANEL_ART = 'd:/ymir work/ui/game/crimson_ember/minimap_panel/'
RAIL_ART = 'd:/ymir work/ui/game/crimson_ember/inventory/'
RAIL_ART_R1 = 'd:/ymir work/ui/public/althea_r1_postava/inventory/'   # uiinventoryr1.RAIL_ART (the game's R1 rail)
# uiscript/uiscript/minimap.py _MINIMAP_LAUNCHER_ARCS (launcher top-left relative to the frame).
ARC = ((-15, 4), (-27, 33), (-32, 64), (-23, 94), (-4, 119),
       (-62, 4), (-72, 34), (-73, 65), (-67, 96), (-54, 124), (-33, 148), (-8, 167))
ORBIT_POS, ORBIT_HEIGHT = (-72, 0), 176
OUTER_POS, OUTER_HEIGHT = (-71, 10), 179
MORE_POS = (111, 50)
DISC_POS = (7, 8)
FRAME_W = 136
LEFT = 73                     # the leftmost launcher is 73 px left of the frame
MINIMAP_W, MINIMAP_H = LEFT + FRAME_W, 167 + 28

COLUMN_W, CARRIER, STEP, TOP = 42, 37, 41, 4
MORE_BAR_H = 12
EAR_W, PLATE_W, HEAD = 10, 13, 22


def RailArt():
    """The rail frames of the preview: with the round R1 places the recoloured copies the game's R1 rail uses
    (uiinventoryr1.RAIL_ART), today's otherwise."""
    return RAIL_ART_R1 if R1Medallions() else RAIL_ART


def MinimapSize(scale):
    return int(round(MINIMAP_W * scale)), int(round(MINIMAP_H * scale))


class MinimapView(object):
    def __init__(self, page, parent, interactive=True):
        self.page = page
        self.parent = parent
        self.interactive = interactive
        self.disc = Image.Make(parent, V5 + 'minimap_disc.png', 0, 0)
        self.orbit = Image.Make(parent, ORBIT, 0, 0)
        self.outer = Image.Make(parent, PANEL_ART + 'orbit_outer.png', 0, 0)
        self.frame = Image.Make(parent, FRAME, 0, 0)
        self.more = Image.Make(parent, PANEL_ART + 'more_normal.png', 0, 0)
        self.tiles = [Tile(page if interactive else None, parent, 'medallion') for unused in range(len(ARC))]
        self.more_hit = None
        if interactive and page is not None:
            self.more_hit = uikit.HitArea(parent, 0, 0, 22, 22)
            page.AttachTip(self.more_hit, Tr('Další', 'More'), Tr('ve hře otevře menu s ostatními funkcemi',
                                                                  'opens the menu with the other functions'), 'left')
        self.shown = []
        self.scale = 1.0

    def Widgets(self):
        return [self.disc, self.orbit, self.outer, self.frame, self.more] + list(self.tiles) + (
            [self.more_hit] if self.more_hit is not None else [])

    @staticmethod
    def Art():
        """The art of the game's minimap now: {part: (path, (x, y), height)}; in the R1 look the R1 ring, the R1
        "More" control and the arcs of ``minimappanelicons.R1_ARC`` (none: no arc), like uiminimapr1."""
        art = {'frame': (FRAME, (0, 0), 0), 'more': (PANEL_ART + 'more_normal.png', MORE_POS, 0),
               'orbit': (ORBIT, ORBIT_POS, ORBIT_HEIGHT), 'outer': (PANEL_ART + 'orbit_outer.png', OUTER_POS, OUTER_HEIGHT)}
        try:
            import minimappanelicons as icons
            frame, more = icons.R1Art('frame.png'), icons.R1Art('control/more_normal.png')
        except Exception:
            return art
        if not (frame and more):
            return art
        art['frame'] = (frame, (0, 0), 0)
        art['more'] = (more, MORE_POS, 0)
        if icons.R1_ARC != 'edge':
            art['orbit'] = art['outer'] = None
            return art
        import uir1minimapaart as A
        for part, name in (('orbit', 'orbit/edge_ring1.png'), ('outer', 'orbit/edge_ring2.png')):
            art[part] = (A.ROOT + name, tuple(A.ORBITS[name]), A.SIZES[name][1])
        return art

    def Render(self, x, y, scale, slots, free=True, alpha=1.0, selected=None):
        """``slots`` packed functions (ring order); ``free`` shows the free places of all 12."""
        self.scale = s = scale
        ox, oy = x + LEFT * s, y
        art = self.Art()
        Image.Set(self.disc, V5 + 'minimap_disc.png', ox + DISC_POS[0] * s, oy + DISC_POS[1] * s, s, alpha)
        for image, part in ((self.orbit, 'orbit'), (self.outer, 'outer')):
            if art[part] is not None:
                path, (px, py), unused = art[part]
                Image.Set(image, path, ox + px * s, oy + py * s, s, alpha)
        path, unused, unused = art['frame']
        Image.Set(self.frame, path, ox, oy, s, alpha)
        path, (px, py), unused = art['more']
        Image.Set(self.more, path, ox + px * s, oy + py * s, s, alpha)
        if self.more_hit is not None:
            self.more_hit.SetPosition(int(round(ox + MORE_POS[0] * s)), int(round(oy + MORE_POS[1] * s)))
            self.more_hit.SetSize(int(round(22 * s)), int(round(22 * s)))
        slots = tuple(slots)[:len(ARC)]
        ring1 = min(len(slots), 5)
        ring2 = max(0, len(slots) - 5)
        for image, part, last in ((self.orbit, 'orbit', ARC[ring1 - 1][1] if ring1 >= 2 else None),
                                  (self.outer, 'outer', ARC[5 + ring2 - 1][1] if ring2 >= 2 else None)):
            if art[part] is None:
                image.Hide()                                  # R1: no arc between the launchers
            else:
                unused, (unused_x, top), height = art[part]
                self._Clip(image, top, height, last)
        self.shown = []
        for index, tile in enumerate(self.tiles):
            action = slots[index] if index < len(slots) else None
            if action is None and not free:
                tile.Hide()
                continue
            tile.Set(action, ('place', model.TAB_MINIMAP, 0, index), s, alpha, static=not self.interactive)
            tile.SetPosition(int(round(ox + ARC[index][0] * s)), int(round(oy + ARC[index][1] * s)))
            tile.SetSelected(selected is not None and action == selected)
            self.shown.append(tile)
        return MinimapSize(s)

    @staticmethod
    def _Clip(orbit, top, height, last_y):
        if last_y is None:
            orbit.Hide()
            return
        orbit.SetRenderingRect(0.0, 0.0, 0.0, float(last_y + 14 - top - height) / height)

    def Places(self):
        """[(index, tile)] of the shown places."""
        return [(tile.source[3], tile) for tile in self.shown]


class _Toggle(uikit.Interactive):
    """A small image control of the rail preview (ear / arrow beside the cogwheel): click = callback."""

    def __init__(self, parent):
        uikit.Interactive.__init__(self)
        self.SetParent(parent)
        self.image = Image.Make(self, None, 0, 0)
        self.stem = None
        self.scale = 1.0
        self.states = ('normal', 'over', 'down')

    def Set(self, stem, states, x, y, w, h, scale, alpha=1.0):
        self.stem, self.states, self.scale, self.alpha = stem, states, scale, alpha
        self.SetPosition(int(round(x)), int(round(y)))
        self.SetSize(int(round(w * scale)), int(round(h * scale)))
        self.paint()
        self.Show()

    def paint(self):
        if not self.stem:
            return
        state = self.states[2] if self.pressed else (self.states[1] if self.hovered else self.states[0])
        Image.Set(self.image, self.stem + state + '.png', 0, 0, self.scale, getattr(self, 'alpha', 1.0))


class RailView(object):
    """The inventory rail; ``Render`` lays it out with its RIGHT edge at ``right`` (column 1 is the column
    next to the inventory body, column 2 left of it)."""

    def __init__(self, page, parent, interactive=True):
        self.page = page
        self.parent = parent
        self.interactive = interactive
        self.strips = [Image.Make(parent, RAIL_ART + 'rail_background.png', 0, 0) for unused in range(2)]
        self.more = Image.Make(parent, RAIL_ART + 'rail_more_bar_normal.png', 0, 0)
        self.plate = [Image.Make(parent, None, 0, 0) for unused in range(3)]
        self.pagebar = [Image.Make(parent, None, 0, 0) for unused in range(3)]
        self.ear = _Toggle(parent)
        self.head = _Toggle(parent)
        self.more_hit = None
        if interactive and page is not None:
            self.more_hit = uikit.HitArea(parent, 0, 0, CARRIER, MORE_BAR_H)
            page.AttachTip(self.more_hit, Tr('„…“ = Další', '"…" = More'),
                           Tr('ve hře otevře menu s ostatními funkcemi', 'opens the menu with the other functions'),
                           'left')
        if interactive and page is not None:
            self.ear.SetEvent(page.ToggleCollapsed)
            self.head.SetEvent(page.ToggleCollapsed)
        else:
            self.ear.AddFlag('not_pick')
            self.head.AddFlag('not_pick')
        self.tiles = [[], []]
        self.shown = []
        self.rects = []
        self.scale = 1.0

    def Widgets(self):
        result = self.strips + [self.more] + self.plate + self.pagebar + [self.ear, self.head]
        if self.more_hit is not None:
            result.append(self.more_hit)
        for column in self.tiles:
            result.extend(column)
        return result

    def _Tile(self, column, row):
        tiles = self.tiles[column]
        while len(tiles) <= row:
            tiles.append(Tile(self.page if self.interactive else None, self.parent, 'rail'))
        return tiles[row]

    @staticmethod
    def Width(state, scale, editor=True):
        """Width of the rail at a scale (columns, ear / page plate)."""
        s = scale
        if state.IsPages():
            plate = PLATE_W if state.ShowsSwitch() and state.switch_style in (rail.SWITCH_TOP, rail.SWITCH_SIDE) else 0
            return int(round((COLUMN_W + plate) * s))
        second = editor or (state.HasSecond() and not state.collapsed)
        ear = EAR_W if state.HasSecond() and state.tab_style != rail.TAB_COG else 0
        head = HEAD + 2 if state.HasSecond() and state.tab_style == rail.TAB_COG else 0
        return int(round((COLUMN_W + (ear + COLUMN_W if second else 0) + head) * s))

    @staticmethod
    def Height(rows, scale, pitch=None):
        pitch = pitch or STEP * scale
        return int(round(TOP * scale + rows * pitch + (MORE_BAR_H + 2) * scale))

    def Render(self, right, y, scale, state, edit_page=None, editor=True, alpha=1.0, pitch=None, selected=None):
        """``editor``: every list in full height with free places; else what the game shows (packed)."""
        self.scale = s = scale
        pitch = pitch or STEP * s
        pages = state.IsPages()
        lists = model.RailLists(state)
        if pages:
            page = state.ActivePage() if edit_page is None else edit_page
            shown = [(page, lists[page] if page < len(lists) else ())]
        else:
            shown = [(0, lists[0])]
            if editor or (state.HasSecond() and not state.collapsed):
                shown.append((1, lists[1] if len(lists) > 1 else ()))
        switch = state.switch_style if pages and state.ShowsSwitch() else None
        col1 = right - COLUMN_W * s
        # Like in game (v5 fix 2026-10-05): the columns touch, the ear hangs on the outer edge (_Ear).
        xs = [col1, col1 - COLUMN_W * s]
        rows_fixed = None
        if switch in (rail.SWITCH_SIDE, rail.SWITCH_BOTTOM) and not editor:
            rows_fixed = max(len(lists[p]) for p in state.ContentPages() if p < len(lists))
        self.shown, self.rects = [], []
        bar_y = y + TOP * s
        for slot, (list_index, ids) in enumerate(shown):
            rows = rail.MAX_PER_COLUMN if editor else max(len(ids), rows_fixed or 0, 1 if slot == 0 else 0)
            x = xs[slot]
            height = TOP * s + rows * pitch + ((MORE_BAR_H + 2) * s if slot == 0 else 0)
            dim = alpha * (0.45 if slot == 1 and state.collapsed and not pages else 1.0)
            Image.Set(self.strips[slot], RailArt() + 'rail_background.png', x, y, 1.0, dim)
            self.strips[slot].SetScale(float(s), float(height) / 334.0)
            self.strips[slot]._v5scale = None
            for row in range(rows):
                action = ids[row] if row < len(ids) else None
                tile = self._Tile(slot, row)
                if action is None and not editor:
                    tile.Hide()
                    continue
                tile.Set(action, ('place', model.TAB_RAIL, list_index, row), s, dim, static=not self.interactive)
                tile.SetPosition(int(round(x + 2 * s)), int(round(y + TOP * s + row * pitch)))
                tile.SetSelected(selected is not None and action == selected)
                self.shown.append(tile)
            for tile in self.tiles[slot][rows:]:
                tile.Hide()
            self.rects.append((list_index, (int(round(x)), int(round(y)), int(round(COLUMN_W * s)), int(round(height)))))
            if slot == 0:
                bar_y = y + TOP * s + rows * pitch
        for slot in range(len(shown), 2):
            self.strips[slot].Hide()
            for tile in self.tiles[slot]:
                tile.Hide()
        if switch == rail.SWITCH_BOTTOM:
            self.more.Hide()
            if self.more_hit is not None:
                self.more_hit.Hide()
        else:
            Image.Set(self.more, RailArt() + 'rail_more_bar_normal.png', col1 + 2 * s, bar_y, s, alpha)
            if self.more_hit is not None:
                self.more_hit.SetPosition(int(round(col1 + 2 * s)), int(round(bar_y)))
                self.more_hit.SetSize(int(round(CARRIER * s)), int(round(MORE_BAR_H * s)))
                self.more_hit.Show()
        self._Switch(state, switch, col1, y, bar_y, s, alpha)
        self._Ear(state, pages, xs, y, pitch, s, alpha, len(shown))
        return self.rects

    def _Switch(self, state, switch, col1, y, bar_y, s, alpha):
        number = state.ActivePage() + 1
        if switch in (rail.SWITCH_TOP, rail.SWITCH_SIDE):
            top = y + TOP * s if switch == rail.SWITCH_TOP else bar_y + MORE_BAR_H * s - 37 * s
            for image, stem, dy in zip(self.plate, ('rail_page_up_normal.png', 'rail_page_num_%d.png' % number,
                                                    'rail_page_down_normal.png'), (0, 14, 23)):
                Image.Set(image, RailArt() + stem, col1 - PLATE_W * s, top + dy * s, s, alpha)
        else:
            for image in self.plate:
                image.Hide()
        if switch == rail.SWITCH_BOTTOM:
            for image, stem, dx in zip(self.pagebar, ('rail_pagebar_up_normal.png', 'rail_pagebar_num_%d.png' % number,
                                                      'rail_pagebar_down_normal.png'), (0, 13, 24)):
                Image.Set(image, RailArt() + stem, col1 + (2 + dx) * s, bar_y, s, alpha)
        else:
            for image in self.pagebar:
                image.Hide()

    def _Ear(self, state, pages, xs, y, pitch, s, alpha, columns=2):
        second = (not pages) and state.HasSecond()
        stem = 'expand' if state.collapsed else 'minimize'
        if second and state.tab_style == rail.TAB_COG:
            self.ear.Hide()
            self.head.Set(RailArt() + 'rail_head_%s_' % stem, ('normal', 'hover', 'pressed'),
                          xs[1] - (HEAD + 2) * s, y + TOP * s + 7 * s, HEAD, HEAD, s, alpha)
        elif second:
            self.head.Hide()
            row = state.TabRow()
            # On the outer edge of the outermost shown column: column 2 while it is shown, else column 1.
            self.ear.Set(RailArt() + 'rail_tab_%s_' % stem, ('normal', 'over', 'down'), xs[columns - 1] - EAR_W * s,
                         y + TOP * s + row * pitch, EAR_W, 37, s, alpha)
        else:
            self.ear.Hide()
            self.head.Hide()

    def Places(self):
        return [((tile.source[2], tile.source[3]), tile) for tile in self.shown]


# --------------------------------------------------------------------------- legend
LEGEND = (
    ('free', (Tr('Volné místo - přetáhni sem funkci', 'Free place – drop a function here'),
              Tr('Volné místo - přetáhni sem', 'Free place – drop here'), Tr('Volné místo', 'Free place'))),
    ('action', (Tr('Čeká na tebe akce', 'An action waits for you'), Tr('Čeká akce', 'Action waits'),
                Tr('Čeká akce', 'Action waits'))),
    ('info', (Tr('Běží nebo je nové', 'Running or new'), Tr('Běží / nové', 'Running / new'),
              Tr('Běží / nové', 'Running / new'))),
    ('count', (Tr('Kolik věcí čeká', 'How many wait'), Tr('Kolik čeká', 'How many wait'), Tr('Kolik čeká', 'How many'))),
    ('vip', (Tr('Jen s VIP', 'VIP only'), Tr('Jen s VIP', 'VIP only'), Tr('Jen s VIP', 'VIP only'))),
)


def LegendHeight(kit, entries=5):
    return kit.cell('Sb') + 8 + entries * (kit.cell('S') + (10 if kit.prof == '1080' else 6))


def Legend(parent, kit, x, y, width, free=True):
    """Title and the marks; the longest text variant that fits ``width``. Returns the widgets."""
    widgets = [uikit.Text(parent, Tr('Legenda', 'Legend'), x, y, kit.font('Sb'), T.GOLD, valign='top')]
    y += kit.cell('Sb') + 8
    pitch = kit.cell('S') + (10 if kit.prof == '1080' else 6)
    entries = [entry for entry in LEGEND if free or entry[0] != 'free']
    probe = ui.TextLine()
    probe.SetFontName(kit.font('S'))
    variant = 2
    for candidate in range(3):
        if all(_Fits(probe, texts[candidate], width - 26) for unused, texts in entries):
            variant = candidate
            break
    for key, texts in entries:
        cy = y + kit.cell('S') // 2
        if key == 'free':
            widgets.append(FreeLegend(parent, x - 1, cy - 10))
        elif key in ('action', 'info'):
            widgets.append(Image.Make(parent, BADGE_ART + 'dot_%s.png' % key, x + 4, cy - 5))
        elif key == 'count':
            widgets.append(Image.Make(parent, BADGE_ART + 'count_action_18.png', x + 1, cy - 9))
            widgets.append(uikit.Text(parent, '2', x + 10, cy, SmallFont(13), 0xFFF4DA9C, align='center'))
        else:
            widgets.extend(VipTag(parent, x - 1, cy - 5))
        widgets.append(uikit.Text(parent, texts[variant], x + 26, cy, kit.font('S'), T.INK_DIM))
        y += pitch
    for widget in widgets:
        widget.Show()
    return widgets


LEGEND_ROW = (('free', Tr('volné místo', 'free place')), ('action', Tr('čeká akce', 'action waits')),
              ('info', Tr('běží / nové', 'running / new')), ('count', Tr('kolik čeká', 'how many wait')))


def LegendRow(parent, kit, x, y, width):
    """The marks in ONE row under the catalogue (P1): free place, action waits, running / new, count.
    Returns (widgets, height)."""
    widgets = []
    cell = kit.cell('S')
    cy = y + max(cell, 20) // 2
    gap = 22 if kit.prof == '1080' else 14
    for key, text in LEGEND_ROW:
        if key == 'free':
            widgets.append(FreeLegend(parent, x - 1, cy - 10, 0.8))
            tx = x + 18
        elif key in ('action', 'info'):
            widgets.append(Image.Make(parent, BADGE_ART + 'dot_%s.png' % key, x + 2, cy - 5))
            tx = x + 16
        else:
            widgets.append(Image.Make(parent, BADGE_ART + 'count_action_18.png', x, cy - 9))
            widgets.append(uikit.Text(parent, '2', x + 9, cy, SmallFont(13), 0xFFF4DA9C, align='center'))
            tx = x + 24
        line = uikit.Text(parent, text, tx, cy, kit.font('S'), T.INK_DIM)
        widgets.append(line)
        x = tx + uikit.TextWidth(line) + gap
    for widget in widgets:
        widget.Show()
    return widgets, max(cell, 20)


def _Fits(probe, text, width):
    probe.SetText(text)
    return uikit.TextWidth(probe) <= width


def Caption(parent, kit, x, y, lines, align='left'):
    """The muted caption of a dimmed thumbnail ("Minimapa / upravíš na její záložce")."""
    widgets = []
    for line in lines:
        widgets.append(uikit.Text(parent, line, x, y, kit.font('S'), T.MUTED, align=align, valign='top'))
        y += kit.cell('S') + 2
    return widgets
