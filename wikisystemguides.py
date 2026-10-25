# -*- coding: utf-8 -*-
"""Native system guides; every content value comes from the server catalogue."""
import bonuslabels
import uiToolTip
from wikilocale import BonusName
import item
import nonplayer
import ui
import wikiarticles as A
import wikicatalog as M
import uir1tokens as T
from wikiguides import data, number, yang, Page

SUPPORTED = ('aura', 'sash', 'resonance', 'biolog', 'afk', 'pet', 'rarity')
GRADES = uiToolTip.RARITY_GRADE_NAMES[1:]
ROMAN = ('I', 'II', 'III', 'IV', 'V', 'VI')


class Guide(Page):
    def __init__(self, w, title, subtitle, labels):
        Page.__init__(self, w)
        self.labels = labels
        self.index = 0
        self.title(title)
        y = self.para(subtitle, 0, 40, self.width, size=14, line=21)
        if labels:
            self.nav([(str(i), label) for i, label in enumerate(labels)], y+14)
        self.y = y+(60 if labels else 15)

    def chapter(self, title):
        self.y = self.section(str(self.index), title, self.y)
        self.index += 1

    def prose(self, text, color=T.INK_DIM):
        self.y = self.para(text, 0, self.y, self.width, color, 15, 22)+16

    def row(self, vnum, title, body, bonus=None):
        top = self.y
        self.icon(vnum, 8, top+7)
        self.text(title, 52, top+4, 16, T.IVORY, width=self.width-62)
        end = self.para(body, 52, top+29, self.width-62, size=14, line=21)
        if bonus:
            end = self.para(bonus, 52, end+5, self.width-62, A.GREEN, 14, 21)
        self.y = max(top+55, end+12)
        self.rect(0, self.y, self.width, 1, T.LINE)
        self.y += 15

    def note(self, text):
        lines = A.wrap(text, self.width-24, 'Noto Sans:14a')
        self.rect(0, self.y, self.width, len(lines)*21+20)
        self.y = self.para(text, 12, self.y+10, self.width-24, A.GOLD, 14, 21)+27

    def table(self, headers, rows, fractions=None, colors=None):
        fractions = fractions or [1.0/len(headers)]*len(headers)
        widths = [int(self.width*f) for f in fractions]
        widths[-1] = self.width-sum(widths[:-1])
        self.rect(0, self.y, self.width, 29)
        x = 0
        for header, width in zip(headers, widths):
            self.text(header, x+8, self.y+7, 14, T.IVORY, width=width-16)
            x += width
        self.y += 29
        for i, row in enumerate(rows):
            lines = [A.wrap(str(text), width-16, 'Noto Sans:14a') for text, width in zip(row, widths)]
            height = max(34, max([len(part) for part in lines] or [1])*20+14)
            if not i%2:
                self.rect(0, self.y, self.width, height, 0xff171413)
            x = 0
            for column, (part, width) in enumerate(zip(lines, widths)):
                for j, text in enumerate(part):
                    self.text(text, x+8, self.y+7+j*20, 14, (colors or {}).get(column, T.INK_DIM))
                x += width
            self.rect(0, self.y+height-1, self.width, 1, T.LINE)
            self.y += height
        self.y += 25

    def step(self, title, body):
        self.text(title, 0, self.y, 16, T.IVORY, width=self.width)
        self.y = self.para(body, 0, self.y+30, self.width, size=15, line=22)+24

    def recipe(self, recipe):
        vnum = M.number(recipe['vnum'])
        top = self.y
        self.rect(0, top, self.width, 64)
        self.icon(vnum, 10, top+8, M.number(recipe['count']))
        self.text(name(self.w, vnum), 56, top+7, 17, T.IVORY, width=self.width-66)
        npc = M.number(recipe['npc'])
        locations = {M.number(r.get('map')) for sources in self.w.receiver.catalog.ingredient_sources.values()
                     for r in sources if M.number(r.get('npc')) == npc}
        maker = 'Vyrobí: '+nonplayer.GetMonsterName(npc)
        if locations:
            maker += ' · '+', '.join(self.w.receiver.catalog.MapName(m) for m in sorted(locations, key=self.w.receiver.catalog.MapKey))
        if M.number(recipe.get('level')):
            maker += ' · úroveň '+str(recipe['level'])+'+'
        end = self.para(maker, 56, top+34, self.width-66, size=14, line=20)
        self.y = max(top+74, end+10)
        self.rect(0, self.y, self.width, 26)
        self.text('Potřebné materiály', 8, self.y+5)
        self.text('Počet', self.width-12, self.y+5, align='right')
        self.y += 26
        materials = M.rows(recipe.get('materials'))
        columns = 2 if len(materials) > 4 else 1
        cell = self.width//columns
        for start in range(0, len(materials), columns):
            top = self.y
            ends = []
            for j, material in enumerate(materials[start:start+columns]):
                x = j*cell; v = M.number(material['vnum']); count = M.number(material['count'])
                self.icon(v, x+8, top+7, count)
                ends.append(self.para(name(self.w, v), x+54, top+13, cell-105, size=14, line=20))
                self.text(str(count)+'×', x+cell-12, top+13, color=T.IVORY, align='right')
            self.y = max(top+47, max(ends)+12)
            self.rect(0, self.y, self.width, 1, T.LINE); self.y += 1
        self.y += 10
        self.text('Cena: '+yang(recipe.get('gold'))+' Yang', 8, self.y, 15, A.GOLD)
        self.text('Šance: '+number(recipe.get('chance'), ' %'), self.width-12, self.y, 15, A.GREEN, 'right')
        self.y += 45


