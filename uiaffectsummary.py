"""Screen-bounded, hoverable details for one active-effect category."""
import app
import fontconfig
import localeInfo
import ui
import uieffecttooltipstyle
import wndMgr
from _weakref import proxy
from settingslocale import Text as T
from uicrimsonember import SettingsScrollBar


def WrapText(text, width, measure):
    """Wrap with native font metrics, including a word wider than the viewport."""
    lines = []
    for paragraph in str(text or "").splitlines():
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if measure(candidate) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ""
            for char in word:
                if line and measure(line + char) > width:
                    lines.append(line)
                    line = ""
                line += char
        if line:
            lines.append(line)
    return lines


def PlaceSummary(anchor, size, screen):
    x, y, icon_height = anchor
    width, height = size
    screen_width, screen_height = screen
    x = max(4, min(x, screen_width - width - 4))
    below = y + icon_height + 2
    if below + height > screen_height - 4:
        below = max(4, y - height - 2)
    return x, max(4, min(below, screen_height - height - 4))


def FormatTime(end_time, now):
    if end_time <= 0 or end_time - now >= 365 * 24 * 3600:
        return ""
    seconds = max(0, end_time - now)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "%s: %d:%02d:%02d" % (localeInfo.LEFT_TIME, hours, minutes, seconds)


