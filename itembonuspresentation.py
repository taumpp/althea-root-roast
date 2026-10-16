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


def WeaponBase(value, percent):
    return min(2147483647, int(value) * (100 + max(0, int(percent))) // 100) if value > 0 else value


def WeaponRange(minimum, maximum, refinement, percent):
    return (WeaponBase(minimum, percent) + refinement,
            WeaponBase(maximum, percent) + refinement)


def WeaponSuffix(percent):
    return " (+%d%%)" % percent if percent > 0 else ""


class EquipmentTotals(object):
    """Bounded, atomic read-only server snapshot; never infer gear from all stats."""
    def __init__(self):
        self._serial = 0
        self._version = 0
        self.EndSession()

    def EndSession(self):
        self._send = None
        self._clock = lambda: 0.0
        self._nextRequest = 0.0
        self._expires = 0.0
        self._request = None
        self._parts = {}
        self._count = None
        self._values = None
        self._version += 1

    def BeginSession(self, clock, send):
        self.EndSession()
        self._clock, self._send = clock, send

    def Request(self):
        if self._send is None or self._clock() < self._nextRequest:
            return False
        self._nextRequest = self._clock() + 1.0
        self._serial = self._serial % 4294967295 + 1
        self._request = self._serial
        self._parts, self._count = {}, None
        self._send("/equipment_bonuses %d" % self._request)
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
                    if not 1 <= kind <= 255 or abs(value) > 9223372036854775807 or kind in values:
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
        return True

    def Version(self):
        return (self._version, self._values is not None and self._clock() < self._expires)

    def Get(self, kind):
        if not self.Version()[1]:
            return None
        return self._values.get(kind, 0)

    def Format(self, text, kind):
        value = self.Get(kind)
        if value is None:
            return text
        return text + " (%d%s)" % (value, "%" if "%" in text else "")


totals = EquipmentTotals()


def TotalsLegend(czech):
    return (u"V z\u00e1vorce: nasazen\u00e1 v\u00fdbava." if czech
            else "In brackets: equipped items.")
