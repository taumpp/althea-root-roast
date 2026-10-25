import chat
import background
import fontconfig
import grp
import localeInfo
import net
import ui
import uiCommon
import uicrimsoncontrols
import uiwheel


SLOT_COUNT = 50
PAGE_COUNT = 5
ROWS_PER_PAGE = 10
PAGE_LABELS = ("I", "II", "III", "IV", "V")
ROW_ACTIONS = ("save", "edit", "delete", "teleport")
ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/custom_ports/"
ICON_PATHS = {
	"save": ASSET_ROOT + "icon_save_16.png",
	"edit": ASSET_ROOT + "icon_edit_16.png",
	"delete": ASSET_ROOT + "icon_delete_16.png",
	"teleport": ASSET_ROOT + "icon_teleport_16.png",
}
SHARED_FAMILIES = {"utility": "26x24", "page": "72x24", "teleport": "92x24"}
ROW_NUMBER_COLOR = grp.GenerateColor(226 / 255.0, 162 / 255.0, 75 / 255.0, 1.0)
COORDINATE_COLOR = grp.GenerateColor(148 / 255.0, 235 / 255.0, 126 / 255.0, 1.0)
ACTION_LABEL_COLOR = grp.GenerateColor(228 / 255.0, 218 / 255.0, 203 / 255.0, 1.0)
SHORT_ACTION_LABEL_MAX = 10


def _Locale(key, fallback):
	return getattr(localeInfo, key, fallback)


