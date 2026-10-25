# -*- coding: utf-8 -*-
"""ESC menu V1.1 in the Althea UI kit (2026-10-05; design "ESC menu V1.1", variant A, kept by
the team vote; docs/SETTINGS_KIT_LOOK.md).

The window and the actions stay uisystem.SystemDialog (Interface.dlgSystem: Esc, the taskbar, warp capture and
restore, OpenGameOptionDialog, the exit preparation). This module only draws the menu INTO that window and calls
back the dialog's own handlers, so every item keeps today's behaviour and condition:

  Služby   Item Shop (app.ENABLE_ITEMSHOP, otherwise greyed) · Wiki (app.ENABLE_WIKI, otherwise greyed) · Nápověda
  Hra      Nastavení hry · Kanál: the channels as kit segment cells, five to a line
  Relace   Změnit postavu · Odhlásit se · Odblokovat postavu (/unstuck)
  bottom   "Zpět do hry" (left; Esc in its tooltip) and "Ukončit hru" (right), one width, centred icon + label

* Look: kit window frame, the kit's lower dialog title bar with a baked "MENU", the kit's one button family (owner
  2026-10-06): secondary buttons of the content height with an icon on the left, the bottom row (Zpět do hry /
  Ukončit hru) in the footer height with Ukončit hru as the one primary action, Spectral only
  (uikit.FontSet: Tahoma only as the automatic fallback of an old EXE). Icons and the title texture are this menu's
  own (tools/build_esc_menu_v5_assets.py -> althea_kit_esc/, uiescmenuassets); the kit itself is unchanged.
* Channels: the channel bar's logic (uichannelbar.ChannelList / Layout / its online probe): every channel the
  client knows from serverInfo (the server list of UserData/channel.inf), the current one selected, a VIP channel
  only with VIP (it is added when VIP starts), an offline channel dimmed; in the Shared City, on CH99 and in an
  instance the whole row is dimmed. 2026-10-06 (round 3): today's segment look "CH1 | CH2 | ...", always
  "CH<n>"; every cell is 1/5 of the row wide and left-aligned (one channel is no giant button), at most five in a
  line - six to nine channels make a second line of the same cells, 4 px under the first, one block. The states
  are queried live like the channel bar (on opening and every PROBE_EVERY s while the menu is open); a channel that
  comes online or is added lights up with a short soft gold rim and its label fades in, one that goes down is
  dimmed. Every cell's state and the reason of a blocked row are its tooltip ("Kanál 7 | jen s VIP", "aktuální",
  "offline"). A click switches through the bar's path (minimappanel.Invoke('channel.N') -> the keybinding
  callback -> uisystem.RequestChannelChange).
* Section headings are swappable: SECTION_STYLE picks one of SECTION_STYLES (the look of the separation is still
  being tuned in the design).
* Settings -> "Starý vzhled" (settingslook 'legacy') switches this menu back to the original crimson one as well
  (uisystem decides on every open; UseKitLook()).
"""
import app
import ui
import wndMgr

import uikit
import uikitlayout as L
import uikittokens as T
import uiescmenuassets as A
from settingslocale import Text as Tr

# Design gen/mock_esc11.py: window width, side padding, gap after a button, gap under the title bar, bottom padding.
GEOMETRY = {'1080': dict(width=340, pad=18, gap=8, top=14, bottom=18),
            '768': dict(width=280, pad=14, gap=6, top=14, bottom=12)}
# Item Shop icon (2026-10-06: the stack of coins "nelíbí", "prostě napsat IS"): 'shop_is' = IS monogram in a
# ring (default), 'shop_coin' = a coin with a gem, 'shop_gem' = a cut gem - all drawn in the menu's line style
# (tools/build_esc_menu_v5_assets.py draw_source).
SHOP_ICON = 'shop_is'
LINE_CELLS = 5          # channel cells in one line, each 1/5 of the row; a sixth channel starts a second line
LINE_GAP = 4            # px between the two lines of the channel block (2026-10-06)
FLASH = 0.8             # s of the soft gold rim + label fade-in of a channel that came online / was added
TIP_DELAY = 0.3         # s the mouse rests on a cell / button before its tooltip shows
REFRESH = 0.5           # channel state refresh while the menu is shown (as the channel bar)
PROBE_EVERY = 10.0      # s between the online queries (the channel bar's ServerStateChecker) while the menu is open
ICON_GAP = 10           # icon <-> label (design)
ICON_LEFT = 12          # icon from the left edge of a button (design)
LABEL_FONT = 'Mb'       # Spectral semibold for every menu button: the regular cut looked thin on the dark plates
HEADING_FONT = 'M'      # headings of the 'divider' style: the row size (the note size S was too small), muted
CHANNEL_LABEL = False   # no "Kanál" heading: the CH cells say it (team 2026-10-06)


