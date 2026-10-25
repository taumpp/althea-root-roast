# -*- coding: utf-8 -*-
"""Trvalé úkoly (uipermanenttasks.PermanentTasksWindow: Lov bossů / Lov meteorů) in the Althea R1 look
"Krvavá žíla" (docs/ALTHEA_R1_KIT.md, E:/althea-local-work/ui-navrhy-r1/PRAVIDLA-UI.md).

The window keeps its width (410), its flags (movable, float) and every function: the two hunt tabs, the 3D preview of
the next target, the stage, the target rows with their counters, the rewards of the stage with their item tooltips,
the passive bonus icon with its tooltip and the loading / unavailable / completed states. uipermanenttasks keeps all
of that logic; this module only draws it in R1:

* the R1 frame and the red R1 header (title, vein, plain X) on the window's own board (uir1.BoardSkin);
* the tabs as an R1 tab row with the original category icons: the selected tab is shown by brightness only (ivory
  label, full icon, a lighter well), the others are dimmed - never a red underline (PRAVIDLA-UI 3);
* the progress bars as R1 bars: a grey track and a dark blood red fill (Gauge);
* the reward slots and the passive bonus frame as the R1 item slot C (uir1.SLOT_CELL, native 32 x 32);
* the texts in Noto Sans and the R1 ink (the bonus keeps its green), the preview in a thin R1 panel outline;
* compact: the tabs sit right under the header, the content and the window are DY px shorter.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building or laying out
R1 restores the original look (traced to syserr) and R1 is not tried again in this session.
"""
import ui

import uir1
import uir1layout as L
import uir1tokens as T

WHAT = u'Trvalé úkoly'
TITLE = u'Trvalé úkoly'
TAB = (12, 32, 386)             # x, y, width of the tab row (24 px, right under the header)
PANEL_Y = 64                    # the preview and details panels (78 in the original)
DY = 78 - PANEL_Y               # the window is this much shorter
TAB_ICON = 'd:/ymir work/ui/game/crimson_ember/permanent_tasks/tab_%s_16.png'
TAB_ICON_SIZE = 16
TAB_ICON_GAP = 6
ORIGINAL_SLOT = 'd:/ymir work/ui/public/Slot_Base.sub'

# R1 progress bar: a grey track with a lighter grey outline, the dark blood red fill with a darker bottom row.
GAUGE_H = 6
TRACK_LINE = 0xFF4E4A4A
TRACK = 0xFF2E2B2B
FILL = 0xFF8C0B0D
FILL_DK = 0xFF4A0708
BONUS = 0xFFA6D69B              # the green of the original bonus line

_failed = set()


