# -*- coding: utf-8 -*-
"""Guild cosmetics and the guild DM treasury - the client model (no UI).

Server: the guild cosmetics module. The client asks with chat
commands "/gcosm state|styles|dm <n> [1]|buy <id> <0 rent|1 permanent>|use <id>|off <kind>|log <offset> <kind> [name]" and receives CHAT_TYPE_COMMAND lines
"GuildCosmV1 ..." (game.BINARY_ServerCommand_Run hands them to ServerLine):

  ON 0|1                    the feature is open (1) or locked (0) - server event flag guild_cosmetic_enabled (owner
                            15. 10.: locked on DEV and production). Sent at login and with a refused command; a
                            client that never got "ON 1" keeps the Vzhled page and the DM part of Pokladna locked,
                            sends no /gcosm and ignores looks (an older server that does not know the switch)
  R                         forget every guild style (sent first at login)
  G gid:item.item,...       worn items of guilds - one item of every kind (frame, colour, ...) at once; "0" = none
                            (older servers sent gid:frame:color and gid:style - still read)
  S gid dm 0 role now coins schema worn   state of the own guild (role 1 leader, 2 council, 3 member, 0 none),
                            worn = "10.21" / "0"
  H created kind amount item name   one treasury history row of a /gcosm log page; HE offset more = end of the page
  I item expire             an owned style (expire 0 = permanent)
  D name dm                 a donor of the last 30 days ("-" = anonymous)
  L created kind amount item name   treasury history (kind 1 donation, 2 purchase, 3 style set, 4 GM credit)
  E                         end of a state block
  M code                    result of the last request (CODES; "locked" = locale_game GUILD_COSMETIC_SOON)

The nameplate style is drawn by the EXE (textTail.SetGuildNameStyle);
an older EXE without it simply keeps today's guild line, the pages still work.
Prices are the server's; CATALOG only shows them (both lists change together)."""
import app
import net

try:
    import builtins
except ImportError:  # Python 2 tests
    import __builtin__ as builtins

# The client replaces open() with the pack reader, which returns bytes (owner 12. 10.: the second visit of Vzhled
# stayed on "Načítání" - load_cache split bytes by a str). UserData files are read from the disk as text.
_DISK_OPEN = getattr(builtins, "old_open", builtins.open)


def _read_text(path):
    handle = _DISK_OPEN(path, "rb")
    try:
        data = handle.read()
    finally:
        handle.close()
    return data.decode("utf-8", "replace") if isinstance(data, bytes) else data

try:
    import textTail
except ImportError:  # tests
    textTail = None

PLATE_ROOT = "icon/guild_cosmetic/"

