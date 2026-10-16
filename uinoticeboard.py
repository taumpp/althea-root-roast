# -*- coding: utf-8 -*-
"""One click-through presenter for notice, important result and zodiac mission."""
import app
import dbg
import grp
import ui
import wndMgr

import noticestyle as style


class NoticeSink:
    """Keep the existing tipBoard/bigBoard call contract on a shared owner."""
    def __init__(self, owner, importance):
        self.owner = owner
        self.importance = importance

    def SetTip(self, message):
        return self.owner.Add(message, self.importance)

    def Hide(self):
        self.owner.Hide()

    def SetYPos(self, value):
        self.owner.minimumY = max(0, int(value))

    def Destroy(self):
        self.owner = None


class MissionSink:
    def __init__(self, owner):
        self.owner = owner
        self.base = ''

    def SetMission(self, text):
        self.base = text if isinstance(text, str) else style.clean_text(text)
        self.owner.SetMission(self.base)

    def SetSubMission(self, text):
        if self.base:
            # Legacy mission API concatenates a server-supplied suffix.
            self.owner.SetMission(self.base + str(text))

    def CleanMission(self):
        self.base = ''
        self.owner.SetMission('')

    def Hide(self):
        self.owner.Hide()


class NoticeBoard(ui.Window):
    def __init__(self):
        ui.Window.__init__(self, 'TOP_MOST')
        self.AddFlag('not_pick')
        self.queue = style.NoticeQueue()
        self.customHolds = {}
        self.active = None
        self.mission = ''
        self.minimumY = 0
        self.started = 0.0
        self.pausedAt = None
        self.suspended = False
        self.pageIndex = 0
        self.pages = []
        self.visualKey = None
        self.loadedAsset = None
        self.screen = None
        self.images = []
        self.lines = []
        self.loggedAssets = set()
        self.measureLine = ui.TextLine()
        self.measureLine.SetParent(self)
        self.measureLine.AddFlag('not_pick')
        self.measureLine.Hide()
        self.fallback = ui.Bar()
        self.fallback.SetParent(self)
        self.fallback.AddFlag('not_pick')
        self.fallback.SetColor(grp.GenerateColor(0.035, 0.035, 0.045, 0.93))
        self.fallback.Hide()
        self.Hide()

    def Add(self, message, importance=1, hold=None):
        if not app.IsVisibleNotice():
            return False
        added = self.queue.add(message, importance, app.GetTime())
        if added and hold is not None:
            if len(self.customHolds) >= 64:
                self.customHolds.pop(next(iter(self.customHolds)))
            self.customHolds[(importance, style.clean_text(message))] = max(1.0, min(10.0, float(hold)))
        return added

    def SetMission(self, text):
        text = style.clean_text(text)
        if text != self.mission:
            self.mission = text
            if self.active is None:
                self.visualKey = None

    def Remove(self, message, importance=1):
        """Withdraw one stale system notice without disturbing other messages."""
        identity = (importance, style.clean_text(message))
        self.queue.pending[:] = [entry for entry in self.queue.pending if entry != identity]
        self.customHolds.pop(identity, None)
        if self.active == identity:
            self.active = None
            self.visualKey = None
            self.Hide()

    def Clear(self):
        self.queue.clear()
        self.customHolds.clear()
        self.active = None
        self.mission = ''
        self.visualKey = None
        self.pages = []
        self.pageIndex = 0
        self.pausedAt = None
        self.suspended = False
        self.Hide()

    def Suspend(self):
        self.suspended = True
        if self.pausedAt is None:
            self.pausedAt = app.GetTime()
        self.Hide()

    def Resume(self):
        self.suspended = False

    def Destroy(self):
        self.Clear()
        for child in self.images + self.lines:
            child.Hide()
        self.images = []
        self.lines = []
        if self.measureLine:
            self.measureLine.Hide()
        if self.fallback:
            self.fallback.Hide()
        self.measureLine = None
        self.fallback = None

    def _Measure(self, font, text):
        # The native glyph run must be cleared before switching fonts.
        self.measureLine.SetText('')
        self.measureLine.SetFontName(font)
        self.measureLine.SetText(text)
        return self.measureLine.GetTextSize()

    def _LoadArt(self, importance, role, width):
        path = style.ASSET_ROOT + '%02d_%s_%d.png' % (importance, role, width)
        if path == self.loadedAsset:
            return
        self.loadedAsset = path
        for image in self.images:
            image.Hide()
        self.images = []
        self.fallback.Hide()
        try:
            for index in range(7):
                image = ui.ExpandedImageBox()
                image.SetParent(self)
                image.AddFlag('not_pick')
                image.LoadImage(path)
                image.SetPosition(0, 0)
                image.SetAlpha(0.0)
                # Authored 520/780/1040 variants render at native size. Never
                # call SetScale on this image or its text-bearing parent.
                self.images.append(image)
            self.SetSize(width, self.images[0].GetHeight())
        except RuntimeError as error:
            for image in self.images:
                image.Hide()
            self.images = []
            height = round((39 if role == 'notice' else (82 if importance == 1 else 122)) * width/520.0)
            self.SetSize(width, height)
            self.fallback.SetSize(width, height)
            self.fallback.Show()
            if path not in self.loggedAssets:
                dbg.TraceError('Notice artwork unavailable: %s (%s)' % (path, error))
                self.loggedAssets.add(path)

    def _Prepare(self, entry, width, now, persistent=False):
        importance, text = entry
        self.role, self.pages = style.layout(text, importance, width, self._Measure)
        self.pageIndex = 0
        self.started = now
        self._LoadArt(importance, self.role, width)
        self.visualKey = (persistent, importance, text, width)
        self._SetPage(width)

    def _SetPage(self, width):
        for line in self.lines:
            line.Hide()
        self.lines = []
        center = round(width * (266.0/520 if self.visualKey[1] == 1 else 0.5))
        for row in self.pages[self.pageIndex]:
            line = ui.TextLine()
            line.SetParent(self)
            line.AddFlag('not_pick')
            line.SetText('')
            line.SetFontName(row['font'])
            line.SetHorizontalAlignCenter()
            line.SetVerticalAlignTop()
            line.SetPosition(center, row['y'])
            line.SetText(row['text'])
            line.Show()
            self.lines.append(line)

    def _Draw(self, entry, width, screen_width, screen_height, values):
        scale = width/520.0
        y = max(self.minimumY, round(88*scale))
        if screen_width < 1000:
            y = max(y, 210)
        y = min(y, max(0, screen_height-self.GetHeight()-90))
        self.SetPosition((screen_width-width)//2, y+round(values['offset']*scale))
        bands = style.reveal_bands(width, values['reveal'])
        for i, image in enumerate(self.images):
            if i >= len(bands):
                image.Hide()
                continue
            left, right, alpha = bands[i]
            # Native cropping truncates float*width to LONG. Bias inside that
            # same integer pixel to keep disjoint bands free of one-pixel seams.
            crop_left = -(left+0.25)/width if left else 0.0
            crop_right = -(width-right+0.25)/width if right < width else 0.0
            image.SetRenderingRect(crop_left, 0.0, crop_right, 0.0)
            image.SetAlpha(alpha * values['art'])
            image.Show()
        if not self.images:
            self.fallback.SetColor(grp.GenerateColor(0.035, 0.035, 0.045, 0.93*values['art']))
        for line, row in zip(self.lines, self.pages[self.pageIndex]):
            r, g, b = style.COLORS[row['color']]
            line.SetPackedFontColor(grp.GenerateColor(r, g, b, values['text']))
        self.Show()

    def Update(self, arrivalVisible=False):
        """GameWindow owns the sole tick, including while this window is hidden."""
        now = app.GetTime()
        if arrivalVisible or self.suspended:
            if self.pausedAt is None:
                self.pausedAt = now
            self.Hide()
            return
        if self.pausedAt is not None:
            self.started += max(0.0, now-self.pausedAt)
            self.pausedAt = None
        if not app.IsVisibleNotice():
            self.queue.clear()
            if self.active is not None:
                self.visualKey = None
            self.active = None
        if self.active is None:
            self.active = self.queue.pop()
        persistent = self.active is None
        entry = self.active or ((1, self.mission) if self.mission else None)
        if entry is None:
            self.visualKey = None
            self.Hide()
            return
        screen_width, screen_height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        width = style.profile(screen_width, screen_height)
        key = (persistent, entry[0], entry[1], width)
        if key != self.visualKey:
            self._Prepare(entry, width, now, persistent)
        elapsed = max(0.0, now-self.started)
        if persistent:
            if len(self.pages) > 1 and elapsed >= 4.5:
                self.pageIndex = (self.pageIndex+1) % len(self.pages)
                self.started = now
                self._SetPage(width)
            values = {'art': 1.0, 'text': 1.0, 'reveal': 1.0, 'offset': 0, 'done': False}
        else:
            enter, hold, leave = style.TIMING[entry[0]]
            hold = self.customHolds.get(entry, hold)
            if self.pageIndex+1 < len(self.pages) and elapsed >= enter+hold:
                self.pageIndex += 1
                # Page changes keep the carrier fully visible. Only the final
                # page fades out; each page receives its own full read time.
                self.started = now-enter
                self._SetPage(width)
                elapsed = enter
            values = style.animation(entry[0], elapsed, hold)
            if values['done']:
                self.customHolds.pop(entry, None)
                self.active = None
                self.visualKey = None
                self.Hide()
                return
        self._Draw(entry, width, screen_width, screen_height, values)
