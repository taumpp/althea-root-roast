# -*- coding: utf-8 -*-
"""Category-specific public market queries. No engine or price dependencies."""
from copy import deepcopy

ANY = -1
CATEGORIES = ((0, 'Všechny předměty'), (1, 'Zbraně'), (2, 'Výbava'),
    (3, 'Kostýmy'), (11, 'Šerpy'), (4, 'Mazlíci'), (5, 'Mounti'),
    (6, 'Alchymie'), (7, 'Knihy'), (8, 'Kameny'), (9, 'Spotřební'), (10, 'Materiály'))
# Server category 12 is the complement of 1..11. Offer it only after the
# server's `virtualmarketcategoryotherv1` capability: an older server
# disconnects a client that sends an unknown category.
OTHER = 12
OTHER_CATEGORY = (OTHER, 'Ostatní')
JOBS = ((-1, 'Všechna'), (0, 'Válečník'), (1, 'Ninja'), (2, 'Sura'), (3, 'Šaman'))
GENDERS = ((-1, 'Libovolné'), (0, 'Muž'), (1, 'Žena'))
GRADES = ('Surová', 'Broušená', 'Vzácná', 'Starověká', 'Legendární', 'Mýtická')
STEPS = ('Matná', 'Čistá', 'Bezchybná', 'Brilantní', 'Excelentní')
SUBTYPE_NAMES = {
    1: ('Meče', 'Dýky', 'Luky', 'Obouruční zbraně', 'Zvony', 'Vějíře', 'Šípy', 'Jezdecká kopí', 'Drápy', 'Toulce', 'Kytice'),
    2: ('Brnění', 'Přilby', 'Štíty', 'Náramky', 'Boty', 'Náhrdelníky', 'Náušnice', 'Talismany', 'Rukavice', 'Srdce talismanu'),
    28: ('Tělo', 'Účesy', 'Kostýmoví mounti', 'Šerpy', 'Zbraně', 'Aury', 'Efekty zbraní', 'Efekty brnění', 'Vzhledy šerp', 'Kostýmoví mazlíci'),
    37: ('Vejce', 'Vychovatelní mazlíci', 'Přepravní boxy', 'Krmivo', 'Knihy schopností', 'Odstranění schopnosti', 'Změna jména', 'Zkušenosti', 'Odstranění všech schopností', 'Zkušenosti v procentech', 'Určení vlastností', 'Změna vlastností', 'Platby', 'Prémiové krmivo'),
    5: ('Výrobní materiály', 'Krev', 'Kořeny', 'Jehly', 'Šperky', 'Alchymie: běžné zesílení', 'Alchymie: požehnané zesílení', 'Alchymie: dračí zesílení', 'Alchymie: změna bonusů', 'Zbraně', 'Brnění', 'Šerpy', 'Elementy'),
    29: ('Dračí diamant', 'Dračí rubín', 'Dračí nefrit', 'Dračí safír', 'Dračí granát', 'Dračí onyx'),
}
TYPE_NAMES = {4: 'Automatické lektvary', 10: 'Kameny ducha', 14: 'Ušlechtilé materiály',
    17: 'Knihy schopností', 22: 'Zapomínání schopností', 27: 'Směsi', 31: 'Speciální předměty',
    33: 'Prsteny', 34: 'Opasky', 42: 'Pomocníci', 43: 'Výbava mountů'}


def matches_category(category, kind, subtype):
    if category == 0: return True
    if category == 1: return kind == 1
    if category == 2: return kind in (2, 33, 34)
    if category == 3: return kind == 28 and subtype not in (2, 3, 9)
    if category == 4: return kind in (37, 42) or (kind, subtype) == (28, 9)
    if category == 5: return kind == 43 or (kind, subtype) == (28, 2)
    if category == 6: return kind == 29
    if category == 7: return kind in (17, 22)
    if category == 8: return kind == 10
    if category == 9: return kind in (3, 4, 27, 31)
    if category == 10: return kind in (5, 14)
    if category == 11: return (kind, subtype) == (28, 3)
    if category == OTHER:
        return not any(matches_category(named, kind, subtype) for named in range(1, 12))
    return False


def available_categories(other=False):
    return CATEGORIES + ((OTHER_CATEGORY,) if other else ())


# Shared immutable translation table; Wiki folds thousands of indexed names.
_FOLD_GROUPS = {'a': 'áäàâãåąă', 'c': 'čćç', 'd': 'ďđ', 'e': 'éěëèêę', 'i': 'íïìî',
    'l': 'ĺľł', 'n': 'ńňñ', 'o': 'óöòôõő', 'r': 'ŕř', 's': 'šśş', 't': 'ťţ',
    'u': 'úůüùûű', 'y': 'ýÿ', 'z': 'žźż'}
