# -*- coding: utf-8 -*-
"""One native scrolling dungeon guide over the connected server catalogue."""
from _weakref import proxy
import app
import bonuslabels
import net
import item
import nonplayer
import player
import skill
import ui
import uiinventoryr1 as Inventory
import wikitabs as Tabs
import uir1 as R
import uir1tokens as T
import wikiarticles as A
import wikicatalog as M
import wikihome as H
import wikiworld as W
from wikilocale import Text as L, BonusName

SECTIONS = ('overview','bonuses','gear','spells','route')
EQUIPMENT = {'weapon':'weapon','head':'head','body':'armor','shield':'shield',
 'wrist':'wrist','foots':'shoes','neck':'neck','ear':'ear','belt':'belt','glove':'glove'}
COSTUMES = {'body':'body','hair':'hair','weapon':'weapon','sash':'sash_skin',
 'aura':'aura','pet':'pet','mount':'mount','costume_body':'body',
 'costume_hair':'hair','costume_weapon':'weapon','costume_pet':'pet'}

def equipment_board(w,x,y,rows,costume=False):
    hints=Inventory.COSTUME_HINTS if costume else Inventory.EQUIPMENT_HINTS
    ox,oy=Inventory.COSTUME_SLOT_ORIGIN if costume else Inventory.EQUIPMENT_SLOT_ORIGIN
    art=ui.ImageBox();w._Keep(art,w.body,x,y,w.content);art.AddFlag('not_pick')
    art.LoadImage(Inventory.ART+('panel_costume.png' if costume else 'panel_equipment.png'))
    slots={hint:(x+ox+xx,y+oy+yy,32,height) for hint,source,xx,yy,height in hints}
    placed=set()
    for row in rows:
        hint='pet' if row['kind']=='pet' else (COSTUMES if costume else EQUIPMENT).get(row.get('slot'))
        if hint not in slots:continue
        xx,yy,ww,hh=slots[hint]
        if icon(w,row,xx,yy,ww,hh):placed.add(hint)
    for hint,source,xx,yy,height in hints:
        if hint in placed:continue
        image=ui.ImageBox();w._Keep(image,w.body,x+ox+xx,y+oy+yy,w.content)
        image.AddFlag('not_pick');image.LoadImage(Inventory.ART+'hint_'+('co' if costume else 'eq')+'_'+hint+'.png')

def fmt(value, unit=''):
    return ('%g'%float(value)).replace('.',',')+(' '+unit if unit else '')

def rank(value):
    value=int(value)
    return 'P' if value>=40 else 'G%d'%(value-29) if value>=30 else 'M%d'%(value-19) if value>=20 else str(value)

def profile(w):
    catalog=w.receiver.catalog
    boss=M.number(catalog.maps.get(w.location,{}).get('boss'))
    guide=catalog.dungeon_guides.get(boss,{})
    profiles=M.rows(guide.get('profiles'))
    return boss,guide,profiles[0] if profiles else {}

def class_row(row):
    choices=M.rows(row.get('class_skills'))
    if not choices:return row
    import chr
    job=chr.RaceToJob(net.GetMainActorRace());group=net.GetMainActorSkillGroup()
    choice=next((r for r in choices if M.number(r['job'])==job and M.number(r['group'])==group),None)
    result=dict(row);result['skill']=M.number(choice['skill']) if choice else 0
    return result

def jump(w, key):
    y=w.dungeonAnchors.get(key,0)
    w.scroll.SetPos(min(1.0,float(y)/max(1,w.bodyHeight-w.viewHeight)))
    w.Scroll();w.SaveHistory()

def band(w,title,y,width):
    w._Rect(w.body,0,y,width,23,A.BAND)
    w.ExactText(w.body,8,y+4,title,'Althea Caps:16a',T.IVORY,width=width-16)
    return y+31

def label(w,row):
    if row['kind']=='max_hp':return BonusName(item.APPLY_MAX_HP)
    if row['kind']=='defense':return BonusName(item.APPLY_DEF_GRADE_BONUS)
    if row['kind']=='buff_level':return 'Úroveň Buffi'
    if row['kind']=='buff_iq':return 'Inteligence Buffi'
    if row.get('preparation_label'):return row['preparation_label']
    if row['kind']=='apply':
        description = bonuslabels.Describe(w.ApplyText, M.number(row['apply']))
        return description[0] if description else ''
    if row.get('skill'):
        return skill.GetSkillName(M.number(row['skill']))
    if row.get('vnum'):
        return A.name(M.number(row['vnum']))
    if row['kind']=='skill' and 'effect_role' in row:
        kinds = (item.APPLY_ATT_GRADE_BONUS, item.APPLY_DEF_GRADE_BONUS, item.APPLY_RESIST_MONSTER)
        return BonusName(kinds[M.number(row['effect_role'])])
    return row.get('label','')

