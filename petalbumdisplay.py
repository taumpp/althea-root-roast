# -*- coding: utf-8 -*-
"""Read-only album display arithmetic and per-character discovery journal.

The journal controls badges/reveals only. It cannot grant pets, XP or bonuses.
"""
import builtins
import hashlib
import json
import os


_DISK_OPEN = getattr(builtins, 'old_open', builtins.open)

def Number(value):
    text = ('%.2f' % value).rstrip('0').rstrip('.')
    whole, dot, fraction = text.partition('.')
    whole = format(int(whole), ',').replace(',', ' ')
    return whole + (',' + fraction if dot else '')


def LevelProgress(row, projection, units_per_xp):
    """Project the server's integer thresholds within the current level."""
    thresholds = projection['level_growth_thresholds']
    level = row['level']
    if level >= len(thresholds):
        return 0.0, 0.0, 1.0, True
    start, end = thresholds[level-1:level+1]
    earned = max(0, min(end-start, row['growth']-start))
    factor = projection['legacy_growth_factor'] / float(units_per_xp)
    return earned*factor, (end-start)*factor, earned/float(end-start), False


def Percent(value):
    return ('%.2f' % (value / 1000000.0)).replace('.', ',')


def Schedule(schedule, words):
    days, windows = schedule['weekdays'], schedule['windows']
    if days == list(range(1, 8)) and windows == [[0, 1440]]:
        return words['anytime'], [], False
    names = words['weekdays'].split('|')
    label = words['everyday'] if len(days) == 7 else ' | '.join(names[d-1] for d in days)
    if windows == [[0, 1440]]:
        return label, [words['whole_day']], False
    def clock(minute):
        return '%d:%02d' % (minute // 60, minute % 60)
    return label, [clock(a) + '-' + clock(b % 1440 if b > 1440 else b) + ('¹' if b > 1440 else '')
                   for a, b in windows], any(b > 1440 for a, b in windows)


def TargetName(pool, row, fallback):
    # The server selected a real pool actor. Never infer it from the pet species.
    exact = [item for item in pool if item['map'] == row['map'] and item['vnum'] == row['vnum']
             and item['direction'] == row['direction']]
    if not exact:
        exact = [item for item in pool if item['map'] == row['map'] and item['vnum'] == row['vnum']]
    return exact[0]['name'] if exact else fallback


def Location(row, pool, words):
    direction = row['direction'].strip().rstrip('.')
    matching = [h for h in pool if h['map'] == row['map'] and h['direction'] == row['direction']]
    if matching:
        direction = matching[0].get('place', direction)
    if row.get('shared_hub'):
        return words['hub'] % direction
    template = words['channel'] if row.get('channel') else words['place']
    # Direction is already a server-authored map description (e.g. jih Údolí orků).
    return template % (direction, row['channel']) if row.get('channel') else template % direction


def GrowthRows(targets, offset, wrap):
    rows, y = [], 252
    for target in targets[offset:]:
        names = wrap(target['name'], 174, 12, True)
        meta = wrap(target['location'] + ' | ' + target['days'], 262, 11, False)
        height = len(names)*14 + len(meta)*13 + 7
        if rows and y + height > 350:
            break
        rows.append((target, y, names, meta))
        y += height
        if len(rows) == 3:
            break
    return rows


class Journal(object):
    def __init__(self, directory='UserData/pet-album'):
        self.directory = directory
        self.key = None
        self.entries = {}
        self.path = None

    def Bind(self, character, context):
        if not character or not context:
            return False
        key = (str(character), context[0], context[2])
        if key == self.key:
            return True
        self.key, self.entries = key, {}
        name = hashlib.sha256(json.dumps(key, ensure_ascii=True).encode('ascii')).hexdigest() + '.json'
        self.path = os.path.join(self.directory, name)
        try:
            with _DISK_OPEN(self.path, 'r') as stream:
                value = json.load(stream)
            if value.get('key') == list(key) and isinstance(value.get('entries'), dict):
                self.entries = value['entries']
        except (OSError, ValueError, TypeError):
            pass
        return True

    def Save(self):
        if not self.path:
            return
        try:
            os.makedirs(self.directory, exist_ok=True)
            temporary = self.path + '.tmp'
            with _DISK_OPEN(temporary, 'w') as stream:
                json.dump({'key': self.key, 'entries': self.entries}, stream, ensure_ascii=True)
            os.replace(temporary, self.path)
        except OSError:
            # An unavailable local presentation file must never block gameplay.
            pass

    def Sync(self, rows, receipts=None):
        changed = False
        receipts = receipts or {}
        for identity, row in rows.items():
            phase = row['phase']
            signature = [phase]
            if phase == 1:
                signature += [row['hunt_high'], row['hunt_low']]
            old = self.entries.get(identity)
            receipt = receipts.get(identity)
            new_event = receipt is not None and (not isinstance(old, dict) or old.get('receipt') != receipt)
            if not isinstance(old, dict) or old.get('signature') != signature or new_event:
                self.entries[identity] = {'signature': signature, 'read': phase == 0, 'receipt': receipt if receipt is not None else (old or {}).get('receipt')}
                changed = True
        if changed:
            self.Save()
        return changed

    def Unread(self, identity):
        entry = self.entries.get(identity, {})
        return bool(entry and not entry.get('read', True))

    def Read(self, identity):
        if self.Unread(identity):
            self.entries[identity]['read'] = True
            self.Save()

_journal = Journal()
def GetJournal():
    return _journal