def UseKitLook():
    """The kit menu unless Settings -> "Starý vzhled" chose the original look (settingslook 'legacy')."""
    try:
        import settingslook
        return settingslook.Get('look') != 'legacy'
    except Exception:
        return True


def _Locale(module_name, key, czech, english):
    try:
        value = getattr(__import__(module_name), key, None)
    except ImportError:
        value = None
    return value if isinstance(value, str) and value else Tr(czech, english)


def Labels():
    """The item labels of today's menu (systemdialog_crimson_ember.py), same locale keys and fallbacks."""
    return dict(
        shop=_Locale('uiScriptLocale', 'SYSTEM_MALL', 'Item Shop', 'Item Shop'),
        wiki=_Locale('localeInfo', 'WIKI_TITLENAME', 'Wiki', 'Wiki'),
        help=_Locale('uiScriptLocale', 'SYSTEM_HELP', 'Nápověda', 'Help'),
        options=_Locale('uiScriptLocale', 'GAMEOPTION_TITLE', 'Nastavení hry', 'Game options'),
        change=_Locale('uiScriptLocale', 'SYSTEM_CHANGE', 'Změnit postavu', 'Change character'),
        logout=_Locale('uiScriptLocale', 'SYSTEM_LOGOUT', 'Odhlásit se', 'Log out'),
        unstuck=_Locale('uiScriptLocale', 'SYSTEM_DEBUG', 'Odblokovat postavu', 'Unstuck character'),
        exit=_Locale('uiScriptLocale', 'SYSTEM_EXIT', 'Ukončit hru', 'Exit game'),
        title=_Locale('uiScriptLocale', 'SYSTEM_TITLE', 'Menu', 'Menu'),
        back=Tr('Zpět do hry', 'Back to game'),
        services=Tr('Služby', 'Services'), game=Tr('Hra', 'Game'), session=Tr('Relace', 'Session'),
        channel=Tr('Kanál', 'Channel'))


# --------------------------------------------------------------------------- channels (the channel bar's logic)
def _Bar():
    import uichannelbar
    return uichannelbar


def ChannelFacts(interface):
    """(current, map_index, vip) as the channel bar reads them (uichannelbar._Facts); None without channel moving."""
    try:
        facts = _Bar()._Facts(interface)
    except Exception:
        return None
    if not facts:
        return None
    current, map_index, unused_count, vip = facts
    return current, map_index, vip


def BlockedNote(current, map_index):
    """The one sentence of a place without channel change - the same order as uichannelbar.Layout (hub, CH99,
    instance); '' elsewhere."""
    import buttonpanelstatus as status
    if status.IsHub(current, map_index):
        return _Locale('localeInfo', 'GLOBAL_HUB_CHANNEL_SWITCH_BLOCKED', 'Ve Společném městě nelze měnit kanál.',
                       'Channel switching is unavailable in the Shared City.')
    if current == status.MAX_CHANNEL:
        return Tr('Z CH99 kanál změnit nejde.', 'No channel change from CH99.')
    if map_index >= status.INSTANCE_MAP_INDEX:
        return Tr('Tady kanál změnit nejde.', 'No channel change in an instance.')
    return ''


def OfflineNote(numbers):
    if not numbers:
        return ''
    names = ['CH%d' % number for number in numbers]
    if len(names) == 1:
        return Tr('%s je offline.', '%s is offline.') % names[0]
    listed = ', '.join(names[:-1]) + Tr(' a ', ' and ') + names[-1]
    return Tr('%s jsou offline.', '%s are offline.') % listed


def ChannelView(facts, channels, online=None):
    """``(cells, note)`` of the ESC channel row: uichannelbar.Layout cells (VIP hidden without VIP, offline and
    blocked cells disabled, the current one marked) and the sentence under the row."""
    if facts is None:
        return [], ''
    current, map_index, vip = facts
    cells, unused_tag = _Bar().Layout(current, map_index, list(channels), vip, online)
    note = BlockedNote(current, map_index)
    if not note:
        note = OfflineNote([cell.channel for cell in cells if not cell.enabled])
    return cells, note


