# -*- coding: utf-8 -*-
"""Catalogue of Settings v5 -> Panely tlačítek (2026-10-05, design v4.1): "Katalog funkcí".

A header ("Najít funkci…" search over the whole width) and the sections of one tab: the panel itself (Kruh 1 /
Kruh 2, or Na liště), V menu Další, Skryto and Kanály side by side. P1 (2026-10-06): the medallions of the
game icon set are drawn at TILE px - the size of the preview next to the catalogue ("když tu je tolik místa,
nemůžeš ty ikony udělat větší? Velikosti jako vedle?") - in a grid without frames; a section area is still the drop
target, only an empty one shows a faint outline with "přetáhni sem". The four retired systems are not in the
catalogue at all (keybindings.RETIRED_ACTION_IDS); a panel section ends with one free place while the panel has
room. The search folds Czech accents and also finds the channel aliases ("ch 2", "kanál").
"""
import math

import ui

import uikit
import uikittokens as T
import minimappanel
from settingslocale import Text as Tr
from uisettingspanelsv5widgets import Tile, Well

TILE = {'1080': 36, '768': 30}   # catalogue medallion (native art 28 px, drawn scaled like the preview next to it)
GAP = {'1080': 6, '768': 5}
PAD = 2
NATIVE = 28.0


def Pitch(kit):
    return TILE[kit.prof] + GAP[kit.prof]


def TileScale(kit):
    return TILE[kit.prof] / NATIVE


def Fold(text):
    return minimappanel.SearchText(text)


class SearchLine(ui.EditLine):
    def __init__(self, page):
        ui.EditLine.__init__(self)
        self.page = page

    def OnIMEUpdate(self):
        ui.EditLine.OnIMEUpdate(self)
        if self.page is not None:
            self.page.OnSearch(self.GetText())


