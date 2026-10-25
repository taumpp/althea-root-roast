"""Channel bar: every channel in one row right at the "Změna kanálu" button.

Owner idea 2026-10-04: the channel switch opened the whole ESC menu just to
pick a channel. A click on "Změna kanálu" (minimap, rail, More board) opens
this small horizontal bar at the cursor; another click on it, the cross or
Esc closes it (owner round 4: it stays open after a switch).

* The channels are the ESC menu's / login screen's list: the server's
  channel dict in ``serverInfo.REGION_DICT`` chosen by ``UserData/channel.inf``
  (``uisystem.LoadChannelInfo``), at most 9, as the same 28 px medallions as
  the channel buttons of the panels. A VIP channel is shown only with VIP.
* Online state: like the login screen, the bar asks ``ServerStateChecker``
  for every listed channel when it opens (and every ``PROBE_INTERVAL`` while
  shown); an offline channel is dimmed, cannot be clicked and says so in its
  tooltip. Until a reply arrives a channel counts as available.
* The current channel has a small gold marker under it - no rim over the
  button. In the global hub or on CH99 the marker stands at a small "Hub" /
  "CH99" tag at the left end; from there (and from an instance) the server
  refuses every change (``uisystem.RequestChannelChange``), so the channels
  are dimmed with the reason in their tooltip.
* A click switches exactly like the ESC menu and the channel buttons
  (``minimappanel.Invoke('channel.N')`` -> ``/move_channel N``).

The lock (owner round 5: an icon, not the "Připnout" text) pins the bar:
closed lock = a small movable window that never closes (no cross, Esc
ignored), shows again after login and remembers its place in the
``channel_bar`` section of ``UserData/button-panels.json`` (default: section
absent); open lock = the closable popup. Tooltip "Připnout lištu" /
"Odepnout lištu".

Looks: the R1 look (``uichannelbarr1``: the stepper "‹ CH 3 ›" with the
small row of numbers, or the list with the load of every channel - Settings ->
Vzhled -> "Lišta kanálů") unless Settings -> "Starý vzhled" chose the original
windows; then (and when the R1 bar fails to build, traced) the bar of this
module. The load (``ServerStateChecker``: 2 = busy, 3 = full) is shown by the
R1 bar only.
"""
import app
import ui
import wndMgr
import fontconfig
from settingslocale import Text as T

import buttonpanelbadges as badges
import buttonpanelstatus as status
import uibuttonpaneldecor as decor

SECTION = 'channel_bar'
MAX_CHANNELS = 9
CELL = 32
ICON = 28
PAD = 6
MARKER_HEIGHT = 6
TAG_WIDTH = 40
PIN_WIDTH = 24   # the lock button (button_panel_badges/lock_*.png)
CLOSE = 22
REFRESH = 0.5
PROBE_INTERVAL = 30.0
PROBE_TIMEOUT = 5.0
OFFLINE = 0
BUSY = 2       # the server's state checker: 1 = normal, 2 = busy, 3 = full (CLIENT_DESC::UpdateChannelStatus)
FULL = 3
BACKGROUND = 0xf0171410 - 0x100000000
BORDER = 0xff5a4630 - 0x100000000
GOLD = (.95, .80, .45)
ART = decor.ART
CLOSE_ART = 'd:/ymir work/ui/game/crimson_ember/minimap/close_%s.png'


# Model -------------------------------------------------------------------------------
def ChannelList(region_dict=None, channel_info=None):
    """``[(number, entry)]`` of the server the player logged into - the same dict
    the ESC menu counts (``uisystem.GetChannelCount``) and the login screen lists."""
    try:
        if region_dict is None:
            import serverInfo
            region_dict = serverInfo.REGION_DICT
        if channel_info is None:
            import uisystem
            channel_info = uisystem.LoadChannelInfo()
        region_id, server_id = channel_info[0], channel_info[1]
        channels = region_dict[region_id][server_id]['channel']
    except Exception:
        return []
    return sorted((number, entry) for number, entry in channels.items()
                  if isinstance(number, int) and 1 <= number <= MAX_CHANNELS)[:MAX_CHANNELS]


