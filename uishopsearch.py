import ui
import localeInfo
import uiScriptLocale
import item
import grp
import shopsearch
import net
import uiToolTip
import uiCommon
import player
import app
import osfInfo
import cfg
import time
import helper
import chrmgr
import wndMgr

import math

import grp

from _weakref import proxy
from operator import truediv
ROOT_PATH = "d:/ymir work/ui/game/search_shop/{}"
ROOT_PATH_ITEM_SLOT = "d:/ymir work/ui/game/search_shop/items/slots/{}.png"
TWN_SPACER_Y = 10

categoryPeakWindowSize = [150, 486-5]
itemPeakWindowSize = [570, 475]

#######################################################
## CATEGORY_PROTO STRUCTURE:
## [ <-- proto list start
##   { <-- category start
##	 "icon" : <icon_path_name>,
##	 "name" : <display_name>,
##	 "itemvnum" : 139 OR (129, 139, 149) OR (129, "130~139", 149), <-- accepts the specific vnum 139 OR the vnums 129, 139, 149 OR the vnums 129, 130, 131, 132, ..., 139, 149 as well as the item types (optional)
########################## ITEM_TYPE:
############# OPTION 1:
##	 "itemtype" : item.ITEM_TYPE_WEAPON, <-- accepts all items with item type = weapon
############# OPTION 2:
##	 "itemtype" : (item.ITEM_TYPE_WEAPON, item.WEAPON_ARROW, item.WEAPON_FAN), <-- accepts all items with item type = weapon and sub type = arrow or fan (add as many subtypes as you want)
############# OPTION 3:
##	 "itemtype" : [
##	   (item.ITEM_TYPE_WEAPON, item.WEAPON_SWORD, item.WEAPON_TWO_HANDED), <-- accepts all items with item type = weapon and sub type = sword or two handed
##	   item.ITEM_TYPE_ARMOR, <-- AND accepts all items with item type = armor
##	   <-- you could add any more item types to be accepted by this category
##	 ],
########################## END OF ITEM_TYPE
##   }, <-- category end
## ] <-- proto list end
#######################################################
CATEGORY_PROTO = [
	##############################
	## ALL CATEGORY
	{
		"icon" : "everything",
		"name" : localeInfo.SHOP_SEARCH_CAT_ALL,
		"itemtype" : list(range(item.ITEM_TYPE_MAX_NUM)),
	},
	{
		"icon" : "weapons",
		"name" : localeInfo.SHOP_SEARCH_CAT_WEAPON,
		"itemtype" : item.ITEM_TYPE_WEAPON,
		"sub_category" : [
			## SWORD SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_WEAPON_SWORD,
				"itemtype" : (item.ITEM_TYPE_WEAPON, item.WEAPON_SWORD),
			},
			## TWOHANDED SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_WEAPON_TWOHANDED,
				"itemtype" : (item.ITEM_TYPE_WEAPON, item.WEAPON_TWO_HANDED),
			},
			## DAGGER SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_WEAPON_DAGGER,
				"itemtype" : (item.ITEM_TYPE_WEAPON, item.WEAPON_DAGGER),
			},
			## BOW SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_WEAPON_BOW,
				"itemtype" : (item.ITEM_TYPE_WEAPON, item.WEAPON_BOW),
			},
			## FAN SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_WEAPON_FAN,
				"itemtype" : (item.ITEM_TYPE_WEAPON, item.WEAPON_FAN),
			},
			## BELL SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_WEAPON_BELL,
				"itemtype" : (item.ITEM_TYPE_WEAPON, item.WEAPON_BELL),
			},
		],
	},
	## EQUIPMENT CATEGORY
	{
		"icon" : "armors",
		"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT,
		"itemtype" : [ item.ITEM_TYPE_ARMOR, item.ITEM_TYPE_BELT, ],
		"sub_category" : [
			## ARMOR SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_ARMOR,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_BODY),
			},
			## SHIELD SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_SHIELD,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_SHIELD),
			},
			## EARRING SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_EARRING,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_EAR),
			},
			## NECKLACE SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_NECK,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_NECK),
			},
			## BRACELET SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_WRIST,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_WRIST),
			},
			## BOOTS SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_BOOTS,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_FOOTS),
			},
			## HELMET SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_HELMET,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_HEAD),
			},
			## BELT SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_BELT,
				"itemtype" : item.ITEM_TYPE_BELT,
			},
			### PENDANT SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_TALISMAN,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_PENDANT),
			},
			### TALISMAN HEART SUB CATEGORY
			{
				"name" : localeInfo.TOOLTIP_TALISMAN_HEART,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_TALISMAN_HEART),
			},
			### GLOVE SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_EQUIPMENT_GLOVES,
				"itemtype" : (item.ITEM_TYPE_ARMOR, item.ARMOR_GLOVE,),
			},
		],
	},

	## COSTUMES CATEGORY
	{
		"icon" : "costumes",
		"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME,
		"itemtype" : ( item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_BODY, item.COSTUME_TYPE_HAIR, item.COSTUME_TYPE_WEAPON , item.COSTUME_TYPE_EFFECT_WEAPON , item.COSTUME_TYPE_EFFECT_ARMOR),
		"sub_category" : [
			## COSTUMES SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_BODY),
			},
			## HAIRSTYLES SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME_HAIR,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_HAIR),
			},
			## WEAPONSKIN SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME_WEAPON,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_WEAPON),
			},	
			##	SHINING SUB CATEGORY
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME_SHINING,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_EFFECT_WEAPON, item.COSTUME_TYPE_EFFECT_ARMOR),
			},					
		],
	},
	{
		"icon": "sashes",
		"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME_ACCE,
		"itemtype" : ( item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_ACCE, item.COSTUME_TYPE_ACCE_SKIN ),
		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME_ACCE,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_ACCE),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_COSTUME_ACCE_SKIN,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_ACCE_SKIN),
			},
		],
	},	

	{
		"icon": "aura",
		"name" : localeInfo.SHOP_SEARCH_CAT_AURA,
		"itemvnum" : (49983, 49996, 49997, 49998, 49999, 50000, 49970, 49980, 49984, 49990, 49995),
		"itemtype" : ( item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_AURA),
		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_AURA_OUTFIT,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_AURA),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_AURA_RESSOURCE,
				"itemvnum" : (49983, 49996, 49997, 49998, 49999, 50000, 49970, 49980, 49984, 49990, 49995),
			},
		],
	},

	{
		"icon" : "skills",
		"name" : localeInfo.SHOP_SEARCH_CAT_SKILLS,
		"itemtype" : (item.ITEM_TYPE_SKILLBOOK, item.ITEM_TYPE_PET, item.PET_SKILL),
		"itemvnum" : (
		71001, 71094, 70102, 50513, 72810, 50525, 72812, 72813, 71003,
		"50514~50567", "55043~55048", "50314~50316", "50301~50303", 50060, 50600, 50305
		),
		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_IMPROVEMENT,
				"itemvnum" : (71001, 71094, 70102, 50513, 72810, 50525, 72812, 72813, 71003 ),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_NORMAL_SKILLS,
				"itemtype" : (item.ITEM_TYPE_SKILLBOOK),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_PASSIVE_SKILLS,
				"itemvnum" : ("50514~50567", "55043~55048", "50314~50316", "50301~50303", 50060, 50600, 50305),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_PET_SKILLS,
				"itemtype" : (item.ITEM_TYPE_PET, item.PET_SKILL),
			},					
		],
	},
	{
		"icon": "consumeables",
		"name" : localeInfo.SHOP_SEARCH_CAT_CONSUMEABLES,
		"itemvnum" : (
		"50821~50826", 51002, 940031,
		"27800~27892", "50601~50664", 18900
		),
		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_DEWS,
				"itemvnum" : ("50821~50826", 51002),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_FISHES,
				"itemvnum" : ("27800~27892"),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_ORES,
				"itemvnum" : ("50601~50664", 18900),
			},
		],
	},

	{

		"icon": "items",
		"name" : localeInfo.SHOP_SEARCH_CAT_ITEMS,
		"itemtype" : [item.ITEM_TYPE_GIFTBOX, (item.ITEM_TYPE_METIN, item.METIN_NORMAL) ],
		"itemvnum" : (
		27987, 30021, 30022, 30048, 30061, 30091, 
		30193, 30197, 51001, 30195, 30197,
		51003, 30506, 30589, 30587, 30509, 30508, 30500, 30588,  30511, 30512,
		30502, 30610, 30615, 30614, 30602, 30603, 30616, 30617, 30618, 30609,
		30606, 30605, 30517, 30519, 30520, 31005, 31006, 31117, 31120, 71123,
		71129, 70031, 30626,
		"90002~90017",
		"27990~27994", "33001~33022", "33100~33112", "56001~56007",
		33200, 33201, 30324, 60003, 30319, 30179, 71095, 30613, 33203, 33204,
		71084, 71151,
		30006, 30047, 30015, 30050, 30165, 30166,
		30167, 30168, 30251, 30252, 31043, 30628,
		39023, 71097, 71098, 71099,
		),

		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_BONUSES,
				"itemvnum" : (71084, 71151),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_REFINEMENT_MANUFACTURING,
				"itemvnum" : (
				27987, 30021, 30022, 30048, 30061, 30091, 
				30193, 30197, 51001, 30195, 30197,
				51003, 30506, 30589, 30587, 30509, 30508, 30500, 30588,  30511, 30512,
				30502, 30610, 30615, 30614, 30602, 30603, 30616, 30617, 30618, 30609,
				30606, 30605, 30517, 30519, 30520, 31005, 31006, 31117, 31120, 71123,
				71129, 70031, 30626,
				"27990~27994", "33001~33022", "33100~33112", "56001~56007"
				),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_BIOLOGIST,
				"itemvnum" : (30006, 30047, 30015, 30050, 30165,
				30166, 30167, 30168, 30251, 30252, 31043, 30628,
				39023, 71097, 71098, 71099),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_CHESTS,
				"itemtype" : (item.ITEM_TYPE_GIFTBOX),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_STONE,
				"itemtype" : (item.ITEM_TYPE_METIN, item.METIN_NORMAL),
			},
		],
	},
	
	{
		"icon": "mounts",
		"name" : localeInfo.SHOP_SEARCH_CAT_MOUNTS,
		"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_MOUNT),
		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_MOUNTS,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_MOUNT),
			},
		],
	},
	
	{
		"icon": "pets",
		"name" : localeInfo.SHOP_SEARCH_CAT_PETS,
		"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_PET),
		"itemvnum" : ("55401~55799", "55001~55009", "55028~55033", 55100, "55350~55352", "69300~69399"),
		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_PETS,
				"itemtype" : (item.ITEM_TYPE_COSTUME, item.COSTUME_TYPE_PET),
			},
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_PET_GROWTH,
				"itemvnum" : ("55401~55799", "55001~55009", "55028~55033", 55100, "55350~55352"),
			},
			
		],
	},

	{
		"icon": "alchemy",
		"name" : localeInfo.SHOP_SEARCH_CAT_ALCHEMY,
		"itemtype" : [item.ITEM_TYPE_DS, -1],
		"itemvnum" : ("100000~100701", "51511~51516", 50252, 50259),
		"sub_category" : [
			{
				"name" : localeInfo.SHOP_SEARCH_CAT_IMPROVEMENT,
				"itemvnum" : ("100000~100701", "51511~51516", 50252, 50259),
			},
			{
				"name" : uiScriptLocale.DRAGONSOUL_PAGE_BUTTON_2,
				"itemvnum" : ("111000~111499", "121000~121499", "131000~131499", "141000~141499","151000~151499", "161000~161499", "171000~171499"),
			},
			{
				"name" : uiScriptLocale.DRAGONSOUL_PAGE_BUTTON_3,
				"itemvnum" : ("112000~112499", "122000~122499", "132000~132499", "142000~142499","152000~152499", "162000~162499", "172000~172499"),
			},
			{
				"name" : uiScriptLocale.DRAGONSOUL_PAGE_BUTTON_4,
				"itemvnum" : ("113000~113499", "123000~123499", "133000~133499", "143000~143499","153000~153499", "163000~163499", "173000~173499"),
			},
			{
				"name" : uiScriptLocale.DRAGONSOUL_PAGE_BUTTON_5,
				"itemvnum" : ("114000~114499", "124000~124499", "134000~134499", "144000~144499","154000~154499", "164000~164499", "174000~174499"),
			},
			{
				"name" : uiScriptLocale.DRAGONSOUL_PAGE_BUTTON_6,
				"itemvnum" : ("115000~115499", "125000~125499", "135000~135499", "145000~145499","155000~155499", "165000~165499", "175000~175499"),
			},
		],
	},
]

