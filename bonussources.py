# -*- coding: utf-8 -*-
"""Odkud bonus pochází (jen data klienta).

Rozpad jednoho řádku okna Bonusy (uicharacterdetails.bonus_list: [apply, point, label, percent]) na zdroje, které
klient zná sám:

  Výbava    nasazené předměty po kusech (proto + náhodné + bonusy předmětu, šerpa s absorpcí), kameny ve výbavě
            zvlášť, talismany a Srdce talismanu (jen když je aktivní); "Ostatní z výbavy" = serverový součet výbavy
            (/equipment_bonuses) minus kusy, tedy absorpce aury, rarita, perly, dračí kameny
  Mount     pečeť mounta (affect 533, jméno a ikona z kostýmu jezdeckého zvířete), výbava mounta a jádro (jen
            s nasazeným skinem, stejně jako server)
  Mazlíček  nasazený mazlíček a jeho affecty (545 růstový mazlíček, 546 srdce mazlíčka)
  Efekty    lektvary, rosy, elixíry, požehnání, buffy (Buffka = podpůrné schopnosti 194-198) ze seznamu affectů
  Biolog    odměny Biologa (AFFECT_COLLECT 515)
  Pasivky   PvM osobní hodnoty (pvmpersonal): hodnota útoku, obrana, odolnost proti běžným příšerám

Zbytek do celkové serverové hodnoty (characterbonuses.totals) je řádek "Ostatní (server)", takže součet vždy sedí.

Krok 2: když server pošle přesný rozpad řádku (/bonus_sources -> BonusSourcesV1, ``server``), použije se místo odhadu
klienta (ServerBuild). Klient jen pojmenuje zdroj z vlastních dat (předmět ve slotu, affect, Pasivka) a přidá skupiny,
které sám nezná: Strom schopností, Živelná výprava (odměny větví mounta), Cech, Album mazlíčků, Trvalé úkoly,
Rarita, Mudrc, Družina, Svatba, Event, Základ.
"Ostatní (server)" zůstane jen pro nenulový RESIDUAL. Bez odpovědi (starý server) platí krok 1.
Odolnost proti běžným příšerám se na serveru skládá násobně (Resistance v character_bonus_snapshot.h): rozpad pak
ukazuje sčítací část a Pasivky zvlášť se vzorcem.

Nic se nepočítá jinak než na serveru; kde klient pravidlo nezná, rozdíl zůstane ve zbytku. Modul nehází výjimky:
chybějící data = méně řádků, nikdy pád okna.
"""

SCALE = 1000000

# Skupiny v pořadí náhledu 2-A.
GROUPS = (
    ('equipment', u'Výbava'),
    ('mount', u'Mount'),
    # Jen se serverem: odměna větve Živelné výpravy (mount systém, EXPEDITION:<živel>).
    ('expedition', u'Živelná výprava'),
    ('pet', u'Mazlíček'),
    ('effects', u'Efekty'),
    # Časové zdroje (lektvar, rosa, Buffi, buff): vlastní rozklikávací skupina „Efekty (dočasné)“ (GroupTitle).
    ('temporary', None),
    ('biolog', u'Biolog'),
    ('passive', u'Pasivky'),
    # Jen s rozpadem ze serveru (BonusSourcesV1, krok 2).
    ('talent', u'Strom schopností'),
    ('guild', u'Cech'),
    ('album', u'Album mazlíčků'),
    ('hunt', u'Trvalé úkoly'),
    ('rarity', u'Rarita'),
    ('sage', u'Mudrc'),
    ('attrbuff', u'Posílení výbavy'),
    ('party', u'Družina'),
    ('marriage', u'Svatba'),
    ('event', u'Event'),
    ('base', u'Základ postavy'),
    ('server', u'Ostatní (server)'),
)
GROUP_TITLES = dict(GROUPS)

# Nasazené buňky (offset od player.EQUIPMENT_SLOT_START, server common/length.h EWearPositions) -> (popis, skupina).
# 9 šípy (vyřazeno), 21 kostým mounta (bonusy jdou přes pečeť = affect 533), 34-45 výbava Buffky (bonusy nemá hráč).
WEAR = {
    0: (u'Zbroj', 'equipment'),
    1: (u'Helma', 'equipment'),
    2: (u'Boty', 'equipment'),
    3: (u'Náramek', 'equipment'),
    4: (u'Zbraň', 'equipment'),
    5: (u'Náhrdelník', 'equipment'),
    6: (u'Náušnice', 'equipment'),
    7: (u'Unikátní předmět', 'equipment'),
    8: (u'Unikátní předmět', 'equipment'),
    10: (u'Štít', 'equipment'),
    11: (u'Výbava', 'equipment'), 12: (u'Výbava', 'equipment'), 13: (u'Výbava', 'equipment'),
    14: (u'Výbava', 'equipment'), 15: (u'Výbava', 'equipment'), 16: (u'Výbava', 'equipment'),
    17: (u'Výbava', 'equipment'), 18: (u'Výbava', 'equipment'),
    19: (u'Kostým', 'equipment'),
    20: (u'Kostým vlasů', 'equipment'),
    22: (u'Šerpa', 'equipment'),
    23: (u'Kostým zbraně', 'equipment'),
    24: (u'Kostým s aurou', 'equipment'),
    25: (u'Efekt zbraně', 'equipment'),
    26: (u'Efekt zbroje', 'equipment'),
    27: (u'Vzhled šerpy', 'equipment'),
    28: (u'Mazlíček', 'pet'),
    29: (u'Prsten', 'equipment'),
    30: (u'Prsten', 'equipment'),
    31: (u'Opasek', 'equipment'),
    32: (u'Talisman', 'equipment'),
    33: (u'Rukavice', 'equipment'),
    46: (u'Výbava mounta', 'mount'),
    47: (u'Výbava mounta', 'mount'),
    48: (u'Výbava mounta', 'mount'),
    49: (u'Výbava mounta', 'mount'),
    50: (u'Jádro mounta', 'mount'),
    51: (u'Srdce talismanu', 'equipment'),
    52: (u'Talisman', 'equipment'),
    53: (u'Talisman', 'equipment'),
    54: (u'Talisman', 'equipment'),
    55: (u'Talisman', 'equipment'),
}
WEAR_MOUNT_SKIN = 21
WEAR_PET = 28
WEAR_SASH = 22
WEAR_TALISMAN_HEART = 51
MOUNT_GEAR = (46, 47, 48, 49, 50)

