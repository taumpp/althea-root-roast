import ui
import localeInfo
import app
import ime
import uiScriptLocale
import chat
import osfInfo

if app.ENABLE_NEW_DROP_DIALOG:
	import player
	import item, uiToolTip

import shop

import re

class PopupDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadDialog()
		self.acceptEvent = lambda *arg: None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/PopupDialog.py")

			self.board = self.GetChild("board")
			self.message = self.GetChild("message")
			self.accceptButton = self.GetChild("accept")
			self.accceptButton.SetEvent(ui.__mem_func__(self.Close))

		except:
			import exception
			exception.Abort("PopupDialog.LoadDialog.BindObject")

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()
		self.acceptEvent()

	def Destroy(self):
		self.Close()
		self.ClearDictionary()

	def SetWidth(self, width):
		height = self.GetHeight()
		self.SetSize(width, height)

		if self.board.IsRTL():
			self.board.SetPosition(width, 0)

		self.board.SetSize(width, height)
		self.SetCenterPosition()
		self.UpdateRect()

	def SetText(self, text):
		self.message.SetText(text)

	def SetAcceptEvent(self, event):
		self.acceptEvent = event

	def SetButtonName(self, name):
		self.accceptButton.SetText(name)

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnIMEReturn(self):
		self.Close()
		return True

	def GetTextSize(self):
		if self.message:
			return self.message.GetTextSize()

		return (0,0)

	def GetLineHeight(self):
		if self.message:
			return self.message.GetLineHeight()

		return 0

	def SetLineHeight(self, Height):
		self.message.SetLineHeight(Height)

	def GetTextLineCount(self):
		return self.message.GetTextLineCount()

class InputDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/inputdialog.py")

		getObject = self.GetChild
		self.board = getObject("Board")
		self.acceptButton = getObject("AcceptButton")
		self.cancelButton = getObject("CancelButton")
		self.inputSlot = getObject("InputSlot")
		self.inputValue = getObject("InputValue")

	def Open(self):
		self.inputValue.SetFocus()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.ClearDictionary()
		self.board = None
		self.acceptButton = None
		self.cancelButton = None
		self.inputSlot = None
		self.inputValue = None
		self.Hide()

	def SetTitle(self, name):
		self.board.SetTitleName(name)

	def SetNumberMode(self):
		self.inputValue.SetNumberMode()

	def SetUseCodePage(self, bUse = True):
		self.inputValue.SetUseCodePage(bUse)

	def SetSecretMode(self):
		self.inputValue.SetSecret()

	def SetFocus(self):
		self.inputValue.SetFocus()

	def SetMaxLength(self, length):
		width = length * 6 + 10
		self.SetBoardWidth(max(width + 50, 160))
		self.SetSlotWidth(width)
		self.inputValue.SetMax(length)

	def SetSlotWidth(self, width):
		self.inputSlot.SetSize(width, self.inputSlot.GetHeight())
		self.inputValue.SetSize(width, self.inputValue.GetHeight())
		if self.IsRTL():
			self.inputValue.SetPosition(self.inputValue.GetWidth(), 0)

	def SetBoardWidth(self, width):
		self.SetSize(max(width + 50, 160), self.GetHeight())
		self.board.SetSize(max(width + 50, 160), self.GetHeight())
		if self.IsRTL():
			self.board.SetPosition(self.board.GetWidth(), 0)
		self.UpdateRect()

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)
		self.inputValue.OnIMEReturn = event

	def SetCancelEvent(self, event):
		self.board.SetCloseEvent(event)
		self.cancelButton.SetEvent(event)
		self.inputValue.OnPressEscapeKey = event

	def GetText(self):
		return self.inputValue.GetText()

class QuestionDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog.py")

		self.board = self.GetChild("board")
		self.textLine = self.GetChild("message")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()

	def SetWidth(self, width):
		height = self.GetHeight()
		self.SetSize(width, height)

		if self.board.IsRTL():
			self.board.SetPosition(width, 0)

		self.board.SetSize(width, height)
		self.SetCenterPosition()
		self.UpdateRect()

	def SAFE_SetAcceptEvent(self, event):
		self.acceptButton.SAFE_SetEvent(event)

	def SAFE_SetCancelEvent(self, event):
		self.cancelButton.SAFE_SetEvent(event)

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)

	def SetCancelEvent(self, event):
		self.cancelButton.SetEvent(event)

	def SetText(self, text):
		self.textLine.SetText(text)
		
		if text:
			self.textLine.SetPosition(0, 38 - (self.textLine.GetTextLineCount() - 1) * 10)

	def SetAcceptText(self, text):
		self.acceptButton.SetText(text)

	def SetCancelText(self, text):
		self.cancelButton.SetText(text)

	def OnPressEscapeKey(self):
		self.Close()
		self.cancelButton.CallEvent()
		return True

	def GetTextSize(self):
		if self.textLine:
			return self.textLine.GetTextSize()

		return (0,0)

	def GetLineHeight(self):
		if self.textLine:
			return self.textLine.GetLineHeight()

		return 0

	def SetLineHeight(self, Height):
		self.textLine.SetLineHeight(Height)

	def GetTextLineCount(self):
		return self.textLine.GetTextLineCount()

class QuestionDialog2(QuestionDialog):
	def __init__(self):
		QuestionDialog.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		QuestionDialog.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog2.py")

		self.board = self.GetChild("board")
		self.textLine1 = self.GetChild("message1")
		self.textLine2 = self.GetChild("message2")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def SetText1(self, text):
		self.textLine1.SetText(text)

	def SetText2(self, text):
		self.textLine2.SetText(text)
		
	if app.ENABLE_GROWTH_PET_SYSTEM:
		def GetTextSize1(self):
			if self.textLine1:
				return self.textLine1.GetTextSize()
				
			return (0,0)
			
		def GetTextSize2(self):
			if self.textLine2:
				return self.textLine2.GetTextSize()
				
			return (0,0)


class QuestionDialog3(QuestionDialog):
	def __init__(self):
		QuestionDialog.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		QuestionDialog.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog3.py")

		self.board = self.GetChild("board")
		self.textLine1 = self.GetChild("message1")
		self.textLine2 = self.GetChild("message2")
		self.textLine3 = self.GetChild("message3")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def SetText1(self, text):
		self.textLine1.SetText(text)

	def SetText2(self, text):
		self.textLine2.SetText(text)
		
	def SetText3(self, text):
		self.textLine3.SetText(text)
		
	if app.ENABLE_GROWTH_PET_SYSTEM:
		def GetTextSize1(self):
			if self.textLine1:
				return self.textLine1.GetTextSize()
				
			return (0,0)
			
		def GetTextSize2(self):
			if self.textLine2:
				return self.textLine2.GetTextSize()
				
			return (0,0)

class InputDialogWithDescription(InputDialog):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__CreateDialog()

	def __del__(self):
		InputDialog.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		if localeInfo.IsARABIC() :
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "inputdialogwithdescription.py")
		else:
			pyScrLoader.LoadScriptFile(self, "uiscript/inputdialogwithdescription.py")

		try:
			getObject = self.GetChild
			self.board = getObject("Board")
			self.acceptButton = getObject("AcceptButton")
			self.cancelButton = getObject("CancelButton")
			self.inputSlot = getObject("InputSlot")
			self.inputValue = getObject("InputValue")
			self.description = getObject("Description")

		except:
			import exception
			exception.Abort("InputDialogWithDescription.LoadBoardDialog.BindObject")

	def SetDescription(self, text):
		self.description.SetText(text)

class InputDialogWithDescription2(InputDialog):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__CreateDialog()

	def __del__(self):
		InputDialog.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/inputdialogwithdescription2.py")

		try:
			getObject = self.GetChild
			self.board = getObject("Board")
			self.acceptButton = getObject("AcceptButton")
			self.cancelButton = getObject("CancelButton")
			self.inputSlot = getObject("InputSlot")
			self.inputValue = getObject("InputValue")
			self.description1 = getObject("Description1")
			self.description2 = getObject("Description2")

		except:
			import exception
			exception.Abort("InputDialogWithDescription.LoadBoardDialog.BindObject")

	def SetDescription1(self, text):
		self.description1.SetText(text)

	def SetDescription2(self, text):
		self.description2.SetText(text)

class QuestionDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog.py")

		self.board = self.GetChild("board")
		self.textLine = self.GetChild("message")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()

	def SetWidth(self, width):
		height = self.GetHeight()
		self.SetSize(width, height)

		if self.board.IsRTL():
			self.board.SetPosition(width, 0)

		self.board.SetSize(width, height)
		self.SetCenterPosition()
		self.UpdateRect()

	def SAFE_SetAcceptEvent(self, event):
		self.acceptButton.SAFE_SetEvent(event)

	def SAFE_SetCancelEvent(self, event):
		self.cancelButton.SAFE_SetEvent(event)

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)

	def SetCancelEvent(self, event):
		self.cancelButton.SetEvent(event)

	def SetText(self, text):
		self.textLine.SetText(text)

	def SetAcceptText(self, text):
		self.acceptButton.SetText(text)

	def SetCancelText(self, text):
		self.cancelButton.SetText(text)

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def GetTextSize(self):
		if self.textLine:
			return self.textLine.GetTextSize()

		return (0,0)

	def GetLineHeight(self):
		if self.textLine:
			return self.textLine.GetLineHeight()

		return 0

	def SetLineHeight(self, Height):
		self.textLine.SetLineHeight(Height)

	def GetTextLineCount(self):
		return self.textLine.GetTextLineCount()

class QuestionDialog2(QuestionDialog):
	def __init__(self):
		QuestionDialog.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		QuestionDialog.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog2.py")

		self.board = self.GetChild("board")
		self.textLine1 = self.GetChild("message1")
		self.textLine2 = self.GetChild("message2")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def SetText1(self, text):
		self.textLine1.SetText(text)

	def SetText2(self, text):
		self.textLine2.SetText(text)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def GetTextSize1(self):
			if self.textLine1:
				return self.textLine1.GetTextSize()
				
			return (0,0)
			
		def GetTextSize2(self):
			if self.textLine2:
				return self.textLine2.GetTextSize()
				
			return (0,0)

class QuestionDialogWithTimeLimit(QuestionDialog2):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__CreateDialog()
		self.endTime = 0
		self.timeoverMsg = None
		self.isCancelOnTimeover = False

	def __del__(self):
		QuestionDialog2.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog2.py")

		self.board = self.GetChild("board")
		self.textLine1 = self.GetChild("message1")
		self.textLine2 = self.GetChild("message2")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def Open(self, msg, timeout):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

		self.SetText1(msg)
		self.endTime = app.GetTime() + timeout

	def OnUpdate(self):
		leftTime = max(0, self.endTime - app.GetTime())
		self.SetText2(localeInfo.UI_LEFT_TIME % (leftTime))
		if leftTime<0.5:
			if self.timeoverMsg:
				chat.AppendChat(chat.CHAT_TYPE_INFO, self.timeoverMsg)
			if self.isCancelOnTimeover:
				self.cancelButton.CallEvent()

	def SetTimeOverMsg(self, msg):
		self.timeoverMsg = msg

	def SetCancelOnTimeOver(self):
		self.isCancelOnTimeover = True

