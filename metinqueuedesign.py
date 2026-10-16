# Native composition V5. The first fourteen fields retain their V4 identity.
import systemSetting
import WikiRenderTarget


VERSION = 5
FIELD_NAMES = (
	"preset", "primaryRgb", "brightness", "focus", "size", "tempo",
	"clearance", "accentRgb", "accentEnabled", "glow", "ringWidth",
	"sparks", "pulse", "ringStyle", "colorMode", "colorStrength",
	"markerScale", "ringEnabled", "bodyEnabled", "artRevision",
)
PRESET, PRIMARY, BRIGHTNESS, FOCUS, SIZE, TEMPO = range(6)
CLEARANCE, ACCENT, ACCENT_ENABLED, GLOW, RING_WIDTH, SPARKS, PULSE = range(6, 13)
RING_STYLE, COLOR_MODE, COLOR_STRENGTH, MARKER_SCALE = range(13, 17)
RING_ENABLED, BODY_ENABLED, ART_REVISION = range(17, 20)
RANGES = {
	BRIGHTNESS: (25, 240), FOCUS: (0, 2), SIZE: (85, 125), TEMPO: (60, 140),
	CLEARANCE: (15, 70), GLOW: (0, 200), RING_WIDTH: (50, 180),
	SPARKS: (0, 200), PULSE: (0, 3), COLOR_MODE: (0, 2),
	COLOR_STRENGTH: (0, 100), MARKER_SCALE: (100, 240), ART_REVISION: (0, 1),
}
STEPS = {BRIGHTNESS: 5, SIZE: 5, TEMPO: 5, CLEARANCE: 5, GLOW: 10,
	RING_WIDTH: 5, SPARKS: 10, COLOR_STRENGTH: 5, MARKER_SCALE: 10}
# Owner selection, 2026-09-06-orb-depth-6; body numbers are never renumbered.
CATALOG = (
	(5, "orbit", u"Astrální dráhy", u"Světelné dráhy obíhají kámen v prostoru."),
	(6, "crystals", u"Krystalový roj", u"Krystaly obíhají a levitují kolem kamene."),
	(7, "moons", u"Měsíční srpky", u"Dvojice srpků obíhá boky kamene."),
	(9, "lotus", u"Karmínový lotos", u"Světelné lístky vyrůstají kolem paty kamene."),
	(10, "phoenix", u"Fénixova křídla", u"Dvě křídla a jiskry po stranách kamene."),
	(12, "embers", u"Žhavé uhlíky", u"Uhlíky stoupají kolem kamene."),
	(14, "blades", u"Tančící čepele", u"Úzké světelné čepele obíhají kámen."),
	(15, "veil", u"Živý závoj", u"Pohyblivé stuhy obklopují kámen."),
	(19, "beacon", u"Světelná koule", u"Světelné jádro a proudy energie uvnitř kulatého povrchu."),
	(20, "orbs", u"Tři oběžnice", u"Tři koule s vlastními proudy světla obíhají nad vrcholem."),
	(21, "arrow", u"Šipka cíle", u"Plastická šipka míří na vybraný kámen."),
	(24, "native_corona", u"Koróna · Althea", u"Autorské prostorové oblouky Althea."),
	(25, "native_resonance", u"Rezonance · Althea", u"Autorské Althea stuhy a pomalé pulzování."),
	(26, "native_serpent", u"Hadí spirála · Althea", u"Dva hadi s animovanými hlavami a hřbetními ploutvemi."),
	(28, "current_pulse", u"Pulzující obal", u"Pohyblivý částicový obal kolem kamene."),
	(30, "talismans", u"Runové talismany", u"Čtyři vyřezávané talismany s třásněmi obíhají kámen."),
	(34, "spiral_pair", u"Dvojitá šroubovice", u"Dvě úzké protilehlé stuhy opisují klidnou šroubovici."),
	(35, "falling_stars", u"Hvězdný déšť", u"Malé čtyřcípé hvězdy klesají podél boků kamene."),
	(40, "comet_pair", u"Dvě komety", u"Dvě komety za sebou nechávají krátkou zužující se stopu."),
	(48, "double_chevron", u"Dvojitá značka", u"Dvě klidné úzké šipky označují vrchol kamene."),
	(49, "three_sparks", u"Tři světla", u"Tři světla drží nad kamenem trojúhelníkové uspořádání."),
)
BY_NUMBER = dict((entry[0], entry) for entry in CATALOG)
RING_STYLE_CHOICES = (
	(1, u"Klasický vír"), (2, u"Segmenty"), (3, u"Malovaná pečeť"),
	(4, u"Propletené dráhy"), (6, u"Lotos"), (7, u"Přerušené oblouky"),
	(9, u"Světelný běžec"), (12, u"Jemný vír"), (16, u"Prstencový kompas"),
	(19, u"Dvojitý prstenec"), (20, u"Rezonance"), (21, u"Prstenec jisker"),
	(22, u"Původní · Krystaly"), (23, u"Původní · Lotos"),
	(24, u"Původní · Uhlíky"), (25, u"Původní · Závoj"),
	(26, u"Původní · Závoj Althea"), (27, u"Původní · Koróna"),
	(28, u"Původní · Rezonance"),
)
RING_NAMES = dict(RING_STYLE_CHOICES)
ORIGINAL_RING_STYLES = {6: 22, 9: 23, 12: 24, 15: 25, 22: 26, 24: 27, 25: 28}
SPARK_PRESETS = (10, 12, 24, 25, 26, 35, 40, 49)
OVERHEAD_PRESETS = (19, 20, 21, 48, 49)
PREVIOUS_ART_PRESETS = (5, 6, 12, 14, 15, 21, 24, 25, 26, 28)
FOCUS_CHOICES = ((0, u"Všechny stejně"), (1, u"Ostatní tlumené"), (2, u"Pouze první"))
PULSE_CHOICES = ((0, u"Podle efektu"), (1, u"Vypnuto"), (2, u"Jemné"), (3, u"Výrazné"))
ART_REVISION_CHOICES = ((1, u"Nová kresba"), (0, u"Předchozí kresba"))
MODEL_VNUMS = (8001, 8005, 8013)

