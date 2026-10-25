# -*- coding: utf-8 -*-
"""Mouse wheel for every scrollable panel: every list scrolls with the wheel while the mouse is over it, like the
inventory pages.

How a wheel notch reaches Python (the engine's CPythonApplication::OnMouseWheel, CWindowManager::RunMouseWheelEvent
and RunMouseWheel, CWindow::OnMouseWheel / RunMouseWheelEvent):

1. OnRunMouseWheel(delta) of the window under the mouse, then of its top window. There a return of None counts as
   consumed (PyCallClassMemberFunc with a bool result), so such a handler must return True / False on purpose.
2. OnMouseWheel(delta) of the window under the mouse, of its parent, ... up to the top window, until one returns a
   true NUMBER (True); None does NOT consume. An instance attribute OnMouseWheel works like a method.
3. Nothing consumed it: the camera zooms, but only when the mouse is over the game itself (FLAG_GAME_SURFACE).

One shared rule instead of a hook in every window: a scroll bar binds itself to the window it is placed in (every
bar class calls Follow from its SetParent) and a list binds the bar it scrolls (SetScrollBar -> Attach). Such a
window - the panel - scrolls its bar by one step on a wheel notch anywhere over it: the arrow step of the bar
(OnUp / OnDown) or one row where the list knows its rows (``step``), the same step as over the bar itself. The
engine asks the deepest window first, so a nested list scrolls before the panel around it. A shown bar consumes the
notch also at its end (nothing else scrolls and the camera stays); a hidden bar (everything fits) lets the notch go
on to the panel around it. The window's own OnMouseWheel (the inventory pages, a zoom, ...) and its own run-wheel
handler (OnRunMouseWheel / SetOnRunMouseWheelEvent: the list's own step) run first and win when they take the
notch. Several bars in one panel: the bar beside the mouse (its height, the first bar right of it). Bind keeps a bar
to one part of a window (a list beside grids that must not scroll it, or a bar placed outside its list). Pages gives
a paged list without a bar (page buttons) the same wheel: up = the previous page, down = the next one.

Pure Python, no engine calls besides wndMgr.GetMousePosition for panels with several bars (MousePosition, the tests
replace it).
"""
from _weakref import ref as _ref
from _weakref import ProxyType as _ProxyType, CallableProxyType as _CallableProxyType


def _MousePosition():
    import wndMgr
    return wndMgr.GetMousePosition()


MousePosition = _MousePosition


class _WeakCall(object):
    """A bound method kept weakly: list -> bar -> list.method would be a cycle that keeps both alive."""

    def __init__(self, method):
        self.obj = _ref(method.__self__)
        self.func = method.__func__

    def __call__(self, *args):
        obj = self.obj()
        if obj is None:
            return None
        return self.func(obj, *args)


def _Real(window):
    """The window behind a weak proxy (some callers pass _weakref.proxy(bar)): proxies take no weak reference and
    are never ``is`` the window. A method read through the proxy is bound to the real object."""
    if isinstance(window, (_ProxyType, _CallableProxyType)):
        try:
            return window.IsShow.__self__
        except (ReferenceError, AttributeError):
            return None
    return window


def _Weak(call):
    if call is not None and getattr(call, '__self__', None) is not None and hasattr(call, '__func__'):
        return _WeakCall(call)
    return call


def _Consumed(result):
    """True for what the engine counts as consumed in OnMouseWheel: a non-zero number (bool included)."""
    return isinstance(result, (bool, int, float)) and bool(result)


def _Shown(window):
    try:
        return bool(window.IsShow())
    except Exception:
        return False


def Scroll(bar, delta):
    """One wheel notch on ``bar`` (delta > 0 = up). True when the notch is taken: the bar is shown (also at its end,
    where nothing moves); False for no bar, a hidden one or no delta."""
    bar = _Real(bar)
    if bar is None or not delta or not _Shown(bar):
        return False
    if getattr(bar, 'lockFlag', False):
        return True                                       # a locked bar (nothing to scroll, shown on purpose)
    up = delta > 0
    try:
        pos = float(bar.GetPos())
    except Exception:
        pos = None
    if pos is not None and ((up and pos <= 0.0) or (not up and pos >= 1.0)):
        return True                                       # at the end: taken, nothing moves, no scroll event
    step = getattr(bar, 'wheelStep', None)
    if callable(step):
        step = step()
    if step is None:
        bar.OnUp() if up else bar.OnDown()
    elif step > 0 and pos is not None:
        bar.SetPos(max(0.0, min(1.0, pos - step if up else pos + step)))
    return True


