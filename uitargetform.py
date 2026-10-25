# -*- coding: utf-8 -*-
"""The unified target form, variant A "Sekce pod sebou" (approved 9. 10. 2026, round
kolo-20261009-jednotny-cil-animace): the R1 target board, its drop panel ("Kořist") and the DPS table are ONE form in
ONE R1 frame of ONE width; the form only grows downward.

* Under the 38 px header (a stone too: its queue hint is no longer a permanent line) the sections unroll in a fixed
  order:
  Kořist, then DPS. Both can be open. A section's heading is its separator: one R1 rule with the label on the left
  (Tahoma 12, INK_DIM) and the count on the right (Kořist: the number of drops), no other line or frame.
* The header pair (owner 9. 10. 2026, round kolo-20261009-formular-upravy): "?" (look L0) and the "DPS" switch (D2)
  side by side, centred between the name and the HP block (uitargetr1.PlacePair). Two symmetric toggles:
  "?" opens / closes Kořist; the switch turns DPS on (the blood red track, the knob right: open now and by itself
  on the first own hit) or off (closed and staying closed).
* Kořist (uitarget.CrimsonTargetDetailsPanel, now a section: no frame of its own, the grid re-packed to the form's
  width - 12 columns at most, a tall item still over its 2 slots, the wheel pages, the tooltips and the cycling
  spirit stones as before). A stone's section starts with the queue hint "Shift + mouse Fronta meteorů 2/5"
  (keys at 67 % as native art, Tahoma 12, measured and centred, 6 px above the grid; "Fronta 2/5" when the line
  does not fit): the hint is shown only with "?".
* DPS (uidpsmeter, table A unchanged: Hráč | Poškození | Podíl | DPS 5 s, your row on the R1 hover band, "Boj … ·
  celkem …", "Další" with the badge) also OPENS BY ITSELF on your first damage on the target (once per fight: a
  section the player closed stays closed) and collapses at the table's own end (15 s after "Zničeno za …", 5 s
  without a snapshot). Opened by the chip before any damage it shows the labels and "Boj 0:00 · celkem 0".
  The header switch is the player's preference, saved per character (targetformprefs dps_auto, default ON): OFF
  keeps the section closed for all following targets, fights and relogs (no auto-open) until switched ON again.
  Settings › Rozhraní › Jména a ukazatele › "Ukazatel poškození (DPS)" is the master switch (uidpsmeter.IsEnabled):
  off = no chip, no section, no auto-open, the snapshots dropped. Another target or closing the board resets the
  form at once.
* Players and NPCs have no sections (the header and target panel A stay as they are).

Motion (uir1motion, smoother than the preview): a section unrolls in 240 ms ease-out quint, collapses in 150 ms; the
content stands still and the bottom edge reveals it (EnableScissorRect on the body and on every section); the DPS
section moves up with the Kořist above it on the same curve; the drop icons come in column after column 25 ms apart
from 40 % of the unroll; a click during a motion turns it from the current height. Time based (app.GetTime), dt
clamped, whole pixels; nothing is created per frame.

Engine: the sections are not children of the board - a child outside its parent's rectangle cannot be picked
(CWindow::PickWindow), and the board's height is its header for all of uitarget. They live in the form's own
top-level window ("body") right under the board. One frame: the board's R1 frame and the body's frame are the same
9-slice of the whole form's height; the board clips its copy to the header (EnableScissorRect), the body draws the
rest from -header, so the edges meet without a seam whichever of the two windows is on top.

Starý vzhled has no form (uitargetr1 makes it only for the R1 look); any failure is traced (uir1.TraceFailure) and
gives the drop panel and the table back as the separate boxes.
"""
import weakref

import chr
import ui

import uir1
import uir1layout as L
import uir1motion as M
import uir1tokens as T

SIDE = 12                  # section labels and the footer from the frame's edge (the DPS "Hráč")
RULE_IN = 8                # the rules' inset (the DPS RULE_INSET): one width in the whole form
SEC_H = 16                 # a section heading row: label, rule, count (20 before the spacing round of 9. 10.)
LOOT_GAP = 2               # heading -> the drop grid
QUEUE_TOP = 3              # a stone's queue hint row: 3 px under the Kořist heading,
QUEUE_H = 14               # 14 px high (the 12 px keys and the Tahoma 12 cell centred on it),
QUEUE_GAP = 6              # 6 px above the drop grid
QUEUE_KEYS = ('key_shift.png', 'key_mouse.png')    # FORM_ART, built at 67 % (29 x 12, 11 x 12): native size
QUEUE_SPACE = (4, 4, 6)    # Shift | "+" | mouse | the text
GRID_PAD = 4               # under the drop grid (6 before the spacing round)
BOTTOM = 4                 # under the last section's content (the DPS table has its own 4 px)
MIN_W = 300                # uidpsmeter.DpsMeterPanel.MIN_WIDTH: the form is at least as wide as the table
LABEL_GAP = 8              # label -> rule, rule -> count
FONT_ROLE = 'tahoma'