# Affecty (server game/src/affect.h).
AFFECT_COLLECT = 515          # Biolog
AFFECT_MOUNT_BONUS = 533      # pečeť mounta
AFFECT_GROWTH_PET = 545
AFFECT_PET_HEART = 546
DRAGON_SOUL_AFFECTS = (540, 541, 542, 543)
# Buffka sesílá podpůrné verze šamanských buffů (uiaffectshower.SupportSkillTooltip).
BUFFI_SKILLS = {194: 94, 195: 95, 196: 96, 197: 110, 198: 111}
# PvM osobní hodnoty nahrazují tyto staré příspěvky schopností (server pvm_personal.cpp Legacy*Contribution).
LEGACY_ATTACK_SKILLS = (4, 63, 79, 111)
LEGACY_DEFENSE_SKILLS = (19, 65, 79)
FOREVER = 365 * 24 * 3600

ICON_BIOLOG = 'd:/ymir work/ui/game/crimson_ember/biolog/research/chaegirab_header.png'


def _module(name):
    # The game imports some modules with capitals (game.py: uiAffectShower). A second import under another
    # spelling would create a separate, empty copy (affectDict without any affect -> every effect "trvale"),
    # so an already loaded module of the same name wins.
    import sys
    lowered = name.lower()
    loaded = [module for key, module in list(sys.modules.items())
              if module is not None and key.lower() == lowered]
    others = [module for module in loaded if getattr(module, '__name__', name) != name]
    if others or loaded:
        return (others or loaded)[0]
    try:
        return __import__(name)
    except Exception:
        return None


def _const(module, name, default=None):
    return getattr(module, name, default) if module is not None else default


def AffectKey(shower, affect, point):
    """Klíč affectDict lišty efektů pro serverový typ affectu (stejně jako BINARY_NEW_AddAffect): obchod
    a spotřební lektvary jsou pod klíčem podle bodu, některé typy pod klientským číslem. Funkce bere přímo
    z lišty efektů (ResolveAffectKey, AffectToRealIndex), takže mapování zůstává na jednom místě."""
    cls = getattr(shower, 'AffectShower', None) if shower is not None else None
    key = affect
    for name, args in (('ResolveAffectKey', (point,)), ('AffectToRealIndex', ())):
        fn = getattr(cls, '__dict__', {}).get(name) if cls is not None else None
        if fn is not None:
            try:
                key = fn(cls, key, *args)
            except Exception:
                return affect
    return key


