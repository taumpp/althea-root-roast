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
# Commands the server accepts at any revision of the same guild (batch 7 add-on, player report 21. 10.: the
# first deposit / invitation failed because member awards had changed the revision while the dialog was open).
ANY_REVISION = (INVITE, DEPOSIT, POST_NOTICE)
OK, UNAVAILABLE, INVALID, FORBIDDEN, NOT_MEMBER, STALE = range(6)
INSUFFICIENT, MAX_LEVEL, BUSY, EXPIRED, NOT_READY, CONFLICT, NOT_FOUND, CAPACITY = range(6, 14)
# Guild growth materials follow the server stock/rankgrow order.
GROWTH = ("cores", "scales", "wood")
# BEGIN GENERATED GUILD STOCK PANEL (tools/build_guild_stock_panel.py from tools/data/guild_v2_stock_panel.json)
STOCK_PER_ROW = 4
STOCK_PANEL = (  # (key, source, field, locale label, icon)
    ('shards', 'balance', 0, 'GUILD_V2_STOCK_SHARDS', 'metin'),
    ('ore', 'balance', 1, 'GUILD_V2_STOCK_ORE', 'ore'),
    ('souls', 'balance', 2, 'GUILD_V2_STOCK_SOULS', 'soul'),
    ('yang', 'balance', 3, '', ''),
    ('scales', 'stock', 'scales', 'GUILD_V2_STOCK_SCALES', 'scale'),
    ('wood', 'stock', 'wood', 'GUILD_V2_STOCK_WOOD', 'wood'),
)
MATERIALS = tuple(row[3] for row in STOCK_PANEL if row[1] == 'balance' and row[4])
MATERIAL_ICONS = tuple(row[4] for row in STOCK_PANEL if row[1] == 'balance' and row[4])
# END GENERATED GUILD STOCK PANEL
# The members' contributions (Cech -> Členové -> Příspěvky): the three materials, then scales and wood.
CONTRIBUTIONS = MATERIALS + ('GUILD_V2_STOCK_SCALES', 'GUILD_V2_STOCK_WOOD')
# The Yang column after them (owner 21. 10., batch 7 add-on): what the member deposited into the treasury.
CONTRIBUTION_YANG = 'GUILD_V2_CONTRIB_YANG'
# The member's craft actions of this week after them (owner 22. 10., batch 8 G2): mining, fishing, woodcutting - the
# effort, whatever the guild material roll (Rights t1 "act <pid> <mining> <fishing> <woodcutting> ...").
ACTIONS = ('GUILD_V2_ACT_MINING', 'GUILD_V2_ACT_FISHING', 'GUILD_V2_ACT_WOOD')
# Their column headers in Příspěvky ("Ryby": "Rybaření" does not fit the column).
ACTION_HEADERS = ('GUILD_V2_ACT_MINING', 'GUILD_V2_ACT_FISHING_SHORT', 'GUILD_V2_ACT_WOOD')
# Batch 8 G4 (owner 22. 10.): one weekly EXP ceiling for the whole guild for each source - Metins and bosses, crafts, the
# active day (Doctrine t0 "xpcap <ceilings> <used>", t1 "xpsrc <pid> <metin> <craft> <activity> ...", each member's EXP).
XP_SOURCES = ('GUILD_V2_XP_METIN', 'GUILD_V2_XP_CRAFT', 'GUILD_V2_XP_ACTIVITY')
ROLES = ("Vůdce", "Rada", "Člen")
DOCTRINES = ("Bez doktríny", "Lovci příšer", "Průzkumníci")
RIGHT_NAMES = ("Správa členů a hodností", "Volba kontraktů", "Nastavení cechovního cíle",
    "Správa doktríny", "Vylepšování schopností", "Použití materiálů", "Správa pokladny",
    "Spuštění výpravy", "Schvalování rozhodnutí", "Rozšířený audit")
