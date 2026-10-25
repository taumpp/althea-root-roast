"""Atomic, session-owned native wiki catalogue. No packaged gameplay fallback."""
import binascii
import json
import time
import heapq
from collections import deque
import codecs
import wikijson
try:
    import app
    _native_checksum = getattr(app, 'UpdateWikiChecksum', None)
except ImportError:
    _native_checksum = None
try:
    import zlib
except ImportError:
    zlib = None
from marketfilters import folded

MAX_BYTES = 2 * 1024 * 1024
PART_BYTES = 160
MAX_SCOPE_BYTES = 384
# Keep the elapsed-time allowance authoritative even for very cheap tokens.
MAX_PUMP_STEPS = 8192


_active_receiver = None


def BindDungeonReceiver(receiver):
    """Share the wiki's one session/nonce stream; never request a second one."""
    global _active_receiver
    _active_receiver = receiver


def UnbindDungeonReceiver(receiver):
    global _active_receiver
    if _active_receiver is receiver:
        _active_receiver = None


def DungeonElements(boss):
    catalog = _active_receiver.catalog if _active_receiver is not None else None
    return catalog.dungeon_elements.get(boss, ()) if catalog is not None else ()


def MobDrops(map_index, vnum):
    """[(item, count)] the connected server lists for this mob on this map, an
    item once in server order; None while no catalogue says anything about it."""
    catalog = _active_receiver.catalog if _active_receiver is not None else None
    if catalog is None:
        return None
    return catalog.MobDrops(map_index, vnum)


def DropsStamp():
    """Changes whenever MobDrops may answer differently (a new catalogue, none)."""
    receiver = _active_receiver
    if receiver is None or receiver.catalog is None:
        return 0
    return receiver.revision


def tab_scope(destinations, dungeons):
    """Presentation selection only; the server intersects it with live data."""
    maps = sorted({number(row['map_index']) for row in destinations})
    bosses = sorted({number(vnum) for vnum in dungeons})
    if any(v <= 0 or v > 4294967295 for v in maps + bosses):
        raise ValueError('invalid TAB identity')
    token = 'tabs=%s;%s' % (','.join(map(str, maps)) or '-', ','.join(map(str, bosses)) or '-')
    if len(token) > MAX_SCOPE_BYTES:
        raise ValueError('TAB scope size')
    return token


def rows(value):
    return value if isinstance(value, list) else []


