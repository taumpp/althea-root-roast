# -*- coding: utf-8 -*-
"""Settings v5 -> Rozhraní -> Panely tlačítek (2026-10-05, design v4.1).

Design: Panely v4 + v4.1 (docs/SETTINGS_KIT_LOOK.md); layout P1 and the badges
table O1 of the v5 proposals (owner's choice 2026-10-06): nothing scrolls
in the 1160 x 780 window.

* Tabs Minimapa / Lišta u inventáře / Odznaky a kanály in the heading row of the window. The preview column is
  as wide as its preview and runs from the heading row down (SideLayout, small caption): the minimap ring with
  all 12 places, the rail with all 13 places as big as the column allows (up to 1.25x), the rail as in game on
  the badges tab - no dimmed second panel.
* The settings in ONE line (Rozložení, Šipka 2. sloupce / Přepínač + Kolečko, Kruhy u minimapy) in the row font;
  a click on a control always switches it; the help (text + small preview) shows only when the mouse rests on a
  group for INFO_DELAY - never on a click (owner play test 2026-10-06: a click on "Sloupce" opened the help). Zasunout /
  Vyrovnat sit at the heading of the "Na liště" section they act on (uikit.ButtonGroup: B1 or the B3 block).
* Katalog funkcí with search (whole width): Na liště / Kruh 1-2, V menu Další, Skryto, Kanály as a grid of
  medallions as big as the preview icons ("Velikosti jako vedle?"). Drag from the catalogue
  into the preview and back; a gold frame shows where the function lands. A click on a catalogue icon adds
  it to the first free place. Right click: Odznak, Stav a odpočet, Přesunout do Další, Skrýt, Vrátit na
  výchozí místo. A free place is a dotted circle ("Volné místo – přetáhni sem funkci z katalogu").
* The legend in one row and the drag hint under the catalogue, the 4-step guide on the first opening
  (``tour_seen``), "Obnovit stránku" with a confirmation that says exactly what returns (this tab or the page).

Storage and game refresh are the existing models: ``minimappanel`` / ``inventoryrail`` / ``buttonpanelbadges``
/ ``uichannelbar`` sections of ``UserData/button-panels.json`` (format unchanged; new: ``settings_page``).

HOST CONTRACT. The class is a custom view of the v5 shell as it is:
``uisettingsc9.CUSTOM_VIEWS['panels'] = ('uisettingspanelsv5', 'PanelsPage')`` with ``custom='panels'`` and
``side=T('Náhled ve hře', ...)`` in settingsc9pages - ``FillSide(x, y, w, h)`` (the preview column, may come
before ``Build``), ``Build(width)`` -> content height (the shell does the second pass with a scrollbar),
``Clear()``, ``OnUpdate()``, ``Destroy()``, ``AskReset()``, ``ResetText()``, ``OnPressEscapeKey()``; and
``SelectTab(key)`` ('minimap', 'inventory', 'badges') for the cogwheels (buttonpanelsettings.Open). Fallback
kept for the c9 v4 shell (with a render hook): ``Build()`` without a width does the second
pass itself and the preview goes into the "Náhled ve hře" info panel (``c9_info_box``).
"""
import uikit
import uikittokens as T
import buttonpanelsv5 as model
import buttonpanelsettings as panelsettings
import buttonpanelstore
import inventoryrail as rail
import minimappanel as panel
from settingslocale import Text as Tr
from uisettingspanelsv5catalog import Catalog
from uisettingspanelsv5input import PanelsInput
from uisettingspanelsv5preview import MinimapView, RailView, MinimapSize, LegendRow, TOP, MORE_BAR_H, STEP
import uisettingspanelsv5widgets as widgets
from uisettingspanelsv5widgets import InfoZone, Outline

TAB_LABELS = ((model.TAB_MINIMAP, Tr('Minimapa', 'Minimap')),
              (model.TAB_RAIL, Tr('Lišta u inventáře', 'Inventory rail')),
              (model.TAB_BADGES, Tr('Odznaky a kanály', 'Badges and channels')))
MODE_OPTIONS = ((rail.MODE_COLUMNS, Tr('Sloupce', 'Columns')), (rail.MODE_PAGES, Tr('Strany', 'Pages')))
SWITCH_OPTIONS = ((rail.SWITCH_BOTTOM, Tr('Dole', 'Below')), (rail.SWITCH_SIDE, Tr('Vedle …', 'By …')),
                  (rail.SWITCH_TOP, Tr('Nahoře', 'Top')))
ARROW_OPTIONS = ((rail.TAB_TOP, Tr('Nahoře', 'Top')), (rail.TAB_BOTTOM, Tr('Dole', 'Bottom')),
                 (rail.TAB_COG, Tr('U kola', 'At cog')))
# P1 geometry (2026-10-06): the preview column only as wide as its preview, the rail as big as the design
# (1.25x = 30 px icons) while 13 places fit the column, the minimap ring at its native size.
RAIL_SCALE = {'1080': 1.25, '768': 1.0}
MINIMAP_SCALE = {'1080': 1.0, '768': 0.85}
MIN_STEP = 39            # px (native) between two rail places in the preview; the game uses 41
SIDE_PAD = {'1080': 12, '768': 8}
SIDE_MIN = {'1080': 120, '768': 96}
SEG_CELL = {'1080': 56, '768': 44}   # narrow segment cells of the one-line settings


def PageKit(window):
    """The window's kit: Spectral in the v5 shell (2026-10-05: everything Spectral), which falls back to
    the Tahoma sizes itself with an EXE that has no registered font family - the page follows it."""
    kit = getattr(window, 'kit', None)
    return kit if kit is not None else uikit.Kit(uikit.Profile(), 'B')


