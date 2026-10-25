# -*- coding: utf-8 -*-
"""Kaskáda "odkud bonus mám" v seznamu okna Bonusy (akordeon se skupinami, vzhled R1).

Klik na řádek bonusu rozbalí rozpad přímo POD řádkem (uicharacterdetailskit.BonusPanel ho vloží do seznamu, další
řádky se posunou dolů); druhý klik na řádek ho sbalí. Obsah je bonussources.Breakdown:

  skupina se zdroji   šipka (› sbalená, ∨ rozbalená), tučný název a tučný součet; klik rozbalí / sbalí. Každá
                      skupina vypadá stejně, i s jediným zdrojem (vlastník 13. 10.); časové zdroje (lektvar, rosa,
                      Buffi) mají vlastní skupinu „Efekty (dočasné)“
  položka             odsazený bílý název, šedá poznámka u hodnoty (vč. kamenů, absorpce šerpy, druh efektu, u
                      časového zdroje zbývající čas); najetí myší ukáže tooltip: předmět ve slotu (výbava, mount,
                      mazlíček, talisman) ze slotu, efekt z lišty efektů, jiný zdroj celý název a poznámku
  poznámky            šedě pod rozpadem (vzorec násobného řádku, chybějící serverová hodnota)

Ze začátku je rozbalená první skupina s více zdroji, jinak první skupina. Rozbalení se drží při obnově hodnot ze serveru.
"""
import ui

import bonussources
import uikit
import uir1
import uir1tokens as T

ROW_H = 22              # řádek kaskády (o něco nižší než řádek bonusu)
GROUP_X = 22            # odsazení skupin (pod textem řádku bonusu)
ENTRY_X = GROUP_X + 18  # odsazení položek
VALUE_X = 6             # hodnota zarovnaná vpravo, stejný sloupec jako řádky bonusů
VALUE_W = 44            # místo pro hodnotu
NOTE_GAP = 8
NOTE_MAX = 96           # nejširší poznámka
NOTE_H = 18
BOTTOM = 4


def EntryNote(entry, stones=False):
    """Šedá poznámka u položky."""
    if entry.kind == 'item':
        if entry.note:
            return entry.note
        return u'vč. kamenů' if stones else u''
    if entry.kind == 'stone':
        return u'kámen'
    if entry.kind == 'ledger':
        return u'absorpce, rarita'
    if entry.kind == 'residual':
        return u''
    return entry.detail or u''


def Items(entries):
    """Položky skupiny pro zobrazení: kámen se přičte k předmětu ve stejné buňce ("vč. kamenů")."""
    rows = []
    owners = {}
    for entry in entries:
        if entry.kind == 'stone' and entry.cell is not None and entry.cell in owners:
            row = owners[entry.cell]
            row[1] += entry.value
            row[2] = True
            continue
        row = [entry, entry.value, False]
        rows.append(row)
        if entry.kind == 'item' and entry.cell is not None:
            owners[entry.cell] = row
    return [(entry, value, EntryNote(entry, stones)) for entry, value, stones in rows]


class GroupHead(uikit.HitArea):
    """Řádek skupiny: šipka, tučný název, tučný součet; klik rozbalí nebo sbalí."""

    def __init__(self, parent, kit, w, key, title, value, expanded, event):
        uikit.HitArea.__init__(self, parent, 0, 0, w, ROW_H)
        self.key = key
        self.expanded = expanded
        self.callback = event
        self.band = uir1.Band(self, 0, 0, w, ROW_H)
        cs = T.CHEVRON
        self.chevron = uir1.Image(self, uir1.ChevronPath('down' if expanded else 'right'), GROUP_X - cs - 4,
                                  (ROW_H - cs) // 2)
        font = kit.font('text_sb')
        self.title = uir1.RowText(self, '', GROUP_X, ROW_H, font, T.IVORY)
        self.value = uir1.RowText(self, value, w - VALUE_X, ROW_H, font, T.IVORY, align='right')
        uir1.Fit(self.title, title, w - GROUP_X - VALUE_X - VALUE_W)
        self.paint()

    def paint(self):
        if not hasattr(self, 'band'):
            return
        self.band.SetState('hover' if self.hovered else 'normal')
        state = 'active' if self.hovered else 'normal'
        self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath('down' if self.expanded else 'right', state))


class ItemRow(uikit.HitArea):
    """Řádek zdroje s tooltipem při najetí myší: předmět ve výbavě (``cell``) tooltip ze slotu, jiný zdroj
    (``entry``: lektvar, rosa, Buffi ... tooltip z lišty efektů, jinak celý název a poznámka)."""

    def __init__(self, parent, w, y, cell=None, on_in=None, on_out=None, entry=None):
        uikit.HitArea.__init__(self, parent, 0, y, w, ROW_H)
        self.cell = cell
        self.entry = entry
        self.on_in, self.on_out = on_in, on_out
        self.band = uir1.Band(self, 0, 0, w, ROW_H)

    def _Source(self):
        return self.cell if self.cell is not None else self.entry

    def paint(self):
        if hasattr(self, 'band'):
            self.band.SetState('hover' if self.hovered and self._Source() is not None else 'normal')

    def OnMouseOverIn(self):
        uikit.HitArea.OnMouseOverIn(self)
        if self._Source() is not None and self.on_in:
            self.on_in(self._Source())

    def OnMouseOverOut(self):
        uikit.HitArea.OnMouseOverOut(self)
        if self._Source() is not None and self.on_out:
            self.on_out()


