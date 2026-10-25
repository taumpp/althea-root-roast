# -*- coding: utf-8 -*-
"""R1 tables over the connected wiki catalogue. No packaged gameplay data."""
from _weakref import proxy
import bonuslabels
import bonuscolor
import item
import nonplayer
import ui
import wikitabs as Tabs
import uir1 as R
import uir1tokens as T
import wikicatalog as M
import wikiequipment as E
import wikihome as H
from wikilocale import Text as L

GOLD = 0xffd8be85
BLUE = 0xff82bfcd
GREEN = bonuscolor.POSITIVE
RED = bonuscolor.NEGATIVE
BAND = 0xff221d1c


def FixedColor(value):
    return RED if value < 0 else GREEN


def BaseStats(proto):
    """Intrinsic stats of the selected grade, using the connected server values.

    Mirrors the ordinary item tooltip's unabsorbed weapon/armor arithmetic;
    player-specific buffs, rarity and weapon-base percentages do not belong here.
    """
    values = M.rows(proto.get('values'))
    if len(values) != 6:
        return []
    values = [M.number(v) for v in values]
    kind, subtype = M.number(proto.get('type')), M.number(proto.get('subtype'))
    result = []
    def attack(label, low, high):
        if low or high:
            low, high = low+values[5], high+values[5]
            result.append(L(label)+' '+(str(low) if low == high else '%d–%d'%(low, high)))
    if kind == item.ITEM_TYPE_WEAPON:
        if subtype == getattr(item, 'WEAPON_ARROW', None):
            if values[1]: result.append(L('base_attack')+' '+str(values[1]))
        else:
            attack('base_attack', values[3], values[4])
            attack('base_magic_attack', values[1], values[2])
    elif kind == item.ITEM_TYPE_ARMOR:
        if values[1] > 0:
            result.append(L('base_defense')+' '+str(values[1]+2*values[5]))
        if values[0] > 0:
            result.append(L('base_magic_defense')+' '+str(values[0]))
    return result


def name(vnum):
    return item.GetItemName() if item.SelectItemWiki(int(vnum)) else L('unknown_item')


def viewport(w, y, bottom=14):
    w.viewHeight = w.windowHeight-y-bottom
    w.viewport.SetPosition(H.ARTICLE_X, y)
    w.viewport.SetSize(w.pageWidth, w.viewHeight)
    w.scroll.SetPosition(w.windowWidth-18, y)
    w.scroll.SetScrollBarSize(w.viewHeight)


def heading(w, section, title):
    w.ExactText(w, H.ARTICLE_X, 42, section)
    w.ExactText(w, H.ARTICLE_X, 67, title.upper(), 'Althea Caps:23a', T.IVORY,
                width=w.pageWidth-8)


def chest_rows(catalog, category=None, query=''):
    if not catalog:
        return []
    missions = {M.number(r['chest']): r for r in catalog.missions
                if M.number(r['book']) in catalog.available}
    bosses = {M.number(r['vnum']) for r in catalog.mobs if M.truth(r.get('boss'))}
    bosses.update(M.number(r.get('boss')) for r in catalog.maps.values() if M.number(r.get('boss')))
    result = []
    for vnum, contents in catalog.chests.items():
        if vnum not in catalog.available or not contents:
            continue
        routes = E.sources(catalog, [vnum])
        group = 'mission_chests' if vnum in missions else 'boss_chests' if any(
            r['mob'] in bosses for r in routes) else 'other_chests'
        if category and group != category:
            continue
        if query and M.folded(query) not in M.folded(catalog.names[vnum]):
            continue
        # Preserve real counts/grades in tooltips; one icon per family.
        grouped = {}
        for drop in contents:
            target = M.number(drop['vnum'])
            proto = catalog.items.get(target, {})
            key = (M.family_name(catalog.names.get(target, '')), M.number(proto.get('type')),
                   M.number(proto.get('subtype')))
            quantities = grouped.setdefault(key, {}).setdefault(target, set())
            quantities.add(M.number(drop['count']))
        grouped = {key: {v: next(iter(q)) if len(q) == 1 else tuple(sorted(q)) for v, q in values.items()}
                   for key, values in grouped.items()}
        result.append(dict(vnum=vnum, contents=sorted(grouped.values(), key=catalog.FamilyKey), routes=routes,
                           mission=missions.get(vnum), group=group))
    return sorted(result, key=lambda r: catalog.ChestKey(r['vnum']))


def chest_categories(catalog):
    present = {r['group'] for r in chest_rows(catalog)}
    return [key for key in ('boss_chests', 'mission_chests', 'other_chests') if key in present]


