"""Show only the server-owned active mission and its live objectives."""
import weakref
import fontconfig
import net
import player
import ui
import uiCommon
import missionbookmodel as model
from missionbooklocale import Text
from uimissionbookwidgets import WindowDestroy, line, fitted, book_image, button, Target, GOLD, DIM
from uimissionbooktracker import MissionBookTracker


class MissionBookWindow(ui.ScriptWindow):
    def __init__(self, interface):
        # The native base constructor calls our Hide override.
        self.Initialize()
        ui.ScriptWindow.__init__(self)
        self.interface = weakref.proxy(interface)
        self.character = str(player.GetName() or "")
        self.settings = model.load_settings(self.character)
        self.state = model.MissionState()
        self.AddFlag("float")
        self.AddFlag("movable")
        self.SetWindowName("MissionBooksActive")
        self.SetSize(302, 344)
        self.SetCenterPosition()
        self.Build()
        self.tracker = MissionBookTracker(self)
        self.Hide()

    def Initialize(self):
        self.interface = None
        self.character = ""
        self.settings = None
        self.state = None
        self.receivedState = False
        self.board = self.titleBar = self.title = None
        self.bookIcon = self.bookName = self.rewardIcon = None
        self.rewardLabel = self.rewardText = None
        self.empty = self.emptyHint = None
        self.topRule = self.rewardRule = None
        self.checkbox = self.cancelButton = self.tracker = None
        self.cancelDialog = None
        self.children = []
        self.targets = []
        self.r1 = None
        self.suspended = False
        self.restoreMain = False
        self.restoreTracker = False

    def __del__(self):
        ui.ScriptWindow.__del__(self)

    def Rule(self, y, width):
        rule = ui.Bar()
        rule.SetParent(self)
        rule.AddFlag("not_pick")
        rule.SetPosition(18, y)
        rule.SetSize(width, 1)
        rule.SetColor(0xff522c2c)
        rule.Show()
        return rule

    def Build(self):
        self.board = ui.Board()
        self.board.SetParent(self)
        self.board.SetPosition(4, 0)
        self.board.SetSize(294, 344)
        self.board.AddFlag("not_pick")
        self.board.Show()
        self.titleBar = ui.TitleBar()
        self.titleBar.SetParent(self)
        self.titleBar.AddFlag("attach")
        self.titleBar.MakeTitleBar(302, "red")
        self.titleBar.SetPosition(0, 0)
        self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
        self.titleBar.Show()
        self.title = line(self.titleBar, 151, 3, Text("ACTIVE"), align="center",
                          role=fontconfig.ROLE_WINDOW_TITLE)
        self.topRule = self.Rule(72, 266)
        self.rewardRule = self.Rule(271, 266)
        self.bookName = line(self, 58, 43, "")
        self.rewardLabel = line(self, 18, 283, Text("REWARD"), DIM)
        self.rewardText = line(self, 116, 285, "")
        self.empty = line(self, 151, 135, Text("NO_ACTIVE"), align="center")
        self.emptyHint = line(self, 151, 162, Text("USE_BOOK_HINT"), DIM, "center")
        self.checkbox = ui.CheckBox_N()
        self.checkbox.SetParent(self)
        self.checkbox.text.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
        self.checkbox.SetText(Text("PIN_TRACKER"))
        self.checkbox.SetPosition(18, 314)
        self.checkbox.SetChecked(self.settings["auto_track"])
        self.checkbox.SetEvent(ui.__mem_func__(self.ToggleTracking))
        self.checkbox.Show()
        self.cancelButton = button(self, 192, 309, Text("CANCEL_MISSION"),
                                   ui.__mem_func__(self.CancelMission))
        self.children = [self.board, self.titleBar, self.title, self.topRule,
                         self.rewardRule, self.bookName, self.rewardLabel,
                         self.rewardText, self.empty, self.emptyHint,
                         self.checkbox, self.cancelButton]
        self.RefreshActive()
        self.ApplyR1Look()

    def ApplyR1Look(self):
        """R1 look (root/uimissionbooksr1.py) unless Settings -> "Starý vzhled" chose the original one; a build
        failure undoes every change and keeps the original look (traced to syserr, not tried again this session)."""
        self.r1 = None
        try:
            import uimissionbooksr1
        except Exception:
            return
        self.r1 = uimissionbooksr1.Build(self)

    def SyncR1(self):
        if self.r1:
            self.r1.SyncSafe()

    def ResizeForTargets(self, count):
        width, height = {0: (302, 344), 1: (302, 344),
                         2: (390, 344), 3: (566, 344)}[min(count, 3)]
        self.SetSize(width, height)
        self.board.SetSize(width - 8, height)
        self.titleBar.SetWidth(width)
        self.title.SetPosition(width // 2, 3)
        self.topRule.SetSize(width - 36, 1)
        self.rewardRule.SetSize(width - 36, 1)
        self.empty.SetPosition(width // 2, 135)
        self.emptyHint.SetPosition(width // 2, 162)
        self.cancelButton.SetPosition(width - 110, 309)
        self.SetCenterPosition()

    def ClearActive(self):
        for target in self.targets:
            target.Destroy()
        self.targets = []
        for image in (self.bookIcon, self.rewardIcon):
            if image:
                image.Hide()
        self.bookIcon = self.rewardIcon = None

    def RefreshActive(self):
        self.ClearActive()
        active = self.state.active
        targets = self.state.targets()
        self.ResizeForTargets(len(targets))
        visible = bool(active)
        self.empty.Show() if not visible else self.empty.Hide()
        self.emptyHint.Show() if not visible else self.emptyHint.Hide()
        for widget in (self.bookName, self.rewardLabel, self.rewardText,
                       self.topRule, self.rewardRule, self.checkbox):
            widget.Show() if visible else widget.Hide()
        self.cancelButton.Show() if visible else self.cancelButton.Hide()
        if not active:
            self.SyncR1()
            return
        book, mission = active
        self.bookIcon = book_image(self, book, 18, 34)
        tier = model.BOOKS.index(book)
        self.bookName.SetText("%s (%s)" % (Text("BOOK_NAME"), Text("TIER_%d" % tier).lower()))
        fitted(self.bookName, self.bookName.GetText(), self.GetWidth() - 80)
        self.rewardIcon = book_image(self, model.CHESTS[tier], 78, 275)
        self.rewardText.SetText(Text("CHEST_%d" % tier))
        fitted(self.rewardText, self.rewardText.GetText(), self.GetWidth() - 132)
        for index, (vnum, required) in enumerate(targets):
            kind = model.objectives(book, mission)[index][0]
            name = Text("MINE_ALTHEIT") if kind == 2 else Text("FISH_POND") if kind == 3 else None
            x = 67 if len(targets) == 1 else 21 + index * 180 if len(targets) == 2 else 19 + index * 180
            target = Target(self, vnum, required, x, 82, kind, name)
            self.targets.append(target)
        self.RefreshProgress()
        self.SyncR1()
        if self.IsShow():
            self.OpenTargets()

    def RefreshProgress(self):
        for index, target in enumerate(self.targets):
            text = "%d / %d" % (self.state.progress[index], self.state.targets()[index][1])
            target.count.SetText(text)

    def OpenTargets(self):
        for target in self.targets:
            target.Open()

    def Open(self):
        if self.suspended:
            return
        self.Show()
        self.SetTop()
        self.SetFocus()
        self.OpenTargets()

    def Close(self):
        self.CloseCancelDialog()
        self.KillFocus()
        self.Hide()

    def Hide(self):
        for target in self.targets:
            target.Close()
        ui.ScriptWindow.Hide(self)

    def ReceiveState(self, book, mission, p1, p2, p3, ready):
        previous = self.state.active
        hadSnapshot = self.receivedState
        if not self.state.receive(book, mission, p1, p2, p3, ready):
            return
        self.receivedState = True
        if not self.state.active:
            self.CloseCancelDialog()
        if self.state.active != previous:
            self.RefreshActive()
        else:
            self.RefreshProgress()
            self.cancelButton.Show() if self.state.active else self.cancelButton.Hide()
        self.tracker.Refresh()
        self.tracker.Open() if self.state.active else self.tracker.Close()
        # The first state restores login/warp data, not a new book activation.
        if hadSnapshot and self.state.active and self.state.active != previous:
            if self.suspended:
                self.restoreMain = True
            else:
                self.Open()

    def ToggleTracking(self):
        self.settings["auto_track"] = bool(self.checkbox.IsChecked())
        self.Save()
        self.tracker.Open() if self.settings["auto_track"] else self.tracker.Close()

    def CancelMission(self):
        if not self.state.active:
            return
        if self.cancelDialog is None:
            self.cancelDialog = uiCommon.QuestionDialog()
            self.cancelDialog.SetText(Text("CANCEL_CONFIRM"))
            self.cancelDialog.SetAcceptEvent(ui.__mem_func__(self.ConfirmCancel))
            self.cancelDialog.SetCancelEvent(ui.__mem_func__(self.CloseCancelDialog))
        self.cancelDialog.Open()

    def CloseCancelDialog(self):
        if self.cancelDialog:
            self.cancelDialog.Close()

    def ConfirmCancel(self):
        self.CloseCancelDialog()
        if self.state.active:
            net.SendChatPacket("/mission_book_cancel")

    def Save(self):
        if self.settings is not None:
            model.save_settings(self.character, self.settings)

    def Suspend(self):
        if self.suspended:
            return
        self.restoreMain = self.IsShow()
        self.restoreTracker = self.tracker.IsShow()
        self.suspended = True
        self.Close()
        self.tracker.Close()

    def Resume(self):
        if not self.suspended:
            return
        self.suspended = False
        if self.restoreMain:
            self.Open()
        if self.restoreTracker:
            self.tracker.Open()
        self.restoreMain = self.restoreTracker = False

    def OnPressEscapeKey(self):
        self.Close()
        return True

    @WindowDestroy
    def Destroy(self):
        if self.settings is None:
            return
        self.Close()
        self.Save()
        self.tracker.Destroy()
        if self.cancelDialog:
            self.cancelDialog.SetAcceptEvent(None)
            self.cancelDialog.SetCancelEvent(None)
            self.cancelDialog.Close()
        self.cancelButton.SetEvent(None)
        self.checkbox.SetEvent(None)
        self.titleBar.SetCloseEvent(None)
        if self.r1:
            self.r1.Destroy()
            self.r1 = None
        self.ClearActive()
        for widget in self.children:
            widget.Hide()
        self.ClearDictionary()
        self.Initialize()
