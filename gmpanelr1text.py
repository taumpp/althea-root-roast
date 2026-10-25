# -*- coding: utf-8 -*-
"""Czech texts of the R1 GM panel (uigmpanelr1), with diacritics.

The server describes the panel in ASCII only (gm_panel_catalog.h: IsRowText lets characters 32-126 through), so the
names read "Umlcet", "Hraci". Owner 8. 10. 2026 (GM panel B2): the panel shows Czech with diacritics from this
client table. It is presentation only: what a session may use, which inputs an action takes and whether it asks
for confirmation still come from the server catalogue and mask (gmpanelcatalog), and the server decides every
request. An action is named from here only while the server still describes that id with the ASCII label recorded
here ("server"), so a renumbered or renamed action falls back to the server's own text; an unknown id always does.

Sources: the server's panel catalogue (gm_panel_catalog.h: ids, labels, field labels, result texts) and gm_panel.cpp
(hardMinimumLevel, protectsTargetGM, the result and error messages) as of 8. 10. 2026. No client imports: the
module also runs on Python 2 (bytes from the client are decoded by Unicode()).
"""
import re

# GM levels of the server (GM_LOW_WIZARD .. GM_IMPLEMENTOR) and the names it sends for them.
ROLES = {
    0: u'Hráč', 1: u'Low Wizard', 2: u'Wizard', 3: u'High Wizard', 4: u'God', 5: u'Implementor',
}

CATEGORIES = {
    1: u'Podpora', 2: u'Hráči', 3: u'Moderace', 4: u'Oznámení', 5: u'Svět',
}
# gmpanelcatalog.PLAIN_CATEGORY: actions the catalogue does not describe (offered by number).
PLAIN_CATEGORY_LABEL = u'Ostatní'

# Inputs that read the same for every action (and the labels of an undescribed action).
FIELDS = {
    'target': u'Jméno hráče',
    'argument': u'Text',
    'value': u'Hodnota',
    'secondary': u'Druhá hodnota',
    'reason': u'Důvod (zapisuje se do auditu)',
    'map': u'Cílová mapa',
}

# Helpers of the form; the server still receives the number of seconds / the count.
MUTE_PRESETS = ((60, u'1 min'), (600, u'10 min'), (3600, u'1 h'), (86400, u'1 den'), (604800, u'7 dní'))

# Detail hráče (PLAYER_LOOKUP): the "Detail" button beside the player field runs it; named only while the server
# still describes this id as recorded in ACTIONS.
DETAIL_ACTION = 17

# The "Údržba" section of the list: not a server action. It types the Implementor-only chat command
# /maintenance (gmmaintenance); the texts of the form are here.
MAINTENANCE_SECTION = u'Údržba'
MAINTENANCE_LABEL = u'Údržba serveru'
MAINTENANCE_TITLE = u'ÚDRŽBA SERVERU'
MAINTENANCE_DESCRIPTION = (u'Vyhlásí odpočet všem hráčům na všech kanálech. V čase začátku je odpojí a zavře '
                           u'přihlášení.')
MAINTENANCE_START_LABEL = u'Za kolik minut *'
MAINTENANCE_DURATION_LABEL = u'Jak dlouho (min) *'
MAINTENANCE_REASON_LABEL = u'Důvod pro hráče (volitelně)'
MAINTENANCE_REASON_HINT = u'Vlastní text bez diakritiky, nebo tlačítko'
MAINTENANCE_PREVIEW_LABEL = u'Hráči uvidí v chatu'
MAINTENANCE_START = u'Vyhlásit údržbu'
MAINTENANCE_STOP = u'Zrušit údržbu'
MAINTENANCE_ASK_START = u'Vyhlásit údržbu za %s na %s?'
MAINTENANCE_ASK_START_NOTE = u'Hráči budou v čase začátku odpojeni.'
MAINTENANCE_ASK_STOP = u'Zrušit ohlášenou údržbu?'
MAINTENANCE_ASK_STOP_NOTE = u'Hráči se to dozvědí; zavřené přihlášení se znovu otevře.'
MAINTENANCE_YES_START = u'Ano, vyhlásit'
MAINTENANCE_YES_STOP = u'Ano, zrušit'
MAINTENANCE_BACK = u'Zpět'
MAINTENANCE_SENT = u'Příkaz odeslán. Výsledek je v chatu.'
MAINTENANCE_FAILED = u'Příkaz se nepodařilo odeslat.'