def Signed(color):
    """A packed colour for SetPackedFontColor: the x64 binding ignores values >= 0x80000000 (PRAVIDLA-UI, Kód)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color & 0x80000000 else color


def UseR1(what=WHAT):
    return what not in _failed and uir1.UseR1()


def Fail(what=WHAT):
    _failed.add(what)
    uir1.TraceFailure(what)


# --------------------------------------------------------------------------- shared R1 pieces (also uidailytasksr1)
class Gauge(ui.Window):
    """R1 progress bar with the API of ui.Gauge the task windows use (SetPercentage, SetPosition, Show / Hide): a grey
    track, the dark blood red fill from its start up to the value. Plain fills (ui.Bar): nothing is stretched."""

    def __init__(self, parent, x, y, w):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.w = max(4, int(w))
        self.SetSize(self.w, GAUGE_H)
        self.track = uir1.Rect(self, 0, 0, self.w, GAUGE_H, TRACK_LINE)
        self.inner = uir1.Rect(self, 1, 1, self.w - 2, GAUGE_H - 2, TRACK)
        self.fill = uir1.Rect(self, 1, 1, 1, GAUGE_H - 2, FILL)
        self.shade = uir1.Rect(self, 1, GAUGE_H - 2, 1, 1, FILL_DK)
        self.value, self.maximum, self.filled = 0, 1, 0
        self.SetPercentage(0, 1)
        self.Show()

    def MakeGauge(self, width, color=None):
        pass

    def SetPercentage(self, value, maximum):
        try:
            maximum = max(1, int(maximum))
            value = max(0, min(maximum, int(value)))
        except (TypeError, ValueError, OverflowError):
            value, maximum = 0, 1
        self.value, self.maximum = value, maximum
        self.filled = (self.w - 2) * value // maximum
        if self.filled > 0:
            self.fill.SetSize(self.filled, GAUGE_H - 2)
            self.shade.SetSize(self.filled, 1)
            self.fill.Show()
            self.shade.Show()
        else:
            self.fill.Hide()
            self.shade.Hide()


class TabCell(uir1.Interactive):
    """One tab: the R1 segment well, the original category icon and the label. Selected = a lighter well, the ivory
    label and the full icon; the others are dimmed (brightness only, no red line)."""

    def __init__(self, tabs, index, pos, value, label, icon):
        uir1.Interactive.__init__(self)
        self.SetParent(tabs)
        self.tabs, self.index, self.pos, self.value = tabs, index, pos, value
        self.selected = False
        self.w = 0
        self.ops = uir1.Ops(self, L.segment_cell(pos, 'normal', 16))         # the well before the icon and label
        self.icon = None
        if icon:
            self.icon = ui.ImageBox()
            self.icon.SetParent(self)
            self.icon.AddFlag('not_pick')
            self.icon.LoadImage(icon)
            self.icon.Show()
        self.label = uir1.Text(self, label, 0, 0, tabs.font, Signed(T.MUTED), valign='top')
        self.Show()

    def Place(self, x, w):
        self.w = int(w)
        self.SetPosition(int(x), 0)
        self.SetSize(self.w, T.SEG_H)
        icon_w = TAB_ICON_SIZE + TAB_ICON_GAP if self.icon is not None else 0
        left = (self.w - icon_w - uir1.TextWidth(self.label)) // 2
        if self.icon is not None:
            self.icon.SetPosition(left, (T.SEG_H - TAB_ICON_SIZE) // 2)
        self.label.SetPosition(left + icon_w, uir1.CellTop(T.SEG_H, self.tabs.font))
        self.paint()

    def paint(self):
        if not self.w:
            return
        if not self.enabled:
            art, color, alpha = 'disabled', T.DISABLED, 0.4
        elif self.selected:
            art, color, alpha = 'hover', T.IVORY, 1.0
        elif self.hovered:
            art, color, alpha = 'normal', T.INK, 0.85
        else:
            art, color, alpha = 'normal', T.MUTED, 0.55
        self.art = art
        self.ops.Apply(L.segment_cell(self.pos, art, self.w))
        self.label.SetPackedFontColor(Signed(color))
        if self.icon is not None:
            self.icon.SetAlpha(alpha)

    def click(self):
        self.tabs.Select(self.index)


class Tabs(ui.Window):
    """The tab row: ``options`` = [(value, label, icon path)], the cells share ``w``; event(value) on a click."""

    def __init__(self, parent, kit, x, y, w, options, event=None):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.kit = kit
        self.font = kit.font('text')
        self.values = [value for value, unused, unused in options]
        self.callback = event
        n = len(options)
        self.cells = []
        for index, (value, label, icon) in enumerate(options):
            pos = 'single' if n == 1 else ('first' if index == 0 else ('last' if index == n - 1 else 'mid'))
            self.cells.append(TabCell(self, index, pos, value, label, icon))
        base = int(w) // max(1, n)
        for index, cell in enumerate(self.cells):
            cell.Place(index * base, base if index < n - 1 else int(w) - base * (n - 1))
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), T.SEG_H)
        self.Show()

    def SetValue(self, value):
        for cell in self.cells:
            selected = cell.value == value
            if selected != cell.selected:
                cell.selected = selected
                cell.paint()

    def Select(self, index):
        if self.callback:
            self.callback(self.values[index])


class SkinBase(object):
    """Bookkeeping of a skin drawn into an original window: own widgets, replaced attributes (the window keeps driving
    the replacement), hidden originals, moved originals and changed images, all undone by Undo()."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.widgets = []
        self.swaps = []
        self.hidden = []
        self.moved = []
        self.reloads = []
        self.board = None

    def own(self, widget):
        self.widgets.append(widget)
        return widget

    def hide(self, widget):
        if widget is not None:
            self.hidden.append((widget, widget.IsShow()))
            widget.Hide()
        return widget

    def move(self, widget, x, y):
        self.moved.append((widget, widget.GetLocalPosition()))
        widget.SetPosition(int(x), int(y))

    def reload(self, restore, apply):
        """``apply()`` now, ``restore()`` in Undo (an image or a slot base set again)."""
        apply()
        self.reloads.append(restore)

    def swap(self, holder, name, new, index=None):
        """The window's ``holder.name`` (or ``holder.name[index]``) becomes ``new``; the original is hidden and comes
        back with the current text and visibility of the replacement in Undo."""
        old = getattr(holder, name) if index is None else getattr(holder, name)[index]
        shown = old.IsShow()
        old.Hide()
        if index is None:
            setattr(holder, name, new)
        else:
            getattr(holder, name)[index] = new
        if shown:
            new.Show()
        else:
            new.Hide()
        self.own(new)
        self.swaps.append((holder, name, index, old))
        return new

    def text(self, parent, old, role, color, align='left', limit=None):
        """An R1 text where ``old`` (a top-aligned original text line) was: its text, position and alignment."""
        x, y = old.GetLocalPosition()
        return uir1.Text(parent, old.GetText(), x, y, self.kit.font(role), Signed(color), align=align, valign='top',
                         limit=limit)

    def Undo(self):
        # The replacements are asked whether they were shown BEFORE they are hidden: an original comes back shown
        # exactly when its replacement was (hidden first, every swapped text and bar stayed hidden after a fallback).
        for holder, name, index, old in reversed(self.swaps):
            try:
                new = getattr(holder, name) if index is None else getattr(holder, name)[index]
                if index is None:
                    setattr(holder, name, old)
                else:
                    getattr(holder, name)[index] = old
                if hasattr(old, 'SetText') and hasattr(new, 'GetText'):
                    old.SetText(new.GetText())
                if new.IsShow():
                    old.Show()
                else:
                    old.Hide()
            except Exception:
                pass
        for widget in reversed(self.widgets):
            try:
                widget.Hide()
            except Exception:
                pass
        for widget, shown in reversed(self.hidden):
            try:
                if shown:
                    widget.Show()
            except Exception:
                pass
        for widget, position in reversed(self.moved):
            try:
                widget.SetPosition(*position)
            except Exception:
                pass
        for restore in reversed(self.reloads):
            try:
                restore()
            except Exception:
                pass
        if self.board is not None:
            try:
                self.board.Restore()
            except Exception:
                pass
        self.widgets, self.swaps, self.hidden, self.moved, self.reloads = [], [], [], [], []
        self.board = None