_FOLD_ACCENTS = str.maketrans({accent: base for base, letters in _FOLD_GROUPS.items() for accent in letters})


def folded(text):
    return ''.join(c for c in str(text).lower().translate(_FOLD_ACCENTS) if not 0x300 <= ord(c) <= 0x36f)


def _rail_extras(category, catalog, result):
    # Rail entries outside the type lists below (truhly, klíče in Ostatní; drahokamy, pečetě in Spotřební).
    for extra_category, key, name in RAIL_EXTRA:
        if extra_category == category and key not in dict(result) and key[0] not in SUBTYPE_NAMES and \
                key[0] not in TYPE_NAMES and key[0] != 3 and _catalog_has(category, key[0], key[1], catalog):
            result.append((key, name))
    if category == 9:
        for extra_category, key, name in RAIL_EXTRA:
            if extra_category == 9 and key[0] == 3 and key[1] >= 0 and _catalog_has(9, 3, key[1], catalog):
                result.append((key, name))


def subcategories(category, catalog):
    result = [((-1, -1), 'Všechny')]
    _rail_extras(category, catalog, result)
    if category in (0, 11, OTHER): return result
    seen_types = set()
    for kind, subtype, flags, sample, refines, variants, bonuses in catalog:
        if not matches_category(category, kind, subtype): continue
        names = SUBTYPE_NAMES.get(kind, ())
        if subtype < len(names):
            result.append(((kind, subtype), names[subtype]))
        elif kind == 29:
            # Extra Althea stones retain their authored prototype name.
            result.append(((kind, subtype), sample.split('+')[0].strip()))
        elif kind in TYPE_NAMES and kind not in seen_types:
            result.append(((kind, -1), TYPE_NAMES[kind]))
            seen_types.add(kind)
        elif kind == 3 and kind not in seen_types:
            result.append(((kind, -1), 'Použitelné předměty'))
            seen_types.add(kind)
    return result


# The market's category rail uses the server's searchable types and subtypes. A row is
#   (key, header category, folder, entries); an entry is (category, (kind, subtype), name or None = catalog name).
# A plain row searches its header category and opens into its entries. A folder row (Zbroj, Šperky, Mazlíci a
# mounti, Kameny, Truhly a klíče) groups entries of one or more server categories that no single query covers; it
# opens and searches its first entry. Entries list tradeable, playable items:
# no ANTI_MYSHOP / ANTI_GIVE or test / GM items. Left out on purpose: Jezdecká kopí, Drápy (Lykan cannot be
# created), Toulce, Kytice, Srdce talismanu, Aury and Kostýmoví mazlíci (untradeable), Efekty zbraní / brnění (placeholder items) and the single-item subtypes.
USE_PUT_INTO_ACCESSORY_SOCKET = 21
USE_RESONANCE_SEAL = 50
RAIL_ROWS = (
    ('weapons', 1, False, tuple((1, (1, subtype), name) for subtype, name in
        enumerate(('Meče', 'Dýky', 'Luky', 'Obouruční zbraně', 'Zvony', 'Vějíře', 'Šípy')))),
    ('armor', 2, True, ((2, (2, 0), 'Brnění'), (2, (2, 1), 'Přilby'), (2, (2, 2), 'Štíty'), (2, (2, 4), 'Boty'),
        (2, (2, 8), 'Rukavice'))),
    ('jewelry', 2, True, ((2, (2, 3), 'Náramky'), (2, (2, 5), 'Náhrdelníky'), (2, (2, 6), 'Náušnice'),
        (2, (2, 7), 'Talismany'), (2, (34, -1), 'Opasky'))),
    ('sashes', 11, False, ()),
    ('looks', 3, False, ((3, (28, 0), 'Oblek'), (3, (28, 1), 'Účesy'), (3, (28, 4), 'Zbraně'),
        (3, (28, 8), 'Vzhledy šerp'))),
    ('pets_mounts', 4, True, ((4, (-1, -1), 'Mazlíci'), (4, (37, 0), 'Vejce'), (4, (37, 4), 'Knihy mazlíků'),
        (5, (-1, -1), 'Mounti'))),
    ('stones', 8, True, ((8, (-1, -1), 'Kameny ducha'), (9, (3, USE_PUT_INTO_ACCESSORY_SOCKET), 'Drahokamy do šperků'),
        (9, (3, USE_RESONANCE_SEAL), 'Pečetě'))),
    ('alchemy', 6, False, tuple((6, (29, subtype), None) for subtype in range(7))),
    ('books', 7, False, ()),
    ('consumables', 9, False, ((9, (3, -1), 'Použitelné předměty'), (9, (27, -1), 'Rosy a směsi'))),
    ('materials', 10, False, ((10, (5, 0), 'Výrobní materiály'), (10, (14, -1), 'Ušlechtilé materiály'))),
    ('chests', OTHER, True, ((OTHER, (23, -1), 'Truhly'), (OTHER, (20, -1), 'Pokladnice'),
        (OTHER, (21, -1), 'Klíče'), (OTHER, (36, -1), 'Truhly štěstí'))),
    ('other', OTHER, False, ()),
)
RAIL = dict((key, (category, folder, entries)) for key, category, folder, entries in RAIL_ROWS)
# Rail entries the filter dialog's Podkategorie list has no own name for (a type / subtype inside another category).
RAIL_EXTRA = tuple((category, key, name) for unused, unused2, unused3, entries in RAIL_ROWS
    for category, key, name in entries if key[0] >= 0 and name)