# id: (name, group, rent DM / 30 days (0 = not rented), permanent DM (0 = free), until (epoch, 0 = always), look)
# look: text colour, gradient bottom (0 none), outline, plate ("" none), plate padding, swatch colour for the UI
FREE, FRAME, COLOUR, LIMITED = "free", "frame", "colour", "limited"
CATALOG = (
    (1, "Bronzový rámeček", FREE, 0, 0, 0, (0xFFF3E6CC, 0, 0xFF1E1206, "bronze", 6, 0xFFB08850)),
    (2, "Ocelový rámeček", FREE, 0, 0, 0, (0xFFE8EEF4, 0, 0xFF0A1016, "steel", 6, 0xFF9AA6B2)),
    (3, "Krvavá žíla", FREE, 0, 0, 0, (0xFFF6E9DA, 0, 0xFF160404, "vein", 6, 0xFFD30D0E)),
    (10, "Zlatý rámeček", FRAME, 600, 2400, 0, (0xFFFFF4C8, 0xFFE39A2A, 0xFF2A1602, "gold", 7, 0xFFE8B04A)),
    (11, "Krvavý rámeček", FRAME, 600, 2400, 0, (0xFFFFE6DC, 0xFFFF5A48, 0xFF2A0000, "blood", 7, 0xFFD30D0E)),
    (12, "Mrazivý rámeček", FRAME, 600, 2400, 0, (0xFFF2FBFF, 0xFF7CC7FF, 0xFF04172B, "frost", 7, 0xFF7CC7FF)),
    (13, "Smaragdový rámeček", FRAME, 600, 2400, 0, (0xFFEFFFF2, 0xFF4FD98A, 0xFF03200F, "emerald", 7, 0xFF4FD98A)),
    (14, "Noční rámeček", FRAME, 600, 2400, 0, (0xFFF4E9FF, 0xFFB07CFF, 0xFF12051F, "night", 7, 0xFFB07CFF)),
    (15, "Královský rámeček", FRAME, 900, 3600, 0, (0xFFFFF6D6, 0xFFF0A830, 0xFF2B0B3A, "royal", 14, 0xFFF0A830)),
    (20, "Jantarová barva", COLOUR, 300, 1200, 0, (0xFFFFE2A8, 0xFFF59B23, 0xFF2B1400, "", 0, 0xFFF59B23)),
    (21, "Azurová barva", COLOUR, 300, 1200, 0, (0xFFDDF1FF, 0xFF58A8FF, 0xFF041A33, "", 0, 0xFF58A8FF)),
    (22, "Jedová barva", COLOUR, 300, 1200, 0, (0xFFEBFFDC, 0xFF7BE04A, 0xFF0B2000, "", 0, 0xFF7BE04A)),
    (23, "Růžová barva", COLOUR, 300, 1200, 0, (0xFFFFE3F0, 0xFFFF7DB8, 0xFF2A0716, "", 0, 0xFFFF7DB8)),
    (24, "Krvavá barva", COLOUR, 300, 1200, 0, (0xFFFFDCDC, 0xFFE0262A, 0xFF1A0000, "", 0, 0xFFD30D0E)),
    (30, "Dýňový rámeček", LIMITED, 0, 1500, 1793664000, (0xFFFFEBC6, 0xFFFF8A1E, 0xFF2A0E00, "pumpkin", 12, 0xFFFF8A1E)),
)
BY_ID = dict((entry[0], entry) for entry in CATALOG)
# Guild level that unlocks an item (owner KO2=C 12. 10.: basic frames 1 / 5 / 10, name colours 5 / 10 / 15 / 20);
# missing = level 1. Mirrors the server catalog field "level".
LEVELS = {2: 5, 3: 10, 20: 5, 21: 10, 22: 15, 23: 20, 24: 20}
# KO4=A: a purchase above this price waits for a second member of the leadership (/gcosm confirm | reject)
APPROVAL_PRICE = 1000
# Every catalog group belongs to one kind; a guild wears one item of every kind at once (owner 12. 10.). A new kind
# (effect, wreath, aura ...) = a new group + its kind here + the server catalog; nothing else changes.
GROUP_KIND = {FREE: "frame", FRAME: "frame", LIMITED: "frame", COLOUR: "color"}
KINDS = (("frame", "Rámeček"), ("color", "Barva"))
GROUPS = ((FREE, "Základní – zdarma"), (FRAME, "Rámečky"), (COLOUR, "Barvy"), (LIMITED, "Limitka"))
ROLES = {0: "-", 1: "Vůdce", 2: "Rada", 3: "Člen"}
LOG_KINDS = {1: "Dar DM", 2: "Nákup", 3: "Změna vzhledu", 4: "GM test", 5: "Vklad Yang"}
LOG_FILTERS = ((0, "Vše"), (1, "Dary DM"), (5, "Vklady Yang"), (2, "Nákupy"))
CODES = {
    "deposit_ok": "Dar byl připsán do pokladny cechu.",
    "buy_ok": "Koupeno a nasazeno. Celý cech ho teď nosí nad hlavou.",
    "use_ok": "Vzhled cechu změněn.",
    "not_member": "Nejsi v cechu.",
    "leader_only": "Utrácet z pokladny a měnit vzhled smí jen vůdce cechu.",
    "amount": "Zadej 10 až 50 000 DM.",
    "busy": "Chvilku počkej a zkus to znovu.",
    "coins": "Nemáš tolik dračích mincí.",
    "balance": "V pokladně cechu není dost DM.",
    "owned": "Tenhle vzhled už cech vlastní natrvalo.",
    "not_owned": "Tenhle vzhled cech nevlastní.",
    "sold_out": "Limitovaná edice už skončila.",
    "item": "Tahle položka se nedá koupit.",
    "unavailable": "Pokladna cechu teď není dostupná.",
    "level": "Cech na to ještě nemá úroveň.",
    "pending": "Nákup nad 1 000 DM čeká, až ho potvrdí druhý člen vedení.",
    "pending_cancelled": "Čekající nákup zrušen.",
    "pending_expired": "Čekající nákup vypršel nebo už se neprodává.",
    "no_pending": "Žádný nákup nečeká na potvrzení.",
    "second_member": "Svůj vlastní nákup potvrdit nemůžeš, musí druhý člen vedení.",
    "leadership_only": "Potvrdit nebo zamítnout může jen vůdce nebo Rada.",
    "usage": "Neznámý příkaz pokladny.",
}
DONATE_STEPS = (50, 100, 500, 1000)
# Guild window pages that stay locked ("Připravujeme") until the server says "ON 1"; Pokladna stays open for the Yang
# of Guild v2 and locks only its DM part.
LOCKED_PAGES = ("vzhled",)