def craft_recipes(w, subtype):
    catalog = w.receiver.catalog
    recipes = [r for v, alternatives in catalog.recipe_index.items()
               if v in catalog.available and M.number(catalog.items[v].get('type')) == item.ITEM_TYPE_COSTUME
               and M.number(catalog.items[v].get('subtype')) == subtype for r in alternatives]
    return sorted(recipes, key=lambda r: (M.number(r.get('level')), catalog.ItemKey(M.number(r['vnum'])), M.number(r.get('npc')), M.number(r.get('index'))))


def crafting_intro(c, subtype):
    c.chapter('01   Vyrob základní předmět')
    recipes = craft_recipes(c.w, subtype)
    if not recipes:
        c.prose('V aktuálním katalogu není dostupný recept pro výrobu.')
    for recipe in recipes:
        c.recipe(recipe)
    return recipes


def name(w, vnum):
    return w.receiver.catalog.names.get(M.number(vnum), '')


def available(w, rows):
    return [r for r in M.rows(rows) if M.number(r.get('vnum')) in w.receiver.catalog.available]


def proto_items(w, kind, subtype=None):
    return sorted([v for v, p in w.receiver.catalog.items.items()
                   if v in w.receiver.catalog.available and M.number(p.get('type')) == kind
                   and (subtype is None or M.number(p.get('subtype')) == subtype)],
                  key=w.receiver.catalog.ItemKey)


def example(w, kind, subtype=None):
    values = proto_items(w, kind, subtype)
    return values[0] if values else 0


def apply(w, kind, value):
    return w.ApplyText(M.number(kind), M.number(value))


