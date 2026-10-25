"""Status providers of the button panels: function ID -> badge / state (wave 1).

Owner decision 2026-10-04 (proposal ``panely-odznaky-stav-navrh.md``): wave 1
uses only data the client already holds. A provider never opens a window,
never creates a lazily built window and never sends a packet; when the data is
not there yet it returns nothing. Each provider gets a ``Context`` (the
interface plus the native modules, injectable for tests) and returns a
``buttonpanelbadges.Decor`` or None. ``Evaluate`` runs the providers of the
shown functions and never raises: a failing provider shows nothing.

Badge rules (``BADGE_ACTION`` = ruby, something waits for the player;
``BADGE_INFO`` = gold, live or new) and their sources are documented at each
provider. Countdowns are in seconds; ``total`` sizes the dark sector.
"""
import buttonpanelbadges as badges
from buttonpanelbadges import Decor, SecondsBadge, BADGE_ACTION, BADGE_INFO
from buttonpanelbadges import STATE_ACTIVE, STATE_RUNNING, STATE_CURRENT, STATE_UNAVAILABLE, STATE_ROLLING

VIP_CHANNELS = (6, 7)
MAX_CHANNEL = 99
INSTANCE_MAP_INDEX = 10000


def _import(name):
    try:
        return __import__(name)
    except ImportError:
        return None


class Context(object):
    """What a provider may read. ``modules`` overrides imports (tests)."""

    def __init__(self, interface, modules=None):
        self.interface = interface
        self._modules = dict(modules or {})

    def module(self, name):
        if name not in self._modules:
            self._modules[name] = _import(name)
        return self._modules[name]

    def now(self):
        """Server-synchronised unix time (``app.GetGlobalTimeStamp``)."""
        app = self.module('app')
        return float(app.GetGlobalTimeStamp()) if app else 0.0

    def clock(self):
        """Client monotonic seconds (``app.GetTime``)."""
        app = self.module('app')
        return float(app.GetTime()) if app else 0.0

    def attr(self, *path):
        """``interface.a.b.c`` or None; never builds a lazily created window."""
        value = self.interface
        for name in path:
            if value is None:
                return None
            value = getattr(value, name, None)
        return value


_PROVIDERS = {}
_PREFIX_PROVIDERS = []
# What a function can show at all (for the per-button menu entries).
_CAPABILITIES = {}


def provider(action_id, badge=False, state=False):
    def register(function):
        if action_id.endswith('.'):
            _PREFIX_PROVIDERS.append((action_id, function))
        else:
            _PROVIDERS[action_id] = function
        _CAPABILITIES[action_id] = (badge, state)
        return function
    return register


def ProviderFor(action_id):
    function = _PROVIDERS.get(action_id)
    if function is not None:
        return function
    for prefix, function in _PREFIX_PROVIDERS:
        if isinstance(action_id, str) and action_id.startswith(prefix):
            return function
    return None


def Capabilities(action_id):
    """(can show a badge, can show a state/countdown)."""
    if action_id in _CAPABILITIES:
        return _CAPABILITIES[action_id]
    for prefix, unused in _PREFIX_PROVIDERS:
        if isinstance(action_id, str) and action_id.startswith(prefix):
            return _CAPABILITIES[prefix]
    return (False, False)


def KnownIds():
    return tuple(sorted(_PROVIDERS))


def Evaluate(action_ids, context):
    """{action id: Decor} for the given functions; a failing provider gives EMPTY."""
    result = {}
    for action_id in action_ids:
        function = ProviderFor(action_id)
        decor = None
        if function is not None:
            try:
                decor = function(context, action_id)
            except Exception:
                decor = None
        result[action_id] = decor if isinstance(decor, Decor) else badges.EMPTY
    return result


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _call(module, name, *args):
    function = getattr(module, name, None) if module is not None else None
    return function(*args) if callable(function) else None


