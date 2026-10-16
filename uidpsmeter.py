import app
import localeInfo
import player
import ui


def _Locale(name, fallback):
	return getattr(localeInfo, name, fallback)


def FormatCompactNumber(value):
	value = max(0, int(value))
	for divisor, suffix in ((1000000000000, "T"), (1000000000, "B"), (1000000, "M"), (1000, "K")):
		if value >= divisor:
			amount = float(value) / divisor
			if amount >= 100:
				return "%.0f%s" % (amount, suffix)
			if amount >= 10:
				return "%.1f%s" % (amount, suffix)
			return "%.2f%s" % (amount, suffix)
	return str(value)


class DpsMeterPanel(ui.ThinBoard):
	WIDTH = 320
	HEADER_HEIGHT = 22
	ROW_HEIGHT = 18
	FOOTER_PADDING = 5
	COMPACT_ROWS = 5
	MAXIMUM_ROWS = 20
	RESET_FLAG = 1

	RANK_X = 23
	PLAYER_X = 80
	DAMAGE_X = 166
	PERCENT_X = 232
	DPS_X = 286
	PLAYER_WIDTH = 96

	NORMAL_COLOR = 0xFFD8D8D8
	OWN_COLOR = 0xFFFFD35A
	HEADER_COLOR = 0xFFF0D9A0
	HEADER_BACKGROUND = 0x99251F19
	HEADER_DIVIDER_COLOR = 0xAA80663D
	ODD_ROW_COLOR = 0x221A1714
	EVEN_ROW_COLOR = 0x12231F1B
	OWN_ACCENT_COLOR = 0xFFE2A33A

	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEADER_HEIGHT)
		self.encounterId = 0
		self.snapshotRows = []
		self.totalDamage = 0
		self.expanded = False
		self.rowWidgets = []
		self.rowBars = []
		self.rowAccents = []

		self._MakeHeader()
		self._MakeRows()
		self.Hide()

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def _MakeText(self, text, x, y, color=None, align="left", limitWidth=0):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		line.SetText(text)
		line.SetOutline()
		if align == "right":
			line.SetHorizontalAlignRight()
		elif align == "center":
			line.SetHorizontalAlignCenter()
		if limitWidth > 0:
			line.SetLimitWidth(limitWidth)
		if color is not None:
			line.SetPackedFontColor(color)
		line.Show()
		return line

	def _MakeBar(self, x, y, width, height, color):
		bar = ui.Bar()
		bar.SetParent(self)
		bar.SetPosition(x, y)
		bar.SetSize(width, height)
		bar.SetColor(color)
		bar.AddFlag("not_pick")
		bar.Show()
		return bar

	def _MakeHeader(self):
		self.headerBar = self._MakeBar(5, 3, self.WIDTH - 10, 17, self.HEADER_BACKGROUND)
		self.headerDivider = self._MakeBar(7, 19, self.WIDTH - 14, 1, self.HEADER_DIVIDER_COLOR)

		# Native UI parents do not retain Python child wrappers. Keep the labels on
		# the panel so they cannot be garbage-collected after this method returns.
		self.headerWidgets = (
			self._MakeText(_Locale("DPS_METER_PLAYER", "Hrac"), self.PLAYER_X, 4, self.HEADER_COLOR, "center"),
			self._MakeText(_Locale("DPS_METER_DAMAGE", "DMG"), self.DAMAGE_X, 4, self.HEADER_COLOR, "center"),
			self._MakeText(_Locale("DPS_METER_PERCENT", "%"), self.PERCENT_X, 4, self.HEADER_COLOR, "center"),
			self._MakeText(_Locale("DPS_METER_DPS5", "DPS (5 s)"), self.DPS_X, 4, self.HEADER_COLOR, "center"),
		)

		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(6, 3)
		button.SetUpVisual("d:/ymir work/ui/public/small_thin_button_01.sub")
		button.SetOverVisual("d:/ymir work/ui/public/small_thin_button_02.sub")
		button.SetDownVisual("d:/ymir work/ui/public/small_thin_button_03.sub")
		button.SetText("+")
		button.SetEvent(ui.__mem_func__(self.ToggleExpanded))
		button.Show()
		self.expandButton = button

	def _MakeRows(self):
		for index in range(self.MAXIMUM_ROWS):
			y = self.HEADER_HEIGHT + index * self.ROW_HEIGHT
			rowBar = self._MakeBar(7, y, self.WIDTH - 14, self.ROW_HEIGHT - 1, self.ODD_ROW_COLOR)
			rowBar.Hide()
			self.rowBars.append(rowBar)
			rowAccent = self._MakeBar(9, y + 3, 2, self.ROW_HEIGHT - 7, self.OWN_ACCENT_COLOR)
			rowAccent.Hide()
			self.rowAccents.append(rowAccent)
			widgets = (
				self._MakeText("", self.RANK_X, y + 2, align="right"),
				self._MakeText("", self.PLAYER_X, y + 2, align="center", limitWidth=self.PLAYER_WIDTH),
				self._MakeText("", self.DAMAGE_X, y + 2, align="center"),
				self._MakeText("", self.PERCENT_X, y + 2, align="center"),
				self._MakeText("", self.DPS_X, y + 2, align="center"),
			)
			for widget in widgets:
				widget.Hide()
			self.rowWidgets.append(widgets)

	def Reset(self):
		self.encounterId = 0
		self.snapshotRows = []
		self.totalDamage = 0
		for rowBar, rowAccent, widgets in zip(self.rowBars, self.rowAccents, self.rowWidgets):
			rowBar.Hide()
			rowAccent.Hide()
			for widget in widgets:
				widget.Hide()
		self.Hide()

	def ApplySnapshot(self, victimVid, encounterId, flags, totalDamage, rows):
		if flags & self.RESET_FLAG:
			self.Reset()
			return

		if not rows:
			self.Reset()
			return

		self.encounterId = encounterId
		self.totalDamage = max(0, int(totalDamage))
		self.snapshotRows = list(rows[:self.MAXIMUM_ROWS])
		self._Refresh()
		self.Show()

	def ToggleExpanded(self):
		self.expanded = not self.expanded
		self.expandButton.SetText("-" if self.expanded else "+")
		self._Refresh()

	def _Refresh(self):
		visibleLimit = self.MAXIMUM_ROWS if self.expanded else self.COMPACT_ROWS
		visibleRows = min(len(self.snapshotRows), visibleLimit)
		mainVid = player.GetMainCharacterIndex()

		for index, widgets in enumerate(self.rowWidgets):
			rowBar = self.rowBars[index]
			rowAccent = self.rowAccents[index]
			if index >= visibleRows:
				rowBar.Hide()
				rowAccent.Hide()
				for widget in widgets:
					widget.Hide()
				continue

			attackerVid, attackerName, totalDamage, rollingDps = self.snapshotRows[index]
			percent = 0.0
			if self.totalDamage > 0:
				percent = float(totalDamage) * 100.0 / self.totalDamage
			isOwnRow = int(attackerVid) == mainVid
			color = self.OWN_COLOR if isOwnRow else self.NORMAL_COLOR
			rowBar.SetColor(self.EVEN_ROW_COLOR if index % 2 else self.ODD_ROW_COLOR)
			if visibleRows > 1:
				rowBar.Show()
			else:
				rowBar.Hide()
			rowAccent.Show() if isOwnRow else rowAccent.Hide()
			values = (
				"%d." % (index + 1),
				attackerName,
				FormatCompactNumber(totalDamage),
				"%.1f%%" % percent,
				FormatCompactNumber(rollingDps),
			)
			for widget, value in zip(widgets, values):
				widget.SetText(value)
				widget.SetPackedFontColor(color)
				widget.Show()

		self.SetSize(self.WIDTH, self.HEADER_HEIGHT + visibleRows * self.ROW_HEIGHT + self.FOOTER_PADDING)
		self.expandButton.Show() if len(self.snapshotRows) > self.COMPACT_ROWS else self.expandButton.Hide()
