# -*- coding: utf-8 -*-
"""Compact A3 countdown HUD; server state stays owned by existing systems."""
import weakref

import app
import item
import fontconfig
import localeInfo
import player
import ui
import uiToolTip
import wndMgr
import countdownmodel as model


ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/countdown_hud/"
PORTRAIT_ROOT = ASSET_ROOT + "portrait/"
NAME_X = 46
TEXT_TOP = 9
INK = (234 / 255.0, 226 / 255.0, 211 / 255.0)
BIO = (148 / 255.0, 194 / 255.0, 172 / 255.0)
COPPER = (214 / 255.0, 171 / 255.0, 124 / 255.0)
READY = (234 / 255.0, 211 / 255.0, 151 / 255.0)
DIM = (170 / 255.0, 160 / 255.0, 147 / 255.0)
_reminderCharacter = ""
_pendingReminders = {}


def Text(key):
    return getattr(localeInfo, "COUNTDOWN_" + key)


def ResetReminderState():
    global _reminderCharacter
    _reminderCharacter = ""
    _pendingReminders.clear()


def _SetControl(button, family, selected=False):
    for setter, state in ((button.SetUpVisual, "selected" if selected else "normal"),
                          (button.SetOverVisual, "selected" if selected else "hover"),
                          (button.SetDownVisual, "pressed"),
                          (button.SetDisableVisual, "disabled")):
        setter(ASSET_ROOT + family + "_" + state + ".png")


def CreateLauncher(parent, callback):
    button = ui.Button()
    button.SetParent(parent)
    _SetControl(button, "clock")
    button.SetPosition(parent.GetWidth() - 49, 0)
    button.SetEvent(callback)
    button.SetToolTipText(Text("TITLE"))
    button.Show()
    return button


def _Image(parent, path, x=0, y=0):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag("not_pick")
    image.LoadImage(path)
    image.SetPosition(x, y)
    image.Show()
    return image


def _Line(parent, x=0, y=0, role=fontconfig.ROLE_BODY, color=INK, right=False):
    line = ui.TextLine()
    line.SetParent(parent)
    line.AddFlag("not_pick")
    line.SetFontName(fontconfig.FontForRole(role))
    line.SetPosition(x, y)
    if right:
        line.SetHorizontalAlignRight()
    line.SetFontColor(*color)
    line.Show()
    return line


def _SetText(line, text, color=INK):
    line.SetText(str(text))
    line.SetFontColor(*color)


def _Fit(line, text, width):
    def measure(value):
        line.SetText(value)
        return line.GetTextSize()[0]
    fitted = model.fit_text(str(text), max(0, int(width)), measure)
    line.SetText(fitted)


def _SetRowText(name, timer, label, value, width, color):
    # Same font roles, baseline and measured column gap in both categories.
    _SetText(timer, value, color)
    available = max(0, width - NAME_X - 32 - 8)
    timerWidth = min(timer.GetTextSize()[0], available)
    _Fit(timer, value, timerWidth)
    timer.SetPosition(width, TEXT_TOP)
    _SetText(name, label)
    _Fit(name, label, max(0, width - NAME_X - timerWidth - 8))


def _Bar(parent, color):
    bar = ui.Bar()
    bar.SetParent(parent)
    bar.AddFlag("not_pick")
    # Native bar uses unsigned color, unlike the signed packed-font bridge.
    bar.SetColor(color)
    bar.Show()
    return bar


class _HitArea(ui.Window):
    def __init__(self, owner, action, tooltip="", drag=False):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.action = action
        self.tooltipText = tooltip
        self.SetParent(owner)
        if drag:
            self.AddFlag("dragable")
        self.drag = drag
        self.hovered = False
        self.Show()

    def OnMouseLeftButtonDown(self):
        if self.drag:
            self.owner.BeginDrag(self.action)
        return True

    def OnMouseDrag(self, x, y):
        if self.drag:
            self.owner.Drag()

    def OnMouseLeftButtonUp(self):
        if self.drag:
            self.owner.EndDrag()
        else:
            self.owner.Activate(self.action)
        return True

    def OnMouseOverIn(self):
        self.hovered = True
        if self.action == "resize":
            self.owner.UpdateResizeVisual()
        if self.tooltipText:
            self.owner.ShowHint(self.tooltipText)

    def OnMouseOverOut(self):
        self.hovered = False
        if self.action == "resize":
            self.owner.UpdateResizeVisual()
        self.owner.HideHint()

    def OnMouseWheel(self, delta):
        return self.owner.OnMouseWheel(delta)