def aura(w, values):
    c = Guide(w, 'Aura', 'Výroba u Theowahdana v Hlavním městě.', ['Výroba', 'Rozvoj', 'Absorpce'])
    crafting_intro(c, getattr(item, 'COSTUME_TYPE_AURA', -1))
    vnum = example(w, item.ITEM_TYPE_COSTUME, getattr(item, 'COSTUME_TYPE_AURA', -1))
    c.chapter('02   Nasaď auru a začni lovit')
    if vnum:
        c.row(vnum, name(w, vnum), 'Auru vybav ve slotu kostýmů. Úroveň, absorpci a růst sleduj v jejím tooltipu.')
    c.prose('Body získáváš s nasazenou aurou. Po naplnění potřebného počtu bodů se automaticky posune na další stupeň.')
    c.note('Nepotřebuješ staré krmení runami ani ruční povýšení.')
    c.rect(0,c.y,c.width,26);c.text('Za který lov získáš body',8,c.y+4,18,T.IVORY,font='Althea Caps:18a');c.y+=40
    c.table(['Poražený cíl', 'Body'], [['Meteor', '+'+str(values['meteor'])], ['Boss', '+'+str(values['boss'])], ['Finální boss dungeonu', '+'+str(values['final_boss'])]], [.72, .28], {1:A.GREEN})
    c.prose('Cíl smí být nejvýše o '+str(values['deficit'])+' úrovní níž než tvoje postava. Obyčejné příšery růst neposouvají.')
    c.text('Stupně aury',0,c.y,18,T.IVORY,font='Althea Caps:18a');c.y+=34
    c.table(['Stupeň', 'Absorpce', 'Body'], [[str(r['grade']), str(r['absorption'])+' %', str(r['points'])] for r in M.rows(values['grades'])], [.25,.3,.45], {1:A.GREEN})
    c.chapter('03   Absorpce bonusů')
    c.prose('Otevři Absorpci a zvol vhodnou výbavu. V náhledu zkontroluj přenášené bonusy; vložený předmět se spotřebuje. Vyšší stupeň zesílí již absorbované bonusy.')
    return c


def sash(w, values):
    c = Guide(w, 'Šerpy', 'Výroba u Theowahdana v Hlavním městě.', ['Výroba','Rozvoj','Absorpce'])
    crafting_intro(c, getattr(item, 'COSTUME_TYPE_ACCE', -1))
    vnum = example(w, item.ITEM_TYPE_COSTUME, getattr(item, 'COSTUME_TYPE_ACCE', -1))
    c.chapter('02   Od výroby ke spojování')
    c.row(vnum, 'Promluv s Theowahdanem', 'Vyber Kombinování a potvrď Ano. V prvním slotu je hlavní šerpa; do druhého vlož šerpu stejného stupně.')
    c.note('Výsledek zachová vzhled a absorbované bonusy hlavní šerpy. Absorpce druhé se nepřičítá.')
    c.text('Stupně a cena jednoho pokusu',0,c.y,18,T.IVORY,font='Althea Caps:18a');c.y+=34
    c.table(['Stupeň','Yang','Základní šance'], [[str(r['grade']),yang(r['gold']),str(r['chance'])+' %'] for r in M.rows(values['grades'])], [.3,.35,.35], {1:A.GOLD,2:A.GREEN})
    c.prose('Při přechodu na čtvrtý stupeň získáš '+str(values['first_fourth_min'])+'–'+str(values['first_fourth_max'])+' % absorpce. Konečnou šanci může změnit aktivní talent; ověř ji v kombinování.')
    c.text('Jak se dostat na '+str(values['maximum'])+' %',0,c.y,18,T.IVORY,font='Althea Caps:18a');c.y+=34
    c.prose('Čtvrtý stupeň spojuj s další šerpou čtvrtého stupně. V prvním slotu nech tu, jejíž vzhled a bonusy chceš zachovat.')
    maximum = M.number(values['maximum'])
    c.table(['Hlavní šerpa','Úspěšný výsledek'], [[str(maximum-1)+' %',str(maximum)+' %']], [.5,.5], {1:A.GREEN})
    if M.truth(values.get('fixed_increment')):
        c.prose('Úspěšný pokus zvýší absorpci o jeden procentní bod, nejvýše do uvedeného maxima.')
    else:
        c.prose('Úspěšný pokus zvýší absorpci náhodně až o '+str(values['increment_range'])+' procentních bodů, nejvýše do uvedeného maxima.')
    c.note('Při neúspěchu hlavní šerpa zůstane, druhá se spotřebuje. Yang platíš i za neúspěšný pokus.')
    c.chapter('03   Absorbuj bonusy zbraně')
    c.step('Theowahdan · Absorpce bonusů', 'Vlož šerpu a vhodnou zbraň. Výsledek si přečti v náhledu; zbraň se při potvrzení spotřebuje.')
    c.prose('Při dalším spojování hlavní šerpy již absorbovaná zbraň zůstává zachovaná.')
    return c