STATUS_TEXT = (
    "Změna byla potvrzena.", "Tato akce teď není dostupná.", "Zkontroluj zadané hodnoty.",
    "K této akci nemáš oprávnění.", "Nejsi členem cechu.", "Údaje se změnily. Obnov je a potvrď znovu.",
    "Cech nemá dostatek materiálů nebo Yangů.", "Schopnost už má nejvyšší stupeň.",
    "Probíhá jiná akce. Zkus to za chvíli.", "Čas pro tuto akci vypršel.",
    "Podmínky ještě nejsou splněny.", "Tato akce už neplatí nebo se mezitím změnila.",
    "Nic takového se nenašlo.", "Není dostatek volných míst.",
    "Spojení se obnovuje.", "Čeká se na potvrzení.")
ROMAN = ("-", "I", "II", "III", "IV", "V")
# Progression v2 (the server's guild progression policy): one passive upgrade at a time; the build of
# rank I..V takes these hours, a speed-up costs a fifth of the rank price and removes a quarter of the time, never
# below half. The server sends the running build itself (Passive t0), these numbers only describe the next one.
LEVEL_UP = 2                   # Upgrade v0 = 0, v1 = level, v2 = LEVEL_UP pays the next guild level
SPEEDUP_COST_PERCENT, SPEEDUP_PERCENT, SPEEDUP_FLOOR_PERCENT = 20, 25, 50
SPEEDUP = 1                    # Upgrade v2: speed up the passive under construction

def speedup_cost(cost):
    return (int(cost) * SPEEDUP_COST_PERCENT + 99) // 100

def hours(value):
    value = int(value)
    return "%s %s" % (value, "hodina" if value == 1 else ("hodiny" if 1 < value < 5 else "hodin"))

def _fields(text):
    """Keyword groups of a server text field ("contrib 1 stock 3 0 5 cap 22"): {keyword: (numbers, ...)};
    {} when the field holds anything else."""
    out, key = {}, None
    for part in str(text or "").split():
        if part.isascii() and part.isdecimal() and len(part) <= 19:
            if key is None:
                return {}
            out[key] = out[key] + (int(part),)
        elif part.isascii() and part.isalpha() and part not in out:
            key = part
            out[key] = ()
        else:
            return {}
    return out


def _numbers(text, prefix, count):
    """Decimal fields after a text prefix ("build 2 17... 17... 21600"); None on another server."""
    parts = str(text or "").split()
    if len(parts) != count + 1 or parts[0] != prefix:
        return None
    if not all(part.isascii() and part.isdecimal() and len(part) <= 19 for part in parts[1:]):
        return None
    return tuple(int(part) for part in parts[1:])
# Disband v0: schedule the close after the server's delay, or cancel it.
DISBAND_SCHEDULE, DISBAND_CANCEL = 0, 1
DISBAND_DELAY_HOURS = 72
DISBAND_LEADER_COOLDOWN_DAYS = 7
INVITE_DECISION = "invite-decision-v1"
# Server announces the 72 h disband (Disband v0 0 schedules, 1 cancels); older servers close at once.
DISBAND_DELAY = "disband-delay-v1"
SOLO_DISBAND = "solo-disband-v1"
# No answer within this time means the reply was lost: the server abandons a
# read after 10 s and closes the connection after a mutation's last resend.
PENDING_TIMEOUT = 15.0
PENDING_LOST = "Server neodpověděl, zkus to znovu."
POINTS_HELP = ("Osobní cechovní body získávají členové, kteří přispěli do splněného cechovního cíle, "
    "a účastníci úspěšné výpravy. Body patří členství v cechu. Po odchodu se nepřenášejí.")
PASSIVE_DESCRIPTIONS = {
    1: "Bonus k průměrnému poškození", 2: "Bonus k poškození schopností", 3: "Pevná hodnota útoku",
    4: "Zvyšuje maximální ZB", 5: "Silný proti meteorům", 6: "Síla proti příšerám",
    7: "Síla proti bossům", 8: "Síla blesku, ohně, ledu, větru, země a temnoty",
    10: "Šance získat při zabití o 30 % více zkušeností", 11: "Síla proti pololidem", 12: "Rychlost pohybu",
    13: "Více míst pro rodiny v cechu"}
PASSIVE_ICONS = {1: "glyph_damage", 2: "glyph_guide", 3: "nav_expedition_28x28",
    4: "glyph_level", 5: "passive_stone_41x41", 6: "passive_beast_41x41", 7: "passive_boss_41x41",
    8: "dragon_eye_41x41", 10: "nav_chronicle_28x28", 11: "nav_members_28x28", 12: "glyph_cooldown",
    13: "glyph_group"}
