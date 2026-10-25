# -*- coding: utf-8 -*-
"""Rychlá aktivace (uiquickbuff.QuickBuffWindow, 408 x 445) in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md),
drawn INTO the original window. The size, the rows, the 8 x 5 item grid (pitch 45 x 50), every handler and every
function stay:

* the R1 frame and the red R1 header (the title in Cinzel, the vein, the plain X) over the board; the original title
  bar stays as the invisible drag handle;
* the profile PVM / PVP as an R1 switch: the chosen profile is shown by brightness only (a lighter well, ivory label),
  the other one is dimmed - never a red underline; a click runs the window's own _SelectProfile;
* the item grid in a dark R1 panel with a thin outline, every slot the R1 item slot C (native 32 x 32);
* the check box under each filled slot and "Auto VIP" as R1 check boxes (a glowing red tick); the window keeps
  driving them through adapters that stand in for the original toggle buttons (Show / Hide / Down / SetUp);
* the texts in Noto Sans (the hint and the count dimmed, the status green / calm gold / grey by its state);
* "Aktivovat buffy" (primary) and "Vymazat" as R1 buttons calling the original handlers.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window; a failure while building traces to
syserr (uir1.TraceFailure), the original look comes back and R1 is not tried again in this session.
"""
from weakref import proxy

import ui

import uir1
import uir1layout as L
import uir1skin
import uir1tokens as T

LEFT, RIGHT = 18, 390                   # the panel, the rows and the buttons share these edges (18 px side margins)
HINT_Y = 34
PROFILE_Y = 56                          # the profile row (24 px: the switch, the label and the count centred in it)
CAPTION_Y = 88
PANEL = (LEFT, 108, RIGHT - LEFT, 256)  # the item grid panel (x, y, w, h)
GRID_AT = (12, 4)                       # the grid inside the panel: 7 * 45 + 32 = 347 px of slots, 12 / 13 px sides
VIP_Y = PANEL[1] + PANEL[3] + 8
RULE_Y = VIP_Y + 25
BUTTON_Y = RULE_Y + 8
ACTIVATE_W, CLEAR_W = 180, 96
SWITCH_CELL_W = 56
LABEL_GAP = 12
ACTIVE = 0xFF5FC45A                     # "Auto VIP je aktivní": the positive green of the R1 windows
WAITING = 0xFFE8C77A                    # "Auto VIP čeká na nasazené VIP": the calm gold of R1 values
PANEL_FILL = 0xFF0C0B0C
ORIGINAL_SLOT = 'd:/ymir work/ui/public/Slot_Base.sub'
ORIGINAL_FILL = 0x990b0807              # uiquickbuff: the grid background bar


def Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


