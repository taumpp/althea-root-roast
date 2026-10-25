import app
import chat
import grp
import ime
import localeInfo
import messenger
import net
import player
import time
import ui
import uiCommon

import unifiedmessengermodel as model

try:
	import messengerHistory
except ImportError:
	messengerHistory = None


MESSAGE_PAGE_SIZE = 50
MAX_RENDERED_MESSAGES = 80
MAX_BODY_BYTES = 512
MAX_TARGET_NAME_LENGTH = 24
CONVERSATION_ROWS = 7
MESSAGE_ROWS = 9
PREFIX_DEBOUNCE_MILLISECONDS = 250
SEARCH_DEBOUNCE_MILLISECONDS = 150
CONVERSATION_REFRESH_MILLISECONDS = 250
MAX_ROW_HEIGHT_CACHE = 600
MAX_LOOKUP_RESULTS = 8
LOOKUP_MODE_PREFIX = 1
LOOKUP_MODE_EXACT = 2
LOOKUP_STATUS_OK = 0
LOOKUP_STATUS_NOT_FOUND = 1
LOOKUP_STATUS_RATE_LIMITED = 2
LOOKUP_STATUS_UNAVAILABLE = 3

PUBLIC = "d:/ymir work/ui/public/"
WINDOWS = "d:/ymir work/ui/game/windows/"


# The divider above the first unread message (not the badge setting's label).
UNREAD_DIVIDER_TEXT = u"— Nepřečtené —"


def _Text(key):
	# New locale keys are optional so a root pack never aborts on an older
	# locale pack; an empty text simply suppresses the notice.
	if not key:
		return ""
	return str(getattr(localeInfo, key, "") or "")


def _Notice(key):
	text = _Text(key)
	if text:
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)


def _ShortUrl(url, limit=64):
	url = str(url)
	return url if len(url) <= limit else url[:limit - 3] + "..."


def _SanitizedBody(body):
	# Bodies are authored by other players. Reuse the public-chat policy:
	# keep item/pet/wiki links, turn forged web/player links into their plain
	# visible text and linkify real URLs with the URL itself as the label.
	body = str(body)
	if "|" not in body and "://" not in body and "www." not in body:
		return body
	try:
		import compactchatmodel
		return compactchatmodel.linkify(body)
	except:
		return body


def _PreviewText(body):
	body = str(body or "").replace("[ENTER]", " ")
	if "|" not in body:
		return body
	try:
		import compactchatmodel
		return compactchatmodel.visible_text(body)
	except:
		return body


def _MessageErrorText(message, incoming):
	if incoming:
		return ""
	errorCode = model.message_error(message)
	if not errorCode:
		return ""
	state = int(message[9])
	if errorCode in (model.ERROR_RECIPIENT_MISMATCH, model.ERROR_OUTCOME_UNKNOWN) or \
			state in (model.STATE_FAILED, model.STATE_REJECTED):
		return _Text(model.error_key(errorCode))
	return ""


def _MessageAgeMilliseconds(message):
	try:
		return max(0, int(time.time() * 1000) - int(message[6]))
	except (TypeError, ValueError):
		return 0


def _MessageRetryable(message, incoming):
	if incoming or not message[1]:
		return False
	return model.can_retry(message[9], model.message_error(message),
		_MessageAgeMilliseconds(message))


class ConversationRow(ui.Window):
	HEIGHT = 42
	COLOR_IDLE = grp.GenerateColor(0.07, 0.06, 0.05, 0.92)
	COLOR_OVER = grp.GenerateColor(0.15, 0.11, 0.08, 0.96)
	COLOR_SELECTED = grp.GenerateColor(0.23, 0.15, 0.10, 0.98)
	COLOR_ACCENT = grp.GenerateColor(0.64, 0.40, 0.20, 1.0)

	def __init__(self):
		ui.Window.__init__(self)
		self.SetSize(168, self.HEIGHT)
		self.key = ""
		self.name = ""
		self.selectEvent = None
		self.selected = False

		self.background = ui.Bar()
		self.background.SetParent(self)
		self.background.SetSize(168, self.HEIGHT - 2)
		self.background.SetColor(self.COLOR_IDLE)
		self.background.AddFlag("not_pick")
		self.background.Show()

		self.accent = ui.Bar()
		self.accent.SetParent(self)
		self.accent.SetSize(2, self.HEIGHT - 2)
		self.accent.SetColor(self.COLOR_ACCENT)
		self.accent.AddFlag("not_pick")
		self.accent.Hide()

		self.presence = ui.ImageBox()
		self.presence.SetParent(self)
		self.presence.SetPosition(7, 7)
		self.presence.LoadImage(WINDOWS + "messenger_list_offline.sub")
		self.presence.AddFlag("not_pick")
		self.presence.Hide()

		self.nameLine = ui.TextLine()
		self.nameLine.SetParent(self)
		self.nameLine.SetPosition(8, 5)
		self.nameLine.SetLimitWidth(96)
		self.nameLine.AddFlag("not_pick")
		self.nameLine.Show()

		self.previewLine = ui.TextLine()
		self.previewLine.SetParent(self)
		self.previewLine.SetPosition(8, 22)
		self.previewLine.SetLimitWidth(126)
		self.previewLine.SetPackedFontColor(0xFF938673)
		self.previewLine.AddFlag("not_pick")
		self.previewLine.Show()

		self.timeLine = ui.TextLine()
		self.timeLine.SetParent(self)
		self.timeLine.SetPosition(160, 5)
		self.timeLine.SetHorizontalAlignRight()
		self.timeLine.SetPackedFontColor(0xFF796D5D)
		self.timeLine.AddFlag("not_pick")
		self.timeLine.Show()

		self.unreadLine = ui.TextLine()
		self.unreadLine.SetParent(self)
		self.unreadLine.SetPosition(160, 22)
		self.unreadLine.SetHorizontalAlignRight()
		self.unreadLine.SetPackedFontColor(0xFFE1BD84)
		self.unreadLine.AddFlag("not_pick")
		self.unreadLine.Show()

	def SetConversation(self, row, selected, selectEvent):
		self.key = row["key"]
		self.name = row["name"]
		self.selectEvent = selectEvent
		self.nameLine.SetText(self.name)
		self.previewLine.SetText(row.get("preview", ""))
		self.timeLine.SetText(row.get("display_time", ""))
		online = row.get("online")
		if online is None:
			self.presence.Hide()
			self.nameLine.SetPosition(8, 5)
			self.previewLine.SetPosition(8, 22)
		else:
			presenceImage = "messenger_list_online.sub" if online else "messenger_list_offline.sub"
			self.presence.LoadImage(WINDOWS + presenceImage)
			self.presence.Show()
			self.nameLine.SetPosition(26, 5)
			self.previewLine.SetPosition(26, 22)
		unread = int(row.get("unread", 0))
		self.unreadLine.SetText(str(unread) if unread else "")
		self.SetSelected(selected)

	def SetSelected(self, selected):
		self.selected = bool(selected)
		self.background.SetColor(
			self.COLOR_SELECTED if self.selected else self.COLOR_IDLE)
		if self.selected:
			self.accent.Show()
		else:
			self.accent.Hide()

	def OnMouseOverIn(self):
		if not self.selected:
			self.background.SetColor(self.COLOR_OVER)

	def OnMouseOverOut(self):
		if not self.selected:
			self.background.SetColor(self.COLOR_IDLE)

	def OnMouseLeftButtonDown(self):
		if self.selectEvent:
			self.selectEvent(self.name, self.key)


class MessageRow(ui.Window):
	HEIGHT = 28
	COLOR_INCOMING = grp.GenerateColor(0.16, 0.11, 0.08, 0.84)
	COLOR_OUTGOING = grp.GenerateColor(0.09, 0.14, 0.11, 0.84)

	def __init__(self, copyEvent):
		ui.Window.__init__(self)
		self.SetSize(454, self.HEIGHT)
		self.messageID = ""
		self.body = ""
		self.copyEvent = copyEvent
		self.hyperlinkEvent = None

		self.background = ui.Bar()
		self.background.SetParent(self)
		self.background.SetSize(454, self.HEIGHT - 2)
		self.background.AddFlag("not_pick")
		self.background.Show()

		self.senderLine = ui.TextLine()
		self.senderLine.SetParent(self)
		self.senderLine.SetPosition(7, 7)
		self.senderLine.SetLimitWidth(80)
		self.senderLine.AddFlag("not_pick")
		self.senderLine.Show()

		self.bodyLine = ui.TextLine()
		self.bodyLine.SetParent(self)
		self.bodyLine.SetPosition(92, 7)
		self.bodyLine.SetLimitWidth(245)
		self.bodyLine.AddFlag("not_pick")
		self.bodyLine.Show()

		self.stateLine = ui.TextLine()
		self.stateLine.SetParent(self)
		self.stateLine.SetPosition(382, 7)
		self.stateLine.SetHorizontalAlignRight()
		self.stateLine.SetPackedFontColor(0xFF8C8275)
		self.stateLine.AddFlag("not_pick")
		self.stateLine.Show()

		self.timeLine = ui.TextLine()
		self.timeLine.SetParent(self)
		self.timeLine.SetPosition(446, 7)
		self.timeLine.SetHorizontalAlignRight()
		self.timeLine.SetPackedFontColor(0xFF756B5E)
		self.timeLine.AddFlag("not_pick")
		self.timeLine.Show()

		self.retryButton = ui.Button()
		self.retryButton.SetParent(self)
		self.retryButton.SetPosition(330, 3)
		self.retryButton.SetUpVisual(PUBLIC + "xsmall_button_01.sub")
		self.retryButton.SetOverVisual(PUBLIC + "xsmall_button_02.sub")
		self.retryButton.SetDownVisual(PUBLIC + "xsmall_button_03.sub")
		self.retryButton.SetText(localeInfo.UNIFIED_MESSENGER_RETRY)
		self.retryButton.Hide()

	def SetMessage(self, message, retryEvent):
		self.messageID = message[1]
		self.body = message[5]
		incoming = int(message[3]) == 1
		self.background.SetColor(
			self.COLOR_INCOMING if incoming else self.COLOR_OUTGOING)
		self.senderLine.SetText(str(message[4]) + ":")
		self.bodyLine.SetText(str(message[5]))
		timestamp = model.message_time_ms(message)
		self.timeLine.SetText(time.strftime(
			"%H:%M", time.localtime(timestamp / 1000.0)))
		stateKey = "" if incoming else model.message_state_key(message[9])
		self.stateLine.SetText(getattr(localeInfo, stateKey, "") if stateKey else "")
		if _MessageRetryable(message, incoming):
			self.retryButton.SetEvent(retryEvent, message[1])
			self.retryButton.Show()
		else:
			self.retryButton.Hide()

	def SetHyperlinkEvent(self, event):
		self.hyperlinkEvent = event

	def OnMouseLeftButtonDown(self):
		if self.hyperlinkEvent:
			return self.hyperlinkEvent()
		return False

	def OnMouseLeftButtonDoubleClick(self):
		if self.copyEvent:
			self.copyEvent(self.body)


