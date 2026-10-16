# -*- coding: utf-8 -*-
"""Compact B research trays, driven by server snapshots (legacy compatible)."""
import bonuscolor
import app
import item
import net
import player
import osfInfo
import ui
import uicrimsoncontrols
import biologresearchmodel as model
import uiBiolog as legacy
from uicrimsonember import SettingsScrollBar
from uiToolTip import ToolTip, GET_AFFECT_STRING

ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/biolog/research/"
CHECKBOX_ROOT = "d:/ymir work/ui/game/crimson_ember/gameoption/"
WIDTH, HEIGHT = 720, 446
ROW_X, ROW_Y = 20, 92
ROW_STEP, VISIBLE_ROWS = 84, 4
ELIXIR_X, CLOCK_X = 392, 454
GOLD, WHITE, MUTED = 0xffffcf6c, 0xffeee6dc, 0xffa99f94
GREEN, AMBER, RED, BLUE = 0xff72c66a, 0xffdea435, 0xffe04457, 0xff69a7d7
_REMINDERS = {}  # character/research/due survives same-character warp reconstruction
ACCELERATOR_VNUM = 72357
LEGACY_CLOCK_VNUM = 72347


def Text(key, fallback):
    return legacy._Text(key, fallback)


def Tint(widget, color):
    # Native bindings accept float RGB reliably, including values above INT_MAX.
    widget.SetFontColor(((color >> 16) & 255) / 255.0,
                        ((color >> 8) & 255) / 255.0, (color & 255) / 255.0)


def Line(parent, x, y, value="", font="Tahoma:12", color=WHITE, center=False):
    line = ui.TextLine()
    line.SetParent(parent)
    line.SetPosition(x, y)
    line.SetFontName(font)
    line.SetText(value)
    Tint(line, color)
    if center:
        line.SetHorizontalAlignCenter()
    line.AddFlag("not_pick")
    line.Show()
    return line


def Image(parent, x, y, name):
    image = ui.ImageBox()
    image.SetParent(parent)
    image.SetPosition(x, y)
    image.LoadImage(ASSET_ROOT + name + ".png")
    image.AddFlag("not_pick")
    image.Show()
    return image


class IconButton(ui.Button):
    def __init__(self, parent, x, y, family, action, over=None, out=None):
        ui.Button.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetUpVisual(ASSET_ROOT + family + "_normal.png")
        self.SetOverVisual(ASSET_ROOT + family + "_hover.png")
        self.SetDownVisual(ASSET_ROOT + family + "_pressed.png")
        self.SetDisableVisual(ASSET_ROOT + family + "_disabled.png")
        self.SetEvent(action)
        self.over = over
        self.out = out
        self.Show()

    def OnMouseOverIn(self):
        if self.over:
            self.over()

    def OnMouseOverOut(self):
        if self.out:
            self.out()


class Booster(ui.Window):
    """The checkbox and its cost share a generous hit rectangle."""
    def __init__(self, parent, x, callback, tooltip, hide):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x, 24)
        self.SetSize(58, 28)
        self.callback, self.tooltip, self.hide = callback, tooltip, hide
        self.check = ui.ImageBox()
        self.check.SetParent(self)
        self.check.SetPosition(0, 7)
        self.check.AddFlag("not_pick")
        self.check.Show()
        self.count = Line(self, 20, 5, "1 ks", color=GOLD)
        self.count.SetLimitWidth(36)
        self.enabled = False
        self.Show()

    def Refresh(self, selected, cost, owned, enabled):
        self.enabled = enabled
        state = "selected" if selected else "unselected"
        self.check.LoadImage(CHECKBOX_ROOT + "checkbox_" + state + ".tga")
        self.count.SetText("%d ks" % cost)
        Tint(self.count, (GOLD if owned >= cost else RED) if enabled else MUTED)

    def OnMouseLeftButtonUp(self):
        if self.enabled:
            self.callback()
        return True

    def OnMouseOverIn(self):
        self.tooltip()

    def OnMouseOverOut(self):
        self.hide()