def CellTip(cell, offline, blocked):
    """(title, body) of a channel cell's tooltip: "Kanál 7 | jen s VIP | aktuální" / "| offline"; the reason of a
    blocked row (hub, CH99, instance) as the body."""
    parts = [Tr('Kanál %d', 'Channel %d') % cell.channel]
    try:
        import buttonpanelstatus as status
        vip = cell.channel in status.VIP_CHANNELS
    except Exception:
        vip = False
    if vip:
        parts.append(Tr('jen s VIP', 'VIP only'))
    if cell.current:
        parts.append(Tr('aktuální', 'current'))
    if offline:
        parts.append(Tr('offline', 'offline'))
    return u' | '.join(parts), blocked or ''


def SwitchChannel(channel, interface):
    """The channel bar's switch (uichannelbar.ChannelBar.Switch): True when the request was dispatched."""
    try:
        import minimappanel
        return bool(minimappanel.Invoke('channel.%d' % int(channel), interface))
    except Exception:
        import dbg
        import traceback
        dbg.TraceError('esc menu channel: %s' % traceback.format_exc())
        return False


# --------------------------------------------------------------------------- section headings (swappable)
class DividerSection(object):
    """Design V1.1: a kit divider (line with a centre diamond) between sections, none above the first; the heading
    is small muted text."""
    SPACE = 14
    CAPS = False            # the settings sidebar's group look: upper case semibold (kit.group_font / group_text)
    COLOR = 'MUTED'         # uikittokens name, read when the section is built (the R1 skin puts its colours there)
    LABEL = True            # False: dividers only, no heading text

    def __init__(self, parent, kit, x, w, text, first):
        self.kit, self.x = kit, x
        self.divider = None if first else uikit.Divider(parent, kit, x, 0, w)
        self.label = None
        self.font = kit.group_font() if self.CAPS else kit.font(HEADING_FONT)
        if self.LABEL:
            self.label = uikit.Text(parent, kit.group_text(text) if self.CAPS else text, x, 0, self.font,
                                    getattr(T, self.COLOR), valign='top')

    def Place(self, y):
        if self.divider is not None:
            self.divider.SetPosition(self.x, y)
            y += self.SPACE
        if self.label is None:
            return y
        self.label.SetPosition(self.x, y)
        return y + uikit.FontCell(self.font) + 8

    def Widgets(self):
        return [w for w in (self.divider, self.label) if w is not None]


class CapsSection(DividerSection):
    """Variant (2026-10-06, Tetsu: "ty nadpisy"): the heading as the settings sidebar groups - upper case
    semibold in muted gold - under the same divider."""
    CAPS = True
    COLOR = 'GOLD'


class PlainSection(DividerSection):
    """Variant (2026-10-06): dividers only, no heading text (the buttons say enough)."""
    LABEL = False


class RuleSection(object):
    """The settings v5 section (uikit.Section: semibold heading and a fading rule after it), above every section."""

    def __init__(self, parent, kit, x, w, text, first):
        self.x, self.first = x, first
        self.section = uikit.Section(parent, kit, x, 0, w, text)

    def Place(self, y):
        if not self.first:
            y += 6
        self.section.SetPosition(self.x, y)
        return y + self.section.Height() + 8

    def Widgets(self):
        return [self.section]


SECTION_STYLES = {'divider': DividerSection, 'rule': RuleSection, 'caps': CapsSection, 'plain': PlainSection}
SECTION_STYLE = 'caps'       # team vote 2026-10-06: variant C


# --------------------------------------------------------------------------- widgets
def IconPath(name, size, state='normal'):
    """The menu's own icon; in the R1 skin its R1 ink version (tools/build_althea_r1_nastaveni.py, esc/icons/)."""
    if name not in A.ICONS or size not in A.ICON_SIZES:
        return None
    root = A.ROOT
    if uikit.R1():
        import uir1nastavenitokens
        root = uir1nastavenitokens.ESC_ROOT
    return root + 'icons/%d/%s_%s.png' % (size, name, state)


