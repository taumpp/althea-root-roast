# -*- coding: utf-8 -*-
"""Denní úkoly (uidailytasks.DailyTasksWindow) in the Althea R1 look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md,
E:/althea-local-work/ui-navrhy-r1/PRAVIDLA-UI.md).

The window keeps its width (573, 589 with the scroll bar), its flags (movable, float) and every function: the task
rows (scroll icon, name, objective - on a second line when it is too long, no row tooltip -, counter or "Splněno",
the progress, "Odevzdat" for a chest task, up to five rewards with their item tooltips, completed rows dimmed), seven
visible rows with the scroll bar and the mouse wheel, the loading / empty / error states and the footer with the completed count and the reset countdown.
uidailytasks keeps all of that logic; this module only builds the widgets it drives (same attribute names) in R1:

* the R1 frame and the red R1 header (title, vein, plain X) on the window's own board (uir1.BoardSkin);
* the column headings Úkol / Postup / Odměny as R1 labels over a quiet divider instead of the market header plate;
* every row an R1 panel (a completed row's panel dimmed) with the texts in Noto Sans and the R1 ink;
* the progress as the R1 bar (grey track, dark blood red fill, uipermanenttasksr1.Gauge), "Odevzdat" as a small R1
  button, the rewards in the R1 item slot C (uir1.SLOT_CELL, native 32 x 32), the narrow R1 scroll bar;
* the switch "Denní úkoly | Řemesla" (uir1.Segment, T.SEG_H) over the column headings: the daily tasks or the craft
  contract rows (craftcontractmodel); the window opens on the tab the character had last (dailytasksprefs). The list
  starts DY px lower than in the original (DY < 0), the window is that much taller.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building or laying out
R1 restores the original look (traced to syserr) and R1 is not tried again in this session.
"""
import ui

import uir1
import uir1tokens as T

import uidailytasks as D
import uipermanenttasksr1 as R

WHAT = u'Denní úkoly'
TITLE = u'Denní úkoly'
TABS_Y = T.HEAD_H + 6           # the switch Denní úkoly | Řemesla under the header
COLUMNS_Y = TABS_Y + T.SEG_H + 8    # the column headings (text_sb, top-aligned)
DIVIDER_Y = COLUMNS_Y + 18      # the divider under them
LIST_Y = DIVIDER_Y + 5          # the task list (68 in the original)
DY = D.VIEWPORT_POSITION[1] - LIST_Y
COLUMNS = (u'Úkol', u'Postup', u'Odměny')
SCROLL_X = D.VIEWPORT_POSITION[0] + D.ROW_SIZE[0] + (D.SCROLL_GUTTER - T.SCROLL_W) // 2
COMPLETE = 0xFF8FCB7C           # "Splněno": the green of a complete counter of the R1 mount tasks
DIMMED = 0.55                   # the panel of a completed row

NAME = (48, 7)
OBJECTIVE = (48, 26)
WRAPPED = (1, 17, 33)           # name, objective, its second line: three 16 px cells inside the 51 px row
PROGRESS_Y = 7
GAUGE_Y = 31
HAND_IN = (D.PROGRESS_CENTER_X - 36, 25, 72)


class Surface(object):
    """The row's ``background`` for DailyTaskRow.SetData: the R1 panel, dimmed for a completed task (the original
    loads result_disabled.png then)."""

    def __init__(self, panel):
        self.panel = panel
        self.dimmed = False

    def LoadImage(self, path):
        self.dimmed = 'disabled' in str(path)
        self.panel.ops.SetAlpha(DIMMED if self.dimmed else 1.0)


class RewardSlot(D.DailyRewardSlot):
    """The original reward slot (item, amount, tooltip, dimming) on the R1 item slot C."""

    def __init__(self, parent, x, y):
        D.DailyRewardSlot.__init__(self, parent, x, y)
        self.frame.LoadImage(uir1.SLOT_CELL)