class ResearchRow(ui.Window):
    def __init__(self, owner, offset):
        ui.Window.__init__(self)
        self.owner = owner
        self.index = 0
        self.SetParent(owner)
        self.SetPosition(ROW_X, ROW_Y + offset * ROW_STEP)
        self.SetSize(670, 78)
        self.plate = Image(self, 0, 4, "level_badge_B")
        self.surface = Image(self, 52, 0, "tray_normal")
        self.level = Line(self, 20, 28, font="Tahoma:18b", color=GOLD, center=True)
        self.icon = ui.ImageBox()
        self.icon.SetParent(self)
        self.icon.SetPosition(88, 22)
        self.icon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverItem)
        self.icon.SAFE_SetStringEvent("MOUSE_OVER_OUT", owner.HideTooltip)
        self.icon.Show()
        self.name = Line(self, 146, 11, font="Tahoma:13b")
        self.name.SetLimitWidth(238)
        self.intervalLabel = Line(self, 146, 29, Text("BIO_RESEARCH_DURATION", u"Výzkum:"), "Tahoma:11", MUTED)
        self.interval = Line(self, 197, 29, font="Tahoma:11b", color=BLUE)
        self.status = Line(self, 279, 29, font="Tahoma:11", color=GREEN)
        self.status.SetLimitWidth(101)
        self.track = Image(self, 146, 46, "progress_parent_track_127x12")
        self.fill = ui.ExpandedImageBox()
        self.fill.SetParent(self)
        self.fill.SetPosition(150, 50)
        self.fill.LoadImage(ASSET_ROOT + "progress_parent_fill_119x4.png")
        self.fill.AddFlag("not_pick")
        self.fill.Show()
        self.progress = Line(self, 283, 44, color=GOLD)
        self.elixir = Booster(self, ELIXIR_X, lambda: self.Toggle(0), lambda: self.BoosterTip(0), owner.HideTooltip)
        self.clock = Booster(self, CLOCK_X, lambda: self.Toggle(1), lambda: self.BoosterTip(1), owner.HideTooltip)
        self.alarm = IconButton(self, 518, 24, "icon_button", self.ToggleAlarm,
                                self.AlarmTip, owner.HideTooltip)
        self.bell = Image(self.alarm, 4, 4, "alarm")
        self.reward = IconButton(self, 552, 22, "reward", self.Rewards,
                                 self.Rewards, owner.HideTooltip)
        self.submit = IconButton(self, 590, 16, "submit", self.Submit,
                                 self.SubmitTip, owner.HideTooltip)
        # Keep the level badge readable; two veils quiet the tray underneath.
        self.lockVeil = Image(self, 52, 0, "lock_veil_618x78")
        self.lockShade = Image(self, 52, 0, "lock_veil_618x78")
        self.lockGlyph = Image(self, 345, 17, "lock_gate_32x44")
        self.lockVeil.Hide()
        self.lockShade.Hide()
        self.lockGlyph.Hide()
        self.Show()

    def Data(self):
        return self.owner.researches[self.index]

    def SetIndex(self, index):
        if self.index != index:
            self.owner.HideTooltip()
        self.index = index
        data = self.Data()
        self.level.SetText("-" if data["level"] <= 1 else str(data["level"]))
        self.name.SetText(legacy._ItemName(data["vnum"]))
        self.interval.SetText(model.duration(data["interval"]))
        vnum = data["stone"] if model.phase(data) == "stone" else data["vnum"]
        path = legacy._ItemIcon(vnum)
        if path:
            self.icon.LoadImage(path)
            self.icon.Show()
        else:
            self.icon.Hide()
        self.Refresh()

    def Refresh(self):
        data = self.Data()
        state = model.phase(data)
        available = self.owner.Available(self.index)
        remaining = max(0, data["due"] - app.GetGlobalTimeStamp())
        selected = self.owner.boosters.setdefault(self.index, [False, False])
        self.elixir.Refresh(selected[0], data["elixir_cost"], self.owner.Owned(data["elixir"]), available and state == "mission")
        self.clock.Refresh(selected[1], data["clock_cost"], self.owner.Owned(data["clock"]), available and state == "mission")
        self.progress.SetText("%d / %d" % (min(data["count"], data["total"]), data["total"]))
        self.fill.SetRenderingRect(0.0, 0.0, min(1.0, float(data["count"]) / data["total"]) - 1.0, 0.0)
        if state == "completed":
            caption, color = Text("BIO_COMPLETED", u"Dokončeno"), GOLD
        elif not available:
            caption, color = Text("BIO_LOCKED", u"Uzamčeno"), MUTED
        elif state == "stone":
            caption, color = Text("BIO_SOUL_STONE_SHORT", u"Kámen duše"), AMBER
        elif state == "gift":
            caption, color = Text("BIO_CHOOSE_SHORT", u"Vyber odměnu"), GOLD
        elif remaining:
            caption, color = model.duration(remaining), AMBER
        elif self.owner.Owned(data["vnum"]) < 1:
            caption, color = Text("BIO_MISSING_ITEM", u"Chybí předmět"), RED
        else:
            caption, color = Text("BIO_READY_SHORT", u"Připraveno"), GREEN
        self.status.SetText(caption)
        Tint(self.status, color)
        Tint(self.name, WHITE if available or data["done"] else MUTED)
        self.surface.LoadImage(ASSET_ROOT + ("tray_waiting.png" if remaining and state == "mission" else "tray_normal.png"))
        self.alarm.SetUpVisual(ASSET_ROOT + ("icon_button_selected.png" if data["alarm"] else "icon_button_normal.png"))
        if available and not data["done"]:
            self.alarm.Enable()
        else:
            self.alarm.Disable()
        enabled = self.owner.CanSubmit(self.index)
        if enabled:
            self.submit.Enable()
        else:
            self.submit.Disable()
        if player.GetStatus(player.LEVEL) < data["level"]:
            self.lockVeil.Show()
            self.lockShade.Show()
            self.lockGlyph.Show()
        else:
            self.lockVeil.Hide()
            self.lockShade.Hide()
            self.lockGlyph.Hide()

    def Toggle(self, kind):
        selected = self.owner.boosters.setdefault(self.index, [False, False])
        selected[kind] = not selected[kind]
        self.Refresh()

    def ToggleAlarm(self):
        self.owner.SetAlarm(self.index, not self.Data()["alarm"])

    def Submit(self):
        self.owner.Submit(self.index)

    def OverItem(self):
        data = self.Data()
        self.owner.ItemTooltip(data["stone"] if model.phase(data) == "stone" else data["vnum"])

    def Rewards(self):
        self.owner.Rewards(self.index)

    def BoosterTip(self, kind):
        data = self.Data()
        key = "clock" if kind else "elixir"
        title = Text("BIO_CLOCK_NAME", u"Biologist's Accelerator") if kind else legacy._ItemName(data[key])
        self.owner.Tooltip(title, [
            Text("BIO_HELPER_COST", u"Potřeba: %d ks") % data[key + "_cost"],
            Text("BIO_HELPER_OWNED", u"V batohu: %d ks") % self.owner.Owned(data[key]),
            Text("BIO_CLOCK_HINT", u"Přeskočí zbývající čas výzkumu.") if kind else
            Text("BIO_ELIXIR_HINT", u"Pomůže s přijetím odevzdaného předmětu."),
        ])

    def AlarmTip(self):
        self.owner.Tooltip(Text("BIO_ALARM_TITLE", u"Budík"), [
            Text("BIO_ALARM_HINT", u"Upozornit, až půjde tento výzkum znovu odevzdat.")])

    def SubmitTip(self):
        data = self.Data()
        vnum = data["stone"] if model.phase(data) == "stone" else data["vnum"]
        self.owner.Tooltip(Text("BIO_SUBMIT_ITEM", u"Odevzdat"), [legacy._ItemName(vnum),
            Text("BIO_HELPER_OWNED", u"V batohu: %d ks") % self.owner.Owned(vnum)])


