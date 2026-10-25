# -*- coding: utf-8 -*-
"""Pohybový systém R1 (Althea): curves, duration tokens and the "unroll" helper shared by the R1 windows.

Source of the numbers: the motion system of the UI round kolo-20261009-jednotny-cil-animace (POHYB-SYSTEM.md, tokens
in pohyb.py) and the animation research of 9. 10. 2026. First user: the unified target form, variant A (uitargetform),
whose unroll was asked to be smoother than the preview (9. 10. 2026): ease-out quint over 240 ms,
the collapse 150 ms, an icon cascade 25 ms apart, a re-toggle reverses from the current height.

Rules every animation here keeps:

* time based: the value is computed from the time since the animation started (app.GetTime(), seconds), never by
  a step per frame, so 30, 60 or 144 FPS run the same length;
* stutter safe: the time between two updates counts at most DT_MAX (50 ms). A frame that took 400 ms (loading,
  a GC pause) continues the motion instead of jumping to its end; a clock that went backwards counts 0;
* integer pixels: Unroll.Height() is a whole pixel and ends exactly on the target;
* reversible: To() during a motion starts the new one from the CURRENT value (never snaps to an end), with a
  duration scaled to the remaining distance;
* nothing here makes windows: the helpers only compute numbers, the caller moves and sizes its own widgets.

Python 2 and 3.
"""
# --------------------------------------------------------------------------- curves (t = 0 .. 1)


def Clamp(t, lo=0.0, hi=1.0):
    return lo if t < lo else (hi if t > hi else t)


def Linear(t):
    """LINEÁRNÍ: rotation, countdown, loading only."""
    return Clamp(t)


def EaseOutCubic(t):
    t = Clamp(t)
    return 1.0 - (1.0 - t) ** 3