# One entry per server action id (EGMPanelAction). Keys:
#   server       the ASCII label the server sends for this id (gm_panel_catalog.h kActions)
#   label        Czech name; description: Czech description
#   fields       Czech labels of inputs whose label differs per action
#   role         hardMinimumLevel of gm_panel.cpp (the server may still ask more for the command itself)
#   protects     protectsTargetGM: a GM of the same or a higher level is protected
#   execute      label of the main button
#   confirm      question of the second step ('%(target)s', '%(entity)s', '%(count)s', '%(argument)s')
#   presets      'mute' = the duration presets on the value; count = the -/+ bound of the secondary value
#   preview      True = the text is shown as a preview of the announcement
ACTIONS = {
    1: {'server': 'Online hraci', 'label': u'Online hráči', 'role': 1,
        'description': u'Vypíše aktuální počet hráčů online.', 'execute': u'Vypsat'},
    2: {'server': 'Jit k hraci', 'label': u'Jít k hráči', 'role': 1,
        'description': u'Teleportuje tvou postavu k vybranému hráči.', 'execute': u'Jít k hráči'},
    3: {'server': 'Privolat', 'label': u'Přivolat', 'role': 1, 'protects': True,
        'description': u'Přivolá hráče na tvou aktuální pozici.', 'execute': u'Přivolat hráče',
        'confirm': u'Opravdu přivolat hráče %(target)s?'},
    4: {'server': 'Odpojit', 'label': u'Odpojit', 'role': 1, 'protects': True,
        'description': u'Odpojí vybraného hráče ze hry.', 'execute': u'Odpojit hráče',
        'confirm': u'Opravdu odpojit hráče %(target)s?'},
    5: {'server': 'Umlcet', 'label': u'Umlčet', 'role': 3, 'protects': True,
        'description': u'Zakáže hráči chat na 60 sekund až 7 dní.', 'execute': u'Umlčet hráče',
        'fields': {'value': u'Délka v sekundách'}, 'presets': 'mute'},
    6: {'server': 'Zrusit umlceni', 'label': u'Zrušit umlčení', 'role': 3, 'protects': True,
        'description': u'Okamžitě zruší blokaci chatu.', 'execute': u'Zrušit umlčení'},
    7: {'server': 'Neviditelnost', 'label': u'Neviditelnost', 'role': 1,
        'description': u'Zapne nebo vypne GM neviditelnost.', 'execute': u'Přepnout'},
    8: {'server': 'Zprava mapy', 'label': u'Zpráva mapy', 'role': 1,
        'description': u'Pošle oznámení hráčům na aktuální mapě.', 'execute': u'Poslat na mapu',
        'fields': {'argument': u'Text zprávy'}, 'preview': True},
    9: {'server': 'Globalni zprava', 'label': u'Globální zpráva', 'role': 3,
        'description': u'Pošle globální oznámení.', 'execute': u'Poslat všem',
        'fields': {'argument': u'Text zprávy'}, 'preview': True},
    10: {'server': 'Velka zprava', 'label': u'Velká zpráva', 'role': 3,
         'description': u'Pošle velké globální oznámení.', 'execute': u'Poslat všem',
         'fields': {'argument': u'Text zprávy'}, 'preview': True},
    11: {'server': 'Event flagy', 'label': u'Event flagy', 'role': 1,
         'description': u'Vypíše aktuální event flagy do chatu.', 'execute': u'Vypsat'},
    12: {'server': 'Nastavit flag', 'label': u'Nastavit flag', 'role': 3,
         'description': u'Nastaví serverový event flag.', 'execute': u'Nastavit flag',
         'fields': {'argument': u'Název event flagu', 'value': u'Hodnota'},
         'confirm': u'Opravdu nastavit event flag %(argument)s?'},
    13: {'server': 'Purge okoli', 'label': u'Purge okolí', 'role': 2,
         'description': u'Odstraní moby a NPC v okolí; nikdy nepoužije variantu purge all.',
         'execute': u'Vyčistit okolí', 'confirm': u'Opravdu odstranit moby a NPC v okolí?'},
    14: {'server': 'Spawn mob', 'label': u'Spawn moba', 'role': 3,
         'description': u'Vytvoří moby u tvé postavy.', 'execute': u'Spawn',
         'fields': {'value': u'Monstrum / VNUM', 'secondary': u'Počet (1–20)'}, 'count': 20,
         'confirm': u'Opravdu vytvořit %(count)s× %(entity)s?'},
    15: {'server': 'Spawn skupiny', 'label': u'Spawn skupiny', 'role': 3,
         'description': u'Vytvoří skupinu mobů u tvé postavy.', 'execute': u'Spawn skupiny',
         'fields': {'value': u'VNUM skupiny'}, 'confirm': u'Opravdu vytvořit skupinu mobů?'},
    16: {'server': 'Vytvorit item', 'label': u'Vytvořit předmět', 'role': 4,
         'description': u'Vytvoří předmět do inventáře GM postavy.', 'execute': u'Vytvořit',
         'fields': {'value': u'Předmět / VNUM', 'secondary': u'Počet (1–200)'}, 'count': 200,
         'confirm': u'Opravdu vytvořit %(count)s× %(entity)s?'},
    17: {'server': 'Detail hrace', 'label': u'Detail hráče', 'role': 1,
         'description': u'Zjistí, zda je hráč online, jeho kanál, mapu, pozici a stav postavy.',
         'execute': u'Zjistit detail'},
    18: {'server': 'Prohlednout vybavu', 'label': u'Prohlédnout výbavu', 'role': 1,
         'description': u'Otevře prohlížeč výbavy postavy na stejném kanálu.', 'execute': u'Prohlédnout'},
    19: {'server': 'Jit na souradnice', 'label': u'Jít na souřadnice', 'role': 1,
         'description': u'Přemístí GM na souřadnice aktuální mapy.', 'execute': u'Jít na souřadnice',
         'fields': {'value': u'X v metrech', 'secondary': u'Y v metrech'}},
    20: {'server': 'Vylecit hrace', 'label': u'Vyléčit hráče', 'role': 2,
         'description': u'Doplní živé postavě na stejném kanálu HP a SP.', 'execute': u'Vyléčit hráče',
         'confirm': u'Opravdu vyléčit hráče %(target)s?'},
    21: {'server': 'Zabit hrace', 'label': u'Zabít hráče', 'role': 3, 'protects': True,
         'description': u'Zabije postavu na stejném kanálu; stejně vysoký nebo vyšší GM je chráněn.',
         'execute': u'Zabít hráče', 'confirm': u'Opravdu zabít hráče %(target)s?'},
    22: {'server': 'Nastavit level', 'label': u'Nastavit level', 'role': 4, 'protects': True,
         'description': u'Nastaví level, přepočítá staty a vynuluje aktuální EXP.', 'execute': u'Nastavit level',
         'fields': {'value': u'Nový level'}, 'confirm': u'Opravdu změnit level hráče %(target)s?'},
    23: {'server': 'Obnovit okoli', 'label': u'Obnovit okolí', 'role': 2,
         'description': u'Znovu načte regen mobů a NPC jen v okolí GM.', 'execute': u'Obnovit okolí',
         'confirm': u'Opravdu znovu načíst regen v okolí?'},
    24: {'server': 'Teleport na mapu', 'label': u'Teleport na mapu', 'role': 1,
         'description': u'Přemístí GM na bezpečný start vybrané mapy.', 'execute': u'Teleportovat'},
}