class CustomPortsButton(ui.Button):
	HEIGHT = 24

	def __init__(self, parent, x, y, width, family, text="", icon=None, tooltip=""):
		ui.Button.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, self.HEIGHT)
		uicrimsoncontrols.ApplyVisuals(self, SHARED_FAMILIES[family])
		if text and icon:
			role = fontconfig.ROLE_BODY
			if len(text) > SHORT_ACTION_LABEL_MAX:
				role = fontconfig.ROLE_DENSE
			self.SetFontName(fontconfig.FontForRole(role, 0))
		self.SetText(text)
		if text and icon:
			self.ButtonText.SetPackedFontColor(ACTION_LABEL_COLOR)
			self.ButtonText.SetOutline()
		self.icon = None
		if icon:
			self.icon = ui.ImageBox()
			self.icon.SetParent(self)
			self.icon.AddFlag("not_pick")
			self.icon.LoadImage(icon)
			if text:
				iconX = 2 if len(text) > 10 else 9
				self.icon.SetPosition(iconX, 4)
				self.ButtonText.SetPosition(width // 2 + 8, self.HEIGHT // 2)
			else:
				self.icon.SetPosition((width - 16) // 2, 4)
			self.icon.Show()
		if tooltip:
			self.SetToolTipText(tooltip)
		self.Show()


class CustomPortsRow(ui.Window):
	def __init__(self, parent, x, y, width, height):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)

		self.topLine = ui.Bar()
		self.topLine.SetParent(self)
		self.topLine.SetPosition(0, 0)
		self.topLine.SetSize(width, 1)
		self.topLine.SetColor(grp.GenerateColor(74 / 255.0, 52 / 255.0, 40 / 255.0, 1.0))
		self.topLine.AddFlag("not_pick")
		self.topLine.Show()

		self.bottomLine = ui.Bar()
		self.bottomLine.SetParent(self)
		self.bottomLine.SetPosition(0, height - 1)
		self.bottomLine.SetSize(width, 1)
		self.bottomLine.SetColor(grp.GenerateColor(42 / 255.0, 28 / 255.0, 22 / 255.0, 1.0))
		self.bottomLine.AddFlag("not_pick")
		self.bottomLine.Show()
		self.Show()


class CustomPortsWindow(ui.BoardWithTitleBar):
	WIDTH = 500
	HEIGHT = 380
	ROW_HEIGHT = 27
	PANEL_WIDTH = 480
	PANEL_HEIGHT = 25
	QUESTION_WIDTH = 450
	UTILITY_BUTTON_WIDTH = 26
	TELEPORT_BUTTON_WIDTH = 92
	PAGE_BUTTON_WIDTH = 72
	ACTION_X = (282, 311, 340, 376)
	PAGE_GAP = 6

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName(_Locale("CUSTOM_PORTS_TITLE", "Saved locations"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()

		self.page = 0
		self.loading = False
		self.loaded = False
		self.unavailable = False
		self.error = ""
		self.pendingRows = {}
		self.loadRequested = False
		self.requestFailed = False
		self.records = {}
		self.offer = (SLOT_COUNT, 0, 0)
		self.children = []
		self.rows = []
		self.pageButtons = []
		self.inputDialog = None
		self.questionDialog = None
		self.dialogSlot = None
		self.dialogAction = None

		self.r1 = self._BuildR1()
		if self.r1 is None:
			self._Build()
		uiwheel.Pages(self, self.WheelPreviousPage, self.WheelNextPage)		# the wheel pages I-V
		self.Hide()

	def _BuildR1(self):
		# The R1 look (root/uicustomportsr1.py) unless Settings -> "Starý vzhled"; None = the original controls.
		try:
			import uicustomportsr1
		except Exception:
			return None
		try:
			return uicustomportsr1.Build(self, ICON_PATHS, PAGE_LABELS, ROWS_PER_PAGE, _Locale)
		except Exception:
			return None

	def Destroy(self):
		self._CloseInputDialog()
		self._CloseQuestionDialog()
		self.Hide()
		if getattr(self, "r1", None) is not None:
			self.r1.Destroy()
			self.r1 = None
		self.records = {}
		self.pendingRows = {}
		self.rows = []
		self.pageButtons = []
		self.children = []

	def _MakeText(self, parent, x, y, text, packedColor=None):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		if packedColor is not None:
			line.SetPackedFontColor(packedColor)
		line.SetText(text)
		line.Show()
		self.children.append(line)
		return line

	def _MakeButton(self, parent, x, y, width, family, text, event, args=(), icon=None, tooltip=""):
		button = CustomPortsButton(parent, x, y, width, family, text, icon, tooltip)
		button.SetEvent(event, *args)
		self.children.append(button)
		return button

	def _Build(self):
		self.instructionText = self._MakeText(self, 12, 34, "")

		for rowIndex in range(ROWS_PER_PAGE):
			panel = CustomPortsRow(
				self, 10, 55 + rowIndex * self.ROW_HEIGHT,
				self.PANEL_WIDTH, self.PANEL_HEIGHT,
			)
			self.children.append(panel)

			slotText = self._MakeText(panel, 8, 5, "", ROW_NUMBER_COLOR)
			name = self._MakeText(panel, 30, 5, "")
			coords = self._MakeText(panel, 163, 5, "", COORDINATE_COLOR)
			name.SetLimitWidth(128)
			coords.SetLimitWidth(110)
			saveText = _Locale("CUSTOM_PORTS_SAVE_HERE", "Save")
			editText = _Locale("CUSTOM_PORTS_RENAME", "Edit")
			deleteText = _Locale("CUSTOM_PORTS_DELETE", "Delete")
			teleportText = _Locale("CUSTOM_PORTS_TELEPORT", "Teleport")
			buttons = {
				"save": self._MakeButton(
					panel, self.ACTION_X[0], 1, self.UTILITY_BUTTON_WIDTH,
					"utility", "", self._Save, (rowIndex,), ICON_PATHS["save"], saveText,
				),
				"edit": self._MakeButton(
					panel, self.ACTION_X[1], 1, self.UTILITY_BUTTON_WIDTH,
					"utility", "", self._OpenRenameDialog, (rowIndex,), ICON_PATHS["edit"], editText,
				),
				"delete": self._MakeButton(
					panel, self.ACTION_X[2], 1, self.UTILITY_BUTTON_WIDTH,
					"utility", "", self._OpenDeleteDialog, (rowIndex,), ICON_PATHS["delete"], deleteText,
				),
				"teleport": self._MakeButton(
					panel, self.ACTION_X[3], 1, self.TELEPORT_BUTTON_WIDTH,
					"teleport", teleportText, self._Teleport, (rowIndex,), ICON_PATHS["teleport"],
				),
			}
			self.rows.append({
				"panel": panel,
				"slot": slotText,
				"name": name,
				"coords": coords,
				"buttons": buttons,
			})

		pageTotalWidth = PAGE_COUNT * self.PAGE_BUTTON_WIDTH + (PAGE_COUNT - 1) * self.PAGE_GAP
		pageStartX = (self.WIDTH - pageTotalWidth) // 2
		for pageIndex, label in enumerate(PAGE_LABELS):
			button = self._MakeButton(
				self,
				pageStartX + pageIndex * (self.PAGE_BUTTON_WIDTH + self.PAGE_GAP),
				340,
				self.PAGE_BUTTON_WIDTH,
				"page",
				label,
				self.SetPage,
				(pageIndex,),
			)
			self.pageButtons.append(button)

	def Open(self):
		self.Show()
		self.SetTop()
		self.error = ""
		self.requestFailed = False
		self._RequestList()
		self.Refresh()

	def Close(self):
		self._CloseInputDialog()
		self._CloseQuestionDialog()
		self.Hide()

	def Hide(self):
		if getattr(self, "inputDialog", None):
			self._CloseInputDialog()
		if getattr(self, "questionDialog", None):
			self._CloseQuestionDialog()
		ui.BoardWithTitleBar.Hide(self)

	def Toggle(self):
		if self.IsShow():
			self.Close()
		else:
			self.Open()

	def _IsAvailable(self):
		for functionName in (
			"IsCustomPortsAvailable", "GetCustomPortsOffer", "GetCustomPortRecords",
			"SendCustomPortsList", "SendCustomPortsSave", "SendCustomPortsRename",
			"SendCustomPortsDelete", "SendCustomPortsTeleport",
		):
			if not callable(getattr(net, functionName, None)):
				return False
		function = getattr(net, "IsCustomPortsAvailable", None)
		return bool(function())

	def _RequestList(self):
		if self.loaded or self.loadRequested:
			return
		self.unavailable = not self._IsAvailable()
		if self.unavailable:
			self.loading = False
			return
		function = getattr(net, "SendCustomPortsList", None)
		if function and function():
			self.requestFailed = False
			self.loading = True
			self.loadRequested = True
		else:
			self.requestFailed = True
			self.unavailable = True
			self.loading = False

	def SetPage(self, pageIndex):
		if pageIndex < 0 or pageIndex >= PAGE_COUNT:
			return
		self.page = pageIndex
		self.Refresh()

	def WheelPreviousPage(self):
		self.SetPage(self.page - 1)

	def WheelNextPage(self):
		self.SetPage(self.page + 1)

	def _AbsoluteSlot(self, rowIndex):
		return self.page * ROWS_PER_PAGE + rowIndex

	def _ReadState(self):
		if self.requestFailed:
			self.unavailable = True
			self.loaded = False
			self.loading = False
			self.records = {}
			return
		if not self._IsAvailable():
			self.unavailable = True
			self.loaded = False
			self.loading = False
			self.loadRequested = False
			self.records = {}
			return
		offerFunction = getattr(net, "GetCustomPortsOffer", None)
		recordsFunction = getattr(net, "GetCustomPortRecords", None)
		if not callable(offerFunction) or not callable(recordsFunction):
			self.unavailable = True
			self.loaded = False
			self.records = {}
			return
		self.unavailable = False
		self.offer = offerFunction()
		self.records = {}
		for record in recordsFunction():
			slot, mapIndex, x, y, name = record
			if 0 <= slot < SLOT_COUNT:
				self.records[slot] = (mapIndex, x, y, name)

	def Refresh(self):
		self._ReadState()

		if self.unavailable:
			status = _Locale("CUSTOM_PORTS_UNAVAILABLE", "Custom ports are not available.")
		elif self.error:
			status = _Locale("CUSTOM_PORTS_ERROR", "Error: %s") % self.error
		elif self.loading and not self.loaded:
			status = _Locale("CUSTOM_PORTS_LOADING", "Loading saved ports...")
		else:
			status = _Locale("CUSTOM_PORTS_INSTRUCTION", "Save a location and teleport to it.")
		self.instructionText.SetText(status)

		requestPending = bool(self.pendingRows)
		for rowIndex, row in enumerate(self.rows):
			slot = self._AbsoluteSlot(rowIndex)
			record = self.records.get(slot)
			showPending = self.pendingRows.get(slot, False)
			row["slot"].SetText("%d." % (slot + 1))
			row["name"].SetText(_Locale("CUSTOM_PORTS_ADD", "+Add+"))
			row["coords"].SetText("X: 0 Y: 0")
			for button in row["buttons"].values():
				button.Disable()
			if not self.loaded:
				continue
			if record:
				_mapIndex, x, y, name = record
				_mapName, baseX, baseY = background.GlobalPositionToMapInfo(x, y)
				localX = int(x - baseX) // 100
				localY = int(y - baseY) // 100
				row["name"].SetText(name)
				row["coords"].SetText("X: %d Y: %d" % (localX, localY))

			if showPending:
				row["coords"].SetText(_Locale("CUSTOM_PORTS_PENDING", "Pending..."))
			if not requestPending and not self.unavailable:
				row["buttons"]["save"].Enable()
				if record:
					for action in ("edit", "delete", "teleport"):
						row["buttons"][action].Enable()

		for pageIndex, button in enumerate(self.pageButtons):
			if pageIndex == self.page:
				button.Down()
			else:
				button.SetUp()
		if getattr(self, "r1", None) is not None:
			self.r1.Sync()

	def _RecordForRow(self, rowIndex):
		slot = self._AbsoluteSlot(rowIndex)
		return slot, self.records.get(slot)

	def _Save(self, rowIndex):
		slot, record = self._RecordForRow(rowIndex)
		if record:
			text = _Locale("CUSTOM_PORTS_CONFIRM_OVERWRITE", "Overwrite %s with your current position?") % record[3]
			self._OpenQuestionDialog("overwrite", slot, text)
		else:
			self._OpenInputDialog("save", slot, "")

	def _OpenRenameDialog(self, rowIndex):
		slot, record = self._RecordForRow(rowIndex)
		if record:
			self._OpenInputDialog("rename", slot, record[3])

	def _OpenInputDialog(self, action, slot, currentName):
		self._CloseQuestionDialog()
		self._CloseInputDialog()
		dialog = uiCommon.InputDialog()
		dialog.SetTitle(_Locale("CUSTOM_PORTS_NAME_TITLE", "Port name"))
		dialog.SetMaxLength(24)
		dialog.inputValue.SetText(currentName)
		dialog.SetAcceptEvent(ui.__mem_func__(self._AcceptInputDialog))
		dialog.SetCancelEvent(ui.__mem_func__(self._CloseInputDialog))
		self.inputDialog = dialog
		self.dialogAction = action
		self.dialogSlot = slot
		dialog.Open()

	def _AcceptInputDialog(self):
		if not self.inputDialog:
			return
		name = self.inputDialog.GetText().strip()
		action = self.dialogAction
		slot = self.dialogSlot
		self._CloseInputDialog()
		if not name:
			return
		if action == "save":
			self._Send(slot, "SendCustomPortsSave", slot, name)
		elif action == "rename":
			self._Send(slot, "SendCustomPortsRename", slot, name)

	def _CloseInputDialog(self):
		if self.inputDialog:
			self.inputDialog.Close()
		self.inputDialog = None
		self.dialogAction = None
		self.dialogSlot = None

	def _Teleport(self, rowIndex):
		slot, record = self._RecordForRow(rowIndex)
		if record:
			self._Send(slot, "SendCustomPortsTeleport", slot)

	def _OpenDeleteDialog(self, rowIndex):
		slot, record = self._RecordForRow(rowIndex)
		if record:
			text = _Locale("CUSTOM_PORTS_CONFIRM_DELETE", "Delete %s?") % record[3]
			self._OpenQuestionDialog("delete", slot, text)

	def _OpenQuestionDialog(self, action, slot, text):
		self._CloseInputDialog()
		self._CloseQuestionDialog()
		dialog = uiCommon.QuestionDialog()
		dialog.SetWidth(self.QUESTION_WIDTH)
		dialog.SetText(text)
		dialog.SetAcceptEvent(ui.__mem_func__(self._AcceptQuestionDialog))
		dialog.SetCancelEvent(ui.__mem_func__(self._CloseQuestionDialog))
		self.questionDialog = dialog
		self.dialogAction = action
		self.dialogSlot = slot
		dialog.Open()

	def _AcceptQuestionDialog(self):
		action = self.dialogAction
		slot = self.dialogSlot
		record = self.records.get(slot)
		self._CloseQuestionDialog()
		if action == "overwrite" and record:
			self._Send(slot, "SendCustomPortsSave", slot, record[3])
		elif action == "delete":
			self._Send(slot, "SendCustomPortsDelete", slot)

	def _CloseQuestionDialog(self):
		if self.questionDialog:
			self.questionDialog.Close()
		self.questionDialog = None
		self.dialogAction = None
		self.dialogSlot = None

	def _Send(self, slot, functionName, *args):
		function = getattr(net, functionName, None)
		if callable(function) and function(*args):
			self.pendingRows[slot] = functionName != "SendCustomPortsTeleport"
			self.error = ""
			self.Refresh()
			return True
		else:
			self.OnError(0, getattr(net, "CUSTOM_PORT_ERROR_UNAVAILABLE", 2))
		return False

	def OnChanged(self):
		self.requestFailed = False
		self.pendingRows = {}
		if self.loadRequested:
			self.loading = False
			self.loaded = True
			self.loadRequested = False
		elif self.IsShow() and self._IsAvailable() and not self.loaded and not self.error:
			self._RequestList()
		self.Refresh()

	def OnError(self, requestID, reason):
		self.requestFailed = False
		self.pendingRows = {}
		self.loading = False
		self.loadRequested = False
		keys = {
			getattr(net, "CUSTOM_PORT_ERROR_DISABLED", 1): "CUSTOM_PORTS_ERROR_DISABLED",
			getattr(net, "CUSTOM_PORT_ERROR_UNAVAILABLE", 2): "CUSTOM_PORTS_ERROR_UNAVAILABLE",
			getattr(net, "CUSTOM_PORT_ERROR_INVALID_REQUEST", 3): "CUSTOM_PORTS_ERROR_INVALID_REQUEST",
			getattr(net, "CUSTOM_PORT_ERROR_INVALID_NAME", 4): "CUSTOM_PORTS_ERROR_INVALID_NAME",
			getattr(net, "CUSTOM_PORT_ERROR_SLOT_EMPTY", 5): "CUSTOM_PORTS_ERROR_SLOT_EMPTY",
			getattr(net, "CUSTOM_PORT_ERROR_MAP_FORBIDDEN", 6): "CUSTOM_PORTS_ERROR_MAP_FORBIDDEN",
			getattr(net, "CUSTOM_PORT_ERROR_INVALID_STATE", 7): "CUSTOM_PORTS_ERROR_INVALID_STATE",
			getattr(net, "CUSTOM_PORT_ERROR_RATE_LIMITED", 8): "CUSTOM_PORTS_ERROR_RATE_LIMITED",
			getattr(net, "CUSTOM_PORT_ERROR_TARGET_UNAVAILABLE", 9): "CUSTOM_PORTS_ERROR_TARGET_UNAVAILABLE",
			getattr(net, "CUSTOM_PORT_ERROR_LEVEL_TOO_LOW", 10): "CUSTOM_PORTS_ERROR_LEVEL_TOO_LOW",
			getattr(net, "CUSTOM_PORT_ERROR_INSUFFICIENT_YANG", 11): "CUSTOM_PORTS_ERROR_INSUFFICIENT_YANG",
			getattr(net, "CUSTOM_PORT_ERROR_COOLDOWN", 12): "CUSTOM_PORTS_ERROR_COOLDOWN",
			getattr(net, "CUSTOM_PORT_ERROR_INTERNAL", 13): "CUSTOM_PORTS_ERROR_INTERNAL",
		}
		fallbacks = {
			"CUSTOM_PORTS_ERROR_DISABLED": "Custom ports are disabled.",
			"CUSTOM_PORTS_ERROR_UNAVAILABLE": "Custom ports are unavailable.",
			"CUSTOM_PORTS_ERROR_INVALID_REQUEST": "Invalid request.",
			"CUSTOM_PORTS_ERROR_INVALID_NAME": "Invalid port name.",
			"CUSTOM_PORTS_ERROR_SLOT_EMPTY": "This port slot is empty.",
			"CUSTOM_PORTS_ERROR_MAP_FORBIDDEN": "Ports cannot be used on this map.",
			"CUSTOM_PORTS_ERROR_INVALID_STATE": "You cannot use a port right now.",
			"CUSTOM_PORTS_ERROR_RATE_LIMITED": "Please wait before trying again.",
			"CUSTOM_PORTS_ERROR_TARGET_UNAVAILABLE": "The saved destination is unavailable.",
			"CUSTOM_PORTS_ERROR_LEVEL_TOO_LOW": "Your level is too low.",
			"CUSTOM_PORTS_ERROR_INSUFFICIENT_YANG": "You do not have enough Yang.",
			"CUSTOM_PORTS_ERROR_COOLDOWN": "The teleport cooldown is active.",
			"CUSTOM_PORTS_ERROR_INTERNAL": "The server could not complete the request.",
		}
		key = keys.get(reason, "CUSTOM_PORTS_ERROR_INTERNAL")
		self.error = _Locale(key, fallbacks[key])
		chat.AppendChat(chat.CHAT_TYPE_INFO, self.error)
		self.Refresh()

	def OnPressEscapeKey(self):
		self.Close()
		return True
