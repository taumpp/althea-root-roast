"""Presentation state for the typed native guild protocol; no economy writer."""
import time

SUMMARY, BALANCE, PASSIVE, GOAL, MEMBER, RIGHTS, DOCTRINE = range(1, 8)
APPROVAL, NOTICE, PROFILE, EXPEDITION, PARTICIPANT, MILESTONE = range(8, 14)
LEDGER, CONTRIBUTION, RECRUITMENT, INVITATION, CATALOG, RECEIPT = range(14, 20)
CAPABILITY, GOAL_HISTORY, AUDIT, CHRONICLE, INSTANCE = range(20, 25)
CONTRACTS = 25
SNAPSHOT, BROWSE, HISTORY, CREATE, UPGRADE, CREATE_GOAL, EDIT_GOAL = range(1, 8)
SET_ROLE, SET_RIGHTS, INVITE, ACCEPT_INVITE, LEAVE, KICK, TRANSFER = range(8, 15)
DISBAND, DEPOSIT, SET_PROFILE, POST_NOTICE, DELETE_NOTICE, PROPOSE_DOCTRINE = range(15, 21)
APPROVE, ENROLL, READY_CHECK, READY, START, VOTE, VILLAGE = range(21, 28)
SELECT_CONTRACTS = 28
OK, UNAVAILABLE, INVALID, FORBIDDEN, NOT_MEMBER, STALE = range(6)
MATERIALS = ("Úlomky Meteoru", "Cechovní ruda", "Fragmenty duše")
MATERIAL_ICONS = ("metin", "ore", "soul")
ROLES = ("Vůdce", "Rada", "Člen")
DOCTRINES = ("Bez doktríny", "Lovci nestvůr", "Průzkumníci")
RIGHT_NAMES = ("Správa členů a hodností", "Volba kontraktů", "Nastavení cechovního cíle",
    "Správa doktríny", "Vylepšování schopností", "Použití materiálů", "Správa pokladny",
    "Spuštění výpravy", "Schvalování rozhodnutí", "Rozšířený audit")
STATUS_TEXT = (
    "Změna byla potvrzena.", "Tato akce teď není dostupná.", "Zkontroluj zadané hodnoty.",
    "K této akci nemáš oprávnění.", "Nejsi členem cechu.", "Údaje se změnily. Obnov je a potvrď znovu.",
    "Cech nemá dostatek materiálů nebo Yang.", "Schopnost už má nejvyšší stupeň.",
    "Probíhá jiná operace. Zkus to za chvíli.", "Čas pro tuto akci vypršel.",
    "Podmínky ještě nejsou splněny.", "Požadavek už byl použit nebo se změnil jeho obsah.",
    "Požadovaný záznam nebyl nalezen.", "Není dostatek volných míst.",
    "Spojení se obnovuje.", "Čekáme na potvrzení serveru.")
ROMAN = ("—", "I", "II", "III", "IV", "V")
POINTS_HELP = ("Osobní cechovní body získávají členové, kteří přispěli do splněného cechovního cíle, "
    "a účastníci úspěšné výpravy. Body patří členství v cechu; po odchodu se nepřenášejí.")
PASSIVE_DESCRIPTIONS = {
    1: "Bonus k průměrné škodě", 2: "Bonus k poškození schopností", 3: "Pevná hodnota útoku",
    4: "Zvyšuje maximální ZB", 5: "Silný proti meteorům", 6: "Síla proti příšerám",
    7: "Síla proti bossům", 8: "Síla blesku, ohně, ledu, větru, země a temnoty",
    10: "Šance získat při zabití o 30 % více EXP", 11: "Síla proti lidem", 12: "Rychlost pohybu"}
PASSIVE_ICONS = {1: "glyph_damage", 2: "glyph_guide", 3: "nav_expedition_28x28",
    4: "glyph_level", 5: "passive_stone_41x41", 6: "passive_beast_41x41", 7: "passive_boss_41x41",
    8: "dragon_eye_41x41", 10: "nav_chronicle_28x28", 11: "nav_members_28x28", 12: "glyph_cooldown"}

def number(value):
    return format(int(value), ",").replace(",", " ")

def effect(identifier, value):
    return "+" + number(value) + ("" if identifier in (3, 4) else " %")

def moment(epoch):
    try:
        return time.strftime("%d.%m.%Y %H:%M", time.localtime(int(epoch))) if epoch else "—"
    except (ValueError, OverflowError, OSError):
        return "—"