# Results the server sends in its own (ASCII) wording or in English (gm_panel_catalog.h kResultTexts,
# gm_panel.cpp, gm_action_service.cpp). Anything else is shown as the server wrote it.
RESULTS = {
    'Opravneni byla nactena ze serveru.': u'Oprávnění byla načtena ze serveru.',
    'Akce byla prijata. Podrobny vysledek je v chatu.': u'Akce byla přijata. Podrobný výsledek je v chatu.',
    'Tvoje serverova role tuto akci nepovoluje.': u'Tvoje serverová role tuto akci nepovoluje.',
    'Pred dalsi akci chvili pockej.': u'Před další akcí chvíli počkej.',
    'Pozadavek uz byl zpracovan nebo je zastaraly.': u'Požadavek už byl zpracován nebo je zastaralý.',
    'Jmeno postavy neni platne.': u'Jméno postavy není platné.',
    'Tuto akci nelze pouzit na vlastni postavu.': u'Tuto akci nelze použít na vlastní postavu.',
    'Nelze zasahnout GM se stejnou nebo vyssi pravomoci.': u'Nelze zasáhnout GM se stejnou nebo vyšší pravomocí.',
    'Souradnice musi byt mezi 0 a 100000 metry.': u'Souřadnice musí být mezi 0 a 100000 metry.',
    'Index musi oznacovat verejnou runtime mapu.': u'Index musí označovat veřejnou runtime mapu.',
    'Prohlizeni vybavy neni v tomto serverovem buildu dostupne.':
        u'Prohlížení výbavy není v tomto serverovém buildu dostupné.',
    'A text field is not terminated.': u'Textové pole není ukončené.',
    'Unknown GM panel action.': u'Neznámá akce GM panelu.',
    'Request id must be non-zero.': u'Číslo požadavku nesmí být nula.',
    'Control characters are not allowed.': u'Řídicí znaky nejsou povolené.',
    'This action requires an argument.': u'Akce potřebuje vyplněný text.',
    'This action requires a reason of at least 3 characters.': u'Akce potřebuje důvod alespoň o 3 znacích.',
    'This action cannot target a name containing a double quote.': u'Jméno nesmí obsahovat uvozovky.',
    'Mute duration must be between 60 seconds and 7 days.': u'Délka umlčení musí být 60 sekund až 7 dní.',
    'Event flag name may contain only letters, numbers, underscore and dot.':
        u'Název flagu smí obsahovat jen písmena, číslice, podtržítko a tečku.',
    'Purge requires explicit confirmation.': u'Purge vyžaduje výslovné potvrzení.',
    'Group vnum is required.': u'Zadej VNUM skupiny.',
    'Unsupported GM panel action.': u'Nepodporovaná akce GM panelu.',
    'Generated command is too long.': u'Vytvořený příkaz je příliš dlouhý.',
    'Monster VNUM and count (1-20) are required.': u'Zadej VNUM monstra a počet 1–20.',
    'Item VNUM and count (1-200) are required.': u'Zadej VNUM předmětu a počet 1–200.',
    'Level change rejected: passage incomplete or level outside server limit.':
        u'Změna levelu odmítnuta: chybí průchod nebo je level mimo limit serveru.',
    'Character is unavailable.': u'Postava není dostupná.',
    'Item VNUM must be greater than zero.': u'VNUM předmětu musí být větší než nula.',
    'The item could not be placed into the inventory.': u'Předmět se nevešel do inventáře.',
    'Monster count must be between 1 and 20.': u'Počet monster musí být 1–20.',
    'The server could not find a valid nearby spawn position.': u'Server v okolí nenašel místo pro spawn.',
}
# The formatted results; groups are passed through as written.
RESULT_PATTERNS = (
    (r'^(.+) is not online\.$', u'%s není online.'),
    (r'^(.+) is online on channel (\d+), map (-?\d+)\. Go to the player and retry\.$',
     u'%s je online na kanálu %s, mapa %s. Jdi za hráčem a zkus to znovu.'),
    (r'^(.+) is online on channel (\d+), map (-?\d+); detailed status is on that core\.$',
     u'%s je online na kanálu %s, mapa %s; podrobný stav zná jen ten kanál.'),
    (r'^(.+): level (-?\d+), job (\d+), channel (\d+), map (-?\d+), pos (-?\d+)/(-?\d+), HP (-?\d+)/(-?\d+)\.$',
     None),
    (r'^Equipment window opened for (.+)\.$', u'Výbava hráče %s je otevřená.'),
    (r'^(.+) was set to level (-?\d+)\.$', u'%s má nyní level %s.'),
    (r'^Item count must be between 1 and (\d+)\.$', u'Počet předmětů musí být 1–%s.'),
    (r'^Item VNUM (\d+) does not exist\.$', u'Předmět VNUM %s neexistuje.'),
    (r'^Monster VNUM (\d+) does not exist\.$', u'Monstrum VNUM %s neexistuje.'),
    (r'^Created (\d+)x (.+) \(VNUM (\d+)\) in your inventory\.$', u'Vytvořeno %s× %s (VNUM %s) v inventáři.'),
    (r'^Spawned (\d+)/(\d+) x (.+) \(VNUM (\d+)\)\.$', u'Spawnuto %s/%s × %s (VNUM %s).'),
)
_LOOKUP = re.compile(RESULT_PATTERNS[3][0])
_ONLINE_ELSEWHERE = re.compile(r'^(.+) is online on channel (\d+), map (-?\d+)[.;]')
_OFFLINE = re.compile(RESULT_PATTERNS[0][0])
_PATTERNS = [(re.compile(pattern), text) for pattern, text in RESULT_PATTERNS]