def SlotBase(slot, original=ORIGINAL_SLOT):
    """(restore, apply) for the base image of a slot window: the R1 slot C now, ``original`` in Undo."""
    return (lambda: slot.SetSlotBaseImage(original, 1.0, 1.0, 1.0, 1.0),
            lambda: slot.SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0))


# --------------------------------------------------------------------------- the window
class Skin(SkinBase):
    def Build(self):
        win, kit = self.window, self.kit
        import uipermanenttasks as P
        title = TITLE
        try:
            title = win.titleName.GetText() or TITLE
        except Exception:
            pass
        self.board = uir1.BoardSkin(win, kit, title, on_close=ui.__mem_func__(win.Close))

        for category in win.CATEGORY_ORDER:
            self.hide(win.tabs[category])
        x, y, w = TAB
        options = [(category, P.CATEGORY_LABELS[category], TAB_ICON % category) for category in win.CATEGORY_ORDER]
        self.tabs = self.own(Tabs(win, kit, x, y, w, options, ui.__mem_func__(win.SelectCategory)))
        self.tabs.SetValue(win.category)

        for panel in (win.previewPanel, win.detailsPanel):
            self.move(panel, panel.GetLocalPosition()[0], PANEL_Y)
        self.preview = self.own(uir1.Frame(win.previewPanel, 0, 0, win.previewPanel.GetWidth(),
                                           win.previewPanel.GetHeight(), 'panel', bg=None))

        panel = win.detailsPanel
        self.swap(win, 'categoryText', self.text(panel, win.categoryText, 'text_b', T.IVORY))
        self.swap(win, 'stageText', self.text(panel, win.stageText, 'text_s', BONUS))
        self.swap(win, 'targetText', self.text(panel, win.targetText, 'text_b', T.INK, 'center'))
        self.swap(win, 'progressText', self.text(panel, win.progressText, 'text_s', T.INK, 'center'))
        self.swap(win, 'rewardsText', self.text(panel, win.rewardsText, 'text_sb', T.INK_DIM))
        self.swap(win, 'rewardBonusText', self.text(panel, win.rewardBonusText, 'text_s', BONUS, 'center'))
        for index in range(len(win.huntProgressTexts)):
            self.swap(win, 'huntProgressTexts', self.text(panel, win.huntProgressTexts[index], 'text_s', T.INK),
                      index)
            self.swap(win, 'huntCountTexts', self.text(panel, win.huntCountTexts[index], 'text_s', T.INK_DIM,
                                                       'right'), index)
            self.swap(win, 'huntProgressGauges', Gauge(panel, 0, 0, panel.GetWidth()), index)
        gx, gy = win.progressGauge.GetLocalPosition()
        self.swap(win, 'progressGauge', Gauge(panel, gx, gy, panel.GetWidth()))

        frame = win.passiveFrame
        self.reload(lambda: frame.LoadImage(ORIGINAL_SLOT), lambda: frame.LoadImage(uir1.SLOT_CELL))
        for slot in win.rewardSlots:
            self.reload(*SlotBase(slot))
        return self

    def Layout(self, width, height):
        """After the window laid itself out for ``height`` (uipermanenttasks.__LayoutHunt): DY px shorter."""
        win = self.window
        height = int(height) - DY
        win.SetSize(int(width), height)
        self.board.Resize(int(width), height)
        self.preview.Resize(win.previewPanel.GetWidth(), win.previewPanel.GetHeight())

    def SelectCategory(self, category):
        self.tabs.SetValue(self.window.category)

    def Destroy(self):
        self.window = None
        self.widgets, self.swaps, self.hidden, self.moved, self.reloads = [], [], [], [], []
        self.board = None


