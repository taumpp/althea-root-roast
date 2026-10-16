# Shared appearance contract. This module does not create a game/network phase.
import systemSetting
import WikiRenderTarget


DEFAULT_V1 = (1, 1, 0, 0, 100, 100, 100, 100, 100, 100, 100, 0, 0, 0, 0)
DEFAULT_V2 = DEFAULT_V1 + (0xFFD28D, 1, 100, 100, 0, 100, 0)
PERCENT_RANGES = {
	4: (25, 300), 5: (25, 300), 6: (25, 300), 7: (25, 300),
	8: (25, 300), 9: (25, 500), 10: (25, 300), 13: (0, 100),
	14: (0, 100), 17: (0, 200), 18: (25, 300), 20: (25, 200),
}
FIELD_NAMES = (
	"bodyEnabled", "ringEnabled", "customColorEnabled", "customRgb",
	"bodyStretchPct", "bodyDensityPct", "bodyIntensityPct", "ringDiameterPct",
	"ringBrightnessPct", "bodyReachPct", "bodyFillPct", "bodyStyle",
	"ringStyle", "bodyGapPct", "ringGapPct", "accentRgb", "sparksEnabled",
	"sparkDensityPct", "ringLineWidthPct", "pulseEnabled", "animationSpeedPct",
	"reserved",
)
NEW_STYLE_LABELS = (
	(u"Závoj", u"Závoj"), (u"Pečeť", u"Pečeť"),
	(u"Koróna", u"Koróna"), (u"Rezonance", u"Rezonance"),
	(u"Hadí spirála", u"Hadí spirála"),
)
MODEL_VNUMS = (8001, 8005, 8013)


def HasV2():
	try:
		return (systemSetting.GetMetinQueueAppearanceVersion() >= 2
			and WikiRenderTarget.GetMetinQueueAppearanceVersion() >= 2
			and all(hasattr(systemSetting, name) for name in (
				"GetMetinQueueAppearanceV2", "SetMetinQueueAppearanceV2",
				"GetDefaultMetinQueueAppearanceV2"))
			and all(hasattr(WikiRenderTarget, name) for name in (
				"SelectMetinQueuePreviewV2", "SetMetinQueuePreviewAppearanceV2")))
	except (AttributeError, TypeError, RuntimeError):
		return False


def Normalize(values, version=2):
	defaults = DEFAULT_V2 if version >= 2 else DEFAULT_V1
	try:
		result = list(values)
		if not 9 <= len(result) <= len(defaults):
			return defaults
		result.extend(defaults[len(result):])
		for index in (0, 1, 2):
			result[index] = 1 if result[index] else 0
		result[3] = int(result[3]) & 0xFFFFFF if result[2] else 0
		for index, bounds in PERCENT_RANGES.items():
			if index < len(result):
				result[index] = max(bounds[0], min(bounds[1], int(result[index])))
		result[11] = max(0, min(6 if version >= 2 else 1, int(result[11])))
		result[12] = max(0, min(7 if version >= 2 else 2, int(result[12])))
		if version >= 2:
			result[15] = int(result[15]) & 0xFFFFFF
			result[16] = 1 if result[16] else 0
			result[19] = 1 if result[19] else 0
			result[21] = 0
		return tuple(result)
	except (TypeError, ValueError, OverflowError):
		return defaults


def _Preset(body, ring, rgb, accent, overrides):
	values = list(DEFAULT_V2)
	values[2], values[3], values[11], values[12], values[15] = 1, rgb, body, ring, accent
	for index, value in overrides.items():
		values[index] = value
	return Normalize(values)


# Starting compositions, editable in the same native renderer as the live queue.
PRESETS = (
	("legacy", u"Původní", DEFAULT_V2),
	("veil", u"Závoj", _Preset(2, 3, 0xBD263E, 0xFFD28D, {5: 80, 6: 90, 9: 130, 10: 85})),
	("seal", u"Pečeť", _Preset(3, 4, 0xAD3448, 0xFFD28D, {5: 70, 9: 90, 17: 65, 18: 85})),
	("corona", u"Koróna", _Preset(4, 5, 0xB92835, 0xFFD28D, {5: 115, 9: 120, 17: 120})),
	("resonance", u"Rezonance", _Preset(5, 6, 0x873BC8, 0xFFD28D, {19: 1, 20: 80, 18: 80})),
	("serpent", u"Hadí spirála", _Preset(6, 7, 0xE5B95F, 0xFFF0BC, {5: 80, 17: 60, 20: 80})),
)


class GameBackend(object):
	offline = False

	def __init__(self):
		self.version = 2 if HasV2() else 1

	def Normalize(self, values):
		return Normalize(values, self.version)

	def Defaults(self):
		if self.version >= 2:
			return self.Normalize(systemSetting.GetDefaultMetinQueueAppearanceV2())
		return DEFAULT_V1

	def Read(self):
		getter = (systemSetting.GetMetinQueueAppearanceV2 if self.version >= 2
			else systemSetting.GetMetinQueueAppearance)
		return self.Normalize(getter())

	def ReadNearby(self):
		return 1 if systemSetting.GetMetinQueueNearbyFillEnabled() else 0

	def Apply(self, values, nearby):
		values = self.Normalize(values)
		if self.version >= 2:
			committed = systemSetting.SetMetinQueueAppearanceV2(*values)
		else:
			lastError = None
			for count in (15, 13, 11):
				try:
					committed = systemSetting.SetMetinQueueAppearance(*values[:count])
					break
				except TypeError as error:
					lastError = error
			else:
				raise lastError
		nearby = systemSetting.SetMetinQueueNearbyFillEnabled(1 if nearby else 0)
		return self.Normalize(committed), 1 if nearby else 0


class OfflineBackend(GameBackend):
	"""An isolated in-memory session. Never reads or writes player appearance."""
	offline = True

	def __init__(self):
		GameBackend.__init__(self)
		self.appearance = self.Normalize(PRESETS[1][2]) if self.version >= 2 else DEFAULT_V1
		self.nearby = 1

	def Read(self):
		return self.appearance

	def ReadNearby(self):
		return self.nearby

	def Apply(self, values, nearby):
		self.appearance = self.Normalize(values)
		self.nearby = 1 if nearby else 0
		return self.appearance, self.nearby
