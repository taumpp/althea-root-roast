"""Approved B library policy. Drafts never write native settings before Save."""
import json
import os
import systemSetting
import metinqueuedesign as original
from metinqueuedesign import *

if hasattr(systemSetting, "SetQueueSpiritPreviewDraft"):
    import metinqueuespiritdesign as native
else:
    native = original

FULL_NATIVE = hasattr(systemSetting, "SetQueueLibraryDraft")
RING_TEMPO = 20
RING_SIZE = 21
FIELD_NAMES = original.FIELD_NAMES + ("ringTempo", "ringSize")
VERSION = 10
CONFIG = "UserData/metin-queue-library-b.json"
GOLD = 0xE5B95F
RANGES = dict(original.RANGES)
RANGES[TEMPO] = (0, 150)
RANGES[RING_TEMPO] = (0, 150)
STEPS = dict(original.STEPS)
STEPS[RING_TEMPO] = 5
STEPS[RING_SIZE] = 5
RANGES[RING_SIZE] = (60, 160)
if FULL_NATIVE:
    RANGES[RING_WIDTH] = (80, 120)
if FULL_NATIVE:
    RANGES[SIZE] = (60, 160)

# Owner handoff with lotus retired on 2026-09-09; wire IDs stay stable.
APPROVED_CATALOG = ((28, 'current_pulse', 'Pulzující obal', 'Pulzující obal'), (5, 'orbit', 'Astrální dráhy', 'Astrální dráhy'), (6, 'crystals', 'Krystalový roj', 'Krystalový roj'), (7, 'moons', 'Měsíční srpky', 'Měsíční srpky'), (10, 'phoenix', 'Fénixova křídla', 'Fénixova křídla'), (14, 'blades', 'Tančící čepele', 'Tančící čepele'), (15, 'veil', 'Živý závoj', 'Živý závoj'), (19, 'beacon', 'Světelná koule', 'Světelná koule'), (24, 'native_corona', 'Koróna · Althea', 'Koróna · Althea'), (26, 'native_serpent', 'Hadí spirála · Althea', 'Hadí spirála · Althea'), (34, 'spiral_pair', 'Dvojitá šroubovice', 'Dvojitá šroubovice'), (35, 'falling_stars', 'Hvězdný déšť', 'Hvězdný déšť'), (40, 'comet_pair', 'Dvě komety', 'Dvě komety'), (48, 'double_chevron', 'Dvojitá značka', 'Dvojitá značka'), (49, 'three_sparks', 'Tři světla', 'Tři světla'), (68, 'creature_celestial', 'Východní drak', 'Východní drak'), (72, 'creature_twins', 'Dračí dvojčata', 'Dračí dvojčata'), (96, 'exorcist_seal', 'Pečeť exorcisty', 'Pečeť exorcisty'), (97, 'spirit_tiger', 'Tygří proud', 'Tygří proud · souvislá kresba'), (98, 'spirit_current', 'Duchovní proud', 'Duchovní proud'), (99, 'spirit_wolf', 'Vlčí stopa', 'Vlčí stopa'), (100, 'spirit_dragon', 'Dračí dech', 'Dračí dech'), (101, 'spirit_boar', 'Kančí nápor', 'Kančí nápor'))
APPROVED_RINGS = ((1, 'Klasický vír'), (2, 'Segmenty'), (3, 'Malovaná pečeť'), (7, 'Přerušené oblouky'), (9, 'Světelný běžec'), (12, 'Jemný vír'), (19, 'Dvojitý prstenec'), (20, 'Rezonance'), (21, 'Prstenec jisker'), (22, 'Původní · Krystaly'), (24, 'Původní · Uhlíky'), (25, 'Původní · Závoj'), (26, 'Původní · Závoj Althea'), (27, 'Původní · Koróna'), (28, 'Původní · Rezonance'), (29, 'Chrámová pečeť'), (30, 'Dračí tahy'), (32, 'Obsidiánové desky'))

NATIVE_V5 = original.HasV5()
SPIRIT_IDS = getattr(native, "SPIRIT_IDS", ())
CATALOG = tuple(row for row in APPROVED_CATALOG if FULL_NATIVE or row[0] in native.BY_NUMBER)
BY_NUMBER = dict((row[0], row) for row in CATALOG)
RING_STYLE_CHOICES = tuple(row for row in APPROVED_RINGS if FULL_NATIVE or row[0] in dict(native.RING_STYLE_CHOICES))
RING_NAMES = dict(APPROVED_RINGS)


def Ranges(preset):
    result = dict(RANGES)
    if FULL_NATIVE:
        return result
    if hasattr(native, "Ranges"):
        result.update(native.Ranges(preset))
    result[TEMPO] = (10, 150) if preset in SPIRIT_IDS else original.RANGES[TEMPO]
    result[RING_TEMPO] = (0, 150)
    return result


