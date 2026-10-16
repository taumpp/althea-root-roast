"""Spirit profiles in the existing queue editor; native V5 remains unchanged."""
import systemSetting
import WikiRenderTarget
import metinqueuedesign as original
import metinqueuepresets as legacy
from metinqueuedesign import *

RING_TEMPO = 20
FIELD_NAMES = original.FIELD_NAMES + ("ringTempo",)
SPIRITS = (
    (97, "tiger_current", u"Tygří proud", u"Prostorová tygří hlava s navazujícím proudem."),
    (98, "spirit_current", u"Duchovní proud", u"Proud energie bez hlavy."),
    (99, "wolf_current", u"Vlčí stopa", u"Vlčí hlava a úzká pohyblivá stopa."),
    (100, "dragon_current", u"Dračí dech", u"Dračí hlava s navazujícím proudem."),
    (101, "boar_current", u"Kančí nápor", u"Kančí hlava s kly a proudem energie."),
)
SPIRIT_IDS = tuple(row[0] for row in SPIRITS)
LEGACY_CATALOG = (
    (0, "legacy_continuous", u"Původní obal", u"Původní souvislý částicový obal."),
    (28, "legacy_pulse", u"Pulzující obal", u"Původní pulzující částicový obal."),
)
NATIVE_V5 = original.HasV5()
CATALOG = (original.CATALOG if NATIVE_V5 else LEGACY_CATALOG) + SPIRITS
BY_NUMBER = dict((row[0], row) for row in CATALOG)
SPIRIT_RINGS = ((1, u"Klasický prstenec"), (2, u"Pulzující prstenec"), (19, u"Dvojitý prstenec"))
RING_STYLE_CHOICES = original.RING_STYLE_CHOICES if NATIVE_V5 else SPIRIT_RINGS
RING_NAMES = dict(RING_STYLE_CHOICES)
RANGES = dict(original.RANGES)
RANGES[RING_TEMPO] = (0, 240)
STEPS = dict(original.STEPS)
STEPS[RING_TEMPO] = 5
if not NATIVE_V5:
    STEPS[COLOR_STRENGTH] = 100


def Ranges(preset):
    result = dict(RANGES)
    if preset in SPIRIT_IDS:
        result[SIZE] = (60, 160)
        result[TEMPO] = (10, 240)
    return result


def RingChoices(preset):
    return SPIRIT_RINGS if preset in SPIRIT_IDS or not NATIVE_V5 else RING_STYLE_CHOICES


def Defaults(preset=97):
    if preset in SPIRIT_IDS:
        return (preset, 0xFFCC78, 160, 0, 100, 100, 30, 0xFFD28D, 0,
                100, 100, 100, 0, 1, 2, 100, 160, 1, 1, 1, 100)
    if not NATIVE_V5:
        return (preset, 0xAD3DFF, 100, 0, 100, 100, 30, 0xFFD28D, 0,
                100, 100, 100, 0, 1, 2, 0, 160, 1, 1, 1, 100)
    return original.Defaults(preset) + (100,)


DEFAULT = Defaults()
PROFILE_DEFAULTS = dict((row[0], Defaults(row[0])) for row in CATALOG)


def Normalize(values):
    result = [int(value) for value in values]
    if len(result) not in (20, 21) or result[PRESET] not in BY_NUMBER:
        raise ValueError("Unknown queue editor profile")
    result.extend(Defaults(result[PRESET])[len(result):])
    preset = result[PRESET]
    if preset not in SPIRIT_IDS and NATIVE_V5:
        return original.Normalize(result[:20]) + (result[RING_TEMPO],)
    for field, bounds in Ranges(preset).items():
        result[field] = max(bounds[0], min(bounds[1], result[field]))
    for field in (PRIMARY, ACCENT):
        result[field] &= 0xFFFFFF
    for field in (BODY_ENABLED, RING_ENABLED, ACCENT_ENABLED):
        result[field] = int(bool(result[field]))
    if result[RING_STYLE] not in dict(RingChoices(preset)):
        result[RING_STYLE] = 1
    return tuple(result)


