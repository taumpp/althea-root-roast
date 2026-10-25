"""Resizable HUD for server-owned mission progress."""
import weakref
import nonplayer
import ui
import wndMgr
import uiToolTip
import fontconfig
import missionbookmodel as model
from missionbooklocale import Text
from uimissionbookwidgets import WindowDestroy, line, fitted, book_image, GOLD, DIM
from uicountdownhud import _HitArea, _SetControl, _Image, Text as CountdownText, R1ShowHint, R1HideHint
from uicrimsonember import SettingsScrollBar


class MissionBookTracker(ui.Window):
    def __init__(self, owner):
        ui.Window.__init__(self)
        self.Initialize()
        self.owner = weakref.proxy(owner)
        self.AddFlag("float")
        self.SetWindowName("MissionBookTracker")
        self.tooltip = uiToolTip.ToolTip()
        self.board = ui.Board()
        self.board.SetParent(self)
        self.board.SetPosition(4, 0)
        self.board.AddFlag("not_pick")
        self.board.Show()
        self.titleBar = ui.TitleBar()
        self.titleBar.SetParent(self)
        self.titleBar.MakeTitleBar(260, "red")
        self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
        self.titleBar.Show()
        self.title = line(self.titleBar, 130, 3, Text("TRACKER"), align="center", role=fontconfig.ROLE_WINDOW_TITLE)
        self.titleGrip = _HitArea(self, "move", CountdownText("MOVE"), True)
        self.titleGrip.SetPosition(0, 0)
        self.lockButton = ui.Button()
        self.lockButton.SetParent(self.titleBar)
        self.lockButton.SetEvent(ui.__mem_func__(self.ToggleLock))
        self.lockButton.Show()
        self.collapseButton = ui.Button()
        self.collapseButton.SetParent(self.titleBar)
        self.collapseButton.SetEvent(ui.__mem_func__(self.ToggleCollapse))
        self.collapseButton.Show()
        self.bookHit = _HitArea(self, "open", Text("TITLE"))
        self.bookHit.SetPosition(14, 33)
        self.bookHit.SetSize(32, 32)
        self.viewport = ui.Window()
        self.viewport.SetParent(self)
        self.viewport.SetPosition(54, 33)
        self.viewport.EnableScissorRect()
        self.viewport.Show()
        self.scroll = SettingsScrollBar()
        self.scroll.SetParent(self)
        self.scroll.SetScrollEvent(ui.__mem_func__(self.Refresh))
        self.resizeGrip = _HitArea(self, "resize", CountdownText("RESIZE"), True)
        self.resizeGrip.SetSize(25, 25)
        self.resizeImage = _Image(self.resizeGrip,
            "d:/ymir work/ui/game/crimson_ember/countdown_hud/resize_left_normal.png", 4, 6)
        self.children = [self.board, self.titleBar, self.title, self.titleGrip,
            self.lockButton, self.collapseButton, self.bookHit, self.viewport,
            self.scroll, self.resizeGrip, self.resizeImage]
        self.Layout()
        self.ApplyR1Look()
        self.Hide()

    def ApplyR1Look(self):
        """R1 look (root/uihudpanelr1.py, shared with Odpočty) unless Settings -> "Starý vzhled" chose the original
        one; a build failure keeps the original look (traced, not tried again in this session)."""
        self.r1 = None
        try:
            import uihudpanelr1
            self.r1 = uihudpanelr1.Build(self, uihudpanelr1.TrackerSkin, Text("TRACKER"),
                                         lambda me=weakref.proxy(self): me.owner.settings)
        except Exception:
            self.r1 = None

    def SyncR1(self):
        if self.r1:
            self.r1.SyncSafe()

    def Initialize(self):
        self.owner = None
        self.tooltip = self.board = self.titleBar = self.title = None
        self.titleGrip = self.lockButton = self.collapseButton = None
        self.bookHit = self.book = self.viewport = self.scroll = None
        self.resizeGrip = self.resizeImage = None
        self.children = []
        self.rows = []
        self.dragState = None
        self.growLeft = False
        self.lastScreen = None
        self.bookVnum = None
        self.layoutBusy = False
        self.r1 = None
        self.resizeState = None

    def __del__(self):
        ui.Window.__del__(self)

    def Screen(self):
        width, height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        taskbar = getattr(self.owner.interface, "wndTaskBar", None)
        if taskbar:
            unused, top = taskbar.GetGlobalPosition()
            if 138 < top < height:
                height = top
        return width, height

    def Layout(self):
        s = self.owner.settings
        sw, sh = self.Screen()
        x, y, w, h = model.clamp_geometry(s["x"], s["y"], s["width"], s["height"], sw, sh)
        if s["collapsed"]:
            y = max(8, min(s["y"], sh - 23 - 8))
        s.update(x=x, y=y, width=w, height=h)
        self.lastScreen = (sw, sh)
        self.SetPosition(x, y)
        self.SetSize(w, 23 if s["collapsed"] else h)
        self.board.SetSize(w - 8, h)
        self.titleBar.SetWidth(w)
        self.title.SetPosition(w // 2, 3)
        fitted(self.title, Text("TRACKER"), max(1, w - 146))
        self.titleGrip.SetSize(max(1, w - 71), 23)
        self.lockButton.SetPosition(w - 71, 0)
        self.collapseButton.SetPosition(w - 48, 0)
        _SetControl(self.lockButton, "lock", s["locked"])
        _SetControl(self.collapseButton, "up" if s["collapsed"] else "down")
        self.lockButton.SetToolTipText(CountdownText("UNLOCK" if s["locked"] else "LOCK"))
        self.collapseButton.SetToolTipText(Text("TRACKER_EXPAND" if s["collapsed"] else "TRACKER_COLLAPSE"))
        self.viewport.SetSize(max(1, w - 81), max(1, h - 62))
        self.layoutBusy = True
        self.scroll.SetPosition(w - 23, 33)
        self.scroll.SetScrollBarSize(max(20, h - 62))
        self.layoutBusy = False
        self.growLeft = self.dragState[4] if self.dragState else x + w // 2 >= sw // 2
        self.resizeGrip.SetPosition(6 if self.growLeft else w - 31, h - 28)
        self.UpdateResizeVisual()
        for widget in (self.board, self.viewport, self.bookHit, self.resizeGrip):
            widget.Hide() if s["collapsed"] else widget.Show()
        self.Refresh()

    def Refresh(self):
        if self.layoutBusy or not self.owner:
            return
        targets = self.owner.state.targets()
        s = self.owner.settings
        visible = max(1, self.viewport.GetHeight() // model.ROW_HEIGHT)
        overflow = max(0, len(targets) - visible)
        self.layoutBusy = True
        self.scroll.SetMiddleBarSize(max(0.1, min(1.0, float(visible) / max(1, len(targets)))))
        if overflow:
            self.scroll.SetScrollStep(1.0 / overflow)       # one target per wheel notch (was 40 % of the list)
        else:
            self.scroll.SetPos(0)
        self.layoutBusy = False
        first = int(round(overflow * self.scroll.GetPos()))
        self.scroll.Show() if overflow and not s["collapsed"] else self.scroll.Hide()
        for name, count in self.rows:
            name.Hide()
            count.Hide()
        while len(self.rows) < min(visible, len(targets)):
            self.rows.append((line(self.viewport, 0, 0), line(self.viewport, 0, 0, color=GOLD, align="right")))
        for index, (row, (vnum, required)) in enumerate(zip(self.rows, targets[first:first + visible])):
            name, count = row
            name.SetPosition(0, 3 + index * model.ROW_HEIGHT)
            count.SetPosition(self.viewport.GetWidth(), 3 + index * model.ROW_HEIGHT)
            count.SetText("%d / %d" % (self.owner.state.progress[first + index], required))
            kind = model.objectives(*self.owner.state.active)[first + index][0]
            target_name = Text("MINE_ALTHEIT") if kind == 2 else Text("FISH_POND") if kind == 3 else nonplayer.GetMonsterName(vnum)
            fitted(name, target_name, self.viewport.GetWidth() - count.GetTextSize()[0] - 8)
            name.Show()
            count.Show()
        active = self.owner.state.active
        if active and active[0] != self.bookVnum:
            if self.book:
                self.book.Hide()
            self.book = book_image(self.bookHit, active[0], 0, 0)
            self.bookVnum = active[0]
        self.SyncR1()

    def Open(self, force=False):
        if not self.owner.state.active or (not force and not self.owner.settings["auto_track"]) or self.owner.suspended:
            return
        self.Layout()
        self.Show()
        self.SetTop()

    def Close(self):
        self.EndDrag()
        self.HideHint()
        self.Hide()
        # Temporary hide is deliberately not the persistent auto-track flag.

    def ToggleLock(self):
        self.EndDrag()
        self.owner.settings["locked"] = not self.owner.settings["locked"]
        self.Layout()
        self.owner.Save()

    def ToggleCollapse(self):
        self.EndDrag()
        self.owner.settings["collapsed"] = not self.owner.settings["collapsed"]
        self.Layout()
        self.owner.Save()

    def BeginDrag(self, kind):
        if self.owner.settings["locked"]:
            return
        self.HideHint()
        self.SetTop()
        mx, my = wndMgr.GetMousePosition()
        self.dragState = (kind, mx, my, dict(self.owner.settings), self.growLeft)
        self.UpdateResizeVisual()

    def Drag(self):
        if not self.dragState:
            return
        kind, mx, my, initial, left = self.dragState
        px, py = wndMgr.GetMousePosition()
        dx, dy = px - mx, py - my
        x, y, w, h = (initial[k] for k in ("x", "y", "width", "height"))
        sw, sh = self.Screen()
        if kind == "move":
            x, y = x + dx, y + dy
        else:
            right = x + w
            w = max(model.MIN_WIDTH, min(w - dx if left else w + dx, right - 8 if left else sw - x - 8))
            if left:
                x = right - w
            h = max(model.MIN_HEIGHT, min(h + dy, sh - y - 8))
        self.owner.settings.update(x=int(x), y=int(y), width=int(w), height=int(h))
        self.Layout()

    def EndDrag(self):
        if self.dragState:
            self.dragState = None
            self.Layout()
            self.owner.Save()

    def UpdateResizeVisual(self):
        state = "disabled" if self.owner.settings["locked"] else (
            "pressed" if self.dragState else "hover" if self.resizeGrip.hovered else "normal")
        path = "d:/ymir work/ui/game/crimson_ember/countdown_hud/resize_%s_%s.png"
        self.resizeState = ("left" if self.growLeft else "right", state)
        self.resizeImage.LoadImage(path % self.resizeState)
        if self.r1:
            self.r1.SyncResizeSafe()

    def Activate(self, action):
        self.HideHint()
        if action == "open":
            self.owner.Open()

    def ShowHint(self, text, widget=None):
        if self.dragState:
            return
        if R1ShowHint(self, text, widget):
            return
        self.tooltip.ClearToolTip()
        self.tooltip.SetThinBoardSize(uiToolTip.ToolTip.TOOL_TIP_WIDTH)
        self.tooltip.AutoAppendTextLine(text)
        self.tooltip.AlignHorizonalCenter()
        self.tooltip.ShowToolTip()

    def HideHint(self):
        R1HideHint(self)
        if self.tooltip:
            self.tooltip.HideToolTip()

    def OnMouseWheel(self, delta):
        if not self.scroll.IsShow() or not delta:
            return False
        self.scroll.OnUp() if delta > 0 else self.scroll.OnDown()
        return True

    def OnUpdate(self):
        if self.Screen() != self.lastScreen:
            self.Layout()

    @WindowDestroy
    def Destroy(self):
        if not self.owner:
            return
        self.Close()
        self.owner.Save()
        if self.r1:
            self.r1.Destroy()
            self.r1 = None
        self.titleBar.SetCloseEvent(None)
        self.lockButton.SetEvent(None)
        self.collapseButton.SetEvent(None)
        self.scroll.Destroy()
        for widget in self.children:
            widget.Hide()
        self.Initialize()
