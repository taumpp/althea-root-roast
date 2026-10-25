import app

AUTOBAN_QUIZ_ANSWER = "ANSWER"
AUTOBAN_QUIZ_REFRESH = "REFRESH"
AUTOBAN_QUIZ_REST_TIME = "REST_TIME"

OPTION_SHADOW = "SHADOW"
OPTION_FPS_LIMIT = "FPS limit"
OPTION_FAMILY_NAME = "My family name"
OPTION_FAMILY_NAME_SHOW = "Show"
OPTION_FAMILY_NAME_HIDE = "Hide"
OPTION_SHOW_FPS = "Show FPS"
OPTION_VSYNC = "VSync"
OPTION_VSYNC_RESTART = "The VSync change will take effect after restarting the client."
OPTION_MSAA = "Anti-aliasing"
OPTION_MSAA_OFF = "Off"
OPTION_MSAA_RESTART = "The anti-aliasing change will take effect after restarting the client."
OPTION_FPS_COUNTER = "FPS: %d | %.1f ms"
COSTUME_INVENTORY_MODE_TITLE = "Costume equipment"
COSTUME_INVENTORY_MODE_INTEGRATED = "Inside inventory"
COSTUME_INVENTORY_MODE_SEPARATE = "Separate window"
SPECIAL_INVENTORY_CONSUMABLE = "Dew and elixirs"
OPTION_WORLD_GRAPHICS_CATEGORY = "World renderer"
OPTION_WORLD_GRAPHICS_PROFILE = "World renderer profile"
OPTION_WORLD_GRAPHICS_EFFECTIVE = "Renderer status"
OPTION_WORLD_GRAPHICS_STOCK = "Stock"
OPTION_WORLD_GRAPHICS_LOW = "Low"
OPTION_WORLD_GRAPHICS_HIGH = "High"
OPTION_WORLD_GRAPHICS_ULTRA = "Ultra"
OPTION_WORLD_GRAPHICS_STATUS = "Selected: %s | Active: %s"
OPTION_WORLD_GRAPHICS_STOCK_TOOLTIP = "Original renderer; maximum compatibility."
OPTION_WORLD_GRAPHICS_LOW_TOOLTIP = "Modern renderer with conservative GPU load."
OPTION_WORLD_GRAPHICS_HIGH_TOOLTIP = "Recommended modern rendering quality."
OPTION_WORLD_GRAPHICS_ULTRA_TOOLTIP = "Maximum quality with significantly higher GPU and VRAM load."
OPTION_WORLD_GRAPHICS_RECOMMENDED = "Recommended settings"
OPTION_WORLD_GRAPHICS_RECOMMENDED_TOOLTIP = "Selects a safe profile from the detected GPU capabilities."
OPTION_WORLD_GRAPHICS_CAPABILITIES = "AA: %s -> %s | INTZ: %s | GPU: %s"
OPTION_WORLD_ANTIALIAS = "Anti-aliasing"
OPTION_WORLD_ANTIALIAS_OFF = "Off"
OPTION_WORLD_ANTIALIAS_OFF_TOOLTIP = "Disables edge anti-aliasing."
OPTION_WORLD_ANTIALIAS_FXAA_TOOLTIP = "Fast post-process anti-aliasing for enhanced profiles; the interface stays sharp."
OPTION_WORLD_ANTIALIAS_MSAA_TOOLTIP = "2x MSAA resets the graphics device; depth-based god rays use a compatibility path."
OPTION_WORLD_ANTIALIAS_MSAA4_TOOLTIP = "4x MSAA resets the graphics device and falls back to 2x when unsupported."
OPTION_WORLD_STATUS_ON = "on"
OPTION_WORLD_STATUS_OFF = "off"
OPTION_WORLD_GRAPHICS_ULTRA_WARNING = "Ultra has significantly higher GPU and VRAM load."
OPTION_WORLD_GRAPHICS_ULTRA_WARNING_MEMORY = "Ultra has high GPU load | available ~%d MB"
OPTION_WORLD_GRAPHICS_REASON_DISABLED = "Stock renderer is active."
OPTION_WORLD_GRAPHICS_REASON_DEVICE = "Graphics device is not ready."
OPTION_WORLD_GRAPHICS_REASON_RENDERER = "Enhanced renderer resources are not ready."
OPTION_WORLD_GRAPHICS_REASON_SM3 = "Shader Model 3.0 is required."
OPTION_WORLD_GRAPHICS_REASON_LIMIT = "GPU shader instruction limit is too low."
OPTION_WORLD_GRAPHICS_REASON_REFLECTION = "Reflections were disabled by GPU compatibility."
OPTION_WORLD_GRAPHICS_REASON_DEPTH = "Required depth format is unsupported."
OPTION_WORLD_GRAPHICS_REASON_CLAMPED = "The active profile was reduced for this GPU."
OPTION_WORLD_GRAPHICS_REASON_SHADER_PACK = "Enhanced shader files are missing."
OPTION_WORLD_GRAPHICS_REASON_SHADER_INVALID = "Enhanced shader data is invalid."
OPTION_WORLD_GRAPHICS_REASON_SHADER_CREATE = "The GPU rejected an enhanced shader."
OPTION_WORLD_GRAPHICS_REASON_TARGET = "An enhanced render target could not be created."
OPTION_WORLD_GRAPHICS_REASON_RESET = "Enhanced graphics are recovering after a device reset."
OPTION_WORLD_GRAPHICS_REASON_LIGHT_TEXTURE = "This GPU does not support the point-light texture format."
OPTION_WORLD_GRAPHICS_REASON_LIGHT_RUNTIME = "Enhanced point lights are temporarily unavailable."
OPTION_WORLD_GRAPHICS_REASON_NEUTRAL_TEXTURE = "Enhanced fallback textures could not be created."
OPTION_WORLD_GRAPHICS_REASON_REFLECTION_CLIP = "This GPU cannot clip the reflection pass safely."
OPTION_WORLD_GRAPHICS_REASON_REFLECTION_PROFILE = "Real-time reflections require the Ultra profile."
OPTION_WORLD_GRAPHICS_REASON_GRASS_RUNTIME = "Enhanced grass is temporarily unavailable."
OPTION_WORLD_GRAPHICS_REASON_POSTPROCESS = "World post-processing is temporarily unavailable."
OPTION_WORLD_GRAPHICS_REASON_WEATHER_RUNTIME = "Enhanced rain is temporarily unavailable; classic rain is active."
OPTION_WORLD_RAIN = "Rain intensity"
OPTION_WORLD_RAIN_OFF = "Off"
OPTION_WORLD_RAIN_LOW = "Low"
OPTION_WORLD_RAIN_MEDIUM = "Medium"
OPTION_WORLD_RAIN_HIGH = "High"
OPTION_WORLD_RAIN_FX = "Rain effects"
OPTION_WORLD_RAIN_FX_CLASSIC = "Classic"
OPTION_WORLD_RAIN_FX_ENHANCED = "Enhanced"
OPTION_WORLD_RAIN_FX_TOOLTIP = "Adds surface-aware rain, splashes and distant rainfall."
OPTION_WORLD_RAIN_FX_EFFECTIVE_TOOLTIP = "Enhanced rain active: %s"
OPTION_WORLD_FEATURES = "Enhanced world features"
OPTION_WORLD_GRASS = "Grass"
OPTION_WORLD_GRASS_RADIUS = "Grass range"
OPTION_WORLD_GRASS_RADIUS_VALUE = "%.1fx (active %.1fx)"
OPTION_WORLD_GRASS_RADIUS_LIMITED_SUFFIX = " | limited by the active profile"
OPTION_WORLD_LIGHTS = "Point lights"
OPTION_WORLD_REFLECTIONS = "Reflections"
OPTION_WORLD_POSTPROCESS = "Post-processing"
OPTION_WORLD_GRASS_TOOLTIP = "Animated grass with wind and character interaction."
OPTION_WORLD_LIGHTS_TOOLTIP = "Dynamic light from nearby torches, lamps and effects."
OPTION_WORLD_REFLECTIONS_TOOLTIP = "Real-time reflections on water and wet surfaces."
OPTION_WORLD_POSTPROCESS_TOOLTIP = "World colour grade, god rays, underwater effects and sharpness; the interface stays untouched."
OPTION_WORLD_ON = "On"
OPTION_WORLD_OFF = "Off"

