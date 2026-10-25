import app
import chat
import grp
import item
import localeInfo
import mouseModule
import net
import player
import sys
import ui
import uiCommon
import marketpricedialog
import uitooltip
import uicrimsoncontrols
import virtualmarket
import marketpurchasefailure
import fontconfig
import marketlayout
import marketobtainable
import uimarketfilters
import uiwheel
import wndMgr
from uicrimsonember import SettingsScrollBar
from uimarketfilters import AdvancedMarketFilterDialog


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 590
# Market snapshots carry socket5 separately as the bonus-change counter.
ATTR_CHANGE_COUNT_SOCKET = 5
ROW_HEIGHT = marketlayout.BASE_ROW_HEIGHT
MARKET_ROWS_Y = 30
GRID_COLUMNS = 15
GRID_ROWS = 11
GRID_SLOT_COUNT = GRID_COLUMNS * GRID_ROWS

ROW_WIDTH = 541
SEARCH_INPUT_X = 17
SEARCH_INPUT_Y = 86
SEARCH_BUTTON_X = 168
SEARCH_BUTTON_Y = 88
FILTER_BUTTON_X = 199
FILTER_BUTTON_Y = 88
CONTENT_MARGIN = 12
CONTENT_TOP = 78
CONTENT_HEIGHT = 500
BODY_X = 239
BODY_Y = 78
BODY_WIDTH = 549
BODY_HEIGHT = 500
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
# A click on a category opens it like an accordion and its item_proto
# subtypes (the filter dialog's Podkategorie, marketfilters.subcategories) follow as smaller, indented rows of the
# same row plate; a click on one filters, a second click on the category closes it. One category is open at a time.
# A category opens only with SearchV4 (the only query carrying a subtype) and at least two subcategories.
SUBCATEGORY_STEP_Y = 24
SUBCATEGORY_BUTTON_HEIGHT = 24
SUBCATEGORY_INDENT_X = 6
SUBCATEGORY_WIDTH = CATEGORY_VIEWPORT_WIDTH - SUBCATEGORY_INDENT_X
SUBCATEGORY_TEXT_X = 12
SUBCATEGORY_TEXT_COLOR = 0xff9e8c7c
SUBCATEGORY_SELECTED_COLOR = 0xffeadfc8
SUBCATEGORY_MINIMUM = 2
SUBCATEGORY_POOL = 16
# Opening a row lets its entries in one after another over this time instead of one jump of every row below.
SUBCATEGORY_OPEN_SECONDS = 0.15
CATEGORY_CHEVRON_X = 180
CATEGORY_CHEVRON_Y = 11
CATEGORY_CHEVRON_PATH = "d:/ymir work/ui/public/althea_r1/chevron/%s_normal.png"
SEARCH_RESET_X = 170
SEARCH_RESET_Y = 110
SEARCH_RESET_WIDTH = 64
# The 20 px pagination plates stand on the centre line of the footer bar (FOOTER_CENTER_Y 482 - 10).
PAGINATION_Y = 472
RETRY_Y = 548

ACCOUNT_PANEL_X = 4
ACCOUNT_PANEL_WIDTH = 541
ACCOUNT_HEADER_Y = 0
ACCOUNT_HEADER_HEIGHT = 29
ACCOUNT_CONTENT_Y = 30
ACCOUNT_CONTENT_HEIGHT = 470
ACCOUNT_TOOLBAR_X = 12
ACCOUNT_TOOLBAR_LOCAL_X = ACCOUNT_TOOLBAR_X - ACCOUNT_PANEL_X
ACCOUNT_TOOLBAR_WIDTH = 525                      # panel/account_toolbar.png (the value strip too)
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
CLOSED_TITLE_Y = 105
CLOSED_HINT_Y = 134
CREATE_BUTTON_Y = 175
SHOP_NAME_MAX_BYTES = 64
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
# The 24 px "Napsat prodejci" envelope (owner 13. 10.: the 16 px one was too small, "tak 2x větší"): its click area
# is the icon, centred on ACTION_CENTER_X and on the 51 px row, right of the seller column (SELLER_CENTER_X +
# SELLER_SAFE_WIDTH / 2 = 502) and inside the row (ROW_WIDTH 541).
MESSAGE_ICON_X = 512
MESSAGE_ICON_Y = 14
# A row with a leading two-line column in place of the check box ("Můj obchod" -> Historie, owner 22. 10.: the same
# row as the market results, no new table): the date over the time, centred on ROW_LEAD_CENTER_X like the price's
# two lines; the item slot and the name move right by ROW_LEAD_SHIFT (slot 55..87, name 95..221 as before).
ROW_LEAD_CENTER_X = 27
ROW_LEAD_SHIFT = 22
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
# The market footer (owner 13. 10.: "Koupit vybrané" hung on the footer's top line above "Celkem" and stuck out of
# it) is the R1 footer bar (docs/ALTHEA_R1_KIT.md, 2 "Spodní lišta"): a 36 px panel across the market column, its
# bottom 12 px (T.PAD) above the window's bottom (= the body's bottom), inner padding 10, one row on its centre line:
# "Vybráno" left, the pagination in the middle, "Celkem" right and 10 px after it the primary 26 px button, inside
# the bar. The original look keeps its 61 px band (MARKET_FOOTER_*) with the same row on the same centre line.
FOOTER_BAR_X = 0
FOOTER_BAR_WIDTH = BODY_WIDTH
FOOTER_BAR_HEIGHT = 36
FOOTER_BAR_Y = BODY_HEIGHT - FOOTER_BAR_HEIGHT
FOOTER_BAR_PAD = 10
FOOTER_GAP = 10
FOOTER_CENTER_Y = FOOTER_BAR_Y + FOOTER_BAR_HEIGHT // 2
SELECTION_LABEL_X = FOOTER_BAR_X + FOOTER_BAR_PAD
# At least T.BTN_W 96; "Koupit vybrané" fits in the kit's button_s label (uir1.Button steps the label down).
BUY_SELECTED_WIDTH = 110
BUY_SELECTED_HEIGHT = 26
BUY_SELECTED_X = FOOTER_BAR_X + FOOTER_BAR_WIDTH - FOOTER_BAR_PAD - BUY_SELECTED_WIDTH
BUY_SELECTED_Y = FOOTER_CENTER_Y - BUY_SELECTED_HEIGHT // 2
LEGACY_BUY_WIDTH = 96       # the original "button/buy" plate, 28 px
LEGACY_BUY_X = FOOTER_BAR_X + FOOTER_BAR_WIDTH - FOOTER_BAR_PAD - LEGACY_BUY_WIDTH
LEGACY_BUY_Y = FOOTER_CENTER_Y - 14
TOTAL_RIGHT_X = BUY_SELECTED_X - FOOTER_GAP
RETRY_BUTTON_WIDTH = 72
RETRY_BUTTON_X = FOOTER_BAR_X + FOOTER_BAR_WIDTH - FOOTER_BAR_PAD - RETRY_BUTTON_WIDTH
RETRY_BUTTON_Y = FOOTER_CENTER_Y - 12
# ‹ 1 2 3 ›: 3 page plates between the arrows, 27 px apart = 132 px. It stands in the middle of the room between
# the widest "Vybráno: 20 / 20" (90 px, ends at 100) and the widest "Celkem: 2.000.000.000 Yang" (154 px, starts at
# 265), 10 px from both.
PAGINATION_SLOTS = 3
PAGINATION_STEP = 27
PAGINATION_WIDTH = PAGINATION_STEP * (PAGINATION_SLOTS + 1) + 24
PAGINATION_X = 117

CRIMSON_MARKET_DIR = "d:/ymir work/ui/game/crimson_ember/virtual_market/"
SEARCH_UI_PATH = "d:/ymir work/ui/game/search_shop/"
ITEM_ROW_PATH = CRIMSON_MARKET_DIR + "surface/result_normal.png"
ITEM_SLOT_PATH = "d:/ymir work/ui/public/Slot_Base.sub"
ITEM_COIN_PATH = ""

TAB_MARKET = 0
TAB_OWNER = 1
TAB_DELIVERIES = 2
TAB_RETURNS = 3
OWNER_VIEW_LISTINGS = "listings"
OWNER_VIEW_HISTORY = "history"   # spelled out where partial test windows run the method

# The category rail (marketfilters.RAIL_ROWS): locale key, fallback,
# icon (the original icons; Šperky and Truhly a klíče use the original offline-shop ones), the V3 type / subtype of
# an older server, the SearchV4 category the row searches (a folder row searches its first entry) and its rail key.
MARKET_CATEGORIES = (
	("VIRTUAL_MARKET_CATEGORY_WEAPONS", "Zbran\u011b", "weapons", item.ITEM_TYPE_WEAPON, -1),
	("VIRTUAL_MARKET_CATEGORY_ARMOR", "Zbroj", "armors", item.ITEM_TYPE_ARMOR, -1),
	("VIRTUAL_MARKET_CATEGORY_JEWELRY", "\u0160perky", "rings", item.ITEM_TYPE_ARMOR, -1),
	("VIRTUAL_MARKET_CATEGORY_SASHES", "Šerpy", "sashes", item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_ACCE),
	("VIRTUAL_MARKET_CATEGORY_LOOKS", "Vzhled", "costumes", item.ITEM_TYPE_COSTUME, -1),
	("VIRTUAL_MARKET_CATEGORY_PETS_MOUNTS", "Mazl\u00edci a mounti", "pets", item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_PET),
	("VIRTUAL_MARKET_CATEGORY_STONES", "Kameny", "ghoststones", item.ITEM_TYPE_METIN, -1),
	("VIRTUAL_MARKET_CATEGORY_ALCHEMY", "Alchymie", "alchemy", item.ITEM_TYPE_DS, -1),
	("VIRTUAL_MARKET_CATEGORY_BOOKS", "Knihy", "skills", item.ITEM_TYPE_SKILLBOOK, -1),
	("VIRTUAL_MARKET_CATEGORY_CONSUMABLES", "Spot\u0159ebn\u00ed", "consumeables", item.ITEM_TYPE_USE, -1),
	("VIRTUAL_MARKET_CATEGORY_MATERIALS", "Materi\u00e1ly", "materials", item.ITEM_TYPE_MATERIAL, -1),
	# Server category 12 holds both rows below: truhly / pokladnice / klíče by item type, the rest as Ostatní. It has
	# no single item type, so it exists only as a SearchV4 category.
	("VIRTUAL_MARKET_CATEGORY_CHESTS", "Truhly a kl\u00ed\u010de", "quests", -1, -1),
	("VIRTUAL_MARKET_CATEGORY_OTHER", "Ostatn\u00ed", "other", -1, -1),
)
MARKET_CATEGORY_IDS = (1, 2, 2, 11, 3, 4, 8, 6, 7, 9, 10, 12, 12)
MARKET_CATEGORY_KEYS = ("weapons", "armor", "jewelry", "sashes", "looks", "pets_mounts", "stones", "alchemy",
	"books", "consumables", "materials", "chests", "other")
MARKET_CATEGORY_FOLDERS = ("armor", "jewelry", "pets_mounts", "stones", "chests")
MARKET_CATEGORY_OTHER = 12
# The server rate-limits searches per player to 250 ms; one automatic retry
# waits slightly longer so a refused request succeeds without user action.
SEARCH_RATE_LIMIT_RETRY_DELAY = 0.3
# The game refuses a second change of the owner's listings inside its limit
# (cancel/reprice 500 ms, move 150 ms) with RATE_LIMITED. The native bridge then
# keeps that operation for "Opakovat" and refuses every other market action
# (another cancel, a claim from Vrácené) until it is resolved: two quick
# right-clicks in Můj obchod left only one item taken out (owner 15. 10.).
# The same operation is resent by itself once the limit has passed.
OPERATION_RATE_LIMIT_RETRY_DELAY = 0.55
OPERATION_RATE_LIMIT_RETRY_ATTEMPTS = 5
# A refused read of the own shop (the game allows one per 250 ms; a listing, a reprice and opening the tab
# each ask for one) carries no shop: the native copy then says "no shop" and "Můj obchod" showed
# "Tvůj obchod zatím není otevřen" with Založit instead of the grid, so nothing could be offered
# (prod 22. 10.). The last shop read with status OK stays shown and the read is asked again.
OWNER_SHOP_RETRY_DELAY = 0.3
OWNER_SHOP_RETRY_ATTEMPTS = 5
# "Vložit vše (N×)" offers the further listings one by one (the market has no
# batch create and the game takes one create at a time): the next create goes
# once the previous one is answered and no sooner than this long after the
# previous one was SENT, just above the game's create limit (CONFIG
# MARKET_LISTING_CREATE_RATE_LIMIT_MS, 250 ms, counted from the previous create
# it accepted). Owner 21. 10.: 0.3 s after each answer listed one stack every
# ~0.44 s on DEV (answer ~0.14 s + 0.3 s); now it is ~0.28 s per listing.
OFFER_ALL_STEP_DELAY = 0.28
# The owner grid places listings by slot while the server pages them by id,
# so every page is loaded. The next page is asked for right after an answer
# (the server exempts it from its owner read limit, CONFIG
# MARKET_OWNER_PAGE_RATE_LIMIT_MS); a server that refuses it with the read limit
# gets every further page after OWNER_LISTINGS_PAGE_DELAY, which stays above
# that limit (250 ms).
OWNER_LISTINGS_NEXT_PAGE_DELAY = 0.0
OWNER_LISTINGS_PAGE_DELAY = 0.3
OWNER_LISTINGS_PAGE_ATTEMPTS = 40
# A reload of a shop with more than one server page (50 listings) first
# replaces the list with page 1 and appends the rest one by one. The grid keeps the
# last complete layout until the last page arrives; when no page arrives for this
# many seconds the reload counts as stalled and is asked again (the layout stays).
OWNER_RELOAD_HOLD_MAX = 3.0
# ALTHEA-622: item.GetItemNamesByName accepts at most 64 results; the dropdown
# shows eight rows and scrolls the rest, so every +N of an item is reachable.
SEARCH_SUGGESTION_LIMIT = 64
SEARCH_SUGGESTION_VISIBLE = 8


# The R1 look of the market window (root/uivirtualmarketr1.Theme) while the window is built and shown in it; None in
# the original look. The helpers below ask it for the R1 file of a market texture, the R1 text font and colour.
_R1 = None


def _R1Theme():
	"""The R1 theme unless Settings -> "Starý vzhled" chose the original windows (settingslook 'legacy')."""
	import uir1
	if not uir1.UseR1():
		return None
	import uivirtualmarketr1
	return uivirtualmarketr1.Theme()


def _SetTheme(theme):
	"""The look the market and its filter dialog build in from now on (None = the original look)."""
	global _R1
	_R1 = theme
	uimarketfilters._R1 = theme


def _MarketFile(path):
	if _R1 is not None:
		return _R1.Path(path) or path
	return path


def _SlotBase():
	"""The slot base of the market's item slots (result rows, the shop and delivery grids): the R1 item slot C in
	the R1 look, the original slot otherwise."""
	if _R1 is not None:
		return _R1.SlotBase()
	return ITEM_SLOT_PATH


def _OtherCategoryAvailable():
	# Needs the compatible executable and the server capability offer.
	return bool(getattr(net, "IsVirtualMarketCategoryOtherAvailable", lambda: 0)())



def _IsListingInventorySource(windowType, position):
	if position < 0:
		return False
	if windowType == player.DRAGON_SOUL_INVENTORY:
		return position < player.DRAGON_SOUL_SLOT_COUNT
	if windowType != player.INVENTORY:
		return False
	if position < player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT:
		return True
	if not getattr(app, "ENABLE_SPECIAL_INVENTORY_SYSTEM", 0):
		return False
	# Category starts retain their legacy stride; its reserved tail is not active.
	capacity = player.SPECIAL_INVENTORY_PAGE_SIZE * player.SPECIAL_INVENTORY_PAGE_COUNT
	starts = (
		item.SKILL_BOOK_INVENTORY_SLOT_START,
		item.UPGRADE_ITEMS_INVENTORY_SLOT_START,
		item.STONE_INVENTORY_SLOT_START,
		item.GIFT_BOX_INVENTORY_SLOT_START,
		item.SWITCH_INVENTORY_SLOT_START,
		item.COSTUME_INVENTORY_SLOT_START,
		item.CONSUMABLE_INVENTORY_SLOT_START,
	)
	return any(start <= position < start + capacity for start in starts)


def _ListingInventorySlots():
	"""Every inventory cell _IsListingInventorySource accepts, in order: the ordinary pages, then the special ones."""
	slots = list(range(player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT))
	if getattr(app, "ENABLE_SPECIAL_INVENTORY_SYSTEM", 0):
		capacity = player.SPECIAL_INVENTORY_PAGE_SIZE * player.SPECIAL_INVENTORY_PAGE_COUNT
		for start in (
			item.SKILL_BOOK_INVENTORY_SLOT_START,
			item.UPGRADE_ITEMS_INVENTORY_SLOT_START,
			item.STONE_INVENTORY_SLOT_START,
			item.GIFT_BOX_INVENTORY_SLOT_START,
			item.SWITCH_INVENTORY_SLOT_START,
			item.COSTUME_INVENTORY_SLOT_START,
			item.CONSUMABLE_INVENTORY_SLOT_START,
		):
			slots.extend(range(start, start + capacity))
	return slots


def _Text(key, fallback):
	return getattr(localeInfo, key, fallback)


def _AutomaticShopName():
	"""The market protocol still requires a shop name (1..64 bytes), but nobody sees it: listings show the
	character name. Send the character name, or a fixed word if the name is not available."""
	try:
		name = str(player.GetName()).strip()
	except Exception:
		name = ""
	return name[:SHOP_NAME_MAX_BYTES] or "Obchod"


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
	button.SetUpVisual(_MarketFile(CRIMSON_MARKET_DIR + prefix + "_normal.png"))
	button.SetOverVisual(_MarketFile(CRIMSON_MARKET_DIR + prefix + "_hover.png"))
	button.SetDownVisual(_MarketFile(CRIMSON_MARKET_DIR + prefix +
		("_selected.png" if selected else "_pressed.png")))
	button.SetDisableVisual(_MarketFile(CRIMSON_MARKET_DIR + prefix + "_disabled.png"))


