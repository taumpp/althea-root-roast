# -*- coding: utf-8 -*-
"""Gathering guides composed from the connected server's public summaries."""
import item
import uir1 as R
import uir1tokens as T
import wikiarticles as A
import wikicatalog as M
import wikiworld as W
from wikiguides import data, number
from wikisystemguides import Guide, name


def tool(w, kind):
    catalog=w.receiver.catalog
    candidates=[v for v,p in catalog.items.items() if M.number(p.get('type'))==kind
                and (v in catalog.available or v in catalog.ingredient_sources)]
    return min(candidates,key=catalog.ItemKey) if candidates else 0


def framed_model(c, actor, x, y, width, height):
    frame = R.Frame(c.w.body,x,y,width,height,'panel',bg='panel_dark')
    c.w.content.append(frame)
    model = W.LiveModel(c.w.body,x+1,y+1,width-2,height-2,M.number(actor))
    c.w.modelPreviews.append(model);c.w.content.append(model.view)


def map_rows(c, ids):
    catalog = c.w.receiver.catalog
    return sorted({M.number(m) for m in ids if M.number(m) in catalog.maps},key=catalog.MapKey)


def map_table(c, ids):
    catalog = c.w.receiver.catalog
    c.table(['Úroveň','Mapa'],[[str(M.number(catalog.maps[m].get('level')))+'+',catalog.MapName(m)]
                             for m in map_rows(c,ids)],[.22,.78],{0:A.GOLD})