class AffectSummary(ui.ThinBoard):
    WIDTH = 360
    MAX_HEIGHT = 480
    HEADER = 36
    FOOTER = 26
    ICON_SIZE = 24
    ROW_GAP = 12
    TEXT_X = 44
    TITLE_COLOR = uieffecttooltipstyle.TITLE_COLOR
    VALUE_COLOR = uieffecttooltipstyle.STAT_COLOR
    TIME_COLOR = uieffecttooltipstyle.TIME_COLOR

    def __init__(self, owner):
        ui.ThinBoard.__init__(
            self, "TOP_MOST",
            cornerPrefix=ui.TOOLTIP_CORNER_PREFIX,
            linePrefix=ui.TOOLTIP_LINE_PREFIX,
            baseColor=ui.TOOLTIP_BASE_COLOR,
        )
        self.AddFlag("float")
        self.owner = proxy(owner)
        self.signature = None
        self.rows = []
        self.timers = []
        self.content_height = 0
        self.leave_time = 0
        self.next_refresh = 0
        self.title = self.Text(self, 12, 10, "", self.TITLE_COLOR, True)
        self.hint = self.Text(self, 12, 0, "", self.TIME_COLOR)
        self.measure = ui.TextLine()
        self.measure.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
        self.boldMeasure = ui.TextLine()
        self.boldMeasure.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL))
        self.viewport = ui.Window()
        self.viewport.SetParent(self)
        self.viewport.SetPosition(8, self.HEADER)
        self.viewport.EnableScissorRect()
        self.viewport.OnMouseWheel = self.OnMouseWheel
        self.viewport.Show()
        self.content = ui.Window()
        self.content.SetParent(self.viewport)
        self.content.OnMouseWheel = self.OnMouseWheel
        self.content.Show()
        self.scroll = SettingsScrollBar()
        self.scroll.SetParent(self)
        self.scroll.SetScrollEvent(ui.__mem_func__(self.OnScroll))
        self.scroll.OnMouseWheel = self.OnMouseWheel
        self.scroll.Hide()

    @staticmethod
    def Text(parent, x, y, text, color, bold=False):
        line = ui.TextLine()
        line.SetParent(parent)
        line.AddFlag("not_pick")
        line.SetFontName(fontconfig.FontForRole(
            fontconfig.ROLE_CONTROL if bold else fontconfig.ROLE_BODY))
        line.SetPosition(x, y)
        line.SetPackedFontColor(color)
        line.SetOutline()
        line.SetText(text)
        line.Show()
        return line

    def Measure(self, text, bold=False):
        measure = self.boldMeasure if bold else self.measure
        measure.SetText(text)
        return measure.GetTextSize()[0]

    def AppendText(self, text, y, color, width, bold=False):
        for part in WrapText(text, width, lambda value: self.Measure(value, bold)):
            line = self.Text(self.content, self.TEXT_X, y, part, color, bold)
            self.rows.append(line)
            y += max(16, line.GetTextSize()[1] + 2)
        return y

    def Open(self):
        self.Refresh()
        if not self.owner.members:
            return
        self.leave_time = app.GetTime() + 0.3
        self.Show()
        self.SetTop()

    def Close(self):
        self.Hide()

    def Destroy(self):
        self.Close()
        self.scroll.Destroy()
        self.scroll.OnMouseWheel = None
        self.viewport.OnMouseWheel = None
        self.content.OnMouseWheel = None
        self.rows = []
        self.timers = []
        self.owner = None

    def Refresh(self):
        data = self.owner.GetSummaryRows()
        if not data:
            self.Close()
            return
        screen = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        signature = (tuple(data), screen)
        if signature != self.signature:
            self.Rebuild(data, screen)
            self.signature = signature
        self.UpdateTimers()
        x, y = self.owner.GetGlobalPosition()
        self.SetPosition(*PlaceSummary((x, y, self.owner.GetHeight()),
                                      (self.GetWidth(), self.GetHeight()), screen))

    def Rebuild(self, data, screen):
        for child in self.rows:
            child.Hide()
        self.rows = []
        self.timers = []
        width = min(self.WIDTH, screen[0] - 16)
        available = max(60, min(self.MAX_HEIGHT, screen[1] - 16) - self.HEADER - self.FOOTER)
        text_width = width - self.TEXT_X - 36
        y = 0
        self.title.SetPackedFontColor(uieffecttooltipstyle.GROUP_COLORS.get(
            getattr(self.owner, "groupKey", ""), self.TITLE_COLOR))
        for entry in data:
            path, title, bonuses, end_time = entry[:4]
            roles = entry[4] if len(entry) > 4 else ()
            title_role = roles if roles and not isinstance(roles, tuple) else None
            row_top = y
            if path:
                icon = ui.ExpandedImageBox()
                icon.SetParent(self.content)
                icon.AddFlag("not_pick")
                icon.LoadImage(path)
                native_width, native_height = icon.GetWidth(), icon.GetHeight()
                scale = min(1.0, float(self.ICON_SIZE) / max(1, native_width, native_height))
                icon.SetScale(scale, scale)
                # Native SetScale can scale bounds twice; normalize once.
                iw, ih = int(native_width * scale), int(native_height * scale)
                icon.SetSize(iw, ih)
                icon.SetPosition(4 + (self.ICON_SIZE - iw) // 2, row_top)
                icon.Show()
                self.rows.append(icon)
            title_color = (uieffecttooltipstyle.ColorForRole(title_role)
                           if title_role else self.TITLE_COLOR)
            y = self.AppendText(title, y, title_color, text_width,
                                bold=not title_role)
            for index, bonus in enumerate(bonuses):
                if bonus != title:
                    role = roles[index] if isinstance(roles, tuple) and index < len(roles) else None
                    color = (uieffecttooltipstyle.ColorForRole(role)
                             if role else self.VALUE_COLOR)
                    y = self.AppendText(bonus, y, color, text_width)
            timer_text = FormatTime(end_time, app.GetGlobalTimeStamp())
            if timer_text:
                timer = self.Text(self.content, self.TEXT_X, y, timer_text, self.TIME_COLOR)
                self.timers.append((timer, end_time))
                self.rows.append(timer)
                y += max(16, timer.GetTextSize()[1] + 2)
            y = max(y, row_top + self.ICON_SIZE) + self.ROW_GAP
        self.content_height = max(0, y - 4)
        visible_height = min(available, self.content_height)
        scrollable = self.content_height > visible_height
        footer = self.FOOTER if scrollable else 6
        self.SetSize(width, self.HEADER + visible_height + footer)
        self.viewport.SetSize(width - 32, visible_height)
        self.content.SetSize(width - 32, self.content_height)
        self.title.SetText("%s (%d)" % (self.owner.GetSummaryTitle(), len(data)))
        self.hint.SetPosition(12, self.GetHeight() - 20)
        self.hint.SetText(T("Kolečkem myši posuneš seznam", "Scroll to see all effects") if scrollable
                          else "")
        if scrollable:
            position = self.scroll.GetPos()
            self.scroll.SetPosition(width - 20, self.HEADER)
            self.scroll.SetScrollBarSize(visible_height)
            self.scroll.SetMiddleBarSize(float(visible_height) / self.content_height)
            self.scroll.SetScrollStep(min(1.0, 48.0 / (self.content_height - visible_height)))
            self.scroll.Show()
            self.scroll.SetPos(position)
        else:
            self.scroll.Hide()
            self.content.SetPosition(0, 0)

    def UpdateTimers(self):
        now = app.GetGlobalTimeStamp()
        for line, end_time in self.timers:
            line.SetText(FormatTime(end_time, now))

    def OnScroll(self):
        maximum = max(0, self.content_height - self.viewport.GetHeight())
        self.content.SetPosition(0, -int(self.scroll.GetPos() * maximum))

    def OnMouseWheel(self, delta):
        if self.scroll.IsShow():
            if delta > 0:
                self.scroll.OnUp()
            elif delta < 0:
                self.scroll.OnDown()
        return True

    def OnUpdate(self):
        if not self.owner or not self.owner.IsShow() or not self.owner.members:
            self.Close()
            return
        now = app.GetTime()
        if self.IsInPosition() or self.owner.IsInPosition():
            self.leave_time = now + 0.3
        elif now > self.leave_time:
            self.Close()
            return
        if now >= self.next_refresh:
            self.next_refresh = now + 0.2
            self.Refresh()


class CompactAffectSummary(AffectSummary):
    GROUP_KEY = ""
    HEADER = 28
    TEXT_X = 4
    ICON_SIZE = 0
    ROW_GAP = 2

    def Rebuild(self, data, screen):
        self.WIDTH = max(190, self.Measure(self.owner.GetSummaryTitle(), True) + 24,
                         max(self.Measure(row[1]) for row in data) + 40)
        AffectSummary.Rebuild(self, data, screen)
        self.title.SetText(self.owner.GetSummaryTitle())
        self.title.SetPackedFontColor(uieffecttooltipstyle.GROUP_COLORS.get(self.GROUP_KEY, self.TITLE_COLOR))
        self.title.SetHorizontalAlignCenter()
        self.title.SetPosition(self.GetWidth() // 2, 10)
        if not self.scroll.IsShow():
            self.viewport.SetSize(self.GetWidth() - 16, self.viewport.GetHeight())
            self.content.SetSize(self.GetWidth() - 16, self.content_height)
        for line in self.rows:
            _, y = line.GetLocalPosition()
            line.SetHorizontalAlignCenter()
            line.SetPosition(self.content.GetWidth() // 2, y)
