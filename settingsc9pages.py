# -*- coding: utf-8 -*-
"""Settings window (c9 v4 2026-10-05, settings v5 the same evening): the menu - 6 groups, 17 pages.

v5 structure (owner, binding): Rychlé nastavení · Grafika (Kvalita a výkon, Svět a počasí, Stíny a efekty + the former
Doprovody, Barvy a jas) · Ovládání (Kamera a myš, Klávesové zkratky) · Rozhraní (Chat a text, Jména a ukazatele,
Kořist a inventář, Panely tlačítek, Upozornění, Vzhled nastavení) · Hra (Souboje a soukromí, Automatický sběr, Fronta
kamenů) · Zvuk. Every page is assembled from the EXISTING Settings A7 pages (settingspages.compose) by control keys, so
behaviour, persistence and reset stay the A7 code; a page lists blocks:

  ('a7', A7 page, keys or None)   controls of an A7 page in the A7 order (its A7 section titles unless sections=False)
  ('section', label)               a section heading
  ('item', dict)                   an explicit row: kind toggle / choice / slider / chips / reset_all / look_*;
                                   keys outside the A7 session belong to settingschat or settingslook
  legacy = A7 page drawn by its own A7 code (old look) inside the new frame (panels, queue - other workstreams)
  custom = page with its own renderer (keys: uisettingsc9keys)

Old links (settingspages.PAGES / ALIASES, the c9 v4 page ids, warp restore, OpenPage('panels')) resolve through
resolve().
"""
import settingslook
import settingspages as pages
from settingslocale import Text as T

NAME_VISIBILITY_OPTIONS = ((2, T('Vždy', 'Always')), (1, T('Při najetí', 'On hover')),
                           (0, T('Skrýt', 'Hide')))
NAME_VISIBILITY_LABELS = (('name_own', T('Vlastní postava', 'Own character')),
                          ('name_players', T('Ostatní hráči', 'Other players')),
                          ('name_monsters', T('Běžné příšery', 'Ordinary monsters')),
                          ('name_stones', T('Meteory', 'Meteors')),
                          ('name_bosses', T('Bossové a polobossové', 'Bosses and minibosses')),
                          ('name_npcs', T('NPC', 'NPCs')),
                          ('name_buff_support', T('Buffky hráčů', 'Player buff companions')),
                          ('name_companions', T('Mazlíčci a následovníci', 'Pets and followers')))
NAME_VISIBILITY_BLOCKS = (('section', T('Názvy nad postavami', 'Names above characters')),
                          ('item', dict(kind='name_actions', key='name_actions', label='', hint=''))) + tuple(
    ('item', dict(kind='choice', key=key, label=label, options=NAME_VISIBILITY_OPTIONS,
                  hint=T('Skrýt vypne celý popisek nad hlavou, včetně úrovně, titulu a cechu. '
                         'Výběr postavy ani okno cíle se nemění.',
                         'Hide removes the overhead label, including level, title and guild. '
                         'Character selection and the target window stay available.')))
    for key, label in NAME_VISIBILITY_LABELS)

CUSTOM_COLOR_KEYS = tuple(key for key, unused in pages.CUSTOM_COLORS)
CHAT_FILTERS = ((1, T('Okolí', 'Local')), (2, T('Skupina', 'Party')), (3, T('Cech', 'Guild')),
                (4, T('Volání', 'Shout')), (5, T('Systém', 'System')), (6, T('Oznámení', 'Notices')),
                (7, T('Kostka', 'Dice')))


def _toggle(key, label, hint=''):
    return ('item', dict(kind='toggle', key=key, label=label, hint=hint))


_ALARM = T('Jen položky s nastaveným budíkem; bez budíků se odpočtové okno nezobrazí.',
           'Only entries with an alarm; without alarms the timer window stays hidden.')
_BELL = T('Zpráva do systémových zpráv (zvonek), jakmile přijde čas.',
          'A message in the system messages (bell) when the time comes.')