# Character -----------------------------------------------------------------------
@provider('character.skills', badge=True)
def SkillPoints(context, unused_id):
    """Ruby number: unspent active skill points - the same rule as the classic
    "+" orb (``uigamebutton.CheckGameButton`` via ``skillraise``): only while a
    skill of the group can still take a point (``skillraise.CanTakePoint``:
    a class skill below M; owner 8. 10.: M/G/P need books, horse skills use
    their own points, so no badge when every class skill is M or better). Support points
    are never shown (``HIDE_SUPPORT_SKILL_POINT``). Nothing before a skill
    group is chosen (``net.GetMainActorSkillGroup() == 0``)."""
    player = context.module('player')
    net = context.module('net')
    if player is None:
        return None
    group = _call(net, 'GetMainActorSkillGroup')
    if group is not None and _int(group) == 0:
        return None
    skill = context.module('skill')
    rule = context.module('skillraise')
    if skill is not None and rule is not None:
        points = rule.SpendablePoints(player, skill, net)
    else:
        points = _int(player.GetStatus(player.SKILL_ACTIVE))
    if points <= 0:
        return None
    return Decor(BADGE_ACTION, points)


PERSISTENT_QUEST_BUTTONS = ('permanent_tasks', 'daily_tasks')


@provider('character.quests', badge=True)
def QuestLetters(context, unused_id):
    """Ruby number: unread quest letters on the left of the screen
    (``interface.questButtonList`` without the persistent "Trvalé úkoly" /
    "Denní úkoly" buttons; a letter disappears when it is clicked)."""
    buttons = context.attr('questButtonList') or ()
    letters = sum(1 for button in buttons if getattr(button, 'index', None) not in PERSISTENT_QUEST_BUTTONS)
    return Decor(BADGE_ACTION, letters) if letters > 0 else None


@provider('information.skill_tree', badge=True, state=True)
def SkillTree(context, unused_id):
    """Ruby dot: some node can be upgraded now (``model.CanUpgrade`` and the
    next cost - points, yang, items - is affordable, as ``uiskilltree``
    ``CanUpgradeNode``). Gold rim + countdown while the timed activation runs
    (``wndSkillTree.activationEnabled`` / ``activationRemainingSeconds``, kept
    current by the runtime even while the window is hidden)."""
    window = context.attr('wndSkillTree')
    if window is None:
        return None
    badge = None
    model = getattr(window, 'model', None)
    if model is not None and _AffordableUpgrade(context, model):
        badge = BADGE_ACTION
    state = remaining = total = None
    if getattr(window, 'activationEnabled', False):
        seconds = _int(getattr(window, 'activationRemainingSeconds', 0))
        if seconds > 0:
            state = STATE_ACTIVE
            remaining = seconds
            total = _int(getattr(window, 'activationMaxSeconds', 0)) or seconds
    if badge is None and state is None:
        return None
    return Decor(badge, 0, state, remaining, total)


def _AffordableUpgrade(context, model):
    if not callable(getattr(model, 'IsReady', None)) or not model.IsReady():
        return False
    balance = model.GetPointBalance()
    if balance is None:
        return False
    player = context.module('player')
    if player is None:
        return False
    yang = _int(player.GetElk())
    for node_id in model.GetNodePresenters() or ():
        if not model.CanUpgrade(node_id):
            continue
        cost = model.GetNextCost(node_id)
        if not cost:
            continue
        if balance < _int(cost.get('points')) or yang < _int(cost.get('yang')):
            continue
        items = cost.get('items') or ()
        if all(_int(player.GetItemCountByVnum(_int(item.get('vnum')))) >= _int(item.get('count'))
               for item in items):
            return True
    return False


# Community ------------------------------------------------------------------------
GUILD_RIGHT_APPROVE = 256
GUILD_APPROVAL_PENDING = 0


