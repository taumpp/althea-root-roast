"""Settings -> Panely tlačítek: the "Odznaky a stav" block and the per-button switches.

Owner decision 2026-10-04 (wave 1): three global switches shared by every
panel - badges (dot / number), states and countdowns, pulsing of the ruby
badge - and, per function, "Odznak" and "Stav/odpočet" from the right-click
menu of a button (in game and in the settings preview / grid). Everything is
stored in the ``badges`` section of ``UserData/button-panels.json``
(``buttonpanelbadges.Settings``); a refused write shows the shared store error.

Owner review 2026-10-04 (in game): every switch has a short description; the
pulse switch is visibly grey with a reason while badges are off; the popup
lists every function that has a badge or a state (icon, name, what it shows)
with its own "Odznak" / "Stav" checkboxes - the same switches as the right
click on a button.
"""
import ui
import fontconfig
from settingslocale import Text as T

import buttonpanelbadges as badges

IMG = 'd:/ymir work/ui/game/crimson_ember/gameoption/'
INK = (.88, .85, .78)
GOLD = (.84, .71, .47)
DIM = (.68, .64, .58)
MUTED = (.45, .41, .38)
ROW = 34
CHECK_WIDTH = 15

# (setting, label, description, description while the badges are off or None)
ROWS = (
    ('enabled', T('Odznaky (tečka / číslo)', 'Badges (dot / number)'),
     T('Rubínový = čeká akce, zlatý = běží nebo je nové.', 'Ruby = an action waits, gold = live or new.'), None),
    ('state', T('Stav a odpočty', 'States and countdowns'),
     T('Zlatý rám, záře při běhu, ztmavení, výseč s časem.', 'Gold rim, glow while running, dimming, countdown.'),
     None),
    ('pulse', T('Pulzování', 'Pulsing'),
     T('Rubínový odznak jemně dýchá, aby byl vidět.', 'The ruby badge gently breathes so it is noticed.'),
     T('Jen se zapnutými odznaky.', 'Only while badges are on.')),
)
TITLE = T('Odznaky a stav', 'Badges and state')


def _check_visuals(button, checked):
    name = 'selected' if checked else 'unselected'
    button.SetUpVisual(IMG + 'checkbox_' + name + '.tga')
    button.SetOverVisual(IMG + 'checkbox_' + ('selected' if checked else 'hover') + '.tga')
    button.SetDownVisual(IMG + 'checkbox_selected.tga')
    if hasattr(button, 'SetDisableVisual'):
        button.SetDisableVisual(IMG + 'checkbox_' + name + '.tga')


CheckVisuals = _check_visuals   # shared checkbox look (Settings -> Panely tlačítek)


def _SetEnabled(button, enabled):
    """A disabled checkbox is drawn at 40 % so it reads as grey, not just dead."""
    (button.Enable if enabled else button.Disable)()
    if hasattr(button, 'SetAlpha'):
        button.SetAlpha(1.0 if enabled else 0.4)


class BadgeSettingsBlock(object):
    """A compact block of three checkboxes; ``Build(x, y)`` returns its height.

    ``owner`` is the settings view (``_keep``/``text`` helpers); ``on_change``
    runs after a successful save so the panels refresh at once; ``on_error``
    receives the player-facing text of a refused save.
    """

    def __init__(self, owner, on_change=None, on_error=None, path=None):
        self.owner = owner
        self.on_change = on_change
        self.on_error = on_error
        self.path = path
        self.settings = badges.Load(path)
        self.buttons = {}

    def Build(self, x, y, title=True):
        v = self.owner
        top = 15 if title else 0
        if title:
            v.text(TITLE, x, y, small=True, bold=True, width=200, color=GOLD)
        self.labels = {}
        for index, (name, label, description, unused) in enumerate(ROWS):
            row = y + top + index * ROW
            button = v._keep(ui.Button(), x, row)
            button.SetEvent(lambda selected=name: self.Toggle(selected))
            self.buttons[name] = button
            self.labels[name] = (v.text(label, x + CHECK_WIDTH + 6, row - 1, small=True, bold=True, width=300,
                                        color=INK),
                                 v.text(description, x + CHECK_WIDTH + 6, row + 14, small=True, width=360,
                                        color=DIM))
        self.Sync()
        return top + len(ROWS) * ROW

    def Sync(self):
        for name, button in self.buttons.items():
            _check_visuals(button, getattr(self.settings, name))
            if name == 'pulse':
                _SetEnabled(button, self.settings.enabled)
                self._Describe(name, self.settings.enabled)

    def _Describe(self, name, enabled):
        """Grey label with the reason while the switch has no effect."""
        lines = getattr(self, 'labels', {}).get(name)
        if not lines or lines[0] is None:
            return
        row = dict((key, (text, off)) for key, unused, text, off in ROWS)[name]
        title, description = lines
        title.SetFontColor(*(INK if enabled else MUTED))
        if description is not None:
            description.SetFontColor(*(DIM if enabled else MUTED))
            description.SetText(row[0] if enabled or not row[1] else row[1])

    def Reload(self):
        self.settings = badges.Load(self.path)
        self.Sync()

    def Toggle(self, name):
        if name not in [row[0] for row in ROWS]:
            return False
        setattr(self.settings, name, not getattr(self.settings, name))
        return self._Save()

    def RestoreDefaults(self):
        extra = self.settings.extra
        self.settings = badges.Settings(extra)
        return self._Save()

    def _Save(self):
        if not badges.Save(self.settings, self.path):
            import buttonpanelsettings
            self.settings = badges.Load(self.path)
            if self.on_error:
                self.on_error(buttonpanelsettings.StoreErrorText())
            self.Sync()
            return False
        self.Sync()
        if self.on_change:
            self.on_change()
        return True


