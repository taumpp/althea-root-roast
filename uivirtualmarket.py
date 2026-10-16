import app
import chat
import grp
import item
import localeInfo
import mouseModule
import net
import player
import ui
import uiCommon
import marketpricedialog
import uitooltip
import uicrimsoncontrols
import virtualmarket
import fontconfig
import marketlayout
import wndMgr
from uicrimsonember import SettingsScrollBar
from uimarketfilters import AdvancedMarketFilterDialog


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 590
CRIMSON_MARKET_SKIN_REVISION = 14
ROW_HEIGHT = marketlayout.BASE_ROW_HEIGHT
MARKET_ROWS_Y = 30
GRID_COLUMNS = 15
GRID_ROWS = 11
GRID_SLOT_COUNT = GRID_COLUMNS * GRID_ROWS
SHOP_LEASE_SECONDS = 5 * 24 * 60 * 60

ROW_WIDTH = 541
SEARCH_INPUT_X = 17
SEARCH_INPUT_Y = 86
SEARCH_ITEM_X = SEARCH_INPUT_X
SEARCH_SELLER_X = SEARCH_INPUT_X
SEARCH_MODE_Y = 117
SEARCH_BUTTON_X = 168
SEARCH_BUTTON_Y = 88
FILTER_BUTTON_X = 199
FILTER_BUTTON_Y = 88
CONTENT_MARGIN = 12
CONTENT_TOP = 78
CONTENT_HEIGHT = 500
CLASSIC_BACKGROUND_NATIVE_HEIGHT = 500
BODY_X = 239
BODY_Y = 78
BODY_WIDTH = 549
BODY_HEIGHT = 500
TOP_INFO_X = 490
TOP_INFO_Y = 550
NAV_START_Y = 36
NAV_STEP_Y = 34
CATEGORY_TITLE_X = 27
CATEGORY_TITLE_Y = 164
CATEGORY_ALL_X = 186
CATEGORY_ALL_Y = 158
CATEGORY_ALL_WIDTH = 43
CATEGORY_VIEWPORT_X = 22
CATEGORY_VIEWPORT_WIDTH = 199
CATEGORY_START_Y = 184
# Compact 32 px rows keep all twelve categories visible inside the discovery
# panel (ends at y=578); only the row surface is scaled, never icons or text.
CATEGORY_STEP_Y = 32
CATEGORY_BUTTON_HEIGHT = 32
CATEGORY_SOURCE_HEIGHT = 38
CATEGORY_VISIBLE_COUNT = 12
CATEGORY_VIEW_HEIGHT = CATEGORY_VISIBLE_COUNT * CATEGORY_STEP_Y
CATEGORY_SCROLL_X = 219
SEARCH_RESET_X = 170
SEARCH_RESET_Y = 110
SEARCH_RESET_WIDTH = 64
PAGINATION_Y = 466
RETRY_Y = 548

ACCOUNT_PANEL_X = 4
ACCOUNT_PANEL_WIDTH = 541
ACCOUNT_HEADER_Y = 0
ACCOUNT_HEADER_HEIGHT = 29
ACCOUNT_CONTENT_Y = 30
ACCOUNT_CONTENT_HEIGHT = 470
ACCOUNT_TOOLBAR_X = 12
ACCOUNT_TOOLBAR_LOCAL_X = ACCOUNT_TOOLBAR_X - ACCOUNT_PANEL_X
ACCOUNT_TOOLBAR_Y = 30
ACCOUNT_TOOLBAR_WIDTH = 525
ACCOUNT_TOOLBAR_HEIGHT = 38
ACCOUNT_ACTION_SIZE = 30
ACCOUNT_ACTION_GAP = 4
ACCOUNT_TOOLBAR_LOCAL_Y = 0
ACCOUNT_GRID_X = (ACCOUNT_PANEL_WIDTH - GRID_COLUMNS * 32) // 2
ACCOUNT_GRID_Y = 46
ACCOUNT_VALUE_STRIP_Y = 402
ACCOUNT_VALUE_STRIP_HEIGHT = 38
ACCOUNT_PAGE_Y = 9
ACCOUNT_PREV_X = 223
ACCOUNT_PAGE_CENTER_X = 270
ACCOUNT_NEXT_X = 292
CREATE_BUTTON_WIDTH = 170
CREATE_BUTTON_X = (ACCOUNT_PANEL_WIDTH - CREATE_BUTTON_WIDTH) // 2
OWNER_ACTION_START_X = 355
DELIVERY_ACTION_START_X = 457
RETURN_ACTION_START_X = 423
OWNER_STATE_OPEN_COLOR = (114 / 255.0, 198 / 255.0, 106 / 255.0)
OWNER_STATE_CLOSED_COLOR = (224 / 255.0, 68 / 255.0, 87 / 255.0)
OWNER_STATE_SUSPENDED_COLOR = (227 / 255.0, 154 / 255.0, 59 / 255.0)
CURRENCY_YANG_COLOR = (247 / 255.0, 200 / 255.0, 28 / 255.0)

ITEM_SLOT_X = 33
ITEM_NAME_X = 73
ITEM_NAME_SAFE_WIDTH = 148
ITEM_COLUMN_CENTER_X = 127
COUNT_CENTER_X = 244
COUNT_SAFE_WIDTH = 32
SELLER_CENTER_X = 469
SELLER_SAFE_WIDTH = 66
PRICE_COLUMN_CENTER_X = 347
PRICE_RIGHT_X = 430
PRICE_SAFE_WIDTH = 166
PRICE_PRIMARY_CENTER_Y = 20
PRICE_UNIT_CENTER_Y = 31
COIN_X = 0
MESSAGE_X = 510
MESSAGE_ICON_X = 516
MESSAGE_ICON_Y = 18
ACTION_X = 7
ACTION_CENTER_X = 524
CATEGORY_TEXT_CENTER_X = 100
CATEGORY_TEXT_CENTER_Y = 16
MODE_TEXT_CENTER_X = 95
MODE_TEXT_CENTER_Y = 17
ROW_TEXT_CENTER_Y = 24
HEADER_TEXT_CENTER_Y = 15
MODE_TAB_WIDTH = 190
CHECKBOX_LABEL_Y_OFFSET = -1
PAGINATION_ICON_X = 5
PAGINATION_ICON_Y = 5
MARKET_FOOTER_X = 4
MARKET_FOOTER_Y = 439
MARKET_ROWS_HEIGHT = MARKET_FOOTER_Y - MARKET_ROWS_Y - 1
MARKET_FOOTER_WIDTH = 541
MARKET_FOOTER_HEIGHT = 61
SELECTION_LABEL_X = 11
FOOTER_TEXT_Y = 469
TOTAL_RIGHT_X = 530
BUY_SELECTED_Y = 440

CRIMSON_MARKET_DIR = "d:/ymir work/ui/game/crimson_ember/virtual_market/"
SEARCH_UI_PATH = "d:/ymir work/ui/game/search_shop/"
OFFLINE_SHOP_UI_PATH = "d:/ymir work/ui/game/offline_shop/"
ITEM_ROW_PATH = CRIMSON_MARKET_DIR + "surface/result_normal.png"
ITEM_SLOT_PATH = "d:/ymir work/ui/public/Slot_Base.sub"
ITEM_COIN_PATH = ""

TAB_MARKET = 0
TAB_OWNER = 1
TAB_DELIVERIES = 2
TAB_RETURNS = 3

MARKET_CATEGORIES = (
	("VIRTUAL_MARKET_CATEGORY_WEAPONS", "Zbran\u011b", "weapons", item.ITEM_TYPE_WEAPON, -1),
	("VIRTUAL_MARKET_CATEGORY_EQUIPMENT", "V\u00fdbava", "armors", item.ITEM_TYPE_ARMOR, -1),
	("VIRTUAL_MARKET_CATEGORY_COSTUMES", "Kost\u00fdmy", "costumes", item.ITEM_TYPE_COSTUME, -1),
	("VIRTUAL_MARKET_CATEGORY_SASHES", "Šerpy", "sashes", item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_ACCE),
	("VIRTUAL_MARKET_CATEGORY_PETS", "Mazl\u00ed\u010dci", "pets", item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_PET),
	("VIRTUAL_MARKET_CATEGORY_MOUNTS", "Mounti", "mounts", item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_MOUNT),
	("VIRTUAL_MARKET_CATEGORY_ALCHEMY", "Alchymie", "alchemy", item.ITEM_TYPE_DS, -1),
	("VIRTUAL_MARKET_CATEGORY_BOOKS", "Knihy", "skills", item.ITEM_TYPE_SKILLBOOK, -1),
	("VIRTUAL_MARKET_CATEGORY_STONES", "Kameny", "ghoststones", item.ITEM_TYPE_METIN, -1),
	("VIRTUAL_MARKET_CATEGORY_CONSUMABLES", "Spot\u0159ebn\u00ed", "consumeables", item.ITEM_TYPE_USE, -1),
	("VIRTUAL_MARKET_CATEGORY_MATERIALS", "Materi\u00e1ly", "materials", item.ITEM_TYPE_MATERIAL, -1),
	# Server category 12: everything outside the categories above. It has no
	# single item type, so it exists only as a SearchV4 category.
	("VIRTUAL_MARKET_CATEGORY_OTHER", "Ostatn\u00ed", "other", -1, -1),
)
MARKET_CATEGORY_IDS = (1, 2, 3, 11, 4, 5, 6, 7, 8, 9, 10, 12)
MARKET_CATEGORY_OTHER = 12
# The server rate-limits searches per player to 250 ms; one automatic retry
# waits slightly longer so a refused request succeeds without user action.
SEARCH_RATE_LIMIT_RETRY_DELAY = 0.3
# ALTHEA-622: item.GetItemNamesByName accepts at most 64 results; the dropdown
# shows eight rows and scrolls the rest, so every +N of an item is reachable.
SEARCH_SUGGESTION_LIMIT = 64
SEARCH_SUGGESTION_VISIBLE = 8


def _OtherCategoryAvailable():
	# Needs the compatible executable and the server capability offer.
	return bool(getattr(net, "IsVirtualMarketCategoryOtherAvailable", lambda: 0)())



def _Text(key, fallback):
	return getattr(localeInfo, key, fallback)


def _ListingItemLink(index):
	"""Build the normal client item hyperlink from the immutable market snapshot."""
	try:
		vnum = int(virtualmarket.GetListingVnum(index))
		if vnum <= 0:
			return ""
		tokens = ["item", "%x" % vnum, "0"]
		socketCount = 5 if hasattr(chat, "HYPER_LINK_ITEM_SOCKET4") else 3
		for socket in range(socketCount):
			tokens.append("%x" % int(virtualmarket.GetListingSocket(index, socket)))

		if getattr(app, "ENABLE_CHANGE_LOOK_SYSTEM", 0):
			unusedSoulbind, transmutation = virtualmarket.GetListingIdentity(index)
			tokens.append("%x" % int(transmutation))

		if getattr(app, "ENABLE_APPLY_RANDOM", 0):
			for attribute in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
				applyType, applyValue = tuple(
					virtualmarket.GetListingRandomApply(index, attribute))[:2]
				tokens.extend(("%x" % int(applyType), str(int(applyValue))))

		if getattr(app, "ENABLE_REFINE_ELEMENT_SYSTEM", 0):
			applyType, grade, values, bonuses = virtualmarket.GetListingRefineElement(index)
			refineValues = (applyType, grade) + tuple(values) + tuple(bonuses)
			tokens.extend("%x" % int(value) for value in refineValues)

		for attribute in range(player.ATTRIBUTE_SLOT_MAX_NUM):
			applyType, applyValue = tuple(
				virtualmarket.GetListingAttribute(index, attribute))[:2]
			if int(applyType) == 0:
				continue
			tokens.extend(("%x" % int(applyType), str(int(applyValue))))

		link = chat.GetLinkFromHyperlink(":".join(tokens))
		return link if link else ""
	except:
		return ""


def _SetButtonVisuals(button, prefix, selected=False):
	button.SetUpVisual(CRIMSON_MARKET_DIR + prefix + "_normal.png")
	button.SetOverVisual(CRIMSON_MARKET_DIR + prefix + "_hover.png")
	button.SetDownVisual(CRIMSON_MARKET_DIR + prefix +
		("_selected.png" if selected else "_pressed.png"))
	button.SetDisableVisual(CRIMSON_MARKET_DIR + prefix + "_disabled.png")


def _CrimsonButton(parent, x, y, prefix, event, text="", selected=False):
	button = ui.RadioButton() if selected else ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	_SetButtonVisuals(button, prefix, selected)
	if text:
		button.SetText(text)
		button.SetTextColor(0xffeadfc8)
	button.SetEvent(event)
	button.Show()
	return button


def _Button(parent, x, y, text, event, size="middle"):
	prefix = "button/action"
	return _CrimsonButton(parent, x, y, prefix, event, text)


def _CrimsonPrimaryButton(parent, x, y, text, event):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetSize(CREATE_BUTTON_WIDTH, 24)
	uicrimsoncontrols.ApplyVisuals(button, "170x24")
	button.SetText(text)
	button.SetEvent(event)
	button.Show()
	return button


def _Label(parent, x, y, text="", color=None, role=fontconfig.ROLE_BODY):
	label = ui.TextLine()
	label.SetParent(parent)
	label.SetPosition(x, y)
	label.AddFlag("not_pick")
	label.SetFontName(fontconfig.FontForRole(role))
	label.SetText(text)
	if color is not None:
		label.SetPackedFontColor(color)
	label.Show()
	return label


def _SmallLabel(parent, x, y, text):
	label = _Label(parent, x, y, text, role=fontconfig.ROLE_DENSE)
	label.SetFontColor(1.0, 1.0, 1.0)
	return label


def _Image(parent, x, y, filename):
	image = ui.ExpandedImageBox()
	image.SetParent(parent)
	image.SetPosition(x, y)
	image.LoadImage(filename)
	image.AddFlag("not_pick")
	image.Show()
	return image


def _Panel(parent, x, y, width, height):
	panel = ui.ThinBoard()
	panel.SetParent(parent)
	panel.SetPosition(x, y)
	panel.SetSize(width, height)
	panel.Show()
	return panel


def _Container(parent, x, y, width, height):
	container = ui.Window()
	container.SetParent(parent)
	container.SetPosition(x, y)
	container.SetSize(width, height)
	container.Show()
	return container


def _Edit(parent, x, y, width, placeholder=""):
	board = ui.ThinBoard()
	board.SetParent(parent)
	board.SetPosition(x, y)
	board.SetSize(width, 24)
	board.Show()
	edit = ui.EditLine()
	edit.SetParent(board)
	edit.SetPosition(7, 5)
	edit.SetSize(width - 14, 16)
	edit.SetMax(6)
	edit.SetInfoMessage(placeholder)
	edit.Show()
	return board, edit


def _CrimsonModeTab(parent, x, text, role, event):
	button = _CrimsonButton(parent, x, 36, "tab/%s" % role,
		event, "", True)
	label = _Label(
		button, MODE_TEXT_CENTER_X, MODE_TEXT_CENTER_Y, text, 0xffeadfc8,
		role=fontconfig.ROLE_CONTROL)
	label.SetHorizontalAlignCenter()
	label.SetVerticalAlignCenter()
	iconPositions = {
		"market": (10, 7),
		"owner_shop": (11, 7),
		"deliveries": (10, 7),
		"returns": (10, 7),
	}
	iconX, iconY = iconPositions[role]
	icon = _Image(button, iconX, iconY,
		CRIMSON_MARKET_DIR + "icon/mode_%s.png" % role)
	return button, icon, label


def _ClassicTab(parent, x, y, text, iconName, event):
	button = _CrimsonButton(parent, x, y, "category/row",
		event, "", True)
	wndMgr.SetScale(button.hWnd, 1.0,
		float(CATEGORY_BUTTON_HEIGHT) / CATEGORY_SOURCE_HEIGHT)
	button.SetSize(CATEGORY_VIEWPORT_WIDTH, CATEGORY_BUTTON_HEIGHT)
	label = _Label(
		button, CATEGORY_TEXT_CENTER_X, CATEGORY_TEXT_CENTER_Y, text, 0xffeadfc8,
		role=fontconfig.ROLE_CONTROL)
	label.SetHorizontalAlignCenter()
	label.SetVerticalAlignCenter()
	iconAliases = {
		"armors": "equipment",
		"skills": "books",
		"ghoststones": "stones",
		"consumeables": "consumables",
	}
	# 24 px Crimson icons are centred on the 32 px row; the 18 px legacy
	# offline-shop icons (sashes, other) share the same centre.
	iconPositions = {
		"weapons": (8, 4),
		"armors": (8, 4),
		"costumes": (9, 4),
		"pets": (9, 4),
		"mounts": (9, 4),
		"alchemy": (8, 4),
		"skills": (8, 4),
		"ghoststones": (9, 4),
		"consumeables": (12, 4),
		"materials": (8, 5),
		"sashes": (11, 7),
		"other": (11, 7),
	}
	legacyIcons = {
		"sashes": "sashes_default.png",
		"other": "everything_default.png",
	}
	iconX, iconY = iconPositions.get(iconName, (8, 4))
	iconRole = iconAliases.get(iconName, iconName)
	iconPath = "assets/ui/offlineshop-search/icons/" + legacyIcons[iconName] \
		if iconName in legacyIcons else \
		CRIMSON_MARKET_DIR + "icon/category_%s.png" % iconRole
	icon = _Image(button, iconX, iconY, iconPath)
	return button, icon, label


def _FilterButton(parent, x, y, text, event):
	button = _CrimsonButton(parent, x, y, "choice/checkbox",
		event, text, True)
	return button


def _CrimsonCheckbox(parent, x, y, text, downEvent, upEvent):
	button = _CrimsonCheckboxButton(parent, x, y, downEvent, upEvent)
	label = _Label(
		parent, x + 22, y + CHECKBOX_LABEL_Y_OFFSET,
		text, 0xffd8cbb5)
	return button, label


def _CrimsonCheckboxButton(parent, x, y, downEvent, upEvent):
	button = ui.ToggleButton()
	button.SetParent(parent)
	button.SetSize(15, 14)
	button.SetPosition(x, y)
	_SetButtonVisuals(button, "choice/checkbox", True)
	button.SetToggleDownEvent(downEvent)
	button.SetToggleUpEvent(upEvent)
	button.Show()
	return button


def _CrimsonIconButton(
		parent, x, y, prefix, event, icon=None,
		iconX=7, iconY=5):
	button = _CrimsonButton(parent, x, y, prefix, event)
	if icon:
		button.icon = _Image(button, iconX, iconY,
			CRIMSON_MARKET_DIR + icon)
	return button


def _TransparentIconButton(parent, x, y, icon, event):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	filename = CRIMSON_MARKET_DIR + icon
	button.SetUpVisual(filename)
	button.SetOverVisual(filename)
	button.SetDownVisual(filename)
	button.SetDisableVisual(filename)
	button.SetEvent(event)
	button.Show()
	return button


