# -*- coding: utf-8 -*-
"""Duel challenges as a chat line and as rows in Messages (Zprávy).

The native PVP state drives invitations, acceptance, expiry and revenge.
Declining closes only this client's invitation because the server has no
refusal command. Chat and Messages share the same invitation state.
"""
import re
import time

# pvp.cpp:833: deleted when (now - last fight time) > 600000 ms.
SERVER_REQUEST_LIFETIME_SECONDS = 600.0
# The client counts from the whisper (after the server created the request);
# the margin keeps "Vypršelo" strictly after the server's deletion.
EXPIRY_MARGIN_SECONDS = 1.0
EXPIRY_SECONDS = SERVER_REQUEST_LIFETIME_SECONDS + EXPIRY_MARGIN_SECONDS
# Entering the game (login, warp) replays every CPVP state of the player
# (CPVPManager::SendList, input_login.cpp:1768); no new rows from that burst.
ENTER_GAME_QUIET_SECONDS = 3.0

ACCEPT = "accept"
DECLINE = "decline"
LABELS = ((ACCEPT, u"[Přijmout]"), (DECLINE, u"[Odmítnout]"))
BUTTON_TEXTS = {ACCEPT: u"Přijmout", DECLINE: u"Odmítnout"}
ACTIVE_COLORS = {ACCEPT: "|cFF8FD47A", DECLINE: "|cFFE0605C"}
INACTIVE_COLOR = "|cFF6F6A63"
LINE_COLOR = "|cFFE1C594"
# locale_string "%s님이 대결신청을 했습니다. 승낙하려면 대결동의를 하세요." (cz, en).
CHALLENGE_TEXTS = (u"%s tě vyzval na souboj!", u"%s challenged you to a battle!")
# locale_string "%s에게 대결신청을 했습니다." (cz).
OUTGOING_TEXT = u"Vyzval jsi %s na souboj."
LINK = re.compile(r"^duel:(accept|decline):([0-9]{1,9})$")
STATE_ACTIVE = "active"
STATE_EXPIRED = "expired"
STATE_TEXTS = {
    "accepted": u"Přijato",
    "declined": u"Odmítnuto",
    STATE_EXPIRED: u"Vypršelo",
    "ended": u"Ukončeno",          # the fight ended without a result (server idle timeout)
    "superseded": u"Nahrazeno",    # the same player challenged again
}
WAITING_TEXT = u"Čeká na odpověď"

# The result row of an ended duel (see result_body).
RESULT_SENDER = u"Souboj"
# A server result (DuelResultV1) arrives before the REVENGE packet of the same
# death; the client-only result of that death is then skipped.
SERVER_RESULT_WINDOW_SECONDS = 30.0

# Phases of one opponent, from the PVP flags.
PHASE_INCOMING = "incoming"
PHASE_OUTGOING = "outgoing"
PHASE_FIGHT = "fight"
PHASE_WON = "won"
PHASE_LOST = "lost"


def format_number(value):
    """12345 -> "12 345" (Czech thousands, a plain space the game font has)."""
    digits = str(int(value))
    sign = "-" if digits.startswith("-") else ""
    digits = digits.lstrip("-")
    groups = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return sign + " ".join(groups or ["0"])