class Cascade(ui.Window):
    """Rozpad jednoho bonusu jako vnořené řádky v seznamu. ``on_resize()`` po změně výšky (rozbalení skupiny),
    ``wheel(delta)`` kolečko myši (posouvá seznam)."""

    def __init__(self, parent, kit, w, on_resize=None, wheel=None, item_in=None, item_out=None):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.kit = kit
        self.w = int(w)
        self.on_resize = on_resize
        self.wheel = wheel
        self.item_in, self.item_out = item_in, item_out
        self.expanded = None            # None = výchozí (první skupina s více zdroji)
        self.breakdown = None
        self.parts = []
        self.rows = []
        self.heads = []
        self.item_rows = []
        self.notes = []
        self.height = 0
        self.SetSize(self.w, 1)
        self.Hide()

    def OnMouseWheel(self, delta):
        return self.wheel(delta) if self.wheel else False

    def _Keep(self, widget):
        self.parts.append(widget)
        return widget

    def _Clear(self):
        for widget in self.parts:
            try:
                widget.Hide()
            except Exception:
                pass
        for head in self.heads:
            head.callback = None
        for row in getattr(self, 'rows', ()):
            row.on_in = row.on_out = None
        self.rows = []
        self.parts, self.heads, self.item_rows, self.notes = [], [], [], []

    def _Line(self, parent, text, x, role, color, width, align='left'):
        line = self._Keep(uir1.RowText(parent, '', x, ROW_H, self.kit.font(role), color, align=align))
        uir1.Fit(line, text, width)
        return line

    def _Item(self, y, x, name, note, value, percent, name_color=T.INK, cell=None, note_color=T.MUTED, entry=None):
        w = self.w
        row = self._Keep(ItemRow(self, w, y, cell, self.item_in, self.item_out, entry))
        row.SetWheelEvent(self.OnMouseWheel)
        self.rows.append(row)
        value_text = bonussources.Format(value, percent)
        value_line = self._Line(row, value_text, w - VALUE_X, 'text', T.IVORY if value else T.MUTED, VALUE_W, 'right')
        room = w - VALUE_X - VALUE_W - x
        note_line = None
        note_w = 0
        # Časový zdroj: zbývající čas hned za názvem (vlevo), mezera k hodnotě zůstane volná (vlastník 13. 10.).
        row.note_after_name = bool(note and getattr(entry, 'temporary', False))
        if row.note_after_name:          # název + čas smí jít až k hodnotě (skutečná šířka, ne celý sloupec)
            room = w - VALUE_X - uikit.TextWidth(value_line) - NOTE_GAP - x
        if note:
            note_room = min(NOTE_MAX, room // 2) if note_color == T.MUTED else room // 2
            note_line = self._Line(row, note, x if row.note_after_name else w - VALUE_X - VALUE_W - NOTE_GAP,
                                   'text_xs' if note_color == T.MUTED else 'text', note_color, note_room,
                                   'left' if row.note_after_name else 'right')
            note_w = uikit.TextWidth(note_line) + NOTE_GAP
        name_line = self._Line(row, name, x, 'text', name_color, room - note_w - 4)
        self._PlaceNote(row, name_line, note_line, x)
        self.item_rows.append((name_line, note_line, value_line, row))
        return name_line

    def _PlaceNote(self, row, name_line, note_line, x):
        # Poznámka časového zdroje stojí hned za (zkráceným) názvem, ne u hodnoty.
        if note_line is not None and getattr(row, 'note_after_name', False):
            note_line.SetPosition(x + uikit.TextWidth(name_line) + NOTE_GAP,
                                  uir1.CellTop(ROW_H, self.kit.font('text_xs')))

    def _Specs(self, breakdown, prefix=None):
        """Řádky kaskády jako data: ('head', klíč, název, hodnota, rozbaleno), ('item', x, název, poznámka, hodnota,
        buňka), ('note', text)."""
        percent = breakdown.percent
        specs = []
        components = getattr(breakdown, 'components', None)
        if components:
            for index, part in enumerate(components):
                specs.append(('note', part.title + ': ' + bonussources.Format(part.total, part.percent)))
                specs.extend(self._Specs(part, index))
            return specs
        for key, title, value, entries in breakdown.groups:
            if prefix is not None:
                key = (prefix, key)
            # Každá skupina má řádek se šipkou a součtem, i s jedinou položkou (vlastník 13. 10.).
            expanded = key in self.expanded
            specs.append(('head', key, title, bonussources.Format(value, percent), expanded))
            if expanded:
                for entry, amount, note in Items(entries):
                    specs.append(('item', ENTRY_X, entry.name, note, amount, entry.cell, T.MUTED, percent, entry))
        for text in (breakdown.formula, breakdown.note):
            if text:
                specs.append(('note', text))
        return specs

    @staticmethod
    def _Structure(specs):
        """Co určuje widgety; hodnoty, poznámky a časy se mění na místě."""
        result = []
        for spec in specs:
            if spec[0] == 'item':
                result.append(('item', spec[1], spec[2], spec[5], bool(spec[3]), bool(spec[4]), spec[6], spec[7]))
            elif spec[0] == 'head':
                result.append(('head', spec[1], spec[2], spec[4]))
            else:
                result.append(('note',))
        return tuple(result)

    def SetContent(self, breakdown):
        """Postaví řádky z bonussources.Breakdown; vrátí výšku. Když se nezmění řádky (jen hodnoty, poznámky, čas
        efektu), přepíše jen texty: řádek pod myší zůstane a jeho tooltip se znovu nestaví."""
        self.breakdown = breakdown
        percent = breakdown.percent
        if self.expanded is None:
            first = [key for key, _, _, entries in breakdown.groups if len(entries) > 1]
            for index, part in enumerate(getattr(breakdown, 'components', ())):
                first.extend((index, key) for key, _, _, entries in part.groups if len(entries) > 1)
            first.extend(key for key, _, _, _ in breakdown.groups[:1])
            self.expanded = set(first[:1])
        specs = self._Specs(breakdown)
        structure = self._Structure(specs)
        if self.parts and structure == getattr(self, 'structure', None):
            self._Update(specs, percent)
            return self.height
        self._Clear()
        self.structure = structure
        y = 0
        for spec in specs:
            if spec[0] == 'item':
                self._Item(y, spec[1], spec[2], spec[3], spec[4], spec[7], T.INK, spec[5], spec[6],
                           spec[8] if len(spec) > 8 else None)
                y += ROW_H
            elif spec[0] == 'head':
                key = spec[1]
                head = GroupHead(self, self.kit, self.w, key, spec[2], spec[3], spec[4],
                                 lambda key=key: self.Toggle(key))
                head.SetPosition(0, y)
                head.SetWheelEvent(self.OnMouseWheel)
                head.Show()
                self._Keep(head)
                self.heads.append(head)
                y += ROW_H
            else:
                line = self._Keep(uir1.Text(self, '', GROUP_X, y + 1, self.kit.font('text_xs'), T.MUTED,
                                            valign='top'))
                uir1.Fit(line, spec[1], self.w - GROUP_X - VALUE_X)
                self.notes.append(line)
                y += NOTE_H
        y += BOTTOM
        self.height = y
        self.SetSize(self.w, y)
        return y

    def _Update(self, specs, percent):
        items, heads, notes = iter(self.item_rows), iter(self.heads), iter(self.notes)
        for spec in specs:
            if spec[0] == 'item':
                name_line, note_line, value_line, _row = next(items)
                x, name, note, value = spec[1], spec[2], spec[3], spec[4]
                uir1.Fit(value_line, bonussources.Format(value, spec[7]), VALUE_W)
                room = self.w - VALUE_X - VALUE_W - x
                if getattr(_row, 'note_after_name', False):
                    room = self.w - VALUE_X - uikit.TextWidth(value_line) - NOTE_GAP - x
                note_w = 0
                if note_line is not None:
                    uir1.Fit(note_line, note, min(NOTE_MAX, room // 2) if spec[6] == T.MUTED else room // 2)
                    note_w = uikit.TextWidth(note_line) + NOTE_GAP
                uir1.Fit(name_line, name, room - note_w - 4)
                self._PlaceNote(_row, name_line, note_line, x)
                # Tooltip řádku pod myší sleduje tutéž obnovu jako řádek (zbývající čas, hodnota).
                _row.entry = spec[8] if len(spec) > 8 else None
                if getattr(_row, 'hovered', False) and _row.cell is None and _row.entry is not None and _row.on_in:
                    _row.on_in(_row.entry)
            elif spec[0] == 'head':
                head = next(heads)
                head.value.SetText(spec[3])
            else:
                uir1.Fit(next(notes), spec[1], self.w - GROUP_X - VALUE_X)

    def Height(self):
        return self.height

    def Toggle(self, key):
        if self.expanded is None:
            self.expanded = set()
        if key in self.expanded:
            self.expanded.discard(key)
        else:
            self.expanded.add(key)
        if self.breakdown is not None:
            self.SetContent(self.breakdown)
        if self.on_resize:
            self.on_resize()

    def Reset(self):
        """Nový bonus: výchozí rozbalení."""
        self.expanded = None
        self.structure = None

    def Destroy(self):
        self._Clear()
        self.on_resize = self.wheel = self.item_in = self.item_out = None
        self.Hide()