class PlayerLookupDialog(ui.ScriptWindow):
	def __init__(self, owner):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'acceptButton')
		self.owner = owner
		self.pendingPrefixToken = 0
		self.pendingExactToken = 0
		self.lastText = ""
		self.lastEditTime = 0
		self.requestedPrefix = ""

		self.SetSize(330, 245)
		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetSize(330, 245)
		self.board.SetTitleName(localeInfo.UNIFIED_MESSENGER_NEW_MESSAGE)
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.Show()

		self.inputBoard = ui.ThinBoard()
		self.inputBoard.SetParent(self.board)
		self.inputBoard.SetPosition(16, 38)
		self.inputBoard.SetSize(298, 28)
		self.inputBoard.Show()

		self.edit = ui.EditLine()
		self.edit.SetParent(self.inputBoard)
		self.edit.SetPosition(8, 7)
		self.edit.SetSize(282, 16)
		self.edit.SetMax(MAX_TARGET_NAME_LENGTH)
		self.edit.SetReturnEvent(ui.__mem_func__(self.Accept))
		self.edit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.edit.SetUpArrowEvent(ui.__mem_func__(self.SelectPrevious))
		self.edit.SetDownArrowEvent(ui.__mem_func__(self.SelectNext))
		self.edit.Show()

		self.suggestionBoard = ui.ThinBoard()
		self.suggestionBoard.SetParent(self.board)
		self.suggestionBoard.SetPosition(16, 70)
		self.suggestionBoard.SetSize(298, 122)
		self.suggestionBoard.Show()

		self.suggestions = ui.ListBox()
		self.suggestions.SetParent(self.suggestionBoard)
		self.suggestions.SetPosition(8, 6)
		self.suggestions.SetSize(282, 110)
		self.suggestions.SetTextCenterAlign(False)
		self.suggestions.SetEvent(ui.__mem_func__(self.SelectSuggestion))
		self.suggestions.Show()

		self.status = ui.TextLine()
		self.status.SetParent(self.board)
		self.status.SetPosition(16, 197)
		self.status.SetLimitWidth(180)
		self.status.SetPackedFontColor(0xFFC7AA7D)
		self.status.Show()

		self.acceptButton = self.__CreateButton(
			190, localeInfo.UNIFIED_MESSENGER_CONFIRM, self.Accept)
		self.cancelButton = self.__CreateButton(
			254, localeInfo.UNIFIED_MESSENGER_CANCEL, self.Close)
		self.r1Skin = None
		try:
			import uir1messenger
			uir1messenger.DressLookup(self)
		except Exception:
			import uir1
			uir1.TraceFailure("messenger recipient")
		self.Hide()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateButton(self, x, text, event):
		button = ui.Button()
		button.SetParent(self.board)
		button.SetPosition(x, 202)
		button.SetUpVisual(PUBLIC + "middle_button_01.sub")
		button.SetOverVisual(PUBLIC + "middle_button_02.sub")
		button.SetDownVisual(PUBLIC + "middle_button_03.sub")
		button.SetText(text)
		button.SetEvent(ui.__mem_func__(event))
		button.Show()
		return button

	def Open(self):
		self.pendingPrefixToken = 0
		self.pendingExactToken = 0
		self.lastText = ""
		self.lastEditTime = app.GetGlobalTime()
		self.requestedPrefix = ""
		self.edit.SetText("")
		self.suggestions.ClearItem()
		self.status.SetText("")
		self.acceptButton.Enable()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.edit.SetFocus()

	def Close(self):
		self.pendingPrefixToken = 0
		self.pendingExactToken = 0
		self.edit.KillFocus()
		self.Hide()
		if self.owner and self.owner.targetDialog is self:
			self.owner.targetDialog = None
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __LookupAvailable(self):
		try:
			return bool(net.IsUnifiedMessengerPlayerLookupAvailable())
		except:
			return False

	def OnUpdate(self):
		if not self.IsShow():
			return
		now = app.GetGlobalTime()
		query = self.edit.GetText().strip()
		if query != self.lastText:
			self.lastText = query
			self.lastEditTime = now
			self.requestedPrefix = ""
			self.pendingPrefixToken = 0
			self.suggestions.ClearItem()
			self.status.SetText("")
		if (query != self.requestedPrefix and
				model.lookup_prefix_ready(query, now, self.lastEditTime)):
			self.requestedPrefix = query
			if not self.__LookupAvailable():
				self.status.SetText(localeInfo.UNIFIED_MESSENGER_LOOKUP_UNAVAILABLE)
				return
			token = net.SendUnifiedMessengerPlayerLookup(
				LOOKUP_MODE_PREFIX, query)
			if token is None:
				self.status.SetText(localeInfo.UNIFIED_MESSENGER_LOOKUP_UNAVAILABLE)
				return
			self.pendingPrefixToken = int(token)

	def SelectSuggestion(self, index, name):
		self.edit.SetText(str(name))
		# Selecting with arrows must not clear the list on the next frame.
		self.lastText = str(name).strip()
		self.requestedPrefix = self.lastText
		self.pendingPrefixToken = 0
		self.edit.SetEndPosition()
		self.edit.SetFocus()

	def __MoveSelection(self, direction):
		count = self.suggestions.GetItemCount()
		if not count:
			return
		line = self.suggestions.GetSelectedLine()
		line = (line + direction) % count if line >= 0 else \
			(0 if direction > 0 else count - 1)
		self.suggestions.SelectItem(line)

	def SelectPrevious(self):
		self.__MoveSelection(-1)

	def SelectNext(self):
		self.__MoveSelection(1)

	def Accept(self):
		name = self.edit.GetText().strip()
		if not name or self.pendingExactToken:
			return True
		if not self.__LookupAvailable():
			self.status.SetText(localeInfo.UNIFIED_MESSENGER_LOOKUP_UNAVAILABLE)
			return True
		token = net.SendUnifiedMessengerPlayerLookup(LOOKUP_MODE_EXACT, name)
		if token is None:
			self.status.SetText(localeInfo.UNIFIED_MESSENGER_LOOKUP_UNAVAILABLE)
			return True
		self.pendingExactToken = int(token)
		self.status.SetText(localeInfo.UNIFIED_MESSENGER_LOOKUP_CHECKING)
		self.acceptButton.Disable()
		return True

	def OnLookupResult(self, token, mode, status, rows):
		pending = self.pendingPrefixToken if int(mode) == LOOKUP_MODE_PREFIX else \
			self.pendingExactToken
		if not model.lookup_response_is_current(token, pending, self.IsShow()):
			return
		if int(mode) == LOOKUP_MODE_PREFIX:
			self.pendingPrefixToken = 0
			self.suggestions.ClearItem()
			if int(status) == LOOKUP_STATUS_OK:
				for index, row in enumerate(list(rows)[:MAX_LOOKUP_RESULTS]):
					self.suggestions.InsertItem(index, str(row[1]))
				self.status.SetText("")
			else:
				self.status.SetText(localeInfo.UNIFIED_MESSENGER_LOOKUP_UNAVAILABLE)
			return

		self.pendingExactToken = 0
		self.acceptButton.Enable()
		if int(status) == LOOKUP_STATUS_OK and len(rows) == 1:
			pid, canonicalName = rows[0]
			self.Close()
			# The closed dialog released targetDialog: the composer takes the focus.
			self.owner.OpenConversation(canonicalName, model.stable_key(pid))
		elif int(status) == LOOKUP_STATUS_NOT_FOUND:
			self.status.SetText(localeInfo.UNIFIED_MESSENGER_PLAYER_NOT_FOUND)
		else:
			self.status.SetText(localeInfo.UNIFIED_MESSENGER_LOOKUP_UNAVAILABLE)