# id: label, blocks / legacy / custom, description (right-column placeholder of a page with side=)
PAGES = {
    'quick': dict(label=T('Rychlé nastavení', 'Quick settings'), sections=False, index=False,
                  blocks=(('a7', 'world', ('quality_preset', 'recommended')), ('a7', 'sound', ('sound', 'music')),
                          ('a7', 'interface', ('font', 'names', 'damage')), ('a7', 'game', ('pvp',)),
                          ('section', T('Obnovení', 'Reset')),
                          ('item', dict(kind='reset_all', key='reset_all',
                                        label=T('Obnovit všechna nastavení', 'Reset all settings'),
                                        hint=T('Vrátí volby všech stránek na výchozí hodnoty. Před tím ukáže, co se '
                                               'vrátí a co zůstane.', 'Returns the options of every page to their '
                                               'defaults. It lists what changes first.')))),
                  text=T('Nejčastější volby na jednom místě. Podrobnosti najdeš ve skupinách vlevo.',
                         'The most common options in one place. Details are in the groups on the left.')),
    'performance': dict(label=T('Kvalita a výkon', 'Quality and performance'),
                        blocks=(('a7', 'world', ('quality_preset', 'recommended', 'aa')),
                                ('a7', 'image', ('fps', 'background_fps', 'refresh_hz', 'vsync', 'show_fps'))),
                        text=T('Předvolba kvality světa, vyhlazování a plynulost obrazu.',
                               'World quality preset, antialiasing and smoothness.')),
    'world': dict(label=T('Svět a počasí', 'World and weather'),
                  blocks=(('a7', 'world', ('rain', 'rain_fx', 'fog', 'grass', 'grass_radius', 'lights', 'reflections',
                                           'postprocess', 'sky')),),
                  text=T('Počasí, zeleň, světla a odrazy. Mění atmosféru světa i výkon.',
                         'Weather, greenery, lights and reflections. Changes the atmosphere and performance.')),
    # v5: Doprovody (pets, mounts, support shaman) merged here - the A7 page "Stíny a efekty" always had them.
    'effects': dict(label=T('Stíny a efekty', 'Shadows and effects'),
                    # the tree shadow distance (own section "Stíny stromů") right under the shadows.
                    blocks=(('a7', 'effects', ('shadow_target', 'shadow_quality', 'tree_shadow', 'skills', 'buffs',
                                               'special_effects', 'pet', 'mount', 'support')),),
                    text=T('Kdo vrhá stín, kvalita stínů, dosah stínů stromů, záře kouzel a zobrazení doprovodů.',
                           'Shadow casters, shadow quality, tree shadow distance, spell glows and companions.')),
    'colors': dict(label=T('Barvy a jas', 'Colors and brightness'),
                   blocks=(('a7', 'image', ('color_preset', 'exposure', 'sharpness') + CUSTOM_COLOR_KEYS),),
                   text=T('Barevný profil, jas a doostření. Vlastní profil odkryje další posuvníky.',
                          'Color profile, brightness and sharpening. The custom profile reveals more sliders.')),
    'camera': dict(label=T('Kamera a myš', 'Camera and mouse'), blocks=(('a7', 'image', ('fov', 'camera')),),
                   text=T('Zorné pole a oddálení kamery.', 'Field of view and camera distance.')),
    'keys': dict(label=T('Klávesové zkratky', 'Keybindings'), custom='keys', a7='keys',
                 text=T('Klikni na klávesu akce a stiskni novou; Delete přiřazení zruší. Ukládá se hned.',
                        'Click the key of an action and press a new one; Delete clears it. Saved at once.')),
    'chat': dict(label=T('Chat a text', 'Chat and text'), sections=False,
                 # Velikost rozhraní heads the page (the A7 Rozhraní page has it first too); the
                 # section stays empty and hidden on a client without UI scaling.
                 blocks=(('section', T('Velikost rozhraní', 'Interface scale')), ('a7', 'interface', ('ui_scale',)),
                         ('section', T('Písmo', 'Font')), ('a7', 'interface', ('font',)),
                         ('section', T('Chat', 'Chat')), ('a7', 'interface', ('chat',)),
                         ('item', dict(kind='choice', key='chat_font', label=T('Velikost písma chatu', 'Chat font size'),
                                       options=tuple((size, str(size)) for size in range(12, 19)),
                                       hint=T('Velikost textu v okně chatu, projeví se hned.',
                                              'Text size of the chat window, applies at once.'))),
                         _toggle('chat_timestamps', T('Čas u zpráv', 'Message time'),
                                 T('Před každou zprávou čas příchodu (hodiny:minuty).',
                                   'The arrival time (hours:minutes) before every message.')),
                         ('item', dict(kind='slider', key='chat_opacity', label=T('Pozadí chatu při psaní', 'Chat background while typing'),
                                       hint=T('Jak moc pozadí chatu zakrývá hru, když píšeš (0 % = průhledné).',
                                              'How much the chat background covers the game while typing (0 % = clear).'))),
                         ('item', dict(kind='slider', key='chat_idle_opacity', label=T('Pozadí chatu při hraní', 'Chat background while playing'),
                                       hint=T('Pozadí zpráv, když chat neotevřeš klávesou Enter (0 % = průhledné).',
                                              'The message background when the chat is not opened with Enter (0 % = clear).'))),
                         ('section', T('Záložka „Vše“ zobrazuje', 'The "All" tab shows')),
                         ('item', dict(kind='chips', key='chat_filters', label=T('Záložka „Vše“ zobrazuje', 'The "All" tab shows'),
                                       items=tuple(dict(key='chat_filter_%d' % index, label=label)
                                                   for index, label in CHAT_FILTERS),
                                       hint=T('Druhy zpráv v hlavní záložce chatu. Další záložky nastavíš v chatu '
                                              '(ozubené kolečko).', 'Message types of the main chat tab. Other tabs '
                                              'are set in the chat (cogwheel).'))),
                         ('section', T('Soukromé zprávy', 'Private messages')),
                         _toggle('pm_sound', T('Zvuk nové zprávy', 'New message sound')),
                         _toggle('pm_toast', T('Upozornění na novou zprávu', 'New message notice')),
                         _toggle('pm_preview', T('Náhled textu v upozornění', 'Text preview in the notice')),
                         _toggle('pm_badge', T('Odznak nepřečtených zpráv', 'Unread messages badge'))),
                 text=T('Písmo hry, vzhled a obsah chatu a upozornění na soukromé zprávy.',
                        'Game font, chat look and content and private message notices.')),
    'names': dict(label=T('Jména a ukazatele', 'Names and indicators'),
                  blocks=NAME_VISIBILITY_BLOCKS + (('a7', 'interface', ('quests', 'affects', 'names', 'family_names', 'npc_names', 'outline',
                                               'mob_level', 'mob_aggressive', 'damage', 'damage_size', 'damage_height',
                                               'damage_font', 'damage_normal_color', 'damage_critical_color',
                                               'damage_outline', 'damage_grouping')),
                          _toggle('dps_meter', T('Ukazatel poškození (DPS)', 'Damage meter (DPS)'),
                                  hint=T('Tabulka poškození v okně cíle; otevře se sama při tvém prvním zásahu. '
                                         'Vypnuto = žádná tabulka ani výpočet DPS.',
                                         'The damage table in the target window; it opens by itself on your first '
                                         'hit. Off = no table and no DPS calculation.'))),
                  text=T('Jména postav, informace o nestvůrách, čísla zásahů, ukazatel poškození a ikony.',
                         'Character names, monster information, damage numbers, the damage meter and icons.')),
    'loot': dict(label=T('Kořist a inventář', 'Loot and inventory'),
                 blocks=(('a7', 'interface', ('loot_messages', 'loot_lifetime', 'yang', 'loot_placement', 'edit_loot',
                                              'reset_loot', 'costumes')),),
                 text=T('Zprávy o kořisti, jejich umístění a inventář kostýmů.',
                        'Loot messages, their placement and the costume inventory.')),
    # Panely tlačítek v5: own view uisettingspanelsv5.PanelsPage (CUSTOM_VIEWS), the
    # in-game preview in the right column; custom='panels' is also its A7 page (primary()).
    'panels': dict(label=T('Panely tlačítek', 'Button panels'), custom='panels',
                   side=T('Náhled ve hře', 'In-game preview'),
                   text=T('Náhled vpravo ukazuje, co upravuješ.', 'The preview on the right shows what you edit.')),
    'notifications': dict(label=T('Upozornění', 'Notifications'), sections=False, a7='notifications',
                          blocks=(('section', T('Biolog - další odevzdání', 'Biologist – next submission')),
                                  _toggle('biolog_hud', T('Odpočtové okno', 'Timer window'), _ALARM),
                                  _toggle('biolog_messages', T('Systémová zpráva', 'System message'), _BELL),
                                  ('section', T('Dungeony - další vstup', 'Dungeons – next entry')),
                                  _toggle('dungeon_hud', T('Odpočtové okno', 'Timer window'), _ALARM),
                                  _toggle('dungeon_messages', T('Systémová zpráva', 'System message'), _BELL),
                                  ('section', T('Switchbot - výsledek přepínání', 'Switchbot – switching result')),
                                  _toggle('switchbot_messages', T('Systémová zpráva', 'System message'),
                                          T('Zpráva do systémových zpráv, když Switchbot skončí.',
                                            'A message in the system messages when the Switchbot finishes.'))),
                          text=T('Odpočty a systémové zprávy Biologa, dungeonů a Switchbotu.',
                                 'Timers and system messages of the Biologist, dungeons and the Switchbot.')),
    'look': dict(label=T('Vzhled nastavení', 'Settings look'),
                 blocks=(('item', dict(kind='look_icons', key='row_icons', label=T('Ikony u voleb', 'Option icons'),
                                       hint=T('Malé ikony před názvy voleb. Ikony skupin vlevo zůstávají vždy.',
                                              'Small icons in front of the option names. The group icons on the '
                                              'left always stay.'))),
                         ('item', dict(kind='look_old', key='look_old', label=T('Starý vzhled Nastavení', 'Old settings look'),
                                       hint=T('Přepne na původní okno Nastavení pro porovnání. Zpět vede tlačítko '
                                              '„Nový vzhled“ dole v původním okně.', 'Switches to the original '
                                              'settings window for comparison. "New look" at its bottom returns.'))),
                         ('item', dict(kind='choice', key='channel_bar_style', label=T('Lišta kanálů', 'Channel bar'),
                                       options=(('stepper', T('Krokovač', 'Stepper')), ('list', T('Seznam', 'List'))),
                                       hint=T('Krokovač: šipky CH- a CH+ a řada čísel kanálů. Seznam: kanály pod '
                                              'sebou i s vytížením. Projeví se hned.', 'Stepper: CH- and CH+ arrows '
                                              'and a row of channel numbers. List: the channels one below another '
                                              'with their load. Applies at once.')))),
                 text=T('Vzhled tohoto okna (ikony u voleb, návrat ke starému vzhledu pro porovnání) a podoba '
                        'lišty kanálů.', 'The look of this window (option icons, the old look for comparison) and '
                        'the style of the channel bar.'),
                 # owner 9. 10. 2026 ("zatím"): no "Starý vzhled" for players (settingslook.ALLOW_LEGACY_TOGGLE)
                 text_no_legacy=T('Vzhled tohoto okna (ikony u voleb) a podoba lišty kanálů.',
                                  'The look of this window (option icons) and the style of the channel bar.')),
    'combat': dict(label=T('Souboje a soukromí', 'Combat and privacy'), blocks=(('a7', 'game', None),),
                   text=T('Režim boje a blokování žádostí ostatních hráčů; obojí potvrzuje server.',
                          'Combat mode and blocking requests of other players; the server confirms both.')),
    'pickup': dict(label=T('Automatický sběr', 'Automatic pickup'), blocks=(('a7', 'pickup', None),), chips=True,
                   text=T('Co se sbírá automaticky: způsob sběru, povolání, rozmezí úrovní a druhy vybavení.',
                          'What is picked up automatically: mode, classes, level range and equipment types.')),
    'queue': dict(label=T('Fronta kamenů', 'Stone queue'), custom='queue', a7='queue',  # custom view uisettingsmeteorpage
                  text=T('Velikost kamenů ve světě a vzhled označení; podrobnosti v editoru.',
                         'World stone size and marker look; details in the editor.')),
    'sound': dict(label=T('Hlasitost a hudba', 'Volume and music'), blocks=(('a7', 'sound', None),),
                  text=T('Hlasitost efektů a hudby, hudba v menu a výběr skladby.', 'Effect and music volume, the menu music and the track.')),
}
for _spec in PAGES.values():
    _spec['sources'] = tuple((block[1], block[2]) for block in _spec.get('blocks', ()) if block[0] == 'a7')