# The panel's own status lines (uigmpanel.GMPanelWindow; the R1 panel runs the same request code).
STATUS = {
    'Nacitam opravneni ze serveru...': u'Načítám oprávnění ze serveru…',
    'Pozadavek se nepodarilo odeslat.': u'Požadavek se nepodařilo odeslat.',
    'Pozadavek byl odeslan serveru...': u'Požadavek byl odeslán serveru…',
    'Ciselna pole musi obsahovat platne cele cislo.': u'Číselná pole musí obsahovat platné celé číslo.',
    'Nejprve vyber cilovou mapu.': u'Nejprve vyber cílovou mapu.',
    'Vypln jmeno hrace.': u'Vyplň jméno hráče.',
    'Vypln argument akce.': u'Vyplň text akce.',
    'Vypln duvod alespon o trech znacich.': u'Vyplň důvod alespoň o třech znacích.',
}
SEND_FAILED = 'Pozadavek se nepodarilo odeslat.'
SENT = 'Pozadavek byl odeslan serveru...'
# Status lines that are a mistake in the form (shown in the form's error colour).
FORM_ERRORS = ('Ciselna pole musi obsahovat platne cele cislo.', 'Nejprve vyber cilovou mapu.',
               'Vypln jmeno hrace.', 'Vypln argument akce.', 'Vypln duvod alespon o trech znacich.',
               'Pozadavek se nepodarilo odeslat.')