class UnifiedMessengerWindow(ui.ScriptWindow):
	# Immutable defaults for state that is always reassigned, never mutated.
	aliases = None
	allConversations = ()
	r1Skin = None
	newerMessages = ()
	historyDirty = False
	historyScrollable = False
	pendingNewRows = False
	searchDirty = False
	searchEditedAt = 0
	conversationRefreshPending = False
	lastConversationRefresh = 0
	linkDialog = None
	linkTarget = ""
	typingText = ""
	typingChangedAt = 0
	duelRevision = None
	unreadAnchorPending = False
	unreadAnchorRowID = None
	lastMessageTimes = None
	minimized = False
	minimizeButton = None

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.interface = None
		self.loaded = False
		self.selectedKey = ""
		self.selectedName = ""
		self.drafts = {}
		self.selectedUnread = 0
		self.conversationRows = []
		self.messageRows = []
		self.loadedMessages = []
		self.hasOlderMessages = False
		self.historyWindowShifted = False
		self.newerMessages = []
		self.pendingNewRows = False
		self.historyScrollable = False
		self.allConversations = []
		self.filteredConversations = []
		self.aliases = None
		self.historyDirty = False
		self.conversationRefreshPending = False
		self.lastConversationRefresh = 0
		self.searchDirty = False
		self.searchEditedAt = 0
		self.rowHeightCache = {}
		self.settingsButtons = []
		self.questionDialog = None
		self.linkDialog = None
		self.targetDialog = None
		self.typingPeer = ""
		self.typingUpdated = 0
		self.typingSent = False
		self.lastTypingSent = 0
		self.typingText = ""
		self.typingChangedAt = 0
		self.recoveryStatus = ""

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def BindInterface(self, interface):
		self.interface = interface

	def OnClickMessageLink(self):
		hyperlink = ui.GetHyperlink()
		if not hyperlink:
			return False
		if hyperlink.startswith("chatweb:"):
			# Player-authored bodies are untrusted: confirm the real address
			# before leaving the game instead of trusting a link label.
			import compactchatmodel
			kind, target = compactchatmodel.link_target(hyperlink)
			if kind == "chatweb" and target:
				self.__AskOpenLink(target)
			return True
		if app.IsPressed(app.DIK_LALT) and hyperlink.startswith(("item:", "petitem:")):
			ime.PasteString(chat.GetLinkFromHyperlink(hyperlink))
		elif self.interface:
			self.interface.MakeHyperlinkTooltip(hyperlink)
		return True

	def __AskOpenLink(self, target):
		self.__CloseLinkDialog()
		dialog = uiCommon.QuestionDialog2()
		dialog.SetText1(_Text("UNIFIED_MESSENGER_OPEN_LINK") or "?")
		dialog.SetText2(_ShortUrl(target))
		dialog.SetAcceptEvent(ui.__mem_func__(self.__OpenLink))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseLinkDialog))
		dialog.Open()
		self.linkDialog = dialog
		self.linkTarget = target

	def __OpenLink(self):
		target = self.linkTarget
		self.__CloseLinkDialog()
		import compactchatmodel
		valid = compactchatmodel.web_url(target)
		if valid:
			app.ShellExecute(valid)
		return True

	def __CloseLinkDialog(self):
		if self.linkDialog:
			self.linkDialog.Close()
		self.linkDialog = None
		self.linkTarget = ""
		return True

	def LoadWindow(self):
		if self.loaded:
			return True
		loader = ui.PythonScriptLoader()
		loader.LoadScriptFile(self, "uiscript/unifiedmessengerwindow.py")
		self.board = self.GetChild("Board")
		self.search = self.GetChild("ConversationSearch")
		self.searchClearButton = self.GetChild("ConversationSearchClearButton")
		self.searchButton = self.GetChild("ConversationSearchButton")
		self.conversationPane = self.GetChild("ConversationList")
		self.conversationScrollBar = self.GetChild("ConversationScrollBar")
		self.unreadBadge = self.GetChild("UnreadBadge")
		self.newMessageButton = self.GetChild("NewMessageButton")
		self.conversationHeader = self.GetChild("ConversationHeader")
		self.historyPane = self.GetChild("HistoryPane")
		self.historyScrollBar = self.GetChild("HistoryScrollBar")
		self.emptyState = self.GetChild("EmptyState")
		self.composerBar = self.GetChild("ComposerBar")
		self.composer = self.GetChild("Composer")
		self.sendButton = self.GetChild("SendButton")
		self.addFriendButton = self.GetChild("AddFriendButton")
		self.marketButton = self.GetChild("MarketButton")
		self.blockButton = self.GetChild("BlockButton")
		self.settingsButton = self.GetChild("SettingsButton")
		self.deleteConversationButton = self.GetChild("DeleteConversationButton")
		self.conversationTitle = self.GetChild("ConversationTitle")
		self.presenceText = self.GetChild("PresenceText")
		self.typingIndicator = self.GetChild("TypingIndicator")
		self.conversationPane.AddFlag("float")
		self.conversationPane.SetTop()
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.search.SetReturnEvent(ui.__mem_func__(self.RefreshConversations))
		self.search.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
		self.searchClearButton.SetEvent(ui.__mem_func__(self.ClearSearch))
		self.searchButton.SetEvent(ui.__mem_func__(self.RefreshConversations))
		self.composer.SetReturnEvent(ui.__mem_func__(self.SendMessage))
		self.composer.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
		self.sendButton.SetEvent(ui.__mem_func__(self.SendMessage))
		self.newMessageButton.SetEvent(ui.__mem_func__(self.OpenNewMessage))
		self.addFriendButton.SetEvent(ui.__mem_func__(self.AddSelectedFriend))
		self.marketButton.SetEvent(ui.__mem_func__(self.OpenSelectedSellerMarket))
		self.marketButton.SetToolTipText(getattr(
			localeInfo, "UNIFIED_MESSENGER_MARKET_OFFERS",
			"Zobrazit nab\u00eddky hr\u00e1\u010de"))
		self.blockButton.SetEvent(ui.__mem_func__(self.BlockSelectedPeer))
		self.settingsButton.SetEvent(ui.__mem_func__(self.ToggleSettings))
		self.deleteConversationButton.SetEvent(ui.__mem_func__(self.AskDeleteConversation))
		self.historyScrollBar.SetScrollEvent(ui.__mem_func__(self.OnHistoryScroll))
		self.conversationScrollBar.SetScrollEvent(ui.__mem_func__(self.RenderConversations))
		self.loaded = True
		self.RefreshConversations()
		self.RefreshSelectionState()
		return True

	def Destroy(self):
		# The native network stream has already left the game phase when the
		# interface is destroyed during character selection. Clear local typing
		# state without emitting another game-phase packet on that socket.
		self.StopTyping(False)
		self.__ReleaseInputFocus()
		self.__DestroyRows(self.conversationRows)
		self.__DestroyRows(self.messageRows)
		self.loadedMessages = []
		self.hasOlderMessages = False
		self.historyWindowShifted = False
		self.newerMessages = []
		self.pendingNewRows = False
		self.allConversations = []
		self.drafts = {}
		self.filteredConversations = []
		self.rowHeightCache = {}
		self.__DestroyRows(self.settingsButtons)
		if self.questionDialog:
			self.questionDialog.Close()
		self.questionDialog = None
		self.__CloseLinkDialog()
		if self.r1Skin:
			self.r1Skin.Destroy()
		self.r1Skin = None
		if getattr(self, "minimized", False) and self.interface:
			self.interface.HideUnifiedMessengerMinimized()
		self.minimized = False
		self.minimizeButton = None
		self.interface = None
		self.loaded = False
		self.ClearDictionary()

	def __DestroyRows(self, rows):
		for row in rows:
			row.Hide()
		del rows[:]

	def SyncPresenceWatch(self, shown=None):
		available = getattr(net, "IsUnifiedMessengerPresenceAvailable", None)
		watch = getattr(net, "WatchUnifiedMessengerPresence", None)
		if not available or not watch or not available():
			return
		if shown is None:
			shown = self.IsShow()
		name = self.selectedName if shown and not str(self.selectedKey).startswith("guild:") else ""
		watch(name or "")

	def OnPresenceChanged(self):
		if self.loaded and self.IsShow():
			self.RenderConversations()

	def Hide(self):
		if getattr(self, "loaded", False):
			self.SyncPresenceWatch(False)
		ui.ScriptWindow.Hide(self)

	def Show(self):
		restored = getattr(self, "minimized", False)
		self.minimized = False
		ui.ScriptWindow.Show(self)
		self.SyncPresenceWatch(True)
		self.OnPresenceChanged()
		if self.interface:
			# Also removes the minimized "Messenger" letter.
			self.interface.ClearUnifiedMessengerNotifications()
		if restored:
			self.SetTop()
			# The draft is still in the composer: let the player go on typing.
			if self.composer.GetText():
				self.FocusComposer()

	def IsMinimized(self):
		return bool(getattr(self, "minimized", False) and self.loaded and not self.IsShow())

	def Minimize(self):
		# The title bar's "_": hides the window and leaves one "Messenger"
		# letter among the whisper letters. Hide keeps everything a restore
		# needs (the open conversation, the composer draft, the position);
		# the letter, the Messenger shortcut or the friends button bring it
		# back through Open() without a name.
		if not self.loaded or not self.IsShow():
			return True
		self.StopTyping()
		self.HideSettings()
		self.__ReleaseInputFocus()
		self.minimized = True
		self.Hide()
		if self.interface:
			self.interface.ShowUnifiedMessengerMinimized(self.MinimizedUnread())
		return True

	def MinimizedUnread(self):
		# Private unread messages (with duel rows), like the in-window badge.
		if not self.loaded:
			return 0
		self.RefreshConversations()
		return model.unread_total(self.allConversations)

	def RestoreMinimized(self, name, key):
		# Warp reconstruction must not read a hidden thread or steal focus.
		if not self.LoadWindow():
			return False
		if name and not self.OpenConversation(name, key, markRead=False):
			return False
		self.historyDirty = True
		self.minimized = True
		self.Hide()
		if self.interface:
			self.interface.ShowUnifiedMessengerMinimized(self.MinimizedUnread())
		return True

	def Open(self, name=None, key=None):
		if not self.LoadWindow():
			return False
		# Changes received while hidden only marked the window dirty.
		dirty = self.historyDirty
		self.historyDirty = False
		self.RefreshConversations()
		if name:
			self.OpenConversation(name, key)
		elif dirty and self.selectedKey:
			self.LoadMessages()
			self.__MarkConversationRead()
		self.Show()
		# every opening (a friend's double click, a letter, the
		# envelope, the friends button, a restore) lands in the message line.
		self.FocusComposer()
		return True

	def CanCompose(self):
		# A former guild's history stays readable, but guild chat would go to
		# the current guild, so its composer is hidden.
		if not self.selectedKey or not self.selectedName:
			return False
		return (not self.selectedKey.startswith("guild:") or
			self.selectedKey == self.__CurrentGuildKey())

	def FocusComposer(self):
		# The player can type at once, without clicking the message line.
		# The "Nová zpráva" name dialog keeps its own focus.
		if not self.loaded or not self.IsShow() or not self.CanCompose():
			return False
		if getattr(self, "targetDialog", None):
			return False
		self.composer.SetFocus()
		return True

	def OpenWithoutTarget(self):
		if not self.Open():
			return False
		self.OpenNewMessage()
		return True

	def OpenLatestUnread(self):
		# Opens Messages on the newest unread private thread, or as it was.
		if not self.Open():
			return False
		row = model.latest_unread_conversation(self.allConversations)
		if row:
			self.OpenConversation(row["name"], row["key"])
		return True

	def Toggle(self):
		if not self.loaded or not self.IsShow():
			return self.Open()
		self.Close()
		return True

	def __ReleaseInputFocus(self):
		self.__CloseTargetDialog()
		if self.loaded:
			self.search.KillFocus()
			self.composer.KillFocus()

	def Close(self):
		self.StopTyping()
		self.HideSettings()
		self.__ReleaseInputFocus()
		if getattr(self, "minimized", False) and self.interface:
			self.interface.HideUnifiedMessengerMinimized()
		self.minimized = False
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		if not self.loaded or not self.IsShow():
			return True
		self.Close()
		if self.interface and self.selectedName:
			# A minimized read conversation is a shortcut, not a new message.
			self.interface.ShowUnifiedMessengerNotification(
				self.selectedKey, self.selectedName, False)
		return True

	def IsConversationOpen(self, name, key=""):
		if not self.IsShow():
			return False
		return model.same_conversation(
			self.selectedKey, self.selectedName, key, name)

	def ClearSearch(self):
		self.search.SetText("")
		self.RefreshConversations()
		self.search.SetFocus()

	def OpenNewMessage(self):
		if self.targetDialog:
			self.targetDialog.SetTop()
			self.targetDialog.edit.SetFocus()
			return
		dialog = PlayerLookupDialog(self)
		dialog.Open()
		self.targetDialog = dialog

	def __CloseTargetDialog(self):
		if self.targetDialog:
			self.targetDialog.Close()
		self.targetDialog = None
		return True

	def OnPlayerLookupCapability(self, enabled):
		if self.targetDialog and not enabled:
			self.targetDialog.status.SetText(
				localeInfo.UNIFIED_MESSENGER_LOOKUP_UNAVAILABLE)

	def OnPlayerLookupResult(self, token, mode, status, rows):
		if self.targetDialog:
			self.targetDialog.OnLookupResult(token, mode, status, rows)

	def OnSubmitResult(self, messageID, error):
		# The bubble keeps the persisted reason; this is the one-time notice for
		# the player's live action. Wording never reveals a block.
		# Newer executables expose GetStorageMode together with error codes.
		nativeErrorCodes = bool(messengerHistory and
			hasattr(messengerHistory, "GetStorageMode"))
		text = _Text(model.submit_notice_key(error, nativeErrorCodes))
		if text:
			chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	def AddSelectedFriend(self):
		if not self.selectedName or self.selectedKey.startswith("guild:"):
			return
		if messenger.IsFriendByName(self.selectedName):
			return
		net.SendMessengerAddByNamePacket(self.selectedName)
		# Sending is not acceptance. Keep retry available after offline/denied
		# requests; the confirmed roster refresh disables this button for friends.

	def BlockSelectedPeer(self):
		if (not getattr(app, "ENABLE_MESSENGER_BLOCK", 0) or
				not self.selectedName or self.selectedKey.startswith("guild:")):
			return
		if messenger.IsBlockFriendByName(self.selectedName):
			# Same transport/cache contract as the existing blocked-friends list.
			net.SendMessengerBlockRemoveByVIDPacket(self.selectedName, self.selectedName)
			messenger.RemoveBlock(self.selectedName)
		else:
			# Only the server's block-list callback confirms an addition. A
			# rejected request (e.g. an offline target) must not freeze the button.
			net.SendMessengerBlockAddByNamePacket(self.selectedName)
		self.RefreshBlockButton()

	def RefreshBlockButton(self):
		if not self.loaded:
			return
		available = bool(self.selectedKey and self.selectedName and
			not self.selectedKey.startswith("guild:") and
			getattr(app, "ENABLE_MESSENGER_BLOCK", 0))
		blocked = available and messenger.IsBlockFriendByName(self.selectedName)
		self.blockButton.SetToolTipText(localeInfo.TARGET_BUTTON_BLOCK_REMOVE
			if blocked else localeInfo.TARGET_BUTTON_BLOCK)
		if available:
			self.blockButton.Enable()
		else:
			self.blockButton.Disable()

	def OpenSelectedSellerMarket(self):
		if (not self.selectedKey or not self.selectedName or
				self.selectedKey.startswith("guild:")):
			return False
		opener = getattr(self.interface, "OpenVirtualMarketForSeller", None)
		if not opener:
			return False
		return bool(opener(self.selectedName))

	def RefreshSelectionState(self):
		if not self.loaded:
			return
		hasSelection = bool(self.selectedKey and self.selectedName)
		isGuild = hasSelection and self.selectedKey.startswith("guild:")
		canCompose = self.CanCompose()
		if hasSelection:
			self.conversationTitle.SetText(self.selectedName)
			self.emptyState.Hide()
			self.historyScrollBar.Show()
			self.deleteConversationButton.Enable()
		else:
			self.conversationTitle.SetText("")
			self.presenceText.SetText("")
			if self.search.GetText() and not self.filteredConversations:
				self.emptyState.SetText(localeInfo.UNIFIED_MESSENGER_NO_RESULTS)
			elif not self.filteredConversations:
				self.emptyState.SetText(localeInfo.UNIFIED_MESSENGER_EMPTY)
			else:
				self.emptyState.SetText(localeInfo.UNIFIED_MESSENGER_SELECT_CONVERSATION)
			self.emptyState.Show()
			self.historyScrollBar.Hide()
			self.deleteConversationButton.Disable()
		if canCompose:
			self.composerBar.Show()
			self.composer.Show()
			self.sendButton.Show()
		else:
			self.composerBar.Hide()
			self.composer.Hide()
			self.sendButton.Hide()

		if hasSelection and not isGuild and not messenger.IsFriendByName(self.selectedName):
			self.addFriendButton.Enable()
		else:
			self.addFriendButton.Disable()
		self.RefreshBlockButton()
		marketAvailable = bool(
			hasSelection and not isGuild and
			getattr(app, "ENABLE_VIRTUAL_MARKET", 0) and
			self.interface and
			hasattr(self.interface, "OpenVirtualMarketForSeller"))
		if marketAvailable:
			self.marketButton.Enable()
			self.marketButton.Show()
		else:
			self.marketButton.Hide()

	def __CurrentGuildKey(self):
		guildID = player.GetGuildID()
		return model.guild_key(guildID) if guildID else ""

	def __StoredConversations(self):
		if not messengerHistory:
			return ()
		# Newer executables return previews in the same query (no N+1 reads).
		lister = getattr(messengerHistory, "ListConversationSummaries", None)
		if lister:
			try:
				return tuple(lister())
			except:
				pass
		return tuple(messengerHistory.ListConversations())

	def __ProfilePid(self, name):
		getter = getattr(net, "GetUnifiedMessengerPlayerProfileByName", None)
		if not getter:
			return 0
		try:
			profile = getter(str(name))
		except:
			return 0
		try:
			return int(profile[0]) if profile else 0
		except (IndexError, TypeError, ValueError):
			return 0

	def __Aliases(self, rows):
		return model.conversation_aliases(rows, self.__ProfilePid)

	def __RecipientReassigned(self):
		# Protocol v1 submits by name. When the server confirmed in this session
		# that the name belongs to another PID, the message would reach the
		# other character, so it is not sent into this conversation.
		pid = model.pid_from_key(self.selectedKey)
		if not pid:
			return False
		owner = self.__ProfilePid(self.selectedName)
		return bool(owner and owner != pid and
			messengerportraitresolver.ConfirmedOwner(self.selectedName) == owner)

	def __RecipientUnverified(self):
		# The local profile cache is not tied to a server or a session (a row of
		# a DEV / test server character, DanStřela 19. 10.): a different cached
		# owner that this session did not confirm is asked again by pid and
		# name; the answer replaces the stale row and the next send goes out.
		pid = model.pid_from_key(self.selectedKey)
		if not pid:
			return False
		owner = self.__ProfilePid(self.selectedName)
		if not owner or owner == pid or \
				messengerportraitresolver.ConfirmedOwner(self.selectedName) == owner:
			return False
		return bool(messengerportraitresolver.Verify(pid, self.selectedName))

	def OpenConversation(self, name, key=None, markRead=True):
		name = str(name)
		if not self.LoadWindow():
			return False
		self.StopTyping()
		rows = self.__StoredConversations()
		aliases = self.__Aliases(rows)
		self.aliases = aliases
		self.drafts = {aliases.get(oldKey, oldKey): text
			for oldKey, text in self.drafts.items()}
		oldKey = aliases.get(self.selectedKey, self.selectedKey)
		if oldKey:
			body = self.composer.GetText()
			if body:
				self.drafts[oldKey] = body
			else:
				self.drafts.pop(oldKey, None)
		key = aliases.get(str(key), key)
		self.selectedKey, self.selectedName, self.selectedUnread = \
			model.resolve_open_conversation(name, key,
				model.conversation_summaries(rows, aliases))
		self.composer.SetText(self.drafts.get(self.selectedKey, ""))
		# The unread divider is placed once, on the rows loaded below.
		self.unreadAnchorPending = True
		self.unreadAnchorRowID = None
		if self.selectedKey.startswith("guild:"):
			self.selectedName = self.__GuildName(self.selectedKey, self.selectedName)
		self.conversationTitle.SetText(self.selectedName)
		self.typingIndicator.SetText("")
		self.RefreshSelectionState()
		self.LoadMessages()
		if markRead:
			self.__MarkConversationRead()
		self.RefreshConversations()
		interface = getattr(self, "interface", None)
		if interface and self.IsShow():
			# A thread read inside Messages no longer needs its letter.
			interface.DismissUnifiedMessengerNotification(
				self.selectedKey, self.selectedName)
		# Switching threads in an open window (a letter, a guild member's
		# whisper, the newest unread) also goes straight to typing.
		self.FocusComposer()
		return True

	def __GuildName(self, key, storedName):
		if key == self.__CurrentGuildKey():
			return localeInfo.UNIFIED_MESSENGER_GUILD
		return model.guild_display_name(storedName, localeInfo.UNIFIED_MESSENGER_GUILD)

	def NameForKey(self, key):
		for row in self.__StoredConversations():
			if row[0] == key:
				return row[1]
		return str(key)

	def OpenGuild(self):
		guildID = player.GetGuildID()
		if not guildID:
			return False
		return self.OpenConversation(localeInfo.UNIFIED_MESSENGER_GUILD,
			model.guild_key(guildID))

	def __LoadConversationMessages(self, key, before, limit, rows=None):
		local = self.__LocalMessages(key)
		if not messengerHistory:
			return model.merge_local_messages([], local, before, limit)
		aliases = self.__CurrentAliases(rows)
		messages = []
		for storageKey in model.storage_keys_for(key, aliases):
			messages.extend(messengerHistory.LoadMessages(storageKey,
				model.stored_page_boundary(before), limit))
		# row_id is global to this character's database, including pending sends.
		return model.merge_local_messages(messages, local, before, limit)

	def __LocalMessages(self, key):
		# Session-only system whispers (duel invitations...) of the open thread.
		router = getattr(getattr(self, "interface", None), "unifiedMessengerRouter", None)
		if (not router or not key or key != self.selectedKey or
				str(key).startswith("guild:")):
			return ()
		return router.LocalMessages(self.selectedName)

	def OnLocalMessage(self):
		if self.loaded and self.IsShow():
			self.__RefreshSelectedMessages()

	def OnLocalDuel(self, name):
		# A duel challenge row arrived or replaced a pending one: the list shows
		# the thread with its unread badge, an open thread shows the row.
		if not self.loaded:
			return
		if not self.IsShow():
			self.historyDirty = True
			return
		self.RefreshConversations()
		if self.IsConversationOpen(name):
			self.__RefreshSelectedMessages()

	def __CurrentAliases(self, rows=None):
		# Aliases are computed once per refresh and reused by page loads.
		if rows is not None:
			return self.__Aliases(rows)
		if self.aliases is None:
			return self.__Aliases(self.__StoredConversations())
		return self.aliases

	def __MarkConversationRead(self):
		router = getattr(getattr(self, "interface", None), "unifiedMessengerRouter", None)
		if router and self.selectedName and not str(self.selectedKey).startswith("guild:"):
			router.MarkLocalRead(self.selectedName)  # duel challenge rows
		if messengerHistory and self.selectedKey:
			for key in model.storage_keys_for(self.selectedKey, self.__CurrentAliases()):
				messengerHistory.MarkRead(key)

	def __LoadPreview(self, key):
		# Fallback for executables without ListConversationSummaries.
		messages = self.__LoadConversationMessages(key, 0, 1)
		return str(messages[-1][5]) if messages else ""

	def __ConversationPresentation(self, preview, lastActivity):
		displayTime = ""
		if int(lastActivity or 0) > 0:
			displayTime = time.strftime(
				"%H:%M", time.localtime(int(lastActivity) / 1000.0))
		return _PreviewText(preview), displayTime

	def RefreshConversations(self):
		if not self.loaded:
			return
		self.__ReloadConversations()
		self.__ApplyConversationFilter()

	def __ReloadConversations(self):
		self.conversationRefreshPending = False
		self.lastConversationRefresh = app.GetGlobalTime()
		storedRows = self.__StoredConversations()
		aliases = self.__Aliases(storedRows)
		self.aliases = aliases
		previews = model.conversation_previews(storedRows, aliases)
		summaryApi = bool(storedRows) and len(storedRows[0]) >= 7
		lastRows = model.conversation_last_rows(storedRows, aliases) if summaryApi else {}
		rows = []
		guildKey = self.__CurrentGuildKey()
		if guildKey:
			rows.append({"key": guildKey,
				"name": localeInfo.UNIFIED_MESSENGER_GUILD,
				"last_activity": 0, "unread": 0,
				"preview": "", "display_time": ""})
		for key, name, kind, lastActivity, unread in model.conversation_summaries(
				storedRows, aliases):
			rawPreview = previews.get(key, "") if summaryApi else self.__LoadPreview(key)
			if key in lastRows:
				lastActivity = self.__LastMessageTime(lastRows[key][1], lastRows[key][0]) or lastActivity
			preview, displayTime = self.__ConversationPresentation(rawPreview, lastActivity)
			row = {"key": key, "name": name,
				"last_activity": lastActivity, "unread": unread,
				"preview": preview, "display_time": displayTime}
			if key == guildKey:
				rows[0].update({"last_activity": lastActivity, "unread": unread,
					"preview": preview, "display_time": displayTime})
				continue
			if key.startswith("guild:"):
				row["name"] = model.guild_display_name(
					name, localeInfo.UNIFIED_MESSENGER_GUILD)
			rows.append(row)
		router = getattr(getattr(self, "interface", None), "unifiedMessengerRouter", None)
		if router:
			# Duel challenge rows list the challenger's thread with its badge.
			rows = model.merge_local_conversations(rows, router.LocalConversations(),
				self.__ConversationPresentation)
		self.allConversations = model.sort_conversations(rows)

	def __LastMessageTime(self, storageKey, rowID):
		# The list shows the newest message's local time, like its bubble. The
		# stored last_activity_ms takes a delivery's SERVER time and keeps the
		# maximum, so with the server clock behind it stayed at the time of an
		# older own message. One row read per new last message (cached).
		if self.lastMessageTimes is None:
			self.lastMessageTimes = {}
		cache = self.lastMessageTimes
		cacheKey = (storageKey, int(rowID))
		if cacheKey not in cache:
			if len(cache) >= 256:
				cache.clear()
			value = 0
			try:
				rows = messengerHistory.LoadMessages(storageKey, int(rowID) + 1, 1)
				if rows and int(rows[-1][0]) == int(rowID):
					value = model.message_time_ms(rows[-1])
			except Exception:
				value = 0
			cache[cacheKey] = value
		return cache[cacheKey]

	def __ApplyConversationFilter(self):
		self.searchDirty = False
		self.filteredConversations = model.filter_conversations(
			self.allConversations, self.search.GetText())
		self.RenderConversations()
		self.RefreshSelectionState()

	def RenderConversations(self):
		if not self.loaded:
			return
		self.__DestroyRows(self.conversationRows)
		rows = self.filteredConversations
		maximumStart = max(0, len(rows) - CONVERSATION_ROWS)
		start = int(self.conversationScrollBar.GetPos() * maximumStart) if maximumStart else 0
		for index, row in enumerate(rows[start:start + CONVERSATION_ROWS]):
			item = ConversationRow()
			item.SetParent(self.conversationPane)
			item.SetPosition(0, index * ConversationRow.HEIGHT)
			item.SetConversation(row, row["key"] == self.selectedKey,
				ui.__mem_func__(self.__SelectConversation))
			item.Show()
			self.conversationRows.append(item)
		unreadTotal = model.unread_total(self.allConversations)
		badgeEnabled = self.__LoadSettings()["badge"]
		self.unreadBadge.SetText(str(unreadTotal) if unreadTotal and badgeEnabled else "")

	def __SelectConversation(self, name, key):
		self.OpenConversation(name, key)

	def LoadMessages(self, before=0):
		if before:
			self.__LoadOlderMessages()
			return
		self.newerMessages = []
		self.pendingNewRows = False
		self.historyWindowShifted = False
		if not messengerHistory or not self.selectedKey:
			self.loadedMessages = []
			self.hasOlderMessages = False
			self.__RenderMessages()
			return
		messages = self.__LoadConversationMessages(self.selectedKey, 0, MESSAGE_PAGE_SIZE)
		self.loadedMessages = list(messages)[-MAX_RENDERED_MESSAGES:]
		self.hasOlderMessages = len(messages) == MESSAGE_PAGE_SIZE
		self.historyScrollBar.SetPos(1.0, False)
		self.__RenderMessages()

	def __LoadOlderMessages(self):
		if not self.loadedMessages:
			self.LoadMessages()
			return
		anchorRowID = self.loadedMessages[0][0]
		older = self.__LoadConversationMessages(
			self.selectedKey, anchorRowID, MESSAGE_PAGE_SIZE)
		self.hasOlderMessages = len(older) == MESSAGE_PAGE_SIZE
		if not older:
			self.__RenderMessages()
			return
		# Slide the window: older rows enter at the top, the newest rows leave
		# and are kept so scrolling down restores them without a jump.
		combined, trimmed = model.merge_older_page(
			self.loadedMessages, older, MAX_RENDERED_MESSAGES)
		self.newerMessages = list(trimmed) + list(self.newerMessages)
		self.historyWindowShifted = bool(self.newerMessages)
		self.loadedMessages = combined
		self.__RenderMessages(anchorRowID)

	def __LoadNewerMessages(self):
		if not self.newerMessages:
			self.LoadMessages()
			return
		count = min(MESSAGE_PAGE_SIZE, len(self.newerMessages))
		first = self.newerMessages[0][0]
		last = self.newerMessages[count - 1][0]
		anchorRowID = self.loadedMessages[-1][0] if self.loadedMessages else first
		# Reload the trimmed range so delivery states are current.
		fresh = [row for row in self.__LoadConversationMessages(
			self.selectedKey, last + 1, min(200, count + MESSAGE_PAGE_SIZE))
			if row[0] >= first]
		combined, unused, dropped = model.restore_newer_rows(
			self.loadedMessages, fresh, len(fresh), MAX_RENDERED_MESSAGES)
		self.newerMessages = list(self.newerMessages[count:])
		self.historyWindowShifted = bool(self.newerMessages)
		if dropped:
			self.hasOlderMessages = True
		self.loadedMessages = combined
		self.__RenderMessages(anchorRowID)

	def __ReloadLoadedRange(self):
		# Refresh states of the visible window without moving the viewport.
		if not self.loadedMessages:
			self.LoadMessages()
			return
		first = self.loadedMessages[0][0]
		last = self.loadedMessages[-1][0]
		fresh = [row for row in self.__LoadConversationMessages(
			self.selectedKey, last + 1, min(200, len(self.loadedMessages) + 10))
			if row[0] >= first]
		if fresh:
			self.loadedMessages = fresh[:MAX_RENDERED_MESSAGES]
		self.__RenderMessages(None, True)

	def __RenderMessages(self, anchorRowID=None, keepPosition=False):
		self.__DestroyRows(self.messageRows)
		visibleCount = MESSAGE_ROWS
		maximumStart = max(0, len(self.loadedMessages) - visibleCount)
		start = int(self.historyScrollBar.GetPos() * maximumStart) if maximumStart else 0
		messages = self.loadedMessages[start:start + visibleCount]
		previousDay = None
		unreadAt = max(0, len(self.loadedMessages) - self.selectedUnread)
		yIndex = 0
		for index, message in enumerate(messages):
			absoluteIndex = start + index
			timestamp = model.message_time_ms(message)
			day = time.strftime("%Y-%m-%d", time.localtime(timestamp / 1000.0))
			if day != previousDay and yIndex < visibleCount:
				separator = ui.TextLine()
				separator.SetParent(self.historyPane)
				separator.SetPosition(235, 8 + yIndex * 30)
				separator.SetHorizontalAlignCenter()
				separator.SetText(day)
				separator.SetPackedFontColor(0xFF8D806E)
				separator.Show()
				self.messageRows.append(separator)
				yIndex += 1
				previousDay = day
			if self.selectedUnread and absoluteIndex == unreadAt and yIndex < visibleCount:
				separator = ui.TextLine()
				separator.SetParent(self.historyPane)
				separator.SetPosition(235, 8 + yIndex * 30)
				separator.SetHorizontalAlignCenter()
				separator.SetText(UNREAD_DIVIDER_TEXT)
				separator.SetPackedFontColor(0xFFCDB58C)
				separator.Show()
				self.messageRows.append(separator)
				yIndex += 1
			if yIndex >= visibleCount:
				break
			row = MessageRow(ui.__mem_func__(self.CopyMessage))
			row.SetParent(self.historyPane)
			row.SetHyperlinkEvent(ui.__mem_func__(self.OnClickMessageLink))
			row.SetPosition(8, 4 + yIndex * 30)
			row.SetMessage(message, ui.__mem_func__(self.RetryMessage))
			row.Show()
			self.messageRows.append(row)
			yIndex += 1

	def __IsHistoryAtBottom(self):
		return (not self.historyScrollable or
			self.historyScrollBar.GetPos() >= 0.98)

	def OnHistoryScroll(self):
		position = self.historyScrollBar.GetPos()
		if position >= 0.98 and (self.newerMessages or self.pendingNewRows):
			if self.newerMessages:
				self.__LoadNewerMessages()
			else:
				self.LoadMessages()
			return
		if position <= 0.02 and self.hasOlderMessages and self.loadedMessages:
			self.__LoadOlderMessages()
			return
		self.__RenderMessages()

	def SendMessage(self):
		body = self.composer.GetText()
		if not body or not self.selectedName:
			return
		if len(body.encode("utf-8")) > MAX_BODY_BYTES:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.UNIFIED_MESSENGER_TOO_LONG)
			return
		if self.selectedKey.startswith("guild:"):
			if self.selectedKey != self.__CurrentGuildKey():
				_Notice("UNIFIED_MESSENGER_GUILD_READ_ONLY")
				return
			net.SendChatPacket(body, chat.CHAT_TYPE_GUILD)
		else:
			if self.__RecipientReassigned():
				_Notice("UNIFIED_MESSENGER_NAME_REASSIGNED")
				return
			if self.__RecipientUnverified():
				_Notice("UNIFIED_MESSENGER_RECIPIENT_CHECKING")
				return
			if self.selectedKey.startswith("pid:"):
				# Newer executables store the row in this open conversation at
				# once; older ones ignore the optional key.
				messageID = net.SendUnifiedMessage(
					self.selectedName, body, self.selectedKey)
			else:
				messageID = net.SendUnifiedMessage(self.selectedName, body)
			if not messageID:
				_Notice("UNIFIED_MESSENGER_SEND_FAILED")
				return
		self.composer.SetText("")
		self.drafts.pop(self.selectedKey, None)
		self.StopTyping()
		self.LoadMessages()
		self.RefreshConversations()

	def RetryMessage(self, messageID):
		if net.RetryUnifiedMessage(messageID):
			self.__RefreshSelectedMessages()
			return
		if self.__RecipientReassigned():
			_Notice("UNIFIED_MESSENGER_NAME_REASSIGNED")
		elif self.__RecipientUnverified():
			_Notice("UNIFIED_MESSENGER_RECIPIENT_CHECKING")
		else:
			_Notice("UNIFIED_MESSENGER_RETRY_UNAVAILABLE")
		self.__RefreshSelectedMessages()

	def CopyMessage(self, body):
		draft = self.composer.GetText()
		self.composer.SetText(body)
		self.composer.SetFocus()
		ime.SelectAll()
		ime.CopySelection()
		self.composer.SetText(draft)

	def StopTyping(self, notifyServer=True):
		if (notifyServer and self.typingSent and self.selectedName and
				not self.selectedKey.startswith("guild:")):
			net.SendUnifiedTyping(self.selectedName, False)
		self.typingSent = False
		self.lastTypingSent = 0

	def OnUpdate(self):
		if not self.loaded:
			return
		now = app.GetGlobalTime()
		if self.typingPeer and not model.typing_active(self.typingUpdated, now):
			self.typingPeer = ""
			self.typingIndicator.SetText("")
		if not self.IsShow():
			if self.typingSent:
				self.StopTyping()
			return
		if self.searchDirty and now - self.searchEditedAt >= SEARCH_DEBOUNCE_MILLISECONDS:
			self.__ApplyConversationFilter()
		if (self.conversationRefreshPending and
				now - self.lastConversationRefresh >= CONVERSATION_REFRESH_MILLISECONDS):
			self.RefreshConversations()
		self.__UpdateTyping(now)

	def __UpdateTyping(self, now):
		text = self.composer.GetText()
		if not (self.selectedName and not self.selectedKey.startswith("guild:")):
			if self.typingSent:
				self.StopTyping()
			self.typingText = text
			return
		if text != self.typingText:
			self.typingChangedAt = now
		# Typing is announced only while the text changes (refreshed every 3 s)
		# and stops after 4 s without an edit.
		decision = model.typing_transition(text, self.typingText,
			self.typingSent, self.lastTypingSent, self.typingChangedAt, now)
		self.typingText = text
		if decision is True:
			net.SendUnifiedTyping(self.selectedName, True)
			self.typingSent = True
			self.lastTypingSent = now
		elif decision is False:
			self.StopTyping()

	def OnSearchEdited(self):
		# Keystrokes only re-filter cached rows after a short pause.
		self.searchDirty = True
		self.searchEditedAt = app.GetGlobalTime()

	def __RefreshSelectedMessages(self):
		if self.__IsHistoryAtBottom() and not self.newerMessages:
			self.LoadMessages()
		else:
			if self.loadedMessages:
				self.pendingNewRows = True
			self.__ReloadLoadedRange()

	def OnHistoryChanged(self, key, event):
		if not self.loaded:
			return
		if not self.IsShow():
			# Hidden: no SQLite reads or row rebuilds per guild line/receipt.
			self.historyDirty = True
			return
		rows = self.__StoredConversations()
		aliases = self.__Aliases(rows)
		self.aliases = aliases
		if self.selectedKey or self.selectedName:
			oldKey = self.selectedKey
			self.selectedKey, self.selectedName = model.resolve_selection(
				self.selectedKey, self.selectedName,
				model.conversation_summaries(rows, aliases), key)
			if oldKey != self.selectedKey:
				self.drafts.pop(oldKey, None)
			if self.selectedKey.startswith("guild:"):
				self.selectedName = self.__GuildName(self.selectedKey, self.selectedName)
			self.conversationTitle.SetText(self.selectedName)
		selectedChanged = key in model.storage_keys_for(self.selectedKey, aliases)
		if selectedChanged:
			self.__MarkConversationRead()
		if int(event) == 1:
			self.RefreshConversations()
		else:
			self.conversationRefreshPending = True
		if selectedChanged:
			self.__RefreshSelectedMessages()

	def OnTyping(self, pid, name, active):
		if not self.loaded or str(name).lower() != self.selectedName.lower():
			return
		self.typingPeer = str(name) if active else ""
		self.typingUpdated = app.GetGlobalTime()
		self.typingIndicator.SetText(
			localeInfo.UNIFIED_MESSENGER_TYPING if active else "")

	def OnRecovery(self, status):
		# The router writes the notice to chat without requiring this window.
		self.recoveryStatus = str(status)

	def __LoadSettings(self):
		settings = model.default_notification_settings()
		if messengerHistory:
			for key in settings:
				settings[key] = bool(messengerHistory.GetNotificationPreference(key))
		return settings

	def ToggleSettings(self):
		if self.r1Skin:
			# R1 (uir1messenger): check boxes instead of the ON / OFF buttons, the same preferences.
			self.r1Skin.ToggleSettings()
			return
		if self.settingsButtons:
			self.HideSettings()
			return
		panel = ui.ThinBoard()
		panel.SetParent(self)
		panel.SetPosition(475, 85)
		panel.SetSize(205, 158)
		panel.Show()
		self.settingsButtons.append(panel)
		settings = self.__LoadSettings()
		labels = (
			("badge", localeInfo.UNIFIED_MESSENGER_BADGE),
			("sound", localeInfo.UNIFIED_MESSENGER_SOUND),
			("toast", localeInfo.UNIFIED_MESSENGER_TOAST),
			("preview", localeInfo.UNIFIED_MESSENGER_PREVIEW),
		)
		for index, (key, label) in enumerate(labels):
			button = ui.Button()
			button.SetParent(panel)
			button.SetPosition(12, 9 + index * 27)
			button.SetUpVisual(PUBLIC + "xlarge_button_01.sub")
			button.SetOverVisual(PUBLIC + "xlarge_button_02.sub")
			button.SetDownVisual(PUBLIC + "xlarge_button_03.sub")
			button.SetText("%s: %s" % (label, "ON" if settings[key] else "OFF"))
			button.SetEvent(ui.__mem_func__(self.__ToggleSetting), key)
			button.Show()
			self.settingsButtons.append(button)
		clearButton = ui.Button()
		clearButton.SetParent(panel)
		clearButton.SetPosition(12, 117)
		clearButton.SetUpVisual(PUBLIC + "xlarge_button_01.sub")
		clearButton.SetOverVisual(PUBLIC + "xlarge_button_02.sub")
		clearButton.SetDownVisual(PUBLIC + "xlarge_button_03.sub")
		clearButton.SetText(localeInfo.UNIFIED_MESSENGER_CLEAR)
		clearButton.SetEvent(ui.__mem_func__(self.AskClearHistory))
		clearButton.Show()
		self.settingsButtons.append(clearButton)

	def HideSettings(self):
		if self.r1Skin:
			self.r1Skin.HideSettings()
		self.__DestroyRows(self.settingsButtons)

	def __ToggleSetting(self, key):
		if messengerHistory:
			value = not bool(messengerHistory.GetNotificationPreference(key))
			messengerHistory.SetNotificationPreference(key, value)
		self.HideSettings()
		self.ToggleSettings()

	def AskClearHistory(self):
		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetText(localeInfo.UNIFIED_MESSENGER_CLEAR)
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__ClearHistory))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__CloseQuestion))
		self.questionDialog.Open()

	def AskDeleteConversation(self):
		if not self.selectedKey:
			return
		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetText(localeInfo.UNIFIED_MESSENGER_DELETE)
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__DeleteConversation))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__CloseQuestion))
		self.questionDialog.Open()

	def __DeleteConversation(self):
		if messengerHistory and self.selectedKey:
			for key in model.conversation_storage_keys(
					self.selectedKey, messengerHistory.ListConversations()):
				messengerHistory.DeleteConversation(key)
				self.drafts.pop(key, None)
		self.drafts.pop(self.selectedKey, None)
		self.composer.SetText("")
		self.__CloseQuestion()
		self.selectedKey = ""
		self.selectedName = ""
		self.selectedUnread = 0
		self.conversationTitle.SetText("")
		self.LoadMessages()
		self.RefreshConversations()
		self.RefreshSelectionState()

	def __CloseQuestion(self):
		if self.questionDialog:
			self.questionDialog.Close()
		self.questionDialog = None

	def __ClearHistory(self):
		if messengerHistory:
			messengerHistory.ClearHistory()
		self.drafts.clear()
		self.composer.SetText("")
		self.__CloseQuestion()
		self.selectedKey = ""
		self.selectedName = ""
		self.selectedUnread = 0
		self.conversationTitle.SetText("")
		self.LoadMessages()
		self.RefreshConversations()
		self.RefreshSelectionState()