def soon_text():
    """The short "coming soon" text of the locked guild looks: locale_game GUILD_COSMETIC_SOON ("" when missing)."""
    try:
        import localeInfo
        return getattr(localeInfo, "GUILD_COSMETIC_SOON", "") or ""
    except Exception:
        return ""


def page_locked(key):
    """A guild window page of the looks that is locked because the server has not opened the feature."""
    return key in LOCKED_PAGES and not MODEL.enabled


def name(item):
    entry = BY_ID.get(item)
    return entry[1] if entry else "Výchozí"


def level(item):
    return LEVELS.get(int(item), 1)


def kind(item):
    entry = BY_ID.get(int(item))
    return GROUP_KIND.get(entry[2]) if entry else None


def is_colour(item):
    return kind(item) == "color"


def combined(items):
    """The nameplate look of the worn items: the plate of the frame, the text colours of the name colour (or of the
    frame when no colour is worn). Kinds the nameplate does not draw are ignored. None = engine default."""
    by_kind = dict((kind(item), item) for item in items if kind(item))
    f, c = look(by_kind.get("frame", 0)), look(by_kind.get("color", 0))
    if not f and not c:
        return None
    if f and c:
        return (c[0], c[1], c[2], f[3], f[4], c[5])
    return f or c


def parse_items(text):
    """ "10.21" -> (10, 21); "0" / "" -> ()."""
    items = []
    for part in str(text).replace(":", ".").split("."):
        if part.isdigit() and int(part):
            items.append(int(part))
    return tuple(sorted(items))


def price_text(value):
    text = "{:,}".format(int(value)).replace(",", ".")
    return text + " DM"