def _CrimsonButton(parent, x, y, prefix, event, text="", selected=False):
	button = ui.RadioButton() if selected else ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	_SetButtonVisuals(button, prefix, selected)
	if text:
		button.SetText(text)
		button.SetTextColor(0xffeadfc8)
		if _R1 is not None:
			_R1.StyleButtonText(button, prefix == "button/buy")
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
	if _R1 is not None:
		_SetButtonVisuals(button, "button/create")
	else:
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
	if _R1 is not None:
		# R1: section / control texts in Spectral, R1 text colours (before the text is laid out).
		label.SetFontName(_R1.Font(role, fontconfig.FontForRole(role)))
		color = _R1.Color(color) if color is not None else None
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
	image.LoadImage(_MarketFile(filename))
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
	# 24 px Crimson icons are centred on the 32 px row. Sashes, Other, Jewelry
	# and Chests had the grey 18 px offline-shop icons (tinted gold they still
	# read as monochrome); they now have the
	# coloured game item icons of a sash (85003), a chest (50006), a ring
	# (50002) and a key (50008), resized to the 24 px of the other icons.
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
		"sashes": (8, 4),
		"other": (8, 4),
		"rings": (8, 4),
		"quests": (8, 4),
	}
	iconX, iconY = iconPositions.get(iconName, (8, 4))
	iconRole = iconAliases.get(iconName, iconName)
	icon = _Image(button, iconX, iconY,
		CRIMSON_MARKET_DIR + "icon/category_%s.png" % iconRole)
	return button, icon, label


def _SubcategoryRow(parent, event):
	"""A subcategory row: the category row plate, narrower and lower, its text left-aligned."""
	button = _CrimsonButton(parent, SUBCATEGORY_INDENT_X, 0, "category/row",
		event, "", True)
	wndMgr.SetScale(button.hWnd,
		float(SUBCATEGORY_WIDTH) / CATEGORY_VIEWPORT_WIDTH,
		float(SUBCATEGORY_BUTTON_HEIGHT) / CATEGORY_SOURCE_HEIGHT)
	button.SetSize(SUBCATEGORY_WIDTH, SUBCATEGORY_BUTTON_HEIGHT)
	label = _Label(
		button, SUBCATEGORY_TEXT_X, SUBCATEGORY_BUTTON_HEIGHT // 2, "",
		SUBCATEGORY_TEXT_COLOR)
	label.SetVerticalAlignCenter()
	button.Hide()
	return button, label


def _MarkRow(button, selected):
	"""Shows a category / subcategory row as chosen or not WITHOUT the engine's pressed state: a pressed
	CRadioButton takes no click at all (EterPythonLib CRadioButton::OnMouseLeftButtonDown), so the open
	category could not be closed by a second click. The chosen row shows the selected plate as its up / over
	visual instead and stays clickable; every click ends in _SyncMarketCategory, which marks the rows again."""
	base = CRIMSON_MARKET_DIR + "category/row"
	if getattr(button, "rowSelected", None) != bool(selected):
		# CButton::SetUpVisual sizes the window to the image: the row keeps its own (scaled) size.
		width, height = button.GetWidth(), button.GetHeight()
		button.SetUpVisual(_MarketFile(base + ("_selected.png" if selected else "_normal.png")))
		button.SetOverVisual(_MarketFile(base + ("_selected.png" if selected else "_hover.png")))
		button.SetSize(width, height)
		button.rowSelected = bool(selected)
	button.SetUp()


def _MarketColor(color):
	return _R1.Color(color) if _R1 is not None else color


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


# The market shortcuts under the "i" of "Můj obchod" (owner 21. 10.: Shift + right-click needs a guide). The kit's
# info icon of the settings ("i" in a circle, root/uisettingspanelsv5widgets.py InfoDot), hover shows the R1 hint.
MARKET_HELP_ICON = "d:/ymir work/ui/public/althea_kit/icons/20/info_%s.png"
MARKET_HELP_ICON_SIZE = 20
MARKET_HELP_LINES = (
	("VIRTUAL_MARKET_HELP_RIGHT", "Prav\u00e9 tla\u010d\u00edtko na p\u0159edm\u011bt v invent\u00e1\u0159i = nab\u00eddnout (zad\u00e1\u0161 cenu)"),
	("VIRTUAL_MARKET_HELP_SHIFT_RIGHT", "Shift + prav\u00e9 = vystavit za posledn\u00ed cenu bez dialogu"),
	("VIRTUAL_MARKET_HELP_SHIFT_LEFT", "Shift + lev\u00e9 v invent\u00e1\u0159i = rozd\u011blit hrom\u00e1dku (po\u010det kus\u016f v nab\u00eddce)"),
	("VIRTUAL_MARKET_HELP_OFFER_ALL", "Vlo\u017eit v\u0161e = dal\u0161\u00ed nab\u00eddky po stejn\u00e9m po\u010dtu kus\u016f a cen\u011b"),
	("VIRTUAL_MARKET_HELP_CTRL_LEFT", "Ctrl + lev\u00e9 na p\u0159edm\u011bt v invent\u00e1\u0159i = hledat ho na trhu"),
	("VIRTUAL_MARKET_HELP_CTRL_RIGHT", "Ctrl + prav\u00e9 na nab\u00eddku = zm\u011bnit cenu"),
	("VIRTUAL_MARKET_HELP_OWNER_RIGHT", "Prav\u00e9 na nab\u00eddku = vr\u00e1tit do Vr\u00e1cen\u00e9"),
)


def _MarketHelpLines():
	return [_Text(key, default) for key, default in MARKET_HELP_LINES]


class _MarketHelpDot(ui.Window):
	"""The "i" in a circle with the market shortcuts in its hint (R1: the one R1 hint; "Starý vzhled": a tooltip)."""

	def __init__(self, parent, x, y):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(MARKET_HELP_ICON_SIZE, MARKET_HELP_ICON_SIZE)
		self.image = ui.ImageBox()
		self.image.SetParent(self)
		self.image.AddFlag("not_pick")
		self.image.SetPosition(0, 0)
		self.image.LoadImage(MARKET_HELP_ICON % "normal")
		self.image.Show()
		self.title = _Text("VIRTUAL_MARKET_HELP_TITLE", "Zkratky trhu")
		self.tooltip = None
		if _R1 is None:
			self.tooltip = uitooltip.ToolTip()
			self.tooltip.SetTitle(self.title)
			for line in _MarketHelpLines():
				self.tooltip.AutoAppendNewTextLineResize(line)
			self.tooltip.HideToolTip()
		self.Show()

	def OnMouseOverIn(self):
		self.image.LoadImage(MARKET_HELP_ICON % "hover")
		if self.tooltip:
			self.tooltip.ShowToolTip()
		else:
			import uir1
			uir1.ShowHint(None, self, self.title, "\n".join(_MarketHelpLines()))

	def OnMouseOverOut(self):
		self.image.LoadImage(MARKET_HELP_ICON % "normal")
		self.__HideHint()

	def __HideHint(self):
		if self.tooltip:
			self.tooltip.HideToolTip()
		else:
			import uir1
			uir1.HideHint(self)

	def Destroy(self):
		self.__HideHint()
		self.tooltip = None
		self.image = None


class _SellerLink(ui.Window):
	NORMAL_COLOR = grp.GenerateColor(
		216.0 / 255.0, 173.0 / 255.0, 85.0 / 255.0, 1.0)
	HOVER_COLOR = grp.GenerateColor(
		255.0 / 255.0, 211.0 / 255.0, 107.0 / 255.0, 1.0)
	NORMAL_UNDERLINE_COLOR = NORMAL_COLOR
	HOVER_UNDERLINE_COLOR = HOVER_COLOR

	def __init__(self, parent, x, y, width, height, text, event, payload):
		ui.Window.__init__(self)
		if _R1 is not None:
			# R1 link: ink, red under the mouse; the underline keeps the colour of its text.
			self.NORMAL_COLOR = self.NORMAL_UNDERLINE_COLOR = _R1.link_normal
			self.HOVER_COLOR = self.HOVER_UNDERLINE_COLOR = _R1.link_hover
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
			"Kliknutím zobrazíš nabídky hráče %s.") % sellerName
		self.hintText = tooltipText
		self.tooltip = None
		if _R1 is None:
			# "Starý vzhled": the original tooltip board. The R1 look shows the one R1 hint (uir1.ShowHint).
			self.tooltip = uitooltip.ToolTip()
			self.tooltip.AutoAppendNewTextLineResize(tooltipText)
			self.tooltip.HideToolTip()
		self.Show()

	def OnMouseOverIn(self):
		self.label.SetPackedFontColor(self.HOVER_COLOR)
		self.underline.SetColor(self.HOVER_UNDERLINE_COLOR)
		if self.tooltip:
			self.tooltip.ShowToolTip()
		else:
			import uir1
			uir1.ShowHint(None, self, self.hintText)

	def OnMouseOverOut(self):
		self.label.SetPackedFontColor(self.NORMAL_COLOR)
		self.underline.SetColor(self.NORMAL_UNDERLINE_COLOR)
		self.__HideHint()

	def __HideHint(self):
		if self.tooltip:
			self.tooltip.HideToolTip()
		else:
			import uir1
			uir1.HideHint(self)

	def OnMouseLeftButtonUp(self):
		if self.IsIn() and self.event:
			self.event(self.payload)

	def Destroy(self):
		self.__HideHint()
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
		if _R1 is not None:
			self.NORMAL_COLOR, self.HOVER_COLOR = _R1.link_normal, _R1.link_hover
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
	left.SetPosition(startX, getattr(left, "footerY", FOOTER_CENTER_Y))
	right.SetPosition(startX + leftWidth, getattr(right, "footerY", FOOTER_CENTER_Y))


def _FooterText(label, role, color):
	"""A text of the footer row on the bar's centre line. R1: the kit font of the role, a uir1tokens colour and the
	line's top at uir1.CellTop of the bar (never the engine's vertical centre); original look: the engine centre."""
	if _R1 is not None:
		import uir1
		font = _R1.kit.font(role)
		uir1.SetFont(label, font)
		label.SetPackedFontColor(uir1.SignedColor(color))
		label.footerY = FOOTER_BAR_Y + uir1.CellTop(FOOTER_BAR_HEIGHT, font)
	else:
		label.SetVerticalAlignCenter()
		label.footerY = FOOTER_CENTER_Y
	x, _y = label.GetLocalPosition()
	label.SetPosition(x, label.footerY)


def _CenterAccountValuePair(left, right, centerX, y):
	leftWidth, _leftHeight = left.GetTextSize()
	rightWidth, _rightHeight = right.GetTextSize()
	startX = int(centerX - (leftWidth + rightWidth) / 2)
	left.SetPosition(startX, y)
	right.SetPosition(startX + leftWidth, y)


def _R1Yang(value):
	"""The amount as the one R1 yang price of the client ("500.000 Yang", root/uir1price.py
	) while the market is in the R1 look; None in the original look (its own texts stay)."""
	if _R1 is None:
		return None
	try:
		import uir1price
		return uir1price.FormatYang(int(value))
	except Exception:
		return None


def _YangText(value):
	text = _R1Yang(value)
	if text is not None:
		return text
	return "%s Yang\u016f" % format(int(value), ",").replace(",", " ")


def _UnitYangText(value, count):
	# the exact per-piece fraction stays; a whole amount as the one R1 yang price in the R1 look
	return marketpricedialog.UnitPriceText(value, count, _R1Yang(0) is not None)


def _R1PriceFont(label):
	"""R1: a price in the font of the one R1 yang price (Tahoma 12, PRAVIDLA-UI 9. 10.); its market colour stays."""
	try:
		import uir1
		import uir1price
		uir1.SetFont(label, uir1price.FONT)
	except Exception:
		pass


def _ItemName(vnum):
	try:
		item.SelectItem(int(vnum))
		return item.GetItemName()
	except:
		return "VNUM %d" % int(vnum)


def _Money(value):
	text = _R1Yang(value)
	if text is not None:
		return text
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


# The (folded name, name) of every obtainable item (marketobtainable), built once on the first suggestion;
# None until then. An empty tuple when the pack has no list (the engine search then suggests every item).
_OBTAINABLE_NAMES = None


def _ObtainableNames():
	global _OBTAINABLE_NAMES
	if _OBTAINABLE_NAMES is None:
		allowed = marketobtainable.Allowed()
		entries = []
		if allowed:
			from marketfilters import folded
			for vnum in sorted(allowed):
				try:
					# by vnum: no selection change for the tooltips, no syserr line for a missing vnum
					name = item.GetItemNameByVnum(int(vnum))
				except:
					continue
				if name:
					entries.append((folded(name), name))
		_OBTAINABLE_NAMES = tuple(entries)
	return _OBTAINABLE_NAMES


def _ItemSuggestions(text):
	"""The suggestion names for a typed item name: only obtainable items when the pack has the list,
	otherwise every item the engine knows."""
	entries = _ObtainableNames()
	if entries:
		from marketfilters import folded
		return marketobtainable.MatchNames(entries, text, folded, SEARCH_SUGGESTION_LIMIT)
	return list(item.GetItemNamesByName(text, SEARCH_SUGGESTION_LIMIT))


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


def _SyncGridItems(grid, shown, wanted):
	"""Bring a native item grid to `wanted` ({anchor slot: (vnum, count)}).

	wndMgr.ClearAllSlot() destroys the native slot definitions in this client, so
	the arranged 15x11 grid is kept and only item payloads are cleared or set.

	Only the slots that differ are touched: an unchanged slot keeps its icon, so
	adding, removing or paging never blanks the whole grid. `shown`
	mirrors what the native grid holds and is updated in place. Returns how many
	slots changed; RefreshSlot runs only when something did."""
	changed = 0
	for slotIndex in [slot for slot in shown if slot not in wanted]:
		grid.ClearSlot(slotIndex)
		del shown[slotIndex]
		changed += 1
	for slotIndex in sorted(wanted):
		payload = wanted[slotIndex]
		if shown.get(slotIndex) != payload:
			grid.SetItemSlot(slotIndex, payload[0], payload[1])
			shown[slotIndex] = payload
			changed += 1
	if changed:
		grid.RefreshSlot()
	return changed


# The suggestion list of the search field lies over the check boxes, the categories and the filters, so it is one
# opaque, framed popup above them. In R1 it is a small R1 window like the Bonusy panel of the character window: the
# opaque graphite base (uir1.BoardSkin 'window') under the panel texture, the R1 window frame, the rows in INK with
# the quiet graphite row line and hover band, and the narrow R1 scroll bar. In the original look the
# same in the crimson colours. Its own rows (not ui.ListBox) are sized to the font, so no row is cut, and the frame
# always has the popup's size.
SEARCH_SUGGESTION_WIDTH = 220
SEARCH_SUGGESTION_PAD = 5           # frame -> the first / last row, the left edge, the scroll bar
SEARCH_SUGGESTION_TEXT_X = 6        # the row's left edge -> its text
SEARCH_SUGGESTION_SCROLL_X = SEARCH_SUGGESTION_WIDTH - SEARCH_SUGGESTION_PAD - 12
# Original look: the crimson ember well and outline; the R1 look takes the R1 tokens (uir1tokens).
SEARCH_SUGGESTION_LEGACY = {"base": 0xFF0A0807, "line": 0xFF5C3A2C, "hover": 0xFF3A2219,
                            "text": 0xFFD8CBB5, "text_hover": 0xFFFFFFFF}
SEARCH_SUGGESTION_R1_FRAME = "window"   # the R1 window frame + panel texture (as Bonusy), not the dark inner well
SEARCH_SUGGESTION_ROW_LINE_ALPHA = 0.55  # the graphite row line of the Bonusy rows (uicharacterdetailskit)


def _FontCell(descriptor):
	"""Cell height of a client font "Family:12[b][a]" (uikit.FontCell, without importing the kit)."""
	digits = "".join(ch for ch in str(descriptor).rpartition(":")[2] if ch.isdigit())
	return int(digits or 12)


def _Signed(colour):
	colour = int(colour) & 0xFFFFFFFF
	return int(colour - 0x100000000 if colour >= 0x80000000 else colour)


def _PackedBar(parent, colour, alpha=1.0):
	bar = ui.Bar()
	bar.SetParent(parent)
	bar.AddFlag("not_pick")
	bar.SetColor(grp.GenerateColor(((colour >> 16) & 255) / 255.0, ((colour >> 8) & 255) / 255.0,
		(colour & 255) / 255.0, alpha))
	return bar