# CRIMSON_EMBER_MESSENGER_V16_BEGIN
import messengerportraitresolver
import uicrimsonember
try:
	import uir1messenger
except Exception:
	uir1messenger = None

CRIMSON_MESSENGER_IMG_DIR = "d:/ymir work/ui/game/crimson_ember/messenger/"
CRIMSON_ERROR_LINE_HEIGHT = 16


def _CrimsonResolvePortrait(key, name):
	pid = 0
	key = str(key or "")
	if key.startswith("pid:"):
		try:
			pid = int(key.split(":", 1)[1])
		except (TypeError, ValueError):
			pid = 0
	return messengerportraitresolver.ResolvePortrait(pid, name)


def _CrimsonGetPresence(self, name):
	available = getattr(net, "IsUnifiedMessengerPresenceAvailable", None)
	getPresence = getattr(net, "GetUnifiedMessengerPresence", None)
	if name == self.selectedName and available and getPresence and available():
		# Unknown is deliberately hidden; stale roster state must not override it.
		state = getPresence(name)
		return True if state == 2 else False if state == 1 else None
	interface = getattr(self, "interface", None)
	roster = getattr(interface, "wndMessenger", None) if interface else None
	if roster and hasattr(roster, "GetCrimsonPresence"):
		return roster.GetCrimsonPresence(name)
	return None


