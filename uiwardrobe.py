import app
import item
import localeInfo
import osfInfo
import player
import renderTarget
import ui

import iscostumevoucher
import wardrobedata


RENDER_TARGET_INDEX = 4
CATALOG_COLUMNS = 7
CATALOG_ROWS = 5
CATALOG_PAGE_SIZE = CATALOG_COLUMNS * CATALOG_ROWS

SOURCE_ALL = 0
SOURCE_ITEMSHOP = 1
SOURCE_GAME = 2

ITEMSHOP_ITEM_ID = 0
ITEMSHOP_ITEM_VNUM = 1
ITEMSHOP_ITEM_PRICE = 2
ITEMSHOP_ITEM_DISCOUNT = 3
ITEMSHOP_ITEM_TIME = 4
FALLBACK_ITEM_ICON = "icon/item/27995.tga"
WARDROBE_IMG_DIR = "d:/ymir work/ui/game/crimson_ember/wardrobe/"
CRIMSON_SHARED_IMG_DIR = "d:/ymir work/ui/game/crimson_ember/shared/"
PAGE_WINDOW_SIZE = 5
PREVIEW_ROTATION_STEP = 15.0


def _Text(key, fallback):
	return getattr(localeInfo, key, fallback)


WARDROBE_SOURCE_ICON_POSITIONS = {
	"all": (3, 3),
	"item_shop": (3, 2),
	"in_game": (3, 3),
}
WARDROBE_TYPE_ICON_POSITIONS = {
	"all": (3, 3),
	"body": (3, 4),
	"hair": (4, 3),
	"weapon": (3, 3),
	"acce": (3, 4),
	"effect": (4, 3),
}
WARDROBE_SOURCE_TEXT_CENTER = 55
WARDROBE_TYPE_TEXT_CENTER = 47
WARDROBE_FILTER_TEXT_Y = 9
WARDROBE_FILTER_TEXT_NORMAL = 0xffc8bba6
WARDROBE_FILTER_TEXT_SELECTED = 0xffffe9bd
CATALOG_ICON_WELL = (8, 8, 44, 45)
CATALOG_ICON_MAX = (42, 43)


def _SetWardrobeButtonVisuals(button, prefix, selected=False):
	button.SetUpVisual(WARDROBE_IMG_DIR + prefix + "normal.png")
	button.SetOverVisual(WARDROBE_IMG_DIR + prefix + "hover.png")
	button.SetDownVisual(WARDROBE_IMG_DIR + prefix + ("selected.png" if selected else "pressed.png"))
	button.SetDisableVisual(WARDROBE_IMG_DIR + prefix + "disabled.png")


def _CreateWardrobeButton(parent, x, y, text, event, prefix, selected=False):
	button = ui.RadioButton() if selected else ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	_SetWardrobeButtonVisuals(button, prefix, selected)
	if text:
		button.SetText(text)
		button.SetTextColor(0xffeadfc8)
	button.SetEvent(event)
	button.Show()
	return button


def _CreateImage(parent, x, y, filename):
	image = ui.ImageBox()
	image.SetParent(parent)
	image.SetPosition(x, y)
	image.AddFlag("not_pick")
	image.LoadImage(filename)
	image.Show()
	return image


def _SetFilterButtonText(button, text, centerX):
	button.SetListText(text, centerX)
	button.ButtonText.SetHorizontalAlignCenter()
	button.ButtonText.SetPosition(centerX, WARDROBE_FILTER_TEXT_Y)
	button.SetTextColor(WARDROBE_FILTER_TEXT_NORMAL)


def _SetFilterButtonState(button, selected):
	if selected:
		button.Down()
		button.SetTextColor(0xffffe9bd)
	else:
		button.SetUp()
		button.SetTextColor(0xffc8bba6)


def _CreateSourceButton(parent, x, text, event, role):
	button = _CreateWardrobeButton(
		parent, x, 10, "", event, "tab/source_", True)
	_SetFilterButtonText(button, text, WARDROBE_SOURCE_TEXT_CENTER)
	iconPosition = WARDROBE_SOURCE_ICON_POSITIONS[role]
	icon = _CreateImage(
		button, iconPosition[0], iconPosition[1],
		WARDROBE_IMG_DIR + "icon/source_%s.png" % role)
	button.roleIcon = icon
	return button