def resonance(w, values):
    c = Guide(w, 'Rezonantní pečetě', 'Odemkni sloty v helmě, štítu nebo botách a přidej pečetě.', ['Výbava','Odemčení','Pečetě','Spojování'])
    c.chapter('01   Kam pečetě vložit')
    c.prose('Rezonantní sloty patří konkrétní helmě, štítu nebo botám. Přetáhni klíč na vhodný předmět; pečeť vlož do odemčeného prázdného slotu.')
    c.chapter('02   Odemkni sloty postupně')
    c.row(values['key'],name(w,values['key']), 'Začni prvním slotem a pokračuj v pořadí.')
    c.table(['Slot','Klíče','Yang'], [[r['slot'],r['count'],yang(r['gold'])] for r in M.rows(values['keys'])], [.25,.3,.45], {2:A.GOLD})
    c.chapter('03   Druhy a dostupné stupně')
    for family in M.rows(values['families']):
        vnum=M.number(family['vnum']);ranks=M.rows(family['ranks'])
        if vnum not in w.receiver.catalog.available:continue
        c.row(vnum,name(w,vnum), 'Stupně '+ROMAN[0]+'–'+ROMAN[len(ranks)-1]+': '+', '.join(str(r['value']) for r in ranks), 'Limit účinku '+str(family['cap'])+' %')
    c.note('V jednom předmětu může být nejvýše jedna pečeť každého druhu. Vyjmutá pečeť se vrátí do inventáře, pokud máš místo. Rarita výbavy zesiluje její účinek do limitu.')
    c.chapter('04   Spojování u Theowahdana')
    c.step('Theowahdan · Hlavní město', 'Vyber Kombinování, stejně jako u šerp. Vlož dvě pečetě stejného stupně; druh výsledku určuje první slot.')
    transitions=M.rows(values['transitions'])
    c.table(['Spojení','Šance','Yang'], [[ROMAN[M.number(r['from'])-1]+' + '+ROMAN[M.number(r['from'])-1]+' na '+ROMAN[M.number(r['to'])-1],str(r['chance'])+' %',yang(r['gold'])] for r in transitions], [.5,.25,.25], {1:A.GREEN,2:A.GOLD})
    maximum=max([M.number(r['to']) for r in transitions] or [1])
    c.note(ROMAN[maximum-1]+' je aktuální maximum spojování. Úspěch spotřebuje obě pečetě; při neúspěchu zůstane první a spotřebuje se druhá.')
    return c


def biolog(w, values):
    c = Guide(w, 'Biolog', 'Trvalé bonusy za dokončené výzkumy.', [])
    rows = sorted(M.rows(values.get('researches')), key=lambda r:(M.number(r['level']),M.number(r['vnum'])))
    helpers = sorted({M.number(r.get(field)) for r in rows for field in ('elixir','clock') if M.number(r.get(field))})
    if helpers:
        top = c.y; label_width = 90; cell = (c.width-label_width)//len(helpers)
        ends = []
        height = max([49]+[len(A.wrap(name(w,v),cell-45,'Noto Sans:13a'))*19+23 for v in helpers])
        c.rect(0,top,c.width,height)
        c.text('Lze použít:',8,top+16,13)
        for i, vnum in enumerate(helpers):
            x = label_width+i*cell
            c.icon(vnum,x,top+8)
            ends.append(c.para(name(w,vnum),x+40,top+13,cell-45,T.IVORY,13,19))
        c.y = top+height+18
    c.chapter('Trvalé odměny podle výzkumu')
    for row in rows:
        top = c.y; middle = int(c.width*.43)+20
        c.text(str(row['level'])+'+',8,top+12,15,A.GOLD)
        c.icon(row['vnum'],64,top+6)
        item_end = c.para(name(w,row['vnum']),108,top+11,middle-112,T.IVORY,14,20)
        bonuses = ' · '.join(apply(w,b['type'],b['value']) for b in M.rows(row['bonuses']))
        end = c.para(bonuses,middle,top+9,c.width-middle-8,A.GREEN,14,21)
        c.y = max(top+57,item_end+14,end+14)
        c.rect(0,c.y,c.width,1,T.LINE);c.y+=16
    c.prose('Odměnu vyzvedni po dokončení výzkumu v okně Biologa.')
    return c


