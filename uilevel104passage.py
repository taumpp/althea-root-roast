# -*- coding: utf-8 -*-
"""Level104 passage progress: compact R1 chrome and client-only placement.

The server owns the count, phase and deadline. Dragging never sends a game
command. Position is stored once after a completed drag, not in OnUpdate.
"""
import app
import localeInfo
import passagetrialstate
import player
import weakref
import wndMgr
import ui
import pvmhudposition
import uir1
import uir1tokens as T
from uir1hud import Signed

WIDTH, HEIGHT = 216, 56
def _Text(key):
    # locale_game.txt of the client language; the key itself if a pack lacks it.
    return getattr(localeInfo, key, key)
POSITION_DIRECTORY = 'UserData/level104_passage_hud'


class DragPlate(ui.Window):
    """Same captured drag interaction as the existing R1 maintenance HUD."""
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


class TrialHud(ui.Window):
    def __init__(self):
        # ui.Window.__init__ invokes the virtual Hide() during registration.
        self.dragOrigin = None
        self.dragMoved = False
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.SetSize(WIDTH, HEIGHT)
        self.phase = 0
        self.deadline = 0
        self.lastSecond = -1
        self.progressKey = None
        self.dragOrigin = None
        self.dragMoved = False
        self.positionKey = player.GetName()
        self.saved = pvmhudposition.load(self.positionKey, POSITION_DIRECTORY)
        self.screen = self.ScreenSize()
        start = self.saved if self.saved is not None else ((self.screen[0] - WIDTH) // 2, 55)
        self.SetPosition(*pvmhudposition.clamp(start, (WIDTH, HEIGHT), self.screen))
        self.kit = uir1.Kit()
        self.frame = uir1.Frame(self, 0, 0, WIDTH, HEIGHT, 'window')
        self.title = uir1.Text(self, _Text("LEVEL104_PASSAGE_HUD_TITLE"), 10, 13,
                               self.kit.font('button_s'), Signed(T.INK_DIM))
        self.vein = uir1.Vein(self, 6, 25, WIDTH - 12)
        self.progress = uir1.Text(self, '', 10, 39,
                                  self.kit.font('tahoma'), Signed(T.INK))
        self.clock = uir1.Text(self, '', WIDTH - 10, 39,
                               self.kit.font('tahoma'), Signed(T.IVORY), align='right')
        self.plate = DragPlate(self)
        self.Hide()

    def ScreenSize(self):
        return (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())

    def BeginDrag(self):
        self.SetTop()
        self.dragOrigin = (wndMgr.GetMousePosition(), self.GetGlobalPosition())
        self.dragMoved = False

    def Drag(self):
        if self.dragOrigin is None:
            return
        (mx, my), (x, y) = self.dragOrigin
        nx, ny = wndMgr.GetMousePosition()
        position = pvmhudposition.clamp((x + nx - mx, y + ny - my),
                                        (WIDTH, HEIGHT), self.ScreenSize())
        if position != self.GetGlobalPosition():
            self.SetPosition(*position)
            self.saved = position
            self.dragMoved = True

    def EndDrag(self):
        if getattr(self, 'dragOrigin', None) is None:
            return
        self.dragOrigin = None
        if self.dragMoved and self.saved is not None:
            pvmhudposition.save(self.positionKey, self.saved, POSITION_DIRECTORY)
        self.dragMoved = False

    def Receive(self, phase, count, goal, remaining):
        self.phase = int(phase)
        passagetrialstate.SetPhase(self.phase)
        if self.phase == 0:
            self.Hide()
            return
        key = (self.phase, int(count), int(goal))
        if key != self.progressKey:
            self.progressKey = key
            label = _Text("LEVEL104_PASSAGE_HUD_FIRST_HIT") if self.phase == 1 else _Text("LEVEL104_PASSAGE_HUD_COUNT") % key[1:]
            self.progress.SetText(label)
        self.deadline = app.GetTime() + max(0, int(remaining))
        # A progress packet updates data only: never recenter a dragged HUD.
        self.Show()
        self.OnUpdate()

    def OnUpdate(self):
        if not self.phase:
            return
        screen = self.ScreenSize()
        if screen != self.screen:
            self.screen = screen
            self.SetPosition(*pvmhudposition.clamp(self.GetGlobalPosition(), (WIDTH, HEIGHT), screen))
        seconds = max(0, int(self.deadline - app.GetTime() + 0.999))
        if seconds != self.lastSecond:
            self.lastSecond = seconds
            self.clock.SetText('%02d:%02d' % (seconds // 60, seconds % 60))

    def Hide(self):
        self.EndDrag()
        ui.Window.Hide(self)

    def Destroy(self):
        self.Hide()
        self.phase = 0
        passagetrialstate.SetPhase(0)
        self.plate = None
        self.frame = self.vein = None
        self.title = self.progress = self.clock = None
