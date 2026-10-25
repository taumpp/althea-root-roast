"""Server-owned dungeon objective snapshot and elapsed-time marquee policy."""


class ObjectiveSubscription:
    """Subscribe after Loading; only a validated server snapshot acknowledges it."""
    def __init__(self, send, clock):
        self.send = send
        self.clock = clock
        self.next_request = None
        self.deadline = 0.0

    def start(self):
        now = self.clock()
        self.next_request = now + 1.0
        self.deadline = now + 60.0

    def stop(self):
        self.next_request = None

    def update(self):
        if self.next_request is None:
            return
        now = self.clock()
        if now >= self.deadline:
            self.stop()
            return
        if now < self.next_request:
            return
        self.next_request = now + 2.0
        # Python's SendChatPacket returns None even when the native Loading
        # phase rejects the command. Do not treat that return value as an ACK.
        self.send("/dungeon_objective 1")


class ObjectiveState:
    def __init__(self, texts):
        self.texts = texts
        self.sequence = -1
        self.visible = False
        self.instance = self.boss = self.phase = self.phases = 0
        self.current = self.target = self.status = 0
        self.key = "none"
        self.text = ""

    @property
    def text_identity(self):
        return self.instance, self.phase, self.key

    def receive(self, arguments, map_index=None):
        if len(arguments) != 9:
            return False
        try:
            seq, instance, boss, phase, phases = map(int, arguments[:5])
            current, target, status = map(int, arguments[6:])
        except (ValueError, TypeError, OverflowError):
            return False
        key = arguments[5]
        if (seq <= self.sequence or not 0 <= seq <= 0xFFFFFFFF
                or not 0 <= instance <= 0x7FFFFFFF or not 0 <= boss <= 1000000
                or not 0 <= phase <= phases <= 100
                or not 0 <= current <= target <= 1000000 or status not in (0, 1, 2)):
            return False
        if status and (not instance or not boss):
            return False
        # A source core can still have an objective packet in flight on warp.
        # Reject it without advancing the destination's sequence or ACKing it.
        if status and map_index is not None and instance != map_index:
            return False
        if status and key not in self.texts:
            # A newer server may know a task this pack cannot translate.
            # Retire the previous instruction instead of displaying stale text.
            self.sequence = seq
            self.visible = False
            return True
        self.sequence = seq
        self.instance, self.boss = instance, boss
        self.phase, self.phases = phase, phases
        self.current, self.target, self.status = current, target, status
        self.key = key
        self.text = self.texts.get(key, "")
        self.visible = bool(status)
        return True


class Marquee:
    HOLD = 1.25
    SPEED = 24.0

    def __init__(self):
        self.identity = None
        self.started = 0.0
        self.width = self.viewport = 0

    def set_text(self, identity, width, viewport, now):
        signature = identity, width, viewport
        if signature != self.identity:
            self.identity = signature
            self.started = now
            self.width, self.viewport = max(0, width), max(0, viewport)

    def offset(self, now):
        distance = self.width - self.viewport
        if distance <= 0:
            return (self.viewport - self.width) // 2
        duration = distance / self.SPEED
        elapsed = max(0.0, now - self.started) % (duration + 2 * self.HOLD)
        return -min(float(distance), max(0.0, elapsed - self.HOLD) * self.SPEED)