def _CreateTypeButton(parent, x, text, event, role):
	button = _CreateWardrobeButton(
		parent, x, 43, "", event, "tab/type_", True)
	_SetFilterButtonText(button, text, WARDROBE_TYPE_TEXT_CENTER)
	iconPosition = WARDROBE_TYPE_ICON_POSITIONS[role]
	icon = _CreateImage(
		button, iconPosition[0], iconPosition[1],
		WARDROBE_IMG_DIR + "icon/type_%s.png" % role)
	button.roleIcon = icon
	return button


class WardrobeItemCard(ui.RadioButton):
	def __init__(self, parent, x, y, data, selectEvent, overInEvent, overOutEvent):
		ui.RadioButton.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		_SetWardrobeButtonVisuals(self, "card/catalogue_", True)
		self.vnum = data["vnum"]
		self.SetEvent(selectEvent, self.vnum)
		self.SAFE_SetOverInEvent(overInEvent, self.vnum)
		self.SAFE_SetOverOutEvent(overOutEvent)

		icon = ui.ExpandedImageBox()
		icon.SetParent(self)
		icon.AddFlag("not_pick")
		try:
			icon.LoadImage(data["icon"])
		except RuntimeError:
			icon.LoadImage(FALLBACK_ITEM_ICON)
		width = max(1, icon.GetWidth())
		height = max(1, icon.GetHeight())
		wellX, wellY, wellWidth, wellHeight = CATALOG_ICON_WELL
		maxWidth, maxHeight = CATALOG_ICON_MAX
		scale = min(1.0, maxWidth / float(width), maxHeight / float(height))
		icon.SetScale(scale, scale)
		icon.SetPosition(
			int(wellX + (wellWidth - width * scale) / 2),
			int(wellY + (wellHeight - height * scale) / 2))
		icon.Show()
		self.icon = icon

		if data["is_shop"]:
			badge = _CreateImage(
				self, 34, 2, CRIMSON_SHARED_IMG_DIR + "badge/item_shop.png")
			badgeText = ui.TextLine()
			badgeText.SetParent(badge)
			badgeText.SetPosition(12, 8)
			badgeText.SetHorizontalAlignCenter()
			badgeText.SetVerticalAlignCenter()
			badgeText.SetPackedFontColor(0xffffe9bd)
			badgeText.SetText("IS")
			badgeText.Show()
			self.badge = badge
			self.badgeText = badgeText
		else:
			self.badge = None
			self.badgeText = None

		self.Show()

	def SetSelected(self, selected):
		self.Down() if selected else self.SetUp()

	def Destroy(self):
		self.icon = None
		self.badge = None
		self.badgeText = None
		self.vnum = 0


class WardrobeLoadoutCard(ui.Button):
	WIDTH = 38
	HEIGHT = 38
	ICON_WIDTH = 30
	ICON_HEIGHT = 30

	def __init__(self, parent, x, y, slotIndex, removeEvent, overInEvent, overOutEvent):
		ui.Button.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		_SetWardrobeButtonVisuals(self, "card/loadout_")
		self.slotIndex = slotIndex
		self.vnum = 0
		self.removeEvent = removeEvent
		self.SAFE_SetOverInEvent(overInEvent, slotIndex)
		self.SAFE_SetOverOutEvent(overOutEvent)

		icon = ui.ExpandedImageBox()
		icon.SetParent(self)
		icon.AddFlag("not_pick")
		icon.Hide()
		self.icon = icon
		self.Show()

	def SetItem(self, vnum):
		self.vnum = int(vnum or 0)
		if not self.vnum:
			self.icon.Hide()
			return

		item.SelectItem(self.vnum)
		try:
			self.icon.LoadImage(item.GetIconImageFileName())
		except RuntimeError:
			self.icon.LoadImage(FALLBACK_ITEM_ICON)
		width = max(1, self.icon.GetWidth())
		height = max(1, self.icon.GetHeight())
		scale = min(1.0, self.ICON_WIDTH / float(width), self.ICON_HEIGHT / float(height))
		self.icon.SetScale(scale, scale)
		self.icon.SetPosition(
			int((self.WIDTH - width * scale) / 2),
			int((self.HEIGHT - height * scale) / 2))
		self.icon.Show()

	def OnMouseRightButtonDown(self):
		if not self.vnum:
			return
		removeEvent = self.removeEvent
		if removeEvent:
			removeEvent(self.slotIndex)

	def Destroy(self):
		self.icon = None
		self.removeEvent = None
		self.vnum = 0


