import app
import chat
import fontconfig
import localeInfo
import namepolicy
import net
import player
import ui
import uiUploadMark
import uir1tokens as T
import wndMgr
import guildv2model as m
import guildcosmetic
import ownedcount
from marketfilters import folded
from uiguildv2widgets import (ART, SCALE, Canvas, Dialog, Flat, ScrollList, SearchField, SettingsScrollBar,
    INK, DIM, GOLD, GREEN, RED, MUTED, ROLE_TITLE, ROLE_FIGURE, ROLE_CAPTION, check, native_color, px, span, scale_button,
    unit, font, R1, LOCKED_HINT, lock_image, scrollbar)
import uiguildv2widgets as widgets
from uiguildv2r1 import R1Pages, rank_step, shown_passives
from uiguildv2katalog import KatalogPages

def yang(value):
    """A yang amount of the guild window: the one R1 yang price of the client ("200.000 Yang", root/uir1price.py,
    ) in the R1 look; "Starý vzhled" keeps "200 000 Yang"."""
    if R1:
        try:
            import uir1price
            return uir1price.FormatYang(value)
        except Exception:
            pass
    return m.number(value) + " Yang"

YANG_ICON = "d:/ymir work/ui/game/crimson_ember/inventory/icon_yang.png"   # the R1 coin (root/uir1price.py ICON)

NAVIGATION = (("overview", "Přehled"), ("goals", "Cíle a kontrakty"), ("passives", "Schopnosti"),
    ("expedition", "Výprava"), ("members", "Členové"), ("doctrines", "Doktríny"),
    ("chronicle", localeInfo.GUILD_V2_DIARY), ("materials", localeInfo.GUILD_V2_MATERIALS),
    ("treasury", localeInfo.GUILD_V2_TREASURY))
NAV_ICONS = ("overview", "contracts", "skills", "expedition", "members", "doctrines", "chronicle", "materials", "treasury")
# The guild for the start is founding, invitations, members and the council, the disband with its
# delay, the notice board and the village with the boss souls. Everything else stays visible but locked (dimmed,
# padlock, hint "Připravujeme") until the first larger update.
# Keys: the locked pages plus "catalog" (guild catalog), "profile" (recruiting profile), "points" (members tab) and
# "rights" (every right but member management). An empty set is the full window as before.
# 12. 10. 2026: the passives are open with the build queue (one upgrade at a time, progression v2); the
# catalogue, the recruiting profile and the diary (Kronika -> "Deník") are open (guild catalogue v1).
# Which features are locked is data (owner 13. 10. 2026): tools/data/guild_v2_features.json, "open": false.
# BEGIN GENERATED GUILD FEATURES (tools/build_guild_v2_features.py from tools/data/guild_v2_features.json)
LOCKED = frozenset(("portal", "goals", "expedition", "doctrines", "materials", "treasury", "approvals", "audit", "points", "rights"))
# END GENERATED GUILD FEATURES

def locked(key):
    # The guild looks (Vzhled) are locked by the server's switch, not by this file (root/guildcosmetic.py).
    return key in LOCKED or guildcosmetic.page_locked(key)
PAGES = {
    "overview": ("Cechovní přehled", None),
    "goals": ("Cíle a kontrakty", "Společné cíle cechu a volba kontraktů"),
    "passives": ("Pasivní schopnosti", "Společné bonusy, jejich stupně a vylepšování"),
    "expedition": ("Výprava", "Společná výprava členů cechu"),
    "members": ("Členové cechu", None),
    "doctrines": ("Doktríny", "Směr, kterým se cech vydává"),
    "chronicle": (localeInfo.GUILD_V2_DIARY, localeInfo.GUILD_V2_DIARY_SUBTITLE),
    "materials": ("Cechovní materiály", "Zásoby cechu a materiály získané v aktuálním cíli"),
    "treasury": ("Pokladna", "Yang vložený členy do cechu"),
    "settings": ("Správa cechu", "Nábor, profil a vedení cechu"),
    "board": ("Cechovní nástěnka", "Důležité zprávy pro členy cechu"),
    "approvals": ("Schvalování", "Rozhodnutí, která čekají na souhlas"),
    "audit": ("Rozšířený audit", "Přehled akcí vedení cechu"),
}
GOAL_TITLES = ("Lov meteorů", "Cechovní těžba", "Fragmenty duše")
GOAL_HINTS = ("Získávej úlomky meteoru ničením meteorů.", "Získávej cechovní rudu těžbou.",
    "Získávej fragmenty duše z vybraných bossů.")
MATERIAL_SOURCES = ("Šance při zničení meteoru", "Šance při úspěšné těžbě", "Šance při zabití vybraných bossů")
# One glossary for every page; the same words are used in all labels.
HELP = (
    (localeInfo.GUILD_V2_DIARY, localeInfo.GUILD_V2_HELP_DIARY),
    ("Hodnost", "Postavení člena v cechu: Vůdce, Rada nebo Člen. Co která hodnost smí, nastavuje vůdce "
        "v Oprávněních (Členové > Hodnosti a práva)."),
    (localeInfo.GUILD_V2_HELP_RANK_TERM, localeInfo.GUILD_V2_HELP_RANK),
    ("Materiály", localeInfo.GUILD_V2_STOCK_SHARDS + " (šance při zničení meteoru), " + localeInfo.GUILD_V2_STOCK_ORE + " (šance při těžbě) a "
        + localeInfo.GUILD_V2_STOCK_SOULS + " (šance u vybraných bossů). Cech je získává sám, stačí být jeho členem."),
    ("Cíl a kontrakty", "Cíl je společný úkol s termínem. Počítají se do něj nově získané materiály, zásoby se "
        "nespotřebují. Kontrakty jsou množství připravená pro příští cíl."),
    ("Mandát", "Cech získá 1 Mandát za každých 100 získaných materiálů. "
        "Musí přispět aspoň 3 různé účty."),
    ("Cechovní body", "Osobní body člena za příspěvek do splněného cíle a za úspěšnou výpravu. "
        "Po odchodu z cechu se nepřenášejí."),
)
# Member table: sort key, header, column start as a fraction of the row width.
MEMBER_COLUMNS = (("name", "Člen", 0.0), ("role", "Hodnost", 0.25), ("level", "Lv.", 0.38),
    ("metin", localeInfo.GUILD_V2_STOCK_SHARDS, 0.48), ("ore", localeInfo.GUILD_V2_STOCK_ORE, 0.59), ("soul", localeInfo.GUILD_V2_STOCK_SOULS, 0.69), ("online", "Aktivita", 0.83))
NOTICE_LIMIT = 12

def supported():
    # Native availability becomes true only after the first server snapshot.
    # Its initial false value must never select a legacy mutation/UI path.
    return callable(getattr(net, "IsGuildV2Available", None))

def available():
    return bool(getattr(net, "IsGuildV2Available", lambda: False)())

class InvitationDialog(Canvas):
    """Independent invitation; Enter uses the same guarded acceptance as its button."""
    def __init__(self, owner, invitation):
        Canvas.__init__(self, None, 0, 0, 410, 204)
        import uiconfirm
        uiconfirm.Bind(self, 'accept')
        self.owner, self.identifier = owner, invitation[0][0]
        self.AddFlag("float")
        self.AddFlag("movable")
        self.shell(410, 204, "Pozvánka do cechu", ui.__mem_func__(self.Close))
        self.text(205, 44, invitation[1], 362, GOLD, ROLE_FIGURE, align="center")
        self.text(205, 80, "Tento cech tě zve mezi své členy.", 362, align="center")
        self.message = self.text(205, 112, "Esc nebo křížek pozvánku odloží na později.", 362, DIM, ROLE_CAPTION, "center")
        self.accept = self.button("Přijmout", 24, 158, lambda: self.decide(0))
        self.decline = self.action("Odmítnout", 236, 158, lambda: self.decide(1), owner.can_decline(), width=150, height=28)
        self.SetCenterPosition()
        self.Show()
        self.SetTop()

    def decide(self, decision):
        owner = self.owner
        if not owner or owner.pending or not owner.valid_invitation(self.identifier):
            return False
        if decision not in (0, 1) or (decision == 1 and not owner.can_decline()):
            return False
        if not owner.request(m.ACCEPT_INVITE, (self.identifier, decision)):
            self.message.SetText(owner.status_text.GetText())
            return False
        owner.invitation_decision = decision
        self.accept.Disable()
        self.decline.Disable()
        self.message.SetText("Čeká se na potvrzení...")
        return True

    def Close(self):
        if self.owner and self.owner.invitation_dialog is self:
            self.owner.invitation_dialog = None
        self.owner = None
        self.Destroy()

    def OnPressEscapeKey(self):
        self.Close()
        return True

