"""Owner-approved chat controls. Icon images never enter the button resolver."""
import grp
import ui
import uiToolTip
import wndMgr
import compactchatmodel as model
from _weakref import proxy
from uicrimsonember import CrimsonWindowChrome

ICON_ROOT = 'chat_compact/icons/'
ICONS = {
    'all': "all.png", 'shout': "shout.png", 'party': "party.png",
    'guild': "guild.png", 'system': "system.png", 'add': "add.png",
    'settings': "settings.png", 'recent': "recent.png", 'emoji': "emoji.png",
    'symbols': "symbols.png", 'repeat': "repeat.png", 'send': "send.png",
    'pm': "pm.png", 'history': "history.png", 'pause': "pause.png", 'close': "close.png",
}
INK = (.88, .85, .78)
DIM = (.70, .65, .57)
GOLD = (.94, .86, .70)
GREEN = (.57, .73, .57)


def bar(x, y, width, height, rgb, alpha=1):
    grp.SetColor(grp.GenerateColor(rgb[0], rgb[1], rgb[2], alpha))
    grp.RenderBar(int(x), int(y), int(width), int(height))


def label(parent, x, y, value='', size=12, color=INK):
    text = ui.TextLine()
    text.SetParent(parent)
    text.AddFlag('not_pick')
    text.SetPosition(x, y)
    text.SetFontName('Tahoma:%d' % size)
    text.SetFontColor(*color)
    text.SetText(value)
    text.Show()
    return text


def _R1Hint():
    """uir1 when the R1 look is on (Settings -> "Starý vzhled" keeps the original tooltip board), else None."""
    try:
        import uir1
        return uir1 if uir1.UseR1() else None
    except Exception:
        return None