class _Row(_HitArea):
    def __init__(self, owner):
        _HitArea.__init__(self, owner, ("dungeon", 0))
        self.picture = ui.ImageBox()
        self.picture.SetParent(self)
        self.picture.AddFlag("not_pick")
        self.name = _Line(self, NAME_X, TEXT_TOP)
        self.time = _Line(self, 0, TEXT_TOP, fontconfig.ROLE_CONTROL, right=True)
        self.separator = _Bar(self, 0xff29231e)
        self.progressBack = _Bar(self, 0xff29231e)
        self.progress = _Bar(self, 0xffd6ab7c)
        self.readyMark = _Bar(self, 0xffead397)
        self.children = [self.picture, self.name, self.time, self.separator,
                         self.progressBack, self.progress, self.readyMark]
        self.iconPath = None
        self.signature = None
        self.Hide()

    def SetRow(self, vnum, data, status, width):
        signature = (vnum, data["name"], status["state"], status["remaining"],
                     status["progress"], width)
        if signature == self.signature:
            self.Show()
            return
        self.signature = signature
        self.action = ("dungeon", vnum)
        self.SetSize(width, model.ROW_HEIGHT)
        path = PORTRAIT_ROOT + "%d_41x32.png" % vnum
        if path != self.iconPath:
            self.iconPath = path
            try:
                self.picture.LoadImage(path)
                self.picture.SetPosition(0, 2)
                self.picture.Show()
            except (RuntimeError, OSError):
                self.picture.Hide()
        state = status["state"]
        if state == "cooldown":
            value, color = model.format_time(status["remaining"]), COPPER
        elif state == "ready":
            value, color = Text("READY"), READY
        elif state == "locked":
            value, color = Text("LEVEL") % data["minLevel"], DIM
        else:
            value, color = "—", DIM
        _SetRowText(self.name, self.time, data["name"], value, width, color)
        if state == "locked":
            self.name.SetFontColor(*DIM)
        self.separator.SetPosition(0, model.ROW_HEIGHT - 1)
        self.separator.SetSize(width, 1)
        self.readyMark.SetPosition(-4, TEXT_TOP)
        self.readyMark.SetSize(2, 15)
        self.readyMark.Show() if state == "ready" else self.readyMark.Hide()
        for bar in (self.progressBack, self.progress):
            bar.SetPosition(width - 49, model.ROW_HEIGHT - 4)
        self.progressBack.SetSize(49, 3)
        fill = int(round(49 * status["progress"]))
        self.progress.SetSize(max(1, fill), 3)
        self.progressBack.Show() if state == "cooldown" else self.progressBack.Hide()
        self.progress.Show() if state == "cooldown" and fill else self.progress.Hide()
        detail = Text("WAITING") if state == "unknown" else value
        if state == "ready":
            detail = Text("READY_HINT")
        self.tooltipText = "%s\n%s" % (data["name"], detail)
        self.Show()