class Row(D.DailyTaskRow):
    """A task row with the widgets of DailyTaskRow in R1; SetData / Clear / the hand-in are the original ones."""

    TEXT_Y = (NAME[1], OBJECTIVE[1])
    WRAPPED_TEXT_Y = WRAPPED
    SIDE_Y = (NAME[1], OBJECTIVE[1])     # a contract row: the stock line beside the name, the reward text under it

    def __init__(self, parent, index, kit):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(0, index * D.ROW_STEP)
        self.SetSize(*D.ROW_SIZE)
        self.tooltipItem = None
        self.kit = kit
        font = kit.font('text_s')
        self.panel = uir1.Frame(self, 0, 0, D.ROW_SIZE[0], D.ROW_SIZE[1], 'panel')       # first: under everything
        self.background = Surface(self.panel)
        self.scrollIcon = D._CreateImage(self, 9, 9, D.QUEST_SCROLL_ROOT + "quest_scroll_normal.png")
        self.name = uir1.Text(self, u'', NAME[0], NAME[1], font, R.Signed(T.INK), valign='top',
                              limit=D.NAME_LIMIT_WIDTH)
        self.objective = uir1.Text(self, u'', OBJECTIVE[0], OBJECTIVE[1], font, R.Signed(T.MUTED), valign='top',
                                   limit=D.NAME_LIMIT_WIDTH)
        self.objectiveWrap = uir1.Text(self, u'', OBJECTIVE[0], WRAPPED[2], font, R.Signed(T.MUTED), valign='top',
                                       limit=D.NAME_LIMIT_WIDTH)
        self.objectiveProbe = uir1.Text(self, u'', OBJECTIVE[0], 0, font, R.Signed(T.MUTED), valign='top')
        self.objectiveProbe.Hide()                                  # measures the objective for the wrap
        self.progressText = uir1.Text(self, u'0 / 0', D.PROGRESS_CENTER_X, PROGRESS_Y, font, R.Signed(T.INK),
                                      align='center', valign='top')
        self.gauge = R.Gauge(self, D.GAUGE_LEFT, GAUGE_Y, D.GAUGE_SIZE[0])
        self.rewardSlots = [RewardSlot(self, 0, 9) for unusedIndex in range(D.MAX_VISIBLE_REWARDS)]
        self.placeholderText = uir1.Text(self, u'Připravujeme', D.REWARD_RIGHT_X,
                                         uir1.CellTop(D.ROW_SIZE[1], font), font, R.Signed(T.MUTED), align='right',
                                         valign='top')
        self._InitContractWidgets(uir1.Text(self, u'', D.REWARD_RIGHT_X, NAME[1], font, R.Signed(T.MUTED),
                                            align='right', valign='top'))
        self.handInTaskId = ""
        self.handInEvent = None
        x, y, w = HAND_IN
        self.handInButton = uir1.Button(self, kit, x, y, w, u'Odevzdat', small=True,
                                        event=ui.__mem_func__(self._DailyTaskRow__HandIn))
        self.handInButton.Hide()
        self.Hide()

    def _SideTextWidth(self):
        return uir1.TextWidth(self.sideText)

    def _Hint(self, area, text, over):
        if over and text:
            uir1.ShowHint(self.kit, area, text)
        else:
            uir1.HideHint(area)

    def SetData(self, data):
        D.DailyTaskRow.SetData(self, data)
        if not data:
            return
        completed = data["status"] == D.TASK_STATUS_COMPLETED
        self.name.SetPackedFontColor(R.Signed(T.MUTED if completed else T.INK))
        self.objective.SetPackedFontColor(R.Signed(T.MUTED))
        self.objectiveWrap.SetPackedFontColor(R.Signed(T.MUTED))
        self.progressText.SetPackedFontColor(R.Signed(COMPLETE if completed else T.INK))