class IconControl(ui.Window):
    def __init__(self, parent, x, y, icon, tooltip, event, width=24, text='', height=24):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetSize(width, height)
        self.icon = None
        self.text = None
        self.tip = None
        self.tooltip = tooltip
        self.event = event
        self.hover = False
        self.pressed = False
        self.selected = False
        self.running = False
        self.repeat_icon = icon == 'repeat'
        self.enabled = True
        self.check = None
        if icon:
            self.icon = ui.ImageBox()
            self.icon.SetParent(self)
            self.icon.AddFlag('not_pick')
            self.icon.LoadImage(ICON_ROOT + ICONS[icon])
            self.icon.SetPosition(5 if text else 2, 4 if height == 28 else 2)
            self.icon.Show()
        if text:
            self.text = label(self, 28 if icon else 0, 8 if height == 28 else 5, text)
            if not icon:
                self.text.SetPosition(width // 2, 8 if height == 28 else 5)
                self.text.SetHorizontalAlignCenter()
        self.Show()

    def SetText(self, value):
        if self.text:
            self.text.SetText(value)

    def SetSelected(self, value):
        self.selected = bool(value)
        if self.icon:
            self.icon.SetDiffuseColor(1, 1, 1, 1 if self.selected else .86)
        if self.text:
            self.text.SetFontColor(*(GOLD if self.selected else DIM))

    def SetEnabled(self, value):
        self.enabled = bool(value)
        if self.icon:
            self.icon.SetDiffuseColor(1, 1, 1, 1 if self.enabled else .45)

    def OnMouseOverIn(self):
        self.hover = True
        if self.tooltip:
            if _R1Hint():
                # R1 look: the one R1 hint above the control (the header tabs and icons stay these controls).
                _R1Hint().ShowHint(None, self, self.tooltip)
                return
            if not self.tip:
                self.tip = uiToolTip.ToolTip()
                self.tip.AutoAppendNewTextLineResize(self.tooltip)
            self.tip.ShowToolTip()

    def OnMouseOverOut(self):
        self.hover = False
        self.pressed = False
        if getattr(self, 'tip', None):
            self.tip.HideToolTip()
        if _R1Hint():
            _R1Hint().HideHint(self)

    def OnMouseLeftButtonDown(self):
        self.pressed = self.enabled
        return True

    def OnMouseLeftButtonUp(self):
        activate = self.enabled and self.pressed and self.IsIn()
        self.pressed = False
        if activate and self.event:
            self.event()
        return True

    def OnRender(self):
        x, y = self.GetGlobalPosition()
        w, h = self.GetWidth(), self.GetHeight()
        if self.repeat_icon and self.icon:
            self.icon.SetDiffuseColor(1, 1, 1, 1 if self.running or self.hover else .58)
        if self.selected:
            bar(x, y, w, h - 1, (52/255., 27/255., 29/255.))
            bar(x+6, y+h-1, w-12, 1, (169/255., 73/255., 69/255.))
        elif self.hover or self.pressed:
            bar(x, y, w, h, (48/255., 37/255., 30/255.), 1 if self.pressed else .85)
        if self.running:
            bar(x+4, y+h-1, 16, 1, (151/255., 125/255., 82/255.))
            bar(x+19, y+2, 3, 3, GREEN)
        if self.check is not None:
            ui.RenderRoundBox(x+1, y+4, 12, 12, grp.GenerateColor(.47, .39, .27, 1))
            if self.check:
                grp.SetColor(grp.GenerateColor(*GOLD, 1))
                grp.RenderLine(x+3, y+10, 3, 3)
                grp.RenderLine(x+6, y+13, 5, -7)
        elif not self.icon and h == 22:
            bar(x+4, y+21, w-8, 1, (.31, .25, .19))

    def Hide(self):
        self.OnMouseOverOut()
        ui.Window.Hide(self)

    def Destroy(self):
        self.Hide()
        self.event = None
        self.tip = None
        self.text = None
        self.icon = None


def text_button(parent, x, y, width, text, tooltip, event):
    return IconControl(parent, x, y, None, tooltip, event, width, text, 22)


def checkbox(parent, x, y, width, text, checked, event):
    control = IconControl(parent, x, y, None, 'Zobrazí nebo skryje: ' + text, event, width, text, 22)
    control.check = bool(checked)
    control.text.SetHorizontalAlignLeft()
    control.text.SetPosition(20, 5)
    control.text.SetFontName('Tahoma:11')
    control.text.SetText('')
    control.text.SetText(text)
    return control


def section(parent, x, y, width, text):
    """Section heading of a panel (upper case, gold)."""
    return label(parent, x, y, text.upper(), 11, GOLD)


def tabs(parent, titles, selected, make_event, tooltip):
    """Page tabs of a panel; make_event(title) returns the click callback. Returns the controls."""
    controls = []
    for index, title in enumerate(titles):
        button = IconControl(parent, 6+index*103, 33, None, tooltip + title, make_event(title), 103, title, 28)
        button.SetSelected(title == selected)
        controls.append(button)
    return controls


def slider(parent, x, y, position, event):
    """Opacity slider (0..1) of the settings panel."""
    control = ui.SliderBar()
    control.SetParent(parent)
    path = 'd:/ymir work/ui/public/crimson/controls/slider/'
    control.SetButtonVisual(path, 'small_thumb_01.tga', 'small_thumb_02.tga', 'small_thumb_03.tga')
    control.SetBackgroundVisual(path + 'small_track.tga')
    control.SetPosition(x, y)
    control.SetSliderPos(position)
    control.SetEvent(event)
    control.Show()
    return control


def divider(parent, x, y, width):
    """No divider in the original look."""
    return None


class ResizeGrip(IconControl):
    def __init__(self, owner):
        IconControl.__init__(self, owner, 0, 0, None,
            'Tažením změnit šířku a výšku chatu.', None, 16, '', 28)
        self.owner = proxy(owner)
        self.AddFlag('dragable')

    def OnMouseLeftButtonDown(self):
        self.OnMouseOverOut()
        self.owner.BeginResize()
        return True

    def OnMouseDrag(self, x, y):
        self.owner.DragResize()

    def OnMouseLeftButtonUp(self):
        self.owner.EndResize()
        return True

    def OnRender(self):
        x, y = self.GetGlobalPosition()
        grp.SetColor(grp.GenerateColor(*(GOLD if self.hover else DIM), 1))
        for offset in (0, 4, 8):
            grp.RenderLine(x+3+offset, y+4, 9-offset, 9-offset)

    def Destroy(self):
        self.owner = None
        IconControl.Destroy(self)


class MoveGrip(IconControl):
    def __init__(self, owner):
        IconControl.__init__(self, owner, 10, 28, None,
            'Tažením přesunout chat. Poloha se uloží pro tuto postavu.', None, 568, '', 10)
        self.owner = proxy(owner)
        self.AddFlag('dragable')

    def OnMouseLeftButtonDown(self):
        self.OnMouseOverOut()
        self.owner.BeginMove()
        return True

    def OnMouseDrag(self, x, y):
        self.owner.DragMove()

    def OnMouseLeftButtonUp(self):
        self.owner.EndMove()
        return True

    def OnRender(self):
        x, y = self.GetGlobalPosition()
        for offset in (3, 6):
            bar(x+self.GetWidth()//2-14, y+offset, 28, 1, GOLD if self.hover else DIM, .8)

    def Destroy(self):
        self.owner = None
        IconControl.Destroy(self)


class DropDown(IconControl):
    def __init__(self, parent, x, y, width, options, value, changed):
        IconControl.__init__(self, parent, x, y, None, 'Vybrat velikost písma.',
                             ui.__mem_func__(self.Toggle), width, '', 22)
        self.options = list(options)
        self.changed = changed
        self.value = value
        self.text = label(self, width//2-5, 5, '')
        self.text.SetHorizontalAlignCenter()
        self.menu = None
        self.SetValue(value)

    def SetValue(self, value):
        self.value = value
        self.SetText(next(text for key, text in self.options if key == value))

    def Toggle(self):
        if self.menu:
            self.CloseMenu()
            return
        self.menu = ui.Window('TOP_MOST')
        self.menu.SetSize(self.GetWidth(), len(self.options)*22+4)
        x, y = self.GetGlobalPosition()
        self.menu.SetPosition(x, max(0, min(y+self.GetHeight(), wndMgr.GetScreenHeight()-self.menu.GetHeight())))
        self.menu.fill = ui.Bar()
        self.menu.fill.SetParent(self.menu)
        self.menu.fill.AddFlag('not_pick')
        self.menu.fill.SetPosition(0, 0)
        self.menu.fill.SetSize(self.menu.GetWidth(), self.menu.GetHeight())
        self.menu.fill.SetColor(grp.GenerateColor(.06, .05, .05, .98))
        self.menu.fill.Show()
        self.menu.options = []
        for index, (value, text) in enumerate(self.options):
            button = text_button(self.menu, 2, 2+index*22, self.GetWidth()-4, text,
                                 'Změna se projeví ihned.', lambda value=value: self.Select(value))
            button.SetSelected(value == self.value)
            self.menu.options.append(button)
        self.OnUpdate()
        self.menu.Show()
        self.menu.SetTop()

    def OnUpdate(self):
        if self.menu:
            x, y = self.GetGlobalPosition()
            position = (max(0, min(x, wndMgr.GetScreenWidth()-self.menu.GetWidth())),
                        max(0, min(y+self.GetHeight(), wndMgr.GetScreenHeight()-self.menu.GetHeight())))
            if position != self.menu.GetGlobalPosition():
                self.menu.SetPosition(*position)

    def Select(self, value):
        self.SetValue(value)
        self.CloseMenu()
        self.changed(value)

    def CloseMenu(self):
        if self.menu:
            self.menu.Hide()
            for button in self.menu.options:
                button.Destroy()
            self.menu.options = []
            self.menu = None

    def OnRender(self):
        IconControl.OnRender(self)
        x, y = self.GetGlobalPosition()
        grp.SetColor(grp.GenerateColor(*DIM, 1))
        grp.RenderLine(x+self.GetWidth()-14, y+9, 4, 4)
        grp.RenderLine(x+self.GetWidth()-10, y+13, 4, -4)

    def Hide(self):
        if hasattr(self, 'menu'):
            self.CloseMenu()
        IconControl.Hide(self)

    def Destroy(self):
        self.changed = None
        IconControl.Destroy(self)


class PassivePreview(ui.Window):
    def __init__(self, parent, size, opacity):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(13, 337)
        self.SetSize(295, 34)
        self.text = label(self, 8, 8, '')
        self.font_size = None
        self.SetStyle(size, opacity)
        self.Show()

    def SetStyle(self, size, opacity):
        self.opacity = opacity/100.
        if size != self.font_size:
            self.font_size = size
            self.text.SetFontName(model.chat_font(size))
            self.text.SetText('')
            self.text.SetText('Náhled chatu při hraní')

    def OnRender(self):
        x, y = self.GetGlobalPosition()
        bar(x, y, self.GetWidth(), self.GetHeight(), (.035, .039, .043), self.opacity)

    def Destroy(self):
        self.Hide()
        self.text = None


class Panel(ui.Window):
    def __init__(self, width, height, title, icon, close_event=None):
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.SetSize(width, height)
        self.children = []
        self.close_event = close_event
        self.chrome = CrimsonWindowChrome(False)
        self.chrome.SetParent(self)
        self.chrome.AddFlag('not_pick')
        self.chrome.SetChromeSize(width, height)
        self.chrome.body_fill.SetDiffuseColor(1, 1, 1, .96)
        self.top_line = ui.Bar()
        self.top_line.SetParent(self)
        self.top_line.AddFlag('not_pick')
        self.top_line.SetSize(width, 1)
        self.top_line.SetColor(grp.GenerateColor(.47, .38, .27, 1))
        self.top_line.Show()
        self.title_icon = ui.ImageBox()
        self.title_icon.SetParent(self)
        self.title_icon.AddFlag('not_pick')
        self.title_icon.LoadImage(ICON_ROOT + ICONS[icon])
        self.title_icon.SetPosition(9, 6)
        self.title_icon.Show()
        self.title = label(self, 35, 10, title, 12, GOLD)
        self.close = IconControl(self, width-27, 3, 'close', 'Zavřít panel', close_event or ui.__mem_func__(self.Hide))

    def OnRender(self):
        if getattr(self, 'r1', None):
            return
        x, y = self.GetGlobalPosition()
        bar(x, y, self.GetWidth(), 1, (.47, .38, .27))

    def Clear(self):
        for child in self.children:
            child.Hide()
            if hasattr(child, 'Destroy'):
                child.Destroy()
        self.children = []

    def Hide(self):
        for child in getattr(self, 'children', ()):
            if isinstance(child, Input) and child.edit:
                child.edit.KillFocus()
            if hasattr(child, 'OnMouseOverOut'):
                child.OnMouseOverOut()
            if isinstance(child, DropDown):
                child.CloseMenu()
        ui.Window.Hide(self)

    def OnPressEscapeKey(self):
        if self.close_event:
            self.close_event()
        else:
            self.Hide()
        return True

    def Destroy(self):
        self.Hide()
        self.Clear()
        self.close.Destroy()
        if getattr(self, 'r1', None):
            self.r1.Destroy()
            self.r1 = None
        self.title = None
        self.title_icon = None
        self.chrome = None
        self.top_line = None
        self.close_event = None


class Input(ui.Window):
    def __init__(self, parent, x, y, width, text='', max_length=76, height=25):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetSize(width, height)
        self.edit = ui.EditLine()
        self.edit.SetParent(self)
        self.edit.SetPosition(7, 5)
        self.edit.SetSize(width-14, height-10)
        self.edit.SetFontName('Tahoma:12')
        self.edit.SetMax(512)
        self.edit.SetUserMax(max_length)
        self.edit.SetText(text)
        self.edit.Show()
        self.Show()

    def OnRender(self):
        x, y = self.GetGlobalPosition()
        ui.RenderRoundBox(x, y, self.GetWidth(), self.GetHeight(), grp.GenerateColor(.40, .33, .25, 1))

    def Hide(self):
        if getattr(self, 'edit', None):
            self.edit.KillFocus()
        ui.Window.Hide(self)

    def Destroy(self):
        self.Hide()
        self.edit = None
