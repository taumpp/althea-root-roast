# -*- coding: utf-8 -*-
"""R1 layout of the guild window (root/uiguildv2.py GuildWindow) in the look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md),
built like the approved R1 market: a side panel with the guild header, the page list and the village button, one
content panel with a header band (page name left, a short status right) and the page body made of sections,
key / value rows and list row bands, never outlined boxes. Features after the start (uiguildv2.LOCKED) stay visible
in the side panel under "Připravujeme" (dimmed, padlock, hint) and as compact padlock rows on the pages.

GuildWindow mixes this in; uiguildv2 calls r1_build / render_r1 only while uiguildv2widgets.R1 is true. All layout
is in the design units of uiguildv2widgets (the window is 1040 x 690 units, SCALE 0.78 = 811 x 538 px). The legacy
layout of the window ("Starý vzhled") is not touched."""
import app
import fontconfig
import localeInfo
import ui
import uir1tokens as T

import guildv2model as m
import uiguildv2widgets as widgets
from uiguildcosmeticpages import CosmeticPages
from uiguildv2widgets import (Canvas, Flat, INK, DIM, GOLD, GREEN, MUTED, ROLE_CAPTION, LOCKED_HINT, lock_image,
    px, span, scrollbar)

SIDE_X, PANEL_Y, SIDE_W = 18, 46, 256           # side panel (200 px wide)
CONTENT_X = 287                                  # content panel x (its width is the rest of the window)
PAD = 16                                         # inner padding of the panels
BAND_H = 40                                      # header band of the content panel (31 px surface)
FOOT_H = 36                                      # footer bar of the content panel (28 px surface)
SURFACE, EDGE = 0xff161516, 0xff2c2829           # band / footer fill and their border line
ROW = 36                                         # key / value row and list row band (28 px)
# Členové -> Příspěvky (owner 21. 10. / 22. 10.): design widths of the value columns - five materials (the widest header
# "Úlomky"), the Yang ("12,84 mld.") and the three craft actions of this week (headers Těžba / Ryby / Kácení, the row hint
# spells them out); the actions stand a GROUP_GAP apart.
CONTRIBUTION_CELLS = (54, 54, 54, 54, 54, 78)
ACTION_CELLS = (44, 40, 47)
CELL_GAP, GROUP_GAP = 8, 16
LIVE_PAGES = (("overview", "Přehled", "overview"), ("passives", "Schopnosti", "skills"), ("members", "Členové", "members"),
    ("chronicle", "Deník", "chronicle"), ("settings", "Správa", "settings"), ("board", "Nástěnka", "messages"),
    ("pokladna", "Pokladna", "treasury"), ("vzhled", "Vzhled", "doctrines"))   # uiguildcosmeticpages
LOCKED_NAV = (("goals", "Cíle a kontrakty", "contracts"), ("passives", "Schopnosti", "skills"),
    ("expedition", "Výprava", "expedition"), ("doctrines", "Doktríny", "doctrines"), ("chronicle", "Kronika", "chronicle"),
    ("materials", "Materiály", "materials"),
    ("vzhled", "Vzhled", "doctrines"))   # Pokladna is live (uiguildcosmeticpages); Vzhled until the server's "ON 1"
NAV_ICON = {"overview": "nav_overview_28x28", "members": "nav_members_28x28", "settings": "action_settings_28x28",
    "messages": "action_messages_28x28"}
TITLES = {"overview": "Přehled", "passives": "Schopnosti", "members": "Členové", "settings": "Správa cechu",
    "board": "Nástěnka", "pokladna": "Pokladna", "vzhled": "Vzhled cechu", "chronicle": "Deník"}
# The overview names the locked features exactly as the side panel does.
SOON = (("Cíle a kontrakty", "úkoly s termínem pro celý cech"),
    ("Materiály", "zásoby cechu, ze kterých roste jeho úroveň"))


def _Yang(value):
    """The one R1 yang price of the client as text ("200.000 Yang", root/uir1price.py)."""
    try:
        import uir1price
        return uir1price.FormatYang(value)
    except Exception:
        return m.number(value) + " Yang"


def caption(canvas, x, y, text, width, color=MUTED, align="left"):
    return canvas.text(x, y, text, width, color, ROLE_CAPTION, align)


def rank_step(rank, target=None):
    """The rank line of a guild passive (owner 16. 10. 2026, never "Stupeň - -> I"): "Nenaučeno → I", "Stupeň II → III",
    "Stupeň V, nejvyšší". Words from locale_game (GUILD_V2_RANK*), the arrow from the kit (uir1tokens.ARROW)."""
    target = rank + 1 if target is None else target
    if target > 5:
        return localeInfo.GUILD_V2_RANK_MAX % m.ROMAN[5]
    start = localeInfo.GUILD_V2_RANK % m.ROMAN[rank] if rank > 0 else localeInfo.GUILD_V2_RANK_NONE
    return "%s %s %s" % (start, T.ARROW, m.ROMAN[target])


def shown_passives(model):
    """Passives the window can show: a passive without its catalog row (an older or partial snapshot) would be a blank,
    dead row in the list and a detail that cannot be drawn, so it is left out (owner 16. 10.: a click on a row showed
    nothing). Kapacita (guildv2model.CAPACITY) is the twelfth when the server sends it."""
    return tuple(value for value in model.shown_passive_ids() if model.catalog(value, max(1, model.rank(value))))