class Guard(object):
    """The window's handle on the skin: every call runs guarded; a failure restores the original look."""

    def __init__(self, skin):
        self.skin = skin

    def __nonzero__(self):
        return self.skin is not None

    __bool__ = __nonzero__

    def _Run(self, name, *args):
        if self.skin is None:
            return
        try:
            getattr(self.skin, name)(*args)
        except Exception:
            Fail()
            self.Fallback()

    def Fallback(self):
        skin, self.skin = self.skin, None
        window = skin.window
        skin.Undo()
        if window is not None:
            window.r1 = None
            try:
                window._PermanentTasksWindow__RefreshTask()
            except Exception:
                uir1.TraceFailure(WHAT + u' (original look)')

    def Layout(self, width, height):
        self._Run('Layout', width, height)

    def SelectCategory(self, category):
        self._Run('SelectCategory', category)

    def Destroy(self):
        if self.skin is not None:
            self.skin.Destroy()
        self.skin = None


def Build(window):
    """The R1 look of a PermanentTasksWindow (its original widgets already made), or None for the original look
    ("Starý vzhled", or R1 failed: then the original look is back)."""
    if not UseR1():
        return None
    skin = Skin(window)
    try:
        skin.Build()
    except Exception:
        Fail()
        skin.Undo()
        return None
    return Guard(skin)