class CountdownWindow(ui.Window):
    def __init__(self, interface):
        ui.Window.__init__(self)
        self.interface = weakref.proxy(interface)
        self.AddFlag("float")
        self.SetWindowName("CountdownHUD")
        self.character = str(player.GetName() or "")
        self.settings = model.load_settings(self.character)
        self.children = []
        self.rows = []
        self.dragState = None
        self.nextTick = 0.0
        self.lastScreen = None
        self.tracked = []
        self.visibleRows = 0
        self.bioTracked = False
        self.selectionSignature = None
        self.listTop = model.LIST_TOP
        self.suspended = True
        self.destroyed = False
        self.bioIconVnum = None
        self.tooltip = uiToolTip.ToolTip()
        self._Build()
        self._RestoreGeometry()
        self.Hide()

    def _Own(self, child):
        self.children.append(child)
        return child

    def _Build(self):
        self.board = self._Own(ui.Board())
        self.board.SetParent(self)
        self.board.SetPosition(4, 0)
        self.board.AddFlag("not_pick")
        self.board.Show()
        self.titleBar = self._Own(ui.TitleBar())
        self.titleBar.SetParent(self)
        self.titleBar.MakeTitleBar(model.DEFAULT_WIDTH, "red")
        self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
        self.titleBar.Show()
        self.title = self._Own(_Line(self.titleBar, 111, 3, fontconfig.ROLE_WINDOW_TITLE))
        self.title.SetHorizontalAlignCenter()
        self.titleGrip = self._Own(_HitArea(self, "move", Text("MOVE"), True))
        self.titleGrip.SetPosition(0, 0)
        self._Own(_Image(self.titleGrip, ASSET_ROOT + "grip_normal.png", 10, 5))
        self.lockButton = self._Own(ui.Button())
        self.lockButton.SetParent(self.titleBar)
        self.lockButton.SetEvent(ui.__mem_func__(self.ToggleLock))
        self.lockButton.Show()
        self.collapseButton = self._Own(ui.Button())
        self.collapseButton.SetParent(self.titleBar)
        self.collapseButton.SetEvent(ui.__mem_func__(self.ToggleCollapse))
        self.collapseButton.Show()
        self.bioBand = self._Own(_HitArea(self, "biolog", Text("OPEN_BIO")))
        self.bioBand.SetPosition(13, 28)
        self.bioSurface = self._Own(_Image(self.bioBand, ASSET_ROOT + "band_bio.png"))
        self._Own(_Image(self.bioBand, ASSET_ROOT + "bio_normal.png", 3, 2))
        self.bioLabel = self._Own(_Line(self.bioBand, 23, 2, fontconfig.ROLE_SECTION, color=BIO))
        _SetText(self.bioLabel, Text("BIOLOG"), BIO)
        self.bioHit = self._Own(_HitArea(self, "biolog", Text("OPEN_BIO")))
        self.bioHit.SetPosition(14, 49)
        self.bioPicture = self._Own(ui.ImageBox())
        self.bioPicture.SetParent(self.bioHit)
        self.bioPicture.AddFlag("not_pick")
        self.bioName = self._Own(_Line(self.bioHit, NAME_X, TEXT_TOP))
        self.bioTime = self._Own(_Line(self.bioHit, 0, TEXT_TOP, fontconfig.ROLE_CONTROL, BIO, True))
        self.dungeonBand = self._Own(_HitArea(self, "dungeons", Text("OPEN_DUNGEONS")))
        self.dungeonBand.SetPosition(13, 79)
        self.dungeonSurface = self._Own(_Image(self.dungeonBand, ASSET_ROOT + "band_dungeon.png"))
        self._Own(_Image(self.dungeonBand, ASSET_ROOT + "dungeon_normal.png", 3, 2))
        self.dungeonLabel = self._Own(_Line(self.dungeonBand, 23, 2, fontconfig.ROLE_SECTION, color=COPPER))
        _SetText(self.dungeonLabel, Text("DUNGEONS"), COPPER)
        self.scroll = self._Own(_HitArea(self, "scroll", "", True))
        self.scrollBack = self._Own(_Bar(self.scroll, 0xff29231e))
        self.scrollThumb = self._Own(_Bar(self.scroll, 0xff937b59))
        self.resizeGrip = self._Own(_HitArea(self, "resize", Text("RESIZE"), True))
        self.resizeGrip.SetSize(25, 25)
        self.resizeImage = self._Own(_Image(self.resizeGrip, ASSET_ROOT + "resize_left_normal.png", 4, 6))
        self.notificationSettings = None
        if hasattr(self.interface, "OpenSystemNotificationSettings"):
            from uisystemnotifications import SettingsLink
            self.notificationSettings = self._Own(SettingsLink(
                self, ui.__mem_func__(self.interface.OpenSystemNotificationSettings), False))

    def _Screen(self):
        width, height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        taskbar = getattr(self.interface, "wndTaskBar", None)
        if taskbar:
            unused, top = taskbar.GetGlobalPosition()
            if 216 < top < height:
                height = top
        return int(width), int(height)

    def _RestoreGeometry(self):
        sw, sh = self._Screen()
        s = self.settings
        x = sw - s["width"] - 18 if s["x"] is None else s["x"]
        y = min(326, sh - s["height"] - 8) if s["y"] is None else s["y"]
        requestedY = y
        x, y, w, h = model.clamp_geometry(x, y, s["width"], s["height"], sw, sh)
        if s["collapsed"]:
            y = max(8, min(requestedY, sh - 23 - 8))
        s.update(x=x, y=y, width=w, height=h)
        self.SetPosition(x, y)
        self.lastScreen = (sw, sh)
        self._Layout()

    def _Layout(self):
        s = self.settings
        w, h = s["width"], s["height"]
        self.SetSize(w, 23 if s["collapsed"] else h)
        self.board.SetSize(w - 8, h)
        self.titleBar.SetWidth(w)
        self.title.SetPosition(w // 2, 3)
        self.titleGrip.SetSize(w - 71, 23)
        self.lockButton.SetPosition(w - 71, 0)
        self.collapseButton.SetPosition(w - 48, 0)
        _SetControl(self.lockButton, "lock", s["locked"])
        _SetControl(self.collapseButton, "up" if s["collapsed"] else "down")
        self.lockButton.SetToolTipText(Text("UNLOCK" if s["locked"] else "LOCK"))
        self.collapseButton.SetToolTipText(Text("EXPAND" if s["collapsed"] else "COLLAPSE"))
        self.bioBand.SetSize(w - 26, 19)
        self.dungeonBand.SetSize(w - 26, 19)
        for surface in (self.bioSurface, self.dungeonSurface):
            surface.SetScale(float(w - 26) / 196.0, 1.0)
        self.bioHit.SetSize(w - 31, model.ROW_HEIGHT)
        self.growLeft = s["x"] + w // 2 >= self._Screen()[0] // 2
        if self.dragState is not None and self.dragState[0] == "resize":
            self.growLeft = self.dragState[4]
        self.resizeGrip.SetPosition(6 if self.growLeft else w - 31, h - 28)
        if self.notificationSettings:
            self.notificationSettings.SetPosition(w - 33 if self.growLeft else 13, h - 26)
            self.notificationSettings.Hide() if s["collapsed"] else self.notificationSettings.Show()
        self.UpdateResizeVisual()
        for child in (self.board, self.resizeGrip):
            child.Hide() if s["collapsed"] else child.Show()
        self._Refresh()

    def UpdateResizeVisual(self):
        if self.settings["locked"]:
            state = "disabled"
        elif self.dragState is not None and self.dragState[0] == "resize":
            state = "pressed"
        else:
            state = "hover" if self.resizeGrip.hovered else "normal"
        self.resizeImage.LoadImage(ASSET_ROOT + "resize_" +
                                  ("left" if self.growLeft else "right") + "_" + state + ".png")

    def _Catalog(self):
        if not getattr(app, "ENABLE_DUNGEON_INFO", False):
            return {}
        import uiDungeonTrack
        return uiDungeonTrack.dungeonData

    def _Refresh(self):
        s = self.settings
        w, h = s["width"], s["height"]
        now = app.GetGlobalTimeStamp()
        level = player.GetStatus(player.LEVEL)
        known = getattr(self.interface, "countdownKnownDungeons", set())
        self.tracked = model.watched_dungeons(self._Catalog())
        if not self._HUDEnabled("dungeon"):
            self.tracked = []
        states = [model.dungeon_status(data, now, level, vnum in known) for vnum, data in self.tracked]
        self.bioTracked = self._BiologTracked()
        selection = (self.bioTracked, tuple(vnum for vnum, data in self.tracked))
        if selection != self.selectionSignature:
            self.HideHint()
            self.selectionSignature = selection
        expanded = not s["collapsed"]
        for child in (self.bioBand, self.bioHit):
            child.Show() if self.bioTracked and expanded else child.Hide()
        self.dungeonBand.Show() if self.tracked and expanded else self.dungeonBand.Hide()
        self.dungeonBand.SetPosition(13, 87 if self.bioTracked else 28)
        self.listTop = model.LIST_TOP if self.bioTracked else 49
        _SetText(self.title, Text("TITLE"))
        _Fit(self.title, self.title.GetText(), max(20, w - 146))
        self.visibleRows = model.visible_count(h, len(self.tracked), self.listTop)
        s["scroll"] = min(s["scroll"], max(0, len(self.tracked) - self.visibleRows))
        while len(self.rows) < self.visibleRows:
            self.rows.append(_Row(self))
        for index, row in enumerate(self.rows):
            if index < self.visibleRows and not s["collapsed"]:
                itemIndex = s["scroll"] + index
                vnum, data = self.tracked[itemIndex]
                row.SetPosition(14, self.listTop + index * model.ROW_HEIGHT)
                row.SetRow(vnum, data, states[itemIndex], w - 31)
            else:
                row.Hide()
        total = len(self.tracked)
        if total > self.visibleRows > 0 and not s["collapsed"]:
            length = self.visibleRows * model.ROW_HEIGHT
            self.scroll.SetPosition(w - 17, self.listTop)
            self.scroll.SetSize(11, length)
            self.scrollBack.SetPosition(4, 0)
            self.scrollBack.SetSize(3, length)
            thumb = max(12, int(length * float(self.visibleRows) / total))
            offset = int((length - thumb) * float(s["scroll"]) / (total - self.visibleRows))
            self.scrollThumb.SetPosition(4, offset)
            self.scrollThumb.SetSize(3, thumb)
            self.scroll.Show()
        else:
            self.scroll.Hide()
        if self.bioTracked:
            self._RefreshBiolog(now)

    def _HUDEnabled(self, category):
        callback = getattr(self.interface, "IsCountdownCategoryEnabled", None)
        return callback(category) if callback else True

    def _BiologTracked(self):
        if not self._HUDEnabled("biolog"):
            return False
        bio = getattr(self.interface, "wndBio", None)
        if bio and hasattr(bio, "GetTrackedResearches"):
            return bool(bio.GetTrackedResearches())
        checkbox = getattr(bio, "checkBoxCall", None)
        return bool(checkbox and checkbox.IsDown() and
                    getattr(bio, "dataKnown", False) and bio.bioLevel > 0)

    def RefreshSelection(self, reveal=False):
        self._Refresh()
        hasSelection = self.bioTracked or bool(self.tracked)
        if reveal and hasSelection:
            self.settings["visible"] = True
            self.Save()
        if hasSelection and self.settings["visible"] and not self.suspended:
            self.Show()
            if reveal:
                self.SetTop()
        else:
            self.HideHint()
            self.Hide()

    def _RefreshBiolog(self, now):
        bio = getattr(self.interface, "wndBio", None)
        name, value, vnum = Text("NO_BIO"), "—", 0
        tracked = bio.GetTrackedResearches() if bio and hasattr(bio, "GetTrackedResearches") else []
        detailLines = []
        if tracked:
            import biologresearchmodel as researchModel
            tracked.sort(key=lambda row: (max(0, row["due"] - now), row["index"]))
            for row in tracked:
                state = researchModel.phase(row)
                remaining = max(0, row["due"] - now)
                rowValue = Text("STONE") if state == "stone" else Text("REWARD") if state == "gift" else model.format_time(remaining) if remaining else Text("READY")
                detailLines.append("%s: %s" % (item.GetItemNameByVnum(row["vnum"]), rowValue))
            row = tracked[0]
            vnum = row["stone"] if researchModel.phase(row) == "stone" else row["vnum"]
            name = item.GetItemNameByVnum(row["vnum"])
            if len(tracked) > 1:
                name += " (+%d)" % (len(tracked) - 1)
            value = detailLines[0].split(": ", 1)[1]
        elif bio and not hasattr(bio, "GetTrackedResearches") and getattr(bio, "dataKnown", False) and 0 < bio.bioLevel:
            import uiBiolog
            data = uiBiolog.bio_data[bio.bioLevel]
            vnum = data[1]
            if bio.mode in ("stone", "gift"):
                vnum = data[5] or vnum
            name = item.GetItemNameByVnum(vnum)
            if player.GetStatus(player.LEVEL) < data[0]:
                value = Text("LEVEL") % data[0]
            elif bio.mode == "stone":
                value = Text("STONE")
            elif bio.mode == "gift":
                value = Text("REWARD")
            elif bio.mode == "mission":
                remaining = max(0, bio.bioTime - now)
                value = model.format_time(remaining) if remaining else Text("READY")
        _SetRowText(self.bioName, self.bioTime, name, value,
                    self.settings["width"] - 31, BIO)
        self.bioHit.tooltipText = "\n".join(detailLines) if detailLines else "%s\n%s" % (name, value)
        if vnum != self.bioIconVnum:
            self.bioIconVnum = vnum
            self.bioPicture.Hide()
            if vnum:
                try:
                    item.SelectItem(vnum)
                    self.bioPicture.LoadImage(item.GetIconImageFileName())
                    self.bioPicture.SetPosition(4, 2)
                    self.bioPicture.Show()
                except (RuntimeError, OSError):
                    pass

    def Tick(self):
        if self.destroyed or self.suspended:
            return
        now = app.GetTime()
        if now < self.nextTick:
            return
        self.nextTick = now + 0.25
        if self._Screen() != self.lastScreen:
            self._RestoreGeometry()
        self._TickReminders()
        self.RefreshSelection()

    def _TickReminders(self):
        global _reminderCharacter
        if _reminderCharacter != self.character:
            ResetReminderState()
            _reminderCharacter = self.character
        known = getattr(self.interface, "countdownKnownDungeons", set())
        watched = dict(model.watched_dungeons(self._Catalog()))
        for vnum in list(_pendingReminders):
            if vnum not in watched:
                del _pendingReminders[vnum]
        now = app.GetGlobalTimeStamp()
        level = player.GetStatus(player.LEVEL)
        for vnum, data in watched.items():
            status = model.dungeon_status(data, now, level, vnum in known)
            if status["state"] == "cooldown":
                _pendingReminders[vnum] = data["server_cooldown"]
            elif status["state"] == "ready" and vnum in _pendingReminders:
                # One silent edge; Biolog's existing notifier remains its sole owner.
                if self.interface.PushDungeonCountdownNotification(Text("DUNGEONS"),
                        Text("DUNGEON_READY") % data["name"], vnum, _pendingReminders[vnum]):
                    del _pendingReminders[vnum]

    def Resume(self):
        self.suspended = False
        self.nextTick = 0
        self._RestoreGeometry()
        self.RefreshSelection()

    def Suspend(self):
        self.EndDrag()
        self.suspended = True
        self.HideHint()
        self.Hide()

    def Open(self):
        self._RestoreGeometry()
        self.RefreshSelection(reveal=True)

    def Close(self):
        self.EndDrag()
        self.settings["visible"] = False
        self.HideHint()
        self.Hide()
        self.Save()

    def Toggle(self):
        self.Close() if self.IsShow() else self.Open()

    def ToggleLock(self):
        self.EndDrag()
        self.settings["locked"] = not self.settings["locked"]
        self._Layout()
        self.Save()

    def ToggleCollapse(self):
        self.EndDrag()
        self.settings["collapsed"] = not self.settings["collapsed"]
        self.HideHint()
        self._RestoreGeometry()
        self.Save()

    def BeginDrag(self, kind):
        if kind != "scroll" and self.settings["locked"]:
            return
        self.HideHint()
        self.SetTop()
        mx, my = wndMgr.GetMousePosition()
        self.dragState = (kind, mx, my, dict(self.settings), self.growLeft)
        self.UpdateResizeVisual()
        if kind == "scroll":
            self.Drag()

    def Drag(self):
        if self.dragState is None:
            return
        kind, mx, my, initial, growLeft = self.dragState
        px, py = wndMgr.GetMousePosition()
        dx, dy = px - mx, py - my
        sw, sh = self._Screen()
        if kind == "scroll":
            unused, top = self.scroll.GetGlobalPosition()
            length = self.visibleRows * model.ROW_HEIGHT
            total = len(self.tracked)
            thumb = max(12, int(length * float(self.visibleRows) / max(1, total)))
            fraction = max(0.0, min(1.0, float(py - top - thumb // 2) / max(1, length - thumb)))
            self.settings["scroll"] = int(round(fraction * max(0, total - self.visibleRows)))
            self._Refresh()
            return
        x, y, w, h = (initial[k] for k in ("x", "y", "width", "height"))
        if kind == "move":
            visibleHeight = 23 if self.settings["collapsed"] else h
            x = max(8, min(x + dx, sw - w - 8))
            y = max(8, min(y + dy, sh - visibleHeight - 8))
        else:
            right = x + w
            if growLeft:
                w = max(model.MIN_WIDTH, min(w - dx, right - 8))
                x = right - w
            else:
                w = max(model.MIN_WIDTH, min(w + dx, sw - x - 8))
            h = max(model.MIN_HEIGHT, min(h + dy, sh - y - 8))
        self.settings.update(x=int(x), y=int(y), width=int(w), height=int(h))
        self.SetPosition(int(x), int(y))
        self._Layout()

    def EndDrag(self):
        if self.dragState is not None:
            wasResize = self.dragState[0] == "resize"
            self.dragState = None
            if wasResize:
                self._Layout()
            else:
                self.UpdateResizeVisual()
            self.Save()

    def OnMouseWheel(self, delta):
        if self.settings["collapsed"] or not self.tracked:
            return False
        offset = self.settings["scroll"] + (-1 if delta > 0 else 1)
        self.settings["scroll"] = max(0, min(offset, len(self.tracked) - self.visibleRows))
        self._Refresh()
        self.Save()
        self.HideHint()
        return True

    def Activate(self, action):
        self.HideHint()
        if action == "biolog":
            bio = getattr(self.interface, "wndBio", None)
            if bio:
                bio.Show()
                bio.SetTop()
        elif action == "dungeons" or isinstance(action, tuple):
            self.interface.OpenDungeonInfo()
            if isinstance(action, tuple):
                atlas = getattr(self.interface, "wndTeleportAtlas", None)
                page = getattr(atlas, "dungeonPage", None)
                if page:
                    page.OpenTrackedDungeon(action[1])

    def ShowHint(self, text):
        if self.dragState is not None:
            return
        self.tooltip.ClearToolTip()
        self.tooltip.SetThinBoardSize(uiToolTip.ToolTip.TOOL_TIP_WIDTH)
        for line in text.split("\n"):
            self.tooltip.AutoAppendTextLine(line)
        self.tooltip.AlignHorizonalCenter()
        self.tooltip.ShowToolTip()

    def HideHint(self):
        if self.tooltip:
            self.tooltip.HideToolTip()

    def Save(self):
        model.save_settings(self.character, self.settings)

    def Destroy(self):
        self.Suspend()
        self.Save()
        self.destroyed = True
        for row in self.rows:
            row.Hide()
            row.children = []
        self.rows = []
        self.titleBar.SetCloseEvent(None)
        self.lockButton.SetEvent(None)
        self.collapseButton.SetEvent(None)
        if self.notificationSettings:
            self.notificationSettings.Destroy()
            self.notificationSettings = None
        self.children = []
        self.tooltip = None
        self.interface = None