def remember(w,row,have=None,status=None):
    w.dungeonStatusWidgets.append((row,have,status))

def update(w):
    if not w.receiver or not w.receiver.catalog:return
    boss,guide,p=profile(w)
    values=w.dungeonStatus.get(boss,{})
    fresh=app.GetTime()-w.dungeonStatusAt.get(boss,-100)<10
    skills=tuple(class_row(row).get('skill') for row in M.rows(p.get('checks')) if row['kind']=='skill')
    if skills!=getattr(w,'dungeonSkillIds',skills):
        w.dungeonStatus.pop(boss,None);w.dungeonRequestAt=-100
        w.restoreScroll=w.scroll.GetPos();w.Draw();return
    for row,have,status in w.dungeonStatusWidgets:
        value=values.get(M.number(row['id']),-1) if fresh else -1
        need=float(row.get('need',1));known=value>=0
        optional=M.truth(row.get('optional'))
        color=(A.GREEN if known and value>0 else T.INK_DIM) if optional else A.GREEN if known and value>=need else A.RED if known else T.INK_DIM
        if have:
            boolean=row['kind'] in ('wear','alchemy','quest','talents','album','pet','consumable','growth_pet','mount_elements')
            text=L('ready') if boolean and value>=need else L('missing') if boolean and known else fmt(value,row.get('unit','')) if known else '-'
            if known and row['kind'] in ('skill','buff_skill'):text=rank(value)
            have.SetText(text);have.SetPackedFontColor(R.SignedColor(color))
        if status:
            status.SetText('' if optional else '+' if known and value>=need else 'x' if known else '-')
            status.SetPackedFontColor(R.SignedColor(color))

def request(w):
    if not w.receiver or not w.receiver.catalog or not w.NetworkReady():return
    boss,guide,p=profile(w)
    w.dungeonRequestAt=app.GetTime()
    if not p:return
    w.Send('/wiki_catalog prepare %d %d %s'%(w.receiver.nonce,boss,w.receiver.scope))

def feed(w,action,args):
    if not w.receiver or len(args)<2 or M.number(args[0])!=w.receiver.nonce:return
    boss=M.number(args[1]);catalog=w.receiver.catalog
    if not catalog or boss not in catalog.dungeon_guides:return
    if action=='prep_begin' and len(args)==4:
        profiles=M.rows(catalog.dungeon_guides[boss].get('profiles'));p=profiles[0] if profiles else {}
        count=M.number(args[2])
        valid=0<count<=128 and count==len(M.rows(p.get('checks'))) and args[3]==p.get('reference_sha256')
        w.dungeonPending=(boss,count,{}) if valid else None
    elif action=='prep_row' and len(args)==4 and w.dungeonPending and w.dungeonPending[0]==boss:
        key=M.number(args[2]);values=w.dungeonPending[2]
        try:value=float(args[3])
        except (ValueError,TypeError):w.dungeonPending=None;return
        if key in values or key<0 or key>=w.dungeonPending[1] or value!=value or abs(value)>1e12:
            w.dungeonPending=None;return
        values[key]=value
    elif action=='prep_end' and len(args)==2 and w.dungeonPending and w.dungeonPending[0]==boss:
        unused,count,values=w.dungeonPending;w.dungeonPending=None
        if len(values)==count:
            w.dungeonStatus[boss]=values;w.dungeonStatusAt[boss]=app.GetTime()
            if w.mode=='dungeons' and w.location:update(w)