def ShortLeft(seconds, locale=None):
    # Zbývající čas do úzké poznámky: pod den jako TimeLeft (09:35, 1:59:00), jinak dny a hodiny s jednotkami
    # z locale (DAY, HOUR) jako v liště efektů.
    seconds = max(0, int(seconds))
    days, rest = divmod(seconds, 24 * 3600)
    day = getattr(locale, 'DAY', None) if locale is not None else None
    hour = getattr(locale, 'HOUR', None) if locale is not None else None
    if days and day and hour:
        return u'%d%s %d%s' % (days, day, rest // 3600, hour)
    return TimeLeft(seconds, 0) if seconds else u''


def TemporaryNote(seconds):
    # Šedá poznámka časového zdroje ve skupině „Efekty (dočasné)“: jen zbývající čas.
    return ShortLeft(seconds, _module('localeInfo'))


def AffectItemSource(entry):
    # Předmět, ze kterého časový efekt pochází, pro tooltip jako v inventáři: (slot, vnum).
    # 1) předmět v inventáři, jehož data dávají tentýž affect (quickbuffruntime.QuickBuffItemPolicy, stejná cesta
    #    jako Rychlá aktivace): typ affectu (USE_AFFECT server posílá jako EURO_FREE), bod, síla a doba >= zbývá;
    #    rosa jen aktivní (dewcatalog); 2) jinak předmět, kterým efekt ukazuje lišta efektů (SUMMARY_ITEMS).
    if entry is None or getattr(entry, 'affect_type', None) is None:
        return None, None
    item, player, chr_ = _module('item'), _module('player'), _module('chr')
    runtime, catalog, dews = _module('quickbuffruntime'), _module('quickbuffcatalog'), _module('dewcatalog')
    now = Collector().Now()
    left = max(0, int(getattr(entry, 'end', 0) or 0) - now) if getattr(entry, 'end', 0) else 0
    best = None
    if runtime is not None and item is not None and player is not None:
        dew_affects = _call(getattr(catalog, 'DewAffects', None), getattr(dews, 'DEWS', ())) or {}
        euro = getattr(chr_, 'NEW_AFFECT_EXP_BONUS_EURO_FREE', None)
        policy = runtime.QuickBuffItemPolicy(item, player)
        scanner = runtime.InventoryScanner(item, player)
        try:
            positions = list(scanner.Positions())
        except Exception:
            positions = []
        for slot in positions:
            vnum = _call(player.GetItemIndex, slot) or 0
            if not vnum:
                continue
            if vnum in dew_affects:
                # Rosa: druh efektu podle dewcatalog, jen ta aktivní (její zbývající čas je v jejím tooltipu).
                if dew_affects[vnum] == entry.affect_type and _call(policy.IsActiveBlend, slot, {'kind': 'blend'}):
                    return slot, vnum
                continue
            desc = _call(policy.Describe, vnum, slot)
            if not desc or desc.get('apply') is None:
                continue
            types = set([desc.get('affect'), dew_affects.get(vnum)])
            if desc.get('kind') == 'affect':
                types.add(euro)
            if entry.affect_type not in types or _call(item.GetApplyPoint, desc['apply']) != entry.point:
                continue
            if desc.get('kind') == 'blend':
                if not _call(policy.IsActiveBlend, slot, desc):
                    continue
                return slot, vnum
            else:
                _call(item.SelectItem, vnum)
                strength = _call(item.GetValue, 2)
                duration = int(desc.get('duration') or 0)
                if strength is not None and abs(strength - entry.value) >= 0.5 or duration < left:
                    continue
                if best is not None and best[0] <= duration:
                    continue
                best = (duration, slot, vnum)
    if best is not None:
        return best[1], best[2]
    shower = _module('uiaffectshower')
    summary = getattr(getattr(shower, 'AffectShower', None), 'SUMMARY_ITEMS', {}) or {}
    vnum = summary.get(entry.affect)
    return (None, vnum) if vnum else (None, None)


def AffectHoverImage(entry):
    # Ikona affectu v živé liště efektů (interface.uiAffectshower), jejíž tooltip ukáže řádek rozpadu: celý
    # název, co dává a zbývající čas, stejně jako při najetí na lištu. None = affect na liště není.
    if entry is None or getattr(entry, 'affect', None) is None:
        return None
    osf = _module('osfInfo')
    interface = _call(getattr(osf, 'GetInterfaceInstance', None)) if osf is not None else None
    images = getattr(getattr(interface, 'uiAffectshower', None), 'affectImageDict', None)
    if not isinstance(images, dict):
        return None
    shower = _module('uiaffectshower')
    keys = [entry.affect, entry.affect_type]
    skill_index = BUFFI_SKILLS.get(entry.affect, entry.affect if isinstance(entry.affect, int) and
                                   0 < entry.affect < 200 else 0)
    to_affect = getattr(shower, 'SkillToAffect', None) if shower is not None else None
    data = getattr(getattr(shower, 'AffectShower', None), 'AFFECT_DATA_DICT', {}) or {}
    if skill_index and to_affect is not None:
        keys.append(_call(to_affect, skill_index, data))
    for key in keys:
        if key is not None and key in images:
            return images[key]
    return None


def GroupTitle(key, title):
    # Skupina časových zdrojů nemá vlastní text: „Efekty“ + BONUS_SOURCE_TEMPORARY z locale.
    return title if title is not None else TemporaryTitle(GROUP_TITLES['effects'])


def TemporaryTitle(title):
    # Název skupiny časových zdrojů: + BONUS_SOURCE_TEMPORARY; bez textu v locale beze změny.
    locale = _module('localeInfo')
    label = getattr(locale, 'BONUS_SOURCE_TEMPORARY', u'') if locale is not None else u''
    return title + u' ' + label if label else title


def _Trace(text):
    dbg = _module('dbg')
    fn = getattr(dbg, 'TraceError', None) if dbg is not None else None
    if fn is not None:
        _call(fn, text)


def _call(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None


# --------------------------------------------------------------------------- hodnoty a texty
def FromScaled(exact):
    """Serverová hodnota (škála 1 = 1 000 000) -> číslo, None když není."""
    if exact is None:
        return None
    return float(exact) / SCALE


def Format(value, percent, signed=False):
    """Hodnota pro řádek: celé číslo bez desetin, jinak nejvýš dvě desetinná místa; None -> '--'."""
    if value is None:
        return '--'
    rounded = round(float(value), 2)
    if abs(rounded - int(round(rounded))) < 0.005:
        text = '%d' % int(round(rounded))
    else:
        text = ('%.2f' % rounded).rstrip('0').rstrip('.')
    if text == '-0':
        text = '0'
    if signed and rounded > 0:
        text = '+' + text
    return text + (' %' if percent else '')


def TimeLeft(end_time, now):
    """Zbývající čas affectu: '' pro trvalé, jinak 'm:ss' nebo 'h:mm:ss'."""
    if not end_time or end_time - now >= FOREVER:
        return ''
    seconds = max(0, int(end_time - now))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    if hours:
        return '%d:%02d:%02d' % (hours, minutes, seconds)
    return '%02d:%02d' % (minutes, seconds)


def CalcAcceValue(value, absorption):
    """Absorpce šerpy, stejný výpočet jako ItemToolTip.CalcAcceValue (a server)."""
    if not value:
        return 0
    calc = int((round(value * absorption) / 100) - .5) + int(int((round(value * absorption) / 100) - .5) > 0)
    if calc <= 0 and value > 0:
        return 1
    return calc


# --------------------------------------------------------------------------- jeden řádek rozpadu
class Entry(object):
    """Jeden zdroj: ikona (cesta, výška slotu), název, podrobnost, hodnota; ``cell`` = buňka výbavy (kámen patří
    k předmětu ve stejné buňce), ``note`` = krátká poznámka k hodnotě (absorpce šerpy)."""

    def __init__(self, group, name, detail, value, icon=None, icon_height=32, kind='', cell=None, note=''):
        self.group = group
        self.name = name
        self.detail = detail
        self.value = value
        self.icon = icon
        self.icon_height = icon_height
        self.kind = kind
        self.cell = cell
        self.note = note
        self.temporary = False      # časový affect: skupina „Efekty (dočasné)“, v poznámce zbývající čas
        self.affect = None          # klíč affectu (affectDict) a serverový typ: tooltip řádku z lišty efektů
        self.affect_type = None
        self.point = None           # bod řádku a konec affectu: předmět, ze kterého efekt je (AffectItemSource)
        self.end = 0

    def __repr__(self):
        return 'Entry(%r, %r, %r, %r)' % (self.group, self.name, self.detail, self.value)


class Breakdown(object):
    """Výsledek: title, percent, total (None = server ještě neposlal), groups [(key, title, value, [Entry])],
    formula (text u násobného řádku), note."""

    def __init__(self, title, percent):
        self.title = title
        self.percent = percent
        self.total = None
        self.groups = []
        self.formula = ''
        self.note = ''
        self.multiplicative = False

    def Sum(self):
        return sum(value for _, _, value, _ in self.groups)

    def Entries(self):
        return [entry for _, _, _, entries in self.groups for entry in entries]

    def Group(self, key):
        for group in self.groups:
            if group[0] == key:
                return group
        return None


# --------------------------------------------------------------------------- sběr zdrojů z klienta
class Collector(object):
    """Čte data klienta (player, item, affecty, Pasivky). Každý přístup je chráněný: chybějící modul nebo funkce
    starého EXE znamená jen méně zdrojů."""

    def __init__(self):
        self.player = _module('player')
        self.item = _module('item')
        self.app = _module('app')

    # ------------------------------------------------------------ pomocné
    def Now(self):
        fn = getattr(self.app, 'GetGlobalTimeStamp', None)
        return (_call(fn) or 0) if fn is not None else 0

    def Clock(self):
        fn = getattr(self.app, 'GetTime', None)
        return (_call(fn) or 0.0) if fn is not None else 0.0

    def Matches(self, apply_type, kind, point):
        if not apply_type:
            return False
        if apply_type == kind:
            return True
        if point and self.item is not None:
            return _call(self.item.GetApplyPoint, apply_type) == point
        return False

    def ItemIndex(self, cell):
        player = self.player
        window = _const(player, 'INVENTORY')
        vnum = None
        if window is not None:
            vnum = _call(player.GetItemIndex, window, cell)
        if vnum is None:
            vnum = _call(player.GetItemIndex, cell)
        return vnum or 0

    def _Slot(self, getter, cell, index):
        player = self.player
        fn = getattr(player, getter, None)
        if fn is None:
            return None
        window = _const(player, 'INVENTORY')
        value = _call(fn, window, cell, index) if window is not None else None
        if value is None:
            value = _call(fn, cell, index)
        return value

    def Sockets(self, cell):
        count = int(_const(self.player, 'METIN_SOCKET_MAX_NUM', 6) or 0)
        return [self._Slot('GetItemMetinSocket', cell, i) or 0 for i in range(count)]

    def Attributes(self, cell):
        count = int(_const(self.player, 'ATTRIBUTE_SLOT_MAX_NUM', 7) or 0)
        result = []
        for i in range(count):
            pair = self._Slot('GetItemAttribute', cell, i)
            if pair and len(pair) >= 2:
                result.append((pair[0], pair[1]))
        return result

    def RandomApplies(self, cell, vnum):
        count = int(_const(self.player, 'APPLY_RANDOM_SLOT_MAX_NUM', 0) or 0)
        if not count or not hasattr(self.player, 'GetItemApplyRandom'):
            return []
        policy = _module('equipmentbonuspolicy')
        if policy is not None and _call(policy.HasRetiredRandomApplies, vnum):
            return []
        result = []
        for i in range(count):
            pair = self._Slot('GetItemApplyRandom', cell, i)
            if pair and len(pair) >= 2:
                result.append((pair[0], pair[1]))
        return result

    def ProtoApplies(self, vnum):
        item = self.item
        if item is None or _call(item.SelectItem, vnum) is False:
            return []
        count = int(_const(item, 'ITEM_APPLY_MAX_NUM', 4) or 0)
        result = []
        for i in range(count):
            pair = _call(item.GetAffect, i)
            if pair and len(pair) >= 2:
                result.append((pair[0], pair[1]))
        return result

    def ItemFace(self, vnum):
        """(název, ikona, výška slotu) předmětu."""
        item = self.item
        if item is None or not vnum:
            return None, None, 32
        _call(item.SelectItem, vnum)
        name = _call(item.GetItemName) or ''
        icon = _call(item.GetIconImageFileName) or None
        size = _call(item.GetItemSize) or (1, 1)
        try:
            height = 32 * max(1, min(3, int(size[1])))
        except Exception:
            height = 32
        return name, icon, height

    def IsStone(self, vnum):
        item = self.item
        if item is None or vnum < 1000:
            return False
        if _call(item.SelectItem, vnum) is False:
            return False
        metin = _const(item, 'ITEM_TYPE_METIN')
        return metin is not None and _call(item.GetItemType) == metin

    def IsSash(self, vnum):
        item = self.item
        if item is None:
            return False
        _call(item.SelectItem, vnum)
        return (_call(item.GetItemType) == _const(item, 'ITEM_TYPE_COSTUME', -1) and
                _call(item.GetItemSubType) == _const(item, 'COSTUME_TYPE_ACCE', -2))

    def HeartActive(self):
        talisman = _module('uitalisman')
        if talisman is None or not hasattr(talisman, 'IsHeartActive'):
            return True
        return bool(_call(talisman.IsHeartActive))

    # ------------------------------------------------------------ výbava
    def Equipment(self, kind, point):
        """[Entry] nasazených předmětů a kamenů; druhá hodnota = součet, který odpovídá serverovému ledgeru výbavy."""
        start = _const(self.player, 'EQUIPMENT_SLOT_START')
        if start is None:
            return [], 0
        entries = []
        ledger = 0
        skin = self.ItemIndex(start + WEAR_MOUNT_SKIN)
        for offset in sorted(WEAR):
            label, group = WEAR[offset]
            cell = start + offset
            vnum = self.ItemIndex(cell)
            if not vnum:
                continue
            if offset in MOUNT_GEAR and not skin:
                continue          # výbava mounta platí jen s nasazeným skinem (item.cpp ModifyPoints)
            if offset == WEAR_TALISMAN_HEART and not self.HeartActive():
                continue
            sockets = self.Sockets(cell)
            own = 0
            note = ''
            if offset == WEAR_SASH and self.IsSash(vnum):
                own += self._SashValue(vnum, cell, sockets, kind, point)
                index = _const(_module('acce'), 'ABSORPTION_SOCKET', 1)
                absorption = sockets[index] if 0 <= index < len(sockets) else 0
                if absorption:
                    note = u'absorpce %d %%' % absorption
            else:
                for apply_type, value in self.ProtoApplies(vnum) + self.RandomApplies(cell, vnum):
                    if self.Matches(apply_type, kind, point):
                        own += value
                for apply_type, value in self.Attributes(cell):
                    if self.Matches(apply_type, kind, point):
                        own += value
            name, icon, height = self.ItemFace(vnum)
            if own:
                entries.append(Entry(group, name or label, label, own, icon, height, 'item', cell, note))
                ledger += own
            if offset == WEAR_SASH:
                continue
            for stone in sockets:
                if not stone or not self.IsStone(stone):
                    continue
                value = sum(v for t, v in self.ProtoApplies(stone) if self.Matches(t, kind, point))
                if value:
                    stone_name, stone_icon, _ = self.ItemFace(stone)
                    entries.append(Entry(group, stone_name or u'Kámen', u'kámen · ' + label, value, stone_icon, 32,
                                         'stone', cell))
                    ledger += value
        return entries, ledger

    def _SashValue(self, vnum, cell, sockets, kind, point):
        acce = _module('acce')
        absorption_socket = _const(acce, 'ABSORPTION_SOCKET', 1)
        absorbed_socket = _const(acce, 'ABSORBED_SOCKET', 0)
        try:
            absorption = int(sockets[absorption_socket])
            absorbed = int(sockets[absorbed_socket])
        except Exception:
            absorption = absorbed = 0
        total = 0
        for apply_type, value in self.ProtoApplies(vnum):
            if self.Matches(apply_type, kind, point):
                total += value
        if absorbed and absorption:
            for apply_type, value in self.ProtoApplies(absorbed):
                if self.Matches(apply_type, kind, point) and value > 0:
                    total += CalcAcceValue(value, absorption)
            for apply_type, value in self.Attributes(cell):
                if self.Matches(apply_type, kind, point):
                    total += CalcAcceValue(value, absorption)
        else:
            for apply_type, value in self.Attributes(cell):
                if self.Matches(apply_type, kind, point):
                    total += value
        return total

    # ------------------------------------------------------------ affecty
    def AffectData(self):
        shower = _module('uiaffectshower')
        data = getattr(shower, 'affectDict', None) if shower is not None else None
        return dict(data) if isinstance(data, dict) else {}

    def Affects(self, kind, point, skip_skills=()):
        """[Entry] affectů, které působí na bod ``point``."""
        if not point:
            return []
        shower = _module('uiaffectshower')
        now = self.Now()
        start = _const(self.player, 'EQUIPMENT_SLOT_START')
        entries = []
        rows = sorted(self.AffectData().items(),
                      key=lambda pair: (0, pair[0], '') if isinstance(pair[0], int) else (1, 0, str(pair[0])))
        for key, data in rows:
            if not isinstance(key, int):
                continue                  # ("actor", typ): otrava, zpomalení ... bez bonusu
            if key in skip_skills:
                continue
            for entry in (data or {}).get('entries', ()) or ():
                try:
                    entry_point, value, end = entry[0], entry[1], entry[2]
                except Exception:
                    continue
                if entry_point != point or not value:
                    continue
                entry = self._AffectEntry(shower, key, value, end, now, start)
                if entry is not None:
                    entry.affect_type, entry.point, entry.end = key, point, end
                entries.append(entry)
        return [entry for entry in entries if entry is not None]

    def _AffectEntry(self, shower, key, value, end, now, start):
        # Entry affectu; časový zdroj (lektvar, rosa, Buffi, buff) jde do skupiny „Efekty (dočasné)“ se
        # zbývajícím časem v poznámce. ``affect`` = klíč pro tooltip z lišty efektů (AffectHoverImage).
        entry = self._AffectSource(shower, key, value, end, now, start)
        left = TimeLeft(end, now)
        if entry is not None:
            entry.affect = key
        if entry is not None and left and entry.group == 'effects':
            entry.temporary = True
            entry.group = 'temporary'
            entry.detail = TemporaryNote(end - now) or entry.detail
        return entry

    def _AffectSource(self, shower, key, value, end, now, start):
        left = TimeLeft(end, now)

        def detail(text):
            return text + (u' · ' + left if left else u' · trvale')

        if key == AFFECT_MOUNT_BONUS:
            name, icon, height = self.ItemFace(self.ItemIndex(start + WEAR_MOUNT_SKIN)) if start is not None else (
                None, None, 32)
            cell = start + WEAR_MOUNT_SKIN if start is not None and name else None
            return Entry('mount', name or u'Pečeť mounta', u'Kostým jezdeckého zvířete', value, icon, height, 'affect',
                         cell)
        if key in (AFFECT_GROWTH_PET, AFFECT_PET_HEART):
            name, icon, height = self.ItemFace(self.ItemIndex(start + WEAR_PET)) if start is not None else (
                None, None, 32)
            text = u'Srdce mazlíčka' if key == AFFECT_PET_HEART else u'Mazlíček · vyvolaný'
            cell = start + WEAR_PET if start is not None and name else None
            return Entry('pet', name or u'Mazlíček', text, value, icon, height, 'affect', cell)
        if key == AFFECT_COLLECT:
            return Entry('biolog', u'Biolog', u'odměna za výzkum · trvale', value, ICON_BIOLOG, 32, 'affect')
        name, icon = self._AffectFace(shower, key, value)
        if key in BUFFI_SKILLS:
            return Entry('effects', name, detail(u'Buffka'), value, icon, 32, 'affect')
        if key in DRAGON_SOUL_AFFECTS:
            return Entry('equipment', name or u'Dračí kameny', u'Alchymie', value, icon, 32, 'affect')
        if 0 < key < 200:
            return Entry('effects', name, detail(u'Buff'), value, icon, 32, 'affect')
        kind = u'Efekt'
        cls = getattr(shower, 'AffectShower', None)
        if key in (getattr(cls, 'POTION_AFFECTS', ()) or ()):
            kind = u'Lektvar'
        elif key in (getattr(cls, 'DEW_AFFECTS', ()) or ()):
            kind = u'Rosa'
        return Entry('effects', name, detail(kind), value, icon, 32, 'affect')

    def _AffectFace(self, shower, key, value):
        """(název, ikona) affectu z dat lišty efektů; schopnost podle svého vnum."""
        skill = _module('skill')
        skill_index = BUFFI_SKILLS.get(key, key if 0 < key < 200 else 0)
        cls = getattr(shower, 'AffectShower', None) if shower is not None else None
        data = getattr(cls, 'AFFECT_DATA_DICT', {}) or {}
        summary = getattr(cls, 'SUMMARY_ITEMS', {}) or {}
        if skill_index:
            name = _call(getattr(skill, 'GetSkillName', None), skill_index) if skill is not None else None
            # Stejná dlaždice jako v okně Schopnosti (uiaffectshower.CurrentSkillIcon ze SkillDesc.txt); vnum
            # se nikdy neporovnává s čísly affectů (AFFECT_POISON = 3 a AFFECT_SLOW = 4 by vyšly pro schopnosti 3, 4).
            to_affect = getattr(shower, 'SkillToAffect', None)
            affect = _call(to_affect, skill_index, data) if to_affect is not None else None
            row = data.get(affect) if affect is not None else None
            icon = row[1] if row and len(row) > 1 else None
            current = getattr(shower, 'CurrentSkillIcon', None)
            if current is not None:
                icon = _call(current, icon, skill_index) or icon
            return name or u'Schopnost', icon
        if key in summary:
            name, icon, _ = self.ItemFace(summary[key])
            return name or u'Efekt', icon
        row = data.get(key)
        if row:
            name = row[0]
            if callable(name):
                name = _call(name, float(value))
            elif name and '%' in name:
                try:
                    name = name % value
                except Exception:
                    pass
            return name or u'Efekt', row[1] if len(row) > 1 else None
        return u'Efekt', None

    # ------------------------------------------------------------ Pasivky
    def Passives(self):
        """{role: Entry} aktivních PvM osobních hodnot (0 útok, 1 obrana, 2 odolnost proti běžným příšerám)."""
        model_module = _module('pvmpersonal')
        model = _call(model_module.current) if model_module is not None else None
        if model is None:
            return {}
        skill = _module('skill')
        now = self.Clock()
        result = {}
        for row in (getattr(model, 'rows', {}) or {}).values():
            try:
                left = model.remaining(row['skill'], now)
                role, value = row['role'], row['value']
            except Exception:
                continue
            if not left or not value:
                continue
            name = _call(getattr(skill, 'GetSkillName', None), row['skill']) if skill is not None else None
            icon = None
            if skill is not None and hasattr(skill, 'GetIconImageNew'):
                icon = _call(skill.GetIconImageNew, row['skill'], _call(model_module.icon_grade, row['learned']) or 0)
            minutes, seconds = divmod(int(left), 60)
            hours, minutes = divmod(minutes, 60)
            time = '%d:%02d:%02d' % (hours, minutes, seconds) if hours else '%02d:%02d' % (minutes, seconds)
            result[role] = Entry('passive', name or u'Pasivka', u'Pasivky · ' + time, value, icon, 32, 'passive')
        return result

    # ------------------------------------------------------------ server
    def EquipmentTotal(self, kind):
        """Serverový součet výbavy pro apply ``kind`` (/equipment_bonuses) nebo None."""
        presentation = _module('itembonuspresentation')
        totals = getattr(presentation, 'totals', None) if presentation is not None else None
        if totals is None or not kind or kind > 255:
            return None
        _call(totals.Request)
        return _call(totals.Get, kind)


# --------------------------------------------------------------------------- rozpad
def Build(bonus, total, collector=None, title=None, server_entries=None):
    """Rozpad řádku ``bonus`` ([apply, point, label, percent]) se serverovou hodnotou ``total`` (číslo nebo None).
    ``server_entries`` = přesný rozpad ze serveru (SourceStore.Get); bez něj odhad klienta (krok 1)."""
    collector = collector or Collector()
    if server_entries:
        try:
            return ServerBuild(bonus, server_entries, collector, title)
        except Exception:
            import traceback
            _Trace('BONUS_SOURCES ServerBuild: %s' % traceback.format_exc())
    kind, point, label, percent = bonus[0], bonus[1], bonus[2], bool(bonus[3])
    result = Breakdown(title or label, percent)
    result.total = total
    item = collector.item
    resist_monster = _const(item, 'APPLY_RESIST_MONSTER')
    attack_bonus = _const(item, 'APPLY_ATT_GRADE_BONUS')
    defense_bonus = _const(item, 'APPLY_DEF_GRADE_BONUS')

    try:
        equipment, ledger = collector.Equipment(kind, point)
    except Exception:
        equipment, ledger = [], 0
    passives = {}
    try:
        passives = collector.Passives()
    except Exception:
        passives = {}
    skip = ()
    personal = None
    if kind is not None and kind == attack_bonus and 0 in passives:
        skip, personal = LEGACY_ATTACK_SKILLS, passives[0]
    elif kind is not None and kind == defense_bonus and 1 in passives:
        skip, personal = LEGACY_DEFENSE_SKILLS, passives[1]
    try:
        affects = collector.Affects(kind, point, skip)
    except Exception:
        affects = []
    entries = equipment + affects
    # Kusy výbavy proti serverovému součtu výbavy: rozdíl je absorpce aury, rarita, perly, dračí kameny.
    server_equipment = None
    try:
        server_equipment = collector.EquipmentTotal(kind)
    except Exception:
        server_equipment = None
    if server_equipment is not None and server_equipment != ledger:
        entries.append(Entry('equipment', u'Ostatní z výbavy', u'absorpce, rarita, perly, dračí kameny',
                             server_equipment - ledger, None, 32, 'ledger'))

    multiplicative = kind is not None and kind == resist_monster and 2 in passives
    if personal is not None:
        entries.append(personal)

    def group_rows(rows):
        groups = []
        for key, group_title in GROUPS:
            members = [entry for entry in rows if entry.group == key]
            if members:
                groups.append([key, GroupTitle(key, group_title), sum(entry.value for entry in members), members])
        return groups

    if multiplicative:
        # Server: 100 - (100 - výbava a ostatní) x (100 - Pasivky) / 100 (character_bonus_snapshot.h Resistance).
        own = passives[2]
        p = max(0, min(100, own.value))
        additive = sum(entry.value for entry in entries)
        if total is not None and p < 100:
            a = 100.0 - (100.0 - total) * 100.0 / (100.0 - p)
            residual = a - additive
            if abs(residual) >= 0.005:
                entries.append(Entry('server', u'Ostatní (server)', u'server tento zdroj zatím nerozlišuje',
                                     residual, None, 32, 'residual'))
            additive = a
        result.groups = group_rows(entries) + [['passive', GROUP_TITLES['passive'], own.value, [own]]]
        result.multiplicative = True
        shown_total = total if total is not None else 100.0 - (100.0 - min(100, max(0, additive))) * (100 - p) / 100.0
        result.formula = u'Násobí se: 100 − (100 − %s) × (100 − %s) / 100 = %s' % (
            Format(additive, False), Format(p, False), Format(shown_total, False))
        result.note = u'Prostý součet by byl %s.' % Format(additive + p, True)
        return result

    if total is not None:
        residual = total - sum(entry.value for entry in entries)
        if abs(residual) >= 0.005:
            entries.append(Entry('server', u'Ostatní (server)', u'server tento zdroj zatím nerozlišuje',
                                 residual, None, 32, 'residual'))
    else:
        result.note = u'Celkovou hodnotu server zatím neposlal.'
    result.groups = group_rows(entries)
    return result


# --------------------------------------------------------------------------- krok 2: rozpad ze serveru
SOURCE_COMMAND = '/bonus_sources'
MAX_SOURCE_FRAMES = 8


class SourceStore(object):
    """Rozpad otevřeného řádku ze serveru (BonusSourcesV1 <req> <řádek> <idx> <count> TAG:arg:hodnota,...).

    Dotaz jen pro otevřený řádek, nejvýš 1x za sekundu; přijímá jen úplnou odpověď na poslední dotaz. Data platí
    3 s, potom (nebo když server neodpoví) zůstane rozpad kroku 1. Složky sloučeného řádku se střídají;
    každá má vlastní data, ale společný limit dotazů a vždy jen jeden rozpracovaný dotaz."""
    INTERVAL = 1.0
    TIMEOUT = 1.5
    FRESH = 3.0

    def __init__(self):
        self._serial = 0
        self._version = 0
        self.EndSession()

    def EndSession(self):
        self._send = None
        self._clock = lambda: 0.0
        self._row = None
        self._rows = ()
        self._cursor = 0
        self._request = None
        self._deadline = 0.0
        self._next = 0.0
        self._parts = {}
        self._count = None
        self._data = {}
        self._version += 1

    def BeginSession(self, clock, send):
        self.EndSession()
        self._clock, self._send = clock, send

    def Request(self, row):
        """Požádá o rozpad řádku ``row`` (apply 1-255, 60000+, 61000+, 62000+bod); vrací True, když poslal."""
        return self.RequestRows((row,)) if row else False

    def RequestRows(self, rows):
        rows = tuple(rows)
        if rows != self._rows:
            self._rows, self._cursor = rows, 0
            self._row = None
            self._request = None
            self._next = 0.0
            self._parts, self._count = {}, None
            self._data = dict((row, data) for row, data in self._data.items() if row in rows)
        return self.Poll()

    def Poll(self):
        if self._send is None or not self._rows:
            return False
        now = self._clock()
        if self._request is not None and now < self._deadline:
            return False
        if now < self._next:
            return False
        self._row = self._rows[self._cursor]
        self._cursor = (self._cursor + 1) % len(self._rows)
        self._next = now + self.INTERVAL
        self._serial = self._serial % 4294967295 + 1
        self._request = self._serial
        self._deadline = now + self.TIMEOUT
        self._parts, self._count = {}, None
        try:
            self._send('%s %d %d' % (SOURCE_COMMAND, self._request, self._row))
        except Exception:
            return False
        return True

    def Stop(self):
        self._rows = ()
        self._row = None
        self._request = None

    def Receive(self, request, row, index, count, payload):
        if self._send is None:
            return False
        try:
            request, row, index, count = int(request), int(row), int(index), int(count)
            if request != self._request or row != self._row:
                return False
            if not (1 <= count <= MAX_SOURCE_FRAMES and 0 <= index < count):
                return False
            if len(payload) > 350 or index in self._parts or self._count not in (None, count):
                return False
            entries = []
            if payload != '-':
                for item in payload.split(','):
                    tag, arg, value = item.split(':')
                    if not tag or len(tag) > 16 or not tag.replace('_', '').isalpha() or not tag.isupper():
                        return False
                    arg, value = int(arg), int(value)
                    if arg < 0 or arg > 4294967295 or abs(value) > 9223372036854775807:
                        return False
                    entries.append((tag, arg, value))
            elif count != 1:
                return False
        except (ValueError, TypeError, OverflowError):
            return False
        self._count = count
        self._parts[index] = entries
        if len(self._parts) != count:
            return False
        merged = []
        for i in range(count):
            merged.extend(self._parts[i])
        data = merged if any(tag == 'TOTAL' for tag, _, _ in merged) else None
        previous = self._data.get(row)
        if previous is None or previous[0] != data:
            self._version += 1
            # Diagnostika: co server k řádku poslal (jen při změně).
            _Trace('BONUS_SOURCES row=%d %s' % (row, ','.join('%s:%d:%d' % entry for entry in merged) or '-'))
        self._data[row] = (data, self._clock())
        self._request = None
        self._parts, self._count = {}, None
        return True

    def Get(self, row):
        """[(tag, arg, hodnota ve škále 1 = 1 000 000)] pro ``row`` nebo None (žádná / stará / neznámá data)."""
        data = self._data.get(row)
        if data is None or data[0] is None:
            return None
        if self._clock() > data[1] + self.FRESH:
            return None
        return list(data[0])

    def Version(self):
        # Otevřený rozpad se překreslí i každou sekundu: zbývající čas efektů běží, i když server posílá totéž.
        tick = int(self._clock()) if self._rows else None
        return (self._version, tuple((row, self.Get(row) is not None) for row in self._rows), tick)


server = SourceStore()

# Pojmenování tagů, které klient sám nezná: tag -> (skupina, {arg: název} nebo název, podrobnost).
SERVER_NAMES = {
    'TALENT': ('talent', u'Strom schopností', u'nasazené uzly'),
    'GUILD': ('guild', u'Cechovní pasivka', u'Cech'),
    'ALBUM': ('album', {0: u'Album mazlíčků', 1: u'Album mazlíčků (v boji)', 2: u'Síla knih z alba'}, u'sbírka'),
    'HUNT': ('hunt', {0: u'Lov meteorů', 1: u'Lov bossů'}, u'Trvalé úkoly'),
    'RARITY_SET': ('rarity', {0: u'Rarita sady', 1: u'Rarita sady (průraz útoku)'}, u'vyvážená rarita výbavy'),
    'SAGE': ('sage', u'Bonus mudrce', u'dokončené úkoly mudrce'),
    'ATTR_BUFF': ('attrbuff', u'Posílení bonusů výbavy', u'Efekt'),
    'PARTY': ('party', u'Bonus družiny', u'Družina'),
    'MARRIAGE': ('marriage', u'Svatební bonus', u'Svatba'),
    'EVENT': ('event', u'Bonusový event', u'Event'),
    'BASE': ('base', {0: u'Úroveň, staty a povolání', 1: u'Z procentního bonusu'}, u'Základ'),
    # arg = živel větve v pořadí katalogu (uimountmodel.ELEMENT_NAMES).
    'EXPEDITION': ('expedition', {0: u'Oheň', 1: u'Led', 2: u'Blesk', 3: u'Vítr', 4: u'Země', 5: u'Temnota'},
                   u'větev Živelné výpravy'),
}


def _ServerName(tag, arg):
    group, names, detail = SERVER_NAMES[tag]
    name = names.get(arg, names.get(0)) if isinstance(names, dict) else names
    return group, name, detail


def ServerBuild(bonus, entries, collector=None, title=None):
    """Rozpad řádku z přesných serverových záznamů; klient jen pojmenuje zdroje."""
    collector = collector or Collector()
    kind, point, label, percent = bonus[0], bonus[1], bonus[2], bool(bonus[3])
    result = Breakdown(title or label, percent)
    start = _const(collector.player, 'EQUIPMENT_SLOT_START')
    shower = _module('uiaffectshower')
    now = collector.Now()
    try:
        affect_data = collector.AffectData()
    except Exception:
        affect_data = {}
    try:
        passives = collector.Passives()
    except Exception:
        passives = {}

    total = None
    residual = 0.0
    stages = {}
    legacy_roles = set(arg for tag, arg, _ in entries if tag == 'LEGACY')
    legacy_skills = set()
    if 0 in legacy_roles:
        legacy_skills.update(LEGACY_ATTACK_SKILLS)
    if 1 in legacy_roles:
        legacy_skills.update(LEGACY_DEFENSE_SKILLS)
    legacy_pool = 0.0
    items = {}       # buňka -> [hodnota, poznámky]
    order = []
    stones = []
    dragon = {}      # 'DS_DECK' / 'DS_SET' -> hodnota
    rows = []
    for tag, arg, raw in entries:
        value = FromScaled(raw)
        if tag == 'TOTAL':
            total = value
        elif tag == 'RESIDUAL':
            residual += value
        elif tag == 'STAGE':
            stages[arg] = value
        elif tag in ('WEAR', 'ABSORB', 'RARITY'):
            if arg not in items:
                items[arg] = [0.0, []]
                order.append(arg)
            items[arg][0] += value
            note = {'ABSORB': u'absorpce', 'RARITY': u'rarita'}.get(tag)
            if note and note not in items[arg][1]:
                items[arg][1].append(note)
        elif tag == 'STONE':
            stones.append((arg // 16, arg % 16, value))
        elif tag in ('DS_DECK', 'DS_SET'):
            dragon[tag] = dragon.get(tag, 0.0) + value
        elif tag == 'AFFECT':
            if arg in legacy_skills:
                legacy_pool += value
                continue
            end = 0
            key = AffectKey(shower, arg, point)
            for row in ((affect_data.get(key) or {}).get('entries', ()) or ()):
                try:
                    if row[0] == point:
                        end = row[2]
                        break
                except Exception:
                    continue
            entry = None
            try:
                entry = collector._AffectEntry(shower, key, value, end, now, start)
                if entry is not None:
                    entry.affect_type = arg
                    entry.point = point
                    entry.end = end
            except Exception:
                entry = None
            rows.append(entry or Entry('effects', u'Efekt', u'', value, None, 32, 'affect'))
        elif tag == 'PVM':
            own = passives.get(arg)
            if own is not None:
                rows.append(Entry('passive', own.name, own.detail, value, own.icon, own.icon_height, 'passive'))
            else:
                rows.append(Entry('passive', u'Pasivka', u'Pasivky', value, None, 32, 'passive'))
        elif tag == 'LEGACY':
            legacy_pool += value
        elif tag in SERVER_NAMES:
            group, name, detail = _ServerName(tag, arg)
            rows.append(Entry(group, name, detail, value, None, 32, 'server'))
        else:
            residual += value          # tag, který tento klient ještě nezná

    # Předměty ve výbavě: jméno a ikona ze slotu, skupina podle slotu (mount, mazlíček).
    equipment = []
    for cell in order:
        value, notes = items[cell]
        if abs(value) < 0.0000005:
            continue
        wear_label, group = WEAR.get(cell, (u'Výbava', 'equipment'))
        name = icon = None
        height = 32
        inventory_cell = start + cell if start is not None else None
        if inventory_cell is not None:
            name, icon, height = collector.ItemFace(collector.ItemIndex(inventory_cell))
        if cell == WEAR_SASH and inventory_cell is not None:
            sockets = collector.Sockets(inventory_cell)
            index = _const(_module('acce'), 'ABSORPTION_SOCKET', 1)
            absorption = sockets[index] if 0 <= index < len(sockets) else 0
            if absorption:
                notes = [u'absorpce %d %%' % absorption] + [n for n in notes if n != u'absorpce']
        equipment.append(Entry(group, name or wear_label, wear_label, value, icon, height, 'item', inventory_cell,
                               u', '.join(notes)))
    for cell, socket, value in stones:
        wear_label, group = WEAR.get(cell, (u'Výbava', 'equipment'))
        stone_name, stone_icon = None, None
        inventory_cell = start + cell if start is not None else None
        if inventory_cell is not None:
            sockets = collector.Sockets(inventory_cell)
            vnum = sockets[socket] if 0 <= socket < len(sockets) else 0
            if vnum:
                stone_name, stone_icon, _ = collector.ItemFace(vnum)
        equipment.append(Entry(group, stone_name or u'Kámen', u'kámen · ' + wear_label, value, stone_icon, 32,
                               'stone', inventory_cell))
    if dragon.get('DS_DECK'):
        equipment.append(Entry('equipment', u'Dračí kameny', u'aktivní sada', dragon['DS_DECK'], None, 32, 'ds'))
    if dragon.get('DS_SET'):
        equipment.append(Entry('equipment', u'Dračí kameny', u'bonus sady', dragon['DS_SET'], None, 32, 'ds'))
    rows = equipment + rows
    # Staré buffy, které Pasivky nahrazují: zbude jen rozdíl, který server neodečetl (obvykle 0).
    if abs(legacy_pool) >= 0.005:
        rows.append(Entry('effects', u'Schopnosti nahrazené Pasivkami', u'', legacy_pool, None, 32, 'affect'))
    if abs(residual) >= 0.005:
        rows.append(Entry('server', u'Ostatní (server)', u'server tento zdroj zatím nerozlišuje', residual, None, 32,
                          'residual'))
    result.total = total

    def group_rows(members_all):
        groups = []
        for key, group_title in GROUPS:
            members = [entry for entry in members_all if entry.group == key]
            if members:
                groups.append([key, GroupTitle(key, group_title), sum(entry.value for entry in members), members])
        return groups

    if 0 in stages and 1 in stages:
        additive, p = stages[0], stages[1]
        shown_total = stages.get(2, total)
        own = passives.get(2)
        own_entry = Entry('passive', own.name if own else u'Pasivka', own.detail if own else u'Pasivky', p,
                          own.icon if own else None, own.icon_height if own else 32, 'passive')
        result.groups = group_rows(rows)
        if p:
            result.groups.append(['passive', GROUP_TITLES['passive'], p, [own_entry]])
            result.multiplicative = True
            result.formula = u'Násobí se: 100 − (100 − %s) × (100 − %s) / 100 = %s' % (
                Format(additive, False), Format(p, False), Format(shown_total, False))
            result.note = u'Prostý součet by byl %s.' % Format(additive + p, True)
        return result
    result.groups = group_rows(rows)
    return result
