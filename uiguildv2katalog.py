# -*- coding: utf-8 -*-
"""Guild catalogue v1 and the guild diary (Deník) of the R1 guild window (owner 12. 10. 2026: variant K2 "Karty" and
D1 "Deník").

Without a guild the side panel lists Katalog cechů, Moje žádosti and Pozvánky; the catalogue shows the recruiting
guilds (Guild V2 Browse) as cards, two in a row; a card opens the profile with "Požádat o vstup". The leader and
the council see the applications under Členové -> Žádosti and accept (the ordinary Invite; the applicant's client
confirms it on its own) or decline them. Správa -> Nábor edits the recruiting profile: focus and play time
are kept in the first line of the profile text ("#nabor z=pve,hardcore c=vecery"), so the server needs no new
profile columns.

Today's client EXE only knows Guild V2 actions 1-28 and sections 1-25, so the applications travel as the chat command
/guild_app and the server command GuildAppV1; every text is hex of
UTF-8. GuildWindow mixes KatalogPages in; uiguildv2r1 calls these pages only in the R1 look."""
import app
import chat
import fontconfig
import localeInfo
import net
import ui

import guildv2model as m
import uiguildv2widgets as widgets
from uiguildv2widgets import (Canvas, Flat, INK, DIM, GOLD, GREEN, MUTED, ROLE_CAPTION, px, span)
try:
    from marketfilters import folded
except Exception:          # the tests and an old pack: plain lower case
    def folded(text):
        return str(text).lower()

ROW = 36
# Profile tags (first line of the recruiting profile text).
TAG = "#nabor"
# Focus tags: how the guild plays (owner 12. 10. 2026: no language, the server is CZ/SK only; no Portály/Sběr).
FOCUS = (("pve", "PvE"), ("pvp", "PvP"), ("pohoda", "Pohodový"), ("hardcore", "Hardcore"),
    ("zebricek", "Žebříček"), ("novacci", "Nováčci"))
FOCUS_HINTS = {
    "pve": "Metiny, bossové a dungeony.",
    "pvp": "Souboje, arény a války cechů.",
    "pohoda": "Hrajeme v klidu, bez povinností a tlaku.",
    "hardcore": "Hrajeme hodně a od členů čekáme aktivitu.",
    "zebricek": "Jdeme po předních místech žebříčků a rekordech.",
    "novacci": "Rádi vezmeme a naučíme začátečníky.",
}
# Short passive names for one diary line ("Vylepšeno: Průměrná škoda II"); the full names stay in Schopnosti.
PASSIVE_SHORT = {1: "Průměrná škoda", 2: "Poškození schopností", 3: "Útok", 4: "Max. ZB", 5: "Proti meteorům",
    6: "Proti příšerám", 7: "Proti bossům", 8: "Síla živlů", 10: "Bonus EXP", 11: "Proti pololidem",
    12: "Rychlost pohybu"}
ELLIPSIS = "…"
CATALOG_REFRESH = 30.0      # seconds: the open catalogue asks the server again (the server caches a page 5 s)
TIMES = (("vecery", "večery"), ("vikendy", "víkendy"), ("cely", "celý den"))
FOCUS_MAX = 3
MESSAGE_BYTES = 120
APPLICATIONS_MAX = 3
VALID_HOURS = 72
JOBS = ("Válečník", "Ninja", "Sura", "Šaman", "Lycan")
# GuildAppV1 res codes (server Code enum) as Czech messages.
RESULT_TEXT = {
    1: "Už jsi členem cechu.",
    2: "Tento cech teď nenabírá.",
    3: "Na tento cech nemáš ještě dost vysokou úroveň.",
    4: "Můžeš mít nejvýš 3 žádosti naráz. Nějakou zruš v Moje žádosti.",
    5: "Stejnému cechu můžeš znovu napsat až 24 hodin po poslední žádosti.",
    6: "Po odchodu z cechu můžeš do jiného až za 24 hodin.",
    7: "Zpráva je moc dlouhá nebo obsahuje nepovolený znak.",
    8: "Žádosti vyřizuje vůdce a Rada.",
    9: "Cech už neexistuje nebo žádost už neplatí.",
    10: "Server neodpověděl, zkus to znovu.",
    11: "Tomuto cechu už žádost posíláš.",
}
STATE_TEXT = ("Čeká na vyřízení", "Přijata", "Odmítnuta", "Zrušena", "Uzavřena")
DIARY_FILTERS = (("all", "Vše"), ("members", "Členové"), ("leaders", "Vedení"), ("guild", "Cech"))
DIARY_KIND = {4: "guild", 5: "guild", 6: "guild", 129: "guild", 11: "members", 12: "members", 13: "members",
    8: "leaders", 14: "leaders", 15: "leaders", 20: "leaders", 21: "leaders"}
BADGE = "d:/ymir work/ui/public/althea_r1_lista/badge/"


# ---------------------------------------------------------------------------------------------------- pure helpers
def to_hex(text):
    if not text:
        return "-"
    data = text if isinstance(text, bytes) else str(text).encode("utf-8")
    return "".join("%02X" % value for value in bytearray(data))


def from_hex(text):
    if not text or text == "-" or len(text) % 2:
        return ""
    try:
        data = bytes(bytearray(int(text[i:i + 2], 16) for i in range(0, len(text), 2)))
    except ValueError:
        return ""
    if str is bytes:            # Python 2: the client works in UTF-8 byte strings
        return data
    return data.decode("utf-8", "replace")