def _CrimsonRowPresence(self, name):
	"""the dot of a conversation row shows only a KNOWN state: green online, red offline. Only the selected
	conversation is watched natively and the friends roster knows only the friends, so a stranger that is not selected
	has an unknown state; it gets no dot (None) instead of a red one, because the person may be online. The header dot
	of the selected conversation hides an unknown state the same way."""
	online = _CrimsonGetPresence(self, name)
	return online if online in (True, False) else None


def _CrimsonApplyPresence(self):
	if not self.selectedName or str(self.selectedKey).startswith("guild:"):
		self.presenceDot.Hide()
		return
	online = _CrimsonGetPresence(self, self.selectedName)
	if online is None:
		self.presenceDot.Hide()
		return
	presencePath = (
		"icon/presence_online.png" if online
		else "icon/presence_offline.png")
	self.presenceDot.LoadImage(
		CRIMSON_MESSENGER_IMG_DIR + presencePath)
	self.presenceDot.Show()


def _CrimsonMessengerConversationInit(self):
	ui.Window.__init__(self)
	self.SetSize(168, 53)
	self.key = ""
	self.name = ""
	self.selectEvent = None
	self.selected = False
	self.background = ui.ImageBox()
	self.background.SetParent(self)
	self.background.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "row/conversation_normal.png")
	self.background.AddFlag("not_pick")
	self.background.Show()
	self.avatarIcon = ui.ImageBox()
	self.avatarIcon.SetParent(self)
	self.avatarIcon.SetPosition(8, 6)
	self.avatarIcon.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "portrait/neutral_player.png")
	self.avatarIcon.AddFlag("not_pick")
	self.avatarIcon.Show()
	self.presence = ui.ImageBox()
	self.presence.SetParent(self)
	self.presence.SetPosition(31, 30)
	self.presence.AddFlag("not_pick")
	self.presence.Hide()
	self.nameLine = ui.TextLine()
	self.nameLine.SetParent(self)
	self.nameLine.SetPosition(50, 5)
	self.nameLine.SetLimitWidth(96)
	self.nameLine.AddFlag("not_pick")
	self.nameLine.Show()
	self.previewLine = ui.TextLine()
	self.previewLine.SetParent(self)
	self.previewLine.SetPosition(50, 22)
	self.previewLine.SetLimitWidth(112)
	self.previewLine.SetPackedFontColor(0xFFB9A78E)
	self.previewLine.AddFlag("not_pick")
	self.previewLine.Show()
	self.timeLine = ui.TextLine()
	self.timeLine.SetParent(self)
	self.timeLine.SetPosition(164, 5)
	self.timeLine.SetHorizontalAlignRight()
	self.timeLine.SetPackedFontColor(0xFF8E806D)
	self.timeLine.AddFlag("not_pick")
	self.timeLine.Show()
	self.unreadLine = ui.TextLine()
	self.unreadLine.SetParent(self)
	self.unreadLine.SetPosition(164, 23)
	self.unreadLine.SetHorizontalAlignRight()
	self.unreadLine.SetPackedFontColor(0xFFFFE9BD)
	self.unreadLine.AddFlag("not_pick")
	self.unreadLine.Show()
	self.unreadBackground = ui.ImageBox()
	self.unreadBackground.SetParent(self)
	self.unreadBackground.SetPosition(148, 22)
	self.unreadBackground.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "badge/unread.png")
	self.unreadBackground.AddFlag("not_pick")
	self.unreadBackground.Hide()
	self.unreadLine.SetTop()