def ponds(w, values):
    catalog = w.receiver.catalog
    map_id = M.number(values['map'])
    c = Guide(w,'Jezírka','Najdi aktivní jezírko a nahoď.',['Kde je najdu','Jak lovit','Úlovky'])
    top=c.y; half=c.width//2; x=half+17; right=c.width-x
    c.w.guideAnchors['0']=top
    # Approved real screenshot, scaled uniformly inside the bordered viewport.
    photo_width=min(317,half)
    c.art('pond-scene',(half-photo_width)//2,top,width=photo_width)
    frame=R.Frame(w.body,0,top,half,210,'panel',bg=None);w.content.append(frame)
    label=catalog.MapName(map_id)+' · '+str(M.number(catalog.maps[map_id].get('level')))+'+'
    end=c.para(label,x,top+7,right,T.IVORY,17,22)
    c.para('Otevři TAB a zvol tuto mapu. Jezírka hledej přímo při průzkumu.',x,max(top+39,end+8),right)
    c.text(str(values['active'])+' aktivní jezírka',x,top+113,16,A.GOLD,width=right)
    c.text(number(M.number(values['visible_seconds'])/60.0)+' minut na jednom místě',x,top+146,width=right)
    c.text('Potom '+number(M.number(values['absent_seconds'])/60.0)+' min do nové polohy',x,top+173,width=right)
    c.y=top+235;c.index=1
    c.chapter('01   Prut, nástraha a rybářská minihra')
    rod=tool(w,getattr(item,'ITEM_TYPE_ROD',-1))
    if rod:c.icon(rod,8,c.y)
    c.y=c.para('Připrav prut a nástrahu. Postav se k okraji jezírka a nahoď směrem do vody.',54,c.y+3,c.width-54)+22
    c.step('1   Dokonči minihru','Zasáhni rybu v lovné oblasti. Potřebuješ '+str(values['goals'])+' zásahy během '+str(values['duration_seconds'])+' sekund.')
    c.step('2   Sleduj svoje okolí','Jezírko po uplynutí své doby zmizí. Další výskyt může být na jiné pozici; vyhledej aktivní jezírko znovu.')
    c.text('Lepší prut zvýší šanci na úlovek',0,c.y,18,T.IVORY,font='Althea Caps:18a');c.y+=34
    grades=M.rows(values.get('rod_grades'))
    if M.truth(values.get('rod_policy')):
        c.table(['Stupeň prutu','Základní šance'],[['+'+str(r['grade']),str(r['chance'])+' %'] for r in grades],[.55,.45],{1:A.GREEN})
        c.prose('Mezi uvedenými stupni roste šance plynule. Aktivní rybářský talent ji může dále zvýšit.')
    else:
        c.table(['Základní šance'],[[str(values['success'])+' %']],colors={0:A.GREEN})
    c.chapter('03   Co lze z jezírka získat')
    c.prose('Jezírko používá vlastní nabídku ryb. Úlovky si můžeš prokliknout na detail a jejich použití.')
    catches=sorted({M.number(r['vnum']) for r in M.rows(values.get('catches')) if M.number(r['vnum']) in catalog.items},key=catalog.ItemKey)
    cell=c.width//3
    for start in range(0,len(catches),3):
        top=c.y;ends=[]
        for j,vnum in enumerate(catches[start:start+3]):
            x=j*cell;c.icon(vnum,x+6,top+4)
            ends.append(c.para(name(w,vnum),x+45,top+8,cell-51,size=13,line=19))
        c.y=max(top+65,max(ends)+15)
    extras=M.rows(values.get('extras'))
    if extras:
        c.prose('Po úspěšném úlovku můžeš navíc získat některý z těchto předmětů:')
        for row in sorted(extras,key=lambda r:catalog.ItemKey(M.number(r['vnum']))):
            v=M.number(row['vnum']);c.icon(v,8,c.y,M.number(row['count']))
            c.y=max(c.y+45,c.para(name(w,v),52,c.y+8,c.width-52,T.IVORY)+12)
    return c


def altheits(w, values):
    catalog=w.receiver.catalog
    veins=[r for r in M.rows(values.get('veins')) if r.get('kind')=='altheit' and any(M.number(m) in catalog.maps for m in M.rows(r.get('maps')))]
    c=Guide(w,'Altheity','Vytěž žílu a využij Altheit při výrobě.',['Těžba','Kde ho najdu','Použití'])
    if not veins:
        c.prose('Na dostupných mapách aktuálně není žíla Altheitu.');return c
    c.w.guideAnchors['0']=c.y
    raw={M.number(r['vnum']) for r in veins}
    for vein in sorted(veins,key=lambda r:catalog.ItemKey(M.number(r['vnum']))):
        top=c.y;half=c.width//2;x=half+14
        framed_model(c,vein['actor'],0,top,half,210)
        c.text('Žíla Altheitu',x,top+8,18,T.IVORY,width=c.width-x)
        c.icon(vein['vnum'],x,top+47)
        c.text(name(w,vein['vnum']),x+43,top+55,15,T.IVORY,width=c.width-x-43)
        c.text('Zásoba '+format(M.number(vein['capacity']),',').replace(',',' ')+' kusů',x,top+103,16,A.GOLD,width=c.width-x)
        c.text('Nejvýše '+str(vein['maximum_per_map'])+' žíly na mapu a CH',x,top+138,width=c.width-x)
        if not M.number(vein['lifetime_max']):
            end=c.para('Zůstane na místě, dokud se jeho zásoba nevyčerpá.',x,top+171,c.width-x)
        else:
            end=c.para('Doba výskytu '+number(M.number(vein['lifetime_min'])/60.0)+'–'+number(M.number(vein['lifetime_max'])/60.0)+' minut.',x,top+171,c.width-x)
        c.y=max(top+238,end+20)
    c.index=1
    # Keep this heading under the first tab, with map/use tabs at their actual anchors.
    c.rect(0,c.y,c.width,26);c.text('01   Jak těžit Altheit',8,c.y+4,18,T.IVORY,font='Althea Caps:18a');c.y+=40
    pick=tool(w,getattr(item,'ITEM_TYPE_PICK',-1))
    if pick:c.icon(pick,8,c.y)
    c.y=c.para('Nasaď krumpáč a klikni na žílu. Při úspěšné těžbě získáš Altheit; vydané kusy se odečtou ze zásoby žíly.',54,c.y+1,c.width-54)+22
    c.prose('Po vyčerpání žíla zmizí a další výskyt se objeví na nové průchozí pozici.')
    if all(not M.number(r['refined']) for r in veins):c.prose('Altheit se nepřetavuje na zušlechtěnou rudu.')
    if M.truth(values.get('check_enabled')):
        c.prose('Těžební minihru zapneš v Knize řemesel. Dobré a skvělé zásahy zvyšují výtěžek.')
    c.chapter('02   Mapy dostupné přes TAB')
    map_table(c,[m for r in veins for m in M.rows(r['maps'])])
    c.chapter('03   Na co Altheit použiješ')
    recipes=[r for alternatives in catalog.recipe_index.values() for r in alternatives
             if M.number(r['vnum']) in catalog.available and any(M.number(m['vnum']) in raw for m in M.rows(r.get('materials')))]
    recipes=sorted(recipes,key=lambda r:(M.number(r.get('level')),catalog.ItemKey(M.number(r['vnum'])),M.number(r.get('npc')),M.number(r.get('index'))))
    if not recipes:c.prose('V aktuálním katalogu není dostupný recept používající Altheit.')
    for recipe in recipes:c.recipe(recipe)
    return c


def draw(w,guide):
    values=data(w,'ponds' if guide=='ponds' else 'mining')
    required=('map','active','visible_seconds','absent_seconds','goals','duration_seconds') if guide=='ponds' else ('veins',)
    if not values or any(key not in values for key in required):
        c=Guide(w,'Jezírka' if guide=='ponds' else 'Altheity','Aktuální údaje se načítají ze serveru.',['Začátek','Postup','Použití'])
        for label in c.labels:c.chapter(label);c.prose('Čekám na aktuální údaje ze hry.')
    else:
        c=ponds(w,values) if guide=='ponds' else altheits(w,values)
    return max(c.y+12,max(w.guideAnchors.values())+w.viewHeight if w.guideAnchors else c.y)
