# -*- coding: utf-8 -*-
"""InputGuard v1: headless state of the GM watch viewer.

Loaded only once the server starts a watch for this client; nothing a player
needs lives here. Tuple orders are fixed by the cross-repository contract;
see docs/FEATURE_INVARIANTS.md ("InputGuard v1"). The module keeps the
viewer's bounded history and formats it. It imports no client module, so it
runs under plain Python in tests. Every value the server hands over is
validated here; a malformed tuple is counted and dropped, never trusted and
never raised to the caller.

What the watched values mean (names, directions, colour limits) is not kept
here: the server sends it to the watching GM as a legend before every watch.
Without one the viewer shows plain numbers and no colour bands.
"""

from inputguardmodel import (
	AUTOMATION_METIN_QUEUE,
	AUTOMATION_AUTO_PICKUP,
	AUTOMATION_QUICK_BUFF,
	AUTOMATION_SWITCHBOT,
	AUTOMATION_AUTO_ATTACK,
	AUTOMATION_OTHER,
	HOVER_UI_WINDOWS,
	SLOT_NONE,
	_Integer,
	_U8,
	_U32,
)

AUTOMATION_LABELS = (
	(AUTOMATION_METIN_QUEUE, "queue"),
	(AUTOMATION_AUTO_PICKUP, "pickup"),
	(AUTOMATION_QUICK_BUFF, "buffs"),
	(AUTOMATION_SWITCHBOT, "switchbot"),
	(AUTOMATION_AUTO_ATTACK, "auto attack"),
	(AUTOMATION_OTHER, "other"),
)

# TInputGuardSample, in struct order.
SAMPLE_FIELD_COUNT = 12
(S_TIME, S_X, S_Y, S_TYPE, S_BUTTONS, S_KEY, S_WHEEL, S_FLAGS, S_AUTOMATION,
	S_HOVER_VID, S_HOVER_SLOT, S_HOVER_UI) = range(SAMPLE_FIELD_COUNT)

COORD_MAX = 10000
COORD_OUTSIDE = 0xFFFF

SAMPLE_MOVE = 0
SAMPLE_LEFT_DOWN = 1
SAMPLE_LEFT_UP = 2
SAMPLE_RIGHT_DOWN = 3
SAMPLE_RIGHT_UP = 4
SAMPLE_MIDDLE_DOWN = 5
SAMPLE_MIDDLE_UP = 6
SAMPLE_WHEEL = 7
SAMPLE_KEY_DOWN = 8
SAMPLE_KEY_UP = 9
SAMPLE_TYPE_MAX = 9

BUTTON_DOWN_TYPES = {
	SAMPLE_LEFT_DOWN: 1,
	SAMPLE_RIGHT_DOWN: 2,
	SAMPLE_MIDDLE_DOWN: 4,
}

FLAG_INJECTED = 1
FLAG_UNTRUSTED_DEVICE = 2
FLAG_WINDOW_ACTIVE = 4
FLAG_TEXT_FOCUSED = 8

# TInputGuardVerdict after pid: the positions the layout addresses itself.
# Every other position is named by the legend.
V_SCORE = 0
V_DECIDED = 1
V_CLICKS = 2
V_DWELL_P50 = 5
V_HOLD_P50 = 6
V_TOP_FACTOR = 13
VERDICT_FIELD_COUNT = 14  # the trailing reserved byte is optional

# TInputGuardReport, in struct order.
(R_NONCE, R_WINDOW_SEC, R_STATE, R_MOUSE_PHYSICAL, R_MOUSE_INJECTED,
	R_MOUSE_LOWER_IL, R_KEY_PHYSICAL, R_KEY_INJECTED, R_KEY_LOWER_IL,
	R_UNTRUSTED_EVENTS, R_BLOCKED_EVENTS, R_UNTRUSTED_COUNT, R_REMOTE_TOOLS,
	R_FOREGROUND_MS, R_MOVE_INJECTED) = range(15)
REPORT_FIELD_COUNT = 15

