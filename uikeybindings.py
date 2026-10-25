import app
import ui
import uiCommon
import uiScriptLocale

import keybindingcore
import keybindings


BUTTON_PATH = "d:/ymir work/ui/public/"
OPTION_IMAGE_PATH = "d:/ymir work/ui/game/crimson_ember/gameoption/"


def _locale(key, fallback):
	return getattr(uiScriptLocale, key, fallback)


class BindingSession(object):
	def __init__(self, manager):
		self.manager = manager
		self.state = None

	def begin(self):
		self.state = self.manager.clone_state()
		return self.state

	def assign(self, action_id, shortcut, replace=False):
		if self.state is None:
			self.begin()
		return self.state.assign(action_id, shortcut, replace=replace)

	def restore_defaults(self):
		if self.state is None:
			self.begin()
		self.state.reset_defaults()

	def save(self):
		if self.state is None:
			self.begin()
		self.manager.save_state(self.state)
		self.state = self.manager.clone_state()

	def discard(self):
		self.state = self.manager.clone_state()


class ShortcutCaptureDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.manager = None
		self.callback = None
		self._LoadWindow()

	def __del__(self):
		self.Close()
		ui.ScriptWindow.__del__(self)

	def _LoadWindow(self):
		# Overridable: the settings kit look builds the same controls (board, capturedShortcut, cancelButton)
		# without this script (uisettingsc9dialogs).
		loader = ui.PythonScriptLoader()
		loader.LoadScriptFile(self, "UIScript/keybindingcapturedialog.py")
		self.board = self.GetChild("Board")
		self.capturedShortcut = self.GetChild("CapturedShortcut")
		self.cancelButton = self.GetChild("CancelButton")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.cancelButton.SAFE_SetEvent(self.Close)

	def Open(self, manager, callback):
		self.manager = manager
		self.callback = callback
		self.capturedShortcut.SetText("...")
		manager.set_capture_active(True)
		self.SetCenterPosition()
		self.Show()
		self.SetTop()
		self.SetFocus()

	def Close(self):
		if self.manager:
			self.manager.set_capture_active(False)
		self.KillFocus()
		self.manager = None
		self.callback = None
		self.Hide()

	def Destroy(self):
		self.Close()
		self.ClearDictionary()
		self.board = None
		self.capturedShortcut = None
		self.cancelButton = None

	def __HeldModifierText(self):
		if not self.manager:
			return "..."
		labels = {"CTRL": "Ctrl", "SHIFT": "Shift", "ALT": "Alt"}
		held = []
		for name in keybindingcore.MODIFIER_ORDER:
			if any(
				app.IsPressed(value)
				for value in self.manager._modifier_diks[name]
			):
				held.append(labels[name])
		return "+".join(held) + ("+..." if held else "...")

	def OnUpdate(self):
		if self.IsShow() and self.manager:
			self.capturedShortcut.SetText(self.__HeldModifierText())

	def OnKeyDown(self, key):
		if key == app.DIK_ESC:
			self.Close()
			return True
		if not self.manager or not self.callback:
			return False
		if key == app.DIK_DELETE:
			if self.callback(None) is not False:
				self.Close()
			return True

		shortcut = self.manager.shortcut_from_dik(key)
		if shortcut is None:
			self.capturedShortcut.SetText(self.__HeldModifierText())
			return True
		self.capturedShortcut.SetText(shortcut.display())
		if self.callback(shortcut) is not False:
			self.Close()
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True


class ConflictDialog(uiCommon.QuestionDialog2):
	def __init__(self):
		uiCommon.QuestionDialog2.__init__(self)
		self.replaceEvent = None
		self.cancelEvent = None

	def OpenConflict(self, message, replace_event, cancel_event):
		self.replaceEvent = replace_event
		self.cancelEvent = cancel_event
		self.SetText1(message)
		self.SetText2("")
		self.SetAcceptText(_locale("KEYBIND_REPLACE", "Replace"))
		self.SetCancelText(_locale("KEYBIND_CANCEL", "Cancel"))
		self.SetAcceptEvent(ui.__mem_func__(self.__Replace))
		self.SetCancelEvent(ui.__mem_func__(self.__Cancel))
		self.Open()

	def __Replace(self):
		callback = self.replaceEvent
		self.Close()
		if callback:
			callback()

	def __Cancel(self):
		callback = self.cancelEvent
		self.Close()
		if callback:
			callback()


