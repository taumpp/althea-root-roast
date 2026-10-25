"""Item-scoped switchbot options received from the authoritative server."""
import time

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


def HeldScroll(scroll):
    """The scroll while the player holds some, else the variant of its kind he holds most of (the menu one).

    One kind can have several scroll vnums and the server spends exactly the
    asked one: a remembered variant at 0 pcs would show "0 ks" and never roll.
    """
    scroll = int(scroll or 0)
    if not scroll or player.GetItemCountByVnum(scroll):
        return scroll
    kind = bonuscatalog.ScrollKind(scroll)
    for menu in bonuscatalog.MenuScrolls():
        if bonuscatalog.ScrollKind(menu) == kind and player.GetItemCountByVnum(menu):
            return menu
    return scroll


def SameKind(first, second):
    """Scrolls of one family roll the same bonuses of an item; only another family changes what can be set."""
    return int(first) == int(second) or bonuscatalog.ScrollKind(first) == bonuscatalog.ScrollKind(second)


class Options:
    # A request or its reply can be lost (the sends of a stream that is reconnecting after a warp are dropped, the
    # items of the slot may not be here yet): an occupied slot without options is asked again, a few times.
    RETRY_SECONDS = 1.5
    RETRY_LIMIT = 6
    POLL_SECONDS = 0.5

    def __init__(self):
        self.serial = 0
        self.pending = {}
        self.catalogs = {}
        self.selected = {}
        self.rarity = {}
        self.tries = {}
        self.changed = None
        self.clock = time.monotonic
        self.nextPoll = 0

    def Reset(self):
        self.pending.clear()
        self.catalogs.clear()
        self.selected.clear()
        self.rarity.clear()
        self.tries.clear()
        self.changed = None
        self.nextPoll = 0

    def Scroll(self, slot):
        slot = int(slot)
        if slot in self.selected:
            return self.selected[slot]
        return RecommendedScroll(player.GetItemIndex(player.SWITCHBOT, slot))

    def Wanted(self, slot, vnum):
        """Scroll for the item in the slot: the player's own while it is offered and of the item's family."""
        recommended = RecommendedScroll(vnum)
        chosen = self.selected.get(int(slot))
        if chosen and bonuscatalog.IsOfferedScroll(chosen) and SameKind(chosen, recommended):
            return HeldScroll(chosen)
        return recommended

    def Request(self, slot, scroll=None, retry=False):
        slot = int(slot)
        scroll = self.Scroll(slot) if scroll is None else int(scroll)
        if not 0 <= slot < switchbot.SLOT_COUNT or not bonuscatalog.IsOfferedScroll(scroll):
            return False
        self.serial += 1
        self.tries[slot] = self.tries.get(slot, 0) + 1 if retry else 0
        self.selected[slot] = scroll
        self.catalogs.pop(slot, None)
        self.pending[slot] = {'nonce': self.serial, 'scroll': scroll, 'values': {}, 'sent': self.clock()}
        net.SendChatPacket('/switchbot_options %d %d %d' % (slot, scroll, self.serial))
        return True

    def Retry(self):
        """Ask again for every occupied slot that has no options and no fresh request; returns those slots."""
        now = self.clock()
        if now < self.nextPoll:
            return []
        self.nextPoll = now + self.POLL_SECONDS
        asked = []
        for slot in range(switchbot.SLOT_COUNT):
            if (not bonuscatalog.IsSlotAllowed(slot) or not player.GetItemIndex(player.SWITCHBOT, slot) or
                    self.Catalog(slot) or self.tries.get(slot, 0) >= self.RETRY_LIMIT):
                continue
            pending = self.pending.get(slot)
            if pending and now - pending.get('sent', now) < self.RETRY_SECONDS:
                continue
            if self.Request(slot, retry=True):
                asked.append(slot)
        return asked

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
            # The item of the slot may still be on its way (a warp sends the items and the answer to the first
            # request together): Catalog() holds the options back until the client has that very item.
            here = player.GetItemIndex(player.SWITCHBOT, slot)
            if ('item_id' not in pending or len(pending['values']) != pending['rows'] or
                    (here and here != pending['vnum'])):
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

    def BuildRequest(self, slot, instant=False, force=False):
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
        elif force:
            # the player confirmed rolling an item that already carries the bonuses (SLOT_MATCHED).
            request += ' force'
        return request

    def Start(self, slot, instant=False, expected=None, force=False):
        request = self.BuildRequest(slot, instant, force)
        if not request or (expected is not None and request != expected):
            return False
        net.SendChatPacket(request)
        return True


options = Options()


class AttributeMemory:
    """The bonuses the player set for each slot and variant.

    The server sends its whole switchbot table (switchbot.Update replaces every slot's bonuses at once) on each start
    and stop, for a removed item and when a character enters a core, so after a warp. The server only knows the
    bonuses a slot had when it was last started. A slot that is not running keeps what the player set here and gets
    it back after each such table; a running slot is the server's."""

    def __init__(self):
        self.owner = None
        self.slots = {}     # slot -> {(alternative, index): (kind, value)}

    @staticmethod
    def _Owner():
        name = getattr(player, 'GetName', None)
        return name() if name else ''

    def _Check(self):
        owner = self._Owner()
        if owner != self.owner:         # another character in the same client process
            self.owner = owner
            self.slots.clear()

    def Remember(self, slot):
        self._Check()
        self.slots[slot] = dict(
            ((alternative, index), tuple(switchbot.GetAttribute(slot, alternative, index)))
            for alternative in range(switchbot.ALTERNATIVE_COUNT) for index in range(5))

    def SetAttribute(self, slot, alternative, index, kind, value):
        switchbot.SetAttribute(slot, alternative, index, kind, value)
        self.Remember(slot)

    def Forget(self, slot):
        self.slots.pop(slot, None)

    def Apply(self):
        """Put the remembered bonuses back onto the table the server has just replaced."""
        self._Check()
        for slot in list(self.slots):
            if switchbot.IsActive(slot):
                self.Remember(slot)     # the bonuses of the run, as the server holds them
            elif player.GetItemIndex(player.SWITCHBOT, slot):
                for (alternative, index), pair in self.slots[slot].items():
                    if tuple(switchbot.GetAttribute(slot, alternative, index)) != pair:
                        switchbot.SetAttribute(slot, alternative, index, pair[0], pair[1])


memory = AttributeMemory()


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