def afk(w, values):
    c=Guide(w,'AFK režim','Odpočívej v bezpečné oblasti a získávej body účtu.',['Začátek','Body','Odměny','Limit'])
    c.chapter('01   Aktivuj AFK v bezpečné oblasti')
    c.prose('Otevři AFK nabídku v hlavním městě. Pokud jsi mimo určenou bezpečnou oblast, použij nabídnutý přesun.')
    c.note('Nejdřív proběhne kvalifikace '+number(M.number(values['qualification'])/60,' minut')+'. Pohyb, boj a používání předmětů klidovou sérii přeruší.')
    c.chapter('02   Body za nepřerušenou sérii')
    c.table(['Průběh','Body za hodinu'], [['Prvních '+str(values['early_hours'])+' hodin',values['early_points']],['Další hodiny série',values['later_points']]], [.7,.3], {1:A.GREEN})
    c.prose('Průběh a další připsání sleduj v AFK okně. Body jsou společné pro účet.')
    c.chapter('03   Nabídka za AFK body')
    for row in M.rows(values['offers']):
        c.row(row['vnum'],name(w,row['vnum']),str(row['price'])+' bodů · '+number(M.number(row['lifetime'])/86400,' dní'))
    c.prose('Odměny pořídíš přes AFK nabídku v Item Shopu. Nelze je obchodovat; čas začíná skutečným doručením do inventáře.')
    c.chapter('04   Týdenní limit a více účtů')
    c.table(['Pravidlo','Co znamená'], [[str(values['weekly_cap'])+' bodů týdně','Limit nově získaných bodů; utrácení jej nezvyšuje.'],['Pondělí 00:00','Reset týdenního zisku podle českého času. Zůstatek nezmizí.'],['Jeden účet na zařízení','Současně vydělává jeden účet. Hraní na dalším účtu stejného zařízení sérii přeruší.']], [.4,.6])
    return c


