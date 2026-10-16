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
	return _OBJECTIVE_AMOUNT_PATTERN.sub(
		lambda match: _GroupDigits(match.group(0)), objective
	)


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
		self.nameHit = ui.Button()
		self.nameHit.SetParent(self)
		self.nameHit.SetPosition(46, 3)
		self.nameHit.SetSize(NAME_LIMIT_WIDTH + 4, 43)
		self.nameHit.Show()
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
			self, REWARD_RIGHT_X, 18, u"Připravujeme", MUTED_COLOR, "right",
			fontconfig.ROLE_BODY,
		)
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

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem
		for rewardSlot in self.rewardSlots:
			rewardSlot.SetItemToolTip(tooltipItem)

	def Clear(self):
		self.handInTaskId = ""
		self.handInButton.Hide()
		self.placeholderText.Hide()
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
		self.objective.SetText(_FormatObjective(data["objective"]))
		self.nameHit.SetToolTipText(data["name"], 0, -19)
		if completed:
			progressText = u"Splněno"
			progressColor = COMPLETED_COLOR
		else:
			progressText = u"%s / %s" % (
				_FormatAmount(data["current"]),
				_FormatAmount(data["required"]),
			)
			progressColor = TEXT_COLOR
		self.progressText.SetText(progressText)
		self.progressText.SetPackedFontColor(progressColor)
		self.gauge.SetPercentage(data["percent"], 100)
		self.handInTaskId = data["id"] if data["id"].startswith("d2_chest_") and not completed else ""
		self.handInButton.Hide()
		self.gauge.Show()
		if self.handInTaskId:
			self.gauge.Hide()
			self.handInButton.Show()
		visibleRewards = data["rewards"][:MAX_VISIBLE_REWARDS]
		self.placeholderText.Hide()
		if not visibleRewards:
			self.placeholderText.Show()
		centers = _RewardCenters(len(visibleRewards))
		for index, rewardSlot in enumerate(self.rewardSlots):
			rewardSlot.Clear()
			reward = visibleRewards[index] if index < len(visibleRewards) else None
			if reward:
				rewardSlot.SetPosition(centers[index] - 16, 9)
			rewardSlot.SetData(reward)
		dimmed = completed
		self.scrollIcon.SetAlpha(0.55 if dimmed else 1.0)
		self.name.SetPackedFontColor(MUTED_COLOR if dimmed else TEXT_COLOR)
		self.objective.SetPackedFontColor(MUTED_COLOR)
		for rewardSlot in self.rewardSlots:
			rewardSlot.SetDimmed(dimmed)
		self.Show()


class DailyTasksWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.children = []
		self.rows = []
		self.tasks = []
		self.tooltipItem = None
		self.firstVisibleIndex = 0
		self.available = False
		self.hasSnapshot = False
		self.statusUnavailable = False
		self.resetEpoch = 0
		self.resetRequestSent = False
		self.snapshotRequestEvent = None
		self.completionLimit = 3
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
		elif statusCode in (STATUS_LOADING, STATUS_RESYNC_REQUIRED):
			self.SetLoading()

	def __ClearRows(self):
		for row in self.rows:
			row.Clear()

	def __ShowState(self, message):
		self.__ResizeForTasks(0)
		self.__ClearRows()
		self.scrollBar.Hide()
		self.stateText.SetText(message)
		self.stateText.Show()

	def SetTasks(self, taskRecords):
		normalizedTasks, skipped = _NormalizeTasks(taskRecords)
		if skipped:
			chat.AppendChat(
				chat.CHAT_TYPE_INFO,
				u"Denní úkoly: přeskočeno %d neplatných záznamů." % min(skipped, 999),
			)
		self.tasks = normalizedTasks
		self.__ResizeForTasks(len(self.tasks))
		self.firstVisibleIndex = 0
		self.stateText.Hide()
		self.scrollBar.SetPos(0.0, False)
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
		else:
			self.__ShowState(u"Žádné denní úkoly")

	def SetLoading(self):
		self.statusUnavailable = False
		self.hasSnapshot = False
		self.tasks = []
		self.firstVisibleIndex = 0
		self.__ShowState(u"Načítání…")

	def SetError(self, message):
		self.hasSnapshot = False
		self.tasks = []
		self.firstVisibleIndex = 0
		if not message or not hasattr(message, "strip"):
			message = u"Denní úkoly se nepodařilo načíst."
		self.__ShowState(message.strip()[:96])

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
		if len(self.tasks) <= VISIBLE_ROWS or not self.scrollBar.IsShow():
			return False
		if scrollDown:
			self.scrollBar.OnDown()
		else:
			self.scrollBar.OnUp()
		return True

	def __RefreshCountdown(self):
		remaining = max(0, self.resetEpoch - _SafeInt(app.GetGlobalTimeStamp(), 0))
		self.resetText.SetText(
			u"Dokončeno dnes: %d/%d   ·   Nové úkoly za: %s" % (
				sum(1 for task in self.tasks if task["status"] == TASK_STATUS_COMPLETED),
				self.completionLimit, _FormatCountdown(remaining))
		)
		return remaining

	def OnUpdate(self):
		remaining = self.__RefreshCountdown()
		if remaining > 0 or not self.hasSnapshot or self.resetRequestSent:
			return
		self.resetRequestSent = True
		self.SetLoading()
		if self.snapshotRequestEvent:
			self.snapshotRequestEvent()

	def Open(self):
		wasShown = self.IsShow()
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
		self.tooltipItem = None
		self.snapshotRequestEvent = None
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