STATE_MOUSE_HOOK_OK = 1
STATE_KEY_HOOK_OK = 2
STATE_RAW_INPUT_OK = 4
STATE_REMOTE_SESSION = 8
STATE_HOOK_REINSTALLED = 16
STATE_BLOCKING_ACTIVE = 32
STATE_CAPTURE_SHIELD_ACTIVE = 64
STATE_HOOK_STALLED = 128
STATE_REMOTE_TOOL_SCAN_OK = 256

# Width of the report's remote-tool mask.
REMOTE_TOOL_BITS = 16

BAND_NONE = 0
BAND_OK = 1
BAND_WARN = 2
BAND_ALERT = 3
BAND_DIM = 4

HIGH_IS_SUSPICIOUS = 1
LOW_IS_SUSPICIOUS = -1

# Metric units: hundredths of a percent, or value x100.
LEGEND_UNITS = ("pct", "x100")
LEGEND_MAX_ROWS = 128
LEGEND_MAX_METRICS = 16
LEGEND_MAX_NAMES = 32
LEGEND_MAX_LABEL = 32
LEGEND_MAX_FIELD = 31
LEGEND_MAX_TOOL_BIT = 1 << 31
LEGEND_SEPARATOR = "|"
SUMMARY_NAME_LENGTH = 12
# A row is one text whose parts are joined by LEGEND_SEPARATOR, the row kind
# first; these are the parts after the kind.
LEGEND_ROW_FIELDS = {
	"score": 2,
	"metric": 6,
	"tool": 2,
	"action": 2,
	"cover": 3,
	"endreason": 2,
}
# Order of the action summary: worst first.
SUMMARY_BANDS = (BAND_ALERT, BAND_DIM, BAND_WARN, BAND_NONE)

HOVER_UI_LABELS = dict((uiId, label) for uiId, _attribute, label in HOVER_UI_WINDOWS)

PATH_CAPACITY = 384
CLICK_CAPACITY = 48
ACTION_CAPACITY = 10
MAX_SAMPLES_PER_TRACE = 64
MAX_NAME_LENGTH = 24
# A capture restarts its clock after a warp; a backwards jump lifts the pen.
TIME_RESET_TOLERANCE_MS = 1000

_U16 = 0xFFFF


def _Fields(values, count, maxima):
	"""First `count` items of a sequence as bounded integers, or None."""
	if not isinstance(values, (tuple, list)) or len(values) < count:
		return None
	result = []
	for index in range(count):
		number = _Integer(values[index], maxima[index])
		if number is None:
			return None
		result.append(number)
	return result


_VERDICT_MAXIMA = (100, 1) + (_U16,) * 11 + (_U8,)
_REPORT_MAXIMA = (_U32, _U16, _U16) + (_U32,) * 8 + (_U16, _U16, _U32, _U32)


def FormatMetric(value, unit):
	if unit == "pct":
		return "%.1f %%" % (value / 100.0)
	return "%.2f" % (value / 100.0)


def BandFor(value, direction, warn, alert):
	if direction == HIGH_IS_SUSPICIOUS:
		if value >= alert:
			return BAND_ALERT
		if value >= warn:
			return BAND_WARN
		return BAND_OK
	if value <= alert:
		return BAND_ALERT
	if value <= warn:
		return BAND_WARN
	return BAND_OK


def _LegendNumber(text, maximum):
	"""A legend field written as plain decimal digits, or None."""
	if not isinstance(text, str) or not 1 <= len(text) <= 10:
		return None
	for character in text:
		if character not in "0123456789":
			return None
	number = int(text)
	if number > maximum:
		return None
	return number


def _LegendLabel(text):
	"""A legend label with its spaces restored, or None."""
	if not isinstance(text, str):
		return None
	label = text.replace("_", " ")
	if not 1 <= len(label) <= LEGEND_MAX_LABEL or not label.strip():
		return None
	for character in label:
		# No control characters and no text-markup escape.
		if ord(character) < 32 or ord(character) == 127 or character == "|":
			return None
	return label


