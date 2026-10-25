# -*- coding: utf-8 -*-
"""R1 pages "Pokladna" and "Vzhled" of the guild window (root/uiguildv2r1.py mixes CosmeticPages into R1Pages).

Pokladna: the DM of the guild (donated by members, spent only on the look of the guild) next to the Yang of Guild v2
(the existing Deposit), donors of the last 30 days and the history. Nothing is ever paid out to a player.
Vzhled: the nameplate styles of the guild - basic frames free, premium frames / colours for DM (30 days or permanent),
a limited edition with an end date; only the leader buys and puts a style on, everybody sees what the guild wears.
Data: root/guildcosmetic.py (MODEL), server game/src/guild_cosmetic.cpp."""
import time

import fontconfig
import ui

import guildcosmetic as gc
import guildv2model as m
import uiguildv2widgets as widgets
from uiguildv2widgets import INK, DIM, GOLD, GREEN, MUTED, ROLE_CAPTION, LOCKED_HINT, lock_image, px, span

ROW = 36
PAGE_KEYS = ("pokladna", "vzhled")


def _caption(canvas, x, y, text, width, color=MUTED, align="left"):
    return canvas.text(x, y, text, width, color, ROLE_CAPTION, align)


def _date(epoch):
    try:
        return time.strftime("%d. %m. %Y", time.localtime(int(epoch)))
    except (ValueError, OverflowError):
        return "-"


def _yang(value):
    try:
        import uir1price
        return uir1price.FormatYang(value)
    except Exception:
        return m.number(value) + " Yang"


