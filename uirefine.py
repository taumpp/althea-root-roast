import app
import grp
import net
import player
import item
import ui
import uiToolTip
import uimaterialrow
import mouseModule
import localeInfo
import uiCommon
import constInfo
import osfInfo
import wiki
import wndMgr
import talismanrefine
import ownedcount
import gloverefine
import crafttoolmodel

if app.WJ_ENABLE_TRADABLE_ICON:
	INVENTORY_PAGE_SIZE = player.INVENTORY_PAGE_SIZE

class RefineDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'AcceptButton', child=True)
		self.__LoadScript()

		self.scrollItemPos = 0
		self.targetItemPos = 0
		self.weaponEnhancement = None

	def __LoadScript(self):
		self.__LoadQuestionDialog()

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/refinedialog.py")

		except:
			import exception
			exception.Abort("RefineDialog.__LoadScript.LoadObject")

		try:
			self.board = self.GetChild("Board")
			self.titleBar = self.GetChild("TitleBar")
			self.successPercentage = self.GetChild("SuccessPercentage")
			self.GetChild("AcceptButton").SetEvent(self.OpenQuestionDialog)
			self.GetChild("CancelButton").SetEvent(self.Close)
		except:
			import exception
			exception.Abort("RefineDialog.__LoadScript.BindObject")

		if osfInfo.SHOW_REFINE_PERCENTAGE == True:
			self.successPercentage.Show()
		else:
			self.successPercentage.Hide()

		toolTip = uiToolTip.ItemToolTip()
		toolTip.SetParent(self)
		toolTip.SetPosition(15, 38)
		toolTip.SetFollow(False)
		toolTip.Show()
		self.toolTip = toolTip

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadQuestionDialog(self):
		# uiCommon.QuestionDialog2 (the same uiscript questiondialog2.py, two lines + Ano / Ne): the R1 look of the
		# common dialogs (uir1dialog) and its Esc close come with it, "Starý vzhled" keeps the original.
		self.dlgQuestion = uiCommon.QuestionDialog2()
		self.dlgQuestion.SetText1(localeInfo.REFINE_DESTROY_WARNING)
		self.dlgQuestion.SetText2(localeInfo.REFINE_WARNING2)
		self.dlgQuestion.SetAcceptEvent(ui.__mem_func__(self.Accept))
		self.dlgQuestion.SetCancelEvent(ui.__mem_func__(self.dlgQuestion.Close))

	def Destroy(self):
		self.ClearDictionary()
		self.board = 0
		self.successPercentage = 0
		self.titleBar = 0
		self.toolTip = 0
		self.dlgQuestion = 0

	def Open(self, scrollItemPos, targetItemPos):
		self.weaponEnhancement = None
		self.scrollItemPos = scrollItemPos
		self.targetItemPos = targetItemPos
		# Every USE_TUNING scroll is an ordinary refine: the server rolls
		# refine_proto.prob of the item's refine set, adjusted by the scroll type,
		# and sends it only with the refine
		# window that follows. This step knows no chance, so it shows none.
		self.successPercentage.Hide()

		itemIndex = player.GetItemIndex(targetItemPos)
		self.toolTip.ClearToolTip()
		metinSlot = []
		for i in range(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(player.GetItemMetinSocket(targetItemPos, i))
		self.toolTip.AddItemData(itemIndex, metinSlot)

		self.UpdateDialog()
		self.SetTop()
		self.Show()

	def OpenWeaponEnhancement(self, scrollItemPos, targetItemPos, resultVnum):
		self.Close()
		scrollVnum = player.GetItemIndex(scrollItemPos)
		sourceVnum = player.GetItemIndex(targetItemPos)
		item.SelectItem(resultVnum)
		level = 0
		for i in range(item.LIMIT_MAX_NUM):
			limitType, limitValue = item.GetLimit(i)
			if limitType == item.LIMIT_LEVEL:
				level = limitValue
				break
		if not level:
			return

		self.scrollItemPos = scrollItemPos
		self.targetItemPos = targetItemPos
		self.weaponEnhancement = (scrollVnum, sourceVnum)
		self.successPercentage.SetText(localeInfo.REFINE_SUCCESS_PROBALITY % 100)
		self.successPercentage.Show()
		self.toolTip.ClearToolTip()
		metinSlot = [player.GetItemMetinSocket(targetItemPos, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [player.GetItemAttribute(targetItemPos, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
		self.toolTip.AddItemData(resultVnum, metinSlot, attrSlot)
		self.toolTip.AppendSpace(5)
		self.toolTip.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_LEVEL % level, self.toolTip.NEGATIVE_COLOR)
		self.UpdateDialog()
		self.SetTop()
		self.Show()

	def UpdateDialog(self):
		newWidth = self.toolTip.GetWidth() + 30
		# The tooltip starts at y=38; the chance row sits 70px above the bottom.
		# Leave 14px between them even when weapon bonuses make the tooltip tall.
		newHeight = self.toolTip.GetHeight() + 122
		self.board.SetSize(newWidth, newHeight)
		self.titleBar.SetWidth(newWidth + 8)
		self.SetSize(newWidth, newHeight)

		(x, y) = self.GetLocalPosition()
		self.SetPosition(x, max(0, min(y, wndMgr.GetScreenHeight() - newHeight - 4)))

	def OpenQuestionDialog(self):
		if self.weaponEnhancement:
			self.Accept()
			return
		self.dlgQuestion.Open()

	def Accept(self):
		if self.weaponEnhancement:
			scrollVnum, sourceVnum = self.weaponEnhancement
			if (player.GetItemIndex(self.scrollItemPos) != scrollVnum or
					player.GetItemIndex(self.targetItemPos) != sourceVnum):
				self.Close()
				return
		net.SendItemUseToItemPacket(self.scrollItemPos, self.targetItemPos)
		self.Close()

	def Close(self):
		self.weaponEnhancement = None
		if self.dlgQuestion:
			self.dlgQuestion.Close()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

class RefineDialogNew(ui.ScriptWindow):
	# the material name stays neutral, only "owned / need" is green / red (root/ownedcount.py)
	MATERIAL_NAME_COLOR = ownedcount._Signed(0xFFEEE6D8)
	MATERIAL_AVAILABLE_COLOR = ownedcount.Color(1, 1)
	MATERIAL_MISSING_COLOR = ownedcount.Color(0, 1)
	WINDOW_WIDTH = 284
	MATERIALS_Y = 166
	MATERIAL_ROW_HEIGHT = 34
	MATERIAL_ROW_CONTENT_HEIGHT = 34
	MATERIAL_ROW_X = 17
	MATERIAL_SLOT_Y = 1
	MATERIAL_TEXT_X = 38
	MATERIAL_TEXT_PADDING = 14
	MATERIAL_TEXT_CENTER_Y = MATERIAL_ROW_CONTENT_HEIGHT // 2
	MATERIAL_FRAME_IMAGE = "d:/ymir work/ui/game/refine/material_name_frame_214x34.png"
	YANG_BAR_IMAGE = "d:/ymir work/ui/game/crimson_ember/inventory/currency_footer.png"
	YANG_BAR_X = 38
	YANG_BAR_WIDTH = 228
	YANG_BAR_SOURCE_WIDTH = 160.0
	YANG_BAR_HEIGHT = 23
	CHANCE_GAP = 8
	YANG_GAP = 20
	AUTO_REFINE_GAP = 28
	AUTO_REFINE_ROW_HEIGHT = 29
	ACTION_BOTTOM = 275
	MATERIALS_PER_COLUMN = 7
	SECOND_COLUMN_X = 260
	# R1 look (): the R1 price (root/uir1price.py) in an R1 well instead of the footer strip and the R1
	# OK / Zrušit row (26 px buttons, 10 px above the bottom edge: the dialog grows by R1_BUTTON_EXTRA)
	R1_PRICE_X = MATERIAL_ROW_X			# the R1 price well spans the material rows (slot + name frame)
	R1_PRICE_W = MATERIAL_TEXT_X + 214
	R1_BUTTON_EXTRA = 12
	r1Price = None
	r1Buttons = None
	r1Checks = ()		# uir1price.CheckBoxTwin of "Zrychlit vylepšování" (box, gap, label; left margin of the rows)
	# Tool mode: the rod, the pickaxe and the axe
	# are upgraded in this window. The same slots, rows, chance line, price and buttons; the first row is the practice
	# (a material row with the practice bar of the Biolog in its name frame, R1 look only), the seal and the material
	# rows are ordinary rows with the server's counts. The texts are locale_game CRAFT_TOOL_* (root/crafttoolmodel.py).
	PRACTICE_TEXT_Y = 11			# the name and "mám / potřeba" of the practice row: their Tahoma 12 cell ends on the bar
	PRACTICE_BAR_BOTTOM = 3			# the bar's bottom edge above the name frame's bottom edge
	toolYang = None
	toolMode = False
	toolState = None			# crafttoolmodel.ToolState of the tool in the window, None = empty
	toolIds = ()				# the tools of the NPC (CraftToolShopV1): the empty hint names them
	toolCell = None				# the cell asked for (a drop, CraftToolOpenV1); its state replaces the shown one
	toolAsking = False			# an info / up request is on its way (the inventory refresh asks only then not)
	toolBar = None				# the practice bar (uir1price.ProgressBar: track, fill) on the name frame of row 0
	toolLossText = None			# "[–10 % cviku]" right on the chance line (band A)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'acceptButton')
		self.interface = None
		self.isLoaded = False
		self.materialRows = []
		self.materialCount = 0
		self.materials = []
		self.toolTipItem = None
		self.checkBox = None
		self.yangParts = []
		self.__Initialize()

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None

	def __Initialize(self):
		self.dlgQuestion = None
		self.vnum = 0
		self.targetItemPos = 0
		self.dialogHeight = 0
		self.cost = 0
		self.percentage = 0
		self.type = 0
		self.apply_random_list = None
		self.src_vnum = 0
		self.currentItemVnum = 0
		self.currentMetinSlots = []
		self.currentAttrSlots = []
		self.currentRefineElement = None
		self.currentApplyRandomList = None
		self.currentSetValue = 0

	def IsLoaded(self):
		return self.isLoaded

	def __LoadScript(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/refinepreviewdialog.py")

		except:
			import exception
			exception.Abort("RefineDialog.__LoadScript.LoadObject")

		try:
			self.board = self.GetChild("Board")
			self.titleBar = self.GetChild("TitleBar")
			self.probText = self.GetChild("SuccessPercentage")
			self.bonusText = self.GetChild("BonusText")
			self.yangPanel = self.GetChild("YangPanel")
			self.acceptButton = self.GetChild("AcceptButton")
			self.cancelButton = self.GetChild("CancelButton")
			self.currentItemSlot = self.GetChild("CurrentItemSlot")
			self.resultItemSlot = self.GetChild("ResultItemSlot")
			self.successPercentage = self.GetChild("SuccessPercentage")
			self.acceptButton.SetEvent(self.OpenQuestionDialog)
			self.cancelButton.SetEvent(self.CancelRefine)
		except:
			import exception
			exception.Abort("RefineDialog.__LoadScript.BindObject")

		if osfInfo.SHOW_REFINE_PERCENTAGE == True:
			self.successPercentage.Show()
		else:
			self.successPercentage.Hide()
			self.bonusText.Hide()

		self.currentItemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInCurrentItem))
		self.currentItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.resultItemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInResultItem))
		self.resultItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		# tool mode: a tool dragged from the inventory into "Před vylepšením" (the blacksmith mode ignores drops)
		self.currentItemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__SelectToolSlot))
		self.currentItemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectToolSlot))
		self.blacksmithTitle = self.GetChild("TitleName").GetText()
		self.blacksmithAccept = self.acceptButton.GetText()

		self.toolTipItem = uiToolTip.ItemToolTip()
		self.toolTipItem.HideToolTip()
		self.__CreateYangRow()
		self.__BuildR1()

		if app.ENABLE_AUTO_REFINE:
			self.checkBox = self.GetChild("AutoRefineCheckBox")
			self.checkBox.SetToggleDownEvent(
				ui.__mem_func__(self.AutoRefine), "ON_CHECK", True
			)
			self.checkBox.SetToggleUpEvent(
				ui.__mem_func__(self.AutoRefine), "ON_UNCHECK", False
			)
			self.checkBox.Hide()
		else:
			self.GetChild("AutoRefineCheckBox").Hide()

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.CancelRefine))
		self.isLoaded = True

	def __del__(self):
		ui.ScriptWindow.__del__(self)

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.inven = None

	def __CreateYangRow(self):
		background = ui.ExpandedImageBox()
		background.SetParent(self.yangPanel)
		background.SetPosition(self.YANG_BAR_X, 0)
		background.LoadImage(self.YANG_BAR_IMAGE)
		background.SetScale(
			float(self.YANG_BAR_WIDTH) / self.YANG_BAR_SOURCE_WIDTH,
			1.0,
		)
		background.AddFlag("not_pick")
		background.Show()

		moneyIcon = ui.ImageBox()
		moneyIcon.SetParent(self.yangPanel)
		moneyIcon.SetPosition(20, (self.YANG_BAR_HEIGHT - 16) // 2)
		moneyIcon.LoadImage("d:/ymir work/ui/game/crimson_ember/inventory/icon_yang.png")
		moneyIcon.AddFlag("not_pick")
		moneyIcon.Show()

		costText = ui.TextLine()
		costText.SetParent(self.yangPanel)
		costText.SetPosition(
			self.YANG_BAR_X + self.YANG_BAR_WIDTH - 5,
			self.YANG_BAR_HEIGHT // 2,
		)
		costText.SetHorizontalAlignRight()
		costText.SetVerticalAlignCenter()
		costText.SetOutline()
		costText.AddFlag("not_pick")
		costText.Show()

		self.yangParts = [background, moneyIcon]
		self.costText = costText

	def __BuildR1(self):
		"""R1 look (the board dressed by root/uir1frame.py): the shared R1 price in an R1 well and the R1 OK / Zrušit
		row (root/uir1price.py). The original yang strip and buttons stay for "Starý vzhled"; a failure here or a
		later frame failure gives them back."""
		if self.__dict__.get("r1frame") is None:
			return
		try:
			import uir1price
			self.r1Price = uir1price.PriceField(self.yangPanel, self.R1_PRICE_X, 0, self.R1_PRICE_W)
			self.r1Buttons = uir1price.ConfirmButtons(self.board, self.acceptButton, self.cancelButton)
			self.r1Buttons.Place(self.board.GetWidth(), self.board.GetHeight() - uir1price.BUTTON_BOTTOM)
			if app.ENABLE_AUTO_REFINE:
				native = self.GetChild("AutoRefineCheckBox")
				self.r1Checks = (uir1price.CheckBoxTwin(self.board, native, self.R1_PRICE_X - 42),)
			for part in self.yangParts + [self.costText]:
				part.Hide()
			# a later failure of the frame (uir1frame.FrameSkin.Undo) gives the original row and buttons back too
			self.r1frame.undo.append(ui.__mem_func__(self.__DropR1))
		except Exception:
			try:
				import uir1price
				uir1price.TraceFailure("the refine dialog price and buttons")
			except Exception:
				pass
			self.__DropR1()

	def __DropR1(self):
		checks, self.r1Checks = self.r1Checks, ()
		for check in checks:
			check.Restore()
		if self.r1Buttons is not None:
			self.r1Buttons.Restore()
		if self.r1Price is not None:
			self.r1Price.Destroy()
		self.r1Price = None
		self.r1Buttons = None
		for part in self.yangParts + ([self.costText] if self.costText else []):
			part.Show()

	def __IsR1(self):
		if self.r1Price is None:
			return False
		if self.__dict__.get("r1frame") is None:	# the frame failed after it was built: the original look
			self.__DropR1()
			return False
		return True

	def __ClearComparisonSlots(self):
		for slot in (self.currentItemSlot, self.resultItemSlot):
			for cellIndex in range(3):
				slot.ClearSlot(cellIndex)
			slot.RefreshSlot()

	def OverInCurrentItem(self, slotIndex):
		if not self.toolTipItem or not self.currentItemVnum:
			return

		self.toolTipItem.ClearToolTip()
		self.toolTipItem.AddItemData(
			self.currentItemVnum,
			self.currentMetinSlots,
			self.currentAttrSlots,
			refine_element=self.currentRefineElement,
			apply_random_list=self.currentApplyRandomList,
			set_value=self.currentSetValue,
		)
		self.toolTipItem.ShowToolTip()

	def OverInResultItem(self, slotIndex):
		if not self.toolTipItem or not self.vnum:
			return

		self.toolTipItem.ClearToolTip()
		self.toolTipItem.AddRefineItemData(
			self.vnum,
			self.currentMetinSlots,
			self.currentAttrSlots,
			None,
			self.type,
			self.currentRefineElement,
			self.apply_random_list if app.ENABLE_APPLY_RANDOM else None,
			self.currentSetValue,
		)
		self.toolTipItem.ShowToolTip()

	def __SearchMaterial(self, vnum):
		search = getattr(self.interface, "SearchVirtualMarketInventoryItem", None)
		if search:
			return search(vnum)
		return False

	def OverOutItem(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def __CreateMaterialRow(self, index):
		row = uimaterialrow.MaterialRow(
			self.toolTipItem, ui.__mem_func__(self.__SearchMaterial))
		row.SetParent(self)
		row.SetSize(250, self.MATERIAL_ROW_CONTENT_HEIGHT)

		slot = ui.SlotWindow()
		slot.SetParent(row)
		slot.SetPosition(0, self.MATERIAL_SLOT_Y)
		slot.SetSize(32, 32)
		slot.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		r1frame = self.__dict__.get("r1frame")
		if r1frame is not None:
			# R1 (root/uir1frame.py): the item slot C; a frame failure puts the original back
			r1frame.SetSlot(slot, "d:/ymir work/ui/public/Slot_Base.sub")
		slot.AppendSlot(index, 0, 0, 32, 32)
		slot.AddFlag("not_pick")
		slot.RefreshSlot()
		slot.Show()

		frame = ui.ImageBox()
		frame.SetParent(row)
		frame.SetPosition(self.MATERIAL_TEXT_X, 0)
		frame.LoadImage(self.MATERIAL_FRAME_IMAGE)
		frame.AddFlag("not_pick")
		frame.Show()
		row.SetSize(self.MATERIAL_TEXT_X + frame.GetWidth(), self.MATERIAL_ROW_CONTENT_HEIGHT)

		textLine = ui.TextLine()
		textLine.SetParent(frame)
		textLine.SetPosition(self.MATERIAL_TEXT_PADDING, self.MATERIAL_TEXT_CENTER_Y)
		textLine.SetFontName(localeInfo.UI_DEF_FONT)
		textLine.SetVerticalAlignCenter()
		textLine.SetLimitWidth(160)
		textLine.SetOutline()
		textLine.SetFeather(False)
		textLine.AddFlag("not_pick")
		textLine.Show()

		countLine = ui.TextLine()
		countLine.SetParent(frame)
		countLine.SetPosition(
			frame.GetWidth() - self.MATERIAL_TEXT_PADDING,
			self.MATERIAL_TEXT_CENTER_Y,
		)
		countLine.SetHorizontalAlignRight()
		countLine.SetVerticalAlignCenter()
		countLine.SetPackedFontColor(self.MATERIAL_AVAILABLE_COLOR)
		countLine.SetOutline()
		countLine.SetFeather(False)
		countLine.AddFlag("not_pick")
		countLine.Show()

		row.Hide()
		self.materialRows.append((row, slot, frame, textLine, countLine))
		return row, slot, frame, textLine, countLine

	def __ClearMaterials(self):
		for index, rowData in enumerate(self.materialRows):
			row, slot, frame, textLine, countLine = rowData
			row.SetItem(0)
			slot.ClearSlot(index)
			slot.RefreshSlot()
			textLine.SetText("")
			countLine.SetText("")
			row.Hide()
		self.materialCount = 0
		self.materials = []
		if self.toolBar is not None:
			for layer in self.toolBar:
				layer.Hide()

	def Destroy(self):
		self.OverOutItem()
		self.__ClearMaterials()
		if self.r1Price is not None:
			self.r1Price.Destroy()
		self.r1Price = None
		if self.toolBar is not None:
			for layer in self.toolBar:
				layer.Destroy()
		self.toolBar = None
		self.toolLossText = None
		self.toolState = None
		self.r1Buttons = None
		self.interface = None
		self.ClearDictionary()
		self.dlgQuestion = None
		self.board = None
		self.titleBar = None
		self.probText = None
		self.bonusText = None
		self.costText = None
		self.successPercentage = None
		self.currentItemSlot = None
		self.resultItemSlot = None
		self.yangPanel = None
		self.acceptButton = None
		self.cancelButton = None
		self.toolTipItem = None
		self.checkBox = None
		self.yangParts = []
		self.materialRows = []
		self.materialCount = 0
		self.materials = []

	def Open(self, targetItemPos, nextGradeItemVnum, cost, prob, type, apply_random_list, src_vnum, bonus=0):
		if False == self.isLoaded:
			self.__LoadScript()

		self.__LeaveToolMode()
		self.__ClearMaterials()
		self.__Initialize()

		self.targetItemPos = targetItemPos
		self.vnum = nextGradeItemVnum
		self.cost = cost
		self.percentage = prob
		self.type = type
		self.apply_random_list = apply_random_list
		self.src_vnum = src_vnum
		self.__ReadTarget(targetItemPos)

		self.probText.SetText(localeInfo.REFINE_SUCCESS_PROBALITY % (self.percentage))
		bonusFormat = u"[Bonus +%d%%]"
		if app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz":
			bonusFormat = u"[Nav\u00edc +%d%%]"
		self.bonusText.SetText(bonusFormat % bonus)
		self.__SetCost(self.cost)
		if app.ENABLE_AUTO_REFINE:
			if osfInfo.IS_AUTO_REFINE:
				self.checkBox.Down()
			else:
				self.checkBox.SetUp()
			self.checkBox.Show()

		self.__ClearComparisonSlots()
		self.currentItemSlot.SetItemSlot(0, self.currentItemVnum, 0)
		self.resultItemSlot.SetItemSlot(0, self.vnum, 0)
		self.currentItemSlot.RefreshSlot()
		self.resultItemSlot.RefreshSlot()
		self.UpdateDialog()

		if osfInfo.IS_AUTO_REFINE == True and osfInfo.AUTO_REFINE == True:
			pass
		else:
			self.SetTop()

		self.Show()

	def __ReadTarget(self, targetItemPos):
		"""The item in ``targetItemPos`` with its sockets, bonuses and set (the tooltips of both slots)."""
		self.currentItemVnum = player.GetItemIndex(targetItemPos)
		self.currentMetinSlots = [
			player.GetItemMetinSocket(targetItemPos, i)
			for i in range(player.METIN_SOCKET_MAX_NUM)
		]
		self.currentAttrSlots = [
			player.GetItemAttribute(targetItemPos, i)
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)
		]
		self.currentRefineElement = player.GetItemRefineElement(targetItemPos) if app.ENABLE_REFINE_ELEMENT_SYSTEM else None
		self.currentApplyRandomList = [
			player.GetItemApplyRandom(targetItemPos, i)
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)
		] if app.ENABLE_APPLY_RANDOM else None
		self.currentSetValue = player.GetItemSetValue(targetItemPos) if getattr(app, "ENABLE_SET_ITEM", False) else 0

	def __SetCost(self, cost):
		"""The price row: the original strip's text and the R1 price (red when the player cannot pay it)."""
		self.costText.SetText(
			"%s %s" % (
				localeInfo.NumberToString(cost),
				localeInfo.CHEQUE_SYSTEM_UNIT_YANG,
			)
		)
		if self.r1Price is not None:
			import uir1price
			self.r1Price.SetPrice(cost, uir1price.CanAfford(cost))

	def Close(self):
		self.dlgQuestion = None
		if self.toolMode:
			self.__ReleaseToolCell()
			self.toolCell = None
			self.toolAsking = False
		self.__ClearMaterials()
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
		self.Hide()
		if app.ENABLE_AUTO_REFINE:
			osfInfo.AUTO_REFINE = False

	def AppendMaterial(self, vnum, count):
		index = self.materialCount
		if index >= len(self.materialRows):
			row, slot, frame, textLine, countLine = self.__CreateMaterialRow(index)
		else:
			row, slot, frame, textLine, countLine = self.materialRows[index]

		row.SetItem(vnum)

		slot.SetItemSlot(index, vnum, count)
		slot.RefreshSlot()
		item.SelectItem(vnum)
		textLine.SetPackedFontColor(self.MATERIAL_NAME_COLOR)
		textLine.SetText(item.GetItemName())
		ownedcount.Paint(countLine, ownedcount.Owned(vnum), count)
		self.materials.append((vnum, count))

		if localeInfo.IsARABIC():
			textLine.SetPosition(
				frame.GetWidth() - self.MATERIAL_TEXT_PADDING,
				self.MATERIAL_TEXT_CENTER_Y,
			)
			textLine.SetHorizontalAlignRight()
			countLine.SetPosition(self.MATERIAL_TEXT_PADDING, self.MATERIAL_TEXT_CENTER_Y)
			countLine.SetHorizontalAlignLeft()
		else:
			textLine.SetPosition(self.MATERIAL_TEXT_PADDING, self.MATERIAL_TEXT_CENTER_Y)
			textLine.SetHorizontalAlignLeft()
			countLine.SetPosition(
				frame.GetWidth() - self.MATERIAL_TEXT_PADDING,
				self.MATERIAL_TEXT_CENTER_Y,
			)
			countLine.SetHorizontalAlignRight()

		row.Show()
		self.materialCount += 1
		self.UpdateDialog()

	def RefreshOwnedCounts(self):
		"""The "owned / need" of every material again (the interface calls it when the inventory changes)."""
		if self.toolMode:
			# the server counts a seal or material row over several items: its state again, one request at a time
			if self.toolState is not None and not self.toolAsking:
				self.__AskTool(self.toolState.cell)
			return
		for index, (vnum, count) in enumerate(getattr(self, "materials", [])):
			if index < len(self.materialRows):
				ownedcount.Paint(self.materialRows[index][4], ownedcount.Owned(vnum), count)

	# ---------------------------------------------------------------------------------------------- tool mode
	def RefreshToolYang(self):
		if not self.toolMode or not self.IsShow():
			return
		yang = player.GetElk()
		if yang != self.toolYang and self.toolState is not None and not self.toolAsking:
			self.toolYang = yang
			self.__AskTool(self.toolState.cell)

	def IsToolMode(self):
		return self.toolMode

	def OpenTool(self, toolIds=(), cell=None):
		"""The tool mode: the window opens empty (the shop's "Vylepšit nástroj", ``toolIds`` = the NPC's tools) or for
		the tool in ``cell`` (a tool dragged onto the NPC, CraftToolOpenV1: its CraftToolV1 state follows)."""
		if False == self.isLoaded:
			self.__LoadScript()
		if self.IsShow() and not self.toolMode:
			net.SendRefinePacket(255, 255)		# a blacksmith refine was waiting: cancelled like Zrušit
		self.dlgQuestion = None
		if not self.toolMode:
			self.toolMode = True
			self.GetChild("TitleName").SetText(crafttoolmodel.Text("TITLE"))
			self.__SetAcceptText(crafttoolmodel.Text("UPGRADE"))
			if app.ENABLE_AUTO_REFINE:
				self.checkBox.Hide()
		self.toolYang = player.GetElk()
		self.toolIds = tuple(toolIds or ())
		self.__ShowTool(None)
		self.toolCell = cell
		self.toolAsking = cell is not None
		self.SetTop()
		self.Show()

	def SetToolState(self, state):
		"""A CraftToolV1 answer (crafttoolmodel.ToolState): shown when it is about the cell the window asked for, else
		about the tool it shows."""
		if not self.toolMode or state is None:
			return
		wanted = self.toolCell if self.toolCell is not None else (
			self.toolState.cell if self.toolState is not None else None)
		if state.cell != wanted:
			return
		self.toolCell = None
		self.toolAsking = False
		self.__ShowTool(state)

	def __LeaveToolMode(self):
		"""The blacksmith mode again (Open of a refine): the original title, OK, chance line and price row."""
		if not self.toolMode:
			return
		self.__ReleaseToolCell()
		self.toolYang = None
		self.toolMode = False
		self.toolState = None
		self.toolCell = None
		self.toolAsking = False
		self.toolIds = ()
		self.GetChild("TitleName").SetText(self.blacksmithTitle)
		self.__SetAcceptText(self.blacksmithAccept)
		self.acceptButton.Enable()
		self.yangPanel.Show()
		if self.toolLossText is not None:
			self.toolLossText.Hide()
		if osfInfo.SHOW_REFINE_PERCENTAGE == True:
			self.successPercentage.Show()
			self.bonusText.Show()
		else:
			self.successPercentage.Hide()
			self.bonusText.Hide()

	def __SetAcceptText(self, text):
		self.acceptButton.SetText(text)
		if self.r1Buttons is not None:
			self.r1Buttons.Buttons()[0].SetText(text)

	def __ReleaseToolCell(self):
		"""The inventory cell of the shown tool clickable again (WJ_ENABLE_TRADABLE_ICON locks it while it is in here)."""
		if app.WJ_ENABLE_TRADABLE_ICON and self.targetItemPos >= 0 and getattr(self, "inven", None):
			self.SetCanMouseEventSlot(self.targetItemPos)

	def __AskTool(self, cell, verb="info"):
		self.toolCell = cell
		self.toolAsking = True
		net.SendChatPacket("/craft_tool %s %d" % (verb, cell))

	def __SelectToolSlot(self, slotIndex):
		"""A tool dragged from the inventory into "Před vylepšením" (tool mode): the server says what it is."""
		if not self.toolMode or not mouseModule.mouseController.isAttached():
			return
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			return
		cell = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		self.__AskTool(cell)

	def __ShowTool(self, state):
		"""One state of the tool mode: None = no tool in the slot, a state of a cell without a tool = its hint."""
		tool = state if state is not None and state.IsTool() else None
		if tool is None or tool.cell != self.targetItemPos:
			self.__ReleaseToolCell()
		self.__ClearMaterials()
		self.__Initialize()
		self.toolState = tool
		self.targetItemPos = tool.cell if tool is not None else -1
		self.__ClearComparisonSlots()
		if tool is not None:
			self.__ReadTarget(tool.cell)
			self.currentItemVnum = tool.vnum
			self.vnum = tool.next
			self.percentage = tool.chance
			self.cost = tool.price
			self.currentItemSlot.SetItemSlot(0, self.currentItemVnum, 0)
			if self.vnum:
				self.resultItemSlot.SetItemSlot(0, self.vnum, 0)
			self.currentItemSlot.RefreshSlot()
			self.resultItemSlot.RefreshSlot()
			if not tool.IsTop():
				self.__AppendPractice(tool)
				if tool.seal:
					self.__AppendCounted(tool.seal, crafttoolmodel.SEAL_NEED, tool.sealsHeld)
				for vnum, need, held in tool.materials:
					self.__AppendCounted(vnum, need, held)

		hint = crafttoolmodel.Hint(state, self.toolIds, self.__ToolGrade(tool))
		self.successPercentage.Show()
		self.bonusText.Hide()
		self.probText.SetText(hint or localeInfo.REFINE_SUCCESS_PROBALITY % (self.percentage))
		loss = self.__ToolLossText()
		if not hint and tool.ShowsLoss():
			loss.SetText(crafttoolmodel.LossText(tool))
			loss.Show()
		else:
			loss.Hide()
		if tool is not None and tool.price > 0 and not tool.IsTop():
			self.__SetCost(tool.price)
			self.yangPanel.Show()
		else:
			self.yangPanel.Hide()			# no tool, the top grade or free: no price row
		if tool is not None and tool.CanUpgrade():
			self.acceptButton.Enable()
		else:
			self.acceptButton.Disable()
		self.UpdateDialog()

	def __ToolGrade(self, tool):
		"""The "+N" of a tool at the top grade (its item name), for the hint."""
		if tool is None or not tool.IsTop():
			return None
		item.SelectItem(tool.vnum)
		return crafttoolmodel.GradeOf(item.GetItemName())

	def __AppendPractice(self, tool):
		"""The practice row: a material row (the craft's practice item in the slot, "Cvik", practice / need green or
		red) with the practice bar of the Biolog under the name (R1 look). Not a price: self.materials keeps it out."""
		index = self.materialCount
		if index >= len(self.materialRows):
			row, slot, frame, textLine, countLine = self.__CreateMaterialRow(index)
		else:
			row, slot, frame, textLine, countLine = self.materialRows[index]
		row.SetItem(0)
		slot.SetItemSlot(index, tool.icon, 0)
		slot.RefreshSlot()
		textLine.SetPackedFontColor(self.MATERIAL_NAME_COLOR)
		textLine.SetText(crafttoolmodel.Text("PRACTICE"))
		ownedcount.Paint(countLine, tool.practice, tool.need)
		if index == 0 and self.__IsR1():
			self.__PracticeBar(frame, tool.practice, tool.need)
		row.Show()
		self.materialCount += 1

	def __PracticeBar(self, frame, practice, need):
		"""The practice bar of the Biolog (root/uir1price.ProgressBar) in the name frame of row 0."""
		try:
			import uir1price
			import uir1tokens
			if self.toolBar is None:
				width = frame.GetWidth() - 2 * self.MATERIAL_TEXT_PADDING
				y = self.MATERIAL_ROW_CONTENT_HEIGHT - self.PRACTICE_BAR_BOTTOM - uir1tokens.SLIDER_H
				self.toolBar = uir1price.ProgressBar(frame, self.MATERIAL_TEXT_PADDING, y, width)
			self.toolBar.SetRatio(float(practice) / max(1, need))
			self.toolBar.Show()
		except Exception:
			import uir1price
			uir1price.TraceFailure("the practice bar of the tool upgrade")

	def __HasPracticeBar(self, rowIndex):
		return rowIndex == 0 and self.toolBar is not None and self.toolBar.track.IsShow()

	def __AppendCounted(self, vnum, need, held):
		"""An ordinary material row with the server's count (a seal or material row takes any of several items)."""
		index = self.materialCount
		self.AppendMaterial(vnum, need)
		group = crafttoolmodel.MaterialGroup(self.toolState.toolId, vnum)
		if group:
			title, members = group
			names = []
			for member in members:
				item.SelectItem(member)
				names.append(item.GetItemName())
			row, slot, frame, textLine, countLine = self.materialRows[index]
			textLine.SetText(title)
			row.SetDescription(title, names)
		ownedcount.Paint(self.materialRows[index][4], held, need)

	def __ToolLossText(self):
		"""The practice loss of a failure (band A) right on the chance line, where the blacksmith shows its bonus."""
		if self.toolLossText is None:
			line = ui.TextLine()
			line.SetParent(self.board)
			line.SetHorizontalAlignRight()
			line.SetPackedFontColor(self.MATERIAL_MISSING_COLOR)
			line.SetOutline()
			line.AddFlag("not_pick")
			self.toolLossText = line
		return self.toolLossText

	def UpdateDialog(self):
		twoColumns = self.materialCount > self.MATERIALS_PER_COLUMN
		rowsPerColumn = (self.materialCount + 1) // 2 if twoColumns else self.materialCount
		newWidth = self.WINDOW_WIDTH + (self.SECOND_COLUMN_X if twoColumns else 0)
		newHeight = self.ACTION_BOTTOM + rowsPerColumn * self.MATERIAL_ROW_HEIGHT
		if not app.ENABLE_AUTO_REFINE or self.toolMode:
			newHeight -= self.AUTO_REFINE_ROW_HEIGHT
		isR1 = self.__IsR1()
		if isR1:
			newHeight += self.R1_BUTTON_EXTRA

		chanceY = self.MATERIALS_Y + rowsPerColumn * self.MATERIAL_ROW_HEIGHT + self.CHANCE_GAP
		footerOffset = (newWidth - self.WINDOW_WIDTH) // 2
		yangY = chanceY + self.YANG_GAP
		buttonY = newHeight - 24

		for rowIndex, rowData in enumerate(self.materialRows):
			row, slot, frame, textLine, countLine = rowData
			column = rowIndex // rowsPerColumn if twoColumns else 0
			rowInColumn = rowIndex % rowsPerColumn if twoColumns else rowIndex
			row.SetPosition(self.MATERIAL_ROW_X + column * self.SECOND_COLUMN_X,
				self.MATERIALS_Y + rowInColumn * self.MATERIAL_ROW_HEIGHT)
			textY = self.PRACTICE_TEXT_Y if self.__HasPracticeBar(rowIndex) else self.MATERIAL_TEXT_CENTER_Y
			if localeInfo.IsARABIC():
				textLine.SetPosition(
					frame.GetWidth() - self.MATERIAL_TEXT_PADDING,
					textY,
				)
				countLine.SetPosition(self.MATERIAL_TEXT_PADDING, textY)
			else:
				textLine.SetPosition(self.MATERIAL_TEXT_PADDING, textY)
				countLine.SetPosition(
					frame.GetWidth() - self.MATERIAL_TEXT_PADDING,
					textY,
				)

		previewOffset = footerOffset if twoColumns else 0
		for name, x, y in (("CurrentHeader", 18, 34), ("ResultHeader", 158, 34),
				("CurrentLabel", 72, 43), ("ResultLabel", 212, 43),
				("CurrentItemSlot", 56, 58), ("UpgradeArrow", 129, 92),
				("ResultItemSlot", 196, 58)):
			self.GetChild(name).SetPosition(x + previewOffset, y)
		self.probText.SetPosition(39 + footerOffset, chanceY)
		self.bonusText.SetPosition(264 + footerOffset, chanceY)
		if self.toolLossText is not None:
			self.toolLossText.SetPosition(*self.bonusText.GetLocalPosition())
		self.yangPanel.SetPosition(footerOffset, yangY)
		self.acceptButton.SetPosition(75 + footerOffset, buttonY)
		self.cancelButton.SetPosition(148 + footerOffset, buttonY)
		if isR1:
			import uir1price
			self.r1Buttons.Place(newWidth, newHeight - uir1price.BUTTON_BOTTOM)
		if app.ENABLE_AUTO_REFINE:
			self.checkBox.SetPosition(42 + footerOffset, yangY + self.AUTO_REFINE_GAP)

		self.board.SetSize(newWidth, newHeight)
		self.titleBar.SetWidth(newWidth + 8)
		self.SetSize(newWidth, newHeight)

		(x, y) = self.GetLocalPosition()
		self.SetPosition(max(0, min(x, wndMgr.GetScreenWidth() - newWidth)),
			max(0, min(y, wndMgr.GetScreenHeight() - newHeight - 4)))

	def OpenQuestionDialog(self):
		if self.toolMode:
			# Vylepšit: the server checks everything again; the window stays open for the new state
			if not self.toolAsking and self.toolState is not None and self.toolState.CanUpgrade():
				self.__AskTool(self.toolState.cell, "up")
			return

		if app.ENABLE_AUTO_REFINE and osfInfo.IS_AUTO_REFINE:
			self.Accept()
			return

		if 100 == self.percentage:
			self.Accept()
			return

		if 5 == self.type:
			self.Accept()
			return

		if app.ENABLE_STONE_OF_BLESS:
			if 7 == self.type:
				self.Accept()
				return

		if app.ENABLE_SOUL_SYSTEM:
			if 8 == self.type or 9 == self.type:
				self.Accept()
				return

		dlgQuestion = uiCommon.QuestionDialog2()
		dlgQuestion.SetText2(localeInfo.REFINE_WARNING2)
		dlgQuestion.SetAcceptEvent(ui.__mem_func__(self.Accept))
		dlgQuestion.SetCancelEvent(ui.__mem_func__(dlgQuestion.Close))

		if self.type in (2, 3) and talismanrefine.KeepsGradeOnFailure(self.src_vnum):
			# The server always keeps a talisman's grade after a failed scroll refine.
			dlgQuestion.SetText1(localeInfo.TALISMAN_REFINE_KEEP_GRADE)
		elif 3 == self.type:
			if localeInfo.IsEUROPE():
				if dlgQuestion:
					del dlgQuestion

				dlgQuestion = uiCommon.QuestionDialog()
				dlgQuestion.SetAcceptEvent(ui.__mem_func__(self.Accept))
				dlgQuestion.SetCancelEvent(ui.__mem_func__(dlgQuestion.Close))
				dlgQuestion.SetText(localeInfo.REFINE_DESTROY_WARNING_WITH_BONUS_PERCENT_1)
			else:
				dlgQuestion.SetText1(localeInfo.REFINE_DESTROY_WARNING_WITH_BONUS_PERCENT_1)
				dlgQuestion.SetText2(localeInfo.REFINE_DESTROY_WARNING_WITH_BONUS_PERCENT_2)
		elif 2 == self.type:
			dlgQuestion.SetText1(localeInfo.REFINE_DOWN_GRADE_WARNING)
		elif gloverefine.KeepsItemOnFailure(self.src_vnum):
			# The server keeps these gloves after a failed refine.
			dlgQuestion.SetText1(localeInfo.GLOVE_REFINE_KEEP_GRADE)
		else:
			dlgQuestion.SetText1(localeInfo.REFINE_DESTROY_WARNING)

		dlgQuestion.Open()
		self.dlgQuestion = dlgQuestion

	def Accept(self):
		if app.ENABLE_AUTO_REFINE:
			net.SendRefinePacket(self.targetItemPos, self.type)
		else:
			net.SendRefinePacket(self.targetItemPos, self.type)
			self.Close()

	def CancelRefine(self):
		if self.toolMode:
			self.Close()			# no blacksmith refine is waiting on the server
			return

		net.SendRefinePacket(255, 255)
		self.Close()

		if app.WJ_ENABLE_TRADABLE_ICON:
			self.SetCanMouseEventSlot(self.targetItemPos)

		if app.ENABLE_AUTO_REFINE:
			osfInfo.AUTO_REFINE = False
			osfInfo.AUTO_REFINE_TYPE = 0
			osfInfo.AUTO_REFINE_DATA = {
				"ITEM" : [-1, -1],
				"NPC" : [0, -1, -1, 0]
			}

	if app.ENABLE_AUTO_REFINE:
		def AutoRefine(self, checkType, autoFlag):
			osfInfo.IS_AUTO_REFINE = autoFlag

		def CheckRefine(self, isFail):
			if self.toolMode:
				return				# the tool window stays open: the server sends the new state
			if osfInfo.IS_AUTO_REFINE:
				if osfInfo.AUTO_REFINE_TYPE == 1:
					if osfInfo.AUTO_REFINE_DATA["ITEM"][0] != -1 and osfInfo.AUTO_REFINE_DATA["ITEM"][1] != -1:
						scrollIndex = player.GetItemIndex(osfInfo.AUTO_REFINE_DATA["ITEM"][0])
						itemIndex = player.GetItemIndex(osfInfo.AUTO_REFINE_DATA["ITEM"][1])
						current_level = player.GetItemGrade(osfInfo.AUTO_REFINE_DATA["ITEM"][1])
						max_level = wiki.GetRefineMaxLevel(itemIndex)

						if current_level >= max_level:
							self.Close()
						elif scrollIndex <= 0 or (current_level == max_level - 1 and not isFail):
							self.Close()
						else:
							osfInfo.AUTO_REFINE = True
							net.SendItemUseToItemPacket(osfInfo.AUTO_REFINE_DATA["ITEM"][0], osfInfo.AUTO_REFINE_DATA["ITEM"][1])

				elif osfInfo.AUTO_REFINE_TYPE == 2:
					npcData = osfInfo.AUTO_REFINE_DATA["NPC"]
					if npcData[0] != 0 and npcData[1] != -1 and npcData[2] != -1 and npcData[3] != 0:
						itemIndex = player.GetItemIndex(npcData[1], npcData[2])
						current_level = player.GetItemGrade(npcData[1])
						max_level = wiki.GetRefineMaxLevel(itemIndex)
						if current_level >= max_level:
							self.Close()
						elif (current_level == max_level - 1 and not isFail) or isFail:
							self.Close()
						else:
							osfInfo.AUTO_REFINE = True
							net.SendGiveItemPacket(npcData[0], npcData[1], npcData[2], npcData[3])
				else:
					self.Close()
			else:
				self.Close()

	def OnPressEscapeKey(self):
		self.CancelRefine()
		return True

	def BindInterface(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)

	if app.WJ_ENABLE_TRADABLE_ICON:
		def SetInven(self, inven):
			self.inven = inven

		def SetCanMouseEventSlot(self, idx):
			if idx >= INVENTORY_PAGE_SIZE:
				if app.ENABLE_EXTEND_INVEN_SYSTEM:
					page = self.inven.GetInventoryPageIndex() # 0,1,2,3
					idx -= (page * INVENTORY_PAGE_SIZE)
				else:
					idx -= INVENTORY_PAGE_SIZE

			self.inven.wndItem.SetCanMouseEventSlot(idx)

		def OnUpdate(self):
			if not self.inven:
				return

			targetItemPos = self.targetItemPos
			if targetItemPos <= 0:
				return

			page = self.inven.GetInventoryPageIndex() # range 0 ~ 1

			if (page * INVENTORY_PAGE_SIZE) <= targetItemPos < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
				lock_idx = targetItemPos - (page * INVENTORY_PAGE_SIZE)
				self.inven.wndItem.SetCantMouseEventSlot(lock_idx)
