# -*- coding: utf-8 -*-
"""DPS měřič: the damage table under the target board (uitarget.TargetBoard.dpsMeter), variant A of the round
kolo-20261009-dps ("Tabulka R1", owner 9. 10. 2026).

The server (game/src/dps_meter.cpp, HEADER_GC_DPS_METER) sends up to 20 rows sorted by damage
(attacker VID, name, total damage, DPS of the last 5 s), the total damage, the encounter id and the flags RESET (1)
or FINAL (2, the target was destroyed). The panel:

* four columns Hráč | Poškození | Podíl | DPS 5 s, the numbers right aligned under their right aligned labels,
  as wide as the target board's frame (one block, DETAILS_PANEL_GAP 4 px under it; uitarget places it);
* "you" is a brighter row (a lighter band and the brighter text), no mark beside it; the band has no lines of its
  own and spans the same width as the two rules, which keep RULE_GAP px of room on both sides of the rows (one
  line under the header, no doubled edge where your row meets it);
* five rows; when you are not among them, the fifth row is yours with your real rank after "· · ·", and
  "Další" with a badge (the number of hidden players) opens all rows ("Méně" closes them);
* a footer with the fight time and the total damage ("Boj 0:14 · celkem 338K");
* FINAL: "Zničeno za 0:23 · celkem 454K", the last column becomes Ø DPS (damage / fight time) and the panel
  hides itself after FINAL_HOLD_SECONDS; it also hides when no snapshot came for STALE_SECONDS (the server sends
  one every 0.5 s while the encounter lives), so a destroyed target never leaves a stale live table;
* DPS never more than the row's damage per second of real time: the server floors its window at 0.5 s, which made
  a fight shorter than that report twice the damage as DPS; the floor here is MIN_FIGHT_SECONDS (1 s).

The R1 look (uidpsmeterr1) recolours the panel, sets Tahoma 12 and swaps "Další" for the R1 button with the red
badge; settings "Starý vzhled" keeps this panel's own look.
"""
import app
import localeInfo
import player
import ui


# --------------------------------------------------------------------------- texts
# New strings carry their Czech and English text here (the locale tables keep the older DPS_METER_* keys); a locale
# that defines the key wins.
TEXTS = {
	"DPS_METER_DPS_LIVE": (u"DPS 5 s", u"DPS 5 s"),
	"DPS_METER_DPS_AVERAGE": (u"Ø DPS", u"Ø DPS"),
	"DPS_METER_FIGHT": (u"Boj %s · celkem %s", u"Fight %s · total %s"),
	"DPS_METER_DESTROYED": (u"Zničeno za %s · celkem %s", u"Destroyed in %s · total %s"),
	"DPS_METER_MORE": (u"Další", u"More"),
	"DPS_METER_LESS": (u"Méně", u"Less"),
}
GAP_MARK = u"· · ·"


def _IsCzech():
	try:
		path = app.GetLocalePath()
	except Exception:
		return True
	return str(path).replace("\\", "/").lower().rstrip("/").endswith("cz")


def _Locale(name, fallback):
	value = getattr(localeInfo, name, None)
	if not value or value == name:
		return fallback
	return value


def _Text(name):
	czech, english = TEXTS[name]
	return _Locale(name, czech if _IsCzech() else english)


def _Now():
	try:
		return float(app.GetTime())
	except Exception:
		return 0.0


# --------------------------------------------------------------------------- numbers
def FormatCompactNumber(value):
	"""26,5K / 612K / 1,18M (Czech decimal comma, no trailing zero); a dot outside the Czech locale."""
	value = max(0, int(value))
	for divisor, suffix in ((1000000000000, "T"), (1000000000, "B"), (1000000, "M"), (1000, "K")):
		if value >= divisor:
			amount = float(value) / divisor
			if amount >= 100:
				text = "%.0f" % amount
			elif amount >= 10:
				text = "%.1f" % amount
			else:
				text = "%.2f" % amount
			if "." in text:
				text = text.rstrip("0").rstrip(".")
			if _IsCzech():
				text = text.replace(".", ",")
			return text + suffix
	return str(value)