def RingChoices(preset):
    if FULL_NATIVE:
        return APPROVED_RINGS
    choices = native.RingChoices(preset) if hasattr(native, "RingChoices") else native.RING_STYLE_CHOICES
    # The older spirit bridge's ID2 is a pulsing ring, not the approved Segments.
    allowed = (1, 19) if preset in SPIRIT_IDS or not NATIVE_V5 else tuple(number for number, _ in choices)
    return tuple(row for row in APPROVED_RINGS if row[0] in allowed)


def Defaults(preset=28):
    return (preset, GOLD, 190, 0, 100, 100, 30, GOLD, 0, 200,
            100, 100, 0, 1, 2, 100, 160, 1, 1, 1, 100, 100)


DEFAULT = Defaults()
PROFILE_DEFAULTS = dict((row[0], Defaults(row[0])) for row in CATALOG)


def Normalize(values):
    values = list(values)
    if len(values) in (20, 21, 22) and int(values[PRESET]) == 9:
        values[PRESET] = 28
    if len(values) not in (20, 21, 22) or int(values[PRESET]) not in BY_NUMBER:
        raise ValueError("Unsupported queue library profile")
    result = list(Defaults(int(values[PRESET])))
    result[:len(values)] = [int(value) for value in values]
    if len(values) < 22:
        result[RING_SIZE] = result[SIZE]
    for field, (low, high) in Ranges(result[PRESET]).items():
        result[field] = max(low, min(high, result[field]))
    result[PRIMARY] &= 0xFFFFFF
    # Frozen native ABI slots remain, but the second color is never enabled.
    result[ACCENT], result[ACCENT_ENABLED], result[COLOR_MODE] = result[PRIMARY], 0, 2
    result[COLOR_STRENGTH] = 100
    for field in (RING_ENABLED, BODY_ENABLED):
        result[field] = int(bool(result[field]))
    if result[RING_STYLE] not in dict(RingChoices(result[PRESET])):
        result[RING_STYLE] = 1
    return tuple(result)


def Supports(preset, field, values=None):
    if field is None:
        return True
    if field in (ACCENT, ACCENT_ENABLED, COLOR_MODE, COLOR_STRENGTH, ART_REVISION):
        return False
    if FULL_NATIVE:
        if field == FOCUS:
            return False
        body = values is None or values[BODY_ENABLED]
        ring = values is None or values[RING_ENABLED]
        if field in (SIZE, TEMPO):
            return bool(body) and (field != TEMPO or preset != 28)
        if field in (RING_SIZE, RING_TEMPO):
            return bool(ring)
        if field == RING_WIDTH:
            return bool(ring) and (values is None or values[RING_STYLE] in (2,7,9,12,19,20,21,24,25,29,30,32))
        if field in (MARKER_SCALE, CLEARANCE):
            return bool(body) and preset in (19, 48, 49)
        if field == PULSE:
            return bool(ring) or (bool(body) and preset < 97 and preset != 28)
        if field == GLOW:
            return bool(ring) or (bool(body) and preset in (5,6,7,10,14,15,19,24,26,34,35,40,48,49,96))
        if field == SPARKS:
            return bool(ring) or (bool(body) and preset in (5,6,7,10,14,15,19,34,35,40,48,49))
        return True
    if field == RING_SIZE:
        return False
    if field == RING_TEMPO and native is original:
        return False
    if field == RING_TEMPO and preset not in SPIRIT_IDS:
        return False
    if not native.Supports(preset, field, values):
        return False
    if values is not None:
        if field in (RING_WIDTH, RING_TEMPO):
            return bool(values[RING_ENABLED])
        if field in (TEMPO, CLEARANCE, MARKER_SCALE):
            return bool(values[BODY_ENABLED])
    return True


def _Native(values):
    values = Normalize(values)
    return values[:21] if native is not original else values[:20]


def SelectPreview(index, vnum, values):
    if FULL_NATIVE:
        import WikiRenderTarget
        import metinqueuepresets as appearance
        systemSetting.SetQueueLibraryDraft(*Normalize(values))
        return WikiRenderTarget.SelectMetinQueuePreview(index, vnum, *appearance.DEFAULT_V1)
    return native.SelectPreview(index, vnum, _Native(values))


def UpdatePreview(index, values):
    if FULL_NATIVE:
        import WikiRenderTarget
        import metinqueuepresets as appearance
        systemSetting.SetQueueLibraryDraft(*Normalize(values))
        return WikiRenderTarget.SetMetinQueuePreviewAppearance(index, *appearance.DEFAULT_V1)
    return native.UpdatePreview(index, _Native(values))


