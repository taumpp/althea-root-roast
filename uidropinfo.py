import app
import ui
import localeInfo
import uiScriptLocale
import wndMgr
import chat
import player
import item
import time
import uiToolTip
import osfInfo

class Window(ui.ThinBoard):

	NORMAL_COLOR = (0.7607, 0.7607, 0.7607, 1.0)
	YELLOW_COLOR = (1.0, 0.7843, 0.0, 1.0)
	OPEN_TIME = 15
	SLIDE_TIME = 4
	GAP = 12
	SLOT_PIXEL_HEIGHT = 32
	CONTENT_TOP_PADDING = 8

	BOARD_SIZE = [205, 326]
	RECT_SIZE = [205, 300]

	"""
	You can use the following values to sort the items
		"gold"
		"count"
		"none"
	"""
	SORT_MODE = "gold"

	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.SetSize(self.BOARD_SIZE[0], self.BOARD_SIZE[1])

		self.children = {}
		self.dropInformation = []
		self.scrollOffset = 0.0
		self.drop_slot_animating = False

		self.isActiveSlide = False
		self.isActiveSlideOut = False
		self.isActiveSlideOutEnded = True
		self.isVisible = False
		self.endTime = 0
		self.__quest_buttons_hidden_by_dropinfo = False

		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.Hide()

		self.CreateWindow()

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def CreateWindow(self):
		rectWindow = ui.Window()
		rectWindow.SetParent(self)
		rectWindow.SetSize(self.RECT_SIZE[0], self.RECT_SIZE[1])
		rectWindow.SetPosition(0, 15)
		rectWindow.Show()
		self.rectWindow = rectWindow

		scrollbarWindow = ui.Window()
		scrollbarWindow.SetParent(self)
		scrollbarWindow.SetPosition(190, 5)
		scrollbarWindow.SetSize(7, 360)
		scrollbarWindow.Show()
		self.scrollbarWindow = scrollbarWindow

		scrollBar = ui.ScrollbarDyn()
		scrollBar.SetParent(self.scrollbarWindow)
		scrollBar.SetPosition(0, 8)
		scrollBar.SetSize(5, self.GetHeight() - 25)
		scrollBar.SetScrollEvent(self.OnScrollBar)
		scrollBar.SetScrollSpeed(25)
		scrollBar.Hide()
		self.scrollBar = scrollBar

	def __GetCenteredY(self):
		screen_h = wndMgr.GetScreenHeight()
		wnd_h = self.GetHeight()
		center_y = (screen_h - wnd_h) // 2
		return max(10, min(center_y, screen_h - wnd_h - 10))

	def RecenterVertical(self):
		(x, y) = self.GetLocalPosition()
		self.SetPosition(x, self.__GetCenteredY())

	def SlideIn(self):
		if self.isActiveSlide or self.isActiveSlideOut:
			return

		self.SetTop()
		self.Show()

		self.wndWidth = self.GetWidth()
		self.wndHeight = self.GetHeight()

		screen_w = wndMgr.GetScreenWidth()
		screen_h = wndMgr.GetScreenHeight()

		start_x = -self.wndWidth

		target_y = self.__GetCenteredY()

		self.SetPosition(start_x, target_y)
		self.__HideQuestButtons()

		self.isActiveSlide = True
		self.isActiveSlideOut = False
		self.isActiveSlideOutEnded = False
		self.endTime = app.GetGlobalTimeStamp() + self.OPEN_TIME

	def Open(self):

		if not self.isVisible and not self.isActiveSlide and not self.isActiveSlideOut:
			self.SlideIn()

	def Close(self):
		if self.isActiveSlide or self.isActiveSlideOut or not self.isVisible:
			return

		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()

		self.children = {}
		self.dropInformation = []
		self.scrollOffset = 0.0
		self.isActiveSlideOut = True

	def Destroy(self):
		self.children = {}
		self.dropInformation = []
		self.scrollOffset = 0.0
		self.isActiveSlide = False
		self.isActiveSlideOut = False
		self.isActiveSlideOutEnded = True
		self.isVisible = False
		self.endTime = 0
		self.__RestoreQuestButtons()

	def __HideQuestButtons(self):
		if self.__quest_buttons_hidden_by_dropinfo:
			return
		try:
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				interface.HideAllQuestButton()
				self.__quest_buttons_hidden_by_dropinfo = True
		except:
			pass

	def __RestoreQuestButtons(self):
		if not self.__quest_buttons_hidden_by_dropinfo:
			return
		try:
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				interface.ShowAllQuestButton()
		except:
			pass
		self.__quest_buttons_hidden_by_dropinfo = False

	def AppendDropInfo(self, vnum, count):
		for entry in self.dropInformation:
			if entry["vnum"] == vnum:
				entry["count"] += count
				self.UpdateSlotText(vnum, entry["count"])
				break
		else:
			self.dropInformation.insert(0, {"vnum": vnum, "count": count})

			for widget in self.children.values():
				widget.Hide()
			for index, info in enumerate(self.GetSortedDropInformation()):
				self.CreateDropSlot(info, index)

			totalHeight = self.GetTotalHeight()
			maxHeight = self.BOARD_SIZE[1]
			baseHeight = 26

			if totalHeight + baseHeight <= maxHeight:
				self.SetSize(self.GetWidth(), totalHeight + baseHeight)
				self.rectWindow.SetSize(205, totalHeight)
				self.scrollbarWindow.SetSize(7, totalHeight + 5)
				self.scrollBar.SetSize(5, totalHeight - 25)
			else:
				self.SetSize(self.GetWidth(), maxHeight)
				self.rectWindow.SetSize(205, maxHeight - baseHeight)
				self.scrollbarWindow.SetSize(7, maxHeight)
				self.scrollBar.SetSize(5, maxHeight - 25)

			if self.isVisible or self.isActiveSlide:
				self.RecenterVertical()

			self.UpdateSlotPositions()
			self.ChangeScrollbar()

			self.drop_slot_anim_start_time = time.perf_counter()
			self.drop_slot_animating = True
			self.endTime = app.GetGlobalTimeStamp() + self.OPEN_TIME

		if not self.isVisible and not self.isActiveSlide and not self.isActiveSlideOut:
			self.SlideIn()

	def AppendChatInfo(self, vnum, count):
		item.SelectItem(vnum)
		name = item.GetItemName()

		if vnum == 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GAME_PICK_MONEY % localeInfo.MoneyFormat(count))
		elif count > 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DROP_INFO_TEXT_1 % (name, count))
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DROP_INFO_TEXT_2 % name)


	def CreateDropSlot(self, data, index):
		if data["vnum"] == 0:
			return

		vnum = data["vnum"]
		item.SelectItem(vnum)
		name = item.GetItemName()
		size = item.GetItemSize()[1]
		itemIcon = item.GetIconImageFileName()
		y = 0

		slotImage = ui.MakeImageBox(self.rectWindow, "d:/ymir work/ui/game/dropinfo/slot_{}.tga".format(size), 13, 0)

		iconImage = ui.MakeImageBox(slotImage, itemIcon, 0, 0)
		itemFlare = ui.MakeImageBox(slotImage, "d:/ymir work/ui/game/dropinfo/name.tga", 32, -13)
		itemName = ui.MakeText(itemFlare, name, 5, 9, self.NORMAL_COLOR)

		try:
			w = itemFlare.GetWidth()
			if w > 0:
				itemName.SetLimitWidth(max(0, w - 10))
		except:
			pass

		itemCountBG = ui.MakeImageBox(slotImage, "d:/ymir work/ui/game/dropinfo/line.tga", 32, 13)
		if vnum == 1:
			itemCountText = ui.MakeText(itemCountBG, localeInfo.GAME_PICK_MONEY % localeInfo.MoneyFormat(data["count"]), 5, 0, self.YELLOW_COLOR)
		else:
			itemCountText = ui.MakeText(itemCountBG, localeInfo.DROP_INFO_COUNT % data["count"], 5, 0, self.YELLOW_COLOR)
		try:
			w = itemCountBG.GetWidth()
			if w > 0:
				itemCountText.SetLimitWidth(max(0, w - 10))
		except:
			pass

		for widget in [slotImage, iconImage, itemFlare, itemName, itemCountBG, itemCountText]:
			widget.SetClippingMaskWindow(self.rectWindow)


		metinSlot = [0] * player.METIN_SOCKET_MAX_NUM
		attrSlot = [ (0, 0) ] * player.ATTRIBUTE_SLOT_MAX_NUM

		iconImage.OnMouseOverIn = lambda arg=self, vnum=vnum: arg.OverInItem(vnum, metinSlot, attrSlot)
		iconImage.OnMouseOverOut = ui.__mem_func__(self.OverOutItem)
		iconImage.OnMouseRightButtonUp = lambda : self.UseItemSlot(vnum)

		self.children["slotImage_%d" % index] = slotImage
		self.children["iconImage_%d" % index] = iconImage
		self.children["ItemFlare_%d" % index] = itemFlare
		self.children["ItemName_%d" % index] = itemName
		self.children["ItemCountBG_%d" % index] = itemCountBG
		self.children["ItemCountText_%d" % index] = itemCountText

	def GetSortedDropInformation(self):
		if self.SORT_MODE == "gold":
			gold = [info for info in self.dropInformation if info["vnum"] == 1]
			others = [info for info in self.dropInformation if info["vnum"] != 1]
			return gold + others
		elif self.SORT_MODE == "count":
			return sorted(self.dropInformation, key=lambda x: x["count"], reverse=True)
		return self.dropInformation

	def UpdateSlotText(self, vnum, new_count):
		for i, data in enumerate(self.GetSortedDropInformation()):
			if data["vnum"] == vnum:
				countText = self.children.get("ItemCountText_%d" % i)
				if countText:
					if vnum == 1:
						countText.SetText(localeInfo.GAME_PICK_MONEY % localeInfo.MoneyFormat(new_count))
					else:
						countText.SetText(localeInfo.DROP_INFO_COUNT % new_count)
				break

	def UpdateSlotPositions(self):
		current_y = self.CONTENT_TOP_PADDING + self.scrollOffset
		visible_h = self.rectWindow.GetHeight()
		text_clip_pad = 8
		for i, data in enumerate(self.GetSortedDropInformation()):
			item.SelectItem(data["vnum"])
			size = item.GetItemSize()[1]
			slot = self.children.get("slotImage_%d" % i)
			if slot:
				slot_height = size * self.SLOT_PIXEL_HEIGHT
				slot.SetPosition(13, current_y)
				in_view = not (current_y + slot_height < -text_clip_pad or current_y > visible_h - text_clip_pad)
				nameText = self.children.get("ItemName_%d" % i)
				countText = self.children.get("ItemCountText_%d" % i)
				try:
					flare = self.children.get("ItemFlare_%d" % i)
					if nameText and flare:
						w = flare.GetWidth()
						if w > 0:
							nameText.SetLimitWidth(max(0, w - 10))
					countBG = self.children.get("ItemCountBG_%d" % i)
					if countText and countBG:
						w = countBG.GetWidth()
						if w > 0:
							countText.SetLimitWidth(max(0, w - 10))
				except:
					pass
				if nameText:
					(nameText.Show if in_view else nameText.Hide)()
				if countText:
					(countText.Show if in_view else countText.Hide)()
				current_y += slot_height + self.GAP

	def UpdateDropSlotAnimation(self):
		if not self.drop_slot_animating:
			return

		elapsed = time.perf_counter() - self.drop_slot_anim_start_time
		duration = 0.3
		t = min(1.0, elapsed / duration)
		eased_t = 1 - (1 - t) ** 2

		start_y_offset = -50
		current_y = self.CONTENT_TOP_PADDING + self.scrollOffset
		visible_h = self.rectWindow.GetHeight()
		text_clip_pad = 8

		for i, data in enumerate(self.GetSortedDropInformation()):
			item.SelectItem(data["vnum"])
			size = item.GetItemSize()[1]
			slot_height = size * self.SLOT_PIXEL_HEIGHT

			target_y = current_y
			animated_y = target_y + start_y_offset * (1 - eased_t)

			slot = self.children.get("slotImage_%d" % i)
			if slot:
				slot.SetPosition(13, animated_y)
				in_view = not (animated_y + slot_height < -text_clip_pad or animated_y > visible_h - text_clip_pad)
				nameText = self.children.get("ItemName_%d" % i)
				countText = self.children.get("ItemCountText_%d" % i)
				if nameText:
					(nameText.Show if in_view else nameText.Hide)()
				if countText:
					(countText.Show if in_view else countText.Hide)()
			current_y += slot_height + self.GAP

		if t >= 1.0:
			self.drop_slot_animating = False

	def OnUpdate(self):
		self.UpdateDropSlotAnimation()

		current_time = app.GetGlobalTimeStamp()

		if self.isActiveSlide:
			x, y = self.GetLocalPosition()
			target_x = 10

			delta_x = min(self.SLIDE_TIME, target_x - x)
			self.SetPosition(x + delta_x, y)

			if x >= target_x:
				self.isActiveSlide = False
				self.isVisible = True
				self.endTime = current_time + self.OPEN_TIME

		elif self.isActiveSlideOut:
			x, y = self.GetLocalPosition()
			target_x = -self.wndWidth - 10
			delta_x = max(-self.SLIDE_TIME, target_x - x)
			self.SetPosition(x + delta_x, y)

			if x <= target_x:
				self.Hide()
				self.isActiveSlideOut = False
				self.isActiveSlideOutEnded = True
				self.isVisible = False
				self.__RestoreQuestButtons()

		if not self.isActiveSlide and not self.isActiveSlideOut and current_time >= self.endTime:
			self.Close()

	def UseItemSlot(self, itemVnum):
		if app.IsPressed(app.DIK_LSHIFT) and itemVnum > 1:
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				wndWiki = getattr(interface, "wndWiki", None)
				if not wndWiki or not wndWiki.IsShow():
					interface.OpenWikiWindow()

				wndWiki = getattr(interface, "wndWiki", None)
				if wndWiki and wndWiki.IsShow():
					wndWiki.ShowItemInfo(itemVnum, 0, isHistory=False)
					if hasattr(wndWiki, "FocusSearchItem"):
						wndWiki.FocusSearchItem()
			return

	def OverInItem(self, itemVnum, metinSlot, attrSlot):
		if not self.tooltipItem:
			return
		self.tooltipItem.ClearToolTip()
		self.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot)
		self.tooltipItem.ShowToolTip()

	def OverOutItem(self):
		if None != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	# --- Scrollbar ---
	def GetTotalHeight(self):
		total = 0
		for data in self.dropInformation:
			item.SelectItem(data["vnum"])
			size = item.GetItemSize()[1]
			total += size * self.SLOT_PIXEL_HEIGHT + self.GAP
		return total + self.CONTENT_TOP_PADDING

	def ScrollContent(self, offset):
		self.scrollOffset = offset
		self.UpdateSlotPositions()

	def OnMouseWheel(self, length):
		if self.IsInPosition():
			self.UpdateScrollbar(length * 0.28)
			return True
		return False

	def OnScrollBar(self, scale):
		totalHeight = self.GetTotalHeight()
		visibleHeight = self.rectWindow.GetHeight()

		if totalHeight <= visibleHeight:
			return

		offset = min(0, max(int((totalHeight - visibleHeight) * scale * -1.0), visibleHeight - totalHeight))
		self.ScrollContent(offset)

	def UpdateScrollbar(self, val=0):
		totalHeight = self.GetTotalHeight()
		visibleHeight = self.rectWindow.GetHeight()
		newOffset = min(0, max(self.scrollOffset + val, visibleHeight - totalHeight))
		self.ScrollContent(newOffset)
		self.ChangeScrollbar()

	def ChangeScrollbar(self):
		if not self.scrollBar:
			return

		totalHeight = self.GetTotalHeight()
		visibleHeight = self.rectWindow.GetHeight()

		if totalHeight <= visibleHeight:
			self.scrollBar.Hide()
		else:
			self.scrollBar.SetScale(visibleHeight, totalHeight)
			progress = abs(self.scrollOffset) / float(totalHeight - visibleHeight)
			self.scrollBar.SetPosScale(progress)
			self.scrollBar.Show()
