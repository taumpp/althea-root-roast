# -*- coding: utf-8 -*-
"""R1 label of an announced server maintenance, the "A" variant of the 8. 10. 2026 mock-up.

A 240 x 46 plate, drawn from the R1 kit: the hourglass medallion of the countdowns, "ÚDRŽBA ZA" (Cinzel) and the
time left, a second line "cca 30 min" (the reason, when the server names one, is in the hover hint) and a vein
along the bottom that runs down with the time. Up to 5 minutes it is calm graphite, below that and in the last minute
a dark blood red wash lies over it (never a light red, never gold). The kit's own X (uir1.Close, close/x_*.png)
hides it until the end of the announcement; in the last minute it comes back without the X (the owner decides that
in uimaintenance.MaintenanceIndicator, this module only draws what it is told).

Where it stands: the player can drag it anywhere and the place is remembered (UserData/maintenance_hud, the file the
original table uses, under its own key). Until then it stands right of the affect icons (L1: affects' right edge +
12 px, y 10); where that would run into the targeting board (more than the centre of the screen - 410 px) it stands
in the corner (L2: 10, 8) and the affects and the party panel make room, 50 px lower, while it is shown.

Settings -> "Starý vzhled" keeps the original table (uimaintenance.MaintenanceBoard). A failure is traced
(uir1.TraceFailure) and the original table takes over; R1 is not tried again in this session. No client imports but
the kit: the module also runs on Python 2 (u'' texts), colours go to SetPackedFontColor signed (the x64 binding
ignores values >= 0x80000000).
"""
import weakref

import ui
import wndMgr

import pvmhudposition
import uikit
import uir1
import uir1minimapaart as A
import uir1tokens as T

WHAT = u'indikátor údržby'

# The place the player chose is a presentation preference of this client installation (like the original table's).
POSITION_DIRECTORY = 'UserData/maintenance_hud'
POSITION_KEY = 'maintenance-label'

WIDTH, HEIGHT = 240, 46
MEDALLION = A.ROOT + 'medallion/shortcuts/information_countdowns_normal.png'   # 28 x 28
MEDALLION_X, MEDALLION_Y = 8, 8
TEXT_X = 44
TITLE_Y, TIME_Y, SUB_Y = 14, 13, 32          # centres of the text lines
TIME_RIGHT = WIDTH - 31                       # right edge of the time, the X lies right of it
CLOSE_X, CLOSE_Y = WIDTH - 24, 4              # the 20 px hit box; the 10 px glyph lies 9 px from the right edge
BAR_X, BAR_Y, BAR_W = 8, HEIGHT - 6, WIDTH - 16
WASH_INSET = 3                                # the frame's lines

SOON, LAST = 300, 60                          # seconds: the wash begins / the last minute
MARGIN, GAP, TOP = 10, 12, 10                 # L1: affects start at (10, 10), 12 px gap
CORNER_TOP = 8                                # L2
CORNER_SHIFT = 50                             # L2: the affects and the party panel are this much lower
CENTRE_CLEARANCE = 410                        # the target board is centred, 170 px each way; plus the label's 240

# colour, alpha (a wash over the dark panel); None = nothing
WASH = {'calm': None, 'soon': (0x241112, 0.55), 'last': (0x4A0708, 0.8)}
TITLE_COLOR = {'calm': T.INK_DIM, 'soon': T.INK, 'last': T.INK}
TIME_COLOR = {'calm': T.IVORY, 'soon': T.IVORY, 'last': 0xFFFFF0E8}
SUB_COLOR = {'calm': T.MUTED, 'soon': T.INK_DIM, 'last': T.INK_DIM}
FILL_COLOR = {'calm': T.RED_DK, 'soon': T.RED, 'last': T.RED}
TRACK = 0x2E2A2A

# Reason ids of the server's presets (maintenance_reason <id>): Czech, English.
REASONS = {
    1: (u'aktualizace hry', u'game update'),
    2: (u'oprava chyb', u'bug fixes'),
    3: (u'restart serveru', u'server restart'),
}

