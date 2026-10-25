# -*- coding: utf-8 -*-
"""Biologický výzkum (uibiologresearch.BiologWindow, 720 x 446) in the Althea R1 look "Krvavá žíla"
(docs/ALTHEA_R1_KIT.md), drawn INTO the original window.

uibiologresearch keeps the window, its flags (float + movable: a drag anywhere on the window moves it) and every
function: the two pages (Výzkumy / Dokončené), the four research rows with the scroll bar and the mouse wheel, the
item tooltip over a research icon, the elixir and accelerator check boxes with their costs and tooltips, the alarm
switch, the reward tooltip, the submit button with its enabled state, the locked rows (veil and padlock), the reward
choice dialog and every server command. This module only re-skins it:

* the R1 frame and header (title, vein, plain X) instead of the crimson shell and title bar;
* the pages as an R1 segment, the column captions in the R1 colours, the R1 scroll bar;
* each row: the level in an R1 panel as tall as the tray and aligned with it (the
  70 px level box beside the 78 px tray looked inconsistent), the tray as an R1 panel with the R1 item slot C
  (uir1.SLOT_CELL) under the item icon (centred in the tray), the progress as the red vein on a dark track, the alarm as a
  small R1 button with the original bell (the vein along its bottom while the alarm is on), "Odevzdat" (primary) and
  "Odměna" as small R1 buttons; the value colours (duration, state, progress, costs) stay those of the original
  window;
* the elixir and the accelerator of each row as two cells in the same slot style as the research item: the booster's
  item icon in the R1 slot, the R1 check box with the cost ("1 ks") centred under it; the whole cell takes the click
  and the tooltip. The cells, the alarm and the two actions share the row's centre line; the captions Elixír /
  Urychlovač sit centred over the cells on the line of "Úroveň" and the loose icons above the list are gone
  (screenshot 06: they did not fit the check boxes below them);
* the reward choice dialog in the R1 frame with R1 buttons.

The original controls stay the source of truth: the row's Refresh tells the R1 row its state (the enabled state of a
native button is never asked for - the game EXE has no wndMgr.IsDisable). Settings -> "Starý vzhled" (settingslook
'legacy') keeps the original window. A failure while building the R1 look restores the original window (traced to
syserr) and the R1 look is not tried again in this session.
"""
import ui

import uir1
import uir1layout as L
import uir1skin
import uir1tokens as T

WIDTH, HEIGHT = 720, 446
WHAT = u'Biologický výzkum'
SLOT = uir1.SLOT_CELL               # the R1 item slot C (32 x 32) under the research item and the booster icons
BELL = 'd:/ymir work/ui/game/crimson_ember/biolog/research/alarm.png'
PADLOCK = 'd:/ymir work/ui/game/crimson_ember/biolog/research/lock_gate_32x44.png'
VEIL = (0x0C0B0C, 0.62)            # the veil over a locked row (a plain ui.Bar: no bronze edge)
SEGMENT = (20, 37, 124)            # x, y, cell width of the page switch (Výzkumy / Dokončené)
PORTRAIT = (632, 30)               # the biologist's portrait, under the header vein
SCROLL_X = 699                     # the R1 scroll bar (rows end at 690)
LEVEL_BOX = (0, 0, 40, 78)         # the level panel of a row: as tall as the tray and aligned with it
TRAY = (52, 0, 618, 78)            # the tray panel of a row
ITEM_SLOT = (88, 23)               # the research item's slot and icon (32 px), centred in the tray
BOOSTER_X, BOOSTER_W = (394, 458), 50   # the elixir / accelerator cells (x in the row, width)
BOOSTER_Y, BOOSTER_H = 11, 56      # a cell: the slot (32 px) on top, the check box + cost line under it
BOOSTER_LINE, LINE_H = 40, 16      # the check box + cost line inside a cell (y, height)
BOOSTER_ICONS = ('icon/item/71035.tga', 'icon/item/72357.tga')   # the elixir and the accelerator (every research)
CHECK_GAP = 5                      # check box -> cost
TRACK = (146, 54, 127)             # x, y, width of the progress track in a row
NAME_Y, META_Y = 8, 31             # rows: the item name, the duration / state line
ALARM = (518, 26, 32)              # x, y, width of the alarm button (26 px)
ACTION_X, ACTION_W = 556, 106      # "Odevzdat" (top) and "Odměna" (bottom), 22 px each
SUBMIT_Y, REWARD_Y = 12, 44
CHECK_PATH = T.ROOT + 'check/%s_%s.png'

_failed = set()


def UseR1():
    """The R1 look unless "Starý vzhled" is chosen or the R1 look of this window already failed in this session."""
    return WHAT not in _failed and uir1.UseR1()


def Fail():
    _failed.add(WHAT)
    uir1.TraceFailure(WHAT)


