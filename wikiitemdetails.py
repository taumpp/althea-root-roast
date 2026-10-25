# -*- coding: utf-8 -*-
"""Native R1 item details over the atomic connected-server snapshot."""
from _weakref import proxy
import nonplayer
import ui
import wikitabs as Tabs
import uir1 as R
import uir1tokens as T
import bonuslabels
import wikicatalog as M
import wikiequipment as E
import wikiarticles as A
import wikihome as H
from wikilocale import Text as L


KINDS = ('normal', 'addon', 'rarity', 'boss', 'metin', 'dungeon', 'speed')


def groups(catalog, vnum):
    profile = catalog.bonus_profiles.get(M.number(catalog.items.get(vnum, {}).get('bonus_profile')), {})
    # Legacy 6th/7th attribute pools are not an obtainable Althea feature.
    return [g for g in M.rows(profile.get('groups')) if g.get('kind') != 'rare']


def values(row, unit=''):
    if 'min' in row:
        low, high = M.number(row['min']), M.number(row['max'])
        text = str(low) if low == high else '%s–%s' % (low, high)
    else:
        text = ' / '.join(str(M.number(v)) for v in M.rows(row.get('values')))
    return text + (' '+unit if unit else '')


def choose(w, field, value):
    setattr(w, field, value)
    if field == 'detailKind': w.detailOption = 0
    if field == 'detailPane': w.recipeSelected = None
    w.Draw()


def segment(w, parent, x, y, width, options, selected, field):
    owner = proxy(w)
    control = Tabs.create(w,parent,x,y,width,options,selected,
                          lambda value,r=owner:choose(r,field,value),font='Noto Sans:13a')
    if field != 'itemVnum' and control.cells:
        needs=[R.TextWidth(cell.label)+24 for cell in control.cells]
        if sum(needs)<=width:
            extra=(width-sum(needs))//len(needs);left=0
            for i,(cell,need) in enumerate(zip(control.cells,needs)):
                size=width-left if i==len(needs)-1 else need+extra
                cell.Place(left,size);left+=size
    control.SetValue(selected)
    return control


def band(w, parent, x, y, width, title, color=T.IVORY):
    w._Rect(parent, x, y, width, 23, A.BAND)
    w.ExactText(parent, x+8, y+4, title, 'Althea Caps:16a', color, width=width-16)