class Model(object):
    """State of the own guild plus the styles of every guild this client has seen."""

    def __init__(self):
        self.styles = {}            # gid -> worn item ids
        self.listeners = []
        self.enabled = False        # "ON 1" from the server; nothing from it = locked
        self.reset_state()

    def reset_state(self):
        self.guild = 0
        self.dm = 0
        self.worn_items = ()        # worn items of the own guild, one per kind
        self.role = 0
        self.server_now = 0
        self.client_at = 0.0
        self.coins = 0
        self.schema = False
        self.loaded = False
        self.owned = {}              # item -> expire (0 permanent)
        self.donors = []
        self.message = ""
        self.history = []           # loaded treasury history rows (created, kind, amount, item, name)
        self.history_more = False
        self.history_filter = (0, "")
        self.history_wanted = None
        self.guild_level = 0
        self.pending = None          # (item, permanent, price, requester pid, requester name, created) or None
        self._block = None

    # ---------------------------------------------------------------- queries
    def now(self):
        if not self.server_now:
            return 0
        return self.server_now + int(app.GetTime() - self.client_at)

    def owns(self, item):
        entry = BY_ID.get(item)
        if not entry:
            return item == 0
        if entry[2] == FREE:
            return True
        if item not in self.owned:
            return False
        expire = self.owned[item]
        return expire == 0 or expire > self.now()

    def available(self, item):
        entry = BY_ID.get(item)
        return bool(entry) and (not entry[5] or self.now() < entry[5])

    def leader(self):
        return self.role == 1

    # ---------------------------------------------------------------- requests
    def send(self, command):
        """Every /gcosm request; nothing while the feature is locked."""
        if self.enabled:
            net.SendChatPacket(command)

    def request_state(self):
        self.send("/gcosm state")

    def donate(self, amount, anonymous=False):
        self.send("/gcosm dm %d %d" % (int(amount), 1 if anonymous else 0))

    def buy(self, item, permanent):
        self.send("/gcosm buy %d %d" % (int(item), 1 if permanent else 0))

    def use(self, item):
        self.send("/gcosm use %d" % int(item))

    def take_off(self, kind_):
        self.send("/gcosm off %s" % kind_)

    def worn(self, item):
        return bool(item) and item in self.worn_items

    def unlocked(self, item):
        return self.guild_level >= level(item)

    def confirm(self):
        self.send("/gcosm confirm")

    def reject(self):
        self.send("/gcosm reject")

    def worn_of(self, kind_):
        return next((item for item in self.worn_items if kind(item) == kind_), 0)

    def request_history(self, more=False, kind_=None, name=None):
        """First page (or the next with ``more``) of the treasury history under the filter."""
        if kind_ is not None or name is not None:
            self.history_filter = (self.history_filter[0] if kind_ is None else int(kind_),
                self.history_filter[1] if name is None else name)
        offset = len(self.history) if more else 0
        clean = "".join(c for c in self.history_filter[1] if c.isalnum() or c == "_")[:24]
        self.history_wanted = (offset, self.history_filter)
        self.send("/gcosm log %d %d %s" % (offset, self.history_filter[0], clean or "-"))

    # ---------------------------------------------------------------- wire
    def line(self, tokens):
        if not tokens:
            return
        kind, args = tokens[0], tokens[1:]
        try:
            if kind == "ON":
                self.enabled = bool(int(args[0]))
                if not self.enabled:
                    # locked: no look on any nameplate, none remembered for the character select hall
                    self.styles = {}
                    apply_all({})
                    forget_cache()
                    self.reset_state()
                self.notify()
            elif kind == "R":
                self.styles = {}
                apply_all({})
            elif kind == "G" and not self.enabled:
                pass                    # an older server without the switch: the looks stay locked
            elif kind == "G":
                changed = {}
                for pair in " ".join(args).split(","):
                    if ":" in pair:
                        gid, items = pair.split(":", 1)
                        changed[int(gid)] = parse_items(items)
                for gid, items in changed.items():
                    if items:
                        self.styles[gid] = items
                    else:
                        self.styles.pop(gid, None)
                save_cache(self.styles)
                apply_styles(changed)
            elif kind == "S":
                block = {"owned": {}, "donors": []}
                values = [int(value) for value in args[:7]]
                values += [0] * (7 - len(values))
                values.append(parse_items(args[7]) if len(args) > 7 else parse_items(args[2] if len(args) > 2 else ""))
                block["head"] = values
                self._block = block
            elif kind == "P" and self._block is not None:
                values = [int(value) for value in args[:4]]
                self._block["pending"] = tuple(values + [args[4] if len(args) > 4 else "-",
                    int(args[5]) if len(args) > 5 else 0])
            elif kind == "V" and self._block is not None:
                self._block["level"] = int(args[0])
            elif kind == "I" and self._block is not None:
                self._block["owned"][int(args[0])] = int(args[1])
            elif kind == "D" and self._block is not None:
                self._block["donors"].append(("Anonym" if args[0] == "-" else args[0], int(args[1])))
            elif kind == "H":
                created, what, amount, item = [int(value) for value in args[:4]]
                who = args[4] if len(args) > 4 else "-"
                self._history_page = getattr(self, "_history_page", [])
                self._history_page.append((created, what, amount, item, "Anonym" if who == "-" else who))
            elif kind == "HE":
                offset, more = int(args[0]), bool(int(args[1]))
                page, self._history_page = getattr(self, "_history_page", []), []
                self.history = (self.history[:offset] if offset else []) + page
                self.history_more = more
                self.history_wanted = None
                self.notify()
            elif kind == "E" and self._block is not None:
                gid, dm, unused, role, now, coins, schema, worn = self._block["head"]
                self.guild, self.dm, self.worn_items, self.role = gid, dm, worn, role
                self.server_now, self.client_at, self.coins, self.schema = now, app.GetTime(), coins, bool(schema)
                self.owned = self._block["owned"]
                self.donors = self._block["donors"]
                self.pending = self._block.get("pending")
                self.guild_level = self._block.get("level", 99)       # an older server: no gates
                self.loaded = True
                self._block = None
                if gid:
                    self.styles[gid] = worn
                    save_cache(self.styles)
                self.notify()
            elif kind == "M":
                code = args[0] if args else ""
                self.message = soon_text() if code == "locked" else CODES.get(code, "")
                self.notify()
        except (ValueError, IndexError):
            self._block = None

    def notify(self):
        for listener in list(self.listeners):
            try:
                listener()
            except Exception:
                import dbg
                dbg.TraceError("guildcosmetic listener failed")


MODEL = Model()


def supported():
    return textTail is not None and hasattr(textTail, "SetGuildNameStyle")


def look(item):
    entry = BY_ID.get(item)
    return entry[6] if entry else None