JOBS = {0: u'Válečník', 1: u'Ninja', 2: u'Sura', 3: u'Šaman', 4: u'Lycan'}

_FOLD = {u'á': u'a', u'č': u'c', u'ď': u'd', u'é': u'e', u'ě': u'e', u'í': u'i', u'ň': u'n', u'ó': u'o',
         u'ř': u'r', u'š': u's', u'ť': u't', u'ú': u'u', u'ů': u'u', u'ý': u'y', u'ž': u'z'}


def Unicode(text):
    """A text of the client as unicode: a Python 2 client hands bytes (UTF-8, older locale text cp1250)."""
    if text is None:
        return u''
    if isinstance(text, bytes):
        for encoding in ('utf-8', 'cp1250'):
            try:
                return text.decode(encoding)
            except UnicodeDecodeError:
                pass
        return text.decode('latin-1')
    try:
        return u'%s' % text
    except Exception:
        return u''


def Fold(text):
    """Lower case without diacritics: the key of the action search ("umlcet" finds "Umlčet")."""
    return u''.join(_FOLD.get(ch, ch) for ch in Unicode(text).lower())


def _Entry(action, info):
    """This table's entry for an action, only while the server describes that id with the recorded label."""
    entry = ACTIONS.get(action)
    if entry is None or info is None or info.get('plain'):
        return None
    if Unicode(info.get('label')) != Unicode(entry['server']):
        return None
    return entry


def IsKnown(action, info):
    return _Entry(action, info) is not None


def ActionLabel(action, info):
    entry = _Entry(action, info)
    return entry['label'] if entry else Unicode(info.get('label') if info else u'#%d' % action)


def Description(action, info):
    entry = _Entry(action, info)
    return entry['description'] if entry else Unicode(info.get('description') if info else u'')


def FieldLabel(action, info, field):
    """Czech label of an input: the action's own, the shared one (target, reason, map), else the server's."""
    entry = _Entry(action, info)
    if entry is not None:
        own = entry.get('fields', {}).get(field)
        if own:
            return own
        if field in ('target', 'reason', 'map'):
            return FIELDS[field]
        return Unicode(info.get('labels', {}).get(field, FIELDS.get(field, field)))
    if info and info.get('plain'):
        return FIELDS.get(field, Unicode(field))
    return Unicode((info or {}).get('labels', {}).get(field, FIELDS.get(field, field)))


def ExecuteLabel(action, info):
    entry = _Entry(action, info)
    return entry.get('execute', entry['label']) if entry else u'Spustit akci'


