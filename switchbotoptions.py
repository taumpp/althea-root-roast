"""Item-scoped switchbot options received from the authoritative server."""
import net
import player
import switchbot

import bonuscatalog

# Offered scrolls, their item families, the instant fee and scroll budget come
# from the server's bonus catalog (bonuscatalog.py, ALTHEA-647). Without it no
# scroll is offered and nothing can start.


def RecommendedScroll(vnum):
    """Scroll of the target's item family, from the server catalog (0: none)."""
    return bonuscatalog.RecommendedScroll(vnum)


class Options:
    def __init__(self):
        self.serial = 0
        self.pending = {}
        self.catalogs = {}
        self.selected = {}
        self.rarity = {}
        self.changed = None

    def Reset(self):
        self.pending.clear()
        self.catalogs.clear()
        self.selected.clear()
        self.rarity.clear()
        self.changed = None

    def Scroll(self, slot):
        slot = int(slot)
        if slot in self.selected:
            return self.selected[slot]
        return RecommendedScroll(player.GetItemIndex(player.SWITCHBOT, slot))

    def Request(self, slot, scroll=None):
        slot = int(slot)
        scroll = self.Scroll(slot) if scroll is None else int(scroll)
        if not 0 <= slot < switchbot.SLOT_COUNT or not bonuscatalog.IsOfferedScroll(scroll):
            return
        self.serial += 1
        self.selected[slot] = scroll
        self.catalogs.pop(slot, None)
        self.pending[slot] = {'nonce': self.serial, 'scroll': scroll, 'values': {}}
        net.SendChatPacket('/switchbot_options %d %d %d' % (slot, scroll, self.serial))

    def Receive(self, action, slot, nonce, payload):
        args = () if payload == '-' else payload.split('/')
        slot, nonce = int(slot), int(nonce)
        pending = self.pending.get(slot)
        if not pending or pending['nonce'] != nonce:
            return
        if action == 'begin' and len(args) == 5:
            pending.update(item_id=int(args[0]), vnum=int(args[1]), rows=int(args[2]), scroll=int(args[3]), slots=int(args[4]))
            self.selected[slot] = int(args[3])
        elif action == 'row' and len(args) == 2:
            kind = int(args[0])
            values = tuple(sorted(set(int(v) for v in args[1].split(',') if int(v) > 0)))
            if 0 < kind < 256 and values:
                pending['values'][kind] = values
        elif action == 'end' and not args:
            if ('item_id' not in pending or len(pending['values']) != pending['rows'] or
                    player.GetItemIndex(player.SWITCHBOT, slot) != pending['vnum']):
                return
            self.catalogs[slot] = pending
            del self.pending[slot]
            if self.changed:
                self.changed(slot)

    def ReceiveMetadata(self, slot, itemId, vnum, grade, kind, value):
        self.rarity[int(slot)] = (int(itemId), int(vnum), int(grade), (int(kind), int(value)))

    def Rarity(self, slot):
        metadata = self.rarity.get(int(slot))
        catalog = self.Catalog(slot)
        if metadata and catalog and metadata[0] == catalog['item_id'] and metadata[1] == catalog['vnum']:
            return metadata[2], metadata[3]
        return 0, (0, 0)

    def Catalog(self, slot):
        catalog = self.catalogs.get(int(slot))
        if catalog and catalog['vnum'] == player.GetItemIndex(player.SWITCHBOT, slot):
            return catalog
        return None

    def Values(self, slot, kind):
        catalog = self.Catalog(slot)
        return catalog['values'].get(int(kind), ()) if catalog else ()

    def Maximum(self, slot, kind):
        values = self.Values(slot, kind)
        return max(values) if values else 0

    def Attributes(self, slot):
        catalog = self.Catalog(slot)
        return sorted((kind, max(values)) for kind, values in catalog['values'].items()) if catalog else []

    def InstantCount(self, slot):
        return max(0, min(bonuscatalog.InstantMaxScrolls(), player.GetItemCountByVnum(self.Scroll(slot))))

    def BuildRequest(self, slot, instant=False):
        catalog = self.Catalog(slot)
        if (not catalog or not catalog['item_id'] or switchbot.IsActive(slot) or
                not bonuscatalog.IsSlotAllowed(slot)):
            return None
        alternatives = []
        for alternative in range(switchbot.ALTERNATIVE_COUNT):
            values = []
            for index in range(5):
                kind, value = switchbot.GetAttribute(slot, alternative, index)
                if (instant and alternative) or not value:
                    kind, value = 0, 0
                values.append('%d:%d' % (kind, value))
            alternatives.append(','.join(values))
        request = ('/switchbot_run %d %d %d %d %s' %
                           (slot, catalog['item_id'], catalog['scroll'], int(bool(instant)),
                            ';'.join(alternatives)))
        if instant:
            count = self.InstantCount(slot)
            if not count:
                return None
            request += ' %d' % count
        return request

    def Start(self, slot, instant=False, expected=None):
        request = self.BuildRequest(slot, instant)
        if not request or (expected is not None and request != expected):
            return False
        net.SendChatPacket(request)
        return True


