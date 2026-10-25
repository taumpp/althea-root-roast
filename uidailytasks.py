# -*- coding: utf-8 -*-
import app
import chat
import fontconfig
import re
import ui

from uicrimsonember import SettingsScrollBar


WINDOW_SIZE = (573, 151)
OUTER_MARGIN = 16
FOOTER_HEIGHT = 32
SCROLL_GUTTER = 16
HEADER_POSITION = (16, 34)
HEADER_SIZE = (541, 29)
VIEWPORT_POSITION = (16, 68)
ROW_SIZE = (541, 51)
ROW_STEP = 53
VISIBLE_ROWS = 7
GAUGE_SIZE = (112, 8)
PROGRESS_CENTER_X = 296
GAUGE_LEFT = 240
MAX_VISIBLE_REWARDS = 5
MARKET_ROOT = "d:/ymir work/ui/game/crimson_ember/virtual_market/"
INVENTORY_ROOT = "d:/ymir work/ui/game/crimson_ember/inventory/"
QUEST_SCROLL_ROOT = "d:/ymir work/ui/game/crimson_ember/quest/scroll/"


TASK_STATUS_ACTIVE = 0
PLACEHOLDER_TEXT = u"Připravujeme"
TASK_STATUS_COMPLETED = 1
REWARD_TYPE_ITEM = 0
STATUS_UNAVAILABLE = 1
STATUS_LOADING = 2
STATUS_RESYNC_REQUIRED = 3
STATUS_REWARD_DELAYED = 4
REWARD_RIGHT_X = 525
REWARD_SPACING = 32
REWARD_STRIP_MIN_X = 365
REWARD_STRIP_MAX_X = 525
# The R1 switch "Denní úkoly | Řemesla" (uidailytasksr1): the daily tasks, the craft contract rows (craftcontractmodel).
# The original look ("Starý vzhled") has no switch and keeps both in one list.
TAB_DAILY = "daily"
TAB_CRAFTS = "crafts"
TABS = (TAB_DAILY, TAB_CRAFTS)
TAB_TEXTS = ("DAILY_TASKS_TAB_DAILY", "DAILY_TASKS_TAB_CRAFTS")     # locale_game, in the order of TABS
CRAFTS_EMPTY_TEXT = "DAILY_TASKS_CRAFTS_EMPTY"


def _Text(key):
	"""locale_game text (craftcontractmodel.Text: cp1250 bytes decoded), empty when the client has no such key."""
	try:
		import craftcontractmodel
		return craftcontractmodel.Text(key, u"")
	except Exception:
		return u""


def _LoadTab():
	try:
		import dailytasksprefs
		return dailytasksprefs.Get("tab", TABS)
	except Exception:
		return TAB_DAILY


def _SaveTab(tab):
	try:
		import dailytasksprefs
		dailytasksprefs.Set("tab", tab)
	except Exception:
		pass


def _RewardCenters(count):
	count = max(0, min(MAX_VISIBLE_REWARDS, _SafeInt(count, 0)))
	if not count:
		return ()
	startX = REWARD_RIGHT_X - 16 - (count - 1) * REWARD_SPACING
	return tuple(startX + index * REWARD_SPACING for index in range(count))


def _SafeInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError, OverflowError):
		return default


# Display-only grouping with the same "." separator as the European
# localeInfo.NumberToMoneyString used for inventory and market Yang
# (5.000.000). It is kept local so the module stays free of localeInfo's
# code-page branches. The server sends objective text pre-formatted (for
# example "5000000 Yang — Utratit v tržnici"), so only standalone integers of
# four or more digits are grouped; small counts, percentages, "+9" and
# already grouped numbers stay unchanged.
_OBJECTIVE_AMOUNT_PATTERN = re.compile(r"(?<![0-9A-Za-z_.,+-])[0-9]{4,}(?![0-9A-Za-z_]|[.,][0-9])")


def _GroupDigits(digits):
	head = len(digits) % 3 or 3
	groups = [digits[:head]]
	for index in range(head, len(digits), 3):
		groups.append(digits[index:index + 3])
	return ".".join(groups)


def _FormatAmount(value):
	return _GroupDigits(str(max(0, _SafeInt(value, 0))))


def _FormatObjective(objective):
	# Old daily periods keep their immutable catalog; hide the retired placeholder.
	objective = objective.replace(u" Syst\u00e9m bude dopln\u011bn; \u00fakol zat\u00edm nelze splnit.", u"")
	return _OBJECTIVE_AMOUNT_PATTERN.sub(
		lambda match: _GroupDigits(match.group(0)), objective
	)


# A craft daily task's craft mastery EXP (owner 21. 10.): the server
# appends " \u2014 +N EXP mistrovstv\u00ed" to the objective, so an older client shows it in the objective. This client
# moves it into the reward column, left of the item slots.
_MASTERY_PATTERN = re.compile(u"^(.*\\S) \u2014 \\+([0-9]+) EXP mistrovstv\u00ed$", re.UNICODE)
MASTERY_GAP = 8


def _SplitMastery(objective):
	"""(objective without the mastery EXP, u"+N EXP mistrovství" or u"")."""
	match = _MASTERY_PATTERN.match(objective)
	if not match:
		return (objective, u"")
	return (match.group(1), u"+%s EXP mistrovstv\u00ed" % _FormatAmount(match.group(2)))


def _NormalizeReward(record):
	if not isinstance(record, dict):
		return None
	rewardType = record.get("type", REWARD_TYPE_ITEM)
	if rewardType not in (REWARD_TYPE_ITEM, "item"):
		return None
	identifier = _SafeInt(record.get("vnum", record.get("id", 0)), 0)
	if identifier <= 0:
		return None
	amount = max(1, _SafeInt(record.get("amount", 1), 1))
	return {
		"type": "item",
		"id": identifier,
		"amount": amount,
	}