# Kapacita (owner 21. 10. 2026: the twelfth passive was missing, so a guild never grew over 20 families): the server's
# Capacity passive (share/conf/guild_v2_growth_v1.json capacity_passive id 13, members.per_capacity_rank 2). It is not
# a catalog passive: released EXEs accept exactly the 11 catalog passives in a snapshot, so the server sends its rank,
# the guild level of the next rank and its build in Balance t1 ("cap", "kap", "kapbuild") and the window adds it as
# the twelfth passive. Its ranks cost the same rank_costs as every catalog passive and are bought with Upgrade
# (13, rank, 0) like them. The places a rank adds and the largest capacity come from the server too (Balance t1
# "kapstep <places a rank> <max capacity>", members.per_capacity_rank of the growth catalog): no copy of the
# catalog numbers here (audit of hardcoded values, batch 7). Without it the window names no numbers.
CAPACITY = 13
CAPACITY_NAME = "Kapacita"

def number(value):
    return format(int(value), ",").replace(",", " ")

def short_yang(value, floor=False):
    """A guild yang amount short enough for a cost table column: "675 mil.", "13,5 mld.", "200 000" below a million.
    ``floor`` rounds down (what the guild HAS must never look like enough when it is not)."""
    value = max(0, int(value))
    for scale, suffix in ((1000000000, " mld."), (1000000, " mil.")):
        if value >= scale:
            hundredths = (value * 100 // scale) if floor else ((value * 100 + scale // 2) // scale)
            whole, part = divmod(hundredths, 100)
            return number(whole) + ("," + ("%02d" % part).rstrip("0") if part else "") + suffix
    return number(value)

def effect(identifier, value):
    if identifier == CAPACITY and value is None:
        return "více míst"
    if identifier == CAPACITY:
        return "+" + number(value) + (" místa" if 1 < value < 5 else " místo" if value == 1 else " míst")
    return "+" + number(value) + ("" if identifier in (3, 4) else "%")

def moment(epoch):
    try:
        return time.strftime("%d.%m.%Y %H:%M", time.localtime(int(epoch))) if epoch else "-"
    except (ValueError, OverflowError, OSError):
        return "-"

def last_seen(epoch, now):
    """When an offline member last played (owner 21. 10., batch 7 add-on): "před 25 min", "před 3 h", "před 1 dnem",
    "před 4 dny", the date ("12. 10. 2026") after a week; "offline" when the server did not say."""
    if not epoch:
        return "offline"
    ago = max(0, int(now) - int(epoch))
    if ago < 3600:
        return "před %d min" % max(1, ago // 60)
    if ago < 86400:
        return "před %d h" % (ago // 3600)
    if ago < 7 * 86400:
        days = ago // 86400
        return "před 1 dnem" if days == 1 else "před %d dny" % days
    try:
        t = time.localtime(int(epoch))
        return "%d. %d. %d" % (t.tm_mday, t.tm_mon, t.tm_year)
    except (ValueError, OverflowError, OSError):
        return "offline"

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
        # Public recruitment belongs to Browse, not the member snapshot.
        recruitment = self.rows(RECRUITMENT)
        same_generation = self.generation == int(payload["generation"])
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
        if (same_generation and recruitment and RECRUITMENT not in grouped
                and payload["action"] != BROWSE):
            self.sections[RECRUITMENT] = recruitment
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

    def leader_name(self):
        """Vůdce shown by the window: the leader's character name. In family mode (Capability t1 "family-v1") the
        Member row t0 is the family name and t1 the representative character, i.e. the one that founded the guild or
        took the leadership over (server DecorateFamilyMembers); an older server or a non-family guild sends only t0."""
        leader = self.member(self.row(SUMMARY)[0][0])
        if not leader:
            return "-"
        family = self.row(CAPABILITY)[2] == "family-v1"
        return leader[2] if family and leader[2] else leader[1]

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
        if identifier == CAPACITY:
            growth = self.growth()
            return growth["kap"] if growth and growth["kap"] <= 5 else 0
        return next((row[0][1] for row in self.rows(PASSIVE) if row[0][0] == identifier), 0)

    def catalog(self, identifier, rank):
        if identifier == CAPACITY:
            return self.capacity_catalog(rank)
        return next((row for row in self.rows(CATALOG) if row[0][:2] == (identifier, rank)), None)

    def capacity_catalog(self, rank):
        """A Catalog row of a Capacity rank (values: id, rank, places it adds, guild level, shards, ore, souls; the
        name; "yang N"), None on an older server. The price is the catalog's price of that rank (one rank_costs for
        every passive). The server sends only the guild level of the next rank ("kap" v1), the other ranks have 0."""
        growth = self.growth()
        if not growth or not 1 <= rank <= 5 or growth["kap"] > 5:
            return None
        price = next((row for row in self.rows(CATALOG) if row[0][1] == rank and row[0][0] != CAPACITY), None)
        if not price:
            return None
        level = growth["kap_next"] if rank == growth["kap"] + 1 else 0
        step = growth["kap_step"]
        return ((CAPACITY, rank, step[0] * rank if step else None, level) + tuple(price[0][4:]), CAPACITY_NAME, price[2])

    def description(self, identifier):
        """The description of a passive; Kapacita names the places a rank adds and the largest capacity the server
        sends ("+2 místa pro rodiny (max 30)"), without numbers on a server that does not send them."""
        growth = self.growth() if identifier == CAPACITY else None
        if growth and growth["kap_step"]:
            return effect(CAPACITY, growth["kap_step"][0]) + " pro rodiny (max " + number(growth["kap_step"][1]) + ")"
        return PASSIVE_DESCRIPTIONS.get(identifier, "")

    def building(self):
        """(passive, target rank, start, end, full seconds) of the one upgrade under construction, or None."""
        for values, title, body in self.rows(PASSIVE):
            build = _numbers(title, "build", 4)
            if build and 1 <= build[0] <= 5 and build[1] < build[2]:
                return (values[0],) + build
        # Kapacita is not a Passive row: Balance t1 "kapbuild <rank> <start> <end> <full seconds>"
        growth = self.growth()
        build = growth and growth["kap_build"]
        if build and 1 <= build[0] <= 5 and build[1] < build[2]:
            return (CAPACITY,) + tuple(build)
        return None

    def week(self):
        """Guild week (progression v2, Balance t0): dict or None on an older server."""
        data = _numbers(self.row(BALANCE)[1], "xpweek", 8)
        if not data:
            return None
        keys = ("guild", "cap", "catch_up", "end", "full", "half", "quarter", "member_cap")
        return dict(zip(keys, data))

    def contrib_level(self):
        """Lowest character level that credits the guild (Balance t1 "contrib <level> ..."), None on an older server."""
        data = _fields(self.row(BALANCE)[2]).get("contrib")
        return data[0] if data and len(data) == 1 else None

    def member_capacity(self):
        """Members the guild may have (Balance t1 "cap": base_members + the Capacity passive, server guild growth data),
        None on an older server. The window never computes it itself."""
        data = _fields(self.row(BALANCE)[2]).get("cap")
        return data[0] if data and len(data) == 1 else None

    def members_text(self, count, separator="/"):
        """"18/20" with the server capacity, only "18" when the server does not send it."""
        capacity = self.member_capacity()
        return "%s%s%s" % (count, separator, capacity) if capacity else str(count)

    def member_growth(self, pid):
        """(fish scales, guild wood) the member contributed (Balance t1 "mat <pid> <scales> <wood> ...", server
        21. 10.); (0, 0) for a member without them or on an older server."""
        data = _fields(self.row(BALANCE)[2]).get("mat") or ()
        if len(data) % 3:
            return (0, 0)
        for index in range(0, len(data), 3):
            if data[index] == pid:
                return (data[index + 1], data[index + 2])
        return (0, 0)

    def member_yang(self, pid):
        """Yang the member deposited into the treasury (Balance t0 "dep <pid> <Yang> ...", server batch 7 add-on, owner
        21. 10.); 0 for a member without deposits or on an older server."""
        data = _fields(self.row(BALANCE)[1]).get("dep") or ()
        if len(data) % 2:
            return 0
        for index in range(0, len(data), 2):
            if data[index] == pid:
                return data[index + 1]
        return 0

    def member_seen(self, pid):
        """Epoch the member last played (Rights t0 "seen <pid> <epoch> ...", server batch 7 add-on, owner 21. 10.); 0 when
        unknown or on an older server."""
        data = _fields(self.row(RIGHTS)[1]).get("seen") or ()
        if len(data) % 2:
            return 0
        for index in range(0, len(data), 2):
            if data[index] == pid:
                return data[index + 1]
        return 0

    def member_actions(self, pid):
        """(mining, fishing, woodcutting): how often the member finished a mining (also a failed one) and cut wood
        with at least the server's share of the minigame checks hit and won a fishing minigame (all goals) this week
        (owner 23. 10.) (Rights t1 "act <pid> <m> <f> <w> ...", server batch 8 G2, owner 22. 10.); (0, 0, 0)
        for a member without actions this week or on an older server."""
        data = _fields(self.row(RIGHTS)[2]).get("act") or ()
        if len(data) % 4:
            return (0, 0, 0)
        for index in range(0, len(data), 4):
            if data[index] == pid:
                return tuple(data[index + 1:index + 4])
        return (0, 0, 0)

    def xp_ceilings(self):
        """((ceilings), (used)): the guild's weekly EXP ceiling of each source (Metins, crafts, active day) and its EXP of
        this week from each (Doctrine t0 "xpcap <m> <c> <a> <m used> <c used> <a used>", server batch 8 G4: one ceiling
        for the whole guild); None on an older server."""
        data = _fields(self.row(DOCTRINE)[1]).get("xpcap") or ()
        count = len(XP_SOURCES)
        if len(data) != 2 * count:
            return None
        return tuple(data[:count]), tuple(data[count:])

    def member_xp_sources(self, pid):
        """(Metins, crafts, active day): the member's raw guild EXP of this week from each source (Doctrine t1 "xpsrc <pid>
        <m> <c> <a> ...", server batch 8 G4); (0, 0, 0) for a member without EXP this week or on an older server."""
        data = _fields(self.row(DOCTRINE)[2]).get("xpsrc") or ()
        if len(data) % 4:
            return (0, 0, 0)
        for index in range(0, len(data), 4):
            if data[index] == pid:
                return tuple(data[index + 1:index + 4])
        return (0, 0, 0)

    def member_contributions(self, row):
        """All five contributions of a Member row: shards, ore, souls (v3..v5), scales, wood."""
        values = row[0]
        return (values[3], values[4], values[5]) + self.member_growth(values[0])

    def growth(self):
        """Guild growth (Balance t1, server 13. 10.): golem cores, fish scales, guild wood in the treasury, member
        capacity, Capacity rank and the level of its next rank (0 = done), the growth materials of passive ranks
        I..V, a Capacity build (rank, start, end, full seconds) or None and the places a Capacity rank adds with the
        largest capacity ("kapstep", or None); None on an older server."""
        f = _fields(self.row(BALANCE)[2])
        stock, cap, kap, grow = f.get("stock"), f.get("cap"), f.get("kap"), f.get("rankgrow")
        if not (stock and len(stock) == 3 and cap and len(cap) == 1 and kap and len(kap) == 2 and grow and len(grow) == 15):
            return None
        build, step = f.get("kapbuild"), f.get("kapstep")
        return {"cores": stock[0], "scales": stock[1], "wood": stock[2], "capacity": cap[0], "kap": kap[0], "kap_next": kap[1],
                "rank_grow": [grow[i * 3:i * 3 + 3] for i in range(5)], "kap_build": build if build and len(build) == 4 else None,
                "kap_step": step if step and len(step) == 2 and step[0] > 0 else None}

    def levelup_growth(self):
        """Golem cores, fish scales and guild wood of the next level (Contracts t1 "levelcost c s w"), None if none."""
        data = _fields(self.row(CONTRACTS)[2]).get("levelcost")
        return data if data and len(data) == 3 else None

    def member_week(self, pid):
        """(raw, counted) guild EXP of a member this week (Member t1), (0, 0) when none."""
        member = self.member(pid)
        data = _numbers(member[2], "xp", 2) if member else None
        return data or (0, 0)

    def levelup(self):
        """Next guild level offer (Contracts t0 "levelup ..."), None at level 20 or on an older server."""
        data = _numbers(self.row(CONTRACTS)[1], "levelup", 10)
        if not data:
            return None
        keys = ("target", "exp", "metin", "ore", "soul", "yang", "group_need", "group_have", "active_need", "active_have")
        return dict(zip(keys, data))

    def level_need(self):
        """EXP of the current level's bar: the server's level-up offer (economy v3 curve), else the
        catalog step times the level (an older server)."""
        level = max(1, self.row(SUMMARY)[0][1])
        offer = self.levelup()
        if offer and offer["target"] == level + 1 and offer["exp"]:
            return offer["exp"]
        return level * (self.row(CAPABILITY)[0][6] or 1000)

    def rank_yang(self, identifier, rank):
        """Treasury Yang of a passive rank (Catalog t1 "yang N"), 0 on an older server."""
        row = self.catalog(identifier, rank)
        data = _numbers(row[2], "yang", 1) if row else None
        return data[0] if data else 0

    def week_table(self):
        """Members by this week's counted guild EXP (Member t1), best first: (place, name, counted, raw, pid)."""
        rows = []
        for values, name, body in self.rows(MEMBER):
            raw, counted = _numbers(body, "xp", 2) or (0, 0)
            rows.append((counted, raw, name, values[0]))
        rows.sort(key=lambda r: (-r[0], r[2]))
        return [(1 + sum(1 for o in rows if o[0] > r[0]), r[2], r[0], r[1], r[3]) for r in rows]

    def passive_ids(self):
        return tuple(row[0][0] for row in self.rows(PASSIVE))

    def shown_passive_ids(self):
        """The passives of the Schopnosti page: the catalog passives and Kapacita when the server sends it."""
        ids = self.passive_ids()
        return ids + (CAPACITY,) if ids and self.capacity_catalog(1) else ids

    def identity(self):
        return (self.guild, self.revision, self.generation)

    def command_identity(self, action, reviewed):
        """The identity a command from a dialog opened at ``reviewed`` is sent with: that one, or for ANY_REVISION
        the current one while the guild and the catalog are the same; None when the shown data no longer hold."""
        current = self.identity()
        if reviewed == current:
            return current
        if action in ANY_REVISION and reviewed[0] == current[0] and reviewed[2] == current[2] and current[0]:
            return current
        return None

    def capabilities(self):
        """Capability text tokens (t0 and t1, space separated); never an exact single value."""
        values, first, second = self.row(CAPABILITY)
        return set(" ".join((first or "", second or "")).split())

    def has_capability(self, token):
        return token in self.capabilities()

    def disband_at(self):
        """UTC epoch of a scheduled disband (Summary t1), 0 when none or on an older server."""
        text = str(self.row(SUMMARY)[2] or "").strip() if self.guild else ""
        return int(text) if text.isascii() and text.isdecimal() and len(text) <= 19 else 0

    def capabilities(self):
        """Capability text tokens (t0 and t1, space separated); never an exact single value."""
        values, first, second = self.row(CAPABILITY)
        return set(" ".join((first or "", second or "")).split())

    def has_capability(self, token):
        return token in self.capabilities()

    def disband_at(self):
        """UTC epoch of a scheduled disband (Summary t1), 0 when none or on an older server."""
        text = str(self.row(SUMMARY)[2] or "").strip() if self.guild else ""
        return int(text) if text.isascii() and text.isdecimal() and len(text) <= 19 else 0


class Pending:
    """The one request the window waits for, with a watchdog for a lost reply."""
    def __init__(self):
        self.action = None
        self.since = 0.0

    def __bool__(self):
        return self.action is not None

    def start(self, action, now):
        self.action, self.since = action, float(now)

    def answer(self, action):
        """True when this reply answers the waiting request (and releases it)."""
        if self.action is None or action != self.action:
            return False
        self.action = None
        return True

    def expired(self, now):
        """True once when the reply did not come in PENDING_TIMEOUT (and releases it)."""
        if self.action is None or float(now) - self.since < PENDING_TIMEOUT:
            return False
        self.action = None
        return True


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