class Cell(object):
    """One channel of the bar. ``load``: '' / 'busy' / 'full' (shown by the R1 bar); ``note``: the second tooltip
    line of a busy / full channel."""
    __slots__ = ('channel', 'current', 'enabled', 'tooltip', 'load', 'note', 'offline')

    def __init__(self, channel, current, enabled, tooltip, load='', note='', offline=False):
        self.channel, self.current, self.enabled, self.tooltip = channel, current, enabled, tooltip
        self.load, self.note, self.offline = load, note, offline

    def Key(self):
        return (self.channel, self.current, self.enabled, self.tooltip, self.load, self.offline)


def Layout(current, map_index, channels, vip, online=None):
    """``(cells, tag)`` of the bar.

    ``channels``: channel numbers of the server list; ``online``: number ->
    ``ServerStateChecker`` state (0 = offline; missing = not known yet).
    ``tag``: '' or the "Hub" / "CH99" label that carries the current marker.
    """
    online = online or {}
    hub = status.IsHub(current, map_index)
    if hub:
        tag, blocked = T('Hub', 'Hub'), T('Z hubu kanál změnit nejde.', 'No channel change from the hub.')
    elif current == status.MAX_CHANNEL:
        tag, blocked = 'CH99', T('Z CH99 kanál změnit nejde.', 'No channel change from CH99.')
    elif map_index >= status.INSTANCE_MAP_INDEX:
        tag, blocked = '', T('Tady kanál změnit nejde.', 'No channel change in an instance.')
    else:
        tag, blocked = '', ''
    cells = []
    for channel in channels:
        if channel in status.VIP_CHANNELS and not vip:
            continue   # owner 2026-10-04: no VIP, no VIP channel
        here = not hub and channel == current
        state = online.get(channel)
        load = {BUSY: 'busy', FULL: 'full'}.get(state, '')
        note = ''
        if state == OFFLINE:
            tooltip, enabled = T('CH%d je offline.', 'CH%d is offline.') % channel, False
        elif blocked:
            tooltip, enabled = blocked, False
        elif here:
            tooltip, enabled = T('CH%d - tady jsi.', 'CH%d - you are here.') % channel, True
        else:
            tooltip, enabled = T('Přepnout na CH%d', 'Switch to CH%d') % channel, True
            note = {'busy': T('Rušno - hodně hráčů', 'Busy - many players'), 'full': T('Plno', 'Full')}.get(load, '')
        cells.append(Cell(channel, here, enabled, tooltip, load, note, state == OFFLINE))
    if not tag and current > 0 and not any(cell.current for cell in cells) and current != 98:
        tag = 'CH%d' % current   # e.g. a channel the list does not have
    return cells, tag


def StepTarget(cells, step):
    """CH+ (``step`` 1) / CH- (-1) of the bar: the next channel of the bar in that direction, round the ends like the
    CH+ / CH- shortcuts (``uisystem.RequestAdjacentChannelChange``), skipping what the bar does not offer - a hidden
    VIP channel (not in ``cells``) and an offline one (dimmed). None where no change is possible (hub, CH99, an
    instance, a channel the list does not have, nothing else to go to)."""
    if step not in (-1, 1):
        return None
    order = [cell for cell in cells if cell.current or cell.enabled]
    here = [index for index, cell in enumerate(order) if cell.current]
    if not here or not order[here[0]].enabled:
        return None
    index = here[0]
    for unused in range(len(order) - 1):
        index = (index + step) % len(order)
        if order[index].enabled and not order[index].current:
            return order[index].channel
    return None


class BarSettings(object):
    """The ``channel_bar`` section: ``pinned`` and the pinned window's place."""

    def __init__(self, section=None):
        section = section if isinstance(section, dict) else {}
        self.pinned = section.get('pinned') is True
        self.x = _coordinate(section.get('x'))
        self.y = _coordinate(section.get('y'))

    def ToSection(self):
        if not self.pinned:
            return None   # default: the popup, nothing stored
        section = {'pinned': True}
        if self.x is not None and self.y is not None:
            section.update(x=self.x, y=self.y)
        return section


def _coordinate(value):
    return int(value) if isinstance(value, int) and not isinstance(value, bool) and -10000 < value < 10000 else None


def Load(path=None):
    try:
        import buttonpanelstore
        return BarSettings(buttonpanelstore.ReadSection(SECTION, path))
    except Exception:
        return BarSettings()