# group id, label, sidebar icon, pages. Rychlé nastavení stays first: it is the page the window opens on.
GROUPS = (
    ('quick', T('Rychlé nastavení', 'Quick settings'), 'quick', ('quick',)),
    ('graphics', T('Grafika', 'Graphics'), 'monitor', ('performance', 'world', 'effects', 'colors')),
    ('controls', T('Ovládání', 'Controls'), 'camera', ('camera', 'keys')),
    ('interface', T('Rozhraní', 'Interface'), 'window', ('chat', 'names', 'loot', 'panels', 'notifications', 'look')),
    ('game', T('Hra', 'Game'), 'swords', ('combat', 'pickup', 'queue')),
    ('sound', T('Zvuk', 'Sound'), 'speaker', ('sound',)),
)
ORDER = tuple(page for group in GROUPS for page in group[3])
DEFAULT_PAGE = 'quick'
# Page ids of the c9 v4 trial that v5 merged into another page: id -> (page, highlighted key).
C9_ALIASES = dict(companions=('effects', 'pet'))

# Extra search names: what v5 merged or renamed (the merged page and the row it highlights).
SEARCH_EXTRA = (('effects', 'pet', T('Doprovody', 'Companions')), ('camera', None, T('Myš', 'Mouse')),
                ('chat', 'chat_font', T('Písmo chatu', 'Chat font')),
                ('chat', 'ui_scale', T('Škálování rozhraní', 'UI scaling')),
                ('names', 'dps_meter', T('Měřič poškození', 'DPS meter')))