def number(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def truth(value):
    return value is True or value == 'true'


def digest(raw):
    value = 2166136261
    for byte in bytearray(raw):
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return '%08x' % value


class Receiver(object):
    def __init__(self, send, scope_provider=None, deferred=False, name_provider=None, catalog_setup=None, stream=False):
        self.send = send
        self.stream = stream
        self.scope_provider = scope_provider
        self.deferred, self.name_provider, self.catalog_setup = deferred, name_provider, catalog_setup
        self.Reset()

    def CancelWork(self):
        work, self.work = getattr(self, 'work', None), None
        if work is not None:
            work.close()

    def Reset(self):
        self.CancelWork()
        self.phase = 'idle'
        self.max_work_us = 0
        self.work_pumps = self.work_steps = self.step_limited_pumps = 0
        self.phase_seconds = {}
        self.phase_started = None
        self.catalog = None
        self.pending = None
        self.nonce = 0
        self.error = ''
        self.revision = 0
        self.scope = ''
        self.requested = False
        self.background = False
        self.stale = False
        self.marks = 0
        self._marks_at_request = 0

    def MarkStale(self):
        """The server changed a live catalog (LiveCatalogV1). The server builds
        a reply when it is requested, so a transfer in flight is stale too.
        Never requests anything: the owner refetches lazily."""
        self.marks += 1
        if self.catalog is not None or self.requested:
            self.stale = True

    def Fail(self, reason):
        """End the current transfer. A background refetch keeps the catalogue
        it was to replace; that catalogue stays stale."""
        self.CancelWork()
        self.pending = None
        self.requested = False
        if not self.background:
            self.catalog = None
        self.background = False
        self.error = reason

    def Request(self, keep=False):
        """``keep``: the installed catalogue stays readable until the new one
        is complete (a refetch nobody asked for by hand)."""
        self.CancelWork()
        self.max_work_us = 0
        self.work_pumps = self.work_steps = self.step_limited_pumps = 0
        self.phase_seconds = {}
        self.phase_started = None
        self.nonce = self.nonce % 2147483646 + 1
        self.pending = None
        self.background = bool(keep and self.catalog is not None)
        if not self.background:
            self.catalog = None
        self.requested = False
        self.error = ''
        encoding = ' zlib' if zlib is not None else ''
        if self.scope_provider is not None:
            try:
                self.scope = self.scope_provider()
                if not self.scope:
                    raise ValueError('missing TAB scope')
            except (ValueError, TypeError, KeyError, AttributeError, ImportError):
                self.Fail('invalid')
                return
            encoding = (' zlib ' if zlib is not None else ' plain ') + self.scope
        self.requested = True
        self._marks_at_request = self.marks
        suffix = ' stream' if self.stream and self.scope else ''
        self.send('/wiki_catalog %d 0%s%s' % (self.nonce, encoding, suffix))

    def Feed(self, action, *args):
        if self.error:
            return
        try:
            self._Feed(action, args)
        except (ValueError, TypeError, KeyError, AttributeError, IndexError, UnicodeError, binascii.Error):
            self.Fail('invalid')

    def _Feed(self, action, args):
        if not args or number(args[0]) != self.nonce:
            return
        if action == 'error':
            self.Fail(args[1] if len(args) == 2 else 'unavailable')
            return
        if action in ('begin', 'begin_zlib'):
            compressed = action == 'begin_zlib'
            if compressed and zlib is None:
                raise ValueError('unsupported compression')
            if len(args) != (4 if compressed else 3) or self.pending is not None:
                raise ValueError('duplicate begin')
            count = number(args[1])
            if count <= 0 or count > (MAX_BYTES + PART_BYTES - 1) // PART_BYTES:
                raise ValueError('size')
            raw_size = number(args[3]) if compressed else 0
            if compressed and not 0 < raw_size <= MAX_BYTES:
                raise ValueError('expanded size')
            self.pending = {'count': count, 'hash': args[2], 'parts': [], 'bytes': 0,
                            'compressed': compressed, 'raw_size': raw_size}
            return
        pending = self.pending
        if pending is None:
            return
        if action == 'part':
            if len(args) != 3 or number(args[1], -1) != len(pending['parts']):
                raise ValueError('part order')
            raw = binascii.unhexlify(args[2])
            if not raw or len(raw) > PART_BYTES or len(pending['parts']) >= pending['count']:
                raise ValueError('part size')
            pending['bytes'] += len(raw)
            if pending['bytes'] > MAX_BYTES:
                raise ValueError('payload size')
            pending['parts'].append(raw)
        elif action == 'page':
            if len(args) != 2 or number(args[1], -1) != len(pending['parts']) or not pending['parts']:
                raise ValueError('page order')
            if len(pending['parts']) >= pending['count']:
                raise ValueError('page after last part')
            self.send('/wiki_catalog %d %d' % (self.nonce, len(pending['parts'])))
        elif action == 'end':
            if len(args) != 3 or number(args[1]) != pending['count'] or len(pending['parts']) != pending['count']:
                raise ValueError('incomplete')
            if self.work is not None or args[2] != pending['hash']:
                raise ValueError('duplicate end or hash')
            self.SetPhase('decode')
            self.work = self.Prepare(pending, self.nonce, self.scope, self._marks_at_request)
            if not self.deferred:
                for unused in self.work:
                    pass
                self.work = None

    def Prepare(self, pending, nonce, scope, marks):
        if nonce != self.nonce or self.pending is not pending:
            return
        decoder = zlib.decompressobj() if pending['compressed'] else None
        utf8 = codecs.getincrementaldecoder('utf-8')()
        text, size, checksum = [], 0, 2166136261
        for part in pending['parts']:
            remaining = part
            while remaining:
                yield
                if decoder:
                    try:
                        raw = decoder.decompress(remaining, 8192)
                    except zlib.error:
                        raise ValueError('compressed stream')
                    remaining = decoder.unconsumed_tail
                    if decoder.unused_data:
                        raise ValueError('compressed framing')
                else:
                    raw, remaining = remaining[:8192], remaining[8192:]
                size += len(raw)
                if size > MAX_BYTES:
                    raise ValueError('expanded size')
                if _native_checksum is not None:
                    checksum = _native_checksum(raw, checksum)
                else:
                    for index, byte in enumerate(bytearray(raw)):
                        if index % 128 == 0:
                            yield
                        checksum = ((checksum ^ byte) * 16777619) & 0xffffffff
                text.append(utf8.decode(raw))
        if decoder and (size != pending['raw_size'] or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data):
            raise ValueError('compressed size or framing')
        if '%08x' % checksum != pending['hash']:
            raise ValueError('hash')
        text.append(utf8.decode(b'', final=True))
        self.SetPhase('json')
        reader = wikijson.Reader(''.join(text))
        text = None
        yield from reader.Read()
        data = reader.result
        if scope and (not isinstance(data, dict) or data.get('scope') != scope):
            raise ValueError('unscoped catalogue')
        self.SetPhase('graph')
        catalog = Catalog.__new__(Catalog)
        yield from catalog.Initialize(data)
        if self.catalog_setup:
            self.catalog_setup(catalog)
        if self.name_provider:
            self.SetPhase('names')
            yield from catalog.NameIndex(self.name_provider)
        if nonce != self.nonce or self.pending is not pending or not self.requested:
            return
        # One installation point after all validation and indices are complete.
        self.catalog, self.pending = catalog, None
        self.error = ''
        self.requested = self.background = False
        self.stale = self.marks != marks
        self.revision += 1
        self.SetPhase('ready')

    def SetPhase(self, phase):
        now = time.perf_counter()
        if self.phase_started is not None:
            self.phase_seconds[self.phase] = now - self.phase_started
        self.phase, self.phase_started = phase, now

    def Pump(self, budget=0.001, max_steps=MAX_PUMP_STEPS, clock=None):
        if self.work is None:
            return
        clock = clock or time.perf_counter
        started = clock()
        work = self.work
        self.work_pumps += 1
        try:
            for unused in range(max_steps):
                next(work)
                self.work_steps += 1
                if work is not self.work or clock()-started >= budget:
                    break
            else:
                self.step_limited_pumps += 1
        except StopIteration:
            if work is self.work:
                self.work = None
        except (ValueError, TypeError, KeyError, AttributeError, IndexError, UnicodeError, binascii.Error):
            self.Fail('invalid')
        self.max_work_us = max(self.max_work_us, int((clock()-started)*1000000))



def family_name(name):
    base, marker, grade = name.rpartition('+')
    return base.strip() if marker and grade.isdigit() else name


class Catalog(object):
    def __init__(self, data):
        # Synchronous accessor for tools; the game drives the same generator.
        for unused in self.Initialize(data):
            pass

    def Initialize(self, data):
        if not isinstance(data, dict) or number(data.get('schema')) != 1:
            raise ValueError('schema')
        for target, field, key in (('maps', 'maps', 'id'), ('items', 'items', 'vnum'),
                                  ('bonus_profiles', 'bonus_profiles', 'id'),
                                  ('refines', 'refines', 'from'),
                                  ('dungeon_guides', 'dungeon_guides', 'boss')):
            index = {}
            setattr(self, target, index)
            for row in rows(data.get(field)):
                yield
                index[number(row[key])] = row
        self.mobs = rows(data.get('mobs'))
        self.recipes = rows(data.get('recipes'))
        self.chests = {}
        for row in rows(data.get('chests')):
            yield
            self.chests[number(row['vnum'])] = rows(row.get('contents'))
        self.systems = data.get('systems') or {}
        self._soul_levels = {}
        for row in rows(self.systems.get('mount', {}).get('gear')):
            yield
            self._soul_levels[number(row['vnum'])] = number(row.get('soul_level'))
        self.missions = rows(data.get('mission_rewards'))
        if not self.maps or not self.items:
            raise ValueError('empty catalogue')
        dungeon_elements = {}
        self.sources, self._mob_rows = {}, {}
        self.available, self.craftable = set(), set()
        self.recipe_index, self.ingredient_sources = {}, {}
        for row in rows(data.get('ingredients')):
            yield
            vnum = number(row['vnum'])
            if vnum not in self.items or number(row.get('map')) not in self.maps:
                raise ValueError('invalid ingredient source')
            self.ingredient_sources.setdefault(vnum, []).append(row)
        for row in self.mobs:
            yield
            map_id, mob_id = number(row.get('map')), number(row.get('vnum'))
            if map_id not in self.maps:
                raise ValueError('unreachable map')
            boss = number(self.maps[map_id].get('boss'))
            if boss:
                elements = dungeon_elements.setdefault(boss, set())
                for element in rows(row.get('elements')):
                    yield
                    index = number(element.get('index'), -1)
                    if 0 <= index < 6:
                        elements.add(index)
            self._mob_rows.setdefault((map_id, mob_id), row)
            for drop in rows(row.get('drops')):
                yield
                vnum = number(drop['vnum'])
                if vnum not in self.items or number(drop['count']) <= 0:
                    raise ValueError('invalid drop')
                self.available.add(vnum)
                self.sources.setdefault(vnum, []).append((map_id, mob_id, (), drop))
        self.dungeon_elements = {boss: tuple(sorted(elements)) for boss, elements in dungeon_elements.items()}

        # Each dependency edge wakes once. Circular recipes cannot invent a seed.
        reachable, reached, listed = set(), deque(), deque()
        waiting, requirements, book_chests = {}, [], {}
        def reach(vnum):
            if vnum not in reachable:
                reachable.add(vnum)
                reached.append(vnum)
        def obtain(vnum):
            reach(vnum)
            if vnum not in self.available:
                self.available.add(vnum)
                listed.append(vnum)
        def rule(dependencies, target, crafted=False):
            index = len(requirements)
            requirements.append([len(dependencies), target, crafted])
            for vnum in dependencies:
                waiting.setdefault(vnum, []).append(index)
            if not dependencies:
                obtain(target)
                if crafted:
                    self.craftable.add(target)
        for recipe in self.recipes:
            yield
            vnum = number(recipe['vnum'])
            if vnum not in self.items or number(recipe['count']) <= 0:
                raise ValueError('invalid recipe')
            deps = set()
            for material in rows(recipe.get('materials')):
                yield
                ingredient = number(material['vnum'])
                if ingredient not in self.items or number(material['count']) <= 0:
                    raise ValueError('invalid material')
                deps.add(ingredient)
            self.recipe_index.setdefault(vnum, []).append(recipe)
            if number(recipe.get('chance')) > 0:
                rule(deps, vnum, True)
        for source, refine in self.refines.items():
            yield
            if number(refine.get('chance')) > 0:
                deps = {source}
                for material in rows(refine.get('materials')):
                    yield
                    deps.add(number(material['vnum']))
                rule(deps, number(refine['to']))
        for mission in self.missions:
            yield
            if number(mission['chest']) in self.chests:
                book_chests.setdefault(number(mission['book']), []).append(number(mission['chest']))
        listed.extend(self.available)
        for vnum in self.available | set(self.ingredient_sources):
            yield
            reach(vnum)
        while reached or listed:
            if reached:
                vnum = reached.popleft()
                for child in self.chests.get(vnum, ()):
                    yield
                    if number(child['count']) > 0:
                        reach(number(child['vnum']))
                for index in waiting.get(vnum, ()):
                    yield
                    entry = requirements[index]
                    entry[0] -= 1
                    if not entry[0]:
                        obtain(entry[1])
                        if entry[2]:
                            self.craftable.add(entry[1])
            if listed:
                vnum = listed.popleft()
                for child in self.chests.get(vnum, ()):
                    yield
                    if number(child['count']) > 0:
                        obtain(number(child['vnum']))
                for chest in book_chests.get(vnum, ()):
                    yield
                    obtain(chest)
            yield
        self.available.intersection_update(self.items)
        for vnum, recipes in self.recipe_index.items():
            valid = []
            for recipe in recipes:
                yield
                if number(recipe.get('chance')) > 0 and all(number(m['vnum']) in reachable for m in rows(recipe.get('materials'))):
                    valid.append(recipe)
            self.recipe_index[vnum] = valid
        candidates = rows(data.get('alchemy'))
        grades = set()
        for row in candidates:
            yield
            if number(row['vnum']) in self.available:
                grades.add((number(row['kind']), number(row['grade'])))
        by_grade = {}
        for row in candidates:
            yield
            by_grade.setdefault((number(row['kind']), number(row['grade'])), []).append(row)
        pending = deque(grades)
        while pending:
            kind, grade = pending.popleft()
            for row in by_grade.get((kind, grade), ()):
                for target in rows(row.get('grade_results')):
                    yield
                    key = (kind, number(target['grade']))
                    if float(target.get('chance', 0)) > 0 and key not in grades:
                        grades.add(key)
                        pending.append(key)
        self.alchemy = {}
        for row in candidates:
            yield
            if (number(row['kind']), number(row['grade'])) in grades:
                self.alchemy[number(row['vnum'])] = row
        self.names, self.families, self._route_cache, self._parents = {}, {}, {}, {}
        for chest, contents in self.chests.items():
            if chest in self.available:
                for row in contents:
                    yield
                    self._parents.setdefault(number(row['vnum']), set()).add(chest)
        self._family_search, self._family_names, self._item_keys, self._ordered_families = {}, {}, {}, []

    def MobDrops(self, map_index, vnum):
        row = self._mob_rows.get((number(map_index), number(vnum)))
        if row is None:
            return None
        result, seen = [], set()
        for drop in rows(row.get('drops')):
            item = number(drop['vnum'])
            if item not in seen:
                seen.add(item)
                result.append((item, number(drop['count'])))
        return result

    def SoulLevel(self, vnum):
        return self._soul_levels.get(vnum, 0)

    def ItemLevel(self, vnum):
        return number(self.items.get(vnum, {}).get('level')) or self.SoulLevel(vnum)

    def ItemKey(self, vnum):
        if vnum in self._item_keys:
            return self._item_keys[vnum]
        return (self.ItemLevel(vnum),
                folded(self.names.get(vnum, '')), vnum)

    def FamilyKey(self, variants):
        return min(self.ItemKey(v) for v in (list(v for v in variants if v in self.available) or variants))

    def MapKey(self, map_id):
        row = self.maps.get(map_id, {})
        return (number(row.get('level')), folded(row.get('name', '')), map_id)

    def ChestKey(self, vnum):
        # Chests usually have no use-level limit: use their lowest obtainable
        # route (or mission book) rather than placing every boss chest at zero.
        level = number(self.items.get(vnum, {}).get('level'))
        levels = [self.MapKey(r[0])[0] for r in self.Routes([vnum])]
        levels.extend(number(r.get('level')) for r in self.missions if number(r.get('chest')) == vnum)
        return (max(level, min(levels)) if levels else level, folded(self.names.get(vnum, '')), vnum)

    def IndexNames(self, name):
        for unused in self.NameIndex(name):
            pass

    def NameIndex(self, name):
        self.names, self.families, self._family_names, self._item_keys = {}, {}, {}, {}
        families, ids, ordered = {}, [], []
        for vnum in self.items:
            yield
            heapq.heappush(ids, vnum)
        while ids:
            yield
            vnum = heapq.heappop(ids)
            self.names[vnum] = name(vnum)
            base = family_name(self.names[vnum])
            proto = self.items[vnum]
            if 'dew_family' in proto:
                base = self.names[vnum].rsplit(' ', 1)[0]
            key = (base, number(proto['type']), number(proto['subtype']))
            families.setdefault(key, []).append(vnum)
        for key, variants in families.items():
            best = None
            for vnum in variants:
                yield
                if vnum in self.available:
                    value = (self.ItemLevel(vnum), folded(self.names[vnum]), vnum)
                    self._item_keys[vnum] = value
                    best = value if best is None else min(best, value)
            if best is not None:
                self.families[key] = variants
                self._family_names[key] = folded(key[0])
                heapq.heappush(ordered, (best, len(ordered), key, variants))
        self._ordered_families = []
        while ordered:
            yield
            unused, order, key, variants = heapq.heappop(ordered)
            self._ordered_families.append((key, variants))
        locations, children, pending, queued = {}, {}, deque(), set()
        for child, parents in self._parents.items():
            for parent in parents:
                yield
                children.setdefault(parent, []).append(child)
        for vnum, routes in self.sources.items():
            yield
            locations[vnum] = {r[0] for r in routes}
            pending.append(vnum)
            queued.add(vnum)
        while pending:
            parent = pending.popleft()
            queued.remove(parent)
            for child in children.get(parent, ()):
                yield
                current = locations.setdefault(child, set())
                inherited = locations[parent]
                if not inherited.issubset(current):
                    current.update(inherited)
                    if child not in queued:
                        pending.append(child)
                        queued.add(child)
        for key, variants in self.families.items():
            names = set()
            for vnum in variants:
                yield
                names.update(folded(self.MapName(m)) for m in locations.get(vnum, ()))
            self._family_search[key] = tuple(names)

    def Families(self, category=None, query=''):
        needle = folded(query)
        result = []
        for key, variants in self._ordered_families:
            if category is not None and key[1:] != category:
                continue
            if needle and needle not in self._family_names[key]:
                if not any(needle in name for name in self._family_search.get(key, ())):
                    continue
            result.append((key, variants))
        return result

    def MapName(self, map_index):
        return self.maps.get(map_index, {}).get('name', '')

    def Routes(self, variants):
        """All simple chest paths, deduplicated; deterministic without best-source guesses."""
        output, seen = [], set()
        cache_key = tuple(sorted(variants))
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]
        parents = self._parents
        pending = deque((v, ()) for v in variants if v in self.available)
        while pending:
            vnum, trail = pending.popleft()
            for route in self.sources.get(vnum, []):
                identity = (route[0], route[1], trail, number(route[3].get('min_level')), truth(route[3].get('gloves')))
                if identity not in seen:
                    seen.add(identity)
                    output.append((route[0], route[1], tuple(reversed(trail)), route[3]))
            for parent in parents.get(vnum, []):
                if parent not in trail and parent != vnum:
                    pending.append((parent, trail + (parent,)))
        result = sorted(output, key=lambda route: (self.MapKey(route[0]), route[1], route[2]))
        self._route_cache[cache_key] = result
        return result

    def Forge(self, variants):
        # Reverse-refine closure includes unavailable legacy copies. Preserve
        # their exact identities elsewhere; combine only equal forge columns.
        result, seen = [], set()
        for source in variants:
            step = self.refines.get(source)
            if step is None or source not in self.available:
                continue
            target = number(step['to'])
            if target not in variants or target not in self.available:
                continue
            protos = [{k: v for k, v in self.items[item].items() if k not in ('vnum', 'to')}
                      for item in (source, target)]
            terms = {k: v for k, v in step.items() if k not in ('from', 'to')}
            identity = json.dumps([self.names.get(source, str(source)),
                                   self.names.get(target, str(target)), protos, terms],
                                  sort_keys=True, ensure_ascii=True)
            if identity not in seen:
                seen.add(identity)
                result.append(step)
        return result
