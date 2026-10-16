import app
import localeInfo
import net
import player
import ui
import wndMgr

import pvpmatchmaking
import uicrimsoncontrols


WIDTH = 860
WINDOW_HEIGHT = 513
CONTENT_WIDTH = 821
CONTENT_HEIGHT = 491
CONTENT_X = 19
CONTENT_Y = 22
HEIGHT = CONTENT_HEIGHT
ASSET = "d:/ymir work/ui/game/crimson_ember/pvp_matchmaking/"
DUNGEON = "d:/ymir work/ui/game/crimson_ember/dungeon_teleport/"

PLAY_LEFT = (8, 54, 224, 427)
PLAY_CENTER = (240, 54, 335, 427)
PLAY_RIGHT = (583, 54, 230, 427)
QUEUE_ACTION = (309, 397, 196, 36)
LEADERBOARD_SIDE = (8, 54, 214, 427)
LEADERBOARD_TABLE = (230, 54, 583, 427)
HISTORY_TABLE = (8, 54, 805, 427)
LEADERBOARD_COLUMNS = (252, 286, 330, 650, 720, 790)


def _SignedColor(color):
	# wndMgr's Python 3 bridge accepts a C int, while packed ARGB is a DWORD.
	color = int(color)
	return color - 0x100000000 if color > 0x7fffffff else color


GOLD = _SignedColor(0xffffcf6c)
WHITE = _SignedColor(0xffeee6dc)
DIM = _SignedColor(0xffa99f94)
MUTED = _SignedColor(0xff766e67)
GREEN = _SignedColor(0xff72c66a)
AMBER = _SignedColor(0xffdea435)
RED = _SignedColor(0xffe04457)
BLUE = _SignedColor(0xff69a7d7)

SEMANTIC_COLORS = {
	"wins": GREEN,
	"waiting": AMBER,
	"error": RED,
	"played": BLUE,
	"rank": GOLD,
}


def _PersonalOutcome(outcome, ratingDelta):
	outcome = int(outcome)
	ratingDelta = int(ratingDelta)
	if outcome == 3:
		return ("REMÍZA", WHITE)
	if outcome == 4:
		return ("BEZ VÝSLEDKU", MUTED)
	if ratingDelta > 0:
		return ("VÝHRA", GREEN)
	if ratingDelta < 0:
		return ("PROHRA", RED)
	return ("ZÁPAS UKONČEN", MUTED)