def _catalog_has(category, kind, subtype, catalog):
    return any(matches_category(category, row[0], row[1]) and row[0] == kind and (subtype < 0 or row[1] == subtype)
        for row in catalog)


def rail_entries(key, catalog):
    """The entries ((category, (kind, subtype)), name) a rail row opens into, those the catalog has, in order. A whole
    category entry ((kind, subtype) = (-1, -1)) is always there."""
    if key not in RAIL:
        return []
    result = []
    for category, sub, name in RAIL[key][2]:
        if sub == (-1, -1):
            result.append(((category, sub), name))
            continue
        names = dict(subcategories(category, catalog))
        if sub in names:
            result.append(((category, sub), name or names[sub]))
    return result


def profile(state, catalog):
    category = state.get('category', 0)
    kind, subtype = state.get('subtype', (-1, -1))
    rows = [row for row in catalog if matches_category(category, row[0], row[1])
        and (kind < 0 or kind == row[0]) and (subtype < 0 or subtype == row[1])]
    fields = set()
    flags = 0
    refines, variants, bonuses = set(), set(), set()
    for row in rows:
        flags |= row[2]
        refines.update(row[4])
        variants.update(tuple(value) for value in row[5])
        bonuses.update(row[6])
    if category in (1, 2, 3):
        if flags & 1: fields.add('job')
        if flags & 2: fields.add('gender')
    if category in (1, 2, 9) or (category == 5 and kind == 43):
        if flags & 4: fields.add('level')
    if category in (1, 2, 8) or (category == 5 and kind == 43):
        if refines and not (kind == 1 and subtype in (6, 9)): fields.add('refine')
    if category == 11: fields.add('absorption')
    if category == 6:
        fields.update(('grade', 'step', 'strength'))
    if category in (1, 2, 3, 6, 11) and bonuses:
        fields.add('applies')
    else:
        bonuses.clear()
    return {'fields': fields, 'refines': sorted(refines), 'variants': sorted(variants), 'bonuses': bonuses}


def number(value, fallback=0):
    try: return int(value)
    except (TypeError, ValueError): return fallback


def normalize(state, catalog, other=False):
    category = number(state.get('category'))
    if category not in dict(available_categories(other)): category = 0
    subtype = state.get('subtype', (-1, -1))
    subtype = tuple(subtype) if isinstance(subtype, (tuple, list)) and len(subtype) == 2 else (-1, -1)
    if subtype not in dict(subcategories(category, catalog)): subtype = (-1, -1)
    output = {'category': category, 'subtype': subtype}
    info = profile(output, catalog)
    fields = info['fields']
    for key, options in (('job', dict(JOBS)), ('gender', dict(GENDERS))):
        value = number(state.get(key), -1)
        if key in fields and value != ANY and value in options: output[key] = value
    for key in ('level', 'refine', 'absorption', 'strength'):
        if key not in fields: continue
        for bound in ('minimum_', 'maximum_'):
            field = bound + key
            value = number(state.get(field), 0 if key == 'level' else -1)
            if key == 'level' and value != 0: output[field] = value
            elif key != 'level' and value != -1:
                if key != 'refine' or value in info['refines']: output[field] = value
    if 'grade' in fields:
        for key, index in (('grade', 0), ('step', 1)):
            value = number(state.get(key), -1)
            if value in set(v[index] for v in info['variants']): output[key] = value
    if 'applies' in fields:
        rows, used = [], set()
        candidates = state.get('applies', ())
        if not isinstance(candidates, (tuple, list)): candidates = ()
        for row in candidates:
            if not isinstance(row, (tuple, list)) or len(row) != 2: continue
            kind, value = number(row[0]), number(row[1])
            if kind in info['bonuses'] and kind not in used:
                rows.append((kind, value))
                used.add(kind)
            if len(rows) == 3: break
        if rows: output['applies'] = rows
    return output


