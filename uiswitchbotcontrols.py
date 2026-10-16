"""Native Althea controls for the compact switchbot extension."""
import item
import player
import ui
import wndMgr
import bonuscatalog
from switchbotoptions import options


def Text(parent, x, y, value):
    text = ui.TextLine()
    text.SetParent(parent)
    text.AddFlag('not_pick')
    text.SetPosition(x, y)
    text.SetText(value)
    text.Show()
    return text


def Button(parent, x, y, text, event):
    button = ui.Button()
    button.SetParent(parent)
    for method, state in ((button.SetUpVisual, 1), (button.SetOverVisual, 2),
                          (button.SetDownVisual, 3), (button.SetDisableVisual, 3)):
        method('d:/ymir work/ui/switchbot/btn_big_0%d.sub' % state)
    button.SetPosition(x, y)
    button.SetText(text)
    button.SetEvent(event)
    button.Show()
    return button


def Arrow(parent, x, y, event):
    button = ui.Button()
    button.SetParent(parent)
    button.SetUpVisual('d:/ymir work/ui/game/switchbot/arrow_normal.tga')
    button.SetOverVisual('d:/ymir work/ui/game/switchbot/arrow_hover.tga')
    button.SetDownVisual('d:/ymir work/ui/game/switchbot/arrow_down.tga')
    button.SetPosition(x, y)
    button.SetEvent(event)
    button.Show()
    return button


def PopupPosition(anchor, width, height, preferAbove=False):
    x, y = anchor.GetGlobalPosition()
    screenWidth, screenHeight = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
    below = y + anchor.GetHeight()
    left = max(0, min(x, screenWidth - width))
    if preferAbove and y >= height:
        return left, y - height
    if below + height <= screenHeight:
        return left, below
    if y >= height:
        return left, y - height
    # On a short display use the side: never cover the arrow that closes us.
    top = max(0, min(y, screenHeight - height))
    if x >= width:
        return x - width, top
    return x + anchor.GetWidth(), top


class ItemChoice(ui.ThinBoardCircle):
    def __init__(self, parent, width, vnum, event):
        ui.ThinBoardCircle.__init__(self)
        self.SetParent(parent)
        self.SetSize(width, 40)
        self.SetOnMouseLeftButtonUpEvent(event)
        self.icon = ui.ImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.SetPosition(4, 4)
        self.name = Text(self, 41, 5, '')
        self.count = Text(self, 41, 21, '')
        self.SetItem(vnum)
        self.Show()

    def SetItem(self, vnum):
        self.vnum = vnum
        if not vnum:
            # No catalog yet (or no scroll for this item): an empty choice.
            self.icon.Hide()
            self.name.SetText('-')
            self.count.SetText('')
            return
        item.SelectItem(vnum)
        self.icon.LoadImage(item.GetIconImageFileName())
        self.icon.Show()
        self.name.SetText(item.GetItemName())
        self.RefreshCount()

    def RefreshCount(self):
        if self.vnum:
            self.count.SetText('%s ks' % player.GetItemCountByVnum(self.vnum))


class ScrollPicker(ui.Window):
    def __init__(self, parent, event, model=None):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetSize(214, 40)
        self.event = event
        self.model = model or options
        self.enabled = True
        self.choice = ItemChoice(self, 214, 0, self.Toggle)
        self.arrow = Arrow(self.choice, 194, 10, self.Toggle)
        self.popup = ui.ThinBoardCircle('TOP_MOST')
        self.popup.AddFlag('float')
        self.rows = []
        self.menu = ()
        self.Show()

    def BuildRows(self):
        # One row per offered scroll kind, from the server bonus catalog.
        menu = tuple(bonuscatalog.MenuScrolls())
        if menu == self.menu:
            return
        self.menu = menu
        for row in self.rows:
            row.Hide()
        self.rows = []
        self.popup.SetSize(300, 8 + 42 * len(menu))
        for index, vnum in enumerate(menu):
            row = ItemChoice(self.popup, 292, vnum, lambda v=vnum: self.Select(v))
            row.SetPosition(4, 4 + 42 * index)
            self.rows.append(row)

    def Toggle(self):
        if not self.popup:
            return
        if self.popup.IsShow():
            self.popup.Hide()
        elif self.enabled:
            self.BuildRows()
            if not self.rows:
                return
            self.popup.SetPosition(*PopupPosition(self, 300, self.popup.GetHeight(), True))
            for row in self.rows:
                row.RefreshCount()
            self.popup.SetTop()
            self.popup.Show()

    def Select(self, vnum):
        self.popup.Hide()
        if self.enabled:
            self.event(vnum)

    def Refresh(self, slot):
        self.enabled = not self.model.IsActive(slot) if self.model is not options else not __import__('switchbot').IsActive(slot)
        self.choice.SetItem(self.model.Scroll(slot))
        if not self.enabled:
            self.popup.Hide()

    def Close(self):
        if self.popup:
            self.popup.Hide()

    def Destroy(self):
        self.Close()
        self.rows = []
        self.event = None
        self.popup = None


class ValuePicker(ui.ThinBoardCircle):
    def __init__(self):
        ui.ThinBoardCircle.__init__(self, 'TOP_MOST')
        self.AddFlag('float')
        self.rows = []
        self.event = None

    def Toggle(self, anchor, values, event):
        if self.IsShow():
            self.Close()
        else:
            self.Open(anchor, values, event)

    def Open(self, anchor, values, event):
        self.Hide()
        self.rows = []
        self.event = event
        # Menu suggestions supplement, never replace, the editable integer field.
        values = tuple(sorted(set(values)))
        self.SetSize(80, 8 + 20 * len(values))
        for index, value in enumerate(values):
            row = ui.ThinBoardCircle()
            row.SetParent(self)
            row.SetPosition(4, 4 + 20 * index)
            row.SetSize(72, 20)
            row.SetOnMouseLeftButtonUpEvent(lambda v=value: self.Select(v))
            row.label = Text(row, 8, 2, str(value))
            row.Show()
            self.rows.append(row)
        self.SetPosition(*PopupPosition(anchor, 80, self.GetHeight()))
        self.SetTop()
        self.Show()

    def Select(self, value):
        self.Hide()
        if self.event:
            self.event(value)

    def Close(self):
        self.Hide()
        self.event = None
        self.rows = []
