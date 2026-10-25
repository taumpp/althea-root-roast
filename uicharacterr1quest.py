# -*- coding: utf-8 -*-
"""The quest page (Úkoly) of the character window in the R1 look, part of uicharacterr1.CharacterSkin.

uicharacter.CharacterWindow keeps the page (Quest_Page of uiscript/uiscript/characterwindow.py): five row buttons
(their click opens the quest or runs the shortcut - Trvalé úkoly / Denní úkoly), the quest scroll icons, the name /
time / counter lines that RefreshQuest fills and places, the clock of OnUpdate and the scrolling of OnQuestScroll and
OnRunMouseWheel. R1 changes only the look, consistent with the other pages of the R1 character window:

* the list on the R1 window background like the other pages (testers 8. 10.: the dark inner panel with its own
  border looked like an old box next to the grey Akce / Status pages); the rows are R1 bands (nothing at rest, a lighter fill under the mouse, the dark fill
  with the red line under the row while pressed - tools/build_althea_r1_alchymie.py) with quiet dividers between
  the shown rows;
* the name, the time and the counter in Noto Sans, placed inside the row after every
  RefreshQuest (three lines in the 56 px row, a shortcut row's single line in its middle);
* the R1 scroll bar (same API: SetScrollEvent, GetPos, OnUp / OnDown, Show / Hide) instead of the old one.

The quest scroll icons stay. Every change is recorded on the skin's Recorder (undone with the whole skin).
"""
import ui

import uir1
import uir1tokens as T

ROW_ART = 'd:/ymir work/ui/public/althea_r1_alchymie/quest/row_%s.png'
ROW_ORIGINAL = 'd:/ymir work/ui/game/crimson_ember/dungeon_teleport/row/dungeon_231x42_%s.png'
ROW_STATES = ('normal', 'hover', 'pressed')
NAME_COLOR, META_COLOR = 0xffeadfc8, 0xffa99e8a      # uicharacter QUEST_NAME_COLOR / QUEST_META_COLOR
PAGE_Y = 24                                          # Quest_Page inside the window
ROW_X, ROW_TOP, ROW_STEP, ROW_W, ROW_H = 10, 8, 60, 219, 56
ICONS = (16, 20)                                     # Quest_Slot: the 32 px icons in the middle of the rows
TEXT_X = 56
LINES = (5, 21, 37)                                  # name, time, counter: tops inside a row (15 px cells)
SCROLL = (230, 10, 292)                              # x, y, height of the R1 scroll bar


class QuestPage(object):
    """R1 look of the quest page of one CharacterWindow (built by CharacterSkin, recorded on its Recorder)."""

    def __init__(self, skin):
        self.skin = skin
        self.total = None
        w, rec, kit = skin.window, skin.rec, skin.kit
        self.window = w
        page = w.GetChild('Quest_Page')
        self.rows = [w.GetChild('Quest_Row_0%d' % i) for i in range(5) if w.IsChild('Quest_Row_0%d' % i)]
        self.names = [w.GetChild('Quest_Name_0%d' % i) for i in range(len(self.rows))]
        self.times = [w.GetChild('Quest_LastTime_0%d' % i) for i in range(len(self.rows))]
        self.counts = [w.GetChild('Quest_LastCount_0%d' % i) for i in range(len(self.rows))]
        # Under the page (the first child of the board draws under every page): the dividers, shown only while the
        # quest page is. No inner panel: the page lies on the window's R1 background like Status / Akce.
        back = w.GetChild('Character_Background')
        self.dividers = []
        for index in range(len(self.rows) - 1):
            y = PAGE_Y + ROW_TOP + index * ROW_STEP + ROW_H + 1
            self.dividers.append(skin._new(uir1.Divider(back, ROW_X + 6, y, ROW_W - 12)))
        for index, row in enumerate(self.rows):
            rec.Visuals(row, [ROW_ART % s for s in ROW_STATES], [ROW_ORIGINAL % s for s in ROW_STATES])
            rec.Position(row, ROW_X, ROW_TOP + index * ROW_STEP)
        rec.Position(w.GetChild('Quest_Slot'), *ICONS)
        for line in self.names:
            rec.Font(line, kit.font('text_sb'), T.INK, None, NAME_COLOR)
        for line in self.times + self.counts:
            rec.Font(line, kit.font('text_s'), T.INK_DIM, None, META_COLOR)
        # The R1 scroll bar stands in for the original one (the window shows / hides / reads it as questScrollBar).
        original = getattr(w, 'questScrollBar', None) or w.GetChild('Quest_ScrollBar')
        rec.Hide(original)
        bar = uir1.ScrollBar(kit)
        bar.SetParent(page)
        sx, sy, sh = SCROLL
        bar.SetPosition(sx, sy)
        bar.SetScrollBarSize(sh)
        scroll = getattr(w, 'OnQuestScroll', None)
        if scroll is not None:
            bar.SetScrollEvent(ui.__mem_func__(scroll))
        if original.IsShow():
            bar.Show()
        else:
            bar.Hide()
        self.bar = skin._new(bar)

        def use_bar():
            w.questScrollBar = bar

        def use_original():
            w.questScrollBar = original
        rec.Call(use_bar, use_original)

    def Sync(self):
        """After SetState / RefreshQuest: the text lines inside their rows, the dividers between shown rows (only
        with the page), the scroll thumb for the number of quests."""
        w = self.window
        shown = getattr(w, 'state', None) == 'QUEST'
        for widget in self.dividers:
            widget.Show() if shown else widget.Hide()
        visible = [row.IsShow() for row in self.rows]
        for index, divider in enumerate(self.dividers):
            if not (shown and visible[index] and visible[index + 1]):
                divider.Hide()
        for index in range(len(self.rows)):
            top = ROW_TOP + index * ROW_STEP
            name, time, count = self.names[index], self.times[index], self.counts[index]
            if time.IsShow() or count.IsShow():
                lines = ((name, LINES[0]), (time, LINES[1]), (count, LINES[2]))
            else:                                   # a shortcut row (one line in the middle)
                lines = ((name, uir1.CellTop(ROW_H, self.skin.kit.font('text_sb'))),)
            for line, dy in lines:
                if line.GetLocalPosition() != (TEXT_X, top + dy):
                    line.SetPosition(TEXT_X, top + dy)
        total = getattr(w, 'questTotalCount', 0) or 0
        if total > len(self.rows) and total != self.total:
            self.bar.SetMiddleBarSize(float(len(self.rows)) / total)
            self.bar.SetScrollStep(1.0 / (total - len(self.rows)))
            self.bar.SetPos(self.bar.GetPos(), False)        # the thumb where the list is (no scroll event)
        self.total = total
