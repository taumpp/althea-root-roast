# -*- coding: utf-8 -*-
"""Approved illustrated guides, composed from native widgets and live catalogues."""
from _weakref import proxy
import json
import bonuslabels
import localeInfo
import ui
import item
import uiScriptLocale
import wikitabs as Tabs
import uir1 as R
import uir1tokens as T
import wikiarticles as A
import wikicatalog as M
import wikiworld as W

ART = 'd:/ymir work/ui/wiki/guides/'
SUPPORTED = ('daily', 'album', 'luck', 'meteors', 'tree', 'mount', 'expeditions', 'dews', 'aura', 'sash', 'resonance', 'biolog', 'afk', 'pet', 'rarity', 'ponds', 'altheits')
CYAN = 0xff70dedb
PAPER_INK = 0xff35241b
PAPER_RED = 0xff702526


def number(value, suffix=''):
    return '-' if value is None else ('%g' % float(value)).replace('.', ',')+suffix


def yang(value):
    if value is None:return '-'
    value=M.number(value)
    for scale,suffix in ((1000000000,'kkk'),(1000000,'kk'),(1000,'k')):
        if value>=scale:return number(float(value)/scale)+suffix
    return str(value)


def data(w, key):
    catalog=w.receiver.catalog if w.receiver else None
    return (catalog.systems.get(key) or {}) if catalog else {}


def jump(w, key):
    y=w.guideAnchors.get(key,0)
    w.scroll.SetPos(min(1.0,float(y)/max(1,w.bodyHeight-w.viewHeight)))
    w.Scroll();w.SaveHistory()


class Page(object):
    def __init__(self,w):
        self.w=proxy(w);self.width=w.pageWidth-16
        w.guideAnchors={}

    def text(self,value,x,y,size=14,color=T.INK_DIM,align='left',width=None,font=None):
        return self.w.ExactText(self.w.body,2 if x==0 and align=='left' else x,y,value,font or ('Noto Sans:%da'%size),color,align,width)

    def title(self,value,y=0,x=0):
        self.text(value,x,y,25,T.IVORY,font='Althea Caps:25a',width=self.width-x)

    def para(self,value,x,y,width=None,color=T.INK_DIM,size=14,line=21):
        width=width or self.width-x
        if x==0:width-=2
        for paragraph in value.split('\n'):
            for text in A.wrap(paragraph,width,'Noto Sans:%da'%size):
                self.text(text,x,y,size,color);y+=line
        return y

    def rect(self,x,y,width,height,color=A.BAND):
        self.w._Rect(self.w.body,x,y,width,height,color)

    def art(self,name,x,y,width=None,height=None):
        obj=self.w._Keep(ui.ExpandedImageBox(),self.w.body,x,y,self.w.content)
        obj.AddFlag('not_pick');obj.LoadImage(ART+name+'.png')
        if width is not None:
            if height is None:height=round(obj.GetHeight()*float(width)/max(1,obj.GetWidth()))
            obj.SetScale(float(width)/max(1,obj.GetWidth()),float(height)/max(1,obj.GetHeight()))
        return obj

    def icon(self,vnum,x,y,count=0):
        if M.number(vnum):return self.w._Icon(self.w.body,x,y,M.number(vnum),count)

    def link(self,label,x,y,width,event):
        self.w._Button(self.w.body,x,y,width,label,event,arrow=False)

    def nav(self,labels,y):
        Tabs.anchors(self.w,self.w.body,0,y,self.width,labels,self.w.guideAnchors,
                     lambda key,w=self.w:jump(w,key))

    def section(self,key,title,y,index=None):
        self.w.guideAnchors[key]=y
        if index:
            self.text('%02d'%index,0,y+3,20,A.GOLD,font='Althea Caps:20a')
            self.text(title,38,y,21,T.IVORY,font='Althea Caps:21a',width=self.width-38)
            self.rect(0,y+35,self.width,1,T.LINE)
            return y+48
        self.rect(0,y,self.width,26)
        self.text(title,8,y+4,18,T.IVORY,font='Althea Caps:18a')
        return y+40


def daily_offers(w):
    # Already selected by the same server level-shop authority as NPC opening.
    return M.rows(data(w,'daily').get('offers'))