def table(w, rows, y=0):
    width = w.pageWidth-8
    for index, row in enumerate(rows):
        kind = M.number(row['type'])
        description = bonuslabels.Describe(w.ApplyText, kind)
        label, unit = description if description else (w.ApplyText(kind, 0), '')
        value = values(row, unit)
        # Values retain their full meaning; long sets wrap inside this row.
        value_width = max(174, width*46//100)
        lines = A.wrap(value, value_width-16, 'Noto Sans:13a') or ['']
        label_lines = A.wrap(label, width-value_width-16, 'Noto Sans:14a') or ['']
        height = max(22, len(lines)*17+5, len(label_lines)*17+5)
        w._Rect(w.body, 0, y, width, height, 0xff141110)
        w._Rect(w.body, 0, y+height-1, width, 1, T.LINE)
        for n, line in enumerate(label_lines):
            w.ExactText(w.body, 8, y+4+n*17, line, 'Noto Sans:14a', A.GREEN)
        for n, line in enumerate(lines):
            w.ExactText(w.body, width-10, y+4+n*17, line, 'Noto Sans:13a', A.BLUE, align='right')
        y += height
    return y


def compact_button(w, parent, x, y, width, text, event, height=23):
    button=w._Button(parent,x,y,width,text,event)
    button.SetSize(width,height);button.band.Resize(0,0,width,height)
    button.label.SetPosition(7,1)
    return button


def source_text_width(text, font):
    probe=ui.TextLine();probe.SetFontName(font);probe.SetText(text)
    return R.TextWidth(probe)


def source_links(w, links, y, x, width):
    left, row_height = x, 24
    for label, event in links:
        size = min(width, source_text_width(label, 'Noto Sans:13a')+20)
        lines = A.wrap(label, size-16, 'Noto Sans:13a') or [label]
        height = max(24, len(lines)*17+7)
        if left > x and left+size > x+width:
            y += row_height+5; left, row_height = x, 24
        button = compact_button(w,w.body,left,y,size,'',event,height)
        button.label.SetText(label);button.label.Hide()
        for n,line in enumerate(lines):
            w.ExactText(button,8,4+n*17,line,'Noto Sans:13a',T.IVORY)
        left += size+6; row_height = max(row_height,height)
    return y+row_height+5 if links else y


def source_card(w, y, title, paths, method, header_event=None):
    catalog, owner, width = w.receiver.catalog, proxy(w), w.pageWidth-8
    caption_width=source_text_width(method,'Noto Sans:12a')+24
    title_width=max(100,width-caption_width-24)
    lines=A.wrap(title,title_width,'Althea Caps:16a') or [title]
    head=max(31,len(lines)*18+12)
    frame=R.Frame(w.body,0,y,width,head,'panel',bg='panel_dark');w.content.append(frame)
    w._Rect(w.body,2,y+2,width-4,head-3,A.BAND)
    if header_event:
        button=compact_button(w,w.body,4,y+3,title_width+8,'',header_event,head-6)
        button.label.SetText(title);button.label.Hide()
        for n,line in enumerate(lines):w.ExactText(button,8,5+n*18,line,'Althea Caps:16a',T.IVORY)
    else:
        for n,line in enumerate(lines):w.ExactText(w.body,12,y+8+n*18,line,'Althea Caps:16a',T.IVORY)
    w.ExactText(w.body,width-12,y+9,method,'Noto Sans:12a',A.GOLD,align='right')
    yy=y+head+8
    for index,path in enumerate(paths):
        if index:w._Rect(w.body,12,yy,width-24,1,T.LINE);yy+=10
        chests=path.get('chests',())
        if len(paths)>1:
            w.ExactText(w.body,12,yy,L('source_chest') if chests else L('source_direct'),'Noto Sans:13a',A.GOLD);yy+=19
        if chests:
            # Every link is visible, in order, rather than hiding the outer chests in a hover.
            links=[((' / ' if index else '')+A.name(chest),lambda v=chest,r=owner:r.OpenItem(v)) for index,chest in enumerate(chests)]
            yy=source_links(w,links,yy,12,width-24)
        conditions=[]
        if path.get('min_level'):conditions.append(L('source_drop_level')%path['min_level'])
        if path.get('gloves'):conditions.append(L('gloves'))
        for line in A.wrap(' · '.join(conditions),width-24,'Noto Sans:12a'):
            w.ExactText(w.body,12,yy,line,'Noto Sans:12a',A.GOLD);yy+=18
        levels={}
        for location in sorted(path.get('maps',()),key=catalog.MapKey):
            levels.setdefault(M.number(catalog.maps.get(location,{}).get('level')),[]).append(location)
        for level,locations in sorted(levels.items()):
            w.ExactText(w.body,18,yy+5,str(level)+'+' if level else '—','Noto Sans:13a',A.GOLD)
            links=[]
            for location in locations:
                mode='dungeons' if M.number(catalog.maps.get(location,{}).get('boss')) else 'maps'
                label=(L('dungeons') if mode=='dungeons' else L('maps')) if path.get('header_map')==location else catalog.MapName(location)
                links.append((label,lambda v=location,m=mode,r=owner:r.Navigate(m,location=v)))
            yy=source_links(w,links,yy,94,width-106)
    frame.Resize(width,max(head+8,yy-y+4))
    return yy+12


def sources(w, variants, y=0):
    catalog, owner, width = w.receiver.catalog, proxy(w), w.pageWidth-8
    actors={}
    for route in E.sources(catalog,variants):actors.setdefault(route['mob'],[]).append(route)
    missions={M.number(m['book']):m for m in catalog.missions if M.number(m['chest']) in variants and M.number(m['book']) in catalog.available}
    ingredients={}
    for v in variants:
        for route in catalog.ingredient_sources.get(v,[]):
            ingredients.setdefault((M.number(route.get('npc')),route.get('kind','')),set()).add(M.number(route['map']))
    if not actors and not missions and not ingredients:return y
    band(w,w.body,0,y,width,L('sources'))
    w.ExactText(w.body,width-8,y+5,L('source_count')%(len(actors)+len(missions)+len(ingredients)),'Noto Sans:12a',T.INK_DIM,align='right');y+=29
    w.ExactText(w.body,12,y,L('source_map_level'),'Noto Sans:12a',T.INK_DIM)
    w.ExactText(w.body,94,y,L('source_maps'),'Noto Sans:12a',T.INK_DIM);y+=23
    normalize=lambda text:' '.join(M.folded(text).replace('-',' ').split())
    for mob,paths in sorted(actors.items(),key=lambda entry:(min(catalog.MapKey(m) for path in entry[1] for m in path['maps']),entry[0])):
        paths=sorted(paths,key=lambda p:(bool(p['chests']),p['chests'],p['min_level'],p['gloves']))
        title=nonplayer.GetMonsterName(mob);event=None
        locations=set(m for path in paths for m in path['maps'])
        if len(locations)==1:
            location=next(iter(locations))
            if normalize(title)==normalize(catalog.MapName(location)):
                title=catalog.MapName(location)
                mode='dungeons' if M.number(catalog.maps.get(location,{}).get('boss')) else 'maps'
                event=lambda v=location,m=mode,r=owner:r.Navigate(m,location=v)
                paths=[dict(path,header_map=location) for path in paths]
        method=L('source_variants')%len(paths) if len(paths)>1 else L('source_chest') if paths[0]['chests'] else L('source_direct')
        y=source_card(w,y,title,paths,method,event)
    for mission in missions.values():
        book=M.number(mission['book'])
        y=source_card(w,y,A.name(book),[],L('mission_obtain'),lambda v=book,r=owner:r.OpenItem(v))
    for (npc,kind),locations in sorted(ingredients.items()):
        label=L({'shop':'source_shop','ponds':'source_fishing','fishing':'source_fishing','mining':'source_mining'}.get(kind,'sources'))
        title=nonplayer.GetMonsterName(npc) if npc else label
        y=source_card(w,y,title,[{'maps':locations}],label)
    return y

def uses(w, variants, y):
    catalog, owner, width = w.receiver.catalog, proxy(w), w.pageWidth-8
    rows = E.uses(catalog, variants)
    if not rows:
        return y
    band(w, w.body, 0, y, width, L('detail_uses')); y += 28
    w.ExactText(w.body, 44, y, L('item_detail'))
    w.ExactText(w.body, width-135, y, L('forge'))
    w.ExactText(w.body, width-8, y, L('detail_quantity'), align='right'); y += 21
    for row in rows:
        target = min(row['targets'],key=catalog.ItemKey)
        w._Button(w.body, 0, y, width, '', lambda v=target, r=owner: r.OpenItemForge(v), arrow=False)
        w._Icon(w.body, 6, y, target, size=26)
        w.ExactText(w.body, 44, y+6, row['key'][0], color=T.IVORY, width=width-208)
        caption = L('reforge') if row['sources'].intersection(variants) else w.GradeRange(sorted(row['sources'] | row['targets'])) if 'refine' in row['kinds'] else L('recipes')
        counts = ([1] if any(source in variants for source in row['sources']) else [])+[M.number(m['count']) for recipe in list(catalog.refines.values())+catalog.recipes
                  if M.number(recipe.get('to', recipe.get('vnum'))) in row['variants']
                  for m in M.rows(recipe.get('materials')) if M.number(m['vnum']) in variants]
        w.ExactText(w.body, width-135, y+6, caption, 'Noto Sans:13a', A.GOLD, width=91)
        if counts:
            amount = str(min(counts)) if min(counts)==max(counts) else '%d–%d'%(min(counts),max(counts))
            w.ExactText(w.body, width-8, y+6, amount, 'Noto Sans:13a', T.IVORY, align='right')
        y += 28
    return y


def core(w, profile, y):
    owner, width, x = proxy(w), w.pageWidth-8, H.ARTICLE_X
    all_groups = {g['kind']:g for g in profile}
    kinds = [k for k in ('boss', 'metin', 'dungeon') if k in all_groups]
    selected = w.detailKind if w.detailKind in kinds else kinds[0]
    group = all_groups[selected]
    w.ExactText(w, x, y, L('detail_core_count')%M.number(group['count']), width=width)
    segment(w, w, x, y+23, width, [(k, L('detail_'+k)) for k in kinds], selected, 'detailKind')
    row_y = y+63
    for kind in ([selected, 'cooldown'] if selected == 'dungeon' else [selected]):
        if kind not in all_groups: continue
        g = all_groups[kind]
        positive = M.number(g.get('positive'), 100)
        vals = ' / '.join(('±' if 0<positive<100 else '−' if positive==0 else '')+str(M.number(v)) for v in M.rows(g.get('values')))+' %'
        w.ExactText(w, x, row_y, L('detail_scope_'+kind), color=A.GREEN)
        w.ExactText(w, x+width-8, row_y, vals, color=A.BLUE, align='right'); row_y += 21
    if selected != 'dungeon':
        positive = M.number(group.get('positive'),100)
        w.ExactText(w, x, row_y, L('detail_signs')%(positive,100-positive), 'Noto Sans:13a'); row_y += 23
    else:
        w.ExactText(w, x, row_y, L('detail_separate_core'), 'Noto Sans:12a', width=width); row_y += 23
    A.viewport(w, row_y, 6)
    rows = M.rows(group.get('rows')); count = (len(rows)+1)//2; cell = width//2
    for index, row in enumerate(rows):
        col, line = index//max(1,count), index%max(1,count)
        location, mob = M.number(row.get('map')), M.number(row.get('mob'))
        label = w.receiver.catalog.MapName(location) if selected == 'dungeon' else nonplayer.GetMonsterName(mob)
        if selected == 'dungeon' and location not in w.receiver.catalog.maps:
            label = nonplayer.GetMonsterName(mob)
        if location in w.receiver.catalog.maps:
            compact_button(w,w.body,col*cell,line*20,cell-8,label,
                           lambda v=location, mode='dungeons' if selected=='dungeon' else 'maps', r=owner: r.Navigate(mode,location=v),20)
        else:
            w.ExactText(w.body,col*cell+7,line*20+2,label,'Noto Sans:13a',T.IVORY,width=cell-18)
    return count*20


def refining(w, selected, y):
    # The selected grade is the result: show only its actual incoming transitions.
    for recipe in E.creations(w.receiver.catalog, [selected], transforms_only=True, include_refining=True):
        y = w.DrawRecipe(y+8, recipe, show_result=False)
    return y


def draw(w):
    catalog, owner, width, x = w.receiver.catalog, proxy(w), w.pageWidth-8, H.ARTICLE_X
    if w.itemVnum not in catalog.items:
        return w._Flow(0, L('empty'))
    key, variants = w.DetailFamily()
    available = [v for v in variants if v in catalog.available] or [w.itemVnum]
    selected = w.itemVnum
    proto = catalog.items[selected]
    profile = groups(catalog, selected)
    equipment = E.group(key[1:])
    A.heading(w, w.category+' / '+L('item_detail') if w.category else L('item_detail'), '')
    w._Icon(w, x+8, 71, selected, size=32)
    w.ExactText(w, x+54, 70, key[0], 'Althea Caps:21a', T.IVORY, width=width-60)
    level = M.number(proto.get('level'))
    info = (L('level')+' %d+ · '%level if level else '')+w.GradeRange(variants)
    w.ExactText(w, x+54, 97, info, width=width-215)
    w._Button(w, x+width-151, 91, 151, L('detail_sources_forge'),
              lambda r=owner: choose(r, 'detailPane', 'sources' if r.detailPane!='sources' else 'bonuses'), arrow=False)
    if w.recipeSelected is not None:
        recipes=[r for v in variants for r in catalog.recipe_index.get(v,[])]
        if 0 <= w.recipeSelected < len(recipes):
            A.viewport(w, 127)
            return w.DrawRecipe(0, recipes[w.recipeSelected], show_result=False)
    if w.detailPane == 'forge':
        A.viewport(w, 127)
        y = w.DrawMatrix(0, key, variants, L('forge')+' '+w.GradeRange(variants))
        for recipe in catalog.recipe_index.get(selected, []):
            if E.forge(catalog,variants):y = w.DrawRecipe(y+12, recipe, show_result=False)
        return y
    if w.detailPane == 'sources' or (not profile and not equipment):
        A.viewport(w, 127)
        y = sources(w, variants)
        y = uses(w, variants, y)
        for recipe in E.creations(catalog,[selected],include_refining=True): y = w.DrawRecipe(y+8, recipe, show_result=False)
        # Chest detail preserves the complete grouped contents renderer.
        if any(v in catalog.chests for v in variants):
            band(w,w.body,0,y,width,L('loot')); y+=29
            grouped={}
            for v in variants:
                for row in catalog.chests.get(v,[]):
                    target=M.number(row['vnum']); identity=M.family_name(A.name(target))
                    grouped.setdefault(identity,{})[target]=M.number(row['count'])
            columns=max(1,width//42)
            for i,counts in enumerate(grouped.values()):
                target=min(counts);icon=w._Icon(w.body,i%columns*42,y+i//columns*42,target,counts[target]);icon.variants=counts
            y += ((len(grouped)+columns-1)//columns)*42
        return y
    forge=E.forge(catalog,variants)
    core_profile=any(g['kind'] in ('boss','metin','dungeon','cooldown') for g in profile)
    fixed_y=123
    if len(available)>1:
        options=[(v,'+'+catalog.names[v].rpartition('+')[2]) for v in available]
        # Long refining families wrap controls instead of spilling at 800x600.
        per_row=max(1,(width-80)//28)
        for index in range(0,len(options),per_row):
            subset=options[index:index+per_row]
            segment(w,w,x,123+(index//per_row)*Tabs.GAP,min(width-85,len(subset)*28),subset,selected,'itemVnum')
        fixed_y=123+((len(options)+per_row-1)//per_row)*Tabs.GAP+9
    if forge:
        w._Button(w,x+width-78,123,78,L('forge'),lambda r=owner:choose(r,'detailPane','forge'),arrow=True)
    applies=M.rows(proto.get('applies'))
    base_stats=A.BaseStats(proto)
    for line in base_stats:
        w.ExactText(w,x,fixed_y,line,'Noto Sans:14a',A.GREEN,width=width)
        fixed_y+=20
    if base_stats: fixed_y+=7
    split=width//2 if core_profile else width
    w.ExactText(w,x,fixed_y,L('detail_fixed'),'Althea Caps:15a',A.GOLD)
    if core_profile:
        for i,a in enumerate(applies):
            w.ExactText(w,x,fixed_y+23+i*19,w.ApplyText(M.number(a['type']),M.number(a['value'])),'Noto Sans:13a',A.FixedColor(M.number(a['value'])),width=split-12)
        recipes=catalog.recipe_index.get(selected,[])
        if recipes:
            recipe=recipes[0];rx=x+split+5
            w._Button(w,rx,fixed_y-6,width-split-5,L('recipes')+' · '+(L('scroll_craft') if recipe.get('method') == 'scroll' else nonplayer.GetMonsterName(M.number(recipe['npc']))),
                      lambda r=owner:r.OpenItemRecipe(0),arrow=False)
            mats=M.rows(recipe.get('materials'));cols=max(1,(width-split-5)//36)
            for i,m in enumerate(mats):w._Icon(w,rx+i%cols*36,fixed_y+22+i//cols*36,M.number(m['vnum']),M.number(m['count']))
            price=E.amount(recipe['gold'])+' Yang · '+str(M.number(recipe['chance']))+' %'
            if M.truth(recipe.get('mount_required')):price+=' · '+L('soul_level')%M.number(recipe.get('mount_level'))
            w.ExactText(w,rx,fixed_y+22+((len(mats)+cols-1)//cols)*36,price,'Noto Sans:13a',A.GOLD,width=width-split-5)
        bonus_y=max(209,fixed_y+28+len(applies)*19)
    else:
        columns=2 if len(applies)<=2 else 1
        for i,a in enumerate(applies):
            w.ExactText(w,x+(i%columns)*(width//columns),fixed_y+23+(i//columns)*19,
                        w.ApplyText(M.number(a['type']),M.number(a['value'])),'Noto Sans:13a',A.FixedColor(M.number(a['value'])),width=width//columns-8)
        bonus_y=fixed_y+32+((len(applies)+columns-1)//columns)*19
        if profile:
            bonus_y=max(208,bonus_y)
    if not profile:
        A.viewport(w,bonus_y)
        y=0
        for recipe in E.creations(catalog,[selected],include_refining=True):y=w.DrawRecipe(y,recipe,show_result=False)
        return uses(w,variants,sources(w,variants,y))
    band(w,w,x,bonus_y,width,L('detail_rolls'),A.BLUE)
    kinds=[k for k in KINDS if any(g['kind']==k for g in profile)]
    selected_kind=w.detailKind if w.detailKind in kinds else kinds[0]
    choices=[g for g in profile if g['kind']==selected_kind]
    choice=min(w.detailOption,len(choices)-1);group=choices[choice]
    changers=[M.number(v) for v in M.rows(group.get('changers'))]
    if M.number(group.get('changer')):changers.insert(0,M.number(group['changer']))
    changer=next((v for v in changers if v in catalog.items),0)
    if changer:
        w._Icon(w,x+width-182,bonus_y-4,changer,size=26)
        w.ExactText(w,x+width-150,bonus_y+6,A.name(changer),'Noto Sans:13a',T.IVORY,width=144)
    if core_profile:return refining(w,selected,core(w,profile,bonus_y+29))
    hint=L('detail_count_variable' if M.truth(group.get('variable_count')) else 'detail_count')%M.number(group.get('count'))
    if selected_kind=='addon':hint=L('detail_addon_hint')
    elif selected_kind=='rarity':hint=L('detail_rarity_hint')
    w.ExactText(w,x,bonus_y+30,hint,'Noto Sans:13a',width=width)
    y=bonus_y+55
    if len(kinds)>1:
        segment(w,w,x,y,width,[(k,L('detail_'+k)) for k in kinds],selected_kind,'detailKind');y+=34
    if len(choices)>1:
        options=[]
        for i,g in enumerate(choices):
            if selected_kind=='rarity':label=L('rarity_grade_'+str(M.number(g.get('grade'))))
            else:
                ids=[M.number(v) for v in M.rows(g.get('changers'))]
                label=A.name(next((v for v in ids if v in catalog.items),ids[0] if ids else 0))
            options.append((i,label))
        # Rows of at most three named changer/rarity choices remain readable.
        for start in range(0,len(options),3):
            segment(w,w,x,y,width,options[start:start+3],choice,'detailOption');y+=Tabs.GAP
    A.viewport(w,y,6)
    # A long reroll pool must not push the selected grade's requirements out of view.
    body_y=refining(w,selected,0)
    band(w,w.body,0,body_y,width,L('detail_bonus'),T.INK_DIM)
    w.ExactText(w.body,width-10,body_y+5,L('detail_values'),'Noto Sans:13a',T.INK_DIM,align='right')
    return table(w,M.rows(group.get('rows')),body_y+22)
