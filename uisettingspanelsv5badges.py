# -*- coding: utf-8 -*-
"""Tab "Odznaky a kanály" of Settings v5 -> Panely tlačítek (2026-10-05; O1 table 2026-10-06).

Replaces the A7 popup "Odznaky…" (uisettingsbuttonbadges.BadgeSettingsPopup) inside the page: the same three
global switches (badges, states and countdowns, pulsing - greyed with its reason while badges are off), the
same per-function "Odznak" / "Stav" switches of the functions that have them (uisettingsbuttonbadges
.FUNCTIONS, uisettingsbuttonbadges.Capabilities), and the lock of the channel bar (uichannelbar, section
``channel_bar``). Everything is stored by the existing models; a refused write shows the shared store error.

O1 (owner's choice 2026-10-06, design v5 section 4): one compact table on one screen - the three global options as
check boxes in one line, then Funkce | Co ukazuje | Odznak | Stav with check boxes and a faint zebra, an empty
cell where a function has no such option, the channel bar lock at the bottom. The row tooltip of the shell has the
full text of a row.
"""
import uikit
import uikittokens as T
import buttonpanelbadges as badges
import buttonpanelsv5 as model
import uisettingsbuttonbadges as rows_model
from settingslocale import Text as Tr
from uisettingspanelsv5widgets import Image, FitText

GLOBAL_ROWS = (
    ('enabled', Tr('Odznaky (tečka / číslo)', 'Badges (dot / number)'),
     Tr('rubínová = čeká akce, zlatá = běží nebo je nové', 'ruby = an action waits, gold = live or new')),
    ('state', Tr('Stav a odpočty', 'States and countdowns'),
     Tr('zlatý rám, záře při běhu, výseč s časem', 'gold rim, glow while running, countdown sector')),
    ('pulse', Tr('Pulzování', 'Pulsing'), Tr('rubínový odznak jemně dýchá', 'the ruby badge gently breathes')),
)
PULSE_OFF = Tr('jen se zapnutými odznaky', 'only while badges are on')


