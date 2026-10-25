"""Runtime of the button-panel badges: one shared evaluation, overlays per panel.

Every panel (minimap launchers, inventory rail, the More/picker board) owns a
``PanelBadges``: ``Sync`` tells it which button shows which function, ``SetMore``
names its "More" control and the functions behind it, ``Update`` (called from
the panel's ``OnUpdate``) refreshes the overlays. Provider results are shared by
all panels and recomputed at most every ``INTERVAL`` seconds; the player's
settings (``badges`` section) are cached until ``Invalidate``.
"""
import app

import buttonpanelbadges as badges
import buttonpanelstatus as status
import uibuttonpaneldecor as decor

INTERVAL = 0.5
BATTLE_PASS = 'system.battle_pass'

_shared = {'time': None, 'decors': {}, 'settings': None, 'revision': 0}


def Settings():
    if _shared['settings'] is None:
        try:
            _shared['settings'] = badges.Load()
        except Exception:
            _shared['settings'] = badges.Settings()
    return _shared['settings']


def Invalidate():
    """Settings changed (settings block, right-click menu): reload and redraw now."""
    _shared['settings'] = None
    _shared['time'] = None
    _shared['revision'] += 1


def Evaluate(interface, action_ids):
    """Shown decor per function (settings applied); providers run once per interval."""
    now = app.GetTime()
    if _shared['time'] is None or now - _shared['time'] >= INTERVAL:
        _shared['time'] = now
        _shared['decors'] = {}
    cache = _shared['decors']
    missing = [action_id for action_id in action_ids if action_id not in cache]
    if missing:
        context = status.Context(interface)
        if BATTLE_PASS in missing:
            try:
                status.PrefetchBattlePass(context)
            except Exception:
                pass
        cache.update(status.Evaluate(missing, context))
    settings = Settings()
    return dict((action_id, badges.Apply(cache.get(action_id), settings, action_id)) for action_id in action_ids)


class PanelBadges(object):
    """Overlays of one panel. ``suppress(action_id, button)`` may hide a badge
    where the button already shows another one (the pet-album count)."""

    def __init__(self, kind, suppress=None):
        self.kind = kind
        self.suppress = suppress
        self.overlays = {}    # id(button) -> [button, overlay, action id]
        self.more = []        # [[button, overlay]] of the "More" controls
        self.more_ids = ()
        self.revision = None

    def Sync(self, pairs):
        """``pairs`` = [(button, action id)] currently shown; others lose their overlay."""
        wanted = {}
        for button, action_id in pairs:
            if button is not None and action_id:
                wanted[id(button)] = (button, action_id)
        for key in list(self.overlays):
            if key not in wanted:
                self.overlays.pop(key)[1].Destroy()
        for key, (button, action_id) in wanted.items():
            entry = self.overlays.get(key)
            if entry is None:
                self.overlays[key] = [button, decor.ButtonDecor(button, self.kind), action_id]
            elif entry[2] != action_id:
                entry[2] = action_id
                entry[1].SetDecor(badges.EMPTY)
        self.revision = None

    def SetMore(self, controls, action_ids):
        """"More" controls ``[(button, dot position)]`` show one dot when a function
        behind them (``action_ids``) has a badge."""
        wanted = [(button, dot) for button, dot in (controls or ()) if button is not None]
        keep = dict((id(button), True) for button, unused in wanted)
        for entry in list(self.more):
            if id(entry[0]) not in keep:
                entry[1].Destroy()
                self.more.remove(entry)
        present = set(id(entry[0]) for entry in self.more)
        for button, dot in wanted:
            if id(button) not in present:
                self.more.append([button, decor.ButtonDecor(button, decor.KIND_DOT, dot=dot)])
        self.more_ids = tuple(action_ids or ())

    def Update(self, interface, force=False):
        if not self.overlays and not self.more:
            return
        ids = [entry[2] for entry in self.overlays.values()] + list(self.more_ids)
        shown = Evaluate(interface, ids)
        settings = Settings()
        pulse = settings.pulse
        for button, overlay, action_id in self.overlays.values():
            value = shown.get(action_id, badges.EMPTY)
            if value.badge and self.suppress is not None and self.suppress(action_id, button):
                value = badges.Decor(None, 0, value.state, value.remaining, value.total, value.label)
            overlay.SetDecor(value, pulse)
        if self.more:
            merged = badges.Strongest(shown.get(action_id) for action_id in self.more_ids)
            for unused_button, overlay in self.more:
                overlay.SetDecor(merged, pulse)

    def Destroy(self):
        for button, overlay, unused in self.overlays.values():
            overlay.Destroy()
        self.overlays = {}
        for unused_button, overlay in self.more:
            overlay.Destroy()
        self.more = []
        self.more_ids = ()


def ContextEntries(action_id):
    """Per-button switches for the right-click menus ("Odznak", "Stav/odpočet")."""
    import uisettingsbuttonbadges
    has_badge, has_state = status.Capabilities(action_id)
    return tuple(uisettingsbuttonbadges.ContextEntries(action_id, has_badge, has_state, on_change=Invalidate))
