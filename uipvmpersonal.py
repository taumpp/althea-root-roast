# -*- coding: utf-8 -*-
"""Two-hour personal bonuses using native skill icons and the shared notice queue."""
import weakref
import math
import app
import dbg
import fontconfig
import grp
import net
import player
import skill
import ui
import uiToolTip
import uiAffectShower
import uiaffecthover
import wndMgr
import pvmhudposition
import pvmpersonal as policy
import pvmpersonaltext as labels


class DragHeader(ui.Window):
    def __init__(self, owner):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.SetParent(owner)
        self.SetPosition(0, 0)
        self.AddFlag('dragable')
        self.Show()

    def OnMouseLeftButtonDown(self):
        self.owner.BeginDrag()
        return True

    def OnMouseDrag(self, x, y):
        self.owner.Drag()

    def OnMouseLeftButtonUp(self):
        self.owner.EndDrag()
        return True


class BonusButton(ui.Window):
    def __init__(self, owner, source):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.source = source
        self.SetParent(owner)
        self.SetSize(36, 50)
        self.slot = ui.SlotWindow()
        self.slot.SetParent(self)
        self.slot.AddFlag('not_pick')
        self.slot.SetPosition(2, 1)
        self.slot.SetSize(32, 32)
        self.slot.AppendSlot(0, 0, 0, 32, 32)
        self.slot.Show()
        self.label = ui.TextLine()
        self.label.SetParent(self)
        self.label.AddFlag('not_pick')
        self.label.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE, 0))
        self.label.SetHorizontalAlignCenter()
        self.label.SetPosition(18, 35)
        self.label.SetOutline()
        self.label.Show()
        self.edges = []
        for x, y, width, height in ((0, 0, 36, 1), (0, 33, 36, 1), (0, 0, 1, 34), (35, 0, 1, 34)):
            bar = ui.Bar()
            bar.SetParent(self)
            bar.AddFlag('not_pick')
            bar.SetPosition(x, y)
            bar.SetSize(width, height)
            bar.Show()
            self.edges.append(bar)
        self.visual = None
        self.hover = False
        self.label_key = None
        self.next_tooltip = 0.0
        self.tooltip_serial = None

    def Refresh(self, now):
        row = self.owner.model.rows[self.source]
        left = self.owner.model.remaining(self.source, now)
        active = left > 0
        visual = (row['learned'], active)
        if visual != self.visual:
            icon = skill.GetIconImageNew(self.source, policy.icon_grade(row['learned']))
            tint = (1.0, 1.0, 1.0, 1.0) if active else (0.38, 0.38, 0.38, 1.0)
            # SetSlot's same-item fast path does not update the diffuse color.
            self.slot.ClearSlot(0)
            self.slot.SetSlot(0, self.source, 1, 1, icon, tint)
            if active:
                self.slot.ActivateSlotOld(0)
            else:
                self.slot.DeactivateSlot(0)
            self.visual = visual
        label_key = (labels.timer(left) if active else labels.text('ON') if row['learned'] else '--',
            0xffDAB77C - 0x100000000 if 0 < left <= 300 else labels.VALUE_COLOR if active else labels.MUTED_COLOR)
        if label_key != self.label_key:
            self.label.SetText(label_key[0])
            self.label.SetPackedFontColor(label_key[1])
            self.label_key = label_key
        if active:
            self.owner.pulses.pop(self.source, None)
        pulse = self.owner.pulses.get(self.source, 0)
        elapsed = now - pulse
        glow = 0.3 + 0.6 * max(0.0, math.sin(elapsed * math.pi)) if pulse and 0 <= elapsed < 6 else 0.3
        color = grp.GenerateColor(0.78, 0.63, 0.39, 0.9 if active else glow if self.hover or pulse else 0.25)
        for edge in self.edges:
            edge.SetColor(color)

    def RefreshTooltip(self, now):
        serial = self.owner.model.serial
        if self.hover and (now >= self.next_tooltip or serial != self.tooltip_serial):
            # Advance before rendering: an error must never cause a frame loop.
            self.next_tooltip = now + 1.0
            self.tooltip_serial = serial
            self.owner.ShowTooltip(self.source)

    def OnMouseLeftButtonUp(self):
        self.owner.Request(self.source, not self.owner.model.remaining(self.source, app.GetTime()))
        return True

    def OnMouseRightButtonUp(self):
        self.owner.Request(self.source, False)
        return True

    # The Pasivky row under the effect bar shares the bar's one hover surface (root/uiaffecthover.py): a fast move
    # between the two never leaves two tooltips, Over B before Out A never hides B, and two buttons are never hovered.
    def ShowHover(self):
        self.hover = True
        self.next_tooltip = 0.0
        self.RefreshTooltip(app.GetTime())
        button = weakref.ref(self)
        tooltip = self.owner.tooltip

        def hide():
            alive = button()
            if alive is not None:
                alive.hover = False
            tooltip.HideToolTip()
        return hide

    def OnMouseOverIn(self):
        uiaffecthover.Over(self)

    def OnMouseOverOut(self):
        uiaffecthover.Out(self)