def table(w,rows,y,width):
    cols=(8,int(width*.51),int(width*.69),int(width*.88))
    w._Rect(w.body,0,y,width,24,A.BAND)
    for x,key in zip(cols,('dg_bonus','have','need','status')):
        w.ExactText(w.body,x,y+5,L(key),'Noto Sans:13a',T.IVORY)
    y+=24
    for row in rows:
        w.ExactText(w.body,8,y+7,label(w,row),'Noto Sans:14a',A.GREEN,width=cols[1]-16)
        have=w.ExactText(w.body,cols[1],y+7,'-','Noto Sans:14a')
        need=fmt(row['need'],row.get('unit',''))
        if row['kind']=='skill' and M.number(row['need'])==40:need='P'
        w.ExactText(w.body,cols[2],y+7,need,'Noto Sans:14a',A.GREEN)
        status=w.ExactText(w.body,cols[3],y+7,'-','Noto Sans:14a')
        remember(w,row,have,status);w._Rect(w.body,0,y+29,width,1,T.LINE);y+=30
    return y+12

def icon(w,row,x,y,width=32,height=None):
    vnum=M.number(row.get('vnum'))
    if vnum not in w.receiver.catalog.available and vnum not in w.receiver.catalog.alchemy:return None
    obj=w._Icon(w.body,x,y,vnum,size=width,height=height)
    attrs=[(M.number(a['type']),M.number(a['value'])) for a in M.rows(row.get('attrs'))]
    stone=w.receiver.catalog.alchemy.get(vnum,{})
    attrs += [(M.number(a['type']),M.number(a['value'])) for a in M.rows(stone.get('fixed'))]
    requested={M.number(a) for a in M.rows(row.get('extras'))}
    attrs += [(M.number(a['type']),M.number(a['value'])) for a in M.rows(stone.get('extra')) if M.number(a['type']) in requested]
    sockets=[M.number(v) for v in M.rows(row.get('stones'))]
    if row.get('absorption_percent'):
        import math
        attrs=[(kind,int(math.ceil(value*M.number(row['absorption_percent'])/100.0))) for kind,value in attrs]
        obj.extraLines.append('Absorpce: '+fmt(row['absorption_percent'],'%'))
        if row.get('absorbed_vnum'):obj.extraLines.append(A.name(M.number(row['absorbed_vnum'])))
    if row.get('rarity_grade'):
        obj.extraLines.append('Rarita: '+fmt(row['rarity_grade']))
        if row.get('rarity_type'):
            bonus=bonuslabels.Describe(w.ApplyText,M.number(row['rarity_type']))
            if bonus:obj.extraLines.append(bonus[0])
    if row.get('socket_grade'):obj.extraLines.append('Osazení drahokamy: '+fmt(row['socket_grade']))
    obj.recommendation=(sockets,attrs)
    status=w.ExactText(w.body,x+width-9,y+(height or width)-12,'-','Tahoma:12ba')
    remember(w,row,status=status)
    return obj

def loot_page(w,delta):
    w.restoreScroll=w.scroll.GetPos()
    w.dungeonLootPage=max(0,w.dungeonLootPage+delta)
    w.Draw()

