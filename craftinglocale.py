"""Short crafting captions; locale packs may override each CRAFT_* symbol."""
import localeInfo

DEFAULTS = {
    'TITLE': u'V\u00fdroba',
    'ALL': u'V\u0161e',
    'SEARCH': u'Hledat recept...',
    'MATERIALS': u'Suroviny',
    'USE_ANY': u'Pou\u017e\u00edt libovoln\u00e9',
    'COUNTS': u'M\u00e1\u0161 / pot\u0159eba',
    'SELECTED_COUNTS': u'Vlo\u017eeno / pot\u0159eba',
    'OUTPUT': u'V\u00fdsledek: %d ks',
    'OUTPUT_UPTO': u'V\u00fdsledek: a\u017e %d ks',
    'CHANCE': u'\u0160ance',
    'QUANTITY': u'Po\u010det',
    'MAKE': u'Vyrobit %dx',
    'WAIT': u'\u010cek\u00e1n\u00ed...',
    'RECIPES': u'Recepty: %d',
    'NO_RECIPES': u'\u017d\u00e1dn\u00e9 dostupn\u00e9 recepty',
    'OLD_LOW': u'Star\u00e9 kameny +0 a\u017e +3',
    'OLD_FOUR': u'Star\u00e9 kameny +4',
    'NO_SPACE': u'Chyb\u00ed m\u00edsto nebo Yang.',
    'MISSING': u'Chyb\u00ed suroviny.',
    'CHANGED': u'Vybran\u00fd p\u0159edm\u011bt se zm\u011bnil.',
    'LIST_CHANGED': u'Seznam recept\u016f se zm\u011bnil. Vyber recept znovu.',
    'ARMOR_BODY': u'Brn\u011bn\u00ed',
    'ARMOR_HEAD': u'Helmy',
    'ARMOR_SHIELD': u'\u0160t\u00edty',
    'ARMOR_WRIST': u'N\u00e1ramky',
    'ARMOR_FOOTS': u'Obuv',
    'ARMOR_NECK': u'N\u00e1hrdeln\u00edky',
    'ARMOR_EAR': u'N\u00e1u\u0161nice',
    'ARMOR_GLOVE': u'Rukavice',
    'ARMOR_PENDANT': u'Talismany',
    'COSTUMES': u'Kost\u00fdmy',
}

def Text(key):
    return getattr(localeInfo, 'CRAFT_'+key, DEFAULTS[key])