_failed = []


def Signed(color):
    """A packed colour for SetPackedFontColor: the x64 binding ignores values >= 0x80000000 (PRAVIDLA-UI, Kód)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color & 0x80000000 else color


def UseR1():
    """The R1 label unless "Starý vzhled" is chosen or it already failed in this session."""
    return not _failed and uir1.UseR1()


def Fail():
    _failed.append(True)
    uir1.TraceFailure(WHAT)


def Stage(remaining):
    if remaining <= LAST:
        return 'last'
    return 'soon' if remaining <= SOON else 'calm'


def Clock(seconds):
    """14:59, from an hour 1:14:59 (no 45.23 sec of the original table)."""
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return '%d:%02d:%02d' % (hours, minutes, seconds)
    return '%02d:%02d' % (minutes, seconds)


def DurationText(duration):
    """"30 min", "1 h", "1 h 30 min" for a duration in seconds (never less than a minute)."""
    minutes = max(1, (int(duration) + 59) // 60)
    hours, minutes = divmod(minutes, 60)
    if hours and minutes:
        return '%d h %d min' % (hours, minutes)
    if hours:
        return '%d h' % hours
    return '%d min' % minutes


def SubText(duration):
    return uikit.Tr_(u'cca %s', u'about %s') % DurationText(duration)


def ReasonText(reason):
    """The preset's text in the client language, or None (no reason, or an id this client does not know)."""
    names = REASONS.get(reason)
    return uikit.Tr_(names[0], names[1]) if names else None


def HintText(reason):
    parts = []
    text = ReasonText(reason)
    if text:
        parts.append(uikit.Tr_(u'Důvod údržby: %s', u'Maintenance reason: %s') % text)
    else:
        parts.append(uikit.Tr_(u'Údržba serveru', u'Server maintenance'))
    parts.append(uikit.Tr_(u'štítek lze přetáhnout myší', u'you can drag this label'))
    return u' · '.join(parts)


def _ref(window):
    if window is None:
        return None
    try:
        return weakref.ref(window)
    except TypeError:                        # no weak references: keep it (a window of the game lives on anyway)
        return lambda window=window: window


def _deref(reference):
    return reference() if reference is not None else None


class Reserve(object):
    """Makes room under the corner label (L2): the windows go ``CORNER_SHIFT`` px down and, once it leaves the corner,
    exactly as far back (relative, so a window that moves for another reason is not put back to a stale place)."""

    def __init__(self):
        self.moved = []

    def Set(self, windows, on):
        if on and not self.moved:
            for window in windows:
                if window is None:
                    continue
                x, y = window.GetGlobalPosition()
                window.SetPosition(x, y + CORNER_SHIFT)
                self.moved.append(_ref(window))
        elif not on and self.moved:
            for reference in self.moved:
                window = _deref(reference)
                if window is not None:
                    x, y = window.GetGlobalPosition()
                    window.SetPosition(x, y - CORNER_SHIFT)
            self.moved = []


class Plate(ui.Window):
    """Transparent plate over the label: a left press starts the drag, the hover shows the hint. The X lies over it
    (made later, picks first)."""

    def __init__(self, owner):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.SetParent(owner)
        self.SetPosition(0, 0)
        self.SetSize(WIDTH, HEIGHT)
        self.AddFlag('dragable')
        self.Show()

    def OnMouseLeftButtonDown(self):
        self.owner.BeginDrag()
        return True

    def OnMouseDrag(self, x, y):
        self.owner.Drag()

    def OnMouseLeftButtonUp(self):
        self.owner.EndDrag()
        return True

    def OnMouseOverIn(self):
        self.owner.ShowHint(self)

    def OnMouseOverOut(self):
        uir1.HideHint()