def _CrimsonMessengerConversationSet(self, row, selected, selectEvent):
	self.key = row["key"]
	self.name = row["name"]
	self.selectEvent = selectEvent
	self.previewLine.SetText(row.get("preview", ""))
	self.timeLine.SetText(row.get("display_time", ""))
	isGuild = str(self.key).startswith("guild:")
	if isGuild:
		self.avatarIcon.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "icon/guild_conversation.png")
		self.avatarIcon.SetPosition(11, 11)
	else:
		self.avatarIcon.LoadImage(_CrimsonResolvePortrait(self.key, self.name))
		self.avatarIcon.SetPosition(8, 6)
	online = row.get("online")
	if online is None:
		self.presence.Hide()
	else:
		presenceImage = "presence_online.png" if online else "presence_offline.png"
		self.presence.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "icon/" + presenceImage)
		self.presence.Show()
	unread = int(row.get("unread", 0))
	self.unreadLine.SetText(str(unread) if unread else "")
	if unread:
		self.unreadBackground.Show()
	else:
		self.unreadBackground.Hide()
	self.SetSelected(selected)
	self.nameLine.SetText(self.name)


def _CrimsonMessengerConversationRefreshPortrait(self):
	if str(self.key).startswith("guild:"):
		return
	self.avatarIcon.LoadImage(_CrimsonResolvePortrait(self.key, self.name))
	self.avatarIcon.SetPosition(8, 6)


def _CrimsonMessengerConversationSelected(self, selected):
	self.selected = bool(selected)
	state = "selected" if self.selected else "normal"
	self.background.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "row/conversation_" + state + ".png")
	if self.selected:
		selectedFont = getattr(
			localeInfo,
			"UI_DEF_FONT_LARGE_BOLD",
			getattr(localeInfo, "UI_DEF_FONT_BOLD", localeInfo.UI_DEF_FONT),
		)
		self.nameLine.SetFontName(selectedFont)
		self.nameLine.SetPackedFontColor(0xFFE7D0AC)
	else:
		self.nameLine.SetFontName(localeInfo.UI_DEF_FONT)
		self.nameLine.SetPackedFontColor(0xFFCDB58C)
	self.nameLine.SetTop()


def _CrimsonMessengerConversationOverIn(self):
	if not self.selected:
		self.background.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "row/conversation_hover.png")


def _CrimsonMessengerConversationOverOut(self):
	self.background.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "row/conversation_" + ("selected" if self.selected else "normal") + ".png")


def _CrimsonMessengerRowHeight(textHeight):
	return max(38, 26 + max(1, int(textHeight)))


class _CrimsonMessageBubble(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.SetSize(300, 38)
		self.top = ui.ImageBox()
		self.top.SetParent(self)
		self.top.AddFlag("not_pick")
		self.top.Show()
		self.middle = ui.ExpandedImageBox()
		self.middle.SetParent(self)
		self.middle.AddFlag("not_pick")
		self.middle.Show()
		self.bottom = ui.ImageBox()
		self.bottom.SetParent(self)
		self.bottom.AddFlag("not_pick")
		self.bottom.Show()

	def LoadKind(self, kind):
		messageDir = CRIMSON_MESSENGER_IMG_DIR + "message/"
		self.top.LoadImage(messageDir + kind + "_top.png")
		self.middle.LoadImage(messageDir + kind + "_middle.png")
		self.bottom.LoadImage(messageDir + kind + "_bottom.png")

	def SetBubbleHeight(self, height):
		height = max(38, int(height))
		self.SetSize(300, height)
		self.top.SetPosition(0, 0)
		self.middle.SetPosition(0, 18)
		self.middle.SetScale(1.0, float(height - 36) / 2.0)
		self.bottom.SetPosition(0, height - 18)


def _CrimsonMessengerMessageInit(self, copyEvent):
	ui.Window.__init__(self)
	self.SetSize(454, 38)
	self.messageID = ""
	self.body = ""
	self.copyEvent = copyEvent
	self.hyperlinkEvent = None
	# The R1 row class (uir1messenger) brings its own bubble; it is created first, under the texts.
	self.background = (getattr(self, "BUBBLE_CLASS", None) or _CrimsonMessageBubble)()
	self.background.SetParent(self)
	self.background.AddFlag("not_pick")
	self.background.Show()
	self.senderLine = ui.TextLine()
	self.senderLine.SetParent(self)
	self.senderLine.AddFlag("not_pick")
	self.senderLine.Show()
	self.bodyLine = ui.TextLine()
	self.bodyLine.SetParent(self)
	self.bodyLine.SetLimitWidth(224)
	self.bodyLine.SetMultiLine()
	self.bodyLine.AddFlag("not_pick")
	self.bodyLine.Show()
	self.linkBodyLines = []
	self.stateLine = ui.TextLine()
	self.stateLine.SetParent(self)
	self.stateLine.SetHorizontalAlignRight()
	self.stateLine.SetPackedFontColor(0xFFB9A78E)
	self.stateLine.AddFlag("not_pick")
	self.stateLine.Show()
	self.errorLine = ui.TextLine()
	self.errorLine.SetParent(self)
	self.errorLine.SetLimitWidth(224)
	self.errorLine.SetPackedFontColor(0xFFE8A07A)
	self.errorLine.AddFlag("not_pick")
	self.errorLine.Hide()
	self.timeLine = ui.TextLine()
	self.timeLine.SetParent(self)
	self.timeLine.SetHorizontalAlignRight()
	self.timeLine.SetPackedFontColor(0xFF8E806D)
	self.timeLine.AddFlag("not_pick")
	self.timeLine.Show()
	self.retryButton = ui.Button()
	self.retryButton.SetParent(self)
	self.retryButton.SetUpVisual(CRIMSON_MESSENGER_IMG_DIR + "button/launcher_normal.png")
	self.retryButton.SetOverVisual(CRIMSON_MESSENGER_IMG_DIR + "button/launcher_hover.png")
	self.retryButton.SetDownVisual(CRIMSON_MESSENGER_IMG_DIR + "button/launcher_pressed.png")
	self.retryButton.SetText(localeInfo.UNIFIED_MESSENGER_RETRY)
	self.retryButton.Hide()


def _CrimsonMessengerMessageSet(self, message, retryEvent):
	self.messageID = message[1]
	self.body = message[5]
	incoming = int(message[3]) == 1
	body = _SanitizedBody(message[5])
	gameMaster = int(message[8] or 0) == model.MESSAGE_TYPE_GAME_MASTER
	errorText = _MessageErrorText(message, incoming)
	x = 4 if incoming else 156
	self.background.SetPosition(x, 0)
	self.background.LoadKind("incoming" if incoming else "outgoing")
	self.senderLine.SetPosition(x + 10, 6)
	if gameMaster:
		self.senderLine.SetPackedFontColor(0xFFFFA200)
		self.senderLine.SetText("[GM] " + str(message[4]))
	else:
		self.senderLine.SetPackedFontColor(0xFFFFE9BD if incoming else 0xFFE63A54)
		self.senderLine.SetText(str(message[4]))
	self.bodyLine.SetPosition(x + 10, 21)
	self.stateLine.SetPosition(x + 242, 6)
	textHeight = _CrimsonMessengerMeasuredTextHeight(
		self.bodyLine, body)
	for line in self.linkBodyLines:
		line.Hide()
	self.linkBodyLines = []
	if "|H" in body:
		# Native multiline text only picks hyperlinks on its first line.
		# Use the same balanced single-line runs as the general chat.
		lines, lineHeight = _CrimsonMessengerLinkLines(self.bodyLine, body)
		self.bodyLine.Hide()
		for index, value in enumerate(lines):
			line = ui.TextLine()
			line.SetParent(self)
			line.SetPosition(x + 10, 21 + index * lineHeight)
			line.AddFlag("not_pick")
			line.DisableEnterToken()
			line.SetText(value)
			line.Show()
			self.linkBodyLines.append(line)
	else:
		self.bodyLine.Show()
	rowHeight = _CrimsonMessengerRowHeight(textHeight)
	if errorText:
		# The persisted server/local reason stays next to the message.
		self.errorLine.SetPosition(x + 10, 21 + textHeight + 2)
		self.errorLine.SetText(errorText)
		self.errorLine.Show()
		rowHeight += CRIMSON_ERROR_LINE_HEIGHT
	else:
		self.errorLine.Hide()
	self.SetSize(454, rowHeight)
	self.background.SetBubbleHeight(rowHeight)
	self.timeLine.SetPosition(x + 292, rowHeight - 17)
	timestamp = model.message_time_ms(message)
	self.timeLine.SetText(time.strftime("%H:%M", time.localtime(timestamp / 1000.0)))
	stateKey = "" if incoming else model.message_state_key(message[9])
	if model.message_error(message) == model.ERROR_OUTCOME_UNKNOWN:
		stateKey = ""  # the reason line explains the unknown outcome
	self.stateLine.SetText(getattr(localeInfo, stateKey, "") if stateKey else "")
	if _MessageRetryable(message, incoming):
		self.retryButton.SetPosition(x + 118, 5)
		self.retryButton.SetEvent(retryEvent, message[1])
		self.retryButton.Show()
	else:
		self.retryButton.Hide()


def _CrimsonApplyHeaderPortrait(self):
	if not getattr(self, "headerPortrait", None):
		return
	if not self.selectedName:
		self.headerPortrait.Hide()
		return
	if str(self.selectedKey).startswith("guild:"):
		self.headerPortrait.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "icon/guild_conversation.png")
		self.headerPortrait.SetPosition(242, 48)
	else:
		self.headerPortrait.LoadImage(
			_CrimsonResolvePortrait(self.selectedKey, self.selectedName))
		self.headerPortrait.SetPosition(238, 44)
	self.headerPortrait.Show()


TITLE_MINIMIZE_IMAGES = tuple(PUBLIC + "crimson/controls/legacy/minimize_%02d.tga" % index
	for index in (1, 2, 3))