# Per-button switches ---------------------------------------------------------------
def ContextEntries(action_id, has_badge, has_state, on_change=None, path=None):
    """Right-click menu entries ``(label, callback)`` for one function.

    ``has_badge`` / ``has_state``: whether this function can show them at all
    (``buttonpanelstatus.Capabilities``); functions without either get none.
    """
    settings = badges.Load(path)
    entries = []
    if has_badge:
        on = action_id not in settings.off
        entries.append((T('Odznak: zapnutý', 'Badge: on') if on else T('Odznak: vypnutý', 'Badge: off'),
                        lambda: _SetBadge(action_id, not on, on_change, path)))
    if has_state:
        on = action_id not in settings.state_off
        entries.append((T('Stav/odpočet: zapnutý', 'State/countdown: on') if on
                        else T('Stav/odpočet: vypnutý', 'State/countdown: off'),
                        lambda: _SetState(action_id, not on, on_change, path)))
    return entries


def _SetBadge(action_id, on, on_change, path):
    settings = badges.Load(path)
    settings.SetBadge(action_id, on)
    return _Store(settings, on_change, path)


def _SetState(action_id, on, on_change, path):
    settings = badges.Load(path)
    settings.SetState(action_id, on)
    return _Store(settings, on_change, path)


def _Store(settings, on_change, path):
    if not badges.Save(settings, path):
        import buttonpanelsettings
        buttonpanelsettings.ReportStoreError()
        return False
    if on_change:
        on_change()
    return True


def BadgeOff(action_id, settings):
    """The settings grid marks functions whose badge the player turned off."""
    return settings is not None and action_id in settings.off


# Functions with a badge or a state (owner 2026-10-04: "which functions have it?") ----
CHANNEL_PREFIX = 'channel.'
CHANNEL_IDS = tuple('channel.%d' % index for index in range(1, 10))
# (action id, name, what it shows). ``channel.`` stands for the nine channel buttons.
FUNCTIONS = (
    ('information.event_calendar', T('Kalendář událostí', 'Event calendar'),
     T('událost běží | začíná / končí za', 'event live · starts / ends in')),
    ('information.dungeon', T('Dungeony', 'Dungeons'), T('sledovaný připraven | odpočet', 'tracked ready · cooldown')),
    ('information.countdowns', T('Odpočty', 'Countdowns'),
     T('něco připraveno | nejbližší odpočet', 'something ready · next countdown')),
    ('system.biolog', T('Biolog', 'Biologist'), T('výzkumy k odevzdání | odpočet', 'research to hand in · countdown')),
    ('system.mission_books', T('Knihy misí', 'Mission books'), T('čeká truhla', 'a chest waits')),
    ('character.quests', T('Úkoly', 'Quests'), T('nepřečtené dopisy', 'unread letters')),
    ('character.skills', T('Schopnosti', 'Skills'), T('volné body', 'free points')),
    ('information.skill_tree', T('Strom schopností', 'Skill tree'),
     T('lze vylepšit | aktivace s odpočtem', 'upgrade ready · activation countdown')),
    (CHANNEL_PREFIX, T('Kanály 1-9', 'Channels 1-9'), T('aktuální | CH6/7 jen s VIP', 'current · CH6/7 VIP only')),
    ('system.channel_switch', T('Změna kanálu', 'Channel switch'), T('popisek CH n', 'CH n label')),
    ('system.switchbot', T('Switchbot', 'Switchbot'), T('běží (záře) | bonus nalezen', 'running (glow) · bonus found')),
    ('system.pet', T('Mazlík', 'Pet'), T('vyvolán | nakrmit / evoluce', 'summoned · feed / evolve')),
    ('system.quick_buffs', T('Rychlé buffy', 'Quick buffs'), T('odpočet | vypršel | auto (VIP)', 'countdown · expired · auto (VIP)')),
    ('community.guild', T('Cech', 'Guild'), T('čekající schválení', 'pending approvals')),
    ('system.pvp_matchmaking', T('Hodnocená aréna', 'Rated arena'), T('zápas nalezen | fronta | trest', 'match found · queue · penalty')),
)


