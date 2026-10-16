"""Approved A7: compact live settings and a separate full queue editor."""
from settingslocale import Text as T

PAGES = {
    'game': (0, 0, T('Hraní', 'Gameplay'), ''),
    'pickup': (0, 1, T('Sběr předmětů', 'Item pickup'), ''),
    'keys': (0, 2, T('Klávesové zkratky', 'Keybindings'), ''),
    'queue': (0, 3, T('Fronta kamenů', 'Stone queue'), ''),
    'interface': (0, 4, T('Rozhraní', 'Interface'), ''),
    'notifications': (0, 5, T('Upozornění', 'Notifications'), ''),
    'image': (1, 0, T('Obraz a kamera', 'Image and camera'), ''),
    'effects': (1, 1, T('Stíny a efekty', 'Shadows and effects'), ''),
    'world': (1, 2, T('Renderování světa', 'World rendering'), ''),
    'sound': (2, 0, T('Hlasitost a hudba', 'Volume and music'), ''),
}
NAV = tuple(PAGES)
# Existing external links remain valid without creating hidden subpages.
ALIASES = dict(details=('image', None), colors=('image', 'color_preset'),
    shadows=('effects', 'shadow_target'), camera=('image', 'fov'),
    sky=('world', 'sky'), names=('interface', 'names'),
    loot=('interface', 'loot_messages'))
HEIGHTS = dict(game=432, pickup=432, keys=456, queue=456, interface=1324,
    notifications=432, image=456, effects=456, world=432, sound=456)

QUALITY = tuple(enumerate((T('Původní', 'Original'), T('Nízká', 'Low'), T('Vysoká', 'High'), T('Ultra', 'Ultra'), T('Vlastní', 'Custom'))))
COLORS = ((1, T('Althea', 'Althea')), (0, T('Původní', 'Original')),
          (2, T('Živější', 'Vivid')), (3, T('Atmosférický', 'Atmospheric')), (4, T('Vlastní', 'Custom')))
CUSTOM_COLORS = (('contrast',T('Kontrast','Contrast')), ('saturation',T('Sytost barev','Saturation')),
    ('temperature',T('Teplota barev','Color temperature')), ('shadows',T('Prosvětlení stínů','Shadow brightness')),
    ('glow',T('Jemná záře','Soft glow')))
SKIES = tuple(T(cz, en) for cz, en in (('Podle mapy','Map default'), ('Noc','Night'), ('Oblačno','Cloudy'),
    ('Jasno','Clear'), ('Soumrak','Twilight'), ('Slunce','Sun'), ('Rozbřesk','Dawn'), ('Opar','Haze'),
    ('Červánky','Red sky'), ('Západ','Sunset'), ('Zlatavá','Golden'), ('Měsíc','Moon')))


def options(*labels):
    return tuple(enumerate(labels))

