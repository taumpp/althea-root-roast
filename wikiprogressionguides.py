# -*- coding: utf-8 -*-
"""Approved progression guides. Text and numbers remain native/live widgets."""
import bonuslabels
import item
import ui
import uir1 as R
import uir1tokens as T
import wikiarticles as A
import wikicatalog as M
from wikiguides import data, number, yang, unavailable

ELEMENTS = (('fire','Oheň','ohně'),('ice','Led','ledu'),
            ('lightning','Blesk','blesku'),('wind','Vítr','větru'),
            ('earth','Země','země'),('dark','Temnota','temnoty'))


def art(p, name, x, y, width=None, height=None):
    return p.art('progression-'+name,x,y,width,height)


def entry(p, title, subtitle, links, icon=None):
    if icon:art(p,icon,0,6)
    p.title(title,x=32 if icon else 0)
    y=p.para(subtitle,0,40,p.width,size=16,line=22)
    p.nav(links,y+15)
    return y+60


def step(p, n, title, body, x, y, width):
    p.text(str(n),x,y,21,A.GOLD,font='Althea Caps:21a')
    p.text(title,x+29,y+2,16,T.IVORY,width=width-29)
    return p.para(body,x+29,y+29,width-29,size=15,line=21)


def frame(p,x,y,width,height):
    obj=R.Frame(p.w.body,x,y,width,height,'panel',bg='panel_dark')
    p.w.content.append(obj)


def item_name(p,vnum):
    return p.w.receiver.catalog.names.get(M.number(vnum),'')


def bonuses(p,vnum,x,y,width):
    for row in M.rows(p.w.receiver.catalog.items.get(M.number(vnum),{}).get('applies')):
        value=M.number(row.get('value'));kind=M.number(row.get('type'))
        if kind and value:
            text=p.w.ApplyText(kind,value)
            if text:y=p.para(text,x,y,width,A.FixedColor(value),15,21)
    return y


def soul_panel(p,x,y,mount):
    art(p,'surface_200x272',x,y)
    art(p,'hint-skin',x+14,y+13)
    p.text('Vzhled mounta',x+54,y+21,14,T.IVORY,width=132)
    p.rect(x+14,y+59,172,1,T.LINE)
    art(p,'level_48x64',x+14,y+73)
    p.text('Duše',x+72,y+76,18,T.IVORY,font='Althea Caps:18a')
    p.text('Úroveň 0 / '+str(mount['maximum_soul_level']),x+72,y+107,14,A.GOLD)
    p.text('Náhled systému',x+100,y+158,13,align='center')
    p.link('Nakrmit',x+43,y+210,114,lambda:None)
    p.text('Krystaly → EXP Duše',x+100,y+244,13,A.BLUE,align='center')


def pending(p,y,sections):
    # Keep the guide navigation usable before the first catalogue arrives;
    # public numbers remain explicitly unavailable, never proposal defaults.
    for index,(key,title) in enumerate(sections):
        y=p.section(key,title,y+24)
        y=p.para('Aktuální hodnoty se zobrazí po přijetí údajů ze hry.',8,y,p.width-16)+24
    return unavailable(p,y)