def ClearPreview():
    if FULL_NATIVE:
        systemSetting.ClearQueueLibraryDraft()
    if hasattr(native, "ClearPreview"):
        native.ClearPreview()


def DisplayValue(field, value):
    if field == BRIGHTNESS:
        value = int(round(value * 100.0 / 190))
    elif field == GLOW:
        value = int(round(value * 100.0 / 200))
    elif field == MARKER_SCALE:
        value = int(round(value * 100.0 / 160))
    return str(value) if field == CLEARANCE else "%d %%" % value


def SearchKey(text):
    # Embedded Python omits unicodedata. Search must work without native modules.
    text = text.lower()
    for accented, plain in zip(u"áčďéěíňóřšťúůýž", u"acdeeinorstuuyz"):
        text = text.replace(accented, plain)
    return text


class GameBackend(object):
    version = VERSION
    offline = False
    Normalize = staticmethod(Normalize)
    Defaults = staticmethod(Defaults)

    def __init__(self, backend=None):
        self.offline = bool(getattr(backend, "offline", False))
        self.base = None if self.offline else (FullNativeBackend() if FULL_NATIVE else native.AdaptBackend(backend))
        self.active = DEFAULT
        self.saved = dict(PROFILE_DEFAULTS)
        self.nearby = 1 if self.offline else self.base.ReadNearby()
        if not self.offline:
            self._Load()

    def _Load(self):
        if not os.path.isfile(CONFIG):
            return
        try:
            with open(CONFIG, "r") as source:
                data = json.load(source)
            if data.get("version") != 1:
                return
            for key, values in data.get("profiles", {}).items():
                number = int(key)
                if number in BY_NUMBER and int(values[0]) == number:
                    self.saved[number] = Normalize(values)
            active = int(data.get("active", 28))
            if active == 9 and "9" in data.get("profiles", {}):
                self.active = Normalize(data["profiles"]["9"])
                self.saved[28] = self.active
            else:
                self.active = self.saved.get(active, DEFAULT)
        except (OSError, ValueError, TypeError, KeyError, IndexError):
            # Preserve an unreadable file; edits stay usable and Save is explicit.
            self.saved, self.active = dict(PROFILE_DEFAULTS), DEFAULT

    def Read(self):
        return self.active

    def Profiles(self):
        return dict(self.saved)

    def ReadNearby(self):
        return self.nearby if self.offline else self.base.ReadNearby()

    def CanResetAll(self):
        return True

    def ApplyProfiles(self, profiles, active, nearby):
        if set(profiles) != set(BY_NUMBER) or active not in profiles:
            raise ValueError("Incomplete library draft")
        normalized = dict((key, Normalize(value)) for key, value in profiles.items())
        if any(key != value[PRESET] for key, value in normalized.items()):
            raise ValueError("Profile identity mismatch")
        if self.offline:
            self.saved, self.active = normalized, normalized[active]
            self.nearby = int(bool(nearby))
            return self.active, self.nearby
        payload = json.dumps({"version": 1, "active": active,
                              "profiles": normalized}, ensure_ascii=True, indent=2)
        temporary = CONFIG + ".tmp"
        if not self.offline:
            with open(temporary, "w") as target:
                target.write(payload)
                target.flush()
        previous, previousNearby = self.base.Read(), self.base.ReadNearby()
        wasEnabled = systemSetting.IsQueueLibraryEnabled() if FULL_NATIVE else True
        try:
            self.base.Apply(normalized[active] if FULL_NATIVE else _Native(normalized[active]), nearby)
            if not self.offline:
                os.replace(temporary, CONFIG)
        except Exception:
            self.base.Apply(previous, previousNearby)
            if FULL_NATIVE and not wasEnabled:
                systemSetting.DisableQueueLibrary()
            raise
        self.saved = normalized
        self.active = normalized[active]
        self.nearby = int(bool(nearby))
        return self.active, self.nearby

    def Apply(self, values, nearby):
        profiles = self.Profiles()
        profiles[values[PRESET]] = Normalize(values)
        return self.ApplyProfiles(profiles, values[PRESET], nearby)


def AdaptBackend(backend=None):
    return backend if isinstance(backend, GameBackend) else GameBackend(backend)


class FullNativeBackend(object):
    def Read(self):
        return Normalize(systemSetting.GetQueueLibrary())

    def ReadNearby(self):
        return systemSetting.GetMetinQueueNearbyFillEnabled()

    def Apply(self, values, nearby):
        committed = Normalize(systemSetting.SetQueueLibrary(*Normalize(values)))
        nearby = systemSetting.SetMetinQueueNearbyFillEnabled(int(bool(nearby)))
        return committed, int(bool(nearby))