def _QueueCooldownPresentation(cooldownSeconds):
	remaining = max(0, int(cooldownSeconds))
	if remaining > 0:
		return ("TREST FRONTY — %d:%02d" % (
			remaining // 60, remaining % 60), RED, False)
	return ("PŘIPRAVEN NA HLEDÁNÍ", GREEN, True)

MODE_CARD_WIDTH = 210
MODE_CARD_HEIGHT = 92
MODE_CARD_BORDER = _SignedColor(0xff5b3423)
MODE_CARD_INNER_BORDER = _SignedColor(0xff1a1210)
MODE_CARD_SELECTED = _SignedColor(0xff180509)
MODE_CARD_NORMAL = _SignedColor(0xff070606)
PANEL_BORDER = _SignedColor(0xff5b3423)
PANEL_INNER = _SignedColor(0xff1a1210)
PANEL_FILL = _SignedColor(0xff030303)
ROW_BORDER = _SignedColor(0xff2d1d17)
ROW_FILL = _SignedColor(0xff080707)
HEADER_LEFT_WIDTH = 12
HEADER_RIGHT_WIDTH = 23


def _PassiveBar(parent, x, y, width, height, color):
	bar = ui.Bar()
	bar.SetParent(parent)
	bar.SetPosition(x, y)
	bar.SetSize(max(1, int(width)), max(1, int(height)))
	bar.SetColor(color)
	bar.AddFlag("not_pick")
	bar.Show()
	return bar


class _LayeredPanel(ui.Window):
	def __init__(self, parent, x, y, width, height, fill=PANEL_FILL):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.AddFlag("not_pick")
		self.outer = _PassiveBar(self, 0, 0, width, height, PANEL_BORDER)
		self.edge = _PassiveBar(self, 1, 1, width - 2, height - 2, fill)
		self.inner = _PassiveBar(self, 3, 3, width - 6, height - 6, PANEL_INNER)
		self.surface = _PassiveBar(self, 4, 4, width - 8, height - 8, fill)
		self.Show()


class _SectionHeader(ui.Window):
	def __init__(self, owner, parent, x, y, width, text):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, 28)
		self.AddFlag("not_pick")
		self.left = owner._Image(self, 0, 0,
			ASSET + "header/section_left_12x28.png", False)
		self.middle = owner._Image(self, HEADER_LEFT_WIDTH, 0,
			ASSET + "header/section_middle_260x28.png", False)
		middleWidth = max(1, width - HEADER_LEFT_WIDTH - HEADER_RIGHT_WIDTH)
		self.middle.SetScale(float(middleWidth) / 260.0, 1.0)
		self.right = owner._Image(self, width - HEADER_RIGHT_WIDTH, 0,
			ASSET + "header/section_right_23x28.png", False)
		self.label = owner._Label(self, 10, 7, text, GOLD)
		self.textState = text
		self.Show()

	def SetText(self, text):
		if text == self.textState:
			return
		self.textState = text
		self.label.SetText(text)


class _StatRow(ui.Window):
	def __init__(self, owner, parent, x, y, width, label, value,
			accent=GOLD, height=27):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.AddFlag("not_pick")
		self.outer = _PassiveBar(self, 0, 0, width, height, ROW_BORDER)
		self.edge = _PassiveBar(self, 1, 1, width - 2, height - 2, ROW_FILL)
		self.inner = _PassiveBar(self, 3, 3, width - 6, height - 6, PANEL_INNER)
		self.surface = _PassiveBar(self, 4, 4, width - 8, height - 8, ROW_FILL)
		dotY = max(1, (height - 8) // 2)
		self.dot = _PassiveBar(self, 8, dotY, 8, 8, accent)
		textY = max(1, (height - 13) // 2)
		self.label = owner._Label(self, 22, textY, label, DIM)
		self.value = owner._Label(self, width - 8, textY, value, WHITE, "right")
		self.valueState = (value, WHITE)
		self.accentState = accent
		self.Show()

	def SetValue(self, value, color=WHITE):
		state = (value, color)
		if state == self.valueState:
			return
		self.valueState = state
		self.value.SetText(value)
		self.value.SetPackedFontColor(color)

	def SetAccent(self, color):
		if color == self.accentState:
			return
		self.accentState = color
		self.dot.SetColor(color)


class _TextLink(ui.Window):
	def __init__(self, parent, x, y, width, height, text, event):
		ui.Window.__init__(self)
		self.event = event
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.SetPosition(width // 2, max(0, (height - 14) // 2))
		self.label.SetHorizontalAlignCenter()
		self.label.SetText(text)
		self.label.SetPackedFontColor(GOLD)
		self.label.SetOutline()
		self.label.AddFlag("not_pick")
		self.label.Show()
		self.Show()

	def OnMouseOverIn(self):
		self.label.SetPackedFontColor(WHITE)

	def OnMouseOverOut(self):
		self.label.SetPackedFontColor(GOLD)

	def OnMouseLeftButtonUp(self):
		if self.IsIn():
			self.event()


def _Text(key, fallback):
	return getattr(localeInfo, key, fallback)


def _Format(value):
	return format(int(value), ",").replace(",", " ")


def _IsCommandPending():
	method = getattr(pvpmatchmaking, "IsCommandPending", None)
	if not method:
		return False
	try:
		return bool(method())
	except Exception:
		return False


def _Rank(rating):
	rating = int(rating)
	if rating >= 2000:
		return ("legenda", "LEGENDA", 0)
	if rating >= 1800:
		return ("diamant", "DIAMANT", 2000)
	if rating >= 1600:
		return ("platina", "PLATINA", 1800)
	if rating >= 1500:
		return ("zlato", "ZLATO I", 1600)
	if rating >= 1350:
		return ("zlato", "ZLATO II", 1500)
	if rating >= 1200:
		return ("zlato", "ZLATO III", 1350)
	if rating >= 900:
		return ("stribro", "STŘÍBRO", 1200)
	return ("bronz", "BRONZ", 900)


def _ModeName(mode):
	return {1: "1V1", 2: "2V2", 3: "3V3"}.get(int(mode), "1V1")


def _ModeTitle(mode):
	return {1: "HODNOCENÝ SOUBOJ", 2: "HODNOCENÁ DVOJICE",
		3: "HODNOCENÁ TROJICE"}.get(int(mode), "HODNOCENÝ SOUBOJ")


def _ErrorText(error):
	return {1: "SYSTÉM JE VYPNUTÝ", 2: "SLUŽBA NENÍ DOSTUPNÁ",
		3: "NEPLATNÝ POŽADAVEK", 4: "POSTAVA NESPLŇUJE PODMÍNKY",
		5: "FRONTU MŮŽE SPUSTIT JEN VŮDCE SKUPINY",
		6: "SKUPINA JE PRO TENTO REŽIM PŘÍLIŠ VELKÁ",
		7: "UŽ JSI VE FRONTĚ", 8: "TREST FRONTY — %d s" % int(error[1]),
		9: "POŽADAVEK UŽ NENÍ PLATNÝ", 10: "VNITŘNÍ CHYBA"}.get(
			int(error[0]), "")


class _ModeCard(ui.Window):
	def __init__(self, owner, mode, y):
		ui.Window.__init__(self)
		self.owner = owner
		self.mode = mode
		self.SetParent(owner.body)
		self.SetPosition(15, y)
		self.SetSize(MODE_CARD_WIDTH, MODE_CARD_HEIGHT)
		self.background = ui.Bar()
		self.background.SetParent(self)
		self.background.SetPosition(0, 0)
		self.background.SetSize(MODE_CARD_WIDTH, MODE_CARD_HEIGHT)
		self.background.SetColor(MODE_CARD_BORDER)
		self.background.AddFlag("not_pick")
		self.background.Show()
		self.inner = ui.Bar()
		self.inner.SetParent(self)
		self.inner.SetPosition(1, 1)
		self.inner.SetSize(MODE_CARD_WIDTH - 2, MODE_CARD_HEIGHT - 2)
		self.inner.SetColor(MODE_CARD_INNER_BORDER)
		self.inner.AddFlag("not_pick")
		self.inner.Show()
		self.innerLine = ui.Bar()
		self.innerLine.SetParent(self)
		self.innerLine.SetPosition(4, 4)
		self.innerLine.SetSize(MODE_CARD_WIDTH - 8, MODE_CARD_HEIGHT - 8)
		self.innerLine.SetColor(_SignedColor(0xff40241b))
		self.innerLine.AddFlag("not_pick")
		self.innerLine.Show()
		self.fill = ui.Bar()
		self.fill.SetParent(self)
		self.fill.SetPosition(5, 5)
		self.fill.SetSize(MODE_CARD_WIDTH - 10, MODE_CARD_HEIGHT - 10)
		self.fill.AddFlag("not_pick")
		self.fill.Show()
		self.accent = ui.Bar()
		self.accent.SetParent(self)
		self.accent.SetPosition(1, 1)
		self.accent.SetSize(3, MODE_CARD_HEIGHT - 2)
		self.accent.AddFlag("not_pick")
		self.accent.Show()
		self.icon = owner._Image(self, 2, 8,
			ASSET + "mode_numeric_%dv%d_80.png" % (mode, mode))
		self.icon.SetScale(0.775, 0.775)
		self.title = owner._Label(self, 65, 15, _ModeTitle(mode), WHITE)
		self.subtitle = owner._Label(self, 65, 34,
			"Sólo" if mode == 1 else "Sólo nebo skupina", DIM)
		self.queue = owner._Label(self, 65, 69, "Globální fronta", MUTED)
		self.eta = owner._Label(self, 200, 69, "", GOLD, "right")
		self.selectedState = None
		self.Refresh(False)
		self.Show()

	def Refresh(self, selected):
		selected = bool(selected)
		if selected == self.selectedState:
			return
		self.selectedState = selected
		self.fill.SetColor(MODE_CARD_SELECTED if selected else MODE_CARD_NORMAL)
		self.accent.SetColor(
			_SignedColor(0xffd91e3a) if selected else _SignedColor(0xff39231d))
		self.title.SetPackedFontColor(GOLD if selected else WHITE)

	def OnMouseLeftButtonUp(self):
		if self.IsIn():
			self.owner.SelectMode(self.mode)


class PvPRulesDialog(ui.ScriptWindow):
	DIALOG_WIDTH = 520
	DIALOG_HEIGHT = 238

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.SetSize(self.DIALOG_WIDTH, self.DIALOG_HEIGHT)
		self.AddFlag("float")
		self.AddFlag("movable")
		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetPosition(0, 0)
		self.board.SetSize(self.DIALOG_WIDTH, self.DIALOG_HEIGHT)
		self.board.SetTitleName("PRAVIDLA A TRESTY")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.Show()
		self.__Label(260, 46, "BO3  •  nejvýše 3 minuty na kolo", WHITE)
		self.__Label(260, 72,
			"1v1 sólo  •  2v2 a 3v3 sólo nebo skupina", DIM)
		self.__Label(260, 104,
			"Odmítnutí nebo neodpovězení: 30 sekund, 2 minuty,", GOLD)
		self.__Label(260, 126, "5 minut, 15 minut", GOLD)
		self.__Label(260, 154,
			"Po 24 hodinách bez dalšího prohřešku začíná trest znovu na 30 sekund.",
			DIM)
		self.closeButton = ui.Button()
		self.closeButton.SetParent(self.board)
		self.closeButton.SetPosition((self.DIALOG_WIDTH - 137) // 2, 190)
		self.closeButton.SetSize(137, 31)
		uicrimsoncontrols.ApplyVisuals(self.closeButton, "137x31")
		self.closeButton.SetText("ZAVŘÍT")
		self.closeButton.SetEvent(ui.__mem_func__(self.Close))
		self.closeButton.Show()
		self.Hide()

	def __Label(self, x, y, text, color):
		label = ui.TextLine()
		label.SetParent(self.board)
		label.SetPosition(x, y)
		label.SetHorizontalAlignCenter()
		label.SetText(text)
		label.SetPackedFontColor(color)
		label.SetOutline()
		label.AddFlag("not_pick")
		label.Show()
		return label

	def Open(self):
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()

	def Destroy(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class PvPMatchmakingWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.mode = 2
		self.activeTab = "play"
		self.widgets = []
		self.tabWidgets = []
		self.tabButtons = {}
		self.lastRefresh = 0.0
		self.lastDataRequest = 0.0
		self.requestHistoryAfterSnapshot = False
		self.localError = ""
		self.playRenderState = None
		self.__Build()
		self.rulesDialog = PvPRulesDialog()
		self.readyWindow = PvPReadyWindow()
		self.matchHud = PvPMatchHud()

	def __Build(self):
		self.SetSize(WIDTH, WINDOW_HEIGHT)
		self.SetCenterPosition()
		self.AddFlag("movable")
		self.AddFlag("float")
		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetPosition(0, 0)
		self.board.SetSize(WIDTH, WINDOW_HEIGHT)
		self.board.SetTitleName(_Text("PVP_MATCHMAKING_TITLE", "Hodnocená aréna"))
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.Show()
		self.body = ui.Window()
		self.body.SetParent(self.board)
		self.body.SetPosition(CONTENT_X, CONTENT_Y)
		self.body.SetSize(CONTENT_WIDTH, CONTENT_HEIGHT)
		self.body.Show()
		self.surface = _PassiveBar(self.body, 0, 0,
			CONTENT_WIDTH, CONTENT_HEIGHT, PANEL_FILL)
		self.widgets.append(self.surface)
		self.__BuildTabs()
		self.__ShowTab("play")
		self.Hide()

	def _Image(self, parent, x, y, path, track=True):
		image = ui.ExpandedImageBox()
		image.SetParent(parent)
		image.SetPosition(x, y)
		image.LoadImage(path)
		image.AddFlag("not_pick")
		image.Show()
		if track:
			self.widgets.append(image)
		return image

	def _Label(self, parent, x, y, text="", color=WHITE, align="left"):
		label = ui.TextLine()
		label.SetParent(parent)
		label.SetPosition(x, y)
		label.SetText(text)
		label.SetPackedFontColor(color)
		label.SetOutline()
		if align == "center":
			label.SetHorizontalAlignCenter()
		elif align == "right":
			label.SetHorizontalAlignRight()
		label.AddFlag("not_pick")
		label.Show()
		self.widgets.append(label)
		return label

	def _Button(self, parent, x, y, text, event, prefix=None,
			width=137, height=31, family=None, radio=False):
		button = ui.RadioButton() if radio else ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetSize(width, height)
		if family:
			uicrimsoncontrols.ApplyVisuals(button, family)
			if radio:
				button.SetDownVisual(uicrimsoncontrols.Visual(family, "selected"))
		else:
			button.SetUpVisual(prefix + "_normal.png")
			button.SetOverVisual(prefix + "_hover.png")
			button.SetDownVisual(prefix + "_pressed.png")
			try:
				button.SetDisableVisual(prefix + "_disabled.png")
			except:
				pass
		button.SetText(text)
		button.SetEvent(event)
		button.Show()
		self.widgets.append(button)
		return button

	def _Panel(self, x, y, width, height):
		panel = _LayeredPanel(self.body, x, y, width, height)
		self.widgets.append(panel)
		return panel

	def _Header(self, x, y, width, text):
		header = _SectionHeader(self, self.body, x, y, width, text)
		self.widgets.append(header)
		return header

	def _StatRow(self, parent, x, y, width, label, value, accent=GOLD,
			height=27):
		row = _StatRow(self, parent, x, y, width, label, value, accent, height)
		self.widgets.append(row)
		return row

	def _Separator(self, x, y, width):
		line = _PassiveBar(
			self.body, x, y, width, 1, _SignedColor(0xff5e3422))
		shadow = _PassiveBar(
			self.body, x, y + 1, width, 1, _SignedColor(0xff100b0a))
		self.widgets.extend((line, shadow))
		return line

	def __SetLabel(self, label, text, color=None):
		state = (text, color)
		if getattr(label, "pvpRenderState", None) == state:
			return
		label.SetText(text)
		if color is not None:
			label.SetPackedFontColor(color)
		label.pvpRenderState = state

	def __SetButton(self, button, text, enabled):
		state = (text, bool(enabled))
		if getattr(button, "pvpRenderState", None) == state:
			return
		button.SetText(text)
		if enabled:
			button.Enable()
		else:
			button.Disable()
		button.pvpRenderState = state

	def __BuildTabs(self):
		for x, key, label in ((196, "play", "HRÁT"),
			(342, "leaderboard", "ŽEBŘÍČEK"), (488, "history", "HISTORIE")):
			button = self._Button(self.body, x, 12, label,
				lambda value=key: self.__SelectTab(value),
				family="137x31", radio=True)
			self.tabWidgets.append(button)
			self.tabButtons[key] = button

	def __RefreshTabButtons(self):
		for key, button in self.tabButtons.items():
			if key == self.activeTab:
				button.Down()
			else:
				button.SetUp()

	def __ClearContent(self):
		for widget in self.widgets[len(self.tabWidgets) + 1:]:
			try:
				widget.Hide()
			except:
				pass
		self.widgets = [self.surface] + self.tabWidgets[:]
		self.playRenderState = None

	def __SelectTab(self, tab):
		self.__ShowTab(tab)

	def __OpenHistory(self):
		self.__SelectTab("history")

	def __OpenRules(self):
		self.rulesDialog.Open()

	def __ShowTab(self, tab, requestData=True):
		self.activeTab = tab
		self.__RefreshTabButtons()
		self.__ClearContent()
		if tab == "play":
			self.__BuildPlay()
		elif tab == "leaderboard":
			self.__BuildLeaderboard()
		else:
			self.__BuildHistory()
		if requestData:
			self.__RequestTabData()

	def __RequestTabData(self):
		if not pvpmatchmaking.IsAvailable():
			return False
		if self.activeTab == "play":
			sent = net.SendPvPMatchmakingSnapshot()
			if sent:
				self.requestHistoryAfterSnapshot = True
		elif self.activeTab == "leaderboard":
			sent = net.SendPvPMatchmakingLeaderboard(self.mode, 0, 0)
		else:
			sent = net.SendPvPMatchmakingHistory(self.mode, 0)
		if sent:
			self.lastDataRequest = app.GetTime()
		return sent

	def SelectMode(self, mode):
		self.mode = int(mode)
		if self.activeTab == "play":
			for card in getattr(self, "modeCards", []):
				card.Refresh(card.mode == self.mode)
			self.playRenderState = None
			self.__RefreshPlayData()
			self.__RequestTabData()
		else:
			self.__ShowTab(self.activeTab)

	def __BuildPlay(self):
		queue = tuple(pvpmatchmaking.GetQueue())
		if int(queue[0]) != pvpmatchmaking.QUEUE_IDLE and int(queue[1]) in (1, 2, 3):
			self.mode = int(queue[1])
		self._Panel(*PLAY_LEFT)
		self._Panel(*PLAY_CENTER)
		self._Panel(*PLAY_RIGHT)
		self._Header(PLAY_LEFT[0], PLAY_LEFT[1], PLAY_LEFT[2], "VYBER REŽIM")
		self.rankHeader = self._Header(
			PLAY_CENTER[0], PLAY_CENTER[1], PLAY_CENTER[2],
			"TVŮJ RANK — %s" % _ModeName(self.mode))
		self.seasonHeader = self._Header(
			PLAY_RIGHT[0], PLAY_RIGHT[1], PLAY_RIGHT[2], "SEZÓNA 0")
		self.modeCards = []
		for mode, y in ((1, 91), (2, 190), (3, 289)):
			card = _ModeCard(self, mode, y)
			card.Refresh(mode == self.mode)
			self.modeCards.append(card)
			self.widgets.append(card)
		self._Label(self.body, 120, 401,
			"Maximální level  •  běžná výbava", MUTED, "center")
		self._Label(self.body, 120, 421,
			"BO3  •  3 minuty na kolo", DIM, "center")
		self.rulesLink = _TextLink(self.body, 35, 444, 170, 24,
			"?  PRAVIDLA A TRESTY", ui.__mem_func__(self.__OpenRules))
		self.widgets.append(self.rulesLink)

		self.rankCrest = self._Image(
			self.body, 334, 88, ASSET + "rank_zlato_148.png")
		self.rankAssetPath = ASSET + "rank_zlato_148.png"
		self.rankNameLabel = self._Label(self.body, 407, 244, "", GOLD, "center")
		self.ratingLabel = self._Label(self.body, 407, 270, "", WHITE, "center")
		self.nextRankLabel = self._Label(self.body, 260, 301, "", DIM)
		self.nextRatingLabel = self._Label(self.body, 555, 301, "", GOLD, "right")
		self.rankTrack = _PassiveBar(self.body, 260, 312, 295, 10, PANEL_BORDER)
		self.rankTrackInner = _PassiveBar(
			self.body, 261, 313, 293, 8, _SignedColor(0xff050505))
		self.rankFill = _PassiveBar(
			self.body, 262, 314, 1, 6, _SignedColor(0xffb51936))
		self.widgets.extend((self.rankTrack, self.rankTrackInner, self.rankFill))
		self.rankFillWidth = 1
		self.rankDistanceLabel = self._Label(self.body, 407, 339, "", DIM, "center")
		self._Separator(254, 355, 307)
		self.statusLabel = self._Label(self.body, 407, 372, "", GREEN, "center")
		self.queueButton = self._Button(
			self.body, QUEUE_ACTION[0], QUEUE_ACTION[1], "VSTOUPIT DO FRONTY",
			self.__ToggleQueue, DUNGEON + "button/enter_196x36",
			QUEUE_ACTION[2], QUEUE_ACTION[3])
		self._Label(self.body, 407, 453,
			"Při hledání můžeš okno zavřít.", MUTED, "center")

		self.currentSeasonLabel = self._Label(
			self.body, 598, 94, "AKTUÁLNÍ SEZÓNA", GOLD)
		self.seasonDaysLabel = self._Label(self.body, 798, 94, "", DIM, "right")
		self.seasonTrack = _PassiveBar(self.body, 598, 109, 200, 8, PANEL_BORDER)
		self.seasonTrackInner = _PassiveBar(
			self.body, 599, 110, 198, 6, _SignedColor(0xff050505))
		self.seasonFill = _PassiveBar(
			self.body, 600, 111, 1, 4, _SignedColor(0xff825622))
		self.widgets.extend((self.seasonTrack, self.seasonTrackInner, self.seasonFill))
		self.seasonFillWidth = 1
		self.personalStatsLabel = self._Label(
			self.body, 598, 133, "", GOLD)
		self.playStatRows = {
			"record": self._StatRow(self.body, 598, 148, 200,
				"Výhry / prohry", "0 / 0", GREEN),
			"winrate": self._StatRow(self.body, 598, 179, 200,
				"Úspěšnost", "0 %", GOLD),
			"best": self._StatRow(self.body, 598, 210, 200,
				"Nejvyšší Elo", "0", AMBER),
			"streak": self._StatRow(self.body, 598, 241, 200,
				"Série", "0", RED),
		}
		self._Label(self.body, 598, 292, "TVOJE HODNOCENÍ", GOLD)
		self.playRatingRows = {
			"position": self._StatRow(self.body, 598, 307, 200,
				"Pořadí serveru", "—", GOLD, 30),
			"played": self._StatRow(self.body, 598, 341, 200,
				"Odehrané zápasy", "0", BLUE, 30),
		}
		self._Separator(598, 387, 200)
		self._Label(self.body, 598, 405, "Poslední zápas", DIM)
		self.lastDeltaLabel = self._Label(self.body, 798, 405, "—", MUTED, "right")
		self.lastOutcomeLabel = self._Label(self.body, 598, 426, "—", WHITE)
		self.lastWhenLabel = self._Label(self.body, 798, 426, "", MUTED, "right")
		self.historyLink = _TextLink(self.body, 620, 449, 156, 24,
			"Zobrazit historii  ›", ui.__mem_func__(self.__OpenHistory))
		self.widgets.append(self.historyLink)
		self.playRenderState = None
		self.__RefreshPlayData()

	def __RefreshPlayData(self):
		if self.activeTab != "play" or not getattr(self, "queueButton", None):
			return
		queue = tuple(pvpmatchmaking.GetQueue())
		queueStatus = int(queue[0])
		if queueStatus != pvpmatchmaking.QUEUE_IDLE and int(queue[1]) in (1, 2, 3):
			self.mode = int(queue[1])
		stats = tuple(pvpmatchmaking.GetModeStats(self.mode))
		rating, best, wins, losses, draws, winStreak, completedMatches, position, placement = stats[1:]
		snapshot = tuple(pvpmatchmaking.GetSnapshot())
		seasonId, seasonEnds = int(snapshot[0]), int(snapshot[1])
		days = max(0, (seasonEnds - app.GetGlobalTimeStamp()) // 86400) if seasonEnds else 0
		error = tuple(pvpmatchmaking.GetError())
		errorText = _ErrorText(error)
		commandPending = _IsCommandPending()
		cooldownRemaining = max(0, int(queue[4]))
		cooldownStatus, cooldownColor, cooldownAllowsQueue = \
			_QueueCooldownPresentation(cooldownRemaining)
		result = tuple(pvpmatchmaking.GetResult())
		history = tuple(pvpmatchmaking.GetHistory())
		state = (self.mode, queue, stats, snapshot, error, commandPending,
			self.localError, result, history, days)
		if state == self.playRenderState:
			return
		self.playRenderState = state

		for card in self.modeCards:
			card.Refresh(card.mode == self.mode)
		self.rankHeader.SetText("TVŮJ RANK — %s" % _ModeName(self.mode))
		self.seasonHeader.SetText("SEZÓNA %d" % seasonId)
		rankAsset, rankName, nextRating = _Rank(rating)
		rankPath = ASSET + "rank_%s_148.png" % rankAsset
		if rankPath != self.rankAssetPath:
			self.rankCrest.LoadImage(rankPath)
			self.rankAssetPath = rankPath
		self.__SetLabel(self.rankNameLabel, rankName, GOLD)
		self.__SetLabel(self.ratingLabel, "%s ELO" % _Format(rating), WHITE)
		if nextRating:
			previous = {900: 100, 1200: 900, 1350: 1200, 1500: 1350,
				1600: 1500, 1800: 1600, 2000: 1800}.get(nextRating, 100)
			ratio = float(max(0, rating - previous)) / max(1, nextRating - previous)
			self.__SetLabel(self.nextRankLabel, rankName.split(" ")[0], DIM)
			self.__SetLabel(self.nextRatingLabel, _Format(nextRating), GOLD)
			self.__SetLabel(self.rankDistanceLabel,
				"%d bodů do dalšího ranku" % max(0, nextRating - rating), DIM)
		else:
			ratio = 1.0
			self.__SetLabel(self.nextRankLabel, "MAXIMUM", GOLD)
			self.__SetLabel(self.nextRatingLabel, "", GOLD)
			self.__SetLabel(self.rankDistanceLabel, "Nejvyšší dosažený rank", GOLD)
		fillWidth = max(1, min(291, int(round(291.0 * ratio))))
		if fillWidth != self.rankFillWidth:
			self.rankFill.SetSize(fillWidth, 6)
			self.rankFillWidth = fillWidth

		status = "PŘIPRAVEN NA HLEDÁNÍ"
		statusColor = GREEN
		if not pvpmatchmaking.IsAvailable():
			status = "ČEKÁM NA KOMPATIBILNÍ SERVER"
			statusColor = RED
		elif commandPending:
			status = ("RUŠÍM HLEDÁNÍ…" if queueStatus == pvpmatchmaking.QUEUE_SEARCHING
				else "PŘIPOJUJI DO FRONTY…")
			statusColor = AMBER
		elif queueStatus == pvpmatchmaking.QUEUE_COOLDOWN and cooldownRemaining > 0:
			status = cooldownStatus
			statusColor = cooldownColor
		elif self.localError:
			status = self.localError
			statusColor = RED
		elif errorText and queueStatus not in (
				pvpmatchmaking.QUEUE_SEARCHING, pvpmatchmaking.QUEUE_MATCH,
				pvpmatchmaking.QUEUE_COOLDOWN):
			status = errorText
			statusColor = RED
		elif queueStatus == pvpmatchmaking.QUEUE_SEARCHING:
			status = "HLEDÁM SOUPEŘE — %02d:%02d" % (
				int(queue[2]) // 60, int(queue[2]) % 60)
			statusColor = GREEN
		elif queueStatus == pvpmatchmaking.QUEUE_COOLDOWN and cooldownRemaining <= 0:
			status = cooldownStatus
			statusColor = cooldownColor
		self.__SetLabel(self.statusLabel, status, statusColor)
		buttonText = ("ZRUŠIT HLEDÁNÍ" if queueStatus == pvpmatchmaking.QUEUE_SEARCHING
			else "VSTOUPIT DO FRONTY")
		if commandPending:
			buttonText = ("RUŠÍM…" if queueStatus == pvpmatchmaking.QUEUE_SEARCHING
				else "PŘIPOJUJI…")
		buttonEnabled = (not commandPending and pvpmatchmaking.IsAvailable() and
			queueStatus not in (2, 3) and
			(queueStatus != pvpmatchmaking.QUEUE_COOLDOWN or cooldownAllowsQueue))
		self.__SetButton(self.queueButton, buttonText, buttonEnabled)

		self.__SetLabel(self.seasonDaysLabel, "zbývá %d dnů" % days, DIM)
		seasonRatio = max(0.0, min(1.0, float(90 - min(90, days)) / 90.0))
		seasonWidth = max(1, min(196, int(round(196.0 * seasonRatio))))
		if seasonWidth != self.seasonFillWidth:
			self.seasonFill.SetSize(seasonWidth, 4)
			self.seasonFillWidth = seasonWidth
		self.__SetLabel(self.personalStatsLabel,
			"OSOBNÍ STATISTIKY — %s" % _ModeName(self.mode), GOLD)
		played = completedMatches
		winrate = int(round(float(wins) * 100.0 / played)) if played else 0
		self.playStatRows["record"].SetValue("%d / %d" % (wins, losses))
		self.playStatRows["winrate"].SetValue("%d %%" % winrate)
		self.playStatRows["best"].SetValue(_Format(best))
		self.playStatRows["streak"].SetValue("%d výher" % winStreak)
		self.playRatingRows["position"].SetValue(
			"#%d" % position if position else "—")
		self.playRatingRows["played"].SetValue(str(played))

		lastOutcome = int(result[1]) if int(result[7]) else 0
		lastDelta = int(result[6]) if int(result[7]) else 0
		lastScoreO = int(result[2]) if int(result[7]) else 0
		lastScoreX = int(result[3]) if int(result[7]) else 0
		if not lastOutcome and int(history[3]) and int(history[0]) == self.mode and int(history[2]):
			last = tuple(pvpmatchmaking.GetHistoryRow(0))
			lastOutcome = int(last[2])
			lastScoreO, lastScoreX = int(last[3]), int(last[4])
			lastDelta = int(last[7])
		outcomeText, outcomeColor = _PersonalOutcome(lastOutcome, lastDelta)
		if not lastOutcome:
			outcomeText, outcomeColor = "—", MUTED
		if lastOutcome in (1, 2, 3):
			outcomeText += "  %d : %d" % (lastScoreO, lastScoreX)
		deltaText = "%+d ELO" % lastDelta if lastOutcome else "—"
		deltaColor = GREEN if lastDelta > 0 else (RED if lastDelta < 0 else MUTED)
		self.__SetLabel(self.lastOutcomeLabel, outcomeText, outcomeColor)
		self.__SetLabel(self.lastDeltaLabel, deltaText, deltaColor)

	def __ToggleQueue(self):
		if _IsCommandPending():
			return
		mainVid = player.GetMainCharacterIndex()
		if player.IsPartyMember(mainVid) and not player.IsPartyLeader(mainVid):
			self.localError = "FRONTU MŮŽE SPUSTIT JEN VŮDCE SKUPINY"
			self.playRenderState = None
			self.__RefreshPlayData()
			return
		self.localError = ""
		queue = tuple(pvpmatchmaking.GetQueue())
		if int(queue[0]) == pvpmatchmaking.QUEUE_SEARCHING:
			sent = net.SendPvPMatchmakingCancel()
		else:
			sent = net.SendPvPMatchmakingQueue(self.mode)
		if sent:
			self.playRenderState = None
			self.__RefreshPlayData()

	def __BuildLeaderboard(self):
		self._Panel(*LEADERBOARD_SIDE)
		self._Panel(*LEADERBOARD_TABLE)
		self._Header(LEADERBOARD_SIDE[0], LEADERBOARD_SIDE[1],
			LEADERBOARD_SIDE[2], "TVŮJ RANK")
		snapshot = tuple(pvpmatchmaking.GetSnapshot())
		seasonId = int(snapshot[0])
		self._Header(LEADERBOARD_TABLE[0], LEADERBOARD_TABLE[1],
			LEADERBOARD_TABLE[2], "ŽEBŘÍČEK SEZÓNY %d" % seasonId)
		stats = tuple(pvpmatchmaking.GetModeStats(self.mode))
		rankAsset, rankName, unused = _Rank(stats[1])
		icon = self._Image(self.body, 59, 89, ASSET + "rank_%s_128.png" % rankAsset)
		icon.SetScale(0.88, 0.88)
		self._Label(self.body, 115, 204, rankName, GOLD, "center")
		self._Label(self.body, 115, 227, "%s ELO" % _Format(stats[1]), WHITE, "center")
		self._StatRow(self.body, 22, 248, 186, "Pořadí",
			"#%d" % stats[8] if stats[8] else "—", GOLD, 28)
		self._StatRow(self.body, 22, 280, 186, "Výhry / prohry",
			"%d / %d" % (stats[3], stats[4]), GREEN, 28)
		self._StatRow(self.body, 22, 312, 186, "Nejvyšší Elo",
			_Format(stats[2]), AMBER, 28)
		self._Label(self.body, 22, 365, "REŽIM", GOLD)
		for mode, x in ((1, 22), (2, 84), (3, 146)):
			button = self._Button(self.body, x, 382, _ModeName(mode),
				lambda value=mode: self.SelectMode(value),
				width=61, height=21, family="61x21", radio=True)
			if mode == self.mode:
				button.Down()
		seasonDays = (max(0, (int(snapshot[1]) - app.GetGlobalTimeStamp()) // 86400)
			if seasonId and int(snapshot[1]) else 0)
		self._Label(self.body, 115, 443, "Sezóna končí za %d dnů" % seasonDays,
			MUTED, "center")
		headerRow = _PassiveBar(
			self.body, 238, 91, 567, 29, _SignedColor(0xff160b0c))
		self.widgets.append(headerRow)
		for x, label, align in zip(LEADERBOARD_COLUMNS,
			("#", "RANK", "HRÁČ", "ELO", "V–P", "FORMA"),
			("center", "center", "left", "left", "left", "center")):
			self._Label(self.body, x, 100, label, GOLD, align)
		board = tuple(pvpmatchmaking.GetLeaderboard())
		boardValid = int(board[3]) and int(board[0]) == self.mode
		rowCount = int(board[2]) if boardValid else 0
		for index in range(min(8, rowCount)):
			row = tuple(pvpmatchmaking.GetLeaderboardRow(index))
			y = 124 + index * 41
			bar = ui.Bar()
			bar.SetParent(self.body)
			bar.SetPosition(238, y)
			bar.SetSize(567, 39)
			bar.SetColor(
				_SignedColor(0xff080707) if index % 2 == 0
				else _SignedColor(0xff0d0909))
			bar.AddFlag("not_pick")
			bar.Show()
			self.widgets.append(bar)
			self._Label(self.body, 252, y + 13, str(row[0]),
				GOLD if index < 3 else DIM, "center")
			rowRankAsset = _Rank(row[2])[0]
			rankIcon = self._Image(self.body, 270, y + 3,
				ASSET + "rank_%s_128.png" % rowRankAsset)
			rankIcon.SetScale(0.25, 0.25)
			self._Label(self.body, 330, y + 13, row[5], WHITE)
			self._Label(self.body, 650, y + 13, _Format(row[2]), GOLD)
			self._Label(self.body, 720, y + 13,
				"%d–%d" % (row[3], row[4]), WHITE)
			form = int(row[3]) - int(row[4])
			self._Label(self.body, 790, y + 13, "%+d" % form,
				GREEN if form > 0 else (RED if form < 0 else MUTED), "center")
		if rowCount == 0:
			errorText = _ErrorText(tuple(pvpmatchmaking.GetError()))
			message = errorText or ("V žebříčku zatím nikdo není." if boardValid else "Žebříček se načítá…")
			self._Label(self.body, 522, 270, message,
				RED if errorText else DIM, "center")

	def __BuildHistory(self):
		self._Panel(*HISTORY_TABLE)
		self._Header(HISTORY_TABLE[0], HISTORY_TABLE[1], HISTORY_TABLE[2],
			"HISTORIE ZÁPASŮ — %s" % _ModeName(self.mode))
		for mode, x in ((1, 28), (2, 93), (3, 158)):
			button = self._Button(self.body, x, 92, _ModeName(mode),
				lambda value=mode: self.SelectMode(value),
				width=61, height=21, family="61x21", radio=True)
			if mode == self.mode:
				button.Down()
		self._Label(self.body, 34, 133, "DATUM", DIM)
		self._Label(self.body, 166, 133, "VÝSLEDEK", DIM)
		self._Label(self.body, 350, 133, "SKÓRE", DIM)
		self._Label(self.body, 510, 133, "ELO", DIM)
		self._Label(self.body, 798, 133, "ZMĚNA", DIM, "right")
		history = tuple(pvpmatchmaking.GetHistory())
		historyValid = int(history[3]) and int(history[0]) == self.mode
		rowCount = int(history[2]) if historyValid else 0
		for index in range(min(10, rowCount)):
			row = tuple(pvpmatchmaking.GetHistoryRow(index))
			y = 164 + index * 29
			outcome, outcomeColor = _PersonalOutcome(row[2], row[7])
			self._Label(self.body, 34, y, str(row[1]), DIM)
			self._Label(self.body, 166, y, outcome, outcomeColor)
			self._Label(self.body, 350, y, "%d : %d" % (row[3], row[4]), WHITE)
			self._Label(self.body, 510, y, "%s → %s" % (_Format(row[5]), _Format(row[6])), WHITE)
			self._Label(self.body, 798, y, "%+d" % int(row[7]),
				GREEN if int(row[7]) > 0 else (RED if int(row[7]) < 0 else MUTED),
				"right")
		if rowCount == 0:
			errorText = _ErrorText(tuple(pvpmatchmaking.GetError()))
			message = errorText or ("Zatím tu nejsou žádné hodnocené zápasy." if historyValid else "Historie se načítá…")
			self._Label(self.body, 430, 270, message, RED if errorText else DIM, "center")

	def OnServerChanged(self):
		self.localError = ""
		if self.IsShow():
			if self.activeTab == "play":
				self.playRenderState = None
				self.__RefreshPlayData()
				if self.requestHistoryAfterSnapshot:
					if net.SendPvPMatchmakingHistory(self.mode, 0):
						self.requestHistoryAfterSnapshot = False
						self.lastDataRequest = app.GetTime()
			elif self.activeTab in ("leaderboard", "history"):
				self.__ShowTab(self.activeTab, False)
		self.readyWindow.Refresh()
		self.matchHud.Refresh()

	def Show(self):
		ui.ScriptWindow.Show(self)
		self.SetTop()
		self.__ShowTab(self.activeTab)

	def Close(self):
		self.rulesDialog.Close()
		self.Hide()

	def Destroy(self):
		self.rulesDialog.Destroy()
		self.readyWindow.Destroy()
		self.matchHud.Destroy()
		self.widgets = []
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		now = app.GetTime()
		if now - self.lastRefresh >= 1.0:
			self.lastRefresh = now
			if self.IsShow() and self.activeTab == "play":
				self.__RefreshPlayData()
			if self.IsShow() and now - self.lastDataRequest >= 5.0:
				self.__RequestTabData()
			self.readyWindow.Refresh()
			self.matchHud.Refresh()


class PvPReadyWindow(ui.ScriptWindow):
	READY_WIDTH = 480
	READY_HEIGHT = 350

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.readyId = 0
		self.accepted = False
		self.declining = False
		self.pendingDecision = None
		self.lastRefresh = 0.0
		self.widgets = []
		self.timerPath = None
		self.dotPaths = []
		self.labelStates = [None] * 6
		self.summaryText = ""
		self.modePath = None
		self.buttonStates = {}
		self.SetSize(self.READY_WIDTH, self.READY_HEIGHT)
		self.SetCenterPosition()
		self.AddFlag("float")
		self.AddFlag("movable")
		self.board = ui.Window()
		self.board.SetParent(self)
		self.board.SetSize(self.READY_WIDTH, self.READY_HEIGHT)
		self.board.AddFlag("not_pick")
		self.board.Show()
		self.__Bar(0, 0, self.READY_WIDTH, self.READY_HEIGHT,
			_SignedColor(0xff6f3e27))
		self.__Bar(1, 1, self.READY_WIDTH - 2, self.READY_HEIGHT - 2,
			_SignedColor(0xff050404))
		self.__Bar(4, 4, self.READY_WIDTH - 8, self.READY_HEIGHT - 8,
			_SignedColor(0xff1f1411))
		self.__Bar(5, 5, self.READY_WIDTH - 10, self.READY_HEIGHT - 10,
			_SignedColor(0xff020202))
		self.__Header(9, 9, 462, "ZÁPAS NALEZEN", 49)
		self.modeIcon = self.__Image(14, 4, ASSET + "mode_numeric_1v1_80.png")
		self.modeIcon.SetScale(0.45, 0.45)
		self.modePath = ASSET + "mode_numeric_1v1_80.png"
		self.dragHeader = self.__AttachRegion(9, 9, 462, 28)
		self.timer = self.__Image(182, 61, ASSET + "timer/timer_15.png")
		self.timerPath = ASSET + "timer/timer_15.png"
		self.readyDots = []
		for index in range(6):
			x = 209 + index * 12
			dot = self.__Image(x, 181,
				ASSET + "ready_participant_empty_8.png")
			self.readyDots.append(dot)
			self.dotPaths.append(ASSET + "ready_participant_empty_8.png")
		self.title = self.__Label(240, 53, "POTVRĎ ÚČAST", WHITE, "center")
		self.summary = self.__Label(240, 201, "", DIM, "center")
		self.__Label(109, 219, "TÝM O", GOLD, "center")
		self.__Label(371, 219, "TÝM X", RED, "center")
		self.left = [self.__ParticipantRow(30, 231 + index * 26)
			for index in range(3)]
		self.right = [self.__ParticipantRow(292, 231 + index * 26)
			for index in range(3)]
		self.__Label(240, 264, "VS", RED, "center")
		self.decline = self.__Button(112, 318, "ODMÍTNOUT", self.__Decline,
			None, 100, 21, "100x21")
		self.accept = self.__Button(222, 311, "PŘIJMOUT", self.__Accept,
			ASSET + "ready/action_150x36", 150, 36)
		self.buttonStates["accept"] = ("PŘIJMOUT", True)
		self.buttonStates["decline"] = ("ODMÍTNOUT", True)
		self.Hide()

	def __Bar(self, x, y, width, height, color):
		bar = ui.Bar()
		bar.SetParent(self.board)
		bar.SetPosition(x, y)
		bar.SetSize(width, height)
		bar.SetColor(color)
		bar.AddFlag("not_pick")
		bar.Show()
		self.widgets.append(bar)
		return bar

	def __Image(self, x, y, path):
		image = ui.ExpandedImageBox()
		image.SetParent(self.board)
		image.SetPosition(x, y)
		image.LoadImage(path)
		image.AddFlag("not_pick")
		image.Show()
		self.widgets.append(image)
		return image

	def __AttachRegion(self, x, y, width, height):
		window = ui.Window()
		window.SetParent(self.board)
		window.SetPosition(x, y)
		window.SetSize(width, height)
		window.AddFlag("attach")
		window.Show()
		self.widgets.append(window)
		return window

	def __Header(self, x, y, width, text, labelInset=10):
		left = self.__Image(x, y, ASSET + "header/section_left_12x28.png")
		middle = self.__Image(x + 12, y,
			ASSET + "header/section_middle_260x28.png")
		middle.SetScale(float(width - 35) / 260.0, 1.0)
		self.__Image(x + width - 23, y,
			ASSET + "header/section_right_23x28.png")
		return self.__Label(x + labelInset, y + 7, text, GOLD)

	def __ParticipantRow(self, x, y):
		self.__Bar(x, y, 157, 23, _SignedColor(0xff472b1f))
		self.__Bar(x + 1, y + 1, 155, 21, _SignedColor(0xff090808))
		return self.__Label(x + 25, y + 6, "", DIM)

	def __Label(self, x, y, text, color, align="left"):
		label = ui.TextLine()
		label.SetParent(self.board)
		label.SetPosition(x, y)
		label.SetText(text)
		label.SetPackedFontColor(color)
		label.SetOutline()
		if align == "center":
			label.SetHorizontalAlignCenter()
		elif align == "right":
			label.SetHorizontalAlignRight()
		label.Show()
		return label

	def __Button(self, x, y, text, event, prefix, width, height, family=None):
		button = ui.Button()
		button.SetParent(self.board)
		button.SetPosition(x, y)
		button.SetSize(width, height)
		if family:
			uicrimsoncontrols.ApplyVisuals(button, family)
		else:
			button.SetUpVisual(prefix + "_normal.png")
			button.SetOverVisual(prefix + "_hover.png")
			button.SetDownVisual(prefix + "_pressed.png")
			try:
				button.SetDisableVisual(prefix + "_disabled.png")
			except:
				pass
		button.SetText(text)
		button.SetEvent(event)
		button.Show()
		return button

	def __SetButtonState(self, key, button, text, enabled):
		state = (text, enabled)
		if self.buttonStates.get(key) == state:
			return
		oldState = self.buttonStates.get(key)
		if not oldState or oldState[0] != text:
			button.SetText(text)
		if not oldState or oldState[1] != enabled:
			if enabled:
				button.Enable()
			else:
				button.Disable()
		self.buttonStates[key] = state

	def __SetLabelState(self, index, label, text, color):
		state = (text, color)
		if self.labelStates[index] == state:
			return
		oldState = self.labelStates[index]
		if not oldState or oldState[0] != text:
			label.SetText(text)
		if not oldState or oldState[1] != color:
			label.SetPackedFontColor(color)
		self.labelStates[index] = state

	def __TrySendDecision(self):
		if self.pendingDecision is None or _IsCommandPending():
			return
		ready = tuple(pvpmatchmaking.GetReady())
		if (not int(ready[0]) or int(ready[0]) != self.readyId or
			int(ready[2]) <= app.GetGlobalTimeStamp()):
			self.pendingDecision = None
			return
		decision = self.pendingDecision
		if net.SendPvPMatchmakingReady(self.readyId, decision):
			self.pendingDecision = None
			self.accepted = decision == 1
			self.declining = decision == 0

	def __ChooseDecision(self, decision):
		if (self.accepted or self.declining or
			self.pendingDecision is not None or not self.readyId):
			return
		self.pendingDecision = decision
		self.__TrySendDecision()
		self.Refresh()

	def Refresh(self):
		ready = tuple(pvpmatchmaking.GetReady())
		readyId = int(ready[0])
		if not readyId:
			self.Hide()
			self.readyId = 0
			self.accepted = False
			self.declining = False
			self.pendingDecision = None
			return
		if readyId != self.readyId:
			self.readyId = readyId
			self.accepted = False
			self.declining = False
			self.pendingDecision = None
			self.SetCenterPosition()
		modePath = ASSET + "mode_numeric_%dv%d_80.png" % (int(ready[1]), int(ready[1]))
		if modePath != self.modePath:
			self.modeIcon.LoadImage(modePath)
			self.modePath = modePath
		accepted = 0
		localReadyStatus = 0
		teamRows = {1: [], 2: []}
		for index in range(int(ready[3])):
			participant = tuple(pvpmatchmaking.GetReadyParticipant(index))
			accepted += 1 if int(participant[2]) == 1 else 0
			if participant[3] == player.GetName():
				localReadyStatus = int(participant[2])
			teamRows[int(participant[1])].append(participant)
		commandPending = _IsCommandPending()
		if localReadyStatus == 1:
			self.accepted = True
			self.declining = False
			self.pendingDecision = None
		elif localReadyStatus == 2:
			self.accepted = False
			self.declining = True
			self.pendingDecision = None
		elif not commandPending and self.pendingDecision is None:
			self.accepted = False
			self.declining = False
		remaining = max(0, min(15, int(ready[2]) - app.GetGlobalTimeStamp()))
		if not remaining and localReadyStatus == 0:
			self.pendingDecision = None
		timerPath = (ASSET + "timer/timer_%02d.png" % remaining
			if not self.accepted else ASSET + "timer/timer_accepted.png")
		if timerPath != self.timerPath:
			self.timer.LoadImage(timerPath)
			self.timerPath = timerPath
		for index, dot in enumerate(self.readyDots):
			team = 1 if index < 3 else 2
			rowIndex = index if index < 3 else index - 3
			if rowIndex < len(teamRows[team]):
				dotPath = ASSET + ("ready_participant_accepted_8.png" if int(teamRows[team][rowIndex][2]) == 1 else "ready_participant_waiting_8.png")
			else:
				dotPath = ASSET + "ready_participant_empty_8.png"
			if dotPath != self.dotPaths[index]:
				dot.LoadImage(dotPath)
				self.dotPaths[index] = dotPath
		for team, labels in ((1, self.left), (2, self.right)):
			for index, label in enumerate(labels):
				labelIndex = index if team == 1 else index + 3
				if index < len(teamRows[team]):
					row = teamRows[team][index]
					status = "PŘIJATO" if int(row[2]) == 1 else "ČEKÁ SE…"
					self.__SetLabelState(labelIndex, label,
						status,
						GREEN if int(row[2]) == 1 else GOLD)
				else:
					self.__SetLabelState(labelIndex, label, "", DIM)
		summaryText = "%d / %d PŘIPRAVENO" % (accepted, int(ready[3]))
		if summaryText != self.summaryText:
			self.summary.SetText(summaryText)
			self.summaryText = summaryText
		if self.accepted or self.pendingDecision == 1:
			self.__SetButtonState("accept", self.accept, "PŘESOUVÁM…", False)
			self.__SetButtonState("decline", self.decline, "ODMÍTNOUT", False)
		elif self.declining or self.pendingDecision == 0:
			self.__SetButtonState("accept", self.accept, "PŘIJMOUT", False)
			self.__SetButtonState("decline", self.decline, "ODCHÁZÍM…", False)
		else:
			self.__SetButtonState("accept", self.accept, "PŘIJMOUT", True)
			self.__SetButtonState("decline", self.decline, "ODMÍTNOUT", True)
		if not self.IsShow():
			ui.ScriptWindow.Show(self)
			self.SetTop()

	def __Accept(self):
		self.__ChooseDecision(1)

	def __Decline(self):
		self.__ChooseDecision(0)

	def Destroy(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.__Decline()
		return True

	def OnUpdate(self):
		now = app.GetTime()
		if now - self.lastRefresh >= 0.2:
			self.lastRefresh = now
			self.__TrySendDecision()
			self.Refresh()


class PvPMatchHud(ui.Window):
	HUD_WIDTH = 460
	HUD_HEIGHT = 72
	RESULT_PRESENTATION_SECONDS = 5.0

	def __init__(self):
		ui.Window.__init__(self)
		self.SetSize(self.HUD_WIDTH, self.HUD_HEIGHT)
		self.AddFlag("not_pick")
		self.lastRefresh = 0.0
		self.resultMatchId = 0
		self.resultUntil = 0.0
		self.cachedResult = None
		self.SetPosition((wndMgr.GetScreenWidth() - self.HUD_WIDTH) // 2, 24)

		self.background = self.__Image(0, 0,
			ASSET + "hud_shell_460x72.png")
		self.teamOIcon = self.__Image(16, 26,
			ASSET + "hud_team_o_20.png")
		self.teamXIcon = self.__Image(424, 26,
			ASSET + "hud_team_x_20.png")
		self.countdownRing = self.__Image(202, 8,
			ASSET + "hud_countdown_ring_56.png")
		self.countdownRing.Hide()

		self.teamO = self.__Label(66, 18, GOLD)
		self.teamO.SetText("TÝM O")
		self.scoreO = self.__Label(121, 29, WHITE)
		self.teamX = self.__Label(394, 18, RED)
		self.teamX.SetText("TÝM X")
		self.scoreX = self.__Label(339, 29, WHITE)
		self.status = self.__Label(230, 20, GOLD)
		self.clock = self.__Label(230, 39, WHITE)
		self.Hide()

	def __Image(self, x, y, filename):
		image = ui.ExpandedImageBox()
		image.SetParent(self)
		image.SetPosition(x, y)
		image.LoadImage(filename)
		image.AddFlag("not_pick")
		image.Show()
		return image

	def __Label(self, x, y, color):
		label = ui.TextLine()
		label.SetParent(self)
		label.SetPosition(x, y)
		label.SetHorizontalAlignCenter()
		label.SetPackedFontColor(color)
		label.SetOutline()
		label.AddFlag("not_pick")
		label.Show()
		return label

	def __SetScores(self, scoreO, scoreX):
		self.scoreO.SetText(str(max(0, int(scoreO))))
		self.scoreX.SetText(str(max(0, int(scoreX))))

	def __ShowMatch(self, match):
		roundNumber = max(1, min(3, int(match[3])))
		seconds = max(0, int(match[6]))
		combatActive = bool(int(match[7]))
		self.__SetScores(match[4], match[5])
		self.status.SetPackedFontColor(GOLD)
		self.clock.SetPackedFontColor(WHITE)

		if combatActive:
			self.countdownRing.Hide()
			self.status.SetPosition(230, 20)
			self.status.SetText("KOLO %d" % roundNumber)
			self.clock.SetPosition(230, 39)
			self.clock.SetText("%02d:%02d" % (seconds // 60, seconds % 60))
		elif seconds > 0:
			self.countdownRing.Show()
			self.status.SetPosition(230, 14)
			self.status.SetText("KOLO %d ZA" % roundNumber)
			self.clock.SetPosition(230, 34)
			self.clock.SetText(str(seconds))
		else:
			self.countdownRing.Hide()
			self.status.SetPosition(230, 29)
			self.status.SetText("ČEKÁ SE NA HRÁČE")
			self.clock.SetText("")

	def __ShowResult(self, result):
		self.__SetScores(result[2], result[3])
		self.countdownRing.Hide()
		self.status.SetPosition(230, 22)
		outcomeText, outcomeColor = _PersonalOutcome(result[1], result[6])
		self.status.SetText(outcomeText)
		self.status.SetPackedFontColor(outcomeColor)
		self.clock.SetPosition(230, 41)
		self.clock.SetPackedFontColor(WHITE)
		self.clock.SetText("ZÁPAS UKONČEN")

	def __ShowHud(self):
		self.SetPosition((wndMgr.GetScreenWidth() - self.HUD_WIDTH) // 2, 24)
		if not self.IsShow():
			self.Show()
		self.SetTop()

	def Refresh(self):
		now = app.GetTime()
		result = tuple(pvpmatchmaking.GetResult())
		if int(result[7]) and int(result[0]) and \
				int(result[0]) != self.resultMatchId:
			self.resultMatchId = int(result[0])
			self.cachedResult = result
			self.resultUntil = now + self.RESULT_PRESENTATION_SECONDS

		match = tuple(pvpmatchmaking.GetMatch())
		showResult = (self.cachedResult and now < self.resultUntil and
			(not int(match[8]) or int(match[0]) == int(self.cachedResult[0])))
		if showResult:
			self.__ShowResult(self.cachedResult)
			self.__ShowHud()
		elif int(match[8]) and (not self.cachedResult or
			int(match[0]) != int(self.cachedResult[0])):
			self.__ShowMatch(match)
			self.__ShowHud()
		else:
			self.Hide()

	def Destroy(self):
		self.cachedResult = None
		self.resultUntil = 0.0
		self.Hide()

	def OnUpdate(self):
		now = app.GetTime()
		if now - self.lastRefresh >= 0.2:
			self.lastRefresh = now
			self.Refresh()