def daily(p):
    w=p.w;width=p.width;tw=244 if width<600 else 300;half=(width-20)//2
    tokens=M.rows(data(w,'daily').get('rewards'));token=M.number(tokens[0]['vnum']) if tokens else 0
    offers=daily_offers(w)
    p.title('Denní úkoly',4)
    p.para('Hraj, plň úkoly a získávej Althea žetony.',0,43,tw,T.IVORY,15,22)
    p.para('Prodloužíš jimi strom dovedností nebo si vybereš odměny u obchodníka.',0,86,tw)
    variant='506' if width<600 else '634';hx=tw+16;hw=width-hx;cx=hx+hw//2
    p.art('tree-hero-'+variant,hx,0,width=hw,height=151)
    p.art('quest',cx-70,54);p.icon(token,cx-16,54);p.art('tree-active',cx+35,20)
    if offers:p.icon(offers[0]['vnum'],cx+35,90)
    p.text('Althea žeton',hx+hw//2,124,color=A.GOLD,align='center')
    p.nav((('start','Jak začít'),('uses','Strom dovedností'),('shop','Obchod a odměny')),163)
    p.section('start','Jak to funguje',204)
    cell=width//3
    for i,(title,body) in enumerate((('Otevři úkoly','Klikni na dopis\n„Denní úkoly“.'),('Plň zadání','Úkoly dostáváš podle\nsvé úrovně.'),('Získej žeton','Za dokončení získáš\nAlthea žeton.'))):
        x=i*cell+8;p.text('%02d'%(i+1),x,249,20,A.GOLD,font='Althea Caps:20a')
        p.text(title,x+33,252,color=T.IVORY,width=cell-43);p.para(body,x,282,cell-18)
    p.section('uses','Kam s Althea žetony',344)
    p.art('tree-active',4,385)
    if offers:p.icon(offers[0]['vnum'],half+24,385)
    for x,title,body in ((0,'Strom dovedností','Prodluž dobu, po kterou jsou naučené bonusy stromu aktivní.'),(half+20,'Obchodní cestující','Vyměň žetony za svitky a materiály. Nabídka odpovídá tvé úrovni.')):
        p.text(title,x+45,392,17,T.IVORY,width=half-45,font='Althea Caps:17a')
        p.para(body,x+4,428,half-10)
    p.rect(half+9,383,1,181,T.LINE)
    p.art('tree-strip-'+variant,4,498,width=half-8,height=47);p.art('tree-active',13,505)
    p.text('Prodloužení aktivace',53,516,13,T.IVORY,width=half-57)
    for i,r in enumerate(offers[:4]):p.icon(r['vnum'],half+25+i*42,506)
    p.link('O stromu dovedností',0,557,half-3,lambda w=w:w.Navigate('systems',guide='tree'))
    p.link('Nabídka za žetony',half+20,557,half-3,lambda w=w:jump(w,'shop'))
    p.rect(0,607,width,1,T.LINE)
    p.text('Každý den nové zadání',4,621,17,T.IVORY,font='Althea Caps:17a')
    y=p.para('Čas do další obnovy a svůj postup najdeš přímo v okně Denní úkoly.',4,650,width-8)
    y=p.section('shop','Nabídka za žetony',y+25)
    if not offers:return unavailable(p,y)
    for r in offers:
        v=M.number(r['vnum']);p.icon(v,4,y)
        p.link(A.name(v),45,y,width-49,lambda v=v,w=w:w.OpenItem(v))
        y+=36
        for material in M.rows(r.get('materials')):
            currency=M.number(material.get('vnum'));p.icon(currency,45,y,M.number(material.get('count')))
            p.text(A.name(currency),85,y+7,width=width-90);y+=38
        p.rect(0,y+2,width,1,T.LINE);y+=14
    return y


def album_example():
    # The same public hint text the Unknown card displays; never import portraits,
    # probabilities, reward amounts or growth locations from this presentation.
    try:
        with open('petalbumpresentation.txt','r') as stream:pet=json.load(stream)['pets'][0]
        hint=pet.get('first_display',{})
        return pet.get('name','Ukázka stopy'),hint.get('activity','Podle záznamu'),hint.get('when','Podle záznamu')
    except (IOError,ValueError,KeyError,IndexError,TypeError):return 'Ukázka stopy','Podle záznamu','Podle záznamu'


def album(p):
    w=p.w;width=p.width;example,activity,when=album_example()
    p.title('Pet album',2);p.text('Album najdeš v okně mazlíčka.',0,38,16,T.IVORY)
    p.nav((('clue','Získání stopy'),('notice','Oznámení'),('area','Výskyt'),('hunt','Lov'),('growth','Rozvoj')),64)
    y=p.section('clue','Jak získat první stopu',100,1)
    p.art('acquisition-paper',0,y)
    p.text('Získání',136,y+13,color=PAPER_RED,align='center',font='Tahoma:12ba')
    p.art('unknown-detail',78,y+36)
    p.text('Vzhled zatím neznámý',136,y+132,color=PAPER_RED,align='center',font='Tahoma:12ba')
    for value,yy,color in (('PRVNÍ STOPA',156,PAPER_RED),(activity,171,PAPER_INK),('KDY',186,PAPER_RED),(when,201,PAPER_INK)):
        p.text(value,8,y+yy,color=color,font='Tahoma:12a',width=256)
    for title,body,offset in (('Vyber si záznam','Otevři Album a vyber neobjeveného mazlíčka.',0),('Přečti si nápovědu','První stopa říká, koho lovit nebo co splnit. Kdy určuje čas.',78),('Opakuj danou činnost','Každé splnění správných podmínek má šanci odhalit stopu.',156)):
        p.text(title,294,y+offset,16,T.IVORY,width=width-294)
        p.para(body,294,y+offset+26,width-294,size=15)
    y=p.para('Stopa nemusí přijít napoprvé. Pokračuj, dokud se neobjeví oznámení o nové stopě.',8,y+254,width-16,A.GOLD,15)
    y=p.section('notice','Takto poznáš, že jsi objevil stopu',y+28)
    x=(width-460)//2;p.art('notice-frame',x,y);p.art('notice-symbol',x+35,y+31)
    for value,yy,font,color in (('Objevena nová stopa',32,'Tahoma:13ba',PAPER_RED),(example,55,'Tahoma:18ba',PAPER_INK),('Podrobnosti lovu najdeš v albu.',87,'Tahoma:11a',0xff63462f)):
        p.text(value,x+285,y+yy,color=color,align='center',font=font)
    y=p.para('Toto oznámení se objeví přímo při hraní. Stopu pak najdeš uloženou v albu — otevři její záznam a pokračuj přes Výskyt.',8,y+162,width-16,T.IVORY,16,22)
    y=p.para('Stopa je začátek lovu. Bonus získáš až ulovením.',8,y+12,width-16,A.GOLD)
    y=p.section('area','Ze stopy do hledané oblasti',y+30,2)
    p.text('V albu klikni na Výskyt',12,y+7,16,T.IVORY);p.text('Prohledej zlatý kruh',width-216,y+7,16,A.GOLD)
    p.art('clue-paper',12,y+39);p.art('paw-58',89,y+78)
    p.text('Získání',118,y+52,color=PAPER_RED,align='center',font='Tahoma:12ba')
    p.text('STOPA OBJEVENA',118,y+144,color=PAPER_RED,align='center',font='Tahoma:12ba')
    p.art('button-normal',50,y+166);p.text('Výskyt',118,y+172,color=T.IVORY,align='center',font='Tahoma:12a')
    p.art('atlas-fragment',width-216,y+31)
    p.text('Detail objevené stopy',118,y+220,13,align='center')
    y=p.para('Oblast a kanál jsou přidělené tvé stopě. Ve Výskytu zkontroluj také dobu lovu; kruh označuje oblast k prohledání.',8,y+257,width-16,T.IVORY,16,22)
    y=p.para('Mimo dobu lovu zůstává tlačítko Výskyt neaktivní.',8,y+12,width-16)
    y=p.section('hunt','Svůj cíl poznáš podle kruhu',y+30,3)
    p.text('Tyrkysová značka pod příšerou',0,y+6,16,CYAN)
    p.art('hunt-ring',2,y+33,width=218,height=218);p.art('ground-ring-example',width-264,y+41)
    p.text('Kruh leží na zemi pod cílem.',width-136,y+227,14,CYAN,'center')
    y=p.para('Značku vidíš jen ty. Poraz takto označenou příšeru uvnitř hledané oblasti; porážka se musí připsat tobě.',8,y+264,width-16,T.IVORY,16,22)
    y=p.para('Když cíl zmizí nebo ho porazí jiný hráč, stopa ti zůstane.',8,y+12,width-16)
    y=p.section('growth','Úlovek odhalí záznam i bonus',y+30,4)
    y=p.para('Po ulovení se ti v albu odhalí podoba mazlíčka a začne platit jeho bonus. Záložka Expení pak ukáže podmínky dalšího rozvoje.',8,y+6,width-16,T.IVORY,16,22)
    a=data(w,'album');maximum=number(a.get('max_level'))
    y+=20;p.text('Úroveň 1',8,y,15,A.GREEN);p.text('Úroveň '+maximum,width-8,y,15,A.GREEN,'right')
    ix=(width-265)//2;p.art('progress-empty',ix,y+5);p.art('progress-left',ix,y+5);p.art('progress-middle',ix+3,y+5,width=170,height=7);p.art('progress-right',ix+173,y+5)
    p.text('Rozvojem zvyšuješ bonus záznamu.',width//2,y+31,15,A.GREEN,'center')
    y=p.section('rewards','Za co získáš odměny',y+67)
    book_label = uiScriptLocale.PET_ALBUM_V7_SILA_KNIH_PETA_S_S.split('+',1)[0].strip()
    def chapter_bonus(key, kind):
        value = a.get(key)
        return w.ApplyText(kind,M.number(value)) if value is not None else '-'
    rows=(('Ulovíš celou kapitolu',chapter_bonus('chapter_attack',item.APPLY_ATT_GRADE_BONUS)+' · '+chapter_bonus('chapter_magic_attack',item.APPLY_MAGIC_ATT_GRADE)),('Záznam dosáhne úrovně '+maximum,book_label+' +'+number(a.get('book_per_max_percent'))+' %'),('Rozvineš celé album na maximum',book_label+' +'+number(a.get('book_complete_percent'))+' %'))
    for trigger,reward in rows:
        if width<600:
            p.text(trigger,8,y,14,width=width-16);p.text(reward,8,y+21,14,A.GREEN,width=width-16);step=49
        else:
            p.text(trigger,8,y,14,width=width//2-8);p.text(reward,width-8,y,14,A.GREEN,'right',width//2-8);step=35
        p.rect(8,y+step-8,width-16,1,T.LINE);y+=step
    return p.para('Bonus „'+book_label+'“ posiluje schopnosti mazlíčka naučené z knih. Bonusy alba má postava i bez přivolaného mazlíčka.',8,y+5,width-16)


def unavailable(p,y):
    p.para('Aktuální údaje nejsou k dispozici.',8,y,p.width-16)
    p.link('Obnovit údaje',0,y+28,180,lambda w=p.w:w.Refresh())
    return y+70


def luck(p):
    w=p.w;width=p.width;luck=data(w,'luck');levels=M.rows(luck.get('levels'))
    p.art('uzel_stesti',0,4);p.title('Uzel štěstí',1,43)
    p.text('Vylepši své štěstí. Přivolej Althea meteor.',0,41,16)
    p.nav((('start','Jak začít'),('levels','Stupně a bonusy'),('meteor','Althea meteor'),('protection','Ochrana a drop')),73)
    y=p.section('start','Jak uzel vylepšit',118,1)
    p.rect(0,y,153,80);p.text('Schopnosti',10,y+8)
    for i,a in enumerate(('bossologie','kamenologie','uzel_stesti')):p.art(a,12+i*37,y+32)
    p.art('plus',106,y+52)
    p.para('V okně postavy otevři Schopnosti a klikni na + u Uzlu štěstí.',171,y+2,width-176,T.IVORY,16,23)
    p.para('V potvrzovacím okně zvol Vylepšit.',171,y+56,width-176,size=15)
    y+=101;half=(width-14)//2
    for i,(key,title,system) in enumerate((('stone_seal','Pečeť meteorů','Kamenologie'),('boss_seal','Pečeť bossů','Bossologie'))):
        x=i*(half+14);p.icon(luck.get(key),x+4,y+6)
        p.text(number(luck.get('seal_count'))+'× '+title,x+45,y+3,16,T.IVORY,width=half-45)
        p.text('Vybrané stupně '+system,x+45,y+28,width=half-45);p.rect(x,y+58,half,1,T.LINE)
    y=p.para('V Trvalých úkolech plň Kamenologii i Bossologii a vyzvedávej odměny. Pečetě získáš za vybrané stupně obou lovů.',0,y+75,width,size=16,line=22)
    y+=18;p.rect(0,y,width,41);p.text('První stupeň',10,y+11,15,T.IVORY)
    p.text(yang(levels[0].get('yang') if levels else None)+' Yang',width//2,y+11,16,A.GOLD,'center')
    p.text('Jisté vylepšení',width-10,y+11,15,A.GREEN,'right')
    y=p.section('levels','Stupně a trvalé bonusy',y+67,2)
    p.text('Bonusy daného stupně platí trvale.',8,y-2,16)
    y+=34
    if levels:
        # Column width follows the active catalogue, never a fixed number of ranks.
        labelwidth=190 if width<600 else 224;cw=(width-labelwidth)//len(levels)
        if cw<35:
            for level in levels:
                y=p.section('level-'+str(level['level']),'Stupeň '+str(level['level']),y)
                for key,label,unit in effect_rows():
                    value=effect_value(level,key,unit);p.text(label,8,y,width=width-110);p.text(value,width-8,y,color=A.GREEN,align='right');y+=27
        else:
            p.rect(0,y,width,29);p.text('Stupeň uzlu',8,y+6,color=A.GOLD)
            for i,level in enumerate(levels):p.text(str(level['level']),labelwidth+i*cw+cw//2,y+6,15,T.IVORY,'center')
            y+=29
            for key,label,unit in effect_rows():
                p.text(label,8,y+8,13,T.IVORY,width=labelwidth-12)
                for i,level in enumerate(levels):p.text(effect_value(level,key,unit),labelwidth+i*cw+cw//2,y+7,13,A.GREEN if unit=='bp' else A.GOLD,'center')
                p.rect(0,y+32,width,1,T.LINE);y+=33
        y=p.para('Šance na raritu pomáhá při prvním nasazení rarity. Nemění přetáčení ani povyšování již nasazené rarity.',8,y+14,width-16,size=14)
    else:y=unavailable(p,y)
    y=p.section('meteor','Takto poznáš Althea meteor',y+30,3)
    tiers=M.rows(data(w,'meteors')) if isinstance(data(w,'meteors'),list) else []
    catalog=w.receiver.catalog if w.receiver else None
    visible={M.number(m['vnum']) for m in catalog.mobs} if catalog else set()
    vnum=next((M.number(t['vnum']) for t in tiers if M.number(t.get('vnum')) in visible),0)
    if vnum:
        model=W.LiveModel(w.body,0,y,219,278,vnum);w.modelPreviews.append(model);w.content.append(model.view)
    p.text('Althea meteor',109,y+279,18,T.IVORY,'center',font='Althea Caps:18a')
    x=238;room=width-x
    yy=p.para('Objeví se u tebe při ničení běžných meteorů.',x,y+4,room,T.IVORY,17,24)
    yy=p.para('Uzel štěstí ti na něj přidává šanci. Neobjeví se po každém zničení.',x,yy+12,room,size=16,line=23)
    rules=data(w,'meteor_rules')
    yy=p.para('Lov na podporované veřejné mapě. Rozdíl mezi tvou úrovní a úrovní meteoru může být nejvýše '+number(rules.get('maximum_level_difference'))+'.',x,yy+12,room,size=16,line=23)
    yy=p.para('V dungeonech se nevyvolává. Althea meteor další Althea meteor nepřivolá.',x,yy+12,room,size=15,line=22)
    y=max(y+320,yy+22);p.text('Když se objeví, uvidíš toto oznámení:',0,y,16,T.IVORY)
    nw=min(width,520);nx=(width-nw)//2;p.art('meteor-notice',nx,y+31,width=nw,height=166)
    p.text('Althea meteor',nx+int(295*nw/520),y+108,20,A.GOLD,'center',font='Tahoma:20ba')
    y=p.para('Rozhlédni se hned vedle postavy. Stupeň meteoru a jeho odměny závisejí na mapě.',0,y+206,width,size=16,line=22)
    y=p.section('protection','Tvůj meteor a jeho odměny',y+30,4)
    tooltip(p,y,True);minutes=number(float(rules['protection_seconds'])/60) if 'protection_seconds' in rules else '-'
    yy=p.para('Prvních '+minutes+' minut je chráněný pro tebe.',260,y+2,width-260,T.IVORY,17,24)
    yy=p.para('Útočit na něj můžeš jen ty. Po najetí myší uvidíš zbývající čas.',260,yy+10,width-260,size=16,line=23)
    y=max(y+112,yy+16);tooltip(p,y,False)
    yy=p.para('Po vypršení ochrany je volný pro všechny.',260,y+8,width-260,size=16,line=23)
    y=max(y+112,yy+20);p.rect(0,y,width,1,T.LINE)
    y=p.para('Možné odměny najdeš u příslušného Althea meteoru. Na předmět můžeš kliknout a otevřít jeho detail.',0,y+18,width,size=16,line=23)
    w.guideAnchors['loot']=y+16
    p.link('Prohlédnout Althea meteory a drop',0,y+14,min(width,330),lambda w=w:jump(w,'loot'))
    y+=54
    for tier in tiers:
        actor=M.number(tier.get('vnum'))
        if actor not in visible:continue
        import nonplayer
        p.text(nonplayer.GetMonsterName(actor),0,y,18,T.IVORY,font='Althea Caps:18a');y+=32
        loot=[r for mob in catalog.mobs if M.number(mob['vnum'])==actor for r in M.rows(mob.get('drops'))]
        y=w.DrawLoot(y,loot)+16
    return y


def effect_rows():
    effects = (('spawn_bp', localeInfo.LUCK_KNOT_METEOR),
               ('meteor_double_bp', localeInfo.LUCK_KNOT_DOUBLE_METEOR),
               ('boss_double_bp', localeInfo.LUCK_KNOT_DOUBLE_BOSS),
               ('rarity_bp', localeInfo.LUCK_KNOT_RARITY))
    names = tuple((key, bonuslabels.Describe(lambda text, value: text % value, template)[0], 'bp')
                  for key, template in effects)
    return names + (('minimum_level','Od úrovně','level'),('yang','Cena vylepšení','yang'))


def effect_value(row,key,unit):
    value=row.get(key)
    if value is None:return '-'
    if unit=='bp':return number(float(value)/100,' %') if M.number(value) else '—'
    if unit=='yang':return yang(value)
    return str(value) if M.number(value) else '—'


def tooltip(p,y,owner):
    # Embedded illustration of the existing R1 tooltip; it is not player state.
    frame=R.Frame(p.w.body,0,y,240,94,'tooltip');p.w.content.append(frame)
    for text,yy,color,font in (('Althea meteor',12,0xfff0dfba,'Tahoma:14a'),('Tvůj meteor' if owner else 'Volný pro všechny',40,A.GOLD if owner else A.GREEN,'Tahoma:12a'),('Ochrana 08:42' if owner else 'Může útočit každý',61,T.INK_DIM,'Tahoma:12a')):
        p.text(text,120,y+yy,color=color,align='center',font=font)


def draw(w,guide):
    if guide in ('aura', 'sash', 'resonance', 'biolog', 'afk', 'pet', 'rarity'):
        import wikisystemguides
        return wikisystemguides.draw(w, guide)
    if guide in ('ponds', 'altheits'):
        import wikigatheringguides
        return wikigatheringguides.draw(w, guide)
    p=Page(w)
    if guide in ('tree', 'mount', 'expeditions', 'dews'):
        import wikiprogressionguides
        end=getattr(wikiprogressionguides,guide)(p)
    else:
        end=daily(p) if guide=='daily' else album(p) if guide=='album' else luck(p)
    # Allow the last anchor to reach the top even on the compact profile.
    return max(end+12,max(w.guideAnchors.values())+w.viewHeight if w.guideAnchors else end)
