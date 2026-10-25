"""View-scoped, server-authoritative meteor protection presentation."""

class ProtectionState(object):
    def __init__(self):
        self.entries = {}

    def receive(self, vid, owned, deadline):
        try:
            vid, owned, deadline = int(vid), int(owned), int(deadline)
        except (TypeError, ValueError):
            return False
        if not 0 < vid <= 0xffffffff or owned not in (0, 1) or not 0 <= deadline <= 0x7fffffffffffffff:
            return False
        self.entries[vid] = (bool(owned), deadline)
        return True

    def remove(self, vid):
        try:
            self.entries.pop(int(vid), None)
        except (TypeError, ValueError):
            pass

    def clear(self):
        self.entries.clear()

    def presentation(self, vid, server_now):
        entry = self.entries.get(vid)
        if entry is None:
            return None
        owned, deadline = entry
        remaining = max(0, deadline - int(server_now))
        if not remaining:
            return ('public', None)
        return ('owner' if owned else 'foreign', '%02d:%02d' % (remaining // 60, remaining % 60))
