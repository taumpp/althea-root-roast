"""Badges and state overlays of the button panels: the pure model and its settings.

Owner decision 2026-10-04 (wave 1, client only): a panel button may show

* a badge in its top-right corner - ``BADGE_ACTION`` (ruby: something waits for
  the player: claim, hand in, spend points) or ``BADGE_INFO`` (gold: something is
  live or new, never pulses); ``count`` > 0 shows a number (``9+`` cap),
  otherwise a dot;
* a state - ``STATE_ACTIVE`` (gold rim: on / summoned), ``STATE_RUNNING`` (gold
  rim with a turning spark), ``STATE_CURRENT`` (the current channel: gold
  rim, never the dimmed pressed look) or ``STATE_UNAVAILABLE`` (dark veil, e.g. a VIP channel) or
  ``STATE_ROLLING`` (the Switchbot's green glow running round the edge);
* a countdown - ``remaining`` of ``total`` seconds: a dark sector over the
  remaining part plus the time in the middle;
* a short ``label`` in the middle (``CH3``, ``VIP``) when no countdown shows;
  ``numeral``: the label is the big number of an R1 launcher (Cinzel, ivory).

Providers (``buttonpanelstatus``) only read data the client already has; this
module never touches the game. The settings live in the ``badges`` section of
``UserData/button-panels.json`` (``buttonpanelstore``): presentation only, per
PC, shared by every panel, so one function behaves the same on the minimap and
on the inventory rail.
"""
import math

BADGE_ACTION = 'action'
BADGE_INFO = 'info'
BADGES = (BADGE_ACTION, BADGE_INFO)

STATE_ACTIVE = 'active'
STATE_RUNNING = 'running'
STATE_CURRENT = 'current'
STATE_UNAVAILABLE = 'unavailable'
# Switchbot rolling bonuses: the green glow of the Switchbot slot (owner 2026-10-04).
STATE_ROLLING = 'rolling'
STATES = (STATE_ACTIVE, STATE_RUNNING, STATE_CURRENT, STATE_UNAVAILABLE, STATE_ROLLING)

MAX_COUNT_SHOWN = 9


class Decor(object):
    """What one button shows besides its icon. Immutable by convention."""
    __slots__ = ('badge', 'count', 'state', 'remaining', 'total', 'label', 'flash', 'numeral')

    def __init__(self, badge=None, count=0, state=None, remaining=None, total=None, label='', flash=False,
                 numeral=False):
        self.badge = badge if badge in BADGES else None
        self.count = max(0, int(count or 0)) if self.badge else 0
        self.state = state if state in STATES else None
        remaining = _seconds(remaining)
        total = _seconds(total)
        if remaining is not None and remaining <= 0:
            remaining = None
        self.remaining = remaining
        self.total = max(total, remaining) if remaining is not None and total else (remaining if remaining is not None else None)
        self.label = str(label or '')
        self.flash = bool(flash)
        self.numeral = bool(numeral) and bool(self.label)   # the label is the big number of an R1 launcher

    def Key(self):
        """Comparable value; the countdown is compared by its shown text."""
        return (self.badge, self.count, self.state, FormatRemaining(self.remaining), self.total and int(self.total),
                self.label, self.flash, self.numeral)

    def IsEmpty(self):
        return self.Key() == EMPTY_KEY

    def BadgeLabel(self):
        """The text of the number badge ('' = a dot)."""
        return BadgeText(self.count)

    def ShowsCountdownText(self):
        """Whether the countdown time is written in the middle of the button."""
        return True

    def __eq__(self, other):
        return isinstance(other, Decor) and self.Key() == other.Key()

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None

    def __repr__(self):
        return 'Decor(%r)' % (self.Key(),)


def _seconds(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float('inf'), float('-inf')):
        return None
    return value