def Save(settings, path=None):
    try:
        import buttonpanelstore
        return buttonpanelstore.WriteSection(SECTION, settings.ToSection(), path)
    except Exception:
        return False


def _Facts(interface):
    try:
        return status._ChannelFacts(status.Context(interface))
    except Exception:
        return None


def StepChannelTarget(interface, step):
    """The channel CH+ (1) / CH- (-1) goes to from outside the bar (the ‹ › of the R1 minimap pennant): the bar's
    ``StepTarget`` with the live facts and the probe's states, None where no change is possible."""
    facts = _Facts(interface)
    if not facts:
        return None
    current, map_index, unused_count, vip = facts
    cells, unused_tag = Layout(current, map_index, [number for number, unused in ChannelList()], vip, _probe.states)
    return StepTarget(cells, step)


def StepChannel(interface, step):
    """CH+ / CH- from outside the bar, sent like the bar's arrows; False where no change is possible."""
    target = StepChannelTarget(interface, step)
    if target is None:
        return False
    _Send(target, interface)
    return True


# Online state (the login screen's ServerStateChecker) ---------------------------------
class StateProbe(object):
    """Receives ``NotifyChannelState`` from the native checker. A module-level
    object that is never freed: the checker keeps a raw pointer to it."""

    def __init__(self):
        self.keys = {}       # checker key -> channel number
        self.states = {}     # channel number -> state
        self.until = 0.0     # pump replies until this time
        self.next = 0.0

    def Request(self, channels, now):
        try:
            import ServerStateChecker as checker
        except ImportError:
            return False
        self.keys = {}
        checker.Initialize()
        checker.Create(self)
        for number, entry in channels:
            try:
                key, ip, port = int(entry['key']), str(entry['ip']), int(entry['udp_port'])
            except (KeyError, TypeError, ValueError):
                continue
            self.keys[key] = number
            checker.AddChannel(key, ip, port)
        if not self.keys:
            return False
        self.until = now + PROBE_TIMEOUT
        self.next = now + PROBE_INTERVAL
        checker.Request()
        return True

    def Pump(self, now):
        if now > self.until:
            return
        try:
            import ServerStateChecker as checker
            checker.Update()
        except ImportError:
            self.until = 0.0

    def NotifyChannelState(self, key, state, count=0):
        number = self.keys.get(key)
        if number is not None:
            self.states[number] = int(state)


_probe = StateProbe()


# Window -------------------------------------------------------------------------------
def _Send(channel, interface):
    """The channel buttons' way to switch (``minimappanel.Invoke('channel.N')`` -> ``RequestChannelChange`` ->
    ``/move_channel N``), the same as the CH+ / CH- shortcuts send."""
    import minimappanel
    minimappanel.Invoke('channel.%d' % channel, interface)
    return True


class BarBehaviour(object):
    """What every look of the bar does the same way: probing, refreshing, switching, pinning, placing, closing.
    A look provides ``Refresh(force)``, ``_Enabled(channel)``, ``_HideTip()`` and ``Destroy()``."""

    def Model(self):
        """``(cells, tag)`` of the bar now (``Layout`` with the live channel facts and the probe's states)."""
        facts = _Facts(self.interface)
        if facts:
            current, map_index, unused_count, vip = facts
        else:
            current, map_index, vip = 0, 0, False
        return Layout(current, map_index, [number for number, unused in ChannelList()], vip, _probe.states)

    def OnUpdate(self):
        now = app.GetTime()
        _probe.Pump(now)
        if now >= _probe.next:
            _probe.Request(ChannelList(), now)
        if now >= self.nextRefresh:
            self.nextRefresh = now + REFRESH
            self.Refresh()

    # Actions ---------------------------------------------------------------------------
    def Switch(self, channel):
        """The bar stays open after a switch (owner round 4)."""
        if not self._Enabled(channel):
            return False
        _Send(channel, self.interface)
        self.nextRefresh = 0.0
        return True

    def Step(self, step):
        """CH+ (1) / CH- (-1) of the bar (``StepTarget``); False where no change is possible."""
        cells, unused_tag = self.Model()
        target = StepTarget(cells, step)
        if target is None:
            return False
        _Send(target, self.interface)
        self.nextRefresh = 0.0
        return True

    def TogglePin(self):
        self.settings.pinned = not self.settings.pinned
        if self.settings.pinned:
            (self.settings.x, self.settings.y) = self.GetGlobalPosition()
        if not Save(self.settings):
            import buttonpanelsettings
            buttonpanelsettings.ReportStoreError()
        self.Refresh(force=True)

    def OnMoveWindow(self, x, y):
        """Called by the client (CWindow::OnMoveWindow) after a drag of this movable window."""
        if self.settings.pinned:
            (self.settings.x, self.settings.y) = self.GetGlobalPosition()
            Save(self.settings)

    def OpenAt(self, position, place=None):
        """Popup at the cursor (above it, or below when there is no room); ``place``: this top-left corner instead
        (a look switched while the bar was open). A pinned bar opens at its saved place."""
        self.settings = Load()
        _probe.next = 0.0   # fresh online states for this opening
        self.Refresh(force=True)
        width, height = self.GetWidth(), self.GetHeight()
        screen_w, screen_h = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        if self.settings.pinned and self.settings.x is not None:
            x, y = self.settings.x, self.settings.y
        elif place is not None:
            x, y = place
        else:
            x, y = position[0] - width // 2, position[1] - height - 10
            if y < 0:
                y = position[1] + 18
        x = max(0, min(int(x), screen_w - width))
        y = max(0, min(int(y), screen_h - height))
        self.SetPosition(x, y)
        self.Show()
        self.SetTop()

    def Close(self):
        if self.settings.pinned:
            return False
        self._HideTip()
        self.Hide()
        return True

    def OnPressEscapeKey(self):
        return self.Close() if self.IsShow() else False