class WatchLegend(object):
	"""What the server says the watched values mean. An empty legend names
	nothing: ids are shown as numbers and nothing gets a colour band.

	A table the legend carries is the complete list of its ids; where the
	legend carries none, every id in range is taken as it comes.
	"""

	def __init__(self):
		self.complete = False
		# (warn, alert) of the score, or None.
		self.score = None
		# [(verdict position, label, direction, warn, alert, unit)] in
		# topFactor order.
		self.metrics = []
		# [(bit, label)] of the report's remote tools, in row order.
		self.tools = []
		# kind -> label
		self.actions = {}
		# cover -> (label, band); coverOrder keeps the row order.
		self.covers = {}
		self.coverOrder = []
		# reason -> label
		self.endReasons = {}

	def ScoreBand(self, score):
		if self.score is None:
			return BAND_NONE
		return BandFor(score, HIGH_IS_SUSPICIOUS, self.score[0], self.score[1])

	def KnowsAction(self, kind):
		return not self.actions or kind in self.actions

	def KnowsCover(self, cover):
		return not self.covers or cover in self.covers

	def ActionText(self, kind):
		return self.actions.get(kind) or "%d" % kind

	def CoverText(self, cover):
		entry = self.covers.get(cover)
		return entry[0] if entry else "%d" % cover

	def CoverBand(self, cover):
		entry = self.covers.get(cover)
		return entry[1] if entry else BAND_NONE

	def EndReasonText(self, reason):
		if not self.endReasons:
			return "%d" % reason
		return self.endReasons.get(reason, "unknown")

	def RemoteToolTexts(self, mask):
		if self.tools:
			return [label for bit, label in self.tools if mask & bit]
		return ["%d" % (1 << index) for index in range(REMOTE_TOOL_BITS)
			if mask & (1 << index)]


class _LegendDraft(object):
	"""A legend being received. One bad row spoils the whole draft."""

	def __init__(self):
		self.legend = WatchLegend()
		self.valid = True
		self.rowCount = 0

	def Add(self, kind, fields):
		if not self.valid:
			return
		if not isinstance(kind, str):
			self.valid = False
			return
		count = LEGEND_ROW_FIELDS.get(kind)
		if count is None:
			# A row kind this viewer does not know yet.
			return
		self.rowCount += 1
		if (self.rowCount > LEGEND_MAX_ROWS or len(fields) != count
				or not getattr(self, "_Add_" + kind)(*fields)):
			self.valid = False

	def _Add_score(self, warn, alert):
		warn = _LegendNumber(warn, 100)
		alert = _LegendNumber(alert, 100)
		if warn is None or alert is None or warn > alert:
			return False
		if self.legend.score is not None:
			return False
		self.legend.score = (warn, alert)
		return True

	def _Add_metric(self, field, direction, warn, alert, unit, label):
		metrics = self.legend.metrics
		field = _LegendNumber(field, LEGEND_MAX_FIELD)
		warn = _LegendNumber(warn, _U16)
		alert = _LegendNumber(alert, _U16)
		label = _LegendLabel(label)
		if direction == "1":
			direction = HIGH_IS_SUSPICIOUS
		elif direction == "-1":
			direction = LOW_IS_SUSPICIOUS
		else:
			return False
		if None in (field, warn, alert, label) or unit not in LEGEND_UNITS:
			return False
		if len(metrics) >= LEGEND_MAX_METRICS:
			return False
		for metric in metrics:
			if metric[0] == field:
				return False
		metrics.append((field, label, direction, warn, alert, unit))
		return True

	def _Add_tool(self, bit, label):
		tools = self.legend.tools
		bit = _LegendNumber(bit, LEGEND_MAX_TOOL_BIT)
		label = _LegendLabel(label)
		if not bit or label is None or bit & (bit - 1):
			return False
		if len(tools) >= LEGEND_MAX_NAMES:
			return False
		for known, _label in tools:
			if known == bit:
				return False
		tools.append((bit, label))
		return True

	def _Add_action(self, kind, label):
		label = _LegendLabel(label)
		if label is None:
			return False
		kind = _LegendNumber(kind, _U8)
		if kind is None or kind in self.legend.actions:
			return False
		if len(self.legend.actions) >= LEGEND_MAX_NAMES:
			return False
		self.legend.actions[kind] = label
		return True

	def _Add_cover(self, cover, band, label):
		legend = self.legend
		cover = _LegendNumber(cover, _U8)
		band = _LegendNumber(band, BAND_DIM)
		label = _LegendLabel(label)
		if None in (cover, band, label) or cover in legend.covers:
			return False
		if len(legend.covers) >= LEGEND_MAX_NAMES:
			return False
		legend.covers[cover] = (label, band)
		legend.coverOrder.append(cover)
		return True

	def _Add_endreason(self, reason, label):
		reasons = self.legend.endReasons
		reason = _LegendNumber(reason, _U8)
		label = _LegendLabel(label)
		if reason is None or label is None or reason in reasons:
			return False
		if len(reasons) >= LEGEND_MAX_NAMES:
			return False
		reasons[reason] = label
		return True

	def Finish(self):
		self.legend.complete = True
		return self.legend