class PersonalBonuses(ui.Window):
    # Every passive shows the tile the skill window shows for its skill
    # (uiAffectShower.CurrentSkillIcon reads it from SkillDesc.txt). The skill
    # vnum is never matched against affect numbers: AFFECT_POISON is 3 and
    # AFFECT_SLOW is 4, which gave Bojove zureni and Aura mece their icons.

    def __init__(self, parent, affect_shower, interface):
        ui.Window.__init__(self)
        # Keep the movable panel in UI; GameWindow is in the lower GAME layer.
        self.AddFlag('float')
        self.parent_window = weakref.proxy(parent)
        self.character = player.GetName()
        self.saved_position = pvmhudposition.load(self.character)
        self.drag_origin = None
        self.drag_moved = False
        self.affects = weakref.proxy(affect_shower)
        self.interface = weakref.proxy(interface)
        self.model = policy.Model()
        policy.restore_warp(player.GetName(), self.model)
        if hasattr(player, 'SetPvmPersonalVersion'):
            player.SetPvmPersonalVersion(0)
        policy.set_current(self.model)
        self.buttons = {}
        self.cast_images = {}
        self.pulses = {}
        self.pending_notice = None
        self.next_notice = 0.0
        self.next_command = 0.0
        self.pending_activation = None
        self.next_sync = 0.0
        self.cast_key = None
        self.tooltip = uiToolTip.SkillToolTip()
        self.tooltip_error = None
        self.header = DragHeader(self)
        self.header_background = ui.Bar()
        self.header_background.SetParent(self.header)
        self.header_background.AddFlag('not_pick')
        self.header_background.SetColor(grp.GenerateColor(0.03, 0.03, 0.03, 0.6))
        self.header_background.Show()
        self.grip = []
        for x in (2, 5):
            for y in (3, 6, 9):
                dot = ui.Bar()
                dot.SetParent(self.header)
                dot.AddFlag('not_pick')
                dot.SetPosition(x, y)
                dot.SetSize(1, 1)
                dot.SetColor(grp.GenerateColor(0.74, 0.66, 0.53, 1.0))
                dot.Show()
                self.grip.append(dot)
        self.heading = ui.TextLine()
        self.heading.SetParent(self.header)
        self.heading.AddFlag('not_pick')
        self.heading.SetPosition(11, 0)
        self.heading.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE, 0))
        self.heading.SetPackedFontColor(0xffBDA886 - 0x100000000)
        self.heading.SetText(labels.text('TITLE'))
        self.heading.Show()
        self.Hide()

    def _ClampedPosition(self, position):
        return pvmhudposition.clamp(position, (self.GetWidth(), self.GetHeight()),
                                    (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()))

    def _Place(self, position):
        x, y = self._ClampedPosition(position)
        self.SetPosition(x, y)

    def OnUpdate(self):
        if not self.parent_window.IsShow():
            self.EndDrag()
            self.tooltip.HideToolTip()
            self.Hide()

    def BeginDrag(self):
        if not self.model.enabled or not self.IsShow():
            return
        self.tooltip.HideToolTip()
        for button in self.buttons.values():
            button.hover = False
        self.SetTop()
        self.drag_origin = (wndMgr.GetMousePosition(), self.GetGlobalPosition())
        self.drag_moved = False

    def Drag(self):
        if self.drag_origin is None:
            return
        (mx, my), (x, y) = self.drag_origin
        px, py = wndMgr.GetMousePosition()
        if (px, py) != (mx, my) or self.drag_moved:
            self.drag_moved = True
            self.saved_position = self._ClampedPosition((x + px - mx, y + py - my))
            self._Place(self.saved_position)

    def EndDrag(self):
        if self.drag_origin is None:
            return
        self.drag_origin = None
        if self.drag_moved and self.saved_position is not None:
            pvmhudposition.save(self.character, self.saved_position)
        self.drag_moved = False

    def Snapshot(self, version, server_time, wire_job, wire_group, serial,
                 attack_skill, attack_hud, attack_learned, attack_activated,
                 attack_revision, attack_end, attack_value, attack_power,
                 attack_notice, attack_status,
                 defense_skill, defense_hud, defense_learned, defense_activated,
                 defense_revision, defense_end, defense_value, defense_power,
                 defense_notice, defense_status,
                 reduction_skill, reduction_hud, reduction_learned, reduction_activated,
                 reduction_revision, reduction_end, reduction_value, reduction_power,
                 reduction_notice, reduction_status):
        # stringcommander forwards only declared positional arguments. Keep
        # this signature aligned with the server's five-header/three-row wire.
        arguments = (version, server_time, wire_job, wire_group, serial,
                     attack_skill, attack_hud, attack_learned, attack_activated,
                     attack_revision, attack_end, attack_value, attack_power,
                     attack_notice, attack_status,
                     defense_skill, defense_hud, defense_learned, defense_activated,
                     defense_revision, defense_end, defense_value, defense_power,
                     defense_notice, defense_status,
                     reduction_skill, reduction_hud, reduction_learned, reduction_activated,
                     reduction_revision, reduction_end, reduction_value, reduction_power,
                     reduction_notice, reduction_status)
        race = net.GetMainActorRace()
        jobs = (0, 1, 2, 3, 0, 1, 2, 3, 4)
        job = jobs[race] if 0 <= race < len(jobs) else -1
        if self.model.accept(arguments, app.GetTime(), job, net.GetMainActorSkillGroup()):
            if hasattr(player, 'SetPvmPersonalVersion'):
                player.SetPvmPersonalVersion(1)
            self.Update()

    def Request(self, source, on):
        now = app.GetTime()
        if not self.model.enabled or self.drag_origin is not None or now < self.next_command:
            return
        row = self.model.rows.get(source)
        if not row or not row['learned']:
            return
        if self.pending_activation:
            pending_source, revision, deadline = self.pending_activation
            pending_row = self.model.rows.get(pending_source)
            if pending_row and pending_row['revision'] == revision and now < deadline:
                return
            self.pending_activation = None
        command = self.model.command(source, on, now)
        if command:
            if on and source in policy.CAST_SKILLS:
                self.pending_activation = (source, row['revision'], now + 2.0)
            net.SendChatPacket(command)
            self.next_command = now + 0.3
            self.next_sync = now + 1.0

    def ShowTooltip(self, source):
        try:
            self.tooltip.ClearToolTip()
            self.tooltip.SetPersonalStyle()
            self.tooltip.SetTitle(labels.title(source, skill.GetSkillName(source), app.GetTime()))
            if not labels.append_bonus(self.tooltip, source, app.GetTime(), passive_only=True):
                self.tooltip.HideToolTip()
                return
            self.tooltip.ShowToolTip()
            self.tooltip_error = None
        except Exception as error:
            # Only tooltip presentation is contained. Snapshot validation and
            # activation errors must retain their normal diagnostics.
            self.tooltip.HideToolTip()
            identity = (source, type(error).__name__, str(error))
            if identity != self.tooltip_error:
                self.tooltip_error = identity
                import traceback
                dbg.TraceError('PvM tooltip failed for skill %d:\n%s' % (source, traceback.format_exc()))

    def _CastImages(self, now):
        active = tuple((r['skill'], r['revision']) for r in self.model.rows.values()
            if self.model.remaining(r['skill'], now))
        if active == self.cast_key and self.affects.pvmPersonalImages == self.cast_images:
            return
        for image in self.cast_images.values():
            image.Hide()
        self.cast_images = {}
        for source, unused_revision in active:
            affect = uiAffectShower.SkillToAffect(source, self.affects.AFFECT_DATA_DICT)
            raw = source if affect is None else affect
            fallback = self.affects.AFFECT_DATA_DICT.get(affect, (None, ''))[1]
            filename = uiAffectShower.CurrentSkillIcon(fallback, source)
            if not filename:
                continue
            # Summary membership never replaces the separate activation controls.
            image = uiAffectShower.AffectImage()
            image.SetParent(self.affects)
            image.skillIconSource = (fallback, source)
            image.LoadImage(filename)
            image.SetScale(0.7, 0.7)
            image.SetSize(22, 22)
            image.SetAffect(raw)
            image.SetSkillAffectFlag(True)
            image.SetDescription(skill.GetSkillName(source))
            image.SetEndTime(self.model.rows[source]['end'])
            image.pvmPersonalSkill = source
            self.cast_images[source] = image
        self.cast_key = active
        self.affects.SetPvmPersonalImages(self.cast_images)

    def _Notices(self, now):
        board = self.interface.noticeBoard
        if self.pending_notice:
            message, identities = self.pending_notice
            valid = self.model.notices()
            if any(identity not in valid for identity in identities):
                board.Remove(message)
                self.pending_notice = None
                self.next_notice = now
        if self.pending_notice:
            message, identities = self.pending_notice
            if board.active == (1, message) and board.IsShow() and now - board.started >= 0.25:
                self.model.displayed(identities)
                for source, unused_revision in identities:
                    self.pulses[source] = now
                self.pending_notice = None
            elif now >= self.next_notice:
                # A full queue or disabled notices must not falsely acknowledge.
                self.pending_notice = None
        if not self.pending_notice and now >= self.next_notice:
            identities = self.model.notices()
            if identities:
                names = ', '.join(skill.GetSkillName(source) for source, revision in identities)
                key = 'RECAST' if any(source in policy.CAST_SKILLS for source, revision in identities) else 'EXPIRED'
                message = labels.text(key) % names
                if board.Add(message, 1, hold=7.5):
                    self.pending_notice = (message, identities)
                self.next_notice = now + 30
        if now >= self.next_command:
            command = self.model.next_ack()
            if command:
                net.SendChatPacket(command)
                self.next_command = now + 0.3

    def Update(self):
        if not self.model.enabled:
            return
        race = net.GetMainActorRace()
        jobs = (0, 1, 2, 3, 0, 1, 2, 3, 4)
        identity = (jobs[race] if 0 <= race < len(jobs) else -1, net.GetMainActorSkillGroup())
        if identity != self.model.identity:
            self.EndDrag()
            self.model.enabled = False
            self.affects.SetPvmPersonalImages({})
            self.cast_key = None
            if self.pending_notice:
                self.interface.noticeBoard.Remove(self.pending_notice[0])
                self.pending_notice = None
            if hasattr(player, 'SetPvmPersonalVersion'):
                player.SetPvmPersonalVersion(0)
            self.tooltip.HideToolTip()
            self.Hide()
            return
        now = app.GetTime()
        wanted = [r['skill'] for r in self.model.control_rows()]
        title_width, title_height = self.heading.GetTextSize()
        header_height = max(18, title_height + 4)
        for source in list(self.buttons):
            if source not in wanted:
                button = self.buttons.pop(source)
                button.hover = False
                button.Hide()
                self.tooltip.HideToolTip()
        for index, source in enumerate(wanted):
            if source not in self.buttons:
                self.buttons[source] = BonusButton(self, source)
            button = self.buttons[source]
            button.SetPosition(index * 40, header_height + 1)
            button.Refresh(now)
            button.Show()
        # The confirmed two-hour state also owns ordinary skill highlights
        # and the native second-use path, independently of visual affects.
        if hasattr(player, 'SetPvmPersonalSkillActive'):
            for source in self.model.rows:
                if source in policy.CAST_SKILLS:
                    player.SetPvmPersonalSkillActive(source, bool(self.model.remaining(source, now)))
        self._CastImages(now)
        width = max(52, title_width + 12, len(wanted)*40-4) if wanted else 0
        self.SetSize(width, header_height + 51 if wanted else 0)
        self.header.SetSize(width, header_height)
        self.header_background.SetSize(width, header_height)
        self.heading.SetPosition(11, (header_height - title_height) // 2)
        if wanted:
            if self.saved_position is None:
                x, y = self.affects.GetGlobalPosition()
                self._Place((x, y + self.affects.GetHeight() + 8))
            else:
                self._Place(self.saved_position)
            if self.parent_window.IsShow():
                self.Show()
            else:
                self.OnUpdate()
        else:
            self.EndDrag()
            self.tooltip.HideToolTip()
            self.Hide()
        if self.next_sync and now >= self.next_sync and now >= self.next_command:
            net.SendChatPacket('/pvm_bonus sync')
            self.next_command = now + 0.3
            self.next_sync = 0.0
        self._Notices(now)
        # Hover rendering must not interrupt core state, icon or notice work.
        for button in self.buttons.values():
            button.RefreshTooltip(now)

    def Destroy(self, warping=False):
        self.EndDrag()
        if warping:
            policy.save_warp(player.GetName(), self.model)
        else:
            policy.clear_warp()
        if hasattr(player, 'SetPvmPersonalVersion'):
            player.SetPvmPersonalVersion(0)
        self.Hide()
        self.tooltip.HideToolTip()
        self.affects.SetPvmPersonalImages({})
        for button in self.buttons.values():
            button.Hide()
        self.buttons = {}
        self.cast_images = {}
        self.pending_notice = None
        self.pending_activation = None
        policy.set_current(None)
