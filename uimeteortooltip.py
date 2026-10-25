import ui
import localeInfo


class MeteorToolTip(ui.ThinBoard):
    WIDTH = 240
    HEIGHT = 94

    def __init__(self):
        # The tooltip board of every other tooltip (uiToolTip.ToolTip), not the red-brown default thin board.
        ui.ThinBoard.__init__(
            self, 'TOP_MOST',
            cornerPrefix=ui.TOOLTIP_CORNER_PREFIX,
            linePrefix=ui.TOOLTIP_LINE_PREFIX,
            baseColor=ui.TOOLTIP_BASE_COLOR,
        )
        self.AddFlag('not_pick')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.HEIGHT)
        # The R1 tooltip frame of the item tooltips (None: the original look or a failure). Made after the board's
        # own pieces and before the texts, so it lies under them.
        self.r1Frame = self._DressR1()
        self.lines = []
        self.lastContent = None
        for y, font in ((12, 'Tahoma:14'), (40, 'Tahoma:12'), (61, 'Tahoma:12')):
            line = ui.TextLine()
            line.SetParent(self)
            line.AddFlag('not_pick')
            line.SetFontName(font)
            line.SetHorizontalAlignCenter()
            line.SetPosition(self.WIDTH // 2, y)
            line.SetOutline()
            line.Show()
            self.lines.append(line)
        self.Hide()

    def _DressR1(self):
        try:
            import uitooltipskin
            return uitooltipskin.Dress(self)
        except Exception:
            return None

    def _FollowLook(self):
        """Settings switched the look since the board was made: the frame of the look in use now, the texts above it
        (uitooltipskin.Sync). Checked when the tooltip appears, not on every Present."""
        try:
            import uitooltipskin
            uitooltipskin.Sync(self, self.lines)
        except Exception:
            pass

    def Present(self, name, state, countdown, x, y, screen_width, screen_height):
        if not self.IsShow():
            self._FollowLook()
        content = (name, state, countdown)
        if content != self.lastContent:
            self.lastContent = content
            self.lines[0].SetText(name)
            # wndMgr's packed-color binding accepts a signed C int. Pass RGB
            # through the float binding, retaining the approved opaque colors.
            self.lines[0].SetFontColor(240 / 255.0, 223 / 255.0, 186 / 255.0)
            statuses = {
                'foreign': (localeInfo.ALTHEA_METEOR_LOCKED, (219 / 255.0, 153 / 255.0, 144 / 255.0)),
                'owner': (localeInfo.ALTHEA_METEOR_OWN, (232 / 255.0, 205 / 255.0, 143 / 255.0)),
                'public': (localeInfo.ALTHEA_METEOR_PUBLIC, (152 / 255.0, 201 / 255.0, 157 / 255.0)),
            }
            text, color = statuses[state]
            self.lines[1].SetText(text)
            self.lines[1].SetFontColor(*color)
            self.lines[1].SetPosition(self.WIDTH // 2, 48 if state == 'public' else 40)
            timer = ''
            if countdown:
                template = localeInfo.ALTHEA_METEOR_PROTECTION_TIME if state == 'owner' else localeInfo.ALTHEA_METEOR_UNLOCK_TIME
                timer = template % countdown
            self.lines[2].SetText(timer)
            self.lines[2].SetFontColor(231 / 255.0, 220 / 255.0, 199 / 255.0)
        # Keep the cursor clear; prefer its right side, flip at the screen edge.
        left = x + 24
        if left + self.WIDTH > screen_width:
            left = x - self.WIDTH - 16
        self.SetPosition(max(0, min(left, screen_width - self.WIDTH)),
                         max(0, min(y - 18, screen_height - self.HEIGHT)))
        self.Show()

    # This client's ThinBoard has no WindowDestroy decorator.
    def Destroy(self):
        self.Hide()
        self.lines = []
        self.lastContent = None
