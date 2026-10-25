"""One hover surface for the whole active-effect bar (root/uiaffectshower.py, top left).

Every icon of the bar (effects, the Buffy / Bohové / Dovednosti / Rosy groups, the biolog passives, the skill tree,
the horse, the lover, Sungma, multi-farm) asks this controller to show its tooltip or summary instead of showing it
itself. The controller keeps exactly one surface visible: the one of the icon under the mouse.

- Over sets the hovered icon. Out clears it only when it is still the hovered one (Over B before Out A, the order of a
  fast move or of a missed event, never hides B), and on the bar it is left to the next frame check: the engine calls
  Out before it switches the pointed window and checks the mouse every rendered frame, the bar's OnUpdate runs at most
  60 times a second, so an Out in the 3 px gap between two icons hid the tooltip for the rendered frames up to the next
  UI tick (blinking at more than 60 FPS).
- The owner's OnUpdate checks the hovered icon against the mouse every frame (Update), so a missed Out, an icon that was
  hidden, moved or destroyed under the mouse, or an Over that never came does not leave a stale tooltip.
- With `within` (the mouse is on the owner window itself, i.e. in the gap of an icon's cell) that check runs without
  any Over too: a mouse coming to rest in the gap shows the icon the hit test gives the gap to.
- Entering the bar from outside waits DELAY; while a surface is up or for WARM after it closed, the next icon shows at
  once, with a shorter wait and a longer warm time.
- A ShowHover / TickHover that raises does not leave the controller believing a surface is up: the icon is tried again
  when the mouse comes back to it, and the error goes once to `report` (syserr in game).
- A group summary is a hoverable panel under its icon: it stays while the mouse crosses to it, and an icon in the row
  below takes over only after PANEL_SWITCH (the short crossing over the next row towards the panel).

Pure Python (no engine module), so the CI tests run it for real.

The protocol of a target (an icon window):
  ShowHover() -> hide callable or None   build (or reuse) and show its surface; the callable hides exactly that surface
                                          and must not hold the icon itself (an icon can be destroyed while shown)
  TickHover() -> hide callable or None   optional, once a second while shown (remaining time)
  HoverHeld() -> bool                     optional, the surface still wants to stay without the mouse on the icon
  HoverGuard(other) -> bool               optional, `other` must wait PANEL_SWITCH before replacing this surface
"""
import traceback
import weakref

DELAY = 0.12
WARM = 1.0
PANEL_SWITCH = 0.1


def _Ref(target):
    if target is None:
        return None
    try:
        return weakref.ref(target)
    except TypeError:
        return lambda target=target: target


def _Deref(ref):
    if ref is None:
        return None
    try:
        return ref()
    except ReferenceError:
        return None


def _Call(target, name, *args):
    method = getattr(target, name, None)
    if method is None:
        return None
    try:
        return method(*args)
    except ReferenceError:
        return None


class HoverController(object):
    def __init__(self, clock, pointed=None, delay=DELAY, warm=WARM, panelSwitch=PANEL_SWITCH, report=None,
                 within=None):
        self.clock = clock
        self.pointed = pointed
        self.within = within
        self.report = report
        self.reported = set()
        self.failed = None
        self.delay = delay
        self.warm = warm
        self.panelSwitch = panelSwitch
        self.hovered = None
        self.hoveredSince = 0.0
        self.shown = None
        self.hide = None
        self.warmUntil = None

    # Events of the icons.
    def Over(self, target):
        if _Deref(self.hovered) is not target:
            self.hovered = _Ref(target)
            self.hoveredSince = self.clock()
        if _Deref(self.shown) is target:
            # A new entry onto the icon whose surface is up (its Out was missed, or its panel closed meanwhile):
            # show it again; the content is reused when its data did not change.
            hide, ok = self._Safe(target, "ShowHover")
            if ok:
                self.hide = hide
            else:
                self._Failed(target)
            return
        self._Reconcile(self.clock())

    def Out(self, target):
        if self.pointed is not None:
            # The next frame check decides by the mouse position (see the module doc): no hide in a gap of the bar.
            return
        if _Deref(self.hovered) is target:
            self.hovered = None
        self._Reconcile(self.clock())

    # Called by the bar every frame.
    def Update(self):
        now = self.clock()
        if self.hovered is None and self.shown is None and (self.warmUntil is None or now > self.warmUntil):
            if not self._Within():
                return                              # the mouse is away from the bar: nothing to check
        if self.pointed is not None:
            hovered = _Deref(self.hovered)
            under = self.pointed(hovered)
            if under is not hovered:
                self.hovered = _Ref(under)
                self.hoveredSince = now
        self._Reconcile(now)

    # Called by the bar once a second: the remaining time of the shown surface.
    def Tick(self):
        shown = _Deref(self.shown)
        if shown is None:
            return
        hide, ok = self._Safe(shown, "TickHover")
        if hide is not None:
            self.hide = hide

    def _Within(self):
        """The mouse is on the owner window itself, between its targets. An icon's gap (3 px to the
        right, 4 px below a 22 px icon) is the bar window for the engine, so a mouse that comes to rest there never
        sends an icon's Over, yet the hit test gives the gap to that icon: without this check nothing showed until
        the mouse was moved onto the icon itself ("někdy ne, někdy až za pár sekund")."""
        if self.within is None or self.pointed is None:
            return False
        try:
            return bool(self.within())
        except ReferenceError:
            return False

    def Reset(self):
        self._HideShown(None)
        self.hovered = None
        self.warmUntil = None
        self.failed = None

    def Shown(self):
        return _Deref(self.shown)

    def _Reconcile(self, now):
        hovered = _Deref(self.hovered)
        if self.hovered is not None and hovered is None:
            self.hovered = None
        shown = _Deref(self.shown)
        if self.shown is not None and shown is None:
            self._HideShown(now)                    # the icon died under the mouse: its surface goes with it
        if hovered is not None and hovered is shown:
            return
        failed = _Deref(self.failed)
        if failed is not None and failed is not hovered:
            self.failed = None
        elif failed is not None:
            return                                  # its ShowHover raised: again when the mouse comes back to it
        if hovered is None:
            if shown is not None and _Call(shown, "HoverHeld"):
                return
            if self.shown is not None:
                self._HideShown(now)
            return
        if shown is not None and _Call(shown, "HoverHeld") and _Call(shown, "HoverGuard", hovered):
            if now - self.hoveredSince < self.panelSwitch:
                return
        warm = self.shown is not None or (self.warmUntil is not None and now <= self.warmUntil)
        if not warm and now - self.hoveredSince < self.delay:
            return
        self._HideShown(now)
        self._Show(hovered)

    def _Show(self, target):
        self.shown = _Ref(target)
        hide, ok = self._Safe(target, "ShowHover")
        self.hide = hide
        if not ok:
            self._Failed(target)

    def _Failed(self, target):
        self.shown = None
        self.hide = None
        self.failed = _Ref(target)

    def _Safe(self, target, name):
        """(result, True), or (None, False) when the method raised; the first error of each kind goes to report."""
        try:
            return _Call(target, name), True
        except Exception:
            key = (type(target).__name__, name)
            if self.report is not None and key not in self.reported:
                self.reported.add(key)
                try:
                    self.report("uiaffecthover: %s.%s failed\n%s" % (key[0], name, traceback.format_exc()))
                except Exception:
                    pass
            return None, False

    def _HideShown(self, now):
        hide, self.hide = self.hide, None
        wasShown = self.shown is not None
        self.shown = None
        if hide is not None:
            try:
                hide()
            except ReferenceError:
                pass
        if wasShown and now is not None:
            self.warmUntil = now + self.warm