def EaseInOutCubic(t):
    """A turn (a click during a motion) and a collapse: starts from rest, ends at rest - no jerk where it turns."""
    t = Clamp(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def EaseOutQuart(t):
    """VSTUP: ease-out quart, cubic-bezier(0.25, 1, 0.5, 1) - opening, appearing, hover."""
    t = Clamp(t)
    return 1.0 - (1.0 - t) ** 4


def EaseOutQuint(t):
    """The unroll of a section: quint decelerates longer than quart, the last pixels settle slowly (smoother)."""
    t = Clamp(t)
    return 1.0 - (1.0 - t) ** 5


def EaseInQuad(t):
    """ODCHOD: ease-in quad, cubic-bezier(0.11, 0, 0.5, 0) - closing, disappearing (alpha only)."""
    t = Clamp(t)
    return t * t


def _BezierTable(p1x, p1y, p2x, p2y, steps=64):
    def bx(s):
        return 3 * (1 - s) ** 2 * s * p1x + 3 * (1 - s) * s * s * p2x + s ** 3

    def by(s):
        return 3 * (1 - s) ** 2 * s * p1y + 3 * (1 - s) * s * s * p2y + s ** 3
    table = []
    for index in range(steps + 1):
        t = float(index) / steps
        lo, hi = 0.0, 1.0
        for _ in range(32):
            mid = (lo + hi) / 2
            if bx(mid) < t:
                lo = mid
            else:
                hi = mid
        table.append(by((lo + hi) / 2))
    table[0], table[-1] = 0.0, 1.0
    return table


_PRESUN = _BezierTable(0.2, 0.0, 0.0, 1.0)


def Presun(t):
    """PŘESUN: M3 standard cubic-bezier(0.2, 0, 0, 1), a 64 step table - a visible element changes size / place."""
    t = Clamp(t)
    position = t * (len(_PRESUN) - 1)
    index = int(position)
    if index >= len(_PRESUN) - 1:
        return 1.0
    frac = position - index
    return _PRESUN[index] + (_PRESUN[index + 1] - _PRESUN[index]) * frac


# --------------------------------------------------------------------------- tokens (ms)
XS = (80, 60)              # (in, out): hover, tooltip out, press back
S = (120, 100)             # tooltip, menu, popup, target board, open by key (alpha only)
M = (200, 130)             # window, side panel, dialog
L = (260, 180)             # big window (map, market, switchbot), toast
TRAVEL = {'xs': 4, 's': 8, 'm': 12}

UNROLL_MS = 240            # a section unrolls (variant A of the target form: 220 - 260 ms asked, quint)
COLLAPSE_MS = 150          # a section collapses (shorter: what leaves must not hold the player)
STAGGER_MS = 25            # columns of icons / rows one after another (20 - 30 ms)
STAGGER_MAX = 8            # at most 8 steps in a wave, the rest together
CONTENT_FROM = 0.4         # the content of an unrolling section starts at 40 % of the unroll
REVERSE_MIN = 0.35         # a reversed / partial motion lasts at least 35 % of its full time
DT_MAX = 0.05              # s: one update counts at most this much time (stutter does not skip the motion)


def Now():
    """app.GetTime() in seconds (float); 0.0 without the client (tools, tests)."""
    try:
        import app
        return float(app.GetTime())
    except Exception:
        return 0.0


class Clock(object):
    """Time since a start, from app.GetTime() samples: every step counts at most DT_MAX, backwards counts 0."""

    def __init__(self, now=None):
        self.last = Now() if now is None else float(now)
        self.elapsed = 0.0

    def Tick(self, now=None):
        now = Now() if now is None else float(now)
        dt = now - self.last
        if dt < 0.0:
            dt = 0.0
        elif dt > DT_MAX:
            dt = DT_MAX
        self.elapsed += dt
        self.last = now
        return self.elapsed


def CascadeDelay(index, duration_ms=UNROLL_MS, start=CONTENT_FROM, stagger_ms=STAGGER_MS, cap=STAGGER_MAX):
    """Seconds after the unroll started when step ``index`` (a column of icons, a row) appears."""
    return (duration_ms * start + min(max(0, int(index)), cap) * stagger_ms) / 1000.0


def CascadeDue(elapsed, count, duration_ms=UNROLL_MS, start=CONTENT_FROM, stagger_ms=STAGGER_MS, cap=STAGGER_MAX):
    """How many of ``count`` steps are due ``elapsed`` seconds after the unroll started."""
    due = 0
    for index in range(int(count)):
        if elapsed + 1e-9 >= CascadeDelay(index, duration_ms, start, stagger_ms, cap):
            due = index + 1
        else:
            break
    return due


class Unroll(object):
    """A height (or any length) in whole pixels that unrolls to a target and collapses back.

    To(target) starts a motion from the current value: UNROLL_MS with EaseOutQuint when it grows, COLLAPSE_MS with
    EaseInOutCubic when it shrinks; a turn during a motion uses EaseInOutCubic both ways (it starts from rest where
    the old motion turned, so nothing jumps); a motion that covers only part of the full span (a reversal half way,
    a table that got one row more) lasts the same part of the time, at least REVERSE_MIN. Update(now) once a frame; Height() is
    the whole pixel to show, exactly the target at the end."""

    def __init__(self, value=0, open_ms=UNROLL_MS, close_ms=COLLAPSE_MS, open_curve=EaseOutQuint,
                 close_curve=EaseInOutCubic, turn_curve=EaseInOutCubic):
        self.value = float(value)
        self.target = int(value)
        self.origin = float(value)        # where the current motion started
        self.span = 0.0                   # the full span the current motion belongs to
        self.open_ms, self.close_ms = open_ms, close_ms
        self.open_curve, self.close_curve, self.turn_curve = open_curve, close_curve, turn_curve
        self.curve = open_curve
        self.duration = 0.0
        self.clock = None
        self.opening = True

    def IsAnimating(self):
        return self.clock is not None

    def Height(self):
        if self.clock is None:
            return self.target
        return int(self.value + 0.5)

    def Elapsed(self):
        return self.clock.elapsed if self.clock is not None else None

    def Progress(self):
        """0 .. 1 of the current motion (1 when at rest)."""
        if self.clock is None or self.duration <= 0:
            return 1.0
        return Clamp(self.clock.elapsed / self.duration)

    def Set(self, target):
        """Jumps to ``target`` without a motion (a new target, the board closed)."""
        self.value = self.origin = float(int(target))
        self.target = int(target)
        self.clock = None
        self.span = 0.0

    def To(self, target, now=None):
        """Moves to ``target``; True when a motion started (or turned)."""
        target = max(0, int(target))
        if target == self.target:
            return False
        reverse = self.clock is not None and ((target > self.value) != self.opening)
        distance = abs(target - self.value)
        if self.clock is None or reverse:
            span = max(distance, abs(self.target - self.origin), 1.0)
        else:
            span = max(distance, self.span, 1.0)
        self.opening = target > self.value
        if reverse:
            self.curve = self.turn_curve
        else:
            self.curve = self.open_curve if self.opening else self.close_curve
        full = (self.open_ms if self.opening else self.close_ms) / 1000.0
        self.duration = full * max(REVERSE_MIN, min(1.0, distance / span))
        self.span = span
        self.origin = self.value
        self.target = target
        self.clock = Clock(now)
        if distance < 0.5:
            self.Set(target)
            return False
        return True

    def Update(self, now=None):
        """Advances the motion; True when the shown height changed."""
        if self.clock is None:
            return False
        before = self.Height()
        elapsed = self.clock.Tick(now)
        if elapsed >= self.duration:
            self.Set(self.target)
        else:
            self.value = self.origin + (self.target - self.origin) * self.curve(elapsed / self.duration)
        return self.Height() != before