class PanelsPage(PanelsInput):
    def __init__(self, window):
        self.window = window
        self.tab = model.TAB_RAIL
        self.edit_page = None
        self.query = ''
        self.status = ''
        self.status_error = False
        self.kit = PageKit(window)
        self.side_box = None
        self.mm_entries, self.mm_known, self.mm_state = {}, (), panel.PanelState()
        self.rl_entries, self.rl_known, self.rl_state = {}, (), rail.RailState()
        PanelsInput.__init__(self)
        self._Forget()

    # ------------------------------------------------------------------ compatibility with the A7 page API
    @property
    def minimap(self):
        return self

    def Page(self, key=None):
        return self

    # ------------------------------------------------------------------ host
    def _Forget(self):
        self.built = False
        self.collect = None
        self.left_widgets = []
        self.rects = {}
        self.rows = {}
        self.catalog = None
        self.badges_tab = None
        self.mm_view = self.rl_view = None
        self.thumbs = []
        self.page_tabs = None
        self.status_lines = []
        self.status_anchor = None
        self.focus = None
        self.info_dots = []
        self.footer = []
        self.footer_top = 0
        self.rail_place = None
        self.tabs_parent = None

    def _Track(self, widget, wheel=True):
        window = self.window
        window.page_widgets.append(widget)
        if wheel:
            if hasattr(widget, 'SetWheelEvent'):
                widget.SetWheelEvent(window.OnMouseWheel)
            else:
                widget.OnMouseWheel = window.OnMouseWheel
        if self.collect is not None:
            self.collect.append(widget)
        return widget

    def Geometry(self):
        """Content column and preview column: v5 shell (``c9_current_view``, ``c9_side_box`` / ``FillSide``) or the
        c9 v4 shell of this branch (``c9_view``, the "Náhled ve hře" info panel ``c9_info_box``)."""
        window = self.window
        view = getattr(window, 'c9_current_view', None) or window.c9_view
        side = self.side_box or getattr(window, 'c9_side_box', None)
        pad = window.c9.get('pad', 0)
        if side is None:
            x, y, w = window.c9_info_box
            side = (x, y, w, window.c9['bot'] - 8 - y)
        return dict(content=window.content, width=view['w'], view_h=view['h'], view=(view['x'], view['y'], view['w'],
                    view['h']), preview_parent=window, preview=tuple(side), pad=pad)

    def FillSide(self, x, y, w, h):
        """v5 shell: the preview column (called while the shell lays out its columns, before ``Build``)."""
        self.side_box = (x, y, w, h)

    def Clear(self):
        """v5 shell: the page widgets are being cleared (page change, second layout pass)."""
        self.Detach()

    def ResetText(self):
        """The tooltip text of "Obnovit stránku"; the dialog itself is ``AskReset``."""
        import uisettingspanelsv5help as help_texts
        question, lines = help_texts.ResetText(self, model.SCOPE_TAB)
        return question

    def InfoText(self, key):
        """One line about a setting for the row tooltip of the v5 shell (the "i" bubble has the full help)."""
        import uisettingspanelsv5help as help_texts
        return help_texts.STRIP.get(key, '')

    def Interface(self):
        getter = getattr(getattr(self.window, 'backend', None), 'interface', None)
        try:
            return getter() if callable(getter) else None
        except Exception:
            return None

    # ------------------------------------------------------------------ models
    def Load(self):
        interface = self.Interface()
        self.mm_entries = dict((entry.action_id, entry) for entry in panel.Catalog(interface))
        self.mm_known = tuple(entry.action_id for entry in panel.Catalog(interface))
        self.mm_state = model.MinimapPacked(panel.LoadState(self.mm_known))
        self.rl_entries = dict((entry.action_id, entry) for entry in rail.Catalog(interface))
        bar = getattr(interface, 'wndExpandedTaskBar', None) if interface is not None else None
        named = rail.DEFAULT_IDS
        getter = getattr(bar, 'RailKnownIds', None)
        if callable(getter):
            try:
                named = tuple(getter())
            except Exception:
                named = rail.DEFAULT_IDS
        self.rl_known = tuple(a for a in rail.KnownIds(tuple(self.rl_entries), named)
                              if a in self.rl_entries)
        self.rl_state = model.RailPacked(rail.LoadState(self.rl_known))
        if self.edit_page is None or not self.rl_state.IsPages():
            self.edit_page = self.rl_state.ActivePage() if self.rl_state.IsPages() else 0

    def Label(self, action):
        entry = self.mm_entries.get(action) or self.rl_entries.get(action)
        if entry is None:
            return action or ''
        return panel.Label(entry)

    def Shortcut(self, action):
        try:
            return panel.ShortcutText(action)
        except Exception:
            return ''

    def ReadOnly(self):
        try:
            return buttonpanelstore.IsReadOnly()
        except Exception:
            return False

    # ------------------------------------------------------------------ v5 shell: the preview column (P1)
    def SideLayout(self):
        """(width, caption) of the preview column for the v5 shell (P1, 2026-10-06): as wide as the preview of
        this tab needs, from the heading row down to the footer, a small caption instead of the "Náhled ve hře"
        heading; the content column (settings line + catalogue) gets the rest and never scrolls in 1160 x 780."""
        self.kit = PageKit(self.window)
        self.Load()
        k = self.kit
        pad = SIDE_PAD[k.prof]
        if self.tab == model.TAB_MINIMAP:
            width = MinimapSize(MINIMAP_SCALE[k.prof])[0] + 2 * pad
            return width, Tr('Náhled ve hře | minimapa', 'In-game preview · minimap')
        scale, unused = self.RailPreviewMetrics(self.SideHeight() - self._PageTabsHeight())
        width = RailView.Width(self.rl_state, scale, editor=self.tab == model.TAB_RAIL)
        caption = Tr('Náhled | lišta', 'Preview · rail') if self.tab == model.TAB_RAIL else \
            Tr('Náhled | odznaky', 'Preview · badges')
        return max(width + 2 * pad, SIDE_MIN[k.prof]), caption

    def SideHeight(self):
        """Height of the preview column the shell gives (its compact layout: caption, then the column to the
        footer); the c9 v4 fallback uses its info panel."""
        window, k = self.window, self.kit
        g = getattr(window, 'c9', {})
        if 'top' in g and 'bot' in g:
            return g['bot'] - 8 - (g['top'] + 2 + k.cell('S') + 8)
        return self.Geometry()['preview'][3]

    def _PageTabsHeight(self):
        return (self.kit.p('seg_h') + 8) if self.tab == model.TAB_RAIL and self.rl_state.IsPages() else 0

    # ------------------------------------------------------------------ build
    def Build(self, width=None):
        """Left column into the scrolled content and the preview into its column; returns the content height.
        ``width`` given (v5 shell): exactly that width, the shell repeats the call narrower when it overflows."""
        window = self.window
        self.CancelDrag()
        self.HidePopups()
        self._Forget()
        self.kit = PageKit(window)
        widgets.SetFamily(self.kit)
        self.geo = self.Geometry()
        highlight = getattr(window, 'highlight', None)
        if highlight in model.HIGHLIGHT_TABS:
            self.tab = model.HIGHLIGHT_TABS[highlight]
            window.highlight = None
        self.Load()
        external = width is not None
        width = int(width) if external else self.geo['width']
        self.geo['width'] = width
        self.collect = []
        height = self._BuildLeft(width)
        if not external and height > self.geo['view_h']:
            self._DropLeft()
            self.collect = []
            height = self._BuildLeft(width - 18)
        self.left_widgets, self.collect = self.collect, None
        self._BuildPreview()
        self.built = True
        if self.ReadOnly():
            self.SetStatus(panelsettings.StoreErrorText(buttonpanelstore.ERROR_NEWER), error=True)
        else:
            self.SetStatus(self.status, self.status_error)
        self.Sync()
        self.MaybeStartTour()
        return height if external else max(self.geo['view_h'], height + 8)

    def _DropLeft(self):
        dropped = set(id(widget) for widget in self.collect)
        for widget in self.collect:
            widget.Hide()
        self.window.page_widgets = [w for w in self.window.page_widgets if id(w) not in dropped]
        if self.catalog is not None:
            self.catalog.Detach()
        if self.badges_tab is not None:
            self.badges_tab.Detach()
        self.catalog = self.badges_tab = None
        self.rows, self.rects, self.info_dots, self.footer = {}, {}, [], []

    # ------------------------------------------------------------------ left column (P1)
    def _BuildLeft(self, width):
        """P1 (2026-10-06): the tabs in the heading row, the settings in ONE line, the catalogue as a grid of
        big medallions, the legend and the drag hint under it - nothing scrolls in the 1160 x 780 window."""
        k = self.kit
        parent = self.geo['content']
        self.left_width = width
        self.footer = []
        self._BuildTabs()
        y = 0
        if self.tab == model.TAB_BADGES:
            import uisettingspanelsv5badges
            self.badges_tab = uisettingspanelsv5badges.BadgesTab(self, parent, k, self._Track)
            self.rects['badges'] = (0, y, width, 0)
            y = self.badges_tab.Build(y, width)
            self.status_anchor = (parent, 0, y + 2, width)
            return y + k.cell('S') + 5
        y = self._SettingsLine(parent, y, width)
        self.catalog = Catalog(self, parent, k, self._Track)
        self.catalog.query = self.query
        if self.tab == model.TAB_RAIL and not self.rl_state.IsPages():
            # Column 2 actions at the heading of the rail section they act on (B1 buttons or the B3 block).
            buttons = self._Track(uikit.ButtonGroup(parent, k, (
                (Tr('Vysunout', 'Show'), lambda: self._Run(self.ToggleCollapsed)),
                (Tr('Vyrovnat', 'Balance'), lambda: self._Run(self.Balance)))))
            self.rows['collapse'], self.rows['balance'] = buttons.buttons
            self.catalog.header_widgets['rail'] = buttons
        y = self.catalog.BuildHeader(y, width)
        top = y
        y = self.catalog.Build(y, width, self.CatalogSections())
        buttons = self.catalog.header_widgets.get('rail')
        if buttons is not None and buttons.IsShow():    # placed by the catalogue in its "Na liště" heading
            bx, by = buttons.GetLocalPosition()
            self.info_dots.append(InfoZone(parent, bx, by, buttons.GetWidth(), buttons.GetHeight(), 'second'))
        self.rects['catalog'] = (0, top, width, y - top)
        return self._BuildFooter(parent, y, width)

    def _BuildTabs(self):
        """Tabs Minimapa / Lišta u inventáře / Odznaky a kanály in the heading row of the window, right-aligned to
        the content column (P1); the c9 v4 fallback keeps them at the top of the content."""
        k = self.kit
        window = self.window
        font = k.font('M' if k.prof == '1080' else 'S')
        g = getattr(window, 'c9', {})
        vx, vy, vw, vh = self.geo['view']
        if 'hy' in g:
            parent = self.geo['preview_parent']
            heading = getattr(window, 'heading', None)
            room = vw - (uikit.TextWidth(heading) if heading is not None else 160) - 24
            segment = self._Track(uikit.Segment(parent, k, TAB_LABELS, event=self.SelectTab, font=font,
                                                max_width=room))
            x, y = vx + vw - segment.Width(), g['hy'] - k.p('seg_h') // 2
        else:
            parent = self.geo['content']
            segment = self._Track(uikit.Segment(parent, k, TAB_LABELS, event=self.SelectTab, font=font))
            x, y = self.left_width - segment.Width(), 0
        segment.SetPosition(x, y)
        segment.SetValue(self.tab)
        self.rows['tabs'] = segment
        self.rects['tabs'] = (x, y, segment.Width(), k.p('seg_h'))
        self.tabs_parent = parent

    def _Section(self, parent, text, y):
        """The section heading of the shell: the v5 kit component when the kit has it, else the c9 v4 text."""
        k = self.kit
        section = getattr(uikit, 'Section', None)
        if section is not None:
            widget = self._Track(section(parent, k, 0, y, self.left_width, text), wheel=False)
            return y + widget.Height() + (8 if k.prof == '1080' else 6)
        self._Track(uikit.Text(parent, text, 0, y + 4, k.font('S'), T.MUTED, valign='top'), wheel=False)
        return y + k.cell('S') + 10

    def LineFont(self):
        """Font of the one-line settings (2026-10-06: the 13 px line of the design was too dense - the row
        font and air between the groups; the column-2 actions moved to the "Na liště" heading)."""
        return self.kit.font('M' if self.kit.prof == '1080' else 'S')

    def _Segment(self, parent, options, event, key):
        """A segment of the one-line settings: cells as wide as their labels (the line stays one line at 1080), a
        click closes the hover help first."""
        k = self.kit
        segment = self._Track(uikit.Segment(parent, k, options, event=lambda value, run=event: self._Run(run, value),
                                            font=self.LineFont(), max_width=1, min_cell=SEG_CELL[k.prof]))
        self.rows[key] = segment
        return segment

    def _Run(self, callback, *args):
        """A control was used: the hover help goes away (it never opens from a click) and its group stays quiet
        until the mouse leaves it, then the action."""
        self.CloseInfo()
        zone = self._InfoZoneAt(widgets.Mouse())
        self.info_quiet = zone.info_key if zone is not None else None
        callback(*args)

    def _SettingsLine(self, parent, y, width):
        """The rail (ring) settings as label + control groups in ONE line (P1); a group that does not fit starts a
        second line (only the 768 profile). A click on a control always switches it; resting the mouse on a group
        for INFO_DELAY shows its help bubble (text + small preview) under the line - never a click (2026-10-06:
        a click on "Sloupce" opened the help instead of switching)."""
        k = self.kit
        state = self.rl_state
        groups = []
        if self.tab == model.TAB_RAIL:
            groups.append(('layout', Tr('Rozložení', 'Layout'), self._Segment(parent, MODE_OPTIONS, self.SetMode, 'mode')))
            if state.IsPages():
                groups.append(('switch', Tr('Přepínač', 'Switcher'),
                               self._Segment(parent, SWITCH_OPTIONS, self.SetSwitchStyle, 'switch')))
                toggle = self._Track(uikit.Toggle(parent, k, 0, 0, event=lambda: self._Run(self.ToggleWheel)))
                self.rows['wheel'] = toggle
                groups.append(('wheel', Tr('Kolečko', 'Wheel'), toggle))
            else:
                groups.append(('arrow', Tr('Šipka 2. sloupce', 'Column 2 arrow') if k.prof == '1080' else
                               Tr('Šipka', 'Arrow'),
                               self._Segment(parent, ARROW_OPTIONS, self.SetTabStyle, 'arrow')))
        else:
            counts = self._Track(uikit.Text(parent, '', 0, 0, self.LineFont(), T.INK_DIM), wheel=False)
            counts.SetText('kruh 1: 5 / 5 | kruh 2: 7 / 7')
            self.rows['rings'] = counts
            groups.append(('rings', Tr('Kruhy u minimapy', 'Minimap rings'), counts))
        texts = set(id(control) for key, label, control in groups if key == 'rings')
        line_h = k.p('seg_h') + (12 if k.prof == '1080' else 8)
        gap = 24 if k.prof == '1080' else 18
        x, top = 0, y
        for key, label, control in groups:
            label_w = 0
            if label:
                probe = uikit.Text(parent, label, 0, 0, self.LineFont(), T.INK)
                label_w = uikit.TextWidth(probe) + (12 if k.prof == '1080' else 8)
                probe.Hide()
            if id(control) in texts:
                control_w = uikit.TextWidth(control)
            else:
                control_w = control.Width() if hasattr(control, 'Width') else control.GetWidth()
            group_w = label_w + control_w
            if x > 0 and x + group_w > width:
                x, top = 0, top + line_h
            self._Group(parent, key, label, control, x, top, group_w, label_w, line_h, id(control) in texts)
            x += group_w + gap
        self.rects['rows'] = (0, y, width, top + line_h - y)
        return top + line_h + (6 if k.prof == '1080' else 4)

    def _Group(self, parent, key, label, control, x, y, w, label_w, line_h, text=False):
        k = self.kit
        # The group's help is a polled rectangle, not a window: nothing lies over the control (C++ pick rule).
        zone = InfoZone(parent, x, y, w, line_h, key)
        self.info_dots.append(zone)
        cy = y + line_h // 2
        if label:
            self._Track(uikit.Text(parent, label, x, cy - self.Nudge(), self.LineFont(), T.INK), wheel=False)
        cx = x + label_w
        if text:
            control.SetPosition(cx, cy - self.Nudge())
        else:
            ch = getattr(control, 'h', None) or control.GetHeight()
            control.SetPosition(cx, cy - ch // 2)
        return zone

    def Nudge(self):
        nudge = getattr(self.window, 'C9TextNudge', None)
        return nudge() if callable(nudge) else 0

    def _BuildFooter(self, parent, y, width):
        """Legend in one row and the drag hint under the catalogue (P1); they follow the catalogue height."""
        k = self.kit
        y += 10 if k.prof == '1080' else 6
        widgets_, height = LegendRow(parent, k, 0, y, width)
        for widget in widgets_:
            self._Track(widget, wheel=False)
            self.footer.append((widget, widget.GetLocalPosition()[1] - y))
        hy = height + (6 if k.prof == '1080' else 4)
        lines, unused = uikit.Wrap(parent, Tr('Táhni ikonu do náhledu nebo zpět | klik = první volné místo | pravý klik '
                                              '= další volby', 'Drag an icon into the preview or back · click = first '
                                              'free place · right click = more'), 0, y + hy, width, k.font('S'),
                                   T.MUTED, k.cell('S') + 3)
        for line in lines:
            self._Track(line, wheel=False)
            self.footer.append((line, line.GetLocalPosition()[1] - y))
        self.footer_top = y
        bottom = y + hy + len(lines) * (k.cell('S') + 3)
        self.status_anchor = (parent, 0, bottom + 4, width)
        return bottom + 2 * (k.cell('S') + 3) + 4

    def _PlaceFooter(self):
        """The catalogue changed its height (search, moves): the legend, hint and status follow it."""
        if self.catalog is None or not self.footer:
            return
        k = self.kit
        y = self.catalog.bottom + (10 if k.prof == '1080' else 6)
        if y == self.footer_top:
            return
        shift = y - self.footer_top
        for widget, dy in self.footer:
            widget.SetPosition(widget.GetLocalPosition()[0], y + dy)
        self.footer_top = y
        if self.status_anchor is not None:
            parent, x, sy, w = self.status_anchor
            self.status_anchor = (parent, x, sy + shift, w)
            self.SetStatus(self.status, self.status_error)

    def FooterBottom(self):
        if not self.footer:
            return self.catalog.bottom if self.catalog is not None else 0
        k = self.kit
        return max(widget.GetLocalPosition()[1] for widget, unused in self.footer) + k.cell('S') + 3 + \
            2 * (k.cell('S') + 3)

    def CatalogSections(self):
        if self.tab == model.TAB_MINIMAP:
            sections = dict(model.MinimapSections(self.mm_state, self.mm_known))
            full = len(model.Pack(self.mm_state.slots)) >= panel.MAX_SLOTS
            ring1_full = len(sections['ring1']) >= panel.RING_SIZES[0]
            return (('ring1', Tr('Kruh 1', 'Ring 1'), Tr('%d míst', '%d places') % panel.RING_SIZES[0],
                     sections['ring1'], not ring1_full, 'left'),
                    ('ring2', Tr('Kruh 2', 'Ring 2'), Tr('%d míst', '%d places') % panel.RING_SIZES[1],
                     sections['ring2'], ring1_full and not full, 'right',
                     None if ring1_full else Tr('plní se, až bude kruh 1 plný', 'fills once ring 1 is full')),
                    ('menu', Tr('V menu Další', 'In the More menu'), Tr('ve hře přes „…“', 'in game via "…"'),
                     sections['menu'], False, None),
                    ('hidden', Tr('Skryto', 'Hidden'), '', sections['hidden'], False, 'left',
                     Tr('přetáhni sem, co nechceš vidět', 'drop here what you do not want to see')),
                    ('channels', Tr('Kanály', 'Channels'), Tr('CH6-7 jen s VIP', 'CH6–7 VIP only'),
                     sections['channels'], False, 'right'))
        state = self.rl_state
        sections = dict(model.RailSections(state, self.rl_known))
        if state.IsPages():
            pages = model.RailContentPages(state) or [0]
            label = (Tr('Na liště | strana %d', 'On the rail · page %d') % (pages[0] + 1) if len(pages) == 1
                     else Tr('Na liště | strany %s', 'On the rail · pages %s') % ', '.join(str(p + 1) for p in pages))
        else:
            label = (Tr('Na liště | 2 sloupce', 'On the rail · 2 columns') if state.HasSecond()
                     else Tr('Na liště', 'On the rail'))
        lists = model.RailLists(state)
        room = any(len(ids) < rail.MAX_PER_COLUMN for ids in lists)
        return (('rail', label, Tr('pořadí jako ve hře', 'order as in game'), sections['rail'], room, None),
                ('menu', Tr('V menu Další', 'In the More menu'), Tr('ve hře přes „…“', 'in game via "…"'),
                 sections['menu'], False, None),
                ('hidden', Tr('Skryto', 'Hidden'), '', sections['hidden'], False, 'left',
                 Tr('přetáhni sem, co nechceš vidět', 'drop here what you do not want to see')),
                ('channels', Tr('Kanály', 'Channels'), Tr('CH6-7 jen s VIP', 'CH6–7 VIP only'),
                 sections['channels'], False, 'right'))

    # ------------------------------------------------------------------ preview (P1: the whole column height)
    def _BuildPreview(self):
        k = self.kit
        px, py, pw, ph = self.geo['preview']
        parent = self.geo['preview_parent']
        bottom = py + ph
        self.collect = []
        self.focus = None
        if self.tab == model.TAB_MINIMAP:
            scale = min(MINIMAP_SCALE[k.prof], float(pw) / MinimapSize(1.0)[0])
            mw, mh = MinimapSize(scale)
            mx = px + (pw - mw) // 2
            self.mm_view = MinimapView(self, parent)
            for widget in self.mm_view.Widgets():
                self._Track(widget, wheel=False)
            self.mm_view.Render(mx, py + 6, scale, model.Pack(self.mm_state.slots), free=True)
            self.focus = (mx - 6, py, mw + 12, mh + 12)
            counts = self._Track(uikit.Text(parent, '', px + pw // 2, py + mh + 22, k.font('S'), T.INK_DIM,
                                            align='center', valign='top'), wheel=False)
            self.rows['preview_counts'] = counts
        elif self.tab == model.TAB_RAIL:
            self._PreviewRail(parent, px, py, pw, bottom)
        else:
            self._PreviewBadges(parent, px, py, pw, bottom)
        if self.focus is not None:
            outline = Outline(parent, alpha=0.55)
            outline.Set(*self.focus)
            for widget in outline.Widgets():
                self._Track(widget, wheel=False)
        self.preview_widgets, self.collect = self.collect, None

    def RailPreviewMetrics(self, avail_h):
        """(scale, pitch) of the rail preview: all 13 places in the column height, as big as the design (P1: up to
        1.25x, icons 30 px) - the in-game 41 px step is tightened to 39 px before the scale goes down (never under
        0.5)."""
        rows = rail.MAX_PER_COLUMN
        fixed = TOP + MORE_BAR_H + 2
        top = RAIL_SCALE[self.kit.prof] if self.kit is not None else 1.0
        scale = max(0.5, min(top, float(avail_h) / (fixed + rows * MIN_STEP)))
        step = max(MIN_STEP, min(STEP, (float(avail_h) / scale - fixed) / rows))
        return scale, step * scale

    def _RailPlace(self, px, py, pw, bottom, editor=True):
        """(right, top, scale, pitch) of the rail centred in the preview column."""
        top = py + 4 + self._PageTabsHeight()
        scale, pitch = self.RailPreviewMetrics(bottom - top)
        width = RailView.Width(self.rl_state, scale, editor=editor)
        return px + (pw + width) // 2, top, scale, pitch

    def _PreviewRail(self, parent, px, py, pw, bottom):
        k = self.kit
        state = self.rl_state
        right, top, scale, pitch = self._RailPlace(px, py, pw, bottom)
        if state.IsPages():
            seg = self._Track(uikit.Segment(parent, k, [(p, str(p + 1)) for p in range(rail.MAX_PAGES)],
                                            event=self.SelectPage, font=k.font('S'),
                                            min_cell=26 if k.prof == '1080' else 22))
            seg.SetPosition(px + (pw - seg.Width()) // 2, py + 4)
            seg.SetValue(self.edit_page)
            self.page_tabs = seg
            for page, cell in enumerate(seg.cells):
                self.AttachTip(cell, Tr('Strana %d', 'Page %d') % (page + 1),
                               lambda page=page: self.PageTabText(page), 'above')
        self.rail_place = (right, top, scale, pitch)
        self.rl_view = RailView(self, parent)
        rects = self.rl_view.Render(right, top, scale, state, self.edit_page, editor=True, pitch=pitch)
        for widget in self.rl_view.Widgets():
            self._Track(widget, wheel=False)
        for widget in (self.rl_view.ear, self.rl_view.head):
            self.AttachTip(widget, lambda: (Tr('Vysunout 2. sloupec', 'Show column 2') if self.rl_state.collapsed
                                            else Tr('Zasunout 2. sloupec', 'Hide column 2')),
                           Tr('jeho tlačítka zůstanou', 'its buttons stay'), 'left')
        width = RailView.Width(state, scale, editor=True)
        left = right - width - 4
        height = max(r[1][3] for r in rects) if rects else 0
        self.focus = (left, top - 4, width + 8, height + 8)

    def _PreviewBadges(self, parent, px, py, pw, bottom):
        """O1: the rail as the game shows it (badges and states on its buttons), as big as on the rail tab."""
        state = self.rl_state
        top = py + 4
        scale, pitch = self.RailPreviewMetrics(bottom - top)
        width = RailView.Width(state, scale, editor=False)
        self.rl_view = RailView(None, parent, interactive=False)
        self.rl_view.Render(px + (pw + width) // 2, top, scale, state, editor=False, pitch=pitch)
        for widget in self.rl_view.Widgets():
            self._Track(widget, wheel=False)

    # ------------------------------------------------------------------ sync after a change
    def Sync(self):
        if not self.built:
            return
        rows = self.rows
        if 'tabs' in rows:
            rows['tabs'].SetValue(self.tab)
        state = self.rl_state
        if 'mode' in rows:
            rows['mode'].SetValue(state.mode)
        if 'switch' in rows:
            rows['switch'].SetValue(state.switch_style)
        if 'wheel' in rows:
            rows['wheel'].SetOn(state.wheel)
        if 'arrow' in rows:
            rows['arrow'].SetValue(state.tab_style)
            (rows['arrow'].Enable if state.HasSecond() else rows['arrow'].Disable)()
        if 'collapse' in rows:
            rows['collapse'].SetText(Tr('Vysunout', 'Show') if state.collapsed else Tr('Zasunout', 'Hide'))
            (rows['collapse'].Enable if state.HasSecond() else rows['collapse'].Disable)()
            count = sum(len(ids) for ids in model.RailLists(state))
            (rows['balance'].Enable if count >= 2 else rows['balance'].Disable)()
        slots = model.Pack(self.mm_state.slots)
        counts = Tr('kruh 1: %d / %d | kruh 2: %d / %d', 'ring 1: %d / %d · ring 2: %d / %d') % (
            min(len(slots), panel.RING_SIZES[0]), panel.RING_SIZES[0], max(0, len(slots) - panel.RING_SIZES[0]),
            panel.RING_SIZES[1])
        if 'rings' in rows:
            rows['rings'].SetText(counts)
        if 'preview_counts' in rows:
            rows['preview_counts'].SetText(counts.replace('kruh', 'Kruh').replace(' | ', '  |  '))
        if self.catalog is not None:
            self.catalog.Sync(self.CatalogSections())
            self._PlaceFooter()
            self._ContentHeight()
        selected = self.menu_action if self.menu_open() else None
        if self.mm_view is not None and self.tab == model.TAB_MINIMAP:
            self.mm_view.Render(self.mm_view_pos()[0], self.mm_view_pos()[1], self.mm_view.scale, slots, free=True,
                                selected=selected)
        if self.rl_view is not None and self.tab == model.TAB_RAIL:
            self._RenderRail(selected)
        if self.page_tabs is not None:
            self.page_tabs.SetValue(self.edit_page)
        if self.badges_tab is not None:
            self.badges_tab.Sync()
        self.SyncBadges()

    def mm_view_pos(self):
        s = self.mm_view.scale
        x, y = self.mm_view.frame.GetLocalPosition()
        return x - 73 * s, y

    def _RenderRail(self, selected=None):
        px, py, pw, ph = self.geo['preview']
        right, top, scale, pitch = self._RailPlace(px, py, pw, py + ph)
        self.rl_view.Render(right, top, scale, self.rl_state, self.edit_page, editor=True, pitch=pitch,
                            selected=selected)

    def _ContentHeight(self):
        """The catalogue height changed (search, moves): resize the scrolled content, keep the offset."""
        window = self.window
        if self.catalog is None or not hasattr(window, '_LayoutScroll'):
            return
        height = max(self.geo['view_h'], self.FooterBottom() + 8)
        if height != getattr(window, 'content_height', None):
            offset = max(0, -window.content.GetLocalPosition()[1])
            window.content_height = height
            window._LayoutScroll(offset)

    def SetStatus(self, text, error=False):
        """A save result or error: P1 under the legend in the content column (two lines), the badges tab under the
        table; ``status_anchor`` = (parent, x, y, width)."""
        self.status, self.status_error = text or '', error
        for line in self.status_lines:
            line.Hide()
        self.status_lines = []
        if not self.built or not text or self.status_anchor is None:
            return
        parent, x, y, w = self.status_anchor
        k = self.kit
        lines, unused = uikit.Wrap(parent, text, x, y, max(80, w), k.font('S'), T.RUBY_HI if error else T.GOLD,
                                   k.cell('S') + 3)
        for line in lines[:2]:
            self._TrackPreview(line)
        for line in lines[2:]:
            line.Hide()
        self.status_lines = lines[:2]

    def _TrackPreview(self, widget):
        self.window.page_widgets.append(widget)
        return widget

    # ------------------------------------------------------------------ tabs and settings
    def SelectTab(self, key):
        tab = model.TabOf(key) or (key if key in model.TABS else None)
        if tab is None:
            return
        if tab == self.tab and self.built:
            return
        self.tab = tab
        self.status = ''
        self.Rerender(keep_scroll=False)

    def Rerender(self, keep_scroll=True):
        window = self.window
        if keep_scroll and hasattr(window, '_SaveScroll'):
            window._SaveScroll()
        elif hasattr(window, 'scroll_offsets'):
            window.scroll_offsets[getattr(window, 'c9_page', 'panels')] = 0
        window._Render()

    def OnSearch(self, text):
        """The catalogue search: only the catalogue is laid out again (the field keeps its focus)."""
        self.query = text or ''
        if self.catalog is not None:
            self.catalog.query = self.query
            self.catalog.Sync(self.CatalogSections())
            self._ContentHeight()
            self.SyncBadges()

    def SetMode(self, mode):
        state = rail.SetMode(self.rl_state, mode)
        if mode == rail.MODE_PAGES:
            self.edit_page = state.ActivePage()
            state = rail.SetPage(state, self.edit_page)
        if self.CommitRail(state):
            self.Rerender()

    def SetSwitchStyle(self, style):
        self.CommitRail(rail.SetSwitchStyle(self.rl_state, style))

    def ToggleWheel(self):
        self.CommitRail(rail.SetWheel(self.rl_state, not self.rl_state.wheel))

    def SetTabStyle(self, style):
        if self.rl_state.HasSecond():
            self.CommitRail(rail.SetTabStyle(self.rl_state, style))

    def ToggleCollapsed(self):
        if self.rl_state.HasSecond():
            self.CommitRail(rail.SetCollapsed(self.rl_state, not self.rl_state.collapsed))

    def Balance(self):
        self.CommitRail(rail.Balance(self.rl_state))

    def PageTabText(self, page):
        count = len(model.RailLists(self.rl_state)[page]) if page < self.rl_state.ListCount() else 0
        if page == self.edit_page:
            text = Tr('upravuješ ji; ve hře je vidět', 'you edit it; shown in game')
        else:
            text = Tr('klik = upravit | pusť sem ikonu = přesun', 'click = edit · drop an icon = move here')
        return '%s | %s' % (Tr('%d tlačítek', '%d buttons') % count if count else Tr('prázdná', 'empty'), text)

    def SelectPage(self, page):
        """Edit this page; it is also the page shown in game (an empty page shows the first with functions)."""
        self.edit_page = page
        self.CommitRail(rail.SetPage(self.rl_state, page))

    # ------------------------------------------------------------------ commits
    def CommitMinimap(self, state, status=''):
        if state is None:
            self.SetStatus(Tr('Kruhy pojmou nejvýš %d tlačítek.', 'The rings hold at most %d buttons.')
                           % panel.MAX_SLOTS, error=True)
            self.Sync()
            return False
        try:
            panel.SaveState(state, self.mm_known)
            error = panelsettings.StoreErrorText()
        except (ValueError, TypeError):
            error = Tr('Nastavení panelu se nepodařilo uložit.', 'Could not save the panel settings.')
        self.mm_state = model.MinimapPacked(panel.LoadState(self.mm_known))
        minimap = getattr(self.Interface(), 'wndMiniMap', None)
        if minimap is not None and hasattr(minimap, 'RefreshLauncherPanel'):
            minimap.RefreshLauncherPanel()
        self.SetStatus(error or status, error=bool(error))
        self.Sync()
        return not error

    def CommitRail(self, state, status=''):
        if state is None:
            self.SetStatus(Tr('Lišta je plná (%d x 13).', 'The rail is full (%d x 13).')
                           % self.rl_state.ListCount(), error=True)
            self.Sync()
            return False
        try:
            rail.SaveState(state, self.rl_known)
            error = panelsettings.StoreErrorText()
        except (ValueError, TypeError):
            error = Tr('Nastavení lišty se nepodařilo uložit.', 'Could not save the rail settings.')
        self.rl_state = model.RailPacked(rail.LoadState(self.rl_known))
        bar = getattr(self.Interface(), 'wndExpandedTaskBar', None)
        if bar is not None and hasattr(bar, 'RefreshRail'):
            bar.RefreshRail()
        self.SetStatus(error or status, error=bool(error))
        self.Sync()
        return not error

    def StoreError(self):
        self.SetStatus(panelsettings.StoreErrorText(), error=True)

    def BadgesChanged(self):
        try:
            import uibuttonpanelbadges
            uibuttonpanelbadges.Invalidate()
        except Exception:
            pass
        self.SetStatus('')
        self.SyncBadges()

    def ChannelBarChanged(self):
        """Refresh an open channel bar (its lock) after the switch on the badges tab."""
        try:
            import uichannelbar
            window = uichannelbar._bar.get('window')
            if window is not None:
                window.settings = uichannelbar.Load()
                window.Refresh(force=True)
        except Exception:
            pass

    # ------------------------------------------------------------------ lifecycle
    def Detach(self):
        """The window clears the page widgets: drop every reference, close the popups and the guide."""
        self.CancelDrag()
        self.HidePopups()
        self.EndTour(mark=False, keep_step=True)
        self.DropBadges()
        if self.catalog is not None:
            self.catalog.Detach()
        if self.badges_tab is not None:
            self.badges_tab.Detach()
        self._Forget()

    def Destroy(self):
        self.Detach()
        self.DestroyPopups()
        self.window = None

    def RestoreDefaults(self, scope=model.SCOPE_TAB):
        """Without a dialog (A7 API): the active tab, or every tab with ``scope='page'``."""
        for tab in model.ResetTabs(self.tab, scope):
            if tab == model.TAB_MINIMAP:
                panel.SaveState(panel.DefaultState(self.mm_known), self.mm_known, forget_unavailable=True)
            elif tab == model.TAB_RAIL:
                rail.SaveState(rail.DefaultState(self.rl_known), self.rl_known, forget_unavailable=True)
                self.edit_page = 0
            else:
                import buttonpanelbadges as badges
                settings = badges.Load()
                if not badges.Save(badges.Settings(settings.extra)):
                    self.StoreError()
                model.SetChannelBarPinned(False)
                self.ChannelBarChanged()
                self.BadgesChanged()
        error = panelsettings.StoreErrorText()
        self.mm_state = model.MinimapPacked(panel.LoadState(self.mm_known))
        self.rl_state = model.RailPacked(rail.LoadState(self.rl_known))
        interface = self.Interface()
        for name, method in (('wndMiniMap', 'RefreshLauncherPanel'), ('wndExpandedTaskBar', 'RefreshRail')):
            target = getattr(interface, name, None)
            if target is not None and hasattr(target, method):
                getattr(target, method)()
        self.status = error
        self.status_error = bool(error)
        if self.built:
            self.Rerender()


def FillWidth(segment, width):
    """Stretch a kit segment to ``width``: every cell its label plus an equal share of the rest."""
    cells = segment.cells
    texts = [uikit.TextWidth(cell.label) for cell in cells]
    extra = max(0, int(width) - sum(texts)) // max(1, len(cells))
    widths = [t + extra for t in texts]
    widths[-1] = int(width) - sum(widths[:-1])
    h = segment.kit.p('seg_h')
    x = 0
    for cell, w in zip(cells, widths):
        cell.Place(x, w, h)
        x += w
    segment.width = int(width)
    segment.SetSize(int(width), h)
