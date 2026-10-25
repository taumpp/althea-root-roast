"""Prepared parchment announcements, independent of the album window."""
import app
import ui
import uiScriptLocale
import wndMgr
import noticeplacement

ASSET_ROOT = "d:/ymir work/ui/pet/album_c/"
WIDTH, HEIGHT = 460, 153
HOLD, FADE = 4.2, .25
WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)


class PetAlbumNoticeWindow(ui.Window):
    def __init__(self):
        # Announcements stay above the world and below open UI and tooltips.
        ui.Window.__init__(self, "GAME")
        self.Initialize()
        self.AddFlag("not_pick")
        self.SetSize(WIDTH, HEIGHT)
        self.frame = self.Image(0, 0, "notice-frame.png")
        # Authored inset centre is (69, 65), not the frame's bounding centre.
        # Every notice sprite is optically cropped into the same 68px canvas.
        self.portrait = self.Image(35, 31, "notice-symbol.png")
        self.title = self.Text(285, 45, 13, True, 0xff702526)
        self.name = self.Text(285, 73, 18, True, 0xff35241b)
        self.body = self.Text(285, 98, 11, False, 0xff63462f)
        self.Hide()

    def Initialize(self):
        self.owned = []
        self.queue = []
        self.active = None
        self.started = 0.0
        self.suspended = False
        self.pausedAt = None
        self.protectedRects = lambda: []
        self.blockedAt = None
        self.frame = self.portrait = self.title = self.name = self.body = None

    def __del__(self):
        ui.Window.__del__(self)

    def Image(self, x, y, filename):
        image = ui.ExpandedImageBox()
        image.SetParent(self)
        image.AddFlag("not_pick")
        image.SetPosition(x, y)
        image.LoadImage(ASSET_ROOT + filename)
        image.Show()
        self.owned.append(image)
        return image

    def Text(self, x, baseline, size, bold, color):
        line = ui.TextLine()
        line.SetParent(self)
        line.AddFlag("not_pick")
        line.SetFontName("Tahoma:%d%sa" % (size, "b" if bold else ""))
        line.SetPosition(x, baseline + 2)
        line.SetVerticalAlignBottom()
        line.SetHorizontalAlignCenter()
        line.SetPackedFontColor(color if color < 0x80000000 else color-0x100000000)
        line.Show()
        self.owned.append(line)
        return line

    def Add(self, notice):
        if notice.get("kind") not in ("clue", "capture", "level"):
            return
        self.queue.append(dict(notice))
        if self.active is None and not self.suspended:
            self.Next()

    def Next(self):
        if not self.queue:
            self.active = None
            self.Hide()
            return
        self.blockedAt = None
        self.active = self.queue.pop(0)
        kind = self.active["kind"].upper()
        filename = "notice-symbol.png" if kind == "CLUE" else "notice-" + self.active["id"] + "_66.png"
        self.portrait.LoadImage(ASSET_ROOT + filename)
        self.title.SetText(getattr(uiScriptLocale, "PET_ALBUM_NOTICE_" + kind + "_TITLE"))
        self.name.SetText(self.active["name"])
        body = getattr(uiScriptLocale, "PET_ALBUM_NOTICE_" + kind + "_BODY")
        self.body.SetText(body % self.active["level"] if kind == "LEVEL" else body)
        self.started = app.GetTime()
        self.OnUpdate()
        self.SetTop()
        if self.blockedAt is None:
            self.Show()

    def OnUpdate(self):
        if self.suspended or self.active is None:
            return
        now = app.GetTime()
        position = noticeplacement.place((WIDTH, HEIGHT),
                    ((wndMgr.GetScreenWidth() - WIDTH) // 2, 72),
                    (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()), self.protectedRects())
        if position is None:
            if self.blockedAt is None:
                self.blockedAt = now
            self.Hide()
            return
        if self.blockedAt is not None:
            self.started += max(0.0, now - self.blockedAt)
            self.blockedAt = None
        elapsed = max(0.0, now - self.started)
        if elapsed >= HOLD:
            self.Next()
            return
        self.SetPosition(*position)
        self.Show()
        alpha = min(1.0, elapsed / FADE, (HOLD - elapsed) / FADE)
        for widget in (self.frame, self.portrait):
            widget.SetAlpha(alpha)
        for line, color in ((self.title, 0x702526), (self.name, 0x35241b), (self.body, 0x63462f)):
            packed = (int(alpha * 255) << 24) | color
            line.SetPackedFontColor(packed if packed < 0x80000000 else packed-0x100000000)

    def Pending(self):
        # Presentation only: replay an interrupted card, never album progress.
        result = []
        until = self.pausedAt if self.pausedAt is not None else app.GetTime()
        if self.blockedAt is not None:
            until = min(until, self.blockedAt)
        if self.active is not None and max(0.0, until - self.started) < HOLD:
            result.append(dict(self.active))
        result.extend(dict(notice) for notice in self.queue)
        return result

    def Suspend(self):
        if not self.suspended:
            if self.blockedAt is not None:
                self.started += max(0.0, app.GetTime() - self.blockedAt)
                self.blockedAt = None
            self.suspended = True
            self.pausedAt = app.GetTime() if self.active is not None else None
        self.Hide()

    def Resume(self):
        if not self.suspended:
            return
        self.suspended = False
        if self.pausedAt is not None:
            self.started += max(0.0, app.GetTime() - self.pausedAt)
        self.pausedAt = None
        if self.active is not None:
            self.OnUpdate()
            if self.active is not None and self.blockedAt is None:
                self.Show()
        else:
            self.Next()

    def Close(self):
        self.blockedAt = None
        self.Hide()
        self.suspended = False
        self.pausedAt = None
        self.queue = []
        self.active = None

    @WindowDestroy
    def Destroy(self):
        self.Close()
        for widget in self.owned:
            widget.Hide()
        self.Initialize()