def utf8_len(text):
    return len(text if isinstance(text, bytes) else str(text).encode("utf-8"))


def clean_message(text):
    """The message of an application: one line, no '|' (link syntax), at most MESSAGE_BYTES of UTF-8."""
    text = str(text).replace("\r", " ").replace("\n", " ").strip()
    if "|" in text or utf8_len(text) > MESSAGE_BYTES:
        return None
    return text


def parse_profile(body):
    """(tags, description) of a recruiting profile text. tags = {"z": [...], "j": "cz", "c": "vecery"}."""
    body = str(body or "")
    tags = {"z": [], "j": "", "c": ""}
    if not body.startswith(TAG):
        return tags, body
    first, _, rest = body.partition("\n")
    for part in first[len(TAG):].split():
        key, _, value = part.partition("=")
        if key == "z":
            known = [code for code, label in FOCUS]
            tags["z"] = [code for code in value.split(",") if code in known][:FOCUS_MAX]
        elif key == "c" and value in [code for code, label in TIMES]:
            tags["c"] = value
    return tags, rest


def build_profile(tags, description):
    parts = []
    if tags.get("z"):
        parts.append("z=" + ",".join(tags["z"][:FOCUS_MAX]))
    if tags.get("c"):
        parts.append("c=" + tags["c"])
    description = str(description or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not parts:
        return description
    return TAG + " " + " ".join(parts) + ("\n" + description if description else "")


def label(pairs, code):
    return next((text for key, text in pairs if key == code), "")


def ago(seconds):
    seconds = max(0, int(seconds))
    if seconds < 3600:
        return "před %d min" % max(1, seconds // 60)
    if seconds < 86400:
        return "před %d h" % (seconds // 3600)
    return "před %d d" % (seconds // 86400)


def catalog_rows(rows, query="", focus="", level_ok=0, free_only=False):
    """The recruiting guilds after the filters, active-looking first: by members, and the first places alternate a big
    and a small (level <= 2 or < 10 members) guild so a new guild is not always at the bottom."""
    result = []
    for row in rows:
        v, name, body = row
        tags, text = parse_profile(body)
        if query and query not in folded(name):
            continue
        if focus and focus not in tags["z"]:
            continue
        if level_ok and v[3] > level_ok:
            continue
        # free_only: the server lists only guilds with a free place (its capacity follows the guild's Capacity
        # passive, which the client does not know), so every listed guild has room.
        result.append(row)
    result.sort(key=lambda row: (-row[0][2], -row[0][1], row[1]))
    small = [row for row in result if row[0][1] <= 2 or row[0][2] < 10]
    big = [row for row in result if row not in small]
    mixed = []
    while (big or small) and len(mixed) < 6:
        if big:
            mixed.append(big.pop(0))
        if small:
            mixed.append(small.pop(0))
    return mixed + big + small


def diary_sentence(values, actor, text, member_name):
    """(kind, sentence) of a Chronicle row (Deník); None for a row the diary does not show. A declined invitation
    (action 11, command v1 = 1) is shown, too (owner 19. 10.: the diary says who declined and goes on).
    values = (id, actor pid, action, revision, created, command v0, command v1). The sentences avoid Czech past
    tense gender ("Nový člen: Lucka", not "Lucka vstoupila")."""
    action, first, second = values[2], values[5], values[6]
    kind = DIARY_KIND.get(action)
    if not kind:
        return None
    target = member_name(first) or "člen"
    if action == 11:
        return kind, (localeInfo.GUILD_V2_DIARY_INVITE_DECLINED % actor) if second == 1 else "Nový člen: %s" % actor
    if action == 12:
        return kind, "Odchod z cechu: %s" % actor
    if action == 13:
        return kind, "Vyloučení člena: %s (rozhodl/a %s)" % (target, actor)
    if action == 8:
        role = m.ROLES[second] if second < len(m.ROLES) else "-"
        return kind, "Nová hodnost: %s je %s" % (target, role)
    if action == 14:
        return kind, "Předání vedení: novým vůdcem je %s" % target
    if action == 15:
        return kind, "Rozpuštění cechu zrušeno (%s)" % actor if first == m.DISBAND_CANCEL else \
            "Naplánováno rozpuštění cechu (%s)" % actor
    if action == 4:
        return kind, "Cech založen (%s)" % actor
    if action == 5:
        # Upgrade v0 passive, v1 current rank, v2 0 start / 1 speed-up / 2 guild level-up (progression v2); the
        # server puts v2 into the row text (owner 12. 10.: a start and two speed-ups read as the same upgrade 3x).
        rank = m.ROMAN[min(5, second + 1)] if second < 5 else ""
        name = ("%s %s" % (PASSIVE_SHORT.get(first, "schopnost cechu"), rank)).strip()
        step = (text or "").strip()
        if step == "2":
            return kind, "Povýšení cechu na úroveň %d" % (second + 1)
        if step == "1":
            return kind, "Urychleno vylepšení: %s" % name
        if step == "0":
            return kind, "Zahájeno vylepšení: %s" % name
        return kind, "Vylepšeno: %s" % name
    if action == 6:
        return kind, "Nový cíl cechu: %s" % (text or "cíl")
    if action == 20:
        return kind, "Návrh doktríny (%s)" % actor
    if action == 21:
        return kind, "Rozhodnutí vedení (%s)" % actor
    if action == 129:
        return kind, "Výprava cechu dokončena"
    return None


def when(epoch, now):
    """Short time of a diary row: "dnes 21:14", "včera 19:02" or "12.10. 18:00"."""
    import time
    try:
        stamp = time.localtime(int(epoch))
        today = time.localtime(int(now))
    except (ValueError, OverflowError, OSError):
        return "-"
    clock = "%02d:%02d" % (stamp.tm_hour, stamp.tm_min)
    days = (time.mktime((today.tm_year, today.tm_mon, today.tm_mday, 0, 0, 0, 0, 0, -1)) -
        time.mktime((stamp.tm_year, stamp.tm_mon, stamp.tm_mday, 0, 0, 0, 0, 0, -1))) // 86400
    if days <= 0:
        return "dnes " + clock
    if days == 1:
        return "včera " + clock
    return "%d.%d. %s" % (stamp.tm_mday, stamp.tm_mon, clock)


# ---------------------------------------------------------------------------------------------------- applications
class Applications(object):
    """Presentation state of the applications (server command GuildAppV1) and the queue of /guild_app commands (the
    server admits one per 400 ms and player)."""
    INTERVAL = 0.6

    def __init__(self, send=None, clock=None):
        self.send_chat = send or send_chat
        self.clock = clock or app.GetTime
        self.mine = []              # (guild, state, age seconds at receipt, guild name, received at)
        self.guild_rows = []        # (pid, level, job, age, name, family, message, received at)
        self.mine_loaded = self.list_loaded = False
        self.queue = []
        self.last = -10.0
        self.incoming_mine = None
        self.incoming_list = None
        self.accepted = set()       # invitations already confirmed automatically
        self.last_result = None

    def command(self, text):
        if text not in self.queue:
            self.queue.append(text)
        self.tick()

    def tick(self):
        now = self.clock()
        if self.queue and now - self.last >= self.INTERVAL:
            self.last = now
            self.send_chat(self.queue.pop(0))

    # requests
    def apply(self, guild, message):
        self.command("/guild_app apply %d %s" % (int(guild), to_hex(message)))

    def cancel(self, guild=0):
        self.command("/guild_app cancel %d" % int(guild))

    def refresh_mine(self):
        self.command("/guild_app mine")

    def refresh_list(self):
        self.command("/guild_app list")

    def decide(self, pid, accept):
        self.command("/guild_app decide %d %d" % (int(pid), 1 if accept else 0))

    # state
    def pending(self):
        return [row for row in self.mine if row[1] == 0]

    def state_of(self, guild):
        """The state of the newest application to this guild (None = none in the last 72 h)."""
        return next((row[1] for row in self.mine if row[0] == guild), None)

    def wants(self, guild):
        """True when an invitation of this guild answers an application (pending or accepted)."""
        return self.state_of(guild) in (0, 1)

    def receive(self, args):
        """One GuildAppV1 line; returns what changed: "mine", "list", "result", "new", "decided" or None."""
        if not args:
            return None
        kind, rest = args[0], list(args[1:])
        now = self.clock()

        def number(index):
            try:
                return int(rest[index])
            except (IndexError, ValueError):
                return 0
        if kind == "mine_begin":
            self.incoming_mine = []
        elif kind == "mine" and self.incoming_mine is not None:
            self.incoming_mine.append((number(0), number(1), number(2), from_hex(rest[3] if len(rest) > 3 else ""), now))
        elif kind == "mine_end" and self.incoming_mine is not None:
            self.mine, self.incoming_mine, self.mine_loaded = self.incoming_mine, None, True
            return "mine"
        elif kind == "list_begin":
            self.incoming_list = []
        elif kind == "app" and self.incoming_list is not None:
            text = lambda index: from_hex(rest[index]) if len(rest) > index else ""
            self.incoming_list.append((number(0), number(1), number(2), number(3), text(4), text(5), text(6), now))
        elif kind == "list_end" and self.incoming_list is not None:
            self.guild_rows, self.incoming_list, self.list_loaded = self.incoming_list, None, True
            return "list"
        elif kind == "res":
            self.last_result = (rest[0] if rest else "", number(1), number(2))
            return "result"
        elif kind == "new":
            self.refresh_list()
            return "new"
        elif kind == "decided":
            self.refresh_mine()
            return "decided"
        return None

    def result_text(self):
        what, code, guild = self.last_result or ("", 0, 0)
        if code == 0:
            return {"apply": "Žádost byla odeslána. Vedení cechu ji uvidí v okně cechu.",
                "cancel": "Žádost byla zrušena.", "decide": ""}.get(what, "")
        return RESULT_TEXT.get(code, "Akce se nepovedla.")


# ---------------------------------------------------------------------------------------------------- pages
class KatalogPages(object):
    """Methods of the R1 guild window; ``self`` is the GuildWindow."""

    def katalog_init(self):
        self.apps = Applications()
        self.no_guild_page = "catalog"
        self.catalog_focus = ""
        self.catalog_level_ok = True
        self.catalog_free = False
        self.members_view = "list"
        self.diary_filter = "all"
        self.diary_revision = None
        self.accepting = None       # (pid, name) of the application whose Invite is on its way
        self.was_member = None
        self.apps_session = False
        self.browsed_at = -CATALOG_REFRESH

    # ------------------------------------------------------------------ server command
    def ApplicationCommand(self, args):
        changed = self.apps.receive(args)
        if changed == "result":
            text = self.apps.result_text()
            what, code, guild = self.apps.last_result
            if text:
                self.message(text, GREEN if code == 0 else widgets.RED)
                if what == "apply" or code:
                    chat.AppendChat(chat.CHAT_TYPE_INFO, text)
        elif changed == "decided":
            pass
        if changed and self.IsShow():
            self.render()
        else:
            self.stale = True

    def katalog_tick(self):
        """Every frame (UpdateInvitations): the command queue, the first applications read and the automatic
        confirmation of an invitation that answers an application."""
        apps = self.apps
        apps.tick()
        if not widgets_ready(self):
            return
        guild = self.model.guild
        if guild and widgets.R1 and self.IsShow() and not self.pending and self.currentPage == "overview" and \
                self.diary_revision != self.model.revision and app.GetTime() - self.pending_since > 1.0:
            # Přehled shows the newest diary rows: one read per revision, a moment after the snapshot.
            self.diary_revision = self.model.revision
            self.history(5)
            return
        if self.was_member is not None and not self.was_member and guild and apps.pending():
            apps.cancel(0)              # joined a guild: the other applications close
        self.was_member = bool(guild)
        if not self.apps_session:
            self.apps_session = True
            if guild:
                if self.leadership():
                    apps.refresh_list()
            else:
                apps.refresh_mine()
        if not guild and self.IsShow() and self.no_guild_page == "catalog" and not self.pending and \
                app.GetTime() - self.browsed_at >= CATALOG_REFRESH and self.invitation_requested is None and \
                not self.snapshot_wanted and not self.catalog_wanted:
            # The open catalogue follows the recruiting guilds on its own (a changed profile within 30 s).
            self.browsed_at = app.GetTime()
            self.request(m.BROWSE)
            return
        if guild or self.pending or not apps.mine_loaded:
            return
        now = self.model.now(app.GetTime())
        for values, name, body in self.model.rows(m.INVITATION):
            identifier, inviting = values[0], values[1]
            if values[2] > now and identifier not in apps.accepted and apps.wants(inviting):
                apps.accepted.add(identifier)
                m.invitation_notices.shown(identifier)
                if self.request(m.ACCEPT_INVITE, (identifier, 0)):
                    chat.AppendChat(chat.CHAT_TYPE_INFO, "Cech %s přijal tvoji žádost. Vstupuješ do cechu." % name)
                return

    def leadership(self):
        me = self.model.member(self.pid())
        return bool(me) and me[0][1] <= 1

    def katalog_open(self):
        """Every opening of the window reads the catalogue again (it was read once per session before)."""
        self.browsed = False
        self.browsed_at = -CATALOG_REFRESH

    def katalog_after_receive(self, action, status, matched):
        """After a Guild V2 reply: the Invite of an accepted application marks it accepted; a fresh snapshot of the
        overview or the diary loads the diary page once per revision."""
        if action == m.BROWSE and status == m.OK:
            self.browsed_at = app.GetTime()
        if matched and action == m.INVITE and self.accepting:
            pid, name = self.accepting
            self.accepting = None
            if status == m.OK:
                self.apps.decide(pid, True)
                chat.AppendChat(chat.CHAT_TYPE_INFO, "Žádost hráče %s přijata, pozvánka odeslána." % name)

    # ------------------------------------------------------------------ side panel without a guild
    def sidebar_no_guild_r1(self, bar, w, loaded):
        bar.keep(widgets.uir1.Frame(bar, px(16) - 2, px(14) - 2, 36, 32, "panel"))
        bar.text(16 + 52, 14, "Bez cechu" if loaded else "Cech", w - 16 - 60, GOLD, fontconfig.ROLE_WINDOW_TITLE)
        fitted_text(bar, 16 + 52, 42, "Najdi nebo založ cech.", w - 16 - 60, DIM, ROLE_CAPTION)
        bar.rule(16, 76, w - 32)
        now = self.model.now(app.GetTime())
        invitations = sum(1 for row in self.model.rows(m.INVITATION) if row[0][2] > now)
        pages = (("catalog", "Katalog cechů", "nav_overview_28x28", 0),
            ("mine", "Moje žádosti", "nav_chronicle_28x28", len(self.apps.pending())),
            ("invites", "Pozvánky", "nav_members_28x28", invitations))
        y = 84
        for key, text, icon, count in pages:
            bar.keep(Flat(bar, px(6), px(y), span(6, w - 12), span(y, ROW + 2), lambda k=key: self.select_no_guild(k),
                text, "plain", self.no_guild_page == key, True, px(16 + 34), fontconfig.ROLE_CONTROL, accent=True))
            image = bar.image(icon, 16, y + 5, 28, 28)
            image.SetAlpha(1.0 if self.no_guild_page == key else 0.75)
            if count:
                badge(bar, px(w - 16) - 19, px(y + 12), count)
            y += ROW + 4
            bar.rule(16, y - 2, w - 32, 0xff1e1c1d)

    def select_no_guild(self, key):
        self.no_guild_page = key
        if key == "catalog" and not self.pending:
            self.request(m.BROWSE)
        if key == "mine":
            self.apps.refresh_mine()
        self.render()

    def without_guild_katalog_r1(self, w):
        page = self.no_guild_page
        if page == "mine":
            self.band_r1("Moje žádosti", "nejvýš %d naráz, platí %d h" % (APPLICATIONS_MAX, VALID_HOURS))
            return self.page_mine_r1(w)
        if page == "invites":
            self.band_r1("Pozvánky", "")
            return self.without_guild_r1(w)
        records = self.model.rows(m.RECRUITMENT)
        self.band_r1("Katalog cechů", ("%d nabírá" % len(records)) if self.browsed else "")
        self.page_catalog_r1(w)

    # ------------------------------------------------------------------ Katalog (K1: list and detail)
    def page_catalog_r1(self, w):
        if not self.browsed and not self.pending and not self.catalog_wanted and not self.snapshot_wanted and \
                self.invitation_requested is None:
            self.request(m.BROWSE)
        self.search_field("catalog", 0, 0, 230)
        self.page.checkbox(250, 8, self.catalog_level_ok, self.toggle_level_ok)
        self.page.text(276, 6, "Úroveň mi stačí", 150, INK)
        self.page.checkbox(436, 8, self.catalog_free, self.toggle_free)
        self.page.text(462, 6, "Volná místa", 120, INK)
        self.page.action("Obnovit", w - 110, 0, self.refresh_catalog, not self.pending, width=110, height=30)
        x = 0
        for code, text in (("", "Vše"),) + FOCUS:
            cell = 94 if code else 50
            self.page.keep(Flat(self.page, px(x), px(42), span(x, cell), span(42, 30),
                lambda c=code: self.set_focus(c), text, "tab", self.catalog_focus == code, True, "center",
                fontconfig.ROLE_CONTROL, hint=FOCUS_HINTS.get(code)))
            x += cell + 4
        top = 86
        level = self.my_level()
        records = catalog_rows(self.model.rows(m.RECRUITMENT), self.query(), self.catalog_focus,
            level if self.catalog_level_ok else 0, self.catalog_free)
        # K2 "Karty" (owner 12. 10. 2026: few guilds will recruit): two cards per row, a click opens the profile.
        pairs = [records[index:index + 2] for index in range(0, len(records), 2)]
        gap = 12
        card_w = (w - 16 - gap) // 2
        card_h = 92

        def draw(canvas, pair, y, width):
            for index, row in enumerate(pair):
                self.guild_card_r1(canvas, index * (card_w + gap), y, card_w, card_h, row)
        self.list(pairs, top, 424, card_h + 10, draw, w)
        if not records:
            if not self.browsed:
                empty = "Načítání katalogu..."
            elif self.model.rows(m.RECRUITMENT):
                empty = "Žádný cech neodpovídá filtru."
            else:
                empty = "Zatím nikdo nenabírá. Založ vlastní cech nebo počkej na pozvánku."
            self.page.text(8, top + 12, empty, w - 16, MUTED, multiline=True)
            if self.model.rows(m.RECRUITMENT):
                self.page.action("Zrušit filtry", 8, top + 50, self.reset_filters, width=150, height=30)

    def guild_card_r1(self, canvas, x, y, w, h, record):
        v, name, body = record
        tags, text = parse_profile(body)
        canvas.row(x, y, w, h, lambda r=record: self.profile_dialog_r1(r), style="row")
        mark = canvas.keep(ui.MarkBox())
        mark.SetParent(canvas)
        mark.SetPosition(px(x + 12), px(y + 14))
        mark.SetIndex(v[0])
        mark.Show()
        fitted_text(canvas, x + 40, y + 8, name, w - 130, GOLD, fontconfig.ROLE_CONTROL, hint=False)
        canvas.text(x + w - 12, y + 10, "úr. %d" % v[1], 90, DIM, ROLE_CAPTION, "right")
        facts = ["%s: %d" % (localeInfo.GUILD_V2_FAMILY_COUNT, v[2])]
        if tags["c"]:
            facts.append(label(TIMES, tags["c"]))
        facts.append("od %d" % v[3])
        fitted_text(canvas, x + 12, y + 36, " · ".join(facts), w - 24, DIM, ROLE_CAPTION, hint=False)
        state = self.apps.state_of(v[0])
        right = 130 if state == 0 else 0
        if state == 0:
            canvas.text(x + w - 12, y + 62, "Žádost odeslána", 130, GREEN, ROLE_CAPTION, "right")
        focus = ", ".join(label(FOCUS, c) for c in tags["z"])
        if focus:
            fitted_text(canvas, x + 12, y + 62, focus, w - 24 - right, INK, ROLE_CAPTION, hint=False)

    def profile_dialog_r1(self, record):
        """The profile of a recruiting guild (K2): facts, focus, description and the application with its message."""
        v, name, body = record
        tags, text = parse_profile(body)
        level = self.my_level()
        d = self.popup("Profil cechu", 470)
        fitted_text(d, 24, 46, name, 512, GOLD, fontconfig.ROLE_CONTROL)
        rows = (("Úroveň cechu", str(v[1])), (localeInfo.GUILD_V2_FAMILY_COUNT, str(v[2])),
            ("Přijímá od úrovně", str(v[3])), ("Kdy hrají", label(TIMES, tags["c"]) or "-"),
            ("Zaměření", ", ".join(label(FOCUS, c) for c in tags["z"]) or "-"))
        top = 76
        for key, value in rows:
            d.text(24, top + 4, key, 240, DIM)
            fitted_text(d, 536, top + 4, value, 270, INK, fontconfig.ROLE_CONTROL, align="right")
            d.rule(24, top + 30, 512)
            top += 32
        description = text.strip() or "Cech zatím nemá veřejný popis."
        d.paragraph(24, top + 8, 512, 74, description)
        top += 92
        state = self.apps.state_of(v[0])
        if state == 0:
            d.text(24, top + 8, "Žádost odeslána, čeká na vedení cechu.", 512, GREEN)

            def cancel():
                self.apps.cancel(v[0])
                d.Close()
            d.primary("Zrušit žádost", cancel)
            return
        reason = None
        if level and level < v[3]:
            reason = "Na tento cech potřebuješ úroveň %d." % v[3]
        elif len(self.apps.pending()) >= APPLICATIONS_MAX:
            reason = "Už máš 3 žádosti. Nějakou zruš v Moje žádosti."
        d.text(24, top + 2, "Zpráva pro vedení (nepovinné, do %d znaků)" % MESSAGE_BYTES, 512,
            MUTED if reason else DIM)
        message = d.edit(24, top + 30, 482, MESSAGE_BYTES)

        def submit():
            if reason:
                return
            text_ = clean_message(message.GetText())
            if text_ is None:
                d.message.SetText("Zpráva je moc dlouhá nebo obsahuje znak |.")
                return
            self.apps.apply(v[0], text_)
            self.message("Odesílám žádost...", DIM)
            d.Close()
        message.SetReturnEvent(submit)
        d.primary("Požádat o vstup", submit, reason=reason)
        if state == 2 and not reason:
            d.message.SetPackedFontColor(widgets.native_color(MUTED))
            d.message.SetText("Minulou žádost cech odmítl.")

    def my_level(self):
        try:
            import player
            return int(player.GetStatus(player.LEVEL))
        except Exception:
            return 0

    def toggle_level_ok(self):
        self.catalog_level_ok = not self.catalog_level_ok
        self.render()

    def toggle_free(self):
        self.catalog_free = not self.catalog_free
        self.render()

    def set_focus(self, code):
        self.catalog_focus = code
        self.scroll = None
        self.render()

    def reset_filters(self):
        self.catalog_focus, self.catalog_level_ok, self.catalog_free = "", False, False
        self.queries["catalog"] = ""
        if self.search and self.search_key == "catalog":
            self.search.reset("")
        self.render()

    def refresh_catalog(self):
        self.browsed = False
        self.request(m.BROWSE)
        self.apps.refresh_mine()

    # ------------------------------------------------------------------ Moje žádosti
    def page_mine_r1(self, w):
        apps = self.apps
        rows = apps.mine
        now = app.GetTime()
        caption = "Vedení cechu tvou žádost vidí v okně cechu. Když ji přijme, vstoupíš do cechu sám." \
            if rows else ""
        self.page.text(0, 0, caption, w, DIM, ROLE_CAPTION)

        def draw(canvas, row, y, width):
            guild, state, age, name, received = row
            age = age + int(now - received)
            canvas.text(12, y + 6, name or ("Cech %d" % guild), width - 330, INK, fontconfig.ROLE_CONTROL)
            left = max(0, VALID_HOURS * 3600 - age)
            info = ago(age) + (" · vyprší za %d h" % (left // 3600) if state == 0 else "")
            canvas.text(12, y + 28, info, width - 330, DIM, ROLE_CAPTION)
            color = (DIM, GREEN, widgets.RED, MUTED, MUTED)[state] if state < 5 else MUTED
            canvas.text(width - 170, y + 14, STATE_TEXT[state] if state < 5 else "-", 150, color, ROLE_CAPTION, "right")
            if state == 0:
                canvas.action("Zrušit", width - 150, y + 9, lambda g=guild: apps.cancel(g), True, width=140, height=30)
            canvas.rule(0, y + 50, width, 0xff1e1c1d)
        self.list(rows, 30, 380, 52, draw, w)
        if not rows:
            self.page.text(0, 40, "Načítání žádostí..." if not apps.mine_loaded else
                "Nemáš žádné žádosti. Cech si najdeš v Katalogu cechů.", w, MUTED)
        self.page.text(0, 420, "Nejvýš %d žádosti naráz, každá platí %d hodin; stejnému cechu znovu po 24 hodinách."
            % (APPLICATIONS_MAX, VALID_HOURS), w, MUTED, ROLE_CAPTION)

    # ------------------------------------------------------------------ Členové -> Žádosti (leader and council)
    def applications_toggle_r1(self, x, y, width):
        count = len(self.apps.guild_rows)
        on = self.members_view == "apps"
        button = self.page.action("Žádosti (%d)" % count if count else "Žádosti", x, y, self.toggle_members_view, True,
            width=width, height=30, selected=on)
        return button

    def toggle_members_view(self):
        self.members_view = "list" if self.members_view == "apps" else "apps"
        if self.members_view == "apps":
            self.apps.refresh_list()
        self.render()

    def page_applications_r1(self, w, top):
        apps = self.apps
        rows = apps.guild_rows
        now = app.GetTime()

        def draw(canvas, row, y, width):
            pid, level, job, age, name, family, message, received = row
            who = "%s · %s %d" % (name, JOBS[job] if job < len(JOBS) else "", level)
            canvas.text(12, y + 6, who, width - 440, INK, fontconfig.ROLE_CONTROL)
            canvas.text(width - 304, y + 8, ago(age + int(now - received)), 120, MUTED, ROLE_CAPTION, "right")
            fitted_text(canvas, 12, y + 32, ('„%s“' % message) if message else "bez zprávy", width - 316,
                DIM if message else MUTED, ROLE_CAPTION)
            canvas.button("Přijmout", width - 290, y + 12, lambda r=row: self.accept_application(r),
                not self.pending and self.can(1), width=135)
            canvas.action("Odmítnout", width - 145, y + 12, lambda p=pid: apps.decide(p, False), not self.pending,
                width=135, height=30)
            canvas.rule(0, y + 58, width, 0xff1e1c1d)
        self.list(rows, top, 340, 60, draw, w)
        if not rows:
            self.page.text(12, top + 12, "Načítání žádostí..." if not apps.list_loaded else
                "Žádné nové žádosti. Nábor se zapíná ve Správě cechu.", w - 24, MUTED)
        self.page.text(0, top + 350, "Přijmout = pozvánka do cechu; žadatel online vstoupí hned, jinak při přihlášení.",
            w, MUTED, ROLE_CAPTION)

    def accept_application(self, row):
        pid, level, job, age, name, family, message, received = row
        target = family if self.family_mode() and family else name
        if self.request(m.INVITE, (), target):
            self.accepting = (pid, name)

    # ------------------------------------------------------------------ Správa -> Nábor
    def recruiting_section_r1(self, y, w):
        y = self.section_r1("Nábor", y)
        values, title, body = self.model.row(m.PROFILE)
        tags, text = parse_profile(body)
        if values[0]:
            parts = ["Cech nabírá od úrovně %d" % values[1]]
            if tags["z"]:
                parts.append(", ".join(label(FOCUS, c) for c in tags["z"]))
            if tags["c"]:
                parts.append(label(TIMES, tags["c"]))
            status, color = " · ".join(parts), INK
        else:
            status, color = "Nábor je vypnutý, cech se v katalogu neukazuje.", DIM
        fitted_text(self.page, 0, y + 2, status, w - 200, color, fontconfig.ROLE_CONTROL)
        self.page.text(0, y + 26, "Hráči bez cechu tě najdou v Katalogu cechů a pošlou žádost.", w - 200, DIM,
            ROLE_CAPTION)
        self.page.action("Upravit nábor", w - 170, y + 4, self.recruiting_dialog, self.can(1) and not self.pending,
            width=170, height=32)
        return y + 62

    def recruiting_dialog(self):
        values, title, body = self.model.row(m.PROFILE)
        tags, text = parse_profile(body)
        # A guild that never set its recruiting opens the dialog to recruit: the switch starts on (owner 12. 10.: a
        # saved profile with the switch left off never showed up in the catalogue).
        fresh = not values[0] and not str(body or "").strip()
        state = {"open": bool(values[0]) or fresh, "z": list(tags["z"]), "c": tags["c"] or "vecery"}
        d = self.popup("Nábor cechu", 480)
        box = d.keep(widgets.uir1.CheckBox(d, widgets.kit(), px(24), px(52), "Cech nabírá (ukáže se v Katalogu cechů)",
            on=state["open"], event=lambda: toggle_open()))
        d.text(24, 92, "Od úrovně", 160, DIM)
        level = d.edit(200, 92, 80, 3, values[1] or 1, True)
        cells = {}

        def row_of(y, title_text, pairs, key, width):
            if title_text:
                d.text(24, y + 6, title_text, 160, DIM)
            x = 200
            for code, text_ in pairs:
                cells[(key, code)] = d.keep(Flat(d, px(x), px(y), span(x, width), span(y, 30),
                    lambda k=key, c=code: pick(k, c), text_, "tab", False, True, "center", fontconfig.ROLE_CONTROL,
                    hint=FOCUS_HINTS.get(code) if key == "z" else None))
                x += width + 4

        def paint():
            for (key, code), cell in cells.items():
                cell.SetSelected(code in state["z"] if key == "z" else state[key] == code)

        def pick(key, code):
            if key == "z":
                if code in state["z"]:
                    state["z"].remove(code)
                elif len(state["z"]) < FOCUS_MAX:
                    state["z"].append(code)
                else:
                    d.message.SetText("Zaměření může mít nejvýš %d štítky." % FOCUS_MAX)
            else:
                state[key] = code
            paint()

        def toggle_open():
            state["open"] = not state["open"]
            box.SetOn(state["open"])
        row_of(136, "Zaměření (až 3)", FOCUS[:3], "z", 100)
        row_of(172, "", FOCUS[3:], "z", 100)
        row_of(216, "Kdy hrajete", TIMES, "c", 100)
        paint()
        d.text(24, 262, "Představení cechu (co děláte, koho hledáte)", 480, DIM)
        description = d.edit(24, 292, 482, 900, text, height=80)

        def submit():
            try:
                minimum = m.positive(level.GetText())
                if minimum > 120:
                    raise ValueError("Úroveň musí být od 1 do 120.")
            except ValueError as error:
                d.message.SetText(str(error))
                return
            profile = build_profile({"z": state["z"], "c": state["c"]}, description.GetText())
            if utf8_len(profile) > 1024 or "|" in profile:
                d.message.SetText("Představení je moc dlouhé nebo obsahuje znak |.")
                return
            if d.submit(m.SET_PROFILE, (int(state["open"]), minimum), "", profile) and not state["open"]:
                chat.AppendChat(chat.CHAT_TYPE_INFO, "Nábor je vypnutý, cech se v Katalogu cechů neukáže.")
        d.primary("Uložit nábor", submit)

    # ------------------------------------------------------------------ Deník (D1)
    def diary_rows(self):
        rows = list(self.model.history.get(m.CHRONICLE, ()))
        rows.sort(key=lambda row: -row[0][0])
        names = dict((row[0][0], row[1]) for row in self.model.rows(m.MEMBER))
        result = []
        for values, actor, text in rows:
            entry = diary_sentence(values, actor, text, names.get)
            if entry:
                result.append((values, entry[0], entry[1]))
        return result

    def page_chronicle_r1(self, w):
        x = 0
        for key, text in DIARY_FILTERS:
            self.page.keep(Flat(self.page, px(x), px(0), span(x, 100), span(0, 30),
                lambda k=key: self.set_diary_filter(k), text, "tab", self.diary_filter == key, True, "center",
                fontconfig.ROLE_CONTROL))
            x += 104
        self.page.action("Obnovit", w - 110, 0, lambda: self.history(5), not self.pending, width=110, height=30)
        rows = [row for row in self.diary_rows() if self.diary_filter == "all" or row[1] == self.diary_filter]
        now = self.model.now(app.GetTime())

        def draw(canvas, row, y, width):
            values, kind, sentence = row
            canvas.text(12, y + 9, when(values[4], now), 110, MUTED, ROLE_CAPTION)
            fitted_text(canvas, 130, y + 7, sentence, width - 142, INK, fontconfig.ROLE_CONTROL)
            canvas.rule(0, y + ROW, width, 0xff1e1c1d)
        self.list(rows, 44, 380, ROW + 2, draw, w)
        if not rows:
            loading = self.pending or self.history_wanted or self.model.history_kind != 5 or not self.model.history
            self.page.text(12, 56, "Načítání deníku..." if loading and not self.model.history.get(m.CHRONICLE)
                and self.pending else "Zatím tu nic není. Deník se píše sám: příchody, odchody, hodnosti a úspěchy cechu.",
                w - 24, MUTED, multiline=True)
        if self.model.history_next:
            self.page.action("Starší", w - 150, 432, lambda: self.history(5, self.model.history_next), not self.pending,
                width=150, height=30)
        if self.model.history_cursor:
            self.page.action("Nejnovější", 0, 432, lambda: self.history(5), not self.pending, width=150, height=30)

    def set_diary_filter(self, key):
        self.diary_filter = key
        self.scroll = None
        self.render()

    def recent_events_r1(self, y, w):
        """Přehled: the 3 newest diary rows and "Otevřít deník"."""
        y = self.section_r1("Poslední události", y)
        rows = self.diary_rows()[:3]
        now = self.model.now(app.GetTime())
        for values, kind, sentence in rows:
            self.page.text(0, y + 4, when(values[4], now), 110, MUTED, ROLE_CAPTION)
            fitted_text(self.page, 118, y + 2, sentence, w - 330, INK)
            y += 30
        if not rows:
            self.page.text(0, y + 2, "Zatím tu nic není." if self.model.history else "Načítání...", w - 200, MUTED)
            y += 30
        self.page.action("Otevřít deník", w - 190, y - 30, lambda: self.SelectPage("chronicle"), width=190, height=30)
        return y + 10


def shorten(measure, text, limit):
    """``text`` cut at a word boundary with "…" so that measure(result) <= limit pixels; the text itself when it fits.
    ``measure`` returns the pixel width of a string in the line's font (the client's real glyph advances)."""
    text = str(text)
    if measure(text) <= limit:
        return text
    words = text.split(" ")
    while len(words) > 1:
        words.pop()
        candidate = " ".join(words).rstrip(" :,·-") + ELLIPSIS
        if measure(candidate) <= limit:
            return candidate
    # one long word: cut letters
    word = words[0] if words else ""
    while word and measure(word + ELLIPSIS) > limit:
        word = word[:-1]
    return word + ELLIPSIS


def fitted_text(canvas, x, y, text, width, color=INK, role=fontconfig.ROLE_BODY, hint=True, align="left"):
    """A one-line text of a list: measured in its font, shortened at a word with "…" when wider than ``width`` design
    units (never cut inside a word by the line's limit), the full text as the hint of the row."""
    probe = ui.TextLine()
    probe.SetFontName(widgets.font(role))

    def measure(value):
        probe.SetText(value)
        return probe.GetTextSize()[0]
    limit = px(width)
    shown = shorten(measure, text, limit)
    if shown != str(text) and hint:
        # the hover area first: the text draws above it (never inside a clickable row: it would take the click)
        height = probe.GetTextSize()[1] or 16
        left = px(x) - (limit if align == "right" else 0)
        canvas.keep(Flat(canvas, left, px(y) - 2, limit, height + 4, None, "", "plain", enabled=False,
            hint=str(text)))
    return canvas.text(x, y, shown, 0, color, role, align)


def send_chat(text):
    sender = getattr(net, "SendChatPacket", None)
    if sender:
        sender(text)


def widgets_ready(window):
    return bool(getattr(net, "IsGuildV2Available", lambda: False)()) and bool(window.model.rows(m.CAPABILITY))


def badge(parent, x, y, count):
    """The one count badge of R1 (a red circle with a white number, PRAVIDLA-UI "Odznaky"), at pixel x, y."""
    text = str(count) if count < 10 else "9+"
    pill = ui.ExpandedImageBox()
    pill.SetParent(parent)
    pill.AddFlag("not_pick")
    pill.LoadImage(BADGE + ("count_1.png" if len(text) == 1 else "count_2.png"))
    pill.SetPosition(x, y)
    pill.Show()
    parent.keep(pill)
    digits = [c for c in text if c.isdigit()]
    start = (pill.GetWidth() - (len(text) * 6 - 1)) // 2
    for index, digit in enumerate(digits):
        image = ui.ExpandedImageBox()
        image.SetParent(pill)
        image.AddFlag("not_pick")
        image.LoadImage(BADGE + "digit_%s.png" % digit)
        image.SetPosition(start + index * 6, 3)
        image.Show()
        parent.keep(image)
    return pill
