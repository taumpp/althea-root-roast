# -*- coding: utf-8 -*-
"""Detect consumed dungeon tickets after a settled map change.

Automatic ticket grants are suppressed as pickup notices during a pending entry.
State survives a game-window rebuild during warp, expires after ENTRY_TTL and
is discarded when a different character owns the game session. An authoritative
DungeonTicketUsed command ends the estimate to prevent duplicate notices.
"""

CONTEXT_DUNGEON = 'dungeon'

ENTRY_TTL = 45.0            # seconds from the click on "Vstoupit" until the entry is forgotten
SETTLE_SECONDS = 0.8        # the ticket count must stay the same this long on the new map
MAX_COUNT = 200             # d.new_jump_paid refuses more than 200 tickets


def _Int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def Tickets(rows):
    """[(vnum, count), ...] of a dungeon catalog 'ticket' value ([[30179, 1]]); invalid rows are left out."""
    tickets = []
    for row in rows or ():
        try:
            vnum, count = _Int(row[0]), _Int(row[1])
        except (TypeError, IndexError, KeyError):
            continue
        if 0 < vnum <= 0xFFFFFFFF and 0 < count <= MAX_COUNT and vnum not in [t[0] for t in tickets]:
            tickets.append((vnum, count))
    return tickets


class TicketEntry(object):
    def __init__(self):
        self.Reset()

    def Reset(self):
        self.pending = None

    def Pending(self):
        return self.pending is not None

    # ----------------------------------------------------------------- the client's own detection
    def BeginEntry(self, ticketRows, countOf, mapName, now, owner=None):
        """The player asked the dungeon window to enter. ``countOf(vnum)`` = the ticket count in the inventory."""
        tickets = Tickets(ticketRows)
        if not tickets:
            self.pending = None
            return False
        rows = {}
        for vnum, unusedCount in tickets:
            count = max(0, _Int(countOf(vnum)))
            rows[vnum] = {'base': count, 'granted': 0, 'last': count}
        self.pending = {'rows': rows, 'map': mapName, 'started': float(now), 'changed': float(now), 'owner': owner}
        return True

    def _Live(self, now):
        if self.pending is None:
            return False
        if float(now) - self.pending['started'] > ENTRY_TTL:
            self.pending = None
            return False
        return True

    def OnGain(self, vnum, count, now):
        """A pickup notice ("DropInfo"). True: it is the auto ticket of the entry - do not show it as a pickup."""
        if not self._Live(now):
            return False
        row = self.pending['rows'].get(_Int(vnum))
        count = _Int(count)
        if row is None or count <= 0:
            return False
        row['granted'] += count
        return True

    def Poll(self, countOf, mapName, now, owner=None):
        """Called every frame of the game. Returns [] or the notices [(vnum, used, CONTEXT_DUNGEON)] once."""
        if not self._Live(now):
            return []
        pending = self.pending
        if pending['owner'] is not None and owner != pending['owner']:
            self.Reset()
            return []
        for vnum, row in pending['rows'].items():
            count = max(0, _Int(countOf(vnum)))
            if count != row['last']:
                row['last'] = count
                pending['changed'] = float(now)
        if mapName == pending['map'] or float(now) - pending['changed'] < SETTLE_SECONDS - 1e-6:
            return []
        notices = []
        for vnum in sorted(pending['rows']):
            row = pending['rows'][vnum]
            used = row['base'] + row['granted'] - row['last']
            if used > 0:
                notices.append((vnum, min(used, MAX_COUNT), CONTEXT_DUNGEON))
        if notices:
            self.pending = None
        # Nothing used yet: a deferred auto ticket is taken only after the arrival - keep waiting until ENTRY_TTL.
        return notices

    # ----------------------------------------------------------------- the server's word
    def OnServerUsed(self, vnum, count, now):
        """``DungeonTicketUsed <vnum> <count>``: the notice, and the client's own entry is done (no second one)."""
        vnum, count = _Int(vnum), _Int(count)
        if not (0 < vnum <= 0xFFFFFFFF and 0 < count <= MAX_COUNT):
            return None
        self.pending = None
        return (vnum, count, CONTEXT_DUNGEON)


STATE = TicketEntry()