options = Options()


class InstantOptions:
    """A separate inventory target and bonus list for the instant reroller."""
    def __init__(self):
        self.cell = None
        self.scroll = 0
        self.serial = 0
        self.pending = None
        self.catalog = None
        self.attrs = [(0, 0) for _ in range(5)]
        self.running = False
        self.changed = None

    def Reset(self):
        self.cell = None
        self.pending = None
        self.catalog = None
        self.attrs = [(0, 0) for _ in range(5)]
        self.running = False
        self.scroll = 0

    def SetTarget(self, cell):
        self.cell = cell
        self.attrs = [(0, 0) for _ in range(5)]
        self.scroll = RecommendedScroll(player.GetItemIndex(player.INVENTORY, cell)) if cell is not None else 0
        self.Request()

    def Scroll(self, unused=None):
        return self.scroll

    def Request(self):
        self.catalog = None
        if (self.cell is None or self.running or not player.GetItemIndex(player.INVENTORY, self.cell) or
                not bonuscatalog.IsOfferedScroll(self.scroll)):
            self.pending = None
            if self.changed:
                self.changed()
            return
        self.serial += 1
        self.pending = {'nonce': self.serial, 'cell': self.cell, 'values': {}}
        net.SendChatPacket('/switchbot_instant_options %d %d %d' % (self.cell, self.scroll, self.serial))
        if self.changed:
            self.changed()

    def Receive(self, action, cell, nonce, payload):
        cell, nonce = int(cell), int(nonce)
        pending = self.pending
        if not pending or cell != pending['cell'] or nonce != pending['nonce']:
            return
        args = () if payload == '-' else payload.split('/')
        if action == 'begin' and len(args) == 5:
            pending.update(item_id=int(args[0]), vnum=int(args[1]), rows=int(args[2]),
                           scroll=int(args[3]), slots=int(args[4]))
        elif action == 'row' and len(args) == 2:
            kind = int(args[0])
            values = tuple(sorted(set(int(value) for value in args[1].split(',') if int(value) > 0)))
            if 0 < kind < 256 and values:
                pending['values'][kind] = values
        elif action == 'end' and not args:
            self.pending = None
            if ('item_id' in pending and pending['item_id'] and
                    len(pending['values']) == pending['rows'] and
                    player.GetItemIndex(player.INVENTORY, cell) == pending['vnum']):
                self.catalog = pending
            if self.changed:
                self.changed()

    def Catalog(self, unused=None):
        if self.cell is not None and self.catalog and player.GetItemIndex(player.INVENTORY, self.cell) == self.catalog['vnum']:
            return self.catalog
        return None

    def Values(self, unused, kind):
        catalog = self.Catalog()
        return catalog['values'].get(int(kind), ()) if catalog else ()

    def Maximum(self, unused, kind):
        values = self.Values(None, kind)
        return max(values) if values else 0

    def Attributes(self):
        catalog = self.Catalog()
        return sorted((kind, max(values)) for kind, values in catalog['values'].items()) if catalog else []

    def GetAttribute(self, unused, alternative, index):
        return self.attrs[index]

    def SetAttribute(self, unused, alternative, index, kind, value):
        self.attrs[index] = (kind, value)
        if self.changed:
            self.changed()

    def IsActive(self, unused=None):
        return self.running

    def InstantCount(self):
        return max(0, min(bonuscatalog.InstantMaxScrolls(), player.GetItemCountByVnum(self.scroll)))

    def BuildRequest(self):
        catalog = self.Catalog()
        if not catalog or self.running or not self.InstantCount():
            return None
        if not any(kind and value for kind, value in self.attrs):
            return None
        values = ','.join('%d:%d' % pair for pair in self.attrs)
        return '/switchbot_instant_run %d %d %d %d %s' % (
            self.cell, catalog['item_id'], self.scroll, self.InstantCount(), values)

    def Start(self, expected):
        request = self.BuildRequest()
        if not request or request != expected:
            return False
        net.SendChatPacket(request)
        return True

    def Started(self):
        self.running = True
        if self.changed:
            self.changed()

    def Finish(self):
        self.running = False
        if self.changed:
            self.changed()


instantOptions = InstantOptions()