def apply_style(gid, items):
    if not supported():
        return
    items = items if isinstance(items, tuple) else parse_items(items)
    data = combined(items)
    if not data:
        textTail.ClearGuildNameStyle(gid)
        return
    color, gradient, outline, plate, pad, swatch = data
    tune = TUNING.get("all", {}).copy()
    for item in items:
        tune.update(TUNING.get(str(item), {}))
    color = tune.get("color", color)
    gradient = tune.get("gradient", gradient)
    outline = tune.get("outline", outline)
    pad = int(tune.get("pad", pad))
    plate = tune.get("plate", plate)
    textTail.SetGuildNameStyle(gid, color, gradient, outline, "", "", PLATE_ROOT + plate if plate else "", pad,
        int(tune.get("offset_y", 0)), float(tune.get("alpha", 1.0)))


# Quick tuning of the nameplate without a new pack (owner: "nevypadá moc dobře"): an optional file
# UserData/guildcosmetic_tuning.txt, one line per key: "<item id|all> <field>=<value> ...", fields color, gradient,
# outline (0xAARRGGBB), pad, offset_y (px), alpha (0-1), plate (texture name). Read when the Vzhled page opens
# (ReloadTuning) and at the first style; a missing or broken file changes nothing.
TUNING_FILE = "UserData/guildcosmetic_tuning.txt"
TUNING = {}


def parse_tuning(text):
    tuning = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        key, fields = parts[0], {}
        for part in parts[1:]:
            if "=" not in part:
                continue
            name, value = part.split("=", 1)
            try:
                if name in ("color", "gradient", "outline"):
                    fields[name] = int(value, 16)
                elif name in ("pad", "offset_y"):
                    fields[name] = int(value)
                elif name == "alpha":
                    fields[name] = float(value)
                elif name == "plate":
                    fields[name] = value
            except ValueError:
                pass
        tuning[key] = fields
    return tuning


def ReloadTuning():
    global TUNING
    try:
        TUNING = parse_tuning(_read_text(TUNING_FILE))
    except Exception:      # missing or broken file: no tuning
        TUNING = {}
    apply_all(MODEL.styles)


def apply_styles(changed):
    for gid, pair in changed.items():
        apply_style(gid, pair)


def apply_all(styles):
    if supported():
        textTail.ClearGuildNameStyles()
    apply_styles(styles)


def ServerLine(line):
    """game.BINARY_ServerCommand_Run: one "GuildCosmV1 ..." line."""
    tokens = line.split()
    if tokens and tokens[0] == "GuildCosmV1":
        MODEL.line(tokens[1:])
        return True
    return False


# ---------------------------------------------------------------------------------------------------------------------
# Pregame (character select hall): the hall has no game connection and the character list carries only the
# guild NAME, so the client remembers the worn items of guilds it saw in game by name: UserData/guildcosmetic_cache.txt,
# "name<TAB>10.21" per line. The hall draws the same plate and colour from it (uipregamehall). Updated whenever styles
# arrive in game; a guild never seen keeps the plain line.
CACHE_FILE = "UserData/guildcosmetic_cache.txt"
_cache_written = None


def _guild_name(gid):
    try:
        import guild
        return guild.GetGuildName(int(gid)) or ""
    except Exception:
        return ""


def save_cache(styles):
    global _cache_written
    cache = load_cache()
    for gid, items in styles.items():
        name = _guild_name(gid).strip()
        if name and "\t" not in name and "\n" not in name:
            cache[name] = tuple(items)
    lines = sorted("%s\t%s" % (name, ".".join(str(i) for i in items) or "0") for name, items in cache.items())
    text = "\n".join(lines[:200]) + "\n"
    if text == _cache_written:
        return
    try:
        handle = _DISK_OPEN(CACHE_FILE, "wb")
        try:
            handle.write(text.encode("utf-8") if not isinstance(text, bytes) else text)
        finally:
            handle.close()
        _cache_written = text
    except Exception:      # the cache only helps the character select hall; never break the guild window
        pass


def forget_cache():
    """The looks are locked: the character select hall shows no remembered look either."""
    global _cache_written
    try:
        handle = _DISK_OPEN(CACHE_FILE, "wb")
        try:
            handle.write(b"")
        finally:
            handle.close()
        _cache_written = ""
    except Exception:      # the cache only helps the character select hall; never break the guild window
        pass


def load_cache():
    cache = {}
    try:
        for line in _read_text(CACHE_FILE).splitlines():
            if "\t" in line:
                name, items = line.split("\t", 1)
                cache[name] = parse_items(items)
    except Exception:      # missing or broken cache: start empty
        pass
    return cache


def cached_look(guild_name):
    """(text colour, gradient, outline, plate, pad, swatch) for a guild name from the cache, or None."""
    items = load_cache().get((guild_name or "").strip())
    return combined(items) if items else None