if app.ENABLE_REFINE_ELEMENT_SYSTEM:
	import chat

	MIN_REFINE_LEVEL = 7

	REFINE_ELEMENT_ITEM_TYPE_TUPLE = (item.ITEM_TYPE_WEAPON,)
	REFINE_ELEMENT_KIND_TUPLE = (item.APPLY_ENCHANT_ELEC, item.APPLY_ENCHANT_FIRE, item.APPLY_ENCHANT_ICE, item.APPLY_ENCHANT_WIND, item.APPLY_ENCHANT_EARTH, item.APPLY_ENCHANT_DARK)

	REFINE_ELEMENT_UPGRADE_YANG = 3000000
	REFINE_ELEMENT_DOWNGRADE_YANG = 10000000
	REFINE_ELEMENT_CHANGE_YANG = 10000000

	def IsSealedRefineElementTarget(item_window, item_pos):
		if not app.ENABLE_SOUL_BIND_SYSTEM:
			return False

		sealDate = player.GetItemSealDate(item_window, item_pos)
		if sealDate == item.E_SEAL_DATE_UNLIMITED_TIMESTAMP:
			return True

		if sealDate > 0:
			return True

		return False

	class RefineElementChangeDialog(ui.ScriptWindow):
		def CanRefineElementChange(cls, material_window, material_pos, item_window, item_pos, is_fail_msg = True, is_yang_check = True):
			if item_window != player.INVENTORY:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if player.IsEquipmentSlot(item_pos):
				if is_fail_msg:
					if app.ENABLE_CHANGE_LOOK_SYSTEM:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHANGE_LOOK_DO_NOT_EQUIP_ITEM)
					else:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			material_vnum = player.GetItemIndex(material_window, material_pos)
			if material_vnum == 0:
				return False

			item_vnum = player.GetItemIndex(item_window, item_pos)
			if item_vnum == 0:
				return False

			item.SelectItem(item_vnum)
			if not item.GetItemType() in REFINE_ELEMENT_ITEM_TYPE_TUPLE:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if item.GetRefineLevel() < MIN_REFINE_LEVEL:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_ENOUGHT_GRADE)
				return False

			if IsSealedRefineElementTarget(item_window, item_pos):
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			refine_element = player.GetItemRefineElement(item_window, item_pos)
			if refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_GRADE] == 0:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if is_yang_check:
				if player.GetElk() < REFINE_ELEMENT_CHANGE_YANG:
					if is_fail_msg:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_ENOUGHT_YANG)
					return False

			return True

		CanRefineElementChange = classmethod(CanRefineElementChange)

		def __init__(self):
			ui.ScriptWindow.__init__(self)
			import uiconfirm
			uiconfirm.Bind(self, 'AcceptButton', child=True)
			self.is_loaded = False

			self.tabButtonDict = {}
			self.cost_text = None

			self.popup_dlg = None
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.inven = None

			self.disable_type = 0
			self.apply_type = 0
			self.refine_type = 0
			self.material_pos = 0
			self.item_pos = 0
			self.item_name = None
			self.change_element = None

		def __del__(self):
			ui.ScriptWindow.__del__(self)

		def __Clear(self):
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.__SetMouseEventSlot(False)

			self.disable_type = 0
			self.apply_type = 0
			self.refine_type = 0
			self.material_pos = 0
			self.item_pos = 0
			self.item_name = None
			self.change_element = None

			self.Hide()

		def __LoadScript(self):
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "UIScript/RefineElementChange.py")
			except:
				import exception
				exception.Abort("RefineElementChangeDialog.__LoadScript.LoadObject")

			try:
				self.__BindObject()
			except:
				import exception
				exception.Abort("RefineElementChangeDialog.__LoadScript.BindObject")

			try:
				self.__BindEvent()
			except:
				import exception
				exception.Abort("RefineElementChangeDialog.__LoadScript.BindEvent")

			self.is_loaded = True

		def __BindObject(self):
			self.tabButtonDict = {
				item.APPLY_ENCHANT_FIRE : self.GetChild("FireButton"),
				item.APPLY_ENCHANT_ICE : self.GetChild("IceButton"),
				item.APPLY_ENCHANT_WIND : self.GetChild("WindButton"),
				item.APPLY_ENCHANT_ELECT : self.GetChild("ElectButton"),
				item.APPLY_ENCHANT_EARTH : self.GetChild("EarthButton"),
				item.APPLY_ENCHANT_DARK : self.GetChild("DarkButton"),
			}

			self.cost_text = self.GetChild("Cost")
			self.cost_text.SetText(localeInfo.NumberToMoneyString(REFINE_ELEMENT_CHANGE_YANG))

			self.popup_dlg = uiCommon.PopupDialog()
			self.popup_dlg.Hide()

		def __BindEvent(self):
			for key, button in self.tabButtonDict.items():
				button.SetEvent(ui.__mem_func__(self.__OnClickTabButton), key)

			self.GetChild("board").SetCloseEvent(ui.__mem_func__(self.__CancelRefine))
			self.GetChild("AcceptButton").SetEvent(self.__ClickAcceptButton)
			self.GetChild("CancelButton").SetEvent(self.__CancelRefine)

		def __ClickAcceptButton(self):
			if self.refine_type != player.REFINE_ELEMENT_CHANGE:
				return

			if self.disable_type == self.apply_type:
				return

			if self.CanRefineElementChange(player.INVENTORY, self.material_pos, player.INVENTORY, self.item_pos):
				net.SendRefineElementPacket(True, self.apply_type)

		def __CancelRefine(self):
			net.SendRefineElementPacket(False)
			self.__Clear()

		def __DisableButton(self, key):
			for apply_type, button in self.tabButtonDict.items():
				button.SetUp()
				button.Enable()

			self.tabButtonDict[key].Disable()

		def __OnClickTabButton(self, key):
			for apply_type, button in self.tabButtonDict.items():
				if apply_type != key and apply_type != self.disable_type:
					button.SetUp()

			self.apply_type = key
			self.change_element = self.tabButtonDict[key].GetText()

		def __Open(self, refine_type, material_pos, item_pos):
			if False == self.is_loaded:
				self.__LoadScript()

			refine_element = player.GetItemRefineElement(item_pos)
			self.disable_type = refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_APPLY_TYPE]

			self.refine_type = refine_type
			self.material_pos = material_pos
			self.item_pos = item_pos

			item_vnum = player.GetItemIndex(item_pos)
			if item_vnum != 0:
				item.SelectItem(item_vnum)
				self.item_name = item.GetItemName()

			self.__DisableButton(self.disable_type)
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.__SetMouseEventSlot(True)

			self.SetTop()
			self.Show()

		def Destroy(self):
			self.ClearDictionary()

			self.tabButtonDict = {}
			self.cost_text = None

			self.popup_dlg = None
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.inven = None

			self.__Clear()

		def OnPressEscapeKey(self):
			self.__CancelRefine()
			return True

		if app.WJ_ENABLE_TRADABLE_ICON:
			def __SetMouseEventSlot(self, is_cant_mouse_event):
				if not self.inven:
					return

				page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
				min_range = page * player.INVENTORY_PAGE_SIZE
				max_range = (page + 1) * player.INVENTORY_PAGE_SIZE

				if self.material_pos >= 0:
					if (min_range) <= self.material_pos < (max_range): # range 0 ~ 44, 45 ~ 89
						lock_idx = self.material_pos - (min_range)
						if is_cant_mouse_event:
							self.inven.wndItem.SetCantMouseEventSlot(lock_idx)
						else:
							self.inven.wndItem.SetCanMouseEventSlot(lock_idx)

				if self.item_pos >= 0:
					if (min_range) <= self.item_pos < (max_range): # range 0 ~ 44, 45 ~ 89
						lock_idx = self.item_pos - (min_range)
						if is_cant_mouse_event:
							self.inven.wndItem.SetCantMouseEventSlot(lock_idx)
						else:
							self.inven.wndItem.SetCanMouseEventSlot(lock_idx)

			def SetInven(self, inven):
				self.inven = inven

			def OnUpdate(self):
				if not self.inven:
					return

				self.__SetMouseEventSlot(True)

		def RefineElementChangeProcess(self, type, refine_type, data):
			if type == player.REFINE_ELEMENT_GC_OPEN:
				if refine_type == player.REFINE_ELEMENT_CHANGE:
					material_pos, item_pos = data
					self.__Open(refine_type, material_pos, item_pos)

			elif type == player.REFINE_ELEMENT_GC_RESULT:
				if refine_type == player.REFINE_ELEMENT_CHANGE:
					if self.popup_dlg:
						self.popup_dlg.SetText(localeInfo.REFINE_ELEMENT_CHANGE_TEXT % (self.item_name, self.change_element))
						self.popup_dlg.Open()

				self.__Clear()

	class RefineElementDialog(ui.ScriptWindow):
		REFINE_ELEMENT_RANDOM_VALUE_MIN = 1
		REFINE_ELEMENT_RANDOM_VALUE_MAX = 8

		REFINE_ELEMENT_RANDOM_BONUS_VALUE_MIN = 2
		REFINE_ELEMENT_RANDOM_BONUS_VALUE_MAX = 12

		def CanRefineElementUpgrade(cls, material_window, material_pos, item_window, item_pos, is_fail_msg = True, is_yang_check = True):
			if item_window != player.INVENTORY:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if player.IsEquipmentSlot(item_pos):
				if is_fail_msg:
					if app.ENABLE_CHANGE_LOOK_SYSTEM:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHANGE_LOOK_DO_NOT_EQUIP_ITEM)
					else:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			material_vnum = player.GetItemIndex(material_window, material_pos)
			if material_vnum == 0:
				return False

			item.SelectItem(material_vnum)
			material_element_apply_type = item.GetValue(0)

			item_vnum = player.GetItemIndex(item_window, item_pos)
			if item_vnum == 0:
				return False

			item.SelectItem(item_vnum)
			if not item.GetItemType() in REFINE_ELEMENT_ITEM_TYPE_TUPLE:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if item.GetRefineLevel() < MIN_REFINE_LEVEL:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_ENOUGHT_GRADE)
				return False

			if IsSealedRefineElementTarget(item_window, item_pos):
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			refine_element = player.GetItemRefineElement(item_window, item_pos)
			if refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_APPLY_TYPE] != 0 and\
				refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_APPLY_TYPE] != material_element_apply_type:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_EXIST)
				return False

			if refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_GRADE] >= item.REFINE_ELEMENT_MAX:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_GRADE_MAX)
				return False

			if is_yang_check:
				if player.GetElk() < REFINE_ELEMENT_UPGRADE_YANG:
					if is_fail_msg:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_ENOUGHT_YANG)
					return False

			return True

		def CanRefineElementDowngrade(cls, material_window, material_pos, item_window, item_pos, is_fail_msg = True, is_yang_check = True):
			if item_window != player.INVENTORY:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if player.IsEquipmentSlot(item_pos):
				if is_fail_msg:
					if app.ENABLE_CHANGE_LOOK_SYSTEM:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHANGE_LOOK_DO_NOT_EQUIP_ITEM)
					else:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			material_vnum = player.GetItemIndex(material_window, material_pos)
			if material_vnum == 0:
				return False

			item_vnum = player.GetItemIndex(item_window, item_pos)
			if item_vnum == 0:
				return False

			item.SelectItem(item_vnum)
			if not item.GetItemType() in REFINE_ELEMENT_ITEM_TYPE_TUPLE:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if item.GetRefineLevel() < MIN_REFINE_LEVEL:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_ENOUGHT_GRADE)
				return False

			if IsSealedRefineElementTarget(item_window, item_pos):
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			refine_element = player.GetItemRefineElement(item_window, item_pos)
			if refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_GRADE] == 0:
				if is_fail_msg:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_EXSIT)
				return False

			if is_yang_check:
				if player.GetElk() < REFINE_ELEMENT_DOWNGRADE_YANG:
					if is_fail_msg:
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_ELEMENT_NOT_ENOUGHT_YANG)
					return False

			return True

		CanRefineElementUpgrade = classmethod(CanRefineElementUpgrade)
		CanRefineElementDowngrade = classmethod(CanRefineElementDowngrade)

		def __init__(self):
			ui.ScriptWindow.__init__(self)
			import uiconfirm
			uiconfirm.Bind(self, 'AcceptButton', child=True)
			self.is_loaded = False

			self.board = None
			self.title_bar = None
			self.title_name = None
			self.cost_text = None
			self.item_image = None
			self.slot_list = []

			self.tooltip = None
			self.popup_dlg = None
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.inven = None

			self.refine_type = 0
			self.material_pos = 0
			self.item_pos = 0
			self.apply_type = 0

		def __del__(self):
			ui.ScriptWindow.__del__(self)

		def __Clear(self):
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.__SetMouseEventSlot(False)

			self.refine_type = 0
			self.material_pos = 0
			self.item_pos = 0
			self.apply_type = 0

			self.Hide()

		def __LoadScript(self):
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "UIScript/RefineDialog.py")
			except:
				import exception
				exception.Abort("RefineElementDialog.__LoadScript.LoadObject")

			try:
				self.board = self.GetChild("Board")
				self.title_bar = self.GetChild("TitleBar")
				self.cost_text = self.GetChild("Cost")
				self.GetChild("SuccessPercentage").Hide()
				self.GetChild("AcceptButton").SetEvent(self.__ClickAcceptButton)
				self.GetChild("CancelButton").SetEvent(self.__CancelRefine)
			except:
				import exception
				exception.Abort("RefineDialog.__LoadScript.BindObject")

			tooltip = uiToolTip.ItemToolTip()
			tooltip.SetParent(self)
			tooltip.SetFollow(False)
			tooltip.SetPosition(15, 38)
			tooltip.Show()
			self.tooltip = tooltip

			self.slot_list = []
			for i in range(3):
				slot = self.__MakeSlot()
				slot.SetParent(tooltip)
				slot.SetWindowVerticalAlignCenter()
				self.slot_list.append(slot)

			item_image = self.__MakeItemImage()
			item_image.SetParent(tooltip)
			item_image.SetWindowVerticalAlignCenter()
			item_image.SetPosition(-35, 0)
			self.item_image = item_image

			self.popup_dlg = uiCommon.PopupDialog()
			self.popup_dlg.Hide()

			self.title_bar.SetCloseEvent(ui.__mem_func__(self.__CancelRefine))
			self.is_loaded = True

		def __MakeSlot(self):
			slot = ui.ImageBox()
			slot.LoadImage("d:/ymir work/ui/public/slot_base.sub")
			slot.Show()
			return slot

		def __MakeItemImage(self):
			item_image = ui.ImageBox()
			item_image.Show()
			return item_image

		def __MakeThinBoard(self):
			thinboard = ui.ThinBoard()
			thinboard.SetParent(self)
			thinboard.Show()
			return thinboard

		def __UpdateDialog(self):
			new_width = self.tooltip.GetWidth() + 60
			new_height = self.tooltip.GetHeight() + 103

			if localeInfo.IsARABIC():
				self.board.SetPosition(new_width, 0)

				(x, y) = self.title_bar.GetLocalPosition()
				self.title_bar.SetPosition(new_width - 15, y)

			self.board.SetSize(new_width, new_height)
			self.tooltip.SetPosition(15 + 35, 38)
			self.title_bar.SetWidth(new_width + 8)
			self.SetSize(new_width, new_height)

			(x, y) = self.GetLocalPosition()
			self.SetPosition(x, y)

		def __UpgradeUIOpen(self, material_pos, item_pos):
			material_vnum = player.GetItemIndex(material_pos)
			if material_vnum == 0:
				return

			item.SelectItem(material_vnum)
			self.apply_type = item.GetValue(0)

			item_vnum = player.GetItemIndex(item_pos)
			if item_vnum == 0:
				return

			metin_slot = [player.GetItemMetinSocket(item_pos, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attr_slot = [player.GetItemAttribute(item_pos, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			refine_element = player.GetItemRefineElement(item_pos)
			apply_random_list = [player.GetItemApplyRandom(item_pos, i) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)] if app.ENABLE_APPLY_RANDOM else []
			set_value = player.GetItemSetValue(item_pos) if getattr(app, "ENABLE_SET_ITEM", False) else 0

			new_refine_element = (
				self.apply_type,
				refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_GRADE] + 1,
				refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_VALUE],
				refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_BONUS],
			)

			self.tooltip.ClearToolTip()
			self.tooltip.isRefineElementItem = True
			self.tooltip.AddRefineItemData(item_vnum, metin_slot, attr_slot, None, 0, new_refine_element, apply_random_list, set_value)

			item.SelectItem(item_vnum)
			self.item_image.LoadImage(item.GetIconImageFileName())

			x_slot_count, y_slot_count = item.GetItemSize()
			for slot in self.slot_list:
				slot.Hide()

			for i in range(min(3, y_slot_count)):
				self.slot_list[i].SetPosition(-35, i * 32 - (y_slot_count - 1) * 16)
				self.slot_list[i].Show()

			self.cost_text.SetText(localeInfo.REFINE_COST % REFINE_ELEMENT_UPGRADE_YANG)

		def __DowngradeUIOpen(self, material_pos, item_pos):
			material_vnum = player.GetItemIndex(material_pos)
			if material_vnum == 0:
				return

			item_vnum = player.GetItemIndex(item_pos)
			if item_vnum == 0:
				return

			metin_slot = [player.GetItemMetinSocket(item_pos, i) for i in range(player.METIN_SOCKET_MAX_NUM)]
			attr_slot = [player.GetItemAttribute(item_pos, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			refine_element = player.GetItemRefineElement(item_pos)
			apply_random_list = [player.GetItemApplyRandom(item_pos, i) for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM)] if app.ENABLE_APPLY_RANDOM else []
			set_value = player.GetItemSetValue(item_pos) if getattr(app, "ENABLE_SET_ITEM", False) else 0

			new_grade = refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_GRADE] - 1
			new_refine_element = (
				0 if new_grade <= 0 else refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_APPLY_TYPE],
				new_grade,
				refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_VALUE],
				refine_element[uiToolTip.ItemToolTip.REFINE_ELEMENT_INDEX_BONUS],
			)

			self.tooltip.ClearToolTip()
			self.tooltip.isRefineElementItem = False
			self.tooltip.AddRefineItemData(item_vnum, metin_slot, attr_slot, None, 0, new_refine_element, apply_random_list, set_value)

			item.SelectItem(item_vnum)
			self.item_image.LoadImage(item.GetIconImageFileName())

			x_slot_count, y_slot_count = item.GetItemSize()
			for slot in self.slot_list:
				slot.Hide()

			for i in range(min(3, y_slot_count)):
				self.slot_list[i].SetPosition(-35, i * 32 - (y_slot_count - 1) * 16)
				self.slot_list[i].Show()

			self.cost_text.SetText(localeInfo.REFINE_COST % REFINE_ELEMENT_DOWNGRADE_YANG)

		def __Open(self, refine_type, material_pos, item_pos):
			if False == self.is_loaded:
				self.__LoadScript()

			self.refine_type = refine_type
			self.material_pos = material_pos
			self.item_pos = item_pos

			if app.WJ_ENABLE_TRADABLE_ICON:
				self.__SetMouseEventSlot(True)

			if refine_type == player.REFINE_ELEMENT_UPGRADE:
				self.__UpgradeUIOpen(material_pos, item_pos)
			elif refine_type == player.REFINE_ELEMENT_DOWNGRADE:
				self.__DowngradeUIOpen(material_pos, item_pos)

			self.__UpdateDialog()

			self.SetTop()
			self.Show()

		def __ClickAcceptButton(self):
			if self.refine_type == player.REFINE_ELEMENT_UPGRADE:
				if self.CanRefineElementUpgrade(player.INVENTORY, self.material_pos, player.INVENTORY, self.item_pos):
					net.SendRefineElementPacket(True)

			elif self.refine_type == player.REFINE_ELEMENT_DOWNGRADE:
				if self.CanRefineElementDowngrade(player.INVENTORY, self.material_pos, player.INVENTORY, self.item_pos):
					net.SendRefineElementPacket(True)

		def __CancelRefine(self):
			net.SendRefineElementPacket(False)
			self.__Clear()

		if app.WJ_ENABLE_TRADABLE_ICON:
			def __SetMouseEventSlot(self, is_cant_mouse_event):
				if not self.inven:
					return

				page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
				min_range = page * player.INVENTORY_PAGE_SIZE
				max_range = (page + 1) * player.INVENTORY_PAGE_SIZE

				if self.material_pos >= 0:
					if (min_range) <= self.material_pos < (max_range): # range 0 ~ 44, 45 ~ 89
						lock_idx = self.material_pos - (min_range)
						if is_cant_mouse_event:
							self.inven.wndItem.SetCantMouseEventSlot(lock_idx)
						else:
							self.inven.wndItem.SetCanMouseEventSlot(lock_idx)

				if self.item_pos >= 0:
					if (min_range) <= self.item_pos < (max_range): # range 0 ~ 44, 45 ~ 89
						lock_idx = self.item_pos - (min_range)
						if is_cant_mouse_event:
							self.inven.wndItem.SetCantMouseEventSlot(lock_idx)
						else:
							self.inven.wndItem.SetCanMouseEventSlot(lock_idx)

			def SetInven(self, inven):
				self.inven = inven

			def OnUpdate(self):
				if not self.inven:
					return

				self.__SetMouseEventSlot(True)

		def Destroy(self):
			self.ClearDictionary()

			self.board = None
			self.title_bar = None
			self.title_name = None
			self.cost_text = None
			self.item_image = None
			self.slot_list = []

			self.tooltip = None
			self.popup_dlg = None
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.inven = None

			self.__Clear()

		def OnPressEscapeKey(self):
			self.__CancelRefine()
			return True

		def RefineElementProcess(self, type, refine_type, data):
			if type == player.REFINE_ELEMENT_GC_OPEN:
				if refine_type != player.REFINE_ELEMENT_CHANGE:
					material_pos, item_pos = data
					self.__Open(refine_type, material_pos, item_pos)

			elif type == player.REFINE_ELEMENT_GC_RESULT:
				if refine_type == player.REFINE_ELEMENT_UPGRADE:
					if data:
						if self.popup_dlg:
							self.popup_dlg.SetText(localeInfo.REFINE_ELEMENT_UPGRADE_SUCCESS_TEXT)
							self.popup_dlg.Open()
					else:
						if self.popup_dlg:
							self.popup_dlg.SetText(localeInfo.REFINE_ELEMENT_UPGRADE_FAIL_TEXT)
							self.popup_dlg.Open()

				elif refine_type == player.REFINE_ELEMENT_DOWNGRADE and data:
					if self.popup_dlg:
						self.popup_dlg.SetText(localeInfo.REFINE_ELEMENT_DOWNGRADE_TEXT)
						self.popup_dlg.Open()

				self.__Clear()
