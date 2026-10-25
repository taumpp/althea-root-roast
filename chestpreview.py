"""Route the existing chest response stream without owning any windows."""


def CanPreview(vnum):
    # Raw Cor Draconis is a cube material, despite its legacy GIFTBOX type.
    return vnum > 0 and vnum != 50252


class ChestPreviewBroker(object):
    def __init__(self, send):
        self.send = send
        self.pending = {}

    def Request(self, vnum, owner, callback):
        self.Cancel(owner)
        if not CanPreview(vnum):
            return False
        # Moonlight Box: the event server owns its contents (no special_item_group);
        # answer from the latest public EventBoxV1 list, never with odds.
        try:
            import eventboxmodel
        except ImportError:     # standalone broker (tests) without the event module
            eventboxmodel = None
        local = eventboxmodel.ChestPages(vnum) if eventboxmodel else None
        if local is not None:
            callback(vnum, local)
            return True
        if vnum not in self.pending:
            # Keep abandoned unanswered requests until their end marker. The
            # protocol has a VNUM but no request ID, so overlapping re-requests
            # must never merge an old response into a newer one.
            if len(self.pending) >= 32:
                return False
            self.pending[vnum] = ({}, {})
            self.pending[vnum][1][owner] = callback
            self.send(vnum)
        else:
            self.pending[vnum][1][owner] = callback
        return True

    def Add(self, vnum, page, slot, item, count):
        pending = self.pending.get(vnum)
        if pending is None or not (1 <= page <= 5 and 0 <= slot < 40 and item > 0 and count > 0):
            return
        pending[0].setdefault(page, {})[slot] = (item, count)

    def Complete(self, vnum):
        pending = self.pending.pop(vnum, None)
        if pending is None:
            return
        pages, callbacks = pending
        for callback in list(callbacks.values()):
            callback(vnum, dict((page, dict(rows)) for page, rows in pages.items()))

    def Cancel(self, owner):
        for pages, callbacks in self.pending.values():
            callbacks.pop(owner, None)

    def Clear(self):
        self.pending.clear()