def _NormalizeTask(record):
	if not isinstance(record, dict):
		return None
	taskId = record.get("id", "")
	name = record.get("name", u"")
	objective = record.get("objective", u"")
	if not all(hasattr(value, "strip") for value in (taskId, name, objective)):
		return None
	taskId = taskId.strip()
	name = name.strip()
	objective = objective.strip()
	if not taskId or not name or not objective:
		return None
	objective, masteryText = _SplitMastery(objective)
	required = max(0, _SafeInt(record.get("required", 0), 0))
	current = max(0, _SafeInt(record.get("current", 0), 0))
	if required > 0:
		current = min(current, required)
	else:
		current = 0
	status = _SafeInt(record.get("status", TASK_STATUS_ACTIVE), TASK_STATUS_ACTIVE)
	if status not in (TASK_STATUS_ACTIVE, TASK_STATUS_COMPLETED):
		status = TASK_STATUS_ACTIVE
	rewards = []
	try:
		for reward in record.get("rewards", ()):
			normalized = _NormalizeReward(reward)
			if normalized:
				rewards.append(normalized)
	except TypeError:
		return None
	percent = int(current * 100 / required) if required > 0 else 0
	if status == TASK_STATUS_COMPLETED:
		percent = 100
	return {
		"id": taskId,
		"name": name,
		"objective": objective,
		"current": current,
		"required": required,
		"percent": percent,
		"status": status,
		"rewards": tuple(rewards),
		"mastery_text": masteryText,
	}


def _NormalizeTasks(records):
	normalizedTasks = []
	skipped = 0
	try:
		iterator = iter(records or ())
	except TypeError:
		return (normalizedTasks, 1)
	for record in iterator:
		normalized = _NormalizeTask(record)
		if normalized:
			normalizedTasks.append(normalized)
		else:
			skipped += 1
	return (normalizedTasks, skipped)


def _ApplyDeltaToSnapshot(snapshot, delta):
	if not isinstance(snapshot, dict) or not isinstance(delta, dict):
		return None
	sequence = _SafeInt(snapshot.get("sequence", -1), -1)
	deltaSequence = _SafeInt(delta.get("sequence", -1), -1)
	if deltaSequence <= sequence:
		return snapshot
	if (
		_SafeInt(delta.get("period_key", 0), 0) !=
		_SafeInt(snapshot.get("period_key", 0), 0) or
		_SafeInt(delta.get("generation", 0), 0) !=
		_SafeInt(snapshot.get("generation", 0), 0) or
		deltaSequence != sequence + 1
	):
		return None
	task = delta.get("task")
	if not isinstance(task, dict) or not task.get("id"):
		return None
	tasks = list(snapshot.get("tasks", ()))
	for index, existing in enumerate(tasks):
		if isinstance(existing, dict) and existing.get("id") == task.get("id"):
			tasks[index] = task
			break
	else:
		return None
	merged = dict(snapshot)
	for key in ("server_epoch", "reset_epoch", "sequence", "period_key", "generation"):
		merged[key] = delta.get(key, snapshot.get(key, 0))
	merged["tasks"] = tuple(tasks)
	return merged


# The Prague day of the daily tasks and craft contracts (server daily_tasks_period.cpp, PraguePeriodPolicy): the
# window counts down to the next Prague midnight itself while it has no snapshot with the server's reset_epoch
# (unavailable today, e.g. the account rollout's "from tomorrow" day, or still loading) instead of a frozen 00:00:00.
SECONDS_PER_DAY = 24 * 60 * 60


def _DaysFromCivil(year, month, day):
	year -= 1 if month <= 2 else 0
	era = (year if year >= 0 else year - 399) // 400
	yearOfEra = year - era * 400
	dayOfYear = (153 * (month - 3 if month > 2 else month + 9) + 2) // 5 + day - 1
	return era * 146097 + yearOfEra * 365 + yearOfEra // 4 - yearOfEra // 100 + dayOfYear - 719468