# Every tuple is the owner's per-effect appearance. Export ring 0 becomes the
# independent original-ring ID; rejected comet ring 13 falls back to kept ring 1.
PROFILE_DEFAULTS = {
	5: (5, 0xFF405F, 240, 0, 100, 100, 30, 0xFFD28D, 0, 200, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
	6: (6, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 22, 2, 100, 160, 1, 1, 1),
	7: (7, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
	9: (9, 0xFF405F, 175, 0, 100, 100, 30, 0xFFD28D, 0, 130, 130, 100, 0, 23, 2, 100, 160, 1, 1, 1),
	10: (10, 0xFF405F, 180, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 21, 2, 100, 160, 1, 1, 1),
	12: (12, 0xFF405F, 190, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 24, 2, 30, 160, 1, 1, 1),
	14: (14, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
	15: (15, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 25, 2, 100, 160, 1, 1, 1),
	19: (19, 0xFF405F, 130, 0, 90, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
	20: (20, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
	21: (21, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
	24: (24, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 27, 2, 100, 160, 1, 1, 1),
	25: (25, 0xFF405F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 28, 2, 100, 160, 1, 1, 1),
	26: (26, 0xFF405F, 130, 0, 110, 105, 30, 0xFFD28D, 0, 100, 100, 100, 0, 2, 2, 100, 160, 1, 1, 1),
	28: (28, 0xAD3DFF, 130, 0, 100, 100, 30, 0xFFD28D, 0, 200, 50, 100, 0, 6, 2, 100, 160, 1, 1, 1),
	30: (30, 0xE5B95F, 130, 0, 100, 100, 30, 0xFFD28D, 0, 100, 100, 100, 0, 2, 2, 100, 160, 1, 1, 1),
	34: (34, 0xE5B95F, 130, 0, 100, 100, 30, 0xDCC9A8, 0, 100, 180, 100, 0, 16, 2, 100, 160, 1, 1, 1),
	35: (35, 0x9EBDFF, 130, 0, 100, 100, 30, 0xDCC9A8, 0, 100, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
	40: (40, 0xFFBD70, 240, 0, 100, 100, 30, 0xDCC9A8, 0, 100, 100, 100, 0, 1, 2, 100, 160, 1, 1, 1),
	48: (48, 0xFF405F, 130, 0, 100, 100, 30, 0xDCC9A8, 0, 100, 100, 100, 0, 1, 2, 100, 160, 1, 1, 1),
	49: (49, 0x54E88D, 130, 0, 100, 100, 30, 0xDCC9A8, 0, 100, 100, 100, 0, 1, 2, 100, 160, 0, 1, 1),
}
DEFAULT = PROFILE_DEFAULTS[28]


def HasV5():
	try:
		return (systemSetting.GetMetinQueueDesignVersion() >= VERSION
			and WikiRenderTarget.GetMetinQueueDesignVersion() >= VERSION
			and all(hasattr(systemSetting, name) for name in (
				"GetMetinQueueDesignV5", "GetDefaultMetinQueueDesignV5",
				"GetMetinQueueDesignProfilesV5", "SetMetinQueueDesignV5"))
			and all(hasattr(WikiRenderTarget, name) for name in (
				"SelectMetinQueueDesignPreviewV5", "SetMetinQueueDesignPreviewV5")))
	except (AttributeError, TypeError, RuntimeError):
		return False


def HasV3():
	# Existing option/viewer entrypoints ask this legacy name. The expanded
	# editor must never send a truncated V5 draft to an older native bridge.
	return HasV5()


def _SystemCall(name, values=None):
	if not HasV5():
		raise RuntimeError("Metin queue design requires both native V5 bridges")
	method = getattr(systemSetting, name + "V5")
	return method() if values is None else method(*Normalize(values))


def SelectPreview(index, vnum, values):
	return WikiRenderTarget.SelectMetinQueueDesignPreviewV5(index, vnum, *Normalize(values))


def UpdatePreview(index, values):
	return WikiRenderTarget.SetMetinQueueDesignPreviewV5(index, *Normalize(values))


def Defaults(preset=28):
	return PROFILE_DEFAULTS.get(preset, DEFAULT)


def Quantize(field, value):
	minimum, maximum = RANGES[field]
	value = max(minimum, min(maximum, int(value)))
	step = STEPS.get(field, 1)
	return min(maximum, minimum + ((value - minimum + step // 2) // step) * step)


def Normalize(values):
	try:
		result = [int(value) for value in values]
		if len(result) not in (13, 14, len(DEFAULT)) or result[PRESET] not in BY_NUMBER:
			return DEFAULT
		result.extend(Defaults(result[PRESET])[len(result):])
		for index in (PRIMARY, ACCENT):
			result[index] &= 0xFFFFFF
		for index in (ACCENT_ENABLED, RING_ENABLED, BODY_ENABLED):
			result[index] = 1 if result[index] else 0
		for index in RANGES:
			result[index] = Quantize(index, result[index])
		# Keep the wire slot for saved V5 profiles, but make detail preservation
		# automatic. The old untinted mode remains available through strength 0.
		if result[COLOR_MODE] == 0:
			result[COLOR_STRENGTH] = 0
		result[COLOR_MODE] = 2
		if result[RING_STYLE] == 0:
			result[RING_STYLE] = ORIGINAL_RING_STYLES.get(result[PRESET], 1)
		if result[RING_STYLE] not in RING_NAMES:
			result[RING_STYLE] = 1
		if result[PRESET] not in PREVIOUS_ART_PRESETS:
			result[ART_REVISION] = 1
		return tuple(result)
	except (TypeError, ValueError, OverflowError):
		return DEFAULT


def Supports(preset, field, values=None):
	if preset not in BY_NUMBER:
		return False
	if field is None:
		return True
	if field == COLOR_MODE:
		return False
	if field == ART_REVISION:
		return preset in PREVIOUS_ART_PRESETS
	if field in (CLEARANCE, MARKER_SCALE):
		return (preset in OVERHEAD_PRESETS and (values is None or values[BODY_ENABLED])
			and (field != MARKER_SCALE or values is None or values[ART_REVISION]))
	if field == SPARKS:
		return ((preset in SPARK_PRESETS and (values is None or values[BODY_ENABLED]))
			or (values is not None and values[RING_ENABLED] and values[RING_STYLE] == 21))
	if values is not None:
		if field == RING_WIDTH:
			return bool(values[RING_ENABLED])
	return True


def _NormalizeProfiles(profiles, active):
	if set(profiles) != set(BY_NUMBER) or active not in BY_NUMBER:
		raise ValueError("A complete selected profile collection is required")
	result = []
	for preset, _, _, _ in CATALOG:
		values = profiles[preset]
		if len(values) != len(DEFAULT) or values[PRESET] != preset:
			raise ValueError("Profile identity or field count is invalid")
		normalized = Normalize(values)
		if normalized[PRESET] != preset:
			raise ValueError("Profile values are invalid")
		result.append(normalized)
	return tuple(result)


class GameBackend(object):
	version = VERSION
	offline = False
	Normalize = staticmethod(Normalize)
	Defaults = staticmethod(Defaults)

	def Read(self):
		return Normalize(_SystemCall("GetMetinQueueDesign"))

	def Profiles(self):
		profiles = dict(PROFILE_DEFAULTS)
		for values in _SystemCall("GetMetinQueueDesignProfiles"):
			# A removed historical profile must not overwrite the active default.
			if values and values[PRESET] in BY_NUMBER:
				values = Normalize(values)
				profiles[values[PRESET]] = values
		return profiles

	def ReadNearby(self):
		return 1 if systemSetting.GetMetinQueueNearbyFillEnabled() else 0

	def CanResetAll(self):
		return HasV5() and hasattr(systemSetting, "SetMetinQueueDesignProfilesV5")

	def ApplyProfiles(self, profiles, active, nearby):
		values = _NormalizeProfiles(profiles, active)
		if not self.CanResetAll():
			raise RuntimeError("Complete profile submission requires the updated client")
		committed = Normalize(systemSetting.SetMetinQueueDesignProfilesV5(values, active))
		nearby = systemSetting.SetMetinQueueNearbyFillEnabled(1 if nearby else 0)
		return committed, 1 if nearby else 0

	def Apply(self, values, nearby):
		values = Normalize(_SystemCall("SetMetinQueueDesign", Normalize(values)))
		nearby = systemSetting.SetMetinQueueNearbyFillEnabled(1 if nearby else 0)
		return values, 1 if nearby else 0


class OfflineBackend(GameBackend):
	"""Native preview with in-memory profiles; no player config or file writes."""
	offline = True

	def __init__(self):
		self.active = DEFAULT
		self.profiles = dict(PROFILE_DEFAULTS)
		self.nearby = 1

	def Read(self):
		return self.active

	def Profiles(self):
		return dict(self.profiles)

	def ReadNearby(self):
		return self.nearby

	def CanResetAll(self):
		return True

	def ApplyProfiles(self, profiles, active, nearby):
		values = _NormalizeProfiles(profiles, active)
		self.profiles = dict((row[PRESET], row) for row in values)
		self.active = self.profiles[active]
		self.nearby = 1 if nearby else 0
		return self.active, self.nearby

	def Apply(self, values, nearby):
		self.active = Normalize(values)
		self.profiles[self.active[PRESET]] = self.active
		self.nearby = 1 if nearby else 0
		return self.active, self.nearby


def AdaptBackend(backend=None):
	if backend is not None and getattr(backend, "version", 0) >= VERSION:
		return backend
	if backend is not None and getattr(backend, "offline", False):
		return OfflineBackend()
	return GameBackend()