class ChannelBar(BarBehaviour, ui.Window):
    """The original look of the bar (Settings -> "Starý vzhled", and the fallback of the R1 bar)."""

    def __init__(self, interface):
        ui.Window.__init__(self)
        self.interface = interface
        self.settings = Load()
        self.AddFlag('float')
        self.AddFlag('movable')
        self.border = self._Bar(BORDER)
        self.background = self._Bar(BACKGROUND)
        self.cells = []
        self.tooltip = None
        self.tag = self._Text(fontconfig.ROLE_SECTION, GOLD)
        self.tagMarker = self._Marker(self)
        self.pin = ui.Button()
        self.pin.SetParent(self)
        self.pin.SetEvent(self.TogglePin)
        self.pin.channelTooltip = ''
        self.pinLocked = None
        if hasattr(self.pin, 'SetShowToolTipEvent'):
            import uibuttonpaneltooltip
            from _weakref import proxy
            uibuttonpaneltooltip.Attach(self.pin, self._ToolTip(),
                                        lambda pin=proxy(self.pin): getattr(pin, 'channelTooltip', ''), 'above')
        self.pin.Show()
        self.close = ui.Button()
        self.close.SetParent(self)
        self.close.SetUpVisual(CLOSE_ART % 'normal')
        self.close.SetOverVisual(CLOSE_ART % 'hover')
        self.close.SetDownVisual(CLOSE_ART % 'pressed')
        self.close.SetEvent(self.Close)
        self.shown = None
        self.nextRefresh = 0.0

    def _Bar(self, color):
        bar = ui.Bar()
        bar.SetParent(self)
        bar.AddFlag('not_pick')
        bar.SetColor(color)
        bar.Show()
        return bar

    def _Text(self, role, color):
        line = ui.TextLine()
        line.SetParent(self)
        line.AddFlag('not_pick')
        line.SetFontName(fontconfig.FontForRole(role))
        line.SetFontColor(*color)
        line.SetHorizontalAlignCenter()
        line.SetVerticalAlignCenter()
        return line

    @staticmethod
    def _Marker(parent):
        marker = ui.ImageBox()
        marker.SetParent(parent)
        marker.AddFlag('not_pick')
        marker.LoadImage(ART + 'current_marker.png')
        marker.Hide()
        return marker

    def _ToolTip(self):
        if self.tooltip is None:
            import uibuttonpaneltooltip
            self.tooltip = uibuttonpaneltooltip.PanelToolTip()
        return self.tooltip

    def _Cell(self, channel):
        while len(self.cells) < channel:
            import minimappanelicons as icons
            number = len(self.cells) + 1
            action_id = 'channel.%d' % number
            button = ui.Button()
            button.SetParent(self)
            button.SetUpVisual(icons.Visual(action_id, 'normal'))
            button.SetOverVisual(icons.Visual(action_id, 'hover'))
            button.SetDownVisual(icons.Visual(action_id, 'hover'))
            button.SetEvent(lambda selected=number: self.Switch(selected))
            button.channelTooltip = ''
            if hasattr(button, 'SetShowToolTipEvent'):
                import uibuttonpaneltooltip
                from _weakref import proxy
                uibuttonpaneltooltip.Attach(button, self._ToolTip(),
                                            lambda cell=proxy(button): getattr(cell, 'channelTooltip', ''), 'above')
            mark = ui.TextLine()
            mark.SetParent(button)
            mark.AddFlag('not_pick')
            mark.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_SECTION))
            mark.SetHorizontalAlignCenter()
            mark.SetVerticalAlignCenter()
            mark.SetPosition(ICON // 2, ICON // 2)
            mark.SetText(icons.Mark(action_id) or str(number))
            mark.Show()
            overlay = decor.ButtonDecor(button, decor.KIND_MEDALLION)
            self.cells.append({'button': button, 'mark': mark, 'overlay': overlay, 'marker': self._Marker(self),
                               'enabled': True})
        return self.cells[channel - 1]

    # Content ---------------------------------------------------------------------------
    def Refresh(self, force=False):
        facts = _Facts(self.interface)
        channels = ChannelList()
        if facts:
            current, map_index, unused_count, vip = facts
        else:
            current, map_index, vip = 0, 0, False
        cells, tag = Layout(current, map_index, [number for number, unused in channels], vip, _probe.states)
        key = (tuple(cell.Key() for cell in cells), tag, self.settings.pinned)
        if key == self.shown and not force:
            return
        self.shown = key
        x = PAD
        if tag:
            self.tag.SetText(tag)
            self.tag.SetPosition(x + TAG_WIDTH // 2, PAD + ICON // 2)
            self.tag.Show()
            self._PlaceMarker(self.tagMarker, x + TAG_WIDTH // 2)
            x += TAG_WIDTH
        else:
            self.tag.Hide()
            self.tagMarker.Hide()
        shown = set()
        for cell in cells:
            entry = self._Cell(cell.channel)
            entry['button'].SetPosition(x, PAD)
            entry['button'].channelTooltip = cell.tooltip
            entry['enabled'] = cell.enabled
            # Dimmed = the native veil; no gold rim any more (owner round 4).
            state = None if cell.enabled else badges.STATE_UNAVAILABLE
            entry['overlay'].SetDecor(badges.Decor(None, 0, state), False)
            entry['button'].Show()
            if cell.current:
                self._PlaceMarker(entry['marker'], x + ICON // 2)
            else:
                entry['marker'].Hide()
            shown.add(cell.channel)
            x += CELL
        for index, entry in enumerate(self.cells):
            if index + 1 not in shown:
                entry['button'].Hide()
                entry['marker'].Hide()
        self._LockVisuals(self.settings.pinned)
        self.pin.SetPosition(x + 2, PAD + (ICON - PIN_WIDTH) // 2)
        x += 2 + PIN_WIDTH
        if self.settings.pinned:
            self.close.Hide()   # a pinned bar never closes
        else:
            self.close.SetPosition(x + 2, PAD + (ICON - CLOSE) // 2)
            self.close.Show()
            x += 2 + CLOSE
        width, height = x + PAD, PAD + ICON + MARKER_HEIGHT + PAD // 2
        self.SetSize(width, height)
        self.border.SetPosition(0, 0)
        self.border.SetSize(width, height)
        self.background.SetPosition(1, 1)
        self.background.SetSize(width - 2, height - 2)

    def _LockVisuals(self, locked):
        self.pin.channelTooltip = T('Odepnout lištu', 'Unpin the bar') if locked else T('Připnout lištu', 'Pin the bar')
        if locked == self.pinLocked:
            return
        self.pinLocked = locked
        name = ART + 'lock_' + ('closed' if locked else 'open') + '_%s.png'
        self.pin.SetUpVisual(name % 'normal')
        self.pin.SetOverVisual(name % 'hover')
        self.pin.SetDownVisual(name % 'pressed')

    @staticmethod
    def _PlaceMarker(marker, centre_x):
        marker.SetPosition(centre_x - 3, PAD + ICON + 1)
        marker.Show()

    def _Enabled(self, channel):
        return 0 < channel <= len(self.cells) and self.cells[channel - 1]['enabled']

    def _HideTip(self):
        if self.tooltip is not None:
            self.tooltip.Hide(None)

    def Destroy(self):
        self.Hide()
        for entry in self.cells:
            entry['overlay'].Destroy()
        self.cells = []
        self.tooltip = None
        self.interface = None


_bar = {'window': None, 'kind': None, 'failed': False, 'retired': []}
LEGACY = 'legacy'
STEPPER = 'stepper'
LIST = 'list'
STYLE_KEY = 'channel_bar_style'     # settingslook: 'stepper' (default) / 'list'


def Kind():
    """The look of the bar: 'legacy' (Settings -> "Starý vzhled"), else the R1 style chosen in Settings -> Vzhled ->
    "Lišta kanálů" ('stepper' default, 'list'). A failed R1 build keeps 'legacy' for this session."""
    try:
        import settingslook
        if settingslook.Get('look') == LEGACY:
            return LEGACY
        style = LIST if settingslook.Get(STYLE_KEY) == LIST else STEPPER
    except Exception:
        return LEGACY
    return LEGACY if _bar['failed'] else style


def _Trace():
    try:
        import uir1
        uir1.TraceFailure('the channel bar')
    except Exception:
        import dbg
        import traceback
        dbg.TraceError('channel bar: %s' % traceback.format_exc())


def _Build(interface, kind):
    if kind != LEGACY:
        try:
            import uichannelbarr1
            return uichannelbarr1.Create(interface, kind), kind
        except Exception:
            _Trace()
            _bar['failed'] = True
    return ChannelBar(interface), LEGACY


def _Window(interface):
    kind = Kind()
    window = _bar['window']
    if window is not None and _bar['kind'] != kind:
        _Retire(window)
        window = None
    if window is None:
        window, kind = _Build(interface, kind)
        _bar['window'], _bar['kind'] = window, kind
    else:
        window.interface = interface
    return window


def _Retire(window):
    """Hides and frees a bar of another look. It may be the caller (a failing R1 bar in its own OnUpdate), so it is
    kept referenced until the next DestroyAll."""
    try:
        window.Destroy()
    except Exception:
        pass
    _bar['retired'].append(window)
    if _bar['window'] is window:
        _bar['window'] = _bar['kind'] = None


def FallBack(window):
    """An R1 bar that raised: traced, the original bar takes its place (open where it was) for this session."""
    _Trace()
    _bar['failed'] = True
    try:
        shown, place = window.IsShow(), window.GetGlobalPosition()
    except Exception:
        shown, place = False, None
    interface = getattr(window, 'interface', None)
    _Retire(window)
    if shown:
        try:
            _Window(interface).OpenAt((0, 0), place)
        except Exception:
            _Trace()


def StyleChanged(interface=None):
    """Settings changed the look or the style: an open bar is rebuilt in the new one at the same place."""
    window = _bar['window']
    if window is None or _bar['kind'] == Kind():
        return False
    shown, place = window.IsShow(), window.GetGlobalPosition()
    interface = interface if interface is not None else window.interface
    _Retire(window)
    if shown:
        _Window(interface).OpenAt((0, 0), place)
    return True


def Toggle(interface):
    """The "Změna kanálu" click: open the bar at the cursor; a second click
    closes it (a pinned bar only comes to the front)."""
    try:
        window = _Window(interface)
        if window.IsShow():
            if window.settings.pinned:
                window.SetTop()
            else:
                window.Close()
            return True
        window.OpenAt(wndMgr.GetMousePosition())
        return True
    except Exception:
        import dbg
        import traceback
        dbg.TraceError('channel bar: %s' % traceback.format_exc())
        return False


def RestorePinned(interface):
    """After login: a pinned bar shows again at its saved place."""
    if not Load().pinned:
        return False
    try:
        _Window(interface).OpenAt((0, 0))
        return True
    except Exception:
        return False


def DestroyAll():
    window = _bar['window']
    _bar['window'] = _bar['kind'] = None
    if window is not None:
        window.Destroy()
    _bar['retired'] = []
    _probe.until = _probe.next = 0.0
    try:
        import ServerStateChecker
        ServerStateChecker.Initialize()   # drop a pending request; the probe object stays alive
    except ImportError:
        pass