def FormatPercent(part, whole):
	"""31 % (Czech) / 31% (English), "<1 %" for a share under one percent."""
	space = u" " if _IsCzech() else u""
	if whole <= 0 or part <= 0:
		return u"0" + space + u"%"
	percent = float(part) * 100.0 / whole
	if percent < 1.0:
		return u"<1" + space + u"%"
	return u"%d%s%%" % (int(percent + 0.5), space)


def FormatDuration(seconds):
	seconds = max(0, int(seconds))
	return u"%d:%02d" % (seconds // 60, seconds % 60)


def VisibleRows(count, ownIndex, expanded, compactRows=5, maximumRows=20):
	"""(row indexes to show, True when the last one is your pinned row after "· · ·", number of hidden rows)."""
	count = min(count, maximumRows)
	if expanded or count <= compactRows:
		return list(range(count)), False, 0
	if ownIndex is not None and ownIndex >= compactRows:
		return list(range(compactRows - 1)) + [ownIndex], True, count - compactRows
	return list(range(compactRows)), False, count - compactRows


# --------------------------------------------------------------------------- the switch (Settings)
# Nastavení › Rozhraní › Jména a ukazatele › "Ukazatel poškození (DPS)" (settingsbackend, key dps_meter, default on).
# Off: no table and no DPS section in the target form, snapshots are dropped before any work; switching it off
# collapses an open table at once (live, no restart).
ENABLED = None                    # None = not read yet (the saved preference is read lazily, once)
_PANELS = []                      # weak references to the live tables (SetEnabled reaches them)


def _LoadEnabled():
	try:
		import settingsbackend
		return bool(settingsbackend.load_dps_meter())
	except Exception:
		return True


def IsEnabled():
	global ENABLED
	if ENABLED is None:
		ENABLED = _LoadEnabled()
	return ENABLED


def SetEnabled(enabled):
	"""Settings: on / off live. Off hides every shown table (the form collapses its section first)."""
	global ENABLED
	ENABLED = bool(enabled)
	alive = []
	for ref in _PANELS:
		panel = ref()
		if panel is None:
			continue
		alive.append(ref)
		if not ENABLED:
			panel.Disable()
		elif panel.layoutEvent:
			panel.layoutEvent()       # the target form shows its "DPS" chip again
	_PANELS[:] = alive


def _DressR1(panel):
	try:
		import uidpsmeterr1
		return uidpsmeterr1.Dress(panel)
	except:
		return None


class DpsMeterPanel(ui.ThinBoard):
	MIN_WIDTH = 300           # the block (target board frame + this panel) is at least this wide
	WIDTH = MIN_WIDTH         # the current width (SetBlockWidth)
	TOP = 6                   # the header row starts here
	ROW_HEIGHT = 18
	TEXT_Y = 2                # a Tahoma 12 line inside its 18 px row
	HEADER_RULE_Y = TOP + ROW_HEIGHT + 1   # the one hairline under the column labels
	RULE_GAP = 2              # the room between a hairline and the rows, the same above and under them
	HEADER_HEIGHT = HEADER_RULE_Y + 1 + RULE_GAP   # the first data row starts here
	PIN_GAP = 8               # the room of "· · ·" before your pinned row
	FOOTER_GAP = 4            # from the footer hairline to the footer line / "Další" (20 px)
	FOOTER_HEIGHT = RULE_GAP + 1 + FOOTER_GAP + 20 + 4   # hairline, footer line / "Další" and the bottom edge
	# in the target form without "Další" the footer keeps no empty room for the button: the space under the footer
	# line equals the one above the "DPS" heading (round kolo-20261009-formular-upravy, owner 9. 10. 2026)
	FOOTER_HEIGHT_COMPACT = RULE_GAP + 1 + FOOTER_GAP + 20 + 1
	COMPACT_ROWS = 5
	MAXIMUM_ROWS = 20
	RESET_FLAG = 1
	FINAL_FLAG = 2
	FINAL_HOLD_SECONDS = 15.0
	STALE_SECONDS = 5.0
	MIN_FIGHT_SECONDS = 1.0

	SIDE = 12                 # "Hráč" and the footer line
	RANK_RIGHT = 30
	NAME_X = 36
	DPS_INSET = 12            # the DPS column ends this far from the right edge
	PERCENT_TO_DPS = 64
	DAMAGE_TO_PERCENT = 46
	NAME_ROOM = 62            # free room between the end of a name and the damage column's right edge
	RULE_INSET = 8            # both hairlines and your row's band: one width, the edges line up
	BAND_INSET = RULE_INSET
	MORE_WIDTH = 58
	MORE_RIGHT = 10

	NORMAL_COLOR = 0xFFD8D8D8
	OWN_COLOR = 0xFFFFD35A
	HEADER_COLOR = 0xFFF0D9A0
	RANK_COLOR = 0xFFB0B0B0
	MUTED_COLOR = 0xFF909090
	FOOTER_COLOR = 0xFFB0B0B0
	FOOTER_FINAL_COLOR = 0xFFD8D8D8
	DIVIDER_COLOR = 0xAA80663D
	OWN_ROW_COLOR = 0x33FFFFFF

	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.AddFlag("float")
		self.width = self.MIN_WIDTH
		self.victimVid = 0
		self.encounterId = 0
		self.snapshotRows = []
		self.totalDamage = 0
		self.expanded = False
		self.final = False
		self.startedAt = 0.0
		self.lastDamageAt = 0.0
		self.lastSnapshotAt = 0.0
		self.hideAt = 0.0
		self.fightSeconds = 0.0
		self.expireEvent = None
		self.collapseEvent = None     # the unified target form (uitargetform): it collapses the table, then Reset()s it
		self.layoutEvent = None       # the unified target form: the table changed its height by itself ("Další")
		self.expiring = False
		self.compactFooter = False    # the target form: FOOTER_HEIGHT_COMPACT while "Další" is not shown
		self.rowWidgets = []
		self.visibleRows = []
		self.hiddenRows = 0
		self.pinned = False

		self._MakeHeader()
		self._MakeRows()
		self._MakeFooter()
		self.SetSize(self.width, self.HEADER_HEIGHT + self.FOOTER_HEIGHT)
		# R1 look (uidpsmeterr1): the R1 frame, Tahoma 12, the R1 colours and "Další" with the badge; None = this look.
		self.r1 = _DressR1(self)
		self.Hide()
		import weakref
		_PANELS.append(weakref.ref(self))

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def SetSize(self, width, height):
		ui.ThinBoard.SetSize(self, width, height)
		r1 = getattr(self, "r1", None)
		if r1:
			r1.Resize(width, height)

	# ----------------------------------------------------------------------- widgets
	def _MakeText(self, text, x, y, color=None, align="left"):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		line.SetText(text)
		line.SetOutline()
		if align == "right":
			line.SetHorizontalAlignRight()
		elif align == "center":
			line.SetHorizontalAlignCenter()
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
		# Native UI parents do not retain Python child wrappers. Keep the labels on
		# the panel so they cannot be garbage-collected after this method returns.
		y = self.TOP + self.TEXT_Y
		self.headerWidgets = (
			self._MakeText(_Locale("DPS_METER_PLAYER", u"Hráč"), self.SIDE, y, self.HEADER_COLOR),
			self._MakeText(_Locale("DPS_METER_DAMAGE", u"Poškození"), 0, y, self.HEADER_COLOR, "right"),
			self._MakeText(_Locale("DPS_METER_PERCENT", u"Podíl"), 0, y, self.HEADER_COLOR, "right"),
			self._MakeText(_Text("DPS_METER_DPS_LIVE"), 0, y, self.HEADER_COLOR, "right"),
		)
		self.headerDivider = self._MakeBar(self.RULE_INSET, self.HEADER_RULE_Y, 1, 1, self.DIVIDER_COLOR)

	def _MakeRows(self):
		# your row: a lighter band, no lines of its own (under the texts: made first)
		self.ownBand = self._MakeBar(self.BAND_INSET, 0, 1, self.ROW_HEIGHT, self.OWN_ROW_COLOR)
		self.ownBand.Hide()
		self.gapMark = self._MakeText(GAP_MARK, 0, 0, self.MUTED_COLOR, "center")
		self.gapMark.Hide()
		for index in range(self.MAXIMUM_ROWS):
			widgets = (
				self._MakeText("", self.RANK_RIGHT, 0, align="right"),
				self._MakeText("", self.NAME_X, 0),
				self._MakeText("", 0, 0, align="right"),
				self._MakeText("", 0, 0, align="right"),
				self._MakeText("", 0, 0, align="right"),
			)
			for widget in widgets:
				widget.Hide()
			self.rowWidgets.append(widgets)

	def _MakeFooter(self):
		self.footerDivider = self._MakeBar(self.RULE_INSET, 0, 1, 1, self.DIVIDER_COLOR)
		self.footerText = self._MakeText("", self.SIDE, 0, self.FOOTER_COLOR)

		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual("d:/ymir work/ui/public/small_thin_button_01.sub")
		button.SetOverVisual("d:/ymir work/ui/public/small_thin_button_02.sub")
		button.SetDownVisual("d:/ymir work/ui/public/small_thin_button_03.sub")
		button.SetText(_Text("DPS_METER_MORE"))
		button.SetEvent(ui.__mem_func__(self.ToggleExpanded))
		button.Hide()
		self.expandButton = button

	# ----------------------------------------------------------------------- geometry
	def SetBlockWidth(self, width):
		"""The width of the target board's frame (uitarget.UpdatePosition): the panel is as wide, at least MIN_WIDTH."""
		width = max(self.MIN_WIDTH, int(width))
		if width != self.width:
			self.width = width
			self.WIDTH = width
			if self.snapshotRows:
				self._Refresh()

	def BoardWidth(self, inset=0):
		"""The width the target board needs for this panel while it is shown (0 while hidden)."""
		if not self.IsShow():
			return 0
		return self.MIN_WIDTH + 2 * int(inset)

	def Columns(self):
		"""The right edges of the damage, share and DPS columns and the room of a name, for the current width."""
		dpsRight = self.width - self.DPS_INSET
		percentRight = dpsRight - self.PERCENT_TO_DPS
		damageRight = percentRight - self.DAMAGE_TO_PERCENT
		return damageRight, percentRight, dpsRight, damageRight - self.NAME_ROOM - self.NAME_X

	def SetExpireEvent(self, event):
		"""Called after the panel hid itself (final state over, stale table): the target board fits again."""
		self.expireEvent = event

	def SetFormEvents(self, collapse, layout):
		"""The unified target form (variant A): ``collapse`` replaces the hiding when the fight is over (the form
		animates the section away and calls Reset at its end), ``layout`` follows a height change of its own."""
		self.collapseEvent = collapse
		self.layoutEvent = layout

	def ShowEmpty(self):
		"""The form opened the DPS section before any damage: the column labels and "Boj 0:00 · celkem 0"."""
		if not self.snapshotRows:
			self.Reset()
			self._Refresh()
		self.Show()

	def HasOwnRow(self):
		"""True while the table has your row (you damaged this target): the form opens the section on that."""
		return bool(self.snapshotRows) and self.OwnIndex() is not None

	# ----------------------------------------------------------------------- state
	def Reset(self):
		self.victimVid = 0
		self.encounterId = 0
		self.snapshotRows = []
		self.totalDamage = 0
		self.final = False
		self.expanded = False
		self.expiring = False
		self.fightSeconds = 0.0
		self.visibleRows = []
		self.hiddenRows = 0
		self.pinned = False
		for widgets in self.rowWidgets:
			for widget in widgets:
				widget.Hide()
		self.ownBand.Hide()
		self.gapMark.Hide()
		self.expandButton.Hide()
		self.Hide()

	def Disable(self):
		"""The switch went off: the table goes away (through the form's collapse when it is in one)."""
		if not self.snapshotRows or self.expiring:
			if not self.snapshotRows:
				self.Reset()
			return
		if self.collapseEvent:
			self.expiring = True
			self.collapseEvent()
			return
		self.Reset()
		if self.expireEvent:
			self.expireEvent()

	def ApplySnapshot(self, victimVid, encounterId, flags, totalDamage, rows):
		if not IsEnabled():
			return                    # switched off in Settings: nothing is computed or shown
		if flags & self.RESET_FLAG:
			self.Reset()
			return

		if not rows:
			self.Reset()
			return

		now = _Now()
		totalDamage = max(0, int(totalDamage))
		if encounterId != self.encounterId or victimVid != self.victimVid or not self.snapshotRows:
			# a new fight: its clock starts with its first snapshot (the server sends one on the first hit)
			self.Reset()
			self.victimVid = victimVid
			self.encounterId = encounterId
			self.startedAt = now
			self.lastDamageAt = now
		elif totalDamage != self.totalDamage and not self.final:
			self.lastDamageAt = now
		self.lastSnapshotAt = now
		self.expiring = False             # a snapshot again: the table lives (the form unrolls it again)
		if flags & self.FINAL_FLAG and not self.final:
			# the target was destroyed: the fight lasted until this snapshot (the final hit), at least 1 s
			self.final = True
			self.lastDamageAt = now
			self.hideAt = now + self.FINAL_HOLD_SECONDS
		self.fightSeconds = max(0.0, self.lastDamageAt - self.startedAt)
		self.totalDamage = totalDamage
		self.snapshotRows = list(rows[:self.MAXIMUM_ROWS])
		self._Refresh()
		self.Show()

	def OnUpdate(self):
		if not self.snapshotRows or self.expiring:
			return
		now = _Now()
		if (self.final and now >= self.hideAt) or (not self.final and now - self.lastSnapshotAt >= self.STALE_SECONDS):
			if self.collapseEvent:
				self.expiring = True          # the form collapses the section with the table still in it
				self.collapseEvent()
				return
			self.Reset()
			if self.expireEvent:
				self.expireEvent()

	def ToggleExpanded(self):
		self.expanded = not self.expanded
		self._Refresh()
		if self.layoutEvent:
			self.layoutEvent()

	def FightSeconds(self):
		"""The real length of the fight for the rates: at least MIN_FIGHT_SECONDS."""
		return max(self.MIN_FIGHT_SECONDS, self.fightSeconds)

	def RowDps(self, totalDamage, rollingDps):
		"""Final: the average over the fight. Live: the server's 5 s rate, never more than the damage per
		MIN_FIGHT_SECONDS (the server floors its window at 0.5 s: a shorter fight doubled the rate)."""
		totalDamage = max(0, int(totalDamage))
		if self.final:
			return int(totalDamage / self.FightSeconds())
		return min(max(0, int(rollingDps)), int(totalDamage / self.MIN_FIGHT_SECONDS))

	def OwnIndex(self):
		mainVid = player.GetMainCharacterIndex()
		for index, row in enumerate(self.snapshotRows):
			if int(row[0]) == mainVid:
				return index
		return None

	def FooterText(self):
		duration = FormatDuration(self.FightSeconds() if self.final else self.fightSeconds)
		key = "DPS_METER_DESTROYED" if self.final else "DPS_METER_FIGHT"
		return _Text(key) % (duration, FormatCompactNumber(self.totalDamage))

	# ----------------------------------------------------------------------- layout
	def _FitName(self, line, name, width):
		line.SetText(name)
		r1 = getattr(self, "r1", None)
		if r1:
			return r1.FitName(line, name, width)
		try:
			if line.GetTextSize()[0] <= width:
				return name
		except Exception:
			return name
		cut = name
		while len(cut) > 1:
			cut = cut[:-1]
			line.SetText(cut + u"…")
			if line.GetTextSize()[0] <= width:
				break
		return line.GetText()

	def _Refresh(self):
		width = self.width
		damageRight, percentRight, dpsRight, nameWidth = self.Columns()

		header = self.headerWidgets
		for line in header:
			line.SetPackedFontColor(self.HEADER_COLOR)
		header[3].SetText(_Text("DPS_METER_DPS_AVERAGE" if self.final else "DPS_METER_DPS_LIVE"))
		y = self.TOP + self.TEXT_Y
		header[0].SetPosition(self.SIDE, y)
		header[1].SetPosition(damageRight, y)
		header[2].SetPosition(percentRight, y)
		header[3].SetPosition(dpsRight, y)
		self.headerDivider.SetPosition(self.RULE_INSET, self.HEADER_RULE_Y)
		self.headerDivider.SetSize(width - 2 * self.RULE_INSET, 1)
		self.headerDivider.SetColor(self.DIVIDER_COLOR)

		ownIndex = self.OwnIndex()
		visible, pinned, hidden = VisibleRows(len(self.snapshotRows), ownIndex, self.expanded,
											  self.COMPACT_ROWS, self.MAXIMUM_ROWS)
		self.visibleRows, self.pinned, self.hiddenRows = visible, pinned, hidden

		self.ownBand.Hide()
		self.gapMark.Hide()
		y = self.HEADER_HEIGHT
		for slot, widgets in enumerate(self.rowWidgets):
			if slot >= len(visible):
				for widget in widgets:
					widget.Hide()
				continue
			index = visible[slot]
			if pinned and slot == len(visible) - 1:
				self.gapMark.SetPosition(width // 2, y - 3)
				self.gapMark.SetPackedFontColor(self.MUTED_COLOR)
				self.gapMark.Show()
				y += self.PIN_GAP

			attackerVid, attackerName, totalDamage, rollingDps = self.snapshotRows[index]
			isOwnRow = index == ownIndex
			if isOwnRow:
				self._PlaceOwnBand(y, width)
			color = self.OWN_COLOR if isOwnRow else self.NORMAL_COLOR
			rankColor = self.OWN_COLOR if isOwnRow else self.RANK_COLOR
			rank, name, damage, share, dps = widgets
			textY = y + self.TEXT_Y
			rank.SetPosition(self.RANK_RIGHT, textY)
			name.SetPosition(self.NAME_X, textY)
			damage.SetPosition(damageRight, textY)
			share.SetPosition(percentRight, textY)
			dps.SetPosition(dpsRight, textY)
			rank.SetText(u"%d." % (index + 1))
			self._FitName(name, attackerName, nameWidth)
			damage.SetText(FormatCompactNumber(totalDamage))
			share.SetText(FormatPercent(totalDamage, self.totalDamage))
			dps.SetText(FormatCompactNumber(self.RowDps(totalDamage, rollingDps)))
			for widget in widgets:
				widget.SetPackedFontColor(rankColor if widget is rank else color)
				widget.Show()
			y += self.ROW_HEIGHT

		# footer: hairline, "Boj 0:14 · celkem 338K" / "Zničeno za 0:23 · …" and "Další" / "Méně"
		ruleY = y + self.RULE_GAP
		self.footerDivider.SetPosition(self.RULE_INSET, ruleY)
		self.footerDivider.SetSize(width - 2 * self.RULE_INSET, 1)
		self.footerDivider.SetColor(self.DIVIDER_COLOR)
		footerY = ruleY + 1 + self.FOOTER_GAP
		self.footerText.SetText(self.FooterText())
		self.footerText.SetPosition(self.SIDE, footerY + 3)
		self.footerText.SetPackedFontColor(self.FOOTER_FINAL_COLOR if self.final else self.FOOTER_COLOR)
		more = len(self.snapshotRows) > self.COMPACT_ROWS
		self._PlaceExpandButton(width, footerY, more)

		footer = self.FOOTER_HEIGHT_COMPACT if (self.compactFooter and not more) else self.FOOTER_HEIGHT
		self.SetSize(width, y + footer)

	def _PlaceOwnBand(self, y, width):
		w = width - 2 * self.BAND_INSET
		self.ownBand.SetPosition(self.BAND_INSET, y)
		self.ownBand.SetSize(w, self.ROW_HEIGHT)
		self.ownBand.SetColor(self.OWN_ROW_COLOR)
		self.ownBand.Show()

	def _PlaceExpandButton(self, width, y, shown):
		button = self.expandButton
		if not shown:
			button.Hide()
			return
		setMore = getattr(button, "SetMore", None)
		if setMore is not None:            # the R1 button: label, chevron and the badge
			button.SetPosition(width - self.MORE_RIGHT - self.MORE_WIDTH, y)
			setMore(self.expanded, self.hiddenRows)
		else:
			label = _Text("DPS_METER_LESS" if self.expanded else "DPS_METER_MORE")
			if not self.expanded and self.hiddenRows:
				label = u"%s (%d)" % (label, self.hiddenRows)
			button.SetText(label)
			button.SetPosition(width - self.MORE_RIGHT - button.GetWidth(), y)
		button.Show()
