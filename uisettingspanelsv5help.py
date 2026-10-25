# -*- coding: utf-8 -*-
"""Texts of Settings v5 -> Panely tlačítek (2026-10-05, design v4.1): the "i" bubbles with their
small previews, the exact text of "Obnovit stránku" and the 4 steps of the guide.

The reset text says exactly what returns (owner finding 2026-10-05: the A7 dialog promised "všechny volby"
while only the shown tab was reset): the defaults are read from the models (``minimappanel.DEFAULT_IDS``,
``inventoryrail.DefaultState``), so the text follows a change of the defaults.
"""
import uikit
import uikittokens as T
import buttonpanelsv5 as model
import inventoryrail as rail
import minimappanel as panel
from settingslocale import Text as Tr
from uisettingspanelsv5preview import MinimapView, RailView, MinimapSize
from uisettingspanelsv5widgets import Outline, Bar, GlobalRect

TAB_NAMES = {model.TAB_MINIMAP: Tr('Minimapa', 'Minimap'), model.TAB_RAIL: Tr('Lišta u inventáře', 'Inventory rail'),
             model.TAB_BADGES: Tr('Odznaky a kanály', 'Badges and channels')}


# --------------------------------------------------------------------------- small previews of the bubbles
def _SampleIds(page, count):
    ids = [a for a in rail.DEFAULT_IDS if a in page.rl_entries] or list(page.rl_known)
    return tuple(ids[:count])


def _RailFigures(page, states, captions, current):
    """Mini rails side by side with a caption each; the current variant is outlined. -> figure callback."""
    def figure(parent, width):
        k = page.kit
        widgets = []
        n = len(states)
        cell = width // n
        scale = 0.7
        top = 2
        height = 0
        for index, (state, caption) in enumerate(zip(states, captions)):
            view = RailView(None, parent, interactive=False)
            rw = RailView.Width(state, scale, editor=False)
            right = index * cell + cell // 2 + rw // 2
            view.Render(right, top, scale, state, editor=False)
            widgets.extend(view.Widgets())
            rows = max(len(ids) for ids in model.RailLists(state))
            h = RailView.Height(rows, scale)
            height = max(height, h)
            widgets.append(uikit.Text(parent, caption, index * cell + cell // 2, top + h + 6, k.font('S'),
                                      T.GOLD_HI if index == current else T.MUTED, align='center', valign='top'))
            if index == current:
                outline = Outline(parent, alpha=0.8)
                outline.Set(index * cell + 4, 0, cell - 8, h + k.cell('S') + 12)
                widgets.extend(outline.Widgets())
        page.bubble_widgets = widgets
        return height + k.cell('S') + 14
    return figure