# The controller of the bar in game; without one (a bare icon, a test) the icons still keep one surface, at once.
_fallback = HoverController(lambda: 0.0, delay=0.0, warm=0.0, panelSwitch=0.0)
_current = None


def Install(controller):
    global _current
    _current = controller


def Uninstall(controller):
    global _current
    if _current is controller:
        _current = None


def Controller():
    return _current or _fallback


def Over(target):
    Controller().Over(target)


def Out(target):
    Controller().Out(target)


# The shared game tooltips (interface.tooltipItem / tooltipSkill) are filled by many windows. A stamp says which icon
# filled one and from which data: the same icon with the same data shows the built tooltip again instead of rebuilding
# it, and an icon hides the tooltip only while the tooltip still shows its content. ClearToolTip of any other window
# replaces childrenList, which voids the stamp.
_generation = [0]


def Invalidate():
    """Data every cached tooltip depends on changed (skill grades): the next show rebuilds."""
    _generation[0] += 1


def Owner(owner):
    return id(owner)


def Owns(tooltip, ownerId, key=None):
    stamp = getattr(tooltip, "affectHoverStamp", None)
    if not stamp or stamp[0] is not getattr(tooltip, "childrenList", None) or stamp[1] != ownerId:
        return False
    return key is None or stamp[2] == (_generation[0], key)


def Fill(tooltip, owner, key, build):
    """Build `owner`'s content into `tooltip` unless it already shows exactly that. True when it was rebuilt."""
    ownerId = Owner(owner)
    if Owns(tooltip, ownerId, key):
        return False
    tooltip.ClearToolTip()
    build(tooltip)
    FitContent(tooltip)
    tooltip.affectHoverStamp = (getattr(tooltip, "childrenList", None), ownerId, (_generation[0], key))
    return True


def FitContent(tooltip, padding=30):
    """The tooltip is at least as wide as its widest text line ("Kliknutím zapnout/vypnout Multi-Farm"
    built with AppendTextLine, which never widens, stuck out of a 190 px box and, at the left screen edge, out of the
    screen). Centred lines stay centred; the box then follows the mouse inside the screen (ToolTip OnUpdate)."""
    width = getattr(tooltip, "toolTipWidth", None)
    children = getattr(tooltip, "childrenList", None)
    if width is None or not children:
        return
    needed = width
    for child in children:
        size = getattr(child, "GetTextSize", None)
        if size is None:
            continue
        try:
            needed = max(needed, int(size()[0]) + padding)
        except Exception:
            continue
    if needed <= width:
        return
    oldCenter = width // 2
    tooltip.toolTipWidth = needed
    for child in children:
        try:
            x, y = child.GetLocalPosition()
        except Exception:
            continue
        if x == oldCenter:
            child.SetPosition(needed // 2, y)
    resize = getattr(tooltip, "ResizeToolTip", None)
    if resize is not None:
        resize()


def Hider(tooltip, owner):
    """Hide `tooltip` if it still shows `owner`'s content; holds no reference to the owner."""
    ownerId = Owner(owner)

    def hide():
        if Owns(tooltip, ownerId):
            tooltip.HideToolTip()
    return hide


def ShowTooltip(tooltip, owner, key, build):
    if tooltip is None:
        return None
    Fill(tooltip, owner, key, build)
    tooltip.ShowToolTip()
    return Hider(tooltip, owner)