class Catalog(object):
    """``sections``: [(key, label, note, ids, free_place, half[, empty text])] where half is None, 'left' or
    'right' (two sections side by side). The page owns the tiles' behaviour (``Tile`` -> page callbacks)."""

    def __init__(self, page, parent, kit, track):
        self.page = page
        self.parent = parent
        self.kit = kit
        self.track = track          # registers a widget with the settings window (cleared with the page)
        self.tiles = {}             # action -> Tile
        self.free = {}              # section key -> Tile (free place)
        self.parts = {}             # section key -> (label, note, well, empty text)
        self.rects = {}             # section key -> (x, y, w, h) in content coordinates
        self.search = None
        self.query = ''
        self.top = 0
        self.width = 0
        self.bottom = 0
        self.header_widgets = {}    # section key -> widget right-aligned in its heading (e.g. column 2 actions)

    def BuildHeader(self, y, width, title=None):
        """The "Najít funkci…" field over the whole width (P1; with a title: the title left and a shorter field):
        the v5 kit edit field (``uikit.EditField``) with the search icon."""
        k = self.kit
        sw = width if not title else (210 if k.prof == '1080' else 150)
        isz = 20
        search = SearchLine(self.page)
        field_class = getattr(uikit, 'SearchField', None)
        if field_class is not None:
            # The kit's one search field (2026-10-06): row font, centred placeholder, a small clear cross.
            field = self.track(field_class(self.parent, k, width - sw, y, sw, hint=Tr('Najít funkci...',
                                                                                    'Find a function…'),
                                           edit=search, max_len=24, on_clear=self._Cleared))
            bh = field.h
        else:   # c9 v4 kit: a dark plate with an EditLine over it
            bh = k.p('button_h')
            field = self.track(uikit.Button(self.parent, k, width - sw, y, sw, '', role='reset',
                                            event=lambda: search.SetFocus()))
            self.track(uikit.Icon(field, 'search', isz, 10, (field.h - isz) // 2), wheel=False)
            search.SetParent(self.parent)
            search.SetPosition(width - sw + isz + 18, y + (bh - k.cell('S')) // 2)
            search.SetSize(sw - isz - 30, k.cell('S') + 2)
            search.SetMax(24)
            search.SetFontName(k.font('S'))
            search.SetInfoMessage(Tr('Najít funkci...', 'Find a function…'))
            search.Show()
        if title:
            self.track(uikit.Text(self.parent, title, 0, y + bh // 2, k.font('S'), T.MUTED))
        search.SetText(self.query)
        window = getattr(self.page, 'window', None)
        escape = getattr(window, 'OnPressEscapeKey', None)
        if escape is not None:
            search.SetEscapeEvent(escape)
        if window is not None and hasattr(window, 'edit_lines'):
            window.edit_lines.append(search)
        self.track(search)
        self.search = search
        self.field = field
        return y + bh + (12 if k.prof == '1080' else 8)

    def _Cleared(self):
        if self.page is not None:
            self.page.OnSearch('')
            if self.search is not None:
                self.search.SetFocus()

    def Matches(self, action):
        query = Fold(self.query).strip()
        if not query:
            return True
        return (query in Fold(self.page.Label(action)) or query in Fold(action)
                or query in Fold(minimappanel.SearchAliases(action)))

    def Build(self, y, width, sections):
        self.top, self.width = y, width
        for section in sections:
            key = section[0]
            if key not in self.parts:
                label = self.track(uikit.Text(self.parent, '', 0, 0, self.kit.font('Sb'), T.GOLD, valign='top'))
                note = self.track(uikit.Text(self.parent, '', 0, 0, self.kit.font('S'), T.MUTED, align='right',
                                             valign='top'))
                well = Well(self.parent, plain=True)
                for widget in well.Widgets():
                    self.track(widget)
                empty = self.track(uikit.Text(self.parent, Tr('přetáhni sem', 'drop here'), 0, 0, self.kit.font('S'),
                                              T.MUTED))
                self.parts[key] = (label, note, well, empty)
        return self.Sync(sections)

    def _Tile(self, action):
        tile = self.tiles.get(action)
        if tile is None:
            tile = self.tiles[action] = self.track(Tile(self.page, self.parent, 'medallion'))
        return tile

    def Pitch(self):
        return Pitch(self.kit)

    def _Free(self, key):
        tile = self.free.get(key)
        if tile is None:
            tile = self.free[key] = self.track(Tile(self.page, self.parent, 'medallion'))
        return tile

    def Sync(self, sections):
        k = self.kit
        y = self.top
        shown, shown_free = set(), set()
        self.rects = {}
        row_bottom = y
        index = 0
        while index < len(sections):
            group = [sections[index]]
            if sections[index][5] == 'left' and index + 1 < len(sections) and sections[index + 1][5] == 'right':
                group.append(sections[index + 1])
            index += len(group)
            if len(group) == 2:
                left_w = self._LeftWidth(group)
                spans = ((0, left_w), (left_w + 24, self.width - left_w - 24))
            else:
                spans = ((0, self.width),)
            bottom = y
            for section, (x, w) in zip(group, spans):
                key, label, note, ids, free_place = section[:5]
                empty_text = section[6] if len(section) > 6 else None
                bottom = max(bottom, self._Section(key, label, note, ids, free_place, x, y, w, shown, shown_free,
                                                   empty_text))
            y = bottom + (12 if k.prof == '1080' else 8)
            row_bottom = bottom
        for action, tile in self.tiles.items():
            if action not in shown:
                tile.Hide()
        for key, tile in self.free.items():
            if key not in shown_free:
                tile.Hide()
        for key, parts in self.parts.items():
            if key not in self.rects:
                for widget in parts[:2] + (parts[3],):
                    widget.Hide()
                for widget in parts[2].Widgets():
                    widget.Hide()
        self.bottom = row_bottom
        return row_bottom

    def _LeftWidth(self, group):
        """Width of the left one of two sections side by side (Skryto | Kanály, Kruh 1 | Kruh 2): as many places
        as it needs (at least 4), never more than half."""
        k = self.kit
        pitch = Pitch(k)
        key, label, note, ids, free_place = group[0][:5]
        cells = max(4, len([a for a in ids if self.Matches(a)]) + (1 if free_place and not self.query else 0))
        return min(self.width // 2, max(int(self.width * 0.34), 2 * PAD + cells * pitch - GAP[k.prof]))

    def _Section(self, key, label, note, ids, free_place, x, y, w, shown, shown_free, empty_text=None):
        k = self.kit
        pitch, scale = Pitch(k), TileScale(k)
        label_line, note_line, well, empty = self.parts[key]
        visible = [action for action in ids if self.Matches(action)]
        label_line.SetText('%s (%d)' % (label, len(visible)))
        label_line.SetPosition(x, y)
        label_line.Show()
        extra = self.header_widgets.get(key)
        head_h = k.cell('Sb')
        if extra is not None:
            head_h = max(head_h, extra.h)
            extra.SetPosition(x + w - extra.Width(), y + (head_h - extra.h) // 2)
            label_line.SetPosition(x, y + (head_h - k.cell('Sb')) // 2)
            note_line.Hide()
        elif note:
            note_line.SetText(note)
            note_line.SetPosition(x + w, y)
            note_line.Show()
        else:
            note_line.Hide()
        wy = y + head_h + 6
        per_row = max(1, (w - 2 * PAD + GAP[k.prof]) // pitch)
        cells = len(visible) + (1 if free_place and not self.query else 0)
        rows = max(1, int(math.ceil(cells / float(per_row))))
        h = rows * pitch - GAP[k.prof] + 2 * PAD
        well.Set(x, wy, w, h, empty=not cells)
        self.rects[key] = (x, wy, w, h)
        for position, action in enumerate(visible):
            tile = self._Tile(action)
            tile.Set(action, ('catalog', key, position), scale)
            tile.SetPosition(x + PAD + (position % per_row) * pitch, wy + PAD + (position // per_row) * pitch)
            shown.add(action)
        if free_place and not self.query:
            position = len(visible)
            tile = self._Free(key)
            tile.Set(None, ('catalog_free', key, position), scale)
            tile.SetPosition(x + PAD + (position % per_row) * pitch, wy + PAD + (position // per_row) * pitch)
            shown_free.add(key)
        if not cells:
            empty.SetText(Tr('nic nenalezeno', 'nothing found') if self.query and ids else
                          (empty_text or Tr('přetáhni sem', 'drop here')))
            if uikit.TextWidth(empty) > w - 24:            # a narrow well (768): the short hint
                empty.SetText(Tr('přetáhni sem', 'drop here'))
            empty.SetPosition(x + 12, wy + h // 2)
            empty.Show()
        else:
            empty.Hide()
        return wy + h

    def Rects(self):
        """{section key: global rect} of the wells (drop targets)."""
        px, py = self.parent.GetGlobalPosition()
        return dict((key, (px + x, py + y, w, h)) for key, (x, y, w, h) in self.rects.items())

    def Tiles(self):
        return [(action, tile) for action, tile in self.tiles.items() if tile.IsShow()]

    def Detach(self):
        self.tiles, self.free, self.parts, self.rects = {}, {}, {}, {}
        if self.search is not None:
            self.search.page = None
        self.search = None
        self.page = None