class Dispatcher(object):
    """``area.OnMouseWheel`` of a panel: the window's own wheel handler first, then the bar beside the mouse."""

    def __init__(self, area, own=None):
        self.area = _ref(area)
        self.own = own                    # an instance handler that was set before (uikit SetWheelEvent, ...)
        self.bars = []
        self.pages = None                 # (previous, next) of a paged list without a bar (Pages)

    def Bars(self):
        bars = [bar for bar in (ref() for ref in self.bars) if bar is not None]
        if len(bars) != len(self.bars):
            self.bars = [_ref(bar) for bar in bars]
        return bars

    def Add(self, bar):
        if not any(ref() is bar for ref in self.bars):
            self.bars.append(_ref(bar))

    def Remove(self, bar):
        self.bars = [ref for ref in self.bars if ref() is not None and ref() is not bar]

    def Pick(self):
        shown = [bar for bar in self.Bars() if _Shown(bar)]
        if len(shown) < 2:
            return shown[0] if shown else None
        try:
            mx, my = MousePosition()
        except Exception:
            return shown[0]

        def distance(bar):
            x, y = bar.GetGlobalPosition()
            w, h = bar.GetWidth(), bar.GetHeight()
            dy = 0 if y <= my <= y + h else min(abs(my - y), abs(my - y - h))
            dx = x - mx if mx <= x + w else 100000 + mx - x - w    # bars stand right of their list
            return dy, dx
        return min(shown, key=distance)

    def __call__(self, delta):
        area = self.area()
        if area is None:
            return False
        own = self.own
        if own is None:
            method = getattr(type(area), 'OnMouseWheel', None)
            if method is not None:
                own = lambda length: method(area, length)
        if own is not None and _Consumed(own(delta)):
            return True
        run = getattr(area, 'OnRunMouseWheel', None)
        if callable(run):
            result = run(delta)           # the panel's own run-wheel (SetOnRunMouseWheelEvent or a method): its step
            if not isinstance(result, (bool, int, float)) or result:
                return True               # None counts as taken, like the engine's step 1
        if Scroll(self.Pick(), delta):
            return True
        if self.pages is not None:
            return (self.pages[0] if delta > 0 else self.pages[1])() is not False
        return False


def Area(area):
    """The dispatcher of ``area`` (installed on first use)."""
    current = area.__dict__.get('OnMouseWheel')
    if isinstance(current, Dispatcher):
        return current
    dispatcher = Dispatcher(area, current)
    area.OnMouseWheel = dispatcher
    return dispatcher


def Attach(bar, area, step=None):
    """The wheel over ``area`` (a panel or a list and everything inside it) scrolls ``bar``. ``step``: the position
    change of one row (a number or a callable, e.g. 1.0 / hidden rows); None keeps the arrow step of the bar."""
    bar, area = _Real(bar), _Real(area)
    if bar is None:
        return
    if step is not None:
        bar.wheelStep = _Weak(step)
    if area is None:
        return
    Area(area).Add(bar)


def Detach(bar, area):
    bar, area = _Real(bar), _Real(area)
    current = area.__dict__.get('OnMouseWheel') if area is not None else None
    if isinstance(current, Dispatcher):
        current.Remove(bar)


def Pages(area, previous, following):
    """A paged list without a bar (page buttons): a notch up over ``area`` shows the previous page, a notch down the
    next one (taken also on the first / last page). A callback returns False when paging does not apply now (the
    notch goes on to the window around)."""
    area = _Real(area)
    if area is not None:
        Area(area).pages = (_Weak(previous), _Weak(following))


def Bind(bar, area, step=None):
    """The wheel scrolls ``bar`` over ``area`` only (not over the whole window the bar is placed in): a list in one
    part of a window whose other parts must not scroll it, or a bar placed outside its list."""
    bar = _Real(bar)
    if bar is None:
        return
    previous = bar.__dict__.get('wheelParent')
    previous = previous() if previous is not None else None
    if previous is not None:
        Detach(bar, previous)
    bar.wheelParent = None
    bar.wheelBound = True
    Attach(bar, area, step)
    Attach(bar, bar)                      # and over the bar itself (its parent no longer forwards the wheel)


def Follow(bar, parent):
    """Called by every scroll bar class from SetParent: the window the bar is placed in is its panel."""
    bar, parent = _Real(bar), _Real(parent)
    if bar is None or bar.__dict__.get('wheelBound'):
        return
    previous = bar.__dict__.get('wheelParent')
    previous = previous() if previous is not None else None
    if previous is not None and previous is not parent:
        Detach(bar, previous)
    if parent is None or not hasattr(parent, '__dict__'):
        bar.wheelParent = None
        return
    try:
        bar.wheelParent = _ref(parent)
    except TypeError:
        bar.wheelParent = None
        return
    Attach(bar, parent)