class GuildWindow(KatalogPages, R1Pages, Canvas):
    @property
    def shows_approvals(self):
        # buttonpanelstatus: no approvals badge while the approvals page is locked.
        return not locked("approvals")

    def __init__(self, interface):
        # Design units; the window occupies SCALE of them on screen.
        width = min(1040, int((wndMgr.GetScreenWidth() - 16) / SCALE))
        height = min(690, int((wndMgr.GetScreenHeight() - 38) / SCALE))
        Canvas.__init__(self, None, 0, 0, width, height)
        self.AddFlag("movable")
        self.AddFlag("float")
        self.interface = interface
        self.model = m.Model()
        self.currentPage, self.tab = "overview", 0
        self.pageWindow = dict((name, True) for name, title in NAVIGATION)
        self.selected_passive, self.selected_member = 5, 0
        self.dialog = None
        self.invitation_dialog = None
        self.mark_dialog = None
        self.invitation_decision = None
        self.create_requested = False
        self.disband_requested = False
        self.leave_requested = False
        self.invite_requested = None
        self.invitation_requested = None
        self.pending = False
        self.development_pending = False
        self.pending_action = None
        self.pending_since = 0.0
        self.scroll = None
        # Presentation-only state; never sent to the server.
        self.stale = True
        self.browsed = False
        self.snapshot_wanted = False
        self.catalog_wanted = False
        self.refresh_after = 0.0
        self.history_wanted = None
        self.rights_draft = None
        self.member_sort = ("role", False)
        self.online_only = False
        self.queries = {}
        self.search = None
        self.search_key = None
        self.katalog_init()
        if R1:
            # The R1 layout (side panel, content panel with a header band): uiguildv2r1.
            self.r1_build(width, height)
            self.SetCenterPosition()
            self.Hide()
            return
        self.shell(width, height, "Cech", ui.__mem_func__(self.Close))
        # R1: below the header row, so the whole row drags the window (its height is 27 px).
        self.sidebar = Canvas(self, 8, 38, 188, height - 42) if R1 else Canvas(self, 8, 26, 188, height - 30)
        self.sidebar.Show()
        self.viewport = Canvas(self, 216, 43, width - 236, height - 90)
        self.viewport.EnableScissorRect()
        self.viewport.Show()
        self.page = Canvas(self.viewport, 0, 0, width - 252, 600)
        self.page.on_wheel = ui.__mem_func__(self.wheel_page)
        self.page.Show()
        self.page_scroll = scrollbar()
        self.page_scroll.SetParent(self)
        self.page_scroll.SetPosition(px(width - 29), px(43))
        self.page_scroll.SetScrollBarSize(px(height - 90))
        self.page_scroll.SetMiddleBarSize(min(1.0, float(height - 90) / 600))
        self.page_scroll.SetScrollStep(0.15)
        self.page_scroll.SetScrollEvent(ui.__mem_func__(self.scroll_page))
        self.viewport.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel_page))
        self.page.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel_page))
        if height < 690:
            self.page_scroll.Show()
        self.footer = Canvas(self, 216, height - 35, width - 236, 32)
        self.footer.Show()
        self.status_text = self.footer.text(0, 9, "Načítání cechu...", width - 466, DIM)
        if R1:
            # R1 primary button; its label is the village label the page code renames.
            self.village = self.footer.keep(widgets.uir1.Button(self.footer, widgets.kit(),
                px(self.footer.design_width - 214), 0, span(self.footer.design_width - 214, 214), "Do cechovní vesnice",
                primary=True, event=lambda: self.request(m.VILLAGE)))
            self.village.SetToolTipText("Teleportovat do cechovní vesnice")
            self.village_label = self.village.label
            self.SetCenterPosition()
            self.Hide()
            return
        self.village = self.footer.keep(ui.Button())
        self.village.SetParent(self.footer)
        self.village.SetPosition(px(self.footer.design_width - 214), 0)
        self.village.SetUpVisual(ART + "guild_village_normal.png")
        self.village.SetOverVisual(ART + "guild_village_hover.png")
        self.village.SetDownVisual(ART + "guild_village_pressed.png")
        self.village.SetDisableVisual(ART + "guild_village_disabled.png")
        scale_button(self.village)
        self.village.SetEvent(lambda: self.request(m.VILLAGE))
        self.village.SetToolTipText("Teleportovat do cechovní vesnice")
        self.village.Show()
        self.village_label = self.footer.text(self.footer.design_width - 82, 8, "Do cechovní vesnice", 158,
            role=fontconfig.ROLE_CONTROL, align="center")
        self.SetCenterPosition()
        self.Hide()

    def pid(self):
        return self.model.row(m.CAPABILITY)[0][9]

    def family_mode(self):
        return self.model.row(m.CAPABILITY)[2] == "family-v1"

    def member_name(self, name, body):
        return body if self.family_mode() and body else name

    def member_state_text(self, v):
        """ "Online", or when the member last played ("před 3 h", "před 2 dny", a date; owner 21. 10., batch 7 add-on)."""
        return "Online" if v[7] else m.last_seen(self.model.member_seen(v[0]), self.model.now(app.GetTime()))

    def member_yang_text(self, pid, prefix=""):
        """ "Yang 12,5 mld." - the Yang the member deposited into the treasury (batch 7 add-on), "" without deposits."""
        value = self.model.member_yang(pid)
        return prefix + "%s %s" % (getattr(localeInfo, m.CONTRIBUTION_YANG, "Yang"), m.short_yang(value, True)) if value else ""

    def member_actions_text(self, pid, prefix=""):
        """ "Těžba 142 · Rybaření 80 · Kácení 0 (tento týden)" - the member's craft actions of this week (owner 22. 10.,
        batch 8 G2); "" while the member has none."""
        values = self.model.member_actions(pid)
        if not any(values):
            return ""
        return prefix + getattr(localeInfo, "GUILD_V2_ACT_WEEK", "%s") % " · ".join("%s %s" % (getattr(localeInfo, key, key),
            m.number(value)) for key, value in zip(m.ACTIONS, values))

    def member_xp_text(self, pid, prefix=""):
        """ "Přínos EXP tento týden: Meteory 1 340 · Řemesla 60 · Aktivita 30" - what the member brought this week from each
        source (owner 22. 10., batch 8 G4); "" on an older server."""
        if not self.model.xp_ceilings():
            return ""
        values = self.model.member_xp_sources(pid)
        return prefix + getattr(localeInfo, "GUILD_V2_XP_WEEK", "%s") % " · ".join("%s %s" % (getattr(localeInfo, key, key),
            m.number(value)) for key, value in zip(m.XP_SOURCES, values))

    def guild_xp_text(self):
        """ "Strop cechu tento týden: Meteory 3 400/12 000 · Řemesla 900/2 500 · Aktivita 300/1 500" - the guild's EXP of this
        week from each source against its weekly ceiling (owner 22. 10., batch 8 G4: one ceiling for the whole guild);
        "" on an older server."""
        state = self.model.xp_ceilings()
        if not state:
            return ""
        ceilings, used = state
        return getattr(localeInfo, "GUILD_V2_XP_GUILD", "%s") % " · ".join("%s %s/%s" % (getattr(localeInfo, key, key),
            m.number(min(value, ceiling)), m.number(ceiling)) for key, value, ceiling in zip(m.XP_SOURCES, used, ceilings))

    def member_actions_hint(self, pid, extra=None):
        """Row hint of Příspěvky, "title\nbody" of the shared R1 hint: the actions of this week, then which actions count
        (owner 22. 10.: AFK mining does not), the EXP of this week per source with its ceiling (batch 8 G4: the ceiling
        limits EXP only) and ``extra`` (the family line) under the vein."""
        title = self.member_actions_text(pid) or getattr(localeInfo, "GUILD_V2_ACT_NONE", "")
        xp = self.member_xp_text(pid)
        guild = self.guild_xp_text() if xp else ""
        xp_hint = getattr(localeInfo, "GUILD_V2_XP_HINT", "") if xp else ""
        return "\n".join(part for part in (title, getattr(localeInfo, "GUILD_V2_ACT_HINT", ""), xp, guild, xp_hint, extra) if part)

    def member_family_hint(self, name):
        return localeInfo.GUILD_V2_MEMBER_FAMILY % name if self.family_mode() else None

    def leader(self):
        return self.pid() != 0 and self.model.row(m.SUMMARY)[0][0] == self.pid()

    def can(self, right):
        return not self.pending and self.model.can(self.pid(), right)

    def request(self, action, values=(), title="", body="", identity=None):
        if not available() or (action != m.SNAPSHOT and not self.model.rows(m.CAPABILITY)):
            self.message("Načítání cechu...", DIM)
            return False
        identity = identity or self.model.identity()
        if self.pending:
            self.message("Čeká se na potvrzení předchozí akce.")
            return False
        if identity != self.model.identity():
            self.message(m.STATUS_TEXT[m.STALE])
            return False
        title_limit = {m.CREATE: namepolicy.GUILD_MAX_BYTES, m.DISBAND: namepolicy.GUILD_MAX_BYTES, m.CREATE_GOAL: 64, m.EDIT_GOAL: 64, m.POST_NOTICE: 64, m.INVITE: 24}.get(action, 128)
        if action in (m.CREATE, m.DISBAND) and not namepolicy.valid(title, namepolicy.GUILD_MAX_CHARACTERS):
            self.message("Zkontroluj délku názvu, znaky a mezery.")
            return False
        if len(str(title).encode("utf-8")) > title_limit or len(str(body).encode("utf-8")) > 1024 or "|" in str(title) + str(body):
            self.message("Text je příliš dlouhý nebo obsahuje nepovolený znak.")
            return False
        sent = net.SendGuildV2Command(int(action), int(identity[0]), int(identity[1]), tuple(int(v) for v in values), str(title), str(body))
        if not sent:
            self.message("Akce teď není dostupná. Obnov údaje cechu.")
            return False
        self.pending = True
        self.pending_action = action
        self.pending_since = app.GetTime()
        self.message("Čeká se na potvrzení...", DIM)
        return True

    def Receive(self, payload):
        old_identity = self.model.identity()
        if not self.model.receive(payload, app.GetTime()):
            # An older snapshot than the shown one is not drawn, but when it
            # answers the waiting request it must still release the window.
            if payload["action"] == self.pending_action:
                self.pending = False
                self.pending_action = None
                self.message("", DIM)
                if self.IsShow():
                    self.render()
            return
        action, status = payload["action"], payload["status"]
        if action == m.SNAPSHOT and self.catalog_wanted:
            self.refresh_after = app.GetTime() + 2.0
        matched_command = action == self.pending_action
        decision = self.invitation_decision
        if matched_command and action == m.ACCEPT_INVITE:
            self.invitation_decision = None
        # Server awards and periodic snapshots can arrive independently of a UI
        # operation. Only the matching native response releases its pending UI.
        if action == self.pending_action:
            self.pending = False
            self.pending_action = None
        membership_changed = old_identity[0] != self.model.guild
        if membership_changed:
            self.rights_draft = None
            self.selected_member = 0
            self.currentPage, self.tab = "overview", 0
            self.scroll = None
            self.history_wanted = None
            if self.search:
                self.search.edit.KillFocus()
            if self.dialog:
                self.dialog.Close()
            if self.mark_dialog:
                self.mark_dialog.Close()
        if status == m.OK and action in (m.CREATE, m.LEAVE, m.DISBAND, m.ACCEPT_INVITE):
            # Mutation replies can contain only a receipt/capability. Read the
            # resulting membership and invitations, including an empty roster.
            self.snapshot_wanted = True
            self.catalog_wanted = self.browsed or not locked("catalog")
            self.refresh_after = app.GetTime() + 0.25
        elif membership_changed:
            self.catalog_wanted = self.browsed or not locked("catalog")
            self.refresh_after = app.GetTime() + 0.25
        if action == m.BROWSE and status == m.OK:
            self.browsed = True
        if status == m.OK and matched_command and action not in (m.SNAPSHOT, m.BROWSE, m.HISTORY, m.VILLAGE):
            if self.dialog:
                self.dialog.Close()
            if action == m.UPGRADE:
                text = localeInfo.GUILD_V2_UPGRADE_QUEUED if self.model.building() else localeInfo.GUILD_V2_DONE
                if self.development_pending:
                    text = localeInfo.GUILD_V2_LEVEL_REACHED % self.model.row(m.SUMMARY)[0][1]
                self.development_pending = False
            elif action == m.DISBAND:
                text = "Rozpuštění bylo zrušeno." if not self.model.disband_at() else \
                    "Cech bude rozpuštěn %s." % m.moment(self.model.disband_at())
            else:
                text = m.STATUS_TEXT[status]
            self.message(text, GREEN)
            if action == m.INVITE:
                chat.AppendChat(chat.CHAT_TYPE_INFO, "Pozvánka do cechu byla odeslána.")
            elif action == m.ACCEPT_INVITE:
                text = "Pozvánka byla odmítnuta." if decision == 1 else "Jsi členem cechu %s." % self.model.row(m.SUMMARY)[1]
                chat.AppendChat(chat.CHAT_TYPE_INFO, text)
        elif matched_command and action == m.CREATE and status == m.NOT_READY:
            self.message("Po rozpuštění cechu můžeš založit nový až za %d dní." % m.DISBAND_LEADER_COOLDOWN_DAYS)
        elif matched_command and action == m.CREATE and status == m.CONFLICT:
            self.message("Tento název cechu je obsazený nebo rezervovaný.")
        elif matched_command and action == m.ACCEPT_INVITE and status == m.BUSY:
            self.message(localeInfo.GUILD_V2_INVITE_BUSY)
        elif status not in (m.OK, m.NOT_MEMBER):
            self.message(m.STATUS_TEXT[status])
        elif action == m.SNAPSHOT or matched_command:
            # A confirmed read (snapshot, history, catalog, village) has no
            # outcome to report; never leave "waiting for confirmation" behind.
            self.message("", DIM)
        if self.invitation_dialog:
            dialog = self.invitation_dialog
            if not self.valid_invitation(dialog.identifier) or (matched_command and action == m.ACCEPT_INVITE and status == m.OK):
                dialog.Close()
            elif matched_command and action == m.ACCEPT_INVITE:
                dialog.message.SetText(localeInfo.GUILD_V2_INVITE_BUSY if status == m.BUSY else m.STATUS_TEXT[status])
                dialog.accept.Enable()
                if self.can_decline():
                    dialog.decline.Enable()
        open_page = self.model.row(m.INSTANCE)[0][1]
        if open_page in (1, 2):
            self.currentPage = "chronicle" if open_page == 1 else "expedition"
            self.Show()
            self.SetTop()
        self.settle_rights(action, status, matched_command)
        self.katalog_after_receive(action, status, matched_command)
        # A closed window only keeps the data; it is drawn when it is shown.
        if self.IsShow():
            self.render()
        else:
            self.stale = True
        if not self.pending and self.history_wanted:
            kind, cursor = self.history_wanted
            self.history_wanted = None
            if kind == self.history_kind():
                self.history(kind, cursor)
        if action == m.SNAPSHOT and status in (m.OK, m.NOT_MEMBER):
            if self.invite_requested is not None:
                name, self.invite_requested = self.invite_requested, None
                if self.can(1):
                    self.invite_dialog(name)
                else:
                    self.message("K pozvání hráče nemáš oprávnění.")
            if self.invitation_requested is not None:
                if not self.valid_invitation(self.invitation_requested):
                    self.invitation_requested = None
                    self.message("Pozvánka už není platná nebo už jsi členem cechu.")
        if self.disband_requested and action == m.SNAPSHOT:
            self.disband_requested = False
            if status == m.OK and self.leader():
                self.disband_dialog()
            else:
                self.message("Cech může rozpustit jen jeho vůdce.")
        if self.leave_requested and action == m.SNAPSHOT:
            self.leave_requested = False
            if status == m.OK and self.model.guild and not self.leader():
                self.leave_dialog()
            else:
                self.message("Vůdce musí nejdřív předat vedení." if self.leader() else "Nejsi členem cechu.")
        if self.create_requested and action == m.SNAPSHOT:
            self.create_requested = False
            if status in (m.OK, m.NOT_MEMBER) and self.model.rows(m.CAPABILITY):
                if self.model.guild:
                    self.message("Už jsi členem cechu.")
                else:
                    self.create_dialog()

    def message(self, text, color=RED):
        self.status_text.SetPackedFontColor(native_color(color))
        self.status_text.SetText(text)
        if self.dialog:
            self.dialog.message.SetPackedFontColor(native_color(color))
            self.dialog.message.SetText(text)

    def Show(self):
        Canvas.Show(self)
        if self.stale:
            self.render()

    def Open(self):
        self.katalog_open()
        self.stale = True
        self.Show()
        self.SetTop()
        self.expire_pending()
        if not self.pending:
            self.request(m.SNAPSHOT)

    def expire_pending(self):
        """Release a request whose reply never came (lost answer, reconnect)."""
        if not self.pending or app.GetTime() - self.pending_since < m.PENDING_TIMEOUT:
            return False
        self.pending = False
        self.pending_action = None
        self.history_wanted = None
        self.create_requested = self.disband_requested = self.leave_requested = False
        self.message(m.PENDING_LOST)
        if self.invitation_dialog:
            self.invitation_dialog.accept.Enable()
            if self.can_decline():
                self.invitation_dialog.decline.Enable()
            self.invitation_dialog.message.SetText(m.PENDING_LOST)
        if self.IsShow():
            self.render()
        else:
            self.stale = True
        return True

    def OpenCreateDialog(self):
        # The NPC entry must obtain fresh capability/identity before opening
        # the same typed creation flow as the guild window.
        self.Open()
        self.create_requested = not available() or self.pending_action == m.SNAPSHOT
        if self.pending and not self.create_requested:
            self.message("Čeká se na potvrzení předchozí akce.")

    def OpenDisbandDialog(self):
        if self.dialog or (self.pending and self.pending_action != m.SNAPSHOT):
            self.message("Nejprve dokonči předchozí akci.")
            return False
        # Retain the NPC intent while the initial server offer is unavailable.
        # The snapshot handler rechecks leadership before opening confirmation.
        self.disband_requested = True
        self.Open()
        if not available() or self.pending_action == m.SNAPSHOT:
            return True
        self.disband_requested = False
        return False

    def OpenLeaveDialog(self):
        if self.dialog or (self.pending and self.pending_action != m.SNAPSHOT):
            self.message("Nejprve dokonči předchozí akci.")
            return False
        # As disband: the snapshot handler rechecks membership and leadership.
        self.leave_requested = True
        self.Open()
        if not available() or self.pending_action == m.SNAPSHOT:
            return True
        self.leave_requested = False
        return False

    def CanOpen(self):
        return supported()

    def Close(self):
        self.disband_requested = False
        self.leave_requested = False
        self.create_requested = False
        self.invite_requested = None
        self.invitation_requested = None
        if self.search:
            self.search.edit.KillFocus()
        if self.dialog:
            self.dialog.Close()
        if self.mark_dialog:
            self.mark_dialog.Close()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnUpdate(self):
        self.expire_pending()
        self.tick_build()
        # The persistent search line survives re-rendering; follow its text.
        search = self.search
        if search and search.IsShow() and self.search_key:
            value = search.value()
            if value != self.queries.get(self.search_key, ""):
                self.queries[self.search_key] = value
                self.render()

    def tick_build(self):
        """Countdown of the running upgrade: redraw every 30 s on the passives page, refresh once when it ends."""
        build = self.model.building() if self.IsShow() else None
        if not build:
            return
        now = app.GetTime()
        if self.model.now(now) >= build[3]:
            if not self.pending and getattr(self, "build_refreshed", None) != build[3]:
                self.build_refreshed = build[3]
                self.request(m.SNAPSHOT)
            return
        if self.currentPage == "passives" and now - getattr(self, "build_drawn", 0.0) >= 30.0:
            self.build_drawn = now
            self.render()

    def Destroy(self):
        if self.invitation_dialog:
            self.invitation_dialog.Close()
        self.Close()
        self.mark_dialog = None
        if self.search:
            self.search.Destroy()
            self.search = None
        self.sidebar.Destroy()
        self.page.Destroy()
        self.page_scroll.SetScrollEvent(None)
        self.page_scroll.Destroy()
        self.page_scroll.Hide()
        self.viewport.Destroy()
        self.footer.Destroy()
        if getattr(self, "band", None):
            self.band.Destroy()
        self.interface = None
        Canvas.Destroy(self)

    def SelectPage(self, name, tab=0):
        if locked(name):
            self.message(LOCKED_HINT + ": tahle část cechu přijde s první větší aktualizací.", DIM)
            name, tab = ("overview", 0) if locked(self.currentPage) else (self.currentPage, self.tab)
        self.create_requested = False
        self.disband_requested = False
        self.leave_requested = False
        if self.dialog:
            self.dialog.Close()
        if (name, tab) != (self.currentPage, self.tab):
            self.scroll = None
        if name != self.currentPage:
            self.rights_draft = None
        self.currentPage, self.tab = name, tab
        self.page_scroll.SetPos(0)
        self.model.history.clear()
        self.model.history_cursor = 0
        self.history_wanted = None
        self.render()
        kind = self.history_kind()
        if kind is not None:
            self.history(kind)

    def scroll_page(self):
        self.page.SetPosition(0, -int(max(0, self.page.GetHeight() - self.viewport.GetHeight()) * self.page_scroll.GetPos()))

    def wheel_page(self, down):
        if self.viewport.GetHeight() >= self.page.GetHeight():
            return False
        self.page_scroll.OnDown() if down else self.page_scroll.OnUp()
        return True

    def history_kind(self):
        if self.currentPage == "treasury" and not (self.model.can(self.pid(), 64) or self.model.can(self.pid(), 512)):
            return None
        return {("materials", 1): 2, ("materials", 2): 0, ("treasury", 0): 1,
            ("goals", 2): 4, ("chronicle", 0): 5, ("audit", 0): 3}.get((self.currentPage, self.tab))

    def history(self, kind, cursor=0):
        self.model.history_kind, self.model.history_cursor = kind, cursor
        if self.pending:
            # Ask again once the running request is confirmed instead of
            # presenting an unrequested history as empty.
            self.history_wanted = (kind, cursor)
            return False
        return self.request(m.HISTORY, (kind, cursor))

    def popup(self, title, height=340, width=560):
        if self.dialog:
            self.dialog.Close()
        self.dialog = Dialog(self, title, height, width)
        return self.dialog

    def confirm(self, title, description, action, values=(), text="", label="Potvrdit"):
        d = self.popup(title)
        d.text(24, 58, description, d.design_width - 48, multiline=True)
        d.primary(label, lambda: d.submit(action, values, text))

    def leave_dialog(self):
        if R1:
            return self.confirm("Opustit cech", "Opravdu chceš opustit cech? Do jiného cechu můžeš vstoupit "
                "až za 24 hodin.", m.LEAVE, label="Opustit cech")
        return self.confirm("Opustit cech", "Opravdu chceš opustit cech? Tvoje příspěvky zůstanou cechu a přestaneš "
            "získávat jeho bonusy.", m.LEAVE, label="Opustit cech")

    def tabs(self, labels, locked=()):
        for index, label in enumerate(labels):
            self.page.tab(label, index * 140, 72, lambda i=index: self.SelectPage(self.currentPage, i), self.tab == index,
                locked=index in locked)

    def list(self, rows, y, height, row_height, draw, width=None):
        offset = self.scroll.offset if self.scroll else 0
        self.scroll = self.page.keep(ScrollList(self.page, 0, y, width or self.page.design_width, height, list(rows), row_height, draw, offset))

    def search_field(self, key, x, y, width):
        if not self.search:
            self.search = SearchField(self.page, ui.__mem_func__(self.OnPressEscapeKey))
        if self.search_key != key:
            self.search_key = key
            self.search.reset(self.queries.get(key, ""))
        self.search.place(x, y, width)

    def query(self):
        return folded(self.queries.get(self.search_key, "").strip())

    # ------------------------------------------------------------------ frame
    def is_locked(self, key):
        return locked(key)

    def render(self):
        if R1:
            return self.render_r1()
        self.stale = False
        offset = self.scroll.offset if self.scroll else 0
        self.page.clear()
        self.scroll = None
        if self.search:
            self.search.Hide()
        self.render_sidebar()
        width, height = self.page.design_width, self.page.design_height
        values, name, body = self.model.row(m.SUMMARY)
        self.title_line.SetText("Cech | " + name if self.model.guild and name else "Cech")
        in_village = bool(self.model.row(m.INSTANCE)[0][0])
        if R1:
            self.village.SetText("Opustit vesnici" if in_village else "Do cechovní vesnice")
        else:
            self.village_label.SetText("Opustit vesnici" if in_village else "Do cechovní vesnice")
        self.village.SetToolTipText("Vrátit se na původní mapu" if in_village else "Teleportovat do cechovní vesnice")
        if (self.model.guild or in_village) and self.model.row(m.CAPABILITY)[0][5] and not self.pending:
            self.village.Enable()
            if not R1:
                self.village_label.SetPackedFontColor(native_color(INK))
        else:
            self.village.Disable()
            if not R1:
                self.village_label.SetPackedFontColor(native_color(MUTED))
        if not available() or not self.model.rows(m.CAPABILITY):
            self.page.text(0, 0, "Cech", width, INK, ROLE_TITLE)
            self.page.text(0, 36, "Načítání cechu...", width, DIM)
            return
        if not self.model.guild:
            self.without_guild()
            return
        title, subtitle = PAGES.get(self.currentPage, ("Cech", None))
        if self.currentPage == "settings" and locked("profile"):
            subtitle = "Rada, nástěnka a vedení cechu"
        if subtitle is None:
            subtitle = name + (" | přehled cechu" if locked("materials") else " | společné zásoby a rozvoj cechu")
            if self.currentPage == "members":
                members = self.model.rows(m.MEMBER)
                subtitle = "%s členů | %s online" % (len(members), sum(1 for row in members if row[0][7]))
        disband = self.model.disband_at()
        if disband:
            subtitle = "Cech bude rozpuštěn %s. Vůdce to může zrušit ve Správě cechu." % m.moment(disband)
        self.page.text(0, 0, title, width - 130, INK, ROLE_TITLE)
        self.page.text(0, 34, subtitle, width - 130, RED if disband else DIM)
        self.page.action("Obnovit", width - 100, 6, lambda: self.request(m.SNAPSHOT), not self.pending, width=100, height=24)
        self.page.rule(0, 62, width, 0xff3a2e24)
        render = getattr(self, "page_" + self.currentPage, self.page_overview)
        render(width, height)
        if self.scroll and offset:
            self.scroll.scroll.SetPos(float(min(offset, self.scroll.maximum)) / max(1, self.scroll.maximum))

    def render_sidebar(self):
        bar = self.sidebar
        bar.clear()
        values, name, body = self.model.row(m.SUMMARY)
        h = bar.design_height
        small = self.design_height < 650
        loaded = bool(self.model.rows(m.CAPABILITY))
        guild = bool(self.model.guild)
        bar.text(94, 8, name or ("Bez cechu" if loaded else "Cech"), 176, GOLD, ROLE_FIGURE, "center")
        nav_top = 150
        if guild:
            top = 40 if small else 44
            bar.panel(56, top, 76, 64 if small else 92)
            # Display the guild's real mark. The sample wolf banner is not an emblem.
            mark = bar.keep(ui.MarkBox())
            mark.SetParent(bar)
            mark.SetPosition(px(70), px(top + (13 if small else 27)))
            mark.SetIndex(self.model.guild)
            mark.SetScale(3 * SCALE)
            mark.Show()
            y = top + (74 if small else 104)
            if locked("chronicle"):
                # The chronicle (level progress from materials) comes after the start: the level only.
                bar.text(94, y, "ÚROVEŇ CECHU " + m.number(values[1]), 176, GOLD, fontconfig.ROLE_SECTION, "center")
            else:
                bar.text(94, y, "KRONIKA | ÚROVEŇ " + m.number(values[1]), 176, GOLD, fontconfig.ROLE_SECTION, "center")
                needed = self.model.level_need()
                bar.gauge(26, y + 22, 136, values[2] if values[1] < 20 else 1, needed if values[1] < 20 else 1, 5, T.BRONZE)
            nav_top = y + 40
        elif loaded and not R1:
            bar.image("pennant_93x171", 48, 40, 93, 171)
            bar.text(94, 222, "Cech tě čeká", 176, DIM, align="center")
        if guild or not loaded:
            step = max(30, min(39, (h - 70 - nav_top) // 9))
            nav_top = max(nav_top, h - 72 - 9 * step)
            for index, (key, label) in enumerate(NAVIGATION):
                y = nav_top + index * step
                selected = self.currentPage == key
                closed = locked(key)
                role = fontconfig.ROLE_CONTROL if selected else fontconfig.ROLE_BODY
                bar.keep(Flat(bar, px(5), px(y), span(5, 176), span(y, step - 3), lambda k=key: self.SelectPage(k),
                    label, "plain", selected, guild and not closed, px(50), role, accent=True,
                    hint=LOCKED_HINT if closed else None))
                icon = bar.image("nav_" + NAV_ICONS[index] + "_28x28", 12, y + (step - 3 - 28) // 2)
                if closed:
                    # dimmed icon, the padlock on its lower right corner (the label keeps its room)
                    icon.SetAlpha(0.35)
                    bar.keep(lock_image(bar, px(12 + 28) - 10, px(y + (step - 3 - 28) // 2 + 28) - 13))
            bar.rule(5, nav_top - 8, 176, 0xff3a2e24)
            bar.rule(5, h - 68, 176, 0xff3a2e24)
        if guild:
            members = self.model.rows(m.MEMBER)
            bar.text(12, h - 60, "%s online / %s členů" % (sum(row[0][7] for row in members), len(members)), 176, GREEN)
            bar.icon_button("action_settings_28x28", 12, h - 34, lambda: self.SelectPage("settings"), "Správa cechu")
            bar.icon_button("action_messages_28x28", 77, h - 34, self.messages, "Cechovní zprávy")
        bar.icon_button("action_help_28x28", 142, h - 34, self.help_dialog, "Nápověda a pojmy")

    def messages(self):
        if self.interface:
            if self.dialog:
                self.dialog.Close()
            self.interface.unifiedMessengerRouter.Open(self.model.row(m.SUMMARY)[1], "guild:" + str(self.model.guild))

    def help_dialog(self):
        # The glossary sets the height: Zavřít (height - 36) stays below the last paragraph instead of covering
        # it. A low screen first widens the dialog (fewer lines), only then the height is capped.
        screen = max(620, int((wndMgr.GetScreenHeight() - 38) / SCALE))
        for width in (700, 860, 1000):
            height = max(620, 88 + sum(30 + widgets.block_height(text, width - 48) for term, text in HELP) + 48)
            if height <= screen:
                break
        d = self.popup("Nápověda | pojmy cechu", min(height, screen), width)
        d.text(24, 46, "Jak cech funguje", width - 48, INK, ROLE_TITLE)
        y = 88
        for term, text in HELP:
            d.text(24, y, term, width - 48, GOLD, fontconfig.ROLE_CONTROL)
            y += 30 + d.block(24, y + 22, text, width - 48, DIM)
        return d

    # ------------------------------------------------------------------ mark
    def open_mark_dialog(self):
        if not self.model.guild or not self.leader():
            self.message("Znak cechu může změnit jen vůdce.")
            return False
        if self.model.row(m.SUMMARY)[0][1] < 1:
            self.message("Znak cechu lze nahrát od úrovně 1.")
            return False
        if not self.mark_dialog:
            self.mark_dialog = uiUploadMark.MarkSelectDialog()
            self.mark_dialog.SAFE_SetSelectEvent(self.upload_mark)
        self.mark_dialog.Open()
        return True

    def upload_mark(self, filename):
        if not self.model.guild or not self.leader() or self.model.row(m.SUMMARY)[0][1] < 1:
            return False
        result = net.UploadMark("upload/" + filename)
        if result in (net.ERROR_MARK_UPLOAD_NEED_RECONNECT, net.ERROR_MARK_CHECK_NEED_RECONNECT):
            self.message("Pro nahrání znaku se znovu přihlas a zkus to znovu.")
        elif result != net.ERROR_NONE:
            self.message("Znak se nepodařilo nahrát. Zkontroluj obrázek 32x32 px a připojení.")
        else:
            self.message("Znak byl odeslán. Jeho zobrazení se může chvíli obnovovat.", GREEN)
            # the footer line is easy to miss behind the picker; the chat keeps it
            chat.AppendChat(chat.CHAT_TYPE_INFO, "Znak cechu byl nahrán. Pokud se hned neukáže, přihlas se znovu.")
        return result

    # ------------------------------------------------------------------ overview
    def material_strip(self, y=76):
        width = self.page.design_width
        for kind, label in enumerate(getattr(localeInfo, key) for key in m.MATERIALS):
            x, w = kind * (width + 16) // 3, (width - 32) // 3
            self.page.panel(x, y, w, 66)
            self.page.image(m.MATERIAL_ICONS[kind] + "_32x42", x + 14, y + 12)
            self.page.text(x + 60, y + 10, label, w - 66, DIM)
            self.page.text(x + 60, y + 32, m.number(self.model.row(m.BALANCE)[0][kind]), w - 66, INK, ROLE_FIGURE)

    def featured_passives(self):
        ranked = sorted(self.model.passive_ids(), key=lambda value: (-self.model.rank(value), value))
        return ranked[:3] if ranked and self.model.rank(ranked[0]) else (5, 6, 7)

    def page_overview(self, w, h):
        if not locked("materials"):
            return self.page_overview_full(w, h)
        self.overview_strip()
        # Materials, passives, the common goal and the chronicle come after the start.
        self.page.locked_panel(0, 170, w, 148, "PASIVNÍ SCHOPNOSTI",
            "Společné bonusy cechu za suroviny. Přijdou s první větší aktualizací.")
        left = (w * 3) // 5
        self.page.locked_panel(0, 336, left, 190, "SPOLEČNÝ CÍL",
            "Společné úkoly s termínem a kontrakty. Přijdou s první větší aktualizací.")
        self.page.locked_panel(left + 16, 336, w - left - 16, 190, "KRONIKA A MATERIÁLY",
            "Úroveň z materiálů, deník a relikvie.")

    def page_overview_full(self, w, h):
        self.material_strip()
        self.page.header("PASIVNÍ SCHOPNOSTI", 0, 156, w)
        for index, identifier in enumerate(self.featured_passives()):
            x, width = index * (w + 16) // 3, (w - 32) // 3
            rank = self.model.rank(identifier)
            catalog = self.model.catalog(identifier, max(1, rank))
            if not catalog:
                continue
            self.page.row(x, 194, width, 124, lambda i=identifier: self.select_passive(i))
            self.page.image(m.PASSIVE_ICONS[identifier], x + 14, 206, 41, 41)
            self.page.text(x + 64, 208, catalog[1], width - 72, GOLD, fontconfig.ROLE_CONTROL)
            self.page.text(x + 64, 232, "Stupeň " + m.ROMAN[rank], width - 72, DIM)
            self.page.text(x + 16, 262, m.effect(identifier, catalog[0][2] if rank else 0), width - 60, INK, ROLE_FIGURE)
            self.page.text(x + width - 16, 264, ">", 20, GOLD, ROLE_FIGURE, "right")
            self.page.pips(x + 16, 302, width - 32, rank, height=5)
        left = (w * 3) // 5
        goal, goal_name, goal_body = self.model.row(m.GOAL)
        now = self.model.now(app.GetTime())
        remaining = ""
        if goal[0] and not goal[3] and now < goal[2]:
            days = (goal[2] - now + 86399) // 86400
            remaining = " | ZBÝVÁ %s %s" % (days, "DEN" if days == 1 else ("DNY" if days < 5 else "DNÍ"))
        self.page.header("SPOLEČNÝ CÍL" + remaining, 0, 336, left)
        for kind in range(3):
            y = 378 + kind * 54
            self.page.image(m.MATERIAL_ICONS[kind] + "_25x32", 14, y)
            self.page.text(52, y + 1, getattr(localeInfo, m.MATERIALS[kind]), left - 200, INK, fontconfig.ROLE_CONTROL)
            self.page.text(left - 16, y + 1, "%s / %s" % (m.number(goal[7 + kind]), m.number(goal[4 + kind])) if goal[4 + kind] else "Neaktivní",
                150, GOLD, fontconfig.ROLE_CONTROL, "right")
            self.page.gauge(52, y + 26, left - 68, goal[7 + kind], goal[4 + kind])
        x = left + 16
        self.page.header("KRONIKA CECHU", x, 336, w - x)
        self.page.image("chronicle_83x100", x + 12, 376)
        summary = self.model.row(m.SUMMARY)[0]
        self.page.text(x + 110, 384, "Úroveň " + m.number(summary[1]), w - x - 116, GOLD, ROLE_TITLE)
        needed = self.model.level_need()
        self.page.text(x + 110, 418, "%s / %s" % (m.number(summary[2]), m.number(needed)) if summary[1] < 20 else "Nejvyšší úroveň", w - x - 116, DIM)
        self.page.gauge(x + 110, 444, w - x - 126, summary[2] if summary[1] < 20 else 1, needed if summary[1] < 20 else 1)
        self.page.row(x, 492, w - x, 34, lambda: self.SelectPage("chronicle", 1), style="plain")
        self.page.text(x + 14, 499, "Mandát " + m.number(summary[3]), w - x - 60, GOLD, fontconfig.ROLE_CONTROL)
        self.page.text(w - 14, 496, ">", 20, GOLD, ROLE_FIGURE, "right")

    def overview_strip(self, y=76):
        """Name, leader, members and the village in the place of the material strip."""
        width = self.page.design_width
        values, name, body = self.model.row(m.SUMMARY)
        members = self.model.rows(m.MEMBER)
        leader = self.model.leader_name()
        me = self.model.member(self.pid())
        level = max(1, values[1])
        cells = (("Cech", name), ("Vůdce", leader),
            ("Členové", "%s (%s online)" % (self.model.members_text(len(members), " / "), sum(1 for r in members if r[0][7]))),
            ("Tvoje hodnost", m.ROLES[me[0][1]] if me and me[0][1] < 3 else "-"))
        for index, (label, value) in enumerate(cells):
            x, w = index * (width + 16) // 4, (width - 48) // 4
            self.page.panel(x, y, w, 66)
            self.page.text(x + 14, y + 10, label, w - 24, DIM)
            self.page.text(x + 14, y + 34, value, w - 24, INK, fontconfig.ROLE_CONTROL)
        disband = self.model.disband_at()
        hint = ("Cech bude rozpuštěn %s. Vůdce to může zrušit ve Správě cechu." % m.moment(disband)) if disband else \
            "Do soukromé vesnice vede tlačítko dole. Duši bosse tam vyvoláš pravým klikem na ni."
        self.page.text(0, 146 - 2, hint, width, RED if disband else DIM, ROLE_CAPTION)

    # ------------------------------------------------------------------ passives
    def select_passive(self, identifier):
        self.selected_passive = identifier
        self.SelectPage("passives")

    def page_passives(self, w, h):
        self.tabs(("Pasivní schopnosti", "Stupně a postup"))
        ids = shown_passives(self.model)
        learned = sum(1 for value in ids if self.model.rank(value))
        self.page.text(w, 78, "%s / %s vylepšených" % (learned, len(ids)), 200, DIM, align="right")
        if self.selected_passive not in ids and ids:
            self.selected_passive = ids[0]
        identifier = self.selected_passive
        rank = self.model.rank(identifier)
        catalog = self.model.catalog(identifier, max(1, rank))
        if not catalog:
            return
        if self.tab == 1:
            self.page.image(m.PASSIVE_ICONS[identifier], 0, 112, 41, 41)
            self.page.text(54, 114, catalog[1], w - 60, GOLD, fontconfig.ROLE_LARGE_BOLD)
            self.page.text(54, 138, self.model.description(identifier), w - 60, DIM)
            self.page.table_header(0, 168, w)
            for x, label, align in ((18, "Stupeň", "left"), (110, "Bonus", "left"), (250, "Vyžaduje", "left"), (w - 18, "Cena (úlomky / ruda / fragmenty)", "right")):
                self.page.text(x, 175, label, 300, GOLD, ROLE_CAPTION, align)
            for level in range(1, 6):
                data = self.model.catalog(identifier, level)[0]
                y = 200 + (level - 1) * 62
                self.page.panel(0, y, w, 56, level == rank)
                self.page.text(24, y + 17, m.ROMAN[level], 60, GOLD, fontconfig.ROLE_LARGE_BOLD)
                self.page.text(110, y + 19, m.effect(identifier, data[2]), 130, GREEN if level <= rank else INK, fontconfig.ROLE_CONTROL)
                self.page.text(250, y + 19, (localeInfo.GUILD_V2_GUILD_LEVEL % m.number(data[3])) if data[3] else T.DASH, 150, DIM)
                self.page.text(w - 18, y + 19, " / ".join(m.number(v) for v in data[4:7]), w - 420, GOLD, align="right")
            return
        compact = w < 690
        left = w if compact else w - 362
        def draw(canvas, value, y, width):
            current = self.model.rank(value)
            data = self.model.catalog(value, max(1, current))
            chosen = value == identifier and not compact
            canvas.row(0, y, width, 64, lambda v=value: self.compact_passive(v) if compact else self.select_passive(v), chosen)
            canvas.image(m.PASSIVE_ICONS[value], 12, y + 11, 41, 41)
            canvas.text(66, y + 11, data[1], width - 150, GOLD if chosen else INK, fontconfig.ROLE_CONTROL)
            canvas.text(66, y + 36, self.model.description(value), width - 150, DIM, ROLE_CAPTION)
            canvas.text(width - 44, y + 9, m.ROMAN[current], 60, GOLD if current else MUTED, fontconfig.ROLE_LARGE_BOLD, "center")
            canvas.pips(width - 76, y + 44, 64, current, height=4)
        self.list(ids, 112, min(488, h - 112), 70, draw, left)
        if compact:
            return
        x = left + 16
        extra = 42 * max(0, len(self.passive_costs(identifier, rank + 1)) - 3)
        self.page.SetSize(self.page.GetWidth(), max(self.page.GetHeight(), px(112 + 476 + extra)))
        self.passive_detail(self.page, x, 112, w - x, identifier, 476 + extra)

    def compact_passive(self, identifier):
        self.selected_passive = identifier
        if R1:
            # R1: the detail is its own dialog beside the window, sized to its content (uiguildv2r1)
            return self.passive_popup_r1(identifier)
        if not self.model.catalog(identifier, max(1, self.model.rank(identifier))):
            return None
        extra = 42 * max(0, len(self.passive_costs(identifier, self.model.rank(identifier) + 1)) - 3)
        d = self.popup("Pasivní schopnost", 535 + extra)
        self.passive_detail(d, 17, 34, d.design_width - 34, identifier, 432 + extra)

    def passive_detail(self, canvas, x, y, width, identifier, height):
        rank = self.model.rank(identifier)
        current = self.model.catalog(identifier, max(1, rank))
        upcoming = self.model.catalog(identifier, min(5, rank + 1)) or current
        if not current:
            return
        canvas.panel(x, y, width, height)
        canvas.header("VYLEPŠENÍ SCHOPNOSTI", x, y, width)
        canvas.image(m.PASSIVE_ICONS.get(identifier, "passive_rank_41x41"), x + 16, y + 44, 48, 48)
        canvas.text(x + 78, y + 44, current[1], width - 90, GOLD, fontconfig.ROLE_LARGE_BOLD)
        canvas.text(x + 78, y + 70, rank_step(rank), width - 90, DIM)
        top = y + 104 + canvas.block(x + 16, y + 104, self.model.description(identifier), width - 32) + 8
        canvas.text(x + 16, top, m.effect(identifier, current[0][2] if rank else 0), 150, INK, ROLE_FIGURE)
        if rank < 5:
            canvas.text(x + width // 2, top + 2, T.ARROW, 30, DIM, ROLE_FIGURE, "center")
        canvas.text(x + width - 16, top, m.effect(identifier, upcoming[0][2]) if rank < 5 else "Maximum", 150, GREEN, ROLE_FIGURE, "right")
        canvas.pips(x + 16, top + 34, width - 32, rank, height=5)
        build = self.model.building()
        if build and build[0] == identifier:
            now = self.model.now(app.GetTime())
            canvas.text(x + 16, top + 60, localeInfo.GUILD_V2_BUILDING % (m.ROMAN[build[1]],
                m.moment(build[3]), m.duration(max(0, build[3] - now))), width - 32, GOLD)
            canvas.gauge(x + 16, top + 90, width - 32, max(0, min(build[3], now) - build[2]), max(1, build[3] - build[2]), 6, T.BRONZE)
            # owner C13 (server b00e2d04): the build is not sped up, it runs its full time
            return
        if rank == 5:
            canvas.text(x + 16, top + 60, "Nejvyšší stupeň je dosažen.", width - 32, GOLD)
            return
        costs = self.passive_costs(identifier, rank + 1)
        self.cost_table(canvas, x + 12, top + 54, width - 24, costs)
        reason = self.upgrade_reason(upcoming)
        canvas.block(x + 14, top + 82 + len(costs) * 42, reason or (localeInfo.GUILD_V2_UPGRADE_COST %
            yang(self.model.rank_yang(identifier, rank + 1))), width - 28,
            GOLD if reason else DIM, ROLE_CAPTION)
        canvas.button("Vylepšit na " + m.ROMAN[rank + 1], x + width - 186, y + height - 40,
            lambda: self.upgrade_dialog(identifier), not reason, tooltip=reason)

    def upgrade_reason(self, upcoming):
        if not self.model.can(self.pid(), 16 | 32):
            return "Nemáš právo vylepšovat schopnosti."
        build = self.model.building()
        if build and self.model.now(app.GetTime()) < build[3]:
            data = self.model.catalog(build[0], build[1])
            return localeInfo.GUILD_V2_BUSY % (data[1] if data else localeInfo.GUILD_V2_OTHER_PASSIVE)
        if self.model.row(m.SUMMARY)[0][1] < upcoming[0][3]:
            return localeInfo.GUILD_V2_NEED_LEVEL % upcoming[0][3]
        if any(have < cost for label, icon, cost, have in self.rank_costs(upcoming[0][0], upcoming[0][1])):
            return "Chybí materiál, viz červená čísla."
        if self.model.row(m.BALANCE)[0][3] < self.model.rank_yang(upcoming[0][0], upcoming[0][1]):
            return localeInfo.GUILD_V2_NO_YANG_PRICE % yang(self.model.rank_yang(upcoming[0][0], upcoming[0][1]))
        if self.pending:
            return "Čeká se na potvrzení předchozí akce."
        return None

    def material_costs(self, costs):
        """Cost rows (label, icon, cost, in the guild) of the catalog materials: metin shards, ore, soul fragments."""
        balance = self.model.row(m.BALANCE)[0]
        return [(getattr(localeInfo, m.MATERIALS[kind]), m.MATERIAL_ICONS[kind], cost, balance[kind]) for kind, cost in enumerate(costs)]

    def growth_material(self, field):
        """Label and icon of a guild growth material: its 'Zásoby cechu' item when the panel data has one, else its
        part of the locale line GUILD_V2_ROW_GROWTH ("Jádra / šupiny / dřevo") without an icon."""
        for key, source, value, label, icon in getattr(m, "STOCK_PANEL", ()):
            if source == "stock" and value == field:
                return getattr(localeInfo, label, key), icon
        names = getattr(localeInfo, "GUILD_V2_ROW_GROWTH", "").split(" / ")
        return (names[m.GROWTH.index(field)] if len(names) == len(m.GROWTH) else field), ""

    def rank_costs(self, identifier, rank):
        """Every material the server charges for a passive rank (common/guild_v2/domain.cpp Upgrade): the catalog
        price and the guild growth price of the rank (Balance t1 "rankgrow": golem cores, fish scales, guild wood,
        share/conf/guild_v2_growth_v1.json rank_costs), a growth material only when the rank asks for it. Owner
        16. 10. 2026: scales and wood were charged but missing in the passive detail."""
        data = self.model.catalog(identifier, rank)
        rows = self.material_costs(data[0][4:7]) if data else []
        growth = self.model.growth()
        if growth and 1 <= rank <= len(growth["rank_grow"]):
            for field, cost in zip(m.GROWTH, growth["rank_grow"][rank - 1]):
                if cost:
                    label, icon = self.growth_material(field)
                    rows.append((label, icon, cost, growth[field]))
        return rows

    def cost_table(self, canvas, x, y, w, costs, after=False):
        """Table of cost rows (label, icon, cost, in the guild), one row each."""
        canvas.table_header(x, y, w, 26)
        canvas.text(x + 10, y + 6, "Materiál", w - 146, GOLD, ROLE_CAPTION)
        canvas.icon_button("action_help_28x28", x + 90, y - 1, self.material_sources_dialog,
            localeInfo.GUILD_V2_PASSIVE_MATERIALS_HINT)
        canvas.text(x + w - 86, y + 6, "Cena", 70, GOLD, ROLE_CAPTION, "right")
        canvas.text(x + w - 10, y + 6, "Po platbě" if after else "V cechu", 70, GOLD, ROLE_CAPTION, "right")
        for kind, (label, icon, cost, balance) in enumerate(costs):
            yy = y + 26 + kind * 42
            coin = icon == YANG_ICON
            if coin:
                canvas.image(icon, x + 8, yy + 11, 20, 20)
            elif icon:
                canvas.image(icon + "_25x32", x + 6, yy + 5)
            # yang reaches billions: the short form fits the 70 wide columns ("13,5 mld."), what the guild has rounded down
            price, have = (m.short_yang, lambda value: m.short_yang(value, True)) if coin else (m.number, m.number)
            widgets.whole_text(canvas, x + 38, yy + 13, label, w - 220)   # never into the Cena column
            canvas.text(x + w - 86, yy + 13, price(cost), 70, INK, fontconfig.ROLE_CONTROL, "right")
            canvas.text(x + w - 10, yy + 13, have(balance - cost if after and balance >= cost else balance), 70,
                # the green / red of every item price (root/ownedcount.py)
                ownedcount.GREEN if balance >= cost else ownedcount.SHORT, fontconfig.ROLE_CONTROL, "right")
            canvas.bar(x + 6, yy + 41, w - 12, 1, 0xff32281e)

    def upgrade_dialog(self, identifier):
        rank = self.model.rank(identifier)
        if rank >= 5:
            return
        data = self.model.catalog(identifier, rank + 1)
        current = self.model.catalog(identifier, max(1, rank))
        if not data or not current:
            return
        costs = self.rank_costs(identifier, rank + 1)
        affordable = all(have >= cost for label, icon, cost, have in costs)
        extra = 42 * max(0, len(costs) - 3)    # a row for each growth material of the rank (scales, wood, cores)
        d = self.popup(localeInfo.GUILD_V2_UPGRADE_TITLE if affordable else localeInfo.GUILD_V2_NO_MATERIAL_TITLE,
            456 + extra)
        d.image(m.PASSIVE_ICONS.get(identifier, "passive_rank_41x41"), 24, 46, 48, 48)
        d.text(88, 46, data[1], 440, GOLD, ROLE_TITLE)
        d.text(88, 78, rank_step(rank), 440, DIM)
        d.text(24, 118, self.model.description(identifier), 300, INK)
        d.text(536, 114, "%s %s %s" % (m.effect(identifier, current[0][2] if rank else 0), T.ARROW,
            m.effect(identifier, data[0][2])), 220, GREEN, ROLE_FIGURE, "right")
        self.cost_table(d, 24, 150, 512, costs, True)
        price = self.model.rank_yang(identifier, rank + 1)
        treasury = self.model.row(m.BALANCE)[0][3]
        d.text(24, 312 + extra, localeInfo.GUILD_V2_TREASURY_PRICE % (yang(price), yang(treasury)), 512,
            GREEN if treasury >= price else RED, fontconfig.ROLE_CONTROL)
        reason = self.upgrade_reason(data)
        d.primary(localeInfo.GUILD_V2_UPGRADE_TO % m.ROMAN[rank + 1], lambda: d.submit(m.UPGRADE, (identifier, rank, 0)),
            reason=reason)
        if R1:
            d.place_beside(self)    # where the passive detail was (owner 16. 10. 2026: not over the guild window)

    def passive_costs(self, identifier, rank):
        """The cost table of a passive rank: every material (rank_costs) and the treasury Yang the server charges with
        them (Catalog t1 "yang N", progression RankYang 675 mil. .. 13,5 mld.), red while the treasury is short.
        Owner 21. 10. 2026: the Yang was charged but the passive window did not show it."""
        rows = self.rank_costs(identifier, rank)
        price = self.model.rank_yang(identifier, rank)
        if price:
            rows.append(("Yang", YANG_ICON, price, self.model.row(m.BALANCE)[0][3]))
        return rows


    def speedup_open(self):
        """Owner C13 (server b00e2d04 refuses Upgrade v2 = 1): no speed-up action anywhere in the guild window."""
        return False


    def speedup_costs(self, build):
        data = self.model.catalog(build[0], build[1])
        return tuple(m.speedup_cost(value) for value in data[0][4:7]) if data else (0, 0, 0)

    def speedup_reason(self, build, now):
        if not self.model.can(self.pid(), 16 | 32):
            return localeInfo.GUILD_V2_NO_UPGRADE_RIGHT
        identifier, rank, start, end, full = build
        if now >= end:
            return localeInfo.GUILD_V2_BUILD_DONE
        if end <= start + full * m.SPEEDUP_FLOOR_PERCENT // 100:
            return localeInfo.GUILD_V2_SPEEDUP_FLOOR
        if not all(self.model.row(m.BALANCE)[0][i] >= cost for i, cost in enumerate(self.speedup_costs(build))):
            return localeInfo.GUILD_V2_SPEEDUP_NO_MATERIAL
        if self.pending:
            return localeInfo.GUILD_V2_WAITING
        return None

    def speedup_dialog(self):
        build = self.model.building()
        if not build:
            return
        identifier, rank, start, end, full = build
        data = self.model.catalog(identifier, rank)
        now = self.model.now(app.GetTime())
        d = self.popup(localeInfo.GUILD_V2_SPEEDUP_TITLE, 400)
        d.image(m.PASSIVE_ICONS.get(identifier, "passive_rank_41x41"), 24, 46, 48, 48)
        d.text(88, 46, data[1] if data else localeInfo.GUILD_V2_PASSIVE, 440, GOLD, ROLE_TITLE)
        step = full * m.SPEEDUP_PERCENT // 100
        new_end = max(start + full * m.SPEEDUP_FLOOR_PERCENT // 100, end - step)
        d.text(88, 78, localeInfo.GUILD_V2_SPEEDUP_LEFT % (m.duration(max(0, end - now)), m.duration(max(0, new_end - now))),
            440, DIM)
        self.cost_table(d, 24, 120, 512, self.material_costs(self.speedup_costs(build)), True)
        d.text(24, 286, localeInfo.GUILD_V2_SPEEDUP_RULE, 512, DIM, ROLE_CAPTION)
        reason = self.speedup_reason(build, now)
        d.primary(localeInfo.GUILD_V2_SPEEDUP, lambda: d.submit(m.UPGRADE, (identifier, rank - 1, m.SPEEDUP)), reason=reason)

    # ------------------------------------------------------------------ materials
    def page_materials(self, w, h):
        self.tabs(("Zásoby", "Příspěvky členů", "Historie"))
        if self.tab:
            self.history_list(w, h)
            return
        goal, balance = self.model.row(m.GOAL)[0], self.model.row(m.BALANCE)[0]
        self.page.table_header(0, 112, w)
        self.page.text(16, 119, "Materiál", 200, GOLD, ROLE_CAPTION)
        self.page.text(w - 220, 119, "V cechu", 160, GOLD, ROLE_CAPTION, "right")
        self.page.text(w - 24, 119, "Během cíle", 160, GOLD, ROLE_CAPTION, "right")
        for kind in range(3):
            y = 146 + kind * 92
            self.page.panel(0, y, w, 86)
            self.page.image(m.MATERIAL_ICONS[kind] + "_44x62", 20, y + 12)
            self.page.text(84, y + 20, getattr(localeInfo, m.MATERIALS[kind]), w - 400, GOLD, fontconfig.ROLE_LARGE_BOLD)
            self.page.text(84, y + 48, MATERIAL_SOURCES[kind], w - 400, DIM, ROLE_CAPTION)
            self.page.text(w - 220, y + 28, m.number(balance[kind]), 200, INK, ROLE_FIGURE, "right")
            self.page.text(w - 24, y + 28, "+" + m.number(goal[7 + kind]), 160, GREEN, ROLE_FIGURE, "right")
        self.page.header("Další cechovní zůstatky", 0, 430, w)
        self.page.image("mandate_31x37", 16, 470)
        self.page.text(60, 478, "Mandát", 200, INK)
        self.page.text(w // 2 - 30, 474, m.number(self.model.row(m.SUMMARY)[0][3]), 120, GOLD, ROLE_FIGURE, "right")
        self.page.text(w // 2 + 10, 478, "Yang v pokladně", 200, INK)
        self.page.text(w - 24, 474, m.number(balance[3]), w // 2 - 200, GOLD, ROLE_FIGURE, "right")
        self.page.text(0, 524, "Materiály cechu zůstávají. Do cíle se počítají jen nově získané.", w, DIM, ROLE_CAPTION)

    # ------------------------------------------------------------------ goals
    def page_goals(self, w, h):
        self.tabs(("Aktuální cíl", "Kontrakty", "Historie cílů"))
        if self.tab == 2:
            self.history_list(w, h)
            return
        if self.tab == 1:
            targets = self.model.row(m.CONTRACTS)[0]
            self.page.text(0, 112, "Kontrakty pro příští cíl", w, GOLD, fontconfig.ROLE_LARGE_BOLD)
            self.page.text(0, 138, "Vůdce je převezme při nastavení nového cíle. Aktuální cíl se nemění.", w, DIM)
            for kind in range(3):
                y = 170 + kind * 100
                self.page.panel(0, y, w, 90, bool(targets[kind]))
                self.page.image(m.MATERIAL_ICONS[kind] + "_44x62", 18, y + 14)
                self.page.text(84, y + 18, GOAL_TITLES[kind], w - 300, GOLD, fontconfig.ROLE_LARGE_BOLD)
                self.page.text(84, y + 46, GOAL_HINTS[kind], w - 300, DIM, ROLE_CAPTION)
                self.page.text(w - 20, y + 30, m.number(targets[kind]) if targets[kind] else "Nevybráno", 200,
                    GOLD if targets[kind] else MUTED, ROLE_FIGURE, "right")
            self.page.primary("Vybrat kontrakty", w - 170, 560, self.contracts_dialog,
                None if self.can(2) else ("Čeká se na potvrzení." if self.pending else "Chybí právo Volba kontraktů."))
            return
        goal, name, body = self.model.row(m.GOAL)
        self.page.text(0, 112, name or "Zatím není nastavený cíl", w, GOLD, fontconfig.ROLE_LARGE_BOLD)
        now = self.model.now(app.GetTime())
        if goal[0]:
            state = "Splněno" if goal[3] else ("Ukončeno" if now >= goal[2] else "Zbývá " + m.duration(goal[2] - now))
            self.page.text(0, 138, m.moment(goal[1]) + " - " + m.moment(goal[2]) + " | " + state, w, DIM)
        else:
            self.page.text(0, 138, "Cíl nastavuje vůdce cechu. Počítají se do něj nově získané materiály.", w, DIM)
        for kind in range(3):
            y = 170 + kind * 104
            active = bool(goal[4 + kind])
            self.page.panel(0, y, w, 96)
            self.page.image(m.MATERIAL_ICONS[kind] + "_44x62", 18, y + 16)
            self.page.text(84, y + 14, GOAL_TITLES[kind], w - 300, GOLD, fontconfig.ROLE_LARGE_BOLD)
            self.page.text(84, y + 42, GOAL_HINTS[kind], w - 300, DIM, ROLE_CAPTION)
            self.page.text(w - 20, y + 14, "%s / %s" % (m.number(goal[7 + kind]), m.number(goal[4 + kind])) if active else "Neaktivní",
                220, GOLD if active else MUTED, ROLE_FIGURE, "right")
            self.page.gauge(84, y + 72, w - 104, goal[7 + kind], goal[4 + kind])
        self.page.text(0, 492, "Do cíle se počítají nově získané materiály, zásoby se nespotřebují.", w, DIM, ROLE_CAPTION)
        active = goal[0] and now < goal[2]
        reason = None
        if not self.leader():
            reason = "Cíl nastavuje jen vůdce."
        elif active and goal[3]:
            reason = "Cíl je splněný, nový nastavíš po jeho konci."
        elif self.pending:
            reason = "Čeká se na potvrzení."
        self.page.primary("Upravit cíl" if active else "Nastavit cíl", w - 170, 560, lambda: self.goal_dialog(bool(active)), reason)

    def contracts_dialog(self):
        d = self.popup("Volba kontraktů", 380)
        current = self.model.row(m.CONTRACTS)[0]
        fields = []
        d.text(24, 46, "Kontrakty pro příští cíl", 512, INK, ROLE_TITLE)
        d.text(24, 80, "Připrav množství pro příští cíl. Nula kontrakt vyřadí.", 512, DIM, multiline=True)
        for kind in range(3):
            y = 128 + kind * 50
            d.image(m.MATERIAL_ICONS[kind] + "_25x32", 26, y - 8)
            d.text(66, y, getattr(localeInfo, m.MATERIALS[kind]), 260)
            fields.append(d.edit(338, y, 168, 19, current[kind], True))
        def submit():
            try:
                values = tuple(m.positive(field.GetText(), True) for field in fields)
                if not any(values):
                    raise ValueError("Vyber alespoň jeden kontrakt.")
            except ValueError as error:
                d.message.SetText(str(error))
                return
            d.submit(m.SELECT_CONTRACTS, values)
        d.primary("Uložit volbu", submit)

    def goal_dialog(self, edit=False):
        d = self.popup("Upravit cechovní cíl" if edit else "Nastavit cechovní cíl", 490)
        goal, name, body = self.model.row(m.GOAL)
        d.text(24, 44, "Společný cíl cechu", 512, INK, ROLE_TITLE)
        d.text(24, 78, "Nastavuje vůdce cechu", 512, DIM)
        d.text(24, 112, "Název cíle", 170, GOLD)
        title = d.edit(197, 112, 330, 64, name if edit else "")
        d.text(24, 158, "Délka cíle", 170, GOLD)
        days = (goal[2] - goal[1]) // 86400 if edit else 7
        amount = d.edit(197, 158, 108, 19, days, True)
        weeks = [False]
        def choose(value):
            weeks[0] = value
            day_button.SetSelected(not value)
            week_button.SetSelected(value)
        day_button = d.action("Dny", 330, 154, lambda: choose(False), width=96, selected=True)
        week_button = d.action("Týdny", 430, 154, lambda: choose(True), width=96)
        targets = []
        selected_contracts = self.model.row(m.CONTRACTS)[0][:3]
        proposed = selected_contracts if any(selected_contracts) else (100, 100, 20)
        d.text(24, 206, "Kontrakty | nula znamená nevybraný kontrakt", 512, DIM)
        for kind in range(3):
            y = 248 + kind * 48
            d.image(m.MATERIAL_ICONS[kind] + "_25x32", 26, y - 8)
            d.text(66, y, getattr(localeInfo, m.MATERIALS[kind]), 230)
            targets.append(d.edit(335, y, 170, 19, goal[4 + kind] if edit else proposed[kind], True))
        d.text(24, 398, "Začátek se nastaví sám. 1 týden = 7 dní.", 512, DIM, ROLE_CAPTION)
        if edit:
            d.text(24, 420, "Délku a množství jde jen zvýšit. Příspěvky zůstávají.", 512, DIM, ROLE_CAPTION)
        def submit():
            try:
                values = (m.positive(amount.GetText()), int(weeks[0])) + tuple(m.positive(field.GetText(), True) for field in targets)
                if not any(values[2:]):
                    raise ValueError("Vyber alespoň jeden kontrakt.")
                if not title.GetText().strip():
                    raise ValueError("Zadej název cíle.")
            except ValueError as error:
                d.message.SetText(str(error))
                return
            d.submit(m.EDIT_GOAL if edit else m.CREATE_GOAL, values, title.GetText().strip())
        d.primary("Potvrdit cíl", submit)

    # ------------------------------------------------------------------ treasury
    def material_sources_dialog(self):
        d = self.popup(localeInfo.GUILD_V2_PASSIVE_MATERIALS_TITLE, 220)
        d.block(24, 48, localeInfo.GUILD_V2_PASSIVE_MATERIALS_HINT, d.design_width - 48, DIM)
        return d

    def page_treasury(self, w, h):
        self.page.panel(0, 76, w, 70)
        self.page.image("nav_treasury_28x28", 16, 88, 38, 38)
        self.page.text(64, 86, "V pokladně", 300, DIM)
        self.page.text(64, 108, yang(self.model.row(m.BALANCE)[0][3]), w - 300, GOLD, ROLE_FIGURE)
        self.page.primary("Vložit Yang", w - 186, 99, self.deposit_dialog, "Čeká se na potvrzení." if self.pending else None)
        self.page.icon_button("action_help_28x28", 0, 150, self.material_sources_dialog,
            localeInfo.GUILD_V2_PASSIVE_MATERIALS_HINT)
        self.page.text(38, 156, "Vložený Yang zůstává cechu. Vybrat ho zatím nelze.", w - 38, DIM, ROLE_CAPTION)
        if self.history_kind() is None:
            self.page.text(0, 192, "Historii vkladů vidí správce pokladny a členové s právem Rozšířený audit.", w, DIM)
        else:
            self.history_list(w, h, 184)

    # ------------------------------------------------------------------ guild level (two layers)
    def levelup_reason(self, offer):
        if not offer:
            return localeInfo.GUILD_V2_MAX_LEVEL
        if not self.model.can(self.pid(), 16 | 32):
            return localeInfo.GUILD_V2_LEVELUP_NO_RIGHT
        level = self.model.row(m.SUMMARY)[0]
        if level[2] < offer["exp"]:
            return localeInfo.GUILD_V2_LEVELUP_NO_EXP
        if offer["group_have"] < offer["group_need"] or offer["active_have"] < offer["active_need"]:
            return localeInfo.GUILD_V2_LEVELUP_NO_TASK
        need, stock = self.model.levelup_growth(), self.model.growth()
        if need and stock and any(have < n for have, n in zip((stock["cores"], stock["scales"], stock["wood"]), need)):
            return localeInfo.GUILD_V2_LEVELUP_NO_GROWTH
        balance = self.model.row(m.BALANCE)[0]
        if any(balance[i] < offer[k] for i, k in enumerate(("metin", "ore", "soul"))):
            return localeInfo.GUILD_V2_NO_MATERIAL
        if balance[3] < offer["yang"]:
            return localeInfo.GUILD_V2_NO_YANG
        if self.pending:
            return localeInfo.GUILD_V2_WAITING
        return None

    def development_dialog(self):
        """Rozvoj cechu: the next level (EXP, common task, materials, Yang) and this week's contribution table."""
        offer = self.model.levelup()
        summary = self.model.row(m.SUMMARY)[0]
        balance = self.model.row(m.BALANCE)[0]
        d = self.popup(localeInfo.GUILD_V2_DEVELOPMENT, 600)
        w = d.design_width - 48
        if offer:
            d.text(24, 44, localeInfo.GUILD_V2_LEVELUP_TITLE % offer["target"], w - 170, GOLD, ROLE_TITLE)
            lines = (
                (localeInfo.GUILD_V2_ROW_EXP, "%s / %s" % (m.number(summary[2]), m.number(offer["exp"])),
                    summary[2] >= offer["exp"]),
                (localeInfo.GUILD_V2_ROW_GROUP, localeInfo.GUILD_V2_ROW_GROUP_VALUE % (m.number(offer["group_have"]),
                    m.number(offer["group_need"])), offer["group_have"] >= offer["group_need"]),
                (localeInfo.GUILD_V2_ROW_ACTIVE, "%s / %s" % (offer["active_have"], offer["active_need"]),
                    offer["active_have"] >= offer["active_need"]),
                (localeInfo.GUILD_V2_ROW_MATERIALS, "%s / %s / %s" % (m.number(offer["metin"]), m.number(offer["ore"]),
                    m.number(offer["soul"])), all(balance[i] >= offer[k] for i, k in enumerate(("metin", "ore", "soul")))),
                (localeInfo.GUILD_V2_ROW_YANG, localeInfo.GUILD_V2_ROW_YANG_VALUE % (yang(offer["yang"]), yang(balance[3])),
                    balance[3] >= offer["yang"]))
            need = self.model.levelup_growth()
            if need and any(need):
                # guild growth (server 13. 10.): golem cores, fish scales and guild wood of the level
                stock = self.model.growth() or {}
                have = (stock.get("cores", 0), stock.get("scales", 0), stock.get("wood", 0))
                lines = lines[:4] + ((localeInfo.GUILD_V2_ROW_GROWTH, "%s / %s / %s" % tuple(m.number(v) for v in need),
                    all(h >= n for h, n in zip(have, need))),) + lines[4:]
            step = 28 if len(lines) > 5 else 32
            y = 84
            for label, value, done in lines:
                widgets.whole_text(d, 24, y, label, 250, DIM)
                d.text(24 + w, y, value, w - 260, GREEN if done else RED, fontconfig.ROLE_CONTROL, "right")
                d.rule(24, y + step - 6, w)
                y += step
            reason = self.levelup_reason(offer)
            d.text(24, y + 4, reason or localeInfo.GUILD_V2_LEVELUP_READY, w, GOLD if reason else GREEN, ROLE_CAPTION)
        else:
            d.text(24, 44, localeInfo.GUILD_V2_MAX_LEVEL_TITLE, w - 170, GOLD, ROLE_TITLE)
            reason = localeInfo.GUILD_V2_MAX_LEVEL
        d.action(localeInfo.GUILD_V2_DEPOSIT, 24 + w - 150, 44, self.deposit_dialog, not self.pending, width=150, height=28)
        y = 286
        d.text(24, y, localeInfo.GUILD_V2_WEEK_TITLE, w, GOLD, fontconfig.ROLE_CONTROL)
        # The level limit comes from the server (Balance t1); level 1 = every member counts, nothing to say.
        floor = self.model.contrib_level()
        note = " " + localeInfo.GUILD_V2_WEEK_FLOOR % floor if floor and floor > 1 else ""
        d.text(24, y + 22, localeInfo.GUILD_V2_WEEK_HINT + note, w, DIM, ROLE_CAPTION)
        d.table_header(24, y + 46, w, 26)
        d.text(34, y + 52, "#", 30, GOLD, ROLE_CAPTION)
        d.text(70, y + 52, localeInfo.GUILD_V2_WEEK_MEMBER, 240, GOLD, ROLE_CAPTION)
        d.text(24 + w - 10, y + 52, localeInfo.GUILD_V2_WEEK_EXP, 160, GOLD, ROLE_CAPTION, "right")
        own = self.pid()
        table = self.model.week_table()[:7]
        for index, (place, name, counted, raw, pid) in enumerate(table):
            yy = y + 78 + index * 26
            color = GOLD if pid == own else INK
            d.text(34, yy, str(place), 30, color)
            d.text(70, yy, name, 300, color)
            d.text(24 + w - 10, yy, m.number(counted), 160, color, align="right")
        if not table:
            d.text(34, y + 80, localeInfo.GUILD_V2_WEEK_EMPTY, w, MUTED)
        if offer:
            d.primary(localeInfo.GUILD_V2_LEVELUP_BUTTON % offer["target"], lambda: self.submit_levelup(d, offer),
                reason=reason)

    def submit_levelup(self, d, offer):
        self.development_pending = True
        if not d.submit(m.UPGRADE, (0, offer["target"] - 1, m.LEVEL_UP)):
            self.development_pending = False

    def deposit_dialog(self):
        d = self.popup("Vložit Yang do cechovní pokladny", 320)
        d.text(24, 46, "Vložit Yang", 512, INK, ROLE_TITLE)
        d.text(24, 82, "Vklad se odečte z tvých Yangů a zůstane cechu.", 512, DIM)
        d.text(24, 126, "Částka", 180, GOLD)
        amount = d.edit(209, 126, 298, 19, "", True)
        d.text(24, 172, "Cech nyní: " + yang(self.model.row(m.BALANCE)[0][3]), 512, DIM)
        def submit():
            try:
                value = m.positive(amount.GetText())
            except ValueError as error:
                d.message.SetText(str(error))
                return
            d.submit(m.DEPOSIT, (value,))
        d.primary("Vložit", submit)

    def history_list(self, w, h, y=112):
        records = [(section, row) for section, rows in self.model.history.items() if section != m.CAPABILITY for row in rows]
        def draw(canvas, record, y, width):
            section, (v, title, body) = record
            canvas.panel(0, y, width, 54)
            if section == m.CONTRIBUTION:
                canvas.text(16, y + 18, title, 220, GOLD, fontconfig.ROLE_CONTROL)
                for kind in range(3):
                    canvas.image(m.MATERIAL_ICONS[kind] + "_25x32", width - 300 + kind * 100, y + 11, 20, 26)
                    canvas.text(width - 274 + kind * 100, y + 18, m.number(v[1 + kind]), 70, GREEN)
            elif section == m.GOAL_HISTORY:
                canvas.text(16, y + 8, title, width - 240, GOLD, fontconfig.ROLE_CONTROL)
                canvas.text(16, y + 31, m.moment(v[1]) + " - " + m.moment(v[2]), width - 240, DIM, ROLE_CAPTION)
                canvas.text(width - 16, y + 18, "Splněno" if v[3] else "Nesplněno", 205, GREEN if v[3] else DIM, align="right")
            elif section in (m.AUDIT, m.CHRONICLE):
                # Accept-invite with command v1 = 1 is a declined invitation, not a new member.
                action = localeInfo.GUILD_V2_AUDIT_INVITE_DECLINED if v[2] == m.ACCEPT_INVITE and v[6] == 1 else self.action_name(v[2])
                canvas.text(16, y + 8, title + " | " + action, width - 180, GOLD, fontconfig.ROLE_CONTROL)
                canvas.text(16, y + 31, body, width - 180, DIM, ROLE_CAPTION)
                canvas.text(width - 14, y + 18, m.moment(v[4]), 150, DIM, ROLE_CAPTION, "right")
            else:
                resource = getattr(localeInfo, m.MATERIALS[v[2]]) if v[2] < 3 else "Yang"
                canvas.text(16, y + 8, title, 200, GOLD, fontconfig.ROLE_CONTROL)
                canvas.text(16, y + 31, m.moment(v[7]), 200, DIM, ROLE_CAPTION)
                canvas.text(232, y + 18, resource, width - 460)
                canvas.text(width - 16, y + 18, ("-" if v[8] else "+") + m.number(v[3]), 200, RED if v[8] else GREEN, fontconfig.ROLE_CONTROL, "right")
        if records:
            self.list(records, y, min(600 - y - 44, h - y - 44), 60, draw)
        elif self.pending or self.history_wanted:
            self.page.text(0, y + 12, "Načítání historie...", w, DIM)
        else:
            self.page.text(0, y + 12, "Zatím tu nic není.", w, DIM)
        bottom = min(566, h - 30)
        self.page.action("Od začátku", 0, bottom, lambda: self.history(self.model.history_kind), not self.pending, width=150)
        self.page.action("Další", w - 150, bottom, lambda: self.history(self.model.history_kind, self.model.history_next),
            bool(self.model.history_next) and not self.pending, width=150)

    @staticmethod
    def action_name(action):
        return {m.CREATE: "Založení cechu", m.UPGRADE: "Vylepšení schopnosti", m.CREATE_GOAL: "Nový cíl", m.EDIT_GOAL: "Úprava cíle",
            m.SET_ROLE: "Změna hodnosti", m.SET_RIGHTS: "Změna oprávnění", m.INVITE: "Pozvánka", m.ACCEPT_INVITE: "Nový člen",
            m.LEAVE: "Odchod", m.KICK: "Vyloučení", m.TRANSFER: "Předání vedení", m.DEPOSIT: "Vklad Yang",
            m.SET_PROFILE: "Úprava náboru", m.POST_NOTICE: "Nové oznámení", m.DELETE_NOTICE: "Smazání oznámení",
            m.PROPOSE_DOCTRINE: "Volba doktríny", m.APPROVE: "Rozhodnutí", 128: "Příspěvek materiálu", 129: "Výsledek výpravy"}.get(action, "Cechovní událost")

    # ------------------------------------------------------------------ members
    def page_members(self, w, h):
        if self.tab == 2 and locked("points"):
            self.tab = 0            # personal points come from goals and the expedition (after the start)
        self.tabs(("Členové", "Hodnosti a práva", "Cechovní body"), locked=(2,) if locked("points") else ())
        if self.tab == 1:
            self.rights_page(w, h)
            return
        if self.tab == 2:
            self.points_page(w, h)
            return
        field = max(110, min(240, w - 170 - 16 - 64 - 150))
        self.page.text(0, 118, "Hledat", 60, DIM)
        self.search_field("members", 64, 115, field)
        self.page.checkbox(64 + field + 18, 119, self.online_only, self.toggle_online)
        self.page.text(64 + field + 40, 118, "Pouze online", 110, INK)
        self.page.primary("Pozvat člena", w - 170, 112, self.invite_dialog,
            None if self.can(1) else ("Čeká se na potvrzení." if self.pending else "Zve správce členů."))
        width = w - 16
        key, descending = self.member_sort
        columns = self.member_columns()
        self.page.table_header(0, 152, w)
        for index, (column, label, fraction) in enumerate(columns):
            x = int(width * fraction)
            end = int(width * columns[index + 1][2]) if index + 1 < len(columns) else w
            active = column == key
            # Whole header cell sorts; the active column shows its direction.
            header = self.page.keep(Flat(self.page, px(x), px(152), span(x, end - x), span(152, 28), lambda c=column: self.sort_members(c),
                label, "link", active, True, px(12), fontconfig.ROLE_SECTION))
            if active:
                # The direction glyph follows the measured label.
                after = x + 12 + int(header.label.GetTextSize()[0] / SCALE) + 2
                self.page.image("glyph_down" if descending else "glyph_up", min(after, end - 18), 157, 18, 18)
        rows = self.member_rows()
        own = self.pid()
        def draw(canvas, row, y, width):
            v, name, body = row
            canvas.row(0, y, width, 38, lambda pid=v[0]: self.member_dialog(pid), style="plain",
                hint=self.member_family_hint(name))
            canvas.rule(0, y + 39, width)
            color = GOLD if v[0] == own else (INK if v[7] else DIM)
            cells = (self.member_name(name, body), m.ROLES[v[1]], str(v[2]), m.number(v[3]), m.number(v[4]), m.number(v[5]))[:len(columns) - 1]
            for index, text in enumerate(cells):
                x = int(width * columns[index][2])
                limit = int(width * (columns[index + 1][2] - columns[index][2])) - 10
                canvas.text(x + 12, y + 11, text, limit, color, fontconfig.ROLE_CONTROL if index == 0 else fontconfig.ROLE_BODY)
            x = int(width * columns[-1][2])
            canvas.bar(x + 12, y + 17, 7, 7, GREEN if v[7] else 0xff5a5048)
            # Online, or when the member last played (owner 21. 10., batch 7 add-on).
            canvas.text(x + 26, y + 11, self.member_state_text(v), width - x - 30, GREEN if v[7] else DIM)
        self.list(rows, 182, min(378, h - 182), 40, draw)
        if not rows:
            self.page.text(12, 196, "Žádný člen neodpovídá hledání." if self.query() or self.online_only else "Cech zatím nemá členy.", w, DIM)
        self.page.text(0, 572, "Klikni na člena pro detail a akce" if locked("goals") else
            "Příspěvky v aktuálním cíli | klikni na člena pro detail a akce", w, DIM, ROLE_CAPTION)

    def member_columns(self):
        """The member table with the member's material contributions, always (owner 21. 10.)."""
        return MEMBER_COLUMNS

    def toggle_online(self):
        self.online_only = not self.online_only
        self.scroll = None
        self.render()

    def sort_members(self, column):
        key, descending = self.member_sort
        self.member_sort = (column, not descending) if column == key else (column, column not in ("name", "role"))
        self.scroll = None
        self.render()

    def member_rows(self):
        query, key, descending = self.query(), self.member_sort[0], self.member_sort[1]
        family = self.family_mode()
        rows = [row for row in self.model.rows(m.MEMBER)
            if (not self.online_only or row[0][7]) and (not query or query in folded(row[1]) or (family and query in folded(row[2])))]
        index = {"role": 1, "level": 2, "metin": 3, "ore": 4, "soul": 5, "online": 7}
        if key == "name":
            rows.sort(key=lambda row: folded(self.member_name(row[1], row[2])), reverse=descending)
        else:
            rows.sort(key=lambda row: folded(self.member_name(row[1], row[2])))
            rows.sort(key=lambda row: row[0][index[key]], reverse=descending)
        return rows

    def points_page(self, w, h):
        help_text = ("Rodinné cechovní body získávají všechny postavy stejného účtu společně. "
            "Body patří členství rodiny v cechu. Po odchodu se nepřenášejí.") if self.family_mode() else m.POINTS_HELP
        top = 112 + self.page.block(0, 112, help_text, w, DIM) + 12
        self.page.table_header(0, top, w)
        self.page.text(16, top + 7, "Pořadí | člen", w - 240, GOLD, fontconfig.ROLE_SECTION)
        self.page.text(w - 16, top + 7, "Cechovní body", 200, GOLD, fontconfig.ROLE_SECTION, "right")
        own = self.pid()
        def draw(canvas, record, y, width):
            place, (v, name, body) = record
            canvas.row(0, y, width, 40, lambda pid=v[0]: self.member_dialog(pid), selected=v[0] == own,
                hint=self.member_family_hint(name))
            canvas.text(14, y + 11, str(place) + ".", 44, GOLD, fontconfig.ROLE_CONTROL)
            canvas.bar(62, y + 17, 7, 7, GREEN if v[7] else 0xff5a5048)
            canvas.text(78, y + 11, self.member_name(name, body), width - 300, INK if v[7] else DIM, fontconfig.ROLE_CONTROL)
            canvas.text(width - 16, y + 11, m.number(v[8]), 200, GOLD, fontconfig.ROLE_CONTROL, "right")
        self.list(self.model.ranking(), top + 34, min(600 - top - 44, h - top - 44), 46, draw)

    def member_dialog(self, pid):
        row = self.model.member(pid)
        if not row:
            return
        self.selected_member = pid
        v, name, body = row
        if R1:
            return self.member_dialog_r1(pid, v, name, body)
        d = self.popup("Detail člena", 420)
        d.image("nav_members_28x28", 24, 46)
        d.text(64, 46, self.member_name(name, body), 470, GOLD, ROLE_TITLE)
        if self.family_mode():
            d.text(64, 66, self.member_family_hint(name), 470, DIM, ROLE_CAPTION)
        d.text(24, 86, m.ROLES[v[1]] + " | úroveň " + str(v[2]) + " | " + self.member_state_text(v), 270, GREEN if v[7] else DIM)
        if not locked("points"):
            d.text(536, 86, "Cechovní body: " + m.number(v[8]), 240, GOLD, align="right")
        # The member's contributions of the guild materials are always shown (owner 21. 10.), the materials page stays locked.
        d.header("Příspěvky do cechu", 24, 116, 512)
        # All five like R1 (shards, ore, souls, scales, wood); rows of 26 so the rule at 290 stays.
        icons = m.MATERIAL_ICONS + ("scale", "wood")
        for kind, value in enumerate(self.model.member_contributions((v, name, body))):
            y = 150 + kind * 26
            d.image(icons[kind] + "_25x32", 28, y - 4, 20, 26)
            d.text(66, y, getattr(localeInfo, m.CONTRIBUTIONS[kind], m.CONTRIBUTIONS[kind]), 260)
            d.text(532, y - 2, m.number(value), 170, GOLD, ROLE_FIGURE, "right")
        # The Yang the member deposited into the treasury (batch 7 add-on), at the right end of the header line.
        if self.model.member_yang(pid):
            d.text(532, 118, self.member_yang_text(pid), 200, GOLD, ROLE_CAPTION, "right")
        d.rule(24, 290, 512)
        def message_member():
            d.Close()
            self.interface.unifiedMessengerRouter.Open(body if self.family_mode() and body else name)
        own = self.model.member(self.pid())
        self_target = pid == self.pid()
        role_allowed = self.leader() or (self.can(1) and own and own[0][1] == 1 and v[1] == 2)
        actions = (
            ("Zpráva", message_member, None if not self_target else "Tohle jsi ty", "secondary"),
            ("Hodnost", lambda: self.role_dialog(pid), "Tohle jsi ty" if self_target else (None if role_allowed else "Jen vůdce nebo Rada"), "secondary"),
            ("Předat vedení", lambda: self.confirm("Předání vedení", "Nový vůdce: " + name + ". Získá správu cechu a tvoje hodnost se změní na Člen.", m.TRANSFER, (pid,)),
                "Tohle jsi ty" if self_target else (None if self.leader() else "Jen vůdce"), "secondary"),
            ("Vyloučit", lambda: self.confirm("Vyloučit člena", "Opravdu chceš vyloučit " + ("rodinu " if self.family_mode() else "postavu ") + name + "? Dosavadní příspěvky zůstanou cechu.", m.KICK, (pid,), label="Vyloučit"),
                self.kick_reason(v, self_target), "danger"))
        for index, (label, event, reason, style) in enumerate(actions):
            x = 24 + index * 130
            d.action(label, x, 304, event, not reason and not self.pending, width=122, height=28, style=style)
            if reason:
                d.text(x + 61, 338, reason, 124, GOLD, ROLE_CAPTION, "center")

    def member_dialog_r1(self, pid, v, name, body):
        offset = 24 if self.family_mode() else 0
        # Batch 8 G2 / G4 (owner 22. 10.): caption lines under the contributions - the craft actions and the EXP of this
        # week per source with its ceiling; the buttons move down by the lines shown.
        # (the guild's state per source stands under the Příspěvky table and in the row hint; too long for this line)
        lines = [text for text in (self.member_actions_text(pid), self.member_xp_text(pid)) if text]
        extra = max(0, len(lines) - 1) * 18
        d = self.popup(self.member_name(name, body), 250 + offset + extra)
        if offset:
            d.text(24, 46, self.member_family_hint(name), 512, DIM, ROLE_CAPTION)
        d.text(24, 50 + offset, "%s · úroveň %s · %s" % (m.ROLES[v[1]], v[2], self.member_state_text(v)), 512,
            GREEN if v[7] else DIM)
        # The member's contributions of the guild materials, always (owner 21. 10.), scales and wood too.
        d.text(24, 90 + offset, "Příspěvky do cechu: " + " · ".join("%s %s" % (getattr(localeInfo, key, key),
            m.number(value)) for key, value in zip(m.CONTRIBUTIONS, self.model.member_contributions((v, name, body)))) +
            self.member_yang_text(pid, " · "), 512, DIM, ROLE_CAPTION)
        for index, text in enumerate(lines):
            d.text(24, 108 + offset + index * 18, text, 512, DIM, ROLE_CAPTION)
        own = self.model.member(self.pid())
        self_target = pid == self.pid()
        role_allowed = not self_target and (self.leader() or (self.can(1) and own and own[0][1] == 1 and v[1] == 2))
        def message_member():
            d.Close()
            self.interface.unifiedMessengerRouter.Open(body if self.family_mode() and body else name)
        actions = (
            ("Zpráva", message_member, not self_target),
            ("Hodnost", lambda: self.role_dialog(pid), role_allowed and not self.pending),
            ("Předat vedení", lambda: self.confirm("Předání vedení", "Nový vůdce: " + name +
                ". Získá správu cechu a tvoje hodnost se změní na Člen.", m.TRANSFER, (pid,)),
                self.leader() and not self_target and not self.pending and not self.model.disband_at()),
            ("Vyloučit", lambda: self.confirm("Vyloučit člena", "Opravdu chceš vyloučit " + name +
                "? Do jiného cechu může až za 24 hodin.", m.KICK, (pid,), label="Vyloučit"),
                not self.kick_reason(v, self_target) and not self.pending))
        for index, (label, event, enabled) in enumerate(actions):
            # Zpráva and Hodnost on the left; the two irreversible actions on the right after a gap.
            d.action(label, 24 + index * 124 + (24 if index >= 2 else 0), 130 + offset + extra, event, enabled, width=118, height=30,
                style="danger" if label == "Vyloučit" else "secondary")
        return d

    def kick_reason(self, values, self_target):
        if self_target:
            return "Tohle jsi ty"
        if values[1] == 0:
            return "Vůdce nelze vyloučit"
        if values[1] == 1 and not self.leader():
            return "Radu vylučuje vůdce"
        if not self.model.can(self.pid(), 1):
            return "Chybí právo"
        return None

    def role_dialog(self, pid):
        row = self.model.member(pid)
        if not row:
            return
        d = self.popup("Změnit hodnost", 320)
        d.text(24, 46, row[1], 512, GOLD, ROLE_TITLE)
        d.text(24, 90, "Nová hodnost", 512, DIM)
        selected = [row[0][1] if row[0][1] in (1, 2) else 2]
        buttons = []
        def choose(role):
            selected[0] = role
            for index, button in enumerate(buttons):
                button.SetSelected(role == index + 1)
        for role in (1, 2):
            buttons.append(d.action(m.ROLES[role], 24 + (role - 1) * 160, 116, lambda r=role: choose(r), width=150, height=30, selected=role == selected[0]))
        d.text(24, 166, "Co která hodnost smí, určují Oprávnění.", 512, DIM, ROLE_CAPTION)
        d.primary("Potvrdit hodnost", lambda: d.submit(m.SET_ROLE, (pid, selected[0])))

    def OpenInvite(self, name):
        if self.pending:
            self.Show()
            self.SetTop()
            self.message("Čeká se na potvrzení předchozí akce.")
            return False
        self.create_requested = False
        self.invitation_requested = None
        self.invite_requested = name
        self.Open()
        if available() and self.pending_action != m.SNAPSHOT:
            self.invite_requested = None
        return True

    def OpenInvitation(self, identifier):
        self.expire_pending()
        if self.search:
            # Explicit navigation must release the persistent search IME;
            # typing otherwise keeps UpdateInvitations blocked indefinitely.
            self.search.edit.KillFocus()
        self.Show()
        self.SetTop()
        if self.pending:
            if self.pending_action == m.SNAPSHOT:
                self.invitation_requested = identifier
                return True
            self.message("Čeká se na potvrzení předchozí akce.")
            return False
        if self.request(m.SNAPSHOT):
            self.snapshot_wanted = False
            self.invitation_requested = identifier
            return True
        return False

    def can_decline(self):
        return self.model.has_capability(m.INVITE_DECISION)

    def valid_invitation(self, identifier):
        if self.model.guild:
            return None
        now = self.model.now(app.GetTime())
        return next((row for row in self.model.rows(m.INVITATION)
                     if row[0][0] == identifier and row[0][2] > now), None)

    def confirm_invitation(self, identifier):
        return self.OpenInvitation(identifier)

    def refresh_state(self):
        # Use the interface tick even while hidden. Serialize reads and leave
        # the server input/browse rate gates time after the preceding receipt.
        if self.pending or not available() or app.GetTime() < self.refresh_after:
            return
        if self.snapshot_wanted:
            if self.request(m.SNAPSHOT):
                self.snapshot_wanted = False
                self.refresh_after = app.GetTime() + 0.25
        elif self.catalog_wanted and self.invitation_requested is None and not self.invitation_dialog:
            if self.request(m.BROWSE):
                self.catalog_wanted = False

    def UpdateInvitations(self, ready):
        # Called every frame by the interface; a hidden window gets no OnUpdate.
        self.expire_pending()
        self.refresh_state()
        if ready:
            try:
                self.katalog_tick()
            except Exception as error:
                try:
                    import dbg
                    dbg.TraceError("guild catalogue tick: %s" % error)
                except Exception:
                    pass
        if self.invitation_dialog and not self.valid_invitation(self.invitation_dialog.identifier):
            self.invitation_dialog.Close()
        if not ready or self.pending or self.dialog or self.invitation_dialog or not available() or self.model.guild:
            return
        candidates = m.invitation_notices.observe(self.pid(), self.model.rows(m.INVITATION), self.model.now(app.GetTime()))
        identifier = self.invitation_requested or (candidates[0][0] if candidates else None)
        invitation = self.valid_invitation(identifier)
        if invitation:
            self.invitation_dialog = InvitationDialog(self, invitation)
            m.invitation_notices.shown(identifier)
        self.invitation_requested = None

    def invite_dialog(self, initial_name=""):
        d = self.popup("Pozvat člena", 250 if R1 else 300)
        d.text(24, 46, "Pozvat do cechu", 512, INK, ROLE_TITLE)
        d.text(24, 96, "Jméno postavy", 165, GOLD)
        name = d.edit(201, 96, 305, 24)
        name.SetText(initial_name)
        d.text(24, 140, "Zadej jméno postavy. Pozvánka platí jeden den. " +
            ("Přijetím vstoupí do cechu její rodina." if self.family_mode() else "Členství vznikne jejím přijetím."), 512, DIM, multiline=True)
        d.primary("Odeslat pozvánku", lambda: d.submit(m.INVITE, (), name.GetText().strip()))

    # ------------------------------------------------------------------ rights
    def rights_values(self):
        rights = self.model.row(m.RIGHTS)[0]
        return list(self.rights_draft) if self.rights_draft else [rights[0], rights[1], rights[2]]

    def rights_page(self, w, h):
        rights = self.rights_values()
        saved = self.model.row(m.RIGHTS)[0]
        editable = self.leader()
        self.page.header("OPRÁVNĚNÍ", 0, 112, w)
        centers = (w - 300, w - 190, w - 80)
        self.page.table_header(0, 148, w)
        self.page.text(16, 155, "Pravomoc", 300, GOLD, fontconfig.ROLE_SECTION)
        for role in (0, 1, 2):
            self.page.text(centers[role], 155, m.ROLES[role], 90, GOLD, fontconfig.ROLE_SECTION, "center")
        for index, label in enumerate(m.RIGHT_NAMES):
            y = 180 + index * 35
            self.page.rule(0, y + 33, w)
            if index and locked("rights"):
                # Only member management is used at the start; the other rights belong to locked features.
                self.page.text(16, y + 9, label, centers[0] - 60, MUTED)
                self.page.keep(lock_image(self.page, px(centers[0] - 40), px(y + 9)))
                self.page.text(centers[1], y + 10, LOCKED_HINT, 220, MUTED, ROLE_CAPTION, "center")
                continue
            self.page.text(16, y + 9, label, centers[0] - 60, INK)
            for role in (0, 1, 2):
                x = centers[role] - 10
                if role and index == 2:
                    self.page.text(centers[role], y + 10, "Jen vůdce", 100, DIM, ROLE_CAPTION, "center")
                    continue
                active = bool(rights[role] & (1 << index))
                changed = role and self.rights_draft and bool(saved[role] & (1 << index)) != active
                if changed:
                    self.page.bar(x - 5, y + 5, 30, 26, 0xff34131a)
                self.page.checkbox(x, y + 9, active, lambda r=role, bit=index: self.change_right(r, bit),
                    editable and role != 0 and not self.pending)
        self.page.block(0, 548, "Vůdce má vždy všechna práva." if locked("rights") else
            "Vůdce má vždy všechna práva. Cíl cechu a předání vedení zůstávají jemu.", w - 340, DIM, ROLE_CAPTION)
        if not editable:
            self.page.text(w, 560, "Oprávnění může měnit jen vůdce.", 320, GOLD, align="right")
            return
        dirty = bool(self.rights_draft) and self.rights_draft[1:] != [saved[1], saved[2]]
        self.page.action("Zrušit změny", w - 130, 559, self.discard_rights, dirty and not self.pending, width=130, height=30)
        if dirty and self.pending:
            self.page.primary("Uložit oprávnění", w - 316, 560, self.save_rights, "Čeká se na potvrzení.")
        else:
            self.page.button("Uložit oprávnění", w - 316, 560, self.save_rights, dirty)

    def change_right(self, role, bit):
        if not self.leader() or role == 0 or bit == 2 or self.pending:
            return False
        draft = self.rights_values()
        draft[role] ^= 1 << bit
        self.rights_draft = draft
        self.render()
        return True

    def discard_rights(self):
        self.rights_draft = None
        self.render()

    def save_rights(self):
        saved = self.model.row(m.RIGHTS)[0]
        if not self.rights_draft:
            return False
        for role in (1, 2):
            if self.rights_draft[role] != saved[role]:
                return self.request(m.SET_RIGHTS, (role, self.rights_draft[role]))
        self.rights_draft = None
        return False

    def settle_rights(self, action, status, matched):
        """Send the second role's change after the first is confirmed."""
        if not self.rights_draft:
            return
        saved = self.model.row(m.RIGHTS)[0]
        if self.rights_draft[1:] == [saved[1], saved[2]]:
            self.rights_draft = None
        elif matched and action == m.SET_RIGHTS and status == m.OK and not self.pending:
            self.save_rights()

    # ------------------------------------------------------------------ doctrines
    def page_doctrines(self, w, h):
        self.page.action("Schvalování", w - 150, 72, lambda: self.SelectPage("approvals"), self.can(256) or self.can(512), width=150)
        doctrine = self.model.row(m.DOCTRINE)[0]
        width = (w - 18) // 2
        for value in (1, 2):
            x = (value - 1) * (width + 18)
            active = doctrine[0] == value
            self.page.panel(x, 112, width, 420, active)
            self.page.image("passive_boss_41x41" if value == 1 else "nav_doctrines_28x28", x + 18, 134, 41, 41)
            self.page.text(x + 74, 134, m.DOCTRINES[value], width - 90, GOLD, fontconfig.ROLE_LARGE_BOLD)
            self.page.text(x + 74, 160, "Aktivní doktrína" if active else "Trvalý postup zůstává zachován", width - 90, GREEN if active else DIM)
            self.page.rule(x + 18, 196, width - 36)
            self.page.text(x + 18, 214, "Dokončené cíle", width - 140, DIM)
            self.page.text(x + width - 18, 210, m.number(doctrine[value + 1]), 100, INK, ROLE_FIGURE, "right")
            self.page.text(x + 18, 250, "Dokončené výpravy", width - 140, DIM)
            self.page.text(x + width - 18, 246, m.number(doctrine[value + 3]), 100, INK, ROLE_FIGURE, "right")
            self.page.block(x + 18, 300, "Doktrína určuje směr cechu a počítá jeho úspěchy. Bojové bonusy získáváš v pasivních schopnostech.", width - 36, DIM, ROLE_CAPTION)
            if active:
                continue
            reason = None
            if not self.model.can(self.pid(), 8):
                reason = "Chybí právo Správa doktríny."
            elif self.pending:
                reason = "Čeká se na potvrzení."
            self.page.primary("Změnit doktrínu" if doctrine[0] else "Zvolit doktrínu", x + width - 188, 488,
                lambda v=value: self.confirm("Změna doktríny", "Zvolit doktrínu " + m.DOCTRINES[v] + "? " +
                    ("První volbu potvrzuje vůdce." if not doctrine[0] else "Změnu musí potvrdit ještě někdo s oprávněním z jiného účtu."), m.PROPOSE_DOCTRINE, (v,)),
                reason)

    def page_approvals(self, w, h):
        self.page.text(0, 76, "Souhlas platí jen pro návrh v této podobě.", w, DIM)
        def draw(canvas, row, y, width):
            v, title, body = row
            actor = self.model.member(v[2])
            canvas.panel(0, y, width, 82)
            canvas.text(16, y + 14, "Doktrína: " + m.DOCTRINES[v[3]], width - 340, GOLD, fontconfig.ROLE_LARGE_BOLD)
            canvas.text(16, y + 44, (actor[1] if actor else "Bývalý člen") + " | " + m.moment(v[4]), width - 340, DIM)
            if v[5] == 0:
                reason = None
                if not self.model.can(self.pid(), 256):
                    reason = "Chybí právo Schvalování rozhodnutí"
                elif v[2] == self.pid():
                    reason = "Vlastní návrh schvaluje někdo jiný"
                canvas.action("Schválit", width - 290, y + 14, lambda i=v[0]: self.confirm("Schválit rozhodnutí", "Potvrdit navrženou změnu doktríny?", m.APPROVE, (i, 1)),
                    not reason and not self.pending, width=130)
                canvas.action("Odmítnout", width - 146, y + 14, lambda i=v[0]: self.confirm("Odmítnout rozhodnutí", "Odmítnout tento návrh?", m.APPROVE, (i, 0), label="Odmítnout"),
                    not reason and not self.pending, width=130, style="danger")
                if reason:
                    canvas.text(width - 16, y + 50, reason, 280, GOLD, ROLE_CAPTION, "right")
            else:
                canvas.text(width - 20, y + 30, ("Čeká", "Schváleno", "Odmítnuto", "Zastaralé")[v[5]], 190, GOLD, fontconfig.ROLE_CONTROL, "right")
        self.list(self.model.rows(m.APPROVAL), 112, min(476, h - 112), 90, draw)
        if not self.model.rows(m.APPROVAL):
            self.page.text(0, 124, "Žádná rozhodnutí ke schválení.", w, DIM)

    # ------------------------------------------------------------------ chronicle
    def page_chronicle(self, w, h):
        self.tabs(("Kronika", "Relikvie a odkaz"))
        if self.tab == 0:
            self.history_list(w, h)
            return
        paths = ("Odkaz lovců", "Odkaz průzkumu", "Cechovní rozvoj", "Mistrovství výprav")
        complete = 0
        for row in self.model.rows(m.MILESTONE):
            v = row[0]
            index = v[0] - 1
            if index not in range(4):
                continue
            y = 112 + index * 84
            done = bool(v[5])
            complete += int(done)
            self.page.panel(0, y, w, 76, done)
            self.page.image("mandate_31x37", 18, y + 19)
            self.page.text(66, y + 12, paths[index], w - 280, GOLD, fontconfig.ROLE_LARGE_BOLD)
            labels = (("Cíle", "Výpravy"), ("Cíle", "Výpravy"), ("Stupně schopností", "Kronika"), ("Výpravy", "Cíle"))[index]
            self.page.text(66, y + 42, "%s %s/%s | %s %s/%s" % (labels[0], m.number(v[1]), m.number(v[2]), labels[1], m.number(v[3]), m.number(v[4])), w - 280, DIM)
            self.page.text(w - 20, y + 27, "Dokončeno" if done else "Probíhá", 195, GREEN if done else DIM, fontconfig.ROLE_CONTROL, "right")
        self.page.header("VELKÝ ODKAZ", 0, 458, w)
        self.page.text(16, 498, "Trvalý Velký odkaz byl získán." if self.model.row(m.SUMMARY)[0][8] else "Dokončené cesty: %s / 4" % complete, w - 32, GOLD, fontconfig.ROLE_CONTROL)
        self.page.text(16, 524, "Mandát cechu: " + m.number(self.model.row(m.SUMMARY)[0][3]), w - 32, DIM)

    # ------------------------------------------------------------------ expedition
    def page_expedition(self, w, h):
        run = self.model.row(m.EXPEDITION)[0]
        states = ("Sestavování výpravy", "Kontrola připravenosti", "Sestava uzamčena", "Příprava vstupu", "Výprava probíhá", "Výprava dokončena", "Výprava neuspěla", "Výprava uzavřena")
        opened = bool(self.model.row(m.CAPABILITY)[0][4])
        self.page.text(0, 76, states[run[6]], w - 230, GOLD, fontconfig.ROLE_LARGE_BOLD)
        self.page.text(0, 102, "Doktrína výpravy: " + m.DOCTRINES[run[3]], w, DIM)
        if not opened:
            self.page.text(0, 124, "Výprava zatím není otevřená. Sestavu lze připravit předem.", w, GOLD, ROLE_CAPTION)
        participants = self.model.rows(m.PARTICIPANT)
        enrolled = any(row[0][0] == self.pid() for row in participants)
        self.page.header("ÚČASTNÍCI | %s" % len(participants), 0, 152, w)
        def draw(canvas, row, y, width):
            v = row[0]
            member = self.model.member(v[0])
            canvas.panel(0, y, width, 40)
            canvas.text(16, y + 11, member[1] if member else "-", width - 285, GOLD, fontconfig.ROLE_CONTROL)
            canvas.text(width - 16, y + 11, "Připraven" if v[1] else "Čeká", 190, GREEN if v[1] else DIM, align="right")
        self.list(participants, 190, min(340, h - 190), 46, draw)
        if not participants:
            self.page.text(0, 200, "Zatím se nikdo nepřihlásil.", w, DIM)
        self.page.action("Odhlásit se" if enrolled else "Přihlásit se", 0, 560,
            lambda: self.request(m.ENROLL, (0 if enrolled else 1,)), not self.pending and run[6] not in (2, 3, 4), width=150)
        if run[6] == 1 and enrolled:
            self.page.action("Připravenost", 160, 560, self.ready_dialog, not self.pending, width=150)
        elif run[6] in (5, 6):
            self.page.action("Výsledek", 160, 560, self.result_dialog, width=150)
        else:
            self.page.action("Kontrola", 160, 560, lambda: self.request(m.READY_CHECK), self.can(128) and enrolled, width=150)
        if run[6] == 4:
            self.page.action("Volba větve", 320, 560, self.vote_dialog, not bool(run[5]) and enrolled and not self.pending, width=150)
        reason = None
        if not opened:
            reason = "Výprava zatím není otevřená."
        elif not self.model.can(self.pid(), 128):
            reason = "Chybí právo Spuštění výpravy."
        elif run[6] != 1:
            reason = "Nejdřív proveď kontrolu připravenosti."
        elif self.pending:
            reason = "Čeká se na potvrzení."
        self.page.primary("Spustit výpravu", w - 170, 560,
            lambda: self.confirm("Spustit výpravu", "Potvrdit připravenou sestavu a zahájit společnou výpravu?", m.START, (run[1],)), reason)

    def ready_dialog(self):
        run = self.model.row(m.EXPEDITION)[0]
        d = self.popup("Výprava | připravenost", 310)
        d.text(24, 46, "Jsi připraven vstoupit?", 512, INK, ROLE_TITLE)
        d.text(24, 90, "Odpověz do " + m.moment(run[2]) + ".", 512, DIM)
        d.action("Nejsem připraven", 24, 150, lambda: d.submit(m.READY, (run[1], 0)), width=180, height=28)
        d.primary("Jsem připraven", lambda: d.submit(m.READY, (run[1], 1)))

    def vote_dialog(self):
        run = self.model.row(m.EXPEDITION)[0]
        d = self.popup("Výprava | volba větve", 320)
        d.text(24, 46, "Kudy dál?", 512, INK, ROLE_TITLE)
        d.text(24, 90, "Vyber větev výpravy. Každý účastník má jeden hlas.", 512, DIM, multiline=True)
        d.text(24, 120, "Při rovnosti hlasů rozhoduje vedoucí výpravy.", 512, DIM, ROLE_CAPTION, multiline=True)
        d.action("Levá větev", 24, 172, lambda: d.submit(m.VOTE, (run[0], 1)), width=200, height=30)
        d.action("Pravá větev", 240, 172, lambda: d.submit(m.VOTE, (run[0], 2)), width=200, height=30)

    def result_dialog(self):
        run = self.model.row(m.EXPEDITION)[0]
        d = self.popup("Výprava dokončena" if run[6] == 5 else "Výprava neuspěla", 310)
        d.text(24, 46, "Výprava dokončena" if run[6] == 5 else "Výprava neuspěla", 512, INK, ROLE_TITLE)
        d.text(24, 92, "Společný výsledek je zapsaný v Kronice." if run[6] == 5 else "Výprava skončila. Můžeš připravit novou sestavu.", 512, DIM, multiline=True)
        d.primary("Otevřít Kroniku", lambda: self.SelectPage("chronicle"))

    # ------------------------------------------------------------------ settings
    def page_settings(self, w, h):
        if not locked("profile"):
            return self.page_settings_full(w, h)
        self.page.header("RADA A NÁBOR", 0, 74, w)
        council = bool(self.model.row(m.RIGHTS)[0][1] & 1)
        self.page.checkbox(0, 116, council, self.toggle_council, self.leader() and not self.pending)
        self.page.text(30, 114, "Rada smí zvát a vyhazovat členy", 420, INK if self.leader() else MUTED)
        self.page.text(w, 114, "Mění jen vůdce." if not self.leader() else "Ostatní práva jsou v Oprávněních.",
            360, DIM, ROLE_CAPTION, "right")
        # Recruiting and the profile serve the guild catalog, which comes after the start.
        self.page.action("Nábor a profil", 0, 160, None, width=170, height=30, locked=True)
        self.page.text(188, 166, LOCKED_HINT + " (katalog cechů)", 400, MUTED, ROLE_CAPTION)
        self.page.header("SPRÁVA CECHU", 0, 256, w)
        leader = self.leader()
        level = self.model.row(m.SUMMARY)[0][1]
        rows = (
            ("Nástěnka", lambda: self.SelectPage("board"), "Oznámení a zprávy pro členy cechu", None, "secondary"),
            ("Schvalování", None, "Rozhodnutí, která čekají na souhlas", LOCKED_HINT, "locked") if locked("approvals") else
            ("Schvalování", lambda: self.SelectPage("approvals"), "Rozhodnutí, která čekají na souhlas",
                None if self.model.can(self.pid(), 256) or self.model.can(self.pid(), 512) else "Chybí právo Schvalování nebo Audit", "secondary"),
            ("Oprávnění", lambda: self.SelectPage("members", 1), "Co smí Rada (zvát, vyhazovat) a Členové", None, "secondary"),
            ("Audit", None, "Přehled akcí vedení cechu", LOCKED_HINT, "locked") if locked("audit") else
            ("Audit", lambda: self.SelectPage("audit"), "Přehled akcí vedení cechu",
                None if self.model.can(self.pid(), 512) else "Chybí právo Rozšířený audit", "secondary"),
            ("Nahrát znak", self.open_mark_dialog, "Obrázek 32x32 px ve složce upload",
                "Jen vůdce" if not leader else (None if level >= 1 else "Od úrovně cechu 1"), "secondary"),
            ("Opustit cech", self.leave_dialog,
                "Tvoje příspěvky zůstanou cechu", "Vůdce musí nejdřív předat vedení" if leader else None, "danger"),
            ("Zrušit rozpuštění", self.cancel_disband_dialog, "Cech zůstane zachován", None if leader else "Jen vůdce", "secondary")
            if self.model.disband_at() else
            ("Rozpustit cech", self.disband_dialog, ("Za %d hodin ukončí cech pro všechny členy" % m.DISBAND_DELAY_HOURS)
                if self.model.has_capability(m.DISBAND_DELAY) else "Ukončí cech pro všechny členy",
                None if leader else "Jen vůdce", "danger"))
        for index, (label, event, description, reason, style) in enumerate(rows):
            y = 294 + index * 40
            if style == "locked":
                self.page.action(label, 0, y, None, width=170, height=30, locked=True)
            else:
                self.page.action(label, 0, y, event, not reason and not self.pending, width=170, height=30, style=style)
            room = w - 188 - (280 if reason else 0)
            if room >= 140:
                self.page.text(188, y + 7, description, room, DIM)
            if reason:
                self.page.text(w, y + 8, reason, min(270, w - 188), GOLD, ROLE_CAPTION, "right")

    def page_settings_full(self, w, h):
        profile = self.model.row(m.PROFILE)
        self.page.header("NÁBOR A PROFIL", 0, 74, w)
        self.page.text(0, 112, "Nábor je otevřený" if profile[0][0] else "Nábor je uzavřený", 300,
            GREEN if profile[0][0] else DIM, fontconfig.ROLE_CONTROL)
        self.page.text(w, 112, "Přijímá hráče od úrovně " + str(profile[0][1]), 360, DIM, align="right")
        self.page.paragraph(0, 140, w, 64, profile[2] or "Cech zatím nemá veřejný popis.")
        self.page.primary("Upravit profil", 0, 214, self.profile_dialog,
            None if self.can(1) else ("Čeká se na potvrzení." if self.pending else "Profil upravuje správce členů."), place="right")
        self.page.header("SPRÁVA CECHU", 0, 256, w)
        leader = self.leader()
        level = self.model.row(m.SUMMARY)[0][1]
        rows = (
            ("Nástěnka", lambda: self.SelectPage("board"), "Oznámení a zprávy pro členy cechu", None, "secondary"),
            ("Schvalování", lambda: self.SelectPage("approvals"), "Rozhodnutí, která čekají na souhlas",
                None if self.model.can(self.pid(), 256) or self.model.can(self.pid(), 512) else "Chybí právo Schvalování nebo Audit", "secondary"),
            ("Oprávnění", lambda: self.SelectPage("members", 1), "Co smí Rada a Členové", None, "secondary"),
            ("Audit", lambda: self.SelectPage("audit"), "Přehled akcí vedení cechu",
                None if self.model.can(self.pid(), 512) else "Chybí právo Rozšířený audit", "secondary"),
            ("Nahrát znak", self.open_mark_dialog, "Obrázek 32x32 px ve složce upload",
                "Jen vůdce" if not leader else (None if level >= 1 else "Od úrovně cechu 1"), "secondary"),
            ("Opustit cech", self.leave_dialog,
                "Tvoje příspěvky zůstanou cechu", "Vůdce musí nejdřív předat vedení" if leader else None, "danger"),
            ("Zrušit rozpuštění", self.cancel_disband_dialog, "Cech zůstane zachován", None if leader else "Jen vůdce", "secondary")
            if self.model.disband_at() else
            ("Rozpustit cech", self.disband_dialog, ("Za %d hodin ukončí cech pro všechny členy" % m.DISBAND_DELAY_HOURS)
                if self.model.has_capability(m.DISBAND_DELAY) else "Ukončí cech pro všechny členy",
                None if leader else "Jen vůdce", "danger"))
        for index, (label, event, description, reason, style) in enumerate(rows):
            y = 294 + index * 40
            self.page.action(label, 0, y, event, not reason and not self.pending, width=170, height=30, style=style)
            room = w - 188 - (280 if reason else 0)
            if room >= 140:
                self.page.text(188, y + 7, description, room, DIM)
            if reason:
                self.page.text(w, y + 8, reason, min(270, w - 188), GOLD, ROLE_CAPTION, "right")

    def toggle_council(self):
        """The council's member right (invite, kick, ranks) in one click; the other rights stay as they are."""
        if not self.leader() or self.pending:
            return False
        masks = self.model.row(m.RIGHTS)[0]
        return self.request(m.SET_RIGHTS, (1, (masks[1] ^ 1) & ~4))

    def profile_dialog(self):
        profile = self.model.row(m.PROFILE)
        d = self.popup("Nábor a profil cechu", 410)
        d.text(24, 46, "Nábor a profil", 512, INK, ROLE_TITLE)
        d.text(24, 96, "Minimální úroveň", 180, GOLD)
        level = d.edit(227, 96, 280, 3, profile[0][1], True)
        d.text(24, 138, "Krátké představení cechu", 300, GOLD)
        description = d.edit(24, 170, 482, 1024, profile[2], height=62)
        opened = [bool(profile[0][0])]
        def toggle():
            opened[0] = not opened[0]
            check(box, opened[0])
        box = d.checkbox(24, 262, opened[0], toggle)
        d.text(48, 260, "Nábor je otevřený (cech se ukáže v katalogu)", 460)
        def submit():
            try:
                minimum = m.positive(level.GetText())
                if minimum > 120:
                    raise ValueError("Úroveň musí být od 1 do 120.")
            except ValueError as error:
                d.message.SetText(str(error))
                return
            d.submit(m.SET_PROFILE, (int(opened[0]), minimum), "", description.GetText().replace("\r\n", "\n").replace("\r", "\n"))
        d.primary("Uložit profil", submit)

    # ------------------------------------------------------------------ board
    def page_board(self, w, h):
        records = sorted(self.model.rows(m.NOTICE), key=lambda row: (-row[0][3], -row[0][0]))
        reason = None
        if len(records) >= NOTICE_LIMIT:
            reason = "Nástěnka je plná. Nejdřív smaž starší oznámení."
        elif self.pending:
            reason = "Čeká se na potvrzení."
        self.page.primary("Napsat oznámení", w - 170, 88, self.notice_dialog, reason, place="left")
        def draw(canvas, row, y, width):
            v, title, body = row
            canvas.row(0, y, width, 102, lambda record=row: self.read_notice(record), bool(v[3]))
            canvas.text(16, y + 12, ("Připnuto | " if v[3] else "") + title, width - 190, GOLD, fontconfig.ROLE_LARGE_BOLD)
            canvas.text(width - 16, y + 14, m.moment(v[2]), 170, DIM, ROLE_CAPTION, "right")
            preview = canvas.text(16, y + 44, body.replace("\n", " "), width - 32, DIM, multiline=True)
            lines = preview.GetText().split("\n")
            if len(lines) > 2:
                preview.SetText("\n".join(lines[:2]) + "...")
        self.list(records, 128, min(464, h - 128), 110, draw)
        if not records:
            self.page.text(0, 140, "Nástěnka zatím neobsahuje oznámení.", w, DIM)

    def read_notice(self, record):
        values, title, body = record
        d = self.popup(title, 489, 634)
        d.text(24, 46, title, 586, GOLD, ROLE_TITLE)
        d.text(24, 80, m.moment(values[2]), 586, DIM, ROLE_CAPTION)
        d.paragraph(24, 108, 586, 300, body)
        allowed = self.can(1) or values[1] == self.pid()
        d.action("Smazat oznámení", 24, d.design_height - 36, lambda: d.submit(m.DELETE_NOTICE, (values[0],)), allowed, width=170, style="danger")
        if not allowed:
            d.text(208, d.design_height - 30, "Smazat může autor nebo správce členů", 260, GOLD, ROLE_CAPTION)

    def notice_dialog(self):
        d = self.popup("Napsat oznámení", 420)
        d.text(24, 46, "Nové oznámení", 512, INK, ROLE_TITLE)
        d.text(24, 96, "Nadpis", 150, GOLD)
        title = d.edit(195, 96, 312, 64)
        d.text(24, 138, "Text oznámení", 300, GOLD)
        body = d.edit(24, 170, 482, 1024, height=70)
        pinned = [False]
        def toggle():
            pinned[0] = not pinned[0]
            check(box, pinned[0])
        allowed = self.model.can(self.pid(), 1)
        box = d.checkbox(24, 270, False, toggle, allowed)
        d.text(48, 268, "Připnout nahoru", 200, INK if allowed else MUTED)
        if not allowed:
            d.text(236, 270, "Připnout může jen správce členů.", 290, GOLD, ROLE_CAPTION)
        d.text(24, 298, "Oznámení uvidí všichni členové na cechovní nástěnce.", 512, DIM, ROLE_CAPTION, multiline=True)
        d.primary("Zveřejnit", lambda: d.submit(m.POST_NOTICE, (int(pinned[0]),), title.GetText().strip(), body.GetText().replace("\r\n", "\n").replace("\r", "\n").strip()))

    def page_audit(self, w, h):
        self.history_list(w, h, 76)

    def disband_dialog(self):
        if not self.leader() or self.pending:
            self.message("Cech může rozpustit jen jeho vůdce.")
            return False
        name = self.model.row(m.SUMMARY)[1]
        if R1:
            self.disband_dialog_r1(name)
            return None
        d = self.popup("Rozpustit cech", 370)
        d.text(24, 46, "Rozpustit cech " + name, 512, RED, ROLE_TITLE)
        if self.model.has_capability(m.SOLO_DISBAND):
            text = ("Jsi-li jediným členem, cech zanikne ihned a nový můžeš založit hned. Jinak platí lhůta %d hodin "
                "s možností zrušení. Název zůstane 30 dní rezervovaný. Potvrď přesným názvem cechu." % m.DISBAND_DELAY_HOURS)
        elif self.model.has_capability(m.DISBAND_DELAY):
            text = ("Cech " + name + " se rozpustí za %d hodin. Do té doby ho můžeš zrušit. Pak členové ztratí "
                "členství a bonusy a název zůstane %s dní rezervovaný. Pro potvrzení napiš přesný název cechu." % (m.DISBAND_DELAY_HOURS, 30))
        else:
            text = "Tímto ukončíš cech " + name + ". Členové ztratí členství a bonusy. Pro potvrzení napiš přesný název cechu."
        d.text(24, 86, text, 512, INK, multiline=True)
        confirmation = d.edit(24, 176, 482, namepolicy.GUILD_MAX_BYTES)
        d.primary("Rozpustit cech", lambda: d.submit(m.DISBAND, (m.DISBAND_SCHEDULE,), confirmation.GetText()))

    def disband_texts(self):
        """The short texts of the R1 disband dialog by what the server offers: (line, line, note or None). Solo:
        a lone member ends the guild at once, otherwise the delay with the way back; with the delay: it ends after it;
        an older server: at once."""
        hours = m.DISBAND_DELAY_HOURS
        reserved = "Název zůstane 30 dní rezervovaný."
        if self.model.has_capability(m.SOLO_DISBAND):
            return "Jediný člen: cech zanikne ihned.", "Jinak za %d hodin, lze zrušit." % hours, reserved
        if self.model.has_capability(m.DISBAND_DELAY):
            return "Cech zanikne za %d hodin, lze zrušit." % hours, "Členové pak ztratí členství a bonusy.", reserved
        return "Cech zanikne ihned.", "Členové ztratí členství a bonusy.", None

    def disband_dialog_r1(self, name):
        """Rozpustit cech in the R1 look (the narrow dialog chosen for the R1 round of 8 Oct 2026): 280 x 180
        px, 14 px from the frame on every side (the first line 14 px under the vein of the header, the buttons 14 px
        over the bottom), two short lines and a note, the name of the guild as the hint of the field, two equal buttons
        across the width: Rozpustit cech (primary, the red vein, on the left) and Zavřít (secondary, on the right);
        Rozpustit cech works only while the field holds exactly the name of the guild. Laid out in pixels (unit() = the
        design unit of a pixel row). The row of the note is also the row of the messages of the dialog (an error, "Čeká se na potvrzení...")."""
        frame, pad, vein, width = 3, 14, 28, 280
        left = frame + pad
        content = width - 2 * left
        first, step = vein + pad - 3, 20                   # the capitals of a 17 px line begin 3 px under its top
        field = first + 2 * step + 2 + 24                  # the note (16 px): its capitals 2 px under its top
        buttons = field + 22 + pad
        d = self.popup("Rozpustit cech", unit(buttons + 22 + pad + frame), unit(width))
        texts = self.disband_texts()
        d.text(unit(left), unit(first), texts[0], unit(content), INK)
        d.text(unit(left), unit(first + step), texts[1], unit(content), INK)
        note = d.text(unit(left), unit(first + 2 * step), texts[2] or "", unit(content), DIM, ROLE_CAPTION)
        d.place_message(unit(left), unit(first + 2 * step), unit(content))
        edit_left = unit(left + 4)
        confirmation = d.edit(edit_left, unit(field + 3), unit(left + content - 4) - edit_left, namepolicy.GUILD_MAX_BYTES)
        confirmation.SetInfoMessage("Napiš: " + name)
        hint = getattr(confirmation, "backText", None)
        if R1 and hint is not None:                        # the hint in the font and the grey of the R1 fields
            widgets.uir1.SetFont(hint, font(fontconfig.ROLE_BODY))
            hint.SetPackedFontColor(native_color(MUTED))
        each = (content - 8) // 2
        send = d.primary("Rozpustit cech", lambda: d.submit(m.DISBAND, (m.DISBAND_SCHEDULE,), confirmation.GetText()),
            equal=(unit(left + content - each), unit(buttons), unit(left + each) - unit(left), unit(left)))
        send.Disable()
        state = [False]
        def follow():
            exact = confirmation.GetText() == name
            if exact != state[0]:
                state[0] = exact
                send.Enable() if exact else send.Disable()
            if bool(d.message.GetText()) == note.IsShow():
                note.Hide() if d.message.GetText() else note.Show()
        d.ticks.append(follow)
        d.ticks.append(d.fit_message)
        follow()

    def cancel_disband_dialog(self):
        if not self.leader() or self.pending:
            self.message("Rozpuštění může zrušit jen vůdce.")
            return False
        name = self.model.row(m.SUMMARY)[1]
        self.confirm("Zrušit rozpuštění", "Cech " + name + " zůstane zachován a nábor můžeš znovu otevřít v profilu.",
            m.DISBAND, (m.DISBAND_CANCEL,), name, "Zrušit rozpuštění")

    # ------------------------------------------------------------------ without guild
    def without_guild(self):
        if not locked("catalog"):
            return self.without_guild_full()
        w, h = self.page.design_width, self.page.design_height
        self.page.text(0, 0, "Najdi svůj cech", w, GOLD, ROLE_TITLE)
        self.page.text(0, 34, "Založ vlastní cech, nebo přijmi pozvánku.", w, DIM)
        self.page.rule(0, 62, w, 0xff3a2e24)
        self.page.button("Založit cech", 0, 76, self.create_dialog, not self.pending)
        # The guild catalog (recruiting profiles) comes after the start.
        self.page.action("Katalog cechů", 184, 76, None, width=150, height=24, locked=True)
        self.page.header("POZVÁNKY", 0, 118, w)
        invitations = self.model.rows(m.INVITATION)
        def draw(canvas, row, y, width):
            v, name, body = row
            canvas.panel(0, y, width, 52)
            canvas.text(16, y + 8, name, width - 205, GOLD, fontconfig.ROLE_CONTROL)
            canvas.text(16, y + 30, "Platí do " + m.moment(v[2]), width - 205, DIM, ROLE_CAPTION)
            canvas.action("Zobrazit pozvánku", width - 180, y + 12, lambda i=v[0]: self.confirm_invitation(i), not self.pending, width=168, height=28)
        self.list(invitations, 154, 118, 58, draw)
        if not invitations:
            self.page.text(0, 166, "Nemáš žádné platné pozvánky. Pozvánku ti pošle vůdce nebo rada cechu.", w, DIM)
        self.page.locked_panel(0, 280, w, min(200, h - 290), "CECHY S OTEVŘENÝM NÁBOREM",
            "Katalog cechů s náborem přijde s první větší aktualizací. Do cechu tě zatím pozve jeho vůdce nebo Rada.")

    def without_guild_full(self):
        w, h = self.page.design_width, self.page.design_height
        self.page.text(0, 0, "Najdi svůj cech", w, GOLD, ROLE_TITLE)
        self.page.text(0, 34, "Společné cíle. Výpravy. Vlastní historie.", w, DIM)
        self.page.rule(0, 62, w, 0xff3a2e24)
        self.page.button("Založit cech", 0, 76, self.create_dialog, not self.pending)
        self.page.action("Katalog cechů", 184, 76, lambda: self.request(m.BROWSE), not self.pending, width=150, height=24)
        self.page.header("POZVÁNKY", 0, 118, w)
        invitations = self.model.rows(m.INVITATION)
        def draw(canvas, row, y, width):
            v, name, body = row
            canvas.panel(0, y, width, 52)
            canvas.text(16, y + 8, name, width - 205, GOLD, fontconfig.ROLE_CONTROL)
            canvas.text(16, y + 30, "Platí do " + m.moment(v[2]), width - 205, DIM, ROLE_CAPTION)
            canvas.action("Zobrazit pozvánku", width - 180, y + 12, lambda i=v[0]: self.confirm_invitation(i), not self.pending, width=168, height=28)
        self.list(invitations, 154, 118, 58, draw)
        if not invitations:
            self.page.text(0, 166, "Nemáš žádné platné pozvánky. Pozvánku ti pošle vůdce nebo rada cechu.", w, DIM)
        self.page.header("Cechy s otevřeným náborem", 0, 280, w)
        self.page.text(0, 322, "Hledat", 60, DIM)
        self.search_field("catalog", 64, 319, 240)
        query = self.query()
        records = [row for row in self.model.rows(m.RECRUITMENT) if not query or query in folded(row[1])]
        self.page.table_header(0, 354, w)
        width = w - 16
        for x, label in ((0, "Cech"), (0.46, "Kronika"), (0.62, localeInfo.GUILD_V2_FAMILY_COUNT), (0.78, "Od úrovně")):
            self.page.text(int(width * x) + 12, 361, label, 150, GOLD, fontconfig.ROLE_SECTION)
        def recruitment(canvas, row, y, width):
            v, name, body = row
            canvas.row(0, y, width, 38, lambda record=row: self.recruitment_dialog(record), style="plain")
            canvas.rule(0, y + 39, width)
            canvas.text(12, y + 11, name, int(width * 0.46) - 20, INK, fontconfig.ROLE_CONTROL)
            canvas.text(int(width * 0.46) + 12, y + 11, str(v[1]), 100, INK)
            canvas.text(int(width * 0.62) + 12, y + 11, str(v[2]), 100, INK)
            canvas.text(int(width * 0.78) + 12, y + 11, str(v[3]), 100, INK)
            canvas.text(width - 12, y + 9, ">", 20, GOLD, ROLE_FIGURE, "right")
        self.page.keep(ScrollList(self.page, 0, 384, w, min(200, h - 384), records, 40, recruitment))
        if not records:
            if not self.browsed:
                empty = "Klikni na Katalog cechů a zobrazí se cechy, které právě nabírají."
            elif query:
                empty = "Žádný nabírající cech neodpovídá hledání."
            else:
                empty = "Žádný cech teď nenabírá. Založ vlastní cech."
            self.page.text(12, 396, empty, w - 24, DIM)

    def recruitment_dialog(self, record):
        v, name, body = record
        d = self.popup("Profil cechu", 400)
        d.panel(24, 46, 64, 64)
        mark = d.keep(ui.MarkBox())
        mark.SetParent(d)
        mark.SetPosition(px(35), px(57))
        mark.SetIndex(v[0])
        mark.SetScale(2 * SCALE)
        mark.Show()
        d.text(104, 46, name, 430, GOLD, ROLE_TITLE)
        d.text(104, 82, localeInfo.GUILD_V2_RECRUITMENT_FAMILIES % (v[1], v[2], v[3]), 430, DIM)
        d.paragraph(104, 112, 432, 120, body or "Cech zatím nemá veřejný popis.")
        d.block(24, 250, "Do cechu se vstupuje pozvánkou. O pozvánku požádej vůdce nebo radu cechu. "
            "Pozvánka se ti pak ukáže tady v okně Cech.", 512, DIM, ROLE_CAPTION)

    def create_dialog(self):
        capability = self.model.row(m.CAPABILITY)[0]
        d = self.popup("Založit cech", 290 if R1 else 360)
        d.text(24, 46, "Nový cech", 512, INK, ROLE_TITLE)
        d.text(24, 96, "Název cechu", 180, GOLD)
        name = d.edit(209, 96, 298, namepolicy.GUILD_MAX_BYTES)
        d.text(24, 128, getattr(localeInfo, "GUILD_CREATE_NAME_LENGTH_HINT",
            "Nejvýš %d znaků včetně diakritiky." % namepolicy.GUILD_MAX_CHARACTERS), 512, DIM, ROLE_CAPTION)
        d.text(24, 150, getattr(localeInfo, "GUILD_CREATE_NAME_SPACING_HINT",
            "Slova odděl jednou mezerou."), 512, DIM, ROLE_CAPTION)
        d.text(24, 186, "Cena: " + yang(capability[0]), 512, 0xffe6c84b if R1 else GOLD, fontconfig.ROLE_CONTROL)
        d.text(24, 210, "Od úrovně " + str(capability[1]) + ". Staneš se vůdcem nového cechu.", 512, DIM)
        def submit():
            value = name.GetText()
            if not value:
                d.message.SetText("Zadej název cechu.")
                name.SetFocus()
                return False
            if not namepolicy.valid(value, namepolicy.GUILD_MAX_CHARACTERS):
                d.message.SetText(getattr(localeInfo, "GUILD_CREATE_NAME_INVALID",
                    "Zkontroluj délku názvu, znaky a mezery."))
                name.SetFocus()
                return False
            # The server refuses a founder below the capability level with the generic
            # Status::Invalid ("Zkontroluj zadané hodnoty."); say the real reason first.
            level = player.GetStatus(player.LEVEL)
            if capability[1] and level < capability[1]:
                d.message.SetText("Cech můžeš založit od úrovně %d. Tvoje postava má úroveň %d." % (capability[1], level))
                return False
            return d.submit(m.CREATE, (), value)
        name.SetReturnEvent(submit)
        d.primary("Založit cech", submit)

class GuildWindowRouter:
    """Select the modern shell before its first snapshot; old clients keep legacy."""
    def __init__(self, interface, legacy):
        self.interface, self.legacy, self.window = interface, legacy, None
        self.warp_restore = None

    def RestoreGuildV2Warp(self, state, restore_position):
        pages = {name for name, label in NAVIGATION} | {"settings", "approvals", "board", "audit"}
        if state.get("page") not in pages:
            return False
        # The native nonce is renewed after loading. Hold only presentation
        # until its first authoritative snapshot; never reopen a mutation dialog.
        self.warp_restore = (dict(state), restore_position)
        return True

    def _window(self):
        if supported():
            if not self.window:
                self.window = GuildWindow(self.interface)
            return self.window
        return self.legacy

    def Receive(self, payload):
        window = self._window()
        if window is not self.legacy:
            was_open = self.legacy.IsShow()
            self.legacy.Hide()
            window.Receive(payload)
            if self.warp_restore:
                state, restore_position = self.warp_restore
                self.warp_restore = None
                window.SelectPage(state["page"])
                restore_position(window, state)
                window.Show()
                window.SetTop()
                # The first offer after a warp was not requested by this client,
                # so it lacks personal points until a client snapshot declares them.
                if not window.pending:
                    window.request(m.SNAPSHOT)
            elif was_open:
                window.Show()

    def UpdateInvitations(self, ready):
        if self.window:
            self.window.UpdateInvitations(ready)

    def ApplicationCommand(self, *args):
        """Server command GuildAppV1 (guild catalogue applications, root/uiguildv2katalog.py)."""
        if supported():
            self._window().ApplicationCommand(args)

    @property
    def currentPage(self):
        return self._window().currentPage

    @property
    def pageWindow(self):
        return self._window().pageWindow

    def OpenCreateDialog(self):
        if not supported():
            return False
        self.legacy.Hide()
        self._window().OpenCreateDialog()
        return True

    def OpenDisbandDialog(self):
        if not supported():
            return False
        self.legacy.Hide()
        return self._window().OpenDisbandDialog()

    def OpenLeaveDialog(self):
        if not supported():
            return False
        self.legacy.Hide()
        return self._window().OpenLeaveDialog()

    def CanInviteMember(self):
        return bool(available() and self.window and self.window.can(1))

    def OpenInvite(self, name):
        self.legacy.Hide()
        return self._window().OpenInvite(name)

    def OpenInvitation(self, identifier):
        if not supported():
            return False
        self.legacy.Hide()
        return self._window().OpenInvitation(identifier)

    def Open(self):
        if supported():
            self.legacy.Hide()
        return self._window().Open()

    def CanOpen(self):
        return self._window().CanOpen()

    def IsShow(self):
        return self._window().IsShow()

    def Hide(self):
        self.legacy.Hide()
        if self.window:
            self.window.Close()

    def Destroy(self):
        self.warp_restore = None
        self.legacy.Destroy()
        if self.window:
            self.window.Destroy()
        self.interface = None

    def __getattr__(self, name):
        if name in ("SetTop", "GetWidth", "GetHeight", "GetLocalPosition", "SetPosition", "Show", "SelectPage"):
            return getattr(self._window(), name)
        return getattr(self.legacy, name)