def _MinimapFigure(page):
    def figure(parent, width):
        scale = min(0.6, float(width) / MinimapSize(1.0)[0])
        view = MinimapView(None, parent, interactive=False)
        mw, mh = MinimapSize(scale)
        view.Render((width - mw) // 2, 0, scale, model.Pack(page.mm_state.slots), free=True)
        page.bubble_widgets = view.Widgets()
        return mh + 4
    return figure


def Info(page, key):
    """(title, paragraphs, figure callback or None) of one "i"."""
    state = page.rl_state
    ids = _SampleIds(page, 7)
    if key == 'layout':
        states = (rail.RailState((ids[:4], ids[4:7]), mode=rail.MODE_COLUMNS),
                  rail.RailState((ids[:4], ids[4:7]), mode=rail.MODE_PAGES, switch_style=rail.SWITCH_TOP))
        current = 0 if not state.IsPages() else 1
        return (Tr('Rozložení lišty', 'Rail layout'),
                (Tr('Sloupce - jeden nebo dva sloupce vedle sebe; 2. sloupec zasuneš a vysuneš šipkou u lišty.',
                    'Columns – one or two columns side by side; column 2 is pushed in and out by an arrow.'),
                 Tr('Strany - jeden sloupec a strany 1-3 jako u lišty schopností; přepínáš malým přepínačem nebo '
                    'kolečkem myši.', 'Pages – one column with pages 1–3 like the skillbar; flip them with a small '
                    'switcher or the mouse wheel.')),
                _RailFigures(page, states, (Tr('Sloupce', 'Columns'), Tr('Strany', 'Pages')), current))
    if key == 'switch':
        styles = (rail.SWITCH_BOTTOM, rail.SWITCH_SIDE, rail.SWITCH_TOP)
        states = [rail.RailState((ids[:4], ids[4:7]), mode=rail.MODE_PAGES, switch_style=style) for style in styles]
        return (Tr('Přepínač stran', 'Page switcher'),
                (Tr('Kde ve hře přepínáš strany 1-3 lišty:', 'Where you flip pages 1–3 of the rail in game:'),
                 Tr('Dole - místo lišty „…“; tlačítko „…“ se přesune nad lištu ke kolu.',
                    'Below – instead of the "…" bar; "…" moves above the rail to the cogwheel.'),
                 Tr('Vedle … - vlevo u posledního řádku, vedle „…“.', 'By … – left of the last row, next to "…".'),
                 Tr('Nahoře - vlevo u prvního řádku, místo ouška.', 'Top – left of the first row.'),
                 Tr('Přepínač je vidět, jen když má tlačítka víc stran.',
                    'The switcher shows only while more than one page has buttons.')),
                _RailFigures(page, states, [label for unused, label in (
                    (rail.SWITCH_BOTTOM, Tr('Dole', 'Below')), (rail.SWITCH_SIDE, Tr('Vedle …', 'By …')),
                    (rail.SWITCH_TOP, Tr('Nahoře', 'Top')))], styles.index(state.switch_style)))
    if key == 'wheel':
        return (Tr('Kolečko myši', 'Mouse wheel'),
                (Tr('Kolečko myši nad lištou přepíná strany. Vypni ho, když kolečkem nad lištou raději nic '
                    'neměníš.', 'The mouse wheel over the rail flips its pages. Turn it off if the wheel should '
                    'not change anything there.'),), None)
    if key == 'arrow':
        styles = (rail.TAB_TOP, rail.TAB_BOTTOM, rail.TAB_COG)
        states = [rail.RailState((ids[:4], ids[4:7]), mode=rail.MODE_COLUMNS, tab_style=style) for style in styles]
        return (Tr('Šipka 2. sloupce', 'Column 2 arrow'),
                (Tr('Čím ve hře zasuneš a vysuneš 2. sloupec:', 'What pushes column 2 in and out in game:'),
                 Tr('Nahoře - ouško u prvního řádku.', 'Top – an ear at the first row.'),
                 Tr('Dole - ouško u posledního řádku kratšího sloupce.', 'Bottom – an ear at the last row of the '
                    'shorter column.'),
                 Tr('U kola - šipka vedle ozubeného kola nad lištou.', 'At cog – an arrow next to the cogwheel.'),
                 Tr('Platí, jen když má 2. sloupec tlačítka.', 'Only while column 2 has buttons.')),
                _RailFigures(page, states, (Tr('Nahoře', 'Top'), Tr('Dole', 'Bottom'), Tr('U kola', 'At cog')),
                             styles.index(state.tab_style)))
    if key == 'second':
        states = (rail.RailState((ids[:4], ids[4:7]), mode=rail.MODE_COLUMNS),
                  rail.RailState((ids[:4], ids[4:7]), mode=rail.MODE_COLUMNS, collapsed=True))
        return (Tr('2. sloupec', 'Column 2'),
                (Tr('Zasunout schová 2. sloupec; jeho tlačítka zůstanou a ve hře je do vysunutí najdeš v menu '
                    'Další.', 'Hide pushes column 2 in; its buttons stay and wait in the More menu until it is '
                    'shown again.'),
                 Tr('Vyrovnat rozdělí tlačítka do dvou stejně dlouhých sloupců.',
                    'Balance splits the buttons into two columns of equal length.')),
                _RailFigures(page, states, (Tr('Vysunutý', 'Shown'), Tr('Zasunutý', 'Pushed in')),
                             1 if state.collapsed else 0))
    if key == 'rings':
        return (Tr('Kruhy u minimapy', 'Minimap rings'),
                (Tr('Kruh 1 má 5 míst, kruh 2 dalších 7. Ve hře jdou tlačítka po sobě: kruh 2 se plní, až když '
                    'je kruh 1 plný.', 'Ring 1 has 5 places, ring 2 seven more. In game the buttons follow each '
                    'other: ring 2 fills once ring 1 is full.'),
                 Tr('Ostatní funkce jsou v menu Další (… u minimapy); skryté nejsou nikde.',
                    'Every other function is in the More menu (… at the minimap); hidden ones are nowhere.')),
                _MinimapFigure(page))
    return '', (), None


# One line per setting for the row tooltip of the v5 shell (the "i" bubble has the full help).
STRIP = {
    'layout': Tr('Sloupce = jeden nebo dva sloupce, Strany = strany 1-3.', 'Columns = one or two, Pages = pages 1–3.'),
    'switch': Tr('Kde ve hře přepínáš strany 1-3 lišty.', 'Where you flip pages 1–3 of the rail in game.'),
    'wheel': Tr('Kolečko myši nad lištou přepíná strany.', 'The mouse wheel over the rail flips pages.'),
    'arrow': Tr('Čím ve hře zasuneš a vysuneš 2. sloupec.', 'What pushes column 2 in and out in game.'),
    'second': Tr('Zasunout schová 2. sloupec, Vyrovnat srovná délky.', 'Hide pushes column 2 in, Balance evens them.'),
    'rings': Tr('Kruh 1 má 5 míst, kruh 2 dalších 7.', 'Ring 1 has 5 places, ring 2 seven more.'),
}


# --------------------------------------------------------------------------- reset
def _Names(page, ids):
    return ', '.join(page.Label(action) for action in ids)


def _MinimapDefault(page):
    layout = panel.DefaultLayout(page.mm_known)
    return Tr('Kruh 1: %s; kruh 2 prázdný.', 'Ring 1: %s; ring 2 empty.') % _Names(page, layout)


def _RailDefault(page):
    count = len(rail.DefaultState(page.rl_known).columns[0])
    return (Tr('Strany, %d výchozích tlačítek na straně 1, přepínač Nahoře, kolečko zapnuté.',
               'Pages, %d default buttons on page 1, switcher Top, wheel on.') % count)


BADGES_DEFAULT = Tr('Odznaky, stavy i pulzování zapnuté, u každé funkce znovu odznak i stav; lišta kanálů '
                    'se odepne.', 'Badges, states and pulsing on, badge and state on for every function again; the '
                    'channel bar is unpinned.')
OTHERS = Tr('Ostatní funkce půjdou do menu Další, skryté se znovu ukážou.',
            'Every other function goes to the More menu, hidden ones show again.')


def ResetText(page, scope):
    """(question, [lines]) - exactly what "Obnovit" returns for this choice."""
    if scope == model.SCOPE_PAGE:
        return (Tr('Vrátit celou stránku „Panely tlačítek“ na výchozí?', 'Reset the whole page "Button panels"?'),
                [Tr('Minimapa - %s', 'Minimap – %s') % _MinimapDefault(page),
                 Tr('Lišta - %s', 'Rail – %s') % _RailDefault(page), BADGES_DEFAULT, OTHERS,
                 Tr('Jiné stránky Nastavení se nemění.', 'No other settings page changes.')])
    tab = page.tab
    stays = {model.TAB_MINIMAP: Tr('Lišta u inventáře, odznaky a kanály zůstanou, jak jsou.',
                                   'The inventory rail, badges and channels stay as they are.'),
             model.TAB_RAIL: Tr('Minimapa, odznaky a kanály zůstanou, jak jsou.',
                                'The minimap, badges and channels stay as they are.'),
             model.TAB_BADGES: Tr('Minimapa a lišta u inventáře zůstanou, jak jsou.',
                                  'The minimap and the inventory rail stay as they are.')}[tab]
    question = Tr('Vrátit záložku „%s“ na výchozí?', 'Reset the tab "%s" to its default?') % TAB_NAMES[tab]
    if tab == model.TAB_MINIMAP:
        lines = [_MinimapDefault(page), OTHERS]
    elif tab == model.TAB_RAIL:
        lines = [_RailDefault(page), OTHERS]
    else:
        lines = [BADGES_DEFAULT]
    return question, lines + [stays]


# --------------------------------------------------------------------------- guide
def Arrow(window, kit, start, end):
    """Dashed gold arrow from ``start`` to ``end`` (window coordinates, same y) with a chevron head."""
    widgets = []
    (x0, y), (x1, unused) = start, end
    x = x0
    while x < x1 - 14:
        bar = Bar(window, 0xFFF0C882, 1.0)
        bar.SetPosition(int(x), int(y) - 1)
        bar.SetSize(int(min(8, x1 - 14 - x)), 3)
        bar.SetTop()
        widgets.append(bar)
        x += 13
    head = uikit.Image(window, kit.rel('chevron/right_active.png'), x1 - 12, y - kit.size('chevron/right_active.png')[1] // 2)
    head.SetTop()
    widgets.append(head)
    return widgets


def _Global(page, rect, parent):
    px, py = parent.GetGlobalPosition()
    return rect[0] + px, rect[1] + py, rect[2], rect[3]


def TourSteps(page):
    """[(title, paragraphs, holes (global rects), box position (global), arrow (x0, y, x1) or None)]."""
    window = page.window
    wx, wy = window.GetGlobalPosition()
    content = page.geo['content']
    view = page._ViewRect()
    px, py, pw, ph = page.geo['preview']
    preview = (px + wx, py + wy, pw, ph)
    tabs = _Global(page, page.rects.get('tabs', (0, 0, 0, 0)), getattr(page, 'tabs_parent', None) or content)
    focus = page._PreviewGlobal(page.focus) if page.focus is not None else preview
    catalog = page.rects.get('catalog')
    catalog = _Global(page, catalog, content) if catalog else None
    if catalog is not None and view is not None:
        x0, y0 = catalog[0], max(catalog[1], view[1])
        y1 = min(catalog[1] + catalog[3], view[1] + view[3])
        catalog = (x0, y0, catalog[2], max(0, y1 - y0)) if y1 > y0 else None
    left_x = view[0] if view is not None else wx + 20
    steps = [
        (Tr('Krok 1 / 4 | Co upravuješ', 'Step 1 / 4 · What you edit'),
         (Tr('Nahoře vybereš Minimapu, Lištu u inventáře, nebo Odznaky a kanály.',
             'Pick the Minimap, the Inventory rail, or Badges and channels at the top.'),
          Tr('Náhled vpravo ukazuje právě tu část a mění se hned, stejně jako ve hře.',
             'The preview on the right shows exactly that part and changes at once, like in game.')),
         [tabs, preview], (left_x + 20, tabs[1] + tabs[3] + 16), None),
    ]
    holes = [rect for rect in (catalog, focus) if rect is not None]
    arrow = None
    if catalog is not None:
        arrow = (catalog[0] + catalog[2] + 10, catalog[1] + catalog[3] // 2 - 40, focus[0] - 6)
    steps.append((Tr('Krok 2 / 4 | Přetahování', 'Step 2 / 4 · Drag and drop'),
                  (Tr('Táhni ikonu z katalogu na místo v náhledu vpravo. Zlatý rámeček ukáže, kam dopadne.',
                      'Drag an icon from the catalogue to a place in the preview. A gold frame shows where it lands.'),
                   Tr('Ikonu v náhledu můžeš přesunout jinam nebo ji vrátit do katalogu. Klik na ikonu v katalogu '
                      'ji dá na první volné místo.', 'Move an icon in the preview elsewhere or drag it back to the '
                      'catalogue. A click on a catalogue icon puts it on the first free place.')),
                  holes, (left_x + 20, (view[1] if view is not None else wy) + 70), arrow))
    steps.append((Tr('Krok 3 / 4 | Pravý klik', 'Step 3 / 4 · Right click'),
                  (Tr('Pravým klikem na ikonu ji přesuneš do menu Další, skryješ, nebo vrátíš na výchozí místo.',
                      'Right-click an icon to move it to the More menu, hide it, or put it back on its default '
                      'place.'),
                   Tr('Tam také zapneš nebo vypneš její odznak a stav. Všechny najednou jsou na záložce Odznaky '
                      'a kanály.', 'There you also switch its badge and state. All of them are on the Badges and '
                      'channels tab.')),
                  [focus], (max(wx + 10, focus[0] - 400), focus[1] + 40), None))
    dot = page.info_dots[0] if page.info_dots else None
    reset = getattr(window, 'reset_button', None)
    holes = [rect for rect in ((GlobalRect(dot) if dot is not None else None),
                               (GlobalRect(reset) if reset is not None else None)) if rect is not None]
    box_y = (holes[-1][1] - 230) if holes else wy + 200
    steps.append((Tr('Krok 4 / 4 | Nápověda a obnovení', 'Step 4 / 4 · Help and reset'),
                  (Tr('Když necháš myš chvíli na volbě, ukáže se, co dělá, i s malým náhledem.',
                      'Rest the mouse on a setting for a moment to see what it does, with a small preview.'),
                   Tr('Obnovit stránku se nejdřív zeptá a napíše přesně, co vrátí - jen tuto záložku, nebo celou '
                      'stránku.', 'Reset page asks first and says exactly what it returns – this tab only or the '
                      'whole page.')),
                  holes, (left_x + 20, box_y), None))
    return steps