PET_ALBUM_CHRONICLE = "Chronicle of your encounters"
PET_ALBUM_CONTENTS = "Album contents"
PET_ALBUM_COUNT = "Seven groups - thirty-five creatures"
PET_ALBUM_OPEN_CHAPTER = "Open chapter"
PET_ALBUM_COLLECTION = "Your collection"
PET_ALBUM_BOND = "The complete album"
PET_ALBUM_PREPARING = "Album coming soon"
PET_ALBUM_CATALOG_ONLY = "Catalog preview only."
PET_ALBUM_NO_REWARDS = "Collection and bonuses are not active yet."
PET_ALBUM_CHAPTER = "Chapter %d"
PET_ALBUM_ENTRY = "Entry %d / 5"
PET_ALBUM_ACQUISITION = "ACQUISITION"
PET_ALBUM_GROWTH = "LEVELING"
PET_ALBUM_PLACEHOLDER = "To be specified."
PET_ALBUM_SEAL = "Seal"
PET_ALBUM_PET = "PET"
PET_ALBUM_FEED = "Feed"
PET_ALBUM_EVOLVE = "Evolve"
PET_ALBUM_REVIVE = "Revive"
PET_ALBUM_OPEN = "Open album"
PET_ALBUM_HP = "HP"
PET_ALBUM_DEF = "Defense"
PET_ALBUM_SP = "SP"
PET_ALBUM_JUMP_UNKNOWN = "Growth: -"
PET_ALBUM_JUMP = "Growth %s"
PET_ALBUM_EMPTY = "No active pet"
PET_ALBUM_LOCKED = "Locked"
PET_ALBUM_FREE = "Free"
PET_FEED_CRYSTAL_HINT = "Insert companion crystals for EXP"