def mount(p):
    w=p.w;width=p.width;catalog=w.receiver.catalog;values=data(w,'mount')
    y=entry(p,'Mount a jeho Duše','Krm Duši, odemykej výbavu a posiluj svého mounta.',
            [('start','Jak začít'),('feed','Krmení'),('gear','Výbava'),('exped','Výpravy')],'glyph-mount')
    if not values:return pending(p,y,[('start','Jak začít'),('feed','Krmení'),('gear','Výbava'),('exped','Výpravy')])
    y=p.section('start','01   Jak začít',y)
    rx=width-200;soul_panel(p,rx,y,values)
    end=step(p,1,'Otevři systém mounta','V rozšířené spodní liště zvol mounta. V jeho okně najdeš Duši, výbavu i výpravy.',0,y+2,rx-18)
    end=step(p,2,'Zvyšuj úroveň Duše','Klikni na Nakrmit a vlož krystaly společníka. Každý krystal přidá zkušenosti do Duše.',0,end+23,rx-18)
    end=step(p,3,'Odemkni další výbavu','S úrovní Duše získáš další sloty. Výbavu si vyrobíš u Pacholka.',0,end+23,rx-18)
    y=max(y+272,end)+30
    y=p.para('Duše patří tvé postavě. Výměnou vzhledu mounta o její postup nepřijdeš.',0,y,width,A.GOLD,15,21)+34
    y=p.section('feed','02   Čím krmit Duši',y)
    y=p.para('Používají se stejné krystaly společníka jako pro mazlíčky. Každý druh ale dává Duši vlastní množství EXP.',0,y,width,size=15)+20
    p.rect(0,y,width,26);p.text('Krystal společníka',10,y+5,14,T.IVORY)
    p.text('EXP do Duše / kus',width-12,y+5,14,T.IVORY,align='right');y+=27
    for row in sorted(M.rows(values.get('crystals')),key=lambda r:M.number(r['experience'])):
        p.icon(row['vnum'],8,y+8);p.text(item_name(p,row['vnum']),51,y+14,16,T.IVORY,width=width-190)
        p.text(number(row['experience'])+' EXP',width-12,y+14,16,A.BLUE,align='right')
        p.rect(0,y+51,width,1,T.LINE);y+=52
    y=p.para('V okně Nakrmit vlož vybrané stacky a potvrď OK. Pravým tlačítkem výběr odebereš. Duše roste až na úroveň '+str(values['maximum_soul_level'])+'; po dosažení maxima zůstanou zbylé krystaly v inventáři.',0,y+17,width,size=15)+34
    y=p.section('gear','03   Výbava podle úrovně Duše',y)
    y=p.para('Výbavu mounta neplusuješ. Vyrobený kus nasadíš do odemčeného slotu; jeho bonusy vyžadují nasazený vzhled mounta.',0,y,width,size=15)+20
    for row in sorted(M.rows(values.get('gear')),key=lambda r:(M.number(r['soul_level']),catalog.ItemKey(M.number(r['vnum'])))):
        vnum=M.number(row['vnum'])
        if vnum not in catalog.available:continue
        p.icon(vnum,8,y+13);p.text(item_name(p,vnum),54,y+5,16,T.IVORY,width=width-180)
        p.text('Duše Lv. '+str(row['soul_level']),width-10,y+5,14,A.GOLD,align='right')
        end=bonuses(p,vnum,54,y+29,width-60);y=max(y+64,end+12)
        p.rect(0,y,width,1,T.LINE);y+=8
    if M.truth(values.get('core_requires_branches')):
        y=p.para('Prizmatické jádro nasadíš až na maximální úrovni Duše a po dokončení všech elementárních výprav.',0,y+13,width,A.GOLD,15,21)+34
    y=p.section('exped','04   Druhá cesta: elementární výpravy',y)
    for i,(key,unused,unused2) in enumerate(ELEMENTS):art(p,'element-'+key,8+i*37,y)
    y=p.para('Vedle Duše rozvíjíš šest živlů. Plněním jejich úkolů získáváš trvalou sílu živlů; krystaly tento postup nenahrazují.',0,y+43,width,size=15)+12
    p.link('Otevřít průvodce elementárními výpravami',0,y,width,lambda w=w:w.Navigate('systems',guide='expeditions'))
    return y+45