def CheckPath(selected, enabled):
    """The R1 check box of a booster (15 px): ticked or not, dimmed while the booster cannot be used."""
    return CHECK_PATH % ('on' if selected else 'off', 'normal' if enabled else 'disabled')


class ActionButton(uir1.Button):
    """R1 button that also runs the original hover handlers (the tooltips of the alarm, the reward, the submit)."""

    def __init__(self, parent, kit, x, y, w, text='', primary=False, small=False, event=None, over=None, out=None):
        uir1.Button.__init__(self, parent, kit, x, y, w, text, primary=primary, small=small, event=event)
        self.over, self.out = over, out

    def OnMouseOverIn(self):
        uir1.Button.OnMouseOverIn(self)
        if getattr(self, 'over', None):
            self.over()

    def OnMouseOverOut(self):
        uir1.Button.OnMouseOverOut(self)
        if getattr(self, 'out', None):
            self.out()


class RowSkin(object):
    """The R1 layer of one research row. Made at the START of ResearchRow.__init__ (so its panels, slot and track lie
    under every original child of the row); Apply() hides the crimson art once the row is complete; Refresh() follows
    the row's state on every refresh of the original."""

    def __init__(self, skin, row):
        self.skin, self.row = skin, row
        kit = skin.kit
        self.level_box = uir1.Frame(row, *LEVEL_BOX, kind='panel')
        self.tray = uir1.Frame(row, *TRAY, kind='panel')
        self.slot = self.Picture(row, SLOT, *ITEM_SLOT)
        # The booster cells' slots and icons: made now, under the original booster windows that take their clicks.
        self.booster_slots, self.booster_icons = [], []
        for x, icon in zip(BOOSTER_X, BOOSTER_ICONS):
            sx = x + (BOOSTER_W - 32) // 2
            self.booster_slots.append(self.Picture(row, SLOT, sx, BOOSTER_Y))
            picture = self.Picture(row, icon, sx, BOOSTER_Y)
            picture.SetPosition(sx + (32 - picture.GetWidth()) // 2, BOOSTER_Y + (32 - picture.GetHeight()) // 2)
            self.booster_icons.append(picture)
        tx, ty, tw = TRACK
        self.track = uir1.Layer(row, tx, ty, tw, T.SLIDER_H, L.slider_track(0, 0, tw))
        self.fill = uir1.Layer(row, tx, ty, tw, T.SLIDER_H, [])
        ax, ay, aw = ALARM
        self.alarm = ActionButton(row, kit, ax, ay, aw, '', event=lambda: row.ToggleAlarm(),
                                  over=lambda: row.AlarmTip(), out=lambda: row.owner.HideTooltip())
        self.bell = ui.ImageBox()
        self.bell.SetParent(self.alarm)
        self.bell.AddFlag('not_pick')
        self.bell.LoadImage(BELL)
        self.bell.SetPosition((aw - 20) // 2, (T.BTN_H - 20) // 2)
        self.bell.Show()
        self.submit = ActionButton(row, kit, ACTION_X, SUBMIT_Y, ACTION_W, skin.texts['submit'], primary=True,
                                   small=True, event=lambda: row.Submit(), over=lambda: row.SubmitTip(),
                                   out=lambda: row.owner.HideTooltip())
        self.reward = ActionButton(row, kit, ACTION_X, REWARD_Y, ACTION_W, skin.texts['reward'], small=True,
                                   event=lambda: row.Rewards(), over=lambda: row.Rewards(),
                                   out=lambda: row.owner.HideTooltip())
        self.widgets = [self.level_box, self.tray, self.slot, self.track, self.fill, self.alarm, self.submit,
                        self.reward] + self.booster_slots + self.booster_icons

    @staticmethod
    def Picture(parent, path, x, y):
        image = ui.ImageBox()
        image.SetParent(parent)
        image.AddFlag('not_pick')
        image.LoadImage(path)
        image.SetPosition(x, y)
        image.Show()
        return image

    def Apply(self, rec):
        row, kit, C = self.row, self.skin.kit, self.skin.colors
        for widget in (row.plate, row.surface, row.track, row.fill, row.alarm, row.reward, row.submit):
            rec.Hide(widget)
        cell = uir1.FontCell(kit.font('text_b'))
        rec.Font(row.level, kit.font('text_b'), T.IVORY, 'Tahoma:18b', C['gold'])
        rec.Position(row.level, LEVEL_BOX[0] + LEVEL_BOX[2] // 2, LEVEL_BOX[1] + (LEVEL_BOX[3] - cell) // 2)
        rec.Position(row.icon, *ITEM_SLOT)
        rec.Font(row.name, kit.font('text_b'), T.INK, 'Tahoma:13b', C['white'])
        rec.Position(row.name, 146, NAME_Y)
        rec.Font(row.intervalLabel, kit.font('text_s'), T.INK_DIM, 'Tahoma:11', C['muted'])
        rec.Position(row.intervalLabel, 146, META_Y)
        label_w = uir1.TextWidth(row.intervalLabel)
        rec.Font(row.interval, kit.font('text_sb'), C['blue'], 'Tahoma:11b', C['blue'])
        rec.Position(row.interval, 146 + label_w + 5, META_Y)
        rec.Font(row.status, kit.font('text_s'), C['green'], 'Tahoma:11', C['green'])
        rec.Position(row.status, 279, META_Y)
        tx, ty, tw = TRACK
        rec.Font(row.progress, kit.font('text_s'), C['gold'], 'Tahoma:12', C['gold'])
        rec.Position(row.progress, tx + tw + 10, ty + uir1.CellTop(T.SLIDER_H, kit.font('text_s')))
        # The veil and the padlock of a locked row: made now, over everything of the row; the crimson veil (with its
        # bronze edge) stays hidden, Refresh() shows these instead.
        self.veil = uir1.Rect(row, TRAY[0], TRAY[1], TRAY[2], TRAY[3], *VEIL)
        self.veil.Hide()
        self.padlock = ui.ImageBox()
        self.padlock.SetParent(row)
        self.padlock.AddFlag('not_pick')
        self.padlock.LoadImage(PADLOCK)
        x, y = row.lockGlyph.GetLocalPosition()
        self.padlock.SetPosition(x, y)
        self.padlock.Hide()
        self.widgets += [self.veil, self.padlock]
        for booster, x in zip((row.elixir, row.clock), BOOSTER_X):
            original = booster.checkPath
            rec.Call(lambda b=booster: setattr(b, 'checkPath', CheckPath),
                     lambda b=booster, path=original: setattr(b, 'checkPath', path))
            rec.Position(booster, x, BOOSTER_Y)
            rec.Size(booster, BOOSTER_W, BOOSTER_H)
            rec.Font(booster.count, kit.font('text_s'), C['gold'], 'Tahoma:12', C['gold'])
            rec.Position(booster.check, 0, BOOSTER_LINE + (LINE_H - T.CHECK) // 2)
            rec.Position(booster.count, T.CHECK + CHECK_GAP, BOOSTER_LINE + uir1.CellTop(LINE_H, kit.font('text_s')))
            self.CentreLine(booster)

    def CentreLine(self, booster):
        """The check box and the cost centred together under the cell's slot (the cost text changes: "1 ks", "6 ks")."""
        group = T.CHECK + CHECK_GAP + uir1.TextWidth(booster.count)
        gx = max(0, (BOOSTER_W - group) // 2)
        booster.check.SetPosition(gx, booster.check.GetLocalPosition()[1])
        booster.count.SetPosition(gx + T.CHECK + CHECK_GAP, booster.count.GetLocalPosition()[1])

    def Refresh(self, ratio, alarm_on, alarm_enabled, submit_enabled, locked=False):
        """The row's state from its Refresh: progress 0..1, the alarm switch, the enabled actions, the level lock."""
        row = self.row
        for original in (row.lockVeil, row.lockShade, row.lockGlyph):
            original.Hide()
        for widget in (self.veil, self.padlock):
            widget.Show() if locked else widget.Hide()
        for booster, icon in zip((row.elixir, row.clock), self.booster_icons):
            self.CentreLine(booster)
            icon.SetAlpha(1.0 if getattr(booster, 'enabled', True) else 0.35)
        tw = TRACK[2]
        width = int(round(max(0.0, min(1.0, float(ratio))) * tw))
        self.fill.Apply(L.slider_fill(0, 0, width) if width > 0 else [])
        self.alarm.SetPrimary(bool(alarm_on))
        for button, enabled in ((self.alarm, alarm_enabled), (self.submit, submit_enabled)):
            if bool(enabled) != button.IsEnabled():
                button.Enable() if enabled else button.Disable()

    def Destroy(self):
        uir1skin.Destroy(self.widgets)
        self.widgets = []


class ChoiceSkin(object):
    """The reward choice dialog (a ui.BoardWithTitleBar 380 x 166) in the R1 frame with R1 buttons."""

    def __init__(self, kit, board, title, labels, accept, close):
        self.board = board
        self.skin = uir1.BoardSkin(board, kit, title, on_close=close)
        self.buttons = []
        try:
            for choice, label in enumerate(labels):
                self.buttons.append(uir1.Button(board, kit, 37, 41 + choice * 33, 306, label, small=True,
                                                event=lambda value=choice: accept(value)))
        except Exception:
            self.Restore()
            raise

    def Restore(self):
        uir1skin.Destroy(self.buttons)
        self.buttons = []
        self.skin.Restore()


class Skin(object):
    """The R1 look of one BiologWindow. Made before the window's own content (the chrome lies under it), the rows
    call Row() at their start, Apply() finishes the look once the window is complete."""

    def __init__(self, window, title, texts, colors, geometry):
        self.window = window
        self.kit = uir1.Kit()
        self.texts = texts              # tab0, tab1, submit, reward
        self.colors = colors            # the original value colours: gold, white, muted, green, blue
        self.geometry = geometry        # row_y, row_step, visible_rows
        self.rec = uir1skin.Recorder()
        self.rows = []
        self.broken = False
        self.extra = []
        self.chrome = uir1.Chrome(window, self.kit, WIDTH, HEIGHT, title, on_close=window.Close)

    def Row(self, row):
        """The R1 layer of a research row (or None after a failure: Apply() then falls back)."""
        if self.broken:
            return None
        try:
            skin = RowSkin(self, row)
        except Exception:
            self.broken = True
            uir1.TraceFailure(WHAT + ' (row)')
            return None
        self.rows.append(skin)
        return skin

    def Apply(self):
        """Finishes the R1 look; False (and the original look back) when anything failed."""
        try:
            if self.broken:
                raise RuntimeError('a research row could not build its R1 layer')
            self._Apply()
            return True
        except Exception:
            Fail()
            self.Undo()
            return False

    def _Apply(self):
        window, rec, kit = self.window, self.rec, self.kit
        rec.Hide(window.body)
        rec.Hide(window.titleBar)
        rec.Position(window.portrait, *PORTRAIT)
        for button in window.tabs:
            rec.Hide(button)
        x, y, cell_w = SEGMENT
        self.segment = uir1.Segment(window, kit, [(0, self.texts['tab0']), (1, self.texts['tab1'])],
                                    event=window.SetTab, font=kit.font('text_s'), width=2 * cell_w)
        self.segment.SetPosition(x, y)
        self.segment.SetValue(window.tab)
        self.extra.append(self.segment)
        for line in window.captions:
            rec.Font(line, kit.font('text_sb'), T.INK_DIM, 'Tahoma:12b', self.colors['gold'])
        rec.Font(window.empty, kit.font('text'), T.MUTED, 'Tahoma:12', self.colors['muted'])
        scroll = window.scroll
        rec.Hide(scroll)
        self.scroll = uir1.ScrollBar(self.kit)
        self.scroll.SetParent(window)
        row_y, row_step, visible = self.geometry
        self.scroll.SetPosition(SCROLL_X, row_y + 9)
        self.scroll.SetScrollBarSize(visible * row_step - 24)
        self.scroll.SetScrollEvent(window.OnScroll)
        self.scroll.Hide()
        self.extra.append(self.scroll)
        rec.Call(lambda: setattr(window, 'scroll', self.scroll), lambda: setattr(window, 'scroll', scroll))
        for row in self.rows:
            row.Apply(rec)
        self._AlignBoosterHeaders(rec)
        for row in window.rows:
            if row.IsShow():
                row.Refresh()

    def _AlignBoosterHeaders(self, rec):
        """The Elixír / Urychlovač captions centred over their cells (on the line of "Úroveň"); the loose icons above
        the list are hidden - every row shows the booster's icon in its own slot now."""
        window = self.window
        rx = window.rows[0].GetLocalPosition()[0]
        for index, x in enumerate(BOOSTER_X):
            caption = window.captions[1 + index]
            rec.Position(caption, rx + x + BOOSTER_W // 2, caption.GetLocalPosition()[1])
        for icon in getattr(window, 'boosterIcons', []):
            rec.Hide(icon)

    def SetTab(self, index):
        segment = getattr(self, 'segment', None)
        if segment is not None:
            segment.SetValue(index)

    def Choice(self, board, title, labels, accept, close):
        """The reward choice dialog in R1; None when that failed (the caller builds the original buttons)."""
        try:
            return ChoiceSkin(self.kit, board, title, labels, accept, close)
        except Exception:
            uir1.TraceFailure(WHAT + ' (reward choice)')
            return None

    def Undo(self):
        """The original look again: every recorded change undone, the R1 widgets hidden and dropped."""
        self.rec.Undo()
        for row in self.rows:
            row.Destroy()
            if getattr(row.row, 'r1', None) is row:
                row.row.r1 = None
        self.rows = []
        uir1skin.Destroy(self.extra)
        self.extra = []
        if self.chrome is not None:
            self.chrome.Destroy()
            self.chrome = None
        if getattr(self.window, 'r1', None) is self:
            self.window.r1 = None

    def Destroy(self):
        for row in self.rows:
            row.Destroy()
        self.rows = []
        uir1skin.Destroy(self.extra)
        self.extra = []
        if self.chrome is not None:
            self.chrome.Destroy()
            self.chrome = None
