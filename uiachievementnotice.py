# -*- coding: utf-8 -*-
"""Approved compact C: native R1 slices, separate live text and animated art."""
import app
import math
import ui
import wndMgr
import item
import localeInfo
import uiScriptLocale
import uir1
import uikit
import noticeplacement
import achievementnoticemodel as model

ROOT = "d:/ymir work/ui/game/achievement_notice/"
HOLD = 6.45
CARD_WIDTH, CARD_HEIGHT = 460, 88
ICON_SIZE, ICON_SCALE = 50, .57
WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)


def Progress(elapsed, begin, end):
    t = max(0.0, min(1.0, (elapsed - begin) / (end - begin)))
    return t * t * (3 - 2 * t)


def Packed(rgb, alpha):
    value = (int(max(0.0, min(1.0, alpha)) * 255) << 24) | rgb
    return value - 0x100000000 if value >= 0x80000000 else value


class AchievementNoticeWindow(ui.Window):
    def __init__(self):
        ui.Window.__init__(self, "GAME")
        self.Initialize()
        self.AddFlag("not_pick")
        self.kit = uir1.Kit()
        self.chrome = uir1.Ops(self)
        self.Hide()

    def Initialize(self):
        self.queue = []
        self.active = None
        self.started = 0.0
        self.blockedAt = None
        self.suspended = False
        self.pausedAt = None
        self.owned = []
        self.lines = []
        self.symbols = []
        self.kit = self.chrome = self.finial = self.divider = self.measure = None
        self.width, self.height = CARD_WIDTH, CARD_HEIGHT
        self.screen = None
        self.protectedRects = lambda: []
        self.chromeWidth = -1

    def __del__(self):
        ui.Window.__del__(self)

    def Font(self, size, heading=False):
        # Families come from the live R1 kit; sizes preserve the approved C.
        font = self.kit.font("title" if heading else "text")
        return font.split(":", 1)[0] + ":%da" % size

    def Image(self, filename):
        image = ui.ExpandedImageBox()
        image.SetParent(self)
        image.AddFlag("not_pick")
        image.LoadImage(ROOT + filename + ".png")
        image.Show()
        self.owned.append(image)
        return image

    def Text(self, text, x, y, size, color, heading=False):
        line = ui.TextLine()
        line.SetParent(self)
        line.AddFlag("not_pick")
        uikit.SetFont(line, self.Font(size, heading), text)
        line.SetHorizontalAlignCenter()
        line.SetPosition(int(x), int(y))
        line.SetPackedFontColor(Packed(color, 1))
        line.Show()
        self.owned.append(line)
        self.lines.append((line, color))
        return line

    def Measure(self, text, size, heading=False):
        uikit.SetFont(self.measure, self.Font(size, heading), text)
        return uikit.TextWidth(self.measure)

    def Add(self, kind, subject, value, name):
        if not app.IsVisibleNotice():
            return
        notice = model.Decode(kind, subject, value, name)
        if notice is None:
            return
        if notice["kind"] != 3 and notice["subject"] not in localeInfo.DUNGEON_DISPLAY_NAMES:
            return
        # Replace queued intermediate records; never replay a long stale backlog.
        if notice["kind"] != 3:
            self.queue[:] = [entry for entry in self.queue if
                (entry["kind"], entry["subject"]) != (notice["kind"], notice["subject"])]
        self.queue.append(notice)
        self.queue[:] = self.queue[-8:]
        if self.active is None and not self.suspended:
            self.Next()

    def Next(self):
        self.active = self.queue.pop(0) if self.queue else None
        self.blockedAt = None
        if self.active is None:
            self.Hide()
            return
        self.Build()
        self.started = app.GetTime()
        self.OnUpdate()

    def Build(self):
        for widget in self.owned:
            widget.Hide()
        self.owned, self.lines, self.symbols = [], [], []
        self.screen = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        self.width = min(CARD_WIDTH, max(280, self.screen[0] - 24))
        self.chromeWidth = -1
        self.measure = ui.TextLine()
        self.measure.SetParent(self)
        self.measure.AddFlag("not_pick")
        self.owned.append(self.measure)
        notice = self.active
        kind = notice["kind"]
        if kind == 3:
            item.SelectItem(notice["subject"])
            label = item.GetItemName()
            suffix = "+%d" % notice["value"]
            if label.endswith(suffix):
                label = label[:-len(suffix)].rstrip()
            value = suffix
            paragraphs = [(uiScriptLocale.ACHIEVEMENT_REFINE_BODY, 14, 19, 0xded4c4)]
        else:
            dungeon = localeInfo.DUNGEON_DISPLAY_NAMES[notice["subject"]]
            lead, placeholder, tail = uiScriptLocale.ACHIEVEMENT_RECORD_BODY.partition("%s")
            paragraphs = [(lead.rstrip(), 14, 19, 0xded4c4),
                          (dungeon + tail, 15, 20, 0xf4e4cc)]
            label = getattr(uiScriptLocale, "ACHIEVEMENT_TIME" if kind == 1 else "ACHIEVEMENT_DAMAGE")
            value = model.TimeText(notice["value"]) if kind == 1 else format(notice["value"], ",").replace(",", " ")
        # Approved readable C: no player prefix, a smaller frame and larger copy.
        metricWidth = min(170, max(143, int(self.Measure(value, 24)) + 8))
        copyLeft, metricLeft = 66, self.width - 12 - metricWidth
        copyWidth = max(40, metricLeft - 14 - copyLeft)
        stacked = copyWidth < 145
        if stacked:
            metricLeft, metricWidth = copyLeft, self.width - copyLeft - 12
            copyWidth = metricWidth
        nameSize = 25
        while nameSize > 21 and self.Measure(notice["name"], nameSize, True) > copyWidth:
            nameSize -= 1
        nameRows = model.Wrap(notice["name"], copyWidth, lambda text: self.Measure(text, nameSize, True))
        bodyRows = []
        for paragraph, size, step, color in paragraphs:
            if paragraph:
                bodyRows.extend((row, size, step, color) for row in model.Wrap(
                    paragraph, copyWidth, lambda text: self.Measure(text, size)))
        labelRows = model.Wrap(label, metricWidth, lambda text: self.Measure(text, 15))
        valueRows = model.Wrap(value, metricWidth, lambda text: self.Measure(text, 24))
        copyHeight = len(nameRows) * 29 + 2 + sum(row[2] for row in bodyRows)
        metricHeight = len(labelRows) * 20 + 2 + len(valueRows) * 29
        self.height = max(CARD_HEIGHT, (copyHeight + 10 + metricHeight if stacked else max(copyHeight, metricHeight)) + 16)
        self.SetSize(self.width, self.height)
        # Allocate all background slices BEFORE text/art. Later reveal reuses
        # these widgets so a new tile cannot jump above the foreground.
        ops = uir1.L.frame("window", self.width, self.height - 6, "panel")
        ops = [(kind, path, x, y + 5, width, height) for kind, path, x, y, width, height in ops]
        self.chrome.Apply(ops + uir1.L.vein(7, self.height - 12, self.width - 14))
        # R1 artwork is shared, never enlarged to fit a longer string.
        self.finial = self.Image("finial")
        finialScale = min(52.0 / self.finial.GetWidth(), 14.0 / self.finial.GetHeight())
        self.finial.SetScale(finialScale, finialScale)
        self.finial.SetPosition((self.width - 52) // 2, int((14 - self.finial.GetHeight() * finialScale) / 2))
        shapes = (("blade", 3, 67, 78, 15), ("hammer", 46, 0, 40, 78),
                  ("sparks", -8, 60, 30, 30)) if kind == 3 else (
                  ("trophy", 12, 9, 64, 70) if kind == 1 else ("swords", 9, 9, 70, 70),)
        for filename, x, y, boxWidth, boxHeight in shapes:
            widget = self.Image(filename)
            nativeWidth, nativeHeight = widget.GetWidth(), widget.GetHeight()
            scale = min(float(boxWidth) / nativeWidth, float(boxHeight) / nativeHeight) * ICON_SCALE
            w, h = nativeWidth * scale, nativeHeight * scale
            dx, dy = x * ICON_SCALE + (boxWidth * ICON_SCALE - w) / 2, y * ICON_SCALE + (boxHeight * ICON_SCALE - h) / 2
            widget.SetScale(scale, scale)
            # Native expanded-image origins are PIXELS, not normalized fractions.
            widget.SetOrigin(w / 2, h / 2)
            self.symbols.append((widget, dx, dy, w, h))
        center = copyLeft + copyWidth // 2
        top = (self.height - (copyHeight + 10 + metricHeight if stacked else copyHeight)) // 2
        y = top
        for row in nameRows:
            self.Text(row, center, y, nameSize, 0xfff2df, True)
            y += 29
        y += 2
        for row, size, step, color in bodyRows:
            self.Text(row, center, y, size, color)
            y += step
        metricY = y + 10 if stacked else (self.height - metricHeight) // 2
        for row in labelRows:
            self.Text(row, metricLeft + metricWidth // 2, metricY, 15, 0xe7d4b6)
            metricY += 20
        for row in valueRows:
            self.Text(row, metricLeft + metricWidth // 2, metricY + 2, 24, 0xf0d49a)
            metricY += 29
        self.divider = ui.Bar()
        self.divider.SetParent(self)
        self.divider.AddFlag("not_pick")
        self.divider.SetPosition(metricLeft - 10, (self.height - min(metricHeight, self.height - 20)) // 2)
        self.divider.SetSize(1, min(metricHeight, self.height - 20))
        if not stacked:
            self.divider.Show()
        self.owned.append(self.divider)

    def Animate(self, elapsed):
        exitAlpha = 1.0 - Progress(elapsed, 6.0, 6.45)
        reveal = Progress(elapsed, 1.14, 1.78)
        w = max(6, int(self.width * (1 - (1 - reveal) ** 3)))
        if self.chromeWidth != w:
            ops = uir1.L.frame("window", w, self.height - 6, "panel")
            ops = [(kind, path, x, y + 5, width, height) for kind, path, x, y, width, height in ops]
            if w > 16:
                ops += uir1.L.vein(7, self.height - 12, w - 14)
            self.chrome.Apply(ops)
            self.chromeWidth = w
        self.chrome.SetAlpha(reveal * exitAlpha)
        self.finial.SetAlpha(reveal * exitAlpha)
        textAlpha = Progress(elapsed, 1.68, 2.04) * exitAlpha
        for line, color in self.lines:
            line.SetPackedFontColor(Packed(color, textAlpha))
        self.divider.SetColor(Packed(0x746451, textAlpha * .6))
        dock = Progress(elapsed, 1.05, 1.65)
        iconX = int((self.width - ICON_SIZE) * .5 * (1 - dock) + 9 * dock)
        iconY = (self.height - ICON_SIZE) // 2
        iconAlpha = Progress(elapsed, 0, .26) * exitAlpha
        for widget, dx, dy, w, h in self.symbols:
            widget.SetPosition(int(iconX + dx), int(iconY + dy))
            widget.SetAlpha(iconAlpha)
            widget.SetRotation(0)
        if self.active["kind"] == 3:
            angle, spark = -35.0, 0.0
            if elapsed < 1.05:
                angle = -35.0
                for begin in (.05, .53):
                    t = elapsed - begin
                    if 0 <= t < .16:
                        angle = -35 + 60 * t / .16
                    elif .16 <= t < .25:
                        angle = 25 - 115 * (t - .16) / .09
                    elif .25 <= t < .44:
                        angle = -90 + 55 * (t - .25) / .19
                    spark = max(spark, max(0, 1 - abs(t - .25) / .065))
            hammer, dx, dy, w, h = self.symbols[1]
            # Rotate around the authored handle pivot, compensating the native
            # renderer's centre rotation with an explicit centre translation.
            pivotX, pivotY = 66 * ICON_SCALE, 78 * .95 * ICON_SCALE
            vx, vy = dx + w / 2 - pivotX, dy + h / 2 - pivotY
            radians = math.radians(angle)
            cx = pivotX + vx * math.cos(radians) - vy * math.sin(radians)
            cy = pivotY + vx * math.sin(radians) + vy * math.cos(radians)
            hammer.SetPosition(int(iconX + cx - w / 2), int(iconY + cy - h / 2))
            hammer.SetRotation(angle)
            self.symbols[0][0].SetRotation(-3 + 2 * spark)
            self.symbols[2][0].SetAlpha(spark * exitAlpha)

    def OnUpdate(self):
        if not app.IsVisibleNotice():
            self.Close()
            return
        if self.suspended or self.active is None:
            return
        now = app.GetTime()
        screen = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        if screen != self.screen:
            self.Build()
        position = noticeplacement.place((self.width, self.height), ((screen[0] - self.width) // 2, 72), screen, self.protectedRects())
        if position is None:
            if self.blockedAt is None:
                self.blockedAt = now
            self.Hide()
            return
        if self.blockedAt is not None:
            self.started += max(0, now - self.blockedAt)
            self.blockedAt = None
        elapsed = max(0, now - self.started)
        if elapsed >= HOLD:
            self.Next()
            return
        self.SetPosition(*position)
        self.Animate(elapsed)
        self.Show()

    def Suspend(self):
        if not self.suspended:
            self.suspended = True
            self.pausedAt = app.GetTime()
        self.Hide()

    def Resume(self):
        if not self.suspended:
            return
        now = app.GetTime()
        if self.pausedAt is not None and self.active is not None:
            paused = max(0, now - self.pausedAt)
            self.started += paused
            if self.blockedAt is not None:
                self.blockedAt += paused
        self.suspended, self.pausedAt = False, None
        if self.active is None:
            self.Next()
        else:
            self.OnUpdate()

    def Close(self):
        self.Hide()
        self.queue, self.active = [], None

    @WindowDestroy
    def Destroy(self):
        self.Close()
        if self.chrome:
            self.chrome.Hide()
        for widget in self.owned:
            if widget:
                widget.Hide()
        self.Initialize()
