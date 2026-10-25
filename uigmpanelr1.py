# -*- coding: utf-8 -*-
"""GM panel (F10) in the Althea R1 look, design B2 "Nejdřív hráč" (owner 8. 10. 2026).

One 820 x 640 window instead of category tabs with three visible actions:

* the player field at the top fills the player of every action on a player; without a player those actions are
  dimmed. "Detail" runs Detail hráče for that player, and the card beside it shows what the reply of that action
  told (online, channel, map, level): the client gets nothing else about another player (a dedicated server reply
  for the card is a follow-up);
* every action of the session's mask, grouped by the server's categories, with an action search; a scroll bar only
  when the actions do not fit;
* the form on the right: the action's inputs with Czech labels, the mute presets (1 min .. 7 dní, the server still
  gets seconds), the monster / item search inside the value field (by name or VNUM, the client's own data), the
  runtime map search, -/+ on a count, the preview of an announcement, the minimum role and "chrání vyšší GM" chips;
* a risky action (the catalogue's confirmation) asks in a second step inside the form; the server's refusal is
  shown in the form; the last actions of this session are listed at the bottom.

The protocol is the original panel's: the request, confirmation-mark, capability and result code of
uigmpanel.GMPanelWindow runs here unchanged (its functions are taken over, not copied), so the panel sends exactly
the commands the original sends and reads the same catalogue rows (gmpanelcatalog). Czech names come from
gmpanelr1text with the server's text as the fallback.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original panel (uigmpanel.NewWindow). A failure while
building or using R1 is traced (uir1.TraceFailure), the original panel takes over with the same state and R1 is
not tried again in this session.
"""
import time
from weakref import proxy, WeakMethod

import ui
import wndMgr

import gmmaintenance as M
import gmmapcatalog
import gmpanelcatalog
import gmpanelr1text as X
import uigmpanel as legacy
import uir1
import uir1layout as L
import uir1tokens as T

WHAT = u'GM panel'
TITLE = u'GM panel'

_failed = False

# The "Údržba" section of the action list. Not a server action: the ids of those are 1..63. Its form
# types the chat command /maintenance, which the server limits to the highest GM level (gmmaintenance); nothing
# goes through the panel protocol.
MAINTENANCE_ACTION = 1000
MAINTENANCE_CATEGORY = 'maintenance'      # its own section only when the server sends no world category
WORLD_CATEGORY = 5

# The original panel's request, capability and result code, run on this window.
_LEGACY = legacy.GMPanelWindow.__dict__
_BORROWED = ('_CanUse', '_CountAvailableActions', '_RoleName', 'SetCatalogCollector', 'OnCatalogRow',
             '_NextRequestID', 'QueryCapabilities', 'ExecuteSelected', '_AcceptQuestion')


def UseR1():
    """R1 unless Settings -> "Starý vzhled" chose the original look, or R1 already failed in this session."""
    return not _failed and uir1.UseR1()


def Failed():
    """Called from an except block: traces why R1 is not used and keeps the original panel for this session."""
    global _failed
    _failed = True
    uir1.TraceFailure(WHAT)


def Signed(color):
    """A packed colour for SetPackedFontColor: the x64 binding ignores values >= 0x80000000 (PRAVIDLA-UI, Kód)."""
    color &= 0xFFFFFFFF
    return color - 0x100000000 if color & 0x80000000 else color


W, H = 820, 640
PLAYER = (10, 31, 800, 56)
LIST = (10, 95, 470, 434)
FORM = (490, 95, 320, 434)
HISTORY = (10, 537, 800, 93)

PAD = 8
SEARCH_H = 38                   # the action search and the gap under it
COLS = 3
GAP = 6
ROW = T.BTN_H_S                 # 22
ROW_STEP = ROW + 4
SECTION_H = 20
SECTION_GAP = 2
FORM_X, FORM_W = 10, 300
FIELD_STEP = 18 + T.FIELD_H + 8
RESULT_ROWS = 4
RESULT_H = 22
HISTORY_ROWS = 3
HISTORY_KEEP = 20

OK = 0xFF8FCB7C                 # accepted (the green of a complete counter of the R1 task windows)
ERROR = T.RED_HI
DOT = 0xFFA80B0D                # the small mark of an action that asks before it is sent
WARN_FILL = 0xFF2A0B0C
WARN_LINE = 0xFF6E1012


def _Status(name, default):
    try:
        return getattr(legacy.net, name)
    except AttributeError:
        return default


