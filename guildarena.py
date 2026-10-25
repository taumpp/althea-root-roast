# -*- coding: utf-8 -*-
"""Guild wars and the guild arena queue (tab "Cechy" of the arena window).

The server (its guild war arena command) answers "/guild_arena status" and every change of
the queue or of a war with one command line:

  GuildArenaV1 gid level members online avgLevel win draw loss canLead queueMode queueSeconds
               warState warMode oppName myScore oppScore minMembers

warState 0 none, 1 we declared (waiting for them), 2 they declared to us, 3 starting, 4 at war; warMode 0 field,
1 battle, 2 flag, 5 / 10 the arena queue. The commands go out as chat commands (/guild_arena, /war, /nowar), the
same ones the old guild window used; nothing new in the EXE. The tab is locked (uipvpmatchmakingr1.GuildArenaOpen)
while the server keeps guild_arena or ranked_arena paused (FeatureAvailabilityV1); no command is sent then.
"""
import app
import net

FIELDS = ('gid', 'level', 'members', 'online', 'avg', 'win', 'draw', 'loss', 'lead', 'queueMode', 'queueSeconds',
          'warState', 'warMode', 'opp', 'myScore', 'oppScore', 'minMembers')
# added 12. 10. after the owner's answers (role: 0 member, 1 Válečník, 2 rada, 3 vůdce; Meley V9 B); an older server
# sends only FIELDS, these then keep their defaults
EXTRA = (('role', 0), ('meleyOpen', 0), ('meleyLevel', 0), ('meleyFree', 1), ('meleyRegistered', 0), ('near', 0),
         ('nearNeed', 4))
ROLE_NAME = {0: 'Člen', 1: 'Válečník', 2: 'Rada', 3: 'Vůdce'}
TEXT_FIELDS = ('opp',)

WAR_NONE, WAR_SENT, WAR_RECEIVED, WAR_STARTING, WAR_ON = 0, 1, 2, 3, 4
WAR_FIELD, WAR_BATTLE = 0, 1
QUEUE_MODES = (5, 10, 15)
WAR_MODE = 0                         # the challenge "Válka": battle map without a team cap (classic battle war)
CHALLENGE_MODES = (5, 10, 15, WAR_MODE)
# The server's guild war table: ARENA5 / 10 / 15 = first to 30 / 50 / 70 kills, 20 min
QUEUE_RULES = {5: (30, 20), 10: (50, 20), 15: (70, 20)}

_STATE = dict(data=None, at=0.0, requested=0.0, warriors=[])


def Parse(tokens):
    """dict of the fields of one GuildArenaV1 line (without the command word); None when it is malformed."""
    tokens = list(tokens)
    if len(tokens) < len(FIELDS):
        return None
    data = {}
    try:
        for key, value in zip(FIELDS, tokens):
            data[key] = value if key in TEXT_FIELDS else int(value)
    except ValueError:
        return None
    for (key, default), value in zip(EXTRA, tokens[len(FIELDS):]):
        try:
            data[key] = int(value)
        except ValueError:
            data[key] = default
    for key, default in EXTRA:
        data.setdefault(key, default)
    if data['opp'] == '-':
        data['opp'] = ''
    return data


def ReceiveWarriors(tokens):
    """GuildArenaWarriorsV1 name name ...: the members the leader made Válečník."""
    _STATE['warriors'] = [name for name in tokens if name][:20]
    return True


def Warriors():
    return list(_STATE['warriors'])


def Receive(tokens, now=None):
    data = Parse(tokens)
    if data is None:
        return False
    _STATE['data'] = data
    _STATE['at'] = app.GetTime() if now is None else now
    return True


def Get(now=None):
    """The last state (None before the first answer); queueSeconds runs on locally between the answers."""
    data = _STATE['data']
    if data is None:
        return None
    data = dict(data)
    if data['queueMode']:
        now = app.GetTime() if now is None else now
        data['queueSeconds'] += max(0, int(now - _STATE['at']))
    return data


def Reset():
    _STATE['data'] = None
    _STATE['at'] = 0.0
    _STATE['warriors'] = []


def _Send(command):
    try:
        return bool(net.SendChatPacket(command))
    except Exception:
        return False


def Request(now=None, every=5.0):
    """"/guild_arena status", at most once per `every` seconds."""
    now = app.GetTime() if now is None else now
    if now - _STATE['requested'] < every:
        return False
    _STATE['requested'] = now
    return _Send('/guild_arena status')


def Queue(mode):
    return _Send('/guild_arena queue %d' % int(mode))


def Leave():
    return _Send('/guild_arena leave')


def CleanName(name):
    """A guild name as the server finds it (one word, no command characters)."""
    name = (name or '').strip()
    for bad in (' ', '\t', '/', '\\'):
        name = name.replace(bad, '')
    return name[:24]


def Challenge(name, mode):
    """Výzva: 5 / 10 / 15 = aréna se stropem hráčů, 0 = válka na mapě bez stropu."""
    name = CleanName(name)
    if not name or int(mode) not in CHALLENGE_MODES:
        return False
    return _Send('/guild_arena challenge %s %d' % (name, int(mode)))


def Accept(name):
    name = CleanName(name)
    return bool(name) and _Send('/guild_arena accept %s' % name)


def Refuse(name):
    name = CleanName(name)
    return bool(name) and _Send('/guild_arena refuse %s' % name)


def Meley():
    return _Send('/guild_arena meley')


def SetWarrior(name, on):
    name = CleanName(name)
    return bool(name) and _Send('/guild_arena warrior %s %d' % (name, 1 if on else 0))


def WarModeName(mode):
    return {0: 'pole', 1: 'válka', 2: 'vlajka', 5: '5v5', 10: '10v10', 15: '15v15'}.get(int(mode), '')


def ModeLabel(mode):
    return 'Válka' if int(mode) == WAR_MODE else '%dv%d' % (int(mode), int(mode))


def WarLine(data):
    """(title, detail, kind) of the war card; kind: 'idle', 'sent', 'received', 'starting', 'war'."""
    state, opp = int(data['warState']), data['opp'] or '?'
    mode = WarModeName(data['warMode'])
    if state == WAR_SENT:
        return ('Výzva odeslána: %s' % opp, '%s · čeká se na jejich odpověď' % mode, 'sent')
    if state == WAR_RECEIVED:
        return ('%s vás vyzývá na %s' % (opp, mode), 'Odpovídá vůdce, rada nebo válečník.', 'received')
    if state == WAR_STARTING:
        return ('%s proti %s' % (mode.capitalize(), opp), 'Zápas začne do minuty, přijde pozvánka.', 'starting')
    if state == WAR_ON:
        rules = QUEUE_RULES.get(int(data['warMode']))
        detail = 'do %d zabití' % rules[0] if rules else 'bez stropu hráčů'
        return ('%s proti %s' % (mode.capitalize(), opp), detail, 'war')
    return ('', '', 'idle')


def QueueNeed(mode, data):
    """Online members the mode needs (the server lowers it to 1 only with the test flag; it rejects the rest)."""
    return int(mode)