def IsValidTargetName(name):
	"""A character name that is safe to put into a GM chat command."""
	if not isinstance(name, str) or not name or len(name) > MAX_NAME_LENGTH:
		return False
	for character in name:
		if character.isspace() or character in "/\\\"'|%" or ord(character) < 32:
			return False
	return True


def ParsePenaltySeconds(text, maximum=30 * 24 * 60 * 60):
	"""GM-typed duration: a positive whole number of seconds, or 0."""
	try:
		seconds = int(str(text).strip())
	except (TypeError, ValueError):
		return 0
	if seconds <= 0 or seconds > maximum:
		return 0
	return seconds


class _Ring(object):
	"""Fixed-capacity history; the oldest entry is overwritten."""

	def __init__(self, capacity):
		self.capacity = max(1, int(capacity))
		self.items = [None] * self.capacity
		self.start = 0
		self.count = 0

	def Clear(self):
		for index in range(self.capacity):
			self.items[index] = None
		self.start = 0
		self.count = 0

	def Append(self, item):
		if self.count < self.capacity:
			self.items[(self.start + self.count) % self.capacity] = item
			self.count += 1
		else:
			self.items[self.start] = item
			self.start = (self.start + 1) % self.capacity

	def Get(self, index):
		"""Entry by age: 0 is the oldest kept one."""
		return self.items[(self.start + index) % self.capacity]

	def Newest(self, back=0):
		"""Entry counted from the newest: 0 is the latest."""
		return self.items[(self.start + self.count - 1 - back) % self.capacity]

	def __len__(self):
		return self.count


# One bounded staff-only model across a phase change; no UI object is retained.
_continuation = None


def KeepContinuation(model):
	global _continuation
	_continuation = model if model.logicalWatch and model.active and not model.ended else None


def TakeContinuation():
	global _continuation
	model, _continuation = _continuation, None
	return model if model else None