QUICK_EQUIP_TITLE = 'Quick equipment'
QUICK_EQUIP_SETS = 'EQUIPMENT SETS'
QUICK_EQUIP_EQUIPMENT = 'EQUIPMENT'
QUICK_EQUIP_COSTUMES = 'COSTUMES'
QUICK_EQUIP_NEW_SET = '+ NEW SET'
QUICK_EQUIP_APPLY = 'SWITCH EQUIPMENT'
QUICK_EQUIP_DRAG_HINT = 'Drag items into the set slots.'
QUICK_EQUIP_SELECTED = 'Selected set'
QUICK_EQUIP_UNAVAILABLE = 'Sets are currently unavailable.'
QUICK_EQUIP_TRY_LATER = 'Try opening the window later.'

CODEPAGE = str(app.GetDefaultCodePage())

#CUBE_TITLE = "Cube Window"

def LoadLocaleFile(srcFileName, localeDict):
	localeDict["CUBE_INFO_TITLE"] = "Recipe"
	localeDict["CUBE_REQUIRE_MATERIAL"] = "Requirements"
	localeDict["CUBE_REQUIRE_MATERIAL_OR"] = "or"

	try:
		lines = open(srcFileName, "r").readlines()
	except IOError:
		import dbg
		dbg.LogBox("LoadUIScriptLocaleError(%(srcFileName)s)" % locals())
		app.Abort()

	for lineIndex, line in enumerate(lines, 1):
		localeLine = line.rstrip("\r\n")
		if not localeLine:
			continue

		tokens = localeLine.split("\t")

		if len(tokens) >= 2:
			localeDict[tokens[0]] = tokens[1]
		else:
			print(len(tokens), lineIndex, line)

if "locale/ymir" == app.GetLocalePath():
	LOCALE_UISCRIPT_PATH = "locale/ymir_ui/"

	WINDOWS_PATH = "d:/ymir work/ui/game/949_windows/"
	SELECT_PATH = "d:/ymir work/ui/intro/949_select/"
	GUILD_PATH = "d:/ymir work/ui/game/949_guild/"
	EMPIRE_PATH = "d:/ymir work/ui/intro/949_empire/"
	MAPNAME_PATH = "locale/ymir_ui/mapname/"
	LOGIN_PATH = "d:/ymir work/ui/intro/949_login/"

	JOBDESC_WARRIOR_PATH = "locale/ymir/desc_warrior.txt"
	JOBDESC_ASSASSIN_PATH = "locale/ymir/desc_assassin.txt"
	JOBDESC_SURA_PATH = "locale/ymir/desc_sura.txt"
	JOBDESC_SHAMAN_PATH = "locale/ymir/desc_shaman.txt"
	JOBDESC_WOLFMAN_PATH = "locale/ymir/desc_wolfman.txt"

	EMPIREDESC_A = "locale/ymir/desc_empire_a.txt"
	EMPIREDESC_B = "locale/ymir/desc_empire_b.txt"
	EMPIREDESC_C = "locale/ymir/desc_empire_c.txt"

	LOCALE_INTERFACE_FILE_NAME = "locale/ymir/locale_interface.txt"
	NEW_LOCALE_INTERFACE_FILE_NAME = "%s/new_locale_interface.txt" % (name)
