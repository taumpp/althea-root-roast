# -*- coding: utf-8 -*-
"""InputGuard v1 GM watch viewer (/input_watch) in the Althea R1 look
(docs/ALTHEA_R1_KIT.md, "Using it in a window").

Loaded and built by uiinputguard.InputGuardSystem only when the server
starts a watch for this (GM) client; a warp or relog destroys the viewer and
nothing is remembered. State and validation live in inputguardwatchmodel;
the names and colour limits of what is shown come from the server's legend.
Its texts are English only (a GM tool).

A new R1 window (float + movable, uir1.Chrome: frame, header with the title
and the plain X, the whole header row drags it): the cursor canvas in an R1
panel, the session / cursor / counter / action lines under it, the verdict
and status blocks in the right column and the R1 buttons Stop and Penalty.
The X and Esc stop the watch, as the X of the original title bar did. Fonts
come from the kit (kit.font(ROW_ROLE)), colours from uir1tokens; a row that
is wider than its column is shortened with an ellipsis (uir1.Fit), so no text
leaves the window.

There is no second look: Settings -> "Starý vzhled" does not apply to this
staff-only window (it has no original board any more). When the R1 build
raises, the failure is traced once (uir1.TraceFailure), the half built window
is hidden and the exception goes on to uiinputguard.OnWatchBegin, which logs
"InputGuard watch viewer unavailable", resets the watch model and keeps the
game untouched. Later watches of the same session do not try the build again
(they fail at once with the same log line); a relog loads the module afresh.
"""

import grp
import net
import ui
import uiCommon

import uir1
import uir1tokens as T

import inputguardwatchmodel

WHAT = "input watch viewer"
WARN_YELLOW = 0xffffd36b      # semantic "warning" band; the R1 tokens have no yellow

BAND_COLORS = {
	inputguardwatchmodel.BAND_NONE: T.INK,
	inputguardwatchmodel.BAND_OK: T.GREEN_HI,
	inputguardwatchmodel.BAND_WARN: WARN_YELLOW,
	inputguardwatchmodel.BAND_ALERT: T.RED_HI,
	inputguardwatchmodel.BAND_DIM: T.MUTED,
}

ROW_ROLE = "text_xs"          # the kit font role of every text row
ROW_GAP = 2                   # px between two rows

_failed = []


