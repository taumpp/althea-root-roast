"""Read-only item presentation; combat remains server-authoritative."""

_talentWeaponPercent = 0


def SetTalentWeaponPercent(percent):
    global _talentWeaponPercent
    _talentWeaponPercent = max(0, min(12, int(percent)))


def WeaponPercent(player, item):
    applyType = getattr(item, "APPLY_WEAPON_BASE_PERCENT", None)
    point = item.GetApplyPoint(applyType) if applyType is not None else 0
    if not point:
        return 0
    return max(0, int(player.GetStatus(point)) + _talentWeaponPercent)


# Skill tree duration nodes: 2124 jewellery ores, 2141 dews.
# The server (common/talent/talent_effects.h, common/dew_policy.h) keeps the
# item's own seconds unmodified and stretches them while the timer runs, so a
# tooltip that prints the raw socket shows the base time. These helpers turn
# that base into the time the owner really gets. Both bonuses are capped at
# +25 % by the server.
TALENT_DURATION_MAX = 25
LEGACY_DEW_FIRST = 50821
LEGACY_DEW_LAST = 50826
LEGACY_DEW_EXTENDED_OFFSET = 900000

_talentJewelryPercent = 0
_talentDewPercent = 0


def _ClampDuration(percent):
    try:
        return max(0, min(TALENT_DURATION_MAX, int(percent)))
    except (TypeError, ValueError):
        return 0


def SetTalentDurationPercents(jewelry, dew):
    global _talentJewelryPercent, _talentDewPercent
    _talentJewelryPercent = _ClampDuration(jewelry)
    _talentDewPercent = _ClampDuration(dew)


def TalentJewelryPercent():
    return _talentJewelryPercent


def TalentDewPercent():
    return _talentDewPercent


def IsLegacyDew(vnum):
    vnum = int(vnum)
    if LEGACY_DEW_FIRST + LEGACY_DEW_EXTENDED_OFFSET <= vnum <= LEGACY_DEW_LAST + LEGACY_DEW_EXTENDED_OFFSET:
        vnum -= LEGACY_DEW_EXTENDED_OFFSET
    return LEGACY_DEW_FIRST <= vnum <= LEGACY_DEW_LAST


def IncreaseByPercent(seconds, percent):
    """talent::IncreaseByPercent: legacy dews and jewellery ores."""
    seconds, percent = int(seconds), int(percent)
    if seconds <= 0 or percent <= 0:
        return seconds
    return min(2147483647, seconds + seconds * percent // 100)


def DewSeconds(seconds, freshSeconds, masterySeconds, percent):
    """dew::EffectiveDuration: crafted dews with Dew Mastery and the tree."""
    seconds, freshSeconds = int(seconds), int(freshSeconds)
    if seconds <= 0 or freshSeconds <= 0:
        return seconds
    percent = _ClampDuration(percent)
    return seconds * (freshSeconds + max(0, int(masterySeconds))) * (100 + percent) // (freshSeconds * 100)


def DurationSuffix(percent, template):
    if percent <= 0:
        return ""
    # Byte str on purpose: the Python 2 client joins it to cp1250 locale text.
    return template % percent


def WeaponBase(value, percent):
    return min(2147483647, int(value) * (100 + max(0, int(percent))) // 100) if value > 0 else value


def WeaponRange(minimum, maximum, refinement, percent):
    return (WeaponBase(minimum, percent) + refinement,
            WeaponBase(maximum, percent) + refinement)


def WeaponSuffix(percent):
    return " (+%d%%)" % percent if percent > 0 else ""


def _SashShare(base, percent, present):
    # item.cpp ModifyPoints: (long)(base * percent / 100 + .5), then one more
    # point whenever the donor has the underlying value at all.
    return (int(base) * int(percent) * 2 + 100) // 200 + (1 if present else 0)


def SashWeaponAttack(values, percent, isBow=False):
    """Attack value the server grants for an absorbed weapon: one number."""
    base = max(values[3], values[4]) + values[5]
    if isBow and values[0] > 0:
        # Value0 preserves the original donor maximum after narrowing the bow range.
        base = values[0]
    return _SashShare(base, percent, values[3] > 0 or values[4] > 0)


def SashWeaponMagicAttack(values, percent):
    return _SashShare(max(values[1], values[2]) + values[5], percent,
                      values[1] > 0 or values[2] > 0)


def SashArmorDefence(values, percent):
    return _SashShare(values[1] + values[5] * 2, percent, values[1] > 0 or values[5] > 0)


def SashArmorMagicDefence(values, percent):
    return _SashShare(values[0], percent, values[0] > 0)


class EquipmentTotals(object):
    """Bounded, atomic read-only server snapshot; never infer gear from all stats."""
    _RESPONSE_TIMEOUT = 10.0
    def __init__(self, command="/equipment_bonuses", maximumKind=255):
        self._command, self._maximumKind = command, maximumKind
        self._serial = 0
        self._version = 0
        self.EndSession()

    def EndSession(self):
        self._send = None
        self._clock = lambda: 0.0
        self._nextRequest = 0.0
        self._expires = 0.0
        self._request = None
        self._requestDeadline = 0.0
        self._parts = {}
        self._count = None
        self._values = None
        self._version += 1

    def BeginSession(self, clock, send):
        self.EndSession()
        self._clock, self._send = clock, send

    def Request(self):
        now = self._clock()
        if self._send is None or now < self._nextRequest:
            return False
        # Polling must not replace a response that is still in flight. Its
        # chunks share one identity and are published only as a complete set.
        if self._request is not None and now < self._requestDeadline:
            return False
        self._nextRequest = now + 1.0
        self._serial = self._serial % 4294967295 + 1
        self._request = self._serial
        self._requestDeadline = now + self._RESPONSE_TIMEOUT
        self._parts, self._count = {}, None
        self._send("%s %d" % (self._command, self._request))
        return True

    def Receive(self, request, index, count, payload):
        if self._send is None:
            return False
        try:
            request, index, count = int(request), int(index), int(count)
            if request != self._request or not (1 <= count <= 32 and 0 <= index < count):
                return False
            if len(payload) > 350 or index in self._parts or self._count not in (None, count):
                return False
            values = {}
            if payload != "-":
                for entry in payload.split(","):
                    kind, value = (int(part) for part in entry.split(":"))
                    if not 1 <= kind <= self._maximumKind or abs(value) > 9223372036854775807 or kind in values:
                        return False
                    values[kind] = value
            elif count != 1:
                return False
            if any(kind in part for kind in values for part in self._parts.values()):
                return False
        except (ValueError, TypeError, OverflowError):
            return False
        self._count = count
        self._parts[index] = values
        if len(self._parts) != count:
            return False
        merged = {}
        for part in self._parts.values():
            merged.update(part)
        if merged != self._values:
            self._version += 1
        self._values = merged
        self._expires = self._clock() + 3.0
        self._request = None
        self._parts, self._count = {}, None
        return True

    def Version(self):
        return (self._version, self._values is not None and self._clock() < self._expires)

    def Get(self, kind):
        if not self.Version()[1]:
            return None
        return self._values.get(kind, 0)

    def GetExact(self, kind):
        if not self.Version()[1]:
            return None
        return self._values.get(kind)

    def Format(self, text, kind):
        value = self.Get(kind)
        if value is None:
            return text
        return text + " (%d%s)" % (value, "%" if "%" in text else "")


totals = EquipmentTotals()


def TotalsLegend(czech):
    return (u"V z\u00e1vorce: nasazen\u00e1 v\u00fdbava." if czech
            else "In brackets: equipped items.")
