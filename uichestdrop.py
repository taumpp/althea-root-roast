import chestpreview
import uiCommon
import snd
import wndMgr
import mouseModule
import localeInfo
import osfInfo
import ui
import uiScriptLocale
import uiToolTip
import chat
import player
import item
import app
import net
import stonecrafting
import uir1frame
import uiwheel

MAX_CHEST_OPEN_COUNT = 100
PREVIEW_CHEST_TYPES = (
	item.ITEM_TYPE_GIFTBOX,
	item.ITEM_TYPE_GACHA,
	item.ITEM_TYPE_TREASURE_BOX,
)


def GetOpenAmountFromSlider(sliderPos):
	return max(1, min(MAX_CHEST_OPEN_COUNT,
		int(sliderPos * MAX_CHEST_OPEN_COUNT)))


def GetBatchOpenCount(requestedCount, availableCount):
	return max(0, min(MAX_CHEST_OPEN_COUNT, int(requestedCount),
		int(availableCount)))


def IsPreviewChestType(itemType):
	return itemType in PREVIEW_CHEST_TYPES


def IsRequestedChestStillPresent(invItemPos, chestVnum):
	if invItemPos < 0 or chestVnum <= 0:
		return False
	return (player.GetItemIndex(invItemPos) == chestVnum and
		IsPreviewChestType(player.GetItemTypeBySlot(invItemPos)))


def FindMatchingTreasureKey(chestVnum):
	item.SelectItem(chestVnum)
	requiredKeyValue = item.GetValue(0)
	for slotIndex in range(player.INVENTORY_SLOT_COUNT):
		keyVnum = player.GetItemIndex(slotIndex)
		if keyVnum <= 0:
			continue
		item.SelectItem(keyVnum)
		if (item.GetItemType() == item.ITEM_TYPE_TREASURE_KEY and
				item.GetValue(0) == requiredKeyValue):
			return slotIndex
	return -1


class ChestDropWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.tooltipItem = None
		self.previewRequest = None
		self.previewCancel = None

		self.currentChest = 0
		self.requestedChestVnum = 0
		self.currentPage = 1
		self.openAmount = 1
		self.invItemPos = -1
		self.chestDrop = { }
		self.chestDropReply = {}
		self.stoneGradeRanges = {}
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/chestdropwindow.py")
		except:
			import exception
			exception.Abort("GemShopWindow.__LoadWindow.LoadObject")

		try:
			self.titleBar = self.GetChild("TitleBar")
			self.openCountController = self.GetChild("OpenCountController")
			self.openChestButtonSingle = self.GetChild("OpenChestButtonSingle")
			self.openChestButtonMultiple = self.GetChild("OpenChestButtonMultiple")

			self.prevButton = self.GetChild("prev_button")
			self.nextButton = self.GetChild("next_button")
			self.currentPageBack = self.GetChild("CurrentPageBack")
			self.currentPageText = self.GetChild("CurrentPage")
		except:
			import exception
			exception.Abort("GemShopWindow.__LoadWindow.BindObject")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		sliderPath = "d:/ymir work/ui/game/crimson_ember/gameoption/slider/"
		self.openCountController.SetButtonVisual(
			sliderPath, "thumb_01.tga", "thumb_02.tga", "thumb_03.tga")
		self.openCountController.SetBackgroundVisual(sliderPath + "track.tga")
		self.openCountController.SetEvent(ui.__mem_func__(self.OnChangeOpenAmount))

		self.openChestButtonSingle.SetEvent(ui.__mem_func__(self.OnClickOpenChest))
		self.openChestButtonMultiple.SetEvent(ui.__mem_func__(self.OnClickOpenChest))

		self.openChestButtonSingle.SetText(localeInfo.CHEST_DROP_QUANTITY % self.openAmount)
		self.openChestButtonMultiple.SetText(localeInfo.CHEST_DROP_QUANTITY % self.openAmount)

		self.prevButton.SetEvent(ui.__mem_func__(self.OnClickPrevPage))
		self.nextButton.SetEvent(ui.__mem_func__(self.OnClickNextPage))
		uiwheel.Pages(self, self.OnClickPrevPage, self.OnClickNextPage)		# the wheel pages the chest contents

		self.currentPageText.SetText(str(self.currentPage))

		wndItem = ui.GridSlotWindow()
		wndItem.SetParent(self)
		wndItem.SetPosition(16, 35)
		wndItem.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
		wndItem.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndItem.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		wndItem.ArrangeSlot(0, 5, 8, 32, 32, 0, 0)
		wndItem.RefreshSlot()
		uir1frame.SetSlotBase(self, wndItem, "d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		wndItem.Show()

		self.wndItem = wndItem

	def Close(self):
		if self.previewCancel:
			self.previewCancel("inventory")
		self.OverOutItem()
		self.currentChest = 0
		self.requestedChestVnum = 0
		self.invItemPos = -1
		self.chestDrop = { }
		self.chestDropReply = {}
		self.stoneGradeRanges = {}
		self.Hide()

	def Destroy(self):
		self.Close()
		self.ClearDictionary()

		self.tooltipItem = None
		self.previewRequest = None
		self.previewCancel = None
		self.wndItem = None
		self.chestDrop = { }
		self.chestDropReply = {}
		self.stoneGradeRanges = {}
		self.currentChest = 0
		self.requestedChestVnum = 0
		self.currentPage = 1
		self.openAmount = 1
		self.invItemPos = -1

	def __PrepareRequest(self, chestVnum, invItemPos):
		self.OverOutItem()
		self.currentChest = 0
		self.requestedChestVnum = chestVnum
		self.currentPage = 1
		self.openAmount = 1
		self.chestDrop = { }
		self.chestDropReply = {}
		self.stoneGradeRanges = {}
		self.SetInvItemSlot(invItemPos)
		self.openCountController.SetSliderPos(0.0)
		self.OnChangeOpenAmount()
		self.currentPageText.SetText(str(self.currentPage))
		self.Hide()

	def SetPreviewService(self, request, cancel):
		self.previewRequest = request
		self.previewCancel = cancel

	def __RequestContent(self, chestVnum):
		if self.previewRequest:
			if not self.previewRequest(chestVnum, "inventory", ui.__mem_func__(self.OnChestPreview)):
				self.OnChestPreview(chestVnum, {})
		else:
			net.SendChestDropInfoByVnum(chestVnum)

	def OnChestPreview(self, chestVnum, pages):
		if chestVnum != self.requestedChestVnum:
			return
		self.chestDropReply = {}
		for page, rows in pages.items():
			for slot, entry in rows.items():
				self.AddChestDropItem(chestVnum, page, slot, entry[0], entry[1])
		self.RefreshItems(chestVnum)

	def RequestPreview(self, invItemPos):
		chestVnum = player.GetItemIndex(invItemPos)
		if not chestpreview.CanPreview(chestVnum) or not IsPreviewChestType(
				player.GetItemTypeBySlot(invItemPos)):
			return False
		self.__PrepareRequest(chestVnum, invItemPos)
		self.__RequestContent(chestVnum)
		return True

	def RequestPreviewByVnum(self, chestVnum):
		if not chestpreview.CanPreview(chestVnum):
			return False
		item.SelectItem(chestVnum)
		if not IsPreviewChestType(item.GetItemType()):
			return False
		self.__PrepareRequest(chestVnum, -1)
		self.__RequestContent(chestVnum)
		return True

	def Open(self, invItemPos = -1):
		if invItemPos < 0:
			return False
		return self.RequestPreview(invItemPos)

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def OnChangeOpenAmount(self):
		self.openAmount = GetOpenAmountFromSlider(
			self.openCountController.GetSliderPos())

		self.openChestButtonSingle.SetText(localeInfo.CHEST_DROP_QUANTITY % self.openAmount)
		self.openChestButtonMultiple.SetText(localeInfo.CHEST_DROP_QUANTITY % self.openAmount)

	def AddChestDropItem(self, chestVnum, pageIndex, slotIndex, itemVnum, itemCount):
		if chestVnum != self.requestedChestVnum:
			return
		if chestVnum not in self.chestDropReply:
			self.chestDropReply[chestVnum] = {}

		if pageIndex not in self.chestDropReply[chestVnum]:
			self.chestDropReply[chestVnum][pageIndex] = {}

		if pageIndex in self.chestDropReply[chestVnum]:
			if slotIndex in self.chestDropReply[chestVnum][pageIndex]:
				if self.chestDropReply[chestVnum][pageIndex][slotIndex][0] == itemVnum and self.chestDropReply[chestVnum][pageIndex][slotIndex][1] == itemCount:
					return

		self.chestDropReply[chestVnum][pageIndex][slotIndex] = [itemVnum, itemCount]

	def __GetAvailableOpenCount(self):
		if player.GetItemTypeBySlot(self.invItemPos) == item.ITEM_TYPE_GACHA:
			remaining = player.GetItemMetinSocket(self.invItemPos, 0)
			item.SelectItem(self.requestedChestVnum)
			fullUses = max(1, item.GetLimit(1)[1])
			if fullUses == 1 and remaining <= 1:
				return player.GetItemCount(self.invItemPos)
			# The server retains the active multi-use piece in the clicked slot.
			# Zero is the historical unopened representation, not zero rewards.
			return remaining if remaining > 0 else fullUses
		return player.GetItemCount(self.invItemPos)

	def OnClickOpenChest(self):
		if self.invItemPos == -1:
			return
		if not IsRequestedChestStillPresent(
				self.invItemPos, self.requestedChestVnum):
			self.Close()
			return

		itemType = player.GetItemTypeBySlot(self.invItemPos)
		if itemType == item.ITEM_TYPE_TREASURE_BOX:
			keySlot = FindMatchingTreasureKey(self.requestedChestVnum)
			if keySlot < 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO,
					localeInfo.CHEST_DROP_KEY_MISSING)
				return
			net.SendItemUseToItemPacket(keySlot, self.invItemPos)
			self.Close()
			return

		availableCount = self.__GetAvailableOpenCount()
		openCount = GetBatchOpenCount(self.openAmount, availableCount)
		for i in range(openCount):
			net.SendItemUsePacket(self.invItemPos)

		if openCount > 0 and openCount == availableCount:
			self.OnPressEscapeKey()

	def OnClickPrevPage(self):
		if self.currentChest not in self.chestDrop:
			return

		if (self.currentPage - 1) in self.chestDrop[self.currentChest]:
			self.currentPage = self.currentPage - 1
			self.currentPageText.SetText(str(self.currentPage))
			self.RefreshItemSlot()

	def OnClickNextPage(self):
		if self.currentChest not in self.chestDrop:
			return

		if (self.currentPage + 1) in self.chestDrop[self.currentChest]:
			self.currentPage = self.currentPage + 1
			self.currentPageText.SetText(str(self.currentPage))
			self.RefreshItemSlot()

	def EnableMultiPage(self):
		self.openChestButtonSingle.Hide()
		self.openChestButtonMultiple.Show()

		self.prevButton.Show()
		self.nextButton.Show()
		self.currentPageBack.Show()

	def EnableSinglePage(self):
		self.openChestButtonSingle.Show()
		self.openChestButtonMultiple.Hide()

		self.prevButton.Hide()
		self.nextButton.Hide()
		self.currentPageBack.Hide()

	def SetInvItemSlot(self, invItemPos):
		self.invItemPos = invItemPos

		if invItemPos < 0:
			return

		player.GetItemIndex(invItemPos)

	def RefreshItems(self, chestVnum):
		if chestVnum != self.requestedChestVnum:
			return
		if chestVnum not in self.chestDropReply:
			chat.AppendChat(chat.CHAT_TYPE_INFO,
				localeInfo.CHEST_DROP_CONTENTS_UNAVAILABLE)
			self.Close()
			return

		self.chestDrop[chestVnum], self.stoneGradeRanges = stonecrafting.GroupChestPreview(
			chestVnum, self.chestDropReply[chestVnum])
		self.currentChest = chestVnum
		if self.invItemPos >= 0 and player.GetItemTypeBySlot(
				self.invItemPos) == item.ITEM_TYPE_TREASURE_BOX:
			self.openAmount = 1
			self.openCountController.Hide()
		else:
			self.openCountController.Show()

		if 2 in self.chestDrop[self.currentChest]:
			self.EnableMultiPage()
		else:
			self.EnableSinglePage()

		self.RefreshItemSlot()
		self.SetTop()
		self.SetCenterPosition()
		self.Show()

	def RefreshItemSlot(self):
		for i in range(5 * 8):
			self.wndItem.ClearSlot(i)

		if self.currentChest not in self.chestDrop:
			return

		if self.currentPage not in self.chestDrop[self.currentChest]:
			return

		for key, value in self.chestDrop[self.currentChest][self.currentPage].items():
			itemVnum = value[0]
			itemCount = value[1]

			if itemCount <= 1:
				itemCount = 0

			self.wndItem.SetItemSlot(key, itemVnum, itemCount)

		wndMgr.RefreshSlot(self.wndItem.GetWindowHandle())

	def OverInItem(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			return

		if self.currentChest not in self.chestDrop:
			return

		if self.currentPage not in self.chestDrop[self.currentChest]:
			return

		entry = self.chestDrop[self.currentChest][self.currentPage].get(slotIndex)
		if not self.tooltipItem or not entry:
			return
		gradeRange = self.stoneGradeRanges.get((self.currentPage, slotIndex))
		if gradeRange:
			item.SelectItem(entry[0])
			name = item.GetItemName().rsplit("+", 1)[0].rstrip()
			self.tooltipItem.itemVnum = entry[0]
			self.tooltipItem.ClearToolTip()
			self.tooltipItem.SetTitle(name)
			self.tooltipItem.AppendTextLine(getattr(localeInfo,
				"CHEST_DROP_GRADE_RANGE", "+%d - +%d") % gradeRange)
			self.tooltipItem.ShowToolTip()
		else:
			self.tooltipItem.SetItemToolTip(entry[0])

	def OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True