def _MakeTitleBarMinimizeButton(board, event):
	# "_" left of the title bar's X, the same crimson control family (the
	# whisper dialog's minimize). A child of the title bar: it hides with it
	# when the R1 look draws its own header (uir1messenger adds its "_").
	titleBar = getattr(board, "titleBar", None)
	closeButton = getattr(titleBar, "btnClose", None)
	if not titleBar or not closeButton:
		return None
	button = ui.Button()
	button.SetParent(titleBar)
	button.SetUpVisual(TITLE_MINIMIZE_IMAGES[0])
	button.SetOverVisual(TITLE_MINIMIZE_IMAGES[1])
	button.SetDownVisual(TITLE_MINIMIZE_IMAGES[2])
	try:
		import uiScriptLocale
		tooltip = uiScriptLocale.MINIMIZE
	except Exception:
		tooltip = u"Minimalizovat"
	button.SetToolTipText(tooltip, 0, -23)
	x, y = closeButton.GetLocalPosition()
	button.SetPosition(x - button.GetWidth() - 3,
		y + max(0, (closeButton.GetHeight() - button.GetHeight()) // 2))
	button.SetEvent(event)
	button.Show()
	return button


def _CrimsonMessengerLoadWindow(self):
	if self.loaded:
		return True
	loader = ui.PythonScriptLoader()
	loader.LoadScriptFile(self, "uiscript/unifiedmessengerwindow.py")
	self.board = self.GetChild("Board")
	self.searchBackground = self.GetChild("ConversationSearchBackground")
	self.search = self.GetChild("ConversationSearch")
	self.searchHint = self.GetChild("ConversationSearchHint")
	self.conversationPane = self.GetChild("ConversationList")
	self.unreadBadge = self.GetChild("UnreadBadge")
	self.newMessageButton = self.GetChild("NewMessageButton")
	self.conversationHeader = self.GetChild("ConversationHeader")
	self.historyPane = self.GetChild("HistoryPane")
	self.emptyState = self.GetChild("EmptyState")
	self.composerBar = self.GetChild("ComposerBar")
	self.composer = self.GetChild("Composer")
	self.sendButton = self.GetChild("SendButton")
	self.addFriendButton = self.GetChild("AddFriendButton")
	self.marketButton = self.GetChild("MarketButton")
	self.blockButton = self.GetChild("BlockButton")
	self.settingsButton = self.GetChild("SettingsButton")
	self.deleteConversationButton = self.GetChild("DeleteConversationButton")
	self.conversationTitle = self.GetChild("ConversationTitle")
	self.conversationTitle.SetPackedFontColor(0xFFE7D0AC)
	self.presenceText = self.GetChild("PresenceText")
	self.presenceText.Hide()
	self.presenceDot = self.GetChild("PresenceDot")
	self.presenceDot.Hide()
	self.typingIndicator = self.GetChild("TypingIndicator")
	self.headerPortrait = self.GetChild("HeaderPortrait")
	self.headerPortrait.Hide()

	self.conversationScrollBar = uicrimsonember.CrimsonScrollBar()
	self.conversationScrollBar.SetParent(self)
	self.conversationScrollBar.SetPosition(200, 82)
	self.conversationScrollBar.SetScrollBarSize(315)
	self.conversationScrollBar.SetScrollEvent(ui.__mem_func__(self.RenderConversations))
	self.conversationScrollBar.Show()
	self.historyScrollBar = uicrimsonember.CrimsonScrollBar()
	self.historyScrollBar.SetParent(self)
	self.historyScrollBar.SetPosition(700, 96)
	self.historyScrollBar.SetScrollBarSize(293)
	self.historyScrollBar.SetScrollEvent(ui.__mem_func__(self.OnHistoryScroll))
	self.historyScrollBar.Show()
	self.messageMeasureLine = ui.TextLine()
	self.messageMeasureLine.SetParent(self.historyPane)
	self.messageMeasureLine.SetLimitWidth(224)
	self.messageMeasureLine.SetMultiLine()
	self.messageMeasureLine.AddFlag("not_pick")
	self.messageMeasureLine.Hide()
	self.SetOnRunMouseWheelEvent(
		ui.__mem_func__(self._CrimsonRootMouseWheel))

	self.conversationPane.AddFlag("float")
	self.conversationPane.SetTop()
	self.board.SetCloseEvent(ui.__mem_func__(self.Close))
	self.minimizeButton = _MakeTitleBarMinimizeButton(
		self.board, ui.__mem_func__(self.Minimize))
	self.search.SetReturnEvent(ui.__mem_func__(self.RefreshConversations))
	self.search.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
	self.search.OnIMEUpdate = ui.__mem_func__(self._CrimsonSearchIMEUpdate)
	self.search.SetOnFocusEvent(ui.__mem_func__(self._CrimsonSearchFocus))
	self.search.SetKillFocusEvent(ui.__mem_func__(self._CrimsonSearchBlur))
	self.composer.SetReturnEvent(ui.__mem_func__(self.SendMessage))
	self.composer.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
	self.composer.SetOnFocusEvent(ui.__mem_func__(self._CrimsonComposerFocus))
	self.composer.SetKillFocusEvent(ui.__mem_func__(self._CrimsonComposerBlur))
	self.sendButton.SetEvent(ui.__mem_func__(self.SendMessage))
	self.newMessageButton.SetEvent(ui.__mem_func__(self.OpenNewMessage))
	self.addFriendButton.SetEvent(ui.__mem_func__(self.AddSelectedFriend))
	self.marketButton.SetEvent(ui.__mem_func__(self.OpenSelectedSellerMarket))
	self.marketButton.SetToolTipText(getattr(
		localeInfo, "UNIFIED_MESSENGER_MARKET_OFFERS",
		"Zobrazit nab\u00eddky hr\u00e1\u010de"))
	self.blockButton.SetEvent(ui.__mem_func__(self.BlockSelectedPeer))
	self.settingsButton.SetEvent(ui.__mem_func__(self.ToggleSettings))
	self.deleteConversationButton.SetEvent(ui.__mem_func__(self.AskDeleteConversation))
	# The R1 look (default) is drawn into the loaded window; "Starý vzhled" or a failure keeps this one.
	self.r1Skin = uir1messenger.Build(self) if uir1messenger else None
	self.loaded = True
	self.RefreshConversations()
	self.RefreshSelectionState()
	return True


def _CrimsonMessengerSearchIMEUpdate(self):
	ui.EditLine.OnIMEUpdate(self.search)
	if self.search.GetText():
		self.searchHint.Hide()
	else:
		self.searchHint.Show()
	self.OnSearchEdited()


def _CrimsonMessengerSearchFocus(self):
	self.searchBackground.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "field/search_focused.png")
	self.searchHint.Hide()


def _CrimsonMessengerSearchBlur(self):
	self.searchBackground.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "field/search_normal.png")
	if not self.search.GetText():
		self.searchHint.Show()


def _CrimsonMessengerComposerFocus(self):
	self.composerBar.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "field/composer_focused.png")


def _CrimsonMessengerComposerBlur(self):
	self.composerBar.LoadImage(CRIMSON_MESSENGER_IMG_DIR + "field/composer_normal.png")


def _CrimsonMessengerMouseInWindow(self, window):
	mouseX, mouseY = self.GetMouseLocalPosition()
	windowX, windowY = window.GetLocalPosition()
	return (
		mouseX >= windowX and mouseX < windowX + window.GetWidth()
		and mouseY >= windowY and mouseY < windowY + window.GetHeight())


def _CrimsonMessengerRootMouseWheel(self, isDown):
	delta = -1 if isDown else 1
	if _CrimsonMessengerMouseInWindow(self, self.historyPane):
		self.historyScrollBar.OnMouseWheel(delta)
	elif _CrimsonMessengerMouseInWindow(self, self.conversationPane):
		self.conversationScrollBar.OnMouseWheel(delta)
	else:
		return False	# outside both panes (the bars, the header): the panel wheel (uiwheel) picks the bar beside it
	return True


def _CrimsonMessengerValidStarts(dayKeys, heights, unreadAt, viewportHeight):
	if not heights:
		return [0]
	lastStart = 0
	while lastStart < len(heights) - 1:
		yPos = 4
		previousDay = None
		lastBottom = yPos
		for index in range(lastStart, len(heights)):
			if dayKeys[index] != previousDay:
				yPos += 20
				previousDay = dayKeys[index]
			if index == unreadAt:
				yPos += 20
			lastBottom = yPos + int(heights[index])
			yPos = lastBottom + 4
		if lastBottom <= int(viewportHeight):
			break
		lastStart += 1
	return list(range(lastStart + 1))


def _CrimsonMessengerStartFromPosition(position, validStarts):
	if not validStarts:
		return 0
	position = max(0.0, min(1.0, float(position)))
	index = int(round(position * max(0, len(validStarts) - 1)))
	return validStarts[index]


def _CrimsonMessengerLinkLines(textLine, body):
	import compactchatmodel

	def measure(value):
		textLine.SetText(value)
		return textLine.GetTextSize()[0]

	lines = compactchatmodel.wrap_rich(str(body).replace("[ENTER]", "\n"), 224, measure)
	textLine.SetText(str(body))
	return lines, max(1, int(textLine.GetTextHeight()))


def _CrimsonMessengerMeasuredTextHeight(textLine, body):
	body = str(body)
	if "|H" in body:
		lines, lineHeight = _CrimsonMessengerLinkLines(textLine, body)
		return len(lines) * lineHeight
	totalLines = 0
	baseTextHeight = 1
	normalized = body.replace("[ENTER]", "\n").replace("\\n", "\n")
	for segment in normalized.split("\n"):
		textLine.SetText(segment)
		baseTextHeight = max(baseTextHeight, int(textLine.GetTextHeight()))
		totalLines += max(1, int(textLine.GetTextLineCount()))
	textLine.SetText(body)
	return baseTextHeight * max(1, totalLines)


def _CrimsonMessengerMeasureRowHeight(self, message):
	# Heights depend only on the immutable body and the displayed reason, so a
	# wheel step no longer re-measures every loaded message.
	errorText = _MessageErrorText(message, int(message[3]) == 1)
	cacheKey = (message[0], errorText)
	cache = self.rowHeightCache
	height = cache.get(cacheKey)
	if height is None:
		textHeight = _CrimsonMessengerMeasuredTextHeight(
			self.messageMeasureLine, _SanitizedBody(message[5]))
		height = _CrimsonMessengerRowHeight(textHeight)
		if errorText:
			height += CRIMSON_ERROR_LINE_HEIGHT
		if len(cache) >= MAX_ROW_HEIGHT_CACHE:
			cache.clear()
		cache[cacheKey] = height
	return height


def _CrimsonMessengerUnreadAt(messageCount, unreadCount):
	if not unreadCount:
		return -1
	return max(0, int(messageCount) - int(unreadCount))


def _CrimsonMessengerUnreadIndex(self):
	# The divider stays above the oldest message that was unread when the
	# conversation was opened. It used to sit `unread` rows from the end, so
	# the player's own messages (and rows added later) pushed it onto their
	# own last message.
	if getattr(self, "unreadAnchorPending", False):
		self.unreadAnchorPending = False
		self.unreadAnchorRowID = model.first_unread_row_id(
			self.loadedMessages, self.selectedUnread)
	anchor = getattr(self, "unreadAnchorRowID", None)
	if anchor is None:
		return -1
	for index, message in enumerate(self.loadedMessages):
		if message[0] == anchor:
			return index
	return -1