else:
	if "HONGKONG" == app.GetLocaleServiceName():
		name = "locale/hongkong"
	elif "JAPAN" == app.GetLocaleServiceName():
		name = "locale/japan"
	elif "TAIWAN" == app.GetLocaleServiceName():
		name = "locale/taiwan"
	elif "NEWCIBN" == app.GetLocaleServiceName():
		name = "locale/newcibn"
	elif "EUROPE" == app.GetLocaleServiceName():
		name = app.GetLocalePath()
	else:
		name = "locale/ymir"

	LOCALE_UISCRIPT_PATH = "locale/common/ui/"
	LOGIN_PATH = "locale/common/ui/login/"
	EMPIRE_PATH = "%s/ui/empire/" % (name)
	GUILD_PATH = "locale/common/ui/guild/"
	SELECT_PATH = "%s/ui/select/" % (name)
	WINDOWS_PATH = "%s/ui/windows/" % (name)
	MAPNAME_PATH = "%s/ui/mapname/" % (name)

	JOBDESC_WARRIOR_PATH = "%s/jobdesc_warrior.txt" % (name)
	JOBDESC_ASSASSIN_PATH = "%s/jobdesc_assassin.txt" % (name)
	JOBDESC_SURA_PATH = "%s/jobdesc_sura.txt" % (name)
	JOBDESC_SHAMAN_PATH = "%s/jobdesc_shaman.txt" % (name)
	JOBDESC_WOLFMAN_PATH = "%s/jobdesc_wolfman.txt" % (name)

	EMPIREDESC_A = "%s/empiredesc_a.txt" % (name)
	EMPIREDESC_B = "%s/empiredesc_b.txt" % (name)
	EMPIREDESC_C = "%s/empiredesc_c.txt" % (name)

	LOCALE_INTERFACE_FILE_NAME = "%s/locale_interface.txt" % (name)
	NEW_LOCALE_INTERFACE_FILE_NAME = "%s/new_locale_interface.txt" % (name)

	if app.ENABLE_LOADING_TIP:
		LOADING_TIP_LIST = "locale/common/loading_tip_list.txt"
		LOADING_TIP_VNUM = "%s/loading_tip_vnum.txt" % (name)

	if app.ENABLE_MINI_GAME_OKEY:
		MINIGAME_RUMI_DESC = "%s/mini_game_okey_desc.txt" % (name)

	if app.ENABLE_MINI_GAME_CATCH_KING:
		MINIGAME_CATCH_KING_DESC = "%s/catchking_event_desc.txt" % (name)
		MINIGAME_CATCH_KING_SIMPLE_DESC = "%s/catchking_event_simple_desc.txt" % (name)
	if app.ENABLE_GROWTH_PET_SYSTEM:
		PET_PRIMIUM_FEEDSTUFF_DESC = "%s/pet_primium_feedstuff_desc.txt" % (name)
LoadLocaleFile(LOCALE_INTERFACE_FILE_NAME, locals())
LoadLocaleFile(NEW_LOCALE_INTERFACE_FILE_NAME, locals())