def _YearFromDays(days):
	days += 719468
	era = (days if days >= 0 else days - 146096) // 146097
	dayOfEra = days - era * 146097
	yearOfEra = (dayOfEra - dayOfEra // 1460 + dayOfEra // 36524 - dayOfEra // 146096) // 365
	dayOfYear = dayOfEra - (365 * yearOfEra + yearOfEra // 4 - yearOfEra // 100)
	monthPrime = (5 * dayOfYear + 2) // 153
	return yearOfEra + era * 400 + (1 if monthPrime >= 10 else 0)


def _LastSundayEpoch(year, month):
	"""01:00 UTC of the month's last Sunday: the Central European summer time switch."""
	firstOfNext = _DaysFromCivil(year + 1, 1, 1) if month == 12 else _DaysFromCivil(year, month + 1, 1)
	lastDay = firstOfNext - 1
	return (lastDay - (lastDay + 4) % 7) * SECONDS_PER_DAY + 3600


def _PragueOffset(utcEpoch):
	year = _YearFromDays(utcEpoch // SECONDS_PER_DAY)
	return 7200 if _LastSundayEpoch(year, 3) <= utcEpoch < _LastSundayEpoch(year, 10) else 3600


def _NextPragueMidnight(utcEpoch):
	"""UTC epoch of the next Prague midnight after utcEpoch (0 for an unknown time)."""
	utcEpoch = _SafeInt(utcEpoch, 0)
	if utcEpoch <= 0:
		return 0
	nextLocalMidnight = ((utcEpoch + _PragueOffset(utcEpoch)) // SECONDS_PER_DAY + 1) * SECONDS_PER_DAY
	offset = _PragueOffset(nextLocalMidnight - 3600)
	resetEpoch = nextLocalMidnight - offset
	corrected = _PragueOffset(resetEpoch)
	if corrected != offset:
		resetEpoch = nextLocalMidnight - corrected
	return resetEpoch


def _FormatCountdown(seconds):
	seconds = max(0, _SafeInt(seconds, 0))
	hours, remainder = divmod(seconds, 3600)
	minutes, seconds = divmod(remainder, 60)
	return u"%02d:%02d:%02d" % (hours, minutes, seconds)


TEXT_COLOR = 0xffeadfc8
MUTED_COLOR = 0xff9f968c
HEADER_COLOR = 0xffc8bba6
COMPLETED_COLOR = 0xffffdc63
VIEWPORT_HEIGHT = ROW_STEP * VISIBLE_ROWS - 2
NAME_LIMIT_WIDTH = 180
STATE_LIMIT_WIDTH = 500
TEXT_X = 48
# Tops of the name and the objective in a row. An objective wider than the column
# wraps to a second line (OBJECTIVE_LINES) instead of being cut off; the three
# lines then move up to stay inside the 51 px row. The rows have no hover
# tooltip: the name and the whole objective are always readable in the row and
# only the reward slots show the item tooltip.
TEXT_Y = (7, 27)
WRAPPED_TEXT_Y = (3, 19, 33)
OBJECTIVE_LINES = 2
OBJECTIVE_SEPARATOR = u" \u2014 "


def _TitleKey(text):
	return u" ".join(text.split()).rstrip(u".").strip().lower()


def _ObjectiveText(objective, name):
	"""The objective shown under the task name: formatted, without a part that
	only repeats the name ("25 ryb \u2014 Chytit ryby" under "Chytit ryby" shows
	"25 ryb"; an objective that is just the name shows nothing)."""
	objective = _FormatObjective(objective)
	parts = objective.split(OBJECTIVE_SEPARATOR)
	nameKey = _TitleKey(name)
	kept = [part for part in parts if _TitleKey(part) != nameKey]
	if len(kept) == len(parts):
		return objective
	return OBJECTIVE_SEPARATOR.join(kept)


def _WrapObjective(text, width, measure, maxLines=OBJECTIVE_LINES):
	"""``text`` word-wrapped to lines ``width`` px wide (``measure(text)`` ->
	px), at most ``maxLines`` of them; the last line keeps the rest (the line's
	limit width bounds it)."""
	words = text.split()
	lines = []
	current = u""
	for index, word in enumerate(words):
		candidate = current + u" " + word if current else word
		if not current or measure(candidate) <= width:
			current = candidate
			continue
		lines.append(current)
		if len(lines) >= maxLines - 1:
			current = u" ".join(words[index:])
			break
		current = word
	if current:
		lines.append(current)
	return tuple(lines)


def _LineMeasure(line):
	"""Width in px of a text in the font of ``line``, a hidden probe without a
	limit width (a limited line would report the cut width)."""
	def measure(text):
		line.SetText(text)
		try:
			return int(line.GetTextSize()[0])
		except Exception:
			return len(text) * 7
	return measure


def _CreateText(parent, x, y, text=u"", color=TEXT_COLOR, align="left",
				fontRole=fontconfig.ROLE_BODY, verticalAlign=None, outline=False):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	line.SetFontName(fontconfig.FontForRole(fontRole))
	line.SetPackedFontColor(color)
	if align == "center":
		line.SetHorizontalAlignCenter()
	elif align == "right":
		line.SetHorizontalAlignRight()
	if verticalAlign == "center":
		line.SetVerticalAlignCenter()
	if outline:
		line.SetOutline()
	line.AddFlag("not_pick")
	line.SetText(text)
	line.Show()
	return line


def _CreateImage(parent, x, y, filename, notPick=True):
	image = ui.ImageBox()
	image.SetParent(parent)
	image.SetPosition(x, y)
	image.LoadImage(filename)
	if notPick:
		image.AddFlag("not_pick")
	image.Show()
	return image


def _BuildR1(window):
	"""The R1 look of the window (uidailytasksr1) or None for the original look ("Starý vzhled")."""
	try:
		import uidailytasksr1
	except Exception:
		return None
	return uidailytasksr1.Build(window)


class HoverArea(ui.Window):
	"""An invisible hover area over a text of a row: over(True) on mouse in, over(False) on mouse out."""

	def __init__(self, parent, over):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.over = over
		self.Hide()

	def OnMouseOverIn(self):
		self.over(True)

	def OnMouseOverOut(self):
		self.over(False)


class DailyRewardSlot(ui.Window):
	def __init__(self, parent, x, y):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(32, 32)
		self.vnum = 0
		self.amount = 0
		self.tooltipItem = None
		self.frame = _CreateImage(
			self, 0, 0, INVENTORY_ROOT + "item_slot_framed.png"
		)
		self.slot = ui.SlotWindow()
		self.slot.SetParent(self)
		self.slot.SetPosition(0, 0)
		self.slot.SetSize(32, 32)
		self.slot.AppendSlot(0, 0, 0, 32, 32)
		self.slot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
		self.slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		self.slot.Show()
		self.Show()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetData(self, reward):
		self.slot.ClearSlot(0)
		self.vnum = 0
		self.amount = 0
		if not reward or reward.get("type") != "item":
			self.Hide()
			return
		self.vnum = reward["id"]
		self.amount = reward["amount"]
		self.slot.SetItemSlot(0, self.vnum, self.amount)
		self.slot.RefreshSlot()
		self.Show()

	def SetDimmed(self, dimmed):
		alpha = 0.55 if dimmed else 1.0
		self.frame.SetAlpha(alpha)
		if not self.vnum:
			return
		self.slot.ClearSlot(0)
		self.slot.SetItemSlot(
			0, self.vnum, self.amount,
			(1.0, 1.0, 1.0, alpha),
		)
		self.slot.RefreshSlot()

	def Clear(self):
		self.SetData(None)

	def __OverInItem(self, unusedSlot=0):
		if self.vnum and self.tooltipItem:
			self.tooltipItem.SetItemToolTip(self.vnum)
			if self.amount > 1:
				self.tooltipItem.AppendTextLine(u"Množství: %d" % self.amount)

	def __OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()


class DailyTaskRow(ui.Window):
	TEXT_Y = TEXT_Y
	WRAPPED_TEXT_Y = WRAPPED_TEXT_Y
	SIDE_Y = (7, 27)                # a contract row: its stock line right, the reward text under it
	NEAR_CHECK_SECONDS = 0.25       # how often a contract row asks whether its hand-in NPC is in range

	def __init__(self, parent, index):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(0, index * ROW_STEP)
		self.SetSize(*ROW_SIZE)
		self.tooltipItem = None
		self.background = _CreateImage(
			self, 0, 0, MARKET_ROOT + "surface/result_normal.png"
		)
		self.scrollIcon = _CreateImage(
			self, 9, 9, QUEST_SCROLL_ROOT + "quest_scroll_normal.png"
		)
		self.name = _CreateText(
			self, 48, 7, u"", TEXT_COLOR,
			fontRole=fontconfig.ROLE_CONTROL,
		)
		self.name.SetLimitWidth(NAME_LIMIT_WIDTH)
		self.objective = _CreateText(
			self, 48, 27, u"", MUTED_COLOR,
			fontRole=fontconfig.ROLE_DENSE,
		)
		self.objective.SetLimitWidth(NAME_LIMIT_WIDTH)
		self.objectiveWrap = _CreateText(
			self, TEXT_X, WRAPPED_TEXT_Y[2], u"", MUTED_COLOR,
			fontRole=fontconfig.ROLE_DENSE,
		)
		self.objectiveWrap.SetLimitWidth(NAME_LIMIT_WIDTH)
		self.objectiveProbe = _CreateText(
			self, TEXT_X, 0, u"", MUTED_COLOR, fontRole=fontconfig.ROLE_DENSE,
		)
		self.objectiveProbe.Hide()
		self.progressText = _CreateText(
			self, PROGRESS_CENTER_X, 9, u"0 / 0", TEXT_COLOR, "center",
			fontconfig.ROLE_BODY,
		)
		self.gauge = ui.Gauge()
		self.gauge.SetParent(self)
		self.gauge.SetPosition(GAUGE_LEFT, 30)
		self.gauge.MakeGauge(GAUGE_SIZE[0], "red")
		self.gauge.Show()
		self.rewardSlots = [
			DailyRewardSlot(self, 0, 9) for unusedIndex in range(MAX_VISIBLE_REWARDS)
		]
		self.placeholderText = _CreateText(
			self, REWARD_RIGHT_X, 18, PLACEHOLDER_TEXT, MUTED_COLOR, "right",
			fontconfig.ROLE_BODY,
		)
		self._InitContractWidgets(_CreateText(
			self, REWARD_RIGHT_X, self.SIDE_Y[0], u"", MUTED_COLOR, "right",
			fontconfig.ROLE_DENSE,
		))
		self.handInTaskId = ""
		self.handInEvent = None
		self.handInButton = ui.Button()
		self.handInButton.SetParent(self)
		self.handInButton.SetPosition(PROGRESS_CENTER_X - 36, 25)
		controls = "d:/ymir work/ui/public/crimson/controls/unified/"
		self.handInButton.SetUpVisual(controls + "button_72x24_normal.png")
		self.handInButton.SetOverVisual(controls + "button_72x24_hover.png")
		self.handInButton.SetDownVisual(controls + "button_72x24_pressed.png")
		self.handInButton.SetText(u"Odevzdat")
		self.handInButton.SetEvent(ui.__mem_func__(self.__HandIn))
		self.handInButton.Hide()
		self.Hide()

	def __HandIn(self):
		if self.handInTaskId and self.handInEvent:
			self.handInEvent(self.handInTaskId)

	def _InitContractWidgets(self, sideText):
		"""A craft contract row (craftcontractmodel): the stock right of the row with its hint, and the Odevzdat
		button active only in range of the contract's NPC (owner 14. 10.)."""
		self.sideText = sideText
		self.sideText.Hide()
		self.sideHint = u""
		self.sideHover = HoverArea(self, ui.__mem_func__(self._OverSide))
		self.placeholderY = self.placeholderText.GetLocalPosition()[1]
		self.handInHint = u""
		self.handInHover = None     # over the grey Odevzdat button (a disabled button gets no hover of its own)
		self.stateDefaults = None   # the button's and the count's own places, saved before a contract row moves them
		self.objectiveText = u""
		self.handInNearEvent = None
		self.handInNear = None
		self.nearCheckTime = 0.0

	def _SideTextWidth(self):
		return self.sideText.GetTextSize()[0]

	def _Hint(self, area, text, over):
		"""The hint of a hover area of the row: the R1 skin row (uidailytasksr1.Row) shows the shared R1 hint; the
		plain row has none (no one-line tooltip board, test_r1_hint_tooltips)."""
		return

	def _OverSide(self, over):
		self._Hint(self.sideHover, self.sideHint, over)

	def _OverHandIn(self, over):
		self._Hint(self.handInHover, self.handInHint, over)

	def _SetSide(self, data):
		text = data.get("side_text") or u""
		self.sideHint = data.get("side_hint") or u""
		self.sideText.SetText(text)
		if not text:
			self.sideText.Hide()
			self.sideHover.Hide()
			self.placeholderText.SetPosition(REWARD_RIGHT_X, self.placeholderY)
			return
		width = self._SideTextWidth()
		self.sideText.SetPosition(REWARD_RIGHT_X, self.SIDE_Y[0])
		self.sideText.Show()
		self.sideHover.SetPosition(REWARD_RIGHT_X - width, self.SIDE_Y[0])
		self.sideHover.SetSize(width, 16)
		self.sideHover.Show()
		self.placeholderText.SetPosition(REWARD_RIGHT_X, self.SIDE_Y[1])

	def _PlaceState(self, centered):
		"""A contract row handed in (owner 14. 10.): "Odevzdáno" alone in the middle of the row; a done row keeps
		its count above the Odevzdat button like the count above the gauge of other rows."""
		if self.stateDefaults is None:
			self.stateDefaults = (self.handInButton.GetLocalPosition(), self.progressText.GetLocalPosition())
		(bx, by), (tx, ty) = self.stateDefaults
		if not centered:
			self.handInButton.SetPosition(bx, by)
			self.progressText.SetPosition(tx, ty)
			return
		rowHeight = self.GetHeight()
		buttonY = max(0, (rowHeight - self.handInButton.GetHeight()) // 2)
		self.handInButton.SetPosition(bx, buttonY)
		try:
			textHeight = self.progressText.GetTextSize()[1]
		except Exception:
			textHeight = 16
		self.progressText.SetPosition(tx, max(0, (rowHeight - textHeight) // 2))

	def _HideHandInHover(self):
		if self.handInHover:
			self.handInHover.Hide()
			self._OverHandIn(False)

	def _CheckHandInNear(self):
		"""Grey the Odevzdat button of a contract row out of its NPC's range, with the hint where to stand."""
		near = True
		if self.handInTaskId.startswith("craft_contract_") and self.handInNearEvent:
			try:
				near = bool(self.handInNearEvent(self.handInTaskId))
			except Exception:
				near = True
		if near == self.handInNear:
			return
		self.handInNear = near
		# why the button is grey, in the row itself (owner 14. 10.): "Postav se k Deokbaeovi" instead of the objective
		if self.handInTaskId.startswith("craft_contract_") and self.handInHint:
			self._SetObjective(self.objectiveText if near else self.handInHint)
		if not self.handInHover:            # created after the button: it lies on top of it
			self.handInHover = HoverArea(self, ui.__mem_func__(self._OverHandIn))
		if near:
			self.handInButton.Enable()
			self.handInHover.Hide()
			self._OverHandIn(False)
			return
		self.handInButton.Disable()
		x, y = self.handInButton.GetLocalPosition()
		self.handInHover.SetPosition(x, y)
		self.handInHover.SetSize(self.handInButton.GetWidth(), self.handInButton.GetHeight())
		self.handInHover.Show()

	def OnUpdate(self):
		if not self.handInTaskId or not self.handInNearEvent:
			return
		now = app.GetTime()
		if now < self.nearCheckTime:
			return
		self.nearCheckTime = now + self.NEAR_CHECK_SECONDS
		self._CheckHandInNear()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem
		for rewardSlot in self.rewardSlots:
			rewardSlot.SetItemToolTip(tooltipItem)

	def _SetMastery(self, text, centers):
		"""A craft daily task's "+N EXP mistrovství" (owner 21. 10.) in the reward column: right-aligned left of the
		item slots, or in the slots' place when the task has no item reward."""
		y = self.placeholderText.GetLocalPosition()[1]
		if not text:
			self.placeholderText.SetPosition(REWARD_RIGHT_X, y)
			return
		right = centers[0] - 16 - MASTERY_GAP if centers else REWARD_RIGHT_X
		self.placeholderText.SetText(text)
		self.placeholderText.SetPosition(right, y)
		self.placeholderText.Show()

	def _SetObjective(self, text):
		lines = _WrapObjective(
			text, NAME_LIMIT_WIDTH, _LineMeasure(self.objectiveProbe)
		) or (u"",)
		wrapped = len(lines) > 1
		self.objective.SetText(lines[0])
		self.objectiveWrap.SetText(lines[1] if wrapped else u"")
		positions = self.WRAPPED_TEXT_Y if wrapped else self.TEXT_Y
		self.name.SetPosition(TEXT_X, positions[0])
		self.objective.SetPosition(TEXT_X, positions[1])
		if wrapped:
			self.objectiveWrap.SetPosition(TEXT_X, positions[2])
			self.objectiveWrap.Show()
		else:
			self.objectiveWrap.Hide()

	def Clear(self):
		self.handInTaskId = ""
		self.handInButton.Hide()
		self.placeholderText.Hide()
		self.sideText.Hide()
		self.sideHover.Hide()
		self._HideHandInHover()
		self.handInNear = None
		for rewardSlot in self.rewardSlots:
			rewardSlot.Clear()
		self.Hide()

	def SetData(self, data):
		if not data:
			self.Clear()
			return
		completed = data["status"] == TASK_STATUS_COMPLETED
		if completed:
			self.background.LoadImage(
				MARKET_ROOT + "surface/result_disabled.png"
			)
		else:
			self.background.LoadImage(
				MARKET_ROOT + "surface/result_normal.png"
			)
		self.name.SetText(data["name"])
		self._SetObjective(_ObjectiveText(data["objective"], data["name"]))
		if completed:
			progressText = u"Splněno"
			progressColor = COMPLETED_COLOR
		else:
			progressText = u"%s / %s" % (
				_FormatAmount(data["current"]),
				_FormatAmount(data["required"]),
			)
			progressColor = TEXT_COLOR
		# a contract row (craftcontractmodel) can say its state itself: "" = only the Odevzdat button, "Odevzdáno"
		if data.get("progress_text") is not None:
			progressText = data["progress_text"]
		self.progressText.SetText(progressText)
		self.progressText.Show() if progressText else self.progressText.Hide()
		handedIn = bool(data.get("progress_text")) and not data.get("hand_in")   # "Odevzdáno": alone, no gauge
		self._PlaceState(handedIn)
		self.objectiveText = data["objective"]
		self.progressText.SetPackedFontColor(progressColor)
		self.gauge.SetPercentage(data["percent"], 100)
		# the chests of the daily tasks, and a done craft contract (craftcontractmodel: "hand_in", one click near its NPC)
		self.handInTaskId = data.get("hand_in") or (data["id"] if data["id"].startswith("d2_chest_") and not completed else "")
		self.handInButton.Hide()
		self.gauge.Show()
		self.handInHint = data.get("hand_in_hint") or u""
		self.handInNear = None
		self.nearCheckTime = 0.0
		self._HideHandInHover()
		if handedIn:
			self.gauge.Hide()
		if self.handInTaskId:
			self.gauge.Hide()
			self.handInButton.Show()
			self._CheckHandInNear()
		self._SetSide(data)
		visibleRewards = data["rewards"][:MAX_VISIBLE_REWARDS]
		self.placeholderText.Hide()
		# a craft contract (craftcontractmodel) rewards craft EXP: its text stands where the item slots would be
		self.placeholderText.SetText(data.get("reward_text") or PLACEHOLDER_TEXT)
		if not visibleRewards:
			self.placeholderText.Show()
		centers = _RewardCenters(len(visibleRewards))
		for index, rewardSlot in enumerate(self.rewardSlots):
			rewardSlot.Clear()
			reward = visibleRewards[index] if index < len(visibleRewards) else None
			if reward:
				rewardSlot.SetPosition(centers[index] - 16, 9)
			rewardSlot.SetData(reward)
		self._SetMastery(data.get("mastery_text") or u"", centers)
		dimmed = completed
		self.scrollIcon.SetAlpha(0.55 if dimmed else 1.0)
		self.name.SetPackedFontColor(MUTED_COLOR if dimmed else TEXT_COLOR)
		self.objective.SetPackedFontColor(MUTED_COLOR)
		self.objectiveWrap.SetPackedFontColor(MUTED_COLOR)
		for rewardSlot in self.rewardSlots:
			rewardSlot.SetDimmed(dimmed)
		self.Show()


class DailyTasksWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.children = []
		self.rows = []
		self.tasks = []
		self.dailyTasks = []
		self.contracts = []      # craft contract rows (craftcontractmodel), after the daily tasks
		self.tooltipItem = None
		self.firstVisibleIndex = 0
		self.available = False
		self.hasSnapshot = False
		self.statusUnavailable = False
		self.resetEpoch = 0
		self.resetRequestSent = False
		self.unavailableReset = 0  # the Prague midnight after which an unavailable day asks for a snapshot again
		self.snapshotRequestEvent = None
		self.contractsRequestEvent = None   # craft contracts (interfacemodule.RequestCraftContracts)
		self.completionLimit = 3
		self.tabbed = False      # the R1 look shows the switch Denní úkoly | Řemesla (uidailytasksr1.Skin)
		self.tab = TAB_DAILY
		self.stateMessage = None # loading / error text of the daily tasks while they have no snapshot
		self.r1 = None
		self.__BuildWindow()
		self.SetAvailable(False)
		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Keep(self, child):
		self.children.append(child)
		return child

	def __BuildWindow(self):
		self.SetSize(*WINDOW_SIZE)
		self.SetTitleName(u"Denní úkoly")
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.AddFlag("movable")
		self.AddFlag("float")

		self.header = self.__Keep(_CreateImage(
			self, HEADER_POSITION[0], HEADER_POSITION[1],
			MARKET_ROOT + "surface/data_header.png",
		))
		self.__Keep(_CreateText(
			self, HEADER_POSITION[0] + 48 + NAME_LIMIT_WIDTH // 2, 49, u"Úkol", HEADER_COLOR, "center",
			fontconfig.ROLE_CONTROL, "center",
		))
		self.__Keep(_CreateText(
			self, HEADER_POSITION[0] + PROGRESS_CENTER_X, 49, u"Postup", HEADER_COLOR, "center",
			fontconfig.ROLE_CONTROL, "center",
		))
		self.__Keep(_CreateText(
			self, HEADER_POSITION[0] + REWARD_RIGHT_X, 49, u"Odměny", HEADER_COLOR, "right",
			fontconfig.ROLE_CONTROL, "center",
		))

		self.viewport = ui.Window()
		self.viewport.SetParent(self)
		self.viewport.SetPosition(*VIEWPORT_POSITION)
		self.viewport.SetSize(ROW_SIZE[0], VIEWPORT_HEIGHT)
		self.viewport.EnableScissorRect()
		self.viewport.SetOnRunMouseWheelEvent(ui.__mem_func__(self.OnMouseWheel))
		self.viewport.Show()
		self.__Keep(self.viewport)

		for index in range(VISIBLE_ROWS):
			row = DailyTaskRow(self.viewport, index)
			self.rows.append(row)

		self.stateText = _CreateText(
			self.viewport, ROW_SIZE[0] // 2, VIEWPORT_HEIGHT // 2,
			u"", MUTED_COLOR, "center", fontconfig.ROLE_BODY, "center",
		)
		self.stateText.SetLimitWidth(STATE_LIMIT_WIDTH)
		self.stateText.Hide()
		self.__Keep(self.stateText)

		self.scrollBar = SettingsScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(
			VIEWPORT_POSITION[0] + ROW_SIZE[0] + 4, VIEWPORT_POSITION[1],
		)
		self.scrollBar.SetScrollBarSize(VIEWPORT_HEIGHT)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar.Hide()
		self.__Keep(self.scrollBar)

		self.resetText = _CreateText(
			self, WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] - FOOTER_HEIGHT // 2, u"", MUTED_COLOR, "center",
			fontconfig.ROLE_DENSE, "center",
		)
		self.__Keep(self.resetText)
		self.r1 = _BuildR1(self)

	def __ResizeForTasks(self, count):
		# The row pool is a viewport limit, independent of the daily task limit.
		visibleCount = max(1, min(VISIBLE_ROWS, count))
		viewportHeight = visibleCount * ROW_STEP - (ROW_STEP - ROW_SIZE[1])
		width = ROW_SIZE[0] + 2 * OUTER_MARGIN
		if count > VISIBLE_ROWS:
			width += SCROLL_GUTTER
		height = VIEWPORT_POSITION[1] + viewportHeight + FOOTER_HEIGHT
		self.SetSize(width, height)
		self.viewport.SetSize(ROW_SIZE[0], viewportHeight)
		self.stateText.SetPosition(ROW_SIZE[0] // 2, viewportHeight // 2)
		self.scrollBar.SetScrollBarSize(viewportHeight)
		self.resetText.SetPosition(width // 2, height - FOOTER_HEIGHT // 2)
		r1 = self.__dict__.get("r1")
		if r1:
			r1.Layout(width, height)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem
		for row in self.rows:
			row.SetItemToolTip(tooltipItem)

	def SetCompletionLimit(self, limit):
		newLimit = max(3, min(7, _SafeInt(limit, 3)))
		changed = newLimit != self.completionLimit
		self.completionLimit = newLimit
		self.__RefreshCountdown()
		if changed and self.available and self.hasSnapshot and self.snapshotRequestEvent:
			self.snapshotRequestEvent()

	def SetHandInEvent(self, event):
		for row in self.rows:
			row.handInEvent = event

	def SetHandInNearEvent(self, event):
		"""event(taskId) -> True when the player stands in range of the NPC of a contract row (its Odevzdat button)."""
		for row in self.rows:
			row.handInNearEvent = event

	def SetContractsRequestEvent(self, event):
		self.contractsRequestEvent = event

	def SetSnapshotRequestEvent(self, event):
		self.snapshotRequestEvent = event

	def SetAvailable(self, enabled):
		wasAvailable = self.available
		self.available = bool(enabled)
		if not self.available:
			self.hasSnapshot = False
			self.resetEpoch = 0
			self.resetRequestSent = False
			self.statusUnavailable = True
			self.SetError(u"Denní úkoly nejsou dostupné.")
		elif not wasAvailable and not self.hasSnapshot:
			self.SetLoading()

	def SetSnapshot(self, snapshot):
		if not isinstance(snapshot, dict):
			self.SetError(u"Denní úkoly se nepodařilo načíst.")
			return False
		self.available = True
		self.hasSnapshot = True
		self.statusUnavailable = False
		self.resetEpoch = max(0, _SafeInt(snapshot.get("reset_epoch", 0), 0))
		self.resetRequestSent = False
		self.SetTasks(snapshot.get("tasks", ()))
		self.__RefreshCountdown()
		return True

	def SetStatus(self, statusCode):
		statusCode = _SafeInt(statusCode, 0)
		if statusCode == STATUS_UNAVAILABLE:
			self.SetError(u"Denní úkoly nejsou dostupné.")
			self.statusUnavailable = True
			self.resetRequestSent = False
		elif statusCode in (STATUS_LOADING, STATUS_RESYNC_REQUIRED):
			self.SetLoading()

	def __ClearRows(self):
		for row in self.rows:
			row.Clear()

	def __ShowState(self, message):
		self.tasks = []
		self.__ResizeForTasks(0)
		self.__ClearRows()
		self.scrollBar.Hide()
		self.stateText.SetText(message)
		self.stateText.Show()

	def __CraftsTab(self):
		return self.tabbed and self.tab == TAB_CRAFTS

	def SetTabbed(self, tabbed):
		"""The R1 skin turns the switch on (its Build) and off again (its Undo: the original look lists both)."""
		self.tabbed = bool(tabbed)
		if not self.tabbed:
			self.tab = TAB_DAILY

	def SelectTab(self, tab, remember=True):
		"""A click on the switch (remember: kept per character, dailytasksprefs) or Open() with the kept tab."""
		if not self.tabbed:
			return
		if tab not in TABS:
			tab = TAB_DAILY
		if remember:
			_SaveTab(tab)
		r1 = self.__dict__.get("r1")
		if r1:
			r1.SelectTab(tab)
		if tab == self.tab:
			return
		self.tab = tab
		self.firstVisibleIndex = 0
		self.scrollBar.SetPos(0.0, False)
		self.__ApplyTasks()
		self.__RefreshCountdown()

	def SetTasks(self, taskRecords):
		normalizedTasks, skipped = _NormalizeTasks(taskRecords)
		if skipped:
			chat.AppendChat(
				chat.CHAT_TYPE_INFO,
				u"Denní úkoly: %d úkolů se nepodařilo načíst." % min(skipped, 999),
			)
		self.dailyTasks = normalizedTasks
		self.stateMessage = None
		self.firstVisibleIndex = 0
		self.scrollBar.SetPos(0.0, False)
		self.__ApplyTasks()

	def SetContracts(self, records):
		"""The craft contract rows (craftcontractmodel.Records()); shown after the daily tasks once those are loaded."""
		self.contracts = list(records or ())
		if self.hasSnapshot or self.__CraftsTab():
			self.__ApplyTasks()

	def __VisibleTasks(self):
		if not self.tabbed:
			return list(self.dailyTasks) + list(self.contracts)
		return list(self.contracts) if self.tab == TAB_CRAFTS else list(self.dailyTasks)

	def __ApplyTasks(self):
		# the daily tab (and the original look) shows the loading / error text until the snapshot comes; the Řemesla
		# tab does not wait for the daily tasks
		if self.stateMessage is not None and not self.__CraftsTab():
			self.__ShowState(self.stateMessage)
			return
		self.tasks = self.__VisibleTasks()
		self.__ResizeForTasks(len(self.tasks))
		self.firstVisibleIndex = min(self.firstVisibleIndex, max(0, len(self.tasks) - VISIBLE_ROWS))
		self.stateText.Hide()
		if len(self.tasks) > VISIBLE_ROWS:
			self.scrollBar.SetMiddleBarSize(
				float(VISIBLE_ROWS) / float(len(self.tasks))
			)
			self.scrollBar.SetScrollStep(
				1.0 / float(len(self.tasks) - VISIBLE_ROWS)
			)
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		if self.tasks:
			self.__RefreshRows()
		elif self.__CraftsTab():
			self.__ShowState(_Text(CRAFTS_EMPTY_TEXT))
		else:
			self.__ShowState(u"Žádné denní úkoly")

	def SetLoading(self):
		self.statusUnavailable = False
		self.hasSnapshot = False
		self.tasks = []
		self.firstVisibleIndex = 0
		self.stateMessage = u"Načítání..."
		self.__ApplyTasks()

	def SetError(self, message):
		self.hasSnapshot = False
		self.tasks = []
		self.firstVisibleIndex = 0
		if not message or not hasattr(message, "strip"):
			message = u"Denní úkoly se nepodařilo načíst."
		self.stateMessage = message.strip()[:96]
		self.__ApplyTasks()

	def __RefreshRows(self):
		self.stateText.Hide()
		for offset, row in enumerate(self.rows):
			index = self.firstVisibleIndex + offset
			row.SetData(self.tasks[index] if index < len(self.tasks) else None)

	def __OnScroll(self):
		maximumStart = max(0, len(self.tasks) - VISIBLE_ROWS)
		self.firstVisibleIndex = int(
			float(maximumStart) * self.scrollBar.GetPos() + 0.5
		)
		self.__RefreshRows()

	def OnMouseWheel(self, scrollDown):
		# The viewport's run-wheel event passes "down" (a bool); the engine calls OnMouseWheel over a row or the bar
		# with the wheel delta (+120 up, -120 down), which always counted as "down".
		if not isinstance(scrollDown, bool):
			scrollDown = scrollDown < 0
		if len(self.tasks) <= VISIBLE_ROWS or not self.scrollBar.IsShow():
			return False
		if scrollDown:
			self.scrollBar.OnDown()
		else:
			self.scrollBar.OnUp()
		return True

	def __RefreshCountdown(self):
		"""The footer of the shown tab; returns the seconds left of the snapshot's day (0 = it ended, resync)."""
		now = _SafeInt(app.GetGlobalTimeStamp(), 0)
		remaining = max(0, self.resetEpoch - now)
		# without the server's reset_epoch (no snapshot: unavailable today or loading) the Prague midnight, both
		# the daily tasks and the craft contracts (craft_mastery) start a new day then
		shown = remaining if self.hasSnapshot and self.resetEpoch else max(0, _NextPragueMidnight(now) - now)
		if self.__CraftsTab():
			# the Řemesla tab lists the craft contracts: the daily task count does not belong to it
			text = u"Nové zakázky za: %s" % _FormatCountdown(shown)
		else:
			text = u"Dokončeno dnes: %d/%d   |   Nové úkoly za: %s" % (
				sum(1 for task in self.dailyTasks if task["status"] == TASK_STATUS_COMPLETED),
				self.completionLimit, _FormatCountdown(shown))
		self.resetText.SetText(text)
		return remaining

	def OnUpdate(self):
		remaining = self.__RefreshCountdown()
		if not self.hasSnapshot:
			self.__RetryUnavailableDay()
			return
		if remaining > 0 or self.resetRequestSent:
			return
		self.resetRequestSent = True
		self.SetLoading()
		if self.snapshotRequestEvent:
			self.snapshotRequestEvent()

	def __RetryUnavailableDay(self):
		"""A day the server refused (status unavailable, e.g. the account rollout's first day) asks once again after
		the next Prague midnight, so a window left open shows the new day's tasks."""
		if not self.available or not self.statusUnavailable or self.resetRequestSent:
			self.unavailableReset = 0
			return
		now = _SafeInt(app.GetGlobalTimeStamp(), 0)
		if not self.unavailableReset:
			self.unavailableReset = _NextPragueMidnight(now)
			return
		if now < self.unavailableReset:
			return
		self.unavailableReset = 0
		self.resetRequestSent = True
		if self.snapshotRequestEvent:
			self.snapshotRequestEvent()

	def Open(self):
		wasShown = self.IsShow()
		if self.tabbed and not wasShown:
			self.SelectTab(_LoadTab(), False)      # the tab this character had open last time
		if self.contractsRequestEvent:
			self.contractsRequestEvent()
		if self.available and not self.hasSnapshot and not self.statusUnavailable:
			self.SetLoading()
			if self.snapshotRequestEvent:
				self.snapshotRequestEvent()
		self.Show()
		if not wasShown:
			self.SetCenterPosition()
		self.SetTop()
		return True

	def Close(self):
		self.Hide()

	def Destroy(self):
		self.SetHandInEvent(None)
		self.Close()
		if self.scrollBar:
			self.scrollBar.Destroy()
		if self.r1:
			self.r1.Destroy()
		self.r1 = None
		self.tooltipItem = None
		self.snapshotRequestEvent = None
		self.contractsRequestEvent = None
		self.tasks = []
		self.rows = []
		self.children = []
		self.viewport = None
		self.scrollBar = None
		self.stateText = None
		self.resetText = None

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		return self.OnPressEscapeKey()