class R1Pages(CosmeticPages):
    """Methods of the R1 layout; ``self`` is the GuildWindow."""

    # ------------------------------------------------------------------ build
    def r1_build(self, width, height):
        uir1 = widgets.uir1
        self.shell(width, height, "Cech", ui.__mem_func__(self.Close))
        panel_h = height - PANEL_Y - 18
        content_w = width - CONTENT_X - 18
        # Frames first: everything else draws above them.
        self.side_frame = self.keep(uir1.Frame(self, px(SIDE_X), px(PANEL_Y), span(SIDE_X, SIDE_W),
            span(PANEL_Y, panel_h), "panel"))
        self.content_frame = self.keep(uir1.Frame(self, px(CONTENT_X), px(PANEL_Y), span(CONTENT_X, content_w),
            span(PANEL_Y, panel_h), "panel"))
        self.sidebar = Canvas(self, SIDE_X, PANEL_Y, SIDE_W, panel_h)
        self.sidebar.Show()
        # The header band and the footer bar are filled surfaces, like the market's "Můj obchod" band.
        self.band_fill = [self.pixel_bar(px(CONTENT_X) + 2, px(PANEL_Y) + 2, span(CONTENT_X, content_w) - 4,
            span(PANEL_Y, BAND_H) - 2, SURFACE), self.pixel_bar(px(CONTENT_X) + 2, px(PANEL_Y + BAND_H),
            span(CONTENT_X, content_w) - 4, 1, EDGE)]
        self.band = Canvas(self, CONTENT_X, PANEL_Y, content_w, BAND_H)        # after its surface: drawn above it
        self.band.Show()
        foot_y = PANEL_Y + panel_h - FOOT_H
        self.pixel_bar(px(CONTENT_X) + 2, px(foot_y), span(CONTENT_X, content_w) - 4, 1, EDGE)
        self.pixel_bar(px(CONTENT_X) + 2, px(foot_y) + 1, span(CONTENT_X, content_w) - 4,
            span(foot_y, FOOT_H) - 3, SURFACE)
        body_y = PANEL_Y + BAND_H + 12
        body_h = panel_h - BAND_H - 12 - FOOT_H - 8
        self.viewport = Canvas(self, CONTENT_X + PAD, body_y, content_w - 2 * PAD, body_h)
        self.viewport.EnableScissorRect()
        self.viewport.Show()
        self.body_h_r1 = body_h
        self.page = Canvas(self.viewport, 0, 0, content_w - 2 * PAD - 14, max(body_h, 520))
        self.page.on_wheel = ui.__mem_func__(self.wheel_page)
        self.page.Show()
        self.page_scroll = scrollbar()
        self.page_scroll.SetParent(self)
        self.page_scroll.SetPosition(px(CONTENT_X + content_w) - 14, px(body_y))
        self.page_scroll.SetScrollBarSize(span(body_y, body_h))
        self.page_scroll.SetMiddleBarSize(min(1.0, float(body_h) / max(body_h, 520)))
        self.page_scroll.SetScrollStep(0.15)
        self.page_scroll.SetScrollEvent(ui.__mem_func__(self.scroll_page))
        self.viewport.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel_page))
        self.page.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel_page))
        if body_h < 520:
            self.page_scroll.Show()
        else:
            self.page_scroll.Hide()             # fit_page_r1 shows it when a page is taller
        # The footer bar: the status of the last action on the left, page facts on the right.
        self.footer = Canvas(self, CONTENT_X + PAD, foot_y, content_w - 2 * PAD, FOOT_H)
        self.footer.Show()
        self.status_text = self.footer.text(0, 10, "Načítání cechu...", content_w - 2 * PAD - 260, DIM, ROLE_CAPTION)
        self.footer_info = self.footer.text(content_w - 2 * PAD, 10, "", 250, DIM, ROLE_CAPTION, "right")
        # The village is the main action of the guild at the start: the primary button of the side panel.
        self.village = self.keep(uir1.Button(self, widgets.kit(), px(SIDE_X + PAD), px(PANEL_Y + panel_h - 52),
            span(SIDE_X + PAD, SIDE_W - 2 * PAD), "Do cechovní vesnice", primary=True,
            event=lambda: self.request(m.VILLAGE), font=widgets.button_font()))
        self.village.SetToolTipText("Teleportovat do cechovní vesnice")
        self.village_label = self.village.label

    # ------------------------------------------------------------------ frame
    def render_r1(self):
        self.stale = False
        offset = self.scroll.offset if self.scroll else 0
        self.page.clear()
        self.band.clear()
        self.scroll = None
        if self.search:
            self.search.Hide()
        values, name, body = self.model.row(m.SUMMARY)
        guild = bool(self.model.guild)
        self.title_line.SetText("Cech")
        self.footer_info.SetText("")
        self.render_sidebar_r1()
        self.render_village_r1(guild)
        width = self.page.design_width
        if not widgets_available() or not self.model.rows(m.CAPABILITY):
            self.band_r1("Cech", "")
            self.page.text(0, 4, "Načítání cechu...", width, DIM)
            self.fit_page_r1(None)
            return
        if not guild:
            self.fit_page_r1(self.without_guild_katalog_r1(width))
            return
        if self.currentPage not in TITLES:
            self.currentPage, self.tab = "overview", 0
        members = self.model.rows(m.MEMBER)
        disband = self.model.disband_at()
        online = "%s online z %s" % (sum(1 for row in members if row[0][7]), len(members))
        status = ("Rozpouští se, konec %s" % m.moment(disband)) if disband else ""
        self.band_r1(TITLES[self.currentPage], status, bool(disband))
        self.footer_info.SetText(online)
        self.fit_page_r1(getattr(self, "page_%s_r1" % self.currentPage)(width))
        if self.scroll and offset:
            self.scroll.scroll.SetPos(float(min(offset, self.scroll.maximum)) / max(1, self.scroll.maximum))

    def fit_page_r1(self, bottom):
        """The page as tall as its content (``bottom``, design units; None: the default 520), the page scroll bar
        shown only when it is taller than the viewport. Owner 21. 10.: Přehled grew past the viewport (Nástěnka and
        Zásoby cechu) and its last block was cut off without a way to scroll to it."""
        body_h = getattr(self, "body_h_r1", 0)
        if not body_h:
            return
        height = max(body_h, int(bottom) + 16) if bottom else max(body_h, 520)
        if height != self.page.design_height:
            self.page.design_height = height
            self.page.SetSize(self.page.GetWidth(), span(0, height))
            self.page_scroll.SetMiddleBarSize(min(1.0, float(body_h) / height))
        if height > body_h:
            self.page_scroll.Show()
        else:
            self.page_scroll.SetPos(0)
            self.page_scroll.Hide()
        self.scroll_page()

    def band_r1(self, title, status, warning=False):
        band = self.band
        w = band.design_width
        band.text(PAD, 10, title, 200, GOLD, fontconfig.ROLE_LARGE_BOLD)
        right = w - PAD
        if self.model.guild:
            # Guild chat and the glossary (round 0 had them as painted icons) on the right of the band.
            band.action("Nápověda", right - 120, 5, self.help_dialog, True, width=120, height=28)
            band.action("Zprávy cechu", right - 268, 5, self.messages, True, width=140, height=28)
            right -= 284
        if status:
            band.text(right, 12, status, 300, widgets.RED if warning else DIM, ROLE_CAPTION, "right")

    def render_village_r1(self, guild):
        in_village = bool(self.model.row(m.INSTANCE)[0][0])
        if not guild and not in_village:
            # Without a guild the main action of the side panel founds one.
            self.village.SetText("Založit cech")
            self.village.SetToolTipText("Od úrovně %s za %s" % (self.model.row(m.CAPABILITY)[0][1] or 40,
                _Yang(self.model.row(m.CAPABILITY)[0][0] or 200000)))
            self.village.SetEvent(self.create_dialog)
            self.village.Show()
            self.village.Enable() if self.model.rows(m.CAPABILITY) and not self.pending else self.village.Disable()
            return
        self.village.SetEvent(lambda: self.request(m.VILLAGE))
        self.village.SetText("Opustit vesnici" if in_village else "Do cechovní vesnice")
        self.village.SetToolTipText("Vrátit se na původní mapu" if in_village else "Teleportovat do cechovní vesnice")
        self.village.Show()
        if self.model.row(m.CAPABILITY)[0][5] and not self.pending:
            self.village.Enable()
        else:
            self.village.Disable()

    def render_sidebar_r1(self):
        bar = self.sidebar
        bar.clear()
        values, name, body = self.model.row(m.SUMMARY)
        w = bar.design_width
        loaded = bool(self.model.rows(m.CAPABILITY))
        if not self.model.guild:
            return self.sidebar_no_guild_r1(bar, w, loaded)
        # Guild header: the real mark in a well (an empty well still looks intended), the name in Cinzel, level and
        # members under it.
        bar.keep(widgets.uir1.Frame(bar, px(PAD) - 2, px(14) - 2, 36, 32, "panel"))
        mark = bar.keep(ui.MarkBox())
        mark.SetParent(bar)
        mark.SetPosition(px(PAD), px(14))
        mark.SetIndex(self.model.guild)
        mark.SetScale(2.0)
        mark.Show()
        members = self.model.rows(m.MEMBER)
        level = max(1, values[1])
        bar.text(PAD + 52, 14, name, w - PAD - 60, GOLD, fontconfig.ROLE_WINDOW_TITLE)
        widgets_fit(bar, PAD + 52, 42, "Úroveň %s · %s členů" % (level, self.model.members_text(len(members))),
            w - PAD - 60, DIM, ROLE_CAPTION)
        bar.rule(PAD, 76, w - 2 * PAD)
        y = 84
        for key, label, icon in LIVE_PAGES:
            if self.is_locked(key):
                continue
            bar.keep(Flat(bar, px(6), px(y), span(6, w - 12), span(y, ROW + 2), lambda k=key: self.SelectPage(k),
                label, "plain", self.currentPage == key, True, px(PAD + 34), fontconfig.ROLE_CONTROL, accent=True))
            image = bar.image(NAV_ICON[icon] if icon in NAV_ICON else "nav_%s_28x28" % icon, PAD, y + 5, 28, 28)
            image.SetAlpha(1.0 if self.currentPage == key else 0.75)
            if key == "members" and self.apps.guild_rows and self.leadership():
                widgets_badge(bar, px(w - PAD) - 19, px(y + 12), len(self.apps.guild_rows))
            y += ROW + 4
            bar.rule(PAD, y - 2, w - 2 * PAD, 0xff1e1c1d)
        y += 10
        bar.header("Připravujeme", PAD, y, w - 2 * PAD)
        y += 34
        for key, label, icon in LOCKED_NAV:
            if not self.is_locked(key):
                continue
            bar.keep(Flat(bar, px(6), px(y), span(6, w - 12), span(y, 30), lambda k=key: self.SelectPage(k),
                label, "plain", False, False, px(PAD + 34), ROLE_CAPTION, hint=LOCKED_HINT, locked=True))
            image = bar.image("nav_%s_28x28" % icon, PAD + 4, y + 4, 22, 22)
            image.SetAlpha(0.3)
            y += 31


    # ------------------------------------------------------------------ helpers
    def section_r1(self, title, y, width=None):
        self.page.header(title, 0, y, width or self.page.design_width)
        return y + 36

    def pair_r1(self, x, y, label, value, width, value_color=INK):
        self.page.text(x, y + 8, label, width // 2 - 8, DIM)
        self.page.text(x + width, y + 8, value, width // 2, value_color, fontconfig.ROLE_CONTROL, "right")
        self.page.rule(x, y + ROW - 2, width, widgets.T1.LINE if widgets.T1 else 0xff2a2627)

    def locked_row_r1(self, y, title, text, width):
        self.page.keep(lock_image(self.page, px(4), px(y + 10)))
        line = self.page.text(26, y + 8, title, 300, MUTED, fontconfig.ROLE_CONTROL)
        after = 26 + int(line.GetTextSize()[0] / widgets.SCALE) + 12
        caption(self.page, after, y + 9, "– " + text, width - after)
        return y + 30

    # ------------------------------------------------------------------ Přehled
    def page_overview_r1(self, w):
        values, name, body = self.model.row(m.SUMMARY)
        members = self.model.rows(m.MEMBER)
        leader = self.model.leader_name()
        me = self.model.member(self.pid())
        level = max(1, values[1])
        y = self.section_r1("Cech", 0)
        half = (w - 40) // 2
        self.pair_r1(0, y, "Vůdce", leader, half)
        self.pair_r1(half + 40, y, "Tvoje hodnost", m.ROLES[me[0][1]] if me and me[0][1] < 3 else "-", half)
        y += ROW
        self.pair_r1(0, y, "Členové", self.model.members_text(len(members), " / "), half)
        self.pair_r1(half + 40, y, "Úroveň cechu", str(level), half)
        y += ROW + 18
        disband = self.model.disband_at()
        if disband:
            y = self.section_r1("Rozpouští se", y)
            self.page.text(0, y + 6, "Cech zanikne %s." % m.moment(disband), w - 200, widgets.RED,
                fontconfig.ROLE_CONTROL)
            if self.leader():
                self.page.action("Zrušit rozpuštění", w - 190, y, self.cancel_disband_dialog, not self.pending,
                    width=190, height=32)
            y += 54
        y = self.level_week_r1(w, y)
        y = self.section_r1("Cechovní vesnice", y)
        self.page.text(0, y - 2, "Soukromá vesnice jen pro členy cechu.", w - 230, DIM)
        self.page.text(0, y + 22, "Duši bosse z dungeonu tam vyvoláš pravým klikem.", w - 230, DIM)
        in_village = bool(self.model.row(m.INSTANCE)[0][0])
        self.page.button("Opustit vesnici" if in_village else "Do vesnice", w - 190, y, lambda: self.request(m.VILLAGE),
            bool(self.model.row(m.CAPABILITY)[0][5]) and not self.pending, width=190)
        y += 72  # the second text line ends at +44; the same gap as above a section
        y = self.section_r1("Nástěnka", y)
        notices = sorted(self.model.rows(m.NOTICE), key=lambda row: (-row[0][3], -row[0][0]))[:2]
        for values_, title, text in notices:
            self.page.row(0, y, w, ROW + 8, lambda: self.SelectPage("board"), style="plain")
            caption(self.page, 12, y + 12, "Připnuto" if values_[3] else "", 90)
            self.page.text(104, y + 10, title, w - 300, INK, fontconfig.ROLE_CONTROL)
            caption(self.page, w - 12, y + 12, m.moment(values_[2]), 170, MUTED, "right")
            y += ROW + 10
        if not notices:
            self.page.text(0, y + 6, "Na nástěnce zatím nic není.", w - 200, MUTED)
            y += 40
        self.page.action("Otevřít nástěnku", w - 190, y - 40 if not notices else y, lambda: self.SelectPage("board"),
            width=190, height=30)
        if notices:
            y += 40
        y += 14
        y = self.recent_events_r1(y, w)
        # The locked features stay listed under "Připravujeme" in the side panel; the overview shows the level.
        return y                                # the page grows to it and scrolls (fit_page_r1)

    # ------------------------------------------------------------------ Úroveň a týden (progression v2)
    def level_week_r1(self, w, y):
        """Level gauge, the guild's week and the own week; the rules in one caption line."""
        values = self.model.row(m.SUMMARY)[0]
        level = max(1, values[1])
        top = y
        y = self.section_r1("Úroveň cechu %s" % level, y)
        # Two layers: the full bar is paid in the Rozvoj dialog (task, materials, Yang); the weekly table is there too.
        self.page.action("Rozvoj a žebříček", w - 190, top + 4, self.development_dialog, True, width=190, height=28)
        if level < 20:
            needed = self.model.level_need()
            offer = self.model.levelup()
            full = values[2] >= needed
            label = ("Lišta plná, povýšení v Rozvoji" if full and offer else
                "Do úrovně %s: %s / %s" % (level + 1, m.number(values[2]), m.number(needed)))
            self.page.text(0, y, label, w // 2, GOLD if full else INK, fontconfig.ROLE_CONTROL)
            self.page.gauge(0, y + 28, w // 2 - 20, values[2], needed, 6, 0xffbd8551)
        else:
            self.page.text(0, y, "Nejvyšší úroveň", w // 2, GOLD, fontconfig.ROLE_CONTROL)
        week = self.model.week()
        if week:
            x = w // 2 + 20
            own_raw, own = self.model.member_week(self.pid())
            self.page.text(x, y, "Týden cechu: %s / %s" % (m.number(week["guild"]), m.number(week["cap"])), w - x, INK,
                fontconfig.ROLE_CONTROL)
            self.page.gauge(x, y + 28, w - x, week["guild"], week["cap"], 6)
            if own_raw < week["full"]:
                rate = "plně"
            elif own_raw < week["half"]:
                rate = "napůl"
            elif own_raw < week["quarter"]:
                rate = "ze čtvrtiny"
            else:
                rate = "už ne (strop)"
            caption(self.page, 0, y + 44, "Tvůj týden: %s / %s EXP · tvoje suroviny se teď počítají %s · nový týden %s" % (
                m.number(own), m.number(week["member_cap"]), rate, m.moment(week["end"])), w, DIM)
            return y + 82
        return y + 54

    # ------------------------------------------------------------------ Schopnosti (fronta staveb)
    def page_passives_r1(self, w):
        now = self.model.now(app.GetTime())
        build = self.model.building()
        y = self.section_r1("Právě se vylepšuje", 0)
        if build:
            identifier, rank, start, end, full = build
            data = self.model.catalog(identifier, rank)
            name = data[1] if data else "Schopnost"
            self.page.image(m.PASSIVE_ICONS.get(identifier, "passive_rank_41x41"), 0, y, 41, 41)
            self.page.text(54, y, "%s  %s" % (name, rank_step(rank - 1, rank)), w - 260, GOLD,
                fontconfig.ROLE_CONTROL)
            left = max(0, end - now)
            caption(self.page, 54, y + 24, ("Hotovo %s · zbývá %s" % (m.moment(end), m.duration(left))) if left else
                "Hotovo, načítá se…", w - 260, DIM)
            self.page.gauge(54, y + 48, w - 270, min(end - start, max(0, now - start)), max(1, end - start), 6, 0xffbd8551)
            # owner C13 (server b00e2d04): no speed-up, the build runs its full time
            y += 74
        else:
            self.page.text(0, y, "Cech teď nic nevylepšuje. Vyber schopnost a vylepšení zadej.", w, INK,
                fontconfig.ROLE_CONTROL)
            y += 30
        caption(self.page, 0, y, "Naráz jde vylepšovat jen jedna schopnost. Stupeň I trvá 4 h, II 12 h, III 24 h, IV 48 h, V 96 h.", w)
        y += 22
        caption(self.page, 0, y, "Urychlení za materiály: pětina ceny stupně ubere čtvrtinu času, nejvýš na polovinu.", w)
        y += 34
        y = self.section_r1(localeInfo.GUILD_V2_STOCK_TITLE, y)
        y = self.stock_panel_r1(w, y)
        ids = shown_passives(self.model)
        learned = sum(1 for value in ids if self.model.rank(value))
        y = self.section_r1("Schopnosti · %s / %s vylepšených" % (learned, len(ids)), y)
        building = build[0] if build else 0
        def draw(canvas, value, yy, width):
            current = self.model.rank(value)
            data = self.model.catalog(value, max(1, current))
            if not data:
                return
            # the hint says what the passive does (owner 21. 10.; Kapacita names the server's kapstep numbers)
            canvas.row(0, yy, width, ROW + 6, lambda v=value: self.compact_passive(v), style="plain",
                hint=self.model.description(value) or None)
            canvas.image(m.PASSIVE_ICONS.get(value, "passive_rank_41x41"), 6, yy + 5, 32, 32)
            canvas.text(48, yy + 10, data[1], width - 330, INK if current else DIM, fontconfig.ROLE_CONTROL)
            canvas.text(width - 250, yy + 10, m.effect(value, data[0][2]) if current else T.DASH, 90, GREEN if current else MUTED,
                fontconfig.ROLE_CONTROL, "right")
            canvas.pips(width - 140, yy + 18, 70, current, height=4)
            label = m.ROMAN[current] if current else T.DASH
            if value == building:
                label = "%s %s" % (T.ARROW, m.ROMAN[current + 1])
            canvas.text(width - 12, yy + 10, label, 60, GOLD if (current or value == building) else MUTED,
                fontconfig.ROLE_CONTROL, "right")
        self.list(ids, y, max(ROW + 8, min(len(ids), 5) * (ROW + 8)), ROW + 8, draw, w)
        self.footer_info.SetText("Klik na schopnost = detail")

    # ------------------------------------------------------------------ detail of one passive (popup)
    def passive_popup_r1(self, identifier):
        """Detail of a passive as an R1 dialog (profile 'dialog' of the kit): icon, name and rank line, what it does,
        the bonus now -> next with the five rank marks, then the running build or the price of the next rank, the
        actions in the bottom row. Sized to its content (no blank half) and placed beside the guild window, never over
        its list (owner 16. 10. 2026: the centred popup covered the rows, so a click on a row 'did nothing').
        Every spacing is a token of the kit profile (uir1tokens.PROFILE_DIALOG), converted to the window units."""
        profile = T.PROFILE_DIALOG
        unit = widgets.unit
        pad, gap, button = unit(profile["pad"]), unit(profile["gap"]), unit(profile["btn"])
        foot, head = unit(profile["foot_gap"]), unit(T.HEAD_H)
        icon, width = unit(T.SLOT) * 3 // 2, unit(profile["w_max"])
        inner = width - 2 * pad
        rank = self.model.rank(identifier)
        current = self.model.catalog(identifier, max(1, rank))
        upcoming = self.model.catalog(identifier, rank + 1) if rank < 5 else None
        if not current:
            return None
        build = self.model.building()
        building = bool(build and build[0] == identifier)
        description = self.model.description(identifier)
        text_h = widgets.block_height(description, inner) if description else 0
        line = unit(widgets.font_height(fontconfig.ROLE_CONTROL) + 8)
        note = reason = None
        caption_h = widgets.lines_height(1, ROLE_CAPTION)
        # the speed-up action, unless the window has it closed (HA-C13 speedup_open where the switch exists)
        speedup = getattr(self, "speedup_open", lambda: True)()
        if building:
            body = line + gap + 6 + (gap + caption_h if speedup else 0)
        elif upcoming:
            reason = self.upgrade_reason(upcoming)
            costs = self.passive_costs(identifier, rank + 1)
            note = reason or localeInfo.GUILD_V2_UPGRADE_COST % _Yang(self.model.rank_yang(identifier, rank + 1))
            body = 26 + len(costs) * 42 + gap + widgets.block_height(note, inner, ROLE_CAPTION)
        else:
            body = line
        top = head + pad
        height = top + icon + gap + (text_h + gap if text_h else 0) + line + 6 + gap + body + foot + button + pad
        d = self.popup("Pasivní schopnost", height, width)
        y = top
        d.image(m.PASSIVE_ICONS.get(identifier, "passive_rank_41x41"), pad, y, icon, icon)
        d.text(pad + icon + gap, y + 2, current[1], inner - icon - gap, GOLD, fontconfig.ROLE_LARGE_BOLD)
        d.text(pad + icon + gap, y + icon // 2 + 4, rank_step(rank), inner - icon - gap, DIM, fontconfig.ROLE_CONTROL)
        y += icon + gap
        if text_h:
            d.block(pad, y, description, inner, INK)
            y += text_h + gap
        d.text(pad, y, m.effect(identifier, current[0][2] if rank else 0), inner // 2 - 30, INK, fontconfig.ROLE_CONTROL)
        if upcoming:
            d.text(pad + inner // 2, y, T.ARROW, 40, DIM, fontconfig.ROLE_CONTROL, "center")
            d.text(pad + inner, y, m.effect(identifier, upcoming[0][2]), inner // 2 - 30, GREEN, fontconfig.ROLE_CONTROL,
                "right")
        y += line
        d.pips(pad, y, inner, rank, height=6)
        y += 6 + gap
        each = (inner - gap) // 2
        bottom = height - pad - button
        primary = None
        if building:
            now = self.model.now(app.GetTime())
            d.text(pad, y, localeInfo.GUILD_V2_BUILDING % (m.ROMAN[build[1]], m.moment(build[3]),
                m.duration(max(0, build[3] - now))), inner, GOLD, ROLE_CAPTION)
            d.gauge(pad, y + line + gap, inner, max(0, min(build[3], now) - build[2]), max(1, build[3] - build[2]), 6)
            d.place_message(pad, y + line + gap + 6 + gap, inner)
            if speedup:
                why = self.speedup_reason(build, now)
                primary = d.primary(localeInfo.GUILD_V2_SPEEDUP, self.speedup_dialog, reason=why,
                    equal=(pad + each + gap, bottom, each, pad))
        elif upcoming:
            self.cost_table(d, pad, y, inner, costs)
            y += 26 + len(costs) * 42 + gap
            # the line under the table: why the upgrade is not possible (the dialog message) or what it costs
            d.place_message(pad, y, inner)
            if not reason:
                d.block(pad, y, note, inner, DIM, ROLE_CAPTION)
            primary = d.primary(localeInfo.GUILD_V2_UPGRADE_TO % m.ROMAN[rank + 1],
                lambda: self.upgrade_dialog(identifier), reason=reason, equal=(pad + each + gap, bottom, each, pad))
        else:
            d.text(pad, y, "Nejvyšší stupeň je dosažen.", inner, GOLD, fontconfig.ROLE_CONTROL)
            d.place_message(pad, y + line, inner)
        if primary is None:
            d.close_button.SetPosition(widgets.px(pad + each + gap), widgets.px(bottom))
            d.close_button.SetWidth(widgets.span(pad + each + gap, each))
        d.place_beside(self)
        return d

    def stock_panel_r1(self, w, y):
        """Render server stock using shared material labels and icons; omit unavailable growth data."""
        import localeInfo
        balance = self.model.row(m.BALANCE)[0]
        stock = self.model.growth() or {}
        per = m.STOCK_PER_ROW
        column = (w - 20 * (per - 1)) // per
        shown = 0
        for key, source, field, label, icon in m.STOCK_PANEL:
            value = balance[field] if source == "balance" else stock.get(field)
            if value is None:
                continue
            x, yy = (shown % per) * (column + 20), y + (shown // per) * 40
            if icon:
                self.page.image(icon + "_25x32", x, yy)
                self.page.text(x + 34, yy + 6, "%s %s" % (getattr(localeInfo, label, key), m.number(value)), column - 34, INK)
            else:
                self.page.text(x, yy + 6, _Yang(value), column, INK)
            shown += 1
        return y + 48 + 40 * max(0, (shown - 1) // per)

    # ------------------------------------------------------------------ Členové
    def page_members_r1(self, w):
        # One toolbar line (search 24 px, Členové | Příspěvky, check box, Žádosti, Pozvat), centred on y + 15. Owner
        # 21. 10. (variant A): "Členové" lists rank, level and state, "Příspěvky" the five guild materials of each member,
        # the Yang the member deposited into the treasury (batch 7 add-on) and how often the member mined, fished and cut
        # this week (batch 8 G2, owner 22. 10.: the effort, not the luck of the material roll; the row hint spells it out).
        leadership = self.leadership()
        if not leadership:
            self.members_view = "list"
        contributions = getattr(self, "member_view", "members") == "contributions"
        # x of: search width, the two view tabs and their width, the check box, Žádosti, Pozvat (width).
        search_w, tab_x, tab_w, box_x = (140, 150, 88, 340) if leadership else (190, 204, 100, 420)
        invite_w = 119 if leadership else 150
        self.search_field("members", 0, 0, search_w)
        for index, (key, label) in enumerate((("members", "Členové"), ("contributions", "Příspěvky"))):
            x = tab_x + index * (tab_w + 2)
            selected = self.members_view != "apps" and key == ("contributions" if contributions else "members")
            self.page.keep(Flat(self.page, px(x), px(0), span(x, tab_w), span(0, 30),
                lambda k=key: self.select_member_view_r1(k), label, "tab", selected, True))
        self.page.checkbox(box_x, 8, self.online_only, self.toggle_online)
        self.page.text(box_x + 26, 6, "Jen online", 84, INK)
        if leadership:
            self.applications_toggle_r1(w - invite_w - 8 - 110, 0, 110)
        self.page.action("Pozvat člena", w - invite_w, 0, self.invite_dialog, self.can(1), width=invite_w, height=30)
        top = 46
        if self.members_view == "apps":
            if self.search:
                self.search.Hide()
            return self.page_applications_r1(w, top)
        rows, height = self.member_rows(), 340
        if contributions:
            # The biggest contributor first (all five materials together, then the deposited Yang), then by name.
            rows.sort(key=lambda row: (-sum(self.model.member_contributions(row)), -self.model.member_yang(row[0][0])))
        width = w - widgets.ScrollList.gutter_for(len(rows), height, ROW)
        grid = self.contribution_grid(width) if contributions else self.member_grid(width)
        self.page.table_header(0, top, w)
        if contributions:
            labels = ("Člen",) + tuple(getattr(localeInfo, key, key) for key in m.CONTRIBUTIONS) + (
                getattr(localeInfo, m.CONTRIBUTION_YANG, "Yang"),)
            if self.craft_actions_shown():
                labels += tuple(getattr(localeInfo, key, key) for key in m.ACTION_HEADERS)
        else:
            labels = ("Člen", "Hodnost", "Úr.", "Stav")
        # Contributions: each header and its values share the right edge and the same width (owner 21. 10. on DEV:
        # "Dřevo" ran to the right border and its "–" stood off the header).
        cells = (160,) + (self.contribution_cells(width) if contributions else (160,) * 3)
        cell = cells[1]
        for label, (x, align), size in zip(labels, grid, cells):
            caption(self.page, x, top + 8, label, size, DIM, align)
        own, selected = self.pid(), self.selected_member

        def draw(canvas, row, y, width):
            v, name, body = row
            hint = self.member_family_hint(name)
            if contributions and self.craft_actions_shown():
                hint = self.member_actions_hint(v[0], hint)
            canvas.row(0, y, width, ROW - 2, lambda pid=v[0]: self.select_member_r1(pid), selected=v[0] == selected,
                style="plain", hint=hint)
            color = GOLD if v[0] == own else (INK if v[7] else DIM)
            (nx, na), (rx, ra) = grid[:2]
            canvas.text(nx, y + 7, self.member_name(name, body), rx - nx - (cell + 4 if contributions else 16), color,
                fontconfig.ROLE_CONTROL)
            if contributions:
                # The five materials and the Yang ("12,5 mld.", "340 mil.", "200 000", rounded down), "–" for none.
                yang = self.model.member_yang(v[0])
                texts = [m.number(value) if value else "–" for value in self.model.member_contributions(row)]
                texts.append(m.short_yang(yang, True) if yang else "–")
                # Batch 8 G2: the craft actions of this week, "–" for none.
                if self.craft_actions_shown():
                    texts += [m.number(value) if value else "–" for value in self.model.member_actions(v[0])]
                for text, (cx, ca), size in zip(texts, grid[1:], cells[1:]):
                    canvas.text(cx, y + 7, text, size, MUTED if text == "–" else (INK if v[7] else DIM), align=ca)
                return
            (lx, la), (sx, sa) = grid[2:4]
            canvas.text(rx, y + 7, m.ROLES[v[1]], lx - rx - 60, INK if v[7] else DIM)
            canvas.text(lx, y + 7, str(v[2]), 80, INK if v[7] else DIM, align=la)
            # Online, or when the member last played (owner 21. 10., batch 7 add-on).
            canvas.text(sx, y + 8, self.member_state_text(v), 120, GREEN if v[7] else MUTED, ROLE_CAPTION, sa)
        self.list(rows, top + 34, height, ROW, draw, w)
        if not rows:
            self.page.text(12, top + 46, "Žádný člen neodpovídá hledání." if self.query() or self.online_only else
                "Cech zatím nemá členy.", w, MUTED)
        self.member_actions_r1(w, top + 384)

    def select_member_view_r1(self, view):
        if getattr(self, "member_view", "members") != view or self.members_view == "apps":
            self.member_view = view
            self.members_view = "list"          # a tab leaves Žádosti
            self.scroll = None
            self.render()

    def member_grid(self, w):
        """x and alignment of the member columns, shared by the header and the rows (Člen, Hodnost, Úr., Stav)."""
        return ((12, "left"), (int(w * 0.40), "left"), (int(w * 0.68), "right"), (w - 12, "right"))

    def contribution_grid(self, w):
        """Člen and nine right-aligned columns (Úlomky, Ruda, Duše, Šupiny, Dřevo, Yang, then Těžba, Rybaření, Kácení of
        this week): right edges packed from the 12 px right margin of the other tables, CONTRIBUTION_CELLS / ACTION_CELLS
        wide, the actions a GROUP_GAP apart; Člen gets the rest."""
        if not self.craft_actions_shown():
            # Older server (no Doctrine "xpcap", batch 8 G4): the former six evenly spaced columns from 40 % of the
            # width to the 12 px right margin, without the craft actions it does not send.
            first, last = int(w * 0.40), w - 12
            return ((12, "left"),) + tuple((first + (last - first) * index // 5, "right") for index in range(6))
        cells = self.contribution_cells()
        edges, edge = [], w - 12
        for index in reversed(range(len(cells))):
            edges.insert(0, edge)
            edge -= cells[index] + (GROUP_GAP if index == len(CONTRIBUTION_CELLS) else CELL_GAP)
        return ((12, "left"),) + tuple((x, "right") for x in edges)

    def craft_actions_shown(self):
        """Těžba / Ryby / Kácení and their row hint only from a server that sends Doctrine "xpcap" (batch 8 G2/G4
        server; it always sends it). An older server sends neither the actions nor the rules behind them: the client
        keeps the former six columns, so it can be released before the server."""
        return self.model.xp_ceilings() is not None

    def contribution_cells(self, w=None):
        """The widths of the contribution columns, header and values alike (they share the right edge). An older server
        (no craft actions) keeps the former even width of the six columns of a ``w`` wide table."""
        if not self.craft_actions_shown():
            return CONTRIBUTION_CELLS if w is None else ((w - 12 - int(w * 0.40)) // 5 - 6,) * len(CONTRIBUTION_CELLS)
        return CONTRIBUTION_CELLS + ACTION_CELLS

    def contribution_cell(self, w):
        """The width of the first contribution column (the name ends a gap before it)."""
        return self.contribution_cells(w)[0] if w else CONTRIBUTION_CELLS[0]

    def select_member_r1(self, pid):
        self.selected_member = 0 if self.selected_member == pid else pid
        self.render()

    def member_actions_r1(self, w, y):
        self.page.rule(0, y - 8, w)
        row = self.model.member(self.selected_member)
        if not row:
            # Batch 8 G4 (owner 22. 10.): Příspěvky shows the guild's weekly EXP against each source's ceiling above the hint.
            guild = self.guild_xp_text() if getattr(self, "member_view", "members") == "contributions" else ""
            if guild:
                caption(self.page, 0, y + 8, guild, w)
            caption(self.page, 0, y + (36 if guild else 8), "Klikni na člena a vyber, co s ním.", w)
            return
        v, name, body = row
        own = self.model.member(self.pid())
        self_target = v[0] == self.pid()
        role_allowed = not self_target and (self.leader() or (self.can(1) and own and own[0][1] == 1 and v[1] == 2))

        def message_member():
            self.interface.unifiedMessengerRouter.Open(body if self.family_mode() and body else name)
        actions = (
            ("Zpráva", message_member, not self_target, "secondary"),
            ("Hodnost", lambda: self.role_dialog(v[0]), role_allowed and not self.pending, "secondary"),
            ("Předat vedení", lambda: self.confirm("Předání vedení", "Nový vůdce: " + name +
                ". Získá správu cechu a tvoje hodnost se změní na Člen.", m.TRANSFER, (v[0],)),
                self.leader() and not self_target and not self.pending and not self.model.disband_at(), "secondary"),
            ("Vyloučit", lambda: self.confirm("Vyloučit člena", "Opravdu chceš vyloučit " + name +
                "? Do jiného cechu může až za 24 hodin.", m.KICK, (v[0],), label="Vyloučit"),
                not self.kick_reason(v, self_target) and not self.pending, "danger"))
        x = w - len(actions) * 146 + 5
        self.member_label_r1(self.member_name(name, body), m.ROLES[v[1]], y, x - 12)       # the label takes the room left of the actions
        for label, event, enabled, style in actions:
            self.page.action(label, x, y, event, enabled, width=141, height=30, style=style)
            x += 146

    def member_label_r1(self, name, role, y, width):
        """The selected member left of the actions (``width`` design units up to them), never clipped by the line's
        limit ("Azzar · Vůdc"): one line while it fits, else the name over its role; a name too long even for that is
        shortened with "..." and the hint names the member in full."""
        full = "%s · %s" % (name, role)
        room = px(width)
        probe = ui.TextLine()
        probe.SetFontName(widgets.font(fontconfig.ROLE_CONTROL))
        probe.SetText(full)
        if widgets.uir1.TextWidth(probe) <= room:
            return self.page.text(0, y + 5, full, 0, INK, fontconfig.ROLE_CONTROL)
        shown = widgets.uir1.Fit(probe, name, room)
        if shown != name:
            # the hover area under the texts (they do not pick): its hint names the member in full
            self.page.keep(Flat(self.page, px(0), px(y - 4), room, px(40), None, "", "plain", enabled=False,
                hint=full))
        line = self.page.text(0, y - 4, shown, 0, INK, fontconfig.ROLE_CONTROL)
        caption(self.page, 0, y + 17, role, width, DIM)
        return line

    def rights_r1(self, w):
        rights = self.rights_values()
        saved = self.model.row(m.RIGHTS)[0]
        editable = self.leader()
        y = self.section_r1("Oprávnění", 50)
        centers = (w - 330, w - 200, w - 70)
        self.page.table_header(0, y, w)
        caption(self.page, 12, y + 8, "Právo", 200, DIM)
        for x, label in zip(centers, ("Vůdce", "Rada", "Člen")):
            self.page.text(x, y + 8, label, 100, DIM, ROLE_CAPTION, "center")
        y += 34
        self.page.text(12, y + 8, "Zvát a vyhazovat členy, měnit hodnosti", centers[0] - 80, INK)
        for role in (0, 1, 2):
            active = bool(rights[role] & 1)
            self.page.checkbox(centers[role] - 10, y + 9, active, lambda r=role: self.change_right(r, 0),
                editable and role != 0 and not self.pending)
        self.page.rule(0, y + ROW, w)
        y += ROW + 16
        caption(self.page, 0, y, "Vůdce má vždy všechna práva. Další práva přijdou s cechovními funkcemi po startu.", w)
        dirty = bool(self.rights_draft) and self.rights_draft[1:] != [saved[1], saved[2]]
        if not editable:
            caption(self.page, 0, y + 26, "Oprávnění mění jen vůdce.", w, DIM)
        elif dirty:
            self.page.action("Zrušit", w - 316, y + 36, self.discard_rights, not self.pending, width=141, height=32)
            self.page.button("Uložit", w - 170, y + 36, self.save_rights, not self.pending)

    # ------------------------------------------------------------------ Správa
    def page_settings_r1(self, w):
        leader = self.leader()
        y = self.section_r1("Rada", 0)
        council = bool(self.model.row(m.RIGHTS)[0][1] & 1)
        self.page.checkbox(0, y + 4, council, self.toggle_council, leader and not self.pending)
        self.page.text(26, y + 2, "Rada smí zvát a vyhazovat členy", 420, INK if leader else MUTED)
        if not leader:
            caption(self.page, w, y + 4, "Mění jen vůdce.", 200, MUTED, "right")
        y += 50
        y = self.section_r1("Značka cechu", y)
        self.page.text(0, y + 6, "Obrázek 32 × 32 px (PNG) ze složky upload ve hře", w - 200, INK)
        self.page.action("Nahrát znak", w - 170, y, self.open_mark_dialog, leader and not self.pending, width=170,
            height=32)
        if not leader:
            caption(self.page, 0, y + 30, "Značku mění jen vůdce.", w - 200)
        y += 66
        y = self.section_r1("Členství", y)
        disband = self.model.disband_at()
        rows = []
        if not leader:
            rows.append(("Opustit cech", "Do jiného cechu můžeš vstoupit až za 24 hodin.",
                self.leave_dialog, True, "secondary"))
        elif disband:
            rows.append(("Zrušit rozpuštění", "Cech se rozpouští, konec %s." % m.moment(disband),
                self.cancel_disband_dialog, True, "secondary"))
        else:
            delay = self.model.has_capability(m.DISBAND_DELAY)
            rows.append(("Opustit cech", "Vůdce nejdřív předá vedení jinému členovi.", None, False, "secondary"))
            hint = ("Cech zanikne za %d hodin, do té doby jde rozpuštění zrušit." % m.DISBAND_DELAY_HOURS) \
                if delay else "Cech zanikne hned pro všechny členy."
            if self.model.has_capability(m.SOLO_DISBAND):
                hint = "Jednočlenný cech zanikne ihned, ostatní za %d hodin." % m.DISBAND_DELAY_HOURS
            rows.append(("Rozpustit cech", hint, self.disband_dialog, True, "danger"))
        for label, text, event, enabled, style in rows:
            self.page.text(0, y + 2, label, 300, INK, fontconfig.ROLE_CONTROL)
            caption(self.page, 0, y + 26, text, w - 200, DIM)
            self.page.action(label, w - 170, y + 4, event, enabled and not self.pending, width=170, height=32,
                style=style)
            y += 62
        y += 10
        y = self.recruiting_section_r1(y, w)

    # ------------------------------------------------------------------ Nástěnka
    def page_board_r1(self, w):
        records = sorted(self.model.rows(m.NOTICE), key=lambda row: (-row[0][3], -row[0][0]))
        full = len(records) >= 12
        caption(self.page, 0, 8, "%s / 12 oznámení" % len(records), 300, DIM)
        self.page.action("Napsat oznámení", w - 200, 0, self.notice_dialog, not full and not self.pending, width=200,
            height=32)

        def draw(canvas, row, y, width):
            v, title, body = row
            canvas.row(0, y, width, 70, lambda record=row: self.read_notice(record), style="plain")
            caption(canvas, 12, y + 10, "Připnuto" if v[3] else "", 90)
            canvas.text(104 if v[3] else 12, y + 8, title, width - 320, INK, fontconfig.ROLE_CONTROL)
            canvas.text(width - 12, y + 10, m.moment(v[2]), 170, MUTED, ROLE_CAPTION, "right")
            preview = body.replace("\n", " ")
            canvas.text(12, y + 38, preview if len(preview) < 90 else preview[:87] + "...", width - 24, DIM)
            canvas.rule(0, y + 72, width)
        self.list(records, 50, 430, 76, draw, w)
        if not records:
            self.page.text(0, 62, "Nástěnka zatím neobsahuje oznámení.", w, MUTED)

    # ------------------------------------------------------------------ bez cechu
    def without_guild_r1(self, w):
        capability = self.model.row(m.CAPABILITY)[0]
        self.page.text(0, 0, "Cech je parta, se kterou hraješ, máš svou vesnici a vyvoláváš v ní bosse z duší.", w, INK)
        caption(self.page, 0, 28, "Založení cechu: od úrovně %s, %s." % (
            capability[1] or 40, _Yang(capability[0] or 200000)), w, DIM)
        y = self.section_r1("Pozvánky", 70)
        now = self.model.now(app.GetTime())
        invitations = [row for row in self.model.rows(m.INVITATION) if row[0][2] > now]

        def draw(canvas, row, y, width):
            v, name, body = row
            canvas.row(0, y, width, ROW + 6, lambda i=v[0]: self.confirm_invitation(i), style="plain")
            canvas.text(12, y + 9, name, width - 400, INK, fontconfig.ROLE_CONTROL)
            canvas.text(width - 190, y + 11, "platí do " + m.moment(v[2]), 200, MUTED, ROLE_CAPTION, "right")
            canvas.action("Zobrazit", width - 153, y + 5, lambda i=v[0]: self.confirm_invitation(i), not self.pending,
                width=141, height=30)
        self.list(invitations, y, 380, ROW + 10, draw, w)
        if not invitations:
            self.page.text(0, y + 4, "Nemáš žádné platné pozvánky. Pošle ti je vůdce nebo Rada cechu.", w, MUTED)

def widgets_fit(canvas, x, y, text, width, color, role):
    import uiguildv2katalog
    return uiguildv2katalog.fitted_text(canvas, x, y, text, width, color, role)


def widgets_badge(parent, x, y, count):
    import uiguildv2katalog
    return uiguildv2katalog.badge(parent, x, y, count)


def widgets_available():
    import net
    return bool(getattr(net, "IsGuildV2Available", lambda: False)())