class ActionButton(uir1.Interactive):
    """An action of the list: the 22 px R1 secondary plate, the Czech name left in Noto Sans, a small dark red mark
    when the action asks before it is sent. Selected = the lighter plate and the ivory name (brightness, no red
    line); dimmed = the disabled plate (an action on a player while no player is entered)."""

    def __init__(self, parent, kit, text, confirm, event, center=False):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.kit = kit
        self.text = text
        self.center = center
        self.w = 0
        self.selected = False
        self.ops = uir1.Ops(self, L.button(False, True, 'normal', 64))    # all three plate images before the label
        self.font = kit.font('text_s')
        self.label = uir1.Text(self, u'', 10, uir1.CellTop(ROW, self.font), self.font, Signed(T.BUTTON_TEXT),
                               align='center' if center else 'left', valign='top')
        self.dot = uir1.Rect(self, 0, 0, 3, 3, DOT) if confirm else None
        self.callback = event
        self.Show()

    def Place(self, x, y, w):
        self.SetPosition(int(x), int(y))
        if int(w) != self.w:
            self.w = int(w)
            self.SetSize(self.w, ROW)
            if self.center:
                self.label.SetPosition(self.w // 2, uir1.CellTop(ROW, self.font))
            uir1.Fit(self.label, self.text, self.w - (4 if self.center else (24 if self.dot else 16)))
            if self.dot is not None:
                self.dot.SetPosition(self.w - 10, ROW // 2 - 1)
        self.paint()

    def SetSelected(self, selected):
        if bool(selected) != self.selected:
            self.selected = bool(selected)
            self.paint()

    def paint(self):
        if not self.w:
            return
        if not self.enabled:
            plate, color = 'disabled', T.DISABLED
        elif self.pressed:
            plate, color = 'pressed', T.IVORY
        elif self.selected:
            plate, color = 'hover', T.IVORY
        else:
            plate, color = ('hover' if self.hovered else 'normal'), (T.IVORY if self.hovered else T.BUTTON_TEXT)
        self.ops.Apply(L.button(False, True, plate, self.w))
        self.label.SetPackedFontColor(Signed(color))
        if self.dot is not None:
            self.dot.Show() if self.enabled else self.dot.Hide()


class Chip(ui.Window):
    """A small outlined label: the minimum role of an action, "chrání vyšší GM", the role of this session."""
    H = 18

    def __init__(self, parent, kit):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.frame = uir1.Frame(self, 0, 0, 40, self.H, 'panel')
        self.font = kit.font('text_xs')
        self.label = uir1.Text(self, u'', 6, uir1.CellTop(self.H, self.font), self.font, Signed(T.INK_DIM),
                               valign='top')
        self.w = 40
        self.SetSize(self.w, self.H)

    def SetText(self, text):
        self.label.SetText(text)
        self.w = uir1.TextWidth(self.label) + 12
        self.SetSize(self.w, self.H)
        self.frame.Resize(self.w, self.H)
        return self.w


class ResultRow(uir1.Interactive):
    """One hit of a search inside the form (monster, item, map): the name left, the VNUM / index right."""

    def __init__(self, parent, kit, w, event):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.w = int(w)
        self.SetSize(self.w, RESULT_H)
        self.band = uir1.Band(self, 0, 0, self.w, RESULT_H)
        font = kit.font('text_s')
        top = uir1.CellTop(RESULT_H, font)
        self.name = uir1.Text(self, u'', 8, top, font, Signed(T.INK), valign='top')
        self.detail = uir1.Text(self, u'', self.w - 8, top, font, Signed(T.MUTED), align='right', valign='top')
        self.entry = None
        self.selected = False
        self.callback = event

    def SetEntry(self, entry, name, detail):
        self.entry = entry
        self.detail.SetText(detail)
        uir1.Fit(self.name, name, self.w - 24 - uir1.TextWidth(self.detail))

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def paint(self):
        lit = self.selected or self.hovered
        self.band.SetState('hover' if lit else 'normal')
        self.name.SetPackedFontColor(Signed(T.IVORY if lit else T.INK))

    def click(self):
        if self.callback and self.entry is not None:
            self.callback(self.entry)


class _EntitySource(object):
    """The monster / item lookup of the original picker (GMEntitySelectionDialog), on the client's own data."""
    MAX_RESULTS = legacy.GMEntitySelectionDialog.MAX_RESULTS
    RECENT = legacy.GMEntitySelectionDialog.RECENT
    _ItemEntry = legacy.GMEntitySelectionDialog.__dict__['_ItemEntry']
    _MobEntry = legacy.GMEntitySelectionDialog.__dict__['_MobEntry']
    _BuildEntry = legacy.GMEntitySelectionDialog.__dict__['_BuildEntry']
    _SearchVnums = legacy.GMEntitySelectionDialog.__dict__['_SearchVnums']

    def __init__(self, mode):
        self.mode = mode

    def Search(self, query):
        query = query.strip()
        entries, seen = [], set()
        for vnum in self._SearchVnums(query):
            vnum = int(vnum)
            if vnum <= 0 or vnum in seen:
                continue
            seen.add(vnum)
            entry = self._BuildEntry(vnum)
            if entry:
                entries.append(entry)
            if len(entries) >= self.MAX_RESULTS:
                break
        lower = X.Fold(query)
        entries.sort(key=lambda entry: (0 if lower and X.Fold(entry['name']).startswith(lower) else 1,
                                        X.Fold(entry['name']), entry['vnum']))
        return entries


def _MapEntries(query):
    """Runtime maps matching a query (index, internal or display name), as the original map picker searched."""
    lower = X.Fold(query.strip())
    found = []
    for mapIndex, internalName in gmmapcatalog.RUNTIME_MAPS:
        displayName = legacy._GetMapDisplayName(mapIndex, internalName)
        if not lower or lower in X.Fold(u'%d %s %s' % (mapIndex, X.Unicode(internalName), X.Unicode(displayName))):
            found.append((mapIndex, internalName, displayName))
    return found


def _MapName(mapIndex):
    for index, internalName in gmmapcatalog.RUNTIME_MAPS:
        if index == mapIndex:
            return X.Unicode(legacy._GetMapDisplayName(index, internalName))
    return u'mapa %d' % mapIndex


class MaintenanceForm(object):
    """The form of the "Údržba" section: when the maintenance starts (minutes), how long it lasts
    (minutes), an optional reason for the players (a preset or a short text), the sentence the players will read,
    and the two buttons. Both ask a second step first. It sends the chat command /maintenance (gmmaintenance.Check
    builds it with the server's own limits); the server decides, and its answer is in the chat."""

    def __init__(self, owner, form, kit):
        self.owner = proxy(owner)
        self.preset = None
        self.pending = None                 # ('start', command, question, note) or ('stop', ...)
        self.status = (u'', T.MUTED)
        half = (FORM_W - 12) // 2
        self.half = half
        text = owner._Text
        safe = owner._Safe

        self.title = text(form, FORM_X, 9, 'title', T.IVORY)
        self.title.SetText(X.MAINTENANCE_TITLE)
        self.roleTag = Chip(form, kit)
        self.roleTag.SetText(X.RoleTag(M.LEVEL))
        self.descLines = [text(form, FORM_X, 32 + 17 * i, color=T.INK_DIM) for i in range(2)]

        self.startLabel = text(form, FORM_X, 0, color=T.INK_DIM)
        self.startLabel.SetText(X.MAINTENANCE_START_LABEL)
        self.startField = uir1.Field(form, kit, FORM_X, 0, half, hint=u'15', max_len=M.FIELD_DIGITS, number=True)
        self.durationLabel = text(form, FORM_X + half + 12, 0, color=T.INK_DIM)
        self.durationLabel.SetText(X.MAINTENANCE_DURATION_LABEL)
        self.durationField = uir1.Field(form, kit, FORM_X + half + 12, 0, half, hint=u'30', max_len=M.FIELD_DIGITS,
                                        number=True)
        self.reasonLabel = text(form, FORM_X, 0, color=T.INK_DIM)
        self.reasonLabel.SetText(X.MAINTENANCE_REASON_LABEL)
        self.reasonField = uir1.Field(form, kit, FORM_X, 0, FORM_W, hint=X.MAINTENANCE_REASON_HINT,
                                      max_len=M.REASON_MAX)
        self.edits = [owner._Edit(field, maximum) for field, maximum in
                      ((self.startField, M.FIELD_DIGITS), (self.durationField, M.FIELD_DIGITS),
                       (self.reasonField, M.REASON_MAX))]
        for edit in self.edits:
            edit.SetReturnEvent(safe(self.Ask))

        self.presetButtons = []
        for word, name in M.PRESETS:
            button = ActionButton(form, kit, name, False,
                                  safe(lambda word=word, form=proxy(self): form.SetPreset(word)), center=True)
            self.presetButtons.append((word, button))

        self.previewLabel = text(form, FORM_X, 0, color=T.INK_DIM)
        self.previewLabel.SetText(X.MAINTENANCE_PREVIEW_LABEL)
        self.previewFrame = uir1.Frame(form, FORM_X, 0, FORM_W, 44, 'panel')
        self.previewLines = [text(form, FORM_X + 8, 0, color=T.IVORY) for unused in range(2)]
        self.problem = text(form, FORM_X, 0, color=ERROR)

        self.startButton = uir1.Button(form, kit, 0, 0, 150, X.MAINTENANCE_START, primary=True, event=safe(self.Ask))
        self.stopButton = uir1.Button(form, kit, 0, 0, 150, X.MAINTENANCE_STOP, event=safe(self.AskStop))
        self.askFill = uir1.Rect(form, FORM_X, 0, FORM_W, 84, WARN_FILL, 0.92)
        self.askLines = [uir1.Rect(form, FORM_X, 0, FORM_W, 1, WARN_LINE) for unused in range(2)] + \
                        [uir1.Rect(form, FORM_X, 0, 1, 84, WARN_LINE) for unused in range(2)]
        self.askDot = uir1.Rect(form, FORM_X + 12, 0, 4, 4, T.RED)
        self.askText = text(form, FORM_X + 24, 0, 'text', T.IVORY)
        self.askNote = text(form, FORM_X + 24, 0, color=T.INK_DIM)
        self.backButton = uir1.Button(form, kit, 0, 0, 80, X.MAINTENANCE_BACK, small=True, event=safe(self.Back))
        self.acceptButton = uir1.Button(form, kit, 0, 0, 130, u'', primary=True, small=True, event=safe(self.Accept))
        self.statusLine = text(form, FORM_X, 0, color=T.MUTED)
        self.Hide()

    def _Widgets(self):
        widgets = [self.title, self.roleTag, self.startLabel, self.startField, self.durationLabel,
                   self.durationField, self.reasonLabel, self.reasonField, self.previewLabel, self.previewFrame,
                   self.problem, self.startButton, self.stopButton, self.askFill, self.askDot, self.askText,
                   self.askNote, self.backButton, self.acceptButton, self.statusLine]
        widgets += self.descLines + self.previewLines + self.askLines + [button for unused, button in
                                                                         self.presetButtons]
        return widgets

    def Hide(self):
        for widget in self._Widgets():
            widget.Hide()

    def Edits(self):
        return list(self.edits)

    def Reset(self):
        for edit in self.edits:
            edit.SetText('')
        self.preset = None
        self.pending = None
        self.status = (u'', T.MUTED)

    def Signature(self):
        """What redraws the form when it changes (the edit lines are polled; the engine has no change event)."""
        return tuple(edit.GetText() for edit in self.edits) + (self.preset,)

    def _Form(self):
        return M.Check(self.edits[0].GetText(), self.edits[1].GetText(), self.preset, self.edits[2].GetText())

    def SetPreset(self, word):
        self.preset = None if self.preset == word else word
        if self.preset:
            self.edits[2].SetText('')       # the text beats a preset, so a chosen preset empties it
        self.pending = None
        self.status = (u'', T.MUTED)
        self.owner._LayoutForm()

    def Ask(self):
        """The main button (and Enter in a field): the second step with the sentence that will be sent."""
        command, preview, problem = self._Form()
        if command is None:
            self.status = (problem or u'Vyplň, za kolik minut údržba začne a jak dlouho potrvá.', ERROR)
        else:
            start = M.Minutes(self.edits[0].GetText(), M.START_MAX)
            duration = M.Minutes(self.edits[1].GetText(), M.DURATION_MAX)
            self.pending = ('start', command, X.MAINTENANCE_ASK_START % (M.Span(start), M.Span(duration)),
                            X.MAINTENANCE_ASK_START_NOTE)
            self.status = (u'', T.MUTED)
        self.owner._LayoutForm()
        return True

    def AskStop(self):
        self.pending = ('stop', M.STOP, X.MAINTENANCE_ASK_STOP, X.MAINTENANCE_ASK_STOP_NOTE)
        self.status = (u'', T.MUTED)
        self.owner._LayoutForm()
        return True

    def Back(self):
        if self.pending is not None:
            self.pending = None
            self.owner._LayoutForm()
        return True

    def Accept(self):
        if self.pending is None:
            return True
        kind, command = self.pending[0], self.pending[1]
        self.pending = None
        self.status = self.owner._SendMaintenance(command, kind)
        self.owner._LayoutForm()
        return True

    def _Place(self, label, field, y):
        label.SetPosition(label.GetLocalPosition()[0], y)
        field.SetPosition(field.GetLocalPosition()[0], y + 18)
        label.Show()
        field.Show()

    def Layout(self):
        """Shown in place of the form of an action; the owner has hidden everything else."""
        owner = self.owner
        self.title.Show()
        x = FORM_X + uir1.TextWidth(self.title) + 10
        self.roleTag.SetPosition(x, 8)
        self.roleTag.Show()
        y = 32
        for line, text in zip(self.descLines, owner._Wrap(X.MAINTENANCE_DESCRIPTION, FORM_W, 2)):
            line.SetPosition(FORM_X, y)
            line.SetText(text)
            line.Show()
            y += 17
        y += 8

        if self.edits[2].GetText().strip():
            self.preset = None
        for label, field in ((self.startLabel, self.startField), (self.durationLabel, self.durationField)):
            self._Place(label, field, y)
        y += FIELD_STEP
        self._Place(self.reasonLabel, self.reasonField, y)
        y += FIELD_STEP
        width = (FORM_W - 2 * GAP) // len(self.presetButtons)
        for column, (word, button) in enumerate(self.presetButtons):
            button.Place(FORM_X + column * (width + GAP), y, width)
            button.SetSelected(word == self.preset)
            button.Show()
        y += ROW_STEP + 8

        command, preview, problem = self._Form()
        self.previewLabel.SetPosition(FORM_X, y)
        self.previewLabel.Show()
        self.previewFrame.SetPosition(FORM_X, y + 18)
        self.previewFrame.Show()
        lines = owner._Wrap(preview or u'—', FORM_W - 16, 2, self.previewLines[0])
        for index, line in enumerate(self.previewLines):
            if index < len(lines):
                line.SetPosition(FORM_X + 8, y + 18 + 6 + 17 * index)
                line.SetText(lines[index])
                line.SetPackedFontColor(Signed(T.IVORY if preview else T.MUTED))
                line.Show()
        y += 18 + 44 + 10

        if self.pending is not None:
            kind, unused, question, note = self.pending
            owner._Box(self.askFill, self.askLines, y, 84)
            self.askDot.SetPosition(FORM_X + 12, y + 16)
            self.askText.SetPosition(FORM_X + 24, y + 8)
            uir1.Fit(self.askText, question, FORM_W - 34)
            self.askNote.SetPosition(FORM_X + 24, y + 30)
            self.askNote.SetText(note)
            self.acceptButton.SetText(X.MAINTENANCE_YES_START if kind == 'start' else X.MAINTENANCE_YES_STOP)
            self.backButton.SetPosition(FORM_X + FORM_W - 12 - self.backButton.w, y + 54)
            self.acceptButton.SetPosition(FORM_X + FORM_W - 12 - self.backButton.w - 8 - self.acceptButton.w, y + 54)
            for widget in (self.askDot, self.askText, self.askNote, self.backButton, self.acceptButton):
                widget.Show()
            return

        self.startButton.SetPosition(FORM_X + FORM_W - self.startButton.w, y)
        self.stopButton.SetPosition(FORM_X, y)
        self.startButton.Show()
        self.stopButton.Show()
        self.startButton.Enable() if command is not None else self.startButton.Disable()
        y += T.BTN_H + 8
        text, color = (problem, ERROR) if problem else self.status
        if text:
            self.statusLine.SetPosition(FORM_X, y)
            uir1.Fit(self.statusLine, text, FORM_W)
            self.statusLine.SetPackedFontColor(Signed(color))
            self.statusLine.Show()


class GMPanelR1Window(ui.Window):
    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('movable')
        self.AddFlag('float')
        self._SetGeometry()

        # The state the original panel starts with (the interface hands requestID / openAfterQuery /
        # capabilitiesLoaded over right after building it).
        self.requestID = 0
        self.actionMask = 0
        self.gmLevel = 0
        self.capabilitiesLoaded = False
        self.openAfterQuery = False
        self.selectedAction = None
        self.selectedCategory = None
        self.questionDialog = None
        self.selectedMapIndex = 0
        self.selectedMapName = ""
        self.selectedEntities = {}
        self.fieldRows = {}
        self.catalogCollector = gmpanelcatalog.Collector()
        self.catalog = self.catalogCollector.catalog
        self.maintenance = None

        self.legacy = None
        self.kit = uir1.Kit()
        self.actionButtons = {}
        self.sections = {}
        self.scroll = 0
        self.contentHeight = 0
        self.pending = None
        self.history = []
        self.card = None
        self.lastStatus = None
        self.refusal = None
        self.statusText = (u'', T.MUTED)
        self.pickerHits = []
        self.pickerEntry = None
        self.mapHits = []
        self.seen = {}
        self._Build()
        self.SetCenterPosition()
        self.Hide()

    def _SetGeometry(self):
        width = min(W, max(800, wndMgr.GetScreenWidth()))
        height = min(H, max(600, wndMgr.GetScreenHeight()))
        self.SetSize(width, height)
        self.PLAYER = (10, 31, width - 20, 56)
        self.LIST = (10, 95, width - 350, 434)
        self.FORM = (width - 330, 95, 320, 434)
        self.HISTORY = (10, 537, width - 20, height - 547)

    def _Refit(self):
        size = (min(W, max(800, wndMgr.GetScreenWidth())), min(H, max(600, wndMgr.GetScreenHeight())))
        if size == (self.GetWidth(), self.GetHeight()):
            return
        self._SetGeometry()
        self.chrome.frame.Resize(*size)
        header = self.chrome.header
        header.w = size[0]
        header.SetSize(size[0], header.GetHeight())
        header.SetTitle(TITLE)
        for panel, rect in ((self.playerPanel, self.PLAYER), (self.listPanel, self.LIST),
                            (self.formPanel, self.FORM), (self.historyPanel, self.HISTORY)):
            x, y, w, h = rect
            panel.SetPosition(x, y)
            panel.SetSize(w, h)
            panel.frame.Resize(w, h)
        self.searchField.SetWidth(self.LIST[2] - 2 * PAD)
        self.scrollBar.SetPosition(self.LIST[2] - PAD - T.SCROLL_W, SEARCH_H)
        self.emptyList.SetPosition(self.LIST[2] // 2, SEARCH_H + 8)
        for section in self.sections.values():
            section.w = self.LIST[2] - 2 * PAD
            section.SetSize(section.w, section.GetHeight())
            section.SetText(section.label.GetText())
        for band, when, label, detail, state in self.historyRows:
            band.SetSize(self.HISTORY[2] - 16, band.GetHeight())
            state.SetPosition(self.HISTORY[2] - 16, state.GetLocalPosition()[1])
        self._RefreshSummary()
        self._LayoutActions()
        self._RefreshHistory()
        x, y = self.GetLocalPosition()
        self.SetPosition(max(0, min(x, wndMgr.GetScreenWidth() - size[0])),
                         max(0, min(y, wndMgr.GetScreenHeight() - size[1])))

    # ------------------------------------------------------------------ build
    def _Panel(self, rect):
        x, y, w, h = rect
        panel = ui.Window()
        panel.SetParent(self)
        panel.SetPosition(x, y)
        panel.SetSize(w, h)
        panel.frame = uir1.Frame(panel, 0, 0, w, h, 'panel')
        panel.Show()
        return panel

    def _Text(self, parent, x, y, role='text_s', color=T.INK, align='left'):
        return uir1.Text(parent, u'', x, y, self.kit.font(role), Signed(color), align=align, valign='top')

    def _Edit(self, field, maximum):
        edit = field.edit
        edit.SetMax(maximum)
        edit.SetEscapeEvent(self._Safe(self.Close))
        return edit

    def _Build(self):
        kit = self.kit
        self.chrome = uir1.Chrome(self, kit, self.GetWidth(), self.GetHeight(), TITLE, on_close=self._Safe(self.Close))

        # Player
        top = self.playerPanel = self._Panel(self.PLAYER)
        self.playerLabel = self._Text(top, 10, 4, color=T.INK_DIM)        # kept: an unreferenced line is gone
        self.playerLabel.SetText(u'Hráč (pro akce na hráče)')
        self.playerField = uir1.Field(top, kit, 10, 24, 200, hint=u'Jméno postavy…', max_len=24)
        self.playerEdit = self._Edit(self.playerField, 24)
        self.playerEdit.SetReturnEvent(self._Safe(self._OnDetail))
        self.detailButton = uir1.Button(top, kit, 218, 23, 86, u'Detail', event=self._Safe(self._OnDetail))
        self.cardName = self._Text(top, 320, 8, 'text', T.IVORY)
        self.cardInfo = self._Text(top, 320, 29, 'text_s', T.MUTED)
        self.roleChip = Chip(top, kit)

        # Actions
        left = self.listPanel = self._Panel(self.LIST)
        left.OnMouseWheel = self._Safe(self._OnWheel)
        self.searchField = uir1.SearchField(left, kit, PAD, PAD, self.LIST[2] - 2 * PAD, hint=u'Hledat akci…', max_len=32,
                                            on_clear=self._Safe(self._LayoutActions))
        self._Edit(self.searchField, 32)
        self.scrollBar = uir1.ScrollBar(kit)
        self.scrollBar.SetParent(left)
        self.scrollBar.SetPosition(self.LIST[2] - PAD - T.SCROLL_W, SEARCH_H)
        self.scrollBar.SetScrollBarSize(self.LIST[3] - SEARCH_H - PAD)
        self.scrollBar.SetScrollEvent(self._Safe(self._OnScroll))
        self.scrollBar.Hide()
        self.emptyList = self._Text(left, self.LIST[2] // 2, SEARCH_H + 8, color=T.MUTED, align='center')

        # Form
        form = self.formPanel = self._Panel(self.FORM)
        self.formTitle = self._Text(form, FORM_X, 9, 'title', T.IVORY)
        self.roleTag = Chip(form, kit)
        self.protectTag = Chip(form, kit)
        self.protectTag.SetText(u'chrání vyšší GM')
        self.descLines = [self._Text(form, FORM_X, 32 + 17 * i, color=T.INK_DIM) for i in range(2)]

        self.refusalFill = uir1.Rect(form, FORM_X, 0, FORM_W, 44, WARN_FILL, 0.92)
        self.refusalLines = [uir1.Rect(form, FORM_X, 0, FORM_W, 1, WARN_LINE) for unused in range(2)] + \
                            [uir1.Rect(form, FORM_X, 0, 1, 44, WARN_LINE) for unused in range(2)]
        self.refusalTitle = self._Text(form, FORM_X + 10, 0, color=ERROR)
        self.refusalTitle.SetText(u'Odmítnuto serverem')
        self.refusalTexts = [self._Text(form, FORM_X + 10, 0, color=T.INK) for unused in range(2)]

        for name, maximum in (('target', 24), ('argument', 127), ('value', 12), ('secondary', 12),
                              ('reason', 95)):
            label = self._Text(form, FORM_X, 0, color=T.INK_DIM)
            field = uir1.Field(form, kit, FORM_X, 0, FORM_W, max_len=maximum)
            edit = self._Edit(field, maximum)
            edit.SetReturnEvent(self._Safe(self.ExecuteSelected))
            self.fieldRows[name] = (label, field, edit)
        self.valueGlyph = uir1.Glyph(self.fieldRows['value'][1], 'icon/search_%s.png', FORM_W - 20,
                                     (T.FIELD_H - T.ICON) // 2, T.ICON)
        self.presetButtons = []
        for seconds, text in X.MUTE_PRESETS:
            button = ActionButton(form, kit, text, False, self._Safe(lambda seconds=seconds, owner=proxy(self): owner._Preset(seconds)),
                                  center=True)
            self.presetButtons.append((seconds, button))
        self.minusButton = uir1.Button(form, kit, 0, 0, 24, '-', small=True,
                                       event=self._Safe(lambda owner=proxy(self): owner._Count(-1)), font=kit.font('text'))
        self.plusButton = uir1.Button(form, kit, 0, 0, 24, u'+', small=True,
                                      event=self._Safe(lambda owner=proxy(self): owner._Count(1)), font=kit.font('text'))
        self.mapLabel = self._Text(form, FORM_X, 0, color=T.INK_DIM)
        self.mapField = uir1.SearchField(form, kit, FORM_X, 0, FORM_W, hint=u'Název nebo číslo mapy…', max_len=32)
        self._Edit(self.mapField, 32)
        self.resultRows = [ResultRow(form, kit, FORM_W, self._Safe(self._PickResult)) for unused in range(RESULT_ROWS)]
        self.previewLabel = self._Text(form, FORM_X, 0, color=T.INK_DIM)
        self.previewLabel.SetText(u'Náhled ve hře')
        self.previewFrame = uir1.Frame(form, FORM_X, 0, FORM_W, 26, 'panel')
        self.previewText = self._Text(form, FORM_X + FORM_W // 2, 0, color=T.IVORY, align='center')

        self.askHint = self._Text(form, FORM_X, 0, color=T.MUTED)
        self.askHint.SetText(u'Před odesláním se zeptá')
        self.executeButton = uir1.Button(form, kit, 0, 0, 150, u'', primary=True,
                                         event=self._Safe(self.ExecuteSelected))
        self.confirmFill = uir1.Rect(form, FORM_X, 0, FORM_W, 84, WARN_FILL, 0.92)
        self.confirmLines = [uir1.Rect(form, FORM_X, 0, FORM_W, 1, WARN_LINE) for unused in range(2)] + \
                            [uir1.Rect(form, FORM_X, 0, 1, 84, WARN_LINE) for unused in range(2)]
        self.confirmDot = uir1.Rect(form, FORM_X + 12, 0, 4, 4, T.RED)
        self.confirmText = self._Text(form, FORM_X + 24, 0, 'text', T.IVORY)
        self.confirmNote = self._Text(form, FORM_X + 24, 0, color=T.INK_DIM)
        self.confirmNote.SetText(u'Akce se zapíše do auditu s důvodem.')
        self.backButton = uir1.Button(form, kit, 0, 0, 80, u'Zpět', small=True, event=self._Safe(self.CloseQuestion))
        self.acceptButton = uir1.Button(form, kit, 0, 0, 130, u'', primary=True, small=True,
                                        event=self._Safe(self._AcceptPending))
        self.statusLine = self._Text(form, FORM_X, 0, color=T.MUTED)
        self.emptyTitle = self._Text(form, self.FORM[2] // 2, 186, 'text', T.INK, align='center')
        self.emptyHint = self._Text(form, self.FORM[2] // 2, 210, color=T.MUTED, align='center')
        self.maintenance = MaintenanceForm(self, form, kit)

        # History
        bottom = self.historyPanel = self._Panel(self.HISTORY)
        self.historyTitle = self._Text(bottom, 10, 5, color=T.INK_DIM)
        self.historyTitle.SetText(u'Poslední akce')
        self.historyRows = []
        for index in range(HISTORY_ROWS):
            y = 26 + index * 21
            band = uir1.Rect(bottom, 8, y, self.HISTORY[2] - 16, 20, T.BAND_HOVER, 0.35)
            font = self.kit.font('text_s')
            top_ = uir1.CellTop(20, font)
            when = self._Text(bottom, 16, y + top_, color=T.MUTED)
            label = self._Text(bottom, 60, y + top_, color=T.INK)
            detail = self._Text(bottom, 0, y + top_, color=T.INK_DIM)
            state = self._Text(bottom, self.HISTORY[2] - 16, y + top_, align='right')
            self.historyRows.append((band, when, label, detail, state))
        self.historyEmpty = self._Text(bottom, 16, 26 + uir1.CellTop(20, self.kit.font('text_s')), color=T.MUTED)
        self.historyEmpty.SetText(u'V této relaci zatím žádná akce.')

        self._RefreshSummary()
        self._RefreshCard()
        self._LayoutActions()
        self._LayoutForm()
        self._RefreshHistory()

    # ------------------------------------------------------------------ failure: the original panel takes over
    def _Safe(self, function):
        # Widgets retain callbacks; neither this failure wrapper nor its bound
        # method may keep the whole window alive after interface teardown.
        owner = proxy(self)
        method = WeakMethod(function) if getattr(function, '__self__', None) is not None else None
        if method is not None:
            function = None
        def call(*args):
            try:
                if owner.legacy is not None:
                    return True
                callback = method() if method is not None else function
                return callback(*args) if callback is not None else True
            except ReferenceError:
                return True
            except Exception:
                owner._Fail()
                return True
        return call

    def _Fail(self):
        """Called from an except block: traces, builds the original panel with this panel's state and hands every
        later call to it."""
        Failed()
        if self.legacy is not None:
            return
        shown = self.IsShow()
        try:
            ui.Window.Hide(self)
        except Exception:
            pass
        panel = legacy.GMPanelWindow()
        for name in ('requestID', 'actionMask', 'gmLevel', 'capabilitiesLoaded', 'openAfterQuery'):
            setattr(panel, name, getattr(self, name))
        panel.SetCatalogCollector(self.catalogCollector)
        self.legacy = panel
        if shown and panel.actionMask:
            panel.Open()

    def Toggle(self):
        if self.legacy is None:
            try:
                return _LEGACY['Toggle'](self)
            except Exception:
                self._Fail()
        return self.legacy.Toggle()

    def OnServerResult(self, requestID, action, status, gmLevel, maskLow, maskHigh, message):
        if self.legacy is None:
            handled = False
            try:
                _LEGACY['OnServerResult'](self, requestID, action, status, gmLevel, maskLow, maskHigh, message)
                handled = True
                self._AfterResult(requestID, action, status, message)
                return
            except Exception:
                self._Fail()
                if handled:
                    return
        self.legacy.OnServerResult(requestID, action, status, gmLevel, maskLow, maskHigh, message)

    def Destroy(self):
        self.Close()
        if self.legacy is not None:
            self.legacy.Destroy()
        self.pending = None
        ui.Window.Hide(self)
        self.actionButtons = {}
        self.sections = {}

    def Open(self):
        if self.legacy is not None:
            return self.legacy.Open()
        if not self.actionMask:
            return
        self._Refit()
        self.SetCenterPosition()
        self.SetTop()
        self.Show()
        if not self._Player():
            self.playerEdit.SetFocus()

    def Close(self):
        if self.legacy is not None:
            return self.legacy.Close()
        self.CloseQuestion()
        for edit in self._Edits():
            edit.KillFocus()
        self.Hide()
        return True

    def OnPressEscapeKey(self):
        if self.legacy is None and (self.pending is not None or self._MaintenanceAsking()):
            self.CloseQuestion()
            return True
        return self.Close()

    def _Edits(self):
        return [self.playerEdit, self.searchField.edit, self.mapField.edit] + \
               [row[2] for row in self.fieldRows.values()] + (self.maintenance.Edits() if self.maintenance else [])

    # ------------------------------------------------------------------ what the original panel calls
    def _ApplyCatalog(self):
        self.catalog = self.catalogCollector.catalog
        self.CloseQuestion()
        self._DropButtons()
        self.selectedAction = None
        self.selectedCategory = None
        if self.capabilitiesLoaded:
            self._RefreshSummary()
            self._RefreshActions()
        else:
            self._LayoutForm()

    def _DropButtons(self):
        for widget in list(self.actionButtons.values()) + list(self.sections.values()):
            widget.Hide()
        self.actionButtons = {}
        self.sections = {}

    def _RefreshSummary(self):
        level = self.gmLevel
        text = u'Role: %s (%d)' % (X.RoleName(level, self._RoleName()), level)
        w = self.roleChip.SetText(text)
        self.roleChip.SetPosition(self.PLAYER[2] - 10 - w, (self.PLAYER[3] - Chip.H) // 2)
        self.roleChip.Show() if self.capabilitiesLoaded else self.roleChip.Hide()

    def _RefreshActions(self):
        self._RefreshSummary()                  # the original refreshes the summary before capabilitiesLoaded is set
        if self.selectedAction is not None and not self._Usable(self.selectedAction):
            self.selectedAction = None
        self._LayoutActions()
        self._LayoutForm()

    def _SetStatus(self, message):
        self.lastStatus = message
        text = X.Status(message)
        color = ERROR if message in X.FORM_ERRORS else T.MUTED
        self.statusText = (text, color)
        self._ShowStatus()

    def _ReadInteger(self, fieldName):
        """The value of an action with a search is the chosen hit, else the typed number (the original panel's)."""
        if fieldName == 'value' and self._Picker() and self.pickerEntry is not None:
            return int(self.pickerEntry['vnum'])
        return _LEGACY['_ReadInteger'](self, fieldName)

    def _OpenQuestion(self, unusedText, action, payload):
        """The second step inside the form (the original opens a question dialog with the same payload)."""
        info = self.catalog.Info(action)
        value, secondary, target, argument, unusedReason = payload
        entity = u''
        if info['picker'] and value > 0:
            entry = self.selectedEntities.get(info['picker'])
            entity = X.Unicode(entry['name']) if entry and entry['vnum'] == value else u'VNUM %d' % value
        self.pending = (action, payload)
        self.confirmQuestion = X.Question(action, info, target, entity, secondary, argument)
        self._LayoutForm()

    def _AcceptPending(self):
        if self.pending is not None:
            action, payload = self.pending
            self._AcceptQuestion(action, payload)

    def CloseQuestion(self):
        if self.pending is not None:
            self.pending = None
            self._LayoutForm()
        elif self._MaintenanceAsking():
            self.maintenance.Back()
        return True

    # ------------------------------------------------------------------ the "Údržba" section
    def _MaintenanceAllowed(self):
        """Only the highest GM level sees the section: the server limits /maintenance to it."""
        return bool(self.capabilitiesLoaded and self.gmLevel >= M.LEVEL)

    def _IsWorld(self, category):
        """The server's world category (its ASCII name), the home of the maintenance entry."""
        return category == WORLD_CATEGORY and X.Fold(self.catalog.CategoryLabel(category)) == \
            X.Fold(X.CATEGORIES[WORLD_CATEGORY])

    def _MaintenanceAsking(self):
        return bool(self.maintenance is not None and self.maintenance.pending is not None)

    def _Usable(self, action):
        return self._MaintenanceAllowed() if action == MAINTENANCE_ACTION else self._CanUse(action)

    def _SelectMaintenance(self):
        if not self._MaintenanceAllowed():
            self.selectedAction = None
        else:
            if self.selectedAction != MAINTENANCE_ACTION:
                self.maintenance.Reset()
                self.refusal = None
                self.statusText = (u'', T.MUTED)
                self.pickerEntry = None
                self.pickerHits = []
                self.mapHits = []
            self.pending = None
            self.selectedAction = MAINTENANCE_ACTION
        for other, button in self.actionButtons.items():
            button.SetSelected(other == self.selectedAction)
        self._LayoutForm()

    def _SendMaintenance(self, command, kind):
        """Types the command for the server and notes it in the history; returns the status line of the form."""
        sent = False
        try:
            sent = legacy.net.SendChatPacket(command) is not False
        except Exception:
            sent = False
        self.history.insert(0, {'request': None, 'action': MAINTENANCE_ACTION, 'time': time.strftime('%H:%M'),
                                'label': X.MAINTENANCE_LABEL,
                                'detail': command[len(M.COMMAND):].strip() or u'stop',
                                'state': 'sent' if sent else 'failed'})
        del self.history[HISTORY_KEEP:]
        self._RefreshHistory()
        return (X.MAINTENANCE_SENT, OK) if sent else (X.MAINTENANCE_FAILED, ERROR)

    def _SendSelected(self, action, payload, confirmed=False):
        before = self.requestID
        self.lastStatus = None
        _LEGACY['_SendSelected'](self, action, payload, confirmed)
        sent = self.requestID != before and self.lastStatus != X.SEND_FAILED
        self._Remember(self.requestID, action, payload, 'sent' if sent else 'failed')
        if sent:
            self.refusal = None
            self._LayoutForm()

    def _SelectMap(self, mapEntry):
        self.selectedMapIndex = int(mapEntry[0])
        self.selectedMapName = mapEntry[2]
        self._RefreshMapHits()

    # ------------------------------------------------------------------ results
    def _AfterResult(self, requestID, action, status, message):
        if action == legacy.net.GM_PANEL_ACTION_QUERY:
            return
        refused = status in (_Status('GM_PANEL_RESULT_DENIED', 2), _Status('GM_PANEL_RESULT_INVALID', 3),
                             _Status('GM_PANEL_RESULT_RATE_LIMITED', 4), _Status('GM_PANEL_RESULT_REPLAYED', 5))
        for entry in self.history:
            if entry['request'] == requestID and entry['action'] == action:
                entry['state'] = 'refused' if refused else 'ok'
                break
        self._RefreshHistory()
        card = X.PlayerCard(message)
        if card is not None and X.Fold(card['name']) == X.Fold(self._Player()):
            self.card = card
            self._RefreshCard()
        if action != self.selectedAction:
            return
        if refused:
            self.refusal = X.Result(message) or u'Server akci odmítl.'
            self.statusText = (u'', T.MUTED)
        else:
            self.refusal = None
            self.statusText = (X.Result(message), OK)
        self._LayoutForm()

    def _Remember(self, requestID, action, payload, state):
        info = self.catalog.Info(action)
        value, secondary, target, argument, unusedReason = payload
        fields = info['fields']
        parts = []
        if 'target' in fields and target:
            parts.append(X.Unicode(target))
        if X.Presets(action, info) == 'mute':
            parts.append(X.Duration(value))
        elif info['picker'] and value > 0:
            entry = self.selectedEntities.get(info['picker'])
            name = X.Unicode(entry['name']) if entry and entry['vnum'] == value else u'VNUM %d' % value
            parts.append(u'%s × %d' % (name, secondary))
        elif 'map' in fields and value > 0:
            parts.append(_MapName(value))
        elif 'value' in fields and 'secondary' in fields:
            parts.append(u'%d, %d' % (value, secondary))
        elif 'value' in fields:
            parts.append(u'%d' % value)
        if 'argument' in fields and argument:
            parts.append(X.Unicode(argument))
        self.history.insert(0, {'request': requestID, 'action': action, 'time': time.strftime('%H:%M'),
                                'label': X.ActionLabel(action, info), 'detail': u' · '.join(parts),
                                'state': state})
        del self.history[HISTORY_KEEP:]
        self._RefreshHistory()

    def _RefreshHistory(self):
        states = {'sent': (u'odesláno', T.MUTED), 'ok': (u'přijato', OK), 'refused': (u'odmítnuto', ERROR),
                  'failed': (u'neodesláno', ERROR)}
        for index, (band, when, label, detail, state) in enumerate(self.historyRows):
            widgets = (band, when, label, detail, state)
            if index >= len(self.history) or band.GetLocalPosition()[1] + band.GetHeight() > self.HISTORY[3]:
                for widget in widgets:
                    widget.Hide()
                continue
            entry = self.history[index]
            when.SetText(entry['time'])
            label.SetText(entry['label'])
            text, color = states[entry['state']]
            state.SetText(text)
            state.SetPackedFontColor(Signed(color))
            x = 60 + uir1.TextWidth(label) + 10
            detail.SetPosition(x, label.GetLocalPosition()[1])
            uir1.Fit(detail, entry['detail'], self.HISTORY[2] - 16 - uir1.TextWidth(state) - 16 - x)
            for widget in widgets:
                widget.Show()
        self.historyEmpty.Show() if not self.history else self.historyEmpty.Hide()

    # ------------------------------------------------------------------ player
    def _Player(self):
        return self.playerEdit.GetText().strip()

    def _NeedsPlayer(self, action):
        info = self.catalog.Info(action)
        return 'target' in info['fields'] and not info['plain']

    def _OnDetail(self):
        action = X.DETAIL_ACTION
        if not self._Player() or not self._CanUse(action) or not X.IsKnown(action, self.catalog.Info(action)):
            return True
        self.SelectAction(action)
        self.ExecuteSelected()
        return True

    def _OnPlayerChanged(self, previous, player):
        target = self.fieldRows['target'][2]
        if not target.GetText().strip() or target.GetText().strip() == previous:
            target.SetText(player)
        if self.card is not None and X.Fold(self.card['name']) != X.Fold(player):
            self.card = None
        if not player and self.selectedAction is not None and self._NeedsPlayer(self.selectedAction):
            self.selectedAction = None
            self.pending = None
        self._RefreshCard()
        self._RefreshDimming()
        self._LayoutForm()

    def _RefreshCard(self):
        player = X.Unicode(self._Player())
        detail = X.DETAIL_ACTION
        canDetail = bool(player) and self._CanUse(detail) and X.IsKnown(detail, self.catalog.Info(detail))
        self.detailButton.Enable() if canDetail else self.detailButton.Disable()
        if not player:
            self.cardName.SetText(u'')
            self.cardInfo.SetPosition(320, 19)
            self.cardInfo.SetText(u'Bez hráče: akce na hráče jsou ztlumené.')
            self.cardInfo.SetPackedFontColor(Signed(T.MUTED))
            return
        self.cardInfo.SetPosition(320, 29)
        card = self.card
        name = player
        if card is None:
            self.cardName.SetText(name)
            self.cardInfo.SetText(u'Stav ukáže Detail.' if canDetail else u'')
            self.cardInfo.SetPackedFontColor(Signed(T.MUTED))
            return
        extra = []
        if card['level'] is not None:
            extra.append(u'Lv %d' % card['level'])
        if card['job']:
            extra.append(card['job'])
        self.cardName.SetText(X.Unicode(card['name']) + (u'   ' + u' · '.join(extra) if extra else u''))
        if card['online']:
            self.cardInfo.SetText(u'Online · CH %d · %s' % (card['channel'], _MapName(card['map'])))
            self.cardInfo.SetPackedFontColor(Signed(OK))
        else:
            self.cardInfo.SetText(u'Není online')
            self.cardInfo.SetPackedFontColor(Signed(T.MUTED))

    def _RefreshDimming(self):
        player = bool(self._Player())
        for action, button in self.actionButtons.items():
            if player or not self._NeedsPlayer(action):
                button.Enable()
            else:
                button.Disable()

    # ------------------------------------------------------------------ the action list
    def _ActionButton(self, action):
        button = self.actionButtons.get(action)
        if button is None:
            if action == MAINTENANCE_ACTION:
                label, confirm = X.MAINTENANCE_LABEL, True
            else:
                info = self.catalog.Info(action)
                label, confirm = X.ActionLabel(action, info), info['confirm']
            button = ActionButton(self.listPanel, self.kit, label, confirm,
                                  self._Safe(lambda action=action, owner=proxy(self): owner.SelectAction(action)))
            button.OnMouseWheel = self._Safe(self._OnWheel)
            self.actionButtons[action] = button
        return button

    def _Section(self, category):
        section = self.sections.get(category)
        if section is None:
            section = uir1.Section(self.listPanel, self.kit, PAD, 0, self.LIST[2] - 2 * PAD, u'', Signed(T.INK_DIM))
            self.sections[category] = section
        return section

    def _Matches(self, action, query):
        if not query:
            return True
        info = self.catalog.Info(action)
        return query in X.Fold(X.ActionLabel(action, info)) or query in X.Fold(info['label'])

    def _Rows(self):
        """[(kind, key, items)]: a section heading or a row of up to three actions, in the server's order."""
        query = X.Fold(self.searchField.edit.GetText().strip())
        actions = self.catalog.Actions(self.actionMask) if self.capabilitiesLoaded else []
        rows = []
        maintenance = self._MaintenanceAllowed() and (not query or query in X.Fold(X.MAINTENANCE_LABEL) or
                                                      query in u'maintenance')
        placed = False
        for category in self.catalog.Categories(self.actionMask) if actions else []:
            shown = [action for action in actions if self.catalog.Info(action)['category'] == category and
                     self._Matches(action, query)]
            if maintenance and not placed and self._IsWorld(category):
                # Last of the world actions, where the owner's mock-up has it; the list does not grow a section.
                shown.append(MAINTENANCE_ACTION)
                placed = True
            if not shown:
                continue
            rows.append(('section', category, len(shown)))
            for start in range(0, len(shown), COLS):
                rows.append(('actions', category, shown[start:start + COLS]))
        if maintenance and not placed:
            rows.append(('section', MAINTENANCE_CATEGORY, 1))
            rows.append(('actions', MAINTENANCE_CATEGORY, [MAINTENANCE_ACTION]))
        return rows

    def _LayoutActions(self):
        rows = self._Rows()
        top, bottom = SEARCH_H, self.LIST[3] - PAD
        height = 0
        for kind, unusedKey, unusedItems in rows:
            height += SECTION_H if kind == 'section' else ROW_STEP
        height += SECTION_GAP * max(0, sum(1 for row in rows if row[0] == 'section') - 1)
        self.contentHeight = height
        overflow = max(0, height - (bottom - top))
        if overflow:
            self.scrollBar.SetMiddleBarSize(float(bottom - top) / height)
            self.scrollBar.Show()
        else:
            self.scrollBar.Hide()
        self.scroll = max(0, min(self.scroll, overflow))
        inner = self.LIST[2] - 2 * PAD - (T.SCROLL_W + 6 if overflow else 0)
        colW = (inner - (COLS - 1) * GAP) // COLS

        used = set()
        y = top - self.scroll
        first = True
        for kind, key, items in rows:
            if kind == 'section':
                if not first:
                    y += SECTION_GAP
                first = False
                section = self._Section(key)
                label = X.MAINTENANCE_SECTION if key == MAINTENANCE_CATEGORY else \
                    X.CategoryLabel(key, self.catalog.CategoryLabel(key))
                section.SetText(u'%s (%d)' % (label, items))
                section.SetPosition(PAD, y)
                used.add(('s', key))
                visible = y >= top and y + SECTION_H <= bottom
                section.Show() if visible else section.Hide()
                y += SECTION_H
                continue
            for column, action in enumerate(items):
                button = self._ActionButton(action)
                button.Place(PAD + column * (colW + GAP), y, colW)
                button.SetSelected(action == self.selectedAction)
                used.add(('a', action))
                visible = y >= top and y + ROW <= bottom
                button.Show() if visible else button.Hide()
            y += ROW_STEP
        for category, section in self.sections.items():
            if ('s', category) not in used:
                section.Hide()
        for action, button in self.actionButtons.items():
            if ('a', action) not in used:
                button.Hide()
        if not rows:
            self.emptyList.SetText(u'Žádná akce neodpovídá hledání.' if self.capabilitiesLoaded and
                                   self.catalog.Actions(self.actionMask) else u'Načítám akce…')
            self.emptyList.Show()
        else:
            self.emptyList.Hide()
        self._RefreshDimming()

    def _OnScroll(self):
        overflow = max(0, self.contentHeight - (self.LIST[3] - PAD - SEARCH_H))
        self.scroll = int(round(self.scrollBar.GetPos() * overflow))
        self._LayoutActions()

    def _OnWheel(self, delta):
        if not self.scrollBar.IsShow():
            return True
        overflow = max(1, self.contentHeight - (self.LIST[3] - PAD - SEARCH_H))
        step = float(ROW_STEP * 2) / overflow
        self.scrollBar.SetPos(self.scrollBar.GetPos() + (-step if delta > 0 else step))
        return True

    # ------------------------------------------------------------------ the form
    def SelectAction(self, action):
        if action == MAINTENANCE_ACTION:
            return self._SelectMaintenance()
        if action is None or not self._CanUse(action):
            self.selectedAction = None
            self._LayoutActions()
            self._LayoutForm()
            return
        previous = self.selectedAction
        self.pending = None
        self.selectedAction = action
        info = self.catalog.Info(action)
        if previous != action:
            self.refusal = None
            self.statusText = (u'', T.MUTED)
            rows = self.fieldRows
            rows['target'][2].SetText(self._Player())
            for name in ('argument', 'value', 'secondary'):
                rows[name][2].SetText('')
            self.pickerEntry = None
            self.pickerHits = []
            self.mapField.edit.SetText('')
            if info['picker']:
                rows['secondary'][2].SetText('1')
        for other, button in self.actionButtons.items():
            button.SetSelected(other == action)
        self._RefreshMapHits()
        self._LayoutForm()

    def _Picker(self):
        if self.selectedAction is None:
            return None
        return self.catalog.Info(self.selectedAction)['picker']

    def _Hide(self, *widgets):
        for widget in widgets:
            widget.Hide()

    def _Box(self, fill, lines, y, h):
        fill.SetPosition(FORM_X, y)
        fill.SetSize(FORM_W, h)
        top, bottom, left, right = lines
        top.SetPosition(FORM_X, y)
        bottom.SetPosition(FORM_X, y + h - 1)
        left.SetPosition(FORM_X, y)
        left.SetSize(1, h)
        right.SetPosition(FORM_X + FORM_W - 1, y)
        right.SetSize(1, h)
        for widget in [fill] + list(lines):
            widget.Show()

    def _ShowStatus(self):
        text, color = self.statusText
        line = self.statusLine
        if not text or self.selectedAction is None or self.pending is not None:
            line.Hide()
            return
        uir1.Fit(line, text, FORM_W)
        line.SetPackedFontColor(Signed(color))
        line.Show()

    def _LayoutForm(self):
        rows = self.fieldRows
        everything = [self.formTitle, self.roleTag, self.protectTag, self.refusalFill, self.refusalTitle,
                      self.valueGlyph, self.minusButton, self.plusButton, self.mapLabel,
                      self.mapField, self.previewLabel, self.previewFrame, self.previewText, self.askHint,
                      self.executeButton, self.confirmFill, self.confirmDot, self.confirmText, self.confirmNote,
                      self.backButton, self.acceptButton, self.statusLine, self.emptyTitle, self.emptyHint]
        everything += self.descLines + self.refusalTexts + self.refusalLines + self.confirmLines + self.resultRows
        everything += [button for unused, button in self.presetButtons]
        for label, field, unusedEdit in rows.values():
            everything += [label, field]
        self._Hide(*everything)
        self.maintenance.Hide()

        action = self.selectedAction
        if action == MAINTENANCE_ACTION:
            self.maintenance.Layout()
            return
        if action is None:
            if self.capabilitiesLoaded and self.actionMask:
                self.emptyTitle.SetText(u'Vyber akci vlevo.')
                self.emptyHint.SetText(u'' if self._Player() else u'Akce na hráče se odemknou po zadání jména.')
            else:
                self.emptyTitle.SetText(X.Status(self.lastStatus) if self.lastStatus else u'Načítám oprávnění…')
                self.emptyHint.SetText(u'')
            self.emptyTitle.Show()
            self.emptyHint.Show()
            return

        info = self.catalog.Info(action)
        self.formTitle.SetText(X.ActionLabel(action, info).upper())
        self.formTitle.Show()
        x = FORM_X + uir1.TextWidth(self.formTitle) + 10
        role = X.MinimumRole(action, info)
        if role is not None:
            x += self.roleTag.SetText(X.RoleTag(role)) + 6
            self.roleTag.SetPosition(x - self.roleTag.w - 6, 8)
            self.roleTag.Show()
        if X.ProtectsGM(action, info):
            self.protectTag.SetPosition(x, 8)
            self.protectTag.Show()

        y = 32
        description = X.Description(action, info)
        for line, text in zip(self.descLines, self._Wrap(description, FORM_W, 2)):
            line.SetPosition(FORM_X, y)
            line.SetText(text)
            line.Show()
            y += 17
        y += 8

        if self.refusal and self.pending is None:
            lines = self._Wrap(self.refusal, FORM_W - 20, 2, self.refusalTexts[0])
            h = 24 + 17 * len(lines) + 4
            self._Box(self.refusalFill, self.refusalLines, y, h)
            self.refusalTitle.SetPosition(FORM_X + 10, y + 4)
            self.refusalTitle.Show()
            for index, (line, text) in enumerate(zip(self.refusalTexts, lines)):
                line.SetPosition(FORM_X + 10, y + 22 + 17 * index)
                line.SetText(text)
                line.Show()
            y += h + 10

        required = u'' if info['plain'] else u' *'
        picker = info['picker']
        for name in info['fields']:
            if name == 'map':
                self.mapLabel.SetText(X.FieldLabel(action, info, 'map') + required)
                self.mapLabel.SetPosition(FORM_X, y)
                self.mapField.SetPosition(FORM_X, y + 18)
                self._ShowAll(self.mapLabel, self.mapField)
                y += FIELD_STEP
                y = self._ShowHits(self.mapHits, y - 4, self._MapRow)
                continue
            label, field, edit = rows[name]
            label.SetText(X.FieldLabel(action, info, name) + required)
            label.SetPosition(FORM_X, y)
            field.SetPosition(FORM_X, y + 18)
            width = FORM_W
            if name == 'value' and X.Presets(action, info) == 'mute':
                width = 70
                bx = FORM_X + width + 6
                bw = (FORM_W - width - 6) // len(self.presetButtons)
                current = edit.GetText().strip()
                for seconds, button in self.presetButtons:
                    button.Place(bx, y + 18 + 1, bw)
                    button.SetSelected(current == str(seconds))
                    button.Show()
                    bx += bw
            elif name == 'secondary' and X.CountLimit(action, info):
                width = 70
                self.minusButton.SetPosition(FORM_X + width + 6, y + 18 + 1)
                self.plusButton.SetPosition(FORM_X + width + 6 + 24 + 4, y + 18 + 1)
                self._ShowAll(self.minusButton, self.plusButton)
            field.trail = 20 if (name == 'value' and picker) else 0
            field.SetWidth(width)
            self._ShowAll(label, field)
            y += FIELD_STEP
            if name == 'value' and picker:
                self.valueGlyph.Show()
                y = self._ShowHits(self.pickerHits, y - 4, self._EntityRow)
            if name == 'argument' and X.HasPreview(action, info):
                self.previewLabel.SetPosition(FORM_X, y)
                self.previewFrame.SetPosition(FORM_X, y + 18)
                self.previewText.SetPosition(FORM_X + FORM_W // 2, y + 18 + uir1.CellTop(26, self.kit.font('text_s')))
                uir1.Fit(self.previewText, X.Unicode(edit.GetText()), FORM_W - 16)
                self._ShowAll(self.previewLabel, self.previewFrame, self.previewText)
                y += 18 + 26 + 8

        y += 4
        if self.pending is not None:
            self._Box(self.confirmFill, self.confirmLines, y, 84)
            self.confirmDot.SetPosition(FORM_X + 12, y + 16)
            self.confirmText.SetPosition(FORM_X + 24, y + 8)
            uir1.Fit(self.confirmText, self.confirmQuestion, FORM_W - 34)
            self.confirmNote.SetPosition(FORM_X + 24, y + 30)
            self.acceptButton.SetText(self._YesLabel(action, info))
            self.backButton.SetPosition(FORM_X + FORM_W - 12 - self.backButton.w, y + 54)
            self.acceptButton.SetPosition(FORM_X + FORM_W - 12 - self.backButton.w - 8 - self.acceptButton.w, y + 54)
            self._ShowAll(self.confirmDot, self.confirmText, self.confirmNote, self.backButton, self.acceptButton)
            y += 84 + 8
        else:
            self.executeButton.SetText(self._ExecuteText(action, info))
            self.executeButton.FitWidth(150)
            if self.executeButton.w > FORM_W:
                self.executeButton.SetWidth(FORM_W)
            self.executeButton.SetPosition(FORM_X + FORM_W - self.executeButton.w, y)
            self.executeButton.Show()
            if info['confirm'] and FORM_W - self.executeButton.w > uir1.TextWidth(self.askHint) + 10:
                self.askHint.SetPosition(FORM_X, y + uir1.CellTop(T.BTN_H, self.kit.font('text_s')))
                self.askHint.Show()
            y += T.BTN_H + 8
        self.statusLine.SetPosition(FORM_X, y)
        self._ShowStatus()

    def _ShowAll(self, *widgets):
        for widget in widgets:
            widget.Show()

    def _Wrap(self, text, width, count, probe=None):
        probe = probe or self.descLines[0]
        lines, current = [], u''
        for word in text.split():
            candidate = (current + u' ' + word).strip()
            probe.SetText(candidate)
            if not current or uir1.TextWidth(probe) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        if len(lines) > count:
            rest = u' '.join(lines[count - 1:])
            lines = lines[:count - 1] + [rest]
            uir1.Fit(probe, rest, width)
            lines[-1] = probe.GetText()
        return lines

    def _ExecuteText(self, action, info):
        text = X.ExecuteLabel(action, info)
        if info['picker'] and self.pickerEntry is not None:
            count = self.fieldRows['secondary'][2].GetText().strip()
            return u'%s %s× %s' % (text, X.Unicode(count) or u'1', X.Unicode(self.pickerEntry['name']))
        return text

    def _YesLabel(self, action, info):
        words = X.ExecuteLabel(action, info).split()
        return u'Ano, %s' % (words[0].lower() if words else u'provést')

    # ------------------------------------------------------------------ helpers of the form
    def _Preset(self, seconds):
        self.fieldRows['value'][2].SetText(str(seconds))
        self._LayoutForm()

    def _Count(self, step):
        action = self.selectedAction
        if action is None:
            return
        limit = X.CountLimit(action, self.catalog.Info(action)) or 1
        edit = self.fieldRows['secondary'][2]
        try:
            current = int(edit.GetText().strip() or '0')
        except ValueError:
            current = 0
        edit.SetText(str(max(1, min(limit, current + step))))
        self._LayoutForm()

    def _ShowHits(self, hits, y, describe):
        for row, entry in zip(self.resultRows, hits[:RESULT_ROWS]):
            name, detail, selected = describe(entry)
            row.SetEntry(entry, name, detail)
            row.SetSelected(selected)
            row.SetPosition(FORM_X, y)
            row.Show()
            y += RESULT_H
        return y + (6 if hits else 0)

    def _EntityRow(self, entry):
        selected = self.pickerEntry is not None and self.pickerEntry['vnum'] == entry['vnum']
        return X.Unicode(entry['name']), u'VNUM %d' % entry['vnum'], selected

    def _MapRow(self, entry):
        return X.Unicode(entry[2]), u'%03d' % entry[0], entry[0] == self.selectedMapIndex

    def _PickResult(self, entry):
        if isinstance(entry, tuple):
            self._SelectMap(entry)
        else:
            mode = self._Picker()
            if not mode:
                return
            self.pickerEntry = entry
            self.selectedEntities[mode] = entry
            recent = _EntitySource.RECENT[mode]
            if entry['vnum'] in recent:
                recent.remove(entry['vnum'])
            recent.insert(0, entry['vnum'])
            del recent[12:]
            if not self.fieldRows['secondary'][2].GetText().strip():
                self.fieldRows['secondary'][2].SetText('1')
        self._LayoutForm()

    def _RefreshPicker(self):
        mode = self._Picker()
        if not mode:
            self.pickerHits = []
            return
        hits = _EntitySource(mode).Search(self.fieldRows['value'][2].GetText())
        if self.pickerEntry is not None and self.pickerEntry['vnum'] not in [hit['vnum'] for hit in hits]:
            self.pickerEntry = None
        self.pickerHits = hits

    def _RefreshMapHits(self):
        action = self.selectedAction
        if action is None or 'map' not in self.catalog.Info(action)['fields']:
            self.mapHits = []
            return
        query = self.mapField.edit.GetText().strip()
        hits = _MapEntries(query) if query else []
        if not query and self.selectedMapIndex > 0:
            hits = [entry for entry in _MapEntries(str(self.selectedMapIndex)) if entry[0] == self.selectedMapIndex]
        self.mapHits = hits

    # ------------------------------------------------------------------ polling of the edit lines
    def OnUpdate(self):
        if self.legacy is not None or not self.IsShow():
            return
        try:
            self._Refit()
            self._Poll()
        except Exception:
            self._Fail()

    def _Changed(self, key, text):
        previous = self.seen.get(key)
        if previous == text:
            return False, previous
        self.seen[key] = text
        return True, previous

    def _Poll(self):
        changed, previous = self._Changed('player', self._Player())
        if changed:
            self._OnPlayerChanged((previous or '').strip(), self._Player())
        changed, unused = self._Changed('search', self.searchField.edit.GetText())
        if changed:
            self.scroll = 0
            self._LayoutActions()
        relayout = False
        for name in ('value', 'secondary', 'argument'):
            changed, unused = self._Changed(name, self.fieldRows[name][2].GetText())
            if changed:
                relayout = True
                if name == 'value':
                    self._RefreshPicker()
        changed, unused = self._Changed('map', self.mapField.edit.GetText())
        if changed:
            self._RefreshMapHits()
            relayout = True
        changed, unused = self._Changed('action', self.selectedAction)
        if changed:
            self._RefreshPicker()
            self._RefreshMapHits()
            relayout = True
        changed, unused = self._Changed('maintenance', self.maintenance.Signature())
        if changed and self.selectedAction == MAINTENANCE_ACTION:
            self.maintenance.pending = None
            relayout = True
        if relayout and self.selectedAction is not None:
            self._LayoutForm()


# The original panel's request, catalogue and capability code (see _BORROWED), unchanged.
for _name in _BORROWED:
    setattr(GMPanelR1Window, _name, _LEGACY[_name])
del _name