def Supports(preset, field, values=None):
    if field is None:
        return True
    if preset in SPIRIT_IDS:
        return field in (PRIMARY, BRIGHTNESS, SIZE, TEMPO, RING_TEMPO,
                         BODY_ENABLED, RING_ENABLED, RING_STYLE)
    if not NATIVE_V5:
        return field in (PRIMARY, COLOR_STRENGTH, BRIGHTNESS, SIZE,
                         BODY_ENABLED, RING_ENABLED, RING_STYLE)
    return field != RING_TEMPO and original.Supports(preset, field, values)


def _Spirit(values):
    return (values[PRESET] if values[PRESET] in SPIRIT_IDS else 0,
            values[PRIMARY], values[BRIGHTNESS], values[SIZE], values[TEMPO],
            values[RING_TEMPO], values[BODY_ENABLED], values[RING_ENABLED],
            {1: 0, 2: 1, 19: 2}.get(values[RING_STYLE], 0))


def _FromSpirit(values):
    result = list(Defaults(values[0]))
    for field, value in zip((PRESET, PRIMARY, BRIGHTNESS, SIZE, TEMPO,
                            RING_TEMPO, BODY_ENABLED, RING_ENABLED), values[:8]):
        result[field] = value
    result[RING_STYLE] = (1, 2, 19)[max(0, min(2, values[8]))]
    return Normalize(result)


def _Legacy(values):
    # Preserve original dimensions, density and spacing; the simplified editor
    # changes only controls it actually exposes.
    result = list(legacy.Normalize(systemSetting.GetMetinQueueAppearance(), 1))
    result[0], result[1] = values[BODY_ENABLED], values[RING_ENABLED]
    result[2] = int(values[COLOR_STRENGTH] > 0)
    result[3] = values[PRIMARY] if result[2] else 0
    result[4], result[6], result[7] = values[SIZE], values[BRIGHTNESS], values[SIZE]
    result[8] = values[RING_WIDTH]
    result[11] = int(values[PRESET] == 28)
    result[12] = {1: 0, 2: 1, 19: 2}[values[RING_STYLE]]
    return tuple(result)


def _FromLegacy(values):
    result = list(Defaults(28 if values[11] else 0))
    result[BODY_ENABLED], result[RING_ENABLED] = values[0], values[1]
    result[COLOR_STRENGTH] = 100 if values[2] else 0
    result[PRIMARY] = values[3] if values[2] else 0xAD3DFF
    result[SIZE], result[BRIGHTNESS] = values[4], values[6]
    result[RING_STYLE] = (1, 2, 19)[values[12]]
    return Normalize(result)


def SelectPreview(index, vnum, values):
    values = Normalize(values)
    systemSetting.SetQueueSpiritPreviewDraft(*_Spirit(values))
    if values[PRESET] in SPIRIT_IDS:
        # The native actor remains a queue target while its old body is hidden.
        return WikiRenderTarget.SelectMetinQueuePreview(index, vnum, *legacy.DEFAULT_V1)
    if NATIVE_V5:
        return original.SelectPreview(index, vnum, values[:20])
    return WikiRenderTarget.SelectMetinQueuePreview(index, vnum, *_Legacy(values))


def UpdatePreview(index, values):
    values = Normalize(values)
    systemSetting.SetQueueSpiritPreviewDraft(*_Spirit(values))
    if values[PRESET] in SPIRIT_IDS:
        return WikiRenderTarget.SetMetinQueuePreviewAppearance(index, *legacy.DEFAULT_V1)
    if NATIVE_V5:
        return original.UpdatePreview(index, values[:20])
    return WikiRenderTarget.SetMetinQueuePreviewAppearance(index, *_Legacy(values))