class WatchCanvas(ui.Window):
	"""Scaled replay of the watched cursor: recent path, click marks and the
	current position. Geometry is rebuilt only when new samples arrive."""

	BACKGROUND_COLOR = grp.GenerateColor(0.03, 0.03, 0.04, 0.92)
	AREA_COLOR = grp.GenerateColor(0.35, 0.33, 0.30, 1.0)
	PATH_OLD_COLOR = grp.GenerateColor(0.36, 0.42, 0.52, 1.0)
	PATH_NEW_COLOR = grp.GenerateColor(0.78, 0.88, 1.0, 1.0)
	CURSOR_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)
	INJECTED_COLOR = grp.GenerateColor(1.0, 0.25, 0.2, 1.0)
	CLICK_COLORS = {
		1: grp.GenerateColor(1.0, 0.83, 0.3, 1.0),
		2: grp.GenerateColor(0.35, 0.85, 1.0, 1.0),
		4: grp.GenerateColor(0.85, 0.85, 0.85, 1.0),
	}
	MARK_SIZE = 5

	def __init__(self, model):
		ui.Window.__init__(self)
		self.model = model
		self.segments = []
		self.marks = []
		self.area = (0, 0, 1, 1)
		self.cursorPoint = None
		self.builtKey = None

	def __del__(self):
		ui.Window.__del__(self)

	def Rebuild(self, width, height):
		"""Canvas-relative geometry from the model's bounded history."""
		model = self.model
		clientWidth, clientHeight = model.clientWidth, model.clientHeight
		areaWidth, areaHeight = max(1, width - 2), max(1, height - 2)
		if clientWidth > 0 and clientHeight > 0:
			if clientWidth * areaHeight > clientHeight * areaWidth:
				areaHeight = max(1, areaWidth * clientHeight // clientWidth)
			else:
				areaWidth = max(1, areaHeight * clientWidth // clientHeight)
		areaX = (width - areaWidth) // 2
		areaY = (height - areaHeight) // 2
		self.area = (areaX, areaY, areaWidth, areaHeight)
		limit = inputguardwatchmodel.COORD_MAX

		segments = self.segments
		del segments[:]
		path = model.path
		previousX = previousY = 0
		for index in range(len(path)):
			x, y, penDown, _injected = path.Get(index)
			pixelX = areaX + x * (areaWidth - 1) // limit
			pixelY = areaY + y * (areaHeight - 1) // limit
			if penDown and index:
				segments.append((previousX, previousY, pixelX - previousX, pixelY - previousY))
			previousX, previousY = pixelX, pixelY

		marks = self.marks
		del marks[:]
		clicks = model.clicks
		for index in range(len(clicks)):
			x, y, button, injected = clicks.Get(index)
			color = self.INJECTED_COLOR if injected else self.CLICK_COLORS.get(
				button, self.CURSOR_COLOR)
			marks.append((areaX + x * (areaWidth - 1) // limit,
				areaY + y * (areaHeight - 1) // limit, color))

		cursor = model.cursor
		if cursor is None:
			self.cursorPoint = None
		else:
			self.cursorPoint = (areaX + cursor[0] * (areaWidth - 1) // limit,
				areaY + cursor[1] * (areaHeight - 1) // limit)

	def OnRender(self):
		x, y = self.GetGlobalPosition()
		width, height = self.GetWidth(), self.GetHeight()
		model = self.model
		key = (model.sessionRevision, model.traceRevision, width, height)
		if key != self.builtKey:
			self.builtKey = key
			self.Rebuild(width, height)

		grp.SetColor(self.BACKGROUND_COLOR)
		grp.RenderBar(x, y, width, height)
		areaX, areaY, areaWidth, areaHeight = self.area
		grp.SetColor(self.AREA_COLOR)
		grp.RenderBox(x + areaX, y + areaY, areaWidth, areaHeight)

		segments = self.segments
		count = len(segments)
		split = count // 2
		grp.SetColor(self.PATH_OLD_COLOR)
		for index in range(split):
			startX, startY, deltaX, deltaY = segments[index]
			grp.RenderLine(x + startX, y + startY, deltaX, deltaY)
		grp.SetColor(self.PATH_NEW_COLOR)
		for index in range(split, count):
			startX, startY, deltaX, deltaY = segments[index]
			grp.RenderLine(x + startX, y + startY, deltaX, deltaY)

		half = self.MARK_SIZE // 2
		for markX, markY, color in self.marks:
			grp.SetColor(color)
			grp.RenderBox(x + markX - half, y + markY - half, self.MARK_SIZE, self.MARK_SIZE)

		point = self.cursorPoint
		if point is not None:
			grp.SetColor(self.CURSOR_COLOR)
			grp.RenderLine(x + point[0] - 5, y + point[1], 11, 0)
			grp.RenderLine(x + point[0], y + point[1] - 5, 0, 11)


class WatchWindow(ui.Window):
	"""GM viewer: canvas, verdict, action list, status, Stop and Penalty.

	``title`` holds the current title text as the model gave it (the R1 header
	shows it upper case)."""

	PAD = T.PAD
	PANEL_INSET = 2           # the 'panel' frame lines around the canvas
	BLOCK_GAP = 12            # between the verdict and the status block
	SUMMARY_GAP = 4           # above the action summary
	ACTIONS_GAP = 2           # between the action summary and the action rows
	# The tallest cell of the row font in any font set plus the gap.
	ROW_HEIGHT = max(uir1.FontCell(fonts[ROW_ROLE]) for fonts in T.FONTS.values()) + ROW_GAP
	VERDICT_ROWS = 12
	# Score, clicks, every metric a legend may name and the two medians. The
	# status block moves down when a legend names more than fit VERDICT_ROWS.
	VERDICT_ROWS_MAX = 4 + inputguardwatchmodel.LEGEND_MAX_METRICS
	STATUS_ROWS = 9
	ACTION_ROWS = inputguardwatchmodel.ACTION_CAPACITY
	PENALTY_DIGITS = 7

	CANVAS_X = PAD + PANEL_INSET
	CANVAS_Y = T.HEAD_H + T.CONTENT_GAP + T.PROFILE_WINDOW["gap"] + PANEL_INSET
	CANVAS_WIDTH = 410
	CANVAS_HEIGHT = 226
	LEFT_WIDTH = CANVAS_WIDTH
	COLUMN_X = CANVAS_X + CANVAS_WIDTH + PANEL_INSET + PAD
	COLUMN_WIDTH = 300
	WIDTH = COLUMN_X + COLUMN_WIDTH + PAD

	# Left column: four lines, the action summary and the action rows.
	LINES_Y = CANVAS_Y + CANVAS_HEIGHT + PANEL_INSET + T.PROFILE_WINDOW["gap"]
	SUMMARY_Y = LINES_Y + 4 * ROW_HEIGHT + SUMMARY_GAP
	ACTIONS_Y = SUMMARY_Y + ROW_HEIGHT + ACTIONS_GAP
	ACTIONS_BOTTOM = ACTIONS_Y + ACTION_ROWS * ROW_HEIGHT
	# Right column: the status block under the longest verdict a legend may
	# name, then the footer buttons.
	STATUS_BOTTOM_MAX = CANVAS_Y + VERDICT_ROWS_MAX * ROW_HEIGHT + BLOCK_GAP + STATUS_ROWS * ROW_HEIGHT
	HEIGHT = max(STATUS_BOTTOM_MAX + T.PROFILE_WINDOW["foot_gap"] + T.BTN_H, ACTIONS_BOTTOM) + PAD
	BUTTON_Y = HEIGHT - PAD - T.BTN_H
	BUTTON_W = T.BTN_W
	BUTTON_GAP = 8

	def __init__(self, model):
		ui.Window.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.model = model
		self.kit = None
		self.chrome = None
		self.title = model.TitleText()
		self.children = []
		self.canvasPanel = None
		self.canvas = None
		self.sessionLine = None
		self.cursorLine = None
		self.automationLine = None
		self.counterLine = None
		self.actionSummaryLine = None
		self.actionLines = []
		self.verdictLines = []
		self.statusLines = []
		self.statusOffset = self.VERDICT_ROWS
		self.stopButton = None
		self.penaltyButton = None
		self.penaltyDialog = None
		self.penaltyTarget = ""
		self.revisions = None
		self.rowFont = None
		self.rowTop = 0
		self.SetSize(self.WIDTH, self.HEIGHT)
		if _failed:
			self.Hide()
			raise RuntimeError("R1 look of the %s failed earlier in this session" % WHAT)
		try:
			self.__Build()
		except Exception:
			_failed.append(WHAT)
			uir1.TraceFailure(WHAT)
			self.Hide()
			raise
		self.SetCenterPosition()
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.__ClosePenaltyDialog()
		self.Hide()
		if self.chrome:
			self.chrome.Destroy()
		self.chrome = None
		self.canvasPanel = None
		self.canvas = None
		self.sessionLine = None
		self.cursorLine = None
		self.automationLine = None
		self.counterLine = None
		self.actionSummaryLine = None
		self.actionLines = []
		self.verdictLines = []
		self.statusLines = []
		self.stopButton = None
		self.penaltyButton = None
		self.children = []

	def __MakeText(self, x, y, width):
		line = uir1.Text(self, "", x, y + self.rowTop, self.rowFont, BAND_COLORS[inputguardwatchmodel.BAND_NONE],
			valign="top")
		line.fitWidth = width
		self.children.append(line)
		return line

	def __MakeRows(self, x, y, count, width):
		return [self.__MakeText(x, y + index * self.ROW_HEIGHT, width) for index in range(count)]

	def __MakeButton(self, x, text, event):
		button = uir1.Button(self, self.kit, x, self.BUTTON_Y, self.BUTTON_W, text, event=event)
		self.children.append(button)
		return button

	def __Build(self):
		kit = uir1.Kit()
		self.kit = kit
		# The chrome first: the content draws above it.
		self.chrome = uir1.Chrome(self, kit, self.WIDTH, self.HEIGHT, self.title,
			on_close=ui.__mem_func__(self.Stop))
		self.rowFont = kit.font(ROW_ROLE)
		self.rowTop = uir1.CellTop(self.ROW_HEIGHT, self.rowFont)

		inset = self.PANEL_INSET
		self.canvasPanel = uir1.Frame(self, self.CANVAS_X - inset, self.CANVAS_Y - inset,
			self.CANVAS_WIDTH + 2 * inset, self.CANVAS_HEIGHT + 2 * inset, "panel")
		self.children.append(self.canvasPanel)
		canvas = WatchCanvas(self.model)
		canvas.SetParent(self)
		canvas.SetPosition(self.CANVAS_X, self.CANVAS_Y)
		canvas.SetSize(self.CANVAS_WIDTH, self.CANVAS_HEIGHT)
		canvas.Show()
		self.canvas = canvas

		x, y, width, row = self.CANVAS_X, self.LINES_Y, self.LEFT_WIDTH, self.ROW_HEIGHT
		self.sessionLine = self.__MakeText(x, y, width)
		self.cursorLine = self.__MakeText(x, y + row, width)
		self.automationLine = self.__MakeText(x, y + 2 * row, width)
		self.counterLine = self.__MakeText(x, y + 3 * row, width)
		self.actionSummaryLine = self.__MakeText(x, self.SUMMARY_Y, width)
		self.actionLines = self.__MakeRows(x, self.ACTIONS_Y, self.ACTION_ROWS, width)

		self.verdictLines = self.__MakeRows(self.COLUMN_X, self.CANVAS_Y, self.VERDICT_ROWS_MAX,
			self.COLUMN_WIDTH)
		self.statusLines = self.__MakeRows(self.COLUMN_X, self.__StatusY(self.statusOffset),
			self.STATUS_ROWS, self.COLUMN_WIDTH)

		self.stopButton = self.__MakeButton(self.COLUMN_X, "Stop", ui.__mem_func__(self.Stop))
		self.penaltyButton = self.__MakeButton(self.COLUMN_X + self.BUTTON_W + self.BUTTON_GAP, "Penalty",
			ui.__mem_func__(self.AskPenalty))

	def __StatusY(self, verdictRows):
		return self.CANVAS_Y + verdictRows * self.ROW_HEIGHT + self.BLOCK_GAP

	def __PlaceStatus(self, verdictRows):
		offset = max(self.VERDICT_ROWS, min(verdictRows, self.VERDICT_ROWS_MAX))
		if offset == self.statusOffset:
			return
		self.statusOffset = offset
		y = self.__StatusY(offset) + self.rowTop
		for index, line in enumerate(self.statusLines):
			line.SetPosition(self.COLUMN_X, y + index * self.ROW_HEIGHT)

	def __SetText(self, line, text, band):
		uir1.Fit(line, text, line.fitWidth)
		line.SetPackedFontColor(BAND_COLORS.get(band, BAND_COLORS[inputguardwatchmodel.BAND_NONE]))

	def __ApplyRows(self, lines, rows):
		for index in range(len(lines)):
			line = lines[index]
			if index < len(rows):
				text, band = rows[index]
				self.__SetText(line, text, band)
				line.Show()
			else:
				line.Hide()

	def __ApplyLine(self, line, text, band=inputguardwatchmodel.BAND_NONE):
		self.__SetText(line, text, band)

	def Refresh(self, force=False):
		"""Rewrite only the parts whose model revision changed."""
		model = self.model
		current = (model.sessionRevision, model.traceRevision, model.verdictRevision,
			model.actionRevision, model.statusRevision)
		previous = self.revisions
		if force or previous is None:
			previous = (None, None, None, None, None)
		if current == previous:
			return
		self.revisions = current
		if current[0] != previous[0]:
			self.title = model.TitleText()
			self.chrome.SetTitle(self.title)
			text, band = model.SessionText()
			self.__ApplyLine(self.sessionLine, text, band)
		if current[0] != previous[0] or current[1] != previous[1]:
			self.__ApplyLine(self.cursorLine, model.CursorText())
			self.__ApplyLine(self.automationLine, model.AutomationText())
			self.__ApplyLine(self.counterLine, model.CounterText(),
				inputguardwatchmodel.BAND_DIM)
		if current[0] != previous[0] or current[2] != previous[2]:
			rows = model.VerdictRows()
			self.__ApplyRows(self.verdictLines, rows)
			self.__PlaceStatus(len(rows))
		if current[0] != previous[0] or current[3] != previous[3]:
			self.__ApplyLine(self.actionSummaryLine, model.ActionSummaryText())
			self.__ApplyRows(self.actionLines, model.ActionRows())
		if current[0] != previous[0] or current[4] != previous[4]:
			self.__ApplyRows(self.statusLines, model.StatusRows())

	def Open(self):
		"""A watch began: a dialog left from the previous target is closed."""
		self.__ClosePenaltyDialog()
		self.Refresh(True)
		if not self.IsShow():
			self.SetCenterPosition()
			self.Show()
		self.SetTop()

	def Close(self):
		self.__ClosePenaltyDialog()
		self.Hide()

	def OnUpdate(self):
		self.Refresh()

	def OnPressEscapeKey(self):
		"""Esc does what the X does: stop the watch and close the viewer."""
		self.Stop()
		return True

	# Buttons -----------------------------------------------------------------
	def Stop(self):
		"""Stop the watch (when it still runs) and close the viewer."""
		model = self.model
		if model.active and not model.ended:
			net.SendChatPacket("/input_watch_off")
		model.Reset()
		self.Close()

	def AskPenalty(self):
		name = self.model.name
		if not self.model.active or not inputguardwatchmodel.IsValidTargetName(name):
			return
		self.__ClosePenaltyDialog()
		dialog = uiCommon.InputDialog()
		dialog.SetTitle("Penalty for %s (seconds)" % name)
		dialog.SetNumberMode()
		dialog.SetMaxLength(self.PENALTY_DIGITS)
		dialog.SetAcceptEvent(ui.__mem_func__(self.__OnPenaltyAccept))
		dialog.SetCancelEvent(ui.__mem_func__(self.__ClosePenaltyDialog))
		dialog.Open()
		self.penaltyDialog = dialog
		self.penaltyTarget = name

	def __OnPenaltyAccept(self):
		dialog = self.penaltyDialog
		if not dialog:
			return True
		seconds = inputguardwatchmodel.ParsePenaltySeconds(dialog.GetText())
		# The name the GM saw in the dialog, never a target that began later.
		name = self.penaltyTarget
		self.__ClosePenaltyDialog()
		if (seconds and self.model.active and name == self.model.name
				and inputguardwatchmodel.IsValidTargetName(name)):
			net.SendChatPacket("/penalty %s %d" % (name, seconds))
		return True

	def __ClosePenaltyDialog(self):
		dialog = self.penaltyDialog
		self.penaltyDialog = None
		self.penaltyTarget = ""
		if dialog:
			dialog.Close()
		return True