class MenuButton(uikit.Button):
    """Kit button with this menu's icon on the left (or an icon + label group centred). The icon is the family's
    one size (20 px) everywhere, the label the row font; a key hint ("Esc") goes to the tooltip (``tip``), never
    into the button (2026-10-06: "Esc" stuck to the right edge looked odd). Plate, states and label colours
    are uikit.Button's."""

    def __init__(self, parent, kit, x, y, w, text, icon, event=None, role='secondary', hint='', center=False,
                 size='content'):
        self.menu_icon_name, self.center, self.hint = icon, center, None
        self.menu_icon = None
        self.tip = (text + ' | ' + hint, '') if hint else None
        uikit.Button.__init__(self, parent, kit, x, y, w, text, role=role, event=event, align='left', size=size)
        # the kit button sets M; laid out again in Mb (the R1 skin: the R1 button font, Cinzel)
        font = kit.button_font() if uikit.R1() else kit.font(LABEL_FONT)
        uikit.SetFont(self.label, font, uikit.WordGap(text, font))
        size = self.icon_size   # the family's one icon size
        path = IconPath(icon, size)
        if path:
            self.menu_icon = ui.ImageBox()
            self.menu_icon.SetParent(self)
            self.menu_icon.AddFlag('not_pick')
            self.menu_icon.LoadImage(path)
            self.menu_icon.Show()
        self.paint()

    def _IconState(self):
        state = self.state()
        if state == 'normal' and self.role in uikit.RUBY_ROLES:
            return 'active'   # gold icon on the ruby plate (design)
        return {'disabled': 'disabled', 'hover': 'hover', 'pressed': 'active'}.get(state, 'normal')

    def _place(self):
        dy = 1 if self.pressed else 0
        size = self.icon_size
        label_w = uikit.TextWidth(self.label)
        hint_w = uikit.TextWidth(self.hint) + 6 if self.hint is not None else 0
        x = ICON_LEFT
        if self.menu_icon is not None:
            self.menu_icon.SetPosition(x, (self.h - size) // 2 + dy)
        x += size + ICON_GAP
        if self.center:
            # Footer pair (Zpět do hry / Ukončit hru): the icon at the edge like every menu button, the label centred
            # in the room right of it (centring icon + label as one group left the icon far from the edge).
            x = max(x, x + (self.w - ICON_LEFT - x - label_w - hint_w) // 2)
        self.label.SetPosition(x, self.h // 2 + dy - self.nudge)
        if self.hint is not None:
            if self.center:
                self.hint.SetPosition(x + label_w + 6, self.h // 2 + dy)
            else:
                self.hint.SetHorizontalAlignRight()
                self.hint.SetPosition(self.w - 12, self.h // 2 + dy)

    def paint(self):
        uikit.Button.paint(self)
        if self.menu_icon is not None:
            self.menu_icon.LoadImage(IconPath(self.menu_icon_name, self.icon_size, self._IconState()))
        if self.hint is not None:
            self.hint.SetPackedFontColor(T.DISABLED if not self.enabled else T.MUTED)


class MenuTitleBar(uikit.TitleBar):
    """The kit dialog title bar with this menu's baked title texture ("MENU", uiescmenuassets.TITLES); any other
    title falls back to the kit's own behaviour (its baked titles or engine text). FLOURISH = False drops the lines
    with diamonds next to the title (design V1.1: a plain lower bar)."""
    FLOURISH = False

    def _OwnTitle(self, width):
        own = A.TITLES.get('%s|%d' % ((self.title or '').upper(), self.bar))
        if not own or self.mode == 'text' or getattr(self, 'r1', False):
            return None     # the R1 skin: the R1 header with the title in Cinzel (no baked texture)
        path, w, h = own
        return (path, (w, h)) if L.titlebar(width, self.bar, (w, h), self.has_close, self.FLOURISH)['fits'] else None

    def SetTitle(self, title, width=None):
        self.title = title or ''
        width = int(width or self.GetWidth())
        own = self._OwnTitle(width)
        if own is None:
            return uikit.TitleBar.SetTitle(self, title, width)
        path, size = own
        layout = L.titlebar(width, self.bar, size, self.has_close, self.FLOURISH)  # no lines: centred on the bar
        self.SetSize(layout['width'], layout['height'])
        fresh = self._ApplyBar([op for op in layout['ops'] if self.FLOURISH or '/flourish_' not in op[1]])
        if self.title_image is None or fresh:
            # made after the bar images (the engine draws children in the order they were added; a SetParent to
            # the same parent does not move a window - CWindowManager::SetParent)
            if self.title_image is not None:
                self.title_image.Hide()
            self.title_image = ui.ImageBox()
            self.title_image.SetParent(self)
            self.title_image.AddFlag('not_pick')
        self.title_image.LoadImage(A.ROOT + path)
        tx, ty, unused_w, unused_h = layout['title']
        self.title_image.SetPosition(tx, ty)
        self.title_image.Show()
        if self.title_text is not None:
            self.title_text.Hide()
        if self.close:
            cx, cy, unused_cw, unused_ch = layout['close']
            self.close.SetPosition(cx, cy)
        self.layout = layout
        return layout


class ChannelRow(ui.Window):
    """The channels as kit segment cells (2026-10-06, round 3): "CH1".."CH9", every cell 1/5 of the row wide,
    left-aligned, at most LINE_CELLS in a line - a second line of the same cells LINE_GAP px under the first (one
    block). The selected cell = the current channel, disabled cells = no change possible. A channel that came online
    or was added flashes (Flash / Tick). ``tip`` of a cell = (title, body) of its tooltip (set by the menu)."""

    def __init__(self, parent, kit, width, event):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.kit, self.width, self.event = kit, int(width), event
        self.segments = []
        self.numbers = ()
        self.current = None
        self.lines = 1
        self.on_hover = None
        self.known = None          # {channel: offline} of the last Apply; None = first state after opening
        self.flashes = {}          # channel -> start time of its flash
        self.SetSize(self.width, kit.p('seg_h'))
        self.Show()

    def Height(self):
        return self.lines * self.kit.p('seg_h') + (self.lines - 1) * LINE_GAP

    def Edges(self):
        """x of the cell borders of a line: LINE_CELLS equal cells over the row (the last absorbs the rounding)."""
        return [int(round(index * self.width / float(LINE_CELLS))) for index in range(LINE_CELLS + 1)]

    @staticmethod
    def Grid(count):
        """(cells in the first line, lines) of ``count`` channels."""
        if count <= 0:
            return 0, 0
        return min(count, LINE_CELLS), (count + LINE_CELLS - 1) // LINE_CELLS

    def _Build(self, numbers):
        for segment in self.segments:
            segment.Hide()
        self.segments = []
        self.flashes = {}
        self.numbers = tuple(numbers)
        unused, self.lines = self.Grid(len(numbers))
        self.lines = max(1, self.lines)
        if not numbers:
            self.SetSize(self.width, self.Height())
            return
        font = self.kit.font('M')
        h = self.kit.p('seg_h')
        edges = self.Edges()
        for line in range(self.lines):
            chunk = numbers[line * LINE_CELLS:(line + 1) * LINE_CELLS]
            segment = uikit.Segment(self, self.kit, [(number, 'CH%d' % number) for number in chunk],
                                    event=self._Click, font=font)
            for index, cell in enumerate(segment.cells):
                cell.Place(edges[index], edges[index + 1] - edges[index], h)
                cell.SetHoverEvent(lambda cell=cell: self.on_hover and self.on_hover(cell))
            segment.width = edges[len(chunk)]
            segment.SetSize(segment.width, h)
            segment.SetPosition(0, line * (h + LINE_GAP))
            self.segments.append(segment)
        self.SetSize(self.width, self.Height())

    def Reset(self):
        """A new opening: the first state shows without flashes."""
        self.known = None
        self.flashes = {}
        for cell in self.Cells():
            self._PaintFlash(cell, None)

    def Apply(self, cells, offline=(), now=0.0):
        numbers = tuple(cell.channel for cell in cells)
        if numbers != self.numbers:
            self._Build(numbers)
        self.current = None
        offline = set(offline)
        for widget, cell in zip(self.Cells(), cells):
            # A blocked row (hub, CH99, instance) is dimmed as a whole: no selected cell (design V1.1).
            widget.selected = bool(cell.current and cell.enabled)
            widget.channel = cell.channel
            if cell.current:
                self.current = cell.channel
            if cell.enabled:
                widget.Enable()
            else:
                widget.Disable()
            if self.known is not None and cell.enabled and cell.channel not in offline and \
                    (cell.channel not in self.known or self.known[cell.channel]):
                self.flashes[cell.channel] = now       # came online / was added (VIP) while the menu is open
        self.known = dict((cell.channel, cell.channel in offline) for cell in cells)
        self.Tick(now)

    def Tick(self, now):
        for cell in self.Cells():
            start = self.flashes.get(getattr(cell, 'channel', None))
            if start is None:
                continue
            t = (now - start) / FLASH
            if t >= 1.0 or t < 0.0 or not cell.enabled:
                del self.flashes[cell.channel]
                self._PaintFlash(cell, None)
            else:
                self._PaintFlash(cell, t)

    def _PaintFlash(self, cell, t):
        """t in 0..1 of the flash: a soft gold rim inside the cell (clear of its rounded caps) fading out, the label
        fading in from the dimmed colour; None = no flash."""
        bars = getattr(cell, 'flash_bars', None)
        if t is None:
            if bars:
                for bar in bars:
                    bar.Hide()
            if getattr(cell, 'flashing', False):
                cell.flashing = False
                cell.paint()
            return
        if bars is None:
            w, h = cell.w, cell.GetHeight()
            cell.flash_bars = bars = [uikit.Rect(cell, 3, 3, w - 6, h - 6, T.GOLD, 0.0),
                                      uikit.Rect(cell, 3, 3, w - 6, 1, T.GOLD_HI, 0.0),
                                      uikit.Rect(cell, 3, h - 4, w - 6, 1, T.GOLD_HI, 0.0),
                                      uikit.Rect(cell, 3, 4, 1, h - 8, T.GOLD_HI, 0.0),
                                      uikit.Rect(cell, w - 4, 4, 1, h - 8, T.GOLD_HI, 0.0)]
        fade = (1.0 - t) * (1.0 - t)
        for index, bar in enumerate(bars):
            bar.SetColor(uikit.GenerateColor(T.GOLD if index == 0 else T.GOLD_HI, fade * (0.22 if index == 0 else 0.9)))
            bar.Show()
        cell.flashing = True
        target = T.GOLD_HI if cell.selected else (T.INK if cell.hovered else T.INK_DIM)
        cell.label.SetPackedFontColor(_Mix(T.DISABLED, target, min(1.0, t * 3.0)))

    def Cells(self):
        return [cell for segment in self.segments for cell in segment.cells]

    def _Click(self, channel):
        if channel != self.current and self.event:
            self.event(channel)


def _Mix(a, b, t):
    """Packed ARGB colour between a and b (t 0..1)."""
    out = 0
    for shift in (24, 16, 8, 0):
        ca, cb = (a >> shift) & 0xFF, (b >> shift) & 0xFF
        out |= int(round(ca + (cb - ca) * t)) << shift
    return out


# --------------------------------------------------------------------------- the menu
class EscMenu(ui.Window):
    """The menu inside ``owner`` (uisystem.SystemDialog). ``actions``: name -> callable for shop, wiki, help,
    options, change, logout, unstuck, exit, back and channel (called with the channel number). ``features``:
    shop / wiki / channels (app.ENABLE_ITEMSHOP / ENABLE_WIKI / ENABLE_MOVE_CHANNEL). ``interface``: callable
    returning the game interface (the channel facts and the switch path), may return None."""

    def __init__(self, owner, actions, features=None, interface=None, labels=None):
        ui.Window.__init__(self)
        self.owner = owner
        self.actions = dict(actions)
        self.features = dict(features or {})
        self.interface = interface or (lambda: None)
        self.kit = uikit.Kit(uikit.Profile(), uikit.FontSet())
        self.geo = GEOMETRY[self.kit.prof]
        self.labels = labels or Labels()
        self.next_refresh = self.next_probe = 0.0
        self.channel_key = None
        self.channel_list = None   # the server's channel list, read once per opening (UserData/channel.inf)
        self.note_text = ''         # why the channel cannot change here (the tooltip of the dimmed row)
        self.tip = None
        self.tip_pending = self.tip_owner = None
        self.SetParent(owner)
        self.AddFlag('not_pick')
        self.SetPosition(0, 0)
        self._Build()
        self.Show()

    def _Action(self, name):
        return lambda: self._Run(name)

    def _Run(self, name, *args):
        callback = self.actions.get(name)
        if callable(callback):
            callback(*args)

    def _Build(self):
        k, g, lab = self.kit, self.geo, self.labels
        W = g['width']
        x, iw = g['pad'], g['width'] - 2 * g['pad']
        self.width, self.x0, self.iw = W, x, iw
        style = SECTION_STYLES.get(SECTION_STYLE, DividerSection)
        # Frame first (drawn under everything), then the title bar, then the content.
        self.frame = uikit.Frame(self, k, 'window', 0, 0, W, 200, bg=True, vignette=True)
        self.titlebar = MenuTitleBar(self, k, 5, 5, W - 10, lab['title'], kind='dialog',
                                     on_close=self._Action('back'))
        self.sections = {}
        self.buttons = {}

        def button(name, icon, text, enabled=True):
            widget = MenuButton(self, k, x, 0, iw, text, icon, event=self._Action(name))
            if not enabled:
                widget.Disable()
            self.buttons[name] = widget
            return widget
        self.sections['services'] = style(self, k, x, iw, lab['services'], True)
        button('shop', SHOP_ICON, lab['shop'], self.features.get('shop', True))
        button('wiki', 'wiki', lab['wiki'], self.features.get('wiki', True))
        button('help', 'help', lab['help'])
        self.sections['game'] = style(self, k, x, iw, lab['game'], False)
        button('options', 'gear_c6', lab['options'])
        self.channels_enabled = bool(self.features.get('channels', True))
        self.channel_label = None
        if CHANNEL_LABEL:
            self.channel_label = uikit.Text(self, lab['channel'], x, 0, k.font(HEADING_FONT), T.MUTED, valign='top')
        self.channel_row = ChannelRow(self, k, iw, self._Channel)
        self.channel_row.on_hover = self._HoverTip
        if not self.channels_enabled:
            if self.channel_label is not None:
                self.channel_label.Hide()
            self.channel_row.Hide()
        self.sections['session'] = style(self, k, x, iw, lab['session'], False)
        button('change', 'change_char', lab['change'])
        button('logout', 'logout', lab['logout'])
        button('unstuck', 'unstuck', lab['unstuck'])
        self.rule = uikit.HLine(self, x, 0, iw, T.BRONZE_LINE_DK)
        # The bottom row: two buttons of ONE width, centred icon + label (2026-10-06); Esc in the tooltip.
        half = (iw - 10) // 2
        self.buttons['back'] = MenuButton(self, k, x, 0, half, lab['back'], 'back', event=self._Action('back'),
                                          hint='Esc', center=True, size='bar')
        self.buttons['exit'] = MenuButton(self, k, x + iw - half, 0, half, lab['exit'], 'exit',
                                          event=self._Action('exit'), role='primary', center=True, size='bar')
        self.buttons['back'].SetHoverEvent(lambda: self._HoverTip(self.buttons['back']))
        self.Layout()

    def Layout(self):
        """Places every row from the top; returns the window height (the frame and the owner follow it)."""
        k, g = self.kit, self.geo
        x, gap = self.x0, g['gap']
        y = 5 + self.titlebar.Height() + g['top']

        def row(name, y):
            widget = self.buttons[name]
            widget.SetPosition(x, y)
            return y + widget.h + gap
        y = self.sections['services'].Place(y)
        for name in ('shop', 'wiki', 'help'):
            y = row(name, y)
        y += 4
        y = self.sections['game'].Place(y)
        y = row('options', y)
        if self.channels_enabled:
            if self.channel_label is not None:
                self.channel_label.SetPosition(x, y + 2)
                y += k.cell(HEADING_FONT) + 8
            else:
                y += 4                          # the CH cells right under Nastavení hry, a little apart
            self.channel_row.SetPosition(x, y)
            y += self.channel_row.Height() + 8
        y += 2
        y = self.sections['session'].Place(y)
        for name in ('change', 'logout', 'unstuck'):
            y = row(name, y)
        y += 6
        self.rule.SetPosition(x, y)
        y += 12
        self.buttons['back'].SetPosition(x, y)
        self.buttons['exit'].SetPosition(x + self.iw - self.buttons['exit'].w, y)
        y += max(self.buttons['back'].h, self.buttons['exit'].h) + g['bottom']
        self.height = y
        self.SetSize(self.width, y)
        self.frame.SetSize(self.width, y)
        self.frame.Apply(L.frame('window', k.prof, self.width, y, bg=True, vignette=True))
        if self.owner is not None:
            self.owner.SetSize(self.width, y)
        return y

    # ------------------------------------------------------------------ channels
    def RefreshChannels(self, force=False):
        if not self.channels_enabled:
            return
        bar = _Bar()
        if force or self.channel_list is None:
            self.channel_list = bar.ChannelList()
        facts = ChannelFacts(self.interface())
        probe = getattr(bar, '_probe', None)
        cells, note = ChannelView(facts, [number for number, unused in self.channel_list],
                                  probe.states if probe is not None else None)
        key = (tuple(cell.Key() for cell in cells), note)
        if key == self.channel_key and not force:
            return
        self.channel_key = key
        lines = self.channel_row.lines
        offline = getattr(_Bar(), 'OFFLINE', 0)
        states = probe.states if probe is not None else {}
        down = [cell.channel for cell in cells if states.get(cell.channel) == offline]
        self.channel_row.Apply(cells, down, app.GetTime())
        self.note_text = BlockedNote(facts[0], facts[1]) if facts is not None else ''
        for widget, cell in zip(self.channel_row.Cells(), cells):
            widget.tip = CellTip(cell, cell.channel in down, self.note_text)
        if self.channel_row.lines != lines:
            self.Layout()

    def _Channel(self, channel):
        self._Run('channel', channel)

    # ------------------------------------------------------------------ tooltips (channel cells, Zpět do hry)
    def _HoverTip(self, widget):
        if getattr(widget, 'tip', None):
            self.tip_pending = (widget, app.GetTime() + TIP_DELAY)

    def HideTip(self):
        """Also called by the owner on closing: the tooltip is its own top window and OnUpdate stops with the menu."""
        self.tip_pending = self.tip_owner = None
        if self.tip is not None and self.tip.IsShow():
            self.tip.Hide()

    def _TipTick(self):
        try:
            mouse = tuple(wndMgr.GetMousePosition())
        except Exception:
            return

        def inside(widget):
            x, y = widget.GetGlobalPosition()
            return widget.IsShow() and x <= mouse[0] < x + widget.GetWidth() and y <= mouse[1] < y + widget.GetHeight()
        if self.tip_owner is not None and not inside(self.tip_owner):
            self.tip_owner = None                     # keeps a pending tooltip of the widget the mouse moved to
            if self.tip is not None:
                self.tip.Hide()
        pending = self.tip_pending
        if pending is None:
            return
        widget, due = pending
        if not inside(widget):
            self.tip_pending = None
            return
        if app.GetTime() < due:
            return
        self.tip_pending = None
        if self.tip is None:
            self.tip = uikit.Tooltip(self.kit)
        title, body = widget.tip
        x, y = widget.GetGlobalPosition()
        self.tip.ShowAt((x, y, widget.GetWidth(), widget.GetHeight()), title, body)
        self.tip_owner = widget

    def Open(self):
        """Before the owner shows: fresh online states (as the bar on opening) and the current channel row."""
        if self.channels_enabled:
            probe = getattr(_Bar(), '_probe', None)
            if probe is not None:
                probe.next = 0.0
        self.next_refresh = self.next_probe = 0.0
        self.channel_row.Reset()
        self.RefreshChannels(force=True)

    def OnUpdate(self):
        self._TipTick()
        if not self.channels_enabled:
            return
        now = app.GetTime()
        bar = _Bar()
        probe = getattr(bar, '_probe', None)
        if probe is not None:
            probe.Pump(now)
            # The bar's query at the menu's own pace while it is open (the bar asks every PROBE_INTERVAL); never
            # while the replies of the last request are still being pumped.
            if self.channel_list and now >= self.next_probe and now > probe.until:
                self.next_probe = now + PROBE_EVERY
                probe.Request(self.channel_list, now)
        if now >= self.next_refresh:
            self.next_refresh = now + REFRESH
            self.RefreshChannels()
        self.channel_row.Tick(now)

    def Destroy(self):
        """Hide and break the callback cycles (button -> lambda -> menu); the owner drops its reference."""
        self.HideTip()
        self.Hide()
        for widget in self.buttons.values():
            widget.callback = None
        if self.titlebar.close is not None:
            self.titlebar.close.callback = None
        self.channel_row.event = None
        self.frame.Destroy()
        self.buttons = {}
        self.sections = {}
        self.owner = None
        self.actions = {}
        self.interface = lambda: None
