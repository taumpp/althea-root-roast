# -*- coding: utf-8 -*-
"""The rated arena (hodnocená aréna) in the R1 look, variant C "Přehled režimů" (owner's choice 9. 10. 2026, preview
round ui-navrhy-r1/kolo-20261009-arena; A and B stay previews only).

* ArenaWindow 520 x 353: the three modes stacked, each with its crest, rank, ELO, record, position and its own
  "Hledat"; placement matches as "4 / 10" with ten points; the tabs Žebříček (your row pinned at the bottom) and
  Historie (the date as "dnes 21:14", never the raw unix time) in the same width;
* ReadyDialog (dialog C, 360 px): Přijmout left, Odmítnout right, the 15 s countdown ring; "Zápas zrušen" when the
  offer ends without a match;
* MatchHud (300 x 44, top centre): your team always left (MatchState.team), the BO3 rounds as points;
* ResultDialog (NEW, dialog C 360 px): the ELO change and "Hrát znovu" (the queue in the same mode);
* RulesDialog (dialog C 340 px): label / value rows.

Tahoma 12 for every text, button and tab (PRAVIDLA-UI 9. 10.), the titles in the R1 title font like POSTAVA.
The packets are the ones of uipvpmatchmaking (net.SendPvPMatchmaking*), nothing new is sent.

Data the server does not send today (round NAVRHY.md, D1-D8) is not drawn at all - no placeholder, no sample
value. Each has a hook below (SHOW_D*): switch it on once the protocol carries the data.

Nothing shows while the server keeps the arena closed (ArenaShown: featureavailability.IsShown, the gate of
fix/arena-ui-hidden-when-off-20261009, or its parts on an older base). Settings -> "Starý vzhled" keeps the original
windows (uipvpmatchmaking.CreateWindow); a failure while building traces to syserr and keeps them too.
"""
import time

import app
import net
import player
import ui
import wndMgr

import guildarena
import pvpmatchmaking
import uir1
import uir1layout as L
import uir1tokens as T


# --------------------------------------------------------------------------- hooks for the data the server lacks
SHOW_D1_QUEUE_ESTIMATE = False      # QueueState.estimateSeconds is in the protocol, the server always sends 0
SHOW_D2_SEASON_REWARDS = False      # no season / rank rewards on the server (no table, no packet)
SHOW_D3_SEASON_PROGRESS = False     # the snapshot has only seasonEndsAt, no start or length
SHOW_D4_HISTORY_OPPONENTS = False   # HistoryRow has no opponent names (pvp_match_player has them)
SHOW_D5_MATCH_STATS = False         # kills / deaths / damage stay in pvp_match_player
SHOW_D6_HUD_ROSTER = False          # MatchState has no names or HP of the teams
SHOW_D7_LEADERBOARD_GUILD = False   # LeaderboardRow = position, pid, rating, wins, losses, name
SHOW_D8_QUEUE_POPULATION = False    # the number of searching players is not sent

# Leaderboard filters (variant B "Jeden řádek", owner 9. 10. 2026). The division filter works with today's protocol
# (the rating cursor); these need a server query first (arena-201/ZEBRICEK-FILTRY-SERVER.md, S1-S3): a filter over
# the pages the client happens to hold would show only the friends / members among the top 50, so they stay hidden.
SHOW_FRIENDS = False                # S2: ratings and positions of the friends list
SHOW_GUILD = False                  # S3: members of the player's guild
SHOW_SEARCH = False                 # S1: name search

ASSET = "d:/ymir work/ui/game/crimson_ember/pvp_matchmaking/"
ART = ASSET + "r1/"

W = 520
PLAY_H = 353
BOARD_H = 396
HISTORY_H = 371
PAD = 12
ROW_H = 58
ROW_GAP = 6
TABS_W = 336                        # Hrát, Žebříček, Historie, Cechy
MODE_SEG_W = 150
PAGE_ROWS = 10
LINE = 20

READY_W = 360
READY_H = 237
CANCEL_H = 149
RESULT_W = 360
RESULT_H = 191
RULES_W = 340
HUD_W, HUD_H, HUD_Y = 300, 44, 24
HUD_FILL_ALPHA = 0.86
RESULT_HUD_SECONDS = 5.0
READY_SECONDS = 15
PLACEMENT_MATCHES = 10              # common/pvp_matchmaking/rating.h kPlacementMatches
PENALTY_LADDER = (30, 120, 300, 900)

TAH = 'Tahoma:12'
TAHB = 'Tahoma:12b'

QUEUE_IDLE, QUEUE_SEARCHING, QUEUE_READY, QUEUE_MATCH, QUEUE_COOLDOWN = 0, 1, 2, 3, 4

# The rating window of the server's queue: +-75 ELO per
# player, +25 every 30 s of waiting, at most +-300. The client gets no packet with it; the footer only says that the
# range widens while the search takes longer (no number of its own).
RATING_WINDOW_STEP_SECONDS = 30
RATING_WINDOW_FULL_SECONDS = 270

# The result of the last match, kept across the interface rebuild of a warp: the server warps the players out of the
# arena map 5 s after the result (pvp_match_runtime.cpp kResultDisplayMs), which destroys the interface with the
# result window. The new window shows it again until the player closes it or plays again (owner test 9. 10.).
_RESULT = dict(pending=None, seen=0)


def PendingResult():
    return _RESULT['pending']


def _KeepResult(result, team, mode):
    _RESULT['seen'] = int(result[0])
    _RESULT['pending'] = dict(result=tuple(result), team=int(team), mode=int(mode))


def _DropResult():
    _RESULT['pending'] = None


def _Signed(color):
    """wndMgr takes a signed C int; a packed ARGB >= 0x80000000 would be ignored (PRAVIDLA-UI, Kód)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


IVORY = _Signed(T.IVORY)
INK = _Signed(T.INK)
INK_DIM = _Signed(T.INK_DIM)
MUTED = _Signed(T.MUTED)
DISABLED = _Signed(T.DISABLED)
RED_HI = _Signed(T.RED_HI)
WIN = _Signed(0xFF8AB98E)           # uitooltip POSITIVE_COLOR: a win / a gain
LOSS = _Signed(0xFFEC463C)          # a loss / a penalty: saturated blood red, never pink
TRACK = 0x080707
TRACK_EDGE = 0x343030
FILL = 0x5C0A0C
FILL_TOP = 0xD30D0E
GAIN = 0xC82822


# --------------------------------------------------------------------------- pure helpers (tested directly)
RANKS = ((2000, 'legenda', 'Legenda'), (1800, 'diamant', 'Diamant'), (1600, 'platina', 'Platina'),
         (1500, 'zlato', 'Zlato I'), (1350, 'zlato', 'Zlato II'), (1200, 'zlato', 'Zlato III'),
         (900, 'stribro', 'Stříbro'), (0, 'bronz', 'Bronz'))
NEXT = {0: 900, 900: 1200, 1200: 1350, 1350: 1500, 1500: 1600, 1600: 1800, 1800: 2000}
MODE_NAME = {1: '1v1', 2: '2v2', 3: '3v3'}
MODE_TITLE = {1: 'Hodnocený souboj', 2: 'Hodnocená dvojice', 3: 'Hodnocená trojice'}


# The "Zobrazit" divisions: (key, label, lower bound, upper bound exclusive or None).
DIVISIONS = (('legenda', 'Legenda', 2000, None), ('diamant', 'Diamant', 1800, 2000),
             ('platina', 'Platina', 1600, 1800), ('zlato', 'Zlato I–III', 1200, 1600),
             ('stribro', 'Stříbro', 900, 1200), ('bronz', 'Bronz', 0, 900))
# The leaderboard query returns rating < cursorRating OR (rating = cursorRating AND pid > cursorPid); the client
# binding takes a signed int pid, so the largest one stands for "every pid": the page starts at the best player
# under the bound, with the server's own position (#).
CURSOR_ALL_PIDS = 0x7FFFFFFF


def BoardFilters():
    """[(key, label)] of the "Zobrazit" menu: Všichni, the shown server filters, the divisions."""
    items = [('all', 'Všichni')]
    if SHOW_FRIENDS:
        items.append(('friends', 'Přátelé'))
    if SHOW_GUILD:
        items.append(('guild', 'Můj cech'))
    return items + [(key, label) for key, label, lo, hi in DIVISIONS]


def DivisionBounds(key):
    """(lower, upper) of a division (upper None = no limit); (None, None) for "Všichni"."""
    for name, label, lo, hi in DIVISIONS:
        if name == key:
            return lo, hi
    return None, None


def BoardStartCursor(key):
    """The (cursorRating, cursorPid) of the first page of a filter: (0, 0) = from the top."""
    lo, hi = DivisionBounds(key)
    if hi is None:
        return (0, 0)
    return (hi, CURSOR_ALL_PIDS)


def DivisionSlice(ratings, key):
    """(first, end) indexes of the rows of a page (sorted by rating, best first) inside the division."""
    lo, hi = DivisionBounds(key)
    first, end = 0, len(ratings)
    if hi is not None:
        while first < end and ratings[first] >= hi:
            first += 1
    if lo is not None:
        while end > first and ratings[end - 1] < lo:
            end -= 1
    return first, end


def Rank(rating):
    """dict(art, name, lo, hi, next): the thresholds of uipvpmatchmaking._Rank / server DisplayRankFor."""
    rating = int(rating)
    for lo, art, name in RANKS:
        if rating >= lo:
            hi = NEXT.get(lo)
            nxt = None
            if hi is not None:
                nxt = [n for l, a, n in RANKS if l == hi][0]
            return dict(art=art, name=name, lo=lo, hi=hi, next=nxt)


def Progress(rating):
    rank = Rank(rating)
    if rank['hi'] is None:
        return 1.0
    return max(0.0, min(1.0, float(int(rating) - rank['lo']) / (rank['hi'] - rank['lo'])))


def Number(value):
    """1437 -> "1 437"."""
    value = int(value)
    text = '{:,}'.format(abs(value)).replace(',', ' ')
    return ('-' if value < 0 else '') + text


def Clock(seconds):
    seconds = max(0, int(seconds))
    return '%d:%02d' % (seconds // 60, seconds % 60)


def Plural(count, one, few, many):
    count = abs(int(count))
    if count == 1:
        return one
    if 2 <= count <= 4:
        return few
    return many


def _Day(stamp, localtime):
    t = localtime(int(stamp))
    return (t.tm_year, t.tm_yday)


def FormatPlayedAt(stamp, now, localtime=time.localtime):
    """The history date: "dnes 21:14", "včera 22:07", "7. 10. 19:32" (another year: "7. 10. 2025"). The server sends
    UNIX_TIMESTAMP(completed_at); the old window printed that number (1791569640)."""
    stamp = int(stamp)
    if stamp <= 0:
        return '–'
    t = localtime(stamp)
    hm = '%d:%02d' % (t.tm_hour, t.tm_min)
    today = _Day(now, localtime)
    day = (t.tm_year, t.tm_yday)
    if day == today:
        return 'dnes ' + hm
    if day == _Day(int(now) - 86400, localtime):
        return 'včera ' + hm
    if t.tm_year == localtime(int(now)).tm_year:
        return '%d. %d. %s' % (t.tm_mday, t.tm_mon, hm)
    return '%d. %d. %d' % (t.tm_mday, t.tm_mon, t.tm_year)


def Ago(stamp, now):
    """"před 12 min" for the last match line."""
    stamp, now = int(stamp), int(now)
    if stamp <= 0:
        return ''
    seconds = max(0, now - stamp)
    if seconds < 60:
        return 'právě teď'
    if seconds < 3600:
        return 'před %d min' % (seconds // 60)
    if seconds < 86400:
        return 'před %d h' % (seconds // 3600)
    days = seconds // 86400
    return 'před %d %s' % (days, Plural(days, 'dnem', 'dny', 'dny'))


def SeasonText(season_id, ends_at, now, localtime=time.localtime):
    """("Sezóna 3", "končí za 23 dní (1. 11.)"); the second part is empty without an end time."""
    if not int(season_id):
        return ('Sezóna', '')
    title = 'Sezóna %d' % int(season_id)
    if not int(ends_at):
        return (title, '')
    days = max(0, (int(ends_at) - int(now)) // 86400)
    t = localtime(int(ends_at))
    if days == 0:
        left = 'končí dnes'
    else:
        left = 'končí za %d %s' % (days, Plural(days, 'den', 'dny', 'dní'))
    return (title, '%s (%d. %d.)' % (left, t.tm_mday, t.tm_mon))


def Outcome(outcome, delta, team=0):
    """(text, colour) of the player's result. outcome is per TEAM (1 = team O won, 2 = team X, 3 draw, 4 no
    contest); with the player's team known it decides, otherwise the sign of the rating change."""
    outcome, delta, team = int(outcome), int(delta), int(team)
    if outcome == 3:
        return ('Remíza', INK)
    if outcome == 4:
        return ('Bez výsledku', MUTED)
    if team in (1, 2) and outcome in (1, 2):
        return ('Výhra', WIN) if outcome == team else ('Prohra', LOSS)
    if delta > 0:
        return ('Výhra', WIN)
    if delta < 0:
        return ('Prohra', LOSS)
    return ('Zápas ukončen', MUTED)


def MyTeam(outcome, delta, team=0):
    """The player's team (1 = O, 2 = X) from the result when the match state did not tell it (0 = unknown)."""
    outcome, delta, team = int(outcome), int(delta), int(team)
    if team in (1, 2):
        return team
    if outcome in (1, 2) and delta:
        return outcome if delta > 0 else 3 - outcome
    return 0


def MyScore(outcome, delta, rounds_o, rounds_x, team=0):
    """(mine, theirs): the player's team first, like the HUD (your team always left)."""
    if MyTeam(outcome, delta, team) == 2:
        return int(rounds_x), int(rounds_o)
    return int(rounds_o), int(rounds_x)


def DaySummary(rows, now, localtime=time.localtime):
    """"Dnes: 2 výhry, 1 prohra · +28 ELO" from history rows (playedAt, outcome, delta); '' without a match today."""
    today = _Day(now, localtime)
    wins = losses = draws = total = 0
    for played_at, outcome, delta in rows:
        if int(played_at) <= 0 or _Day(played_at, localtime) != today:
            continue
        text = Outcome(outcome, delta)[0]
        if text == 'Výhra':
            wins += 1
        elif text == 'Prohra':
            losses += 1
        elif text == 'Remíza':
            draws += 1
        total += int(delta)
    parts = []
    if wins:
        parts.append('%d %s' % (wins, Plural(wins, 'výhra', 'výhry', 'výher')))
    if losses:
        parts.append('%d %s' % (losses, Plural(losses, 'prohra', 'prohry', 'proher')))
    if draws:
        parts.append('%d %s' % (draws, Plural(draws, 'remíza', 'remízy', 'remíz')))
    if not parts:
        return ''
    return 'Dnes: %s · %+d ELO' % (', '.join(parts), total)


