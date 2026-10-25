# -*- coding: utf-8 -*-
"""Equipment presentation over the connected catalogue and native item proto.

No recipe, obtainable-item list, class permission bits or balance values live
here. Group definitions name native type/subtype symbols only.
"""
import item
import json
import wikicatalog as M

GROUPS = ('weapon', 'armor', 'jewelry', 'talisman', 'glove', 'belt',
          'costume', 'mount_equipment', 'rings', 'dragon_stones')
JOBS = (('WARRIOR', 'warrior', 'warrior_m'), ('ASSASSIN', 'ninja', 'assassin_w'),
        ('SURA', 'sura', 'sura_m'), ('SHAMAN', 'shaman', 'shaman_w'))
SUBTYPE_ORDER = ('SWORD', 'DAGGER', 'BOW', 'TWO_HANDED', 'BELL', 'FAN', 'MOUNT_SPEAR',
                 'BODY', 'HEAD', 'SHIELD', 'FOOTS', 'WRIST', 'NECK', 'EAR', 'PENDANT', 'TALISMAN_HEART', 'GLOVE')


def group(category):
    kind, subtype = category
    if kind == getattr(item, 'ITEM_TYPE_WEAPON', None):
        return 'weapon'
    if kind == getattr(item, 'ITEM_TYPE_ARMOR', None):
        if subtype == getattr(item, 'ARMOR_GLOVE', None):
            return 'glove'
        if subtype in [getattr(item,'ARMOR_'+s,None) for s in ('PENDANT','TALISMAN_HEART')]:
            return 'talisman'
        if subtype in [getattr(item, 'ARMOR_'+s, None) for s in ('WRIST','NECK','EAR')]:
            return 'jewelry'
        return 'armor'
    for symbols, label in ((('BELT',),'belt'), (('COSTUME',),'costume'),
                           (('MOUNT_EQUIPMENT',),'mount_equipment'),
                           (('RING','UNIQUE'),'rings'), (('DS','SPECIAL_DS'),'dragon_stones')):
        if any(kind == getattr(item, 'ITEM_TYPE_'+s, None) for s in symbols):
            return label
    return None


def permits(variants, catalog, job):
    if job is None:
        return True
    flag = getattr(item, 'ITEM_ANTIFLAG_'+job, None)
    if flag is None:
        return False
    return any(v in catalog.available and item.SelectItemWiki(v) and not item.IsAntiFlag(flag)
               for v in variants)


def families(catalog, category=None, subtype=None, job=None, query=''):
    return [(key, variants) for key, variants in catalog.Families(query=query)
            if group(key[1:]) is not None and
            (category is None or group(key[1:]) == category) and
            (subtype is None or key[1:] == subtype) and permits(variants,catalog,job)]


def categories(catalog):
    present = {group(key[1:]) for key in catalog.families}
    return [g for g in GROUPS if g in present]


def subtypes(catalog, category):
    present = {key[1:] for key in catalog.families if group(key[1:]) == category}
    order = {}
    for n,symbol in enumerate(SUBTYPE_ORDER):
        prefix = 'WEAPON_' if n < SUBTYPE_ORDER.index('BODY') else 'ARMOR_'
        value = getattr(item,prefix+symbol,None)
        if value is not None:
            kind = getattr(item,'ITEM_TYPE_WEAPON' if prefix == 'WEAPON_' else 'ITEM_TYPE_ARMOR',None)
            order[(kind,value)] = n
    return sorted(present,key=lambda cat:(order.get(cat,len(order)),cat))


def preferred_subtype(catalog, category, options, job):
    if not options:
        return None
    if category != 'weapon' or job is None:
        return options[0]
    # Prefer the selected class's own weapons over shared weapons. Permission
    # remains the native proto's decision; this only chooses the initial tab.
    def sharing(subtype):
        entries = families(catalog, category, subtype, job)
        return sum(any(permits(variants, catalog, other) for key, variants in entries)
                   for other, unused, face in JOBS)
    return min(options, key=sharing)


def grade(name):
    base, marker, value = name.rpartition('+')
    return int(value) if marker and value.isdigit() else None


def forge(catalog, variants):
    return sorted(catalog.Forge(variants),key=lambda r:(
        grade(catalog.names[M.number(r['to'])]) if grade(catalog.names[M.number(r['to'])]) is not None else -1,
        M.number(r['from'])))