def ShownFunctions():
    """``FUNCTIONS`` without a function the server reports off (the rated arena
    while it is paused: no settings row for a launcher that is not offered)."""
    try:
        import minimappanel
    except ImportError:
        return FUNCTIONS
    return tuple(row for row in FUNCTIONS if minimappanel.ServerOpen(row[0]))


def _Ids(action_id):
    return CHANNEL_IDS if action_id == CHANNEL_PREFIX else (action_id,)


def Capabilities(action_id):
    """(badge, state) the function supports; False, False when unknown."""
    try:
        import buttonpanelstatus
        return buttonpanelstatus.Capabilities(CHANNEL_IDS[0] if action_id == CHANNEL_PREFIX else action_id)
    except Exception:
        return False, False


def IsSupported(action_id):
    """The settings grid marks functions whose right-click menu offers badge/state."""
    return any(Capabilities(action_id))


def FunctionOn(settings, action_id, kind):
    check = settings.BadgeOn if kind == 'badge' else settings.StateOn
    return all(check(one) for one in _Ids(action_id))


def SetFunction(settings, action_id, kind, on):
    for one in _Ids(action_id):
        (settings.SetBadge if kind == 'badge' else settings.SetState)(one, on)


# Popup of the global switches and the function list (Settings -> Panely tlačítek, "Odznaky…")
POPUP_WIDTH = 460
POPUP_PAD = 14
POPUP_TOP = 36
LIST_ROW = 22
ICON_SCALE = 0.68   # 28 px launcher art -> 19 px
COLUMNS = dict(icon=POPUP_PAD, name=POPUP_PAD + 26, shows=POPUP_PAD + 140, badge=POPUP_WIDTH - 86, state=POPUP_WIDTH - 40)