@provider('community.guild', badge=True)
def GuildApprovals(context, unused_id):
    """Ruby number: guild proposals waiting for my approval (guild v2,
    ``APPROVAL`` rows pending, not proposed by me, and I hold the approve
    right - the rule of ``uiguildv2`` approvals page). Reads the already built
    v2 window only (``wndGuild.window``; the router builds it on first use)."""
    net = context.module('net')
    if net is not None and not _call(net, 'IsGuildV2Available'):
        return None
    window = context.attr('wndGuild', 'window')
    if window is not None and not getattr(window, 'shows_approvals', True):
        return None             # the approvals page of the guild window is locked
    model = getattr(window, 'model', None) if window is not None else None
    if model is None or not getattr(model, 'guild', None):
        return None
    module = context.module('guildv2model')
    if module is None:
        return None
    capability = model.row(module.CAPABILITY)
    if not capability or len(capability[0]) <= 9:
        return None
    pid = capability[0][9]
    if not model.can(pid, GUILD_RIGHT_APPROVE):
        return None
    waiting = sum(1 for values, unused_title, unused_body in model.rows(module.APPROVAL)
                  if len(values) > 5 and values[5] == GUILD_APPROVAL_PENDING and values[2] != pid)
    return Decor(BADGE_ACTION, waiting) if waiting > 0 else None


# Rated arena ----------------------------------------------------------------------
QUEUE_IDLE, QUEUE_SEARCHING, QUEUE_READY, QUEUE_MATCH, QUEUE_COOLDOWN = range(5)


ARENA_MODES = {1: '1v1', 2: '2v2', 3: '3v3'}


def _ArenaShown(context, module):
    """The server announced the arena open and the core offers matchmaking (featureavailability.IsShown of the gate
    branch; its two parts on an older base). Closed: no badge, no state, no hint."""
    if module is None or not _call(module, 'IsAvailable'):
        return False
    gate = context.module('featureavailability')
    if gate is None:
        return True
    name = getattr(gate, 'RANKED_ARENA', 'ranked_arena')
    shown = getattr(gate, 'IsShown', None)
    if callable(shown):
        return bool(shown(name))
    available = getattr(gate, 'IsAvailable', None)
    return bool(available(name)) if callable(available) else True


def _UseR1(context):
    r1 = context.module('uir1')
    try:
        return bool(r1 is not None and r1.UseR1())
    except Exception:
        return False


def _ArenaState(context):
    """(kind, values) of the rated arena for the medallion and its hint, or None (idle / closed)."""
    module = context.module('pvpmatchmaking')
    if not _ArenaShown(context, module):
        return None
    queue = tuple(module.GetQueue() or ())
    if len(queue) < 5:
        return None
    status = _int(queue[0])
    ready = tuple(_call(module, 'GetReady') or ())
    now = context.now()
    if len(ready) >= 3 and ready[0] and _int(ready[2]) > now:
        return 'ready', dict(remaining=min(15, _int(ready[2]) - now))
    if status == QUEUE_SEARCHING:
        return 'search', dict(mode=_int(queue[1]), elapsed=_int(queue[2]))
    if status == QUEUE_MATCH:
        match = tuple(_call(module, 'GetMatch') or ())
        if len(match) >= 9 and _int(match[8]):
            team = _int(match[2])
            mine, theirs = (_int(match[5]), _int(match[4])) if team == 2 else (_int(match[4]), _int(match[5]))
            return 'match', dict(round=max(1, _int(match[3])), mine=mine, theirs=theirs)
        return 'match', dict()
    if status == QUEUE_COOLDOWN and _int(queue[4]) > 0:
        return 'cooldown', dict(remaining=_int(queue[4]))
    return None


@provider('system.pvp_matchmaking', badge=True, state=True)
def RatedArena(context, unused_id):
    """``pvpmatchmaking`` state, pushed by the server as it changes (nothing while the server keeps the arena closed):

    * ready check pending (``GetReady``: id and a future deadline) - the R1 look: the one badge (red circle) with the
      seconds left, the countdown arc and the brighter ring (rated arena round 9. 10., variant C); the original look:
      the ruby dot, the button flashes, countdown to the deadline;
    * searching - running rim; in a match - the active ring;
    * cooldown after a refused match - countdown (``GetQueue`` cooldown)."""
    state = _ArenaState(context)
    if state is None:
        return None
    kind, values = state
    if kind == 'ready':
        remaining = values['remaining']
        if _UseR1(context):
            return SecondsBadge(BADGE_ACTION, remaining, STATE_ACTIVE, remaining, 15)
        return Decor(BADGE_ACTION, 0, STATE_ACTIVE, remaining, 15, flash=True)
    if kind == 'search':
        return Decor(None, 0, STATE_RUNNING)
    if kind == 'match':
        return Decor(None, 0, STATE_ACTIVE)
    return Decor(None, 0, None, values['remaining'])


