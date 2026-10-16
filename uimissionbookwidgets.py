"""Native components shared by the mission book window and its small HUD."""
import fontconfig
import item
import nonplayer
import ui
import WikiRenderTarget
import uicrimsoncontrols
from countdownmodel import fit_text

INK = (0.894, 0.855, 0.796)
GOLD = (0.898, 0.757, 0.482)
DIM = (0.671, 0.635, 0.588)
MISSION_FRAME = "d:/ymir work/ui/game/mission_book/Frame_"
# This fork predates the optional community WindowDestroy decorator.
# Explicit owned cleanup is still required in every consumer.
WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)


def line(parent, x, y, text="", color=INK, align="left", role=fontconfig.ROLE_BODY):
    result = ui.TextLine()
    result.SetParent(parent)
    result.AddFlag("not_pick")
    result.SetFontName(fontconfig.FontForRole(role))
    result.SetPosition(x, y)
    if align == "center":
        result.SetHorizontalAlignCenter()
    elif align == "right":
        result.SetHorizontalAlignRight()
    result.SetText(text)
    result.SetFontColor(*color)
    result.Show()
    return result


def fitted(label, text, width):
    def measure(value):
        label.SetText(value)
        return label.GetTextSize()[0]
    label.SetText(fit_text(text, max(0, width), measure))


def book_image(parent, book, x, y):
    item.SelectItem(book)
    icon = ui.ImageBox()
    icon.SetParent(parent)
    icon.AddFlag("not_pick")
    icon.LoadImage(item.GetIconImageFileName())
    icon.SetPosition(x, y)
    icon.Show()
    return icon


def button(parent, x, y, text, callback):
    result = ui.Button()
    result.SetParent(parent)
    result.SetPosition(x, y)
    uicrimsoncontrols.ApplyVisuals(result, "92x24")
    result.SetText(text)
    result.SetEvent(callback)
    result.Show()
    return result


class Target(ui.Window):
    """One rotating live objective inside its own tooltip frame."""
    def __init__(self, parent, vnum, count, x, y, kind=1, display_name=None):
        ui.Window.__init__(self)
        self.Initialize()
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetSize(168, 186)
        self.AddFlag("not_pick")
        self.vnum = vnum
        self.kind = kind
        self.view = ui.WikiRenderTargetUi()
        self.view.SetParent(self)
        self.view.AddFlag("not_pick")
        self.view.SetPosition(0, 0)
        self.view.SetSize(168, 138)
        self.frame = ui.ThinBoard(cornerPrefix=MISSION_FRAME + "Corner_",
                                  linePrefix=MISSION_FRAME + "Line_",
                                  baseColor=0x00000000)
        self.frame.SetParent(self)
        self.frame.AddFlag("attach")
        self.frame.AddFlag("not_pick")
        # Native widgets can otherwise draw at screen origin on first open.
        self.frame.SetPosition(0, 0)
        self.frame.SetSize(168, 138)
        self.frame.Show()
        name = display_name or nonplayer.GetMonsterName(vnum)
        self.name_text = name
        self.name = line(self, 84, 148, name, align="center")
        fitted(self.name, name, 162)
        self.count = line(self, 84, 166, "0 / %d" % count, GOLD, "center")
        self.children = [self.frame, self.view, self.name, self.count]
        self.Show()

    def Initialize(self):
        self.index = None
        self.vnum = 0
        self.kind = 1
        self.name_text = ""
        self.frame = self.view = self.name = self.count = None
        self.children = []

    def __del__(self):
        ui.Window.__del__(self)

    def Open(self):
        if self.index is not None:
            return
        try:
            self.index = int(WikiRenderTarget.GetFreeIndex(86, 1000000))
            # Legacy Wiki widget has a uint8 target index. Reject overflow
            # before binding/removing an index we do not own.
            if not 1 <= self.index <= 255:
                self.index = None
                return
            self.view.SetRenderTarget(self.index)
            WikiRenderTarget.SetBackground(self.index,
                "d:/ymir work/ui/game/crimson_ember/mount_system/k1/preview_254x266.png")
            WikiRenderTarget.SetRotation(self.index, True)
            # Published FrameWikiModel fits deformed bounds and viewport aspect.
            # Leave extra room for idle poses/weapons/effects. Set before model
            # selection; do not accumulate user-speed-dependent Zoom steps.
            WikiRenderTarget.SetScale(self.index, 0.8)
            WikiRenderTarget.SelectModel(self.index, self.vnum)
            WikiRenderTarget.SetVisibility(self.index, True)
            self.view.Show()
        except (AttributeError, RuntimeError, TypeError, ValueError):
            self.Close()

    def Close(self):
        index, self.index = self.index, None
        if self.view:
            self.view.Hide()
        if index is not None:
            try:
                WikiRenderTarget.SetVisibility(index, False)
                WikiRenderTarget.Remove(index)
            except (AttributeError, RuntimeError):
                pass

    @WindowDestroy
    def Destroy(self):
        self.Close()
        self.Hide()
        self.Initialize()