def pet(w, values):
    c=Guide(w,'Růst a vývoj mazlíčka','Vylíhni, přivolej a rozvíjej svého klasického mazlíčka.',['Začátek','Bonusy a růst','Krmení','Evoluce','Dovednosti'])
    species=available(w,values['species']);eggs=[r for r in species if M.number(r['subtype'])==item.PET_EGG]
    c.chapter('01   Od vejce k mazlíčkovi')
    if eggs:c.row(eggs[0]['vnum'],name(w,eggs[0]['vnum']),'Použij vejce a pojmenuj mazlíčka. Přivolej ho jeho pečetí a otevři okno mazlíčka.')
    c.prose('Maximální úroveň je '+str(values['maximum_level'])+'; nesmí překročit úroveň tvé postavy. Životnost a otevřené sloty kontroluj v okně peta.')
    c.chapter('02   Co získáš při vylíhnutí')
    hp_name=BonusName(item.APPLY_MAX_HP_PCT);defense_name=BonusName(item.APPLY_DEF_GRADE_BONUS)
    c.prose('Náhodně se určí počáteční bonusy, útočné zaměření a počet slotů podle druhu. Bonusy každého peta: '+hp_name+', '+defense_name+' a jeden útočný bonus.')
    c.table(['Zaměření','Útočný bonus'], [['Lov příšer',BonusName(item.APPLY_ATTBONUS_MONSTER)],['Souboje s hráči',BonusName(item.APPLY_ATTBONUS_HUMAN)]], [.5,.5], {1:A.GREEN})
    c.prose('Počáteční hodnoty: '+number(M.number(values['initial_min'])/10)+'–'+number(M.number(values['initial_max'])/10)+' %. Každý bonus se při svém skoku losuje samostatně podle kvality peta. Sloty se losují nezávisle na kvalitě růstu.')
    total_weight = M.number(values.get('quality_total_weight', 0))
    for quality in values.get('qualities', []):
        chance = 100.0 * M.number(quality['weight']) / total_weight if total_weight else 0
        c.prose('Kvalita '+number(M.number(quality['quality']))+': +'+number(M.number(quality['minimum'])/10)+' až +'+number(M.number(quality['maximum'])/10)+' procentního bodu pro HP, útok i obranu. Šance při líhnutí a přerolování: '+number(chance)+' %.')
    c.table(['Bonus','Růst'], [[hp_name,'Každých '+str(values['hp_interval'])+' úrovní'],['Útočný bonus','Každých '+str(values['attack_interval'])+' úrovní'],[defense_name,'Každých '+str(values['defense_interval'])+' úrovní']], [.4,.6], {1:A.GREEN})
    maximum=M.number(values['maximum_level']);interval=M.number(values['attack_interval'])
    cap=(M.number(values['initial_max'])+(maximum//interval)*M.number(values['growth_max']))/10.0
    c.note('Teoretické maximum útočného bonusu na úrovni '+str(maximum)+': '+number(cap,' %')+'. Započítává se celá zobrazená hodnota včetně desetin. Vyžaduje maximální počáteční hodnotu a každý skok; nejde o běžný výsledek.')
    c.prose('Počet slotů se losuje od jednoho do maxima druhu. Každý počet má stejnou šanci; u druhu s menším maximem další sloty získat nemůžeš.')
    c.table(['Druh vejce','Maximum slotů','Šance na maximum'],[[name(w,r['vnum']),r['slots'],number(100.0/M.number(r['slots']),' %')] for r in eggs if M.number(r['slots'])>0],[.5,.2,.3],{2:A.GREEN})
    c.chapter('03   Krystaly přidávají EXP, tyčinka životnost')
    for crystal in available(w,data(w,'mount').get('crystals')):
        c.row(crystal['vnum'],name(w,crystal['vnum']),str(crystal['experience'])+' EXP · vlož do okna Nakrmit.')
    for row in species:
        if M.number(row['subtype'])==item.PET_FEEDSTUFF:c.row(row['vnum'],name(w,row['vnum']),'Doplňuje životnost mazlíčka.')
    c.note('Zkušenosti a životnost jsou různé hodnoty. Krystaly a proteinovou tyčinku nezaměňuj.')
    c.chapter('04   Při zastavení růstu zkontroluj evoluci')
    for row in M.rows(values['evolutions']):c.row(row['vnum'],'Od úrovně '+str(row['level']),name(w,row['vnum'])+' · '+str(row['count'])+' ks')
    c.prose('Otevři Evoluce a připrav požadovanou knihu. Na hranici vývojového stupně musíš nejdřív dokončit evoluci.')
    c.chapter('05   Knihy a otevřené sloty')
    c.prose('Dovednosti mohou mít úroveň až '+str(values['maximum_skill_level'])+'. Po poslední evoluci můžeš učit dovednosti. Stejná dovednost může být v jednom petovi jen jednou. Kapacitu druhu a skutečně otevřené sloty ověř v okně peta nebo tooltipu přepravní bedny.')
    c.note('Pet album má samostatného průvodce. Klasický pet zde roste vlastními zkušenostmi a evolucemi.')
    return c


def rarity(w, values):
    c=Guide(w,'Rarity','Povyš výbavu, vyber bonusy a srovnej raritu celé sestavy.',['Stupně','Povýšení','Bonusy','Přetáčení','Sestava'])
    grades=M.rows(values['grades'])
    c.chapter('01   Stupně a počet bonusů')
    for row in grades:c.row(row['essence'],GRADES[M.number(row['grade'])-1],str(row['slots'])+' otevřené bonusy')
    c.chapter('02   Povýšení má vlastní recept')
    c.row(values['application'],name(w,values['application']),'Sundej výbavu a otevři povýšení. Zkontroluj výsledek, materiály i konečnou šanci.')
    c.table(['Cílový stupeň','Šance','Yang'], [[GRADES[M.number(r['grade'])-1],number(M.number(r['chance_bp'])/100,' %'),yang(r['gold'])] for r in grades], [.46,.28,.26], {1:A.GOLD,2:A.GOLD})
    for row in grades:
        c.text(GRADES[M.number(row['grade'])-1],0,c.y,16,T.IVORY);c.y+=29
        c.row(values['dust'],name(w,values['dust']),str(row['dust'])+' ks')
        for cost in M.rows(row['materials']):c.row(cost['vnum'],name(w,cost['vnum']),str(cost['count'])+' ks')
    c.row(values['booster'],name(w,values['booster']),'Zvyšuje šanci o '+number(M.number(values['booster_bp'])/100,' procentního bodu')+'. Konečný přepočet zkontroluj v náhledu.')
    c.chapter('03   Možné bonusy rarity')
    c.prose('Tabulka ukazuje možné alternativy a hodnotu jednoho bonusu pro každý stupeň. Předmět nezíská všechny řádky současně.')
    headers=['Bonus']+[ROMAN[M.number(r['grade'])-1] for r in grades]
    for row in grades:
        c.text(ROMAN[M.number(row['grade'])-1]+' · '+GRADES[M.number(row['grade'])-1],0,c.y,13);c.y+=23
    c.y+=15
    rows=[]
    for bonus in M.rows(values['bonuses']):
        description=bonuslabels.Describe(w.ApplyText,M.number(bonus['type']))
        if not description:continue
        label,unit=description
        rows.append([label]+['+'+str(v['value'])+(' '+unit if unit else '') for v in M.rows(bonus['values'])])
    c.table(headers,rows,[.4]+[.6/max(1,len(grades))]*len(grades),{i:A.GREEN for i in range(1,len(headers))})
    c.note('Nové přetočení již nenabízí bonus „'+BonusName(item.APPLY_ATTBONUS_MONSTER)+'“. Starší předměty jej mohou mít.')
    c.prose('Celkový příspěvek rarity k bezvědomí a zpomalení je omezen na +'+str(values['control_cap'])+' procentních bodů pro každý efekt. Ostatní zdroje mají vlastní příspěvek.')
    c.chapter('04   Přetáčet můžeš vše nebo jeden slot')
    c.row(values['reroll'],name(w,values['reroll']),'Přetáčí všechny otevřené bonusy rarity najednou.')
    c.row(values['targeted_reroll'],name(w,values['targeted_reroll']),'Přetáčí zvolený bonus; ostatní zůstanou zachované. Může znovu padnout stejný druh.')
    c.chapter('05   Vyvážená rarita výbavy')
    c.prose('Počítá se zbraň, brnění, helma, štít, náramek, boty, náhrdelník, náušnice a rukavice. Výsledný stupeň určuje nejnižší rarita těchto předmětů. Chybějící kus nebo kus bez rarity bonus vypne.')
    c.table(['Nejnižší rarita sestavy',BonusName(item.APPLY_MELEE_MAGIC_ATTBONUS_PER)],[[GRADES[M.number(r['grade'])-1],'+'+str(r['balanced_attack'])+' %'] for r in grades],[.57,.43],{1:A.GREEN})
    c.prose('Kostýmy, aura a talismany do této sestavy nepatří. Aktuální přínos sleduj v přehledu bonusů postavy.')
    return c


def draw(w, guide):
    values=data(w, {'sash':'sash','resonance':'resonance'}.get(guide,guide))
    if not values:
        c=Guide(w,'Načítání průvodce','Aktuální hodnoty se zobrazí po přijetí údajů ze serveru.',['Začátek','Postup','Bonusy','Podrobnosti'])
        for title in c.labels:
            c.chapter(title)
            c.prose('Čekám na aktuální údaje ze hry.')
    else:
        c=globals()[guide](w,values)
    return max(c.y+12,max(w.guideAnchors.values())+w.viewHeight if w.guideAnchors else c.y)