class BiologWindow(ui.Window):
    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag("float")
        self.AddFlag("movable")
        self.SetWindowName("BiologWindow")
        self.SetSize(WIDTH, HEIGHT)
        self.SetCenterPosition()
        self.children = []
        self.researches = {}
        self.boosters = {}
        self.pending = {}
        self.snapshot = model.Snapshot()
        self.modern = False
        self.dataKnown = False
        self.legacyIndex = 0
        self.tab = 0
        self.start = 0
        self.nextTick = 0
        self.nextRequest = 0
        self.choiceIndex = 0
        self.choiceWindow = None
        self.tooltip = ToolTip(320)
        self.tooltip.HideToolTip()
        self.body = Image(self, 0, 0, "D8_shell_720")
        self.portrait = Image(self, 618, 25, "chaegirab_header")
        self.titleBar = ui.TitleBar()
        self.titleBar.SetParent(self)
        self.titleBar.MakeTitleBar(WIDTH, "red")
        # Parenting alone does not refresh the native rect of this centered window.
        self.titleBar.SetPosition(0, 0)
        self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
        self.titleBar.Show()
        self.children.append(Line(self.titleBar, WIDTH // 2, 4,
            Text("BIO_RESEARCH_TITLE", u"Biologický výzkum"), "Tahoma:14", WHITE, True))
        self.tabs = []
        for index, label in enumerate((Text("BIO_RESEARCH_TAB", u"Výzkumy"), Text("BIO_COMPLETED_TAB", u"Dokončené"))):
            button = ui.RadioButton()
            button.SetParent(self)
            button.SetPosition(74 + 140 * index, 36)
            uicrimsoncontrols.ApplyVisuals(button, "137x31")
            button.SetText(label)
            button.SetEvent(lambda value=index: self.SetTab(value))
            button.Show()
            self.tabs.append(button)
        self.tabs[0].Down()
        for center, caption in ((ROW_X + 20, Text("BIO_LEVEL_HEADER", u"Úroveň")),
                                (ROW_X + ELIXIR_X + 8, Text("BIO_ELIXIR_HEADER", u"Elixír")),
                                (ROW_X + CLOCK_X + 8, Text("BIO_CLOCK_HEADER", u"Urychlovac"))):
            self.children.append(Line(self, center, 72, caption, "Tahoma:12b", GOLD, True))
        for column, vnum, asset in ((ELIXIR_X, 71035, "helper_elixir24"),
                                    (CLOCK_X, ACCELERATOR_VNUM, "icon/item/72357.tga")):
            icon = ui.ImageBox()
            icon.SetParent(self)
            # Header alpha centers share the checkbox column, rounded by 0.5px.
            icon.SetPosition(ROW_X + column + 8 - 12, 41)
            icon.LoadImage(asset if asset.endswith(".tga") else ASSET_ROOT + asset + ".png")
            icon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.HeaderBoosterTooltip, vnum)
            icon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.HideTooltip)
            icon.Show()
            self.children.append(icon)
        self.rows = [ResearchRow(self, index) for index in range(VISIBLE_ROWS)]
        for row in self.rows:
            row.Hide()
        self.scroll = SettingsScrollBar()
        self.scroll.SetParent(self)
        self.scroll.SetPosition(WIDTH - 24, ROW_Y + 9)
        self.scroll.SetScrollBarSize(VISIBLE_ROWS * ROW_STEP - 24)
        self.scroll.SetScrollEvent(ui.__mem_func__(self.OnScroll))
        self.scroll.Hide()
        self.empty = Line(self, WIDTH // 2, ROW_Y + (VISIBLE_ROWS * ROW_STEP - 6) // 2,
                          "", color=MUTED, center=True)

    @staticmethod
    def Owned(vnum):
        if vnum in (ACCELERATOR_VNUM, LEGACY_CLOCK_VNUM):
            return (max(0, player.GetItemCountByVnum(ACCELERATOR_VNUM)) +
                    max(0, player.GetItemCountByVnum(LEGACY_CLOCK_VNUM)))
        return max(0, player.GetItemCountByVnum(vnum))

    def Available(self, index):
        return (self.dataKnown and player.GetStatus(player.LEVEL) >= self.researches[index]["level"]
                and (self.modern or index == self.legacyIndex))

    def CanSubmit(self, index):
        return index not in self.pending and model.submission(self.researches[index],
            app.GetGlobalTimeStamp(), player.GetStatus(player.LEVEL), self.Owned,
            *self.boosters.get(index, [False, False]), available=self.Available(index))

    def RequestState(self):
        if app.GetTime() >= self.nextRequest:
            self.nextRequest = app.GetTime() + 2.0
            net.SendChatPacket("/bio state2")

    def BeginSnapshot(self, count):
        try:
            self.snapshot.begin(count)
        except (ValueError, TypeError):
            self.snapshot.invalid = True

    def SnapshotRow(self, *values):
        self.snapshot.append(values)

    def EndSnapshot(self):
        rows = self.snapshot.finish()
        if rows is None:
            return
        self.modern = True
        self.researches = rows
        self.dataKnown = True
        self.pending.clear()
        self.RefreshRows()
        self.UpdateReminders()
        self.EnsureLoop()
        self.RefreshHUD()
        interface = osfInfo.GetInterfaceInstance()
        if interface and getattr(interface, "uiAffectshower", None):
            interface.uiAffectshower.SetBiologBonuses(model.passive_totals(rows))
        if self.choiceIndex and model.phase(rows[self.choiceIndex]) != "gift":
            self.CloseChoice()

    def Legacy(self, index, count=0, due=0, alarm=False, mode="mission"):
        if self.modern:
            self.RequestState()
            return
        # Generated copy of the server catalogue (tools/build_server_game_data.py).
        self.researches = model.legacy_rows(legacy.BiologCatalogRows(), index, count, due, alarm, mode)
        self.legacyIndex = index
        self.dataKnown = True
        self.pending.clear()
        self.RefreshRows()
        self.UpdateReminders()
        self.EnsureLoop()
        self.RequestState()

    def LoadData(self, level, count, time, enableNotification):
        self.Legacy(level, count, time, bool(enableNotification))

    def LoadStone(self, level):
        self.Legacy(level, alarm=self.researches.get(level, {}).get("alarm", False), mode="stone")

    def LoadGift(self, level):
        self.Legacy(level, alarm=self.researches.get(level, {}).get("alarm", False), mode="gift")

    def LoadEmpty(self, completed=False):
        self.Legacy(model.MAX_RESEARCHES + 1 if completed else 0)

    def SetTab(self, index):
        self.tab = index
        self.start = 0
        self.scroll.SetPos(0.0)
        for offset, button in enumerate(self.tabs):
            button.Down() if offset == index else button.SetUp()
        self.RefreshRows()

    def Indexes(self):
        return sorted(
            (index for index, row in self.researches.items() if row["done"] == bool(self.tab)),
            key=lambda index: (self.researches[index]["level"], index))

    def RefreshRows(self):
        indexes = self.Indexes()
        maximum = max(0, len(indexes) - VISIBLE_ROWS)
        self.start = min(self.start, maximum)
        for offset, row in enumerate(self.rows):
            if self.start + offset < len(indexes):
                row.SetIndex(indexes[self.start + offset])
                row.Show()
            else:
                row.Hide()
        if maximum:
            self.scroll.SetMiddleBarSize(float(VISIBLE_ROWS) / len(indexes))
            self.scroll.SetScrollStep(1.0 / maximum)
            self.scroll.Show()
        else:
            self.scroll.Hide()
        self.empty.SetText("" if indexes else Text("BIO_NO_RESEARCH_TAB", u"Žádné výzkumy v této záložce"))

    def OnScroll(self):
        self.start = int(round(self.scroll.GetPos() * max(0, len(self.Indexes()) - VISIBLE_ROWS)))
        self.RefreshRows()

    def OnMouseWheel(self, delta):
        if delta > 0:
            self.scroll.OnUp()
        elif delta < 0:
            self.scroll.OnDown()
        return True

    def Submit(self, index):
        if not self.CanSubmit(index):
            return
        if model.phase(self.researches[index]) == "gift":
            self.ChooseReward(index)
            return
        elixir, clock = self.boosters.get(index, [False, False])
        self.pending[index] = app.GetTime()
        command = "/bio give2 %d %d %d" % (index, elixir, clock) if self.modern else "/bio mission %d %d" % (elixir, clock)
        net.SendChatPacket(command)
        self.RefreshRows()

    def SetAlarm(self, index, enabled):
        if self.modern:
            net.SendChatPacket("/bio alarm2 %d %d" % (index, enabled))
        else:
            net.SendChatPacket("/bio_notification %d" % enabled)
            self.researches[index]["alarm"] = enabled
            self.RefreshRows()
            self.UpdateReminders()
            self.EnsureLoop()
            self.RefreshHUD(enabled)

    def RewardLines(self, index):
        row = self.researches[index]
        rewards = row["rewards"]
        if row["done"] and row["choose"] and row["chosen"]:
            rewards = [rewards[row["chosen"] - 1]]
        return [GET_AFFECT_STRING(kind, value) for kind, value in rewards if kind]

    def Rewards(self, index):
        lines = self.RewardLines(index)
        row = self.researches[index]
        if row["choose"] and not row["done"]:
            lines.insert(0, Text("BIO_REWARD_CHOICE_COUNT", u"Výběr 1 ze 3"))
        self.Tooltip(Text("BIO_COMPLETION_REWARD", u"Odměna za dokončení"), lines, bonus_rows=self.RewardLines(index))

    def ChooseReward(self, index):
        self.CloseChoice()
        self.choiceIndex = index
        self.choiceWindow = ui.BoardWithTitleBar()
        self.choiceWindow.SetSize(380, 166)
        self.choiceWindow.SetTitleName(Text("BIO_CHOOSE_REWARD", u"Vyber jednu odměnu"))
        self.choiceWindow.SetCloseEvent(ui.__mem_func__(self.CloseChoice))
        self.choiceWindow.AddFlag("float")
        self.choiceWindow.SetCenterPosition()
        self.choiceButtons = []
        for choice, label in enumerate(self.RewardLines(index)):
            button = ui.Button()
            button.SetParent(self.choiceWindow)
            button.SetPosition(37, 43 + choice * 33)
            uicrimsoncontrols.ApplyVisuals(button, "306x18")
            button.SetText(label, 0)
            button.SetEvent(lambda value=choice: self.AcceptReward(value))
            button.Show()
            self.choiceButtons.append(button)
        self.choiceWindow.Show()
        self.choiceWindow.SetTop()

    def AcceptReward(self, choice):
        index = self.choiceIndex
        if not index or index in self.pending:
            return
        self.pending[index] = app.GetTime()
        net.SendChatPacket("/bio gift2 %d %d" % (index, choice) if self.modern else "/bio gift %d" % choice)
        self.CloseChoice()

    def CloseChoice(self):
        if self.choiceWindow:
            self.choiceWindow.Hide()
        self.choiceWindow = None
        self.choiceButtons = []
        self.choiceIndex = 0

    def Tooltip(self, title, lines, bonus_rows=()):
        self.HideTooltip()
        self.tooltip.ClearToolTip()
        Tint(self.tooltip.AutoAppendTextLine(title, GOLD), GOLD)
        for line in lines:
            color = bonuscolor.Text(line) if line in bonus_rows else GOLD
            Tint(self.tooltip.AutoAppendTextLine(line, color), color)
        # Width may grow while appending localized reward lines; recenter all.
        for line in self.tooltip.childrenList:
            _, y = line.GetLocalPosition()
            line.SetPosition(self.tooltip.toolTipWidth // 2, y)
        self.tooltip.ResizeToolTip()
        self.tooltip.ShowToolTip()

    def HeaderBoosterTooltip(self, vnum):
        title = Text("BIO_CLOCK_NAME", u"Biologist's Accelerator") if vnum in (ACCELERATOR_VNUM, LEGACY_CLOCK_VNUM) else legacy._ItemName(vnum)
        self.Tooltip(title, [Text("BIO_HELPER_OWNED", u"V batohu: %d ks") % self.Owned(vnum)])

    def ItemTooltip(self, vnum):
        self.HideTooltip()
        interface = osfInfo.GetInterfaceInstance()
        if interface and interface.tooltipItem:
            interface.tooltipItem.SetItemToolTip(vnum)
            interface.tooltipItem.ShowToolTip()

    def HideTooltip(self):
        self.tooltip.HideToolTip()
        interface = osfInfo.GetInterfaceInstance()
        if interface and interface.tooltipItem:
            interface.tooltipItem.HideToolTip()

    def EnsureLoop(self):
        game = osfInfo.GetGameInstance()
        if game:
            game.AddLoopEvent("bio", ui.__mem_func__(self.OnUpdate))

    def UpdateReminders(self):
        now = app.GetGlobalTimeStamp()
        character = player.GetName()
        interface = osfInfo.GetInterfaceInstance()
        for index, row in self.researches.items():
            key = (character, index)
            previous = _REMINDERS.get(key)
            if previous is None or previous[0] != row["due"]:
                previous = [row["due"], row["due"] > now, False]
                _REMINDERS[key] = previous
            if not row["alarm"]:
                previous[1] = row["due"] > now
                continue
            if model.phase(row) != "mission" or row["due"] > now or not previous[1] or previous[2]:
                continue
            if interface and interface.PushBiologReadyNotification(
                    Text("BIO_READY_NOTIFICATION_TITLE", u"Biologický výzkum"),
                    legacy._ItemName(row["vnum"]) + u" — " + Text("BIO_READY_SHORT", u"Připraveno"),
                    row["vnum"], (character, index, row["due"])):
                previous[2] = True

    def GetTrackedResearches(self):
        return [row for row in self.researches.values() if self.dataKnown and row["alarm"] and not row["done"]]

    def RefreshHUD(self, reveal=False):
        interface = osfInfo.GetInterfaceInstance()
        if interface and hasattr(interface, "RefreshCountdownHUDSelection"):
            interface.RefreshCountdownHUDSelection(reveal)

    def ResetReminderState(self):
        _REMINDERS.clear()
        legacy.ResetReminderState()

    def OnUpdate(self):
        now = app.GetTime()
        if now < self.nextTick:
            return False
        self.nextTick = now + 0.25
        self.UpdateReminders()
        if self.IsShow() and not self.dataKnown:
            self.RequestState()
        if any(now - started > 5.0 for started in self.pending.values()):
            self.RequestState()  # resynchronize; never automatically repeat item use
        if self.IsShow():
            for row in self.rows:
                if row.IsShow():
                    row.Refresh()
        return False

    def Show(self):
        ui.Window.Show(self)
        self.RequestState()

    def Hide(self):
        if "tooltip" in self.__dict__:
            self.HideTooltip()
        if "choiceWindow" in self.__dict__:
            self.CloseChoice()
        ui.Window.Hide(self)

    def Open(self):
        self.Show()
        self.SetTop()

    def Close(self):
        self.HideTooltip()
        self.CloseChoice()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Close()
        game = osfInfo.GetGameInstance()
        if game:
            game.RemoveLoopEvent("bio")
        self.rows = []
        self.children = []
        ui.Window.Destroy(self)
