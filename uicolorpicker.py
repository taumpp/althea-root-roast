import grp
import ui
import wndMgr


def _ClampByte(value):
	return max(0, min(255, int(value)))


def PackRgb(red, green, blue):
	return (_ClampByte(red) << 16) | (_ClampByte(green) << 8) | _ClampByte(blue)


def UnpackRgb(rgb):
	rgb = int(rgb) & 0xFFFFFF
	return ((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF)


def RgbToHex(rgb):
	return "#{:06X}".format(int(rgb) & 0xFFFFFF)


def HexToRgb(value):
	value = str(value).strip()
	if value.startswith("#"):
		value = value[1:]
	if len(value) != 6:
		raise ValueError("RGB color must contain exactly six hexadecimal digits")
	try:
		return int(value, 16)
	except ValueError:
		raise ValueError("RGB color contains a non-hexadecimal digit")


class ColorPickerDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'confirmButton')
		self.isLoaded = False
		self.selectedRgb = 0
		self.onConfirm = None
		self.onDefault = None
		self._updatingHex = False
		self._pickerHover = False

	def _LoadWindow(self):
		if self.isLoaded:
			return

		self.isLoaded = True
		try:
			loader = ui.PythonScriptLoader()
			loader.LoadScriptFile(self, "UIScript/ColorPickerDialog.py")
			self.board = self.GetChild("Board")
			self.pickerImage = self.GetChild("ColorPickerImage")
			self.pickerButton = self.GetChild("ColorPickerButton")
			self.selectedDot = self.GetChild("SelectedDot")
			self.hexEditLine = self.GetChild("HexEditLine")
			self.colorSwatch = self.GetChild("ColorSwatch")
			self.confirmButton = self.GetChild("ConfirmButton")
			self.defaultButton = self.GetChild("DefaultButton")
			self.cancelButton = self.GetChild("CancelButton")
		except:
			import exception
			exception.Abort("ColorPickerDialog._LoadWindow")

		self.board.SetCloseEvent(ui.__mem_func__(self.Cancel))
		self.pickerButton.SetEvent(ui.__mem_func__(self.SelectHoveredColor))
		self.selectedDot.SetEvent(ui.__mem_func__(self.SelectHoveredColor), "mouse_click")
		self.hexEditLine.OnIMEUpdate = ui.__mem_func__(self.OnUpdateHex)
		self.hexEditLine.SetReturnEvent(ui.__mem_func__(self.Confirm))
		self.hexEditLine.SetEscapeEvent(ui.__mem_func__(self.Cancel))
		self.confirmButton.SetEvent(ui.__mem_func__(self.Confirm))
		self.defaultButton.SetEvent(ui.__mem_func__(self.UseDefault))
		self.cancelButton.SetEvent(ui.__mem_func__(self.Cancel))
		self.selectedDot.Hide()

	def Open(self, initialRgb, onConfirm, onDefault):
		self._LoadWindow()
		self.selectedRgb = int(initialRgb) & 0xFFFFFF
		self.onConfirm = onConfirm
		self.onDefault = onDefault
		self._pickerHover = False
		self.selectedDot.Hide()
		self._RefreshColor()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def _ClearCallbacks(self):
		self.onConfirm = None
		self.onDefault = None

	def Confirm(self):
		callback = self.onConfirm
		selectedRgb = self.selectedRgb
		self._ClearCallbacks()
		self.Hide()
		if callback:
			callback(selectedRgb)
		return True

	def UseDefault(self):
		callback = self.onDefault
		self._ClearCallbacks()
		self.Hide()
		if callback:
			callback()
		return True

	def Cancel(self):
		self._ClearCallbacks()
		self.Hide()
		return True

	def Close(self):
		return self.Cancel()

	def _RefreshColor(self):
		red, green, blue = UnpackRgb(self.selectedRgb)
		self.colorSwatch.SetColor(grp.GenerateColor(red / 255.0, green / 255.0, blue / 255.0, 1.0))
		self._updatingHex = True
		self.hexEditLine.SetText(RgbToHex(self.selectedRgb))
		self._updatingHex = False

	def OnUpdateHex(self):
		ui.EditLine.OnIMEUpdate(self.hexEditLine)
		if self._updatingHex:
			return
		try:
			self.selectedRgb = HexToRgb(self.hexEditLine.GetText())
		except ValueError:
			return
		self.selectedDot.Hide()
		red, green, blue = UnpackRgb(self.selectedRgb)
		self.colorSwatch.SetColor(grp.GenerateColor(red / 255.0, green / 255.0, blue / 255.0, 1.0))

	def _ColorUnderMouse(self):
		xMouse, yMouse = wndMgr.GetRealMousePosition()
		red, green, blue = wndMgr.GetColorAtPosition(xMouse, yMouse)
		return PackRgb(red, green, blue)

	def _MoveSelectedDot(self):
		xImage, yImage = self.pickerImage.GetGlobalPosition()
		xMouse, yMouse = wndMgr.GetMousePosition()
		xLocal = max(0, min(255, xMouse - xImage))
		yLocal = max(0, min(255, yMouse - yImage))
		self.selectedDot.SetPosition(xLocal - 6, yLocal - 6)
		self.selectedDot.Show()

	def SelectHoveredColor(self):
		self.selectedRgb = self._ColorUnderMouse()
		self._MoveSelectedDot()
		self._RefreshColor()

	def OnUpdate(self):
		if not self.isLoaded:
			return
		isHovering = self.pickerButton.IsIn() or self.selectedDot.IsIn()
		if not isHovering:
			if self._pickerHover:
				self._RefreshColor()
			self._pickerHover = False
			return
		self._pickerHover = True
		previewRgb = self._ColorUnderMouse()
		red, green, blue = UnpackRgb(previewRgb)
		self.colorSwatch.SetColor(grp.GenerateColor(red / 255.0, green / 255.0, blue / 255.0, 1.0))

	def OnPressEscapeKey(self):
		return self.Cancel()