def _CrimsonMessengerRenderMessages(self, anchorRowID=None, keepPosition=False):
	self._UnifiedMessengerWindow__DestroyRows(self.messageRows)
	skin = getattr(self, "r1Skin", None)
	viewportHeight = getattr(self, "historyViewportHeight", 303)
	dayKeys = []
	heights = []
	for message in self.loadedMessages:
		timestamp = model.message_time_ms(message)
		dayKeys.append(time.strftime(
			"%Y-%m-%d", time.localtime(timestamp / 1000.0)))
		heights.append(_CrimsonMessengerMeasureRowHeight(self, message))
	unreadAt = _CrimsonMessengerUnreadIndex(self)
	validStarts = _CrimsonMessengerValidStarts(
		dayKeys, heights, unreadAt, viewportHeight)
	self.historyScrollable = len(validStarts) > 1
	if len(validStarts) > 1:
		self.historyScrollBar.SetScrollStep(
			1.0 / float(len(validStarts) - 1))
		if anchorRowID is not None:
			# Keep the previously visible row in place after paging.
			anchorIndex = 0
			for index, message in enumerate(self.loadedMessages):
				if message[0] == anchorRowID:
					anchorIndex = index
					break
			anchorStart = min(anchorIndex, validStarts[-1])
			self.historyScrollBar.SetPos(
				float(anchorStart) / float(len(validStarts) - 1), False)
	else:
		self.historyScrollBar.SetPos(0.0, False)
	start = _CrimsonMessengerStartFromPosition(
		self.historyScrollBar.GetPos(), validStarts)
	previousDay = None
	yPos = 4
	renderedRows = 0
	for absoluteIndex in range(start, len(self.loadedMessages)):
		message = self.loadedMessages[absoluteIndex]
		day = dayKeys[absoluteIndex]
		separatorHeight = 20 if day != previousDay else 0
		if absoluteIndex == unreadAt:
			separatorHeight += 20
		rowHeight = heights[absoluteIndex]
		if yPos + separatorHeight + rowHeight > viewportHeight and renderedRows:
			break
		if day != previousDay:
			separator = ui.TextLine()
			separator.SetParent(self.historyPane)
			separator.SetPosition(235, yPos)
			separator.SetHorizontalAlignCenter()
			separator.SetText(day)
			separator.SetPackedFontColor(0xFF8D806E)
			separator.Show()
			self.messageRows.append(separator)
			yPos += 20
			previousDay = day
		if absoluteIndex == unreadAt:
			separator = ui.TextLine()
			separator.SetParent(self.historyPane)
			separator.SetPosition(235, yPos)
			separator.SetHorizontalAlignCenter()
			separator.SetText(UNREAD_DIVIDER_TEXT)
			separator.SetPackedFontColor(0xFFCDB58C)
			separator.Show()
			self.messageRows.append(separator)
			yPos += 20
		row = (skin.MessageRow if skin else MessageRow)(ui.__mem_func__(self.CopyMessage))
		row.SetParent(self.historyPane)
		row.SetHyperlinkEvent(ui.__mem_func__(self.OnClickMessageLink))
		row.SetPosition(8, yPos)
		row.SetMessage(message, ui.__mem_func__(self.RetryMessage))
		row.Show()
		self.messageRows.append(row)
		yPos += row.GetHeight() + 4
		renderedRows += 1
	if skin:
		skin.AfterMessages(len(validStarts))


def _CrimsonMessengerRenderConversations(self):
	if not self.loaded:
		return
	self._UnifiedMessengerWindow__DestroyRows(self.conversationRows)
	rows = self.filteredConversations
	for row in rows:
		if not str(row["key"]).startswith("guild:"):
			row["online"] = _CrimsonRowPresence(self, row["name"])
	skin = getattr(self, "r1Skin", None)
	rowClass = skin.ConversationRow if skin else ConversationRow
	rowCount = skin.CONVERSATION_ROWS if skin else CONVERSATION_ROWS
	maximumStart = max(0, len(rows) - rowCount)
	start = int(self.conversationScrollBar.GetPos() * maximumStart) if maximumStart else 0
	# The badge counts all private conversations, independent of the filter.
	unreadTotal = model.unread_total(self.allConversations)
	for index, row in enumerate(rows[start:start + rowCount]):
		item = rowClass()
		item.SetParent(self.conversationPane)
		item.SetPosition(0, index * rowClass.HEIGHT)
		item.SetConversation(row, row["key"] == self.selectedKey,
			ui.__mem_func__(self._UnifiedMessengerWindow__SelectConversation))
		item.Show()
		self.conversationRows.append(item)
	badgeEnabled = self._UnifiedMessengerWindow__LoadSettings()["badge"]
	self.unreadBadge.SetText(str(unreadTotal) if unreadTotal and badgeEnabled else "")
	if skin:
		skin.AfterConversations(unreadTotal, badgeEnabled, len(rows))
	_CrimsonApplyPresence(self)


_CrimsonOriginalOpenConversation = UnifiedMessengerWindow.OpenConversation


def _CrimsonMessengerOpenConversation(self, name, key=None, markRead=True):
	result = _CrimsonOriginalOpenConversation(self, name, key, markRead)
	_CrimsonApplyHeaderPortrait(self)
	return result


_CrimsonOriginalRefreshSelectionState = UnifiedMessengerWindow.RefreshSelectionState


def _CrimsonMessengerRefreshSelectionState(self):
	_CrimsonOriginalRefreshSelectionState(self)
	self.SyncPresenceWatch()
	_CrimsonApplyHeaderPortrait(self)
	_CrimsonApplyPresence(self)


def _CrimsonMessengerPlayerProfileChanged(self):
	for row in self.conversationRows:
		if hasattr(row, "RefreshPortrait"):
			row.RefreshPortrait()
	_CrimsonApplyHeaderPortrait(self)


_CrimsonOriginalMessengerOnUpdate = UnifiedMessengerWindow.OnUpdate


def _CrimsonMessengerOnUpdate(self):
	messengerportraitresolver.Pump()
	_CrimsonOriginalMessengerOnUpdate(self)


CONVERSATION_ROWS = 6
ConversationRow.HEIGHT = 53
ConversationRow.__init__ = _CrimsonMessengerConversationInit
ConversationRow.SetConversation = _CrimsonMessengerConversationSet
ConversationRow.RefreshPortrait = _CrimsonMessengerConversationRefreshPortrait
ConversationRow.SetSelected = _CrimsonMessengerConversationSelected
ConversationRow.OnMouseOverIn = _CrimsonMessengerConversationOverIn
ConversationRow.OnMouseOverOut = _CrimsonMessengerConversationOverOut
MessageRow.HEIGHT = 38
MessageRow.__init__ = _CrimsonMessengerMessageInit
MessageRow.SetMessage = _CrimsonMessengerMessageSet
UnifiedMessengerWindow.LoadWindow = _CrimsonMessengerLoadWindow
UnifiedMessengerWindow._CrimsonSearchIMEUpdate = _CrimsonMessengerSearchIMEUpdate
UnifiedMessengerWindow._CrimsonSearchFocus = _CrimsonMessengerSearchFocus
UnifiedMessengerWindow._CrimsonSearchBlur = _CrimsonMessengerSearchBlur
UnifiedMessengerWindow._CrimsonComposerFocus = _CrimsonMessengerComposerFocus
UnifiedMessengerWindow._CrimsonComposerBlur = _CrimsonMessengerComposerBlur
UnifiedMessengerWindow._CrimsonRootMouseWheel = _CrimsonMessengerRootMouseWheel
UnifiedMessengerWindow.OpenConversation = _CrimsonMessengerOpenConversation
UnifiedMessengerWindow.RefreshSelectionState = _CrimsonMessengerRefreshSelectionState
UnifiedMessengerWindow.OnPlayerProfileChanged = _CrimsonMessengerPlayerProfileChanged
UnifiedMessengerWindow.OnUpdate = _CrimsonMessengerOnUpdate
UnifiedMessengerWindow._UnifiedMessengerWindow__RenderMessages = _CrimsonMessengerRenderMessages
UnifiedMessengerWindow.RenderConversations = _CrimsonMessengerRenderConversations
# CRIMSON_EMBER_MESSENGER_V16_END


# DUEL_CHALLENGE_ROW_BEGIN
# A duel challenge is also a session row of the challenger's thread (see
# UnifiedMessengerRouter.ReceiveDuel): the bubble with the server's text gets
# Přijmout (left, confirm) and Odmítnout (right, cancel) under it. Once the
# challenge is answered here or in the chat line, expires, is ended by the
# server or replaced, a grey state ("Přijato", "Odmítnuto", "Vypršelo", ...)
# takes the buttons' place. The state lives in duelchallenge, shared with the
# chat line, so an answer in one place shows in both.
import duelchallenge

DUEL_ACTIONS_HEIGHT = 28
DUEL_FONT = "Tahoma:12"


class DuelActions(ui.Window):
	BUTTON_GAP = 6
	STATUS_COLOR = 0xFF8E806D

	def __init__(self):
		ui.Window.__init__(self)
		self.identifier = 0
		self.answerEvent = None
		self.buttons = []
		x = 0
		for action in (duelchallenge.ACCEPT, duelchallenge.DECLINE):
			button = self.MakeButton(action, x)
			x += button.GetWidth() + self.BUTTON_GAP
			self.buttons.append(button)
		self.SetSize(max(1, x - self.BUTTON_GAP), 22)
		self.status = self.MakeStatus()

	def MakeButton(self, action, x):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, 0)
		button.SetUpVisual(CRIMSON_MESSENGER_IMG_DIR + "button/launcher_normal.png")
		button.SetOverVisual(CRIMSON_MESSENGER_IMG_DIR + "button/launcher_hover.png")
		button.SetDownVisual(CRIMSON_MESSENGER_IMG_DIR + "button/launcher_pressed.png")
		button.SetText(duelchallenge.BUTTON_TEXTS[action])
		button.SetEvent(ui.__mem_func__(self.Answer), action)
		button.Show()
		return button

	def MakeStatus(self):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetFontName(DUEL_FONT)
		line.SetPosition(0, 4)
		color = int(self.STATUS_COLOR)
		# Signed: the x64 binding silently ignores values >= 0x80000000.
		line.SetPackedFontColor(color - 0x100000000 if color >= 0x80000000 else color)
		line.AddFlag("not_pick")
		line.Hide()
		return line

	def SetChallenge(self, identifier):
		# The player's own request has no actions, only its state.
		self.identifier = int(identifier)
		challenges = duelchallenge.challenges
		status = u""
		if challenges.IsOutgoing(self.identifier) or not challenges.IsActive(self.identifier):
			status = challenges.StatusText(self.identifier) or \
				duelchallenge.STATE_TEXTS[duelchallenge.STATE_EXPIRED]
		for button in self.buttons:
			if status:
				button.Hide()
			else:
				button.Show()
		self.status.SetText(status)
		if status:
			self.status.Show()
		else:
			self.status.Hide()

	def SetAnswerEvent(self, event):
		self.answerEvent = event

	def Answer(self, action):
		challenges = duelchallenge.challenges
		if self.answerEvent and challenges.IsActive(self.identifier) and \
				not challenges.IsOutgoing(self.identifier):
			self.answerEvent(action, self.identifier)


_DuelOriginalMessageSet = MessageRow.SetMessage


def _DuelMessageSet(self, message, retryEvent):
	_DuelOriginalMessageSet(self, message, retryEvent)
	identifier = model.duel_identifier(message)
	actions = getattr(self, "duelActions", None)
	if not identifier:
		if actions:
			actions.Hide()
		return
	if not actions:
		actions = (getattr(self, "DUEL_ACTIONS_CLASS", None) or DuelActions)()
		actions.SetParent(self)
		self.duelActions = actions
	x = 4 if int(message[3]) == 1 else 156
	self.stateLine.SetText("")  # no "Doručeno": the actions show the state
	height = self.GetHeight()
	actions.SetPosition(x + 10, height - 2)
	actions.SetChallenge(identifier)
	actions.Show()
	height += DUEL_ACTIONS_HEIGHT
	self.SetSize(454, height)
	self.background.SetBubbleHeight(height)
	self.timeLine.SetPosition(x + 292, height - 17)


_DuelOriginalMeasureRowHeight = _CrimsonMessengerMeasureRowHeight


def _DuelMeasureRowHeight(self, message):
	height = _DuelOriginalMeasureRowHeight(self, message)
	return height + DUEL_ACTIONS_HEIGHT if model.duel_identifier(message) else height


_DuelOriginalRenderMessages = UnifiedMessengerWindow._UnifiedMessengerWindow__RenderMessages


def _DuelRenderMessages(self, anchorRowID=None, keepPosition=False):
	_DuelOriginalRenderMessages(self, anchorRowID, keepPosition)
	self.duelRevision = duelchallenge.challenges.Revision()
	for row in self.messageRows:
		actions = getattr(row, "duelActions", None)
		if actions:
			actions.SetAnswerEvent(ui.__mem_func__(self.AnswerDuel))


def _DuelMessengerAnswer(self, action, identifier):
	# The same answer as the chat line's link (Přijmout sends "/pvp <vid>").
	if self.interface:
		self.interface.AnswerDuelChallenge("duel:%s:%d" % (action, int(identifier)))
	# The rows are rebuilt on the next update, not inside the button's click.
	self.duelRevision = None


_DuelOriginalOnUpdate = UnifiedMessengerWindow.OnUpdate


def _DuelMessengerOnUpdate(self):
	_DuelOriginalOnUpdate(self)
	if not self.loaded or not self.IsShow():
		return
	# Answered in the chat, expired or ended by the server: re-render the rows.
	revision = duelchallenge.challenges.Revision()
	if revision != self.duelRevision:
		self.duelRevision = revision
		if any(model.duel_identifier(message) for message in self.loadedMessages):
			self._UnifiedMessengerWindow__RenderMessages()


MessageRow.SetMessage = _DuelMessageSet
_CrimsonMessengerMeasureRowHeight = _DuelMeasureRowHeight
UnifiedMessengerWindow._UnifiedMessengerWindow__RenderMessages = _DuelRenderMessages
UnifiedMessengerWindow.AnswerDuel = _DuelMessengerAnswer
UnifiedMessengerWindow.OnUpdate = _DuelMessengerOnUpdate
# DUEL_CHALLENGE_ROW_END
