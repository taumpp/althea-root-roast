# -*- coding: utf-8 -*-
"""The compact chat and its panels ("Nastavení chatu" and the others) in the Althea R1 look (docs/ALTHEA_R1_KIT.md).

uicompactchat.ChatWindow stays the window and keeps every function (header filters and custom tabs, the message
view with scrolling, links and tooltips, the channel switch, emoticons, sending, Messenger, history, repeated
shouts, moving and resizing, the passive preview). This module only draws it in R1:

* the chat itself stays as it is (header, message area, messages in Tahoma); the bottom row is one 26 px line:
  the channel ("Okolí" and a down chevron) as its own button left of the field (it opens the channel choice as
  before and shows the current channel), the R1 field around the native chat line (the 24 px kit field centred
  in the row, the vein while it has the focus), then the four original icons as 26 px R1 buttons - sending is the
  primary one (the vein along its bottom edge);
* the message view (and the detached histories) scroll with the narrow R1 scroll bar;
* every panel (Nastavení chatu, Odesílat do, Emotikony, Opakované zprávy, Vlastní záložky, Přidat záložku, the
  histories) has the R1 frame: no bar, the title in Cinzel with the vein and the plain X; inside, the panels use
  R1 controls: tabs as a segment, check boxes with the red tick, buttons, fields, the font size choice, the
  opacity sliders and section headings (Controls is the R1 counterpart of the uicompactchatcontrols factories).

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original chat. When building the R1 look raises, the
chat traces it (syserr), drops the R1 parts and goes on in the original look (no retry until the next start).
"""
import ui

import uir1
import uir1layout as L
import uir1tokens as T
import uicompactchatcontrols as controls

ROW_H = 26                   # the bottom row: channel button, field, icon buttons
CHANNEL_W = 74
GAP = 4
ICON_W = 26
ICON_STEP = 27
ICONS_RIGHT = 114            # the first icon starts this far from the right window edge
ROW_INSET = 6                # the row starts this far from the left window edge
FIELD_RIGHT = 120            # the field ends this far from the right window edge
SCROLL_INSET = 9             # the scroll bar's left edge from the right edge of the message view
ICON_KEYS = ('emoji', 'send', 'pm', 'history')
SLIDER_TRACK = 123           # opacity slider: track + knob end 13 px inside the 322 px settings panel
FAILED = []                  # a failed R1 build: the original look until the next start


def UseR1():
    """The R1 chat unless Settings -> "Starý vzhled" chose the original look or R1 failed in this session."""
    return not FAILED and uir1.UseR1()


def _Packed(rgb):
    known = {controls.DIM: T.INK_DIM, controls.GOLD: T.IVORY, controls.INK: T.INK}
    if rgb in known:
        return known[rgb]
    r, g, b = [max(0, min(255, int(round(c * 255)))) for c in rgb]
    return 0xFF000000 | (r << 16) | (g << 8) | b


# --------------------------------------------------------------------------- controls
class _Tip(object):
    """The tooltip of the original chat controls for an R1 control: the one R1 hint above the control (it was an item
    tooltip under the mouse). A uir1.Button shows its ``tooltip`` itself (uir1.Button.OnMouseOverIn): the hint is
    shown once, by ONE source (never two boxes on one control)."""
    tooltip = ''

    def _OwnHint(self):
        return not isinstance(self, uir1.Button)

    def OnMouseOverIn(self):
        super(_Tip, self).OnMouseOverIn()
        if self.tooltip and self._OwnHint():
            uir1.ShowHint(None, self, self.tooltip)

    def OnMouseOverOut(self):
        super(_Tip, self).OnMouseOverOut()
        if self.tooltip and self._OwnHint():
            uir1.HideHint(self)

    def SetEnabled(self, value):
        self.Enable() if value else self.Disable()

    def Hide(self):
        # ui.Window.__init__ calls Hide() before the control has its state (enabled, images): nothing to reset then.
        if 'enabled' in self.__dict__:
            self.OnMouseOverOut()
        ui.Window.Hide(self)

    def Destroy(self):
        self.Hide()
        self.callback = None