class HideButton(uir1.Close):
    """The kit's X with its hover hint ("Skrýt (v poslední minutě se vrátí)")."""

    def __init__(self, parent, kit, x, y, event):
        uir1.Close.__init__(self, parent, x, y, event)
        self.kit = kit

    def OnMouseOverIn(self):
        uir1.Close.OnMouseOverIn(self)
        uir1.ShowHint(self.kit, self, uikit.Tr_(u'Skrýt (v poslední minutě se vrátí)',
                                                  u'Hide (it returns in the last minute)'))

    def OnMouseOverOut(self):
        uir1.Close.OnMouseOverOut(self)
        uir1.HideHint()


class Label(ui.Window):
    """The R1 label. It draws what ``SetState`` says and keeps its place; the announcement is not its business."""

    def __init__(self, on_hide):
        ui.Window.__init__(self, 'UI_BOTTOM')
        self.AddFlag('float')
        self.SetSize(WIDTH, HEIGHT)
        self.kit = uir1.Kit()
        self.onHide = on_hide
        self.stage = None
        self.stateKey = None
        self.reason = 0
        self.shower = self.party = None
        self.reserve = Reserve()
        self.saved = LoadPosition()
        self.placed = None
        self.screenSize = None
        self.dragOrigin = None
        self.dragMoved = False

        # Draw order = creation order; later controls pick first.
        self.frame = uir1.Frame(self, 0, 0, WIDTH, HEIGHT, 'window')
        inner = (WIDTH - 2 * WASH_INSET, HEIGHT - 2 * WASH_INSET)
        self.wash = uikit.Rect(self, WASH_INSET, WASH_INSET, inner[0], inner[1], 0x000000, 0.0)
        self.wash.Hide()
        self.medallion = ui.ExpandedImageBox()          # the minimap art's root, not the kit's: native 28 x 28
        self.medallion.SetParent(self)
        self.medallion.AddFlag('not_pick')
        self.medallion.LoadImage(MEDALLION)
        self.medallion.SetPosition(MEDALLION_X, MEDALLION_Y)
        self.medallion.Show()
        self.title = uir1.Text(self, uikit.Upper(uikit.Tr_(u'Údržba za', u'Maintenance in')), TEXT_X, TITLE_Y,
                               self.kit.font('button_s'), Signed(T.INK_DIM))
        self.time = uir1.Text(self, '', TIME_RIGHT, TIME_Y, self.kit.font('text_l'), Signed(T.IVORY), align='right')
        self.sub = uir1.Text(self, '', TEXT_X, SUB_Y, self.kit.font('text_xs'), Signed(T.MUTED))
        self.track = uikit.Rect(self, BAR_X, BAR_Y, BAR_W, 2, TRACK, 1.0)
        self.fill = uikit.Rect(self, BAR_X, BAR_Y, BAR_W, 2, T.RED_DK, 1.0)
        self.glow = uikit.Rect(self, BAR_X, BAR_Y + 2, BAR_W, 1, T.RED, 0.27)
        self.plate = Plate(self)
        self.close = HideButton(self, self.kit, CLOSE_X, CLOSE_Y, self.OnClose)

    def __del__(self):
        ui.Window.__del__(self)

    # -- what to draw
    def SetNeighbours(self, shower, party):
        self.shower, self.party = _ref(shower), _ref(party)

    def SetState(self, remaining, duration, reason, total, closable):
        """Time left (s), the announced duration (s), the reason id (0 = none), the time left when it was announced
        (the vein is full then) and whether the X is offered."""
        key = (int(remaining), int(duration), int(reason), int(total), bool(closable))
        if key == self.stateKey:
            return
        self.stateKey = key
        remaining, duration, reason, total, closable = key
        self.reason = reason
        self.time.SetText(Clock(remaining))
        self.sub.SetText(SubText(duration))
        stage = Stage(remaining)
        if stage != self.stage:
            self.stage = stage
            self.Restyle(stage)
        width = int(round(BAR_W * max(0.0, min(1.0, remaining / float(max(1, total))))))
        if width > 0:
            self.fill.SetSize(width, 2)
            self.fill.Show()
        else:
            self.fill.Hide()
        if closable:
            self.close.Show()
        else:
            self.close.Hide()
            uir1.HideHint()

    def Restyle(self, stage):
        self.title.SetPackedFontColor(Signed(TITLE_COLOR[stage]))
        self.time.SetPackedFontColor(Signed(TIME_COLOR[stage]))
        self.sub.SetPackedFontColor(Signed(SUB_COLOR[stage]))
        self.fill.SetColor(uikit.GenerateColor(FILL_COLOR[stage], 1.0))
        wash = WASH[stage]
        if wash is None:
            self.wash.Hide()
        else:
            self.wash.SetColor(uikit.GenerateColor(wash[0], wash[1]))
            self.wash.Show()

    def OnClose(self):
        uir1.HideHint()
        if self.onHide:
            self.onHide()

    def ShowHint(self, widget):
        if self.dragOrigin is None:
            uir1.ShowHint(self.kit, widget, HintText(self.reason))

    # -- where it stands
    def GetScreenSize(self):
        return (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())

    def DefaultPlace(self, screen):
        """((x, y), corner): L1 right of the affects, or L2 in the corner when L1 would reach the target board."""
        shower = _deref(self.shower)
        x = MARGIN
        width = 0
        if shower is not None:
            try:
                width = int(shower.GetWidth())
                if width > 0:
                    x = int(shower.GetGlobalPosition()[0]) + width + GAP
            except Exception:
                width = 0
                x = MARGIN
        if width > 0 and x > max(MARGIN, screen[0] // 2 - CENTRE_CLEARANCE):
            return (MARGIN, CORNER_TOP), True
        return (x, TOP), False

    def Place(self):
        if self.dragOrigin is not None:
            return
        screen = self.GetScreenSize()
        if self.saved is not None:
            position = pvmhudposition.clamp(self.saved, (WIDTH, HEIGHT), screen)
            corner = False
        else:
            position, corner = self.DefaultPlace(screen)
        if position != self.placed or screen != self.screenSize:
            self.placed, self.screenSize = position, screen
            self.SetPosition(position[0], position[1])
        self.reserve.Set((_deref(self.shower), _deref(self.party)), corner and self.IsShow())

    # -- the drag
    def BeginDrag(self):
        self.SetTop()
        uir1.HideHint()
        self.dragOrigin = (wndMgr.GetMousePosition(), self.GetGlobalPosition())
        self.dragMoved = False

    def Drag(self):
        if self.dragOrigin is None:
            return
        (mouseX, mouseY), (x, y) = self.dragOrigin
        nowX, nowY = wndMgr.GetMousePosition()
        if (nowX, nowY) != (mouseX, mouseY) or self.dragMoved:
            self.dragMoved = True
            self.saved = pvmhudposition.clamp((x + nowX - mouseX, y + nowY - mouseY), (WIDTH, HEIGHT),
                                              self.GetScreenSize())
            self.placed = self.saved
            self.SetPosition(self.saved[0], self.saved[1])
            self.reserve.Set((), False)

    def EndDrag(self):
        if self.dragOrigin is None:
            return
        self.dragOrigin = None
        if self.dragMoved and self.saved is not None:
            SavePosition(self.saved)
        self.dragMoved = False

    # -- window
    def Show(self):
        ui.Window.Show(self)
        self.Place()

    def Hide(self):
        self.EndDrag()
        uir1.HideHint()
        self.reserve.Set((), False)
        ui.Window.Hide(self)

    def Destroy(self):
        self.Hide()
        self.close = self.plate = None


def LoadPosition():
    try:
        return pvmhudposition.load(POSITION_KEY, POSITION_DIRECTORY)
    except Exception:
        return None


def SavePosition(position):
    try:
        return pvmhudposition.save(POSITION_KEY, position, POSITION_DIRECTORY)
    except Exception:
        return False
