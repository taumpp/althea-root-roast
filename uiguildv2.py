import app
import chat
import fontconfig
import localeInfo
import namepolicy
import net
import ui
import uiUploadMark
import wndMgr
import guildv2model as m
from marketfilters import folded
from uiguildv2widgets import (ART, SCALE, Canvas, Dialog, Flat, ScrollList, SearchField, SettingsScrollBar,
    INK, DIM, GOLD, GREEN, RED, MUTED, ROLE_TITLE, ROLE_FIGURE, ROLE_CAPTION, check, native_color, px, span, scale_button)

NAVIGATION = (("overview", "Přehled"), ("goals", "Cíle a kontrakty"), ("passives", "Schopnosti"),
    ("expedition", "Výprava"), ("members", "Členové"), ("doctrines", "Doktríny"),
    ("chronicle", "Kronika"), ("materials", "Materiály"), ("treasury", "Pokladna"))
NAV_ICONS = ("overview", "contracts", "skills", "expedition", "members", "doctrines", "chronicle", "materials", "treasury")
PAGES = {
    "overview": ("Cechovní přehled", None),
    "goals": ("Cíle a kontrakty", "Společné cíle cechu a volba kontraktů"),
    "passives": ("Pasivní schopnosti", "Společné bonusy, jejich stupně a vylepšování"),
    "expedition": ("Výprava", "Společná výprava členů cechu"),
    "members": ("Členové cechu", None),
    "doctrines": ("Doktríny", "Směr, kterým se cech vydává"),
    "chronicle": ("Kronika", "Úroveň cechu a záznam jeho historie"),
    "materials": ("Cechovní materiály", "Zásoby cechu a nové přípisy v aktuálním cíli"),
    "treasury": ("Pokladna", "Yang vložený členy do cechu"),
    "settings": ("Správa cechu", "Nábor, profil a vedení cechu"),
    "board": ("Cechovní nástěnka", "Důležité zprávy pro členy cechu"),
    "approvals": ("Schvalování", "Rozhodnutí, která čekají na souhlas"),
    "audit": ("Rozšířený audit", "Záznam akcí vedení cechu"),
}
GOAL_TITLES = ("Lov meteorů", "Cechovní těžba", "Fragmenty duše")
GOAL_HINTS = ("Získávej úlomky meteoru ničením meteorů.", "Získávej cechovní rudu těžbou.",
    "Získávej fragmenty duše z vybraných bossů.")
MATERIAL_SOURCES = ("Šance při zničení meteoru", "Šance při úspěšné těžbě", "Šance při zabití vybraných bossů")
# One glossary for every page; the same words are used in all labels.
HELP = (
    ("Kronika", "Úroveň cechu (1–20) i záznam jeho historie. Každý materiál připsaný cechu přidá Kronice "
        "zkušenost. Vyšší Kronika odemyká vyšší stupně schopností."),
    ("Hodnost", "Postavení člena v cechu: Vůdce, Rada nebo Člen. Co která hodnost smí, nastavuje vůdce "
        "v Oprávněních (Členové › Hodnosti a práva)."),
    ("Stupeň schopnosti", "Síla pasivní schopnosti I–V. Nezaměňuj ho s hodností člena. Každý stupeň stojí "
        "materiály ze zásob cechu a vyžaduje určitou úroveň Kroniky."),
    ("Materiály", "Úlomky Meteoru (šance při zničení meteoru), Cechovní ruda (šance při těžbě) a Fragmenty "
        "duše (šance u vybraných bossů). Připisují se cechu samy, stačí být jeho členem."),
    ("Cíl a kontrakty", "Cíl je společný úkol s termínem. Počítají se do něj nové přípisy, zásoby se "
        "nespotřebují. Kontrakty jsou množství připravená pro příští cíl."),
    ("Mandát", "Ukazatel společné aktivity. Cech získá 1 Mandát za každých 100 připsaných materiálů, "
        "pokud přispěly aspoň tři různé účty."),
    ("Cechovní body", "Osobní body člena za příspěvek do splněného cíle a za úspěšnou výpravu. "
        "Po odchodu z cechu se nepřenášejí."),
)
# Member table: sort key, header, column start as a fraction of the row width.
MEMBER_COLUMNS = (("name", "Člen", 0.0), ("role", "Hodnost", 0.25), ("level", "Lv.", 0.38),
    ("metin", "Úlomky", 0.48), ("ore", "Ruda", 0.59), ("soul", "Fragmenty", 0.69), ("online", "Aktivita", 0.83))
NOTICE_LIMIT = 12

def supported():
    # Native availability becomes true only after the first server snapshot.
    # Its initial false value must never select a legacy mutation/UI path.
    return callable(getattr(net, "IsGuildV2Available", None))

def available():
    return bool(getattr(net, "IsGuildV2Available", lambda: False)())

class InvitationDialog(Canvas):
    """Independent, non-focus-stealing invitation; only buttons send decisions."""
    def __init__(self, owner, invitation):
        Canvas.__init__(self, None, 0, 0, 410, 204)
        self.owner, self.identifier = owner, invitation[0][0]
        self.AddFlag("float")
        self.AddFlag("movable")
        self.shell(410, 204, "Pozvánka do cechu", ui.__mem_func__(self.Close))
        self.text(205, 44, invitation[1], 362, GOLD, ROLE_FIGURE, align="center")
        self.text(205, 80, "Tento cech tě zve mezi své členy.", 362, align="center")
        self.message = self.text(24, 112, "Křížkem pozvánku odložíš na později.", 362, DIM, ROLE_CAPTION)
        self.decline = self.action("Odmítnout", 24, 158, lambda: self.decide(1), owner.can_decline(), width=150, height=28)
        self.accept = self.button("Přijmout", 216, 158, lambda: self.decide(0))
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
        self.message.SetText("Čekáme na potvrzení…")
        return True

    def Close(self):
        if self.owner and self.owner.invitation_dialog is self:
            self.owner.invitation_dialog = None
        self.owner = None
        self.Destroy()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnPressReturnKey(self):
        return True