class TextButton(_Tip, uir1.Button):
    """R1 secondary button (22 px) with the API of uicompactchatcontrols.text_button; selected = the primary plate
    (the vein along the bottom edge). The label is a top-aligned line centred by its position (uir1.RowText): the
    engine clips a text line as if it ran from its y down by the text height, so the whole cell stays inside."""

    def __init__(self, parent, kit, x, y, width, text, tooltip, event):
        self.label_font = kit.font('text_s')
        uir1.Button.__init__(self, parent, kit, x, y, width, '', small=True, event=event)
        self.text = uir1.RowText(self, '', width // 2, self.h, self.label_font, T.BUTTON_TEXT, align='center')
        self.SetText(text)
        self.tooltip = tooltip
        self.selected = False
        self.icon = None
        self.check = None
        self.paint()

    def SetText(self, value):
        self.text.SetText(value)

    def GetText(self):
        return self.text.GetText()

    def paint(self):
        uir1.Button.paint(self)
        text = getattr(self, 'text', None)
        if text is not None:
            state = self.state()
            text.SetPackedFontColor(T.DISABLED if state == 'disabled' else
                                    (T.PRIMARY_TEXT if self.primary else T.BUTTON_TEXT))
            text.SetPosition(self.w // 2, uir1.CellTop(self.h, self.label_font) + (1 if self.pressed else 0))

    def SetSelected(self, value):
        self.selected = bool(value)
        if self.primary != self.selected:
            self.primary = self.selected
            self.paint()


class IconButton(_Tip, uir1.Button):
    """26 px R1 button with an original chat icon (20 px) in the middle; send is the primary one."""

    def __init__(self, parent, kit, key, tooltip, event, primary=False):
        uir1.Button.__init__(self, parent, kit, 0, 0, ICON_W, '', primary=primary, event=event)
        self.key = key
        self.tooltip = tooltip
        self.icon = ui.ImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.LoadImage(controls.ICON_ROOT + controls.ICONS[key])
        self.icon.SetPosition((ICON_W - 20) // 2, (ROW_H - 20) // 2)
        self.icon.Show()
        self.text = None
        self.check = None

    def paint(self):
        uir1.Button.paint(self)
        icon = getattr(self, 'icon', None)
        if icon is not None:
            icon.SetPosition((ICON_W - 20) // 2, (ROW_H - 20) // 2 + (1 if self.pressed else 0))


class ChannelButton(_Tip, uir1.Button):
    """The sending channel as its own button left of the field: the channel name on the left, a down chevron on
    the right; a click opens the channel choice. API of the original CompactInput.mode (text, SetText)."""

    def __init__(self, parent, kit, name, tooltip, event):
        uir1.Button.__init__(self, parent, kit, 0, 0, CHANNEL_W, '', event=event)
        self.tooltip = tooltip
        self.font = kit.font('text_s')
        self.text = uir1.RowText(self, '', 8, ROW_H, self.font, T.BUTTON_TEXT)
        self.chevron = uir1.Image(self, uir1.ChevronPath('down'), CHANNEL_W - 8 - T.CHEVRON,
                                  (ROW_H - T.CHEVRON) // 2)
        self.SetText(name)

    def SetText(self, value):
        uir1.Fit(self.text, value, CHANNEL_W - 8 - T.CHEVRON - 12)
        self.name = value

    def paint(self):
        if getattr(self, 'ops', None) is None:      # not built yet (native Hide / mouse event during __init__)
            return
        uir1.Button.paint(self)
        state = self.state()
        text = getattr(self, 'text', None)
        if text is not None:
            text.SetPackedFontColor(T.DISABLED if state == 'disabled' else
                                    (T.IVORY if state in ('hover', 'pressed') else T.BUTTON_TEXT))
            text.SetPosition(8, uir1.CellTop(ROW_H, self.font) + (1 if self.pressed else 0))
        chevron = getattr(self, 'chevron', None)
        if chevron is not None:
            chevron.LoadImage(uir1.ROOT + uir1.ChevronPath('down', {'pressed': 'active'}.get(state, state)))


class Check(_Tip, uir1.CheckBox):
    """R1 check box with the API of uicompactchatcontrols.checkbox (.check, .tooltip, .text, SetEnabled)."""

    def __init__(self, parent, kit, x, y, width, text, checked, event):
        uir1.CheckBox.__init__(self, parent, kit, x, y, '', on=checked, event=event)
        # The label as a top-aligned line at CellTop of the box row (uir1.RowText), the box centred beside it.
        font = kit.font('text')
        s = T.CHECK
        self.h = max(s, uir1.FontCell(font))
        self.label = uir1.RowText(self, text, s + 7, self.h, font, self.color)
        self.w = s + 7 + uir1.TextWidth(self.label)
        self.box.SetPosition(0, (self.h - s) // 2)
        self.SetSize(self.w, self.h)
        self.SetPosition(x, y + max(0, (22 - self.h) // 2))
        self.tooltip = 'Zobrazí nebo skryje: ' + text
        self.text = self.label
        self.icon = None
        self.paint()

    @property
    def check(self):
        return self.on

    @check.setter
    def check(self, value):
        self.SetOn(value)


class Input(controls.Input):
    """R1 edit field with the API of uicompactchatcontrols.Input (.edit): the 24 px kit field for one line, a dark
    panel well for a taller multi-line field."""

    def __init__(self, parent, kit, x, y, width, text='', max_length=76, height=25):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetSize(width, height)
        self.field = None
        self.well = None
        if height <= T.FIELD_H + 2:
            self.field = uir1.Field(self, kit, 0, (height - T.FIELD_H) // 2, width, max_len=512)
            self.edit = self.field.edit
        else:
            self.well = uir1.Frame(self, 0, 0, width, height, 'panel')
            self.edit = ui.EditLine()
            self.edit.SetParent(self)
            self.edit.SetPosition(8, 6)
            self.edit.SetSize(width - 16, height - 12)
            self.edit.SetMax(512)
            uir1.SetFont(self.edit, kit.font('text_s'), '')
            self.edit.Show()
        self.edit.SetUserMax(max_length)
        self.edit.SetText(text)
        self.Show()

    def OnRender(self):
        pass

    def Destroy(self):
        controls.Input.Destroy(self)
        self.field = None
        self.well = None


class DropDown(controls.DropDown):
    """The font size choice in R1: a secondary 22 px button with the value and a down chevron; the list opens in an
    R1 tooltip frame of 22 px R1 buttons (the selected one with the vein)."""

    def __init__(self, parent, kit, x, y, width, options, value, changed):
        ui.Window.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetSize(width, L.button_height(True))
        self.tip = None
        self.tooltip = 'Vybrat velikost písma.'
        self.event = ui.__mem_func__(self.Toggle)
        self.hover = self.pressed = self.selected = self.running = self.repeat_icon = False
        self.enabled = True
        self.check = None
        self.icon = None
        self.options = list(options)
        self.changed = changed
        self.menu = None
        self.plate = uir1.Ops(self, L.button(False, True, 'normal', width))      # images before the texts
        self.text = uir1.RowText(self, '', width // 2 - 6, self.GetHeight(), kit.font('text_s'), T.BUTTON_TEXT,
                                 align='center')
        self.chevron = uir1.Image(self, uir1.ChevronPath('down'), width - 8 - T.CHEVRON,
                                  (self.GetHeight() - T.CHEVRON) // 2)
        self.Paint()
        self.SetValue(value)
        self.Show()

    def Paint(self):
        state = 'pressed' if self.pressed else ('hover' if self.hover else 'normal')
        self.plate.Apply(L.button(False, True, state, self.GetWidth()))

    def OnMouseOverIn(self):
        controls.DropDown.OnMouseOverIn(self)
        self.Paint()

    def OnMouseOverOut(self):
        controls.DropDown.OnMouseOverOut(self)
        if getattr(self, 'plate', None):
            self.Paint()

    def OnMouseLeftButtonDown(self):
        controls.DropDown.OnMouseLeftButtonDown(self)
        self.Paint()
        return True

    def OnMouseLeftButtonUp(self):
        controls.DropDown.OnMouseLeftButtonUp(self)
        if getattr(self, 'plate', None):
            self.Paint()
        return True

    def Toggle(self):
        if self.menu:
            self.CloseMenu()
            return
        step, pad = L.button_height(True) + 2, 4
        self.menu = ui.Window('TOP_MOST')
        self.menu.SetSize(self.GetWidth(), len(self.options) * step + 2 * pad - 2)
        self.menu.fill = uir1.Frame(self.menu, 0, 0, self.menu.GetWidth(), self.menu.GetHeight(), 'tooltip',
                                    fill_alpha=uir1.MENU_FILL_ALPHA)      # a menu, no tooltip: near opaque
        self.menu.options = []
        for index, (value, text) in enumerate(self.options):
            button = TextButton(self.menu, self.kit, pad, pad + index * step, self.GetWidth() - 2 * pad, text,
                                'Změna se projeví ihned.', lambda value=value: self.Select(value))
            button.SetSelected(value == self.value)
            self.menu.options.append(button)
        x, y = self.GetGlobalPosition()
        self.menu.SetPosition(x, y + self.GetHeight())
        self.OnUpdate()
        self.menu.Show()
        self.menu.SetTop()

    def OnRender(self):
        pass

    def Destroy(self):
        controls.DropDown.Destroy(self)
        self.plate = None


class Controls(object):
    """R1 counterparts of the uicompactchatcontrols factories (same signatures), used for the panel contents."""

    def __init__(self, kit):
        self.kit = kit

    def label(self, parent, x, y, value='', size=12, color=controls.INK):
        # The original Tahoma line's middle (y + 6 / y + 7) as the middle of the R1 cell, the line top-aligned.
        font = self.kit.font('text_s' if size <= 11 else 'text')
        top = y + (6 if size <= 11 else 7) - uir1.FontCell(font) // 2
        return uir1.Text(parent, value, x, top, font, _Packed(color), valign='top')

    def text_button(self, parent, x, y, width, text, tooltip, event):
        return TextButton(parent, self.kit, x, y, width, text, tooltip, event)

    def checkbox(self, parent, x, y, width, text, checked, event):
        return Check(parent, self.kit, x, y, width, text, checked, event)

    def Input(self, parent, x, y, width, text='', max_length=76, height=25):
        return Input(parent, self.kit, x, y, width, text, max_length, height)

    def DropDown(self, parent, x, y, width, options, value, changed):
        return DropDown(parent, self.kit, x, y, width, options, value, changed)

    def section(self, parent, x, y, width, text):
        return uir1.Section(parent, self.kit, x, y - 2, width, text)

    def tabs(self, parent, titles, selected, make_event, tooltip):
        segment = uir1.Segment(parent, self.kit, [(title, title) for title in titles],
                               lambda title: make_event(title)(), font=self.kit.font('text_s'),
                               width=parent.GetWidth() - 2 * T.PAD)
        segment.SetPosition(T.PAD, 33)
        font = self.kit.font('text_s')
        for cell in segment.cells:
            # The kit cell centres its label vertically; the panel keeps a top-aligned line at CellTop instead.
            old = cell.label
            old.Hide()
            cell.label = uir1.RowText(cell, old.GetText(), cell.w // 2, T.SEG_H, font, T.INK_DIM, align='center')
            cell.label.SetPosition(cell.w // 2, uir1.CellTop(T.SEG_H, font) - 1)
            cell.paint()
        segment.SetValue(selected)
        return [segment]

    def slider(self, parent, x, y, position, event):
        control = uir1.Slider(parent, self.kit, x, y, SLIDER_TRACK, event)
        control.SetSliderPos(position)
        return control

    def divider(self, parent, x, y, width):
        return uir1.Divider(parent, x, y, width)


# --------------------------------------------------------------------------- the chat window
class ChatSkin(object):
    """The R1 parts of one ChatWindow. Build raises after undoing itself, so the owner keeps the original look."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.controls = Controls(self.kit)
        self.views = []
        self.panels = []
        self.legacy_buttons = None
        self.legacy_mode = None
        self.buttons = []
        self.channel = None
        self.well = None
        self.focused = None
        try:
            self._Build()
        except Exception:
            self.Undress()
            raise

    def _Build(self):
        window = self.window
        inp = window.chatInputSet
        self.DressView(window.view)
        # Channel button and the field well under the chat line: the line is re-parented after them so the engine
        # draws it (and its placeholder) above the well (a window joins the END of its new parent's children).
        self.legacy_mode = inp.mode
        inp.mode.Hide()
        self.channel = ChannelButton(inp, self.kit, inp.mode.text.GetText() or 'Okolí',
                                     'Vybrat kanál odesílání. Horní filtry se nezmění.',
                                     ui.__mem_func__(window.OpenChannels))
        self.well = uir1.Ops(inp, L.field('normal', 64))
        line = inp.chatLine
        line.SetParent(window)
        line.SetParent(inp)
        back = getattr(line, 'backText', None)
        if back is not None:
            uir1.SetFont(back, self.kit.font('text_s'))
            back.SetPackedFontColor(T.MUTED)
        inp.mode = self.channel
        inp.r1 = self
        tips = dict((key, button.tooltip) for key, button in zip(ICON_KEYS, window.buttons))
        events = dict((key, button.event) for key, button in zip(ICON_KEYS, window.buttons))
        self.legacy_buttons = list(window.buttons)
        for button in self.legacy_buttons:
            button.Hide()
        self.buttons = [IconButton(window, self.kit, key, tips[key], events[key], primary=key == 'send')
                        for key in ICON_KEYS]
        window.buttons = list(self.buttons)

    # ------------------------------------------------------------------ message views
    def DressView(self, view):
        old = view.scroll
        bar = uir1.ScrollBar(self.kit)
        bar.SetParent(view)
        bar.SetPosition(view.GetWidth() - SCROLL_INSET, 0)
        bar.SetScrollBarSize(view.GetHeight())
        bar.SetScrollEvent(ui.__mem_func__(view.OnScroll))
        bar.SetScrollStep(.12)
        bar.Hide()
        if old.IsShow():
            old.Hide()
            bar.Show()
        view.legacy_scroll = old
        view.scroll = bar
        view.scroll_inset = SCROLL_INSET
        view.layout_key = None
        self.views.append(view)

    def _UndressView(self, view):
        old = getattr(view, 'legacy_scroll', None)
        if old is None:
            return
        if view.scroll is not old:
            view.scroll.Hide()
            view.scroll.Destroy()
        view.scroll = old
        view.legacy_scroll = None
        view.scroll_inset = 12
        old.SetPosition(view.GetWidth() - 12, 0)
        view.layout_key = None

    # ------------------------------------------------------------------ panels
    def DressPanel(self, panel):
        """The R1 frame of a controls.Panel, before its content is added: the original chrome, line, icon, title
        and cross are hidden (kept for Destroy), the header's X runs the panel's close event."""
        for widget in (panel.chrome, panel.top_line, panel.title_icon, panel.title, panel.close):
            widget.Hide()
        close = panel.close.event or panel.Hide
        panel.r1 = uir1.Chrome(panel, self.kit, panel.GetWidth(), panel.GetHeight(), panel.title.GetText(),
                               on_close=close)
        self.panels.append(panel)
        return panel

    # ------------------------------------------------------------------ layout
    def Layout(self, width, height):
        """Bottom row of the edit mode: channel + field inside the input set, the icon buttons on the window."""
        inp = self.window.chatInputSet
        y = height - 32
        inp.SetPosition(ROW_INSET, y)
        inp.SetSize(width - FIELD_RIGHT - ROW_INSET, ROW_H)
        self.channel.SetPosition(0, 0)
        field_x = CHANNEL_W + GAP
        field_w = max(40, width - FIELD_RIGHT - ROW_INSET - field_x)
        self.field_rect = (field_x, field_w)
        self.focused = None
        self.SyncInput()
        line = inp.chatLine
        line.SetPosition(field_x + 8, (ROW_H - 17) // 2 + 1)
        line.SetSize(field_w - 16, 17)
        line.x, line.y, line.width, line.height = line.GetRect()
        for index, button in enumerate(self.buttons):
            button.SetPosition(width - ICONS_RIGHT + index * ICON_STEP, y)

    def SyncInput(self):
        rect = getattr(self, 'field_rect', None)
        if not rect:
            return
        try:
            focused = bool(self.window.chatInputSet.chatLine.IsFocus())
        except Exception:
            focused = False
        if focused != self.focused:
            self.focused = focused
            x, w = rect
            self.well.Apply([(k, p, ox + x, oy + (ROW_H - T.FIELD_H) // 2, ow, oh)
                             for k, p, ox, oy, ow, oh in L.field('focus' if focused else 'normal', w)])

    # ------------------------------------------------------------------ undo
    def Undress(self):
        """Back to the original look (a failed build or a failure later in a panel)."""
        window = self.window
        inp = getattr(window, 'chatInputSet', None)
        if inp is not None:
            if self.legacy_mode is not None:
                inp.mode = self.legacy_mode
                inp.mode.Show()
            inp.r1 = None
            if self.channel is not None:
                self.channel.Destroy()
            if self.well is not None:
                self.well.Destroy()
            back = getattr(getattr(inp, 'chatLine', None), 'backText', None)
            if back is not None:
                uir1.SetFont(back, 'Tahoma:12')
                back.SetFontColor(*controls.DIM)
        if self.legacy_buttons is not None:
            for button in self.buttons:
                button.Destroy()
            window.buttons = self.legacy_buttons
        for view in self.views:
            self._UndressView(view)
        for panel in self.panels:
            if getattr(panel, 'r1', None):
                panel.r1.Destroy()
                panel.r1 = None
            for widget in (panel.chrome, panel.top_line, panel.title_icon, panel.title, panel.close):
                widget.Show()
        self.views, self.panels, self.buttons = [], [], []
        self.channel = self.well = self.legacy_mode = self.legacy_buttons = None
        self.field_rect = None

    def Destroy(self):
        for button in self.legacy_buttons or ():
            button.Destroy()
        if self.legacy_mode is not None:
            self.legacy_mode.Destroy()
        for view in self.views:
            old = getattr(view, 'legacy_scroll', None)
            if old is not None:
                old.Destroy()
                view.legacy_scroll = None
        self.views, self.panels = [], []
        self.legacy_buttons = self.legacy_mode = None
        self.window = None