def format_duration(seconds):
    seconds = max(0, int(round(float(seconds))))
    return u"%d:%02d" % (seconds // 60, seconds % 60)


def result_body(winner, damages=(), winner_hp=None, duration=None):
    """The text of a duel result row; only the parts actually known.
    damages: ((name, damage), ...); winner_hp: (hp, max_hp); duration: s."""
    lines = [u"Vítěz: %s" % winner]
    if damages:
        lines.append(u"Poškození: " + u", ".join(
            u"%s %s" % (name, format_number(damage)) for name, damage in damages))
    if winner_hp:
        hp, maximum = int(winner_hp[0]), int(winner_hp[1])
        if maximum > 0:
            percent = int(round(100.0 * max(0, hp) / maximum))
            lines.append(u"HP vítěze: %s / %s (%d %%)" % (
                format_number(max(0, hp)), format_number(maximum), percent))
    if duration is not None and float(duration) > 0:
        lines.append(u"Délka: %s" % format_duration(duration))
    return u"[ENTER]".join(lines)


def parse_link(link):
    match = LINK.match(str(link or ""))
    if not match:
        return None, 0
    return match.group(1), int(match.group(2))


def is_player_name(name):
    name = str(name or "")
    return 0 < len(name) <= 24 and not name.startswith("[") and not re.search(r"[\s|:]", name)


# chr.GetNameByVID returns the text "None" for a VID this client does not
# cannot resolve.
UNKNOWN_NAME = "None"


def known_name(name):
    """The name, or "" when it is not a resolved player name."""
    name = str(name or "")
    return name if is_player_name(name) and name != UNKNOWN_NAME else ""


class Challenges(object):
    def __init__(self, clock=time.time):
        self.clock = clock
        self.Clear()

    def Clear(self):
        self.rows = {}
        self.vids = {}
        self.phases = {}
        self.nextID = 1
        self.revision = 0
        self.enteredAt = None
        self.fightStarted = {}
        self.serverResults = {}

    # ------------------------------------------------------------- server state
    def EnterGame(self):
        """The game window opened (login or warp): the server replays states."""
        self.enteredAt = float(self.clock())

    def __Quiet(self):
        return (self.enteredAt is not None and
                float(self.clock()) - self.enteredAt < ENTER_GAME_QUIET_SECONDS)

    def __KeyForVid(self, vid):
        for key, known in self.vids.items():
            if known == vid:
                return key
        return ""

    def Observe(self, vid, name, challenged, waiting=False, revenge=False, fighting=False):
        """A PVP packet refreshed the target board of `vid` (not the player).

        challenged: player.IsChallengeInstance (`vid` challenged me, pending);
        waiting: player.IsCantFightInstance (I challenged `vid` and wait, or I
        won against `vid`); revenge: player.IsRevengeInstance (`vid` won
        against me); fighting: player.IsPVPInstance (the fight is on).
        Returns events for the interface: ("outgoing", name, identifier),
        ("fight", name), ("result", name, won)."""
        vid = int(vid or 0)
        # A VID the client does not see has no name yet: no row is made for
        # it (the request of a player out of sight after a relog, say).
        name = known_name(name)
        key = name.lower() or self.__KeyForVid(vid)
        if not key:
            return []
        known = self.__NameOf(key, name)
        if vid:
            self.vids[key] = vid
        previous = self.phases.get(key)
        events = []
        if fighting:
            if previous != PHASE_FIGHT:
                self.phases[key] = PHASE_FIGHT
                self.fightStarted[key] = float(self.clock())
                self.__ResolveName(key, "accepted")
                events.append(("fight", known))
        elif challenged:
            self.phases[key] = PHASE_INCOMING
        elif revenge:
            # Only CPVP::Win sends REVENGE: `vid` killed me in the fight.
            if previous != PHASE_LOST:
                self.phases[key] = PHASE_LOST
                self.__ResolveName(key, "accepted")
                if not self.__Quiet():
                    events.append(("result", known, False))
        elif waiting:
            if previous in (PHASE_FIGHT, PHASE_INCOMING):
                # After a fight (seen or not: `vid` challenged me, so this is
                # not my own request) only CPVP::Win sets it: I won.
                self.phases[key] = PHASE_WON
                self.__ResolveName(key, "accepted")
                if not self.__Quiet():
                    events.append(("result", known, True))
            elif previous in (PHASE_OUTGOING, PHASE_WON):
                pass
            elif name and not self.__Quiet():
                self.phases[key] = PHASE_OUTGOING
                events.append(("outgoing", known, self.Add(known, outgoing=True)))
        else:
            # Every flag cleared: mode NONE (the server deleted the CPVP) or a
            # fight this client cannot see. Only the server lifetime proves
            # that a request is gone.
            if previous == PHASE_FIGHT:
                del self.phases[key]
                self.__ResolveName(key, "ended")
            elif previous in (PHASE_INCOMING, PHASE_OUTGOING):
                if self.__ExpireName(key):
                    del self.phases[key]
            elif previous is not None:
                del self.phases[key]
        return events

    # ------------------------------------------------------------- results
    def FightSeconds(self, name):
        """Seconds since this client saw the fight start (PVP mode FIGHT, after
        the countdown), None when it did not see it."""
        started = self.fightStarted.pop(str(name or "").lower(), None)
        return None if started is None else float(self.clock()) - started

    def RecordServerResult(self, name):
        self.serverResults[str(name or "").lower()] = float(self.clock())
        self.fightStarted.pop(str(name or "").lower(), None)

    def HasServerResult(self, name):
        at = self.serverResults.get(str(name or "").lower())
        return at is not None and float(self.clock()) - at < SERVER_RESULT_WINDOW_SECONDS

    def __NameOf(self, key, name):
        if name:
            return str(name)
        for row in self.rows.values():
            if row["name"].lower() == key:
                return row["name"]
        return key

    def VidFor(self, name):
        return self.vids.get(str(name or "").lower(), 0)

    def IsChallengeWhisper(self, name, line):
        if not is_player_name(name):
            return False
        # The server sends the challenge whisper once, right after the AGREE
        # packet of a new request. Any later system whisper of a pending
        # challenger (e.g. "has blocked you") stays an ordinary whisper.
        if self.phases.get(str(name).lower()) == PHASE_INCOMING and not self.Pending(name):
            return True
        text = str(line or "").strip()
        return any(text == template % name for template in CHALLENGE_TEXTS)

    # ------------------------------------------------------------- rows
    def Pending(self, name, outgoing=False):
        """Answerable challenges of `name` (a new one replaces them)."""
        key = str(name or "").lower()
        return [identifier for identifier, row in sorted(self.rows.items())
                if row["name"].lower() == key and row["outgoing"] == bool(outgoing)
                and self.IsActive(identifier)]

    def Add(self, name, outgoing=False):
        self.__ResolveName(str(name).lower(), "superseded", outgoing)
        identifier = self.nextID
        self.nextID += 1
        self.rows[identifier] = {"name": str(name), "at": float(self.clock()),
                                 "state": STATE_ACTIVE, "unread": False,
                                 "outgoing": bool(outgoing)}
        # Bounded: old lines only need to render as inactive.
        for old in sorted(self.rows)[:-64]:
            del self.rows[old]
        self.revision += 1
        return identifier

    def Get(self, identifier):
        return self.rows.get(int(identifier))

    def IsOutgoing(self, identifier):
        row = self.Get(identifier)
        return bool(row and row["outgoing"])

    def IsActive(self, identifier):
        return self.State(identifier) == STATE_ACTIVE

    def State(self, identifier):
        """"active", "expired" (the server has deleted the request) or how it
        ended; None for an unknown (or long forgotten) challenge."""
        row = self.Get(identifier)
        if not row:
            return None
        if row["state"] == STATE_ACTIVE and self.__PastLifetime(row):
            return STATE_EXPIRED
        return row["state"]

    def __PastLifetime(self, row):
        return float(self.clock()) - row["at"] >= EXPIRY_SECONDS

    def StatusText(self, identifier):
        """The grey text that replaces the actions of an answered challenge."""
        if self.IsActive(identifier):
            return WAITING_TEXT if self.IsOutgoing(identifier) else u""
        return STATE_TEXTS.get(self.State(identifier), u"")

    def Resolve(self, identifier, state):
        if self.IsActive(identifier):
            self.Get(identifier)["state"] = state
            self.revision += 1
            return True
        return False

    def __ResolveName(self, key, state, outgoing=None):
        for identifier, row in self.rows.items():
            if row["state"] != STATE_ACTIVE or row["name"].lower() != key:
                continue
            if outgoing is not None and row["outgoing"] != bool(outgoing):
                continue
            # One that already ran out keeps saying so.
            row["state"] = state if self.IsActive(identifier) else STATE_EXPIRED
            row["unread"] = row["unread"] and row["state"] != "superseded"
            self.revision += 1

    def __ExpireName(self, key):
        """The NONE packet: expire the requests the server has deleted. A
        younger request is still alive on the server (the flags were cleared
        for another reason), so it stays answerable."""
        pending = [row for row in self.rows.values()
                   if row["state"] == STATE_ACTIVE and row["name"].lower() == key]
        if any(float(self.clock()) - row["at"] < SERVER_REQUEST_LIFETIME_SECONDS for row in pending):
            return False
        for row in pending:
            row["state"] = STATE_EXPIRED
            self.revision += 1
        return True

    # ------------------------------------------------------- Messages unread
    # The thread's unread badge in Messages (and the friends / chat badges that
    # add the local history's unread count) counts challenges not yet seen.
    def MarkUnread(self, identifier):
        row = self.Get(identifier)
        if row:
            row["unread"] = True

    def MarkRead(self, name=None, identifiers=None):
        """Marks the challenges of `name` (all when None, or just
        `identifiers`) as read; returns how many changed."""
        key = None if name is None else str(name).lower()
        changed = 0
        for identifier, row in self.rows.items():
            if not row["unread"] or (key is not None and row["name"].lower() != key):
                continue
            if identifiers is not None and identifier not in identifiers:
                continue
            row["unread"] = False
            changed += 1
        return changed

    def UnreadCount(self, name=None):
        key = None if name is None else str(name).lower()
        return sum(1 for row in self.rows.values()
                   if row["unread"] and (key is None or row["name"].lower() == key))

    def Revision(self):
        """Changes whenever a line's links change, including by expiry."""
        expired = sum(1 for row in self.rows.values()
                      if row["state"] == STATE_ACTIVE and self.__PastLifetime(row))
        return (self.revision, expired)

    # ------------------------------------------------------------- chat line
    def ChatLine(self, identifier, name):
        links = " ".join("|Hduel:%s:%d|h%s|h" % (action, identifier, label)
                         for action, label in LABELS)
        return u"%sSouboj s %s:|r %s" % (LINE_COLOR, name, links)

    def RenderLink(self, payload, label):
        """A duel link of a chat line: coloured while active; afterwards the
        [Přijmout] place shows the grey state and [Odmítnout] disappears."""
        action, identifier = parse_link(payload)
        if not action or self.IsOutgoing(identifier):
            return label
        if self.IsActive(identifier):
            return "%s|H%s|h%s|h|r" % (ACTIVE_COLORS[action], payload, label)
        if action == DECLINE:
            return ""
        return "%s%s|r" % (INACTIVE_COLOR, self.StatusText(identifier) or label)


challenges = Challenges()