def compose(v, page):
    if page == 'image':
        v.section(T('Plynulost', 'Smoothness'), 0)
        v.frame_limit(34)
        v.refresh_rate(72)
        v.check('vsync', T('Synchronizace s monitorem', 'Vertical sync'), 0, 115, width=348,
                hint=T('Projeví se po restartu hry.', 'Takes effect after restarting the game.'))
        v.check('show_fps', T('Zobrazovat počet FPS', 'Show FPS'), 0, 143, width=348)
        v.section(T('Kamera', 'Camera'), 180)
        v.slider('fov', T('Zorné pole (FOV)', 'Field of view (FOV)'), 217, compact=True)
        v.radios('camera', T('Maximální oddálení', 'Maximum camera distance'), 245,
                 options(T('Blízko', 'Near'), T('Daleko', 'Far')), gap=25)
        v.section(T('Barvy a světlo', 'Colors and light'), 307)
        v.radios('color_preset', '', 342, COLORS, columns=3, gap=0)
        v.slider('exposure', T('Jas obrazu', 'Brightness'), 405, compact=True)
        v.slider('sharpness', T('Doostření', 'Sharpening'), 431, compact=True)
        v.custom_colors()
    elif page == 'game':
        v.section(T('Souboje hráčů', 'Player combat'), 0)
        v.radios('pvp', T('Režim boje', 'Combat mode'), 39,
                 ((0,T('Mír','Peace')),(1,T('Pomsta','Revenge')),(4,T('Cech','Guild')),(2,T('Volný','Free'))))
        v.section(T('Blokovat požadavky', 'Block requests'), 125)
        blocks=((1,T('Obchod','Trade')),(8,T('Soukromé zprávy','Private messages')),(2,T('Pozvání do skupiny','Party invites')),
                (32,T('Žádosti o vstup','Join requests')),(4,T('Pozvání do cechu','Guild invites')),
                (16,T('Přátelství','Friend requests')),(64,T('Prohlížení vybavení','Equipment inspection')))
        for index,(mask,label) in enumerate(blocks):
            v.check('block', label, (index % 2) * 174, 172 + (index // 2) * 40, mask=mask)
    elif page == 'pickup':
        v.radios('pickup_mode',T('Způsob sběru','Pickup mode'),4,((2,T('Jednotlivě','Single item')),(1,T('Vše v dosahu','All nearby'))))
        v.section(T('Nesbírat vybavení pro','Exclude equipment for'),79)
        for index,(job,label) in enumerate(((0,T('Válečníka','Warrior')),(3,T('Ninju','Ninja')),(1,T('Suru','Sura')),(2,T('Šamana','Shaman')))):
            v.check('pickup_class_%d'%job,label,0+(index%2)*175,117+(index//2)*33)
        v.section(T('Rozmezí úrovně vybavení','Equipment level range'),183)
        v.number('pickup_min',T('Od','From'),0,221)
        v.number('pickup_max',T('Do','To'),175,221)
        v.section(T('Nesbírat tyto druhy vybavení','Exclude equipment types'),266)
        rows=(('weapon',0,T('Meče','Swords')),('weapon',2,T('Dýky','Daggers')),('weapon',1,T('Obouruční','Two-handed')),
              ('weapon',4,T('Luky','Bows')),('weapon',5,T('Zvony','Bells')),('weapon',6,T('Vějíře','Fans')),
              ('armor',0,T('Brnění','Armor')),('armor',1,T('Helmy','Helmets')),('armor',2,T('Štíty','Shields')),
              ('armor',4,T('Náramky','Bracelets')),('armor',6,T('Náhrdelníky','Necklaces')),('armor',3,T('Náušnice','Earrings')),
              ('armor',5,T('Boty','Shoes')),('weapon',3,T('Šípy','Arrows')))
        for index,(group,number,label) in enumerate(rows):
            v.check('pickup_%s_%d'%(group,number),label,0+(index%3)*116,301+(index//3)*26,width=112)
    elif page == 'keys':
        v.keybindings()
    elif page == 'queue':
        v.queue_inline()
    elif page == 'interface':
        v.section(T('Chat a text', 'Chat and text'), 0)
        v.radios('font', T('Velikost písma', 'Font size'), 36, options(T('Běžné','Normal'),T('Větší','Larger')))
        v.hint(T('Změna velikosti písma se projeví po restartu.', 'Font size changes require a restart.'), 104)
        v.check('chat', T('Chat při hraní','Chat while playing'), 0, 140, width=348)
        v.hint(T('Zprávy i bez otevření chatu klávesou Enter.', 'Messages remain visible without opening chat.'), 164)
        v.section(T('Úkoly a účinky','Quests and affects'), 202)
        v.check('quests', T('Tlačítka úkolů','Quest buttons'), 0, 244, width=348)
        v.check('affects', T('Ikony aktivních účinků','Active affect icons'), 0, 281, width=348)
        v.section(T('Jména postav','Character names'), 329)
        for key, label, y in (('names', T('Jména stále viditelná','Always show names'),369),
                             ('family_names', T('Zobrazovat moje rodinn\u00e9 jm\u00e9no ostatn\u00edm','Show my family name to others'),407),
                             ('npc_names', T('Jména NPC','NPC names'),445),
                             ('outline', T('Obrys textu','Text outline'),483)):
            v.check(key, label, 0, y, width=348)
        v.section(T('Informace o nestvůrách','Monster information'), 526)
        v.check('mob_level', T('Úroveň','Level'), 0, 566)
        v.check('mob_aggressive', T('Agresivita','Aggression'), 174, 566)
        v.section(T('Poškození','Damage'), 616)
        v.check('damage', T('Zobrazovat čísla zásahů','Show damage numbers'), 0, 657, width=348)
        v.slider('damage_size', T('Velikost čísel','Number size'), 701, compact=True)
        v.section(T('Kořist a inventář','Loot and inventory'), 769)
        v.radios('loot_messages', T('Zprávy o získané kořisti','Loot messages'), 806,
                 options(T('Okénko','Window'),T('Chat','Chat'),T('Vypnuto','Off')))
        v.radios('loot_lifetime', T('Doba zobrazení kořisti','Loot display duration'), 888,
                 ((3, '3 s'), (5, '5 s'), (7, '7 s'), (10, '10 s'), (15, '15 s'),
                  (0, T('Trvale','Always'))), columns=3)
        v.check('yang', T('Zobrazovat získaný Yang','Show collected Yang'), 0, 978, width=348)
        v.radios('loot_placement', T('Umístění přehledu kořisti','Loot tracker placement'), 1032,
                 options(T('Spodní lišta','Taskbar'),T('Volně na ploše','Free floating')))
        v.action('edit_loot', T('Upravit polohu','Edit placement'), 1125, v.edit_loot, left=True)
        v.action('reset_loot', T('Obnovit polohu','Reset placement'), 1162, v.reset_loot, left=True)
        v.hint(T('Úprava polohy přepne do tažení okénka ve hře.', 'Placement editing lets you drag the tracker in game.'), 1200)
        v.radios('costumes', T('Inventář kostýmů','Costume inventory'), 1242,
                 options(T('S inventářem','With inventory'),T('Samostatně','Separate')))
    elif page == 'effects':
        v.section(T('Kdo vrhá stín', 'Who casts shadows'), 0)
        v.radios('shadow_target', '', 38, options(T('Nikdo','Nobody'),T('Jen prostředí','Environment only'),
                 T('Prostředí a moje postava','Environment and my character'),
                 T('Prostředí a všechny postavy','Environment and all characters')), vertical=True, gap=0, pitch=27)
        v.radios('shadow_quality', T('Kvalita stínů','Shadow quality'), 158,
                 options(T('Nízká','Low'),T('Střední','Medium'),T('Vysoká','High')), gap=25)
        v.section(T('Záře kouzel','Spell glows'), 216)
        v.check('skills', T('Aury a záře zbraní','Auras and weapon glows'), 0, 252, width=348,
                hint=T('Trvalé efekty vybraných schopností, například Aura meče.','Persistent effects of selected skills, such as Aura of the Sword.'))
        v.check('buffs', T('Záře šamanských buffů','Shaman buff glows'), 0, 281, width=348)
        v.radios('special_effects', T('Záblesky při lektvarech a zásazích','Potion and hit flashes'), 310,
                 options(T('U všech','Everyone'),T('Jen u mě','Only me'),T('Vypnuto','Off')), gap=25)
        v.section(T('Doprovody','Companions'), 373)
        v.check('pet', T('Mazlíčci','Pets'), 0, 406)
        v.check('mount', T('Jezdecká zvířata','Mounts'), 174, 406)
        v.check('support', T('Podpůrný šaman','Support shaman'), 0, 433)
    elif page == 'world':
        v.section(T('Kvalita světa','World quality'), 0)
        v.radios('quality_preset', '', 37, QUALITY, columns=3, gap=0)
        v.action('recommended', T('Doporučit','Recommend'), 64, v.recommended, left=True, x=244, family='88x21')
        v.radios('aa', T('Vyhlazování hran','Antialiasing'), 99, options(T('Vyp.','Off'),'FXAA','2×','4×'), gap=25)
        v.section(T('Počasí a prvky světa','Weather and world features'), 164)
        v.radios('rain', T('Počasí','Weather'), 200,
                 options(T('Jasno','Clear'),T('Slabý déšť','Light rain'),T('Déšť','Rain'),T('Silný déšť','Heavy rain')), gap=25)
        v.check('rain_fx', T('Vylepšený déšť','Enhanced rain'), 0, 261)
        v.check('fog', T('Mlha v krajině','Landscape fog'), 174, 261)
        v.check('grass', T('Tráva','Grass'), 0, 291)
        v.slider('grass_radius', T('Dosah trávy','Grass distance'), 325, compact=True)
        v.check('lights', T('Bodová světla','Point lights'), 0, 350)
        v.check('reflections', T('Odrazy','Reflections'), 174, 350)
        v.check('postprocess', T('Obrazové efekty světa','World image effects'), 0, 378, width=348)
        v.sky_picker(403)
    elif page == 'notifications':
        v.section(T('Způsob upozornění','Notification delivery'), 0)
        v.text(T('Odpočty','Timers'), 222, 48, small=True, center=True)
        v.text(T('Zpráva','Message'), 311, 48, small=True, center=True)
        for index,(key,label,hint) in enumerate((('biolog',T('Biolog','Biologist'),T('Další odevzdání','Next submission')),
                  ('dungeon',T('Dungeony','Dungeons'),T('Další vstup','Next entry')),
                  ('switchbot','Switchbot',T('Výsledek přepínání','Switching result')))):
            y=88+index*76
            v.tint(0,y-2,352,65,index)
            v.text(label,10,y+7,bold=True)
            v.text(hint,10,y+32,small=True)
            if key!='switchbot':
                v.check(key+'_hud','',215,y+20,width=22)
            else:
                v.text('—',222,y+18,center=True)
            v.check(key+'_messages','',304,y+20,width=22)
        v.hint(T('Biolog a dungeony: jen položky s budíkem.','Biologist and dungeons: enabled alarms only.'),339)
        v.hint(T('Bez budíků se odpočtové okno nezobrazí.','Without alarms, the timer window stays hidden.'),365)
    elif page == 'sound':
        v.section(T('Hlasitost','Volume'), 0)
        v.slider('sound', T('Zvukové efekty','Sound effects'), 47, compact=True)
        v.slider('music', T('Hudba','Music'), 97, compact=True)
        v.section(T('Hudební doprovod','Background music'), 162)
        v.music_inline(177)