def creations(catalog, variants, transforms_only=False, include_refining=False):
    """Loaded crafting/refine recipes into targets, including the exact source grade."""
    targets = set(variants)
    output = [] if transforms_only else [r for v in variants for r in catalog.recipe_index.get(v, [])]
    for source, recipe in catalog.refines.items():
        target = M.number(recipe['to'])
        if source in targets or target not in targets or source not in catalog.available or target not in catalog.available:
            continue
        same_family = M.family_name(catalog.names.get(source,'')) == M.family_name(catalog.names.get(target,''))
        if same_family and not include_refining:
            continue
        if M.number(recipe.get('chance')) <= 0 or not all(M.number(m['vnum']) in catalog.available or M.number(m['vnum']) in catalog.ingredient_sources for m in M.rows(recipe.get('materials'))):
            continue
        output.append(dict(recipe, vnum=target, count=1, npc=0, method='forge' if same_family else 'refine',
                           materials=[{'vnum':source,'count':1}]+M.rows(recipe.get('materials'))))
    unique = {recipe_key(recipe): recipe for recipe in output}
    return sorted(unique.values(), key=lambda r:catalog.ItemKey(M.number(r['vnum'])))


def recipe_key(recipe):
    # Include all terms: alternatives with different inputs/conditions are distinct.
    return json.dumps(recipe, sort_keys=True, separators=(',', ':'))


def recipe_card_owner(catalog, recipe, families):
    target = M.number(recipe['vnum'])
    # A recipe-only result has its own card in the filtered list, even on another page.
    for key, variants in families:
        if target in variants and not forge(catalog, variants):
            return key
    materials = {M.number(row['vnum']) for row in M.rows(recipe.get('materials'))}
    target_group = group((M.number(catalog.items[target]['type']), M.number(catalog.items[target]['subtype'])))
    for key, variants in families:
        if target in variants or not materials.intersection(variants):
            continue
        if (recipe.get('method') == 'refine' and M.number(recipe.get('from')) in variants) or group(key[1:]) == target_group:
            return key
    return None


def level_caption(catalog, vnum):
    from wikilocale import Text as L
    values = []
    level = M.number(catalog.items[vnum].get('level'))
    if level: values.append(L('level')+' %d+'%level)
    soul = catalog.SoulLevel(vnum)
    if soul: values.append(L('soul_level')%soul)
    return ' · '.join(values)


def uses(catalog, variants):
    """Reverse recipes grouped by actual identity, preserving refine vs craft."""
    ingredients=set(variants);by_item={v:(key,vs) for key,vs in catalog.families.items() for v in vs}
    output={}
    for kind,recipes in (('refine',catalog.refines.values()),('craft',[r for recipes in catalog.recipe_index.values() for r in recipes])):
        for recipe in recipes:
            if M.number(recipe.get('chance')) <= 0:
                continue
            if kind=='refine' and M.number(recipe['from']) not in catalog.available:
                continue
            if not all(M.number(m['vnum']) in catalog.available or M.number(m['vnum']) in catalog.ingredient_sources for m in M.rows(recipe.get('materials'))):
                continue
            target=M.number(recipe['to'] if kind=='refine' else recipe['vnum'])
            if target not in catalog.available or target not in by_item:
                continue
            if target in ingredients:
                continue
            if not (kind=='refine' and M.number(recipe['from']) in ingredients) and not any(M.number(m['vnum']) in ingredients for m in M.rows(recipe.get('materials'))):
                continue
            key,vs=by_item[target]
            row=output.setdefault(key,{'key':key,'variants':vs,'kinds':set(),'targets':set(),'sources':set()})
            row['kinds'].add(kind);row['targets'].add(target)
            if kind=='refine':row['sources'].add(M.number(recipe['from']))
    return sorted(output.values(),key=lambda r:catalog.FamilyKey(r['variants']))


def sources(catalog, variants):
    """One compact row per mob/chest path, collecting all reachable locations."""
    grouped={}
    for map_index,mob,chests,drop in catalog.Routes(variants):
        key=(mob,chests,M.number(drop.get('min_level')),M.truth(drop.get('gloves')))
        row=grouped.setdefault(key,{'mob':mob,'chests':chests,'maps':set(),
                                  'min_level':key[2],'gloves':key[3]})
        row['maps'].add(map_index)
    return sorted(grouped.values(),key=lambda r:(min(catalog.MapKey(m) for m in r['maps']),r['mob'],r['chests']))


def amount(value):
    value=M.number(value)
    for scale,suffix in ((1000000000,'kkk'),(1000000,'kk'),(1000,'k')):
        if value>=scale:
            return ('%.3f'%(value/float(scale))).rstrip('0').rstrip('.').replace('.',',')+suffix
    return str(value)