def draw(w,query=''):
    catalog,owner,width=w.receiver.catalog,proxy(w),w.pageWidth-8
    location=catalog.maps.get(w.location)
    w.dungeonStatusWidgets=[];w.dungeonAnchors={}
    if not location:
        A.heading(w,L('dungeons'),L('dungeons'));A.viewport(w,110)
        y=0
        for map_id,row in sorted(catalog.maps.items(),key=lambda r:catalog.MapKey(r[0])):
            if not M.number(row.get('boss')) or (query and M.folded(query) not in M.folded(row['name'])):continue
            model=W.LiveModel(w.body,0,y+1,62,88,M.number(row['boss']))
            w.modelPreviews.append(model);w.content.append(model.view)
            w._Button(w.body,76,y+9,width-82,row['name'],lambda m=map_id,r=owner:r.Navigate('dungeons',location=m),arrow=True)
            w.ExactText(w.body,83,y+44,L('level')+' '+str(row['level'])+'+','Noto Sans:14a',A.GOLD)
            w._Rect(w.body,0,y+93,width,1,T.LINE);y+=99
        return y
    boss,guide,p=profile(w)
    w.dungeonSkillIds=tuple(class_row(row).get('skill') for row in M.rows(p.get('checks')) if row['kind']=='skill')
    if w.dungeonLootBoss!=boss:w.dungeonLootPage=0;w.dungeonLootBoss=boss
    A.heading(w,L('dungeons')+' / '+location['name'],location['name'])

    Tabs.anchors(w,w,H.ARTICLE_X,98,width,[(key,L('dg_'+key)) for key in SECTIONS],
                 w.dungeonAnchors,lambda key,r=owner:jump(r,key),font='Noto Sans:16a')
    A.viewport(w,140,14);y=4;w.dungeonAnchors['overview']=0
    model=W.LiveModel(w.body,0,y,154,146,boss);w.modelPreviews.append(model);w.content.append(model.view)
    w.ExactText(w.body,170,y+2,nonplayer.GetMonsterName(boss),'Althea Caps:18a',T.IVORY,width=width-178)
    facts=[(L('level'),str(location['level'])+'+'),(L('cooldown'),str(M.number(location['cooldown'])//60)+' min'),(L('dg_entry'),L('dg_group') if M.truth(guide.get('party',location.get('group'))) else L('dg_solo'))]
    for i,(name,value) in enumerate(facts):
        w.ExactText(w.body,170,y+33+i*25,name,'Noto Sans:14a',T.INK_DIM)
        w.ExactText(w.body,width-7,y+33+i*25,value,'Noto Sans:14a',A.GOLD,align='right')
    y+=157;ticket=M.number(location['ticket'])
    if ticket:
        w._Icon(w.body,4,y,ticket,M.number(location['ticket_count']))
        w.ExactText(w.body,46,y+7,A.name(ticket),'Noto Sans:14a',width=width-55)
        y+=42
    y=band(w,L('loot'),y,width)
    loot={}
    for mob in catalog.mobs:
        if M.number(mob['vnum'])!=boss or M.number(mob['map'])!=w.location:continue
        for row in M.rows(mob.get('drops')):
            v=M.number(row['vnum'])
            if v not in catalog.available:continue
            proto=catalog.items[v]
            key=(M.family_name(A.name(v)),M.number(proto['type']),M.number(proto['subtype']),M.number(row.get('min_level')),M.truth(row.get('gloves')))
            loot.setdefault(key,{}).setdefault(v,set()).add(M.number(row['count']))
    cols=max(1,(width-8)//36)
    per_page=cols*2
    pages=max(1,(len(loot)+per_page-1)//per_page)
    page=min(w.dungeonLootPage,pages-1);w.dungeonLootPage=page
    entries=sorted(loot.items(),key=lambda row:catalog.FamilyKey(row[1]))[page*per_page:(page+1)*per_page]
    for i,(name,variants) in enumerate(entries):
        v=min(variants);quantities=sorted({n for values in variants.values() for n in values});count=str(quantities[0]) if len(quantities)==1 else '%d-%d'%(quantities[0],quantities[-1])
        obj=w._Icon(w.body,4+i%cols*36,y+i//cols*36,v,count);obj.variants={k:tuple(sorted(n)) for k,n in variants.items()}
        if name[3]:obj.extraLines.append(L('level')+' %d+'%name[3])
        if name[4]:obj.extraLines.append(L('gloves'))
    y+=((len(entries)+cols-1)//cols)*36+8
    if pages>1:
        w._Button(w.body,0,y,92,L('previous'),lambda r=owner:loot_page(r,-1))
        w.ExactText(w.body,101,y+7,'%d / %d'%(page+1,pages))
        w._Button(w.body,165,y,92,L('next'),lambda r=owner:loot_page(r,1))
        y+=31
    y+=10
    checks=M.rows(p.get('checks'))
    w.dungeonAnchors['bonuses']=y;y=band(w,L('dg_bonuses'),y,width)
    if checks:y=table(w,[r for r in checks if r['section']=='bonuses'],y,width)
    else:
        for line in A.wrap(L('dg_no_minimum'),width-16):w.ExactText(w.body,8,y,line);y+=20
        y+=12
    if not checks:
        w.dungeonAnchors.update({key:y for key in ('gear','spells')})
        return route(w,guide,boss,y,width)
    w.dungeonAnchors['gear']=y;y=band(w,L('dg_gear'),y,width)
    col=width//3
    for i,key in enumerate(('dg_basic','dg_costumes','dg_mount_alchemy')):
        w.ExactText(w.body,i*col+col//2,y,L(key),'Althea Caps:16a',T.IVORY,align='center')
        if i:w._Rect(w.body,i*col,y+25,1,242,T.LINE)
    top=y+27;bx=(col-155)//2
    equipment_board(w,bx,top,[r for r in checks if r['section']=='equipment'])
    equipment_board(w,col+(col-155)//2,top,[r for r in checks if r['section']=='costumes'],True)
    mount=[r for r in checks if r['section']=='mount']
    rx=2*col+12
    if mount:
        soul=next((row for row in mount if row['kind']=='mount'),None)
        if soul:w.ExactText(w.body,rx,top+6,L('dg_mount_soul')+' '+fmt(soul['need']),'Noto Sans:14a',A.GOLD)
        for i,row in enumerate(mount):icon(w,row,rx+i*39,top+31)
    stones=[r for r in checks if r['section']=='alchemy']
    if stones:
        w.ExactText(w.body,rx,top+84,L('dg_alchemy'),'Noto Sans:14a',A.GOLD)
        for i,row in enumerate(stones):icon(w,row,rx+i%3*39,top+109+i//3*39)
    y=top+258
    extra=[row for row in checks if row['section']=='costumes' and COSTUMES.get(row.get('slot')) not in ('body','hair','weapon','pet')]
    extra.extend(row for row in checks if row['section']=='mount')
    if extra:
        y=table(w,extra,y,width)
    w.dungeonAnchors['spells']=y;y=band(w,L('dg_spells'),y,width)
    w._Rect(w.body,0,y,width,24,A.BAND)
    for xx,key in ((8,'dg_spells'),(int(width*.55),'have'),(int(width*.73),'need')):
        w.ExactText(w.body,xx,y+5,L(key),'Noto Sans:13a',T.IVORY)
    y+=28
    skill_rows=[class_row(r) for r in checks if r['section']=='skills']
    if any(r['kind']=='skill' and not M.number(r.get('skill')) for r in skill_rows):
        y=w._Flow(y, 'Vyber zaměření postavy, aby se zobrazily její schopnosti.')+8
    for row in skill_rows:
        sid=M.number(row.get('skill'));left=8
        if sid:
            obj=w._Keep(ui.SlotWindow(),w.body,4,y,w.content);obj.SetSize(32,32);obj.AppendSlot(0,0,0,32,32)
            grade=3 if M.number(row['need'])>=40 else 2 if M.number(row['need'])>=30 else 1 if M.number(row['need'])>=20 else 0
            obj.SetSkillSlotNew(0,sid,grade,M.number(row['need']))
            obj.SetOverInItemEvent(lambda unused,s=sid,g=grade,r=owner:r.skillToolTip.SetSkillOnlyName(0,s,g))
            obj.SetOverOutItemEvent(lambda r=owner:r.HideTooltip())
            left=46
        w.ExactText(w.body,left,y+7,label(w,row),'Noto Sans:14a',width=width//2-left)
        have=w.ExactText(w.body,int(width*.55),y+7,'-');w.ExactText(w.body,int(width*.73),y+7,'—' if M.truth(row.get('optional')) else rank(row['need']) if row['kind'] in ('skill','buff_skill') else fmt(row['need']),color=A.GREEN)
        status=w.ExactText(w.body,width-24,y+7,'-');remember(w,row,have,status);y+=39
    update(w)
    return route(w,guide,boss,y,width)

def route(w,guide,boss,y,width):
    w.dungeonAnchors['route']=y;y=band(w,L('dg_route'),y,width)
    if not M.rows(guide.get('stages')):
        for line in A.wrap(L('dg_route_missing'),width-16):w.ExactText(w.body,8,y,line);y+=20
    for i,stage in enumerate(M.rows(guide.get('stages'))):
        actors=M.rows(stage.get('actors'));is_boss=any(M.number(a['vnum'])==boss for a in actors)
        w.ExactText(w.body,8,y,str(i+1),'Althea Caps:20a',A.GOLD)
        w.ExactText(w.body,43,y,stage.get('title') or (L('dg_finish') if is_boss else L('dg_clear')),'Althea Caps:18a',T.IVORY,width=width-54)
        y+=28
        if stage.get('description'):
            for line in A.wrap(stage['description'],width-54,'Noto Sans:14a'):
                w.ExactText(w.body,43,y,line,'Noto Sans:14a');y+=21
        else:
            for actor in actors:
                text=nonplayer.GetMonsterName(M.number(actor['vnum']))+' × '+str(actor['count'])
                w.ExactText(w.body,43,y,text,'Noto Sans:14a',width=width-54);y+=21
        y+=19
    update(w)
    return y