def expeditions(p):
    w=p.w;width=p.width;values=data(w,'mount')
    y=entry(p,'Elementární výpravy','Dlouhodobé cíle, které trvale posilují šest živlů.',
            [('find','Kde je najdu'),('progress','Postup'),('permanent','Trvalé bonusy'),('core','Jádro')],'glyph-elements')
    if not values:return pending(p,y,[('find','Kde výpravy najdeš'),('progress','Postup'),('permanent','Trvalé bonusy'),('core','Jádro')])
    elements=M.rows(values.get('elements'));by_id={M.number(r['id']):r for r in elements}
    y=p.section('find','01   Kde výpravy najdeš',y)
    rx=width-236;frame(p,rx-1,y-1,238,113);art(p,'detail-fire',rx,y)
    art(p,'element-fire',rx+12,y+24);p.text('Oheň',rx+49,y+25,18,T.IVORY)
    fire=M.rows(by_id.get(0,{}).get('tasks'))
    # Element IDs follow the mounted system's wire enum, not array position.
    if not fire:fire=M.rows(elements[0].get('tasks')) if elements else []
    total=sum(M.number(t.get('reward_bp')) for t in fire)
    p.text('Bonus větve',rx+16,y+66,14,A.GOLD)
    p.text('až +'+number(float(total)/100,' %'),rx+220,y+65,20,A.GREEN,align='right')
    art(p,'glyph-elements',10,y+12)
    end=p.para('V okně mounta klikni na boční ikonu živlů.',53,y+3,rx-68,T.IVORY,16,22)
    end=p.para('Vyber živel. Vpravo uvidíš jeho úkoly, postup a získaný bonus.',4,end+20,rx-19,size=15)
    y=max(y+111,end)+16
    y=p.para('Plň cíle vlastními činnostmi při hraní. Za dokončené úkoly získáváš trvalé bonusy.',0,y,width,A.GOLD,15,21)+15
    cell=(width-20)//3;image_w=cell-16;image_h=round(111*image_w/236.0);card_h=image_h+69
    for i,(key,title,form) in enumerate(ELEMENTS):
        x=(i%3)*(cell+10);yy=y+(i//3)*(card_h+12)
        frame(p,x,yy,cell,card_h);frame(p,x+7,yy+7,image_w+2,image_h+2)
        art(p,'detail-'+key,x+8,yy+8,image_w,image_h)
        art(p,'element-'+key,x+10,yy+image_h+18)
        p.text(title,x+42,yy+image_h+20,16,T.IVORY,width=cell-46)
        tasks=M.rows(by_id.get(i,{}).get('tasks'))
        maximum=sum(M.number(t.get('reward_bp')) for t in tasks)
        kind = getattr(item, 'APPLY_ENCHANT_'+('ELEC' if key=='lightning' else key.upper()), None)
        p.text(w.ApplyText(kind,maximum//100) if kind is not None else '',x+10,yy+image_h+47,14,A.GREEN,width=cell-18)
    y+=2*(card_h+12)+12
    y=p.section('progress','02   Jak se započítává postup',y)
    for i,(title,body) in enumerate((('Přečti si cíl','Každý živel má vlastní úkoly. Některé plníš bojem, jiné výrobou, sběrem nebo rozvojem postavy.'),('Plň příslušnou činnost','Postup se připisuje průběžně. U výroby a kování se počítají úspěšné akce, nákup hotového předmětu je nenahradí.'),('Dokonči úkol a získej bonus','Za každý dokončený úkol získáš sílu příslušného živlu. Bonus roste průběžně, nemusíš nejdřív dokončit celou větev.'))):
        y=step(p,i+1,title,body,0,y,width)+22
    if fire:
        p.rect(0,y,width,26);p.text('Ukázka postupu · Oheň',10,y+5,14,T.IVORY);y+=39
        art(p,'element-fire',5,y);p.text('Splň cíl uvedený v okně výprav',40,y,16,T.IVORY,width=width-130)
        p.text('0 / '+number(fire[0]['target']),width-10,y+1,14,align='right')
        p.rect(40,y+30,width-50,4);y+=61
    y=p.para('Při lovu elementárních příšer se počítají veřejné mapy, nikoli dungeonové příšery. Rozhoduje živel samotné příšery.',0,y,width,size=15)+34
    y=p.section('permanent','03   Co získáš trvale',y)
    rewards=sorted({M.number(t['reward_bp']) for r in elements for t in M.rows(r.get('tasks'))})
    reward_text=number(float(rewards[0])/100,' %') if len(rewards)==1 else 'dle konkrétního cíle'
    for label,text in (('Jeden dokončený úkol','+'+reward_text+' síly daného živlu'),('Celá větev · '+str(len(fire))+' úkolů','až +'+number(float(total)/100,' %')+' síly daného živlu')):
        p.text(label,8,y,16,T.IVORY,width=width//2)
        p.text(text,width-10,y,15,A.GREEN,align='right',width=width//2-10)
        p.rect(0,y+31,width,1,T.LINE);y+=41
    y=p.para('Každý živel se počítá samostatně. Tyto bonusy platí i bez Prizmatického jádra a bez nasazeného vzhledu mounta.',0,y+17,width,size=15)+34
    y=p.section('core','04   Dokončení všech výprav a jádro',y)
    # The last gear subtype is the native prismatic slot; use exported metadata.
    gear=M.rows(values.get('gear'));highest=max((M.number(r['subtype']) for r in gear),default=-1)
    cores=[r for r in gear if M.number(r['subtype'])==highest and M.number(r['vnum']) in w.receiver.catalog.available]
    for row in sorted(cores,key=lambda r:w.receiver.catalog.ItemKey(M.number(r['vnum']))):
        vnum=M.number(row['vnum']);p.icon(vnum,8,y+7)
        y=p.para(item_name(p,vnum),55,y,width-60,T.IVORY,18,23)
        y=p.para('Pro nasazení dosáhni maxima Duše'+(' a dokonči všechny větve výprav.' if M.truth(values.get('core_requires_branches')) else '.')+' Jádro potom rozšíří výbavu tvého mounta.',55,y+9,width-60,size=15)
        y=bonuses(p,vnum,55,y+13,width-60)+27
    p.link('Zpět na průvodce mountem a Duší',0,y,width,lambda w=w:w.Navigate('systems',guide='mount'))
    return y+43


def tree(p):
    w=p.w;width=p.width;values=data(w,'tree')
    y=entry(p,'Strom dovedností','Rozkládej předměty, získej body a sestav si vlastní bonusy.',
            [('start','Jak začít'),('points','Rozklad'),('upgrade','Vylepšování'),('active','Aktivace')])
    if not values:return pending(p,y,[('start','Jak začít'),('points','Rozklad'),('upgrade','Vylepšování'),('active','Aktivace')])
    y=p.section('start','01   Otevři strom a vyber cestu',y)
    y=p.para('Strom otevřeš ikonou u minimapy. Začni společným základem; propojené uzly ukazují, kudy můžeš pokračovat.',0,y,width,T.IVORY,16,22)+20
    image_width=min(width,760);art(p,'tree-composite',(width-image_width)//2,y,image_width)
    y+=round(image_width*516.0/884)+22
    y=p.para('Ukázka návazností. Každý uzel má vlastní podmínky; jejich splnění i dostupný bonus zjistíš po najetí myší.',0,y,width,size=15)+34
    y=p.section('points','02   Získej body rozkladem',y)
    rx=width-250;frame(p,rx,y,250,246)
    p.text('Rozklad',rx+125,y+9,18,T.IVORY,align='center',font='Althea Caps:18a')
    for row in range(3):
        for col in range(3):
            p.w.content.append(R.Ops(w.body,R.L.slot_cell(rx+77+col*32,y+45+row*32)))
    sources=M.rows(values.get('sources'));source=next((r for r in sources if M.number(r['vnum']) in w.receiver.catalog.available),None)
    if source:
        p.icon(source['vnum'],rx+77,y+45,2)
        p.text('Získáš '+number(2*M.number(source['points']))+' bodů',rx+125,y+145,15,A.GOLD,align='center')
    p.text('Limit '+format(M.number(values['point_cap']), ',').replace(',', ' ')+' bodů',rx+125,y+178,14,align='center')
    art(p,'info-book',rx+70,y+219);p.link('Rozložit',rx+104,y+214,88,lambda:None)
    end=step(p,1,'Otevři Rozklad','Ve spodní části stromu zvol Rozklad.',0,y+2,rx-16)
    end=step(p,2,'Vlož předměty','Přesuň přijímané předměty z inventáře do okna rozkladu.',0,end+20,rx-16)
    end=step(p,3,'Potvrď zisk bodů','Zkontroluj zobrazený počet bodů a klikni na Rozložit.',0,end+20,rx-16)
    y=max(y+246,end)+20
    if source:
        p.icon(source['vnum'],4,y,2);p.text('2× '+item_name(p,source['vnum']),47,y+5,16,T.IVORY,width=width-190)
        p.text(number(2*M.number(source['points']))+' bodů',width-10,y+5,16,A.GOLD,align='right');y+=49
    y=p.para('Rozklad spotřebuje vložené předměty. Ikona knihy v jeho okně otevře Hodnoty rozkladu: přijaté předměty i počet bodů za kus.',0,y,width,size=15)+34
    y=p.section('upgrade','03   Vylepšuj schopnosti',y)
    rx=width-300;frame(p,rx,y,300,176)
    p.text('Vylepšit schopnost',rx+150,y+10,18,T.IVORY,align='center',font='Althea Caps:18a')
    p.text('Bonus: aktuální → další úroveň',rx+20,y+48,15,A.GREEN,width=260)
    p.text('Cena: body a Yang',rx+20,y+78,15,A.GOLD)
    p.text('Před potvrzením zkontroluj hodnoty.',rx+20,y+105,13,width=260)
    p.link('Vylepšit',rx+53,y+139,110,lambda:None)
    p.link('Zrušit',rx+175,y+139,72,lambda:None)
    art(p,'node-color-2101',10,y+10)
    end=p.para('Najetím na uzel zjistíš jeho bonus, podmínky a cenu další úrovně.',0,y+84,rx-19,T.IVORY,15,21)
    y=max(y+176,end)+23
    y=p.para('Klikni na + u dostupné schopnosti a potvrď Vylepšit. Potřebuješ body i Yang; některé uzly také požadovanou úroveň postavy a předchozí schopnosti.',0,y,width,size=15)+20
    for title,body in (('Předchozí schopnosti','Propojovací čáry ukazují návaznost. V nápovědě zjistíš, kolik úrovní musíš mít v předchozích uzlech.'),('Naučená úroveň zůstává','Vylepšením roste hodnota bonusu. Vypršení aktivace naučené schopnosti nesmaže.')):
        p.text(title,8,y,16,T.IVORY);y=p.para(body,8,y+28,width-16,size=15)+22
    y=p.section('active','04   Zapni bonusy a prodluž jejich účinek',y+12)
    art(p,'status-on',8,y+8);p.text('Zapnout / Vypnout',45,y+10,16,T.IVORY)
    p.text('Prodloužit (+'+number(float(M.number(values['renew_seconds']))/3600)+' hod)',width-10,y+10,16,A.GOLD,align='right');y+=61
    y=p.para('Naučené bonusy se uplatní, když je strom zapnutý a zbývá mu čas. Tlačítky Zapnout a Vypnout přepínáš jejich účinek; při vypnutí se odpočet pozastaví.',0,y,width,size=15)+24
    p.rect(0,y,width,64)
    costs=M.rows(values.get('renew_items'))
    for row in costs:
        p.icon(row['vnum'],10,y+15,M.number(row['count']))
        p.text(str(row['count'])+'× '+item_name(p,row['vnum']),55,y+10,16,T.IVORY,width=width-230)
    p.text('+'+number(float(M.number(values['renew_seconds']))/3600)+' hodin účinku',55,y+36,15,A.GREEN)
    p.text('Nejvýše '+number(float(M.number(values['activation_max_seconds']))/3600)+' hodin',width-12,y+12,14,A.GOLD,align='right')
    p.text('+ cena v Yangu',width-12,y+37,14,A.GOLD,align='right');y+=82
    y=p.para('Althea žetony získáváš plněním denních úkolů. Prodloužení spotřebuje žeton a Yang; cena v Yangu roste s počtem naučených úrovní. Přesnou částku zjistíš najetím na tlačítko Prodloužit.',0,y,width,size=15)+15
    y=p.para('Cena: '+yang(values['renew_yang'])+' Yang + '+yang(values['renew_yang_per_rank'])+' Yang za každou naučenou úroveň.',0,y,width,A.GOLD,15,21)+24
    p.rect(0,y,width,28);p.text('Po vypršení času',9,y+6,15,T.IVORY);y+=43
    y=p.para('Bonusy přestanou působit, ale naučené úrovně ti zůstanou. Doplň čas a znovu zkontroluj zapnutí stromu.',0,y,width,T.IVORY,15,21)+22
    p.link('Denní úkoly a Althea žetony',0,y,width,lambda w=w:w.Navigate('systems',guide='daily'))
    return y+42


def dew_families(catalog):
    if not catalog:return []
    groups={}
    for vnum,proto in catalog.items.items():
        if 'dew_family' in proto and vnum in catalog.available:
            groups.setdefault(M.number(proto['dew_family']),[]).append(vnum)
    return [sorted(variants,key=catalog.ItemKey) for unused,variants in sorted(groups.items(),key=lambda row:catalog.FamilyKey(row[1]))]


def dews(p):
    w=p.w;catalog=w.receiver.catalog;width=p.width;mastery=data(w,'dew_mastery');families=dew_families(catalog)
    y=entry(p,'Rosy','Vyber bonus, vyrob rosu a zapni ji, když ji potřebuješ.',
            [('use','Používání'),('effects','Účinky'),('craft','Výroba'),('mastery','Znalec ros')])
    if not mastery or not families:return pending(p,y,[('use','Používání'),('effects','Účinky'),('craft','Výroba'),('mastery','Znalec ros')])
    example=max(families,key=lambda vs:len(vs));cell=(width-20)//3
    for i,vnum in enumerate(example):
        proto=catalog.items[vnum];x=i*(cell+10);frame(p,x,y,cell,85);p.icon(vnum,x+10,y+12)
        tier=item_name(p,vnum).split()[-1];p.text('Velikost '+tier,x+52,y+12,16,T.IVORY)
        p.text('Úroveň '+str(proto.get('level','?'))+'+',x+52,y+37,14,A.GOLD)
        p.text('Základ '+number(float(M.number(proto['dew_seconds']))/60)+' min',x+10,y+63,14)
    y+=109;y=p.section('use','01   Zapni rosu z inventáře',y)
    y=step(p,1,'Pravým tlačítkem zapni','Rosa začne poskytovat svůj bonus. Aktivní lahvičku poznáš podle zvýraznění v inventáři.',0,y,width)+20
    y=step(p,2,'Dalším kliknutím vypni','Bonus se vypne a zbývající čas se pozastaví. Rosu si můžeš schovat na další boj.',0,y,width)+18
    p.rect(0,y,width,47)
    for i,variants in enumerate(families[:5]):p.icon(variants[-1],10+i*38,y+7)
    p.text('Různé barvy společně',width-12,y+15,15,A.GREEN,align='right');y+=65
    y=p.para('Od každé barvy může běžet jedna rosa. S, M a L stejné barvy mezi sebou nekombinuješ.',0,y,width,T.IVORY,15,21)+17
    y=p.para('Smrt rosu nevypne. Při odhlášení se zbývající čas uloží a po přihlášení pokračuje; offline se nespotřebovává.',0,y,width,size=15)+34
    y=p.section('effects','02   Vyber účinek a velikost',y)
    y=p.para('Základní bonusy před zesílením pasivkou Znalec ros.',0,y,width,size=15)+17
    left=width-177;col=59;p.rect(0,y,width,29);p.text('Rosa a její bonus',9,y+7,14,T.IVORY)
    for i,tier in enumerate('SML'):p.text(tier,left+i*col+col//2,y+7,15,A.GOLD,align='center')
    y+=29
    for j,variants in enumerate(families):
        if j%2==0:p.rect(0,y,width,57,0xff171413)
        first=variants[0];proto=catalog.items[first];p.icon(variants[-1],7,y+12)
        p.text(item_name(p,first).rsplit(' ',1)[0],48,y+7,15,T.IVORY,width=left-52)
        effect,unit=bonuslabels.Describe(w.ApplyText,M.number(proto['dew_apply'])) or ('','')
        p.text(effect,48,y+31,13,A.GREEN,width=left-52)
        for i,vnum in enumerate(variants):
            strength=catalog.items[vnum]['dew_strength'];p.text('+'+str(strength)+(' '+unit if unit else ''),left+i*col+col//2,y+20,15,A.GREEN,align='center')
        p.rect(0,y+56,width,1,T.LINE);y+=57
    y=p.para('Silnější velikost mění hodnotu bonusu. Základní doba účinku je u všech tří velikostí stejná.',0,y+19,width,size=15)+34
    y=p.section('craft','03   Výroba ros',y)
    art(p,'open-dews',0,y)
    end=p.para('Otevři výrobu tlačítkem s červenou lahvičkou v boční liště inventáře.',55,y+2,width-60,T.IVORY,16,22)
    y=max(y+42,end)+24
    y=step(p,1,'Vyber barvu a velikost','V okně výroby vyber požadovanou rosu. U receptu uvidíš suroviny a cenu.',0,y,width)+19
    y=step(p,2,'Zkontroluj materiály a vyrob','Zvol počet kusů a potvrď výrobu. Tlačítko Max nastaví nejvyšší dostupný počet.',0,y,width)+22
    # A real current recipe, never a proposal copy. Ingredients open their detail.
    target=example[0];recipes=catalog.recipe_index.get(target,[])
    if recipes:
        p.rect(0,y,width,29);p.text('Příklad receptu · '+item_name(p,target),10,y+6,15,T.IVORY);y+=43
        for material in M.rows(recipes[0].get('materials')):
            p.icon(material['vnum'],10,y+3,M.number(material['count']))
            p.text(str(material['count'])+'× '+item_name(p,material['vnum']),53,y+1,15,T.IVORY,width=width-60);y+=40
        p.text(yang(recipes[0].get('gold'))+' Yang',53,y+4,14,A.GOLD)
        p.icon(target,width-180,y);p.text('Úspěch '+str(recipes[0].get('chance','?'))+' %',width-138,y+8,14,A.GREEN);y+=57
    y=p.para('S, M a L mají vlastní recepty. Byliny získáš také z Truhly bylinek; zdroje dalších surovin otevřeš kliknutím na předmět.',0,y,width,size=15)+34
    y=p.section('mastery','04   Pasivní schopnost Znalec ros',y)
    art(p,'mastery',0,y+1);p.text('Silnější rosy pro všechna povolání',45,y+2,17,T.IVORY,width=width-50)
    y=p.para('Pasivku najdeš mezi podpůrnými schopnostmi. Učíš ji pravým kliknutím na knihu odpovídající aktuálnímu stupni.',0,y+51,width,size=15)+20
    ranks={M.number(r['rank']):r for r in M.rows(mastery.get('ranks'))}
    books=M.rows(mastery.get('books'))
    for book in books:
        last=M.number(book['last'])+1;rank=ranks.get(last,{})
        stage='M1' if last==10 else 'G1' if last==20 else 'P' if last==30 else str(last)
        p.rect(0,y,width,96,0xff171413);p.rect(0,y+95,width,1,T.LINE)
        p.icon(book['vnum'],9,y+15);p.text(item_name(p,book['vnum']),52,y+9,16,T.IVORY,width=width-60)
        p.text('Stupně '+str(book['first'])+'–'+str(book['last'])+' · '+str(last-M.number(book['first']))+' knih',52,y+35,14,A.GOLD)
        p.text('Na '+stage+': síla ros +'+number(float(M.number(rank.get('strength_tenths')))/10,' %'),52,y+64,15,A.GREEN)
        duration=M.number(rank.get('duration_seconds'))
        if duration:p.text('Doba +'+number(float(duration)/60)+' min',width-12,y+64,15,A.GREEN,align='right')
        y+=109
    y=p.para('Každá správná kniha zlepší schopnost o jeden stupeň, vždy úspěšně a bez čekání. Kniha pro jinou etapu se nespotřebuje.',0,y,width,T.IVORY,15,21)+19
    y=p.para('Knihy získáváš z vybraných bossů a Althea meteorů. Kliknutím na knihu otevřeš její aktuální zdroje.',0,y,width,size=15)+27
    best=max(ranks) if ranks else 0;rank=ranks.get(best,{});vnum=example[-1];proto=catalog.items[vnum]
    p.rect(0,y,width,29);p.text('Co změní nejvyšší stupeň · '+item_name(p,vnum),10,y+6,15,T.IVORY,width=width-20);y+=44
    p.icon(vnum,9,y+9);x1=52;x2=width-145
    p.text('Bez pasivky',x1,y,15);p.text('Znalec ros P',x2,y,15,A.GOLD)
    base=M.number(proto['dew_strength']);boost=base*(1000+M.number(rank.get('strength_tenths')))//1000
    effect,unit=bonuslabels.Describe(w.ApplyText,M.number(proto['dew_apply'])) or ('Bonus','')
    p.text(effect,52,y-23,13,A.GREEN,width=width-60)
    p.text('+'+str(base)+unit,x1,y+29,18,A.GREEN);p.text('+'+str(boost)+unit,x2,y+29,18,A.GREEN)
    seconds=M.number(proto['dew_seconds'])
    p.text(number(float(seconds)/60)+' minut',x1,y+58,15)
    p.text(number(float(seconds+M.number(rank.get('duration_seconds')))/60)+' minut',x2,y+58,15,A.GREEN);y+=100
    y=p.para('Pasivka zesiluje hodnotu bonusu rosy. Výsledek se zaokrouhluje dolů.',0,y,width,size=15)+19
    y=p.para('Doba se může dále prodloužit zapnutým Stromem dovedností. Přesný bonus a čas pro svou postavu uvidíš v nápovědě lahvičky.',0,y,width,size=15)+23
    p.link('Strom dovedností',0,y,width,lambda w=w:w.Navigate('systems',guide='tree'))
    return y+43