class WardrobeWindow(ui.BoardWithTitleBar):
	SELECTED_SLOT_TYPES = (
		item.COSTUME_TYPE_BODY,
		item.COSTUME_TYPE_HAIR,
		item.COSTUME_TYPE_WEAPON,
		item.COSTUME_TYPE_ACCE,
		item.COSTUME_TYPE_EFFECT_WEAPON,
		item.COSTUME_TYPE_EFFECT_ARMOR,
	)

	TYPE_FILTERS = (
		("all", None, "WARDROBE_TAB_ALL", "V\u0161e"),
		("body", (item.COSTUME_TYPE_BODY,), "WARDROBE_TAB_BODY", "T\u011blo"),
		("hair", (item.COSTUME_TYPE_HAIR,), "WARDROBE_TAB_HAIR", "\u00da\u010des"),
		("weapon", (item.COSTUME_TYPE_WEAPON,), "WARDROBE_TAB_WEAPON", "Zbra\u0148"),
		("acce", (item.COSTUME_TYPE_ACCE,), "WARDROBE_TAB_ACCE", "\u0160erpa"),
		("effect", (item.COSTUME_TYPE_EFFECT_WEAPON, item.COSTUME_TYPE_EFFECT_ARMOR), "WARDROBE_TAB_EFFECT", "Efekty"),
	)

	SUPPORTED_SUBTYPES = frozenset(
		(item.COSTUME_TYPE_BODY, item.COSTUME_TYPE_HAIR, item.COSTUME_TYPE_WEAPON,
		 item.COSTUME_TYPE_ACCE, item.COSTUME_TYPE_EFFECT_WEAPON,
		 item.COSTUME_TYPE_EFFECT_ARMOR)
	)

	MALE_RACES = frozenset((0, 2, 5, 7, 8))
	FEMALE_RACES = frozenset((1, 3, 4, 6))
	RACE_JOBS = {0: 0, 4: 0, 1: 1, 5: 1, 2: 2, 6: 2, 3: 3, 7: 3, 8: 4}
	JOB_ANTI_FLAGS = {
		0: item.ITEM_ANTIFLAG_WARRIOR,
		1: item.ITEM_ANTIFLAG_ASSASSIN,
		2: item.ITEM_ANTIFLAG_SURA,
		3: item.ITEM_ANTIFLAG_SHAMAN,
		4: item.ITEM_ANTIFLAG_WOLFMAN,
	}
	WEAPON_JOBS = {
		0: frozenset((0, 2)),
		1: frozenset((1,)),
		2: frozenset((1,)),
		3: frozenset((0,)),
		4: frozenset((3,)),
		5: frozenset((3,)),
		8: frozenset((4,)),
	}

	def __init__(self, owner):
		ui.BoardWithTitleBar.__init__(self)
		self.owner = owner
		self.itemshopOffers = {}
		self.catalogue = []
		self.filteredCatalogue = []
		self.cards = []
		self.loadoutCards = []
		self.selectedItems = {}
		self.baseItems = {}
		self.currentRace = 0
		self.currentPage = 0
		self.currentSource = SOURCE_ALL
		self.currentType = "all"
		self.currentVnum = 0
		self.isDragging = False
		self.lastMouseX = 0
		self._BuildWindow()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def _BuildWindow(self):
		self.SetSize(920, 600)
		self.SetTitleName(_Text("WARDROBE_TITLE", "\u0160atn\u00edk"))
		self.SetCloseEvent(self.Close)
		self.AddFlag("movable")
		self.AddFlag("float")

		previewBoard = _CreateImage(
			self, 15, 38, WARDROBE_IMG_DIR + "panel/preview.png")
		self.previewBoard = previewBoard

		renderWindow = ui.RenderTarget()
		renderWindow.SetParent(previewBoard)
		renderWindow.SetPosition(8, 8)
		renderWindow.SetSize(344, 414)
		renderWindow.SetRenderTarget(RENDER_TARGET_INDEX)
		renderWindow.SetMouseLeftButtonDownEvent(self._StartDrag)
		renderWindow.SetMouseLeftButtonUpEvent(self._StopDrag)
		renderWindow.SetOnRunMouseWheelEvent(self._OnMouseWheel)
		renderWindow.Show()
		self.renderWindow = renderWindow

		self.rotateLeftButton = _CreateWardrobeButton(
			previewBoard, 12, 396, "", self._RotateLeft, "button/pager_")
		self.rotateLeftButton.SetOnRunMouseWheelEvent(self._OnMouseWheel)
		self.rotateLeftIcon = _CreateImage(
			self.rotateLeftButton, 5, 5,
			WARDROBE_IMG_DIR + "icon/arrow_left.png")

		self.rotateRightButton = _CreateWardrobeButton(
			previewBoard, 324, 396, "", self._RotateRight, "button/pager_")
		self.rotateRightButton.SetOnRunMouseWheelEvent(self._OnMouseWheel)
		self.rotateRightIcon = _CreateImage(
			self.rotateRightButton, 5, 5,
			WARDROBE_IMG_DIR + "icon/arrow_right.png")

		loadoutBoard = _CreateImage(
			self, 15, 493, WARDROBE_IMG_DIR + "panel/loadout.png")
		self.loadoutBoard = loadoutBoard

		setLabel = ui.TextLine()
		setLabel.SetParent(loadoutBoard)
		setLabel.SetPosition(10, 7)
		setLabel.SetPackedFontColor(0xffeadfc8)
		setLabel.SetText(_Text("WARDROBE_SET", "Sestava (prav\u00fdm klikem sund\u00e1te)"))
		setLabel.Show()
		self.setLabel = setLabel

		for index in range(len(self.SELECTED_SLOT_TYPES)):
			loadoutCard = WardrobeLoadoutCard(
				loadoutBoard, 10 + index * 41, 27, index,
				self._RemoveSelectedSlot, self._OverInSelectedSlot, self._OverOutItem)
			self.loadoutCards.append(loadoutCard)

		self.resetButton = _CreateWardrobeButton(
			loadoutBoard, 263, 27, _Text("WARDROBE_RESET", "Reset"),
			self._ResetSelection, "button/reset_")
		self.buyButton = _CreateWardrobeButton(
			loadoutBoard, 263, 56, _Text("WARDROBE_BUY", "Koupit"),
			self._BuySelected, "button/buy_")
		self.buyButton.Hide()

		totalPriceText = ui.TextLine()
		totalPriceText.SetParent(loadoutBoard)
		totalPriceText.SetPosition(10, 68)
		totalPriceText.SetPackedFontColor(0xffd6b36a)
		totalPriceText.Show()
		self.totalPriceText = totalPriceText

		catalogBoard = _CreateImage(
			self, 390, 38, WARDROBE_IMG_DIR + "panel/catalogue.png")
		self.catalogBoard = catalogBoard

		self.sourceButtons = (
			_CreateSourceButton(
				catalogBoard, 12, _Text("WARDROBE_SOURCE_ALL", "V\u0161e"),
				lambda: self._SelectSource(SOURCE_ALL), "all"),
			_CreateSourceButton(
				catalogBoard, 106, _Text("WARDROBE_SOURCE_ITEMSHOP", "IS obchod"),
				lambda: self._SelectSource(SOURCE_ITEMSHOP), "item_shop"),
			_CreateSourceButton(
				catalogBoard, 200, _Text("WARDROBE_SOURCE_GAME", "Ve h\u0159e"),
				lambda: self._SelectSource(SOURCE_GAME), "in_game"),
		)

		searchBar = _CreateImage(
			catalogBoard, 354, 9, WARDROBE_IMG_DIR + "field/search_normal.png")
		self.searchBar = searchBar

		searchEdit = ui.EditLine()
		searchEdit.SetParent(searchBar)
		searchEdit.SetPosition(8, 4)
		searchEdit.SetSize(132, 18)
		searchEdit.SetMax(40)
		searchEdit.SetInfoMessage(_Text(
			"WARDROBE_SEARCH_HINT", "Hledat n\u00e1zev nebo VNUM"))
		searchEdit.OnIMEUpdate = self._OnSearchUpdate
		searchEdit.SetEscapeEvent(self.Close)
		searchEdit.Show()
		self.searchEdit = searchEdit

		self.typeButtons = []
		for index, typeData in enumerate(self.TYPE_FILTERS):
			button = _CreateTypeButton(
				catalogBoard, 12 + index * 82,
				_Text(typeData[2], typeData[3]),
				lambda selected=typeData[0]: self._SelectType(selected),
				typeData[0])
			self.typeButtons.append(button)

		self.cardsBoard = ui.Window()
		self.cardsBoard.SetParent(catalogBoard)
		self.cardsBoard.SetPosition(12, 76)
		self.cardsBoard.SetSize(468, 364)
		self.cardsBoard.Show()

		self.selectedName = ui.TextLine()
		self.selectedName.SetParent(catalogBoard)
		self.selectedName.SetPosition(12, 448)
		self.selectedName.SetPackedFontColor(0xffeadfc8)
		self.selectedName.SetText("")
		self.selectedName.Show()

		self.selectedSource = ui.TextLine()
		self.selectedSource.SetParent(catalogBoard)
		self.selectedSource.SetPosition(12, 468)
		self.selectedSource.SetPackedFontColor(0xffb9a78e)
		self.selectedSource.Show()

		self.previousButton = _CreateWardrobeButton(
			catalogBoard, 164, 493, "", self._PreviousPage, "button/pager_")
		self.previousIcon = _CreateImage(
			self.previousButton, 5, 5,
			WARDROBE_IMG_DIR + "icon/arrow_left.png")

		self.pageButtons = []
		for slotIndex in range(PAGE_WINDOW_SIZE):
			button = _CreateWardrobeButton(
				catalogBoard, 191 + slotIndex * 27, 493, "",
				lambda index=slotIndex: self._GoToPage(index),
				"button/page_", True)
			self.pageButtons.append(button)

		self.nextButton = _CreateWardrobeButton(
			catalogBoard, 322, 493, "", self._NextPage, "button/pager_")
		self.nextIcon = _CreateImage(
			self.nextButton, 5, 5,
			WARDROBE_IMG_DIR + "icon/arrow_right.png")

		self.pageText = ui.TextLine()
		self.pageText.SetParent(catalogBoard)
		self.pageText.SetPosition(257, 498)
		self.pageText.SetHorizontalAlignCenter()
		self.pageText.SetPackedFontColor(0xffb9a78e)
		self.pageText.Hide()

		self.SetCenterPosition()

	def Destroy(self):
		self.Close()
		self._ClearCards()
		for loadoutCard in self.loadoutCards:
			loadoutCard.Hide()
			loadoutCard.Destroy()
		self.loadoutCards = []
		self.owner = None
		self.itemshopOffers = {}
		self.catalogue = []
		self.filteredCatalogue = []
		self.selectedItems = {}
		self.baseItems = {}

	def Open(self, itemshopData):
		self.currentRace = int(player.GetRace())
		if self.currentRace not in self.RACE_JOBS:
			self.currentRace = 0
		self._IndexItemshopOffers(itemshopData)
		self._LoadCurrentEquipment()
		self.selectedItems = {}
		self.currentVnum = 0
		self.currentPage = 0
		self.selectedName.SetText("")
		self.selectedSource.SetText("")
		self.buyButton.Hide()
		self._BuildCatalogue()
		self._ApplyFilters()
		self._RefreshLoadoutCards()
		renderTarget.SetBackground(RENDER_TARGET_INDEX, "d:/ymir work/ui/render_target/render_target_bg.dds")
		self._RefreshModel()
		renderTarget.ResetCamera(RENDER_TARGET_INDEX)
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.isDragging = False
		renderTarget.SetVisibility(RENDER_TARGET_INDEX, False)
		self._OverOutItem()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def _IndexItemshopOffers(self, itemshopData):
		self.itemshopOffers = {}
		currentTime = app.GetGlobalTimeStamp()
		for subcategories in itemshopData.values():
			for offerList in subcategories:
				for offer in offerList:
					if offer[ITEMSHOP_ITEM_TIME] and currentTime > offer[ITEMSHOP_ITEM_TIME]:
						continue
					# A costume voucher offer is listed under the costume it
					# redeems to; the purchase still buys the voucher row.
					vnum = int(iscostumevoucher.DisplayVnum(int(offer[ITEMSHOP_ITEM_VNUM])))
					oldOffer = self.itemshopOffers.get(vnum)
					if oldOffer is None or self._OfferPrice(offer) < self._OfferPrice(oldOffer):
						self.itemshopOffers[vnum] = offer

	def _OfferPrice(self, offer):
		price = int(offer[ITEMSHOP_ITEM_PRICE])
		discount = int(offer[ITEMSHOP_ITEM_DISCOUNT])
		if discount > 0:
			price = (price * (100 - discount)) // 100
		return price

	def _LoadCurrentEquipment(self):
		self.baseItems = {}
		body = player.GetItemIndex(item.COSTUME_SLOT_BODY) or player.GetItemIndex(player.EQUIPMENT, item.EQUIPMENT_BODY)
		weapon = player.GetItemIndex(item.COSTUME_SLOT_WEAPON) or player.GetItemIndex(player.EQUIPMENT, item.EQUIPMENT_WEAPON)
		slots = (
			(item.COSTUME_TYPE_BODY, body),
			(item.COSTUME_TYPE_HAIR, player.GetItemIndex(item.COSTUME_SLOT_HAIR)),
			(item.COSTUME_TYPE_WEAPON, weapon),
			(item.COSTUME_TYPE_ACCE, player.GetItemIndex(item.COSTUME_SLOT_START + 3)),
			(item.COSTUME_TYPE_EFFECT_WEAPON, player.GetItemIndex(item.COSTUME_TYPE_SLOT_EFFECT_WEAPON)),
			(item.COSTUME_TYPE_EFFECT_ARMOR, player.GetItemIndex(item.COSTUME_TYPE_SLOT_EFFECT_ARMOR)),
		)
		for subType, vnum in slots:
			if vnum:
				self.baseItems[subType] = int(vnum)

	def _BuildCatalogue(self):
		self.catalogue = []
		seenVisuals = set()
		vnums = sorted(set(int(value) for value in item.GetCostumeVnumList()), key=lambda value: (value not in self.itemshopOffers, value))
		for vnum in vnums:
			if vnum not in self.itemshopOffers and not wardrobedata.IsPublicVnum(vnum):
				continue
			try:
				item.SelectItem(vnum)
				if item.GetItemType() != item.ITEM_TYPE_COSTUME:
					continue
				subType = item.GetItemSubType()
				if subType not in self.SUPPORTED_SUBTYPES or not self._CanUseSelectedItem(subType):
					continue
				name = item.GetItemName().strip()
				icon = item.GetIconImageFileName()
			except Exception:
				continue
			if not name or name.lower() == "noname" or name.startswith("<MISSING") or not icon or icon.lower() == "noname":
				continue
			if subType in (item.COSTUME_TYPE_BODY, item.COSTUME_TYPE_HAIR) and item.GetValue(3) <= 0:
				continue
			if subType == item.COSTUME_TYPE_ACCE and vnum < 85000:
				continue

			visualKey = self._GetVisualKey(vnum, subType, name)
			if visualKey in seenVisuals:
				continue
			seenVisuals.add(visualKey)
			self.catalogue.append({
				"vnum": vnum,
				"subtype": subType,
				"name": name,
				"search": name.lower(),
				"icon": icon,
				"is_shop": vnum in self.itemshopOffers,
			})

		self.catalogue.sort(key=lambda data: (not data["is_shop"], data["name"].lower(), data["vnum"]))

	def _CanUseSelectedItem(self, subType):
		job = self.RACE_JOBS[self.currentRace]
		if item.IsAntiFlag(self.JOB_ANTI_FLAGS[job]):
			return False
		if self.currentRace in self.MALE_RACES and item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
			return False
		if self.currentRace in self.FEMALE_RACES and item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
			return False
		if subType == item.COSTUME_TYPE_WEAPON:
			allowedJobs = self.WEAPON_JOBS.get(item.GetValue(3))
			if allowedJobs is not None and job not in allowedJobs:
				return False
		return True

	def _GetVisualKey(self, vnum, subType, name):
		antiFlags = tuple(item.IsAntiFlag(flag) for flag in self.JOB_ANTI_FLAGS.values()) + (
			item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE),
			item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE),
		)
		if subType in (item.COSTUME_TYPE_BODY, item.COSTUME_TYPE_HAIR):
			return subType, item.GetValue(3), antiFlags
		if subType == item.COSTUME_TYPE_WEAPON:
			return subType, name.lower(), item.GetValue(3), antiFlags
		return subType, vnum

	def _ApplyFilters(self):
		search = self.searchEdit.GetText().strip().lower()
		typeFilter = None
		for name, subtypes, localeKey, fallback in self.TYPE_FILTERS:
			if name == self.currentType:
				typeFilter = subtypes
				break

		self.filteredCatalogue = []
		for data in self.catalogue:
			if self.currentSource == SOURCE_ITEMSHOP and not data["is_shop"]:
				continue
			if self.currentSource == SOURCE_GAME and data["is_shop"]:
				continue
			if typeFilter is not None and data["subtype"] not in typeFilter:
				continue
			if search and search not in data["search"] and search not in str(data["vnum"]):
				continue
			self.filteredCatalogue.append(data)

		pageCount = self._GetPageCount()
		self.currentPage = min(self.currentPage, max(0, pageCount - 1))
		self._RefreshButtons()
		self._RefreshPage()

	def _RefreshButtons(self):
		for index, button in enumerate(self.sourceButtons):
			_SetFilterButtonState(button, index == self.currentSource)
		for index, typeData in enumerate(self.TYPE_FILTERS):
			_SetFilterButtonState(
				self.typeButtons[index], typeData[0] == self.currentType)

	def _ClearCards(self):
		for card in self.cards:
			card.Hide()
			card.Destroy()
		self.cards = []

	def _RefreshPage(self):
		self._ClearCards()
		start = self.currentPage * CATALOG_PAGE_SIZE
		for index, data in enumerate(self.filteredCatalogue[start:start + CATALOG_PAGE_SIZE]):
			column = index % CATALOG_COLUMNS
			row = index // CATALOG_COLUMNS
			card = WardrobeItemCard(
				self.cardsBoard, column * 66, row * 72, data,
				self._SelectItem, self._OverInItem, self._OverOutItem)
			card.SetSelected(data["vnum"] in self.selectedItems.values())
			self.cards.append(card)
		self._RefreshPagination()

	def _RefreshPagination(self):
		pageCount = self._GetPageCount()
		if not pageCount:
			self.previousButton.Hide()
			self.nextButton.Hide()
			for button in self.pageButtons:
				button.Hide()
			self.pageText.SetText(_Text("WARDROBE_EMPTY", "\u017d\u00e1dn\u00e9 odpov\u00eddaj\u00edc\u00ed p\u0159edm\u011bty"))
			self.pageText.Show()
			return

		self.pageText.Hide()
		visibleCount = min(PAGE_WINDOW_SIZE, pageCount)
		maxStart = max(0, pageCount - visibleCount)
		firstPage = max(0, min(self.currentPage - visibleCount // 2, maxStart))
		pageWidth = visibleCount * 24 + max(0, visibleCount - 1) * 3
		totalWidth = 24 + 3 + pageWidth + 3 + 24
		startX = (515 - totalWidth) // 2
		pageX = startX + 27

		self.previousButton.SetPosition(startX, 493)
		self.previousButton.Show()
		if self.currentPage > 0:
			self.previousButton.Enable()
		else:
			self.previousButton.Disable()

		for slotIndex, button in enumerate(self.pageButtons):
			pageIndex = firstPage + slotIndex
			if slotIndex >= visibleCount or pageIndex >= pageCount:
				button.Hide()
				continue
			button.SetPosition(pageX + slotIndex * 27, 493)
			button.SetText(str(pageIndex + 1))
			button.SetEvent(self._GoToPage, pageIndex)
			button.Show()
			button.Down() if pageIndex == self.currentPage else button.SetUp()

		self.nextButton.SetPosition(pageX + pageWidth + 3, 493)
		self.nextButton.Show()
		if self.currentPage + 1 < pageCount:
			self.nextButton.Enable()
		else:
			self.nextButton.Disable()

	def _GetPageCount(self):
		return (len(self.filteredCatalogue) + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE

	def _GoToPage(self, pageIndex):
		if pageIndex < 0 or pageIndex >= self._GetPageCount():
			return
		self.currentPage = pageIndex
		self._RefreshPage()

	def _SelectSource(self, source):
		self.currentSource = source
		self.currentPage = 0
		self._ApplyFilters()

	def _SelectType(self, typeName):
		self.currentType = typeName
		self.currentPage = 0
		self._ApplyFilters()

	def _OnSearchUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchEdit)
		self.currentPage = 0
		self._ApplyFilters()

	def _PreviousPage(self):
		if self.currentPage > 0:
			self.currentPage -= 1
			self._RefreshPage()

	def _NextPage(self):
		if self.currentPage + 1 < self._GetPageCount():
			self.currentPage += 1
			self._RefreshPage()

	def _SelectItem(self, vnum):
		data = next((entry for entry in self.catalogue if entry["vnum"] == vnum), None)
		if data is None:
			return
		self.selectedItems[data["subtype"]] = vnum
		self.currentVnum = vnum
		self.selectedName.SetText("%s (VNUM %d)" % (data["name"], vnum))
		if data["is_shop"]:
			price = self._OfferPrice(self.itemshopOffers[vnum])
			self.selectedSource.SetText(_Text("WARDROBE_ITEMSHOP_PRICE", "V IS obchodu: %d DC") % price)
			self.buyButton.Show()
		else:
			self.selectedSource.SetText(_Text("WARDROBE_GAME_ITEM", "Hern\u00ed kosmetika - pouze n\u00e1hled"))
			self.buyButton.Hide()
		self._RefreshPage()
		self._RefreshLoadoutCards()
		self._RefreshModel()

	def _BuySelected(self):
		if self.currentVnum in self.itemshopOffers and self.owner:
			self.owner.BuyWardrobeItem(self.currentVnum)

	def _RefreshLoadoutCards(self):
		for index, subtype in enumerate(self.SELECTED_SLOT_TYPES):
			vnum = self.selectedItems.get(subtype, 0)
			self.loadoutCards[index].SetItem(vnum)
		self._RefreshTotalPrice()

	def _RefreshTotalPrice(self):
		totalPrice = sum(
			self._OfferPrice(self.itemshopOffers[vnum])
			for vnum in self.selectedItems.values()
			if vnum in self.itemshopOffers
		)
		self.totalPriceText.SetText(
			_Text("WARDROBE_TOTAL_PRICE", "Cena IS polo\u017eek v sestav\u011b: %d DC") % totalPrice)

	def _RemoveSelectedSlot(self, slotIndex):
		if slotIndex < 0 or slotIndex >= len(self.SELECTED_SLOT_TYPES):
			return
		subtype = self.SELECTED_SLOT_TYPES[slotIndex]
		if subtype not in self.selectedItems:
			return
		self.selectedItems.pop(subtype, None)
		self.currentVnum = 0
		self.selectedName.SetText("")
		self.selectedSource.SetText("")
		self.buyButton.Hide()
		self._RefreshPage()
		self._RefreshLoadoutCards()
		self._RefreshModel()

	def _ResetSelection(self):
		self.selectedItems = {}
		self.currentVnum = 0
		self.selectedName.SetText("")
		self.selectedSource.SetText("")
		self.buyButton.Hide()
		self._RefreshPage()
		self._RefreshLoadoutCards()
		self._RefreshModel()

	def _RefreshModel(self):
		effectiveItems = dict(self.baseItems)
		effectiveItems.update(self.selectedItems)
		renderTarget.SetVisibility(RENDER_TARGET_INDEX, False)
		renderTarget.SelectModel(RENDER_TARGET_INDEX, self.currentRace)
		renderTarget.SetVisibility(RENDER_TARGET_INDEX, True)

		body = effectiveItems.get(item.COSTUME_TYPE_BODY, 0)
		weapon = effectiveItems.get(item.COSTUME_TYPE_WEAPON, 0)
		hair = effectiveItems.get(item.COSTUME_TYPE_HAIR, 0)
		acce = effectiveItems.get(item.COSTUME_TYPE_ACCE, 0)
		weaponEffect = effectiveItems.get(item.COSTUME_TYPE_EFFECT_WEAPON, 0)
		armorEffect = effectiveItems.get(item.COSTUME_TYPE_EFFECT_ARMOR, 0)
		if body:
			renderTarget.ChangeArmor(RENDER_TARGET_INDEX, body)
		if weapon:
			renderTarget.ChangeWeapon(RENDER_TARGET_INDEX, weapon)
		if hair:
			item.SelectItem(hair)
			renderTarget.ChangeHair(RENDER_TARGET_INDEX, item.GetValue(3))
		if acce:
			renderTarget.ChangeAcce(RENDER_TARGET_INDEX, acce)
		if weaponEffect:
			renderTarget.ChangeWeaponShining(RENDER_TARGET_INDEX, weaponEffect, armorEffect)
		if armorEffect:
			renderTarget.ChangeArmorShining(RENDER_TARGET_INDEX, armorEffect, weaponEffect)

	def _StartDrag(self):
		self.lastMouseX = self.renderWindow.GetMouseLocalPosition()[0]
		self.isDragging = True

	def _StopDrag(self):
		self.isDragging = False

	def _OnMouseWheel(self, scrollDown):
		renderTarget.SetZoom(RENDER_TARGET_INDEX, not scrollDown)
		return True

	def _RotateLeft(self):
		renderTarget.Rotate(RENDER_TARGET_INDEX, -PREVIEW_ROTATION_STEP)

	def _RotateRight(self):
		renderTarget.Rotate(RENDER_TARGET_INDEX, PREVIEW_ROTATION_STEP)

	def OnUpdate(self):
		if not self.isDragging:
			return
		mouseX = self.renderWindow.GetMouseLocalPosition()[0]
		delta = mouseX - self.lastMouseX
		if delta:
			renderTarget.Rotate(RENDER_TARGET_INDEX, float(delta) * 0.45)
			self.lastMouseX = mouseX

	def _OverInItem(self, vnum):
		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.tooltipItem:
			interface.tooltipItem.SetItemToolTip(vnum)

	def _OverInSelectedSlot(self, slotIndex):
		if 0 <= slotIndex < len(self.SELECTED_SLOT_TYPES):
			vnum = self.selectedItems.get(self.SELECTED_SLOT_TYPES[slotIndex])
			if vnum:
				self._OverInItem(vnum)

	def _OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface and interface.tooltipItem:
			interface.tooltipItem.HideToolTip()