def MinimumRole(action, info):
    """GM level the server needs at least for this action, or None when this table does not know the action."""
    entry = _Entry(action, info)
    return entry.get('role') if entry else None


def ProtectsGM(action, info):
    entry = _Entry(action, info)
    return bool(entry and entry.get('protects'))


def Presets(action, info):
    entry = _Entry(action, info)
    return entry.get('presets') if entry else None


def CountLimit(action, info):
    """Upper bound of the -/+ count helper, or None (no helper)."""
    entry = _Entry(action, info)
    return entry.get('count') if entry else None


def HasPreview(action, info):
    entry = _Entry(action, info)
    return bool(entry and entry.get('preview'))


def Question(action, info, target=u'', entity=u'', count=0, argument=u''):
    """The question of the second step."""
    entry = _Entry(action, info)
    values = {'target': Unicode(target) or u'?', 'entity': Unicode(entity) or u'?', 'count': count,
              'argument': Unicode(argument) or u'?'}
    if entry and entry.get('confirm'):
        return entry['confirm'] % values
    return u'Opravdu provést akci „%s“?' % ActionLabel(action, info)


def CategoryLabel(category, serverLabel):
    if category == 0:
        return PLAIN_CATEGORY_LABEL
    known = CATEGORIES.get(category)
    if known is not None and Fold(known) == Fold(serverLabel):
        return known
    return Unicode(serverLabel)


def RoleName(level, serverName=None):
    """The name of a GM level; the server's name when it differs from the table (a renamed role)."""
    known = ROLES.get(level)
    if known is not None and (serverName is None or Fold(known) == Fold(serverName)
                              or serverName == 'Role %d' % level):
        return known
    return Unicode(serverName) if serverName is not None else u'Role %d' % level


def RoleTag(level):
    """The minimum role chip ("High Wizard+")."""
    return u'%s+' % ROLES.get(level, u'Role %d' % level)


def Result(message):
    """A server result in Czech with diacritics, or the message as written."""
    text = Unicode(message)
    known = RESULTS.get(text)
    if known is not None:
        return known
    for pattern, czech in _PATTERNS:
        found = pattern.match(text)
        if found is None:
            continue
        if czech is None:
            name, level, job, channel, mapIndex, x, y, hp, maxHp = found.groups()
            return u'%s: level %s, %s, kanál %s, mapa %s, pozice %s/%s, HP %s/%s.' % (
                name, level, JOBS.get(int(job), u'povolání %s' % job), channel, mapIndex, x, y, hp, maxHp)
        return czech % found.groups()
    return text


def Status(message):
    text = Unicode(message)
    return STATUS.get(text) or Result(text)


def PlayerCard(message):
    """What a Detail reply tells about a player: {'name', 'online', 'level', 'job', 'channel', 'map'} or None.
    Only the replies the client already gets (gm_panel.cpp PLAYER_LOOKUP / FindLocalTarget); no new server reply."""
    text = Unicode(message)
    found = _LOOKUP.match(text)
    if found:
        name, level, job, channel, mapIndex = found.groups()[:5]
        return {'name': name, 'online': True, 'level': int(level), 'job': JOBS.get(int(job)),
                'channel': int(channel), 'map': int(mapIndex)}
    found = _ONLINE_ELSEWHERE.match(text)
    if found:
        name, channel, mapIndex = found.groups()
        return {'name': name, 'online': True, 'level': None, 'job': None, 'channel': int(channel),
                'map': int(mapIndex)}
    found = _OFFLINE.match(text)
    if found:
        return {'name': found.group(1), 'online': False, 'level': None, 'job': None, 'channel': None,
                'map': None}
    return None


def Duration(seconds):
    """A mute length for the history ("10 min", "1 h 30 min", "2 dny")."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return u''
    for value, label in MUTE_PRESETS:
        if seconds == value:
            return label
    if seconds < 60:
        return u'%d s' % seconds
    if seconds < 3600:
        return u'%d min' % (seconds // 60)
    if seconds < 86400:
        hours, minutes = divmod(seconds // 60, 60)
        return u'%d h %d min' % (hours, minutes) if minutes else u'%d h' % hours
    days = seconds // 86400
    return u'%d %s' % (days, u'den' if days == 1 else (u'dny' if days < 5 else u'dní'))
