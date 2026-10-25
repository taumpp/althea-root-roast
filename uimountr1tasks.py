# -*- coding: utf-8 -*-
"""Úkoly větve of the mount window (uimountsystem.MountSystemWindow, page Živly) in the R1 look, used by
uimountr1.MountSkin.

TaskRow has the API of uimountk1.TaskRow (SetData(row, name, number), SetEnabled, HideToolTip, HEIGHT) and the same
behaviour - the wrapped task text, the counter ("0 / 7 500", green when complete), the progress, "Odevzdat" for an
item task that is not complete (the submit event only while enabled), the tooltip with the task and its reward - in
R1: the number and the text in Noto Sans, the progress as the red vein on a dark track, "Odevzdat"
as a small R1 button and a quiet divider under the row. Every text is top-aligned (the task list clips its content
with a scissor rectangle: no line may hang below its row).

Gauge is the R1 progress (the vein up to the value on a dark track); the skin also uses it for the bonus of the
selected branch.
"""
import ui
import uitooltip

import uimountk1 as K1
import uir1
import uir1tokens as T

COMPLETE = 0xFF8FCB7C           # the green of a complete counter (uimountk1.GREEN)
TRACK_H = 5
WIDTH = 210
TEXT_X = 27
LINE_H = 17                     # the text_s cell (16 px) and 1 px between the lines of a wrapped task
NAME_TOP = 4
COUNTER_TOP = 26
GAUGE_TOP = 47
SUBMIT = (130, 44, 80)          # x, y, width of "Odevzdat" (22 px)
BASE_H = 78


class Gauge(ui.Window):
    """R1 progress: a dark track with a graphite outline, the red vein from its start up to the value."""

    def __init__(self, parent, x, y, w):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.w = int(w)
        self.SetSize(self.w, TRACK_H)
        self.track = uir1.Rect(self, 0, 0, self.w, TRACK_H, T.BORDER)
        self.inner = uir1.Rect(self, 1, 1, self.w - 2, TRACK_H - 2, 0x0A0909)
        self.vein = uir1.Vein(self, 1, TRACK_H // 2, 1)
        self.fill = None
        self.value, self.maximum = 0, 1
        self.SetValue(0, 1)
        self.Show()

    def SetValue(self, value, maximum):
        try:
            maximum = max(1, int(maximum))
            value = max(0, min(maximum, int(value)))
        except (TypeError, ValueError):
            value, maximum = 0, 1
        self.value, self.maximum = value, maximum
        fill = int((self.w - 2) * value // maximum)
        if fill != self.fill:
            self.fill = fill
            self.vein.SetWidth(fill if fill >= 2 else 0)


class TaskRow(ui.Window):
    """R1 row of one branch task (the API and behaviour of uimountk1.TaskRow)."""
    WIDTH = WIDTH
    HEIGHT = BASE_H

    def __init__(self, parent, submitEvent):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.kit = kit = uir1.Kit()
        self.submitEvent = submitEvent
        self.canSubmit = False
        self.enabled = False
        self.tooltip = None
        self.tooltipLines = []
        self.SAFE_SetOverInEvent(self.__ShowToolTip)
        self.SAFE_SetOverOutEvent(self.HideToolTip)
        self.divider = uir1.Divider(self, 0, self.HEIGHT - T.RULE_H, self.WIDTH)     # pictures first
        self.progress = Gauge(self, TEXT_X, GAUGE_TOP, self.WIDTH - TEXT_X)
        self.number = uir1.Text(self, '', 0, NAME_TOP, kit.font('text_sb'), T.INK_DIM, valign='top')
        self.measure = uir1.Text(self, '', TEXT_X, NAME_TOP, kit.font('text_s'), T.INK, valign='top')
        self.measure.Hide()
        self.lines = []
        self.counter = uir1.Text(self, '', self.WIDTH, COUNTER_TOP, kit.font('text_s'), T.INK_DIM, align='right',
                                 valign='top')
        x, y, w = SUBMIT
        self.submit = uir1.Button(self, kit, x, y, w, u'Odevzdat', small=True, event=self.__Submit)
        self.submit.Hide()
        self.Show()

    def __Measure(self, text):
        self.measure.SetText(text)
        return uir1.TextWidth(self.measure)

    def SetData(self, row, name, number):
        self.number.SetText(u'%02d' % number)
        for line in self.lines:
            line.Hide()
        self.lines = []
        wrapped = K1.WrappedLines(name, self.WIDTH - TEXT_X, self.__Measure)
        self.tooltipLines = wrapped + [row['reward_text']]
        for index, text in enumerate(wrapped):
            self.lines.append(uir1.Text(self, text, TEXT_X, NAME_TOP + index * LINE_H, self.kit.font('text_s'), T.INK,
                                        valign='top'))
        extra = (len(wrapped) - 1) * LINE_H
        self.HEIGHT = BASE_H + extra
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.counter.SetPosition(self.WIDTH, COUNTER_TOP + extra)
        self.counter.SetText(row['progress_text'])
        self.counter.SetPackedFontColor(COMPLETE if row['complete'] else T.INK_DIM)
        self.progress.SetPosition(TEXT_X, GAUGE_TOP + extra)
        self.progress.SetValue(row['progress'], row['target'])
        x, y, unused = SUBMIT
        self.submit.SetPosition(x, y + extra)
        self.submit.SetToolTipText(name + u' | ' + row['reward_text'])
        self.divider.SetPosition(0, self.HEIGHT - T.RULE_H)
        self.canSubmit = row['event_kind'] == 3 and not row['complete']
        if self.canSubmit:
            self.progress.Hide()
            self.submit.Show()
        else:
            self.progress.Show()
            self.submit.Hide()
        self.SetEnabled(self.enabled)

    def SetEnabled(self, enabled):
        self.enabled = bool(enabled)
        if self.enabled and self.canSubmit:
            self.submit.Enable()
        else:
            self.submit.Disable()

    def __Submit(self):
        if self.enabled and self.canSubmit:
            self.submitEvent()

    def __ShowToolTip(self):
        if self.tooltip is None:
            self.tooltip = uitooltip.ToolTip(240)
        self.tooltip.ClearToolTip()
        for line in self.tooltipLines:
            self.tooltip.AppendTextLine(line)
        self.tooltip.ShowToolTip()

    def HideToolTip(self):
        uir1.HideHint()
        if self.tooltip:
            self.tooltip.HideToolTip()