def _Clock(seconds):
    seconds = max(0, int(seconds))
    return '%d:%02d' % (seconds // 60, seconds % 60)


def RatedArenaHint(context):
    """The lines under the vein of the medallion hint (title "Hodnocená aréna"), or None for the one-line hint
    (idle, closed). Only what the client knows: no queue estimate (D1), no player count (D8)."""
    state = _ArenaState(context)
    if state is None:
        return None
    kind, values = state
    dim = 0xFF928B84
    if kind == 'ready':
        return ['Zápas nalezen · potvrď do %d s' % int(values['remaining']), ('Klik: otevřít okno', dim)]
    if kind == 'search':
        mode = ARENA_MODES.get(values['mode'], '')
        return ['Hledání soupeře · %s' % mode if mode else 'Hledání soupeře', _Clock(values['elapsed']),
                ('Klik: otevřít okno', dim)]
    if kind == 'match':
        if 'round' in values:
            return ['Zápas běží · kolo %d · %d : %d' % (values['round'], values['mine'], values['theirs'])]
        return ['Zápas běží']
    return [('Trest fronty %s' % _Clock(values['remaining']), 0xFFEC463C)]


def HintBody(action_id, context):
    """Status lines of a launcher hint (only the rated arena has them today); None = the plain name."""
    if action_id == 'system.pvp_matchmaking':
        try:
            return RatedArenaHint(context)
        except Exception:
            return None
    return None


# Channels ---------------------------------------------------------------------------
HUB_PRESENTED_CHANNEL = 1


def IsHub(current, map_index):
    """``globalhub.IsGlobalHub``: channel 0 on map 1."""
    return current == 0 and map_index == 1


def ChannelState(channel, current, map_index, channel_count, vip):
    """``STATE_CURRENT`` / ``STATE_UNAVAILABLE`` / None for one channel button.

    Owner 2026-10-04 ("Kanál 1 je šedý, když na něm jsem"): the current channel
    is bright with the gold rim - in the global hub that is CH1, exactly as the
    minimap shows it (``minimapstatus.FormatChannel``); only a VIP channel
    (6, 7) without VIP is dimmed. Places where no change is possible (hub, CH99,
    an instance) dim nothing: a click gets the native refusal message of
    ``uisystem.RequestChannelChange``."""
    if channel < 1 or channel > channel_count:
        return None
    shown = HUB_PRESENTED_CHANNEL if IsHub(current, map_index) else current
    if channel == shown:
        return STATE_CURRENT
    if channel in VIP_CHANNELS and not vip:
        return STATE_UNAVAILABLE
    return None


def _ChannelFacts(context):
    app = context.module('app')
    net = context.module('net')
    if app is None or net is None or not getattr(app, 'ENABLE_MOVE_CHANNEL', False):
        return None
    uisystem = context.module('uiSystem') or context.module('uisystem')
    count = _int(_call(uisystem, 'GetChannelCount'))
    player = context.module('player')
    vip = bool(_call(player, 'IsVipActive'))
    return _int(net.GetChannelNumber()), _int(net.GetMapIndex()), count, vip


@provider('channel.', state=True)
def ChannelButton(context, action_id):
    """Current channel: gold rim, bright (never the dimmed pressed look);
    unavailable: dark veil, with "VIP" on a VIP channel the player cannot enter."""
    facts = _ChannelFacts(context)
    if facts is None:
        return None
    current, map_index, count, vip = facts
    channel = _int(action_id.split('.', 1)[1], -1)
    state = ChannelState(channel, current, map_index, count, vip)
    if state is None:
        return None
    label = 'VIP' if state == STATE_UNAVAILABLE and channel in VIP_CHANNELS and not vip else ''
    return Decor(None, 0, state, label=label)


@provider('system.channel_switch', state=True)
def ChannelSwitch(context, unused_id):
    """The current channel as a small label (``CH3``; ``CH1`` in the hub, like the minimap). On the R1 launcher (two
    red arrows, ``minimappanelicons.R1Channel``) the number alone, big, between the arrows: ``3``, CH99 ``99``."""
    facts = _ChannelFacts(context)
    if facts is None:
        return None
    current, map_index, unused_count, unused_vip = facts
    if IsHub(current, map_index):
        current = HUB_PRESENTED_CHANNEL   # the minimap shows the hub as CH1 too
    if current <= 0:
        return None
    if _call(context.module('minimappanelicons'), 'R1Channel', 'system.channel_switch'):
        return Decor(label='%d' % current, numeral=True)
    if current == MAX_CHANNEL:
        return None
    return Decor(label='CH%d' % current)


# Battle Pass ------------------------------------------------------------------------
BP_UNCLAIMED = 0
HALF_DAY = 12 * 3600


def BattlePassMonthOpen(activated_month, season_end, now):
    """Server rule (``CollectBattlePassRewards``, char_battlepass.cpp:341-347):
    rewards are collectable only in the month the pass was activated (server
    local month == MONTH_ACTIVATED, 1-12). ``BP_INFOG`` gives that month and the
    end of the server's current month (``seasonEndTime`` = the 1st of the next
    month, 00:00 server time); the month of ``season_end - 12 h`` is the
    server's month for any client time zone less than 12 h away. Unknown data
    or a passed month end: closed (the server would refuse)."""
    if not activated_month or not season_end or now >= season_end:
        return False
    import time
    return time.localtime(season_end - HALF_DAY).tm_mon == activated_month


@provider('system.battle_pass', badge=True, state=True)
def BattlePass(context, unused_id):
    """Ruby number: rewards claimable now - the server's collect rule
    (``CollectBattlePassRewards``): only in the activation month
    (``BattlePassMonthOpen``), level reached, not claimed, premium rows only
    with premium. Rows live in the hidden ``wndBattlePass`` (built at
    start) after ``/battle_pass request`` (``PrefetchBattlePass``). Countdown:
    the season end (``seasonEndTime``, server unix time)."""
    window = context.attr('wndBattlePass')
    module = context.module('ui_bpass')
    if window is None or module is None:
        return None
    level = _int(getattr(module, 'CURRENT_LEVEL', 0))
    free = getattr(getattr(window, 'ListBoxItems', None), 'itemList', None) or ()
    premium_box = getattr(window, 'ListBoxItemsPremium', None)
    premium = getattr(premium_box, 'itemList', None) or ()
    unlocked = bool(_call(premium_box, 'IsPremiumUnlocked'))
    rows = list(free) + (list(premium) if unlocked else [])
    end = _int(getattr(window, 'seasonEndTime', 0))
    now = context.now()
    claimable = 0
    if BattlePassMonthOpen(_int(getattr(window, 'monthBattlePass', 0)), end, now):
        claimable = sum(1 for row in rows if _int(getattr(row, 'status', -1), -1) == BP_UNCLAIMED
                        and level >= _int(getattr(row, 'iNecessaryLevel', 1 << 30), 1 << 30))
    remaining = end - now if end else None
    if not claimable and not (remaining and remaining > 0):
        return None
    return Decor(BADGE_ACTION if claimable else None, claimable, None, remaining)


PREFETCH_INTERVAL = 60.0
_prefetch = {'next': 0.0}


def PrefetchBattlePass(context):
    """Wave 1, owner-approved: when the Battle Pass button is on a panel and the
    hidden window holds no reward rows (login, warp), send the same
    ``/battle_pass request`` its ``Show()`` sends - at most once a minute and
    never while the window is open (it requests itself). Clears the three lists
    first, exactly like ``Show()``, so a reply never duplicates rows."""
    window = context.attr('wndBattlePass')
    net = context.module('net')
    if window is None or net is None or _call(window, 'IsShow'):
        return False
    lists = [getattr(window, name, None) for name in ('ListBoxItem', 'ListBoxItems', 'ListBoxItemsPremium')]
    if any(box is None for box in lists):
        return False
    if any(getattr(box, 'itemList', None) for box in lists[1:]):
        return False
    clock = context.clock()
    if clock < _prefetch['next']:
        return False
    _prefetch['next'] = clock + PREFETCH_INTERVAL
    for box in lists:
        box.Clear(True)
    net.SendChatPacket('/battle_pass request')
    return True


# Event calendar ---------------------------------------------------------------------
EVENT_INDEX_START, EVENT_INDEX_END, EVENT_INDEX_ACTIVE = 15, 16, 17
EVENT_SOON = 30 * 60


@provider('information.event_calendar', badge=True, state=True)
def EventCalendar(context, unused_id):
    """Gold dot: an event runs now (``eventcalendarlogic.EventState`` ==
    "active", the calendar's own rule). Countdown: the running event that ends
    first, otherwise an event that starts within 30 minutes. Data: the module
    global ``uiEventCalendar.server_event_data`` (sent at login and on change;
    read fresh, ``ClearEventManager`` rebinds it)."""
    module = context.module('uiEventCalendar')
    logic = context.module('eventcalendarlogic')
    if module is None or logic is None:
        return None
    data = getattr(module, 'server_event_data', None)
    if not isinstance(data, dict):
        return None
    now = context.now()
    running = False
    ends, starts = [], []
    for day in data.values():
        if not isinstance(day, dict):
            continue
        for row in day.values():
            try:
                start, end, active = _int(row[EVENT_INDEX_START]), _int(row[EVENT_INDEX_END]), row[EVENT_INDEX_ACTIVE]
            except (IndexError, KeyError, TypeError):
                continue
            state = logic.EventState(start, end, active, now)
            if state == 'active':
                running = True
                if end > start and end > now:
                    ends.append((end - now, end - start))
            elif state == 'upcoming' and 0 < start - now <= EVENT_SOON:
                starts.append((start - now, EVENT_SOON))
    countdown = min(ends) if ends else (min(starts) if starts else None)
    if not running and countdown is None:
        return None
    remaining, total = countdown if countdown else (None, None)
    return Decor(BADGE_INFO if running else None, 0, None, remaining, total)


# Dungeons and countdowns --------------------------------------------------------------
def _DungeonRows(context, watched_only):
    """[(vnum, status)] from the countdown model (the HUD's own rule)."""
    model = context.module('countdownmodel')
    track = context.module('uiDungeonTrack')
    player = context.module('player')
    if model is None or track is None or player is None:
        return []
    catalog = getattr(track, 'dungeonData', None)
    if not isinstance(catalog, dict):
        return []
    known = context.attr('countdownKnownDungeons') or ()
    level = _int(player.GetStatus(player.LEVEL))
    now = context.now()
    rows = model.watched_dungeons(catalog) if watched_only else sorted(
        (vnum, data) for vnum, data in catalog.items() if isinstance(data, dict))
    result = []
    for vnum, data in rows:
        status = model.dungeon_status(data, now, level, vnum in known)
        result.append((vnum, data, status))
    return result


def _DungeonCountdown(rows):
    best = None
    for unused_vnum, data, status in rows:
        if status.get('state') == 'cooldown':
            candidate = (_int(status.get('remaining')), _int(data.get('cooldown')))
            if best is None or candidate[0] < best[0]:
                best = candidate
    return best


@provider('information.dungeon', badge=True, state=True)
def Dungeons(context, unused_id):
    """Gold dot: a watched dungeon (alarm on) is ready again; countdown: the
    shortest remaining cooldown of the watched dungeons (all dungeons when none
    is watched). Data: ``uiDungeonTrack.dungeonData`` + the server cooldowns
    sent at login and after each run (``countdownKnownDungeons``)."""
    watched = _DungeonRows(context, True)
    ready = any(status.get('state') == 'ready' for unused, unused_data, status in watched)
    countdown = _DungeonCountdown(watched if watched else _DungeonRows(context, False))
    if not ready and countdown is None:
        return None
    remaining, total = countdown if countdown else (None, None)
    return Decor(BADGE_INFO if ready else None, 0, None, remaining, total)


def _BiologRows(context):
    """(window, [(index, row)]) of the biolog snapshot, or (None, [])."""
    window = context.attr('wndBio')
    if window is None or not getattr(window, 'dataKnown', False):
        return None, []
    researches = getattr(window, 'researches', None)
    if not isinstance(researches, dict):
        return None, []
    return window, sorted(researches.items())


@provider('information.countdowns', badge=True, state=True)
def Countdowns(context, unused_id):
    """Gold dot: something tracked by the countdown HUD is ready (a watched
    dungeon, or a tracked biolog research whose timer ran out); countdown: the
    nearest of them; gold rim while the HUD is shown."""
    interface_enabled = getattr(context.interface, 'IsCountdownCategoryEnabled', None)

    def enabled(category):
        try:
            return interface_enabled(category) if callable(interface_enabled) else True
        except Exception:
            return True

    ready = False
    candidates = []
    if enabled('dungeon'):
        rows = _DungeonRows(context, True)
        ready = any(status.get('state') == 'ready' for unused, unused_data, status in rows)
        countdown = _DungeonCountdown(rows)
        if countdown:
            candidates.append(countdown)
    window, rows = _BiologRows(context)
    model = context.module('biologresearchmodel')
    if window is not None and model is not None and enabled('biolog'):
        now = context.now()
        for unused_index, row in rows:
            if not row.get('alarm') or row.get('done'):
                continue
            if model.phase(row) != 'mission':
                continue
            remaining = _int(row.get('due')) - now
            if remaining <= 0:
                ready = True
            else:
                candidates.append((remaining, 0))
    hud = context.attr('wndCountdownHUD')
    shown = bool(hud is not None and _call(hud, 'IsShow'))
    countdown = min(candidates) if candidates else None
    if not ready and countdown is None and not shown:
        return None
    remaining, total = countdown if countdown else (None, None)
    return Decor(BADGE_INFO if ready else None, 0, STATE_ACTIVE if shown else None, remaining, total or remaining)


# Biolog and mission books ----------------------------------------------------------------
@provider('system.biolog', badge=True, state=True)
def Biolog(context, unused_id):
    """Ruby number: researches that can be handed in now (``wndBio.CanSubmit``:
    timer over and the item owned, a reward to choose, or the stone owned);
    countdown: the soonest research timer (``due``, server unix time). The
    snapshot arrives at login without opening the window."""
    window, rows = _BiologRows(context)
    if window is None:
        return None
    model = context.module('biologresearchmodel')
    ready = sum(1 for index, unused_row in rows if window.CanSubmit(index))
    now = context.now()
    dues = []
    if model is not None:
        for index, row in rows:
            if window.Available(index) and model.phase(row) == 'mission' and _int(row.get('due')) > now:
                dues.append(_int(row.get('due')) - now)
    remaining = min(dues) if dues else None
    if not ready and remaining is None:
        return None
    return Decor(BADGE_ACTION if ready else None, ready, None, remaining)


@provider('system.mission_books', badge=True)
def MissionBooks(context, unused_id):
    """Ruby dot: the finished mission's chest is waiting (``ready``: delivery
    failed, usually a full inventory; the quest retries). The state arrives by
    the quest at login and on progress (``MissionBookStateV1``)."""
    window = context.attr('wndMissionBooks')
    state = getattr(window, 'state', None) if window is not None else None
    if state is None or not getattr(state, 'ready', False):
        return None
    return Decor(BADGE_ACTION)


# Switchbot, pet, quick buffs ------------------------------------------------------------
@provider('system.switchbot', badge=True, state=True)
def Switchbot(context, unused_id):
    """Green rolling glow (like the Switchbot slot) while any slot runs; ruby
    dot when a slot finished (bonus found) and is not running again. The native cache is updated by the server
    push even while the window is closed (``switchbot.IsActive/IsFinished``)."""
    module = context.module('switchbot')
    if module is None:
        return None
    count = _int(getattr(module, 'SLOT_COUNT', 5), 5)
    running = any(module.IsActive(slot) for slot in range(count))
    finished = any(module.IsFinished(slot) and not module.IsActive(slot) for slot in range(count))
    if not running and not finished:
        return None
    return Decor(BADGE_ACTION if finished else None, 0, STATE_ROLLING if running else None)


PET_EVOLUTION_LEVELS = {1: 40, 2: 80, 3: 81}


def PetEvolutionReady(level, evolution, exp, next_exp, item_exp, item_max, skill_open_level=4):
    """``uipetinfo.PetEvolFlashEventCheck`` as a pure function."""
    if evolution == skill_open_level:
        return False
    required = PET_EVOLUTION_LEVELS.get(evolution, 0)
    if not required:
        return False
    if evolution < 3:
        return level == required and exp == next_exp and item_exp == item_max
    return level >= required


@provider('system.pet', badge=True, state=True)
def Pet(context, unused_id):
    """Gold rim while a growth pet is summoned (``player.GetActivePetItemId``);
    ruby dot when it must be fed (life under ``LIFE_TIME_FLASH_MIN_TIME``, one
    hour) or can evolve - the pet window's own flash rules."""
    player = context.module('player')
    if player is None or not callable(getattr(player, 'GetActivePetItemId', None)):
        return None
    pet_id = _int(player.GetActivePetItemId())
    if pet_id <= 0:
        return None
    action = False
    life = tuple(_call(player, 'GetPetLifeTime', pet_id) or ())
    if len(life) >= 1 and _int(life[0]) > 0:
        remaining = _int(life[0]) - context.now()
        if remaining < _int(getattr(player, 'LIFE_TIME_FLASH_MIN_TIME', 3600), 3600):
            action = True
    if not action:
        item = tuple(_call(player, 'GetPetItem', pet_id) or ())
        points = tuple(_call(player, 'GetPetExpPoints', pet_id) or ())
        if len(item) >= 2 and len(points) >= 4:
            values = [_int(value) & 0xFFFFFFFF for value in points[:4]]
            action = PetEvolutionReady(_int(item[0]), _int(item[1]), *values,
                                       skill_open_level=_int(getattr(player, 'PET_GROWTH_SKILL_OPEN_EVOL_LEVEL', 4), 4))
    return Decor(BADGE_ACTION if action else None, 0, STATE_ACTIVE)


@provider('system.quick_buffs', badge=True, state=True)
def QuickBuffs(context, unused_id):
    """Countdown: the soonest expiry of the configured buffs that are active;
    ruby dot: a configured buff is not active although its item is in the
    inventory (the same rule as a manual activation); running rim while the
    VIP automatic mode is on. Reads ``interface.quickBuffSystem`` only - never
    its ``Tick``/``QueueManual`` (they use items)."""
    system = context.attr('quickBuffSystem')
    model = getattr(system, 'model', None) if system is not None else None
    if model is None or getattr(system, 'affectShower', None) is None:
        return None
    vnums = tuple(model.ExecutionVnums() or ())
    if not vnums:
        return None
    scanner = getattr(system, 'scanner', None)
    policy = getattr(system, 'policy', None)
    remaining_list = []
    expired = False
    for vnum in vnums:
        remaining = _int(system._ActiveEffectRemaining(vnum))
        slot = scanner.Find(vnum) if scanner is not None else None
        if remaining > 0:
            total = 0
            if policy is not None and slot is not None:
                described = policy.Describe(vnum, slot) or {}
                total = _int(described.get('duration'))
            remaining_list.append((remaining, max(total, remaining)))
            continue
        if _BlendActive(context, scanner, vnum):
            continue
        if slot is not None and policy is not None and policy.Describe(vnum, slot) is not None:
            expired = True
    controller = getattr(system, 'controller', None)
    auto = bool(getattr(model, 'auto_enabled', False) and getattr(controller, 'vip_active', False))
    countdown = min(remaining_list) if remaining_list else None
    if not expired and countdown is None and not auto:
        return None
    remaining, total = countdown if countdown else (None, None)
    return Decor(BADGE_ACTION if expired else None, 0, STATE_RUNNING if auto else None, remaining, total)


def _BlendActive(context, scanner, vnum):
    player = context.module('player')
    if scanner is None or player is None or not callable(getattr(scanner, 'MatchingPositions', None)):
        return False
    for slot in scanner.MatchingPositions(vnum) or ():
        if _int(player.GetItemMetinSocket(slot, 3)):
            return True
    return False
