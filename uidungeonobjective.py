"""Variant A: native text inside the existing Althea minimap frame."""
import app
import grp
import ui
import uidungeontrack
from dungeonobjectivemodel import ObjectiveState, Marquee
from dungeonobjectivetext import TEXTS


class ObjectivePanel(ui.Window):
    def __init__(self, parent):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetSize(136, 137)
        # Native SetParent/SetSize leave the cached global rect at (0, 0).
        # Anchor before creating children so the disc/text share the frame.
        self.SetPosition(0, 0)
        self.AddFlag("not_pick")
        self.state = ObjectiveState(TEXTS)
        self.scroll = Marquee()
        self.titleScroll = Marquee()
        self.children = []
        self.background = ui.ImageBox()
        self.background.SetParent(self)
        self.background.AddFlag("not_pick")
        self.background.LoadImage("d:/ymir work/ui/game/dungeon_objective/disc.png")
        self.background.Show()
        gold = grp.GenerateColor(0.82, 0.69, 0.40, 1.0)
        ink = grp.GenerateColor(0.92, 0.89, 0.81, 1.0)
        self.titleView, self.title = self._viewport(29, 20, 76, "Tahoma:11b", gold)
        self.phase = self._text(self, 67, 38, "Tahoma:16b", ink, True)
        self.viewport, self.notice = self._viewport(19, 64, 97, "Tahoma:12", ink)
        self.count = self._text(self, 67, 95, "Tahoma:14b", gold, True)
        self.track = self._bar(grp.GenerateColor(0.21, 0.16, 0.14, 1.0), 70)
        self.fill = self._bar(grp.GenerateColor(0.65, 0.14, 0.11, 1.0), 0)
        self.Hide()

    def _text(self, parent, x, y, font, color, centered=False):
        text = ui.TextLine()
        text.SetParent(parent)
        text.AddFlag("not_pick")
        text.SetFontName(font)
        text.SetPackedFontColor(color)
        text.SetPosition(x, y)
        if centered:
            text.SetHorizontalAlignCenter()
        text.Show()
        self.children.append(text)
        return text

    def _viewport(self, x, y, width, font, color):
        view = ui.Window()
        view.SetParent(self)
        view.AddFlag("not_pick")
        view.SetPosition(x, y)
        view.SetSize(width, 18)
        view.EnableScissorRect()
        view.Show()
        self.children.append(view)
        return view, self._text(view, 0, 0, font, color)

    def _bar(self, color, width):
        bar = ui.Bar()
        bar.SetParent(self)
        bar.AddFlag("not_pick")
        bar.SetPosition(32, 115)
        bar.SetSize(width, 4)
        bar.SetColor(color)
        self.children.append(bar)
        return bar

    def Receive(self, arguments):
        if not self.state.receive(arguments):
            return False
        state = self.state
        if not state.visible:
            self.Hide()
            return True
        data = uidungeontrack.dungeonData.get(state.boss)
        if not data:
            state.visible = False
            self.Hide()
            return True
        self.title.SetText(data["name"].upper())
        self.phase.SetText("%d / %d" % (state.phase, state.phases) if state.phases else "")
        self.notice.SetText(state.text)
        now = app.GetTime()
        self.scroll.set_text(state.text_identity, self.notice.GetTextSize()[0], 97, now)
        self.titleScroll.set_text(state.boss, self.title.GetTextSize()[0], 76, now)
        self.count.SetText("%d / %d" % (state.current, state.target) if state.target else "")
        if state.target:
            self.track.Show()
            self.fill.SetSize(int(70 * state.current / state.target), 4)
            self.fill.Show()
        else:
            self.track.Hide()
            self.fill.Hide()
        self.OnUpdate()
        self.Show()
        return True

    def OnUpdate(self):
        now = app.GetTime()
        self.notice.SetPosition(int(self.scroll.offset(now)), 0)
        self.title.SetPosition(int(self.titleScroll.offset(now)), 0)

    def Destroy(self):
        self.Hide()
        for child in self.children:
            child.Hide()
        self.children = []
