# -*- coding: utf-8 -*-
"""The messenger (Zprávy, uiunifiedmessenger.UnifiedMessengerWindow) in the Althea R1 look "Krvavá žíla".

The window keeps its 720 x 461 size, the uiscript UnifiedMessengerWindow and every function: the conversation list
with the search (filter after a short pause), selecting a conversation, the new message dialog, the unread count, the
header actions (market offers, add friend, block, delete the conversation, settings), the history with day and unread
separators, item links, copying by a double click, retrying a failed message, paging older / newer messages with the
scroll bar and the mouse wheel, typing notices, the composer (Enter sends, Esc closes, up to 512 characters, the
codepage) and the settings (unread badge, sound, notification, message preview, clearing the local history). This
module draws the R1 look INTO the window:

* the R1 frame and header "Zprávy" on the window's board, the left column, the header strip and the history as R1
  panels (also drawn into the board, so everything of the window lies above them); the crimson art is hidden;
* the search as an R1 field around the original edit line, the "Nepřečtené: n" line, conversation rows in R1
  (band, the original portraits and presence dots, the unread count as a small dark badge), R1 scroll bars;
* the header actions and the new message button as dark R1 buttons with the ORIGINAL icons (uir1friends.IconButton
  follows the window's Enable / Disable / Show / Hide on the originals);
* message bubbles in graphite (incoming with a graphite outline, mine with the vein along the bottom edge); the
  message text keeps the game's default font, like the chat;
* a thinner composer: one line (the original edit line in an R1 field) with "Poslat" next to it; a longer message
  wraps and the field grows upwards line by line; the history gets the freed height;
* the settings as a small R1 panel "Nastavení zpráv" with check boxes instead of the ON / OFF buttons and the button
  "Vymazat místní historii".

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window; a failure while building the R1 look
restores it (traced to syserr) and the R1 look is not tried again in this session.
"""
from _weakref import ref

import ui

import uir1
import uir1drag
import uir1friends as F
import uir1layout as L
import uir1tokens as T

WIDTH, HEIGHT = 720, 461
LEFT = (10, 33, 206, 418)               # left column panel
SEARCH = (18, 41, 156)                  # search field
NEW_BUTTON = (180, 42, 28)              # new message button (22 px)
UNREAD = (20, 77)                       # "Nepřečtené: n"
LIST = (12, 91, 190, 350)               # conversation rows (7 x 50 px)
LIST_SCROLL = (204, 91, 350)
HEAD = (226, 33, 484, 46)               # header strip: portrait, name, presence, actions
TITLE = (274, 40)
PRESENCE = (275, 64)
ACTIONS = (537, 45, 30, 33)             # x, y, width, pitch of the five header actions (22 px)
ACTION_NAMES = (('MarketButton', 'MarketIcon'), ('AddFriendButton', 'AddFriendIcon'), ('BlockButton', 'BlockIcon'),
                ('DeleteConversationButton', 'DeleteIcon'), ('SettingsButton', 'SettingsIcon'))
HISTORY = (226, 85, 484, 332)           # history panel
HISTORY_PANE = (230, 89, 462, 310)      # the message rows (viewport 310 px; the original had 303)
HISTORY_SCROLL = (700, 89, 310)
TYPING = (238, 401)
COMPOSER = (226, 426, 392)              # the composer field; it grows upwards for a wrapped message
SEND = (624, 425, 86)                   # "Poslat" (26 px, primary)
COMPOSER_MAX_LINES = 4
SETTINGS = (474, 73, 230, 164)          # the settings panel under the settings button
CONVERSATION_ROWS = 7
ROW_W, ROW_H = 190, 50
BUBBLE_W = 300
MINIMIZE_GAP = 4                        # between the "_" hit box and the X hit box
MINIMIZE_COLORS = {'normal': 0xFF968C8C, 'hover': 0xFFF42922, 'pressed': 0xFFD30D0E, 'disabled': 0xFF5A5450}


def Tr(czech, english):
    return F.Tr(czech, english)