class BadgesTab(object):
    def __init__(self, page, parent, kit, track):
        self.page = page
        self.parent = parent
        self.kit = kit
        self.track = track
        self.settings = badges.Load()
        self.globals = {}      # name -> (check box, its label, note shown while it is unavailable)
        self.checks = {}       # (action, kind) -> check box
        self.pin = None

    def _Tip(self, hit, title, text):
        """The shell's row tooltip for a table row / option (title + the whole description)."""
        window = getattr(self.page, 'window', None)
        if hasattr(window, '_C9TipTick') and title:
            row = dict(key='panels_badges', kind='open', label=title, hint_text=text, band=None, hit=hit)
            hit.SetHoverEvent(lambda row=row: window._C9ShowInfo(row))
            return row
        return None

    def Build(self, y, width):
        k = self.kit
        big = k.prof == '1080'
        self.settings = badges.Load()
        check = uikit.CheckBox
        # 1) the three global options in one line
        line_h = k.p('seg_h') + (8 if big else 6)
        x = 0
        for name, label, sub in GLOBAL_ROWS:
            hit = self.track(uikit.HitArea(self.parent, x, y, 10, line_h))
            box = self.track(check(self.parent, k, x, 0, label, event=lambda name=name: self.ToggleGlobal(name)))
            box.SetPosition(x, y + (line_h - box.h) // 2)
            hit.SetSize(box.Width() + 8, line_h)
            self._Tip(hit, label, sub)
            box.SetHoverEvent(lambda hit=hit: hit.OnMouseOverIn())
            note = self.track(uikit.Text(self.parent, '', x + box.Width() + 8, y + line_h // 2, k.font('S'),
                                         T.MUTED), wheel=False)
            note.Hide()
            self.globals[name] = (box, box.label, note)
            x += box.Width() + (34 if big else 22)
        y += line_h + (6 if big else 4)
        # 2) the table
        pitch = 26 if big else 23
        state_cx = width - (28 if big else 22)
        badge_cx = state_cx - (64 if big else 52)
        name_x = 28 if big else 24
        import minimappanelicons
        names_w = 0
        probe = uikit.Text(self.parent, '', 0, 0, k.font('M'), T.INK)
        functions = rows_model.ShownFunctions()
        for unused, name, unused2 in functions:
            probe.SetText(name)
            names_w = max(names_w, uikit.TextWidth(probe))
        probe.Hide()
        shows_x = min(name_x + names_w + (24 if big else 16), badge_cx - 150)
        head_y = y + (pitch - k.cell('S')) // 2
        for text, hx, align in ((Tr('Funkce', 'Function'), 0, 'left'), (Tr('Co ukazuje', 'What it shows'), shows_x, 'left'),
                                (Tr('Odznak', 'Badge'), badge_cx, 'center'), (Tr('Stav', 'State'), state_cx, 'center')):
            self.track(uikit.Text(self.parent, text, hx, head_y, k.font('S'), T.MUTED, align=align, valign='top'),
                       wheel=False)
        self.track(uikit.HLine(self.parent, 0, y + pitch - 1, width, T.BRONZE_LINE_DK), wheel=False)
        y += pitch
        s = k.p('check')
        for index, (action, name, shows) in enumerate(functions):
            has_badge, has_state = rows_model.Capabilities(action)
            icon_id = rows_model.CHANNEL_IDS[0] if action == rows_model.CHANNEL_PREFIX else action
            if index % 2:
                self.track(uikit.Rect(self.parent, 0, y, width, pitch, T.PANEL_HI, .55), wheel=False)
            hit = self.track(uikit.HitArea(self.parent, 0, y, width, pitch))
            self._Tip(hit, name, shows)
            icon = self.track(Image.Make(self.parent, minimappanelicons.Visual(icon_id), 0, y + (pitch - 20) // 2,
                                         20 / 28.0), wheel=False)
            icon.Show()
            name_line = self.track(uikit.Text(self.parent, '', name_x, y + pitch // 2, k.font('M'), T.INK),
                                   wheel=False)
            FitText(name_line, name, shows_x - name_x - 8)
            what = self.track(uikit.Text(self.parent, '', shows_x, y + pitch // 2, k.font('S'), T.MUTED), wheel=False)
            FitText(what, shows, badge_cx - 34 - shows_x)   # the whole text is in the row tooltip on hover
            for kind, supported, cx in (('badge', has_badge, badge_cx), ('state', has_state, state_cx)):
                if supported:
                    box = self.track(check(self.parent, k, cx - s // 2, y + (pitch - s) // 2,
                                           event=lambda a=action, w=kind: self.ToggleFunction(a, w)))
                    box.SetHoverEvent(lambda hit=hit: hit.OnMouseOverIn())
                    self.checks[(action, kind)] = box
            y += pitch
        self.track(uikit.HLine(self.parent, 0, y, width, T.BRONZE_LINE_DK, .7), wheel=False)
        # 3) the channel bar lock and the hint
        y += 14 if big else 10
        hit = self.track(uikit.HitArea(self.parent, 0, y, 10, line_h))
        self.pin = self.track(check(self.parent, k, 0, 0, Tr('Lišta kanálů připnutá', 'Channel bar pinned'),
                                    event=self.TogglePin))
        self.pin.SetPosition(0, y + (line_h - self.pin.h) // 2)
        hit.SetSize(self.pin.Width() + 8, line_h)
        lock = Tr('zůstane na obrazovce u minimapy, i po přihlášení', 'stays on screen at the minimap, also after login')
        self._Tip(hit, Tr('Lišta kanálů připnutá', 'Channel bar pinned'), lock)
        self.pin.SetHoverEvent(lambda hit=hit: hit.OnMouseOverIn())
        self.track(uikit.Text(self.parent, lock, self.pin.Width() + 14, y + line_h // 2, k.font('S'), T.MUTED),
                   wheel=False)
        y += line_h + 2
        self.track(uikit.Text(self.parent, Tr('Totéž nabízí pravý klik na tlačítko ve hře i v náhledu.',
                                              'A right click on a button in game or in the preview offers the same.'),
                              0, y, k.font('S'), T.MUTED, valign='top'), wheel=False)
        y += k.cell('S') + 4
        self.Sync()
        return y

    def Sync(self):
        settings = self.settings
        for name, (toggle, line, note) in self.globals.items():
            toggle.SetOn(getattr(settings, name))
            if name == 'pulse':
                (toggle.Enable if settings.enabled else toggle.Disable)()
                note.SetText(PULSE_OFF)
                note.Hide() if settings.enabled else note.Show()
        for (action, kind), toggle in self.checks.items():
            toggle.SetOn(rows_model.FunctionOn(settings, action, kind) if (settings.enabled if kind == 'badge'
                                                                           else settings.state) else False)
            enabled = settings.enabled if kind == 'badge' else settings.state
            (toggle.Enable if enabled else toggle.Disable)()
        if self.pin is not None:
            self.pin.SetOn(model.ChannelBarPinned())

    def _Save(self, settings):
        if not badges.Save(settings):
            self.settings = badges.Load()
            self.page.StoreError()
        else:
            self.settings = settings
            self.page.BadgesChanged()
        self.Sync()

    def ToggleGlobal(self, name):
        if name == 'pulse' and not self.settings.enabled:
            return
        settings = badges.Load()
        setattr(settings, name, not getattr(settings, name))
        self._Save(settings)

    def ToggleFunction(self, action, kind):
        settings = badges.Load()
        if not (settings.enabled if kind == 'badge' else settings.state):
            return
        rows_model.SetFunction(settings, action, kind, not rows_model.FunctionOn(settings, action, kind))
        self._Save(settings)

    def TogglePin(self):
        pinned = not model.ChannelBarPinned()
        if not model.SetChannelBarPinned(pinned):
            self.page.StoreError()
        else:
            self.page.ChannelBarChanged()
        self.Sync()

    def Detach(self):
        self.globals, self.checks, self.pin = {}, {}, None
        self.page = None