class KeybindingsPage(object):
	def __init__(self, manager=None, auto_save=False):
		self.auto_save = auto_save
		self.dirty = False
		self.manager = manager or keybindings.GetManager()
		self.session = BindingSession(self.manager) if self.manager else None
		self.window = None
		self.bindingList = None
		self.bindingScrollBar = None
		self.saveButton = None
		self.restoreButton = None
		self.rows = []
		self.contentHeight = 0
		self.maxStartIndex = 0
		self.bindingButtons = {}
		self.captureDialog = None
		self.conflictDialog = None
		self.restoreDialog = None
		self.popupDialog = None
		self.pendingConflict = None

	def Bind(self, window):
		self.window = window
		self.bindingList = window.GetChild("BindingList")
		self.bindingScrollBar = window.GetChild("BindingScrollBar")
		self.saveButton = window.GetChild("SaveButton")
		self.restoreButton = window.GetChild("RestoreDefaultsButton")
		self.bindingScrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.bindingList.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)
		self.saveButton.SAFE_SetEvent(self.Save)
		self.restoreButton.SAFE_SetEvent(self.RestoreDefaults)

		if not self.manager:
			self.saveButton.Disable()
			self.restoreButton.Disable()
			return

		self.captureDialog = ShortcutCaptureDialog()
		self.conflictDialog = ConflictDialog()
		self.restoreDialog = uiCommon.QuestionDialog()
		self.popupDialog = uiCommon.PopupDialog()
		self.__BuildRows()
		self.BeginSession()

	def __BuildRows(self):
		self.contentHeight = 0
		for category_key, actions in self.manager.actions_by_category():
			header = ui.ExpandedImageBox()
			header.SetParent(self.bindingList)
			header.LoadImage(OPTION_IMAGE_PATH + "option_title.tga")
			header.SetScale(2.0, 1.0)
			self.__PrepareListWidget(header)
			header.Show()

			header_text = ui.TextLine()
			header_text.SetParent(header)
			header_text.SetPosition(17, 4)
			header_text.SetText(_locale(category_key, category_key))
			self.__PrepareListWidget(header_text)
			header_text.Show()
			header.label = header_text
			self.__RegisterRow(header, 28)

			for action in actions:
				row = ui.Window()
				row.SetParent(self.bindingList)
				row.SetSize(352, 28)
				self.__PrepareListWidget(row)

				label = ui.TextLine()
				label.SetParent(row)
				label.SetPosition(14, 7)
				label.SetText(_locale(action.locale_key, action.action_id))
				self.__PrepareListWidget(label)
				label.Show()

				button = ui.Button()
				button.SetParent(row)
				button.SetPosition(172, 2)
				button.SetUpVisual(BUTTON_PATH + "large_button_01.sub")
				button.SetOverVisual(BUTTON_PATH + "large_button_02.sub")
				button.SetDownVisual(BUTTON_PATH + "large_button_03.sub")
				button.SAFE_SetEvent(self.BeginCapture, action.action_id)
				self.__PrepareListWidget(button)
				button.Show()

				row.label = label
				row.button = button
				row.Show()
				self.bindingButtons[action.action_id] = button
				self.__RegisterRow(row, 30)

		self.__RefreshScrollBar()

	def __PrepareListWidget(self, widget):
		widget.SetClippingMaskWindow(self.bindingList)
		widget.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)

	def __RegisterRow(self, row, height):
		self.rows.append((row, height))
		row.SetPosition(0, self.contentHeight)
		self.contentHeight += height

	def __GetMaxStartIndex(self, viewport_height):
		if self.contentHeight <= viewport_height:
			return 0

		visible_height = 0
		start_index = len(self.rows)
		while start_index > 0:
			row_height = self.rows[start_index - 1][1]
			if visible_height + row_height > viewport_height:
				break
			visible_height += row_height
			start_index -= 1
		return start_index

	def __RefreshScrollBar(self):
		viewport_height = self.bindingList.GetHeight()
		self.maxStartIndex = self.__GetMaxStartIndex(viewport_height)
		if self.maxStartIndex:
			self.bindingScrollBar.SetMiddleBarSize(
				min(1.0, float(viewport_height) / float(self.contentHeight))
			)
			self.bindingScrollBar.SetScrollStep(
				1.0 / float(self.maxStartIndex)
			)
			self.bindingScrollBar.SetPos(0.0)
			self.bindingScrollBar.Show()
		else:
			self.bindingScrollBar.SetPos(0.0)
			self.bindingScrollBar.Hide()
		self.__OnScroll()

	def __OnScroll(self):
		start_index = int(
			self.maxStartIndex * self.bindingScrollBar.GetPos() + 0.5
		)
		for row, unused_height in self.rows:
			row.Hide()

		viewport_height = self.bindingList.GetHeight()
		y = 0
		for row, row_height in self.rows[start_index:]:
			if y + row_height > viewport_height:
				break
			row.SetPosition(0, y)
			row.Show()
			y += row_height

	def OnMouseWheel(self, delta):
		if not self.bindingScrollBar or not self.bindingScrollBar.IsShow():
			return False
		if delta > 0:
			self.bindingScrollBar.OnUp()
		else:
			self.bindingScrollBar.OnDown()
		return True

	def BeginSession(self):
		if not self.session:
			return
		self.__CloseDialogs()
		self.session.begin()
		self.RefreshRows()

	def RefreshRows(self):
		if not self.session or self.session.state is None:
			return
		unbound = _locale("KEYBIND_UNBOUND", "Unbound")
		for action_id, button in self.bindingButtons.items():
			shortcut = self.session.state.get(action_id)
			button.SetText(unbound if shortcut is None else shortcut.display())

	def BeginCapture(self, action_id):
		if self.captureDialog:
			self.captureDialog.Open(
				self.manager,
				lambda shortcut, selected=action_id: self.ApplyCaptured(
					selected,
					shortcut,
				),
			)

	def ApplyCaptured(self, action_id, shortcut):
		try:
			conflict = self.session.assign(action_id, shortcut)
		except keybindingcore.ReservedShortcutError:
			if action_id in getattr(keybindings, "SPACE_IN_MINIGAME_ACTIONS", ()) and shortcut == keybindingcore.Shortcut("SPACE"):
				self.__ShowPopup(
					_locale(
						"KEYBIND_SPACE_IN_MINIGAME_MESSAGE",
						"Space already hits in the minigame, no need to bind it.",
					)
				)
				return False
			self.__ShowPopup(
				_locale(
					"KEYBIND_RESERVED_MESSAGE",
					"This shortcut is reserved.",
				)
			)
			return False

		if conflict is not None:
			self.pendingConflict = (action_id, shortcut)
			owner = self.manager.get_action(conflict.action_id)
			owner_name = _locale(owner.locale_key, owner.action_id)
			message = _locale(
				"KEYBIND_CONFLICT_MESSAGE",
				"Shortcut is already used by: %s. Replace it?",
			)
			try:
				message = message % owner_name
			except TypeError:
				message = "%s %s" % (message, owner_name)
			self.conflictDialog.OpenConflict(
				message,
				self.__ReplaceConflict,
				self.__CancelConflict,
			)
			return True

		self.dirty = True
		self.RefreshRows()
		return self.Save() if self.auto_save else True

	def __ReplaceConflict(self):
		if self.pendingConflict:
			action_id, shortcut = self.pendingConflict
			self.session.assign(action_id, shortcut, replace=True)
			self.dirty = True
			if self.auto_save:
				self.Save()
		self.pendingConflict = None
		self.RefreshRows()

	def __CancelConflict(self):
		self.pendingConflict = None

	def RestoreDefaults(self):
		if not self.restoreDialog:
			return
		self.restoreDialog.SetText(
			_locale(
				"KEYBIND_RESTORE_CONFIRM",
				"Restore default shortcuts?",
			)
		)
		self.restoreDialog.SetAcceptText(_locale("KEYBIND_RESTORE_DEFAULTS", "Restore defaults"))
		self.restoreDialog.SetCancelText(_locale("KEYBIND_CANCEL", "Cancel"))
		self.restoreDialog.SetAcceptEvent(ui.__mem_func__(self.__ConfirmRestore))
		self.restoreDialog.SetCancelEvent(ui.__mem_func__(self.restoreDialog.Close))
		self.restoreDialog.Open()

	def __ConfirmRestore(self):
		self.restoreDialog.Close()
		self.session.restore_defaults()
		self.dirty = True
		if self.auto_save:
			self.Save()
		self.RefreshRows()

	def Save(self):
		if not self.session or (self.auto_save and not self.dirty):
			return True
		try:
			self.session.save()
		except (OSError, UnicodeError, ValueError):
			self.__ShowPopup(
				_locale(
					"KEYBIND_SAVE_FAILED",
					"The shortcuts could not be saved.",
				)
			)
			return False
		self.dirty = False
		self.RefreshRows()
		return True

	def __ShowPopup(self, message):
		if self.popupDialog:
			self.popupDialog.SetText(message)
			self.popupDialog.Open()

	def Discard(self):
		if not self.session:
			return
		self.__CloseDialogs()
		self.session.discard()
		self.dirty = False
		self.RefreshRows()

	def __CloseDialogs(self):
		if self.captureDialog:
			self.captureDialog.Close()
		if self.conflictDialog:
			self.conflictDialog.Close()
		if self.restoreDialog:
			self.restoreDialog.Close()
		if self.popupDialog:
			self.popupDialog.Close()
		self.pendingConflict = None

	def Destroy(self):
		self.Discard()
		if self.captureDialog:
			self.captureDialog.Destroy()
		for row, unused_height in self.rows:
			row.Hide()
		self.rows = []
		self.bindingButtons = {}
		self.captureDialog = None
		self.conflictDialog = None
		self.restoreDialog = None
		self.popupDialog = None
		self.bindingList = None
		if self.bindingScrollBar:
			self.bindingScrollBar.SetScrollEvent(lambda: None)
		self.bindingScrollBar = None
		self.saveButton = None
		self.restoreButton = None
		self.window = None