class ShopSearchWindow(ui.ScriptWindow):

	CAT_NAME_COLOR_NORMAL = ui.GenerateColor(218, 218, 218)
	CAT_NAME_COLOR_FOCUSED = ui.GenerateColor(255, 199, 0)

	PRICE_COLOR_BY_LEVEL = {
		shopsearch.AVG_PRICE_GOOD : ui.GenerateColor(134, 206, 140),
		shopsearch.AVG_PRICE_NORMAL : ui.GenerateColor(255, 255, 255),
		shopsearch.AVG_PRICE_BAD : ui.GenerateColor(255, 199, 0),
		shopsearch.AVG_PRICE_WORST : ui.GenerateColor(232, 80, 16),
	}

	ENTRYCOUNT_BUTTON_COUNT = 3
	PAGE_BUTTON_COUNT = 5

	STATE_NONE = 0
	STATE_LOADING = 1
	STATE_RESULT = 2

	BUY_RESULT_LOCALE = {
		shopsearch.BUY_SUCCESS : localeInfo.SHOP_SEARCH_BUY_SUCCESS,
		shopsearch.BUY_NOT_EXIST : localeInfo.SHOP_SEARCH_BUY_NOT_EXIST,
		shopsearch.BUY_PRICE_CHANGE : localeInfo.SHOP_SEARCH_BUY_PRICE_CHANGE,
		shopsearch.BUY_TIMEOUT : localeInfo.SHOP_SEARCH_BUY_TIMEOUT,
		shopsearch.BUY_NO_PEER : localeInfo.SHOP_SEARCH_BUY_NO_PEER,
		shopsearch.BUY_UNKNOWN_ERROR : localeInfo.SHOP_SEARCH_BUY_UNKNOWN,
	}

	SORT_BUTTON_BASE_PATH = ROOT_PATH.format("sort_button_%s%%s.png")

	GRAPH_X_DESC_WEEKLY_MAX_NUM = 7
	GRAPH_X_DESC_MONTHLY_MAX_NUM = 15
	GRAPH_COUNT_Y_DESC_MAX_NUM = 5
	GRAPH_PRICE_Y_DESC_MAX_NUM = 3

	GRAPH_PRICE_STEP = 10000
	GRAPH_COUNT_STEP = 5

	class ItemDropDownMenu(ui.ImageBox):

		SHOW_SPACE_Y = 5

		START_Y = 1
		START_X = 5
		SPACE_Y = 4

		ELEM_WIDTH = 118
		ELEM_HEIGHT = 14

		def __init__(self):
			ui.ImageBox.__init__(self)
			self.AddFlag("float")

			self.LoadImage(ROOT_PATH.format("drop_down_menu.png"))

			self.childs = []
			yPos = self.START_Y
			for data in self.__GetContent():
				textLine = ui.SelectableTextLine(False)
				textLine.SetParent(self)
				textLine.SetSize(self.ELEM_WIDTH, self.ELEM_HEIGHT)
				textLine.SetPosition(self.START_X, yPos)
				textLine.SetText(data[0])
				textLine.SetEvent(data[1])
				textLine.Show()

				self.childs.append(textLine)
				yPos += self.ELEM_HEIGHT + self.SPACE_Y

			self.currentItemIndex = -1
			self.parent = None
			self.eventShowAveragePrice = None
			self.eventAddFavourite = None

		def Destroy(self):
			ui.ImageBox.Destroy(self)
			self.parent = None
			self.eventShowAveragePrice = None
			self.eventAddFavourite = None

		def __GetContent(self):
			return [
				(localeInfo.SHOP_SEARCH_DROPDOWN_ADD_FAVOURITE, self.__AddFavourite),
				(localeInfo.SHOP_SEARCH_DROPDOWN_AVERAGE_PRICE, self.__ShowAveragePrice),
			]

		def SetParent(self, parent):
			ui.ImageBox.SetParent(self, parent)
			self.parent = parent

		def Open(self, parentObj, itemIndex):
			if self.currentItemIndex == itemIndex:
				self.Close()
				return

			self.currentItemIndex = itemIndex

			(parent_x, parent_y) = parentObj.GetLocalPosition(self.parent)
			self.SetPosition(parent_x + parentObj.GetWidth() - self.GetWidth(), parent_y + parentObj.GetHeight() + self.SHOW_SPACE_Y)
			self.Show()
			self.SetTop()

		def Close(self):
			self.currentItemIndex = -1
			self.Hide()

		def SetAveragePriceEvent(self, event):
			self.eventShowAveragePrice = event

		def SetFavouriteEvent(self, event):
			self.eventAddFavourite = event

		def __AddFavourite(self):
			if self.eventAddFavourite:
				self.eventAddFavourite(self.currentItemIndex)

			self.Close()

		def __ShowAveragePrice(self):
			if self.eventShowAveragePrice:
				self.eventShowAveragePrice(self.currentItemIndex)

			self.Close()

	class FavouriteBoard(ui.BoardWithTitleBar):

		X_BORDER = 20
		TOP_BORDER = 40
		BOT_BORDER = 17

		BOARD_WIDTH = 241 + X_BORDER * 2
		BOARD_HEIGHT = 426 + TOP_BORDER + BOT_BORDER -49 -22

		ITEM_X_POS = 3
		ITEM_Y_START = 74
		ITEM_Y_SPACE = 1
		ITEM_MAX_COUNT = 10

		def __init__(self, searchFunc):
			ui.BoardWithTitleBar.__init__(self)

			self.searchFunc = searchFunc

			self.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)
			self.SetCenterPosition()

			self.AddFlag("float")
			self.AddFlag("movable")
			self.SetTitleName(localeInfo.SHOP_SEARCH_FAV_TITLE)
			self.SetCloseEvent(self.Close)

			bg = ui.ImageBox()
			bg.SetParent(self)
			bg.SetPosition(self.X_BORDER-8, self.TOP_BORDER-7)
			bg.LoadImage(ROOT_PATH.format("fav/search_shop_favourite_bg.png"))
			bg.Show()
			self.bg = bg

			# desc = ui.MultiTextLine()
			# desc.SetParent(bg)
			# desc.SetPosition(5, 5)
			# desc.SetWidth(bg.GetWidth() - 5 * 2)
			# desc.SetText(localeInfo.SHOP_SEARCH_FAV_DESCRIPTION)
			# desc.Show()
			# bg.desc = desc

			self.items = []

		def Destroy(self):
			ui.BoardWithTitleBar.Destroy(self)

			self.searchFunc = None

		def __AppendFavElem(self, favName):
			elemIdx = len(self.items)

			elem = ui.ImageBox()
			elem.SetParent(self.bg)
			elem.LoadImage(ROOT_PATH.format("fav/search_shop_favourite_item.png"))
			elem.SetPosition(self.ITEM_X_POS+8, self.ITEM_Y_START + (elem.GetHeight() + self.ITEM_Y_SPACE) * elemIdx -42 -22)
			elem.Show()
			self.items.append(elem)

			textLine = ui.TextLine()
			textLine.SetParent(elem)
			textLine.SetPosition(10, 0)
			textLine.SetVerticalAlignCenter()
			textLine.SetWindowVerticalAlignCenter()
			textLine.SetText(favName)
			textLine.Show()
			elem.textLine = textLine

			deleteBtn = ui.Button()
			deleteBtn.SetParent(elem)
			deleteBtn.SetUpVisual(ROOT_PATH.format("fav/search_shop_favourite_delete_1.png"))
			deleteBtn.SetOverVisual(ROOT_PATH.format("fav/search_shop_favourite_delete_2.png"))
			deleteBtn.SetDownVisual(ROOT_PATH.format("fav/search_shop_favourite_delete_3.png"))
			deleteBtn.SetPosition(elem.GetWidth() - 10 - deleteBtn.GetWidth(), (elem.GetHeight() - deleteBtn.GetHeight()) // 2)
			deleteBtn.SetEvent(lambda idx=elemIdx: self.__DeleteFavourite(idx))
			deleteBtn.Show()
			elem.deleteBtn = deleteBtn

			searchBtn = ui.Button()
			searchBtn.SetParent(elem)
			searchBtn.SetUpVisual(ROOT_PATH.format("fav/search_shop_favourite_search_1.png"))
			searchBtn.SetOverVisual(ROOT_PATH.format("fav/search_shop_favourite_search_2.png"))
			searchBtn.SetDownVisual(ROOT_PATH.format("fav/search_shop_favourite_search_3.png"))
			searchBtn.SetPosition(deleteBtn.GetLeft() - 3 - searchBtn.GetWidth(), (elem.GetHeight() - searchBtn.GetHeight()) // 2)
			searchBtn.SetEvent(lambda name=favName: self.searchFunc(name))
			searchBtn.Show()
			elem.searchBtn = searchBtn

		def RefreshFavourites(self):
			self.items = []

			for i in range(self.ITEM_MAX_COUNT):
				favName = cfg.Get(cfg.SAVE_SHOPSEARCH, "fav_%d" % i, "")
				if not favName:
					break

				self.__AppendFavElem(favName)

		def __DeleteFavourite(self, index):
			cfg.Set(cfg.SAVE_SHOPSEARCH, "fav_%d" % index, "")
			for i in range(index + 1, self.ITEM_MAX_COUNT):
				favName = cfg.Get(cfg.SAVE_SHOPSEARCH, "fav_%d" % i, "")
				cfg.Set(cfg.SAVE_SHOPSEARCH, "fav_%d" % (i - 1), favName)
				cfg.Set(cfg.SAVE_SHOPSEARCH, "fav_%d" % i, "")

			self.RefreshFavourites()

		def Open(self, x, y):
			self.RefreshFavourites()
			self.SetPosition(x, y)
			self.Show()
			self.SetTop()

		def Close(self):
			self.Hide()

		def OnPressEscapeKey(self):
			self.Close()
			return TRUE

	class SearchDropdownList(ui.Window):

		BORDER_SCALE_SIZE = 10
		BASE_SCALE_SIZE = 10

		BASE_TOP_SPACE = 3

		MAX_DISPLAY_ITEMS = 10

		def __init__(self, selectNameEvent):
			ui.Window.__init__(self)

			self.AddFlag("float")

			leftBorder = ui.ExpandedImageBox()
			leftBorder.AddFlag("not_pick")
			leftBorder.SetParent(self)
			leftBorder.LoadImage(ROOT_PATH.format("search_dropdown_border_x.png"))
			leftBorder.Show()
			self.leftBorder = leftBorder

			rightBorder = ui.ExpandedImageBox()
			rightBorder.SetParent(self)
			rightBorder.LoadImage(ROOT_PATH.format("search_dropdown_border_x.png"))
			rightBorder.SetWindowHorizontalAlignRight()
			rightBorder.SetPosition(rightBorder.GetWidth(), 0)
			rightBorder.Show()
			self.rightBorder = rightBorder

			bottomBorder = ui.ExpandedImageBox()
			bottomBorder.AddFlag("not_pick")
			bottomBorder.SetParent(self)
			bottomBorder.LoadImage(ROOT_PATH.format("search_dropdown_border_y.png"))
			bottomBorder.SetWindowVerticalAlignBottom()
			bottomBorder.SetPosition(0, bottomBorder.GetHeight())
			bottomBorder.Show()
			self.bottomBorder = bottomBorder

			base = ui.ExpandedImageBox()
			base.AddFlag("not_pick")
			base.SetParent(self)
			base.LoadImage(ROOT_PATH.format("search_dropdown_base.png"))
			base.SetPosition(leftBorder.GetWidth(), self.BASE_TOP_SPACE)
			base.Show()
			self.base = base

			itemList = ui.ListBox()
			itemList.SetParent(self)
			itemList.SetPosition(leftBorder.GetWidth(), self.BASE_TOP_SPACE)
			itemList.SetEvent(lambda key, name: selectNameEvent(name))
			itemList.Show()
			self.itemList = itemList

		def Destroy(self):
			ui.Window.Destroy(self)

			self.itemList = None

		def SetSize(self, width, height):
			ui.Window.SetSize(self, width, height)

			xBorderHeight = height - self.bottomBorder.GetHeight()
			xBorderScale = -1.0 + xBorderHeight / float(self.BORDER_SCALE_SIZE)
			self.leftBorder.SetRenderingRect(0.0, 0.0, 0.0, xBorderScale)
			self.rightBorder.SetRenderingRect(0.0, 0.0, 0.0, xBorderScale)

			yBorderScale = -1.0 + width / float(self.BORDER_SCALE_SIZE)
			self.bottomBorder.SetRenderingRect(0.0, 0.0, yBorderScale, 0.0)
			self.bottomBorder.UpdateRect()

			xBaseScale = -1.0 + (width - self.leftBorder.GetWidth() - self.rightBorder.GetWidth()) / float(self.BASE_SCALE_SIZE)
			yBaseScale = -1.0 + (height - self.BASE_TOP_SPACE - self.bottomBorder.GetHeight()) / float(self.BASE_SCALE_SIZE)
			self.base.SetRenderingRect(0.0, 0.0, xBaseScale, yBaseScale)

			self.itemList.SetSize(width - self.leftBorder.GetWidth() - self.rightBorder.GetWidth(), height - self.BASE_TOP_SPACE - self.bottomBorder.GetHeight() - 2)

		def SetWidth(self, width):
			self.SetSize(width, max(self.GetHeight(), 10))

		def Open(self, itemNames):
			self.SetSize(self.GetWidth(), min(self.MAX_DISPLAY_ITEMS, len(itemNames)) * self.itemList.GetStepSize() + self.BASE_TOP_SPACE + self.bottomBorder.GetHeight() + 2)

			self.itemList.ClearItem()
			i = 0
			for name in itemNames:
				self.itemList.InsertItem(i, name)
				i += 1

				if i >= self.MAX_DISPLAY_ITEMS:
					break

			self.Show()
			self.SetTop()

		def Close(self):
			self.Hide()

		def SelectPrevElement(self):
			curOverLine = self.itemList.GetOverLineIdx()
			if curOverLine <= 0:
				curOverLine = self.itemList.GetItemCount() - 1
			else:
				curOverLine -= 1

			self.itemList.SetOverLineIdx(curOverLine)

		def SelectNextElement(self):
			curOverLine = self.itemList.GetOverLineIdx()
			if curOverLine >= self.itemList.GetItemCount() - 1:
				curOverLine = 0
			else:
				curOverLine += 1

			self.itemList.SetOverLineIdx(curOverLine)

		def SelectCurrentElement(self):
			curOverLine = self.itemList.GetOverLineIdx()
			if curOverLine == -1:
				return False

			self.itemList.SelectItem(curOverLine)
			return True

	def __init__(self, interface):
		ui.ScriptWindow.__init__(self)

		self.interface = interface
		self.__Initialize()

		self.__LoadDialog()
		self.SetCenterPosition()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		ui.ScriptWindow.Destroy(self)

		self.Close()

		self.shopSearchItemWindow.ClearItems()
		self.main = None

		self.dropDownMenu.Destroy()
		self.favBoard.Destroy()
		self.searchDropdown.Destroy()

	def __Initialize(self):
		## initialize general
		self.state = self.STATE_NONE
		self.entryCount = -1
		self.page = 0
		self.sortType = shopsearch.SORT_RANDOM
		self.currentGraphItem = 0
		self.currentGraphRefresh = False

		self.lastSelectedCategory = None
		self.lastInputSearch = None
		self.lastSearchFunc = None

	def __LoadDialog(self):
		PythonScriptLoader = ui.PythonScriptLoader()
		PythonScriptLoader.LoadScriptFile(self, "UIScript/shopsearchwindow.py")

		## load childs
		GetObj = self.GetChild
		self.board = GetObj("board")
		self.main = {
			"wnd" : GetObj("main"),

			"cat_window" : GetObj("CategoryWindow"),

			"fav_btn" : GetObj("fav_button"),
			"sort_btn" : GetObj("sort_button"),
			"search_bg" : GetObj("search_bg"),
			"search" : GetObj("search_line"),
			"search_btn" : GetObj("search_button"),
			
			"item_window" : GetObj("item_window"),
			"item_loading" : GetObj("loading_image"),

			"no_search_info" : GetObj("item_no_search_info"),
			"no_result_info" : GetObj("item_no_result_info"),

			"entry_count" : [GetObj("entry_count_%d" % (i + 1)) for i in range(self.ENTRYCOUNT_BUTTON_COUNT)],

			"page_wnd" : GetObj("item_page_wnd"),
			"page_first" : GetObj("item_first_page_btn"),
			"page_back" : GetObj("item_previous_page_btn"),
			"page_next" : GetObj("item_next_page_btn"),
			"page_last" : GetObj("item_last_page_btn"),
			"page_btn" : [GetObj("item_page_btn%d" % (i + 1)) for i in range(self.PAGE_BUTTON_COUNT)],

			"graph" : {
				"wnd" : GetObj("graph"),
				"close" : GetObj("graph_close"),
				"item_name" : GetObj("graph_item_name"),
				"weekly_btn" : GetObj("graph_time_weekly_button"),
				"monthly_btn" : GetObj("graph_time_monthly_button"),
				"refresh_btn" : GetObj("graph_refresh_button"),
				"last_updated" : GetObj("graph_last_updated"),
				"graph_price" : GetObj("graph_average_price"),
				"price_cursor" : GetObj("graph_average_price_cursor"),
				"price_cursor_money" : GetObj("graph_average_price_money"),
				"graph_count" : GetObj("graph_sold_items"),
				"x_desc_weekly" : {
					"wnd" : GetObj("graph_sold_weekly_x_description"),
				},
				"x_desc_monthly" : {
					"wnd" : GetObj("graph_sold_monthly_x_description"),
				},
				"y_desc_price" : [GetObj("graph_price_y_desc_%d" % (i + 1)) for i in range(self.GRAPH_PRICE_Y_DESC_MAX_NUM)],
				"y_desc_count" : [GetObj("graph_sold_y_desc_%d" % (i + 1)) for i in range(self.GRAPH_COUNT_Y_DESC_MAX_NUM)],
			},
		}

		## CATEGORY_WINDOW
		self.shopSearchCategoryWindow = ShopSearchCategoryWindow()
		self.shopSearchCategoryWindow.SetParent(self.main["cat_window"])
		self.shopSearchCategoryWindow.AddFlag("attach")
		self.shopSearchCategoryWindow.SetPosition(0, 0)
		self.shopSearchCategoryWindow.Show()

		self.shopSearchCategoryScrollBar = ShopSearchScrollBar()
		self.shopSearchCategoryScrollBar.SetParent(self.main["cat_window"])
		self.shopSearchCategoryScrollBar.SetPosition(self.shopSearchCategoryWindow.GetLocalPosition()[0] + self.shopSearchCategoryWindow.GetWidth() + 2, self.shopSearchCategoryWindow.GetLocalPosition()[1])
		self.shopSearchCategoryScrollBar.SetSize(7, categoryPeakWindowSize[1])
		self.shopSearchCategoryScrollBar.Show()

		self.shopSearchCategoryWindow.RegisterScrollBar(self.shopSearchCategoryScrollBar)

		for catData in CATEGORY_PROTO:
			ret = self.shopSearchCategoryWindow.AddCategory(self, catData, catData["name"])

			if "sub_category" in catData:
				for subData in catData["sub_category"]:
					ret.AddSubCategory(subData, subData["name"])

			ret.clickEvent = ui.__mem_func__(self.OnCategoryListSelect)

		## ITEM_WINDOW
		self.shopSearchItemWindow = ShopSearchItemWindow(self.interface, self.main["graph"]["wnd"])
		self.shopSearchItemWindow.SetParent(self.main["item_window"])
		self.shopSearchItemWindow.AddFlag("attach")
		self.shopSearchItemWindow.SetPosition(0, 0)
		self.shopSearchItemWindow.Show()

		for i in range(self.GRAPH_X_DESC_WEEKLY_MAX_NUM):
			self.main["graph"]["x_desc_weekly"][i] = GetObj("graph_sold_weekly_desc_%d" % i)
		for i in range(self.GRAPH_X_DESC_MONTHLY_MAX_NUM):
			self.main["graph"]["x_desc_monthly"][i] = GetObj("graph_sold_monthly_x_desc_%d" % i)

		## initialize childs
		self.board.SetCloseEvent(self.Close)

		self.main["fav_btn"].SetEvent(self.__OnClickFavButton)
		self.main["sort_btn"].SetEvent(self.__OnClickSortButton)
		self.main["search"].SetReturnEvent(self.__OnSearchByNameReturn)
		self.main["search"].SetEscapeEvent(self.OnPressEscapeKey)
		self.main["search"].SetUpdateEvent(self.__OnUpdateSearchSuggestions)
		self.main["search"].SetTabEvent(self.__AutoSearchCompletion)
		self.main["search"].SetOnFocusEvent(self.__OnSearchFocusEdit)
		self.main["search"].SetKillFocusEvent(self.__OnSearchUnfocusEdit)
		self.main["search"].SetUpArrowEvent(self.__OnSearchUpArrow)
		self.main["search"].SetDownArrowEvent(self.__OnSearchDownArrow)
		self.main["search_btn"].SetEvent(self.__OnSearchByName)
		self.main["search"].SetOverlayText(uiScriptLocale.SHOP_SEARCH_SEARCH_OVERLAY)

		for i in range(self.ENTRYCOUNT_BUTTON_COUNT):
			self.main["entry_count"][i].SetEvent(lambda arg=i: self.__OnSelectEntryCount(arg))
			self.main["entry_count"][i].Hide()
		self.main["page_first"].SetEvent(lambda: self.__SelectPage(0))
		self.main["page_back"].SetEvent(lambda: self.__ChangePage(-1))
		self.main["page_next"].SetEvent(lambda: self.__ChangePage(1))
		self.main["page_last"].SetEvent(lambda: self.__OnSelectLastPageBtn(1))
		for i in range(self.PAGE_BUTTON_COUNT):
			self.main["page_btn"][i].SetEvent(lambda arg=i: self.__OnSelectPageBtn(arg))

		## initialize graph childs
		self.main["graph"]["close"].SetEvent(self.OnPressEscapeKey)
		self.main["graph"]["weekly_btn"].SetEvent(self.__GraphOnSelectWeekly)
		self.main["graph"]["monthly_btn"].SetEvent(self.__GraphOnSelectMonthly)
		self.main["graph"]["refresh_btn"].SetEvent(self.__GraphOnClickRefresh)
		self.main["graph"]["graph_price"].SetOverLineEvent(self.__GraphPriceOnOver)
		self.main["graph"]["graph_price"].SetOutLineEvent(self.__GraphPriceOnOut)

		self.main["graph"]["price_cursor"].Hide()

		## initialize custom objects
		searchDropdown = self.SearchDropdownList(self.__StartSearchByNameDropdown)
		searchDropdown.SetParent(self.main["wnd"])
		searchDropdown.SetPosition(self.main["search_bg"].GetLeft(), self.main["search_bg"].GetBottom() - self.SearchDropdownList.BASE_TOP_SPACE)
		searchDropdown.SetWidth(self.main["search_bg"].GetWidth())
		searchDropdown.Close()
		self.searchDropdown = searchDropdown

		dropDownMenu = self.ItemDropDownMenu()
		dropDownMenu.SetParent(self)
		dropDownMenu.SetFavouriteEvent(self.__OnAddToFavourite)
		dropDownMenu.SetAveragePriceEvent(self.__OnRequestAveragePrice)
		dropDownMenu.Close()
		self.dropDownMenu = dropDownMenu

		favBoard = self.FavouriteBoard(self.__StartSearchByName)
		favBoard.Close()
		self.favBoard = favBoard

		itemToolTip = uiToolTip.ItemToolTip()
		itemToolTip.HideToolTip()
		self.itemToolTip = itemToolTip

		buyQuestionDlg = uiCommon.QuestionDialog()
		buyQuestionDlg.SetCancelEvent(buyQuestionDlg.Close)
		buyQuestionDlg.Close()
		self.buyQuestionDlg = buyQuestionDlg

		popupDlg = uiCommon.PopupDialog()
		popupDlg.Close()
		self.popupDlg = popupDlg

		## init window
		self.__OnSelectEntryCount(0)
		self.Refresh()

		## init graph window
		self.main["graph"]["wnd"].Hide()
		self.__EnableItemTooltip()
		self.__GraphOnSelectWeekly()

	def Open(self):
		self.Show()
		self.SetTop()

	def FocusSearchLine(self):
		if self.main and self.main.get("search"):
			self.main["search"].SetFocus()

	def CloseDialogs(self):
		self.itemToolTip.HideToolTip()
		self.buyQuestionDlg.Close()
		self.dropDownMenu.Close()
		self.favBoard.Close()
		self.searchDropdown.Close()

	def Close(self):
		self.Hide()
		self.main["search"].KillFocus()
		self.CloseDialogs()

	def OnPressEscapeKey(self):
		if self.main["graph"]["wnd"].IsShow():
			self.main["graph"]["wnd"].Hide()
			self.__EnableItemTooltip()
			return TRUE

		if self.main["search"].IsFocus() and self.main["search"].GetText():
			self.main["search"].SetText("")
			return TRUE

		self.Close()
		return TRUE

	def Refresh(self):
		self.shopSearchItemWindow.ClearItems()
		self.main["item_loading"].Hide()
		self.main["no_search_info"].Hide()
		self.main["no_result_info"].Hide()
		self.main["page_wnd"].Hide()
		self.CloseDialogs()

		self.__RefreshSortButton()

		if self.state == self.STATE_NONE:
			self.main["no_search_info"].Show()

		elif self.state == self.STATE_LOADING:
			self.main["item_loading"].Show()

		elif self.state == self.STATE_RESULT:
			if shopsearch.GetResultItemMaxNum() > 0:
				self.main["page_wnd"].Show()

			self.__RefreshItems()
			self.__RefreshPageButtons()

	
	def RefreshResult(self):
		self.state = self.STATE_RESULT
		self.Refresh()

	def ShowBuyResult(self, result):
		if result in self.BUY_RESULT_LOCALE:
			self.popupDlg.SetText(self.BUY_RESULT_LOCALE[result])
		else:
			self.popupDlg.SetText(localeInfo.SHOP_SEARCH_BUY_UNKNOWN)
		self.popupDlg.Open()

	def __DisableItemTooltip(self):
		self.itemToolTip.disabled = True
		self.itemToolTip.HideToolTip()

	def __EnableItemTooltip(self):
		self.itemToolTip.disabled = False

	def __SearchItems(self, func = None):
		if func:
			self.lastSearchFunc = func
		if self.lastSearchFunc:
			self.main["search"].KillFocus()
			
			self.lastSearchFunc(self.page, self.entryCount, self.sortType)

			self.state = self.STATE_LOADING
			self.Refresh()

			return True

		return False

	def __OnClickFavButton(self):
		if self.favBoard.IsShow():
			self.favBoard.Close()
		else:
			(x, y) = self.GetGlobalPosition()
			self.favBoard.Open(x + self.GetWidth() - 7, y)

	def __OnClickSortButton(self):
		self.sortType += 1
		if self.sortType >= shopsearch.SORT_MAX_NUM:
			self.sortType = 0

		self.__RefreshSortButton()
		self.__SearchItems()

	def __RefreshSortButton(self):
		btn = self.main["sort_btn"]

		imageTypeDict = {
			shopsearch.SORT_RANDOM : "random",
			shopsearch.SORT_ASC : "asc",
			shopsearch.SORT_DESC : "desc",
		}
		tooltipDict = {
			shopsearch.SORT_RANDOM : localeInfo.SHOP_SEARCH_SORT_TOOLTIP_RANDOM,
			shopsearch.SORT_ASC : localeInfo.SHOP_SEARCH_SORT_TOOLTIP_ASC,
			shopsearch.SORT_DESC : localeInfo.SHOP_SEARCH_SORT_TOOLTIP_DESC,
		}
		basePath = self.SORT_BUTTON_BASE_PATH % imageTypeDict[self.sortType]

		btn.SetUpVisual(basePath % "")
		btn.SetOverVisual(basePath % "_over")
		btn.SetDownVisual(basePath % "_down")
		btn.SetToolTipText(tooltipDict[self.sortType])

	def __OnSearchByNameReturn(self):
		if self.searchDropdown.IsShow():
			if self.searchDropdown.SelectCurrentElement():
				return

		self.__OnSearchByName()

	def __OnSearchByName(self):
		name = self.main["search"].GetText()
		self.__StartSearchByName(name)

	def __StartSearchByNameDropdown(self, name):
		self.__StartSearchByName(name)
		self.searchDropdown.Close()

	def __StartSearchByName(self, name):
		if not name or self.lastInputSearch == name:
			return

		self.lastSelectedCategory = None
		self.lastInputSearch = name
		self.main["search"].SetText(name)

		## softfix (cannot handle "()")
		isDS = name.lower().find("cor draconis") == -1
		if isDS and name.find("(") >= 0:
			name = name[:name.find("(")]
		## softfix : end
		self.__SearchItems(lambda page, entryCount, sortType, itemName=name: net.SendShopSearchByName(page, entryCount, sortType, itemName))

	def __OnUpdateSearchSuggestions(self):
		self.__OpenSearchDropdownList()

		name = self.main["search"].GetText()
		if not name:
			self.main["search"].SetOverlayText("")
			return

		itemNames = item.GetItemNamesByName(name)
		self.main["search"].SetOverlayText(helper.GetBestMatchingName(name, itemNames))

	def __AutoSearchCompletion(self):
		self.main["search"].SetText(self.main["search"].GetOverlayText())
		self.main["search"].SetEndPosition()

	def __OpenSearchDropdownList(self):
		name = self.main["search"].GetText()
		if name:
			itemNames = item.GetItemNamesByName(name)
			if len(itemNames) > 1:
				self.searchDropdown.Open(itemNames)
				return

		self.searchDropdown.Close()

	def __OnSearchFocusEdit(self):
		self.__OpenSearchDropdownList()

	def __OnSearchUnfocusEdit(self):
		self.searchDropdown.Close()

	def __OnSearchUpArrow(self):
		if self.searchDropdown.IsShow():
			self.searchDropdown.SelectPrevElement()

	def __OnSearchDownArrow(self):
		if self.searchDropdown.IsShow():
			self.searchDropdown.SelectNextElement()

	def OnCategoryListSelect(self, data):
		if self.lastSelectedCategory == data:
			return

		self.lastSelectedCategory = data
		self.lastInputSearch = None
		itemTypeList = []
		if "itemtype" in data:
			itemTypeList = data["itemtype"]
		vnumTuple = ()
		if "itemvnum" in data:
			vnumTuple = data["itemvnum"]

		self.__SearchItems(lambda page, entryCount, sortType, itemTypes=itemTypeList, vnums=vnumTuple: net.SendShopSearchByOptions(page, entryCount, sortType, itemTypes, vnums))

	def __RefreshItems(self):
		## remove all current items

		## add items into display list
		for i in range(shopsearch.GetResultItemMaxNum()):
			self.shopSearchItemWindow.AppendItem(i, self.dropDownMenu, self.itemToolTip, self.buyQuestionDlg, self.popupDlg)

		if shopsearch.GetResultItemMaxNum() == 0:
			self.main["no_result_info"].Show()

	def __RefreshPageButtons(self):
		maxPageNum = self.__GetMaxPage()
		if self.page >= maxPageNum:
			self.page = maxPageNum - 1

		for btn in self.main["page_btn"]:
			btn.Hide()

		minBtnIdx = max(0, self.PAGE_BUTTON_COUNT // 2 - maxPageNum // 2)
		maxBtnIdx = min(self.PAGE_BUTTON_COUNT - 1, self.PAGE_BUTTON_COUNT // 2 + (maxPageNum - 1) // 2)

		minPageIdx = self.page
		maxPageIdx = self.page
		for i in range(1, (maxBtnIdx + 1) - minBtnIdx):
			if i % 2 == 1:
				if minPageIdx > 0:
					minPageIdx -= 1
				else:
					maxPageIdx += 1
			else:
				if maxPageIdx < maxPageNum-1:
					maxPageIdx += 1
				else:
					minPageIdx -= 1

		for i in range(minBtnIdx, maxBtnIdx + 1):
			btn = self.main["page_btn"][i]
			btn.pageIdx = minPageIdx + i - minBtnIdx
			btn.SetText(str(btn.pageIdx + 1))
			if btn.pageIdx == self.page:
				btn.Down()
			else:
				btn.SetUp()
			btn.Show()

	def __OnSelectEntryCount(self, index):
		if self.entryCount == index:
			return

		for i in range(self.ENTRYCOUNT_BUTTON_COUNT):
			if i != index:
				self.main["entry_count"][i].SetUp()
			else:
				self.main["entry_count"][i].Down()

		self.entryCount = index
		self.__SearchItems()

	def __OnSelectPageBtn(self, index):
		btn = self.main["page_btn"][index]
		self.__SelectPage(btn.pageIdx)

	def __GetMaxPage(self):
		return max(1, shopsearch.GetResultPageMaxNum())

	def __OnSelectLastPageBtn(self, page):
		self.__SelectPage(self.__GetMaxPage())

	def __ChangePage(self, amount):
		self.page += amount
		if self.page < 0:
			self.page = 0
		if self.page >= self.__GetMaxPage():
			self.page = self.__GetMaxPage() - 1

		self.__SearchItems()

	def __SelectPage(self, pageIdx):
		self.page = pageIdx
		self.__SearchItems()

	def __OnAddToFavourite(self, itemIndex):
		itemVnum = shopsearch.GetResultItemVnum(itemIndex)
		item.SelectItem(itemVnum)
		itemName = item.GetItemName(False)

		emptyIdx = -1
		for i in range(self.FavouriteBoard.ITEM_MAX_COUNT):
			favName = cfg.Get(cfg.SAVE_SHOPSEARCH, "fav_%d" % i, "")
			if not favName:
				emptyIdx = i
				break

			if favName == itemName:
				self.popupDlg.SetText(localeInfo.SHOP_SEARCH_FAV_SAVE_ALREADY)
				self.popupDlg.Open()
				return

		if emptyIdx == -1:
			self.popupDlg.SetText(localeInfo.SHOP_SEARCH_FAV_SAVE_NO_EMPTY)
			self.popupDlg.Open()
			return

		cfg.Set(cfg.SAVE_SHOPSEARCH, "fav_%d" % emptyIdx, itemName)

		if self.favBoard.IsShow():
			self.favBoard.RefreshFavourites()

		self.popupDlg.SetText(localeInfo.SHOP_SEARCH_FAV_SAVE_SUCCESS)
		self.popupDlg.Open()

	def __OnRequestAveragePrice(self, itemIndex):
		itemVnum = shopsearch.GetResultItemVnum(itemIndex)
		net.SendShopSearchRequestSoldInfo(itemVnum)

		self.currentGraphItem = itemVnum
		self.currentGraphRefresh = False

	##################
	## GRAPH WINDOW
	##################

	def __GraphOnSelectWeekly(self):
		self.main["graph"]["wnd"].LoadImage(ROOT_PATH.format("graph/search_shop_graph_bg_weekly.png"))
		self.main["graph"]["wnd"].SetPosition(15, 34)

		self.main["graph"]["x_desc_weekly"]["wnd"].Show()
		self.main["graph"]["x_desc_monthly"]["wnd"].Hide()

		self.main["graph"]["weekly_btn"].Down()
		self.main["graph"]["monthly_btn"].SetUp()

		self.__GraphRefresh()

	def __GraphOnSelectMonthly(self):
		self.main["graph"]["wnd"].LoadImage(ROOT_PATH.format("graph/search_shop_graph_bg_monthly.png"))
		self.main["graph"]["wnd"].SetPosition(15, 34)

		self.main["graph"]["x_desc_weekly"]["wnd"].Hide()
		self.main["graph"]["x_desc_monthly"]["wnd"].Show()

		self.main["graph"]["weekly_btn"].SetUp()
		self.main["graph"]["monthly_btn"].Down()

		self.__GraphRefresh()

	def __GraphOnClickRefresh(self):
		net.SendShopSearchRequestSoldInfo(self.currentGraphItem)
		self.currentGraphRefresh = True

	def __GraphPriceOnOver(self, x, y, value):
		cursor = self.main["graph"]["price_cursor"]
		cursor.SetPosition(x - cursor.GetWidth() // 2, y - cursor.GetHeight() // 2)
		cursor.Show()

		moneyText = self.main["graph"]["price_cursor_money"]
		moneyText.SetText(localeInfo.SHOP_SEARCH_GRAPH_AVERAGE_PRICE_TOOLTIP % (localeInfo.LongNumberToString(int(value)), str(ui.GenerateColor(255, 0, 0))))
		moneyText.SetPosition(-4 - moneyText.GetWidth(), 0)

	def __GraphPriceOnOut(self):
		self.main["graph"]["price_cursor"].Hide()

	def __GraphGetXAxisCount(self):
		if self.main["graph"]["x_desc_weekly"]["wnd"].IsShow():
			return 7
		else:
			return shopsearch.SOLD_ITEM_INFO_COUNT

	def __GraphRefreshPrice(self):
		xAxisLimitCount = self.__GraphGetXAxisCount()

		maxPrice = shopsearch.GetSoldPriceAverage(0)

		for i in range(1, xAxisLimitCount):
			price = shopsearch.GetSoldPriceAverage(i)
			if price > maxPrice:

				maxPrice = price

		stepValue = (1 + maxPrice // (self.GRAPH_PRICE_STEP * self.GRAPH_PRICE_Y_DESC_MAX_NUM)) * self.GRAPH_PRICE_STEP
		for i in range(self.GRAPH_PRICE_Y_DESC_MAX_NUM):
			self.main["graph"]["y_desc_price"][i].SetText(localeInfo.LongNumberToString((i + 1) * stepValue))

		graph = self.main["graph"]["graph_price"]
		graph.SetYAxisLimitValue(0, stepValue * self.GRAPH_PRICE_Y_DESC_MAX_NUM)
		graph.SetXAxisLimitValue(0, xAxisLimitCount)

		graph.Clear()
		for i in range(xAxisLimitCount):
			graph.AddValue(xAxisLimitCount - (i + 1), shopsearch.GetSoldPriceAverage(i))
		graph.AddValue(xAxisLimitCount, shopsearch.GetSoldPriceAverage(0))

		graph.Refresh()

	def __GraphRefreshCount(self):
		xAxisLimitCount = self.__GraphGetXAxisCount()

		maxCount = shopsearch.GetSoldItemCount(0)
		for i in range(1, xAxisLimitCount):
			count = shopsearch.GetSoldItemCount(i)
			if count > maxCount:
				maxCount = count

		stepValue = (1 + max(0, (maxCount - 1)) // (self.GRAPH_COUNT_STEP * self.GRAPH_COUNT_Y_DESC_MAX_NUM)) * self.GRAPH_COUNT_STEP
		for i in range(self.GRAPH_COUNT_Y_DESC_MAX_NUM):
### TYWIN
			self.main["graph"]["y_desc_count"][i].SetText(uiScriptLocale.SHOP_SEARCH_GRAPH_SALES + " - " + localeInfo.LongNumberToString((i + 1) * stepValue))

		graph = self.main["graph"]["graph_count"]
		graph.SetYAxisLimitValue(0, stepValue * self.GRAPH_COUNT_Y_DESC_MAX_NUM)
		graph.SetXAxisLimitValue(0, xAxisLimitCount)

		graph.Clear()
		for i in range(xAxisLimitCount):
			graph.AddValue(xAxisLimitCount - (i + 1), shopsearch.GetSoldItemCount(i))

		graph.Refresh()

	def __GraphRefreshXAxisDesc(self):
		xAxisLimitCount = self.__GraphGetXAxisCount()

		if xAxisLimitCount == 7:
			objCount = self.GRAPH_X_DESC_WEEKLY_MAX_NUM
			objList = self.main["graph"]["x_desc_weekly"]
		else:
			objCount = self.GRAPH_X_DESC_MONTHLY_MAX_NUM
			objList = self.main["graph"]["x_desc_monthly"]

		dayChange = 0
		for i in range(objCount):
			objList[objCount - i - 1].SetText("%02d/%02d" % (1 + app.GetLocalMonth(int(dayChange)), app.GetLocalDay(int(dayChange))))
			dayChange -= float(xAxisLimitCount) / objCount

	def __GraphRefresh(self):
		if self.currentGraphItem == 0:
			return

		item.SelectItem(self.currentGraphItem)
		self.main["graph"]["item_name"].SetText(item.GetItemName())

		self.__GraphRefreshPrice()
		self.__GraphRefreshCount()
		self.__GraphRefreshXAxisDesc()

	def ShowSoldInfoResult(self, hasResults):
		if not hasResults:
			self.popupDlg.SetText(localeInfo.SHOP_SEARCH_GRAPH_NO_HISTORY)
			self.popupDlg.Open()
			return

		self.main["graph"]["last_updated"].SetText(localeInfo.SHOP_SEARCH_GRAPH_LAST_UPDATED % time.strftime("%Y.%m.%d  %H:%M"))

		self.__GraphRefresh()
		self.main["graph"]["wnd"].Show()

		self.__DisableItemTooltip()

		if self.currentGraphRefresh:
			self.popupDlg.SetText(localeInfo.SHOP_SEARCH_GRAPH_REFRESH_SUCCESS)
			self.popupDlg.Open()

class ShopSearchScrollBar(ui.Window):
	BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)
	CORNERS_AND_LINES_COLOR = grp.GenerateColor(0.3411, 0.3411, 0.3411, 1.0)
	
	BAR_NUMB = 9 #This is static value! Please dont touch in him.
	
	class MiddleBar(ui.DragButton):
		MIDDLE_BAR_COLOR = grp.GenerateColor(0.6470, 0.6470, 0.6470, 1.0)
		
		def __init__(self, horizontal_scroll):
			ui.DragButton.__init__(self)
			self.AddFlag("movable")
			
			self.horizontal_scroll = horizontal_scroll
			
			self.middle = ui.Bar()
			self.middle.SetParent(self)
			self.middle.AddFlag("attach")
			self.middle.AddFlag("not_pick")
			self.middle.SetColor(self.MIDDLE_BAR_COLOR)
			self.middle.SetSize(1, 1)
			self.middle.Show()
		
		def SetStaticScale(self, size):
			(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())
			
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, base_width, size)
				self.middle.SetSize(base_width, size)
			else:
				ui.DragButton.SetSize(self, size, base_height)
				self.middle.SetSize(size, base_height)
		
		def SetSize(self, selfSize, fullSize):
			(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())
			
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
				self.middle.SetSize(base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
			else:
				ui.DragButton.SetSize(self, truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
				self.middle.SetSize(truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
		
		def SetStaticSize(self, size):
			size = max(2, size)
			
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, size, self.middle.GetHeight())
				self.middle.SetSize(size, self.middle.GetHeight())
			else:
				ui.DragButton.SetSize(self, self.middle.GetWidth(), size)
				self.middle.SetSize(self.middle.GetWidth(), size)
	
	def __init__(self, horizontal_scroll = False):
		ui.Window.__init__(self)
		
		self.horizontal_scroll = horizontal_scroll
		
		self.scrollEvent = None
		self.scrollSpeed = 1
		self.sizeScale = 1.0
		
		self.bars = []
		for i in range(self.BAR_NUMB):
			br = ui.Bar()
			br.SetParent(self)
			br.AddFlag("attach")
			br.AddFlag("not_pick")
			br.SetColor([self.CORNERS_AND_LINES_COLOR, self.BASE_COLOR][i == (self.BAR_NUMB-1)])
			if not (i % 2 == 0): br.SetSize(1, 1)
			br.Show()
			
			self.bars.append(br)
		
		self.middleBar = self.MiddleBar(self.horizontal_scroll)
		self.middleBar.SetParent(self)
		self.middleBar.SetMoveEvent(ui.__mem_func__(self.OnScrollMove))
		self.middleBar.Show()

		# if app.ENABLE_MOUSE_WHEEL_EVENT:
		# self.SetScrollWheelEvent(self.OnMouseWheel)

	def OnScrollMove(self):
		if not self.scrollEvent:
			return
		
		arg = float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else\
				float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())
		
		self.scrollEvent(arg)
	
	def SetScrollEvent(self, func):
		self.scrollEvent = ui.__mem_func__(func)
	
	def SetScrollSpeed(self, speed):
		self.scrollSpeed = speed
	
	def OnMouseWheel(self, length):
		if self.IsInPosition():
			if not self.horizontal_scroll:
				val = min(max(1, self.middleBar.GetLocalPosition()[1] - (length * 0.01) * self.scrollSpeed * self.sizeScale), self.GetHeight() - self.middleBar.GetHeight() - 1)
				self.middleBar.SetPosition(1, val)
			else:
				val = min(max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) *  self.scrollSpeed * self.sizeScale), self.GetWidth() - self.middleBar.GetWidth() - 1)
				self.middleBar.SetPosition(val, 1)
			
			self.OnScrollMove()
			return True
		
		return False

	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
		
		if not self.horizontal_scroll:
			if xMouseLocalPosition == 0 or xMouseLocalPosition == self.GetWidth():
				return
			
			y_pos = (yMouseLocalPosition - self.middleBar.GetHeight() // 2)
			self.middleBar.SetPosition(1, y_pos)
		else:
			if yMouseLocalPosition == 0 or yMouseLocalPosition == self.GetHeight():
				return
			
			x_pos = (xMouseLocalPosition - self.middleBar.GetWidth() // 2)
			self.middleBar.SetPosition(x_pos, 1)
		
		self.OnScrollMove()
	
	def SetSize(self, w, h):
		(width, height) = (max(3, w), max(3, h))
		
		ui.Window.SetSize(self, width, height)
		
		self.bars[0].SetSize(1, (height - 2))
		self.bars[0].SetPosition(0, 1)
		self.bars[2].SetSize((width - 2), 1)
		self.bars[2].SetPosition(1, 0)
		self.bars[4].SetSize(1, (height - 2))
		self.bars[4].SetPosition((width - 1), 1)
		self.bars[6].SetSize((width - 2), 1)
		self.bars[6].SetPosition(1, (height - 1))
		self.bars[8].SetSize((width - 2), (height - 2))
		self.bars[8].SetPosition(1, 1)
		
		self.bars[1].SetPosition(0, 0)
		self.bars[3].SetPosition((width - 1), 0)
		self.bars[5].SetPosition((width - 1), (height - 1))
		self.bars[7].SetPosition(0, (height - 1))
		
		if not self.horizontal_scroll:
			self.middleBar.SetStaticSize(width - 2)
			self.middleBar.SetSize(12, self.GetHeight())
		else:
			self.middleBar.SetStaticSize(height - 2)
			self.middleBar.SetSize(12, self.GetWidth())
		
		self.middleBar.SetRestrictMovementArea(1, 1, width - 2, height - 2)
	
	def SetScale(self, selfSize, fullSize):
		self.sizeScale = float(selfSize // fullSize)
		self.middleBar.SetSize(selfSize, fullSize)
	
	def SetStaticScale(self, r_size):
		self.middleBar.SetStaticScale(r_size)
	
	def SetPosScale(self, fScale):
		pos = (math.ceil((self.GetHeight() - 2 - self.middleBar.GetHeight()) * fScale) + 1) if not self.horizontal_scroll else\
				(math.ceil((self.GetWidth() - 2 - self.middleBar.GetWidth()) * fScale) + 1)
		
		self.SetPos(pos)
	
	def SetPos(self, pos):
		wPos = (1, pos) if not self.horizontal_scroll else (pos, 1)
		self.middleBar.SetPosition(*wPos)

class ShopSearchSubCategoryItem(ui.Window):
	def __init__(self, subData, text):
		ui.Window.__init__(self)
		self.SetWindowName("SubCategObject_ListBoxEx_Item")
		
		self.subData = subData
		self.mArgs = ()
		self.parent = None
		
		new_text = ""

		new_text = text
		self.textWindow = ui.Window()
		self.textWindow.SetParent(self)
		self.textWindow.AddFlag("attach")
		self.textWindow.AddFlag("not_pick")
		self.textWindow.SetPosition(2, 3)
		self.textWindow.Show()
		
		self.textLine = ui.TextLine()
		self.textLine.AddFlag("attach")
		self.textLine.AddFlag("not_pick")
		self.textLine.SetParent(self.textWindow)
		self.textLine.SetText(new_text)
		self.textLine.Show()
		
		self.cutTextLine = ui.TextLine()
		self.cutTextLine.SetParent(self.textWindow)
		self.cutTextLine.SetText(new_text)
		self.cutTextLine.Hide()
		
		self.originText = new_text
		self.cutedText = new_text
	
	def SetSize(self, w, h):
		ui.Window.SetSize(self, w, h)
		self.textWindow.SetSize(w - 2, h - 3)
		
		self.cutedText = self.GetCutText()
	
	def SetParent(self, parent):
		self.parent = proxy(parent)
		
		ui.Window.SetParent(self, parent)
	
	def OnMouseLeftButtonDown(self):
		if self.parent:
			self.parent.SelectItem(self)
	
	def GetCutText(self):
		(wL, wT, wR, wB) = self.cutTextLine.GetRenderBox()
		if wR > 0:
			i = (len(self.originText) - 1)
			
			while wR > 0:
				self.cutTextLine.SetText(self.originText[:i])
				(wL, wT, wR, wB) = self.cutTextLine.GetRenderBox()
				i -= 1
			
			self.cutTextLine.SetText(self.originText[:i].strip() + "..")
			
			(wL, wT, wR, wB) = self.cutTextLine.GetRenderBox()
			if wR > 0:
				i -= 1
			
			cut_text = (self.originText[:i] + "..")
			self.cutTextLine.SetText(self.originText)
			self.textLine.SetText(cut_text)
			
			return cut_text
		
		self.cutTextLine.SetText(self.originText)
		self.textLine.SetText(self.originText)
		
		return self.originText
	
	def OnUpdate(self):
		(wL, wT, wR, wB) = self.cutTextLine.GetRenderBox()
		currX = self.textLine.GetLocalPosition()[0]
		
		if self.IsInPosition():
			if wR > 0:
				if self.originText != self.textLine.GetText():
					self.textLine.SetText(self.originText)
				
				(wL, wT, wR, wB) = self.textLine.GetRenderBox()
				if wR > 0:
					self.textLine.SetPosition(currX - 1, 0)
		elif currX < 0:
			self.textLine.SetPosition(currX + 1, 0)
		elif self.textLine.GetText() != self.cutedText:
			self.textLine.SetText(self.cutedText)
	
	def OnRender(self):
		if self.parent.GetSelectedItem()==self:
			grp.SetColor(ui.SELECT_COLOR)
			self.OnSelectedRender()
		elif self.IsIn():
			grp.SetColor(ui.HALF_WHITE_COLOR)
			self.OnSelectedRender()
		else:
			grp.SetColor(ui.BACKGROUND_COLOR)
			self.OnSelectedRender()

	def OnSelectedRender(self):
		(rLeft, rTop, rRight, rBottom) = self.GetRenderBox()
		x, y = self.GetGlobalPosition()
		
		grp.RenderBar(x + rLeft, y + rTop, self.GetWidth() - rLeft - rRight, self.GetHeight() - rBottom - rTop)

class ShopSearchCategoryItem(ui.Window):
	"""Static values!
		Please dont touch on them."""
	TICK_COUNT = 6
	MIN_HEIGHT = 20
	ARROW_IMG = ["d:/ymir work/ui/wiki/arrow.tga", "d:/ymir work/ui/wiki/arrow_up.tga"]
	
	LINES_COLOR = grp.GenerateColor(0.3215, 0.3019, 0.2235, 1.0)
	CORNER_COLOR = grp.GenerateColor(0.3215, 0.3019, 0.2235, 1.0)
	BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.4)
	
	def __init__(self, mainParent = None, owner = None):
		ui.Window.__init__(self)
		
		self.data = None

		self.mainParent = (None if not mainParent else proxy(mainParent))
		self.owner = (None if not owner else proxy(owner))

		self.expectedSize = 0
		self.currHeight = self.MIN_HEIGHT
		
		self.isAnimating = False
		self.isOpening = False
		
		self.clickEvent = None

		# self.titleImg = ui.BoxedBoard()
		# self.titleImg.SetSize(150, 29)
		# self.titleImg.SetParent(self)
		# self.titleImg.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.ClickExpand))
		# self.titleImg.Show()

		self.titleImg = ui.Button()
		self.titleImg.SetParent(self)
		self.titleImg.SetUpVisual(ROOT_PATH.format("search_shop_category_btn_1.png"))
		self.titleImg.SetOverVisual(ROOT_PATH.format("search_shop_category_btn_2.png"))
		self.titleImg.SetDownVisual(ROOT_PATH.format("search_shop_category_btn_3.png"))
		self.titleImg.SetEvent(ui.__mem_func__(self.ClickExpand))
		self.titleImg.Show()

		self.icon = ui.ExpandedImageBox()
		self.icon.SetParent(self.titleImg)
		self.icon.AddFlag("attach")
		self.icon.AddFlag("not_pick")
		self.icon.Show()

		self.titleText = ui.TextLine()
		self.titleText.SetParent(self.titleImg)
		self.titleText.AddFlag("attach")
		self.titleText.AddFlag("not_pick")
		self.titleText.SetPosition(35, self.titleImg.GetHeight() // 2)
		self.titleText.Show()

		self.arrow = ui.ExpandedImageBox()
		self.arrow.SetParent(self.titleImg)
		self.arrow.AddFlag("attach")
		self.arrow.AddFlag("not_pick")
		self.arrow.LoadImage(self.ARROW_IMG[0])
		self.arrow.SetPosition(self.titleImg.GetWidth() - self.arrow.GetWidth() - 5, self.titleImg.GetHeight() // 2 - self.arrow.GetHeight() // 2)
		self.arrow.Show()
		
		self.expandWnd = ui.Window()
		self.expandWnd.SetParent(self)
		self.expandWnd.AddFlag("attach")
		self.expandWnd.AddFlag("not_pick")
		self.expandWnd.SetPosition(0, self.titleImg.GetHeight())
		self.expandWnd.SetSize(self.titleImg.GetWidth(), 0)
		self.expandWnd.Show()
		
		self.bars = []
		for i in range(self.TICK_COUNT):
			br = ui.Bar()
			br.SetParent(self.expandWnd)
			br.AddFlag("attach")
			br.AddFlag("not_pick")
			br.SetColor([self.LINES_COLOR, self.CORNER_COLOR, self.BASE_COLOR][2 if i == (self.TICK_COUNT - 1) else int(i % 2 == 0)])
			br.Show()
			
			self.bars.append(br)
		
		self.categList = ui.ListBoxEx()
		self.categList.SetParent(self.expandWnd)
		self.categList.SetItemSize(self.titleImg.GetWidth() - 6, 17)
		self.categList.SetItemStep(17)
		self.categList.SetSize(self.titleImg.GetWidth() - 6, self.MIN_HEIGHT - 1)
		self.categList.SetPosition(3, 1)
		self.categList.SetSelectEvent(ui.__mem_func__(self.OnSelectSubCategory))
		self.categList.Show()
		
		ui.Window.SetSize(self, self.titleImg.GetWidth(), self.titleImg.GetHeight())
		self.ArrangeBars(self.MIN_HEIGHT)

	def OnSelectSubCategory(self, elem):
		if self.owner:
			self.owner.NotifyCategorySelect(self)

		if self.clickEvent:
			self.clickEvent(elem.subData)

	def UnselectSubCategory(self):
		self.categList.SelectIndex(-1)

	def AddSubCategory(self, subData, text):
		self.currHeight = (17 * (self.categList.GetItemCount() + 1) + 3)
		
		if self.expandWnd.GetHeight() > 0:
			self.ArrangeBars(self.currHeight)
			self.isAnimating = True
		
		self.categList.SetViewItemCount(self.categList.GetItemCount() + 1)
		
		item = ShopSearchSubCategoryItem(subData, text)
		self.categList.AppendItem(item)
		
		self.categList.SetSize(self.categList.GetWidth(), self.currHeight - 1)

	def ClickExpand(self):
		if not "sub_category" in self.data:
			self.mainParent.OnCategoryListSelect(self.data)

			# self.isOpening = not self.isOpening
			return
		else:
			self.mainParent.OnCategoryListSelect(self.data)

		self.arrow.LoadImage(self.ARROW_IMG[(0 if self.isOpening else 1)])
		
		self.icon.LoadImage(ROOT_PATH.format("icons/{}_{}.png".format(self.data["icon"], "default" if self.isOpening else "active")))

		self.isOpening = not self.isOpening
		self.isAnimating = True
		
		self.expandWnd.Show()
		
		self.ArrangeBars(self.currHeight if self.isOpening else 0)
		
		if self.owner:
			self.owner.UnselectAllSubCategorys()

	def OnUpdate(self):
		if not self.isAnimating:
			return
		
		h = self.expandWnd.GetHeight()
		
		if h == self.expectedSize:
			self.isAnimating = False
			
			if h == 0:
				self.expandWnd.Hide()
			
			return
		
		step = (self.currHeight // self.TICK_COUNT)
		newSize = 0
		isOpening = (False if h > self.expectedSize else True)
		
		if isOpening:
			newSize = min(self.currHeight, self.expandWnd.GetHeight() + step)
		else:
			newSize = max(0, self.expandWnd.GetHeight() - step)
		
		change = newSize - self.expandWnd.GetHeight()
		
		self.expandWnd.SetSize(self.titleImg.GetWidth(), newSize)
		ui.Window.SetSize(self, self.titleImg.GetWidth(), self.titleImg.GetHeight() + newSize)
		self.owner.NotifySizeChange(self, change, (newSize > h))
	
	def SetSize(self, width, height):
		dbg.LogBox("WikiCategory -> SetSize - unsupported function")
	
	def ArrangeBars(self, currHeight):
		self.expectedSize = currHeight
		if currHeight < self.MIN_HEIGHT:
			return
		
		currWidth = self.expandWnd.GetWidth()
		
		self.bars[0].SetSize(1, (currHeight - 1))
		self.bars[1].SetSize(1, 1)
		self.bars[1].SetPosition(0, (currHeight - 1))
		self.bars[2].SetSize((currWidth - 2), 1)
		self.bars[2].SetPosition(1, (currHeight - 1))
		self.bars[3].SetSize(1, 1)
		self.bars[3].SetPosition((currWidth - 1), (currHeight - 1))
		self.bars[4].SetSize(1, (currHeight - 1))
		self.bars[4].SetPosition((currWidth - 1), 0)
		self.bars[5].SetSize((currWidth - 2), (currHeight - 1))
		self.bars[5].SetPosition(1, 0)

	def SetData(self, data):
		self.data = data

		self.icon.LoadImage(ROOT_PATH.format("icons/{}_default.png".format(self.data["icon"])))
		self.icon.SetPosition(6, (self.titleImg.GetHeight() // 2 - self.icon.GetHeight() // 2 -1))

	def SetTitleName(self, text):
		self.titleText.SetText(text)
		
		pos_y = (self.titleImg.GetHeight() // 2 - self.titleText.GetTextSize()[1] // 2 - 1)
		self.titleText.SetPosition(35, pos_y)

class ShopSearchCategoryWindow(ui.Window):
	"""Static values!
		Please dont touch on them."""
	CATEGORY_PADDING = 3
	SCROLL_SPEED = 17
	
	def __init__(self):
		ui.Window.__init__(self)
		
		self.SetSize(*categoryPeakWindowSize)
		self.SetInsideRender(True)
		
		self.scrollBar = None
		self.hideWindowsEvent = None
		self.elements = []
		
		self.scrollBoard = ui.Window()
		self.scrollBoard.SetParent(self)
		self.scrollBoard.AddFlag("attach")
		self.scrollBoard.AddFlag("not_pick")
		self.scrollBoard.Show()

	def AddCategory(self, mainParent, data, text):
		tmp = ShopSearchCategoryItem(mainParent, self)
		tmp.SetParent(self.scrollBoard)
		tmp.SetData(data)
		tmp.SetTitleName(text)
		tmp.Show()
		
		addPadding = 0
		if len(self.elements) > 0:
			pos_y = (self.elements[-1].GetLocalPosition()[1] + self.elements[-1].GetHeight() + self.CATEGORY_PADDING)
			tmp.SetPosition(0, pos_y)
			
			addPadding = self.CATEGORY_PADDING
		
		(width, height) = (tmp.GetWidth(), self.scrollBoard.GetHeight() + addPadding + tmp.GetHeight())
		self.scrollBoard.SetSize(width, height)
		
		self.elements.append(tmp)
		return tmp
	
	def NotifySizeChange(self, obj, amount, expanded):
		ind = len(self.elements)
		if obj in self.elements:
			ind = (self.elements.index(obj) + 1)
		
		if ind < len(self.elements):
			for i in range(ind, len(self.elements)):
				pos_y = (self.elements[(i - 1)].GetLocalPosition()[1] + self.elements[(i - 1)].GetHeight() + self.CATEGORY_PADDING)
				self.elements[i].SetPosition(0, pos_y)
		
		(width, height) = (self.scrollBoard.GetWidth(), (self.scrollBoard.GetHeight() + amount))
		self.scrollBoard.SetSize(width, height)
		self.UpdateScrollbar()
	
	def NotifyCategorySelect(self, obj):
		if self.hideWindowsEvent:
			self.hideWindowsEvent()
		
		for i in self.elements:
			if obj != proxy(i) and obj != i:
				i.UnselectSubCategory()
	
	def UnselectAllSubCategorys(self):
		for i in self.elements:
			i.UnselectSubCategory()

	def OnMouseWheel(self, length):
		if self.IsInPosition():
			self.UpdateScrollbar(int((length * 0.01) * self.SCROLL_SPEED))
			return True
		
		return False
	
	def OnScrollBar(self, fScale):
		curr = min(0, max(math.ceil((self.scrollBoard.GetHeight() - categoryPeakWindowSize[1]) * fScale * -1.0), -self.scrollBoard.GetHeight() + categoryPeakWindowSize[1]))
		self.scrollBoard.SetPosition(0, curr)
	
	def ChangeScrollbar(self):
		if not self.scrollBar:
			return
		
		scrollBoardHeight = self.scrollBoard.GetHeight()
		selfHeight = self.GetHeight()
		
		if scrollBoardHeight <= selfHeight:
			self.scrollBar.Hide()
		else:
			self.scrollBar.SetScale(selfHeight, scrollBoardHeight)
			
			new_pos = self.GetNewScrollBarPosition()
			if new_pos != 0:
				self.scrollBar.SetPos(new_pos)
			else:
				pos_scale = truediv(abs(self.scrollBoard.GetLocalPosition()[1]), (scrollBoardHeight - selfHeight))
				self.scrollBar.SetPosScale(pos_scale)
			
			self.scrollBar.Show()

	def GetNewScrollBarPosition(self):
		if self.scrollBoard.GetLocalPosition()[1] >= 0:
			return 0

		out_perc = truediv(self.scrollBoard.GetLocalPosition()[1], self.scrollBoard.GetHeight())
		scroll_max_size = abs(self.GetHeight() * out_perc)
		
		return scroll_max_size
	
	def UpdateScrollbar(self, val = 0):
		curr = min(0, max(self.scrollBoard.GetLocalPosition()[1] + val, -self.scrollBoard.GetHeight() + categoryPeakWindowSize[1]))
		self.scrollBoard.SetPosition(0, curr)
		
		self.ChangeScrollbar()
	
	def RegisterScrollBar(self, scroll):
		# if app.ENABLE_MOUSE_WHEEL_EVENT:
		# self.SetScrollWheelEvent(self.OnMouseWheel)
		self.scrollBar = proxy(scroll)
		self.scrollBar.SetScrollEvent(self.OnScrollBar)
		self.scrollBar.SetScrollSpeed(self.SCROLL_SPEED)
		
		self.ChangeScrollbar()

class ShopSearchItemWindow(ui.Window):
	class ItemObject(ui.Window):
	
		def OverInItem2(self, index):
			self.OverIn()
			if self.itemToolTip.disabled:
				return
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				if interface.tooltipItem:
					interface.tooltipItem.SetShopSearchItem(index, self.itemPriceColor)
					interface.tooltipItem.ShowToolTip()

		def OverOutItem2(self):
			self.OverOut()
			if self.itemToolTip.disabled:
				return
			interface = osfInfo.GetInterfaceInstance()
			if interface:
				if interface.tooltipItem:
					interface.tooltipItem.HideToolTip()
	
		def __init__(self, parent, index, dropDownMenu, itemToolTip, buyQuestionDlg, buyErrorDlg, interface, graph):
			ui.Window.__init__(self)

			self.parent = proxy(parent)
			self.interface = interface
			
			self.graphObj = graph

			self.itemIndex = index
			self.itemPriceColor = ShopSearchWindow.PRICE_COLOR_BY_LEVEL[shopsearch.GetResultItemAvgPriceLevel(index)]
			self.endTime = shopsearch.GetResultItemEndTime(index)
			self.lastLeftSec = -1
			self.dropDownMenu = dropDownMenu
			self.itemToolTip = itemToolTip

			self.buyQuestionDlg = buyQuestionDlg
			self.buyErrorDlg = buyErrorDlg

			itemVnum = shopsearch.GetResultItemVnum(index)
			item.SelectItem(itemVnum)
			_, itemSize = item.GetItemSize()

			bgImage = ui.BoxedBoard()
			bgImage.SetParent(self)
			bgImage.SetSize(545, (itemSize * (32 + 2)) + 10)
			bgImage.SetInsideRender(True)
			bgImage.SAFE_SetOverInEvent(self.OverIn)
			bgImage.SAFE_SetOverOutEvent(self.OverOut)
			bgImage.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.AskBuyItem), buyQuestionDlg, buyErrorDlg)
			bgImage.Show()
			self.bgImage = bgImage
			self.SetSize(bgImage.GetWidth(), bgImage.GetHeight())

			# self.SetSize(565, 84)

			itemSlot = ui.ExpandedImageBox()
			itemSlot.AddFlag("not_pick")
			itemSlot.SetParent(bgImage)
			itemSlot.SetPosition(12, (bgImage.GetHeight() - itemSize * 32)//2)
			itemSlot.LoadImage(ROOT_PATH_ITEM_SLOT.format(itemSize))
			itemSlot.Show()
			self.itemSlot = itemSlot

			## icon
			itemIcon = ui.ExpandedImageBox()
			itemIcon.SetParent(itemSlot)
			# itemIcon.AddFlag("not_pick")
			itemIcon.SetPosition(0, 0)
			itemIcon.LoadImage(item.GetIconImageFileName())
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem2)
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem2, index)
			itemIcon.SAFE_SetStringEvent("MOUSE_LEFT_UP", self.AskBuyItem, buyQuestionDlg, buyErrorDlg)
			itemIcon.Show()
			self.itemIcon = itemIcon

			## name
			itemName = ui.ExtendedTextLine()
			itemName.SetParent(bgImage)
			itemName.AddFlag("not_pick")
			itemName.SetText("%dx <TEXT color=%d text=\"%s\">" % (shopsearch.GetResultItemCount(index), self.__GetItemNameColor(), self.__GetItemNameString()))
			itemName.Show()

			pos_y = (bgImage.GetHeight() // 2 - itemName.GetTextHeight() // 2 - 1)
			itemName.SetPosition(12+46, pos_y)

			self.itemName = itemName

			## time
			timeText = ui.TextLine()
			timeText.SetParent(bgImage)
			timeText.AddFlag("not_pick")
			timeText.Show()

			self.timeText = timeText

			if self.endTime == 0:
				timeText.SetText(uiScriptLocale.SHOP_SEARCH_SELLER_ONLINE)
				# timeText.SetText("<TEXT text=\"%s\">" % "Online")
				pos_y = (bgImage.GetHeight() // 2 - timeText.GetTextHeight() // 2 - 1)
				timeText.SetPosition(280-38+102+3, pos_y)
			else:
				self.__RefreshTimeText()

			## submenu button
			submenuBtn = ui.Button()
			submenuBtn.SetParent(bgImage)
			submenuBtn.SetToolTipText(localeInfo.SHOP_SEARCH_ITEM_SUBMENU_TOOLTIP)
			submenuBtn.SetUpVisual(ROOT_PATH.format("search_shop_btn_details_1.png"))
			submenuBtn.SetOverVisual(ROOT_PATH.format("search_shop_btn_details_2.png"))
			submenuBtn.SetDownVisual(ROOT_PATH.format("search_shop_btn_details_3.png"))
			# submenuBtn.SetWindowVerticalAlignCenter()
			submenuBtn.SetPosition(280-38+21-13+229, (bgImage.GetHeight() // 2 - submenuBtn.GetHeight() // 2 - 1))
			submenuBtn.SetEvent(self.__OnSubmenuBtnClick)
			submenuBtn.Show()
			self.submenuBtn = submenuBtn
			
			280-38+21-13+229

			## message button
			messageBtn = ui.Button()
			messageBtn.SetParent(bgImage)
			messageBtn.SetToolTipText(localeInfo.SHOP_SEARCH_ITEM_MESSAGE_OWNER_TOOLTIP)
			messageBtn.SetUpVisual(ROOT_PATH.format("search_shop_btn_msg_1.png"))
			messageBtn.SetOverVisual(ROOT_PATH.format("search_shop_btn_msg_2.png"))
			messageBtn.SetDownVisual(ROOT_PATH.format("search_shop_btn_msg_3.png"))
			# messageBtn.SetWindowVerticalAlignCenter()
			messageBtn.SetPosition(280-38+21-13+229+26, (bgImage.GetHeight() // 2 - messageBtn.GetHeight() // 2 - 1))
			messageBtn.SetEvent(self.__SendMessage)
			messageBtn.Show()
			self.messageBtn = messageBtn

			## gold icon
			goldIcon = ui.ExpandedImageBox()
			goldIcon.SetParent(bgImage)
			goldIcon.AddFlag("not_pick")
			goldIcon.LoadImage(ROOT_PATH.format("yang.png"))
			goldIcon.SetPosition(280-38-13, (bgImage.GetHeight() // 2 - goldIcon.GetHeight() // 2 - 1))
			goldIcon.Show()
			self.goldIcon = goldIcon

			## gold text
			goldText = ui.TextLine()
			goldText.SetParent(bgImage)
			goldText.AddFlag("attach")
			goldText.AddFlag("not_pick")
			# goldText.SetWindowHorizontalAlignRight()
			# goldText.SetHorizontalAlignRight()
			goldText.SetText(localeInfo.LongNumberToString(shopsearch.GetResultItemPrice(index)))
			goldText.SetPackedFontColor(self.itemPriceColor)
			goldText.Show()

# TWN
			pos_y = (bgImage.GetHeight() // 2 - goldText.GetTextHeight() // 2 - 1)
			goldText.SetPosition(280-38+21-13, pos_y)
			self.goldText = goldText

		def __del__(self):
			ui.Window.__del__(self)

		def Destroy(self):
			ui.Window.Destroy(self)
			self.timeText = None
			self.dropDownMenu = None
			self.itemIcon = None
			self.itemToolTip = None
			self.submenuBtn = None

			self.Hide()
		
		def OverIn(self):
			self.bgImage.SetBaseColor(grp.GenerateColor(0.71, 0.71, 0.74, 0.4))

		def OverOut(self):
			self.bgImage.SetBaseColor(self.bgImage.DEFAULT_BASE_COLOR)

		def __OnSubmenuBtnClick(self):
			self.dropDownMenu.Open(self.submenuBtn, self.itemIndex)

		def __GetItemNameData(self):
			itemVnum = shopsearch.GetResultItemVnum(self.itemIndex)
			itemName = item.GetItemName()
			if len(itemName) > 28:
				itemName = itemName[:28] + "..."

			(title, specialColor) = osfInfo.GetItemSpecialColor(itemVnum)
			if title != None and specialColor != None:
				return (title, specialColor)

			titleColor = osfInfo.GetItemTitleColor(itemVnum)
			if titleColor != None:
				return (itemName, titleColor)

			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
				attrType, attrValue = shopsearch.GetResultItemAttribute(self.itemIndex, i)
				if attrType != 0:
					return (itemName, uiToolTip.ToolTip.SPECIAL_TITLE_COLOR)

			return (itemName, uiToolTip.ToolTip.TITLE_COLOR)

		def __GetItemNameString(self):
			return self.__GetItemNameData()[0]

		def __GetItemNameColor(self):
			return self.__GetItemNameData()[1]

		def __RefreshTimeText(self):
			if self.graphObj and self.graphObj.IsShow():
				return
				
			leftSec = max(0, self.endTime - app.GetGlobalTimeStamp())
			if leftSec != self.lastLeftSec:
				self.lastLeftSec = leftSec
				self.timeText.SetText(localeInfo.SecondToDHMS(leftSec))


				pos_y = (self.bgImage.GetHeight() // 2 - self.timeText.GetTextHeight() // 2 - 1)
				self.timeText.SetPosition(280-38+102+3, pos_y)

		def OnUpdate(self):
			# if self.IsInPosition() and not self.itemToolTip.disabled:
				# if self.itemIcon.IsInPosition():
					# if osfInfo.SHOP_SEARCH_ITEM == -1:
						# self.itemToolTip.BindInterfaceClass(self.interface)
						# self.itemToolTip.SetShopSearchItem(self.itemIndex, self.itemPriceColor)
						# osfInfo.SHOP_SEARCH_ITEM = self.itemIndex
				# else:
					# self.itemToolTip.HideToolTip()
					# osfInfo.SHOP_SEARCH_ITEM = -1

			if self.endTime > 0:
				self.__RefreshTimeText()

		def AskBuyItem(self, dlg, errDlg):
			itemID = shopsearch.GetResultItemID(self.itemIndex)
			itemVnum = shopsearch.GetResultItemVnum(self.itemIndex)
			itemPrice = shopsearch.GetResultItemPrice(self.itemIndex)
			ownerItemID = shopsearch.GetResultItemOwnerID(self.itemIndex)
			vid = player.GetMainCharacterIndex()

			if chrmgr.GetPlayerID(vid) == ownerItemID:
				errDlg.SetText(localeInfo.SHOP_SEARCH_CANNOT_BUY_OWN_ITEM)
				errDlg.Open()
				return

			if player.GetElk() < itemPrice:
				errDlg.SetText(localeInfo.SHOP_SEARCH_CANNOT_BUY_NO_MONEY)
				errDlg.Open()
				return

			item.SelectItem(itemVnum)
			dlg.SetText(localeInfo.SHOP_SEARCH_ITEM_BUY_QUESTION % (item.GetItemName(), localeInfo.NumberToMoneyString(itemPrice)))
			dlg.SetAcceptEvent(lambda argDlg=dlg, argItemID=itemID, argItemVnum=itemVnum, argItemPrice=itemPrice: self.__BuyItem(argDlg, argItemID, argItemVnum, argItemPrice))
			dlg.Open()

			self.dropDownMenu.Close()

		def __BuyItem(self, dlg, itemID, itemVnum, itemPrice):
			net.SendShopSearchBuy(itemID, itemVnum, itemPrice)
			dlg.Close()

			self.dropDownMenu.Close()

		def __SendMessage(self):
			net.SendShopSearchOwnerMessage(shopsearch.GetResultItemOwnerID(self.itemIndex))

	"""Static values!
		Please dont touch on them."""
	ELEM_PADDING = -1
	SCROLL_SPEED = 30

	def __init__(self, interface, graph):
		ui.Window.__init__(self)

		self.SetSize(*itemPeakWindowSize)

		self.elements = []

		self.interface = interface

		self.peekWindow = ui.Window()
		self.peekWindow.SetParent(self)
		self.peekWindow.AddFlag("attach")
		self.peekWindow.AddFlag("not_pick")
		self.peekWindow.SetSize(itemPeakWindowSize[0] - 5, self.GetHeight())
		self.peekWindow.SetPosition(0, 0)
		self.peekWindow.SetInsideRender(True)
		self.peekWindow.Show()
		
		self.scrollBoard = ui.Window()
		self.scrollBoard.SetParent(self.peekWindow)
		self.scrollBoard.AddFlag("attach")
		self.scrollBoard.AddFlag("not_pick")
		self.scrollBoard.Show()
		
		self.graphWnd = graph

		self.RegisterScrollBar()

	def Show(self):
		wndMgr.Show(self.hWnd)

		self.scrollBoard.SetSize(0, 0)
		self.UpdateScrollbar()

	def AppendItem(self, i, dropDownMenu, itemToolTip, buyQuestionDlg, popupDlg):
		tmp = self.ItemObject(self, i, dropDownMenu, itemToolTip, buyQuestionDlg, popupDlg, self.interface, self.graphWnd)
		tmp.SetParent(self.scrollBoard)
		tmp.AddFlag("attach")

		addPadding = 0
		totalElem = len(self.elements)

		if totalElem > 0:
			lastIndex = totalElem
			
			self.elements.insert(lastIndex, tmp)
			totalElem += 1
			
			for i in range(lastIndex, totalElem):
				self.elements[i].SetPosition(0,\
					(0 if i == 0 else self.elements[i - 1].GetLocalPosition()[1] + self.elements[i - 1].GetHeight() + self.ELEM_PADDING))
			
			addPadding = self.ELEM_PADDING
		else:
			self.elements.append(tmp)

		tmp.Show()

		self.scrollBoard.SetSize(tmp.GetWidth(), self.scrollBoard.GetHeight() + addPadding + tmp.GetHeight())
		self.UpdateScrollbar()
		
		return tmp

	def ClearItems(self):
		for wnd in self.elements:
			wnd.Hide()
		del self.elements[:]

		self.scrollBoard.SetSize(0, 0)
		self.UpdateScrollbar()

	def GetLenElements(self):
		return len(self.elements) != 0

	def OnMouseWheel(self, length):
		if self.peekWindow.IsInPosition():
			self.UpdateScrollbar(int((length * 0.01) * self.SCROLL_SPEED))
			return True
		
		return False
	
	def OnScrollBar(self, fScale):
		curr = min(0, max(math.ceil((self.scrollBoard.GetHeight() - self.peekWindow.GetHeight()) * fScale * -1.0), -self.scrollBoard.GetHeight() + self.peekWindow.GetHeight()))
		self.scrollBoard.SetPosition(0, curr)
	
	def ChangeScrollbar(self):
		if not self.scrollBar:
			return
		
		if self.scrollBoard.GetHeight() <= self.GetHeight():
			self.scrollBar.Hide()
		else:
			self.scrollBar.SetScale(self.GetHeight(), self.scrollBoard.GetHeight())
			self.scrollBar.SetPosScale(truediv(abs(self.scrollBoard.GetLocalPosition()[1]), (self.scrollBoard.GetHeight() - self.peekWindow.GetHeight())))
			self.scrollBar.Show()
	
	def UpdateScrollbar(self, val = 0):
		curr = min(0, max(self.scrollBoard.GetLocalPosition()[1] + val, -self.scrollBoard.GetHeight() + self.peekWindow.GetHeight()))
		self.scrollBoard.SetPosition(0, curr)
		
		self.ChangeScrollbar()
	
	def RegisterScrollBar(self):
		# if app.ENABLE_MOUSE_WHEEL_EVENT:
		# self.SetScrollWheelEvent(self.OnMouseWheel)
		self.scrollBar = ShopSearchScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(547, self.peekWindow.GetLocalPosition()[1])
		self.scrollBar.SetSize(7, self.peekWindow.GetHeight())
		self.scrollBar.SetScrollEvent(self.OnScrollBar)
		self.scrollBar.SetScrollSpeed(self.SCROLL_SPEED)
		self.scrollBar.Show()
		
		self.ChangeScrollbar()