if app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz":
	SPECIAL_INVENTORY_CONSUMABLE = "Rosy"
	DROP_TRACKER_FILTERS = "Filtry"
	DROP_TRACKER_FILTERS_CLOSE = "Zavřít filtry"
	DROP_TRACKER_ICON_LIFETIME = "Ikony: %d s"
	DROP_TRACKER_ICON_LIFETIME_ALWAYS = "Ikony: vždy"
	DROP_TRACKER_KILLS = "Zabití"
	DROP_TRACKER_ITEMS = "Předměty"
	DROP_TRACKER_TOP_DROPS = "Nejčastější kořist"
	DROP_TRACKER_EMPTY = "V tomto filtru zatím není žádná kořist"
	DROP_TRACKER_TOP_SOURCES = "Hlavní zdroje"
	DROP_TRACKER_OPEN_DETAILS = "Detaily >"
	DROP_TRACKER_COMPACT_HINT = "Kliknutím na předmět zobrazíte zdroje"
	DROP_TRACKER_DETAIL_HINT = (
		"Levý klik rozbalí zdroje | Pravý klik skryje"
	)
	DROP_TRACKER_SESSION = "Relace %s"
	DROP_TRACKER_DETAIL_ITEMS_STATUS = "%s | %s zabití | %s předmětů"
	DROP_TRACKER_DETAIL_STATUS = (
		"%s | %s zabití | %s předmětů | %s Yang"
	)
	DROP_TRACKER_SOURCE_COUNT = "%d zdrojů"
	DROP_TRACKER_SOURCE_DETAIL = "Detail zdroje"
	DROP_TRACKER_SOURCE_META = "%s předmětů | %s zabití"
	DROP_TRACKER_OBTAINED = "Získáno: %s"
	OPTION_SHOW_FPS = "Zobrazit FPS"
	OPTION_VSYNC_RESTART = "Změna VSync se projeví po restartu hry."
	OPTION_MSAA = "Vyhlazování hran"
	OPTION_MSAA_OFF = "Vyp."
	OPTION_MSAA_RESTART = "Změna vyhlazování hran se projeví po restartu hry."
	OPTION_WORLD_GRAPHICS_CATEGORY = "Renderování světa"
	OPTION_WORLD_GRAPHICS_PROFILE = "Profil renderování světa"
	OPTION_WORLD_GRAPHICS_EFFECTIVE = "Stav rendereru"
	OPTION_WORLD_GRAPHICS_STOCK = "Původní"
	OPTION_WORLD_GRAPHICS_LOW = "Nízký"
	OPTION_WORLD_GRAPHICS_HIGH = "Vysoký"
	OPTION_WORLD_GRAPHICS_ULTRA = "Ultra"
	OPTION_WORLD_GRAPHICS_STATUS = "Zvoleno: %s | Aktivní: %s"
	OPTION_WORLD_GRAPHICS_STOCK_TOOLTIP = "Původní renderer s nejvyšší kompatibilitou."
	OPTION_WORLD_GRAPHICS_LOW_TOOLTIP = "Moderní renderer s úsporným zatížením grafické karty."
	OPTION_WORLD_GRAPHICS_HIGH_TOOLTIP = "Doporučená kvalita moderního renderování."
	OPTION_WORLD_GRAPHICS_ULTRA_TOOLTIP = "Maximální kvalita s výrazně vyššími nároky na GPU a VRAM."
	OPTION_WORLD_GRAPHICS_RECOMMENDED = "Doporučené nastavení"
	OPTION_WORLD_GRAPHICS_RECOMMENDED_TOOLTIP = "Zvolí vhodný profil podle zjištěných možností grafické karty."
	OPTION_WORLD_GRAPHICS_CAPABILITIES = "AA: %s -> %s | INTZ: %s | GPU: %s"
	OPTION_WORLD_ANTIALIAS = "Vyhlazování hran"
	OPTION_WORLD_ANTIALIAS_OFF = "Vyp."
	OPTION_WORLD_ANTIALIAS_OFF_TOOLTIP = "Vypne vyhlazování hran."
	OPTION_WORLD_ANTIALIAS_FXAA_TOOLTIP = "Rychlé vyhlazování vylepšených profilů. Herní rozhraní zůstane ostré."
	OPTION_WORLD_ANTIALIAS_MSAA_TOOLTIP = "Vyhlazování MSAA 2x vyžaduje obnovení grafického zařízení. Světelné paprsky se vykreslí v režimu kompatibility."
	OPTION_WORLD_ANTIALIAS_MSAA4_TOOLTIP = "MSAA 4x resetuje grafické zařízení a při nepodpoře přejde na 2x."
	OPTION_WORLD_STATUS_ON = "zap."
	OPTION_WORLD_STATUS_OFF = "vyp."
	OPTION_WORLD_GRAPHICS_ULTRA_WARNING = "Ultra má výrazně vyšší nároky na GPU a VRAM."
	OPTION_WORLD_GRAPHICS_ULTRA_WARNING_MEMORY = "Ultra: vysoká zátěž GPU | dostupné ~%d MB"
	OPTION_WORLD_GRAPHICS_REASON_DISABLED = "Je aktivní původní renderer."
	OPTION_WORLD_GRAPHICS_REASON_DEVICE = "Grafické zařízení zatím není připravené."
	OPTION_WORLD_GRAPHICS_REASON_RENDERER = "Prostředky nového rendereru zatím nejsou připravené."
	OPTION_WORLD_GRAPHICS_REASON_SM3 = "Je vyžadován Shader Model 3.0."
	OPTION_WORLD_GRAPHICS_REASON_LIMIT = "Limit instrukcí shaderu GPU je příliš nízký."
	OPTION_WORLD_GRAPHICS_REASON_REFLECTION = "Odrazy byly vypnuty kvůli kompatibilitě GPU."
	OPTION_WORLD_GRAPHICS_REASON_DEPTH = "Požadovaný formát depth bufferu není podporován."
	OPTION_WORLD_GRAPHICS_REASON_CLAMPED = "Aktivní profil byl pro tuto GPU snížen."
	OPTION_WORLD_GRAPHICS_REASON_SHADER_PACK = "Chybí soubory shaderů nového rendereru."
	OPTION_WORLD_GRAPHICS_REASON_SHADER_INVALID = "Data shaderů nového rendereru jsou neplatná."
	OPTION_WORLD_GRAPHICS_REASON_SHADER_CREATE = "Grafická karta odmítla vytvořit některý shader."
	OPTION_WORLD_GRAPHICS_REASON_TARGET = "Nepodařilo se připravit obraz pro vylepšenou grafiku."
	OPTION_WORLD_GRAPHICS_REASON_RESET = "Nová grafika se obnovuje po resetu zařízení."
	OPTION_WORLD_GRAPHICS_REASON_LIGHT_TEXTURE = "Grafická karta nepodporuje formát textury bodových světel."
	OPTION_WORLD_GRAPHICS_REASON_LIGHT_RUNTIME = "Bodová světla nového rendereru nejsou dočasně dostupná."
	OPTION_WORLD_GRAPHICS_REASON_NEUTRAL_TEXTURE = "Nepodařilo se vytvořit náhradní textury nového rendereru."
	OPTION_WORLD_GRAPHICS_REASON_REFLECTION_CLIP = "Grafická karta neumí oříznout průchod odrazů."
	OPTION_WORLD_GRAPHICS_REASON_REFLECTION_PROFILE = "Odrazy v reálném čase vyžadují profil Ultra."
	OPTION_WORLD_GRAPHICS_REASON_GRASS_RUNTIME = "Rozšířená tráva není dočasně dostupná."
	OPTION_WORLD_GRAPHICS_REASON_POSTPROCESS = "Postprocessing světa není dočasně dostupný."
	OPTION_WORLD_GRAPHICS_REASON_WEATHER_RUNTIME = "Vylepšený déšť teď není dostupný. Aktivní zůstává klasický déšť."
	OPTION_WORLD_RAIN = "Intenzita deště"
	OPTION_WORLD_RAIN_OFF = "Vyp."
	OPTION_WORLD_RAIN_LOW = "Nízká"
	OPTION_WORLD_RAIN_MEDIUM = "Střední"
	OPTION_WORLD_RAIN_HIGH = "Vysoká"
	OPTION_WORLD_RAIN_FX = "Efekty deště"
	OPTION_WORLD_RAIN_FX_CLASSIC = "Klasické"
	OPTION_WORLD_RAIN_FX_ENHANCED = "Vylepšené"
	OPTION_WORLD_RAIN_FX_TOOLTIP = "Přidá déšť reagující na povrch, cákance a vzdálenou dešťovou clonu."
	OPTION_WORLD_RAIN_FX_EFFECTIVE_TOOLTIP = "Vylepšený déšť aktivní: %s"
	OPTION_WORLD_FEATURES = "Rozšířené prvky světa"
	OPTION_WORLD_GRASS = "Tráva"
	OPTION_WORLD_GRASS_RADIUS = "Dosah trávy"
	OPTION_WORLD_GRASS_RADIUS_VALUE = "%.1fx (aktivní %.1fx)"
	OPTION_WORLD_GRASS_RADIUS_LIMITED_SUFFIX = " | omezeno aktivním profilem"
	OPTION_WORLD_LIGHTS = "Bodová světla"
	OPTION_WORLD_REFLECTIONS = "Odrazy"
	OPTION_WORLD_POSTPROCESS = "Postprocessing"
	OPTION_WORLD_GRASS_TOOLTIP = "Animovaná tráva reagující na vítr a pohyb postavy."
	OPTION_WORLD_LIGHTS_TOOLTIP = "Dynamické světlo blízkých pochodní, lamp a efektů."
	OPTION_WORLD_REFLECTIONS_TOOLTIP = "Odrazy vody a mokrých povrchů v reálném čase."
	OPTION_WORLD_POSTPROCESS_TOOLTIP = "Barevné ladění světa, světelné paprsky, podvodní efekt a ostrost bez změn rozhraní."
	OPTION_WORLD_ON = "Zap."
	OPTION_WORLD_OFF = "Vyp."