def NextPenalty(current_seconds):
    """The next step of the penalty ladder after the current cooldown (None: the last step)."""
    current = int(current_seconds)
    for step in PENALTY_LADDER:
        if step > current:
            return step
    return None


def PenaltyText(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return '%d s' % seconds
    return '%d min' % (seconds // 60)


def ArenaShown():
    """Whether anything of the arena may show: the server announced it open and the core offers matchmaking
    (featureavailability.IsShown of the gate branch 4de477536; its two parts on a base without it)."""
    try:
        import featureavailability as fa
    except Exception:
        fa = None
    if fa is not None:
        shown = getattr(fa, 'IsShown', None)
        name = getattr(fa, 'RANKED_ARENA', 'ranked_arena')
        if shown is not None:
            try:
                return bool(shown(name))
            except Exception:
                return False
        try:
            if not fa.IsAvailable(name):
                return False
        except Exception:
            pass
    try:
        return bool(pvpmatchmaking.IsAvailable())
    except Exception:
        return False


def RankingsOpen():
    """rankings_open (FEATURE_PAUSE_SWITCH): False = "Žebříčky jsou dočasně vypnuté"."""
    try:
        import featureavailability as fa
        return bool(fa.IsAvailable(getattr(fa, 'RANKINGS', 'rankings')))
    except Exception:
        return True


def GuildArenaOpen():
    """Whether the tab Cechy is open: the server announced guild_arena AND ranked_arena open (FeatureAvailabilityV1,
    the server's feature pause switch; the server refuses /guild_arena queue | challenge | accept | meley while
    either is paused). Never read from content; a client or server that does not know the guild arena, or any
    failure, keeps the tab locked."""
    try:
        import featureavailability as fa
        name = getattr(fa, 'GUILD_ARENA', None)
        if not name:
            return False
        return bool(fa.IsAvailable(name)) and bool(fa.IsAvailable(getattr(fa, 'RANKED_ARENA', 'ranked_arena')))
    except Exception:
        return False


def _Now():
    try:
        return int(app.GetGlobalTimeStamp())
    except Exception:
        return int(time.time())


def _CommandPending():
    method = getattr(pvpmatchmaking, 'IsCommandPending', None)
    if not method:
        return False
    try:
        return bool(method())
    except Exception:
        return False


def ErrorText(error):
    code = int(error[0])
    if code == 8:
        return 'Trest fronty %s' % Clock(int(error[1]))
    return {1: 'Systém je vypnutý.', 2: 'Aréna teď není dostupná.', 3: 'Tohle teď nejde.',
            4: 'Postava nesplňuje podmínky.', 5: 'Frontu může spustit jen vůdce skupiny.',
            6: 'Skupina je pro tento režim příliš velká.', 7: 'Už jsi ve frontě.', 9: 'Tato akce už neplatí.',
            10: 'Něco se nepovedlo. Zkus to znovu.'}.get(code, '')


def _NotLeader():
    try:
        vid = player.GetMainCharacterIndex()
        return bool(player.IsPartyMember(vid)) and not bool(player.IsPartyLeader(vid))
    except Exception:
        return False


def _Stats(mode):
    """dict of pvpmatchmaking.GetModeStats(mode)."""
    values = tuple(pvpmatchmaking.GetModeStats(mode))
    keys = ('mode', 'rating', 'best', 'wins', 'losses', 'draws', 'streak', 'played', 'position', 'placement')
    return dict(zip(keys, [int(v) for v in values]))


class TahomaKit(uir1.Kit):
    """Tahoma 12 for every text, button and tab (PRAVIDLA-UI "Písmo textu", 9. 10. 2026); the window title stays the
    R1 title (Cinzel capitals, like the POSTAVA window)."""

    def font(self, role='text'):
        return uir1.Kit.font(self, 'title' if role == 'title' else 'tahoma')


# --------------------------------------------------------------------------- small widgets
def _Text(parent, x, y, color=INK, font=TAH, align='left', outline=False):
    return uir1.Text(parent, '', x, y, font, color, align=align, valign='top', outline=outline)


def _Set(line, text, color=None):
    """Text and colour only when they change (no re-layout per refresh)."""
    state = (text, color)
    if getattr(line, 'arenaState', None) == state:
        return
    old = getattr(line, 'arenaState', None)
    if old is None or old[0] != text:
        line.SetText(text)
    if color is not None and (old is None or old[1] != color):
        line.SetPackedFontColor(color)
    line.arenaState = state


def _Visible(widget, visible):
    if visible:
        if not widget.IsShow():
            widget.Show()
    elif widget.IsShow():
        widget.Hide()


def _Image(parent, path, x, y):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(path)
    image.SetPosition(int(x), int(y))
    image.arenaPath = path
    image.Show()
    return image


def _Load(image, path):
    if getattr(image, 'arenaPath', None) != path:
        image.LoadImage(path)
        image.arenaPath = path


def _Button(button, text, enabled):
    state = (text, bool(enabled))
    if getattr(button, 'arenaState', None) == state:
        return
    if button.GetText() != text:
        button.SetText(text)
    if enabled:
        button.Enable()
    else:
        button.Disable()
    button.arenaState = state


class _Page(ui.Window):
    """A not-pickable container: its controls take the clicks, the empty area drags the window."""

    def __init__(self, parent, y, h):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(0, int(y))
        self.SetSize(W, int(h))
        self.Show()


class Link(uir1.Interactive):
    """A text link (Pravidla a tresty): dim, lighter under the mouse."""

    def __init__(self, parent, x, y, text, event, align='right'):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.label = _Text(self, 0, 0, INK_DIM)
        self.label.SetText(text)
        w = uir1.TextWidth(self.label)
        self.SetSize(w, 14)
        self.SetPosition(int(x) - (w if align == 'right' else 0), int(y))
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        _Set(self.label, self.label.GetText(), INK if self.hovered else INK_DIM)


class Track(object):
    """A progress track of plain bars (nothing stretched): dark well, a hairline, the blood red fill with a brighter
    top line and an optional highlighted gain."""

    def __init__(self, parent, x, y, w, h=5):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.edge = uir1.Rect(parent, x, y, w, h, TRACK_EDGE)
        self.well = uir1.Rect(parent, x + 1, y + 1, w - 2, h - 2, TRACK)
        self.fill = uir1.Rect(parent, x + 1, y + 1, 1, h - 2, FILL)
        self.top = uir1.Rect(parent, x + 1, y + 1, 1, 1, FILL_TOP)
        self.gain = uir1.Rect(parent, x + 1, y + 1, 1, h - 2, GAIN)
        self.state = None
        self.Set(0.0)

    def Set(self, fraction, gain=None):
        inner = self.w - 2
        width = int(round(inner * max(0.0, min(1.0, float(fraction)))))
        span = None
        if gain:
            a, b = [int(round(inner * max(0.0, min(1.0, float(v))))) for v in gain]
            if b > a:
                span = (a, b - a)
        state = (width, span)
        if state == self.state:
            return
        self.state = state
        for bar in (self.fill, self.top):
            if width > 0:
                bar.SetSize(width, bar.GetHeight())
                bar.Show()
            else:
                bar.Hide()
        if span:
            self.gain.SetPosition(self.x + 1 + span[0], self.y + 1)
            self.gain.SetSize(span[1], self.h - 2)
            self.gain.Show()
        else:
            self.gain.Hide()

    def Show(self):
        for bar in (self.edge, self.well):
            bar.Show()
        state, self.state = self.state, None
        self.Set(*([0.0] if state is None else [float(state[0]) / max(1, self.w - 2)]))

    def Hide(self):
        for bar in (self.edge, self.well, self.fill, self.top, self.gain):
            bar.Hide()


class Pips(object):
    """N round points (placement matches, BO3 rounds): the first ``count`` red, the rest dark."""

    def __init__(self, parent, x, y, total, size, gap):
        self.size = int(size)
        self.images = [_Image(parent, ART + 'pip_off_%d.png' % self.size, int(x) + i * (size + gap) - 4, int(y) - 4)
                       for i in range(int(total))]
        self.count = None
        self.Set(0)

    def Set(self, count):
        count = max(0, int(count))
        if count == self.count:
            return
        self.count = count
        for index, image in enumerate(self.images):
            _Load(image, ART + ('pip_on_%d.png' if index < count else 'pip_off_%d.png') % self.size)

    def Show(self):
        for image in self.images:
            image.Show()

    def Hide(self):
        for image in self.images:
            image.Hide()


class Dots(object):
    """The three small dots "…" of a waiting state (2 x 2 px bars); Step() moves the bright one."""

    def __init__(self, parent, x, y, color=0xF42922):
        self.color = color
        self.bars = [uir1.Rect(parent, int(x) + i * 4, int(y), 2, 2, color) for i in range(3)]
        self.lit = None

    def Step(self, now):
        lit = int(now / 0.4) % 3
        if lit == self.lit:
            return
        self.lit = lit
        for index, bar in enumerate(self.bars):
            bar.SetColor(uir1.GenerateColor(self.color, 1.0 if index == lit else 0.45))

    def Place(self, x, y):
        for index, bar in enumerate(self.bars):
            bar.SetPosition(int(x) + index * 4, int(y))

    def Show(self):
        for bar in self.bars:
            bar.Show()

    def Hide(self):
        for bar in self.bars:
            bar.Hide()


# --------------------------------------------------------------------------- main window: one mode row
class ModeRow(ui.Window):
    """One mode of variant C: crest 48, "2v2 Hodnocená dvojice", the rank + ELO + track + "63 do Zlato I" (or the
    placement matches 4 / 10 with ten points), V / P and Pořadí (or the search time) and the row's own button."""

    def __init__(self, window, parent, kit, mode, x, y, w):
        ui.Window.__init__(self)
        self.window, self.mode = window, int(mode)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), ROW_H)
        self.w = int(w)
        self.frame = uir1.Frame(self, 0, 0, w, ROW_H, 'panel')
        self.band = uir1.Band(self, 2, 2, w - 4, ROW_H - 4, 'normal')
        self.crest = _Image(self, ART + 'rank_placement_48.png', 8, (ROW_H - 48) // 2)
        lx = 64
        self.modeName = _Text(self, lx, 9, IVORY, TAHB)
        self.modeName.SetText(MODE_NAME[self.mode])
        self.modeTitle = _Text(self, lx + uir1.TextWidth(self.modeName) + 6, 9, INK_DIM)
        self.modeTitle.SetText(MODE_TITLE[self.mode])
        self.rankName = _Text(self, lx, 26, IVORY)
        self.rating = _Text(self, lx + 74, 26, INK)
        self.track = Track(self, lx, 43, 120, 5)
        self.toNext = _Text(self, lx + 128, 39, MUTED)
        self.placementTitle = _Text(self, lx, 26, INK)
        self.placementTitle.SetText('Umísťovací zápasy')
        self.placementNote = _Text(self, lx, 40, MUTED)
        self.pips = Pips(self, lx + 128, 30, PLACEMENT_MATCHES, 6, 3)
        rx = w - 112 - 104
        self.rx = rx
        self.recordLabel = _Text(self, rx, 13, MUTED)
        self.recordLabel.SetText('V / P')
        self.record = _Text(self, rx + 96, 13, INK, align='right')
        self.positionLabel = _Text(self, rx, 29, MUTED)
        self.positionLabel.SetText('Pořadí')
        self.position = _Text(self, rx + 96, 29, INK, align='right')
        self.searchTitle = _Text(self, rx, 13, IVORY)
        self.searchTitle.SetText('Hledání soupeře')
        self.searchDots = Dots(self, rx + uir1.TextWidth(self.searchTitle) + 3, 22)
        self.searchTime = _Text(self, rx, 29, INK)
        self.estimate = _Text(self, rx + 30, 29, MUTED)          # D1 hook
        self.button = uir1.Button(self, kit, w - 104, (ROW_H - T.BTN_H) // 2, 94, 'Hledat', primary=True,
                                  event=self.Click)
        self.key = None
        self.search = False
        self.hover = None
        self.Show()

    def SyncHover(self):
        """The row lights up while the mouse is over its enabled button (checked every frame, no window made)."""
        hover = bool(self.search or (self.button.hovered and self.button.IsEnabled()))
        if hover != self.hover:
            self.hover = hover
            self.band.SetState('hover' if hover else 'normal')

    def Click(self):
        self.window.ToggleQueue(self.mode)

    def Apply(self, state):
        """state: dict(stats, loaded, search, elapsed, estimate, button, enabled, primary)."""
        key = repr(sorted(state.items()))
        if key == self.key:
            return
        self.key = key
        stats = state['stats']
        placing = state['loaded'] and stats['placement'] < PLACEMENT_MATCHES
        searching = self.search = state['search']
        rank = Rank(stats['rating'])
        _Load(self.crest, ART + ('rank_placement_48.png' if placing or not state['loaded'] else
                                 'rank_%s_48.png' % rank['art']))
        ranked = state['loaded'] and not placing
        for widget in (self.rankName, self.rating, self.toNext):
            _Visible(widget, ranked)
        if ranked:
            self.track.Show()
            self.track.Set(Progress(stats['rating']))
            _Set(self.rankName, rank['name'], IVORY)
            _Set(self.rating, '%s ELO' % Number(stats['rating']), INK)
            if rank['hi'] is not None:
                _Set(self.toNext, '%d do %s' % (rank['hi'] - stats['rating'], rank['next']), MUTED)
            else:
                _Set(self.toNext, 'Nejvyšší rank', MUTED)
        else:
            self.track.Hide()
        _Visible(self.placementTitle, placing or not state['loaded'])
        _Visible(self.placementNote, placing)
        if placing:
            _Set(self.placementTitle, 'Umísťovací zápasy', INK)
            self.pips.Show()
            self.pips.Set(stats['placement'])
            _Set(self.placementNote, '%d / %d, pak dostaneš rank' % (stats['placement'], PLACEMENT_MATCHES), MUTED)
        else:
            self.pips.Hide()
            if not state['loaded']:
                _Set(self.placementTitle, 'Načítá se…', MUTED)
        for widget in (self.recordLabel, self.record, self.positionLabel, self.position):
            _Visible(widget, not searching)
        for widget in (self.searchTitle, self.searchTime):
            _Visible(widget, searching)
        if searching:
            self.searchDots.Show()
            _Set(self.searchTime, Clock(state['elapsed']), INK)
            estimate = SHOW_D1_QUEUE_ESTIMATE and state['estimate'] > 0
            _Visible(self.estimate, estimate)
            if estimate:
                _Set(self.estimate, 'odhad ~%d min' % max(1, (state['estimate'] + 59) // 60), MUTED)
        else:
            self.searchDots.Hide()
            _Visible(self.estimate, False)
            _Set(self.record, '%d / %d' % (stats['wins'], stats['losses']) if state['loaded'] else '–', INK)
            _Set(self.position, '#%d' % stats['position'] if stats['position'] else '–', INK)
        self.button.SetPrimary(state['primary'])
        _Button(self.button, state['button'], state['enabled'])
        self.SyncHover()


# --------------------------------------------------------------------------- main window pages
class PlayPage(_Page):
    def __init__(self, window, kit, y):
        _Page.__init__(self, window, y, PLAY_H - y)
        self.window = window
        top = 69 - y
        self.seasonTitle = _Text(self, PAD, top, IVORY, TAHB)
        self.seasonEnds = _Text(self, PAD + 62, top, INK_DIM)
        self.rules = Link(self, W - PAD, top, 'Pravidla a tresty', window.OpenRules)
        self.seasonTrack = Track(self, PAD, top + 18, W - 2 * PAD, 4)       # D3 hook
        self.seasonTrack.Hide()
        self.rows = {}
        ry = 99 - y
        for mode in (1, 2, 3):
            self.rows[mode] = ModeRow(window, self, kit, mode, 8, ry, W - 16)
            ry += ROW_H + ROW_GAP
        ry += 4
        self.divider = uir1.Divider(self, PAD, ry, W - 2 * PAD)
        ry += 8
        self.lastLabel = _Text(self, PAD, ry, MUTED)
        self.lastLabel.SetText('Poslední zápas')
        self.lastOutcome = _Text(self, PAD + 96, ry, WIN)
        self.lastScore = _Text(self, PAD + 96, ry, INK)
        self.lastDelta = _Text(self, PAD + 96, ry, WIN)
        self.lastWhen = _Text(self, W - PAD, ry, MUTED, align='right')
        self.lastNone = _Text(self, PAD + 96, ry, MUTED)
        self.lastNone.SetText('Zatím žádný hodnocený zápas')
        ry += 20
        self.message = _Text(self, PAD, ry, LOSS)            # status / error; the D2 reward line stays hidden
        self.footerY = ry

    def SetLast(self, last):
        """last: None or dict(outcome text, colour, score, mode, delta, when)."""
        shown = last is not None
        for widget in (self.lastOutcome, self.lastScore, self.lastDelta, self.lastWhen):
            _Visible(widget, shown)
        _Visible(self.lastNone, not shown)
        if not shown:
            return
        x = PAD + 96
        _Set(self.lastOutcome, last['text'], last['color'])
        x += uir1.TextWidth(self.lastOutcome) + 6
        self.lastScore.SetPosition(x, self.lastOutcome.GetLocalPosition()[1])
        score = '%d : %d  ·  %s  ·' % (last['score'][0], last['score'][1], MODE_NAME.get(last['mode'], '')) \
            if last['mode'] in MODE_NAME else '%d : %d  ·' % last['score']
        _Set(self.lastScore, score, INK)
        x += uir1.TextWidth(self.lastScore) + 6
        self.lastDelta.SetPosition(x, self.lastOutcome.GetLocalPosition()[1])
        delta = last['delta']
        _Set(self.lastDelta, '%+d ELO' % delta, WIN if delta > 0 else (LOSS if delta < 0 else INK_DIM))
        _Set(self.lastWhen, last['when'], MUTED)


class BoardRow(object):
    """One leaderboard row: #, crest 18 + rank, player, ELO, V – P, success rate (the guild column is D7)."""

    def __init__(self, parent, x, y, w, pinned=False):
        self.y = int(y)
        h = 22 if pinned else LINE
        self.shade = None if pinned else uir1.Rect(parent, x + 4, y, w - 8, h, 0xFFFFFF, 6 / 255.0)
        self.band = uir1.Band(parent, x + 3, y + 1, w - 6, h - 2, 'hover') if pinned else None
        ty = y + uir1.CellTop(h, TAH)
        self.pos = _Text(parent, x + 26, ty, INK_DIM, align='center')
        self.crest = _Image(parent, ART + 'rank_bronz_18.png', x + 52, y + (h - 18) // 2)
        self.rank = _Text(parent, x + 74, ty, INK_DIM)
        self.name = _Text(parent, x + 170, ty, INK)
        self.elo = _Text(parent, x + 330, ty, IVORY, align='right')
        self.record = _Text(parent, x + 410, ty, INK, align='right')
        self.rate = _Text(parent, x + w - 12, ty, INK_DIM, align='right')
        self.widgets = [w_ for w_ in (self.shade, self.pos, self.crest, self.rank, self.name, self.elo, self.record,
                                      self.rate) if w_ is not None]
        self.shown = None

    def Set(self, row, mine=False):
        """row: (position, rating, wins, losses, name) or None (hidden)."""
        shown = row is not None
        if shown != self.shown:
            self.shown = shown
            for widget in self.widgets:
                widget.Show() if shown else widget.Hide()
            if self.band is not None:
                self.band.SetState('hover' if shown else 'normal')
        if not shown:
            return
        position, rating, wins, losses, name = row
        top = 0 < int(position) <= 3
        _Set(self.pos, str(position) if int(position) else '–', IVORY if top or mine else INK_DIM)
        if getattr(self.pos, 'arenaFont', TAH) != (TAHB if top else TAH):
            uir1.SetFont(self.pos, TAHB if top else TAH)
            self.pos.arenaFont = TAHB if top else TAH
        rank = Rank(rating)
        _Load(self.crest, ART + 'rank_%s_18.png' % rank['art'])
        _Set(self.rank, rank['name'], INK_DIM)
        _Set(self.name, name, IVORY if mine else INK)
        _Set(self.elo, Number(rating), IVORY)
        _Set(self.record, '%d – %d' % (int(wins), int(losses)), INK)
        played = int(wins) + int(losses)
        _Set(self.rate, '%d %%' % int(round(int(wins) * 100.0 / played)) if played else '–', INK_DIM)

    def Hide(self):
        self.shown = None
        self.Set(None)


class MenuRow(uir1.Interactive):
    def __init__(self, menu, parent, x, y, w, key, label):
        uir1.Interactive.__init__(self)
        self.menu, self.key = menu, key
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), LINE)
        self.fill = uir1.Rect(self, 0, 0, w, LINE, T.BAND_HOVER, T.BAND_ALPHA['hover'])
        self.fill.Hide()
        self.label = _Text(self, 8, uir1.CellTop(LINE, TAH), INK)
        self.label.SetText(label)
        self.callback = self.Pick
        self.Show()

    def paint(self):
        _Visible(self.fill, self.hovered or self.key == self.menu.value)
        _Set(self.label, self.label.GetText(), IVORY if self.key == self.menu.value else INK)

    def Pick(self):
        self.menu.Choose(self.key)


class Dropdown(uir1.Interactive):
    """"Zobrazit: Všichni ▾": the R1 field well with the down chevron; the menu opens under it on the R1 tooltip frame
    (94 %, the menus of PRAVIDLA-UI), one row per filter, the chosen one lit."""

    MENU_FILL = 0.94

    def __init__(self, parent, menu_parent, kit, x, y, w, items, event):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.w = int(w)
        self.SetSize(self.w, T.FIELD_H)
        self.ops = uir1.Ops(self, L.field('normal', self.w))     # the well before the label and the chevron
        self.label = _Text(self, 8, uir1.CellTop(T.FIELD_H, TAH), INK)
        self.chevron = uir1.Image(self, uir1.ChevronPath('down'), self.w - 18, (T.FIELD_H - T.CHEVRON) // 2)
        self.items = list(items)
        self.event = event
        self.value = self.items[0][0]
        self.callback = self.Toggle
        h = 8 + len(self.items) * LINE
        self.popup = ui.Window()
        self.popup.SetParent(menu_parent)
        self.popup.AddFlag('float')          # SetTop brings it above the pages made after it
        self.popup.SetSize(self.w, h)
        self.frame = uir1.Frame(self.popup, 0, 0, self.w, h, 'tooltip')
        if self.frame.fill is not None:
            self.frame.fill.SetColor(uir1.GenerateColor(0x0C0B0C, self.MENU_FILL))
        self.rows = [MenuRow(self, self.popup, 2, 4 + i * LINE, self.w - 4, key, label)
                     for i, (key, label) in enumerate(self.items)]
        self.popup.Hide()
        self.SetValue(self.value)
        self.paint()
        self.Show()

    def paint(self):
        self.ops.Apply(L.field('hover' if self.hovered else 'normal', self.w))

    def Label(self, key):
        for name, label in self.items:
            if name == key:
                return label
        return ''

    def SetValue(self, key):
        self.value = key
        _Set(self.label, 'Zobrazit: %s' % self.Label(key), INK)
        for row in self.rows:
            row.paint()

    def IsOpen(self):
        return self.popup.IsShow()

    def Toggle(self):
        if self.popup.IsShow():
            self.CloseMenu()
            return
        x, y = self.GetLocalPosition()
        px, py = self.GetParentPosition()
        self.popup.SetPosition(px + x, py + y + T.FIELD_H + 1)
        self.popup.Show()
        self.popup.SetTop()

    def GetParentPosition(self):
        """The dropdown's parent page inside the window that holds the menu."""
        parent = self.parentPage
        return parent.GetLocalPosition() if parent is not None else (0, 0)

    def CloseMenu(self):
        self.popup.Hide()

    def Choose(self, key):
        self.CloseMenu()
        if key != self.value:
            self.SetValue(key)
            if self.event:
                self.event(key)


class BoardPage(_Page):
    """Žebříček: the mode switch and the season, 10 rows, your row pinned at the bottom (ModeStats), paging by the
    server cursor; "Žebříčky jsou dočasně vypnuté" while rankings_open = 0."""

    def __init__(self, window, kit, y):
        _Page.__init__(self, window, y, BOARD_H - y)
        self.window = window
        top = 69 - y
        self.modes = uir1.Segment(self, kit, [(1, '1v1'), (2, '2v2'), (3, '3v3')], window.SelectMode,
                                  width=MODE_SEG_W)
        self.modes.SetPosition(PAD, top)
        # One row (variant B): the mode, "Zobrazit" (Všichni / divisions; Přátelé, Můj cech behind SHOW_*), the search
        # (SHOW_SEARCH) or, while it is hidden, the season.
        self.filter = Dropdown(self, window, kit, PAD + MODE_SEG_W + 8, top, 150, BoardFilters(),
                               window.SelectBoardFilter)
        self.filter.parentPage = self
        self.search = None
        if SHOW_SEARCH:
            self.search = uir1.SearchField(self, kit, W - PAD - 170, top, 170, 'Hledat hráče…')
        self.season = _Text(self, W - PAD, top + uir1.CellTop(T.SEG_H, TAH), INK_DIM, align='right')
        if self.search is not None:
            self.season.Hide()
        ty = top + T.SEG_H + 8
        tx, tw = 8, W - 16
        self.panel = uir1.Frame(self, tx, ty, tw, 20 + PAGE_ROWS * LINE + 4 + 24 + 4, 'panel')
        self.heads = []
        for cx, text, align in ((tx + 26, '#', 'center'), (tx + 52, 'Rank', 'left'), (tx + 170, 'Hráč', 'left'),
                                (tx + 330, 'ELO', 'right'), (tx + 410, 'V – P', 'right'),
                                (tx + tw - 12, 'Úspěšnost', 'right')):
            head = _Text(self, cx, ty + uir1.CellTop(18, TAH) + 2, MUTED, align=align)
            head.SetText(text)
            self.heads.append(head)
        self.ruleTop = uir1.Divider(self, tx + 8, ty + 19, tw - 16)
        ry = ty + 22
        self.rows = [BoardRow(self, tx, ry + i * LINE, tw) for i in range(PAGE_ROWS)]
        ry += PAGE_ROWS * LINE + 4
        self.ruleBottom = uir1.Divider(self, tx + 8, ry - 3, tw - 16)
        self.mine = BoardRow(self, tx, ry, tw, pinned=True)
        self.message = _Text(self, W // 2, ty + 22 + 70, INK_DIM, align='center')
        self.message2 = _Text(self, W // 2, ty + 22 + 90, MUTED, align='center')
        by = ty + 20 + PAGE_ROWS * LINE + 4 + 24 + 4 + 8
        self.prev = uir1.Button(self, kit, PAD, by, 96, '‹ Předchozí', event=window.BoardPrev)
        self.pageText = _Text(self, W // 2, by + uir1.CellTop(T.BTN_H, TAH), MUTED, align='center')
        self.next = uir1.Button(self, kit, W - PAD - 96, by, 96, 'Další ›', event=window.BoardNext)


class HistoryRow(object):
    def __init__(self, parent, x, y, w):
        self.shade = uir1.Rect(parent, x + 4, y, w - 8, LINE, 0xFFFFFF, 6 / 255.0)
        ty = y + uir1.CellTop(LINE, TAH)
        self.when = _Text(parent, x + 10, ty, INK_DIM)
        self.outcome = _Text(parent, x + 110, ty, INK)
        self.score = _Text(parent, x + 230, ty, INK, align='center')
        self.elo = _Text(parent, x + 400, ty, INK, align='right')
        self.delta = _Text(parent, x + w - 10, ty, INK_DIM, align='right')
        self.widgets = (self.shade, self.when, self.outcome, self.score, self.elo, self.delta)
        self.shown = None

    def Set(self, row, now, shade=False):
        """row: (matchId, playedAt, outcome, roundsO, roundsX, before, after, delta) or None."""
        shown = row is not None
        if shown != self.shown:
            self.shown = shown
            for widget in self.widgets[1:]:
                widget.Show() if shown else widget.Hide()
        _Visible(self.shade, shown and shade)
        if not shown:
            return
        unused, played_at, outcome, rounds_o, rounds_x, before, after, delta = [int(v) for v in row]
        text, color = Outcome(outcome, delta)
        _Set(self.when, FormatPlayedAt(played_at, now), INK_DIM)
        _Set(self.outcome, text, color)
        _Set(self.score, '%d : %d' % MyScore(outcome, delta, rounds_o, rounds_x), INK)
        _Set(self.elo, '%s › %s' % (Number(before), Number(after)), INK)
        _Set(self.delta, '%+d' % delta if delta else '0', WIN if delta > 0 else (LOSS if delta < 0 else INK_DIM))


class HistoryPage(_Page):
    def __init__(self, window, kit, y):
        _Page.__init__(self, window, y, HISTORY_H - y)
        self.window = window
        top = 69 - y
        self.modes = uir1.Segment(self, kit, [(1, '1v1'), (2, '2v2'), (3, '3v3')], window.SelectMode,
                                  width=MODE_SEG_W)
        self.modes.SetPosition(PAD, top)
        self.summary = _Text(self, W - PAD, top + uir1.CellTop(T.SEG_H, TAH), INK_DIM, align='right')
        ty = top + T.SEG_H + 8
        tx, tw = 8, W - 16
        self.panel = uir1.Frame(self, tx, ty, tw, 20 + PAGE_ROWS * LINE + 4, 'panel')
        self.heads = []                   # kept: a text line nobody references is destroyed (ui.Window.__del__)
        for cx, text, align in ((tx + 10, 'Kdy', 'left'), (tx + 110, 'Výsledek', 'left'),
                                (tx + 230, 'Skóre', 'center'), (tx + 400, 'ELO', 'right'),
                                (tx + tw - 10, 'Změna', 'right')):
            head = _Text(self, cx, ty + uir1.CellTop(18, TAH) + 2, MUTED, align=align)
            head.SetText(text)
            self.heads.append(head)
        self.rule = uir1.Divider(self, tx + 8, ty + 19, tw - 16)
        self.rows = [HistoryRow(self, tx, ty + 22 + i * LINE, tw) for i in range(PAGE_ROWS)]
        self.message = _Text(self, W // 2, ty + 22 + 80, INK_DIM, align='center')
        by = ty + 20 + PAGE_ROWS * LINE + 4 + 8
        self.older = uir1.Button(self, kit, (W - 150) // 2, by, 150, 'Načíst starší', event=window.HistoryOlder)


# --------------------------------------------------------------------------- the main window
# --------------------------------------------------------------------------- tab Cechy (guild wars and the guild arena)
# Owner 12. 10. (V10): clean cards like the guild catalogue K2. One line about the guild, an alert card only while
# something needs an answer or runs, two cards side by side (Výzva = a chosen guild, Aréna = the server finds one),
# Meley underneath, the Válečníci of the guild in a small dialog of the leader.
GUILD_H = 364
GUILD_ALERT_H = 46
CARD_W = (W - 24) // 2              # 248
CARD_H = 152
CARD_PAD = 10
ALERT_OK = WIN


def GuildSummary(data, name):
    """("Krvaví vlci", "úroveň 4 · 18 členů · 7 online", "3 / 0 / 1")."""
    members = int(data['members'])
    info = 'úroveň %d · %d %s · %d online' % (
        int(data['level']), members, Plural(members, 'člen', 'členové', 'členů'), int(data['online']))
    record = '%d / %d / %d' % (int(data['win']), int(data['draw']), int(data['loss']))
    return (name or 'Můj cech', info, record)


def GuildQueueButton(mode, data):
    """(text, enabled, primary, searching) of the Aréna card for the selected mode."""
    queueMode, warState = int(data['queueMode']), int(data['warState'])
    lead = bool(int(data['lead']))
    if queueMode:
        return ('Zrušit hledání', lead, False, True)
    enabled = lead and warState == guildarena.WAR_NONE
    return ('Hledat soupeře', enabled, True, False)


def MeleyChecks(data):
    """[(text, ok)] of the Meley card: level, members near, this week's attempt."""
    level, need = int(data['meleyLevel']), int(data['nearNeed'])
    return [('úroveň %d' % level, int(data['level']) >= level),
            ('u tebe %d / %d' % (int(data['near']), need), int(data['near']) >= need),
            ('tento týden volno' if int(data['meleyFree']) else 'tento týden hotovo', bool(int(data['meleyFree'])))]


def _CardTitle(kit, parent, x, y, text):
    title = uir1.Text(parent, text, x, y, uir1.Kit.font(kit, 'button_s'), IVORY, align='left', valign='top')
    return title


# A locked feature (the convention of the guild window, root/uiguildv2widgets.py LOCK / LOCKED_HINT / locked_panel):
# dimmed, the padlock of the guild window and the hint "Připravujeme".
LOCK_ART = 'd:/ymir work/ui/public/althea_r1_cech/'
LOCKED_HINT = 'Připravujeme'
LOCKED_TEXT = 'Války cechů, aréna cechů a přihlášení do Meley se tu otevřou později.'
LOCK_W, LOCK_H = 12, 14
# The picture under the text of the locked page (owner 13. 10. 2026, CECH-ARENA-OBRAZEK = B: guilds at the arena
# gates): a pack file with its darkening baked in, inside the 2 px border of the panel. Another picture = another file.
GUILD_TEASER = ART + 'guild_teaser.png'
GUILD_TEASER_INSET = 2


class LockableTabCell(uir1.SegmentCell):
    """The cell Cechy of the tab row. Locked: the label dimmed, the padlock right of it, "Připravujeme" as its hint;
    it stays selectable and opens the locked page. ArenaWindow turns the cell into this class after the row is
    built (uir1.Segment makes plain cells)."""

    def InitLock(self):
        self.locked = False
        self.lock = _Image(self, LOCK_ART + 'lock_normal.png', 0, (T.SEG_H - LOCK_H) // 2)
        self.lock.Hide()

    def SetLocked(self, locked):
        locked = bool(locked)
        if locked == self.locked:
            return
        self.locked = locked
        if not locked and self.hovered:
            uir1.HideHint(self)
        self.paint()

    def paint(self):
        uir1.SegmentCell.paint(self)
        lock = getattr(self, 'lock', None)
        if lock is None or not self.w:
            return
        if not self.locked:
            self.label.SetPosition(self.w // 2, self.label.GetLocalPosition()[1])
            _Visible(lock, False)
            return
        # label and padlock centred together (a 5 px gap), the label dimmed unless the cell is the shown tab
        width = uir1.TextWidth(self.label) + 5 + LOCK_W
        left = (self.w - width) // 2
        self.label.SetPosition(left + uir1.TextWidth(self.label) // 2, self.label.GetLocalPosition()[1])
        if not self.selected:
            self.label.SetPackedFontColor(DISABLED)
        lock.SetPosition(left + width - LOCK_W, (T.SEG_H - LOCK_H) // 2)
        _Load(lock, LOCK_ART + ('lock_hover.png' if self.hovered else 'lock_normal.png'))
        _Visible(lock, True)

    def OnMouseOverIn(self):
        uir1.SegmentCell.OnMouseOverIn(self)
        if self.locked:
            uir1.ShowHint(self.segment.kit, self, LOCKED_HINT)

    def OnMouseOverOut(self):
        uir1.SegmentCell.OnMouseOverOut(self)
        uir1.HideHint(self)


class GuildLocked(ui.Window):
    """The page Cechy while the server keeps the guild arena closed: one panel with its title, the padlock,
    "Připravujeme" and one muted line over a darkened picture of what comes (GUILD_TEASER) - no cards, no buttons."""

    def __init__(self, page, kit, y, h):
        ui.Window.__init__(self)
        self.SetParent(page)
        self.AddFlag('not_pick')
        self.SetPosition(8, int(y))
        w = W - 16
        self.SetSize(w, int(h))
        self.frame = uir1.Frame(self, 0, 0, w, h, 'panel')
        self.teaser = _Image(self, GUILD_TEASER, GUILD_TEASER_INSET, GUILD_TEASER_INSET)   # made first: under the text
        self.title = _CardTitle(kit, self, 16, 12, 'Cechy')
        self.lock = _Image(self, LOCK_ART + 'lock_normal.png', w - 30, 14)
        self.hint = _Text(self, 16, 42, DISABLED, TAHB)
        self.hint.SetText(LOCKED_HINT)
        self.text = _Text(self, 16, 66, MUTED)
        self.text.SetText(LOCKED_TEXT)
        self.Hide()


class _Card(ui.Window):
    """A panel card: frame, a Cinzel title with a small crest, a muted line under it."""

    def __init__(self, parent, kit, x, y, w, h, crest, title, sub):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.w, self.h = int(w), int(h)
        self.frame = uir1.Frame(self, 0, 0, w, h, 'panel')
        self.crest = _Image(self, ART + crest, CARD_PAD, CARD_PAD)
        self.title = _CardTitle(kit, self, CARD_PAD + 24, CARD_PAD + 1, title)
        self.sub = _Text(self, CARD_PAD, CARD_PAD + 24, MUTED)
        self.sub.SetText(sub)
        self.Show()


class GuildAlert(ui.Window):
    """Only while something needs an answer or runs: a challenge (Přijmout / Odmítnout), our sent challenge (Zrušit),
    the match starting, the score of the running match."""

    def __init__(self, page, window, kit, y):
        ui.Window.__init__(self)
        self.window = window
        self.SetParent(page)
        self.AddFlag('not_pick')
        self.SetPosition(8, int(y))
        self.SetSize(W - 16, GUILD_ALERT_H)
        w = W - 16
        self.frame = uir1.Frame(self, 0, 0, w, GUILD_ALERT_H, 'panel')
        self.band = uir1.Band(self, 2, 2, w - 4, GUILD_ALERT_H - 4, 'selected')
        self.title = _Text(self, 12, 7, IVORY, TAHB)
        self.detail = _Text(self, 12, 25, INK_DIM)
        self.score = _Text(self, w - 16, 14, IVORY, TAHB, align='right')
        by = (GUILD_ALERT_H - T.BTN_H_S) // 2
        self.accept = uir1.Button(self, kit, w - 12 - 96 - 6 - 96, by, 96, 'Přijmout', primary=True, small=True,
                                  event=self.Accept)
        self.refuse = uir1.Button(self, kit, w - 12 - 96, by, 96, 'Odmítnout', small=True, event=self.Refuse)
        self.kind, self.opp = 'idle', ''
        self.Hide()

    def Accept(self):
        if self.kind == 'received':
            self.window.GuildAccept(self.opp)

    def Refuse(self):
        if self.kind in ('received', 'sent'):
            self.window.GuildRefuse(self.opp)

    def Apply(self, data):
        title, detail, kind = guildarena.WarLine(data)
        self.kind, self.opp = kind, data['opp']
        lead = bool(int(data['lead']))
        _Set(self.title, title, IVORY)
        _Set(self.detail, detail, INK_DIM)
        war = kind == 'war'
        _Visible(self.score, war)
        if war:
            _Set(self.score, '%d : %d' % (int(data['myScore']), int(data['oppScore'])), IVORY)
        _Visible(self.accept, kind == 'received')
        _Visible(self.refuse, kind in ('received', 'sent'))
        if kind == 'received':
            _Button(self.accept, 'Přijmout', lead)
            _Button(self.refuse, 'Odmítnout', lead)
        elif kind == 'sent':
            _Button(self.refuse, 'Zrušit výzvu', lead)


class ChallengeCard(_Card):
    """Výzva: the name of a guild, the format (5v5 / 10v10 / 15v15 / Válka), Vyzvat."""

    def __init__(self, page, window, kit, x, y):
        _Card.__init__(self, page, kit, x, y, CARD_W, CARD_H, 'rank_stribro_18.png', 'Výzva',
                       'Vyzvi konkrétní cech.')
        self.window = window
        inner = CARD_W - 2 * CARD_PAD
        self.name = uir1.Field(self, kit, CARD_PAD, 52, inner, 'Jméno cechu', max_len=24)
        self.mode = 5
        self.modes = uir1.Segment(self, kit, [(m, guildarena.ModeLabel(m)) for m in guildarena.CHALLENGE_MODES],
                                  self.SetMode, width=inner, min_cell=40)
        self.modes.SetPosition(CARD_PAD, 84)
        self.modes.SetValue(self.mode)
        self.button = uir1.Button(self, kit, CARD_PAD, CARD_H - CARD_PAD - T.BTN_H_S, inner, 'Vyzvat', primary=True,
                                  small=True, event=self.Send)

    def SetMode(self, mode):
        self.mode = int(mode)
        self.modes.SetValue(self.mode)
        self.window.GuildRefresh()

    def Send(self):
        self.window.GuildChallenge(self.name.edit.GetText(), self.mode)

    def Apply(self, data):
        has = bool(data and int(data['gid']))
        lead = has and bool(int(data['lead']))
        free = has and int(data['warState']) == guildarena.WAR_NONE and not int(data['queueMode'])
        enabled = lead and free
        for widget in (self.name, self.modes):
            if enabled:
                widget.Enable()
            else:
                widget.Disable()
        if self.mode == guildarena.WAR_MODE:
            sub = 'Válka na mapě, bez stropu hráčů.'
        else:
            sub = 'Vyzvi konkrétní cech na %dv%d.' % (self.mode, self.mode)
        _Set(self.sub, sub, MUTED)
        _Button(self.button, 'Vyzvat', enabled)


class QueueCard(_Card):
    """Aréna cechů: the format, Hledat soupeře; while searching the time and Zrušit hledání."""

    def __init__(self, page, window, kit, x, y):
        _Card.__init__(self, page, kit, x, y, CARD_W, CARD_H, 'rank_zlato_18.png', 'Aréna cechů',
                       'Soupeře najde server.')
        self.window = window
        inner = CARD_W - 2 * CARD_PAD
        self.mode = 5
        self.modes = uir1.Segment(self, kit, [(m, '%dv%d' % (m, m)) for m in guildarena.QUEUE_MODES],
                                  self.SetMode, width=inner, min_cell=40)
        self.modes.SetPosition(CARD_PAD, 52)
        self.modes.SetValue(self.mode)
        self.stateLabel = _Text(self, CARD_PAD, 88, MUTED)
        self.stateValue = _Text(self, CARD_W - CARD_PAD, 88, INK, align='right')
        self.searchTitle = _Text(self, CARD_PAD, 88, IVORY)
        self.searchTitle.SetText('Hledám soupeře')
        self.searchDots = Dots(self, CARD_PAD + uir1.TextWidth(self.searchTitle) + 3, 97)
        self.searchTime = _Text(self, CARD_W - CARD_PAD, 88, INK, align='right')
        self.button = uir1.Button(self, kit, CARD_PAD, CARD_H - CARD_PAD - T.BTN_H_S, inner, 'Hledat soupeře',
                                  primary=True, small=True, event=self.Click)
        self.search = False

    def SetMode(self, mode):
        if self.search:
            return
        self.mode = int(mode)
        self.modes.SetValue(self.mode)
        self.window.GuildRefresh()

    def Click(self):
        self.window.GuildQueue(self.mode)

    def Apply(self, data):
        has = bool(data and int(data['gid']))
        if not has:
            text, enabled, primary, search = 'Hledat soupeře', False, True, False
        else:
            text, enabled, primary, search = GuildQueueButton(self.mode, data)
            if search and int(data['queueMode']) in guildarena.QUEUE_MODES:
                self.mode = int(data['queueMode'])
                self.modes.SetValue(self.mode)
        self.search = search
        kills = guildarena.QUEUE_RULES[self.mode][0]
        _Set(self.sub, 'Do %d zabití, v týmu nejvýš %d.' % (kills, self.mode), MUTED)
        if search:
            self.modes.Disable()
        else:
            self.modes.Enable()
        for widget in (self.stateLabel, self.stateValue):
            _Visible(widget, not search)
        _Visible(self.searchTitle, search)
        _Visible(self.searchTime, search)
        if search:
            self.searchDots.Show()
            _Set(self.searchTime, Clock(data['queueSeconds']), INK)
        else:
            self.searchDots.Hide()
            _Set(self.stateLabel, 'Online z cechu', MUTED)
            if has:
                online = int(data['online'])
                _Set(self.stateValue, '%d / %d' % (online, self.mode), INK if online >= self.mode else LOSS)
            else:
                _Set(self.stateValue, '–', MUTED)
        self.button.SetPrimary(primary)
        _Button(self.button, text, enabled)


class MeleyCard(ui.Window):
    """Meley (owner V9 B): crest, the three conditions as short coloured facts, Přihlásit cech."""

    H = 58

    def __init__(self, page, window, kit, y):
        ui.Window.__init__(self)
        self.window = window
        self.SetParent(page)
        self.AddFlag('not_pick')
        self.SetPosition(8, int(y))
        w = W - 16
        self.SetSize(w, self.H)
        self.frame = uir1.Frame(self, 0, 0, w, self.H, 'panel')
        self.crest = _Image(self, ART + 'rank_legenda_48.png', 6, (self.H - 48) // 2)
        self.title = _CardTitle(kit, self, 60, 8, 'Meley')
        self.subtitle = _Text(self, 60 + 58, 11, INK_DIM)
        self.subtitle.SetText('Dračí doupě · 1× týdně')
        self.checks = [_Text(self, 60, 33, INK) for unused in range(3)]
        self.button = uir1.Button(self, kit, w - 12 - 120, (self.H - T.BTN_H_S) // 2, 120, 'Přihlásit cech',
                                  primary=True, small=True, event=window.GuildMeley)
        self.Show()

    def Apply(self, data):
        has = bool(data and int(data['gid']))
        if not has:
            for line in self.checks:
                _Visible(line, False)
            _Button(self.button, 'Přihlásit cech', False)
            return
        x = 60
        for line, (text, ok) in zip(self.checks, MeleyChecks(data)):
            _Visible(line, True)
            line.SetPosition(x, 33)
            _Set(line, text, WIN if ok else LOSS)
            x += uir1.TextWidth(line) + 14
        role = int(data['role'])
        if not int(data['meleyOpen']):
            text, enabled = 'Zavřeno', False
        elif int(data['meleyRegistered']):
            text, enabled = 'Přihlášeno', False
        else:
            ready = all(ok for unused, ok in MeleyChecks(data))
            free = int(data['warState']) == guildarena.WAR_NONE
            text, enabled = 'Přihlásit cech', ready and free and role >= 2
        self.button.SetPrimary(enabled)
        _Button(self.button, text, enabled)


class GuildPage(_Page):
    def __init__(self, window, kit, y):
        _Page.__init__(self, window, y, GUILD_H + GUILD_ALERT_H - y)
        self.window = window
        self.y0 = y
        top = 69 - y
        self.guildName = _Text(self, PAD, top, IVORY, TAHB)
        self.guildInfo = _Text(self, PAD + 80, top, INK_DIM)
        self.role = _Text(self, W - PAD, top, INK_DIM, align='right')
        self.warriors = Link(self, W - PAD, top, 'Válečníci', window.GuildWarriors)
        self.alert = GuildAlert(self, window, kit, 93 - y)
        self.challenge = ChallengeCard(self, window, kit, 8, 93 - y)
        self.queue = QueueCard(self, window, kit, 8 + CARD_W + 8, 93 - y)
        self.meley = MeleyCard(self, window, kit, 93 - y + CARD_H + 8)
        self.footer = 93 - y + CARD_H + 8 + MeleyCard.H + 8
        self.record = _Text(self, PAD, self.footer, MUTED)
        self.message = _Text(self, PAD, self.footer + 20, LOSS)
        self.alertShown = None
        self.locked = None
        self.lockedPanel = GuildLocked(self, kit, top, 93 - y + CARD_H + 8 + MeleyCard.H - top)
        self.content = (self.guildName, self.guildInfo, self.role, self.warriors, self.challenge, self.queue,
                        self.meley, self.record, self.message)

    def SetLocked(self, locked):
        """Locked: only the locked panel; open: the cards come back (Apply fills them)."""
        locked = bool(locked)
        if locked == self.locked:
            return
        self.locked = locked
        _Visible(self.lockedPanel, locked)
        for widget in self.content:
            _Visible(widget, not locked)
        if locked:
            _Visible(self.alert, False)
            self.alertShown = None
            self.__Place(False)

    def HasAlert(self):
        return bool(self.alertShown)

    def __Place(self, alert):
        if alert == self.alertShown:
            return
        self.alertShown = alert
        dy = (GUILD_ALERT_H + 8) if alert else 0
        base = 93 - self.y0
        self.challenge.SetPosition(8, base + dy)
        self.queue.SetPosition(8 + CARD_W + 8, base + dy)
        self.meley.SetPosition(8, base + dy + CARD_H + 8)
        self.footer = base + dy + CARD_H + 8 + MeleyCard.H + 8
        self.record.SetPosition(PAD, self.footer)
        self.message.SetPosition(PAD, self.footer + 20)
        _Visible(self.alert, alert)

    def Apply(self, data, name, localError):
        has = bool(data and int(data['gid']))
        if has:
            title, info, record = GuildSummary(data, name)
        else:
            title, info, record = ('Cechy', '', '')
        _Set(self.guildName, title, IVORY)
        self.guildInfo.SetPosition(PAD + uir1.TextWidth(self.guildName) + 8, self.guildName.GetLocalPosition()[1])
        _Set(self.guildInfo, info, INK_DIM)
        leader = has and int(data['role']) == 3
        _Visible(self.role, has and not leader)
        if has and not leader:
            _Set(self.role, guildarena.ROLE_NAME.get(int(data['role']), ''), INK_DIM)
        alert = has and int(data['warState']) != guildarena.WAR_NONE
        self.__Place(alert)
        if alert:
            self.alert.Apply(data)
        self.challenge.Apply(data)
        self.queue.Apply(data)
        self.meley.Apply(data)
        _Set(self.record, 'Výhry / remízy / prohry  %s' % record if has else '', MUTED)
        _Visible(self.warriors, leader)
        if data is None:
            message, color = 'Načítá se…', INK_DIM
        elif not has:
            message, color = 'Nejsi v žádném cechu. Výzvy a aréna jsou pro cechy.', INK_DIM
        elif localError:
            message, color = localError, LOSS
        elif not int(data['lead']):
            message, color = 'Vyzývat a hledat smí vůdce, rada a válečníci.', MUTED
        else:
            message, color = '', MUTED
        _Set(self.message, message, color)


class ArenaWindow(ui.Window):
    """Hodnocená aréna, variant C. The interface uses it like uipvpmatchmaking.PvPMatchmakingWindow: Show, Close,
    IsShow, OnServerChanged, Destroy (the ready dialog, the HUD and the result belong to it)."""

    TITLE = 'Hodnocená aréna'
    HEIGHTS = {'play': PLAY_H, 'board': BOARD_H, 'history': HISTORY_H, 'guild': GUILD_H}

    def __init__(self):
        ui.Window.__init__(self)
        self.built = False
        self.kit = TahomaKit()
        self.mode = 2
        self.tab = 'play'
        self.localError = ''
        self.guildError = ''
        self.guildPoll = 0.0
        self.lastRefresh = 0.0
        self.lastRequest = 0.0
        self.historyAfterSnapshot = False
        self.boardFilter = 'all'
        self.boardCursors = [(0, 0)]
        self.boardOffset = 0
        self.historyCursors = [0]
        self.historyOffset = 0
        self.failed = False
        self.rulesDialog = None
        self.readyDialog = None
        self.matchHud = None
        self.resultDialog = None
        self.warriorsDialog = None
        self.AddFlag('float')
        self.AddFlag('movable')
        self.SetSize(W, PLAY_H)
        self.chrome = uir1.Chrome(self, self.kit, W, PLAY_H, self.TITLE, on_close=self.Close)
        top = self.chrome.ContentTop()
        self.tabs = uir1.Segment(self, self.kit, [('play', 'Hrát'), ('board', 'Žebříček'),
                                                  ('history', 'Historie'), ('guild', 'Cechy')], self.SelectTab,
                                 width=TABS_W)
        self.tabs.SetPosition((W - TABS_W) // 2, top + 6)
        self.guildCell = self.tabs.cells[self.tabs.values.index('guild')]
        self.guildCell.__class__ = LockableTabCell
        self.guildCell.InitLock()
        self.guildLocked = None
        pageY = top + 6 + T.SEG_H
        self.pages = {'play': PlayPage(self, self.kit, pageY), 'board': BoardPage(self, self.kit, pageY),
                      'history': HistoryPage(self, self.kit, pageY), 'guild': GuildPage(self, self.kit, pageY)}
        self.rulesDialog = RulesDialog(self.kit)
        self.readyDialog = ReadyDialog(self.kit, self)
        self.matchHud = MatchHud(self.kit)
        self.resultDialog = ResultDialog(self.kit, self)
        self.warriorsDialog = WarriorsDialog(self.kit, self)
        self.matchHud.resultDialog = self.resultDialog
        # A shown 0 x 0 window that is never drawn or picked: its OnUpdate brings the kept result back after a warp
        # (the arena window, the HUD and the dialogs are hidden then, so none of them is updated).
        self.ticker = ui.Window()
        self.ticker.AddFlag('not_pick')
        self.ticker.SetSize(0, 0)
        self.ticker.OnUpdate = ui.__mem_func__(self.__PendingTick)
        self.ticker.Show()
        self.tickerNext = 0.0
        self.built = True
        self.__ShowTab('play', False)
        self.SetCenterPosition()
        ui.Window.Hide(self)

    # ------------------------------------------------------------------ interface API
    def Show(self):
        if not ArenaShown():
            self.Close()
            return
        ui.Window.Show(self)
        self.SetTop()
        self.__ShowTab(self.tab, True)

    def Hide(self):
        # Safe before the build finished (Hide may come from a parent while __init__ runs).
        ui.Window.Hide(self)

    def Close(self):
        if getattr(self, 'rulesDialog', None) is not None:
            self.rulesDialog.Close()
        if getattr(self, 'warriorsDialog', None) is not None:
            self.warriorsDialog.Close()
        if getattr(self, 'pages', None):
            self.pages['board'].filter.CloseMenu()
        ui.Window.Hide(self)

    def Destroy(self):
        for name in ('rulesDialog', 'readyDialog', 'matchHud', 'resultDialog', 'warriorsDialog'):
            dialog = getattr(self, name, None)
            if dialog is not None:
                dialog.Destroy()
        ticker = getattr(self, 'ticker', None)
        if ticker is not None:
            ticker.Hide()
            ticker.OnUpdate = lambda: None
        ui.Window.Hide(self)

    def OnPressEscapeKey(self):
        board = self.pages['board'] if getattr(self, 'pages', None) else None
        if board is not None and board.filter.IsOpen():
            board.filter.CloseMenu()
            return True
        self.Close()
        return True

    def OnServerChanged(self):
        self.localError = ''
        self.__Guard(self.__ServerChanged)

    def __ServerChanged(self):
        if self.IsShow():
            self.__Refresh()
            if self.tab == 'play' and self.historyAfterSnapshot:
                if net.SendPvPMatchmakingHistory(self.mode, 0):
                    self.historyAfterSnapshot = False
                    self.lastRequest = app.GetTime()
        self.__RefreshOverlays()

    def OnUpdate(self):
        now = app.GetTime()
        if self.IsShow() and self.tab == 'play':
            for row in self.pages['play'].rows.values():
                row.SyncHover()
                if row.search:
                    row.searchDots.Step(now)
        if self.IsShow() and self.tab == 'guild':
            page = self.pages['guild']
            if page.queue.search:
                page.queue.searchDots.Step(now)
            if self.guildPoll and now >= self.guildPoll:
                self.guildPoll = 0.0
                if GuildArenaOpen():
                    guildarena.Request(now, every=0.0)
        if now - self.lastRefresh < 1.0:
            return
        self.lastRefresh = now
        self.__Guard(self.__Tick, now)

    def __Tick(self, now):
        if self.IsShow():
            if not ArenaShown():
                self.Close()
            else:
                self.__Refresh()
                if self.tab == 'play' and now - self.lastRequest >= 5.0:
                    self.__Request()
                elif self.tab == 'guild' and GuildArenaOpen():
                    guildarena.Request(now)
        self.__RefreshOverlays()

    def __Guard(self, function, *args):
        """A failure of the R1 refresh is traced once (syserr) and never reaches the game loop."""
        try:
            function(*args)
        except Exception:
            if not self.failed:
                self.failed = True
                uir1.TraceFailure('the rated arena window')

    def __PendingTick(self):
        now = app.GetTime()
        if now < self.tickerNext:
            return
        self.tickerNext = now + 0.5
        self.__Guard(self.__RestoreResult)

    def __RestoreResult(self):
        """Shows the kept result again (after a warp) while the player has not closed it."""
        pending = _RESULT['pending']
        dialog = self.resultDialog
        if pending is None or dialog is None or dialog.IsShow():
            return
        hud = self.matchHud
        if hud is not None and hud.cachedResult is not None:
            return                          # still the 5 s in the HUD of this window
        if ArenaShown():
            dialog.Present(pending['result'], pending['team'], pending['mode'])

    def __RefreshOverlays(self):
        for dialog in (self.readyDialog, self.matchHud, self.resultDialog):
            if dialog is not None:
                dialog.Refresh()

    # ------------------------------------------------------------------ tabs
    def SelectTab(self, tab):
        self.__ShowTab(tab, True)

    def __ShowTab(self, tab, request):
        self.tab = tab if tab in self.pages else 'play'
        self.tabs.SetValue(self.tab)
        height = self.HEIGHTS[self.tab]
        if self.GetHeight() != height:
            self.SetSize(W, height)
            self.chrome.frame.Resize(W, height)
        for key, page in self.pages.items():
            if key == self.tab:
                page.Show()
            else:
                page.Hide()
        self.pages['board'].modes.SetValue(self.mode)
        self.pages['history'].modes.SetValue(self.mode)
        if self.tab != 'board':
            self.pages['board'].filter.CloseMenu()
        if self.tab == 'board':
            self.boardCursors, self.boardOffset = [BoardStartCursor(self.boardFilter)], 0
        elif self.tab == 'history':
            self.historyCursors, self.historyOffset = [0], 0
        self.__Refresh()
        if request:
            self.__Request()

    def SelectMode(self, mode):
        self.mode = int(mode)
        self.__ShowTab(self.tab, True)

    def SelectBoardFilter(self, key):
        """"Zobrazit": Všichni or a division (the page from the division's upper bound, the server's #)."""
        self.boardFilter = key
        self.boardCursors, self.boardOffset = [BoardStartCursor(key)], 0
        self.__Refresh()
        self.__Request()

    def OpenRules(self):
        self.rulesDialog.Open()

    # ------------------------------------------------------------------ requests (the packets of the original window)
    def __Request(self):
        if self.tab == 'guild':
            return GuildArenaOpen() and guildarena.Request(every=0.5)
        if not pvpmatchmaking.IsAvailable():
            return False
        if self.tab == 'play':
            sent = net.SendPvPMatchmakingSnapshot()
            if sent:
                self.historyAfterSnapshot = True
        elif self.tab == 'board':
            rating, pid = self.boardCursors[-1]
            sent = net.SendPvPMatchmakingLeaderboard(self.mode, rating, pid)
        else:
            sent = net.SendPvPMatchmakingHistory(self.mode, self.historyCursors[-1])
        if sent:
            self.lastRequest = app.GetTime()
        return sent

    def ToggleQueue(self, mode):
        if _CommandPending():
            return
        if _NotLeader():
            self.localError = 'Frontu může spustit jen vůdce skupiny.'
            self.__Refresh()
            return
        self.localError = ''
        queue = tuple(pvpmatchmaking.GetQueue())
        if int(queue[0]) == QUEUE_SEARCHING:
            sent = net.SendPvPMatchmakingCancel()
        else:
            self.mode = int(mode)
            sent = net.SendPvPMatchmakingQueue(int(mode))
        if sent:
            self.__Refresh()

    def PlayAgain(self, mode):
        """"Hrát znovu" of the result: the queue in the same mode."""
        if _CommandPending() or not ArenaShown():
            return False
        if _NotLeader():
            self.localError = 'Frontu může spustit jen vůdce skupiny.'
            return False
        self.mode = int(mode)
        return bool(net.SendPvPMatchmakingQueue(int(mode)))

    def CancelSearch(self):
        if not _CommandPending():
            net.SendPvPMatchmakingCancel()

    # ------------------------------------------------------------------ paging
    def __BoardPage(self):
        """(rows of the page inside the filter, page has more, the page's last row is still inside the filter)."""
        board = tuple(pvpmatchmaking.GetLeaderboard())
        valid = bool(int(board[3])) and int(board[0]) == self.mode
        count = int(board[2]) if valid else 0
        rows = [tuple(pvpmatchmaking.GetLeaderboardRow(i)) for i in range(count)]
        first, end = DivisionSlice([int(r[2]) for r in rows], self.boardFilter)
        more = bool(int(board[1])) and count > 0 and end == count       # stops at the division's lower bound
        return rows[first:end], more, rows[-1] if rows else None, valid

    def BoardNext(self):
        rows, more, last, unused = self.__BoardPage()
        if self.boardOffset + PAGE_ROWS < len(rows):
            self.boardOffset += PAGE_ROWS
        elif more and last is not None:
            self.boardCursors.append((int(last[2]), int(last[1])))
            self.boardOffset = 0
            self.__Request()
        self.__Refresh()

    def BoardPrev(self):
        if self.boardOffset >= PAGE_ROWS:
            self.boardOffset -= PAGE_ROWS
        elif len(self.boardCursors) > 1:
            self.boardCursors.pop()
            self.boardOffset = 0
            self.__Request()
        self.__Refresh()

    def HistoryOlder(self):
        history = tuple(pvpmatchmaking.GetHistory())
        count = int(history[2]) if int(history[3]) else 0
        if self.historyOffset + PAGE_ROWS < count:
            self.historyOffset += PAGE_ROWS
        elif int(history[1]) and count:
            last = tuple(pvpmatchmaking.GetHistoryRow(count - 1))
            self.historyCursors.append(int(last[0]))
            self.historyOffset = 0
            self.__Request()
        self.__Refresh()

    # ------------------------------------------------------------------ refresh
    def __Refresh(self):
        if not self.built:
            return
        self.__SyncGuildLock()
        if self.tab == 'play':
            self.__RefreshPlay()
        elif self.tab == 'board':
            self.__RefreshBoard()
        elif self.tab == 'guild':
            self.__RefreshGuild()
        else:
            self.__RefreshHistory()

    # ------------------------------------------------------------------ tab Cechy
    def __SyncGuildLock(self):
        """The server state (GuildArenaOpen) on the tab cell and the page, live: opening brings the cards back and asks
        for the state at once, closing switches an open page to the locked panel."""
        locked = not GuildArenaOpen()
        if locked == self.guildLocked:
            return
        opened = self.guildLocked and not locked
        self.guildLocked = locked
        self.guildCell.SetLocked(locked)
        self.pages['guild'].SetLocked(locked)
        if locked:
            self.guildError = ''
            self.guildPoll = 0.0
            if self.warriorsDialog is not None:
                self.warriorsDialog.Close()
        elif opened and self.tab == 'guild' and self.IsShow():
            guildarena.Request(every=0.0)

    def __RefreshGuild(self):
        page = self.pages['guild']
        if self.guildLocked:
            if self.tab == 'guild' and self.GetHeight() != GUILD_H:
                self.SetSize(W, GUILD_H)
                self.chrome.frame.Resize(W, GUILD_H)
            return
        data = guildarena.Get()
        name = ''
        if data and int(data['gid']):
            try:
                import guild
                name = guild.GetGuildName(int(data['gid']))
            except Exception:
                name = ''
            if name == 'Noname':
                name = ''
        page.Apply(data, name, self.guildError)
        height = GUILD_H + (GUILD_ALERT_H + 8 if page.HasAlert() else 0)
        if self.tab == 'guild' and self.GetHeight() != height:
            self.SetSize(W, height)
            self.chrome.frame.Resize(W, height)
        if self.warriorsDialog is not None and self.warriorsDialog.IsShow():
            self.warriorsDialog.Refresh()

    def __GuildSent(self, sent, error=''):
        self.guildError = '' if sent else (error or 'Příkaz se nepodařilo odeslat.')
        self.guildPoll = app.GetTime() + 1.0
        self.__Refresh()

    def GuildRefresh(self):
        self.__Refresh()

    def GuildPollSoon(self):
        self.guildPoll = app.GetTime() + 1.0

    def GuildChallenge(self, name, mode):
        if self.guildLocked:
            return
        if not guildarena.CleanName(name):
            self.guildError = 'Napiš jméno cechu, který chceš vyzvat.'
            self.__Refresh()
            return
        self.__GuildSent(guildarena.Challenge(name, mode))

    def GuildAccept(self, name):
        if self.guildLocked:
            return
        self.__GuildSent(guildarena.Accept(name))

    def GuildRefuse(self, name):
        if self.guildLocked:
            return
        self.__GuildSent(guildarena.Refuse(name))

    def GuildMeley(self):
        if self.guildLocked:
            return
        self.__GuildSent(guildarena.Meley())

    def GuildWarriors(self):
        if self.guildLocked:
            return
        self.warriorsDialog.Refresh()
        self.warriorsDialog.Open()

    def GuildQueue(self, mode):
        if self.guildLocked:
            return
        data = guildarena.Get()
        if data and int(data['queueMode']) == int(mode):
            self.__GuildSent(guildarena.Leave())
        else:
            self.__GuildSent(guildarena.Queue(mode))

    def __RefreshPlay(self):
        page = self.pages['play']
        now = _Now()
        snapshot = tuple(pvpmatchmaking.GetSnapshot())
        loaded = int(snapshot[5]) > 0
        title, ends = SeasonText(snapshot[0], snapshot[1], now)
        _Set(page.seasonTitle, title, IVORY)
        page.seasonEnds.SetPosition(PAD + uir1.TextWidth(page.seasonTitle) + 8, page.seasonTitle.GetLocalPosition()[1])
        _Set(page.seasonEnds, ends, INK_DIM)
        queue = tuple(pvpmatchmaking.GetQueue())
        status, queueMode = int(queue[0]), int(queue[1])
        cooldown = max(0, int(queue[4])) if status == QUEUE_COOLDOWN else 0
        pending = _CommandPending()
        available = bool(pvpmatchmaking.IsAvailable())
        notLeader = _NotLeader()
        busy = status in (QUEUE_READY, QUEUE_MATCH)
        for mode, row in page.rows.items():
            stats = _Stats(mode)
            search = status == QUEUE_SEARCHING and queueMode == mode
            if search:
                text, enabled, primary = 'Zrušit', not pending, False
            elif cooldown:
                text, enabled, primary = 'Trest %s' % Clock(cooldown), False, False
            else:
                text = 'Hledat'
                enabled = (available and not pending and not busy and not notLeader and
                           status != QUEUE_SEARCHING)
                primary = True
            row.Apply(dict(stats=stats, loaded=loaded, search=search, elapsed=int(queue[2]),
                           estimate=int(queue[3]), button=text, enabled=enabled, primary=primary))
        page.SetLast(self.__LastMatch(now))
        message, color = '', LOSS
        error = ErrorText(tuple(pvpmatchmaking.GetError()))
        if not available:
            message = 'Aréna teď není dostupná.'
        elif pending:
            message, color = ('Hledání se ruší…' if status == QUEUE_SEARCHING else 'Připojování do fronty…'), INK_DIM
        elif cooldown:
            message = 'Odmítl jsi zápas. Hledat můžeš znovu za %s.' % Clock(cooldown)
        elif notLeader:
            message = 'Frontu může spustit jen vůdce skupiny.'
        elif self.localError:
            message = self.localError
        elif error and status not in (QUEUE_SEARCHING, QUEUE_MATCH, QUEUE_COOLDOWN):
            message = error
        elif status == QUEUE_SEARCHING and int(queue[2]) >= RATING_WINDOW_FULL_SECONDS:
            message, color = 'Hledám soupeře v nejširším rozsahu ELO (±300).', MUTED
        elif status == QUEUE_SEARCHING and int(queue[2]) >= RATING_WINDOW_STEP_SECONDS:
            message, color = 'Hledám soupeře… rozsah ELO se každých 30 s rozšiřuje.', MUTED
        elif status == QUEUE_SEARCHING:
            message, color = 'Při hledání můžeš okno zavřít, stav ukazuje medailon u minimapy.', MUTED
        _Set(page.message, message, color)

    def __LastMatch(self, now):
        result = tuple(pvpmatchmaking.GetResult())
        team = mode = 0
        if self.matchHud is not None:
            team, mode = self.matchHud.TeamOf(int(result[0]))
        if int(result[7]) and int(result[0]) and int(result[1]):
            outcome, delta = int(result[1]), int(result[6])
            text, color = Outcome(outcome, delta, team)
            when = ''
            history = tuple(pvpmatchmaking.GetHistory())
            if int(history[3]) and int(history[2]):
                row = tuple(pvpmatchmaking.GetHistoryRow(0))
                if int(row[0]) == int(result[0]):
                    when = Ago(row[1], now)
                    mode = mode or int(history[0])
            return dict(text=text, color=color, score=MyScore(outcome, delta, result[2], result[3], team),
                        mode=mode, delta=delta, when=when)
        history = tuple(pvpmatchmaking.GetHistory())
        if int(history[3]) and int(history[2]):
            row = tuple(pvpmatchmaking.GetHistoryRow(0))
            outcome, delta = int(row[2]), int(row[7])
            text, color = Outcome(outcome, delta)
            return dict(text=text, color=color, score=MyScore(outcome, delta, row[3], row[4]), mode=int(history[0]),
                        delta=delta, when=Ago(row[1], now))
        return None

    def __RefreshBoard(self):
        page = self.pages['board']
        snapshot = tuple(pvpmatchmaking.GetSnapshot())
        title, ends = SeasonText(snapshot[0], snapshot[1], _Now())
        _Set(page.season, '%s · %s' % (title, ends.split(' (')[0]) if ends else title, INK_DIM)
        open_ = RankingsOpen()
        page.filter.SetValue(self.boardFilter)
        rows, more, unused, valid = self.__BoardPage()
        count = len(rows)
        start = self.boardOffset
        for index, row in enumerate(page.rows):
            source = start + index
            if open_ and source < count:
                values = rows[source]
                row.Set((int(values[0]), int(values[2]), int(values[3]), int(values[4]), values[5]))
                if row.shade is not None:
                    _Visible(row.shade, index % 2 == 1)
            else:
                row.Set(None)
        stats = _Stats(self.mode)
        snapshotLoaded = int(snapshot[5]) > 0
        if open_ and snapshotLoaded:
            name = ''
            try:
                name = player.GetName()
            except Exception:
                pass
            page.mine.Set((stats['position'], stats['rating'], stats['wins'], stats['losses'], '%s (ty)' % name),
                          mine=True)
        else:
            page.mine.Set(None)
        _Visible(page.ruleBottom, open_)
        if not open_:
            _Set(page.message, 'Žebříčky jsou dočasně vypnuté.', INK_DIM)
            _Set(page.message2, 'Výsledky se dál počítají.', MUTED)
        elif count == 0:
            error = ErrorText(tuple(pvpmatchmaking.GetError()))
            empty = ('V divizi %s zatím nikdo není.' % page.filter.Label(self.boardFilter)
                     if self.boardFilter != 'all' else 'V žebříčku zatím nikdo není.')
            _Set(page.message, error or (empty if valid else 'Žebříček se načítá…'), LOSS if error else INK_DIM)
            _Set(page.message2, '', MUTED)
        else:
            _Set(page.message, '', INK_DIM)
            _Set(page.message2, '', MUTED)
        first = int(rows[start][0]) if open_ and start < count else 0
        last = int(rows[min(count, start + PAGE_ROWS) - 1][0]) if open_ and start < count else 0
        span = '%d–%d' % (first, last) if first else ''
        if span and self.boardFilter != 'all':
            span += ' · ' + page.filter.Label(self.boardFilter)
        _Set(page.pageText, span, MUTED)
        _Button(page.prev, '‹ Předchozí', open_ and (start > 0 or len(self.boardCursors) > 1))
        _Button(page.next, 'Další ›', open_ and (start + PAGE_ROWS < count or more))
        if not open_:
            page.filter.CloseMenu()

    def __RefreshHistory(self):
        page = self.pages['history']
        now = _Now()
        history = tuple(pvpmatchmaking.GetHistory())
        valid = bool(int(history[3])) and int(history[0]) == self.mode
        count = int(history[2]) if valid else 0
        rows = [tuple(pvpmatchmaking.GetHistoryRow(i)) for i in range(count)]
        start = self.historyOffset
        for index, row in enumerate(page.rows):
            source = start + index
            row.Set(rows[source] if source < count else None, now, index % 2 == 1)
        summary = DaySummary([(r[1], r[2], r[7]) for r in rows], now) if len(self.historyCursors) == 1 else ''
        _Set(page.summary, summary, INK_DIM)
        if count == 0:
            error = ErrorText(tuple(pvpmatchmaking.GetError()))
            _Set(page.message, error or ('Zatím tu nejsou žádné hodnocené zápasy.' if valid else
                                         'Historie se načítá…'), LOSS if error else INK_DIM)
        else:
            _Set(page.message, '', INK_DIM)
        _Button(page.older, 'Načíst starší', start + PAGE_ROWS < count or (bool(int(history[1])) and count > 0))


# --------------------------------------------------------------------------- dialogs
class _Dialog(ui.Window):
    """Dialog style C: the R1 dialog frame, the title like POSTAVA with the vein, the content, the buttons with the
    confirm on the LEFT. Floating and movable; Esc = the cancel."""

    def __init__(self, kit, w, h, title):
        ui.Window.__init__(self)
        self.kit = kit
        self.w, self.h = int(w), int(h)
        self.AddFlag('float')
        self.AddFlag('movable')
        self.SetSize(self.w, self.h)
        self.chrome = uir1.Chrome(self, kit, self.w, self.h, title, kind='dialog')
        self.top = self.chrome.ContentTop()

    def Resize(self, h):
        if int(h) != self.h:
            self.h = int(h)
            self.SetSize(self.w, self.h)
            self.chrome.frame.Resize(self.w, self.h)

    def Center(self, text, y, color=INK, font=TAH):
        line = _Text(self, self.w // 2, y, color, font, align='center')
        line.SetText(text)
        return line

    def Open(self):
        self.SetCenterPosition()
        self.Show()
        self.SetTop()

    def Close(self):
        ui.Window.Hide(self)

    def Destroy(self):
        ui.Window.Hide(self)

    def Refresh(self):
        pass

    def OnPressEscapeKey(self):
        self.Close()
        return True


class RulesDialog(_Dialog):
    LINES = (('Formát', 'BO3, max. 3 minuty na kolo, 5 s příprava'),
             ('Režimy', '1v1 sólo · 2v2 a 3v3 sólo i skupina'),
             ('Výbava', 'Maximální úroveň, běžná výbava'),
             ('Odpověď', '15 s na přijetí zápasu'),
             ('Tresty', '30 s · 2 min · 5 min · 15 min'),
             ('', '24 h bez prohřešku = znovu od 30 s'),
             ('Odpojení', '60 s na návrat, jinak tým prohrává'))

    def __init__(self, kit):
        h = 29 + 10 + len(self.LINES) * 18 + 12 + T.BTN_H + 12
        _Dialog.__init__(self, kit, RULES_W, h, 'Pravidla a tresty')
        y = self.top + 10
        self.labels = []
        for label, value in self.LINES:
            a = _Text(self, PAD + 4, y, MUTED)
            a.SetText(label)
            b = _Text(self, PAD + 84, y, INK)
            b.SetText(value)
            self.labels.append((a, b))
            y += 18
        self.close = uir1.Button(self, kit, (RULES_W - 96) // 2, y + 12, 96, 'Zavřít', primary=True,
                                 event=self.Close)
        ui.Window.Hide(self)


class ReadyDialog(_Dialog):
    """Zápas nalezen: mode · BO3, the 15 s ring (ReadyOffer.deadlineUnix), your team with names left, the opponents
    without names right (only their confirmation, as today), "2 / 4 připraveno", Přijmout LEFT (primary) and
    Odmítnout right, Esc = odmítnout. After the offer ends without a match: Zápas zrušen (back in the queue, or the
    penalty)."""

    def __init__(self, kit, owner):
        _Dialog.__init__(self, kit, READY_W, READY_H, 'Zápas nalezen')
        import uiconfirm
        uiconfirm.Prioritize(self)
        self.owner = owner
        self.readyId = 0
        self.accepted = self.declining = False
        self.pendingDecision = None
        self.cancelled = None             # None or dict(kind, ...) while "Zápas zrušen" shows
        self.lastMode = 0
        self.lastRefresh = 0.0
        y = self.top + 10
        self.subtitle = self.Center('', y, INK_DIM)
        y += 24
        self.ringY = y
        self.ring = _Image(self, ART + 'timer_15.png', (READY_W - 72) // 2, y + 34 - 36)
        self.seconds = _Text(self, READY_W // 2, y + 34 - 12, IVORY, TAHB, align='center')
        self.unit = _Text(self, READY_W // 2, y + 34 + 2, INK_DIM, align='center')
        self.unit.SetText('s')
        lx, rx = 18, READY_W - 18
        self.mineHead = _Text(self, lx, y + 6, MUTED)
        self.mineHead.SetText('Tvůj tým')
        self.theirHead = _Text(self, rx, y + 6, MUTED, align='right')
        self.theirHead.SetText('Soupeři')
        self.mine, self.theirs = [], []
        for index in range(3):
            ty = y + 26 + index * 20
            tick = _Image(self, ART + 'tick_11.png', lx, ty + 1)
            dots = Dots(self, lx + 1, ty + 6, 0xBEB6AC)
            name = _Text(self, lx + 16, ty, INK_DIM)
            self.mine.append((tick, dots, name))
            tick = _Image(self, ART + 'tick_11.png', rx - 11, ty + 1)
            dots = Dots(self, rx - 11, ty + 6, 0xBEB6AC)
            name = _Text(self, rx - 16, ty, INK_DIM, align='right')
            name.SetText('Soupeř')
            self.theirs.append((tick, dots, name))
        y += 68 + 10
        self.ready = self.Center('', y, INK)
        y += 26
        self.note = self.Center('', y, MUTED)
        y += 32
        bx = (READY_W - 2 * 120 - 10) // 2
        self.accept = uir1.Button(self, kit, bx, y, 120, 'Přijmout', primary=True, event=self.Accept)
        self.decline = uir1.Button(self, kit, bx + 130, y, 120, 'Odmítnout', event=self.Decline)
        # Zápas zrušen
        cy = self.top + 14
        self.cancelLines = [self.Center('', cy + i * 18, color) for i, color in enumerate((INK, INK_DIM, MUTED))]
        cy += 36 + 18 + 14
        self.ok = uir1.Button(self, kit, (READY_W - 96 * 2 - 10) // 2, cy, 96, 'OK', primary=True, event=self.Dismiss)
        self.stopSearch = uir1.Button(self, kit, (READY_W - 96 * 2 - 10) // 2 + 106, cy, 96, 'Zrušit hledání',
                                      event=self.StopSearch)
        self.offerWidgets = [self.subtitle, self.ring, self.seconds, self.unit, self.mineHead, self.theirHead,
                             self.ready, self.note, self.accept, self.decline]
        self.cancelWidgets = self.cancelLines + [self.ok, self.stopSearch]
        self.view = None
        ui.Window.Hide(self)

    # ------------------------------------------------------------------ actions
    def OnIMEReturn(self):
        import uiconfirm
        return uiconfirm.Activate(self.ok if self.cancelled is not None else self.accept)

    def Accept(self):
        self.__Choose(1)

    def Decline(self):
        self.__Choose(0)

    def Dismiss(self):
        self.cancelled = None
        self.Close()

    def StopSearch(self):
        self.owner.CancelSearch()
        self.Dismiss()

    def OnPressEscapeKey(self):
        if self.cancelled is not None:
            self.Dismiss()
        else:
            self.Decline()
        return True

    def __Choose(self, decision):
        if self.accepted or self.declining or self.pendingDecision is not None or not self.readyId:
            return
        self.pendingDecision = decision
        self.__TrySend()
        self.Refresh()

    def __TrySend(self):
        if self.pendingDecision is None or _CommandPending():
            return
        ready = tuple(pvpmatchmaking.GetReady())
        if not int(ready[0]) or int(ready[0]) != self.readyId or int(ready[2]) <= _Now():
            self.pendingDecision = None
            return
        decision = self.pendingDecision
        if net.SendPvPMatchmakingReady(self.readyId, decision):
            self.pendingDecision = None
            self.accepted = decision == 1
            self.declining = decision == 0

    # ------------------------------------------------------------------ views
    def __View(self, view):
        if view == self.view:
            return
        self.view = view
        for widget in self.offerWidgets:
            widget.Show() if view == 'offer' else widget.Hide()
        for widget in self.cancelWidgets:
            widget.Show() if view == 'cancel' else widget.Hide()
        if view != 'offer':
            for tick, dots, name in self.mine + self.theirs:
                tick.Hide()
                dots.Hide()
                name.Hide()
        if view == 'cancel':
            self.chrome.SetTitle('Zápas zrušen')
            self.Resize(CANCEL_H)
        else:
            self.chrome.SetTitle('Zápas nalezen')
            self.Resize(READY_H)

    def Refresh(self):
        ready = tuple(pvpmatchmaking.GetReady())
        readyId = int(ready[0])
        if not ArenaShown():
            self.readyId, self.cancelled = 0, None
            self.Close()
            return
        if not readyId:
            if self.readyId:
                self.__Ended()
            self.readyId = 0
            self.accepted = self.declining = False
            self.pendingDecision = None
            if self.cancelled is None:
                self.Close()
            else:
                self.__ShowCancelled()
            return
        if readyId != self.readyId:
            self.readyId = readyId
            self.accepted = self.declining = False
            self.pendingDecision = None
            self.cancelled = None
            self.SetCenterPosition()
        self.lastMode = int(ready[1])
        self.__ShowOffer(ready)

    def __Ended(self):
        """The offer ended: a match (nothing to say), back in the queue (an opponent did not accept) or a penalty."""
        queue = tuple(pvpmatchmaking.GetQueue())
        status = int(queue[0])
        if status == QUEUE_MATCH or int(tuple(pvpmatchmaking.GetMatch())[8]):
            self.cancelled = None
        elif status == QUEUE_SEARCHING:
            self.cancelled = dict(kind='requeue')
        elif status == QUEUE_COOLDOWN and int(queue[4]) > 0:
            self.cancelled = dict(kind='penalty', declined=self.declining, cooldown=int(queue[4]))
        else:
            self.cancelled = dict(kind='ended')

    def __ShowCancelled(self):
        self.__View('cancel')
        kind = self.cancelled['kind']
        queue = tuple(pvpmatchmaking.GetQueue())
        if kind == 'requeue':
            if int(queue[0]) != QUEUE_SEARCHING:
                self.cancelled = None
                self.Close()
                return
            lines = ('Jeden ze soupeřů zápas nepřijal.', 'Vracíš se do fronty, čas hledání běží dál.',
                     'Hledání soupeře %s · %s' % (Clock(queue[2]), MODE_NAME.get(int(queue[1]), '')))
            colors = (INK, INK_DIM, MUTED)
        elif kind == 'penalty':
            cooldown = self.cancelled['cooldown']
            nxt = NextPenalty(cooldown)
            lines = ('Odmítl jsi zápas.' if self.cancelled['declined'] else 'Na zápas jsi neodpověděl včas.',
                     'Trest fronty: %s' % Clock(max(0, int(queue[4])) if int(queue[0]) == QUEUE_COOLDOWN else 0),
                     ('Další odmítnutí %s; 24 h bez prohřešku = 30 s.' % PenaltyText(nxt)) if nxt else
                     '24 h bez prohřešku = znovu od 30 s.')
            colors = (INK, LOSS, MUTED)
        else:
            lines = ('Zápas byl zrušen.', '', '')
            colors = (INK, INK_DIM, MUTED)
        for line, text, color in zip(self.cancelLines, lines, colors):
            _Set(line, text, color)
        two = kind == 'requeue'
        if two:
            self.ok.SetPosition((READY_W - 96 * 2 - 10) // 2, self.ok.GetLocalPosition()[1])
            self.stopSearch.Show()
        else:
            self.ok.SetPosition((READY_W - 96) // 2, self.ok.GetLocalPosition()[1])
            self.stopSearch.Hide()
        if not self.IsShow():
            self.Show()
            self.SetTop()

    def __ShowOffer(self, ready):
        self.__View('offer')
        mode = int(ready[1])
        _Set(self.subtitle, '%s · %s · BO3' % (MODE_TITLE.get(mode, ''), MODE_NAME.get(mode, '')), INK_DIM)
        me = ''
        try:
            me = player.GetName()
        except Exception:
            pass
        participants = [tuple(pvpmatchmaking.GetReadyParticipant(i)) for i in range(int(ready[3]))]
        myTeam = 1
        localStatus = 0
        for pid, team, status, name in participants:
            if name == me:
                myTeam, localStatus = int(team), int(status)
        mine = [p for p in participants if int(p[1]) == myTeam]
        theirs = [p for p in participants if int(p[1]) != myTeam]
        accepted = sum(1 for p in participants if int(p[2]) == 1)
        if localStatus == 1:
            self.accepted, self.declining, self.pendingDecision = True, False, None
        elif localStatus == 2:
            self.accepted, self.declining, self.pendingDecision = False, True, None
        # A decision sent stays latched until the offer ends or the server reports it (one click, never twice).
        remaining = max(0, min(READY_SECONDS, int(ready[2]) - _Now()))
        _Load(self.ring, ART + 'timer_%02d.png' % remaining)
        _Set(self.seconds, str(remaining), IVORY)
        for slots, rows, named in ((self.mine, mine, True), (self.theirs, theirs, False)):
            for index, (tick, dots, name) in enumerate(slots):
                if index < len(rows):
                    ok = int(rows[index][2]) == 1
                    tick.Show() if ok else tick.Hide()
                    dots.Show() if not ok else dots.Hide()
                    name.Show()
                    _Set(name, rows[index][3] if named else 'Soupeř', IVORY if ok else INK_DIM)
                else:
                    tick.Hide()
                    dots.Hide()
                    name.Hide()
        _Set(self.ready, '%d / %d připraveno' % (accepted, len(participants)), IVORY if self.accepted else INK)
        if self.accepted or self.pendingDecision == 1:
            _Set(self.note, 'Přijato. Přesun do arény, až potvrdí všichni.', INK_DIM)
            _Button(self.accept, 'Přijato', False)
            _Button(self.decline, 'Odmítnout', False)
        elif self.declining or self.pendingDecision == 0:
            _Set(self.note, 'Odmítnuto.', INK_DIM)
            _Button(self.accept, 'Přijmout', False)
            _Button(self.decline, 'Odmítnout', False)
        else:
            _Set(self.note, 'Odmítnutí nebo neodpověď = trest fronty (od 30 s).', MUTED)
            _Button(self.accept, 'Přijmout', remaining > 0)
            _Button(self.decline, 'Odmítnout', remaining > 0)
        if not self.IsShow():
            self.Show()
            self.SetTop()

    def OnUpdate(self):
        now = app.GetTime()
        if now - self.lastRefresh >= 0.2:
            self.lastRefresh = now
            self.__TrySend()
            self.Refresh()
        for tick, dots, name in self.mine + self.theirs:
            dots.Step(now)


class MatchHud(ui.Window):
    """In-match HUD, top centre, 300 x 44 on the R1 tooltip frame (86 % fill): your team always LEFT (MatchState.team),
    the opponents right, the won rounds of BO3 as points, the round and time in the middle (the last 10 s in red,
    no blinking), the big red countdown while the round prepares; after the match 5 s "Výhra 2 : 1", then the
    result window."""

    def __init__(self, kit):
        ui.Window.__init__(self)
        self.kit = kit
        self.AddFlag('not_pick')
        self.SetSize(HUD_W, HUD_H)
        self.frame = uir1.Frame(self, 0, 0, HUD_W, HUD_H, 'tooltip')
        if self.frame.fill is not None:
            self.frame.fill.SetColor(uir1.GenerateColor(0x0C0B0C, HUD_FILL_ALPHA))
        self.mineLabel = _Text(self, 12, 7, INK_DIM, outline=True)
        self.mineLabel.SetText('Tvůj tým')
        self.minePips = Pips(self, 14, 27, 2, 8, 5)
        self.mineScore = _Text(self, 70, 12, IVORY, TAHB, align='center', outline=True)
        self.theirLabel = _Text(self, HUD_W - 12, 7, INK_DIM, align='right', outline=True)
        self.theirLabel.SetText('Soupeři')
        self.theirPips = Pips(self, HUD_W - 14 - 21, 27, 2, 8, 5)
        self.theirScore = _Text(self, HUD_W - 70, 12, IVORY, TAHB, align='center', outline=True)
        self.status = _Text(self, HUD_W // 2, 6, INK_DIM, align='center', outline=True)
        self.clock = _Text(self, HUD_W // 2, 22, IVORY, TAHB, align='center', outline=True)
        self.vein = uir1.Vein(self, HUD_W // 2 - 22, HUD_H - 4, 44)
        self.lastRefresh = 0.0
        self.resultMatchId = 0
        self.resultUntil = 0.0
        self.cachedResult = None
        self.teams = {}                   # matchId -> (team, mode), from MatchState
        self.resultDialog = None
        self.key = None
        ui.Window.Hide(self)

    def TeamOf(self, matchId):
        return self.teams.get(int(matchId), (0, 0))

    def Destroy(self):
        self.cachedResult = None
        self.resultUntil = 0.0
        ui.Window.Hide(self)

    def __Place(self):
        self.SetPosition((wndMgr.GetScreenWidth() - HUD_W) // 2, HUD_Y)
        if not self.IsShow():
            self.Show()
        self.SetTop()

    def __Draw(self, mine, theirs, status, clock, clockColor, vein):
        key = (mine, theirs, status, clock, clockColor, vein)
        if key == self.key:
            return
        self.key = key
        self.minePips.Set(mine)
        self.theirPips.Set(theirs)
        _Set(self.mineScore, str(mine), IVORY)
        _Set(self.theirScore, str(theirs), IVORY)
        _Set(self.status, status, INK_DIM)
        _Set(self.clock, clock, clockColor)
        _Visible(self.vein, vein)

    def Refresh(self):
        if not ArenaShown():
            self.cachedResult = None
            ui.Window.Hide(self)
            return
        now = app.GetTime()
        match = tuple(pvpmatchmaking.GetMatch())
        if int(match[8]) and int(match[0]):
            self.teams[int(match[0])] = (int(match[2]), int(match[1]))
            if len(self.teams) > 8:
                for old in sorted(self.teams)[:-8]:
                    del self.teams[old]
        result = tuple(pvpmatchmaking.GetResult())
        if (int(result[7]) and int(result[0]) and int(result[0]) != self.resultMatchId and
                int(result[0]) != _RESULT['seen']):
            self.resultMatchId = int(result[0])
            self.cachedResult = result
            self.resultUntil = now + RESULT_HUD_SECONDS
            team, mode = self.TeamOf(result[0])
            _KeepResult(result, team, mode)
        cached = self.cachedResult
        if cached is not None and now < self.resultUntil and (not int(match[8]) or int(match[0]) == int(cached[0])):
            team, unused = self.TeamOf(cached[0])
            mine, theirs = MyScore(cached[1], cached[6], cached[2], cached[3], team)
            text, color = Outcome(cached[1], cached[6], team)
            self.__Draw(mine, theirs, 'Zápas ukončen', '%s %d : %d' % (text, mine, theirs), color, False)
            self.__Place()
            return
        if cached is not None and now >= self.resultUntil and self.resultDialog is not None:
            pending = _RESULT['pending']
            if pending is not None and int(pending['result'][0]) == int(cached[0]):
                self.resultDialog.Present(pending['result'], pending['team'], pending['mode'])
            self.cachedResult = None
        if int(match[8]) and (cached is None or int(match[0]) != int(cached[0])):
            team = int(match[2])
            roundNumber = max(1, min(3, int(match[3])))
            seconds = max(0, int(match[6]))
            mine, theirs = (int(match[5]), int(match[4])) if team == 2 else (int(match[4]), int(match[5]))
            if int(match[7]):
                self.__Draw(mine, theirs, 'Kolo %d' % roundNumber, Clock(seconds),
                            RED_HI if seconds <= 10 else IVORY, True)
            elif seconds > 0:
                self.__Draw(mine, theirs, 'Kolo %d začíná' % roundNumber, str(seconds), RED_HI, False)
            else:
                self.__Draw(mine, theirs, 'Kolo %d' % roundNumber, 'Čeká se na hráče', INK, False)
            self.__Place()
            return
        ui.Window.Hide(self)

    def OnUpdate(self):
        now = app.GetTime()
        if now - self.lastRefresh >= 0.2:
            self.lastRefresh = now
            self.Refresh()


class ResultDialog(_Dialog):
    """NEW: the result after the 5 s in the HUD. VÝHRA / PROHRA / POSTUP (a new rank), the score, mode and season,
    the crest, "1 412 › 1 437 ELO" with the change, the rank track with the gain highlighted, "63 do Zlato I";
    Hrát znovu (the queue in the same mode) LEFT, Zavřít right. The player table is D5 (not sent)."""

    def __init__(self, kit, owner):
        _Dialog.__init__(self, kit, RESULT_W, RESULT_H, 'Výhra')
        self.owner = owner
        self.mode = 0
        y = self.top + 10
        self.subtitle = self.Center('', y, INK_DIM)
        y += 28
        self.crest = _Image(self, ASSET + 'rank_zlato_64.png', PAD + 4, y)
        tx = PAD + 80
        self.rankName = _Text(self, tx, y + 4, IVORY, TAHB)
        self.newRank = _Text(self, tx, y + 4, WIN)
        self.newRank.SetText('nový rank')
        self.ratings = _Text(self, tx, y + 22, INK)
        self.delta = _Text(self, RESULT_W - PAD, y + 22, WIN, TAHB, align='right')
        self.track = Track(self, tx, y + 44, RESULT_W - PAD - tx, 6)
        self.toNext = _Text(self, tx, y + 54, MUTED)
        y += 64 + 12
        bx = (RESULT_W - 2 * 120 - 10) // 2
        self.again = uir1.Button(self, kit, bx, y, 120, 'Hrát znovu', primary=True, event=self.PlayAgain)
        self.close = uir1.Button(self, kit, bx + 130, y, 120, 'Zavřít', event=self.Close)
        ui.Window.Hide(self)

    def Present(self, result, team, mode):
        """result: GetResult() of the finished match; team / mode from its MatchState (0 = unknown)."""
        if not ArenaShown():
            return
        outcome, before, after, delta = int(result[1]), int(result[4]), int(result[5]), int(result[6])
        text, color = Outcome(outcome, delta, team)
        rankBefore, rankAfter = Rank(before), Rank(after)
        promoted = delta > 0 and rankAfter['name'] != rankBefore['name']
        self.chrome.SetTitle('Postup' if promoted else text)
        mode = int(mode) or int(tuple(pvpmatchmaking.GetQueue())[1])
        self.mode = mode if mode in MODE_NAME else 0
        snapshot = tuple(pvpmatchmaking.GetSnapshot())
        mine, theirs = MyScore(outcome, delta, result[2], result[3], team)
        parts = ['%d : %d' % (mine, theirs)]
        if self.mode:
            parts.append('%s %s' % (MODE_TITLE[self.mode], MODE_NAME[self.mode]))
        if int(snapshot[0]):
            parts.append('Sezóna %d' % int(snapshot[0]))
        _Set(self.subtitle, '  ·  '.join(parts), INK_DIM)
        _Load(self.crest, ASSET + 'rank_%s_64.png' % rankAfter['art'])
        _Set(self.rankName, rankAfter['name'], IVORY)
        self.newRank.SetPosition(PAD + 80 + uir1.TextWidth(self.rankName) + 8, self.rankName.GetLocalPosition()[1])
        _Visible(self.newRank, promoted)
        _Set(self.ratings, '%s › %s ELO' % (Number(before), Number(after)), INK)
        _Set(self.delta, '%+d' % delta, WIN if delta > 0 else (LOSS if delta < 0 else INK_DIM))
        lo, hi = rankAfter['lo'], rankAfter['hi']
        span = float((hi if hi is not None else max(after, lo + 1)) - lo) or 1.0
        a = max(0.0, (min(before, after) - lo) / span)
        b = max(0.0, (max(before, after) - lo) / span)
        if delta > 0:
            self.track.Set(a, (a, b))
        else:
            self.track.Set(b)
        _Set(self.toNext, '%d do %s' % (hi - after, rankAfter['next']) if hi is not None else 'Nejvyšší rank', MUTED)
        _Button(self.again, 'Hrát znovu', bool(self.mode) and not _CommandPending())
        self.Open()

    def PlayAgain(self):
        if self.mode and self.owner.PlayAgain(self.mode):
            self.Close()

    def Close(self):
        """Closed by the player (Zavřít, Esc, Hrát znovu): the kept result is done. Destroy (the interface rebuild of
        a warp) keeps it for the next window."""
        _DropResult()
        ui.Window.Hide(self)

    def Refresh(self):
        if self.IsShow() and not ArenaShown():
            ui.Window.Hide(self)


class WarriorsDialog(_Dialog):
    """Válečníci (owner V1): the leader names members who may challenge and queue without the leader or the
    council. The list comes from GuildArenaWarriorsV1."""

    ROWS = 5

    def __init__(self, kit, window):
        h = 29 + 10 + 18 + 8 + self.ROWS * LINE + 10 + T.FIELD_H + 12 + T.BTN_H + 12
        _Dialog.__init__(self, kit, 300, h, 'Válečníci')
        self.window = window
        y = self.top + 10
        self.note = _Text(self, PAD, y, MUTED)
        self.note.SetText('Smí vyzývat cechy a hledat arénu.')
        y += 26
        self.rows = []
        for i in range(self.ROWS):
            name = _Text(self, PAD + 4, y + i * LINE + 3, INK)
            remove = Link(self, self.w - PAD, y + i * LINE + 3, 'odebrat', lambda i=i: self.Remove(i))
            self.rows.append((name, remove))
        self.empty = _Text(self, self.w // 2, y + 40, MUTED, align='center')
        self.empty.SetText('Zatím nikdo.')
        y += self.ROWS * LINE + 10
        self.name = uir1.Field(self, kit, PAD, y, self.w - 2 * PAD - 96 - 8, 'Jméno člena', max_len=24)
        self.add = uir1.Button(self, kit, self.w - PAD - 96, y - 1, 96, 'Přidat', primary=True, small=True,
                               event=self.Add)
        y += T.FIELD_H + 12
        self.close = uir1.Button(self, kit, (self.w - 110) // 2, y, 110, 'Zavřít', event=self.Close)
        self.names = []
        self.Hide()

    def Add(self):
        name = guildarena.CleanName(self.name.edit.GetText())
        if name:
            guildarena.SetWarrior(name, True)
            self.name.edit.SetText('')
            self.window.GuildPollSoon()

    def Remove(self, index):
        if index < len(self.names):
            guildarena.SetWarrior(self.names[index], False)
            self.window.GuildPollSoon()

    def Refresh(self):
        self.names = guildarena.Warriors()
        for i, (name, remove) in enumerate(self.rows):
            shown = i < len(self.names)
            _Visible(name, shown)
            _Visible(remove, shown)
            if shown:
                _Set(name, self.names[i], INK)
        _Visible(self.empty, not self.names)