# Row icons of the c9 icon set (uikittokens.ICONS), shown only with "Ikony u voleb" on (default off).
ICONS = dict(quality_preset='quality', recommended='quality', aa='quality', fps='monitor', background_fps='monitor', refresh_hz='monitor',
             vsync='monitor', show_fps='monitor', rain='drop', rain_fx='rain', fog='fog', grass='grass',
             grass_radius='grass_range', lights='lamp', reflections='waves', postprocess='sun', sky='sky',
             shadow_target='sun', shadow_quality='sun', tree_shadow='sun', skills='swords', buffs='swords', special_effects='swords',
             color_preset='sun', exposure='sun', sharpness='sun', fov='camera', camera='camera', font='font',
             chat='font', names='names', family_names='names', npc_names='names', outline='names',
             mob_level='swords', mob_aggressive='swords', damage='damage', damage_size='damage', quests='info',
             damage_height='damage', damage_font='damage', damage_normal_color='damage', damage_critical_color='damage',
             damage_outline='damage', damage_grouping='damage', dps_meter='damage', ui_scale='window',
             affects='info', loot_messages='info', loot_lifetime='info', yang='info', loot_placement='window',
             costumes='window', pvp='swords', block='shield', pet='info', mount='info', support='info',
             sound='speaker', music='music', track='music', menu_music='music', row_icons='columns', look_old='reset',
             chat_font='font', chat_timestamps='font', chat_opacity='window', chat_idle_opacity='window',
             pm_sound='speaker', pm_toast='info', pm_preview='info', pm_badge='info', reset_all='reset',
             biolog_hud='info', biolog_messages='info', dungeon_hud='info', dungeon_messages='info',
             switchbot_messages='info', pickup_mode='swords')
