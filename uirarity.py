import chat
import grp
import item
import itemrarityaura
import raritypreview
import localeInfo
import net
import osfInfo
import player
import time
import ui
import uiToolTip
import uimaterialrow


MODE_PROMOTION = 0
MODE_REROLL = 1
RARITY_SCROLL_VNUM = 79628
RARITY_BOOSTER_VNUM = 79629
RARITY_MATERIAL_COUNT_COLOR = grp.GenerateColor(1.0, 216.0 / 255.0, 0.0, 1.0)
# The server may consume a request without answering (for example while a
# captcha blocks the session); never keep the dialog waiting forever.
RESPONSE_TIMEOUT_SECONDS = 15.0

RARITY_GRADE_NAMES = (
	localeInfo.RARITY_GRADE_NONE,
	localeInfo.RARITY_GRADE_MATNA,
	localeInfo.RARITY_GRADE_POZEHNANA,
	localeInfo.RARITY_GRADE_PRASTARA,
	localeInfo.RARITY_GRADE_ANTICKA,
	localeInfo.RARITY_GRADE_DRACI,
	localeInfo.RARITY_GRADE_ASTRALNI,
	localeInfo.RARITY_GRADE_BOZSKA,
)

RARITY_GRADE_COLORS = (
	grp.GenerateColor(0.65, 0.65, 0.65, 1.0),
	grp.GenerateColor(0.58, 0.58, 0.58, 1.0),
	grp.GenerateColor(0.95, 0.95, 0.95, 1.0),
	grp.GenerateColor(0.30, 0.82, 0.35, 1.0),
	grp.GenerateColor(0.30, 0.55, 1.00, 1.0),
	grp.GenerateColor(1.00, 0.55, 0.18, 1.0),
	grp.GenerateColor(0.70, 0.35, 1.00, 1.0),
	grp.GenerateColor(1.00, 0.82, 0.20, 1.0),
)

RESULT_MESSAGES = {
	getattr(net, "RARITY_RESULT_DISABLED", 2): "RARITY_RESULT_DISABLED",
	getattr(net, "RARITY_RESULT_INVALID_TARGET", 3): "RARITY_RESULT_INVALID_TARGET",
	getattr(net, "RARITY_RESULT_LEGACY_RARE", 4): "RARITY_RESULT_LEGACY_RARE",
	getattr(net, "RARITY_RESULT_MISSING_RESOURCES", 5): "RARITY_RESULT_MISSING_RESOURCES",
	getattr(net, "RARITY_RESULT_STALE_PREVIEW", 6): "RARITY_RESULT_STALE_PREVIEW",
	getattr(net, "RARITY_RESULT_CONFLICT", 7): "RARITY_RESULT_CONFLICT",
	getattr(net, "RARITY_RESULT_DUPLICATE", 8): "RARITY_RESULT_DUPLICATE",
	getattr(net, "RARITY_RESULT_INTERNAL", 9): "RARITY_RESULT_INTERNAL",
}


def GradeName(grade):
	grade = max(0, min(int(grade), len(RARITY_GRADE_NAMES) - 1))
	return RARITY_GRADE_NAMES[grade]


def GradeColor(grade):
	grade = max(0, min(int(grade), len(RARITY_GRADE_COLORS) - 1))
	return RARITY_GRADE_COLORS[grade]


def ResultText(result):
	key = RESULT_MESSAGES.get(int(result), "RARITY_RESULT_INTERNAL")
	return getattr(localeInfo, key)


def TimeoutText():
	return getattr(localeInfo, "RARITY_TIMEOUT", localeInfo.RARITY_REQUEST_FAILED)


def Now():
	return time.time()


def CommitResultText(mode, result, succeeded, grade):
	if int(result) == getattr(net, "RARITY_RESULT_OK", 0):
		if bool(succeeded):
			if int(mode) == MODE_REROLL:
				return localeInfo.RARITY_REROLL_SUCCESS
			return localeInfo.RARITY_PROMOTION_SUCCESS % GradeName(grade)
		return localeInfo.RARITY_REROLL_FAILED if int(mode) == MODE_REROLL else localeInfo.RARITY_PROMOTION_FAILED
	if int(result) == getattr(net, "RARITY_RESULT_ROLL_FAILED", 1):
		return localeInfo.RARITY_REROLL_FAILED if int(mode) == MODE_REROLL else localeInfo.RARITY_PROMOTION_FAILED
	return ResultText(result)