class WatchModel(object):
	"""State of the GM watch viewer for one watched character.

	Callbacks for another pid, or without a preceding Begin, are ignored:
	the viewer opens only when the server starts a watch for this GM.
	"""

	def __init__(self):
		# (x, y, penDown, injected): penDown is False where the path breaks.
		self.path = _Ring(PATH_CAPACITY)
		# (x, y, buttonBit, injected)
		self.clicks = _Ring(CLICK_CAPACITY)
		# (tMs, kind, cover)
		self.actions = _Ring(ACTION_CAPACITY)
		# cover -> number of actions
		self.coverCounts = {}
		# The legend is not session state: it arrives before Begin, which
		# resets the session, and only ForgetLegend drops it.
		self.legend = WatchLegend()
		self.legendDraft = None
		self.__ResetSession()
		self.logicalWatch = 0
		self.logicalDeadline = 0
		self.segments = _Ring(16)
		self.nextSegment = None

	def __ResetSession(self):
		self.active = False
		self.ended = False
		self.endReason = 0
		self.pid = 0
		self.captureId = 0
		self.name = ""
		self.clientWidth = 0
		self.clientHeight = 0
		self.path.Clear()
		self.clicks.Clear()
		self.actions.Clear()
		self.coverCounts.clear()
		self.penDown = False
		self.lastTime = 0
		self.cursor = None
		self.lastSample = None
		self.sampleCount = 0
		self.clickCount = 0
		self.keyCount = 0
		self.wheelCount = 0
		self.injectedCount = 0
		self.malformedCount = 0
		self.actionCount = 0
		self.verdict = None
		self.status = None
		# Bumped whenever the corresponding part needs to be redrawn.
		self.traceRevision = 0
		self.verdictRevision = 0
		self.actionRevision = 0
		self.statusRevision = 0
		self.sessionRevision = 0

	def Reset(self):
		revision = self.sessionRevision
		self.__ResetSession()
		self.sessionRevision = revision + 1
		self.logicalWatch = 0
		self.logicalDeadline = 0
		self.nextSegment = None
		self.segments.Clear()

	def IsOpen(self):
		return self.active

	# Legend ------------------------------------------------------------------
	def LegendRow(self, row):
		"""One legend row as the server wrote it. Rows are collected between
		"begin" and "end" and replace the legend only when every one of them
		was valid. Returns True when this row applied a legend."""
		if isinstance(row, str):
			parts = row.split(LEGEND_SEPARATOR)
			kind, fields = parts[0], tuple(parts[1:])
		else:
			kind, fields = None, ()
		if kind == "begin":
			draft = _LegendDraft()
			draft.valid = not fields
			self.legendDraft = draft
			return False
		draft = self.legendDraft
		if draft is None:
			return False
		if kind != "end":
			draft.Add(kind, fields)
			return False
		self.legendDraft = None
		if fields or not draft.valid:
			return False
		self.legend = draft.Finish()
		self.sessionRevision += 1
		return True

	def ForgetLegend(self):
		self.legendDraft = None
		if self.legend.complete:
			self.legend = WatchLegend()
			self.sessionRevision += 1

	def __Accepts(self, pid):
		return self.active and _Integer(pid, _U32) == self.pid

	# Callbacks ---------------------------------------------------------------
	def KeepContinuation(self):
		self.penDown = False
		self.lastTime = 0
		self.lastSample = None
		self.sessionRevision += 1
		KeepContinuation(self)

	def LogicalState(self, pid, watchId, captureId, deadline, gap):
		try:
			pid, watchId, captureId, deadline, gap = tuple(int(v) for v in (pid, watchId, captureId, deadline, gap))
		except (TypeError, ValueError, OverflowError):
			return False
		if not 0 < pid <= _U32 or not 0 < watchId < (1 << 64) or not 0 < captureId <= _U32 or not 0 < deadline < (1 << 63) or gap not in (0, 1):
			return False
		if self.logicalWatch != watchId:
			self.Reset()
			self.segments.Clear()
			self.logicalWatch = watchId
		self.logicalDeadline = deadline
		self.nextSegment = (pid, captureId, bool(gap))
		self.sessionRevision += 1
		return True

	def Begin(self, pid, captureId, name):
		pid = _Integer(pid, _U32)
		captureId = _Integer(captureId, _U32)
		if not pid or captureId is None or not isinstance(name, str):
			return False
		continuing = bool(self.nextSegment and self.nextSegment[:2] == (pid, captureId) and self.pid == pid and self.active and not self.ended)
		if continuing:
			if self.captureId == captureId:
				return True
			# Capture clocks are unrelated: lift the pen and discard held state.
			self.penDown = False
			self.lastTime = 0
			self.cursor = None
			self.lastSample = None
			self.sessionRevision += 1
		elif self.nextSegment and self.nextSegment[:2] == (pid, captureId):
			revision = self.sessionRevision
			self.__ResetSession()
			self.sessionRevision = revision + 1
		else:
			self.Reset()
		if self.nextSegment and self.nextSegment[:2] == (pid, captureId):
			self.segments.Append((captureId, self.nextSegment[2]))
		self.active = True
		self.pid = pid
		self.captureId = captureId
		self.name = name[:MAX_NAME_LENGTH]
		return True

	def Trace(self, pid, clientWidth, clientHeight, samples):
		"""Returns the number of accepted samples."""
		if not self.__Accepts(pid) or self.ended:
			return 0
		if not isinstance(samples, (tuple, list)):
			self.malformedCount += 1
			return 0
		width = _Integer(clientWidth, _U16)
		height = _Integer(clientHeight, _U16)
		if width and height:
			self.clientWidth = width
			self.clientHeight = height
		accepted = 0
		for index in range(min(len(samples), MAX_SAMPLES_PER_TRACE)):
			if self.__AddSample(samples[index]):
				accepted += 1
			else:
				self.malformedCount += 1
		if len(samples) > MAX_SAMPLES_PER_TRACE:
			self.malformedCount += len(samples) - MAX_SAMPLES_PER_TRACE
		if accepted or samples:
			self.traceRevision += 1
		return accepted

	def __AddSample(self, sample):
		if not isinstance(sample, (tuple, list)) or len(sample) < SAMPLE_FIELD_COUNT:
			return False
		time = _Integer(sample[S_TIME], _U32)
		x = _Integer(sample[S_X], _U16)
		y = _Integer(sample[S_Y], _U16)
		kind = _Integer(sample[S_TYPE], SAMPLE_TYPE_MAX)
		buttons = _Integer(sample[S_BUTTONS], _U8)
		flags = _Integer(sample[S_FLAGS], _U8)
		automation = _Integer(sample[S_AUTOMATION], _U8)
		hoverVid = _Integer(sample[S_HOVER_VID], _U32)
		hoverSlot = _Integer(sample[S_HOVER_SLOT], _U16)
		hoverUi = _Integer(sample[S_HOVER_UI], _U16)
		if None in (time, x, y, kind, buttons, flags, automation, hoverVid,
				hoverSlot, hoverUi):
			return False
		# Key identity is neither needed nor kept; wheel only has to be sane.
		if _Integer(sample[S_KEY], _U16) is None:
			return False
		if _Integer(sample[S_WHEEL], 32767, -32768) is None:
			return False
		outside = x == COORD_OUTSIDE or y == COORD_OUTSIDE
		if not outside and (x > COORD_MAX or y > COORD_MAX):
			return False

		if time + TIME_RESET_TOLERANCE_MS < self.lastTime:
			self.penDown = False
		self.lastTime = time
		injected = bool(flags & FLAG_INJECTED)
		self.sampleCount += 1
		if injected:
			self.injectedCount += 1
		if kind in (SAMPLE_KEY_DOWN, SAMPLE_KEY_UP):
			if kind == SAMPLE_KEY_DOWN:
				self.keyCount += 1
		elif outside:
			self.penDown = False
			self.cursor = None
		else:
			self.path.Append((x, y, self.penDown, injected))
			self.penDown = True
			self.cursor = (x, y)
			button = BUTTON_DOWN_TYPES.get(kind)
			if button:
				self.clickCount += 1
				self.clicks.Append((x, y, button, injected))
			elif kind == SAMPLE_WHEEL:
				self.wheelCount += 1
		self.lastSample = (time, buttons, flags, automation, hoverVid, hoverSlot, hoverUi)
		return True

	def Verdict(self, pid, verdict):
		if not self.__Accepts(pid):
			return False
		fields = _Fields(verdict, VERDICT_FIELD_COUNT, _VERDICT_MAXIMA)
		if fields is None:
			self.malformedCount += 1
			return False
		self.verdict = tuple(fields)
		self.verdictRevision += 1
		return True

	def Action(self, pid, tMs, kind, cover):
		if not self.__Accepts(pid) or self.ended:
			return False
		time = _Integer(tMs, _U32)
		kind = _Integer(kind, _U8)
		cover = _Integer(cover, _U8)
		legend = self.legend
		if (time is None or kind is None or cover is None
				or not legend.KnowsAction(kind) or not legend.KnowsCover(cover)):
			self.malformedCount += 1
			return False
		self.actions.Append((time, kind, cover))
		self.coverCounts[cover] = self.coverCounts.get(cover, 0) + 1
		self.actionCount += 1
		self.actionRevision += 1
		return True

	def End(self, pid, reason):
		if not self.__Accepts(pid):
			return False
		self.ended = True
		self.endReason = _Integer(reason, _U8) or 0
		self.sessionRevision += 1
		return True

	def Status(self, pid, report, secondsSinceReport, missedHeartbeats, penaltyActive):
		if not self.__Accepts(pid):
			return False
		fields = _Fields(report, REPORT_FIELD_COUNT, _REPORT_MAXIMA)
		age = _Integer(secondsSinceReport, _U32)
		missed = _Integer(missedHeartbeats, _U32)
		if fields is None or age is None or missed is None:
			self.malformedCount += 1
			return False
		self.status = (tuple(fields), age, missed, bool(penaltyActive))
		self.statusRevision += 1
		return True

	# Presentation ------------------------------------------------------------
	def TitleText(self):
		if not self.active:
			return "Input watch"
		return "Input watch: %s (%d)" % (self.name, self.pid)

	def SessionText(self):
		"""(text, band) for the line under the canvas."""
		if not self.active:
			return ("", BAND_NONE)
		if self.ended:
			return ("Watch ended: %s" % self.legend.EndReasonText(self.endReason),
				BAND_WARN)
		return ("Watching, capture %d | segments %d (gaps possible)" % (self.captureId, len(self.segments)), BAND_NONE) if self.logicalWatch else ("Watching, capture %d" % self.captureId, BAND_NONE)

	def CursorText(self):
		sample = self.lastSample
		if sample is None:
			return "Waiting for input samples"
		_time, buttons, flags, _automation, hoverVid, hoverSlot, hoverUi = sample
		if self.cursor is None:
			position = "outside"
		else:
			position = "%d%% %d%%" % (self.cursor[0] // 100, self.cursor[1] // 100)
		held = "".join(label for bit, label in ((1, "L"), (2, "R"), (4, "M"))
			if buttons & bit) or "-"
		parts = ["Cursor %s" % position, "held %s" % held]
		if not flags & FLAG_WINDOW_ACTIVE:
			parts.append("window inactive")
		if flags & FLAG_TEXT_FOCUSED:
			parts.append("typing")
		if hoverUi:
			label = HOVER_UI_LABELS.get(hoverUi, "ui %d" % hoverUi)
			if hoverSlot != SLOT_NONE:
				label = "%s slot %d" % (label, hoverSlot)
			parts.append("over %s" % label)
		elif hoverVid:
			parts.append("over actor %d" % hoverVid)
		elif hoverSlot != SLOT_NONE:
			parts.append("over slot %d" % hoverSlot)
		return " | ".join(parts)

	def AutomationText(self):
		sample = self.lastSample
		active = [label for bit, label in AUTOMATION_LABELS
			if sample is not None and sample[3] & bit]
		return "Sanctioned automation: %s" % (", ".join(active) or "none")

	def CounterText(self):
		return "Samples %d  clicks %d  keys %d  wheel %d  injected %d  dropped %d" % (
			self.sampleCount, self.clickCount, self.keyCount, self.wheelCount,
			self.injectedCount, self.malformedCount)

	def VerdictRows(self):
		"""[(text, band)] for the verdict panel."""
		verdict = self.verdict
		if verdict is None:
			return [("Verdict: waiting for the server", BAND_DIM)]
		if not verdict[V_DECIDED]:
			return [
				("Verdict: not enough data", BAND_DIM),
				("Clicks analysed: %d" % verdict[V_CLICKS], BAND_DIM),
			]
		legend = self.legend
		score = verdict[V_SCORE]
		rows = [
			("Score %d / 100 (lead only)" % score, legend.ScoreBand(score)),
			("Clicks analysed: %d" % verdict[V_CLICKS], BAND_NONE),
		]
		if not legend.metrics:
			# Nothing names the measured values, so none is shown.
			rows.append(("Metrics: waiting for the server legend", BAND_DIM))
			return rows
		top = verdict[V_TOP_FACTOR]
		for factor, (index, label, direction, warn, alert, unit) in enumerate(legend.metrics):
			if index < len(verdict):
				value = verdict[index]
				text = "%s: %s" % (label, FormatMetric(value, unit))
				band = BandFor(value, direction, warn, alert)
			else:
				text = "%s: -" % label
				band = BAND_NONE
			if factor == top:
				text += "  < top"
			rows.append((text, band))
		rows.append(("Dwell median: %d ms" % verdict[V_DWELL_P50], BAND_NONE))
		rows.append(("Hold median: %d ms" % verdict[V_HOLD_P50], BAND_NONE))
		return rows

	def ActionRows(self):
		"""[(text, band)], newest first."""
		legend = self.legend
		rows = []
		for back in range(len(self.actions)):
			time, kind, cover = self.actions.Newest(back)
			rows.append(("%7.1f s  %-9s  %s" % (time / 1000.0,
				legend.ActionText(kind), legend.CoverText(cover)), legend.CoverBand(cover)))
		return rows

	def ActionSummaryText(self):
		if not self.actionCount:
			return "Actions: none yet"
		# One count per colour band other than the plain covered one, named
		# by the covers the legend puts into that band. Names are cut so the
		# line stays clear of the status block beside it.
		legend = self.legend
		parts = []
		for band in SUMMARY_BANDS:
			covers = [cover for cover in legend.coverOrder if legend.covers[cover][1] == band]
			if covers:
				name = "/".join(legend.covers[cover][0] for cover in covers)
				parts.append("%s %d" % (name[:SUMMARY_NAME_LENGTH].rstrip(),
					sum(self.coverCounts.get(cover, 0) for cover in covers)))
		if not parts:
			return "Actions %d" % self.actionCount
		return "Actions %d: %s" % (self.actionCount, ", ".join(parts))

	def StatusRows(self):
		"""[(text, band)] for the status block."""
		if self.status is None:
			return [("Status: no report yet", BAND_DIM)]
		report, age, missed, penaltyActive = self.status
		state = report[R_STATE]
		windowSec = report[R_WINDOW_SEC]
		rows = [("Report %d s ago, window %d s, missed %d" % (age, windowSec, missed),
			BAND_WARN if missed else BAND_NONE)]

		hooks = []
		broken = False
		for bit, label in ((STATE_MOUSE_HOOK_OK, "mouse"), (STATE_KEY_HOOK_OK, "keys"),
				(STATE_RAW_INPUT_OK, "raw")):
			if state & bit:
				hooks.append(label)
			else:
				hooks.append("%s OFF" % label)
				broken = True
		text = "Hooks: " + ", ".join(hooks)
		if state & STATE_HOOK_STALLED:
			text += ", stalled"
			broken = True
		if state & STATE_HOOK_REINSTALLED:
			text += ", reinstalled"
			broken = True
		rows.append((text, BAND_WARN if broken else BAND_OK))

		injected = report[R_MOUSE_INJECTED] + report[R_KEY_INJECTED]
		rows.append(("Mouse: %d physical, %d injected, %d lower IL" % (
			report[R_MOUSE_PHYSICAL], report[R_MOUSE_INJECTED], report[R_MOUSE_LOWER_IL]),
			BAND_WARN if report[R_MOUSE_INJECTED] or report[R_MOUSE_LOWER_IL] else BAND_NONE))
		rows.append(("Keys: %d physical, %d injected, %d lower IL" % (
			report[R_KEY_PHYSICAL], report[R_KEY_INJECTED], report[R_KEY_LOWER_IL]),
			BAND_WARN if report[R_KEY_INJECTED] or report[R_KEY_LOWER_IL] else BAND_NONE))
		rows.append(("Injected moves: %d, blocked events: %d" % (
			report[R_MOVE_INJECTED], report[R_BLOCKED_EVENTS]),
			BAND_WARN if report[R_MOVE_INJECTED] or (injected and report[R_BLOCKED_EVENTS])
			else BAND_NONE))
		rows.append(("Untrusted devices: %d (%d events)" % (
			report[R_UNTRUSTED_COUNT], report[R_UNTRUSTED_EVENTS]),
			BAND_WARN if report[R_UNTRUSTED_COUNT] or report[R_UNTRUSTED_EVENTS]
			else BAND_NONE))

		remote = self.legend.RemoteToolTexts(report[R_REMOTE_TOOLS])
		if state & STATE_REMOTE_SESSION:
			remote.insert(0, "remote session")
		if remote:
			rows.append(("Remote: " + ", ".join(remote), BAND_WARN))
		elif state & STATE_REMOTE_TOOL_SCAN_OK:
			rows.append(("Remote: none found", BAND_NONE))
		else:
			rows.append(("Remote: not scanned", BAND_DIM))

		modes = []
		if state & STATE_BLOCKING_ACTIVE:
			modes.append("blocking")
		if state & STATE_CAPTURE_SHIELD_ACTIVE:
			modes.append("capture shield")
		rows.append(("Foreground %.1f s%s" % (report[R_FOREGROUND_MS] / 1000.0,
			(", " + ", ".join(modes)) if modes else ""), BAND_NONE))
		rows.append(("Restriction: %s" % ("active" if penaltyActive else "none"),
			BAND_WARN if penaltyActive else BAND_NONE))
		return rows