class CosmeticPages(object):
    """Methods of the GuildWindow (``self``)."""

    # ------------------------------------------------------------------ wiring
    def cosmetic_attach(self):
        if getattr(self, "_cosmetic_attached", False):
            return
        self._cosmetic_attached = True
        self._cosmetic_requested = 0.0
        gc.MODEL.listeners.append(ui.__mem_func__(self.cosmetic_changed))

    def cosmetic_changed(self):
        if self.IsShow() and self.currentPage in PAGE_KEYS:
            self.render()

    def cosmetic_request(self, force=False):
        import app
        now = app.GetTime()
        if force or not gc.MODEL.loaded or now - self._cosmetic_requested > 20.0:
            self._cosmetic_requested = now
            gc.MODEL.request_state()

    def cosmetic_status(self, w, y):
        message = gc.MODEL.message
        if message:
            self.status_text.SetText(message)
        return y

    # ------------------------------------------------------------------ Pokladna
    def page_pokladna_r1(self, w):
        self.cosmetic_attach()
        if not gc.MODEL.enabled:
            return self.pokladna_locked_r1(w)
        self.cosmetic_request()
        model = gc.MODEL
        self.cosmetic_status(w, 0)
        if not model.loaded:
            self.page.text(0, 4, "Načítání pokladny...", w, DIM)
            return
        if not model.schema:
            self.page.text(0, 4, "Pokladna cechu na tomhle serveru zatím není zapnutá.", w, DIM)
            return
        # two tabs: Přehled (balances, donors) and Historie (filter, search, scroll, older pages from the server)
        for index, label in enumerate(("Přehled", "Historie")):
            self.page.tab(label, index * 140, 0, lambda i=index: self.SelectPage(self.currentPage, i), self.tab == index)
        self.footer_info.SetText("Tvoje DM: " + gc.price_text(model.coins))
        if self.tab == 1:
            return self.treasury_history_r1(w, 44)
        half = (w - 40) // 2
        y = self.section_r1("Pokladna cechu", 44)
        # two balance tiles: DM (cosmetics) and Yang (Guild v2 development)
        for index, (label, value, note, button, event) in enumerate((
                ("Dračí mince", gc.price_text(model.dm), "jen na vzhled cechu", "Darovat DM", self.donate_dialog_r1),
                ("Yang", _yang(self.model.row(m.BALANCE)[0][3]), "na rozvoj cechu", "Vložit Yang", self.deposit_dialog))):
            x = index * (half + 40)
            self.page.panel(x, y, half, 104)
            _caption(self.page, x + 16, y + 12, label, half - 32, DIM)
            self.page.text(x + 16, y + 34, value, half - 32, GOLD, fontconfig.ROLE_LARGE_BOLD)
            _caption(self.page, x + 16, y + 70, note, half - 200, MUTED)
            self.page.action(button, x + half - 166, y + 64, event, not self.pending, width=150, height=30)
        y += 104 + 12
        _caption(self.page, 0, y, "Dary jsou nevratné. Z pokladny nic neodchází hráčům, každý pohyb je v historii.", w, DIM)
        y += 34
        y = self.section_r1("Dárci za 30 dní", y)
        if not model.donors:
            self.page.text(0, y + 6, "Zatím nikdo nedaroval.", w, MUTED)
        for rank, (name, amount) in enumerate(model.donors[:5]):
            self.page.text(0, y + 8, "%d. %s" % (rank + 1, name), w - 160, GOLD if rank == 0 else INK,
                fontconfig.ROLE_CONTROL)
            self.page.text(w, y + 8, gc.price_text(amount), 160, INK, fontconfig.ROLE_CONTROL, "right")
            self.page.rule(0, y + ROW - 2, w)
            y += ROW

    def pokladna_locked_r1(self, w):
        """The looks are locked by the server (no "ON 1"): the Yang of Guild v2 as always, the DM tile with a padlock
        and "Připravujeme", no DM history, no donors and no /gcosm request."""
        half = (w - 40) // 2
        y = self.section_r1("Pokladna cechu", 0)
        self.page.panel(0, y, half, 104)
        _caption(self.page, 16, y + 12, "Yang", half - 32, DIM)
        self.page.text(16, y + 34, _yang(self.model.row(m.BALANCE)[0][3]), half - 32, GOLD, fontconfig.ROLE_LARGE_BOLD)
        _caption(self.page, 16, y + 70, "na rozvoj cechu", half - 200, MUTED)
        self.page.action("Vložit Yang", half - 166, y + 64, self.deposit_dialog, not self.pending, width=150, height=30)
        x = half + 40
        self.page.panel(x, y, half, 104)
        self.page.keep(lock_image(self.page, px(x + 14), px(y + 10)))
        _caption(self.page, x + 40, y + 12, "Dračí mince", half - 56, MUTED)
        self.page.text(x + 16, y + 34, LOCKED_HINT, half - 32, MUTED, fontconfig.ROLE_LARGE_BOLD)
        soon = gc.soon_text()
        if soon:
            _caption(self.page, x + 16, y + 70, soon, half - 32, MUTED)
        self.footer_info.SetText("")

    def treasury_history_r1(self, w, y):
        """Owner 12. 10.: the history must scroll and be searchable. Filter tabs by kind, a name search (the server
        filters, so older records are found too), a scroll list (wheel + bar) and "Starší záznamy" for the next page."""
        model = gc.MODEL
        kind_filter, name_filter = model.history_filter
        self.search_field("pokladna", 0, y, 240)
        query = self.queries.get("pokladna", "").strip()          # the server matches a part of the name
        if model.history_wanted is None and (query != name_filter or not getattr(self, "_history_loaded", False)):
            self._history_loaded = True
            model.request_history(kind_=kind_filter, name=query)
        x = 256
        for value, label in gc.LOG_FILTERS:
            self.page.action(label, x, y, lambda v=value: self.treasury_filter(v), True, width=104, height=28,
                selected=kind_filter == value)
            x += 110
        y += 44
        self.page.table_header(0, y, w)
        for label, cx, align in (("Kdy", 12, "left"), ("Kdo", 130, "left"), ("Co", 290, "left"), ("Částka", w - 12, "right")):
            _caption(self.page, cx, y + 8, label, 160, DIM, align)
        y += 34

        def draw(canvas, row, ry, width):
            created, kind_, amount, item, who = row
            what = gc.LOG_KINDS.get(kind_, "Pohyb")
            if kind_ in (2, 3):
                what += ": " + (gc.name(item) if item else "sundáno")
            canvas.text(12, ry + 8, _date(created), 110, DIM, ROLE_CAPTION)
            canvas.text(130, ry + 7, who, 150, INK, fontconfig.ROLE_CONTROL)
            canvas.text(290, ry + 7, what, width - 290 - 150, INK)
            if kind_ in (1, 2, 4, 5):
                text = ("-" if kind_ == 2 else "+") + (_yang(amount) if kind_ == 5 else gc.price_text(amount))
                canvas.text(width - 12, ry + 7, text, 150, widgets.RED if kind_ == 2 else GREEN, fontconfig.ROLE_CONTROL,
                    "right")
            canvas.rule(0, ry + ROW - 2, width)
        rows = model.history
        self.list(rows, y, 300, ROW, draw, w)
        if not rows:
            self.page.text(12, y + 12, "Načítání historie..." if model.history_wanted is not None else
                "Nic neodpovídá filtru.", w, MUTED)
        bottom = y + 300 + 10
        _caption(self.page, 0, bottom + 6, "%d záznamů%s" % (len(rows), " · jsou i starší" if model.history_more else ""),
            w - 220, DIM)
        self.page.action("Starší záznamy", w - 200, bottom, lambda: gc.MODEL.request_history(more=True),
            model.history_more and model.history_wanted is None, width=200, height=28)

    def treasury_filter(self, value):
        gc.MODEL.request_history(kind_=value)
        self.render()

    def donate_dialog_r1(self):
        model = gc.MODEL
        d = self.popup("Darovat DM cechu", 330)
        d.text(24, 50, "Dar se odečte z tvých dračích mincí a zůstane cechu. Vůdce za něj koupí vzhled pro všechny.",
            d.design_width - 48, DIM, multiline=True)
        d.text(24, 104, "Máš %s · cech má %s" % (gc.price_text(model.coins), gc.price_text(model.dm)), 512, INK)
        amount = d.edit(209, 144, 140, 6, "100", True)
        d.text(24, 146, "Částka (DM)", 180, GOLD)
        x = 24
        for step in gc.DONATE_STEPS:
            d.action(str(step), x, 186, lambda value=step: amount.SetText(str(value)), True, width=90, height=28)
            x += 98
        anonymous = {"on": False}

        def toggle():
            anonymous["on"] = not anonymous["on"]
            widgets.check(box, anonymous["on"])
        box = d.checkbox(24, 232, False, toggle)
        d.text(50, 230, "Darovat anonymně (v historii a mezi dárci jako Anonym)", 470, INK)

        def submit():
            try:
                value = int(amount.GetText())
            except ValueError:
                d.message.SetText("Zadej číslo.")
                return
            if value < 10 or value > 50000:
                d.message.SetText(gc.CODES["amount"])
                return
            if value > model.coins:
                d.message.SetText(gc.CODES["coins"])
                return
            model.donate(value, anonymous["on"])
            d.Close()
        d.primary("Darovat", submit)

    # ------------------------------------------------------------------ Vzhled
    def page_vzhled_r1(self, w):
        self.cosmetic_attach()
        if not gc.MODEL.enabled:            # SelectPage keeps a locked page closed; never ask the server for it
            self.page.text(0, 4, LOCKED_HINT, w, DIM)
            return
        self.cosmetic_request()
        model = gc.MODEL
        self.cosmetic_status(w, 0)
        if not model.loaded:
            self.page.text(0, 4, "Načítání vzhledu cechu...", w, DIM)
            return
        if not model.schema:
            self.page.text(0, 4, "Vzhled cechu na tomhle serveru zatím není zapnutý.", w, DIM)
            return
        values, guild_name, body = self.model.row(m.SUMMARY)
        y = self.section_r1("Jméno cechu nad hlavou", 0)
        # the two slots are worn together: the preview shows the frame with the name colour
        gc.ReloadTuning() if not getattr(self, "_tuning_loaded", False) else None
        self._tuning_loaded = True
        self.cosmetic_preview(0, y, w, model.worn_items, guild_name or "Cech")
        for row, (slot, label) in enumerate(gc.KINDS):
            item = model.worn_of(slot)
            ry = y + row * 32
            text = "%s: %s" % (label, gc.name(item) if item else "výchozí")
            expire = model.owned.get(item)
            if item and expire:
                text += " · do " + _date(expire)
            self.page.text(w - 112, ry + 4, text, 330, GOLD if item else DIM, fontconfig.ROLE_CONTROL, "right")
            if item and model.leader():
                self.page.action("Sundat", w - 100, ry, lambda s_=slot: gc.MODEL.take_off(s_), not self.pending,
                    width=100, height=26)
        notes = []
        if not gc.supported():
            notes.append("Tvoje verze hry vzhled jména zatím nekreslí; ostatní ho uvidí.")
        if not model.leader():
            notes.append("Kupuje a mění jen vůdce. Ty můžeš do pokladny darovat DM.")
        y += 64
        for note in notes:
            _caption(self.page, 0, y, note, w, DIM)
            y += 22
        y += 8
        y = self.pending_banner_r1(w, y)
        # one group per tab (the page never scrolls): Základní / Rámečky / Barvy / Limitka
        groups = [(group, title) for group, title in gc.GROUPS if self.cosmetic_entries(group)]
        if self.tab >= len(groups):
            self.tab = 0
        for index, (group, title) in enumerate(groups):
            self.page.tab(title.split(" – ")[0], index * 140, y, lambda i=index: self.SelectPage(self.currentPage, i),
                self.tab == index)
        y += 44
        # a scroll list: the rows of a group fit any height (a waiting purchase banner, more items later)
        rows = self.cosmetic_entries(groups[self.tab][0])
        height = max(ROW + 18, min(len(rows) * (ROW + 18), (self.page.design_height - 16 - y) // (ROW + 18) * (ROW + 18)))
        self.list(rows, y, height, ROW + 18, lambda canvas, entry, ry, width: self.cosmetic_row(width, ry, entry, canvas), w)
        self.footer_info.SetText("Pokladna: " + gc.price_text(model.dm))

    def cosmetic_image(self, path, left, top, scale_x=1.0):
        """An unscaled nameplate texture at pixel (left, top) of the page (the nameplate is drawn 1:1 in game)."""
        image = self.page.keep(ui.ExpandedImageBox())
        image.SetParent(self.page)
        image.AddFlag("not_pick")
        image.LoadImage(path)
        image.SetPosition(int(left), int(top))
        if scale_x != 1.0:
            image.SetScale(scale_x, 1.0)
        image.Show()
        return image

    def cosmetic_preview(self, x, y, w, pair, name):
        """The guild line as the nameplate draws it: <plate>_l / _m (stretched) / _r 1:1 and the name in the style
        colour (the UI text has no gradient; the nameplate has)."""
        look = gc.combined(pair) if isinstance(pair, tuple) else gc.look(pair)
        color, gradient, outline, plate, pad, swatch = look if look else (0xFFEFD3FF, 0, 0xFF000000, "", 6, 0)
        probe = ui.TextLine()
        probe.SetFontName(widgets.font(fontconfig.ROLE_CONTROL))
        probe.SetText(name)
        text_w = widgets.uir1.TextWidth(probe) if widgets.uir1 else len(name) * 7
        left, top = px(x) + 6, px(y) + 8
        if plate:
            try:
                root = gc.PLATE_ROOT + plate
                cap_l = self.cosmetic_image(root + "_l.tga", left, top)
                inner = text_w + 2 * pad
                mid = self.cosmetic_image(root + "_m.tga", left + cap_l.GetWidth(), top)
                mid_w_native = max(1, mid.GetWidth())
                mid.SetScale(float(inner) / mid_w_native, 1.0)
                self.cosmetic_image(root + "_r.tga", left + cap_l.GetWidth() + inner, top)
                text_left = left + cap_l.GetWidth() + pad
                text_top = top + (cap_l.GetHeight() - 14) // 2
            except Exception:
                text_left, text_top = left, top
        else:
            text_left, text_top = left, top
        line = self.page.keep(ui.TextLine())
        line.SetParent(self.page)
        line.SetFontName(widgets.font(fontconfig.ROLE_CONTROL))
        line.SetPackedFontColor(widgets.native_color(color))
        if hasattr(line, "SetOutline"):
            line.SetOutline()
        line.SetPosition(int(text_left), int(text_top))
        line.AddFlag("not_pick")
        line.SetText(name)
        line.Show()

    def pending_banner_r1(self, w, y):
        """KO4=A: a purchase above 1 000 DM waiting for a second member of the leadership."""
        model = gc.MODEL
        if not model.pending:
            return y
        item, permanent, price, requester, name, created = model.pending
        me = self.pid()
        self.page.panel(0, y, w, 52)
        self.page.text(14, y + 6, "Čeká na potvrzení: " + gc.name(item), w - 330, GOLD, fontconfig.ROLE_CONTROL)
        _caption(self.page, 14, y + 28, "%s · %s · navrhl %s" % ("trvale" if permanent else "30 dní", gc.price_text(price),
            name), w - 330, DIM)
        leadership = model.role in (1, 2)
        self.page.action("Potvrdit", w - 300, y + 12, gc.MODEL.confirm, leadership and requester != me, width=140,
            height=28)
        self.page.action("Zrušit", w - 152, y + 12, gc.MODEL.reject, leadership or requester == me, width=140, height=28,
            style="danger")
        return y + 64

    def cosmetic_entries(self, group):
        model = gc.MODEL
        return [entry for entry in gc.CATALOG if entry[2] == group and (group != gc.LIMITED or
            model.available(entry[0]) or model.owns(entry[0]))]

    def cosmetic_row(self, w, y, entry, page=None):
        page = page or self.page
        model = gc.MODEL
        item, title, group, rent, perm, until, look = entry
        owned = model.owns(item)
        active = model.worn(item)
        unlocked = model.unlocked(item)                         # KO2=C: the guild level unlocks it
        page.row(0, y, w, ROW + 14, None, selected=active, style="plain", enabled=False)
        page.pixel_bar(px(10), px(y + 16), span(10, 18), span(y + 16, 18), look[5])
        page.text(40, y + 3, title, 260, GOLD if active else INK, fontconfig.ROLE_CONTROL)
        if not unlocked:
            note = "Od úrovně cechu %d" % gc.level(item)
            if group != gc.FREE:
                note += " · " + " · ".join(part for part in (
                    ("%s / 30 dní" % gc.price_text(rent)) if rent else "", ("%s trvale" % gc.price_text(perm)) if perm else "")
                    if part)
        elif group == gc.FREE:
            note = "Zdarma" + (" od úrovně %d" % gc.level(item) if gc.level(item) > 1 else " pro každý cech")
        elif owned:
            expire = model.owned.get(item, 0)
            note = "Vlastníte trvale" if not expire else "Vlastníte do " + _date(expire)
        else:
            parts = []
            if rent:
                parts.append("%s / 30 dní" % gc.price_text(rent))
            if perm:
                parts.append("%s trvale" % gc.price_text(perm))
            note = " · ".join(parts)
            if until:
                note += " · jen do " + _date(until)
        _caption(page, 40, y + 28, note, 360, GREEN if owned and group != gc.FREE else DIM)
        leader = model.leader() and not self.pending
        if active:
            _caption(page, w - 12, y + 16, "Nasazeno", 140, GREEN, "right")
        elif not unlocked:
            page.keep(widgets.lock_image(page, px(w - 30), px(y + 15)))
            _caption(page, w - 40, y + 16, "Úroveň %d" % gc.level(item), 120, MUTED, "right")
        elif owned:
            page.action("Nasadit", w - 140, y + 11, lambda i=item: gc.MODEL.use(i), leader, width=130, height=28)
        else:
            page.action("Koupit", w - 140, y + 11, lambda e=entry: self.buy_dialog_r1(e),
                leader and model.available(item), width=130, height=28)
        if unlocked and owned and group != gc.FREE and model.owned.get(item, 0) and rent:
            page.action("Prodloužit", w - 280, y + 11, lambda e=entry: self.buy_dialog_r1(e), leader, width=130,
                height=28)
        return y + ROW + 18

    def buy_dialog_r1(self, entry):
        model = gc.MODEL
        item, title, group, rent, perm, until, look = entry
        d = self.popup("Koupit: " + title, 300)
        d.text(24, 50, "Zaplatí se z pokladny cechu a hned se nasadí. Uvidí ho všichni hráči nad hlavou každého člena.",
            d.design_width - 48, DIM, multiline=True)
        d.text(24, 104, "V pokladně: " + gc.price_text(model.dm), 512, INK)
        if max(rent, perm) > gc.APPROVAL_PRICE:
            _caption(d, 24, 196, "Nákup nad %s musí potvrdit druhý člen vedení (vůdce nebo Rada)." %
                gc.price_text(gc.APPROVAL_PRICE), d.design_width - 48, GOLD)
        y = 144
        options = []
        if rent:
            options.append(("30 dní · " + gc.price_text(rent), False, rent))
        if perm:
            options.append(("Trvale · " + gc.price_text(perm), True, perm))

        def buy(permanent):
            gc.MODEL.buy(item, permanent)
            d.Close()
        x = 24
        for label, permanent, price in options:
            d.action(label, x, y, lambda p=permanent: buy(p), price <= model.dm, width=240, height=32)
            x += 256
        if not any(price <= model.dm for label, permanent, price in options):
            d.message.SetText("V pokladně není dost DM. Členové mohou darovat v Pokladně.")