class _SuggestionRow(ui.Window):
	"""One suggestion: the hover band under its text; a click chooses it."""

	def __init__(self, owner, index):
		ui.Window.__init__(self)
		self.owner = owner
		self.index = index
		self.hovered = False
		self.SetParent(owner)
		look = owner.look
		self.line = None
		if look.r1 is not None:
			self.band = look.r1.Band(self, 0, 0, 1, 1, "normal")
			self.line = _PackedBar(self, look.line, SEARCH_SUGGESTION_ROW_LINE_ALPHA)
		else:
			self.band = _PackedBar(self, SEARCH_SUGGESTION_LEGACY["hover"])
			self.band.Hide()
		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.AddFlag("not_pick")
		self.label.SetFontName(look.font)
		self.label.SetVerticalAlignCenter()
		self.label.Show()
		self.text = ""
		self.SetOnRunMouseWheelEvent(owner.wheelEvent)

	def Place(self, y, width, height):
		self.SetPosition(0, y)
		self.SetSize(width, height)
		self.width = width
		if self.owner.look.r1 is not None:
			self.band.Resize(0, 0, width, height - 1)
			self.line.SetPosition(0, height - 1)
			self.line.SetSize(width, 1)
		else:
			self.band.SetPosition(0, 0)
			self.band.SetSize(width, height)
		self.label.SetPosition(SEARCH_SUGGESTION_TEXT_X, height // 2)
		self.SetText(self.text)

	def SetLineShown(self, shown):
		"""The row line under every row but the last one shown."""
		if self.line is not None:
			if shown:
				self.line.Show()
			else:
				self.line.Hide()

	def SetText(self, text):
		self.text = text
		room = getattr(self, "width", SEARCH_SUGGESTION_WIDTH) - 2 * SEARCH_SUGGESTION_TEXT_X
		if self.owner.look.r1 is not None:
			self.owner.look.r1.Fit(self.label, text, room)
		else:
			self.label.SetText(text)
			self.label.SetLimitWidth(room)
		self._Paint()

	def _Paint(self):
		look = self.owner.look
		if look.r1 is not None:
			self.band.SetState("hover" if self.hovered else "normal")
		elif self.hovered:
			self.band.Show()
		else:
			self.band.Hide()
		self.label.SetPackedFontColor(_Signed(look.text_hover if self.hovered else look.text))

	def OnMouseOverIn(self):
		self.hovered = True
		self._Paint()

	def OnMouseOverOut(self):
		self.hovered = self.pressed = False
		self._Paint()

	def OnMouseLeftButtonDown(self):
		self.pressed = True
		return True

	def OnMouseLeftButtonUp(self):
		# Only a press that started on this row chooses it (not a release after dragging from elsewhere).
		pressed, self.pressed = getattr(self, "pressed", False), False
		if pressed:
			self.owner.Click(self.index)
		return True


class _SuggestionLook(object):
	"""The colours, the font and the row height of the list in the look the market is built in."""

	def __init__(self):
		self.r1 = None
		if _R1 is not None:
			import uir1
			import uir1tokens
			self.r1 = uir1
			self.font = _R1.kit.font("text_s")
			# Opaque graphite of the R1 windows (BoardSkin 'window' 0xFF141213), the row text and line of Bonusy.
			self.base = uir1.BoardSkin.BASE_COLOR["window"]
			self.text, self.text_hover = uir1tokens.INK, uir1tokens.IVORY
			self.line = uir1tokens.LINE
		else:
			self.font = fontconfig.FontForRole(fontconfig.ROLE_BODY)
			self.base = SEARCH_SUGGESTION_LEGACY["base"]
			self.text = SEARCH_SUGGESTION_LEGACY["text"]
			self.text_hover = SEARCH_SUGGESTION_LEGACY["text_hover"]
			self.line = SEARCH_SUGGESTION_LEGACY["line"]
		# The font cell and 3 px above and below it: diacritics (Š, Ř) and descenders stay inside the row.
		self.step = _FontCell(self.font) + 6


class _SuggestionList(ui.Window):
	"""The rows of the suggestion list with the ui.ListBox calls the dropdown makes (ClearItem, InsertItem,
	GetStepSize, SetSize, SetBasePos, SetEvent): only as many rows as fit, filled from the base position."""

	def __init__(self, owner, look):
		ui.Window.__init__(self)
		self.owner = owner
		self.look = look
		self.wheelEvent = None
		self.items = []
		self.rows = []
		self.basePos = 0
		self.event = None
		self.SetParent(owner)
		self.AddFlag("not_pick")

	def SetEvent(self, event):
		self.event = event

	def SetOnRunMouseWheelEvent(self, event):
		self.wheelEvent = event
		ui.Window.SetOnRunMouseWheelEvent(self, event)
		for row in self.rows:
			row.SetOnRunMouseWheelEvent(event)

	def GetStepSize(self):
		return self.look.step

	def ClearItem(self):
		self.items = []
		self.basePos = 0
		self._Fill()

	def InsertItem(self, key, text):
		self.items.append((key, text))

	def SetSize(self, width, height):
		ui.Window.SetSize(self, width, height)
		visible = max(0, int(height) // self.look.step)
		while len(self.rows) < visible:
			self.rows.append(_SuggestionRow(self, len(self.rows)))
		for index, row in enumerate(self.rows):
			row.Place(index * self.look.step, int(width), self.look.step)
		self.visible = visible
		self._Fill()

	def SetBasePos(self, pos):
		self.basePos = max(0, int(pos))
		self._Fill()

	def _Fill(self):
		visible = getattr(self, "visible", 0)
		for index, row in enumerate(self.rows):
			position = self.basePos + index
			if index < visible and position < len(self.items):
				row.SetText(self.items[position][1])
				row.SetLineShown(index + 1 < visible and position + 1 < len(self.items))
				row.Show()
			else:
				row.hovered = False
				row.Hide()

	def Click(self, index):
		position = self.basePos + index
		if self.event and 0 <= position < len(self.items):
			key, text = self.items[position]
			self.event(key, text)


class SearchSuggestionDropdown(ui.Window):
	def __init__(self, parent, selectEvent, x=10, y=31):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.AddFlag("float")             # SetTop on Open: above every control of the window
		self.look = _SuggestionLook()
		# Under everything: one opaque well over the whole popup, so nothing beneath it shows through.
		self.base = _PackedBar(self, self.look.base)
		self.base.SetPosition(0, 0)
		self.base.Show()
		if self.look.r1 is not None:
			self.frame = self.look.r1.Frame(self, 0, 0, SEARCH_SUGGESTION_WIDTH, 24, SEARCH_SUGGESTION_R1_FRAME)
			self.lines = []
		else:
			self.frame = None
			self.lines = [_PackedBar(self, SEARCH_SUGGESTION_LEGACY["line"]) for unused in range(4)]
			for line in self.lines:
				line.Show()
		self.selectEvent = selectEvent
		self.listBox = _SuggestionList(self, self.look)
		self.listBox.SetPosition(SEARCH_SUGGESTION_PAD + 1, SEARCH_SUGGESTION_PAD)
		self.listBox.SetEvent(self._Select)
		self.listBox.SetOnRunMouseWheelEvent(self._OnMouseWheel)
		self.listBox.Show()
		self.SetOnRunMouseWheelEvent(self._OnMouseWheel)
		self.scrollBar = SettingsScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(SEARCH_SUGGESTION_SCROLL_X, SEARCH_SUGGESTION_PAD)
		self.scrollBar.SetScrollEvent(self._OnScroll)
		self.scrollBar.Hide()
		self.startIndex = 0
		self.itemCount = 0
		self.SetSize(SEARCH_SUGGESTION_WIDTH, 24)
		self.Hide()

	def SetSize(self, width, height):
		"""The well and the outline always cover the popup's whole size."""
		ui.Window.SetSize(self, width, height)
		self.base.SetSize(width, height)
		if self.frame is not None:
			self.frame.Resize(width, height)
		for line, (x, y, w, h) in zip(self.lines, ((0, 0, width, 1), (0, height - 1, width, 1),
				(0, 0, 1, height), (width - 1, 0, 1, height))):
			line.SetPosition(x, y)
			line.SetSize(w, h)

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
		# The rows end 4 px before the scroll bar, which keeps 5 px to the right edge.
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


# The market's column header: ((locale key, default, centre x in the 541 px row), ...).
MARKET_COLUMNS = (
	("VIRTUAL_MARKET_ITEM", "P\u0158EDM\u011aT", ITEM_COLUMN_CENTER_X),
	("VIRTUAL_MARKET_COUNT", "PO\u010cET", COUNT_CENTER_X),
	("VIRTUAL_MARKET_PRICE", "CENA", PRICE_COLUMN_CENTER_X),
	("VIRTUAL_MARKET_SELLER", "HR\u00c1\u010c", SELLER_CENTER_X))


def DataHeader(parent, x, y, columns):
	"""The column header of the market rows (surface/data_header.png, centred labels); the market results and the
	"Můj obchod" sale history use it. Returns (board, label, ...): the caller keeps them all (the client destroys a
	widget nobody references at once)."""
	board = _Image(parent, x, y, CRIMSON_MARKET_DIR + "surface/data_header.png")
	widgets = [board]
	for key, default, centerX in columns:
		label = _Label(board, centerX, HEADER_TEXT_CENTER_Y, _Text(key, default), 0xffeadfc8)
		label.SetHorizontalAlignCenter()
		label.SetVerticalAlignCenter()
		widgets.append(label)
	return tuple(widgets)


class CrimsonMarketRow(ui.Window):
	"""One market result row: check box, the item in its slot, name, count, price (total over per piece), the
	seller link and the envelope. The "Můj obchod" sale history draws its rows with it too: checkbox=False,
	lead=(date, time) in the check box's place, rowTooltip=False (the item tooltip only over the slot),
	messageHint for the envelope and compactItem=True: the row keeps the base height (BASE_ROW_HEIGHT, the native
	result surface) and a tall item (1 x 2, 1 x 3) is drawn in ONE slot cell, its icon scaled into the cell with
	uir1.FitIcon (docs/ALTHEA_R1_KIT.md, Item slots)."""

	def __init__(self, parent, y, vnum, itemCount, priceText, metaText,
			sellerName, actionText, actionEvent, payload, messageEvent=None,
			tooltipIn=None, tooltipOut=None, messagePayload=None,
			sellerSearchEvent=None, sellerSearchPayload=None, selected=False,
			selectionMode=True, checkbox=True, rowTooltip=True, lead=None,
			messageHint=None, compactItem=False):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(4, y)
		itemHeight = _ItemHeight(vnum)
		slotHeight = 1 if compactItem else itemHeight
		rowHeight = marketlayout.RowHeight(slotHeight)
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
		if rowTooltip:
			self.background.SAFE_SetOverInEvent(self._TooltipIn)
			self.background.SAFE_SetOverOutEvent(self._TooltipOut)
		self.background.Show()

		self.checkbox = None
		if checkbox:
			self.checkbox = _CrimsonCheckboxButton(
				self, ACTION_X, 18 + centerOffset,
				lambda: self._RequestSelected(True),
				lambda: self._RequestSelected(False))
		self.action = self.checkbox
		self.SetSelected(selected)

		shift = 0
		if lead:
			shift = ROW_LEAD_SHIFT
			top, bottom = lead
			topLabel = _Label(
				self, ROW_LEAD_CENTER_X, PRICE_PRIMARY_CENTER_Y + centerOffset, top, 0xffeadfc8)
			topLabel.SetHorizontalAlignCenter()
			topLabel.SetVerticalAlignCenter()
			self.labels.append(topLabel)
			bottomLabel = _SmallLabel(
				self, ROW_LEAD_CENTER_X, PRICE_UNIT_CENTER_Y + centerOffset, bottom)
			bottomLabel.SetHorizontalAlignCenter()
			bottomLabel.SetVerticalAlignCenter()
			self.labels.append(bottomLabel)

		self.itemSlot = ui.GridSlotWindow()
		self.itemSlot.SetParent(self)
		self.itemSlot.SetPosition(ITEM_SLOT_X + shift, 10)
		self.itemSlot.ArrangeSlot(0, 1, slotHeight, 32, 32, 0, 0)
		self.itemSlot.SetSlotBaseImage(
			_SlotBase(),
			1.0, 1.0, 1.0, 1.0)
		self.itemSlot.SetOverInItemEvent(self._TooltipIn)
		self.itemSlot.SetOverOutItemEvent(self._TooltipOut)
		self.itemSlot.SetOverInEvent(self._TooltipIn)
		self.itemSlot.SetOverOutEvent(self._TooltipOut)
		self.itemSlot.SetSelectItemSlotEvent(self._ToggleSelection)
		self.itemSlot.SetSelectEmptySlotEvent(self._ToggleSelection)
		self.itemIcon = None
		self.itemHit = None
		if slotHeight == itemHeight:
			self.itemSlot.SetItemSlot(0, int(vnum))
		self.itemSlot.RefreshSlot()
		self.itemSlot.Show()
		if slotHeight != itemHeight:
			self._CompactItem(vnum, ITEM_SLOT_X + shift, 10)

		name = _ItemName(vnum)
		if len(name) > 24:
			name = name[:23] + "..."
		nameLabel = _Label(
			self, ITEM_NAME_X + shift, ROW_TEXT_CENTER_Y + centerOffset, name, 0xffeadfc8)
		nameLabel.SetVerticalAlignCenter()
		nameLabel.SetLimitWidth(ITEM_NAME_SAFE_WIDTH - shift)
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
		if _R1 is not None:
			_R1PriceFont(priceLabel)
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
			self.message.SetToolTipText(messageHint or _Text(
				"VIRTUAL_MARKET_MESSAGE_SELLER", "Napsat prodejci"))
		self.Show()

	def _CompactItem(self, vnum, x, y):
		"""A tall item in the one slot cell: its icon scaled into the cell (not pickable) and a hit box over the cell
		that shows the item tooltip, as the slot does for a one-cell item."""
		import uir1
		item.SelectItem(int(vnum))
		self.itemIcon = ui.ExpandedImageBox()
		self.itemIcon.SetParent(self)
		self.itemIcon.AddFlag("not_pick")
		uir1.FitIcon(self.itemIcon, item.GetIconImageFileName(), x, y,
			marketlayout.SLOT_SIZE, marketlayout.SLOT_SIZE)
		self.itemIcon.Show()
		self.itemHit = ui.Window()
		self.itemHit.SetParent(self)
		self.itemHit.SetPosition(x, y)
		self.itemHit.SetSize(marketlayout.SLOT_SIZE, marketlayout.SLOT_SIZE)
		self.itemHit.SAFE_SetOverInEvent(self._TooltipIn)
		self.itemHit.SAFE_SetOverOutEvent(self._TooltipOut)
		self.itemHit.Show()

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
			if self.checkbox:
				self.checkbox.Down()
		else:
			self.background.SetUp()
			if self.checkbox:
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
		self.itemIcon = None
		self.itemHit = None
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
		self.ownerListingsNextAt = 0.0
		self.ownerListingsAttempts = 0
		self.searchMode = "item"
		self.sellerExact = False
		self.searchChangedAt = 0.0
		self.lastSuggestionText = ""
		self.pendingSuggestionText = ""
		self.marketSearched = False
		self.selectedPurchases = {}
		self.batchPurchaseAvailable = hasattr(net, "SendVirtualMarketBatchPurchase")
		self.categoryStartIndex = 0
		self.expandedCategory = -1
		self.closedChoice = None
		self.railOpenAt = 0.0
		self.subcategoryEntries = []
		self.offer = None
		self.offerUsesPreviousPrice = False
		self.offerAll = None
		self.retryButtonLabel = None
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
		self.ownerPageCount = 1
		self.ownerHasMore = False
		self.gridSlotMap = {}
		# The owner grid is a model (ownerGridPages) rendered once per frame
		# as a slot diff (ownerGridShown -> ownerGridWanted); a paged reload is held.
		self.ownerGridPages = [[]]
		self.ownerGridShown = {}
		self.ownerGridWanted = {}
		self.ownerGridWantedMap = {}
		self.ownerGridDirty = False
		self.ownerModelComplete = False
		self.ownerReloadHoldUntil = 0.0
		# A confirmed add, remove, move or price change is drawn at once from the
		# server's answer (ownerLocalChanges: listing id -> (reload serial, record or
		# None)); the paged reload that follows only confirms it. ownerBaseLayout is
		# the last complete native layout, ownerLayout the one on screen.
		self.ownerReloadSerial = 0
		# False after the first page of a reload failed: the native list is then empty,
		# so the grid keeps the last complete layout (and a refused reload is asked again).
		self.ownerNativeOk = True
		self.ownerNextPageDelay = OWNER_LISTINGS_NEXT_PAGE_DELAY
		self.ownerReloadRetryAt = 0.0
		self.ownerHoverSlot = None
		self.ownerHoverRefresh = False
		self.ownerReloadRetries = 0
		self.ownerLocalChanges = {}
		self.ownerBaseLayout = {}
		self.ownerLayout = {}
		self.pendingListingMove = None
		self.boxGridShown = {}
		self.claimAllController = _SequentialClaimController()
		self.lastLeaseRefresh = 0.0
		self.lastBoxRefresh = 0.0
		self.ownerShopLastGood = None
		self.ownerShopRetryAt = 0.0
		self.ownerShopRetryAttempts = 0
		self.nextClaimAt = 0.0
		self.operationRetryAt = 0.0
		self.operationRetrySender = None
		self.operationRetryAttempts = 0
		self.queuedClaims = []
		self.activeClaim = None
		self.boxStateSignature = None
		self.retryEvent = None
		self.confirmEvent = None
		self.look = "legacy"
		self.r1Skin = None
		self.r1Failed = False
		# "Můj obchod": the shop grid (listings) or its sale history (root/uimarketsaleshistory.py).
		self.ownerView = OWNER_VIEW_LISTINGS
		self.salesHistory = None
		self.ownerViewSwitch = None
		self._BuildLook()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def _BuildLook(self):
		"""The R1 look (root/uivirtualmarketr1.py) unless the original one is wanted; the original look when building
		the R1 look raises (traced, not tried again). Both looks build the same controls and events."""
		theme = None
		if not self.r1Failed:
			try:
				theme = _R1Theme()
			except Exception:
				theme = None
		if theme is not None:
			try:
				_SetTheme(theme)
				self._Build()
				import uivirtualmarketr1
				self.r1Skin = uivirtualmarketr1.MarketSkin(self, theme)
				self.look = "r1"
				return
			except Exception:
				import uir1
				uir1.TraceFailure("the virtual market")
				self.r1Failed = True
				self._DropLook()
		_SetTheme(None)
		self._Build()
		self.look = "legacy"

	def _DropLook(self):
		"""Forgets a (partly) built look: every control hidden and dropped, the original board frame back."""
		self._DestroySalesHistory()
		skin, self.r1Skin = self.r1Skin, None
		if skin is not None:
			try:
				skin.Restore()
			except Exception:
				pass
		try:
			self._ClearRows()
		except Exception:
			self.rows = []
		for name in ("advancedFilters", "confirm", "priceDialog", "suggestionDropdown"):
			widget = getattr(self, name, None)
			if widget is not None:
				try:
					widget.Hide()
					if name == "advancedFilters":
						widget.Destroy()
				except Exception:
					pass
				setattr(self, name, None)
		keep = set(id(widget) for widget in (getattr(self, "Corners", None) or []) + (getattr(self, "Lines", None) or []))
		keep.update((id(getattr(self, "Base", None)), id(getattr(self, "titleBar", None)), id(self.interface)))
		for value in list(self.__dict__.values()):
			for widget in (value if isinstance(value, (list, tuple)) else (value,)):
				if hasattr(widget, "SetParent") and hasattr(widget, "Hide") and id(widget) not in keep:
					try:
						widget.Hide()
					except Exception:
						pass
		_SetTheme(None)
		self.look = "legacy"

	def Show(self):
		if not self.IsShow():
			self._SyncLook()
		ui.BoardWithTitleBar.Show(self)

	def _SyncLook(self):
		"""Settings -> "Starý vzhled" / "Nový vzhled" take effect when the closed window opens again: it is built
		again in the chosen look (the search state and the native snapshots are kept; the tab refresh redraws)."""
		wanted = "legacy"
		if not self.r1Failed:
			try:
				wanted = "r1" if _R1Theme() is not None else "legacy"
			except Exception:
				wanted = "legacy"
		if wanted == self.look:
			_SetTheme(self.r1Skin.theme if self.r1Skin is not None else None)
			return
		self._DropLook()
		self._BuildLook()

	def _Build(self):
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.SetTitleName(_Text("VIRTUAL_MARKET_TITLE", "Virtu\u00e1ln\u00ed trh"))
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
			self.body, RETRY_BUTTON_X, RETRY_BUTTON_Y,
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
			"VIRTUAL_MARKET_VNUM_PLACEHOLDER", "N\u00e1zev \u010di \u010d\u00edslo"))
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

		if _R1 is not None:
			import uir1
			import uir1tokens
			self.marketFooter = uir1.Frame(
				self.body, FOOTER_BAR_X, FOOTER_BAR_Y,
				FOOTER_BAR_WIDTH, FOOTER_BAR_HEIGHT, "panel")
		else:
			self.marketFooter = _Image(
				self.body, MARKET_FOOTER_X, MARKET_FOOTER_Y,
				CRIMSON_MARKET_DIR + "panel/market_footer.png")
		self.selectionCountLabel = _Label(
			self.body, SELECTION_LABEL_X, FOOTER_CENTER_Y,
			"", 0xffeadfc8)
		self.totalPrefixLabel = _Label(
			self.body, TOTAL_RIGHT_X, FOOTER_CENTER_Y,
			"Celkem: ", 0xffeadfc8)
		self.totalAmountLabel = _Label(
			self.body, TOTAL_RIGHT_X, FOOTER_CENTER_Y,
			"")
		self.totalAmountLabel.SetFontColor(1.0, 1.0, 0.0)
		if _R1 is not None:
			# The count and "Celkem:" in the text_s role, the amount as the R1 yang price (the tahoma role).
			_FooterText(self.selectionCountLabel, "text_s", uir1tokens.INK)
			_FooterText(self.totalPrefixLabel, "text_s", uir1tokens.INK)
			_FooterText(self.totalAmountLabel, "tahoma", uir1tokens.IVORY)
			self.buySelectedButton = uir1.Button(
				self.body, _R1.kit, BUY_SELECTED_X, BUY_SELECTED_Y, BUY_SELECTED_WIDTH,
				_Text("VIRTUAL_MARKET_BUY_SELECTED", "Koupit vybran\u00e9"),
				primary=True, event=self._ConfirmSelectedPurchases)
		else:
			for label in (self.selectionCountLabel, self.totalPrefixLabel, self.totalAmountLabel):
				_FooterText(label, None, None)
			self.buySelectedButton = _CrimsonButton(
				self.body, LEGACY_BUY_X, LEGACY_BUY_Y, "button/buy",
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
		self.categoryChevrons = []
		for index, (localeKey, fallback, iconName, itemType, itemSubtype) in enumerate(MARKET_CATEGORIES):
			button, icon, label = _ClassicTab(
				self.categoryViewport, 0, index * CATEGORY_STEP_Y,
				_Text(localeKey, fallback), iconName,
				lambda selected=index: self._SelectMarketCategory(selected))
			button.SetOnRunMouseWheelEvent(self._OnCategoryMouseWheel)
			self.filterButtons.append(button)
			self.filterIcons.append(icon)
			self.categoryLabels.append(label)
			chevron = _Image(button, CATEGORY_CHEVRON_X, CATEGORY_CHEVRON_Y,
				CATEGORY_CHEVRON_PATH % "right")
			chevron.Hide()
			self.categoryChevrons.append(chevron)
		self.expandedCategory = -1
		self.closedChoice = None
		self.subcategoryEntries = []
		self.subcategoryButtons = []
		self.subcategoryLabels = []
		for position in range(SUBCATEGORY_POOL):
			self._SubcategoryButton(position)
		self.categoryScrollBar = SettingsScrollBar()
		self.categoryScrollBar.SetParent(self)
		self.categoryScrollBar.SetPosition(
			CATEGORY_SCROLL_X, CATEGORY_START_Y)
		self.categoryScrollBar.SetScrollBarSize(CATEGORY_VIEW_HEIGHT)
		self.categoryScrollBar.SetScrollEvent(self._OnCategoryScroll)
		# The wheel scrolls the categories over the rail and its bar only, never over the item grids beside them.
		uiwheel.Bind(self.categoryScrollBar, self.categoryViewport, self._CategoryWheelStep)
		self._RefreshCategoryViewport()

		self.prevButton = _CrimsonIconButton(
			self.body, PAGINATION_X, PAGINATION_Y,
			"button/pagination", self._PreviousPage,
			"icon/arrow_left.png",
			PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.pageButtons = []
		for slotIndex in range(PAGINATION_SLOTS):
			button = _CrimsonButton(
				self.body, PAGINATION_X + PAGINATION_STEP * (slotIndex + 1), PAGINATION_Y,
				"button/pagination",
				lambda page=slotIndex: self._GoMarketPage(page),
				"", True)
			self.pageButtons.append(button)
		self.nextButton = _CrimsonIconButton(
			self.body, PAGINATION_X + PAGINATION_STEP * (PAGINATION_SLOTS + 1), PAGINATION_Y,
			"button/pagination", self._NextPage,
			"icon/arrow_right.png",
			PAGINATION_ICON_X, PAGINATION_ICON_Y)
		self.marketPage = _Label(self.body, PAGINATION_X + PAGINATION_WIDTH // 2, PAGINATION_Y + 3, "")
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

		self.headers = DataHeader(self.body, 4, 0, MARKET_COLUMNS)
		self.headerBoard = self.headers[0]

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
		# The page arrows start hidden (page 1 of 1) and only _RefreshOwnerPageArrows shows them, so neither one can
		# flash before the first refresh of the owner pages.
		self.ownerPrevButton.Hide()
		self.ownerNextButton.Hide()
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
		self.ownerGrid.SetSlotBaseImage(_SlotBase(), 1.0, 1.0, 1.0, 1.0)
		self.ownerGrid.SetSelectEmptySlotEvent(self._AttachOffer)
		self.ownerGrid.SetSelectItemSlotEvent(self._SelectOwnerSlot)
		self.ownerGrid.SetUnselectItemSlotEvent(self._UseOwnerSlot)
		self.ownerGrid.SetOverInItemEvent(self._OverInOwnerSlot)
		self.ownerGrid.SetOverOutItemEvent(self._OverOutOwnerSlot)
		self.ownerGrid.SetOverInEvent(self._OverInOwnerSlot)
		self.ownerGrid.SetOverOutEvent(self._OverOutOwnerSlot)
		self.ownerGrid.Show()

		self.ownerValueStrip = _Image(self.ownerGridPanel, ACCOUNT_TOOLBAR_LOCAL_X, ACCOUNT_VALUE_STRIP_Y, CRIMSON_MARKET_DIR + "panel/account_toolbar.png")
		self.ownerTotalPrefix = _Label(self.ownerGridPanel, 90, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2, _Text("VIRTUAL_MARKET_TOTAL_LISTING_VALUE", "Celková hodnota nabídek: "), 0xffeadfc8)
		self.ownerTotalPrefix.SetVerticalAlignCenter()
		self.ownerTotalValue = _Label(self.ownerGridPanel, 250, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2, _YangText(0), 0xffeadfc8)
		self.ownerTotalValue.SetFontColor(*CURRENCY_YANG_COLOR)
		self.ownerTotalValue.SetVerticalAlignCenter()
		_CenterAccountValuePair(self.ownerTotalPrefix, self.ownerTotalValue, ACCOUNT_PAGE_CENTER_X, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2)
		# The market shortcuts (Shift + right-click and the others): the "i" at the right end of the value strip.
		self.ownerHelp = _MarketHelpDot(self.ownerGridPanel,
			ACCOUNT_TOOLBAR_LOCAL_X + ACCOUNT_TOOLBAR_WIDTH - MARKET_HELP_ICON_SIZE - 12,
			ACCOUNT_VALUE_STRIP_Y + (ACCOUNT_VALUE_STRIP_HEIGHT - MARKET_HELP_ICON_SIZE) // 2)

		# No shop-name field: Althea has no offline shops standing in the world and the market shows the seller's
		# character name (market_shop.owner_name), so a shop name would never be seen. _CreateShop sends the
		# character name because the market protocol still requires a non-empty name. Title, hint and button sit
		# where the old title-to-button block was centred (y 75..229, centre 152).
		self.ownerClosedPanel = _Image(self.body, ACCOUNT_PANEL_X, ACCOUNT_CONTENT_Y, CRIMSON_MARKET_DIR + "panel/closed_shop.png")
		self.ownerClosedTitle = _Label(self.ownerClosedPanel, 271, CLOSED_TITLE_Y, _Text("VIRTUAL_MARKET_CLOSED_TITLE", "Tvůj obchod zatím není otevřen."), 0xffffd500)
		self.ownerClosedTitle.SetHorizontalAlignCenter()
		self.ownerClosedHint = _Label(self.ownerClosedPanel, 271, CLOSED_HINT_Y, _Text("VIRTUAL_MARKET_CLOSED_HINT_NO_NAME", "Založ si obchod na 5 dní."), 0xffeadfc8)
		self.ownerClosedHint.SetHorizontalAlignCenter()
		self.createButton = _CrimsonPrimaryButton(
			self.ownerClosedPanel, CREATE_BUTTON_X, CREATE_BUTTON_Y,
			_Text("VIRTUAL_MARKET_CREATE", "Založit na 5 dní"), self._CreateShop)

		self.ownerListingActions = (self.ownerToolbar, self.ownerCreditField, self.ownerCreditPrefix, self.ownerCredit, self.ownerPrevButton, self.ownerNextButton, self.ownerPage, self.withdrawButton, self.renewButton, self.ownerRepriceButton, self.ownerCancelButton, self.closeButton, self.ownerGrid, self.ownerValueStrip, self.ownerTotalPrefix, self.ownerTotalValue, self.ownerHelp)
		self.ownerActiveToolbarWidgets = (self.ownerCreditField, self.ownerCreditPrefix, self.ownerCredit, self.ownerPage, self.withdrawButton, self.renewButton, self.ownerRepriceButton, self.ownerCancelButton, self.closeButton)
		self.ownerWidgets = (self.ownerHeader, self.ownerGridPanel, self.ownerClosedPanel)
		self._BuildSalesHistory()

	def _BuildSalesHistory(self):
		"""Nabídky | Historie in the owner header and the history view. Optional: if building it raises, the owner
		tab stays as it was (no switch) and the market keeps its look."""
		self._DestroySalesHistory()
		try:
			import uimarketsaleshistory
			module = sys.modules[__name__]
			self.ownerViewSwitch = uimarketsaleshistory.ViewSwitch(module, self.ownerHeader, self._SelectOwnerView)
			self.ownerViewSwitch.Hide()
			self.salesHistory = uimarketsaleshistory.SalesHistoryPanel(
				module, self.body, ACCOUNT_PANEL_X, ACCOUNT_CONTENT_Y,
				tooltip=ui.__mem_func__(self._SalesHistoryTooltip),
				whisper=ui.__mem_func__(self._WhisperAboutSale),
				searchPlayer=ui.__mem_func__(self._SearchSeller))
		except Exception as error:
			# Kept silent (no syserr line per window build); the owner tab simply has no switch.
			self.salesHistoryError = repr(error)
			self._DestroySalesHistory()
		self.ownerView = OWNER_VIEW_LISTINGS

	def _SalesHistoryTooltip(self):
		"""The item tooltip the history rows fill (the same one as the market rows)."""
		return getattr(getattr(self, "interface", None), "tooltipItem", None)

	def _WhisperAboutSale(self, payload):
		"""The envelope of a history row: a message to the buyer with the sold item, like "Napsat prodejci"."""
		buyerName, vnum = payload
		if not buyerName:
			return
		if hasattr(self.interface, "OpenWhisperWithMarketItem"):
			self.interface.OpenWhisperWithMarketItem(buyerName, _ItemName(int(vnum)))
		else:
			self.interface.OpenWhisperDialog(buyerName)

	def _DestroySalesHistory(self):
		for name in ("salesHistory", "ownerViewSwitch"):
			widget = getattr(self, name, None)
			setattr(self, name, None)
			if widget is not None:
				try:
					widget.Destroy()
				except Exception:
					pass

	def _SalesHistoryAvailable(self):
		if self.salesHistory is None or self.ownerViewSwitch is None:
			return False
		try:
			import marketsaleshistory
			return bool(marketsaleshistory.RECEIVER.available)
		except Exception:
			return False

	def _SelectOwnerView(self, view):
		if view not in (OWNER_VIEW_LISTINGS, OWNER_VIEW_HISTORY) or view == self.ownerView:
			return
		if view == OWNER_VIEW_HISTORY and not self._SalesHistoryAvailable():
			return
		self.ownerView = view
		if view == OWNER_VIEW_HISTORY:
			self._CancelOwnerDrag()
			self._HideTooltip()
			self._ApplyOwnerView()
			self.salesHistory.Open()
		else:
			self._ApplyOwnerView()
			self._RefreshOwner(True)

	def _ApplyOwnerView(self):
		"""Shows the switch (server offers the history) and, in the history view, the history instead of the shop
		grid / closed-shop panel. Returns True while the history is shown."""
		available = self._SalesHistoryAvailable()
		if not available:
			self.ownerView = OWNER_VIEW_LISTINGS
		owner = self.currentTab == TAB_OWNER
		if self.ownerViewSwitch is not None:
			self.ownerViewSwitch.SetValue(self.ownerView)
			self.ownerViewSwitch.Show() if available and owner else self.ownerViewSwitch.Hide()
		history = owner and self.ownerView == OWNER_VIEW_HISTORY
		if self.salesHistory is not None:
			if history:
				self.ownerGridPanel.Hide()
				self.ownerClosedPanel.Hide()
				if not self.salesHistory.IsShow():
					self.salesHistory.Show()
			else:
				self.salesHistory.Hide()
		return history

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
		self.boxGrid.SetSlotBaseImage(_SlotBase(), 1.0, 1.0, 1.0, 1.0)
		self.boxGrid.SetUnselectItemSlotEvent(self._UseBoxSlot)
		self.boxGrid.SetUnselectEmptySlotEvent(self._UseBoxSlot)
		self.boxGrid.SetOverInItemEvent(self._OverInBoxSlot)
		self.boxGrid.SetOverOutItemEvent(self._HideTooltip)
		self.boxGrid.SetOverInEvent(self._OverInBoxSlot)
		self.boxGrid.SetOverOutEvent(self._HideTooltip)
		self.boxGrid.Show()
		self.boxWidgets = (self.boxHeader, self.boxGridPanel)

	def Destroy(self):
		self._DestroySalesHistory()
		self._StopClaimAll()
		self._CancelOwnerDrag()
		self._ClearRows()
		self._HideTooltip()
		if getattr(self, "r1Skin", None):
			self.r1Skin.Destroy()
		self.r1Skin = None
		if getattr(self, "advancedFilters", None):
			self.advancedFilters.Destroy()
		if getattr(self, "ownerHelp", None):
			self.ownerHelp.Destroy()
		self.ownerHelp = None
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
		self.categoryChevrons = ()
		self.subcategoryButtons = ()
		self.subcategoryLabels = ()
		self.subcategoryEntries = []
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
			"category_expanded": int(self.expandedCategory),
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
		self._ExpandCategory(int(state.get("category_expanded", -1)))
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
				_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed nab\u00eddek..."),
				_Text("VIRTUAL_MARKET_LOADING_HINT",
					"Hled\u00e1 se na trhu."))
			if self.marketSearched:
				if not self._RepeatMarketSearch():
					self._SetStatus(_Text(
						"VIRTUAL_MARKET_REQUEST_BUSY",
						"Te\u010f to nejde. Zkus to za chv\u00edli."),
						self._RepeatMarketSearch)
				else:
					self._SetStatus(_Text(
						"VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed..."))
			else:
				self._BrowseMarket()
		if tab != TAB_OWNER:
			net.SendVirtualMarketOwnerShop()
		self.SetFocus()
		return True

	def Close(self):
		self._StopClaimAll()
		if getattr(self, "offerAll", None):
			self._StopOfferAll(None, False)    # no reload: the window closes or leaves the owner tab
		self._CancelOwnerDrag()
		self.searchRetryAt = 0.0
		self.searchRetryEvent = None
		self.ownerListingsNextAt = 0.0
		self.repricingListingId = 0
		self.priceDialog.SetTitle(_Text(
			"PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE", "Prodejn\u00ed cena"))
		self.searchInput.KillFocus()
		self.KillFocus()
		self.confirm.Hide()
		self.priceDialog.Hide()
		self._ClearOffer()
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

	def _RefreshOwnerPageArrows(self, isOpen=True):
		"""Shows the owner page arrows from the page state alone: the left one never on page 1, the right one only
		while a further page exists. A shown/hidden arrow is left alone, so a periodic refresh never toggles it."""
		showPrev = bool(isOpen) and self.currentPage > 0
		showNext = bool(isOpen) and (self.currentPage + 1 < self.ownerPageCount or self.ownerHasMore)
		for button, visible in ((self.ownerPrevButton, showPrev), (self.ownerNextButton, showNext)):
			if bool(button.IsShow()) != visible:
				button.Show() if visible else button.Hide()

	def _SelectTab(self, tab, force=False, loadMarket=True):
		if not force and self.currentTab == tab:
			if tab == TAB_MARKET and loadMarket:
				self._BrowseMarket()
			return
		if self.currentTab == TAB_OWNER and tab != TAB_OWNER:
			self._CancelOwnerDrag()
			if getattr(self, "offerAll", None):
				self._StopOfferAll(None, False)    # no reload: the window closes or leaves the owner tab
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
		if getattr(self, "salesHistory", None) is not None:
			self._ApplyOwnerView()
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
						"Trh se teď nepodařilo obnovit."), self._RepeatMarketSearch)
			else:
				self._BrowseMarket()
		elif tab == TAB_OWNER:
			net.SendVirtualMarketOwnerShop()
			self._ReloadOwnerListings()
			self._RefreshOwner(True)
			if getattr(self, "ownerView", None) == "history" and getattr(self, "salesHistory", None):
				self.salesHistory.Open()
		elif tab == TAB_DELIVERIES:
			self.boxTitleBase = _Text("VIRTUAL_MARKET_DELIVERIES_TITLE", "Doru\u010den\u00e9 n\u00e1kupy")
			self.boxTitle.SetText(self.boxTitleBase)
			net.SendVirtualMarketBuyerDeliveries()
			self._RefreshBox()
		else:
			self.boxTitleBase = _Text("VIRTUAL_MARKET_RETURNS_TITLE", "Vr\u00e1cen\u00e9 p\u0159edm\u011bty")
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

	def _SetStatus(self, text, retryEvent=None, preserveMessage=False, readStatus=False):
		if preserveMessage:
			previous = getattr(self, "statusText", "")
			loading = _Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed...")
			if previous != loading and not getattr(self, "statusIsRead", False):
				text = previous
				retryEvent = self.retryEvent
		if getattr(self, "offerAll", None) and not retryEvent:
			# "Vložit vše": the status button cancels the remaining stacks, the line shows the progress.
			retryEvent = self._CancelOfferAll
			if not text:
				text = self._OfferAllProgressText()
		operationRetry = self._GetOperationRetry()
		if operationRetry:
			if retryEvent != operationRetry or not text:
				text = _Text("VIRTUAL_MARKET_RETRY_REQUIRED",
					"Dokonči předchozí akci tlačítkem Zkusit znovu.")
			retryEvent = operationRetry
		self.statusText = text
		self.statusIsRead = readStatus and not operationRetry
		self.status.SetText(text)
		if text:
			self.sidebarLine2.Hide()
			self.status.Show()
		else:
			self.status.Hide()
			self.sidebarLine2.Hide()
		self.retryEvent = retryEvent
		label = _Text("VIRTUAL_MARKET_OFFER_ALL_CANCEL", "Zru\u0161it") \
			if retryEvent is not None and retryEvent == getattr(self, "_CancelOfferAll", None) else \
			_Text("VIRTUAL_MARKET_RETRY", "Opakovat")
		if label != getattr(self, "retryButtonLabel", None):
			self.retryButtonLabel = label
			self.retryButton.SetText(label)
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
					"Čeká se na dokončení předchozí akce..."))
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
		visibleCount = min(PAGINATION_SLOTS, pageCount)
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
		self._MarkCategoryRows(-1, -1)

	def _MarkCategoryRows(self, chosenIndex, chosenPosition):
		for index, button in enumerate(self.filterButtons):
			_MarkRow(button, index == chosenIndex)
		for position, button in enumerate(self.subcategoryButtons):
			chosen = position == chosenPosition
			_MarkRow(button, chosen)
			self.subcategoryLabels[position].SetPackedFontColor(
				_MarketColor(SUBCATEGORY_SELECTED_COLOR if chosen else SUBCATEGORY_TEXT_COLOR))

	def _ShowAllMarketCategories(self):
		self.advancedFilters.SelectCategory(0)
		self._SyncMarketCategory()
		self._Search()

	def _SyncMarketCategory(self):
		filters = self.advancedFilters.GetFilters()
		category = filters.get("category", 0)
		subtype = tuple(filters.get("subtype", (-1, -1)))
		self.lastSearchType = None
		index, chosenPosition = self._RailRowOf(category, subtype)
		# The open row follows the applied filters: another category closes it, a subcategory chosen in the filter
		# dialog opens its row so the chosen entry shows.
		follow = subtype != (-1, -1) and (category, subtype) != self.closedChoice
		if index != self.expandedCategory and (self.expandedCategory >= 0 or follow):
			self._ExpandCategory(index if follow else -1)
			self._RefreshCategoryViewport(reveal=True)
		if index != self.expandedCategory:
			chosenPosition = -1
		if index >= 0:
			searchType = tuple(MARKET_CATEGORIES[index][3:5])
			self.lastSearchType = searchType if searchType[0] >= 0 else None
		self._MarkCategoryRows(index, chosenPosition)

	def _RailRowOf(self, category, subtype):
		"""(row index, entry position) of the rail showing the applied category / subtype: the entry in the open row,
		else a row holding that entry, else the row searching that category (a plain row first); -1 when none."""
		key = (category, tuple(subtype))
		if self.expandedCategory >= 0:
			for position, (entry, name) in enumerate(self.subcategoryEntries):
				if tuple(entry) == key:
					return self.expandedCategory, position
		visible = self._VisibleCategoryIndexes()
		if subtype != (-1, -1):
			for index in visible:
				for position, (entry, name) in enumerate(self._CategorySubcategories(index)):
					if tuple(entry) == key:
						return index, position
		rows = [index for index in visible if MARKET_CATEGORY_IDS[index] == category]
		plain = [index for index in rows if MARKET_CATEGORY_KEYS[index] not in MARKET_CATEGORY_FOLDERS]
		if plain or rows:
			return (plain or rows)[0], -1
		for index in visible:
			for position, (entry, name) in enumerate(self._CategorySubcategories(index)):
				if tuple(entry) == key:
					return index, -1
		return -1, -1

	def _CategorySubcategories(self, index):
		"""The entries ((category, (kind, subtype)), name) the row at index opens into, or [] when it does not open.
		A folder row opens with one entry, a plain row needs SUBCATEGORY_MINIMUM."""
		if index < 0 or index >= len(MARKET_CATEGORIES):
			return []
		if not getattr(net, "IsVirtualMarketSearchV4Available", lambda: False)():
			return []
		try:
			rows = self.advancedFilters.RailEntries(MARKET_CATEGORY_KEYS[index])
		except Exception:
			return []
		if MARKET_CATEGORY_KEYS[index] in MARKET_CATEGORY_FOLDERS:
			return rows
		return rows if len(rows) >= SUBCATEGORY_MINIMUM else []

	def _SubcategoryButton(self, position):
		while len(self.subcategoryButtons) <= position:
			slot = len(self.subcategoryButtons)
			button, label = _SubcategoryRow(
				self.categoryViewport,
				lambda selected=slot: self._SelectMarketSubcategory(selected))
			button.SetOnRunMouseWheelEvent(self._OnCategoryMouseWheel)
			self.subcategoryButtons.append(button)
			self.subcategoryLabels.append(label)
		return self.subcategoryButtons[position]

	def _ExpandCategory(self, index):
		"""Opens the row at index (and closes any other); -1 or a row without entries closes all."""
		entries = self._CategorySubcategories(index)
		opened = bool(entries) and index != self.expandedCategory
		self.expandedCategory = index if entries else -1
		self.railOpenAt = app.GetTime() if opened else 0.0
		if entries:
			self.closedChoice = None
		self.subcategoryEntries = entries
		for position, (entry, name) in enumerate(entries):
			self._SubcategoryButton(position)
			self.subcategoryLabels[position].SetText(name)

	def _ResetMarketSearch(self):
		self.advancedFilters.Reset()
		self.searchMode = "item"
		self.searchPlayerCheck.SetUp()
		self._SetExactMatch(False)
		self.searchInput.SetText("")
		self.pinnedSearch = None
		self.searchInput.SetInfoMessage(_Text(
			"VIRTUAL_MARKET_VNUM_PLACEHOLDER", "N\u00e1zev \u010di \u010d\u00edslo"))
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

	def _CategoryEntries(self):
		"""The rail rows top to bottom: (category index, -1) for a category, (category index, position) for a
		subcategory row of the open category."""
		entries = []
		for index in self._VisibleCategoryIndexes():
			entries.append((index, -1))
			if index == self.expandedCategory:
				entries.extend((index, position) for position in range(len(self.subcategoryEntries)))
		return entries

	def _RailRevealCount(self):
		"""How many entries of the open row show now: all, or the part let in by the opening animation."""
		count = len(self.subcategoryEntries)
		openAt = getattr(self, "railOpenAt", 0.0)
		if not openAt:
			return count
		progress = (app.GetTime() - openAt) / SUBCATEGORY_OPEN_SECONDS
		if progress >= 1.0:
			self.railOpenAt = 0.0
			return count
		return min(count, int(count * max(0.0, progress)) + 1)

	def _AnimateRail(self):
		if getattr(self, "railOpenAt", 0.0) and self.categoryViewport:
			self._RefreshCategoryViewport()

	@staticmethod
	def _CategoryEntryHeight(entry):
		return CATEGORY_STEP_Y if entry[1] < 0 else SUBCATEGORY_STEP_Y

	def _CategoryMaxStart(self, entries=None):
		"""The first row that still fills the rail to its end (0 = every row fits, nothing scrolls)."""
		entries = self._CategoryEntries() if entries is None else entries
		viewHeight = CATEGORY_VISIBLE_COUNT * CATEGORY_STEP_Y
		used = 0
		for position in range(len(entries) - 1, -1, -1):
			used += self._CategoryEntryHeight(entries[position])
			if used > viewHeight:
				return position + 1
		return 0

	def _RefreshCategoryViewport(self, reveal=False):
		entries = self._CategoryEntries()
		count = len(entries)
		maxStart = self._CategoryMaxStart(entries)
		viewHeight = CATEGORY_VISIBLE_COUNT * CATEGORY_STEP_Y
		startIndex = min(max(0, self.categoryStartIndex), maxStart)
		if reveal and (self.expandedCategory, -1) in entries:
			# Scroll just enough that the open category and its rows show (the category row first of all).
			first = entries.index((self.expandedCategory, -1))
			last = first + len(self.subcategoryEntries)
			startIndex = min(startIndex, first)
			while startIndex < first and sum(self._CategoryEntryHeight(entry)
					for entry in entries[startIndex:last + 1]) > viewHeight:
				startIndex += 1
			startIndex = min(startIndex, maxStart)
		moved = startIndex != self.categoryStartIndex
		self.categoryStartIndex = startIndex
		for button in self.filterButtons:
			button.Hide()
		for button in self.subcategoryButtons:
			button.Hide()
		for index, chevron in enumerate(self.categoryChevrons):
			if self._CategorySubcategories(index):
				chevron.LoadImage(CATEGORY_CHEVRON_PATH % ("down" if index == self.expandedCategory else "right"))
				chevron.Show()
			else:
				chevron.Hide()
		y = 0
		shown = 0
		revealed = self._RailRevealCount()
		for index, position in entries[self.categoryStartIndex:]:
			if position >= revealed:
				continue
			height = self._CategoryEntryHeight((index, position))
			if y + height > viewHeight:
				break
			if position < 0:
				button = self.filterButtons[index]
				button.SetPosition(0, y)
			else:
				button = self.subcategoryButtons[position]
				button.SetPosition(SUBCATEGORY_INDENT_X, y)
			button.Show()
			y += height
			shown += 1
		if maxStart:
			self.categoryScrollBar.SetMiddleBarSize(float(shown) / count)
			self.categoryScrollBar.SetScrollStep(1.0 / float(maxStart))
			if reveal or moved:
				# Code moved the rail: the thumb follows (its scroll event finds the same first row and returns).
				self.categoryScrollBar.SetPos(float(self.categoryStartIndex) / maxStart)
			self.categoryScrollBar.Show()
		else:
			self.categoryScrollBar.SetPos(0.0)
			self.categoryScrollBar.Hide()

	def _OnCategoryScroll(self):
		maxStart = self._CategoryMaxStart()
		if not maxStart:
			return
		startIndex = int(
			self.categoryScrollBar.GetPos() * maxStart + 0.5)
		if startIndex == self.categoryStartIndex:
			return
		self.categoryStartIndex = startIndex
		self._RefreshCategoryViewport()

	def _CategoryWheelStep(self):
		maxStart = self._CategoryMaxStart()
		return 1.0 / float(maxStart) if maxStart else 0.0

	def _OnCategoryMouseWheel(self, scrollDown):
		maxStart = self._CategoryMaxStart()
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
			_Text("VIRTUAL_MARKET_VNUM_PLACEHOLDER", "N\u00e1zev \u010di \u010d\u00edslo")
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
				names = _SortSuggestions(_ItemSuggestions(text))
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
		if index not in self._VisibleCategoryIndexes():
			self._SyncMarketCategory()
			return
		folder = MARKET_CATEGORY_KEYS[index] in MARKET_CATEGORY_FOLDERS
		if index == self.expandedCategory:
			# The second click closes the open row. A plain row with a chosen subcategory goes back to its whole
			# category; a folder keeps what is shown (it has no whole of its own).
			filters = self.advancedFilters.GetFilters()
			subtype = tuple(filters.get("subtype", (-1, -1)))
			self._ExpandCategory(-1)
			# The closed row stays closed while its choice stays applied (a search does not open it again).
			self.closedChoice = (filters.get("category", 0), subtype)
			self._RefreshCategoryViewport()
			if folder or subtype == (-1, -1):
				self._SyncMarketCategory()
				return
			self.advancedFilters.SelectCategory(MARKET_CATEGORY_IDS[index])
		else:
			self._ExpandCategory(index)
			self._RefreshCategoryViewport(reveal=True)
			if folder and self.subcategoryEntries:
				# A folder searches its first entry.
				(category, subtype), name = self.subcategoryEntries[0]
				self.advancedFilters.SelectSubcategory(category, subtype)
			else:
				self.advancedFilters.SelectCategory(MARKET_CATEGORY_IDS[index])
		self._SyncMarketCategory()
		self._Search()

	def _SelectMarketSubcategory(self, position):
		index = self.expandedCategory
		if index < 0 or position < 0 or position >= len(self.subcategoryEntries):
			self._SyncMarketCategory()
			return
		(category, subtype), name = self.subcategoryEntries[position]
		subtype = tuple(subtype)
		filters = self.advancedFilters.GetFilters()
		chosen = filters.get("category") == category and tuple(filters.get("subtype", (-1, -1))) == subtype
		if chosen and MARKET_CATEGORY_KEYS[index] in MARKET_CATEGORY_FOLDERS:
			self._SyncMarketCategory()  # a folder has no whole to go back to
			return
		if chosen:
			category, subtype = MARKET_CATEGORY_IDS[index], (-1, -1)   # again: the whole category
		self.advancedFilters.SelectSubcategory(category, subtype)
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
		if self.expandedCategory >= 0:
			self._ExpandCategory(-1)
			self._RefreshCategoryViewport()
		self._ClearRows()
		self._SetMarketEmptyState(
			_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed nab\u00eddek..."),
			_Text("VIRTUAL_MARKET_LOADING_HINT", "Hled\u00e1 se na trhu."))
		if not self._SendMarketSearch([], "", False, -1, -1):
			self.marketSearched = False
			self._SetStatus(_Text("VIRTUAL_MARKET_REQUEST_BUSY", "Te\u010f to nejde. Zkus to za chv\u00edli."),
				self._BrowseMarket)
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_REQUEST_FAILED", "Trh nelze na\u010d\u00edst"),
				_Text("VIRTUAL_MARKET_REQUEST_FAILED_HINT", "Chv\u00edli po\u010dkej a zkus trh obnovit."))
			return False
		self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed..."))
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
				self._SetStatus("Zadej platné číslo předmětu.")
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
					self._SetStatus("Zadej platný název nebo číslo předmětu.")
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
			_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed nab\u00eddek..."),
			_Text("VIRTUAL_MARKET_LOADING_HINT", "Hled\u00e1 se na trhu."))
		if not self._SendMarketSearch(vnums, sellerName, sellerExact, *(self.lastSearchType or (-1, -1))):
			self._SetStatus(_Text("VIRTUAL_MARKET_REQUEST_BUSY", "Te\u010f to nejde. Zkus to za chv\u00edli."))
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_REQUEST_FAILED", "Trh nelze na\u010d\u00edst"),
				_Text("VIRTUAL_MARKET_REQUEST_FAILED_HINT", "Chv\u00edli po\u010dkej a zkus hledat znovu."))
		else:
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed..."))

	def _OpenAdvancedFilters(self):
		if not getattr(net, "IsVirtualMarketSearchV4Available", lambda: False)():
			self._SetStatus("Rozšířené filtry zatím nejsou dostupné.")
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

	def _OwnerListingsLoading(self):
		return bool(getattr(virtualmarket, "OwnerListingsHasMore", lambda: 0)())

	def _ArmOwnerListingsPage(self, delay=OWNER_LISTINGS_PAGE_DELAY):
		self.ownerListingsNextAt = app.GetTime() + delay

	def _LoadNextOwnerListingsPage(self):
		self.ownerListingsNextAt = 0.0
		if not self._OwnerListingsLoading():
			self.ownerListingsAttempts = 0
			return False
		self.ownerListingsAttempts += 1
		if self.ownerListingsAttempts > OWNER_LISTINGS_PAGE_ATTEMPTS:
			if self.ownerReloadHoldUntil:
				self.ownerReloadHoldUntil = 0.0
				self._RefreshOwnerGrid()
			return False
		sent = bool(getattr(net, "SendVirtualMarketOwnerListingsNextPage", lambda: False)())
		if not sent:
			# Another owner request is still open; try again after its answer.
			self._ArmOwnerListingsPage()
		return sent

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
				_Text("VIRTUAL_MARKET_WELCOME_HINT", "Vyber kategorii nebo napi\u0161 n\u00e1zev \u010di \u010d\u00edslo p\u0159edm\u011btu."),
				_Text("VIRTUAL_MARKET_WELCOME_DETAIL", "Pro v\u00fdpis v\u0161ech nab\u00eddek si aktualizuj hru."))
			return
		count = int(virtualmarket.GetListingCount())
		if count == 0:
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_NO_RESULTS", "\u017d\u00e1dn\u00e9 nab\u00eddky"),
				_Text("VIRTUAL_MARKET_NO_RESULTS_HINT", "Tomuto v\u00fdb\u011bru te\u010f neodpov\u00edd\u00e1 \u017e\u00e1dn\u00e1 nab\u00eddka."),
				_Text("VIRTUAL_MARKET_NO_RESULTS_DETAIL", "Zkus jinou kategorii, n\u00e1zev nebo \u010d\u00edslo p\u0159edm\u011btu."))
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
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed..."))

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
					"Najednou můžeš koupit max. 20 nabídek."))
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
			"Koupit %d nabídek celkem za %s? Vše proběhne najednou.") %
			(len(items), _Money(total)))
		self.confirm.SetAcceptEvent(self._AcceptConfirm)
		self.confirm.Open()

	def _PurchaseSelected(self, items):
		send = getattr(net, "SendVirtualMarketBatchPurchase", None)
		if send and send([(int(value[0]), int(value[1]), int(value[2])) for value in items]):
			self._SetStatus(_Text("VIRTUAL_MARKET_BATCH_PURCHASING",
				"Probíhá nákup..."))

	def _Purchase(self, listingId, vnum, price):
		if net.SendVirtualMarketPurchase(listingId, vnum, price):
			self._SetStatus(_Text("VIRTUAL_MARKET_PURCHASING", "Prob\u00edh\u00e1 n\u00e1kup..."))

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
		exists, state, closeReason, expiresAt, listedItems, pendingReturns, activeSellers, availableCredit = \
			self._OwnerShopSnapshot()
		self._UpdateSidebarSellers(activeSellers)
		exists = bool(exists)
		isOpen = exists and int(state) == 0
		isSuspended = exists and int(state) == 2
		if isOpen:
			stateText = _Text("VIRTUAL_MARKET_OWNER_OPEN", "otevřen")
			stateColor = OWNER_STATE_OPEN_COLOR
		elif isSuspended:
			stateText = _Text("VIRTUAL_MARKET_OWNER_SUSPENDED", "pozastaven")
			stateColor = OWNER_STATE_SUSPENDED_COLOR
		else:
			stateText = _Text("VIRTUAL_MARKET_OWNER_CLOSED", "zavřen")
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
		self._SetWidgetsVisible(self.ownerActiveToolbarWidgets, isOpen)
		self._RefreshOwnerPageArrows(isOpen)
		if isSuspended:
			self.ownerClosedTitle.SetText(_Text("VIRTUAL_MARKET_SUSPENDED_TITLE", "Obchod je pozastaven správcem"))
			self.ownerClosedHint.SetText(_Text("VIRTUAL_MARKET_SUSPENDED_HINT", "Tvoje nabídky jsou v bezpečí. Napiš podpoře."))
		else:
			self.ownerClosedTitle.SetText(_Text("VIRTUAL_MARKET_CLOSED_TITLE", "Tvůj obchod zatím není otevřen."))
			self.ownerClosedHint.SetText(_Text("VIRTUAL_MARKET_CLOSED_HINT_NO_NAME", "Založ si obchod na 5 dní."))
		_SetAccountActionAvailable(self.withdrawButton, int(availableCredit) > 0)
		if getattr(self, "salesHistory", None) is not None and self._ApplyOwnerView():
			return
		if refreshGrid and isOpen:
			self._RefreshOwnerGrid()

	def _RefreshOwnerGrid(self):
		if self.currentTab != TAB_OWNER:
			return
		self.ownerTotalPrefix.SetText(_Text(
			"VIRTUAL_MARKET_TOTAL_LISTING_VALUE", "Celková hodnota nabídek: "))
		totalListingValue = 0
		if not hasattr(virtualmarket, "GetOwnerListingCount"):
			self._ClearOwnerSelection()
			self.ownerGridPages = [[]]
			self.gridPages = self.ownerGridPages
			self.ownerModelComplete = True
			self.ownerHasMore = False
			self.ownerLayout = {}
			self._ShowOwnerPage()
			self.ownerTotalValue.SetText(_YangText(totalListingValue))
			self.ownerTotalValue.SetFontColor(*CURRENCY_YANG_COLOR)
			_CenterAccountValuePair(self.ownerTotalPrefix, self.ownerTotalValue, ACCOUNT_PAGE_CENTER_X, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2)
			return
		hasMore = bool(virtualmarket.OwnerListingsHasMore())
		if self.ownerModelComplete and (hasMore or not self.ownerNativeOk):
			# A reload is under way, or its first page failed and the native list is empty: the grid keeps the
			# last complete layout and only the confirmed local changes differ from it.
			layout = dict(self.ownerBaseLayout)
			self.ownerHasMore = False
		else:
			layout = {}
			for index in range(int(virtualmarket.GetOwnerListingCount())):
				listingId, vnum, itemCount, price, itemType, itemSubtype, expiresAt, displaySlot, itemSize = virtualmarket.GetOwnerListingInfo(index)
				listingId = int(listingId)
				layout[listingId] = (
					int(displaySlot),
					(
						listingId, int(index), int(vnum), int(itemCount), int(price),
						int(expiresAt), max(1, min(GRID_ROWS, int(itemSize))),
					),
				)
			if not hasMore and self.ownerNativeOk:
				self.ownerBaseLayout = dict(layout)
				self.ownerModelComplete = True
			self.ownerHasMore = hasMore
		for listingId, change in self.ownerLocalChanges.items():
			if change[1] is None:
				layout.pop(listingId, None)
			else:
				layout[listingId] = change[1]
		self.ownerLayout = layout
		selectedRecord = None
		maxPage = 0
		for displaySlot, payload in layout.values():
			totalListingValue += int(payload[4])
			if payload[0] == self.selectedOwnerListingId:
				selectedRecord = (payload[0], payload[2], payload[3], payload[4])
			maxPage = max(maxPage, displaySlot // GRID_SLOT_COUNT)
		self.ownerTotalValue.SetText(_YangText(totalListingValue))
		self.ownerTotalValue.SetFontColor(*CURRENCY_YANG_COLOR)
		_CenterAccountValuePair(self.ownerTotalPrefix, self.ownerTotalValue, ACCOUNT_PAGE_CENTER_X, ACCOUNT_VALUE_STRIP_Y + ACCOUNT_VALUE_STRIP_HEIGHT // 2)
		pageCount = maxPage + 1
		if layout and pageCount < int(getattr(virtualmarket, "LAYOUT_MAXIMUM_PAGES", 64)):
			pageCount += 1
		self.ownerGridPages = [[] for unused in range(max(1, pageCount))]
		for displaySlot, payload in layout.values():
			page = displaySlot // GRID_SLOT_COUNT
			if page < len(self.ownerGridPages):
				self.ownerGridPages[page].append((displaySlot % GRID_SLOT_COUNT, payload))
		for page in self.ownerGridPages:
			page.sort(key=lambda row: row[0])
		self.gridPages = self.ownerGridPages
		self._ShowOwnerPage()
		if selectedRecord:
			self._SetOwnerSelection(*selectedRecord)
		else:
			self._ClearOwnerSelection()

	def _OwnerLayoutKnown(self):
		"""True when every listing's cell is known: the native list is complete, or the grid shows the last complete
		layout plus the confirmed local changes while a reload runs."""
		return bool(self.ownerModelComplete) or not self._OwnerListingsLoading()

	def _ReloadOwnerListings(self):
		"""Ask for the whole owner list again; a local change recorded before this call is dropped once it is complete."""
		if not hasattr(net, "SendVirtualMarketOwnerListings"):
			return False
		self.ownerReloadSerial += 1
		return bool(net.SendVirtualMarketOwnerListings())

	def _RecordOwnerChange(self, listingId, record, removed=False):
		"""Draw a server-confirmed change now: record (displaySlot, payload), or removed for a listing that is gone."""
		listingId = int(listingId)
		if listingId <= 0 or (record is None and not removed):
			return
		if removed:
			record = None
		self.ownerLocalChanges[listingId] = (self.ownerReloadSerial, record)
		self._RefreshOwnerGrid()

	def _RecordCreatedListing(self, vnum, count, price):
		"""Draw a listing the server just created in the cell it answered (the held offer's cell without one)."""
		info = getattr(virtualmarket, "GetListingCreate", lambda: ())()
		if len(info) < 9 or int(info[4]) <= 0:
			return
		listingId, leaseExpiresAt, displaySlot, itemSize = int(info[4]), int(info[6]), int(info[7]), int(info[8])
		maximumPages = int(getattr(virtualmarket, "LAYOUT_MAXIMUM_PAGES", 64))
		if displaySlot < 0 or displaySlot >= maximumPages * GRID_SLOT_COUNT:
			if not self.offer:
				return
			displaySlot = int(self.offer[4])
		if itemSize <= 0:
			itemSize = int(self.offer[5]) if self.offer else _ItemHeight(vnum)
		self._RecordOwnerChange(listingId, (displaySlot, (
			listingId, -1, int(vnum), int(count), int(price), leaseExpiresAt,
			max(1, min(GRID_ROWS, itemSize)))))

	def _OwnerRecord(self, listingId, displaySlot=None, price=None):
		"""The shown record of a listing with a new cell or price, or None when it is not shown."""
		current = self.ownerLayout.get(int(listingId))
		if not current:
			return None
		slot, payload = current
		payload = list(payload)
		if price is not None:
			payload[4] = int(price)
		return (int(slot if displaySlot is None else displaySlot), tuple(payload))

	def _ShowOwnerPage(self):
		"""Stage the current page of the owner model; _FlushOwnerGrid draws it once per frame."""
		pages = self.ownerGridPages or [[]]
		self.currentPage = min(self.currentPage, max(0, len(pages) - 1))
		wanted = {}
		slotMap = {}
		for slotIndex, payload in pages[self.currentPage]:
			listingId, nativeIndex, vnum, itemCount, price, expiresAt, itemSize = payload
			wanted[int(slotIndex)] = (int(vnum), int(itemCount))
			entry = (
				"owner", int(nativeIndex), int(price), int(listingId),
				int(vnum), int(itemCount), int(itemSize),
				self.currentPage * GRID_SLOT_COUNT + int(slotIndex),
				int(expiresAt),
			)
			_MapGridItemFootprint(slotMap, slotIndex, itemSize, entry)
		self.ownerGridWanted = wanted
		self.ownerGridWantedMap = slotMap
		self.ownerGridDirty = True
		self.ownerPage.SetText("%d / %d" % (self.currentPage + 1, max(1, len(pages))))
		self.ownerPageCount = max(1, len(pages))
		self._RefreshOwnerPageArrows(self.ownerShopOpen)

	def _FlushOwnerGrid(self):
		"""One owner grid update per frame: only the slots that differ change, the grid stays shown."""
		if not self.ownerGridDirty:
			return 0
		self.ownerGridDirty = False
		if self.currentTab != TAB_OWNER:
			return 0
		self.gridSlotMap = self.ownerGridWantedMap
		return _SyncGridItems(self.ownerGrid, self.ownerGridShown, self.ownerGridWanted)

	def _OwnerNativeIndex(self, entry):
		"""Native index of an owner entry's listing, or -1 while a held reload has not loaded it yet."""
		listingId = int(entry[3])
		count = int(virtualmarket.GetOwnerListingCount())
		index = int(entry[1])
		if 0 <= index < count and int(virtualmarket.GetOwnerListingInfo(index)[0]) == listingId:
			return index
		for index in range(count):
			if int(virtualmarket.GetOwnerListingInfo(index)[0]) == listingId:
				return index
		return -1

	def _OwnerOccupiedCells(self, excludedListingId=0):
		"""Cells of the layout on screen (ownerLayout): during a held reload the native list is incomplete."""
		occupied = set()
		for listingId, (position, payload) in self.ownerLayout.items():
			if int(listingId) == int(excludedListingId):
				continue
			height = max(1, min(GRID_ROWS, int(payload[6])))
			for offset in range(height):
				occupied.add(int(position) + offset * GRID_COLUMNS)
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
			self.pendingListingMove = (listingId, targetPosition)
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_MOVING",
				"Nab\u00eddka se p\u0159esouv\u00e1 do zvolen\u00e9ho slotu..."))
		else:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_REQUEST_BUSY",
				"Te\u010f to nejde. Zkus to za chv\u00edli."))

	def _SelectOwnerSlot(self, slotIndex):
		if self._IsOwnerDrag():
			self._DropOwnerListing(slotIndex)
			return
		entry = self.gridSlotMap.get(int(slotIndex))
		if not entry or entry[0] != "owner":
			return
		if mouseModule.mouseController.isAttached():
			return
		self._SetOwnerSelection(entry[3], entry[4], entry[5], entry[2])
		self.ownerDragListingId = int(entry[3])
		self.ownerDragHeight = int(entry[6])
		self.ownerDragOriginalPosition = int(entry[7])
		mouseModule.mouseController.AttachObject(
			self, player.SLOT_TYPE_PRIVATE_SHOP, int(slotIndex),
			int(entry[4]), int(entry[5]))
		self._SetStatus(_Text("VIRTUAL_MARKET_OWNER_SELECTED",
			"P\u0159et\u00e1hni %s do voln\u00e9ho slotu. Cena %s, zb\u00fdv\u00e1 %s") %
			(_ItemName(entry[4]), _Money(entry[2]), _Remaining(entry[8])))

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
		if self.selectedOwnerListingId <= 0 or getattr(self, "offerAll", None):
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
				"Nab\u00eddka se ru\u0161\u00ed, p\u0159edm\u011bt se p\u0159esouv\u00e1 do z\u00e1lo\u017eky Vr\u00e1cen\u00e9..."))
			return
		self._SetStatus(_Text(
			"VIRTUAL_MARKET_REQUEST_BUSY",
			"Te\u010f to nejde. Zkus to za chv\u00edli."))

	def _OverInOwnerSlot(self, slotIndex):
		# Restore a tooltip hidden during a reload without requiring mouse movement.
		self.ownerHoverSlot = int(slotIndex)
		entry = self.gridSlotMap.get(int(slotIndex))
		if entry and entry[0] == "owner":
			index = self._OwnerNativeIndex(entry)
			if index < 0:
				self._HideTooltip()
				return
			self._ShowTooltip("owner", index, entry[2])

	def _OverOutOwnerSlot(self):
		self.ownerHoverSlot = None
		self._HideTooltip()

	def _ShowHoveredOwnerTooltip(self):
		"""After a reload completes: the tooltip of the owner slot under the mouse, if any."""
		slot = getattr(self, "ownerHoverSlot", None)
		if slot is None or self.currentTab != TAB_OWNER or not self.IsShow():
			return
		entry = self.gridSlotMap.get(int(slot))
		if entry and entry[0] == "owner" and self._OwnerNativeIndex(entry) >= 0:
			self._OverInOwnerSlot(slot)

	def _UpdateSidebarSellers(self, activeSellers=None):
		if activeSellers is None:
			try:
				activeSellers = virtualmarket.GetOwnerShop()[6]
			except:
				return
		self.sidebarLine2.SetText(_Text("VIRTUAL_MARKET_ACTIVE_SELLERS_SHORT",
			"Aktivn\u00ed prodejci: %d") % int(activeSellers))

	def _CreateShop(self):
		if net.SendVirtualMarketShopCreate(_AutomaticShopName()):
			self._SetStatus(_Text("VIRTUAL_MARKET_CREATING", "Obchod se zakl\u00e1d\u00e1 na 5 dn\u00ed..."))

	def _RenewShop(self):
		if net.SendVirtualMarketShopRenew():
			self._SetStatus(_Text("VIRTUAL_MARKET_RENEWING", "Obchod se prodlu\u017euje na 5 dn\u00ed odte\u010f..."))

	def _ConfirmClose(self):
		self.confirmEvent = self._CloseShop
		self.confirm.SetText(_Text("VIRTUAL_MARKET_CLOSE_CONFIRM",
			"Uzav\u0159\u00edt obchod a p\u0159esunout neprodan\u00e9 p\u0159edm\u011bty do z\u00e1lo\u017eky Vr\u00e1cen\u00e9?"))
		self.confirm.SetAcceptEvent(self._AcceptConfirm)
		self.confirm.Open()

	def _CloseShop(self):
		if net.SendVirtualMarketShopClose():
			self._SetStatus(_Text("VIRTUAL_MARKET_CLOSING", "Obchod se uzav\u00edr\u00e1..."))

	def _Withdraw(self):
		if net.SendVirtualMarketSellerWithdrawal():
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAWING", "V\u00fdt\u011b\u017eek se vyb\u00edr\u00e1..."))

	def _AttachOffer(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return
		if not self.ownerShopOpen:
			return
		if not self._OwnerLayoutKnown() and \
				self.ownerListingsAttempts <= OWNER_LISTINGS_PAGE_ATTEMPTS:
			# Free cells are known only once every listing is loaded (or a held reload shows the complete layout).
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed..."))
			return
		if self._IsOwnerDrag():
			self._DropOwnerListing(slotIndex)
			return
		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotIndex = mouseModule.mouseController.GetAttachedSlotNumber()
		count = int(mouseModule.mouseController.GetAttachedItemCount())
		attachedVnum = int(mouseModule.mouseController.GetAttachedItemIndex())
		mouseModule.mouseController.DeattachObject()
		inventoryType = player.SlotTypeToInvenType(attachedSlotType)
		if inventoryType == player.INVENTORY and player.IsEquipmentSlot(attachedSlotIndex):
			self._SetStatus(_Text("VIRTUAL_MARKET_UNEQUIP_FIRST", "Nejprve item sundejte."))
			return
		if not _IsListingInventorySource(inventoryType, attachedSlotIndex):
			self._SetStatus(_Text("PRIVATE_SHOP_CANNOT_SELL_ITEM", "Tento item nelze prodat."))
			return
		try:
			vnum = int(player.GetItemIndex(inventoryType, attachedSlotIndex))
			sourceCount = int(player.GetItemCount(inventoryType, attachedSlotIndex))
		except:
			return
		if vnum <= 0 or vnum != attachedVnum or count <= 0 or count > sourceCount:
			self._SetStatus(_Text("VIRTUAL_MARKET_OFFER_SOURCE_CHANGED",
				"The item or its count changed. Select it again."))
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
		self._BeginOffer(
			inventoryType, attachedSlotIndex, count, vnum, targetPosition, height)

	def _BeginOffer(self, inventoryType, slotIndex, count, vnum, targetPosition, height,
			usePreviousPrice=False):
		"""Hold the offer and ask for its price, exactly as a drop on the owner grid does.

		usePreviousPrice (Shift + right-click): with a remembered price for this item the offer goes at once at
		that price per piece, without the dialog; without one the dialog opens as usual."""
		if self.offer or self.pendingListingCreate or getattr(self, "offerAll", None):
			return
		self.offer = (
			int(inventoryType), int(slotIndex), int(count), int(vnum),
			int(targetPosition), int(height),
		)
		self.offerUsesPreviousPrice = bool(usePreviousPrice)
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
			# _PriceOffer: Shift + right-click sends at once (window harnesses may lack it).
			getattr(self, "_PriceOffer", self._OpenOfferPriceDialog)(suggestedPrice)
			return
		send = getattr(net, "SendVirtualMarketPricePreference", None)
		if not send or not net.SendVirtualMarketPricePreference(vnum):
			self._OpenOfferPriceDialog(0)

	def _FindFreeOwnerPosition(self, height):
		"""The first owner grid position where an item of this height fits: the shown page first (the seller sees
		the item land), then every page from the first. -1 when the shop has no room."""
		height = max(1, min(GRID_ROWS, int(height)))
		maximumPages = int(getattr(virtualmarket, "LAYOUT_MAXIMUM_PAGES", 64))
		occupied = self._OwnerOccupiedCells()
		currentPage = max(0, min(maximumPages - 1, int(self.currentPage)))
		pages = [currentPage] + [page for page in range(maximumPages) if page != currentPage]
		for page in pages:
			base = page * GRID_SLOT_COUNT
			for localSlot in range((GRID_ROWS - height + 1) * GRID_COLUMNS):
				position = base + localSlot
				free = True
				for offset in range(height):
					if position + offset * GRID_COLUMNS in occupied:
						free = False
						break
				if free:
					return position
		return -1

	def CanQuickOffer(self):
		"""True while "Můj obchod" is shown with an open shop that takes new offers."""
		try:
			shown = bool(self.IsShow())
		except Exception:
			return False
		return shown and self.currentTab == TAB_OWNER and bool(self.ownerShopOpen) and \
			self.repricingListingId <= 0 and getattr(self, "ownerView", None) != "history"

	def QuickOfferInventoryItem(self, slotIndex, windowType=player.INVENTORY, usePreviousPrice=False):
		"""A right-click on an inventory item offers it like a drop on the first free owner slot.
		usePreviousPrice (Shift + right-click): at the price last used for this item, without the price dialog.

		Returns True when the click was taken (the price dialog opens, listings are loading, or an offer is active).
		False keeps the item's ordinary right-click: the window is closed or on another tab, the shop is full,
		the item cannot be sold (equipment, antiflag, sealed) or something is held on the mouse."""
		if slotIndex is None or int(slotIndex) < 0 or not self.CanQuickOffer():
			return False
		if mouseModule.mouseController.isAttached():
			return False
		if self.offer or self.pendingListingCreate or getattr(self, "offerAll", None):
			# Keep one identity through price lookup, editing and the native create/retry
			# (and "Vložit vše" offers its stacks one by one until it ends or is cancelled).
			return True
		slotIndex = int(slotIndex)
		isEquipment = getattr(player, "IsEquipmentSlot", None)
		if windowType == player.INVENTORY and isEquipment and isEquipment(slotIndex):
			return False
		if not _IsListingInventorySource(windowType, slotIndex):
			return False
		try:
			vnum = int(player.GetItemIndex(windowType, slotIndex))
			count = int(player.GetItemCount(windowType, slotIndex))
		except Exception:
			return False
		if vnum <= 0 or count <= 0:
			return False
		item.SelectItem(vnum)
		if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
			return False
		if getattr(app, "ENABLE_SOUL_BIND_SYSTEM", 0):
			sealDate = player.GetItemSealDate(windowType, slotIndex)
			if sealDate == -1 or sealDate > 0:
				return False
		if not self._OwnerLayoutKnown() and \
				self.ownerListingsAttempts <= OWNER_LISTINGS_PAGE_ATTEMPTS:
			# Free cells are known only once every listing is loaded (same as a drop).
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed..."))
			return True
		height = _ItemHeight(vnum)
		position = self._FindFreeOwnerPosition(height)
		if position < 0:
			return False
		self._BeginOffer(windowType, slotIndex, count, vnum, position, height, usePreviousPrice)
		return True

	def _IsOfferableStack(self, windowType, slotIndex, vnum):
		"""The same checks as a right-click offer of this cell, for a stack of the given item."""
		isEquipment = getattr(player, "IsEquipmentSlot", None)
		if isEquipment and isEquipment(slotIndex):
			return False
		if not _IsListingInventorySource(windowType, slotIndex):
			return False
		try:
			if int(player.GetItemIndex(windowType, slotIndex)) != int(vnum) or \
					int(player.GetItemCount(windowType, slotIndex)) <= 0:
				return False
		except Exception:
			return False
		item.SelectItem(int(vnum))
		if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
			return False
		if getattr(app, "ENABLE_SOUL_BIND_SYSTEM", 0):
			sealDate = player.GetItemSealDate(windowType, slotIndex)
			if sealDate == -1 or sealDate > 0:
				return False
		return True

	def _OfferAllSources(self, windowType, firstSlot, vnum):
		"""The other inventory stacks of the offered item that "Vložit vše" would offer, in inventory order.

		Only the ordinary and special inventory: _ContinueOfferAll offers from player.INVENTORY, so a Dragon
		Soul (alchemy) offer goes alone and shows no "Vložit vše" box."""
		if windowType != player.INVENTORY:
			return []
		return [slot for slot in _ListingInventorySlots()
			if slot != int(firstSlot) and self._IsOfferableStack(windowType, slot, vnum)]

	def _OfferAllStacks(self, windowType, firstSlot, vnum, sources=None):
		"""Piece counts of the slots "Vložit vše" takes from, the first offer's slot first."""
		if sources is None:
			sources = self._OfferAllSources(windowType, firstSlot, vnum)
		counts = []
		for slot in [int(firstSlot)] + list(sources):
			try:
				counts.append(int(player.GetItemCount(windowType, slot)))
			except Exception:
				counts.append(0)
		return counts

	def _OfferAllRoom(self, vnum):
		"""The shop's free cells for listings of the item (its height)."""
		cells = int(getattr(virtualmarket, "LAYOUT_MAXIMUM_PAGES", 64)) * GRID_SLOT_COUNT
		return max(0, cells - len(self._OwnerOccupiedCells())) // max(1, _ItemHeight(vnum))

	def _OfferAllCount(self, windowType, firstSlot, vnum, piece, sources=None):
		"""How many listings of ``piece`` pieces "Vložit vše" can make, the first offer included (owner 21. 10.:
		every listing has the first offer's count and price; a stack is split into as many as it holds, a rest
		smaller than ``piece`` stays in the inventory). Never more than the free cells of the shop."""
		piece = int(piece)
		if piece <= 0:
			return 0
		if sources is None:
			sources = self._OfferAllSources(windowType, firstSlot, vnum)
		if not sources and windowType != player.INVENTORY:
			return 0
		total = 0
		for slot in [int(firstSlot)] + list(sources):
			try:
				total += int(player.GetItemCount(windowType, slot)) // piece
			except Exception:
				pass
		height = _ItemHeight(vnum)
		cells = int(getattr(virtualmarket, "LAYOUT_MAXIMUM_PAGES", 64)) * GRID_SLOT_COUNT
		room = max(0, cells - len(self._OwnerOccupiedCells())) // max(1, height)
		return min(total, room)

	def _PriceOffer(self, suggestedPrice):
		"""The held offer's price is known: Shift + right-click sends it at once, otherwise the dialog opens."""
		if getattr(self, "offerUsesPreviousPrice", False) and self.offer and int(suggestedPrice or 0) > 0:
			self.offerUsesPreviousPrice = False
			if not self._SubmitOffer(int(suggestedPrice)):
				self._ClearOffer()
			return
		self._OpenOfferPriceDialog(suggestedPrice)

	def _OpenOfferPriceDialog(self, suggestedPrice):
		stacks, room = [], 0
		offerAllSources = getattr(self, "_OfferAllSources", None)
		if self.offer and offerAllSources:
			windowType, position, count, vnum = self.offer[:4]
			if windowType == player.INVENTORY:
				stacks = self._OfferAllStacks(windowType, position, vnum, offerAllSources(windowType, position, vnum))
				room = self._OfferAllRoom(vnum)
		if sum(stacks) >= 2 and room >= 2:
			# "Vložit vše": "Po [X] ks · Hromádek: [N]" (owner 21. 10.), the price of 1 piece while checked
			self.priceDialog.SetContext(self.offer[2], offerAllStacks=stacks, offerAllRoom=room)
		else:
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
			getattr(self, "_PriceOffer", self._OpenOfferPriceDialog)(suggestedPrice)
		else:
			self._OpenOfferPriceDialog(0)

	def _ClearOffer(self, slotIndex=0):
		self.offer = None
		self.offerUsesPreviousPrice = False

	def _AcceptOfferPrice(self):
		if self.repricingListingId > 0:
			price = int(self.priceDialog.GetValue())
			if price <= 0 or price > 10000000000:
				self._SetStatus(_Text("VIRTUAL_MARKET_PRICE_RANGE", "Cena musí být od 1 do 10 000 000 000 Yangů."))
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
					"Cena nab\u00eddky se m\u011bn\u00ed..."))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_REQUEST_BUSY",
					"Te\u010f to nejde. Zkus to za chv\u00edli."))
			return True
		if not self.offer:
			self.priceDialog.Hide()
			return True
		price = int(self.priceDialog.GetValue())
		# "Vložit vše" (owner 21. 10.): N listings of X pieces, the field is the price of 1 piece.
		offerAll = getattr(self, "_OfferAllSources", None) is not None and \
			getattr(self.priceDialog, "IsOfferAll", lambda: False)() is True
		piece = int(self.priceDialog.GetOfferAllPiece()) if offerAll else 0
		if offerAll:
			price *= piece
		if price <= 0 or price > 10000000000:
			self._SetStatus(_Text("VIRTUAL_MARKET_PRICE_RANGE", "Cena musí být od 1 do 10 000 000 000 Yangů."))
			return True
		windowType, position, count, vnum, targetPosition, height = self.offer
		if not _IsListingInventorySource(windowType, position) or \
				int(player.GetItemIndex(windowType, position)) != vnum or \
				int(player.GetItemCount(windowType, position)) < count:
			self.priceDialog.Hide()
			self._ClearOffer()
			self._SetStatus(_Text("VIRTUAL_MARKET_OFFER_SOURCE_CHANGED",
				"The item or its count changed. Select it again."))
			return True
		# "Vložit vše": N listings of X pieces for X times the price of 1 piece, one by one (_ContinueOfferAll);
		# the server splits a stack, a rest smaller than X stays in the inventory.
		self.priceDialog.Hide()
		if offerAll:
			total = int(self.priceDialog.GetOfferAllCount())
			self.offerAll = {
				"vnum": int(vnum), "price": int(price), "count": piece,
				"slots": [int(position)] + list(self._OfferAllSources(windowType, position, vnum)),
				"done": 0, "total": total, "nextAt": 0, "cancelled": False,
			}
			# the first listing from the offered slot into the cell the seller chose, as an ordinary offer
			self.offer = (windowType, position, piece, vnum, targetPosition, height)
			if int(player.GetItemCount(windowType, position)) >= piece and net.SendVirtualMarketListingCreate(
					windowType, position, piece, price, vnum, targetPosition):
				self.pendingListingCreate = (int(vnum), piece, int(price))
				self.offerAll["nextAt"] = app.GetTime() + OFFER_ALL_STEP_DELAY
				self._SetStatus(self._OfferAllProgressText())
			else:
				self._ClearOffer()
				self._ContinueOfferAll()            # the offered slot holds less than X: the next one that does
			return True
		if net.SendVirtualMarketListingCreate(
				windowType, position, count, price, vnum, targetPosition):
			self.pendingListingCreate = (int(vnum), int(count), int(price))
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_CREATING",
				"P\u0159edm\u011bt se ukl\u00e1d\u00e1 na trh..."))
		else:
			self._ClearOffer()
		return True

	def _SubmitOffer(self, price):
		"""Send the held offer at this total price (Shift + right-click, the further stacks of "Vložit vše");
		False (the offer stays held) when it was not sent. _AcceptOfferPrice sends the dialog's offer itself."""
		windowType, position, count, vnum, targetPosition, height = self.offer
		if not _IsListingInventorySource(windowType, position) or \
				int(player.GetItemIndex(windowType, position)) != vnum or \
				int(player.GetItemCount(windowType, position)) < count:
			self._SetStatus(_Text("VIRTUAL_MARKET_OFFER_SOURCE_CHANGED",
				"The item or its count changed. Select it again."))
			return False
		if not net.SendVirtualMarketListingCreate(
				windowType, position, count, price, vnum, targetPosition):
			return False
		self.pendingListingCreate = (int(vnum), int(count), int(price))
		self._SetStatus(_Text(
			"VIRTUAL_MARKET_LISTING_CREATING",
			"P\u0159edm\u011bt se ukl\u00e1d\u00e1 na trh...") if not getattr(self, "offerAll", None) else
			self._OfferAllProgressText())
		return True

	# -- "Vložit vše (N×)" ----------------------------------------------------

	def _OfferAllProgressText(self):
		batch = self.offerAll
		if not batch:
			return ""
		return _Text("VIRTUAL_MARKET_OFFER_ALL_PROGRESS", "Vkl\u00e1d\u00e1n\u00ed na trh: %d/%d") % (
			batch["done"], batch["total"])

	def _StopOfferAll(self, text=None, reload=True):
		"""End "Vložit vše"; a create already sent still finishes as an ordinary offer. The owner shop and its
		listings are read once here (reload): during the batch each created listing is drawn from its answer."""
		batch, self.offerAll = self.offerAll, None
		if batch and text is not None:
			self._SetStatus(text % (batch["done"], batch["total"]) if "%d" in text else text)
		if batch and reload and batch["done"] > 0:
			send = getattr(net, "SendVirtualMarketOwnerShop", None)
			if send:
				send()
			self._ReloadOwnerListings()

	def _StopOfferAllWithReason(self, reason):
		batch = self.offerAll
		if not batch:
			return
		self._StopOfferAll()
		self._SetStatus(_Text("VIRTUAL_MARKET_OFFER_ALL_STOPPED",
			"Vkl\u00e1d\u00e1n\u00ed zastaveno (%d/%d). %s") % (batch["done"], batch["total"], reason))

	def _CancelOfferAll(self):
		"""The status button while "Vložit vše" runs: no further stack is offered."""
		batch = self.offerAll
		if not batch:
			return
		if self.pendingListingCreate:
			# The stack already sent is answered first; its result ends the batch.
			batch["cancelled"] = True
			batch["slots"] = []
			self._SetStatus(_Text("VIRTUAL_MARKET_OFFER_ALL_CANCELLING",
				"Ru\u0161\u00ed se, dokon\u010duje se posledn\u00ed p\u0159edm\u011bt..."))
			return
		self._StopOfferAll(_Text("VIRTUAL_MARKET_OFFER_ALL_CANCELLED",
			"Vkl\u00e1d\u00e1n\u00ed zru\u0161eno (%d/%d)."))

	def _ContinueOfferAll(self):
		"""Offer the next stack once the previous one is answered: the same checks as a right-click, the first
		free cell, the price per piece of the first stack. A full shop or a refusal ends it with its reason."""
		batch = self.offerAll
		if not batch or self.offer or self.pendingListingCreate or self._GetOperationRetry():
			return
		if batch["cancelled"]:
			self._StopOfferAll(_Text("VIRTUAL_MARKET_OFFER_ALL_CANCELLED",
				"Vkl\u00e1d\u00e1n\u00ed zru\u0161eno (%d/%d)."))
			return
		if batch["done"] >= batch["total"]:
			self._StopOfferAll(_Text("VIRTUAL_MARKET_OFFER_ALL_DONE", "Vlo\u017eeno na trh: %d/%d"))
			return
		if app.GetTime() < batch["nextAt"]:
			return
		if not self.CanQuickOffer():
			self._StopOfferAllWithReason(_Text("VIRTUAL_MARKET_UNAVAILABLE",
				"Trh te\u010f nen\u00ed dostupn\u00fd. Zkus to znovu."))
			return
		if not self._OwnerLayoutKnown():
			return                                  # free cells are known once the reload is complete
		vnum, count, price = batch["vnum"], batch["count"], batch["price"]
		while batch["slots"]:
			slot = batch["slots"][0]
			if not self._IsOfferableStack(player.INVENTORY, slot, vnum) or \
					int(player.GetItemCount(player.INVENTORY, slot)) < count:
				batch["slots"].pop(0)               # moved, used up, or a rest smaller than one listing stays
				continue
			height = _ItemHeight(vnum)
			position = self._FindFreeOwnerPosition(height)
			if position < 0:
				self._StopOfferAllWithReason(_Text("VIRTUAL_MARKET_OFFER_ALL_SHOP_FULL",
					"V obchod\u011b u\u017e nen\u00ed voln\u00e9 m\u00edsto."))
				return
			# The same count and the same price as the first offer; the server splits the stack.
			self.offer = (int(player.INVENTORY), int(slot), int(count), int(vnum), int(position), int(height))
			if not self._SubmitOffer(price):
				self._ClearOffer()
				self._StopOfferAllWithReason(_Text("VIRTUAL_MARKET_REQUEST_BUSY",
					"Te\u010f to nejde. Zkus to za chv\u00edli."))
				return
			batch["nextAt"] = app.GetTime() + OFFER_ALL_STEP_DELAY
			return
		self._StopOfferAll(_Text("VIRTUAL_MARKET_OFFER_ALL_DONE", "Vlo\u017eeno na trh: %d/%d"))

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
		self.boxCount.SetText(_Text("VIRTUAL_MARKET_ITEM_COUNT", "%d předmětů") % count)
		self.gridPages = _PackGridRecords(records)
		self.currentPage = min(self.currentPage, max(0, len(self.gridPages) - 1))
		wanted = {}
		for packed in self.gridPages[self.currentPage]:
			slotIndex, nativeIndex, vnum, itemCount, kind, source, sourceId, price = packed
			payload = (source, sourceId, vnum, itemCount)
			# Keep neighboring anchors/pages stable until the durable result arrives.
			if payload in pending:
				continue
			wanted[int(slotIndex)] = (int(vnum), int(itemCount))
			entry = (kind, int(nativeIndex), payload, int(price))
			_MapGridItemFootprint(
				self.gridSlotMap, slotIndex, _ItemHeight(vnum), entry)
		_SyncGridItems(self.boxGrid, self.boxGridShown, wanted)
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
				"Všechny předměty byly vyzvednuty."))
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

	def _SnapshotAttrChangeCount(self, getSocket, index):
		# Older snapshot getters may refuse the sixth socket; no line then.
		try:
			return max(0, int(getSocket(index, ATTR_CHANGE_COUNT_SOCKET)))
		except Exception:
			return 0

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
			attrChangeCount = self._SnapshotAttrChangeCount(getSocket, index)
			if attrChangeCount:
				# The same line as the inventory tooltip (SetInventoryItem).
				tooltip.AppendTextLine(
					localeInfo.TOOLTIP_ATTR_CHANGE_COUNT % attrChangeCount,
					tooltip.NORMAL_COLOR)
				tooltip.ResizeToolTip()
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
					"Předměty se postupně vyzvedávají..."))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIMING", "Předmět se vyzvedává..."))
		else:
			canRetry = getattr(
				virtualmarket, "CanRetryItemClaimIntent", lambda *args: 0)
			if bool(canRetry(source, sourceId, vnum, count)):
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIM_RETRY_EXACT",
					"Předmět se nepodařilo vyzvednout. "
					"Zkus ho vyzvednout znovu."),
					lambda item=payload: self._Claim(item))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_CLAIM_BUSY_OTHER",
					"Předmět teď nejde vyzvednout, protože probíhá "
					"jiná akce na trhu."))
		return sent

	def OnSearchResult(self, token, status, appended, hasMore):
		if int(status) == virtualmarket.STATUS_RATE_LIMITED and self.searchRetryEvent:
			# Two searches inside the server's 250 ms window: resend once.
			self.searchRetryAt = app.GetTime() + SEARCH_RATE_LIMIT_RETRY_DELAY
			self._SetStatus(_Text("VIRTUAL_MARKET_LOADING", "Na\u010d\u00edt\u00e1n\u00ed..."))
			return
		self.searchRetryEvent = None
		if int(status) != virtualmarket.STATUS_OK:
			self._SetStatus(self._StatusError(status))
			self._SetMarketEmptyState(
				_Text("VIRTUAL_MARKET_REQUEST_FAILED", "Trh nelze na\u010d\u00edst"),
				self._StatusError(status),
				_Text("VIRTUAL_MARKET_REQUEST_FAILED_DETAIL", "Zkus to za chv\u00edli znovu."))
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
			if int(status) == virtualmarket.STATUS_RATE_LIMITED and self._OwnerListingsLoading():
				# A refused page keeps what is loaded; ask for it again. This server holds next pages
				# to its read limit, so the following pages wait for it too.
				self.ownerNextPageDelay = OWNER_LISTINGS_PAGE_DELAY
				self._ArmOwnerListingsPage()
				return
			self.ownerListingsNextAt = 0.0
			self.ownerReloadHoldUntil = 0.0
			if not appended:
				# The native client dropped its list with the failed first page.
				self.ownerNativeOk = False
			if int(status) == virtualmarket.STATUS_RATE_LIMITED and not appended and \
					self.ownerReloadRetries < OWNER_LISTINGS_PAGE_ATTEMPTS:
				# A reload right after another one is refused by the server's read limit: ask again.
				self.ownerReloadRetries += 1
				self.ownerReloadRetryAt = app.GetTime() + OWNER_LISTINGS_PAGE_DELAY
			elif self.currentTab == TAB_OWNER:
				self._SetStatus(self._StatusError(status), readStatus=True)
			self._RefreshOwnerGrid()
			return
		if not appended:
			self.ownerNativeOk = True
		if self.advanceAfterAppend and appended:
			self.currentPage += 1
		self.advanceAfterAppend = False
		self.ownerListingsAttempts = 0
		if hasMore:
			if (not appended and self.ownerModelComplete) or self.ownerReloadHoldUntil:
				# A reload of a multi-page shop: page 1 replaced the list. Keep the
				# complete layout on screen until the last page is appended; every
				# page that arrives keeps the hold, only a stalled reload ends it.
				self.ownerReloadHoldUntil = app.GetTime() + OWNER_RELOAD_HOLD_MAX
			self._ArmOwnerListingsPage(self.ownerNextPageDelay)
		else:
			self.ownerListingsNextAt = 0.0
			self.ownerReloadHoldUntil = 0.0
			self.ownerReloadRetries = 0
			# The complete list now shows every change confirmed before this reload was sent.
			serial = self.ownerReloadSerial
			for listingId in [listingId for listingId, change in self.ownerLocalChanges.items()
					if change[0] < serial]:
				del self.ownerLocalChanges[listingId]
		if self.currentTab == TAB_OWNER:
			self._SetStatus("", preserveMessage=True)
			self._RefreshOwnerGrid()
			if not hasMore:
				self.ownerHoverRefresh = True     # OnUpdate: the hovered tooltip once the grid is drawn

	def _OwnerShopSnapshot(self):
		"""The own shop as the last read with status OK left it. A read refused by the rate limit leaves an empty
		native copy, which must not turn an open shop into "zavřen" with Založit."""
		shop = tuple(virtualmarket.GetOwnerShop())
		statusOf = getattr(virtualmarket, "GetOwnerShopStatus", None)
		if statusOf is None or int(statusOf()) == virtualmarket.STATUS_OK:
			self.ownerShopLastGood = shop
			return shop
		lastGood = getattr(self, "ownerShopLastGood", None)
		if int(statusOf()) == getattr(virtualmarket, "STATUS_RATE_LIMITED", -1) and lastGood is not None:
			return lastGood
		return shop                                 # disabled, unavailable: the market really has no shop now

	def _ScheduleOwnerShopRetry(self, status):
		if int(status) != getattr(virtualmarket, "STATUS_RATE_LIMITED", -1) or \
				self.ownerShopRetryAttempts >= OWNER_SHOP_RETRY_ATTEMPTS:
			return False
		self.ownerShopRetryAttempts += 1
		self.ownerShopRetryAt = app.GetTime() + OWNER_SHOP_RETRY_DELAY
		return True

	def _RunOwnerShopRetry(self):
		self.ownerShopRetryAt = 0.0
		send = getattr(net, "SendVirtualMarketOwnerShop", None)
		if send:
			send()

	def OnOwnerShopResult(self, token, status):
		if int(status) != virtualmarket.STATUS_OK:
			if self._ScheduleOwnerShopRetry(status):
				return                              # the last shop stays shown; asked again by itself
			self.ownerShopRetryAttempts = 0
			if self.currentTab == TAB_OWNER:
				self._SetStatus(self._StatusError(status), readStatus=True)
			return
		self.ownerShopRetryAttempts = 0
		self._UpdateSidebarSellers()
		if self.currentTab == TAB_OWNER:
			self._SetStatus("", preserveMessage=True)
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
			self._SetStatus(self._StatusError(status), readStatus=True)
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
		self._SetStatus("", preserveMessage=True)

	def OnShopCommandResult(self, token, status, command, result, replayed):
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.COMMAND_RESULT_APPLIED:
			self._SetStatus(_Text("VIRTUAL_MARKET_SHOP_UPDATED", "Obchod je aktualizovan\u00fd."))
			net.SendVirtualMarketOwnerShop()
			self._ReloadOwnerListings()
			return
		if int(status) == virtualmarket.STATUS_OK and \
				int(result) == getattr(virtualmarket, "COMMAND_RESULT_ALREADY_OPEN", -1):
			# The shop is open although this window showed it closed: read it again, the grid comes back.
			net.SendVirtualMarketOwnerShop()
			self._ReloadOwnerListings()
		retry = net.SendVirtualMarketShopRetry if virtualmarket.CanRetryShopCommand() else None
		self._SetStatus(self._StatusError(status, result), retry)

	def OnListingCreateResult(self, token, status, result, replayed):
		if int(status) == virtualmarket.STATUS_OK:
			self.operationRetryAttempts = 0     # answered: a later rate limit gets its own resends
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.LISTING_RESULT_APPLIED:
			if self.pendingListingCreate:
				vnum, count, rememberedPrice = self.pendingListingCreate
				getattr(virtualmarket, "CachePricePreference", lambda *args: 0)(
					vnum, rememberedPrice, count)
				self._RecordCreatedListing(vnum, count, rememberedPrice)
			self.pendingListingCreate = None
			self._ClearOffer()
			if getattr(self, "offerAll", None):
				# The listing is drawn from this answer; the shop is read once when the batch ends
				# (_StopOfferAll), not after every listing.
				self.offerAll["done"] += 1
				if not self.offerAll["cancelled"]:
					self._SetStatus(self._OfferAllProgressText())
				self._ContinueOfferAll()
				return
			self._SetStatus(_Text("VIRTUAL_MARKET_LISTED", "P\u0159edm\u011bt je ulo\u017een\u00fd na trhu."))
			net.SendVirtualMarketOwnerShop()
			self._ReloadOwnerListings()
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == \
				virtualmarket.LISTING_RESULT_DISPLAY_SLOT_OCCUPIED:
			self.pendingListingCreate = None
			self._ClearOffer()
			slotChanged = _Text(
				"VIRTUAL_MARKET_SLOT_CHANGED",
				"Zvolen\u00e9 m\u00edsto u\u017e obsadila jin\u00e1 nab\u00eddka. Vyber jin\u00fd slot.")
			if getattr(self, "offerAll", None):
				self._StopOfferAllWithReason(slotChanged)
			else:
				self._SetStatus(slotChanged)
			self._ReloadOwnerListings()
			return
		retry = net.SendVirtualMarketListingCreateRetry if virtualmarket.CanRetryListingCreate() else None
		if self._ScheduleRateLimitRetry(status, retry):
			return                              # keeps the offer: the same native create is resent by itself
		if not retry:
			self.pendingListingCreate = None
			self._ClearOffer()
		if getattr(self, "offerAll", None):
			# A refusal ends "Vložit vše"; an unresolved create keeps its "Opakovat".
			reason = self._StatusError(status, result)
			self._StopOfferAllWithReason(reason)
			if retry:
				self._SetStatus(reason, retry)
			return
		self._SetStatus(self._StatusError(status, result), retry)

	def OnListingMoveResult(self, token, status, result, replayed):
		move, self.pendingListingMove = self.pendingListingMove, None
		if int(status) == virtualmarket.STATUS_OK:
			self.operationRetryAttempts = 0     # answered: a later rate limit gets its own resends
		if int(status) == virtualmarket.STATUS_OK and \
				int(result) == virtualmarket.LISTING_MOVE_RESULT_APPLIED and move:
			self._RecordOwnerChange(move[0], self._OwnerRecord(move[0], displaySlot=move[1]))
		if int(status) == virtualmarket.STATUS_OK:
			self._ReloadOwnerListings()
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
				"Tuhle nab\u00eddku pr\u00e1v\u011b n\u011bkdo kupuje. Zkus to za chv\u00edli."))
			return
		retry = net.SendVirtualMarketListingMoveRetry \
			if virtualmarket.CanRetryListingMove() else None
		if self._ScheduleRateLimitRetry(status, retry):
			return
		self._SetStatus(self._StatusError(status, result), retry)

	def OnListingMutationResult(self, token, status, mutation, result, replayed,
			listingId, price):
		status = int(status)
		mutation = int(mutation)
		result = int(result)
		if status == virtualmarket.STATUS_OK:
			self.operationRetryAttempts = 0     # answered: a later rate limit gets its own resends
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
				self._RecordOwnerChange(listingId, None, removed=True)
			elif mutation != getattr(virtualmarket, "LISTING_MUTATION_REPRICE_MATCHING", -1):
				self._RecordOwnerChange(listingId, self._OwnerRecord(listingId, price=price))
			if mutation == virtualmarket.LISTING_MUTATION_CANCEL:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_LISTING_CANCELED",
					"Nab\u00eddka je zru\u0161en\u00e1. P\u0159edm\u011bt \u010dek\u00e1 v z\u00e1lo\u017ece Vr\u00e1cen\u00e9."))
				net.SendVirtualMarketSellerReturns()
			elif mutation == getattr(virtualmarket, "LISTING_MUTATION_REPRICE_MATCHING", -1):
				self._SetStatus(_Text("VIRTUAL_MARKET_MATCHING_REPRICED",
					"Ceny shodných předmětů se změnily podle ceny za kus."))
			else:
				self._SetStatus(_Text(
					"VIRTUAL_MARKET_LISTING_REPRICED",
					"Cena nab\u00eddky byla zm\u011bn\u011bna na %s.") % _Money(price))
			net.SendVirtualMarketOwnerShop()
			if mutation != getattr(virtualmarket, "LISTING_MUTATION_REPRICE_MATCHING", -1) and \
					getattr(self, "ownerModelComplete", False) and getattr(self, "ownerNativeOk", False) and \
					not getattr(virtualmarket, "OwnerListingsHasMore", lambda: 0)() and \
					not getattr(self, "ownerReloadHoldUntil", 0.0) and not getattr(self, "ownerReloadRetryAt", 0.0):
				# Native mutation results already update the complete list; keep its tooltip indexes.
				getattr(self, "ownerLocalChanges", {}).pop(int(listingId), None)
				self._RefreshOwnerGrid()
			else:
				self._ReloadOwnerListings()
			return
		if status == virtualmarket.STATUS_OK and result == \
				virtualmarket.LISTING_MUTATION_RESULT_LISTING_BUSY:
			self._SetStatus(_Text(
				"VIRTUAL_MARKET_LISTING_BUSY",
				"Tuhle nab\u00eddku pr\u00e1v\u011b n\u011bkdo kupuje. Zkus to za chv\u00edli."))
			return
		if status == virtualmarket.STATUS_OK and result == virtualmarket.LISTING_MUTATION_RESULT_INVALID_PRICE:
			self.pendingReprice = None
			self._SetStatus(_Text("VIRTUAL_MARKET_MATCHING_PRICE_LIMIT",
				"Cena některého balíku by překročila 10 000 000 000 Yangů. Žádná cena se nezměnila."))
			return
		retry = getattr(net, "SendVirtualMarketListingMutationRetry", None) \
			if getattr(virtualmarket, "CanRetryListingMutation", lambda: 0)() else None
		if self._ScheduleRateLimitRetry(status, retry):
			return
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
						"Předměty se postupně vyzvedávají..."))
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
			self._SetStatus(_Text("VIRTUAL_MARKET_PURCHASED", "N\u00e1kup prob\u011bhl. P\u0159edm\u011bt \u010dek\u00e1 v z\u00e1lo\u017ece N\u00e1kupy."))
			self._RepeatMarketSearch()
			return
		retry = net.SendVirtualMarketPurchaseRetry if virtualmarket.CanRetryPurchase() else None
		self._ShowPurchaseFailure(status, result, retry)

	def _ShowPurchaseFailure(self, status, result, retry):
		"""A refused purchase says why and that no Yang was taken; a listing that is gone reloads the offers."""
		failure = marketpurchasefailure.PurchaseFailure(result, _Text) \
			if int(status) == virtualmarket.STATUS_OK and not retry else None
		if failure is None:
			self._SetStatus(self._StatusError(status, result), retry)
			return
		text, reload = failure
		if reload:
			self._ClearPurchaseSelection()
			self._RepeatMarketSearch()
		self._SetStatus(text)

	def OnBatchPurchaseResult(self, token, status, result, replayed, state, itemCount):
		if int(status) == virtualmarket.STATUS_OK and int(result) in (
			virtualmarket.PURCHASE_RESULT_APPLIED, virtualmarket.PURCHASE_RESULT_REPLAYED):
			self._ClearPurchaseSelection()
			self._SetStatus(_Text("VIRTUAL_MARKET_BATCH_PURCHASED",
				"Nákup %d nabídek proběhl. Předměty čekají v záložce Nákupy.") % int(itemCount))
			self._RepeatMarketSearch()
			return
		canRetry = getattr(virtualmarket, "CanRetryBatchPurchase", lambda: 0)
		retry = getattr(net, "SendVirtualMarketBatchPurchaseRetry", None) if canRetry() else None
		self._ShowPurchaseFailure(status, result, retry)

	def OnSellerWithdrawalResult(self, token, status, result, replayed):
		if int(status) == virtualmarket.STATUS_OK and int(result) in (
			virtualmarket.WITHDRAWAL_RESULT_APPLIED, virtualmarket.WITHDRAWAL_RESULT_REPLAYED):
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAWN", "V\u00fdt\u011b\u017eek m\u00e1\u0161 p\u0159ipsan\u00fd k Yang\u016fm."))
			net.SendVirtualMarketOwnerShop()
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.WITHDRAWAL_RESULT_CONFLICT:
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAW_BUSY",
				"Pr\u00e1v\u011b prob\u00edh\u00e1 jin\u00e1 akce. Zkus Yangy vybrat znovu."),
				net.SendVirtualMarketSellerWithdrawal)
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.WITHDRAWAL_RESULT_NO_CREDIT:
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAW_EMPTY", "K vyzvednut\u00ed nejsou \u017e\u00e1dn\u00e9 Yangy."))
			return
		if int(status) == virtualmarket.STATUS_OK and int(result) == virtualmarket.WITHDRAWAL_RESULT_YANG_LIMIT:
			self._SetStatus(_Text("VIRTUAL_MARKET_WITHDRAW_LIMIT",
				"V\u00fdb\u011br by p\u0159ekro\u010dil limit Yang\u016f postavy."))
			return
		retry = net.SendVirtualMarketSellerWithdrawalRetry if virtualmarket.CanRetrySellerWithdrawal() else None
		self._SetStatus(self._StatusError(status, result), retry)

	def _StatusError(self, status, result=None):
		status = int(status)
		if status == virtualmarket.STATUS_DISABLED:
			return _Text("VIRTUAL_MARKET_DISABLED", "Trh je te\u010f vypnut\u00fd.")
		if status == virtualmarket.STATUS_UNAVAILABLE:
			return _Text("VIRTUAL_MARKET_UNAVAILABLE", "Trh te\u010f nen\u00ed dostupn\u00fd. Zkus to znovu.")
		if status == virtualmarket.STATUS_RATE_LIMITED:
			return _Text("VIRTUAL_MARKET_RATE_LIMIT", "Chv\u00edli po\u010dkej a zkus to znovu.")
		return (_Text("VIRTUAL_MARKET_ERROR",
			"Akce se nepovedla (k\u00f3d %d, %s).") %
			(status, str(result) if result is not None else "-"))

	def _ScheduleRateLimitRetry(self, status, sender):
		"""A listing change refused only by the game's rate limit: resend the same native operation by itself
		(OPERATION_RATE_LIMIT_RETRY_DELAY), so it does not wait for "Opakovat" and block the other actions."""
		if int(status) != getattr(virtualmarket, "STATUS_RATE_LIMITED", -1) or not sender or \
				self.operationRetryAttempts >= OPERATION_RATE_LIMIT_RETRY_ATTEMPTS:
			self.operationRetryAttempts = 0
			return False
		self.operationRetryAttempts += 1
		self.operationRetrySender = sender
		self.operationRetryAt = app.GetTime() + OPERATION_RATE_LIMIT_RETRY_DELAY
		self._SetStatus(_Text("VIRTUAL_MARKET_RETRYING",
			"Čeká se na dokončení předchozí akce..."), sender)
		return True

	def _RunOperationRetry(self):
		sender, self.operationRetrySender = self.operationRetrySender, None
		self.operationRetryAt = 0.0
		if not sender or self._GetOperationRetry() != sender:
			return                                  # resolved meanwhile (Opakovat, reconnect)
		if sender():
			return
		if self.operationRetryAttempts < OPERATION_RATE_LIMIT_RETRY_ATTEMPTS:
			# another market request is still on the way: try again a bit later
			self.operationRetryAttempts += 1
			self.operationRetrySender = sender
			self.operationRetryAt = app.GetTime() + OPERATION_RATE_LIMIT_RETRY_DELAY
			return
		self.operationRetryAttempts = 0
		self._SetStatus(_Text("VIRTUAL_MARKET_RATE_LIMIT", "Chvíli počkej a zkus to znovu."), sender)

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
		if self.ownerReloadHoldUntil and app.GetTime() >= self.ownerReloadHoldUntil:
			# No page arrived for a while: the grid keeps the last complete layout and asks for the list again.
			self.ownerReloadHoldUntil = 0.0
			if self.ownerReloadRetries < OWNER_LISTINGS_PAGE_ATTEMPTS:
				self.ownerReloadRetries += 1
				self.ownerReloadRetryAt = app.GetTime()
			self._RefreshOwnerGrid()
		if self.ownerReloadRetryAt and app.GetTime() >= self.ownerReloadRetryAt:
			self.ownerReloadRetryAt = 0.0
			self._ReloadOwnerListings()
		self._FlushOwnerGrid()
		if getattr(self, "ownerHoverRefresh", False):
			self.ownerHoverRefresh = False
			self._ShowHoveredOwnerTooltip()
		self._SyncPendingClaim()
		if self.ownerDragListingId and not self._IsOwnerDrag():
			self._CancelOwnerDrag()
		self._UpdateSearchSuggestions()
		self._AnimateRail()
		now = app.GetTime()
		if self.searchRetryAt and now >= self.searchRetryAt:
			self._RunSearchRetry()
		if self.operationRetryAt and now >= self.operationRetryAt:
			self._RunOperationRetry()
		if self.ownerShopRetryAt and now >= self.ownerShopRetryAt:
			self._RunOwnerShopRetry()
		if getattr(self, "offerAll", None):
			self._ContinueOfferAll()
		if self.ownerListingsNextAt and now >= self.ownerListingsNextAt:
			self._LoadNextOwnerListingsPage()
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
		if getattr(self, "salesHistory", None) is not None and self.ownerView == "history":
			self.salesHistory.Update()
		if now - self.lastLeaseRefresh < 0.5:
			return
		self.lastLeaseRefresh = now
		self._RefreshOwner()