for _key in CUSTOM_COLOR_KEYS:
    ICONS[_key] = 'sun'

# Controls whose A7 label is empty (it lives in the section title or the search index).
LABELS = dict(quality_preset=T('Kvalita světa', 'World quality'), color_preset=T('Barevný profil', 'Color profile'),
              track=T('Skladba', 'Track'), menu_music=T('Skladba', 'Track'))
# Clearer names in the new window (the A7 label stays searchable): the game font next to the chat font.
RELABEL = dict(font=T('Velikost písma hry', 'Game font size'))


def group_of(page):
    for group in GROUPS:
        if page in group[3]:
            return group
    return GROUPS[0]


def primary(page):
    """The A7 page that owns a new page (warp restore, per-page A7 behaviour such as keys/panels reset)."""
    spec = PAGES[page]
    for key in ('legacy', 'a7'):
        if spec.get(key):
            return spec[key]
    if spec.get('custom') in pages.PAGES:  # a custom page that replaces an A7 page of the same id (queue, panels)
        return spec['custom']
    if spec['sources']:
        return spec['sources'][0][0]
    return 'interface'


def LegacyToggle():
    """The "Starý vzhled" switch is offered (settingslook.ALLOW_LEGACY_TOGGLE; owner 9. 10. 2026: not for now)."""
    return bool(getattr(settingslook, 'ALLOW_LEGACY_TOGGLE', False))