def ClearPreview():
    systemSetting.ClearQueueSpiritPreviewDraft()


class GameBackend(object):
    version = 6
    offline = False
    Normalize = staticmethod(Normalize)
    Defaults = staticmethod(Defaults)

    def __init__(self):
        self.base = original.GameBackend() if NATIVE_V5 else legacy.GameBackend()
        self.spiritProfiles = dict((number, Defaults(number)) for number in SPIRIT_IDS)

    def Read(self):
        spirit = systemSetting.GetQueueSpiritPreview()
        if spirit[0] in SPIRIT_IDS:
            return _FromSpirit(spirit)
        values = self.base.Read()
        return values + (100,) if NATIVE_V5 else _FromLegacy(values)

    def Profiles(self):
        result = dict(PROFILE_DEFAULTS)
        if NATIVE_V5:
            result.update((number, values + (100,)) for number, values in self.base.Profiles().items())
        result.update(self.spiritProfiles)
        active = self.Read()
        result[active[PRESET]] = active
        return result

    def ReadNearby(self):
        return self.base.ReadNearby()

    def CanResetAll(self):
        return not NATIVE_V5 or self.base.CanResetAll()

    def Apply(self, values, nearby):
        values = Normalize(values)
        if values[PRESET] in SPIRIT_IDS:
            committed = _FromSpirit(systemSetting.SetQueueSpiritPreview(*_Spirit(values)))
            nearby = systemSetting.SetMetinQueueNearbyFillEnabled(int(bool(nearby)))
            self.spiritProfiles[values[PRESET]] = committed
            return committed, int(bool(nearby))
        saved = systemSetting.GetQueueSpiritPreview()
        systemSetting.SetQueueSpiritPreview(0, *saved[1:])
        try:
            committed, nearby = self.base.Apply(values[:20] if NATIVE_V5 else _Legacy(values), nearby)
        except Exception:
            systemSetting.SetQueueSpiritPreview(*saved)
            raise
        return (committed + (100,) if NATIVE_V5 else _FromLegacy(committed)), nearby

    def ApplyProfiles(self, profiles, active, nearby):
        if set(profiles) != set(BY_NUMBER) or active not in profiles:
            raise ValueError("Complete queue profile set required")
        normalized = dict((number, Normalize(values)) for number, values in profiles.items())
        if any(values[PRESET] != number for number, values in normalized.items()):
            raise ValueError("Queue profile identity mismatch")
        savedSpirit = systemSetting.GetQueueSpiritPreview()
        savedBase, savedNearby = self.base.Read(), self.base.ReadNearby()
        savedProfiles = self.base.Profiles() if NATIVE_V5 else None
        savedMemory = dict(self.spiritProfiles)
        try:
            if NATIVE_V5:
                oldProfiles = dict((number, normalized[number][:20]) for number in original.BY_NUMBER)
                oldActive = active if active not in SPIRIT_IDS else savedBase[PRESET]
                self.base.ApplyProfiles(oldProfiles, oldActive, nearby)
            else:
                # V1 stores one appearance; other original mode has no saved profile.
                oldActive = active if active not in SPIRIT_IDS else (28 if savedBase[11] else 0)
                self.base.Apply(_Legacy(normalized[oldActive]), nearby)
            result, committedNearby = self.Apply(normalized[active], nearby)
        except Exception:
            self.spiritProfiles = savedMemory
            if NATIVE_V5:
                self.base.ApplyProfiles(savedProfiles, savedBase[PRESET], savedNearby)
            else:
                self.base.Apply(savedBase, savedNearby)
            systemSetting.SetQueueSpiritPreview(*savedSpirit)
            raise
        self.spiritProfiles = dict((number, normalized[number]) for number in SPIRIT_IDS)
        return result, committedNearby


def AdaptBackend(backend=None):
    if isinstance(backend, GameBackend):
        return backend
    return GameBackend()

