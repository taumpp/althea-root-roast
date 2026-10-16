"""Server-owned PvM state. This module intentionally has no engine imports."""
SOURCES = {
    (0, 1): (4, 2, 3), (0, 2): (16, 19, 18),
    (1, 1): (31, 34, 33), (1, 2): (46, 49, 47),
    (2, 1): (63, 65, 64), (2, 2): (76, 79, 80),
    (3, 1): (96, 94, 95), (3, 2): (111, 106, 110),
}
HUD_SKILLS = frozenset((2, 16, 18, 31, 33, 46, 47, 76, 80, 106))
CAST_SKILLS = frozenset(s for row in SOURCES.values() for s in row) - HUD_SKILLS
SUPPORT_SKILLS = frozenset((94, 95, 96, 110, 111))
_current = None
_warp_handoff = None


def save_warp(character, model):
    global _warp_handoff
    _warp_handoff = (character, set(model.seen), list(model.acks))


def restore_warp(character, model):
    global _warp_handoff
    if _warp_handoff and _warp_handoff[0] == character:
        model.seen, model.acks = _warp_handoff[1:]
    _warp_handoff = None


def clear_warp():
    global _warp_handoff
    _warp_handoff = None


def set_current(model):
    global _current
    _current = model


def current():
    return _current if _current and _current.enabled else None


def grade(level):
    if level >= 50: return 'S1'
    if level >= 40: return 'P%d' % (level - 39)
    if level >= 30: return 'G%d' % (level - 29)
    if level >= 20: return 'M%d' % (level - 19)
    return str(level)


def icon_grade(level):
    return 4 if level >= 50 else 3 if level >= 40 else 2 if level >= 30 else 1 if level >= 20 else 0


class Model:
    def __init__(self):
        self.enabled = False
        self.rows = {}
        self.serial = 0
        self.received = 0.0
        self.server_time = 0
        self.identity = None
        self.seen = set()
        self.acks = []

    def accept(self, arguments, now, job, group):
        if len(arguments) != 35:
            return False
        values = []
        for token in arguments:
            if not isinstance(token, str) or not token or len(token) > 10 or any(c < '0' or c > '9' for c in token):
                return False
            values.append(int(token))
        version, server, wire_job, wire_group, serial = values[:5]
        if version != 1 or (wire_job, wire_group) != (job, group) or (job, group) not in SOURCES:
            return False
        if not 1577836800 <= server <= 3725320447 or not self.serial < serial <= 4294967295:
            return False
        rows = {}
        for role, source in enumerate(SOURCES[job, group]):
            skill, hud, learned, activated, revision, end, value, power, notice, status = values[5 + role*10:15 + role*10]
            if skill != source or hud != int(skill in HUD_SKILLS) or not 0 <= activated <= learned <= 50:
                return False
            if revision > 2147483647 or value > 10000000 or power > 175 or notice not in (0, 1) or status not in (0, 1, 2):
                return False
            if (status == 0 and end != 0) or (status == 1 and not server < end <= server + 7200):
                return False
            if (status == 2 and not 1577836800 <= end <= server) or (notice and status != 2):
                return False
            if status == 1 and (activated == 0 or power == 0):
                return False
            rows[skill] = dict(skill=skill, hud=hud, learned=learned, activated=activated,
                revision=revision, end=end, value=value, power=power, notice=notice, status=status, role=role)
        self.rows = rows
        self.identity = (job, group)
        self.serial, self.server_time, self.received = serial, server, now
        self.enabled = True
        self.seen.intersection_update((r['skill'], r['revision']) for r in rows.values())
        return True

    def remaining(self, skill, now):
        row = self.rows.get(skill)
        if not row or row['status'] != 1:
            return 0
        return max(0, int(row['end'] - self.server_time - max(0.0, now - self.received)))

    def hud_rows(self):
        return [r for r in self.rows.values() if r['hud'] and r['learned'] > 0]

    def command(self, skill, on, now):
        row = self.rows.get(skill)
        if not row or not row['hud'] or not row['learned']:
            return None
        if on and self.remaining(skill, now):
            return None
        return '/pvm_bonus set %d %d %d' % (skill, bool(on), row['revision'])

    def notices(self):
        return [(r['skill'], r['revision']) for r in self.rows.values()
            if r['notice'] and (r['skill'], r['revision']) not in self.seen]

    def displayed(self, identities):
        for identity in identities:
            if identity not in self.seen:
                self.seen.add(identity)
                self.acks.append(identity)

    def next_ack(self):
        if not self.acks:
            return None
        return '/pvm_bonus ack %d %d' % self.acks.pop(0)