class BadgeSettingsPopup(ui.BoardWithTitleBar):
    """A small Crimson board with the ``BadgeSettingsBlock`` and the list of the
    functions with a badge or a state: the tab row of the settings page holds only
    one "Odznaky…" button, so the 352x456 page does not grow (owner review
    2026-10-04: no scrolling on this page)."""

    def __init__(self, on_change=None):
        ui.BoardWithTitleBar.__init__(self)
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetTitleName(TITLE)
        self.SetCloseEvent(self.Close)
        self.widgets = []
        self.status = None
        self.on_change = on_change
        self.checks = {}
        self.block = BadgeSettingsBlock(self, on_change=self._Changed, on_error=self.ShowError)
        y = POPUP_TOP + self.block.Build(POPUP_PAD, POPUP_TOP, title=False)
        y = self._BuildList(y + 2)
        self.status = self.text('', POPUP_PAD, y + 2, small=True, width=POPUP_WIDTH - 2 * POPUP_PAD, color=GOLD)
        hints = (T('Totéž nabídne pravý klik na tlačítko (ve hře i v Nastavení).',
                   'A right click on a button offers the same (in game and in Settings).'),
                 T('Malá tečka v rohu ikony v mřížce = funkce má odznak nebo stav.',
                   'A small dot in the corner of a grid icon = it has a badge or a state.'))
        for index, hint in enumerate(hints):
            self.text(hint, POPUP_PAD, y + 18 + index * 15, small=True, width=POPUP_WIDTH - 2 * POPUP_PAD, color=DIM)
        self.SetSize(POPUP_WIDTH, y + 62)
        self.SyncList()

    def _BuildList(self, top):
        bar = ui.Bar()
        bar.SetParent(self)
        bar.SetPosition(POPUP_PAD, top)
        bar.SetSize(POPUP_WIDTH - 2 * POPUP_PAD, 1)
        bar.SetColor(0xFF403229 - 0x100000000)   # signed ARGB, as wndMgr expects
        bar.AddFlag('not_pick')
        bar.Show()
        self.widgets.append(bar)
        header = top + 6
        self.text(T('Funkce', 'Function'), COLUMNS['name'], header, small=True, bold=True, color=GOLD)
        self.text(T('Co ukazuje', 'Shows'), COLUMNS['shows'], header, small=True, bold=True, color=GOLD)
        self.text(T('Odznak', 'Badge'), COLUMNS['badge'] - 10, header, small=True, bold=True, color=GOLD)
        self.text(T('Stav', 'State'), COLUMNS['state'] - 4, header, small=True, bold=True, color=GOLD)
        y = header + 18
        import minimappanelicons
        for action_id, name, shows in ShownFunctions():
            has_badge, has_state = Capabilities(action_id)
            icon_id = CHANNEL_IDS[0] if action_id == CHANNEL_PREFIX else action_id
            icon = ui.ExpandedImageBox()
            icon.LoadImage(minimappanelicons.Visual(icon_id))
            icon.SetScale(ICON_SCALE, ICON_SCALE)
            icon.AddFlag('not_pick')
            self._keep(icon, COLUMNS['icon'], y + 1)
            mark = minimappanelicons.Mark(icon_id)
            if mark:
                line = self.text('CH' if action_id == CHANNEL_PREFIX else mark, COLUMNS['icon'] + 10, y + 4,
                                 small=True, color=INK)
                if hasattr(line, 'SetHorizontalAlignCenter'):
                    line.SetHorizontalAlignCenter()
            self.text(name, COLUMNS['name'], y + 3, small=True, width=COLUMNS['shows'] - COLUMNS['name'] - 4, color=INK)
            self.text(shows, COLUMNS['shows'], y + 3, small=True, width=COLUMNS['badge'] - COLUMNS['shows'] - 20,
                      color=DIM)
            for kind, supported in (('badge', has_badge), ('state', has_state)):
                if not supported:
                    continue
                button = self._keep(ui.Button(), COLUMNS[kind], y + 4)
                button.SetEvent(lambda selected=action_id, which=kind: self.ToggleFunction(selected, which))
                self.checks[(action_id, kind)] = button
            y += LIST_ROW
        return y

    def SyncList(self):
        settings = self.block.settings
        for (action_id, kind), button in self.checks.items():
            _check_visuals(button, FunctionOn(settings, action_id, kind))
            _SetEnabled(button, settings.enabled if kind == 'badge' else settings.state)

    def ToggleFunction(self, action_id, kind):
        settings = badges.Load(self.block.path)
        SetFunction(settings, action_id, kind, not FunctionOn(settings, action_id, kind))
        if not badges.Save(settings, self.block.path):
            import buttonpanelsettings
            self.ShowError(buttonpanelsettings.StoreErrorText())
        self.block.Reload()
        self.SyncList()
        if self.on_change:
            self.on_change()

    def _Changed(self):
        self.SyncList()
        if self.on_change:
            self.on_change()

    # Helpers the block expects from its owner (same signatures as the settings view).
    def _keep(self, widget, x, y):
        widget.SetParent(self)
        widget.SetPosition(int(x), int(y))
        widget.Show()
        self.widgets.append(widget)
        return widget

    def text(self, label, x, y, small=False, bold=False, width=None, color=INK, **unused):
        line = self._keep(ui.TextLine(), x, y)
        role = (fontconfig.ROLE_SECTION if bold and not small else fontconfig.ROLE_DENSE if small
                else fontconfig.ROLE_BODY)
        font = fontconfig.FontForRole(role)
        if bold and small and not font.endswith('b'):
            font += 'b'
        line.SetFontName(font)
        line.SetFontColor(*color)
        line.AddFlag('not_pick')
        if width and hasattr(line, 'SetLimitWidth'):
            line.SetLimitWidth(int(width))
        line.SetText(label)
        return line

    def ShowError(self, text):
        if self.status is not None:
            self.status.SetText(text)

    def Open(self, position):
        self.block.Reload()
        self.SyncList()
        if self.status is not None:
            self.status.SetText('')
        self.SetPosition(int(position[0]), int(position[1]))
        self.Show()
        self.SetTop()

    def Close(self):
        self.Hide()
        return True

    def OnPressEscapeKey(self):
        return self.Close()

    def Destroy(self):
        self.Hide()
        self.block = None
        self.widgets = []
        self.checks = {}
        self.status = None
