CONTROL_ROOT = "d:/ymir work/ui/public/crimson/controls/unified/"
STATES = ("normal", "hover", "pressed", "selected", "disabled")
FAMILY_SIZES = {
	"26x24": (26, 24),
	"32x16": (32, 16),
	"32x19": (32, 19),
	"38x19": (38, 19),
	"43x21": (43, 21),
	"49x20": (49, 20),
	"50x18": (50, 18),
	"52x19": (52, 19),
	"53x39": (53, 39),
	"56x19": (56, 19),
	"57x30": (57, 30),
	"60x20": (60, 20),
	"61x21": (61, 21),
	"72x24": (72, 24),
	"78x21": (78, 21),
	"80x24": (80, 24),
	"83x24": (83, 24),
	"85x24": (85, 24),
	"88x21": (88, 21),
	"92x24": (92, 24),
	"94x29": (94, 29),
	"100x21": (100, 21),
	"137x31": (137, 31),
	"148x23": (148, 23),
	"170x24": (170, 24),
	"176x21": (176, 21),
	"180x25": (180, 25),
	"199x27": (199, 27),
	"199x38": (199, 38),
	"255x18": (255, 18),
	"275x18": (275, 18),
	"306x18": (306, 18),
}
ALIAS_GROUPS = {
	"43x21": ("small_button_01.sub", "small_button_02.sub", "small_button_03.sub"),
	"61x21": (
		"middle_button_01.sub", "middle_button_02.sub", "middle_button_03.sub",
		"m_button01.tga", "m_button02.tga", "m_button03.tga",
	),
	"88x21": ("large_button_01.sub", "large_button_02.sub", "large_button_03.sub"),
	"180x25": ("xlarge_button_01.sub", "xlarge_button_02.sub", "xlarge_button_03.sub"),
	"57x30": ("xlarge_thin_button_01.sub", "xlarge_thin_button_02.sub", "xlarge_thin_button_03.sub"),
	"38x19": ("xsmall_button_01.sub", "xsmall_button_02.sub", "xsmall_button_03.sub"),
	"53x39": ("big_button_01.sub", "big_button_02.sub", "big_button_03.sub"),
	"60x20": ("small_thin_button_01.sub", "small_thin_button_02.sub", "small_thin_button_03.sub"),
	"100x21": ("largeb_button_01.tga", "largeb_button_02.tga", "largeb_button_03.tga"),
	"176x21": ("long_button_01.sub", "long_button_02.sub", "long_button_03.sub"),
	"32x16": (
		"private_pagenumber_00.sub", "private_pagenumber_01.sub", "private_pagenumber_02.sub",
		"page_pagenumber_00.sub", "page_pagenumber_01.sub", "page_pagenumber_02.sub",
	),
	"32x19": ("tab_button_small_01.sub", "tab_button_small_02.sub", "tab_button_small_03.sub"),
	"52x19": ("tab_button_middle_01.sub", "tab_button_middle_02.sub", "tab_button_middle_03.sub"),
	"78x21": ("tab_button_large_01.sub", "tab_button_large_02.sub", "tab_button_large_03.sub"),
	"137x31": ("action_button_0.tga", "action_button_1.tga", "action_button_2.tga"),
	"199x27": ("category_0.tga", "category_1.tga", "category_2.tga"),
	"199x38": tuple(
		"%s_title_%d.tga" % (edge, state)
		for edge in ("first", "middle", "end")
		for state in range(3)
	),
}
PRIVATE_PATH_GROUPS = {
	"49x20": (
		"d:/ymir work/ui/switchbot/btn_small_01.sub",
		"d:/ymir work/ui/switchbot/btn_small_02.sub",
		"d:/ymir work/ui/switchbot/btn_small_03.sub",
	),
	"148x23": (
		"d:/ymir work/ui/switchbot/btn_big_01.sub",
		"d:/ymir work/ui/switchbot/btn_big_02.sub",
		"d:/ymir work/ui/switchbot/btn_big_03.sub",
	),
	"78x21": (
		"d:/ymir work/ui/dragonsoul/button_01.tga",
		"d:/ymir work/ui/dragonsoul/button_02.tga",
		"d:/ymir work/ui/dragonsoul/button_03.tga",
	),
	"88x21": (
		"d:/ymir work/ui/dragonsoul/l_button01.tga",
		"d:/ymir work/ui/dragonsoul/l_button02.tga",
		"d:/ymir work/ui/dragonsoul/l_button03.tga",
	),
	"61x21": (
		"d:/ymir work/ui/dragonsoul/m_button01.tga",
		"d:/ymir work/ui/dragonsoul/m_button02.tga",
		"d:/ymir work/ui/dragonsoul/m_button03.tga",
	),
	"50x18": (
		"d:/ymir work/ui/dragonsoul/s_button01.tga",
		"d:/ymir work/ui/dragonsoul/s_button02.tga",
		"d:/ymir work/ui/dragonsoul/s_button03.tga",
	),
	"56x19": (
		"d:/ymir work/ui/game/bravery_cape/btn_start_0.png",
		"d:/ymir work/ui/game/bravery_cape/btn_start_1.png",
		"d:/ymir work/ui/game/bravery_cape/btn_start_2.png",
		"d:/ymir work/ui/game/bravery_cape/btn_stop_0.png",
		"d:/ymir work/ui/game/bravery_cape/btn_stop_1.png",
		"d:/ymir work/ui/game/bravery_cape/btn_stop_2.png",
	),
	"83x24": (
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_m_0.png",
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_m_1.png",
	),
	"85x24": (
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_l_0.png",
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_l_1.png",
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_r_0.png",
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_r_1.png",
	),
	"94x29": (
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_0.png",
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_1.png",
		"d:/ymir work/ui/game/battle_pass_reworked/slice/quest/btn_2.png",
	),
	"255x18": (
		"d:/ymir work/ui/game/cube/cube_menu_tab3_default.sub",
		"d:/ymir work/ui/game/cube/cube_menu_tab3_select.sub",
	),
	"275x18": (
		"d:/ymir work/ui/game/cube/cube_menu_tab2.sub",
	),
	"306x18": (
		"d:/ymir work/ui/game/cube/cube_menu_tab1.sub",
	),
}
GAME_CONTROLS_ENABLED = False
GAME_SETTINGS_NAVIGATION_VISUALS = set(
	"d:/ymir work/ui/game/crimson_ember/gameoption/%s" % basename
	for basename in (
		"category_0.tga", "category_1.tga", "category_2.tga",
		"first_title_0.tga", "first_title_1.tga", "first_title_2.tga",
		"middle_title_0.tga", "middle_title_1.tga", "middle_title_2.tga",
		"end_title_0.tga", "end_title_1.tga", "end_title_2.tga",
	)
)