class _SellerLink(ui.Window):
	NORMAL_COLOR = grp.GenerateColor(
		216.0 / 255.0, 173.0 / 255.0, 85.0 / 255.0, 1.0)
	HOVER_COLOR = grp.GenerateColor(
		255.0 / 255.0, 211.0 / 255.0, 107.0 / 255.0, 1.0)
	NORMAL_UNDERLINE_COLOR = NORMAL_COLOR
	HOVER_UNDERLINE_COLOR = HOVER_COLOR

	def __init__(self, parent, x, y, width, height, text, event, payload):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.event = event
		self.payload = payload
		self.label = _Label(
			self, width // 2, height // 2, text, self.NORMAL_COLOR)
		self.label.SetHorizontalAlignCenter()
		self.label.SetVerticalAlignCenter()
		self.label.SetLimitWidth(width)

		textWidth, _textHeight = self.label.GetTextSize()
		underlineWidth = max(1, min(width, int(textWidth)))
		self.underline = ui.Bar()
		self.underline.SetParent(self)
		self.underline.SetPosition(
			(width - underlineWidth) // 2, height // 2 + 9)
		self.underline.SetSize(underlineWidth, 2)
		self.underline.SetColor(self.NORMAL_UNDERLINE_COLOR)
		self.underline.AddFlag("not_pick")
		self.underline.Show()

		sellerName = str(payload)
		tooltipText = _Text(
			"VIRTUAL_MARKET_FILTER_SELLER_HINT",
			"Kliknutím vyfiltrujete nabídky hráče %s.") % sellerName
		self.tooltip = uitooltip.ToolTip()
		self.tooltip.AutoAppendNewTextLineResize(tooltipText)
		self.tooltip.HideToolTip()
		self.Show()

	def OnMouseOverIn(self):
		self.label.SetPackedFontColor(self.HOVER_COLOR)
		self.underline.SetColor(self.HOVER_UNDERLINE_COLOR)
		self.tooltip.ShowToolTip()

	def OnMouseOverOut(self):
		self.label.SetPackedFontColor(self.NORMAL_COLOR)
		self.underline.SetColor(self.NORMAL_UNDERLINE_COLOR)
		self.tooltip.HideToolTip()

	def OnMouseLeftButtonUp(self):
		if self.IsIn() and self.event:
			self.event(self.payload)

	def Destroy(self):
		if self.tooltip:
			self.tooltip.HideToolTip()
		self.event = None
		self.payload = None
		self.label = None
		self.underline = None
		self.tooltip = None
		self.Hide()


class _UnderlinedTextButton(ui.Window):
	NORMAL_COLOR = grp.GenerateColor(
		234.0 / 255.0, 223.0 / 255.0, 200.0 / 255.0, 1.0)
	HOVER_COLOR = grp.GenerateColor(
		255.0 / 255.0, 211.0 / 255.0, 107.0 / 255.0, 1.0)

	def __init__(self, parent, x, y, width, height, text, event):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.event = event
		self.label = _Label(
			self, width // 2, height // 2, text, self.NORMAL_COLOR,
			role=fontconfig.ROLE_CONTROL)
		self.label.SetHorizontalAlignCenter()
		self.label.SetVerticalAlignCenter()
		self.label.SetLimitWidth(width)

		textWidth, _textHeight = self.label.GetTextSize()
		underlineWidth = max(1, min(width, int(textWidth)))
		self.underline = ui.Bar()
		self.underline.SetParent(self)
		self.underline.SetPosition(
			(width - underlineWidth) // 2, height // 2 + 8)
		self.underline.SetSize(underlineWidth, 1)
		self.underline.SetColor(self.NORMAL_COLOR)
		self.underline.AddFlag("not_pick")
		self.underline.Show()
		self.Show()

	def OnMouseOverIn(self):
		self.label.SetPackedFontColor(self.HOVER_COLOR)
		self.underline.SetColor(self.HOVER_COLOR)

	def OnMouseOverOut(self):
		self.label.SetPackedFontColor(self.NORMAL_COLOR)
		self.underline.SetColor(self.NORMAL_COLOR)

	def OnMouseLeftButtonUp(self):
		if self.IsIn() and self.event:
			self.event()

	def Destroy(self):
		self.event = None
		self.label = None
		self.underline = None
		self.Hide()


def _RunAccountAction(button):
	if getattr(button, "accountActionAvailable", False):
		button.accountActionEvent()


def _SetAccountActionAvailable(button, available):
	button.accountActionAvailable = bool(available)


def _AccountActionButton(parent, x, role, event, tooltip, enabled=True):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, 4)
	button.SetSize(ACCOUNT_ACTION_SIZE, ACCOUNT_ACTION_SIZE)
	_SetButtonVisuals(button, "button/account_action")
	button.icon = _Image(
		button, 5, 5,
		CRIMSON_MARKET_DIR + "icon/account_%s.png" % role)
	button.accountActionEvent = event
	button.accountActionAvailable = bool(enabled)
	button.SetEvent(lambda target=button: _RunAccountAction(target))
	button.SetToolTipText(tooltip)
	button.Show()
	return button


class _SequentialClaimController(object):
	def __init__(self):
		self.Stop()

	def Start(self, source):
		self.source = int(source)
		self.currentPayload = None
		self.awaitingRefresh = False
		self.active = True

	def IsActive(self):
		return self.active

	def CanBegin(self):
		return self.active and self.currentPayload is None and not self.awaitingRefresh

	def Begin(self, payload):
		if not self.CanBegin() or int(payload[0]) != self.source:
			return False
		self.currentPayload = payload
		return True

	def MarkSucceeded(self):
		if self.currentPayload is None:
			return False
		self.currentPayload = None
		self.awaitingRefresh = True
		return True

	def MarkRefreshed(self):
		if not self.active or not self.awaitingRefresh:
			return False
		self.awaitingRefresh = False
		return True

	def Stop(self):
		self.active = False
		self.source = None
		self.currentPayload = None
		self.awaitingRefresh = False


def _RightAlignLabelPair(left, right, rightX):
	leftWidth, _leftHeight = left.GetTextSize()
	rightWidth, _rightHeight = right.GetTextSize()
	startX = int(rightX - leftWidth - rightWidth)
	left.SetPosition(startX, FOOTER_TEXT_Y)
	right.SetPosition(startX + leftWidth, FOOTER_TEXT_Y)


def _CenterAccountValuePair(left, right, centerX, y):
	leftWidth, _leftHeight = left.GetTextSize()
	rightWidth, _rightHeight = right.GetTextSize()
	startX = int(centerX - (leftWidth + rightWidth) / 2)
	left.SetPosition(startX, y)
	right.SetPosition(startX + leftWidth, y)


def _YangText(value):
	return "%s Yang\u016f" % format(int(value), ",").replace(",", " ")


def _UnitYangText(value, count):
	return "%s /ks" % format(
		int(value) // max(1, int(count)), ",").replace(",", " ")


def _ItemName(vnum):
	try:
		item.SelectItem(int(vnum))
		return item.GetItemName()
	except:
		return "VNUM %d" % int(vnum)


def _Money(value):
	try:
		return localeInfo.NumberToMoneyString(int(value))
	except:
		return "%d Yang" % int(value)


def _Remaining(expiresAt):
	remaining = max(0, int(expiresAt) - int(app.GetGlobalTimeStamp()))
	days, remaining = divmod(remaining, 24 * 60 * 60)
	hours, remaining = divmod(remaining, 60 * 60)
	minutes, seconds = divmod(remaining, 60)
	if days:
		return "%dd %02d:%02d:%02d" % (days, hours, minutes, seconds)
	return "%02d:%02d:%02d" % (hours, minutes, seconds)


def _SortSuggestions(names):
	"""Order refine levels numerically within each item (+2 before +10).

	The client returns names sorted as text, so "Item+10" precedes "Item+2".
	Items keep the client's order (prefix matches first); only the +N of the
	same base name are reordered.
	"""
	firstSeen = {}
	keys = []
	for index, name in enumerate(names):
		base, separator, level = name.rpartition("+")
		if not separator or not level.isdigit():
			base, level = name, -1
		else:
			level = int(level)
		firstSeen.setdefault(base, index)
		keys.append((firstSeen[base], level, index))
	return [names[key[2]] for key in sorted(keys)]


def _ScaleRememberedPrice(totalPrice, itemCount, requestedCount):
	try:
		totalPrice = int(totalPrice)
		itemCount = int(itemCount)
		requestedCount = int(requestedCount)
	except (TypeError, ValueError):
		return 0
	if totalPrice <= 0 or itemCount <= 0 or requestedCount <= 0:
		return 0
	scaled = (totalPrice * requestedCount + itemCount - 1) // itemCount
	return scaled if scaled <= 10000000000 else 0


def _ItemHeight(vnum):
	try:
		item.SelectItem(int(vnum))
		return max(1, min(GRID_ROWS, int(item.GetItemSize()[1])))
	except:
		return 1


def _PackGridRecords(records):
	pages = []
	page = []
	occupied = [False] * GRID_SLOT_COUNT
	for record in records:
		height = _ItemHeight(record[1])
		position = None
		for row in range(GRID_ROWS - height + 1):
			for column in range(GRID_COLUMNS):
				candidate = row * GRID_COLUMNS + column
				if all(not occupied[candidate + offset * GRID_COLUMNS]
						for offset in range(height)):
					position = candidate
					break
			if position is not None:
				break
		if position is None:
			pages.append(page)
			page = []
			occupied = [False] * GRID_SLOT_COUNT
			position = 0
		for offset in range(height):
			occupied[position + offset * GRID_COLUMNS] = True
		page.append((position,) + tuple(record))
	if page or not pages:
		pages.append(page)
	return pages


def _MapGridItemFootprint(slotMap, slotIndex, height, entry):
	"""Map every occupied cell back to the item's anchor record.

	The native grid normally resolves a tall item to its anchor slot.  Keeping an
	explicit footprint map also covers the constituent cells reported through the
	empty-slot hover/right-click callbacks, so the full visual slot behaves as one
	item target.
	"""
	slotIndex = int(slotIndex)
	height = max(1, min(GRID_ROWS, int(height)))
	for offset in range(height):
		cell = slotIndex + offset * GRID_COLUMNS
		if 0 <= cell < GRID_SLOT_COUNT:
			slotMap[cell] = entry


def _ClearGridItems(grid):
	# wndMgr.ClearAllSlot() destroys the native slot definitions in this client.
	# Preserve the arranged 15x11 grid and clear only each slot's item payload.
	for slotIndex in range(GRID_SLOT_COUNT):
		grid.ClearSlot(slotIndex)


class SearchSuggestionDropdown(ui.ThinBoard):
	def __init__(self, parent, selectEvent, x=10, y=31):
		ui.ThinBoard.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(220, 24)
		self.AddFlag("float")
		self.selectEvent = selectEvent
		self.listBox = ui.ListBox()
		self.listBox.SetParent(self)
		self.listBox.SetPosition(6, 5)
		self.listBox.SetSize(208, 17)
		self.listBox.SetTextCenterAlign(False)
		self.listBox.SetEvent(self._Select)
		self.listBox.SetOnRunMouseWheelEvent(self._OnMouseWheel)
		self.listBox.Show()
		self.SetOnRunMouseWheelEvent(self._OnMouseWheel)
		self.scrollBar = SettingsScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(204, 5)
		self.scrollBar.SetScrollEvent(self._OnScroll)
		self.scrollBar.Hide()
		self.startIndex = 0
		self.itemCount = 0
		self.Hide()

	def _MaxStart(self):
		return max(0, self.itemCount - SEARCH_SUGGESTION_VISIBLE)

	def Open(self, names):
		self.listBox.ClearItem()
		self.startIndex = 0
		self.itemCount = len(names)
		for index, name in enumerate(names):
			self.listBox.InsertItem(index, name)
		if not names:
			self.scrollBar.Hide()
			self.Hide()
			return
		visible = min(SEARCH_SUGGESTION_VISIBLE, len(names))
		height = visible * self.listBox.GetStepSize() + 10
		self.SetSize(220, height)
		maxStart = self._MaxStart()
		self.listBox.SetSize(194 if maxStart else 208, height - 10)
		self.listBox.SetBasePos(0)
		if maxStart:
			self.scrollBar.SetScrollBarSize(height - 10)
			self.scrollBar.SetMiddleBarSize(float(visible) / len(names))
			self.scrollBar.SetScrollStep(1.0 / float(maxStart))
			self.scrollBar.SetPos(0.0)
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		self.Show()
		self.SetTop()

	def _OnScroll(self):
		maxStart = self._MaxStart()
		startIndex = int(self.scrollBar.GetPos() * maxStart + 0.5) if maxStart else 0
		if startIndex != self.startIndex:
			self.startIndex = startIndex
			self.listBox.SetBasePos(startIndex)

	def _OnMouseWheel(self, scrollDown):
		maxStart = self._MaxStart()
		if not maxStart:
			return
		step = 1.0 / float(maxStart)
		position = self.scrollBar.GetPos()
		self.scrollBar.SetPos(position + step if scrollDown else position - step)

	def Close(self):
		self.Hide()

	def _Select(self, key, name):
		self.Close()
		if self.selectEvent:
			self.selectEvent(name)


class CrimsonMarketRow(ui.Window):
	def __init__(self, parent, y, vnum, itemCount, priceText, metaText,
			sellerName, actionText, actionEvent, payload, messageEvent=None,
			tooltipIn=None, tooltipOut=None, messagePayload=None,
			sellerSearchEvent=None, sellerSearchPayload=None, selected=False,
			selectionMode=True):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(4, y)
		itemHeight = _ItemHeight(vnum)
		rowHeight = marketlayout.RowHeight(itemHeight)
		centerOffset = (rowHeight - ROW_HEIGHT) // 2
		self.SetSize(ROW_WIDTH, rowHeight)
		self.payload = payload
		self.actionEvent = actionEvent
		self.selectionMode = bool(selectionMode)
		self.selected = False
		self.tooltipIn = tooltipIn
		self.tooltipOut = tooltipOut
		self.labels = []

		self.background = ui.ToggleButton()
		self.background.SetParent(self)
		self.background.SetSize(ROW_WIDTH, ROW_HEIGHT)
		self.background.SetPosition(0, 0)
		_SetButtonVisuals(self.background, "surface/result", True)
		# Scale only the result surface; icons and controls retain native pixels.
		wndMgr.SetScale(self.background.hWnd, 1.0, float(rowHeight) / ROW_HEIGHT)
		self.background.SetSize(ROW_WIDTH, rowHeight)
		self.background.SetToggleDownEvent(
			lambda: self._RequestSelected(True))
		self.background.SetToggleUpEvent(
			lambda: self._RequestSelected(False))
		self.background.SAFE_SetOverInEvent(self._TooltipIn)
		self.background.SAFE_SetOverOutEvent(self._TooltipOut)
		self.background.Show()

		self.checkbox = _CrimsonCheckboxButton(
			self, ACTION_X, 18 + centerOffset,
			lambda: self._RequestSelected(True),
			lambda: self._RequestSelected(False))
		self.action = self.checkbox
		self.SetSelected(selected)

		self.itemSlot = ui.GridSlotWindow()
		self.itemSlot.SetParent(self)
		self.itemSlot.SetPosition(ITEM_SLOT_X, 10)
		self.itemSlot.ArrangeSlot(0, 1, itemHeight, 32, 32, 0, 0)
		self.itemSlot.SetSlotBaseImage(
			"d:/ymir work/ui/public/Slot_Base.sub",
			1.0, 1.0, 1.0, 1.0)
		self.itemSlot.SetOverInItemEvent(self._TooltipIn)
		self.itemSlot.SetOverOutItemEvent(self._TooltipOut)
		self.itemSlot.SetOverInEvent(self._TooltipIn)
		self.itemSlot.SetOverOutEvent(self._TooltipOut)
		self.itemSlot.SetSelectItemSlotEvent(self._ToggleSelection)
		self.itemSlot.SetSelectEmptySlotEvent(self._ToggleSelection)
		self.itemSlot.SetItemSlot(0, int(vnum))
		self.itemSlot.RefreshSlot()
		self.itemSlot.Show()

		name = _ItemName(vnum)
		if len(name) > 24:
			name = name[:23] + "..."
		nameLabel = _Label(
			self, ITEM_NAME_X, ROW_TEXT_CENTER_Y + centerOffset, name, 0xffeadfc8)
		nameLabel.SetVerticalAlignCenter()
		nameLabel.SetLimitWidth(ITEM_NAME_SAFE_WIDTH)
		self.labels.append(nameLabel)
		countLabel = _Label(
			self, COUNT_CENTER_X, ROW_TEXT_CENTER_Y + centerOffset,
			str(int(itemCount)), 0xffeadfc8)
		countLabel.SetHorizontalAlignCenter()
		countLabel.SetVerticalAlignCenter()
		countLabel.SetLimitWidth(COUNT_SAFE_WIDTH)
		self.labels.append(countLabel)

		price = int(payload[2])
		priceLabel = _Label(
			self, PRICE_COLUMN_CENTER_X, PRICE_PRIMARY_CENTER_Y + centerOffset,
			_YangText(price))
		priceLabel.SetFontColor(1.0, 1.0, 0.0)
		priceLabel.SetHorizontalAlignCenter()
		priceLabel.SetVerticalAlignCenter()
		priceLabel.SetLimitWidth(PRICE_SAFE_WIDTH)
		self.labels.append(priceLabel)
		unitLabel = _SmallLabel(
			self, PRICE_COLUMN_CENTER_X, PRICE_UNIT_CENTER_Y + centerOffset,
			_UnitYangText(price, itemCount))
		unitLabel.SetHorizontalAlignCenter()
		unitLabel.SetVerticalAlignCenter()
		unitLabel.SetLimitWidth(PRICE_SAFE_WIDTH)
		self.labels.append(unitLabel)

		displaySeller = sellerName if len(sellerName) <= 10 else sellerName[:7] + "..."
		self.sellerLink = None
		if sellerName and sellerSearchEvent:
			self.sellerLink = _SellerLink(
				self, SELLER_CENTER_X - SELLER_SAFE_WIDTH // 2, 0,
				SELLER_SAFE_WIDTH, rowHeight, displaySeller,
				sellerSearchEvent, sellerSearchPayload)
		else:
			sellerLabel = _Label(
				self, SELLER_CENTER_X, ROW_TEXT_CENTER_Y + centerOffset,
				displaySeller, 0xffeadfc8)
			sellerLabel.SetHorizontalAlignCenter()
			sellerLabel.SetVerticalAlignCenter()
			sellerLabel.SetLimitWidth(SELLER_SAFE_WIDTH)
			self.labels.append(sellerLabel)

		self.message = None
		if sellerName and messageEvent:
			self.message = _TransparentIconButton(
				self, MESSAGE_ICON_X, MESSAGE_ICON_Y + centerOffset,
				"icon/message.png",
				lambda value=messagePayload: messageEvent(value),
			)
			self.message.SetToolTipText(_Text(
				"VIRTUAL_MARKET_MESSAGE_SELLER", "Napsat prodejci"))
		self.Show()

	def _TooltipIn(self, slotIndex=None):
		if self.tooltipIn:
			self.tooltipIn()

	def _TooltipOut(self):
		if self.tooltipOut:
			self.tooltipOut()

	def SetSelected(self, selected):
		self.selected = bool(selected)
		if self.selected:
			self.background.Down()
			self.checkbox.Down()
		else:
			self.background.SetUp()
			self.checkbox.SetUp()

	def _ToggleSelection(self, slotIndex=None):
		self._RequestSelected(not self.selected)

	def _RequestSelected(self, selected):
		if self.selectionMode:
			actualSelected = False
			if self.actionEvent:
				actualSelected = bool(
					self.actionEvent(self.payload, bool(selected)))
			self.SetSelected(actualSelected)
			return

		if selected and self.actionEvent:
			self.actionEvent(self.payload)
		self.SetSelected(False)

	def Destroy(self):
		self.action = None
		self.actionEvent = None
		self.checkbox = None
		self.message = None
		if self.sellerLink:
			self.sellerLink.Destroy()
		self.sellerLink = None
		self.background = None
		self.itemSlot = None
		self.labels = []
		self.payload = None
		self.tooltipIn = None
		self.tooltipOut = None
		self.Hide()


class VirtualMarketWindow(ui.BoardWithTitleBar):
	def __init__(self, interface):
		ui.BoardWithTitleBar.__init__(self)
		self.interface = interface
		self.currentTab = TAB_MARKET
		self.rows = []
		self.marketPages = []
		self.marketLayoutCount = 0
		self.currentPage = 0
		self.advanceAfterAppend = False
		self.lastSearchVnum = 0
		self.lastSearchType = None
		self.lastSearchVnums = []
		self.lastSellerName = ""
		self.lastSellerExact = False
		self.lastSearchV3 = None
		self.lastItemName = ""
		self.lastItemExact = False
		# (displayed item name, exact VNUM) from the inventory shortcut.
		self.pinnedSearch = None
		self.searchRetryEvent = None
		self.searchRetryAt = 0.0
		self.searchRetryInProgress = False
		self.searchMode = "item"
		self.sellerExact = False
		self.searchChangedAt = 0.0
		self.lastSuggestionText = ""
		self.pendingSuggestionText = ""
		self.marketSearched = False
		self.selectedPurchases = {}
		self.batchPurchaseAvailable = hasattr(net, "SendVirtualMarketBatchPurchase")
		self.categoryStartIndex = 0
		self.offer = None
		self.ownerShopOpen = False
		self.pendingListingCreate = None
		self.pendingReprice = None
		self.ownerDragListingId = 0
		self.ownerDragHeight = 1
		self.ownerDragOriginalPosition = -1
		self.selectedOwnerListingId = 0
		self.selectedOwnerListingPrice = 0
		self.selectedOwnerVnum = 0
		self.selectedOwnerCount = 0
		self.repricingListingId = 0
		self.gridPages = [[]]
		self.gridSlotMap = {}
		self.claimAllController = _SequentialClaimController()
		self.lastLeaseRefresh = 0.0
		self.lastBoxRefresh = 0.0
		self.nextClaimAt = 0.0
		self.queuedClaims = []
		self.activeClaim = None
		self.boxStateSignature = None
		self.retryEvent = None
		self.confirmEvent = None
		self._Build()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def _Build(self):
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.SetTitleName(_Text("VIRTUAL_MARKET_TITLE", "Virtu\u00e1ln\u00ed tr\u017ei\u0161t\u011b"))
		self.SetCloseEvent(self.Close)
		self.AddFlag("movable")
		self.AddFlag("float")

		self.discoveryPanel = _Image(
			self, 12, 78, CRIMSON_MARKET_DIR + "panel/discovery.png")
		self.workspacePanel = _Image(
			self, 239, 78, CRIMSON_MARKET_DIR + "panel/workspace.png")

		tabData = (
			(_Text("VIRTUAL_MARKET_TAB_MARKET", "Trh"), "market", TAB_MARKET),
			(_Text("VIRTUAL_MARKET_TAB_OWNER", "M\u016fj obchod"), "owner_shop", TAB_OWNER),
			(_Text("VIRTUAL_MARKET_TAB_DELIVERIES", "N\u00e1kupy"), "deliveries", TAB_DELIVERIES),
			(_Text("VIRTUAL_MARKET_TAB_RETURNS", "Vr\u00e1cen\u00e9"), "returns", TAB_RETURNS),
		)
		self.tabs = []
		self.tabIcons = []
		self.tabLabels = []
		self.tabIconNames = []
		self.tabAccents = []
		for index, (text, role, tab) in enumerate(tabData):
			button, icon, label = _CrimsonModeTab(
				self, 20 + index * MODE_TAB_WIDTH, text, role,
				lambda selected=tab: self._SelectTab(selected))
			self.tabs.append(button)
			self.tabIcons.append(icon)
			self.tabLabels.append(label)
			self.tabIconNames.append(role)

		self.categoryTitle = _Label(
			self, CATEGORY_TITLE_X, CATEGORY_TITLE_Y, "Kategorie", 0xff9e8c7c,
			role=fontconfig.ROLE_SECTION)
		self.allCategoriesButton = _UnderlinedTextButton(
			self, CATEGORY_ALL_X, CATEGORY_ALL_Y,
			CATEGORY_ALL_WIDTH, 24,
			_Text("VIRTUAL_MARKET_ALL_CATEGORIES", "Vše"),
			self._ShowAllMarketCategories)
		self.sidebarTitle = _Label(self, 27, 399, "", 0xfff7c81c)
		self.sidebarTitle.Hide()
		self.sidebarLine1 = _Label(self, 27, 425, "", 0xffd8cbb5)
		self.sidebarLine1.Hide()
		self.sidebarLine3 = _Label(self, 27, 467, "", 0xffd8cbb5)
		self.sidebarLine3.Hide()

		self.body = ui.Window()
		self.body.SetParent(self)
		self.body.SetPosition(BODY_X, BODY_Y)
		self.body.SetSize(BODY_WIDTH, BODY_HEIGHT)
		self.body.Show()

		self.sidebarLine2 = _Label(
			self.body, 275, 455,
			_Text("VIRTUAL_MARKET_ACTIVE_SELLERS_SHORT",
				"Aktivn\u00ed prodejci: --"), 0xff9e8c7c)
		self.sidebarLine2.SetHorizontalAlignCenter()
		self.status = _Label(self.body, 275, 455, "")
		self.status.SetHorizontalAlignCenter()
		self.status.Hide()
		self.retryButton = _Button(
			self.body, 441, 456,
			_Text("VIRTUAL_MARKET_RETRY", "Opakovat"), self._Retry)
		self.retryButton.Hide()

		self.confirm = uiCommon.QuestionDialog()
		self.confirm.SetCancelEvent(self._CancelConfirm)
		self.confirm.Hide()
		self.priceDialog = marketpricedialog.MarketPriceDialog()
		self.priceDialog.SetTitle(_Text(
			"PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE", "Prodejn\u00ed cena"))
		self.priceDialog.SetAcceptEvent(self._AcceptOfferPrice)
		self.priceDialog.SetCancelEvent(self._CancelOfferPrice)
		self.priceDialog.Hide()

		self._BuildMarket()
		self._BuildOwner()
		self._BuildBox()
		self.advancedFilters = AdvancedMarketFilterDialog(
			self._ApplyAdvancedFilters)

	def _BuildMarket(self):
		self.searchTitle = _Label(self.body, 10, 4, "", 0xffd8cbb5)
		self.searchTitle.Hide()
		self.searchBackground = _Image(
			self, SEARCH_INPUT_X, SEARCH_INPUT_Y,
			CRIMSON_MARKET_DIR + "field/search_normal.png")
		self.searchBoard = ui.Window()
		self.searchBoard.SetParent(self)
		self.searchBoard.SetPosition(SEARCH_INPUT_X, SEARCH_INPUT_Y)
		self.searchBoard.SetSize(150, 25)
		self.searchBoard.Show()
		self.searchInput = ui.EditLine()
		self.searchInput.SetParent(self.searchBoard)
		self.searchInput.SetPosition(8, 5)
		self.searchInput.SetSize(132, 18)
		self.searchInput.SetMax(64)
		self.searchInput.SetInfoMessage(_Text(
			"VIRTUAL_MARKET_VNUM_PLACEHOLDER", "N\u00e1zev nebo VNUM"))
		self.searchInput.SetReturnEvent(self._Search)
		self.searchInput.SetEscapeEvent(self.OnPressEscapeKey)
		self.searchInput.OnIMEUpdate = self._OnSearchIMEUpdate
		self.searchInput.Show()

		self.exactMatchCheck, self.exactMatchLabel = _CrimsonCheckbox(
			self, 17, 117,
			_Text("VIRTUAL_MARKET_EXACT_MATCH", "P\u0159esn\u00e1 shoda"),
			lambda: self._SetExactMatch(True),
			lambda: self._SetExactMatch(False))
		self.searchPlayerCheck, self.searchPlayerLabel = _CrimsonCheckbox(
			self, 17, 140,
			_Text("VIRTUAL_MARKET_SEARCH_PLAYER", "Hledat jm\u00e9no hr\u00e1\u010de"),
			lambda: self._SetSearchMode("seller"),
			lambda: self._SetSearchMode("item"))
		self.itemModeButton = self.exactMatchCheck
		self.sellerModeButton = self.searchPlayerCheck
		self.searchButton = _CrimsonIconButton(
			self, SEARCH_BUTTON_X, SEARCH_BUTTON_Y,
			"control/search", self._Search)
		self.filterIconButton = _CrimsonIconButton(
			self, FILTER_BUTTON_X, FILTER_BUTTON_Y, "control/filter",
			self._OpenAdvancedFilters)
		self.advancedButton = self.filterIconButton
		self.searchResetButton = _UnderlinedTextButton(
			self, SEARCH_RESET_X, SEARCH_RESET_Y,
			SEARCH_RESET_WIDTH, 20,
			_Text("VIRTUAL_MARKET_SEARCH_RESET", "Reset"),
			self._ResetMarketSearch)
		if not hasattr(net, "SendVirtualMarketSearchV3"):
			self.filterIconButton.Hide()

		self.marketFooter = _Image(
			self.body, MARKET_FOOTER_X, MARKET_FOOTER_Y,
			CRIMSON_MARKET_DIR + "panel/market_footer.png")
		self.selectionCountLabel = _Label(
			self.body, SELECTION_LABEL_X, FOOTER_TEXT_Y,
			"", 0xffeadfc8)
		self.totalPrefixLabel = _Label(
			self.body, TOTAL_RIGHT_X, FOOTER_TEXT_Y,
			"Celkem: ", 0xffeadfc8)
		self.totalAmountLabel = _Label(
			self.body, TOTAL_RIGHT_X, FOOTER_TEXT_Y,
			"")
		self.totalAmountLabel.SetFontColor(1.0, 1.0, 0.0)
		self.buySelectedButton = _CrimsonButton(
			self.body, 441, BUY_SELECTED_Y, "button/buy",
			self._ConfirmSelectedPurchases,
			_Text("VIRTUAL_MARKET_BUY_SELECTED", "Koupit vybran\u00e9"))
		self.buySelectedButton.Hide()
		self.suggestionDropdown = SearchSuggestionDropdown(
			self, self._SelectSuggestion, SEARCH_INPUT_X, 163)

		self.categoryViewport = ui.Window()
		self.categoryViewport.SetParent(self)
		self.categoryViewport.SetPosition(
			CATEGORY_VIEWPORT_X, CATEGORY_START_Y)
		self.categoryViewport.SetSize(
			CATEGORY_VIEWPORT_WIDTH, CATEGORY_VIEW_HEIGHT)
		self.categoryViewport.SetOnRunMouseWheelEvent(
			self._OnCategoryMouseWheel)
		self.categoryViewport.Show()
		self.filterButtons = []
		self.filterIcons = []
		self.categoryLabels = []
		for index, (localeKey, fallback, iconName, itemType, itemSubtype) in enumerate(MARKET_CATEGORIES):
			button, icon, label = _ClassicTab(
				self.categoryViewport, 0, index * CATEGORY_STEP_Y,
				_Text(localeKey, fallback), iconName,
				lambda selected=index: self._SelectMarketCategory(selected))
			button.SetOnRunMouseWheelEvent(self._OnCategoryMouseWheel)
			self.filterButtons.append(button)
			self.filterIcons.append(icon)
			self.categoryLabels.append(label)
		self.categoryScrollBar = SettingsScrollBar()
		self.categoryScrollBar.SetParent(self)
		self.categoryScrollBar.SetPosition(
			CATEGORY_SCROLL_X, CATEGORY_START_Y)
		self.categoryScrollBar.SetScrollBarSize(CATEGORY_VIEW_HEIGHT)
		self.categoryScrollBar.SetScrollEvent(self._OnCategoryScroll)
		self._RefreshCategoryViewport()

		self.prevButton = _CrimsonIconButton(
			self.body, 168, PAGINATION_Y,
			"button/pagination", self._PreviousPage,
			"icon/arrow_left.png",
			PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.pageButtons = []
		for slotIndex in range(6):
			button = _CrimsonButton(
				self.body, 195 + slotIndex * 27, PAGINATION_Y,
				"button/pagination",
				lambda page=slotIndex: self._GoMarketPage(page),
				"", True)
			self.pageButtons.append(button)
		self.nextButton = _CrimsonIconButton(
			self.body, 357, PAGINATION_Y,
			"button/pagination", self._NextPage,
			"icon/arrow_right.png",
			PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.marketPage = _Label(self.body, 275, PAGINATION_Y + 3, "")
		self.marketPage.SetHorizontalAlignCenter()
		self.marketPage.Hide()

		self.emptyBoard = _Image(
			self.body, 4, 30, CRIMSON_MARKET_DIR + "panel/empty.png")
		self.emptyIcon = _Image(
			self.emptyBoard, 256, 80,
			CRIMSON_MARKET_DIR + "icon/mode_market.png")
		self.emptyTitle = _Label(
			self.emptyBoard, 270, 125, "", 0xfff7c81c)
		self.emptyTitle.SetHorizontalAlignCenter()
		self.emptyHint = _Label(
			self.emptyBoard, 270, 154, "", 0xffeadfc8)
		self.emptyHint.SetHorizontalAlignCenter()
		self.emptyDetail = _Label(
			self.emptyBoard, 270, 177, "", 0xff9e8c7c)
		self.emptyDetail.SetHorizontalAlignCenter()

		self.sidebarMarketWidgets = tuple([
			self.searchBackground, self.searchBoard, self.searchInput,
			self.exactMatchCheck, self.exactMatchLabel,
			self.searchPlayerCheck, self.searchPlayerLabel,
			self.searchButton, self.filterIconButton, self.searchResetButton,
			self.categoryTitle, self.allCategoriesButton,
			self.categoryViewport])
		self.marketWidgets = tuple([
			self.searchTitle, self.marketFooter,
			self.selectionCountLabel, self.totalPrefixLabel,
			self.totalAmountLabel,
			self.buySelectedButton, self.prevButton, self.nextButton,
			self.marketPage, self.emptyBoard] + self.pageButtons)

		self.headerBoard = _Image(
			self.body, 4, 0,
			CRIMSON_MARKET_DIR + "surface/data_header.png")
		itemHeader = _Label(
			self.headerBoard, ITEM_COLUMN_CENTER_X, HEADER_TEXT_CENTER_Y,
			_Text("VIRTUAL_MARKET_ITEM", "P\u0158EDM\u011aT"), 0xffeadfc8)
		itemHeader.SetHorizontalAlignCenter()
		itemHeader.SetVerticalAlignCenter()
		countHeader = _Label(
			self.headerBoard, COUNT_CENTER_X, HEADER_TEXT_CENTER_Y,
			_Text("VIRTUAL_MARKET_COUNT", "PO\u010cET"), 0xffeadfc8)
		countHeader.SetHorizontalAlignCenter()
		countHeader.SetVerticalAlignCenter()
		priceHeader = _Label(
			self.headerBoard, PRICE_COLUMN_CENTER_X, HEADER_TEXT_CENTER_Y,
			_Text("VIRTUAL_MARKET_PRICE", "CENA"), 0xffeadfc8)
		priceHeader.SetHorizontalAlignCenter()
		priceHeader.SetVerticalAlignCenter()
		sellerHeader = _Label(
			self.headerBoard, SELLER_CENTER_X, HEADER_TEXT_CENTER_Y,
			_Text("VIRTUAL_MARKET_SELLER", "HR\u00c1\u010c"), 0xffeadfc8)
		sellerHeader.SetHorizontalAlignCenter()
		sellerHeader.SetVerticalAlignCenter()
		self.headers = (
			self.headerBoard, itemHeader, countHeader,
			priceHeader, sellerHeader)

	def _BuildOwner(self):
		self.ownerHeader = _Container(self.body, ACCOUNT_PANEL_X, ACCOUNT_HEADER_Y, ACCOUNT_PANEL_WIDTH, ACCOUNT_HEADER_HEIGHT)
		self.ownerHeaderSurface = _Image(self.ownerHeader, 0, 0, CRIMSON_MARKET_DIR + "surface/account_header.png")
		self.ownerTitle = _Label(self.ownerHeader, 12, 14, _Text("VIRTUAL_MARKET_OWNER_TITLE", "Můj obchod"), 0xffeadfc8)
		self.ownerTitle.SetVerticalAlignCenter()
		self.ownerState = _Label(self.ownerHeader, 94, 14, "", 0xffd0d0d0)
		self.ownerState.SetVerticalAlignCenter()
		self.ownerLease = _Label(self.ownerHeader, 525, 14, "", 0xffd0d0d0)
		self.ownerLease.SetHorizontalAlignRight()
		self.ownerLease.SetVerticalAlignCenter()
		self.ownerCounts = _Label(self.ownerHeader, 525, 14, "", 0xff9e8c7c)
		self.ownerCounts.Hide()

		self.ownerGridPanel = _Container(self.body, ACCOUNT_PANEL_X, ACCOUNT_CONTENT_Y, ACCOUNT_PANEL_WIDTH, ACCOUNT_CONTENT_HEIGHT)
		self.ownerToolbar = _Image(self.ownerGridPanel, ACCOUNT_TOOLBAR_LOCAL_X, ACCOUNT_TOOLBAR_LOCAL_Y, CRIMSON_MARKET_DIR + "panel/account_toolbar.png")
		self.ownerCreditField = _Image(self.ownerGridPanel, 14, 8, CRIMSON_MARKET_DIR + "field/account_value.png")
		self.ownerCreditPrefix = _Label(self.ownerGridPanel, 18, 19, _Text("VIRTUAL_MARKET_UNCLAIMED_YANG", "Nevyzvednuto: "), 0xffeadfc8)
		self.ownerCreditPrefix.SetVerticalAlignCenter()
		self.ownerCredit = _Label(self.ownerGridPanel, 104, 19, "", 0xffeadfc8)
		self.ownerCredit.SetFontColor(*CURRENCY_YANG_COLOR)
		self.ownerCredit.SetVerticalAlignCenter()
		self.ownerPrevButton = _CrimsonIconButton(self.ownerGridPanel, ACCOUNT_PREV_X, ACCOUNT_PAGE_Y, "button/pagination", self._PreviousPage, "icon/arrow_left.png", PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.ownerNextButton = _CrimsonIconButton(self.ownerGridPanel, ACCOUNT_NEXT_X, ACCOUNT_PAGE_Y, "button/pagination", self._NextPage, "icon/arrow_right.png", PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.ownerPage = _Label(self.ownerGridPanel, ACCOUNT_PAGE_CENTER_X, 19, "", 0xffeadfc8)
		self.ownerPage.SetHorizontalAlignCenter()
		self.ownerPage.SetVerticalAlignCenter()
		self.withdrawButton = _AccountActionButton(self.ownerGridPanel, OWNER_ACTION_START_X, "withdraw_proceeds", self._Withdraw, _Text("VIRTUAL_MARKET_WITHDRAW", "Vyzvednout Yangy"))
		self.renewButton = _AccountActionButton(self.ownerGridPanel, OWNER_ACTION_START_X + ACCOUNT_ACTION_SIZE + ACCOUNT_ACTION_GAP, "extend_shop", self._RenewShop, _Text("VIRTUAL_MARKET_RENEW", "Prodloužit obchod na 5 dní"))
		self.ownerRepriceButton = _AccountActionButton(self.ownerGridPanel, OWNER_ACTION_START_X + 2 * (ACCOUNT_ACTION_SIZE + ACCOUNT_ACTION_GAP), "shop_history", self._RepriceSelectedListing, _Text("VIRTUAL_MARKET_REPRICE", "Změnit cenu vybrané nabídky"), False)
		self.ownerCancelButton = _AccountActionButton(self.ownerGridPanel, OWNER_ACTION_START_X + 3 * (ACCOUNT_ACTION_SIZE + ACCOUNT_ACTION_GAP), "claim_item", self._CancelSelectedListing, _Text("VIRTUAL_MARKET_CANCEL_LISTING", "Odebrat vybranou nabídku do Vrácené"), False)
		self.closeButton = _AccountActionButton(self.ownerGridPanel, OWNER_ACTION_START_X + 4 * (ACCOUNT_ACTION_SIZE + ACCOUNT_ACTION_GAP), "close_shop", self._ConfirmClose, _Text("VIRTUAL_MARKET_CLOSE", "Uzavřít obchod"))

		self.ownerGrid = ui.GridSlotWindow()
		self.ownerGrid.SetParent(self.ownerGridPanel)
		self.ownerGrid.SetPosition(ACCOUNT_GRID_X, ACCOUNT_GRID_Y)
		self.ownerGrid.ArrangeSlot(0, GRID_COLUMNS, GRID_ROWS, 32, 32, 0, 0)
		self.ownerGrid.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		self.ownerGrid.SetSelectEmptySlotEvent(self._AttachOffer)
		self.ownerGrid.SetSelectItemSlotEvent(self._SelectOwnerSlot)
		self.ownerGrid.SetUnselectItemSlotEvent(self._UseOwnerSlot)
		self.ownerGrid.SetOverInItemEvent(self._OverInOwnerSlot)
		self.ownerGrid.SetOverOutItemEvent(self._HideTooltip)
		self.ownerGrid.SetOverInEvent(self._OverInOwnerSlot)
		self.ownerGrid.SetOverOutEvent(self._HideTooltip)
		self.ownerGrid.Show()

		self.ownerValueStrip = _Image(self.ownerGridPanel, ACCOUNT_TOOLBAR_LOCAL_X, ACCOUNT_VALUE_STRIP_Y, CRIMSON_MARKET_DIR + "panel/account_toolbar.png")
		self.ownerTotalPrefix = _Label(self.ownerGridPanel, 90, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2, _Text("VIRTUAL_MARKET_TOTAL_LISTING_VALUE", "Celková hodnota nabídek: "), 0xffeadfc8)
		self.ownerTotalPrefix.SetVerticalAlignCenter()
		self.ownerTotalValue = _Label(self.ownerGridPanel, 250, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2, _YangText(0), 0xffeadfc8)
		self.ownerTotalValue.SetFontColor(*CURRENCY_YANG_COLOR)
		self.ownerTotalValue.SetVerticalAlignCenter()
		_CenterAccountValuePair(self.ownerTotalPrefix, self.ownerTotalValue, ACCOUNT_PAGE_CENTER_X, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2)

		self.ownerClosedPanel = _Image(self.body, ACCOUNT_PANEL_X, ACCOUNT_CONTENT_Y, CRIMSON_MARKET_DIR + "panel/closed_shop.png")
		self.ownerClosedTitle = _Label(self.ownerClosedPanel, 271, 75, _Text("VIRTUAL_MARKET_CLOSED_TITLE", "Váš obchod zatím není otevřen"), 0xffffd500)
		self.ownerClosedTitle.SetHorizontalAlignCenter()
		self.ownerClosedHint = _Label(self.ownerClosedPanel, 271, 104, _Text("VIRTUAL_MARKET_CLOSED_HINT", "Zvolte název a založte virtuální obchod na pět dní."), 0xffeadfc8)
		self.ownerClosedHint.SetHorizontalAlignCenter()
		self.nameBackground = _Image(
			self.ownerClosedPanel, 191, 151,
			OFFLINE_SHOP_UI_PATH + "shop_value_bg.png")
		self.nameBoard = _Container(self.ownerClosedPanel, 191, 151, 161, 33)
		self.nameInput = ui.EditLine()
		self.nameInput.SetParent(self.nameBoard)
		self.nameInput.SetPosition(8, 8)
		self.nameInput.SetSize(145, 18)
		self.nameInput.SetMax(24)
		self.nameInput.SetEscapeEvent(self.OnPressEscapeKey)
		self.nameInput.Show()
		self.createButton = _CrimsonPrimaryButton(
			self.ownerClosedPanel, CREATE_BUTTON_X, 205,
			_Text("VIRTUAL_MARKET_CREATE", "Založit na 5 dní"), self._CreateShop)

		self.ownerListingActions = (self.ownerToolbar, self.ownerCreditField, self.ownerCreditPrefix, self.ownerCredit, self.ownerPrevButton, self.ownerNextButton, self.ownerPage, self.withdrawButton, self.renewButton, self.ownerRepriceButton, self.ownerCancelButton, self.closeButton, self.ownerGrid, self.ownerValueStrip, self.ownerTotalPrefix, self.ownerTotalValue)
		self.ownerActiveToolbarWidgets = (self.ownerCreditField, self.ownerCreditPrefix, self.ownerCredit, self.ownerPrevButton, self.ownerNextButton, self.ownerPage, self.withdrawButton, self.renewButton, self.ownerRepriceButton, self.ownerCancelButton, self.closeButton)
		self.ownerWidgets = (self.ownerHeader, self.ownerGridPanel, self.ownerClosedPanel)

	def _BuildBox(self):
		self.boxHeader = _Container(self.body, ACCOUNT_PANEL_X, ACCOUNT_HEADER_Y, ACCOUNT_PANEL_WIDTH, ACCOUNT_HEADER_HEIGHT)
		self.boxHeaderSurface = _Image(self.boxHeader, 0, 0, CRIMSON_MARKET_DIR + "surface/account_header.png")
		self.boxTitle = _Label(self.boxHeader, 12, 14, "", 0xffeadfc8)
		self.boxTitle.SetVerticalAlignCenter()
		self.boxGridPanel = _Container(self.body, ACCOUNT_PANEL_X, ACCOUNT_CONTENT_Y, ACCOUNT_PANEL_WIDTH, ACCOUNT_CONTENT_HEIGHT)
		self.boxToolbar = _Image(self.boxGridPanel, ACCOUNT_TOOLBAR_LOCAL_X, ACCOUNT_TOOLBAR_LOCAL_Y, CRIMSON_MARKET_DIR + "panel/account_toolbar.png")
		self.boxCount = _Label(self.boxGridPanel, 18, 19, "", 0xffeadfc8)
		self.boxCount.SetVerticalAlignCenter()
		self.boxPage = _Label(self.boxGridPanel, ACCOUNT_PAGE_CENTER_X, 19, "", 0xffeadfc8)
		self.boxPage.SetHorizontalAlignCenter()
		self.boxPage.SetVerticalAlignCenter()
		self.boxPrevButton = _CrimsonIconButton(self.boxGridPanel, ACCOUNT_PREV_X, ACCOUNT_PAGE_Y, "button/pagination", self._PreviousPage, "icon/arrow_left.png", PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.boxNextButton = _CrimsonIconButton(self.boxGridPanel, ACCOUNT_NEXT_X, ACCOUNT_PAGE_Y, "button/pagination", self._NextPage, "icon/arrow_right.png", PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.boxClaimAllButton = _AccountActionButton(self.boxGridPanel, DELIVERY_ACTION_START_X, "claim_all", self._ClaimAll, _Text("VIRTUAL_MARKET_CLAIM_ALL", "Vyzvednout všechny předměty"), False)
		self.returnWithdrawButton = _AccountActionButton(self.boxGridPanel, RETURN_ACTION_START_X, "withdraw_proceeds", self._Withdraw, _Text("VIRTUAL_MARKET_WITHDRAW_RETURNS", "Vyzvednout vrácené Yangy"))
		self.returnWithdrawButton.Hide()

		self.boxGrid = ui.GridSlotWindow()
		self.boxGrid.SetParent(self.boxGridPanel)
		self.boxGrid.SetPosition(ACCOUNT_GRID_X, ACCOUNT_GRID_Y)
		self.boxGrid.ArrangeSlot(0, GRID_COLUMNS, GRID_ROWS, 32, 32, 0, 0)
		self.boxGrid.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		self.boxGrid.SetUnselectItemSlotEvent(self._UseBoxSlot)
		self.boxGrid.SetUnselectEmptySlotEvent(self._UseBoxSlot)
		self.boxGrid.SetOverInItemEvent(self._OverInBoxSlot)
		self.boxGrid.SetOverOutItemEvent(self._HideTooltip)
		self.boxGrid.SetOverInEvent(self._OverInBoxSlot)
		self.boxGrid.SetOverOutEvent(self._HideTooltip)
		self.boxGrid.Show()
		self.boxWidgets = (self.boxHeader, self.boxGridPanel)

	def Destroy(self):
		self._StopClaimAll()
		self._CancelOwnerDrag()
		self._ClearRows()
		self._HideTooltip()
		if getattr(self, "advancedFilters", None):
			self.advancedFilters.Destroy()
		self.confirmEvent = None
		self.retryEvent = None
		self.confirm = None
		self.priceDialog = None
		self.interface = None
		self.tabs = ()
		self.tabIcons = ()
		self.tabLabels = ()
		self.tabIconNames = ()
		self.tabAccents = ()
		self.filterButtons = ()
		self.filterIcons = ()
		self.categoryLabels = ()
		self.categoryViewport = None
		self.categoryScrollBar = None
		self.gridPages = ()
		self.gridSlotMap = {}
		self.headers = ()
		self.sidebarMarketWidgets = ()
		self.marketWidgets = ()
		self.suggestionDropdown = None
		self.advancedFilters = None
		self.ownerWidgets = ()
		self.ownerListingActions = ()
		self.boxWidgets = ()
		self.Hide()

	def Open(self, loadMarket=True):
		# loadMarket=False is for callers that immediately send their own
		# search (the Ctrl+click shortcut). A default browse in the same frame
		# would consume the server's per-player search rate limit.
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		if loadMarket:
			self._SelectTab(self.currentTab, True)
		else:
			self._SelectTab(TAB_MARKET, True, False)
		if self.currentTab != TAB_OWNER:
			net.SendVirtualMarketOwnerShop()
		self.SetFocus()

	def OpenSeller(self, sellerName):
		sellerName = str(sellerName).strip()
		if not sellerName:
			return False
		if not self.IsShow():
			self.SetCenterPosition()
		self.Show()
		self.SetTop()
		self._SearchSeller(sellerName)
		net.SendVirtualMarketOwnerShop()
		self.SetFocus()
		return True

	def CaptureWarpState(self):
		return {
			"current_tab": int(self.currentTab),
			"search_mode": str(self.searchMode),
			"search_text": str(self.searchInput.GetText()),
			"seller_exact": bool(self.sellerExact),
			"market_searched": bool(self.marketSearched),
			"last_search_vnum": int(self.lastSearchVnum),
			"last_search_type": self.lastSearchType,
			"last_search_vnums": list(self.lastSearchVnums),
			"last_seller_name": str(self.lastSellerName),
			"last_seller_exact": bool(self.lastSellerExact),
			"last_search_v3": self.lastSearchV3,
			"last_item_name": self.lastItemName,
			"last_item_exact": self.lastItemExact,
			"advanced_filters": self.advancedFilters.GetFilters(),
			"category_start": int(self.categoryStartIndex),
			"pinned_search": self.pinnedSearch,
		}

	def RestoreWarpState(self, state):
		if not isinstance(state, dict):
			state = {}

		searchMode = state.get("search_mode", "item")
		if searchMode not in ("item", "seller"):
			searchMode = "item"
		self._SetSearchMode(searchMode)
		self.searchInput.SetText(str(state.get("search_text", "")))
		self.sellerExact = bool(state.get("seller_exact", False))
		self.exactMatchCheck.Down() if self.sellerExact else \
			self.exactMatchCheck.SetUp()
		self.advancedFilters.SetFilters(state.get("advanced_filters"))
		self.lastItemName = str(state.get("last_item_name", ""))
		self.lastItemExact = bool(state.get("last_item_exact", False))
		self.pinnedSearch = None
		pinned = state.get("pinned_search")
		if isinstance(pinned, (tuple, list)) and len(pinned) == 2:
			try:
				pinnedVnum = int(pinned[1])
			except (TypeError, ValueError):
				pinnedVnum = 0
			if pinned[0] and 0 < pinnedVnum <= 0xffffffff:
				self.pinnedSearch = (str(pinned[0]), pinnedVnum)

		self.lastSearchVnum = max(
			0, int(state.get("last_search_vnum", 0)))
		searchType = state.get("last_search_type")
		if isinstance(searchType, (tuple, list)) and len(searchType) == 2:
			self.lastSearchType = (int(searchType[0]), int(searchType[1]))
		else:
			self.lastSearchType = None

		self.lastSearchVnums = []
		searchVnums = state.get("last_search_vnums", [])
		if isinstance(searchVnums, (tuple, list)):
			for searchVnum in searchVnums:
				try:
					searchVnum = int(searchVnum)
				except (TypeError, ValueError):
					continue
				if searchVnum > 0:
					self.lastSearchVnums.append(searchVnum)
				if len(self.lastSearchVnums) >= 32:
					break

		self.lastSellerName = str(state.get("last_seller_name", ""))
		self.lastSellerExact = bool(
			state.get("last_seller_exact", False))

		searchV3 = state.get("last_search_v3")
		if isinstance(searchV3, (tuple, list)) and len(searchV3) == 5:
			self.lastSearchV3 = (
				list(searchV3[0]),
				str(searchV3[1]),
				bool(searchV3[2]),
				int(searchV3[3]),
				int(searchV3[4]),
			)
		else:
			self.lastSearchV3 = None

		self.marketSearched = bool(state.get("market_searched", False))
		self.categoryStartIndex = max(
			0, int(state.get("category_start", 0)))
		self._RefreshCategoryViewport()
		self._SyncMarketCategory()

		tab = int(state.get("current_tab", TAB_MARKET))
		if tab not in (TAB_MARKET, TAB_OWNER, TAB_DELIVERIES, TAB_RETURNS):
			tab = TAB_MARKET
		self._ClearPurchaseSelection()
		self.SetTop()
		self.Show()
		self._SelectTab(tab, True, False)
		if tab == TAB_MARKET:
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m nab\u00eddky..."),
				_Text("VIRTUAL_MARKET_LOADING_HINT",
					"Vyhled\u00e1v\u00e1m ve virtu\u00e1ln\u00edm trhu."))
			if self.marketSearched:
				if not self._RepeatMarketSearch():
					self._SetStatus(_Text(
						"VIRTUAL_MARKET_REQUEST_BUSY",
						"Po\u017eadavek nyn\u00ed nelze odeslat."),
						self._RepeatMarketSearch)
				else:
					self._SetStatus(_Text(
						"VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m..."))
			else:
				self._BrowseMarket()
		if tab != TAB_OWNER:
			net.SendVirtualMarketOwnerShop()
		self.SetFocus()
		return True

	def Close(self):
		self._StopClaimAll()
		self._CancelOwnerDrag()
		self.searchRetryAt = 0.0
		self.searchRetryEvent = None
		self.repricingListingId = 0
		self.priceDialog.SetTitle(_Text(
			"PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE", "Prodejn\u00ed cena"))
		self.searchInput.KillFocus()
		self.nameInput.KillFocus()
		self.KillFocus()
		self.confirm.Hide()
		self.priceDialog.Hide()
		self.suggestionDropdown.Close()
		self.advancedFilters.Close()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def _SetWidgetsVisible(self, widgets, visible):
		for widget in widgets:
			if visible:
				widget.Show()
			else:
				widget.Hide()

	def _SelectTab(self, tab, force=False, loadMarket=True):
		if not force and self.currentTab == tab:
			if tab == TAB_MARKET and loadMarket:
				self._BrowseMarket()
			return
		if self.currentTab == TAB_OWNER and tab != TAB_OWNER:
			self._CancelOwnerDrag()
		self._StopClaimAll()
		self.currentTab = tab
		self._RefreshTabVisuals()
		self.currentPage = 0
		self.advanceAfterAppend = False
		self.boxStateSignature = None
		self._ClearRows()
		self.suggestionDropdown.Close()
		self._SetWidgetsVisible(self.sidebarMarketWidgets, True)
		self._SetWidgetsVisible(self.marketWidgets, tab == TAB_MARKET)
		self._RefreshCategoryViewport()
		self._RefreshPurchaseSelection()
		self._SetWidgetsVisible(self.headers, False)
		self._SetWidgetsVisible(self.ownerWidgets, tab == TAB_OWNER)
		self._SetWidgetsVisible(self.boxWidgets, tab in (TAB_DELIVERIES, TAB_RETURNS))
		self._SetStatus("")

		if tab == TAB_MARKET:
			# loadMarket=False: the caller sends its own search next. Never fall
			# through to the account-box branches below.
			if not loadMarket:
				pass
			elif self.marketSearched:
				self._RefreshMarket()
				if not self._RepeatMarketSearch():
					self._SetStatus(_Text("VIRTUAL_MARKET_REQUEST_BUSY",
						"Trh se nyní nepodařilo obnovit."), self._RepeatMarketSearch)
			else:
				self._BrowseMarket()
		elif tab == TAB_OWNER:
			net.SendVirtualMarketOwnerShop()
			if hasattr(net, "SendVirtualMarketOwnerListings"):
				net.SendVirtualMarketOwnerListings()
			self._RefreshOwner(True)
		elif tab == TAB_DELIVERIES:
			self.boxTitleBase = _Text("VIRTUAL_MARKET_DELIVERIES_TITLE", "Doru\u010den\u00e9 n\u00e1kupy")
			self.boxTitle.SetText(self.boxTitleBase)
			net.SendVirtualMarketBuyerDeliveries()
			self._RefreshBox()
		else:
			self.boxTitleBase = _Text("VIRTUAL_MARKET_RETURNS_TITLE", "Vr\u00e1cen\u00e9 polo\u017eky")
			self.boxTitle.SetText(self.boxTitleBase)
			net.SendVirtualMarketSellerReturns()
			self._RefreshBox()

	def _RefreshTabVisuals(self):
		for index, button in enumerate(self.tabs):
			if index == self.currentTab:
				button.Down()
			else:
				button.SetUp()

	def _GetOperationRetry(self):
		# The native bridge owns the unresolved operation and its replay identity.
		# Snapshot callbacks and tab changes must not discard its recovery action.
		for operation, sender in (
			("ShopCommand", "SendVirtualMarketShopRetry"),
			("ItemClaim", "SendVirtualMarketItemClaimRetry"),
			("ListingCreate", "SendVirtualMarketListingCreateRetry"),
			("ListingMove", "SendVirtualMarketListingMoveRetry"),
			("ListingMutation", "SendVirtualMarketListingMutationRetry"),
			("Purchase", "SendVirtualMarketPurchaseRetry"),
			("BatchPurchase", "SendVirtualMarketBatchPurchaseRetry"),
			("SellerWithdrawal", "SendVirtualMarketSellerWithdrawalRetry"),
		):
			canRetry = getattr(virtualmarket, "CanRetry" + operation, None)
			retry = getattr(net, sender, None)
			if canRetry and retry and canRetry():
				return retry
		return None

	def _SetStatus(self, text, retryEvent=None):
		operationRetry = self._GetOperationRetry()
		if operationRetry:
			if retryEvent != operationRetry or not text:
				text = _Text("VIRTUAL_MARKET_RETRY_REQUIRED",
					"Dokončete předchozí operaci tlačítkem Zkusit znovu.")
			retryEvent = operationRetry
		self.status.SetText(text)
		if text:
			self.sidebarLine2.Hide()
			self.status.Show()
		else:
			self.status.Hide()
			self.sidebarLine2.Hide()
		self.retryEvent = retryEvent
		if retryEvent:
			self.retryButton.Show()
		else:
			self.retryButton.Hide()

	def _Retry(self):
		operationRetry = self._GetOperationRetry()
		if operationRetry:
			# Use the existing native retry, never issue a fresh mutation or Clear().
			if operationRetry():
				self._SetStatus(_Text("VIRTUAL_MARKET_RETRYING",
					"Čekám na dokončení předchozí operace..."))
			else:
				self._SetStatus("")
		elif self.retryEvent:
			self.retryEvent()

	def _ClearRows(self):
		for row in self.rows:
			row.Destroy()
		self.rows = []

	def _ClearPurchaseSelection(self):
		self.selectedPurchases = {}
		self._RefreshPurchaseSelection()

	def _RefreshPurchaseSelection(self):
		count = len(self.selectedPurchases)
		total = sum(int(value[2]) for value in self.selectedPurchases.values())
		self.selectionCountLabel.SetText("Vybráno: %d / 20" % count)
		self.totalPrefixLabel.SetText("Celkem: ")
		self.totalAmountLabel.SetText(_YangText(total))
		_RightAlignLabelPair(
			self.totalPrefixLabel, self.totalAmountLabel, TOTAL_RIGHT_X)
		self.sidebarLine2.Hide()
		if self.currentTab == TAB_MARKET:
			self.marketFooter.Show()
			self.selectionCountLabel.Show()
			if self.status.IsShow():
				self.totalPrefixLabel.Hide()
				self.totalAmountLabel.Hide()
			else:
				self.totalPrefixLabel.Show()
				self.totalAmountLabel.Show()
			if count:
				self.buySelectedButton.Show()
			else:
				self.buySelectedButton.Hide()
		else:
			self.marketFooter.Hide()
			self.selectionCountLabel.Hide()
			self.totalPrefixLabel.Hide()
			self.totalAmountLabel.Hide()
			self.buySelectedButton.Hide()

	def _SetMarketEmptyState(self, title, hint, detail=""):
		if self.currentTab != TAB_MARKET:
			return
		self._SetWidgetsVisible(self.headers, False)
		self.prevButton.Hide()
		self.nextButton.Hide()
		self.marketPage.Hide()
		for button in self.pageButtons:
			button.Hide()
		self.emptyTitle.SetText(title)
		self.emptyHint.SetText(hint)
		self.emptyDetail.SetText(detail)
		self.emptyBoard.Show()

	def _SetMarketResultsState(self, count):
		self.emptyBoard.Hide()
		self._SetWidgetsVisible(self.headers, True)
		self._RefreshMarketPagination(count)

	def _RefreshMarketPagination(self, count):
		pageCount = max(1, len(self.marketPages))
		visibleCount = min(6, pageCount)
		firstPage = max(0, min(
			self.currentPage - visibleCount // 2,
			pageCount - visibleCount))
		self.prevButton.Show()
		self.nextButton.Show()
		self.prevButton.Enable() if self.currentPage > 0 else self.prevButton.Disable()
		self.nextButton.Enable() if (
			self.currentPage + 1 < pageCount or bool(virtualmarket.HasMore())
		) else self.nextButton.Disable()
		for slotIndex, button in enumerate(self.pageButtons):
			pageIndex = firstPage + slotIndex
			if slotIndex >= visibleCount:
				button.Hide()
				continue
			button.SetText(str(pageIndex + 1))
			button.SetEvent(self._GoMarketPage, pageIndex)
			button.Show()
			button.Down() if pageIndex == self.currentPage else button.SetUp()
		self.marketPage.Hide()

	def _GoMarketPage(self, pageIndex):
		pageCount = len(self.marketPages)
		if pageIndex < 0 or pageIndex >= pageCount:
			return
		self.currentPage = pageIndex
		self._RefreshMarket()

	def _ClearMarketCategory(self):
		for button in self.filterButtons:
			button.SetUp()

	def _ShowAllMarketCategories(self):
		self.advancedFilters.SelectCategory(0)
		self._SyncMarketCategory()
		self._Search()

	def _SyncMarketCategory(self):
		category = self.advancedFilters.GetFilters().get("category", 0)
		self._ClearMarketCategory()
		self.lastSearchType = None
		if category in MARKET_CATEGORY_IDS:
			index = MARKET_CATEGORY_IDS.index(category)
			self.filterButtons[index].Down()
			searchType = tuple(MARKET_CATEGORIES[index][3:5])
			self.lastSearchType = searchType if searchType[0] >= 0 else None

	def _ResetMarketSearch(self):
		self.advancedFilters.Reset()
		self.searchMode = "item"
		self.searchPlayerCheck.SetUp()
		self._SetExactMatch(False)
		self.searchInput.SetText("")
		self.pinnedSearch = None
		self.searchInput.SetInfoMessage(_Text(
			"VIRTUAL_MARKET_VNUM_PLACEHOLDER", "N\u00e1zev nebo VNUM"))
		self.lastSuggestionText = ""
		self.pendingSuggestionText = ""
		self.suggestionDropdown.Close()
		if self.currentTab != TAB_MARKET:
			self._SelectTab(TAB_MARKET, loadMarket=False)
		self._Search()

	def _VisibleCategoryIndexes(self):
		otherAvailable = _OtherCategoryAvailable()
		return [index for index in range(len(self.filterButtons))
			if MARKET_CATEGORY_IDS[index] != MARKET_CATEGORY_OTHER or otherAvailable]

	def _RefreshCategoryViewport(self):
		visible = self._VisibleCategoryIndexes()
		count = len(visible)
		maxStart = max(0, count - CATEGORY_VISIBLE_COUNT)
		self.categoryStartIndex = min(
			max(0, self.categoryStartIndex), maxStart)
		for button in self.filterButtons:
			button.Hide()
		for position, index in enumerate(visible):
			button = self.filterButtons[index]
			row = position - self.categoryStartIndex
			if 0 <= row < CATEGORY_VISIBLE_COUNT:
				button.SetPosition(0, row * CATEGORY_STEP_Y)
				button.Show()
		if maxStart:
			self.categoryScrollBar.SetMiddleBarSize(float(CATEGORY_VISIBLE_COUNT) / count)
			self.categoryScrollBar.SetScrollStep(1.0 / float(maxStart))
			self.categoryScrollBar.Show()
		else:
			self.categoryScrollBar.SetPos(0.0)
			self.categoryScrollBar.Hide()

	def _OnCategoryScroll(self):
		maxStart = max(
			0, len(self._VisibleCategoryIndexes()) - CATEGORY_VISIBLE_COUNT)
		if not maxStart:
			return
		startIndex = int(
			self.categoryScrollBar.GetPos() * maxStart + 0.5)
		if startIndex == self.categoryStartIndex:
			return
		self.categoryStartIndex = startIndex
		self._RefreshCategoryViewport()

	def _OnCategoryMouseWheel(self, scrollDown):
		maxStart = max(
			0, len(self._VisibleCategoryIndexes()) - CATEGORY_VISIBLE_COUNT)
		if not maxStart:
			return
		step = 1.0 / float(maxStart)
		position = self.categoryScrollBar.GetPos()
		self.categoryScrollBar.SetPos(
			position + step if scrollDown else position - step)

	def _SetExactMatch(self, enabled):
		self.sellerExact = bool(enabled)
		self.exactMatchCheck.Down() if self.sellerExact else self.exactMatchCheck.SetUp()

	def _SetSearchMode(self, mode):
		if mode not in ("item", "seller"):
			return
		self.searchMode = mode
		self.pinnedSearch = None
		if mode == "seller":
			self.searchPlayerCheck.Down()
		else:
			self.searchPlayerCheck.SetUp()
		self.searchInput.SetText("")
		self.searchInput.SetInfoMessage(
			_Text("VIRTUAL_MARKET_VNUM_PLACEHOLDER", "N\u00e1zev nebo VNUM")
			if mode == "item" else
			_Text("VIRTUAL_MARKET_SELLER_PLACEHOLDER", "Jm\u00e9no hr\u00e1\u010de"))
		self.lastSuggestionText = ""
		self.pendingSuggestionText = ""
		self.suggestionDropdown.Close()
		self.searchInput.SetFocus()

	def _OnSearchIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchInput)
		self.searchChangedAt = app.GetTime()

	def _SelectSuggestion(self, name):
		self.searchInput.SetText(name)
		self.lastSuggestionText = name
		self._SetExactMatch(True)
		self._Search()

	def _UpdateSearchSuggestions(self):
		if not self.IsShow():
			return
		text = self.searchInput.GetText().strip()
		if text == self.lastSuggestionText or app.GetTime() - self.searchChangedAt < 0.25:
			return
		if len(text) < 2:
			self.lastSuggestionText = text
			self.suggestionDropdown.Close()
			return
		if self.searchMode == "item":
			try:
				names = _SortSuggestions(list(
					item.GetItemNamesByName(text, SEARCH_SUGGESTION_LIMIT)))
			except:
				names = []
			self.lastSuggestionText = text
			self.suggestionDropdown.Open(names)
			return
		if getattr(virtualmarket, "AreSellerSuggestionsLoading", lambda: 0)():
			return
		if net.SendVirtualMarketSellerSuggestions(text):
			self.lastSuggestionText = text
			self.pendingSuggestionText = text

	def _SelectMarketCategory(self, index):
		if index < 0 or index >= len(MARKET_CATEGORIES):
			return
		if MARKET_CATEGORY_IDS[index] == MARKET_CATEGORY_OTHER and \
				not _OtherCategoryAvailable():
			return
		self.advancedFilters.SelectCategory(MARKET_CATEGORY_IDS[index])
		self._SyncMarketCategory()
		self._Search()

	def _BrowseMarket(self):
		browse = getattr(net, "SendVirtualMarketBrowse", None)
		if not browse:
			# Keep the root pack safe while an older executable is still being
			# replaced. The compatible x64 client enters the indexed browse below.
			self._RefreshMarket()
			return False
		self.advancedFilters.SelectCategory(0)
		self.lastItemName = ""
		self.lastItemExact = False
		self.lastSearchVnum = 0
		self.lastSearchType = None
		self.lastSearchVnums = []
		self.lastSellerName = ""
		self.lastSellerExact = False
		self.marketSearched = True
		self.currentPage = 0
		self.advanceAfterAppend = False
		self._ClearMarketCategory()
		self._ClearRows()
		self._SetMarketEmptyState(
			_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m nab\u00eddky..."),
			_Text("VIRTUAL_MARKET_LOADING_HINT", "Vyhled\u00e1v\u00e1m ve virtu\u00e1ln\u00edm trhu."))
		if not self._SendMarketSearch([], "", False, -1, -1):
			self.marketSearched = False
			self._SetStatus(_Text("VIRTUAL_MARKET_REQUEST_BUSY", "Po\u017eadavek nyn\u00ed nelze odeslat."),
				self._BrowseMarket)
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_REQUEST_FAILED", "Po\u017eadavek se neodeslal"),
				_Text("VIRTUAL_MARKET_REQUEST_FAILED_HINT", "Po\u010dkejte chv\u00edli a zkuste trh obnovit."))
			return False
		self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m..."))
		return True

	def _RepeatMarketSearch(self):
		if self.lastSearchV3:
			return self._SendMarketSearch(*self.lastSearchV3)
		if self.lastSearchVnums or self.lastSellerName:
			return net.SendVirtualMarketSearchV2(self.lastSearchVnums,
				self.lastSellerName, int(self.lastSellerExact))
		if self.lastSearchVnum:
			return net.SendVirtualMarketSearchByVnum(self.lastSearchVnum)
		if self.lastSearchType:
			return net.SendVirtualMarketSearchByType(*self.lastSearchType)
		return getattr(net, "SendVirtualMarketBrowse", lambda: False)()

	def _Search(self):
		text = self.searchInput.GetText().strip()
		self.suggestionDropdown.Close()
		name = ""
		pinned = self.pinnedSearch
		if pinned and (self.searchMode != "item" or text != pinned[0]):
			pinned = self.pinnedSearch = None
		if self.searchMode == "seller":
			vnums = []
			sellerName = text
			sellerExact = self.sellerExact
		elif pinned:
			# The field shows the localized name; the shortcut's exact VNUM
			# remains the query until the player edits the text.
			vnums, sellerName, sellerExact = [pinned[1]], "", False
		elif text.isdigit():
			if not 0 < int(text) <= 0xffffffff:
				self._SetStatus("Zadej platné VNUM předmětu.")
				return
			vnums, sellerName, sellerExact = [int(text)], "", False
		else:
			vnums, sellerName, sellerExact = [], "", False
			name = text
			if len(name.encode("utf-8")) > 64:
				self._SetStatus("Zkrať název předmětu pro vyhledání.")
				return
			if name and not getattr(net, "IsVirtualMarketSearchV4Available", lambda: False)():
				vnums = self._ResolveSearchVnums(name)
				if not vnums:
					self._SetStatus("Zadej platný název nebo VNUM předmětu.")
					return
		self.lastItemName = name
		self.lastItemExact = bool(name and self.sellerExact)
		if self.currentTab != TAB_MARKET:
			self._SelectTab(TAB_MARKET, loadMarket=False)
		self.lastSearchVnum = vnums[0] if len(vnums) == 1 else 0
		self.lastSearchVnums = list(vnums)
		self.lastSellerName = sellerName
		self.lastSellerExact = sellerExact
		self.marketSearched = True
		self._SyncMarketCategory()
		self.currentPage = 0
		self.advanceAfterAppend = False
		self._ClearRows()
		self._SetMarketEmptyState(
			_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m nab\u00eddky..."),
			_Text("VIRTUAL_MARKET_LOADING_HINT", "Vyhled\u00e1v\u00e1m ve virtu\u00e1ln\u00edm trhu."))
		if not self._SendMarketSearch(vnums, sellerName, sellerExact, *(self.lastSearchType or (-1, -1))):
			self._SetStatus(_Text("VIRTUAL_MARKET_REQUEST_BUSY", "Po\u017eadavek nyn\u00ed nelze odeslat."))
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_REQUEST_FAILED", "Po\u017eadavek se neodeslal"),
				_Text("VIRTUAL_MARKET_REQUEST_FAILED_HINT", "Po\u010dkejte chv\u00edli a zkuste hled\u00e1n\u00ed znovu."))
		else:
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m..."))

	def _OpenAdvancedFilters(self):
		if not getattr(net, "IsVirtualMarketSearchV4Available", lambda: False)():
			self._SetStatus("Rozšířené filtry čekají na aktualizaci serveru.")
			return
		self.suggestionDropdown.Close()
		self.advancedFilters.Open()

	def _ApplyAdvancedFilters(self):
		self._SyncMarketCategory()
		self._Search()

	def _SendMarketSearch(self, vnums, sellerName, sellerExact, itemType, itemSubtype):
		self._ClearPurchaseSelection()
		self._ArmSearchRetry(self._RepeatMarketSearch)
		self.lastSearchV3 = (list(vnums), str(sellerName), bool(sellerExact),
			int(itemType), int(itemSubtype))
		if getattr(net, "IsVirtualMarketSearchV4Available", lambda: False)():
			arguments = self.advancedFilters.GetArguments(vnums, sellerName, sellerExact,
				self.lastItemName, self.lastItemExact)
			return bool(net.SendVirtualMarketSearchV4(*arguments))
		if self.advancedFilters.IsActive():
			return False
		search = getattr(net, "SendVirtualMarketSearchV3", None)
		if search:
			return bool(search(list(vnums), str(sellerName), int(bool(sellerExact)),
				int(itemType), int(itemSubtype), -1, -1, 0, 0, -1, -1, []))
		if itemType >= 0:
			return bool(net.SendVirtualMarketSearchByType(itemType, itemSubtype))
		if vnums or sellerName:
			return bool(net.SendVirtualMarketSearchV2(vnums, sellerName, int(bool(sellerExact))))
		return bool(getattr(net, "SendVirtualMarketBrowse", lambda: False)())

	def SearchExactVnum(self, vnum):
		vnum = int(vnum)
		if vnum <= 0:
			return False
		if self.currentTab != TAB_MARKET:
			self._SelectTab(TAB_MARKET, loadMarket=False)
		self.advancedFilters.SelectCategory(0)
		self._SyncMarketCategory()
		self._SetSearchMode("item")
		name = self._SearchDisplayName(vnum)
		self.searchInput.SetText(name or str(vnum))
		self.pinnedSearch = (name, vnum) if name else None
		# Do not open item-name suggestions for the text set by the shortcut.
		self.lastSuggestionText = self.searchInput.GetText().strip()
		self.suggestionDropdown.Close()
		self._Search()
		return True

	def _SearchDisplayName(self, vnum):
		try:
			item.SelectItem(int(vnum))
			name = str(item.GetItemName()).strip()
		except:
			return ""
		if not name or name.isdigit() or len(name.encode("utf-8")) > 64:
			return ""
		return name

	def _ArmSearchRetry(self, event):
		# One automatic retry per player request; the retry never re-arms.
		self.searchRetryAt = 0.0
		if not self.searchRetryInProgress:
			self.searchRetryEvent = event

	def _RetryNextMarketPage(self):
		self.advanceAfterAppend = True
		return bool(net.SendVirtualMarketSearchNextPage())

	def _RunSearchRetry(self):
		event = self.searchRetryEvent
		self.searchRetryAt = 0.0
		self.searchRetryEvent = None
		if not event or self.currentTab != TAB_MARKET:
			return False
		self.searchRetryInProgress = True
		try:
			sent = bool(event())
		finally:
			self.searchRetryInProgress = False
		if not sent:
			self._SetStatus(self._StatusError(virtualmarket.STATUS_RATE_LIMITED),
				self._RepeatMarketSearch)
		return sent

	def _ResolveSearchVnums(self, text):
		if not text:
			return []
		if text.isdigit():
			return [int(text)] if int(text) > 0 else []
		if not hasattr(item, "GetItemsByName"):
			return []
		try:
			matches = item.GetItemsByName(text, 32)
		except:
			return []
		if not matches:
			return []
		return sorted(set(int(candidate) for candidate in matches if int(candidate) > 0))[:32]

	def _RefreshMarketLayout(self, count):
		if count < self.marketLayoutCount:
			self.marketPages = []
			self.marketLayoutCount = 0
		if count > self.marketLayoutCount:
			heights = [_ItemHeight(virtualmarket.GetListingVnum(index))
				for index in range(self.marketLayoutCount, count)]
			self.marketPages.extend(marketlayout.PackRows(
				heights, MARKET_ROWS_HEIGHT, self.marketLayoutCount))
			self.marketLayoutCount = count

	def _RefreshMarket(self):
		if self.currentTab != TAB_MARKET:
			return
		self._ClearRows()
		if not self.marketSearched:
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_WELCOME", "Trh je p\u0159ipraven"),
				_Text("VIRTUAL_MARKET_WELCOME_HINT", "Pou\u017eijte kategorii nebo zadejte n\u00e1zev / VNUM."),
				_Text("VIRTUAL_MARKET_WELCOME_DETAIL", "Pro v\u00fdpis v\u0161ech nab\u00eddek aktualizujte klienta."))
			return
		count = int(virtualmarket.GetListingCount())
		if count == 0:
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_NO_RESULTS", "\u017d\u00e1dn\u00e9 nab\u00eddky"),
				_Text("VIRTUAL_MARKET_NO_RESULTS_HINT", "Tomuto v\u00fdb\u011bru te\u010f neodpov\u00edd\u00e1 \u017e\u00e1dn\u00e1 nab\u00eddka."),
				_Text("VIRTUAL_MARKET_NO_RESULTS_DETAIL", "Zkuste jinou kategorii, n\u00e1zev nebo VNUM."))
			return
		self._RefreshMarketLayout(count)
		self.currentPage = min(self.currentPage, len(self.marketPages) - 1)
		self._SetMarketResultsState(count)
		for index, rowY in self.marketPages[self.currentPage]:
			vnum = int(virtualmarket.GetListingVnum(index))
			itemCount = int(virtualmarket.GetListingCountValue(index))
			price = int(virtualmarket.GetListingPrice(index))
			expiresAt = int(virtualmarket.GetListingEndTime(index))
			listingId = int(virtualmarket.GetListingId(index))
			sellerName = getattr(virtualmarket, "GetListingSellerName", lambda unused: "")(index)
			payload = (listingId, vnum, price)
			selected = listingId in self.selectedPurchases
			self.rows.append(CrimsonMarketRow(self.body, MARKET_ROWS_Y + rowY,
				vnum, itemCount, _Money(price), _Remaining(expiresAt), sellerName,
				(_Text("VIRTUAL_MARKET_UNSELECT", "Zrušit") if selected else
					_Text("VIRTUAL_MARKET_SELECT", "Vybrat")) if self.batchPurchaseAvailable else
					_Text("VIRTUAL_MARKET_BUY", "Koupit"),
				self._TogglePurchaseSelection if self.batchPurchaseAvailable else
					self._ConfirmPurchase, payload,
				self._MessageSeller,
				lambda selected=index, cost=price: self._ShowTooltip("listing", selected, cost),
				self._HideTooltip, (sellerName, index),
				self._SearchSeller, sellerName, selected=selected,
				selectionMode=self.batchPurchaseAvailable))

	def _SearchSeller(self, sellerName):
		sellerName = str(sellerName).strip()
		if not sellerName:
			return
		if self.currentTab != TAB_MARKET:
			self._SelectTab(TAB_MARKET, loadMarket=False)
		self.advancedFilters.SelectCategory(0)
		self._SetSearchMode("seller")
		self.searchInput.SetText(sellerName)
		self._SetExactMatch(True)
		self._Search()

	def _MessageSeller(self, payload):
		sellerName, index = payload
		if not sellerName:
			return
		itemLink = _ListingItemLink(index)
		if not itemLink:
			itemLink = _ItemName(int(virtualmarket.GetListingVnum(index)))
		if hasattr(self.interface, "OpenWhisperWithMarketItem"):
			self.interface.OpenWhisperWithMarketItem(sellerName, itemLink)
		else:
			self.interface.OpenWhisperDialog(sellerName)

	def _PreviousPage(self):
		if self.currentPage <= 0:
			return
		self.currentPage -= 1
		if self.currentTab == TAB_MARKET:
			self._RefreshMarket()
		elif self.currentTab == TAB_OWNER:
			self._RefreshOwnerGrid()
		else:
			self._RefreshBox()

	def _NextPage(self):
		if self.currentTab == TAB_MARKET:
			hasMore = bool(virtualmarket.HasMore())
			nextRequest = net.SendVirtualMarketSearchNextPage
			localPageCount = len(self.marketPages)
		elif self.currentTab == TAB_OWNER:
			localPageCount = len(self.gridPages)
			hasMore = bool(getattr(virtualmarket, "OwnerListingsHasMore", lambda: 0)())
			nextRequest = getattr(net, "SendVirtualMarketOwnerListingsNextPage", lambda: False)
		elif self.currentTab == TAB_DELIVERIES:
			localPageCount = len(self.gridPages)
			hasMore = bool(virtualmarket.BuyerDeliveriesHasMore())
			nextRequest = net.SendVirtualMarketBuyerDeliveriesNextPage
		else:
			localPageCount = len(self.gridPages)
			hasMore = bool(virtualmarket.SellerReturnsHasMore())
			nextRequest = net.SendVirtualMarketSellerReturnsNextPage

		if self.currentPage + 1 < localPageCount:
			self.currentPage += 1
			if self.currentTab == TAB_MARKET:
				self._RefreshMarket()
			elif self.currentTab == TAB_OWNER:
				self._RefreshOwnerGrid()
			else:
				self._RefreshBox()
			return
		if self.currentTab == TAB_MARKET and hasMore:
			self._ArmSearchRetry(self._RetryNextMarketPage)
		if hasMore and nextRequest():
			self.advanceAfterAppend = True
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m..."))

	def _ConfirmPurchase(self, payload):
		listingId, vnum, price = payload
		self.confirmEvent = lambda: self._Purchase(listingId, vnum, price)
		self.confirm.SetText(_Text("VIRTUAL_MARKET_BUY_CONFIRM", "Koupit %s za %s?") %
			(_ItemName(vnum), _Money(price)))
		self.confirm.SetAcceptEvent(self._AcceptConfirm)
		self.confirm.Open()

	def _TogglePurchaseSelection(self, payload, selected):
		listingId = int(payload[0])
		if selected:
			if listingId in self.selectedPurchases:
				return True
			elif len(self.selectedPurchases) < 20:
				self.selectedPurchases[listingId] = tuple(payload)
			else:
				self._SetStatus(_Text("VIRTUAL_MARKET_BATCH_LIMIT",
					"Najednou lze koupit nejvýše 20 položek."))
				return False
		else:
			if listingId not in self.selectedPurchases:
				return False
			del self.selectedPurchases[listingId]
		self._RefreshPurchaseSelection()
		return listingId in self.selectedPurchases

	def _ConfirmSelectedPurchases(self):
		items = sorted(self.selectedPurchases.values(), key=lambda value: int(value[0]))
		if not items:
			return
		if len(items) == 1:
			self._ConfirmPurchase(items[0])
			return
		total = sum(int(value[2]) for value in items)
		self.confirmEvent = lambda selected=list(items): self._PurchaseSelected(selected)
		self.confirm.SetText(_Text("VIRTUAL_MARKET_BATCH_CONFIRM",
			"Koupit %d položek celkem za %s? Vše proběhne najednou.") %
			(len(items), _Money(total)))
		self.confirm.SetAcceptEvent(self._AcceptConfirm)
		self.confirm.Open()

	def _PurchaseSelected(self, items):
		send = getattr(net, "SendVirtualMarketBatchPurchase", None)
		if send and send([(int(value[0]), int(value[1]), int(value[2])) for value in items]):
			self._SetStatus(_Text("VIRTUAL_MARKET_BATCH_PURCHASING",
				"Probíhá atomický nákup vybraných položek..."))

	def _Purchase(self, listingId, vnum, price):
		if net.SendVirtualMarketPurchase(listingId, vnum, price):
			self._SetStatus(_Text("VIRTUAL_MARKET_PURCHASING", "Prob\u00edh\u00e1 atomick\u00fd n\u00e1kup..."))

	def _AcceptConfirm(self):
		self.confirm.Hide()
		event = self.confirmEvent
		self.confirmEvent = None
		if event:
			event()

	def _CancelConfirm(self):
		self.confirmEvent = None
		self.confirm.Hide()

	def _RefreshOwner(self, refreshGrid=False):
		if self.currentTab != TAB_OWNER:
			return
		exists, state, closeReason, expiresAt, listedItems, pendingReturns, activeSellers, availableCredit = virtualmarket.GetOwnerShop()
		self._UpdateSidebarSellers(activeSellers)
		exists = bool(exists)
		isOpen = exists and int(state) == 0
		isSuspended = exists and int(state) == 2
		if isOpen:
			stateText = _Text("VIRTUAL_MARKET_OWNER_OPEN", "• otevřen")
			stateColor = OWNER_STATE_OPEN_COLOR
		elif isSuspended:
			stateText = _Text("VIRTUAL_MARKET_OWNER_SUSPENDED", "• pozastaven")
			stateColor = OWNER_STATE_SUSPENDED_COLOR
		else:
			stateText = _Text("VIRTUAL_MARKET_OWNER_CLOSED", "• zavřen")
			stateColor = OWNER_STATE_CLOSED_COLOR
		self.ownerState.SetText(stateText)
		self.ownerState.SetFontColor(*stateColor)
		self.ownerLease.SetText((_Text("VIRTUAL_MARKET_OWNER_LEASE", "Uzavření za %s") % _Remaining(expiresAt)) if isOpen else "")
		self.ownerCounts.SetText(_Text("VIRTUAL_MARKET_OWNER_COUNTS", "Nabídky: %d   Vrácené: %d") % (int(listedItems), int(pendingReturns)))
		self.ownerCredit.SetText(_YangText(availableCredit))
		self.ownerCredit.SetFontColor(*CURRENCY_YANG_COLOR)
		_CenterAccountValuePair(self.ownerCreditPrefix, self.ownerCredit, 109, 19)
		canCreate = not exists or int(state) == 1
		self.ownerShopOpen = bool(isOpen)
		self.ownerGridPanel.Show() if isOpen else self.ownerGridPanel.Hide()
		self.ownerClosedPanel.Show() if canCreate or isSuspended else self.ownerClosedPanel.Hide()
		self.createButton.Show() if canCreate else self.createButton.Hide()
		self.nameBackground.Show() if canCreate else self.nameBackground.Hide()
		self.nameBoard.Show() if canCreate else self.nameBoard.Hide()
		self.nameInput.Show() if canCreate else self.nameInput.Hide()
		self._SetWidgetsVisible(self.ownerActiveToolbarWidgets, isOpen)
		if isSuspended:
			self.ownerClosedTitle.SetText(_Text("VIRTUAL_MARKET_SUSPENDED_TITLE", "Obchod je pozastaven správcem"))
			self.ownerClosedHint.SetText(_Text("VIRTUAL_MARKET_SUSPENDED_HINT", "Nabídky zůstávají v bezpečném escrow; kontaktujte podporu."))
		else:
			self.ownerClosedTitle.SetText(_Text("VIRTUAL_MARKET_CLOSED_TITLE", "Váš obchod zatím není otevřen"))
			self.ownerClosedHint.SetText(_Text("VIRTUAL_MARKET_CLOSED_HINT", "Zvolte název a založte virtuální obchod na pět dní."))
		_SetAccountActionAvailable(self.withdrawButton, int(availableCredit) > 0)
		if refreshGrid and isOpen:
			self._RefreshOwnerGrid()

	def _RefreshOwnerGrid(self):
		if self.currentTab != TAB_OWNER:
			return
		self.ownerTotalPrefix.SetText(_Text(
			"VIRTUAL_MARKET_TOTAL_LISTING_VALUE", "Celková hodnota nabídek: "))
		_ClearGridItems(self.ownerGrid)
		self.gridSlotMap = {}
		totalListingValue = 0
		if not hasattr(virtualmarket, "GetOwnerListingCount"):
			self._ClearOwnerSelection()
			self.gridPages = [[]]
			self.ownerPage.SetText("1 / 1")
			self.ownerTotalValue.SetText(_YangText(totalListingValue))
			self.ownerTotalValue.SetFontColor(*CURRENCY_YANG_COLOR)
			_CenterAccountValuePair(self.ownerTotalPrefix, self.ownerTotalValue, ACCOUNT_PAGE_CENTER_X, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2)
			self.ownerPrevButton.Hide()
			self.ownerNextButton.Hide()
			return
		records = []
		selectedRecord = None
		maxPage = 0
		for index in range(int(virtualmarket.GetOwnerListingCount())):
			listingId, vnum, itemCount, price, itemType, itemSubtype, expiresAt, displaySlot, itemSize = virtualmarket.GetOwnerListingInfo(index)
			listingId = int(listingId)
			vnum = int(vnum)
			displaySlot = int(displaySlot)
			itemSize = max(1, min(GRID_ROWS, int(itemSize)))
			totalListingValue += int(price)
			records.append((
				displaySlot,
				(
					listingId, int(index), vnum, int(itemCount),
					int(price), int(expiresAt), itemSize,
				),
			))
			if listingId == self.selectedOwnerListingId:
				selectedRecord = (listingId, vnum, int(itemCount), int(price))
			maxPage = max(maxPage, displaySlot // GRID_SLOT_COUNT)
		self.ownerTotalValue.SetText(_YangText(totalListingValue))
		self.ownerTotalValue.SetFontColor(*CURRENCY_YANG_COLOR)
		_CenterAccountValuePair(self.ownerTotalPrefix, self.ownerTotalValue, ACCOUNT_PAGE_CENTER_X, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2)
		hasMore = bool(virtualmarket.OwnerListingsHasMore())
		pageCount = maxPage + 1
		if records and pageCount < int(getattr(virtualmarket, "LAYOUT_MAXIMUM_PAGES", 64)):
			pageCount += 1
		self.gridPages = [[] for unused in range(max(1, pageCount))]
		for displaySlot, payload in records:
			page = displaySlot // GRID_SLOT_COUNT
			if page < len(self.gridPages):
				self.gridPages[page].append((displaySlot % GRID_SLOT_COUNT, payload))
		for page in self.gridPages:
			page.sort(key=lambda row: row[0])
		self.currentPage = min(self.currentPage, max(0, len(self.gridPages) - 1))
		for packed in self.gridPages[self.currentPage]:
			slotIndex, payload = packed
			listingId, nativeIndex, vnum, itemCount, price, expiresAt, itemSize = payload
			self.ownerGrid.SetItemSlot(slotIndex, vnum, itemCount)
			entry = (
				"owner", int(nativeIndex), int(price), int(listingId),
				int(vnum), int(itemCount), int(itemSize),
				self.currentPage * GRID_SLOT_COUNT + int(slotIndex),
			)
			_MapGridItemFootprint(
				self.gridSlotMap, slotIndex, itemSize, entry)
		self.ownerGrid.RefreshSlot()
		self.ownerPage.SetText("%d / %d" % (
			self.currentPage + 1, max(1, len(self.gridPages))))
		self.ownerPrevButton.Show() if self.currentPage > 0 else self.ownerPrevButton.Hide()
		self.ownerNextButton.Show() if self.currentPage + 1 < len(self.gridPages) or hasMore else self.ownerNextButton.Hide()
		if selectedRecord:
			self._SetOwnerSelection(*selectedRecord)
		else:
			self._ClearOwnerSelection()

	def _OwnerOccupiedCells(self, excludedListingId=0):
		occupied = set()
		if not hasattr(virtualmarket, "GetOwnerListingCount"):
			return occupied
		for index in range(int(virtualmarket.GetOwnerListingCount())):
			info = virtualmarket.GetOwnerListingInfo(index)
			if int(info[0]) == int(excludedListingId):
				continue
			position = int(info[7])
			height = max(1, min(GRID_ROWS, int(info[8])))
			for offset in range(height):
				occupied.add(position + offset * GRID_COLUMNS)
		return occupied

	def _CanPlaceOwnerListing(self, position, height, excludedListingId=0):
		position = int(position)
		height = max(1, min(GRID_ROWS, int(height)))
		maximumPages = int(getattr(virtualmarket, "LAYOUT_MAXIMUM_PAGES", 64))
		if position < 0 or position >= maximumPages * GRID_SLOT_COUNT:
			return False
		localSlot = position % GRID_SLOT_COUNT
		if localSlot // GRID_COLUMNS + height > GRID_ROWS:
			return False
		occupied = self._OwnerOccupiedCells(excludedListingId)
		for offset in range(height):
			if position + offset * GRID_COLUMNS in occupied:
				return False
		return True

	def _IsOwnerDrag(self):
		return self.ownerDragListingId > 0 and mouseModule.mouseController.isAttached()

	def _CancelOwnerDrag(self):
		if self._IsOwnerDrag():
			mouseModule.mouseController.DeattachObject()
		self.ownerDragListingId = 0
		self.ownerDragHeight = 1
		self.ownerDragOriginalPosition = -1

	def _SetOwnerSelection(self, listingId, vnum, count, price):
		self.selectedOwnerListingId = int(listingId)
		self.selectedOwnerVnum = int(vnum)
		self.selectedOwnerCount = int(count)
		self.selectedOwnerListingPrice = int(price)
		_SetAccountActionAvailable(
			self.ownerRepriceButton,
			hasattr(net, "SendVirtualMarketListingReprice"))
		_SetAccountActionAvailable(
			self.ownerCancelButton,
			hasattr(net, "SendVirtualMarketListingCancel"))

	def _ClearOwnerSelection(self):
		self.selectedOwnerListingId = 0
		self.selectedOwnerVnum = 0
		self.selectedOwnerCount = 0
		self.selectedOwnerListingPrice = 0
		_SetAccountActionAvailable(self.ownerRepriceButton, False)
		_SetAccountActionAvailable(self.ownerCancelButton, False)

	def _DropOwnerListing(self, slotIndex):
		if not self._IsOwnerDrag():
			return
		targetPosition = self.currentPage * GRID_SLOT_COUNT + int(slotIndex)
		listingId = int(self.ownerDragListingId)
		height = int(self.ownerDragHeight)
		originalPosition = int(self.ownerDragOriginalPosition)
		if targetPosition == originalPosition:
			self._CancelOwnerDrag()
			return
		if not self._CanPlaceOwnerListing(targetPosition, height, listingId):
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_SLOT_DOES_NOT_FIT",
				"P\u0159edm\u011bt se do zvolen\u00e9ho m\u00edsta nevejde."))
			self._CancelOwnerDrag()
			return
		sent = bool(getattr(
			net, "SendVirtualMarketListingMove", lambda listing, slot: False)(
				listingId, targetPosition))
		self._CancelOwnerDrag()
		if sent:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_MOVING",
				"P\u0159esouv\u00e1m nab\u00eddku do zvolen\u00e9ho slotu..."))
		else:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_REQUEST_BUSY",
				"Po\u017eadavek nyn\u00ed nelze odeslat."))

	def _SelectOwnerSlot(self, slotIndex):
		if self._IsOwnerDrag():
			self._DropOwnerListing(slotIndex)
			return
		entry = self.gridSlotMap.get(int(slotIndex))
		if not entry or entry[0] != "owner":
			return
		if mouseModule.mouseController.isAttached():
			return
		info = virtualmarket.GetOwnerListingInfo(entry[1])
		self._SetOwnerSelection(entry[3], entry[4], entry[5], entry[2])
		self.ownerDragListingId = int(entry[3])
		self.ownerDragHeight = int(entry[6])
		self.ownerDragOriginalPosition = int(entry[7])
		mouseModule.mouseController.AttachObject(
			self, player.SLOT_TYPE_PRIVATE_SHOP, int(slotIndex),
			int(entry[4]), int(entry[5]))
		self._SetStatus(_Text("VIRTUAL_MARKET_OWNER_SELECTED",
			"P\u0159et\u00e1hn\u011bte %s do voln\u00e9ho slotu. Cena %s, zb\u00fdv\u00e1 %s") %
			(_ItemName(info[1]), _Money(info[3]), _Remaining(info[6])))

	def _UseOwnerSlot(self, slotIndex):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			return self._OpenOwnerReprice(slotIndex)
		return self._OpenOwnerCancel(slotIndex)

	def _OpenOwnerReprice(self, slotIndex):
		entry = self.gridSlotMap.get(int(slotIndex))
		if not entry or entry[0] != "owner":
			return
		self._SetOwnerSelection(entry[3], entry[4], entry[5], entry[2])
		self._RepriceSelectedListing()

	def _OpenOwnerCancel(self, slotIndex):
		entry = self.gridSlotMap.get(int(slotIndex))
		if not entry or entry[0] != "owner":
			return
		self._CancelListing(int(entry[3]))

	def _RepriceSelectedListing(self):
		if self.selectedOwnerListingId <= 0:
			return
		self._CancelOwnerDrag()
		self.offer = None
		self.repricingListingId = int(self.selectedOwnerListingId)
		self.repricingItem = (int(self.selectedOwnerVnum), int(self.selectedOwnerCount))
		self.priceDialog.SetTitle(_Text(
			"VIRTUAL_MARKET_REPRICE_TITLE", "Nov\u00e1 prodejn\u00ed cena"))
		self.priceDialog.SetContext(self.selectedOwnerCount,
			bool(getattr(net, "IsVirtualMarketBulkPriceAvailable", lambda: False)()))
		self.priceDialog.Open()
		self.priceDialog.SetValue(self.selectedOwnerListingPrice)

	def _CancelSelectedListing(self):
		if self.selectedOwnerListingId > 0:
			self._CancelListing(int(self.selectedOwnerListingId))

	def _CancelListing(self, listingId):
		self._CancelOwnerDrag()
		self._HideTooltip()
		send = getattr(net, "SendVirtualMarketListingCancel", None)
		if send and send(int(listingId)):
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_CANCELING_LISTING",
				"Odeb\u00edr\u00e1m nab\u00eddku a p\u0159esouv\u00e1m item do Vr\u00e1cen\u00e9..."))
			return
		self._SetStatus(_Text(
			"VIRTUAL_MARKET_REQUEST_BUSY",
			"Po\u017eadavek nyn\u00ed nelze odeslat."))

	def _OverInOwnerSlot(self, slotIndex):
		entry = self.gridSlotMap.get(int(slotIndex))
		if entry and entry[0] == "owner":
			self._ShowTooltip("owner", entry[1], entry[2])

	def _UpdateSidebarSellers(self, activeSellers=None):
		if activeSellers is None:
			try:
				activeSellers = virtualmarket.GetOwnerShop()[6]
			except:
				return
		self.sidebarLine2.SetText(_Text("VIRTUAL_MARKET_ACTIVE_SELLERS_SHORT",
			"Aktivn\u00ed prodejci: %d") % int(activeSellers))

	def _CreateShop(self):
		name = self.nameInput.GetText().strip()
		if len(name) < 2:
			self._SetStatus(_Text("VIRTUAL_MARKET_NAME_REQUIRED", "Zadejte n\u00e1zev obchodu."))
			return
		if net.SendVirtualMarketShopCreate(name):
			self._SetStatus(_Text("VIRTUAL_MARKET_CREATING", "Zakl\u00e1d\u00e1m obchod na 5 dn\u00ed..."))

	def _RenewShop(self):
		if net.SendVirtualMarketShopRenew():
			self._SetStatus(_Text("VIRTUAL_MARKET_RENEWING", "Nastavuji nov\u00fd deadline na 5 dn\u00ed odte\u010f..."))

	def _ConfirmClose(self):
		self.confirmEvent = self._CloseShop
		self.confirm.SetText(_Text("VIRTUAL_MARKET_CLOSE_CONFIRM",
			"Uzav\u0159\u00edt obchod a p\u0159esunout neprodan\u00e9 itemy do Vr\u00e1cen\u00e9?"))
		self.confirm.SetAcceptEvent(self._AcceptConfirm)
		self.confirm.Open()

	def _CloseShop(self):
		if net.SendVirtualMarketShopClose():
			self._SetStatus(_Text("VIRTUAL_MARKET_CLOSING", "Bezpe\u010dn\u011b uzav\u00edr\u00e1m obchod..."))

	def _Withdraw(self):
		if net.SendVirtualMarketSellerWithdrawal():
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAWING", "Vyb\u00edr\u00e1m dostupn\u00fd v\u00fdt\u011b\u017eek..."))

	def _AttachOffer(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return
		if not self.ownerShopOpen:
			return
		if self._IsOwnerDrag():
			self._DropOwnerListing(slotIndex)
			return
		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotIndex = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		inventoryType = player.SlotTypeToInvenType(attachedSlotType)
		if inventoryType == player.INVENTORY and player.IsEquipmentSlot(attachedSlotIndex):
			self._SetStatus(_Text("VIRTUAL_MARKET_UNEQUIP_FIRST", "Nejprve item sundejte."))
			return
		try:
			vnum = int(player.GetItemIndex(inventoryType, attachedSlotIndex))
			count = int(player.GetItemCount(inventoryType, attachedSlotIndex))
		except:
			return
		if vnum <= 0 or count <= 0:
			return
		item.SelectItem(vnum)
		if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
			self._SetStatus(_Text("PRIVATE_SHOP_CANNOT_SELL_ITEM", "Tento item nelze prodat."))
			return
		height = _ItemHeight(vnum)
		targetPosition = self.currentPage * GRID_SLOT_COUNT + int(slotIndex)
		if not self._CanPlaceOwnerListing(targetPosition, height):
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_SLOT_DOES_NOT_FIT",
				"P\u0159edm\u011bt se do zvolen\u00e9ho m\u00edsta nevejde."))
			return
		self.offer = (
			int(inventoryType), int(attachedSlotIndex), count, vnum,
			targetPosition, height,
		)
		available = getattr(net, "IsVirtualMarketPriceMemoryAvailable", lambda: False)
		# Native cache entry point: virtualmarket.GetPricePreference
		getPreference = getattr(virtualmarket, "GetPricePreference", None)
		if not available() or not getPreference:
			self._OpenOfferPriceDialog(0)
			return
		cached, found, previousPrice, previousCount = getPreference(vnum)
		if cached:
			suggestedPrice = _ScaleRememberedPrice(
				previousPrice, previousCount, count) if found else 0
			self._OpenOfferPriceDialog(suggestedPrice)
			return
		send = getattr(net, "SendVirtualMarketPricePreference", None)
		if not send or not net.SendVirtualMarketPricePreference(vnum):
			self._OpenOfferPriceDialog(0)

	def _OpenOfferPriceDialog(self, suggestedPrice):
		self.priceDialog.SetContext(self.offer[2] if self.offer else 1)
		self.priceDialog.Open()
		# ALTHEA-622: without a remembered price the field stays empty so the
		# seller types the price directly instead of deleting a preset 0.
		if int(suggestedPrice or 0) > 0:
			self.priceDialog.SetValue(int(suggestedPrice))

	def OnPricePreferenceResult(self, token, status, vnum, found,
			totalPrice, itemCount):
		if not self.offer or int(self.offer[3]) != int(vnum):
			return
		if int(status) == virtualmarket.STATUS_OK and bool(found):
			suggestedPrice = _ScaleRememberedPrice(
				totalPrice, itemCount, self.offer[2]) or 0
			self._OpenOfferPriceDialog(suggestedPrice)
		else:
			self._OpenOfferPriceDialog(0)

	def _ClearOffer(self, slotIndex=0):
		self.offer = None

	def _AcceptOfferPrice(self):
		if self.repricingListingId > 0:
			price = int(self.priceDialog.GetValue())
			if price <= 0 or price > 10000000000:
				self._SetStatus(_Text("VIRTUAL_MARKET_PRICE_RANGE", "Cena musí být od 1 do 10 000 000 000 Yang."))
				return True
			listingId = int(self.repricingListingId)
			vnum, count = self.repricingItem
			matching = self.priceDialog.IsMatching()
			self.repricingListingId = 0
			self.priceDialog.Hide()
			self.priceDialog.SetTitle(_Text(
				"PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE", "Prodejn\u00ed cena"))
			send = getattr(net, "SendVirtualMarketListingReprice", None)
			if matching:
				send = getattr(net, "SendVirtualMarketListingRepriceMatching", None)
			if send and send(listingId, price):
				self.pendingReprice = (listingId, vnum, count, price)
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_REPRICING_LISTING",
					"M\u011bn\u00edm cenu nab\u00eddky..."))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_REQUEST_BUSY",
					"Po\u017eadavek nyn\u00ed nelze odeslat."))
			return True
		if not self.offer:
			self.priceDialog.Hide()
			return True
		price = int(self.priceDialog.GetValue())
		if price <= 0 or price > 10000000000:
			self._SetStatus(_Text("VIRTUAL_MARKET_PRICE_RANGE", "Cena musí být od 1 do 10 000 000 000 Yang."))
			return True
		windowType, position, count, vnum, targetPosition, height = self.offer
		self.priceDialog.Hide()
		if net.SendVirtualMarketListingCreate(
				windowType, position, count, price, vnum, targetPosition):
			self.pendingListingCreate = (int(vnum), int(count), int(price))
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_CREATING",
				"P\u0159esouv\u00e1m item do tr\u017en\u00edho escrow..."))
		return True

	def _CancelOfferPrice(self):
		self.priceDialog.Hide()
		self.priceDialog.SetTitle(_Text(
			"PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE", "Prodejn\u00ed cena"))
		self.repricingListingId = 0
		self._ClearOffer()
		return True

	def _RefreshBox(self):
		if self.currentTab not in (TAB_DELIVERIES, TAB_RETURNS):
			return
		_ClearGridItems(self.boxGrid)
		self.gridSlotMap = {}
		if self.currentTab == TAB_DELIVERIES:
			count = int(virtualmarket.GetBuyerDeliveryCount())
			getter = virtualmarket.GetBuyerDeliveryInfo
			self.returnWithdrawButton.Hide()
			self.boxClaimAllButton.SetPosition(DELIVERY_ACTION_START_X, 4)
		else:
			count = int(virtualmarket.GetSellerReturnCount())
			getter = virtualmarket.GetSellerReturnInfo
			self.returnWithdrawButton.Show()
			self.boxClaimAllButton.SetPosition(RETURN_ACTION_START_X + ACCOUNT_ACTION_SIZE + ACCOUNT_ACTION_GAP, 4)
			try:
				credit = int(virtualmarket.GetOwnerShop()[7])
			except:
				credit = 0
			_SetAccountActionAvailable(self.returnWithdrawButton, credit > 0)
		# Pending clicks affect presentation only; native escrow rows remain authoritative.
		pending = set(self.queuedClaims)
		if self.activeClaim is not None:
			pending.add(self.activeClaim)
		records = []
		for index in range(count):
			info = getter(index)
			if self.currentTab == TAB_DELIVERIES:
				sourceId, listingId, vnum, itemCount, price, state, createdAt = info
				source = virtualmarket.CLAIM_SOURCE_DELIVERY
				kind = "delivery"
			else:
				sourceId, vnum, itemCount, reason, state, createdAt = info
				source = virtualmarket.CLAIM_SOURCE_SELLER_RETURN
				price = 0
				kind = "return"
			payload = (int(source), int(sourceId), int(vnum), int(itemCount))
			records.append((index, int(vnum), int(itemCount), kind, int(source), int(sourceId), int(price)))
		count = sum(1 for record in records
			if (record[4], record[5], record[1], record[2]) not in pending)
		self.boxCount.SetText(_Text("VIRTUAL_MARKET_ITEM_COUNT", "%d položek") % count)
		self.gridPages = _PackGridRecords(records)
		self.currentPage = min(self.currentPage, max(0, len(self.gridPages) - 1))
		for packed in self.gridPages[self.currentPage]:
			slotIndex, nativeIndex, vnum, itemCount, kind, source, sourceId, price = packed
			payload = (source, sourceId, vnum, itemCount)
			# Keep neighboring anchors/pages stable until the durable result arrives.
			if payload in pending:
				continue
			self.boxGrid.SetItemSlot(slotIndex, vnum, itemCount)
			entry = (kind, int(nativeIndex), payload, int(price))
			_MapGridItemFootprint(
				self.gridSlotMap, slotIndex, _ItemHeight(vnum), entry)
		self.boxGrid.RefreshSlot()
		self.boxPage.SetText("%d / %d" % (self.currentPage + 1, len(self.gridPages)))
		self.boxGrid.Show()
		self.boxPage.Show() if count else self.boxPage.Hide()
		self.boxPrevButton.Show() if count and self.currentPage > 0 else self.boxPrevButton.Hide()
		hasMore = bool(virtualmarket.BuyerDeliveriesHasMore()) if self.currentTab == TAB_DELIVERIES else bool(virtualmarket.SellerReturnsHasMore())
		self.boxNextButton.Show() if (count and self.currentPage + 1 < len(self.gridPages)) or hasMore else self.boxNextButton.Hide()
		self.boxStateSignature = self._GetBoxStateSignature()
		self._RefreshClaimActions()

	def _GetBoxStateSignature(self):
		if self.currentTab == TAB_DELIVERIES:
			return (TAB_DELIVERIES,
				int(virtualmarket.GetBuyerDeliveryCount()),
				int(virtualmarket.GetBuyerDeliveriesStatus()),
				bool(virtualmarket.IsBuyerDeliveriesLoading()),
				bool(virtualmarket.BuyerDeliveriesHasMore()))
		if self.currentTab == TAB_RETURNS:
			return (TAB_RETURNS,
				int(virtualmarket.GetSellerReturnCount()),
				int(virtualmarket.GetSellerReturnsStatus()),
				bool(virtualmarket.IsSellerReturnsLoading()),
				bool(virtualmarket.SellerReturnsHasMore()))
		return None

	def _RefreshClaimActions(self):
		count = 0
		if self.currentTab == TAB_DELIVERIES:
			count = int(virtualmarket.GetBuyerDeliveryCount())
		elif self.currentTab == TAB_RETURNS:
			count = int(virtualmarket.GetSellerReturnCount())
		claimBusy = bool(getattr(
			virtualmarket, "IsItemClaimLoading", lambda: 0)())
		controller = getattr(self, "claimAllController", None)
		sequenceBusy = bool(controller and controller.IsActive())
		_SetAccountActionAvailable(
			self.boxClaimAllButton,
			count > 0 and not claimBusy and not sequenceBusy and not self.queuedClaims)

	def _UseBoxSlot(self, slotIndex):
		"""Right-click claims one delivery or seller return."""
		if self.claimAllController.IsActive():
			return
		entry = self.gridSlotMap.get(int(slotIndex))
		if not entry or entry[0] not in ("delivery", "return"):
			return
		payload = entry[2]
		if payload == self.activeClaim or payload in self.queuedClaims or len(self.queuedClaims) >= 32:
			return
		self.queuedClaims.append(payload)
		self._HideTooltip()
		self._AdvanceClaims()
		if payload != self.activeClaim:
			self._RefreshBox()
		self._RefreshClaimActions()

	def _RefillEmptyClaimBox(self, source):
		if int(source) == virtualmarket.CLAIM_SOURCE_DELIVERY:
			if not virtualmarket.GetBuyerDeliveryCount() and virtualmarket.BuyerDeliveriesHasMore():
				return net.SendVirtualMarketBuyerDeliveriesNextPage()
		elif int(source) == virtualmarket.CLAIM_SOURCE_SELLER_RETURN:
			if not virtualmarket.GetSellerReturnCount() and virtualmarket.SellerReturnsHasMore():
				return net.SendVirtualMarketSellerReturnsNextPage()
		return False

	def _AdvanceClaims(self):
		if app.GetTime() < self.nextClaimAt or bool(getattr(virtualmarket, "IsItemClaimLoading", lambda: 0)()):
			return
		if not bool(getattr(virtualmarket, "IMMEDIATE_CLAIM_UPDATES", 0)):
			loading = virtualmarket.IsBuyerDeliveriesLoading if self.currentTab == TAB_DELIVERIES else virtualmarket.IsSellerReturnsLoading
			if loading():
				return
		if self.claimAllController.IsActive():
			self._ContinueClaimAll()
			return
		while self.queuedClaims:
			payload = self.queuedClaims.pop(0)
			# Discard double-clicks on a row that an earlier ACK already removed.
			getter = virtualmarket.GetBuyerDeliveryInfo if self.currentTab == TAB_DELIVERIES else virtualmarket.GetSellerReturnInfo
			count = virtualmarket.GetBuyerDeliveryCount() if self.currentTab == TAB_DELIVERIES else virtualmarket.GetSellerReturnCount()
			if any(int(getter(index)[0]) == int(payload[1]) for index in range(int(count))):
				if not self._Claim(payload):
					self.queuedClaims = []
					self._RefreshBox()
				return

	def _FirstBoxClaimPayload(self):
		if self.currentTab == TAB_DELIVERIES:
			if int(virtualmarket.GetBuyerDeliveryCount()) <= 0:
				return None
			info = virtualmarket.GetBuyerDeliveryInfo(0)
			sourceId, listingId, vnum, itemCount, price, state, createdAt = info
			return (int(virtualmarket.CLAIM_SOURCE_DELIVERY),
				int(sourceId), int(vnum), int(itemCount))
		if self.currentTab == TAB_RETURNS:
			if int(virtualmarket.GetSellerReturnCount()) <= 0:
				return None
			info = virtualmarket.GetSellerReturnInfo(0)
			sourceId, vnum, itemCount, reason, state, createdAt = info
			return (int(virtualmarket.CLAIM_SOURCE_SELLER_RETURN),
				int(sourceId), int(vnum), int(itemCount))
		return None

	def _ClaimAll(self):
		if self.currentTab == TAB_DELIVERIES:
			source = virtualmarket.CLAIM_SOURCE_DELIVERY
		elif self.currentTab == TAB_RETURNS:
			source = virtualmarket.CLAIM_SOURCE_SELLER_RETURN
		else:
			return
		if self.claimAllController.IsActive() or self.queuedClaims:
			return
		if bool(getattr(virtualmarket, "IsItemClaimLoading", lambda: 0)()):
			return
		self.claimAllController.Start(source)
		self._RefreshClaimActions()
		self._ContinueClaimAll()

	def _ContinueClaimAll(self):
		if not self.claimAllController.CanBegin() or app.GetTime() < self.nextClaimAt:
			return
		payload = self._FirstBoxClaimPayload()
		if not payload:
			hasMore = virtualmarket.BuyerDeliveriesHasMore() if self.currentTab == TAB_DELIVERIES else virtualmarket.SellerReturnsHasMore()
			if hasMore:
				send = net.SendVirtualMarketBuyerDeliveriesNextPage if self.currentTab == TAB_DELIVERIES else net.SendVirtualMarketSellerReturnsNextPage
				if send():
					self.claimAllController.awaitingRefresh = True
				return
			self._StopClaimAll(_Text(
				"VIRTUAL_MARKET_CLAIM_ALL_DONE",
				"Všechny položky byly vyzvednuty."))
			return
		if not self.claimAllController.Begin(payload):
			self._StopClaimAll()
			return
		if not self._Claim(payload):
			self._StopClaimAll()

	def _StopClaimAll(self, statusText=None):
		self.claimAllController.Stop()
		hadQueued = bool(self.queuedClaims)
		self.queuedClaims = []
		if hadQueued:
			self._RefreshBox()
		self._RefreshClaimActions()
		if statusText is not None:
			self._SetStatus(statusText)

	def _OverInBoxSlot(self, slotIndex):
		entry = self.gridSlotMap.get(int(slotIndex))
		if entry and entry[0] in ("delivery", "return"):
			self._ShowTooltip(entry[0], entry[1], entry[3])

	def _SnapshotGetterPrefix(self, kind):
		return {
			"listing": "GetListing",
			"owner": "GetOwnerListing",
			"delivery": "GetBuyerDelivery",
			"return": "GetSellerReturn",
		}.get(kind)

	def _SnapshotVnum(self, kind, index):
		if kind == "listing":
			return int(virtualmarket.GetListingVnum(index))
		if kind == "owner":
			return int(virtualmarket.GetOwnerListingInfo(index)[1])
		if kind == "delivery":
			return int(virtualmarket.GetBuyerDeliveryInfo(index)[2])
		if kind == "return":
			return int(virtualmarket.GetSellerReturnInfo(index)[1])
		return 0

	def _RarityMetadataKey(self, kind, index):
		context = getattr(net, "RARITY_CONTEXT_MARKET", 6)
		if kind == "listing":
			return (context, getattr(net, "RARITY_MARKET_LISTING", 0), 0, 0,
				int(virtualmarket.GetListingId(index)))
		if kind == "owner":
			return (context, getattr(net, "RARITY_MARKET_LISTING", 0), 0, 0,
				int(virtualmarket.GetOwnerListingInfo(index)[0]))
		if kind == "return":
			return (context, getattr(net, "RARITY_MARKET_RETURN", 1), 0, 0,
				int(virtualmarket.GetSellerReturnInfo(index)[0]))
		if kind == "delivery":
			return (context, getattr(net, "RARITY_MARKET_DELIVERY", 2), 0, 0,
				int(virtualmarket.GetBuyerDeliveryInfo(index)[0]))
		return None

	def _ShowTooltip(self, kind, index, price=0):
		tooltip = getattr(self.interface, "tooltipItem", None)
		prefix = self._SnapshotGetterPrefix(kind)
		if not tooltip or not prefix:
			return
		try:
			vnum = self._SnapshotVnum(kind, index)
			getSocket = getattr(virtualmarket, prefix + "Socket")
			getAttribute = getattr(virtualmarket, prefix + "Attribute")
			sockets = [getSocket(index, value) for value in range(player.METIN_SOCKET_MAX_NUM)]
			# The market snapshot retains the 6th/7th-bonus path as a third
			# protocol field, while the shared tooltip API still consumes
			# classic (type, value) pairs in several code paths.
			attributes = [tuple(getAttribute(index, value))[:2]
				for value in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
			refineElement = None
			if getattr(app, "ENABLE_REFINE_ELEMENT_SYSTEM", 0):
				refineElement = getattr(virtualmarket, prefix + "RefineElement")(index)
			randomApplies = None
			if getattr(app, "ENABLE_APPLY_RANDOM", 0):
				getRandomApply = getattr(virtualmarket, prefix + "RandomApply")
				randomApplies = [tuple(getRandomApply(index, value))[:2]
					for value in range(player.APPLY_RANDOM_SLOT_MAX_NUM)]
			tooltip.ClearToolTip()
			tooltip.AddItemData(vnum, sockets, attributes,
				refine_element=refineElement, apply_random_list=randomApplies,
				rarity_key=self._RarityMetadataKey(kind, index))
			soulbind, transmutation = getattr(virtualmarket, prefix + "Identity")(index)
			if transmutation and hasattr(tooltip, "AppendChangeLookInfoItemVnum"):
				tooltip.AppendChangeLookInfoItemVnum(transmutation)
			if price:
				tooltip.AppendPrice(int(price))
			if kind == "owner":
				tooltip.AutoAppendNewTextLineResize(
					"|Ikey/mouse_left|i - %s" % _Text(
						"VIRTUAL_MARKET_OWNER_SELECT_MOVE", "Select / move listing"))
				tooltip.AutoAppendNewTextLineResize(
					"|Ikey/ctrl|i + |Ikey/mouse_right|i - %s" % _Text(
						"VIRTUAL_MARKET_OWNER_REPRICE_SHORTCUT", "Change price"))
				tooltip.AutoAppendNewTextLineResize(
					"|Ikey/mouse_right|i - %s" % _Text(
						"VIRTUAL_MARKET_OWNER_RETURN_SHORTCUT", "Move to Returns"))
			tooltip.ShowToolTip()
		except:
			self._HideTooltip()

	def _HideTooltip(self):
		tooltip = getattr(self.interface, "tooltipItem", None)
		if tooltip:
			tooltip.HideToolTip()

	def _Claim(self, payload):
		source, sourceId, vnum, count = payload
		sent = bool(net.SendVirtualMarketItemClaim(
			source, sourceId, vnum, count))
		if sent:
			self.activeClaim = tuple(payload)
			self._HideTooltip()
			self._RefreshBox()
			self.nextClaimAt = app.GetTime() + float(getattr(net,
				"GetVirtualMarketClaimIntervalMs", lambda: 510)()) / 1000.0
			if self.claimAllController.IsActive():
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIMING_ALL",
					"Postupně vyzvedávám všechny předměty..."))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIMING", "Vyzvedávám item..."))
		else:
			canRetry = getattr(
				virtualmarket, "CanRetryItemClaimIntent", lambda *args: 0)
			if bool(canRetry(source, sourceId, vnum, count)):
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIM_RETRY_EXACT",
					"Vyzvednutí předmětu se nepodařilo odeslat. "
					"Zkuste stejný předmět znovu."),
					lambda item=payload: self._Claim(item))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIM_BUSY_OTHER",
					"Předmět teď nelze vyzvednout, protože probíhá "
					"jiná změna trhu."))
		return sent

	def OnSearchResult(self, token, status, appended, hasMore):
		if int(status) == virtualmarket.STATUS_RATE_LIMITED and self.searchRetryEvent:
			# Two searches inside the server's 250 ms window: resend once.
			self.searchRetryAt = app.GetTime() + SEARCH_RATE_LIMIT_RETRY_DELAY
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1m..."))
			return
		self.searchRetryEvent = None
		if int(status) != virtualmarket.STATUS_OK:
			self._SetStatus(self._StatusError(status))
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_REQUEST_FAILED", "Trh nelze na\u010d\u00edst"),
				self._StatusError(status),
				_Text("VIRTUAL_MARKET_REQUEST_FAILED_DETAIL", "Zkuste po\u017eadavek za chv\u00edli zopakovat."))
			return
		if not appended:
			self.marketPages = []
			self.marketLayoutCount = 0
		if self.advanceAfterAppend and appended:
			self.currentPage += 1
		self.advanceAfterAppend = False
		self._SetStatus("")
		self._RefreshMarket()

	def OnSellerSuggestionsResult(self, token, status):
		if self.searchMode != "seller" or \
				self.searchInput.GetText().strip() != self.pendingSuggestionText:
			return
		if int(status) != virtualmarket.STATUS_OK:
			self.suggestionDropdown.Close()
			return
		names = []
		for index in range(int(virtualmarket.GetSellerSuggestionCount())):
			name = virtualmarket.GetSellerSuggestion(index)
			if name:
				names.append(name)
		self.suggestionDropdown.Open(names)

	def OnOwnerListingsResult(self, token, status, appended, hasMore):
		if int(status) != virtualmarket.STATUS_OK:
			if self.currentTab == TAB_OWNER:
				self._SetStatus(self._StatusError(status))
			return
		if self.advanceAfterAppend and appended:
			self.currentPage += 1
		self.advanceAfterAppend = False
		if self.currentTab == TAB_OWNER:
			self._SetStatus("")
			self._RefreshOwnerGrid()

	def OnOwnerShopResult(self, token, status):
		if int(status) != virtualmarket.STATUS_OK:
			if self.currentTab == TAB_OWNER:
				self._SetStatus(self._StatusError(status))
			return
		self._UpdateSidebarSellers()
		if self.currentTab == TAB_OWNER:
			self._SetStatus("")
		self._RefreshOwner()

	def OnSellerReturnsResult(self, token, status, appended, hasMore):
		self._OnBoxResult(
			virtualmarket.CLAIM_SOURCE_SELLER_RETURN, status, appended)

	def OnBuyerDeliveriesResult(self, token, status, appended, hasMore):
		self._OnBoxResult(
			virtualmarket.CLAIM_SOURCE_DELIVERY, status, appended)

	def _OnBoxResult(self, source, status, appended):
		if int(status) != virtualmarket.STATUS_OK:
			if self.claimAllController.IsActive() and \
					int(source) == int(self.claimAllController.source):
				self._StopClaimAll()
			self._SetStatus(self._StatusError(status))
			return
		if self.advanceAfterAppend and appended:
			self.currentPage += 1
		self.advanceAfterAppend = False
		self._RefreshBox()
		if self.claimAllController.IsActive() and \
				int(source) == int(self.claimAllController.source):
			if self.claimAllController.MarkRefreshed():
				self._ContinueClaimAll()
			return
		self._SetStatus("")

	def OnShopCommandResult(self, token, status, command, result, replayed):
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.COMMAND_RESULT_APPLIED:
			self._SetStatus(_Text("VIRTUAL_MARKET_SHOP_UPDATED", "Obchod byl bezpe\u010dn\u011b aktualizov\u00e1n."))
			net.SendVirtualMarketOwnerShop()
			if hasattr(net, "SendVirtualMarketOwnerListings"):
				net.SendVirtualMarketOwnerListings()
			return
		retry = net.SendVirtualMarketShopRetry if virtualmarket.CanRetryShopCommand() else None
		self._SetStatus(self._StatusError(status, result), retry)

	def OnListingCreateResult(self, token, status, result, replayed):
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.LISTING_RESULT_APPLIED:
			if self.pendingListingCreate:
				vnum, count, rememberedPrice = self.pendingListingCreate
				getattr(virtualmarket, "CachePricePreference", lambda *args: 0)(
					vnum, rememberedPrice, count)
			self.pendingListingCreate = None
			self._ClearOffer()
			self._SetStatus(_Text("VIRTUAL_MARKET_LISTED", "Item je bezpe\u010dn\u011b ulo\u017een v tr\u017en\u00edm escrow."))
			net.SendVirtualMarketOwnerShop()
			if hasattr(net, "SendVirtualMarketOwnerListings"):
				net.SendVirtualMarketOwnerListings()
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == \
				virtualmarket.LISTING_RESULT_DISPLAY_SLOT_OCCUPIED:
			self.pendingListingCreate = None
			self._ClearOffer()
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_SLOT_CHANGED",
				"Zvolen\u00e9 m\u00edsto u\u017e obsadila jin\u00e1 nab\u00eddka. Vyberte jin\u00fd slot."))
			if hasattr(net, "SendVirtualMarketOwnerListings"):
				net.SendVirtualMarketOwnerListings()
			return
		retry = net.SendVirtualMarketListingCreateRetry if virtualmarket.CanRetryListingCreate() else None
		if not retry:
			self.pendingListingCreate = None
			self._ClearOffer()
		self._SetStatus(self._StatusError(status, result), retry)

	def OnListingMoveResult(self, token, status, result, replayed):
		if int(status) == virtualmarket.STATUS_OK and \
				hasattr(net, "SendVirtualMarketOwnerListings"):
			net.SendVirtualMarketOwnerListings()
		if int(status) == virtualmarket.STATUS_OK and \
				int(result) == virtualmarket.LISTING_MOVE_RESULT_APPLIED:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_MOVED",
				"Nab\u00eddka byla p\u0159esunuta."))
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == \
				virtualmarket.LISTING_MOVE_RESULT_OCCUPIED:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_SLOT_CHANGED",
				"Zvolen\u00e9 m\u00edsto u\u017e obsadila jin\u00e1 nab\u00eddka."))
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == \
				virtualmarket.LISTING_MOVE_RESULT_LISTING_BUSY:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_BUSY",
				"Nab\u00eddku pr\u00e1v\u011b zpracov\u00e1v\u00e1 n\u00e1kup; zkuste to znovu za okam\u017eik."))
			return
		retry = net.SendVirtualMarketListingMoveRetry \
			if virtualmarket.CanRetryListingMove() else None
		self._SetStatus(self._StatusError(status, result), retry)

	def OnListingMutationResult(self, token, status, mutation, result, replayed,
			listingId, price):
		status = int(status)
		mutation = int(mutation)
		result = int(result)
		if status == virtualmarket.STATUS_OK and result == \
				virtualmarket.LISTING_MUTATION_RESULT_APPLIED:
			if mutation != virtualmarket.LISTING_MUTATION_CANCEL and self.pendingReprice:
				_pendingListing, vnum, count, _rememberedPrice = self.pendingReprice
				if int(_pendingListing) == int(listingId):
					getattr(virtualmarket, "CachePricePreference", lambda *args: 0)(
						vnum, int(price), count)
			self.pendingReprice = None
			self._ClearOwnerSelection()
			if mutation == virtualmarket.LISTING_MUTATION_CANCEL:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_LISTING_CANCELED",
					"Nab\u00eddka byla odebr\u00e1na; item \u010dek\u00e1 v z\u00e1lo\u017ece Vr\u00e1cen\u00e9."))
				net.SendVirtualMarketSellerReturns()
			elif mutation == getattr(virtualmarket, "LISTING_MUTATION_REPRICE_MATCHING", -1):
				self._SetStatus(_Text("VIRTUAL_MARKET_MATCHING_REPRICED",
					"Ceny shodných položek byly změněny podle ceny za kus."))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_LISTING_REPRICED",
					"Cena nab\u00eddky byla zm\u011bn\u011bna na %s.") % _Money(price))
			net.SendVirtualMarketOwnerShop()
			if hasattr(net, "SendVirtualMarketOwnerListings"):
				net.SendVirtualMarketOwnerListings()
			return
		if status == virtualmarket.STATUS_OK and result == \
				virtualmarket.LISTING_MUTATION_RESULT_LISTING_BUSY:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_BUSY",
				"Nab\u00eddku pr\u00e1v\u011b zpracov\u00e1v\u00e1 n\u00e1kup; zkuste to znovu za okam\u017eik."))
			return
		if status == virtualmarket.STATUS_OK and result == virtualmarket.LISTING_MUTATION_RESULT_INVALID_PRICE:
			self.pendingReprice = None
			self._SetStatus(_Text("VIRTUAL_MARKET_MATCHING_PRICE_LIMIT",
				"Cena některého balíku by překročila 10 000 000 000 Yang. Žádná cena se nezměnila."))
			return
		retry = getattr(net, "SendVirtualMarketListingMutationRetry", None) \
			if getattr(virtualmarket, "CanRetryListingMutation", lambda: 0)() else None
		if not retry:
			self.pendingReprice = None
		self._SetStatus(self._StatusError(status, result), retry)

	def OnItemClaimResult(self, token, status, source, result, replayed):
		self.activeClaim = None
		if int(status) == virtualmarket.STATUS_OK and int(result) in (
			virtualmarket.CLAIM_RESULT_APPLIED, virtualmarket.CLAIM_RESULT_REPLAYED,
			virtualmarket.CLAIM_RESULT_ALREADY_CLAIMED):
			claimAll = self.claimAllController.IsActive() and \
				int(source) == int(self.claimAllController.source)
			if claimAll:
				if not self.claimAllController.MarkSucceeded():
					self._StopClaimAll()
				else:
					self._SetStatus(_Text(
						"VIRTUAL_MARKET_CLAIMING_ALL",
						"Postupně vyzvedávám všechny předměty..."))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIMED", "Item byl vyzvednut."))
			if bool(getattr(virtualmarket, "IMMEDIATE_CLAIM_UPDATES", 0)):
				self._RefreshBox()
				if claimAll:
					self.claimAllController.MarkRefreshed()
				else:
					self._RefillEmptyClaimBox(source)
			else:
				if int(source) == virtualmarket.CLAIM_SOURCE_DELIVERY:
					net.SendVirtualMarketBuyerDeliveries()
				else:
					net.SendVirtualMarketSellerReturns()
			self._RefreshClaimActions()
			return
		self.queuedClaims = []
		if self.claimAllController.IsActive():
			self._StopClaimAll()
		self._RefreshBox()
		retry = net.SendVirtualMarketItemClaimRetry if virtualmarket.CanRetryItemClaim() else None
		if int(status) == virtualmarket.STATUS_OK and int(result) == \
				virtualmarket.CLAIM_RESULT_DESTINATION_BUSY:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_CLAIM_CONTIGUOUS_SPACE",
				"V inventáři chybí souvislé místo pro celý předmět."), retry)
			return
		self._SetStatus(self._StatusError(status, result), retry)

	def OnPurchaseResult(self, token, status, result, replayed, state):
		if int(status) == virtualmarket.STATUS_OK and int(result) in (
			virtualmarket.PURCHASE_RESULT_APPLIED, virtualmarket.PURCHASE_RESULT_REPLAYED):
			self._SetStatus(_Text("VIRTUAL_MARKET_PURCHASED", "N\u00e1kup prob\u011bhl. Item \u010dek\u00e1 v z\u00e1lo\u017ece N\u00e1kupy."))
			self._RepeatMarketSearch()
			return
		retry = net.SendVirtualMarketPurchaseRetry if virtualmarket.CanRetryPurchase() else None
		self._SetStatus(self._StatusError(status, result), retry)

	def OnBatchPurchaseResult(self, token, status, result, replayed, state, itemCount):
		if int(status) == virtualmarket.STATUS_OK and int(result) in (
			virtualmarket.PURCHASE_RESULT_APPLIED, virtualmarket.PURCHASE_RESULT_REPLAYED):
			self._ClearPurchaseSelection()
			self._SetStatus(_Text("VIRTUAL_MARKET_BATCH_PURCHASED",
				"Nákup %d položek proběhl. Čekají v záložce Nákupy.") % int(itemCount))
			self._RepeatMarketSearch()
			return
		canRetry = getattr(virtualmarket, "CanRetryBatchPurchase", lambda: 0)
		retry = getattr(net, "SendVirtualMarketBatchPurchaseRetry", None) if canRetry() else None
		self._SetStatus(self._StatusError(status, result), retry)

	def OnSellerWithdrawalResult(self, token, status, result, replayed):
		if int(status) == virtualmarket.STATUS_OK and int(result) in (
			virtualmarket.WITHDRAWAL_RESULT_APPLIED, virtualmarket.WITHDRAWAL_RESULT_REPLAYED):
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAWN", "V\u00fdt\u011b\u017eek byl p\u0159ips\u00e1n k Yang."))
			net.SendVirtualMarketOwnerShop()
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.WITHDRAWAL_RESULT_CONFLICT:
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAW_BUSY",
				"Prob\u00edh\u00e1 jin\u00e1 zm\u011bna postavy. V\u00fdb\u011br Yang bezpe\u010dn\u011b zopakujte."),
				net.SendVirtualMarketSellerWithdrawal)
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.WITHDRAWAL_RESULT_NO_CREDIT:
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAW_EMPTY", "K vyzvednut\u00ed nejsou \u017e\u00e1dn\u00e9 Yang."))
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.WITHDRAWAL_RESULT_YANG_LIMIT:
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAW_LIMIT",
				"V\u00fdb\u011br by p\u0159ekro\u010dil limit Yang postavy."))
			return
		retry = net.SendVirtualMarketSellerWithdrawalRetry if virtualmarket.CanRetrySellerWithdrawal() else None
		self._SetStatus(self._StatusError(status, result), retry)

	def _StatusError(self, status, result=None):
		status = int(status)
		if status == virtualmarket.STATUS_DISABLED:
			return _Text("VIRTUAL_MARKET_DISABLED", "Virtu\u00e1ln\u00ed trh je do\u010dasn\u011b vypnut\u00fd.")
		if status == virtualmarket.STATUS_UNAVAILABLE:
			return _Text("VIRTUAL_MARKET_UNAVAILABLE", "Trh je do\u010dasn\u011b nedostupn\u00fd; bezpe\u010dn\u011b opakujte po\u017eadavek.")
		if status == virtualmarket.STATUS_RATE_LIMITED:
			return _Text("VIRTUAL_MARKET_RATE_LIMIT", "Po\u010dkejte chv\u00edli p\u0159ed dal\u0161\u00edm po\u017eadavkem.")
		return (_Text("VIRTUAL_MARKET_ERROR",
			"Po\u017eadavek se nepoda\u0159ilo dokon\u010dit (stav %d, v\u00fdsledek %s).") %
			(status, str(result) if result is not None else "-"))

	def _SyncPendingClaim(self):
		# Reconcile native cancellation/reset even without a Python result callback.
		if self.activeClaim is not None and not bool(getattr(
				virtualmarket, "IsItemClaimLoading", lambda: 0)()):
			self.activeClaim = None
			self._StopClaimAll()
			self._RefreshBox()

	def OnUpdate(self):
		if not self.IsShow():
			return
		self._SyncPendingClaim()
		if self.ownerDragListingId and not self._IsOwnerDrag():
			self._CancelOwnerDrag()
		self._UpdateSearchSuggestions()
		now = app.GetTime()
		if self.searchRetryAt and now >= self.searchRetryAt:
			self._RunSearchRetry()
		if self.currentTab in (TAB_DELIVERIES, TAB_RETURNS):
			self._AdvanceClaims()
			if now - self.lastBoxRefresh < 0.25:
				return
			self.lastBoxRefresh = now
			if self._GetBoxStateSignature() != self.boxStateSignature:
				self._RefreshBox()
			return
		if self.currentTab != TAB_OWNER:
			return
		if now - self.lastLeaseRefresh < 0.5:
			return
		self.lastLeaseRefresh = now
		self._RefreshOwner()