def duration(seconds):
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    return (number(days) + " d " if days else "") + "%02d:%02d" % (hours, minutes)

def positive(text, allow_zero=False):
    text = str(text).strip()
    if not text.isascii() or not text.isdecimal():
        raise ValueError("Zadej celé kladné číslo.")
    value = int(text)
    if value > 9223372036854775807 or value < (0 if allow_zero else 1):
        raise ValueError("Hodnota je mimo povolený rozsah.")
    return value

class Model:
    def __init__(self):
        self.guild = self.revision = self.generation = 0
        self.server_time = 0
        self.received_at = 0.0
        self.sections = {}
        self.history = {}
        self.history_kind = 0
        self.history_cursor = 0
        self.history_next = 0
        self.status = UNAVAILABLE

    def receive(self, payload, now):
        status = int(payload["status"])
        grouped = {}
        for section, values, title, body in payload["rows"]:
            grouped.setdefault(section, []).append((tuple(values), title, body))
        full = SUMMARY in grouped
        changed_guild = full and self.guild != payload["guild"]
        if full:
            if not changed_guild and payload["revision"] < self.revision:
                return False
            self.guild, self.revision = int(payload["guild"]), int(payload["revision"])
            if changed_guild:
                self.history.clear()
            self.sections = grouped
        elif status == NOT_MEMBER or (status == OK and not payload["guild"] and payload["action"] != BROWSE):
            self.guild = self.revision = 0
            self.sections.clear()
            self.history.clear()
            self.sections.update(grouped)
        else:
            for section in (CAPABILITY, INVITATION, RECRUITMENT):
                if section in grouped:
                    self.sections[section] = grouped[section]
            if payload["action"] == BROWSE and status == OK:
                self.sections[RECRUITMENT] = grouped.get(RECRUITMENT, [])
            if payload["action"] == HISTORY and status == OK:
                self.history = grouped
                records = [row for section, rows in grouped.items() if section != CAPABILITY for row in rows]
                self.history_next = records[-1][0][0] if len(records) == 50 else 0
        self.status, self.generation = status, int(payload["generation"])
        if payload["server_time"]:
            self.server_time, self.received_at = int(payload["server_time"]), float(now)
        return True

    def now(self, now):
        return self.server_time + max(0, int(float(now) - self.received_at))

    def rows(self, section):
        return self.sections.get(section, ())

    def row(self, section):
        return self.rows(section)[0] if self.rows(section) else ((0,) * 10, "", "")

    def member(self, pid):
        return next((row for row in self.rows(MEMBER) if row[0][0] == pid), None)

    def ranking(self):
        """Members by personal guild points (Member v8); equal points share a place."""
        members = sorted(self.rows(MEMBER), key=lambda row: (-row[0][8], row[1], row[0][0]))
        return [(1 + sum(1 for other in members if other[0][8] > row[0][8]), row) for row in members]

    def rights(self, pid):
        member = self.member(pid)
        return self.row(RIGHTS)[0][member[0][1]] if member else 0

    def can(self, pid, mask):
        return self.rights(pid) & mask == mask

    def rank(self, identifier):
        return next((row[0][1] for row in self.rows(PASSIVE) if row[0][0] == identifier), 0)

    def catalog(self, identifier, rank):
        return next((row for row in self.rows(CATALOG) if row[0][:2] == (identifier, rank)), None)

    def passive_ids(self):
        return tuple(row[0][0] for row in self.rows(PASSIVE))

    def identity(self):
        return (self.guild, self.revision, self.generation)


def invitation_link_id(link):
    prefix = "guildinvite:"
    if not link.startswith(prefix):
        return None
    value = link[len(prefix):]
    if not value.isascii() or not value.isdecimal() or len(value) > 20:
        return None
    identifier = int(value)
    return identifier if 0 < identifier <= 18446744073709551615 else None


class InvitationNotices:
    """Bounded presentation-only memory; survives rebuilding UI during a warp."""
    def __init__(self):
        self.pid = 0
        self.seen = []

    def observe(self, pid, rows, now):
        if not pid:
            return []
        if self.pid != pid:
            self.pid, self.seen = pid, []
        fresh = []
        for values, name, body in rows:
            identifier = values[0]
            if identifier > 0 and values[2] > now and identifier not in self.seen:
                fresh.append((identifier, name))
        return fresh

    def shown(self, identifier):
        if identifier not in self.seen:
            self.seen = (self.seen + [identifier])[-128:]


invitation_notices = InvitationNotices()