class SwitchCell(uir1.Interactive):
    """One cell of the profile switch: the R1 segment well and the label. The chosen one = a lighter well and the
    ivory label, the other one is dimmed (brightness only, no red line)."""

    def __init__(self, switch, index, pos, value, label):
        uir1.Interactive.__init__(self)
        self.SetParent(switch)
        self.switch, self.index, self.pos, self.value = switch, index, pos, value
        self.selected = False
        self.w = 0
        self.art = 'normal'
        self.ops = uir1.Ops(self, L.segment_cell(pos, 'normal', 16))         # the well before the label
        self.label = uir1.Text(self, label, 0, 0, switch.font, Signed(T.MUTED), align='center', valign='top')
        self.Show()

    def Place(self, x, w):
        self.w = int(w)
        self.SetPosition(int(x), 0)
        self.SetSize(self.w, T.SEG_H)
        self.label.SetPosition(self.w // 2, uir1.CellTop(T.SEG_H, self.switch.font))
        self.paint()

    def paint(self):
        if not self.w:
            return
        if not self.enabled:
            art, color = 'disabled', T.DISABLED
        elif self.selected:
            art, color = 'hover', T.IVORY
        elif self.hovered:
            art, color = 'normal', T.INK
        else:
            art, color = 'normal', T.MUTED
        self.art = art
        self.ops.Apply(L.segment_cell(self.pos, art, self.w))
        self.label.SetPackedFontColor(Signed(color))

    def click(self):
        self.switch.Select(self.index)


class ProfileSwitch(ui.Window):
    """PVM / PVP: ``options`` = [(value, label)], event(value) on a click, SetValue(value) shows the chosen one."""

    def __init__(self, parent, kit, x, y, options, event=None):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.font = kit.font('text_s')
        self.values = [value for value, unused in options]
        self.callback = event
        n = len(options)
        self.cells = []
        for index, (value, label) in enumerate(options):
            pos = 'single' if n == 1 else ('first' if index == 0 else ('last' if index == n - 1 else 'mid'))
            cell = SwitchCell(self, index, pos, value, label)
            cell.Place(index * SWITCH_CELL_W, SWITCH_CELL_W)
            self.cells.append(cell)
        self.width = n * SWITCH_CELL_W
        self.SetPosition(int(x), int(y))
        self.SetSize(self.width, T.SEG_H)
        self.Show()

    def Width(self):
        return self.width

    def SetValue(self, value):
        for cell in self.cells:
            selected = cell.value == value
            if selected != cell.selected:
                cell.selected = selected
                cell.paint()

    def Select(self, index):
        if self.callback:
            self.callback(self.values[index])


class ProfileAdapter(object):
    """Stands in for the window's profilePvm / profilePvp (ui.RadioButton): the window's Down() shows the profile on the
    R1 switch, SetUp() needs nothing (the other profile's Down() takes the brightness away)."""

    def __init__(self, switch, value, original):
        self.switch, self.value, self.original = switch, value, original

    def Down(self):
        self.switch.SetValue(self.value)

    def SetUp(self):
        pass

    def IsDown(self):
        return self.switch.cells[self.switch.values.index(self.value)].selected

    def __getattr__(self, name):
        return getattr(self.original, name)


class CheckAdapter(object):
    """Stands in for one original toggle button of the window (a slot check box, Auto VIP): the window's Show / Hide /
    Down / SetUp drive the R1 check box; a click on it goes through the skin to the window's own handlers."""

    def __init__(self, check, original):
        self.check, self.original = check, original

    def Show(self):
        self.check.Show()

    def Hide(self):
        self.check.Hide()

    def IsShow(self):
        return self.check.IsShow()

    def Down(self):
        self.check.SetOn(True)

    def SetUp(self):
        self.check.SetOn(False)

    def IsDown(self):
        return self.check.IsOn()

    def __getattr__(self, name):
        return getattr(self.original, name)


class QuickBuffSkin(object):
    """R1 into one QuickBuffWindow (after its constructor built the original controls)."""

    def __init__(self, window):
        self.window = window
        self.kit = kit = uir1.Kit()
        self.rec = rec = uir1skin.Recorder()
        self.skin = None
        self.switch = self.vip = self.activate = self.clear = None
        self.widgets = []
        self.checks = []
        self.original_checks = list(window.checkboxes)
        self.originals = {}                     # attribute of the window -> the original object it holds again later
        try:
            self.skin = uir1.BoardSkin(window, kit, window.titleName.GetText(), on_close=ui.__mem_func__(window.Close))
            self._Texts()
            self._Panel()
            self._Profile()
            self._Checks()
            self._Footer()
        except Exception:
            self.Restore()
            raise

    # ------------------------------------------------------------------ build
    def _Fit(self, line, width):
        """The line shortened to ``width`` px (the original text comes back with Undo)."""
        text = line.GetText()
        self.rec.Call(lambda: uir1.Fit(line, text, width), lambda: line.SetText(text))

    def _Texts(self):
        import uiquickbuff as original
        window, rec, kit = self.window, self.rec, self.kit
        small, bold = kit.font('text_s'), kit.font('text_sb')
        rec.Font(window.hintText, small, Signed(T.MUTED), None, Signed(original.MUTED_COLOR))
        rec.Position(window.hintText, LEFT, HINT_Y)
        self._Fit(window.hintText, RIGHT - LEFT)
        rec.Font(window.profileLabel, bold, Signed(T.INK_DIM), None, Signed(original.GOLD_COLOR))
        rec.Position(window.profileLabel, LEFT, PROFILE_Y + uir1.CellTop(T.SEG_H, bold))
        rec.Font(window.itemsLabel, bold, Signed(T.INK_DIM), None, Signed(original.GOLD_COLOR))
        rec.Position(window.itemsLabel, LEFT, CAPTION_Y)
        count = window.selectionCount
        rec.Font(count, small, Signed(T.INK_DIM), None, Signed(original.TEXT_COLOR))
        rec.Position(count, RIGHT, PROFILE_Y + uir1.CellTop(T.SEG_H, small))
        rec.Call(count.SetHorizontalAlignRight, count.SetHorizontalAlignCenter)
        rec.Hide(window.autoVipLabel)                     # the R1 check box carries the label
        status = window.statusText
        rec.Font(status, small, Signed(T.MUTED), None, Signed(original.MUTED_COLOR))
        rec.Position(status, RIGHT, VIP_Y + uir1.CellTop(max(T.CHECK, uir1.FontCell(kit.font('text'))), small))
        rec.Call(status.SetHorizontalAlignRight, status.SetHorizontalAlignCenter)
        colors = {Signed(original.MUTED_COLOR): T.MUTED, Signed(original.GOLD_COLOR): WAITING,
                  Signed(original.ACTIVE_COLOR): ACTIVE}
        set_color, set_text = status.SetPackedFontColor, status.SetText
        limit = RIGHT - LEFT - 110

        def SetPackedFontColor(color):
            set_color(Signed(colors.get(Signed(color), color)))

        fitting = []

        def SetText(text):
            if fitting:                       # uir1.Fit sets the shortened text through this very line
                return set_text(text)
            fitting.append(True)
            try:
                uir1.Fit(status, text, limit)
            finally:
                fitting.pop()

        def undo():
            for name in ('SetPackedFontColor', 'SetText'):
                status.__dict__.pop(name, None)
        rec.Call(lambda: (setattr(status, 'SetPackedFontColor', SetPackedFontColor),
                          setattr(status, 'SetText', SetText)), undo)

    def _Panel(self):
        window, rec = self.window, self.rec
        x, y, w, h = PANEL
        back = window.gridBackground
        rec.Position(back, x, y)
        rec.Size(back, w, h)
        rec.Call(lambda: back.SetColor(uir1.GenerateColor(PANEL_FILL, 1.0)), lambda: back.SetColor(ORIGINAL_FILL))
        rec.Position(window.grid, *GRID_AT)
        rec.SlotBase(window.grid, uir1.SlotBase(), ORIGINAL_SLOT)
        for line in window.borderLines:
            rec.Hide(line)
        self.widgets.append(uir1.Frame(window, x, y, w, h, 'panel', bg=None))     # the outline above the content
        self.widgets.append(uir1.Divider(window, LEFT, RULE_Y, RIGHT - LEFT))

    def _Profile(self):
        window, rec, kit = self.window, self.rec, self.kit
        text = dict((name, getattr(window, name).GetText() or default)
                    for name, default in (('profilePvm', 'PVM'), ('profilePvp', 'PVP')))
        x = LEFT + uir1.TextWidth(window.profileLabel) + LABEL_GAP
        self.switch = ProfileSwitch(window, kit, x, PROFILE_Y,
                                    [('pvm', text['profilePvm']), ('pvp', text['profilePvp'])],
                                    event=ui.__mem_func__(window._SelectProfile))
        self.widgets.append(self.switch)
        for name, value in (('profilePvm', 'pvm'), ('profilePvp', 'pvp')):
            button = getattr(window, name)
            rec.Hide(button)
            self._Swap(name, ProfileAdapter(self.switch, value, button))
        self.switch.SetValue(window.system.model.active_profile if window.system else 'pvm')

    def _Swap(self, name, adapter):
        self.originals.setdefault(name, getattr(self.window, name))
        setattr(self.window, name, adapter)

    def _Checks(self):
        window, rec, kit = self.window, self.rec, self.kit
        skin = proxy(self)
        for index, original in enumerate(self.original_checks):
            x, y = original.GetLocalPosition()
            rec.Hide(original)
            check = uir1.CheckBox(window.grid, kit, x, y, event=lambda index=index: skin._ClickSlot(index))
            check.Hide()                                  # the window shows it with the filled slot (RefreshSlots)
            self.checks.append(check)
            self.widgets.append(check)
            window.checkboxes[index] = CheckAdapter(check, original)
        original = window.autoVip
        rec.Hide(original)
        self.vip = uir1.CheckBox(window, kit, LEFT, VIP_Y, window.autoVipLabel.GetText(),
                                 on=bool(window.system and window.system.model.auto_enabled),
                                 event=lambda: skin._ClickAutoVip(), font=kit.font('text'), color=Signed(T.INK))
        self.widgets.append(self.vip)
        self._Swap('autoVip', CheckAdapter(self.vip, original))

    def _Footer(self):
        window, rec, kit = self.window, self.rec, self.kit
        skin = proxy(self)
        rec.Hide(window.activateButton)
        rec.Hide(window.clearButton)
        self.activate = uir1.Button(window, kit, LEFT, BUTTON_Y, ACTIVATE_W, window.activateButton.GetText(),
                                    primary=True, event=lambda: skin._Activate())
        self.clear = uir1.Button(window, kit, RIGHT - CLEAR_W, BUTTON_Y, CLEAR_W, window.clearButton.GetText(),
                                 event=lambda: skin._Clear())
        self.widgets += [self.activate, self.clear]

    # ------------------------------------------------------------------ the original handlers
    def _ClickSlot(self, index):
        window = self.window
        if window is not None:
            window._SetSlotEnabled(index, not self.checks[index].IsOn())

    def _ClickAutoVip(self):
        window = self.window
        if window is not None:
            window._SetAutoVip(not self.vip.IsOn())
            window.Refresh()

    def _Activate(self):
        window = self.window
        if window is not None and window.system is not None:
            window.system.Activate()

    def _Clear(self):
        window = self.window
        if window is not None:
            window._ClearProfile()

    # ------------------------------------------------------------------ restore
    def Restore(self):
        window = self.window
        if window is None:
            return
        self.window = None
        for name, original in self.originals.items():
            setattr(window, name, original)
        self.originals = {}
        for index, original in enumerate(self.original_checks):
            if index < len(window.checkboxes):
                window.checkboxes[index] = original
        self.checks = []
        uir1skin.Destroy(self.widgets)
        self.widgets = []
        self.switch = self.vip = self.activate = self.clear = None
        self.rec.Undo()
        if self.skin is not None:
            self.skin.Restore()
            self.skin.Destroy()
        self.skin = None
        try:
            window.Refresh()                  # the original toggles and the profile buttons show the model again
        except Exception:
            pass

    Destroy = Restore