def validate(state, catalog):
    for key, maximum in (('level', 65535), ('refine', 254), ('absorption', 100), ('strength', 6)):
        low = state.get('minimum_' + key, -1)
        high = state.get('maximum_' + key, -1)
        if not (-1 <= low <= maximum and -1 <= high <= maximum):
            return key, 'Hodnota je mimo povolený rozsah.'
        if low >= 0 and high >= 0 and low > high:
            return key, 'Hodnota Od nesmí být větší než Do.'
    if any(value < -32768 or value > 32767 for _, value in state.get('applies', ())):
        return 'applies', 'Hodnota bonusu musí být od -32768 do 32767.'
    if state.get('category') == 6:
        variants = profile(state, catalog)['variants']
        if not any((state.get('grade', -1) < 0 or grade == state['grade']) and
            (state.get('step', -1) < 0 or step == state['step']) and
            (state.get('minimum_strength', -1) < 0 or strength >= state['minimum_strength']) and
            (state.get('maximum_strength', -1) < 0 or strength <= state['maximum_strength'])
            for grade, step, strength in variants):
            return 'strength', 'Tato kombinace alchymie neexistuje. Uprav třídu, čistotu nebo zesílení.'
    return None


class FilterState:
    def __init__(self, catalog=(), other=False):
        self.catalog = list(catalog)
        self.other = bool(other)
        self.applied = {'category': 0, 'subtype': (-1, -1)}
        self.draft = deepcopy(self.applied)

    def categories(self):
        return available_categories(self.other)

    def set_other_available(self, other):
        if bool(other) == self.other: return
        self.other = bool(other)
        self.applied = normalize(self.applied, self.catalog, self.other)
        self.draft = normalize(self.draft, self.catalog, self.other)

    def set_catalog(self, catalog):
        self.catalog = list(catalog)
        self.applied = normalize(self.applied, self.catalog, self.other)
        self.draft = normalize(self.draft, self.catalog, self.other)

    def open(self):
        self.draft = deepcopy(self.applied)

    def cancel(self):
        self.draft = deepcopy(self.applied)

    def change(self, **changes):
        if 'category' in changes and changes['category'] != self.draft['category']:
            self.draft['subtype'] = (-1, -1)
        self.draft.update(changes)
        self.draft = normalize(self.draft, self.catalog, self.other)

    def select_category(self, category):
        self.applied = normalize(dict(self.applied, category=category, subtype=(-1, -1)),
            self.catalog, self.other)
        self.cancel()

    def select_subcategory(self, category, subtype):
        # The market's category rail: one click sets the category and its subcategory, other filters stay.
        self.applied = normalize(dict(self.applied, category=category, subtype=tuple(subtype)),
            self.catalog, self.other)
        self.cancel()

    def reset_draft(self):
        self.draft = {'category': self.draft['category'], 'subtype': (-1, -1)}

    def set_filters(self, state):
        self.applied = normalize(state if isinstance(state, dict) else {}, self.catalog, self.other)
        self.cancel()

    def apply(self):
        candidate = normalize(self.draft, self.catalog, self.other)
        error = validate(candidate, self.catalog)
        if error: return error
        self.applied = deepcopy(candidate)
        self.draft = deepcopy(candidate)
        return None

    def arguments(self, vnums, seller, seller_exact, name='', exact=False):
        state = self.applied
        kind, subtype = state['subtype']
        extra = (state['category'], state.get('minimum_refine', -1), state.get('maximum_refine', -1),
            state.get('minimum_absorption', -1), state.get('maximum_absorption', -1),
            state.get('minimum_strength', -1), state.get('maximum_strength', -1), name, int(bool(name and exact)))
        return (list(vnums), str(seller), int(bool(seller and seller_exact)), kind, subtype,
            state.get('job', -1), state.get('gender', -1), state.get('minimum_level', 0),
            state.get('maximum_level', 0), state.get('grade', -1), state.get('step', -1),
            list(state.get('applies', ())), extra)