if app.ENABLE_NEW_DROP_DIALOG:
	class QuestionDropDialog(ui.ScriptWindow):
		def __init__(self):
			ui.ScriptWindow.__init__(self)
			self.__CreateDialog()

		def __del__(self):
			ui.ScriptWindow.__del__(self)

		def __CreateDialog(self):
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/questiondropdialog.py")
			self.acceptEnabled = True
			self.destroyEnabled = True
			self.pending = False

			self.board = self.GetChild("board")
			self.textLine = self.GetChild("message")
			self.acceptButton = self.GetChild("accept")
			self.destroyButton = self.GetChild("destroy")
			self.cancelButton = self.GetChild("cancel")
			self.itemSlot = self.GetChild("ItemSlot")
			self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
			self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		def SetItemSlot(self, slotIndex):
			itemIndex = player.GetItemIndex(slotIndex)
			itemCount = player.GetItemCount(slotIndex)
			self.itemSlot.SetItemSlot(0, itemIndex, itemCount)
			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if not player.GetChangeLookVnum(player.INVENTORY, slotIndex) == 0:
					self.itemSlot.SetSlotCoverImage(slotIndex, "icon/item/ingame_convert_Mark.tga")
				else:
					self.itemSlot.EnableSlotCoverImage(slotIndex, False)

			item.SelectItem(player.GetItemIndex(slotIndex))

			metinSlot = [player.GetItemMetinSocket(slotIndex, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = [player.GetItemAttribute(slotIndex, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]

			if item.IsAntiFlag(item.ITEM_ANTIFLAG_DROP):
				self.acceptEnabled = False
				self.acceptButton.Down()
				self.acceptButton.Disable()

			if item.IsAntiFlag(item.ITEM_ANTIFLAG_DESTROY):
				self.destroyEnabled = False
				self.destroyButton.Down()
				self.destroyButton.Disable()

			if app.ENABLE_SOUL_BIND_SYSTEM:
				if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0:
					self.acceptEnabled = False
					self.destroyEnabled = False
					self.acceptButton.Down()
					self.acceptButton.Disable()
					self.destroyButton.Down()
					self.destroyButton.Disable()

			self.itemToolTip = uiToolTip.ItemToolTip()
			self.itemToolTip.SetInventoryItem(slotIndex) # 2019.02.11.owsap

		def Open(self):
			if 0 != self.itemToolTip:
				self.itemToolTip.HideToolTip()

			self.SetCenterPosition()
			self.SetTop()
			self.Show()

		def Close(self):
			if 0 != self.itemToolTip:
				self.itemToolTip.HideToolTip()

			self.Hide()

		def SetPending(self, pending):
			self.pending = bool(pending)
			if self.pending:
				for button in (self.acceptButton, self.destroyButton, self.cancelButton):
					button.Down()
					button.Disable()
				return

			if self.acceptEnabled:
				self.acceptButton.SetUp()
				self.acceptButton.Enable()
			if self.destroyEnabled:
				self.destroyButton.SetUp()
				self.destroyButton.Enable()
			self.cancelButton.SetUp()
			self.cancelButton.Enable()

		def SetDlgSize(self, width, height):
			self.SetSize(width, height)
			self.board.SetSize(width, height)
			self.SetCenterPosition()
			self.UpdateRect()

		def OverInItem(self, slotNumber):
			if 0 != self.itemToolTip:
				self.itemToolTip.ShowToolTip()

		def OverOutItem(self):
			if 0 != self.itemToolTip:
				self.itemToolTip.HideToolTip()

		def SAFE_SetAcceptEvent(self, event):
			self.acceptButton.SAFE_SetEvent(event)

		def SAFE_SetCancelEvent(self, event):
			self.cancelButton.SAFE_SetEvent(event)

		def SetDestroyEvent(self, event):
			self.destroyButton.SetEvent(event)

		def SetAcceptEvent(self, event):
			self.acceptButton.SetEvent(event)

		def SetCancelEvent(self, event):
			self.cancelButton.SetEvent(event)

		def SetText(self, text):
			self.textLine.SetText(text)
			# self.textLine.SetFontColor(0.72, 1.0, 0.0)

		def SetAcceptText(self, text):
			self.acceptButton.SetText(text)

		def SetCancelText(self, text):
			self.cancelButton.SetText(text)

		def OnPressEscapeKey(self):
			if self.pending:
				return True
			self.Close()
			return True

class MoneyInputDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.moneyHeaderText = localeInfo.MONEY_INPUT_DIALOG_SELLPRICE
		self.__avgPriceText = None
		self.__CreateDialog()
		self.__isNormalizingInput = False
		self.SetMaxLength(13)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/moneyinputdialog.py")

		getObject = self.GetChild
		self.board = self.GetChild("board")
		self.acceptButton = getObject("AcceptButton")
		self.cancelButton = getObject("CancelButton")
		self.inputValue = getObject("InputValue")
		#self.inputValue.SetNumberMode()
		self.inputValue.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdate)
		self.__avgPriceText = getObject("AverageValue")
		try:
			self.__avgPriceText.SetFontColor(0.0, 1.0, 0.0)
		except:
			pass
		self.moneyText = getObject("MoneyValue")

	def Open(self):
		self.inputValue.SetText("")
		self.inputValue.SetFocus()
		self.ClearAveragePrice()
		self.__OnValueUpdate()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.ClearDictionary()
		self.board = None
		self.acceptButton = None
		self.cancelButton = None
		self.inputValue = None
		self.Hide()

	def SetTitle(self, name):
		self.board.SetTitleName(name)

	def SetFocus(self):
		self.inputValue.SetFocus()

	def SetMaxLength(self, length):
		length = min(13, length)

		self.inputValue.SetMax(length)

	def SetMoneyHeaderText(self, text):
		self.moneyHeaderText = text

	def SetAveragePriceText(self, text):
		if not self.__avgPriceText:
			return
		self.__avgPriceText.SetText(text if text else "")

	def ClearAveragePrice(self):
		self.SetAveragePriceText("")

	def SetAveragePrice(self, price, sampleCount=0):
		if price is None:
			self.SetAveragePriceText("")
			return

		try:
			price = int(price)
		except:
			self.SetAveragePriceText("")
			return

		if price <= 0:
			self.SetAveragePriceText("")
			return

		self.SetAveragePriceText("~ %s" % (localeInfo.NumberToMoneyString(price)))

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)
		self.inputValue.SetReturnEvent(event)

	def SetCancelEvent(self, event):
		self.board.SetCloseEvent(event)
		self.cancelButton.SetEvent(event)
		self.inputValue.SetEscapeEvent(event)

	def SetValue(self, value):
		value=str(value)
		self.inputValue.SetText(value)
		self.__OnValueUpdate()
		ime.SetCursorPosition(len(value)+1)

	def GetValue(self):
		text = self.inputValue.GetText()
		money = 0

		if text:
			text = text.strip().replace(" ", "")
			if osfInfo.MONEY_K_FORMAT and len(text) >= 2 and (text[-1] == 'k' or text[-1] == 'K'):
				base = text[:-1]
				if base.isdigit():
					try:
						return int(base) * 1000
					except:
						return 0

		try:
			money = int(text)
		except ValueError:
			money = 0

		return money

	def GetText(self):
		return self.inputValue.GetText()

	def __OnValueUpdate(self):
		if self.__isNormalizingInput:
			return
		ui.EditLine.OnIMEUpdate(self.inputValue)

		text = self.inputValue.GetText()

		if text:
			endsWithK = osfInfo.MONEY_K_FORMAT and (text[-1] == 'k' or text[-1] == 'K')
			if endsWithK:
				base = "".join([c for c in text[:-1] if c.isdigit()])
				clean = base + "k"
			else:
				clean = "".join([c for c in text if c.isdigit()])

			if clean != text:
				self.__isNormalizingInput = True
				self.inputValue.SetText(clean)
				try:
					ime.SetCursorPosition(len(clean) + 1)
				except:
					pass
				self.__isNormalizingInput = False
				text = clean

		if osfInfo.MONEY_K_FORMAT and text and len(text) >= 2 and (text[-1] == 'k' or text[-1] == 'K'):
			base = text[:-1]
			if base.isdigit():
				try:
					newText = str(int(base) * 1000)
				except:
					newText = ""

				if newText and newText != text:
					self.__isNormalizingInput = True
					self.inputValue.SetText(newText)
					try:
						ime.SetCursorPosition(len(newText) + 1)
					except:
						pass
					self.__isNormalizingInput = False
					text = newText

		money = 0
		if text and text.isdigit():
			try:
				money = int(text)

			except ValueError:
				money = 199999999

		self.moneyText.SetText(self.moneyHeaderText + localeInfo.NumberToMoneyString(money))

class InputPinCodeDialog(ui.ScriptWindow):
	PIN_CODE_TOOLTIP = [
		localeInfo.PIN_CODE_TOOLTIP_LINE1,
		localeInfo.PIN_CODE_TOOLTIP_LINE2,
		localeInfo.PIN_CODE_TOOLTIP_LINE3,
		localeInfo.PIN_CODE_TOOLTIP_LINE4,
		localeInfo.PIN_CODE_TOOLTIP_LINE5
	]

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "UIScript/InputPinCodeDialog.py")

		getObject = self.GetChild
		self.board = getObject("Board")
		self.pinCodeSlot = getObject("PinCodeSlot")
		self.pinCodeValue = getObject("PinCodeValue")
		self.acceptButton = getObject("AcceptButton")
		self.cancelButton = getObject("CancelButton")
		self.toolTipButton = getObject("ToolTipButton")
		self.toolTip = self.CreateToolTip(localeInfo.INPUT_PIN_CODE_DIALOG_TITLE, self.PIN_CODE_TOOLTIP)
		self.toolTip.SetTop()
		self.toolTipButton.SetToolTipWindow(self.toolTip)

	def CreateToolTip(self, title, descList):
		toolTip = uiToolTip.ToolTip()
		toolTip.SetTitle(title)
		toolTip.AppendSpace(7)

		for desc in descList:
			toolTip.AutoAppendTextLine(desc)

		toolTip.AlignHorizonalCenter()
		toolTip.SetTop()
		return toolTip

	def Open(self):
		self.pinCodeValue.SetFocus()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.ClearDictionary()
		self.board = None
		self.toolTipButton = None
		self.toolTip = None
		self.acceptButton = None
		self.cancelButton = None
		self.pinCodeSlot = None
		self.pinCodeValue = None
		self.Hide()

	def SetTitle(self, name):
		self.board.SetTitleName(name)

	def SetNumberMode(self):
		self.pinCodeValue.SetNumberMode()

	def SetUseCodePage(self, bUse = True):
		self.pinCodeValue.SetUseCodePage(bUse)

	def SetSecretMode(self):
		self.pinCodeValue.SetSecret()

	def SetFocus(self):
		self.pinCodeValue.SetFocus()

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)
		self.pinCodeValue.OnIMEReturn = event

	def SetCancelEvent(self, event):
		self.board.SetCloseEvent(event)
		self.cancelButton.SetEvent(event)
		self.pinCodeValue.OnPressEscapeKey = event

	def GetText(self):
		return self.pinCodeValue.GetText()

class InputNewPinCodeDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "UIScript/InputNewPinCodeDialog.py")

		getObject = self.GetChild
		self.board = getObject("Board")
		self.acceptButton = getObject("AcceptButton")
		self.cancelButton = getObject("CancelButton")
		self.pinCodeSlot = getObject("PinCodeSlot")
		self.pinCodeSlotCheck = getObject("PinCodeSlotCheck")
		self.pinCodeValue = getObject("PinCodeValue")
		self.pinCodeValueCheck = getObject("PinCodeValueCheck")

		self.pinCodeValue.SetTabEvent(lambda arg = 1: self.OnNextFocus(arg))
		self.pinCodeValueCheck.SetTabEvent(lambda arg = 2: self.OnNextFocus(arg))

	def OnNextFocus(self, arg):
		if 1 == arg:
			self.pinCodeValue.KillFocus()
			self.pinCodeValueCheck.SetFocus()
		elif 2 == arg:
			self.pinCodeValueCheck.KillFocus()
			self.pinCodeValue.SetFocus()

	def Open(self):
		self.pinCodeValue.SetFocus()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Destroy(self):
		self.Close()

	def Close(self):
		self.ClearDictionary()
		self.board = None
		self.acceptButton = None
		self.cancelButton = None
		self.pinCodeSlot = None
		self.pinCodeSlotCheck = None
		self.pinCodeValue = None
		self.pinCodeValueCheck = None
		self.Hide()

	def SetTitle(self, name):
		self.board.SetTitleName(name)

	def SetNumberMode(self):
		self.pinCodeValue.SetNumberMode()
		self.pinCodeValueCheck.SetNumberMode()

	def SetUseCodePage(self, bUse = True):
		self.pinCodeValue.SetUseCodePage(bUse)
		self.pinCodeValueCheck.SetUseCodePage(bUse)

	def SetSecretMode(self):
		self.pinCodeValue.SetSecret()
		self.pinCodeValueCheck.SetSecret()

	def SetFocus(self):
		self.pinCodeValue.SetFocus()

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)
		self.pinCodeValueCheck.OnIMEReturn = event

	def SetCancelEvent(self, event):
		self.board.SetCloseEvent(event)
		self.cancelButton.SetEvent(event)
		self.pinCodeValue.OnPressEscapeKey = event
		self.pinCodeValueCheck.OnPressEscapeKey = event

	def GetText(self):
		return self.pinCodeValue.GetText()

	def GetTextCheck(self):
		return self.pinCodeValueCheck.GetText()

class BuyMultipleDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questionbuymultiple.py")

		self.board = self.GetChild("board")
		self.textLine = self.GetChild("message")
		self.sigilPriceIcon = None
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")
		self.quantityEditValue = self.GetChild("quantity_value")
		self.itemSlot = self.GetChild("ItemSlot")
		self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		
		self.quantityEditValue.SetUpdateEvent(ui.__mem_func__(self.OnChangeQuantity))
		
		self.buyQuantity = 1
		self.totalPrice = 0
		self.singlePrice = 0
		self.slotIndex = -1
		self.canChangeQuantity = True
		
	def SetCanEditQuantity(self, bCan):
		self.canChangeQuantity = bCan
		if not bCan:
			self.quantityEditValue.KillFocus()
		else:
			self.quantityEditValue.SetFocus()
		
	def GetQuantity(self):
		return self.buyQuantity
		
	def SetQuantityEscapeEvent(self, event):
		self.quantityEditValue.SetEscapeEvent(event)
		
	def SetConfirmQuantityEvent(self, event):
		self.quantityEditValue.SetReturnEvent(event)
		
	def OnChangeQuantity(self):
		if not self.canChangeQuantity:
			self.quantityEditValue.SetText("1")
			self.buyQuantity = 1
			self.quantityEditValue.KillFocus()
			return
	
		text = self.quantityEditValue.GetText()
		if len(text) > 0 and text.isdigit():
			if int(text) <= 0:
				self.quantityEditValue.SetText("1")
				text = 1
			elif int(text) > 5000:
				self.quantityEditValue.SetText("5000")
				text = 5000
				
			self.buyQuantity = int(text)

			self.SetItemSlot(self.slotIndex)

	def SetItemSlot(self, slotIndex):
		if self.sigilPriceIcon:
			self.sigilPriceIcon.Hide()
		self.textLine.SetWindowHorizontalAlignCenter()
		self.textLine.SetHorizontalAlignCenter()
		self.textLine.SetPosition(0, 25)
		self.slotIndex = slotIndex
		itemIndex = shop.GetItemID(slotIndex)
		itemPrice = shop.GetItemPrice(slotIndex)
		itemCount = shop.GetItemCount(slotIndex)
		if app.ENABLE_SHOPEX_RENEWAL:
			PriceType = shop.GetItemPriceType(slotIndex)
			PriceVnum = shop.GetItemPriceVnum(slotIndex)
			
		item.SelectItem(itemIndex)
		
		if item.IsFlag(item.ITEM_FLAG_STACKABLE) and itemIndex != 51002 and itemIndex != 55031:
			self.SetCanEditQuantity(True)
		else:
			self.SetCanEditQuantity(False)
			
		itemName = item.GetItemName()
		
		singlePrice = itemPrice // itemCount
		self.singlePrice = singlePrice
		
		if app.ENABLE_SHOPEX_RENEWAL:
			PriceType = shop.GetItemPriceType(slotIndex)
			PriceVnum = shop.GetItemPriceVnum(slotIndex)
			if PriceType == 1:
				txtTitle = "1x " + itemName + " = " + localeInfo.LongNumberToString(singlePrice) + " Yang"
				txtAccept = localeInfo.LongNumberToString(singlePrice * self.buyQuantity) + "|Iitem/money|i"
				self.acceptButton.SetText(localeInfo.BUY_WITH_PRICE % (txtAccept))
			elif PriceType == 2:
				txtTitle = "1x " + itemName + " = " + localeInfo.NumberToSecondaryCoinString(singlePrice)
				txtAccept = localeInfo.NumberToSecondaryCoinString(singlePrice * self.buyQuantity)
				self.acceptButton.SetText(localeInfo.BUY_WITH_PRICE % (txtAccept))
			elif PriceType == 3: #ITEM
			
				txtTitle = localeInfo.FINAL_PRICE
				txtAccept = ""
				sigilPrice = None
				priceItemCount = 0
				
				for j in range(shop.SHOPEX_VNUM_COUNT):
					PriceVnum, PriceVnumCount = shop.ExGetItemPrice(slotIndex, j)
					if PriceVnum == 0 or PriceVnumCount == 0:
						continue
					priceItemCount += 1
					
					item.SelectItem(PriceVnum)
					
					singlePrice = PriceVnumCount // itemCount
				
					priceItem = item.GetIconImageFileName()
					if 91200 <= PriceVnum <= 91203:
						sigilPrice = (priceItem, singlePrice * self.buyQuantity, item.GetItemName())
					priceItem = priceItem.replace("\\", "/")
					priceItem = priceItem.replace("icon/", "")
					priceItem = priceItem.replace(".tga", "")
					iconPriceItem = "|I" + priceItem + "|i"
					
					txtTitle += localeInfo.NumberToString(singlePrice * self.buyQuantity) + "x " + iconPriceItem + " + "
					
				if sigilPrice and priceItemCount == 1:
					iconPath, sigilCount, sigilName = sigilPrice
					txtTitle = "%dx %s" % (sigilCount, sigilName)
					if not self.sigilPriceIcon:
						self.sigilPriceIcon = ui.ExpandedImageBox()
						self.sigilPriceIcon.SetParent(self.board)
						self.sigilPriceIcon.AddFlag("not_pick")
					self.sigilPriceIcon.LoadImage(iconPath)
					self.sigilPriceIcon.SetScale(0.625, 0.625)
					self.textLine.SetText(txtTitle)
					textWidth = self.textLine.GetTextSize()[0]
					iconWidth = int(self.sigilPriceIcon.GetWidth() * 0.625)
					rowX = (self.board.GetWidth() - iconWidth - 5 - textWidth) // 2
					self.sigilPriceIcon.SetPosition(rowX, 22)
					self.sigilPriceIcon.Show()
					self.textLine.SetWindowHorizontalAlignLeft()
					self.textLine.SetHorizontalAlignLeft()
					self.textLine.SetPosition(rowX + iconWidth + 5, 25)
				else:
					txtTitle = txtTitle[:-3]
				txtAccept = txtAccept[:-3]
				
				self.acceptButton.SetText(uiScriptLocale.SHOP_BUY)

			elif PriceType == 4: #EXP
				txtTitle = "1x " + itemName + " = " + str(singlePrice ) + "x " + "EXP"
				txtAccept = localeInfo.NumberToString(singlePrice * self.buyQuantity) + "x " + "EXP"
				self.acceptButton.SetText(localeInfo.BUY_WITH_PRICE % (txtAccept))

			self.textLine.SetText(txtTitle)
		else:
			self.textLine.SetText(localeInfo.INFO_BUY_MULTIPLE_ITEM % (itemName, localeInfo.NumberToMoneyString(singlePrice)))
			self.acceptButton.SetText(localeInfo.BUY_WITH_PRICE % (localeInfo.NumberToMoneyString(singlePrice * self.buyQuantity)))
		
		if self.buyQuantity != 1:
			self.itemSlot.SetItemSlot(0, itemIndex, self.buyQuantity)
		else:
			self.itemSlot.SetItemSlot(0, itemIndex, 1)

		self.itemToolTip = uiToolTip.ItemToolTip()
		self.itemToolTip.SetShopItem(slotIndex)
		self.itemToolTip.HideToolTip()

	def Open(self):
		if 0 != self.itemToolTip:
			self.itemToolTip.HideToolTip()

		self.SetCenterPosition()
		self.SetTop()
		
		if not self.canChangeQuantity:
			self.quantityEditValue.KillFocus()
		else:
			self.quantityEditValue.SetFocus()
		
		self.Show()

	def Close(self):
		if 0 != self.itemToolTip:
			self.itemToolTip.HideToolTip()

		self.Hide()

	def SetDlgSize(self, width, height):
		self.SetSize(width, height)
		self.board.SetSize(width, height)
		self.SetCenterPosition()
		self.UpdateRect()

	def OverInItem(self, slotNumber):
		if 0 != self.itemToolTip:
			self.itemToolTip.ShowToolTip()

	def OverOutItem(self):
		if 0 != self.itemToolTip:
			self.itemToolTip.HideToolTip()

	def SAFE_SetAcceptEvent(self, event):
		self.acceptButton.SAFE_SetEvent(event)

	def SAFE_SetCancelEvent(self, event):
		self.cancelButton.SAFE_SetEvent(event)

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)

	def SetCancelEvent(self, event):
		self.cancelButton.SetEvent(event)

	def SetText(self, text):
		self.textLine.SetText(text)
		# self.textLine.SetFontColor(0.72, 1.0, 0.0)

	def SetAcceptText(self, text):
		self.acceptButton.SetText(text)

	def SetCancelText(self, text):
		self.cancelButton.SetText(text)
		
	def CloseQuantity(self):
		self.Close()
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True