def blocks(page):
    """The blocks of a page as the window shows them: without the "Starý vzhled" row while it is not offered."""
    found = PAGES[page].get('blocks', ())
    if LegacyToggle():
        return found
    return tuple(block for block in found if not (block[0] == 'item' and block[1].get('kind') == 'look_old'))


def text(page):
    """The description of a page (the variant without "Starý vzhled" while it is not offered)."""
    spec = PAGES[page]
    if not LegacyToggle() and 'text_no_legacy' in spec:
        return spec['text_no_legacy']
    return spec.get('text', '')


def items(page):
    """Explicit ('item') rows of a page, chips expanded - for the search index."""
    result = []
    for block in blocks(page):
        if block[0] == 'item':
            result.append(block[1])
            result.extend(block[1].get('items', ()))
    return result


# Where an old A7 page lands as a whole (search by its old title, warp restore, SetOptionType).
A7_HOME = dict(game='combat', pickup='pickup', keys='keys', queue='queue', interface='chat', panels='panels',
               notifications='notifications', image='camera', effects='effects', world='world', sound='sound')


def owner(a7_page, key=None):
    """The new page that shows this A7 page / control; the quick page is never the answer."""
    if key is not None:
        for page in ORDER:
            spec = PAGES[page]
            if not spec.get('index', True):
                continue
            for source, keys in spec['sources']:
                if source == a7_page and (keys is None or key in keys):
                    return page
            if any(item.get('key') == key for item in items(page)):
                return page
    return A7_HOME.get(a7_page)


def resolve(name):
    """Any page name used by the game (new id, c9 v4 id, A7 page, A7 alias) -> (new page, highlighted key) or None."""
    if name in PAGES:
        return name, None
    if name in C9_ALIASES:
        return C9_ALIASES[name]
    if name in pages.ALIASES:
        a7_page, key = pages.ALIASES[name]
        page = owner(a7_page, key)
        return (page, key) if page else None
    if name in pages.PAGES:
        page = owner(name)
        return (page, None) if page else None
    return None