class GuildWindow(Canvas):
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
        self.invite_requested = None
        self.invitation_requested = None
        self.pending = False
        self.pending_action = None
        self.scroll = None
        # Presentation-only state; never sent to the server.
        self.stale = True
        self.browsed = False
        self.history_wanted = None
        self.rights_draft = None
        self.member_sort = ("role", False)
        self.online_only = False
        self.queries = {}
        self.search = None
        self.search_key = None
        self.shell(width, height, "Cech", ui.__mem_func__(self.Close))
        self.sidebar = Canvas(self, 8, 26, 188, height - 30)
        self.sidebar.Show()
        self.viewport = Canvas(self, 216, 43, width - 236, height - 90)
        self.viewport.EnableScissorRect()
        self.viewport.Show()
        self.page = Canvas(self.viewport, 0, 0, width - 252, 600)
        self.page.on_wheel = ui.__mem_func__(self.wheel_page)
        self.page.Show()
        self.page_scroll = SettingsScrollBar()
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
        self.status_text = self.footer.text(0, 9, "Načítání cechu…", width - 466, DIM)
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

    def leader(self):
        return self.pid() != 0 and self.model.row(m.SUMMARY)[0][0] == self.pid()

    def can(self, right):
        return not self.pending and self.model.can(self.pid(), right)

    def request(self, action, values=(), title="", body="", identity=None):
        if not available() or (action != m.SNAPSHOT and not self.model.rows(m.CAPABILITY)):
            self.message("Načítání cechu…", DIM)
            return False
        identity = identity or self.model.identity()
        if self.pending:
            self.message("Čekáme na potvrzení předchozí akce.")
            return False
        if identity != self.model.identity():
            self.message(m.STATUS_TEXT[m.STALE])
            return False
        title_limit = {m.CREATE: 12, m.DISBAND: 12, m.CREATE_GOAL: 64, m.EDIT_GOAL: 64, m.POST_NOTICE: 64, m.INVITE: 24}.get(action, 128)
        if len(str(title).encode("utf-8")) > title_limit or len(str(body).encode("utf-8")) > 1024 or "|" in str(title) + str(body):
            self.message("Text je příliš dlouhý nebo obsahuje nepovolený znak.")
            return False
        sent = net.SendGuildV2Command(int(action), int(identity[0]), int(identity[1]), tuple(int(v) for v in values), str(title), str(body))
        if not sent:
            self.message("Akce teď není dostupná. Obnov údaje cechu.")
            return False
        self.pending = True
        self.pending_action = action
        self.message("Čekáme na potvrzení…", DIM)
        return True

    def Receive(self, payload):
        old_identity = self.model.identity()
        if not self.model.receive(payload, app.GetTime()):
            return
        action, status = payload["action"], payload["status"]
        matched_command = action == self.pending_action
        decision = self.invitation_decision
        if matched_command and action == m.ACCEPT_INVITE:
            self.invitation_decision = None
        # Server awards and periodic snapshots can arrive independently of a UI
        # operation. Only the matching native response releases its pending UI.
        if action == self.pending_action:
            self.pending = False
            self.pending_action = None
        if old_identity[0] != self.model.guild:
            self.rights_draft = None
            if self.dialog:
                self.dialog.Close()
            if self.mark_dialog:
                self.mark_dialog.Close()
        if action == m.BROWSE and status == m.OK:
            self.browsed = True
        if status == m.OK and matched_command and action not in (m.SNAPSHOT, m.BROWSE, m.HISTORY, m.VILLAGE):
            if self.dialog:
                self.dialog.Close()
            self.message("Schopnost byla vylepšena." if action == m.UPGRADE else m.STATUS_TEXT[status], GREEN)
            if action == m.INVITE:
                chat.AppendChat(chat.CHAT_TYPE_INFO, "Pozvánka do cechu byla odeslána.")
            elif action == m.ACCEPT_INVITE:
                text = "Pozvánka byla odmítnuta." if decision == 1 else "Jsi členem cechu %s." % self.model.row(m.SUMMARY)[1]
                chat.AppendChat(chat.CHAT_TYPE_INFO, text)
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
                dialog.message.SetText(m.STATUS_TEXT[status])
                dialog.accept.Enable()
                if self.can_decline():
                    dialog.decline.Enable()
        open_page = self.model.row(m.INSTANCE)[0][1]
        if open_page in (1, 2):
            self.currentPage = "chronicle" if open_page == 1 else "expedition"
            self.Show()
            self.SetTop()
        self.settle_rights(action, status, matched_command)
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
                self.message("Cech může rozpustit pouze jeho vůdce.")
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
        self.stale = True
        self.Show()
        self.SetTop()
        if not self.pending:
            self.request(m.SNAPSHOT)

    def OpenCreateDialog(self):
        # The NPC entry must obtain fresh capability/identity before opening
        # the same typed creation flow as the guild window.
        self.Open()
        self.create_requested = not available() or self.pending_action == m.SNAPSHOT
        if self.pending and not self.create_requested:
            self.message("Čekáme na potvrzení předchozí akce.")

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

    def CanOpen(self):
        return supported()

    def Close(self):
        self.disband_requested = False
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
        # The persistent search line survives re-rendering; follow its text.
        search = self.search
        if search and search.IsShow() and self.search_key:
            value = search.value()
            if value != self.queries.get(self.search_key, ""):
                self.queries[self.search_key] = value
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
        self.interface = None
        Canvas.Destroy(self)

    def SelectPage(self, name, tab=0):
        self.create_requested = False
        self.disband_requested = False
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

    def tabs(self, labels):
        for index, label in enumerate(labels):
            self.page.tab(label, index * 140, 72, lambda i=index: self.SelectPage(self.currentPage, i), self.tab == index)

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
    def render(self):
        self.stale = False
        offset = self.scroll.offset if self.scroll else 0
        self.page.clear()
        self.scroll = None
        if self.search:
            self.search.Hide()
        self.render_sidebar()
        width, height = self.page.design_width, self.page.design_height
        values, name, body = self.model.row(m.SUMMARY)
        self.title_line.SetText("Cech · " + name if self.model.guild and name else "Cech")
        in_village = bool(self.model.row(m.INSTANCE)[0][0])
        self.village_label.SetText("Opustit vesnici" if in_village else "Do cechovní vesnice")
        self.village.SetToolTipText("Vrátit se na původní mapu" if in_village else "Teleportovat do cechovní vesnice")
        if (self.model.guild or in_village) and self.model.row(m.CAPABILITY)[0][5] and not self.pending:
            self.village.Enable()
            self.village_label.SetPackedFontColor(native_color(INK))
        else:
            self.village.Disable()
            self.village_label.SetPackedFontColor(native_color(MUTED))
        if not available() or not self.model.rows(m.CAPABILITY):
            self.page.text(0, 0, "Cech", width, INK, ROLE_TITLE)
            self.page.text(0, 36, "Načítání cechu…", width, DIM)
            return
        if not self.model.guild:
            self.without_guild()
            return
        title, subtitle = PAGES.get(self.currentPage, ("Cech", None))
        if subtitle is None:
            subtitle = name + " · společné zásoby a rozvoj cechu"
            if self.currentPage == "members":
                members = self.model.rows(m.MEMBER)
                subtitle = "%s členů · %s online" % (len(members), sum(1 for row in members if row[0][7]))
        self.page.text(0, 0, title, width - 130, INK, ROLE_TITLE)
        self.page.text(0, 34, subtitle, width - 130, DIM)
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
            bar.text(94, y, "KRONIKA · ÚROVEŇ " + m.number(values[1]), 176, GOLD, fontconfig.ROLE_SECTION, "center")
            needed = values[1] * self.model.row(m.CAPABILITY)[0][6]
            bar.gauge(26, y + 22, 136, values[2] if values[1] < 20 else 1, needed if values[1] < 20 else 1, 5, 0xffbd8551)
            nav_top = y + 40
        elif loaded:
            bar.image("pennant_93x171", 48, 40, 93, 171)
            bar.text(94, 222, "Cech tě čeká", 176, DIM, align="center")
        if guild or not loaded:
            step = max(30, min(39, (h - 70 - nav_top) // 9))
            nav_top = max(nav_top, h - 72 - 9 * step)
            for index, (key, label) in enumerate(NAVIGATION):
                y = nav_top + index * step
                selected = self.currentPage == key
                role = fontconfig.ROLE_CONTROL if selected else fontconfig.ROLE_BODY
                bar.keep(Flat(bar, px(5), px(y), span(5, 176), span(y, step - 3), lambda k=key: self.SelectPage(k),
                    label, "plain", selected, guild, px(50), role, accent=True))
                bar.image("nav_" + NAV_ICONS[index] + "_28x28", 12, y + (step - 3 - 28) // 2)
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
        d = self.popup("Nápověda · pojmy cechu", 620, 700)
        d.text(24, 46, "Jak cech funguje", 652, INK, ROLE_TITLE)
        y = 88
        for term, text in HELP:
            d.text(24, y, term, 652, GOLD, fontconfig.ROLE_CONTROL)
            y += 30 + d.block(24, y + 22, text, 652, DIM)
        return d

    # ------------------------------------------------------------------ mark
    def open_mark_dialog(self):
        if not self.model.guild or not self.leader():
            self.message("Znak cechu může změnit pouze vůdce.")
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
            self.message("Znak se nepodařilo nahrát. Zkontroluj obrázek 32 × 32 px a připojení.")
        else:
            self.message("Znak byl odeslán. Jeho zobrazení se může chvíli obnovovat.", GREEN)
        return result

    # ------------------------------------------------------------------ overview
    def material_strip(self, y=76):
        width = self.page.design_width
        for kind, label in enumerate(m.MATERIALS):
            x, w = kind * (width + 16) // 3, (width - 32) // 3
            self.page.panel(x, y, w, 66)
            self.page.image(m.MATERIAL_ICONS[kind] + "_32x42", x + 14, y + 12)
            self.page.text(x + 60, y + 10, label, w - 66, DIM)
            self.page.text(x + 60, y + 32, m.number(self.model.row(m.BALANCE)[0][kind]), w - 66, INK, ROLE_FIGURE)

    def featured_passives(self):
        ranked = sorted(self.model.passive_ids(), key=lambda value: (-self.model.rank(value), value))
        return ranked[:3] if ranked and self.model.rank(ranked[0]) else (5, 6, 7)

    def page_overview(self, w, h):
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
            self.page.text(x + width - 16, 264, "›", 20, GOLD, ROLE_FIGURE, "right")
            self.page.pips(x + 16, 302, width - 32, rank, height=5)
        left = (w * 3) // 5
        goal, goal_name, goal_body = self.model.row(m.GOAL)
        now = self.model.now(app.GetTime())
        remaining = ""
        if goal[0] and not goal[3] and now < goal[2]:
            days = (goal[2] - now + 86399) // 86400
            remaining = " · ZBÝVÁ %s %s" % (days, "DEN" if days == 1 else ("DNY" if days < 5 else "DNÍ"))
        self.page.header("SPOLEČNÝ CÍL" + remaining, 0, 336, left)
        for kind in range(3):
            y = 378 + kind * 54
            self.page.image(m.MATERIAL_ICONS[kind] + "_25x32", 14, y)
            self.page.text(52, y + 1, m.MATERIALS[kind], left - 200, INK, fontconfig.ROLE_CONTROL)
            self.page.text(left - 16, y + 1, "%s / %s" % (m.number(goal[7 + kind]), m.number(goal[4 + kind])) if goal[4 + kind] else "Neaktivní",
                150, GOLD, fontconfig.ROLE_CONTROL, "right")
            self.page.gauge(52, y + 26, left - 68, goal[7 + kind], goal[4 + kind])
        x = left + 16
        self.page.header("KRONIKA CECHU", x, 336, w - x)
        self.page.image("chronicle_83x100", x + 12, 376)
        summary = self.model.row(m.SUMMARY)[0]
        self.page.text(x + 110, 384, "Úroveň " + m.number(summary[1]), w - x - 116, GOLD, ROLE_TITLE)
        needed = summary[1] * self.model.row(m.CAPABILITY)[0][6]
        self.page.text(x + 110, 418, "%s / %s" % (m.number(summary[2]), m.number(needed)) if summary[1] < 20 else "Nejvyšší úroveň", w - x - 116, DIM)
        self.page.gauge(x + 110, 444, w - x - 126, summary[2] if summary[1] < 20 else 1, needed if summary[1] < 20 else 1)
        self.page.row(x, 492, w - x, 34, lambda: self.SelectPage("chronicle", 1), style="plain")
        self.page.text(x + 14, 499, "Mandát " + m.number(summary[3]), w - x - 60, GOLD, fontconfig.ROLE_CONTROL)
        self.page.text(w - 14, 496, "›", 20, GOLD, ROLE_FIGURE, "right")

    # ------------------------------------------------------------------ passives
    def select_passive(self, identifier):
        self.selected_passive = identifier
        self.SelectPage("passives")

    def page_passives(self, w, h):
        self.tabs(("Pasivní schopnosti", "Stupně a postup"))
        ids = self.model.passive_ids()
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
            self.page.text(54, 138, m.PASSIVE_DESCRIPTIONS[identifier], w - 60, DIM)
            self.page.table_header(0, 168, w)
            for x, label, align in ((18, "Stupeň", "left"), (110, "Bonus", "left"), (250, "Vyžaduje", "left"), (w - 18, "Cena (úlomky / ruda / fragmenty)", "right")):
                self.page.text(x, 175, label, 300, GOLD, ROLE_CAPTION, align)
            for level in range(1, 6):
                data = self.model.catalog(identifier, level)[0]
                y = 200 + (level - 1) * 62
                self.page.panel(0, y, w, 56, level == rank)
                self.page.text(24, y + 17, m.ROMAN[level], 60, GOLD, fontconfig.ROLE_LARGE_BOLD)
                self.page.text(110, y + 19, m.effect(identifier, data[2]), 130, GREEN if level <= rank else INK, fontconfig.ROLE_CONTROL)
                self.page.text(250, y + 19, "Kronika " + m.number(data[3]), 150, DIM)
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
            canvas.text(66, y + 36, m.PASSIVE_DESCRIPTIONS[value], width - 150, DIM, ROLE_CAPTION)
            canvas.text(width - 44, y + 9, m.ROMAN[current], 60, GOLD if current else MUTED, fontconfig.ROLE_LARGE_BOLD, "center")
            canvas.pips(width - 76, y + 44, 64, current, height=4)
        self.list(ids, 112, min(488, h - 112), 70, draw, left)
        if compact:
            return
        x = left + 16
        self.passive_detail(self.page, x, 112, w - x, identifier, 476)

    def compact_passive(self, identifier):
        self.selected_passive = identifier
        d = self.popup("Pasivní schopnost", 535)
        self.passive_detail(d, 17, 34, d.design_width - 34, identifier, 432)

    def passive_detail(self, canvas, x, y, width, identifier, height):
        rank = self.model.rank(identifier)
        current = self.model.catalog(identifier, max(1, rank))
        upcoming = self.model.catalog(identifier, min(5, rank + 1))
        canvas.panel(x, y, width, height)
        canvas.header("VYLEPŠENÍ SCHOPNOSTI", x, y, width)
        canvas.image(m.PASSIVE_ICONS[identifier], x + 16, y + 44, 48, 48)
        canvas.text(x + 78, y + 44, current[1], width - 90, GOLD, fontconfig.ROLE_LARGE_BOLD)
        canvas.text(x + 78, y + 70, "Stupeň " + m.ROMAN[rank] + (" › " + m.ROMAN[rank + 1] if rank < 5 else " · nejvyšší"), width - 90, DIM)
        top = y + 104 + canvas.block(x + 16, y + 104, m.PASSIVE_DESCRIPTIONS[identifier], width - 32) + 8
        canvas.text(x + 16, top, m.effect(identifier, current[0][2] if rank else 0), 150, INK, ROLE_FIGURE)
        if rank < 5:
            canvas.text(x + width // 2, top + 2, "›", 30, DIM, ROLE_FIGURE, "center")
        canvas.text(x + width - 16, top, m.effect(identifier, upcoming[0][2]) if rank < 5 else "Maximum", 150, GREEN, ROLE_FIGURE, "right")
        canvas.pips(x + 16, top + 34, width - 32, rank, height=5)
        if rank == 5:
            canvas.text(x + 16, top + 60, "Nejvyšší stupeň je dosažen.", width - 32, GOLD)
            return
        self.cost_table(canvas, x + 12, top + 54, width - 24, upcoming[0][4:7])
        reason = self.upgrade_reason(upcoming)
        canvas.block(x + 14, top + 208, reason or "Materiály se vezmou z cechovních zásob.", width - 28, GOLD if reason else DIM, ROLE_CAPTION)
        canvas.button("Vylepšit na " + m.ROMAN[rank + 1], x + width - 186, y + height - 40,
            lambda: self.upgrade_dialog(identifier), not reason, tooltip=reason)

    def upgrade_reason(self, upcoming):
        if not self.model.can(self.pid(), 16 | 32):
            return "Nemáš právo vylepšovat schopnosti."
        if self.model.row(m.SUMMARY)[0][1] < upcoming[0][3]:
            return "Potřebuješ Kroniku %s." % upcoming[0][3]
        if not all(self.model.row(m.BALANCE)[0][i] >= upcoming[0][4 + i] for i in range(3)):
            return "Chybí materiál – viz červená čísla."
        if self.pending:
            return "Čekáme na potvrzení předchozí akce."
        return None

    def cost_table(self, canvas, x, y, w, costs, after=False):
        canvas.table_header(x, y, w, 26)
        canvas.text(x + 10, y + 6, "Materiál", w - 146, GOLD, ROLE_CAPTION)
        canvas.text(x + w - 86, y + 6, "Cena", 70, GOLD, ROLE_CAPTION, "right")
        canvas.text(x + w - 10, y + 6, "Po platbě" if after else "V cechu", 70, GOLD, ROLE_CAPTION, "right")
        for kind, cost in enumerate(costs):
            yy = y + 26 + kind * 42
            balance = self.model.row(m.BALANCE)[0][kind]
            canvas.image(m.MATERIAL_ICONS[kind] + "_25x32", x + 6, yy + 5)
            canvas.text(x + 38, yy + 13, m.MATERIALS[kind], w - 180)
            canvas.text(x + w - 86, yy + 13, m.number(cost), 70, INK, fontconfig.ROLE_CONTROL, "right")
            canvas.text(x + w - 10, yy + 13, m.number(balance - cost if after and balance >= cost else balance), 70,
                GREEN if balance >= cost else RED, fontconfig.ROLE_CONTROL, "right")
            canvas.bar(x + 6, yy + 41, w - 12, 1, 0xff32281e)

    def upgrade_dialog(self, identifier):
        rank = self.model.rank(identifier)
        if rank >= 5:
            return
        data = self.model.catalog(identifier, rank + 1)
        current = self.model.catalog(identifier, max(1, rank))
        affordable = all(self.model.row(m.BALANCE)[0][i] >= data[0][4 + i] for i in range(3))
        d = self.popup("Vylepšit pasivní schopnost" if affordable else "Chybí materiál", 430)
        d.image(m.PASSIVE_ICONS[identifier], 24, 46, 48, 48)
        d.text(88, 46, data[1], 440, GOLD, ROLE_TITLE)
        d.text(88, 78, "Stupeň " + m.ROMAN[rank] + " › " + m.ROMAN[rank + 1], 440, DIM)
        d.text(24, 118, m.PASSIVE_DESCRIPTIONS[identifier], 300, INK)
        d.text(536, 114, m.effect(identifier, current[0][2] if rank else 0) + " › " + m.effect(identifier, data[0][2]), 220, GREEN, ROLE_FIGURE, "right")
        self.cost_table(d, 24, 150, 512, data[0][4:7], True)
        d.text(24, 316, "Po potvrzení se použijí cechovní materiály.", 512, DIM, ROLE_CAPTION)
        reason = self.upgrade_reason(data)
        d.primary("Vylepšit na " + m.ROMAN[rank + 1], lambda: d.submit(m.UPGRADE, (identifier, rank)), reason=reason)

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
            self.page.text(84, y + 20, m.MATERIALS[kind], w - 400, GOLD, fontconfig.ROLE_LARGE_BOLD)
            self.page.text(84, y + 48, MATERIAL_SOURCES[kind], w - 400, DIM, ROLE_CAPTION)
            self.page.text(w - 220, y + 28, m.number(balance[kind]), 200, INK, ROLE_FIGURE, "right")
            self.page.text(w - 24, y + 28, "+" + m.number(goal[7 + kind]), 160, GREEN, ROLE_FIGURE, "right")
        self.page.header("DALŠÍ CECHOVNÍ ZŮSTATKY", 0, 430, w)
        self.page.image("mandate_31x37", 16, 470)
        self.page.text(60, 478, "Mandát", 200, INK)
        self.page.text(w // 2 - 30, 474, m.number(self.model.row(m.SUMMARY)[0][3]), 120, GOLD, ROLE_FIGURE, "right")
        self.page.text(w // 2 + 10, 478, "Yang v pokladně", 200, INK)
        self.page.text(w - 24, 474, m.number(balance[3]), w // 2 - 200, GOLD, ROLE_FIGURE, "right")
        self.page.text(0, 524, "Materiály jsou trvalé; do cíle se počítají jen nové přípisy.", w, DIM, ROLE_CAPTION)

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
                None if self.can(2) else ("Čekáme na potvrzení." if self.pending else "Chybí právo Volba kontraktů."))
            return
        goal, name, body = self.model.row(m.GOAL)
        self.page.text(0, 112, name or "Zatím není nastavený cíl", w, GOLD, fontconfig.ROLE_LARGE_BOLD)
        now = self.model.now(app.GetTime())
        if goal[0]:
            state = "Splněno" if goal[3] else ("Ukončeno" if now >= goal[2] else "Zbývá " + m.duration(goal[2] - now))
            self.page.text(0, 138, m.moment(goal[1]) + " – " + m.moment(goal[2]) + " · " + state, w, DIM)
        else:
            self.page.text(0, 138, "Cíl nastavuje vůdce cechu. Počítají se do něj nové přípisy materiálů.", w, DIM)
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
        self.page.text(0, 492, "Do cíle se počítají nové přípisy, zásoby se nespotřebují.", w, DIM, ROLE_CAPTION)
        active = goal[0] and now < goal[2]
        reason = None
        if not self.leader():
            reason = "Cíl nastavuje jen vůdce."
        elif active and goal[3]:
            reason = "Cíl je splněný, nový nastavíš po jeho konci."
        elif self.pending:
            reason = "Čekáme na potvrzení."
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
            d.text(66, y, m.MATERIALS[kind], 260)
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
        d.text(24, 206, "Kontrakty · nula znamená nevybraný kontrakt", 512, DIM)
        for kind in range(3):
            y = 248 + kind * 48
            d.image(m.MATERIAL_ICONS[kind] + "_25x32", 26, y - 8)
            d.text(66, y, m.MATERIALS[kind], 230)
            targets.append(d.edit(335, y, 170, 19, goal[4 + kind] if edit else proposed[kind], True))
        d.text(24, 398, "Začátek určí server. 1 týden = 7 dní.", 512, DIM, ROLE_CAPTION)
        if edit:
            d.text(24, 420, "Délku a množství lze pouze zvýšit. Příspěvky zůstávají.", 512, DIM, ROLE_CAPTION)
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
    def page_treasury(self, w, h):
        self.page.panel(0, 76, w, 70)
        self.page.image("nav_treasury_28x28", 16, 88, 38, 38)
        self.page.text(64, 86, "V pokladně", 300, DIM)
        self.page.text(64, 108, m.number(self.model.row(m.BALANCE)[0][3]) + " Yang", w - 300, GOLD, ROLE_FIGURE)
        self.page.primary("Vložit Yang", w - 186, 99, self.deposit_dialog, "Čekáme na potvrzení." if self.pending else None)
        self.page.text(0, 156, "Vložený Yang zůstává cechu. Vybrat ho zatím nelze.", w, DIM, ROLE_CAPTION)
        if self.history_kind() is None:
            self.page.text(0, 192, "Historii vkladů vidí správce pokladny a členové s právem Rozšířený audit.", w, DIM)
        else:
            self.history_list(w, h, 184)

    def deposit_dialog(self):
        d = self.popup("Vložit Yang do cechovní pokladny", 320)
        d.text(24, 46, "Vložit Yang", 512, INK, ROLE_TITLE)
        d.text(24, 82, "Vklad se odečte z tvého Yang a zůstane cechu.", 512, DIM)
        d.text(24, 126, "Částka", 180, GOLD)
        amount = d.edit(209, 126, 298, 19, "", True)
        d.text(24, 172, "Cech nyní: " + m.number(self.model.row(m.BALANCE)[0][3]) + " Yang", 512, DIM)
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
                canvas.text(16, y + 31, m.moment(v[1]) + " – " + m.moment(v[2]), width - 240, DIM, ROLE_CAPTION)
                canvas.text(width - 16, y + 18, "Splněno" if v[3] else "Nesplněno", 205, GREEN if v[3] else DIM, align="right")
            elif section in (m.AUDIT, m.CHRONICLE):
                canvas.text(16, y + 8, title + " · " + self.action_name(v[2]), width - 180, GOLD, fontconfig.ROLE_CONTROL)
                canvas.text(16, y + 31, body, width - 180, DIM, ROLE_CAPTION)
                canvas.text(width - 14, y + 18, m.moment(v[4]), 150, DIM, ROLE_CAPTION, "right")
            else:
                resource = m.MATERIALS[v[2]] if v[2] < 3 else "Yang"
                canvas.text(16, y + 8, title, 200, GOLD, fontconfig.ROLE_CONTROL)
                canvas.text(16, y + 31, m.moment(v[7]), 200, DIM, ROLE_CAPTION)
                canvas.text(232, y + 18, resource, width - 460)
                canvas.text(width - 16, y + 18, ("−" if v[8] else "+") + m.number(v[3]), 200, RED if v[8] else GREEN, fontconfig.ROLE_CONTROL, "right")
        if records:
            self.list(records, y, min(600 - y - 44, h - y - 44), 60, draw)
        elif self.pending or self.history_wanted:
            self.page.text(0, y + 12, "Načítání historie…", w, DIM)
        else:
            self.page.text(0, y + 12, "Zatím zde nejsou žádné záznamy.", w, DIM)
        bottom = min(566, h - 30)
        self.page.action("Od začátku", 0, bottom, lambda: self.history(self.model.history_kind), not self.pending, width=150)
        self.page.action("Další záznamy", w - 150, bottom, lambda: self.history(self.model.history_kind, self.model.history_next),
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
        self.tabs(("Členové", "Hodnosti a práva", "Cechovní body"))
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
            None if self.can(1) else ("Čekáme na potvrzení." if self.pending else "Zve správce členů."))
        width = w - 16
        key, descending = self.member_sort
        self.page.table_header(0, 152, w)
        for index, (column, label, fraction) in enumerate(MEMBER_COLUMNS):
            x = int(width * fraction)
            end = int(width * MEMBER_COLUMNS[index + 1][2]) if index + 1 < len(MEMBER_COLUMNS) else w
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
            canvas.row(0, y, width, 38, lambda pid=v[0]: self.member_dialog(pid), style="plain")
            canvas.rule(0, y + 39, width)
            color = GOLD if v[0] == own else (INK if v[7] else DIM)
            cells = (name, m.ROLES[v[1]], str(v[2]), m.number(v[3]), m.number(v[4]), m.number(v[5]))
            for index, text in enumerate(cells):
                x = int(width * MEMBER_COLUMNS[index][2])
                limit = int(width * (MEMBER_COLUMNS[index + 1][2] - MEMBER_COLUMNS[index][2])) - 10
                canvas.text(x + 12, y + 11, text, limit, color, fontconfig.ROLE_CONTROL if index == 0 else fontconfig.ROLE_BODY)
            x = int(width * MEMBER_COLUMNS[6][2])
            canvas.bar(x + 12, y + 17, 7, 7, GREEN if v[7] else 0xff5a5048)
            canvas.text(x + 26, y + 11, "Online" if v[7] else "Offline", width - x - 30, GREEN if v[7] else DIM)
        self.list(rows, 182, min(378, h - 182), 40, draw)
        if not rows:
            self.page.text(12, 196, "Žádný člen neodpovídá hledání." if self.query() or self.online_only else "Cech zatím nemá členy.", w, DIM)
        self.page.text(0, 572, "Příspěvky v aktuálním cíli · klikni na člena pro detail a akce", w, DIM, ROLE_CAPTION)

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
            rows.sort(key=lambda row: folded(row[1]), reverse=descending)
        else:
            rows.sort(key=lambda row: folded(row[1]))
            rows.sort(key=lambda row: row[0][index[key]], reverse=descending)
        return rows

    def points_page(self, w, h):
        help_text = ("Rodinné cechovní body získávají všechny postavy stejného účtu společně. "
            "Body patří členství rodiny v cechu; po odchodu se nepřenášejí.") if self.family_mode() else m.POINTS_HELP
        top = 112 + self.page.block(0, 112, help_text, w, DIM) + 12
        self.page.table_header(0, top, w)
        self.page.text(16, top + 7, "Pořadí · člen", w - 240, GOLD, fontconfig.ROLE_SECTION)
        self.page.text(w - 16, top + 7, "Cechovní body", 200, GOLD, fontconfig.ROLE_SECTION, "right")
        own = self.pid()
        def draw(canvas, record, y, width):
            place, (v, name, body) = record
            canvas.panel(0, y, width, 40, v[0] == own)
            canvas.text(14, y + 11, str(place) + ".", 44, GOLD, fontconfig.ROLE_CONTROL)
            canvas.bar(62, y + 17, 7, 7, GREEN if v[7] else 0xff5a5048)
            canvas.text(78, y + 11, name, width - 300, INK if v[7] else DIM, fontconfig.ROLE_CONTROL)
            canvas.text(width - 16, y + 11, m.number(v[8]), 200, GOLD, fontconfig.ROLE_CONTROL, "right")
        self.list(self.model.ranking(), top + 34, min(600 - top - 44, h - top - 44), 46, draw)

    def member_dialog(self, pid):
        row = self.model.member(pid)
        if not row:
            return
        self.selected_member = pid
        v, name, body = row
        d = self.popup("Detail člena", 420)
        d.image("nav_members_28x28", 24, 46)
        d.text(64, 46, name, 470, GOLD, ROLE_TITLE)
        d.text(24, 86, m.ROLES[v[1]] + " · úroveň " + str(v[2]) + (" · online" if v[7] else " · offline"), 270, GREEN if v[7] else DIM)
        d.text(536, 86, "Cechovní body: " + m.number(v[8]), 240, GOLD, align="right")
        d.header("PŘÍSPĚVKY V AKTUÁLNÍM CÍLI", 24, 116, 512)
        for kind in range(3):
            y = 158 + kind * 42
            d.image(m.MATERIAL_ICONS[kind] + "_25x32", 26, y - 6)
            d.text(66, y, m.MATERIALS[kind], 260)
            d.text(532, y - 2, m.number(v[3 + kind]), 170, GOLD, ROLE_FIGURE, "right")
        d.rule(24, 290, 512)
        def message_member():
            d.Close()
            self.interface.unifiedMessengerRouter.Open(body if self.family_mode() and body else name)
        own = self.model.member(self.pid())
        self_target = pid == self.pid()
        role_allowed = self.leader() or (self.can(1) and own and own[0][1] == 1 and v[1] == 2)
        actions = (
            ("Napsat zprávu", message_member, None if not self_target else "Tohle jsi ty", "secondary"),
            ("Změnit hodnost", lambda: self.role_dialog(pid), "Tohle jsi ty" if self_target else (None if role_allowed else "Jen vůdce nebo Rada"), "secondary"),
            ("Předat vedení", lambda: self.confirm("Předání vedení", "Nový vůdce: " + name + ". Získá správu cechu a tvoje hodnost se změní na Člen.", m.TRANSFER, (pid,)),
                "Tohle jsi ty" if self_target else (None if self.leader() else "Jen vůdce"), "secondary"),
            ("Vyloučit", lambda: self.confirm("Vyloučit člena", "Opravdu chceš vyloučit " + ("rodinu " if self.family_mode() else "postavu ") + name + "? Dosavadní příspěvky zůstanou cechu.", m.KICK, (pid,), label="Vyloučit"),
                self.kick_reason(v, self_target), "danger"))
        for index, (label, event, reason, style) in enumerate(actions):
            x = 24 + index * 130
            d.action(label, x, 304, event, not reason and not self.pending, width=122, height=28, style=style)
            if reason:
                d.text(x + 61, 338, reason, 124, GOLD, ROLE_CAPTION, "center")

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
            self.message("Čekáme na potvrzení předchozí akce.")
            return False
        self.create_requested = False
        self.invitation_requested = None
        self.invite_requested = name
        self.Open()
        if available() and self.pending_action != m.SNAPSHOT:
            self.invite_requested = None
        return True

    def OpenInvitation(self, identifier):
        if self.pending:
            self.message("Čekáme na potvrzení předchozí akce.")
            return False
        if self.request(m.SNAPSHOT):
            self.invitation_requested = identifier
            return True
        return False

    def can_decline(self):
        return self.model.row(m.CAPABILITY)[1] == "invite-decision-v1"

    def valid_invitation(self, identifier):
        if self.model.guild:
            return None
        now = self.model.now(app.GetTime())
        return next((row for row in self.model.rows(m.INVITATION)
                     if row[0][0] == identifier and row[0][2] > now), None)

    def confirm_invitation(self, identifier):
        if not self.valid_invitation(identifier):
            self.message("Pozvánka už není platná nebo už jsi členem cechu.")
            return False
        self.invitation_requested = identifier
        return True

    def UpdateInvitations(self, ready):
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
        d = self.popup("Pozvat člena", 300)
        d.text(24, 46, "Pozvat do cechu", 512, INK, ROLE_TITLE)
        d.text(24, 96, "Jméno rodiny" if self.family_mode() else "Jméno postavy", 165, GOLD)
        name = d.edit(201, 96, 305, 24)
        name.SetText("" if self.family_mode() else initial_name)
        d.text(24, 140, ("Zadej jméno rodiny, nikoli postavy. " if self.family_mode() else "") +
            "Pozvánka platí jeden den. Členství vznikne jejím přijetím.", 512, DIM, multiline=True)
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
        self.page.block(0, 548, "Vůdce má vždy všechna práva. Cíl cechu a předání vedení zůstávají jemu.", w - 340, DIM, ROLE_CAPTION)
        if not editable:
            self.page.text(w, 560, "Oprávnění může měnit jen vůdce.", 320, GOLD, align="right")
            return
        dirty = bool(self.rights_draft) and self.rights_draft[1:] != [saved[1], saved[2]]
        self.page.action("Zrušit změny", w - 316, 559, self.discard_rights, dirty and not self.pending, width=130, height=30)
        if dirty and self.pending:
            self.page.primary("Uložit oprávnění", w - 170, 560, self.save_rights, "Čekáme na potvrzení.")
        else:
            self.page.button("Uložit oprávnění", w - 170, 560, self.save_rights, dirty)

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
                reason = "Čekáme na potvrzení."
            self.page.primary("Změnit doktrínu" if doctrine[0] else "Zvolit doktrínu", x + width - 188, 488,
                lambda v=value: self.confirm("Změna doktríny", "Zvolit doktrínu " + m.DOCTRINES[v] + "? " +
                    ("První volbu potvrzuje vůdce." if not doctrine[0] else "Změna vyžaduje souhlas jiného oprávněného účtu."), m.PROPOSE_DOCTRINE, (v,)),
                reason)

    def page_approvals(self, w, h):
        self.page.text(0, 76, "Rozhodnutí jsou vázaná na konkrétní návrh a jeho původní stav.", w, DIM)
        def draw(canvas, row, y, width):
            v, title, body = row
            actor = self.model.member(v[2])
            canvas.panel(0, y, width, 82)
            canvas.text(16, y + 14, "Doktrína: " + m.DOCTRINES[v[3]], width - 340, GOLD, fontconfig.ROLE_LARGE_BOLD)
            canvas.text(16, y + 44, (actor[1] if actor else "Bývalý člen") + " · " + m.moment(v[4]), width - 340, DIM)
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
            self.page.text(66, y + 42, "%s %s/%s · %s %s/%s" % (labels[0], m.number(v[1]), m.number(v[2]), labels[1], m.number(v[3]), m.number(v[4])), w - 280, DIM)
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
        self.page.header("ÚČASTNÍCI · %s" % len(participants), 0, 152, w)
        def draw(canvas, row, y, width):
            v = row[0]
            member = self.model.member(v[0])
            canvas.panel(0, y, width, 40)
            canvas.text(16, y + 11, member[1] if member else "—", width - 285, GOLD, fontconfig.ROLE_CONTROL)
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
            reason = "Čekáme na potvrzení."
        self.page.primary("Spustit výpravu", w - 170, 560,
            lambda: self.confirm("Spustit výpravu", "Potvrdit připravenou sestavu a zahájit společnou výpravu?", m.START, (run[1],)), reason)

    def ready_dialog(self):
        run = self.model.row(m.EXPEDITION)[0]
        d = self.popup("Výprava · připravenost", 310)
        d.text(24, 46, "Jsi připraven vstoupit?", 512, INK, ROLE_TITLE)
        d.text(24, 90, "Odpověz do " + m.moment(run[2]) + ".", 512, DIM)
        d.action("Nejsem připraven", 24, 150, lambda: d.submit(m.READY, (run[1], 0)), width=180, height=28)
        d.primary("Jsem připraven", lambda: d.submit(m.READY, (run[1], 1)))

    def vote_dialog(self):
        run = self.model.row(m.EXPEDITION)[0]
        d = self.popup("Výprava · volba větve", 320)
        d.text(24, 46, "Kudy dál?", 512, INK, ROLE_TITLE)
        d.text(24, 90, "Vyber větev výpravy. Každý účastník má jeden hlas.", 512, DIM, multiline=True)
        d.text(24, 120, "Při rovnosti hlasů rozhoduje vedoucí výpravy.", 512, DIM, ROLE_CAPTION, multiline=True)
        d.action("Levá větev", 24, 172, lambda: d.submit(m.VOTE, (run[0], 1)), width=200, height=30)
        d.action("Pravá větev", 240, 172, lambda: d.submit(m.VOTE, (run[0], 2)), width=200, height=30)

    def result_dialog(self):
        run = self.model.row(m.EXPEDITION)[0]
        d = self.popup("Výprava dokončena" if run[6] == 5 else "Výprava neuspěla", 310)
        d.text(24, 46, "Výprava dokončena" if run[6] == 5 else "Výprava neuspěla", 512, INK, ROLE_TITLE)
        d.text(24, 92, "Společný výsledek je zapsaný v Kronice." if run[6] == 5 else "Výprava skončila. Můžete připravit novou sestavu.", 512, DIM, multiline=True)
        d.primary("Otevřít Kroniku", lambda: self.SelectPage("chronicle"))

    # ------------------------------------------------------------------ settings
    def page_settings(self, w, h):
        profile = self.model.row(m.PROFILE)
        self.page.header("NÁBOR A PROFIL", 0, 74, w)
        self.page.text(0, 112, "Nábor je otevřený" if profile[0][0] else "Nábor je uzavřený", 300,
            GREEN if profile[0][0] else DIM, fontconfig.ROLE_CONTROL)
        self.page.text(w, 112, "Přijímá hráče od úrovně " + str(profile[0][1]), 360, DIM, align="right")
        self.page.paragraph(0, 140, w, 64, profile[2] or "Cech zatím nemá veřejný popis.")
        self.page.primary("Upravit profil", 0, 214, self.profile_dialog,
            None if self.can(1) else ("Čekáme na potvrzení." if self.pending else "Profil upravuje správce členů."), place="right")
        self.page.header("SPRÁVA CECHU", 0, 256, w)
        leader = self.leader()
        level = self.model.row(m.SUMMARY)[0][1]
        rows = (
            ("Nástěnka", lambda: self.SelectPage("board"), "Oznámení a zprávy pro členy cechu", None, "secondary"),
            ("Schvalování", lambda: self.SelectPage("approvals"), "Rozhodnutí, která čekají na souhlas",
                None if self.model.can(self.pid(), 256) or self.model.can(self.pid(), 512) else "Chybí právo Schvalování nebo Audit", "secondary"),
            ("Oprávnění", lambda: self.SelectPage("members", 1), "Co smí Rada a Členové", None, "secondary"),
            ("Audit", lambda: self.SelectPage("audit"), "Záznam akcí vedení cechu",
                None if self.model.can(self.pid(), 512) else "Chybí právo Rozšířený audit", "secondary"),
            ("Nahrát znak", self.open_mark_dialog, "Obrázek 32 × 32 px ve složce upload",
                "Jen vůdce" if not leader else (None if level >= 1 else "Od úrovně cechu 1"), "secondary"),
            ("Opustit cech", lambda: self.confirm("Opustit cech", "Opravdu chceš opustit cech? Tvoje příspěvky zůstanou cechu a přestaneš získávat jeho bonusy.", m.LEAVE, label="Opustit cech"),
                "Tvoje příspěvky zůstanou cechu", "Vůdce musí nejdřív předat vedení" if leader else None, "danger"),
            ("Rozpustit cech", self.disband_dialog, "Ukončí cech pro všechny členy", None if leader else "Jen vůdce", "danger"))
        for index, (label, event, description, reason, style) in enumerate(rows):
            y = 294 + index * 40
            self.page.action(label, 0, y, event, not reason and not self.pending, width=170, height=30, style=style)
            room = w - 188 - (280 if reason else 0)
            if room >= 140:
                self.page.text(188, y + 7, description, room, DIM)
            if reason:
                self.page.text(w, y + 8, reason, min(270, w - 188), GOLD, ROLE_CAPTION, "right")

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
            reason = "Čekáme na potvrzení."
        self.page.primary("Napsat oznámení", w - 170, 88, self.notice_dialog, reason, place="left")
        def draw(canvas, row, y, width):
            v, title, body = row
            canvas.row(0, y, width, 102, lambda record=row: self.read_notice(record), bool(v[3]))
            canvas.text(16, y + 12, ("Připnuto · " if v[3] else "") + title, width - 190, GOLD, fontconfig.ROLE_LARGE_BOLD)
            canvas.text(width - 16, y + 14, m.moment(v[2]), 170, DIM, ROLE_CAPTION, "right")
            preview = canvas.text(16, y + 44, body.replace("\n", " "), width - 32, DIM, multiline=True)
            lines = preview.GetText().split("\n")
            if len(lines) > 2:
                preview.SetText("\n".join(lines[:2]) + "…")
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
            self.message("Cech může rozpustit pouze jeho vůdce.")
            return False
        name = self.model.row(m.SUMMARY)[1]
        d = self.popup("Rozpustit cech", 370)
        d.text(24, 46, "Rozpustit cech " + name, 512, RED, ROLE_TITLE)
        d.text(24, 86, "Tímto ukončíš cech " + name + ". Členové ztratí členství a bonusy. Pro potvrzení napiš přesný název cechu.", 512, INK, multiline=True)
        confirmation = d.edit(24, 176, 482, 12)
        d.primary("Rozpustit cech", lambda: d.submit(m.DISBAND, (), confirmation.GetText()))

    # ------------------------------------------------------------------ without guild
    def without_guild(self):
        w, h = self.page.design_width, self.page.design_height
        self.page.text(0, 0, "NAJDI SVŮJ CECH", w, GOLD, ROLE_TITLE)
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
        self.page.header("CECHY S OTEVŘENÝM NÁBOREM", 0, 280, w)
        self.page.text(0, 322, "Hledat", 60, DIM)
        self.search_field("catalog", 64, 319, 240)
        query = self.query()
        records = [row for row in self.model.rows(m.RECRUITMENT) if not query or query in folded(row[1])]
        self.page.table_header(0, 354, w)
        width = w - 16
        for x, label in ((0, "Cech"), (0.46, "Kronika"), (0.62, "Členové"), (0.78, "Od úrovně")):
            self.page.text(int(width * x) + 12, 361, label, 150, GOLD, fontconfig.ROLE_SECTION)
        def recruitment(canvas, row, y, width):
            v, name, body = row
            canvas.row(0, y, width, 38, lambda record=row: self.recruitment_dialog(record), style="plain")
            canvas.rule(0, y + 39, width)
            canvas.text(12, y + 11, name, int(width * 0.46) - 20, INK, fontconfig.ROLE_CONTROL)
            canvas.text(int(width * 0.46) + 12, y + 11, str(v[1]), 100, INK)
            canvas.text(int(width * 0.62) + 12, y + 11, str(v[2]), 100, INK)
            canvas.text(int(width * 0.78) + 12, y + 11, str(v[3]), 100, INK)
            canvas.text(width - 12, y + 9, "›", 20, GOLD, ROLE_FIGURE, "right")
        self.page.keep(ScrollList(self.page, 0, 384, w, min(200, h - 384), records, 40, recruitment))
        if not records:
            if not self.browsed:
                empty = "Klikni na „Katalog cechů“ a zobrazí se cechy, které právě nabírají."
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
        d.text(104, 82, "Kronika %s · %s členů · přijímá od úrovně %s" % (v[1], v[2], v[3]), 430, DIM)
        d.paragraph(104, 112, 432, 120, body or "Cech zatím nemá veřejný popis.")
        d.block(24, 250, "Do cechu se vstupuje pozvánkou. O pozvánku požádej vůdce nebo radu cechu; "
            "pozvánka se ti pak ukáže tady v okně Cech.", 512, DIM, ROLE_CAPTION)

    def create_dialog(self):
        capability = self.model.row(m.CAPABILITY)[0]
        d = self.popup("Založit cech", 360)
        d.text(24, 46, "Nový cech", 512, INK, ROLE_TITLE)
        d.text(24, 96, "Název cechu", 180, GOLD)
        name = d.edit(209, 96, 298, 12)
        d.text(24, 128, getattr(localeInfo, "GUILD_CREATE_NAME_LENGTH_HINT",
            "Up to 12 characters; accented letters count as two."), 512, DIM, ROLE_CAPTION)
        d.text(24, 150, getattr(localeInfo, "GUILD_CREATE_NAME_SPACING_HINT",
            "Separate words with a single space."), 512, DIM, ROLE_CAPTION)
        d.text(24, 186, "Cena: " + m.number(capability[0]) + " Yang", 512, GOLD, fontconfig.ROLE_CONTROL)
        d.text(24, 210, "Od úrovně " + str(capability[1]) + ". Staneš se vůdcem nového cechu.", 512, DIM)
        def submit():
            value = name.GetText()
            if not value:
                d.message.SetText("Zadej název cechu.")
                name.SetFocus()
                return False
            if not namepolicy.valid(value, namepolicy.GUILD_MAX_BYTES):
                d.message.SetText(getattr(localeInfo, "GUILD_CREATE_NAME_INVALID",
                    "Check the name length, characters and spaces."))
                name.SetFocus()
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