def VisiblePromotionCosts(costs):
	controlVnums = (RARITY_SCROLL_VNUM, RARITY_BOOSTER_VNUM)
	return [
		(int(vnum), int(count))
		for vnum, count in costs
		if int(vnum) not in controlVnums
	]


def HasEnoughRarityMaterial(owned, required):
	return int(owned) >= int(required)


def FormatRarityPercent(chanceBp):
	chanceBp = int(chanceBp)
	sign = "-" if chanceBp < 0 else ""
	whole, fraction = divmod(abs(chanceBp), 100)
	if not fraction:
		return "%s%d" % (sign, whole)
	return "%s%d.%s" % (sign, whole, ("%02d" % fraction).rstrip("0"))


def FormatRarityChance(chanceBp):
	template = localeInfo.RARITY_CHANCE
	if "%.2f" in template:
		template = template.replace("%.2f", "%s")
	return template % FormatRarityPercent(chanceBp)


def FormatRarityBonus(percent):
	return getattr(localeInfo, "RARITY_BONUS", "[Bonus + %d%%]") % int(percent)


class RarityDialog(ui.ScriptWindow):
	MAX_COST_ROWS = 7
	WINDOW_WIDTH = 284
	MATERIALS_Y = 194
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
	CONTROL_GAP = 35
	CHECKBOX_ROW_HEIGHT = 24
	CHECKBOX_ROW_GAP = 4
	CONTROL_ROW_HEIGHT = CHECKBOX_ROW_HEIGHT + CHECKBOX_ROW_GAP
	STATUS_ROW_HEIGHT = 23
	ACTION_BOTTOM_MARGIN = 24

	pendingSince = 0.0
	lateCommit = False
	lateCommitMode = None
	rerollQuestion = None

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.interface = None
		self.isLoaded = False
		self.mode = MODE_PROMOTION
		self.targetSlot = -1
		self.currentPreviewGrade = None
		self.targetPreviewGrade = None
		self.previewRequestId = 0
		self.boosterAvailable = False
		self.boosterSelected = False
		self.visibleMaterialCount = 1
		self.visibleBooster = False
		self.statusMessage = ""
		self.fastRefineSelected = False
		self.waiting = False
		self.pendingPreview = False
		self.pendingCommit = False
		self.discardPendingPreview = False
		self.materialRows = []
		self.yangParts = []
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		if self.isLoaded:
			return
		loader = ui.PythonScriptLoader()
		loader.LoadScriptFile(self, "uiscript/raritydialog.py")
		self.board = self.GetChild("Board")
		self.titleBar = self.GetChild("TitleBar")
		self.currentItemSlot = self.GetChild("CurrentItemSlot")
		self.resultItemSlot = self.GetChild("ResultItemSlot")
		self.upgradeArrow = self.GetChild("UpgradeArrow")
		self.currentGradeText = self.GetChild("CurrentGradeText")
		self.targetGradeText = self.GetChild("TargetGradeText")
		self.chanceText = self.GetChild("SuccessPercentage")
		self.bonusText = self.GetChild("BonusText")
		self.yangPanel = self.GetChild("YangPanel")
		self.boosterCheck = self.GetChild("BoosterCheckBox")
		self.fastRefineCheck = self.GetChild("AutoRefineCheckBox")
		self.statusText = self.GetChild("StatusText")
		self.acceptButton = self.GetChild("AcceptButton")
		self.cancelButton = self.GetChild("CancelButton")
		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		self.acceptButton.SetEvent(ui.__mem_func__(self.__Confirm))
		self.cancelButton.SetEvent(ui.__mem_func__(self.Close))
		self.currentItemSlot.SetOverInItemEvent(
			ui.__mem_func__(self.OverInTargetItem))
		self.currentItemSlot.SetOverOutItemEvent(
			ui.__mem_func__(self.OverOutItem))
		self.resultItemSlot.SetOverInItemEvent(
			ui.__mem_func__(self.OverInResultItem))
		self.resultItemSlot.SetOverOutItemEvent(
			ui.__mem_func__(self.OverOutItem))
		self.toolTipItem = uiToolTip.ItemToolTip()
		self.toolTipItem.HideToolTip()

		self.boosterCheck.SetToggleDownEvent(
			ui.__mem_func__(self.__SetBooster), "ON_CHECK", True)
		self.boosterCheck.SetToggleUpEvent(
			ui.__mem_func__(self.__SetBooster), "ON_UNCHECK", False)
		self.boosterCheck.SetUp()
		self.boosterCheck.Hide()

		self.fastRefineCheck.SetToggleDownEvent(
			ui.__mem_func__(self.__SetFastRefine), "ON_CHECK", True)
		self.fastRefineCheck.SetToggleUpEvent(
			ui.__mem_func__(self.__SetFastRefine), "ON_UNCHECK", False)
		self.fastRefineCheck.SetUp()
		self.fastRefineCheck.Hide()

		self.__CreateYangRow()
		for index in range(self.MAX_COST_ROWS):
			self.materialRows.append(self.__CreateMaterialRow(index))
		self.__ResizeForMaterials(1, False)
		self.isLoaded = True
		self.Hide()

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

	def __CreateMaterialRow(self, index):
		row = uimaterialrow.MaterialRow(
			self.toolTipItem, ui.__mem_func__(self.__SearchMaterial))
		row.SetParent(self)
		row.SetPosition(
			self.MATERIAL_ROW_X,
			self.MATERIALS_Y + int(index) * self.MATERIAL_ROW_HEIGHT,
		)
		row.SetSize(250, self.MATERIAL_ROW_CONTENT_HEIGHT)

		slot = ui.SlotWindow()
		slot.SetParent(row)
		slot.SetPosition(0, self.MATERIAL_SLOT_Y)
		slot.SetSize(32, 32)
		slot.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		slot.AppendSlot(index, 0, 0, 32, 32)
		slot.AddFlag("not_pick")
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
		countLine.SetPackedFontColor(RARITY_MATERIAL_COUNT_COLOR)
		countLine.SetOutline()
		countLine.SetFeather(False)
		countLine.AddFlag("not_pick")
		countLine.Show()

		row.Hide()
		return (row, slot, frame, textLine, countLine)

	def __ResizeForMaterials(self, materialCount, withBooster, withStatus=False):
		rowCount = max(1, min(self.MAX_COST_ROWS, int(materialCount)))
		self.visibleMaterialCount = rowCount
		self.visibleBooster = bool(withBooster)
		materialsHeight = rowCount * self.MATERIAL_ROW_HEIGHT

		chanceY = self.MATERIALS_Y + materialsHeight + self.CHANCE_GAP
		yangY = chanceY + self.YANG_GAP
		controlY = yangY + self.CONTROL_GAP
		boosterY = controlY
		fastRefineY = controlY + self.CONTROL_ROW_HEIGHT if withBooster else controlY
		statusY = fastRefineY + self.CONTROL_ROW_HEIGHT
		buttonY = statusY + (self.STATUS_ROW_HEIGHT if withStatus else 0)
		windowHeight = buttonY + self.ACTION_BOTTOM_MARGIN

		for index, rowData in enumerate(self.materialRows):
			rowData[0].SetPosition(
				self.MATERIAL_ROW_X,
				self.MATERIALS_Y + index * self.MATERIAL_ROW_HEIGHT,
			)
		self.chanceText.SetPosition(39, chanceY)
		self.bonusText.SetPosition(264, chanceY)
		self.yangPanel.SetPosition(0, yangY)
		self.boosterCheck.SetPosition(42, boosterY)
		self.fastRefineCheck.SetPosition(42, fastRefineY)
		self.statusText.SetPosition(self.WINDOW_WIDTH // 2, statusY)
		if withStatus:
			self.statusText.Show()
		else:
			self.statusText.Hide()
		self.acceptButton.SetPosition(75, buttonY)
		self.cancelButton.SetPosition(148, buttonY)
		self.board.SetSize(self.WINDOW_WIDTH, windowHeight)
		self.titleBar.SetWidth(self.WINDOW_WIDTH + 8)
		self.SetSize(self.WINDOW_WIDTH, windowHeight)

	def Destroy(self):
		self.Close()
		self.ClearDictionary()
		self.materialRows = []
		self.yangParts = []
		self.costText = None
		self.boosterCheck = None
		self.fastRefineCheck = None
		self.toolTipItem = None
		self.interface = None

	def BindInterface(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)

	def __SearchMaterial(self, vnum):
		search = getattr(self.interface, "SearchVirtualMarketInventoryItem", None)
		if search:
			return search(vnum)
		return False

	def Open(self, mode, targetSlot):
		if mode not in (MODE_PROMOTION, MODE_REROLL):
			return False
		if targetSlot < 0 or player.IsEquipmentSlot(targetSlot):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_UNEQUIP_FIRST)
			return False
		if not getattr(net, "RequestRarityPreview", None):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_RESULT_DISABLED)
			return False
		if self.IsBusy():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_WAITING)
			return False
		if not player.GetItemIndex(player.INVENTORY, targetSlot):
			return False

		self.mode = mode
		self.targetSlot = int(targetSlot)
		self.previewRequestId = 0
		self.boosterAvailable = False
		self.boosterSelected = False
		self.fastRefineSelected = bool(osfInfo.IS_AUTO_REFINE) and mode == MODE_PROMOTION
		self.boosterCheck.SetUp()
		self.boosterCheck.Hide()
		if self.fastRefineSelected:
			self.fastRefineCheck.Down()
		else:
			self.fastRefineCheck.SetUp()
		if mode == MODE_PROMOTION:
			self.fastRefineCheck.Show()
		else:
			self.fastRefineCheck.Hide()
		self.currentGradeText.SetText("")
		self.targetGradeText.SetText("")
		self.chanceText.SetText("")
		self.bonusText.SetText(FormatRarityBonus(0))
		self.costText.SetText("")
		self.statusText.SetText("")
		self.__ClearMaterials()
		self.__ResizeForMaterials(1, False)
		self.__RefreshTarget()
		if mode == MODE_PROMOTION:
			self.SetCenterPosition()
			self.SetTop()
			self.Show()
		return self.__RequestPreview()

	def Close(self):
		self.__CloseRerollQuestion()
		if self.pendingPreview:
			self.discardPendingPreview = True
		self.previewRequestId = 0
		self.waiting = False
		self.__ClearPreview()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def IsBusy(self):
		self.ExpireStalePending()
		return bool(self.pendingPreview or self.pendingCommit)

	def ExpireStalePending(self):
		if not (self.pendingPreview or self.pendingCommit):
			return False
		if Now() - self.pendingSince < RESPONSE_TIMEOUT_SECONDS:
			return False
		if self.pendingCommit:
			# A late authoritative answer is still reported in chat.
			self.lateCommit = True
			self.lateCommitMode = self.mode
		self.pendingPreview = False
		self.pendingCommit = False
		self.discardPendingPreview = False
		if self.mode == MODE_REROLL or not self.IsShow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, TimeoutText())
			self.Close()
		else:
			self.__ClearPreview()
			self.__SetWaiting(False)
			self.__SetStatusText(TimeoutText())
		return True

	def OnUpdate(self):
		self.ExpireStalePending()

	def OverInTargetItem(self, slotIndex):
		if self.toolTipItem and self.targetSlot >= 0:
			self.toolTipItem.SetInventoryItem(self.targetSlot, player.INVENTORY)

	def OverInResultItem(self, slotIndex):
		if (self.toolTipItem and self.targetSlot >= 0 and self.previewRequestId
				and self.targetPreviewGrade is not None and not self.waiting):
			self.toolTipItem.SetInventoryItem(self.targetSlot, player.INVENTORY,
				appendShortcuts=False, rarityPreviewGrade=self.targetPreviewGrade)

	def OverOutItem(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def __RefreshTarget(self, currentGrade=None, targetGrade=None):
		vnum = player.GetItemIndex(player.INVENTORY, self.targetSlot)
		if not vnum:
			self.Close()
			return False
		if currentGrade is None:
			currentGrade = itemrarityaura.InventoryGrade(self.targetSlot)
		self.currentPreviewGrade = int(currentGrade)
		self.targetPreviewGrade = targetGrade
		self.currentItemSlot.ClearSlot(0)
		self.resultItemSlot.ClearSlot(0)
		self.currentItemSlot.SetItemSlot(0, vnum, 0)
		itemrarityaura.ApplyGrade(self.currentItemSlot, 0, currentGrade)
		self.currentGradeText.SetText(GradeName(currentGrade))
		self.currentGradeText.SetPackedFontColor(GradeColor(currentGrade))
		if targetGrade is not None:
			self.resultItemSlot.SetItemSlot(0, vnum, 0)
			itemrarityaura.ApplyGrade(self.resultItemSlot, 0, targetGrade)
		self.currentItemSlot.RefreshSlot()
		self.resultItemSlot.RefreshSlot()
		return True

	def __ClearPreview(self):
		self.previewRequestId = 0
		self.targetPreviewGrade = None
		self.OverOutItem()
		self.resultItemSlot.ClearSlot(0)
		itemrarityaura.ApplyGrade(self.resultItemSlot, 0, 0)
		self.resultItemSlot.RefreshSlot()
		self.targetGradeText.SetText("")
		self.chanceText.SetText("")
		self.bonusText.SetText("")
		self.costText.SetText("")
		self.__ClearMaterials()
		self.boosterCheck.Hide()
		self.upgradeArrow.Hide()
		self.acceptButton.Disable()
		self.__ResizeForMaterials(0, False)

	def __ShowMaximum(self, grade):
		self.__ClearPreview()
		if not self.__RefreshTarget(grade):
			return
		self.targetGradeText.SetText(localeInfo.RARITY_MAXIMUM)
		self.targetGradeText.SetPackedFontColor(GradeColor(grade))
		self.fastRefineSelected = False
		self.fastRefineCheck.SetUp()
		self.fastRefineCheck.Hide()
		self.__SetWaiting(False)
		self.__SetStatusText(localeInfo.RARITY_MAXIMUM_REACHED)

	def __ClearMaterials(self):
		for index, rowData in enumerate(self.materialRows):
			row, slot, frame, textLine, countLine = rowData
			row.SetItem(0)
			slot.ClearSlot(index)
			slot.RefreshSlot()
			textLine.SetText("")
			countLine.SetText("")
			row.Hide()

	def __SetWaiting(self, waiting):
		self.waiting = bool(waiting)
		if self.waiting:
			self.acceptButton.Disable()
			self.boosterCheck.Disable()
		else:
			if self.previewRequestId:
				self.acceptButton.Enable()
			else:
				self.acceptButton.Disable()
			self.boosterCheck.Enable()
			# Native Enable() calls SetUp(), including for toggle buttons.
			if self.boosterSelected:
				self.boosterCheck.Down()
			else:
				self.boosterCheck.SetUp()

	def __SetStatusText(self, message):
		self.statusMessage = str(message or "")
		self.statusText.SetText(self.statusMessage)
		self.__ResizeForMaterials(
			self.visibleMaterialCount,
			self.visibleBooster,
			bool(self.statusMessage),
		)

	def __RequestPreview(self, currentGrade=None):
		# Invalidate the offer without collapsing the open dialog between replies.
		self.previewRequestId = 0
		self.OverOutItem()
		if not player.GetItemIndex(player.INVENTORY, self.targetSlot):
			self.Close()
			return False
		if currentGrade is None:
			currentGrade = itemrarityaura.InventoryGrade(self.targetSlot)
		if self.mode == MODE_PROMOTION and currentGrade >= raritypreview.MAXIMUM_GRADE:
			self.__ShowMaximum(currentGrade)
			return True
		# A changed booster choice has no authoritative chance until the reply.
		self.chanceText.SetText("")
		self.bonusText.SetText("")
		self.__SetStatusText("")
		self.__SetWaiting(True)
		if self.mode == MODE_REROLL:
			sent = net.RequestRarityRerollPreview(player.INVENTORY, self.targetSlot)
		else:
			sent = net.RequestRarityPreview(player.INVENTORY, self.targetSlot, self.boosterSelected)
		if not sent:
			self.__ClearPreview()
			self.__SetWaiting(False)
			if self.mode == MODE_REROLL:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_REQUEST_FAILED)
				self.Close()
			else:
				self.__SetStatusText(localeInfo.RARITY_REQUEST_FAILED)
		else:
			self.pendingPreview = True
			self.pendingSince = Now()
		return bool(sent)

	def __SetBooster(self, eventName, selected):
		selected = bool(selected) and self.boosterAvailable and self.mode == MODE_PROMOTION
		if selected == self.boosterSelected:
			return
		self.boosterSelected = selected
		self.__RequestPreview()

	def __SetFastRefine(self, eventName, selected):
		self.fastRefineSelected = bool(selected) and self.mode == MODE_PROMOTION
		osfInfo.IS_AUTO_REFINE = self.fastRefineSelected

	def __HandleHeadlessRerollPreview(self, result, requestId):
		if int(result) != getattr(net, "RARITY_RESULT_OK", 0):
			chat.AppendChat(chat.CHAT_TYPE_INFO, ResultText(result))
			self.Close()
			return
		self.previewRequestId = int(requestId)
		self.__OpenRerollQuestion()

	def __OpenRerollQuestion(self):
		# Rerolling replaces every unlocked rarity bonus; ask before consuming.
		import uiCommon
		self.__CloseRerollQuestion()
		question = uiCommon.QuestionDialog2()
		question.SetText1(localeInfo.RARITY_REROLL_WARNING)
		question.SetText2(localeInfo.INVENTORY_REALLY_USE_ITEM2)
		question.SetAcceptEvent(ui.__mem_func__(self.__AcceptRerollQuestion))
		question.SetCancelEvent(ui.__mem_func__(self.__CancelRerollQuestion))
		question.Open()
		self.rerollQuestion = question

	def __CloseRerollQuestion(self):
		question = self.rerollQuestion
		self.rerollQuestion = None
		if question:
			question.Close()

	def __AcceptRerollQuestion(self):
		self.__CloseRerollQuestion()
		self.__Confirm()

	def __CancelRerollQuestion(self):
		self.__CloseRerollQuestion()
		self.Close()

	def OnPreviewResult(self, requestId, mode, result, currentGrade, targetGrade,
			chanceBp, yang, boosterAvailable, boosterSelected, costs):
		if not self.pendingPreview:
			return
		self.pendingPreview = False
		self.__SetWaiting(False)
		if self.discardPendingPreview:
			self.discardPendingPreview = False
			return
		if int(mode) != self.mode:
			return
		if self.mode == MODE_PROMOTION and not self.IsShow():
			return
		if self.mode == MODE_REROLL:
			self.__HandleHeadlessRerollPreview(result, requestId)
			return
		if int(result) != getattr(net, "RARITY_RESULT_OK", 0):
			self.__ClearPreview()
			if not self.__RefreshTarget(currentGrade):
				return
			if int(currentGrade) >= raritypreview.MAXIMUM_GRADE:
				self.__ShowMaximum(currentGrade)
			else:
				self.__SetStatusText(ResultText(result))
			return
		if not (0 <= int(currentGrade) < int(targetGrade) <= raritypreview.MAXIMUM_GRADE):
			self.__ClearPreview()
			self.__RefreshTarget(currentGrade)
			self.__SetStatusText(localeInfo.RARITY_RESULT_INVALID_TARGET)
			return

		self.boosterAvailable = bool(boosterAvailable)
		if bool(boosterSelected) and not self.boosterAvailable:
			self.boosterSelected = False
			self.boosterCheck.SetUp()
			self.__RequestPreview()
			return
		self.previewRequestId = int(requestId)
		self.boosterSelected = bool(boosterSelected)
		showBooster = self.mode == MODE_PROMOTION and self.boosterAvailable
		visibleCosts = VisiblePromotionCosts(costs)
		self.__ResizeForMaterials(len(visibleCosts), showBooster)
		if self.boosterSelected:
			self.boosterCheck.Down()
		else:
			self.boosterCheck.SetUp()
		if showBooster:
			self.boosterCheck.Show()
		else:
			self.boosterCheck.Hide()

		if not self.__RefreshTarget(currentGrade, int(targetGrade)):
			return
		self.upgradeArrow.Show()
		self.fastRefineCheck.Show()
		self.__SetWaiting(False)
		currentName = GradeName(currentGrade)
		targetName = GradeName(targetGrade)
		self.currentGradeText.SetText(currentName)
		self.currentGradeText.SetPackedFontColor(GradeColor(currentGrade))
		self.targetGradeText.SetText(targetName)
		self.targetGradeText.SetPackedFontColor(GradeColor(targetGrade))
		if self.mode == MODE_REROLL:
			self.chanceText.SetText(localeInfo.RARITY_REROLL_WARNING)
		else:
			self.chanceText.SetText(FormatRarityChance(chanceBp))
		self.bonusText.SetText(FormatRarityBonus(5 if self.boosterSelected else 0))
		self.costText.SetText(
			"%s %s" % (
				localeInfo.NumberToString(int(yang)),
				localeInfo.CHEQUE_SYSTEM_UNIT_YANG,
			)
		)

		self.__ClearMaterials()
		for index, row in enumerate(visibleCosts[:self.MAX_COST_ROWS]):
			vnum, count = int(row[0]), int(row[1])
			owned = int(player.GetItemCountByVnum(vnum))
			item.SelectItem(vnum)
			materialRow, materialSlot, materialFrame, materialText, materialCount = self.materialRows[index]
			materialRow.SetItem(vnum)
			materialSlot.SetItemSlot(index, vnum, count)
			materialSlot.RefreshSlot()
			hasEnough = HasEnoughRarityMaterial(owned, count)
			textColor = uiToolTip.ToolTip.TITLE_COLOR if hasEnough else uiToolTip.ToolTip.DISABLE_COLOR
			countColor = RARITY_MATERIAL_COUNT_COLOR if hasEnough else uiToolTip.ToolTip.DISABLE_COLOR
			materialText.SetText("%s x%d" % (item.GetItemName(), count))
			materialCount.SetText("[%d]" % owned)
			materialText.SetPackedFontColor(textColor)
			materialCount.SetPackedFontColor(countColor)
			if localeInfo.IsARABIC():
				materialText.SetPosition(
					materialFrame.GetWidth() - self.MATERIAL_TEXT_PADDING,
					self.MATERIAL_TEXT_CENTER_Y,
				)
				materialText.SetHorizontalAlignRight()
				materialCount.SetPosition(
					self.MATERIAL_TEXT_PADDING,
					self.MATERIAL_TEXT_CENTER_Y,
				)
				materialCount.SetHorizontalAlignLeft()
			else:
				materialText.SetPosition(
					self.MATERIAL_TEXT_PADDING,
					self.MATERIAL_TEXT_CENTER_Y,
				)
				materialText.SetHorizontalAlignLeft()
				materialCount.SetPosition(
					materialFrame.GetWidth() - self.MATERIAL_TEXT_PADDING,
					self.MATERIAL_TEXT_CENTER_Y,
				)
				materialCount.SetHorizontalAlignRight()
			materialRow.Show()

	def __Confirm(self):
		if self.waiting or not self.previewRequestId:
			return
		self.__SetWaiting(True)
		if self.mode == MODE_REROLL:
			sent = net.ConfirmRarityReroll(player.INVENTORY, self.targetSlot, self.previewRequestId)
		else:
			sent = net.ConfirmRarityPromotion(player.INVENTORY, self.targetSlot,
				self.previewRequestId, self.boosterSelected)
		if not sent:
			self.__SetWaiting(False)
			if self.mode == MODE_REROLL:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_REQUEST_FAILED)
				self.Close()
			else:
				self.__SetStatusText(localeInfo.RARITY_REQUEST_FAILED)
		else:
			self.pendingCommit = True
			self.pendingSince = Now()
			self.lateCommit = False

	def __RefreshAfterFastPromotion(self, grade):
		self.previewRequestId = 0
		if int(grade) >= raritypreview.MAXIMUM_GRADE:
			self.__ShowMaximum(grade)
			return
		if self.targetSlot >= 0 and self.IsShow():
			self.__RequestPreview(grade)

	def OnCommitResult(self, requestId, mode, result, succeeded, grade):
		if not self.pendingCommit:
			if self.lateCommit and int(mode) == self.lateCommitMode:
				self.lateCommit = False
				chat.AppendChat(chat.CHAT_TYPE_INFO, CommitResultText(mode, result, succeeded, grade))
			return
		self.pendingCommit = False
		if int(mode) != self.mode:
			return
		self.__SetWaiting(False)
		message = CommitResultText(self.mode, result, succeeded, grade)
		chat.AppendChat(chat.CHAT_TYPE_INFO, message)
		if self.mode == MODE_PROMOTION and self.fastRefineSelected and int(result) in (
				getattr(net, "RARITY_RESULT_OK", 0),
				getattr(net, "RARITY_RESULT_ROLL_FAILED", 1)):
			self.__RefreshAfterFastPromotion(grade)
			return
		self.Close()