def wrap(text, width, font='Noto Sans:14a'):
    probe = ui.TextLine()
    probe.SetFontName(font)
    lines, line = [], ''
    for word in str(text).split():
        candidate = (line+' '+word).strip()
        probe.SetText(candidate)
        if line and probe.GetTextSize()[0] > width:
            lines.append(line); line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def draw_chests(w, query):
    catalog, owner = w.receiver.catalog, proxy(w)
    categories = chest_categories(catalog)
    category = w.category if w.category in categories else next(iter(categories), 'boss_chests')
    heading(w, L('chests')+' / '+L(category), L('chest_title_'+category))
    w.ExactText(w, H.ARTICLE_X, 98, L('chest_open_hint'))
    width, left = w.pageWidth-8, 48
    source = 126 if w.compact else 158
    middle = width-left-source
    w._Rect(w, H.ARTICLE_X, 122, width, 22, BAND)
    w.ExactText(w, H.ARTICLE_X+9, 126, L('chest_contents'), color=GOLD)
    w.ExactText(w, H.ARTICLE_X+width-source+8, 126,
                L('mission_obtain') if category == 'mission_chests' else L('sources'), color=GOLD)
    viewport(w, 144, 25)
    w.ExactText(w, H.ARTICLE_X, w.windowHeight-21, L('chest_random_hint'),
                'Noto Sans:13a', width=width)
    y = 0
    for row in chest_rows(catalog, category, query):
        vnum, mission, routes = row['vnum'], row['mission'], row['routes']
        columns = max(1, (middle-16)//34)
        count = len(row['contents'])
        label = name(M.number(mission['book'])) if mission else nonplayer.GetMonsterName(routes[0]['mob']) if routes else L('recipes')
        label_lines = wrap(label, source-(45 if mission else 20))
        height = max(80, 30+((count+columns-1)//columns)*34, 49+len(label_lines)*16)
        w.content.append(R.Frame(w.body, 0, y, width, height, 'panel', bg='panel_dark'))
        w._Rect(w.body, left, y, 1, height, T.LINE)
        w._Rect(w.body, width-source, y, 1, height, T.LINE)
        w._Icon(w.body, 8, y+(height-32)//2, vnum)
        title = w._Button(w.body, left+1, y+1, middle-2, '', lambda v=vnum, r=owner: r.OpenItem(v), arrow=True)
        title.label.Hide()
        w.ExactText(title, 8, 5, name(vnum), 'Althea Caps:16a', T.IVORY, width=middle-30)
        for i, values in enumerate(row['contents']):
            target = min(values)
            icon = w._Icon(w.body, left+8+i%columns*34, y+27+i//columns*34, target, values[target] if isinstance(values[target], int) else 0)
            icon.variants = values
        sx = width-source+9
        target = M.number(mission['book']) if mission else vnum
        button = w._Button(w.body, sx-4, y+24, source-10, '', lambda v=target, r=owner: r.OpenItem(v), arrow=False)
        button.SetSize(source-10, height-25)
        button.band.Resize(0, 0, source-10, height-25)
        if mission:
            w._Icon(w.body, sx, y+29, target, size=24)
        for index, line in enumerate(label_lines):
            w.ExactText(button, 4+(30 if mission else 0), 5+index*16, line, width=source-(45 if mission else 20))
        if mission:
            caption = L('level')+' %d+'%M.number(mission['level'])
        elif routes:
            locations = sorted({m for route in routes for m in route['maps']})
            level = min(M.number(catalog.maps[m].get('level')) for m in locations)
            caption = L('level')+' %d+'%level
            if len(routes) > 1:
                caption += ' · +%d'% (len(routes)-1)
        else:
            caption = L('sources_and_uses')
        w.ExactText(w.body, sx, y+height-21, caption, 'Noto Sans:13a', width=source-16)
        y += height+6
    return y if y else w._Flow(8, L('empty'))


def draw_craft(w, y, key, variants, recipes=None):
    catalog, owner = w.receiver.catalog, proxy(w)
    width = w.pageWidth-8
    split = 222 if w.compact else 270
    for recipe in E.creations(catalog, variants) if recipes is None else recipes:
        identity = E.recipe_key(recipe)
        if identity in w.drawnCraftRecipes:
            continue
        w.drawnCraftRecipes.add(identity)
        target = M.number(recipe['vnum'])
        applies=M.rows(catalog.items[target].get('applies'))
        bonuses=[(text,T.IVORY) for text in BaseStats(catalog.items[target])]
        bonuses += [(w.ApplyText(M.number(a['type']),M.number(a['value'])),
                     FixedColor(M.number(a['value']))) for a in applies]
        bonuses=[row for row in bonuses if row[0]]
        materials = M.rows(recipe.get('materials'))
        columns = max(1, (width-split-20)//37)
        material_height = max(1, (len(materials)+columns-1)//columns)*36
        conditions = []
        if M.number(recipe.get('level')):
            conditions.append(L('level')+' %d+'%M.number(recipe['level']))
        if M.truth(recipe.get('mount_required')):
            conditions.append(L('soul_level')%M.number(recipe.get('mount_level')))
        if M.truth(recipe.get('unique')):
            conditions.append(L('craft_unique'))
        if M.number(recipe.get('retained')):
            conditions.append(L('retained')+': '+name(recipe['retained']))
        condition_lines = wrap(' · '.join(conditions), width-split-20, 'Noto Sans:13a')
        maker = L('reforge') if recipe.get('method') == 'refine' else L('craft_by')+(L('scroll_craft') if recipe.get('method') == 'scroll' else nonplayer.GetMonsterName(M.number(recipe['npc'])))
        npc_lines = wrap(maker, width-split-20, 'Noto Sans:13a')
        if w.EquipmentGroup() == 'mount_equipment':
            makers = {M.number(r['npc']) for k, vs in w.Families() for v in vs for r in catalog.recipe_index.get(v, [])}
            if len(makers) == 1:
                npc_lines = []
        equipment = E.group((M.number(catalog.items[target]['type']),M.number(catalog.items[target]['subtype'])))
        tall = equipment in ('weapon', 'armor')
        icon_height = 80 if tall else 32
        bonus_x=(84 if width<600 else 96)+8 if tall else 49
        bonus_font='Noto Sans:13a' if w.compact else 'Noto Sans:14a'
        bonuses=[(line,color) for text,color in bonuses
                 for line in wrap(text,split-bonus_x-8,bonus_font)]
        material_y = 38 if tall else 9
        height = max(134 if tall else 65 if w.compact else (103 if len(bonuses)>1 else 74), 35+(20 if E.level_caption(catalog,target) else 0)+len(bonuses)*16,
                     material_y+material_height+20+16*(len(condition_lines)+len(npc_lines)))
        w.content.append(R.Frame(w.body, 0, y, width, height, 'panel', bg='panel_dark'))
        button = w._Button(w.body, 0, y, split, '', lambda v=target, r=owner: r.OpenItem(v), arrow=False)
        button.SetSize(split, height)
        button.band.Resize(0, 0, split, height)
        title_height = 29 if tall else 24
        w._Icon(w.body, ((84 if width<600 else 96)-32)//2 if tall else 8, y+title_height+6 if tall else y+16, target, M.number(recipe['count']) if M.number(recipe['count']) != 1 else 0, height=icon_height)
        if tall:
            w._Rect(w.body,2,y+2,width-4,26,BAND)
            header=w._Button(w.body,0,y,width,'',lambda v=target,r=owner:r.OpenItem(v),arrow=False)
            header.label.Hide()
            w.ExactText(header,10,6,M.family_name(name(target)),'Althea Caps:18a',T.IVORY,width=width-145)
        else:
            w.ExactText(button,49,6,key[0],'Althea Caps:16a',T.IVORY,width=split-56)
        caption = E.level_caption(catalog, target)
        if caption:
            if tall:w.ExactText(header,width-26,8,caption,'Noto Sans:13a',GOLD,align='right')
            else:w.ExactText(button,49,title_height+6,caption,'Noto Sans:13a',GOLD,width=split-58)
        for index, (label,color) in enumerate(bonuses):
            w.ExactText(button, bonus_x, title_height+6+(20 if caption and not tall else 0)+index*16, label, bonus_font, color, width=split-bonus_x-8)
        w._Rect(w.body, split, y+material_y, 1, height-material_y-9, T.LINE)
        for index, material in enumerate(materials):
            w._Icon(w.body, split+10+index%columns*37, y+material_y+index//columns*36,
                    M.number(material['vnum']), M.number(material['count']))
        price = E.amount(recipe['gold'])+' Yang · '+str(M.number(recipe['chance']))+' %'
        if M.number(recipe.get('gem')):
            price += ' · '+str(M.number(recipe['gem']))+' '+L('gaya')
        w.ExactText(w.body, split+10, y+material_y+material_height, price, color=GOLD, width=width-split-20)
        for index, line in enumerate(condition_lines+npc_lines):
            w.ExactText(w.body, split+10, y+material_y+20+material_height+index*16, line, 'Noto Sans:13a', width=width-split-20)
        y += height+5
    return y


def select_rows(catalog, choice, query=''):
    rows = list(catalog.alchemy.values())
    kinds = sorted({M.number(r['kind']) for r in rows})
    if not kinds:
        return [], (None, None, None), []
    if query:
        kinds = [k for k in kinds if any(M.folded(query) in M.folded(name(r['vnum'])) for r in rows if M.number(r['kind']) == k)]
        if not kinds:
            return [], (None, None, None), []
    kind = choice[0] if choice[0] in kinds else kinds[0]
    rows = [r for r in rows if M.number(r['kind']) == kind]
    grades = sorted({M.number(r['grade']) for r in rows})
    grade = choice[1] if choice[1] in grades else grades[-1]
    purities = sorted({M.number(r['purity']) for r in rows if M.number(r['grade']) == grade})
    purity = choice[2] if choice[2] in purities else purities[0]
    return rows, (kind, grade, purity), kinds


def segment(w, y, values, selected, field, width=None):
    owner = proxy(w)
    Tabs.create(w,w,H.ARTICLE_X,y,width or w.pageWidth-8,values,selected,
                lambda value,r=owner:r.SetAlchemy(**{field:value}))


def kind_name(row):
    # The locale's item name owns gemstone spelling (including Nefrit).
    text = M.family_name(name(row['vnum']))
    return text.split(' (')[0].split()[-1].capitalize()


def draw_alchemy(w, query=''):
    catalog, owner = w.receiver.catalog, proxy(w)
    rows, choice, kinds = select_rows(catalog, w.alchemyChoice, query)
    w.alchemyChoice = choice
    heading(w, L('equipment')+' / '+L('dragon_stones'), L('dragon_stones'))
    if not rows:
        viewport(w, 104)
        return w._Flow(8, L('empty'))
    w._Button(w, w.windowWidth-202, 64, 178, L('alchemy_back' if w.alchemyOverview else 'alchemy_overview'),
              lambda r=owner: r.SetAlchemy(overview=not r.alchemyOverview), arrow=False)
    width = w.pageWidth-8
    card = width//len(kinds)
    kind_options = []
    for index, kind in enumerate(kinds):
        candidates = [r for r in catalog.alchemy.values() if M.number(r['kind']) == kind]
        stone = max(candidates, key=lambda r:(M.number(r['grade']), -M.number(r['purity']), -M.number(r['strength'])))
        icon = w._Icon(w, H.ARTICLE_X+index*card+(card-32)//2, 100, M.number(stone['vnum']))
        # Both the native icon and its framed tab select the same gemstone.
        icon.OnMouseLeftButtonUp = lambda k=kind, r=owner: r.SetAlchemy(kind=k)
        kind_options.append((kind,kind_name(stone)))
    Tabs.create(w,w,H.ARTICLE_X,136,width,kind_options,choice[0],
                lambda kind,r=owner:r.SetAlchemy(kind=kind))
    if w.alchemyOverview:
        viewport(w, 175)
        return draw_alchemy_overview(w, rows, kinds)
    grades = sorted({M.number(r['grade']) for r in rows})
    segment(w, 177, [(g,L('alchemy_grade_'+str(g))) for g in grades], choice[1], 'grade',
            min(width, 124*len(grades)))
    purities = sorted({M.number(r['purity']) for r in rows if M.number(r['grade']) == choice[1]})
    segment(w, 213, [(p,L('alchemy_purity_'+str(p))) for p in purities], choice[2], 'purity')
    viewport(w, 253, 26)
    w.ExactText(w, H.ARTICLE_X, w.windowHeight-21, L('alchemy_hint'), 'Noto Sans:13a', width=width)
    selected = [r for r in rows if (M.number(r['grade']), M.number(r['purity'])) == choice[1:]]
    maximum = max(M.number(r['strength']) for r in rows)
    left = 218 if w.compact else 256
    cell = (width-left)//(maximum+1)
    w._Rect(w.body, 0, 0, width, 22, BAND)
    w.ExactText(w.body, 8, 4, L('alchemy_bonus'))
    for strength in range(maximum+1):
        w.ExactText(w.body, left+cell*(strength+.5), 4, '+'+str(strength), align='center')
    y = 22
    for field, color in (('fixed', GREEN), ('extra', BLUE)):
        types = list(dict.fromkeys(M.number(a['type']) for r in selected for a in M.rows(r.get(field))))
        if not types:
            continue
        caption = L('alchemy_fixed') if field == 'fixed' else L('alchemy_extra')%(
            M.number(selected[0]['extra_min']), M.number(selected[0]['extra_max']))
        w._Rect(w.body, 0, y, width, 18, 0xff1a1715 if field == 'fixed' else 0xff121c1e)
        w._Rect(w.body, 0, y, 2, 18, color)
        w.ExactText(w.body, 8, y+2, caption, 'Noto Sans:13a', color)
        y += 18
        for kind in types:
            pattern = w.ApplyText(kind, 0)
            description = bonuslabels.Describe(w.ApplyText, kind)
            label = description[0] if description else ''
            w._Rect(w.body, 0, y, width, 1, T.LINE)
            w.ExactText(w.body, 8, y+3, label, 'Noto Sans:13a', color, width=left-14)
            for strength in range(maximum+1):
                stone = next((r for r in selected if M.number(r['strength']) == strength), None)
                value = next((M.number(a['value']) for a in M.rows(stone.get(field)) if M.number(a['type']) == kind), None) if stone else None
                text = ('%+d'%value+(' %' if '%' in pattern else '')) if value is not None else '—'
                w.ExactText(w.body, left+cell*(strength+.5), y+3, text, 'Noto Sans:13a', (FixedColor(value) if field == 'fixed' else color) if value is not None else T.INK_DIM, align='center', width=cell-2)
            y += 20
    for column in range(maximum+2):
        w._Rect(w.body, left+column*cell, 0, 1, y, T.LINE)
    return y


def draw_alchemy_overview(w, rows, kinds):
    width = w.pageWidth-8
    y = w._Heading(0, L('alchemy_possible'))
    all_rows = list(w.receiver.catalog.alchemy.values())
    by_kind = {kind: [r for r in all_rows if M.number(r['kind']) == kind] for kind in kinds}
    common = set.intersection(*[{M.number(r['grade']) for r in values} for values in by_kind.values()])
    left = 99
    cell = (width-left)//len(kinds)
    for grade in sorted(common):
        w.ExactText(w.body, 0, y+12, L('alchemy_grade_'+str(grade)), color=GOLD)
        for index, kind in enumerate(kinds):
            row = min((r for r in by_kind[kind] if M.number(r['grade']) == grade), key=lambda r:M.number(r['vnum']))
            w._Icon(w.body, left+index*cell+(cell-32)//2, y, M.number(row['vnum']))
        y += 43
    for kind in kinds:
        extra = sorted({M.number(r['grade']) for r in by_kind[kind]}-common)
        if not extra:
            continue
        w.ExactText(w.body, 0, y+10, kind_name(by_kind[kind][0]), color=GOLD)
        cell = (width-left)//len(extra)
        for index, grade in enumerate(extra):
            row = min((r for r in by_kind[kind] if M.number(r['grade']) == grade), key=lambda r:M.number(r['vnum']))
            xx = left+index*cell+cell//2
            w._Icon(w.body, xx-16, y, M.number(row['vnum']))
            w.ExactText(w.body, xx, y+35, L('alchemy_grade_'+str(grade)), align='center', width=cell-4)
        y += 65
    grades = sorted({M.number(r['grade']) for r in rows})
    y = w._Heading(y, L('alchemy_caps'))
    purities = sorted({M.number(r['purity']) for r in rows})
    left = 115
    cell = (width-left)//len(purities)
    w._Rect(w.body, 0, y, width, 24, BAND)
    for index, purity in enumerate(purities):
        w.ExactText(w.body, left+cell*(index+.5), y+4, L('alchemy_purity_'+str(purity)), 'Noto Sans:13a', align='center', width=cell-4)
    y += 24
    for grade in grades:
        w.ExactText(w.body, 8, y+4, L('alchemy_grade_'+str(grade)), color=GOLD)
        for index, purity in enumerate(purities):
            values = [M.number(r['strength']) for r in rows if (M.number(r['grade']),M.number(r['purity'])) == (grade,purity)]
            w.ExactText(w.body, left+cell*(index+.5), y+4, '+'+str(max(values)) if values else '—', align='center')
        y += 25
        w._Rect(w.body, 0, y, width, 1, T.LINE)
    y = w._Heading(y+18, L('alchemy_upgrade'))
    for row in rows:
        if not row.get('grade_results'):
            continue
        text = '%d× %s · %s Yang'%(M.number(row['grade_count']), L('alchemy_grade_'+str(M.number(row['grade']))), E.amount(row['grade_fee']))
        outcomes = ['%s %g %%'%(L('alchemy_grade_'+str(M.number(r['grade']))), float(r['chance'])) for r in M.rows(row['grade_results'])]
        y = w._Flow(y, text+' → '+', '.join(outcomes))
    return y
