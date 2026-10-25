import ime
import localeInfo
import ui
import wndMgr


class SplitItemDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'acceptButton')
		self.maxValue = 0
		self.eventAccept = None
		self.itemGlobalSlotIndex = -1
		self.splitAllCheckBox = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadDialog(self):
		try:
			loader = ui.PythonScriptLoader()
			loader.LoadScriptFile(self, "UIScript/SplitItemDialog.py")
		except:
			import exception
			exception.Abort("SplitItemDialog.LoadDialog.LoadScript")

		try:
			self.board = self.GetChild("board")
			self.maxValueTextLine = self.GetChild("max_value")
			self.pickValueEditLine = self.GetChild("item_value")
			self.acceptButton = self.GetChild("accept_button")
			self.cancelButton = self.GetChild("cancel_button")
		except:
			import exception
			exception.Abort("SplitItemDialog.LoadDialog.BindObject")

		self.splitAllCheckBox = ui.CheckBox_N()
		self.splitAllCheckBox.SetParent(self.board)
		self.splitAllCheckBox.SetPosition(16, 54)
		self.splitAllCheckBox.SetText(localeInfo.INVENTORY_SPLIT_ALL)
		self.splitAllCheckBox.SetChecked(False)
		self.splitAllCheckBox.Show()

		self.pickValueEditLine.SetReturnEvent(ui.__mem_func__(self.OnAccept))
		self.pickValueEditLine.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.acceptButton.SetEvent(ui.__mem_func__(self.OnAccept))
		self.cancelButton.SetEvent(ui.__mem_func__(self.Close))
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))

	def Destroy(self):
		self.ClearDictionary()
		self.eventAccept = None
		self.maxValue = 0
		self.itemGlobalSlotIndex = -1
		self.splitAllCheckBox = None
		self.board = None
		self.maxValueTextLine = None
		self.pickValueEditLine = None
		self.acceptButton = None
		self.cancelButton = None

	def SetTitleName(self, text):
		self.board.SetTitleName(text)

	def SetAcceptEvent(self, event):
		self.eventAccept = event

	def IsSplitAllChecked(self):
		return self.splitAllCheckBox and self.splitAllCheckBox.IsChecked()

	def Open(self, maxValue):
		width = self.GetWidth()
		mouseX, mouseY = wndMgr.GetMousePosition()
		if mouseX + width // 2 > wndMgr.GetScreenWidth():
			xPos = wndMgr.GetScreenWidth() - width
		elif mouseX - width // 2 < 0:
			xPos = 0
		else:
			xPos = mouseX - width // 2

		self.SetPosition(xPos, mouseY - self.GetHeight() - 20)
		self.maxValueTextLine.SetText(" / " + str(maxValue))
		self.pickValueEditLine.SetText("1")
		self.pickValueEditLine.SetFocus()
		ime.SetCursorPosition(1)
		self.maxValue = maxValue
		self.splitAllCheckBox.SetChecked(False)
		self.Show()
		self.SetTop()

	def Close(self):
		if self.splitAllCheckBox:
			self.splitAllCheckBox.SetChecked(False)
		if self.pickValueEditLine:
			self.pickValueEditLine.KillFocus()
		self.Hide()

	def OnAccept(self):
		text = self.pickValueEditLine.GetText()
		if text and text.isdigit():
			count = min(int(text), self.maxValue)
			if count > 0 and self.eventAccept:
				self.eventAccept(count)
		self.Close()