TEXTS = {'loot': (u'Kořist', u'Loot'), 'dps': (u'DPS', u'DPS'),
         'queue': (u'Fronta meteorů %d/%d', u'Meteor queue %d/%d'),
         'queue_short': (u'Fronta %d/%d', u'Queue %d/%d')}


def Make(board):
    """The form for an R1 board with the drop panel; None without the panel."""
    panel = getattr(board, 'target_details_thinboard', None)
    if panel is None or getattr(panel, 'r1look', None) is None:
        return None
    dps = getattr(board, 'dpsMeter', None)
    if dps is not None and getattr(dps, 'r1', None) is None:
        return None                     # the table in its own look: its ThinBoard corners do not fit one frame
    return TargetForm(board)


def _Label(key):
    import localeInfo
    czech, english = TEXTS[key]
    name = 'TARGET_FORM_' + key.upper()
    value = getattr(localeInfo, name, None)
    if value and value != name:
        return value
    try:
        import app
        path = str(app.GetLocalePath()).replace('\\', '/').lower().rstrip('/')
        return czech if path.endswith('cz') else english
    except Exception:
        return czech


def _Scissor(window):
    enable = getattr(window, 'EnableScissorRect', None)
    if enable is not None:
        enable()


class Section(object):
    """One section: a clipping window (its height is the unroll), the heading (label, rule, count) and the content
    panel at a fixed place inside (revealed by the bottom edge, never stretched)."""

    def __init__(self, parent, kit, key, content, content_y, count=False):
        self.key = key
        self.win = ui.Window()
        self.win.SetParent(parent)
        self.win.AddFlag('not_pick')
        self.win.SetWindowName('TargetFormSection_' + key)
        _Scissor(self.win)
        self.win.SetSize(1, 0)
        self.win.Hide()
        font = kit.font(FONT_ROLE)
        y = uir1.CellTop(SEC_H, font) - 1
        self.rule = uir1.Ops(self.win)               # under the texts
        self.label = uir1.Text(self.win, _Label(key), SIDE, y, font, T.INK_DIM, valign='top')
        self.count = uir1.Text(self.win, u'', 0, y, font, T.MUTED, align='right', valign='top') if count else None
        self.content = content
        self.content_y = content_y
        self.anim = M.Unroll(0)
        self.wanted = False
        self.width = 0
        self.countText = None
        content.SetParent(self.win)
        content.SetPosition(0, content_y)

    def Layout(self, width, count=None):
        """The heading at ``width``: "Kořist ——————— 19"."""
        text = u'' if count is None else u'%d' % count
        if width == self.width and text == self.countText:
            return
        self.width, self.countText = width, text
        x0 = SIDE + uir1.TextWidth(self.label) + LABEL_GAP
        x1 = width - RULE_IN
        if self.count is not None:
            self.count.SetText(text)
            self.count.SetPosition(width - RULE_IN, self.count.GetLocalPosition()[1])
            if text:
                x1 -= uir1.TextWidth(self.count) + LABEL_GAP
        self.rule.Apply(L.rule(x0, SEC_H // 2 - T.RULE_H // 2, x1 - x0))

    def SetContentY(self, y):
        if y != self.content_y:
            self.content_y = y
            self.content.SetPosition(0, y)

    def Place(self, y, width, height):
        if height <= 0:
            self.win.Hide()
            return
        self.win.SetPosition(0, y)
        self.win.SetSize(width, height)
        self.win.Show()

    def Height(self):
        return self.anim.Height()


class QueueHint(object):
    """A stone's hint line in the Kořist section: the Shift and right mouse keys (FORM_ART key_*.png, native size),
    "+" and "Fronta meteorů 2/5" (Tahoma 12, INK_DIM), all centred vertically on the QUEUE_H row and the whole line
    centred in the section. Widths are measured (images and texts); a line wider than the section takes the
    short text "Fronta 2/5". Made once; SetCount only re-texts."""

    def __init__(self, parent, kit):
        import uitargetr1
        font = kit.font(FONT_ROLE)
        self.font = font
        self.keys = []
        for name in QUEUE_KEYS:
            image = ui.ExpandedImageBox()
            image.SetParent(parent)
            image.AddFlag('not_pick')
            image.LoadImage(uitargetr1.FORM_ART.ROOT + name)
            self.keys.append(image)
        self.sizes = [tuple(uitargetr1.FORM_ART.SIZES[name]) for name in QUEUE_KEYS]
        self.plus = uir1.Text(parent, u'+', 0, 0, font, T.INK_DIM, valign='top', outline=True)
        self.label = uir1.Text(parent, u'', 0, 0, font, T.INK_DIM, valign='top', outline=True)
        self.state = None
        self.short = False
        self.Hide()

    def SetCount(self, count, capacity):
        state = (int(count), int(capacity))
        if state == self.state:
            return False
        self.state = state
        self.label.SetText(_Label('queue') % state)
        self.short = False
        return True

    def Width(self):
        shift, mouse = self.sizes
        gap1, gap2, gap3 = QUEUE_SPACE
        return shift[0] + gap1 + uir1.TextWidth(self.plus) + gap2 + mouse[0] + gap3 + uir1.TextWidth(self.label)

    def Layout(self, width, y):
        if self.state is not None and not self.short and self.Width() > width - 2 * SIDE:
            self.short = True
            self.label.SetText(_Label('queue_short') % self.state)
        total = self.Width()
        shift, mouse = self.sizes
        gap1, gap2, gap3 = QUEUE_SPACE
        text_y = y + uir1.CellTop(QUEUE_H, self.font)
        x = (width - total) // 2
        self.keys[0].SetPosition(x, y + (QUEUE_H - shift[1]) // 2)
        x += shift[0] + gap1
        self.plus.SetPosition(x, text_y)
        x += uir1.TextWidth(self.plus) + gap2
        self.keys[1].SetPosition(x, y + (QUEUE_H - mouse[1]) // 2)
        x += mouse[0] + gap3
        self.label.SetPosition(x, text_y)
        return total

    def Rects(self):
        """(x, y, w, h) of the Shift key, "+", the mouse key and the text, in the section (for the tests)."""
        out = []
        for image, size in zip(self.keys, self.sizes):
            out.append(tuple(image.GetLocalPosition()) + size)
        for line in (self.plus, self.label):
            out.append(tuple(line.GetLocalPosition()) + (uir1.TextWidth(line), uir1.FontCell(self.font)))
        return [out[0], out[2], out[1], out[3]]

    def Show(self):
        for widget in self.keys + [self.plus, self.label]:
            widget.Show()

    def Hide(self):
        for widget in self.keys + [self.plus, self.label]:
            widget.Hide()


class DpsChip(object):
    """The header's "DPS" switch (D2, FORM_ART dps_<open|closed>_<normal|hover>.png, 50 x 20: the label and a small
    R1 toggle, on while the section is open): opens / closes the DPS
    section like "?" opens / closes Kořist. No tooltip (owner 10. 10. 2026). A uikit.Interactive on the board;
    the form shows it only for a monster
    while the DPS meter is switched on in Settings."""

    def __init__(self, form, board, kit):
        import uikit
        import uitargetr1

        class Chip(uikit.Interactive):
            def paint(chip):
                state = ('open' if chip.opened else 'closed', 'hover' if (chip.hovered or chip.pressed) else 'normal')
                if state != chip.visual:
                    chip.visual = state
                    chip.image.LoadImage(uitargetr1.FORM_ART.ROOT + 'dps_%s_%s.png' % state)

        chip = Chip()
        chip.SetParent(board)
        chip.SetSize(uitargetr1.CHIP_W, uitargetr1.Q_SIZE)
        chip.image = ui.ExpandedImageBox()
        chip.image.SetParent(chip)
        chip.image.AddFlag('not_pick')
        chip.image.Show()
        chip.opened = False
        chip.visual = None
        formRef = weakref.ref(form)
        chip.SetEvent(lambda: formRef() is not None and formRef().ToggleDps())
        chip.paint()
        chip.Hide()
        self.widget = chip

    def SetOpened(self, opened):
        if bool(opened) != self.widget.opened:
            self.widget.opened = bool(opened)
            self.widget.paint()


class TargetForm(object):
    SIDE = SIDE

    def __init__(self, board):
        self.boardRef = weakref.ref(board)
        self.kit = uir1.Kit()
        self.inset = board.TARGET_CHROME_SIDE_INSET
        self.edge = L.frame_inset('window')
        self.width = 0
        self.header = 0
        self.placed = None
        self.broken = False
        self.updating = False

        body = ui.Window()
        body.SetWindowName('TargetFormBody')
        body.AddFlag('float')
        _Scissor(body)
        body.Hide()
        self.body = body
        # the frame of the whole form from -header (made first: under the sections), clipped to the body
        self.frame = uir1.Frame(body, 0, 0, 1, 1, 'window')
        inner = ui.Window()                          # the sections stop above the frame's bottom edge
        inner.SetParent(body)
        inner.AddFlag('not_pick')
        _Scissor(inner)
        inner.Show()
        self.inner = inner

        panel = board.target_details_thinboard
        panel.Hide()
        panel.SetForm(self, MIN_W)
        panel.r1look.SetEmbedded(True)
        self.loot = Section(inner, self.kit, 'loot', panel, SEC_H + LOOT_GAP, count=True)
        self.queue = QueueHint(self.loot.win, self.kit)
        self.queueShown = False
        self.dps = None
        self.chip = None
        self.autoKey = None        # (victim, encounter) of the last auto-open: once per fight
        table = getattr(board, 'dpsMeter', None)
        if table is not None:
            table.r1.SetEmbedded(True)
            table.SetFormEvents(self._OnDpsOver, self.Sync)
            table.compactFooter = True
            self.dps = Section(inner, self.kit, 'dps', table, SEC_H - table.TOP)
            self.chip = DpsChip(self, board, self.kit)
            board.r1look.chip = self.chip.widget
        self.sections = [section for section in (self.loot, self.dps) if section is not None]
        _Scissor(board)                              # the board shows only the header part of its long frame

    @property
    def board(self):
        return self.boardRef()

    # ------------------------------------------------------------------ state
    def Active(self):
        """A monster (or a stone) is the target of a shown R1 board."""
        board = self.board
        if board is None or self.broken or getattr(board, 'r1look', None) is None:
            return False
        vid = getattr(board, 'vid', 0)
        return bool(vid) and chr.GetInstanceType(vid) in (chr.INSTANCE_TYPE_ENEMY, chr.INSTANCE_TYPE_STONE)

    def _Meter(self):
        """The uidpsmeter module of the board's table (its master switch)."""
        import sys
        table = self.dps.content if self.dps is not None else None
        return sys.modules.get(type(table).__module__) if table is not None else None

    def DpsEnabled(self):
        meter = self._Meter()
        return meter is not None and meter.IsEnabled()

    def IsStone(self):
        board = self.board
        return board is not None and bool(board.vid) and chr.GetInstanceType(board.vid) == chr.INSTANCE_TYPE_STONE

    def QueueWanted(self):
        import app
        return getattr(app, 'ENABLE_AUTO_FARM_METIN', False) and self.IsStone()

    def RefreshQueue(self):
        """Board OnUpdate: the hint's numbers while it is shown."""
        if not self.queueShown:
            return
        try:
            import player
            if self.queue.SetCount(player.GetMetinQueueCount(), player.GetMetinQueueCapacity()):
                self.queue.Layout(self.width, SEC_H + QUEUE_TOP)
        except Exception:
            pass

    def DpsAuto(self):
        """The header switch: the player's saved preference (targetformprefs, per character)."""
        try:
            import targetformprefs
            return bool(targetformprefs.Get('dps_auto'))
        except Exception:
            return True

    def ToggleDps(self):
        """The "DPS" switch (D2) = the player's preference, saved per character: OFF closes the section and keeps
        it closed for every following target, fight and relog (no auto-open); ON opens it now (before any damage
        the empty table) and the auto-open on the first own hit works again."""
        if self.dps is None or not self.DpsEnabled():
            return
        on = not self.DpsAuto()
        try:
            import targetformprefs
            targetformprefs.Set('dps_auto', on)
        except Exception:
            pass
        table = self.dps.content
        self.dps.wanted = on
        if on:
            self.autoKey = (table.victimVid, table.encounterId) if table.snapshotRows else None
            if not table.IsShow():
                table.ShowEmpty()
        self.Sync()

    def MinBoardWidth(self):
        return MIN_W + 2 * self.inset if self.Active() else 0

    def BodyHeight(self):
        return sum(section.Height() for section in self.sections)

    def IsAnimating(self):
        return any(section.anim.IsAnimating() for section in self.sections)

    def Targets(self):
        """(Kořist, DPS) heights of the wanted state."""
        loot = self.loot
        dps_open = self.dps is not None and self.dps.wanted
        loot_h = 0
        if loot.wanted:
            loot_h = loot.content_y + loot.content.ContentHeight() + GRID_PAD + (0 if dps_open else BOTTOM)
        dps_h = 0
        if dps_open:
            table = self.dps.content
            dps_h = SEC_H - table.TOP + table.GetHeight()
        return loot_h, dps_h

    # ------------------------------------------------------------------ driving
    def Sync(self):
        """After any change of the board (UpdatePosition, a snapshot, "?", "Další"): the wanted sections, their
        target heights (a motion starts or turns), the width and the place under the board."""
        if self.updating:
            return
        self.updating = True
        refit = False
        try:
            refit = self._Sync()
        except Exception:
            self._Fail()
        finally:
            self.updating = False
        if refit:
            board = self.board
            if board is not None:
                board.UpdatePosition()          # the chip came or went: the header's width and its pair again

    def _Sync(self):
        board = self.board
        if board is None:
            return
        if not self.Active() or not board.IsShow():
            self._Reset()
            return False
        if self.chip is not None:
            chip = self.chip.widget
            want = self.DpsEnabled() and board.target_details_button.IsShow()
            if want != chip.IsShow():
                chip.Show() if want else chip.Hide()
                return True
        width = board.GetWidth() - 2 * self.inset
        if width != self.width:
            self.width = width
            self.loot.content.SetFormWidth(width)
            if self.dps is not None:
                self.dps.content.SetBlockWidth(width)
        panel = self.loot.content
        self.loot.wanted = panel.IsOpen()
        if self.dps is not None:
            table = self.dps.content
            if not self.DpsEnabled():
                self.dps.wanted = False
                self.autoKey = None               # switched on again: the next own hit opens it again
            elif not self.DpsAuto():
                self.dps.wanted = False           # the player switched it OFF: closed for every target and fight
            elif table.expiring:
                self.dps.wanted = False
            elif table.IsShow() and table.HasOwnRow():
                key = (table.victimVid, table.encounterId)
                if key != self.autoKey:
                    self.autoKey = key
                    self.dps.wanted = True        # your first damage in this fight: the section opens by itself
            elif not table.IsShow():
                self.dps.wanted = False
            if self.chip is not None:
                self.chip.SetOpened(self.DpsAuto())     # the switch shows the preference
        queue = self.QueueWanted()
        if queue != self.queueShown:
            self.queueShown = queue
            if queue:
                self.queue.state = None
                self.RefreshQueue()
                self.queue.Show()
            else:
                self.queue.Hide()
        self.loot.SetContentY(SEC_H + (QUEUE_TOP + QUEUE_H + QUEUE_GAP if queue else LOOT_GAP))
        if queue:
            self.queue.Layout(width, SEC_H + QUEUE_TOP)
        loot_h, dps_h = self.Targets()
        now = M.Now()
        was_closed = self.loot.Height() == 0 and not self.loot.anim.IsAnimating()
        if self.loot.anim.To(loot_h, now) and self.loot.wanted and was_closed:
            panel.StartCascade(M.Clock(now))      # its own clock: a turn of the unroll does not stall it
        if self.dps is not None:
            self.dps.anim.To(dps_h, now)
        self.loot.Layout(width, panel.DropCount() if self.loot.wanted or panel.IsShow() else None)
        if self.dps is not None:
            self.dps.Layout(width)
        self._Apply()
        return False

    def Update(self):
        """Once a frame (TargetBoard.OnUpdate): advances the motions; returns at once at rest."""
        if not self.sections:
            return
        panel = self.loot.content
        if panel.cascade is None and not self.IsAnimating():
            return
        try:
            now = M.Now()
            changed = False
            for section in self.sections:
                changed = section.anim.Update(now) or changed
            if panel.cascade is not None:
                panel.cascade[0].Tick(now)
                panel.StepCascade()
            if changed or not self.IsAnimating():
                self._Apply()
        except Exception:
            self._Fail()

    def _Apply(self):
        """Places the body, the sections and the frame for the current heights; hides what finished collapsing."""
        board = self.board
        loot_h = self.loot.Height()
        dps_h = self.dps.Height() if self.dps is not None else 0
        body_h = loot_h + dps_h
        look = getattr(board, 'r1look', None)
        if look is not None:
            look.SetFormExtra(body_h)
        if not self.loot.wanted and loot_h == 0 and not self.loot.anim.IsAnimating():
            if self.loot.content.IsShow():
                self.loot.content.FormHide()
        if self.dps is not None and not self.dps.wanted and dps_h == 0 and not self.dps.anim.IsAnimating():
            table = self.dps.content
            if table.expiring:
                table.Reset()
                if table.expireEvent:
                    table.expireEvent()
            elif table.IsShow() and not table.snapshotRows:
                table.Hide()                   # the empty table opened by the chip
        if body_h <= 0:
            if self.body.IsShow():
                self.body.Hide()
            return
        width = self.width
        header = board.GetHeight()
        bx, by = board.GetGlobalPosition()
        place = (bx + self.inset, by + header, width, body_h, header)
        if place != self.placed:
            self.placed = place
            self.body.SetPosition(bx + self.inset, by + header)
            self.body.SetSize(width, body_h)
            self.frame.SetPosition(0, -header)
            self.frame.Resize(width, header + body_h)
            self.inner.SetSize(width, max(0, body_h - self.edge))
        self.loot.Place(0, width, loot_h)
        if self.dps is not None:
            self.dps.Place(loot_h, width, dps_h)
        if not self.body.IsShow():
            self.body.Show()
            self.body.SetTop()

    def _OnDpsOver(self):
        """The table's end (15 s after the kill, 5 s without a snapshot): the section collapses, the table resets
        at the end of the collapse (_Apply)."""
        if self.dps is not None:
            self.dps.wanted = False
        self.Sync()

    def _Reset(self):
        for section in self.sections:
            section.wanted = False
            section.anim.Set(0)
            section.win.Hide()
        self.autoKey = None
        if self.chip is not None:
            self.chip.SetOpened(self.DpsAuto())
        panel = self.loot.content
        panel.cascade = None
        if panel.IsShow() and not panel.IsOpen():
            panel.FormHide()
        board = self.board
        look = getattr(board, 'r1look', None) if board is not None else None
        if look is not None:
            look.SetFormExtra(0)
        self.placed = None
        self.body.Hide()

    def Reset(self):
        """Another target, the board closed or hidden: everything closed at once (no motion)."""
        try:
            self._Reset()
        except Exception:
            self._Fail()

    # ------------------------------------------------------------------ failure / teardown
    def _Fail(self):
        uir1.TraceFailure('the target form')
        self.broken = True
        board = self.board
        if board is not None and getattr(board, 'form', None) is self:
            board.form = None
        self.Destroy(restore=True)
        if board is not None:
            try:
                board.UpdatePosition()
            except Exception:
                pass

    def Destroy(self, restore=False):
        """Takes the form down. ``restore`` (a failure, the R1 look reverted): the drop panel and the table come
        back as the separate boxes (the original placement of uitarget). A window cannot leave its parent in the
        engine (CWindowManager::SetParent needs one), so the board then gets a new floating drop panel; the table
        goes back under the board. Without ``restore`` (the board is destroyed) nothing new is made."""
        board = self.board
        try:
            self.body.Hide()
            panel = self.loot.content
            panel.cascade = None
            opened = panel.IsOpen()
            panel.opened = False
            panel.Hide()
            panel.parent = panel.owner = None
            if restore and board is not None and getattr(board, 'target_details_thinboard', None) is panel:
                fresh = panel.__class__(board)
                fresh.Hide()
                board.target_details_thinboard = fresh
                if opened and getattr(board, 'race_vnum', 0):
                    fresh.Open(board.race_vnum)
            if self.dps is not None:
                table = self.dps.content
                table.SetFormEvents(None, None)
                if table.expiring:
                    table.Reset()
                if board is not None:
                    table.SetParent(board)
                if table.r1 is not None:
                    table.r1.SetEmbedded(False)
            if board is not None:
                disable = getattr(board, 'DisableScissorRect', None)
                if disable is not None:
                    disable()
                look = getattr(board, 'r1look', None)
                if look is not None:
                    look.SetFormExtra(0)
            if self.chip is not None:
                self.chip.widget.Hide()
                if board is not None and getattr(board, 'r1look', None) is not None:
                    board.r1look.chip = None
        except Exception:
            uir1.TraceFailure('the target form (teardown)')
        self.sections = []