class Skin(R.SkinBase):
    def Build(self):
        win, kit = self.window, self.kit
        title = TITLE
        try:
            title = win.titleName.GetText() or TITLE
        except Exception:
            pass
        self.board = uir1.BoardSkin(win, kit, title, on_close=ui.__mem_func__(win.Close))

        # The switch Denní úkoly | Řemesla: the R1 segment of the kit (default height T.SEG_H).
        self.segment = self.own(uir1.Segment(win, kit, [(tab, D._Text(key)) for tab, key in zip(D.TABS, D.TAB_TEXTS)],
                                             event=ui.__mem_func__(win.SelectTab)))
        self.segment.SetPosition(D.VIEWPORT_POSITION[0], TABS_Y)
        self.segment.SetValue(win.tab)
        win.SetTabbed(True)

        # Column headings: R1 labels over a divider instead of the market header plate.
        self.hide(win.header)
        font = kit.font('text_sb')
        for child in list(win.children):
            text = child.GetText() if hasattr(child, 'GetText') else None
            if text in COLUMNS:
                self.hide(child)
                x = child.GetLocalPosition()[0]
                align = 'right' if text == COLUMNS[2] else 'center'
                self.own(uir1.Text(win, text, x, COLUMNS_Y, font, R.Signed(T.INK_DIM), align=align, valign='top'))
        self.own(uir1.Divider(win, D.VIEWPORT_POSITION[0], DIVIDER_Y, D.ROW_SIZE[0]))

        self.move(win.viewport, D.VIEWPORT_POSITION[0], LIST_Y)
        for row in win.rows:
            self.hide(row)
        rows = [self.own(Row(win.viewport, index, kit)) for index in range(len(win.rows))]
        self.swaps.append((win, 'rows', None, win.rows))
        win.rows = rows

        old = win.stateText
        x, y = old.GetLocalPosition()
        self.swap(win, 'stateText', uir1.Text(win.viewport, old.GetText(), x, y, kit.font('text'), R.Signed(T.MUTED),
                                              align='center', valign='center', limit=D.STATE_LIMIT_WIDTH))
        old = win.resetText
        x, y = old.GetLocalPosition()
        self.swap(win, 'resetText', uir1.Text(win, old.GetText(), x, y, kit.font('text_s'), R.Signed(T.INK_DIM),
                                              align='center', valign='center'))

        bar = uir1.ScrollBar(kit)
        bar.SetParent(win)
        bar.SetPosition(SCROLL_X, LIST_Y)
        bar.SetScrollBarSize(win.viewport.GetHeight())
        bar.SetScrollEvent(ui.__mem_func__(win._DailyTasksWindow__OnScroll))
        self.swap(win, 'scrollBar', bar)
        return self

    def Undo(self):
        win = self.window
        rows = getattr(win, 'rows', None) if win is not None else None
        if win is not None:
            win.SetTabbed(False)            # the original look lists the daily tasks and the contracts together
        R.SkinBase.Undo(self)
        for row in rows or ():
            try:
                row.Hide()
            except Exception:
                pass

    def SelectTab(self, tab):
        self.segment.SetValue(tab)

    def Layout(self, width, height):
        """After the window sized itself (uidailytasks.__ResizeForTasks): DY px shorter (DY < 0 with the switch: that
        much taller), the footer follows."""
        win = self.window
        width, height = int(width), int(height) - DY
        win.SetSize(width, height)
        self.board.Resize(width, height)
        win.resetText.SetPosition(width // 2, height - D.FOOTER_HEIGHT // 2)

    def Destroy(self):
        self.window = None
        self.widgets, self.swaps, self.hidden, self.moved, self.reloads = [], [], [], [], []
        self.board = None
        self.segment = None


class Guard(R.Guard):
    def Fallback(self):
        skin, self.skin = self.skin, None
        window = skin.window
        skin.Undo()
        if window is None:
            return
        window.r1 = None
        try:
            window._DailyTasksWindow__ApplyTasks()      # both lists again, sized for the original look
        except Exception:
            uir1.TraceFailure(WHAT + u' (original look)')

    def _Run(self, name, *args):
        if self.skin is None:
            return
        try:
            getattr(self.skin, name)(*args)
        except Exception:
            R.Fail(WHAT)
            self.Fallback()

    def SelectTab(self, tab):
        self._Run('SelectTab', tab)


def Build(window):
    """The R1 look of a DailyTasksWindow (its original widgets already made), or None for the original look
    ("Starý vzhled", or R1 failed: then the original look is back)."""
    if not R.UseR1(WHAT):
        return None
    skin = Skin(window)
    try:
        skin.Build()
    except Exception:
        R.Fail(WHAT)
        skin.Undo()
        return None
    return Guard(skin)