try:
	_STRING_TYPES = (basestring,)
except NameError:
	_STRING_TYPES = (str,)


def _NormalizePath(filename):
	if not isinstance(filename, _STRING_TYPES):
		return ""
	return filename.replace("\\", "/").lower()


def _Basename(filename):
	return _NormalizePath(filename).rsplit("/", 1)[-1]


def _BuildAliasMap():
	aliases = {}
	for family, names in ALIAS_GROUPS.items():
		for name in names:
			if name in aliases:
				raise ValueError("duplicate crimson control alias: %s" % name)
			aliases[name] = family
	return aliases


def _BuildPrivatePathMap():
	paths = {}
	for family, names in PRIVATE_PATH_GROUPS.items():
		for name in names:
			normalized = _NormalizePath(name)
			if normalized in paths:
				raise ValueError("duplicate crimson private path: %s" % name)
			paths[normalized] = family
	return paths


ALIAS_TO_FAMILY = _BuildAliasMap()
PRIVATE_PATH_TO_FAMILY = _BuildPrivatePathMap()


def Visual(family, state):
	if family not in FAMILY_SIZES or state not in STATES:
		raise ValueError("unsupported crimson control")
	return CONTROL_ROOT + "button_%s_%s.png" % (family, state)


def IsUnifiedVisual(filename):
	return isinstance(filename, _STRING_TYPES) and filename.replace("\\", "/").lower().startswith(CONTROL_ROOT)


def _UnifiedFamily(filename):
	basename = _Basename(filename)
	if not basename.startswith("button_") or not basename.endswith(".png"):
		return None
	stem = basename[len("button_"):-len(".png")]
	for state in STATES:
		suffix = "_" + state
		if stem.endswith(suffix):
			family = stem[:-len(suffix)]
			return family if family in FAMILY_SIZES else None
	return None


def SetGameControlsEnabled(enabled):
	global GAME_CONTROLS_ENABLED
	GAME_CONTROLS_ENABLED = bool(enabled)


def ResolveVisual(filename, state):
	if state not in STATES:
		raise ValueError("unsupported crimson control state")
	if not GAME_CONTROLS_ENABLED:
		return filename
	if IsUnifiedVisual(filename):
		family = _UnifiedFamily(filename)
		return Visual(family, state) if family and state == "selected" else filename
	if _NormalizePath(filename) in GAME_SETTINGS_NAVIGATION_VISUALS:
		return filename
	modalFamily = PRIVATE_PATH_TO_FAMILY.get(_NormalizePath(filename))
	if not modalFamily:
		modalFamily = ALIAS_TO_FAMILY.get(_Basename(filename))
	return Visual(modalFamily, state) if modalFamily else filename


def ApplyVisuals(button, family):
	button.SetUpVisual(Visual(family, "normal"))
	button.SetOverVisual(Visual(family, "hover"))
	button.SetDownVisual(Visual(family, "pressed"))
	button.SetDisableVisual(Visual(family, "disabled"))