# --------------------------------------------------------------------------- title bar "_"
class MinimizeButton(uir1.Interactive):
    """The "_" left of the header's plain X: the same 20 px hit box, a 10 x 2 px bar on the X glyph's bottom line,
    in the X's colours (grey, red under the mouse, blood red pressed)."""

    def __init__(self, parent, x, y, event=None):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(T.X_HIT, T.X_HIT)
        pad = (T.X_HIT - T.X_SIZE) // 2
        self.bar = ui.Bar()
        self.bar.SetParent(self)
        self.bar.AddFlag('not_pick')
        self.bar.SetPosition(pad, pad + T.X_SIZE - 2)
        self.bar.SetSize(T.X_SIZE, 2)
        self.bar.Show()
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        # ui.Bar takes an engine colour (grp.GenerateColor), not a packed 0xAARRGGBB int: the packed value drew the
        # bar black and the "_" vanished next to the X (owner's screenshot, 12. 10. 2026).
        self.bar.SetColor(uir1.GenerateColor(MINIMIZE_COLORS[self.state()]))


# --------------------------------------------------------------------------- conversation row
class ConversationRow(ui.Window):
    """One conversation in R1 (the API of uiunifiedmessenger.ConversationRow): band (hover / selected with the red
    line), the original portrait and presence dot, name and time, the last message, the unread count badge."""

    HEIGHT = ROW_H

    def __init__(self):
        ui.Window.__init__(self)
        self.SetSize(ROW_W, ROW_H)
        self.key = ''
        self.name = ''
        self.selectEvent = None
        self.selected = False
        self.hovered = False
        kit = uir1.Kit()
        self.band = uir1.Band(self, 0, 0, ROW_W, ROW_H - 1)
        self.rule = uir1.Rect(self, 6, ROW_H - 1, ROW_W - 12, 1, T.LINE, 0.6)
        self.avatarIcon = ui.ImageBox()
        self.avatarIcon.SetParent(self)
        self.avatarIcon.AddFlag('not_pick')
        self.avatarIcon.SetPosition(6, 9)
        self.avatarIcon.Show()
        self.presence = ui.ImageBox()
        self.presence.SetParent(self)
        self.presence.AddFlag('not_pick')
        self.presence.SetPosition(29, 33)
        self.presence.Hide()
        # Row texts are top-aligned lines (uir1.RowText rule): name / time in the upper half, the last message in the
        # lower half, every cell inside the row.
        self.nameLine = uir1.RowText(self, '', 44, ROW_H // 2 + 2, kit.font('text_sb'), T.INK)
        self.timeLine = uir1.RowText(self, '', ROW_W - 8, ROW_H // 2 + 2, kit.font('text_s'), T.MUTED,
                                     align='right')
        self.previewLine = uir1.RowText(self, '', 44, ROW_H // 2 - 2, kit.font('text_s'), T.INK_DIM)
        self.previewLine.SetPosition(44, ROW_H // 2 - 2 + uir1.CellTop(ROW_H // 2 - 2, kit.font('text_s')))
        self.badge = F.CountBadge(self, kit, ROW_W - 8, 34)

    def SetConversation(self, row, selected, selectEvent):
        import uiunifiedmessenger as M
        self.key = row['key']
        self.name = row['name']
        self.selectEvent = selectEvent
        if str(self.key).startswith('guild:'):
            self.avatarIcon.LoadImage(M.CRIMSON_MESSENGER_IMG_DIR + 'icon/guild_conversation.png')
            self.avatarIcon.SetPosition(10, 13)
        else:
            self.avatarIcon.LoadImage(M._CrimsonResolvePortrait(self.key, self.name))
            self.avatarIcon.SetPosition(6, 9)
        online = row.get('online')
        if online is None:
            self.presence.Hide()
        else:
            self.presence.LoadImage(M.CRIMSON_MESSENGER_IMG_DIR + 'icon/' +
                                    ('presence_online.png' if online else 'presence_offline.png'))
            self.presence.Show()
        unread = int(row.get('unread', 0) or 0)
        self.badge.SetCount(unread)
        time_text = row.get('display_time', '')
        self.timeLine.SetText(time_text)
        uir1.Fit(self.nameLine, self.name, ROW_W - 44 - 12 - uir1.TextWidth(self.timeLine))
        badge_w = self.badge.GetWidth() + 6 if unread else 0
        uir1.Fit(self.previewLine, row.get('preview', ''), ROW_W - 44 - 8 - badge_w)
        self.SetSelected(selected)

    def RefreshPortrait(self):
        if str(self.key).startswith('guild:'):
            return
        import uiunifiedmessenger as M
        self.avatarIcon.LoadImage(M._CrimsonResolvePortrait(self.key, self.name))
        self.avatarIcon.SetPosition(6, 9)

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self._Paint()

    def _Paint(self):
        state = 'selected' if self.selected else ('hover' if self.hovered else 'normal')
        F.PaintBand(self.band, state)
        self.rule.Hide() if self.selected else self.rule.Show()
        self.nameLine.SetPackedFontColor(T.IVORY if self.selected else T.INK)

    def OnMouseOverIn(self):
        self.hovered = True
        self._Paint()

    def OnMouseOverOut(self):
        self.hovered = False
        self._Paint()

    def OnMouseLeftButtonDown(self):
        if self.selectEvent:
            self.selectEvent(self.name, self.key)


# --------------------------------------------------------------------------- message bubble
class Bubble(ui.Window):
    """Graphite message bubble (the API of uiunifiedmessenger._CrimsonMessageBubble): incoming with a graphite
    outline, outgoing (mine) a shade warmer with the red vein along its bottom edge."""

    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('not_pick')
        self.outgoing = False
        self.fill = uir1.Rect(self, 1, 1, BUBBLE_W - 2, 36, 0x181616, 0.94)
        self.rims = [uir1.Rect(self, 0, 0, 1, 1, 0x403A3A) for unused in range(4)]
        self.vein = uir1.Vein(self, 4, 37, BUBBLE_W - 8)
        self.vein.Hide()
        self.SetBubbleHeight(38)

    def LoadKind(self, kind):
        self.outgoing = kind == 'outgoing'
        self.fill.SetColor(uir1.GenerateColor(0x1E1617 if self.outgoing else 0x181616, 0.94))
        for rim in self.rims:
            rim.SetColor(uir1.GenerateColor(0x4E282A if self.outgoing else 0x403A3A))
        self.vein.Show() if self.outgoing else self.vein.Hide()

    def SetBubbleHeight(self, height):
        height = max(38, int(height))
        self.SetSize(BUBBLE_W, height)
        self.fill.SetSize(BUBBLE_W - 2, height - 2)
        for rim, (x, y, w, h) in zip(self.rims, ((0, 0, BUBBLE_W, 1), (0, height - 1, BUBBLE_W, 1),
                                                 (0, 0, 1, height), (BUBBLE_W - 1, 0, 1, height))):
            rim.SetPosition(x, y)
            rim.SetSize(w, h)
        self.vein.SetPosition(4, height - 1 - T.VEIN_ROW)


_MESSAGE_ROW = []
_DUEL_ACTIONS = []
DUEL_BUTTON_W = 76


def DuelActionsClass():
    """uiunifiedmessenger.DuelActions (a duel challenge row) with small R1 buttons in Tahoma 12: Přijmout (primary,
    left) and Odmítnout (right); the answered state in the muted colour (created once)."""
    if not _DUEL_ACTIONS:
        import uiunifiedmessenger as M

        class DuelActions(M.DuelActions):
            STATUS_COLOR = T.MUTED

            def MakeButton(self, action, x):
                kit = uir1.Kit()
                owner = ref(self)

                def answer(action=action):
                    actions = owner()
                    if actions:
                        actions.Answer(action)

                return uir1.Button(self, kit, x, 0, DUEL_BUTTON_W, M.duelchallenge.BUTTON_TEXTS[action],
                                   primary=action == M.duelchallenge.ACCEPT, small=True, event=answer,
                                   font=kit.font('tahoma'))

        _DUEL_ACTIONS.append(DuelActions)
    return _DUEL_ACTIONS[0]


def MessageRowClass():
    """uiunifiedmessenger.MessageRow with the R1 bubble and R1 sender / time colours (created once)."""
    if not _MESSAGE_ROW:
        import uiunifiedmessenger as M

        class MessageRow(M.MessageRow):
            BUBBLE_CLASS = Bubble
            DUEL_ACTIONS_CLASS = DuelActionsClass()

            def SetMessage(self, message, retryEvent):
                M.MessageRow.SetMessage(self, message, retryEvent)
                incoming = int(message[3]) == 1
                gameMaster = int(message[8] or 0) == M.model.MESSAGE_TYPE_GAME_MASTER
                if not gameMaster:
                    self.senderLine.SetPackedFontColor(T.INK if incoming else T.IVORY)
                self.timeLine.SetPackedFontColor(T.MUTED)
                self.stateLine.SetPackedFontColor(T.INK_DIM)

        _MESSAGE_ROW.append(MessageRow)
    return _MESSAGE_ROW[0]


# --------------------------------------------------------------------------- composer
class ComposerField(uir1.Interactive):
    """The composer well: one 24 px R1 field line; a wrapped message makes it grow upwards (up to
    COMPOSER_MAX_LINES lines, then a panel frame), the vein along the bottom while the line has the focus. The
    original edit line (multi-line, 512 characters, codepage) sits inside; a click anywhere focuses it."""

    def __init__(self, parent, kit, x, bottom, w, edit):
        uir1.Interactive.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.x, self.bottom, self.w = int(x), int(bottom), int(w)
        # Every image the well can use is made now, before the edit line: they all lie under its text.
        self.ops = uir1.Ops(self, L.frame('panel', self.w, 2 * T.FIELD_H, 'panel_dark'))
        self.vein = uir1.Vein(self, 3, T.FIELD_H - 1, self.w - 6)
        self.vein.Hide()
        self.edit = edit
        self.cell = uir1.FontCell(kit.font('text_s'))
        self.lines = 1
        self.focused = False
        self.callback = self.Focus
        edit.SetParent(self)
        uir1.SetFont(edit, kit.font('text_s'))
        edit.SetLimitWidth(self.w - 16)
        self.Layout(1)
        self.Show()

    def Layout(self, lines):
        self.lines = max(1, min(COMPOSER_MAX_LINES, int(lines)))
        h = T.FIELD_H + (self.lines - 1) * (self.cell + 1)
        self.SetPosition(self.x, self.bottom - h)
        self.SetSize(self.w, h)
        self.edit.SetPosition(8, (T.FIELD_H - self.cell) // 2)
        self.edit.SetSize(self.w - 16, h - (T.FIELD_H - self.cell))
        self.paint()

    def Focus(self):
        self.edit.SetFocus()

    def paint(self):
        h = self.GetHeight()
        if h <= T.FIELD_H:
            state = 'focus' if self.focused else ('hover' if self.hovered else 'normal')
            self.ops.Apply(L.field(state, self.w))
            self.vein.Hide()
        else:
            self.ops.Apply(L.frame('panel', self.w, h, 'panel_dark'))
            self.vein.SetWidth(self.w - 6)
            self.vein.SetPosition(3, h - 1 - T.VEIN_ROW)
            self.vein.Show() if self.focused else self.vein.Hide()

    def OnUpdate(self):
        try:
            focused = bool(self.edit.IsFocus())
        except Exception:
            focused = False
        try:
            lines = int(self.edit.GetTextLineCount()) if self.edit.GetText() else 1
        except Exception:
            lines = 1
        if lines != self.lines:
            self.Layout(lines)
        if focused != self.focused:
            self.focused = focused
            self.paint()


# --------------------------------------------------------------------------- settings panel
class SettingsPanel(ui.Window):
    """Nastavení zpráv: the four notification check boxes and "Vymazat místní historii" (R1 tooltip frame + vein)."""

    KEYS = (('badge', 'UNIFIED_MESSENGER_BADGE', u'Odznak nepřečtených'), ('sound', 'UNIFIED_MESSENGER_SOUND', u'Zvuk'),
            ('toast', 'UNIFIED_MESSENGER_TOAST', u'Oznámení'), ('preview', 'UNIFIED_MESSENGER_PREVIEW',
                                                                  u'Náhled zprávy'))

    def __init__(self, window, kit):
        ui.Window.__init__(self)
        self.window = ref(window)
        self.SetParent(window)
        self.AddFlag('float')
        x, y, w, h = SETTINGS
        self.SetPosition(x, y)
        self.SetSize(w, h)
        self.frame = uir1.TooltipFrame(self, uir1.MENU_FILL_ALPHA)          # settings, no tooltip: near opaque
        self.frame.Apply(w, h)
        self.title = uir1.RowText(self, Tr(u'Nastavení zpráv', 'Message settings'), 12, 32, kit.font('text_sb'),
                                  T.IVORY)
        self.frame.Vein(8, 31, w - 16)
        import localeInfo
        self.checks = {}
        for index, (key, locale_key, czech) in enumerate(self.KEYS):
            label = getattr(localeInfo, locale_key, '') or czech
            box = uir1.CheckBox(self, kit, 12, 40 + 24 * index, label, on=_Preference(key),
                                event=lambda key=key: self.Toggle(key), font=kit.font('text_s'))
            self.checks[key] = box
        clear = getattr(localeInfo, 'UNIFIED_MESSENGER_CLEAR', '') or u'Vymazat místní historii'
        self.clear = uir1.Button(self, kit, 12, h - 32, w - 24, clear, small=True, event=self.Clear,
                                 font=kit.font('text_s'))
        self.Show()

    def Toggle(self, key):
        value = not _Preference(key)
        try:
            import messengerHistory
            messengerHistory.SetNotificationPreference(key, value)
        except Exception:
            return
        self.checks[key].SetOn(_Preference(key))
        window = self.window()
        if key == 'badge' and window is not None:
            window.RenderConversations()

    def Clear(self):
        window = self.window()
        if window is not None:
            window.AskClearHistory()

    def OnPressEscapeKey(self):
        window = self.window()
        if window is not None:
            window.HideSettings()
        return True


def _Preference(key):
    try:
        import messengerHistory
        return bool(messengerHistory.GetNotificationPreference(key))
    except Exception:
        return True


# --------------------------------------------------------------------------- the skin
class MessengerSkin(object):
    """The R1 look drawn into a loaded UnifiedMessengerWindow. Raises on failure after undoing its changes."""

    CONVERSATION_ROWS = CONVERSATION_ROWS
    ConversationRow = ConversationRow

    def __init__(self, window):
        self.window = ref(window)
        self.kit = uir1.Kit()
        self.journal = F.Journal()
        self.actions = []
        self.settings = None
        self.MessageRow = MessageRowClass()
        try:
            self._Build(window)
        except Exception:
            self.journal.Undo()
            raise

    def _Build(self, win):
        kit, j = self.kit, self.journal
        child = win.GetChild
        board = child('Board')
        F.HideBoard(j, board)
        self.chrome = uir1.Chrome(board, kit, WIDTH, HEIGHT, Tr(u'Zprávy', 'Messages'),
                                  on_close=ui.__mem_func__(win.Close))
        self.panels = [uir1.Frame(board, x, y, w, h, 'panel') for x, y, w, h in (LEFT, HEAD, HISTORY)]
        for widget in self.chrome.Widgets() + self.panels:
            j.Own(widget)
        for name in ('MessengerBody', 'ConversationPane', 'Workspace', 'ConversationSearchBackground',
                     'ConversationHeader', 'HistoryPane', 'UnreadBadge'):
            j.Hide(child(name))

        # left column: search, new message, unread count, rows, scroll bar
        j.Hide(win.searchHint)
        j.Attr(win, 'searchHint', F.Stub())
        search = win.search
        old = (search.GetLocalPosition(), search.GetWidth(), search.GetHeight())

        def restore_search():
            search.SetParent(win)
            search.SetPosition(*old[0])
            search.SetSize(old[1], old[2])
        j.Do(restore_search)
        import localeInfo
        x, y, w = SEARCH
        self.search = j.Own(uir1.Field(win, kit, x, y, w, hint=localeInfo.UNIFIED_MESSENGER_SEARCH, edit=search,
                                       max_len=24, font=kit.font('text_s')))
        x, y, w = NEW_BUTTON
        self.newButton = j.Own(F.IconButton(win, kit, j, x, y, w, child('NewMessageButton'), child('NewMessageIcon')))
        self.unread = j.Own(uir1.Text(win, '', UNREAD[0], UNREAD[1] - uir1.FontCell(kit.font('text_s')) // 2,
                                      kit.font('text_s'), T.INK_DIM, valign='top'))
        pane = win.conversationPane
        position, size = pane.GetLocalPosition(), (pane.GetWidth(), pane.GetHeight())

        def restore_pane():
            pane.SetPosition(*position)
            pane.SetSize(*size)
        j.Do(restore_pane)
        x, y, w, h = LIST
        pane.SetPosition(x, y)
        pane.SetSize(w, h)
        self.conversationScrollBar = self._ScrollBar(win, 'conversationScrollBar', LIST_SCROLL,
                                                     ui.__mem_func__(win.RenderConversations))

        # header strip
        title = win.conversationTitle
        j.Do(lambda p=title.GetLocalPosition(): title.SetPosition(*p))
        uir1.SetFont(title, kit.font('text_b'))
        title.SetPosition(*TITLE)
        title.SetPackedFontColor(T.IVORY)
        dot = win.presenceDot
        j.Do(lambda p=dot.GetLocalPosition(): dot.SetPosition(*p))
        dot.SetPosition(*PRESENCE)
        x, y, w, pitch = ACTIONS
        for index, (name, icon) in enumerate(ACTION_NAMES):
            self.actions.append(j.Own(F.IconButton(win, kit, j, x + index * pitch, y, w, child(name), child(icon))))
        self.settingsButton = self.actions[-1]

        # history
        x, y, w, h = HISTORY_PANE
        history = ui.Window()
        history.SetParent(win)
        history.SetPosition(x, y)
        history.SetSize(w, h)
        history.Show()
        j.Own(history)
        j.Attr(win, 'historyPane', history)
        j.Attr(win, 'historyViewportHeight', h)
        win.messageMeasureLine.SetParent(history)
        self.history = history
        self.historyScrollBar = self._ScrollBar(win, 'historyScrollBar', HISTORY_SCROLL,
                                                ui.__mem_func__(win.OnHistoryScroll))
        for line, position in ((win.typingIndicator, TYPING), (win.emptyState, None)):
            j.Do(lambda line=line, p=line.GetLocalPosition(): line.SetPosition(*p))
            uir1.SetFont(line, kit.font('text_s'))
            line.SetPackedFontColor(T.INK_DIM)
            if position:
                line.SetPosition(*position)

        # composer
        bar = win.composerBar
        visible = bar.IsShow()
        j.Hide(bar)
        composer = win.composer
        old_composer = (composer.GetLocalPosition(), composer.GetWidth(), composer.GetHeight())

        def restore_composer():
            composer.SetParent(win)
            composer.SetPosition(*old_composer[0])
            composer.SetSize(old_composer[1], old_composer[2])
            composer.SetLimitWidth(366)
        j.Do(restore_composer)
        x, y, w = COMPOSER
        self.composer = j.Own(ComposerField(win, kit, x, y + T.FIELD_H, w, composer))
        weak_field = ref(self.composer)
        j.Attr(bar, 'Show', lambda: weak_field() and weak_field().Show())
        j.Attr(bar, 'Hide', lambda: weak_field() and weak_field().Hide())
        if not visible:
            self.composer.Hide()
        x, y, w = SEND
        send = child('SendButton')
        self.sendButton = j.Own(F.IconButton(win, kit, j, x, y, w, send, None, primary=True, small=False,
                                             text=send.GetText() or Tr(u'Poslat', 'Send')))
        # The header row drags the window like the hidden title bar did ('attach' -> the movable root); the X stays free.
        # "_" next to the X minimizes (UnifiedMessengerWindow.Minimize); the drag strip leaves both free.
        close = self.chrome.header.close
        cx, cy = close.GetLocalPosition()
        self.minimizeButton = j.Own(MinimizeButton(win, cx - T.X_HIT - MINIMIZE_GAP, cy,
                                                   ui.__mem_func__(win.Minimize)))
        self.dragStrip = j.Own(uir1drag.DragStrip(win, WIDTH,
                                                  reserve=uir1drag.X_RESERVE + T.X_HIT + MINIMIZE_GAP))

    def _ScrollBar(self, win, attribute, rect, event):
        j = self.journal
        old = getattr(win, attribute)
        visible = old.IsShow()
        j.Hide(old)
        bar = F.ScrollBar(self.kit)
        bar.SetParent(win)
        bar.SetPosition(rect[0], rect[1])
        bar.SetScrollBarSize(rect[2])
        bar.SetScrollEvent(event)
        bar.Show() if visible else bar.Hide()
        j.Own(bar)
        j.Attr(win, attribute, bar)
        return bar

    # ------------------------------------------------------------------ runtime hooks
    def AfterConversations(self, unread_total, badge_enabled, row_count):
        self.unread.SetText(Tr(u'Nepřečtené: %d', 'Unread: %d') % unread_total
                            if unread_total and badge_enabled else '')
        bar = self.conversationScrollBar
        if row_count > self.CONVERSATION_ROWS:
            pos = bar.GetPos()
            bar.SetMiddleBarSize(float(self.CONVERSATION_ROWS) / row_count)
            bar.SetScrollStep(1.0 / max(1, row_count - self.CONVERSATION_ROWS))
            bar.SetPos(pos, False)
        else:
            bar.SetMiddleBarSize(1.0)

    def AfterMessages(self, valid_starts):
        if valid_starts > 1:
            pos = self.historyScrollBar.GetPos()
            self.historyScrollBar.SetMiddleBarSize(max(0.12, 1.0 / valid_starts))
            self.historyScrollBar.SetPos(pos, False)
        else:
            self.historyScrollBar.SetMiddleBarSize(1.0)

    def Update(self):
        pass

    def ToggleSettings(self):
        if self.settings is not None:
            self.HideSettings()
            return
        window = self.window()
        if window is None:
            return
        self.settings = SettingsPanel(window, self.kit)
        self.settings.SetTop()
        self.settingsButton.SetSelected(True)

    def HideSettings(self):
        if self.settings is not None:
            self.settings.Hide()
            self.settings = None
        self.settingsButton.SetSelected(False)

    def Destroy(self):
        self.HideSettings()
        self.actions = []


def Build(window):
    """The R1 look for a freshly loaded UnifiedMessengerWindow, or None (original look: 'legacy' or a failure)."""
    if not F.UseR1(u'Zprávy'):
        return None
    try:
        skin = MessengerSkin(window)
        F.SyncStates(window, (('RefreshSelectionState', tuple), ('RefreshBlockButton', tuple)))
        return skin
    except Exception:
        F.Fail(u'Zprávy')
        return None


class LookupRow(uir1.Interactive):
    """Recipient suggestion with the shared hover/selection band."""

    def __init__(self, parent, kit, y, width, index):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(0, y)
        self.SetSize(width, T.PROFILE_WINDOW['row_s'])
        self.band = uir1.Band(self, 0, 0, width, self.GetHeight())
        self.label = uir1.RowText(self, '', T.PROFILE_WINDOW['pad'], self.GetHeight(), kit.font('text_s'))
        self.index = index
        self.selected = False
        self.list = ref(parent)
        self.callback = ui.__mem_func__(self._Select)
        self.OnMouseWheel = ui.__mem_func__(self._ForwardWheel)

    def _ForwardWheel(self, delta):
        # ScrollBar.SetParent may replace the parent's method with a Dispatcher.
        parent = self.list()
        return parent.OnMouseWheel(delta) if parent is not None else False

    def _Select(self):
        parent = self.list()
        if parent is not None:
            parent.SelectItem(parent.offset + self.index)

    def paint(self):
        self.band.SetState('selected' if self.selected else ('hover' if self.hovered else 'normal'))


class LookupSuggestions(ui.Window):
    """ListBox-compatible adapter; all server results remain reachable by wheel or arrows."""

    VISIBLE_ROWS = 4

    def __init__(self, parent, kit, x, y, width, event):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetSize(width, self.VISIBLE_ROWS * T.PROFILE_WINDOW['row_s'])
        self.items, self.rows = [], []
        self.selected, self.offset = -1, 0
        self.event = event
        self.frame = uir1.Frame(self, 0, 0, width, self.GetHeight(), kind='panel')
        self.scroll = uir1.ScrollBar(kit)
        self.scroll.SetParent(self)
        self.scroll.SetPosition(width - T.SCROLL_W, 0)
        self.scroll.SetScrollBarSize(self.GetHeight())
        self.scroll.SetScrollEvent(ui.__mem_func__(self._Scroll))
        self.scroll.SetScrollStep(1.0 / self.VISIBLE_ROWS)
        for index in range(self.VISIBLE_ROWS):
            self.rows.append(LookupRow(self, kit, index * T.PROFILE_WINDOW['row_s'],
                                       width - T.SCROLL_W - T.PROFILE_WINDOW['line_gap'], index))
        self._Refresh()
        self.Show()

    def _Refresh(self):
        for index, row in enumerate(self.rows):
            line = self.offset + index
            if line < len(self.items):
                uir1.Fit(row.label, self.items[line][1], row.GetWidth() - 2 * T.PROFILE_WINDOW['pad'])
                row.selected = line == self.selected
                row.paint()
                row.Show()
            else:
                row.Hide()
        if len(self.items) > self.VISIBLE_ROWS:
            self.scroll.SetMiddleBarSize(float(self.VISIBLE_ROWS) / len(self.items))
            self.scroll.Show()
        else:
            self.scroll.Hide()

    def _Scroll(self):
        self.offset = int(round(self.scroll.GetPos() * max(0, len(self.items) - self.VISIBLE_ROWS)))
        self._Refresh()

    def OnMouseWheel(self, delta):
        limit = max(0, len(self.items) - self.VISIBLE_ROWS)
        if limit:
            offset = max(0, min(limit, self.offset + (-1 if delta > 0 else 1)))
            self.scroll.SetPos(float(offset) / limit)
        return True

    def ClearItem(self):
        self.items = []
        self.selected, self.offset = -1, 0
        self.scroll.SetPos(0.0)
        self._Refresh()

    def InsertItem(self, index, name):
        self.items.append((index, name))
        self._Refresh()

    def GetItemCount(self):
        return len(self.items)

    def GetSelectedLine(self):
        return self.selected

    def SelectItem(self, line):
        if not 0 <= line < len(self.items):
            return
        self.selected = line
        self.offset = min(self.offset, line)
        self.offset = max(self.offset, line - self.VISIBLE_ROWS + 1)
        limit = max(0, len(self.items) - self.VISIBLE_ROWS)
        self.scroll.SetPos(float(self.offset) / limit if limit else 0.0)
        self._Refresh()
        self.event(*self.items[line])


class LookupSkin(ui.Window):
    """Recipient window built entirely from the R1 window profile."""

    def __init__(self, dialog):
        ui.Window.__init__(self)
        self.SetParent(dialog)
        self.AddFlag('not_pick')
        try:
            self._Build(dialog)
        except Exception:
            self.Hide()
            raise

    def _Build(self, dialog):
        import localeInfo
        p, kit = T.PROFILE_WINDOW, uir1.Kit()
        pad, gap = p['pad'], p['gap']
        width = T.DIALOG_W + 4 * pad
        inner = width - 2 * pad
        field_y = p['head'] + pad
        list_y = field_y + T.FIELD_H + gap
        status_y = list_y + LookupSuggestions.VISIBLE_ROWS * p['row_s'] + p['line_gap']
        button_y = status_y + 2 * kit.cell('text_s') + p['foot_gap']
        height = button_y + p['btn'] + pad
        self.SetSize(width, height)
        self.chrome = uir1.Chrome(self, kit, width, height, localeInfo.UNIFIED_MESSENGER_NEW_MESSAGE,
                                  on_close=ui.__mem_func__(dialog.Close), kind='window')
        self.field = uir1.Field(self, kit, pad, field_y, inner,
                                hint=Tr(u'Jméno hráče', 'Player name'), max_len=dialog.edit.max)
        self.edit = self.field.edit
        self.edit.SetReturnEvent(ui.__mem_func__(dialog.Accept))
        self.edit.SetEscapeEvent(ui.__mem_func__(dialog.Close))
        self.edit.SetUpArrowEvent(ui.__mem_func__(dialog.SelectPrevious))
        self.edit.SetDownArrowEvent(ui.__mem_func__(dialog.SelectNext))
        self.suggestions = LookupSuggestions(self, kit, pad, list_y, inner,
                                              ui.__mem_func__(dialog.SelectSuggestion))
        self.status = uir1.Text(self, '', pad, status_y, kit.font('text_s'), T.INK_DIM, valign='top')
        self.status.SetMultiLine()
        self.status.SetLimitWidth(inner)
        self.acceptButton = uir1.Button(self, kit, width - pad - 2 * T.BTN_W - gap, button_y, T.BTN_W,
                                        Tr(u'Otevřít', 'Open'), primary=True, event=ui.__mem_func__(dialog.Accept))
        self.cancelButton = uir1.Button(self, kit, width - pad - T.BTN_W, button_y, T.BTN_W,
                                        localeInfo.UNIFIED_MESSENGER_CANCEL, event=ui.__mem_func__(dialog.Close))


_lookupFailed = False


def DressLookup(dialog):
    global _lookupFailed
    if _lookupFailed or not uir1.UseR1():
        return
    try:
        skin = LookupSkin(dialog)
    except Exception:
        _lookupFailed = True
        uir1.TraceFailure('messenger recipient')
        return
    dialog.board.Hide()
    dialog.r1Skin = skin
    for name in ('edit', 'suggestions', 'status', 'acceptButton', 'cancelButton'):
        setattr(dialog, name, getattr(skin, name))
    dialog.SetSize(skin.GetWidth(), skin.GetHeight())
    dialog.AddFlag('float')
    dialog.AddFlag('movable')
    skin.Show()