def FormatRemaining(seconds):
    """Countdown text that fits a 28 px medallion: ``42``, ``18m``, ``2h``, ``3d``."""
    seconds = _seconds(seconds)
    if seconds is None or seconds <= 0:
        return ''
    if seconds < 60:
        return '%d' % int(math.ceil(seconds))
    if seconds < 3600:
        return '%dm' % int(math.ceil(seconds / 60.0))
    if seconds < 100 * 3600:
        return '%dh' % int(seconds // 3600)
    return '%dd' % int(seconds // 86400)


EMPTY = Decor()
EMPTY_KEY = EMPTY.Key()


class SecondsBadge(Decor):
    """A countdown whose seconds ride in the number badge (the one badge style: a red circle with the white number)
    instead of the middle of the button - the rated arena's "Zápas nalezen" (9. 10. 2026): ``count`` = the seconds
    left, shown in full (12, not 9+); the arc of the countdown stays."""
    __slots__ = ()

    def BadgeLabel(self):
        return str(self.count) if self.count > 0 else ''

    def ShowsCountdownText(self):
        return False


def BadgeText(count):
    """'' for a dot, the number, or ``9+``."""
    count = int(count or 0)
    if count <= 0:
        return ''
    return '%d+' % MAX_COUNT_SHOWN if count > MAX_COUNT_SHOWN else str(count)


def Strongest(decors):
    """Aggregate for the "More" button: one dot, action before info; no count, no state."""
    kinds = set(decor.badge for decor in decors if decor is not None)
    if BADGE_ACTION in kinds:
        return Decor(BADGE_ACTION)
    if BADGE_INFO in kinds:
        return Decor(BADGE_INFO)
    return EMPTY


# Settings ----------------------------------------------------------------------
SECTION = 'badges'
MAX_IDS = 128
MAX_ID_LENGTH = 64
_FLAGS = ('enabled', 'state', 'pulse')


def _ids(value):
    result = []
    if isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, str) and item and len(item) <= MAX_ID_LENGTH and item not in result:
                result.append(item)
                if len(result) >= MAX_IDS:
                    break
    return result


class Settings(object):
    """Global switches plus per-function exceptions.

    ``enabled`` - badges at all; ``state`` - states and countdowns at all;
    ``pulse`` - the ruby badge pulses like the pet album reminder.
    ``off`` / ``state_off`` - functions whose badge / state the player turned off.
    Unknown keys of the stored section are kept and written back unchanged.
    """

    def __init__(self, section=None):
        section = section if isinstance(section, dict) else {}
        self.extra = dict((key, value) for key, value in section.items()
                          if key not in _FLAGS + ('off', 'state_off'))
        self.enabled = _flag(section, 'enabled')
        self.state = _flag(section, 'state')
        self.pulse = _flag(section, 'pulse')
        self.off = _ids(section.get('off'))
        self.state_off = _ids(section.get('state_off'))

    def BadgeOn(self, action_id):
        return self.enabled and action_id not in self.off

    def StateOn(self, action_id):
        return self.state and action_id not in self.state_off

    def SetBadge(self, action_id, on):
        self.off = _toggle(self.off, action_id, not on)

    def SetState(self, action_id, on):
        self.state_off = _toggle(self.state_off, action_id, not on)

    def IsDefault(self):
        return self.ToSection() is None

    def ToSection(self):
        """The stored form, or None when everything is default (section removed)."""
        section = dict(self.extra)
        for name in _FLAGS:
            if not getattr(self, name):
                section[name] = False
        if self.off:
            section['off'] = list(self.off)
        if self.state_off:
            section['state_off'] = list(self.state_off)
        return section or None


def _flag(section, name):
    value = section.get(name, True)
    return value if isinstance(value, bool) else True


def _toggle(ids, action_id, present):
    ids = [item for item in ids if item != action_id]
    if present and isinstance(action_id, str) and action_id and len(ids) < MAX_IDS:
        ids.append(action_id)
    return ids


def Load(path=None):
    import buttonpanelstore
    return Settings(buttonpanelstore.ReadSection(SECTION, path))


def Save(settings, path=None):
    """Store the settings; False (see ``buttonpanelstore.LastError``) when refused."""
    import buttonpanelstore
    return buttonpanelstore.WriteSection(SECTION, settings.ToSection(), path)


def Apply(decor, settings, action_id):
    """The decor as the player wants to see it for this function."""
    if decor is None:
        return EMPTY
    if settings is None:
        return decor
    badge_on = settings.BadgeOn(action_id)
    state_on = settings.StateOn(action_id)
    if badge_on and state_on:
        return decor
    return Decor(
        decor.badge if badge_on else None,
        decor.count if badge_on else 0,
        decor.state if state_on else None,
        decor.remaining if state_on else None,
        decor.total if state_on else None,
        decor.label if state_on else '',
        decor.flash if badge_on else False,
    )
